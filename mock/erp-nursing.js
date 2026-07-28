module.exports = [
  {
    url: '/vue-element-admin/erp/nursing/modules/[^/]+$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: {
        list: [],
        total: 0,
        evidenceLevel: '待原系统二次核验',
        loadedAt: Date.now()
      }
    })
  },
  {
    url: '/vue-element-admin/erp/nursing/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        id: config.body.id || `NURSING-DEMO-${Date.now()}`,
        demoOnly: true,
        savedAt: Date.now()
      }
    })
  },
  {
    url: '/vue-element-admin/erp/nursing/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        action: config.body.action,
        demoOnly: true,
        processedAt: Date.now()
      }
    })
  }
]

