module.exports = [
  {
    url: '/vue-element-admin/erp/sales/modules/[^/]+$',
    type: 'get',
    response: _ => ({ code: 20000, data: { list: [], total: 0, loadedAt: Date.now() }})
  },
  {
    url: '/vue-element-admin/erp/sales/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { id: config.body.id || `SALE-${Date.now()}`, savedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/sales/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { action: config.body.action, auditId: `SALE-AUDIT-${Date.now()}`, processedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/sales/modules/[^/]+/audit$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { result: config.body.auditResult, auditId: `APPROVAL-${Date.now()}`, auditedAt: Date.now() }
    })
  }
]
