const stores = ['奇德芬芳·建设路店（中心店）', '奇德芬芳·黄河路店']
const receiptTypes = ['合同首付', '合同补余收款', '合同收款', '其他收款', '押金收款', '诚意金', '会员充值', '续房收款', '服务升级收款', '销售收款', '产康合同收款', '月嫂合同收款']
const createReceiptTypes = ['合同首付', '合同补余收款', '合同收款', '其他收款', '续房收款', '服务升级收款', '销售收款', '产康合同收款', '月嫂合同收款']
const receiptPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '转账汇款', '押金', '会员卡', '优惠券', '积分支付', '赠送', '星pos支付', '订金核销', '信用额度支付', '欠款消费', '客户转卡转账', '积分兑换']
const createPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '押金', '会员卡', '优惠券', '积分支付', '星pos支付']
const refundPaymentMethods = ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '转账汇款', '押金', '会员卡', '优惠券', '积分支付', '星pos支付', '信用额度支付', '客户转卡转账', '积分兑换']
const payoutMethods = ['现金', 'POS机刷卡', '支付宝付款', '微信结算', '转账汇款']
const reconciliationChannels = ['银行转账', 'POS机', '微信支付账单', '支付宝账单', '现金盘点', '其他外部流水']
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
      select('store', '收款分店', stores, true), picker('cashier', '收款人', 'employee', true, '请选择业务员账号'), picker('customerName', '选择客户', 'customer', true, '请选择现有客户'),
      picker('contractNo', '关联合同', 'contract', false, '合同类收款必须选择已审核合同'),
      select('receiptType', '款项类别', createReceiptTypes, true), select('paymentMethod', '结算方式', createPaymentMethods, true),
      number('amount', '单据金额', true), number('giftAmount', '赠送金额'),
      input('recoveryLevel', '产康等级'), select('incomeType', '收入类型', ['销售收款', '抵债收款', '期末调汇', '转账', '退票回冲单', '其他收款']),
      select('bank', '收款银行', banks, true), input('bankAccount', '银行帐号'), select('invoiceStatus', '是否开票', ['未开票']),
      input('coupon', '优惠券'), date('documentDate', '单据日期', true), textarea('remark', '备注'),
      checkbox('sendWechat', '微信推送'), checkbox('sendSms', '短信发送'), upload('attachment', '上传附件')
    ],
    tips: ['单击“合同收款”时自动带入合同余额', '银行类结算方式必须选择收款银行']
  },
  '收款管理': {
    key: 'receipts', icon: 'el-icon-wallet', description: '查询、导出、审核、核销收款；新建收款统一进入“新增收款”，并在此登记真实发票。',
    actions: ['前往新增收款', '星支付', '登记真实发票', '编辑', '删除', '导出', '打印', '审核', '批量审核', '核销', '反审核', '手续费', '扫码支付'],
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
      documentRange: [], settlement: '全部', customerStatus: ['全部'], store: ['全部'],
      hideWriteOff: true, hideMemberCard: false, hideCoupon: true, hideZero: true, hideAdmin: false, hideDischarged: false
    },
    auditFields: [radio('auditResult', '财务审核', ['审核通过', '审核不通过'], true), input('actualAmount', '实收金额', true), number('fee', '手续费'), date('receivedAt', '到账时间'), input('auditRemark', '审核意见')],
    metrics: ['收款单数', '待审核', '实收金额', '可核销余额']
  },
  '退款申请': {
    key: 'refund-applications', icon: 'el-icon-refresh-left', description: '仅发起、编辑和提交退款申请；审批与实际打款统一由退款审核工作台处理。',
    actions: ['添加', '编辑', '删除', '打印', '提交', '导出'],
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
      picker('customerName', '选择客户', 'customer', true, '请选择现有客户'),
      select('store', '退款分店', stores, true),
      select('refundType', '退款类型', refundTypes, true),
      select('refundChannel', '退款渠道', refundChannels, true),
      number('refundAmount', '退款金额', true),
      input('saleNo', '销售编号'),
      textarea('reason', '退款理由', true)
    ],
    auditFields: workflowAuditFields,
    payoutFields: [number('refundAmount', '退款金额'), number('actualRefund', '实退金额', true), select('paymentMethod', '退款方式', refundPaymentMethods, true), date('paidAt', '打款时间', true), input('payee', '收款人', true), select('bank', '银行', banks), input('bankAccount', '银行卡号'), textarea('paymentRemark', '打款说明'), checkbox('sendWechat', '微信'), checkbox('sendSms', '短信')],
    metrics: ['退款申请', '待审核', '待退款', '退款金额'],
    workflow: {
      title: '退款申请闭环',
      description: '申请人录入退款依据并提交；审核人与出纳在审核工作台完成审批和实际打款。',
      stages: [
        { label: '待提交', status: '待提交', action: '编辑' },
        { label: '待审核', status: '待审核' },
        { label: '待退款', status: '待退款' },
        { label: '已退款', status: '已退款' }
      ]
    }
  },
  '退款审核': {
    key: 'refund-audits', icon: 'el-icon-s-check', description: '集中审核待处理退款；审批通过后在本工作台登记真实打款，保留审核轨迹。',
    actions: ['流程审批', '登记退款打款', '反审核', '撤回'],
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
    metrics: ['审核任务', '待审核', '审核通过', '待打款'],
    workflow: {
      title: '退款审批与出纳打款',
      description: '只处理已提交退款：审批通过后才可登记真实打款，不接入或模拟外部退款渠道。',
      stages: [
        { label: '待审核', status: '待审核', action: '流程审批' },
        { label: '待退款', status: '待退款', action: '登记退款打款' },
        { label: '已退款', status: '已退款' }
      ]
    }
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
    key: 'invoices', icon: 'el-icon-tickets', description: '发票档案管理：查询、导出、纠正已登记的真实收付款发票；不调用税务平台。',
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
    metrics: ['发票数量', '发票金额', '税额', '待开票'],
    workflow: {
      title: '真实发票档案',
      description: '发票只能由已审核收款登记；本页用于核验票号、税额和归档，不触发税控平台开票。',
      stages: [
        { label: '已登记', status: '已登记' },
        { label: '已开票', status: '已开票' },
        { label: '已作废', status: '已作废' }
      ]
    }
  },
  '交易对账': {
    key: 'reconciliations',
    icon: 'el-icon-s-check',
    description: '手工登记银行、POS、微信或支付宝账单中的真实外部流水，并与已审核收款逐笔核对；当前未直连任何外部支付通道。',
    actions: ['添加', '确认匹配', '取消匹配', '删除', '导出'],
    workflow: {
      title: '人工交易对账闭环',
      description: '登记真实银行、POS、微信或支付宝外部流水；金额无差异后才能确认匹配。',
      stages: [
        { label: '待匹配', status: '待匹配', action: '确认匹配' },
        { label: '差异待处理', status: '差异待处理' },
        { label: '已匹配', status: '已匹配', action: '取消匹配' }
      ]
    },
    filters: [
      input('receiptNo', '系统收款单号'),
      input('externalReference', '外部流水号'),
      select('externalChannel', '外部渠道', reconciliationChannels),
      select('status', '对账状态', ['待匹配', '差异待处理', '已匹配']),
      select('store', '门店', stores),
      dateRange('transactionRange', '外部交易日期')
    ],
    columns: [
      col('receiptNo', '系统收款单号', 155),
      col('externalChannel', '外部渠道', 125),
      col('externalReference', '外部流水号', 170),
      col('systemAmount', '系统实收金额', 120, false, true),
      col('externalAmount', '外部到账金额', 120, false, true),
      col('differenceAmount', '差异金额', 105, false, true),
      col('transactionDate', '外部交易日期', 120),
      col('status', '对账状态', 105, true),
      col('store', '门店', 150),
      col('creator', '登记人'),
      col('matchedBy', '匹配人'),
      col('matchedAt', '匹配时间', 150),
      col('remark', '备注', 180)
    ],
    formFields: [
      input('receiptNo', '系统收款单号', true),
      select('store', '门店', stores, true),
      select('externalChannel', '外部渠道', reconciliationChannels, true),
      input('externalReference', '外部流水号', true),
      number('externalAmount', '外部到账金额', true),
      date('transactionDate', '外部交易日期', true),
      textarea('remark', '备注')
    ],
    metrics: ['对账流水', '待处理', '已匹配', '差异金额']
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
    key: 'my-expenses', icon: 'el-icon-money', description: '申请人工作台：创建、编辑、提交并查询本人费用；审批与付款分别在对应工作台完成。',
    actions: ['添加', '编辑', '删除', '导出', '打印', '打款', '反审核', '提交'],
    filters: [...expenseFilters, select('status', '状态', ['待提交', '已提交', '已审批', '已打款', '驳回'])],
    columns: expenseColumns,
    formFields: [input('expenseName', '费用名称', true), select('feeType', '费用类型', feeTypes, true), input('applicant', '申请人', true), input('department', '申请部门', true), select('store', '费用分店', stores, true), textarea('reason', '申请事由', true), number('applyAmount', '申请金额', true), input('attachment', '附件')],
    auditFields: workflowAuditFields,
    payoutFields: [number('amount', '打款金额', true), select('payoutType', '打款类型', payoutMethods, true), date('paidAt', '支付时间', true), textarea('paymentRemark', '打款说明'), input('attachment', '附件')],
    defaultFilters: { status: '已审批' },
    metrics: ['费用申请', '待提交', '已审批', '申请金额'],
    workflow: {
      title: '本人费用申请',
      description: '申请人只能维护本人费用单；提交后转入费用审核，审批通过后才进入付款。',
      stages: [
        { label: '待提交', status: '待提交', action: '提交' },
        { label: '已提交', status: '已提交' },
        { label: '已审批', status: '已审批', action: '打款' },
        { label: '已打款', status: '已打款' }
      ]
    }
  },
  '费用审核': {
    key: 'expense-audits', icon: 'el-icon-document-checked', description: '审核人工作台：集中审核费用申请，保留费用、部门、门店、日期和流程筛选。',
    actions: ['流程审批'],
    filters: [...expenseFilters, select('status', '状态', ['已提交', '已审批', '已打款', '驳回'])],
    columns: expenseColumns.filter(column => column.key !== 'invoiceType'),
    auditFields: workflowAuditFields,
    defaultFilters: { status: '已提交' },
    metrics: ['审核任务', '已提交', '已审批', '申请金额'],
    workflow: {
      title: '费用审批工作台',
      description: '审核人集中处理已提交费用；审批决定写入流程记录，申请人不能在本页篡改申请。',
      stages: [
        { label: '已提交', status: '已提交', action: '流程审批' },
        { label: '已审批', status: '已审批' },
        { label: '驳回', status: '驳回' }
      ]
    }
  },
  '付款管理': {
    key: 'payments', icon: 'el-icon-bank-card', description: '付款流水管理：查询已审批费用产生的真实付款记录，不重复发起费用审批。',
    actions: ['导出'],
    filters: [input('projectName', '工程名称'), select('auditStatus', '审核状态', ['审核中', '审核通过', '审核不通过']), select('paymentStatus', '打款状态', ['待打款', '已打款']), dateRange('publishedRange', '发布时间')],
    columns: [
      col('paymentNo', '付款单编号', 150), col('projectName', '工程名称', 160), col('payee', '打款对象', 140),
      col('amount', '单笔打款金额', 120, false, true), col('commissionStandard', '提成标准', 110),
      col('creator', '制单人'), col('paymentStatus', '结算状态', 100, true), col('auditStatus', '审核状态', 100, true),
      col('createdAt', '制单日期', 150)
    ],
    metrics: ['付款单数', '审核中', '待打款', '付款金额'],
    workflow: {
      title: '付款流水复核',
      description: '只展示审批通过后产生的付款流水，用于资金复核、导出和审计追溯，不重复发起费用审批。',
      stages: [
        { label: '待打款', status: '待打款' },
        { label: '已打款', status: '已打款' }
      ]
    }
  }
}

