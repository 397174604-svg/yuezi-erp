<template>
  <div class="mall-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i class="el-icon-shopping-bag-2" /> 商城管理 · 独立业务工作台</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageConfig.description }}</p>
      </div>
      <div class="hero-status">
        <el-tag type="success" effect="dark">{{ pageConfig.evidenceLevel }}</el-tag>
      </div>
    </section>

    <audited-surface-panel
      :config="pageConfig"
      show-action-icons
      @business-action="handleBusinessAction"
      @query-action="handleAuditedQueryAction"
    />

    <section class="metric-grid">
      <el-card v-for="metric in metrics" :key="metric.label" shadow="never">
        <i :class="metric.icon" />
        <div><strong>{{ metric.value }}</strong><span>{{ metric.label }}</span></div>
        <small>{{ metric.note }}</small>
      </el-card>
    </section>

    <el-row v-if="pageConfig.mode === 'tree'" :gutter="16" class="tree-layout">
      <el-col :lg="7" :xs="24">
        <el-card shadow="never" class="content-card tree-card">
          <div slot="header" class="card-heading">
            <div><h2>商城分类</h2><p>分类层级为演示草案</p></div>
          </div>
          <el-tree :data="categoryTree" node-key="id" default-expand-all :expand-on-click-node="false" />
        </el-card>
      </el-col>
      <el-col :lg="17" :xs="24">
        <records-table
          :rows="pagedRows"
          :columns="pageConfig.columns"
          :loading="loading"
          @selection-change="selection = $event"
          @details="openDetails"
        />
      </el-col>
    </el-row>

    <el-card v-else-if="pageConfig.mode === 'schedule'" shadow="never" class="content-card schedule-card">
      <div slot="header" class="card-heading">
        <div><h2>周排班概览</h2><p>{{ scheduleRange }} · 双击课程查看报名演示信息</p></div>
        <el-tag type="info">排班字段待核验</el-tag>
      </div>
      <div class="schedule-grid">
        <div class="schedule-corner">时段</div>
        <div v-for="day in scheduleDays" :key="day.date" class="schedule-day">
          <strong>{{ day.label }}</strong><span>{{ day.date.slice(5) }}</span>
        </div>
        <template v-for="period in schedulePeriods">
          <div :key="period" class="schedule-period">{{ period }}</div>
          <div
            v-for="day in scheduleDays"
            :key="`${period}-${day.date}`"
            class="schedule-slot"
            :class="{ occupied: scheduleRecord(day.date, period) }"
            @dblclick="scheduleRecord(day.date, period) && openDetails(scheduleRecord(day.date, period))"
          >
            <template v-if="scheduleRecord(day.date, period)">
              <strong>{{ scheduleRecord(day.date, period).className }}</strong>
              <span>{{ scheduleRecord(day.date, period).startTime }}–{{ scheduleRecord(day.date, period).endTime }}</span>
              <small>{{ scheduleRecord(day.date, period).registrations }}/{{ scheduleRecord(day.date, period).capacity }} 人</small>
            </template>
            <i v-else class="el-icon-plus" @click="openForm('添加排班')" />
          </div>
        </template>
      </div>
      <div class="schedule-table-heading">
        <strong>排班明细</strong>
        <span>以下仍为脱敏演示记录</span>
      </div>
      <records-table
        :rows="pagedRows"
        :columns="pageConfig.columns"
        :loading="loading"
        @selection-change="selection = $event"
        @details="openDetails"
      />
    </el-card>

    <records-table
      v-else
      :rows="pagedRows"
      :columns="pageConfig.columns"
      :loading="loading"
      @selection-change="selection = $event"
      @details="openDetails"
    />

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

    <el-dialog
      :title="dialogTitle"
      :visible.sync="dialogVisible"
      width="820px"
      top="5vh"
      :close-on-click-modal="false"
      @closed="resetDialog"
    >
      <el-alert
        title="本窗口为本地 Mock 演示，不会向原 ERP、妈妈端或真实业务数据库写入数据。"
        type="info"
        :closable="false"
        show-icon
        class="dialog-alert"
      />
      <el-form ref="recordForm" :model="recordForm" label-position="top">
        <el-row :gutter="18">
          <el-col
            v-for="field in dialogFields"
            :key="field.key"
            :span="['textarea', 'richText', 'upload'].includes(field.type) ? 24 : 12"
          >
            <el-form-item
              :label="field.label"
              :prop="field.key"
              :rules="field.required ? [{ required: true, message: `请填写${field.label}`, trigger: 'change' }] : []"
            >
              <field-control :field="field" :model="recordForm" />
              <small class="field-evidence">待原系统二次核验</small>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord">确认（演示）</el-button>
      </div>
    </el-dialog>

    <el-drawer :title="`${pageTitle}详情`" :visible.sync="drawerVisible" size="620px">
      <div v-if="currentRow" class="drawer-content">
        <el-alert title="脱敏演示详情；字段和展示顺序待原系统二次核验。" type="warning" :closable="false" show-icon />
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item v-for="column in pageConfig.columns" :key="column.key" :label="column.label">
            {{ displayValue(currentRow[column.key], column) }}
          </el-descriptions-item>
        </el-descriptions>
        <template v-if="['classes', 'class-schedule'].includes(pageConfig.key)">
          <h3>报名信息（脱敏演示）</h3>
          <el-table :data="registrationRows" size="small" border>
            <el-table-column prop="name" label="报名用户" />
            <el-table-column prop="mobile" label="联系电话" />
            <el-table-column prop="status" label="签到状态" />
          </el-table>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { getMallPageConfig } from '@/config/mall-pages'
