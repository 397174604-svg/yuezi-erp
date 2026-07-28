const stores = ['奇德芬芳·建设路店（中心店）', '奇德芬芳·黄河路店']
const receiptTypes = ['合同首付', '合同补余收款', '合同收款', '其他收款', '押金收款', '诚意金', '会员充值', '续房收款', '服务升级收款', '销售收款', '产康合同收款', '月嫂合同收款']
const createReceiptTypes = ['合同首付', '合同补余收款', '合同收款', '其他收款', '续房收款', '服务升级收款', '销售收款', '产康合同收款', '月嫂合同收款']
const receiptPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '转账汇款', '押金', '会员卡', '优惠券', '积分支付', '赠送', '星pos支付', '订金核销', '信用额度支付', '欠款消费', '客户转卡转账', '积分兑换']
const createPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '押金', '会员卡', '优惠券', '积分支付', '星pos支付']
const refundPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '转账汇款', '押金', '会员卡', '优惠券', '积分支付', '星pos支付', '信用额度支付', '客户转卡转账', '积分兑换']
const payoutMethods = ['现金', 'POS机刷卡', '支付宝付款', '微信结算', '转账汇款']
const banks = ['招商银行', '交通银行', '广发银行', '中国银行', '中国工商银行', '中国建设银行', '中国农业银行', '支付宝', '招商银行（一般户）']
const refundTypes = ['合同退款', '订金退款', '押金退款', '服务升级退款', '会员卡退款', '预付款退款', '其他退款', '销售退款']
const refundChannels = ['退款审批', '押金退款流程']
const refundStatuses = ['待提交', '待审核', '待退款', '已退款', '被驳回']
const feeTypes = ['工资(含绩效）', '提成工资', '社保', '临时工工资', '房屋租赁费', '水电费', '备用金申请单']
const receiptCustomerStatuses = [
  '全部', '意向A', '意向B', '意向C', '意向D', '签单客户', '意向E', '同意签合同',
  '已签合同但未入住', '已签合同但未审核', '已订房', '已入住', '已退房但未结账',
  '已退房已结账', '散客客户', '流失客户'
]

const input = (key, label, required = false) => ({ key, label, type: 'input', required })
const select = (key, label, options, required = false) => ({ key, label, type: 'select', options, required })
const multiSelect = (key, label, options) => ({ key, label, type: 'multiSelect', options })
const dateRange = (key, label) => ({ key, label, type: 'dateRange' })
const date = (key, label, required = false) => ({ key, label, type: 'date', required })
const number = (key, label, required = false) => ({ key, label, type: 'number', required })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required })
const radio = (key, label, options, required = false) => ({ key, label, type: 'radio', options, required })
const checkbox = (key, label) => ({ key, label, type: 'checkbox' })
const picker = (key, label, pickerType, required = false, placeholder = '') => ({ key, label, type: 'picker', pickerType, required, placeholder })
const upload = (key, label) => ({ key, label, type: 'upload' })
const col = (key, label, width = 120, tag = false, money = false) => ({ key, label, width, tag, money })

const workflowAuditFields = [
  radio('auditResult', '审核结果', ['通过', '驳回'], true),
  input('auditRemark', '审核意见', true),
  select('nextNode', '下一审核节点', ['财务审核']),
  input('nextAuditor', '下一审核人'),
  checkbox('sendMessage', '是否发送消息'),
  input('ccUser', '抄送人')
]

const expenseFilters = [
  input('feeTypeName', '费用类型'), input('applicant', '申请人'), input('department', '申请部门'),
  select('feeType', '费用类型', feeTypes), select('store', '费用分店', stores),
  select('payoutType', '打款类型', payoutMethods), dateRange('applyRange', '申请日期')
]

