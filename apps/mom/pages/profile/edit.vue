<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">个人资料</text><text class="blank"></text></view>
    <scroll-view scroll-y class="scroll">
      <view class="intro"><text class="intro-title">查看和修改个人资料</text><text class="intro-sub">这里会展示您首次完善资料时填写的信息</text></view>
      <view v-if="loading" class="loading">正在读取已保存的资料…</view>
      <view v-else class="card">
        <view class="field"><text class="label">姓名或希望使用的称呼</text><input v-model.trim="form.displayName" type="nickname" maxlength="30" placeholder="如：王女士、晨晨妈妈（选填）" /></view>
        <view class="group"><text class="label">您是宝宝的？</text><view class="chips"><view v-for="x in roles" :key="x.v" :class="['chip',form.guardianRole===x.v&&'on']" @tap="form.guardianRole=x.v">{{x.l}}</view></view></view>
        <view class="group"><text class="label">目前处于哪个阶段？</text><view class="stage-list"><view v-for="x in stages" :key="x.v" :class="['stage',form.serviceStage===x.v&&'on']" @tap="form.serviceStage=x.v"><text>{{x.l}}</text><text class="dot">✓</text></view></view></view>

        <picker v-if="form.serviceStage==='pregnant'" mode="date" :value="form.edc" @change="form.edc=$event.detail.value"><view class="field row"><text class="label">预产期（选填）</text><text>{{form.edc||'请选择'}} ›</text></view></picker>
        <picker v-if="form.serviceStage==='baby_born'" mode="date" :value="form.babyBirthDate" @change="form.babyBirthDate=$event.detail.value"><view class="field row"><text class="label">宝宝出生日期（选填）</text><text>{{form.babyBirthDate||'请选择'}} ›</text></view></picker>
        <view v-if="form.serviceStage==='baby_born'" class="group"><text class="label">当前喂养方式</text><view class="chips"><view v-for="x in feedings" :key="x.v" :class="['chip',form.feedingMode===x.v&&'on']" @tap="form.feedingMode=x.v">{{x.l}}</view></view></view>
        <view v-if="form.serviceStage==='pregnant'||form.serviceStage==='baby_born'" class="group"><text class="label">最关注的宝宝护理（最多 2 项）</text><view class="chips concerns"><view v-for="x in concerns" :key="x.v" :class="['chip',form.careConcerns.includes(x.v)&&'on']" @tap="toggleConcern(x.v)">{{x.l}}</view></view></view>

        <button class="save" :loading="saving" :disabled="saving" @tap="save">保存修改</button>
        <text class="privacy">手机号和微信绑定不会在这里修改；资料保存后，首页和“我的”会同步显示最新称呼。</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { loadProfileContext, saveProfileContext } from '@/common/remote.js'

const EMPTY_FORM = {
  displayName: '', guardianRole: 'unknown', serviceStage: 'exploring', edc: '',
  babyBirthDate: '', feedingMode: 'unknown', careConcerns: [],
}

export default {
  data() { return {
    loading: true, saving: false, form: { ...EMPTY_FORM },
    roles: [{v:'mother',l:'妈妈'},{v:'father',l:'爸爸'},{v:'family',l:'其他家属'}],
    stages: [{v:'pregnant',l:'孕期'},{v:'baby_born',l:'宝宝已出生'},{v:'checked_in',l:'已入住奇德芬芳'},{v:'exploring',l:'先了解服务'}],
    feedings: [{v:'breast',l:'母乳'},{v:'mixed',l:'混合'},{v:'formula',l:'配方奶'},{v:'unknown',l:'还不确定'}],
    concerns: [{v:'feeding',l:'喂养与拍嗝'},{v:'sleep',l:'睡眠与安抚'},{v:'diaper',l:'便便与尿布'},{v:'observation',l:'日常健康观察'},{v:'bath_umbilical',l:'洗澡与脐部护理'},{v:'unsure',l:'还不确定'}],
  }},
  async onLoad() {
    try {
      const profile = await loadProfileContext()
      this.form = { ...EMPTY_FORM, ...(profile || {}), careConcerns: Array.isArray(profile && profile.careConcerns) ? [...profile.careConcerns] : [] }
    } catch (error) {
      uni.showToast({ title: (error && error.message) || '资料加载失败', icon: 'none' })
    } finally { this.loading = false }
  },
  methods: {
    back() { uni.navigateBack() },
    toggleConcern(value) {
      const index = this.form.careConcerns.indexOf(value)
      if (index >= 0) this.form.careConcerns.splice(index, 1)
      else if (this.form.careConcerns.length < 2) this.form.careConcerns.push(value)
      else uni.showToast({ title: '最多选择 2 项', icon: 'none' })
    },
    async save() {
      if (this.saving) return
      if (this.form.guardianRole === 'unknown') return uni.showToast({ title: '请选择您是宝宝的哪位家属', icon: 'none' })
      this.saving = true
      try {
        const saved = await saveProfileContext({ ...this.form, complete: true })
        this.form = { ...this.form, ...(saved || {}), careConcerns: Array.isArray(saved && saved.careConcerns) ? [...saved.careConcerns] : this.form.careConcerns }
        uni.showToast({ title: '修改已保存', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 500)
      } catch (error) {
        uni.showToast({ title: (error && error.message) || '保存失败', icon: 'none' })
      } finally { this.saving = false }
    },
  },
}
</script>

<style lang="scss" scoped>
.page{height:100vh;background:linear-gradient(160deg,$ivory,#EEECE7);display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 10rpx;display:flex;justify-content:space-between;align-items:center}.back,.blank{width:60rpx}.back{font-size:52rpx;color:$gold-deep}.title{font-family:$font-cn-serif;font-size:31rpx}.scroll{flex:1}.intro{padding:28rpx 40rpx}.intro-title{display:block;font-family:$font-cn-serif;font-size:39rpx}.intro-sub{display:block;color:$ink-3;font-size:23rpx;margin-top:6rpx}.loading{margin:0 34rpx;padding:60rpx 34rpx;text-align:center;color:$ink-3;background:rgba(255,255,255,.96);border:1rpx solid $hair;border-radius:38rpx;box-shadow:$shadow-soft}.card{margin:0 34rpx 80rpx;background:rgba(255,255,255,.96);border:1rpx solid $hair;border-radius:38rpx;padding:34rpx;box-shadow:$shadow-soft}.field,.group{padding:10rpx 0 24rpx;border-bottom:1rpx solid $hair;margin-bottom:20rpx}.field.row{display:flex;justify-content:space-between;align-items:center}.label{display:block;color:$ink-2;font-size:23rpx;margin-bottom:12rpx}.field input{height:62rpx;font-size:28rpx}.chips{display:flex;flex-wrap:wrap;gap:14rpx}.chip{padding:13rpx 22rpx;border:1rpx solid $hair-s;border-radius:40rpx;color:$ink-2;font-size:23rpx}.chip.on{background:$foil;color:#fff;border-color:$gold}.stage{display:flex;justify-content:space-between;padding:18rpx 20rpx;border-radius:20rpx;margin-top:10rpx;background:$platinum-foil}.stage .dot{opacity:0}.stage.on{color:$gold-deep;background:$gold-soft}.stage.on .dot{opacity:1}.save{margin-top:34rpx;border:0;border-radius:28rpx;background:$foil;color:#fff;height:90rpx;line-height:90rpx}.save::after{border:0}.privacy{display:block;text-align:center;color:$ink-3;font-size:20rpx;margin-top:20rpx;line-height:1.6}
</style>
