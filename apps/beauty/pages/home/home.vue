<template>
  <view class="screen">
    <view class="demo-flag">演示数据</view>
    <!-- 顶栏 -->
    <view class="topbar">
      <view class="brand">
        <text class="logo">☾</text><text class="nm">{{ brand.name }} · 科颜</text>
      </view>
      <view class="avatar">店</view>
    </view>

    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">{{ store.name }}<text class="sm">店长 {{ store.manager }}</text></view>

        <!-- 营业额（暗夜金箔卡） -->
        <view class="turn">
          <text class="e">今日营业额 · TURNOVER</text>
          <view class="b">¥ {{ (kpis.turnover || 0).toLocaleString() }}</view>
          <view class="rr">
            <text>预约 <text class="hl">{{ kpis.appts || 0 }}</text></text>
            <text>会员 <text class="hl">{{ kpis.members || 0 }}</text></text>
          </view>
        </view>

        <!-- 快捷宫格 -->
        <view class="g4">
          <view class="qa lead" @tap="toCashier"><text class="ic">¥</text><view><text class="t">收银开单</text><text class="s">快速结账</text></view></view>
          <view class="qa" @tap="toSub('apptBoard')"><text class="ic">⌧</text><view><text class="t">预约排空</text><text class="s">项目·排班</text></view></view>
          <view class="qa" @tap="toCustomers"><text class="ic">⚇</text><view><text class="t">客户管理</text><text class="s">筛选·追踪</text></view></view>
          <view class="qa" @tap="toSub('itemSettings')"><text class="ic">▢</text><view><text class="t">品项设置</text><text class="s">价格·提成</text></view></view>
        </view>

        <!-- 今日预约 -->
        <view class="sechead"><text class="l">今日预约</text><text class="more" @tap="toSub('apptBoard')">排空表 ›</text></view>
        <view class="yz-card">
          <view class="tl-row" v-for="(a,i) in appts" :key="i">
            <text class="tm">{{ a.time }}</text>
            <view class="bd"><text class="t">{{ a.project }}</text><text class="s">{{ a.customer }} · 技师 {{ a.tech }}</text></view>
            <text class="st">{{ a.status }}</text>
          </view>
        </view>

        <!-- 在岗技师 -->
        <view class="sechead"><text class="l">在岗技师</text><text class="more">排班 ›</text></view>
        <view class="techrow">
          <view class="tk" v-for="t in techs" :key="t.name"><view class="p"></view><text class="n">{{ t.name }}</text><text class="x">{{ t.status }}</text></view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { loadDashboard } from '@/common/remote.js'
export default {
  data() {
    const m = getApp().globalData.data
    return { store: m.store, kpis: m.kpis, appts: m.appointments, techs: m.techs, brand: m.brand || { name: '奇德芬芳' } }
  },
  async onLoad() {
    const d = await loadDashboard() // 页面自取真实后端数据（不依赖 onLaunch 时序）
    this.store = d.store; this.kpis = d.kpis; this.appts = d.appointments; this.techs = d.techs; this.brand = d.brand || this.brand
  },
  methods: {
    toCashier() { uni.switchTab({ url: '/pages/cashier/cashier' }) },
    toCustomers() { uni.switchTab({ url: '/pages/customers/customers' }) },
    toSub(key) { uni.navigateTo({ url: '/pages/sub/sub?key=' + key }) }
  }
}
</script>

<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 40rpx 16rpx; }
.brand { display: flex; align-items: center; }
.logo { color: $gold; font-size: 34rpx; margin-right: 12rpx; }
.nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 26rpx; }
.scroll { flex: 1; }
.pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; }
.greet .sm { display: block; font-family: $font-sans; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }

.turn { margin-top: 32rpx; background: radial-gradient(120% 130% at 100% 0%, #3B342A, #2A2620); border-radius: 36rpx; padding: 36rpx; }
.turn .e { font-size: 22rpx; letter-spacing: 4rpx; color: $gold-soft; }
.turn .b { font-family: $font-display; font-size: 88rpx; font-weight: 600; color: #EAD3A0; line-height: 1; margin-top: 16rpx; }
.turn .rr { display: flex; gap: 32rpx; margin-top: 28rpx; font-size: 23rpx; color: #D9CBB0; flex-wrap: wrap; }
.turn .hl { color: #EAD3A0; font-family: $font-display; font-size: 30rpx; }
.turn .growth { margin-left: auto; color: $gold-soft; }

.g4 { display: flex; flex-wrap: wrap; gap: 22rpx; margin-top: 32rpx; }
.qa { width: calc(50% - 11rpx); box-sizing: border-box; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; padding: 30rpx 28rpx; display: flex; align-items: center; }
.qa .ic { width: 80rpx; height: 80rpx; border-radius: 24rpx; border: 1rpx solid $hair-s; display: flex; align-items: center; justify-content: center; color: $gold-deep; font-size: 38rpx; margin-right: 22rpx; }
.qa.lead .ic { background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; border: none; }
.qa .t { font-size: 26rpx; font-weight: 500; }
.qa .s { display: block; font-size: 20rpx; color: $ink-3; margin-top: 4rpx; }

.sechead { display: flex; align-items: baseline; justify-content: space-between; margin: 44rpx 4rpx 24rpx; }
.sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; }
.sechead .more { font-size: 22rpx; color: $gold-deep; }

.tl-row { display: flex; padding: 22rpx 0; border-bottom: 1rpx solid $hair; }
.tl-row:last-child { border-bottom: 0; }
.tl-row .tm { font-family: $font-display; font-size: 34rpx; color: $gold-deep; width: 96rpx; }
.tl-row .bd { flex: 1; }
.tl-row .bd .t { font-size: 27rpx; font-weight: 500; }
.tl-row .bd .s { display: block; font-size: 22rpx; color: $ink-3; margin-top: 6rpx; }
.tl-row .st { align-self: center; font-size: 20rpx; padding: 8rpx 18rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }

.techrow { display: flex; gap: 18rpx; }
.tk { flex: 1; text-align: center; background: $paper; border: 1rpx solid $hair; border-radius: 24rpx; padding: 20rpx 8rpx; }
.tk .p { width: 60rpx; height: 60rpx; border-radius: 50%; margin: 0 auto 10rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; }
.tk .n { font-size: 22rpx; font-weight: 500; }
.tk .x { display: block; font-size: 19rpx; color: $gold-deep; margin-top: 4rpx; }

.demo-flag { position: fixed; top: calc(env(safe-area-inset-top) + 10rpx); left: 50%; transform: translateX(-50%); z-index: 999; font-size: 20rpx; color: #8C6A36; background: rgba(231,212,172,.92); border: 1rpx solid rgba(184,148,90,.42); padding: 4rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 16rpx -10rpx rgba(74,56,24,.4); }
</style>
