<template>
  <view class="screen">
    <view class="topbar"><text class="back" @tap="back">‹</text><view><text class="title">客房清洁与检查</text><text class="sub">按楼层处理即将入住与退房客房</text></view></view>
    <scroll-view scroll-x class="tabs"><view class="tabs-in"><text v-for="item in filters" :key="item.value" :class="['tab',filter===item.value?'on':'']" @tap="changeFilter(item.value)">{{item.label}}</text></view></scroll-view>
    <scroll-view scroll-y class="body">
      <view class="summary"><view><text>{{rows.length}}</text><small>当前任务</small></view><view><text>{{pendingCount}}</text><small>待处理</small></view><view><text>{{abnormalCount}}</text><small>异常</small></view></view>
      <view v-if="loading" class="empty">正在加载客房任务…</view>
      <view v-else-if="!groups.length" class="empty">当前筛选下没有客房任务</view>
      <view v-for="group in groups" :key="group.floor" class="floor-block">
        <view class="floor-head"><text>{{group.floor}}F</text><text>{{group.tasks.length}} 项</text></view>
        <view v-for="task in group.tasks" :key="task.taskId" class="task-card" @tap="openTask(task)">
          <view class="task-top"><view><text class="room">{{task.roomNo}} · {{task.roomType}}</text><text class="customer">{{task.customerName || '待确认客户'}} · {{task.checkIn}} 至 {{task.checkOut}}</text></view><text :class="['pill',statusClass(task.status)]">{{task.status}}</text></view>
          <view class="task-bottom"><text>{{task.taskType}}</text><text>计划 {{task.scheduledDate}} ›</text></view>
        </view>
      </view>
      <view class="bottom-space"></view>
    </scroll-view>

    <view v-if="active" class="mask" @tap.self="active=null">
      <scroll-view scroll-y class="sheet">
        <view class="sheet-head"><view><text class="sheet-title">{{active.roomNo}} · {{active.taskType}}</text><text>{{active.customerName || '待确认客户'}} · {{active.scheduledDate}}</text></view><text class="close" @tap="active=null">×</text></view>
        <text class="label">检查清单</text>
        <view class="checklist"><view v-for="item in checklistOptions" :key="item" :class="['check',selectedChecks.includes(item)?'checked':'']" @tap="toggleCheck(item)"><text>{{selectedChecks.includes(item)?'✓':'○'}}</text>{{item}}</view></view>
        <text class="label">执行说明 / 异常情况</text>
        <textarea v-model.trim="resultNote" maxlength="500" placeholder="可填写缺失物品、设备故障、补做事项等" />
        <view class="actions"><button class="start" :disabled="saving" @tap="save('处理中')">开始处理</button><button class="done" :disabled="saving" @tap="save('已完成')">完成</button></view>
        <button class="danger" :disabled="saving" @tap="save('异常')">标记异常并上报</button>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import { loadRoomTurnoverTasks, saveRoomTurnoverTask } from '@/common/remote.js'
const OPTIONS={
  '入住前清洁':['床品更换','地面清洁','卫生间消毒','母婴用品补齐','垃圾清运','通风除味'],
  '入住前检查':['空调与新风','热水与卫浴','灯光与插座','门锁与呼叫器','婴儿床安全','房间影像留档'],
  '退房清洁':['床品回收','地面清洁','卫生间消毒','垃圾清运','深度消毒','通风除味'],
  '退房物品清点':['布草清点','母婴用品清点','电器设备检查','家具破损检查','遗留物登记','房间影像留档'],
}
export default{
  data(){return{loading:false,saving:false,rows:[],filter:'',active:null,selectedChecks:[],resultNote:'',filters:[{label:'全部',value:''},{label:'待处理',value:'待处理'},{label:'处理中',value:'处理中'},{label:'异常',value:'异常'},{label:'已完成',value:'已完成'}]}},
  computed:{
    groups(){const map={};for(const row of this.rows){const f=Number(row.floor||0);(map[f]||(map[f]=[])).push(row)}return Object.keys(map).map(Number).sort((a,b)=>a-b).map(f=>({floor:f,tasks:map[f]}))},
    pendingCount(){return this.rows.filter(x=>x.status==='待处理'||x.status==='处理中').length},
    abnormalCount(){return this.rows.filter(x=>x.status==='异常').length},
    checklistOptions(){return OPTIONS[(this.active&&this.active.taskType)||'']||[]},
  },
  onLoad(){this.load()},onPullDownRefresh(){this.load().finally(()=>uni.stopPullDownRefresh())},
  methods:{
    back(){uni.navigateBack()},statusClass(s){return s==='已完成'?'ok':s==='异常'?'bad':s==='处理中'?'doing':'wait'},
    async changeFilter(v){this.filter=v;await this.load()},
    async load(){this.loading=true;try{this.rows=await loadRoomTurnoverTasks(this.filter)||[]}catch(e){uni.showToast({title:e.message||'任务加载失败',icon:'none'})}finally{this.loading=false}},
    openTask(task){this.active=task;this.selectedChecks=Array.isArray(task.checklist)?[...task.checklist]:[];this.resultNote=task.resultNote||''},
    toggleCheck(item){const i=this.selectedChecks.indexOf(item);if(i>=0)this.selectedChecks.splice(i,1);else this.selectedChecks.push(item)},
    async save(status){if(this.saving)return;if(status==='已完成'&&this.selectedChecks.length<this.checklistOptions.length){return uni.showModal({title:'清单尚未完成',content:'请完成全部检查项；如存在问题，请选择“标记异常并上报”。',showCancel:false})}this.saving=true;try{await saveRoomTurnoverTask(this.active.taskId,{status,checklist:this.selectedChecks,resultNote:this.resultNote});uni.showToast({title:status==='已完成'?'任务已完成':'状态已更新',icon:'success'});this.active=null;await this.load()}catch(e){uni.showToast({title:e.message||'保存失败',icon:'none'})}finally{this.saving=false}},
  }
}
</script>

