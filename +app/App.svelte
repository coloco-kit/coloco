<script lang="ts">
  import Router from "svelte-spa-router";
  import { onMount } from "svelte";
  import { getRoutes } from "./router";

  let routes: any = null;
  onMount(() => {
    routes = getRoutes();
  });
</script>

<main>
  MAIN
  {#if routes}
    <Router {routes} />
  {/if}
</main>
