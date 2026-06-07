from collections import deque
from functools import lru_cache
import logging

from rich import get_console
from rich.logging import RichHandler
from rich.text import Text
from uvicorn import Server


class DequeHandler(logging.Handler):
    def __init__(self, deque_object):
        super().__init__()
        self.deque = deque_object

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.deque.append(Text.from_markup(log_entry))
        except Exception:
            self.handleError(record)


class RichColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.WARNING: "[yellow]",
        logging.ERROR: "[red]",
        logging.CRITICAL: "[bold red]",
    }

    def format(self, record):
        message = super().format(record)

        color_tag = self.LEVEL_COLORS.get(record.levelno)
        if color_tag:
            return f"{color_tag}{message}[/]"

        return message


def _replace_handlers(logger: logging.Logger, handler: logging.Handler) -> None:
    for existing in logger.handlers[:]:
        logger.removeHandler(existing)
    logger.addHandler(handler)
    logger.propagate = False


def hook_logging_into_handler(
    capture_handler: logging.Handler, logger_names: list[str]
) -> logging.Handler:
    formatter = RichColorFormatter("%(message)s", datefmt="[%X]")
    capture_handler.setFormatter(formatter)

    for logger_name in logger_names:
        _replace_handlers(logging.getLogger(logger_name), capture_handler)

    root = logging.getLogger()
    _replace_handlers(root, capture_handler)
    root.setLevel(logging.INFO)

    return capture_handler


def wrap_uvicorn_logging(server: Server):
    async def run_server(buffer: deque[str]):
        # Uvicorn installs StreamHandlers via dictConfig in Config.__init__ and again
        # in reload child processes; disable that so logs only go to our buffer.
        server.config.log_config = None
        hook_logging_into_handler(
            DequeHandler(buffer),
            [
                "uvicorn",
                "uvicorn.error",
                "uvicorn.access",
                "uvicorn.asgi",
                "watchfiles.main",
                "coloco.cli",
                "coloco.codegen",
                "coloco.db",
            ],
        )

        return await server.serve()

    return run_server


# Set up default logger
@lru_cache
def get_cli_logger(name: str = "coloco.cli"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    rich_handler = RichHandler(rich_tracebacks=True, markup=True)
    formatter = RichColorFormatter("%(message)s", datefmt="[%X]")
    rich_handler.setFormatter(formatter)
    logger.addHandler(rich_handler)
    return logger
