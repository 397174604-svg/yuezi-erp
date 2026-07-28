<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">登录与密码</text><text class="blank"></text></view>
    <view class="card" v-if="loaded">
      <text class="phone">登录账号 {{ account.phoneMasked }}</text>
      <text class="tip">{{ account.hasPassword ? '修改密码后，旧密码立即失效。' : '设置后可使用手机号和密码登录，也可继续使用微信一键登录。' }}</text>
      <view v-if="account.hasPassword" class="field"><text>当前密码</text><input v-model="currentPassword" password maxlength="64" placeholder="请输入当前密码" /></view>
      <view class="field"><text>新密码</text><input v-model="newPassword" password maxlength="64" placeholder="8-64 位，包含字母和数字" /></view>
      <view class="field"><text>确认新密码</text><input v-model="confirmPassword" password maxlength="64" placeholder="请再次输入" /></view>
      <button class="save" :loading="saving" :disabled="saving" @tap="save">{{ account.hasPassword ? '确认修改' : '设置密码' }}</button>
    </view>
  </view>
</template>

<script>
import { makeApi } from '@/common/remote.js'
export default {
  data() { return { loaded: false, saving: false, account: {}, currentPassword: '', newPassword: '', confirmPassword: '' } },
  async onLoad() {
    try { this.account = await makeApi().getCustomerAccount(); this.loaded = true }
    catch (e) { uni.showToast({ title: (e && e.message) || '账号信息加载失败', icon: 'none' }) }
  },
  methods: {
    back() { uni.navigateBack() },
    async save() {
      if (this.saving) return
      if (this.newPassword !== this.confirmPassword) return uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
      if (this.newPassword.length < 8 || !/[A-Za-z]/.test(this.newPassword) || !/\d/.test(this.newPassword)) return uni.showToast({ title: '密码须至少 8 位，并包含字母和数字', icon: 'none' })
      this.saving = true
      try {
        await makeApi().setCustomerPassword(this.newPassword, this.account.hasPassword ? this.currentPassword : undefined)
        this.account.hasPassword = true; this.currentPassword = ''; this.newPassword = ''; this.confirmPassword = ''
        uni.showToast({ title: '保存成功', icon: 'success' })
      } catch (e) { uni.showToast({ title: (e && e.message) || '保存失败', icon: 'none' }) }
      finally { this.saving = false }
    },
  },
}
</script>

<style lang="scss" scoped>
.page { min-height: 100vh; padding: 0 38rpx 70rpx; box-sizing: border-box; background: linear-gradient(160deg,$ivory,#EEECE7); }.top { display: flex; align-items: center; justify-content: space-between; height: 80rpx; }.back { width: 60rpx; font-size: 54rpx; color: $gold-deep; line-height: 60rpx; }.blank { width: 60rpx; }.title { font-family: $font-cn-serif; font-size: 34rpx; }.card { margin-top: 30rpx; background: rgba(255,255,255,.96); border: 1rpx solid $hair; border-radius: 36rpx; padding: 38rpx 32rpx; box-shadow: $shadow-soft; }.phone { display: block; font-size: 31rpx; font-family: $font-cn-serif; }.tip { display: block; color: $ink-3; font-size: 23rpx; margin: 10rpx 0 34rpx; }.field { border-bottom: 1rpx solid $hair; padding: 10rpx 0 20rpx; margin-bottom: 26rpx; }.field text { display: block; color: $ink-2; font-size: 22rpx; }.field input { height: 64rpx; font-size: 28rpx; }.save { margin-top: 42rpx; height: 90rpx; line-height: 90rpx; border-radius: 28rpx; background: $foil; color: #fff; font-size: 28rpx; }.save::after { border: 0; }
</style>
