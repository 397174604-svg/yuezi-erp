<template>
  <div class="inventory-workbench">
    <div class="page-heading">
      <div>
        <div class="title-row">
          <i :class="pageConfig.icon" />
          <h2>{{ title }}</h2>
        </div>
        <p>{{ pageConfig.description }}</p>
      </div>
    </div>

    <el-card v-if="sharedWorkspaceTabs.length" shadow="never" class="shared-workbench-card">
      <div class="shared-workbench-title">{{ pageConfig.workspace.note }}</div>
      <el-tabs :value="title" @tab-click="switchSharedWorkspace">
        <el-tab-pane
          v-for="tab in sharedWorkspaceTabs"
          :key="tab.title"
          :label="tab.label"
          :name="tab.title"
        />
      </el-tabs>
    </el-card>

    <audited-surface-panel
      :config="pageConfig"
      show-action-icons
      @business-action="handleBusinessAction"
      @query-action="handleQueryAction"
    />

    <inventory-p0-workflow
      v-if="p0WorkflowResources.includes(pageConfig.key)"
      :resource="pageConfig.key"
      :rows="filteredRows"
      @select="selectedRow = $event"
    />

    <section v-if="inventoryVisual" class="inventory-visual" :class="`inventory-${inventoryVisual.kind}`">
      <div class="inventory-copy"><span>{{ inventoryVisual.kicker }}</span><h3>{{ inventoryVisual.heading }}</h3><p>{{ inventoryVisual.description }}</p></div>
      <div class="inventory-stages"><article v-for="(stage, index) in inventoryVisual.stages" :key="stage"><b>{{ index + 1 }}</b><strong>{{ stage }}</strong><small>{{ inventoryVisual.notes[index] }}</small></article></div>
      <div class="inventory-footer"><span>当前查询记录：{{ filteredRows.length }} 条</span><el-button size="mini" @click="handleQueryAction('查询')">刷新</el-button></div>
    </section>

    <el-card v-if="pageConfig.mode === 'import'" shadow="never" class="import-card">
      <div slot="header">期初数据文件</div>
      <el-upload action="#" :auto-upload="false" :limit="1" accept=".xls,.xlsx,.csv">
        <el-button size="small" type="primary">点击选择文件</el-button>
        <div slot="tip" class="el-upload__tip">支持 .xls、.xlsx、.csv，导入前请核对门店、仓库和必填列。</div>
      </el-upload>
    </el-card>

    <div v-if="pageConfig.mode === 'warning'" class="metric-grid">
      <el-card v-for="metric in warningMetrics" :key="metric.label" shadow="hover">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>来自当前门店业务数据</small>
      </el-card>
    </div>

    <el-card shadow="never" class="table-card">
      <div slot="header" class="card-header">
        <span>{{ title }}列表</span>
        <span>共 {{ filteredRows.length }} 条</span>
      </div>
      <el-table
        :data="pagedRows"
        border
        stripe
        size="small"
        highlight-current-row
        @current-change="selectedRow = $event"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="44" fixed="left" />
        <el-table-column type="index" label="序号" width="55" fixed="left" />
        <el-table-column
          v-for="column in pageConfig.columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :width="column.width"
          :min-width="column.width ? undefined : 120"
          show-overflow-tooltip
        >
          <template slot-scope="{ row }">
            <el-tag v-if="column.tag" :type="tagType(row[column.key])" size="mini">
              {{ row[column.key] }}
            </el-tag>
            <span v-else-if="column.money">¥ {{ moneyText(row[column.key]) }}</span>
            <span v-else>{{ row[column.key] }}</span>
          </template>
        </el-table-column>
      </el-table>
      <pagination
        v-show="filteredRows.length > pageSize"
        :total="filteredRows.length"
        :page.sync="page"
        :limit.sync="pageSize"
        @pagination="noop"
      />
    </el-card>

    <el-dialog :title="dialogAction" :visible.sync="dialogVisible" width="680px">
      <el-alert
        title="保存后将生成当前门店业务记录；库存实物变动须按审核、出入库或调拨流程执行。"
        type="warning"
        :closable="false"
        show-icon
      />
      <el-form v-if="dialogFields.length" :model="form" label-width="110px" class="dialog-form">
        <el-form-item v-for="field in dialogFields" :key="field.key" :label="field.label" :required="field.required">
          <el-input v-if="field.type === 'input'" v-model="form[field.key]" />
          <el-input-number v-else-if="field.type === 'number'" v-model="form[field.key]" :min="0" />
          <el-input v-else-if="field.type === 'textarea'" v-model="form[field.key]" type="textarea" :rows="3" />
          <el-select v-else-if="field.type === 'select'" v-model="form[field.key]" filterable clearable @change="field.key === 'store' ? handleDialogStoreChange() : null">
            <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
          </el-select>
          <el-select v-else-if="field.type === 'supplier-select'" v-model="form.supplier" filterable clearable :disabled="!form.store || referenceOptionsLoading">
            <el-option v-for="option in referenceOptions.suppliers" :key="option.name" :label="option.name" :value="option.name" />
          </el-select>
          <el-select v-else-if="field.type === 'material-select'" v-model="form.materialName" filterable clearable :disabled="!form.store || referenceOptionsLoading">
            <el-option v-for="option in referenceOptions.materials" :key="option.id" :label="`${option.name}${option.unit ? `（${option.unit}）` : ''}`" :value="option.name" />
          </el-select>
          <el-date-picker v-else-if="field.type === 'date'" v-model="form[field.key]" type="date" value-format="yyyy-MM-dd" />
          <el-upload v-else-if="field.type === 'upload'" action="#" :auto-upload="false" :limit="1">
            <el-button size="small">点击选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <div v-else class="confirm-copy">该状态操作会写入所选记录并保留审计事件。</div>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBusinessAction">确认</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Pagination from '@/components/Pagination'
