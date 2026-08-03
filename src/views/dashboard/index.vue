<template>
  <div v-loading="loading" class="dashboard-page">
    <section class="dashboard-section dashboard-toolbar">
      <div class="section-title">
        <i />
        <div>
          <h1>数据看板</h1>
          <p>客户、合同、收款、预约与客房数据</p>
        </div>
      </div>
      <div class="toolbar-actions">
        <el-select v-model="storeId" size="small" @change="handleDashboardStoreChange">
          <el-option v-if="isSystemAdmin" label="全部门店" value="all" />
          <el-option
            v-for="store in raw.stores"
            :key="store.id"
            :label="store.name"
            :value="String(store.id)"
          />
        </el-select>
        <el-radio-group v-model="period" size="small">
          <el-radio-button label="today">今天</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="quarter">本季度</el-radio-button>
          <el-radio-button label="year">本年度</el-radio-button>
        </el-radio-group>
        <el-button size="small" icon="el-icon-refresh" @click="loadData">刷新</el-button>
      </div>
    </section>

    <section class="kpi-grid">
      <router-link
        v-for="item in kpis"
        :key="item.label"
        :to="item.route"
        :class="['kpi-card', item.color]"
      >
        <span>{{ item.label }}</span>
        <b>{{ item.prefix }}{{ item.value }}<small>{{ item.unit }}</small></b>
        <em>{{ periodText }} · {{ item.note }}</em>
        <i :class="item.icon" />
      </router-link>
    </section>

    <section class="dashboard-section stat-strip">
      <router-link v-for="item in roomStats" :key="item.label" :to="item.route">
        <span>{{ item.label }}</span>
        <b :class="item.tone">{{ item.value }}</b>
      </router-link>
    </section>

    <el-row :gutter="14" class="visual-row">
      <el-col :lg="16" :xs="24">
        <section class="dashboard-section trend-panel">
          <div class="section-title compact">
            <i />
            <div><h2>近 7 日经营趋势</h2><p>合同金额与已审核收款金额</p></div>
            <div class="chart-legend"><span><i class="contract" />合同金额</span><span><i class="receipt" />收款金额</span></div>
          </div>
          <div class="trend-chart">
            <div v-for="item in trendRows" :key="item.key" class="trend-column">
              <div class="bar-area">
                <i class="contract-bar" :style="{ height: trendHeight(item.contract) }"><em>{{ shortMoney(item.contract) }}</em></i>
                <i class="receipt-bar" :style="{ height: trendHeight(item.receipt) }"><em>{{ shortMoney(item.receipt) }}</em></i>
              </div>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </section>
      </el-col>
      <el-col :lg="8" :xs="24">
        <section class="dashboard-section room-visual-panel">
          <div class="section-title compact"><i /><div><h2>房态结构</h2><p>当前门店实时客房状态</p></div></div>
          <div class="room-visual-content">
            <div class="occupancy-ring" :style="occupancyRingStyle">
              <div><b>{{ occupancyRate }}%</b><span>入住率</span></div>
            </div>
            <div class="room-legend">
              <router-link v-for="item in roomVisuals" :key="item.label" :to="item.route">
                <span><i :style="{ background: item.color }" />{{ item.label }}</span>
                <b>{{ item.value }}</b>
              </router-link>
            </div>
          </div>
        </section>
      </el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :lg="17" :xs="24">
        <section class="dashboard-section process-panel">
          <div class="section-title compact"><i /><h2>待办流程</h2></div>
          <div class="process-grid">
            <router-link v-for="item in todoItems" :key="item.label" :to="item.route">
              <span>{{ item.label }}</span>
              <b v-if="item.value">{{ item.value }}</b>
              <i class="el-icon-arrow-right" />
            </router-link>
          </div>
        </section>
      </el-col>
      <el-col :lg="7" :xs="24">
        <section class="dashboard-section notice-panel">
          <div class="section-title compact">
            <i />
            <h2>通知公告</h2>
            <router-link to="/system/item-6">更多</router-link>
          </div>
          <div class="notice-row">
            <span>系统菜单已按功能清单优化</span>
            <time>{{ todayText }}</time>
          </div>
          <div class="notice-row">
            <span>预约与智能排房已进入业务使用</span>
            <time>{{ todayText }}</time>
          </div>
        </section>
      </el-col>
    </el-row>

    <section class="dashboard-section warning-panel">
      <div class="section-title compact">
        <i />
        <div><h2>预警平台</h2><p>仅展示当前系统已有数据能够计算的提醒</p></div>
      </div>
      <div class="warning-summary">
        <span>客户预警 <b>{{ warningTotals.customer }}</b></span>
        <span>财务预警 <b>{{ warningTotals.finance }}</b></span>
        <span>客房预警 <b>{{ warningTotals.room }}</b></span>
        <span>服务预警 <b>{{ warningTotals.service }}</b></span>
        <span>仓库预警 <b>{{ warningTotals.inventory }}</b></span>
      </div>
      <div class="warning-grid">
        <router-link v-for="item in warningItems" :key="item.label" :to="item.route">
          <span>{{ item.label }}</span>
          <b :class="item.tone">{{ item.value }}</b>
          <small>{{ item.unit }}</small>
        </router-link>
      </div>
    </section>

    <footer>
      <span>当前范围：{{ currentStoreName }} · {{ periodText }}</span>
      <span>数据更新时间：{{ updatedAt }}</span>
      <span>开派月子会所经营管理系统</span>
    </footer>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getCustomerModuleData } from '@/api/erp-customer'
