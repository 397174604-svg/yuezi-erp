<template>
  <div class="people-workbench" data-people-workbench>
    <header class="hero">
      <div>
        <small>{{ definition.featureId }} · 人事组织与绩效</small>
        <h1>{{ definition.title }}</h1>
        <p>{{ definition.description }}</p>
      </div>
      <div class="hero-actions">
        <el-button size="small" @click="loadRows">刷新</el-button>
        <el-button type="primary" size="small" @click="pending(definition.primaryAction)">{{ definition.primaryAction }}</el-button>
      </div>
    </header>

    <el-card shadow="never" class="metrics">
      <div><b>{{ rows.length }}</b><span>当前记录</span></div>
      <div><b>{{ definition.scope }}</b><span>数据范围</span></div>
      <div><b>{{ definition.resource ? '业务数据' : '配置中' }}</b><span>数据状态</span></div>
      <div><b>{{ definition.flow }}</b><span>处理方式</span></div>
    </el-card>

    <el-card shadow="never" class="query">
      <el-form :inline="true" size="small">
        <el-form-item v-for="field in definition.filters" :key="field.key" :label="field.label">
          <el-input v-model="filters[field.key]" :placeholder="`请输入${field.label}`" clearable />
        </el-form-item>
        <el-button type="primary" icon="el-icon-search" @click="loadRows">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-button v-if="rows.length" icon="el-icon-download" @click="exportRows">导出当前结果</el-button>
      </el-form>
    </el-card>

    <el-alert v-if="loadError || !definition.resource" :title="loadError || definition.pendingMessage" type="info" :closable="false" show-icon class="notice" />
    <el-card shadow="never" class="table-card">
      <div slot="header" class="table-header">
        <strong>{{ definition.title }}列表</strong>
        <span>仅展示当前权限与门店范围内的真实数据</span>
      </div>
      <el-table v-loading="loading" :data="displayRows" border stripe height="510" :empty-text="emptyText">
        <el-table-column type="index" width="56" label="#" />
        <el-table-column v-for="column in definition.columns" :key="column.key" :prop="column.key" :label="column.label" :min-width="column.width || 145" show-overflow-tooltip />
        <el-table-column label="操作" width="130" fixed="right">
          <template slot-scope="{ row }">
            <el-button type="text" size="mini" @click="pending('查看详情', row)">查看</el-button>
            <el-button type="text" size="mini" @click="pending(definition.rowAction, row)">{{ definition.rowAction }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getBasicModuleData } from '@/api/erp-basic'

const makeColumns = entries => entries.map(([key, label]) => ({ key, label }))
const makeFilters = entries => entries.map(([key, label]) => ({ key, label }))
const waiting = (featureId, title, description, columns, filters, scope = '按门店', flow = '规则确认中') => ({
  featureId,
  title,
  description,
  columns: makeColumns(columns),
  filters: makeFilters(filters),
  scope,
  flow,
  resource: '',
  primaryAction: `新增${title}`,
  rowAction: '查看规则',
  pendingMessage: `${title}的业务规则正在确认，暂未开放记录办理。`
})

const definitions = {
  '护理二次销售业绩': waiting('F025', '护理二次销售业绩', '汇总护理增购、转化与归属人员，作为提成计算的业务来源。', [['staff', '护理人员'], ['store', '门店'], ['salesAmount', '增购金额'], ['conversionCount', '转化单数'], ['status', '核算状态']], [['staff', '护理人员'], ['period', '统计期间']]),
  '品项与提成': waiting('F047', '品项与提成', '维护服务品项与岗位提成归属关系，不与客户订单列表混用。', [['itemCode', '品项编码'], ['item', '品项名称'], ['position', '适用岗位'], ['commissionType', '提成类型'], ['status', '状态']], [['item', '品项名称'], ['position', '适用岗位']], '总部规则', '审批生效'),
  '提成方案': waiting('F048', '提成方案', '按岗位、业绩区间和系数维护阶梯提成，变更应留存审批版本。', [['planNo', '方案编号'], ['plan', '方案名称'], ['position', '适用岗位'], ['effectiveDate', '生效日期'], ['status', '审批状态']], [['plan', '方案名称'], ['position', '适用岗位']], '总部规则', '审批生效'),
  '项目耗材BOM': waiting('F049', '项目耗材BOM', '定义项目耗材用量与成本归集，供库存出库和项目成本核算使用。', [['projectCode', '项目编码'], ['project', '项目名称'], ['material', '耗材名称'], ['quantity', '标准用量'], ['cost', '参考成本']], [['project', '项目名称'], ['material', '耗材名称']], '按门店', '成本联动'),
  '目标管理': waiting('F051', '目标管理', '按门店、部门与岗位分解经营目标，避免与员工档案共用同一张表。', [['targetNo', '目标编号'], ['targetName', '目标名称'], ['owner', '责任人'], ['period', '目标周期'], ['status', '状态']], [['store', '门店'], ['period', '目标周期']]),
  '员工与组织': {
    featureId: 'F052', title: '员工与组织', description: '查询员工、岗位、部门与所属门店，统一维护员工主档。', resource: 'employee-records', scope: '按门店', flow: '员工主档', primaryAction: '新增员工', rowAction: '查看档案', pendingMessage: '',
    filters: makeFilters([['employeeName', '员工姓名'], ['department', '部门'], ['store', '门店']]),
    columns: makeColumns([['employeeNo', '员工编号'], ['employeeName', '员工姓名'], ['department', '部门'], ['position', '岗位'], ['store', '门店'], ['mobile', '联系方式'], ['status', '状态']])
  },
  '角色权限': waiting('F053', '角色权限', '维护岗位角色与功能权限边界，不把权限清单混入员工主档。', [['roleCode', '角色编码'], ['role', '角色名称'], ['scope', '数据范围'], ['owner', '维护人'], ['status', '状态']], [['role', '角色名称']], '总部规则', '授权审批'),
  '品控检查': waiting('F054', '品控检查', '记录检查评分、问题项与整改闭环，避免与绩效列表使用同一状态。', [['inspectionNo', '检查单号'], ['store', '门店'], ['inspector', '检查人'], ['score', '得分'], ['status', '整改状态']], [['store', '门店'], ['inspector', '检查人']], '按门店', '检查整改'),
  '品控看板': waiting('F055', '品控看板', '按部门汇总质量评分与积分趋势，与单次品控检查页面分离。', [['department', '部门'], ['averageScore', '平均得分'], ['issueCount', '问题数'], ['closedRate', '整改完成率'], ['rank', '排名']], [['store', '门店'], ['period', '统计期间']], '按门店', '只读统计'),
  '员工业绩看板': waiting('F096', '员工业绩看板', '按个人、团队和门店查看绩效结果，与目标管理和提成结算分开。', [['employee', '员工'], ['team', '团队'], ['score', '绩效得分'], ['targetRate', '目标达成率'], ['status', '状态']], [['store', '门店'], ['period', '统计期间']], '按门店', '只读统计'),
  '员工提成/绩效计算': waiting('F126', '员工提成/绩效计算', '按已审批业务、提成方案和绩效周期计算应发金额，不能手工伪造结果。', [['calculationNo', '核算单号'], ['employee', '员工'], ['period', '核算周期'], ['amount', '应发金额'], ['status', '审批状态']], [['employee', '员工'], ['period', '核算周期']], '按门店', '核算审批')
}

