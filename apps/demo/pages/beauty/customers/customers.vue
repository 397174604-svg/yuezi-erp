<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳 · 科颜</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">客户管理<text class="sm">精准筛选 · 业务追踪 · 转店记录</text></view>
        <view class="filters">
          <text v-for="f in levels" :key="f" :class="['chip', level===f?'on':'']" @tap="level=f">{{ f }}</text>
        </view>
        <view class="yz-card cust" v-for="(c,i) in shown" :key="i">
          <view class="pic">{{ (c.name || '?').charAt(0) }}</view>
          <view class="info">
            <text class="cn">{{ c.name || '未命名' }} <text class="ph">{{ c.phone }}</text></text>
            <view class="tags"><text class="yz-tag yz-tag--solid">{{ c.level }}</text><text class="yz-tag" v-for="t in c.tags" :key="t">{{ t }}</text></view>
            <text class="meta">到店 {{ c.visitCount }} 次 · 累计 ¥{{ (c.totalSpend || 0).toLocaleString() }} · 顾问 {{ c.advisor }}</text>
          </view>
          <view class="bal"><text class="v">¥{{ (c.balance || 0).toLocaleString() }}</text><text class="bl">余额 · 最近 {{ c.last }}</text></view>
        </view>
        <view v-if="!shown.length" class="empty">暂无客户</view>
      </view>
    </scroll-view>
  </view>
  <demo-tabbar end="beauty" active="customers/customers" />
</template>
<script>
import { loadCustomers } from '@/common/beauty/remote.js'
export default {
  data() {
    return {
      level: '全部', levels: ['全部', '黑金', '钻石', '白银', '体验'],
      customers: [] // 数据来自后端 loadCustomers（onLoad）
    }
  },
  async onLoad() { this.customers = await loadCustomers() },
  computed: { shown() { return this.level === '全部' ? this.customers : this.customers.filter(c => c.level === this.level) } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; }
.nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; }
.pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; }
.greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.filters { display: flex; flex-wrap: wrap; gap: 16rpx; margin: 28rpx 0 8rpx; }
.chip { font-size: 24rpx; padding: 14rpx 28rpx; border-radius: 40rpx; border: 1rpx solid $hair; color: $ink-2; background: $paper; }
.chip.on { background: $ink; color: $gold-soft; border: none; }
.cust { display: flex; align-items: center; margin-top: 22rpx; }
.cust .pic { width: 84rpx; height: 84rpx; border-radius: 24rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; color: $gold-deep; font-size: 32rpx; }
.cust .info { flex: 1; margin-left: 22rpx; }
.cust .cn { font-family: $font-cn-serif; font-size: 29rpx; font-weight: 600; }
.cust .cn .ph { font-size: 22rpx; color: $ink-3; font-weight: 400; margin-left: 10rpx; }
.cust .tags { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 12rpx; }
.cust .meta { display: block; font-size: 20rpx; color: $ink-3; margin-top: 10rpx; }
.cust .bal { text-align: right; }
.cust .bal .v { font-family: $font-display; font-size: 32rpx; color: $gold-deep; font-weight: 600; }
.cust .bal .bl { display: block; font-size: 19rpx; color: $ink-3; }
.empty { text-align: center; color: $ink-3; font-size: 24rpx; padding: 80rpx 0; }

.screen, .page, .wrap { padding-bottom: 140rpx; }
</style>
