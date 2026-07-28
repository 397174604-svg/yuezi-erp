const resourcePermissions = {
  'room-map': {
    navId: 418,
    actions: {
      商品销售: 105,
      订房: 79,
      入住: 80,
      续住: 81,
      换房: 82,
      退房: 83,
      结账: 62,
      入住通知单: 84,
      客房服务申请: 85,
      服务预约: 86,
      房型订房: 87,
      '维修/脏房': 70,
      跨店订房: 115,
      跨店换房: 116
    }
  },
  'room-trend': { navId: 526, actions: {}},
  'room-type-trend': { navId: 587, actions: {}},
  'smart-allocation': { navId: 517, actions: { 订房: 79 }},
  'saleable-statistics': { navId: 567, actions: {}},
  'room-type-bookings': {
    navId: 424,
    actions: { 删除: 3, 房型订房: 87 }
  },
  'room-reservations': {
    navId: 375,
    actions: { 编辑: 10, 退订: 76, 退订并结账: 77 }
  },
  'room-stays': {
    navId: 558,
    actions: { 编辑: 10, 导出: 19, 取消: 65, 续住: 81, 换房: 82 }
  },
  'stay-extensions': {
    navId: 615,
    actions: { 删除: 3, 编辑: 10, 审核: 21, 反审核: 49, 取消: 65 }
  },
  'room-change-applications': {
    navId: 584,
    actions: { 删除: 3, 审核: 21, 反审核: 49 }
  },
  'gift-distribution': { navId: 284, actions: { 物品发放: 78 }},
  'room-services': {
    navId: 236,
    actions: { 确认完成: 37, 取消: 65, 预约确认: 91 }
  },
  'outing-applications': {
    navId: 113,
    actions: { 添加: 1, 删除: 3, 编辑: 10, 审核: 21, 确定已返回: 36, 打印: 48 }
  },
  'borrowed-items': {
    navId: 235,
    actions: { 添加: 1, 删除: 3, 编辑: 10, 确认签收: 38, 打印: 48 }
  },
  laundry: {
    navId: 238,
    actions: { 添加: 1, 删除: 3, 编辑: 10, 确认签收: 38 }
  }
}

const normalize = value => String(value || '').replace(/\s+/g, '')

export function roomNavId(resource) {
  return (resourcePermissions[resource] || {}).navId || null
}

export function roomActionPermission(resource, action) {
  const definition = resourcePermissions[resource]
  if (!definition) return ''
  const buttonId = definition.actions[normalize(action)]
  return buttonId
    ? `LEGACY.WEB.N${definition.navId}.B${buttonId}`
    : ''
}

export function canUseRoomAction(resource, action, permissions, roles) {
  if ((roles || []).includes('SYS_ADMIN')) return true
  const permission = roomActionPermission(resource, action)
  return Boolean(permission && (permissions || []).includes(permission))
}

export function visibleRoomActions(resource, actions, permissions, roles) {
  return (actions || []).filter(action => (
    canUseRoomAction(resource, action, permissions, roles)
  ))
}

export default resourcePermissions
