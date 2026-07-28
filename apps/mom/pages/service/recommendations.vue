<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">专家服务建议</text><text class="refresh" @tap="load">刷新</text></view>
    <scroll-view scroll-y class="scroll"><view class="pad">
      <view class="notice">以下内容由会所专家根据已记录情况人工选择，不替代医疗诊断。您可以逐项选择或拒绝，拒绝原因可不填。</view>
      <view v-for="r in rows" :key="r.recommendation_id" class="card">
        <view class="line"><text class="head">{{r.title}}</text><text class="status">{{r.status}}</text></view>
        <text class="meta">{{r.subject_type==='baby'?(r.baby_name||'宝宝'):'宝妈'}} · {{r.expert_name||'专家'}} · {{fmt(r.sent_at||r.created_at)}}</text>
        <text v-if="r.summary" class="summary">{{r.summary}}</text>
        <view v-for="it in r.items" :key="it.recommendation_item_id" class="service">
          <view class="line"><text class="name">{{it.item_name}}</text><text class="price">¥{{Number(it.price_snapshot||0).toFixed(2)}}</text></view>
          <text class="why">推荐原因：{{it.reason}}</text>
          <view v-if="it.choice_status" class="chosen"><text :class="it.choice_status==='已拒绝'?'no':''">{{it.choice_status}}</text><text v-if="it.choice_status==='已拒绝'&&rejectText(it)" class="reason">{{rejectText(it)}}</text></view>
          <view v-else class="actions"><button size="mini" class="reject" @tap="reject(r,it)">暂不选择</button><button size="mini" class="accept" @tap="accept(r,it)">选择此服务</button></view>
        </view>
      </view>
      <view v-if="!rows.length&&!loading" class="empty">专家暂未发送服务建议</view>
    </view></scroll-view>
  </view>
</template>

<script>
import { loadServiceRecommendations, chooseServiceRecommendation } from '@/common/remote.js'
const REASONS=['暂不需要','价格原因','时间不合适','想先了解','身体状态不允许','家人意见','其他']
export default{
  data(){return{rows:[],loading:false}},onShow(){this.load()},onPullDownRefresh(){this.load().finally(()=>uni.stopPullDownRefresh())},
  methods:{
    back(){uni.navigateBack()},fmt(v){return String(v||'').replace('T',' ').slice(0,16)},
    rejectText(it){let a=[];try{a=JSON.parse(it.reject_reason_codes||'[]')}catch(_){a=[]}return[...a,it.reject_reason_text].filter(Boolean).join('、')},
    async load(){this.loading=true;try{this.rows=await loadServiceRecommendations()}catch(e){uni.showToast({title:e.message||'加载失败',icon:'none'})}finally{this.loading=false}},
    async save(r,it,input){try{await chooseServiceRecommendation(r.recommendation_id,{recommendationItemId:it.recommendation_item_id,...input});uni.showToast({title:'已保存',icon:'success'});await this.load()}catch(e){uni.showToast({title:e.message||'保存失败',icon:'none'})}},
    async accept(r,it){const ok=await new Promise(resolve=>uni.showModal({title:'选择此服务',content:'确认选择“'+it.item_name+'”？会所人员将与您进一步确认时间和安排。',success:x=>resolve(x.confirm),fail:()=>resolve(false)}));if(ok)await this.save(r,it,{choiceStatus:'已选择'})},
    reject(r,it){uni.showActionSheet({itemList:[...REASONS,'不填写原因'],success:async e=>{if(e.tapIndex===REASONS.length)return this.save(r,it,{choiceStatus:'已拒绝'});const code=REASONS[e.tapIndex];if(code!=='其他')return this.save(r,it,{choiceStatus:'已拒绝',rejectReasonCodes:[code]});uni.showModal({title:'其他原因（可选）',editable:true,placeholderText:'简单说明即可',success:x=>{if(x.confirm)this.save(r,it,{choiceStatus:'已拒绝',rejectReasonCodes:['其他'],rejectReasonText:x.content||''})}})}})}
  }
}
</script>

<style lang="scss" scoped>
.page{height:100vh;background:$ivory;display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 12rpx;display:flex;align-items:center;justify-content:space-between}.back{font-size:52rpx;color:$gold-deep;width:60rpx}.title{font-family:$font-cn-serif;font-size:31rpx}.refresh{width:60rpx;text-align:right;color:$gold-deep;font-size:22rpx}.scroll{flex:1}.pad{padding:20rpx 32rpx 100rpx}.notice{background:#F5E7CA;color:$ink-2;border-radius:22rpx;padding:22rpx;font-size:21rpx;line-height:1.7;margin-bottom:20rpx}.card{background:#fff;border:1rpx solid $hair;border-radius:28rpx;padding:28rpx;margin-bottom:20rpx}.line{display:flex;justify-content:space-between;gap:20rpx}.head{font-family:$font-cn-serif;font-size:30rpx}.status,.price{font-size:22rpx;color:$gold-deep}.meta,.summary,.why{display:block}.meta{font-size:20rpx;color:$ink-3;margin-top:8rpx}.summary{font-size:24rpx;margin-top:18rpx}.service{background:$ivory;border-radius:20rpx;padding:22rpx;margin-top:20rpx}.name{font-family:$font-cn-serif;font-size:27rpx}.why{font-size:22rpx;color:$ink-2;line-height:1.7;margin-top:12rpx}.actions{display:flex;justify-content:flex-end;gap:14rpx;margin-top:20rpx}.actions button{margin:0;border-radius:40rpx;font-size:22rpx}.actions button::after{border:0}.reject{background:#EEE8DE;color:$ink-2}.accept{background:$gold-deep;color:#fff}.chosen{display:flex;gap:12rpx;margin-top:18rpx;color:#4A8060;font-size:22rpx}.chosen .no{color:#A04545}.reason{color:$ink-3}.empty{text-align:center;color:$ink-3;padding:160rpx 20rpx}
</style>
