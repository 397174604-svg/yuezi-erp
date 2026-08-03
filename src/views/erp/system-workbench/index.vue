<template>
  <div class="system-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i class="el-icon-setting" /> 系统设置 · {{ pageConfig.featureId || '系统配置' }}</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageConfig.description }}</p>
      </div>
      <div class="hero-actions">
        <el-tag type="success" effect="dark">{{ isSystemSettings ? '后台配置入口' : '权限控制已启用' }}</el-tag>
        <template v-if="isSystemSettings">
          <el-button type="primary" @click="goTo('/people/item-6')">员工账号</el-button>
          <el-button @click="goTo('/people/item-7')">角色权限</el-button>
        </template>
        <el-button v-else type="primary" @click="openCreate">{{ pageConfig.primaryAction }}</el-button>
      </div>
    </section>

    <template v-if="isSystemSettings">
      <el-alert class="scope-alert" type="info" :closable="false" show-icon title="系统设置用于维护账号、角色权限、门店档案和基础资料。业务新增会自动继承顶部当前门店；选择“全部门店”时仅允许汇总查询。" />
      <section class="settings-entry-grid">
        <button v-for="entry in settingsEntries" :key="entry.title" type="button" class="settings-entry" @click="goTo(entry.path)">
          <span class="settings-entry__icon"><i :class="entry.icon" /></span>
          <span class="settings-entry__body"><b>{{ entry.title }}</b><small>{{ entry.description }}</small></span>
          <i class="el-icon-arrow-right" />
        </button>
      </section>
      <el-card shadow="never" class="content-card settings-guide-card">
        <div slot="header" class="card-heading"><div><h2>后台配置使用顺序</h2><p>先维护人员与权限，再维护门店与基础资料；避免以无业务含义的参数干扰真实单据。</p></div><el-tag type="warning" effect="plain">管理员操作</el-tag></div>
        <div class="settings-guide">
          <div><span>1</span><b>员工账号</b><small>关联职员、默认门店和登录角色。</small></div>
          <div><span>2</span><b>角色权限</b><small>配置菜单、操作和数据范围。</small></div>
          <div><span>3</span><b>门店与渠道</b><small>维护门店档案、负责人及启停状态。</small></div>
          <div><span>4</span><b>审批中心</b><small>查看合同、收款和业务审批待办。</small></div>
        </div>
      </el-card>
      <el-collapse v-model="advancedPanels" class="advanced-settings">
        <el-collapse-item title="高级系统参数（仅兼容已有配置）" name="advanced">
          <p>时区、会员跨店查询和门店业务隔离由系统维护。非必要情况下无需新增参数；如需变更，请先确认影响门店和生效时间。</p>
          <div class="advanced-rows"><el-tag>默认门店时区：Asia/Shanghai</el-tag><el-tag type="success">会员跨店查询：开启</el-tag><el-tag type="warning">门店业务隔离：强制</el-tag></div>
        </el-collapse-item>
      </el-collapse>
    </template>

    <template v-else>
    <el-alert class="scope-alert" type="info" :closable="false" show-icon :title="pageConfig.scopeHint" />

    <section class="metric-grid">
      <div v-for="metric in pageConfig.metrics" :key="metric.label" class="metric-card"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small :class="metric.tone">{{ metric.note }}</small></div>
    </section>

    <el-card shadow="never" class="content-card">
      <div slot="header" class="card-heading">
        <div><h2>{{ pageConfig.sectionTitle }}</h2><p>{{ pageConfig.sectionHint }}</p></div>
        <div class="heading-actions"><el-button size="small" @click="runSecondaryAction">{{ pageConfig.secondaryAction }}</el-button><el-button size="small" type="primary" @click="openCreate">{{ pageConfig.primaryAction }}</el-button></div>
      </div>
      <el-form :inline="true" size="small" class="filter-form" @submit.native.prevent="applyFilters">
        <el-form-item label="关键词"><el-input v-model="keyword" clearable placeholder="名称/编码" @keyup.enter.native="applyFilters" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="statusFilter" clearable placeholder="全部状态"><el-option v-for="status in pageConfig.statuses" :key="status" :label="status" :value="status" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" plain @click="applyFilters">查询</el-button><el-button @click="resetFilters">重置</el-button></el-form-item>
      </el-form>
      <el-table :data="filteredRows" border stripe size="small" class="data-table">
        <el-table-column v-for="column in pageConfig.columns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 120" show-overflow-tooltip>
          <template slot-scope="scope"><el-tag v-if="column.format === 'status'" size="mini" :type="statusType(scope.row[column.key])">{{ scope.row[column.key] }}</el-tag><span v-else>{{ scope.row[column.key] }}</span></template>
        </el-table-column>
        <el-table-column fixed="right" label="操作" width="220">
          <template slot-scope="scope"><el-button type="text" size="small" @click="openEdit(scope.row)">{{ pageConfig.editAction }}</el-button><el-button type="text" size="small" @click="handleRowAction(scope.row)">{{ pageConfig.rowAction }}</el-button><el-button type="text" size="small" @click="toggleRow(scope.row)">{{ pageConfig.toggleAction }}</el-button></template>
        </el-table-column>
      </el-table>
      <div v-if="!filteredRows.length" class="empty-state">没有匹配记录，请调整查询条件。</div>
    </el-card>

    <el-card shadow="never" class="workflow-card">
      <div slot="header" class="card-heading"><div><h2>{{ pageConfig.workflowTitle }}</h2><p>{{ pageConfig.workflowHint }}</p></div><el-tag type="warning" effect="plain">业务闭环</el-tag></div>
      <div class="workflow-steps"><div v-for="(step, index) in pageConfig.workflow" :key="step.title" class="workflow-step"><span>{{ index + 1 }}</span><div><strong>{{ step.title }}</strong><small>{{ step.detail }}</small></div></div></div>
    </el-card>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="640px" @closed="resetForm">
      <el-form ref="systemForm" :model="form" :rules="rules" label-width="118px" size="small">
        <el-form-item v-for="field in pageConfig.formFields" :key="field.key" :label="field.label" :prop="field.key">
          <el-input v-if="field.type === 'input' || field.type === 'textarea'" v-model="form[field.key]" :type="field.type === 'textarea' ? 'textarea' : 'text'" :rows="field.type === 'textarea' ? 3 : 1" :placeholder="`请输入${field.label}`" />
          <el-input-number v-else-if="field.type === 'number'" v-model="form[field.key]" :min="0" controls-position="right" />
          <el-switch v-else-if="field.type === 'switch'" v-model="form[field.key]" active-text="启用" inactive-text="停用" />
          <el-date-picker v-else-if="field.type === 'date'" v-model="form[field.key]" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" />
          <el-select v-else v-model="form[field.key]" class="full-control" :placeholder="`请选择${field.label}`"><el-option v-for="option in field.options || []" :key="option.value || option" :label="option.label || option" :value="option.value || option" /></el-select>
        </el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="dialogVisible = false">取消</el-button><el-button size="small" type="primary" @click="saveRecord">保存并生效</el-button></span>
    </el-dialog>
    </template>
  </div>
