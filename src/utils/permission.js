import store from '@/store'

/**
 * @param {Array} value
 * @returns {Boolean}
 * @example see @/views/permission/directive.vue
 */
export default function checkPermission(value) {
  if (value && value instanceof Array && value.length > 0) {
    const roles = store.getters && store.getters.roles
    const permissions = store.getters && store.getters.permissions
    if (roles.includes('SYS_ADMIN')) return true

    return value.some(item => {
      return roles.includes(item) || permissions.includes(item)
    })
  } else {
    console.error(`need role or permission codes! Like v-permission="['SALES_MANAGER','SALES.APPROVE']"`)
    return false
  }
}
