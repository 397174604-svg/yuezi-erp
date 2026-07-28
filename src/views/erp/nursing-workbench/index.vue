<template>
  <div class="nursing-workbench">
    <nursing-center v-if="pageConfig.mode === 'care-center'" />

    <template v-else>
      <div class="page-heading">
        <div>
          <div class="title-row">
            <i :class="pageConfig.icon" />
            <h2>{{ title }}</h2>
            <el-tag size="small" type="warning">{{ pageConfig.evidenceLevel }}</el-tag>
          </div>
          <p>{{ pageConfig.description }}</p>
        </div>
        <el-tag effect="plain">完成度：{{ pageConfig.completionLevel }}</el-tag>
      </div>

      <el-alert
        :title="pageConfig.evidenceNote"
        type="warning"
        :closable="false"
        show-icon
        class="evidence-alert"
      />

      <div
        v-if="pageConfig.actions.length && pageConfig.actionPlacement !== 'query-inline'"
        class="business-toolbar"
        :data-page="title"
      >
        <el-button
          v-for="action in pageConfig.actions"
          :key="action.label"
          size="mini"
          class="toolbar-action"
          :data-action="action.label"
          @click="handleBusinessAction(action)"
        >
          <i :class="action.icon" />
          {{ action.label }}
        </el-button>
        <span v-if="pageConfig.toolbarEvidence" class="toolbar-evidence">
          {{ pageConfig.toolbarEvidence }}
        </span>
      </div>

      <el-card shadow="never" class="filter-card">
        <el-form :inline="true" :model="filters" size="small">
          <el-form-item
            v-for="field in pageConfig.filters"
            :key="field.key"
            :label="field.label"
            :data-field="field.key"
            :data-control-type="field.type"
          >
            <el-input
              v-if="field.type === 'input'"
              v-model="filters[field.key]"
              clearable
              :placeholder="field.placeholder || `请输入${field.label}`"
            />
            <el-select
              v-else-if="field.type === 'select'"
              v-model="filters[field.key]"
              clearable
              filterable
              :placeholder="`请选择${field.label}`"
            >
              <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
            </el-select>
            <el-date-picker
              v-else-if="field.type === 'date'"
              v-model="filters[field.key]"
              type="date"
              value-format="yyyy-MM-dd"
              :placeholder="`选择${field.label}`"
            />
            <el-date-picker
              v-else-if="field.type === 'dateRange'"
              v-model="filters[field.key]"
              type="daterange"
              value-format="yyyy-MM-dd"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
            <el-checkbox
              v-else-if="field.type === 'checkbox'"
              v-model="filters[field.key]"
            >
              {{ field.text || field.label }}
            </el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-button
              v-for="action in pageConfig.queryActions"
              :key="action"
              :type="action === '查询' ? 'primary' : 'default'"
              class="query-action"
              :data-query-action="action"
              @click="handleQueryAction(action)"
            >
              {{ action }}
            </el-button>
            <el-button
              v-for="action in inlineBusinessActions"
              :key="action.label"
              class="inline-business-action"
              :data-action="action.label"
              @click="handleBusinessAction(action)"
            >
              <i :class="action.icon" />
              {{ action.label }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <div v-if="pageConfig.mode === 'dashboard'" class="metric-grid">
        <el-card v-for="metric in metrics" :key="metric.label" shadow="hover">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <small>脱敏演示数据</small>
        </el-card>
      </div>

      <el-card shadow="never" class="table-card">
        <div slot="header" class="table-header">
          <span>{{ pageConfig.mode === 'dashboard' ? '今日护理任务（演示）' : `${title}列表（演示）` }}</span>
          <span>共 {{ filteredRows.length }} 条</span>
        </div>
        <el-table
          :data="pagedRows"
          border
          stripe
          size="small"
          highlight-current-row
          row-key="planNo"
          @current-change="handleCurrentChange"
          @selection-change="handleSelectionChange"
        >
          <el-table-column
            v-if="hasMultipleSelection"
            type="selection"
            width="42"
            fixed="left"
          />
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

      <nursing-baby-dialog
        :visible.sync="babyDialogVisible"
        :client="selectedClient"
      />
      <nursing-toolbar-dialog
        :visible.sync="toolbarDialogVisible"
        :page-title="title"
        :action="activeToolbarAction"
        :row="selectedRow || {}"
        @saved="handleToolbarSaved"
      />
      <nursing-legacy-action-dialog
        :visible.sync="planConfirmVisible"
        action="护理计划确认"
        :client="selectedClient"
      />
    </template>
  </div>
</template>

<script>
import Pagination from '@/components/Pagination'
import { getNursingModuleData } from '@/api/erp-nursing'
import { getNursingPageConfig } from '@/config/nursing-pages'
import NursingBabyDialog from './NursingBabyDialog'
import NursingCenter from './NursingCenter'
import NursingLegacyActionDialog from './NursingLegacyActionDialog'
import NursingToolbarDialog from './NursingToolbarDialog'

const stores = ['中心广场旗舰店', '黄河路轻奢店']

export default {
  name: 'NursingWorkbench',
  components: {
    NursingBabyDialog,
    NursingCenter,
    NursingLegacyActionDialog,
    NursingToolbarDialog,
    Pagination
  },
  data() {
    return {
      filters: {},
      rows: [],
      page: 1,
      pageSize: 10,
      loadingResource: '',
      selectedRow: null,
      selectedRows: [],
      activeToolbarAction: '',
      toolbarDialogVisible: false,
      babyDialogVisible: false,
      planConfirmVisible: false
    }
  },
  computed: {
    title() {
      return this.$route.meta && this.$route.meta.title ? this.$route.meta.title : '护理中心'
    },
    pageConfig() {
      return getNursingPageConfig(this.title)
    },
    hasMultipleSelection() {
      return this.pageConfig.actions.some(action => action.selection === 'multiple')
    },
    inlineBusinessActions() {
      return this.pageConfig.actionPlacement === 'query-inline' ? this.pageConfig.actions : []
    },
    selectedClient() {
      const row = this.selectedRow || this.selectedRows[0] || {}
      return {
        customerName: row.customerName || '',
        room: row.room || '',
        store: row.store || '',
        contractNo: row.planNo || '',
        babies: row.babyAlias ? [{ name: row.babyAlias }] : []
      }
    },
    filteredRows() {
      const filterEntries = Object.entries(this.filters).filter(([, value]) => {
        if (Array.isArray(value)) return value.length > 0
        if (typeof value === 'boolean') return value
        if (value === '' || value === null || value === undefined) return false
        const normalized = String(value).replace(/[\s-]/g, '')
        return !['全部', '请选择'].includes(normalized)
      })
      if (!filterEntries.length) return this.rows
      return this.rows.filter(row => filterEntries.every(([key, value]) => {
        if (Array.isArray(value)) {
          const target = String(row[key] || row.serviceDate || row.planDate || '')
          return (!value[0] || target >= value[0]) && (!value[1] || target <= value[1])
        }
        return String(row[key] || '').includes(String(value))
      }))
    },
    pagedRows() {
      const start = (this.page - 1) * this.pageSize
      return this.filteredRows.slice(start, start + this.pageSize)
    },
    metrics() {
      return [
        { label: '今日任务', value: this.rows.length },
        { label: '待执行', value: this.rows.filter(item => item.status === '待执行').length },
        { label: '执行中', value: this.rows.filter(item => item.status === '执行中').length },
        { label: '已完成', value: this.rows.filter(item => item.status === '已完成').length }
      ]
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
      this.filters = { ...(this.pageConfig.defaults || {}) }
      this.page = 1
      this.selectedRow = null
      this.selectedRows = []
      this.rows = this.createDemoRows()
      this.loadModuleData()
    },
    async loadModuleData() {
      const resource = this.pageConfig.key
      this.loadingResource = resource
      try {
        const response = await getNursingModuleData(resource, this.filters)
        if (this.loadingResource === resource && response.data && response.data.list && response.data.list.length) {
          this.rows = response.data.list
        }
      } catch (error) {
        // The independent mock is wired by the root integration step.
      }
    },
    handleQueryAction(action) {
      if (action === '导出') {
        this.exportCsv()
        return
      }
      if (action === '打印') {
        this.$message.success('已生成打印预览（脱敏演示）')
        return
      }
      this.page = 1
    },
    handleCurrentChange(row) {
      this.selectedRow = row || null
    },
    handleSelectionChange(rows) {
      this.selectedRows = rows
      if (rows.length) this.selectedRow = rows[0]
    },
    requireSelection(action) {
      if (action.selection === 'single' && !this.selectedRow) {
        this.$message.warning('请选中一行数据！')
        return false
      }
      if (action.selection === 'multiple' && !this.selectedRows.length) {
        this.$message.warning('请选中一行数据！')
        return false
      }
      return true
    },
    handleBusinessAction(action) {
      if (!this.requireSelection(action)) return

      if (action.kind === 'delete') {
        this.$confirm('确定删除选中的记录吗？本操作仅影响脱敏演示数据。', '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          const targets = this.selectedRows.length ? this.selectedRows : [this.selectedRow]
          this.rows = this.rows.filter(row => !targets.includes(row))
          this.selectedRow = null
          this.selectedRows = []
          this.$message.success('删除成功（脱敏演示）')
        }).catch(() => {})
        return
      }
      if (action.kind === 'export') {
        this.exportCsv()
        return
      }
      if (action.kind === 'print') {
        this.$message.success('已生成打印预览（脱敏演示）')
        return
      }
      if (this.title === '护理计划' && action.label === '新增宝宝') {
        this.babyDialogVisible = true
        return
      }
      if (this.title === '护理计划' && action.label === '确认完成') {
        this.planConfirmVisible = true
        return
      }

      this.activeToolbarAction = action.label
      this.toolbarDialogVisible = true
    },
    handleToolbarSaved({ action }) {
      this.$message.success(`${action}已保存（脱敏演示）`)
    },
    createDemoRows() {
      return Array.from({ length: 14 }, (_, index) => this.createDemoRow(index))
    },
    createDemoRow(index) {
      const referenceDate = new Date()
      referenceDate.setDate(referenceDate.getDate() - Math.min(index, 8))
      const year = referenceDate.getFullYear()
      const month = String(referenceDate.getMonth() + 1).padStart(2, '0')
      const day = String(referenceDate.getDate()).padStart(2, '0')
      const dateValue = `${year}-${month}-${day}`
      const status = ['待执行', '执行中', '已完成', '异常上报'][index % 4]
      const base = {
        planNo: `NP-DEMO-${String(index + 1).padStart(4, '0')}`,
        recordNo: `NR-DEMO-${String(index + 1).padStart(4, '0')}`,
        assessmentNo: `NA-DEMO-${String(index + 1).padStart(4, '0')}`,
        roundNo: `ND-DEMO-${String(index + 1).padStart(4, '0')}`,
        handoverNo: `NH-DEMO-${String(index + 1).padStart(4, '0')}`,
        babyCode: `BABY-DEMO-${String(index + 1).padStart(3, '0')}`,
        babyAlias: `宝宝${String.fromCharCode(65 + index % 6)}`,
        customerName: `演示客户${String.fromCharCode(65 + index % 6)}`,
        customerStatus: '- 已入住 -',
        room: `${3 + index % 4}0${1 + index % 8}`,
        floor: `${3 + index % 4}楼`,
        store: stores[index % stores.length],
        scheduleType: '护理排班',
        department: '护理部',
        planDate: dateValue,
        serviceDate: dateValue,
        assessmentDate: dateValue,
        roundDate: dateValue,
        handoverDate: dateValue,
        shiftDate: dateValue,
        birthDate: `2026-06-${String((index % 9) + 10).padStart(2, '0')}`,
        birthTime: `${String(8 + index % 10).padStart(2, '0')}:20`,
        planTime: `${String(8 + index % 10).padStart(2, '0')}:30`,
        serviceTime: `${String(8 + index % 10).padStart(2, '0')}:30`,
        recordedAt: `${dateValue} 10:30`,
        createdAt: `${dateValue} 09:00`,
        checkInDate: dateValue,
        lastServiceAt: `${dateValue} 16:20`,
        lastRecordedAt: `${dateValue} 18:10`,
        target: index % 2 ? '宝宝' : '妈妈',
        projectName: ['宝宝沐浴', '妈妈护理', '宝宝抚触', '健康观察'][index % 4],
        nurseName: ['演示护士A', '演示护士B', '演示护士C'][index % 3],
        employeeName: ['演示护士A', '演示护士B', '演示护士C'][index % 3],
        primaryNurse: ['演示护士A', '演示护士B', '演示护士C'][index % 3],
        nursingDirector: '演示护理总监',
        nursingManager: '演示护理主任',
        housekeeper: '演示生活管家',
        gyneDoctor: '演示妇科医师',
        pediatricDoctor: '演示儿科医师',
        rehabNurse: '演示产康师',
        headNurse: '演示责任护士',
        feedingSpecialist: '演示喂养师',
        nutritionist: '演示营养师',
        matronName: index % 2 ? '演示月嫂A' : '',
        planSheet: '查看',
        assessor: ['演示护士A', '演示护士B', '演示营养师A'][index % 3],
        rounder: ['演示护士A', '演示医生A', '演示营养师A'][index % 3],
        doctorName: '演示医生A',
        recorder: '演示记录员',
        creator: '演示制单人',
        confirmer: '演示确认人',
        handoverStaff: '演示交接员',
        status,
        confirmStatus: index % 2 ? '已确认' : '待确认',
        archiveStatus: index % 4 ? '有效' : '待完善',
        riskLevel: ['低', '中', '高'][index % 3],
        resultStatus: index % 3 ? '正常' : '需调整',
        exceptionStatus: index % 3 ? '正常' : '异常',
        serviceType: ['套餐内', '套餐外', '额外购'][index % 3],
        customerType: index % 2 ? '店内客户' : '散客客户',
        auditStatus: index % 2 ? '已审核' : '未审核',
        receiveStatus: index % 3 ? '接收' : '送还',
        homeCustomer: index % 5 === 0,
        customerConfirmation: index % 2 ? '已确认' : '待确认',
        gender: index % 2 ? '女' : '男',
        gestationalWeek: `${38 + index % 3}周`,
        birthWeight: `${3 + (index % 4) * 0.1}kg`,
        deliveryMode: index % 2 ? '顺产分娩' : '剖宫产分娩',
        assessmentType: index % 2 ? '宝宝健康评估' : '妈妈健康评估',
        summary: '脱敏演示评估结论，待原系统字段核验。',
        followUp: '脱敏演示跟进建议。',
        dietType: '演示膳食方案',
        tabooSummary: index % 3 ? '无演示禁忌' : '演示禁忌项',
        nutritionGoal: '均衡营养（演示）',
        roundType: '日常查房',
        templateName: '演示查房模板',
        result: '脱敏演示执行结果。',
        observation: '脱敏演示观察记录。',
        advice: '脱敏演示处理建议。',
        mealPlan: '演示月子餐单',
        finding: '脱敏演示查房发现。',
        adjustment: index % 3 ? '无需调整' : '待营养师确认',
        projectCount: 6 + index % 5,
        frequency: '每日1次',
        consumables: '演示耗材×1',
        vitalSummary: '体征演示摘要',
        careResult: '护理完成（演示）',
        feedingSummary: '喂养演示摘要',
        sleepSummary: '睡眠演示摘要',
        excretionSummary: '排便演示摘要',
        plannedCount: 12,
        completedCount: 8 + index % 5,
        exceptionCount: index % 3,
        completionRate: `${80 + index % 5 * 4}%`,
        careCount: 10 + index,
        feedingCount: 6 + index % 5,
        bathCount: 2 + index % 3,
        lastWeight: `${3.2 + (index % 5) * 0.1}kg`,
        shiftName: ['白班', '夜班', '休息'][index % 3],
        startTime: index % 3 === 1 ? '20:00' : '08:00',
        endTime: index % 3 === 1 ? '08:00' : '20:00',
        area: `${3 + index % 4}楼`,
        roomRange: `${3 + index % 4}01-${3 + index % 4}08`,
        monday: '白班 08:00-20:00',
        tuesday: '休息',
        wednesday: '夜班 20:00-08:00',
        thursday: '休息',
        friday: '白班 08:00-20:00',
        saturday: '休息',
        sunday: '夜班 20:00-08:00',
        totalShifts: 4,
        itemCount: 8,
        plannedQuantity: 12,
        actualQuantity: index % 4 ? 12 : 11,
        remark: '仅用于前端结构演示，不含真实护理数据。'
      }
      return base
    },
    tagType(value) {
      const success = ['已完成', '已确认', '有效', '正常']
      const danger = ['异常上报', '高', '有差异', '需调整']
      const warning = ['待执行', '执行中', '待确认', '待完善', '中']
      if (success.includes(value)) return 'success'
      if (danger.includes(value)) return 'danger'
      if (warning.includes(value)) return 'warning'
      return 'info'
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
.nursing-workbench {
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
      color: #8f7cf6;
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
.business-toolbar,
.filter-card,
.metric-grid {
  margin-bottom: 14px;
}

.business-toolbar {
  display: flex;
  align-items: center;
  min-height: 46px;
  padding: 0 12px;
  overflow-x: auto;
  border: 1px solid #dfe4e9;
  border-radius: 2px;
  background: #fff;

  .toolbar-action {
    flex: 0 0 auto;
    margin-left: 0;
    margin-right: 8px;
    border-color: #d8dde5;
    color: #4f5d6b;
    background: #fff;

    i {
      margin-right: 4px;
      color: #6f8eac;
    }
  }

  .toolbar-evidence {
    flex: 0 0 auto;
    margin-left: auto;
    color: #8a94a2;
    font-size: 12px;
  }
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

@media (max-width: 900px) {
  .page-heading {
    display: block;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