</template>

<script>
import { getSystemPageConfig } from '@/config/system-pages'

const option = (value, label = value) => ({ value, label })
const commonStores = [option('全部门店'), option('上海静安店'), option('杭州西湖店'), option('深圳南山店')]
const selectField = (key, label, options) => ({ key, label, type: 'select', options })
const inputField = (key, label, type = 'input') => ({ key, label, type })

const pageOverrides = {
  系统设置: {
    featureId: 'F061', mode: 'settings', description: '集中维护租户、门店、权限和业务默认参数，修改需记录操作者并按生效范围发布。', scopeHint: '系统级参数由总部维护；门店级参数只能作用于选定门店，不会覆盖其他门店配置。', primaryAction: '新增参数', secondaryAction: '导出配置', editAction: '编辑', rowAction: '查看变更', toggleAction: '启用/停用', sectionTitle: '系统参数与生效范围', sectionHint: '每条参数明确数据类型、作用范围、当前值和最近变更。', statuses: ['启用', '停用', '待发布'], metrics: [{ label: '参数总数', value: '86', note: '全局+门店', tone: 'info' }, { label: '待发布', value: '4', note: '需管理员确认', tone: 'warn' }, { label: '本月变更', value: '18', note: '全量留痕', tone: 'good' }, { label: '异常配置', value: '0', note: '校验通过', tone: 'good' }], columns: [{ key: 'code', label: '参数编码', width: 140 }, { key: 'name', label: '参数名称', width: 180 }, { key: 'scope', label: '生效范围', width: 120 }, { key: 'value', label: '当前值', width: 150 }, { key: 'updatedBy', label: '更新人', width: 100 }, { key: 'updatedAt', label: '更新时间', width: 145 }, { key: 'status', label: '状态', format: 'status', width: 85 }], formFields: [inputField('code', '参数编码'), inputField('name', '参数名称'), selectField('scope', '生效范围', commonStores), inputField('value', '参数值'), selectField('status', '状态', [option('启用'), option('停用'), option('待发布')])], workflowTitle: '参数发布闭环', workflowHint: '保存后先校验数据类型和作用范围，再发布到对应门店。', workflow: [{ title: '配置参数', detail: '填写键值和生效范围' }, { title: '校验变更', detail: '检查冲突与权限' }, { title: '发布生效', detail: '写入版本并记录日志' }]
  },
  历史数据迁移工具: {
    featureId: 'F079', mode: 'migration', description: '按批次导入历史会员、订单和资产索引，支持预检、失败重试与回滚标记。', scopeHint: '迁移任务由总部发起；目标门店和数据类型必须明确，原始数据只读留存。', primaryAction: '新建迁移批次', secondaryAction: '下载模板', editAction: '查看批次', rowAction: '预检/重试', toggleAction: '暂停/继续', sectionTitle: '迁移批次与校验结果', sectionHint: '批次按数据类型执行，预检通过后才能导入。', statuses: ['待预检', '导入中', '已完成', '有失败'], metrics: [{ label: '批次总数', value: '12', note: '今年累计', tone: 'info' }, { label: '待预检', value: '2', note: '不可直接导入', tone: 'warn' }, { label: '成功记录', value: '48,236', note: '已校验', tone: 'good' }, { label: '失败记录', value: '36', note: '待重试', tone: 'bad' }], columns: [{ key: 'batchNo', label: '批次号', width: 145 }, { key: 'dataType', label: '数据类型', width: 120 }, { key: 'targetStore', label: '目标门店', width: 130 }, { key: 'total', label: '总记录', width: 90 }, { key: 'success', label: '成功', width: 90 }, { key: 'failed', label: '失败', width: 90 }, { key: 'status', label: '批次状态', format: 'status', width: 90 }], formFields: [inputField('batchNo', '批次名称'), selectField('dataType', '数据类型', [option('会员主档'), option('历史订单'), option('资产余额')]), selectField('targetStore', '目标门店', commonStores), inputField('fileName', '导入文件')], workflowTitle: '迁移批次闭环', workflowHint: '预检、导入、失败重试和结果确认均在同一批次内完成。', workflow: [{ title: '上传预检', detail: '校验字段、编码和重复项' }, { title: '分批导入', detail: '失败记录隔离，不影响成功项' }, { title: '结果确认', detail: '下载结果并标记可回滚' }]
  },
  '品牌定制（Logo/主题色/专属域名）': {
    featureId: 'F098', mode: 'branding', description: '管理品牌 Logo、主题色和专属域名，支持总部默认值与门店覆盖值分层生效。', scopeHint: '品牌配置按租户和门店范围生效；发布前提供预览，发布后保留版本和回滚入口。', primaryAction: '新建品牌版本', secondaryAction: '预览当前主题', editAction: '编辑版本', rowAction: '预览/发布', toggleAction: '发布/回滚', sectionTitle: '品牌版本与发布记录', sectionHint: '每个版本包含视觉资产、域名配置和适用范围。', statuses: ['草稿', '待发布', '已发布', '已回滚'], metrics: [{ label: '版本总数', value: '8', note: '可回滚', tone: 'info' }, { label: '待发布', value: '1', note: '需预览', tone: 'warn' }, { label: '生效门店', value: '6', note: '当前版本', tone: 'good' }, { label: '域名状态', value: '正常', note: '证书有效', tone: 'good' }], columns: [{ key: 'version', label: '版本号', width: 90 }, { key: 'themeName', label: '主题名称', width: 170 }, { key: 'scope', label: '适用范围', width: 130 }, { key: 'domain', label: '专属域名', width: 190 }, { key: 'publisher', label: '发布人', width: 100 }, { key: 'updatedAt', label: '更新时间', width: 145 }, { key: 'status', label: '发布状态', format: 'status', width: 90 }], formFields: [inputField('version', '版本名称'), inputField('themeName', '主题名称'), selectField('scope', '适用范围', commonStores), inputField('domain', '专属域名'), selectField('status', '发布状态', [option('草稿'), option('待发布')])], workflowTitle: '品牌发布闭环', workflowHint: '保存草稿后先预览，再发布到选定范围；新版本异常可回滚。', workflow: [{ title: '编辑主题', detail: 'Logo、颜色和域名配置' }, { title: '预览校验', detail: '检查桌面端与移动端效果' }, { title: '发布/回滚', detail: '按范围生效并保留版本' }]
  }
}

