const fs = require('fs')
const path = require('path')
const {
  confirmedPackageCatalog,
  confirmedCenterRoomSlots,
  confirmedYellowRiverRoomSlots,
  roomInventoryEvidence
} = require('./client-confirmed-data')

const stores = [
  { id: 1, name: '中心广场旗舰店' },
  { id: 2, name: '黄河路轻奢店' }
]

const customerNames = ['李女士', '王女士', '张女士', '赵女士', '陈女士', '刘女士', '杨女士', '周女士']
const staffNames = ['李顾问', '王顾问', '张护士', '赵主管', '陈管家', '刘营养师', '杨技师', '周店长']
const roomNumbers = ['201', '203', '205', '207', '211', '208', 'VIP302', 'VIP512']
const serviceNames = ['产后恢复基础护理', '宝宝沐浴抚触', '月子营养餐', '乳房疏通护理', '客房深度清洁', '产康体态评估', '新生儿健康观察', '妈妈情绪关怀']
const materialNames = ['产妇护理包', '宝宝洗护套装', '月子服', '消毒湿巾', '纸尿裤', '营养汤料包', '无菌纱布', '客房清洁套装']
const statusCycle = ['待审核', '审核通过', '进行中', '已完成', '启用', '正常', '待处理', '已发布']
const contractTypes = ['月子合同', '婴儿托管', '试住合同', '续住合同', '小月子合同', '到家合同']
const receiptTypes = ['合同首付', '合同补余收款', '合同收款', '其他收款', '续房收款', '服务升级收款', '销售收款', '产康合同收款', '月嫂合同收款']
const paymentMethods = ['现金', '银行卡', '微信', '支付宝', '转账']
const customerStages = ['新线索', '跟进中', '已到店']
const customerIntentLevels = ['A', 'B', 'C', 'D', 'E']
const customerTypes = ['孕期待产', '已分娩', '非孕产服务']

const configFiles = {
  customer: 'customer-pages.js',
  sales: 'sales-pages.js',
  finance: 'finance-pages.js',
  room: 'room-pages.js',
  nursing: 'nursing-pages.js',
  rehab: 'rehab-pages.js',
  'maternity-nurse': 'maternity-nurse-pages.js',
  diet: 'diet-pages.js',
  inventory: 'inventory-pages.js',
  mall: 'mall-pages.js',
  risk: 'risk-pages.js',
  report: 'report-pages.js',
  basic: 'basic-pages.js',
  system: 'system-pages.js'
}

const alwaysAvailableFields = [
  'id', 'code', 'name', 'title', 'status', 'auditStatus', 'customerName', 'mobile', 'store', 'department',
  'room', 'roomNo', 'salesperson', 'creator', 'createdAt', 'updatedAt', 'remark', 'amount', 'totalAmount',
  'quantity', 'unit', 'service', 'silver', 'gold', 'sequence', 'riskNo', 'sourceModule', 'eventSummary',
  'businessObject', 'riskLevel', 'occurredAt', 'owner', 'lastAction', 'nextActionAt', 'ruleCode', 'ruleName',
  'triggerSummary', 'enabled', 'updatedBy'
]

function fieldsForDomain(domain) {
  const fileName = configFiles[domain]
  const fields = new Set(alwaysAvailableFields)
  if (fileName) {
    try {
      const source = fs.readFileSync(path.join(process.cwd(), 'src', 'config', fileName), 'utf8')
      const pattern = /(?:col|text|money|dateColumn|status|numberColumn|draftColumn|column)\('([^']+)'/g
      let match
      while ((match = pattern.exec(source))) fields.add(match[1])
    } catch (error) {
      // The common field set still keeps the local demo usable if a config file moves.
    }
  }
  if (domain === 'maternity-nurse') {
    for (let index = 1; index <= 48; index += 1) fields.add(`field_${index}`)
  }
  return Array.from(fields)
}

const fieldsByDomain = Object.keys(configFiles).reduce((result, domain) => {
  result[domain] = fieldsForDomain(domain)
  return result
}, {})

function dateText(index, includeTime = false) {
  const day = String(20 + (index % 8)).padStart(2, '0')
  return includeTime ? `2026-07-${day} ${String(8 + (index % 9)).padStart(2, '0')}:30` : `2026-07-${day}`
}

function currentDateText() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}

function dateDays(start, end) {
  if (!start || !end) return 0
  return Math.round((
    new Date(`${end}T00:00:00`).getTime() -
    new Date(`${start}T00:00:00`).getTime()
  ) / 86400000)
}

function codeText(field, domain, resource, index) {
  const prefix = String(resource || domain).replace(/[^a-z0-9]/gi, '').slice(0, 6).toUpperCase() || 'ERP'
  return `${prefix}-${String(index + 1).padStart(4, '0')}`
}

function valueForField(field, index, domain, resource) {
  const lower = field.toLowerCase()
  const store = stores[index % stores.length].name
  const status = statusCycle[index % statusCycle.length]

  if (field === 'id') return `${domain}-${resource}-${index + 1}`
  if (field === 'sequence') return index + 1
  if (/^field_\d+$/.test(field)) return `演示字段 ${field.split('_')[1]}-${index + 1}`
  if (field === 'customerName' || field === 'customer' || field === 'clueName' || field === 'name') return customerNames[index % customerNames.length]
  if (/babyName|babyAlias/i.test(field)) return `宝宝${String.fromCharCode(65 + index)}`
  if (/mobile|phone/i.test(field)) return `138****${String(2100 + index * 37).slice(-4)}`
  if (field === 'store' || /store$/i.test(field)) return store
  if (field === 'room' || field === 'roomNo' || /room$/i.test(field)) return roomNumbers[index % roomNumbers.length]
  if (/salesperson|staffName|employeeName|nurseName|doctorName|technician|operator|creator|auditor|applicant|owner|manager|recorder|publisher|updatedBy|cashier|receiver|payee|teacher|expert|assessor|rounder|handler/i.test(field)) return staffNames[index % staffNames.length]
  if (/department/i.test(field)) return ['销售部', '护理部', '财务部', '产康部'][index % 4]
  if (/warehouse/i.test(field)) return ['中心仓', '护理用品仓', '膳食原料仓'][index % 3]
  if (/supplier/i.test(field)) return ['安康母婴供应商', '优选膳食供应商', '洁净客房供应商'][index % 3]
  if (/materialName/i.test(field)) return materialNames[index % materialNames.length]
  if (/itemName|projectName|serviceName|serviceItem|dishName|taskName|templateName|packageName|className|productName|expenseName|contentTitle/i.test(field)) return serviceNames[index % serviceNames.length]
  if (/sourceModule/i.test(field)) return ['客户', '财务', '客房', '护理'][index % 4]
  if (/source/i.test(field)) return ['客户介绍', '线上咨询', '到店咨询', '渠道合作'][index % 4]
  if (/status|result|enabled|visible|recommended|settled|handled|delivered|checkedIn|directArrival|firstOrder|remoteSign/i.test(field)) return status
  if (/riskLevel|level$/i.test(field)) return ['低', '中', '高'][index % 3]
  if (/type|category|scope|channel|method|mode|direction|orientation/i.test(field)) return ['月子护理', '产康服务', '护理服务', '膳食服务'][index % 4]
  if (/no$|code$|^code$|number$|documentNo|accountNo|contractNo|receiptNo|orderNo|saleNo|planNo|applicationNo|bookingNo|transactionNo/i.test(field)) return codeText(field, domain, resource, index)
  if (/date|at$|time$|period$|birthday|due|start|end|expiry|deadline|effective|occurred|updated|created|signed|opened|published/i.test(lower)) return dateText(index, /at$|time$|updated|created|published|occurred/i.test(lower))
  if (/amount|price|fee|cost|income|debt|balance|payment|received|refund|total|budget|rent|deposit|salary|recharge|grossprofit|netamount|recoverable|payable|outstanding/i.test(lower)) return 1800 + index * 860
  if (/count|quantity|days|score|sort|rate|percent|frequency|duration|age|floor|views|stock|capacity|registrations|points|itemcount|fieldcount|nodecount|retrycount/i.test(lower)) return 2 + index * 3
  if (/unit/i.test(field)) return ['次', '份', '套', '间'][index % 4]
  if (/address|location/i.test(field)) return `${store}三楼服务区`
  if (/remark|description|content|summary|reason|advice|finding|observation|details|rule|requirement|opinion|trail|note/i.test(field)) return `依据设计文档生成的脱敏演示记录 ${index + 1}`
  if (field === 'service') return serviceNames[index % serviceNames.length]
  if (field === 'silver') return index % 2 ? '可用' : '—'
  if (field === 'gold') return '可用'
  return `演示数据 ${index + 1}`
}

function buildRows(domain, resource, count = 8) {
  const fields = fieldsByDomain[domain] || alwaysAvailableFields
  return Array.from({ length: count }, (_, index) => {
    const row = { resource, demoOnly: true }
    fields.forEach(field => {
      row[field] = valueForField(field, index, domain, resource)
    })
    row.id = `${domain}-${resource}-${index + 1}`
    return row
  })
}

