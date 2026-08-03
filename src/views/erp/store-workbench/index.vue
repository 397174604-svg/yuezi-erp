<template>
  <div v-loading="loading" class="store-workbench">
    <template v-if="isStoreManagement">
      <section class="hero-panel">
        <div>
          <div class="eyebrow"><i class="el-icon-office-building" /> 门店管理 · F058</div>
          <h1>门店与渠道</h1>
          <p>维护门店基础档案、负责人和启停状态。客户、合同、房间与收款始终保留发生门店，不通过本页改写历史业务归属。</p>
        </div>
        <div class="hero-actions">
          <el-tag effect="dark" type="warning">总部配置</el-tag>
          <el-button type="primary" :disabled="!canCreate" @click="openCreate">新增门店</el-button>
        </div>
      </section>

      <el-alert class="scope-alert" type="info" :closable="false" show-icon>
        <template slot="title">当前顶部门店：{{ scopeLabel }}。全部门店用于汇总及新增筹备门店；编辑、启停已有门店时，请先在顶栏切换到对应门店。</template>
      </el-alert>

      <section class="metric-grid">
        <div v-for="metric in metrics" :key="metric.label" class="metric-card">
          <i :class="metric.icon" :style="{ color: metric.color, background: metric.color + '16' }" />
          <div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div>
        </div>
      </section>

      <el-card shadow="never" class="content-card">
        <div slot="header" class="card-heading">
          <div><h2>门店基础档案</h2><p>门店编号由系统分配；新建门店先以“筹备”状态保存，启用前须完成负责人和基础资料核对。</p></div>
          <div class="heading-actions"><el-button size="small" icon="el-icon-refresh" @click="loadStores">刷新</el-button><el-button size="small" type="primary" icon="el-icon-plus" :disabled="!canCreate" @click="openCreate">新增门店</el-button></div>
        </div>
        <el-form :inline="true" size="small" class="filter-form" @submit.native.prevent="applyFilters">
          <el-form-item label="关键词"><el-input v-model="keyword" clearable placeholder="门店名称/负责人/编号" @keyup.enter.native="applyFilters" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="statusFilter" clearable placeholder="全部状态"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" plain @click="applyFilters">查询</el-button><el-button @click="resetFilters">重置</el-button><el-button @click="exportRows">导出</el-button></el-form-item>
        </el-form>
        <el-table :data="filteredStores" border stripe size="small" class="data-table">
          <el-table-column prop="code" label="门店编号" width="120" />
          <el-table-column prop="name" label="门店名称" min-width="205" show-overflow-tooltip />
          <el-table-column prop="manager" label="负责人" min-width="110"><template slot-scope="scope">{{ scope.row.manager || '未设置' }}</template></el-table-column>
          <el-table-column prop="departments" label="部门" width="82" align="center" />
          <el-table-column prop="employees" label="在职职员" width="96" align="center" />
          <el-table-column prop="rooms" label="客房" width="76" align="center" />
          <el-table-column label="状态" width="90"><template slot-scope="scope"><el-tag size="mini" :type="scope.row.status === '启用' ? 'success' : 'info'">{{ scope.row.status }}</el-tag></template></el-table-column>
          <el-table-column fixed="right" label="操作" width="195"><template slot-scope="scope"><el-button type="text" size="small" @click="openEdit(scope.row)">编辑</el-button><el-button type="text" size="small" @click="toggleStatus(scope.row)">{{ scope.row.status === '启用' ? '停用' : '启用' }}</el-button></template></el-table-column>
        </el-table>
        <div v-if="!filteredStores.length" class="empty-state">当前范围没有匹配的门店档案。</div>
      </el-card>

      <el-card shadow="never" class="workflow-card">
        <div slot="header" class="card-heading"><div><h2>门店配置规则</h2><p>为避免跨店数据混淆，门店档案和门店业务数据采用不同的维护边界。</p></div><el-tag type="success" effect="plain">已按门店隔离</el-tag></div>
        <div class="workflow-steps"><div v-for="(step, index) in workflow" :key="step.title" class="workflow-step"><span>{{ index + 1 }}</span><div><strong>{{ step.title }}</strong><small>{{ step.detail }}</small></div></div></div>
      </el-card>

      <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="600px" @closed="resetForm">
        <el-alert v-if="editingId" type="info" :closable="false" show-icon title="保存后仅更新当前门店基础档案；历史客户、合同、房间和收款记录不会迁移。" />
        <el-alert v-else type="warning" :closable="false" show-icon title="新门店以筹备状态创建。请先配置负责人、账号权限、房型和套餐，再单独启用业务。" />
        <el-form ref="storeForm" :model="form" :rules="rules" label-width="96px" size="small" class="store-form">
          <el-form-item label="门店名称" prop="name"><el-input v-model.trim="form.name" maxlength="128" show-word-limit placeholder="请输入门店名称" /></el-form-item>
          <el-form-item label="负责人" prop="manager"><el-input v-model.trim="form.manager" maxlength="64" placeholder="请输入负责人姓名" /></el-form-item>
          <el-form-item label="经营状态"><el-radio-group v-model="form.status"><el-radio label="启用">启用</el-radio><el-radio label="停用">筹备 / 停用</el-radio></el-radio-group></el-form-item>
          <el-form-item label="配置说明"><el-input v-model.trim="form.remark" type="textarea" :rows="3" maxlength="300" show-word-limit placeholder="例如：开业计划、审批说明（仅作为审计备注）" /></el-form-item>
        </el-form>
        <span slot="footer"><el-button size="small" @click="dialogVisible = false">取消</el-button><el-button size="small" type="primary" :loading="saving" @click="saveStore">保存门店</el-button></span>
      </el-dialog>
    </template>

    <template v-else>
      <section class="hero-panel"><div><div class="eyebrow"><i class="el-icon-connection" /> 连锁经营 · F093</div><h1>连锁多门店管理</h1><p>会员主档可跨店识别；合同、收款、服务与库存始终按发生门店归属。本页只提供规则说明，归集规则须经财务与总部确认后接入。</p></div></section>
      <el-alert class="scope-alert" type="warning" :closable="false" show-icon title="资金归集、客户转店和跨门店资产迁移暂未开放写入，避免在缺少审批规则时误改业务归属。" />
      <el-card shadow="never" class="content-card"><div slot="header" class="card-heading"><div><h2>当前可用门店范围</h2><p>门店主档来自当前数据库；可在“门店与渠道”维护门店负责人和启停状态。</p></div><el-button size="small" @click="loadStores">刷新</el-button></div><el-table :data="stores" border size="small"><el-table-column prop="code" label="门店编号" width="120" /><el-table-column prop="name" label="门店名称" min-width="220" /><el-table-column prop="manager" label="负责人" min-width="120" /><el-table-column prop="status" label="状态" width="90" /></el-table></el-card>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getFoundationOverview, saveFoundationRecord } from '@/api/erp-foundation'

