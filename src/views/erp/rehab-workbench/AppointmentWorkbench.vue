<template>
  <div class="appointment-workbench">
    <section class="page-head">
      <div>
        <div class="eyebrow">P0 · 预约与排班</div>
        <h1>预约管理</h1>
        <p>统一处理预约参观、服务预约、人员排班以及门店、人员、时段与资源冲突。</p>
      </div>
      <div class="head-actions">
        <el-button icon="el-icon-refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button type="primary" icon="el-icon-plus" @click="openBooking()">新建预约</el-button>
      </div>
    </section>

    <el-alert
      class="source-alert"
      type="warning"
      :closable="false"
      show-icon
      title="当前项目与资源范围取自已收到的业务资料；未确认的服务房间和设备不会强制占用，待甲方确认后在基础资料中维护。"
    />

    <section class="filter-panel">
      <div class="filter-grid">
        <label>
          <span>预约门店</span>
          <el-select v-model="filters.store" placeholder="请选择门店">
            <el-option v-for="item in options.stores" :key="item.id" :label="item.name" :value="item.name" />
          </el-select>
        </label>
        <label>
          <span>预约分类</span>
          <el-select v-model="filters.appointmentType" clearable placeholder="全部分类">
            <el-option v-for="item in appointmentTypes" :key="item" :label="item" :value="item" />
          </el-select>
        </label>
        <label>
          <span>预约日期</span>
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            value-format="yyyy-MM-dd"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </label>
        <label>
          <span>服务状态</span>
          <el-select v-model="filters.serviceStatus" clearable placeholder="全部状态">
            <el-option v-for="item in serviceStatuses" :key="item" :label="item" :value="item" />
          </el-select>
        </label>
        <label>
          <span>人员</span>
          <el-select v-model="filters.technician" clearable filterable placeholder="全部人员">
            <el-option v-for="item in storeStaff" :key="item.id" :label="staffLabel(item)" :value="item.name" />
          </el-select>
        </label>
        <label class="keyword-filter">
          <span>客户 / 手机 / 项目</span>
          <el-input v-model.trim="filters.keyword" clearable placeholder="输入关键词" @keyup.enter.native="loadData" />
        </label>
      </div>
      <div class="filter-actions">
        <span class="auto-query"><i class="el-icon-success" /> 切换门店、分类、日期或状态后自动查询</span>
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="primary" @click="loadData">查询</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article>
        <span>今日预约</span>
        <strong>{{ summary.today }}</strong>
        <small>当前门店全部分类</small>
      </article>
      <article>
        <span>待确认</span>
        <strong>{{ summary.pending }}</strong>
        <small>需要电话或到店确认</small>
      </article>
      <article>
        <span>今日进行中</span>
        <strong>{{ summary.inProgress }}</strong>
        <small>已到店或服务中</small>
      </article>
      <article :class="{ warning: summary.conflicts > 0 }">
        <span>冲突预警</span>
        <strong>{{ summary.conflicts }}</strong>
        <small>人员或资源时间重叠</small>
      </article>
    </section>

    <section class="content-panel">
      <div class="content-head">
        <div>
          <h2>{{ filters.store || '全部门店' }}预约排期</h2>
          <p>列表用于业务流转，周排期用于查看人员和资源占用。</p>
        </div>
        <el-radio-group v-model="activeView" size="small">
          <el-radio-button label="list">预约台账</el-radio-button>
          <el-radio-button label="week">周排期</el-radio-button>
        </el-radio-group>
      </div>

      <el-table
        v-if="activeView === 'list'"
        v-loading="loading"
        :data="rows"
        border
        stripe
        empty-text="当前条件暂无预约"
      >
        <el-table-column prop="appointmentNo" label="预约单号" min-width="155" />
        <el-table-column prop="appointmentType" label="分类" width="100">
          <template slot-scope="{ row }"><el-tag size="mini" effect="plain">{{ row.appointmentType }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="customerName" label="客户" width="100" />
        <el-table-column prop="store" label="门店" min-width="145" />
        <el-table-column prop="serviceItem" label="预约内容" min-width="160" show-overflow-tooltip />
        <el-table-column label="预约时间" min-width="175">
          <template slot-scope="{ row }">
            <div class="time-cell"><strong>{{ row.appointmentDate }}</strong><span>{{ row.appointmentPeriod }}</span></div>
          </template>
        </el-table-column>
        <el-table-column prop="technician" label="负责人员" width="120" />
        <el-table-column prop="resourceName" label="房间 / 设备" min-width="135">
          <template slot-scope="{ row }">{{ row.resourceName || '未指定' }}</template>
        </el-table-column>
        <el-table-column prop="serviceStatus" label="状态" width="96">
          <template slot-scope="{ row }"><el-tag size="mini" :type="statusType(row.serviceStatus)">{{ row.serviceStatus }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="245" fixed="right">
          <template slot-scope="{ row }">
            <el-button v-for="action in rowActions(row)" :key="action" type="text" @click="handleRowAction(action, row)">
              {{ action }}
            </el-button>
            <el-button type="text" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-else v-loading="loading" class="week-board">
        <article v-for="day in weekDays" :key="day.date" :class="{ today: day.date === todayText }" class="day-column">
          <header>
            <span>{{ day.weekday }}</span>
            <strong>{{ day.label }}</strong>
            <em>{{ day.items.length }} 项</em>
          </header>
          <div v-if="day.items.length" class="day-events">
            <button v-for="item in day.items" :key="item.id" type="button" class="event-card" @click="openDetail(item)">
              <span>{{ item.appointmentPeriod }}</span>
              <strong>{{ item.customerName }} · {{ item.serviceItem }}</strong>
              <small>{{ item.technician }}{{ item.resourceName ? ` · ${item.resourceName}` : '' }}</small>
              <el-tag size="mini" :type="statusType(item.serviceStatus)">{{ item.serviceStatus }}</el-tag>
            </button>
          </div>
          <div v-else class="empty-day">暂无预约</div>
        </article>
      </div>
    </section>

    <el-dialog
      :title="editingId ? '改期 / 编辑预约' : '新建预约'"
      :visible.sync="dialogVisible"
      width="820px"
      top="5vh"
      :close-on-click-modal="false"
    >
      <el-form ref="bookingForm" :model="bookingForm" :rules="bookingRules" label-position="top" class="booking-form">
        <el-row :gutter="18">
          <el-col :span="12">
            <el-form-item label="预约门店" prop="store">
              <el-select v-model="bookingForm.store" class="full-control" placeholder="先选择门店" @change="onFormStoreChange">
                <el-option v-for="item in options.stores" :key="item.id" :label="item.name" :value="item.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预约分类" prop="appointmentType">
              <el-select v-model="bookingForm.appointmentType" class="full-control" placeholder="请选择" @change="onAppointmentTypeChange">
                <el-option v-for="item in appointmentTypes" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户" prop="customerName">
              <el-select v-model="bookingForm.customerName" class="full-control" filterable placeholder="仅显示当前门店客户">
                <el-option
                  v-for="item in formCustomers"
                  :key="item.id"
                  :label="`${item.name} · ${item.mobile}`"
                  :value="item.name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人员" prop="technician">
              <el-select v-model="bookingForm.technician" class="full-control" filterable placeholder="仅显示当前门店可用人员">
                <el-option v-for="item in formStaff" :key="item.id" :label="staffLabel(item)" :value="item.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="服务类别" prop="serviceCategory">
              <el-select v-model="bookingForm.serviceCategory" class="full-control" placeholder="请选择">
                <el-option v-for="item in formCategories" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预约内容" prop="serviceItem">
              <el-select v-model="bookingForm.serviceItem" class="full-control" filterable placeholder="仅显示当前门店已配置项目">
                <el-option v-for="item in formServiceItems" :key="item.item" :label="serviceItemLabel(item)" :value="item.item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预约日期" prop="appointmentDate">
              <el-date-picker
                v-model="bookingForm.appointmentDate"
                class="full-control"
                type="date"
                value-format="yyyy-MM-dd"
                placeholder="请选择日期"
                :picker-options="futureDateOptions"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预约时段" prop="appointmentPeriod">
              <el-select v-model="bookingForm.appointmentPeriod" class="full-control" placeholder="请选择标准时段">
                <el-option v-for="item in options.timeSlots" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="服务房间 / 设备（可选）">
              <el-select v-model="bookingForm.resourceName" class="full-control" clearable placeholder="待甲方配置时可不指定">
                <el-option v-for="item in formResources" :key="item.id" :label="resourceLabel(item)" :value="item.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="服务次数">
              <el-input-number v-model="bookingForm.serviceCount" class="full-control" :min="1" :max="99" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="预约备注">
              <el-input v-model.trim="bookingForm.remark" type="textarea" :rows="3" maxlength="200" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveBooking">{{ editingId ? '保存改期' : '确认预约' }}</el-button>
      </div>
    </el-dialog>

    <el-drawer title="预约详情" :visible.sync="detailVisible" size="520px">
      <div v-if="currentRow" class="detail-panel">
        <div class="detail-title">
          <strong>{{ currentRow.customerName }} · {{ currentRow.serviceItem }}</strong>
          <el-tag :type="statusType(currentRow.serviceStatus)">{{ currentRow.serviceStatus }}</el-tag>
        </div>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="预约单号">{{ currentRow.appointmentNo }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ currentRow.appointmentType }}</el-descriptions-item>
          <el-descriptions-item label="门店">{{ currentRow.store }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ currentRow.customerName }}（{{ currentRow.mobile }}）</el-descriptions-item>
          <el-descriptions-item label="预约时间">{{ currentRow.appointmentDate }} {{ currentRow.appointmentPeriod }}</el-descriptions-item>
          <el-descriptions-item label="负责人员">{{ currentRow.technician }}</el-descriptions-item>
          <el-descriptions-item label="房间 / 设备">{{ currentRow.resourceName || '未指定' }}</el-descriptions-item>
          <el-descriptions-item label="创建信息">{{ currentRow.createdBy }} · {{ currentRow.createdAt }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ currentRow.remark || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getRehabModuleData, getRehabOptions, performRehabModuleAction, saveRehabModuleRecord } from '@/api/erp-rehab'