// The 104-item feature registry uses product-facing names while the original
// ERP uses operation-facing page names.  Keep that translation here instead
// of silently falling back to 收款管理: a fallback made several finance menus
// look like the same page and, more importantly, exposed the wrong actions.
const financeFeatureAliases = {
  '收银开单与订单': {
    source: '新增收款',
    permissionTitle: '新增收款',
    description: '收银开单入口：先选择具体门店，再选择客户与已审核合同，录入收款方式、金额和附件；支付通道未启用时保留待处理记录。',
    metrics: ['本次开单', '必填字段', '关联合同', '开单金额']
  },
  '财务收支': {
    source: '收款管理',
    permissionTitle: '收款管理',
    presentation: 'ledger',
    description: '财务收支台账：查询、审核、核销和导出各门店真实收款记录；新开单统一从“收银开单与订单”进入。',
    actions: ['前往新增收款', '审核', '批量审核', '核销', '导出'],
    metrics: ['收支流水', '待审核收款', '实收金额', '可核销余额']
  },
  '退款与报销': {
    source: '退款申请',
    permissionTitle: '退款申请',
    presentation: 'approval',
    description: '退款申请台账：发起、编辑、提交退款并保留审核轨迹。费用报销仍通过“我的费用/费用审核”闭环，不把两类单据混写为同一笔记录。',
    metrics: ['退款申请', '待审核', '待退款', '退款金额']
  },
  '收支分析': {
    source: '收款管理',
    permissionTitle: '收款管理',
    presentation: 'analysis',
    description: '收支分析基于已保存的收款台账按门店、款项类别、收款方式和日期筛选汇总；本页只读分析与导出，不产生新的收款。',
    actions: ['导出'],
    metrics: ['收款流水数', '待审核单', '实收金额', '收款方式']
  },
  '成本核算': {
    source: '部门物料预算',
    permissionTitle: '部门物料预算',
    presentation: 'analysis',
    description: '成本核算当前以部门物料预算、采购计划和审批记录为核算底稿；实际结算成本以已接入的采购/入库数据为准，不伪造成本结算结果。',
    actions: ['添加', '编辑', '流程审批', '提交', '生成采购计划', '导出'],
    metrics: ['核算底稿', '待提交', '审核中', '预算总额']
  },
  '充值报表': {
    source: '收款管理',
    permissionTitle: '收款管理',
    presentation: 'analysis',
    description: '充值报表从会员充值类已保存收款记录汇总生成；仅展示和导出，不在报表页直接修改会员资产。',
    actions: ['导出'],
    defaultFilters: { receiptType: '会员充值' },
    metrics: ['充值流水', '待审核充值', '充值实收', '可核销余额']
  },
  '厂商并行期对账帮手': {
    source: '交易对账',
    permissionTitle: '交易对账',
    presentation: 'ledger',
    description: '并行期对账：人工登记厂商或旧系统导出的真实外部流水，与本系统已审核收款逐笔匹配；未接入渠道时不会返回虚假对账成功。',
    actions: ['添加', '确认匹配', '取消匹配', '导出'],
    metrics: ['对账流水', '待处理', '已匹配', '差异金额']
  },
  '在线支付（微信/支付宝）': { source: '在线支付' }
}