const clueFollowStatuses = ['待跟进', '跟进中', '已转化', '已关闭']
const clueState = [
  { id: 'CLUE-001', name: '李女士', mobile: '138****2100', customerMobile: '138****2100', wechat: 'li-demo', source: '客户介绍', salesperson: '李顾问', assignee: '李顾问', creator: '李顾问', store: stores[0].name, followStatus: '待跟进', convertStore: '', sharedBy: '', appointment: '未预约', followCount: 0, followedAt: '', nextFollowAt: '', createdAt: '2026-07-30 08:30', dueDate: '2026-08-18', description: '朋友转介绍，待首次电话联系', autoAssigned: '否', convertedCustomer: '', unfollowedDays: 1 },
  { id: 'CLUE-002', name: '王女士', mobile: '138****2137', customerMobile: '138****2137', wechat: 'wang-demo', source: '线上咨询', salesperson: '王顾问', assignee: '王顾问', creator: '王顾问', store: stores[0].name, followStatus: '跟进中', convertStore: '', sharedBy: '', appointment: '已预约', followCount: 2, followedAt: '2026-07-30 09:30', nextFollowAt: '2026-08-01 10:00', createdAt: '2026-07-28 09:30', dueDate: '2026-09-03', description: '已发送套餐，等待到店参观', autoAssigned: '是', convertedCustomer: '', unfollowedDays: 1 },
  { id: 'CLUE-003', name: '张女士', mobile: '138****2174', customerMobile: '138****2174', wechat: 'zhang-demo', source: '到店咨询', salesperson: '陈顾问', assignee: '陈顾问', creator: '前台', store: stores[1].name, followStatus: '已转化', convertStore: stores[1].name, sharedBy: '', appointment: '已到店', followCount: 4, followedAt: '2026-07-29 10:30', nextFollowAt: '', createdAt: '2026-07-25 10:30', dueDate: '2026-08-26', description: '已完成客户建档并进入合同沟通', autoAssigned: '否', convertedCustomer: 'KH-2026-0026', unfollowedDays: 2 },
  { id: 'CLUE-004', name: '赵女士', mobile: '138****2211', customerMobile: '138****2211', wechat: 'zhao-demo', source: '渠道合作', salesperson: '陈顾问', assignee: '陈顾问', creator: '市场部', store: stores[1].name, followStatus: '已关闭', convertStore: '', sharedBy: '', appointment: '未预约', followCount: 3, followedAt: '2026-07-27 11:30', nextFollowAt: '', createdAt: '2026-07-23 11:30', dueDate: '2026-10-12', description: '客户明确暂不考虑，保留关闭原因', autoAssigned: '否', convertedCustomer: '', unfollowedDays: 4 },
  { id: 'CLUE-005', name: '陈女士', mobile: '138****2248', customerMobile: '138****2248', wechat: 'chen-demo', source: '客户介绍', salesperson: '李顾问', assignee: '李顾问', creator: '李顾问', store: stores[0].name, followStatus: '跟进中', convertStore: '', sharedBy: '王顾问', appointment: '待确认', followCount: 1, followedAt: '2026-07-31 12:30', nextFollowAt: '2026-08-02 14:00', createdAt: '2026-07-30 12:30', dueDate: '2026-09-18', description: '关注大床房和28天套餐', autoAssigned: '否', convertedCustomer: '', unfollowedDays: 0 },
  { id: 'CLUE-006', name: '刘女士', mobile: '138****2285', customerMobile: '138****2285', wechat: 'liu-demo', source: '线上咨询', salesperson: '王顾问', assignee: '王顾问', creator: '客服', store: stores[0].name, followStatus: '待跟进', convertStore: '', sharedBy: '', appointment: '未预约', followCount: 0, followedAt: '', nextFollowAt: '', createdAt: '2026-07-31 13:30', dueDate: '2026-10-05', description: '抖音私信咨询，待分配后首次联系', autoAssigned: '是', convertedCustomer: '', unfollowedDays: 0 },
  { id: 'CLUE-007', name: '杨女士', mobile: '138****2322', customerMobile: '138****2322', wechat: 'yang-demo', source: '到店咨询', salesperson: '陈顾问', assignee: '陈顾问', creator: '前台', store: stores[1].name, followStatus: '跟进中', convertStore: '', sharedBy: '', appointment: '已到店', followCount: 3, followedAt: '2026-07-30 14:30', nextFollowAt: '2026-08-01 15:00', createdAt: '2026-07-27 14:30', dueDate: '2026-09-24', description: '比较35天与42天套餐', autoAssigned: '否', convertedCustomer: '', unfollowedDays: 1 },
  { id: 'CLUE-008', name: '周女士', mobile: '138****2359', customerMobile: '138****2359', wechat: 'zhou-demo', source: '自然上门', salesperson: '陈顾问', assignee: '陈顾问', creator: '前台', store: stores[1].name, followStatus: '已转化', convertStore: stores[1].name, sharedBy: '', appointment: '已到店', followCount: 5, followedAt: '2026-07-31 15:30', nextFollowAt: '', createdAt: '2026-07-22 15:30', dueDate: '2026-08-30', description: '已转客户，等待合同签订', autoAssigned: '否', convertedCustomer: 'KH-2026-0031', unfollowedDays: 0 }
]

const couponTemplateState = [
  { id: 'COUPON-T-001', couponNo: 'YHQ-2026-0001', couponName: '新客签约现金券', couponType: '现金券', itemType: '月子护理', couponAmount: 300, store: stores[0].name, startsAt: '2026-07-01', endsAt: '2026-12-31', totalQuantity: 200, issuedQuantity: 42, limitPerCustomer: 1, limitType: '项目', consumeType: '护理服务', consumeItem: '', stackable: false, scope: '所有人', sendType: '店内发放', remark: '中心店签约活动使用', creator: 'admin', createdAt: '2026-07-20 09:20' },
  { id: 'COUPON-T-002', couponNo: 'YHQ-2026-0002', couponName: '产康体验券', couponType: '体验券', itemType: '产康服务', couponAmount: 500, store: stores[0].name, startsAt: '2026-07-01', endsAt: '2026-10-31', totalQuantity: 100, issuedQuantity: 18, limitPerCustomer: 1, limitType: '项目', consumeType: '产康服务', consumeItem: '产后恢复体验', stackable: false, scope: '所有人', sendType: '店内发放', remark: '仅限指定产康体验项目', creator: 'admin', createdAt: '2026-07-21 10:10' },
  { id: 'COUPON-T-003', couponNo: 'YHQ-2026-0003', couponName: '黄河路入住礼券', couponType: '商品券', itemType: '物料商品', couponAmount: 200, store: stores[1].name, startsAt: '2026-07-15', endsAt: '2026-12-31', totalQuantity: 120, issuedQuantity: 21, limitPerCustomer: 1, limitType: '商品', consumeType: '物料商品', consumeItem: '入住礼包', stackable: false, scope: '所有人', sendType: '店内发放', remark: '黄河路店入住客户使用', creator: 'admin', createdAt: '2026-07-22 11:15' }
]

const customerDiscountState = [
  { id: 'DISCOUNT-001', templateId: 'COUPON-T-001', discountNo: 'KHYH-2026-0001', customerName: '李女士', mobile: '13800138001', couponName: '新客签约现金券', couponType: '现金券', itemType: '月子护理', quantity: 1, couponAmount: 300, usedAmount: 0, remainingAmount: 300, startsAt: '2026-07-01', deadline: '2026-12-31', auditStatus: '待审核', auditor: '', auditRemark: '', status: '待审核', saleNo: '', usedAt: '', operationTrail: '2026-07-30 09:30 李顾问发放 1 张', remark: '签约活动', creator: '李顾问', createdAt: '2026-07-30 09:30', store: stores[0].name, disableReason: '' },
  { id: 'DISCOUNT-002', templateId: 'COUPON-T-002', discountNo: 'KHYH-2026-0002', customerName: '王女士', mobile: '13800138002', couponName: '产康体验券', couponType: '体验券', itemType: '产康服务', quantity: 1, couponAmount: 500, usedAmount: 0, remainingAmount: 500, startsAt: '2026-07-01', deadline: '2026-10-31', auditStatus: '已通过', auditor: 'admin', auditRemark: '活动范围符合', status: '未使用', saleNo: '', usedAt: '', operationTrail: '2026-07-30 10:20 admin审核通过', remark: '', creator: '王顾问', createdAt: '2026-07-30 10:00', store: stores[0].name, disableReason: '' },
  { id: 'DISCOUNT-003', templateId: 'COUPON-T-003', discountNo: 'KHYH-2026-0003', customerName: '张女士', mobile: '13800138003', couponName: '黄河路入住礼券', couponType: '商品券', itemType: '物料商品', quantity: 1, couponAmount: 200, usedAmount: 0, remainingAmount: 200, startsAt: '2026-07-15', deadline: '2026-12-31', auditStatus: '已通过', auditor: 'admin', auditRemark: '审核通过', status: '未使用', saleNo: '', usedAt: '', operationTrail: '2026-07-30 11:10 admin审核通过', remark: '', creator: '周店长', createdAt: '2026-07-30 11:00', store: stores[1].name, disableReason: '' }
]