const APPOINTMENT_TYPES = ['到店参观', '产康服务', '客房服务']
const SERVICE_STATUSES = ['待确认', '已确认', '已到店', '服务中', '已完成', '已取消', '已爽约']

function localDateText(value) {
  const date = value instanceof Date
    ? new Date(value.getTime())
    : value
      ? new Date(`${value}T00:00:00`)
      : new Date()
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 10)
}

function shiftDate(dateText, days) {
  const date = new Date(`${dateText}T00:00:00`)
  date.setDate(date.getDate() + days)
  return localDateText(date)
}

export default {
  name: 'AppointmentWorkbench',
  data() {
    const today = localDateText()
    return {
      loading: false,
      saving: false,
      rows: [],
      activeView: 'list',
      appointmentTypes: APPOINTMENT_TYPES,
      serviceStatuses: SERVICE_STATUSES,
      todayText: today,
      filters: {
        store: '',
        appointmentType: '',
        dateRange: [today, shiftDate(today, 6)],
        serviceStatus: '',
        technician: '',
        keyword: ''
      },
      options: {
        stores: [],
        customers: [],
        staff: [],
        serviceCatalog: [],
        resources: [],
        timeSlots: []
      },
      dialogVisible: false,
      detailVisible: false,
      editingId: null,
      currentRow: null,
      bookingForm: {},
      futureDateOptions: {
        disabledDate(value) {
          const start = new Date()
          start.setHours(0, 0, 0, 0)
          return value.getTime() < start.getTime()
        }
      },
      bookingRules: {
        store: [{ required: true, message: '请选择预约门店', trigger: 'change' }],
        appointmentType: [{ required: true, message: '请选择预约分类', trigger: 'change' }],
        customerName: [{ required: true, message: '请选择当前门店客户', trigger: 'change' }],
        technician: [{ required: true, message: '请选择负责人员', trigger: 'change' }],
        serviceCategory: [{ required: true, message: '请选择服务类别', trigger: 'change' }],
        serviceItem: [{ required: true, message: '请选择预约内容', trigger: 'change' }],
        appointmentDate: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
        appointmentPeriod: [{ required: true, message: '请选择预约时段', trigger: 'change' }]
      }
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    businessStoreId() {
      return String(this.currentStoreId || 'all')
    },
    isAllStores() {
      return this.businessStoreId === 'all'
    },
    storeStaff() {
      return this.options.staff.filter(item => !this.filters.store || item.store === this.filters.store)
    },
    formCustomers() {
      return this.options.customers.filter(item => item.store === this.bookingForm.store)
    },
    formStaff() {
      return this.options.staff.filter(item => (
        item.store === this.bookingForm.store &&
        (!item.appointmentTypes || item.appointmentTypes.includes(this.bookingForm.appointmentType))
      ))
    },
    formCatalog() {
      return this.options.serviceCatalog.filter(item => (
        item.store === this.bookingForm.store &&
        item.appointmentType === this.bookingForm.appointmentType
      ))
    },
    formCategories() {
      return Array.from(new Set(this.formCatalog.map(item => item.category)))
    },
    formServiceItems() {
      return this.formCatalog.filter(item => (
        !this.bookingForm.serviceCategory || item.category === this.bookingForm.serviceCategory
      ))
    },
    formResources() {
      return this.options.resources.filter(item => (
        item.store === this.bookingForm.store &&
        (!item.appointmentTypes || item.appointmentTypes.includes(this.bookingForm.appointmentType))
      ))
    },
    summary() {
      const todayRows = this.rows.filter(item => item.appointmentDate === this.todayText)
      return {
        today: todayRows.length,
        pending: this.rows.filter(item => item.serviceStatus === '待确认').length,
        inProgress: todayRows.filter(item => ['已到店', '服务中'].includes(item.serviceStatus)).length,
        conflicts: this.conflictIds.size
      }
    },
    conflictIds() {
      const ids = new Set()
      const activeRows = this.rows.filter(item => !['已取消', '已爽约'].includes(item.serviceStatus))
      activeRows.forEach((item, index) => {
        activeRows.slice(index + 1).forEach(other => {
          if (
            item.appointmentDate === other.appointmentDate &&
            this.periodsOverlap(item.appointmentPeriod, other.appointmentPeriod) &&
            (
              (item.technician && item.technician === other.technician) ||
              (item.resourceName && item.resourceName === other.resourceName)
            )
          ) {
            ids.add(item.id)
            ids.add(other.id)
          }
        })
      })
      return ids
    },
    weekDays() {
      const start = (this.filters.dateRange && this.filters.dateRange[0]) || this.todayText
      const weekNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
      return Array.from({ length: 7 }).map((_, index) => {
        const date = shiftDate(start, index)
        const value = new Date(`${date}T00:00:00`)
        return {
          date,
          weekday: weekNames[value.getDay()],
          label: date.slice(5).replace('-', '/'),
          items: this.rows
            .filter(item => item.appointmentDate === date)
            .sort((a, b) => a.appointmentPeriod.localeCompare(b.appointmentPeriod))
        }
      })
    }
  },
  watch: {
    '$route.query': {
      handler() {
        if (this.options.stores.length) this.applyRouteStore()
      },
      deep: true
    },
    'filters.store': 'loadData',
    'filters.appointmentType': 'loadData',
    'filters.dateRange': {
      handler: 'loadData',
      deep: true
    },
    'filters.serviceStatus': 'loadData',
    'filters.technician': 'loadData',
    currentStoreId(value, previous) {
      if (String(value) === String(previous)) return
      this.applyRouteStore()
    }
  },
  async created() {
    await this.loadOptions()
    const routeStore = this.resolveRouteStore()
    if (routeStore) {
      this.filters.store = routeStore
    } else if (!this.filters.store && this.options.stores.length) {
      this.filters.store = this.options.stores[0].name
    }
    await this.loadData()
  },
  methods: {
    async loadOptions() {
      const response = await getRehabOptions()
      this.options = {
        stores: response.data.stores || [],
        customers: response.data.customers || [],
        staff: response.data.staff || [],
        serviceCatalog: response.data.serviceCatalog || [],
        resources: response.data.resources || [],
        timeSlots: response.data.timeSlots || []
      }
    },
    resolveRouteStore() {
      if (!this.isAllStores) {
        const currentStore = this.options.stores.find(item => String(item.id) === this.businessStoreId)
        if (currentStore) return currentStore.name
      }
      const requestedStoreId = Number(this.$route.query.storeId)
      if (requestedStoreId) {
        const storeById = this.options.stores.find(item => Number(item.id) === requestedStoreId)
        if (storeById) return storeById.name
      }
      const requestedStoreName = String(this.$route.query.store || '')
      const storeByName = this.options.stores.find(item => item.name === requestedStoreName)
      return storeByName ? storeByName.name : ''
    },
    applyRouteStore() {
      const routeStore = this.resolveRouteStore()
      if (routeStore && routeStore !== this.filters.store) this.filters.store = routeStore
    },
    async loadData() {
      if (!this.filters.store) return
      this.loading = true
      try {
        const response = await getRehabModuleData('service-appointments', {
          store: this.filters.store,
          appointmentType: this.filters.appointmentType,
          dateStart: this.filters.dateRange && this.filters.dateRange[0],
          dateEnd: this.filters.dateRange && this.filters.dateRange[1],
          serviceStatus: this.filters.serviceStatus,
          technician: this.filters.technician,
          keyword: this.filters.keyword
        })
        this.rows = (response.data && response.data.list) || []
      } finally {
        this.loading = false
      }
    },
    resetFilters() {
      const routeStore = this.resolveRouteStore()
      this.filters = {
        store: routeStore || (this.options.stores[0] ? this.options.stores[0].name : ''),
        appointmentType: '',
        dateRange: [this.todayText, shiftDate(this.todayText, 6)],
        serviceStatus: '',
        technician: '',
        keyword: ''
      }
    },
    emptyBookingForm() {
      const store = this.filters.store || (this.options.stores[0] && this.options.stores[0].name) || ''
      return {
        store,
        appointmentType: '产康服务',
        customerName: '',
        technician: '',
        serviceCategory: '',
        serviceItem: '',
        appointmentDate: this.todayText,
        appointmentPeriod: '',
        resourceName: '',
        serviceCount: 1,
        remark: ''
      }
    },
    openBooking(row) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      this.editingId = row ? row.id : null
      this.bookingForm = row
        ? {
          store: row.store,
          appointmentType: row.appointmentType,
          customerName: row.customerName,
          technician: row.technician,
          serviceCategory: row.serviceCategory,
          serviceItem: row.serviceItem,
          appointmentDate: row.appointmentDate,
          appointmentPeriod: row.appointmentPeriod,
          resourceName: row.resourceName || '',
          serviceCount: Number(row.serviceCount || 1),
          remark: row.remark || ''
        }
        : this.emptyBookingForm()
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.bookingForm && this.$refs.bookingForm.clearValidate())
    },
    onFormStoreChange() {
      this.bookingForm.customerName = ''
      this.bookingForm.technician = ''
      this.bookingForm.serviceCategory = ''
      this.bookingForm.serviceItem = ''
      this.bookingForm.resourceName = ''
    },
    onAppointmentTypeChange() {
      this.bookingForm.technician = ''
      this.bookingForm.serviceCategory = ''
      this.bookingForm.serviceItem = ''
      this.bookingForm.resourceName = ''
    },
    saveBooking() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      this.$refs.bookingForm.validate(async valid => {
        if (!valid) return
        this.saving = true
        try {
          await saveRehabModuleRecord('service-appointments', {
            id: this.editingId,
            ...this.bookingForm,
            storeId: this.businessStoreId
          })
          this.dialogVisible = false
          this.$message.success(this.editingId ? '预约已改期并重新校验冲突' : '预约已创建')
          await this.loadData()
        } finally {
          this.saving = false
        }
      })
    },
    rowActions(row) {
      const map = {
        待确认: ['确认预约', '改期', '取消预约'],
        已确认: ['客户到店', '改期', '标记爽约', '取消预约'],
        已到店: ['开始服务', '取消预约'],
        服务中: ['完成服务']
      }
      return map[row.serviceStatus] || []
    },
    handleRowAction(action, row) {
      if (action === '改期') return this.openBooking(row)
      const dangerous = ['取消预约', '标记爽约'].includes(action)
      const execute = async() => {
        await performRehabModuleAction('service-appointments', action, { id: row.id })
        this.$message.success(`${action}成功`)
        await this.loadData()
      }
      if (!dangerous) return execute()
      this.$confirm(`确定要${action}吗？操作会保留审计记录。`, '操作确认', { type: 'warning' })
        .then(execute)
        .catch(() => {})
    },
    openDetail(row) {
      this.currentRow = row
      this.detailVisible = true
    },
    periodsOverlap(first, second) {
      const a = String(first || '').split('-')
      const b = String(second || '').split('-')
      return a.length === 2 && b.length === 2 && a[0] < b[1] && a[1] > b[0]
    },
    staffLabel(item) {
      return `${item.name} · ${item.role}`
    },
    serviceItemLabel(item) {
      return item.duration ? `${item.item} · ${item.duration}分钟` : item.item
    },
    resourceLabel(item) {
      return item.confirmed ? `${item.name} · ${item.type}` : `${item.name} · 待甲方确认`
    },
    statusType(status) {
      if (status === '已完成') return 'success'
      if (['已取消', '已爽约'].includes(status)) return 'danger'
      if (['待确认', '已到店'].includes(status)) return 'warning'
      return ''
    }
  }
}
</script>

