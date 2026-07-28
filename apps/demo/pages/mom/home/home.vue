<template>
  <view class="screen">
    <view class="topbar"><view class="brand"><text class="logo">☾</text><text class="nm">奇德芬芳</text></view><view class="avatar">{{ me.avatar }}</view></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">{{ me.name }}，悦享此刻<text class="sm">愿您与宝贝，安睡如月</text></view>

        <view class="hero">
          <text class="eb">调养进程 · NURTURE</text>
          <view class="moondisc"><view class="shadow"></view></view>
          <view class="fr"><text class="b">{{ journey.day }}</text><text class="d"> / {{ journey.total }}</text></view>
          <text class="lb">月子第 {{ journey.day }} 天 · {{ journey.phase }}</text>
        </view>

        <view class="balance">
          <view class="b" @tap="toSub('mealCard')"><text class="c">套餐余额</text><text class="v"><text class="cur">¥</text>{{ balance.pkg.toLocaleString() }}</text></view>
          <view class="b" @tap="toSub('mealCard')"><text class="c">护理卡</text><text class="v">{{ balance.careCard }}<text class="cur"> 次</text></text></view>
        </view>

        <view class="sechead"><text class="l">今日安排</text><text class="more" @tap="toDiet">膳食 ›</text></view>
        <view class="yz-card">
          <view class="tl" v-for="(s,i) in schedule" :key="i"><text class="tm">{{ s.time }}</text>
            <view class="bd"><text class="t">{{ s.title }}</text><text class="ss">{{ s.sub }}</text></view><text class="st">{{ s.status }}</text></view>
        </view>

        <view class="promo" @tap="toSub('points')"><view class="ic"></view><view><text class="pt">{{ promo.title }}</text><text class="ps">{{ promo.sub }}</text></view></view>
      </view>
    </scroll-view>
  </view>
  <demo-tabbar end="mom" active="home/home" />
</template>
<script>
import { loadDashboard } from '@/common/mom/remote.js'
export default {
  data() { const m = getApp().globalData.data; return { me: m.me, journey: m.journey, balance: m.balance, schedule: m.schedule, promo: m.promo } },
  async onLoad() {
    const d = await loadDashboard() // 页面自取真实后端数据（不依赖 onLaunch 时序）
    this.me = d.me; this.journey = d.journey; this.balance = d.balance; this.schedule = d.schedule; this.promo = d.promo
  },
  methods: { toSub(k) { uni.navigateTo({ url: '/pages/mom/sub/sub?key=' + k }) }, toDiet() { uni.reLaunch({ url: '/pages/mom/diet/diet' }) } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 40rpx 12rpx; }
.brand { display: flex; align-items: center; } .logo { color: $gold; font-size: 34rpx; margin-right: 10rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 26rpx; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.hero { margin-top: 28rpx; background: radial-gradient(120% 120% at 50% 0%, #2A2620, #3B342A 55%, #4A4034); border-radius: 44rpx; padding: 48rpx 40rpx 40rpx; text-align: center; }
.hero .eb { font-size: 21rpx; letter-spacing: 6rpx; color: $gold-soft; }
.moondisc { width: 168rpx; height: 168rpx; border-radius: 50%; background: #E3C892; position: relative; overflow: hidden; margin: 20rpx auto 8rpx; }
.moondisc .shadow { position: absolute; width: 138rpx; height: 168rpx; right: -16rpx; top: 0; border-radius: 50%; background: #1f1a14; }
.hero .fr { margin-top: 8rpx; } .hero .fr .b { font-family: $font-display; font-size: 110rpx; font-weight: 600; color: #EAD3A0; } .hero .fr .d { font-family: $font-display; font-size: 44rpx; color: #EAD3A0; opacity: .7; }
.hero .lb { display: block; color: #D9CBB0; font-size: 24rpx; margin-top: 12rpx; letter-spacing: 3rpx; }
.balance { display: flex; gap: 22rpx; margin-top: 28rpx; }
.balance .b { flex: 1; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; padding: 30rpx 28rpx; } .balance .c { font-size: 22rpx; color: $ink-3; } .balance .v { display: block; font-family: $font-display; font-size: 52rpx; color: $gold-deep; font-weight: 600; margin-top: 10rpx; } .balance .cur { font-size: 26rpx; }
.sechead { display: flex; align-items: baseline; justify-content: space-between; margin: 44rpx 4rpx 24rpx; } .sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; } .sechead .more { font-size: 22rpx; color: $gold-deep; }
.tl { display: flex; padding: 22rpx 0; border-bottom: 1rpx solid $hair; } .tl:last-child { border-bottom: 0; } .tl .tm { font-family: $font-display; font-size: 34rpx; color: $gold-deep; width: 96rpx; } .tl .bd { flex: 1; } .tl .t { font-size: 27rpx; font-weight: 500; } .tl .ss { display: block; font-size: 21rpx; color: $ink-3; margin-top: 6rpx; } .tl .st { align-self: center; font-size: 20rpx; padding: 8rpx 18rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }
.promo { display: flex; align-items: center; margin-top: 28rpx; border: 1rpx solid $hair-s; border-radius: 32rpx; padding: 28rpx 32rpx; background: linear-gradient(105deg, rgba(231,212,172,.22), rgba(255,255,255,.4)); } .promo .ic { width: 72rpx; height: 72rpx; border-radius: 20rpx; background: linear-gradient(135deg,#E9D4A4,#9C7838); margin-right: 24rpx; } .promo .pt { font-family: $font-cn-serif; font-size: 27rpx; font-weight: 600; } .promo .ps { display: block; font-size: 21rpx; color: $ink-2; margin-top: 6rpx; }

.screen, .page, .wrap { padding-bottom: 140rpx; }
</style>
