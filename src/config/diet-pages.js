import { applyOriginalEvidence } from './original-page-evidence'
import { applyAuditedSurfaceEvidence } from './audited-surface-adapter'

const stores = ['中心广场旗舰店', '黄河路轻奢店']

const input = (key, label, required = false) => ({ key, label, type: 'input', required, verified: false })
const select = (key, label, options, required = false) => ({ key, label, type: 'select', options, required, verified: false })
const date = (key, label, required = false) => ({ key, label, type: 'date', required, verified: false })
const dateRange = (key, label) => ({ key, label, type: 'dateRange', verified: false })
const number = (key, label, required = false) => ({ key, label, type: 'number', required, verified: false })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required, verified: false })
const switchField = (key, label) => ({ key, label, type: 'switch', verified: false })
const col = (key, label, width, tag = false, money = false) => ({ key, label, width, tag, money, verified: false })

const mealTypes = ['早餐', '上午加餐', '午餐', '下午加餐', '晚餐', '晚间加餐']
const mealStatuses = ['待排餐', '已排餐', '备餐中', '配送中', '已签收', '已退餐']
const customerMealStatuses = ['全部', '--未到店--', '--已入住--', '--已离店--']
const floorChoices = ['全部', '2楼', '3楼', '4楼', '5楼', '6楼']
const choiceList = (key, label, options, defaultValue = options[0]) => ({
  key,
  label,
  type: 'choice-list',
  options,
  defaultValue,
  verified: true
})
const commonMeta = {
  evidenceLevel: '待原系统二次核验',
  completionLevel: 'Visible',
  originalUrl: '',
  queryActions: ['查询'],
  actions: [],
  evidenceNote: '菜单名称由仓库菜单证据确认；当前筛选项、按钮、表格列、表单、默认值及状态为业务链路草案，未从原 ERP 页面逐项验证。'
}
const withMeta = config => ({ ...commonMeta, ...config })

const customerMealFields = [
  input('customerName', '客户姓名', true),
  input('room', '房间号', true),
  select('store', '门店', stores, true),
  date('mealDate', '用餐日期', true),
  select('mealType', '餐次', mealTypes, true),
  input('dishName', '菜品名称', true),
  number('quantity', '数量', true),
  input('dietitian', '营养师'),
  textarea('taboo', '饮食禁忌'),
  textarea('remark', '备注')
]

const dishFields = [
  input('dishCode', '菜品编码', true),
  input('dishName', '菜品名称', true),
  select('dishCategory', '菜品类别', ['主食', '汤羹', '荤菜', '素菜', '点心', '水果', '饮品'], true),
  select('mealType', '适用餐次', mealTypes, true),
  input('unit', '单位', true),
  number('standardPrice', '标准售价'),
  input('ingredients', '主要食材'),
  input('nutrition', '营养说明'),
  input('tabooTag', '禁忌标签'),
  select('store', '所属门店', stores),
  switchField('enabled', '是否启用'),
  textarea('remark', '备注')
]

const packageFields = [
  input('packageCode', '套餐编码', true),
  input('packageName', '套餐名称', true),
  select('store', '所属门店', stores, true),
  number('cycleDays', '套餐天数', true),
  number('packageAmount', '套餐金额', true),
  select('customerType', '适用客户', ['入住客户', '散客', '陪护人员', '员工']),
  input('mealStandard', '餐次标准'),
  date('effectiveDate', '生效日期'),
  date('expiryDate', '失效日期'),
  switchField('enabled', '是否启用'),
  textarea('packageDetail', '套餐说明')
]

const soupFields = [
  input('soupName', '营养汤名称', true),
  select('store', '所属门店', stores, true),
  select('supplyType', '供应类型', ['常规营养汤', '产后调理汤', '特殊医嘱汤']),
  input('ingredients', '主要食材'),
  input('supplyPeriod', '供应时段'),
  number('standardPrice', '标准价格'),
  input('applicableCustomer', '适用客户'),
  input('contraindication', '禁忌说明'),
  switchField('enabled', '是否启用'),
  textarea('remark', '备注')
]

