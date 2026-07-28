<template>
  <view class="page">
    <view class="top"><text class="back" @tap="leave">‹</text><text class="title">家庭成员与绑定</text><text class="blank"></text></view>
    <scroll-view scroll-y class="scroll"><view class="pad">
      <view class="hero"><text class="moon">☾</text><text class="h">让家人安心加入</text><text class="s">由宝妈出示二维码，家属使用自己的账号扫码验证</text></view>
      <view v-if="isMother" class="card qr-card">
        <template v-if="loadingQr"><view class="qr-placeholder">正在创建安全二维码…</view></template>
        <template v-else-if="qrSrc">
          <image class="qr" mode="aspectFit" :src="qrSrc" />
          <text class="expire">一次性使用 · {{expiresText}} 前有效</text>
          <text class="tip">请让真实家属打开微信扫一扫。绑定后，家属可使用自己的手机号登录。</text>
        </template>
        <template v-else><text class="error">{{qrError||'点击下方按钮创建家庭二维码'}}</text></template>
        <button class="generate" :loading="loadingQr" :disabled="loadingQr" @tap="generate">{{qrSrc?'重新生成':'创建家庭绑定二维码'}}</button>
      </view>
      <view v-else class="card note"><text class="note-title">当前账号不是宝妈账号</text><text>只有宝妈可以生成验证二维码；其他家属可扫描宝妈出示的二维码加入家庭。</text></view>

      <view class="section-title">已验证家庭成员</view>
      <view class="card list">
        <view v-for="b in bindings" :key="b.binding_id" class="member"><view class="avatar">{{initial(b)}}</view><view class="info"><text class="name">{{memberName(b)}}</text><text class="role">{{relationName(b)}}<text v-if="b.baby_name"> · 关联 {{b.baby_name}}</text></text></view><text class="ok">已验证</text></view>
        <view v-if="!bindings.length" class="empty">暂时没有已验证的家庭成员</view>
      </view>
      <button v-if="welcome" class="home" @tap="home">暂时跳过，进入首页</button>
    </view></scroll-view>
  </view>
</template>
<script>
import { createFamilyInvite, loadFamilyBindings, loadProfileContext, REMOTE } from '@/common/remote.js'
const REL={father:'宝宝爸爸',grandparent:'宝宝祖辈',sibling:'宝宝兄弟姐妹',relative:'其他亲属',other:'自定义家属'}
export default{
  data(){return{welcome:false,isMother:false,loadingQr:false,qrSrc:'',qrError:'',expiresAt:'',bindings:[]}},
  computed:{expiresText(){if(!this.expiresAt)return'';const d=new Date(this.expiresAt);return (d.getMonth()+1)+'月'+d.getDate()+'日 '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')}},
  async onLoad(opt){this.welcome=String(opt&&opt.welcome||'')==='1';try{const [profile,bindings]=await Promise.all([loadProfileContext(),loadFamilyBindings()]);this.isMother=profile.guardianRole==='mother';this.bindings=bindings||[];if(this.welcome&&this.isMother)this.generate()}catch(e){uni.showToast({title:e.message||'家庭信息加载失败',icon:'none'})}},
  methods:{
    async generate(){this.loadingQr=true;this.qrError='';this.qrSrc='';try{const r=await createFamilyInvite({});this.expiresAt=r.expiresAt;this.qrSrc='data:'+(r.mime||'image/png')+';base64,'+r.imageBase64}catch(e){this.qrError=e.message||'二维码创建失败，请稍后重试'}finally{this.loadingQr=false}},
    memberName(b){return Number(REMOTE.customerId)===Number(b.owner_customer_id)?(b.member_name||'家庭成员'):(b.owner_name||'宝妈')},
    initial(b){return this.memberName(b).charAt(0)||'家'},
    relationName(b){return b.custom_identity||REL[b.relationship]||'家庭成员'},
    home(){uni.switchTab({url:'/pages/home/home'})},
    leave(){if(this.welcome)this.home();else uni.navigateBack()},
  },
}
</script>
<style lang="scss" scoped>
.page{height:100vh;background:linear-gradient(160deg,$ivory,#EEECE7);display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 10rpx;display:flex;justify-content:space-between;align-items:center}.back,.blank{width:60rpx}.back{font-size:52rpx;color:$gold-deep}.title{font-family:$font-cn-serif;font-size:31rpx}.scroll{flex:1}.pad{padding:10rpx 34rpx 90rpx}.hero{text-align:center;padding:28rpx 20rpx}.moon{display:block;color:$gold;font-size:54rpx}.h{display:block;font-family:$font-cn-serif;font-size:39rpx}.s{display:block;color:$ink-3;font-size:22rpx;margin-top:8rpx;line-height:1.7}.card{background:rgba(255,255,255,.96);border:1rpx solid $hair;border-radius:34rpx;padding:30rpx;box-shadow:$shadow-soft}.qr-card{text-align:center}.qr{width:430rpx;height:430rpx}.qr-placeholder{height:430rpx;display:flex;align-items:center;justify-content:center;color:$ink-3}.expire,.tip{display:block}.expire{color:$gold-deep;font-size:22rpx}.tip{margin:14rpx auto 0;max-width:520rpx;color:$ink-3;font-size:21rpx;line-height:1.7}.generate{margin-top:26rpx;border:0;border-radius:26rpx;background:$foil;color:#fff}.generate::after,.home::after{border:0}.error{display:block;color:#A04545;padding:60rpx 10rpx}.note-title{display:block;font-family:$font-cn-serif;font-size:28rpx;margin-bottom:12rpx}.note{color:$ink-2;font-size:22rpx;line-height:1.7}.section-title{font-family:$font-cn-serif;font-size:29rpx;margin:36rpx 8rpx 18rpx}.list{padding:8rpx 28rpx}.member{display:flex;align-items:center;padding:22rpx 0;border-bottom:1rpx solid $hair}.member:last-child{border-bottom:0}.avatar{width:72rpx;height:72rpx;border-radius:24rpx;background:$platinum-foil;color:$gold-deep;display:flex;align-items:center;justify-content:center;font-size:28rpx;margin-right:20rpx}.info{flex:1}.name{font-size:26rpx}.role{display:block;color:$ink-3;font-size:20rpx;margin-top:5rpx}.ok{color:#4A8060;font-size:20rpx}.empty{text-align:center;color:$ink-3;padding:55rpx 10rpx;font-size:22rpx}.home{margin-top:26rpx;background:rgba(255,255,255,.72);color:$gold-deep;border:1rpx solid $hair-s;border-radius:26rpx}
</style>
