export function findErpRouteByTitle(routes, title) {
  for (const route of routes || []) {
    if (route.meta && route.meta.title === title && route.name) return route
    const child = findErpRouteByTitle(route.children, title)
    if (child) return child
  }
  return null
}

export function workspaceTabs(config) {
  return (config && config.workspace && config.workspace.tabs) || []
}
