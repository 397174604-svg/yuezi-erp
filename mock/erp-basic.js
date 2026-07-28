module.exports = [
  {
    url: '/vue-element-admin/erp/basic/modules/[^/]+$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: {
        list: [],
        total: 0,
        source: 'desensitized-demo',
        persisted: false
      }
    })
  },
  {
    url: '/vue-element-admin/erp/basic/modules/[^/]+/preview$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        preview: config.body,
        persisted: false
      },
      message: '仅完成本地结构预览，未保存业务数据'
    })
  }
]