<style lang="scss" scoped>
.appointment-workbench {
  min-height: calc(100vh - 84px);
  padding: 20px;
  color: #273449;
  background: #f5f4f1;
}
.page-head,
.filter-panel,
.content-panel {
  border: 1px solid #e6dfd2;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 5px 18px rgba(60, 46, 25, .05);
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-top: 3px solid #a68149;
}
.eyebrow { margin-bottom: 5px; color: #9d7a43; font-size: 12px; font-weight: 700; letter-spacing: .8px; }
.page-head h1 { margin: 0 0 6px; color: #2e2922; font-size: 25px; }
.page-head p { margin: 0; color: #7b746a; font-size: 13px; }
.head-actions { display: flex; gap: 8px; }
.source-alert { margin-top: 12px; border-radius: 9px; }
.filter-panel { margin-top: 12px; padding: 18px 20px 14px; }
.filter-grid { display: grid; grid-template-columns: 1fr 1fr 1.45fr 1fr 1fr 1.35fr; gap: 12px; }
.filter-grid label { min-width: 0; }
.filter-grid label > span { display: block; margin-bottom: 7px; color: #71695d; font-size: 12px; font-weight: 600; }
.filter-grid ::v-deep .el-select,
.filter-grid ::v-deep .el-date-editor { width: 100%; }
.filter-actions { display: flex; align-items: center; justify-content: flex-end; gap: 9px; margin-top: 14px; }
.auto-query { margin-right: auto; color: #8b8479; font-size: 12px; }
.auto-query i { color: #4faa82; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 12px; }
.summary-grid article {
  position: relative;
  padding: 17px 20px;
  overflow: hidden;
  border: 1px solid #e7e1d6;
  border-radius: 11px;
  background: linear-gradient(145deg, #fff 0%, #faf7f1 100%);
}
.summary-grid article::after { position: absolute; top: 0; right: 0; width: 56px; height: 4px; content: ''; background: #b59662; }
.summary-grid article.warning::after { background: #d55e54; }
.summary-grid span,
.summary-grid small { display: block; color: #837b70; font-size: 12px; }
.summary-grid strong { display: block; margin: 6px 0 3px; color: #3a3127; font-size: 26px; }
.content-panel { margin-top: 12px; padding: 18px; }
.content-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.content-head h2 { margin: 0 0 4px; color: #342e27; font-size: 17px; }
.content-head p { margin: 0; color: #8c857b; font-size: 12px; }
.time-cell strong,
.time-cell span { display: block; }
.time-cell span { margin-top: 3px; color: #8a8175; font-size: 12px; }
.week-board { display: grid; grid-template-columns: repeat(7, minmax(145px, 1fr)); gap: 9px; min-height: 420px; overflow-x: auto; }
.day-column { min-width: 145px; border: 1px solid #e8e2d8; border-radius: 9px; background: #faf9f6; }
.day-column.today { border-color: #af8950; box-shadow: inset 0 3px #af8950; }
.day-column > header { display: grid; grid-template-columns: 1fr auto; gap: 2px 8px; padding: 12px; border-bottom: 1px solid #e9e3da; }
.day-column > header span,
.day-column > header em { color: #857d72; font-size: 11px; font-style: normal; }
.day-column > header strong { grid-column: 1 / 2; color: #3e372e; font-size: 16px; }
.day-column > header em { grid-column: 2; grid-row: 1 / 3; align-self: center; }
.day-events { padding: 8px; }
.event-card {
  display: block;
  width: 100%;
  margin-bottom: 8px;
  padding: 10px;
  text-align: left;
  border: 1px solid #e5dccd;
  border-left: 3px solid #b18b52;
  border-radius: 7px;
  background: #fff;
  cursor: pointer;
}
.event-card:hover { border-color: #b18b52; box-shadow: 0 4px 10px rgba(81, 61, 31, .08); }
.event-card span,
.event-card strong,
.event-card small { display: block; }
.event-card span { color: #9a7846; font-size: 11px; }
.event-card strong { margin: 5px 0; color: #383128; font-size: 12px; line-height: 1.45; }
.event-card small { margin-bottom: 7px; color: #837b70; line-height: 1.45; }
.empty-day { padding: 32px 8px; color: #aaa399; text-align: center; font-size: 12px; }
.booking-form { max-height: 62vh; padding-right: 8px; overflow-y: auto; }
.booking-form ::v-deep .el-form-item { margin-bottom: 17px; }
.booking-form ::v-deep .el-form-item__label { padding-bottom: 5px; color: #685f53; line-height: 20px; }
.full-control { width: 100%; }
.detail-panel { padding: 0 20px 26px; }
.detail-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; font-size: 17px; }
::v-deep .el-button--primary { border-color: #9f7a43; background: #9f7a43; }
::v-deep .el-button--primary:hover { border-color: #b28d54; background: #b28d54; }
::v-deep .el-radio-button__orig-radio:checked + .el-radio-button__inner {
  border-color: #9f7a43;
  background: #9f7a43;
  box-shadow: -1px 0 0 0 #9f7a43;
}
::v-deep .el-table th { color: #4e463c; background: #f7f4ee; }
@media (max-width: 1280px) {
  .filter-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 820px) {
  .appointment-workbench { padding: 12px; }
  .page-head,
  .content-head { align-items: flex-start; flex-direction: column; gap: 14px; }
  .filter-grid,
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
