<template>
  <div class="report-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i class="el-icon-data-analysis" /> 查询报表 · 独立工作台草案</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-status">
        <el-tag type="warning" effect="dark">待原系统二次核验</el-tag>
        <span>{{ config.family }}类报表</span>
      </div>
    </section>

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
        <strong>Visible</strong>
        <small>Mock 演示，未接真实后端</small>
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
          <h2>报表数据 <el-tag size="mini" type="info">脱敏演示</el-tag></h2>
          <p>未启用汇总行、公式、导出或打印；这些能力必须以原 ERP 证据为准</p>
        </div>
        <span class="result-count">共 {{ filteredRows.length }} 条演示记录</span>
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

export default {
  name: 'ReportWorkbench',
  data() {
    return {
      filters: {},
      rows: [],
      loading: false,
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
    pageTitle() {
      return this.$route.meta.title
    },
    config() {
      return getReportPageConfig(this.pageTitle)
    },
    evidenceMessage() {
      return `当前仓库“查询报表”菜单仅有 ${this.repositoryMenuCount} 项，与任务要求的 ${this.expectedMenuCount} 项相差 1 项；本页筛选、列、枚举、公式、导出与打印均待原系统二次核验。`
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
      this.filters = next
      this.pagination.page = 1
    },
    async loadData() {
      this.loading = true
      try {
        const response = await getReportModuleData(this.config.key, this.filters)
        const list = response.data && response.data.list
        this.rows = list && list.length ? list : this.createDemoRows()
      } catch (error) {
        this.rows = this.createDemoRows()
      } finally {
        this.loading = false
      }
    },
    runQuery(action) {
      this.pagination.page = 1
      this.$message.success(`${action}仅执行本地脱敏演示筛选，原系统查询规则待二次核验`)
    },
    createDemoRows() {
      return Array.from({ length: 12 }, (_, index) => {
        const row = { id: `${this.config.key}-${index + 1}` }
        this.config.columns.forEach(item => {
          row[item.key] = this.sampleValue(item, index)
        })
        return row
      })
    },
    sampleValue(item, index) {
      if (item.format === 'money') return `¥ ${(1200 + index * 185).toLocaleString('zh-CN')}`
      if (item.format === 'count') return 3 + index
      if (item.format === 'percent') return `${72 + index % 8}.0%`
      const letter = String.fromCharCode(65 + index % 6)
      const samples = {
        statDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        saleDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        consumeDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        receiptDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        serviceDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        recordDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        rechargeDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        checkoutDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        transactionDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        shareDate: `2026-07-${String(10 + index).padStart(2, '0')}`,
        plannedCheckInDate: `2026-08-${String(3 + index).padStart(2, '0')}`,
        plannedCheckOutDate: `2026-08-${String(15 + index).padStart(2, '0')}`,
        statMonth: '2026-07',
        statPeriod: '2026-07',
        store: index % 2 ? '黄河路轻奢店' : '中心广场旗舰店',
        sourceStore: index % 2 ? '中心广场旗舰店' : '黄河路轻奢店',
        customerName: `演示客户${letter}`,
        babyName: `演示宝宝${letter}`,
        salesperson: `演示员工${letter}`,
        serviceStaff: `演示员工${letter}`,
        technician: `演示技师${letter}`,
        operator: `演示员工${letter}`,
        receiver: `演示员工${letter}`,
        referrer: `演示推荐人${letter}`,
        roomNo: `${2 + index % 4}0${1 + index % 8}`,
        contractNo: `HT-DEMO-${String(index + 1).padStart(4, '0')}`,
        documentNo: `DJ-DEMO-${String(index + 1).padStart(4, '0')}`,
        cardNo: `CARD-DEMO-${String(index + 1).padStart(4, '0')}`,
        department: '演示部门',
        serviceName: '演示服务项目',
        itemName: '演示商品',
        productName: '演示商品',
        contentTitle: '演示分享内容',
        remark: '仅用于页面演示'
      }
      return Object.prototype.hasOwnProperty.call(samples, item.key) ? samples[item.key] : '演示值'
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
  background: linear-gradient(128deg, #315db8, #548ff0 62%, #62a8ef);
  box-shadow: 0 13px 30px rgba(52, 93, 172, .2);
}
.eyebrow {
  margin-bottom: 9px;
  color: #dceaff;
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
}
</style>
