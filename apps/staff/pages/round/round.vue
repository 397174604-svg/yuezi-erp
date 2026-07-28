<template>
  <view class="screen">
    <view class="demo-flag">演示数据</view>
    <view class="topbar"><text class="nm">奇德芬芳</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">护理巡房<text class="sm">解放 iPad · 床边即记即传</text></view>
        <view class="yz-card" v-for="c in inhouse" :key="c.id">
          <view class="mom"><view class="pic">{{ c.avatar }}</view>
            <view class="info"><text class="cn">{{ c.name }} <text class="rm">{{ c.room }}</text></text>
              <text class="moon" v-if="c.moon">☾ 月子 {{ c.moon.day }}/{{ c.moon.total }} 天</text></view>
            <text class="go" @tap="start(c)">开始</text></view>
          <view class="items"><text class="yz-tag" v-for="it in items" :key="it">{{ it }}</text></view>
        </view>
        <view v-if="!inhouse.length" class="empty">暂无在住宝妈待巡房</view>
      </view>
    </scroll-view>
  </view>
</template>
<script>
import { loadClients } from '@/common/remote.js'
export default {
  data() { const m = getApp().globalData.data; return { clients: m.clients, items: m.roundItems } },
  async onLoad() { const live = await loadClients(); if (live) this.clients = live },
  computed: { inhouse() { return this.clients.filter(c => c.stage === '在住') } },
  methods: {
    // M-A：「开始」进结构化巡房工作台（宝妈 8 项 + 宝宝快捷日志 + 拍照，整包提交），替代原一键打卡
    start(c) {
      const room = (c.room && c.room !== '—') ? c.room : ''
      uni.navigateTo({ url: '/pages/round/workbench?customerId=' + c.customerId + '&name=' + encodeURIComponent(c.name || '') + '&room=' + encodeURIComponent(room) })
    }
  }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.empty { text-align: center; color: $ink-3; font-size: 24rpx; padding: 80rpx 0; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.mom { display: flex; align-items: center; } .mom .pic { width: 88rpx; height: 88rpx; border-radius: 26rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; color: $gold-deep; font-size: 32rpx; }
.mom .info { flex: 1; margin-left: 22rpx; } .mom .cn { font-family: $font-cn-serif; font-size: 29rpx; font-weight: 600; } .mom .cn .rm { font-size: 22rpx; color: $ink-3; font-weight: 400; margin-left: 10rpx; } .mom .moon { display: block; font-size: 21rpx; color: $ink-2; margin-top: 10rpx; }
.mom .go { font-size: 24rpx; color: #fff; background: linear-gradient(135deg,#E9D4A4,#9C7838); padding: 14rpx 30rpx; border-radius: 60rpx; }
.items { display: flex; flex-wrap: wrap; gap: 12rpx; border-top: 1rpx solid $hair; margin-top: 22rpx; padding-top: 20rpx; }

.demo-flag { position: fixed; top: calc(env(safe-area-inset-top) + 10rpx); left: 50%; transform: translateX(-50%); z-index: 999; font-size: 20rpx; color: #8C6A36; background: rgba(231,212,172,.92); border: 1rpx solid rgba(184,148,90,.42); padding: 4rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 16rpx -10rpx rgba(74,56,24,.4); }
</style>
