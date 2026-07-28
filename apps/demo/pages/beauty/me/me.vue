<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳 · 科颜</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">我的</view>
        <view class="prof">
          <view class="big">店</view>
          <view><text class="pn">{{ store.name }}</text><text class="ps">店长 {{ store.manager }}</text></view>
        </view>
        <view class="menu">
          <view class="mi" v-for="m in shownMenu" :key="m.k || m.l" @tap="open(m)"><text>{{ m.l }}</text><text class="r">›</text></view>
        </view>
        <text class="foot">奇德芬芳 · 科研美容门店端 · uni-app 参考实现</text>
        <!-- #ifdef H5 -->
        <view class="logoutbtn" @tap="doLogout">退出登录 · 返回演示门户</view>
        <!-- #endif -->
      </view>
    </scroll-view>
  </view>
  <demo-tabbar end="beauty" active="me/me" />
</template>

<script>
import { loadDashboard, logoutRemote, REMOTE } from '@/common/beauty/remote.js'
export default {
  async onLoad() { const d = await loadDashboard(); this.store = d.store; this.isMgr = !!REMOTE.isManager },
  data() {
    return {
      store: getApp().globalData.data.store,
      isMgr: false, // 登录态管理层标志：非管理层隐藏管理专属入口（后端亦有 manager 守卫双保险）
      menu: [
        { l: '经营数据', k: 'bizData' }, { l: '会员数据', k: 'memberStats' },
        { l: '支付 / 订单管理', k: 'payOrders' }, { l: '转店记录', k: 'transferLog' },
        { l: '库房管理', mg: 'stock' }, { l: '员工排班', k: 'scheduleBoard' },
        { l: '品项设置', k: 'itemSettings', mgr: true }, { l: '提成设置', k: 'commission', mgr: true }, { l: '等级折扣', mg: 'levels', mgr: true }, { l: '预约看板', k: 'apptBoard' },
        { l: '人员管理', mg: 'staff', mgr: true }, { l: '店铺管理', mg: 'store', mgr: true }, { l: '邀约话术', mg: 'scripts', mgr: true }, { l: '设置' }
      ]
    }
  },
  computed: {
    shownMenu() { return this.menu.filter(m => !m.mgr || this.isMgr) } // mgr 项仅管理层可见
  },
  methods: {
    async doLogout() {
      await logoutRemote()
      // #ifdef H5
      location.href = 'http://' + (location.hostname || '127.0.0.1') + ':5179/'
      // #endif
    },
    open(m) {
      if (m.mg) uni.navigateTo({ url: '/pages/beauty/manage/manage?key=' + m.mg })
      else if (m.k) uni.navigateTo({ url: '/pages/beauty/sub/sub?key=' + m.k })
      else uni.showToast({ title: m.l + '（建设中）', icon: 'none' })
    }
  }
}
</script>

<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; }
.nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; }
.pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; }
.prof { display: flex; align-items: center; background: $paper; border: 1rpx solid $hair; border-radius: 36rpx; padding: 32rpx; margin-top: 24rpx; }
.prof .big { width: 100rpx; height: 100rpx; border-radius: 32rpx; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 40rpx; margin-right: 26rpx; }
.prof .pn { font-family: $font-cn-serif; font-size: 34rpx; font-weight: 600; }
.prof .ps { display: block; font-size: 24rpx; color: $ink-3; margin-top: 6rpx; }
.menu { margin-top: 28rpx; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; overflow: hidden; }
.mi { display: flex; align-items: center; justify-content: space-between; padding: 30rpx 32rpx; border-bottom: 1rpx solid $hair; font-size: 27rpx; }
.mi:last-child { border-bottom: 0; }
.mi .r { color: $ink-3; }
.foot { display: block; text-align: center; color: $ink-3; font-size: 21rpx; margin-top: 36rpx; }
.logoutbtn { margin-top: 24rpx; text-align: center; color: #A04545; font-size: 26rpx; padding: 22rpx; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; }

.screen, .page, .wrap { padding-bottom: 140rpx; }
</style>
