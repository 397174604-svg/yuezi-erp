<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳 · 臻选</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">好物臻选<text class="sm">月子滋补 · 母婴护理 · 积分可抵</text></view>
        <view class="grid">
          <view class="card2" v-for="(p,i) in mall" :key="i" @tap="buy(p)">
            <view class="thumb"><text class="ph">{{ (p.name || '奇德芬芳').charAt(0) }}</text><text v-if="p.recommend" class="rec">荐</text></view>
            <text class="pn">{{ p.name }}</text>
            <text class="meta">{{ p.cat }}{{ p.spec ? ' · ' + p.spec : '' }}</text>
            <view class="price"><text class="cur">¥</text>{{ p.price }}<text class="pt" v-if="p.point"> · {{ p.point }}积分</text></view>
          </view>
          <view v-if="!mall.length" class="empty">暂无在售商品</view>
        </view>
      </view>
    </scroll-view>
  </view>
  <demo-tabbar end="mom" active="mall/mall" />
</template>
<script>
import { loadMall, buy as purchaseProduct } from '@/common/mom/remote.js'
export default {
  data() { return { mall: getApp().globalData.data.mall, submitting: false } },
  async onLoad() { this.mall = await loadMall() },
  methods: {
    async buy(p) {
      if (this.submitting) return // 防重复
      if (!p.productId) { uni.showToast({ title: '商品信息缺失', icon: 'none' }); return }
      const ok = await new Promise(r => uni.showModal({ title: '确认购买', content: p.name + ' · ¥' + p.price, success: e => r(e.confirm), fail: () => r(false) }))
      if (!ok) return // 二次确认
      // 稳定幂等键：同一购买意图失败重试沿用同键→后端命中即返回首单，杜绝重复下单/多扣库存
      if (!this._idemKey) this._idemKey = 'mall-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10)
      this.submitting = true
      try {
        const r = await purchaseProduct(p.productId, 1, '微信', this._idemKey) // 真实下单（透传幂等键）
        this._idemKey = null // 成功→下一笔新意图
        uni.showToast({ title: '下单成功 · 实付 ¥' + Number(r.amount != null ? r.amount : p.price).toLocaleString(), icon: 'none' })
      } catch (e) {
        uni.showToast({ title: '下单失败：' + (e && e.message ? e.message : '请重试'), icon: 'none' }) // 失败保留幂等键供重试
      } finally { this.submitting = false }
    }
  }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.grid { display: flex; flex-wrap: wrap; gap: 22rpx; margin-top: 28rpx; }
.empty { width: 100%; text-align: center; color: $ink-3; font-size: 24rpx; padding: 80rpx 0; }
.card2 { width: calc(50% - 11rpx); box-sizing: border-box; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; padding: 20rpx; }
.thumb { height: 200rpx; border-radius: 24rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); display: flex; align-items: center; justify-content: center; position: relative; }
.thumb .ph { font-family: $font-cn-serif; font-size: 60rpx; color: $gold-deep; opacity: .55; } .thumb .rec { position: absolute; top: 14rpx; right: 14rpx; font-size: 19rpx; color: #fff; background: linear-gradient(135deg,#E9D4A4,#9C7838); border-radius: 30rpx; padding: 4rpx 14rpx; }
.pn { display: block; font-family: $font-cn-serif; font-size: 27rpx; font-weight: 600; margin-top: 16rpx; } .meta { display: block; font-size: 20rpx; color: $ink-3; margin-top: 6rpx; }
.price { font-family: $font-display; font-size: 40rpx; color: $gold-deep; font-weight: 600; margin-top: 10rpx; } .price .cur { font-size: 24rpx; } .price .pt { font-family: $font-sans; font-size: 19rpx; color: $ink-3; }

.screen, .page, .wrap { padding-bottom: 140rpx; }
</style>
