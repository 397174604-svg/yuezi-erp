<template>
  <div class="smart-allocation">
    <el-card shadow="never" class="smart-toolbar-card">
      <el-button
        v-if="canBook"
        type="text"
        icon="el-icon-house"
        class="book-action"
        @click="openBooking"
      >订房</el-button>
    </el-card>

    <el-card shadow="never" class="smart-query-card">
      <div class="smart-query-row">
        <div class="smart-query-item">
          <span>分店</span>
          <el-select v-model="filters.store" class="store-control" @change="handleStoreChange">
            <el-option v-for="store in storeOptions" :key="store" :label="store" :value="store" />
          </el-select>
        </div>
        <div class="smart-query-item smart-package-item">
          <span>入住套餐</span>
          <el-select
            v-model="filters.packageNo"
            filterable
            placeholder="请选择本店套餐"
            class="package-control"
            @change="handlePackageChange"
          >
            <el-option
              v-for="item in packageOptions"
              :key="`${item.packageNo}-${item.days}`"
              :label="`${item.packageName} · ${item.days}天`"
              :value="item.packageNo"
            />
          </el-select>
        </div>
        <div class="smart-query-item smart-date-item">
          <span>入住日期</span>
          <el-date-picker
            v-model="filters.startDate"
            type="date"
            value-format="yyyy-MM-dd"
            placeholder="入住时间"
            class="date-control"
            :picker-options="futureDateOptions"
            @change="syncEndFromDays"
          />
          <el-input
            v-model="filters.days"
            maxlength="3"
            class="day-control"
            :disabled="Boolean(filters.packageNo)"
            @input="normalizeDays"
            @change="syncEndFromDays"
          />
          <label>天</label>
          <el-date-picker
            v-model="filters.endDate"
            type="date"
            value-format="yyyy-MM-dd"
            placeholder="退房时间"
            class="date-control"
            :picker-options="futureDateOptions"
            :disabled="Boolean(filters.packageNo)"
            @change="syncDaysFromEnd"
          />
        </div>
        <div class="smart-query-item">
          <span>房型（可选）</span>
          <el-select v-model="filters.roomType" clearable placeholder="全部房型" class="type-control">
            <el-option
              v-for="roomType in roomTypeOptions"
              :key="roomType"
              :label="roomTypeOptionLabel(roomType)"
              :value="roomType"
            />
          </el-select>
        </div>
        <div class="smart-query-item">
          <span>楼层</span>
          <el-select v-model="filters.floor" clearable placeholder="全部楼层" class="floor-control">
            <el-option v-for="floor in floorOptions" :key="floor" :label="`${floor} 楼`" :value="String(floor)" />
          </el-select>
        </div>
        <el-button type="primary" size="small" class="query-button" @click="search">查询</el-button>
      </div>
    </el-card>

    <div class="operational-strip">
      <strong>{{ appliedFilters.store || filters.store }}</strong>
      <span>{{ allocationScopeText }}</span>
      <span>候选 {{ conflictSummary[0].value }} 间</span>
      <span class="is-success">连续可住 {{ conflictSummary[1].value }} 间</span>
      <span v-if="conflictSummary[2].value" class="is-danger">占用 {{ conflictSummary[2].value }} 间</span>
      <span v-if="conflictSummary[3].value" class="is-warning">禁排 {{ conflictSummary[3].value }} 间</span>
    </div>

    <section v-loading="loading" class="decision-shell">
      <el-tabs v-model="activePanel" class="smart-main-tabs">
        <el-tab-pane label="智能决策" name="decision">
          <section class="recommendation-section">
            <div class="recommendation-heading">
              <i class="el-icon-s-promotion" />
              <strong>整住方案</strong>
              <span>同一房间连续住满，全程不换房</span>
              <el-select
                v-model="manualRoomRecommendationId"
                clearable
                filterable
                size="small"
                placeholder="直接指定可用房间"
                class="manual-room-select"
                @change="selectManualRoom"
              >
                <el-option
                  v-for="item in singleRecommendations"
                  :key="`manual-${item.id}`"
                  :label="`${item.rooms[0].room} · ${item.rooms[0].roomType}`"
                  :value="item.id"
                />
              </el-select>
            </div>
            <div v-if="displayedSingleRecommendations.length" class="recommendation-grid">
              <article
                v-for="item in displayedSingleRecommendations"
                :key="item.id"
                :data-recommendation="item.id"
                role="button"
                tabindex="0"
                class="recommendation-card"
                :class="{ selected: selectedRecommendation && selectedRecommendation.id === item.id }"
                @click="selectRecommendation(item)"
                @keyup.enter="selectRecommendation(item)"
              >
                <div class="recommendation-reason">
                  <el-tag size="mini" type="success">推荐</el-tag>
                  <span>{{ item.reason }}</span>
                </div>
                <room-segment :room="item.rooms[0]" />
              </article>
            </div>
            <div v-else class="empty-state">
              <i class="el-icon-receiving" />
              <span>{{ allocationEmptyText }}</span>
            </div>
          </section>

          <section class="recommendation-section">
            <div class="recommendation-heading">
              <i class="el-icon-refresh" />
              <strong>换房方案</strong>
              <span>支持同房型或跨房型，只换一次</span>
            </div>
            <div v-if="displayedPairRecommendations.length" class="recommendation-grid pair-grid">
              <article
                v-for="(item, index) in displayedPairRecommendations"
                :key="item.id"
                :data-recommendation="item.id"
                role="button"
                tabindex="0"
                class="recommendation-card pair-card"
                :class="{ selected: selectedRecommendation && selectedRecommendation.id === item.id }"
                @click="selectRecommendation(item)"
                @keyup.enter="selectRecommendation(item)"
              >
                <div class="recommendation-reason is-warning">
                  <el-tag size="mini" type="warning">方案 {{ index + 1 }}</el-tag>
                  <span>{{ item.reason }}</span>
                </div>
                <div class="pair-rooms">
                  <room-segment :room="item.rooms[0]" />
                  <i class="el-icon-right change-room-icon" />
                  <room-segment :room="item.rooms[1]" />
                </div>
              </article>
            </div>
            <div v-else class="empty-state">
              <i class="el-icon-receiving" />
              <span>{{ allocationEmptyText }}</span>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="未来房态" name="timeline">
          <div class="timeline-toolbar">
            <div>
              <strong>{{ appliedFilters.store || filters.store }} · 未来房态</strong>
              <span>蓝色为订房/入住，橙色为禁排或保留；点击房间行可维护禁排。</span>
            </div>
            <div class="timeline-range-control">
              <span>查看范围</span>
              <el-radio-group v-model="timelineDays" size="mini">
                <el-radio-button v-for="days in timelineOptions" :key="days" :label="days">{{ days }}天</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="timeline-legend">
            <span><i class="is-available" />可排</span>
            <span><i class="is-booked" />已订/在住</span>
            <span><i class="is-blocked" />禁排/保留</span>
          </div>
          <div class="timeline-scroll">
            <div class="timeline-grid" :style="timelineGridStyle">
              <div class="timeline-room-head">房间 / 房型</div>
              <div v-for="date in timelineDates" :key="`head-${date}`" class="timeline-date-head">
                <strong>{{ shortDate(date) }}</strong>
                <small>周{{ weekdayText(date) }}</small>
              </div>
              <template v-for="room in timelineRooms">
                <div :key="`room-${room.id}`" class="timeline-room-cell">
                  <div>
                    <strong>{{ room.room }}</strong>
                    <span>{{ room.roomType }}</span>
                  </div>
                  <el-button type="text" size="mini" @click="openBlockDialog(room)">禁排</el-button>
                </div>
                <div
                  v-for="date in timelineDates"
                  :key="`${room.id}-${date}`"
                  class="timeline-day-cell"
                  :class="timelineCell(room, date).className"
                  :title="timelineCell(room, date).title"
                />
              </template>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="`冲突预警 ${conflictDetails.length}`" name="alerts">
          <div v-if="conflictDetails.length" class="conflict-list">
            <article v-for="item in conflictDetails" :key="item.key">
              <el-tag size="mini" :type="item.type">{{ item.category }}</el-tag>
              <strong>{{ item.room }}</strong>
              <span>{{ item.detail }}</span>
            </article>
          </div>
          <div v-else class="empty-state">
            <i class="el-icon-circle-check" />
            <span>当前查询日期内没有订房或禁排冲突</span>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <el-dialog
      title="房间禁排 / 保留"
      :visible.sync="blockDialogVisible"
      width="620px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form label-width="100px">
        <el-form-item label="房间">
          <el-input :value="blockForm.roomLabel" disabled />
        </el-form-item>
        <el-form-item label="处理类型" required>
          <el-radio-group v-model="blockForm.blockType">
            <el-radio-button v-for="item in blockTypes" :key="item" :label="item" />
          </el-radio-group>
        </el-form-item>
        <el-form-item label="日期范围" required>
          <el-date-picker
            v-model="blockForm.dateRange"
            type="daterange"
            value-format="yyyy-MM-dd"
            start-placeholder="开始日期"
            end-placeholder="结束日期（含）"
            :picker-options="futureDateOptions"
            class="full-control"
          />
        </el-form-item>
        <el-form-item label="原因" required>
          <el-input
            v-model.trim="blockForm.reason"
            type="textarea"
            :rows="3"
            maxlength="100"
            show-word-limit
            placeholder="例如：空调维修、深度消毒、客户指定保留"
          />
        </el-form-item>
      </el-form>
      <div v-if="currentRoomBlocks.length" class="current-blocks">
        <strong>当前禁排记录</strong>
        <article v-for="item in currentRoomBlocks" :key="item.id">
          <el-tag size="mini" type="warning">{{ item.block_type }}</el-tag>
          <span>{{ item.start_at }} 至 {{ addDays(item.end_at, -1) }} · {{ item.reason }}</span>
          <el-button type="text" size="mini" @click="removeBlock(item)">取消</el-button>
        </article>
      </div>
      <div slot="footer">
        <el-button @click="blockDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="blockSaving" @click="saveBlock">保存禁排</el-button>
      </div>
    </el-dialog>

    <el-dialog
      title="订房"
      :visible.sync="bookingVisible"
      width="1000px"
      top="5vh"
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="booking-room-grid">
        <div class="booking-room-label">房间号1：</div>
        <el-input v-model="bookingForm.room1" disabled />
        <div class="booking-room-label">预住日期1：</div>
        <div class="booking-date-range">
          <el-input v-model="bookingForm.startDate1" disabled />
          <span>~</span>
          <el-input v-model="bookingForm.endDate1" disabled />
        </div>
        <div class="booking-room-label">房间号2：</div>
        <el-input v-model="bookingForm.room2" disabled />
        <div class="booking-room-label">预住日期2：</div>
        <div class="booking-date-range">
          <el-input v-model="bookingForm.startDate2" disabled />
          <span>~</span>
          <el-input v-model="bookingForm.endDate2" disabled />
        </div>
      </div>

      <el-form label-position="right" label-width="110px" class="booking-form">
        <el-row :gutter="18">
          <el-col :span="12">
            <el-form-item label="客户姓名：" required>
              <el-input
                v-model="bookingForm.customerName"
                readonly
                class="customer-trigger"
                placeholder="点击选择客户"
                @click.native="openCustomerPicker"
              >
                <el-button slot="append" icon="el-icon-search" @click="openCustomerPicker">选择</el-button>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预住天数：" required>
              <el-input v-model="bookingForm.days" maxlength="3" @input="normalizeBookingDays" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分娩日期：">
              <el-date-picker v-model="bookingForm.birthDate" type="date" value-format="yyyy-MM-dd" class="full-control" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分娩方式：">
              <el-select v-model="bookingForm.birthWay" placeholder="-请选择-" class="full-control">
                <el-option v-for="option in birthWayOptions" :key="option" :label="option" :value="option" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="陪护人电话：">
              <el-input v-model="bookingForm.careTel" maxlength="11" @input="normalizeCareTel" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分娩医院：">
              <el-select v-model="bookingForm.birthHospital" class="full-control">
                <el-option v-for="option in hospitalOptions" :key="option" :label="option" :value="option" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col v-if="bookingForm.birthHospital === '-其他-'" :span="12">
            <el-form-item label="其他分娩医院：">
              <el-input v-model.trim="bookingForm.otherHospital" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注：">
              <el-input v-model.trim="bookingForm.remark" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <p class="demo-note">保存时会校验合同状态、审核入账、门店一致性和日期冲突。</p>
      <div slot="footer">
        <el-button type="primary" @click="saveBooking">保存</el-button>
        <el-button @click="bookingVisible = false">关闭</el-button>
      </div>
    </el-dialog>

    <el-dialog
      title="选择客户"
      :visible.sync="customerPickerVisible"
      width="1180px"
      top="7vh"
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="customer-filter-row">
        <span>客户名称：</span>
        <el-input v-model.trim="customerFilters.name" clearable />
        <span>手机号码：</span>
        <el-input v-model.trim="customerFilters.mobile" clearable />
        <span>门店：</span>
        <el-select v-model="customerFilters.store">
          <el-option v-for="store in storeOptions" :key="store" :label="store" :value="store" />
        </el-select>
        <span>客户状态：</span>
        <el-select v-model="customerFilters.status">
          <el-option label="- 未订房 -" value="- 未订房 -" />
          <el-option label="- 已订房 -" value="- 已订房 -" />
        </el-select>
        <el-button type="primary" size="small">搜  索</el-button>
      </div>
      <el-table
        :data="filteredCustomers"
        border
        stripe
        height="360"
        highlight-current-row
        @current-change="customerCurrent = $event"
        @row-dblclick="chooseCustomer"
      >
        <el-table-column prop="customerName" label="客户名称" min-width="110" fixed="left" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column prop="status" label="客户状态" width="105" />
        <el-table-column prop="store" label="分店" min-width="150" />
        <el-table-column prop="contractNo" label="合同编号" min-width="145" />
        <el-table-column prop="reservedRoomType" label="预定房型" min-width="120" />
        <el-table-column prop="packageName" label="套餐名称" min-width="130" />
        <el-table-column prop="contractAmount" label="合同金额" width="110">
          <template slot-scope="scope">¥ {{ Number(scope.row.contractAmount).toLocaleString('zh-CN') }}</template>
        </el-table-column>
        <el-table-column prop="bookableDays" label="可订房天数" width="110" />
        <el-table-column prop="salesperson" label="签单人" width="100" />
      </el-table>
      <div slot="footer">
        <span class="picker-tip">双击客户行可直接选择</span>
        <el-button type="primary" @click="chooseCustomer(customerCurrent)">选择</el-button>
        <el-button @click="customerPickerVisible = false">关闭</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import RoomSegment from './RoomRecommendationSegment'
