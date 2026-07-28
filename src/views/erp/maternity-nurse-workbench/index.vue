<template>
  <div
    class="maternity-nurse-workbench"
    data-maternity-workbench
    :data-page-title="pageTitle"
  >
    <audited-surface-panel
      :config="config"
      plain
      show-action-icons
      @business-action="handleBusinessAction"
      @query-action="handleQueryAction"
    />

    <el-alert
      v-if="config.hint"
      :title="config.hint"
      type="success"
      :closable="false"
      show-icon
      class="page-hint"
    />

    <el-card shadow="never" class="grid-card" data-maternity-grid>
      <div v-if="isSchedule" class="schedule-meta">
        <div class="schedule-legend">
          <span
            v-for="item in config.scheduleLegend"
            :key="item.label"
            class="legend-item"
          >
            <i :style="{ backgroundColor: item.color }" />
            {{ item.label }}
          </span>
        </div>
        <div class="date-axis">
          <span v-for="day in scheduleDays" :key="day.key">
            {{ day.label }}
          </span>
        </div>
      </div>

      <el-table
        ref="mainTable"
        :data="tableRows"
        border
        stripe
        height="500"
        row-key="_id"
        highlight-current-row
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="46" fixed="left" />
        <el-table-column
          v-for="item in config.columns"
          :key="item.key"
          :prop="item.key"
          :label="item.label"
          :width="item.width"
          :fixed="item.fixed"
          :data-grid-column="item.label"
          show-overflow-tooltip
        >
          <template slot-scope="{ row }">
            <div v-if="isSchedule && item.label === '档期情况'" class="schedule-track">
              <span
                v-for="(day, dayIndex) in scheduleDays"
                :key="day.key"
                class="schedule-cell"
                :style="scheduleCellStyle(row, dayIndex)"
                :title="scheduleCellTitle(row, dayIndex)"
              />
            </div>
            <div v-else-if="cellActionLabels(item.label).length" class="row-actions">
              <el-button
                v-for="action in cellActionLabels(item.label)"
                :key="action"
                type="text"
                size="mini"
                @click.stop="runRowAction(action, row)"
              >{{ action }}</el-button>
            </div>
            <div v-else-if="item.label === '操作'" class="row-actions">
              <el-button
                v-for="action in config.rowActions"
                :key="action"
                type="text"
                size="mini"
                @click.stop="runRowAction(action, row)"
              >{{ action }}</el-button>
            </div>
            <el-button
              v-else-if="item.label === '附件' && row[item.key] !== '--'"
              type="text"
              size="mini"
              @click.stop="runRowAction('查看附件', row)"
            >{{ row[item.key] }}</el-button>
            <span v-else>{{ row[item.key] }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span />
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :total="tableRows.length"
          :page-size="15"
          :page-sizes="[15, 50, 100, 200]"
        />
      </div>
    </el-card>

    <el-dialog
      :title="activeFormTitle"
      :visible.sync="formDialogVisible"
      width="88%"
      top="4vh"
      append-to-body
      data-maternity-form-dialog
    >
      <div class="form-scroll">
        <el-card
          v-for="section in activeSections"
          :key="section.title"
          shadow="never"
          class="form-section"
        >
          <div slot="header" class="section-title">{{ section.title }}</div>
          <el-form :model="formModel" label-width="150px" size="small">
            <el-row :gutter="16">
              <el-col
                v-for="item in section.fields"
                :key="item.key"
                :xs="24"
                :sm="12"
                :lg="item.type === 'textarea' || item.type === 'checkbox-group' ? 24 : 8"
              >
                <el-form-item
                  :label="item.label"
                  :data-form-field="item.label"
                  :data-control-type="item.type"
                >
                  <el-select
                    v-if="item.type === 'select'"
                    v-model="formModel[item.key]"
                    :disabled="item.disabled"
                  >
                    <el-option
                      v-for="option in item.options"
                      :key="option"
                      :label="option"
                      :value="option"
                    />
                  </el-select>
                  <el-date-picker
                    v-else-if="item.type === 'date'"
                    v-model="formModel[item.key]"
                    type="date"
                    value-format="yyyy-MM-dd"
                    :readonly="item.readonly"
                    :disabled="item.disabled"
                  />
                  <el-input
                    v-else-if="item.type === 'textarea'"
                    v-model="formModel[item.key]"
                    type="textarea"
                    :rows="3"
                    :readonly="item.readonly"
                  />
                  <el-checkbox-group
                    v-else-if="item.type === 'checkbox-group'"
                    v-model="formModel[item.key]"
                  >
                    <el-checkbox
                      v-for="option in item.options"
                      :key="option"
                      :label="option"
                    />
                  </el-checkbox-group>
                  <el-radio-group
                    v-else-if="item.type === 'radio-group'"
                    v-model="formModel[item.key]"
                  >
                    <el-radio
                      v-for="option in item.options"
                      :key="option"
                      :label="option"
                    />
                  </el-radio-group>
                  <el-checkbox
                    v-else-if="item.type === 'checkbox'"
                    v-model="formModel[item.key]"
                  >{{ item.label }}</el-checkbox>
                  <el-upload
                    v-else-if="item.type === 'upload'"
                    action="#"
                    :auto-upload="false"
                    :limit="1"
                  >
                    <el-button size="small">选择文件</el-button>
                  </el-upload>
                  <div v-else-if="item.type === 'picker'" class="picker-input">
                    <el-input
                      v-model="formModel[item.key]"
                      :readonly="item.readonly !== false"
                    />
                    <el-button @click="openPicker(item)">{{ item.pickerText }}</el-button>
                  </div>
                  <div v-else-if="item.prefixAction" class="picker-input">
                    <el-input
                      v-model="formModel[item.key]"
                      :readonly="item.readonly"
                      :type="item.type === 'number' ? 'number' : 'text'"
                    />
                    <el-button @click="generateContractNumber">{{ item.prefixAction }}</el-button>
                  </div>
                  <el-input
                    v-else
                    v-model="formModel[item.key]"
                    :readonly="item.readonly"
                    :disabled="item.disabled"
                    :type="item.type === 'number' ? 'number' : 'text'"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>

        <el-card
          v-if="config.lineTabs && config.lineTabs.length && activeFormKind !== 'settlement'"
          shadow="never"
          class="form-section line-section"
        >
          <el-tabs v-model="activeLineTab">
            <el-tab-pane
              v-for="tabItem in config.lineTabs"
              :key="tabItem.label"
              :name="tabItem.label"
              :label="tabItem.label"
            >
              <el-table :data="[]" border height="210" empty-text="暂无明细">
                <el-table-column
                  v-for="item in tabItem.columns"
                  :key="item.key"
                  :prop="item.key"
                  :label="item.label"
                  :width="item.width"
                />
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>

      <span slot="footer" class="dialog-footer">
        <el-button
          v-for="action in activeFormActions"
          :key="action"
          :type="/保存|确定|提交/.test(action.replace(/\s+/g, '')) ? 'primary' : 'default'"
          :data-form-action="action"
          @click="runFormAction(action)"
        >{{ action }}</el-button>
      </span>
    </el-dialog>

    <el-dialog
      :title="pickerTitle"
      :visible.sync="pickerDialogVisible"
      width="760px"
      append-to-body
      data-maternity-picker-dialog
    >
      <el-form :inline="true" size="small">
        <el-form-item :label="pickerType === 'customer' ? '客户名称' : '护理师名称'">
          <el-input v-model="pickerQuery.name" />
        </el-form-item>
        <el-form-item label="手机号码">
          <el-input v-model="pickerQuery.phone" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">搜  索</el-button>
        </el-form-item>
      </el-form>
      <el-table
        :data="pickerRows"
        border
        highlight-current-row
        @current-change="pickerCurrent = $event"
      >
        <el-table-column prop="name" :label="pickerType === 'customer' ? '名称' : '护理师名称'" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="status" :label="pickerType === 'customer' ? '客户状态' : '执业类型'" />
        <el-table-column prop="store" label="分店" />
      </el-table>
      <span slot="footer">
        <el-button @click="pickerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPicker">确  定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getMaternityNursePageConfig } from '@/config/maternity-nurse-pages'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'

