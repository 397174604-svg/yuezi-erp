<template>
  <div class="finance-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i :class="config.icon" /> 财务管理</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-actions">
        <el-button v-if="config.mode !== 'form'" icon="el-icon-refresh" :loading="loading" @click="loadData">刷新</el-button>
      </div>
    </section>

    <el-alert
      v-if="isAllStores"
      title="当前选择“全部门店”：财务明细、客户/合同选择和新增编辑均已暂停。请在右上角选择具体门店；全部门店仅用于汇总查询。"
      type="warning"
      :closable="false"
      show-icon
      class="store-scope-alert"
    />

    <section class="metric-strip">
      <div v-for="(metric, index) in metrics" :key="metric.label" class="metric-item">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.money ? `¥ ${money(metric.value)}` : metric.value }}</strong>
        <small><i :class="index === 0 ? 'el-icon-data-analysis' : 'el-icon-time'" /> 当前查询结果</small>
      </div>
    </section>

    <section v-if="config.presentation === 'ledger'" class="finance-view-panel ledger-view">
      <div class="view-title"><i class="el-icon-collection-tag" /><div><b>账务处理台</b><span>先筛选门店和日期，再对已保存单据执行审核、核销或对账。</span></div></div>
      <div class="view-rule"><i class="el-icon-circle-check" /> 当前页面只处理已落库单据；外部渠道未接入时，不会生成支付或对账成功结果。</div>
      <div class="view-stats"><span>当前台账 <b>{{ rows.length }}</b> 笔</span><span>已选单据 <b>{{ selection.length }}</b> 笔</span><span>可执行操作 <b>{{ visibleActions.length }}</b> 项</span></div>
    </section>

    <section v-if="config.presentation === 'approval'" class="finance-view-panel approval-view">
      <div class="view-title"><i class="el-icon-s-check" /><div><b>退款与报销审批路径</b><span>退款申请、审核与实退登记分段留痕；费用报销仍由费用工作台独立处理。</span></div></div>
      <div class="approval-path"><span>1 发起退款</span><i class="el-icon-right" /><span>2 审核</span><i class="el-icon-right" /><span>3 登记实退</span><i class="el-icon-right" /><span>4 留存审计记录</span></div>
    </section>

    <section v-if="config.presentation === 'analysis'" class="finance-view-panel analysis-view">
      <div class="view-title"><i class="el-icon-data-analysis" /><div><b>统计口径</b><span>统计结果只来自当前门店范围和当前筛选结果；报表页面不直接改写业务单据。</span></div></div>
      <div class="analysis-chips"><span v-for="metric in metrics" :key="`analysis-${metric.label}`"><b>{{ metric.label }}</b>{{ metric.money ? `¥ ${money(metric.value)}` : metric.value }}</span></div>
    </section>

    <el-card v-if="config.mode === 'form'" shadow="never" class="content-card receipt-form-card">
      <div slot="header" class="card-heading">
        <div><h2>收款单</h2><p>登记客户收款信息并提交财务审核</p></div>
        <el-tag type="warning" effect="plain">带 * 为必填项</el-tag>
      </div>
      <el-form ref="receiptForm" :model="receiptForm" label-position="top" class="record-form">
        <el-row :gutter="18">
          <el-col v-for="field in config.formFields" :key="field.key" :xl="6" :lg="8" :md="12" :sm="12" :xs="24">
            <el-form-item :label="field.label" :required="field.required">
              <field-control v-if="field.type !== 'upload'" :field="resolvedField(field)" :model="receiptForm" @pick="openPicker" />
              <el-upload
                v-else
                class="receipt-upload"
                action="#"
                :auto-upload="false"
                :file-list="receiptAttachments"
                :on-change="handleAttachmentChange"
                :on-remove="handleAttachmentRemove"
                multiple
              >
                <el-button size="small" icon="el-icon-upload2">点击上传文件</el-button>
                <div slot="tip" class="el-upload__tip">选择后显示文件名，保存收款单时一并记录附件信息</div>
              </el-upload>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div class="form-tips">
        <span v-for="tip in config.tips" :key="tip"><i class="el-icon-info" />{{ tip }}</span>
      </div>
      <div class="form-actions">
        <el-button v-for="(action, index) in visibleActions" :key="action" :type="index === 0 ? 'primary' : 'default'" :loading="saving && index === 0" :disabled="isAllStores && action !== '关闭'" @click="handleReceiptAction(action)">{{ action }}</el-button>
      </div>
    </el-card>

    <template v-else>
      <el-card shadow="never" class="content-card action-card">
        <div class="table-toolbar">
          <div class="business-actions">
            <el-button
              v-for="(action, index) in visibleActions"
              :key="action"
              size="small"
              :type="index === 0 ? 'primary' : 'default'"
              :plain="index !== 0"
              :icon="actionIcon(action)"
              :disabled="isAllStores"
              @click="handleAction(action)"
            >{{ action }}</el-button>
          </div>
          <div class="selection-tip"><i class="el-icon-s-order" /> 已选 {{ selection.length }} 条 · 共 {{ filteredRows.length }} 条</div>
        </div>
      </el-card>

      <el-card v-if="config.workflow" shadow="never" class="content-card workflow-card">
        <div class="workflow-heading">
          <div><h2>{{ config.workflow.title }}</h2><p>{{ config.workflow.description }}</p></div>
          <el-button size="small" :type="workflowStatus ? 'primary' : 'default'" plain @click="setWorkflowStatus('')">查看全部</el-button>
        </div>
        <div class="workflow-steps">
          <button v-for="(stage, index) in config.workflow.stages" :key="stage.status" type="button" :class="{ active: workflowStatus === stage.status }" @click="setWorkflowStatus(stage.status)">
            <b>{{ index + 1 }}</b><span>{{ stage.label }}</span><em>{{ workflowCount(stage.status) }}</em>
          </button>
        </div>
      </el-card>

      <el-card shadow="never" class="content-card filter-card">
        <div slot="header" class="card-heading">
          <div><h2>查询条件</h2><p>每个财务页面使用原系统独立枚举，不跨页混用</p></div>
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
                <el-select v-else-if="field.type === 'select'" v-model="filters[field.key]" clearable filterable placeholder="请选择" class="full-control">
                  <el-option v-for="option in fieldOptions(field)" :key="option" :label="option" :value="option" />
                </el-select>
                <el-select v-else-if="field.type === 'multiSelect'" v-model="filters[field.key]" multiple collapse-tags filterable placeholder="请选择" class="full-control" @change="handleMultiSelectChange(field, $event)">
                  <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                </el-select>
                <el-date-picker v-else-if="field.type === 'dateRange'" v-model="filters[field.key]" type="daterange" value-format="yyyy-MM-dd" start-placeholder="开始日期" end-placeholder="结束日期" range-separator="至" class="full-control" />
                <el-checkbox v-else-if="field.type === 'checkbox'" v-model="filters[field.key]">{{ field.label }}</el-checkbox>
              </el-form-item>
            </el-col>
          </el-row>
          <div v-if="config.exclusionFilters && config.exclusionFilters.length" class="exclusion-row">
            <strong>不显示：</strong>
            <el-checkbox v-for="field in config.exclusionFilters" :key="field.key" v-model="filters[field.key]">{{ field.label }}</el-checkbox>
          </div>
        </el-form>
        <button v-if="config.filters.length > filterLimit" type="button" class="filter-toggle" @click="filtersExpanded = !filtersExpanded">
          {{ filtersExpanded ? '收起更多条件' : `展开更多条件（${config.filters.length - filterLimit}）` }}
          <i :class="filtersExpanded ? 'el-icon-arrow-up' : 'el-icon-arrow-down'" />
        </button>
      </el-card>

      <el-card shadow="never" class="content-card table-card">
        <el-tabs v-if="config.listTabs" v-model="activeBusinessTab" class="business-tabs" @tab-click="handleBusinessTabChange">
          <el-tab-pane v-for="tab in config.listTabs" :key="tab.key" :label="tab.label" :name="tab.key" />
        </el-tabs>

        <el-table :key="activeBusinessTab || config.key" v-loading="loading" :data="pagedRows" border stripe height="540" highlight-current-row @selection-change="selection = $event">
          <el-table-column v-if="showSelectionColumn" type="selection" width="45" fixed="left" />
          <el-table-column v-if="showIndexColumn" type="index" label="序号" width="58" fixed="left" :index="tableIndex" />
          <el-table-column v-for="column in visibleColumns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 110" show-overflow-tooltip>
            <template slot-scope="scope">
              <el-tag v-if="column.tag" size="mini" :type="tagType(scope.row[column.key])">{{ scope.row[column.key] }}</el-tag>
              <span v-else-if="column.money" class="money">¥ {{ money(scope.row[column.key]) }}</span>
              <span v-else>{{ scope.row[column.key] }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="showOperationColumn" :label="operationColumnLabel" width="145" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openDetails(scope.row)">详情</el-button>
              <el-button v-if="rowWorkflowAction(scope.row)" type="text" @click="runRowWorkflow(scope.row, rowWorkflowAction(scope.row))">{{ rowWorkflowAction(scope.row) }}</el-button>
              <el-button v-else-if="config.auditFields" type="text" @click="openDialog('审核', config.auditFields, scope.row)">审核</el-button>
              <el-button v-else type="text" @click="openDetails(scope.row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-row">
          <span>显示第 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
          <el-pagination background layout="prev, pager, next, sizes" :current-page.sync="pagination.page" :page-size.sync="pagination.size" :page-sizes="[10, 20, 50, 100]" :total="filteredRows.length" />
        </div>
      </el-card>
    </template>

    <el-dialog :title="pickerTitle" :visible.sync="pickerVisible" width="900px" top="7vh" :close-on-click-modal="false">
      <el-alert :title="pickerTip" type="info" :closable="false" show-icon class="dialog-alert" />
      <div class="picker-toolbar">
        <el-input v-model.trim="pickerKeyword" clearable prefix-icon="el-icon-search" :placeholder="pickerPlaceholder" @keyup.enter.native="searchPicker" />
        <el-button type="primary" icon="el-icon-search" @click="searchPicker">查询</el-button>
      </div>
      <el-table v-loading="pickerLoading" :data="filteredPickerRows" border stripe height="360" highlight-current-row>
        <el-table-column v-for="column in pickerColumns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 110" show-overflow-tooltip />
        <el-table-column label="操作" width="82" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="selectPickerRow(scope.row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div slot="footer">
        <span class="picker-total">共 {{ filteredPickerRows.length }} 条可选记录</span>
        <el-button @click="pickerVisible = false">关闭</el-button>
      </div>
    </el-dialog>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="760px" top="6vh" :close-on-click-modal="false">
      <el-alert :title="dialogTip" type="info" :closable="false" show-icon class="dialog-alert" />
      <el-form :model="dialogForm" label-width="118px" class="dialog-form">
        <el-row :gutter="18">
          <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
            <el-form-item :label="field.label" :required="field.required">
              <field-control :field="resolvedField(field)" :model="dialogForm" @pick="openDialogPicker" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitDialog">确认提交</el-button>
      </div>
    </el-dialog>

    <el-drawer title="财务业务详情" :visible.sync="drawerVisible" size="580px">
      <div v-if="currentRow" class="detail-drawer">
        <div class="detail-head"><strong>{{ recordName(currentRow) }}</strong><el-tag size="small" type="success">业务记录</el-tag></div>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item v-for="column in visibleColumns" :key="column.key" :label="column.label">
            <span v-if="column.money">¥ {{ money(currentRow[column.key]) }}</span>
            <span v-else>{{ currentRow[column.key] }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <h3>业务状态</h3>
        <el-alert :title="currentRow.auditStatus || currentRow.status || '待处理'" type="info" :closable="false" show-icon />
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { financePageConfigs, getFinancePageConfig } from '@/config/finance-pages'
import { getFinanceModuleData, getFinanceOptions, getFinancePickerData, performFinanceModuleAction, saveFinanceModuleRecord } from '@/api/erp-finance'

const invoiceFields = [
  { key: 'invoiceNo', label: '真实发票号码', type: 'input', required: true },
  { key: 'taxMode', label: '计税方式', type: 'radio', options: ['含税', '不含税'], required: true },
  { key: 'taxRate', label: '税率', type: 'select', options: ['3%'], required: true },
  { key: 'invoiceType', label: '发票类型', type: 'radio', options: ['增值税普通发票', '增值税专用发票'], required: true },
  { key: 'invoiceTitleType', label: '发票抬头', type: 'radio', options: ['个人', '单位'], required: true },
  { key: 'invoiceDate', label: '开票日期', type: 'date', required: true },
  { key: 'customerName', label: '姓名', type: 'input' },
  { key: 'companyName', label: '单位名称', type: 'input' },
  { key: 'taxpayerNo', label: '纳税人识别码', type: 'input' },
  { key: 'registeredAddress', label: '注册地址', type: 'input' },
  { key: 'registeredPhone', label: '注册电话', type: 'input' },
  { key: 'bank', label: '开户银行', type: 'input' },
  { key: 'bankAccount', label: '银行账号', type: 'input' }
]

const pickerDefinitions = {
  employee: {
    title: '选择业务员',
    tip: '从启用的员工账号中选择收款人，选中后回填员工登录账号。',
    placeholder: '请输入账号、姓名、部门或门店',
    columns: [
      { key: 'username', label: '员工账号', width: 120 },
      { key: 'name', label: '员工姓名', width: 110 },
      { key: 'department', label: '部门', width: 120 },
      { key: 'store', label: '所属门店', width: 160 },
      { key: 'role', label: '角色', width: 120 },
      { key: 'status', label: '状态', width: 90 }
    ]
  },
  customer: {
    title: '选择客户',
    tip: '从客户中心已有客户中选择，选中后回填客户名称并关联客户编号。',
    placeholder: '请输入客户账号、姓名、手机号或业务员',
    columns: [
      { key: 'username', label: '客户账号', width: 120 },
      { key: 'name', label: '客户名称', width: 120 },
      { key: 'mobile', label: '手机号', width: 130 },
      { key: 'status', label: '客户状态', width: 150 },
      { key: 'salesperson', label: '业务员', width: 110 },
      { key: 'store', label: '所属门店', width: 160 }
    ]
  },
  contract: {
    title: '选择已审核合同',
    tip: '合同类收款必须关联当前门店已审核合同；选择后自动回填客户、门店和合同剩余可收金额。',
    placeholder: '请输入合同编号、客户姓名或手机号',
    columns: [
      { key: 'contractNo', label: '合同编号', width: 150 },
      { key: 'customerName', label: '客户姓名', width: 120 },
      { key: 'mobile', label: '手机号', width: 130 },
      { key: 'store', label: '合同门店', width: 160 },
      { key: 'amount', label: '合同金额', width: 110 },
      { key: 'paid', label: '已登记收款', width: 110 },
      { key: 'balance', label: '剩余可收', width: 110 },
      { key: 'status', label: '合同状态', width: 100 }
    ]
  }
}

const financeNavIds = {
  新增收款: 521,
  收款管理: 90,
  退款申请: 95,
  退款审核: 96,
  欠款审核: 281,
  换货审核: 653,
  发票管理: 572,
  交易对账: 90,
  部门物料预算: 251,
  我的费用: 317,
  费用审核: 607,
  付款管理: 415
}

const financeActionButtonIds = {
  收款管理: { 前往新增收款: 1, 星支付: 93, 登记真实发票: 120, 编辑: 10, 删除: 3, 导出: 19, 打印: 48, 审核: 21, 批量审核: 96, 核销: 60, 反审核: 49, 手续费: 125, 扫码支付: 137 },
  退款申请: { 添加: 1, 编辑: 10, 删除: 3, 打印: 48, 提交: 58, 导出: 19 },
  退款审核: { 流程审批: 51, 登记退款打款: 54, 反审核: 49, 撤回: 132 },
  欠款审核: { 审核: 21 },
  换货审核: { 审核: 21, 删除: 3 },
  发票管理: { 导出: 19, 删除: 3 },
  交易对账: { 添加: 1, 确认匹配: 21, 取消匹配: 49, 删除: 3, 导出: 19 },
  部门物料预算: { 添加: 1, 流程审批: 51, 编辑: 10, 删除: 3, 提交: 58, 生成采购计划: 59, 导出: 19 },
  我的费用: { 添加: 1, 编辑: 10, 删除: 3, 导出: 19, 打印: 48, 打款: 54, 反审核: 49, 提交: 58 },
  费用审核: { 流程审批: 51 },
  付款管理: { 导出: 19 }
}

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
    if (field.type === 'picker') {
      return h('el-input', {
        class: 'full-control picker-control',
        attrs: { 'data-field-key': field.key },
        props: { value, readonly: true, clearable: true, placeholder: field.placeholder || `请选择${field.label}` },
        on: { input: setValue }
      }, [
        h('el-button', {
          slot: 'append',
          attrs: { 'data-picker-type': field.pickerType },
          props: { icon: 'el-icon-search' },
          on: { click: () => this.$emit('pick', field) }
        }, '选择')
      ])
    }
    if (field.type === 'select') {
      return h('el-select', { class: 'full-control', props: { value, clearable: !field.disabled, disabled: Boolean(field.disabled), filterable: true, placeholder: '请选择' }, on: { input: setValue }}, field.options.map(option => h('el-option', { key: option, props: { label: option, value: option }})))
    }
    if (field.type === 'radio') {
      return h('el-radio-group', { props: { value }, on: { input: setValue }}, field.options.map(option => h('el-radio', { key: option, props: { label: option }}, option)))
    }
    if (field.type === 'checkbox') {
      return h('el-checkbox', { props: { value: Boolean(value) }, on: { input: setValue }}, field.label)
    }
    if (field.type === 'date') {
      return h('el-date-picker', { class: 'full-control', props: { value, type: 'date', valueFormat: 'yyyy-MM-dd', placeholder: '请选择日期' }, on: { input: setValue }})
    }
    if (field.type === 'number') {
      return h('el-input-number', { class: 'full-control', props: { value: Number(value || 0), min: 0, precision: 2, controlsPosition: 'right' }, on: { input: setValue }})
    }
    if (field.type === 'textarea') {
      return h('el-input', { props: { value, type: 'textarea', rows: 3, placeholder: `请输入${field.label}` }, on: { input: setValue }})
    }
    return h('el-input', { props: { value, clearable: true, placeholder: `请输入${field.label}` }, on: { input: setValue }})
  }
}

