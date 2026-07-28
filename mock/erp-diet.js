module.exports = [
  {
    url: '/vue-element-admin/erp/diet/modules/[^/]+$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: {
        list: [],
        total: 0,
        source: 'desensitized-demo',
        persisted: false,
        loadedAt: Date.now()
      }
    })
  },
  {
    url: '/vue-element-admin/erp/diet/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        id: config.body.id || `DIET-DEMO-${Date.now()}`,
        persisted: false,
        savedAt: Date.now()
      }
    })
  },
  {
    url: '/vue-element-admin/erp/diet/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        action: config.body.action,
        persisted: false,
        operationId: `DIET-ACTION-DEMO-${Date.now()}`,
        processedAt: Date.now()
      }
    })
  }
]