import { getMallModuleData, performMallModuleAction, saveMallModuleRecord } from '@/api/erp-mall'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'

const FieldControl = {
  name: 'FieldControl',
  props: {
    field: { type: Object, required: true },
    model: { type: Object, required: true }
  },
  methods: {
    setValue(value) {
      this.$set(this.model, this.field.key, value)
    }
  },
  render(h) {
    const field = this.field
    const value = this.model[field.key]
    if (field.type === 'select') {
      return h('el-select', {
        class: 'full-control',
        props: { value, clearable: true, filterable: true, placeholder: '请选择' },
        on: { input: this.setValue }
      }, field.options.map(option => h('el-option', { key: option, props: { label: option, value: option }})))
    }
    if (field.type === 'date' || field.type === 'dateRange') {
      const isRange = field.type === 'dateRange'
      return h('el-date-picker', {
        class: 'full-control',
        props: {
          value,
          type: isRange ? 'daterange' : 'date',
          valueFormat: 'yyyy-MM-dd',
          rangeSeparator: '至',
          startPlaceholder: '开始日期',
          endPlaceholder: '结束日期',
          placeholder: `请选择${field.label}`
        },
        on: { input: this.setValue }
      })
    }
    if (field.type === 'number') {
      return h('el-input-number', {
        class: 'full-control',
        props: { value: Number(value || 0), min: 0, controlsPosition: 'right' },
        on: { input: this.setValue }
      })
    }
    if (field.type === 'switch') {
      return h('el-switch', {
        props: { value: Boolean(value), activeText: '是', inactiveText: '否' },
        on: { input: this.setValue }
      })
    }
    if (field.type === 'upload') {
      return h('div', { class: 'upload-demo' }, [
        h('el-upload', {
          props: { action: '#', autoUpload: false, showFileList: false },
          on: { change: file => this.setValue(file.name) }
        }, [h('el-button', { props: { size: 'small', type: 'primary', plain: true }}, '选择文件')]),
        h('span', value || '未选择文件（仅本地演示）')
      ])
    }
    if (field.type === 'textarea' || field.type === 'richText') {
      return h('el-input', {
        props: { value, type: 'textarea', rows: field.type === 'richText' ? 6 : 3, placeholder: `请输入${field.label}` },
        on: { input: this.setValue }
      })
    }
    return h('el-input', {
      props: { value, clearable: true, placeholder: `请输入${field.label}` },
      on: { input: this.setValue }
    })
  }
}

