<script lang="ts">
  import { route, Router, type Route } from "@mateothegreat/svelte5-router";
  import { getRoutes } from "./router";
  import Index from "./index.svelte";
  import NotFound from "./404.svelte";

  const modules: Record<string, any> = import.meta.glob(
    ["../**/*.svelte", "!../node_modules/**/*.svelte", "!../+**/*.svelte"],
    { eager: true },
  );

  const routes: Route[] = [
    {
      path: "^/$",
      component: Index,
    },
    ...getRoutes(modules),
    {
      path: ".+",
      component: NotFound,
    },
  ];
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
