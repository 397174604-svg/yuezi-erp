<template>
  <div class="room-segment">
    <div class="segment-date">
      <span>{{ room.startLabel }}</span>
      <span>～</span>
      <span>{{ room.endLabel }}</span>
    </div>
    <strong>{{ room.room }}</strong>
    <div class="segment-meta">
      <span>{{ room.roomType }}</span>
      <span>{{ room.days }}天</span>
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
  width: 144px;
  padding: 15px 20px;
  border-left: 2px solid #e0e0e0;
  border-radius: 5px;
  background: #fff9f1;
  text-align: center;
}
.segment-date,
.segment-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 12px;
  white-space: nowrap;
}
.room-segment > strong {
  display: block;
  clear: both;
  padding: 7px 0;
  color: #000;
  font-size: 18px;
}
.segment-meta span:first-child {
  max-width: 78px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
