<template>
  <!-- 正式登录页（手机号 + 口令）· 高奢金白。生产走此页；本地 dev 演示自动登录不经此页（App.onLaunch 直接放行）。 -->
  <view class="screen">
    <view class="pad">
      <!-- 品牌字标 -->
      <view class="brand">
        <text class="logo">☾</text>
        <text class="nm">奇德芬芳</text>
        <text class="sub">员工端 · 请登录</text>
      </view>

      <!-- 登录卡片 -->
      <view class="card">
        <view class="field">
          <text class="lb">手机号</text>
          <input class="fi" type="text" v-model="phone" maxlength="20" placeholder="请输入登录手机号"
                 placeholder-class="ph" :disabled="busy" confirm-type="next" />
        </view>
        <view class="field">
          <text class="lb">登录口令</text>
          <input class="fi" v-model="password" password placeholder="请输入登录口令"
                 placeholder-class="ph" :disabled="busy" confirm-type="done" @confirm="doLogin" />
        </view>

        <view :class="['btn', canSubmit ? '' : 'btn--off']" @tap="doLogin">
          <text>{{ busy ? '登录中…' : '登 录' }}</text>
        </view>

        <view class="demo" v-if="demos.length">
          <text class="demo-title">演示账号（点击自动填写）</text>
          <view class="demo-grid">
            <view class="demo-account" v-for="a in demos" :key="a.phone" @tap="chooseDemo(a)">
              <text class="demo-name">{{ a.name }}</text>
              <text class="demo-role">{{ a.role }}</text>
              <text class="demo-phone">{{ a.phone }}</text>
            </view>
          </view>
        </view>
      </view>

      <text class="foot">奇德芬芳 · 员工端 · uni-app</text>
    </view>
  </view>
</template>

<script>
import { loginWith, makeApi } from '@/common/remote.js'
export default {
  data() {
    return { phone: '', password: '', busy: false, redirect: '', demos: [], demoPassword: '' }
  },
  async onLoad(q) {
    // 登录成功后回原目标页（可选），缺省回工作台
    if (q && q.redirect) this.redirect = decodeURIComponent(q.redirect)
    try {
      const d = await makeApi().demoAccounts()
      this.demos = (d && d.staff) || []
      this.demoPassword = (d && d.password) || ''
    } catch (_) { /* 正式环境不开放演示账号时不显示 */ }
  },
  computed: {
    canSubmit() { return !this.busy && this.phone.trim() && this.password.trim() }
  },
  methods: {
    chooseDemo(a) {
      this.phone = a.phone || ''
      this.password = this.demoPassword
    },
    async doLogin() {
      if (this.busy) return
      const phone = this.phone.trim(), password = this.password.trim()
      if (!phone) { uni.showToast({ title: '请输入手机号', icon: 'none' }); return }
      if (!password) { uni.showToast({ title: '请输入登录口令', icon: 'none' }); return }
      this.busy = true
      try {
        await loginWith(phone, password) // 复用 remote.js 现成登录能力（验签 token）
        uni.showToast({ title: '登录成功', icon: 'none' })
        const target = this.redirect || '/pages/home/home'
        // tabBar 页用 switchTab；非 tabBar 目标 switchTab 会 fail → 回退 reLaunch
        uni.switchTab({ url: target, fail: () => uni.reLaunch({ url: target }) })
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '手机号或口令错误', icon: 'none' })
      } finally {
        this.busy = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.screen { min-height: 100vh; background: $ivory; display: flex; flex-direction: column; }
.pad { flex: 1; display: flex; flex-direction: column; justify-content: center; padding: 0 56rpx calc(env(safe-area-inset-bottom) + 40rpx); }

.brand { text-align: center; margin-bottom: 64rpx; }
.brand .logo { display: block; color: $gold; font-size: 72rpx; line-height: 1; margin-bottom: 20rpx; }
.brand .nm { display: block; font-family: $font-display; font-size: 60rpx; letter-spacing: 8rpx; color: $gold-deep; }
.brand .sub { display: block; font-size: 24rpx; color: $ink-3; letter-spacing: 4rpx; margin-top: 18rpx; }

.card { background: $paper; border: 1rpx solid $hair; border-radius: $radius-lg; padding: 44rpx 40rpx; box-shadow: 0 20rpx 60rpx -36rpx rgba(74,56,24,.45); }
.field { margin-bottom: 32rpx; }
.field .lb { display: block; font-size: 22rpx; color: $ink-2; letter-spacing: 2rpx; margin-bottom: 14rpx; }
.field .fi { width: 100%; box-sizing: border-box; height: 92rpx; background: $ivory; border: 1rpx solid $hair; border-radius: 24rpx; padding: 0 28rpx; font-size: 30rpx; color: $ink; }
.ph { color: $ink-3; }

.btn { margin-top: 12rpx; height: 96rpx; border-radius: 28rpx; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 32rpx; letter-spacing: 8rpx; font-weight: 600; box-shadow: 0 16rpx 40rpx -20rpx rgba(140,106,54,.7); }
.btn--off { opacity: .55; box-shadow: none; }

.demo { margin-top: 36rpx; padding-top: 30rpx; border-top: 1rpx solid $hair; }
.demo-title { display: block; color: $ink-3; font-size: 22rpx; margin-bottom: 18rpx; }
.demo-grid { display: flex; flex-wrap: wrap; gap: 14rpx; }
.demo-account { width: calc(33.333% - 10rpx); box-sizing: border-box; padding: 16rpx 8rpx; text-align: center; border: 1rpx solid $hair; border-radius: 18rpx; background: $ivory; }
.demo-name { display: block; font-size: 23rpx; color: $ink; }
.demo-role { display: block; margin-top: 4rpx; font-size: 19rpx; color: $gold-deep; }
.demo-phone { display: block; margin-top: 5rpx; font-size: 17rpx; color: $ink-3; letter-spacing: 1rpx; }

.foot { display: block; text-align: center; color: $ink-3; font-size: 21rpx; margin-top: 48rpx; }
</style>
