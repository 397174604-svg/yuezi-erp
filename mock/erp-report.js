module.exports = [
  {
    url: '/vue-element-admin/erp/report/modules/[^/]+$',
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
  }
]

