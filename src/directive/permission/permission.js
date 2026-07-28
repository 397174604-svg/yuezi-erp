import store from '@/store'

function checkPermission(el, binding) {
  const { value } = binding
  const roles = store.getters && store.getters.roles
  const permissions = store.getters && store.getters.permissions

  if (value && value instanceof Array) {
    if (value.length > 0) {
      const hasPermission = roles.includes('SYS_ADMIN') || value.some(item => {
        return roles.includes(item) || permissions.includes(item)
      })

      if (!hasPermission) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    }
  } else {
    throw new Error(`need role or permission codes! Like v-permission="['SALES_MANAGER','SALES.APPROVE']"`)
  }
}

export default {
  inserted(el, binding) {
    checkPermission(el, binding)
  },
  update(el, binding) {
    checkPermission(el, binding)
  }
}
