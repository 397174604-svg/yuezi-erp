const resourcePermissions = {
  contracts: {
    navId: 85,
    actions: {
      添加: 1,
      删除: 3,
      编辑: 10,
      导出: 19,
      设置: 20,
      审核: 21,
      打印: 48,
      反审核: 49,
      流程审批: 51,
      提交: 58,
      取消: 65,
      套餐升级: 71,
      // 旧系统实时页面显示该按钮，但导入的按钮字典没有独立编号。
      // 新系统为可变更合同数据的动作单独设权，避免复用“浏览”权限。
      膳食套餐: 'SALES.CONTRACT.MEAL_PACKAGE.UPDATE',
      编辑模板: 114,
      变更: 124,
      远程签约: 151,
      折扣率审核: 155
    }
  },
  packages: {
    navId: 87,
    actions: {
      添加: 1,
      删除: 3,
      编辑: 10,
      设置: 20,
      审核: 21,
      复制: 28,
      启用: 34,
      反审核: 49,
      流程审批: 51,
      提交: 58,
      '推荐/取消': 130,
      '屏蔽/取消': 131
    }
  },
  'gift-lists': {
    navId: 237,
    actions: { 添加: 1, 删除: 3, 编辑: 10 }
  },
  discounts: {
    navId: 310,
    actions: {
      添加: 1,
      删除: 3,
      编辑: 10,
      导出: 19,
      审核: 21,
      停用: 35,
      反审核: 49,
      核销: 'SALES.DISCOUNT.CONSUME'
    }
  },
  'card-packages': {
    navId: 412,
    actions: { 添加: 1, 删除: 3, 编辑: 10, 复制: 28 }
  },
  'product-sales': {
    navId: 523,
    actions: {
      删除: 3,
      编辑: 10,
      导出: 19,
      打印: 48,
      退货: 64,
      取消: 65,
      收款: 66,
      服务销售: 72,
      物料销售: 73,
      卡类销售: 75,
      是否启用: 88,
      出库: 92,
      星支付: 93,
      变更: 124,
      介绍分配: 141,
      取消退货: 147,
      折扣率审核: 155
    }
  },
  coupons: {
    navId: 534,
    actions: { 添加: 1, 删除: 3, 编辑: 10, 导出: 19, 分发: 95 }
  },
  'gift-applications': {
    navId: 556,
    actions: {
      删除: 3,
      反审核: 49,
      流程审批: 51,
      服务销售: 72,
      物料销售: 73,
      卡类销售: 75,
      撤回: 132
    }
  },
  'sales-details': {
    navId: 602,
    actions: { 导出: 19 }
  }
}

const normalize = value => String(value || '').replace(/\s+/g, '')

export function salesNavId(resource) {
  return (resourcePermissions[resource] || {}).navId || null
}

export function salesActionPermission(resource, action) {
  const definition = resourcePermissions[resource]
  if (!definition) return ''
  const buttonIdOrCode = definition.actions[normalize(action)]
  if (typeof buttonIdOrCode === 'string') return buttonIdOrCode
  return buttonIdOrCode
    ? `LEGACY.WEB.N${definition.navId}.B${buttonIdOrCode}`
    : ''
}

export function canUseSalesAction(resource, action, permissions, roles) {
  if ((roles || []).includes('SYS_ADMIN')) return true
  const permission = salesActionPermission(resource, action)
  return Boolean(permission && (permissions || []).includes(permission))
}

export function visibleSalesActions(resource, actions, permissions, roles) {
  return (actions || []).filter(action => (
    canUseSalesAction(resource, action, permissions, roles)
  ))
}

export default resourcePermissions
