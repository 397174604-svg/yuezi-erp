<template>
  <el-popover
    v-model="open"
    placement="bottom-end"
    width="410"
    trigger="click"
    popper-class="navbar-notification-popper"
    @show="handleShow"
  >
    <div class="notification-panel">
      <div class="notification-head">
        <div>
          <b>通知中心</b>
          <span>{{ unreadCount ? `${unreadCount} 条未读` : '当前没有未读通知' }}</span>
        </div>
        <div class="notification-head__actions">
          <button type="button" title="刷新通知" @click="refreshNotifications">
            <i :class="loading ? 'el-icon-loading' : 'el-icon-refresh'" />
          </button>
          <button v-if="unreadCount" type="button" @click="markAllRead">全部已读</button>
        </div>
      </div>

      <div class="notification-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}<small>{{ tab.count }}</small>
        </button>
      </div>

      <div v-if="loading" class="notification-empty">
        <i class="el-icon-loading" /> 正在读取最新业务提醒
      </div>
      <div v-else-if="visibleNotifications.length" class="notification-list">
        <button
          v-for="item in visibleNotifications"
          :key="item.id"
          type="button"
          class="notification-item"
          :class="{ unread: !isRead(item) }"
          @click="openNotification(item)"
        >
          <span class="notification-icon" :class="item.tone">
            <i :class="item.icon" />
          </span>
          <span class="notification-main">
            <span class="notification-title">
              <b>{{ item.title }}</b>
              <em>{{ item.typeLabel }}</em>
            </span>
            <span class="notification-description">{{ item.description }}</span>
            <span class="notification-meta">
              <small>{{ item.storeName }}</small>
              <time>{{ item.timeText }}</time>
            </span>
          </span>
          <i class="el-icon-arrow-right notification-arrow" />
        </button>
      </div>
      <div v-else class="notification-empty">
        <i class="el-icon-circle-check" />
        <b>当前分类没有待处理通知</b>
        <span>新的审批、预约和客房提醒会自动出现在这里</span>
      </div>

      <button type="button" class="notification-footer" @click="openDashboard">
        查看全部业务待办 <i class="el-icon-arrow-right" />
      </button>
    </div>

    <el-badge
      slot="reference"
      :value="unreadCount"
      :max="99"
      :hidden="!unreadCount"
      class="notification-badge"
    >
      <button
        type="button"
        class="notification-trigger"
        :class="{ active: open }"
        :aria-label="unreadCount ? `通知中心，${unreadCount}条未读` : '通知中心'"
      >
        <i class="el-icon-bell" />
      </button>
    </el-badge>
  </el-popover>
</template>

<script>
import { mapGetters } from 'vuex'
import { getMvpList } from '@/api/erp-mvp'
import { getRehabModuleData } from '@/api/erp-rehab'

function rows(response) {
  return response && response.data && Array.isArray(response.data.list)
    ? response.data.list
    : []
}

