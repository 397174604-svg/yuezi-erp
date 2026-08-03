import { applyOriginalEvidence } from './original-page-evidence'

const storeOptions = ['奇德芬芳·建设路店（中心店）', '奇德芬芳·黄河路店']

const field = (key, label, type = 'input', options = []) => ({
  key,
  label,
  type,
  options: [...options],
  verified: false
})
const input = (key, label) => field(key, label)
const select = (key, label, options) => field(key, label, 'select', options)
const dateRange = (key, label) => field(key, label, 'dateRange')
const store = (label = '门店') => select('store', label, storeOptions)
const column = (key, label, format = 'text', width = 120) => ({
  key,
  label,
  format,
  width,
  verified: false
})
const text = (key, label, width) => column(key, label, 'text', width)
const money = (key, label, width) => column(key, label, 'money', width)
const count = (key, label, width) => column(key, label, 'count', width)
const percent = (key, label, width) => column(key, label, 'percent', width)

const defineReport = (title, key, family, description, filters, columns) => ({
  title,
  key,
  family,
  mode: 'report-table',
  description,
  filters,
  columns,
  queryActions: ['查询'],
  businessActions: [],
  originalUrl: '',
  evidenceLevel: '待原系统二次核验',
  completionLevel: 'Visible',
  formulaStatus: '待原系统二次核验',
  exportStatus: '待原系统二次核验',
  printStatus: '待原系统二次核验',
  evidenceNote: '报表菜单已完成确认；筛选项、汇总口径、公式、导出和打印规则仍需业务确认。'
})

