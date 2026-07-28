<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳 · 产后康复</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">产后康复中心<text class="sm">项目价格依据 2025-08-21 销售政策 · 预约前由专家评估</text></view>
        <scroll-view scroll-x class="tabs"><view class="tab-row"><view v-for="c in categories" :key="c" :class="['tab',active===c&&'on']" @tap="active=c">{{c}}</view></view></scroll-view>
        <view v-if="loading" class="empty">正在加载项目…</view>
        <view v-else-if="!filtered.length" class="empty">暂无可预约项目</view>
        <view v-for="item in filtered" :key="item.itemId" class="project">
          <view class="head"><view><text class="cat">{{item.category}}</text><text class="name">{{item.name}}</text></view><text class="single">¥{{money(item.singlePrice)}}<text>/{{item.unit||'次'}}</text></text></view>
          <view v-if="item.coursePrice" class="course"><text>疗程参考</text><text class="course-price">¥{{money(item.coursePrice)}}<text v-if="item.courseTimes"> / {{item.courseTimes}}次</text></text></view>
          <view class="action"><text>适用条件及疗程以评估结果为准</text><button @tap="open(item)">预约咨询</button></view>
        </view>
        <view class="policy"><text class="policy-title">当前销售政策说明</text><text v-for="(p,i) in policies" :key="i" class="policy-line">{{i+1}}. {{p}}</text></view>
      </view>
    </scroll-view>

    <view v-if="selected" class="mask" @tap.self="selected=null"><view class="sheet">
      <text class="sheet-title">预约咨询 · {{selected.name}}</text>
      <picker mode="date" :value="form.date" @change="form.date=$event.detail.value"><view class="field"><text>期望到店日期</text><text>{{form.date||'请选择（选填）'}} ›</text></view></picker>
      <textarea v-model.trim="form.note" maxlength="200" placeholder="可填写当前关注的问题或希望了解的疗程（选填）" />
      <button class="submit" :loading="submitting" :disabled="submitting" @tap="submit">提交咨询</button>
      <button class="cancel" @tap="selected=null">取消</button>
    </view></view>
  </view>
</template>
<script>
import { createDirectRequest, loadRehabCatalog } from '@/common/remote.js'
export default{
  data(){return{loading:true,items:[],policies:[],active:'全部',selected:null,submitting:false,form:{date:'',note:''}}},
  computed:{categories(){return['全部',...new Set(this.items.map(x=>x.category))]},filtered(){return this.active==='全部'?this.items:this.items.filter(x=>x.category===this.active)}},
  async onLoad(){try{const r=await loadRehabCatalog();this.items=(r&&r.items)||[];this.policies=(r&&r.policies)||[]}catch(e){uni.showToast({title:e.message||'项目加载失败',icon:'none'})}finally{this.loading=false}},
  methods:{
    money(v){return Number(v||0).toLocaleString()},open(item){this.selected=item;this.form={date:'',note:''}},
    async submit(){if(this.submitting)return;this.submitting=true;try{await createDirectRequest({requestType:'rehab_booking',itemId:this.selected.itemId,preferredDate:this.form.date,note:this.form.note});uni.showToast({title:'咨询已提交',icon:'success'});this.selected=null}catch(e){uni.showToast({title:e.message||'提交失败',icon:'none'})}finally{this.submitting=false}},
  },
}
</script>
<style lang="scss" scoped>
.screen{display:flex;flex-direction:column;height:100vh}.topbar{padding:28rpx 40rpx 8rpx}.nm{font-family:$font-display;font-size:35rpx;letter-spacing:3rpx;color:$gold-deep}.scroll{flex:1}.pad{padding:8rpx 34rpx 160rpx}.greet{font-family:$font-cn-serif;font-size:42rpx;font-weight:500}.sm{display:block;font-family:$font-sans;font-size:22rpx;color:$ink-3;margin-top:10rpx;line-height:1.6}.tabs{width:100%;white-space:nowrap;margin:28rpx 0 8rpx}.tab-row{display:flex;gap:14rpx}.tab{display:inline-block;padding:12rpx 24rpx;border-radius:40rpx;background:$paper;border:1rpx solid $platinum;font-size:22rpx;color:$ink-2}.tab.on{background:$foil;color:#fff;border-color:transparent}.project{margin-top:20rpx;padding:28rpx;background:rgba(255,255,255,.96);border:1rpx solid $platinum;border-radius:30rpx;box-shadow:$shadow-soft}.head{display:flex;justify-content:space-between;gap:20rpx}.head>view{flex:1}.cat{display:block;color:$gold-deep;font-size:19rpx}.name{display:block;font-family:$font-cn-serif;font-size:29rpx;margin-top:6rpx}.single{font-family:$font-display;font-size:30rpx;color:$gold-deep;white-space:nowrap}.single text{font-family:$font-sans;font-size:19rpx}.course{display:flex;justify-content:space-between;margin-top:20rpx;padding:18rpx 20rpx;border-radius:18rpx;background:$ivory-2;color:$ink-2;font-size:21rpx}.course-price{color:$gold-deep}.action{display:flex;align-items:center;justify-content:space-between;gap:16rpx;margin-top:20rpx;color:$ink-3;font-size:19rpx}.action button{margin:0;padding:0 22rpx;border:0;border-radius:40rpx;background:$foil;color:#fff;font-size:21rpx}.action button::after{border:0}.policy{margin-top:30rpx;padding:28rpx;border:1rpx solid $platinum;border-radius:28rpx;background:$platinum-foil;color:$ink-2}.policy-title{display:block;font-family:$font-cn-serif;font-size:27rpx;margin-bottom:14rpx}.policy-line{display:block;font-size:20rpx;line-height:1.8}.empty{text-align:center;color:$ink-3;padding:120rpx 20rpx}.mask{position:fixed;inset:0;background:rgba(39,37,33,.34);display:flex;align-items:flex-end;z-index:10;backdrop-filter:blur(8rpx)}.sheet{width:100%;box-sizing:border-box;padding:40rpx 38rpx calc(env(safe-area-inset-bottom) + 30rpx);border-radius:40rpx 40rpx 0 0;background:$paper}.sheet-title{display:block;font-family:$font-cn-serif;font-size:32rpx;margin-bottom:24rpx}.field{display:flex;justify-content:space-between;padding:24rpx 0;border-bottom:1rpx solid $hair;font-size:24rpx}.sheet textarea{width:100%;box-sizing:border-box;height:150rpx;margin-top:24rpx;padding:20rpx;border:1rpx solid $platinum;border-radius:20rpx;background:$ivory;font-size:24rpx}.submit{margin-top:26rpx;background:$foil;color:#fff;border:0;border-radius:26rpx}.cancel{background:transparent;color:$ink-3;border:0}.submit::after,.cancel::after{border:0}
</style>