const RecordsTable = {
  name: 'RecordsTable',
  props: {
    rows: { type: Array, required: true },
    columns: { type: Array, required: true },
    loading: { type: Boolean, default: false }
  },
  methods: {
    tagType(value) {
      if (['已上架', '已支付', '已出库', '已发布', '已公开', '已回复', '启用', '正常', '可预约', '已确认'].includes(value)) return 'success'
      if (['待审核', '待回复', '部分支付', '待出库', '待发布', '服务中', '待确认'].includes(value)) return 'warning'
      if (['已下架', '停用', '已取消', '休假', '已隐藏', '已退款'].includes(value)) return 'info'
      return ''
    },
    displayValue(value, column) {
      if (column.money) return `¥ ${Number(value || 0).toFixed(2)}`
      return value
    }
  },
  render(h) {
    const columns = [
      h('el-table-column', { props: { type: 'selection', width: 45, fixed: 'left' }}),
      h('el-table-column', { props: { type: 'index', label: '序号', width: 58, fixed: 'left' }}),
      ...this.columns.map(column => h('el-table-column', {
        key: column.key,
        props: {
          prop: column.key,
          label: column.label,
          minWidth: column.width || 110,
          showOverflowTooltip: true
        },
        scopedSlots: {
          default: scope => {
            if (column.tag) return h('el-tag', { props: { size: 'mini', type: this.tagType(scope.row[column.key]) }}, scope.row[column.key])
            if (column.score) return h('el-rate', { props: { value: Number(scope.row[column.key] || 0), disabled: true, showScore: true }})
            return h('span', { class: { money: column.money }}, this.displayValue(scope.row[column.key], column))
          }
        }
      })),
      h('el-table-column', {
        props: { label: '操作', width: 90, fixed: 'right' },
        scopedSlots: {
          default: scope => h('el-button', {
            props: { type: 'text', size: 'mini' },
            on: { click: () => this.$emit('details', scope.row) }
          }, '详情')
        }
      })
    ]
    return h('el-card', { class: 'content-card table-card', props: { shadow: 'never' }}, [
      h('el-table', {
        directives: [{ name: 'loading', value: this.loading }],
        props: { data: this.rows, border: true, stripe: true, height: 520, highlightCurrentRow: true },
        on: {
          'selection-change': value => this.$emit('selection-change', value),
          'row-dblclick': row => this.$emit('details', row)
        }
      }, columns)
    ])
  }
}

