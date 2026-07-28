const financeEmployees = [
  { id: 'U001', username: 'admin', name: '系统管理员', department: '信息中心', store: '全部门店', role: '系统管理员', status: '启用' },
  { id: 'U002', username: 'store01', name: '王店长', department: '店务中心', store: '中心广场旗舰店', role: '店长', status: '启用' },
  { id: 'U003', username: 'sales03', name: '李顾问', department: '营销中心', store: '中心广场旗舰店', role: '销售顾问', status: '启用' },
  { id: 'U004', username: 'finance01', name: '赵主管', department: '财务部', store: '集团共享', role: '财务专员', status: '启用' }
]

const financeCustomers = [
  { id: 'C001', username: 'user', name: 'user', mobile: '138****2001', status: '已签合同但未入住', salesperson: '李顾问', store: '中心广场旗舰店' },
  { id: 'C002', username: 'user02', name: '演示客户甲', mobile: '138****2136', status: '已订房', salesperson: '李顾问', store: '中心广场旗舰店' },
  { id: 'C003', username: 'user03', name: '演示客户乙', mobile: '138****2268', status: '已入住', salesperson: '王顾问', store: '黄河路轻奢店' },
  { id: 'C004', username: 'user04', name: '演示客户丙', mobile: '138****2395', status: '意向A', salesperson: '陈顾问', store: '中心广场旗舰店' }
]

module.exports = [
  {
    url: '/vue-element-admin/erp/finance/pickers/employee$',
    type: 'get',
    response: _ => ({ code: 20000, data: { list: financeEmployees, total: financeEmployees.length }})
  },
  {
    url: '/vue-element-admin/erp/finance/pickers/customer$',
    type: 'get',
    response: _ => ({ code: 20000, data: { list: financeCustomers, total: financeCustomers.length }})
  },
  {
    url: '/vue-element-admin/erp/finance/modules/[^/]+$',
    type: 'get',
    response: _ => ({ code: 20000, data: { list: [], total: 0, loadedAt: Date.now() }})
  },
  {
    url: '/vue-element-admin/erp/finance/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { id: config.body.id || `FINANCE-${Date.now()}`, savedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/finance/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { action: config.body.action, auditId: `FINANCE-AUDIT-${Date.now()}`, processedAt: Date.now() }
    })
  }
]
