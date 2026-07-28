module.exports = [
  {
    url: '/vue-element-admin/erp/maternity-nurse/modules/[^/]+$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: {
        list: [],
        total: 0,
        demonstrationOnly: true,
        internalSchemaVerified: false
      }
    })
  },
  {
    url: '/vue-element-admin/erp/maternity-nurse/modules/[^/]+/save$',
    type: 'post',
    response: _ => ({
      code: 40900,
      message: '页面内部字段尚未完成二次核验，演示环境禁止保存。'
    })
  },
  {
    url: '/vue-element-admin/erp/maternity-nurse/modules/[^/]+/action$',
    type: 'post',
    response: _ => ({
      code: 40900,
      message: '页面内部交互尚未完成二次核验，演示环境禁止执行该动作。'
    })
  }
]

