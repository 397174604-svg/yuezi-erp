import { applyOriginalEvidence } from './original-page-evidence'
import { applyAuditedSurfaceEvidence } from './audited-surface-adapter'

const stores = ['中心广场旗舰店', '黄河路轻奢店']
const warehouses = ['五楼总库', '销售部仓库', '产康部仓库', '护理部仓库', '膳食部仓库']

const input = (key, label, placeholder = '') => ({ key, label, type: 'input', placeholder, verified: false })
const select = (key, label, options) => ({ key, label, type: 'select', options, verified: false })
const date = (key, label) => ({ key, label, type: 'date', verified: false })
const dateRange = (key, label) => ({ key, label, type: 'dateRange', verified: false })
const number = (key, label, required = false) => ({ key, label, type: 'number', required, verified: false })
const textarea = (key, label) => ({ key, label, type: 'textarea', verified: false })
const upload = (key, label) => ({ key, label, type: 'upload', verified: false })
const col = (key, label, width, tag = false, money = false) => ({ key, label, width, tag, money, verified: false })

const auditStatuses = ['待提交', '待审核', '审核通过', '审核不通过']
const stockStatuses = ['待处理', '部分完成', '已完成', '已取消']
const paymentStatuses = ['未付款', '部分付款', '已付款', '已取消']

const commonMeta = {
  evidenceLevel: '待原系统二次核验',
  completionLevel: 'Visible',
  originalUrl: '',
  originalNavid: '',
  queryActions: ['查询'],
  actions: [],
  formFields: [],
  evidenceNote: '仅菜单名称由仓库菜单证据确认；当前筛选项、按钮、列、默认值、下拉选项及交互均为仓存业务预置草案，尚未从原 ERP 页面逐项核验。'
}

const withMeta = config => ({ ...commonMeta, ...config })
const warehouseFilter = select('warehouse', '仓库', warehouses)
const storeFilter = select('store', '门店', stores)
const materialColumns = [
  col('materialCode', '物料编号', 130),
  col('materialName', '物料名称', 160),
  col('specification', '规格型号', 120),
  col('unit', '单位', 75),
  col('quantity', '数量', 90),
  col('unitPrice', '单价', 95, false, true),
  col('amount', '金额', 105, false, true)
]
const reportActions = ['查询', '导出', '打印']

