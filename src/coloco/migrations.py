"""
Topological ordering for tortoise migrations.

Tortoise's autodetector only records cross-app dependencies on migrations
already on disk, so migrations that reference another app's models can be
written without the dependency that orders them after that app's migrations,
and end up applying in alphabetical app order.  Two fixes:

- add_same_run_dependencies links migrations created in the same
  makemigrations run before they are written to disk
- patch_migration_loader heals already-written migration files by deriving
  the missing graph edges from each migration's operations at load time
"""

from tortoise.fields.relational import (
    ForeignKeyFieldInstance,
    ManyToManyFieldInstance,
    OneToOneFieldInstance,
)
from tortoise.migrations.graph import MigrationGraph, MigrationKey
from tortoise.migrations.loader import MigrationLoader
from tortoise.migrations.operations import CreateModel
from tortoise.migrations.writer import MigrationWriter

from .cli.shared.logging import get_cli_logger

cli = get_cli_logger("coloco.migrations")

_RELATION_FIELDS = (ForeignKeyFieldInstance, OneToOneFieldInstance, ManyToManyFieldInstance)


def _iter_relation_references(operations):
    """Yield (app_label, model_name) for each relation field in operations."""
    fields = []
    for operation in operations:
        fields.extend(field for _, field in getattr(operation, "fields", None) or [])
        operation_field = getattr(operation, "field", None)
        if operation_field is not None:
            fields.append(operation_field)

    for field in fields:
        if not isinstance(field, _RELATION_FIELDS):
            continue
        model_name = field.model_name
        if isinstance(model_name, str):
            if "." in model_name:
                app_label, model = model_name.split(".", 1)
                yield app_label, model
        elif model_name._meta.app:
            yield model_name._meta.app, model_name.__name__


def _related_app_labels(writer: MigrationWriter) -> set[str]:
    """App labels referenced by relation fields in a migration's operations."""
    labels = {app_label for app_label, _ in _iter_relation_references(writer.operations)}
    labels.discard(writer.app_label)
    return labels


def _depends_on(source: MigrationWriter, target_app: str, writers_by_app: dict) -> bool:
    """Whether source already reaches target_app through same-run dependencies."""
    seen = set()
    stack = [source]
    while stack:
        writer = stack.pop()
        if writer.app_label in seen:
            continue
        seen.add(writer.app_label)
        if writer.app_label == target_app:
            return True
        for dep_app, dep_name in writer.dependencies:
            dep_writer = writers_by_app.get(dep_app)
            if dep_writer is not None and dep_writer.name == dep_name:
                stack.append(dep_writer)
    return False


def add_same_run_dependencies(writers: list[MigrationWriter]) -> None:
    """
    Link migrations created in the same run so they apply in topological order.

    Tortoise's autodetector only records cross-app dependencies on migrations
    already on disk, so a migration referencing a model whose migration is
    created in the same run would otherwise apply in alphabetical app order.
    """
    writers_by_app = {writer.app_label: writer for writer in writers}
    for writer in writers:
        for related_app in sorted(_related_app_labels(writer)):
            related_writer = writers_by_app.get(related_app)
            if related_writer is None:
                continue
            dependency = (related_app, related_writer.name)
            if dependency in writer.dependencies:
                continue
            if _depends_on(related_writer, writer.app_label, writers_by_app):
                cli.info(
                    f"[yellow]Apps {writer.app_label} and {related_app} reference "
                    f"each other; circular migrations cannot be ordered and will "
                    f"fail to apply. Create the models in one migration and add "
                    f"the circular foreign keys in a follow-up migration.[/yellow]"
                )
                continue
            writer.dependencies.append(dependency)
            writer.dependencies.sort()


def _graph_depends_on(graph: MigrationGraph, source: MigrationKey, target: MigrationKey) -> bool:
    """Whether source (transitively) depends on target in the migration graph."""
    seen = set()
    stack = [graph.node_map[source]]
    while stack:
        node = stack.pop()
        if node.key == target:
            return True
        if node.key in seen:
            continue
        seen.add(node.key)
        stack.extend(node.parents)
    return False


def _add_missing_relation_dependencies(loader: MigrationLoader) -> None:
    """
    Add graph edges for cross-app model references that migration files fail
    to declare (files generated before same-run dependency linking existed),
    so existing migrations still replay and apply in topological order.
    """
    creators: dict[tuple[str, str], MigrationKey] = {}
    for key, migration in loader.disk_migrations.items():
        for operation in migration.operations:
            if isinstance(operation, CreateModel):
                creators.setdefault((key.app_label, operation.name), key)

    for key, migration in loader.disk_migrations.items():
        for reference in _iter_relation_references(migration.operations):
            creator = creators.get(reference)
            if creator is None or creator.app_label == key.app_label:
                continue
            if loader.graph.node_map[creator] in loader.graph.node_map[key].parents:
                continue
            # Mutual references cannot be ordered automatically; leave as-is
            # rather than creating a dependency cycle
            if _graph_depends_on(loader.graph, creator, key):
                continue
            loader.graph.add_dependency(key, key, creator, skip_validation=True)


_original_build_graph = MigrationLoader.build_graph


async def _build_graph_with_relation_dependencies(self: MigrationLoader) -> None:
    await _original_build_graph(self)
    _add_missing_relation_dependencies(self)


def patch_migration_loader() -> None:
    """Make every migration graph include relation-derived dependencies."""
    if not getattr(MigrationLoader.build_graph, "_coloco_patch", False):
        _build_graph_with_relation_dependencies._coloco_patch = True
        MigrationLoader.build_graph = _build_graph_with_relation_dependencies
