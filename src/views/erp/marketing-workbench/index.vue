<template>
  <div class="marketing-workbench">
    <section class="page-hero">
      <div><div class="eyebrow">营销运营 · {{ featureId }}</div><h1>{{ definition.title }}<span v-if="isP0"> ★</span></h1><p>{{ definition.description }}</p></div>
      <div class="hero-actions"><el-button icon="el-icon-download" :disabled="!filteredRows.length" @click="exportRows">导出当前结果</el-button><el-button type="primary" icon="el-icon-plus" @click="openCreate">{{ definition.primaryAction }}</el-button></div>
    </section>
    <el-alert v-if="definition.integrationNotice" type="warning" :closable="false" show-icon :title="definition.integrationNotice" class="notice" />
    <section class="metric-grid"><article v-for="metric in metricCards" :key="metric.key" class="metric-card"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></article></section>
    <el-card shadow="never" class="filter-card">
      <div slot="header" class="card-heading"><div><h2>{{ definition.eyebrow }}</h2><p>当前范围：{{ storeScopeLabel }}；每个功能使用自己的字段、状态与操作。</p></div><el-button type="text" @click="resetFilters">清空筛选</el-button></div>
      <el-form inline size="small" @submit.native.prevent="applyFilters">
        <el-form-item v-for="filter in definition.filters" :key="filter.key" :label="filter.label">
          <el-input v-if="filter.type === 'text'" v-model.trim="filters[filter.key]" clearable :placeholder="filter.placeholder" @keyup.enter.native="applyFilters" />
          <el-select v-else-if="filter.type === 'select'" v-model="filters[filter.key]" clearable :placeholder="`请选择${filter.label}`"><el-option v-for="option in filter.options" :key="option" :label="option" :value="option" /></el-select>
          <el-date-picker v-else v-model="filters[filter.key]" type="date" value-format="yyyy-MM-dd" :placeholder="`请选择${filter.label}`" />
        </el-form-item>
        <el-form-item><el-button type="primary" icon="el-icon-search" @click="applyFilters">查询</el-button></el-form-item>
      </el-form>
    </el-card>
    <el-card shadow="never" class="table-card">
      <div slot="header" class="card-heading"><div><h2>{{ definition.title }}台账</h2><p>按当前功能的业务字段和门店范围展示记录。</p></div><el-tag effect="plain">{{ filteredRows.length }} 条</el-tag></div>
      <el-table :data="filteredRows" border stripe size="small" :empty-text="definition.emptyText">
        <el-table-column type="index" label="#" width="52" />
        <el-table-column v-for="column in definition.columns" :key="column[0]" :prop="column[0]" :label="column[1]" min-width="126" show-overflow-tooltip>
          <template slot-scope="scope"><el-tag v-if="isStatusColumn(column[0])" size="mini" :type="statusType(scope.row[column[0]])">{{ displayValue(scope.row[column[0]]) }}</el-tag><span v-else>{{ displayValue(scope.row[column[0]]) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right"><template slot-scope="scope"><el-button type="text" @click="viewRecord(scope.row)">详情</el-button><el-button type="text" :disabled="!canAdvance(scope.row)" @click="advanceRecord(scope.row)">推进状态</el-button></template></el-table-column>
      </el-table>
    </el-card>
    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="640px" append-to-body>
      <el-alert v-if="viewOnly" type="info" :closable="false" title="当前为详情查看；业务状态请通过列表中的“推进状态”操作变更。" class="dialog-alert" />
      <el-form ref="recordForm" :model="form" label-width="120px">
        <el-form-item v-for="(field, index) in definition.formFields" :key="field.key" :label="field.label" :prop="field.key" :rules="index === 0 ? [{ required: true, message: `请填写${field.label}`, trigger: 'blur' }] : []">
          <el-input v-if="field.type === 'text'" v-model.trim="form[field.key]" :disabled="viewOnly" :placeholder="field.placeholder" />
          <el-select v-else-if="field.type === 'select'" v-model="form[field.key]" :disabled="viewOnly" placeholder="请选择"><el-option v-for="option in field.options" :key="option" :label="option" :value="option" /></el-select>
          <el-input-number v-else-if="field.type === 'number'" v-model="form[field.key]" :disabled="viewOnly" :min="field.min || 0" :precision="2" />
          <el-date-picker v-else v-model="form[field.key]" :disabled="viewOnly" type="date" value-format="yyyy-MM-dd" placeholder="请选择日期" />
        </el-form-item>
        <el-form-item label="当前状态"><el-tag>{{ form.status || definition.statuses[0] }}</el-tag></el-form-item><el-form-item label="发生门店"><span>{{ form.storeId || currentStoreId }}</span></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="dialogVisible = false">{{ viewOnly ? '关闭' : '取消' }}</el-button><el-button v-if="!viewOnly" type="primary" @click="saveRecord">保存内部记录</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getMarketingPageDefinition } from '@/config/marketing-pages'

export default {
  name: 'MarketingWorkbench',
  data() { return { filters: {}, appliedFilters: {}, rows: [], form: {}, dialogVisible: false, viewOnly: false } },
  computed: {
    ...mapGetters(['currentStoreId']),
    featureId() { return this.$route.meta.featureId || 'F039' },
    definition() { return getMarketingPageDefinition(this.featureId) },
    isP0() { return ['F038', 'F039', 'F041', 'F042'].includes(this.featureId) },
    storageKey() { return `erp-marketing-${this.featureId}` },
    storeScopeLabel() { return String(this.currentStoreId || 'all') === 'all' ? '全部授权门店（仅汇总查询）' : `门店 ${this.currentStoreId}` },
    dialogTitle() { return this.viewOnly ? `${this.definition.title}详情` : this.definition.primaryAction },
    statusColumnKey() {
      const column = this.definition.columns.find(([key]) => /status$/i.test(key))
      return column ? column[0] : 'status'
    },
    scopedRows() { const storeId = String(this.currentStoreId || 'all'); return storeId === 'all' ? this.rows : this.rows.filter(row => String(row.storeId) === storeId) },
    filteredRows() {
      const values = Object.entries(this.appliedFilters).filter(([, value]) => value !== '' && value != null)
      if (!values.length) return this.scopedRows
      return this.scopedRows.filter(row => values.every(([key, value]) => String(row[key] == null ? Object.values(row).join(' ') : row[key]).toLowerCase().includes(String(value).toLowerCase())))
    },
    metricCards() { return this.definition.metrics.map(([label, key], index) => ({ label, key, value: index === 0 ? this.scopedRows.length : this.scopedRows.filter(row => String(row.status || '').includes(label.replace(/^已/, ''))).length, note: index === 0 ? '当前门店范围' : '来自当前内部台账' })) }
  },
  watch: {
    featureId: {
      immediate: true,
      handler() { this.initializePage() }
    }
  },
  methods: {
    initializePage() { this.filters = Object.fromEntries(this.definition.filters.map(filter => [filter.key, ''])); this.appliedFilters = { ...this.filters }; this.rows = this.readRows(); this.dialogVisible = false },
    readRows() { try { const parsed = JSON.parse(localStorage.getItem(this.storageKey) || '[]'); return Array.isArray(parsed) ? parsed : [] } catch (_) { return [] } },
    persistRows() { localStorage.setItem(this.storageKey, JSON.stringify(this.rows)) },
    applyFilters() { this.appliedFilters = { ...this.filters } },
    resetFilters() { this.filters = Object.fromEntries(this.definition.filters.map(filter => [filter.key, ''])); this.applyFilters() },
    openCreate() {
      if (String(this.currentStoreId || 'all') === 'all') { this.$message.warning('请先在顶部选择具体门店，再创建营销业务记录'); return }
      this.form = Object.fromEntries(this.definition.formFields.map(field => [field.key, field.type === 'number' ? 0 : '']))
      this.$set(this.form, 'status', this.definition.statuses[0]); this.$set(this.form, this.statusColumnKey, this.definition.statuses[0]); this.$set(this.form, 'storeId', String(this.currentStoreId)); this.viewOnly = false; this.dialogVisible = true
      this.$nextTick(() => this.$refs.recordForm && this.$refs.recordForm.clearValidate())
    },
    saveRecord() { this.$refs.recordForm.validate(valid => { if (!valid) return; const now = new Date().toISOString(); this.rows.unshift({ ...this.form, id: `${this.definition.key}-${Date.now()}`, createdAt: now, updatedAt: now }); this.persistRows(); this.dialogVisible = false; this.$message.success('已保存内部业务记录') }) },
    viewRecord(row) { this.form = { ...row }; this.viewOnly = true; this.dialogVisible = true },
    canAdvance(row) { const index = this.definition.statuses.indexOf(row.status); return index >= 0 && index < this.definition.statuses.length - 1 },
    advanceRecord(row) { const index = this.definition.statuses.indexOf(row.status); if (index < 0 || index >= this.definition.statuses.length - 1) return; row.status = this.definition.statuses[index + 1]; row[this.statusColumnKey] = row.status; row.updatedAt = new Date().toISOString(); this.persistRows(); this.rows = [...this.rows]; this.$message.success(`状态已更新为：${row.status}`) },
    isStatusColumn(key) { return /status|stage|approval/i.test(key) },
    statusType(value) { if (/完成|发布|发放|启用|转化/.test(value || '')) return 'success'; if (/失败|驳回|拦截|过期|关闭/.test(value || '')) return 'danger'; if (/审核|待|草稿/.test(value || '')) return 'warning'; return 'info' },
    displayValue(value) { return value === '' || value == null ? '-' : value },
    exportRows() { const columns = this.definition.columns; const quote = value => `"${String(value == null ? '' : value).replace(/"/g, '""')}"`; const lines = [columns.map(column => quote(column[1])).join(',')]; this.filteredRows.forEach(row => lines.push(columns.map(column => quote(row[column[0]])).join(','))); const blob = new Blob([`\ufeff${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${this.definition.title}-${new Date().toISOString().slice(0, 10)}.csv`; link.click(); URL.revokeObjectURL(link.href) }
  }
}
</script>

<style lang="scss" scoped>
.marketing-workbench { min-height: calc(100vh - 84px); padding: 18px; background: #f3f5f8; color: #25364b; }
.page-hero { display: flex; justify-content: space-between; gap: 18px; padding: 24px 28px; margin-bottom: 14px; color: #fff; border-radius: 14px; background: linear-gradient(120deg, #33495f, #287f83); }
.page-hero h1 { margin: 5px 0 8px; font-size: 27px; }.page-hero p { max-width: 850px; margin: 0; color: rgba(255,255,255,.86); line-height: 1.7; }.eyebrow { color: #d7b77a; font-size: 12px; font-weight: 700; letter-spacing: .8px; }
.hero-actions { display: flex; align-items: flex-start; gap: 8px; white-space: nowrap; }.notice { margin-bottom: 14px; }.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }.metric-card { padding: 16px 18px; border: 1px solid #e5e9ef; border-radius: 10px; background: #fff; }.metric-card span, .metric-card small { display: block; color: #7b8794; }.metric-card strong { display: block; margin: 5px 0; color: #24465c; font-size: 26px; }
.filter-card, .table-card { margin-bottom: 14px; border: 0; border-radius: 10px; }.card-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }.card-heading h2 { margin: 0 0 4px; font-size: 16px; }.card-heading p { margin: 0; color: #8a949f; font-size: 12px; }.dialog-alert { margin-bottom: 18px; }
@media (max-width: 960px) { .metric-grid { grid-template-columns: repeat(2, 1fr); }.page-hero { flex-direction: column; } }
</style>
