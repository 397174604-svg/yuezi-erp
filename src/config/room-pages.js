const stores = ['中心广场旗舰店', '黄河路轻奢店']

export const roomTypes = [
  '豪华套房', '舒适大床', '温馨雅间', '尊享套房', '舒适小套', '5楼VIP', '3楼VIP', '臻享套房',
  '至尊女王', '精致尊享A', '精致尊享B', '总统套房', '基础套餐', '修复套餐', '修养套餐',
  '私享套餐', '女王套餐 （私人定制）', '总统套餐 （私人定制）'
]

const input = (key, label, placeholder = '') => ({ key, label, type: 'input', placeholder })
const number = (key, label) => ({ key, label, type: 'number' })
const select = (key, label, options, placeholder = '请选择') => ({ key, label, type: 'select', options, placeholder })
const date = (key, label) => ({ key, label, type: 'date' })
const dateRange = (key, label) => ({ key, label, type: 'dateRange' })
const checkboxGroup = (key, label, options) => ({ key, label, type: 'checkboxGroup', options })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required })
const col = (key, label, width, tag = false, money = false, hidden = false) => ({ key, label, width, tag, money, hidden })

const today = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const addDays = amount => {
  const value = new Date()
  value.setDate(value.getDate() + amount)
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const bookingFields = [
  input('customerName', '客户姓名'),
  input('mobile', '联系电话'),
  select('store', '门店', stores),
  input('room', '房间号'),
  select('roomType', '房型', roomTypes),
  date('plannedCheckInAt', '预住日期'),
  date('plannedCheckOutAt', '预离开日期'),
  number('plannedDays', '预住天数'),
  textarea('remark', '备注')
]

const auditFields = [
  select('auditResult', '审核结果', ['审核通过', '审核不通过']),
  input('auditor', '审核人'),
  textarea('auditOpinion', '审核意见', true)
]

export const roomPageConfigs = {
  房态图: {
    key: 'room-map',
    mode: 'room-map',
    icon: 'el-icon-office-building',
    description: '按门店、房型、朝向、楼层和展示类型查看实时房态。',
    actions: [
      '商品销售', '订房', '入住', '续住', '换房', '退房', '结账',
      '入住通知单', '客房服务申请', '服务预约', '房型订房', '维修/脏房',
      '跨店订房', '跨店换房'
    ],
    filters: [
      input('room', '房号'),
      select('store', '门店', stores),
      select('roomType', '房型', roomTypes),
      select('direction', '朝向', ['东', '西', '南', '北']),
      input('floor', '楼层', '楼层数'),
      select('displayType', '类型', ['按楼层', '按房型'])
    ],
    defaultFilters: { store: stores[0], displayType: '按楼层' },
    formFields: bookingFields
  },
  房态趋势: {
    key: 'room-trend',
    mode: 'timeline',
    icon: 'el-icon-date',
    description: '按房号或房型展示入住、预订、空闲与换房时间轴。',
    actions: [],
    queryActions: ['导出'],
    filters: [
      select('store', '门店', stores),
      select('roomType', '房间类型', roomTypes),
      select('changeType', '类型', ['全部', '不换房', '换房']),
      select('sortType', '排序字段', ['按房号', '按类型']),
      select('stayStatus', '状态', ['全部', '未入住', '已入住']),
      date('startDate', '时间段'),
      number('days', '天'),
      date('endDate', '结束日期')
    ],
    defaultFilters: { store: stores[0], changeType: '全部', sortType: '按房号', stayStatus: '全部', startDate: today(), days: 28, endDate: addDays(28) }
  },
  房型趋势: {
    key: 'room-type-trend',
    mode: 'occupancy',
    icon: 'el-icon-data-line',
    description: '按门店和预定时间查看每日房型剩余数及余房占比。',
    actions: [],
    filters: [
      select('store', '门店', stores),
      date('startDate', '预定时间'),
      number('days', '天'),
      date('endDate', '结束日期'),
      checkboxGroup('occupancyTypes', '房型占用数', ['入住客户数', '订房客户数', '维修（占用）房数', '合同预住数'])
    ],
    defaultFilters: {
      store: stores[0],
      startDate: today(),
      days: 28,
      endDate: addDays(28),
      occupancyTypes: ['入住客户数', '订房客户数', '维修（占用）房数', '合同预住数']
    }
  },
  智能排房: {
    key: 'smart-allocation',
    mode: 'smart-allocation',
    icon: 'el-icon-guide',
    description: '按分店、入住日期、房间类型和楼层生成无需换房或一次换房的推荐方案。',
    actions: [],
    filters: [
      select('store', '分店', stores),
      date('startDate', '入住日期'),
      number('days', '天'),
      date('endDate', '退房日期'),
      select('roomType', '房间类型', roomTypes, '请选择'),
      input('floor', '楼层')
    ],
    defaultFilters: { store: stores[0], startDate: today(), days: 28, endDate: addDays(28), roomType: '', floor: '' }
  },
  可售房统计: {
    key: 'saleable-statistics',
    mode: 'list',
    icon: 'el-icon-s-data',
    description: '统计指定入住区间内不同连续天数的可售房间。',
    actions: [],
    queryActions: ['导出'],
    filters: [input('room', '房间号'), select('store', '分店', stores), dateRange('stayRange', '入住日期')],
    defaultFilters: { store: stores[0], stayRange: [today(), addDays(28)] },
    columns: [
      col('room', '房间名称'), col('roomStatus', '房间状态', 100, true), col('days28', '28天可售房间数', 150),
      col('days7', '7天可售房间数', 145), col('days10', '10天可售房间数', 150), col('days42', '42天可售房间数', 150)
    ]
  },
  房型列表: {
    key: 'room-type-bookings',
    mode: 'list',
    icon: 'el-icon-house',
    description: '维护按房型预订的客户、入住区间、门店与状态。',
    actions: ['房型订房', '删除'],
    filters: [
      input('customerName', '客户名称'), input('mobile', '联系电话'), select('store', '门店', stores),
      select('roomType', '房型', roomTypes), select('roomTypeStatus', '房型状态', ['正常', '已删除']), dateRange('plannedRange', '预住日期')
    ],
    defaultFilters: { roomTypeStatus: '正常' },
    columns: [
      col('roomType', '房型', 150), col('customerName', '客户姓名'), col('mobile', '联系电话', 130),
      col('store', '门店', 150), col('plannedCheckInAt', '预住日期', 120), col('plannedCheckOutAt', '预离开日期', 120),
      col('plannedDays', '预住天数'), col('roomTypeStatus', '房型状态', 100, true), col('creator', '创建人'),
      col('createdAt', '创建日期', 150), col('remark', '备注', 180)
    ],
    formFields: bookingFields
  },
  订房管理: {
    key: 'room-reservations',
    mode: 'list',
    icon: 'el-icon-tickets',
    description: '管理已落实到具体房号的预约、编辑和退订结账。',
    actions: ['编辑', '退订并结账', '退订'],
    filters: [input('room', '房号'), input('customerName', '客户姓名'), select('store', '门店类别', stores), dateRange('plannedRange', '预住日期')],
    columns: [
      col('room', '房间名称'), col('customerName', '客户姓名'), col('mobile', '客户电话', 130),
      col('plannedCheckInAt', '预住日期', 120), col('plannedCheckOutAt', '预计离开日期', 130),
      col('plannedDays', '预住天数'), col('roomStatus', '房间状态', 100, true), col('creator', '制单人'), col('createdAt', '记录日期', 150),
      col('customerId', '客户ID', 100, false, false, true)
    ],
    formFields: bookingFields
  },
  入住管理: {
    key: 'room-stays',
    mode: 'list',
    icon: 'el-icon-s-home',
    description: '贯通客户入住、续住、换房、取消与房间金额信息。',
    actions: ['导出', '续住', '换房', '取消', '编辑'],
    filters: [
      input('room', '房号'), input('customerName', '客户姓名'), select('store', '门店类别', stores),
      select('roomStatus', '房间状态', ['全部', '入住', '退房', '预约']),
      select('customerStatus', '客户状态', ['全部', '正入住', '已预约', '已退房']), dateRange('checkInRange', '入住时间')
    ],
    defaultFilters: { customerStatus: '正入住' },
    columns: [
      col('room', '房间名称'), col('customerName', '客户姓名'), col('contractStore', '合同分店', 150), col('contractAmount', '合同金额', 110, false, true),
      col('contractDays', '合同天数'), col('store', '入住分店', 150), col('roomDays', '房间天数'), col('checkInAt', '入住日期', 150),
      col('checkOutAt', '离开日期', 150), col('dailyAmount', '间天金额', 105, false, true), col('balanceAmount', '余款金额', 105, false, true),
      col('roomStatus', '房间状态', 100, true), col('creator', '制单人'), col('reservedAt', '预定日期', 150),
      col('changedRoom', '换房号'), col('extensionDays', '续住天数'), col('extensionAt', '续住日期', 150),
      col('extensionAmount', '续住金额', 105, false, true), col('receivedExtensionAmount', '已付续住款', 115, false, true)
    ],
    formFields: bookingFields
  },
  续住信息: {
    key: 'stay-extensions',
    mode: 'list',
    icon: 'el-icon-refresh-right',
    description: '管理月子、到家、外出和退房续住记录及审核状态。',
    actions: ['删除', '取消', '编辑', '审核', '反审核'],
    filters: [
      input('room', '房号'), input('customerName', '客户姓名'), select('store', '门店类别', stores),
      select('auditStatus', '审核状态', ['全部', '待审核', '已审核']),
      select('extensionStatus', '续住状态', ['全部', '待续住', '已续住']),
      select('customerType', '客户类型', ['全部', '正入住', '已退房']),
      select('extensionType', '续住类型', ['全部', '月子续住', '到家续住', '外出续住', '退房续住']),
      dateRange('extensionRange', '续住日期'), dateRange('signedRange', '签单日期'), { key: 'homeCustomer', label: '到家客户', type: 'checkbox' }
    ],
    defaultFilters: { customerType: '正入住' },
    columns: [
      col('room', '房间号'), col('customerName', '客户姓名'), col('mobile', '客户电话', 130),
      col('extensionAmount', '续住金额', 105, false, true), col('receivedAmount', '已收款', 100, false, true),
      col('unpostedAmount', '未入账金额', 110, false, true), col('debtAmount', '欠款金额', 100, false, true),
      col('extensionDays', '续住天数'), col('startAt', '续住开始日期', 130), col('endAt', '续住结束日期', 130),
      col('remark', '续住说明', 170), col('salesperson', '签单人'), col('extensionSalesperson', '续住签单人', 110),
      col('createdAt', '制单日期', 150), col('signedAt', '签单日期', 150), col('status', '状态', 95, true),
      col('auditStatus', '审核状态', 100, true), col('auditedAt', '审核时间', 150), col('auditor', '审核人'),
      col('attachment', '附件'), col('extensionType', '续住类型'), col('extensionStatus', '续住状态', 100, true)
    ],
    formFields: [
      input('customerName', '客户姓名'), input('room', '房间号'), select('extensionType', '续住类型', ['月子续住', '到家续住', '外出续住', '退房续住']),
      number('extensionDays', '续住天数'), date('startAt', '续住开始日期'), date('endAt', '续住结束日期'),
      number('extensionAmount', '续住金额'), input('extensionSalesperson', '续住签单人'), textarea('remark', '续住说明')
    ],
    auditFields
  },
  换房申请: {
    key: 'room-change-applications',
    mode: 'list',
    icon: 'el-icon-sort',
    description: '审核客户换房房间、时间、事由和申请轨迹。',
    actions: ['审核', '反审核', '删除'],
    filters: [input('customerName', '客户名称'), select('auditStatus', '审核状态', ['待审核', '审核通过']), dateRange('changeRange', '换房时间')],
    columns: [
      col('customerName', '客户姓名'), col('mobile', '手机号', 130), col('room', '房间号'), col('targetRoom', '换房房间'),
      col('changedAt', '换房时间', 150), col('reason', '换房事由', 180), col('auditStatus', '审核状态', 100, true),
      col('auditor', '审核人'), col('auditOpinion', '审核意见', 170), col('auditedAt', '审核时间', 150),
      col('applicant', '申请人'), col('appliedAt', '申请时间', 150)
    ],
    formFields: [input('customerName', '客户姓名'), input('room', '原房间号'), input('targetRoom', '换房房间'), date('changedAt', '换房时间'), textarea('reason', '换房事由', true)],
    auditFields
  },
  物品赠送: {
    key: 'gift-distribution',
    mode: 'list',
    icon: 'el-icon-present',
    description: '按合同和房间跟踪入住物品是否已经发放。',
    actions: ['物品发放'],
    filters: [input('customerName', '客户姓名'), select('giftStatus', '是否赠送', ['未赠送', '已赠送'])],
    columns: [
      col('contractName', '合同名称', 160), col('room', '房间号'), col('customerName', '客户姓名'), col('plannedCheckInAt', '预住日期', 120),
      col('auditStatus', '审核状态', 100, true), col('salesperson', '签单人'), col('department', '签单人部门', 120),
      col('giftStatus', '是否赠送', 100, true), col('customGift', '自定义赠送', 160), col('store', '合同分店', 150)
    ],
    formFields: [input('customerName', '客户姓名'), input('room', '房间号'), input('contractName', '合同名称'), textarea('giftItems', '发放物品', true), date('issuedAt', '发放时间'), input('issuer', '发放人'), textarea('remark', '备注')]
  },
  客房服务: {
    key: 'room-services',
    mode: 'list',
    icon: 'el-icon-service',
    description: '管理房间清洁、擦身和房态设置类服务申请。',
    actions: ['确认完成', '取消', '预约确认'],
    filters: [
      input('room', '房间名称'), input('customerName', '申请客户'),
      select('serviceStatus', '服务状态', ['已完成服务', '未完成服务', '已确认预约', '已取消']),
      select('store', '门店', stores)
    ],
    columns: [
      col('room', '房间号'), col('customerName', '申请客户'), col('roomType', '房间类型', 140), col('roomStyle', '房间风格', 140),
      col('serviceType', '服务类型', 130), col('appliedAt', '申请时间', 150), col('serviceStatus', '服务状态', 110, true),
      col('remark', '备注', 180), col('serviceStaff', '服务人员'), col('serviceAt', '服务时间', 150)
    ],
    formFields: [input('room', '房间号'), input('customerName', '申请客户'), input('serviceType', '服务类型'), date('appliedAt', '申请时间'), textarea('remark', '备注')]
  },
  外出申请: {
    key: 'outing-applications',
    mode: 'list',
    icon: 'el-icon-position',
    description: '记录妈妈或新生儿外出、审核与返回时间。',
    actions: ['添加', '编辑', '删除', '审核', '确定已返回', '打印'],
    filters: [
      input('customerName', '客户姓名'),
      select('outingStatus', '外出状态', ['从未被审核', '审核已通过', '已返回', '审核不通过']),
      dateRange('outingRange', '外出时间')
    ],
    columns: [
      col('customerName', '外出客户'), col('outingAt', '外出时间', 220), col('outingDays', '外出天数'),
      col('reason', '外出原因', 190), col('escort', '外出陪护人'), col('department', '制单部门', 120),
      col('createdAt', '制单时间', 150), col('creator', '制单人'), col('outingStatus', '审核状态', 110, true),
      col('personType', '外出人类型'), col('returnedAt', '返回时间', 150), col('store', '分店', 150)
    ],
    formFields: [
      input('customerName', '外出客户'), select('personType', '外出人类型', ['产妇', '新生儿']), date('startAt', '外出开始时间'),
      date('endAt', '预计返回时间'), number('outingDays', '外出天数'), input('escort', '外出陪护人'),
      select('store', '分店', stores), textarea('reason', '外出原因', true)
    ],
    auditFields
  },
  物品借还: {
    key: 'borrowed-items',
    mode: 'list',
    icon: 'el-icon-box',
    description: '管理住客借用物品、押金租金、归还与签收。',
    actions: ['添加', '编辑', '删除', '确认签收', '打印'],
    filters: [
      input('customerName', '客户名称'), select('returnStatus', '状态', ['已还', '未还']),
      select('store', '分店', stores), dateRange('borrowRange', '借物品时间')
    ],
    columns: [
      col('room', '房间号'), col('customerName', '客户姓名'), col('borrowedAt', '借物品时间', 150),
      col('creator', '录入业务员'), col('remark', '备注', 180), col('returnStatus', '是否归还', 100, true),
      col('expectedReturnAt', '预归还时间', 150), col('signedAt', '签收时间', 150), col('signer', '签收人'),
      col('store', '分店', 150), col('deposit', '物品押金', 100, false, true), col('depositPaid', '押金是否收款', 110, true),
      col('rent', '物品租金', 100, false, true), col('rentPaid', '租金是否收款', 110, true)
    ],
    formFields: [
      input('room', '房间号'), input('customerName', '客户姓名'), input('itemName', '借用物品'), date('borrowedAt', '借物品时间'),
      date('expectedReturnAt', '预归还时间'), number('deposit', '物品押金'), number('rent', '物品租金'), select('store', '分店', stores), textarea('remark', '备注')
    ]
  },
  洗衣管理: {
    key: 'laundry',
    mode: 'list',
    icon: 'el-icon-brush',
    description: '登记住客衣物送洗要求、签收状态和操作人员。',
    actions: ['添加', '编辑', '删除', '确认签收'],
    filters: [input('customerName', '客户名称'), dateRange('laundryRange', '送洗时间')],
    columns: [
      col('room', '房间号'), col('department', '送洗部门'), col('customerName', '客户名称'), col('sentAt', '送洗时间', 150),
      col('specialRequirement', '特殊要求', 160), col('signStatus', '签收状态', 100, true), col('signer', '签收人姓名'),
      col('signedAt', '签收时间', 150), col('remark', '备注', 180), col('creator', '录入人员')
    ],
    formFields: [
      input('room', '房间号'), input('department', '送洗部门'), input('customerName', '客户名称'), date('sentAt', '送洗时间'),
      input('specialRequirement', '特殊要求'), textarea('remark', '备注')
    ]
  }
}

export function getRoomPageConfig(title) {
  return roomPageConfigs[title] || roomPageConfigs.房态图
}
