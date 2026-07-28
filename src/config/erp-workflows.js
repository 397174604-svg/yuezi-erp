export const primaryBusinessChain = [
  {
    key: 'customer',
    label: '客户',
    entity: 'customer',
    code: 'CUS-202607-0188',
    status: '跟进中',
    states: ['新建', '跟进中', '已预约参观', '已签约', '转公海', '无效'],
    required: ['姓名', '联系电话', '预产日期', '客户来源', '所属顾问', '所属门店'],
    api: '/api/customers'
  },
  {
    key: 'contract',
    label: '合同',
    entity: 'contract',
    code: 'CON-202607-0062',
    status: '待审核',
    states: ['草稿', '待审核', '已生效', '履约中', '已完成', '已取消'],
    required: ['客户', '套餐', '合同金额', '服务周期', '签约门店', '销售顾问'],
    api: '/api/contracts'
  },
  {
    key: 'receipt',
    label: '收款',
    entity: 'receipt',
    code: 'REC-202607-0116',
    status: '待确认',
    states: ['待确认', '已到账', '已核销', '已退款'],
    required: ['合同', '应收金额', '实收金额', '支付方式', '资金账户', '收款日期'],
    api: '/api/receipts'
  },
  {
    key: 'booking',
    label: '订房',
    entity: 'booking',
    code: 'BKG-202607-0045',
    status: '已预订',
    states: ['待排房', '已预订', '待入住', '已取消'],
    required: ['合同', '房型', '计划入住日', '计划离店日', '定金状态'],
    api: '/api/bookings'
  },
  {
    key: 'stay',
    label: '入住',
    entity: 'stay',
    code: 'STY-202607-0031',
    status: '待入住',
    states: ['待入住', '已入住', '续住', '换房', '已离店'],
    required: ['预订单', '房间', '妈妈档案', '宝宝档案', '交接清单', '押金'],
    api: '/api/stays'
  }
]

export const executionChains = {
  nursing: {
    label: '护理执行',
    states: ['待计划', '待执行', '执行中', '已完成', '异常上报'],
    stockTrigger: '护理项目完成后，按项目物料清单生成领料或消耗记录'
  },
  recovery: {
    label: '产康执行',
    states: ['待预约', '已预约', '已到店', '服务中', '已完成', '爽约'],
    stockTrigger: '服务完成后扣减套餐次数，并按项目标准用量登记耗材'
  },
  diet: {
    label: '膳食执行',
    states: ['待评估', '待排餐', '备餐中', '配送中', '已签收', '退餐'],
    stockTrigger: '确认餐单后汇总食材需求，签收后确认实际食材消耗'
  }
}

export const approvalDefinitions = [
  { key: 'refund', label: '退款审批', amountRule: '金额分级', nodes: ['财务初审', '店长审批', '出纳付款'], result: ['通过', '驳回', '撤回'] },
  { key: 'payment', label: '付款审批', amountRule: '预算与金额分级', nodes: ['部门负责人', '财务审核', '总经理审批', '出纳付款'], result: ['通过', '驳回', '撤回'] },
  { key: 'discount', label: '超额优惠审批', amountRule: '超过角色授权金额', nodes: ['销售主管', '店长审批'], result: ['通过', '驳回'] },
  { key: 'room_change', label: '换房审批', amountRule: '涉及价差时进入财务', nodes: ['客房主管', '财务确认'], result: ['通过', '驳回'] },
  { key: 'matron_dispatch', label: '月嫂派工审批', amountRule: '薪酬标准变化时加签', nodes: ['月嫂主管', '店长审批'], result: ['通过', '驳回'] }
]

export const migrationControls = [
  { key: 'identity', label: '主键映射', rule: '保留旧系统编号，生成新系统不可变 ID，并建立 migration_id_map' },
  { key: 'money', label: '金额对账', rule: '合同额、实收、退款、欠款、账户余额按门店和日期双向核对' },
  { key: 'permission', label: '权限对账', rule: '旧角色逐菜单、按钮、数据范围、敏感字段映射并由负责人签字确认' },
  { key: 'room', label: '房态对账', rule: '迁移窗口内校验预订区间不重叠、在住房间与入住单一致' },
  { key: 'stock', label: '库存对账', rule: '按物料、仓库、批次核对期初、出入库累计和结存' }
]

