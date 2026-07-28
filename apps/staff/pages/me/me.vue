<template>
  <view class="screen">
    <view class="demo-flag">演示数据</view>
    <view class="topbar"><text class="nm">奇德芬芳</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">我的</view>

        <!-- 当前员工信息（姓名 / 角色 / 门店）· 缺失降级为占位，不显假数据 -->
        <view class="prof">
          <view class="big">{{ avatarText }}</view>
          <view class="pinfo">
            <text class="pn">{{ nameText }}<text class="role" v-if="me.role"> · {{ me.role }}</text></text>
            <text class="ps">{{ storeLine }}</text>
          </view>
        </view>

        <!-- 常用入口宫格（仅连已存在的页/函数；未建成入口标灰） -->
        <view class="sechead"><text class="l">常用</text></view>
        <view class="qgrid">
          <view :class="['qt', q.off ? 'qt--off' : '']" v-for="q in quicks" :key="q.t" @tap="go(q)">
            <text class="c">{{ q.c }}</text><text class="t">{{ q.t }}</text>
          </view>
        </view>

        <!-- 全部功能 -->
        <view class="sechead"><text class="l">全部功能</text></view>
        <view class="menu">
          <view class="mi" v-for="m in menu" :key="m.l" @tap="go(m)"><text>{{ m.l }}</text><text class="r">›</text></view>
        </view>

        <view class="logoutbtn" @tap="doLogout">退出登录</view>
        <text class="foot">奇德芬芳 · 员工端 · uni-app</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { MEMENU } from '@/common/data.js'
import { loadDashboard, logoutRemote, REMOTE } from '@/common/remote.js'
import { hasAccess } from '@/common/logic.js'
// 常用入口：仅指向已存在的二级屏（sub?key=）/ tabBar 页；考勤打卡暂无后端与页面 → off 标灰。
const QUICKS = [
  { c: '绩', t: '我的业绩', k: 'perfReport' },
  { c: '审', t: '审批待办', k: 'approvals', manager: true },
  { c: '客', t: '我的客户', tab: '/pages/clients/clients', perm: 'customers' },
  { c: '巡', t: '巡房记录', tab: '/pages/round/round', perm: 'nursing' },
  { c: '费', t: '我的费用', k: 'fees' },
  { c: '访', t: '客户回访', k: 'visitReturn', perm: 'customer-tracking' },
  { c: '评', t: '满意度', k: 'satisfaction', perm: 'customer-tracking' },
  { c: '勤', t: '考勤打卡', off: true }
]
export default {
  data() { return { me: getApp().globalData.data.me || {} } },
  async onLoad() { const d = await loadDashboard(); this.me = (d && d.me) || {} },
  computed: {
    avatarText() { return this.me.avatar || (this.me.name ? this.me.name[0] : '奇') },
    nameText() { return this.me.name || '—' },
    storeLine() { return this.me.branch ? '奇德芬芳 · ' + this.me.branch : '奇德芬芳' },
    menu() { return MEMENU.filter(x => this.can(x.perm, x.manager, x.roles)) },
    quicks() { return QUICKS.filter(x => x.off || this.can(x.perm, x.manager)) }
  },
  methods: {
    can(perm, managerOnly, roles) {
      if (!hasAccess(REMOTE.perms, REMOTE.isManager, perm, managerOnly)) return false
      return REMOTE.isManager || !roles || roles.some(r => (REMOTE.roles || []).includes(r))
    },
    go(item) {
      if (item.off) { uni.showToast({ title: (item.t || item.l) + '（建设中）', icon: 'none' }); return }
      if (item.tab) { uni.switchTab({ url: item.tab }); return }
      if (item.page) { uni.navigateTo({ url: item.page }); return }
      if (item.k) { uni.navigateTo({ url: '/pages/sub/sub?key=' + item.k }); return }
      uni.showToast({ title: (item.t || item.l) + '（建设中）', icon: 'none' })
    },
    async doLogout() {
      const ok = await new Promise(r => uni.showModal({ title: '退出登录', content: '确定退出当前账号？', success: e => r(e.confirm), fail: () => r(false) }))
      if (!ok) return
      await logoutRemote()
      uni.reLaunch({ url: '/pages/login/login' }) // 登出后回正式登录页（各端一致）
    }
  }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { padding: 28rpx 40rpx 8rpx; } .nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 160rpx; }
.greet { font-family: $font-cn-serif; font-size: 42rpx; font-weight: 500; }
.prof { display: flex; align-items: center; background: $paper; border: 1rpx solid $hair; border-radius: 36rpx; padding: 32rpx; margin-top: 24rpx; }
.prof .big { width: 100rpx; height: 100rpx; border-radius: 32rpx; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; font-size: 40rpx; margin-right: 26rpx; flex-shrink: 0; }
.prof .pinfo { flex: 1; }
.prof .pn { font-family: $font-cn-serif; font-size: 34rpx; font-weight: 600; } .prof .role { font-size: 24rpx; color: $ink-3; font-weight: 400; }
.prof .ps { display: block; font-size: 24rpx; color: $ink-3; margin-top: 6rpx; }

.sechead { margin: 40rpx 4rpx 20rpx; } .sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; }
.qgrid { display: flex; flex-wrap: wrap; gap: 18rpx; }
.qt { width: calc(25% - 14rpx); box-sizing: border-box; background: $paper; border: 1rpx solid $hair; border-radius: 28rpx; padding: 26rpx 8rpx; text-align: center; }
.qt .c { font-family: $font-cn-serif; font-size: 36rpx; color: $gold-deep; } .qt .t { display: block; font-size: 22rpx; font-weight: 500; margin-top: 10rpx; }
.qt--off { opacity: .42; } .qt--off .c, .qt--off .t { color: $ink-3; }

.menu { background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; overflow: hidden; }
.mi { display: flex; align-items: center; justify-content: space-between; padding: 30rpx 32rpx; border-bottom: 1rpx solid $hair; font-size: 27rpx; } .mi:last-child { border-bottom: 0; } .mi .r { color: $ink-3; }
.logoutbtn { margin-top: 32rpx; text-align: center; color: #A04545; font-size: 26rpx; padding: 24rpx; background: $paper; border: 1rpx solid $hair; border-radius: 32rpx; }
.foot { display: block; text-align: center; color: $ink-3; font-size: 21rpx; margin-top: 32rpx; }

.demo-flag { position: fixed; top: calc(env(safe-area-inset-top) + 10rpx); left: 50%; transform: translateX(-50%); z-index: 999; font-size: 20rpx; color: #8C6A36; background: rgba(231,212,172,.92); border: 1rpx solid rgba(184,148,90,.42); padding: 4rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 16rpx -10rpx rgba(74,56,24,.4); }
</style>
