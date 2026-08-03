import { asyncRoutes, constantRoutes } from '@/router'

/**
 * Use meta.role to determine if the current user has permission
 * @param roles
 * @param route
 */
function hasPermission(roles, permissions, route) {
  if (roles.includes('SYS_ADMIN')) return true
  let hasAccessRule = false
  if (route.meta && route.meta.permissions) {
    hasAccessRule = true
    if (route.meta.permissions.some(permission => permissions.includes(permission))) return true
  }
  if (route.meta && route.meta.legacyNavId) {
    hasAccessRule = true
    const codePrefix = `LEGACY.WEB.N${route.meta.legacyNavId}.`
    if (permissions.some(permission => permission.startsWith(codePrefix))) return true
  }
  if (route.meta && route.meta.roles) {
    hasAccessRule = true
    if (roles.some(role => route.meta.roles.includes(role))) return true
  }
  return !hasAccessRule
}

/**
 * Filter asynchronous routing tables by recursion
 * @param routes asyncRoutes
 * @param roles
 */
export function filterAsyncRoutes(routes, roles, permissions = []) {
  const res = []

  routes.forEach(route => {
    const tmp = { ...route }
    if (hasPermission(roles, permissions, tmp)) {
      const hadChildren = Boolean(tmp.children && tmp.children.length)
      if (tmp.children) {
        tmp.children = filterAsyncRoutes(tmp.children, roles, permissions)
      }
      if (!hadChildren || tmp.children.length) {
        res.push(tmp)
      }
    }
  })

  return res
}

const state = {
  routes: [],
  addRoutes: []
}

const mutations = {
  SET_ROUTES: (state, routes) => {
    state.addRoutes = routes
    state.routes = constantRoutes.concat(routes)
  }
}

const actions = {
  generateRoutes({ commit, rootGetters }, roles) {
    return new Promise(resolve => {
      let accessedRoutes
      if (roles.includes('SYS_ADMIN')) {
        accessedRoutes = asyncRoutes || []
      } else {
        accessedRoutes = filterAsyncRoutes(
          asyncRoutes,
          roles,
          rootGetters.permissions || []
        )
      }
      commit('SET_ROUTES', accessedRoutes)
      resolve(accessedRoutes)
    })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
