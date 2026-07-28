<template>
  <div class="rehab-workbench">
    <service-overview-query v-if="isServiceOverview" />

    <template v-else>
      <audited-surface-panel
        :config="permissionConfig"
        plain
        show-action-icons
        @business-action="handleAction"
        @query-action="handleAuditedQueryAction"
      />

      <el-card shadow="never" class="content-card table-card">
        <el-table
          v-loading="loading"
          :data="pagedRows"
          border
          stripe
          height="540"
          highlight-current-row
          @selection-change="selection = $event"
          @row-dblclick="openDetails"
        >
          <el-table-column type="selection" width="45" fixed="left" />
          <el-table-column type="index" label="序号" width="58" fixed="left" :index="tableIndex" />
          <el-table-column
            v-for="column in config.columns"
            :key="column.key"
            :prop="column.key"
            :label="column.label"
            :min-width="column.width || 110"
            show-overflow-tooltip
          >
            <template slot-scope="scope">
              <el-tag v-if="column.tag" size="mini" :type="tagType(scope.row[column.key])">{{ scope.row[column.key] }}</el-tag>
              <span v-else>{{ scope.row[column.key] }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openDetails(scope.row)">详情</el-button>
              <el-button v-if="canAction('编辑')" type="text" @click="openEdit(scope.row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-row">
          <span>显示第 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
          <el-pagination
            background
            layout="prev, pager, next, sizes"
            :current-page.sync="pagination.page"
            :page-size.sync="pagination.size"
            :page-sizes="[10, 20, 50]"
            :total="filteredRows.length"
          />
        </div>
      </el-card>

      <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="780px" top="6vh" :close-on-click-modal="false">
        <el-form :model="dialogForm" label-position="top" class="dialog-form">
          <el-row :gutter="18">
            <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
              <el-form-item :label="field.label" :required="field.required">
                <field-control :field="field" :model="dialogForm" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        <div slot="footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitDialog">确认</el-button>
        </div>
      </el-dialog>

      <el-drawer title="产康业务详情" :visible.sync="drawerVisible" size="580px">
        <div v-if="currentRow" class="detail-drawer">
          <div class="detail-head">
            <strong>{{ recordName(currentRow) }}</strong>
          </div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item v-for="column in config.columns" :key="column.key" :label="column.label">
              {{ currentRow[column.key] }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-drawer>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getRehabPageConfig } from '@/config/rehab-pages'
import { canUseRecoveryAction, visibleRecoveryActions } from '@/config/rehab-permissions'
import { getRehabModuleData, getRehabOptions, performRehabModuleAction, saveRehabModuleRecord } from '@/api/erp-rehab'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'
import ServiceOverviewQuery from './ServiceOverviewQuery'

const FieldControl = {
  name: 'FieldControl',
  props: {
    field: { type: Object, required: true },
    model: { type: Object, required: true }
  },
  render(h) {
    const field = this.field
    const value = this.model[field.key]
    const setValue = next => this.$set(this.model, field.key, next)
    if (field.type === 'select') {
      return h('el-select', {
        class: 'full-control',
        props: { value, clearable: true, filterable: true, placeholder: '请选择' },
        on: { input: setValue }
      }, field.options.map(option => h('el-option', { key: option, props: { label: option, value: option }})))
    }
    if (field.type === 'date' || field.type === 'dateRange') {
      const isRange = field.type === 'dateRange'
      return h('el-date-picker', {
        class: 'full-control',
        props: {
          value,
          type: isRange ? 'daterange' : 'date',
          valueFormat: 'yyyy-MM-dd',
          startPlaceholder: '开始日期',
          endPlaceholder: '结束日期',
          rangeSeparator: '至',
          placeholder: `请选择${field.label}`
        },
        on: { input: setValue }
      })
    }
    if (field.type === 'number') {
      return h('el-input-number', {
        class: 'full-control',
        props: { value: Number(value || 0), min: 0, controlsPosition: 'right' },
        on: { input: setValue }
      })
    }
    if (field.type === 'textarea') {
      return h('el-input', {
        props: { value, type: 'textarea', rows: 3, placeholder: `请输入${field.label}` },
        on: { input: setValue }
      })
    }
    return h('el-input', {
      props: { value, clearable: true, placeholder: `请输入${field.label}` },
      on: { input: setValue }
    })
  }
}

export default {
  name: 'RehabWorkbench',
  components: { AuditedSurfacePanel, FieldControl, ServiceOverviewQuery },
  data() {
    return {
      loading: false,
      saving: false,
      rows: [],
      filters: {},
      selection: [],
      pagination: { page: 1, size: 10 },
      currentRow: null,
      drawerVisible: false,
      dialogVisible: false,
      dialogTitle: '',
      dialogAction: '',
      dialogFields: [],
      dialogForm: {},
      recoveryOptions: {
        stores: [],
        customers: [],
        staff: []
      }
    }
  },
  computed: {
    ...mapGetters(['permissions', 'roles']),
    pageTitle() {
      return this.$route.meta.title
    },
    config() {
      return getRehabPageConfig(this.pageTitle)
    },
    isServiceOverview() {
      return this.pageTitle === '服务综合查询'
    },
    permissionConfig() {
      return {
        ...this.config,
        actions: visibleRecoveryActions(
          this.config.key,
          this.config.actions,
          this.permissions,
          this.roles
        )
      }
    },
    filteredRows() {
      return this.rows
    },
    pagedRows() {
      const start = (this.pagination.page - 1) * this.pagination.size
      return this.filteredRows.slice(start, start + this.pagination.size)
    },
    pageStart() {
      return this.filteredRows.length ? (this.pagination.page - 1) * this.pagination.size + 1 : 0
    },
    pageEnd() {
      return Math.min(this.pagination.page * this.pagination.size, this.filteredRows.length)
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
      this.pagination.page = 1
      this.selection = []
      this.resetFilters()
      if (!this.isServiceOverview) {
        this.loadOptions()
        this.loadData()
      }
    },
    async loadOptions() {
      try {
        const response = await getRehabOptions()
        this.recoveryOptions = {
          stores: response.data.stores || [],
          customers: response.data.customers || [],
          staff: response.data.staff || []
        }
      } catch (error) {
        this.recoveryOptions = { stores: [], customers: [], staff: [] }
      }
    },
    async loadData() {
      this.loading = true
      try {
        const response = await getRehabModuleData(this.config.key, this.filters)
        const list = response.data && response.data.list
        this.rows = Array.isArray(list) ? list : []
      } catch (error) {
        this.rows = []
      } finally {
        this.loading = false
      }
    },
    resetFilters() {
      this.filters = {}
      this.pagination.page = 1
    },
    normalizeAuditedFilters(model) {
      const result = {}
      const labelMap = [
        [/客户姓名|客户名称/, 'customerName'],
        [/手机号|联系电话|手机号码/, 'mobile'],
        [/项目名称|服务项目/, 'serviceItem'],
        [/服务人|服务人员|技师|产康师/, 'technician'],
        [/所属分店|预约分店|分店名称|门店类别|服务门店|评估门店|门店/, 'store'],
        [/客户状态/, 'customerStatus'],
        [/服务状态/, 'serviceStatus'],
        [/任务状态/, 'taskStatus'],
        [/排班状态/, 'shiftStatus'],
        [/评估类型/, 'assessmentType'],
        [/物料名称/, 'materialName'],
        [/剩余次数/, 'remainingMax']
      ]
      this.config.filters.forEach(field => {
        const value = model[field.key]
        if (value === '' || value === null || value === undefined || (Array.isArray(value) && !value.length)) return
        const matched = labelMap.find(([pattern]) => pattern.test(field.label || ''))
        if (matched) result[matched[1]] = value
      })
      return result
    },
    search(model = {}) {
      this.filters = this.normalizeAuditedFilters(model)
      this.pagination.page = 1
      this.loadData()
    },
    handleAuditedQueryAction(action, model) {
      if (/查询|搜索/.test(String(action).replace(/\s+/g, ''))) this.search(model)
      if (/重置/.test(action)) {
        this.resetFilters()
        this.loadData()
      }
      if (/打印/.test(action)) window.print()
      if (/导出/.test(action)) this.exportRows()
    },
    canAction(action) {
      return canUseRecoveryAction(
        this.config.key,
        action,
        this.permissions,
        this.roles
      )
    },
    handleAction(action) {
      if (action === '导出') return this.exportRows()
      if (action === '打印') return window.print()
      if (action === '查看详情') {
        const row = this.requireOne()
        if (row) this.openDetails(row)
        return
      }
      if (/删除|取消/.test(action)) {
        const row = this.requireOne()
        if (!row) return
        this.$confirm(`确定要${action}当前记录吗？`, '操作确认', {
          type: 'warning'
        }).then(() => this.executeAction(action, row)).catch(() => {})
        return
      }
      if (/添加|服务预约/.test(action)) {
        return this.openDialog(
          action,
          this.config.formFields || this.defaultActionFields(action)
        )
      }
      if (action === '编辑') {
        const row = this.requireOne()
        if (row) this.openEdit(row)
        return
      }
      if (action === '设置' || action === '批量修改') {
        const row = this.requireOne()
        if (row) this.openDialog(action, this.defaultActionFields(action), row)
        return
      }
      if (/确认完成|预约确认|审核|反审核/.test(action)) {
        const row = this.requireOne()
        if (!row) return
        if (action === '确认完成') {
          return this.openDialog(
            action,
            this.config.completionFields || this.defaultActionFields(action),
            row
          )
        }
        return this.executeAction(action, row)
      }
      this.$message.info(`${action}不产生数据变更`)
    },
    openEdit(row) {
      if (!this.canAction('编辑')) return
      const fields = this.config.formFields || this.config.completionFields || []
      if (!fields.length) return this.openDetails(row)
      this.openDialog('编辑', fields, row)
    },
    defaultActionFields(action) {
      if (action === '设置' || action === '批量修改') {
        return [{ key: 'technician', label: '服务人员', type: 'select', required: true, options: [] }]
      }
      if (action === '确认完成') {
        return [
          { key: 'serviceDate', label: '服务日期', type: 'date', required: true },
          { key: 'servicePeriod', label: '服务时段', type: 'input', required: true },
          { key: 'technician', label: '执行人员', type: 'select', required: true, options: [] },
          { key: 'usedCount', label: '本次耗卡次数', type: 'number', required: true },
          { key: 'serviceResult', label: '服务结果', type: 'textarea', required: true },
          { key: 'customerFeedback', label: '客户反馈', type: 'textarea' }
        ]
      }
      if (action === '添加') {
        return [
          { key: 'customerName', label: '客户姓名', type: 'select', required: true, options: [] },
          { key: 'store', label: '服务门店', type: 'select', required: true, options: [] },
          { key: 'serviceItem', label: '服务项目', type: 'input', required: true },
          { key: 'technician', label: '服务人员', type: 'select', required: true, options: [] },
          { key: 'appointmentDate', label: '预约日期', type: 'date', required: true },
          { key: 'appointmentPeriod', label: '预约时段', type: 'input', required: true },
          { key: 'serviceCount', label: '服务次数', type: 'number', required: true },
          { key: 'remark', label: '备注', type: 'textarea' }
        ]
      }
      return []
    },
    prepareDialogFields(fields) {
      const stores = this.recoveryOptions.stores.map(item => item.name)
      const customers = this.recoveryOptions.customers.map(item => item.name)
      const staff = this.recoveryOptions.staff.map(item => item.name)
      return fields.map(field => {
        const next = { ...field }
        if (field.key === 'store') {
          next.type = 'select'
          next.options = stores
        }
        if (field.key === 'customerName') {
          next.type = 'select'
          next.options = customers
        }
        if (['technician', 'staffName', 'assessor'].includes(field.key)) {
          next.type = 'select'
          next.options = staff
        }
        return next
      })
    },
    openDialog(action, fields, row) {
      if (!fields.length) return this.$message.info('当前操作没有可填写字段')
      this.dialogTitle = action
      this.dialogAction = action
      this.dialogFields = this.prepareDialogFields(fields)
      this.currentRow = row || null
      this.dialogForm = {}
      this.dialogFields.forEach(field => {
        let value = row && row[field.key] !== undefined ? row[field.key] : ''
        if (row && action === '确认完成') {
          if (field.key === 'serviceDate') value = row.appointmentDate || ''
          if (field.key === 'servicePeriod') value = row.appointmentPeriod || row.timePeriod || ''
          if (field.key === 'usedCount') value = row.serviceCount || 1
        }
        if (!row && field.type === 'number') value = ['serviceCount', 'usedCount'].includes(field.key) ? 1 : 0
        this.$set(this.dialogForm, field.key, value)
      })
      this.dialogVisible = true
    },
    async submitDialog() {
      const missing = this.dialogFields.filter(field => field.required && !this.dialogForm[field.key])
      if (missing.length) return this.$message.warning(`请填写：${missing.map(field => field.label).join('、')}`)
      this.saving = true
      try {
        if (['编辑', '添加', '服务预约'].includes(this.dialogAction)) {
          await saveRehabModuleRecord(this.config.key, { id: this.currentRow && this.currentRow.id, ...this.dialogForm })
        } else {
          await performRehabModuleAction(this.config.key, this.dialogAction, { id: this.currentRow && this.currentRow.id, ...this.dialogForm })
        }
        this.dialogVisible = false
        this.$message.success(`${this.dialogAction}成功`)
        await this.loadData()
      } finally {
        this.saving = false
      }
    },
    async executeAction(action, row) {
      await performRehabModuleAction(this.config.key, action, { id: row.id })
      this.$message.success(`${action}成功`)
      await this.loadData()
    },
    requireOne() {
      const row = this.selection[0]
      if (!row) this.$message.warning('请先选择一条产康业务记录')
      return row
    },
    openDetails(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    exportRows() {
      const headers = this.config.columns.map(column => column.label)
      const body = this.filteredRows.map(row => this.config.columns.map(column => `"${String(row[column.key] == null ? '' : row[column.key]).replace(/"/g, '""')}"`).join(','))
      const csv = `\uFEFF${headers.join(',')}\n${body.join('\n')}`
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${this.filteredRows.length} 条记录`)
    },
    recordName(row) {
      return row.appointmentNo || row.recordNo || row.documentNo || row.assessmentNo || row.customerName || row.id
    },
    actionIcon(action) {
      if (/添加|预约/.test(action)) return 'el-icon-plus'
      if (/编辑|设置/.test(action)) return 'el-icon-edit'
      if (/删除/.test(action)) return 'el-icon-delete'
      if (/导出/.test(action)) return 'el-icon-download'
      if (/打印/.test(action)) return 'el-icon-printer'
      if (/完成|确认/.test(action)) return 'el-icon-circle-check'
      if (/开始/.test(action)) return 'el-icon-video-play'
      if (/取消/.test(action)) return 'el-icon-close'
      return 'el-icon-setting'
    },
    tagType(value) {
      if (/完成|出勤|已扣减/.test(value)) return 'success'
      if (/取消|停诊/.test(value)) return 'danger'
      if (/待|请假|休息/.test(value)) return 'warning'
      return 'primary'
    },
    tableIndex(index) {
      return (this.pagination.page - 1) * this.pagination.size + index + 1
    }
  }
}
</script>

<style lang="scss" scoped>
.rehab-workbench { min-height: calc(100vh - 84px); padding: 22px; color: #26354c; background: #f5f4f8; }
.hero-panel { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 25px 30px; border-radius: 16px; color: white; background: linear-gradient(125deg, #763553 0%, #b64f7a 52%, #e77da4 100%); box-shadow: 0 14px 34px rgba(151, 59, 96, .23); }
.eyebrow { margin-bottom: 9px; color: #ffe3ee; font-size: 13px; font-weight: 700; letter-spacing: .7px; }
.hero-panel h1 { margin: 0 0 8px; font-size: 27px; }
.hero-panel p { max-width: 760px; margin: 0; color: #ffe9f1; font-size: 14px; line-height: 1.7; }
.hero-status { display: flex; flex: 0 0 auto; align-items: center; gap: 10px; }
.evidence-alert { margin-top: 14px; border-radius: 10px; }
.content-card { margin-top: 16px; border: 0; border-radius: 12px; }
.action-card ::v-deep .el-card__body { padding: 14px 18px; }
.toolbar, .card-heading, .pagination-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.toolbar > span { flex: 0 0 auto; color: #8290a3; font-size: 12px; }
.business-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.business-actions .el-button + .el-button { margin-left: 0; }
.card-heading h2 { margin: 0 0 4px; font-size: 16px; }
.card-heading p { margin: 0; color: #8a97a8; font-size: 12px; }
.filter-form { margin-bottom: -12px; }
.filter-form ::v-deep .el-form-item { margin-bottom: 16px; }
.filter-form ::v-deep .el-form-item__label, .dialog-form ::v-deep .el-form-item__label { padding-bottom: 5px; color: #607087; font-size: 12px; line-height: 18px; }
.full-control { width: 100%; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 16px; }
.summary-card { display: flex; align-items: center; gap: 15px; padding: 18px 20px; border: 1px solid #eee6eb; border-radius: 12px; background: white; }
.summary-card > i { display: grid; width: 42px; height: 42px; border-radius: 12px; color: #b64f7a; background: #fce9f1; font-size: 20px; place-items: center; }
.summary-card strong, .summary-card span { display: block; }
.summary-card strong { color: #9b3f66; font-size: 23px; }
.summary-card span { margin-top: 3px; color: #7d8999; font-size: 12px; }
.week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; overflow-x: auto; }
.day-card { min-width: 112px; padding: 14px; border: 1px solid #ebe7eb; border-radius: 10px; background: #fbfafb; }
.day-card.today { border-color: #d96e99; background: #fff4f8; }
.day-card span, .day-card strong, .day-card small, .day-card em { display: block; }
.day-card span { color: #6c788a; font-size: 12px; }
.day-card strong { margin: 5px 0 8px; color: #9b3f66; font-size: 18px; }
.day-card small { margin-bottom: 9px; color: #7d8999; }
.day-card em { margin-top: 7px; color: #8b6576; font-size: 11px; font-style: normal; }
.table-card ::v-deep .el-card__body { padding-top: 14px; }
.table-card ::v-deep .el-table th { color: #43536a; background: #fbf5f8; }
.pagination-row { padding-top: 18px; color: #8491a2; font-size: 12px; }
.dialog-alert { margin-bottom: 18px; }
.dialog-form { max-height: 56vh; padding-right: 12px; overflow-y: auto; }
.detail-drawer { padding: 0 22px 30px; }
.detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; font-size: 18px; }
.detail-drawer h3 { margin: 26px 0 14px; font-size: 15px; }
@media (max-width: 900px) {
  .rehab-workbench { padding: 12px; }
  .hero-panel, .hero-status, .toolbar, .pagination-row { align-items: flex-start; flex-direction: column; }
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
