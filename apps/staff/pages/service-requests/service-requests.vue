<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">到店服务待办</text><text class="refresh" @tap="load">刷新</text></view>
    <view class="tabs"><view v-for="x in filters" :key="x" :class="['tab',filter===x&&'on']" @tap="filter=x;load()">{{x||'全部'}}</view></view>
    <scroll-view scroll-y class="scroll"><view class="pad">
      <view v-for="r in rows" :key="r.request_id" class="card">
        <view class="line"><text class="kind">{{labels[r.request_type]||r.request_type}}</text><text class="status">{{r.status}}</text></view>
        <text class="customer">{{r.customer_name}}<text v-if="r.room_no"> · 房间 {{r.room_no}}</text></text>
        <text class="meta">{{r.store_name||'奇德芬芳'}} · {{fmt(r.created_at)}}</text>
        <text v-if="r.content" class="content">{{r.content}}</text>
        <text v-if="r.preferred_time" class="preferred">期望时间：{{r.preferred_time}}</text>
        <view class="actions">
          <button v-if="r.status==='待接单'" size="mini" @tap="setStatus(r,'已接单')">接单</button>
          <button v-if="r.status==='已接单'" size="mini" @tap="setStatus(r,'处理中')">开始处理</button>
          <button v-if="r.status==='已接单'||r.status==='处理中'" class="done" size="mini" @tap="setStatus(r,'已完成')">完成</button>
        </view>
      </view>
      <view v-if="!rows.length&&!loading" class="empty">暂无待办服务</view>
    </view></scroll-view>
  </view>
</template>
<script>
import { loadCustomerServiceRequests, updateCustomerServiceRequest } from '@/common/remote.js'
export default{
  data(){return{loading:false,filter:'',filters:['','待接单','已接单','处理中','已完成'],rows:[],labels:{arrival_checkin:'到店签到',concierge:'呼叫管家',housekeeping:'客房清洁',meal_request:'膳食需求',baby_care:'宝宝护理',room_booking:'房型预订',rehab_booking:'产康预约'}}},
  onShow(){this.load()},onPullDownRefresh(){this.load().finally(()=>uni.stopPullDownRefresh())},
  methods:{back(){uni.navigateBack()},fmt(v){return String(v||'').replace('T',' ').slice(0,16)},async load(){this.loading=true;try{this.rows=await loadCustomerServiceRequests(this.filter)}catch(e){uni.showToast({title:e.message||'加载失败',icon:'none'})}finally{this.loading=false}},async setStatus(r,status){try{await updateCustomerServiceRequest(r.request_id,status);r.status=status;uni.showToast({title:'已更新',icon:'success'})}catch(e){uni.showToast({title:e.message||'更新失败',icon:'none'})}}}
}
</script>
<style lang="scss" scoped>
.page{height:100vh;background:$ivory;display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 12rpx;display:flex;align-items:center;justify-content:space-between}.back{font-size:52rpx;color:$gold-deep;width:60rpx}.title{font-family:$font-cn-serif;font-size:31rpx}.refresh{width:60rpx;text-align:right;color:$gold-deep;font-size:22rpx}.tabs{display:flex;gap:12rpx;padding:18rpx 28rpx;overflow-x:auto}.tab{white-space:nowrap;padding:10rpx 20rpx;border:1rpx solid $hair;border-radius:30rpx;color:$ink-3;font-size:21rpx}.tab.on{background:$gold-deep;color:#fff}.scroll{flex:1}.pad{padding:14rpx 30rpx 80rpx}.card{background:#fff;border:1rpx solid $hair;border-radius:28rpx;padding:28rpx;margin-bottom:18rpx}.line{display:flex;justify-content:space-between}.kind{font-family:$font-cn-serif;font-size:29rpx}.status{font-size:21rpx;color:$gold-deep}.customer,.meta,.content,.preferred{display:block}.customer{font-size:25rpx;margin-top:8rpx}.meta{font-size:20rpx;color:$ink-3;margin-top:4rpx}.content{font-size:24rpx;margin-top:16rpx;background:$ivory;padding:16rpx;border-radius:16rpx}.preferred{font-size:21rpx;color:$ink-2;margin-top:10rpx}.actions{display:flex;justify-content:flex-end;gap:12rpx;margin-top:20rpx}.actions button{margin:0;background:#F2E5CC;color:$gold-deep;border:0}.actions button.done{background:$gold-deep;color:#fff}.actions button::after{border:0}.empty{text-align:center;color:$ink-3;padding:160rpx 20rpx}
</style>
