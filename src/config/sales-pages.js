const stores = ['中心广场旗舰店', '黄河路轻奢店']
const customerStatuses = ['意向A', '意向B', '意向C', '意向D', '签单客户', '同意签合同', '已签合同但未入住', '已订房', '已入住', '已退房已结账', '流失客户']
const contractAuditStatuses = ['待完善', '待提交', '待审核', '审核通过', '合同已结束', '合同中途结束', '驳回', '合同已作废']
const contractCustomerStatuses = ['未订房', '已订房', '已入住', '备孕']
const contractFilterTypes = ['月子合同', '婴儿托管', '试住合同', '续住合同', '小月子合同', '到家合同']
const paymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '转账汇款', '押金', '优惠券', '积分支付', '星pos支付', '欠款消费']
const salesPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '押金', '会员卡', '优惠券', '积分支付', '星pos支付', '欠款消费']
const productSalesTypes = ['项目销售', '物料销售', '卡类销售', '综合销售', '积分物料', '积分项目']
const salesDetailTypes = ['项目销售', '物料销售', '膳食销售', '卡类销售', '积分物料', '积分项目']
const inStoreCustomerStatuses = ['店内客户', '散客客户']
const projectProductTypes = ['产后类', '产康服务', '大礼包', '护理服务', '客房服务', '科颜肌肤', '软硬件服务', '膳食服务', '增值服务']
const materialProductTypes = ['办公用品', '办公用纸类', '办公用笔类', '低值易耗品', '产康仪器及耗材', '一次性用品', '清洁类物品', '布草类物品', '服装类物品', '鞋类物品', '消毒类物品', '生活用纸制品', '活动物料', '护理物品', '护理套盒', '十月结晶', '美德乐', '维修物料', '后厨物品', '后厨餐具', '后厨易耗品']
const couponTypes = ['现金券', '积分券', '体验券', '折扣券', '疗程现金优惠券', '产后券', '早教券', '商品券']
const discountCouponTypes = ['产后券', '早教券', '商品券', '现金券', '积分券', '体验券', '折扣券', '疗程现金优惠券']

const input = (key, label, required = false) => ({ key, label, type: 'input', required })
const select = (key, label, options, required = false) => ({ key, label, type: 'select', options, required })
const dependentSelect = (key, label, dependsOn, optionsByDependency) => ({ key, label, type: 'select', dependsOn, optionsByDependency })
const dateRange = (key, label) => ({ key, label, type: 'dateRange' })
const date = (key, label, dateType = 'date', required = false) => ({ key, label, type: 'date', dateType, required })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required })
const number = (key, label, required = false, precision = 2) => ({ key, label, type: 'number', required, precision })
const switchField = (key, label) => ({ key, label, type: 'switch' })
const col = (key, label, width = 120, tag = false, money = false) => ({ key, label, width, tag, money })

const auditFields = [
  select('auditResult', '审核状态', ['审核通过', '审核不通过'], true),
  textarea('auditRemark', '审核意见', true)
]

const saleBaseFields = [
  input('customerName', '客户姓名', true), input('room', '房间号'), select('customerStatus', '客户状态', customerStatuses),
  input('mobile', '手机号码'), select('store', '销售分店', stores, true), date('saleDate', '销售日期', 'date', true),
  input('salesperson', '销售人员', true), number('totalAmount', '商品总价'), number('paymentAmount', '支付金额'),
  switchField('receiveNow', '立即收款'), input('introducer', '介绍人'), input('introducerMobile', '介绍电话'),
  select('saleType', '销售类型', productSalesTypes),
  dependentSelect('productType', '商品类型', 'saleType', { 项目销售: projectProductTypes, 服务销售: projectProductTypes, 物料销售: materialProductTypes }),
  select('paymentMethod', '支付方式', salesPaymentMethods), textarea('remark', '备注'),
  select('giftType', '赠送类型', ['签单赠送', '补偿赠送', '活动赠送']), textarea('giftReason', '赠送理由')
]

