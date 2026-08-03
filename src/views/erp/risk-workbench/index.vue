<template>
  <div class="risk-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow">风控服务 · 业务管理</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.domainDraft }}</p>
      </div>
      <div class="hero-evidence">
        <el-tag effect="dark" type="warning">{{ config.evidenceLevel }}</el-tag>
        <span>完成层级：{{ config.completionLevel }}</span>
      </div>
    </section>

    <el-alert
      class="evidence-alert"
      title="当前服务范围说明"
      :description="config.evidenceNote"
      type="warning"
      show-icon
      :closable="false"
    />

    <div class="evidence-grid">
      <div v-for="item in evidenceCards" :key="item.label" class="evidence-card">
        <i :class="item.icon" />
        <div><strong>{{ item.value }}</strong><span>{{ item.label }}</span></div>
      </div>
    </div>

    <el-card shadow="never" class="content-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>风险业务台账</h2>
          <p>标签、筛选、枚举和列名均待原系统二次核验，不视为原页面证据。</p>
        </div>
        <el-tag size="small" type="info">无真实业务写入</el-tag>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane
          v-for="tab in config.draftTabs"
          :key="tab.key"
          :name="tab.key"
        >
          <span slot="label">{{ tab.label }} <small>待核验</small></span>
        </el-tab-pane>
      </el-tabs>

      <div class="filter-panel">
        <div class="draft-label"><i class="el-icon-warning-outline" /> 查询条件</div>
        <el-form label-position="top" class="filter-form">
          <el-row :gutter="14">
            <el-col
              v-for="field in currentTab.filters"
              :key="field.key"
              :xl="4"
              :lg="6"
              :md="8"
              :sm="12"
              :xs="24"
            >
              <el-form-item>
                <span slot="label">{{ field.label }} <em>未核验</em></span>
                <el-select
                  v-if="field.type === 'select'"
                  v-model="filters[field.key]"
                  class="full-control"
                  clearable
                  placeholder="请选择"
                >
                  <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                </el-select>
                <el-date-picker
                  v-else-if="field.type === 'dateRange'"
                  v-model="filters[field.key]"
                  class="full-control"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="yyyy-MM-dd"
                />
                <el-input v-else v-model="filters[field.key]" clearable placeholder="请输入查询条件" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        <div class="local-query-actions">
          <el-button type="primary" icon="el-icon-search" @click="applyLocalFilter">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <span>筛选条件仅用于当前风险服务清单。</span>
        </div>
      </div>

      <div class="table-heading">
        <div>
          <strong>{{ currentTab.label }}</strong>
          <span>共 {{ filteredRows.length }} 条业务记录</span>
        </div>
        <el-tag size="mini" type="success">当前清单</el-tag>
      </div>

      <el-table :data="filteredRows" stripe border class="draft-table">
        <el-table-column type="index" label="#" width="52" />
        <el-table-column
          v-for="column in currentTab.columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :min-width="column.width"
          show-overflow-tooltip
        >
          <template slot-scope="scope">
            <el-tag
              v-if="column.format === 'tag'"
              size="mini"
              :type="tagType(scope.row[column.key])"
            >
              {{ scope.row[column.key] }}
            </el-tag>
            <span v-else>{{ scope.row[column.key] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="openDraft(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer
      title="风险记录详情"
      :visible.sync="drawerVisible"
      size="520px"
      custom-class="risk-draft-drawer"
    >
      <div class="drawer-body">
        <el-alert
          title="请核对记录内容后再进行业务处理。"
          type="warning"
          :closable="false"
          show-icon
        />
        <dl v-if="currentRow" class="draft-descriptions">
          <div
            v-for="column in currentTab.columns"
            :key="column.key"
          >
            <dt>{{ column.label }}</dt>
            <dd>{{ currentRow[column.key] || '—' }}</dd>
          </div>
        </dl>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { getRiskPageConfig } from '@/config/risk-pages'
import { getRiskModuleData } from '@/api/erp-risk'

export default {
  name: 'RiskWorkbenchPage',
  data() {
    return {
      activeTab: 'events',
      filters: {},
      appliedFilters: {},
      remoteEvidence: '',
      drawerVisible: false,
      currentRow: null
    }
  },
  computed: {
    pageTitle() {
      return this.$route.meta.title || '悦禧风控'
    },
    config() {
      return getRiskPageConfig(this.pageTitle)
    },
    currentTab() {
      return this.config.draftTabs.find(tab => tab.key === this.activeTab) || this.config.draftTabs[0]
    },
    evidenceCards() {
      return [
        { label: '已确认子菜单', value: '1', icon: 'el-icon-menu' },
        { label: '原页面已审计', value: '0', icon: 'el-icon-document-checked' },
        { label: '字段级已核验', value: '0', icon: 'el-icon-finished' },
        { label: '真实后端写入', value: '0', icon: 'el-icon-connection' }
      ]
    },
    demoRows() {
      if (this.activeTab === 'rules') return this.buildRuleRows()
      if (this.activeTab === 'dispositions') return this.buildDispositionRows()
      return this.buildEventRows()
    },
    filteredRows() {
      return this.demoRows.filter(row => {
        return Object.keys(this.appliedFilters).every(key => {
          const expected = this.appliedFilters[key]
          if (!expected || (Array.isArray(expected) && !expected.length)) return true
          if (Array.isArray(expected)) return true
          return String(row[key] || '').includes(String(expected))
        })
      })
    }
  },
  watch: {
    activeTab: {
      immediate: true,
      handler() {
        this.resetFilters()
      }
    },
    '$route.meta.title': function() {
      this.activeTab = this.config.draftTabs[0].key
      this.loadDraftEvidence()
    }
  },
  created() {
    this.loadDraftEvidence()
  },
  methods: {
    async loadDraftEvidence() {
      try {
        const response = await getRiskModuleData(this.config.key, { draftOnly: true })
        this.remoteEvidence = response.data.evidenceLevel
      } catch (error) {
        this.remoteEvidence = '服务状态暂不可用'
      }
    },
    resetFilters() {
      const next = {}
      this.currentTab.filters.forEach(field => {
        next[field.key] = field.type === 'dateRange' ? [] : ''
      })
      this.filters = next
      this.appliedFilters = {}
    },
    applyLocalFilter() {
      this.appliedFilters = { ...this.filters }
      this.$message.info('已按当前条件筛选风险服务清单')
    },
    openDraft(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    buildEventRows() {
      const modules = ['合同', '财务', '客房', '护理', '仓存']
      const levels = ['中', '高', '低']
      const statuses = ['待确认', '跟进中', '已关闭']
      const customers = ['李女士', '王女士', '张女士', '赵女士', '陈女士', '刘女士']
      const owners = ['李顾问', '王主管', '张护士']
      return Array.from({ length: 6 }, (_, index) => ({
        riskNo: `RISK-202608-${String(index + 1).padStart(4, '0')}`,
        sourceModule: modules[index % modules.length],
        eventSummary: `业务风险跟进 ${index + 1}`,
        businessObject: customers[index],
        store: this.config.stores[index % this.config.stores.length],
        riskLevel: levels[index % levels.length],
        occurredAt: `2026-07-${String(12 + index).padStart(2, '0')} 10:20`,
        owner: owners[index % owners.length],
        status: statuses[index % statuses.length]
      }))
    },
    buildDispositionRows() {
      return this.buildEventRows().map((row, index) => ({
        ...row,
        lastAction: `脱敏跟进摘要 ${index + 1}`,
        nextActionAt: index % 3 === 2 ? '—' : `2026-07-${String(24 + index).padStart(2, '0')} 09:30`,
        updatedAt: `2026-07-${String(20 + index).padStart(2, '0')} 16:10`
      }))
    },
    buildRuleRows() {
      const modules = ['合同', '财务', '客房', '护理', '仓存']
      return Array.from({ length: 5 }, (_, index) => ({
        ruleCode: `RULE-DEMO-${String(index + 1).padStart(3, '0')}`,
        ruleName: `脱敏异常规则草案 ${index + 1}`,
        sourceModule: modules[index % modules.length],
        triggerSummary: '待原系统核验触发字段、运算符、阈值和组合关系',
        riskLevel: ['中', '高', '低'][index % 3],
        enabled: index % 4 ? '启用' : '停用',
        updatedBy: `演示维护人${index % 2 + 1}`,
        updatedAt: `2026-07-${String(15 + index).padStart(2, '0')} 14:30`
      }))
    },
    tagType(value) {
      if (/高|停用/.test(value)) return 'danger'
      if (/中|待确认/.test(value)) return 'warning'
      if (/低|已关闭|启用/.test(value)) return 'success'
      return 'primary'
    }
  }
}
</script>

<style lang="scss" scoped>
.risk-workbench {
  min-height: calc(100vh - 84px);
  padding: 22px;
  color: #2c3546;
  background: #f6f4f5;
}
.hero-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 26px 30px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(125deg, #28241e 0%, #5f4b2d 56%, #a68045 100%);
  box-shadow: 0 14px 34px rgba(74, 55, 26, .2);
}
.eyebrow {
  margin-bottom: 8px;
  color: #f3dfb7;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .8px;
}
.hero-panel h1 {
  margin: 0 0 8px;
  font-size: 28px;
}
.hero-panel p {
  max-width: 790px;
  margin: 0;
  color: #ffecee;
  font-size: 14px;
  line-height: 1.7;
}
.hero-evidence {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 10px;
}
.hero-evidence span {
  color: #ffecee;
  font-size: 12px;
}
.evidence-alert {
  margin-top: 14px;
  border-radius: 10px;
}
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 16px;
}
.evidence-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 17px 19px;
  border: 1px solid #eee5e7;
  border-radius: 12px;
  background: #fff;
}
.evidence-card > i {
  display: grid;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: #b44755;
  background: #fbeaed;
  font-size: 20px;
  place-items: center;
}
.evidence-card strong,
.evidence-card span {
  display: block;
}
.evidence-card strong {
  color: #913845;
  font-size: 23px;
}
.evidence-card span {
  margin-top: 2px;
  color: #7d8797;
  font-size: 12px;
}
.content-card {
  margin-top: 16px;
  border: 0;
  border-radius: 12px;
}
.card-heading,
.table-heading,
.local-query-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}
.card-heading h2 {
  margin: 0 0 5px;
  font-size: 17px;
}
.card-heading p {
  margin: 0;
  color: #8793a4;
  font-size: 12px;
}
.content-card ::v-deep .el-tabs__item small {
  margin-left: 3px;
  color: #c45a66;
  font-size: 10px;
}
.filter-panel {
  margin: 4px 0 18px;
  padding: 17px 18px;
  border: 1px dashed #e2c8cc;
  border-radius: 10px;
  background: #fffafb;
}
.draft-label {
  margin-bottom: 14px;
  color: #9a3e4b;
  font-size: 12px;
  font-weight: 700;
}
.filter-form {
  margin-bottom: -10px;
}
.filter-form ::v-deep .el-form-item {
  margin-bottom: 14px;
}
.filter-form ::v-deep .el-form-item__label {
  padding-bottom: 4px;
  color: #5f6b7b;
  font-size: 12px;
  line-height: 18px;
}
.filter-form em {
  color: #c45a66;
  font-size: 10px;
  font-style: normal;
}
.full-control {
  width: 100%;
}
.local-query-actions {
  justify-content: flex-start;
  flex-wrap: wrap;
  padding-top: 4px;
}
.local-query-actions span {
  color: #9a8790;
  font-size: 11px;
}
.table-heading {
  margin: 4px 0 12px;
}
.table-heading strong {
  display: block;
}
.table-heading span {
  display: block;
  margin-top: 3px;
  color: #8995a4;
  font-size: 11px;
}
.draft-table ::v-deep th {
  color: #4c596c;
  background: #fbf5f6;
}
.drawer-body {
  padding: 0 22px 28px;
}
.draft-descriptions {
  margin-top: 18px;
  border-top: 1px solid #ebeef5;
  border-left: 1px solid #ebeef5;
}
.draft-descriptions > div {
  display: grid;
  grid-template-columns: 130px 1fr;
}
.draft-descriptions dt,
.draft-descriptions dd {
  margin: 0;
  padding: 11px 13px;
  border-right: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
}
.draft-descriptions dt {
  color: #606266;
  background: #fafafa;
  font-size: 12px;
  font-weight: 700;
}
.draft-descriptions dd {
  color: #303133;
  font-size: 13px;
}
@media (max-width: 900px) {
  .risk-workbench {
    padding: 12px;
  }
  .hero-panel,
  .hero-evidence {
    align-items: flex-start;
    flex-direction: column;
  }
  .evidence-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
