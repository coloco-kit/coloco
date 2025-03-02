# Coloco

A kit for creating full-stack apps with co-located code, built on FastAPI and Svelte.  Bundle your front-end and back-end code and easily tie them together with codegen.

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

  const results = test({ query: { name: "Coloco" } });
</script>

{#if $results.loading}
    Loading...
{:else}
    The server says {$results.data}
{/if}
```

Serves the page `myapp.com/hello`, which calls `myapp.com/hello/test?name=Coloco` and prints the message `Hello Coloco!`

# Opinions

This framework is opinionated and combines the following excellent tools:
 * FastAPI
 * Svelte
 * openapi-ts (codegen)
 * svelte5-router (file-based routing)
 * tortoise-orm (optional)
