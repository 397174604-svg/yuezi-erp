<template>
  <view class="screen">
    <view class="topbar"><view class="brand"><text class="logo">☾</text><text class="nm">{{ brand.name }}</text></view><view class="avatar">{{ me.avatar }}</view></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">{{ me.name }}，悦享此刻<text class="sm">愿您与宝贝，安睡如月</text></view>

        <view v-if="onboarding.needsProfile" class="onboarding" @tap="toProfile">
          <view><text class="ot">欢迎加入奇德芬芳</text><text class="os">完善姓名和服务阶段，获得更贴合您与宝宝的照护内容</text></view><text class="oa">去完善 ›</text>
        </view>

        <view v-if="!onboarding.isNew" class="hero">
          <text class="eb">调养进程 · NURTURE</text>
          <view class="moondisc"><view class="shadow"></view></view>
          <view class="fr"><text class="b">{{ journey.day }}</text><text class="d"> / {{ journey.total }}</text></view>
          <text class="lb">月子第 {{ journey.day }} 天 · {{ journey.phase }}</text>
        </view>

        <view class="balance">
          <view class="b" @tap="toSub('mealCard')"><text class="c">套餐余额</text><text class="v"><text class="cur">¥</text>{{ balance.pkg.toLocaleString() }}</text></view>
          <view class="b" @tap="toSub('mealCard')"><text class="c">护理卡</text><text class="v">{{ balance.careCard }}<text class="cur"> 次</text></text></view>
        </view>

          <view class="sechead"><text class="l">今日安排</text><text class="more" @tap="toRooms">查看房型 ›</text></view>
        <view class="yz-card">
          <view class="tl" v-for="(s,i) in schedule" :key="i"><text class="tm">{{ s.time }}</text>
            <view class="bd"><text class="t">{{ s.title }}</text><text class="ss">{{ s.sub }}</text></view><text class="st">{{ s.status }}</text></view>
          <view v-if="!schedule.length" class="empty">暂无服务安排<text>需要帮助可联系门店顾问</text></view>
        </view>

        <view class="promo" @tap="toSub('points')"><view class="ic"></view><view><text class="pt">{{ promo.title }}</text><text class="ps">{{ promo.sub }}</text></view></view>
      </view>
    </scroll-view>
  </view>
