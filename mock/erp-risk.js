module.exports = [
  {
    url: '/vue-element-admin/erp/risk/modules/[^/]+$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: {
        list: [],
        total: 0,
        source: 'desensitized-local-draft',
        persisted: false,
        evidenceLevel: '待原系统二次核验',
        loadedAt: Date.now()
      }
    })
  }
]
