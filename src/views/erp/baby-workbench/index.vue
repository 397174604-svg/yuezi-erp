<template>
  <div class="baby-workbench">
    <section class="baby-hero">
      <div>
        <div class="eyebrow">{{ config.eyebrow }}</div>
        <h1>{{ title }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-meta">
        <el-tag effect="dark" type="warning">P0 / P1 业务闭环</el-tag>
        <span>最后同步 {{ lastLoadedAt || '尚未同步' }}</span>
      </div>
    </section>

    <section v-if="!config.apiAvailable" class="pending-canvas" :class="`pending-${config.kind}`">
      <el-alert :title="config.pendingMessage" type="info" :closable="false" show-icon />
      <div class="pending-layout">
        <div class="pending-summary">
          <span>{{ pendingView.kicker }}</span>
          <h2>{{ pendingView.heading }}</h2>
          <p>{{ pendingView.description }}</p>
          <div class="pending-fields"><el-tag v-for="column in config.columns" :key="column" effect="plain">{{ columnLabel(column) }}</el-tag></div>
        </div>
        <div v-if="config.kind === 'temperature'" class="temperature-timeline">
          <div v-for="(step, index) in pendingView.stages" :key="step" class="timeline-step"><b>{{ index + 1 }}</b><strong>{{ step }}</strong></div>
        </div>
        <div v-else-if="config.kind === 'growth'" class="growth-path">
          <div v-for="(step, index) in pendingView.stages" :key="step" class="growth-stage"><b>{{ index + 1 }}</b><span>{{ step }}</span></div>
        </div>
        <div v-else class="pending-flow">
          <div v-for="(step, index) in pendingView.stages" :key="step"><b>{{ index + 1 }}</b><span>{{ step }}</span></div>
        </div>
      </div>
      <div class="pending-actions"><el-button v-for="action in config.actions" :key="action" size="small" :type="isCreateAction(action) ? 'primary' : 'default'" @click="handleAction(action)">{{ action }}</el-button></div>
    </section>

    <section v-if="config.apiAvailable" class="metric-grid">
      <div v-for="metric in metrics" :key="metric.label" class="metric-card" :class="metric.tone">
        <i :class="metric.icon" />
        <div><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong></div>
      </div>
    </section>

    <el-card v-if="config.apiAvailable" shadow="never" class="filter-card">
      <div slot="header" class="section-head">
        <div><strong>照护工作台</strong><small>按宝宝、房间与状态查询，选中记录后进行下一步流转</small></div>
        <el-button size="small" icon="el-icon-refresh" @click="loadRows">刷新</el-button>
      </div>
      <el-form :inline="true" :model="filters" size="small" class="filter-form">
        <el-form-item v-for="field in config.filters" :key="field.key" :label="field.label">
          <el-select v-if="field.type === 'select'" v-model="filters[field.key]" clearable :placeholder="field.label">
            <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
          </el-select>
          <el-date-picker v-else-if="field.type === 'date'" v-model="filters[field.key]" type="date" value-format="yyyy-MM-dd" :placeholder="field.label" />
          <el-input v-else v-model="filters[field.key]" clearable :placeholder="field.label" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="runSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert
      v-if="config.apiAvailable && loadError"
      class="data-notice"
      type="info"
      :closable="false"
      show-icon
      :title="loadError || config.pendingMessage"
    />

    <div v-if="config.apiAvailable" class="workspace-grid">
      <el-card shadow="never" class="records-card">
        <div class="records-heading">
          <div><strong>{{ tableTitle }}</strong><span>{{ filteredRows.length }} 条记录</span></div>
          <el-button-group>
            <el-button v-for="action in config.actions" :key="action" size="small" :type="isCreateAction(action) ? 'primary' : 'default'" @click="handleAction(action)">
              <i :class="actionIcon(action)" /> {{ action }}
            </el-button>
          </el-button-group>
        </div>

        <div v-if="config.kind === 'temperature'" class="temperature-strip">
          <div v-for="point in temperaturePoints" :key="point.id" class="temperature-point" :class="point.state">
            <span>{{ point.time }}</span><strong>{{ point.temperature }}</strong><small>{{ point.babyName }}</small>
          </div>
          <div class="strip-note"><i class="el-icon-warning-outline" /> 红色点位需护士复核并通知家属</div>
        </div>
        <div v-else-if="config.kind === 'growth'" class="growth-strip">
          <div v-for="card in growthCards" :key="card.label"><span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.note }}</small></div>
        </div>
        <div v-else-if="config.kind === 'handover'" class="handover-strip">
          <div v-for="item in handoverChecklist" :key="item.label" :class="{ done: item.done }"><i :class="item.done ? 'el-icon-circle-check' : 'el-icon-time'" /><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
        </div>

        <el-table :data="pagedRows" border stripe highlight-current-row height="500" :empty-text="emptyText" @current-change="selectRow" @row-dblclick="openDetails">
          <el-table-column type="index" label="#" width="48" fixed="left" />
          <el-table-column v-for="key in config.columns" :key="key" :prop="key" :label="columnLabel(key)" :min-width="columnWidth(key)" show-overflow-tooltip>
            <template slot-scope="scope">
              <el-tag v-if="isStatusKey(key)" size="mini" :type="statusType(scope.row[key])">{{ scope.row[key] }}</el-tag>
              <span v-else>{{ scope.row[key] || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="92" fixed="right">
            <template slot-scope="scope"><el-button type="text" @click="openDetails(scope.row)">查看详情</el-button></template>
          </el-table-column>
        </el-table>
        <div class="pagination-row">
          <span>显示 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
          <el-pagination background layout="prev, pager, next" :current-page.sync="pagination.page" :page-size="pagination.size" :total="filteredRows.length" />
        </div>
      </el-card>

      <el-card shadow="never" class="detail-card">
        <div slot="header" class="section-head"><div><strong>业务详情</strong><small>记录选中后显示关联信息与下一步建议</small></div></div>
        <template v-if="selectedRow">
          <div class="detail-profile"><div class="avatar">{{ (selectedRow.babyName || '宝').slice(0, 1) }}</div><div><strong>{{ selectedRow.babyName }}</strong><span>{{ selectedRow.room }} · {{ selectedRow.store }}</span></div></div>
          <el-alert v-if="selectedRow.temperatureStatus === '待复核' || selectedRow.status === '需关注'" title="当前记录需要护士复核" type="warning" :closable="false" show-icon />
          <dl class="detail-list"><template v-for="key in config.columns"><dt :key="`${key}-label`">{{ columnLabel(key) }}</dt><dd :key="`${key}-value`">{{ selectedRow[key] || '—' }}</dd></template></dl>
          <div class="next-step"><span>建议下一步</span><strong>{{ nextStep }}</strong><el-button size="small" type="primary" @click="handleAction(nextStep)">{{ nextStep }}</el-button></div>
        </template>
        <div v-else class="empty-state"><i class="el-icon-bell" /><strong>尚未选择照护记录</strong><span>请从左侧列表选择一条记录查看照护详情。</span></div>
      </el-card>
    </div>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="640px" :close-on-click-modal="false">
      <el-form :model="dialogForm" label-position="top" class="dialog-form">
        <el-row :gutter="16">
          <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
            <el-form-item :label="field.label" :required="field.required">
              <el-select v-if="field.type === 'select'" v-model="dialogForm[field.key]" class="full-control" clearable>
                <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
              </el-select>
              <el-date-picker v-else-if="field.type === 'date'" v-model="dialogForm[field.key]" class="full-control" type="date" value-format="yyyy-MM-dd" />
              <el-input v-else-if="field.type === 'textarea'" v-model="dialogForm[field.key]" type="textarea" :rows="3" />
              <el-input v-else v-model="dialogForm[field.key]" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer"><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitDialog">保存记录</el-button></div>
    </el-dialog>
  </div>
</template>

<script>
import { getBabyPageConfig } from '@/config/baby-pages'
import { getBabyModuleData, performBabyModuleAction, saveBabyModuleRecord } from '@/api/erp-baby'

const labels = {
  babyName: '宝宝姓名', room: '房间号', store: '门店', logDate: '记录日期', feeding: '喂养', sleep: '睡眠', diaper: '排便', temperature: '体温', status: '任务状态', completionStatus: '补全状态', sleepHours: '睡眠时长', cryCount: '哭闹次数', stoolAmount: '排便量', nurseName: '责任护士', recordNo: '记录编号', careItem: '护理项目', careDate: '护理日期', result: '护理结果', measuredAt: '监测时间', measurer: '监测人', temperatureStatus: '预警状态', actionNote: '处理备注', recordDate: '记录日期', ageDays: '日龄', weight: '体重', height: '身长', milestone: '成长里程碑', growthStage: '成长阶段', visitNo: '访客单号', visitorName: '访客姓名', relationship: '关系', visitDate: '探访日期', disinfection: '消毒核验', visitStatus: '访客状态', handoverNo: '交接单号', handoverDate: '计划离所日', careSummary: '护理摘要', medicine: '用药情况', familySigned: '家属签收', handoverStatus: '交接状态', medicineNo: '用药单号', medicineName: '药品名称', dose: '剂量', medicationDate: '用药日期', operator: '执行人', medicationStatus: '用药状态'
}

export default {
  name: 'BabyWorkbench',
  data() {
    return {
      rows: [], filters: {}, selectedRow: null, lastLoadedAt: '', loading: false, saving: false, loadError: '', loadSequence: 0,
      pagination: { page: 1, size: 10 }, dialogVisible: false, dialogTitle: '', dialogForm: {}
    }
  },
  computed: {
    title() { return this.$route.meta.title || '宝宝照护' },
    config() { return getBabyPageConfig(this.$route.meta.configTitle || this.title) },
    tableTitle() { return this.config.kind === 'temperature' ? '体温监测时间轴' : this.config.kind === 'growth' ? '成长档案记录' : this.config.kind === 'handover' ? '离所交接清单' : `${this.title}记录` },
    filteredRows() {
      const active = Object.keys(this.filters).filter(key => this.filters[key])
      return this.rows.filter(row => active.every(key => String(row[key] || '').includes(String(this.filters[key]))))
    },
    pagedRows() { const start = (this.pagination.page - 1) * this.pagination.size; return this.filteredRows.slice(start, start + this.pagination.size) },
    emptyText() { return this.loadError || this.config.pendingMessage || '暂无记录' },
    pageStart() { return this.filteredRows.length ? (this.pagination.page - 1) * this.pagination.size + 1 : 0 },
    pageEnd() { return Math.min(this.pagination.page * this.pagination.size, this.filteredRows.length) },
    metrics() {
      const flagged = this.rows.filter(row => row.status === '需关注' || row.temperatureStatus === '待复核').length
      return [
        { label: '今日待处理', value: this.rows.filter(row => /待|执行中/.test(row.status || row.medicationStatus || row.handoverStatus || '')).length, icon: 'el-icon-time', tone: 'violet' },
        { label: '异常待复核', value: flagged, icon: 'el-icon-warning-outline', tone: 'orange' },
        { label: '今日已完成', value: this.rows.filter(row => /已完成|已复核|已离场|已服用/.test(row.status || row.completionStatus || row.visitStatus || row.medicationStatus || '')).length, icon: 'el-icon-circle-check', tone: 'green' },
        { label: '在住宝宝', value: new Set(this.rows.map(row => row.babyName)).size, icon: 'el-icon-user', tone: 'pink' }
      ]
    },
    temperaturePoints() { return this.rows.slice(0, 6).map(row => ({ id: row.id, time: row.measuredAt, temperature: row.temperature, babyName: row.babyName, state: row.temperatureStatus === '待复核' ? 'danger' : 'normal' })) },
    growthCards() { const row = this.selectedRow || this.rows[0] || {}; return [{ label: '当前体重', value: row.weight || '—', note: '最近记录' }, { label: '当前身长', value: row.height || '—', note: '最近记录' }, { label: '日龄', value: row.ageDays ? `${row.ageDays} 天` : '—', note: row.growthStage || '待记录' }, { label: '里程碑', value: row.milestone || '—', note: '观察记录' }] },
    handoverChecklist() { const row = this.selectedRow || this.rows[0] || {}; return [{ label: '护理摘要', value: row.careSummary || '待补充', done: Boolean(row.careSummary) }, { label: '用药核对', value: row.medicine || '待核对', done: row.medicine === '无' }, { label: '家属签收', value: row.familySigned || '待签收', done: row.familySigned === '已签收' }] },
    dialogFields() {
      const base = [{ key: 'babyName', label: '宝宝姓名', type: 'input', required: true }, { key: 'room', label: '房间号', type: 'input', required: true }]
      if (this.config.kind === 'temperature') return base.concat([{ key: 'measuredAt', label: '监测时间', type: 'input', required: true }, { key: 'temperature', label: '体温', type: 'input', required: true }, { key: 'measurer', label: '监测人', type: 'input', required: true }, { key: 'actionNote', label: '处理备注', type: 'textarea' }])
      if (this.config.kind === 'visitor') return base.concat([{ key: 'visitorName', label: '访客姓名', type: 'input', required: true }, { key: 'relationship', label: '与宝宝关系', type: 'input', required: true }, { key: 'visitDate', label: '探访日期', type: 'date', required: true }, { key: 'disinfection', label: '消毒核验', type: 'select', options: ['已核验', '待核验'], required: true }])
      if (this.config.kind === 'handover') return base.concat([{ key: 'handoverDate', label: '计划离所日', type: 'date', required: true }, { key: 'careSummary', label: '护理摘要', type: 'textarea', required: true }, { key: 'medicine', label: '用药情况', type: 'input' }])
      if (this.config.kind === 'medication') return base.concat([{ key: 'medicineName', label: '药品名称', type: 'input', required: true }, { key: 'dose', label: '剂量', type: 'input', required: true }, { key: 'medicationDate', label: '用药日期', type: 'date', required: true }, { key: 'operator', label: '执行人', type: 'input', required: true }])
      if (this.config.kind === 'growth') return base.concat([{ key: 'recordDate', label: '记录日期', type: 'date', required: true }, { key: 'weight', label: '体重', type: 'input', required: true }, { key: 'height', label: '身长', type: 'input' }, { key: 'milestone', label: '成长里程碑', type: 'textarea' }])
      if (this.config.kind === 'care') return base.concat([{ key: 'careItem', label: '护理项目', type: 'select', options: ['沐浴', '脐部护理', '黄疸观察', '喂养指导'], required: true }, { key: 'careDate', label: '护理日期', type: 'date', required: true }, { key: 'nurseName', label: '责任护士', type: 'input', required: true }, { key: 'result', label: '护理结果', type: 'textarea', required: true }])
      return base.concat([{ key: 'logDate', label: '记录日期', type: 'date', required: true }, { key: 'feeding', label: '喂养', type: 'input', required: true }, { key: 'sleep', label: '睡眠', type: 'input' }, { key: 'diaper', label: '排便', type: 'input' }])
    },
    nextStep() { if (!this.selectedRow) return '新增照护记录'; if (this.config.kind === 'temperature') return this.selectedRow.temperatureStatus === '待复核' ? '确认异常' : '录入体温'; if (this.config.kind === 'handover') return this.selectedRow.handoverStatus === '已完成' ? '打印交接单' : '确认交接'; if (this.config.kind === 'visitor') return this.selectedRow.visitStatus === '已入场' ? '完成离场' : '核验入场'; if (this.config.kind === 'care') return this.selectedRow.status === '待执行' ? '开始执行' : '完成护理'; if (this.config.kind === 'medication') return this.selectedRow.medicationStatus === '待执行' ? '确认发药' : '完成服用'; return this.selectedRow.status === '已完成' ? '新增照护记录' : '标记完成' },
    pendingView() {
      const views = {
        log: { kicker: '每日照护记录', heading: '喂养、睡眠与排便日志', description: '按宝宝与班次形成连续照护日志，异常项才进入护士复核。', stages: ['录入班次观察', '补全缺失项目', '异常复核'] },
        care: { kicker: '护理执行卡', heading: '新生儿护理项目', description: '沐浴、脐部护理和黄疸观察应从护理任务生成记录。', stages: ['护理任务', '护士执行', '结果留痕', '异常上报'] },
        temperature: { kicker: '异常预警时间轴', heading: '体温监测与护士复核', description: '体温采集、阈值预警与家属通知必须按时间顺序追溯。', stages: ['采集体温', '异常预警', '护士复核', '通知家属'] },
        medication: { kicker: '用药核验流程', heading: '医嘱、发药与服用记录', description: '宝宝用药不得由页面直接伪造，须在医嘱和操作人接入后执行。', stages: ['登记医嘱', '发药核验', '确认服用', '异常复核'] },
        growth: { kicker: '成长里程碑', heading: '体重、身长与离所评估', description: '成长档案按阶段归集，不与日常护理日志混成一张列表。', stages: ['入住初始', '住中观察', '离所评估'] },
        visitor: { kicker: '母婴区域访客控制', heading: '访客登记与消毒核验', description: '访客入场前需核验关系、时段与消毒状态，离场后保留记录。', stages: ['登记访客', '消毒核验', '确认入场', '完成离场'] },
        handover: { kicker: '离所清单', heading: '离所评估与交接', description: '护理、用药、成长资料和家属签收应在离所前逐项核对。', stages: ['离所评估', '资料核对', '家属签收', '完成交接'] }
      }
      return views[this.config.kind] || views.log
    }
  },
  watch: { '$route.fullPath': { immediate: true, handler() { this.filters = {}; this.pagination.page = 1; this.selectedRow = null; this.loadRows() } }},
  methods: {
    columnLabel(key) { return labels[key] || key },
    columnWidth(key) { return /Name|room|status|Status|temperature|Date|At/.test(key) ? 120 : 145 },
    isStatusKey(key) { return /status|Status/.test(key) || ['familySigned', 'disinfection'].includes(key) },
    statusType(value) { if (/需|待|异常|拒绝/.test(value || '')) return 'warning'; if (/完成|正常|已复核|已核验|已签收|离场|服用/.test(value || '')) return 'success'; return 'info' },
    isCreateAction(action) { return /新增|新建|补录|录入/.test(action) },
    actionIcon(action) { if (this.isCreateAction(action)) return 'el-icon-plus'; if (/完成|确认|核验/.test(action)) return 'el-icon-circle-check'; if (/异常/.test(action)) return 'el-icon-warning-outline'; if (/打印|摘要/.test(action)) return 'el-icon-printer'; return 'el-icon-more' },
    async loadRows() {
      const sequence = ++this.loadSequence
      const resource = this.config.key
      this.rows = []
      this.selectedRow = null
      this.loadError = ''
      if (!this.config.apiAvailable) return
      this.loading = true
      try {
        const response = await getBabyModuleData(resource, {
          ...this.filters,
          storeId: this.$route.query.storeId || 'all'
        })
        if (this.loadSequence !== sequence) return
        this.rows = response.data && response.data.list ? response.data.list : []
        this.lastLoadedAt = new Date().toLocaleTimeString()
      } catch (error) {
        if (this.loadSequence === sequence) {
          this.rows = []
          this.loadError = '宝宝照护数据查询失败，请稍后刷新。'
        }
      } finally { if (this.loadSequence === sequence) this.loading = false }
    },
    runSearch() { this.pagination.page = 1; this.loadRows() },
    resetFilters() { this.filters = {}; this.pagination.page = 1; this.loadRows() },
    selectRow(row) { this.selectedRow = row },
    openDetails(row) { this.selectedRow = row },
    handleAction(action) {
      if (!this.config.apiAvailable) return this.$message.info(`“${action}”暂未开放办理，请联系系统管理员。`)
      if (/新增|新建|补录|录入/.test(action)) return this.openDialog(action)
      if (/打印|摘要/.test(action)) { window.print(); return }
      if (!this.selectedRow) return this.$message.warning('请先选择一条记录')
      this.executeAction(action)
    },
    openDialog(action) { this.dialogTitle = action; this.dialogForm = {}; this.dialogFields.forEach(field => { this.$set(this.dialogForm, field.key, '') }); this.dialogVisible = true },
    async submitDialog() {
      if (!this.config.apiAvailable) return this.$message.info(`${this.title}当前尚未开放，记录未保存。`)
      const storeId = String(this.$route.query.storeId || 'all')
      if (!/^\d+$/.test(storeId)) return this.$message.warning('请先在顶部选择具体门店后再新增记录')
      const missing = this.dialogFields.filter(field => field.required && !this.dialogForm[field.key])
      if (missing.length) return this.$message.warning(`请填写：${missing.map(field => field.label).join('、')}`)
      this.saving = true
      try {
        const row = { ...this.dialogForm, storeId: Number(storeId), id: `BABY-${Date.now()}`, store: storeId === '1' ? '中心广场旗舰店' : '黄河路轻奢店', status: '待记录', completionStatus: '待补全', temperatureStatus: '正常', medicationStatus: '待执行', visitStatus: '待核验', handoverStatus: '待评估' }
        await saveBabyModuleRecord(this.config.key, row)
        this.rows.unshift(row)
        this.selectedRow = row
        this.dialogVisible = false
        this.$message.success('记录已保存，可继续执行状态流转')
      } catch (error) { this.$message.error('保存失败，请稍后重试') } finally { this.saving = false }
    },
    async executeAction(action) {
      const storeId = Number(this.selectedRow.storeId || this.$route.query.storeId)
      if (!Number.isInteger(storeId) || storeId <= 0) return this.$message.warning('请先选择具体门店后再处理记录')
      try {
        await performBabyModuleAction(this.config.key, action, { id: this.selectedRow.id, storeId })
        const row = this.selectedRow
        if (/标记完成|完成护理|完成服用/.test(action)) {
          this.$set(row, 'status', '已完成')
          this.$set(row, 'medicationStatus', '已服用')
        }
        if (action === '开始执行') this.$set(row, 'status', '执行中')
        if (action === '确认异常') this.$set(row, 'temperatureStatus', '已确认')
        if (action === '核验入场') this.$set(row, 'visitStatus', '已入场')
        if (action === '完成离场') this.$set(row, 'visitStatus', '已离场')
        if (action === '确认交接') this.$set(row, 'handoverStatus', '已完成')
        if (action === '确认发药') this.$set(row, 'medicationStatus', '已发药')
        this.$message.success(`${action}已完成`)
      } catch (error) {
        this.$message.error('状态流转失败，请稍后重试')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.baby-workbench { min-height: calc(100vh - 84px); padding: 22px; color: #3b3151; background: #f7f4fb; }
.pending-canvas { margin-top: 16px; padding: 16px; border: 1px solid #e4ddeb; border-radius: 14px; background: #fff; box-shadow: 0 5px 18px rgba(78, 55, 96, .05); }.pending-layout { display: grid; grid-template-columns: minmax(270px, 1fr) minmax(330px, 1.4fr); gap: 22px; align-items: center; padding: 22px 8px 16px; }.pending-summary > span { color: #8c629f; font-size: 12px; font-weight: 700; }.pending-summary h2 { margin: 7px 0; color: #4b386d; font-size: 21px; }.pending-summary p { margin: 0; color: #857991; font-size: 13px; line-height: 1.7; }.pending-fields { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }.pending-fields .el-tag { color: #73548a; border-color: #decfe8; background: #fbf8fd; }.pending-flow, .temperature-timeline, .growth-path { display: flex; align-items: center; justify-content: space-between; gap: 7px; min-height: 96px; }.pending-flow > div, .timeline-step, .growth-stage { position: relative; display: grid; gap: 6px; min-width: 76px; padding: 11px; border-radius: 10px; background: #faf6fc; text-align: center; }.pending-flow > div:not(:last-child)::after, .timeline-step:not(:last-child)::after, .growth-stage:not(:last-child)::after { position: absolute; top: 50%; left: calc(100% + 1px); width: 8px; height: 1px; background: #cdbbd8; content: ''; }.pending-flow b, .timeline-step b, .growth-stage b { display: inline-grid; width: 22px; height: 22px; margin: 0 auto; border-radius: 50%; color: #fff; background: #8a63a2; place-items: center; font-size: 11px; }.pending-flow span, .timeline-step strong, .growth-stage span { color: #5d4c6d; font-size: 12px; }.temperature-timeline { align-items: flex-start; padding-top: 8px; border-top: 2px solid #f1d2db; }.temperature-timeline .timeline-step { margin-top: -18px; border: 1px solid #f4dfe5; background: #fff9fa; }.temperature-timeline .timeline-step b { background: #d46f84; }.growth-path { align-items: stretch; }.growth-stage { flex: 1; justify-content: center; border-bottom: 3px solid #84b69a; background: #f5fbf7; }.growth-stage b { background: #5c9b77; }.pending-actions { padding: 14px 8px 2px; border-top: 1px solid #f0ebf3; }.pending-actions .el-button + .el-button { margin-left: 8px; }
.baby-hero { display: flex; justify-content: space-between; gap: 24px; padding: 26px 30px; border-radius: 18px; color: #fff; background: linear-gradient(120deg, #4b386d, #8c5da9 58%, #d68fb5); box-shadow: 0 15px 30px rgba(95, 67, 120, .2); }
.eyebrow { margin-bottom: 8px; color: #f6dff1; font-size: 12px; font-weight: 700; letter-spacing: .5px; }.baby-hero h1 { margin: 0 0 8px; font-size: 26px; }.baby-hero p { max-width: 760px; margin: 0; color: #f9eff8; line-height: 1.7; }.hero-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 13px; white-space: nowrap; }.hero-meta span { color: #f3deee; font-size: 12px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 16px 0; }.metric-card { display: flex; align-items: center; gap: 13px; padding: 17px 18px; border-radius: 12px; background: #fff; box-shadow: 0 3px 11px rgba(78, 55, 96, .05); }.metric-card i { display: grid; width: 40px; height: 40px; border-radius: 12px; place-items: center; font-size: 20px; }.metric-card span, .metric-card strong { display: block; }.metric-card span { color: #8d8098; font-size: 12px; }.metric-card strong { margin-top: 4px; color: #4b386d; font-size: 23px; }.violet i { color: #72559a; background: #efe9fa; }.orange i { color: #c98545; background: #fff0de; }.green i { color: #4b9a75; background: #e8f7ef; }.pink i { color: #c35e8a; background: #fdeaf2; }
.filter-card, .records-card, .detail-card { border: 0; border-radius: 12px; }.section-head, .records-heading, .detail-profile, .pagination-row { display: flex; align-items: center; justify-content: space-between; gap: 15px; }.section-head strong, .records-heading strong { display: block; color: #493b5d; font-size: 15px; }.section-head small { display: block; margin-top: 4px; color: #998fa4; font-size: 12px; }.filter-form { margin-bottom: -12px; }.filter-form ::v-deep .el-form-item { margin-bottom: 14px; }.filter-form ::v-deep .el-input, .filter-form ::v-deep .el-select, .filter-form ::v-deep .el-date-editor { width: 150px; }.workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) 310px; gap: 16px; margin-top: 16px; }.records-heading { margin-bottom: 15px; }.records-heading > div { display: flex; align-items: baseline; gap: 10px; }.records-heading span { color: #9a91a5; font-size: 12px; }.records-heading .el-button + .el-button { margin-left: 0; }.records-heading i { margin-right: 2px; }.records-card ::v-deep .el-table th { color: #5d4d70; background: #f7f1fa; }.records-card ::v-deep .el-table .warning-row { background: #fff8ee; }.pagination-row { padding-top: 16px; color: #93889e; font-size: 12px; }.detail-card { min-height: 300px; }.empty-state { display:flex; align-items:center; flex-direction:column; justify-content:center; min-height:220px; padding:20px; color:#9a8fa3; text-align:center; }.empty-state i { margin-bottom:12px; color:#b7a6c1; font-size:34px; }.empty-state strong,.empty-state span { display:block; }.empty-state strong { margin-bottom:7px; color:#665474; }.detail-profile { justify-content: flex-start; margin: 6px 0 18px; }.avatar { display: grid; width: 48px; height: 48px; border-radius: 50%; color: #fff; background: linear-gradient(135deg, #b47ac7, #7f5a9d); font-size: 22px; place-items: center; }.detail-profile strong, .detail-profile span { display: block; }.detail-profile strong { color: #4b386d; font-size: 16px; }.detail-profile span { margin-top: 5px; color: #9a8fa3; font-size: 12px; }.detail-list { display: grid; grid-template-columns: 84px 1fr; margin: 18px 0; font-size: 12px; line-height: 1.65; }.detail-list dt { color: #9a8fa3; }.detail-list dd { margin: 0 0 9px; color: #554863; }.next-step { padding: 13px; border-radius: 10px; background: #faf5fc; }.next-step span, .next-step strong { display: block; }.next-step span { color: #988ca1; font-size: 11px; }.next-step strong { margin: 4px 0 10px; color: #704c8a; font-size: 14px; }.temperature-strip, .growth-strip, .handover-strip { display: flex; gap: 10px; margin-bottom: 15px; padding: 12px; border-radius: 10px; background: #faf7fb; overflow-x: auto; }.temperature-point { min-width: 94px; padding: 10px; border-radius: 8px; background: #eaf7ef; }.temperature-point.danger { background: #fff0e5; }.temperature-point span, .temperature-point strong, .temperature-point small { display: block; }.temperature-point span, .temperature-point small { color: #9d92a5; font-size: 11px; }.temperature-point strong { margin: 5px 0; color: #4e8e6a; font-size: 16px; }.temperature-point.danger strong { color: #c56d45; }.strip-note { align-self: center; min-width: 210px; color: #9e8a99; font-size: 12px; }.growth-strip > div, .handover-strip > div { min-width: 130px; padding: 10px 12px; border-radius: 8px; background: #fff; }.growth-strip span, .growth-strip strong, .growth-strip small, .handover-strip span, .handover-strip strong { display: block; }.growth-strip span, .handover-strip span { color: #9d92a5; font-size: 11px; }.growth-strip strong, .handover-strip strong { margin: 4px 0; color: #704c8a; font-size: 16px; }.growth-strip small { color: #b0a5b7; font-size: 11px; }.handover-strip i { margin-right: 5px; color: #c4b8c9; }.handover-strip .done i { color: #5aa87e; }.full-control { width: 100%; }.dialog-form { max-height: 58vh; padding-right: 8px; overflow-y: auto; }
@media (max-width: 1050px) { .workspace-grid { grid-template-columns: 1fr; }.detail-card { min-height: auto; }.metric-grid { grid-template-columns: repeat(2, 1fr); } } @media (max-width: 700px) { .baby-workbench { padding: 12px; }.baby-hero, .hero-meta, .records-heading { align-items: flex-start; flex-direction: column; }.hero-meta { align-items: flex-start; }.metric-grid { grid-template-columns: 1fr 1fr; }.records-heading .el-button-group { display: flex; flex-wrap: wrap; }.records-heading .el-button { margin: 0 5px 5px 0; }.filter-form ::v-deep .el-input, .filter-form ::v-deep .el-select, .filter-form ::v-deep .el-date-editor { width: 100%; } }
</style>
