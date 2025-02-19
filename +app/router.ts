const modules: Record<string, any> = import.meta.glob('./pages/**/*.svelte', { eager: true });

function getRoutes() {
  const routes: Record<string, any> = {};
  for (let [path, module] of Object.entries(modules)) {
    // Dev only paths
    if (path.includes('-')) {
      if (import.meta.env.DEV) {
        path = path.replace('-', '');
      } else {
        continue;
      }
    }

    const uri = "/" + path
      .replace(/^\.\/pages\/(.+)\.svelte$/, '$1')
      .replace('index', '');
    routes[uri] = module.default;
  }
  return routes;
}

export { getRoutes }