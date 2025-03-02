import type { Route } from "@mateothegreat/svelte5-router";
import type { Component, Snippet } from "svelte";

function getRoutesFromModules(modules: Record<string, any>) {
  const routes = [];
  for (let [path, module] of Object.entries(modules)) {
    // Dev only paths
    if (path.includes('-')) {
      if (import.meta.env.DEV) {
        path = path.replace('-', '');
      } else {
        continue;
      }
    }

    const uri = "^/" + path
      .replace(/^(..\/)+/, '')
      .replace(/^\.\.\/(.+)$/, '$1')
      .replace(/^(.+)\/index\.svelte$/, '$1')
      .replace(/^(.+)\.svelte$/, '$1') + "$";
    routes.push({ path: uri, component: module.default });
  }
  return routes;
}
export function getRoutes({
  index,
  notFound
}: {
  index: Component<any> | Snippet,
  notFound: Component<any> | Snippet
}): Route[] {
  // path join
  const modules: Record<string, any> = import.meta.glob(
    [`/../**/*.svelte`, "!/../node_modules/**/*.svelte", "!/../+**/*.svelte"],
    { eager: true },
  );
  return [
    {
      path: "^/$",
      component: index,
    },
    ...getRoutesFromModules(modules),
    {
      path: ".+",
      component: notFound,
    },
  ];
}
