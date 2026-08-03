const stores = [
  { id: 'ST001', name: '中心广场旗舰店', code: 'QD-ZXGC', manager: '王店长', departments: 9, employees: 46, rooms: 36, status: '启用' },
  { id: 'ST002', name: '黄河路轻奢店', code: 'QD-HHL', manager: '李店长', departments: 7, employees: 31, rooms: '资料待补', status: '启用' }
]

const departments = [
  { id: 'D001', name: '营销中心', store: '中心广场旗舰店', leader: '李主管', employees: 8, dataScope: '本部门', status: '启用' },
  { id: 'D002', name: '护理部', store: '中心广场旗舰店', leader: '张主管', employees: 16, dataScope: '本门店', status: '启用' },
  { id: 'D003', name: '产康部', store: '中心广场旗舰店', leader: '陈主管', employees: 7, dataScope: '本部门', status: '启用' },
  { id: 'D004', name: '膳食部', store: '中心广场旗舰店', leader: '周主管', employees: 9, dataScope: '本门店', status: '启用' },
  { id: 'D005', name: '财务部', store: '集团共享', leader: '赵主管', employees: 5, dataScope: '全部门店', status: '启用' },
  { id: 'D006', name: '仓储部', store: '黄河路轻奢店', leader: '孙主管', employees: 4, dataScope: '本门店', status: '停用' }
]

const roles = [
  { id: 'R001', name: '系统管理员', code: 'admin', users: 2, dataScope: '全部数据', menus: 220, status: '启用' },
  { id: 'R002', name: '店长', code: 'store_manager', users: 2, dataScope: '本门店', menus: 168, status: '启用' },
  { id: 'R003', name: '销售顾问', code: 'sales', users: 12, dataScope: '本人及本部门', menus: 38, status: '启用' },
  { id: 'R004', name: '护理主管', code: 'nursing_manager', users: 3, dataScope: '本门店护理部', menus: 47, status: '启用' },
  { id: 'R005', name: '财务专员', code: 'finance', users: 5, dataScope: '指定门店', menus: 41, status: '启用' },
  { id: 'R006', name: '仓库管理员', code: 'warehouse', users: 4, dataScope: '本门店仓库', menus: 29, status: '启用' }
]

const users = [
  { id: 'U001', username: 'admin', name: '系统管理员', mobile: '138****1001', store: '全部门店', department: '信息中心', role: '系统管理员', lastLogin: '2026-07-22 17:36', status: '启用' },
  { id: 'U002', username: 'store01', name: '王店长', mobile: '138****1028', store: '中心广场旗舰店', department: '店务中心', role: '店长', lastLogin: '2026-07-22 16:52', status: '启用' },
  { id: 'U003', username: 'sales03', name: '李顾问', mobile: '138****1186', store: '中心广场旗舰店', department: '营销中心', role: '销售顾问', lastLogin: '2026-07-22 15:20', status: '启用' },
  { id: 'U004', username: 'nurse02', name: '张主管', mobile: '138****1269', store: '中心广场旗舰店', department: '护理部', role: '护理主管', lastLogin: '2026-07-22 14:48', status: '启用' },
  { id: 'U005', username: 'finance01', name: '赵主管', mobile: '138****1391', store: '集团共享', department: '财务部', role: '财务专员', lastLogin: '2026-07-21 18:06', status: '启用' },
  { id: 'U006', username: 'warehouse02', name: '孙主管', mobile: '138****1473', store: '黄河路轻奢店', department: '仓储部', role: '仓库管理员', lastLogin: '2026-07-18 09:30', status: '停用' }
]

const dictionaryTypes = [
  { id: 'DT01', name: '客户来源', code: 'customer_source', items: 6, builtIn: true },
  { id: 'DT02', name: '客户状态', code: 'customer_status', items: 7, builtIn: true },
  { id: 'DT03', name: '合同状态', code: 'contract_status', items: 6, builtIn: true },
  { id: 'DT04', name: '支付方式', code: 'payment_method', items: 5, builtIn: true },
  { id: 'DT05', name: '房间状态', code: 'room_status', items: 6, builtIn: true },
  { id: 'DT06', name: '护理任务状态', code: 'care_task_status', items: 5, builtIn: true },
  { id: 'DT07', name: '审批动作', code: 'workflow_action', items: 5, builtIn: true }
]

const dictionaryItems = {
  customer_source: [
    { label: '朋友推荐', value: 'referral', sort: 10, color: '#45b8ac', status: '启用' },
    { label: '线上咨询', value: 'online', sort: 20, color: '#4f8cf7', status: '启用' },
    { label: '到店咨询', value: 'walk_in', sort: 30, color: '#ff6f9c', status: '启用' },
    { label: '渠道合作', value: 'channel', sort: 40, color: '#f5ba35', status: '启用' },
    { label: '老客转介绍', value: 'existing_customer', sort: 50, color: '#8f7cf6', status: '启用' },
    { label: '其他', value: 'other', sort: 99, color: '#8b96a6', status: '启用' }
  ],
  customer_status: [
    { label: '新建', value: 'new', sort: 10, color: '#4f8cf7', status: '启用' },
    { label: '跟进中', value: 'following', sort: 20, color: '#f5ba35', status: '启用' },
    { label: '已预约参观', value: 'visiting', sort: 30, color: '#8f7cf6', status: '启用' },
    { label: '已签约', value: 'signed', sort: 40, color: '#45b8ac', status: '启用' },
    { label: '已入住', value: 'checked_in', sort: 50, color: '#ff6f9c', status: '启用' },
    { label: '转公海', value: 'public_pool', sort: 60, color: '#8b96a6', status: '启用' },
    { label: '无效', value: 'invalid', sort: 70, color: '#ef6b6b', status: '启用' }
  ]
}

const permissions = [
  { module: '客户管理', view: true, create: true, edit: true, approve: false, export: true, sensitive: '脱敏' },
  { module: '销售管理', view: true, create: true, edit: true, approve: true, export: true, sensitive: '可见金额' },
  { module: '财务管理', view: true, create: true, edit: true, approve: true, export: true, sensitive: '全部可见' },
  { module: '客房管理', view: true, create: true, edit: true, approve: false, export: true, sensitive: '脱敏' },
  { module: '护理管理', view: true, create: true, edit: true, approve: true, export: false, sensitive: '健康字段受控' },
  { module: '仓存管理', view: true, create: true, edit: true, approve: true, export: true, sensitive: '采购价受控' },
  { module: '系统设置', view: true, create: true, edit: true, approve: true, export: false, sensitive: '管理员' }
]

module.exports = [
  {
    url: '/vue-element-admin/erp/foundation/overview',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: { stores, departments, roles, users, dictionaryTypes, dictionaryItems, permissions }
    })
  },
  {
    url: '/vue-element-admin/erp/foundation/.*?/save',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { ...config.body, updatedAt: '2026-07-22 18:30' },
      message: '保存成功'
    })
  }
]