const expenseColumns = [
  col('expenseNo', '费用单号', 145), col('applicant', '用户名'), col('department', '部门'), col('store', '费用分店', 140),
  col('expenseName', '费用名称', 150), col('feeType', '费用类型', 130), col('reason', '申请事由', 180),
  col('payoutType', '打款类别'), col('applyAmount', '申请金额', 105, false, true), col('appliedAt', '申请时间', 150),
  col('approvedAt', '审批时间', 150), col('paidAt', '支付时间', 150), col('status', '状态', 95, true),
  col('invoice', '发票'), col('invoiceType', '发票类型'), col('attachment', '附件')
]

const receiptListColumns = [
  col('receiptNo', '单据编号', 145), col('invoiceStatus', '是否开票'), col('customerName', '客户姓名'), col('mobile', '手机号', 125),
  col('department', '部门'), col('cashier', '收款人'), col('documentDate', '单据日期', 120), col('receiptType', '款项类别', 130),
  col('paymentMethod', '支付方式', 125), col('amount', '含税金额', 105, false, true), col('taxAmount', '税金', 95, false, true),
  col('sourceNo', '原单号', 145), col('creator', '制单人'), col('auditStatus', '财务审核', 105, true), col('auditor', '审核人'),
  col('auditRemark', '审核意见', 150), col('auditedAt', '审核时间', 150), col('store', '收款分店', 140),
  col('createdAt', '制单日期', 150), col('fee', '手续费', 95, false, true), col('receivedAmount', '实收金额', 105, false, true),
  col('bank', '收款银行', 130), col('bankAccount', '银行账号', 145), col('receivedAt', '到账时间', 150),
  col('settled', '是否结算数据'), col('remark', '备注', 180)
]

const prepaidListColumns = [
  col('receiptNo', '单据编号', 145), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('department', '部门'),
  col('cashier', '收款人'), col('documentDate', '单据日期', 120), col('receiptType', '款项类别', 130),
  col('paymentMethod', '支付方式', 125), col('amount', '含税金额', 105, false, true), col('taxAmount', '税金', 95, false, true),
  col('writeOffBalance', '可核销金额', 110, false, true), col('auditStatus', '财务审核', 105, true), col('auditor', '审核人'),
  col('auditRemark', '审核意见', 150), col('writeOffStatus', '核销状态', 100, true), col('store', '收款分店', 140),
  col('fee', '手续费', 95, false, true), col('receivedAmount', '实收金额', 105, false, true),
  col('receivedAt', '到账时间', 150), col('remark', '备注', 180)
]

const debtListColumns = [
  col('receiptNo', '单据编号', 145), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('department', '部门'),
  col('cashier', '收款人'), col('documentDate', '单据日期', 120), col('receiptType', '款项类别', 130),
  col('paymentMethod', '支付方式', 125), col('documentAmount', '单据金额', 105, false, true),
  col('recoverableAmount', '可回款金额', 115, false, true), col('creator', '制单人'), col('store', '收款分店', 140),
  col('contractId', 'htid', 120), col('sourceNo', '原单号', 145), col('remark', '备注', 180)
]

const preauthorizationListColumns = [
  col('receiptNo', '单据编号', 145), col('customerName', '客户姓名'), col('mobile', '手机号', 125), col('department', '部门'),
  col('cashier', '收款人'), col('documentDate', '单据日期', 120), col('receiptType', '款项类别', 130),
  col('paymentMethod', '支付方式', 125), col('documentAmount', '单据金额', 105, false, true), col('creator', '制单人'),
  col('auditStatus', '财务审核', 105, true), col('auditor', '审核人'), col('auditRemark', '审核意见', 150),
  col('store', '收款分店', 140), col('saleNo', '销售单号', 145)
]

