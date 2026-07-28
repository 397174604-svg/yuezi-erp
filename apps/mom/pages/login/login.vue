<template>
  <view class="login-page">
    <view class="halo halo-a"></view><view class="halo halo-b"></view>
    <view class="brand">
      <view class="moon">☾</view>
      <text class="brand-cn">奇德芬芳</text>
      <text class="brand-en">QIDE FENFANG · MOM</text>
    </view>

    <view class="card">
      <text class="welcome">欢迎回来</text>
      <text class="desc">登录后查看您的月子照护与宝宝成长记录</text>
      <view class="tabs">
        <view :class="['tab', mode === 'wechat' && 'active']" @tap="mode='wechat'">手机号一键登录</view>
        <view :class="['tab', mode === 'password' && 'active']" @tap="mode='password'">账号密码登录</view>
      </view>

      <view v-if="mode === 'wechat'" class="panel">
        <view class="phone-mark">安全获取微信绑定手机号</view>
        <!-- #ifdef MP-WEIXIN -->
        <button class="primary wx" open-type="getPhoneNumber" :loading="loading" :disabled="loading" @getphonenumber="onGetPhoneNumber">微信手机号一键登录</button>
        <!-- #endif -->
        <!-- #ifndef MP-WEIXIN -->
        <button class="primary disabled" disabled>请在微信小程序内使用</button>
        <text class="hint">当前环境可切换到“账号密码登录”进行测试</text>
        <!-- #endif -->
        <view class="agree-row" @tap="agreed=!agreed"><checkbox :checked="agreed" color="#8C6A36" /><text>我已阅读并同意</text><text class="link" @tap.stop="showAgreement">服务协议与隐私政策</text></view>
        <text class="agreement">手机号由微信验证后传给服务端，本页面不会要求您手工填写微信手机号。</text>
      </view>

      <view v-else class="panel form">
        <view class="field"><text class="label">手机号</text><input v-model.trim="phone" type="number" maxlength="20" placeholder="请输入手机号" /></view>
        <view class="field"><text class="label">密码</text><input v-model="password" password maxlength="64" placeholder="请输入登录密码" confirm-type="done" @confirm="passwordLogin" /></view>
        <button class="primary" :loading="loading" :disabled="loading" @tap="passwordLogin">登录</button>
        <text class="forgot" @tap="forgotPassword">忘记密码？使用微信验证身份</text>
        <text class="hint">首次使用微信手机号登录后，可设置密码；若当时跳过，仍可在“我的 → 登录与密码”中设置。</text>
      </view>
    </view>

    <view v-if="showPasswordPrompt" class="mask">
      <view class="dialog">
        <text class="dialog-title">设置登录密码</text>
        <text class="dialog-desc">这是您第一次登录。设置后，下次可直接使用手机号和密码登录。</text>
        <view class="field"><text class="label">新密码</text><input v-model="newPassword" password maxlength="64" placeholder="8-64 位，包含字母和数字" /></view>
        <view class="field"><text class="label">确认密码</text><input v-model="confirmPassword" password maxlength="64" placeholder="请再次输入" /></view>
        <button class="primary" :loading="settingPassword" :disabled="settingPassword" @tap="saveFirstPassword">保存并进入</button>
        <button class="skip" :disabled="settingPassword" @tap="enterApp">暂时跳过</button>
      </view>
    </view>
  </view>
</template>

<script>
import { applyAuth, clearAuth, isAuthenticated, makeApi, takePendingRoute } from '@/common/remote.js'

const AGREEMENT_VERSION = '2026-07-21.1'

function wxLoginCode() {
  return new Promise((resolve, reject) => {
    uni.login({ provider: 'weixin', success: r => r.code ? resolve(r.code) : reject(new Error('未获取到微信登录凭证')), fail: reject })
  })
}

export default {
  data() {
    return { mode: 'wechat', phone: '', password: '', agreed: false, loading: false, showPasswordPrompt: false, newPassword: '', confirmPassword: '', settingPassword: false }
  },
  onLoad() { if (isAuthenticated()) this.enterApp() },
  methods: {
    message(error, fallback) {
      uni.showToast({ title: (error && (error.message || error.errMsg)) || fallback, icon: 'none', duration: 2600 })
    },
    async onGetPhoneNumber(event) {
      if (this.loading) return
      if (!this.agreed) return this.message(null, '请先阅读并同意服务协议与隐私政策')
      const detail = event && event.detail
      if (!detail || !detail.code || (detail.errMsg && detail.errMsg.indexOf(':ok') < 0)) {
        this.message(detail, '需要授权手机号才能一键登录')
        return
      }
      this.loading = true
      try {
        const loginCode = await wxLoginCode()
        const result = await makeApi().wechatPhoneLogin(loginCode, detail.code)
        applyAuth(result)
        try { await makeApi().acceptCustomerAgreements(AGREEMENT_VERSION) }
        catch (error) { clearAuth(); throw error }
        if (result.needsPassword) this.showPasswordPrompt = true
        else this.enterApp()
      } catch (error) { this.message(error, '微信登录失败，请重试') }
      finally { this.loading = false }
    },
    async passwordLogin() {
      if (this.loading) return
      if (!/^\d{6,20}$/.test(this.phone)) return this.message(null, '请输入正确的手机号')
      if (!this.password) return this.message(null, '请输入密码')
      this.loading = true
      try {
        const result = await makeApi().customerPasswordLogin(this.phone, this.password)
        applyAuth(result)
        this.enterApp()
      } catch (error) { this.message(error, '登录失败，请检查账号和密码') }
      finally { this.loading = false }
    },
    forgotPassword() {
      this.mode = 'wechat'
      this.message(null, '请使用微信手机号一键登录，登录后即可重设密码')
    },
    showAgreement() {
      uni.showModal({ title: '服务协议与隐私政策', content: '手机号仅用于账号识别、本人服务和门店联系；密码只保存安全哈希。您可以在“我的”中管理登录密码和退出账号。', showCancel: false })
    },
    async saveFirstPassword() {
      if (this.settingPassword) return
      if (this.newPassword !== this.confirmPassword) return this.message(null, '两次输入的密码不一致')
      if (this.newPassword.length < 8 || !/[A-Za-z]/.test(this.newPassword) || !/\d/.test(this.newPassword)) {
        return this.message(null, '密码须至少 8 位，并包含字母和数字')
      }
      this.settingPassword = true
      try {
        await makeApi().setCustomerPassword(this.newPassword)
        uni.showToast({ title: '密码设置成功', icon: 'success' })
        setTimeout(() => this.enterApp(), 400)
      } catch (error) { this.message(error, '密码设置失败') }
      finally { this.settingPassword = false }
    },
    enterApp() {
      this.showPasswordPrompt = false
      const pending = takePendingRoute()
      if (pending) uni.reLaunch({ url: pending })
      else uni.switchTab({ url: '/pages/home/home' })
    },
  },
}
</script>