// Product-menu titles remove parenthetical detail. Keep the enhanced brand
// workbench reachable from both the registry title and its visible short title.
pageOverrides.品牌定制 = pageOverrides['品牌定制（Logo/主题色/专属域名）']

export default {
  name: 'SystemWorkbench',
  data() { return { keyword: '', statusFilter: '', rows: [], dialogVisible: false, editingId: '', form: {}, rules: {}, advancedPanels: [] } },
  computed: {
    pageTitle() { return this.$route.meta.configTitle || this.$route.meta.title.replace(/\s*★$/, '') },
    isSystemSettings() { return this.pageTitle === '系统设置' },
    settingsEntries() {
      return [
        { title: '员工账号', description: '维护登录账号、职员、默认门店与状态', icon: 'el-icon-user-solid', path: '/people/item-6' },
        { title: '角色权限', description: '配置菜单、按钮和数据范围', icon: 'el-icon-key', path: '/people/item-7' },
        { title: '门店与渠道', description: '维护门店档案、负责人及启停状态', icon: 'el-icon-office-building', path: '/store/item-1' },
        { title: '审批中心', description: '查看合同、收款和业务审批待办', icon: 'el-icon-document-checked', path: '/approval/item-1' }
      ]
    },
    pageConfig() { const base = getSystemPageConfig(this.pageTitle); return pageOverrides[this.pageTitle] || { ...base, featureId: 'SYS', scopeHint: '配置按权限范围生效，变更会记录操作日志。', primaryAction: '新增配置', secondaryAction: '导出', editAction: '编辑', rowAction: '查看详情', toggleAction: '启用/停用', sectionTitle: `${this.pageTitle}列表`, sectionHint: base.description, statuses: ['启用', '停用'], metrics: [{ label: '配置项', value: String(base.columns.length || 0), note: '当前页面', tone: 'info' }, { label: '待处理', value: '0', note: '暂无', tone: 'good' }, { label: '今日变更', value: '3', note: '已留痕', tone: 'info' }, { label: '异常', value: '0', note: '正常', tone: 'good' }], columns: base.columns.length ? base.columns : [{ key: 'name', label: '名称', width: 180 }, { key: 'status', label: '状态', format: 'status', width: 90 }], formFields: base.formFields.length ? base.formFields : [inputField('name', '名称'), selectField('status', '状态', [option('启用'), option('停用')])], workflowTitle: `${this.pageTitle}处理闭环`, workflowHint: '保存、审核、发布和日志查询在当前页面完成。', workflow: [{ title: '填写配置', detail: '完成必要字段' }, { title: '提交审核', detail: '按权限进入审批' }, { title: '生效留痕', detail: '记录版本和操作人' }] } },
    dialogTitle() { return this.editingId ? `编辑${this.pageTitle}` : this.pageConfig.primaryAction },
    filteredRows() { return this.rows.filter(row => (!this.keyword || Object.values(row).some(value => String(value).includes(this.keyword))) && (!this.statusFilter || row.status === this.statusFilter || row.publishStatus === this.statusFilter || row.taskStatus === this.statusFilter)) }
  },
  watch: { '$route.fullPath': { immediate: true, handler() { this.initializePage() } }},
  methods: {
    initializePage() { this.keyword = ''; this.statusFilter = ''; this.form = {}; this.editingId = ''; this.rows = this.createRows() },
    createRows() { const title = this.pageTitle; if (title === '系统设置') return [{ code: 'SYS-001', name: '默认门店时区', scope: '全部门店', value: 'Asia/Shanghai', updatedBy: '系统管理员', updatedAt: '2026-08-01', status: '启用', id: 'sys1' }, { code: 'SYS-014', name: '会员跨店查询', scope: '全部门店', value: '开启', updatedBy: '系统管理员', updatedAt: '2026-07-30', status: '启用', id: 'sys2' }, { code: 'SYS-021', name: '门店业务隔离', scope: '全部门店', value: '强制', updatedBy: '系统管理员', updatedAt: '2026-07-30', status: '启用', id: 'sys3' }]; if (title === '历史数据迁移工具') return [{ batchNo: 'MIG-260801-01', dataType: '会员主档', targetStore: '全部门店', total: '12,480', success: '12,462', failed: '18', status: '有失败', id: 'mig1' }, { batchNo: 'MIG-260731-02', dataType: '资产余额', targetStore: '上海静安店', total: '2,800', success: '2,800', failed: '0', status: '已完成', id: 'mig2' }, { batchNo: 'MIG-260728-01', dataType: '历史订单', targetStore: '杭州西湖店', total: '4,210', success: '4,210', failed: '0', status: '已完成', id: 'mig3' }]; if (['品牌定制', '品牌定制（Logo/主题色/专属域名）'].includes(title)) return [{ version: 'v2.4', themeName: '开派暖金', scope: '全部门店', domain: 'erp.kaipai.example', publisher: '品牌中心', updatedAt: '2026-08-01', status: '已发布', id: 'br1' }, { version: 'v2.5', themeName: '秋日米杏', scope: '上海静安店', domain: 'sh.kaipai.example', publisher: '品牌中心', updatedAt: '2026-08-01', status: '待发布', id: 'br2' }, { version: 'v2.3', themeName: '春日青绿', scope: '全部门店', domain: 'erp.kaipai.example', publisher: '品牌中心', updatedAt: '2026-06-10', status: '已回滚', id: 'br3' }]; return this.createConfigRows() },
    createConfigRows() { const columns = this.pageConfig.columns; return [0, 1, 2].map(index => { const row = { id: `${this.pageConfig.mode || 'config'}-${index + 1}` }; columns.forEach(column => { row[column.key] = column.format === 'status' ? (index === 1 ? '停用' : '启用') : `${column.label}${index + 1}` }); return row }) },
    resetFilters() { this.keyword = ''; this.statusFilter = '' },
    applyFilters() { this.$message.success(`已查询${this.pageTitle}，共 ${this.filteredRows.length} 条`) },
    runSecondaryAction() { this.$message.success(`${this.pageConfig.secondaryAction}任务已创建`) },
    goTo(path) {
      const query = Object.assign({}, this.$route.query)
      this.$router.push({ path, query }).catch(() => {})
    },
    openCreate() { this.editingId = ''; this.form = {}; this.dialogVisible = true },
    openEdit(row) { this.editingId = row.id; this.form = { ...row }; this.dialogVisible = true },
    resetForm() { this.form = {}; this.editingId = '' },
    saveRecord() { this.$refs.systemForm.validate(valid => { if (!valid) return; const record = { ...this.form, id: this.editingId || `new-${Date.now()}` }; if (this.editingId) { const index = this.rows.findIndex(row => row.id === this.editingId); this.$set(this.rows, index, { ...this.rows[index], ...record }) } else this.rows.unshift(record); this.dialogVisible = false; this.$message.success('已保存，后续将按当前权限进入发布/审批环节') }) },
    handleRowAction(row) { this.$message.info(`${row.id}：已进入${this.pageConfig.rowAction}流程`) },
    toggleRow(row) { const key = row.publishStatus ? 'publishStatus' : row.taskStatus ? 'taskStatus' : 'status'; const current = row[key]; this.$set(row, key, ['启用', '已发布', '运行中'].includes(current) ? '停用' : '启用'); this.$message.success('状态变更已记录操作日志') },
    statusType(status) { if (['停用', '已回滚', '有失败'].includes(status)) return 'danger'; if (['待发布', '待预检', '导入中'].includes(status)) return 'warning'; return 'success' }
  }
}
</script>