import { getInventoryModuleData, getInventoryStoreReferenceOptions, performInventoryModuleAction, saveInventoryModuleRecord } from '@/api/erp-inventory'
import { getInventoryPageConfig } from '@/config/inventory-pages'
import { findErpRouteByTitle, workspaceTabs } from '@/utils/erp-workbench-tabs'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'
import InventoryP0Workflow from '@/views/erp/components/InventoryP0Workflow'

const demoWarehouses = ['五楼总库', '销售部仓库', '产康部仓库', '护理部仓库', '膳食部仓库']

export default {
  name: 'InventoryWorkbench',
  components: { AuditedSurfacePanel, InventoryP0Workflow, Pagination },
  data() {
    return {
      filters: {},
      rows: [],
      page: 1,
      pageSize: 10,
      dialogVisible: false,
      dialogAction: '',
      dialogFields: [],
      form: {},
      loadingResource: '',
      loadSequence: 0,
      selectedRow: null,
      selectedRows: [],
      referenceOptions: { materials: [], suppliers: [] },
      referenceOptionsLoading: false,
      p0WorkflowResources: ['purchase-orders', 'stock-transfers', 'stocktakes', 'stock-warnings', 'warehouse-stock-query', 'stock-summary-report', 'batch-expiry']
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    businessStoreId() {
      return String(this.currentStoreId || 'all')
    },
    isAllStores() {
      return this.businessStoreId === 'all'
    },
    title() {
      const meta = this.$route.meta || {}
      return String(meta.configTitle || meta.title || '采购计划').replace(/\s*★\s*$/, '')
    },
    pageConfig() {
      return getInventoryPageConfig(this.title)
    },
    sharedWorkspaceTabs() {
      return workspaceTabs(this.pageConfig)
    },
    filteredRows() {
      const activeFilters = Object.entries(this.filters).filter(([, value]) => {
        if (Array.isArray(value)) return value.length > 0
        return value !== '' && value !== null && value !== undefined
      })
      if (!activeFilters.length) return this.rows
      return this.rows.filter(row => activeFilters.every(([key, value]) => {
        if (Array.isArray(value)) {
          const target = String(row[key] || row.documentDate || row.businessDate || '')
          return (!value[0] || target >= value[0]) && (!value[1] || target <= value[1])
        }
        return String(row[key] || '').includes(String(value))
      }))
    },
    pagedRows() {
      const start = (this.page - 1) * this.pageSize
      return this.filteredRows.slice(start, start + this.pageSize)
    },
    warningMetrics() {
      return [
        { label: '库存不足', value: this.rows.filter(row => /库存为零|低于安全库存/.test(row.warningType)).length },
        { label: '临期物料', value: this.rows.filter(row => row.warningType === '临期').length },
        { label: '已过期', value: this.rows.filter(row => row.warningType === '已过期').length },
        { label: '待处理', value: this.rows.filter(row => row.warningStatus === '未处理').length }
      ]
    },
    inventoryVisual() {
      const views = {
        'stock-ledger-report': { kind: 'ledger', kicker: '库存总账', heading: '收发存流水与结存', description: '按物料、批次和仓库追溯每一笔入库、出库与结存变化。', stages: ['期初结存', '入库流水', '出库流水', '期末结存'], notes: ['来源可追溯', '采购与退料', '领料与销售', '金额与数量'] },
        'stock-transfers': { kind: 'transfer', kicker: '调拨双向确认', heading: '调出、在途与调入', description: '库存调拨必须由调出仓确认后进入在途，再由调入仓确认收货。', stages: ['调拨申请', '调出确认', '在途追踪', '调入确认'], notes: ['来源仓', '扣减库存', '单据跟踪', '增加库存'] },
        stocktakes: { kind: 'stocktake', kicker: '盘点工作台', heading: '账面、实盘与差异审核', description: '盘点先锁定账面数量，录入实盘后生成差异，再进入审核调整。', stages: ['创建盘点', '录入实盘', '差异复核', '审核调整'], notes: ['盘点范围', '实盘数量', '盈亏明细', '审计留痕'] },
        'stock-warnings': { kind: 'warning', kicker: '效期与库存预警', heading: '安全库存、临期与过期', description: '预警产生后应转为采购、调拨或报损动作，不能直接视为已处理。', stages: ['识别预警', '确认原因', '生成处理单', '处理留痕'], notes: ['数量 / 效期', '责任仓库', '采购或调拨', '关闭预警'] },
        'batch-expiry': { kind: 'warning', kicker: '批次效期看板', heading: '批次、效期与处置', description: '按批次跟踪临期物料，处置结果需要回写库存与审计记录。', stages: ['扫描批次', '临期预警', '处置申请', '结果留痕'], notes: ['批次信息', '预警天数', '报损或调拨', '库存回写'] }
      }
      return views[this.pageConfig.key] || null
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    },
    currentStoreId(value, previous) {
      if (String(value) !== String(previous)) this.initializePage()
    }
  },
  methods: {
    switchSharedWorkspace(tab) {
      if (!tab.name || tab.name === this.title) return
      const target = findErpRouteByTitle(this.$router.options.routes, tab.name)
      if (!target) {
        this.$message.error('未找到对应工作台入口，请联系管理员核对菜单配置。')
        return
      }
      this.$router.push({ name: target.name, query: { ...this.$route.query }})
    },
    initializePage() {
      this.filters = {}
      this.page = 1
      this.rows = []
      this.selectedRow = null
      this.selectedRows = []
      this.loadModuleData()
    },
    async loadModuleData() {
      const resource = this.pageConfig.key
      const sequence = ++this.loadSequence
      this.loadingResource = resource
      try {
        const response = await getInventoryModuleData(resource, {
          ...this.filters,
          storeId: this.businessStoreId
        })
        if (this.loadingResource === resource && this.loadSequence === sequence) {
          this.rows = response.data && Array.isArray(response.data.list)
            ? response.data.list
            : []
        }
      } catch (error) {
        if (this.loadSequence === sequence) this.rows = []
      }
    },
    createDemoRow(index) {
      const sequence = String(index + 1).padStart(4, '0')
      const day = String((index % 9) + 10).padStart(2, '0')
      const dateValue = `2026-07-${day}`
      const quantity = 12 + index * 3
      const unitPrice = 18 + index * 2
      return {
        documentNo: `INV-DEMO-${sequence}`, planNo: `PP-DEMO-${sequence}`, orderNo: `PO-DEMO-${sequence}`,
        purchaseNo: `PO-DEMO-${sequence}`, inboundNo: `IN-DEMO-${sequence}`, outboundNo: `OUT-DEMO-${sequence}`,
        requisitionNo: `REQ-DEMO-${sequence}`, transferNo: `TR-DEMO-${sequence}`, returnNo: `RT-DEMO-${sequence}`,
        stocktakeNo: `ST-DEMO-${sequence}`, damageNo: `DM-DEMO-${sequence}`, prepaymentNo: `PRE-DEMO-${sequence}`,
        paymentNo: `PAY-DEMO-${sequence}`, importBatchNo: `OPEN-DEMO-${sequence}`, batchNo: `B-DEMO-${sequence}`,
        fileName: `期初库存演示文件-${sequence}.xlsx`, materialCode: `MAT-DEMO-${sequence}`,
        materialName: ['演示护理垫', '演示消毒用品', '演示纸品', '演示营养食材'][index % 4],
        specification: ['10片/包', '500ml/瓶', '20卷/箱', '1kg/袋'][index % 4], unit: ['包', '瓶', '箱', '袋'][index % 4],
        store: index % 2 ? '中心广场旗舰店' : '黄河路轻奢店', warehouse: demoWarehouses[index % demoWarehouses.length],
        sourceWarehouse: demoWarehouses[index % demoWarehouses.length], targetWarehouse: demoWarehouses[(index + 1) % demoWarehouses.length],
        department: ['护理部', '产康部', '膳食部'][index % 3], supplier: `演示供应商${String.fromCharCode(65 + index % 4)}`,
        customerName: `演示客户${String.fromCharCode(65 + index % 5)}`, room: `${3 + index % 4}0${1 + index % 8}`,
        planDate: dateValue, orderDate: dateValue, documentDate: dateValue, businessDate: dateValue,
        inboundDate: dateValue, outboundDate: dateValue, requisitionDate: dateValue, transferDate: dateValue,
        returnDate: dateValue, stocktakeDate: dateValue, damageDate: dateValue, paymentDate: dateValue,
        applicationDate: dateValue, openingDate: dateValue, purchaseDate: dateValue, expiryDate: '2027-07-31',
        requiredDate: '2026-07-31', dueDate: '2026-08-15', lastPaymentDate: dateValue, lastRequisitionDate: dateValue,
        quantity, planQuantity: quantity, totalQuantity: quantity, plannedQuantity: quantity, purchaseQuantity: quantity,
        currentQuantity: quantity + 20, safetyQuantity: 20, maxQuantity: 120, lockedQuantity: index % 3,
        availableQuantity: quantity + 20 - index % 3, openingQuantity: 20, inQuantity: quantity, outQuantity: index + 2,
        balanceQuantity: quantity + 18, closingQuantity: quantity + 18, receivedQuantity: quantity - 1,
        inboundQuantity: quantity - 2, bookQuantity: quantity + 1, actualQuantity: quantity,
        differenceQuantity: -1, materialCount: 3 + index % 5, documentCount: 2 + index % 4,
        unitPrice, averagePrice: unitPrice, amount: quantity * unitPrice, totalAmount: quantity * unitPrice,
        budgetAmount: quantity * unitPrice, openingPrice: unitPrice, openingAmount: 20 * unitPrice,
        inAmount: quantity * unitPrice, outAmount: (index + 2) * unitPrice, closingAmount: (quantity + 18) * unitPrice,
        balanceAmount: (quantity + 18) * unitPrice, stockAmount: (quantity + 20) * unitPrice,
        differenceAmount: -unitPrice, applicationAmount: 1200 + index * 100, paymentAmount: 800 + index * 100,
        payableAmount: 2000 + index * 100, prepaymentAmount: 500, paidAmount: 800,
        writtenOffAmount: 300, remainingAmount: 200, returnAmount: 100, unpaidAmount: 600 + index * 100,
        auditStatus: ['待提交', '待审核', '审核通过', '审核不通过'][index % 4],
        arrivalStatus: ['待处理', '部分完成', '已完成'][index % 3],
        outboundStatus: ['待处理', '部分完成', '已完成'][index % 3],
        issueStatus: ['待处理', '部分完成', '已完成'][index % 3],
        transferStatus: ['待处理', '部分完成', '已完成'][index % 3],
        stocktakeStatus: ['未开始', '盘点中', '待审核', '已完成'][index % 4],
        paymentStatus: ['未付款', '部分付款', '已付款'][index % 3],
        refundStatus: ['未退款', '部分退款', '已退款'][index % 3],
        importStatus: ['待校验', '校验通过', '已导入'][index % 3],
        warningType: ['低于安全库存', '临期', '库存积压'][index % 3],
        warningStatus: ['未处理', '处理中', '已处理'][index % 3],
        settlementStatus: ['未结算', '部分结算', '已结算'][index % 3],
        businessType: ['采购入库', '领料出库', '调拨'][index % 3],
        inboundType: ['盘盈入库', '退料入库', '其他入库'][index % 3],
        damageType: ['破损', '过期', '其他'][index % 3], paymentType: ['预付款', '采购付款', '其他付款'][index % 3],
        stockCondition: '有库存', applicant: '演示申请人', operator: '演示经办人', creator: '演示制单人',
        buyer: '演示采购员', inspector: '演示验收人', stocktaker: '演示盘点人', auditor: '演示审核人',
        salesperson: '演示销售员', paymentAccount: '演示资金账户', paymentMethod: '银行转账',
        creatorName: '演示制单人', createdAt: `${dateValue} 09:30`, auditedAt: `${dateValue} 14:20`,
        operatedAt: `${dateValue} 15:10`, paidAt: `${dateValue} 16:00`, importedAt: `${dateValue} 10:00`,
        lastHandledAt: `${dateValue} 17:00`, totalRows: 20, successRows: 20, failedRows: 0,
        auditOpinion: '', returnReason: '', damageReason: '',
        errorMessage: '', remark: ''
      }
    },
    async handleQueryAction(action, filters = {}) {
      if (action === '导出') {
        this.exportCsv()
      } else if (action === '打印') {
        window.print()
      } else {
        this.filters = filters
        this.page = 1
        await this.loadModuleData()
      }
    },
    handleSelectionChange(rows) {
      this.selectedRows = rows
      if (rows.length) this.selectedRow = rows[0]
    },
    handleBusinessAction(action) {
      if (this.isAllStores && !['导出', '打印'].includes(action)) {
        this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
        return
      }
      if (action === '导出') {
        this.exportCsv()
        return
      }
      if (action === '打印') {
        window.print()
        return
      }
      const saveAction = this.isSaveAction(action)
      if (!saveAction && (!this.selectedRow || !this.selectedRow.recordId)) {
        this.$message.warning('请先选择一条本地已落库记录')
        return
      }
      if (action === '编辑' && (!this.selectedRow || !this.selectedRow.recordId)) {
        this.$message.warning('历史源记录为只读，请选择本地已落库记录')
        return
      }
      this.dialogAction = action
      this.dialogFields = saveAction ? this.pageConfig.formFields : this.actionFields(action)
      this.form = this.dialogFields.reduce((result, field) => {
        const value = this.selectedRow && action === '编辑' ? this.selectedRow[field.key] : undefined
        result[field.key] = value !== undefined ? value : (field.type === 'number' ? 0 : '')
        return result
      }, {})
      if (this.dialogFields.some(field => field.key === 'store') && !this.form.store) {
        this.form.store = this.businessStoreId === '1'
          ? '中心广场旗舰店'
          : this.businessStoreId === '2' ? '黄河路轻奢店' : ''
      }
      this.loadStoreReferenceOptions()
      this.dialogVisible = true
    },
    async handleDialogStoreChange() {
      this.form.supplier = ''
      this.form.materialName = ''
      await this.loadStoreReferenceOptions()
    },
    async loadStoreReferenceOptions() {
      if (!this.form.store) {
        this.referenceOptions = { materials: [], suppliers: [] }
        return
      }
      this.referenceOptionsLoading = true
      try {
        const response = await getInventoryStoreReferenceOptions({
          store: this.form.store,
          storeId: this.businessStoreId
        })
        this.referenceOptions = {
          materials: response.data.materials || [],
          suppliers: response.data.suppliers || []
        }
      } catch (error) {
        this.referenceOptions = { materials: [], suppliers: [] }
        this.$message.warning(error.message || '无法加载当前门店物料和供应商')
      } finally {
        this.referenceOptionsLoading = false
      }
    },
    actionFields(action) {
      if (/审核/.test(action)) {
        return [
          { key: 'auditResult', label: '审核结果', type: 'select', options: ['审核通过', '审核不通过'], required: true, verified: false },
          { key: 'auditOpinion', label: '审核意见', type: 'textarea', verified: false }
        ]
      }
      if (/出库|入库|调出|调入|盘点|报损|到货/.test(action)) {
        return [
          { key: 'operator', label: '经办人', type: 'input', verified: false },
          { key: 'operatedAt', label: '操作日期', type: 'date', verified: false },
          { key: 'remark', label: '处理说明', type: 'textarea', verified: false }
        ]
      }
      if (/付款|核销/.test(action)) {
        return [
          { key: 'amount', label: '处理金额', type: 'number', required: true, verified: false },
          { key: 'paymentAccount', label: '资金账户', type: 'input', verified: false },
          { key: 'remark', label: '处理说明', type: 'textarea', verified: false }
        ]
      }
      return []
    },
    async confirmBusinessAction() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      const missing = this.dialogFields.find(field => (
        field.required &&
        (this.form[field.key] === '' || this.form[field.key] === null ||
          this.form[field.key] === undefined ||
          (field.type === 'number' &&
            (['actualQuantity', 'safetyQuantity', 'maxQuantity'].includes(field.key)
              ? Number(this.form[field.key]) < 0
              : Number(this.form[field.key]) <= 0)))
      ))
      if (missing) {
        this.$message.warning(`请填写有效的${missing.label}`)
        return
      }
      try {
        if (this.isSaveAction(this.dialogAction)) {
          await saveInventoryModuleRecord(this.pageConfig.key, {
            ...this.form,
            recordId: this.dialogAction === '编辑' && this.selectedRow
              ? this.selectedRow.recordId
              : undefined,
            storeId: (this.selectedRow && this.selectedRow.storeId) || this.businessStoreId
          })
        } else {
          await performInventoryModuleAction(this.pageConfig.key, this.dialogAction, {
            ...this.form,
            recordId: this.selectedRow && this.selectedRow.recordId,
            storeId: (this.selectedRow && this.selectedRow.storeId) || this.businessStoreId
          })
        }
        await this.loadModuleData()
        this.$message.success(`${this.dialogAction}保存成功`)
      } catch (error) {
        this.$message.warning(error.message || '业务操作失败，请核对门店与必填字段')
      }
      this.dialogVisible = false
    },
    isCreateAction(action) {
      return /添加|新建|采购入库|设置预警值/.test(action)
    },
    isSaveAction(action) {
      return action === '编辑' || this.isCreateAction(action)
    },
    primaryAction(action) {
      return /添加|新建|采购入库|审核|出库|导入数据/.test(action)
    },
    exportCsv() {
      const header = this.pageConfig.columns.map(item => item.label)
      const lines = this.filteredRows.map(row => this.pageConfig.columns.map(item => `"${String(row[item.key] ?? '').replace(/"/g, '""')}"`).join(','))
      const blob = new Blob([`\uFEFF${[header.join(','), ...lines].join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.title}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    },
    moneyText(value) {
      return Number(value || 0).toFixed(2)
    },
    tagType(value) {
      if (/通过|完成|已付款|已导入|已处理|已结算|有库存/.test(value)) return 'success'
      if (/不通过|取消|失败|过期|负库存/.test(value)) return 'danger'
      if (/待|部分|进行|盘点中|临期|不足/.test(value)) return 'warning'
      return 'info'
    },
    noop() {}
  }
}
</script>

<style lang="scss" scoped>
.inventory-workbench {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 84px);
}
.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
  .title-row { display: flex; align-items: center; gap: 9px; }
  h2 { margin: 0; color: #25324a; font-size: 22px; }
  i { color: #5886d6; font-size: 24px; }
  p { margin: 8px 0 0; color: #738098; }
}
.evidence-alert, .action-card, .filter-card, .import-card, .table-card { margin-bottom: 14px; }
.shared-workbench-card { margin-bottom: 14px; }
.shared-workbench-title { margin-bottom: 4px; color: #606266; font-size: 13px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.action-card ::v-deep .el-button { margin: 0 8px 8px 0; }
.filter-card ::v-deep .el-form-item { margin-bottom: 10px; }
.filter-card ::v-deep .el-input { width: 190px; }
.filter-card ::v-deep .el-date-editor--daterange { width: 250px; }
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 14px;
  margin-bottom: 14px;
  span, small { display: block; color: #7b879b; }
  strong { display: block; margin: 10px 0; color: #314b75; font-size: 26px; }
}
.inventory-visual { margin: 14px 0; padding: 18px; border: 1px solid #dce8e3; border-radius: 12px; background: #fbfefc; }.inventory-copy span { color: #397a67; font-size: 12px; font-weight: 700; }.inventory-copy h3 { margin: 5px 0; color: #315e53; }.inventory-copy p { margin: 0; color: #71887f; font-size: 12px; }.inventory-stages { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px; }.inventory-stages article { position: relative; padding: 12px; border-radius: 9px; background: #fff; border-bottom: 3px solid #6fa487; }.inventory-stages article:not(:last-child)::after { position: absolute; top: 50%; left: calc(100% + 1px); width: 8px; height: 1px; background: #c2d8cc; content: ''; }.inventory-stages b { display: inline-grid; width: 21px; height: 21px; border-radius: 50%; color: #fff; background: #579373; place-items: center; font-size: 11px; }.inventory-stages strong, .inventory-stages small { display: block; }.inventory-stages strong { margin-top: 7px; color: #46685d; font-size: 13px; }.inventory-stages small { margin-top: 3px; color: #8ba098; font-size: 11px; }.inventory-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; padding-top: 12px; border-top: 1px solid #e2eee8; color: #81978e; font-size: 12px; }.inventory-transfer .inventory-stages article { border-bottom-color: #6c91ba; background: #fbfdff; }.inventory-transfer .inventory-stages b { background: #5e86b1; }.inventory-stocktake .inventory-stages article { border-bottom-color: #b68f55; background: #fffcf6; }.inventory-stocktake .inventory-stages b { background: #a57d43; }.inventory-warning .inventory-stages article { border-bottom-color: #d08061; background: #fffaf8; }.inventory-warning .inventory-stages b { background: #c67050; }
.dialog-form { margin-top: 18px; }
.dialog-form ::v-deep .el-select,
.dialog-form ::v-deep .el-date-editor,
.dialog-form ::v-deep .el-input { width: 100%; }
.confirm-copy { padding: 24px 4px 8px; color: #67748a; }
@media (max-width: 900px) {
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
  .page-heading { flex-direction: column; gap: 10px; }
}
</style>
