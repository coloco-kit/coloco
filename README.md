# Coloco

A kit for creating FastAPI + Svelte applications focusing on locality of code and decreased boilerplate.  Create simple full-stack apps with built-in codegen.  Deploy with a package that can be hosted with python or a docker container.

File-based routing for your front-end and back-end.  Expose API endpoints with docs via `fastapi`.  Generate a front-end with `svelte`.

Example:

`hello/api.py`
```python
from coloco import api

@api
def test(name: str) -> str:
    return f"Hello {name}!"

```

`hello/index.svelte`
```svelte
<script lang="ts">
  import { test } from "./api";

  const results = test({ query: { name: "DoItLive" } });
</script>

{#if $results.loading}
    Loading...
{:else}
    The server says {$results.data}
{/if}
```

Serves the page `myapp.com/hello`, which calls `myapp.com/hello/test?name=DoItLive` and prints the message `Hello DoItLive!`

# Opinions

This framework is opinionated and combines the following tools/concepts:
 * FastAPI
 * Svelte
 * openapi-ts (codegen)
 * file-based routing (using svelte5-router)
 * tortoise-orm (optional)
