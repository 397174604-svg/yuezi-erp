<template>
  <div class="customer-workbench">
    <section class="hero-panel">
      <div class="hero-copy">
        <div class="eyebrow"><i :class="config.icon" /> 客户管理 · 业务工作台</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-actions">
        <el-tag effect="plain" type="success"><i class="el-icon-circle-check" /> 字段已核对</el-tag>
        <el-button icon="el-icon-refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button v-if="!isPointSettings" type="primary" icon="el-icon-download" @click="exportRows">导出当前结果</el-button>
      </div>
    </section>

    <template v-if="isPointSettings">
      <section class="point-overview">
        <div>
          <span>规则总数</span>
          <strong>{{ pointSettingGroups.length }}</strong>
        </div>
        <div>
          <span>按比例积分</span>
          <strong>{{ percentRuleCount }}</strong>
        </div>
        <div>
          <span>固定积分</span>
          <strong>{{ fixedRuleCount }}</strong>
        </div>
        <el-button type="primary" icon="el-icon-check" :loading="saving" @click="savePoints">保存积分设置</el-button>
      </section>

      <el-card shadow="never" class="point-card">
        <div slot="header" class="card-heading">
          <div><h2>积分生成规则</h2><p>销售和收款类可按金额比例或固定值计算；会员行为按固定积分计算。</p></div>
          <el-tag type="info">共 15 项</el-tag>
        </div>
        <div class="point-grid">
          <div v-for="(item, index) in pointSettingGroups" :key="item.key" class="point-rule">
            <div class="rule-index">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="rule-name">
              <strong>{{ item.label }}</strong>
              <span>{{ index > 9 ? '会员行为完成后生成' : '交易完成后自动生成' }}</span>
            </div>
            <el-radio-group v-if="index < 10" v-model="pointSettings[item.key].mode" size="mini">
              <el-radio-button label="percent">比例</el-radio-button>
              <el-radio-button label="fixed">固定</el-radio-button>
            </el-radio-group>
            <el-tag v-else size="small" type="info">固定</el-tag>
            <el-input-number v-model="pointSettings[item.key].value" :min="0" :max="100000" :precision="pointSettings[item.key].mode === 'percent' ? 2 : 0" controls-position="right" />
            <span class="rule-unit">{{ pointSettings[item.key].mode === 'percent' ? '%' : '分' }}</span>
          </div>
        </div>
      </el-card>
    </template>

    <template v-else>
      <section class="metric-strip">
        <div v-for="item in metrics" :key="item.label" class="metric-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.tip }}</small>
        </div>
      </section>

      <section v-if="config.stages" class="stage-strip">
        <button v-for="stage in config.stages" :key="stage" :class="{ active: activeStage === stage }" @click="activeStage = stage">
          <span>{{ stage }}</span><b>{{ stageCounts[stage] || 0 }}</b>
        </button>
      </section>

      <section v-if="isTagWorkbench" class="tag-overview">
        <div class="tag-overview__copy">
          <h2>客户标签分布</h2>
          <p>标签来自客户档案，不跨门店修改客户归属；“全部门店”仅做汇总查看。</p>
        </div>
        <div class="tag-cloud">
          <el-tag v-for="item in tagSummary" :key="item.name" effect="plain">
            {{ item.name }} <b>{{ item.count }}</b>
          </el-tag>
          <span v-if="!tagSummary.length" class="empty-tag-tip">当前客户档案尚未维护标签</span>
        </div>
      </section>

      <section v-if="pageTitle === '客户管理'" class="reminder-strip">
        <div v-for="item in reminderItems" :key="item.label" @click="applyReminder(item)">
          <i :class="item.icon" /><span>{{ item.label }}</span><strong>{{ item.count }}</strong><small>{{ item.tip }}</small>
        </div>
      </section>

      <el-card shadow="never" class="filter-card">
        <div slot="header" class="card-heading compact">
          <div><h2>查询条件</h2><p>已按原系统保留本页专属查询字段</p></div>
          <div>
            <el-button type="text" icon="el-icon-delete" @click="resetFilters">清空</el-button>
            <el-button type="primary" size="small" icon="el-icon-search" @click="search">查询</el-button>
          </div>
        </div>
        <el-form label-position="top" class="filter-form">
          <el-row :gutter="16">
            <el-col v-for="field in visibleFilters" :key="field.key" :xl="4" :lg="6" :md="8" :sm="12" :xs="24">
              <el-form-item :label="field.label">
                <el-input
                  v-if="field.type === 'input'"
                  v-model.trim="filters[field.key]"
                  clearable
                  :maxlength="isPhoneField(field) ? 11 : 100"
                  :inputmode="isPhoneField(field) ? 'numeric' : undefined"
                  :placeholder="`请输入${field.label}`"
                  @input="handleFilterInput(field, $event)"
                  @keyup.enter.native="search"
                />
                <el-select v-else-if="field.type === 'select'" v-model="filters[field.key]" clearable filterable placeholder="请选择" class="full-control">
                  <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                </el-select>
                <el-date-picker v-else-if="field.type === 'dateRange'" v-model="filters[field.key]" type="daterange" value-format="yyyy-MM-dd" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" class="full-control" />
                <el-date-picker v-else-if="field.type === 'date'" v-model="filters[field.key]" :type="field.dateType || 'date'" value-format="yyyy-MM-dd HH:mm:ss" placeholder="请选择" class="full-control" />
                <el-checkbox v-else-if="field.type === 'checkbox'" v-model="filters[field.key]">启用此条件</el-checkbox>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        <button v-if="config.filters.length > defaultFilterCount" type="button" class="filter-toggle" @click="filtersExpanded = !filtersExpanded">
          {{ filtersExpanded ? '收起更多条件' : `展开更多条件（${config.filters.length - defaultFilterCount}）` }}
          <i :class="filtersExpanded ? 'el-icon-arrow-up' : 'el-icon-arrow-down'" />
        </button>
      </el-card>

      <el-card shadow="never" class="table-card">
        <div slot="header" class="table-toolbar">
          <div class="business-actions">
            <el-button
              v-for="(action, index) in config.actions"
              :key="action"
              :type="index === 0 ? 'primary' : action === '删除' ? 'danger' : 'default'"
              :plain="index !== 0"
              size="small"
              :icon="actionIcon(action)"
              @click="handleAction(action)"
            >{{ action }}</el-button>
          </div>
          <div class="selection-tip"><i class="el-icon-s-order" /> 已选 {{ selection.length }} 条 · 共 {{ filteredRows.length }} 条</div>
        </div>

        <el-table v-loading="loading" :data="pagedRows" border stripe height="510" highlight-current-row @selection-change="selection = $event">
          <el-table-column type="selection" width="45" fixed="left" />
          <el-table-column type="index" label="序号" width="58" fixed="left" :index="tableIndex" />
          <el-table-column v-for="column in config.columns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 110" show-overflow-tooltip>
            <template slot-scope="scope">
              <el-tag v-if="column.tag" size="mini" :type="tagType(scope.row[column.key])">{{ scope.row[column.key] }}</el-tag>
              <span v-else-if="isMoneyColumn(column.key)" class="money">¥ {{ money(scope.row[column.key]) }}</span>
              <span v-else>{{ scope.row[column.key] }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openView(scope.row)">详情</el-button>
              <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
              <el-dropdown trigger="click" @command="command => handleRowCommand(command, scope.row)">
                <span class="more-link">更多<i class="el-icon-arrow-down" /></span>
                <el-dropdown-menu slot="dropdown">
                  <el-dropdown-item command="follow">跟进记录</el-dropdown-item>
                  <el-dropdown-item command="history">操作轨迹</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-row">
          <span>显示第 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
          <el-pagination background layout="prev, pager, next, sizes" :current-page.sync="pagination.page" :page-size.sync="pagination.size" :page-sizes="[10, 20, 50, 100]" :total="filteredRows.length" />
        </div>
      </el-card>
    </template>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="760px" :close-on-click-modal="false">
      <el-alert v-if="dialogMode === 'operation'" :title="operationTip" type="info" :closable="false" show-icon class="dialog-alert" />
      <el-form ref="recordForm" :model="recordForm" label-width="112px" class="record-form">
        <el-row :gutter="18">
          <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
            <el-form-item :label="field.label" :required="isRequired(field)">
              <el-input
                v-if="field.type === 'input'"
                v-model.trim="recordForm[field.key]"
                :maxlength="isPhoneField(field) ? 11 : 100"
                :inputmode="isPhoneField(field) ? 'numeric' : undefined"
                :placeholder="`请输入${field.label}`"
                @input="handleDialogInput(field, $event)"
              />
              <el-input v-else-if="field.type === 'textarea'" v-model.trim="recordForm[field.key]" type="textarea" :rows="3" maxlength="500" show-word-limit :placeholder="`请输入${field.label}`" />
              <el-select v-else-if="field.type === 'select'" v-model="recordForm[field.key]" filterable clearable placeholder="请选择" class="full-control">
                <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
              </el-select>
              <el-date-picker v-else-if="field.type === 'date'" v-model="recordForm[field.key]" :type="field.dateType || 'date'" value-format="yyyy-MM-dd HH:mm:ss" placeholder="请选择" class="full-control" />
              <el-date-picker v-else-if="field.type === 'dateRange'" v-model="recordForm[field.key]" type="daterange" value-format="yyyy-MM-dd" class="full-control" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord">确认保存</el-button>
      </div>
    </el-dialog>

    <el-drawer title="客户业务详情" :visible.sync="drawerVisible" size="520px">
      <div v-if="currentRow" class="detail-drawer">
        <div class="detail-head"><span>{{ displayName(currentRow) }}</span><el-tag size="small" type="success">业务数据</el-tag></div>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item v-for="column in config.columns" :key="column.key" :label="column.label">{{ currentRow[column.key] }}</el-descriptions-item>
        </el-descriptions>
        <h3>业务轨迹</h3>
        <p class="audit-empty">操作轨迹由审计接口返回；当前未返回轨迹时不展示推测记录。</p>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { getCustomerPageConfig, leadFollowStatuses, pointSettingGroups } from '@/config/customer-pages'
import { getCustomerModuleData, performCustomerModuleAction, saveCustomerModuleRecord, savePointSettings } from '@/api/erp-customer'
import { mapGetters } from 'vuex'

const inputField = (key, label) => ({ key, label, type: 'input' })
const textareaField = (key, label) => ({ key, label, type: 'textarea' })
const selectField = (key, label, options) => ({ key, label, type: 'select', options })
const dateField = (key, label, dateType = 'datetime') => ({ key, label, type: 'date', dateType })
const storeByRouteId = { 1: '中心广场旗舰店', 2: '黄河路轻奢店' }
const rangeFieldAliases = {
  createdRange: 'createdAt',
  dueRange: 'dueDate',
  followRange: 'followedAt',
  appointmentRange: 'appointmentAt',
  visitRange: 'visitAt',
  signedRange: 'signedAt'
}

function routeStoreName(route) {
  const query = (route && route.query) || {}
  return storeByRouteId[Number(query.storeId)] || (Object.values(storeByRouteId).includes(query.store) ? query.store : '')
}

function localDateTimeText() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now.getTime() - offset).toISOString().slice(0, 16).replace('T', ' ')
}

