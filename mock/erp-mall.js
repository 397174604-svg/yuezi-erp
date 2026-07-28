module.exports = [
  {
    url: '/vue-element-admin/erp/mall/modules/[^/]+$',
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
    url: '/vue-element-admin/erp/mall/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        id: config.body.id || `MALL-DEMO-${Date.now()}`,
        persisted: false,
        synchronizedToMamaApp: false,
        savedAt: Date.now()
      }
    })
  },
  {
    url: '/vue-element-admin/erp/mall/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        action: config.body.action,
        persisted: false,
        synchronizedToMamaApp: false,
        operationId: `MALL-ACTION-DEMO-${Date.now()}`,
        processedAt: Date.now()
      }
    })
  }
]
