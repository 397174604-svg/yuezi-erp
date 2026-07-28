<template>
  <div class="diet-workbench">
    <div class="page-heading">
      <div>
        <div class="title-row">
          <i :class="pageConfig.icon" />
          <h2>{{ title }}</h2>
          <el-tag size="small" type="success">{{ pageConfig.evidenceLevel }}</el-tag>
        </div>
        <p>{{ pageConfig.description }}</p>
      </div>
      <el-tag effect="plain">完成度：{{ pageConfig.completionLevel }}</el-tag>
    </div>

    <audited-surface-panel
      :config="pageConfig"
      show-action-icons
      @business-action="handleBusinessAction"
      @query-action="handleQueryAction"
    />

    <div v-if="pageConfig.mode === 'summary'" class="metric-grid">
      <el-card v-for="metric in metrics" :key="metric.label" shadow="hover">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>来自 MySQL 业务数据</small>
      </el-card>
    </div>

    <el-card v-if="pageConfig.mode === 'meal-calendar'" shadow="never" class="calendar-card">
      <div slot="header" class="table-header">
        <span>餐次排餐视图</span>
        <span>当前显示 {{ calendarRows.length }} 个餐次</span>
      </div>
      <div class="meal-board">
        <section v-for="item in calendarRows" :key="item.mealType" class="meal-column">
          <header>
            <span>{{ item.mealType }}</span>
            <el-tag size="mini" :type="tagType(item.status)">{{ item.status }}</el-tag>
          </header>
          <div class="meal-time">{{ item.deliveryTime || '待设置配送时间' }}</div>
          <div class="dish-name">{{ item.dishName }}</div>
          <div class="meal-meta">{{ item.room }} · {{ item.customerName }}</div>
          <div class="meal-note">禁忌：{{ item.taboo }}</div>
        </section>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <div slot="header" class="table-header">
        <span>{{ title }}列表</span>
        <span>共 {{ filteredRows.length }} 条</span>
      </div>
      <el-table
        :data="pagedRows"
        border
        stripe
        size="small"
        highlight-current-row
        @current-change="selectedRow = $event"
      >
        <el-table-column type="index" label="序号" width="55" fixed="left" />
        <el-table-column
          v-for="column in pageConfig.columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :width="column.width"
          :min-width="column.width ? undefined : 120"
          show-overflow-tooltip
        >
          <template slot-scope="{ row }">
            <el-tag v-if="column.tag" :type="tagType(row[column.key])" size="mini">
              {{ row[column.key] }}
            </el-tag>
            <span v-else-if="column.money">¥ {{ formatAmount(row[column.key]) }}</span>
            <span v-else>{{ row[column.key] }}</span>
          </template>
        </el-table-column>
      </el-table>
      <pagination
        v-show="filteredRows.length > pageSize"
        :total="filteredRows.length"
        :page.sync="page"
        :limit.sync="pageSize"
        @pagination="noop"
      />
    </el-card>

    <el-dialog
      :title="dialogTitle"
      :visible.sync="dialogVisible"
      width="760px"
      append-to-body
      @closed="resetDialog"
    >
      <el-alert
        title="当前窗口用于字段与交互演示，保存不会写入真实业务系统。"
        type="info"
        :closable="false"
        show-icon
        class="dialog-alert"
      />
      <el-form ref="recordForm" :model="recordForm" :rules="rules" label-width="110px">
        <el-row :gutter="18">
          <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
            <el-form-item :label="field.label" :prop="field.key">
              <el-input
                v-if="field.type === 'input'"
                v-model="recordForm[field.key]"
                :placeholder="`请输入${field.label}`"
              />
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="recordForm[field.key]"
                :min="0"
                :precision="field.key.toLowerCase().includes('amount') || field.key.toLowerCase().includes('price') ? 2 : 0"
                controls-position="right"
                class="full-control"
              />
              <el-select
                v-else-if="field.type === 'select'"
                v-model="recordForm[field.key]"
                filterable
                clearable
                class="full-control"
                :placeholder="`请选择${field.label}`"
              >
                <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
              </el-select>
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="recordForm[field.key]"
                type="date"
                value-format="yyyy-MM-dd"
                class="full-control"
                :placeholder="`请选择${field.label}`"
              />
              <el-switch v-else-if="field.type === 'switch'" v-model="recordForm[field.key]" />
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="recordForm[field.key]"
                type="textarea"
                :rows="3"
                :placeholder="`请输入${field.label}`"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord">保存（演示）</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import Pagination from '@/components/Pagination'
