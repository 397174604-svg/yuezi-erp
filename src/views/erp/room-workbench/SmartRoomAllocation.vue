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
          <el-select v-model="filters.store" class="store-control">
            <el-option v-for="store in storeOptions" :key="store" :label="store" :value="store" />
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
            @change="syncEndFromDays"
          />
          <el-input
            v-model="filters.days"
            maxlength="3"
            class="day-control"
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
            @change="syncDaysFromEnd"
          />
        </div>
        <div class="smart-query-item">
          <span>房间类型</span>
          <el-select v-model="filters.roomType" clearable placeholder="请选择" class="type-control">
            <el-option v-for="roomType in roomTypeOptions" :key="roomType" :label="roomType" :value="roomType" />
          </el-select>
        </div>
        <div class="smart-query-item">
          <span>楼层</span>
          <el-input v-model="filters.floor" maxlength="2" class="floor-control" @input="normalizeFloor" />
        </div>
        <el-button type="primary" size="small" class="query-button" @click="search">查询</el-button>
      </div>
    </el-card>

    <section class="recommendation-section">
      <div class="recommendation-heading">
        <i class="el-icon-s-promotion" />
        <strong>推荐一</strong>
        <span>（注：客户不需换房,系统至多推荐20个房间选择）</span>
      </div>
      <div v-if="singleRecommendations.length" class="recommendation-grid">
        <article
          v-for="item in singleRecommendations"
          :key="item.id"
          :data-recommendation="item.id"
          role="button"
          tabindex="0"
          class="recommendation-card"
          :class="{ selected: selectedRecommendation && selectedRecommendation.id === item.id }"
          @click="selectRecommendation(item)"
          @keyup.enter="selectRecommendation(item)"
        >
          <room-segment :room="item.rooms[0]" />
        </article>
      </div>
      <div v-else class="empty-state">
        <i class="el-icon-receiving" />
        <span>暂无无需换房的推荐房间</span>
      </div>
    </section>

    <section class="recommendation-section">
      <div class="recommendation-heading">
        <i class="el-icon-s-promotion" />
        <strong>推荐二</strong>
        <span>（注：2房间拼房，客户需换1次房）</span>
      </div>
      <div v-if="pairRecommendations.length" class="recommendation-grid pair-grid">
        <article
          v-for="item in pairRecommendations"
          :key="item.id"
          :data-recommendation="item.id"
          role="button"
          tabindex="0"
          class="recommendation-card pair-card"
          :class="{ selected: selectedRecommendation && selectedRecommendation.id === item.id }"
          @click="selectRecommendation(item)"
          @keyup.enter="selectRecommendation(item)"
        >
          <room-segment :room="item.rooms[0]" />
          <i class="el-icon-right change-room-icon" />
          <room-segment :room="item.rooms[1]" />
        </article>
      </div>
      <div v-else class="empty-state">
        <i class="el-icon-receiving" />
        <span>暂无两房拼房推荐</span>
      </div>
    </section>

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
      <p class="demo-note">保存后写入 MySQL 订房记录，并校验合同、门店和日期冲突。</p>
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

const STORE_OPTIONS = ['中心广场旗舰店', '黄河路轻奢店']

