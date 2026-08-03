<template>
  <div class="report-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i class="el-icon-data-analysis" /> 查询报表 · 经营数据分析</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-status">
        <el-tag :type="config.dataState === 'pending' ? 'warning' : 'success'" effect="dark">{{ dataStateLabel }}</el-tag>
        <span>{{ config.family }}类报表</span>
      </div>
    </section>

    <section v-if="config.presentation === 'report-builder'" class="report-mode-card builder-mode">
      <div><i class="el-icon-set-up" /><strong>自定义报表入口</strong><p>当前仅开放已接入数据的筛选、查询和 CSV 导出。自定义字段、公式、图表和打印模板尚未接入，不展示模拟预览。</p></div>
      <div class="mode-steps"><span>选择已接入报表</span><i class="el-icon-right" /><span>配置筛选条件</span><i class="el-icon-right" /><span>导出当前结果</span></div>
    </section>

    <section v-if="config.presentation === 'monthly-operation'" class="report-mode-card monthly-mode">
      <div><i class="el-icon-date" /><strong>经营月报口径</strong><p>以本月已落库收款为基础汇总；退款、付款、成本在对应真实流水未接入前保持为空或零值。</p></div>
      <div class="mode-steps"><span>门店范围</span><i class="el-icon-right" /><span>统计月份</span><i class="el-icon-right" /><span>月度导出</span></div>
    </section>

    <el-alert v-if="config.presentation === 'pending'" title="该报表的数据口径正在确认，暂不展示未经确认的汇总结果。" type="info" :closable="false" show-icon class="evidence-alert" />

    <el-alert
      :title="evidenceMessage"
      type="warning"
      :closable="false"
      show-icon
      class="evidence-alert"
    />

    <section class="audit-grid">
      <div class="audit-card">
        <span>仓库菜单证据</span>
        <strong>{{ repositoryMenuCount }} / {{ expectedMenuCount }}</strong>
        <small>少 1 项，禁止自行补造</small>
      </div>
      <div class="audit-card">
        <span>本页筛选草案</span>
        <strong>{{ config.filters.length }}</strong>
        <small>标签、顺序、枚举均待核验</small>
      </div>
      <div class="audit-card">
        <span>本页列草案</span>
        <strong>{{ config.columns.length }}</strong>
        <small>列顺序与汇总口径待核验</small>
      </div>
      <div class="audit-card">
        <span>完成等级</span>
        <strong>Query</strong>
        <small>按当前筛选范围查询</small>
      </div>
    </section>

    <el-card shadow="never" class="content-card filter-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>查询条件 <el-tag size="mini" type="warning">草案</el-tag></h2>
          <p>未设置推测的默认日期；每个字段均标记为待原系统二次核验</p>
        </div>
        <div class="query-actions">
          <el-button size="small" icon="el-icon-delete" @click="resetFilters">清空</el-button>
          <el-button
            v-for="action in config.queryActions"
            :key="action"
            size="small"
            type="primary"
            icon="el-icon-search"
            @click="runQuery(action)"
          >{{ action }}</el-button>
        </div>
      </div>
      <el-form label-position="top" class="filter-form">
        <el-row :gutter="16">
          <el-col
            v-for="item in config.filters"
            :key="item.key"
            :xl="4"
            :lg="6"
            :md="8"
            :sm="12"
            :xs="24"
          >
            <el-form-item>
              <template slot="label">
                <span>{{ item.label }}</span>
                <em>待核验</em>
              </template>
              <el-select
                v-if="item.type === 'select'"
                v-model="filters[item.key]"
                clearable
                filterable
                placeholder="请选择"
                class="full-control"
              >
                <el-option
                  v-for="option in item.options"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>
              <el-date-picker
                v-else-if="item.type === 'dateRange'"
                v-model="filters[item.key]"
                type="daterange"
                value-format="yyyy-MM-dd"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                class="full-control"
              />
              <el-input
                v-else
                v-model="filters[item.key]"
                clearable
                :placeholder="`请输入${item.label}`"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card shadow="never" class="content-card table-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>报表数据 <el-tag size="mini" type="success">实时</el-tag></h2>
          <p>当前结果支持 CSV 导出；汇总公式和打印版式仍待业务口径确认</p>
        </div>
        <div class="query-actions">
          <span class="result-count">共 {{ filteredRows.length }} 条记录</span>
          <el-button size="small" icon="el-icon-download" :disabled="!filteredRows.length" @click="exportRows">导出当前结果</el-button>
        </div>
      </div>
      <el-table
        v-loading="loading"
        :data="pagedRows"
        border
        stripe
        height="520"
      >
        <el-table-column type="index" label="序号" width="58" fixed="left" :index="tableIndex" />
        <el-table-column
          v-for="item in config.columns"
          :key="item.key"
          :prop="item.key"
          :label="item.label"
          :min-width="item.width || 120"
          show-overflow-tooltip
        >
          <template slot-scope="scope">
            <span :class="`format-${item.format}`">{{ scope.row[item.key] }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>显示第 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
        <el-pagination
          background
          layout="prev, pager, next, sizes"
          :current-page.sync="pagination.page"
          :page-size.sync="pagination.size"
          :page-sizes="[10, 20, 50]"
          :total="filteredRows.length"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="content-card gap-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>本页待核验项</h2>
          <p>完成逐页只读审计后，再把结构草案提升到 Schema-faithful</p>
        </div>
      </div>
      <div class="gap-list">
        <el-tag v-for="gap in auditGaps" :key="gap" type="warning" effect="plain">{{ gap }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script>
import {
  getReportPageConfig,
  REPORT_EXPECTED_MENU_COUNT,
  REPORT_REPOSITORY_MENU_COUNT
} from '@/config/report-pages'
import { getReportModuleData } from '@/api/erp-report'
import { mapGetters } from 'vuex'

export default {
  name: 'ReportWorkbench',
  data() {
    return {
      filters: {},
      rows: [],
      loading: false,
      loadSequence: 0,
      pagination: {
        page: 1,
        size: 10
      },
      expectedMenuCount: REPORT_EXPECTED_MENU_COUNT,
      repositoryMenuCount: REPORT_REPOSITORY_MENU_COUNT,
      auditGaps: [
        '原 URL / navid',
        '筛选标签与顺序',
        '下拉选项与默认值',
        '日期默认范围',
        '工具栏标签与顺序',
        '表头与隐藏列',
        '汇总公式与口径',
        '导出模板',
        '打印版式',
        '权限隐藏行为'
      ]
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    pageTitle() {
      return String(this.$route.meta.configTitle || this.$route.meta.title || '').replace(/\s*★\s*$/, '')
    },
    config() {
      return getReportPageConfig(this.pageTitle)
    },
    evidenceMessage() {
      return `当前仓库“查询报表”菜单仅有 ${this.repositoryMenuCount} 项，与任务要求的 ${this.expectedMenuCount} 项相差 1 项；本页筛选、列、枚举、公式、导出与打印均待原系统二次核验。`
    },
    dataStateLabel() {
      return this.config.dataState === 'pending' ? '口径确认中' : '经营数据查询'
    },
    filteredRows() {
      const entries = Object.entries(this.filters).filter(([, value]) => {
        return value !== '' && value !== null && (!Array.isArray(value) || value.length)
      })
      if (!entries.length) return this.rows
      return this.rows.filter(row => entries.every(([key, value]) => {
        if (Array.isArray(value)) return true
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
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    }
  },
  methods: {
    initializePage() {
      this.pagination.page = 1
      this.resetFilters()
      this.loadData()
    },
    resetFilters() {
      const next = {}
      this.config.filters.forEach(item => {
        next[item.key] = item.type === 'dateRange' ? [] : ''
      })
      const routeStoreId = Number(this.$route.query.storeId)
      const routeStores = { 1: '中心广场旗舰店', 2: '黄河路轻奢店' }
      if (next.store !== undefined && routeStores[routeStoreId]) {
        next.store = routeStores[routeStoreId]
      }
      this.filters = next
      this.pagination.page = 1
    },
    async loadData() {
      const sequence = ++this.loadSequence
      const resource = this.config.key
      this.loading = true
      try {
        const response = await getReportModuleData(resource, {
          ...this.filters,
          storeId: this.currentStoreId || 'all'
        })
        const list = response.data && response.data.list
        if (this.loadSequence !== sequence) return false
        this.rows = Array.isArray(list) ? list : []
        return true
      } catch (error) {
        if (this.loadSequence !== sequence) return false
        this.rows = []
        this.$message.error('报表查询失败，请稍后重试')
        return false
      } finally {
        if (this.loadSequence === sequence) this.loading = false
      }
    },
    async runQuery(action) {
      this.pagination.page = 1
      const loaded = await this.loadData()
      if (!loaded) return this.$message.warning('查询未完成，请检查条件后重试')
      if (loaded) {
        this.$message.success(`${action}已按当前门店和查询条件刷新`)
      }
    },
    exportRows() {
      if (!this.filteredRows.length) return
      const columns = this.config.columns
      const escape = value => `"${String(value === null || value === undefined ? '' : value).replace(/"/g, '""')}"`
      const lines = [
        columns.map(column => escape(column.label)).join(','),
        ...this.filteredRows.map(row => columns.map(column => escape(row[column.key])).join(','))
      ]
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    },
    tableIndex(index) {
      return (this.pagination.page - 1) * this.pagination.size + index + 1
    }
  }
}
</script>

<style lang="scss" scoped>
.report-workbench {
  min-height: 100%;
  padding: 20px;
  background: #f4f7fb;
}
.hero-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 25px 28px;
  border-radius: 15px;
  color: #fff;
  background: linear-gradient(125deg, #28241e 0%, #5f4b2d 56%, #a68045 100%);
  box-shadow: 0 14px 34px rgba(74, 55, 26, .2);
}
.eyebrow {
  margin-bottom: 9px;
  color: #f3dfb7;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .6px;
}
.hero-panel h1 {
  margin: 0 0 8px;
  font-size: 27px;
}
.hero-panel p {
  max-width: 760px;
  margin: 0;
  color: #e7f1ff;
  font-size: 14px;
  line-height: 1.7;
}
.hero-status {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 10px;
}
.hero-status span {
  color: #e9f3ff;
  font-size: 12px;
}
.evidence-alert {
  margin-top: 14px;
  border-radius: 10px;
}
.audit-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 16px;
}
.audit-card {
  padding: 17px 19px;
  border: 1px solid #e3eaf4;
  border-radius: 12px;
  background: #fff;
}
.audit-card span,
.audit-card strong,
.audit-card small {
  display: block;
}
.audit-card span {
  color: #76869d;
  font-size: 12px;
}
.audit-card strong {
  margin: 7px 0 5px;
  color: #345fae;
  font-size: 22px;
}
.audit-card small {
  color: #9aa6b6;
  font-size: 11px;
}
.report-mode-card { display: flex; justify-content: space-between; align-items: center; gap: 22px; margin-top: 16px; padding: 17px 20px; border: 1px solid #dfe7ef; border-radius: 12px; background: #fff; }.report-mode-card > div:first-child { display: grid; grid-template-columns: 26px 1fr; column-gap: 10px; }.report-mode-card > div:first-child > i { grid-row: span 2; padding-top: 2px; color: #997037; font-size: 21px; }.report-mode-card strong { color: #46576a; font-size: 15px; }.report-mode-card p { grid-column: 2; margin: 5px 0 0; color: #738195; font-size: 12px; line-height: 1.55; }.builder-mode { border-left: 4px solid #b58635; }.monthly-mode { border-left: 4px solid #467f98; background: linear-gradient(90deg, #f7fbfe, #fff); }.mode-steps { display: flex; flex: 0 0 auto; align-items: center; gap: 8px; color: #63758a; font-size: 12px; }.mode-steps span { padding: 7px 10px; border: 1px solid #dce4ed; border-radius: 16px; background: #fff; white-space: nowrap; }.mode-steps i { color: #b4863d; }
.content-card {
  margin-top: 16px;
  border: 0;
  border-radius: 12px;
}
.card-heading,
.pagination-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.card-heading h2 {
  margin: 0 0 4px;
  font-size: 16px;
}
.card-heading p {
  margin: 0;
  color: #8996a8;
  font-size: 12px;
}
.filter-form {
  margin-bottom: -12px;
}
.filter-form ::v-deep .el-form-item {
  margin-bottom: 16px;
}
.filter-form ::v-deep .el-form-item__label {
  display: flex;
  align-items: center;
  gap: 7px;
  padding-bottom: 5px;
  color: #596b82;
  font-size: 12px;
  line-height: 18px;
}
.filter-form ::v-deep .el-form-item__label em {
  color: #d4982f;
  font-size: 10px;
  font-style: normal;
}
.full-control {
  width: 100%;
}
.table-card ::v-deep .el-card__body {
  padding-top: 14px;
}
.table-card ::v-deep .el-table th {
  color: #40546e;
  background: #f5f8fd;
}
.format-money {
  color: #c06a2e;
  font-weight: 600;
}
.format-percent {
  color: #34886c;
  font-weight: 600;
}
.result-count,
.pagination-row {
  color: #8593a6;
  font-size: 12px;
}
.pagination-row {
  padding-top: 18px;
}
.gap-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}
@media (max-width: 1000px) {
  .audit-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 760px) {
  .report-workbench {
    padding: 12px;
  }
  .hero-panel,
  .hero-status,
  .card-heading,
  .pagination-row {
    align-items: flex-start;
    flex-direction: column;
  }
  .audit-grid {
    grid-template-columns: 1fr;
  }
  .report-mode-card { align-items: flex-start; flex-direction: column; }
  .mode-steps { flex-wrap: wrap; }
}
</style>
