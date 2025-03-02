# FA-Kit

A kit for creating FastAPI + Svelte applications.  Made to reduce boilerplate and increase locality of code.  Create full-stack apps with auto-generated types and API calling code.  Deploy with a package that can be hosted with python or a docker container.

File-based routing for your front-end and back-end.  Expose API endpoints with openapi docs via `fastapi`.  Generate a front-end with `svelte`.

Example:

`hello/api.py`
```python
from fakit import api

@api.post("/test")
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