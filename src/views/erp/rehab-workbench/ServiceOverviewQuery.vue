<template>
  <div class="service-overview-query" data-service-overview-query>
    <section class="mode-bar">
      <div>
        <strong>服务综合查询</strong>
      </div>
      <el-button-group data-mode-switch>
        <el-button
          size="small"
          :type="viewMode === 'card' ? 'primary' : 'default'"
          data-mode="card"
          @click="switchMode('card')"
        >
          <i class="el-icon-s-grid" /> 图形
        </el-button>
        <el-button
          size="small"
          :type="viewMode === 'list' ? 'primary' : 'default'"
          data-mode="list"
          @click="switchMode('list')"
        >
          <i class="el-icon-s-unfold" /> 列表
        </el-button>
      </el-button-group>
    </section>

    <template v-if="viewMode === 'card'">
      <el-card shadow="never" class="overview-card customer-query-card" data-card-query>
        <div class="customer-query-row">
          <label class="query-pair" data-card-field="cardNumber">
            <span>会员卡号:</span>
            <el-input v-model="cardNumber" size="small" />
          </label>
          <el-button size="small" data-card-action="读 卡" @click="readCardDialogVisible = true">读 卡</el-button>

          <label class="query-pair customer-pair" data-card-field="customerName">
            <span>请选择客户:</span>
            <el-input v-model="selectedCustomerName" size="small" />
          </label>
          <el-button size="small" data-card-action="选择客户" @click="openCustomerDialog">选择客户</el-button>

          <em>注：店内客户及散客均支持查询</em>
          <el-button size="small" data-card-action="项目打印" @click="printProjects">项目打印</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="overview-card service-card">
        <el-tabs v-model="activeServiceTab" data-service-tabs>
          <el-tab-pane
            v-for="tabItem in serviceCardTabs"
            :key="tabItem.key"
            :label="tabItem.label"
            :name="tabItem.key"
            :data-service-tab="tabItem.label"
          >
            <div v-if="tabItem.key !== 'projectCard'" class="service-grid-shell">
              <el-table
                :data="cardRowsFor(tabItem.key)"
                border
                stripe
                height="430"
                :data-original-grid="tabItem.originalGridId"
              >
                <el-table-column type="index" label="序号" width="58" />
                <el-table-column
                  v-for="columnItem in tabItem.columns"
                  :key="columnItem.key"
                  :prop="columnItem.key"
                  :label="columnItem.label"
                  :min-width="columnItem.width"
                  show-overflow-tooltip
                />
                <template slot="empty">
                  <div class="empty-hint">请选择客户或读取会员卡后查看服务项目</div>
                </template>
              </el-table>
            </div>

            <div v-else class="project-card-layout">
              <el-table
                :data="projectCardRows"
                border
                stripe
                height="430"
                highlight-current-row
                data-original-grid="list5"
              >
                <el-table-column
                  v-for="columnItem in tabItem.columns"
                  :key="columnItem.key"
                  :prop="columnItem.key"
                  :label="columnItem.label"
                  :min-width="columnItem.width"
                  show-overflow-tooltip
                />
                <template slot="empty">
                  <div class="empty-hint">请选择客户后查看项目卡</div>
                </template>
              </el-table>

              <el-table
                :data="projectCardDetailRows"
                border
                stripe
                height="430"
                data-original-grid="list8"
              >
                <el-table-column type="index" label="序号" width="58" />
                <el-table-column
                  v-for="columnItem in tabItem.detailColumns"
                  :key="columnItem.key"
                  :prop="columnItem.key"
                  :label="columnItem.label"
                  :min-width="columnItem.width"
                  show-overflow-tooltip
                />
                <template slot="empty">
                  <div class="empty-hint">选择项目卡后查看卡内服务</div>
                </template>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </template>

    <template v-else>
      <el-card shadow="never" class="overview-card list-query-card" data-list-query>
        <el-form :inline="true" :model="listFilters" size="small" class="list-query-form">
          <el-form-item
            v-for="field in serviceListFilters"
            :key="field.key"
            :label="`${field.label}:`"
            :data-field="field.key"
            :data-control-type="field.type"
          >
            <el-select
              v-if="field.type === 'select'"
              v-model="listFilters[field.key]"
            >
              <el-option
                v-for="option in field.options"
                :key="option"
                :label="option"
                :value="option"
              />
            </el-select>
            <el-input
              v-else
              v-model="listFilters[field.key]"
            />
          </el-form-item>
          <el-form-item class="list-query-actions">
            <el-button type="primary" data-query-action="搜  索" @click="runListSearch">搜  索</el-button>
            <el-button data-query-action="导出" @click="exportList">导出</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never" class="overview-card list-table-card">
        <el-table
          :data="pagedListRows"
          border
          stripe
          height="520"
          data-service-list-grid
          @selection-change="listSelection = $event"
        >
          <el-table-column type="selection" width="45" fixed="left" />
          <el-table-column
            v-for="columnItem in serviceListColumns"
            :key="columnItem.key"
            :prop="columnItem.key"
            :label="columnItem.label"
            :min-width="columnItem.width"
            show-overflow-tooltip
          />
        </el-table>
        <div class="list-summary" data-list-summary>
          <span>完成：{{ completedTotal }}</span>
          <span>剩余{{ remainingTotal }}</span>
        </div>
        <div class="pagination-row">
          <span>{{ pageStart }} - {{ pageEnd }} 共 {{ filteredListRows.length }} 条</span>
          <el-pagination
            background
            layout="prev, pager, next, sizes"
            :current-page.sync="pagination.page"
            :page-size.sync="pagination.size"
            :page-sizes="[15, 100, 500, 1000, 10000]"
            :total="filteredListRows.length"
          />
        </div>
      </el-card>
    </template>

    <el-dialog
      title="选择现有客户"
      :visible.sync="customerDialogVisible"
      width="720px"
      :close-on-click-modal="false"
    >
      <el-form :inline="true" :model="customerFilters" size="small" class="picker-query">
        <el-form-item label="客户名称:">
          <el-input v-model="customerFilters.name" />
        </el-form-item>
        <el-form-item label="手机号码:">
          <el-input v-model="customerFilters.mobile" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchCustomer">搜  索</el-button>
        </el-form-item>
      </el-form>
      <el-table
        :data="filteredCustomerCandidates"
        border
        highlight-current-row
        height="300"
        @current-change="selectedCustomerCandidate = $event"
      >
        <el-table-column prop="name" label="名称" min-width="110" />
        <el-table-column prop="mobile" label="手机号" min-width="125" />
        <el-table-column prop="status" label="客户状态" min-width="100" />
        <el-table-column prop="store" label="分店" min-width="150" />
      </el-table>
      <div slot="footer">
        <el-button @click="customerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCustomer">确 认</el-button>
      </div>
    </el-dialog>

    <el-dialog
      title="读卡"
      :visible.sync="readCardDialogVisible"
      width="430px"
      :close-on-click-modal="false"
    >
      <el-form label-width="72px">
        <el-form-item label="卡号:">
          <el-input v-model="readCardNumber" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="readCardDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReadCard">确 认</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  serviceCardTabs,
  serviceListColumns,
  serviceListFilters
} from '@/config/rehab-service-overview'
import { getRehabModuleData, getRehabOptions } from '@/api/erp-rehab'

