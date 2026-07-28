<template>
  <div class="sales-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i :class="config.icon" /> 销售管理 · 实时业务数据</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-actions">
        <el-tag type="success" effect="plain"><i class="el-icon-circle-check" /> 权限与门店已对齐</el-tag>
        <el-button icon="el-icon-refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button type="primary" icon="el-icon-download" @click="exportRows">导出当前结果</el-button>
      </div>
    </section>

    <section class="metric-strip">
      <div v-for="(metric, index) in metrics" :key="metric.label" class="metric-item">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.money ? `¥ ${money(metric.value)}` : metric.value }}</strong>
        <small><i :class="index === 0 ? 'el-icon-data-analysis' : 'el-icon-time'" /> {{ metric.tip }}</small>
      </div>
    </section>

    <section v-if="statusPipeline.length" class="status-pipeline">
      <button v-for="(status, index) in statusPipeline" :key="status" :class="{ active: activeStatus === status }" @click="activeStatus = status">
        <b>{{ index + 1 }}</b><span>{{ status }}</span><em>{{ statusCount(status) }}</em>
      </button>
    </section>

    <el-card shadow="never" class="filter-card">
      <div slot="header" class="card-heading">
        <div><h2>查询条件</h2><p>保留本页在原系统中的专属检索项</p></div>
        <div>
          <el-button type="text" icon="el-icon-delete" @click="resetFilters">清空</el-button>
          <el-button type="primary" size="small" icon="el-icon-search" @click="search">查询</el-button>
        </div>
      </div>
      <el-form label-position="top" class="filter-form">
        <el-row :gutter="16">
          <el-col v-for="field in visibleFilters" :key="field.key" :xl="4" :lg="6" :md="8" :sm="12" :xs="24">
            <el-form-item :label="field.label">
              <el-input v-if="field.type === 'input'" v-model.trim="filters[field.key]" clearable :placeholder="`请输入${field.label}`" @keyup.enter.native="search" />
              <el-select
                v-else-if="field.type === 'select'"
                v-model="filters[field.key]"
                clearable
                filterable
                :disabled="filterDisabled(field)"
                :placeholder="filterPlaceholder(field)"
                class="full-control"
                @change="handleFilterChange(field)"
              >
                <el-option v-for="option in filterOptions(field)" :key="option" :label="option" :value="option" />
              </el-select>
              <el-date-picker v-else-if="field.type === 'dateRange'" v-model="filters[field.key]" type="daterange" value-format="yyyy-MM-dd" start-placeholder="开始日期" end-placeholder="结束日期" range-separator="至" class="full-control" />
              <small v-if="field.dependsOn" class="field-hint">{{ filterDependencyHint(field) }}</small>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div v-if="config.storeOptions || config.filterTips" class="contract-filter-meta">
        <div v-if="config.storeOptions" class="store-selector">
          <span class="meta-label">门店</span>
          <el-radio-group v-model="storeScope" size="small">
            <el-radio-button v-for="store in availableStoreOptions" :key="store" :label="store">{{ store }}</el-radio-button>
          </el-radio-group>
        </div>
        <div v-if="config.filterTips" class="formula-tips">
          <span v-for="tip in config.filterTips" :key="tip"><i class="el-icon-info" />{{ tip }}</span>
        </div>
      </div>
      <button v-if="config.filters.length > filterLimit" type="button" class="filter-toggle" @click="filtersExpanded = !filtersExpanded">
        {{ filtersExpanded ? '收起更多条件' : `展开更多条件（${config.filters.length - filterLimit}）` }}
        <i :class="filtersExpanded ? 'el-icon-arrow-up' : 'el-icon-arrow-down'" />
      </button>
    </el-card>

    <el-card shadow="never" class="table-card">
      <div slot="header" class="table-toolbar">
        <div class="business-actions">
          <el-button
            v-for="(action, index) in visibleActions"
            :key="action"
            size="small"
            :type="index === 0 ? 'primary' : action === '删除' ? 'danger' : 'default'"
            :plain="index !== 0"
            :icon="actionIcon(action)"
            @click="handleAction(action)"
          >{{ action }}</el-button>
        </div>
        <div class="selection-tip"><i class="el-icon-s-order" /> 已选 {{ selection.length }} 条 · 共 {{ filteredRows.length }} 条</div>
      </div>

      <el-table v-loading="loading" :data="pagedRows" border stripe height="520" highlight-current-row @selection-change="selection = $event">
        <el-table-column v-if="visibleActions.length" type="selection" width="45" fixed="left" />
        <el-table-column v-if="config.lineColumns" type="expand" width="44" fixed="left">
          <template slot-scope="scope">
            <div class="expand-panel">
              <div class="expand-heading"><strong>{{ lineTitle }}</strong><span>单据：{{ recordNo(scope.row) }}</span></div>
              <el-table :data="scope.row.lineItems" size="mini" border>
                <el-table-column v-for="column in config.lineColumns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 100">
                  <template slot-scope="lineScope">
                    <span v-if="column.money" class="money">¥ {{ money(lineScope.row[column.key]) }}</span>
                    <span v-else>{{ lineScope.row[column.key] }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column type="index" label="序号" width="58" fixed="left" :index="tableIndex" />
        <el-table-column v-for="column in config.columns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 110" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-tag v-if="column.tag" size="mini" :type="tagType(scope.row[column.key])">{{ scope.row[column.key] }}</el-tag>
            <span v-else-if="column.money" class="money">¥ {{ money(scope.row[column.key]) }}</span>
            <span v-else>{{ scope.row[column.key] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="155" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="openDetails(scope.row)">详情</el-button>
            <el-button v-if="canUseAction('编辑')" type="text" @click="openEdit(scope.row)">编辑</el-button>
            <el-dropdown v-if="canUseAction('打印') || canUseAction('删除')" trigger="click" @command="command => handleRowCommand(command, scope.row)">
              <span class="more-link">更多<i class="el-icon-arrow-down" /></span>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item v-if="canUseAction('打印')" command="print">打印单据</el-dropdown-item>
                <el-dropdown-item v-if="canUseAction('删除')" command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="pageTitle === '合同管理'" class="contract-summary">
        <strong>合同汇总</strong>
        <span>成交金额 <b>¥ {{ money(contractSummary.dealAmount) }}</b></span>
        <span>已收款 <b>¥ {{ money(contractSummary.receivedAmount) }}</b></span>
        <span>退款 <b>¥ {{ money(contractSummary.refundAmount) }}</b></span>
        <span>欠款 <b>¥ {{ money(contractSummary.debtAmount) }}</b></span>
        <span>未入账 <b>¥ {{ money(contractSummary.unpostedAmount) }}</b></span>
        <span>应收 <b>¥ {{ money(contractSummary.receivableAmount) }}</b></span>
      </div>
      <div class="pagination-row">
        <span>显示第 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
        <el-pagination background layout="prev, pager, next, sizes" :current-page.sync="pagination.page" :page-size.sync="pagination.size" :page-sizes="[10, 20, 50, 100]" :total="filteredRows.length" />
      </div>
    </el-card>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="860px" top="5vh" :close-on-click-modal="false">
      <el-alert v-if="dialogMode === 'audit' || dialogMode === 'operation'" :title="dialogTip" type="info" :closable="false" show-icon class="dialog-alert" />
      <el-tabs v-model="dialogTab">
        <el-tab-pane :label="dialogMode === 'audit' ? '审批信息' : '基本信息'" name="base">
          <el-form ref="recordForm" :model="recordForm" label-width="118px" class="record-form">
            <el-row :gutter="18">
              <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
                <el-form-item :label="field.label" :required="field.required">
                  <el-input v-if="field.type === 'input'" v-model.trim="recordForm[field.key]" :placeholder="`请输入${field.label}`" />
                  <el-input v-else-if="field.type === 'textarea'" v-model.trim="recordForm[field.key]" type="textarea" :rows="3" :placeholder="`请输入${field.label}`" />
                  <el-select
                    v-else-if="field.type === 'select'"
                    v-model="recordForm[field.key]"
                    clearable
                    filterable
                    :disabled="dialogFieldDisabled(field)"
                    :placeholder="dialogFieldPlaceholder(field)"
                    class="full-control"
                    @change="handleDialogFieldChange(field)"
                  >
                    <el-option v-for="option in dialogFieldOptions(field)" :key="option" :label="option" :value="option" />
                  </el-select>
                  <el-date-picker v-else-if="field.type === 'date'" v-model="recordForm[field.key]" :type="field.dateType || 'date'" value-format="yyyy-MM-dd HH:mm:ss" placeholder="请选择" class="full-control" />
                  <el-input-number v-else-if="field.type === 'number'" v-model="recordForm[field.key]" :min="0" :precision="field.precision" controls-position="right" class="full-control" @change="recalculateLines" />
                  <el-switch v-else-if="field.type === 'switch'" v-model="recordForm[field.key]" active-text="是" inactive-text="否" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
        <el-tab-pane v-if="config.lineColumns && dialogMode !== 'audit' && dialogMode !== 'operation'" :label="lineTitle" name="lines">
          <div class="line-editor-head">
            <div><strong>{{ lineTitle }}</strong><span>数量、价格和折扣金额自动计算</span></div>
            <el-button type="primary" size="small" icon="el-icon-plus" @click="addLine">添加明细</el-button>
          </div>
          <el-table :data="lineItems" border size="mini" max-height="350">
            <el-table-column label="项目/商品名称" min-width="160"><template slot-scope="scope"><el-input v-model="scope.row.itemName" size="mini" /></template></el-table-column>
            <el-table-column label="单位" width="90"><template slot-scope="scope"><el-input v-model="scope.row.unit" size="mini" /></template></el-table-column>
            <el-table-column label="单价" width="120"><template slot-scope="scope"><el-input-number v-model="scope.row.price" :min="0" :precision="2" size="mini" controls-position="right" @change="recalculateLines" /></template></el-table-column>
            <el-table-column label="折后单价" width="120"><template slot-scope="scope"><el-input-number v-model="scope.row.discountPrice" :min="0" :precision="2" size="mini" controls-position="right" @change="recalculateLines" /></template></el-table-column>
            <el-table-column label="数量" width="105"><template slot-scope="scope"><el-input-number v-model="scope.row.quantity" :min="1" :precision="0" size="mini" controls-position="right" @change="recalculateLines" /></template></el-table-column>
            <el-table-column label="金额" width="110"><template slot-scope="scope"><span class="money">¥ {{ money(scope.row.total) }}</span></template></el-table-column>
            <el-table-column label="操作" width="70"><template slot-scope="scope"><el-button type="text" class="danger-link" @click="removeLine(scope.$index)">删除</el-button></template></el-table-column>
          </el-table>
          <div class="line-total"><span>总数量：<b>{{ lineQuantity }}</b></span><span>合计金额：<strong>¥ {{ money(lineAmount) }}</strong></span></div>
        </el-tab-pane>
      </el-tabs>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="dialogMode === 'create' && pageTitle === '合同管理'" :loading="saving" @click="saveRecord(false)">保存草稿</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord(true)">{{ dialogMode === 'audit' ? '确认审核' : '保存并提交' }}</el-button>
      </div>
    </el-dialog>

    <el-drawer title="销售业务详情" :visible.sync="drawerVisible" size="560px">
      <div v-if="currentRow" class="detail-drawer">
        <div class="detail-head"><span>{{ displayName(currentRow) }}</span><el-tag size="small" type="success">门店权限内数据</el-tag></div>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item v-for="column in config.columns" :key="column.key" :label="column.label">
            <span v-if="column.money">¥ {{ money(currentRow[column.key]) }}</span><span v-else>{{ currentRow[column.key] }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <template v-if="config.lineColumns">
          <h3>{{ lineTitle }}</h3>
          <el-table :data="currentRow.lineItems" border size="mini"><el-table-column prop="itemName" label="名称" /><el-table-column prop="quantity" label="数量" width="70" /><el-table-column prop="total" label="金额" width="100" /></el-table>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getSalesPageConfig } from '@/config/sales-pages'
import { canUseSalesAction, visibleSalesActions } from '@/config/sales-permissions'
import { auditSalesModuleRecord, getSalesModuleData, performSalesModuleAction, saveSalesModuleRecord } from '@/api/erp-sales'

const inputField = (key, label, required = false) => ({ key, label, type: 'input', required })
const textareaField = (key, label, required = false) => ({ key, label, type: 'textarea', required })
const selectField = (key, label, options, required = false) => ({ key, label, type: 'select', options, required })

export default {
  name: 'SalesWorkbench',
  data() {
    return {
      loading: false,
      saving: false,
      filtersExpanded: false,
      filters: {},
      storeScope: '全部',
      storeOptions: [],
      rows: [],
      selection: [],
      activeStatus: '全部',
      pagination: { page: 1, size: 10 },
      dialogVisible: false,
      dialogMode: 'create',
      dialogAction: '',
      dialogTitle: '',
      dialogTip: '',
      dialogFields: [],
      dialogTab: 'base',
      recordForm: {},
      lineItems: [],
      currentRow: null,
      drawerVisible: false
    }
  },
  computed: {
    ...mapGetters(['permissions', 'roles']),
    pageTitle() {
      return this.$route.meta.title
    },
    config() {
      return getSalesPageConfig(this.pageTitle)
    },
    visibleActions() {
      return visibleSalesActions(
        this.config.key,
        this.config.actions,
        this.permissions,
        this.roles
      )
    },
    availableStoreOptions() {
      const names = this.storeOptions.map(item => item.name)
      return ['全部', ...names]
    },
    filterLimit() {
      return this.pageTitle === '合同管理' ? 12 : 8
    },
    visibleFilters() {
      return this.filtersExpanded ? this.config.filters : this.config.filters.slice(0, this.filterLimit)
    },
    statusPipeline() {
      const pipelines = {
        '合同管理': ['全部', '待完善', '待提交', '待审核', '审核通过', '合同已结束', '合同中途结束', '驳回', '合同已作废'],
        '商品销售': ['全部', '未支付', '已支付', '已取消', '已付未出库', '已出库', '已出库未支付', '换货退货'],
        '套餐管理': ['全部', '未提交', '审核中', '已启用', '已推荐'],
        '优惠管理': ['全部', '待审核', '未使用', '已使用', '已过期', '已停用'],
        '赠送项目申请': ['全部', '未提交', '审核中', '待出库', '已出库', '已退货']
      }
      return pipelines[this.pageTitle] || []
    },
    filteredRows() {
      let data = this.rows
      if (this.config.storeOptions && this.storeScope !== '全部') data = data.filter(row => row.store === this.storeScope)
      if (this.activeStatus !== '全部') {
        const statusAliases = {
          '已启用': ['启用', '是'],
          '已推荐': ['是'],
          '待审核': ['待审核', '未提交'],
          '待出库': ['待出库', '已付未出库']
        }
        const expected = statusAliases[this.activeStatus] || [this.activeStatus]
        data = data.filter(row => Object.values(row).some(value => expected.includes(String(value))))
      }
      const entries = Object.entries(this.filters).filter(([, value]) => value !== '' && value !== null && (!Array.isArray(value) || value.length))
      if (!entries.length) return data
      return data.filter(row => entries.every(([key, value]) => {
        if (Array.isArray(value)) return true
        if (key === 'checkedIn') return value === '已入住' ? row.checkedIn === '是' : row.checkedIn === '否'
        if (key === 'contractType' && value === '月子合同') return row.contractType === '月子护理'
        return String(row[key] || row.customerName || row.saleNo || '').includes(String(value))
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
      const labels = this.config.metrics || ['记录总数', '待处理', '本月新增', '已完成']
      return labels.map((label, index) => ({
        label,
        value: this.metricValue(label, index),
        money: /金额|销售额|欠款|剩余/.test(label),
        tip: '当前账号可见范围'
      }))
    },
    lineTitle() {
      if (this.pageTitle.includes('套餐')) return '项目明细'
      if (this.pageTitle === '赠送管理') return '赠送物料明细'
      if (this.pageTitle === '赠送项目申请') return '赠送品项明细'
      return '销售商品明细'
    },
    lineQuantity() {
      return this.lineItems.reduce((sum, item) => sum + Number(item.quantity || 0), 0)
    },
    lineAmount() {
      return this.lineItems.reduce((sum, item) => sum + Number(item.total || 0), 0)
    },
    contractSummary() {
      const keys = ['dealAmount', 'receivedAmount', 'refundAmount', 'debtAmount', 'unpostedAmount', 'receivableAmount']
      return keys.reduce((summary, key) => {
        summary[key] = this.filteredRows.reduce((total, row) => total + Number(row[key] || 0), 0)
        return summary
      }, {})
    }
  },
  watch: {
    '$route.meta.title': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    }
  },
  methods: {
    canUseAction(action) {
      return canUseSalesAction(
        this.config.key,
        action,
        this.permissions,
        this.roles
      )
    },
    initializePage() {
      this.filters = this.config.filters.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'dateRange' ? [] : '')
        return result
      }, {})
      Object.entries(this.config.defaultFilters || {}).forEach(([key, value]) => { this.$set(this.filters, key, value) })
      if (this.pageTitle === '合同管理') this.$set(this.filters, 'signedRange', this.recentDateRange())
      this.storeScope = '全部'
      this.activeStatus = '全部'
      this.filtersExpanded = false
      this.pagination.page = 1
      this.loadData()
    },
    async loadData() {
      this.loading = true
      try {
        const params = { ...this.filters }
        if (this.storeScope && this.storeScope !== '全部') params.store = this.storeScope
        if (this.activeStatus && this.activeStatus !== '全部') params.status = this.activeStatus
        const response = await getSalesModuleData(this.config.key, params)
        this.rows = response.data.list || []
        this.storeOptions = response.data.stores || []
        ;['store', 'stayStore'].forEach(key => {
          if (!this.filters[key]) return
          const matched = this.storeOptions.find(item => this.storeMatches(this.filters[key], item.name))
          if (matched) this.filters[key] = matched.name
        })
        if (this.storeScope !== '全部' && !this.storeOptions.some(item => item.name === this.storeScope)) {
          this.storeScope = '全部'
        }
      } finally {
        this.loading = false
      }
    },
    async search() {
      this.pagination.page = 1
      await this.loadData()
      this.$message.success('查询完成')
    },
    resetFilters() {
      Object.keys(this.filters).forEach(key => { this.filters[key] = Array.isArray(this.filters[key]) ? [] : '' })
      Object.entries(this.config.defaultFilters || {}).forEach(([key, value]) => { this.filters[key] = value })
      if (this.pageTitle === '合同管理') this.filters.signedRange = this.recentDateRange()
      this.storeScope = '全部'
      this.activeStatus = '全部'
      this.pagination.page = 1
    },
    filterOptions(field) {
      if (field.key === 'store' || field.key === 'stayStore') {
        return this.storeOptions.map(item => item.name)
      }
      if (!field.optionsByDependency) return field.options || []
      return field.optionsByDependency[this.filters[field.dependsOn]] || []
    },
    filterDisabled(field) {
      return Boolean(field.optionsByDependency && !this.filterOptions(field).length)
    },
    filterPlaceholder(field) {
      if (!field.dependsOn) return '请选择'
      const dependency = this.config.filters.find(item => item.key === field.dependsOn)
      return this.filterDisabled(field) ? `请先选择${dependency ? dependency.label : '上级类型'}` : '请选择'
    },
    filterDependencyHint(field) {
      if (this.filters[field.dependsOn] === '项目销售') return '项目销售对应项目分类'
      if (this.filters[field.dependsOn] === '物料销售') return '物料销售对应物料分类'
      return '仅项目销售、物料销售可选择商品类型'
    },
    handleFilterChange(field) {
      this.config.filters
        .filter(item => item.dependsOn === field.key)
        .forEach(item => {
          if (!this.filterOptions(item).includes(this.filters[item.key])) this.filters[item.key] = ''
        })
    },
    dialogFieldOptions(field) {
      if (!field.optionsByDependency) return field.options || []
      return field.optionsByDependency[this.recordForm[field.dependsOn]] || []
    },
    dialogFieldDisabled(field) {
      return Boolean(field.optionsByDependency && !this.dialogFieldOptions(field).length)
    },
    dialogFieldPlaceholder(field) {
      if (!field.dependsOn) return '请选择'
      const dependency = this.dialogFields.find(item => item.key === field.dependsOn)
      return this.dialogFieldDisabled(field) ? `请先选择${dependency ? dependency.label : '上级类型'}` : '请选择'
    },
    handleDialogFieldChange(field) {
      this.dialogFields
        .filter(item => item.dependsOn === field.key)
        .forEach(item => {
          if (!this.dialogFieldOptions(item).includes(this.recordForm[item.key])) this.recordForm[item.key] = ''
        })
    },
    storeMatches(requested, actual) {
      if (requested === actual) return true
      if (String(requested).includes('黄河路')) return String(actual).includes('黄河路')
      if (String(requested).includes('中心广场') || String(requested).includes('建设路')) {
        return String(actual).includes('中心广场') || String(actual).includes('建设路')
      }
      return false
    },
    handleAction(action) {
      if (!this.canUseAction(action)) return this.$message.error('当前账号没有此操作权限')
      if (action === '导出') return this.exportRows()
      if (action === '打印') return this.printRows()
      if (['添加', '项目销售', '服务销售', '物料销售', '卡类销售', '膳食销售', '服务赠送', '物料赠送', '卡类赠送'].includes(action)) return this.openCreate(action)
      if (action === '编辑') return this.openEdit(this.requireOne())
      if (action === '删除') return this.removeRows()
      if (['审核', '批量审核', '流程审批', '折扣率审核'].includes(action)) return this.openAudit(action)
      this.openOperation(action)
    },
    actionIcon(action) {
      if (/添加|销售|赠送/.test(action)) return 'el-icon-plus'
      if (action === '编辑') return 'el-icon-edit'
      if (action === '删除') return 'el-icon-delete'
      if (/审核|审批/.test(action)) return 'el-icon-s-check'
      if (action === '导出') return 'el-icon-download'
      if (action === '打印') return 'el-icon-printer'
      return 'el-icon-setting'
    },
    requireOne() {
      const row = this.selection[0]
      if (!row) this.$message.warning('请先选择一条销售业务记录')
      return row
    },
    openCreate(action) {
      this.dialogMode = 'create'
      this.dialogAction = action
      this.dialogTitle = `${action}${action === '添加' ? this.pageTitle : ''}`
      this.dialogFields = this.config.formFields
      this.recordForm = this.emptyForm(this.dialogFields)
      if (action.includes('物料')) this.recordForm.saleType = '物料销售'
      if (action.includes('项目') || action.includes('服务')) this.recordForm.saleType = '项目销售'
      if (action.includes('卡类')) this.recordForm.saleType = '卡类销售'
      if (action.includes('膳食')) this.recordForm.saleType = '膳食销售'
      if (action.includes('赠送')) this.recordForm.giftType = '签单赠送'
      this.lineItems = this.config.lineColumns ? [this.createEditableLine()] : []
      this.dialogTab = 'base'
      this.currentRow = null
      this.dialogVisible = true
    },
    openEdit(row) {
      if (!row) return
      this.dialogMode = 'edit'
      this.dialogAction = '编辑'
      this.dialogTitle = `编辑${this.pageTitle}`
      this.dialogFields = this.config.formFields
      this.currentRow = row
      this.recordForm = this.dialogFields.reduce((result, field) => {
        this.$set(result, field.key, row[field.key] !== undefined ? row[field.key] : field.type === 'switch' ? false : field.type === 'number' ? 0 : '')
        return result
      }, {})
      this.lineItems = row.lineItems ? row.lineItems.map(item => ({ ...item })) : []
      this.dialogTab = 'base'
      this.dialogVisible = true
    },
    openAudit(action) {
      if (!this.selection.length) return this.$message.warning('请先选择需要审核的记录')
      this.dialogMode = 'audit'
      this.dialogAction = action
      this.dialogTitle = `${action} · 已选 ${this.selection.length} 条`
      this.dialogTip = '审核结果、下一节点、审核人与抄送信息会写入审批记录。'
      this.dialogFields = this.config.auditFields || [selectField('auditResult', '审核结果', ['通过', '驳回'], true), textareaField('auditRemark', '审核意见', true)]
      this.recordForm = this.emptyForm(this.dialogFields)
      this.dialogTab = 'base'
      this.dialogVisible = true
    },
    openOperation(action) {
      const row = this.requireOne()
      if (!row) return
      this.dialogMode = 'operation'
      this.dialogAction = action
      this.dialogTitle = action
      this.dialogTip = `${action}将按当前账号的门店和按钮权限更新业务状态，并写入审计日志。`
      this.dialogFields = this.operationFields(action)
      this.recordForm = this.emptyForm(this.dialogFields)
      this.recordForm.documentName = this.displayName(row)
      this.dialogTab = 'base'
      this.dialogVisible = true
    },
    operationFields(action) {
      if (action === '分发') return [inputField('documentName', '优惠券'), inputField('customerName', '客户姓名', true), inputField('mobile', '手机号', true), inputField('quantity', '发放数量', true), textareaField('remark', '发放说明')]
      if (action === '变更' || action === '合同变更') return [inputField('documentName', '合同编号'), selectField('changeType', '变更类型', ['入住日期变更', '房型变更', '套餐变更', '合同金额变更', '签单信息变更'], true), inputField('effectiveDate', '生效日期', true), textareaField('changeReason', '变更原因', true)]
      if (action === '作废') return [inputField('documentName', '合同编号'), inputField('invalidDate', '作废日期', true), textareaField('invalidReason', '作废原因', true)]
      if (action === '设置' || action === '设置套餐') return [inputField('documentName', '合同编号'), inputField('packageName', '套餐名称', true), inputField('packageDays', '套餐天数', true), inputField('packageAmount', '套餐金额', true), textareaField('remark', '设置说明')]
      if (action === '套餐升级') return [inputField('documentName', '合同编号'), inputField('upgradePackage', '升级套餐', true), inputField('upgradeAmount', '升级金额', true), inputField('receivedAmount', '本次收款'), textareaField('remark', '升级说明')]
      if (action === '膳食套餐') return [inputField('documentName', '合同编号'), selectField('mealPackage', '膳食套餐', ['排餐', '点餐'], true), textareaField('remark', '调整说明')]
      if (action === '编辑模板') return [inputField('documentName', '合同编号'), selectField('templateName', '合同模板', ['月子合同模板', '婴儿托管模板', '试住合同模板', '续住合同模板', '小月子合同模板', '到家合同模板'], true), textareaField('remark', '模板说明')]
      if (action === '远程签约') return [inputField('documentName', '合同编号'), inputField('signMobile', '签约手机号', true), inputField('validMinutes', '链接有效分钟数', true), textareaField('remark', '发送说明')]
      if (action === '取消') return [inputField('documentName', '合同编号'), selectField('cancelType', '取消类型', ['合同中途结束', '合同作废'], true), textareaField('cancelReason', '取消原因', true)]
      if (action.includes('收款')) return [inputField('documentName', '业务单据'), selectField('paymentMethod', '支付方式', ['现金', 'POS机刷卡', '支付宝付款', '微信结算'], true), inputField('amount', '收款金额', true), textareaField('remark', '收款备注')]
      if (/出库|退货/.test(action)) return [inputField('documentName', '业务单据'), selectField('warehouse', '业务仓库', ['五楼总库', '销售部仓库', '产康部仓库'], true), inputField('operator', '经办人'), textareaField('remark', '处理说明')]
      if (action.includes('介绍分配')) return [inputField('documentName', '业务单据'), inputField('introducer', '介绍人', true), inputField('introducerMobile', '介绍电话'), textareaField('remark', '分配说明')]
      return [inputField('documentName', '业务单据'), selectField('result', '处理结果', ['确认执行', '暂缓处理', '退回修改'], true), textareaField('remark', '操作说明')]
    },
    emptyForm(fields) {
      return fields.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'switch' ? false : field.type === 'number' ? 0 : '')
        return result
      }, {})
    },
    createEditableLine() {
      return { id: `line-${Date.now()}-${Math.random()}`, itemName: '', unit: '项', price: 0, discountPrice: 0, quantity: 1, total: 0, validDays: 30, warehouse: '' }
    },
    addLine() {
      this.lineItems.push(this.createEditableLine())
    },
    removeLine(index) {
      this.lineItems.splice(index, 1)
    },
    recalculateLines() {
      this.lineItems.forEach(item => { item.total = Number(item.discountPrice || item.price || 0) * Number(item.quantity || 0) })
      if (Object.prototype.hasOwnProperty.call(this.recordForm, 'totalAmount')) this.recordForm.totalAmount = this.lineAmount
      if (Object.prototype.hasOwnProperty.call(this.recordForm, 'packageAmount') && this.pageTitle.includes('套餐')) this.recordForm.packageAmount = this.lineAmount
    },
    async saveRecord(submit) {
      const missing = this.dialogFields.find(field => field.required && (this.recordForm[field.key] === '' || this.recordForm[field.key] === null))
      if (missing) return this.$message.warning(`请填写${missing.label}`)
      if (this.config.lineColumns && this.dialogMode !== 'audit' && this.dialogMode !== 'operation' && !this.lineItems.length) return this.$message.warning(`请至少添加一条${this.lineTitle}`)
      this.saving = true
      try {
        if (this.dialogMode === 'audit') {
          await auditSalesModuleRecord(this.config.key, { ...this.recordForm, action: this.dialogAction, ids: this.selection.map(row => row.id) })
          this.selection.forEach(row => { if (row.auditStatus !== undefined) row.auditStatus = this.recordForm.auditResult === '通过' ? '审核通过' : '审核不通过' })
        } else if (this.dialogMode === 'operation') {
          await performSalesModuleAction(this.config.key, this.dialogAction, { ...this.recordForm, ids: this.selection.map(row => row.id) })
          this.applyActionStatus(this.dialogAction)
        } else {
          await saveSalesModuleRecord(this.config.key, { ...this.recordForm, lineItems: this.lineItems, submit, id: this.currentRow && this.currentRow.id })
          await this.loadData()
        }
        if (this.dialogMode === 'audit' || this.dialogMode === 'operation') await this.loadData()
        this.dialogVisible = false
        this.$message.success(`${this.dialogAction || '销售记录'}已${submit ? '保存并提交' : '保存为草稿'}`)
      } finally {
        this.saving = false
      }
    },
    applyActionStatus(action) {
      const statusMap = { '提交': '待审核', '撤回': '已撤回', '反审核': '待提交', '取消': '合同中途结束', '启用': '启用', '出库': '已出库', '收款': '已支付', '新增收款': '已支付', '退货': '已退货', '取消退货': '已支付', '作废': '合同已作废', '停用': '已停用' }
      const value = statusMap[action]
      if (!value) return
      this.selection.forEach(row => {
        const key = action === '出库' ? 'outboundStatus' : /收款|退货/.test(action) ? 'paymentStatus' : action === '启用' ? 'enabled' : action === '停用' ? 'status' : 'auditStatus'
        if (row[key] !== undefined) row[key] = value
      })
    },
    async removeRows(rows = this.selection) {
      if (!rows.length) return this.$message.warning('请先选择要删除的记录')
      try {
        await this.$confirm(`确认删除选中的 ${rows.length} 条记录吗？操作会保留审计轨迹。`, '删除确认', { type: 'warning' })
        await performSalesModuleAction(this.config.key, '删除', { ids: rows.map(row => row.id) })
        await this.loadData()
        this.$message.success('业务记录已删除')
      } catch (error) {
        if (error !== 'cancel') this.$message.error('删除未完成')
      }
    },
    handleRowCommand(command, row) {
      this.selection = [row]
      if (command === 'audit') this.openDetails(row)
      if (command === 'print') this.printRows([row])
      if (command === 'delete') this.removeRows([row])
    },
    openDetails(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    displayName(row) {
      return row.contractNo || row.saleNo || row.applicationNo || row.packageName || row.cardName || row.listName || row.couponName || row.id
    },
    recordNo(row) {
      return row.contractNo || row.saleNo || row.applicationNo || row.packageNo || row.cardNo || row.listNo || row.id
    },
    exportRows() {
      const header = this.config.columns.map(column => column.label)
      const body = this.filteredRows.map(row => this.config.columns.map(column => String(row[column.key] || '').replace(/"/g, '""')))
      const csv = [header, ...body].map(line => line.map(value => `"${value}"`).join(',')).join('\n')
      const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${this.filteredRows.length} 条结果`)
    },
    escapeHtml(value) {
      return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
    },
    printRows(rows = this.selection.length ? this.selection : this.filteredRows) {
      if (!rows.length) return this.$message.warning('当前没有可打印的业务记录')
      const popup = window.open('', '_blank', 'width=1200,height=800')
      if (!popup) return this.$message.error('浏览器拦截了打印窗口，请允许本站弹出窗口')
      const columns = this.config.columns
      const header = columns.map(column => `<th>${this.escapeHtml(column.label)}</th>`).join('')
      const body = rows.map(row => `<tr>${columns.map(column => `<td>${this.escapeHtml(row[column.key])}</td>`).join('')}</tr>`).join('')
      popup.document.open()
      popup.document.write(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${this.escapeHtml(this.pageTitle)}打印</title><style>@page{size:landscape;margin:10mm}body{font-family:"Microsoft YaHei",sans-serif;color:#222}h1{font-size:20px;margin:0 0 12px}p{font-size:12px;color:#666}table{width:100%;border-collapse:collapse;font-size:10px}th,td{padding:5px;border:1px solid #bbb;text-align:left;white-space:nowrap}th{background:#f3eee4}</style></head><body><h1>${this.escapeHtml(this.pageTitle)}</h1><p>打印时间：${this.escapeHtml(new Date().toLocaleString('zh-CN'))}&nbsp;&nbsp;记录数：${rows.length}</p><table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></body></html>`)
      popup.document.close()
      popup.focus()
      popup.print()
    },
    statusCount(status) {
      if (status === '全部') return this.rows.length
      const aliases = {
        待出库: ['待出库', '已付未出库'],
        已启用: ['启用', '是'],
        已推荐: ['是'],
        审核中: ['待审核', '审核中'],
        未提交: ['待提交', '未提交']
      }
      const expected = aliases[status] || [status]
      return this.rows.filter(row => (
        Object.values(row).some(value => expected.includes(String(value)))
      )).length
    },
    metricValue(label, index) {
      if (/金额|销售额|欠款|剩余/.test(label)) {
        const keys = /欠款/.test(label)
          ? ['debtAmount', 'dueAmount']
          : /剩余/.test(label)
            ? ['remainingAmount']
            : ['consumeAmount', 'total', 'packageAmount', 'couponAmount', 'dealAmount']
        return this.rows.reduce((sum, row) => {
          const key = keys.find(item => row[item] !== undefined && row[item] !== null)
          return sum + Number(key ? row[key] : 0)
        }, 0)
      }
      if (index === 0 || /总数|总量|单量|数量|记录|种类/.test(label)) return this.rows.length
      return this.statusCount(label.replace(/^本月/, ''))
    },
    money(value) {
      return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
    },
    tagType(value) {
      if (/通过|已支付|已出库|启用|已使用|已推荐|已到店/.test(value)) return 'success'
      if (/不通过|作废|停用|退货|驳回|过期/.test(value)) return 'danger'
      if (/待|审核中|未支付|未提交|未使用/.test(value)) return 'warning'
      return 'info'
    },
    tableIndex(index) {
      return (this.pagination.page - 1) * this.pagination.size + index + 1
    },
    recentDateRange() {
      const end = new Date()
      const start = new Date(end)
      start.setDate(end.getDate() - 7)
      const format = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      return [format(start), format(end)]
    }
  }
}
</script>

<style lang="scss" scoped>
.sales-workbench { min-height: calc(100vh - 84px); padding: 22px; color: #26354c; background: #f3f6fa; }
.hero-panel { display: flex; justify-content: space-between; align-items: center; gap: 28px; padding: 26px 30px; border-radius: 16px; color: white; background: linear-gradient(125deg, #382262 0%, #6f3e82 55%, #b25b6c 100%); box-shadow: 0 14px 34px rgba(74, 40, 92, .2); }
.eyebrow { margin-bottom: 9px; color: #ffd7df; font-size: 13px; font-weight: 700; letter-spacing: .7px; }
.hero-panel h1 { margin: 0 0 9px; font-size: 27px; }
.hero-panel p { max-width: 760px; margin: 0; color: #eadfeb; font-size: 14px; line-height: 1.7; }
.hero-actions { display: flex; flex: 0 0 auto; align-items: center; gap: 10px; }
.metric-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; margin-top: 16px; overflow: hidden; border: 1px solid #e4e8ef; border-radius: 12px; background: #e4e8ef; }
.metric-item { padding: 18px 22px; background: white; }
.metric-item span { display: block; color: #718096; font-size: 12px; }
.metric-item strong { display: block; margin: 7px 0 4px; color: #5e376d; font-size: 24px; }
.metric-item small { color: #9aa6b4; }
.status-pipeline { display: flex; gap: 8px; margin-top: 14px; overflow-x: auto; }
.status-pipeline button { display: flex; flex: 0 0 auto; align-items: center; gap: 8px; padding: 9px 13px; border: 1px solid #e0e5ec; border-radius: 9px; color: #637086; background: white; cursor: pointer; }
.status-pipeline b { display: grid; width: 20px; height: 20px; place-items: center; border-radius: 50%; color: #7d8796; background: #eef1f5; font-size: 11px; }
.status-pipeline em { padding: 2px 6px; border-radius: 9px; color: #8b96a5; background: #f0f3f6; font-size: 11px; font-style: normal; }
.status-pipeline button.active { border-color: #855191; color: #74447f; background: #f8effa; box-shadow: 0 4px 12px rgba(112, 61, 126, .12); }
.status-pipeline button.active b { color: white; background: #855191; }
.filter-card, .table-card { margin-top: 16px; border: 0; border-radius: 12px; }
.card-heading, .table-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.card-heading h2 { margin: 0 0 4px; font-size: 16px; }
.card-heading p { margin: 0; color: #8a97a8; font-size: 12px; }
.filter-form { margin-bottom: -12px; }
.filter-form ::v-deep .el-form-item { margin-bottom: 16px; }
.filter-form ::v-deep .el-form-item__label { padding-bottom: 5px; color: #607087; font-size: 12px; line-height: 18px; }
.full-control { width: 100%; }
.field-hint { display: block; margin-top: 5px; color: #8a6a51; font-size: 11px; line-height: 1.4; }
.contract-filter-meta { display: flex; justify-content: space-between; align-items: center; gap: 18px; margin-top: 13px; padding: 14px 16px; border: 1px solid #ece5ef; border-radius: 10px; background: #fcf9fd; }
.store-selector { display: flex; align-items: center; gap: 12px; }
.meta-label { color: #46566d; font-weight: 700; }
.formula-tips { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 10px 18px; color: #8a5a34; font-size: 12px; }
.formula-tips span { white-space: nowrap; }
.formula-tips i { margin-right: 5px; color: #b77746; }
.filter-toggle { display: block; margin: 5px auto -5px; border: 0; color: #7d4688; background: transparent; cursor: pointer; }
.table-toolbar { align-items: flex-start; }
.business-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.business-actions .el-button + .el-button { margin-left: 0; }
.selection-tip { flex: 0 0 auto; padding-top: 7px; color: #7d8999; font-size: 12px; }
.table-card ::v-deep .el-card__body { padding-top: 0; }
.table-card ::v-deep .el-table th { color: #43536a; background: #f5f3f7; }
.contract-summary { display: flex; flex-wrap: wrap; align-items: center; gap: 9px 22px; padding: 13px 15px; border-top: 1px solid #ebeef5; color: #657287; font-size: 12px; background: #fcfbfd; }
.contract-summary strong { color: #4c3356; }
.contract-summary b { margin-left: 4px; color: #c3543c; }
.more-link { margin-left: 10px; color: #7d4688; font-size: 12px; cursor: pointer; }
.money { color: #d05f45; font-weight: 700; }
.expand-panel { padding: 14px 26px 18px; background: #faf8fb; }
.expand-heading { display: flex; justify-content: space-between; margin-bottom: 10px; color: #586579; }
.expand-heading span { color: #8d98a8; font-size: 12px; }
.pagination-row { display: flex; justify-content: space-between; align-items: center; padding-top: 18px; color: #8491a2; font-size: 12px; }
.dialog-alert { margin-bottom: 18px; }
.record-form { max-height: 54vh; padding: 4px 15px 0 0; overflow-y: auto; }
.line-editor-head { display: flex; justify-content: space-between; align-items: center; margin: 4px 0 14px; }
.line-editor-head strong, .line-editor-head span { display: block; }
.line-editor-head span { margin-top: 4px; color: #929dad; font-size: 12px; }
.line-total { display: flex; justify-content: flex-end; gap: 28px; padding: 16px 4px 2px; color: #697689; }
.line-total strong { color: #d05f45; font-size: 17px; }
.danger-link { color: #e25757; }
.detail-drawer { padding: 0 22px 30px; }
.detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; font-size: 19px; font-weight: 700; }
.detail-drawer h3 { margin: 26px 0 14px; font-size: 15px; }
@media (max-width: 900px) {
  .sales-workbench { padding: 12px; }
  .hero-panel, .hero-actions, .table-toolbar, .pagination-row { align-items: flex-start; flex-direction: column; }
  .contract-filter-meta { align-items: flex-start; flex-direction: column; }
  .store-selector { align-items: flex-start; flex-direction: column; }
  .formula-tips { justify-content: flex-start; }
  .metric-strip { grid-template-columns: repeat(2, 1fr); }
}
</style>
