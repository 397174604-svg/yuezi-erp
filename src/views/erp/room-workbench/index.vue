<template>
  <div class="room-workbench">
    <section class="page-heading">
      <div>
        <div class="eyebrow"><i :class="config.icon" /> 开派月子会所 · 房务运营</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ config.description }}</p>
      </div>
    </section>

    <el-card v-if="visibleActions.length && config.mode !== 'smart-allocation'" shadow="never" class="content-card action-card">
      <div class="business-actions">
        <el-button
          v-for="(action, index) in visibleActions"
          :key="action"
          size="small"
          :type="index === 0 ? 'primary' : action === '删除' ? 'danger' : 'default'"
          :plain="index !== 0"
          :icon="actionIcon(action)"
          @click="handleAction(action)"
        >{{ action }}</el-button>
      </div>
    </el-card>

    <el-card v-if="config.mode === 'occupancy'" shadow="never" class="content-card filter-card trend-filter-card">
      <div class="trend-tip">
        房型占用数是由：包括了入住客户数，订房客户数，维修(占用)房数和合同预住数组成
      </div>
      <div class="trend-query-row">
        <div class="trend-query-item">
          <span class="trend-query-label">门店</span>
          <el-select v-model="filters.store" class="trend-store-select">
            <el-option
              v-for="option in trendStoreOptions"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
        </div>
        <div class="trend-query-item trend-date-item">
          <span class="trend-query-label">预定时间</span>
          <el-date-picker
            v-model="filters.startDate"
            type="date"
            value-format="yyyy-MM-dd"
            placeholder="选择日期"
            class="trend-date-control"
            @change="syncEndDate"
          />
          <el-input-number
            v-model="filters.days"
            :min="1"
            :max="365"
            :controls="false"
            class="trend-day-control"
            @change="syncEndDate"
          />
          <span class="trend-day-unit">天</span>
          <el-date-picker
            v-model="filters.endDate"
            type="date"
            value-format="yyyy-MM-dd"
            placeholder="选择日期"
            class="trend-date-control"
          />
        </div>
      </div>
      <div class="trend-metric-row">
        <span class="trend-metric-label">房型占用数:</span>
        <el-checkbox-group v-model="filters.occupancyTypes" class="trend-metric-checks">
          <el-checkbox
            v-for="option in trendOccupancyOptions"
            :key="option"
            :label="option"
          >{{ option }}</el-checkbox>
        </el-checkbox-group>
        <el-button type="primary" size="small" class="trend-search-button" @click="search">查询</el-button>
      </div>
    </el-card>

    <el-card v-else-if="config.mode !== 'smart-allocation'" shadow="never" class="content-card filter-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>查询条件</h2>
          <p>按门店、房型、楼层和房态查看当前可用情况</p>
        </div>
        <div class="query-actions">
          <el-button type="primary" size="small" icon="el-icon-search" @click="search">查询</el-button>
          <el-button
            v-for="action in visibleQueryActions"
            :key="action"
            size="small"
            icon="el-icon-download"
            @click="handleQueryAction(action)"
          >{{ action }}</el-button>
        </div>
      </div>
      <el-form label-position="top" class="filter-form">
        <el-row :gutter="16">
          <el-col v-for="field in config.filters" :key="field.key" :xl="4" :lg="6" :md="8" :sm="12" :xs="24">
            <el-form-item :label="field.label">
              <el-input
                v-if="field.type === 'input'"
                v-model.trim="filters[field.key]"
                clearable
                :placeholder="field.placeholder || `请输入${field.label}`"
                @keyup.enter.native="search"
              />
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="filters[field.key]"
                :min="1"
                :max="365"
                controls-position="right"
                class="full-control"
                @change="syncEndDate"
              />
              <el-select
                v-else-if="field.type === 'select'"
                v-model="filters[field.key]"
                clearable
                filterable
                :placeholder="field.placeholder || '请选择'"
                class="full-control"
                @change="handleFilterChange(field.key)"
              >
                <el-option v-for="option in fieldOptions(field)" :key="option" :label="option" :value="option" />
              </el-select>
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="filters[field.key]"
                type="date"
                value-format="yyyy-MM-dd"
                placeholder="选择日期"
                class="full-control"
                @change="syncEndDate"
              />
              <el-date-picker
                v-else-if="field.type === 'dateRange'"
                v-model="filters[field.key]"
                type="daterange"
                value-format="yyyy-MM-dd"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                range-separator="至"
                class="full-control"
              />
              <el-checkbox v-else-if="field.type === 'checkbox'" v-model="filters[field.key]">{{ field.label }}</el-checkbox>
              <el-checkbox-group v-else-if="field.type === 'checkboxGroup'" v-model="filters[field.key]" class="occupancy-checks">
                <el-checkbox v-for="option in field.options" :key="option" :label="option">{{ option }}</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <smart-room-allocation
      v-if="config.mode === 'smart-allocation'"
      :config="config"
      :can-book="canUseAction('订房')"
    />

    <template v-else-if="config.mode === 'room-map'">
      <section class="room-legend">
        <span v-for="item in roomLegend" :key="item.label"><i :class="item.status" />{{ item.label }} {{ item.count }}</span>
      </section>
      <section class="room-groups">
        <div v-for="group in roomMapGroups" :key="group.name" class="room-group">
          <div class="group-title"><strong>{{ group.name }}</strong><span>{{ group.rooms.length }} 间</span></div>
          <div class="room-grid">
            <div
              v-for="room in group.rooms"
              :key="room.id"
              :data-room="room.room"
              role="button"
              tabindex="0"
              class="room-card"
              :class="[`is-${room.statusKey}`, { 'is-selected': currentRow && currentRow.id === room.id }]"
              @click="selectRoom(room)"
              @keyup.enter="selectRoom(room)"
            >
              <div class="room-card-head">
                <b>{{ room.room }}</b>
                <el-button type="text" size="mini" @click.stop="openRoomBookingDetails(room)">详情({{ room.detailCount }})</el-button>
              </div>
              <div class="room-card-subtitle">
                <strong>{{ room.roomType }}</strong>
                <span>{{ room.status }}</span>
              </div>
              <div v-if="room.stays && room.stays.length" class="room-stays">
                <div
                  v-for="stay in room.stays"
                  :key="stay.id"
                  role="button"
                  tabindex="0"
                  class="room-stay"
                  @click.stop="openResidentDetails(room, stay)"
                  @keyup.enter.stop="openResidentDetails(room, stay)"
                >
                  <div>
                    <strong>{{ stay.customerName }}</strong>
                    <em>{{ stay.remainingDays }}/{{ stay.totalDays }}</em>
                  </div>
                  <small>{{ stay.startAt }}~{{ stay.endAt }}</small>
                </div>
              </div>
              <div v-else class="room-available">{{ room.availableRange }}</div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <el-card v-else-if="config.mode === 'timeline'" shadow="never" class="content-card timeline-card">
      <div class="timeline-scroll">
        <table class="timeline-table">
          <thead>
            <tr>
              <th class="fixed-store">分店</th>
              <th class="fixed-room">房号</th>
              <th class="fixed-type">类型</th>
              <th v-for="day in timelineDays" :key="day.date">{{ day.day }}<small>{{ day.week }}</small></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in timelineRows" :key="row.id">
              <td class="fixed-store">{{ row.store }}</td>
              <td class="fixed-room">{{ row.room }}</td>
              <td class="fixed-type">{{ row.roomType }}</td>
              <td v-for="(day, index) in timelineDays" :key="day.date">
                <span class="timeline-state" :class="`state-${row.timeline[index].key}`" :title="row.timeline[index].label">{{ row.timeline[index].short }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-card>

    <el-card v-else-if="config.mode === 'occupancy'" shadow="never" class="content-card occupancy-card">
      <room-type-trend-chart :filters="appliedTrendFilters" :rows="rows" />
    </el-card>

    <el-card v-else shadow="never" class="content-card table-card">
      <el-table
        v-loading="loading"
        :data="pagedRows"
        border
        stripe
        height="535"
        highlight-current-row
        @selection-change="selection = $event"
        @row-dblclick="openDetails"
      >
        <el-table-column v-if="visibleActions.length" type="selection" width="45" fixed="left" />
        <el-table-column type="index" label="序号" width="58" fixed="left" :index="tableIndex" />
        <el-table-column
          v-for="column in visibleColumns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :min-width="column.width || 110"
          show-overflow-tooltip
        >
          <template slot-scope="scope">
            <el-tag v-if="column.tag" size="mini" :type="tagType(scope.row[column.key])">{{ scope.row[column.key] }}</el-tag>
            <span v-else-if="column.money" class="money">¥ {{ money(scope.row[column.key]) }}</span>
            <span v-else>{{ scope.row[column.key] }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>已选 {{ selection.length }} 条；显示第 {{ pageStart }}–{{ pageEnd }} 条，共 {{ filteredRows.length }} 条</span>
        <el-pagination
          background
          layout="prev, pager, next, sizes"
          :current-page.sync="pagination.page"
          :page-size.sync="pagination.size"
          :page-sizes="[10, 15, 30, 50, 100]"
          :total="filteredRows.length"
        />
      </div>
    </el-card>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="780px" top="6vh" :close-on-click-modal="false">
      <el-form :model="dialogForm" label-position="top" class="dialog-form">
        <el-row :gutter="18">
          <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
            <el-form-item :label="field.label" :required="field.required">
              <el-input v-if="field.type === 'input'" v-model.trim="dialogForm[field.key]" />
              <el-input-number v-else-if="field.type === 'number'" v-model="dialogForm[field.key]" :min="0" controls-position="right" class="full-control" />
              <el-select v-else-if="field.type === 'select'" v-model="dialogForm[field.key]" filterable clearable placeholder="请选择" class="full-control">
                <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
              </el-select>
              <el-date-picker v-else-if="field.type === 'date'" v-model="dialogForm[field.key]" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" placeholder="选择日期时间" class="full-control" />
              <el-input v-else-if="field.type === 'textarea'" v-model.trim="dialogForm[field.key]" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitDialog">确认提交</el-button>
      </div>
    </el-dialog>

    <el-drawer title="客房业务详情" :visible.sync="drawerVisible" size="560px">
      <div v-if="currentRow" class="detail-drawer">
        <div class="detail-head">
          <strong>{{ recordName(currentRow) }}</strong>
          <el-tag size="small" type="success">实时业务数据</el-tag>
        </div>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item v-for="column in drawerColumns" :key="column.key" :label="column.label">
            <span v-if="column.money">¥ {{ money(currentRow[column.key]) }}</span>
            <span v-else>{{ currentRow[column.key] }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="config.mode === 'room-map' && currentRow.stays && currentRow.stays.length" class="detail-room-stays">
          <h3>入住与订房明细</h3>
          <div v-for="stay in currentRow.stays" :key="stay.id">
            <strong>{{ stay.customerName }}</strong>
            <span>{{ stay.remainingDays }}/{{ stay.totalDays }} 天</span>
            <small>{{ stay.startAt }}~{{ stay.endAt }}</small>
          </div>
        </div>
      </div>
    </el-drawer>

    <room-resident-dialog
      :visible.sync="residentDialogVisible"
      :room="residentRoom"
      :stay="residentStay"
    />

    <room-booking-detail-dialog
      :visible.sync="roomDetailVisible"
      :room="roomDetailRoom"
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getRoomPageConfig, roomTypes } from '@/config/room-pages'
import { canUseRoomAction, visibleRoomActions } from '@/config/room-permissions'
import { getRoomModuleData, performRoomModuleAction, saveRoomModuleRecord } from '@/api/erp-room'
import RoomResidentDialog from './RoomResidentDialog'
import RoomBookingDetailDialog from './RoomBookingDetailDialog'
import RoomTypeTrendChart from './RoomTypeTrendChart'
import SmartRoomAllocation from './SmartRoomAllocation'

const operationBase = [
  { key: 'operator', label: '经办人', type: 'input' },
  { key: 'operatedAt', label: '操作时间', type: 'date' },
  { key: 'remark', label: '操作说明', type: 'textarea', required: true }
]

export default {
  name: 'RoomWorkbench',
  components: { RoomResidentDialog, RoomBookingDetailDialog, RoomTypeTrendChart, SmartRoomAllocation },
  data() {
    return {
      filters: {},
      rows: [],
      selection: [],
      loading: false,
      saving: false,
      pagination: { page: 1, size: 15 },
      dialogVisible: false,
      dialogTitle: '',
      dialogAction: '',
      dialogFields: [],
      dialogForm: {},
      currentRow: null,
      drawerVisible: false,
      residentDialogVisible: false,
      residentRoom: null,
      residentStay: null,
      roomDetailVisible: false,
      roomDetailRoom: null,
      appliedTrendFilters: {}
    }
  },
  computed: {
    ...mapGetters(['permissions', 'roles']),
    pageTitle() {
      return this.$route.meta.title
    },
    configTitle() {
      return this.$route.meta.configTitle || this.pageTitle
    },
    config() {
      return getRoomPageConfig(this.configTitle)
    },
    visibleActions() {
      const actions = this.config.mode === 'room-map'
        ? []
        : this.config.actions
      return visibleRoomActions(
        this.config.key,
        actions,
        this.permissions,
        this.roles
      )
    },
    visibleQueryActions() {
      return visibleRoomActions(
        this.config.key,
        this.config.queryActions || [],
        this.permissions,
        this.roles
      )
    },
    trendStoreOptions() {
      const field = this.config.filters.find(item => item.key === 'store')
      return field ? field.options : []
    },
    trendOccupancyOptions() {
      const field = this.config.filters.find(item => item.key === 'occupancyTypes')
      return field ? field.options : []
    },
    visibleColumns() {
      return (this.config.columns || []).filter(column => !column.hidden)
    },
    drawerColumns() {
      if (this.config.mode === 'room-map') {
        return [
          { key: 'room', label: '房号' }, { key: 'store', label: '门店' }, { key: 'roomType', label: '房型' },
          { key: 'direction', label: '朝向' }, { key: 'floor', label: '楼层' }, { key: 'status', label: '房间状态' },
          { key: 'customerName', label: '当前客户' }, { key: 'availableRange', label: '可用信息' }
        ]
      }
      return this.visibleColumns
    },
    filteredRows() {
      return this.rows.filter(row => {
        return this.config.filters.every(field => {
          const value = this.filters[field.key]
          if (value === '' || value == null || value === false || (Array.isArray(value) && !value.length)) return true
          if (field.type === 'date' || field.type === 'dateRange' || field.type === 'number' || field.type === 'checkbox' || field.type === 'checkboxGroup' || field.key === 'displayType') return true
          return String(row[field.key] == null ? '' : row[field.key]).includes(String(value))
        })
      })
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
    roomLegend() {
      const definitions = [
        { label: '入住', status: 'occupied' }, { label: '预约', status: 'reserved' }, { label: '空闲', status: 'available' },
        { label: '待清洁', status: 'cleaning' }, { label: '维修', status: 'maintenance' }
      ]
      return definitions.map(item => ({ ...item, count: this.filteredRows.filter(room => room.statusKey === item.status).length }))
    },
    roomMapGroups() {
      const displayType = this.filters.displayType || '按楼层'
      const key = displayType === '按房型' ? 'roomType' : 'floor'
      const groups = {}
      this.filteredRows.forEach(room => {
        if (!groups[room[key]]) groups[room[key]] = []
        groups[room[key]].push(room)
      })
      return Object.keys(groups).sort().map(name => ({ name, rooms: groups[name] }))
    },
    timelineDays() {
      const count = Math.min(Number(this.filters.days || 28), 31)
      const start = new Date(this.filters.startDate || new Date())
      return Array.from({ length: count }, (_, index) => {
        const value = new Date(start)
        value.setDate(start.getDate() + index)
        const date = `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
        return { date, day: value.getDate(), week: ['日', '一', '二', '三', '四', '五', '六'][value.getDay()] }
      })
    },
    timelineRows() {
      return this.rows.map(row => ({
        ...row,
        timeline: this.timelineDays.map(day => {
          const booking = (row.bookings || []).find(item => {
            const start = String(item.startAt || '').slice(0, 10)
            const end = String(item.endAt || '').slice(0, 10)
            return start <= day.date && end > day.date
          })
          if (booking) {
            return booking.status === '已入住'
              ? { key: 'occupied', label: '已入住', short: '住' }
              : { key: 'reserved', label: '已预订', short: '订' }
          }
          if (row.status === '维修' || row.status === '脏房') {
            return { key: 'maintenance', label: row.status, short: '占' }
          }
          return { key: 'available', label: '空闲', short: '空' }
        })
      }))
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initialize()
      }
    }
  },
  methods: {
    fieldOptions(field) {
      if (this.config.mode !== 'room-map' || field.key !== 'roomType') return field.options || []
      const store = this.canonicalStoreName(this.filters.store)
      const available = new Set(
        this.rows
          .filter(row => !store || this.canonicalStoreName(row.store) === store)
          .map(row => row.roomType)
          .filter(Boolean)
      )
      return (field.options || []).filter(option => available.has(option))
    },
    async handleFilterChange(key) {
      if (key !== 'store' || this.config.mode !== 'room-map') return
      const roomTypeField = this.config.filters.find(field => field.key === 'roomType')
      if (this.filters.roomType && roomTypeField && !this.fieldOptions(roomTypeField).includes(this.filters.roomType)) {
        this.$set(this.filters, 'roomType', '')
      }
      // The in-page store selector is a real scope switch, not only a local
      // form value.  Keep it in step with the header-driven route scope and
      // immediately reload the matching store's room inventory.
      this.pagination.page = 1
      await this.loadData()
    },
    canUseAction(action) {
      return canUseRoomAction(
        this.config.key,
        action,
        this.permissions,
        this.roles
      )
    },
    initialize() {
      this.filters = this.config.filters.reduce((result, field) => {
        this.$set(result, field.key, field.type === 'checkboxGroup' || field.type === 'dateRange' ? [] : field.type === 'checkbox' ? false : field.type === 'number' ? 1 : '')
        return result
      }, {})
      Object.entries(this.config.defaultFilters || {}).forEach(([key, value]) => this.$set(this.filters, key, Array.isArray(value) ? [...value] : value))
      const routeStore = this.routeStoreName()
      if (routeStore && this.config.filters.some(field => field.key === 'store')) {
        this.$set(this.filters, 'store', routeStore)
      }
      this.pagination = { page: 1, size: 15 }
      this.selection = []
      this.currentRow = null
      this.drawerVisible = false
      this.residentDialogVisible = false
      this.roomDetailVisible = false
      this.appliedTrendFilters = this.config.mode === 'occupancy'
        ? JSON.parse(JSON.stringify(this.filters))
        : {}
      if (this.config.mode === 'smart-allocation') {
        this.rows = []
        this.loading = false
      } else {
        this.loadData()
      }
    },
    async loadData() {
      this.loading = true
      try {
        const response = await getRoomModuleData(this.config.key, this.filters)
        this.rows = (response.data.list || []).map(row => ({
          ...row,
          store: this.canonicalStoreName(row.store),
          contractStore: this.canonicalStoreName(row.contractStore)
        }))
        const storeField = this.config.filters.find(field => field.key === 'store')
        const accessibleStores = [...new Set(this.rows.map(row => row.store).filter(Boolean))]
        accessibleStores.forEach(store => {
          if (storeField && Array.isArray(storeField.options) && !storeField.options.includes(store)) {
            storeField.options.push(store)
          }
        })
        if (
          storeField &&
          this.filters.store &&
          accessibleStores.length &&
          !accessibleStores.includes(this.canonicalStoreName(this.filters.store))
        ) {
          this.$set(this.filters, 'store', accessibleStores[0])
        }
      } finally {
        this.loading = false
      }
    },
    canonicalStoreName(name) {
      const value = String(name || '')
      if (!value) return ''
      if (value.includes('黄河路')) return '黄河路轻奢店'
      if (value.includes('中心广场') || value.includes('建设路')) return '中心广场旗舰店'
      return value
    },
    routeStoreName() {
      const storeId = Number(this.$route.query.storeId)
      if (storeId === 1) return '中心广场旗舰店'
      if (storeId === 2) return '黄河路轻奢店'
      return this.canonicalStoreName(this.$route.query.store)
    },
    syncEndDate() {
      if (!this.filters.startDate || !this.filters.days || this.filters.endDate === undefined) return
      const end = new Date(this.filters.startDate)
      end.setDate(end.getDate() + Number(this.filters.days))
      this.$set(this.filters, 'endDate', `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, '0')}-${String(end.getDate()).padStart(2, '0')}`)
    },
    async search() {
      this.pagination.page = 1
      if (this.config.mode === 'occupancy') {
        this.appliedTrendFilters = JSON.parse(JSON.stringify(this.filters))
      }
      await this.loadData()
    },
    handleQueryAction(action) {
      if (action === '导出') this.exportRows()
    },
    handleAction(action) {
      if (action === '导出') return this.exportRows()
      if (action === '打印') {
        if (!this.requireOne()) return
        window.print()
        return
      }
      if (this.config.mode === 'room-map') return this.handleRoomMapAction(action)
      if (/添加|订房/.test(action)) return this.openDialog(action, this.config.formFields || [], null)
      if (action === '编辑') {
        const row = this.requireOne()
        if (row) return this.openDialog(action, this.config.formFields || [], row)
        return
      }
      if (action === '删除') return this.removeRows()
      if (action === '审核') return this.openDialog(action, this.config.auditFields || operationBase, this.requireOne())
      if (action === '反审核') return this.executeDirect(action, this.requireOne())
      return this.openDialog(action, this.operationFields(action), this.requireOne())
    },
    handleRoomMapAction(action) {
      const bookingActions = ['订房', '房型订房', '跨店订房']
      if (bookingActions.includes(action)) {
        const fields = action === '跨店订房'
          ? [
            { key: 'customerName', label: '客户姓名', type: 'input', required: true },
            { key: 'sourceStore', label: '客户当前门店', type: 'select', options: ['中心广场旗舰店', '黄河路轻奢店'], required: true },
            { key: 'store', label: '订房门店', type: 'select', options: ['中心广场旗舰店', '黄河路轻奢店'], required: true },
            { key: 'room', label: '房间号', type: 'input' },
            { key: 'roomType', label: '房型', type: 'select', options: roomTypes, required: true },
            { key: 'plannedCheckInAt', label: '预住日期', type: 'date', required: true },
            { key: 'plannedCheckOutAt', label: '预离开日期', type: 'date', required: true },
            { key: 'remark', label: '备注', type: 'textarea' }
          ]
          : this.config.formFields
        return this.openDialog(action, fields, this.currentRow)
      }
      return this.openDialog(action, this.operationFields(action), this.currentRow)
    },
    operationFields(action) {
      if (action === '商品销售') {
        return [
          { key: 'customerName', label: '客户姓名', type: 'input', required: true },
          { key: 'room', label: '房间号', type: 'input' },
          { key: 'saleType', label: '销售类型', type: 'select', options: ['商品销售', '客房商品销售'], required: true },
          { key: 'productName', label: '商品名称', type: 'input', required: true },
          { key: 'quantity', label: '数量', type: 'number', required: true },
          { key: 'remark', label: '备注', type: 'textarea' }
        ]
      }
      if (action === '入住') {
        return [
          { key: 'customerName', label: '入住客户', type: 'input', required: true },
          { key: 'room', label: '房间号', type: 'input', required: true },
          { key: 'checkInAt', label: '入住时间', type: 'date', required: true },
          { key: 'plannedCheckOutAt', label: '预计离开时间', type: 'date', required: true },
          { key: 'plannedDays', label: '入住天数', type: 'number', required: true },
          { key: 'remark', label: '入住说明', type: 'textarea' }
        ]
      }
      if (action === '续住') {
        return [
          { key: 'extensionType', label: '续住类型', type: 'select', options: ['月子续住', '到家续住', '外出续住', '退房续住'], required: true },
          { key: 'extensionDays', label: '续住天数', type: 'number', required: true },
          { key: 'startAt', label: '续住开始日期', type: 'date', required: true },
          { key: 'endAt', label: '续住结束日期', type: 'date', required: true },
          { key: 'extensionAmount', label: '续住金额', type: 'number' },
          { key: 'remark', label: '续住说明', type: 'textarea' }
        ]
      }
      if (action === '换房') {
        return [
          { key: 'targetRoom', label: '换房房间', type: 'input', required: true },
          { key: 'changedAt', label: '换房时间', type: 'date', required: true },
          { key: 'reason', label: '换房事由', type: 'textarea', required: true }
        ]
      }
      if (action === '跨店换房') {
        return [
          { key: 'targetStore', label: '换入门店', type: 'select', options: ['中心广场旗舰店', '黄河路轻奢店'], required: true },
          { key: 'targetRoom', label: '换入房间', type: 'input', required: true },
          { key: 'changedAt', label: '换房时间', type: 'date', required: true },
          { key: 'reason', label: '换房事由', type: 'textarea', required: true }
        ]
      }
      if (action === '退房') {
        return [
          { key: 'checkOutAt', label: '退房时间', type: 'date', required: true },
          { key: 'roomStatus', label: '退房后房态', type: 'select', options: ['脏房', '空闲', '维修'], required: true },
          { key: 'reason', label: '退房说明', type: 'textarea', required: true }
        ]
      }
      if (action === '结账') {
        return [
          { key: 'receivableAmount', label: '应收金额', type: 'number', required: true },
          { key: 'receivedAmount', label: '已收金额', type: 'number' },
          { key: 'settlementMethod', label: '结账方式', type: 'select', options: ['现金', '银行卡', '微信', '支付宝', '其他'], required: true },
          { key: 'settledAt', label: '结账时间', type: 'date', required: true },
          { key: 'remark', label: '结账说明', type: 'textarea' }
        ]
      }
      if (action === '入住通知单') {
        return [
          { key: 'customerName', label: '客户姓名', type: 'input', required: true },
          { key: 'room', label: '房间号', type: 'input', required: true },
          { key: 'checkInAt', label: '入住时间', type: 'date', required: true },
          { key: 'noticeDepartment', label: '通知部门', type: 'input', required: true },
          { key: 'noticeRemark', label: '通知内容', type: 'textarea' }
        ]
      }
      if (action === '客房服务申请' || action === '服务预约') {
        return [
          { key: 'customerName', label: '申请客户', type: 'input', required: true },
          { key: 'room', label: '房间号', type: 'input', required: true },
          { key: 'serviceType', label: '服务类型', type: 'select', options: ['打扫房间', '擦身服务', '设置员工房'], required: true },
          { key: 'serviceAt', label: action === '服务预约' ? '预约时间' : '申请时间', type: 'date', required: true },
          { key: 'remark', label: '服务说明', type: 'textarea' }
        ]
      }
      if (action === '维修/脏房') {
        return [
          { key: 'room', label: '房间号', type: 'input', required: true },
          { key: 'targetStatus', label: '设置房态', type: 'select', options: ['维修', '脏房', '空闲'], required: true },
          { key: 'operatedAt', label: '设置时间', type: 'date', required: true },
          { key: 'remark', label: '原因说明', type: 'textarea', required: true }
        ]
      }
      if (/退订/.test(action)) {
        return [
          { key: 'settlement', label: '结账方式', type: 'select', options: ['直接退订', '退订并结账'], required: true },
          { key: 'refundAmount', label: '退款金额', type: 'number' },
          { key: 'reason', label: '退订原因', type: 'textarea', required: true }
        ]
      }
      if (action === '物品发放') {
        return [
          { key: 'giftItems', label: '发放物品', type: 'textarea', required: true },
          { key: 'issuedAt', label: '发放时间', type: 'date', required: true },
          { key: 'issuer', label: '发放人', type: 'input' },
          { key: 'remark', label: '备注', type: 'textarea' }
        ]
      }
      if (action === '确定已返回') {
        return [
          { key: 'returnedAt', label: '返回时间', type: 'date', required: true },
          { key: 'receiver', label: '确认人', type: 'input' },
          { key: 'remark', label: '返回说明', type: 'textarea' }
        ]
      }
      if (action === '确认签收') {
        return [
          { key: 'signedAt', label: '签收时间', type: 'date', required: true },
          { key: 'signer', label: '签收人', type: 'input', required: true },
          { key: 'remark', label: '签收说明', type: 'textarea' }
        ]
      }
      return operationBase
    },
    requireOne() {
      const row = this.selection[0]
      if (!row) this.$message.warning('请先选择一条客房业务记录')
      return row
    },
    openDialog(action, fields, row) {
      if (!fields || !fields.length || (row === undefined)) return
      this.dialogAction = action
      this.dialogTitle = action
      this.dialogFields = fields
      this.currentRow = row
      this.dialogForm = fields.reduce((result, field) => {
        const value = row && row[field.key] !== undefined ? row[field.key] : field.type === 'number' ? 0 : ''
        this.$set(result, field.key, value)
        return result
      }, {})
      this.dialogVisible = true
    },
    async submitDialog() {
      const missing = this.dialogFields.filter(field => field.required && !this.dialogForm[field.key])
      if (missing.length) return this.$message.warning(`请填写：${missing.map(field => field.label).join('、')}`)
      this.saving = true
      try {
        if (/添加|订房|编辑/.test(this.dialogAction)) {
          await saveRoomModuleRecord(this.config.key, {
            id: this.currentRow && this.currentRow.id,
            roomId: this.config.mode === 'room-map' && this.currentRow ? this.currentRow.id : undefined,
            bookingId: this.currentRow && this.currentRow.bookingId,
            _action: this.dialogAction,
            ...this.dialogForm
          })
        } else {
          await performRoomModuleAction(this.config.key, this.dialogAction, {
            id: this.currentRow && this.currentRow.id,
            roomId: this.config.mode === 'room-map' && this.currentRow ? this.currentRow.id : undefined,
            bookingId: this.currentRow && this.currentRow.bookingId,
            ...this.dialogForm
          })
        }
        await this.loadData()
        this.dialogVisible = false
        this.$message.success(`${this.dialogAction}已完成并写入客房操作轨迹`)
      } finally {
        this.saving = false
      }
    },
    async executeDirect(action, row) {
      if (!row) return
      const rowId = row.id
      await performRoomModuleAction(this.config.key, action, {
        id: rowId,
        bookingId: row.bookingId
      })
      await this.loadData()
      this.$message.success(`${action}已完成`)
    },
    async removeRows() {
      if (!this.selection.length) return this.$message.warning('请先选择要删除的记录')
      try {
        await this.$confirm(`确认删除选中的 ${this.selection.length} 条记录吗？`, '删除确认', { type: 'warning' })
        await performRoomModuleAction(this.config.key, '删除', { ids: this.selection.map(row => row.id) })
        await this.loadData()
        this.selection = []
        this.$message.success('记录已删除')
      } catch (error) {
        if (error !== 'cancel') this.$message.error('删除未完成')
      }
    },
    openDetails(row) {
      this.currentRow = row
      this.drawerVisible = true
    },
    openResidentDetails(room, stay) {
      this.currentRow = room
      this.residentRoom = room
      this.residentStay = stay
      this.residentDialogVisible = true
    },
    openRoomBookingDetails(room) {
      this.currentRow = room
      this.roomDetailRoom = room
      this.roomDetailVisible = true
    },
    selectRoom(row) {
      this.currentRow = row
    },
    exportRows() {
      const columns = this.config.mode === 'timeline'
        ? [{ key: 'store', label: '分店' }, { key: 'room', label: '房号' }, { key: 'roomType', label: '类型' }]
        : this.visibleColumns
      const rows = this.config.mode === 'timeline' ? this.timelineRows : this.filteredRows
      const headers = columns.map(column => column.label)
      const body = rows.map(row => columns.map(column => `"${String(row[column.key] == null ? '' : row[column.key]).replace(/"/g, '""')}"`).join(','))
      const csv = `\uFEFF${headers.join(',')}\n${body.join('\n')}`
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${Date.now()}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${rows.length} 条当前查询记录`)
    },
    actionIcon(action) {
      if (/添加|订房/.test(action)) return 'el-icon-plus'
      if (/商品销售/.test(action)) return 'el-icon-shopping-cart-full'
      if (/入住通知单/.test(action)) return 'el-icon-document'
      if (/客房服务|服务预约/.test(action)) return 'el-icon-service'
      if (/结账/.test(action)) return 'el-icon-wallet'
      if (/退房/.test(action)) return 'el-icon-switch-button'
      if (/维修|脏房/.test(action)) return 'el-icon-warning-outline'
      if (/审核|确认|完成/.test(action)) return 'el-icon-circle-check'
      if (/编辑|续住|换房/.test(action)) return 'el-icon-edit'
      if (/删除|退订|取消/.test(action)) return 'el-icon-delete'
      if (/导出/.test(action)) return 'el-icon-download'
      if (/打印/.test(action)) return 'el-icon-printer'
      if (/反审核/.test(action)) return 'el-icon-refresh-left'
      if (/发放/.test(action)) return 'el-icon-present'
      return 'el-icon-setting'
    },
    tagType(value) {
      if (/通过|已审核|已完成|已确认|已返回|已签收|已赠送|入住|正常|已还/.test(value)) return 'success'
      if (/删除|取消|不通过|维修|退订/.test(value)) return 'danger'
      if (/待|未|预约|清洁/.test(value)) return 'warning'
      return 'info'
    },
    recordName(row) {
      return row.room || row.customerName || row.contractName || row.id
    },
    money(value) {
      return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
    },
    tableIndex(index) {
      return (this.pagination.page - 1) * this.pagination.size + index + 1
    }
  }
}
</script>

<style lang="scss" scoped>
.room-workbench { min-height: calc(100vh - 84px); padding: 22px; color: #26354c; background: #f3f6fa; }
.page-heading { padding: 26px 30px; border-radius: 16px; color: #fff; background: linear-gradient(125deg, #28241e 0%, #5f4b2d 56%, #a68045 100%); box-shadow: 0 14px 34px rgba(74, 55, 26, .2); }
.eyebrow { margin-bottom: 9px; color: #f3dfb7; font-size: 13px; font-weight: 700; letter-spacing: .7px; }
.page-heading h1 { margin: 0 0 9px; font-size: 27px; }
.page-heading p { max-width: 820px; margin: 0; color: #f7efe0; font-size: 14px; line-height: 1.7; }
.content-card { margin-top: 16px; border: 0; border-radius: 12px; }
.action-card ::v-deep .el-card__body { padding: 14px 18px; }
.business-actions, .query-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.business-actions .el-button + .el-button, .query-actions .el-button + .el-button { margin-left: 0; }
.card-heading { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.card-heading h2 { margin: 0 0 4px; font-size: 16px; }
.card-heading p { margin: 0; color: #8a97a8; font-size: 12px; }
.filter-form { margin-bottom: -12px; }
.filter-form ::v-deep .el-form-item { margin-bottom: 16px; }
.filter-form ::v-deep .el-form-item__label, .dialog-form ::v-deep .el-form-item__label { padding-bottom: 5px; color: #607087; font-size: 12px; line-height: 18px; }
.full-control { width: 100%; }
.occupancy-checks { display: flex; flex-wrap: wrap; gap: 3px 12px; }
.occupancy-checks ::v-deep .el-checkbox { margin-right: 0; }
.trend-filter-card ::v-deep .el-card__body { padding: 14px 18px 16px; }
.trend-tip { margin-bottom: 13px; color: #f00; font-size: 12px; }
.trend-query-row { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 24px; }
.trend-query-item, .trend-date-item, .trend-metric-row { display: flex; align-items: center; }
.trend-query-label { flex: 0 0 auto; margin-right: 8px; color: #4d5d73; font-size: 13px; }
.trend-store-select { width: 188px; }
.trend-date-control { width: 142px; }
.trend-day-control { width: 58px; margin-left: 7px; }
.trend-day-unit { margin: 0 7px 0 4px; color: #4d5d73; font-size: 13px; }
.trend-metric-row { min-width: 780px; margin-top: 12px; overflow-x: auto; white-space: nowrap; }
.trend-metric-label { flex: 0 0 auto; margin-right: 12px; color: #4d5d73; font-size: 13px; }
.trend-metric-checks { display: flex; flex: 0 0 auto; align-items: center; flex-wrap: nowrap; gap: 0 22px; }
.trend-metric-checks ::v-deep .el-checkbox { margin-right: 0; }
.trend-search-button { flex: 0 0 auto; margin-left: 24px; }
.table-card ::v-deep .el-card__body { padding-top: 16px; }
.table-card ::v-deep .el-table th { color: #43536a; background: #eef8f6; }
.money { color: #d05f45; font-weight: 700; }
.pagination-row { display: flex; justify-content: space-between; align-items: center; padding-top: 18px; color: #8491a2; font-size: 12px; }
.room-legend { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 16px; padding: 13px 18px; border-radius: 10px; background: #fff; color: #677489; font-size: 12px; }
.room-legend i { display: inline-block; width: 9px; height: 9px; margin-right: 6px; border-radius: 50%; }
.room-legend .occupied { background: #45b8ac; }.room-legend .reserved { background: #6f8ff7; }.room-legend .available { background: #cbd5df; }.room-legend .cleaning { background: #f5ba35; }.room-legend .maintenance { background: #ef6b6b; }
.room-groups { display: flex; flex-direction: column; gap: 14px; margin-top: 16px; }
.room-group { padding: 18px; border-radius: 12px; background: #fff; box-shadow: 0 2px 12px rgba(27, 45, 75, .055); }
.group-title { display: flex; justify-content: space-between; margin-bottom: 14px; }.group-title span { color: #96a1af; font-size: 12px; }
.room-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(235px, 1fr)); gap: 10px; }
.room-card { min-height: 150px; padding: 12px; border: 1px solid #e4e9ef; border-left: 4px solid #cbd5df; border-radius: 8px; color: #344257; background: #f8fafc; cursor: pointer; text-align: left; transition: .2s; }
.room-card:hover { box-shadow: 0 6px 18px rgba(27, 45, 75, .1); transform: translateY(-2px); }
.room-card.is-selected { outline: 2px solid #237d72; box-shadow: 0 0 0 3px rgba(35, 125, 114, .12); }
.room-card-head, .room-card-subtitle, .room-stay > div { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.room-card-head b { color: #26354c; font-size: 18px; }
.room-card-head ::v-deep .el-button { padding: 0; font-size: 12px; }
.room-card-subtitle { margin-top: 7px; font-size: 12px; }.room-card-subtitle span { color: #66758a; }
.room-stays { margin-top: 10px; border-top: 1px dashed rgba(80, 102, 127, .22); }
.room-stay { padding-top: 8px; border-radius: 5px; cursor: pointer; transition: .16s; }.room-stay:hover { padding-right: 5px; padding-left: 5px; background: rgba(255, 255, 255, .72); }
.room-stay strong { font-size: 12px; }.room-stay em { color: #237d72; font-size: 12px; font-style: normal; font-weight: 700; }
.room-stay small { display: block; margin-top: 3px; color: #7f8b9b; font-size: 11px; }
.room-available { margin-top: 15px; color: #7f8b9b; font-size: 12px; }
.room-card.is-occupied { border-left-color: #45b8ac; background: #f0fbf9; }.room-card.is-reserved { border-left-color: #6f8ff7; background: #f2f4ff; }.room-card.is-cleaning { border-left-color: #f5ba35; background: #fff9eb; }.room-card.is-maintenance { border-left-color: #ef6b6b; background: #fff3f3; }
.timeline-card ::v-deep .el-card__body { padding: 0; overflow: hidden; }
.timeline-scroll { overflow: auto; }
.timeline-table { min-width: 1750px; width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11px; }
.timeline-table th, .timeline-table td { min-width: 44px; height: 42px; padding: 5px; border-right: 1px solid #edf0f4; border-bottom: 1px solid #edf0f4; background: #fff; text-align: center; }
.timeline-table th { position: sticky; top: 0; z-index: 3; color: #506176; background: #eef8f6; }.timeline-table th small { display: block; color: #97a3b1; }
.timeline-table .fixed-store, .timeline-table .fixed-room, .timeline-table .fixed-type { position: sticky; z-index: 2; }
.timeline-table .fixed-store { left: 0; min-width: 145px; }.timeline-table .fixed-room { left: 145px; min-width: 70px; }.timeline-table .fixed-type { left: 215px; min-width: 120px; }
.timeline-table th.fixed-store, .timeline-table th.fixed-room, .timeline-table th.fixed-type { z-index: 5; }
.timeline-state { display: grid; place-items: center; width: 26px; height: 26px; margin: auto; border-radius: 5px; color: #fff; }.state-occupied { background: #45b8ac; }.state-reserved { background: #6f8ff7; }.state-available { color: #8a97a8; background: #edf1f5; }
.occupancy-card ::v-deep .el-card__body { padding: 14px 18px 8px; }
.dialog-alert { margin-bottom: 18px; }.dialog-form { max-height: 56vh; padding-right: 10px; overflow-y: auto; }
.detail-drawer { padding: 0 22px 30px; }.detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; font-size: 18px; }
.detail-room-stays { margin-top: 18px; }.detail-room-stays h3 { margin: 0 0 10px; font-size: 15px; }
.detail-room-stays > div { display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; padding: 11px 12px; border: 1px solid #e7ecef; border-radius: 8px; background: #f8fafc; }
.detail-room-stays > div + div { margin-top: 8px; }.detail-room-stays small { grid-column: 1 / -1; color: #7f8b9b; }
@media (max-width: 1200px) { .room-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 760px) {
  .room-workbench { padding: 12px; }.card-heading, .pagination-row { align-items: flex-start; flex-direction: column; }
  .room-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