import { getRoomModuleData, saveRoomModuleRecord } from '@/api/erp-room'
import {
  roomMatchesAllocationPackage,
  uniqueAllocationPackages
} from './smart-allocation-utils'

const STORE_OPTIONS = ['中心广场旗舰店', '黄河路轻奢店']
const STORE_BY_ID = {
  1: '中心广场旗舰店',
  2: '黄河路轻奢店'
}

function routeStoreName(route) {
  return STORE_BY_ID[Number(route.query.storeId)] || String(route.query.store || '')
}

const BIRTH_WAYS = ['顺产分娩', '剖宫产分娩', '小月子', '未生产']
const HOSPITALS = [
  '-其他-', '濮阳市妇幼保健院', '濮阳市人民医院', '濮阳市油田总医院', '濮阳市中医院',
  '濮阳市第三人民医院', '濮阳县人民医院', '濮阳县第二人民医院', '濮阳县妇幼保健院'
]
const FUTURE_DATE_OPTIONS = {
  disabledDate(value) {
    const startOfToday = new Date()
    startOfToday.setHours(0, 0, 0, 0)
    return value.getTime() < startOfToday.getTime()
  }
}

export default {
  name: 'SmartRoomAllocation',
  components: { RoomSegment },
  props: {
    config: {
      type: Object,
      required: true
    },
    canBook: {
      type: Boolean,
      default: false
    }
  },
  data() {
    const routeStore = routeStoreName(this.$route)
    return {
      filters: {
        store: routeStore || this.config.defaultFilters.store,
        startDate: this.config.defaultFilters.startDate,
        days: String(this.config.defaultFilters.days),
        endDate: this.config.defaultFilters.endDate,
        packageNo: '',
        roomType: '',
        floor: ''
      },
      appliedFilters: {},
      activePanel: 'decision',
      timelineDays: 30,
      timelineOptions: [14, 30, 60, 90],
      selectedRecommendation: null,
      manualRoomRecommendationId: '',
      bookingVisible: false,
      blockDialogVisible: false,
      blockSaving: false,
      blockTypes: ['维修', '消毒', '内部占用', '保留房'],
      blockForm: {
        roomId: '',
        roomLabel: '',
        blockType: '维修',
        dateRange: [],
        reason: ''
      },
      customerPickerVisible: false,
      customerCurrent: null,
      loading: false,
      saving: false,
      futureDateOptions: FUTURE_DATE_OPTIONS,
      rooms: [],
      packages: [],
      roomInventoryEvidence: null,
      storeOptionsData: [...STORE_OPTIONS],
      bookingForm: this.emptyBookingForm(),
      customerFilters: {
        name: '',
        mobile: '',
        store: routeStore || this.config.defaultFilters.store,
        status: '- 未订房 -'
      },
      customers: []
    }
  },
  computed: {
    storeOptions() {
      return this.storeOptionsData
    },
    packageOptions() {
      return uniqueAllocationPackages(
        this.packages,
        this.filters.store,
        this.storeMatches
      )
    },
    hasStorePackages() {
      return this.packageOptions.length > 0
    },
    allocationScopeText() {
      if (this.selectedPackage) return `${this.selectedPackage.packageName} · ${this.selectedPackage.days}天`
      return this.hasStorePackages ? '未选套餐 · 可按房型查看' : '本店未配置套餐 · 按房型排房'
    },
    selectedPackage() {
      return this.packageOptions.find(item => item.packageNo === this.filters.packageNo) || null
    },
    roomTypeOptions() {
      const field = this.config.filters.find(item => item.key === 'roomType')
      if (!field) return []
      const available = new Set(
        this.rooms
          .filter(room => this.storeMatches(this.filters.store, room.store))
          .filter(room => this.roomMatchesSelectedPackage(room, this.selectedPackage))
          .map(room => room.roomType)
          .filter(Boolean)
      )
      const packageAllowed = this.selectedPackage
        ? new Set(this.selectedPackage.allowedRoomTypes || [])
        : null
      return (field.options || []).filter(option => (
        available.has(option) && (!packageAllowed || packageAllowed.has(option))
      ))
    },
    floorOptions() {
      return [...new Set(
        this.rooms
          .filter(room => this.storeMatches(this.filters.store, room.store))
          .map(room => Number(room.floor))
          .filter(Number.isFinite)
      )].sort((left, right) => left - right)
    },
    birthWayOptions() {
      return BIRTH_WAYS
    },
    hospitalOptions() {
      return HOSPITALS
    },
    timelineBaseDate() {
      return this.appliedFilters.startDate || this.filters.startDate || this.formatDate(new Date())
    },
    timelineDates() {
      return Array.from({ length: Number(this.timelineDays) }, (_, index) => (
        this.addDays(this.timelineBaseDate, index)
      ))
    },
    timelineRooms() {
      return this.rooms
        .filter(room => this.storeMatches(this.appliedFilters.store || this.filters.store, room.store))
        // Older confirmed room records do not carry the optional
        // `roomNoConfirmed` flag.  Treat the absence of the flag as confirmed;
        // only an explicit `false` may exclude a room from the timeline.
        .filter(room => room.roomNoConfirmed !== false)
        .sort((a, b) => String(a.room).localeCompare(String(b.room), 'zh-CN', { numeric: true }))
    },
    timelineGridStyle() {
      const dayWidth = this.timelineDays <= 14 ? 72 : this.timelineDays <= 30 ? 66 : 60
      return {
        gridTemplateColumns: `190px repeat(${this.timelineDates.length}, ${dayWidth}px)`,
        minWidth: `${190 + this.timelineDates.length * dayWidth}px`
      }
    },
    currentRoomBlocks() {
      const room = this.rooms.find(item => Number(item.id) === Number(this.blockForm.roomId))
      return room ? (room.allocationBlocks || []) : []
    },
    queryEligibleRooms() {
      const filters = this.appliedFilters
      // 套餐是“门店已配置套餐”时的筛选条件；中心店当前尚未配置套餐，
      // 仍应允许按门店、房型和房态排房，不能把空套餐误判为无可用房。
      const selectedRoomType = filters.roomType || ''
      return this.rooms
        .filter(room => this.storeMatches(filters.store, room.store))
        .filter(room => !selectedRoomType || room.roomType === selectedRoomType)
        .filter(room => this.roomMatchesSelectedPackage(room, this.selectedPackage))
        .filter(room => room.roomNoConfirmed !== false && room.algorithmEnabled !== false)
        .filter(room => !['维修', '脏房'].includes(room.status))
        .filter(room => !filters.floor || String(room.floorNumber || '').replace(/\D/g, '') === String(filters.floor))
    },
    conflictDetails() {
      const { startDate, endDate } = this.appliedFilters
      if (!startDate || !endDate) return []
      const result = []
      this.queryEligibleRooms.forEach(room => {
        const bookings = room.bookings || []
        const blocks = room.allocationBlocks || []
        bookings.forEach(item => {
          const start = String(item.startAt || '').slice(0, 10)
          const end = String(item.endAt || '').slice(0, 10)
          if (start && end && this.rangesOverlap(startDate, endDate, start, end)) {
            result.push({
              key: `booking-${room.id}-${item.id || start}`,
              category: '订房冲突',
              type: 'danger',
              room: room.room,
              detail: `${start} 至 ${end} · ${item.customerName || item.status || '已有安排'}`
            })
          }
        })
        blocks.forEach(item => {
          if (this.rangesOverlap(startDate, endDate, item.start_at, item.end_at)) {
            result.push({
              key: `block-${room.id}-${item.id}`,
              category: item.block_type,
              type: 'warning',
              room: room.room,
              detail: `${item.start_at} 至 ${this.addDays(item.end_at, -1)} · ${item.reason}`
            })
          }
        })
      })
      return result
    },
    conflictSummary() {
      const bookingRooms = new Set(
        this.conflictDetails.filter(item => item.category === '订房冲突').map(item => item.room)
      )
      const blockedRooms = new Set(
        this.conflictDetails.filter(item => item.category !== '订房冲突').map(item => item.room)
      )
      const available = this.queryEligibleRooms.filter(room => (
        this.roomFreeFor(room, this.appliedFilters.startDate, this.appliedFilters.endDate)
      )).length
      return [
        {
          label: '候选房间',
          value: this.queryEligibleRooms.length,
          note: '已按门店、房型和楼层过滤',
          className: 'is-neutral'
        },
        { label: '当前可连续排', value: available, note: '全程无订房及禁排冲突', className: 'is-success' },
        { label: '订房冲突', value: bookingRooms.size, note: '查询日期内已有客户安排', className: 'is-danger' },
        { label: '禁排/保留', value: blockedRooms.size, note: '维修、消毒或人工保留', className: 'is-warning' }
      ]
    },
    allocationEmptyText() {
      return '当前日期和房态下没有可用方案，可调整入住日期、房型或楼层后重试'
    },
    generatedRecommendations() {
      const filters = this.appliedFilters
      if (!filters.store) return { singles: [], pairs: [] }
      const selectedRoomType = filters.roomType || ''
      let pool = this.rooms
        .filter(room => this.storeMatches(filters.store, room.store))
        .filter(room => !selectedRoomType || room.roomType === selectedRoomType)
        .filter(room => this.roomMatchesSelectedPackage(room, this.selectedPackage))
        .filter(room => room.roomNoConfirmed !== false)
        .filter(room => room.algorithmEnabled !== false)
        .filter(room => !['维修', '脏房'].includes(room.status))
        .map(room => ({
          id: room.id,
          roomId: room.id,
          room: room.room,
          roomType: room.roomType,
          roomStyle: room.roomStyle,
          floor: String(room.floorNumber || '').replace(/\D/g, ''),
          allowedPackageCodes: room.allowedPackageCodes || [],
          bookings: room.bookings || [],
          allocationBlocks: room.allocationBlocks || []
        }))
      if (filters.floor) pool = pool.filter(room => room.floor === String(filters.floor))
      const days = Math.max(1, Number(filters.days || 28))
      const singles = pool
        .filter(room => this.roomFreeFor(room, filters.startDate, filters.endDate))
        .map(room => {
          const score = this.recommendationScore(room, false, filters)
          return {
            id: `single-${room.id}`,
            type: 'single',
            score: score.value,
            scoreDetail: score.detail,
            reason: `${room.roomType} · 连续可住 · 日期无冲突`,
            rooms: [this.decorateRoom(room, filters.startDate, filters.endDate, days)]
          }
        })
        .sort((a, b) => b.score - a.score || String(a.rooms[0].room).localeCompare(String(b.rooms[0].room), 'zh-CN', { numeric: true }))
        .slice(0, 60)
      const splitCandidates = Array.from(
        { length: Math.max(0, days - 1) },
        (_, index) => index + 1
      ).sort((a, b) => Math.abs(a - days / 2) - Math.abs(b - days / 2))
      const pairCandidates = []
      splitCandidates.some(firstDays => {
        const splitDate = this.addDays(filters.startDate, firstDays)
        const firstRooms = pool.filter(room => this.roomFreeFor(room, filters.startDate, splitDate))
        const secondRooms = pool.filter(room => this.roomFreeFor(room, splitDate, filters.endDate))
        firstRooms.some(firstRoom => {
          secondRooms.some(secondRoom => {
            if (firstRoom.id === secondRoom.id) return
            const firstScore = this.recommendationScore(firstRoom, true, filters)
            const secondScore = this.recommendationScore(secondRoom, true, filters)
            const roomChoiceScore = firstRoom.roomType === secondRoom.roomType ? 14 : 12
            const floorScore = filters.floor ? 10 : 5
            const fragmentation = Math.round((firstScore.fragmentation + secondScore.fragmentation) / 2)
            pairCandidates.push({
              id: `pair-${firstRoom.id}-${secondRoom.id}-${firstDays}`,
              type: 'pair',
              score: roomChoiceScore + 25 + 12 + floorScore + fragmentation,
              scoreDetail: `房间选择 ${roomChoiceScore} · 两段无冲突 25 · 一次换房 12 · 楼层 ${floorScore} · 空档利用 ${fragmentation}`,
              wholeStayPenalty: Number(this.roomFreeFor(firstRoom, filters.startDate, filters.endDate)) +
                Number(this.roomFreeFor(secondRoom, filters.startDate, filters.endDate)),
              rooms: [
                this.decorateRoom(firstRoom, filters.startDate, splitDate, firstDays),
                this.decorateRoom(secondRoom, splitDate, filters.endDate, days - firstDays)
              ]
            })
            return pairCandidates.length >= 100
          })
          return pairCandidates.length >= 100
        })
        return pairCandidates.length >= 100
      })
      const seen = new Set()
      const pairs = pairCandidates
        .sort((a, b) => a.wholeStayPenalty - b.wholeStayPenalty || b.score - a.score)
        .filter(item => {
          const key = `${item.rooms[0].roomId}-${item.rooms[1].roomId}-${item.rooms[0].endDate}`
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
        .slice(0, 60)
        .map(item => ({
          ...item,
          reason: `${item.rooms[0].roomType} → ${item.rooms[1].roomType} · ${this.shortDate(item.rooms[0].endDate)}换房 · 两段无冲突`
        }))
      return { singles, pairs }
    },
    singleRecommendations() {
      return this.generatedRecommendations.singles
    },
    displayedSingleRecommendations() {
      return this.singleRecommendations.slice(0, 6)
    },
    pairRecommendations() {
      return this.generatedRecommendations.pairs
    },
    displayedPairRecommendations() {
      const sameType = this.pairRecommendations.filter(item => (
        item.rooms[0].roomType === item.rooms[1].roomType
      )).slice(0, 3)
      const crossType = this.pairRecommendations.filter(item => (
        item.rooms[0].roomType !== item.rooms[1].roomType
      )).slice(0, 3)
      const selectedIds = new Set([...sameType, ...crossType].map(item => item.id))
      const fallback = this.pairRecommendations
        .filter(item => !selectedIds.has(item.id))
        .slice(0, 6 - sameType.length - crossType.length)
      return [...sameType, ...crossType, ...fallback]
    },
    filteredCustomers() {
      return this.customers.filter(row => {
        if (this.customerFilters.name && !row.customerName.includes(this.customerFilters.name)) return false
        if (this.customerFilters.mobile && !row.mobile.includes(this.customerFilters.mobile)) return false
        if (this.customerFilters.store && row.store !== this.customerFilters.store) return false
        if (this.customerFilters.status && row.status !== this.customerFilters.status) return false
        if (this.appliedFilters.packageNo && row.packageNo !== this.appliedFilters.packageNo) return false
        return true
      })
    }
  },
  watch: {
    '$route.query': {
      handler() {
        const store = routeStoreName(this.$route)
        if (!store || this.storeMatches(this.filters.store, store)) return
        this.filters.store = store
        this.handleStoreChange()
      },
      deep: true
    }
  },
  created() {
    this.loadData(true)
  },
  methods: {
    async handleStoreChange() {
      const firstPackage = this.packageOptions[0]
      this.filters.roomType = ''
      this.filters.packageNo = firstPackage ? firstPackage.packageNo : ''
      this.syncPackageFilters(true)
      this.customerFilters.store = this.filters.store
      this.selectedRecommendation = null
      this.manualRoomRecommendationId = ''
      await this.loadData(false)
    },
    async handlePackageChange() {
      this.syncPackageFilters(Boolean(this.selectedPackage))
      this.selectedRecommendation = null
      this.manualRoomRecommendationId = ''
      await this.loadData(false)
    },
    syncPackageFilters(resetRoomType = false) {
      if (!this.selectedPackage) {
        return
      }
      this.filters.days = String(this.selectedPackage.days)
      this.syncEndFromDays()
      if (resetRoomType) this.filters.roomType = ''
    },
    roomMatchesSelectedPackage(room, selectedPackage) {
      return roomMatchesAllocationPackage(room, selectedPackage)
    },
    roomTypeOptionLabel(roomType) {
      return roomType
    },
    emptyBookingForm() {
      return {
        room1: '',
        startDate1: '',
        endDate1: '',
        room2: '',
        startDate2: '',
        endDate2: '',
        customerId: '',
        contractId: '',
        customerName: '',
        days: '28',
        birthDate: '',
        birthWay: '',
        careTel: '',
        birthHospital: '-其他-',
        otherHospital: '',
        remark: ''
      }
    },
    parseDate(value) {
      const parts = String(value || '').split('-').map(Number)
      return parts.length === 3 ? new Date(parts[0], parts[1] - 1, parts[2]) : new Date()
    },
    formatDate(value) {
      return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
    },
    shortDate(value) {
      const parts = String(value || '').split('-')
      return parts.length === 3 ? `${parts[1]}-${parts[2]}` : value
    },
    addDays(value, amount) {
      const date = this.parseDate(value)
      date.setDate(date.getDate() + Number(amount || 0))
      return this.formatDate(date)
    },
    dateDiff(start, end) {
      return Math.max(1, Math.round((this.parseDate(end) - this.parseDate(start)) / 86400000))
    },
    storeMatches(requested, actual) {
      if (requested === actual) return true
      if (String(requested).includes('黄河路')) return String(actual).includes('黄河路')
      if (String(requested).includes('中心广场') || String(requested).includes('建设路')) {
        return String(actual).includes('中心广场') || String(actual).includes('建设路')
      }
      return false
    },
    rangesOverlap(startA, endA, startB, endB) {
      return Boolean(startA && endA && startB && endB && startA < endB && endA > startB)
    },
    roomFreeFor(room, startDate, endDate) {
      if (!startDate || !endDate) return false
      const bookingConflict = (room.bookings || []).some(item => {
        const start = String(item.startAt || item.check_in || '').slice(0, 10)
        const end = String(item.endAt || item.check_out || '').slice(0, 10)
        return this.rangesOverlap(startDate, endDate, start, end)
      })
      const blockConflict = (room.allocationBlocks || []).some(item => (
        this.rangesOverlap(startDate, endDate, item.start_at, item.end_at)
      ))
      return !bookingConflict && !blockConflict
    },
    fragmentationScore(room, startDate, endDate) {
      const periods = [
        ...(room.bookings || []).map(item => ({
          start: String(item.startAt || item.check_in || '').slice(0, 10),
          end: String(item.endAt || item.check_out || '').slice(0, 10)
        })),
        ...(room.allocationBlocks || []).map(item => ({ start: item.start_at, end: item.end_at }))
      ].filter(item => item.start && item.end)
      if (!periods.length) return 8
      const previous = periods
        .filter(item => item.end <= startDate)
        .sort((a, b) => b.end.localeCompare(a.end))[0]
      const next = periods
        .filter(item => item.start >= endDate)
        .sort((a, b) => a.start.localeCompare(b.start))[0]
      const previousGap = previous ? this.dateDiff(previous.end, startDate) : 7
      const nextGap = next ? this.dateDiff(endDate, next.start) : 7
      const smallestGap = Math.min(previousGap, nextGap)
      if (smallestGap === 0) return 10
      if (smallestGap <= 2) return 4
      if (smallestGap <= 5) return 7
      return 9
    },
    recommendationScore(room, isPair, filters) {
      const roomChoiceScore = 15
      const stayScore = isPair ? 22 : 30
      const dateScore = 25
      const floorScore = filters.floor ? 10 : 5
      const fragmentation = this.fragmentationScore(room, filters.startDate, filters.endDate)
      return {
        value: roomChoiceScore + stayScore + dateScore + floorScore + fragmentation,
        fragmentation,
        detail: `房间选择 ${roomChoiceScore} · 连续入住 ${stayScore} · 日期无冲突 ${dateScore} · 楼层 ${floorScore} · 空档利用 ${fragmentation}`
      }
    },
    weekdayText(value) {
      return ['日', '一', '二', '三', '四', '五', '六'][this.parseDate(value).getDay()]
    },
    timelineCell(room, date) {
      const nextDate = this.addDays(date, 1)
      const booking = (room.bookings || []).find(item => (
        this.rangesOverlap(date, nextDate, String(item.startAt || '').slice(0, 10), String(item.endAt || '').slice(0, 10))
      ))
      if (booking) {
        return {
          className: 'is-booked',
          title: `${room.room} · ${booking.status || '已订房'} · ${booking.customerName || ''} · ${booking.startAt} 至 ${booking.endAt}`
        }
      }
      const block = (room.allocationBlocks || []).find(item => (
        this.rangesOverlap(date, nextDate, item.start_at, item.end_at)
      ))
      if (block) {
        return {
          className: 'is-blocked',
          title: `${room.room} · ${block.block_type} · ${block.reason} · ${block.start_at} 至 ${this.addDays(block.end_at, -1)}`
        }
      }
      return { className: 'is-available', title: `${room.room} · ${date} · 可排` }
    },
    decorateRoom(room, startDate, endDate, days) {
      return {
        ...room,
        startDate,
        endDate,
        startLabel: this.shortDate(startDate),
        endLabel: this.shortDate(endDate),
        days
      }
    },
    openBlockDialog(room) {
      const start = this.appliedFilters.startDate || this.formatDate(new Date())
      const inclusiveEnd = this.addDays(this.appliedFilters.endDate || this.addDays(start, 1), -1)
      this.blockForm = {
        roomId: room.id,
        roomLabel: `${room.room} · ${room.roomType}`,
        blockType: '维修',
        dateRange: [start, inclusiveEnd < start ? start : inclusiveEnd],
        reason: ''
      }
      this.blockDialogVisible = true
    },
    async saveBlock() {
      if (!this.blockForm.roomId || !this.blockForm.dateRange || this.blockForm.dateRange.length !== 2) {
        this.$message.warning('请选择完整的禁排日期范围')
        return
      }
      if (!this.blockForm.reason) {
        this.$message.warning('请填写禁排或保留原因')
        return
      }
      this.blockSaving = true
      try {
        await saveRoomModuleRecord('smart-allocation', {
          _action: '设置禁排',
          store: this.appliedFilters.store || this.filters.store,
          roomId: this.blockForm.roomId,
          blockType: this.blockForm.blockType,
          startAt: this.blockForm.dateRange[0],
          endAt: this.addDays(this.blockForm.dateRange[1], 1),
          reason: this.blockForm.reason
        })
        this.$message.success('禁排时段已保存，智能推荐已同步避让')
        await this.loadData(false)
      } finally {
        this.blockSaving = false
      }
    },
    async removeBlock(item) {
      this.blockSaving = true
      try {
        await saveRoomModuleRecord('smart-allocation', {
          _action: '取消禁排',
          store: this.appliedFilters.store || this.filters.store,
          roomId: this.blockForm.roomId,
          blockId: item.id
        })
        this.$message.success('禁排时段已取消')
        await this.loadData(false)
      } finally {
        this.blockSaving = false
      }
    },
    normalizeDays(value) {
      this.filters.days = String(value || '').replace(/\D/g, '').slice(0, 3)
    },
    normalizeFloor(value) {
      this.filters.floor = String(value || '').replace(/\D/g, '').slice(0, 2)
    },
    normalizeBookingDays(value) {
      this.bookingForm.days = String(value || '').replace(/\D/g, '').slice(0, 3)
    },
    normalizeCareTel(value) {
      this.bookingForm.careTel = String(value || '').replace(/\D/g, '').slice(0, 11)
    },
    syncEndFromDays() {
      if (!this.filters.startDate || !this.filters.days) return
      this.filters.endDate = this.addDays(this.filters.startDate, Number(this.filters.days))
    },
    syncDaysFromEnd() {
      if (!this.filters.startDate || !this.filters.endDate) return
      if (this.parseDate(this.filters.endDate) < this.parseDate(this.filters.startDate)) {
        this.$message.warning('结束日期不能小于开始日期')
        this.filters.endDate = ''
        this.filters.days = ''
        return
      }
      this.filters.days = String(this.dateDiff(this.filters.startDate, this.filters.endDate))
    },
    async search() {
      if (!this.filters.startDate || !this.filters.endDate || !this.filters.days) {
        this.$message.warning('请填写完整入住日期和预住天数')
        return
      }
      const today = this.formatDate(new Date())
      if (this.filters.startDate < today) {
        this.$message.warning('入住日期不能早于今天')
        return
      }
      if (this.filters.startDate >= this.filters.endDate) {
        this.$message.warning('退房日期必须晚于入住日期')
        return
      }
      if (this.selectedPackage && Number(this.filters.days) !== Number(this.selectedPackage.days)) {
        this.$message.warning('预住天数必须与所选套餐版本一致')
        this.syncPackageFilters()
        return
      }
      await this.loadData(false)
    },
    async loadData(initializing = false) {
      this.loading = true
      try {
        const response = await getRoomModuleData('smart-allocation', this.filters)
        this.rooms = response.data.list || []
        this.packages = response.data.packages || []
        this.roomInventoryEvidence = response.data.roomInventoryEvidence || null
        this.customers = response.data.customers || []
        const stores = (response.data.stores || []).map(item => item.name)
        if (stores.length) {
          this.storeOptionsData = stores
          if (!stores.some(name => this.storeMatches(this.filters.store, name))) {
            this.filters.store = stores[0]
            this.customerFilters.store = stores[0]
          }
        }
        let packageChanged = false
        if (!this.packageOptions.some(item => item.packageNo === this.filters.packageNo)) {
          const firstPackage = this.packageOptions[0]
          this.filters.packageNo = firstPackage ? firstPackage.packageNo : ''
          packageChanged = true
        }
        if (initializing || this.selectedPackage) this.syncPackageFilters(initializing || packageChanged)
        this.selectedRecommendation = null
        this.manualRoomRecommendationId = ''
        this.appliedFilters = { ...this.filters }
      } finally {
        this.loading = false
      }
    },
    selectRecommendation(item) {
      this.selectedRecommendation = item
      this.manualRoomRecommendationId = item.type === 'single' ? item.id : ''
    },
    selectManualRoom(id) {
      if (!id) {
        if (this.selectedRecommendation && this.selectedRecommendation.type === 'single') {
          this.selectedRecommendation = null
        }
        return
      }
      const item = this.singleRecommendations.find(candidate => candidate.id === id)
      if (item) this.selectedRecommendation = item
    },
    openBooking() {
      if (!this.selectedRecommendation) {
        this.$message.warning('请选择想订的房间!')
        return
      }
      const rooms = this.selectedRecommendation.rooms
      this.bookingForm = {
        ...this.emptyBookingForm(),
        room1: rooms[0].room,
        startDate1: rooms[0].startDate,
        endDate1: rooms[0].endDate,
        room2: rooms[1] ? rooms[1].room : '',
        startDate2: rooms[1] ? rooms[1].startDate : '',
        endDate2: rooms[1] ? rooms[1].endDate : '',
        days: String(this.appliedFilters.days || 28)
      }
      this.bookingVisible = true
    },
    openCustomerPicker() {
      this.customerFilters.store = this.appliedFilters.store
      this.customerCurrent = null
      this.customerPickerVisible = true
    },
    chooseCustomer(row) {
      if (!row) {
        this.$message.warning('请选择客户')
        return
      }
      if (!this.storeMatches(this.appliedFilters.store, row.store)) {
        this.$message.warning('客户合同门店与当前排房门店不一致')
        return
      }
      if (this.appliedFilters.packageNo && row.packageNo !== this.appliedFilters.packageNo) {
        this.$message.warning('客户合同套餐与当前排房套餐不一致')
        return
      }
      this.bookingForm.customerId = row.id
      this.bookingForm.contractId = row.contractId
      this.bookingForm.customerName = row.customerName
      this.bookingForm.birthDate = row.birthDate
      this.bookingForm.careTel = row.careTel
      this.customerPickerVisible = false
    },
    async saveBooking() {
      if (!this.selectedRecommendation) {
        this.$message.warning('请重新选择排房方案')
        return
      }
      if (!this.bookingForm.customerId) {
        this.$message.warning('客户不能为空！')
        return
      }
      if (!this.bookingForm.days) {
        this.$message.warning('预住天数不能为空！')
        return
      }
      this.saving = true
      try {
        for (const segment of this.selectedRecommendation.rooms) {
          await saveRoomModuleRecord('smart-allocation', {
            _action: '订房',
            customerId: this.bookingForm.customerId,
            contractId: this.bookingForm.contractId,
            store: this.appliedFilters.store,
            packageNo: this.appliedFilters.packageNo,
            packageName: this.selectedPackage ? this.selectedPackage.packageName : '',
            totalDays: Number(this.appliedFilters.days),
            roomId: segment.roomId,
            room: segment.room,
            plannedCheckInAt: segment.startDate,
            plannedCheckOutAt: segment.endDate,
            remark: this.bookingForm.remark
          })
        }
        this.$message.success('订房记录已保存')
        this.bookingVisible = false
        await this.search()
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.smart-allocation { margin-top: 16px; }
.smart-toolbar-card, .smart-query-card { border: 0; border-radius: 10px; }
.smart-toolbar-card ::v-deep .el-card__body { padding: 9px 18px; }
.smart-query-card { margin-top: 8px; }
.smart-query-card ::v-deep .el-card__body { padding: 13px 18px; }
.book-action { padding: 4px 0; color: #344257; font-size: 13px; }
.book-action:hover { color: #8c6a36; }
.smart-query-row, .smart-query-item, .smart-date-item { display: flex; align-items: center; }
.smart-query-row { flex-wrap: wrap; gap: 10px 18px; }
.smart-query-item > span { flex: 0 0 auto; margin-right: 7px; color: #4c5b70; font-size: 12px; }
.smart-query-item label { margin: 0 7px 0 4px; color: #4c5b70; font-size: 12px; font-weight: 400; }
.store-control { width: 178px; }
.package-control { width: 210px; }
.date-control { width: 150px; }
.day-control { width: 48px; margin-left: 5px; }
.type-control { width: 170px; }
.floor-control { width: 68px; }
.query-button { min-width: 66px; }
.operational-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 10px;
  padding: 10px 16px;
  border: 1px solid #e7e1d7;
  border-radius: 9px;
  color: #746b5f;
  background: #fff;
  font-size: 12px;
}
.operational-strip strong { color: #3d352c; font-size: 13px; }
.operational-strip .is-success { color: #2d8f72; }
.operational-strip .is-danger { color: #cf5d55; }
.operational-strip .is-warning { color: #ba7c2c; }
.decision-shell { margin-top: 10px; padding: 0 16px 16px; border-radius: 10px; background: #fff; }
.smart-main-tabs ::v-deep .el-tabs__header { margin-bottom: 14px; }
.smart-main-tabs ::v-deep .el-tabs__item { height: 48px; line-height: 48px; font-weight: 600; }
.smart-main-tabs ::v-deep .el-tabs__item.is-active { color: #8c6a36; }
.smart-main-tabs ::v-deep .el-tabs__active-bar { background-color: #b8945a; }
.conflict-summary { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; }
.conflict-summary article { display: flex; flex-direction: column; gap: 5px; padding: 13px 15px; border: 1px solid #e6edf3; border-radius: 9px; background: #f8fafc; }
.conflict-summary small { color: #738096; font-size: 12px; }
.conflict-summary strong { color: #26374d; font-size: 24px; }
.conflict-summary span { color: #8c98a8; font-size: 11px; }
.conflict-summary .is-success { border-color: #ccebe2; background: #f0faf7; }
.conflict-summary .is-success strong { color: #159b78; }
.conflict-summary .is-danger { border-color: #f6d3d3; background: #fff6f6; }
.conflict-summary .is-danger strong { color: #e45a5a; }
.conflict-summary .is-warning { border-color: #f5dfbd; background: #fff9ef; }
.conflict-summary .is-warning strong { color: #d9922e; }
.recommendation-section { margin-top: 4px; padding: 12px 0 2px; border-top: 1px solid #eee9e1; background: #fff; }
.recommendation-heading { display: flex; align-items: center; min-height: 26px; margin-bottom: 13px; }
.recommendation-heading > i { color: #a68048; font-size: 18px; }
.recommendation-heading strong { margin-left: 5px; color: #5b4932; font-size: 15px; }
.recommendation-heading span { margin-left: 8px; color: #919191; font-size: 12px; }
.manual-room-select { width: 210px; margin-left: auto; }
.recommendation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  align-items: stretch;
  gap: 14px;
}
.recommendation-grid.pair-grid { grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); }
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 92px;
  color: #909399;
  font-size: 13px;
}
.empty-state i { color: #c0c4cc; font-size: 28px; }
.recommendation-card {
  display: flex;
  box-sizing: border-box;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  padding: 11px;
  border: 1px solid #e6ebf0;
  border-radius: 11px;
  background: #fff;
  cursor: pointer;
  outline: none;
  transition: .15s;
}
.recommendation-card:hover { border-color: #b8945a; box-shadow: 0 4px 13px rgba(86, 65, 35, .1); }
.recommendation-card.selected { border-color: #b8945a; box-shadow: 0 0 0 2px rgba(184, 148, 90, .14); }
.recommendation-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-height: 30px;
  padding-bottom: 7px;
  color: #2f6e67;
  font-size: 12px;
  line-height: 1.55;
}
.recommendation-reason ::v-deep .el-tag { flex: 0 0 auto; margin-top: 1px; }
.recommendation-reason > span {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.recommendation-reason.is-warning { color: #98641c; background: #fff7e9; }
.recommendation-reason.is-warning { margin: -4px -4px 0; padding: 8px 9px 9px; border-radius: 7px; }
.pair-rooms { display: grid; grid-template-columns: minmax(0, 1fr) 28px minmax(0, 1fr); align-items: stretch; gap: 8px; }
.change-room-icon { display: flex; align-items: center; justify-content: center; color: #b8945a; font-size: 22px; }
.timeline-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; padding: 4px 0 2px; }
.timeline-toolbar > div { display: flex; flex-direction: column; gap: 5px; }
.timeline-toolbar strong { color: #26374d; font-size: 15px; }
.timeline-toolbar span { color: #8793a3; font-size: 12px; }
.timeline-range-control { align-items: flex-end; flex: 0 0 auto; }
.timeline-range-control > span { color: #8a96a5; font-size: 11px; }
.timeline-range-control ::v-deep .el-radio-group { display: inline-flex; flex-wrap: nowrap; }
.timeline-range-control ::v-deep .el-radio-button { display: inline-block; }
.timeline-range-control ::v-deep .el-radio-button__inner {
  min-width: 62px;
  padding: 8px 13px;
  text-align: center;
}
.timeline-legend { display: flex; gap: 20px; margin: 14px 0 10px; color: #647287; font-size: 12px; }
.timeline-legend span { display: flex; align-items: center; gap: 5px; }
.timeline-legend i { width: 13px; height: 13px; border: 1px solid rgba(60, 79, 99, .08); border-radius: 4px; }
.timeline-scroll {
  max-height: 570px;
  overflow: auto;
  border: 1px solid #dfe6ed;
  border-radius: 10px;
  background: #fff;
  scrollbar-color: #b7c1cc #eef2f5;
  scrollbar-width: thin;
}
.timeline-grid { display: grid; }
.timeline-room-head, .timeline-date-head {
  position: sticky;
  top: 0;
  z-index: 3;
  min-height: 54px;
  border-right: 1px solid #e4eaf0;
  border-bottom: 1px solid #d8e0e8;
  background: #f5f8fa;
}
.timeline-room-head {
  left: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  padding-left: 16px;
  color: #45566d;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 4px 0 10px rgba(38, 55, 77, .04);
}
.timeline-date-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  color: #43546b;
  white-space: nowrap;
}
.timeline-date-head strong { font-size: 11px; font-weight: 600; writing-mode: horizontal-tb; }
.timeline-date-head small { color: #929eac; font-size: 10px; }
.timeline-room-cell {
  position: sticky;
  left: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 48px;
  padding: 6px 10px 6px 15px;
  border-right: 1px solid #dfe5eb;
  border-bottom: 1px solid #e9eef2;
  background: #fff;
  box-shadow: 4px 0 10px rgba(38, 55, 77, .035);
}
.timeline-room-cell > div { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.timeline-room-cell strong { color: #29394e; font-size: 12px; }
.timeline-room-cell span { overflow: hidden; color: #8894a4; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.timeline-room-cell ::v-deep .el-button { padding: 5px 7px; border-radius: 5px; }
.timeline-day-cell { min-height: 48px; border-right: 1px solid #e7edf1; border-bottom: 1px solid #e7edf1; }
.timeline-day-cell.is-available, .timeline-legend .is-available { background: #f4f8f7; }
.timeline-day-cell.is-booked, .timeline-legend .is-booked { background: #82b9e8; }
.timeline-day-cell.is-blocked, .timeline-legend .is-blocked { background: #f2ae67; }
.timeline-day-cell:hover { box-shadow: inset 0 0 0 2px rgba(31, 59, 88, .22); }
.conflict-list { display: grid; gap: 9px; }
.conflict-list article { display: grid; grid-template-columns: 90px 90px 1fr; align-items: center; gap: 8px; padding: 11px 13px; border: 1px solid #edf0f4; border-radius: 7px; color: #637186; font-size: 12px; }
.conflict-list strong { color: #2f3f55; }
.current-blocks { padding: 12px 14px; border: 1px solid #f0dfc6; border-radius: 7px; background: #fffaf2; }
.current-blocks > strong { display: block; margin-bottom: 8px; color: #6d5a40; font-size: 12px; }
.current-blocks article { display: grid; grid-template-columns: 70px 1fr 35px; align-items: center; gap: 8px; min-height: 31px; color: #7a6b59; font-size: 11px; }
.booking-room-grid { display: grid; grid-template-columns: 95px 1fr 95px 2fr; align-items: center; gap: 10px 12px; padding: 14px 16px; border: 1px solid #eceff3; border-radius: 6px; background: #fafbfc; }
.booking-room-label { color: #536176; font-size: 13px; text-align: right; }
.booking-date-range { display: grid; grid-template-columns: 1fr 16px 1fr; align-items: center; gap: 5px; }
.booking-date-range > span { color: #7c8796; text-align: center; }
.booking-form { margin-top: 18px; }
.booking-form ::v-deep .el-form-item { margin-bottom: 16px; }
.full-control { width: 100%; }
.customer-trigger ::v-deep .el-input__inner { cursor: pointer; }
.demo-note { margin: 0; color: #9a6e45; font-size: 12px; text-align: right; }
.customer-filter-row { display: grid; grid-template-columns: auto 145px auto 145px auto 180px auto 135px auto; align-items: center; gap: 8px; margin-bottom: 14px; color: #536176; font-size: 12px; }
.picker-tip { margin-right: 18px; color: #8a96a5; font-size: 12px; }
@media (max-width: 1180px) {
  .smart-query-row { align-items: flex-start; flex-direction: column; }
  .inventory-stat-grid { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
  .conflict-summary { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
  .recommendation-grid,
  .recommendation-grid.pair-grid { grid-template-columns: 1fr; }
  .customer-filter-row { grid-template-columns: auto 1fr auto 1fr; }
  .booking-room-grid { grid-template-columns: 90px 1fr; }
}
@media (max-width: 760px) {
  .timeline-toolbar { align-items: flex-start; flex-direction: column; }
  .timeline-range-control { align-items: flex-start; width: 100%; }
  .timeline-range-control ::v-deep .el-radio-group { width: 100%; }
  .timeline-range-control ::v-deep .el-radio-button { flex: 1; }
  .timeline-range-control ::v-deep .el-radio-button__inner { width: 100%; min-width: 0; padding-right: 8px; padding-left: 8px; }
  .pair-rooms { grid-template-columns: 1fr; }
  .change-room-icon { min-height: 22px; transform: rotate(90deg); }
}
</style>
