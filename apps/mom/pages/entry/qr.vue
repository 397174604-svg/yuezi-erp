<template>
  <view class="page">
    <view class="top"><text class="back" @tap="home">‹</text><text class="title">{{context.sceneType==='family_bind'?'家庭验证':'到店服务'}}</text><text class="blank"></text></view>
    <view v-if="loading" class="state">正在识别二维码…</view>
    <view v-else-if="error" class="state"><text class="err">{{error}}</text><button class="ghost" @tap="load">重新识别</button></view>
    <scroll-view v-else scroll-y class="scroll">
      <view class="hero"><text class="moon">☾</text><text class="ht">{{context.title}}</text><text v-if="context.sceneType==='family_bind'" class="hs">{{context.ownerName}} 邀请您加入<text v-if="context.babyName"> · {{context.babyName}}的家庭</text></text><text v-else class="hs">{{context.storeName}}<text v-if="context.roomNo"> · 房间 {{context.roomNo}}</text></text></view>

      <view v-if="context.sceneType==='family_bind'" class="family-form">
        <text class="ft">您是宝宝的哪位家属？</text>
        <view class="chips"><view v-for="r in relations" :key="r.v" :class="['chip',relationship===r.v&&'on']" @tap="relationship=r.v">{{r.l}}</view></view>
        <input v-if="relationship==='other'" v-model.trim="customIdentity" maxlength="30" placeholder="请填写身份，如：姨妈、舅舅" />
        <text class="privacy">绑定后继续使用您自己的手机号登录；宝妈授权范围内的家庭信息才会与您共享。</text>
        <button class="submit" :loading="submitting" :disabled="submitting" @tap="bindFamily">确认加入家庭</button>
      </view>

      <template v-else>
        <view class="list"><view v-for="a in context.actions" :key="a.id" class="action" @tap="choose(a)"><view><text class="al">{{a.label}}</text><text class="ad">{{a.desc}}</text></view><text class="arrow">›</text></view></view>
        <view v-if="selected" class="form"><text class="ft">{{selected.label}}</text><textarea v-model.trim="content" maxlength="300" :placeholder="selected.id==='rehab_booking'?'请填写意向项目（选填）':'请简要说明您的需求（选填）'" />
          <picker mode="date" :value="date" @change="date=$event.detail.value"><view class="date">期望日期：{{date||'请选择（选填）'}} ›</view></picker>
          <button class="submit" :loading="submitting" @tap="submit">确认提交</button><button class="cancel" @tap="selected=null">取消</button>
        </view>
        <view class="foot" @tap="toRequests">查看我的服务进度 ›</view>
      </template>
    </scroll-view>
  </view>
