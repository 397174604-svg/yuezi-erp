<template>
  <!-- 合一演示自绘底栏：替代四端各自的原生 tabBar（一个小程序只能有一个原生 tabBar）。
       按当前所在端渲染该端 4 个 tab，点击 reLaunch 切换；末尾「切换身份」回到 launch 选择页。 -->
  <view class="dtabbar">
    <view v-for="t in tabs" :key="t.path" class="dt" :class="{ on: t.path === active }" @tap="go(t.path)">
      <text class="di">{{ t.icon }}</text>
      <text class="dl">{{ t.label }}</text>
    </view>
    <view class="dt switch" @tap="toLaunch">
      <text class="di">🔀</text>
      <text class="dl">切换身份</text>
    </view>
  </view>
</template>

<script>
import { tabsForEnd, tabUrl } from './tabs.js'
export default {
  name: 'demo-tabbar',
  props: {
    end: { type: String, required: true },   // 当前端：staff/rehab/beauty/mom
    active: { type: String, required: true }, // 当前页：如 'home/home'
  },
  computed: {
    tabs() { return tabsForEnd(this.end) },
  },
  methods: {
    go(path) { if (path === this.active) return; uni.reLaunch({ url: tabUrl(this.end, path) }) },
    toLaunch() { uni.reLaunch({ url: '/pages/launch/launch' }) },
  },
}
</script>

<style lang="scss" scoped>
.dtabbar {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 500;
  display: flex; align-items: stretch;
  background: #FBF7F0; border-top: 1rpx solid #EAe0cf;
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -6rpx 24rpx -18rpx rgba(74,56,24,.4);
}
/* #ifdef H5 */
@media screen and (min-width: 500px) { .dtabbar { left: 50%; right: auto; width: 480px; margin-left: -240px; } }
/* #endif */
.dt { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12rpx 0 14rpx; }
.dt:active { opacity: .7; }
.dt .di { font-size: 40rpx; line-height: 1.1; filter: grayscale(1) opacity(.55); }
.dt .dl { font-size: 20rpx; color: #A89E8D; margin-top: 4rpx; }
.dt.on .di { filter: none; }
.dt.on .dl { color: #8C6A36; font-weight: 600; }
.dt.switch .di { filter: none; }
</style>