function currentDateTimeText() {
  const now = new Date()
  const pad = value => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`
}

function couponTemplateRows() {
  const today = currentDateText()
  return couponTemplateState.map(item => ({
    ...item,
    remainingQuantity: Math.max(0, Number(item.totalQuantity || 0) - Number(item.issuedQuantity || 0)),
    status: item.endsAt < today ? '已到期' : Number(item.issuedQuantity || 0) >= Number(item.totalQuantity || 0) ? '已发完' : item.startsAt > today ? '未开始' : '发行中'
  }))
}

function appendOperationTrail(record, text) {
  record.operationTrail = [record.operationTrail, `${currentDateTimeText()} ${text}`].filter(Boolean).join('；')
}

function demoModuleRows(domain, resource) {
  if (domain === 'customer' && resource === 'clues') return clueState.map(item => ({ ...item }))
  if (domain === 'sales' && resource === 'coupons') return couponTemplateRows()
  if (domain === 'sales' && resource === 'discounts') return customerDiscountState.map(item => ({ ...item }))
  return buildRows(domain, resource)
}

function saveDemoModuleRecord(config) {
  const { domain, resource } = moduleContext(config)
  const body = requestBody(config)
  if (domain === 'sales' && resource === 'coupons') {
    const couponAmount = Number(body.couponAmount)
    const totalQuantity = Number(body.totalQuantity)
    const limitPerCustomer = Number(body.limitPerCustomer)
    const startsAt = String(body.startsAt || '').slice(0, 10)
    const endsAt = String(body.endsAt || '').slice(0, 10)
    if (!body.couponName || !body.couponType || !body.store) return mvpError('请补齐优惠券名称、类型和所属门店')
    if (!(couponAmount > 0)) return mvpError('优惠券金额必须大于 0')
    if (!Number.isInteger(totalQuantity) || totalQuantity <= 0) return mvpError('优惠券数量必须为大于 0 的整数')
    if (!Number.isInteger(limitPerCustomer) || limitPerCustomer <= 0) return mvpError('单客户限领数量必须为大于 0 的整数')
    if (!startsAt || !endsAt || startsAt > endsAt) return mvpError('优惠开始时间不能晚于结束时间')
    let record = couponTemplateState.find(item => item.id === body.id)
    if (record && totalQuantity < Number(record.issuedQuantity || 0)) return mvpError('优惠券总数量不能小于已发放数量')
    if (record) {
      Object.assign(record, body, { couponAmount, totalQuantity, limitPerCustomer, startsAt, endsAt })
    } else {
      record = {
        ...body,
        id: `COUPON-T-${String(couponTemplateState.length + 1).padStart(3, '0')}`,
        couponNo: `YHQ-${currentDateText().slice(0, 4)}-${String(couponTemplateState.length + 1).padStart(4, '0')}`,
        couponAmount,
        totalQuantity,
        issuedQuantity: 0,
        limitPerCustomer,
        startsAt,
        endsAt,
        itemType: body.consumeType || body.limitType || '通用',
        creator: '当前用户',
        createdAt: currentDateTimeText()
      }
      couponTemplateState.unshift(record)
    }
    return { code: 20000, data: { ...record }, message: '优惠券配置已保存' }
  }
  if (domain === 'sales' && resource === 'discounts') {
    const couponAmount = Number(body.couponAmount)
    if (!body.customerName || !/^1[3-9]\d{9}$/.test(String(body.mobile || ''))) return mvpError('请填写客户姓名和正确的 11 位手机号')
    if (!body.couponName || !body.couponType || !body.store || !(couponAmount > 0)) return mvpError('请补齐优惠券名称、类型、金额和所属门店')
    let record = customerDiscountState.find(item => item.id === body.id)
    if (record) {
      Object.assign(record, body, { couponAmount })
      appendOperationTrail(record, '当前用户编辑')
    } else {
      record = {
        ...body,
        id: `DISCOUNT-${String(customerDiscountState.length + 1).padStart(3, '0')}`,
        discountNo: body.discountNo || `KHYH-${currentDateText().slice(0, 4)}-${String(customerDiscountState.length + 1).padStart(4, '0')}`,
        quantity: Number(body.quantity || 1),
        couponAmount,
        usedAmount: 0,
        remainingAmount: couponAmount * Number(body.quantity || 1),
        deadline: String(body.endsAt || '').slice(0, 10),
        auditStatus: '待审核',
        auditor: '',
        auditRemark: '',
        status: '待审核',
        saleNo: '',
        usedAt: '',
        operationTrail: `${currentDateTimeText()} 当前用户录入`,
        creator: '当前用户',
        createdAt: currentDateTimeText(),
        disableReason: ''
      }
      customerDiscountState.unshift(record)
    }
    return { code: 20000, data: { ...record }, message: '客户优惠记录已保存' }
  }
  if (domain !== 'customer' || resource !== 'clues') {
    return {
      code: 20000,
      data: { id: body.id || `DEMO-${Date.now()}`, action: 'save', demoOnly: true, processedAt: Date.now() },
      message: '操作成功'
    }
  }
  let record = clueState.find(item => item.id === body.id)
  if (record) {
    Object.assign(record, body)
  } else {
    record = {
      id: `CLUE-${String(clueState.length + 1).padStart(3, '0')}`,
      name: body.name,
      mobile: body.mobile,
      customerMobile: body.mobile,
      wechat: body.wechat || '',
      source: body.source || '其他',
      salesperson: body.assignee || '待分配',
      assignee: body.assignee || '待分配',
      creator: '当前用户',
      store: body.store || stores[0].name,
      followStatus: '待跟进',
      convertStore: '',
      sharedBy: '',
      appointment: '未预约',
      followCount: 0,
      followedAt: '',
      nextFollowAt: '',
      createdAt: new Date().toISOString().slice(0, 16).replace('T', ' '),
      dueDate: body.dueDate || '',
      description: body.description || '',
      autoAssigned: '否',
      convertedCustomer: '',
      unfollowedDays: 0
    }
    clueState.unshift(record)
  }
  return { code: 20000, data: { ...record }, message: '线索已保存' }
}

function performDemoModuleAction(config) {
  const { domain, resource } = moduleContext(config)
  const body = requestBody(config)
  if (domain === 'sales' && resource === 'coupons') {
    const ids = Array.isArray(body.ids) ? body.ids : []
    if (!ids.length) return mvpError('请选择优惠券')
    if (body.action === '删除') {
      const issuedTemplate = couponTemplateState.find(item => ids.includes(item.id) && Number(item.issuedQuantity || 0) > 0)
      if (issuedTemplate) return mvpError(`“${issuedTemplate.couponName}”已有发放记录，不能删除`)
      let removed = 0
      for (let index = couponTemplateState.length - 1; index >= 0; index -= 1) {
        if (ids.includes(couponTemplateState[index].id)) {
          couponTemplateState.splice(index, 1)
          removed += 1
        }
      }
      return removed ? { code: 20000, data: { ids, removed }, message: '优惠券配置已删除' } : mvpError('未找到可删除的优惠券')
    }
    if (body.action === '分发') {
      if (ids.length !== 1) return mvpError('每次只能选择一种优惠券进行分发')
      const template = couponTemplateState.find(item => item.id === ids[0])
      const quantity = Number(body.quantity)
      const today = currentDateText()
      if (!template) return mvpError('未找到优惠券配置')
      if (!body.customerName || !/^1[3-9]\d{9}$/.test(String(body.mobile || ''))) return mvpError('请填写客户姓名和正确的 11 位手机号')
      if (!Number.isInteger(quantity) || quantity <= 0) return mvpError('发放数量必须为大于 0 的整数')
      if (template.startsAt > today || template.endsAt < today) return mvpError('当前优惠券不在可发放有效期内')
      if (Number(template.issuedQuantity || 0) + quantity > Number(template.totalQuantity || 0)) return mvpError('发放数量超过剩余可发数量')
      const received = customerDiscountState
        .filter(item => item.templateId === template.id && item.mobile === body.mobile && item.status !== '已停用')
        .reduce((sum, item) => sum + Number(item.quantity || 0), 0)
      if (received + quantity > Number(template.limitPerCustomer || 1)) return mvpError(`该客户最多可领取 ${template.limitPerCustomer} 张`)
      const record = {
        id: `DISCOUNT-${String(customerDiscountState.length + 1).padStart(3, '0')}`,
        templateId: template.id,
        discountNo: `KHYH-${currentDateText().slice(0, 4)}-${String(customerDiscountState.length + 1).padStart(4, '0')}`,
        customerName: body.customerName,
        mobile: body.mobile,
        couponName: template.couponName,
        couponType: template.couponType,
        itemType: template.itemType,
        quantity,
        couponAmount: Number(template.couponAmount),
        usedAmount: 0,
        remainingAmount: Number(template.couponAmount) * quantity,
        startsAt: template.startsAt,
        deadline: template.endsAt,
        auditStatus: '待审核',
        auditor: '',
        auditRemark: '',
        status: '待审核',
        saleNo: '',
        usedAt: '',
        operationTrail: `${currentDateTimeText()} 当前用户发放 ${quantity} 张`,
        remark: body.remark || '',
        creator: '当前用户',
        createdAt: currentDateTimeText(),
        store: template.store,
        disableReason: ''
      }
      template.issuedQuantity = Number(template.issuedQuantity || 0) + quantity
      customerDiscountState.unshift(record)
      return { code: 20000, data: { ...record }, message: '优惠券已发放，等待审核' }
    }
    return { code: 20000, data: { ids, action: body.action, processedAt: Date.now() }, message: '操作成功' }
  }
  if (domain === 'sales' && resource === 'discounts') {
    const ids = Array.isArray(body.ids) ? body.ids : []
    if (!ids.length) return mvpError('请选择客户优惠记录')
    const selected = customerDiscountState.filter(item => ids.includes(item.id))
    if (!selected.length) return mvpError('未找到客户优惠记录')
    if (body.action === '删除') {
      const used = selected.find(item => Number(item.usedAmount || 0) > 0)
      if (used) return mvpError(`“${used.discountNo}”已有核销流水，不能删除`)
      let removed = 0
      for (let index = customerDiscountState.length - 1; index >= 0; index -= 1) {
        if (ids.includes(customerDiscountState[index].id)) {
          const template = couponTemplateState.find(item => item.id === customerDiscountState[index].templateId)
          if (template) template.issuedQuantity = Math.max(0, Number(template.issuedQuantity || 0) - Number(customerDiscountState[index].quantity || 0))
          customerDiscountState.splice(index, 1)
          removed += 1
        }
      }
      return { code: 20000, data: { ids, removed }, message: '客户优惠记录已删除' }
    }
    if (body.action === '审核') {
      if (!['审核通过', '审核不通过', '通过', '驳回'].includes(body.auditResult)) return mvpError('请选择审核结果')
      const passed = ['审核通过', '通过'].includes(body.auditResult)
      selected.forEach(record => {
        record.auditStatus = passed ? '已通过' : '审核不通过'
        record.status = passed ? '未使用' : '已驳回'
        record.auditor = 'admin'
        record.auditRemark = body.auditRemark || ''
        appendOperationTrail(record, passed ? 'admin审核通过' : 'admin审核不通过')
      })
      return { code: 20000, data: { ids, auditResult: body.auditResult }, message: passed ? '优惠券审核通过' : '优惠券已驳回' }
    }
    if (body.action === '核销') {
      if (selected.length !== 1) return mvpError('每次只能核销一条客户优惠记录')
      const record = selected[0]
      const amount = Number(body.consumeAmount)
      if (record.auditStatus !== '已通过' || !['未使用', '部分使用'].includes(record.status)) return mvpError('仅已审核且未使用完的优惠券可以核销')
      if (record.deadline && record.deadline < currentDateText()) return mvpError('优惠券已过期，不能核销')
      if (!(amount > 0) || amount > Number(record.remainingAmount || 0)) return mvpError('核销金额必须大于 0 且不能超过剩余金额')
      if (!body.saleNo) return mvpError('请填写关联业务单号')
      record.usedAmount = Number(record.usedAmount || 0) + amount
      record.remainingAmount = Number(record.remainingAmount || 0) - amount
      record.saleNo = body.saleNo
      record.usedAt = currentDateTimeText()
      record.status = record.remainingAmount === 0 ? '已核销' : '部分使用'
      appendOperationTrail(record, `核销 ¥${amount.toFixed(2)}，业务单号 ${body.saleNo}${body.remark ? `，${body.remark}` : ''}`)
      return { code: 20000, data: { ...record }, message: record.status === '已核销' ? '优惠券已全部核销' : '优惠券已部分核销' }
    }
    if (body.action === '停用') {
      if (!body.disableReason) return mvpError('请填写停用原因')
      selected.forEach(record => {
        record.status = '已停用'
        record.disableReason = body.disableReason
        appendOperationTrail(record, `停用：${body.disableReason}`)
      })
      return { code: 20000, data: { ids }, message: '优惠券已停用' }
    }
    return { code: 20000, data: { ids, action: body.action, processedAt: Date.now() }, message: '操作成功' }
  }
  if (domain !== 'customer' || resource !== 'clues') {
    return {
      code: 20000,
      data: { id: body.id || `DEMO-${Date.now()}`, action: body.action || 'save', demoOnly: true, processedAt: Date.now() },
      message: '操作成功'
    }
  }
  if (body.action === '删除') {
    const ids = Array.isArray(body.ids) ? body.ids : []
    if (!ids.length) return mvpError('请选择要删除的线索')
    let removed = 0
    for (let index = clueState.length - 1; index >= 0; index -= 1) {
      if (ids.includes(clueState[index].id)) {
        clueState.splice(index, 1)
        removed += 1
      }
    }
    if (!removed) return mvpError('未找到可删除的线索')
    return { code: 20000, data: { ids, removed, action: body.action, processedAt: Date.now() }, message: '线索已删除' }
  }
  const record = clueState.find(item => item.id === body.id)
  if (!record) return mvpError('请选择有效线索')
  if (body.action === '客户跟进' || body.action === '客户跟踪') {
    if (!clueFollowStatuses.includes(body.followStatus)) return mvpError('跟进状态不正确')
    if (!body.followedAt || !body.content) return mvpError('请填写跟进时间和跟进内容')
    if (body.followStatus === '跟进中' && !body.nextFollowAt) return mvpError('跟进中的线索必须填写下次跟进时间')
    record.followStatus = body.followStatus
    record.followedAt = body.followedAt
    record.nextFollowAt = body.nextFollowAt || ''
    record.followContent = body.content
    record.followCount = Number(record.followCount || 0) + 1
    record.unfollowedDays = 0
  } else if (body.action === '转化') {
    record.followStatus = '已转化'
    record.convertStore = body.store || record.store
    record.store = record.convertStore
    record.convertedCustomer = record.convertedCustomer || `KH-TEST-${String(Date.now()).slice(-5)}`
  } else if (body.action === '关闭') {
    if (!body.content) return mvpError('请填写关闭原因')
    record.followStatus = '已关闭'
    record.closeReason = body.content
    record.nextFollowAt = ''
  } else if (body.action.includes('分配') || body.action.includes('转让')) {
    record.assignee = body.assignee || record.assignee
    record.salesperson = record.assignee
    record.store = body.store || record.store
  } else if (body.action === '分享') {
    record.sharedBy = '当前用户'
  }
  return { code: 20000, data: { ...record, action: body.action, processedAt: Date.now() }, message: '操作成功' }
}

function moduleContext(config) {
  const requestPath = config.path || config.url || ''
  const match = requestPath.match(/\/erp\/([^/]+)\/modules\/([^/?]+)/)
  return {
    domain: match ? match[1] : 'system',
    resource: match ? match[2] : 'records'
  }
}

const mvpState = {
  customers: [
    { id: 1, store_id: 1, customer_no: 'KH-2026-0018', name: '李女士', phone: '138****2108', wechat: 'li-demo', store_name: stores[0].name, salesperson: '李顾问', sales_staff_id: 101, source: '客户介绍', intent_level: 'A', customer_type: '孕期待产', edc: '2026-08-16', delivery_date: '', status: '同意签合同', created_at: '2026-07-22 09:18:00' },
    { id: 2, store_id: 1, customer_no: 'KH-2026-0021', name: '王女士', phone: '138****2245', wechat: 'wang-demo', store_name: stores[0].name, salesperson: '王顾问', sales_staff_id: 102, source: '网络搜索', intent_level: 'A', customer_type: '孕期待产', edc: '2026-09-03', delivery_date: '', status: '已订房', created_at: '2026-07-23 10:26:00' },
    { id: 3, store_id: 2, customer_no: 'KH-2026-0026', name: '张女士', phone: '138****2382', wechat: 'zhang-demo', store_name: stores[1].name, salesperson: '周店长', sales_staff_id: 201, source: '自然上门', intent_level: 'B', customer_type: '已分娩', edc: '', delivery_date: '2026-07-20', status: '已入住', created_at: '2026-07-24 14:05:00' },
    { id: 4, store_id: 1, customer_no: 'KH-2026-0030', name: '陈女士', phone: '138****2493', wechat: 'chen-demo', store_name: stores[0].name, salesperson: '李顾问', sales_staff_id: 101, source: '客户介绍', intent_level: 'A', customer_type: '孕期待产', edc: '2026-09-18', delivery_date: '', status: '已审核', created_at: '2026-07-28 15:20:00' }
  ],
  contracts: [
    { id: 1, customer_id: 1, store_id: 1, contract_no: 'HT-2026-0068', customer_name: '李女士', contract_type: '月子合同', package_name: '修养套餐A（28天）', package_no: 'QD-REC-A-28', package_version: '2026-07甲方价目表', reference_amount: 43880, activity_amount: 30999, amount: 27999, discount_rate: 0.6381, paid: 0, unposted_amount: 0, outstanding_amount: 27999, days: 28, expected_check_in: '2026-08-16', expected_check_out: '2026-09-13', sign_date: '2026-07-22', is_backfill: false, backfill_reason: '', status: '已签合同但未审核' },
    { id: 2, customer_id: 2, store_id: 1, contract_no: 'HT-2026-0071', customer_name: '王女士', contract_type: '月子合同', package_name: '精致尊享A（28天）', package_no: 'QD-PREM-A-28', package_version: '2026-07甲方价目表', reference_amount: 52880, activity_amount: 36999, amount: 33999, discount_rate: 0.6429, paid: 23999, unposted_amount: 10000, outstanding_amount: 10000, days: 28, expected_check_in: '2026-08-08', expected_check_out: '2026-09-05', sign_date: '2026-07-23', is_backfill: false, backfill_reason: '', status: '已审核' },
    { id: 3, customer_id: 3, store_id: 2, contract_no: 'HT-2026-0074', customer_name: '张女士', contract_type: '续住合同', package_name: '续住 28 天套餐', reference_amount: 18800, amount: 17800, discount_rate: 0.9468, paid: 17800, unposted_amount: 0, outstanding_amount: 0, days: 28, expected_check_in: '2026-07-22', expected_check_out: '2026-08-19', sign_date: '2026-07-24', is_backfill: false, backfill_reason: '', status: '已审核' },
    { id: 4, customer_id: 4, store_id: 1, contract_no: 'HT-2026-0078', customer_name: '陈女士', contract_type: '月子合同', package_name: '基础套餐（28天）', package_no: 'QD-BASE-28', package_version: '2026-07甲方价目表', reference_amount: 35880, activity_amount: 24999, amount: 21999, discount_rate: 0.6131, paid: 12000, unposted_amount: 0, outstanding_amount: 9999, days: 28, expected_check_in: '2026-09-18', expected_check_out: '2026-10-16', sign_date: '2026-07-28', is_backfill: false, backfill_reason: '', status: '已审核' }
  ],
  receipts: [
    { id: 1, contract_id: 2, store_id: 1, receipt_no: 'SK-2026-0128', customer_name: '王女士', contract_no: 'HT-2026-0071', store_name: stores[0].name, receipt_type: '合同补余收款', amount: 10000, payment_method: '转账', receiver: '赵主管', received_at: '2026-07-25 09:30:00', status: '待审核' },
    { id: 2, contract_id: 2, store_id: 1, receipt_no: 'SK-2026-0131', customer_name: '王女士', contract_no: 'HT-2026-0071', store_name: stores[0].name, receipt_type: '合同首付', amount: 23999, payment_method: '微信', receiver: '赵主管', received_at: '2026-07-25 11:16:00', status: '已审核' }
  ],
  rooms: [
    ...confirmedCenterRoomSlots.map(item => ({ ...item, allocation_blocks: [] })),
    ...confirmedYellowRiverRoomSlots.map(item => ({ ...item, allocation_blocks: [] }))
  ],
  bookings: [
    { id: 1, contract_id: 2, customer_id: 2, room_id: 302, store_id: 1, booking_no: 'DF-2026-0036', customer_name: '王女士', contract_no: 'HT-2026-0071', store_name: stores[0].name, room_no: 'VIP302', check_in: '2026-08-08', check_out: '2026-09-05', status: '已订房', actual_check_in_at: '' }
  ]
}

function mvpOptions() {
  const bookedContractIds = new Set(
    mvpState.bookings
      .filter(item => item.status !== '已取消')
      .map(item => Number(item.contract_id))
  )

  return {
    stores,
    staff: [
      { id: 101, store_id: 1, name: '李顾问', department: '销售部' },
      { id: 102, store_id: 1, name: '王顾问', department: '销售部' },
      { id: 201, store_id: 2, name: '周店长', department: '店务部' }
    ],
    contractTypes,
    receiptTypes,
    paymentMethods,
    packages: catalogPackages
      .filter(item => item.status === '已发布')
      .map(item => ({ ...item })),
    permissions: ['CUSTOMER.VIEW', 'CUSTOMER.CREATE', 'SALES.VIEW', 'SALES.CREATE', 'SALES.APPROVE', 'FINANCE.VIEW', 'FINANCE.CREATE', 'FINANCE.APPROVE', 'ROOM.VIEW', 'ROOM.CREATE', 'ROOM.EXECUTE'],
    roles: ['系统管理员'],
    bookingContracts: mvpState.contracts
      .filter(item => (
        item.status === '已审核' &&
        Number(item.paid || 0) > 0 &&
        !bookedContractIds.has(Number(item.id))
      ))
      .map(item => ({
        id: item.id,
        store_id: item.store_id,
        contract_no: item.contract_no,
        customer_name: item.customer_name,
        amount: item.amount,
        paid: item.paid,
        outstanding_amount: item.outstanding_amount,
        expected_check_in: item.expected_check_in,
        expected_check_out: item.expected_check_out
      }))
  }
}

function mvpOverview() {
  return {
    customers: mvpState.customers.length,
    contracts: mvpState.contracts.length,
    pendingContracts: mvpState.contracts.filter(item => ['已签合同但未审核', '待审核'].includes(item.status)).length,
    pendingReceipts: mvpState.receipts.filter(item => item.status === '待审核').length,
    bookings: mvpState.bookings.length
  }
}

function mvpResource(config) {
  const requestPath = config.path || config.url || ''
  const match = requestPath.match(/\/erp\/mvp\/([^/?]+)/)
  return match ? match[1] : 'customers'
}

function mvpError(message) {
  return { code: 40000, message, data: null }
}

function findMvpRecord(resource, id) {
  return (mvpState[resource] || []).find(item => Number(item.id) === Number(id))
}

function updateCustomerStatus(customerId, status) {
  const customer = findMvpRecord('customers', customerId)
  if (customer) customer.status = status
}

function roomHasConflict(roomId, checkIn, checkOut) {
  return mvpState.bookings.some(item => (
    Number(item.room_id) === Number(roomId) &&
    item.status !== '已取消' &&
    checkIn < item.check_out &&
    checkOut > item.check_in
  ))
}

function roomHasAllocationBlock(roomId, checkIn, checkOut, excludedBlockId = 0) {
  const room = findMvpRecord('rooms', roomId)
  return Boolean(room && (room.allocation_blocks || []).some(item => (
    Number(item.id) !== Number(excludedBlockId) &&
    checkIn < item.end_at &&
    checkOut > item.start_at
  )))
}

function createMvpRecord(config) {
  const resource = mvpResource(config)
  const body = config.body || {}
  if (!mvpState[resource]) return mvpError('不支持的业务资源')

  const id = Math.max(0, ...mvpState[resource].map(item => Number(item.id) || 0)) + 1
  const storeId = Number(body.storeId || 1)
  const store = stores.find(item => item.id === storeId) || stores[0]
  let record

  if (resource === 'customers') {
    if (!body.name || !body.phone) return mvpError('客户姓名和手机号不能为空')
    if (mvpState.customers.some(item => item.phone === body.phone)) return mvpError('该手机号已存在客户档案')
    if (!customerStages.includes(body.stage)) return mvpError('请选择正确的客户阶段')
    if (!customerIntentLevels.includes(body.intentLevel)) return mvpError('请选择意向等级')
    if (!body.source) return mvpError('客户来源不能为空')
    if (!body.salesStaffId) return mvpError('请选择业务员')
    if (!customerTypes.includes(body.customerType)) return mvpError('请选择客户类型')
    if (body.customerType === '孕期待产' && !body.edc) return mvpError('孕期待产客户必须填写预产期')
    if (body.customerType === '已分娩' && !body.deliveryDate) return mvpError('已分娩客户必须填写分娩日期')
    if (body.customerType === '孕期待产' && body.edc < currentDateText()) return mvpError('预产期不能早于今天')
    if (body.customerType === '已分娩' && body.deliveryDate > currentDateText()) return mvpError('分娩日期不能晚于今天')
    const salesperson = mvpOptions().staff.find(item => Number(item.id) === Number(body.salesStaffId))
    if (!salesperson || Number(salesperson.store_id) !== storeId) return mvpError('业务员与客户门店不一致')
    record = {
      id,
      store_id: storeId,
      customer_no: `KH-2026-${String(30 + id).padStart(4, '0')}`,
      name: body.name,
      phone: body.phone,
      wechat: body.wechat || '',
      store_name: store.name,
      salesperson: salesperson.name,
      sales_staff_id: salesperson.id,
      source: body.source,
      intent_level: body.intentLevel,
      customer_type: body.customerType,
      edc: body.edc || '',
      delivery_date: body.deliveryDate || '',
      status: body.stage,
      created_at: dateText(id, true)
    }
  } else if (resource === 'contracts') {
    const customer = findMvpRecord('customers', body.customerId)
    const selectedPackage = catalogPackages.find(item => item.packageName === body.packageName)
    const referenceAmount = Number(body.referenceAmount || 0)
    const amount = Number(body.amount || 0)
    if (!customer) return mvpError('请选择有效客户')
    if (Number(customer.store_id) !== storeId) return mvpError('客户与合同门店不一致')
    if (!contractTypes.includes(body.contractType)) return mvpError('合同类型不正确')
    if (!body.packageName) return mvpError('请选择套餐或录入纸质合同中的套餐名称')
    if (selectedPackage && Number(body.days) !== Number(selectedPackage.days)) return mvpError('入住天数必须与所选套餐版本一致')
    if (selectedPackage && referenceAmount !== Number(selectedPackage.referencePrice)) return mvpError('参考价格必须与甲方套餐价目表原价一致')
    if (referenceAmount <= 0 || amount <= 0) return mvpError('合同金额必须大于 0')
    if (amount > referenceAmount) return mvpError('成交金额不能大于参考价格')
    if (!body.expectedCheckIn || !body.expectedCheckOut || body.expectedCheckIn >= body.expectedCheckOut) return mvpError('预住日期范围不正确')
    if (body.expectedCheckIn < currentDateText()) return mvpError('预住日期不能早于今天')
    if (dateDays(body.expectedCheckIn, body.expectedCheckOut) !== Number(body.days || 0)) return mvpError('入住天数与预住日期不一致')
    const signDate = body.signDate || currentDateText()
    if (signDate > currentDateText()) return mvpError('签单日期不能晚于今天')
    if (signDate < currentDateText() && !body.backfillReason) return mvpError('历史补录合同必须填写补录原因')
    record = {
      id,
      customer_id: customer.id,
      store_id: storeId,
      contract_no: `HT-2026-${String(80 + id).padStart(4, '0')}`,
      customer_name: customer.name,
      contract_type: body.contractType,
      package_name: body.packageName,
      package_no: selectedPackage ? selectedPackage.packageNo : '',
      package_version: selectedPackage ? selectedPackage.versionNo : '纸质合同手工录入',
      reference_amount: referenceAmount,
      activity_amount: selectedPackage ? Number(selectedPackage.activityPrice) : Number(body.activityAmount || 0),
      amount,
      discount_rate: amount / referenceAmount,
      paid: 0,
      unposted_amount: 0,
      outstanding_amount: amount,
      days: Number(body.days),
      expected_check_in: body.expectedCheckIn,
      expected_check_out: body.expectedCheckOut,
      sign_date: signDate,
      is_backfill: signDate < currentDateText(),
      backfill_reason: body.backfillReason || '',
      entered_at: new Date().toISOString(),
      status: '已签合同但未审核'
    }
    updateCustomerStatus(customer.id, '已签合同但未审核')
  } else if (resource === 'receipts') {
    const contract = findMvpRecord('contracts', body.contractId)
    const amount = Number(body.amount || 0)
    if (!contract) return mvpError('请选择有效合同')
    if (contract.status !== '已审核') return mvpError('只有已审核合同可以登记收款')
    if (Number(contract.store_id) !== storeId) return mvpError('合同与收款门店不一致')
    if (!receiptTypes.includes(body.receiptType)) return mvpError('收款类型不正确')
    if (!paymentMethods.includes(body.paymentMethod)) return mvpError('支付方式不正确')
    if (amount <= 0) return mvpError('收款金额必须大于 0')
    const availableAmount = Math.max(0, Number(contract.outstanding_amount || 0) - Number(contract.unposted_amount || 0))
    if (amount > availableAmount) return mvpError('收款金额不能超过合同剩余可收金额')
    if (body.receiptType === '其他收款' && !body.remark) return mvpError('其他收款必须填写款项用途')
    const receivedAt = body.receivedAt || new Date().toISOString().replace('T', ' ').slice(0, 19)
    if (new Date(receivedAt.replace(' ', 'T')).getTime() > Date.now()) return mvpError('实际收款时间不能晚于当前时间')
    if (receivedAt.slice(0, 10) < currentDateText() && !body.backfillReason) return mvpError('历史收款补录必须填写补录原因')
    record = {
      id,
      contract_id: contract.id,
      store_id: storeId,
      receipt_no: `SK-2026-${String(140 + id).padStart(4, '0')}`,
      customer_name: contract.customer_name,
      contract_no: contract.contract_no,
      store_name: store.name,
      receipt_type: body.receiptType,
      amount,
      payment_method: body.paymentMethod,
      receiver: '赵主管',
      received_at: receivedAt,
      is_backfill: receivedAt.slice(0, 10) < currentDateText(),
      backfill_reason: body.backfillReason || '',
      remark: body.remark || '',
      status: '待审核'
    }
    contract.unposted_amount = Number(contract.unposted_amount || 0) + amount
  } else {
    const contract = findMvpRecord('contracts', body.contractId)
    const room = findMvpRecord('rooms', body.roomId)
    if (!contract || contract.status !== '已审核') return mvpError('只有已审核合同可以订房')
    if (Number(contract.paid || 0) <= 0) return mvpError('至少一笔收款审核入账后才可以订房')
    if (!room) return mvpError('请选择有效房间')
    if (Number(contract.store_id) !== storeId || Number(room.store_id) !== storeId) return mvpError('合同、房间与订房门店不一致')
    if (!body.checkIn || !body.checkOut || body.checkIn >= body.checkOut) return mvpError('入住日期范围不正确')
    if (body.checkIn < currentDateText()) return mvpError('入住日期不能早于今天')
    if (room.status !== '空闲' || roomHasConflict(room.id, body.checkIn, body.checkOut)) return mvpError('所选房间在该日期范围不可用')
    record = {
      id,
      contract_id: contract.id,
      customer_id: contract.customer_id,
      room_id: room.id,
      store_id: storeId,
      booking_no: `DF-2026-${String(50 + id).padStart(4, '0')}`,
      customer_name: contract.customer_name,
      contract_no: contract.contract_no,
      store_name: store.name,
      room_no: room.room_no,
      check_in: body.checkIn,
      check_out: body.checkOut,
      status: '已订房',
      actual_check_in_at: ''
    }
    room.status = '已预订'
    updateCustomerStatus(contract.customer_id, '已订房')
  }

  mvpState[resource].unshift(record)
  return { code: 20000, data: record }
}

function performMvpAction(config) {
  const requestPath = config.path || config.url || ''
  const match = requestPath.match(/\/erp\/mvp\/([^/]+)\/([^/]+)\/([^/?]+)/)
  const resource = match ? match[1] : ''
  const id = match ? Number(match[2]) : 0
  const action = match ? match[3] : ''
  const record = (mvpState[resource] || []).find(item => Number(item.id) === id)

  if (!record) return mvpError('业务记录不存在')

  if (resource === 'contracts' && action === 'approve') {
    if (record.status !== '已签合同但未审核') return mvpError('只有待审核合同可以审核')
    record.status = '已审核'
    updateCustomerStatus(record.customer_id, '已审核')
  } else if (resource === 'receipts' && action === 'approve') {
    if (record.status !== '待审核') return mvpError('只有待审核收款单可以审核')
    const contract = findMvpRecord('contracts', record.contract_id)
    if (!contract) return mvpError('收款对应的合同不存在')
    record.status = '已审核'
    contract.paid = Number(contract.paid || 0) + Number(record.amount || 0)
    contract.unposted_amount = Math.max(0, Number(contract.unposted_amount || 0) - Number(record.amount || 0))
    contract.outstanding_amount = Math.max(0, Number(contract.amount || 0) - Number(contract.paid || 0))
  } else if (resource === 'bookings' && action === 'check-in') {
    if (record.status !== '已订房') return mvpError('只有已订房记录可以办理入住')
    record.status = '已入住'
    record.actual_check_in_at = dateText(id, true)
    const room = findMvpRecord('rooms', record.room_id)
    if (room) room.status = '在住'
    updateCustomerStatus(record.customer_id, '已入住')
  } else {
    return mvpError('不支持的业务操作')
  }

  return {
    code: 20000,
    data: { resource, id, action, status: record.status, processedAt: Date.now() }
  }
}

const rehabStaff = [
  { id: 301, name: '杨技师', store: stores[0].name, role: '产康技师', appointmentTypes: ['产康服务'] },
  { id: 302, name: '刘康复师', store: stores[0].name, role: '康复师', appointmentTypes: ['产康服务', '客房服务'] },
  { id: 303, name: '中心店接待', store: stores[0].name, role: '销售接待', appointmentTypes: ['到店参观'] },
  { id: 401, name: '周护理师', store: stores[1].name, role: '产康技师', appointmentTypes: ['产康服务', '客房服务'] },
  { id: 402, name: '黄河路接待', store: stores[1].name, role: '销售接待', appointmentTypes: ['到店参观'] }
]

const rehabServiceCatalog = [
  { id: 1, store: stores[0].name, appointmentType: '到店参观', category: '客户接待', item: '到店参观', duration: 60 },
  { id: 2, store: stores[0].name, appointmentType: '产康服务', category: '产后修复', item: '产后体态评估', duration: 60 },
  { id: 3, store: stores[0].name, appointmentType: '产康服务', category: '产后修复', item: '腹直肌修复', duration: 60 },
  { id: 4, store: stores[0].name, appointmentType: '产康服务', category: '产后修复', item: '骨盆修复', duration: 60 },
  { id: 5, store: stores[0].name, appointmentType: '产康服务', category: '产后修复', item: '盆底肌修复', duration: 60 },
  { id: 6, store: stores[0].name, appointmentType: '产康服务', category: '产后修复', item: '疤痕松解', duration: 60 },
  { id: 7, store: stores[0].name, appointmentType: '客房服务', category: '身体护理', item: '乳房疏通护理', duration: 60 },
  { id: 8, store: stores[1].name, appointmentType: '到店参观', category: '客户接待', item: '到店参观', duration: 60 },
  { id: 9, store: stores[1].name, appointmentType: '产康服务', category: '产后修复', item: '腹直肌修复', duration: 60 },
  { id: 10, store: stores[1].name, appointmentType: '产康服务', category: '产后修复', item: '骨盆修复', duration: 60 },
  { id: 11, store: stores[1].name, appointmentType: '产康服务', category: '产后修复', item: '盆底肌修复', duration: 60 },
  { id: 12, store: stores[1].name, appointmentType: '产康服务', category: '产后修复', item: '腺体修复', duration: 60 },
  { id: 13, store: stores[1].name, appointmentType: '客房服务', category: '身体护理', item: '淋巴护理', duration: 60 }
]

const rehabResources = [
  { id: 1, name: '中心店接待区', store: stores[0].name, type: '接待区域', appointmentTypes: ['到店参观'], confirmed: true },
  { id: 2, name: '中心店产康服务间（待配置）', store: stores[0].name, type: '服务房间', appointmentTypes: ['产康服务', '客房服务'], confirmed: false },
  { id: 3, name: '黄河路接待区', store: stores[1].name, type: '接待区域', appointmentTypes: ['到店参观'], confirmed: true },
  { id: 4, name: '黄河路产康服务间（待配置）', store: stores[1].name, type: '服务房间', appointmentTypes: ['产康服务', '客房服务'], confirmed: false }
]

const rehabTimeSlots = [
  '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
  '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00',
  '17:00-18:00', '18:00-19:00'
]

const recoveryAppointments = [
  {
    id: 1,
    appointmentNo: 'PKYY-20260729-00001',
    appointmentType: '产康服务',
    customerName: '李女士',
    mobile: '138****2108',
    room: '',
    store: stores[0].name,
    serviceCategory: '产后修复',
    serviceItem: '产后体态评估',
    appointmentDate: '2026-07-30',
    appointmentPeriod: '09:00-10:00',
    technician: '杨技师',
    resourceName: '中心店产康服务间（待配置）',
    serviceCount: 1,
    serviceStatus: '已确认',
    createdBy: 'admin',
    createdAt: '2026-07-29 09:20:00',
    remark: '首次评估'
  },
  {
    id: 2,
    appointmentNo: 'PKYY-20260729-00002',
    appointmentType: '客房服务',
    customerName: '王女士',
    mobile: '138****2245',
    room: 'VIP302',
    store: stores[0].name,
    serviceCategory: '身体护理',
    serviceItem: '乳房疏通护理',
    appointmentDate: '2026-07-30',
    appointmentPeriod: '14:00-15:00',
    technician: '刘康复师',
    resourceName: '',
    serviceCount: 1,
    serviceStatus: '已到店',
    createdBy: 'admin',
    createdAt: '2026-07-29 10:05:00',
    remark: ''
  }
]

function requestBody(config) {
  return config.body || {}
}

function smartRoomPayload() {
  const activeBookings = mvpState.bookings.filter(item => item.status !== '已取消')
  const bookedContractIds = new Set(activeBookings.map(item => Number(item.contract_id)))
  const customers = mvpState.contracts
    .filter(item => (
      item.status === '已审核' &&
      Number(item.paid || 0) > 0 &&
      !bookedContractIds.has(Number(item.id))
    ))
    .map(contract => {
      const customer = findMvpRecord('customers', contract.customer_id)
      const store = stores.find(item => Number(item.id) === Number(contract.store_id))
      return {
        id: customer.id,
        customerName: customer.name,
        mobile: customer.phone,
        status: '- 未订房 -',
        store: store.name,
        contractId: contract.id,
        contractNo: contract.contract_no,
        packageNo: contract.package_no || '',
        packageName: contract.package_name,
        contractAmount: contract.amount,
        paidAmount: contract.paid,
        outstandingAmount: contract.outstanding_amount,
        bookableDays: contract.days,
        birthDate: contract.expected_check_in,
        reservedRoomType: '',
        salesperson: customer.salesperson
      }
    })
  const list = mvpState.rooms.map(room => {
    const store = stores.find(item => Number(item.id) === Number(room.store_id))
    return {
      id: room.id,
      store: store.name,
      room: room.room_no,
      roomType: room.room_type,
      roomStyle: room.room_style || room.room_type,
      floorNumber: room.floor || String(room.room_no).slice(0, 1),
      status: room.status,
      roomNoConfirmed: room.room_no_confirmed !== false,
      roomTypeConfirmed: room.room_type_confirmed !== false,
      algorithmEnabled: room.algorithm_enabled !== false,
      allowedPackageCodes: room.allowed_package_codes || [],
      classificationNote: room.classification_note || '',
      dataSource: room.data_source || '',
      allocationBlocks: (room.allocation_blocks || []).map(item => ({ ...item })),
      bookings: activeBookings
        .filter(item => Number(item.room_id) === Number(room.id))
        .map(item => ({
          id: item.id,
          startAt: item.check_in,
          endAt: item.check_out,
          status: item.status,
          customerName: item.customer_name,
          contractNo: item.contract_no
        }))
    }
  })
  return {
    list,
    total: list.length,
    customers,
    stores,
    packages: catalogPackages.map(item => ({ ...item })),
    roomInventoryEvidence
  }
}

function roomMapPayload() {
  const activeBookings = mvpState.bookings.filter(item => item.status !== '已取消')
  const list = mvpState.rooms.map(room => {
    const store = stores.find(item => Number(item.id) === Number(room.store_id))
    const stays = activeBookings
      .filter(item => Number(item.room_id) === Number(room.id))
      .map(item => ({
        id: item.id,
        customerName: item.customer_name,
        contractNo: item.contract_no,
        status: item.status,
        startAt: item.check_in,
        endAt: item.check_out,
        plannedCheckInAt: item.check_in,
        expectedCheckOutAt: item.check_out
      }))
    const displayStatus = room.status === '在住'
      ? '入住'
      : room.status === '已预订'
        ? '预约'
        : room.status
    const statusKey = displayStatus === '入住'
      ? 'occupied'
      : displayStatus === '预约'
        ? 'reserved'
        : displayStatus === '脏房'
          ? 'cleaning'
          : displayStatus === '维修'
            ? 'maintenance'
            : 'available'
    return {
      id: room.id,
      storeId: room.store_id,
      store: store.name,
      room: room.room_no,
      roomType: room.room_type,
      roomStyle: room.room_style || room.room_type,
      floorNumber: room.floor || String(room.room_no).slice(0, 1),
      floor: room.floor && room.floor !== '待确认' ? `${room.floor}楼` : '楼层待确认',
      direction: room.direction || '待确认',
      status: displayStatus,
      statusKey,
      price: room.daily_price,
      roomNoConfirmed: room.room_no_confirmed !== false,
      roomTypeConfirmed: room.room_type_confirmed !== false,
      algorithmEnabled: room.algorithm_enabled !== false,
      classificationNote: room.classification_note || '',
      dataSource: room.data_source || '',
      allocationBlocks: (room.allocation_blocks || []).map(item => ({ ...item })),
      customerName: stays[0]?.customerName || '',
      stays,
      bookings: stays,
      pastStays: [],
      detailCount: stays.filter(item => item.status === '已订房').length,
      availableRange: stays.length
        ? stays.map(item => `${item.startAt}~${item.endAt}`).join('、')
        : '暂无入住安排'
    }
  })
  return { list, total: list.length, stores, roomInventoryEvidence }
}

function createSmartRoomBooking(config) {
  const body = requestBody(config)
  const store = stores.find(item => item.name === body.store)
  const selectedPackage = catalogPackages.find(item => item.packageNo === body.packageNo)
  const customer = findMvpRecord('customers', body.customerId)
  const contract = findMvpRecord('contracts', body.contractId)
  const room = findMvpRecord('rooms', body.roomId)
  const checkIn = String(body.plannedCheckInAt || '').slice(0, 10)
  const checkOut = String(body.plannedCheckOutAt || '').slice(0, 10)
  if (!store || !selectedPackage || !customer || !contract || !room) return mvpError('订房资料不完整，请选择有效门店、套餐、客户和房间')
  if (contract.status !== '已审核') return mvpError('只有已审核合同可以订房')
  if (Number(contract.paid || 0) <= 0) return mvpError('至少一笔收款审核入账后才可以订房')
  if (Number(selectedPackage.store_id) !== Number(store.id)) return mvpError('所选套餐不属于当前排房门店')
  if (
    Number(customer.id) !== Number(contract.customer_id) ||
    Number(contract.store_id) !== Number(store.id) ||
    Number(room.store_id) !== Number(store.id)
  ) return mvpError('客户、合同、房间与订房门店必须一致')
  if (contract.package_no && contract.package_no !== selectedPackage.packageNo) {
    return mvpError('排房套餐与客户合同套餐不一致')
  }
  if (Number(body.totalDays || selectedPackage.days) !== Number(selectedPackage.days)) {
    return mvpError('预住天数必须与所选套餐版本一致')
  }
  if (!checkIn || !checkOut || checkIn >= checkOut) return mvpError('入住日期范围不正确')
  if (checkIn < currentDateText()) return mvpError('入住日期不能早于今天')
  if (['维修', '脏房'].includes(room.status)) return mvpError('该房间当前不可销售')
  if (roomHasConflict(room.id, checkIn, checkOut)) return mvpError('所选日期内房间已被占用')
  if (roomHasAllocationBlock(room.id, checkIn, checkOut)) return mvpError('所选日期内房间处于禁排或保留时段')
  const contractConflict = mvpState.bookings.some(item => (
    Number(item.contract_id) === Number(contract.id) &&
    item.status !== '已取消' &&
    checkIn < item.check_out &&
    checkOut > item.check_in
  ))
  if (contractConflict) return mvpError('该合同在所选日期已有订房记录')

  const id = Math.max(0, ...mvpState.bookings.map(item => Number(item.id) || 0)) + 1
  const record = {
    id,
    contract_id: contract.id,
    customer_id: customer.id,
    room_id: room.id,
    store_id: store.id,
    booking_no: `DF-2026-${String(50 + id).padStart(4, '0')}`,
    customer_name: customer.name,
    contract_no: contract.contract_no,
    package_no: selectedPackage.packageNo,
    package_name: selectedPackage.packageName,
    store_name: store.name,
    room_no: room.room_no,
    check_in: checkIn,
    check_out: checkOut,
    status: '已订房',
    actual_check_in_at: '',
    remark: body.remark || ''
  }
  mvpState.bookings.unshift(record)
  room.status = '已预订'
  updateCustomerStatus(customer.id, '已订房')
  return { code: 20000, data: { id, bookingNo: record.booking_no }, message: '订房成功' }
}

function createSmartRoomBlock(config) {
  const body = requestBody(config)
  const store = stores.find(item => item.name === body.store)
  const room = findMvpRecord('rooms', body.roomId)
  const startAt = String(body.startAt || '').slice(0, 10)
  const endAt = String(body.endAt || '').slice(0, 10)
  const allowedTypes = ['维修', '消毒', '内部占用', '保留房']
  if (!store || !room || Number(room.store_id) !== Number(store.id)) return mvpError('请选择当前门店的有效房间')
  if (!allowedTypes.includes(body.blockType)) return mvpError('请选择有效的禁排类型')
  if (!startAt || !endAt || startAt >= endAt) return mvpError('禁排日期范围不正确')
  if (startAt < currentDateText()) return mvpError('禁排开始日期不能早于今天')
  if (!String(body.reason || '').trim()) return mvpError('请填写禁排或保留原因')
  if (roomHasConflict(room.id, startAt, endAt)) return mvpError('该时段已有订房记录，不能设置禁排')
  if (roomHasAllocationBlock(room.id, startAt, endAt)) return mvpError('该时段已存在禁排或保留记录')

  const blocks = room.allocation_blocks || (room.allocation_blocks = [])
  const id = Math.max(0, ...mvpState.rooms.flatMap(item => (
    (item.allocation_blocks || []).map(block => Number(block.id) || 0)
  ))) + 1
  const record = {
    id,
    block_type: body.blockType,
    start_at: startAt,
    end_at: endAt,
    reason: String(body.reason).trim(),
    created_at: `${currentDateText()} 12:00:00`
  }
  blocks.unshift(record)
  return { code: 20000, data: record, message: '禁排时段已保存' }
}

function removeSmartRoomBlock(config) {
  const body = requestBody(config)
  const store = stores.find(item => item.name === body.store)
  const room = findMvpRecord('rooms', body.roomId)
  if (!store || !room || Number(room.store_id) !== Number(store.id)) return mvpError('请选择当前门店的有效房间')
  const blocks = room.allocation_blocks || []
  const index = blocks.findIndex(item => Number(item.id) === Number(body.blockId))
  if (index < 0) return mvpError('禁排记录不存在或已取消')
  blocks.splice(index, 1)
  return { code: 20000, data: { blockId: body.blockId }, message: '禁排时段已取消' }
}

function saveSmartRoomAllocation(config) {
  const body = requestBody(config)
  if (body._action === '设置禁排') return createSmartRoomBlock(config)
  if (body._action === '取消禁排') return removeSmartRoomBlock(config)
  return createSmartRoomBooking(config)
}

function createRecoveryAppointment(config) {
  const body = requestBody(config)
  const existing = recoveryAppointments.find(item => Number(item.id) === Number(body.id))
  const customer = mvpState.customers.find(item => item.name === body.customerName && item.store_name === body.store)
  const staff = rehabStaff.find(item => item.name === body.technician && item.store === body.store)
  const service = rehabServiceCatalog.find(item => (
    item.store === body.store &&
    item.appointmentType === body.appointmentType &&
    item.category === body.serviceCategory &&
    item.item === body.serviceItem
  ))
  const resource = body.resourceName
    ? rehabResources.find(item => item.name === body.resourceName && item.store === body.store)
    : null
  const period = String(body.appointmentPeriod || '').trim()
  const match = period.match(/^((?:[01]\d|2[0-3]):[0-5]\d)\s*-\s*((?:[01]\d|2[0-3]):[0-5]\d)$/)
  if (!customer || !staff) return mvpError('请选择有效客户和服务人员')
  if (!body.store || customer.store_name !== body.store || staff.store !== body.store) {
    return mvpError('客户、服务人员与预约门店必须一致')
  }
  if (!staff.appointmentTypes.includes(body.appointmentType)) return mvpError('所选人员不支持该预约分类')
  if (!service) return mvpError('请选择当前门店已配置的预约项目')
  if (body.resourceName && !resource) return mvpError('请选择当前门店的有效服务房间或设备')
  if (!body.appointmentDate || body.appointmentDate < currentDateText()) return mvpError('预约日期不能早于今天')
  if (!match || match[1] >= match[2]) return mvpError('预约时段应为有效的 HH:mm-HH:mm')
  if (!rehabTimeSlots.includes(`${match[1]}-${match[2]}`)) return mvpError('请选择门店配置的标准预约时段')
  if (existing && !['待确认', '已确认'].includes(existing.serviceStatus)) return mvpError('当前状态不能改期')
  const staffConflict = recoveryAppointments.some(item => (
    Number(item.id) !== Number(body.id) &&
    item.technician === staff.name &&
    item.appointmentDate === body.appointmentDate &&
    !['已取消', '已爽约'].includes(item.serviceStatus) &&
    match[1] < item.appointmentPeriod.split('-')[1] &&
    match[2] > item.appointmentPeriod.split('-')[0]
  ))
  if (staffConflict) return mvpError('该服务人员在所选时段已有预约')
  const resourceConflict = resource && recoveryAppointments.some(item => (
    Number(item.id) !== Number(body.id) &&
    item.resourceName === resource.name &&
    item.appointmentDate === body.appointmentDate &&
    !['已取消', '已爽约'].includes(item.serviceStatus) &&
    match[1] < item.appointmentPeriod.split('-')[1] &&
    match[2] > item.appointmentPeriod.split('-')[0]
  ))
  if (resourceConflict) return mvpError('该服务房间或设备在所选时段已被占用')

  const id = existing
    ? existing.id
    : Math.max(0, ...recoveryAppointments.map(item => Number(item.id) || 0)) + 1
  const record = {
    id,
    appointmentNo: existing
      ? existing.appointmentNo
      : `PKYY-${String(body.appointmentDate).replace(/-/g, '')}-${String(id).padStart(5, '0')}`,
    appointmentType: body.appointmentType,
    customerName: customer.name,
    mobile: customer.phone,
    room: existing ? existing.room : '',
    store: body.store,
    serviceCategory: body.serviceCategory,
    serviceItem: body.serviceItem,
    appointmentDate: body.appointmentDate,
    appointmentPeriod: `${match[1]}-${match[2]}`,
    technician: staff.name,
    resourceName: resource ? resource.name : '',
    serviceCount: Number(body.serviceCount || 1),
    serviceStatus: existing ? existing.serviceStatus : '待确认',
    createdBy: existing ? existing.createdBy : 'admin',
    createdAt: existing ? existing.createdAt : `${currentDateText()} 12:00:00`,
    updatedAt: `${currentDateText()} 12:00:00`,
    remark: body.remark || ''
  }
  if (existing) {
    Object.assign(existing, record)
  } else {
    recoveryAppointments.unshift(record)
  }
  return { code: 20000, data: record, message: existing ? '预约改期成功' : '预约成功' }
}

function performRecoveryAppointmentAction(config) {
  const body = requestBody(config)
  const record = recoveryAppointments.find(item => Number(item.id) === Number(body.id))
  if (!record) return mvpError('预约记录不存在')
  if (['预约确认', '确认预约'].includes(body.action)) {
    if (record.serviceStatus !== '待确认') return mvpError('只有待确认预约可以确认')
    record.serviceStatus = '已确认'
  } else if (body.action === '客户到店') {
    if (record.serviceStatus !== '已确认') return mvpError('只有已确认预约可以办理到店')
    record.serviceStatus = '已到店'
  } else if (body.action === '开始服务') {
    if (record.serviceStatus !== '已到店') return mvpError('只有已到店预约可以开始服务')
    record.serviceStatus = '服务中'
  } else if (['确认完成', '完成服务'].includes(body.action)) {
    if (record.serviceStatus !== '服务中') return mvpError('只有服务中的预约可以完成')
    record.serviceStatus = '已完成'
  } else if (['取消', '取消预约'].includes(body.action)) {
    if (['服务中', '已完成', '已爽约'].includes(record.serviceStatus)) return mvpError('当前状态不能取消预约')
    record.serviceStatus = '已取消'
  } else if (body.action === '标记爽约') {
    if (!['待确认', '已确认'].includes(record.serviceStatus)) return mvpError('只有未到店的预约可以标记爽约')
    record.serviceStatus = '已爽约'
  } else {
    return mvpError('不支持的预约操作')
  }
  record.updatedAt = `${currentDateText()} 12:00:00`
  return { code: 20000, data: record, message: `${body.action}成功` }
}

function filteredRecoveryAppointments(config) {
  const query = config.query || {}
  const keyword = String(query.keyword || '').trim().toLowerCase()
  return recoveryAppointments.filter(item => (
    (!query.store || item.store === query.store) &&
    (!query.appointmentType || item.appointmentType === query.appointmentType) &&
    (!query.dateStart || item.appointmentDate >= query.dateStart) &&
    (!query.dateEnd || item.appointmentDate <= query.dateEnd) &&
    (!query.serviceStatus || item.serviceStatus === query.serviceStatus) &&
    (!query.technician || item.technician === query.technician) &&
    (
      !keyword ||
      [item.customerName, item.mobile, item.serviceItem, item.appointmentNo]
        .some(value => String(value || '').toLowerCase().includes(keyword))
    )
  ))
}

const catalogPackages = confirmedPackageCatalog.map(item => ({ ...item }))

const assetCardPackages = [
  { id: 1, name: '产后修复 12 次卡', cardType: '次卡', amount: 6800, totalCount: 12 },
  { id: 2, name: '妈妈护理套餐卡', cardType: '套餐卡', amount: 12800, totalCount: 20 },
  { id: 3, name: '尊享储值卡', cardType: '储值卡', amount: 10000, totalCount: 0 }
]

const assetState = {
  cards: [
    {
      id: 1,
      card_no: 'ZC-2026-0018',
      customer_id: 1,
      customer_name: '李女士',
      card_name: '产后修复 12 次卡',
      card_type: '次卡',
      sale_amount: 6800,
      total_count: 12,
      remaining_count: 9,
      balance: 0,
      valid_to: '2027-07-28',
      status: '正常',
      store_name: stores[0].name,
      created_at: '2026-07-26 10:20:00'
    },
    {
      id: 2,
      card_no: 'TC-2026-0021',
      customer_id: 2,
      customer_name: '王女士',
      card_name: '妈妈护理套餐卡',
      card_type: '套餐卡',
      sale_amount: 12800,
      total_count: 20,
      remaining_count: 16,
      balance: 0,
      valid_to: '2027-08-08',
      status: '正常',
      store_name: stores[0].name,
      created_at: '2026-07-25 15:40:00'
    },
    {
      id: 3,
      card_no: 'CZ-2026-0026',
      customer_id: 3,
      customer_name: '张女士',
      card_name: '尊享储值卡',
      card_type: '储值卡',
      sale_amount: 10000,
      total_count: 0,
      remaining_count: 0,
      balance: 8600,
      valid_to: '2027-07-22',
      status: '正常',
      store_name: stores[1].name,
      created_at: '2026-07-22 11:10:00'
    }
  ],
  accounts: [
    { id: 1, account_no: 'YE-2026-0018', customer_id: 1, customer_name: '李女士', mobile: '138****2108', store_name: stores[0].name, balance: 3000, frozen_amount: 0, points: 1280, status: '正常', updated_at: '2026-07-28 17:20:00' },
    { id: 2, account_no: 'YE-2026-0021', customer_id: 2, customer_name: '王女士', mobile: '138****2245', store_name: stores[0].name, balance: 5600, frozen_amount: 500, points: 2360, status: '正常', updated_at: '2026-07-28 16:15:00' },
    { id: 3, account_no: 'YE-2026-0026', customer_id: 3, customer_name: '张女士', mobile: '138****2382', store_name: stores[1].name, balance: 1800, frozen_amount: 0, points: 920, status: '正常', updated_at: '2026-07-28 14:30:00' }
  ],
  payments: [
    { id: 1, config_name: '门店微信收款', channel: '微信', merchant_no: '****2388', fee_rate: 0.6, test_status: '测试通过', enabled: true, updated_at: '2026-07-28 16:20:00' },
    { id: 2, config_name: '门店支付宝收款', channel: '支付宝', merchant_no: '****6190', fee_rate: 0.6, test_status: '测试通过', enabled: true, updated_at: '2026-07-28 16:22:00' },
    { id: 3, config_name: '银联转账', channel: '银行卡', merchant_no: '****8806', fee_rate: 0.38, test_status: '未测试', enabled: false, updated_at: '2026-07-28 15:10:00' },
    { id: 4, config_name: '前台现金', channel: '现金', merchant_no: '无需配置', fee_rate: 0, test_status: '测试通过', enabled: true, updated_at: '2026-07-28 15:05:00' }
  ],
  messages: [
    { id: 1, message_no: 'XX-2026-0081', customer_id: 1, customer_name: '李女士', message_title: '合同审核提醒', channel: '站内消息', content: '您的合同资料已提交，请留意后续审核结果。', planned_at: '2026-07-29 09:30:00', sent_at: '', send_status: '待发送', retry_count: 0 },
    { id: 2, message_no: 'XX-2026-0082', customer_id: 2, customer_name: '王女士', message_title: '入住准备提醒', channel: '微信', content: '请提前准备入住资料和母婴用品，管家将与您联系。', planned_at: '2026-07-29 10:00:00', sent_at: '2026-07-29 10:00:00', send_status: '已发送', retry_count: 0 },
    { id: 3, message_no: 'XX-2026-0083', customer_id: 3, customer_name: '张女士', message_title: '护理服务预约', channel: '短信', content: '您预约的产后恢复护理将在明日进行。', planned_at: '2026-07-29 11:00:00', sent_at: '', send_status: '发送失败', retry_count: 1 },
    { id: 4, message_no: 'XX-2026-0084', customer_id: 2, customer_name: '王女士', message_title: '余额变动通知', channel: '站内消息', content: '您的客户余额账户发生变动，请登录查看明细。', planned_at: '2026-07-29 14:00:00', sent_at: '', send_status: '待发送', retry_count: 0 }
  ]
}

function assetOptions() {
  return {
    customers: mvpState.customers.map(item => ({ id: item.id, name: item.name, phone: item.phone })),
    cardTypes: ['次卡', '套餐卡', '储值卡'],
    cardPackages: assetCardPackages,
    messageChannels: ['短信', '微信', '站内消息']
  }
}

function assetOverview() {
  return {
    activeCards: assetState.cards.filter(item => item.status === '正常').length,
    accountBalance: assetState.accounts.reduce((sum, item) => sum + Number(item.balance || 0), 0),
    enabledPayments: assetState.payments.filter(item => item.enabled).length,
    pendingMessages: assetState.messages.filter(item => item.send_status === '待发送').length
  }
}

function assetRequestParts(config) {
  const requestPath = config.path || config.url || ''
  const match = requestPath.match(/\/erp\/assets\/([^/?]+)(?:\/([^/?]+)\/([^/?]+))?/)
  return {
    resource: match ? match[1] : '',
    id: match && match[2] ? Number(match[2]) : 0,
    action: match && match[3] ? match[3] : ''
  }
}

function findAssetRecord(resource, id) {
  return (assetState[resource] || []).find(item => Number(item.id) === Number(id))
}

function createAssetRecord(config) {
  const { resource } = assetRequestParts(config)
  const body = config.body || {}

  if (resource === 'cards') {
    const customer = findMvpRecord('customers', body.customerId)
    const packageItem = assetCardPackages.find(item => Number(item.id) === Number(body.packageId))
    if (!customer) return mvpError('请选择有效客户')
    if (!packageItem) return mvpError('请选择有效卡套餐')
    if (!['次卡', '套餐卡', '储值卡'].includes(body.cardType)) return mvpError('卡类型不正确')
    if (Number(body.amount) < 0) return mvpError('售卡金额不能小于 0')
    if (body.cardType !== '储值卡' && Number(body.totalCount) <= 0) return mvpError('次卡或套餐卡次数必须大于 0')
    if (!body.validTo) return mvpError('请选择有效期')

    const id = Math.max(...assetState.cards.map(item => Number(item.id)), 0) + 1
    const prefix = body.cardType === '储值卡' ? 'CZ' : body.cardType === '套餐卡' ? 'TC' : 'ZC'
    const record = {
      id,
      card_no: `${prefix}-2026-${String(26 + id).padStart(4, '0')}`,
      customer_id: customer.id,
      customer_name: customer.name,
      card_name: packageItem.name,
      card_type: body.cardType,
      sale_amount: Number(body.amount || 0),
      total_count: body.cardType === '储值卡' ? 0 : Number(body.totalCount),
      remaining_count: body.cardType === '储值卡' ? 0 : Number(body.totalCount),
      balance: body.cardType === '储值卡' ? Number(body.amount || 0) : 0,
      valid_to: body.validTo,
      status: '正常',
      store_name: stores.find(item => Number(item.id) === Number(customer.store_id))?.name || stores[0].name,
      created_at: '2026-07-29 09:00:00'
    }
    assetState.cards.unshift(record)
    return { code: 20000, data: record, message: '发卡成功' }
  }

  if (resource === 'messages') {
    const customer = findMvpRecord('customers', body.customerId)
    if (!customer) return mvpError('请选择有效客户')
    if (!body.messageTitle || !body.content) return mvpError('请填写消息标题和内容')
    if (!['短信', '微信', '站内消息'].includes(body.channel)) return mvpError('发送渠道不正确')
    if (!body.plannedAt) return mvpError('请选择计划发送时间')

    const id = Math.max(...assetState.messages.map(item => Number(item.id)), 0) + 1
    const record = {
      id,
      message_no: `XX-2026-${String(84 + id).padStart(4, '0')}`,
      customer_id: customer.id,
      customer_name: customer.name,
      message_title: body.messageTitle,
      channel: body.channel,
      content: body.content,
      planned_at: body.plannedAt,
      sent_at: '',
      send_status: '待发送',
      retry_count: 0
    }
    assetState.messages.unshift(record)
    return { code: 20000, data: record, message: '消息任务已创建' }
  }

  return mvpError('不支持创建该类资产记录')
}

function performAssetAction(config) {
  const { resource, id, action } = assetRequestParts(config)
  const body = config.body || {}
  const record = findAssetRecord(resource, id)
  if (!record) return mvpError('操作记录不存在')

  if (resource === 'cards' && ['consume', 'deduct'].includes(action)) {
    if (record.status !== '正常') return mvpError('只有正常状态的卡可以核销')
    if (record.card_type === '储值卡') {
      const amount = Number(body.amount || 0)
      if (amount <= 0) return mvpError('请输入有效扣款金额')
      if (amount > Number(record.balance)) return mvpError('储值卡余额不足')
      record.balance = Number(record.balance) - amount
      if (record.balance === 0) record.status = '已用完'
    } else {
      if (action !== 'consume') return mvpError('次卡和套餐卡只支持按次数核销')
      const count = Number(body.count || 1)
      if (count <= 0 || !Number.isInteger(count)) return mvpError('核销次数必须为正整数')
      if (count > Number(record.remaining_count)) return mvpError('剩余次数不足')
      record.remaining_count = Number(record.remaining_count) - count
      if (record.remaining_count === 0) record.status = '已用完'
    }
  } else if (resource === 'accounts' && ['top-up', 'deduct'].includes(action)) {
    const amount = Number(body.amount || 0)
    if (amount <= 0) return mvpError('请输入有效金额')
    if (action === 'deduct' && amount > Number(record.balance)) return mvpError('账户余额不足')
    record.balance = action === 'top-up'
      ? Number(record.balance) + amount
      : Number(record.balance) - amount
    record.updated_at = '2026-07-29 09:10:00'
  } else if (resource === 'payments' && action === 'test') {
    record.test_status = '测试通过'
    record.updated_at = '2026-07-29 09:15:00'
  } else if (resource === 'payments' && action === 'toggle') {
    record.enabled = !record.enabled
    record.updated_at = '2026-07-29 09:16:00'
  } else if (resource === 'messages' && action === 'send') {
    if (record.send_status !== '待发送') return mvpError('只有待发送消息可以立即发送')
    record.send_status = '已发送'
    record.sent_at = '2026-07-29 09:20:00'
  } else if (resource === 'messages' && action === 'cancel') {
    if (record.send_status !== '待发送') return mvpError('只有待发送消息可以取消')
    record.send_status = '已取消'
  } else if (resource === 'messages' && action === 'retry') {
    if (record.send_status !== '发送失败') return mvpError('只有发送失败的消息可以重试')
    record.retry_count = Number(record.retry_count || 0) + 1
    record.send_status = '已发送'
    record.sent_at = '2026-07-29 09:21:00'
  } else {
    return mvpError('不支持的资产操作')
  }

  return {
    code: 20000,
    data: { resource, id, action, record, processedAt: Date.now() },
    message: '资产操作成功'
  }
}

const serviceProjects = serviceNames.map((name, index) => ({
  id: index + 1,
  projectNo: `XM-${String(index + 1).padStart(4, '0')}`,
  projectName: name,
  category: ['护理服务', '产康服务', '膳食服务', '客房服务'][index % 4],
  unit: ['次', '项', '份'][index % 3],
  referencePrice: 180 + index * 80,
  status: index % 3 ? '启用' : '待审核'
}))

module.exports = [
  {
    url: '/vue-element-admin/erp/mvp/options$',
    type: 'get',
    response: _ => ({ code: 20000, data: mvpOptions() })
  },
  {
    url: '/vue-element-admin/erp/mvp/overview$',
    type: 'get',
    response: _ => ({ code: 20000, data: mvpOverview() })
  },
  {
    url: '/vue-element-admin/erp/mvp/(customers|contracts|receipts|rooms|bookings)$',
    type: 'get',
    response: config => {
      const resource = mvpResource(config)
      const list = mvpState[resource] || []
      return {
        code: 20000,
        data: { list, total: list.length }
      }
    }
  },
  {
    url: '/vue-element-admin/erp/mvp/(customers|contracts|receipts|bookings)$',
    type: 'post',
    response: config => createMvpRecord(config)
  },
  {
    url: '/vue-element-admin/erp/mvp/(contracts|receipts|bookings)/[^/]+/(approve|check-in)$',
    type: 'post',
    response: config => performMvpAction(config)
  },
  {
    url: '/vue-element-admin/erp/finance/options$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: { stores }
    })
  },
  {
    url: '/vue-element-admin/erp/rehab/options$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: {
        stores,
        customers: mvpState.customers.map(item => ({
          id: item.id,
          name: item.name,
          mobile: item.phone,
          store: item.store_name
        })),
        staff: rehabStaff,
        serviceCatalog: rehabServiceCatalog,
        resources: rehabResources,
        timeSlots: rehabTimeSlots
      }
    })
  },
  {
    url: '/vue-element-admin/erp/room/modules/smart-allocation$',
    type: 'get',
    response: _ => ({ code: 20000, data: smartRoomPayload() })
  },
  {
    url: '/vue-element-admin/erp/room/modules/smart-allocation/save$',
    type: 'post',
    response: config => saveSmartRoomAllocation(config)
  },
  {
    url: '/vue-element-admin/erp/room/modules/room-map$',
    type: 'get',
    response: _ => ({ code: 20000, data: roomMapPayload() })
  },
  {
    url: '/vue-element-admin/erp/rehab/modules/service-appointments$',
    type: 'get',
    response: config => {
      const list = filteredRecoveryAppointments(config)
      return {
        code: 20000,
        data: {
          resource: 'service-appointments',
          list,
          total: list.length,
          stores,
          source: 'local-business-mock',
          demoOnly: true
        }
      }
    }
  },
  {
    url: '/vue-element-admin/erp/rehab/modules/service-appointments/save$',
    type: 'post',
    response: config => createRecoveryAppointment(config)
  },
  {
    url: '/vue-element-admin/erp/rehab/modules/service-appointments/action$',
    type: 'post',
    response: config => performRecoveryAppointmentAction(config)
  },
  {
    url: '/vue-element-admin/erp/catalog/packages$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: { list: catalogPackages, total: catalogPackages.length }
    })
  },
  {
    url: '/vue-element-admin/erp/catalog/packages/[^/]+$',
    type: 'get',
    response: config => {
      const id = Number((config.path || config.url || '').split('/').pop())
      return { code: 20000, data: catalogPackages.find(item => item.id === id) || catalogPackages[0] }
    }
  },
  {
    url: '/vue-element-admin/erp/catalog/service-projects$',
    type: 'get',
    response: _ => ({
      code: 20000,
      data: { list: serviceProjects, total: serviceProjects.length }
    })
  },
  {
    url: '/vue-element-admin/erp/catalog/(packages|service-projects)(/[^/]+/(publish|deactivate))?(/save)?$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { id: (config.body || {}).id || Date.now(), savedAt: Date.now(), demoOnly: true }
    })
  },
  {
    url: '/vue-element-admin/erp/assets/options$',
    type: 'get',
    response: _ => ({ code: 20000, data: assetOptions() })
  },
  {
    url: '/vue-element-admin/erp/assets/overview$',
    type: 'get',
    response: _ => ({ code: 20000, data: assetOverview() })
  },
  {
    url: '/vue-element-admin/erp/assets/(cards|accounts|payments|messages)$',
    type: 'get',
    response: config => {
      const { resource } = assetRequestParts(config)
      const list = assetState[resource] || []
      return { code: 20000, data: { list, total: list.length }}
    }
  },
  {
    url: '/vue-element-admin/erp/assets/(cards|messages)$',
    type: 'post',
    response: config => createAssetRecord(config)
  },
  {
    url: '/vue-element-admin/erp/assets/(cards|accounts|payments|messages)/[^/]+/(consume|top-up|deduct|test|toggle|send|cancel|retry)$',
    type: 'post',
    response: config => performAssetAction(config)
  },
  {
    url: '/vue-element-admin/erp/(customer|sales|finance|room|nursing|rehab|maternity-nurse|diet|inventory|mall|risk|report|basic|system)/modules/[^/]+$',
    type: 'get',
    response: config => {
      const { domain, resource } = moduleContext(config)
      const list = domain === 'sales' && resource === 'packages'
        ? catalogPackages.map(item => ({ ...item }))
        : demoModuleRows(domain, resource)
      return {
        code: 20000,
        data: {
          resource,
          list,
          total: list.length,
          stores,
          source: domain === 'sales' && resource === 'packages'
            ? 'client-confirmed-package-table'
            : 'design-document-demo',
          demoOnly: !(domain === 'sales' && resource === 'packages'),
          loadedAt: Date.now()
        }
      }
    }
  },
  {
    url: '/vue-element-admin/erp/(customer|sales|finance|room|nursing|rehab|maternity-nurse|diet|inventory|mall|risk|report|basic|system)/modules/[^/]+/save$',
    type: 'post',
    response: config => saveDemoModuleRecord(config)
  },
  {
    url: '/vue-element-admin/erp/(customer|sales|finance|room|nursing|rehab|maternity-nurse|diet|inventory|mall|risk|report|basic|system)/modules/[^/]+/(action|audit|preview)$',
    type: 'post',
    response: config => performDemoModuleAction(config)
  }
]