const reportDefinitions = [
  defineReport(
    'S1 销售排行榜报表',
    's1-sales-ranking',
    '销售',
    '销售人员业绩排行结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('department', '部门'), input('salesperson', '销售人员')],
    [count('rank', '排名', 80), text('salesperson', '销售人员'), text('department', '部门'), count('contractCount', '合同数量'), money('contractAmount', '合同金额'), money('receivedAmount', '收款金额')]
  ),
  defineReport(
    'S2客户简报',
    's2-customer-brief',
    '销售',
    '客户新增、到访、签约与入住概览结构草案。',
    [dateRange('statRange', '统计日期'), store(), select('customerStatus', '客户状态', ['待原系统核验']), input('salesperson', '销售人员')],
    [text('statDate', '统计日期'), text('store', '门店', 150), count('newCustomerCount', '新增客户数'), count('visitCount', '到访数'), count('signedCount', '签约数'), count('checkInCount', '入住数'), percent('conversionRate', '转化率')]
  ),
  defineReport(
    'S3 畅销排行榜报表',
    's3-best-selling-ranking',
    '销售',
    '商品、项目或套餐畅销排行结构草案。',
    [dateRange('statRange', '统计日期'), store(), select('saleType', '销售类型', ['待原系统核验']), input('itemName', '商品/项目名称')],
    [count('rank', '排名', 80), text('saleType', '销售类型'), text('itemName', '商品/项目名称', 180), count('saleQuantity', '销售数量'), money('saleAmount', '销售金额'), money('receivedAmount', '实收金额')]
  ),
  defineReport(
    'S4 (DM)客户合同汇总报表',
    's4-dm-customer-contract-summary',
    '销售',
    'DM 客户合同汇总结构草案。',
    [dateRange('contractRange', '合同日期'), store(), input('customerName', '客户姓名'), input('contractNo', '合同编号'), input('salesperson', '销售人员')],
    [text('contractNo', '合同编号', 150), text('customerName', '客户姓名'), text('store', '合同门店', 150), text('salesperson', '销售人员'), text('contractDate', '合同日期'), money('referenceAmount', '参考金额'), money('dealAmount', '成交金额'), money('receivedAmount', '已收金额')]
  ),
  defineReport(
    'S5商品消费汇总明细表',
    's5-product-consumption-summary',
    '销售',
    '商品消费数量与金额汇总明细结构草案。',
    [dateRange('consumeRange', '消费日期'), store(), input('customerName', '客户姓名'), input('productName', '商品名称'), input('documentNo', '单据编号')],
    [text('documentNo', '单据编号', 150), text('consumeDate', '消费日期'), text('customerName', '客户姓名'), text('productName', '商品名称', 180), text('specification', '规格'), count('quantity', '消费数量'), money('unitPrice', '单价'), money('amount', '消费金额')]
  ),
  defineReport(
    'S6销售统计报表',
    's6-sales-statistics',
    '销售',
    '按门店、人员与销售类型统计销售结果结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('salesperson', '销售人员'), select('saleType', '销售类型', ['待原系统核验'])],
    [text('statPeriod', '统计期间'), text('store', '门店', 150), text('salesperson', '销售人员'), text('saleType', '销售类型'), count('documentCount', '单据数'), money('saleAmount', '销售金额'), money('discountAmount', '优惠金额'), money('dealAmount', '成交金额')]
  ),
  defineReport(
    'S7服务销售汇总明细表',
    's7-service-sales-summary',
    '销售',
    '服务项目销售汇总明细结构草案。',
    [dateRange('saleRange', '销售日期'), store(), input('customerName', '客户姓名'), input('serviceName', '服务项目'), input('salesperson', '销售人员')],
    [text('saleDate', '销售日期'), text('customerName', '客户姓名'), text('serviceName', '服务项目', 180), count('quantity', '销售次数'), money('referenceAmount', '参考金额'), money('dealAmount', '成交金额'), text('salesperson', '销售人员'), text('store', '门店', 150)]
  ),
  defineReport(
    'S8 卡类销售汇总明细表',
    's8-card-sales-summary',
    '销售',
    '卡类套餐销售汇总明细结构草案。',
    [dateRange('saleRange', '销售日期'), store(), input('customerName', '客户姓名'), input('cardName', '卡类名称'), input('salesperson', '销售人员')],
    [text('saleDate', '销售日期'), text('customerName', '客户姓名'), text('cardName', '卡类名称', 180), count('quantity', '销售数量'), money('cardAmount', '卡面金额'), money('dealAmount', '成交金额'), text('salesperson', '销售人员'), text('store', '门店', 150)]
  ),
  defineReport(
    'S9跨店消费报表',
    's9-cross-store-consumption',
    '销售',
    '客户跨门店消费与结算归属结构草案。',
    [dateRange('consumeRange', '消费日期'), store('消费门店'), input('sourceStore', '客户所属门店'), input('customerName', '客户姓名'), select('consumeType', '消费类型', ['待原系统核验'])],
    [text('consumeDate', '消费日期'), text('customerName', '客户姓名'), text('sourceStore', '客户所属门店', 150), text('store', '消费门店', 150), text('consumeType', '消费类型'), text('itemName', '消费项目', 180), money('amount', '消费金额'), text('settlementStatus', '结算状态')]
  ),
  defineReport(
    'S10SML销售日报表',
    's10-sml-daily-sales',
    '销售',
    'SML 销售日报结构草案。',
    [dateRange('saleRange', '销售日期'), store(), input('salesperson', '销售人员'), select('saleType', '销售类型', ['待原系统核验'])],
    [text('saleDate', '销售日期'), text('store', '门店', 150), text('salesperson', '销售人员'), count('customerCount', '客户数'), count('documentCount', '单据数'), money('saleAmount', '销售金额'), money('receivedAmount', '收款金额'), money('refundAmount', '退款金额')]
  ),
  defineReport(
    'S11赠送物品明细表',
    's11-gift-item-details',
    '销售',
    '赠送物品申请、发放与价值明细结构草案。',
    [dateRange('giftRange', '赠送日期'), store(), input('customerName', '客户姓名'), input('itemName', '赠送物品'), input('operator', '经办人')],
    [text('giftDate', '赠送日期'), text('customerName', '客户姓名'), text('itemName', '赠送物品', 180), text('specification', '规格'), count('quantity', '赠送数量'), money('referenceAmount', '参考金额'), text('operator', '经办人'), text('auditStatus', '审核状态')]
  ),
  defineReport(
    'S12客户跨店服务消费表',
    's12-customer-cross-store-service-consumption',
    '销售',
    '跨门店服务项目消费记录结构草案。',
    [dateRange('serviceRange', '服务日期'), store('服务门店'), input('sourceStore', '客户所属门店'), input('customerName', '客户姓名'), input('serviceName', '服务项目')],
    [text('serviceDate', '服务日期'), text('customerName', '客户姓名'), text('sourceStore', '客户所属门店', 150), text('store', '服务门店', 150), text('serviceName', '服务项目', 180), count('consumeCount', '消费次数'), money('consumeAmount', '消费金额'), text('serviceStaff', '服务人员')]
  ),
  defineReport(
    'S13销售业绩报表',
    's13-sales-performance',
    '销售',
    '销售人员合同、商品、服务及回款业绩结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('department', '部门'), input('salesperson', '销售人员')],
    [text('salesperson', '销售人员'), text('department', '部门'), count('contractCount', '合同数'), money('contractAmount', '合同业绩'), money('productAmount', '商品业绩'), money('serviceAmount', '服务业绩'), money('receivedAmount', '回款业绩'), money('totalAmount', '业绩合计')]
  ),
  defineReport(
    'F1 月度入住率报表',
    'f1-monthly-occupancy',
    '房务',
    '月度入住率结构草案。',
    [dateRange('statRange', '统计月份'), store(), input('roomType', '房型')],
    [text('statMonth', '统计月份'), text('store', '门店', 150), text('roomType', '房型'), count('availableRoomDays', '可售间夜'), count('occupiedRoomDays', '入住房晚'), count('reservedRoomDays', '预订房晚'), percent('occupancyRate', '入住率')]
  ),
  defineReport(
    'F2 房态统计总体分析',
    'f2-room-status-overall-analysis',
    '房务',
    '房态数量与占比总体分析结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('roomType', '房型'), select('roomStatus', '房态', ['待原系统核验'])],
    [text('statDate', '统计日期'), text('store', '门店', 150), text('roomType', '房型'), count('roomCount', '房间数'), count('occupiedCount', '入住数'), count('reservedCount', '预订数'), count('vacantCount', '空房数'), percent('occupancyRate', '入住率')]
  ),
  defineReport(
    'F3月度预定明细报表',
    'f3-monthly-reservation-details',
    '房务',
    '月度客户订房与预住明细结构草案。',
    [dateRange('reserveRange', '预住日期'), store(), input('customerName', '客户姓名'), input('roomNo', '房间号'), select('reserveStatus', '预订状态', ['待原系统核验'])],
    [text('customerName', '客户姓名'), text('store', '门店', 150), text('roomNo', '房间号'), text('roomType', '房型'), text('plannedCheckInDate', '预住日期'), text('plannedCheckOutDate', '预计退房日期'), count('plannedDays', '预住天数'), text('reserveStatus', '预订状态')]
  ),
  defineReport(
    'F4月度出中心明细报表',
    'f4-monthly-checkout-details',
    '房务',
    '月度退房、出中心与结账明细结构草案。',
    [dateRange('checkoutRange', '出中心日期'), store(), input('customerName', '客户姓名'), input('roomNo', '房间号'), select('settlementStatus', '结账状态', ['待原系统核验'])],
    [text('customerName', '客户姓名'), text('store', '门店', 150), text('roomNo', '房间号'), text('checkInDate', '入住日期'), text('checkoutDate', '出中心日期'), count('stayDays', '入住天数'), text('settlementStatus', '结账状态'), money('unsettledAmount', '未结金额')]
  ),
  defineReport(
    'F5预住客户采购报表',
    'f5-prestay-customer-purchase',
    '房务',
    '预住客户物品或物料采购需求结构草案。',
    [dateRange('plannedCheckInRange', '预住日期'), store(), input('customerName', '客户姓名'), input('itemName', '采购物品'), select('purchaseStatus', '采购状态', ['待原系统核验'])],
    [text('customerName', '客户姓名'), text('plannedCheckInDate', '预住日期'), text('store', '门店', 150), text('roomNo', '房间号'), text('itemName', '采购物品', 180), count('quantity', '采购数量'), text('purchaseStatus', '采购状态'), text('remark', '备注', 180)]
  ),
  defineReport(
    'F6入住率',
    'f6-occupancy-rate',
    '房务',
    '入住率按日期与门店查询结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('roomType', '房型')],
    [text('statDate', '统计日期'), text('store', '门店', 150), count('totalRoomCount', '总房间数'), count('occupiedRoomCount', '入住房间数'), count('vacantRoomCount', '空房数'), percent('occupancyRate', '入住率')]
  ),
  defineReport(
    'C0经营日报表',
    'c0-daily-operation',
    '财务',
    '门店每日收入、成本、合同与入住经营概览结构草案。',
    [dateRange('statRange', '统计日期'), store()],
    [text('statDate', '统计日期'), text('store', '门店', 150), money('contractAmount', '合同金额'), money('receivedAmount', '收款金额'), money('refundAmount', '退款金额'), money('paymentAmount', '付款金额'), money('incomeAmount', '收入金额'), money('costAmount', '成本金额')]
  ),
  defineReport(
    'C0经营月报',
    'c0-monthly-operation',
    '财务',
    '按已入账收款流水汇总的经营月报；退款、付款和成本待对应业务流水接入后才显示真实值。',
    [input('statMonth', '统计月份（YYYY-MM）'), store()],
    [text('statMonth', '统计月份', 110), text('store', '门店', 150), count('documentCount', '收款单数'), money('receivedAmount', '收款金额'), money('incomeAmount', '收入金额'), money('refundAmount', '退款金额'), money('paymentAmount', '付款金额'), money('costAmount', '成本金额'), money('netAmount', '净收入')]
  ),
  defineReport(
    'C1 会员充值汇总明细表',
    'c1-member-recharge-summary',
    '财务',
    '按门店查询已审核会员充值与预收款，展示充值、赠送金额和经办人。',
    [dateRange('rechargeRange', '充值日期'), store(), input('customerName', '客户姓名'), input('cardNo', '会员卡号'), select('paymentMethod', '支付方式', ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '转账汇款'])],
    [text('rechargeDate', '充值日期'), text('customerName', '客户姓名'), text('cardNo', '会员卡号', 150), text('store', '门店', 150), money('rechargeAmount', '充值金额'), money('giftAmount', '赠送金额'), text('paymentMethod', '支付方式'), text('operator', '经办人')]
  ),
  defineReport(
    'C2 收款结算类型汇总表',
    'c2-receipt-settlement-type-summary',
    '财务',
    '按收款与结算类型汇总金额结构草案。',
    [dateRange('receiptRange', '收款日期'), store(), select('receiptType', '收款类型', ['待原系统核验']), select('settlementType', '结算类型', ['待原系统核验'])],
    [text('receiptType', '收款类型'), text('settlementType', '结算类型'), text('store', '门店', 150), count('documentCount', '单据数'), money('receiptAmount', '收款金额'), money('feeAmount', '手续费'), money('netAmount', '净额')]
  ),
  defineReport(
    'C3 付款汇总分析表',
    'c3-payment-summary-analysis',
    '财务',
    '按已打款费用单汇总付款用途、收款方与资金账户。',
    [dateRange('paymentRange', '付款日期'), store(), input('payee', '收款方'), input('paymentType', '付款类型'), input('fundAccount', '资金账户')],
    [text('paymentType', '付款类型'), text('payee', '收款方', 180), text('store', '门店', 150), text('fundAccount', '资金账户', 150), count('documentCount', '单据数'), money('paymentAmount', '付款金额'), money('auditedAmount', '审核金额')]
  ),
  defineReport(
    'C4 资金收支出余额表',
    'c4-fund-income-expense-balance',
    '财务',
    '按已审核收款、已退款和已打款费用计算资金账户逐日收支与余额。',
    [dateRange('statRange', '统计日期'), store(), input('fundAccount', '资金账户')],
    [text('statDate', '统计日期'), text('fundAccount', '资金账户', 150), text('store', '门店', 150), money('openingBalance', '期初余额'), money('incomeAmount', '收入金额'), money('expenseAmount', '支出金额'), money('closingBalance', '期末余额')]
  ),
  defineReport(
    'C5 月间天统计分析',
    'c5-month-day-statistical-analysis',
    '财务',
    '月内每日经营金额统计分析结构草案。',
    [dateRange('statRange', '统计月份'), store(), select('indicator', '统计指标', ['待原系统核验'])],
    [text('statDate', '日期'), text('store', '门店', 150), money('receiptAmount', '收款金额'), money('refundAmount', '退款金额'), money('paymentAmount', '付款金额'), money('netAmount', '净额'), percent('monthShare', '月度占比')]
  ),
  defineReport(
    'C6 客户收款跟踪明细表',
    'c6-customer-receipt-tracking',
    '财务',
    '客户合同、应收、已收与欠款跟踪结构草案。',
    [dateRange('contractRange', '合同日期'), store(), input('customerName', '客户姓名'), input('contractNo', '合同编号'), input('salesperson', '销售人员')],
    [text('customerName', '客户姓名'), text('contractNo', '合同编号', 150), text('store', '门店', 150), money('contractAmount', '合同金额'), money('receivableAmount', '应收金额'), money('receivedAmount', '已收金额'), money('outstandingAmount', '欠款金额'), text('lastReceiptDate', '最近收款日期')]
  ),
  defineReport(
    'C7 门店收入与成本统计表',
    'c7-store-income-cost-statistics',
    '财务',
    '按月汇总门店已审核净收入、已打款费用成本与经营毛利。',
    [dateRange('statRange', '统计日期'), store()],
    [text('statPeriod', '统计期间'), text('store', '门店', 150), money('incomeAmount', '收入金额'), money('costAmount', '成本金额'), money('grossProfit', '毛利'), percent('grossMargin', '毛利率')]
  ),
  defineReport(
    'C8 商品毛利分析表',
    'c8-product-gross-profit-analysis',
    '财务',
    '按真实销售明细和品项成本价计算商品销售收入、成本与毛利。',
    [dateRange('saleRange', '销售日期'), store(), input('productName', '商品名称'), input('productCategory', '商品类别')],
    [text('productCode', '商品编码', 130), text('productName', '商品名称', 180), text('productCategory', '商品类别'), count('saleQuantity', '销售数量'), money('saleAmount', '销售金额'), money('costAmount', '成本金额'), money('grossProfit', '毛利'), percent('grossMargin', '毛利率')]
  ),
  defineReport(
    'C9 推荐人报表',
    'c9-referrer-report',
    '财务',
    '推荐人带客、签约与返利结果结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('referrer', '推荐人'), select('referrerType', '推荐人类型', ['待原系统核验'])],
    [text('referrer', '推荐人'), text('referrerType', '推荐人类型'), count('customerCount', '推荐客户数'), count('signedCount', '签约客户数'), money('contractAmount', '合同金额'), money('rebateAmount', '返利金额'), text('store', '门店', 150)]
  ),
  defineReport(
    'C12 返现消费查询',
    'c12-cashback-consumption-query',
    '财务',
    '返现额度产生与消费明细结构草案。',
    [dateRange('consumeRange', '消费日期'), store(), input('customerName', '客户姓名'), input('documentNo', '单据编号'), select('consumeType', '消费类型', ['待原系统核验'])],
    [text('documentNo', '单据编号', 150), text('consumeDate', '消费日期'), text('customerName', '客户姓名'), text('consumeType', '消费类型'), money('beforeBalance', '消费前余额'), money('consumeAmount', '消费金额'), money('afterBalance', '消费后余额'), text('operator', '经办人')]
  ),
  defineReport(
    'C10 收款款项汇总明细表',
    'c10-receipt-item-summary',
    '财务',
    '按收款款项、客户与单据汇总收款结构草案。',
    [dateRange('receiptRange', '收款日期'), store(), input('customerName', '客户姓名'), input('receiptItem', '收款款项'), input('documentNo', '单据编号')],
    [text('receiptDate', '收款日期'), text('documentNo', '单据编号', 150), text('customerName', '客户姓名'), text('receiptItem', '收款款项', 160), text('settlementType', '结算类型'), money('receiptAmount', '收款金额'), text('store', '门店', 150), text('receiver', '收款人')]
  ),
  defineReport(
    'C11 项目消费收入报表',
    'c11-service-consumption-income',
    '财务',
    '项目消费次数与确认收入结构草案。',
    [dateRange('consumeRange', '消费日期'), store(), input('customerName', '客户姓名'), input('serviceName', '服务项目'), input('serviceStaff', '服务人员')],
    [text('consumeDate', '消费日期'), text('customerName', '客户姓名'), text('serviceName', '服务项目', 180), count('consumeCount', '消费次数'), money('unitIncome', '单次收入'), money('incomeAmount', '项目收入'), text('serviceStaff', '服务人员'), text('store', '门店', 150)]
  ),
  defineReport(
    'C13收款退款汇总表',
    'c13-receipt-refund-summary',
    '财务',
    '按日和门店汇总已审核收款、已完成退款与净收款。',
    [dateRange('statRange', '统计日期'), store()],
    [text('statPeriod', '统计期间'), text('store', '门店', 150), count('receiptCount', '收款笔数'), money('receiptAmount', '收款金额'), count('refundCount', '退款笔数'), money('refundAmount', '退款金额'), money('netReceiptAmount', '净收款金额')]
  ),
  defineReport(
    'C14合同业绩报表',
    'c14-contract-performance',
    '财务',
    '合同金额按门店、部门与人员归属结构草案。',
    [dateRange('contractRange', '合同日期'), store(), input('department', '部门'), input('salesperson', '销售人员'), select('contractStatus', '合同状态', ['待原系统核验'])],
    [text('contractNo', '合同编号', 150), text('contractDate', '合同日期'), text('customerName', '客户姓名'), text('store', '门店', 150), text('salesperson', '销售人员'), money('contractAmount', '合同金额'), money('performanceAmount', '业绩金额'), text('contractStatus', '合同状态')]
  ),
  defineReport(
    'C15资金账户收支明细表',
    'c15-fund-account-transactions',
    '财务',
    '资金账户逐笔收支明细结构草案。',
    [dateRange('transactionRange', '发生日期'), store(), input('fundAccount', '资金账户'), select('direction', '收支方向', ['待原系统核验']), input('documentNo', '单据编号')],
    [text('transactionDate', '发生日期'), text('documentNo', '单据编号', 150), text('fundAccount', '资金账户', 150), text('direction', '收支方向'), text('businessType', '业务类型'), money('incomeAmount', '收入金额'), money('expenseAmount', '支出金额'), money('balance', '账户余额'), text('operator', '经办人')]
  ),
  defineReport(
    'C16收款及结算类型报表',
    'c16-receipt-and-settlement-types',
    '财务',
    '收款类型与结算类型交叉统计结构草案。',
    [dateRange('receiptRange', '收款日期'), store(), select('receiptType', '收款类型', ['待原系统核验']), select('settlementType', '结算类型', ['待原系统核验'])],
    [text('receiptType', '收款类型'), text('settlementType', '结算类型'), text('store', '门店', 150), count('documentCount', '单据数'), money('receiptAmount', '收款金额'), money('refundAmount', '退款金额'), money('netAmount', '净额')]
  ),
  defineReport(
    'H1 客户服务记录报表',
    'h1-customer-service-records',
    '护理',
    '客户护理、产康或客房服务执行记录结构草案。',
    [dateRange('serviceRange', '服务日期'), store(), input('customerName', '客户姓名'), input('serviceName', '服务项目'), input('serviceStaff', '服务人员')],
    [text('serviceDate', '服务日期'), text('customerName', '客户姓名'), text('roomNo', '房间号'), text('serviceName', '服务项目', 180), text('serviceStaff', '服务人员'), text('serviceStatus', '服务状态'), text('serviceResult', '服务结果', 200), text('store', '门店', 150)]
  ),
  defineReport(
    'H2 宝宝体征统计表',
    'h2-baby-vital-sign-statistics',
    '护理',
    '宝宝体温、体重等体征记录统计结构草案。',
    [dateRange('recordRange', '记录日期'), store(), input('customerName', '妈妈姓名'), input('babyName', '宝宝姓名'), input('roomNo', '房间号')],
    [text('recordDate', '记录日期'), text('babyName', '宝宝姓名'), text('customerName', '妈妈姓名'), text('roomNo', '房间号'), text('temperature', '体温'), text('weight', '体重'), text('otherSigns', '其他体征', 180), text('recorder', '记录人')]
  ),
  defineReport(
    'H3 妈妈的体温与体重变化表',
    'h3-mother-temperature-weight-trend',
    '护理',
    '妈妈体温与体重变化趋势结构草案。',
    [dateRange('recordRange', '记录日期'), store(), input('customerName', '客户姓名'), input('roomNo', '房间号')],
    [text('recordDate', '记录日期'), text('customerName', '客户姓名'), text('roomNo', '房间号'), text('temperature', '体温'), text('weight', '体重'), text('changeValue', '变化值'), text('recorder', '记录人'), text('remark', '备注', 180)]
  ),
  defineReport(
    'H4 产康项目工作汇总表',
    'h4-rehab-service-work-summary',
    '护理',
    '产康项目预约、完成、耗卡与人员工作量汇总结构草案。',
    [dateRange('serviceRange', '服务日期'), store(), input('serviceName', '产康项目'), input('technician', '技师')],
    [text('serviceName', '产康项目', 180), text('technician', '技师'), count('appointmentCount', '预约次数'), count('completedCount', '完成次数'), count('consumedCount', '耗卡次数'), count('customerCount', '服务客户数'), money('incomeAmount', '项目收入'), text('store', '门店', 150)]
  ),
  defineReport(
    '企业微信客服报表',
    'wechat-customer-service-report',
    '其他',
    '企业微信客服接待与跟进统计结构草案。',
    [dateRange('statRange', '统计日期'), store(), input('serviceStaff', '客服人员'), select('conversationStatus', '会话状态', ['待原系统核验'])],
    [text('statDate', '统计日期'), text('serviceStaff', '客服人员'), count('conversationCount', '会话数'), count('customerCount', '客户数'), count('replyCount', '回复数'), text('averageResponseTime', '平均响应时长'), percent('effectiveRate', '有效沟通率'), text('store', '门店', 150)]
  ),
  defineReport(
    '妈妈端分享报表',
    'mother-app-sharing-report',
    '其他',
    '妈妈端内容分享与访问转化结构草案。',
    [dateRange('shareRange', '分享日期'), store(), input('customerName', '客户姓名'), select('contentType', '内容类型', ['待原系统核验'])],
    [text('shareDate', '分享日期'), text('customerName', '客户姓名'), text('contentType', '内容类型'), text('contentTitle', '内容标题', 200), count('shareCount', '分享次数'), count('visitCount', '访问次数'), count('conversionCount', '转化次数'), percent('conversionRate', '转化率')]
  )
]