import { getMvpList, getMvpOptions, getMvpOverview } from '@/api/erp-mvp'
import { getRehabModuleData } from '@/api/erp-rehab'

function responseData(response, fallback) {
  return response && response.data ? response.data : fallback
}

function settle(request, fallback) {
  return request.then(response => responseData(response, fallback)).catch(() => fallback)
}

function rows(payload) {
  return payload && Array.isArray(payload.list) ? payload.list : []
}

function numberValue(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

function dateKey(value) {
  return String(value || '').slice(0, 10)
}

function pad(value) {
  return String(value).padStart(2, '0')
}

function localDate(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export default {
  name: 'Dashboard',
  data() {
    return {
      // Keep the dashboard covered until the authorized store context and the
      // first data snapshot are both ready; restricted accounts must never
      // flash an all-store/zero-room state during login initialization.
      loading: true,
      storeId: String(this.$route.query.storeId || 'all'),
      period: 'month',
      updatedAt: '',
      raw: {
        stores: [],
        overview: {},
        customers: [],
        contracts: [],
        receipts: [],
        rooms: [],
        bookings: [],
        appointments: []
      }
    }
  },
  computed: {
    ...mapGetters(['roles', 'permissions', 'permission_routes', 'storeIds', 'currentStoreId']),
    isSystemAdmin() {
      return (this.roles || []).includes('SYS_ADMIN')
    },
    todayText() {
      return localDate(new Date())
    },
    periodText() {
      return {
        today: '今天',
        week: '近 7 天',
        month: '本月',
        quarter: '本季度',
        year: '本年度'
      }[this.period]
    },
    currentStore() {
      return this.raw.stores.find(item => Number(item.id) === Number(this.storeId))
    },
    currentStoreName() {
      return this.currentStore ? this.currentStore.name : '全部门店'
    },
    scopedCustomers() {
      return this.filterStore(this.raw.customers)
    },
    scopedContracts() {
      return this.filterStore(this.raw.contracts)
    },
    scopedReceipts() {
      return this.filterStore(this.raw.receipts)
    },
    scopedRooms() {
      return this.filterStore(this.raw.rooms)
    },
    scopedBookings() {
      return this.filterStore(this.raw.bookings)
    },
    scopedAppointments() {
      return this.filterStore(this.raw.appointments)
    },
    periodCustomers() {
      return this.scopedCustomers.filter(item => this.inPeriod(item.created_at || item.createdAt))
    },
    periodContracts() {
      return this.scopedContracts.filter(item => this.inPeriod(item.sign_date || item.signDate || item.created_at))
    },
    periodReceipts() {
      return this.scopedReceipts.filter(item => item.status === '已审核' && this.inPeriod(item.received_at || item.receivedAt))
    },
    periodAppointments() {
      return this.scopedAppointments.filter(item => this.inPeriod(item.appointmentDate || item.appointment_date))
    },
    occupiedRooms() {
      return this.scopedRooms.filter(item => ['在住', '入住', '已入住'].includes(item.status)).length
    },
    reservedRooms() {
      return this.scopedRooms.filter(item => ['已预订', '预约', '预订'].includes(item.status)).length
    },
    availableRooms() {
      return this.scopedRooms.filter(item => ['空闲', '可用', '可售'].includes(item.status)).length
    },
    occupancyRate() {
      return this.scopedRooms.length
        ? ((this.occupiedRooms / this.scopedRooms.length) * 100).toFixed(1)
        : '0.0'
    },
    auditedIncome() {
      return this.periodReceipts.reduce((total, item) => total + numberValue(item.amount), 0)
    },
    pendingContracts() {
      return this.scopedContracts.filter(item => ['已签合同但未审核', '待审核'].includes(item.status)).length
    },
    pendingReceipts() {
      return this.scopedReceipts.filter(item => item.status === '待审核').length
    },
    outstandingContracts() {
      return this.scopedContracts.filter(item => numberValue(item.outstanding_amount) > 0)
    },
    outstandingAmount() {
      return this.outstandingContracts.reduce((total, item) => total + numberValue(item.outstanding_amount), 0)
    },
    waitingCheckIn() {
      return this.scopedBookings.filter(item => ['已订房', '待入住'].includes(item.status)).length
    },
    currentStays() {
      return this.scopedBookings.filter(item => item.status === '已入住').length
    },
    pendingAppointments() {
      return this.scopedAppointments.filter(item => !['已完成', '已取消'].includes(item.serviceStatus || item.status)).length
    },
    dueSoonCustomers() {
      const today = new Date()
      const future = new Date(today)
      future.setDate(today.getDate() + 30)
      return this.scopedCustomers.filter(item => {
        const key = dateKey(item.edc)
        return key && key >= localDate(today) && key <= localDate(future)
      }).length
    },
    kpis() {
      return this.authorizedItems([
        { label: '已审核收款（元）', prefix: '¥', value: this.money(this.auditedIncome), unit: '', note: `${this.pendingReceipts} 笔待审核`, icon: 'el-icon-wallet', color: 'pink', route: '/finance/item-1' },
        { label: '新增客户数量', prefix: '', value: this.periodCustomers.length, unit: '人', note: `${this.dueSoonCustomers} 人临近预产期`, icon: 'el-icon-user-solid', color: 'blue', route: '/customer/item-1' },
        { label: '当前入住客房', prefix: '', value: this.occupiedRooms, unit: '间', note: `入住率 ${this.occupancyRate}%`, icon: 'el-icon-house', color: 'orange', route: '/room/item-1' },
        { label: '已签合同数', prefix: '', value: this.periodContracts.length, unit: '份', note: `${this.pendingContracts} 份待审核`, icon: 'el-icon-document-checked', color: 'green', route: '/sales/item-1' }
      ])
    },
    roomStats() {
      return this.authorizedItems([
        { label: '房间总数', value: this.scopedRooms.length, tone: 'blue', route: '/room/item-1' },
        { label: '入住人数', value: this.currentStays, tone: 'dark', route: '/room/item-1' },
        { label: '空房数量', value: this.availableRooms, tone: 'green', route: '/room/item-1' },
        { label: '入住率（%）', value: this.occupancyRate, tone: 'dark', route: '/room/item-1' },
        { label: '已预订房', value: this.reservedRooms, tone: 'orange', route: '/room/item-1' },
        { label: '待入住', value: this.waitingCheckIn, tone: 'pink', route: '/room/item-1' },
        { label: '本期订房', value: this.scopedBookings.filter(item => this.inPeriod(item.check_in)).length, tone: 'blue', route: '/room/item-1' },
        { label: '本期预约', value: this.periodAppointments.length, tone: 'purple', route: '/schedule/item-1' }
      ])
    },
    todoItems() {
      return this.authorizedItems([
        { label: '合同审批', value: this.pendingContracts, route: '/approval/item-1' },
        { label: '收款审批', value: this.pendingReceipts, route: '/finance/item-2' },
        { label: '退款审批', value: 0, route: '/finance/item-3' },
        { label: '服务预约待执行', value: this.pendingAppointments, route: '/schedule/item-1' },
        { label: '待入住办理', value: this.waitingCheckIn, route: '/room/item-1' },
        { label: '采购单审批', value: 0, route: '/warehouse/item-5' },
        { label: '盘点处理', value: 0, route: '/warehouse/item-3' },
        { label: '库存预警', value: 0, route: '/warehouse/item-4' },
        { label: '客户欠款跟进', value: this.outstandingContracts.length, route: '/finance/item-2' }
      ])
    },
    warningTotals() {
      return {
        customer: this.dueSoonCustomers + this.periodCustomers.length,
        finance: this.pendingReceipts + this.outstandingContracts.length,
        room: this.waitingCheckIn + this.reservedRooms,
        service: this.pendingAppointments,
        inventory: 0
      }
    },
    trendRows() {
      const result = []
      for (let offset = 6; offset >= 0; offset -= 1) {
        const day = new Date()
        day.setDate(day.getDate() - offset)
        const key = localDate(day)
        result.push({
          key,
          label: `${day.getMonth() + 1}/${day.getDate()}`,
          contract: this.scopedContracts
            .filter(item => dateKey(item.sign_date || item.signDate || item.created_at) === key)
            .reduce((total, item) => total + numberValue(item.amount), 0),
          receipt: this.scopedReceipts
            .filter(item => item.status === '已审核' && dateKey(item.received_at || item.receivedAt) === key)
            .reduce((total, item) => total + numberValue(item.amount), 0)
        })
      }
      return result
    },
    trendMax() {
      return Math.max(1, ...this.trendRows.map(item => Math.max(item.contract, item.receipt)))
    },
    occupancyRingStyle() {
      const rate = Math.max(0, Math.min(100, Number(this.occupancyRate)))
      return { background: `conic-gradient(#31c69a 0 ${rate}%, #e9edf2 ${rate}% 100%)` }
    },
    roomVisuals() {
      return this.authorizedItems([
        { label: '在住', value: this.occupiedRooms, color: '#31c69a', route: '/room/item-1' },
        { label: '已预订', value: this.reservedRooms, color: '#4a8ef7', route: '/room/item-1' },
        { label: '空闲', value: this.availableRooms, color: '#b8c2cf', route: '/room/item-1' },
        { label: '待入住', value: this.waitingCheckIn, color: '#f2a13a', route: '/room/item-1' }
      ])
    },
    warningItems() {
      return this.authorizedItems([
        { label: '新增客户提醒', value: this.periodCustomers.length, unit: '人', tone: 'green', route: '/customer/item-1' },
        { label: '预产期提醒', value: this.dueSoonCustomers, unit: '人', tone: 'green', route: '/customer/item-1' },
        { label: '合同欠款客户', value: this.outstandingContracts.length, unit: '人', tone: 'orange', route: '/finance/item-2' },
        { label: '合同未收金额', value: `¥${this.money(this.outstandingAmount)}`, unit: '', tone: 'orange', route: '/finance/item-2' },
        { label: '待入住提醒', value: this.waitingCheckIn, unit: '人', tone: 'purple', route: '/room/item-1' },
        { label: '已预订房间', value: this.reservedRooms, unit: '间', tone: 'purple', route: '/room/item-1' },
        { label: '服务预约提醒', value: this.pendingAppointments, unit: '项', tone: 'pink', route: '/schedule/item-1' },
        { label: '物料库存预警', value: 0, unit: '项', tone: 'red', route: '/warehouse/item-4' }
      ])
    }
  },
  watch: {
    '$route.query.storeId'(storeId) {
      const value = this.resolveAuthorizedStoreId(storeId)
      if (value !== this.storeId) this.storeId = value
      if (value !== String(this.currentStoreId || 'all')) {
        this.$store.dispatch('app/setCurrentStore', value)
      }
    }
  },
  async created() {
    try {
      await this.initializeStoreContext()
    } catch (error) {
      // Store initialization must never leave the whole dashboard masked.
      // loadData below can still show the data available to the current role.
    }
    await this.loadData()
  },
  methods: {
    resolveAuthorizedStoreId(candidate) {
      const allowedStoreIds = (this.storeIds || []).map(item => String(item))
      const requested = String(candidate || '')
      if (this.isSystemAdmin) return requested || String(this.currentStoreId || 'all')
      if (requested && allowedStoreIds.includes(requested)) return requested
      const current = String(this.currentStoreId || '')
      if (current && allowedStoreIds.includes(current)) return current
      return allowedStoreIds[0] || requested || 'all'
    },
    async initializeStoreContext() {
      // Resolve the route, global navbar store and local dashboard store before
      // the first request.  Restricted accounts previously rendered once with
      // `all`, then switched to their only store after the navbar watcher ran.
      const storeId = this.resolveAuthorizedStoreId(this.$route.query.storeId)
      this.storeId = storeId
      if (storeId !== String(this.currentStoreId || 'all')) {
        await this.$store.dispatch('app/setCurrentStore', storeId)
      }

      if (String(this.$route.query.storeId || '') !== storeId) {
        const query = { ...this.$route.query, storeId }
        await this.$router.replace({ path: this.$route.path, query }).catch(() => {})
      }
      await this.$nextTick()
    },
    ensureAuthorizedStore() {
      const storeId = this.resolveAuthorizedStoreId(this.storeId)
      if (storeId === this.storeId && storeId === String(this.currentStoreId || 'all')) return
      this.storeId = storeId
      this.$store.dispatch('app/setCurrentStore', storeId)
      const query = { ...this.$route.query, storeId }
      this.$router.replace({ path: this.$route.path, query }).catch(() => {})
    },
    hasAnyPermission(required) {
      if ((this.roles || []).includes('SYS_ADMIN')) return true
      return required.some(item => (this.permissions || []).includes(item))
    },
    canAccessRoute(targetPath) {
      if (!targetPath || targetPath === '/dashboard') return true
      const normalize = value => `/${String(value || '').split('/').filter(Boolean).join('/')}`
      const visit = (routes, parentPath = '') => routes.some(route => {
        const currentPath = String(route.path || '').startsWith('/')
          ? normalize(route.path)
          : normalize(`${parentPath}/${route.path || ''}`)
        if (currentPath === normalize(targetPath)) return true
        return Array.isArray(route.children) && visit(route.children, currentPath)
      })
      return visit(this.permission_routes || [])
    },
    authorizedItems(items) {
      return items.filter(item => this.canAccessRoute(item.route))
    },
    normalizeCustomerAppointment(row) {
      const appointmentAt = row.appointmentAt || row.appointment_at || row.createdAt || ''
      return {
        ...row,
        storeId: row.storeId || row.store_id,
        appointmentDate: String(appointmentAt).slice(0, 10),
        serviceStatus: row.serviceStatus || row.arrivalStatus || row.status || '待确认'
      }
    },
    handleDashboardStoreChange(value) {
      const store = this.raw.stores.find(item => Number(item.id) === Number(value))
      this.$store.dispatch('app/setCurrentStore', String(value))
      const query = { ...this.$route.query, storeId: String(value) }
      if (store) query.store = store.name
      else delete query.store
      this.$router.replace({ path: this.$route.path, query }).catch(() => {})
    },
    async loadData() {
      this.loading = true
      try {
        const silent = { silentError: true }
        const canCustomer = this.hasAnyPermission(['CUSTOMER.VIEW', 'CUSTOMER.QUERY'])
        const canSales = this.hasAnyPermission(['SALES.VIEW', 'SALES.QUERY'])
        const canFinance = this.hasAnyPermission(['FINANCE.VIEW', 'FINANCE.QUERY'])
        const canRoom = this.hasAnyPermission(['ROOM.VIEW', 'ROOM.QUERY'])
        const canRecovery = this.hasAnyPermission(['RECOVERY.VIEW', 'RECOVERY.QUERY'])
        const appointmentRequest = canRecovery
          ? settle(getRehabModuleData('service-appointments', {}, silent), { list: [] })
          : canCustomer
            ? settle(getCustomerModuleData('appointments', {}, silent), { list: [] })
            : Promise.resolve({ list: [] })
        const [options, overview, customers, contracts, receipts, rooms, bookings, appointments] = await Promise.all([
          settle(getMvpOptions(silent), { stores: [] }),
          settle(getMvpOverview(silent), {}),
          canCustomer ? settle(getMvpList('customers', silent), { list: [] }) : Promise.resolve({ list: [] }),
          canSales ? settle(getMvpList('contracts', silent), { list: [] }) : Promise.resolve({ list: [] }),
          canFinance ? settle(getMvpList('receipts', silent), { list: [] }) : Promise.resolve({ list: [] }),
          canRoom ? settle(getMvpList('rooms', silent), { list: [] }) : Promise.resolve({ list: [] }),
          canRoom ? settle(getMvpList('bookings', silent), { list: [] }) : Promise.resolve({ list: [] }),
          appointmentRequest
        ])
        this.raw = {
          stores: Array.isArray(options.stores) ? options.stores : [],
          overview,
          customers: rows(customers),
          contracts: rows(contracts),
          receipts: rows(receipts),
          rooms: rows(rooms),
          bookings: rows(bookings),
          appointments: rows(appointments).map(this.normalizeCustomerAppointment)
        }
        this.ensureAuthorizedStore()
        this.updatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
      } finally {
        this.loading = false
      }
    },
    filterStore(items) {
      if (this.storeId === 'all') return items
      return items.filter(item => {
        const itemStoreId = Number(item.store_id || item.storeId || 0)
        if (itemStoreId) return itemStoreId === Number(this.storeId)
        return [item.store, item.store_name, item.storeName].includes(this.currentStoreName)
      })
    },
    periodStart() {
      const now = new Date()
      const start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      if (this.period === 'week') start.setDate(start.getDate() - 6)
      if (this.period === 'month') start.setDate(1)
      if (this.period === 'quarter') start.setMonth(Math.floor(start.getMonth() / 3) * 3, 1)
      if (this.period === 'year') start.setMonth(0, 1)
      return localDate(start)
    },
    inPeriod(value) {
      const key = dateKey(value)
      return Boolean(key && key >= this.periodStart() && key <= this.todayText)
    },
    money(value) {
      return numberValue(value).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
    },
    shortMoney(value) {
      const number = numberValue(value)
      if (number >= 10000) return `${(number / 10000).toFixed(number % 10000 ? 1 : 0)}万`
      return this.money(number)
    },
    trendHeight(value) {
      if (!numberValue(value)) return '4px'
      return `${Math.max(12, Math.round((numberValue(value) / this.trendMax) * 100))}%`
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: calc(100vh - 84px);
  padding: 20px 22px;
  color: #303846;
  background: #f4f1eb;
}
.dashboard-section {
  margin-bottom: 16px;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #e7dfd2;
  background: #fffdf9;
  box-shadow: 0 10px 28px -24px rgba(74, 55, 26, .42);
}
.dashboard-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-title { display: flex; align-items: center; }
.section-title > i {
  display: block;
  width: 5px;
  height: 26px;
  margin-right: 9px;
  border-radius: 2px;
  background: linear-gradient(180deg, #d6bb85, #8c6a36);
}
.section-title h1, .section-title h2 { margin: 0; color: #202734; font-size: 19px; }
.section-title h1 { font-size: 26px; }
.section-title p { margin: 4px 0 0; color: #8b96a5; font-size: 13px; }
.section-title.compact > i { height: 20px; }
.section-title.compact h2 { font-size: 18px; }
.toolbar-actions { display: flex; align-items: center; gap: 9px; }
.toolbar-actions .el-select { width: 180px; }
.toolbar-actions ::v-deep .el-input__inner,
.toolbar-actions ::v-deep .el-radio-button__inner,
.toolbar-actions .el-button { font-size: 13px; }
.kpi-grid {
  display: grid;
  margin-bottom: 16px;
  gap: 16px;
  grid-template-columns: repeat(4, 1fr);
}
.kpi-card {
  position: relative;
  overflow: hidden;
  min-height: 156px;
  padding: 24px 90px 20px 24px;
  border-radius: 10px;
  color: #fff;
  box-shadow: 0 8px 22px rgba(35, 48, 67, .14);
  transition: transform .2s, box-shadow .2s;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 14px 30px rgba(74, 55, 26, .22); }
.kpi-card.pink { background: linear-gradient(135deg, #d7bd87 0%, #b8945a 52%, #80602f 100%); }
.kpi-card.blue { background: linear-gradient(135deg, #332e27 0%, #5f5547 56%, #85745c 100%); }
.kpi-card.orange { background: linear-gradient(135deg, #9c642f 0%, #b97a3e 52%, #d29b61 100%); }
.kpi-card.green { background: linear-gradient(135deg, #1f5b53 0%, #28766b 54%, #3f9588 100%); }
.kpi-card,
.kpi-card span,
.kpi-card b,
.kpi-card small,
.kpi-card em,
.kpi-card > i { color: #fff !important; }
.kpi-card span { display: block; font-size: 15px; font-weight: 600; }
.kpi-card b { display: block; margin: 24px 0 6px; font-size: 34px; line-height: 1; }
.kpi-card b small { margin-left: 5px; font-size: 13px; }
.kpi-card em { font-size: 12px; font-style: normal; opacity: .94; }
.kpi-card > i { position: absolute; top: 51px; right: 30px; font-size: 52px; opacity: .85; }
.stat-strip { display: grid; padding: 20px 8px; grid-template-columns: repeat(8, 1fr); }
.stat-strip a {
  display: flex;
  align-items: center;
  min-width: 0;
  border-right: 1px solid #e4e7eb;
  flex-direction: column;
  gap: 11px;
}
.stat-strip a:last-child { border-right: 0; }
.stat-strip span { color: #4d5868; font-size: 13px; font-weight: 600; }
.stat-strip b { font-size: 25px; }
.stat-strip b.blue, .warning-grid b.blue { color: #8c6a36; }
.stat-strip b.green, .warning-grid b.green { color: #26b98b; }
.stat-strip b.pink, .warning-grid b.pink { color: #b8945a; }
.stat-strip b.orange, .warning-grid b.orange { color: #ed9a2d; }
.stat-strip b.purple, .warning-grid b.purple { color: #80602f; }
.stat-strip b.red, .warning-grid b.red { color: #e55c63; }
.stat-strip b.dark, .warning-grid b.dark { color: #222b37; }
.visual-row { margin-bottom: 0; }
.trend-panel, .room-visual-panel { min-height: 350px; }
.trend-panel .section-title { position: relative; }
.chart-legend { display: flex; margin-left: auto; gap: 18px; }
.chart-legend span { color: #6f7b8b; font-size: 12px; }
.chart-legend i { display: inline-block; width: 10px; height: 10px; margin-right: 5px; border-radius: 2px; }
.chart-legend i.contract { background: #b8945a; }
.chart-legend i.receipt { background: #28766b; }
.trend-chart {
  display: grid;
  align-items: end;
  height: 260px;
  margin-top: 18px;
  padding: 18px 18px 6px;
  gap: 20px;
  border-radius: 8px;
  background: repeating-linear-gradient(to top, #eee7da 0, #eee7da 1px, transparent 1px, transparent 64px);
  grid-template-columns: repeat(7, 1fr);
}
.trend-column { display: flex; align-items: center; height: 100%; flex-direction: column; justify-content: flex-end; }
.bar-area { display: flex; align-items: flex-end; justify-content: center; width: 100%; height: 210px; gap: 7px; }
.bar-area > i { position: relative; width: 23px; min-height: 4px; border-radius: 5px 5px 0 0; }
.bar-area > i em {
  position: absolute;
  top: -20px;
  left: 50%;
  color: #667384;
  font-size: 10px;
  font-style: normal;
  white-space: nowrap;
  transform: translateX(-50%);
}
.contract-bar { background: linear-gradient(to top, #8c6a36, #d9bf8b); }
.receipt-bar { background: linear-gradient(to top, #1f5b53, #5aa89b); }
.trend-column > span { margin-top: 9px; color: #667384; font-size: 12px; font-weight: 600; }
.room-visual-content { display: flex; align-items: center; justify-content: space-around; min-height: 270px; padding-top: 15px; }
.occupancy-ring {
  width: 174px;
  height: 174px;
  padding: 14px;
  border-radius: 50%;
  box-shadow: 0 10px 28px rgba(49, 198, 154, .18);
}
.occupancy-ring > div {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #fff;
  flex-direction: column;
}
.occupancy-ring b { color: #273343; font-size: 32px; }
.occupancy-ring span { margin-top: 4px; color: #8994a3; font-size: 13px; }
.room-legend { width: 42%; }
.room-legend a { display: flex; align-items: center; padding: 14px 0; border-bottom: 1px solid #edf0f4; }
.room-legend span { flex: 1; color: #5c6878; font-size: 13px; }
.room-legend span i { display: inline-block; width: 10px; height: 10px; margin-right: 8px; border-radius: 50%; }
.room-legend b { color: #273343; font-size: 20px; }
.process-panel, .notice-panel { min-height: 300px; }
.process-grid { display: grid; margin-top: 14px; gap: 8px 12px; grid-template-columns: repeat(3, 1fr); }
.process-grid a {
  display: flex;
  align-items: center;
  min-height: 50px;
  padding: 0 14px;
  border-left: 3px solid #b8945a;
  color: #374151;
  background: #fbf8f1;
  font-size: 14px;
  font-weight: 600;
}
.process-grid a:nth-child(3n+2) { border-color: #35bfa0; background: #f0faf7; }
.process-grid a:nth-child(3n) { border-color: #f4b149; background: #fff8ed; }
.process-grid span { flex: 1; }
.process-grid b {
  min-width: 28px;
  padding: 4px 8px;
  border-radius: 12px;
  color: #fff;
  background: #f39a32;
  text-align: center;
}
.process-grid i { margin-left: 7px; color: #aab3c0; }
.notice-panel .section-title a { margin-left: auto; color: #8c6a36; font-size: 13px; }
.notice-row { display: flex; align-items: center; padding: 22px 4px; border-bottom: 1px solid #edf0f3; font-size: 13px; }
.notice-row span { flex: 1; }
.notice-row time { color: #8994a3; font-size: 11px; }
.warning-panel { min-height: 265px; }
.warning-panel .section-title > div { display: flex; align-items: baseline; gap: 8px; }
.warning-panel .section-title p { margin: 0; }
.warning-summary {
  display: grid;
  margin: 14px 0 0;
  border-bottom: 3px solid #37caaa;
  grid-template-columns: repeat(5, 1fr);
}
.warning-summary span { padding: 11px 12px; color: #526070; font-size: 13px; font-weight: 600; }
.warning-summary span:nth-child(2) { border-color: #e8a632; }
.warning-summary b { margin-left: 4px; font-size: 17px; }
.warning-grid {
  display: grid;
  padding: 6px 0 3px;
  background: #fbf8f1;
  grid-template-columns: repeat(8, 1fr);
}
.warning-grid a {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 104px;
  border-right: 1px solid #e8ebef;
  flex-direction: column;
  gap: 7px;
}
.warning-grid a:last-child { border-right: 0; }
.warning-grid span { color: #697586; font-size: 12px; font-weight: 600; }
.warning-grid b { font-size: 23px; }
.warning-grid small { color: #8f99a6; font-size: 11px; }
footer { display: flex; justify-content: space-between; padding: 7px 3px; color: #7f8a99; font-size: 12px; }
@media (max-width: 1200px) {
  .dashboard-toolbar { align-items: flex-start; flex-direction: column; gap: 12px; }
  .toolbar-actions { width: 100%; flex-wrap: wrap; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .stat-strip { grid-template-columns: repeat(4, 1fr); }
  .stat-strip a { margin: 8px 0; }
  .warning-grid { grid-template-columns: repeat(4, 1fr); }
  .warning-grid a { border-bottom: 1px solid #e8ebef; }
  .trend-chart { gap: 8px; }
  .bar-area > i { width: 16px; }
}
@media (max-width: 768px) {
  .dashboard-page { padding: 10px; }
  .toolbar-actions .el-radio-group { display: none; }
  .kpi-grid { grid-template-columns: 1fr; }
  .stat-strip { grid-template-columns: repeat(2, 1fr); }
  .process-grid { grid-template-columns: 1fr; }
  .warning-summary { grid-template-columns: 1fr; }
  .warning-grid { grid-template-columns: repeat(2, 1fr); }
  .trend-chart { height: 220px; padding-right: 4px; padding-left: 4px; gap: 3px; }
  .bar-area { height: 170px; gap: 2px; }
  .bar-area > i { width: 9px; }
  .bar-area > i em { display: none; }
  .room-visual-content { flex-direction: column; gap: 18px; }
  .room-legend { width: 100%; }
  footer { align-items: center; flex-direction: column; gap: 4px; }
}
</style>