import { getDietModuleData, performDietModuleAction, saveDietModuleRecord } from '@/api/erp-diet'
import { getDietPageConfig } from '@/config/diet-pages'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'

const stores = ['中心广场旗舰店', '黄河路轻奢店']
const mealTypes = ['早餐', '上午加餐', '午餐', '下午加餐', '晚餐', '晚间加餐']
const mealTimes = ['07:30', '10:00', '12:00', '15:30', '18:00', '20:30']

export default {
  name: 'DietWorkbench',
  components: { AuditedSurfacePanel, Pagination },
  data() {
    return {
      filters: {},
      rows: [],
      page: 1,
      pageSize: 10,
      selectedRow: null,
      dialogVisible: false,
      dialogTitle: '',
      dialogFields: [],
      recordForm: {},
      saving: false
    }
  },
  computed: {
    title() {
      return this.$route.meta && this.$route.meta.title ? this.$route.meta.title : '客户餐单'
    },
    pageConfig() {
      return getDietPageConfig(this.title)
    },
    filteredRows() {
      const entries = Object.entries(this.filters).filter(([, value]) => {
        if (Array.isArray(value)) return value.length > 0
        return value !== '' && value !== null && value !== undefined
      })
      if (!entries.length) return this.rows
      return this.rows.filter(row => entries.every(([key, value]) => {
        if (Array.isArray(value)) {
          const target = String(
            row[key] || row.mealDate || row.deliveryDate || row.supplyDate ||
            row.purchaseDate || row.saleDate || row.transactionAt || ''
          ).slice(0, 10)
          return (!value[0] || target >= value[0]) && (!value[1] || target <= value[1])
        }
        return String(row[key] || '').includes(String(value))
      }))
    },
    pagedRows() {
      const start = (this.page - 1) * this.pageSize
      return this.filteredRows.slice(start, start + this.pageSize)
    },
    calendarRows() {
      const byMeal = []
      mealTypes.forEach(type => {
        const row = this.filteredRows.find(item => item.mealType === type)
        if (row) byMeal.push(row)
      })
      return byMeal
    },
    metrics() {
      const quantity = this.filteredRows.reduce((sum, row) => (
        sum + Number(row.plannedCount || row.taskCount || row.plannedQuantity || 0)
      ), 0)
      const completed = this.filteredRows.reduce((sum, row) => (
        sum + Number(row.signedCount || row.signedQuantity || row.deliveredCount || 0)
      ), 0)
      const exceptions = this.filteredRows.reduce((sum, row) => (
        sum + Number(row.returnedCount || row.returnedQuantity || row.timeoutCount || 0)
      ), 0)
      return [
        { label: '统计记录', value: this.filteredRows.length },
        { label: '计划数量', value: quantity },
        { label: '完成数量', value: completed },
        { label: '异常/退回', value: exceptions }
      ]
    },
    rules() {
      return this.dialogFields.reduce((rules, field) => {
        if (field.required) {
          rules[field.key] = [{ required: true, message: `请填写${field.label}`, trigger: field.type === 'select' ? 'change' : 'blur' }]
        }
        return rules
      }, {})
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
    async initializePage() {
      this.filters = {}
      this.page = 1
      this.selectedRow = null
      try {
        const response = await getDietModuleData(this.pageConfig.key, { page: 1, pageSize: this.pageSize })
        this.rows = response.data.list || []
      } catch (error) {
        this.rows = []
      }
    },
    createDemoRow(index) {
      const day = String((index % 9) + 14).padStart(2, '0')
      const dateValue = `2026-07-${day}`
      const mealType = mealTypes[index % mealTypes.length]
      const status = ['待排餐', '已排餐', '备餐中', '配送中', '已签收', '已退餐'][index % 6]
      const amount = 36 + index * 4
      return {
        id: `DIET-DEMO-${String(index + 1).padStart(4, '0')}`,
        store: stores[index % stores.length],
        customerName: `演示客户${String.fromCharCode(65 + index % 6)}`,
        customerType: ['入住客户', '散客', '陪护人员', '员工'][index % 4],
        mobile: `138****${String(1200 + index).slice(-4)}`,
        room: `${2 + index % 4}0${1 + index % 8}`,
        mealDate: dateValue,
        statDate: dateValue,
        deliveryDate: dateValue,
        supplyDate: dateValue,
        purchaseDate: dateValue,
        saleDate: dateValue,
        transactionAt: `${dateValue} ${mealTimes[index % mealTimes.length]}`,
        mealType,
        dishCode: `DISH-${String(index + 1).padStart(4, '0')}`,
        dishName: ['山药小米粥', '银耳红枣羹', '莲藕排骨汤', '清蒸时蔬', '菌菇鸡汤', '时令水果'][index % 6],
        dishCategory: ['主食', '汤羹', '荤菜', '素菜', '点心', '水果'][index % 6],
        ingredients: '脱敏演示食材组合',
        nutrition: '均衡营养（演示）',
        tabooTag: index % 4 ? '无' : '演示禁忌',
        taboo: index % 4 ? '无演示禁忌' : '演示禁忌项',
        dietitian: '演示营养师A',
        unit: '份',
        quantity: 1 + index % 3,
        standardPrice: amount,
        enabled: index % 5 ? '启用' : '停用',
        creator: '演示录入人',
        createdAt: `${dateValue} 09:00`,
        packageCode: `DP-${String(index + 1).padStart(4, '0')}`,
        packageName: ['标准月子膳食套餐', '调理膳食套餐', '陪护餐套餐'][index % 3],
        cycleDays: [28, 42, 7][index % 3],
        mealStandard: '每日三餐三加餐',
        packageAmount: 1680 + index * 50,
        effectiveDate: '2026-07-01',
        expiryDate: '2026-12-31',
        status,
        deliveryTime: mealTimes[index % mealTimes.length],
        remark: '仅用于前端字段与交互演示。',
        plannedCount: 35 + index,
        preparedCount: 32 + index,
        deliveredCount: 30 + index,
        signedCount: 28 + index,
        returnedCount: index % 3,
        completionRate: `${92 + index % 6}%`,
        customerCount: 25 + index,
        deliveryStaff: `演示配送员${String.fromCharCode(65 + index % 3)}`,
        taskCount: 30 + index,
        timeoutCount: index % 2,
        firstDeliveryAt: `${dateValue} 07:20`,
        lastSignedAt: `${dateValue} 18:45`,
        soupCode: `SOUP-${String(index + 1).padStart(4, '0')}`,
        soupName: ['红枣银耳汤', '莲藕排骨汤', '菌菇鸡汤'][index % 3],
        supplyType: ['常规营养汤', '产后调理汤', '特殊医嘱汤'][index % 3],
        supplyPeriod: ['上午', '午间', '晚间'][index % 3],
        applicableCustomer: '入住客户（演示）',
        contraindication: index % 3 ? '无' : '待营养师确认',
        plannedQuantity: 20 + index,
        preparedQuantity: 19 + index,
        deliveredQuantity: 18 + index,
        signedQuantity: 17 + index,
        returnedQuantity: index % 2,
        supplyNo: `GS-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        amount,
        paymentMethod: ['合同套餐', '餐卡', '微信', '挂账'][index % 4],
        supplyStatus: ['待供应', '已供应', '已签收', '已取消'][index % 4],
        signedAt: index % 4 === 2 ? `${dateValue} 12:35` : '—',
        purchaseNo: `CG-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        ingredientName: ['东北小米', '新鲜莲藕', '排骨', '时令蔬菜'][index % 4],
        specification: ['25kg/袋', '5kg/筐', '10kg/箱', '15kg/筐'][index % 4],
        purchaseQuantity: 10 + index,
        unitPrice: 12 + index,
        supplier: `演示供应商${String.fromCharCode(65 + index % 3)}`,
        auditStatus: index % 3 ? '已审核' : '待审核',
        arrivalStatus: ['待到货', '部分到货', '已到货'][index % 3],
        saleNo: `XS-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        saleType: ['膳食套餐', '单点餐品', '营养汤', '客餐'][index % 4],
        itemName: ['标准月子膳食套餐', '山药小米粥', '红枣银耳汤', '陪护午餐'][index % 4],
        saleAmount: amount * 3,
        receivedAmount: index % 3 ? amount * 3 : amount,
        paymentStatus: ['未收款', '部分收款', '已收款', '已退款'][index % 4],
        salesperson: '演示业务员',
        orderNo: `DC-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        deliveryAddress: `${2 + index % 4}楼演示房间`,
        orderStatus: ['待确认', '待备餐', '备餐中', '配送中', '已签收', '已退餐'][index % 6],
        orderedAt: `${dateValue} 08:30`,
        cardNo: `MEAL-${String(80001 + index)}`,
        openedAt: dateValue,
        totalRecharge: 2000 + index * 100,
        totalConsume: 320 + index * 20,
        balance: 1680 + index * 80,
        cardStatus: ['正常', '正常', '挂失', '已退卡'][index % 4],
        operator: '演示操作员',
        lastOperatedAt: `${dateValue} 15:20`,
        transactionNo: `LS-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        transactionType: ['开卡', '充值', '消费', '退款', '退卡'][index % 5],
        beforeBalance: 1800 + index * 80,
        afterBalance: 1800 + index * 80 + (index % 2 ? amount : -amount),
        relatedDocumentNo: `REF-DEMO-${String(index + 1).padStart(4, '0')}`
      }
    },
    handleQueryAction(action) {
      if (/查询|搜索/.test(String(action).replace(/\s+/g, ''))) {
        this.page = 1
        this.$message.success(`已按当前条件筛选，共 ${this.filteredRows.length} 条演示记录`)
      } else if (action === '导出') {
        this.exportCsv()
      } else if (action === '打印') {
        window.print()
      }
    },
    handleBusinessAction(action) {
      if (action === '导出') return this.exportCsv()
      if (action === '打印') return window.print()
      if (['添加', '开卡'].includes(action)) return this.openRecordDialog(action)
      if (action === '编辑') {
        if (!this.requireSelection()) return
        return this.openRecordDialog(action, this.selectedRow)
      }
      if (['删除', '启用', '停用', '提交', '审核', '反审核', '确认供应', '确认签收', '确认下单', '开始备餐', '开始配送', '退餐', '挂失', '恢复', '退卡', '收款', '退款'].includes(action)) {
        if (!this.requireSelection()) return
      }
      this.$confirm(`确认对当前演示记录执行“${action}”？该操作不会写入真实 ERP。`, '演示操作', {
        type: 'warning'
      }).then(async() => {
        await performDietModuleAction(this.pageConfig.key, action, { id: this.selectedRow && this.selectedRow.id })
        this.applyLocalAction(action)
        this.$message.success(`${action}操作已在本地演示完成`)
      }).catch(() => {})
    },
    requireSelection() {
      if (this.selectedRow) return true
      this.$message.warning('请先选择一条演示记录')
      return false
    },
    openRecordDialog(action, row = {}) {
      const fields = this.pageConfig.formFields || []
      if (!fields.length) {
        this.$message.warning('该动作表单尚待原系统二次核验')
        return
      }
      this.dialogTitle = `${action}${this.title}`
      this.dialogFields = fields
      this.recordForm = fields.reduce((form, field) => {
        const value = row[field.key]
        form[field.key] = value !== undefined ? value : (field.type === 'number' ? 0 : field.type === 'switch' ? true : '')
        return form
      }, {})
      this.dialogVisible = true
    },
    saveRecord() {
      this.$refs.recordForm.validate(async valid => {
        if (!valid) return
        this.saving = true
        try {
          await saveDietModuleRecord(this.pageConfig.key, this.recordForm)
          const demoRow = { ...this.createDemoRow(this.rows.length), ...this.recordForm, id: `DIET-LOCAL-${Date.now()}` }
          if (this.dialogTitle.startsWith('编辑') && this.selectedRow) {
            Object.assign(this.selectedRow, this.recordForm)
          } else {
            this.rows.unshift(demoRow)
          }
          this.dialogVisible = false
          this.$message.success('已保存到本地演示数据，未写入真实 ERP')
        } finally {
          this.saving = false
        }
      })
    },
    applyLocalAction(action) {
      if (!this.selectedRow) return
      const actionMapping = {
        启用: ['enabled', '启用'],
        停用: ['enabled', '停用'],
        提交: ['auditStatus', '待审核'],
        审核: ['auditStatus', '已审核'],
        反审核: ['auditStatus', '待审核'],
        确认供应: ['supplyStatus', '已供应'],
        确认签收: ['orderStatus', '已签收'],
        确认下单: ['orderStatus', '待备餐'],
        开始备餐: ['orderStatus', '备餐中'],
        开始配送: ['orderStatus', '配送中'],
        退餐: ['orderStatus', '已退餐'],
        挂失: ['cardStatus', '挂失'],
        恢复: ['cardStatus', '正常'],
        退卡: ['cardStatus', '已退卡'],
        收款: ['paymentStatus', '已收款'],
        退款: ['paymentStatus', '已退款']
      }
      if (action === '删除') {
        this.rows = this.rows.filter(row => row.id !== this.selectedRow.id)
        this.selectedRow = null
      } else if (actionMapping[action]) {
        this.$set(this.selectedRow, actionMapping[action][0], actionMapping[action][1])
      }
    },
    resetDialog() {
      this.dialogFields = []
      this.recordForm = {}
      this.$nextTick(() => {
        if (this.$refs.recordForm) this.$refs.recordForm.clearValidate()
      })
    },
    tagType(value) {
      if (['启用', '已审核', '已到货', '已供应', '已签收', '正常', '已收款', '充值'].includes(value)) return 'success'
      if (['停用', '已取消', '已退餐', '已退卡', '已退款', '退卡'].includes(value)) return 'danger'
      if (['待排餐', '备餐中', '配送中', '待审核', '部分到货', '挂失', '部分收款'].includes(value)) return 'warning'
      return 'info'
    },
    formatAmount(value) {
      const amount = Number(value || 0)
      return amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    exportCsv() {
      const columns = this.pageConfig.columns
      const lines = [
        columns.map(item => item.label).join(','),
        ...this.filteredRows.map(row => columns.map(item => `"${String(row[item.key] || '').replace(/"/g, '""')}"`).join(','))
      ]
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.title}-脱敏演示.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    },
    noop() {}
  }
}
</script>

