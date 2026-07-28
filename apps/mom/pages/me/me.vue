<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">我的</view>
        <view class="prof"><view class="big">{{ me.avatar }}</view>
          <view><text class="pn">{{ me.name }}</text><text class="ps">{{ me.package || '暂未配置套餐' }}<text v-if="me.room"> · 房间 {{ me.room }}</text></text></view></view>
        <view class="menu"><view class="mi" v-for="m in menu" :key="m.l" @tap="open(m)"><text>{{ m.l }}</text><text class="r">›</text></view></view>
        <text class="foot">奇德芬芳 · 宝妈端 · uni-app</text>
        <view class="logoutbtn" @tap="doLogout">退出登录</view>
      </view>
    </scroll-view>
  </view>
</template>
<script>
import { MEMENU } from '@/common/data.js'
import { loadDashboard, logoutRemote } from '@/common/remote.js'
export default {
  data() { return { me: getApp().globalData.data.me, menu: MEMENU } },
  async onShow() {
    const d = await loadDashboard()
    this.me = d.me
    getApp().globalData.data = d
  },
  methods: {
    async doLogout() {
      await logoutRemote()
      uni.reLaunch({ url: '/pages/login/login' })
    }, open(m) { if (m.page) uni.navigateTo({ url: m.page }); else if (m.k) uni.navigateTo({ url: '/pages/sub/sub?key=' + m.k }); else uni.showToast({ title: m.l + '（建设中）', icon: 'none' }) } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; }
.prof { display: flex; align-items: center; background: rgba(255,255,255,.96); border: 1rpx solid $platinum; border-radius: 36rpx; padding: 32rpx; margin-top: 24rpx; box-shadow: $shadow-soft; }
.prof .big { width: 100rpx; height: 100rpx; border-radius: 32rpx; background: $foil; color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 40rpx; margin-right: 26rpx; }
.prof .pn { font-family: $font-cn-serif; font-size: 34rpx; font-weight: 600; } .prof .ps { display: block; font-size: 24rpx; color: $ink-3; margin-top: 6rpx; }
.menu { margin-top: 28rpx; background: rgba(255,255,255,.96); border: 1rpx solid $platinum; border-radius: 32rpx; overflow: hidden; box-shadow: $shadow-soft; }
.mi { display: flex; align-items: center; justify-content: space-between; padding: 30rpx 32rpx; border-bottom: 1rpx solid $hair; font-size: 27rpx; } .mi:last-child { border-bottom: 0; } .mi .r { color: $ink-3; }
.foot { display: block; text-align: center; color: $ink-3; font-size: 21rpx; margin-top: 36rpx; }
.logoutbtn { margin-top: 24rpx; text-align: center; color: #A04545; font-size: 26rpx; padding: 22rpx; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; }

</style>