function dateKey(value) {
  if (!value) return ''
  if (value instanceof Date) {
    const year = value.getFullYear()
    const month = String(value.getMonth() + 1).padStart(2, '0')
    const day = String(value.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }
  return String(value).slice(0, 10)
}

function compactDate(value) {
  const key = dateKey(value)
  if (!key) return ''
  const parts = key.split('-')
  return `${Number(parts[1])}月${Number(parts[2])}日`
}

function amountText(value) {
  return Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

export default {
  data() {
    return {
      open: false,
      loading: false,
      loaded: false,
      activeTab: 'all',
      notificationRows: [],
      readIds: []
    }
  },
  computed: {
    ...mapGetters(['name', 'currentStoreId', 'roles', 'permissions', 'permission_routes']),
    storageKey() {
      return `erp-notification-read:${this.name || 'anonymous'}`
    },
    storeScopedNotifications() {
      const storeId = String(this.currentStoreId || 'all')
      const result = storeId === 'all'
        ? this.notificationRows
        : this.notificationRows.filter(item => String(item.storeId) === storeId)
      return result.slice().sort((a, b) => (
        a.priority - b.priority ||
        String(b.sortTime || '').localeCompare(String(a.sortTime || ''))
      ))
    },
    unreadCount() {
      return this.storeScopedNotifications.filter(item => !this.isRead(item)).length
    },
    tabs() {
      return [
        { key: 'all', label: '全部', count: this.storeScopedNotifications.length },
        {
          key: 'todo',
          label: '待办',
          count: this.storeScopedNotifications.filter(item => item.kind === 'todo').length
        },
        {
          key: 'reminder',
          label: '提醒',
          count: this.storeScopedNotifications.filter(item => item.kind === 'reminder').length
        }
      ]
    },
    visibleNotifications() {
      const list = this.activeTab === 'all'
        ? this.storeScopedNotifications
        : this.storeScopedNotifications.filter(item => item.kind === this.activeTab)
      return list.slice(0, 12)
    }
  },
  watch: {
    storageKey: {
      immediate: true,
      handler() {
        this.loadReadState()
      }
    }
  },
  mounted() {
    this.loadNotifications()
  },
  methods: {
    handleShow() {
      this.loadNotifications()
    },
    loadReadState() {
      try {
        const saved = JSON.parse(localStorage.getItem(this.storageKey) || '[]')
        this.readIds = Array.isArray(saved) ? saved : []
      } catch (error) {
        this.readIds = []
      }
    },
    saveReadState() {
      localStorage.setItem(this.storageKey, JSON.stringify(this.readIds))
    },
    isRead(item) {
      return this.readIds.includes(item.id)
    },
    markRead(id) {
      if (this.readIds.includes(id)) return
      this.readIds = [...this.readIds, id]
      this.saveReadState()
    },
    markAllRead() {
      this.readIds = Array.from(new Set([
        ...this.readIds,
        ...this.storeScopedNotifications.map(item => item.id)
      ]))
      this.saveReadState()
      this.$message.success('当前门店通知已全部标记为已读')
    },
    async refreshNotifications() {
      this.loaded = false
      await this.loadNotifications()
    },
    async loadNotifications() {
      if (this.loading || this.loaded) return
      this.loading = true
      try {
        const sources = [
          ['customers', ['CUSTOMER.VIEW', 'CUSTOMER.QUERY'], () => getMvpList('customers', { silentError: true })],
          ['contracts', ['SALES.VIEW', 'SALES.QUERY'], () => getMvpList('contracts', { silentError: true })],
          ['receipts', ['FINANCE.VIEW', 'FINANCE.QUERY'], () => getMvpList('receipts', { silentError: true })],
          ['bookings', ['ROOM.VIEW', 'ROOM.QUERY'], () => getMvpList('bookings', { silentError: true })],
          ['appointments', ['RECOVERY.VIEW', 'RECOVERY.QUERY'], () => getRehabModuleData('service-appointments', {}, { silentError: true })]
        ]
        const allowed = sources.filter(([, permissions]) => this.hasAnyPermission(permissions))
        const results = await Promise.all(allowed.map(async([key, , request]) => {
          try {
            return [key, rows(await request())]
          } catch (error) {
            return [key, []]
          }
        }))
        const data = { customers: [], contracts: [], receipts: [], bookings: [], appointments: [] }
        results.forEach(([key, list]) => { data[key] = list })
        this.notificationRows = this.buildNotifications(data)
          .filter(item => this.canAccessRoute(item.route))
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
    hasAnyPermission(required) {
      if ((this.roles || []).includes('SYS_ADMIN')) return true
      return required.some(item => (this.permissions || []).includes(item))
    },
    canAccessRoute(target) {
      const targetPath = typeof target === 'string' ? target : target && target.path
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
    buildNotifications(data) {
      const result = []
      const customersById = data.customers.reduce((map, item) => {
        map[item.id] = item
        return map
      }, {})
      const contractsById = data.contracts.reduce((map, item) => {
        map[item.id] = item
        return map
      }, {})
      const storeIdByName = data.customers.reduce((map, item) => {
        map[item.store_name] = item.store_id
        return map
      }, {})

      data.contracts
        .filter(item => ['已签合同但未审核', '待审核'].includes(item.status))
        .forEach(item => {
          const customer = customersById[item.customer_id] || {}
          result.push({
            id: `contract-${item.id}-${item.status}`,
            kind: 'todo',
            typeLabel: '审批待办',
            title: '合同待审核',
            description: `${item.customer_name} · ${item.contract_no} · ¥${amountText(item.amount)}`,
            storeId: item.store_id,
            storeName: customer.store_name || '所属门店',
            timeText: `${compactDate(item.sign_date)}签订`,
            sortTime: item.sign_date,
            priority: 1,
            tone: 'gold',
            icon: 'el-icon-document-checked',
            route: {
              path: '/customer/signing-workbench',
              query: {
                customerId: String(item.customer_id),
                storeId: String(item.store_id),
                open: 'contracts'
              }
            }
          })
        })

      data.receipts
        .filter(item => item.status === '待审核')
        .forEach(item => {
          const contract = contractsById[item.contract_id] || {}
          result.push({
            id: `receipt-${item.id}-${item.status}`,
            kind: 'todo',
            typeLabel: '财务待办',
            title: '收款待审核',
            description: `${item.customer_name} · ${item.receipt_type} · ¥${amountText(item.amount)}`,
            storeId: item.store_id,
            storeName: item.store_name || '所属门店',
            timeText: `${compactDate(item.received_at)}收款`,
            sortTime: item.received_at,
            priority: 1,
            tone: 'orange',
            icon: 'el-icon-wallet',
            route: {
              path: '/customer/signing-workbench',
              query: {
                customerId: String(contract.customer_id || ''),
                storeId: String(item.store_id),
                open: 'receipts'
              }
            }
          })
        })

      data.bookings
        .filter(item => ['已订房', '待入住'].includes(item.status))
        .forEach(item => {
          result.push({
            id: `checkin-${item.id}-${item.check_in}`,
            kind: 'todo',
            typeLabel: '客房待办',
            title: '客户待入住',
            description: `${item.customer_name} · ${item.room_no} · ${item.status}`,
            storeId: item.store_id,
            storeName: item.store_name || '所属门店',
            timeText: `${compactDate(item.check_in)}入住`,
            sortTime: item.check_in,
            priority: 2,
            tone: 'blue',
            icon: 'el-icon-house',
            route: {
              path: '/room/item-1',
              query: { storeId: String(item.store_id) }
            }
          })
        })

      const today = dateKey(new Date())
      data.appointments
        .filter(item => !['已完成', '已取消', '已爽约'].includes(item.serviceStatus || item.status))
        .forEach(item => {
          const overdue = dateKey(item.appointmentDate) < today
          const storeId = storeIdByName[item.store] || ''
          result.push({
            id: `appointment-${item.id}-${item.serviceStatus}`,
            kind: 'todo',
            typeLabel: overdue ? '超时待办' : '服务待办',
            title: overdue ? '预约已超时待处理' : '服务预约待执行',
            description: `${item.customerName} · ${item.serviceItem} · ${item.technician || '待安排人员'}`,
            storeId,
            storeName: item.store || '所属门店',
            timeText: `${compactDate(item.appointmentDate)} ${item.appointmentPeriod || ''}`,
            sortTime: `${item.appointmentDate || ''} ${item.appointmentPeriod || ''}`,
            priority: overdue ? 1 : 2,
            tone: overdue ? 'red' : 'green',
            icon: overdue ? 'el-icon-warning-outline' : 'el-icon-date',
            route: {
              path: '/schedule/item-1',
              query: { storeId: String(storeId) }
            }
          })
        })

      const todayDate = new Date(`${today}T00:00:00`)
      const futureDate = new Date(todayDate)
      futureDate.setDate(futureDate.getDate() + 30)
      data.customers
        .filter(item => {
          const edc = dateKey(item.edc)
          return edc && edc >= today && edc <= dateKey(futureDate)
        })
        .forEach(item => {
          const edcDate = new Date(`${dateKey(item.edc)}T00:00:00`)
          const days = Math.ceil((edcDate - todayDate) / 86400000)
          result.push({
            id: `edc-${item.id}-${item.edc}`,
            kind: 'reminder',
            typeLabel: '客户提醒',
            title: '预产期临近',
            description: `${item.name} · 预计${compactDate(item.edc)} · 请提前确认入住安排`,
            storeId: item.store_id,
            storeName: item.store_name || '所属门店',
            timeText: days ? `还有 ${days} 天` : '今天',
            sortTime: item.edc,
            priority: days <= 7 ? 1 : 3,
            tone: 'purple',
            icon: 'el-icon-time',
            route: {
              path: '/customer/signing-workbench',
              query: {
                customerId: String(item.id),
                storeId: String(item.store_id),
                open: 'customers'
              }
            }
          })
        })

      return result
    },
    openNotification(item) {
      this.markRead(item.id)
      this.open = false
      if (item.storeId) {
        this.$store.dispatch('app/setCurrentStore', String(item.storeId))
      }
      const navigation = this.$router.push(item.route)
      if (navigation && typeof navigation.catch === 'function') navigation.catch(() => {})
    },
    openDashboard() {
      this.open = false
      const navigation = this.$router.push({
        path: '/dashboard',
        query: { storeId: String(this.currentStoreId || 'all') }
      })
      if (navigation && typeof navigation.catch === 'function') navigation.catch(() => {})
    }
  }
}
</script>

<style lang="scss">
.navbar-notification-popper {
  overflow: hidden;
  padding: 0 !important;
  border-color: #e4dacb !important;
  border-radius: 12px !important;
  box-shadow: 0 18px 48px rgba(61, 47, 27, .18) !important;
}
.notification-panel { color: #342e27; background: #fffdf9; }
.notification-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 17px 18px 13px;
  border-bottom: 1px solid #eee6da;
}
.notification-head > div:first-child { display: flex; flex-direction: column; gap: 4px; }
.notification-head b { font-size: 16px; }
.notification-head span { color: #9a8f7f; font-size: 11px; }
.notification-head__actions { display: flex; align-items: center; gap: 7px; }
.notification-head__actions button {
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  border: 0;
  border-radius: 7px;
  color: #8c6a36;
  background: #f6efe3;
  cursor: pointer;
  font-size: 11px;
}
.notification-head__actions button:hover { background: #ecdfca; }
.notification-tabs {
  display: flex;
  padding: 9px 14px 7px;
  gap: 6px;
  border-bottom: 1px solid #f1ebe2;
}
.notification-tabs button {
  height: 30px;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  color: #807565;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
}
.notification-tabs button small {
  margin-left: 5px;
  padding: 1px 5px;
  border-radius: 10px;
  color: #9b8d78;
  background: #f2ece3;
}
.notification-tabs button.active { color: #765526; background: #f5ead7; font-weight: 600; }
.notification-tabs button.active small { color: #fff; background: #b8945a; }
.notification-list { max-height: 430px; overflow-y: auto; }
.notification-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  width: 100%;
  padding: 13px 14px;
  gap: 11px;
  border: 0;
  border-bottom: 1px solid #f2ece3;
  color: inherit;
  background: #fffdf9;
  cursor: pointer;
  text-align: left;
}
.notification-item:hover { background: #fbf6ee; }
.notification-item.unread::before {
  position: absolute;
  top: 17px;
  left: 5px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #c48c43;
  content: '';
}
.notification-icon {
  display: grid;
  flex: 0 0 34px;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 15px;
}
.notification-icon.gold { color: #8c6a36; background: #f4e7ce; }
.notification-icon.orange { color: #b46b28; background: #f9e8d7; }
.notification-icon.blue { color: #4c7ea8; background: #e4eef6; }
.notification-icon.green { color: #4d8066; background: #e4f0e8; }
.notification-icon.red { color: #bd5d53; background: #f8e5e2; }
.notification-icon.purple { color: #7967a0; background: #eee9f6; }
.notification-main { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 5px; }
.notification-title { display: flex; align-items: center; gap: 7px; }
.notification-title b { overflow: hidden; color: #352f28; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.notification-title em {
  padding: 2px 5px;
  border-radius: 5px;
  color: #94713d;
  background: #f3eadc;
  font-size: 9px;
  font-style: normal;
  white-space: nowrap;
}
.notification-description {
  overflow: hidden;
  color: #746a5d;
  font-size: 11px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notification-meta { display: flex; justify-content: space-between; color: #a2988a; }
.notification-meta small, .notification-meta time { font-size: 10px; }
.notification-arrow { align-self: center; color: #c0b7aa; font-size: 11px; }
.notification-empty {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  color: #9b9184;
  text-align: center;
}
.notification-empty > i { color: #b8945a; font-size: 28px; }
.notification-empty b { color: #5d5449; font-size: 13px; }
.notification-empty span { font-size: 11px; }
.notification-footer {
  width: 100%;
  height: 42px;
  border: 0;
  border-top: 1px solid #eee6da;
  color: #8c6a36;
  background: #faf5ec;
  cursor: pointer;
  font-size: 12px;
}
.notification-footer:hover { background: #f4ead9; }
</style>

<style lang="scss" scoped>
.notification-trigger {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 9px;
  color: #7d7162;
  background: transparent;
  cursor: pointer;
  transition: .2s;
}
.notification-trigger:hover,
.notification-trigger.active {
  border-color: #e2d4be;
  color: #8c6a36;
  background: #f7f0e5;
}
.notification-trigger i { font-size: 17px; }
.notification-badge ::v-deep .el-badge__content {
  top: 3px;
  right: 7px;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  border: 2px solid #fffdf9;
  line-height: 13px;
  background: #b85f50;
  font-size: 9px;
}
</style>