export default {
  name: 'FinanceWorkbench',
  components: { FieldControl },
  data() {
    return {
      loading: false,
      saving: false,
      filtersExpanded: false,
      filters: {},
      receiptForm: {},
      receiptAttachments: [],
      rows: [],
      selection: [],
      pagination: { page: 1, size: 10 },
      dialogVisible: false,
      dialogTitle: '',
      dialogTip: '',
      dialogFields: [],
      dialogForm: {},
      dialogAction: '',
      currentRow: null,
      drawerVisible: false,
      pickerVisible: false,
      pickerLoading: false,
      pickerType: '',
      pickerField: null,
      pickerTarget: 'receipt',
      pickerKeyword: '',
      pickerRows: [],
      storeOptions: [],
      activeBusinessTab: '',
      workflowStatus: ''
    }
  },
  computed: {
    ...mapGetters(['permissions', 'roles', 'currentStoreId']),
    pageTitle() {
      return String(this.$route.meta.title || '').replace(/\s*★\s*$/, '')
    },
    config() {
      return getFinancePageConfig(this.pageTitle)
    },
    financePermissionTitle() {
      return this.config.permissionTitle || this.pageTitle
    },
    isAllStores() {
      return String(this.currentStoreId || 'all') === 'all'
    },
    currentStore() {
      return this.storeOptions.find(item => String(item.id) === String(this.currentStoreId)) || null
    },
    filterLimit() {
      return this.config.filterLimit || 8
    },
    visibleActions() {
      if ((this.roles || []).includes('SYS_ADMIN')) return this.config.actions
      if (this.config.key === 'receipt-create') {
        return this.config.actions.filter(action => {
          if (action === '关闭') return true
          if (action === '保存') return (this.permissions || []).includes('FINANCE.CREATE')
          return false
        })
      }
      const navId = financeNavIds[this.financePermissionTitle]
      const buttonMap = financeActionButtonIds[this.financePermissionTitle] || {}
      return this.config.actions.filter(action => {
        const buttonId = buttonMap[action]
        return buttonId && (this.permissions || []).includes(`LEGACY.WEB.N${navId}.B${buttonId}`)
      })
    },
    visibleFilters() {
      return this.filtersExpanded ? this.config.filters : this.config.filters.slice(0, this.filterLimit)
    },
    filteredRows() {
      const entries = Object.entries(this.filters).filter(([, value]) => value !== '' && value !== null && value !== false && (!Array.isArray(value) || value.length))
      const scopedRows = this.workflowStatus
        ? this.rows.filter(row => this.workflowRowStatus(row) === this.workflowStatus)
        : this.rows
      if (!entries.length) return scopedRows
      return scopedRows.filter(row => entries.every(([key, value]) => {
        if (typeof value === 'boolean') return !value || !this.shouldExcludeRow(row, key)
        const field = this.config.filters.find(item => item.key === key)
        if (field && field.type === 'dateRange') {
          const rowDate = this.rowDateForRange(key, row)
          if (!rowDate || value.length !== 2) return true
          return rowDate >= value[0] && rowDate <= value[1]
        }
        if (Array.isArray(value)) return value.includes('全部') || value.includes(row[key])
        if (value === '全部') return true
        return String(row[key] || '').includes(String(value))
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
      const labels = this.config.metrics || ['财务单据', '待处理', '本月新增', '业务金额']
      const moneyTotal = this.rows.reduce((total, row) => {
        const value = row.amount || row.refundAmount || row.applyAmount || row.totalAmount || row.invoiceAmount || row.differenceAmount || 0
        return total + Number(value || 0)
      }, 0)
      return labels.map((label, index) => ({
        label,
        value: /金额|余额|实收|退款|欠款|预算|付款/.test(label)
          ? moneyTotal
          : /待审核|待处理|审核任务/.test(label)
            ? this.rows.filter(row => /待审核|已提交|审核中/.test(row.auditStatus || row.status || '')).length
            : this.rows.length,
        money: /金额|余额|实收|退款|欠款|预算|付款/.test(label)
      }))
    },
    activeTabConfig() {
      if (!this.config.listTabs) return null
      return this.config.listTabs.find(tab => tab.key === this.activeBusinessTab) || this.config.listTabs[0]
    },
    visibleColumns() {
      return this.activeTabConfig ? this.activeTabConfig.columns : this.config.columns
    },
    showSelectionColumn() {
      return this.activeTabConfig ? this.activeTabConfig.selection !== false : true
    },
    showIndexColumn() {
      return this.activeTabConfig ? this.activeTabConfig.index !== false : true
    },
    showOperationColumn() {
      return this.activeTabConfig ? this.activeTabConfig.showOperation !== false : true
    },
    operationColumnLabel() {
      return this.activeTabConfig && this.activeTabConfig.operationLabel ? this.activeTabConfig.operationLabel : '操作'
    },
    pickerDefinition() {
      return pickerDefinitions[this.pickerType] || pickerDefinitions.employee
    },
    pickerTitle() {
      return this.pickerDefinition.title
    },
    pickerTip() {
      return this.pickerDefinition.tip
    },
    pickerPlaceholder() {
      return this.pickerDefinition.placeholder
    },
    pickerColumns() {
      return this.pickerDefinition.columns
    },
    filteredPickerRows() {
      const keyword = this.pickerKeyword.toLowerCase()
      if (!keyword) return this.pickerRows
      return this.pickerRows.filter(row => Object.values(row).some(value => String(value || '').toLowerCase().includes(keyword)))
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    },
    currentStoreId() {
      this.initializePage()
    }
  },
  methods: {
    initializePage() {
      this.loadFinanceOptions()
      if (this.config.mode === 'form') {
        this.receiptForm = this.emptyForm(this.config.formFields)
        this.receiptAttachments = []
        this.receiptForm.receiptKind = '收款单'
        this.applyCurrentStoreToReceipt()
        this.rows = []
        return
      }
      this.activeBusinessTab = this.config.listTabs ? this.config.listTabs[0].key : ''
      const filterFields = [...this.config.filters, ...(this.config.exclusionFilters || [])]
      this.filters = filterFields.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'dateRange' || field.type === 'multiSelect' ? [] : field.type === 'checkbox' ? false : '')
        return result
      }, {})
      Object.entries(this.config.defaultFilters || {}).forEach(([key, value]) => { this.$set(this.filters, key, value) })
      this.filtersExpanded = false
      this.pagination.page = 1
      this.selection = []
      this.workflowStatus = ''
      this.loadData()
    },
    async loadData() {
      if (this.isAllStores || this.config.integrationOnly) {
        this.rows = []
        return
      }
      this.loading = true
      try {
        const response = await getFinanceModuleData(this.config.key, {
          ...this.filters,
          storeId: this.currentStoreId,
          tab: this.activeBusinessTab || undefined
        })
        this.rows = response.data && Array.isArray(response.data.list) ? response.data.list : []
        if (response.data && Array.isArray(response.data.stores)) {
          this.storeOptions = response.data.stores
        }
      } catch (error) {
        this.rows = []
      } finally {
        this.loading = false
      }
    },
    async loadFinanceOptions() {
      try {
        const response = await getFinanceOptions({ storeId: this.currentStoreId })
        this.storeOptions = response.data && Array.isArray(response.data.stores) ? response.data.stores : []
        if (this.config.mode === 'form') this.applyCurrentStoreToReceipt()
      } catch (error) {
        this.storeOptions = []
      }
    },
    fieldOptions(field) {
      if (field.key === 'store' && this.storeOptions.length) return this.storeOptions.map(item => item.name)
      return field.options || []
    },
    resolvedField(field) {
      if (field.key !== 'store' || !this.storeOptions.length) return field
      return { ...field, options: this.storeOptions.map(item => item.name), disabled: true }
    },
    emptyForm(fields) {
      return fields.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'checkbox' ? false : field.type === 'number' ? 0 : '')
        return result
      }, {})
    },
    handleBusinessTabChange(tab) {
      this.activeBusinessTab = tab.name
      this.$nextTick(() => {
        this.pagination.page = 1
        this.selection = []
        this.loadData()
      })
    },
    handleMultiSelectChange(field, values) {
      if (!values.includes('全部') || values.length === 1) return
      const normalized = values[values.length - 1] === '全部' ? ['全部'] : values.filter(value => value !== '全部')
      this.$set(this.filters, field.key, normalized)
    },
    shouldExcludeRow(row, key) {
      const exclusionRules = {
        hideWriteOff: () => row.settlement === '结算核销' || row.writeOffStatus === '已核销',
        hideMemberCard: () => row.paymentMethod === '会员卡',
        hideCoupon: () => row.paymentMethod === '优惠券',
        hideZero: () => Number(row.amount || row.documentAmount || 0) === 0,
        hideAdmin: () => row.creator === 'admin' || row.cashier === 'admin',
        hideDischarged: () => row.customerStatus === '已退房已结账'
      }
      return exclusionRules[key] ? exclusionRules[key]() : false
    },
    search() {
      this.pagination.page = 1
      this.$message.success(`已按 ${this.visibleFilters.length} 个本页字段完成查询`)
    },
    resetFilters() {
      Object.keys(this.filters).forEach(key => { this.filters[key] = Array.isArray(this.filters[key]) ? [] : typeof this.filters[key] === 'boolean' ? false : '' })
      Object.entries(this.config.defaultFilters || {}).forEach(([key, value]) => { this.filters[key] = value })
      this.pagination.page = 1
    },
    async handleAction(action) {
      if (action === '导出') return this.exportRows()
      if (action === '前往新增收款' && this.config.key === 'receipts') return this.$router.push('/finance/item-1')
      if (action === '添加') return this.openDialog(`添加${this.pageTitle}`, this.config.formFields || [], null)
      if (action === '星支付' || action === '扫码支付') {
        const row = this.requireOne()
        if (row) this.$message.warning(`${action}尚未配置真实支付通道，系统不会生成虚假支付结果`)
        return
      }
      if (action === '编辑') {
        const row = this.requireOne()
        const fields = this.config.formFields || (this.config.key === 'receipts' ? financePageConfigs['新增收款'].formFields : [])
        if (row) this.openDialog(action, fields, row)
        return
      }
      if (action === '删除') {
        const row = this.requireOne()
        if (!row) return
        try {
          await this.$confirm(`确认删除 ${this.recordName(row)}？该操作会写入审计日志。`, '删除确认', { type: 'warning' })
          await performFinanceModuleAction(this.config.key, action, { id: row.id })
          await this.loadData()
          this.$message.success('财务记录已删除')
        } catch (error) {
          if (error !== 'cancel') throw error
        }
        return
      }
      if (action === '打印') {
        const row = this.requireOne()
        if (row) window.print()
        return
      }
      if (action === '提交') return this.executeDirectAction(action)
      if (action === '打款' || action === '登记退款打款') return this.openDialog(action, this.config.payoutFields || [], this.requireOne())
      if (/发票|开票/.test(action)) return this.openDialog(action, invoiceFields, this.requireOne())
      if (action === '批量审核') {
        if (!this.selection.length) return this.$message.warning('请至少选择一条财务记录')
        if (!(this.config.auditFields || []).length) return this.$message.info('当前页面需接入原审批流程后执行批量审核')
        return this.openDialog(action, this.config.auditFields, this.selection[0])
      }
      if (action === '审核' || action === '流程审批') {
        const row = this.requireOne()
        if (!row) return
        if (!(this.config.auditFields || []).length) return this.$message.info('当前页面需接入原审批流程后执行审核')
        return this.openDialog(action, this.config.auditFields, row)
      }
      if (action === '反审核' || action === '撤回') {
        const row = this.requireOne()
        if (!row) return
        await performFinanceModuleAction(this.config.key, action, { id: row.id })
        await this.loadData()
        return this.$message.success(`${action}已完成并写入审计日志`)
      }
      if (action === '确认匹配' || action === '取消匹配') {
        const row = this.requireOne()
        if (!row) return
        await performFinanceModuleAction(this.config.key, action, { id: row.id })
        await this.loadData()
        return this.$message.success(`${action}已完成并写入审计日志`)
      }
      if (action === '生成采购计划') {
        const row = this.requireOne()
        if (!row) return
        await performFinanceModuleAction(this.config.key, action, { id: row.id })
        await this.loadData()
        return this.$message.success('采购计划编号已生成')
      }
      if (action === '手续费') {
        return this.openDialog(action, [
          { key: 'fee', label: '手续费', type: 'number', required: true },
          { key: 'receivedAt', label: '到账时间', type: 'date' },
          { key: 'remark', label: '备注', type: 'textarea' }
        ], this.requireOne())
      }
      if (action === '核销') {
        return this.openDialog(action, [
          { key: 'writeOffType', label: '核销类型', type: 'select', options: ['合同首付', '合同收款', '押金收款', '会员充值', '月嫂合同收款'], required: true },
          { key: 'paymentMethod', label: '支付方式', type: 'select', options: ['现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '押金', '会员卡', '优惠券', '积分支付', '星pos支付'], required: true },
          { key: 'availableAmount', label: '可核销金额', type: 'number' },
          { key: 'writeOffAmount', label: '核销金额', type: 'number', required: true },
          { key: 'store', label: '核销门店', type: 'select', options: this.storeOptions.map(item => item.name), required: true },
          { key: 'remark', label: '核销备注', type: 'textarea' }
        ], this.requireOne())
      }
    },
    handleReceiptAction(action) {
      if (action === '关闭') {
        this.receiptForm = this.emptyForm(this.config.formFields)
        this.receiptAttachments = []
        this.receiptForm.receiptKind = '收款单'
        this.receiptForm.store = this.storeOptions.length === 1 ? this.storeOptions[0].name : ''
        return this.$message.info('收款单已清空')
      }
      if (action === '星支付') return this.$message.info('星支付需在真实资金账户接入后启用')
      this.saveReceipt()
    },
    async openPicker(field) {
      if (this.isAllStores) return this.$message.warning('请先在右上角选择具体门店，再选择客户、合同或收款人')
      this.pickerField = field
      this.pickerType = field.pickerType
      this.pickerTarget = 'receipt'
      this.pickerKeyword = ''
      this.pickerRows = []
      this.pickerVisible = true
      this.pickerLoading = true
      try {
        const response = await getFinancePickerData(field.pickerType, { storeId: this.currentStoreId })
        this.pickerRows = response.data.list || []
      } finally {
        this.pickerLoading = false
      }
    },
    openDialogPicker(field) {
      if (this.isAllStores) return this.$message.warning('请先在右上角选择具体门店，再选择下游业务数据')
      this.pickerTarget = 'dialog'
      this.pickerField = field
      this.pickerType = field.pickerType
      this.pickerKeyword = ''
      this.pickerRows = []
      this.pickerVisible = true
      this.pickerLoading = true
      getFinancePickerData(field.pickerType, { storeId: this.currentStoreId })
        .then(response => {
          this.pickerRows = response.data.list || []
        })
        .finally(() => {
          this.pickerLoading = false
        })
    },
    selectPickerRow(row) {
      if (!this.pickerField) return
      const model = this.pickerTarget === 'dialog' ? this.dialogForm : this.receiptForm
      if (this.pickerType === 'employee') {
        this.$set(model, this.pickerField.key, row.username)
        this.$set(model, 'cashierId', row.id)
        this.$set(model, 'cashierName', row.name)
      } else if (this.pickerType === 'contract') {
        this.$set(model, this.pickerField.key, row.contractNo)
        this.$set(model, 'contractId', row.id)
        this.$set(model, 'customerId', row.customerId)
        this.$set(model, 'customerName', row.customerName)
        this.$set(model, 'customerMobile', row.mobile)
        this.$set(model, 'store', row.store)
        this.$set(model, 'amount', Number(row.balance || 0))
      } else {
        this.$set(model, this.pickerField.key, row.name)
        this.$set(model, 'customerId', row.id)
        this.$set(model, 'customerAccount', row.username)
        this.$set(model, 'customerMobile', row.mobile)
      }
      this.pickerVisible = false
      const typeLabel = { employee: '业务员', customer: '客户', contract: '合同' }[this.pickerType] || '记录'
      this.$message.success(`已选择${typeLabel}：${model[this.pickerField.key]}`)
    },
    searchPicker() {
      if (!this.pickerKeyword) return this.$message.info(`当前共 ${this.pickerRows.length} 条可选记录`)
      this.$message.success(`找到 ${this.filteredPickerRows.length} 条匹配记录`)
    },
    handleAttachmentChange(file, fileList) {
      this.receiptAttachments = fileList
      this.$set(this.receiptForm, 'attachment', fileList.map(item => item.name).join('、'))
    },
    handleAttachmentRemove(file, fileList) {
      this.receiptAttachments = fileList
      this.$set(this.receiptForm, 'attachment', fileList.map(item => item.name).join('、'))
    },
    async saveReceipt() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请选择具体门店后保存收款单')
      const missing = this.config.formFields.filter(field => field.required && !this.receiptForm[field.key])
      if (missing.length) return this.$message.warning(`请填写：${missing.map(field => field.label).join('、')}`)
      this.saving = true
      try {
        await saveFinanceModuleRecord(this.config.key, { ...this.receiptForm, storeId: this.currentStoreId })
        this.$message.success('收款单已保存，并写入财务审计轨迹')
      } finally {
        this.saving = false
      }
    },
    requireOne() {
      const row = this.selection[0]
      if (!row) this.$message.warning('请先选择一条财务记录')
      return row
    },
    openDialog(action, fields, row) {
      if (!fields.length) return this.$message.info('当前页面原系统未提供新增表单')
      if (!row && action !== `添加${this.pageTitle}` && action !== '添加') return
      this.dialogAction = action
      this.dialogTitle = action
      this.dialogTip = /发票|开票/.test(action)
        ? '请核对发票号码、开票金额、客户和关联业务单据。'
        : `请核对${action}的金额、门店、经办人和当前状态。`
      this.dialogFields = fields
      this.dialogForm = { ...this.emptyForm(fields), ...(row || {}) }
      this.currentRow = row
      this.dialogVisible = true
    },
    async submitDialog() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请选择具体门店后操作业务单据')
      const missing = this.dialogFields.filter(field => field.required && !this.dialogForm[field.key])
      if (missing.length) return this.$message.warning(`请填写：${missing.map(field => field.label).join('、')}`)
      this.saving = true
      try {
        if (/^添加/.test(this.dialogAction) || this.dialogAction === '编辑') {
          await saveFinanceModuleRecord(this.config.key, {
            ...this.dialogForm,
            storeId: this.currentStoreId,
            id: this.currentRow && this.currentRow.id
          })
        } else {
          const payload = {
            id: this.currentRow && this.currentRow.id,
            ...this.dialogForm,
            storeId: this.currentStoreId
          }
          if (this.dialogAction === '批量审核') payload.ids = this.selection.map(row => row.id)
          await performFinanceModuleAction(this.config.key, this.dialogAction, payload)
        }
        this.dialogVisible = false
        await this.loadData()
        this.$message.success(`${this.dialogAction}已完成`)
      } finally {
        this.saving = false
      }
    },
    async executeDirectAction(action) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请选择具体门店后提交单据')
      const row = this.requireOne()
      if (!row) return
      await performFinanceModuleAction(this.config.key, action, { id: row.id })
      await this.loadData()
      this.$message.success('已提交到下一审批节点')
    },
    workflowRowStatus(row) {
      return String(row.status || row.auditStatus || row.paymentStatus || '')
    },
    workflowCount(status) {
      return this.rows.filter(row => this.workflowRowStatus(row) === status).length
    },
    setWorkflowStatus(status) {
      this.workflowStatus = this.workflowStatus === status ? '' : status
      this.pagination.page = 1
      this.selection = []
    },
    rowWorkflowAction(row) {
      if (!this.config.workflow || this.isAllStores) return ''
      const stage = this.config.workflow.stages.find(item => item.status === this.workflowRowStatus(row))
      const action = stage && stage.action
      return action && this.visibleActions.includes(action) ? action : ''
    },
    runRowWorkflow(row, action) {
      this.selection = [row]
      if (action === '编辑') return this.handleAction(action)
      if (action === '提交') return this.executeDirectAction(action)
      if (action === '流程审批') return this.openDialog(action, this.config.auditFields || [], row)
      if (action === '打款' || action === '登记退款打款') return this.openDialog(action, this.config.payoutFields || [], row)
      if (action === '确认匹配' || action === '取消匹配') return this.handleAction(action)
    },
    applyCurrentStoreToReceipt() {
      if (!this.currentStore) {
        this.$set(this.receiptForm, 'store', '')
        this.$set(this.receiptForm, 'storeId', '')
        return
      }
      this.$set(this.receiptForm, 'store', this.currentStore.name)
      this.$set(this.receiptForm, 'storeId', this.currentStore.id)
    },
    applyLocalStatus() {
      if (!this.currentRow) return
      if (/审核/.test(this.dialogAction)) {
        const result = this.dialogForm.auditResult || ''
        this.$set(this.currentRow, 'auditStatus', /通过/.test(result) ? '审核通过' : '驳回')
      }
      if (this.dialogAction === '打款') this.$set(this.currentRow, 'paymentStatus', '已打款')
      if (/发票|开票/.test(this.dialogAction)) this.$set(this.currentRow, 'invoiceStatus', '已开票')
      if (this.dialogAction === '核销') this.$set(this.currentRow, 'settlement', '结算核销')
    },
    openDetails(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    exportRows() {
      const headers = this.visibleColumns.map(column => column.label)
      const body = this.filteredRows.map(row => this.visibleColumns.map(column => `"${String(row[column.key] == null ? '' : row[column.key]).replace(/"/g, '""')}"`).join(','))
      const csv = `\uFEFF${headers.join(',')}\n${body.join('\n')}`
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${Date.now()}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${this.filteredRows.length} 条当前查询记录`)
    },
    recordName(row) {
      return row.receiptNo || row.externalReference || row.refundNo || row.exchangeNo || row.budgetNo || row.expenseNo || row.paymentNo || row.documentNo || row.customerName || row.id
    },
    rowDateForRange(key, row) {
      const keys = {
        documentRange: ['documentDate', 'createdAt'],
        financeRange: ['documentDate', 'createdAt'],
        stayRange: ['checkInAt'],
        applyRange: ['appliedAt', 'createdAt'],
        budgetRange: ['budgetDate'],
        publishedRange: ['createdAt'],
        transactionRange: ['transactionDate']
      }[key] || []
      const value = keys.map(item => row[item]).find(Boolean)
      return value ? String(value).slice(0, 10) : ''
    },
    actionIcon(action) {
      if (/添加|保存/.test(action)) return 'el-icon-plus'
      if (/流程审批|审核|提交|确认匹配/.test(action)) return 'el-icon-s-check'
      if (/导出/.test(action)) return 'el-icon-download'
      if (/编辑/.test(action)) return 'el-icon-edit'
      if (/删除/.test(action)) return 'el-icon-delete'
      if (/打印/.test(action)) return 'el-icon-printer'
      if (/撤回|反审核|取消匹配/.test(action)) return 'el-icon-refresh-left'
      if (/采购计划/.test(action)) return 'el-icon-shopping-cart-full'
      if (/星支付|扫码支付/.test(action)) return 'el-icon-full-screen'
      if (/手续费/.test(action)) return 'el-icon-coin'
      if (/打款|核销/.test(action)) return 'el-icon-money'
      if (/发票|开票/.test(action)) return 'el-icon-tickets'
      return 'el-icon-setting'
    },
    tagType(value) {
      if (/通过|已打款|已退款|已开票|已出库|已审批|已核销/.test(value)) return 'success'
      if (/不通过|驳回|被驳回|已驳回/.test(value)) return 'danger'
      if (/待|审核中|未出库|未开票/.test(value)) return 'warning'
      return 'info'
    },
    money(value) {
      return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
    },
    tableIndex(index) {
      return (this.pagination.page - 1) * this.pagination.size + index + 1
    }
  }
}
</script>

<style lang="scss" scoped>
.finance-workbench { min-height: calc(100vh - 84px); padding: 22px; color: #26354c; background: #f3f6fa; }
.hero-panel { display: flex; justify-content: space-between; align-items: center; gap: 28px; padding: 26px 30px; border-radius: 16px; color: white; background: linear-gradient(125deg, #28241e 0%, #5f4b2d 56%, #a68045 100%); box-shadow: 0 14px 34px rgba(74, 55, 26, .2); }
.eyebrow { margin-bottom: 9px; color: #f3dfb7; font-size: 13px; font-weight: 700; letter-spacing: .7px; }
.hero-panel h1 { margin: 0 0 9px; font-size: 27px; }
.hero-panel p { max-width: 800px; margin: 0; color: #f7efe0; font-size: 14px; line-height: 1.7; }
.hero-actions { display: flex; flex: 0 0 auto; align-items: center; gap: 10px; }
.metric-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; margin-top: 16px; overflow: hidden; border: 1px solid #e4e8ef; border-radius: 12px; background: #e4e8ef; }
.metric-item { padding: 18px 22px; background: white; }
.metric-item span { display: block; color: #718096; font-size: 12px; }
.metric-item strong { display: block; margin: 7px 0 4px; color: #8c6a36; font-size: 24px; }
.metric-item small { color: #9aa6b4; }
.finance-view-panel { margin-top: 16px; padding: 17px 20px; border: 1px solid #e9e0cf; border-radius: 12px; background: #fff; }
.view-title { display: flex; align-items: flex-start; gap: 11px; color: #6b4b1d; }.view-title > i { margin-top: 2px; font-size: 21px; }.view-title b, .view-title span { display: block; }.view-title b { margin-bottom: 4px; font-size: 15px; }.view-title span { color: #788397; font-size: 12px; line-height: 1.55; }
.ledger-view { display: grid; grid-template-columns: minmax(280px, 1.5fr) minmax(260px, 1.2fr) minmax(260px, 1fr); gap: 18px; align-items: center; border-left: 4px solid #a87b35; }.view-rule { padding: 10px 12px; border-radius: 8px; color: #6d5c3d; background: #fff8e9; font-size: 12px; line-height: 1.5; }.view-rule i { margin-right: 5px; color: #b78026; }.view-stats { display: flex; justify-content: space-between; gap: 10px; color: #7c8796; font-size: 12px; }.view-stats span { min-width: 76px; text-align: center; }.view-stats b { display: block; margin-top: 4px; color: #8d682d; font-size: 18px; }
.approval-view { border-left: 4px solid #d89548; background: linear-gradient(90deg, #fffaf3, #fff); }.approval-path { display: flex; align-items: center; flex-wrap: wrap; gap: 9px; margin-top: 16px; color: #795c2e; font-size: 13px; }.approval-path span { padding: 8px 12px; border: 1px solid #ebd8b8; border-radius: 20px; background: #fff; }.approval-path i { color: #bf913f; }
.analysis-view { border-left: 4px solid #4f8d8a; background: linear-gradient(90deg, #f5fbfa, #fff); }.analysis-chips { display: grid; grid-template-columns: repeat(4, minmax(100px, 1fr)); gap: 10px; margin-top: 14px; }.analysis-chips span { padding: 10px 12px; border: 1px solid #dbece9; border-radius: 8px; color: #28716c; background: #fff; font-size: 18px; font-weight: 700; }.analysis-chips b { display: block; margin-bottom: 4px; color: #70818c; font-size: 11px; font-weight: 500; }
.content-card { margin-top: 16px; border: 0; border-radius: 12px; }
.action-card ::v-deep .el-card__body { padding: 14px 18px; }
.workflow-card { border: 1px solid #ede4d2; background: #fffdfa; }
.workflow-heading { display: flex; justify-content: space-between; gap: 20px; align-items: center; margin-bottom: 16px; }
.workflow-heading h2 { margin: 0 0 5px; color: #513c1d; font-size: 17px; }.workflow-heading p { margin: 0; color: #788397; font-size: 12px; line-height: 1.6; }
.workflow-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.workflow-steps button { display: flex; align-items: center; gap: 10px; min-height: 62px; padding: 12px; border: 1px solid #e7dcc5; border-radius: 9px; color: #536176; background: #fff; cursor: pointer; text-align: left; }.workflow-steps button:hover, .workflow-steps button.active { border-color: #b6802d; color: #74501a; background: #fff8ea; }.workflow-steps b { display: grid; width: 25px; height: 25px; place-items: center; border-radius: 50%; color: white; background: #a97b31; font-size: 12px; }.workflow-steps span { flex: 1; font-weight: 700; }.workflow-steps em { color: #9a6a1f; font-size: 18px; font-style: normal; font-weight: 700; }
.card-heading, .table-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.card-heading h2 { margin: 0 0 4px; font-size: 16px; }
.card-heading p { margin: 0; color: #8a97a8; font-size: 12px; }
.filter-form { margin-bottom: -12px; }
.filter-form ::v-deep .el-form-item { margin-bottom: 16px; }
.filter-form ::v-deep .el-form-item__label, .record-form ::v-deep .el-form-item__label { padding-bottom: 5px; color: #607087; font-size: 12px; line-height: 18px; }
.exclusion-row { display: flex; align-items: center; flex-wrap: nowrap; gap: 18px; min-height: 42px; margin: 2px 0 14px; padding: 0 14px; overflow-x: auto; border: 1px solid #eee5cc; border-radius: 8px; color: #526176; background: #fffaf0; white-space: nowrap; }
.exclusion-row strong { flex: 0 0 auto; color: #8a6318; font-size: 13px; }
.exclusion-row ::v-deep .el-checkbox { flex: 0 0 auto; margin-right: 0; }
.full-control { width: 100%; }
.filter-toggle { display: block; margin: 5px auto -5px; border: 0; color: #a16d0b; background: transparent; cursor: pointer; }
.business-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.business-actions .el-button + .el-button { margin-left: 0; }
.selection-tip { flex: 0 0 auto; padding-top: 7px; color: #7d8999; font-size: 12px; }
.table-card ::v-deep .el-card__body { padding-top: 0; }
.business-tabs { padding: 0 4px; }
.business-tabs ::v-deep .el-tabs__header { margin-bottom: 12px; }
.business-tabs ::v-deep .el-tabs__item { height: 48px; padding: 0 24px; color: #66758a; font-weight: 700; line-height: 48px; }
.business-tabs ::v-deep .el-tabs__item.is-active { color: #a16d0b; }
.business-tabs ::v-deep .el-tabs__active-bar { background-color: #c58b1b; }
.table-card ::v-deep .el-table th { color: #43536a; background: #f8f5ed; }
.money { color: #d05f45; font-weight: 700; }
.pagination-row { display: flex; justify-content: space-between; align-items: center; padding-top: 18px; color: #8491a2; font-size: 12px; }
.receipt-form-card .record-form { max-height: none; }
.receipt-upload ::v-deep .el-upload { display: block; }
.receipt-upload ::v-deep .el-button { width: 100%; border-style: dashed; }
.receipt-upload ::v-deep .el-upload-list { margin-top: 6px; }
.picker-toolbar { display: flex; gap: 10px; margin-bottom: 14px; }
.picker-toolbar .el-input { flex: 1; }
.picker-total { float: left; color: #8a97a8; font-size: 12px; line-height: 36px; }
.form-tips { display: flex; flex-wrap: wrap; gap: 10px 22px; padding: 13px 15px; border-radius: 9px; color: #8a6318; background: #fff8e7; font-size: 12px; }
.form-tips i { margin-right: 5px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 18px; }
.dialog-alert { margin-bottom: 18px; }
.dialog-form { max-height: 56vh; padding-right: 12px; overflow-y: auto; }
.detail-drawer { padding: 0 22px 30px; }
.detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; font-size: 18px; }
.detail-drawer h3 { margin: 26px 0 14px; font-size: 15px; }
@media (max-width: 900px) {
  .finance-workbench { padding: 12px; }
  .hero-panel, .hero-actions, .table-toolbar, .pagination-row, .workflow-heading { align-items: flex-start; flex-direction: column; }
  .metric-strip { grid-template-columns: repeat(2, 1fr); }
  .ledger-view { grid-template-columns: 1fr; }.analysis-chips { grid-template-columns: repeat(2, 1fr); }
}
</style>
