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
- Artifacts will be saved to `dist`
- From dist, run `coloco serve`

# Opinions

This framework is opinionated and combines the following excellent tools:

- FastAPI
- Svelte
- openapi-ts (codegen)
- svelte5-router (file-based routing)
- tortoise-orm (optional)

# TBD Required features for launch

- Deploy tools
- Swap migrations to `tortoise-pathway` once cross-app migrations are supported
- Config with secrets encryption
- Package/share modules with git
- Docs

# Features in development

- CRUD
- Caching
- User module
- Dev tools module
- Admin panel module

# Dreams

- Move `node_modules` into `+node`

# Other TODO

- Swap to `copier` for template creation
- `Textual` CLI app / installer / dev tools?
- Resolve duplicate types in openapi spec (due to model serializers)
