<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">今日餐单<text class="sm">主厨配膳 · 房间送达 · 第 {{ journey.day }} 天 · {{ journey.phase }}</text></view>
        <view class="yz-card">
          <view class="meal" v-for="(m,i) in meals" :key="i">
            <text class="mt">{{ m.meal }}</text>
            <view class="bd"><text class="menu">{{ m.menu }}</text><text class="rk" v-if="m.remark">{{ m.remark }}</text></view>
            <text :class="['st', m.status==='已发布'?'on':'']">{{ m.status }}</text>
          </view>
          <view v-if="!meals || !meals.length" class="empty">今日暂无餐单，敬请期待主厨配膳</view>
        </view>
        <view class="order" @tap="order">＋ 加点 / 订餐</view>
      </view>
    </scroll-view>
  </view>
</template>
<script>
import { loadDashboard } from '@/common/remote.js'
export default {
  data() { const m = getApp().globalData.data; return { meals: m.todayMeals, journey: m.journey } },
  async onLoad() { const d = await loadDashboard(); this.meals = d.todayMeals; this.journey = d.journey },
  methods: { order() { uni.showToast({ title: '加点下单（示意）', icon: 'none' }) } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; } .greet .sm { display: block; font-size: 24rpx; color: $ink-3; margin-top: 12rpx; }
.empty { text-align: center; color: $ink-3; font-size: 24rpx; padding: 60rpx 0; }
.meal { display: flex; align-items: center; padding: 24rpx 0; border-bottom: 1rpx solid $hair; } .meal:last-child { border-bottom: 0; }
.meal .mt { font-family: $font-display; font-size: 30rpx; color: $gold-deep; width: 150rpx; }
.meal .bd { flex: 1; } .meal .menu { font-size: 27rpx; font-weight: 500; } .meal .rk { display: inline-block; font-size: 19rpx; color: $gold-deep; border: 1rpx solid $hair-s; border-radius: 30rpx; padding: 4rpx 14rpx; margin-top: 8rpx; }
.meal .st { font-size: 20rpx; padding: 8rpx 18rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; } .meal .st.on { background: rgba(110,139,106,.16); color: #577053; border: none; }
.order { margin-top: 28rpx; text-align: center; font-size: 27rpx; color: #fff; background: $foil; border-radius: 60rpx; padding: 28rpx; box-shadow: 0 16rpx 34rpx -22rpx rgba(94,74,38,.62); }

</style>
