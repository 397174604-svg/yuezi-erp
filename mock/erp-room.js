module.exports = [
  {
    url: '/vue-element-admin/erp/room/modules/[^/]+$',
    type: 'get',
    response: _ => ({ code: 20000, data: { list: [], total: 0, loadedAt: Date.now() }})
  },
  {
    url: '/vue-element-admin/erp/room/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { id: config.body.id || `ROOM-${Date.now()}`, savedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/room/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { action: config.body.action, auditId: `ROOM-AUDIT-${Date.now()}`, processedAt: Date.now() }
    })
  }
]

