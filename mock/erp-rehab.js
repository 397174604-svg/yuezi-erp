module.exports = [
  {
    url: '/vue-element-admin/erp/rehab/modules/[^/]+$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: { list: [], total: 0, source: 'desensitized-demo', loadedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/rehab/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        id: config.body.id || `REHAB-DEMO-${Date.now()}`,
        persisted: false,
        savedAt: Date.now()
      }
    })
  },
  {
    url: '/vue-element-admin/erp/rehab/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        action: config.body.action,
        persisted: false,
        operationId: `REHAB-ACTION-DEMO-${Date.now()}`,
        processedAt: Date.now()
      }
    })
  }
]
