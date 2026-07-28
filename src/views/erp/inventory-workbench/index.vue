<template>
  <div class="inventory-workbench">
    <div class="page-heading">
      <div>
        <div class="title-row">
          <i :class="pageConfig.icon" />
          <h2>{{ title }}</h2>
          <el-tag size="small" type="success">{{ pageConfig.evidenceLevel }}</el-tag>
        </div>
        <p>{{ pageConfig.description }}</p>
      </div>
      <el-tag effect="plain">完成度：{{ pageConfig.completionLevel }}</el-tag>
    </div>

    <audited-surface-panel
      :config="pageConfig"
      show-action-icons
      @business-action="handleBusinessAction"
      @query-action="handleQueryAction"
    />

    <el-card v-if="pageConfig.mode === 'import'" shadow="never" class="import-card">
      <div slot="header">期初数据文件（演示）</div>
      <el-upload action="#" :auto-upload="false" :limit="1" accept=".xls,.xlsx,.csv">
        <el-button size="small" type="primary">点击选择文件</el-button>
        <div slot="tip" class="el-upload__tip">模板格式、大小限制和必填列待原系统二次核验；本地不会上传真实数据。</div>
      </el-upload>
    </el-card>

    <div v-if="pageConfig.mode === 'warning'" class="metric-grid">
      <el-card v-for="metric in warningMetrics" :key="metric.label" shadow="hover">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>脱敏演示数据</small>
      </el-card>
    </div>

    <el-card shadow="never" class="table-card">
      <div slot="header" class="card-header">
        <span>{{ title }}列表（脱敏演示）</span>
        <span>共 {{ filteredRows.length }} 条</span>
      </div>
      <el-table :data="pagedRows" border stripe size="small" highlight-current-row>
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

    <el-dialog :title="`${dialogAction}（演示）`" :visible.sync="dialogVisible" width="680px">
      <el-alert
        title="该操作仅演示表单与状态反馈，不会写入真实库存、采购、应付或审批数据。字段和校验规则待原系统二次核验。"
        type="warning"
        :closable="false"
        show-icon
      />
      <el-form v-if="dialogFields.length" :model="form" label-width="110px" class="dialog-form">
        <el-form-item v-for="field in dialogFields" :key="field.key" :label="field.label" :required="field.required">
          <el-input v-if="field.type === 'input'" v-model="form[field.key]" />
          <el-input-number v-else-if="field.type === 'number'" v-model="form[field.key]" :min="0" />
          <el-input v-else-if="field.type === 'textarea'" v-model="form[field.key]" type="textarea" :rows="3" />
          <el-select v-else-if="field.type === 'select'" v-model="form[field.key]" filterable clearable>
            <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
          </el-select>
          <el-date-picker v-else-if="field.type === 'date'" v-model="form[field.key]" type="date" value-format="yyyy-MM-dd" />
          <el-upload v-else-if="field.type === 'upload'" action="#" :auto-upload="false" :limit="1">
            <el-button size="small">点击选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <div v-else class="confirm-copy">当前动作的选择规则、校验、状态迁移及审批意见字段均待原系统二次核验。</div>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDemoAction">确认演示</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import Pagination from '@/components/Pagination'
import { getInventoryModuleData, performInventoryModuleAction, saveInventoryModuleRecord } from '@/api/erp-inventory'
import { getInventoryPageConfig } from '@/config/inventory-pages'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'

const demoWarehouses = ['五楼总库', '销售部仓库', '产康部仓库', '护理部仓库', '膳食部仓库']

export default {
  name: 'InventoryWorkbench',
  components: { AuditedSurfacePanel, Pagination },
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
      loadingResource: ''
    }
  },
  computed: {
    title() {
      return this.$route.meta && this.$route.meta.title ? this.$route.meta.title : '采购计划'
    },
    pageConfig() {
      return getInventoryPageConfig(this.title)
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
        { label: '库存不足', value: 4 },
        { label: '临期物料', value: 2 },
        { label: '库存积压', value: 1 },
        { label: '待处理', value: 5 }
      ]
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    }
  },
  methods: {
    initializePage() {
      this.filters = {}
      this.page = 1
      this.rows = []
      this.loadModuleData()
    },
    async loadModuleData() {
      const resource = this.pageConfig.key
      this.loadingResource = resource
      try {
        const response = await getInventoryModuleData(resource, this.filters)
        if (this.loadingResource === resource) {
          this.rows = response.data && Array.isArray(response.data.list)
            ? response.data.list
            : []
        }
      } catch (error) {
        // Root integration wires the independent mock into mock/index.js.
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
        auditOpinion: '脱敏演示审批意见', returnReason: '脱敏演示退货原因', damageReason: '脱敏演示报损原因',
        errorMessage: '', remark: '脱敏演示数据，字段待原系统二次核验。'
      }
    },
    handleQueryAction(action) {
      if (action === '导出') {
        this.exportCsv()
      } else if (action === '打印') {
        window.print()
      } else {
        this.page = 1
      }
    },
    handleBusinessAction(action) {
      if (action === '导出') {
        this.exportCsv()
        return
      }
      if (action === '打印') {
        window.print()
        return
      }
      this.dialogAction = action
      this.form = {}
      this.dialogFields = this.isCreateAction(action) ? this.pageConfig.formFields : this.actionFields(action)
      this.dialogVisible = true
    },
    actionFields(action) {
      if (/审核/.test(action)) {
        return [
          { key: 'auditResult', label: '审核结果', type: 'select', options: ['审核通过', '审核不通过'], verified: false },
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
    async confirmDemoAction() {
      try {
        if (this.isCreateAction(this.dialogAction)) {
          await saveInventoryModuleRecord(this.pageConfig.key, this.form)
        } else {
          await performInventoryModuleAction(this.pageConfig.key, this.dialogAction, this.form)
        }
        this.$message.success(`${this.dialogAction}演示完成，未写入真实业务数据`)
      } catch (error) {
        this.$message.warning('独立 Mock 尚待根任务接入，当前仅完成前端演示')
      }
      this.dialogVisible = false
    },
    isCreateAction(action) {
      return /添加|新建|采购入库|设置预警值/.test(action)
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
      link.download = `${this.title}-脱敏演示.csv`
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