</template>
<script>
import { loadDashboard } from '@/common/remote.js'
export default {
  data() { const m = getApp().globalData.data; return { me: m.me, journey: m.journey, onboarding: m.onboarding || { isNew: false, needsProfile: false }, balance: m.balance, schedule: m.schedule, promo: m.promo, brand: m.brand || { name: '奇德芬芳' } } },
  async onShow() {
    const d = await loadDashboard() // 页面自取真实后端数据（不依赖 onLaunch 时序）
    this.me = d.me; this.journey = d.journey; this.onboarding = d.onboarding || this.onboarding; this.balance = d.balance; this.schedule = d.schedule; this.promo = d.promo; this.brand = d.brand || this.brand
  },
  methods: { toSub(k) { uni.navigateTo({ url: '/pages/sub/sub?key=' + k }) }, toRooms() { uni.switchTab({ url: '/pages/rooms/reserve' }) }, toProfile() { uni.navigateTo({ url: '/pages/profile/onboarding' }) } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 40rpx 12rpx; }
.brand { display: flex; align-items: center; } .logo { color: $gold; font-size: 34rpx; margin-right: 10rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: $foil; color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 26rpx; box-shadow: 0 10rpx 28rpx -16rpx rgba(94,74,38,.58); }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.onboarding { display: flex; align-items: center; justify-content: space-between; margin-top: 26rpx; padding: 28rpx 30rpx; border-radius: 30rpx; border: 1rpx solid $platinum; background: $platinum-foil; box-shadow: $shadow-soft; }.onboarding .ot { display: block; font-family: $font-cn-serif; font-size: 27rpx; color: $gold-deep; }.onboarding .os { display: block; max-width: 430rpx; color: $ink-2; font-size: 21rpx; margin-top: 5rpx; }.onboarding .oa { color: $gold-deep; font-size: 23rpx; white-space: nowrap; margin-left: 12rpx; }
.hero { position: relative; margin-top: 28rpx; overflow: hidden; background: $platinum-foil; border: 1rpx solid $platinum; border-radius: 44rpx; padding: 48rpx 40rpx 40rpx; text-align: center; box-shadow: $shadow-soft; }
.hero::before { content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 20% 0%, rgba(255,255,255,.92), transparent 44%), linear-gradient(120deg, transparent 45%, rgba(195,165,101,.10)); pointer-events: none; }
.hero .eb { position: relative; font-size: 21rpx; letter-spacing: 6rpx; color: $gold-deep; }
.moondisc { width: 168rpx; height: 168rpx; border-radius: 50%; background: $foil; position: relative; overflow: hidden; margin: 20rpx auto 8rpx; box-shadow: 0 0 0 1rpx $hair-s, 0 18rpx 38rpx -24rpx rgba(94,74,38,.58); }
.moondisc .shadow { position: absolute; width: 138rpx; height: 168rpx; right: -16rpx; top: 0; border-radius: 50%; background: #F8F7F3; box-shadow: -10rpx 0 24rpx rgba(135,109,62,.12); }
.hero .fr { position: relative; margin-top: 8rpx; } .hero .fr .b { font-family: $font-display; font-size: 110rpx; font-weight: 600; color: $gold-deep; } .hero .fr .d { font-family: $font-display; font-size: 44rpx; color: $gold-deep; opacity: .58; }
.hero .lb { position: relative; display: block; color: $ink-2; font-size: 24rpx; margin-top: 12rpx; letter-spacing: 3rpx; }
.balance { display: flex; gap: 22rpx; margin-top: 28rpx; }
.balance .b { flex: 1; background: rgba(255,255,255,.96); border: 1rpx solid $hair; border-radius: 32rpx; padding: 30rpx 28rpx; box-shadow: $shadow-soft; } .balance .c { font-size: 22rpx; color: $ink-3; } .balance .v { display: block; font-family: $font-display; font-size: 52rpx; color: $gold-deep; font-weight: 600; margin-top: 10rpx; } .balance .cur { font-size: 26rpx; }
.sechead { display: flex; align-items: baseline; justify-content: space-between; margin: 44rpx 4rpx 24rpx; } .sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; } .sechead .more { font-size: 22rpx; color: $gold-deep; }
.tl { display: flex; padding: 22rpx 0; border-bottom: 1rpx solid $hair; } .tl:last-child { border-bottom: 0; } .tl .tm { font-family: $font-display; font-size: 34rpx; color: $gold-deep; width: 96rpx; } .tl .bd { flex: 1; } .tl .t { font-size: 27rpx; font-weight: 500; } .tl .ss { display: block; font-size: 21rpx; color: $ink-3; margin-top: 6rpx; } .tl .st { align-self: center; font-size: 20rpx; padding: 8rpx 18rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }
.empty { text-align: center; color: $ink-2; font-size: 25rpx; padding: 36rpx 10rpx; }.empty text { display: block; color: $ink-3; font-size: 21rpx; margin-top: 6rpx; }
.promo { display: flex; align-items: center; margin-top: 28rpx; border: 1rpx solid $platinum; border-radius: 32rpx; padding: 28rpx 32rpx; background: $platinum-foil; box-shadow: $shadow-soft; } .promo .ic { width: 72rpx; height: 72rpx; border-radius: 20rpx; background: $foil; margin-right: 24rpx; } .promo .pt { font-family: $font-cn-serif; font-size: 27rpx; font-weight: 600; } .promo .ps { display: block; font-size: 21rpx; color: $ink-2; margin-top: 6rpx; }

</style>
