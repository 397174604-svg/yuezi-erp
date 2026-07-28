<template>
  <div class="system-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i class="el-icon-setting" /> 系统设置 · 独立工作台草案</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <div class="hero-status">
        <el-tag type="success" effect="dark">页面身份已核验</el-tag>
        <el-tag type="warning" effect="dark">内部字段待核验</el-tag>
        <span>完成等级：{{ config.completionLevel }}</span>
      </div>
    </section>

    <el-alert
      :title="config.evidenceNote"
      type="warning"
      :closable="false"
      show-icon
      class="evidence-alert"
    />

    <section class="audit-grid">
      <div class="audit-card">
        <span>菜单覆盖</span>
        <strong>{{ repositoryMenuCount }} / {{ expectedMenuCount }}</strong>
        <small>20 个标题、URL、navid 已对应</small>
      </div>
      <div class="audit-card">
        <span>原页面身份</span>
        <strong>{{ config.originalNavid || '待核验' }}</strong>
        <small>{{ config.originalUrl || '原始 URL 待核验' }}</small>
      </div>
      <div class="audit-card">
        <span>结构字段草案</span>
        <strong>{{ config.filters.length + config.columns.length + config.formFields.length }}</strong>
        <small>标签、顺序、控件、默认值全部待核验</small>
      </div>
      <div class="audit-card">
        <span>工具栏证据</span>
        <strong>0</strong>
        <small>未添加任何推断的原系统业务按钮</small>
      </div>
    </section>

    <el-card v-if="config.structure.length" shadow="never" class="content-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>页面结构假设 <el-tag size="mini" type="warning">待核验</el-tag></h2>
          <p>原页面是否为树、列表、权限矩阵、编辑器或组合页尚未取得内部证据</p>
        </div>
        <el-tag effect="plain">{{ config.mode }}</el-tag>
      </div>
      <div class="structure-list">
        <span v-for="item in config.structure" :key="item"><i class="el-icon-folder-opened" />{{ item }}</span>
      </div>
    </el-card>

    <el-card v-if="config.dependencies.length" shadow="never" class="content-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>依赖关系核验清单</h2>
          <p>以下仅是二次审计要逐项验证的场景，不是已实现的原系统规则</p>
        </div>
      </div>
      <div class="dependency-list">
        <span v-for="item in config.dependencies" :key="item"><i class="el-icon-warning-outline" />{{ item }}</span>
      </div>
    </el-card>

    <el-card shadow="never" class="content-card filter-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>查询区结构草案</h2>
          <p>“本地筛选”和“清空草案条件”是调试操作，不是原 ERP 工具栏证据</p>
        </div>
        <div>
          <el-button size="small" @click="resetFilters">清空草案条件</el-button>
          <el-button size="small" type="primary" @click="runLocalFilter">本地筛选</el-button>
        </div>
      </div>
      <el-form label-position="top" class="filter-form">
        <el-row :gutter="16">
          <el-col
            v-for="item in config.filters"
            :key="item.key"
            :xl="6"
            :lg="8"
            :md="12"
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
                placeholder="选项待原系统核验"
                class="full-control"
              >
                <el-option
                  v-for="option in item.options"
                  :key="option"
                  :label="option"
                  :value="option"
                  disabled
                />
              </el-select>
              <el-date-picker
                v-else-if="item.type === 'dateRange'"
                v-model="filters[item.key]"
                type="daterange"
                value-format="yyyy-MM-dd"
                range-separator="至"
                start-placeholder="开始日期待核验"
                end-placeholder="结束日期待核验"
                class="full-control"
              />
              <el-date-picker
                v-else-if="item.type === 'date'"
                v-model="filters[item.key]"
                type="date"
                value-format="yyyy-MM-dd"
                placeholder="日期默认值待核验"
                class="full-control"
              />
              <el-cascader
                v-else-if="item.type === 'tree'"
                v-model="filters[item.key]"
                :options="treeDraftOptions"
                :props="{ checkStrictly: true }"
                clearable
                placeholder="层级节点待原系统核验"
                class="full-control"
              />
              <el-input
                v-else
                v-model="filters[item.key]"
                clearable
                :placeholder="`${item.label}待原系统核验`"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card shadow="never" class="content-card table-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>列表字段结构草案 <el-tag size="mini" type="info">脱敏演示</el-tag></h2>
          <p>真实表头、顺序、格式、汇总、排序和行操作待原系统二次核验</p>
        </div>
        <span class="result-count">共 {{ filteredRows.length }} 条脱敏演示记录</span>
      </div>
      <el-table v-loading="loading" :data="filteredRows" border stripe>
        <el-table-column type="index" label="演示序号" width="86" fixed="left" />
        <el-table-column
          v-for="item in config.columns"
          :key="item.key"
          :prop="item.key"
          :min-width="item.width || 120"
          show-overflow-tooltip
        >
          <template slot="header">
            <span>{{ item.label }}</span>
            <small class="header-unverified">待核验</small>
          </template>
          <template slot-scope="scope">
            <el-tag v-if="item.format === 'status'" size="mini" type="info">{{ scope.row[item.key] }}</el-tag>
            <span v-else>{{ scope.row[item.key] }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" class="content-card form-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>新增/编辑字段草案</h2>
          <p>不提供保存、发布、启停、授权、执行或删除；必填、校验、控件与权限均待核验</p>
        </div>
        <el-tag type="warning" effect="plain">不可提交</el-tag>
      </div>
      <el-row :gutter="14">
        <el-col v-for="field in config.formFields" :key="field.key" :xl="6" :lg="8" :md="12" :xs="24">
          <div class="field-card">
            <div>
              <strong>{{ field.label }}</strong>
              <span>{{ fieldTypeLabel(field.type) }}</span>
            </div>
            <el-tag size="mini" type="warning">待核验</el-tag>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="content-card gap-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>本页未核验项</h2>
          <p>原系统审计时必须逐项关闭，不得跨页面复用推断</p>
        </div>
      </div>
      <div class="gap-list">
        <el-tag v-for="item in auditGaps" :key="item" type="warning" effect="plain">{{ item }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script>
import {
  SYSTEM_EXPECTED_MENU_COUNT,
  SYSTEM_REPOSITORY_MENU_COUNT,
  getSystemPageConfig
} from '@/config/system-pages'
import { getSystemModuleData } from '@/api/erp-system'

export default {
  name: 'SystemWorkbench',
  data() {
    return {
      filters: {},
      rows: [],
      loading: false,
      expectedMenuCount: SYSTEM_EXPECTED_MENU_COUNT,
      repositoryMenuCount: SYSTEM_REPOSITORY_MENU_COUNT,
      treeDraftOptions: [{
        value: 'unverified-root',
        label: '层级节点待原系统核验',
        disabled: true
      }],
      auditGaps: [
        '页面模式与区域顺序',
        '查询字段与默认值',
        '完整下拉选项顺序',
        '树层级与选择规则',
        '工具栏标签/顺序/位置',
        '列表表头/格式/汇总',
        '新增编辑表单与必填',
        '权限隐藏与数据范围',
        '状态机与审批流转',
        '上传/导入/导出/打印',
        '调度/消息/预警真实行为',
        '真实后端持久化'
      ]
    }
  },
  computed: {
    pageTitle() {
      return this.$route.meta.title
    },
    config() {
      return getSystemPageConfig(this.pageTitle)
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
      this.resetFilters()
      this.loadData()
    },
    resetFilters() {
      const next = {}
      this.config.filters.forEach(item => {
        next[item.key] = ['dateRange', 'tree'].includes(item.type) ? [] : ''
      })
      this.filters = next
    },
    async loadData() {
      this.loading = true
      try {
        const response = await getSystemModuleData(this.config.key, this.filters)
        const list = response.data && response.data.list
        this.rows = list && list.length ? list : this.createDemoRows()
      } catch (error) {
        this.rows = this.createDemoRows()
      } finally {
        this.loading = false
      }
    },
    runLocalFilter() {
      this.$message.info('仅筛选脱敏 Mock；原系统查询行为待二次核验')
    },
    createDemoRows() {
      return Array.from({ length: 3 }, (_, index) => {
        const row = { id: `${this.config.key}-${index + 1}` }
        this.config.columns.forEach(item => {
          row[item.key] = this.sampleValue(item, index)
        })
        return row
      })
    },
    sampleValue(item, index) {
      if (item.format === 'date') return `2026-07-${String(20 + index).padStart(2, '0')}`
      if (item.format === 'number') return index + 1
      if (item.format === 'status') return '演示状态'

      const suffix = String.fromCharCode(65 + index)
      const safeValues = {
        account: `demo_user_${index + 1}`,
        displayName: `演示用户${suffix}`,
        mobile: '138****0000',
        operator: `演示操作员${suffix}`,
        recipient: `演示接收人${suffix}`,
        recipientAddress: '138****0000',
        ipAddress: '192.0.2.1',
        departmentCode: `DEPT-DEMO-${index + 1}`,
        departmentName: `演示部门${suffix}`,
        roleCode: `ROLE-DEMO-${index + 1}`,
        roleName: `演示角色${suffix}`,
        workflowCode: `FLOW-DEMO-${index + 1}`,
        workflowName: `演示流程${suffix}`,
        taskCode: `TASK-DEMO-${index + 1}`,
        taskName: `演示任务${suffix}`,
        parameterValue: '演示值',
        accessKey: '********'
      }
      return Object.prototype.hasOwnProperty.call(safeValues, item.key)
        ? safeValues[item.key]
        : `演示值${suffix}`
    },
    fieldTypeLabel(type) {
      const labels = {
        input: '输入框草案',
        select: '下拉框草案（选项待核验）',
        date: '日期控件草案',
        dateRange: '日期范围草案',
        number: '数字输入草案',
        textarea: '多行文本草案',
        tree: '树选择草案（层级待核验）',
        switch: '开关草案（默认值待核验）'
      }
      return labels[type] || '控件类型待核验'
    }
  }
}
</script>

<style lang="scss" scoped>
.system-workbench {
  min-height: 100%;
  padding: 20px;
  color: #26344a;
  background: #f4f7fa;
}
.hero-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 25px 28px;
  color: #fff;
  background: linear-gradient(128deg, #425269, #65758b 62%, #8291a3);
  border-radius: 15px;
  box-shadow: 0 13px 30px rgba(50, 67, 88, .2);
}
.eyebrow {
  margin-bottom: 9px;
  color: #edf2f7;
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
  color: #eef3f8;
  font-size: 14px;
  line-height: 1.7;
}
.hero-status {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
}
.hero-status span {
  color: #edf2f7;
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
  min-width: 0;
  padding: 17px 19px;
  background: #fff;
  border: 1px solid #e2e8ef;
  border-radius: 12px;
}
.audit-card span,
.audit-card strong,
.audit-card small {
  display: block;
}
.audit-card span {
  color: #76869a;
  font-size: 12px;
}
.audit-card strong {
  margin: 7px 0 5px;
  color: #4f6176;
  font-size: 22px;
}
.audit-card small {
  overflow: hidden;
  color: #9aa6b3;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.content-card {
  margin-top: 16px;
  border: 0;
  border-radius: 12px;
}
.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.card-heading h2 {
  margin: 0 0 4px;
  font-size: 16px;
}
.card-heading p {
  margin: 0;
  color: #8996a5;
  font-size: 12px;
}
.structure-list,
.dependency-list,
.gap-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}
.structure-list span,
.dependency-list span {
  padding: 10px 13px;
  color: #586a7a;
  background: #f5f8fa;
  border-radius: 8px;
  font-size: 13px;
}
.structure-list i,
.dependency-list i {
  margin-right: 6px;
  color: #718698;
}
.dependency-list span {
  color: #886524;
  background: #fff9eb;
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
  color: #596b7c;
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
.table-card ::v-deep .el-table th {
  color: #405469;
  background: #f5f8fa;
}
.header-unverified {
  display: block;
  color: #c88b2b;
  font-size: 9px;
  font-weight: 400;
}
.result-count {
  color: #8593a3;
  font-size: 12px;
}
.field-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 65px;
  padding: 11px 13px;
  margin-bottom: 12px;
  background: #f8fafb;
  border: 1px solid #e7edf1;
  border-radius: 9px;
}
.field-card div {
  min-width: 0;
}
.field-card strong,
.field-card span {
  display: block;
}
.field-card strong {
  overflow: hidden;
  color: #46596a;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.field-card span {
  margin-top: 5px;
  color: #97a3ae;
  font-size: 10px;
}
@media (max-width: 1000px) {
  .audit-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .hero-status {
    align-items: flex-end;
    flex-direction: column;
  }
}
@media (max-width: 760px) {
  .system-workbench {
    padding: 12px;
  }
  .hero-panel,
  .hero-status,
  .card-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .audit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
