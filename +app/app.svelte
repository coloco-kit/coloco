<script lang="ts">
  import { route, Router } from "@mateothegreat/svelte5-router";
  import { getRoutes } from "./fakit/router";
  import Index from "./index.svelte";
  import NotFound from "./404.svelte";

  const routes = getRoutes({
    index: Index,
    notFound: NotFound,
  });
</script>

<main>
  MAIN<br /><br />

  <a use:route href="/">Home</a><br />
  <a use:route href="/test/chongus">chongus</a><br />
  <a use:route href="/besto">besto</a><br />
  <a use:route href="/besto/zesto">zesto</a><br />
  <a use:route href="/ded">nothing</a><br /><br />

  <Router basePath="/" {routes} />
</main>