<style lang="scss" scoped>
.diet-workbench {
  min-height: calc(100vh - 84px);
  padding: 20px;
  background: #f5f7fa;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;

  .title-row {
    display: flex;
    align-items: center;
    gap: 10px;

    i {
      color: #58b66f;
      font-size: 24px;
    }

    h2 {
      margin: 0;
      color: #303133;
      font-size: 22px;
    }
  }

  p {
    margin: 8px 0 0 34px;
    color: #7a8495;
  }
}

.evidence-alert,
.action-card,
.filter-card,
.metric-grid,
.calendar-card {
  margin-bottom: 14px;
}

.action-card ::v-deep .el-card__body {
  padding: 12px 16px;
}

.demo-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.filter-card ::v-deep .el-card__body {
  padding-bottom: 4px;
}

.filter-card ::v-deep .el-input,
.filter-card ::v-deep .el-select {
  width: 180px;
}

.filter-card ::v-deep .el-date-editor--daterange {
  width: 260px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;

  .el-card ::v-deep .el-card__body {
    display: grid;
    gap: 7px;
  }

  span,
  small {
    color: #8b94a4;
  }

  strong {
    color: #303133;
    font-size: 30px;
  }
}

.table-header {
  display: flex;
  justify-content: space-between;
  color: #606266;
}

.meal-board {
  display: grid;
  grid-template-columns: repeat(6, minmax(160px, 1fr));
  gap: 12px;
  overflow-x: auto;
}

.meal-column {
  min-width: 160px;
  padding: 14px;
  border: 1px solid #e6efe8;
  border-radius: 8px;
  background: #f7fcf8;

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    color: #2f7041;
    font-weight: 600;
  }
}

.meal-time,
.meal-meta,
.meal-note {
  color: #8a949f;
  font-size: 12px;
}

.dish-name {
  margin: 8px 0;
  color: #303133;
  font-size: 15px;
  font-weight: 600;
}

.meal-note {
  margin-top: 8px;
}

.dialog-alert {
  margin-bottom: 18px;
}

.full-control {
  width: 100%;
}

@media (max-width: 1000px) {
  .page-heading {
    display: block;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
