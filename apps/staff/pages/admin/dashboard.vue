<template>
  <view class="page"><view class="top"><text class="back" @tap="back">‹</text><text class="title">管理经营看板</text><text class="refresh" @tap="load">刷新</text></view>
    <scroll-view scroll-y class="scroll"><view class="pad">
      <view class="kpis">
        <view class="k"><text class="num">{{c.rooms.occupancyRate||0}}%</text><text>入住率</text></view>
        <view class="k"><text class="num">{{c.rooms.occupied||0}}/{{c.rooms.total||0}}</text><text>在住房间</text></view>
        <view class="k"><text class="num">{{c.customers.inHouse||0}}</text><text>在住客户</text></view>
      </view>
      <view class="card"><text class="head">经营收入</text><view class="metrics"><view><text class="v">¥{{money(c.revenue.today)}}</text><text>今日实收</text></view><view><text class="v">¥{{money(c.revenue.month)}}</text><text>本月实收</text></view><view><text class="v warn">¥{{money(c.revenue.due)}}</text><text>累计待收</text></view></view></view>
      <view class="card"><text class="head">未来 7 天趋势预测</text><text class="forecast">¥{{money(f.summary.nextWeekForecast)}}</text><text class="trend">较近 7 天 {{signed(f.summary.wowPct)}}%</text><text class="note">{{f.note||'趋势外推预测，非承诺'}}</text></view>
      <view class="card"><text class="head">今日待办</text><view class="rows"><text>今日预约</text><text class="strong">{{c.todayAppointments||0}}</text></view><view class="rows"><text>待审批</text><text class="strong">{{c.pendingApprovals||0}}</text></view><view class="rows"><text>月嫂在岗</text><text class="strong">{{c.nannyOnDuty||0}}</text></view></view>
      <view class="card"><text class="head">门店实收排名</text><view v-for="(s,i) in c.storeRanking" :key="s.storeId" class="rows"><text>{{i+1}}. {{s.storeName}}</text><text class="strong">¥{{money(s.turnover)}}</text></view><text v-if="!c.storeRanking.length" class="note">暂无经营数据</text></view>
      <text class="asof">数据时间：{{fmt(c.asOf)}}</text>
    </view></scroll-view>
  </view>
</template>
<script>
import { loadManagementDashboard } from '@/common/remote.js'
const EMPTY={rooms:{},customers:{},revenue:{},storeRanking:[]}
export default{data(){return{c:{...EMPTY},f:{summary:{}}}},onShow(){this.load()},methods:{back(){uni.navigateBack()},money(v){return Number(v||0).toLocaleString()},signed(v){const n=Number(v||0);return n>0?'+'+n:n},fmt(v){return String(v||'').replace('T',' ').slice(0,19)},async load(){try{const d=await loadManagementDashboard();this.c=d.cockpit||{...EMPTY};this.f=d.forecast||{summary:{}}}catch(e){uni.showToast({title:e.message||'加载失败',icon:'none'})}}}}
</script>
<style lang="scss" scoped>
.page{height:100vh;background:$ivory;display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 12rpx;display:flex;align-items:center;justify-content:space-between}.back{font-size:52rpx;color:$gold-deep;width:60rpx}.title{font-family:$font-cn-serif;font-size:31rpx}.refresh{width:60rpx;text-align:right;color:$gold-deep;font-size:22rpx}.scroll{flex:1}.pad{padding:20rpx 30rpx 100rpx}.kpis{display:flex;gap:14rpx}.k{flex:1;background:#fff;border:1rpx solid $hair;border-radius:24rpx;padding:24rpx 8rpx;text-align:center;font-size:20rpx;color:$ink-3}.num{display:block;font-family:$font-display;font-size:36rpx;color:$gold-deep;margin-bottom:8rpx}.card{background:#fff;border:1rpx solid $hair;border-radius:28rpx;padding:28rpx;margin-top:20rpx}.head{font-family:$font-cn-serif;font-size:29rpx}.metrics{display:flex;margin-top:22rpx}.metrics view{flex:1;text-align:center;font-size:20rpx;color:$ink-3}.v{display:block;font-size:28rpx;color:$gold-deep;margin-bottom:8rpx}.warn{color:#A04545}.forecast{display:block;font-family:$font-display;font-size:52rpx;color:$gold-deep;margin-top:18rpx}.trend{font-size:22rpx;color:$ink-2}.note,.asof{display:block;font-size:20rpx;color:$ink-3;margin-top:12rpx}.rows{display:flex;justify-content:space-between;padding:18rpx 0;border-bottom:1rpx solid $hair;font-size:23rpx}.rows:last-child{border-bottom:0}.strong{font-weight:500;color:$gold-deep}.asof{text-align:center;margin-top:24rpx}
</style>
