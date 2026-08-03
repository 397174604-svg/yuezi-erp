<template>
  <div class="room-segment">
    <div class="segment-date">
      <span><small>入住</small>{{ room.startLabel }}</span>
      <i class="el-icon-right" />
      <span><small>退房</small>{{ room.endLabel }}</span>
    </div>
    <div class="segment-main">
      <strong>{{ room.room }}</strong>
      <span class="room-type" :title="room.roomStyle || room.roomType">{{ room.roomStyle || room.roomType }}</span>
      <span class="stay-days">{{ room.days }}天</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RoomRecommendationSegment',
  props: {
    room: {
      type: Object,
      required: true
    }
  }
}
</script>

<style lang="scss" scoped>
.room-segment {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid #eadfcd;
  border-left: 4px solid #c8a364;
  border-radius: 9px;
  background: linear-gradient(135deg, #fffaf3, #fff);
}
.segment-date {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #66758a;
  font-size: 12px;
  white-space: nowrap;
}
.segment-date span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.segment-date small {
  color: #a08b69;
  font-size: 10px;
  font-weight: 500;
}
.segment-date i { color: #c5a56e; font-size: 12px; }
.segment-main {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}
.segment-main strong {
  color: #18283d;
  font-size: 21px;
  line-height: 1;
}
.room-type {
  overflow: hidden;
  color: #58677b;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stay-days {
  padding: 3px 7px;
  border-radius: 10px;
  color: #8d6b34;
  font-size: 11px;
  background: #f5ead7;
}
</style>