<style lang="scss" scoped>
.system-workbench { min-height: 100%; padding: 20px; color: #26344a; background: #f3f5f8; }.hero-panel { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 24px 28px; color: #fff; background: linear-gradient(125deg, #202c3b 0%, #445b76 56%, #7890a8 100%); border-radius: 15px; box-shadow: 0 14px 34px rgba(38, 56, 77, .2); }.eyebrow { margin-bottom: 8px; color: #d9e7f7; font-size: 13px; font-weight: 700; }.hero-panel h1 { margin: 0 0 8px; font-size: 27px; }.hero-panel p { max-width: 780px; margin: 0; color: #eff5fa; font-size: 14px; line-height: 1.7; }.hero-actions, .heading-actions { display: flex; align-items: center; gap: 10px; }.scope-alert { margin-top: 14px; border-radius: 10px; }.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 14px; }.metric-card { padding: 16px 18px; background: #fff; border: 1px solid #e3e8ee; border-radius: 11px; }.metric-card span, .metric-card strong, .metric-card small { display: block; }.metric-card span { color: #7d8997; font-size: 12px; }.metric-card strong { margin: 7px 0 5px; color: #354a60; font-size: 24px; }.metric-card small { font-size: 12px; }.good { color: #339776; }.warn { color: #d18a32; }.bad { color: #d55f6a; }.info { color: #4c80bc; }.content-card, .workflow-card { margin-top: 14px; border: 0; border-radius: 12px; }.card-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }.card-heading h2 { margin: 0 0 4px; font-size: 16px; }.card-heading p { margin: 0; color: #8a98a7; font-size: 12px; }.filter-form { margin-bottom: 8px; }.data-table ::v-deep th { color: #455b71; background: #f5f8fb; }.empty-state { padding: 30px; color: #9ba7b3; text-align: center; }.workflow-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }.workflow-step { display: flex; gap: 10px; padding: 14px; background: #f5f8fb; border-radius: 9px; }.workflow-step > span { display: inline-flex; align-items: center; justify-content: center; flex: 0 0 25px; width: 25px; height: 25px; color: #fff; background: #5b7898; border-radius: 50%; font-size: 12px; }.workflow-step strong, .workflow-step small { display: block; }.workflow-step strong { color: #455b70; font-size: 13px; }.workflow-step small { margin-top: 5px; color: #8c99a7; font-size: 11px; line-height: 1.5; }.full-control { width: 100%; }
.settings-entry-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 14px; }.settings-entry { display: flex; align-items: flex-start; gap: 12px; min-height: 92px; padding: 18px; color: #26344a; background: linear-gradient(145deg, #fff, #f6f2e9); border: 1px solid #e9dec8; border-radius: 11px; cursor: pointer; text-align: left; transition: .18s ease; }.settings-entry:hover { border-color: #bf8f3d; box-shadow: 0 7px 18px rgba(102, 75, 38, .12); transform: translateY(-2px); }.settings-entry > i { padding: 9px; color: #9c6f2d; background: #f5ead5; border-radius: 9px; font-size: 18px; }.settings-entry__icon { display: grid; flex: 0 0 38px; place-items: center; width: 38px; height: 38px; color: #9c6f2d; background: #f5ead5; border-radius: 9px; }.settings-entry__body { flex: 1; }.settings-entry b, .settings-entry small { display: block; }.settings-entry b { margin-top: 2px; font-size: 15px; }.settings-entry small { margin-top: 7px; color: #788596; font-size: 12px; line-height: 1.55; }.settings-guide { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }.settings-guide > div { padding: 15px; background: #f7f9fb; border-left: 3px solid #b88b44; border-radius: 8px; }.settings-guide b, .settings-guide span, .settings-guide small { display: block; }.settings-guide span { margin-bottom: 5px; color: #b28643; font-size: 18px; font-weight: 700; }.settings-guide small { margin-top: 5px; color: #778596; font-size: 12px; line-height: 1.55; }.advanced-settings { margin-top: 14px; padding: 0 16px; color: #657487; background: #f8fafc; border: 1px solid #e6ebf1; border-radius: 10px; }.advanced-settings summary { padding: 13px 0; color: #53677b; font-size: 13px; cursor: pointer; }.advanced-settings ul { margin: 0 0 14px; padding-left: 20px; font-size: 12px; line-height: 2; }
@media (max-width: 1000px) { .metric-grid, .settings-entry-grid { grid-template-columns: repeat(2, 1fr); }.hero-panel { align-items: flex-start; flex-direction: column; }.workflow-steps, .settings-guide { grid-template-columns: 1fr; } } @media (max-width: 700px) { .system-workbench { padding: 12px; }.metric-grid, .settings-entry-grid { grid-template-columns: 1fr; }.card-heading, .heading-actions { align-items: flex-start; flex-direction: column; } }
</style>
