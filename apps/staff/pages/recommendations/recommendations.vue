<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">专家服务建议</text><text class="refresh" @tap="load">刷新</text></view>
    <scroll-view scroll-y class="scroll"><view class="pad">
      <view class="card form">
        <text class="head">新建人工建议</text>
        <picker :range="customers" range-key="name" @change="pickCustomer"><view class="pick">客户：{{ selectedCustomer ? selectedCustomer.name : '请选择' }} ›</view></picker>
        <view class="switches"><view :class="['chip',subjectType==='mom'&&'on']" @tap="subjectType='mom'">宝妈</view><view :class="['chip',subjectType==='baby'&&'on']" @tap="subjectType='baby';loadBabies()">宝宝</view></view>
        <picker v-if="subjectType==='baby'" :range="babies" range-key="name" @change="babyIndex=Number($event.detail.value)"><view class="pick">宝宝：{{ babies[babyIndex] ? (babies[babyIndex].name||'宝宝') : '请选择' }} ›</view></picker>
        <input v-model="title" class="input" maxlength="80" placeholder="建议标题，如：本周恢复服务建议" />
        <textarea v-model="summary" class="textarea" maxlength="500" placeholder="简要说明观察到的状态（可选）" />
        <text class="label">选择服务项目（最多 10 项）</text>
        <checkbox-group @change="selectedItemIds=$event.detail.value">
          <label v-for="it in items" :key="it.item_id" class="item"><checkbox :value="String(it.item_id)" color="#8C6A36"/><view><text>{{it.name}}</text><text class="sub">{{it.domain||''}} · ¥{{price(it)}}</text></view></label>
        </checkbox-group>
        <textarea v-model="reason" class="textarea" maxlength="300" placeholder="填写选择这些服务的原因，将展示给用户" />
        <button class="submit" :loading="saving" @tap="submit">发送给用户确认</button>
        <text class="hint">当前为专家人工判断，不调用 Agent；每个项目都会保存建议原因。</text>
      </view>

      <text class="section">已发送建议</text>
      <view v-for="r in recommendations" :key="r.recommendation_id" class="card">
        <view class="line"><text class="head">{{r.title}}</text><text class="status">{{r.status}}</text></view>
        <text class="meta">{{r.customer_name}} · {{r.subject_type==='baby'?(r.baby_name||'宝宝'):'宝妈'}} · {{r.expert_name||'专家'}}</text>
        <text v-if="r.summary" class="summary">{{r.summary}}</text>
        <view v-for="it in r.items" :key="it.recommendation_item_id" class="result">
          <view class="line"><text>{{it.item_name}}</text><text :class="['choice',it.choice_status==='已拒绝'&&'no']">{{it.choice_status||'待选择'}}</text></view>
          <text class="why">原因：{{it.reason}}</text>
          <text v-if="it.choice_status==='已拒绝'" class="reject">拒绝原因：{{rejectText(it)}}</text>
        </view>
      </view>
      <view v-if="!recommendations.length&&!loading" class="empty">暂无服务建议</view>
    </view></scroll-view>
  </view>
</template>

