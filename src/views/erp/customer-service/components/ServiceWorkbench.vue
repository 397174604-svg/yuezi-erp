<template>
  <div class="service-workbench">
    <header class="page-heading">
      <div>
        <div class="eyebrow">客服管理 · {{ definition.featureCode }} · {{ definition.priority }}</div>
        <h1>{{ definition.title }}</h1>
        <p>{{ definition.description }}</p>
      </div>
      <div class="heading-actions">
        <el-button icon="el-icon-refresh" :loading="loading" @click="loadRecords">刷新</el-button>
        <el-button icon="el-icon-download" @click="exportRows">导出当前结果</el-button>
        <el-button type="primary" icon="el-icon-plus" @click="openCreate">{{ definition.createLabel }}</el-button>
      </div>
    </header>

    <section class="metric-grid">
      <div v-for="metric in metrics" :key="metric.label" class="metric-card">
        <i :class="metric.icon" :style="{ color: metric.color, background: `${metric.color}18` }" />
        <div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div>
        <small>{{ metric.note }}</small>
      </div>
    </section>

    <el-card shadow="never" class="content-card filter-card">
      <el-form inline size="small">
        <el-form-item label="门店范围">
          <el-select v-model="filters.storeId" style="width: 210px" @change="loadRecords">
            <el-option label="全部授权门店" value="all" />
            <el-option v-for="store in stores" :key="store.id" :label="store.name" :value="String(store.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="当前状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 160px">
            <el-option v-for="status in definition.statuses" :key="status" :label="status" :value="status" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-input v-model.trim="filters.keyword" clearable prefix-icon="el-icon-search" :placeholder="definition.searchPlaceholder" style="width: 300px" @keyup.enter.native="loadRecords" />
        </el-form-item>
        <el-form-item><el-button type="primary" icon="el-icon-search" @click="loadRecords">查询</el-button></el-form-item>
        <el-form-item><el-button @click="resetFilters">重置</el-button></el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="content-card table-card">
      <div slot="header" class="card-title">
        <div><b>{{ definition.listTitle }}</b><span>仅展示数据库真实记录</span></div>
        <el-tag size="small" effect="plain">共 {{ rows.length }} 条</el-tag>
      </div>
      <el-table v-loading="loading" :data="rows" stripe empty-text="暂无记录，可点击右上角新增">
        <el-table-column prop="recordNo" label="编号" min-width="158" />
        <el-table-column v-for="column in definition.columns" :key="column.prop" :prop="column.prop" :label="column.label" :min-width="column.width || 120" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-tag v-if="column.tag" :type="statusType(scope.row[column.prop])" size="mini">{{ scope.row[column.prop] || '-' }}</el-tag>
            <span v-else>{{ scope.row[column.prop] || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" prop="updatedAt" min-width="165" />
        <el-table-column label="操作" width="100" fixed="right">
          <template slot-scope="scope"><el-button type="text" @click="openDetail(scope.row)">详情/处理</el-button></template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="760px" top="5vh" @closed="resetDialog">
      <el-alert v-if="definition.integrationNotice" :title="definition.integrationNotice" type="warning" :closable="false" show-icon class="integration-alert" />
      <el-form ref="recordForm" :model="form" :rules="rules" label-width="110px">
        <el-row :gutter="18">
          <el-col v-if="definition.storeRequired || !editingId" :md="12" :xs="24">
            <el-form-item label="所属门店" prop="storeId">
              <el-select v-model="form.storeId" :disabled="Boolean(editingId)" placeholder="请选择具体门店" style="width: 100%">
                <el-option v-if="!definition.storeRequired" label="全部门店共享" value="" />
                <el-option v-for="store in stores" :key="store.id" :label="store.name" :value="String(store.id)" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col v-for="field in definition.fields" :key="field.key" :md="field.type === 'textarea' ? 24 : 12" :xs="24">
            <el-form-item :label="field.label" :prop="field.key">
              <el-select v-if="field.type === 'select'" v-model="form[field.key]" :placeholder="field.placeholder || `请选择${field.label}`" style="width: 100%">
                <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
              </el-select>
              <el-input-number v-else-if="field.type === 'number'" v-model="form[field.key]" :min="field.min || 0" :max="field.max || 100" controls-position="right" style="width: 100%" />
              <el-input v-else v-model.trim="form[field.key]" :type="field.type === 'textarea' ? 'textarea' : 'text'" :rows="field.rows || 3" :maxlength="field.maxlength || 1000" show-word-limit :placeholder="field.placeholder || `请输入${field.label}`" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div v-if="editingId" class="record-state">
        <span>当前状态</span><el-tag :type="statusType(form.status)">{{ form.status }}</el-tag>
        <span v-if="form.externalStatus && form.externalStatus !== 'NOT_REQUIRED'">外部能力：{{ externalStatusLabel }}</span>
      </div>
      <div v-if="editingId" class="log-panel">
        <h3>处理记录</h3>
        <el-timeline v-if="logs.length">
          <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="log.createdAt" placement="top">
            <b>{{ log.action }}</b><span>{{ log.beforeStatus || '-' }} → {{ log.afterStatus || '-' }}</span><p v-if="log.note">{{ log.note }}</p>
          </el-timeline-item>
        </el-timeline>
        <div v-else class="empty-state"><i class="el-icon-document" />暂无处理记录</div>
      </div>

      <span slot="footer" class="dialog-footer">
        <span v-if="editingId" class="state-actions">
          <el-button v-for="action in availableActions" :key="action.code" size="small" :type="action.type || 'default'" @click="performAction(action)">{{ action.label }}</el-button>
        </span>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord">保存资料</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getCustomerEntryOptions } from '@/api/erp-customer'
import { getServiceRecords, getServiceRecord, saveServiceRecord, performServiceAction } from '@/api/erp-customer-service'

export default {
  name: 'CustomerServiceWorkbench',
  props: { definition: { type: Object, required: true }},
  data() {
    return {
      loading: false,
      saving: false,
      rows: [],
      stores: [],
      logs: [],
      filters: { storeId: String(this.$route.query.storeId || 'all'), status: '', keyword: '' },
      dialogVisible: false,
      editingId: null,
      form: {}
    }
  },
  computed: {
    metrics() {
      return this.definition.metrics.map(metric => ({ ...metric, value: this.rows.filter(row => metric.statuses.includes(row.status)).length }))
    },
    rules() {
      const rules = {}
      if (this.definition.storeRequired) rules.storeId = [{ required: true, message: '请选择具体门店', trigger: 'change' }]
      this.definition.fields.filter(field => field.required).forEach(field => {
        rules[field.key] = [{ required: true, message: `${field.label}不能为空`, trigger: field.type === 'select' ? 'change' : 'blur' }]
      })
      if (this.definition.fields.some(field => field.key === 'mobile')) {
        rules.mobile = [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的中国大陆 11 位手机号', trigger: 'blur' }]
      }
      return rules
    },
    dialogTitle() { return this.editingId ? `${this.definition.title}详情与处理` : this.definition.createLabel },
    availableActions() { return this.definition.actions.filter(action => !action.states || action.states.includes(this.form.status)) },
    externalStatusLabel() {
      return { NOT_CONFIGURED: '通道未配置', PENDING: '待处理', SENT: '已发送', FAILED: '失败' }[this.form.externalStatus] || this.form.externalStatus
    }
  },
  watch: {
    '$route.query.storeId'(value) {
      this.filters.storeId = String(value || 'all')
      this.loadRecords()
    }
  },
  created() {
    this.loadOptions()
    this.loadRecords()
  },
  methods: {
    async loadOptions() {
      try {
        const response = await getCustomerEntryOptions()
        this.stores = response.data.stores || []
      } catch (error) {
        this.stores = []
      }
    },
    async loadRecords() {
      this.loading = true
      try {
        const response = await getServiceRecords(this.definition.featureCode, this.filters)
        this.rows = response.data.list || []
      } catch (error) {
        this.rows = []
      } finally {
        this.loading = false
      }
    },
    resetFilters() {
      this.filters = { storeId: String(this.$route.query.storeId || 'all'), status: '', keyword: '' }
      this.loadRecords()
    },
    emptyForm() {
      const next = { storeId: this.filters.storeId === 'all' ? '' : this.filters.storeId, status: '', externalStatus: '' }
      this.definition.fields.forEach(field => { next[field.key] = field.type === 'number' ? null : '' })
      return next
    },
    openCreate() {
      this.editingId = null
      this.logs = []
      this.form = this.emptyForm()
      this.dialogVisible = true
    },
    async openDetail(row) {
      this.editingId = row.id
      this.dialogVisible = true
      try {
        const response = await getServiceRecord(this.definition.featureCode, row.id)
        this.form = { ...this.emptyForm(), ...response.data.record, storeId: response.data.record.storeId ? String(response.data.record.storeId) : '' }
        this.logs = response.data.logs || []
      } catch (error) {
        this.dialogVisible = false
      }
    },
    saveRecord() {
      this.$refs.recordForm.validate(async valid => {
        if (!valid) return
        this.saving = true
        try {
          await saveServiceRecord(this.definition.featureCode, { ...this.form, id: this.editingId })
          this.$message.success('资料已保存')
          this.dialogVisible = false
          await this.loadRecords()
        } catch (error) {
          // The request layer displays the real server error; never report success here.
        } finally {
          this.saving = false
        }
      })
    },
    async performAction(action) {
      let note = ''
      if (action.requiresNote) {
        try {
          const result = await this.$prompt(action.notePrompt || '请输入处理说明', action.label, { inputType: 'textarea', inputValidator: value => Boolean(String(value || '').trim()) || '处理说明不能为空' })
          note = result.value.trim()
        } catch (error) {
          return
        }
      }
      try {
        await this.$confirm(`确认执行“${action.label}”吗？`, '操作确认', { type: action.type === 'danger' ? 'warning' : 'info' })
        await performServiceAction(this.definition.featureCode, this.editingId, action.code, { note })
        this.$message.success('状态已更新')
        await this.openDetail({ id: this.editingId })
        await this.loadRecords()
      } catch (error) {
        // Cancel and real integration errors must not be presented as success.
        if (this.dialogVisible) {
          await this.loadRecords()
          await this.openDetail({ id: this.editingId })
        }
      }
    },
    resetDialog() {
      this.editingId = null
      this.form = {}
      this.logs = []
      if (this.$refs.recordForm) this.$refs.recordForm.clearValidate()
    },
    statusType(status) {
      if (['已完成', '已发布', '已发送', '已关闭'].includes(status)) return 'success'
      if (['已升级', '发送失败', '已停用', '待通道配置'].includes(status)) return 'danger'
      if (['跟进中', '待审核', '待发送', '处理中', '等待客户'].includes(status)) return 'warning'
      return 'info'
    },
    exportRows() {
      if (!this.rows.length) return this.$message.warning('当前没有可导出的记录')
      const columns = [{ prop: 'recordNo', label: '编号' }, ...this.definition.columns, { prop: 'updatedAt', label: '更新时间' }]
      const csv = [columns.map(column => column.label).join(','), ...this.rows.map(row => columns.map(column => `"${String(row[column.prop] == null ? '' : row[column.prop]).replace(/"/g, '""')}"`).join(','))].join('\n')
      const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.definition.title}-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    }
  }
}
</script>

<style lang="scss" scoped>
.service-workbench { min-height: calc(100vh - 84px); padding: 20px; background: #f5f6f8; color: #2f2a24; }
.page-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:20px; margin-bottom:16px; }
.eyebrow { color:#a47b3d; font-size:12px; font-weight:700; letter-spacing:1px; }
h1 { margin:5px 0 6px; font-size:25px; } .page-heading p { margin:0; color:#7d8798; }
.heading-actions { display:flex; gap:8px; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-bottom:14px; }
.metric-card { display:flex; align-items:center; min-height:84px; padding:15px 18px; background:#fff; border:1px solid #ece5da; border-radius:10px; box-shadow:0 5px 18px rgba(55,45,32,.04); }
.metric-card > i { width:40px; height:40px; margin-right:12px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:19px; }
.metric-card div { display:flex; flex-direction:column; } .metric-card b { font-size:22px; } .metric-card span,.metric-card small { color:#8791a1; } .metric-card small { margin-left:auto; }
.content-card { margin-bottom:14px; border-color:#ece5da; border-radius:10px; } .filter-card ::v-deep .el-card__body { padding-bottom:2px; }
.card-title { display:flex; justify-content:space-between; align-items:center; } .card-title div { display:flex; flex-direction:column; gap:4px; } .card-title span { color:#8b95a5; font-size:12px; }
.integration-alert { margin-bottom:18px; }
.record-state { display:flex; gap:12px; align-items:center; padding:12px 14px; margin:8px 0 16px; background:#faf7f1; border-radius:8px; color:#7b6850; }
.log-panel { border-top:1px solid #eee6da; padding-top:12px; } .log-panel h3 { font-size:15px; } .log-panel span { margin-left:10px; color:#8892a2; } .log-panel p { margin:5px 0 0; color:#5f6978; }
.empty-state { padding:24px 12px; color:#9aa3af; text-align:center; background:#fafbfc; border:1px dashed #e1e5ea; border-radius:8px; }.empty-state i { margin-right:6px; }
.dialog-footer { display:flex; justify-content:flex-end; align-items:center; gap:8px; } .state-actions { margin-right:auto; display:flex; flex-wrap:wrap; gap:6px; }
@media (max-width: 1100px) { .metric-grid { grid-template-columns:repeat(2,1fr); } .page-heading { flex-direction:column; } }
</style>