<style lang="scss" scoped>
.login-page { min-height: 100vh; box-sizing: border-box; padding: calc(env(safe-area-inset-top) + 74rpx) 40rpx 70rpx; background: linear-gradient(155deg,$ivory 0%,$ivory-2 100%); position: relative; overflow: hidden; }
.halo { position: absolute; border-radius: 50%; border: 1rpx solid rgba(184,148,90,.18); }
.halo-a { width: 430rpx; height: 430rpx; right: -210rpx; top: -130rpx; }.halo-b { width: 280rpx; height: 280rpx; left: -160rpx; bottom: 100rpx; }
.brand { position: relative; display: flex; flex-direction: column; align-items: center; margin-bottom: 56rpx; }.moon { color: $gold; font-size: 62rpx; line-height: 1; }.brand-cn { font-family: $font-cn-serif; color: $gold-deep; font-size: 44rpx; letter-spacing: 10rpx; margin-left: 10rpx; }.brand-en { color: $ink-3; font-size: 19rpx; letter-spacing: 5rpx; margin-top: 8rpx; }
.card { position: relative; background: rgba(255,255,255,.96); border: 1rpx solid $platinum; border-radius: 44rpx; padding: 46rpx 38rpx 42rpx; box-shadow: $shadow-soft; }.welcome { display: block; font-family: $font-cn-serif; font-size: 40rpx; text-align: center; }.desc { display: block; color: $ink-3; font-size: 23rpx; text-align: center; margin-top: 8rpx; }
.tabs { display: flex; background: $ivory-2; border: 1rpx solid $platinum; border-radius: 28rpx; padding: 6rpx; margin: 36rpx 0 34rpx; }.tab { flex: 1; text-align: center; padding: 18rpx 8rpx; border-radius: 23rpx; color: $ink-3; font-size: 25rpx; }.tab.active { color: $gold-deep; background: $paper; box-shadow: 0 8rpx 24rpx -18rpx rgba(66,58,44,.34); font-weight: 600; }
.panel { min-height: 310rpx; }.phone-mark { text-align: center; color: $ink-2; font-size: 26rpx; padding: 30rpx 0 44rpx; }.primary { margin: 0; border: 0; border-radius: 28rpx; background: $foil; color: #fff; font-size: 28rpx; line-height: 92rpx; height: 92rpx; box-shadow: 0 18rpx 40rpx -24rpx rgba(94,74,38,.62); }.primary::after,.skip::after { border: 0; }.primary.disabled { background: $platinum; box-shadow: none; }.agreement,.hint { display: block; color: $ink-3; font-size: 21rpx; line-height: 1.7; text-align: center; margin-top: 20rpx; }.agree-row { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; margin-top: 26rpx; color: $ink-3; font-size: 21rpx; }.agree-row checkbox { transform: scale(.7); }.agree-row .link { color: $gold-deep; margin-left: 4rpx; }.forgot { display: block; text-align: center; color: $gold-deep; font-size: 23rpx; margin-top: 24rpx; }
.field { border-bottom: 1rpx solid $hair; padding: 10rpx 0 18rpx; margin-bottom: 24rpx; }.field .label { display: block; color: $ink-2; font-size: 22rpx; margin-bottom: 6rpx; }.field input { height: 58rpx; font-size: 29rpx; color: $ink; }.form .primary { margin-top: 38rpx; }
.mask { position: fixed; inset: 0; z-index: 1000; background: rgba(39,37,33,.34); display: flex; align-items: center; justify-content: center; padding: 40rpx; box-sizing: border-box; backdrop-filter: blur(8rpx); }.dialog { width: 100%; background: #fff; border: 1rpx solid $platinum; border-radius: 40rpx; padding: 44rpx 38rpx 30rpx; box-sizing: border-box; box-shadow: $shadow-soft; }.dialog-title { display: block; font-family: $font-cn-serif; font-size: 36rpx; text-align: center; }.dialog-desc { display: block; color: $ink-3; font-size: 23rpx; text-align: center; margin: 12rpx 0 34rpx; }.skip { margin-top: 12rpx; height: 76rpx; line-height: 76rpx; color: $ink-3; background: transparent; font-size: 25rpx; }
</style>