</template>
<script>
import { acceptFamilyInvite, createServiceRequest, goLogin, isAuthenticated, resolveQrContext } from '@/common/remote.js'
export default{
  data(){return{scene:'',loading:true,error:'',context:{actions:[]},selected:null,content:'',date:'',submitting:false,relationship:'',customIdentity:'',relations:[{v:'father',l:'爸爸'},{v:'grandparent',l:'爷爷奶奶 / 姥姥姥爷'},{v:'sibling',l:'哥哥姐姐'},{v:'relative',l:'其他亲属'},{v:'other',l:'自定义身份'}]}},
  onLoad(opt){this.scene=decodeURIComponent((opt&&opt.scene)||'');if(!isAuthenticated()){goLogin('/pages/entry/qr?scene='+encodeURIComponent(this.scene));return}this.load()},
  methods:{
    home(){uni.switchTab({url:'/pages/home/home'})},
    async load(){this.loading=true;this.error='';try{this.context=await resolveQrContext(this.scene)}catch(e){this.error=e.message||'二维码无法使用'}finally{this.loading=false}},
    choose(a){if(a.id==='visit_booking')return uni.navigateTo({url:'/pages/visit/booking'});this.selected=a;this.content='';this.date=''},
    async bindFamily(){if(!this.relationship)return uni.showToast({title:'请选择与宝宝的关系',icon:'none'});if(this.relationship==='other'&&!this.customIdentity)return uni.showToast({title:'请填写您的身份',icon:'none'});this.submitting=true;try{await acceptFamilyInvite({scene:this.scene,relationship:this.relationship,customIdentity:this.customIdentity});uni.showToast({title:'家庭绑定成功',icon:'success'});setTimeout(()=>uni.redirectTo({url:'/pages/profile/onboarding'}),500)}catch(e){uni.showToast({title:e.message||'绑定失败',icon:'none'})}finally{this.submitting=false}},
    async submit(){if(this.submitting)return;this.submitting=true;try{await createServiceRequest({scene:this.scene,requestType:this.selected.id,content:this.content,preferredTime:this.date});uni.showToast({title:'已提交',icon:'success'});this.selected=null}catch(e){uni.showToast({title:e.message||'提交失败',icon:'none'})}finally{this.submitting=false}},
    toRequests(){uni.navigateTo({url:'/pages/service/requests'})},
  },
}
</script>
<style lang="scss" scoped>
.page { min-height: 100vh; background: linear-gradient(160deg, $ivory, $ivory-2); color: $ink; }
.top { display: flex; align-items: center; justify-content: space-between; padding: calc(env(safe-area-inset-top) + 20rpx) 34rpx 16rpx; border-bottom: 1rpx solid rgba(170,164,154,.26); background: rgba(250,249,246,.92); }
.back,.blank { width: 60rpx; }
.back { color: $gold-deep; font-size: 52rpx; }
.title { font-family: $font-cn-serif; font-size: 31rpx; }
.scroll { height: calc(100vh - 110rpx); }
.state { padding: 180rpx 50rpx; color: $ink-3; text-align: center; }
.state .err { display: block; }
.ghost { margin-top: 30rpx; border: 1rpx solid $hair-s; background: $paper; color: $gold-deep; }
.hero { margin: 28rpx 34rpx 34rpx; padding: 54rpx 36rpx 46rpx; border: 1rpx solid $platinum; border-radius: 38rpx; background: $platinum-foil; box-shadow: $shadow-soft; text-align: center; }
.moon { display: block; color: $gold; font-size: 64rpx; }
.ht { display: block; font-family: $font-cn-serif; font-size: 40rpx; }
.hs { display: block; margin-top: 10rpx; color: $ink-3; font-size: 23rpx; }
.list { padding: 0 34rpx; }
.action { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18rpx; padding: 28rpx 30rpx; border: 1rpx solid $hair; border-radius: 28rpx; background: rgba(255,255,255,.96); box-shadow: $shadow-soft; }
.al { display: block; font-family: $font-cn-serif; font-size: 29rpx; }
.ad { display: block; margin-top: 5rpx; color: $ink-3; font-size: 21rpx; }
.arrow { color: $gold-deep; font-size: 42rpx; }
.form,.family-form { margin: 26rpx 34rpx; padding: 30rpx; border: 1rpx solid $hair; border-radius: 32rpx; background: $paper; color: $ink; box-shadow: $shadow-soft; }
.ft { display: block; font-family: $font-cn-serif; font-size: 31rpx; }
.form textarea { width: 100%; height: 150rpx; box-sizing: border-box; margin-top: 20rpx; padding: 20rpx; border: 1rpx solid $platinum; border-radius: 20rpx; background: $ivory; font-size: 25rpx; }
.date { padding: 22rpx 4rpx; border-bottom: 1rpx solid $hair; color: $ink-2; }
.submit { margin-top: 26rpx; border: 0; background: $foil; color: #fff; box-shadow: 0 16rpx 34rpx -22rpx rgba(94,74,38,.62); }
.cancel { border: 0; background: transparent; color: $ink-3; }
.submit::after,.cancel::after { border: 0; }
.foot { padding: 44rpx 20rpx 80rpx; color: $gold-deep; font-size: 23rpx; text-align: center; }
.chips { display: flex; flex-wrap: wrap; gap: 14rpx; margin-top: 24rpx; }
.chip { padding: 13rpx 20rpx; border: 1rpx solid $hair-s; border-radius: 40rpx; color: $ink-2; font-size: 22rpx; }
.chip.on { border-color: $gold-deep; background: $foil; color: #fff; }
.family-form input { height: 72rpx; margin-top: 22rpx; padding: 0 18rpx; border-radius: 18rpx; background: $ivory; font-size: 24rpx; }
.privacy { display: block; margin-top: 24rpx; color: $ink-3; font-size: 20rpx; line-height: 1.7; }
</style>