const normalizePeopleTitle = value => String(value || '')
  .replace(/\s*★\s*$/, '')
  .replace(/\s*[（(][^）)]*[）)]\s*/g, '')
  .trim()

export default {
  name: 'PeopleWorkbench',
  data() { return { rows: [], loading: false, loadError: '', filters: {}, loadSequence: 0 } },
  computed: {
    pageTitle() {
      return normalizePeopleTitle((this.$route.meta && (this.$route.meta.configTitle || this.$route.meta.title)) || '')
    },
    definition() { return definitions[normalizePeopleTitle(this.pageTitle)] || definitions['员工与组织'] },
    displayRows() {
      const values = Object.values(this.filters).map(value => String(value || '').trim()).filter(Boolean)
      return values.length ? this.rows.filter(row => values.every(value => Object.values(row).some(cell => String(cell || '').includes(value)))) : this.rows
    },
    emptyText() { return this.loadError || this.definition.pendingMessage || '暂无符合条件的员工记录' }
  },
  watch: {
    '$route.fullPath': { immediate: true, handler() { this.filters = {}; this.loadRows() } }
  },
  methods: {
    async loadRows() {
      const sequence = ++this.loadSequence
      const resource = this.definition.resource
      this.rows = []
      this.loadError = ''
      if (!resource) return
      this.loading = true
      try {
        const response = await getBasicModuleData(resource, { storeId: this.$route.query.storeId || 'all' })
        if (this.loadSequence === sequence) this.rows = response.data && Array.isArray(response.data.list) ? response.data.list : []
      } catch (error) {
        if (this.loadSequence === sequence) this.loadError = '员工组织数据查询失败，请稍后重试。'
      } finally { if (this.loadSequence === sequence) this.loading = false }
    },
    resetFilters() { this.filters = {}; this.loadRows() },
    pending(action) { this.$message.info(`“${action}”需要完成对应业务接口与审批规则接入后才能执行。`) },
    exportRows() {
      const header = this.definition.columns.map(column => column.label).join(',')
      const body = this.displayRows.map(row => this.definition.columns.map(column => `"${String(row[column.key] || '').replace(/"/g, '""')}"`).join(','))
      const url = URL.createObjectURL(new Blob([[header, ...body].join('\n')], { type: 'text/csv;charset=utf-8;' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `${this.definition.featureId}-${this.definition.title}.csv`
      link.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style lang="scss" scoped>
.people-workbench { min-height: calc(100vh - 84px); padding: 20px; background: #f3f6fa; color: #26354c; }
.hero { display: flex; justify-content: space-between; gap: 18px; padding: 20px 22px; border-radius: 12px; color: #fff; background: linear-gradient(110deg, #4b3e2c, #ab8244); }
.hero small, .hero p { opacity: .84; }.hero h1 { margin: 6px 0; font-size: 25px; }.hero p { margin: 0; font-size: 13px; }.hero-actions { white-space: nowrap; }
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 14px; border: 0; }.metrics div { display: grid; gap: 5px; padding: 10px 20px; border-right: 1px solid #edf0f5; }.metrics div:last-child { border: 0; }.metrics b { color: #9b7337; font-size: 18px; }.metrics span, .table-header span { color: #8390a4; font-size: 12px; }
.query, .table-card { margin-top: 14px; border: 0; }.notice { margin-top: 14px; }.table-header { display: flex; justify-content: space-between; }.table-card ::v-deep .el-table th { background: #f7f0e3; color: #695837; }
@media (max-width: 900px) { .hero { display: block; }.hero-actions { margin-top: 12px; }.metrics { grid-template-columns: repeat(2, 1fr); } }
</style>
