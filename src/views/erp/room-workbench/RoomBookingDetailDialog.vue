<template>
  <el-dialog
    title="订房详情"
    :visible="visible"
    width="94%"
    top="3vh"
    append-to-body
    :close-on-click-modal="false"
    custom-class="room-booking-detail-dialog"
    @update:visible="$emit('update:visible', $event)"
  >
    <template v-if="room">
      <div class="booking-room-title">房间号：<strong>{{ room.room }}</strong></div>

      <section class="current-stay-panel">
        <h3>当前入住详情</h3>
        <div class="current-stay-grid">
          <div v-for="field in currentFields" :key="field.label">
            <span>{{ field.label }}</span>
            <strong :class="{ 'is-danger': field.danger, 'is-money': field.money }">{{ field.value || '—' }}</strong>
          </div>
        </div>
      </section>

      <el-tabs v-model="activeTab" type="card" class="room-record-tabs">
        <el-tab-pane label="客户的房间记录" name="current">
          <el-table :data="currentRecords" border stripe max-height="340">
            <el-table-column prop="room" label="房间名称" min-width="105" fixed="left" />
            <el-table-column prop="customerName" label="客户名称" min-width="120" />
            <el-table-column prop="plannedCheckInAt" label="预住日期" min-width="175" />
            <el-table-column prop="checkInAt" label="入住日期" min-width="175" />
            <el-table-column prop="expectedCheckOutAt" label="预计退房日期" min-width="175" />
            <el-table-column prop="totalDays" label="预住天数" min-width="95" />
            <el-table-column prop="status" label="状态" min-width="95" />
            <el-table-column prop="operation" label="操作" min-width="90" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="过去入住信息" name="past">
          <el-table :data="pastRecords" border stripe max-height="340">
            <el-table-column prop="customerName" label="客户名称" min-width="120" fixed="left" />
            <el-table-column prop="room" label="房间名称" min-width="105" />
            <el-table-column prop="roomType" label="房间类别" min-width="130" />
            <el-table-column prop="roomStyle" label="房间风格" min-width="120" />
            <el-table-column prop="checkInAt" label="入住日期" min-width="175" />
            <el-table-column prop="actualCheckOutAt" label="实际退房日期" min-width="175" />
            <el-table-column prop="stayedDays" label="入住天数" min-width="95" />
            <el-table-column prop="plannedCheckInAt" label="预住日期" min-width="175" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="未来预定信息" name="future">
          <el-table :data="futureRecords" border stripe max-height="340">
            <el-table-column prop="customerName" label="客户名称" min-width="120" fixed="left" />
            <el-table-column prop="room" label="房间名称" min-width="105" />
            <el-table-column prop="roomType" label="房间类别" min-width="130" />
            <el-table-column prop="roomStyle" label="房间风格" min-width="120" />
            <el-table-column prop="totalDays" label="预住天数" min-width="95" />
            <el-table-column prop="plannedCheckInAt" label="预住日期" min-width="175" />
            <el-table-column prop="expectedCheckOutAt" label="预计退房日期" min-width="175" />
            <el-table-column prop="roomStatus" label="房间状态" min-width="100" />
            <el-table-column prop="operation" label="操作" min-width="90" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </template>
  </el-dialog>
</template>

<script>
export default {
  name: 'RoomBookingDetailDialog',
  props: {
    visible: { type: Boolean, default: false },
    room: { type: Object, default: null }
  },
  data() {
    return { activeTab: 'current' }
  },
  computed: {
    currentStay() {
      if (!this.room || !this.room.stays) return {}
      return this.room.stays.find(item => item.status === '已入住') || this.room.stays[0] || {}
    },
    currentFields() {
      const stay = this.currentStay
      const room = this.room || {}
      return [
        { label: '当前入住客户', value: stay.customerName },
        { label: '预入住时间', value: stay.plannedCheckInAt },
        { label: '入住时间', value: stay.checkInAt },
        { label: '预住总天数', value: `${stay.totalDays || 0}天` },
        { label: '已入住天数', value: `${stay.stayedDays || 0}天` },
        { label: '预退房时间', value: stay.expectedCheckOutAt },
        { label: '实际退房时间', value: stay.actualCheckOutAt },
        { label: '剩余天数', value: `${stay.remainingDays || 0}天`, danger: true },
        { label: '陪护人', value: stay.escort },
        { label: '陪护电话', value: stay.escortMobile },
        { label: '押金金额', value: Number(room.deposit || 0).toFixed(2), money: true },
        { label: '相关信息', value: room.relatedInfo },
        { label: '备注', value: room.remark },
        { label: '房间类型', value: room.roomType },
        { label: '房间风格', value: room.roomStyle },
        { label: '房间朝向', value: room.direction },
        { label: '是否带窗', value: room.hasWindow },
        { label: '房间状态', value: room.status },
        { label: '月嫂姓名', value: room.maternityNurse },
        { label: '服务时间', value: room.serviceAt }
      ]
    },
    currentRecords() {
      const room = this.room || {}
      return (room.stays || []).filter(item => item.status === '已入住').map(item => ({
        ...item,
        room: room.room,
        operation: '—'
      }))
    },
    pastRecords() {
      return (this.room && this.room.pastStays) || []
    },
    futureRecords() {
      const room = this.room || {}
      return (room.stays || []).filter(item => item.status === '已订房').map(item => ({
        ...item,
        room: room.room,
        roomType: room.roomType,
        roomStyle: room.roomStyle,
        roomStatus: '已订房',
        operation: '—'
      }))
    }
  },
  watch: {
    visible(value) {
      if (value) this.activeTab = 'current'
    }
  }
}
</script>

<style lang="scss" scoped>
.booking-room-title { margin: -4px 0 14px; color: #26354c; text-align: center; font-size: 18px; }
.current-stay-panel { margin-bottom: 18px; }
.current-stay-panel h3 { margin: 0; padding: 10px 14px; color: #fff; background: #ec6f93; font-size: 14px; }
.current-stay-grid { display: grid; grid-template-columns: repeat(4, minmax(210px, 1fr)); border-top: 1px solid #ebeef5; border-left: 1px solid #ebeef5; }
.current-stay-grid > div { display: grid; grid-template-columns: 105px 1fr; min-height: 44px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.current-stay-grid span { padding: 12px 9px; color: #677489; background: #f7f9fb; }
.current-stay-grid strong { padding: 12px 9px; color: #344257; font-weight: 500; }
.current-stay-grid strong.is-danger { color: #e24f58; font-size: 16px; font-weight: 800; }
.current-stay-grid strong.is-money { color: #d75d67; font-weight: 700; }
.room-record-tabs ::v-deep .el-tabs__item.is-active { color: #fff; background: #ec6f93; }
.room-record-tabs ::v-deep .el-table th { color: #3f4c5d; background: #eeeeef; }

@media (max-width: 1180px) {
  .current-stay-grid { grid-template-columns: repeat(2, minmax(240px, 1fr)); }
}
</style>