export const salesPageConfigs = {
  '合同管理': {
    key: 'contracts', icon: 'el-icon-document', description: '贯通客户签约、套餐房型、入住安排、优惠、收款、审核与合同变更。',
    actions: ['添加', '删除', '编辑', '导出', '设置', '审核', '打印', '反审核', '流程审批', '提交', '取消', '套餐升级', '膳食套餐', '编辑模板', '变更', '远程签约', '折扣率审核'],
    filters: [input('customerName', '客户姓名'), input('contractNo', '合同编号'), input('salesperson', '签单人员'), select('auditStatus', '审核状态', contractAuditStatuses), select('customerStatus', '客户状态', contractCustomerStatuses), select('contractType', '合同类型', contractFilterTypes), dateRange('dueRange', '预产期'), select('checkedIn', '是否入住', ['已入住', '未入住']), dateRange('signedRange', '签单日期')],
    storeOptions: ['全部', ...stores],
    filterTips: ['折扣率=成交金额/参考价格', '未入账金额=已收款未审核的金额'],
    defaultFilters: { auditStatus: '待审核' },
    columns: [
      col('contractNo', '合同编码', 145), col('packageName', '套餐名称', 130), col('customerName', '客户姓名'), col('mobile', '手机号', 125),
      col('arrivalStatus', '到店状态', 100, true), col('directArrival', '直接到店'), col('checkedIn', '是否到店'), col('auditStatus', '审核状态', 105, true),
      col('salesperson', '签单人'), col('dealAmount', '合同最终成交金额', 135, false, true), col('receivedAmount', '合同已收款', 110, false, true), col('refundAmount', '合同退款', 100, false, true),
      col('debtAmount', '合同欠款', 100, false, true), col('unpostedAmount', '未入账金额', 105, false, true), col('discountAmount', '合同优惠金额', 115, false, true), col('postPaymentDiscount', '收款后优惠', 105, false, true),
      col('receivableAmount', '应收金额', 100, false, true), col('contractDays', '合同天数'), col('discountRate', '折扣率'), col('dueDate', '预产期'), col('signedAt', '合同签订日期', 120),
      col('roomType', '预定房型'), col('room', '房号'), col('fetusType', '胎型'), col('checkInAt', '入住日期'), col('checkOutAt', '离开日期'),
      col('extensionAmount', '续住金额', 100, false, true), col('extensionReceived', '已收续住金额', 110, false, true), col('extensionDebt', '续住欠款', 100, false, true),
      col('upgradeAmount', '升级金额', 100, false, true), col('upgradeReceived', '已收升级金额', 110, false, true), col('upgradeDebt', '升级欠款', 100, false, true),
      col('finalAmount', '合同最终额', 110, false, true), col('salesDepartment', '签单人部门'), col('remark', '合同备注', 180), col('creator', '录入人'), col('store', '签单门店', 140),
      col('nursingType', '护理类型'), col('remoteSign', '远程签约'), col('discountAudit', '折扣率审核', 110, true), col('customerSource', '客户来源'), col('firstOrder', '是否首单'),
      col('createdAt', '录入日期', 150), col('contractType', '合同类型'), col('changed', '是否变更'), col('auditTrail', '审批记录', 150)
    ],
    formFields: [
      input('customerName', '选择客户', true), input('mobile', '手机号'), select('idType', '证件类别', ['中国大陆居民身份证', '香港来往大陆通行证', '澳门来往大陆通行证', '台湾来往大陆通行证', '护照']), input('idNo', '证件号'),
      date('birthday', '客户生日'), input('age', '客户年龄'), input('address', '居住地址'), select('store', '签单门店', stores, true), date('signedAt', '合同签订日期', 'date', true), input('salesperson', '选择签单人', true),
      select('roomType', '房间类型', ['豪华套房', '舒适大床', '温馨雅间', '尊享套房', '5楼VIP', '总统套房']), select('nursingType', '护理类型', ['普通护理', '一对一护理'], true), input('occupation', '客户职业'), date('dueDate', '客户预产期'),
      input('contractNo', '合同编码', true), select('mealPackage', '膳食套餐', ['排餐', '点餐']), date('checkInAt', '预住日期'), number('contractDays', '预住天数', false, 0), date('checkOutAt', '预离店日期'), input('hospital', '产检医院'),
      select('pregnancyCount', '本次胎次', ['一胎', '二胎', '三胎', '四胎', '五胎', '六胎']), select('fetusType', '客户胎型', ['不详', '单胎', '双胎', '三胎', '多胎']), select('contractType', '合同类型', ['月子护理', '婴儿托管', '试住合同']),
      switchField('firstOrder', '是否首单'), switchField('companionMeal', '是否有陪护餐'), switchField('enabled', '启用当前合同'), select('packageName', '合同套餐', ['基础套餐', '修复套餐', '修养套餐', '私享套餐', '女王套餐', '总统套餐']),
      number('dealAmount', '合同成交金额', true), select('discountType', '优惠类型', ['活动优惠', '股东优惠', '介绍费抵扣', '礼包抵减', '妈妈护理抵减', '宝宝护理抵减', '其他优惠']), number('discountAmount', '优惠金额'),
      select('paymentType', '款项类型', ['合同首付', '合同收款']), select('paymentMethod', '支付方式', paymentMethods), number('receivedAmount', '收款金额'), textarea('remark', '客户备注')
    ],
    auditFields,
    metrics: ['合同总量', '待审核', '本月签约', '合同欠款']
  },
  '商品销售': {
    key: 'product-sales', icon: 'el-icon-shopping-bag-1', description: '统一管理项目、物料、卡类、综合及积分销售，以及支付、出库、退货、换货与折扣审核。',
    actions: ['服务销售', '物料销售', '卡类销售', '编辑', '删除', '导出', '打印', '退货', '取消', '收款', '是否启用', '出库', '星支付', '变更', '介绍分配', '取消退货', '折扣率审核'],
    filters: [
      input('saleNo', '单据编号'), input('customerName', '客户姓名'), select('saleType', '销售类型', productSalesTypes),
      select('paymentStatus', '单据状态', ['未支付', '已支付', '已取消', '已付未出库', '已出库', '已出库未支付', '换货退货']),
      select('paymentMethod', '支付类型', salesPaymentMethods),
      dependentSelect('productType', '商品类型', 'saleType', { 项目销售: projectProductTypes, 物料销售: materialProductTypes }),
      select('customerStatus', '客户状态', inStoreCustomerStatuses), select('source', '数据来源', ['PC端', '移动端']),
      select('store', '销售分店', stores), select('showReturns', '是否显示退货', ['正常', '已退货', '已取消']),
      dateRange('saleRange', '单据日期'), input('warehouse', '销售仓库')
    ],
    defaultFilters: { source: 'PC端' },
    columns: [col('saleNo', '销售单编号', 150), col('customerNo', '客户号'), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('saleType', '销售类型', 100, true), col('paymentMethod', '支付方式'), col('consumeAmount', '消费金额', 105, false, true), col('couponAmount', '优惠券金额', 105, false, true), col('debtAmount', '欠款金额', 100, false, true), col('salesperson', '销售人'), col('department', '录单所在部门', 120), col('paymentStatus', '支付状态', 110, true), col('saleDate', '销售日期', 120), col('createdAt', '制单日期', 150), col('creator', '制单人'), col('store', '销售分店', 140), col('financeAudit', '财务审核', 100, true), col('source', '订单来源'), col('introducer', '介绍人'), col('introducerMobile', '介绍电话', 120), col('remark', '销售备注', 180), col('paymentRemark', '支付备注', 180), col('discountAudit', '最低折扣审核', 115, true), col('customerSource', '客户来源'), col('attachment', '附件'), col('outboundNo', '出库单号', 140)],
    formFields: saleBaseFields,
    lineColumns: [col('itemNo', '商品编号'), col('itemName', '商品名称', 150), col('unit', '单位'), col('price', '单价', 90, false, true), col('discountPrice', '折后单价', 95, false, true), col('discountRate', '折扣率'), col('quantity', '数量'), col('total', '折后金额', 100, false, true), col('validDays', '有效天数'), col('warehouse', '所属仓库', 140), col('remark', '备注', 150)],
    metrics: ['销售单量', '待支付', '待出库', '本月销售额']
  },
  '销售明细': {
    key: 'sales-details', icon: 'el-icon-s-data', description: '按商品、销售单、客户、门店和支付状态穿透查询所有销售明细。',
    actions: ['项目销售', '物料销售', '卡类销售', '膳食销售', '导出'],
    filters: [
      input('itemName', '商品名称'), input('saleNo', '销售单号'), input('productType', '商品类型'), input('customerName', '客户姓名'),
      select('saleType', '销售类型', salesDetailTypes),
      select('paymentStatus', '单据状态', ['未支付', '已支付', '已取消', '已付未出库', '已退货', '已出库未支付', '换货退货']),
      select('source', '数据来源', ['PC端', '移动端']), select('paymentMethod', '支付类型', salesPaymentMethods),
      select('store', '销售分店', stores), select('stayStore', '入住分店', stores), dateRange('saleRange', '单据日期')
    ],
    defaultFilters: { store: '中心广场旗舰店' },
    columns: [col('detailNo', '编号', 130), col('itemName', '商品名称', 150), col('unit', '单位'), col('productType', '商品类型'), col('quantity', '数量'), col('price', '价格', 90, false, true), col('total', '总价', 100, false, true), col('taxRate', '税率'), col('remark', '备注', 160), col('saleNo', '销售单号', 145), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('paymentMethod', '支付方式'), col('saleType', '销售类型', 100, true), col('paymentStatus', '支付状态', 105, true), col('saleDate', '销售日期', 120), col('salesperson', '销售人'), col('createdAt', '制单日期', 150), col('store', '销售分店', 140), col('stayStore', '入住分店', 140), col('source', '订单来源'), col('saleRemark', '销售备注', 170), col('paymentRemark', '支付备注', 170)],
    formFields: saleBaseFields,
    lineColumns: [col('itemName', '商品名称'), col('unit', '单位'), col('price', '单价', 90, false, true), col('quantity', '数量'), col('total', '金额', 100, false, true)],
    metrics: ['明细数量', '服务销售', '物料销售', '销售总额']
  },
  '套餐管理': {
    key: 'packages', icon: 'el-icon-box', description: '维护月子套餐基础信息、房型、项目明细、众筹规则以及审核启用状态。',
    actions: ['添加', '流程审批', '编辑', '删除', '设置', '提交', '审核', '复制', '启用', '反审核', '推荐/取消', '屏蔽/取消'],
    filters: [input('packageName', '套餐名称'), select('store', '所属分店', stores), select('enabled', '启用状态', ['未启用', '启用']), select('auditStatus', '审核状态', ['待审核', '审核通过', '待提交'])],
    defaultFilters: { auditStatus: '待审核' },
    columns: [col('packageNo', '套餐编号', 135), col('packageName', '套餐名称', 150), col('packageAmount', '套餐价格', 105, false, true), col('roomType', '套餐房型'), col('auditStatus', '审核状态', 105, true), col('enabled', '是否启用', 95, true), col('visible', '是否显示'), col('enabledAt', '启用时间', 150), col('recommended', '是否推荐'), col('recommendedAt', '推荐时间', 150), col('creator', '录入人'), col('store', '所属分店', 140)],
    formFields: [input('packageName', '套餐名称', true), date('enabledAt', '启用时间'), number('packageDays', '套餐天数', true, 0), select('store', '所属门店', stores), number('packageAmount', '套餐总金额', true), number('referencePrice', '参考价'), select('packageType', '套餐类型', ['正常套餐', '小月子套餐', '众筹套餐'], true), select('roomType', '套餐房型', ['豪华套房', '舒适大床', '温馨雅间', '尊享套房', '5楼VIP', '总统套房']), date('deadline', '有效截止日期'), number('crowdfundingDays', '众筹期限', false, 0), input('title', '套餐标题'), textarea('details', '套餐详情'), textarea('roomInfo', '房型信息')],
    lineColumns: [col('itemNo', '项目编号'), col('itemName', '项目名称', 150), col('itemType', '项目类别'), col('unit', '单位'), col('discountPrice', '折扣价', 90, false, true), col('onDemand', '按需'), col('quantity', '数量'), col('validDays', '项目有效期'), col('total', '总价', 100, false, true), col('store', '分店', 140), col('remark', '备注', 150)],
    auditFields,
    metrics: ['套餐总数', '待审核', '已启用', '已推荐']
  },
  '卡类套餐': {
    key: 'card-packages', icon: 'el-icon-bank-card', description: '配置次卡、年卡、套餐卡和储值卡的项目、有效期、价格及折扣规则。',
    actions: ['添加', '编辑', '删除', '复制'],
    filters: [input('cardName', '卡类名称'), select('enabled', '启用状态', ['未启用', '启用']), select('store', '所属门店', stores)],
    columns: [col('cardNo', '卡片编号', 135), col('cardName', '卡片名称', 150), col('packageAmount', '套餐总金额', 110, false, true), col('auditStatus', '审核状态', 105, true), col('enabled', '是否启用', 95, true), col('itemType', '项目类型'), col('validDays', '有效天数'), col('cardType', '卡类型'), col('enabledAt', '启用时间', 150), col('store', '分店', 140), col('visible', '是否显示'), col('creator', '录入人')],
    formFields: [input('cardName', '卡类名称', true), date('enabledAt', '启用时间'), number('validDays', '有效天数', true, 0), number('packageAmount', '套餐总金额', true), select('cardType', '项目卡类型', ['次卡', '年卡', '套餐卡', '储值卡'], true), number('cardCount', '次数', false, 0), select('store', '所属门店', stores), number('referencePrice', '参考价'), switchField('fixedItems', '固定服务项目'), select('itemCategory', '项目卡类别', ['产后类', '产康服务', '护理服务', '膳食服务', '客房服务', '增值服务', '软硬件服务', '大礼包', '科颜肌肤']), switchField('enabled', '是否启用'), switchField('discountEnabled', '启用折扣'), select('saleType', '销售类型', ['服务销售', '卡类销售']), textarea('details', '卡类详情')],
    lineColumns: [col('itemNo', '项目编号'), col('itemName', '项目名称', 150), col('itemType', '项目类别'), col('unit', '单位'), col('discountPrice', '折扣价', 90, false, true), col('quantity', '数量'), col('total', '总价', 100, false, true)],
    metrics: ['卡类总数', '次卡', '套餐卡', '已启用']
  },
  '赠送管理': {
    key: 'gift-lists', icon: 'el-icon-present', description: '维护签约或活动使用的赠送物品清单及物料明细。',
    actions: ['添加', '编辑', '删除', '导出'],
    filters: [input('listName', '清单名称'), select('store', '所属分店', stores), select('enabled', '启用状态', ['启用', '未启用'])],
    columns: [col('listNo', '清单编号', 140), col('listName', '清单名称', 160), col('enabled', '是否启用', 100, true), col('enabledAt', '启用时间', 150), col('store', '所属分店', 140)],
    formFields: [input('listNo', '清单编号', true), input('listName', '清单名称', true), date('enabledAt', '启用时间'), select('store', '所属门店', ['公共', ...stores]), switchField('enabled', '是否启用')],
    lineColumns: [col('materialNo', '物料编码', 135), col('materialName', '物料名称', 150), col('materialType', '物料类别'), col('specification', '规格型号'), col('unit', '单位'), col('price', '单价', 90, false, true), col('quantity', '数量'), col('total', '总价', 100, false, true), col('remark', '备注', 150)],
    metrics: ['清单总数', '已启用', '公共清单', '物料数量']
  },
  '优惠管理': {
    key: 'discounts', icon: 'el-icon-discount', description: '管理客户优惠记录、金额余额、使用期限、审核和停用状态。',
    actions: ['添加', '编辑', '删除', '导出', '审核', '反审核', '停用'],
    filters: [input('customerName', '客户姓名'), select('couponType', '优惠券类型', discountCouponTypes), select('store', '所属分店', stores), select('auditStatus', '审核状态', ['已通过', '待审核']), dateRange('createdRange', '制单日期')],
    columns: [col('discountNo', '编号', 135), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('couponName', '优惠券名称', 150), col('couponType', '优惠券类型'), col('itemType', '优惠项目类型', 120), col('quantity', '数量'), col('couponAmount', '优惠券金额', 110, false, true), col('remainingAmount', '剩余金额', 100, false, true), col('validDays', '有效天数'), col('deadline', '截止日期', 120), col('auditStatus', '审核状态', 105, true), col('auditor', '审核人'), col('auditRemark', '审核意见', 160), col('remark', '备注', 170), col('creator', '制单人'), col('createdAt', '制单时间', 150), col('store', '分店', 140), col('status', '状态', 95, true), col('disableReason', '停用说明', 170)],
    formFields: [input('customerName', '选择客户', true), input('discountNo', '优惠券编号', true), input('couponName', '优惠券名称', true), number('couponAmount', '优惠券金额', true), select('couponType', '优惠券类型', discountCouponTypes, true), select('store', '所属分店', stores), select('limitType', '限制消费类型', ['项目', '商品']), select('consumeType', '消费类型', ['产后类', '产康服务', '护理服务', '膳食服务', '物料商品']), input('consumeItem', '消费项目/商品'), select('validType', '使用类型', ['时间段', '有效期']), date('startsAt', '优惠开始时间'), date('endsAt', '优惠结束时间'), number('validDays', '有效期', false, 0), textarea('useRule', '使用规则'), switchField('receivePayment', '是否收款'), textarea('remark', '优惠券备注')],
    auditFields,
    metrics: ['优惠记录', '待审核', '未使用', '剩余金额']
  },
  '优惠券管理': {
    key: 'coupons', icon: 'el-icon-tickets', description: '配置可发行优惠券的额度、数量、领用限制、适用范围和发放形式。',
    actions: ['添加', '编辑', '删除', '分发'],
    filters: [select('couponType', '优惠券类型', couponTypes), select('store', '所属分店', stores)],
    columns: [col('couponNo', '优惠券编码', 140), col('couponName', '优惠券名称', 150), col('couponType', '优惠券类型'), col('itemType', '优惠项目类型', 120), col('couponAmount', '优惠券金额', 110, false, true), col('store', '所属门店', 140), col('startsAt', '开始时间', 150), col('endsAt', '结束时间', 150), col('totalQuantity', '总数量'), col('issuedQuantity', '发放数量'), col('limitPerCustomer', '每客户限领数量', 130), col('creator', '制单人'), col('createdAt', '制单时间', 150)],
    formFields: [input('couponName', '优惠券名称', true), number('couponAmount', '优惠券金额', true), number('totalQuantity', '优惠券数量', true, 0), select('couponType', '优惠券类型', couponTypes, true), select('store', '所属分店', ['全部', ...stores]), select('limitType', '限制消费类型', ['项目', '商品']), select('consumeType', '消费类型', ['产后类', '产康服务', '护理服务', '膳食服务', '物料商品']), input('consumeItem', '消费项目/商品'), date('startsAt', '优惠开始时间', 'date', true), date('endsAt', '优惠结束时间', 'date', true), number('limitPerCustomer', '单客户可领用数量', true, 0), switchField('stackable', '是否叠加'), select('scope', '适用范围', ['所有人', '会员', '非会员']), select('sendType', '发放形式', ['自由领取', '店内发放']), textarea('remark', '优惠券备注')],
    metrics: ['优惠券种类', '可发行数量', '已发数量', '即将到期']
  },
  '赠送项目申请': {
    key: 'gift-applications', icon: 'el-icon-s-claim', description: '发起服务、物料和卡类赠送申请，并完成流程审批、撤回、反审核和出库。',
    actions: ['服务销售', '物料销售', '卡类销售', '流程审批', '删除', '撤回', '反审核'],
    filters: [input('customerName', '客户姓名'), select('auditStatus', '单据状态', ['待审核', '审核通过', '不通过']), select('customerStatus', '客户状态', inStoreCustomerStatuses), select('store', '销售分店', stores), select('giftType', '赠送类型', ['签单赠送', '补偿赠送', '活动赠送']), dateRange('saleRange', '销售日期'), input('warehouse', '销售仓库')],
    defaultFilters: { auditStatus: '待审核' },
    columns: [col('applicationNo', '销售单编号', 150), col('customerNo', '客户号'), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('giftItems', '赠送品项', 180), col('consumeAmount', '消费金额', 105, false, true), col('salesperson', '销售人'), col('department', '录单所在部门', 120), col('auditStatus', '审核状态', 105, true), col('saleDate', '销售日期', 120), col('createdAt', '制单日期', 150), col('store', '销售分店', 140), col('giftType', '赠送类型'), col('giftReason', '赠送理由', 180), col('outboundStatus', '出库', 95, true), col('attachment', '附件'), col('auditTrail', '审核记录', 150)],
    formFields: saleBaseFields,
    lineColumns: [col('itemNo', '商品编号'), col('itemName', '商品名称', 150), col('unit', '单位'), col('price', '单价', 90, false, true), col('discountPrice', '折后单价', 95, false, true), col('quantity', '数量'), col('total', '折后金额', 100, false, true), col('validDays', '有效期'), col('warehouse', '仓库', 140)],
    auditFields,
    metrics: ['申请总量', '待审批', '待出库', '本月赠送']
  }
}

export function getSalesPageConfig(title) {
  return salesPageConfigs[title] || salesPageConfigs['合同管理']
}