export const inventoryPageConfigs = {
  采购计划: withMeta({
    key: 'purchase-plans',
    mode: 'transaction',
    icon: 'el-icon-shopping-cart-full',
    description: '预置采购需求、计划数量、预算金额与审批状态管理。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '导出', '打印'],
    filters: [input('planNo', '计划单号'), storeFilter, input('department', '申请部门'), select('auditStatus', '审核状态', auditStatuses), dateRange('planRange', '计划日期')],
    columns: [col('planNo', '计划单号', 150), col('planDate', '计划日期', 110), col('store', '门店', 150), col('department', '申请部门', 120), col('materialCount', '物料种类', 95), col('totalQuantity', '计划数量', 100), col('budgetAmount', '预算金额', 105, false, true), col('requiredDate', '需求日期', 110), col('auditStatus', '审核状态', 105, true), col('creator', '制单人', 100), col('createdAt', '制单时间', 150), col('remark', '备注', 180)],
    formFields: [date('planDate', '计划日期'), storeFilter, input('department', '申请部门'), date('requiredDate', '需求日期'), input('materialName', '物料名称'), number('planQuantity', '计划数量', true), number('budgetPrice', '预算单价'), textarea('planReason', '采购原因'), upload('attachment', '附件')]
  }),
  采购订单: withMeta({
    key: 'purchase-orders',
    mode: 'transaction',
    icon: 'el-icon-s-order',
    description: '预置供应商采购订单、到货与付款状态管理。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '到货登记', '打印'],
    filters: [input('orderNo', '采购单号'), input('supplier', '供应商'), storeFilter, select('auditStatus', '审核状态', auditStatuses), select('arrivalStatus', '到货状态', stockStatuses), dateRange('orderRange', '采购日期')],
    columns: [col('orderNo', '采购单号', 155), col('orderDate', '采购日期', 110), col('supplier', '供应商', 160), col('store', '采购门店', 150), col('warehouse', '入库仓库', 135), col('materialCount', '物料种类', 95), col('totalQuantity', '采购数量', 100), col('totalAmount', '采购金额', 110, false, true), col('arrivalStatus', '到货状态', 105, true), col('paymentStatus', '付款状态', 105, true), col('auditStatus', '审核状态', 105, true), col('buyer', '采购员', 100), col('createdAt', '制单时间', 150)],
    formFields: [date('orderDate', '采购日期'), input('supplier', '供应商'), storeFilter, select('warehouse', '入库仓库', warehouses), input('buyer', '采购员'), input('materialName', '物料名称'), number('quantity', '采购数量', true), number('unitPrice', '采购单价', true), date('expectedArrivalDate', '预计到货日期'), textarea('remark', '备注'), upload('attachment', '附件')]
  }),
  采购单审核: withMeta({
    key: 'purchase-order-audits',
    mode: 'approval',
    icon: 'el-icon-document-checked',
    description: '预置采购订单审核、反审核及审批意见查看。',
    actions: ['审核', '反审核', '批量审核', '查看审批记录', '打印'],
    filters: [input('orderNo', '采购单号'), input('supplier', '供应商'), storeFilter, select('auditStatus', '审核状态', auditStatuses), dateRange('orderRange', '采购日期')],
    columns: [col('orderNo', '采购单号', 155), col('orderDate', '采购日期', 110), col('supplier', '供应商', 160), col('store', '采购门店', 150), col('warehouse', '入库仓库', 135), col('totalAmount', '采购金额', 110, false, true), col('creator', '制单人', 100), col('auditStatus', '审核状态', 105, true), col('auditor', '审核人', 100), col('auditedAt', '审核时间', 150), col('auditOpinion', '审核意见', 180)]
  }),
  其他入库: withMeta({
    key: 'other-inbounds',
    mode: 'transaction',
    icon: 'el-icon-box',
    description: '预置非采购类入库单及物料明细登记。',
    actions: ['添加', '编辑', '删除', '审核', '反审核', '打印'],
    filters: [input('inboundNo', '入库单号'), warehouseFilter, select('inboundType', '入库类型', ['盘盈入库', '调拨入库', '退料入库', '其他入库']), select('auditStatus', '审核状态', auditStatuses), dateRange('inboundRange', '入库日期')],
    columns: [col('inboundNo', '入库单号', 155), col('inboundDate', '入库日期', 110), col('inboundType', '入库类型', 110), ...materialColumns, col('warehouse', '入库仓库', 135), col('operator', '经办人', 100), col('auditStatus', '审核状态', 105, true), col('creator', '制单人', 100), col('remark', '备注', 180)],
    formFields: [date('inboundDate', '入库日期'), select('inboundType', '入库类型', ['盘盈入库', '调拨入库', '退料入库', '其他入库']), select('warehouse', '入库仓库', warehouses), input('operator', '经办人'), input('materialName', '物料名称'), number('quantity', '入库数量', true), number('unitPrice', '入库单价'), textarea('remark', '入库说明'), upload('attachment', '附件')]
  }),
  采购入库: withMeta({
    key: 'purchase-inbounds',
    mode: 'transaction',
    icon: 'el-icon-receiving',
    description: '预置采购到货验收、批次与采购入库管理。',
    actions: ['采购入库', '编辑', '删除', '审核', '反审核', '打印'],
    filters: [input('inboundNo', '入库单号'), input('purchaseNo', '采购单号'), input('supplier', '供应商'), warehouseFilter, select('auditStatus', '审核状态', auditStatuses), dateRange('inboundRange', '入库日期')],
    columns: [col('inboundNo', '入库单号', 155), col('purchaseNo', '采购单号', 155), col('inboundDate', '入库日期', 110), col('supplier', '供应商', 160), ...materialColumns, col('batchNo', '批次号', 120), col('warehouse', '入库仓库', 135), col('auditStatus', '审核状态', 105, true), col('inspector', '验收人', 100)],
    formFields: [input('purchaseNo', '采购单号'), date('inboundDate', '入库日期'), input('supplier', '供应商'), select('warehouse', '入库仓库', warehouses), input('materialName', '物料名称'), input('batchNo', '批次号'), date('productionDate', '生产日期'), date('expiryDate', '有效期至'), number('quantity', '实收数量', true), number('unitPrice', '入库单价'), input('inspector', '验收人'), textarea('remark', '验收说明')]
  }),
  领料申请: withMeta({
    key: 'material-requisitions',
    mode: 'transaction',
    icon: 'el-icon-takeaway-box',
    description: '预置部门领料申请、金额、审核与出库状态管理。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '出库', '打印'],
    filters: [input('requisitionNo', '领料单号'), input('department', '领料部门'), warehouseFilter, select('auditStatus', '审核状态', auditStatuses), select('outboundStatus', '出库状态', stockStatuses), dateRange('requisitionRange', '申请日期')],
    columns: [col('requisitionNo', '领料单号', 155), col('requisitionDate', '申请日期', 110), col('department', '领料部门', 120), ...materialColumns, col('warehouse', '出库仓库', 135), col('applicant', '申请人', 100), col('auditStatus', '审核状态', 105, true), col('outboundStatus', '出库状态', 105, true), col('remark', '用途说明', 180)],
    formFields: [date('requisitionDate', '申请日期'), input('department', '领料部门'), input('applicant', '申请人'), select('warehouse', '出库仓库', warehouses), input('materialName', '物料名称'), number('quantity', '申请数量', true), input('purpose', '领料用途'), textarea('remark', '备注')]
  }),
  销售出库: withMeta({
    key: 'sales-outbounds',
    mode: 'transaction',
    icon: 'el-icon-sold-out',
    description: '预置销售单关联的物料拣货与出库管理。',
    actions: ['出库', '取消出库', '打印', '导出'],
    filters: [input('outboundNo', '出库单号'), input('saleNo', '销售单号'), input('customerName', '客户姓名'), warehouseFilter, select('outboundStatus', '出库状态', stockStatuses), dateRange('outboundRange', '出库日期')],
    columns: [col('outboundNo', '出库单号', 155), col('saleNo', '销售单号', 155), col('outboundDate', '出库日期', 110), col('customerName', '客户姓名', 110), ...materialColumns, col('warehouse', '出库仓库', 135), col('salesperson', '销售人', 100), col('outboundStatus', '出库状态', 105, true), col('operator', '出库人', 100), col('operatedAt', '出库时间', 150)]
  }),
  '领料申请(去金额)': withMeta({
    key: 'material-requisitions-no-amount',
    mode: 'transaction',
    icon: 'el-icon-takeaway-box',
    description: '预置隐藏价格和金额的部门领料申请视图。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '出库', '打印'],
    filters: [input('requisitionNo', '领料单号'), input('department', '领料部门'), warehouseFilter, select('auditStatus', '审核状态', auditStatuses), select('outboundStatus', '出库状态', stockStatuses), dateRange('requisitionRange', '申请日期')],
    columns: [col('requisitionNo', '领料单号', 155), col('requisitionDate', '申请日期', 110), col('department', '领料部门', 120), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('specification', '规格型号', 120), col('unit', '单位', 75), col('quantity', '数量', 90), col('warehouse', '出库仓库', 135), col('applicant', '申请人', 100), col('auditStatus', '审核状态', 105, true), col('outboundStatus', '出库状态', 105, true), col('remark', '用途说明', 180)],
    formFields: [date('requisitionDate', '申请日期'), input('department', '领料部门'), input('applicant', '申请人'), select('warehouse', '出库仓库', warehouses), input('materialName', '物料名称'), number('quantity', '申请数量', true), input('purpose', '领料用途'), textarea('remark', '备注')]
  }),
  调拨管理: withMeta({
    key: 'stock-transfers',
    mode: 'transaction',
    icon: 'el-icon-sort',
    description: '预置仓库之间的库存调拨与收货确认。',
    actions: ['添加', '编辑', '删除', '审核', '反审核', '调出确认', '调入确认', '打印'],
    filters: [input('transferNo', '调拨单号'), select('sourceWarehouse', '调出仓库', warehouses), select('targetWarehouse', '调入仓库', warehouses), select('transferStatus', '调拨状态', stockStatuses), dateRange('transferRange', '调拨日期')],
    columns: [col('transferNo', '调拨单号', 155), col('transferDate', '调拨日期', 110), col('sourceWarehouse', '调出仓库', 135), col('targetWarehouse', '调入仓库', 135), ...materialColumns, col('transferStatus', '调拨状态', 105, true), col('auditStatus', '审核状态', 105, true), col('operator', '经办人', 100), col('remark', '调拨原因', 180)],
    formFields: [date('transferDate', '调拨日期'), select('sourceWarehouse', '调出仓库', warehouses), select('targetWarehouse', '调入仓库', warehouses), input('materialName', '物料名称'), number('quantity', '调拨数量', true), input('operator', '经办人'), textarea('transferReason', '调拨原因')]
  }),
  退货管理: withMeta({
    key: 'purchase-returns',
    mode: 'transaction',
    icon: 'el-icon-refresh-left',
    description: '预置供应商退货、审核、出库与退款跟踪。',
    actions: ['添加', '编辑', '删除', '审核', '反审核', '退货出库', '打印'],
    filters: [input('returnNo', '退货单号'), input('purchaseNo', '采购单号'), input('supplier', '供应商'), warehouseFilter, select('auditStatus', '审核状态', auditStatuses), dateRange('returnRange', '退货日期')],
    columns: [col('returnNo', '退货单号', 155), col('purchaseNo', '采购单号', 155), col('returnDate', '退货日期', 110), col('supplier', '供应商', 160), ...materialColumns, col('warehouse', '退货仓库', 135), col('auditStatus', '审核状态', 105, true), col('refundStatus', '退款状态', 105, true), col('returnReason', '退货原因', 180)],
    formFields: [input('purchaseNo', '采购单号'), date('returnDate', '退货日期'), input('supplier', '供应商'), select('warehouse', '退货仓库', warehouses), input('materialName', '物料名称'), number('quantity', '退货数量', true), number('unitPrice', '退货单价'), textarea('returnReason', '退货原因'), upload('attachment', '附件')]
  }),
  '盘点管理(NEW)': withMeta({
    key: 'stocktakes',
    mode: 'stocktake',
    icon: 'el-icon-document-copy',
    description: '预置盘点任务、账面数量、实盘数量与盈亏调整。',
    actions: ['新建盘点', '开始盘点', '录入盘点', '完成盘点', '审核', '反审核', '打印'],
    filters: [input('stocktakeNo', '盘点单号'), warehouseFilter, select('stocktakeStatus', '盘点状态', ['未开始', '盘点中', '待审核', '已完成', '已取消']), input('materialName', '物料名称'), dateRange('stocktakeRange', '盘点日期')],
    columns: [col('stocktakeNo', '盘点单号', 155), col('stocktakeDate', '盘点日期', 110), col('warehouse', '盘点仓库', 135), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('batchNo', '批次号', 120), col('bookQuantity', '账面数量', 100), col('actualQuantity', '实盘数量', 100), col('differenceQuantity', '盈亏数量', 100), col('differenceAmount', '盈亏金额', 105, false, true), col('stocktakeStatus', '盘点状态', 105, true), col('stocktaker', '盘点人', 100), col('auditStatus', '审核状态', 105, true)],
    formFields: [date('stocktakeDate', '盘点日期'), select('warehouse', '盘点仓库', warehouses), input('stocktaker', '盘点人'), input('materialName', '物料名称'), input('batchNo', '批次号'), number('actualQuantity', '实盘数量', true), textarea('remark', '盘点说明')]
  }),
  报损管理: withMeta({
    key: 'stock-damages',
    mode: 'transaction',
    icon: 'el-icon-warning-outline',
    description: '预置库存破损、过期或丢失报损与审批。',
    actions: ['添加', '编辑', '删除', '审核', '反审核', '确认报损', '打印'],
    filters: [input('damageNo', '报损单号'), warehouseFilter, select('damageType', '报损类型', ['破损', '过期', '变质', '丢失', '其他']), select('auditStatus', '审核状态', auditStatuses), dateRange('damageRange', '报损日期')],
    columns: [col('damageNo', '报损单号', 155), col('damageDate', '报损日期', 110), col('warehouse', '报损仓库', 135), ...materialColumns, col('batchNo', '批次号', 120), col('damageType', '报损类型', 100), col('auditStatus', '审核状态', 105, true), col('operator', '报损人', 100), col('damageReason', '报损原因', 180)],
    formFields: [date('damageDate', '报损日期'), select('warehouse', '报损仓库', warehouses), select('damageType', '报损类型', ['破损', '过期', '变质', '丢失', '其他']), input('materialName', '物料名称'), input('batchNo', '批次号'), number('quantity', '报损数量', true), textarea('damageReason', '报损原因'), upload('attachment', '附件')]
  }),
  期初数据导入: withMeta({
    key: 'opening-stock-import',
    mode: 'import',
    icon: 'el-icon-upload2',
    description: '预置库存期初模板下载、文件校验、导入与结果反馈。',
    actions: ['下载模板', '校验文件', '导入数据', '查看导入记录'],
    filters: [storeFilter, warehouseFilter, input('batchNo', '导入批次号'), select('importStatus', '导入状态', ['待校验', '校验通过', '校验失败', '已导入']), dateRange('importRange', '导入日期')],
    columns: [col('batchNo', '导入批次号', 155), col('fileName', '文件名称', 180), col('store', '门店', 150), col('warehouse', '仓库', 135), col('totalRows', '总行数', 90), col('successRows', '成功行数', 90), col('failedRows', '失败行数', 90), col('importStatus', '导入状态', 105, true), col('importer', '导入人', 100), col('importedAt', '导入时间', 150), col('errorMessage', '错误说明', 220)],
    formFields: [storeFilter, warehouseFilter, upload('openingFile', '期初库存文件'), textarea('remark', '导入说明')]
  }),
  物料库存预警: withMeta({
    key: 'stock-warnings',
    mode: 'warning',
    icon: 'el-icon-bell',
    description: '预置安全库存、缺货、积压和临期预警。',
    actions: ['设置预警值', '生成采购计划', '导出'],
    filters: [input('materialName', '物料名称'), warehouseFilter, select('warningType', '预警类型', ['低于安全库存', '库存为零', '库存积压', '临期', '已过期']), select('warningStatus', '处理状态', ['未处理', '处理中', '已处理'])],
    columns: [col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('specification', '规格型号', 120), col('unit', '单位', 75), col('warehouse', '仓库', 135), col('currentQuantity', '当前库存', 100), col('safetyQuantity', '安全库存', 100), col('maxQuantity', '库存上限', 100), col('warningType', '预警类型', 120, true), col('expiryDate', '最近有效期', 110), col('warningStatus', '处理状态', 105, true), col('lastHandledAt', '处理时间', 150)],
    formFields: [select('warehouse', '仓库', warehouses), input('materialName', '物料名称'), number('safetyQuantity', '安全库存'), number('maxQuantity', '库存上限'), number('expiryWarningDays', '临期预警天数'), textarea('remark', '备注')]
  }),
  期初数据查询: withMeta({
    key: 'opening-stock-query',
    mode: 'report',
    icon: 'el-icon-search',
    description: '预置按仓库、物料、批次查询库存期初数据。',
    queryActions: reportActions,
    filters: [storeFilter, warehouseFilter, input('materialCode', '物料编号'), input('materialName', '物料名称'), input('batchNo', '批次号'), dateRange('openingRange', '期初日期')],
    columns: [col('openingDate', '期初日期', 110), col('store', '门店', 150), col('warehouse', '仓库', 135), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('specification', '规格型号', 120), col('batchNo', '批次号', 120), col('unit', '单位', 75), col('openingQuantity', '期初数量', 100), col('openingPrice', '期初单价', 100, false, true), col('openingAmount', '期初金额', 105, false, true), col('importBatchNo', '导入批次号', 155)]
  }),
  赠送清单计划: withMeta({
    key: 'gift-list-plans',
    mode: 'transaction',
    icon: 'el-icon-present',
    description: '预置客户赠送物品计划、审核与发放关联。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '生成领料单', '打印'],
    filters: [input('planNo', '计划单号'), input('customerName', '客户姓名'), storeFilter, select('auditStatus', '审核状态', auditStatuses), select('issueStatus', '发放状态', stockStatuses), dateRange('planRange', '计划日期')],
    columns: [col('planNo', '计划单号', 155), col('planDate', '计划日期', 110), col('customerName', '客户姓名', 110), col('room', '房间号', 90), col('store', '门店', 150), col('materialName', '赠送物品', 160), col('quantity', '计划数量', 100), col('warehouse', '领料仓库', 135), col('auditStatus', '审核状态', 105, true), col('issueStatus', '发放状态', 105, true), col('creator', '制单人', 100), col('remark', '赠送说明', 180)],
    formFields: [date('planDate', '计划日期'), input('customerName', '客户姓名'), input('room', '房间号'), storeFilter, select('warehouse', '领料仓库', warehouses), input('materialName', '赠送物品'), number('quantity', '计划数量', true), textarea('remark', '赠送说明')]
  }),
  收发存汇总统计: withMeta({
    key: 'stock-summary-report',
    mode: 'report',
    icon: 'el-icon-data-analysis',
    description: '预置期初、收入、发出和期末库存数量金额汇总。',
    queryActions: reportActions,
    filters: [storeFilter, warehouseFilter, input('materialCode', '物料编号'), input('materialName', '物料名称'), dateRange('businessRange', '业务日期')],
    columns: [col('warehouse', '仓库', 135), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('specification', '规格型号', 120), col('unit', '单位', 75), col('openingQuantity', '期初数量', 100), col('openingAmount', '期初金额', 105, false, true), col('inQuantity', '收入数量', 100), col('inAmount', '收入金额', 105, false, true), col('outQuantity', '发出数量', 100), col('outAmount', '发出金额', 105, false, true), col('closingQuantity', '期末数量', 100), col('closingAmount', '期末金额', 105, false, true)]
  }),
  库存明细统计: withMeta({
    key: 'stock-ledger-report',
    mode: 'report',
    icon: 'el-icon-document',
    description: '预置物料逐笔出入库流水及结存统计。',
    queryActions: reportActions,
    filters: [warehouseFilter, input('materialCode', '物料编号'), input('materialName', '物料名称'), select('businessType', '业务类型', ['采购入库', '其他入库', '销售出库', '领料出库', '调拨', '退货', '盘点', '报损']), dateRange('businessRange', '业务日期')],
    columns: [col('businessDate', '业务日期', 110), col('documentNo', '单据编号', 155), col('businessType', '业务类型', 110), col('warehouse', '仓库', 135), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('batchNo', '批次号', 120), col('inQuantity', '入库数量', 100), col('outQuantity', '出库数量', 100), col('balanceQuantity', '结存数量', 100), col('unitPrice', '单价', 95, false, true), col('balanceAmount', '结存金额', 105, false, true), col('operator', '经办人', 100)]
  }),
  部门领料统计: withMeta({
    key: 'department-requisition-report',
    mode: 'report',
    icon: 'el-icon-office-building',
    description: '预置部门、物料及仓库维度的领料汇总。',
    queryActions: reportActions,
    filters: [input('department', '领料部门'), warehouseFilter, input('materialName', '物料名称'), input('applicant', '领料人'), dateRange('requisitionRange', '领料日期')],
    columns: [col('department', '领料部门', 120), col('warehouse', '出库仓库', 135), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('specification', '规格型号', 120), col('unit', '单位', 75), col('documentCount', '领料单数', 100), col('totalQuantity', '领料数量', 100), col('averagePrice', '平均单价', 100, false, true), col('totalAmount', '领料金额', 105, false, true), col('lastRequisitionDate', '最后领料日期', 120)]
  }),
  仓库库存查询: withMeta({
    key: 'warehouse-stock-query',
    mode: 'report',
    icon: 'el-icon-house',
    description: '预置各仓库物料当前库存、可用量、锁定量和批次有效期查询。',
    queryActions: ['查询', '导出'],
    filters: [storeFilter, warehouseFilter, input('materialCode', '物料编号'), input('materialName', '物料名称'), input('batchNo', '批次号'), select('stockCondition', '库存条件', ['有库存', '零库存', '负库存', '全部'])],
    columns: [col('store', '门店', 150), col('warehouse', '仓库', 135), col('materialCode', '物料编号', 130), col('materialName', '物料名称', 160), col('specification', '规格型号', 120), col('batchNo', '批次号', 120), col('unit', '单位', 75), col('currentQuantity', '当前库存', 100), col('lockedQuantity', '锁定数量', 100), col('availableQuantity', '可用数量', 100), col('unitPrice', '库存单价', 100, false, true), col('stockAmount', '库存金额', 105, false, true), col('expiryDate', '有效期至', 110)]
  }),
  采购明细报表: withMeta({
    key: 'purchase-detail-report',
    mode: 'report',
    icon: 'el-icon-tickets',
    description: '预置采购订单、供应商、物料、到货和入库明细分析。',
    queryActions: reportActions,
    filters: [input('purchaseNo', '采购单号'), input('supplier', '供应商'), storeFilter, warehouseFilter, input('materialName', '物料名称'), dateRange('purchaseRange', '采购日期')],
    columns: [col('purchaseNo', '采购单号', 155), col('purchaseDate', '采购日期', 110), col('supplier', '供应商', 160), col('store', '采购门店', 150), col('warehouse', '入库仓库', 135), ...materialColumns, col('receivedQuantity', '已到货数量', 105), col('inboundQuantity', '已入库数量', 105), col('buyer', '采购员', 100), col('auditStatus', '审核状态', 105, true)]
  }),
  预付款列表: withMeta({
    key: 'supplier-prepayments',
    mode: 'finance',
    icon: 'el-icon-wallet',
    description: '预置供应商预付款申请、审核、支付和核销管理。',
    actions: ['添加', '编辑', '删除', '提交', '审核', '反审核', '付款', '核销', '打印'],
    filters: [input('prepaymentNo', '预付款单号'), input('supplier', '供应商'), select('auditStatus', '审核状态', auditStatuses), select('paymentStatus', '付款状态', paymentStatuses), dateRange('applicationRange', '申请日期')],
    columns: [col('prepaymentNo', '预付款单号', 155), col('applicationDate', '申请日期', 110), col('supplier', '供应商', 160), col('purchaseNo', '采购单号', 155), col('applicationAmount', '申请金额', 105, false, true), col('paidAmount', '已付金额', 105, false, true), col('writtenOffAmount', '已核销金额', 105, false, true), col('remainingAmount', '未核销金额', 105, false, true), col('auditStatus', '审核状态', 105, true), col('paymentStatus', '付款状态', 105, true), col('applicant', '申请人', 100), col('paymentDate', '付款日期', 110), col('remark', '备注', 180)],
    formFields: [date('applicationDate', '申请日期'), input('supplier', '供应商'), input('purchaseNo', '采购单号'), number('applicationAmount', '申请金额', true), input('paymentAccount', '付款账户'), input('applicant', '申请人'), textarea('paymentPurpose', '付款用途'), upload('attachment', '附件')]
  }),
  付款单列表: withMeta({
    key: 'supplier-payments',
    mode: 'finance',
    icon: 'el-icon-bank-card',
    description: '预置采购付款单、资金账户、审核与支付状态查询。',
    actions: ['添加', '编辑', '删除', '审核', '反审核', '确认付款', '打印'],
    filters: [input('paymentNo', '付款单号'), input('supplier', '供应商'), input('purchaseNo', '采购单号'), select('auditStatus', '审核状态', auditStatuses), select('paymentStatus', '付款状态', paymentStatuses), dateRange('paymentRange', '付款日期')],
    columns: [col('paymentNo', '付款单号', 155), col('paymentDate', '付款日期', 110), col('supplier', '供应商', 160), col('purchaseNo', '采购单号', 155), col('paymentType', '付款类型', 105), col('paymentAmount', '付款金额', 105, false, true), col('paymentAccount', '付款账户', 140), col('paymentMethod', '付款方式', 105), col('auditStatus', '审核状态', 105, true), col('paymentStatus', '付款状态', 105, true), col('operator', '经办人', 100), col('paidAt', '确认付款时间', 150), col('remark', '备注', 180)],
    formFields: [date('paymentDate', '付款日期'), input('supplier', '供应商'), input('purchaseNo', '采购单号'), select('paymentType', '付款类型', ['预付款', '采购付款', '退货退款', '其他付款']), number('paymentAmount', '付款金额', true), input('paymentAccount', '付款账户'), select('paymentMethod', '付款方式', ['现金', '银行转账', '微信', '支付宝']), input('operator', '经办人'), textarea('remark', '备注'), upload('attachment', '附件')]
  }),
  应付账款明细表: withMeta({
    key: 'accounts-payable-detail',
    mode: 'report',
    icon: 'el-icon-money',
    description: '预置供应商应付、已付、预付核销与未付余额明细。',
    queryActions: reportActions,
    filters: [input('supplier', '供应商'), input('purchaseNo', '采购单号'), storeFilter, select('settlementStatus', '结算状态', ['未结算', '部分结算', '已结算']), dateRange('businessRange', '业务日期')],
    columns: [col('businessDate', '业务日期', 110), col('supplier', '供应商', 160), col('purchaseNo', '采购单号', 155), col('store', '采购门店', 150), col('payableAmount', '应付金额', 105, false, true), col('prepaymentAmount', '预付金额', 105, false, true), col('paidAmount', '已付金额', 105, false, true), col('returnAmount', '退货金额', 105, false, true), col('unpaidAmount', '未付金额', 105, false, true), col('dueDate', '到期日期', 110), col('settlementStatus', '结算状态', 105, true), col('lastPaymentDate', '最后付款日期', 120)]
  })
}

applyOriginalEvidence('warehouse', inventoryPageConfigs)
applyAuditedSurfaceEvidence('warehouse', inventoryPageConfigs)

export function getInventoryPageConfig(title) {
  return inventoryPageConfigs[title] || inventoryPageConfigs.采购计划
}