export default {
  name: 'CustomerWorkbench',
  data() {
    return {
      loading: false,
      saving: false,
      filtersExpanded: false,
      filters: {},
      rows: [],
      selection: [],
      activeStage: '全部',
      pagination: { page: 1, size: 10 },
      dialogVisible: false,
      dialogMode: 'create',
      dialogAction: '',
      dialogTitle: '',
      dialogFields: [],
      operationTip: '',
      recordForm: {},
      currentRow: null,
      drawerVisible: false,
      pointSettingGroups,
      pointSettings: {}
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    hasConcreteStore() { return this.currentStoreId && String(this.currentStoreId) !== 'all' },
    pageTitle() {
      return this.$route.meta.configTitle || this.$route.meta.title
    },
    config() {
      return getCustomerPageConfig(this.pageTitle)
    },
    isPointSettings() {
      return this.pageTitle === '积分设置'
    },
    isTrackingWorkbench() {
      return this.pageTitle === '业务跟踪台'
    },
    isTagWorkbench() {
      return this.pageTitle === '客户标签体系'
    },
    defaultFilterCount() {
      return 8
    },
    visibleFilters() {
      return this.filtersExpanded ? this.config.filters : this.config.filters.slice(0, this.defaultFilterCount)
    },
    filteredRows() {
      let data = this.rows
      if (this.config.stages && this.activeStage !== '全部') {
        data = data.filter(row => this.stageForRow(row) === this.activeStage)
      }
      const entries = Object.entries(this.filters).filter(([, value]) => value !== '' && value !== null && value !== false && (!Array.isArray(value) || value.length))
      if (!entries.length) return data
      return data.filter(row => entries.every(([key, value]) => {
        const field = this.config.filters.find(item => item.key === key) || {}
        const targetValue = row[key] !== undefined ? row[key] : row[rangeFieldAliases[key]]
        if (Array.isArray(value)) {
          const target = String(targetValue || '').slice(0, 10)
          return (!value[0] || target >= value[0]) && (!value[1] || target <= value[1])
        }
        if (key === 'unfollowedDays') return Number(targetValue || 0) >= Number(value || 0)
        if (field.type === 'select') return String(targetValue || '') === String(value)
        return String(targetValue || '').toLowerCase().includes(String(value).toLowerCase())
      }))
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
    },
    metrics() {
      const count = this.rows.length
      if (this.isTrackingWorkbench) {
        const dueSoon = this.rows.filter(item => item.dueDate && String(item.dueDate).slice(0, 10) >= this.todayText).length
        return [
          { label: '客户总数', value: count, tip: '来自当前门店权限范围' },
          { label: '意向客户', value: this.stageCounts['意向客户'] || 0, tip: '需要销售持续跟进' },
          { label: '已签约客户', value: this.stageCounts['已签约客户'] || 0, tip: '已进入合同链路' },
          { label: '有预产期客户', value: dueSoon, tip: '用于安排后续跟进' }
        ]
      }
      if (this.isTagWorkbench) {
        return [
          { label: '客户总数', value: count, tip: '当前查询范围' },
          { label: '已维护标签', value: this.rows.filter(item => this.rowTags(item).length).length, tip: '至少包含一个标签' },
          { label: '标签种类', value: this.tagSummary.length, tip: '真实档案去重统计' },
          { label: '待补标签', value: this.rows.filter(item => !this.rowTags(item).length).length, tip: '建议后续完善档案' }
        ]
      }
      if (this.pageTitle === '线索管理') {
        const statusCount = status => this.rows.filter(item => item.followStatus === status).length
        return [
          { label: '线索总量', value: count, tip: '当前门店线索' },
          { label: '待跟进', value: statusCount('待跟进'), tip: '尚无有效跟进记录' },
          { label: '跟进中', value: statusCount('跟进中'), tip: '已有跟进且未关闭' },
          { label: '已转化', value: statusCount('已转化'), tip: '已进入客户或签约流程' }
        ]
      }
      const labels = {
        '预约参观': ['预约总量', '今日到店', '已确认', '已转化'],
        '客户投诉建议': ['投诉总量', '未处理', '处理中', '已完成'],
        '客户消息': ['消息总量', '待发送', '发送成功', '发送失败'],
        '发布活动': ['活动总量', '进行中', '报名人数', '问卷回收']
      }
      const current = labels[this.pageTitle] || ['当前记录', '本月新增', '待处理', '已完成']
      return current.map((label, index) => ({ label, value: index === 0 ? count : 0, tip: '当前查询结果' }))
    },
    reminderItems() {
      const countStage = stage => this.rows.filter(row => this.stageForRow(row) === stage).length
      const withinSevenDays = this.rows.filter(row => {
        const due = String(row.dueDate || '').slice(0, 10)
        if (!due) return false
        const days = Math.floor((new Date(`${due}T00:00:00`).getTime() - new Date(`${this.todayText}T00:00:00`).getTime()) / 86400000)
        return days >= 0 && days <= 7
      }).length
      return [
        { label: '待持续跟进', count: countStage('意向客户') + countStage('进店客户'), tip: '按客户状态统计', icon: 'el-icon-phone-outline', stage: '意向客户' },
        { label: '7 天内预产', count: withinSevenDays, tip: '来自已录预产期档案', icon: 'el-icon-date' },
        { label: '待入住客户', count: countStage('待入住客户'), tip: '按当前客户状态统计', icon: 'el-icon-house', stage: '待入住客户' },
        { label: '已退房待回访', count: countStage('已退房客户'), tip: '按当前客户状态统计', icon: 'el-icon-s-home', stage: '已退房客户' },
        { label: '签约客户', count: countStage('已签约客户'), tip: '按当前客户状态统计', icon: 'el-icon-document-checked', stage: '已签约客户' }
      ]
    },
    todayText() {
      const date = new Date()
      const pad = value => String(value).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    },
    stageCounts() {
      const counts = { 全部: this.rows.length }
      ;(this.config.stages || []).forEach(stage => { if (stage !== '全部') counts[stage] = 0 })
      this.rows.forEach(row => {
        const stage = this.stageForRow(row)
        if (stage) counts[stage] = (counts[stage] || 0) + 1
      })
      return counts
    },
    tagSummary() {
      const counts = {}
      this.rows.forEach(row => this.rowTags(row).forEach(tag => { counts[tag] = (counts[tag] || 0) + 1 }))
      return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name)).slice(0, 20)
    },
    percentRuleCount() {
      return Object.values(this.pointSettings).filter(item => item.mode === 'percent').length
    },
    fixedRuleCount() {
      return this.pointSettingGroups.length - this.percentRuleCount
    }
  },
  watch: {
    currentStoreId() { this.initializePage() },
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    }
  },
  methods: {
    initializePage() {
      this.filters = this.config.filters.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'checkbox' ? false : field.type === 'dateRange' ? [] : '')
        return result
      }, {})
      const store = routeStoreName(this.$route)
      if (store && Object.prototype.hasOwnProperty.call(this.filters, 'store')) this.filters.store = store
      this.activeStage = this.config.stages ? this.config.stages[0] : '全部'
      this.filtersExpanded = false
      this.pagination.page = 1
      this.initializePoints()
      this.loadData()
    },
    initializePoints() {
      this.pointSettingGroups.forEach((item, index) => {
        this.$set(this.pointSettings, item.key, { mode: index < 8 ? 'percent' : 'fixed', value: index < 8 ? 1 : index * 5 + 10 })
      })
    },
    async loadData() {
      if (this.isPointSettings) return
      this.loading = true
      try {
        const response = await getCustomerModuleData(this.config.key, { ...this.filters, storeId: this.currentStoreId || 'all' })
        const list = response.data && Array.isArray(response.data.list) ? response.data.list : []
        this.rows = this.normalizeRows(list)
      } catch (error) {
        this.rows = []
      } finally {
        this.loading = false
      }
    },
    search() {
      this.pagination.page = 1
      this.$message.success(`已按 ${this.visibleFilters.length} 个本页字段完成查询`)
    },
    resetFilters() {
      Object.keys(this.filters).forEach(key => { this.filters[key] = Array.isArray(this.filters[key]) ? [] : typeof this.filters[key] === 'boolean' ? false : '' })
      const store = routeStoreName(this.$route)
      if (store && Object.prototype.hasOwnProperty.call(this.filters, 'store')) this.filters.store = store
      this.activeStage = this.config.stages ? this.config.stages[0] : '全部'
      this.pagination.page = 1
    },
    normalizeRows(rows) {
      if (this.pageTitle !== '线索管理') return rows
      return rows.map(row => ({
        ...row,
        store: row.store || row.convertStore || '',
        followStatus: leadFollowStatuses.includes(row.followStatus) ? row.followStatus : ''
      }))
    },
    stageForRow(row) {
      const status = String(row.status || '')
      if (/流失/.test(status)) return '流失客户'
      if (/散客|零散/.test(status)) return '零散客户'
      if (/已退房/.test(status)) return '已退房客户'
      if (/已入住/.test(status)) return '已入住客户'
      if (/已订房|待入住|未入住/.test(status)) return '待入住客户'
      if (/已签|同意签合同|已审核/.test(status) || row.contractNo) return '已签约客户'
      if (/进店|到店/.test(status)) return '进店客户'
      if (/意向/.test(status)) return '意向客户'
      return ''
    },
    rowTags(row) {
      if (Array.isArray(row.tags)) return row.tags.map(item => String(item).trim()).filter(Boolean)
      return String(row.tags || '').split(/[、,，;；]/).map(item => item.trim()).filter(Boolean)
    },
    actionIcon(action) {
      if (action.includes('添加') || action.includes('新增')) return 'el-icon-plus'
      if (action.includes('编辑')) return 'el-icon-edit'
      if (action.includes('删除')) return 'el-icon-delete'
      if (action.includes('导出')) return 'el-icon-download'
      if (action.includes('导入')) return 'el-icon-upload2'
      if (action.includes('打印') || action.includes('二维码')) return 'el-icon-printer'
      if (action.includes('跟进') || action.includes('跟踪')) return 'el-icon-chat-line-round'
      return 'el-icon-setting'
    },
    handleAction(action) {
      if (action === '添加' && this.pageTitle === '客户管理') {
        this.$router.push('/customer/item-2')
        return
      }
      if (action.includes('导出')) return this.exportRows()
      if (action.includes('导入')) return this.$message.info('已打开客户导入校验流程：模板校验 → 重复检查 → 预览确认')
      if (action === '删除') return this.removeRows()
      if (action.includes('打印') || action.includes('二维码')) return this.$message.success(`${action}任务已生成，可进入打印预览`)
      if (action.includes('添加') || action.includes('新增')) return this.openCreate(action)
      if (action === '编辑') return this.openEdit(this.requireOne())
      if (action.includes('跟进') || action.includes('跟踪')) return this.openFollow()
      this.openOperation(action)
    },
    requireOne() {
      const row = this.selection[0]
      if (!row) this.$message.warning('请先选择一条业务记录')
      return row
    },
    openCreate(action = '添加') {
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再新增')
      this.dialogMode = 'create'
      this.dialogAction = action
      this.dialogTitle = `${action}${this.pageTitle}`
      this.dialogFields = this.config.formFields.length ? this.config.formFields : [inputField('customerName', '客户姓名'), textareaField('remark', '备注')]
      this.recordForm = this.emptyForm(this.dialogFields)
      const store = routeStoreName(this.$route)
      if (store && Object.prototype.hasOwnProperty.call(this.recordForm, 'store')) this.recordForm.store = store
      this.dialogVisible = true
    },
    openEdit(row) {
      if (!row) return
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再编辑')
      this.dialogMode = 'edit'
      this.dialogAction = '编辑'
      this.dialogTitle = `编辑${this.pageTitle}`
      this.currentRow = row
      this.dialogFields = this.config.formFields.length ? this.config.formFields : this.config.columns.slice(0, 8).map(column => inputField(column.key, column.label))
      this.recordForm = this.dialogFields.reduce((result, field) => {
        this.$set(result, field.key, row[field.key] || '')
        return result
      }, {})
      this.dialogVisible = true
    },
    openFollow() {
      const selected = this.requireOne()
      if (!selected) return
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再保存跟进')
      this.dialogMode = 'operation'
      this.dialogAction = '客户跟进'
      this.dialogTitle = '新增客户跟进记录'
      this.operationTip = '保存后将同步更新客户最后跟进时间、跟进状态和下次跟进计划。'
      this.dialogFields = [inputField('customerName', '客户名称'), dateField('followedAt', '跟进时间'), selectField('followStatus', '跟进状态', leadFollowStatuses), selectField('followType', '跟进类型', ['销售', '咨询', '回访', '探访', '投诉']), selectField('contactType', '接触方式', ['微信交流', '店外面谈', '电话交流', '来店参观']), dateField('nextFollowAt', '下次跟进时间'), textareaField('content', '跟进内容')]
      this.recordForm = this.emptyForm(this.dialogFields)
      this.recordForm.id = selected.id
      this.recordForm.customerName = this.displayName(selected)
      this.recordForm.followedAt = localDateTimeText()
      this.recordForm.followStatus = leadFollowStatuses.includes(selected.followStatus) ? selected.followStatus : '跟进中'
      this.dialogVisible = true
    },
    openOperation(action) {
      const selected = this.requireOne()
      if (!selected) return
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再操作')
      this.dialogMode = 'operation'
      this.dialogAction = action
      this.dialogTitle = action
      this.operationTip = `${action}将由后端校验权限与业务状态，并写入操作轨迹。`
      this.dialogFields = this.operationFields(action)
      this.recordForm = this.emptyForm(this.dialogFields)
      this.recordForm.id = selected.id
      this.recordForm.customerName = this.displayName(selected)
      this.dialogVisible = true
    },
    operationFields(action) {
      if (action.includes('分配') || action.includes('转让')) return [inputField('customerName', '客户名称'), selectField('assignee', '分配给', ['李顾问', '王顾问', '陈顾问']), selectField('store', '所属门店', ['中心广场旗舰店', '黄河路轻奢店']), textareaField('remark', '分配说明')]
      if (action === '转化') return [inputField('customerName', '客户名称'), selectField('store', '转化门店', ['中心广场旗舰店', '黄河路轻奢店']), textareaField('remark', '转化说明')]
      if (action === '关闭') return [inputField('customerName', '客户名称'), textareaField('content', '关闭原因')]
      if (action.includes('合同')) return [inputField('customerName', '客户名称'), inputField('contractNo', '合同编号'), selectField('packageName', '合同套餐', ['基础套餐', '修复套餐', '修养套餐']), inputField('contractAmount', '合同金额'), inputField('deposit', '定金金额'), dateField('signedAt', '签订日期', 'date')]
      if (action.includes('审核') || action.includes('授权')) return [inputField('customerName', '客户名称'), selectField('decision', '审核结果', ['同意', '驳回', '退回修改']), inputField('amount', '涉及金额'), textareaField('remark', '审核意见')]
      if (action.includes('发送')) return [inputField('customerName', '客户名称'), selectField('channel', '发送渠道', ['短信', '微信', '站内消息']), textareaField('content', '发送内容')]
      return [inputField('customerName', '客户名称'), selectField('result', '处理结果', ['确认执行', '暂缓处理', '退回修改']), textareaField('remark', '操作说明')]
    },
    emptyForm(fields) {
      return fields.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'dateRange' ? [] : '')
        return result
      }, {})
    },
    isPhoneField(field) {
      return Boolean(field && (
        /mobile|phone/i.test(String(field.key || '')) ||
        /手机号|手机号码|联系电话|客户电话|探访人电话/.test(String(field.label || ''))
      ))
    },
    normalizeFieldInput(field, value) {
      const text = String(value === undefined || value === null ? '' : value)
      return this.isPhoneField(field)
        ? text.replace(/\D/g, '').slice(0, 11)
        : text.slice(0, 100)
    },
    handleFilterInput(field, value) {
      const normalized = this.normalizeFieldInput(field, value)
      if (normalized !== value) this.$set(this.filters, field.key, normalized)
    },
    handleDialogInput(field, value) {
      const normalized = this.normalizeFieldInput(field, value)
      if (normalized !== value) this.$set(this.recordForm, field.key, normalized)
    },
    async saveRecord() {
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再保存')
      const missingRequired = this.dialogFields.find(field => this.isRequired(field) && !this.recordForm[field.key])
      if (missingRequired) {
        this.$message.warning(`请填写${missingRequired.label}`)
        return
      }
      const invalidPhone = this.dialogFields.find(field => (
        this.isPhoneField(field) &&
        this.recordForm[field.key] &&
        !/^1[3-9]\d{9}$/.test(String(this.recordForm[field.key]))
      ))
      if (invalidPhone) {
        this.$message.warning(`${invalidPhone.label}须为中国大陆 11 位手机号`)
        return
      }
      if (this.dialogAction === '客户跟进' || this.dialogAction === '客户跟踪') {
        if (!this.recordForm.followedAt || !this.recordForm.followStatus || !this.recordForm.content) {
          return this.$message.warning('请完整填写跟进时间、跟进状态和跟进内容')
        }
        if (this.recordForm.followStatus === '跟进中' && !this.recordForm.nextFollowAt) {
          return this.$message.warning('跟进中的线索必须填写下次跟进时间')
        }
      }
      this.saving = true
      try {
        if (this.dialogMode === 'operation') await performCustomerModuleAction(this.config.key, this.dialogAction, this.recordForm)
        else await saveCustomerModuleRecord(this.config.key, { ...this.recordForm, id: this.currentRow && this.currentRow.id })
        await this.loadData()
        this.dialogVisible = false
        this.$message.success(`${this.dialogAction || '记录'}已保存并写入操作轨迹`)
      } finally {
        this.saving = false
      }
    },
    async removeRows(rows = this.selection) {
      if (!rows.length) return this.$message.warning('请先选择要删除的记录')
      try {
        await this.$confirm(`确认删除选中的 ${rows.length} 条记录吗？该操作会保留审计轨迹。`, '删除确认', { type: 'warning' })
        await performCustomerModuleAction(this.config.key, '删除', { ids: rows.map(row => row.id) })
        const ids = rows.map(row => row.id)
        this.rows = this.rows.filter(row => !ids.includes(row.id))
        this.$message.success('记录已删除')
      } catch (error) {
        if (error !== 'cancel') this.$message.error('删除未完成')
      }
    },
    handleRowCommand(command, row) {
      this.selection = [row]
      if (command === 'follow') this.openFollow()
      if (command === 'history') this.openView(row)
      if (command === 'delete') this.removeRows([row])
    },
    openView(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    applyReminder(item) {
      if (item.stage && (this.config.stages || []).includes(item.stage)) {
        this.activeStage = item.stage
        this.pagination.page = 1
        this.$message.success(`已按“${item.label}”筛选当前门店的 ${item.count} 条客户记录`)
        return
      }
      this.$message.info(`“${item.label}”共 ${item.count} 条，数据仅按已录入档案统计。`)
    },
    async savePoints() {
      this.saving = true
      try {
        await savePointSettings(this.pointSettings)
        this.$message.success('15 项积分规则已保存')
      } finally {
        this.saving = false
      }
    },
    exportRows() {
      const header = this.config.columns.map(column => column.label)
      const content = this.filteredRows.map(row => this.config.columns.map(column => String(row[column.key] || '').replace(/"/g, '""')))
      const csv = [header, ...content].map(line => line.map(value => `"${value}"`).join(',')).join('\n')
      const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${this.filteredRows.length} 条当前查询结果`)
    },
    displayName(row) {
      return row.customerName || row.name || row.visitor || row.title || row.id
    },
    isRequired(field) {
      return field.required === true || ['customerName', 'name', 'mobile', 'visitor', 'title', 'content'].includes(field.key)
    },
    isMoneyColumn(key) {
      return /amount|balance/i.test(key)
    },
    money(value) {
      return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
    },
    tagType(value) {
      if (/成功|完成|转化|已处理|签约|启用|获取/.test(value)) return 'success'
      if (/失败|关闭|停用|紧急|未处理/.test(value)) return 'danger'
      if (/待|跟进|重要|草稿/.test(value)) return 'warning'
      return 'info'
    },
    tableIndex(index) {
      return (this.pagination.page - 1) * this.pagination.size + index + 1
    }
  }
}
</script>

<style lang="scss" scoped>
.customer-workbench { min-height: calc(100vh - 84px); padding: 22px; background: #f3f6fa; color: #25324a; }
.hero-panel { display: flex; justify-content: space-between; align-items: center; gap: 28px; padding: 26px 30px; border-radius: 16px; color: white; background: linear-gradient(125deg, #28241e 0%, #5f4b2d 56%, #a68045 100%); box-shadow: 0 14px 34px rgba(74, 55, 26, .2); }
.hero-copy { min-width: 0; }
.eyebrow { margin-bottom: 9px; color: #f3dfb7; font-size: 13px; font-weight: 700; letter-spacing: .7px; }
.hero-copy h1 { margin: 0 0 9px; font-size: 27px; line-height: 1.2; }
.hero-copy p { max-width: 760px; margin: 0; color: #f7efe0; font-size: 14px; line-height: 1.7; }
.hero-actions { display: flex; flex: 0 0 auto; align-items: center; gap: 10px; }
.metric-strip, .point-overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; margin-top: 16px; overflow: hidden; border: 1px solid #e4eaf2; border-radius: 12px; background: #e4eaf2; }
.metric-item, .point-overview > div { padding: 18px 22px; background: white; }
.metric-item span, .point-overview span { display: block; color: #718096; font-size: 12px; }
.metric-item strong, .point-overview strong { display: block; margin: 7px 0 3px; color: #8c6a36; font-size: 25px; }
.tag-overview { display: flex; gap: 24px; align-items: center; margin-bottom: 16px; padding: 18px 22px; border: 1px solid #eadfcf; border-radius: 12px; background: linear-gradient(135deg, #fffdf9, #f8f3e9); }
.tag-overview__copy { min-width: 240px; }
.tag-overview__copy h2 { margin: 0 0 5px; color: #2f3c50; font-size: 17px; }
.tag-overview__copy p { margin: 0; color: #7d8898; font-size: 12px; }
.tag-cloud { display: flex; flex: 1; flex-wrap: wrap; gap: 8px; }
.tag-cloud b { margin-left: 5px; color: #9b743c; }
.empty-tag-tip { color: #98a2b1; font-size: 13px; }
.metric-item small { color: #9aa7b6; }
.point-overview { grid-template-columns: repeat(3, 1fr) auto; align-items: stretch; }
.point-overview .el-button { margin: 17px; }
.stage-strip { display: flex; gap: 8px; margin-top: 16px; overflow-x: auto; }
.stage-strip button { display: flex; flex: 0 0 auto; align-items: center; gap: 8px; padding: 10px 14px; border: 1px solid #dfe6ee; border-radius: 9px; color: #5e6c7f; background: white; cursor: pointer; }
.stage-strip button b { min-width: 22px; padding: 2px 5px; border-radius: 10px; color: #8492a6; background: #eef2f6; font-size: 11px; }
.stage-strip button.active { border-color: #19786f; color: #12675f; background: #ecf9f7; box-shadow: 0 4px 12px rgba(25, 120, 111, .12); }
.stage-strip button.active b { color: white; background: #19786f; }
.reminder-strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 12px; }
.reminder-strip > div { position: relative; display: grid; grid-template-columns: 32px 1fr auto; align-items: center; gap: 4px 9px; padding: 13px 15px; border: 1px solid #e5eaf0; border-radius: 10px; background: white; cursor: pointer; transition: .2s; }
.reminder-strip > div:hover { transform: translateY(-2px); border-color: #b8dcd8; box-shadow: 0 7px 18px rgba(27, 77, 95, .09); }
.reminder-strip i { grid-row: 1 / 3; display: grid; width: 32px; height: 32px; place-items: center; border-radius: 8px; color: #19786f; background: #eaf7f5; }
.reminder-strip span { color: #445267; font-size: 12px; }
.reminder-strip strong { color: #e06d3d; font-size: 18px; }
.reminder-strip small { color: #9aa6b3; font-size: 11px; }
.filter-card, .table-card, .point-card { margin-top: 16px; border: none; border-radius: 12px; }
.card-heading, .table-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.card-heading h2 { margin: 0 0 4px; color: #25324a; font-size: 16px; }
.card-heading p { margin: 0; color: #8b98a9; font-size: 12px; }
.filter-form { margin-bottom: -12px; }
.filter-form ::v-deep .el-form-item { margin-bottom: 16px; }
.filter-form ::v-deep .el-form-item__label { padding-bottom: 5px; color: #607087; font-size: 12px; line-height: 18px; }
.full-control { width: 100%; }
.filter-toggle { display: block; margin: 5px auto -5px; border: 0; color: #19786f; background: transparent; cursor: pointer; }
.table-toolbar { align-items: flex-start; }
.business-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.business-actions .el-button + .el-button { margin-left: 0; }
.selection-tip { flex: 0 0 auto; padding-top: 7px; color: #7d8999; font-size: 12px; }
.table-card ::v-deep .el-card__body { padding-top: 0; }
.table-card ::v-deep .el-table th { color: #43536a; background: #f3f7fa; }
.table-card ::v-deep .el-table td { color: #526174; }
.more-link { margin-left: 10px; color: #19786f; font-size: 12px; cursor: pointer; }
.money { color: #cf6839; font-weight: 700; }
.pagination-row { display: flex; justify-content: space-between; align-items: center; padding-top: 18px; color: #8491a2; font-size: 12px; }
.point-card { margin-bottom: 20px; }
.point-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 24px; }
.point-rule { display: grid; grid-template-columns: 34px minmax(130px, 1fr) 116px 135px 24px; align-items: center; gap: 10px; min-height: 68px; border-bottom: 1px solid #edf0f4; }
.rule-index { color: #a0acb9; font-size: 12px; }
.rule-name strong, .rule-name span { display: block; }
.rule-name strong { color: #3e4d62; font-size: 13px; }
.rule-name span { margin-top: 4px; color: #9aa6b4; font-size: 11px; }
.rule-unit { color: #718096; font-size: 12px; }
.dialog-alert { margin-bottom: 20px; }
.record-form { padding-right: 10px; }
.detail-drawer { padding: 0 22px 28px; }
.detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; font-size: 19px; font-weight: 700; }
.detail-drawer h3 { margin: 25px 0 18px; font-size: 15px; }
.audit-empty { padding: 12px 14px; border: 1px dashed #d8c7a5; border-radius: 8px; color: #7c6c53; background: #fffaf1; font-size: 13px; line-height: 1.7; }
@media (max-width: 1200px) {
  .reminder-strip { grid-template-columns: repeat(3, 1fr); }
  .point-grid { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .customer-workbench { padding: 12px; }
  .hero-panel, .hero-actions, .card-heading, .table-toolbar, .pagination-row { align-items: flex-start; flex-direction: column; }
  .hero-actions { width: 100%; }
  .metric-strip, .point-overview { grid-template-columns: repeat(2, 1fr); }
  .reminder-strip { grid-template-columns: 1fr; }
  .point-rule { grid-template-columns: 30px 1fr; padding: 12px 0; }
}
</style>