export const financePageConfigs = {
  '新增收款': {
    key: 'receipt-create',
    mode: 'form',
    icon: 'el-icon-circle-plus-outline',
    description: '按原 ERP 收款单字段录入客户、款项类别、结算方式、银行、开票及通知信息。',
    actions: ['保存', '星支付', '关闭'],
    formFields: [
      input('receiptNo', '收据编码'), radio('receiptKind', '收款类型', ['收款单', '预收款'], true),
      picker('cashier', '收款人', 'employee', true, '请选择业务员账号'), picker('customerName', '选择客户', 'customer', true, '请选择现有客户'),
      select('receiptType', '款项类别', createReceiptTypes, true), select('paymentMethod', '结算方式', createPaymentMethods, true),
      number('amount', '单据金额', true), number('giftAmount', '赠送金额'), select('store', '收款分店', stores, true),
      input('recoveryLevel', '产康等级'), select('incomeType', '收入类型', ['销售收款', '抵债收款', '期末调汇', '转账', '退票回冲单', '其他收款']),
      select('bank', '收款银行', banks, true), input('bankAccount', '银行帐号'), select('invoiceStatus', '是否开票', ['未开票', '已开票']),
      input('coupon', '优惠券'), date('documentDate', '单据日期', true), textarea('remark', '备注'),
      checkbox('sendWechat', '微信推送'), checkbox('sendSms', '短信发送'), upload('attachment', '上传附件')
    ],
    tips: ['单击“合同收款”时自动带入合同余额', '银行类结算方式必须选择收款银行']
  },
  '收款管理': {
    key: 'receipts', icon: 'el-icon-wallet', description: '查询、导出、审核、核销收款，并维护手续费、到账、开票和跨店核销信息。',
    actions: ['添加', '星支付', '开具发票', '编辑', '删除', '导出', '打印', '审核', '批量审核', '核销', '反审核', '手续费', '扫码支付'],
    filters: [
      input('customerName', '客户名称'), select('receiptType', '款项类别', receiptTypes), select('paymentMethod', '支付方式', receiptPaymentMethods),
      input('department', '收款部门'), input('sourceNo', '原单号'), select('auditStatus', '审核状态', ['待审核', '审核通过', '审核未通过']),
      dateRange('documentRange', '单据日期'), select('settlement', '结算核销', ['全部', '结算核销']),
      multiSelect('customerStatus', '客户状态', receiptCustomerStatuses), multiSelect('store', '门店', ['全部', ...stores])
    ],
    exclusionFilters: [
      checkbox('hideWriteOff', '核销'), checkbox('hideMemberCard', '会员卡'), checkbox('hideCoupon', '优惠券'),
      checkbox('hideZero', '收款为0'), checkbox('hideAdmin', 'admin单据'), checkbox('hideDischarged', '已结账出院')
    ],
    filterLimit: 10,
    columns: receiptListColumns,
    listTabs: [
      { key: 'receipts', label: '收款列表', columns: receiptListColumns, selection: true, index: false, showOperation: false },
      { key: 'prepayments', label: '预收款列表', columns: prepaidListColumns, selection: true, index: false, showOperation: true, operationLabel: '功能' },
      { key: 'debts', label: '欠款列表', columns: debtListColumns, selection: false, index: true, showOperation: false },
      { key: 'preauthorizations', label: '预授权列表', columns: preauthorizationListColumns, selection: true, index: false, showOperation: true, operationLabel: '功能' }
    ],
    defaultFilters: {
      documentRange: ['2026-07-22', '2026-07-23'], settlement: '全部', customerStatus: ['全部'], store: ['全部'],
      hideWriteOff: true, hideMemberCard: false, hideCoupon: true, hideZero: true, hideAdmin: true, hideDischarged: false
    },
    auditFields: [radio('auditResult', '财务审核', ['审核通过', '审核不通过'], true), input('actualAmount', '实收金额', true), number('fee', '手续费'), date('receivedAt', '到账时间'), input('auditRemark', '审核意见')],
    metrics: ['收款单数', '待审核', '实收金额', '可核销余额']
  },
  '退款申请': {
    key: 'refund-applications', icon: 'el-icon-refresh-left', description: '管理退款申请、流程提交、审核记录与最终打款。',
    actions: ['添加', '编辑', '删除', '打印', '提交', '打款', '导出'],
    filters: [
      input('refundNo', '单据编号'), input('customerName', '客户姓名'), select('store', '退款分店', stores),
      select('refundType', '退款类型', refundTypes), select('refundChannel', '退款渠道', refundChannels),
      select('status', '状态', refundStatuses), dateRange('financeRange', '财务日期')
    ],
    columns: [
      col('refundNo', '单据编号', 145), col('auditNo', '审核编号', 135), col('customerName', '客户姓名'), col('mobile', '手机号', 125),
      col('refundType', '退款类型', 125), col('refundChannel', '退款渠道', 115), col('refundAmount', '退款金额', 105, false, true),
      col('creator', '录单员'), col('department', '部门'), col('actualRefund', '实退金额', 105, false, true),
      col('status', '退单状态', 95, true), col('documentDate', '单据日期', 120), col('auditStatus', '审核状态', 100, true),
      col('paymentMethod', '退款方式', 120), col('paidAt', '打款时间', 150), col('payer', '打款人'),
      col('store', '退款分店', 140), col('reason', '退款理由', 180), col('cashier', '收款人'),
      col('bank', '银行名称', 130), col('bankAccount', '银行账号', 145), col('salesperson', '签单人员'), col('saleNo', '销售编号', 145),
      col('auditTrail', '审核记录', 130)
    ],
    formFields: [
      input('refundNo', '单据编号'),
      picker('customerName', '选择客户', 'customer', false, '请选择现有客户'),
      select('store', '退款分店', stores, true),
      select('refundType', '退款类型', refundTypes, true),
      select('refundChannel', '退款渠道', refundChannels, true),
      number('refundAmount', '退款金额', true),
      input('saleNo', '销售编号'),
      textarea('reason', '退款理由', true)
    ],
    auditFields: workflowAuditFields,
    payoutFields: [number('refundAmount', '退款金额'), number('actualRefund', '实退金额', true), select('paymentMethod', '退款方式', refundPaymentMethods, true), date('paidAt', '打款时间', true), input('payee', '收款人', true), select('bank', '银行', banks), input('bankAccount', '银行卡号'), textarea('paymentRemark', '打款说明'), checkbox('sendWechat', '微信'), checkbox('sendSms', '短信')],
    metrics: ['退款申请', '待审核', '待退款', '退款金额']
  },
  '退款审核': {
    key: 'refund-audits', icon: 'el-icon-s-check', description: '集中审核待处理退款，支持流程节点、审核人、消息与抄送。',
    actions: ['流程审批', '反审核', '撤回'],
    filters: [
      input('refundNo', '单据编号'), input('customerName', '客户姓名'), select('store', '退款分店', stores),
      select('auditStatus', '审核状态', refundStatuses), select('refundType', '退款类型', refundTypes),
      select('refundChannel', '退款渠道', refundChannels), dateRange('financeRange', '财务日期')
    ],
    columns: [
      col('refundNo', '单据编号', 145), col('auditNo', '审核编号', 135), col('customerName', '客户姓名'), col('mobile', '手机号', 125),
      col('refundType', '退款类型', 125), col('refundChannel', '退款渠道', 115), col('refundAmount', '退款金额', 105, false, true),
      col('creator', '录单员'), col('department', '部门'), col('actualRefund', '实退金额', 105, false, true),
      col('status', '退单状态', 95, true), col('documentDate', '单据日期', 120), col('auditStatus', '审核状态', 100, true),
      col('paymentMethod', '退款方式', 120), col('store', '退款分店', 140), col('allocationStatus', '分配状态'),
      col('reason', '退款理由', 180), col('saleNo', '销售单号', 145), col('paymentRemark', '打款说明', 180),
      col('bank', '银行', 130), col('bankAccount', '银行卡号', 145), col('payee', '收款人'), col('bankBranch', '开户行', 150)
    ],
    auditFields: workflowAuditFields,
    payoutFields: [number('refundAmount', '退款金额'), number('actualRefund', '实退金额', true), select('paymentMethod', '退款方式', refundPaymentMethods, true), date('paidAt', '打款时间', true), input('payee', '收款人', true), select('bank', '银行', banks), input('bankBranch', '开户行'), input('bankAccount', '银行卡号'), textarea('paymentRemark', '打款说明'), input('attachment', '上传附件')],
    defaultFilters: { auditStatus: '待审核' },
    metrics: ['审核任务', '待审核', '审核通过', '待打款']
  },
  '欠款审核': {
    key: 'debt-audits', icon: 'el-icon-warning-outline', description: '审核客户欠款入住，核对合同、收款、房间和入住理由。',
    actions: ['审核'],
    filters: [input('room', '房间号'), input('customerName', '客户姓名'), select('store', '分店', stores), select('auditStatus', '审核状态', ['待审核', '已通过']), dateRange('stayRange', '预住日期')],
    columns: [
      col('room', '房间名称'), col('customerName', '客户姓名'), col('contractNo', '合同编号', 145), col('packageName', '套餐名称', 140),
      col('dealAmount', '合同成交金额', 120, false, true), col('receivedAmount', '合同已收款', 110, false, true),
      col('roomStatus', '房间状态', 95, true), col('creator', '制单人'), col('checkInAt', '预住日期', 120),
      col('auditStatus', '财务审核状态', 115, true), col('auditor', '审核人'), col('reason', '入住理由', 180), col('store', '分店', 140)
    ],
    auditFields: [select('auditResult', '审核状态', ['审核通过', '审核不通过'], true), textarea('auditRemark', '审核意见')],
    defaultFilters: { auditStatus: '已通过' },
    metrics: ['欠款入住', '待审核', '已通过', '合同欠款']
  },
  '换货审核': {
    key: 'exchange-audits', icon: 'el-icon-sort', description: '查询换货申请并核对原销售、退货、仓库、出库与差价。',
    actions: ['审核', '删除'],
    filters: [input('exchangeNo', '换货单编号'), select('auditStatus', '审核状态', ['已通过', '待审核', '已驳回']), dateRange('applyRange', '申请日期')],
    columns: [
      col('exchangeNo', '换货单编号', 150), col('saleNo', '原销售单编号', 150), col('returnNo', '退货单编号', 150),
      col('customerName', '客户名称'), col('mobile', '手机号', 125), col('exchangeType', '换货类型'),
      col('applicant', '换货申请人'), col('appliedAt', '换货申请时间', 150), col('auditor', '审核人'), col('auditedAt', '审核时间', 150),
      col('auditStatus', '审核状态', 100, true), col('outboundStatus', '是否出库', 95, true), col('warehouse', '仓库', 140),
      col('differenceAmount', '差价', 95, false, true)
    ],
    defaultFilters: { auditStatus: '待审核' },
    metrics: ['换货申请', '待审核', '已通过', '差价金额']
  },
  '发票管理': {
    key: 'invoices', icon: 'el-icon-tickets', description: '查询收付款发票，展示税率、税额、抬头、纳税人及银行信息。',
    actions: ['导出', '删除'],
    filters: [input('customerName', '客户姓名'), input('documentNo', '单据编号'), select('documentType', '单据类别', ['采购入库', '其它入库'])],
    columns: [
      col('invoiceAmount', '发票金额', 105, false, true), col('amount', '金额', 95, false, true), col('taxRate', '税率'), col('taxAmount', '税额', 95, false, true),
      col('documentNo', '单据编号', 145), col('documentType', '单据类型'), col('status', '状态', 95, true), col('createdAt', '添加时间', 150),
      col('invoiceType', '发票类型', 130), col('invoiceNo', '发票编号', 145), col('invoicedAt', '开票时间', 150),
      col('invoiceTitle', '发票抬头', 150), col('customerName', '姓名（单位）', 140), col('invoiceContent', '发票内容', 160),
      col('taxpayerNo', '纳税人识别码', 160), col('registeredAddress', '注册地址', 180), col('registeredPhone', '注册电话', 125),
      col('bank', '开户银行', 140), col('bankAccount', '银行账号', 150)
    ],
    metrics: ['发票数量', '发票金额', '税额', '待开票']
  },
  '部门物料预算': {
    key: 'material-budgets', icon: 'el-icon-s-order', description: '管理部门物料预算单、采购计划关联及流程审批。',
    actions: ['添加', '流程审批', '编辑', '删除', '提交', '生成采购计划', '导出'],
    filters: [input('budgetNo', '单据编号'), input('department', '预算部门'), select('status', '单据状态', ['待提交', '审核中', '审核通过', '已下达', '驳回']), dateRange('budgetRange', '预算日期'), input('remark', '备注')],
    columns: [
      col('budgetNo', '预算单编号', 145), col('budgetDate', '预算日期', 120), col('department', '预算部门', 140),
      col('totalQuantity', '单据总数量'), col('totalAmount', '单据总额', 105, false, true), col('status', '审核状态', 100, true),
      col('creator', '制单人'), col('createdAt', '制单时间', 150), col('purchasePlanNo', '采购计划单号', 150), col('remark', '备注', 180)
    ],
    formFields: [input('budgetNo', '预算单编号', true), date('budgetDate', '预算日期', true), input('department', '预算部门', true), input('purchasePlanNo', '采购计划单号'), textarea('remark', '备注')],
    auditFields: workflowAuditFields,
    defaultFilters: { status: '待提交' },
    metrics: ['预算单数', '待提交', '审核中', '预算总额']
  },
  '我的费用': {
    key: 'my-expenses', icon: 'el-icon-money', description: '查询本人费用申请，处理提交、打款、发票和附件。',
    actions: ['添加', '编辑', '删除', '导出', '打印', '打款', '反审核', '提交'],
    filters: [...expenseFilters, select('status', '状态', ['待提交', '已提交', '已审批', '已打款', '驳回'])],
    columns: expenseColumns,
    formFields: [input('expenseName', '费用名称', true), select('feeType', '费用类型', feeTypes, true), input('applicant', '申请人', true), input('department', '申请部门', true), select('store', '费用分店', stores, true), textarea('reason', '申请事由', true), number('applyAmount', '申请金额', true), input('attachment', '附件')],
    auditFields: workflowAuditFields,
    payoutFields: [number('amount', '打款金额', true), select('payoutType', '打款类型', payoutMethods, true), date('paidAt', '支付时间', true), textarea('paymentRemark', '打款说明'), input('attachment', '附件')],
    defaultFilters: { status: '已审批' },
    metrics: ['费用申请', '待提交', '已审批', '申请金额']
  },
  '费用审核': {
    key: 'expense-audits', icon: 'el-icon-document-checked', description: '集中审核费用申请，保留费用、部门、门店、日期和流程筛选。',
    actions: ['流程审批'],
    filters: [...expenseFilters, select('status', '状态', ['已提交', '已审批', '已打款', '驳回'])],
    columns: expenseColumns.filter(column => column.key !== 'invoiceType'),
    auditFields: workflowAuditFields,
    defaultFilters: { status: '已提交' },
    metrics: ['审核任务', '已提交', '已审批', '申请金额']
  },
  '付款管理': {
    key: 'payments', icon: 'el-icon-bank-card', description: '按工程名称、审核状态、打款状态和发布时间查询付款。',
    actions: ['导出'],
    filters: [input('projectName', '工程名称'), select('auditStatus', '审核状态', ['审核中', '审核通过', '审核不通过']), select('paymentStatus', '打款状态', ['待打款', '已打款']), dateRange('publishedRange', '发布时间')],
    columns: [
      col('paymentNo', '付款单编号', 150), col('projectName', '工程名称', 160), col('payee', '打款对象', 140),
      col('amount', '单笔打款金额', 120, false, true), col('commissionStandard', '提成标准', 110),
      col('creator', '制单人'), col('paymentStatus', '结算状态', 100, true), col('auditStatus', '审核状态', 100, true),
      col('createdAt', '制单日期', 150)
    ],
    metrics: ['付款单数', '审核中', '待打款', '付款金额']
  }
}

export function getFinancePageConfig(title) {
  return financePageConfigs[title] || financePageConfigs['收款管理']
}