const pad = value => String(value).padStart(2, '0')

function formatDate(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export default {
  name: 'MaternityNurseWorkbench',
  components: { AuditedSurfacePanel },
  data() {
    return {
      selectedRows: [],
      formDialogVisible: false,
      activeFormKind: 'record',
      activeFormTitle: '',
      activeSections: [],
      activeFormActions: [],
      activeLineTab: '产康项目',
      formModel: {},
      pickerDialogVisible: false,
      pickerField: null,
      pickerTitle: '',
      pickerType: 'nurse',
      pickerQuery: { name: '', phone: '' },
      pickerCurrent: null,
      pickerRows: [
        { name: '示例护理师A', phone: '138****0001', status: '月嫂', store: '中心广场旗舰店' },
        { name: '示例护理师B', phone: '138****0002', status: '育儿嫂', store: '黄河路轻奢店' }
      ]
    }
  },
  computed: {
    pageTitle() {
      return (this.$route.meta && this.$route.meta.title) || '月嫂档案'
    },
    config() {
      return getMaternityNursePageConfig(this.pageTitle)
    },
    isSchedule() {
      return this.config.mode === 'schedule'
    },
    scheduleDays() {
      const start = new Date()
      return Array.from({ length: 15 }, (_, index) => {
        const current = new Date(start)
        current.setDate(current.getDate() + index)
        return {
          key: formatDate(current),
          label: `${pad(current.getMonth() + 1)}/${pad(current.getDate())}`
        }
      })
    },
    tableRows() {
      if (this.isSchedule) {
        return [
          {
            _id: 'schedule-1',
            field_1: '示例护理师A',
            field_2: '138****0001',
            schedule: [
              { start: 0, end: 3, type: '空闲中' },
              { start: 4, end: 7, type: '预约中' },
              { start: 8, end: 14, type: '上户中' }
            ]
          },
          {
            _id: 'schedule-2',
            field_1: '示例护理师B',
            field_2: '138****0002',
            schedule: [
              { start: 0, end: 5, type: '请假/休假' },
              { start: 6, end: 10, type: '空闲中' },
              { start: 11, end: 14, type: '重叠' }
            ]
          }
        ]
      }
      return [1, 2].map(index => {
        const row = { _id: `${this.config.key}-${index}` }
        this.config.columns.forEach(item => {
          row[item.key] = this.sampleValue(item.label, index)
        })
        return row
      })
    }
  },
  watch: {
    'config.key': {
      immediate: true,
      handler() {
        this.selectedRows = []
        this.formDialogVisible = false
        this.pickerDialogVisible = false
      }
    }
  },
  methods: {
    sampleValue(label, index) {
      if (/护理师名称|预约护理师|当前服务月嫂/.test(label)) return `示例护理师${index === 1 ? 'A' : 'B'}`
      if (/客户名称|客户姓名/.test(label)) return `示例客户${index === 1 ? 'A' : 'B'}`
      if (/电话|手机号|联系方式/.test(label)) return `138****000${index}`
      if (/编号|合同号/.test(label)) return `DEMO-${pad(index)}`
      if (/身份证/.test(label)) return '41**************00'
      if (/门店|分店/.test(label)) return index === 1 ? '中心广场旗舰店' : '黄河路轻奢店'
      if (/日期|时间|预产期|服务开始|服务结束/.test(label)) return `2026-08-${pad(10 + index)}`
      if (/金额|价格|工资|奖励|社保|欠款|已收款/.test(label)) return index === 1 ? '0.00' : '100.00'
      if (/审核状态/.test(label)) return index === 1 ? '待审核' : '已审核'
      if (/状态/.test(label)) return index === 1 ? '正常' : '已完成'
      if (/执业类型/.test(label)) return index === 1 ? '月嫂' : '育儿嫂'
      if (/护理师等级|结算等级|星级/.test(label)) return index === 1 ? '初级月嫂' : '中级月嫂'
      if (/服务类型/.test(label)) return index === 1 ? '会所入住' : '到家服务'
      if (/是否/.test(label)) return index === 1 ? '否' : '是'
      if (/备注/.test(label)) return '脱敏演示'
      if (/附件/.test(label)) return '点击查看附件'
      if (/操作/.test(label)) return ''
      if (/天数|时长|工龄|年龄|数量/.test(label)) return String(10 + index)
      return '--'
    },
    handleSelectionChange(rows) {
      this.selectedRows = rows
    },
    handleBusinessAction(action) {
      const rule = this.config.selectionRules && this.config.selectionRules[action]
      if (rule === 'single' && this.selectedRows.length !== 1) {
        this.$message.warning('请选中一行数据！')
        return
      }
      if (action === '结算' && this.config.settlementSections) {
        this.openForm(
          this.config.settlementTitle,
          this.config.settlementSections,
          this.config.settlementActions,
          'settlement'
        )
        return
      }
      if ((action === '添加' || action === '编辑') && this.config.formSections) {
        this.openForm(
          `${this.config.formTitle}${action === '添加' ? '新增' : '编辑'}`,
          this.config.formSections,
          this.config.formActions,
          action === '添加' ? 'add' : 'edit'
        )
        return
      }
      if (/导出|打印/.test(action)) {
        this.$message.info(`“${action}”已保留原页入口；本地演示不生成真实业务文件`)
        return
      }
      this.$message.info(`“${action}”已按原页保留选择规则；当前仅执行脱敏 Mock`)
    },
    handleQueryAction(action) {
      if (/打印/.test(action)) window.print()
    },
    openForm(title, sections, actions, kind) {
      this.activeFormTitle = title
      this.activeSections = sections
      this.activeFormActions = actions
      this.activeFormKind = kind
      this.activeLineTab = (this.config.lineTabs && this.config.lineTabs[0] && this.config.lineTabs[0].label) || ''
      this.formModel = {}
      sections.forEach(section => {
        section.fields.forEach(item => {
          if (Array.isArray(item.defaultValue)) {
            this.$set(this.formModel, item.key, [...item.defaultValue])
          } else if (item.type === 'checkbox') {
            this.$set(this.formModel, item.key, Boolean(item.defaultValue))
          } else {
            this.$set(this.formModel, item.key, item.defaultValue || '')
          }
        })
      })
      this.formDialogVisible = true
    },
    runFormAction(action) {
      const normalized = action.replace(/\s+/g, '')
      if (/关闭|取消/.test(normalized)) {
        this.formDialogVisible = false
        return
      }
      if (/重置/.test(normalized)) {
        this.openForm(this.activeFormTitle, this.activeSections, this.activeFormActions, this.activeFormKind)
        this.$message.success('已恢复原表单默认值')
        return
      }
      if (action === '查看服务详情') {
        this.$message.info('服务详情入口已保留；当前不读取真实客户服务数据')
        return
      }
      this.$message.success(`“${action}”字段校验演示完成，未写入真实业务数据`)
    },
    openPicker(item) {
      this.pickerField = item
      this.pickerType = /客户/.test(item.label) ? 'customer' : 'nurse'
      this.pickerTitle = this.pickerType === 'customer' ? '选择现有客户' : '选择护理师'
      this.pickerQuery = { name: '', phone: '' }
      this.pickerCurrent = null
      this.pickerRows = this.pickerType === 'customer'
        ? [
          { name: '示例客户A', phone: '138****1001', status: '正入住', store: '中心广场旗舰店' },
          { name: '示例客户B', phone: '138****1002', status: '未入住', store: '黄河路轻奢店' }
        ]
        : [
          { name: '示例护理师A', phone: '138****0001', status: '月嫂', store: '中心广场旗舰店' },
          { name: '示例护理师B', phone: '138****0002', status: '育儿嫂', store: '黄河路轻奢店' }
        ]
      this.pickerDialogVisible = true
    },
    confirmPicker() {
      if (!this.pickerCurrent) {
        this.$message.warning('请选择一行数据')
        return
      }
      this.$set(this.formModel, this.pickerField.key, this.pickerCurrent.name)
      if (Object.prototype.hasOwnProperty.call(this.formModel, 'phone')) {
        this.$set(this.formModel, 'phone', this.pickerCurrent.phone)
      }
      this.pickerDialogVisible = false
    },
    generateContractNumber() {
      this.$set(this.formModel, 'contractNumber', 'YS-DEMO-20260724')
      this.$message.success('已生成本地演示合同编号')
    },
    runRowAction(action) {
      this.$message.info(`“${action}”入口已按原列表保留；当前不读取真实业务附件`)
    },
    cellActionLabels(label) {
      return (this.config.cellActions && this.config.cellActions[label]) || []
    },
    scheduleSegment(row, dayIndex) {
      return (row.schedule || []).find(item => dayIndex >= item.start && dayIndex <= item.end)
    },
    scheduleCellStyle(row, dayIndex) {
      const segment = this.scheduleSegment(row, dayIndex)
      const legend = segment && this.config.scheduleLegend.find(item => item.label === segment.type)
      return { backgroundColor: legend ? legend.color : '#f2f4f7' }
    },
    scheduleCellTitle(row, dayIndex) {
      const segment = this.scheduleSegment(row, dayIndex)
      return segment ? `${this.scheduleDays[dayIndex].key} · ${segment.type}` : this.scheduleDays[dayIndex].key
    }
  }
}
</script>

<style lang="scss" scoped>
.maternity-nurse-workbench {
  min-height: calc(100vh - 84px);
  padding: 22px;
  color: #26354c;
  background: #f3f6fa;
}

.page-hint,
.grid-card {
  margin-top: 10px;
}

.grid-card,
.form-section {
  border: 0;
  border-radius: 12px;
}

.table-footer,
.schedule-legend {
  display: flex;
  align-items: center;
}

.table-footer {
  color: #7b899c;
  font-size: 12px;
}

.grid-card ::v-deep .el-table th {
  color: #43536a;
  background: #eef2ff;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0 8px;
}

.row-actions .el-button + .el-button {
  margin-left: 0;
}

.table-footer {
  justify-content: space-between;
  gap: 20px;
  padding-top: 14px;
}

.schedule-meta {
  margin-bottom: 14px;
}

.schedule-legend {
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 10px;
}

.legend-item {
  color: #5e6d82;
  font-size: 12px;
}

.legend-item i {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 5px;
  border: 1px solid rgba(0, 0, 0, .08);
  border-radius: 2px;
  vertical-align: -1px;
}

.date-axis,
.schedule-track {
  display: grid;
  grid-template-columns: repeat(15, minmax(34px, 1fr));
  min-width: 650px;
}

.date-axis {
  margin-left: 305px;
  color: #8290a5;
  font-size: 11px;
  text-align: center;
}

.schedule-track {
  height: 24px;
  overflow: hidden;
  border: 1px solid #e4e8ef;
  border-radius: 4px;
}

.schedule-cell {
  border-right: 1px solid rgba(255, 255, 255, .75);
}

.form-scroll {
  max-height: 68vh;
  padding-right: 4px;
  overflow-y: auto;
}

.form-section + .form-section {
  margin-top: 14px;
}

.section-title {
  color: #35445b;
  font-weight: 700;
}

.form-section ::v-deep .el-select,
.form-section ::v-deep .el-date-editor,
.form-section ::v-deep .el-input {
  width: 100%;
}

.picker-input {
  display: flex;
  gap: 8px;
}

.picker-input .el-button {
  flex: 0 0 auto;
}

.line-section ::v-deep .el-card__body {
  padding-top: 0;
}

.dialog-footer .el-button + .el-button {
  margin-left: 8px;
}

@media (max-width: 900px) {
  .maternity-nurse-workbench {
    padding: 12px;
  }

  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