<script>
import { loadServiceRecommendationWorkbench, loadRecommendationBabies, createServiceRecommendation } from '@/common/remote.js'
export default {
  data(){return{loading:false,saving:false,recommendations:[],customers:[],items:[],customerIndex:-1,subjectType:'mom',babies:[],babyIndex:0,title:'',summary:'',reason:'',selectedItemIds:[]}},
  computed:{selectedCustomer(){return this.customerIndex>=0?this.customers[this.customerIndex]:null}},
  onShow(){this.load()},
  methods:{
    back(){uni.navigateBack()},price(it){return Number(it.sale_price||it.exp_price||0).toFixed(2)},
    rejectText(it){let a=[];try{a=JSON.parse(it.reject_reason_codes||'[]')}catch(_){a=[]}return [...a,it.reject_reason_text].filter(Boolean).join('、')||'未填写'},
    async load(){this.loading=true;try{const d=await loadServiceRecommendationWorkbench();this.recommendations=d.recommendations;this.customers=d.customers;this.items=d.items.filter(x=>x.cat!=='耗材')}catch(e){uni.showToast({title:e.message||'加载失败',icon:'none'})}finally{this.loading=false}},
    async pickCustomer(e){this.customerIndex=Number(e.detail.value);this.babies=[];this.babyIndex=0;if(this.subjectType==='baby')await this.loadBabies()},
    async loadBabies(){if(!this.selectedCustomer)return;try{this.babies=await loadRecommendationBabies(this.selectedCustomer.customer_id)||[]}catch(_){this.babies=[]}},
    async submit(){
      if(!this.selectedCustomer)return uni.showToast({title:'请选择客户',icon:'none'});
      if(!this.title.trim()||!this.reason.trim())return uni.showToast({title:'请填写标题和推荐原因',icon:'none'});
      if(!this.selectedItemIds.length||this.selectedItemIds.length>10)return uni.showToast({title:'请选择 1 至 10 个项目',icon:'none'});
      if(this.subjectType==='baby'&&!this.babies[this.babyIndex])return uni.showToast({title:'请选择宝宝',icon:'none'});
      this.saving=true;try{
        await createServiceRecommendation({customerId:this.selectedCustomer.customer_id,subjectType:this.subjectType,babyId:this.subjectType==='baby'?this.babies[this.babyIndex].baby_id:null,title:this.title,summary:this.summary,items:this.selectedItemIds.map((id,i)=>({itemId:Number(id),priority:i+1,reason:this.reason}))});
        this.title='';this.summary='';this.reason='';this.selectedItemIds=[];uni.showToast({title:'已发送',icon:'success'});await this.load();
      }catch(e){uni.showToast({title:e.message||'发送失败',icon:'none'})}finally{this.saving=false}
    }
  }
}
</script>

<style lang="scss" scoped>
.page{height:100vh;background:$ivory;display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 12rpx;display:flex;align-items:center;justify-content:space-between}.back{font-size:52rpx;color:$gold-deep;width:60rpx}.title{font-family:$font-cn-serif;font-size:31rpx}.refresh{width:60rpx;text-align:right;color:$gold-deep;font-size:22rpx}.scroll{flex:1}.pad{padding:18rpx 30rpx 100rpx}.card{background:#fff;border:1rpx solid $hair;border-radius:28rpx;padding:28rpx;margin-bottom:20rpx}.head{font-family:$font-cn-serif;font-size:29rpx}.pick,.input,.textarea{box-sizing:border-box;width:100%;background:$ivory;border:1rpx solid $hair;border-radius:18rpx;margin-top:18rpx;padding:20rpx;font-size:24rpx}.textarea{height:130rpx}.switches{display:flex;gap:14rpx;margin-top:18rpx}.chip{padding:12rpx 30rpx;border:1rpx solid $hair;border-radius:40rpx;color:$ink-3}.chip.on{background:$gold-deep;color:#fff}.label,.section{display:block;font-family:$font-cn-serif;font-size:26rpx;margin:24rpx 0 12rpx}.section{font-size:30rpx}.item{display:flex;align-items:center;gap:16rpx;padding:18rpx 4rpx;border-bottom:1rpx solid $hair;font-size:24rpx}.sub,.meta,.summary,.why,.reject,.hint{display:block}.sub,.meta,.hint{font-size:20rpx;color:$ink-3;margin-top:5rpx}.submit{margin-top:22rpx;background:$gold-deep;color:#fff;border-radius:50rpx;font-size:25rpx}.submit::after{border:0}.hint{text-align:center;margin-top:12rpx}.line{display:flex;justify-content:space-between;gap:20rpx}.status,.choice{color:$gold-deep;font-size:21rpx}.choice.no,.reject{color:#A04545}.summary{font-size:23rpx;margin-top:14rpx}.result{background:$ivory;border-radius:18rpx;padding:18rpx;margin-top:16rpx;font-size:24rpx}.why,.reject{font-size:21rpx;margin-top:8rpx}.empty{text-align:center;color:$ink-3;padding:120rpx 20rpx}
</style>