const BIRTH_WAYS = ['顺产分娩', '剖宫产分娩', '小月子', '未生产']
const HOSPITALS = [
  '-其他-', '濮阳市妇幼保健院', '濮阳市人民医院', '濮阳市油田总医院', '濮阳市中医院',
  '濮阳市第三人民医院', '濮阳县人民医院', '濮阳县第二人民医院', '濮阳县妇幼保健院'
]

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
    return {
      filters: {
        store: this.config.defaultFilters.store,
        startDate: this.config.defaultFilters.startDate,
        days: String(this.config.defaultFilters.days),
        endDate: this.config.defaultFilters.endDate,
        roomType: '',
        floor: ''
      },
      appliedFilters: {},
      selectedRecommendation: null,
      bookingVisible: false,
      customerPickerVisible: false,
      customerCurrent: null,
      loading: false,
      saving: false,
      rooms: [],
      storeOptionsData: [...STORE_OPTIONS],
      bookingForm: this.emptyBookingForm(),
      customerFilters: {
        name: '',
        mobile: '',
        store: this.config.defaultFilters.store,
        status: '- 未订房 -'
      },
      customers: []
    }
  },
  computed: {
    storeOptions() {
      return this.storeOptionsData
    },
    roomTypeOptions() {
      const field = this.config.filters.find(item => item.key === 'roomType')
      return field ? field.options : []
    },
    birthWayOptions() {
      return BIRTH_WAYS
    },
    hospitalOptions() {
      return HOSPITALS
    },
    generatedRecommendations() {
      const filters = this.appliedFilters
      if (!filters.store) return { singles: [], pairs: [] }
      let pool = this.rooms
        .filter(room => this.storeMatches(filters.store, room.store))
        .filter(room => !['维修', '脏房'].includes(room.status))
        .filter(room => !(room.bookings || []).some(item => {
          const start = String(item.startAt || '').slice(0, 10)
          const end = String(item.endAt || '').slice(0, 10)
          return !(end <= filters.startDate || start >= filters.endDate)
        }))
        .map(room => ({
          id: room.id,
          roomId: room.id,
          room: room.room,
          roomType: room.roomType,
          floor: String(room.floorNumber || '').replace(/\D/g, '')
        }))
      if (filters.roomType) pool = pool.filter(room => room.roomType === filters.roomType)
      if (filters.floor) pool = pool.filter(room => room.floor === String(filters.floor))
      const days = Math.max(1, Number(filters.days || 28))
      const singles = pool.slice(0, 20).map((room, index) => ({
        id: `single-${room.id}-${index}`,
        type: 'single',
        rooms: [this.decorateRoom(room, filters.startDate, filters.endDate, days)]
      }))
      const pairSource = pool.length > 1 ? pool : []
      const pairCount = Math.min(10, pairSource.length * 2)
      const splitCandidates = [days - 2, days - 8, Math.round(days / 2), 8, 18, 20]
      const pairs = Array.from({ length: pairCount }, (_, index) => {
        const firstRoom = pairSource[index % pairSource.length]
        const secondRoom = pairSource[(index + 1 + Math.floor(index / pairSource.length)) % pairSource.length]
        const firstDays = Math.min(days - 1, Math.max(1, splitCandidates[index % splitCandidates.length]))
        const splitDate = this.addDays(filters.startDate, firstDays)
        return {
          id: `pair-${firstRoom.id}-${secondRoom.id}-${index}`,
          type: 'pair',
          rooms: [
            this.decorateRoom(firstRoom, filters.startDate, splitDate, firstDays),
            this.decorateRoom(secondRoom, splitDate, filters.endDate, days - firstDays)
          ]
        }
      })
      return { singles, pairs }
    },
    singleRecommendations() {
      return this.generatedRecommendations.singles
    },
    pairRecommendations() {
      return this.generatedRecommendations.pairs
    },
    filteredCustomers() {
      return this.customers.filter(row => {
        if (this.customerFilters.name && !row.customerName.includes(this.customerFilters.name)) return false
        if (this.customerFilters.mobile && !row.mobile.includes(this.customerFilters.mobile)) return false
        if (this.customerFilters.store && row.store !== this.customerFilters.store) return false
        if (this.customerFilters.status && row.status !== this.customerFilters.status) return false
        return true
      })
    }
  },
  created() {
    this.appliedFilters = { ...this.filters }
    this.search()
  },
  methods: {
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
      this.loading = true
      try {
        const response = await getRoomModuleData('smart-allocation', this.filters)
        this.rooms = response.data.list || []
        this.customers = response.data.customers || []
        const stores = (response.data.stores || []).map(item => item.name)
        if (stores.length) {
          this.storeOptionsData = stores
          if (!stores.some(name => this.storeMatches(this.filters.store, name))) {
            this.filters.store = stores[0]
            this.customerFilters.store = stores[0]
          }
        }
        this.selectedRecommendation = null
        this.appliedFilters = { ...this.filters }
      } finally {
        this.loading = false
      }
    },
    selectRecommendation(item) {
      this.selectedRecommendation = item
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
      this.bookingForm.customerId = row.id
      this.bookingForm.contractId = row.contractId
      this.bookingForm.customerName = row.customerName
      this.bookingForm.birthDate = row.birthDate
      this.bookingForm.careTel = row.careTel
      this.customerPickerVisible = false
    },
    async saveBooking() {
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
            roomId: segment.roomId,
            room: segment.room,
            plannedCheckInAt: segment.startDate,
            plannedCheckOutAt: segment.endDate,
            remark: this.bookingForm.remark
          })
        }
        this.$message.success('订房记录已写入 MySQL')
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
.book-action:hover { color: #ff638b; }
.smart-query-row, .smart-query-item, .smart-date-item { display: flex; align-items: center; }
.smart-query-row { flex-wrap: wrap; gap: 10px 18px; }
.smart-query-item > span { flex: 0 0 auto; margin-right: 7px; color: #4c5b70; font-size: 12px; }
.smart-query-item label { margin: 0 7px 0 4px; color: #4c5b70; font-size: 12px; font-weight: 400; }
.store-control { width: 178px; }
.date-control { width: 132px; }
.day-control { width: 48px; margin-left: 5px; }
.type-control { width: 170px; }
.floor-control { width: 68px; }
.query-button { min-width: 66px; }
.recommendation-section { margin-top: 12px; padding: 15px 18px 2px; border-radius: 10px; background: #fff; }
.recommendation-heading { display: flex; align-items: center; min-height: 26px; margin-bottom: 13px; }
.recommendation-heading > i { color: #f5a623; font-size: 18px; }
.recommendation-heading strong { margin-left: 5px; color: #ef5300; font-size: 15px; }
.recommendation-heading span { color: #919191; font-size: 12px; }
.recommendation-grid { display: flex; flex-wrap: wrap; align-items: stretch; gap: 0 22px; }
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
.recommendation-card { display: flex; margin-bottom: 20px; border: 1px solid #fff; border-radius: 5px; background: #fff; cursor: pointer; outline: none; transition: .15s; }
.recommendation-card:hover { border-color: #f4b5c7; box-shadow: 0 4px 13px rgba(250, 99, 139, .11); }
.recommendation-card.selected { border-color: #fd85a8; box-shadow: 0 0 0 2px rgba(253, 133, 168, .12); }
.pair-card { align-items: center; }
.change-room-icon { width: 30px; margin: 0 8px; color: #fd85a8; font-size: 24px; text-align: center; }
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
  .customer-filter-row { grid-template-columns: auto 1fr auto 1fr; }
  .booking-room-grid { grid-template-columns: 90px 1fr; }
}
</style>