const financeStandaloneFeatureConfigs = {
  在线支付: {
    featureId: 'F083',
    title: '在线支付',
    key: 'online-payment-integration',
    permissionTitle: '在线支付',
    presentation: 'integration',
    integrationOnly: true,
    description: '在线支付工作台：微信、支付宝通道未启用时保留待处理、待执行、失败和重试记录，不复用普通收款台账，也不显示为支付成功。',
    actions: ['导出接入记录'],
    filters: [select('channel', '支付渠道', ['微信支付', '支付宝']), select('integrationStatus', '处理状态', ['待处理', '待执行', '执行失败', '已完成'])],
    columns: [
      col('requestNo', '支付申请号', 150), col('channel', '支付渠道', 110), col('store', '发生门店', 150),
      col('amount', '申请金额', 110, false, true), col('integrationStatus', '接入状态', 105, true),
      col('failureReason', '失败原因', 180), col('updatedAt', '更新时间', 150)
    ],
    metrics: ['接入申请', '待执行支付', '执行失败', '已完成']
  },
  '储值卡/折扣卡/微信卡包': {
    featureId: 'F089',
    title: '储值卡/折扣卡/微信卡包',
    key: 'member-card-wallets',
    permissionTitle: '会员资产',
    presentation: 'integration',
    integrationOnly: true,
    description: '展示会员储值卡、折扣卡与微信卡包的同步状态；会员资产跨店共享，但每笔充值、消费和同步记录必须保留发生门店。',
    actions: ['导出'],
    filters: [],
    columns: [],
    metrics: ['卡账户', '待同步', '同步失败', '即将到期']
  }
}

export function getFinancePageConfig(title) {
  if (financeStandaloneFeatureConfigs[title]) return financeStandaloneFeatureConfigs[title]
  const alias = financeFeatureAliases[title]
  const sourceTitle = alias ? alias.source : title
  if (financeStandaloneFeatureConfigs[sourceTitle]) {
    return { ...financeStandaloneFeatureConfigs[sourceTitle], ...alias }
  }
  const sourceConfig = financePageConfigs[sourceTitle] || financePageConfigs['收款管理']
  return alias ? { ...sourceConfig, ...alias } : sourceConfig
}

export function getFinanceFeatureAlias(title) {
  return financeFeatureAliases[title] || null
}
