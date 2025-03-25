# Coloco

A kit for creating full-stack apps with co-located code, built on FastAPI and Svelte. Bundle your front-end and back-end code and easily tie them together with codegen.

Example:

`hello/api.py`

```python
from coloco import api

@api
def test(name: str):
    return f"Hello {name}!"

```

`hello/index.svelte`

```svelte
<script lang="ts">
  import { test } from "./api";
</script>

{#await test({ name: "Coloco" })}
	Loading...
{:then result}
	The server says {result}
{/await}
```

Serves the page `myapp.com/hello`, which calls `myapp.com/hello/test?name=Coloco` and prints the message `Hello Coloco!`

# Getting Started

- `pip install coloco`
- `coloco createapp myapp`
- From `myapp` - `coloco dev`

# Running in Production

- `coloco build`

- `coloco serve`

# Opinions

This framework is opinionated and combines the following excellent tools:

- FastAPI
- Svelte
- openapi-ts (codegen)
- svelte5-router (file-based routing)
- tortoise-orm (optional)

# Plans

- Deploy tools
- ORM Support
- SQLite/Postgres support
- Package/share modules with git

# Dreams

- Move `node_modules` into `+node`
- Somehow clean up litter from `uv`

# TODO

- Swap to `cyclopts` for CLI
- Swap to `copier` for template creation
- `Textual` CLI app / installer / dev tools?
- Common dev `admin` module