export const REPORT_EXPECTED_MENU_COUNT = 43
export const REPORT_REPOSITORY_MENU_COUNT = reportDefinitions.length
export const REPORT_MENU_COUNT_GAP = REPORT_EXPECTED_MENU_COUNT - REPORT_REPOSITORY_MENU_COUNT

export const reportPageConfigs = reportDefinitions.reduce((result, report) => {
  result[report.title] = report
  return result
}, {})

export const reportMenuTitles = reportDefinitions.map(report => report.title)

applyOriginalEvidence('report', reportPageConfigs)

// Product-level names in the 104-item registry are intentionally mapped here.
// Previously they were not present in reportPageConfigs and rendered the first
// report definition through the generic fallback.  Keep the resource explicit
// and describe the capability boundary instead of showing a different report.
const reportFeatureAliases = {
  '数据报表': {
    source: 'S13销售业绩报表',
    presentation: 'report-builder',
    dataState: 'partial',
    description: '数据报表入口当前提供已接入经营数据的查询与 CSV 导出；自定义列、公式、打印模板尚未接入，因此不会生成模拟分析结果。'
  },
  '数据报表（自定义+导出）': {
    source: 'S13销售业绩报表',
    presentation: 'report-builder',
    dataState: 'partial',
    description: '数据报表入口当前提供已接入经营数据的查询与 CSV 导出；自定义列、公式、打印模板尚未接入，因此不会生成模拟分析结果。'
  },
  '经营月报': {
    source: 'C0经营月报',
    presentation: 'monthly-operation',
    dataState: 'partial',
    description: '经营月报按当前门店范围汇总已确认收款。退款、付款和成本记录不完整时保持为空或零值。'
  }
}

export function getReportPageConfig(title) {
  const alias = reportFeatureAliases[title]
  if (alias) {
    const source = reportPageConfigs[alias.source]
    return { ...source, ...alias, title }
  }
  return reportPageConfigs[title] || {
    ...reportDefinitions[0],
    title,
    key: 'unverified-report-page',
    presentation: 'pending',
    dataState: 'pending',
    description: '该报表的业务口径和展示字段正在确认。',
    filters: [],
    columns: []
  }
}
