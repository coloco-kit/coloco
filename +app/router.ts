function getRoutes(modules: Record<string, any>) {
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
      .replace(/^\.\.\/(.+)$/, '$1')
      .replace(/^(.+)\/index\.svelte$/, '$1')
      .replace(/^(.+)\.svelte$/, '$1') + "$";
    routes.push({ path: uri, component: module.default });
  }
  return routes;
}

export { getRoutes }