export default {
  name: 'MallWorkbench',
  components: { AuditedSurfacePanel, FieldControl, RecordsTable },
  data() {
    return {
      loading: false,
      saving: false,
      rows: [],
      filters: {},
      selection: [],
      pagination: { page: 1, size: 10 },
      dialogVisible: false,
      dialogTitle: '',
      dialogAction: '',
      dialogFields: [],
      recordForm: {},
      drawerVisible: false,
      currentRow: null,
      scheduleOffset: 0,
      registrationRows: [
        { name: '报名用户 A', mobile: '138****7102', status: '已签到' },
        { name: '报名用户 B', mobile: '138****7265', status: '待签到' },
        { name: '报名用户 C', mobile: '138****7381', status: '待签到' }
      ]
    }
  },
  computed: {
    pageTitle() {
      return this.$route.meta.title
    },
    pageConfig() {
      return getMallPageConfig(this.pageTitle)
    },
    filteredRows() {
      return this.rows.filter(row => this.pageConfig.filters.every(field => {
        const filterValue = this.filters[field.key]
        if (filterValue === '' || filterValue === undefined || filterValue === null) return true
        if (Array.isArray(filterValue)) return true
        const rowValue = String(row[field.key] === undefined ? '' : row[field.key]).toLowerCase()
        return field.type === 'input'
          ? rowValue.includes(String(filterValue).trim().toLowerCase())
          : rowValue === String(filterValue).toLowerCase()
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
      return [
        { label: '当前记录', value: this.filteredRows.length, note: '脱敏演示', icon: 'el-icon-document' },
        { label: '待处理', value: this.rows.filter(row => ['待审核', '待回复', '待发布', '待出库'].some(value => Object.values(row).includes(value))).length, note: '推断状态', icon: 'el-icon-bell' },
        { label: '已发布/启用', value: this.rows.filter(row => ['已发布', '已上架', '启用', '正常'].some(value => Object.values(row).includes(value))).length, note: '本地统计', icon: 'el-icon-circle-check' },
        { label: '证据级别', value: 'Visible', note: '待二次核验', icon: 'el-icon-warning-outline' }
      ]
    },
    categoryTree() {
      const roots = ['商城商品', '服务项目', '妈妈课堂']
      return roots.map((root, index) => ({
        id: `ROOT-${index}`,
        label: root,
        children: this.rows.filter(row => row.parent === root).map(row => ({ id: row.id, label: `${row.name}（${row.products}）` }))
      }))
    },
    schedulePeriods() {
      return ['上午', '下午', '晚上']
    },
    scheduleDays() {
      const base = new Date(2026, 6, 20 + this.scheduleOffset * 7)
      return Array.from({ length: 7 }, (_, index) => {
        const current = new Date(base)
        current.setDate(base.getDate() + index)
        const dateValue = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}-${String(current.getDate()).padStart(2, '0')}`
        return { date: dateValue, label: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][index] }
      })
    },
    scheduleRange() {
      return `${this.scheduleDays[0].date} 至 ${this.scheduleDays[6].date}`
    }
  },
  watch: {
    '$route.fullPath'() {
      this.resetPage()
      this.loadData()
    }
  },
  created() {
    this.resetPage()
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const response = await getMallModuleData(this.pageConfig.key)
        const list = response.data && Array.isArray(response.data.list) ? response.data.list : []
        this.rows = list
      } finally {
        this.loading = false
      }
    },
    createDemoRow(index) {
      const stores = ['中心广场旗舰店', '黄河路轻奢店']
      const dateValue = `2026-07-${String(20 + index % 8).padStart(2, '0')}`
      const categoryValues = ['妈妈护理', '宝宝用品', '产康用品', '营养膳食']
      const statusValues = ['已上架', '已下架']
      const parents = ['商城商品', '服务项目', '妈妈课堂']
      return {
        id: `MALL-DEMO-${this.pageConfig.key}-${index + 1}`,
        code: `DEMO-${String(index + 1).padStart(4, '0')}`,
        name: `${this.pageTitle}演示记录 ${index + 1}`,
        title: `${this.pageTitle}演示标题 ${index + 1}`,
        store: stores[index % stores.length],
        category: categoryValues[index % categoryValues.length],
        spec: ['标准装', '礼盒装', '体验装'][index % 3],
        unit: ['套', '盒', '次'][index % 3],
        costPrice: 80 + index * 6,
        originalPrice: 199 + index * 10,
        salePrice: 179 + index * 10,
        pointPrice: 1790 + index * 100,
        stockQuantity: 20 + index,
        status: statusValues[index % 2],
        integral: index % 2 ? '否' : '是',
        inStore: index % 3 ? '是' : '否',
        recommended: index % 3 ? '否' : '是',
        type: ['商城商品', '服务项目', '妈妈课堂'][index % 3],
        payMethod: ['微信结算', '会员卡', '积分支付'][index % 3],
        amount: 268 + index * 20,
        coupon: index % 2 ? 0 : 20,
        debt: index % 3 ? 0 : 80,
        orderedAt: `${dateValue} 10:${String(10 + index).padStart(2, '0')}`,
        customer: `演示客户 ${String.fromCharCode(65 + index % 5)}`,
        nickname: `演示用户 ${String.fromCharCode(65 + index % 5)}`,
        mobile: `138****${String(2108 + index).padStart(4, '0')}`,
        pickup: ['门店自提', '快递配送', '到店服务'][index % 3],
        payStatus: ['未支付', '部分支付', '已支付'][index % 3],
        stockStatus: ['待出库', '已出库', '待核销'][index % 3],
        jobType: ['月嫂', '育儿嫂', '催乳师'][index % 3],
        level: ['初级月嫂', '中级月嫂', '高级月嫂'][index % 3],
        age: 35 + index % 10,
        standardFee: 8800 + index * 300,
        serviceStatus: ['可预约', '服务中', '休假'][index % 3],
        enabled: index % 4 ? '启用' : '停用',
        parent: parents[index % parents.length],
        navigationName: `演示导航 ${index + 1}`,
        sort: (index + 1) * 10,
        products: 5 + index,
        section: ['育儿知识', '护理知识', '妈咪课堂'][index % 3],
        stage: ['新生儿', '婴儿期', '幼儿期', '学龄前'][index % 4],
        contentType: ['图文', '视频', '音频'][index % 3],
        author: `演示运营员 ${String.fromCharCode(65 + index % 3)}`,
        publishedAt: `${dateValue} 09:20`,
        pinned: index % 3 ? '否' : '是',
        question: `这是第 ${index + 1} 条脱敏演示问题，具体内容不来自原 ERP。`,
        askedAt: `${dateValue} 08:30`,
        expert: ['护理专家', '产康专家', '营养师'][index % 3],
        replyStatus: index % 2 ? '已回复' : '待回复',
        visibility: index % 3 ? '公开' : '仅本人',
        content: `这是第 ${index + 1} 条脱敏演示内容，不包含真实客户或业务数据。`,
        images: index % 4,
        createdAt: `${dateValue} 11:00`,
        postedAt: `${dateValue} 13:30`,
        views: 80 + index * 12,
        commentType: ['物料', '项目', '膳食'][index % 3],
        target: `演示商品或项目 ${index + 1}`,
        productScore: 3 + index % 3,
        packageScore: 3 + (index + 1) % 3,
        speedScore: 3 + (index + 2) % 3,
        serviceScore: 4 + index % 2,
        location: `${stores[index % stores.length]} · 演示教室`,
        fee: index % 2 ? 99 : 0,
        audience: '孕产家庭（演示）',
        description: '脱敏演示说明，待原系统二次核验。',
        baseProject: `演示基础项目 ${index + 1}`,
        capacity: 20 + index,
        registrations: 6 + index,
        classDate: this.scheduleDays[index % 7].date,
        period: this.schedulePeriods[index % 3],
        className: `妈妈课堂演示课程 ${index + 1}`,
        teacher: `演示讲师 ${String.fromCharCode(65 + index % 3)}`,
        startTime: ['09:00', '14:00', '19:00'][index % 3],
        endTime: ['10:30', '15:30', '20:30'][index % 3],
        remark: '仅用于字段与交互草案展示。'
      }
    },
    resetPage() {
      this.filters = {}
      this.selection = []
      this.pagination = { page: 1, size: 10 }
      this.drawerVisible = false
      this.dialogVisible = false
    },
    resetFilters() {
      this.filters = {}
      this.pagination.page = 1
    },
    search() {
      this.pagination.page = 1
      this.$message.success(`已按当前条件筛选，共 ${this.filteredRows.length} 条脱敏演示记录`)
    },
    handleAuditedQueryAction(action) {
      if (/查询|搜索/.test(String(action).replace(/\s+/g, ''))) this.search()
      if (/打印/.test(action)) window.print()
      if (/导出/.test(action)) this.exportRows()
    },
    requireSelection() {
      if (this.selection.length) return true
      this.$message.warning('请先选择一条脱敏演示记录')
      return false
    },
    handleBusinessAction(action) {
      if (['新增', '补录订单', '新增分类', '新增子分类', '发布内容', '新增问答', '新增评语', '发布帖子', '新增图文', '新增课程', '添加排班'].includes(action)) {
        this.openForm(action)
        return
      }
      if (action === '编辑回复') {
        if (!this.requireSelection()) return
        this.openForm(action, this.selection[0], this.pageConfig.replyFields || this.pageConfig.formFields)
        return
      }
      if (['编辑', '编辑分类', '编辑排班'].includes(action)) {
        if (!this.requireSelection()) return
        this.openForm(action, this.selection[0])
        return
      }
      if (action === '回复') {
        if (!this.requireSelection()) return
        this.openForm(action, this.selection[0], this.pageConfig.replyFields || this.pageConfig.formFields)
        return
      }
      if (['查看', '查看详情', '预览', '查看报名'].includes(action)) {
        if (!this.requireSelection()) return
        this.openDetails(this.selection[0])
        return
      }
      if (action === '导出') {
        this.exportCsv()
        return
      }
      if (action === '上一周') {
        this.scheduleOffset -= 1
        return
      }
      if (action === '本周') {
        this.scheduleOffset = 0
        return
      }
      if (action === '下一周') {
        this.scheduleOffset += 1
        return
      }
      if (action === '复制本周') {
        this.$message.info('已生成本地排班复制演示，未写入真实业务')
        return
      }
      if (!this.requireSelection()) return
      this.confirmStateAction(action)
    },
    async confirmStateAction(action) {
      const selectedIds = this.selection.map(row => row.id)
      try {
        await this.$confirm(`确认对已选 ${selectedIds.length} 条演示记录执行“${action}”？该操作不会写入真实 ERP。`, '演示操作', { type: 'warning' })
        await performMallModuleAction(this.pageConfig.key, action, { ids: selectedIds })
        this.applyLocalState(action)
        this.$message.success(`${action}已在本地演示数据中完成`)
      } catch (error) {
        if (error !== 'cancel' && error !== 'close') throw error
      }
    },
    applyLocalState(action) {
      if (['删除', '删除分类', '删除排班'].includes(action)) {
        const ids = new Set(this.selection.map(row => row.id))
        this.rows = this.rows.filter(row => !ids.has(row.id))
        this.selection = []
        return
      }
      const mappings = {
        上架: ['status', '已上架'],
        下架: ['status', '已下架'],
        推荐: ['recommended', '是'],
        取消推荐: ['recommended', '否'],
        启用: ['enabled', '启用'],
        停用: ['enabled', '停用'],
        设置可预约: ['serviceStatus', '可预约'],
        确认支付: ['payStatus', '已支付'],
        确认出库: ['stockStatus', '已出库'],
        取消订单: ['status', '已取消'],
        退款: ['payStatus', '已退款'],
        发布: ['status', '已发布'],
        撤回: ['status', '待发布'],
        置顶: ['pinned', '是'],
        取消置顶: ['pinned', '否'],
        审核通过: ['status', '已公开'],
        隐藏: ['status', '已隐藏'],
        公开: ['visibility', '公开']
      }
      const mapping = mappings[action]
      if (mapping) this.selection.forEach(row => this.$set(row, mapping[0], mapping[1]))
    },
    openForm(action, row = {}, fields = this.pageConfig.formFields) {
      if (!fields || !fields.length) {
        this.$message.warning('该动作表单待原系统二次核验')
        return
      }
      this.dialogAction = action
      this.dialogTitle = `${action} · ${this.pageTitle}`
      this.dialogFields = fields
      this.recordForm = fields.reduce((form, field) => {
        const value = row[field.key]
        form[field.key] = value !== undefined ? value : (field.type === 'number' ? 0 : field.type === 'switch' ? false : '')
        return form
      }, { id: row.id })
      this.dialogVisible = true
    },
    async saveRecord() {
      this.$refs.recordForm.validate(async valid => {
        if (!valid) return
        this.saving = true
        try {
          await saveMallModuleRecord(this.pageConfig.key, this.recordForm)
          const existing = this.rows.find(row => row.id === this.recordForm.id)
          if (existing) {
            Object.assign(existing, this.recordForm)
          } else {
            this.rows.unshift({ ...this.createDemoRow(this.rows.length), ...this.recordForm, id: `MALL-LOCAL-${Date.now()}` })
          }
          this.dialogVisible = false
          this.$message.success('已保存到本地 Mock 演示数据，未同步真实妈妈端')
        } finally {
          this.saving = false
        }
      })
    },
    resetDialog() {
      this.dialogFields = []
      this.recordForm = {}
      this.$nextTick(() => {
        if (this.$refs.recordForm) this.$refs.recordForm.clearValidate()
      })
    },
    openDetails(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    scheduleRecord(dateValue, period) {
      return this.rows.find(row => row.classDate === dateValue && row.period === period)
    },
    actionIcon(action) {
      if (['新增', '补录订单', '新增分类', '新增子分类', '发布内容', '新增问答', '新增评语', '发布帖子', '新增图文', '新增课程', '添加排班'].includes(action)) return 'el-icon-plus'
      if (action.includes('编辑')) return 'el-icon-edit'
      if (action.includes('删除')) return 'el-icon-delete'
      if (action === '导出') return 'el-icon-download'
      if (['查看', '查看详情', '预览', '查看报名'].includes(action)) return 'el-icon-view'
      if (action === '回复') return 'el-icon-chat-line-square'
      return ''
    },
    displayValue(value, column) {
      if (column.money) return `¥ ${Number(value || 0).toFixed(2)}`
      return value
    },
    exportCsv() {
      const columns = this.pageConfig.columns
      const lines = [
        columns.map(column => column.label).join(','),
        ...this.filteredRows.map(row => columns.map(column => `"${String(row[column.key] || '').replace(/"/g, '""')}"`).join(','))
      ]
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-脱敏演示.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    }
  }
}
</script>

<style lang="scss" scoped>
.mall-workbench {
  min-height: calc(100vh - 84px);
  padding: 20px;
  background: #f4f7f9;
  color: #27364b;
}

.hero-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 22px 24px;
  margin-bottom: 14px;
  color: #fff;
  border-radius: 12px;
  background: linear-gradient(120deg, #218f96, #35b7bd 58%, #63c9b5);
  box-shadow: 0 8px 24px rgba(38, 157, 163, 0.2);

  h1 {
    margin: 7px 0 8px;
    font-size: 25px;
  }

  p {
    margin: 0;
    color: rgba(255, 255, 255, 0.82);
  }
}

.eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
}

