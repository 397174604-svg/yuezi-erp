<template>
  <view class="screen">
    <view class="topbar"><view class="brand"><text class="logo">☾</text><text class="nm">奇德芬芳</text></view><view class="avatar">{{ me.avatar }}</view></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">午安，{{ me.name }}<text class="sm">六月廿五 · 在住宝妈 {{ kpis.inhouse }} 位</text></view>

        <view class="kpis">
          <view class="k"><text class="num">{{ kpis.inhouse }}</text><text class="cap">在住</text></view>
          <view class="k br"><text class="num">{{ kpis.rounds }}</text><text class="cap">待巡房</text></view>
          <view class="k br"><text class="num">{{ kpis.follow }}</text><text class="cap">待跟进</text></view>
        </view>

        <view class="kgrid">
          <view class="kt" v-for="g in grid" :key="g.k" @tap="toSub(g.k)"><text class="c">{{ g.c }}</text><text class="t">{{ g.t }}</text><text class="s">{{ g.s }}</text></view>
        </view>

        <view class="sechead"><text class="l">待巡房</text><text class="more" @tap="toRound">全部 ›</text></view>
        <view class="yz-card" v-for="c in inhouse" :key="c.id" @tap="toClient(c.id)">
          <view class="mom">
            <view class="pic">{{ c.avatar }}</view>
            <view class="info"><text class="cn">{{ c.name }} <text class="rm">{{ c.room }} · {{ c.roomType }}</text></text>
              <view class="tags"><text v-for="t in c.tags" :key="t" :class="['yz-tag', t==='VIP'?'yz-tag--solid':'']">{{ t }}</text></view></view>
            <text class="go">去巡房</text>
          </view>
          <view class="subline"><text class="moon" v-if="c.moon">☾ 月子第 {{ c.moon.day }} / {{ c.moon.total }} 天</text><text class="ago">上次巡房 {{ c.lastRound }}</text></view>
        </view>

        <view class="sechead"><text class="l">销售漏斗 · 本月</text><text class="more">报表 ›</text></view>
        <view class="yz-card funnel">
          <view class="step"><text class="v">{{ funnel.leads }}</text><text class="fc">线索</text></view><text class="arr">›</text>
          <view class="step"><text class="v">{{ funnel.visits }}</text><text class="fc">到访</text></view><text class="arr">›</text>
          <view class="step"><text class="v">{{ funnel.signed }}</text><text class="fc">签单</text></view><text class="arr">›</text>
          <view class="step"><text class="v">{{ funnel.visits ? Math.round(funnel.signed / funnel.visits * 100) : 0 }}%</text><text class="fc">转化</text></view>
        </view>
      </view>
    </scroll-view>
  </view>
  <demo-tabbar end="staff" active="home/home" />
</template>

<script>
import { GRID } from '@/common/staff/data.js'
import { loadDashboard } from '@/common/staff/remote.js'
export default {
  data() {
    const m = getApp().globalData.data
    return { me: m.me, kpis: m.kpis, funnel: m.funnel, clients: m.clients, grid: GRID }
  },
  async onLoad() {
    const d = await loadDashboard() // 页面自取真实后端数据（不依赖 onLaunch 时序）
    this.me = d.me; this.kpis = d.kpis; this.funnel = d.funnel; this.clients = d.clients
  },
  computed: { inhouse() { return this.clients.filter(c => c.stage === '在住') } },
  methods: {
    toSub(k) { uni.navigateTo({ url: '/pages/staff/sub/sub?key=' + k }) },
    toClient(id) { uni.navigateTo({ url: '/pages/staff/client/client?id=' + id }) },
    toRound() { uni.reLaunch({ url: '/pages/staff/round/round' }) }
  }
}
</script>

<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 40rpx 12rpx; }
.brand { display: flex; align-items: center; } .logo { color: $gold; font-size: 34rpx; margin-right: 10rpx; }
.nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 26rpx; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.kpis { display: flex; background: $paper; border: 1rpx solid $hair; border-radius: 36rpx; margin-top: 32rpx; }
.kpis .k { flex: 1; text-align: center; padding: 30rpx 8rpx; position: relative; } .kpis .br::before { content: ''; position: absolute; left: 0; top: 22%; height: 56%; width: 1rpx; background: $hair; }
.kpis .num { font-family: $font-display; font-weight: 600; font-size: 58rpx; color: $gold-deep; line-height: 1; } .kpis .cap { display: block; font-size: 22rpx; color: $ink-2; margin-top: 12rpx; }
.kgrid { display: flex; flex-wrap: wrap; gap: 18rpx; margin-top: 32rpx; }
.kt { width: calc(25% - 14rpx); box-sizing: border-box; background: $paper; border: 1rpx solid $hair; border-radius: 28rpx; padding: 22rpx 8rpx; text-align: center; }
.kt .c { font-family: $font-cn-serif; font-size: 34rpx; color: $gold-deep; } .kt .t { display: block; font-size: 22rpx; font-weight: 500; margin-top: 8rpx; } .kt .s { display: block; font-size: 18rpx; color: $ink-3; margin-top: 4rpx; }
.sechead { display: flex; align-items: baseline; justify-content: space-between; margin: 44rpx 4rpx 24rpx; }
.sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; } .sechead .more { font-size: 22rpx; color: $gold-deep; }
.mom { display: flex; align-items: center; }
.mom .pic { width: 92rpx; height: 92rpx; border-radius: 28rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; color: $gold-deep; font-size: 34rpx; }
.mom .info { flex: 1; margin-left: 24rpx; } .mom .cn { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; } .mom .cn .rm { font-size: 22rpx; color: $ink-3; font-weight: 400; margin-left: 10rpx; }
.mom .tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 14rpx; } .mom .go { font-size: 24rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 14rpx 24rpx; border-radius: 60rpx; }
.subline { display: flex; justify-content: space-between; border-top: 1rpx solid $hair; margin-top: 22rpx; padding-top: 20rpx; font-size: 22rpx; color: $ink-2; } .subline .ago { color: $ink-3; }
.funnel { display: flex; align-items: center; justify-content: space-between; } .funnel .step { text-align: center; flex: 1; } .funnel .v { font-family: $font-display; font-size: 46rpx; color: $gold-deep; font-weight: 600; } .funnel .fc { display: block; font-size: 20rpx; color: $ink-3; margin-top: 6rpx; } .funnel .arr { color: $hair-s; }

.screen, .page, .wrap { padding-bottom: 140rpx; }
</style>