const defaultListFilters = () => serviceListFilters.reduce((result, field) => {
  result[field.key] = field.defaultValue || ''
  return result
}, {})

export default {
  name: 'ServiceOverviewQuery',
  data() {
    return {
      serviceCardTabs,
      serviceListFilters,
      serviceListColumns,
      viewMode: 'card',
      activeServiceTab: 'contractInside',
      cardNumber: '',
      selectedCustomerId: null,
      selectedCustomerName: '',
      customerDialogVisible: false,
      readCardDialogVisible: false,
      readCardNumber: '',
      customerFilters: { name: '', mobile: '' },
      selectedCustomerCandidate: null,
      customerCandidates: [],
      cardServiceRows: {
        contractInside: [],
        contractOutside: [],
        extraPurchase: []
      },
      projectCardRowsData: [],
      projectCardDetailRowsData: [],
      listFilters: defaultListFilters(),
      listSelection: [],
      pagination: { page: 1, size: 15 },
      listRows: []
    }
  },
  computed: {
    hasSelectedCustomer() {
      return Boolean(this.selectedCustomerName || this.cardNumber)
    },
    projectCardRows() {
      return this.projectCardRowsData
    },
    projectCardDetailRows() {
      return this.projectCardDetailRowsData
    },
    filteredCustomerCandidates() {
      return this.customerCandidates.filter(item => {
        const nameMatch = !this.customerFilters.name || item.name.includes(this.customerFilters.name)
        const mobileMatch = !this.customerFilters.mobile || item.mobile.includes(this.customerFilters.mobile)
        return nameMatch && mobileMatch
      })
    },
    filteredListRows() {
      return this.listRows
    },
    pagedListRows() {
      const start = (this.pagination.page - 1) * this.pagination.size
      return this.filteredListRows.slice(start, start + this.pagination.size)
    },
    pageStart() {
      return this.filteredListRows.length ? (this.pagination.page - 1) * this.pagination.size + 1 : 0
    },
    pageEnd() {
      return Math.min(this.pagination.page * this.pagination.size, this.filteredListRows.length)
    },
    completedTotal() {
      return this.filteredListRows.reduce((total, row) => total + Number(row.completedCount || 0), 0)
    },
    remainingTotal() {
      return this.filteredListRows.reduce((total, row) => total + Number(row.remainingCount || 0), 0)
    }
  },
  created() {
    this.loadOptions()
    this.runListSearch()
  },
  methods: {
    switchMode(mode) {
      this.viewMode = mode
      this.pagination.page = 1
    },
    cardRowsFor(key) {
      return this.cardServiceRows[key] || []
    },
    async loadOptions() {
      const response = await getRehabOptions()
      this.customerCandidates = response.data.customers || []
    },
    async loadCardServices(params) {
      const response = await getRehabModuleData('service-overview-query', params)
      const rows = response.data.list || []
      this.cardServiceRows = {
        contractInside: rows.filter(item => /套餐内/.test(item.serviceType || '')),
        contractOutside: rows.filter(item => /套餐外/.test(item.serviceType || '')),
        extraPurchase: rows.filter(item => /额外购/.test(item.serviceType || ''))
      }
      const cardRows = rows.filter(item => item.cardNo)
      const seen = new Set()
      this.projectCardRowsData = cardRows.filter(item => {
        if (seen.has(item.cardNo)) return false
        seen.add(item.cardNo)
        return true
      }).map(item => ({
        cardNo: item.cardNo,
        cardName: item.cardName,
        cardType: '项目卡',
        projectType: item.projectCategory,
        customerName: item.customerName,
        price: item.price,
        days: item.remainingDays,
        sourceNo: item.sourceNo
      }))
      this.projectCardDetailRowsData = cardRows.map(item => ({
        serviceName: item.serviceName,
        projectType: item.projectCategory,
        unit: item.unit,
        quantity: item.totalCount,
        remainingQuantity: item.remainingCount,
        endDate: item.endDate
      }))
    },
    openCustomerDialog() {
      this.selectedCustomerCandidate = null
      this.customerDialogVisible = true
    },
    searchCustomer() {
      this.selectedCustomerCandidate = null
    },
    confirmCustomer() {
      if (!this.selectedCustomerCandidate) return this.$message.warning('请选择一位客户')
      this.selectedCustomerId = this.selectedCustomerCandidate.id
      this.selectedCustomerName = this.selectedCustomerCandidate.name
      this.customerDialogVisible = false
      this.loadCardServices({ customerId: this.selectedCustomerId })
    },
    confirmReadCard() {
      if (!this.readCardNumber) return this.$message.warning('请输入卡号')
      this.cardNumber = this.readCardNumber
      this.readCardDialogVisible = false
      this.loadCardServices({ cardNo: this.cardNumber })
    },
    printProjects() {
      window.print()
    },
    async runListSearch() {
      this.pagination.page = 1
      const response = await getRehabModuleData(
        'service-overview-query',
        this.listFilters
      )
      this.listRows = response.data.list || []
    },
    exportList() {
      const headers = this.serviceListColumns.map(item => item.label)
      const body = this.filteredListRows.map(row => this.serviceListColumns.map(item => `"${String(row[item.key] == null ? '' : row[item.key]).replace(/"/g, '""')}"`).join(','))
      const blob = new Blob([`\uFEFF${headers.join(',')}\n${body.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = '服务综合查询.csv'
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${this.filteredListRows.length} 条记录`)
    }
  }
}
</script>

<style lang="scss" scoped>
.service-overview-query {
  margin-top: 16px;
}

.mode-bar,
.customer-query-row,
.pagination-row,
.list-summary {
  display: flex;
  align-items: center;
}

.mode-bar {
  justify-content: space-between;
  gap: 20px;
  padding: 14px 18px;
  border-radius: 11px;
  background: #fff;
}

.mode-bar strong,
.mode-bar span {
  display: block;
}

.mode-bar strong {
  color: #33445b;
  font-size: 15px;
}

.mode-bar span {
  margin-top: 3px;
  color: #8794a5;
  font-size: 12px;
}

.overview-card {
  margin-top: 14px;
  border: 0;
  border-radius: 11px;
}

.customer-query-row {
  flex-wrap: wrap;
  gap: 10px;
}

.query-pair {
  display: flex;
  align-items: center;
  gap: 7px;
}

.query-pair > span {
  flex: 0 0 auto;
  color: #526177;
  font-size: 13px;
}

.query-pair ::v-deep .el-input {
  width: 190px;
}

.customer-pair {
  margin-left: 12px;
}

.customer-query-row em {
  color: #e64343;
  font-size: 12px;
  font-style: normal;
}

.service-card ::v-deep .el-card__body {
  padding-top: 8px;
}

.service-card ::v-deep .el-tabs__item {
  height: 44px;
  line-height: 44px;
}

.service-card ::v-deep .el-tabs__item.is-active {
  color: #8c6a36;
}

.service-card ::v-deep .el-tabs__active-bar {
  background: #b8945a;
}

.service-card ::v-deep .el-table th,
.list-table-card ::v-deep .el-table th {
  color: #43536a;
  background: #f4ecdd;
}

.project-card-layout {
  display: grid;
  grid-template-columns: minmax(660px, 1.2fr) minmax(520px, 1fr);
  gap: 12px;
  overflow-x: auto;
}

.empty-hint {
  padding: 28px 0;
  color: #9aa6b4;
}

.list-query-form {
  margin-bottom: -12px;
}

.list-query-form ::v-deep .el-form-item {
  margin: 0 12px 14px 0;
  vertical-align: bottom;
}

.list-query-form ::v-deep .el-form-item__label {
  display: block;
  float: none;
  padding: 0 0 3px;
  color: #596980;
  font-size: 12px;
  line-height: 18px;
  text-align: left;
}

.list-query-form ::v-deep .el-input,
.list-query-form ::v-deep .el-select {
  width: 155px;
}

.list-query-actions {
  padding-top: 21px;
}

.list-query-actions ::v-deep .el-button span {
  white-space: pre;
}

.list-summary {
  justify-content: flex-end;
  gap: 18px;
  padding: 9px 18px;
  color: #606f82;
  background: #fbf7f9;
}

.pagination-row {
  justify-content: space-between;
  gap: 16px;
  padding-top: 16px;
  color: #8491a2;
  font-size: 12px;
}

.picker-query ::v-deep .el-input {
  width: 180px;
}

@media (max-width: 900px) {
  .mode-bar,
  .pagination-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .customer-pair {
    margin-left: 0;
  }
}
</style>