.hero-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.evidence-alert,
.metric-grid,
.content-card,
.tree-layout {
  margin-bottom: 14px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;

  .el-card ::v-deep .el-card__body {
    display: grid;
    grid-template-columns: 42px 1fr auto;
    align-items: center;
    gap: 12px;
  }

  i {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    color: #218f96;
    border-radius: 10px;
    background: #e7f7f6;
    font-size: 20px;
  }

  div {
    display: grid;
  }

  strong {
    font-size: 22px;
  }

  span,
  small {
    color: #8b96a7;
    font-size: 12px;
  }
}

.content-card {
  border: 0;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(27, 45, 75, 0.055);
}

.action-card ::v-deep .el-card__body {
  padding: 12px 16px;
}

.toolbar,
.card-heading,
.pagination-row,
.schedule-table-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.toolbar > div {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar span,
.card-heading p,
.pagination-row,
.schedule-table-heading span {
  color: #8b96a7;
  font-size: 12px;
}

.card-heading {
  h2 {
    margin: 0 0 4px;
    font-size: 16px;
  }

  p {
    margin: 0;
  }
}

.filter-card ::v-deep .el-card__body {
  padding-bottom: 4px;
}

.full-control {
  width: 100%;
}

.tree-card {
  min-height: 590px;
}

.pagination-row {
  padding: 4px 0 18px;
}

.schedule-grid {
  display: grid;
  grid-template-columns: 90px repeat(7, minmax(120px, 1fr));
  min-width: 1020px;
  margin-bottom: 18px;
  border-top: 1px solid #e7edf2;
  border-left: 1px solid #e7edf2;
}

.schedule-card {
  overflow-x: auto;
}

.schedule-grid > div {
  min-height: 72px;
  padding: 10px;
  border-right: 1px solid #e7edf2;
  border-bottom: 1px solid #e7edf2;
}

.schedule-corner,
.schedule-day,
.schedule-period {
  display: grid;
  place-items: center;
  color: #667589;
  background: #f8fafc;
  font-size: 12px;
}

.schedule-day span {
  color: #9aa5b4;
}

.schedule-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c1c9d2;
  cursor: pointer;
}

.schedule-slot.occupied {
  align-items: flex-start;
  justify-content: flex-start;
  color: #2f5d61;
  border-top: 3px solid #35b7bd;
  background: #eefafa;

  span,
  small {
    margin-top: 7px;
    color: #71838a;
    font-size: 12px;
  }
}

.schedule-table-heading {
  margin: 16px 0 10px;
}

.dialog-alert {
  margin-bottom: 18px;
}

.field-evidence {
  display: block;
  margin-top: 4px;
  color: #d49a31;
}

.upload-demo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #909399;
}

.drawer-content {
  padding: 0 20px 30px;

  .el-alert,
  .el-descriptions {
    margin-bottom: 18px;
  }
}

.money {
  color: #e16d64;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .mall-workbench {
    padding: 12px;
  }

  .hero-panel,
  .toolbar {
    display: block;
  }

  .hero-status {
    margin-top: 16px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
