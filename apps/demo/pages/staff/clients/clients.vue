<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">客户追踪<text class="sm">移动办公 · 标签 · 漏斗 · 跟进全在手机</text></view>
        <view class="filters"><text v-for="f in stages" :key="f" :class="['chip', stage===f?'on':'']" @tap="stage=f">{{ f }}</text></view>
        <view class="yz-card lrow" v-for="c in shown" :key="c.id" @tap="toClient(c.id)">
          <view class="pic">{{ c.avatar }}</view>
          <view class="info"><text class="cn">{{ c.name }} <text class="rm">{{ c.room!=='—'? c.room : c.phone }}</text></text>
            <view class="tags"><text v-for="t in c.tags" :key="t" :class="['yz-tag', t==='VIP'?'yz-tag--solid':'']">{{ t }}</text></view></view>
          <text :class="['stage', c.stage==='在住'?'on':'']">{{ c.stage }}</text>
        </view>
        <view v-if="!shown.length" class="empty">暂无客户</view>
      </view>
    </scroll-view>
  </view>
  <demo-tabbar end="staff" active="clients/clients" />
</template>
<script>
import { loadClients } from '@/common/staff/remote.js'
export default {
  data() { return { stage: '全部', stages: ['全部', '在住', '签单', '到访', '线索'], clients: getApp().globalData.data.clients } },
  async onLoad() { const live = await loadClients(); if (live) this.clients = live },
  computed: { shown() { return this.stage === '全部' ? this.clients : this.clients.filter(c => c.stage === this.stage) } },
  methods: { toClient(id) { uni.navigateTo({ url: '/pages/staff/client/client?id=' + id }) } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.filters { display: flex; flex-wrap: wrap; gap: 16rpx; margin: 28rpx 0 8rpx; }
.chip { font-size: 24rpx; padding: 14rpx 28rpx; border-radius: 40rpx; border: 1rpx solid $hair; color: $ink-2; background: $paper; } .chip.on { background: $ink; color: $gold-soft; border: none; }
.lrow { display: flex; align-items: center; margin-top: 22rpx; }
.lrow .pic { width: 84rpx; height: 84rpx; border-radius: 24rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; color: $gold-deep; font-size: 32rpx; }
.lrow .info { flex: 1; margin-left: 22rpx; } .lrow .cn { font-family: $font-cn-serif; font-size: 29rpx; font-weight: 600; } .lrow .cn .rm { font-size: 22rpx; color: $ink-3; font-weight: 400; margin-left: 10rpx; }
.lrow .tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 12rpx; }
.stage { font-size: 20rpx; padding: 8rpx 16rpx; border-radius: 12rpx; background: rgba(184,148,90,.14); color: $gold-deep; } .stage.on { background: rgba(110,139,106,.16); color: #577053; }
.empty { text-align: center; color: $ink-3; font-size: 24rpx; padding: 80rpx 0; }

.screen, .page, .wrap { padding-bottom: 140rpx; }
</style>