const orderFields = [
  input('customerName', '客户姓名', true),
  input('room', '房间号'),
  select('store', '门店', stores, true),
  select('customerType', '客户类型', ['入住客户', '散客', '陪护人员', '员工'], true),
  date('mealDate', '用餐日期', true),
  select('mealType', '餐次', mealTypes, true),
  input('dishName', '菜品/套餐', true),
  number('quantity', '数量', true),
  number('amount', '金额'),
  select('paymentMethod', '结算方式', ['合同套餐', '餐卡', '现金', '微信', '支付宝', '挂账']),
  textarea('deliveryAddress', '送餐位置'),
  textarea('remark', '备注')
]

export const dietPageConfigs = {
  客户餐单: withMeta({
    key: 'customer-meal-plans',
    mode: 'meal-calendar',
    icon: 'el-icon-dish',
    description: '按客户、房间和日期编排餐次、菜品、禁忌与配送状态。',
    actions: ['添加', '编辑', '删除', '生成餐单', '复制餐单', '打印'],
    filters: [
      input('customerName', '客户姓名'), input('room', '房间号'), select('store', '门店', stores),
      choiceList('customerStatus', '客户状态', customerMealStatuses),
      dateRange('mealRange', '用餐日期'), select('mealType', '餐次', mealTypes), select('status', '餐单状态', mealStatuses)
    ],
    columns: [
      col('mealDate', '用餐日期', 110), col('room', '房间号', 90), col('customerName', '客户姓名', 110),
      col('store', '门店', 150), col('mealType', '餐次', 100), col('dishName', '菜品名称', 160),
      col('quantity', '数量', 80), col('taboo', '饮食禁忌', 170), col('dietitian', '营养师', 105),
      col('status', '餐单状态', 100, true), col('deliveryTime', '配送时间', 145), col('remark', '备注', 180)
    ],
    formFields: customerMealFields
  }),
  菜品管理: withMeta({
    key: 'dishes',
    mode: 'list',
    icon: 'el-icon-food',
    description: '维护菜品分类、适用餐次、食材、营养标签和启用状态。',
    actions: ['添加', '编辑', '删除', '启用', '停用', '导出'],
    filters: [
      input('dishCode', '菜品编码'), input('dishName', '菜品名称'),
      select('dishCategory', '菜品类别', ['主食', '汤羹', '荤菜', '素菜', '点心', '水果', '饮品']),
      select('mealType', '适用餐次', mealTypes), select('store', '门店', stores), select('enabled', '启用状态', ['启用', '停用'])
    ],
    columns: [
      col('dishCode', '菜品编码', 130), col('dishName', '菜品名称', 150), col('dishCategory', '菜品类别', 105),
      col('mealType', '适用餐次', 110), col('ingredients', '主要食材', 200), col('nutrition', '营养说明', 180),
      col('tabooTag', '禁忌标签', 140), col('unit', '单位', 75), col('standardPrice', '标准售价', 100, false, true),
      col('store', '所属门店', 150), col('enabled', '启用状态', 95, true), col('creator', '录入人', 100),
      col('createdAt', '录入时间', 150)
    ],
    formFields: dishFields
  }),
  膳食套餐: withMeta({
    key: 'diet-packages',
    mode: 'list',
    icon: 'el-icon-box',
    description: '维护膳食套餐周期、餐次标准、金额及适用客户。',
    actions: ['添加', '编辑', '删除', '设置餐次', '启用', '停用', '导出'],
    filters: [
      input('packageCode', '套餐编码'), input('packageName', '套餐名称'), select('store', '所属门店', stores),
      select('customerType', '适用客户', ['入住客户', '散客', '陪护人员', '员工']), select('enabled', '启用状态', ['启用', '停用'])
    ],
    columns: [
      col('packageCode', '套餐编码', 130), col('packageName', '套餐名称', 170), col('store', '所属门店', 150),
      col('cycleDays', '套餐天数', 100), col('mealStandard', '餐次标准', 170),
      col('packageAmount', '套餐金额', 105, false, true), col('customerType', '适用客户', 105),
      col('effectiveDate', '生效日期', 110), col('expiryDate', '失效日期', 110),
      col('enabled', '启用状态', 95, true), col('creator', '录入人', 100), col('createdAt', '录入时间', 150)
    ],
    formFields: packageFields
  }),
  膳食统计: withMeta({
    key: 'diet-statistics',
    mode: 'summary',
    icon: 'el-icon-data-analysis',
    description: '按日期、门店、客户和餐次汇总计划、制作、配送与退餐数量。',
    queryActions: ['查询', '导出', '打印'],
    filters: [
      dateRange('mealRange', '用餐日期'), select('store', '门店', stores), input('customerName', '客户姓名'),
      select('customerType', '客户类型', ['入住客户', '散客', '陪护人员', '员工']), select('mealType', '餐次', mealTypes),
      choiceList('floor', '楼层', floorChoices)
    ],
    columns: [
      col('statDate', '统计日期', 110), col('store', '门店', 150), col('mealType', '餐次', 100),
      col('plannedCount', '计划份数', 100), col('preparedCount', '制作份数', 100),
      col('deliveredCount', '配送份数', 100), col('signedCount', '签收份数', 100),
      col('returnedCount', '退餐份数', 100), col('completionRate', '完成率', 95),
      col('customerCount', '客户人数', 100), col('remark', '备注', 180)
    ]
  }),
  送餐统计: withMeta({
    key: 'delivery-statistics',
    mode: 'summary',
    icon: 'el-icon-truck',
    description: '汇总送餐任务、配送人员、签收、超时与退餐情况。',
    queryActions: ['查询', '导出', '打印'],
    filters: [
      dateRange('deliveryRange', '送餐日期'), select('store', '门店', stores), select('mealType', '餐次', mealTypes),
      input('deliveryStaff', '送餐人员'), select('deliveryStatus', '送餐状态', ['待配送', '配送中', '已签收', '已退餐', '配送异常']),
      choiceList('floor', '楼层', floorChoices)
    ],
    columns: [
      col('deliveryDate', '送餐日期', 110), col('store', '门店', 150), col('mealType', '餐次', 100),
      col('deliveryStaff', '送餐人员', 105), col('taskCount', '任务数', 90), col('signedCount', '已签收', 90),
      col('timeoutCount', '超时数', 90), col('returnedCount', '退餐数', 90), col('completionRate', '完成率', 95),
      col('firstDeliveryAt', '首次配送时间', 145), col('lastSignedAt', '最后签收时间', 145)
    ]
  }),
  营养汤设置: withMeta({
    key: 'nutrition-soups',
    mode: 'list',
    icon: 'el-icon-cold-drink',
    description: '配置营养汤名称、食材、供应时段、适用人群与禁忌。',
    actions: ['添加', '编辑', '删除', '启用', '停用'],
    filters: [
      input('soupName', '营养汤名称'), select('store', '所属门店', stores),
      select('supplyType', '供应类型', ['常规营养汤', '产后调理汤', '特殊医嘱汤']),
      select('enabled', '启用状态', ['启用', '停用'])
    ],
    columns: [
      col('soupCode', '营养汤编码', 135), col('soupName', '营养汤名称', 160), col('supplyType', '供应类型', 130),
      col('ingredients', '主要食材', 200), col('supplyPeriod', '供应时段', 120),
      col('applicableCustomer', '适用客户', 140), col('contraindication', '禁忌说明', 180),
      col('standardPrice', '标准价格', 100, false, true), col('store', '所属门店', 150),
      col('enabled', '启用状态', 95, true), col('creator', '录入人', 100)
    ],
    formFields: soupFields
  }),
  营养汤统计: withMeta({
    key: 'nutrition-soup-statistics',
    mode: 'summary',
    icon: 'el-icon-pie-chart',
    description: '统计营养汤计划、领取、配送、签收和退回情况。',
    queryActions: ['查询', '导出', '打印'],
    filters: [
      dateRange('supplyRange', '供应日期'), select('store', '门店', stores), input('soupName', '营养汤名称'),
      input('customerName', '客户姓名'), select('supplyStatus', '供应状态', ['待制作', '待配送', '已签收', '已退回'])
    ],
    columns: [
      col('supplyDate', '供应日期', 110), col('store', '门店', 150), col('soupName', '营养汤名称', 160),
      col('plannedQuantity', '计划数量', 100), col('preparedQuantity', '制作数量', 100),
      col('deliveredQuantity', '配送数量', 100), col('signedQuantity', '签收数量', 100),
      col('returnedQuantity', '退回数量', 100), col('completionRate', '完成率', 95), col('remark', '备注', 180)
    ]
  }),
  客餐供应: withMeta({
    key: 'guest-meal-supply',
    mode: 'list',
    icon: 'el-icon-s-order',
    description: '登记散客、陪护及员工客餐供应、结算与签收。',
    actions: ['添加', '编辑', '删除', '确认供应', '确认签收', '打印'],
    filters: [
      input('customerName', '客户姓名'), input('room', '房间号'), select('store', '门店', stores),
      select('customerType', '客户类型', ['散客', '陪护人员', '员工']), dateRange('supplyRange', '供应日期'),
      select('supplyStatus', '供应状态', ['待供应', '已供应', '已签收', '已取消'])
    ],
    columns: [
      col('supplyNo', '供应单号', 145), col('supplyDate', '供应日期', 110), col('customerName', '客户姓名', 110),
      col('customerType', '客户类型', 105), col('room', '房间号', 90), col('store', '门店', 150),
      col('mealType', '餐次', 100), col('dishName', '菜品/套餐', 160), col('quantity', '数量', 80),
      col('amount', '金额', 95, false, true), col('paymentMethod', '结算方式', 105),
      col('supplyStatus', '供应状态', 100, true), col('signedAt', '签收时间', 145)
    ],
    formFields: orderFields
  }),
  食材采购: withMeta({
    key: 'ingredient-purchases',
    mode: 'list',
    icon: 'el-icon-shopping-cart-full',
    description: '按餐单需求汇总食材采购申请、审核、到货和入库。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '导出', '打印'],
    filters: [
      input('purchaseNo', '采购单号'), input('ingredientName', '食材名称'), select('store', '门店', stores),
      input('supplier', '供应商'), select('auditStatus', '审核状态', ['待提交', '待审核', '已审核']),
      select('arrivalStatus', '到货状态', ['待到货', '部分到货', '已到货']), dateRange('purchaseRange', '采购日期')
    ],
    columns: [
      col('purchaseNo', '采购单号', 150), col('purchaseDate', '采购日期', 110), col('store', '采购门店', 150),
      col('ingredientName', '食材名称', 150), col('specification', '规格', 110), col('unit', '单位', 70),
      col('plannedQuantity', '计划数量', 100), col('purchaseQuantity', '采购数量', 100),
      col('unitPrice', '采购单价', 95, false, true), col('amount', '采购金额', 100, false, true),
      col('supplier', '供应商', 150), col('auditStatus', '审核状态', 100, true),
      col('arrivalStatus', '到货状态', 100, true), col('creator', '制单人', 100)
    ],
    formFields: [
      date('purchaseDate', '采购日期', true), select('store', '采购门店', stores, true),
      input('ingredientName', '食材名称', true), input('specification', '规格'), input('unit', '单位', true),
      number('plannedQuantity', '计划数量'), number('purchaseQuantity', '采购数量', true),
      number('unitPrice', '采购单价', true), input('supplier', '供应商', true), textarea('remark', '采购说明')
    ]
  }),
  膳食销售: withMeta({
    key: 'diet-sales',
    mode: 'list',
    icon: 'el-icon-money',
    description: '登记膳食套餐、单点餐品及营养汤销售与收款状态。',
    actions: ['添加', '编辑', '删除', '收款', '退款', '审核', '反审核', '导出', '打印'],
    filters: [
      input('saleNo', '销售单号'), input('customerName', '客户姓名'), select('store', '销售门店', stores),
      select('saleType', '销售类型', ['膳食套餐', '单点餐品', '营养汤', '客餐']),
      select('paymentStatus', '收款状态', ['未收款', '部分收款', '已收款', '已退款']),
      select('auditStatus', '审核状态', ['待审核', '已审核']), dateRange('saleRange', '销售日期')
    ],
    columns: [
      col('saleNo', '销售单号', 150), col('saleDate', '销售日期', 110), col('customerName', '客户姓名', 110),
      col('room', '房间号', 90), col('store', '销售门店', 150), col('saleType', '销售类型', 110),
      col('itemName', '销售项目', 170), col('quantity', '数量', 80), col('saleAmount', '销售金额', 100, false, true),
      col('receivedAmount', '已收金额', 100, false, true), col('paymentStatus', '收款状态', 100, true),
      col('auditStatus', '审核状态', 100, true), col('salesperson', '销售人员', 105)
    ],
    formFields: orderFields
  }),
  订餐列表: withMeta({
    key: 'meal-orders',
    mode: 'list',
    icon: 'el-icon-tickets',
    description: '管理客户点餐、备餐、配送、签收、退餐和结算状态。',
    actions: ['添加', '编辑', '删除', '确认下单', '开始备餐', '开始配送', '确认签收', '退餐', '打印'],
    filters: [
      input('orderNo', '订餐单号'), input('customerName', '客户姓名'), input('room', '房间号'),
      select('store', '门店', stores), select('mealType', '餐次', mealTypes),
      select('orderStatus', '订单状态', ['待确认', '待备餐', '备餐中', '配送中', '已签收', '已退餐', '已取消']),
      dateRange('orderRange', '订餐日期')
    ],
    columns: [
      col('orderNo', '订餐单号', 150), col('mealDate', '用餐日期', 110), col('mealType', '餐次', 100),
      col('customerName', '客户姓名', 110), col('room', '房间号', 90), col('store', '门店', 150),
      col('dishName', '菜品/套餐', 170), col('quantity', '数量', 80), col('amount', '金额', 95, false, true),
      col('deliveryAddress', '送餐位置', 140), col('orderStatus', '订单状态', 100, true),
      col('orderedAt', '下单时间', 145), col('signedAt', '签收时间', 145), col('remark', '备注', 180)
    ],
    formFields: orderFields
  }),
  餐卡管理: withMeta({
    key: 'meal-cards',
    mode: 'list',
    icon: 'el-icon-bank-card',
    description: '维护餐卡开户、充值、挂失、恢复和余额状态。',
    actions: ['开卡', '充值', '编辑', '挂失', '恢复', '退卡', '打印'],
    filters: [
      input('cardNo', '餐卡卡号'), input('customerName', '客户姓名'), input('mobile', '联系电话'),
      select('store', '所属门店', stores), select('cardStatus', '餐卡状态', ['正常', '挂失', '已退卡'])
    ],
    columns: [
      col('cardNo', '餐卡卡号', 150), col('customerName', '客户姓名', 110), col('mobile', '联系电话', 130),
      col('room', '房间号', 90), col('store', '所属门店', 150), col('openedAt', '开卡日期', 110),
      col('totalRecharge', '累计充值', 100, false, true), col('totalConsume', '累计消费', 100, false, true),
      col('balance', '当前余额', 100, false, true), col('cardStatus', '餐卡状态', 95, true),
      col('operator', '操作人', 100), col('lastOperatedAt', '最后操作时间', 150)
    ],
    formFields: [
      input('customerName', '客户姓名', true), input('mobile', '联系电话'), input('room', '房间号'),
      select('store', '所属门店', stores, true), number('openingAmount', '开卡金额'),
      number('rechargeAmount', '充值金额'), textarea('remark', '备注')
    ]
  }),
  餐卡消费报表: withMeta({
    key: 'meal-card-consumption-report',
    mode: 'summary',
    icon: 'el-icon-document',
    description: '查询餐卡充值、消费、退款及余额变动明细。',
    queryActions: ['查询', '导出', '打印'],
    filters: [
      input('cardNo', '餐卡卡号'), input('customerName', '客户姓名'), select('store', '门店', stores),
      select('transactionType', '业务类型', ['开卡', '充值', '消费', '退款', '退卡']),
      input('operator', '操作人'), dateRange('transactionRange', '业务日期')
    ],
    columns: [
      col('transactionNo', '流水号', 150), col('transactionAt', '业务时间', 150), col('cardNo', '餐卡卡号', 150),
      col('customerName', '客户姓名', 110), col('store', '门店', 150), col('transactionType', '业务类型', 95, true),
      col('beforeBalance', '变动前余额', 105, false, true), col('amount', '变动金额', 100, false, true),
      col('afterBalance', '变动后余额', 105, false, true), col('relatedDocumentNo', '关联单号', 150),
      col('operator', '操作人', 100), col('remark', '备注', 180)
    ]
  })
}

applyOriginalEvidence('diet', dietPageConfigs)
applyAuditedSurfaceEvidence('diet', dietPageConfigs)

export function getDietPageConfig(title) {
  return dietPageConfigs[title] || dietPageConfigs.客户餐单
}
