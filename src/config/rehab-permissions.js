const resourcePermissions = {
  'unbooked-customer-services': {
    navId: 266,
    actions: { 设置: 20, 读卡: 18 }
  },
  'service-appointments': {
    navId: 257,
    actions: {
      打印: 48,
      服务预约: 86,
      确认完成: 37,
      取消: 65,
      预约确认: 91,
      读卡: 18
    }
  },
  'service-overview-query': { navId: 553, actions: {}},
  'staff-task-board': {
    navId: 490,
    actions: { 添加: 1, 确认完成: 37, 取消: 65 }
  },
  'staff-schedule-settings': {
    navId: 541,
    actions: { 添加: 1, 编辑: 10, 删除: 3 }
  },
  'technician-task-board': {
    navId: 660,
    actions: { 添加: 1, 确认完成: 37, 取消: 65 }
  },
  'customer-service-query': { navId: 334, actions: {}},
  'rehab-service-records': {
    navId: 255,
    actions: {
      编辑: 10,
      批量修改: 145,
      删除: 3,
      导出: 19,
      打印: 48,
      审核: 21,
      反审核: 49
    }
  },
  'completed-service-consumption': { navId: 618, actions: {}},
  'rehab-health-assessments': {
    navId: 631,
    actions: { 添加: 1, 编辑: 10, 删除: 3 }
  }
}

const normalize = value => String(value || '').replace(/\s+/g, '')

export function recoveryNavId(resource) {
  return (resourcePermissions[resource] || {}).navId || null
}

export function recoveryActionPermission(resource, action) {
  const definition = resourcePermissions[resource]
  if (!definition) return ''
  const buttonId = definition.actions[normalize(action)]
  return buttonId
    ? `LEGACY.WEB.N${definition.navId}.B${buttonId}`
    : ''
}

export function canUseRecoveryAction(resource, action, permissions, roles) {
  if ((roles || []).includes('SYS_ADMIN')) return true
  const permission = recoveryActionPermission(resource, action)
  return Boolean(permission && (permissions || []).includes(permission))
}

export function visibleRecoveryActions(resource, actions, permissions, roles) {
  return (actions || []).filter(action => (
    canUseRecoveryAction(resource, action, permissions, roles)
  ))
}

export default resourcePermissions