<style lang="scss" scoped>
.screen{height:100vh;display:flex;flex-direction:column;background:$ivory}.topbar{display:flex;align-items:center;gap:20rpx;padding:34rpx 28rpx 18rpx;background:#FFFDF8}.back{width:58rpx;height:58rpx;line-height:52rpx;text-align:center;border-radius:50%;background:#F1E8D8;color:$gold-deep;font-size:48rpx}.title,.sub{display:block}.title{font-family:$font-cn-serif;font-size:34rpx;color:$gold-deep}.sub{margin-top:4rpx;color:$ink-3;font-size:19rpx}.tabs{flex:none;background:#FFFDF8;white-space:nowrap}.tabs-in{display:flex;padding:10rpx 28rpx 20rpx;gap:14rpx}.tab{padding:10rpx 22rpx;border-radius:22rpx;background:#F2EBDD;color:$ink-3;font-size:20rpx}.tab.on{background:$gold-deep;color:#fff}.body{flex:1}.summary{display:flex;margin:22rpx 28rpx;padding:22rpx 0;border-radius:24rpx;background:#fff;border:1rpx solid $hair}.summary view{flex:1;text-align:center;border-right:1rpx solid $hair}.summary view:last-child{border:0}.summary text,.summary small{display:block}.summary text{font-family:$font-display;font-size:34rpx;color:$gold-deep}.summary small{margin-top:4rpx;color:$ink-3;font-size:18rpx}.floor-block{margin:0 28rpx 24rpx}.floor-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12rpx;color:$ink-3;font-size:20rpx}.floor-head text:first-child{font-family:$font-display;font-size:31rpx;color:$gold-deep}.task-card{padding:22rpx;margin-bottom:12rpx;border-radius:24rpx;background:#fff;border:1rpx solid $hair;box-shadow:0 8rpx 24rpx rgba(82,60,25,.05)}.task-top,.task-bottom{display:flex;justify-content:space-between;align-items:flex-start}.room,.customer{display:block}.room{font-size:25rpx;color:$ink}.customer{margin-top:7rpx;color:$ink-3;font-size:18rpx}.pill{padding:6rpx 14rpx;border-radius:18rpx;font-size:18rpx}.pill.wait{background:#F6ECD7;color:#96661F}.pill.doing{background:#E3EBF6;color:#426893}.pill.ok{background:#E2F0E4;color:#39704A}.pill.bad{background:#F8E1DE;color:#A94339}.task-bottom{margin-top:18rpx;padding-top:15rpx;border-top:1rpx solid $hair;color:$gold-deep;font-size:20rpx}.task-bottom text:last-child{color:$ink-3}.empty{text-align:center;padding:150rpx 30rpx;color:$ink-3}.bottom-space{height:80rpx}.mask{position:fixed;inset:0;z-index:80;display:flex;align-items:flex-end;background:rgba(28,21,14,.55)}.sheet{box-sizing:border-box;width:100%;max-height:88vh;padding:30rpx 32rpx calc(env(safe-area-inset-bottom) + 28rpx);border-radius:38rpx 38rpx 0 0;background:#FFFDF8}.sheet-head{display:flex;justify-content:space-between}.sheet-head text{display:block;color:$ink-3;font-size:19rpx}.sheet-title{font-family:$font-cn-serif!important;font-size:31rpx!important;color:$gold-deep!important}.close{font-size:40rpx!important}.label{display:block;margin:26rpx 0 12rpx;color:$gold-deep;font-size:22rpx}.checklist{display:grid;grid-template-columns:1fr 1fr;gap:12rpx}.check{padding:17rpx;border:1rpx solid $hair;border-radius:17rpx;background:#fff;color:$ink-2;font-size:20rpx}.check text{margin-right:9rpx;color:#B49A70}.check.checked{border-color:#8C6A36;background:#F0E5D0;color:$gold-deep}.sheet textarea{box-sizing:border-box;width:100%;height:130rpx;padding:18rpx;border-radius:18rpx;background:$ivory;font-size:21rpx}.actions{display:flex;gap:14rpx;margin-top:22rpx}.actions button{flex:1;margin:0}.start{background:#EFE4D0;color:$gold-deep}.done{background:$gold-deep;color:#fff}.danger{margin-top:14rpx;background:#F6E2DF;color:#A94339}.actions button::after,.danger::after{border:0}
</style>