export default {
  name: 'StoreWorkbench',
  data() {
    return {
      loading: false,
      saving: false,
      stores: [],
      keyword: '',
      statusFilter: '',
      dialogVisible: false,
      editingId: null,
      form: { name: '', manager: '', status: '停用', remark: '' },
      rules: { name: [{ required: true, message: '请输入门店名称', trigger: 'blur' }] }
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    featureId() { return this.$route.meta && this.$route.meta.featureId },
    isStoreManagement() { return this.featureId === 'F058' || (this.$route.meta && this.$route.meta.configTitle === '门店与渠道') },
    isAggregateScope() { return !this.currentStoreId || String(this.currentStoreId) === 'all' },
    scopeLabel() {
      if (this.isAggregateScope) return '全部门店（汇总视图）'
      const selected = this.stores.find(item => String(item.id) === String(this.currentStoreId))
      return selected ? selected.name : '当前门店'
    },
    canCreate() { return this.isAggregateScope },
    dialogTitle() { return this.editingId ? '编辑门店档案' : '新增筹备门店' },
    metrics() {
      const enabled = this.stores.filter(item => item.status === '启用').length
      return [
        { label: '可见门店', value: this.stores.length, icon: 'el-icon-office-building', color: '#B8945A' },
        { label: '启用门店', value: enabled, icon: 'el-icon-circle-check', color: '#45b8ac' },
        { label: '覆盖客房', value: this.stores.reduce((total, item) => total + Number(item.rooms || 0), 0), icon: 'el-icon-house', color: '#4f8cf7' },
        { label: '在职职员', value: this.stores.reduce((total, item) => total + Number(item.employees || 0), 0), icon: 'el-icon-user', color: '#8f7cf6' }
      ]
    },
    filteredStores() {
      const keyword = this.keyword.trim().toLowerCase()
      return this.stores.filter(item => (!keyword || [item.code, item.name, item.manager].some(value => String(value || '').toLowerCase().includes(keyword))) && (!this.statusFilter || item.status === this.statusFilter))
    },
    workflow() {
      return [
        { title: '建立门店档案', detail: '总部在全部门店视图新建筹备门店，系统分配门店编号。' },
        { title: '配置人员与基础资料', detail: '分别配置负责人、员工账号、角色权限、房型和套餐。' },
        { title: '启用后发生业务', detail: '客户、合同、收款、房间和服务按门店独立记账。' }
      ]
    }
  },
  watch: {
    '$route.fullPath': { immediate: true, handler() { this.loadStores() } },
    currentStoreId() { this.loadStores() }
  },
  methods: {
    async loadStores() {
      this.loading = true
      try {
        const { data } = await getFoundationOverview({ storeId: this.currentStoreId || 'all' })
        this.stores = Array.isArray(data.stores) ? data.stores : []
      } catch (error) {
        this.stores = []
      } finally {
        this.loading = false
      }
    },
    applyFilters() { this.$message.success(`查询完成，共 ${this.filteredStores.length} 家门店`) },
    resetFilters() { this.keyword = ''; this.statusFilter = '' },
    exportRows() {
      const header = '门店编号,门店名称,负责人,部门数,在职职员,客房数,状态'
      const lines = this.filteredStores.map(item => [item.code, item.name, item.manager || '', item.departments, item.employees, item.rooms, item.status].map(value => `"${String(value == null ? '' : value).replace(/"/g, '""')}"`).join(','))
      const blob = new Blob([`\ufeff${header}\n${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = '门店基础档案.csv'
      anchor.click()
      URL.revokeObjectURL(url)
      this.$message.success('门店基础档案已导出')
    },
    openCreate() {
      if (!this.canCreate) return this.$message.warning('新增门店请先在顶栏切换至“全部门店”')
      this.editingId = null
      this.form = { name: '', manager: '', status: '停用', remark: '' }
      this.dialogVisible = true
    },
    openEdit(store) {
      if (this.isAggregateScope) return this.$message.warning('编辑门店前，请先在顶栏选择该门店')
      if (String(store.id) !== String(this.currentStoreId)) return this.$message.warning('只能维护当前顶栏选中的门店')
      this.editingId = store.id
      this.form = { name: store.name || '', manager: store.manager || '', status: store.status || '停用', remark: '' }
      this.dialogVisible = true
    },
    toggleStatus(store) {
      if (this.isAggregateScope) return this.$message.warning('启停门店前，请先在顶栏选择该门店')
      if (String(store.id) !== String(this.currentStoreId)) return this.$message.warning('只能维护当前顶栏选中的门店')
      const nextStatus = store.status === '启用' ? '停用' : '启用'
      this.$confirm(`确认将“${store.name}”调整为${nextStatus}？停用后不应再新增该门店业务。`, '确认门店状态', { type: 'warning' }).then(async() => {
        this.saving = true
        try {
          await saveFoundationRecord('stores', { id: store.id, name: store.name, manager: store.manager || '', status: nextStatus, selectedStoreId: this.currentStoreId })
          this.$message.success(`门店已${nextStatus}`)
          await this.loadStores()
        } finally { this.saving = false }
      }).catch(() => {})
    },
    saveStore() {
      this.$refs.storeForm.validate(async valid => {
        if (!valid) return
        this.saving = true
        try {
          const selectedStoreId = this.editingId ? this.currentStoreId : 'all'
          await saveFoundationRecord('stores', { ...this.form, id: this.editingId || undefined, selectedStoreId })
          this.$message.success(this.editingId ? '门店档案已保存' : '筹备门店已创建，请继续配置基础资料')
          this.dialogVisible = false
          await this.loadStores()
        } finally { this.saving = false }
      })
    },
    resetForm() { this.editingId = null; this.form = { name: '', manager: '', status: '停用', remark: '' } }
  }
}
</script>

<style lang="scss" scoped>
.store-workbench { min-height:100%; padding:20px; color:#26344a; background:#f5f6f8; }
.hero-panel { display:flex; align-items:center; justify-content:space-between; gap:24px; padding:24px 28px; color:#fff; background:linear-gradient(125deg,#37302a 0%,#6b573d 57%,#ad9468 100%); border-radius:15px; box-shadow:0 14px 34px rgba(93,70,38,.2); }
.eyebrow { margin-bottom:8px; color:#f4dfb5; font-size:13px; font-weight:700; }.hero-panel h1 { margin:0 0 8px; font-size:27px; }.hero-panel p { max-width:820px; margin:0; color:#fbf7ef; font-size:14px; line-height:1.7; }.hero-actions,.heading-actions { display:flex; align-items:center; gap:10px; }
.scope-alert { margin-top:14px; border-radius:10px; }.metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:14px; }.metric-card { display:flex; align-items:center; min-height:90px; padding:16px 18px; background:#fff; border:1px solid #e5e8ec; border-radius:11px; }.metric-card>i { display:grid; place-items:center; width:44px; height:44px; margin-right:13px; border-radius:11px; font-size:20px; }.metric-card div { display:flex; flex-direction:column; }.metric-card b { color:#3f4c59; font-size:24px; }.metric-card span { margin-top:5px; color:#7d8791; font-size:12px; }
.content-card,.workflow-card { margin-top:14px; border:0; border-radius:12px; }.card-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; }.card-heading h2 { margin:0 0 4px; font-size:16px; }.card-heading p { margin:0; color:#8b949d; font-size:12px; }.filter-form { margin-bottom:8px; }.data-table ::v-deep th { color:#495764; background:#f5f7f9; }.empty-state { padding:30px; color:#9aa4ae; text-align:center; }.store-form { margin-top:16px; }
.workflow-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }.workflow-step { display:flex; gap:10px; padding:14px; background:#f8f8f7; border-radius:9px; }.workflow-step>span { display:inline-flex; align-items:center; justify-content:center; flex:0 0 25px; width:25px; height:25px; color:#fff; background:#a58455; border-radius:50%; font-size:12px; }.workflow-step strong,.workflow-step small { display:block; }.workflow-step strong { color:#4b565f; font-size:13px; }.workflow-step small { margin-top:5px; color:#8d979e; font-size:11px; line-height:1.5; }
@media (max-width:1000px) { .metric-grid { grid-template-columns:repeat(2,1fr); }.hero-panel { align-items:flex-start; flex-direction:column; }.workflow-steps { grid-template-columns:1fr; } } @media (max-width:700px) { .store-workbench { padding:12px; }.metric-grid { grid-template-columns:1fr; }.card-heading,.heading-actions { align-items:flex-start; flex-direction:column; } }
</style>
