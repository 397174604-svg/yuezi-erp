<template>
  <view class="screen">
    <view class="topbar"><text class="nm">奇德芬芳 · 3D 选房</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="greet">选择分店与房间<text class="sm">先选择分店，再拖动楼体查看真实楼层与房型</text></view>

        <scroll-view scroll-x class="store-scroll" :show-scrollbar="false">
          <view class="store-track">
            <view v-for="store in stores" :key="store.storeId" :class="['store-card',Number(store.storeId)===Number(selectedStoreId)?'active':'']" @tap="switchStore(store)">
              <image class="store-thumb" mode="aspectFill" :src="storePhoto(store)" />
              <view class="store-copy">
                <text class="store-name">{{storeShortName(store.name)}}</text>
                <text class="store-address">{{store.address || '濮阳 · 奇德芬芳'}}</text>
                <text class="store-count">{{store.roomCount || 0}} 间可订房</text>
              </view>
              <text v-if="Number(store.storeId)===Number(selectedStoreId)" class="store-check">已选择</text>
            </view>
          </view>
        </scroll-view>

        <view v-if="selectedStore" class="store-hero">
          <image mode="aspectFill" :src="storePhoto(selectedStore)" />
          <view class="store-shade"></view>
          <view class="store-hero-copy">
            <text class="store-kicker">{{isHuangheStore ? '黄河路店 · 实景效果' : '奇德芬芳 · 分店实景'}}</text>
            <text class="store-hero-name">{{storeShortName(selectedStore.name)}}</text>
            <text>{{selectedStore.address || '河南 · 濮阳'}}</text>
          </view>
          <view class="store-stats"><text>{{bookableRoomCount}} 间</text><text>{{bookableFloorCount}} 个住宿楼层</text></view>
        </view>

        <view class="date-card">
          <picker mode="date" :value="dates.checkIn" @change="changeDate('checkIn',$event)"><view class="date"><text>预计入住</text><text>{{dates.checkIn}} ›</text></view></picker>
          <view class="date-line"></view>
          <picker mode="date" :value="dates.checkOut" @change="changeDate('checkOut',$event)"><view class="date"><text>预计离店</text><text>{{dates.checkOut}} ›</text></view></picker>
        </view>

        <view class="orders-card">
          <view class="orders-head"><text>我的订房</text><text @tap="loadOrders">刷新</text></view>
          <view v-if="!orders.length" class="orders-empty">还没有正式订房记录</view>
          <view v-for="order in orders.slice(0,3)" :key="order.bookingId" class="order-row">
            <view><text class="order-room">{{order.roomNo}} · {{order.roomType}}</text><text class="order-date">{{storeShortName(order.storeName)}} · {{order.checkIn}} 至 {{order.checkOut}}</text></view>
            <view class="order-state"><text :class="['state',stateClass(order)]">{{order.paymentStatus || order.status}}</text><text>¥{{money(order.amount)}}</text><text v-if="order.status==='待支付'" class="order-cancel" @tap.stop="cancelOrder(order)">取消锁房</text></view>
          </view>
        </view>

        <view class="legend"><text><i class="dot free"></i>可选</text><text><i class="dot busy"></i>档期占用</text><text><i class="dot chosen"></i>当前选择</text><text v-if="isHuangheStore"><i class="dot facility"></i>功能层</text></view>
        <view v-if="loading" class="empty">正在生成整栋楼选房模型…</view>
        <view v-else-if="!floors.length" class="empty">当前门店尚未配置可展示房间</view>

        <view v-else class="viewer">
          <view class="viewer-head">
            <view><text class="view-title">{{viewerTitle}}</text><text class="view-sub">{{viewerSub}}</text></view>
            <view class="viewer-actions"><button class="reset-head" @tap="resetView">还原视角</button><button v-if="focusedFloor" class="building-btn" @tap="exitFloor">返回整栋</button></view>
          </view>

          <view class="control-bar">
            <button aria-label="向左旋转45度" @tap="turn(-45)">↶</button>
            <view class="camera-info"><text>方向 {{yawLabel}}</text><text>水平 {{Math.round(yaw)}}° · 俯视 {{Math.round(pitch)}}°</text></view>
            <button aria-label="向右旋转45度" @tap="turn(45)">↷</button>
          </view>

          <view class="stage" @touchstart="touchStart" @touchmove.stop.prevent="touchMove" @touchend="touchEnd">
            <view v-if="!focusedFloor" class="scene stack-scene" :style="sceneTransform">
              <view v-for="(floor,index) in floors" :key="floor.floor" :class="['stack-floor',floor.facility?'facility-floor-card':'']" :style="stackFloorStyle(index)" @tap="openFloor(floor)">
                <view class="floor-badge"><text>{{floor.floor}}F</text><text class="badge-count">{{floor.facility ? '产康功能层' : floor.availableCount+' 可选'}}</text></view>
                <view v-if="floor.facility" class="facility-mini"><text>产康中心</text><text>瑜伽 · 洗护 · 调理</text></view>
                <view v-else class="mini-layout">
                  <view v-for="room in previewRooms(floor)" :key="room.roomId" :class="['mini-room',room.available?'free':'busy']"></view>
                </view>
                <view class="floor-edge"><text>{{floor.facility ? floor.name : floor.roomCount+' 间房'}}</text></view>
              </view>
              <text class="panorama-south">南</text>
            </view>

            <view v-else class="scene focus-scene" :style="sceneTransform">
              <view v-if="focusedFloor.facility" class="facility-detail">
                <image mode="aspectFill" :src="focusedFloor.image" />
                <view class="facility-overlay"><text class="facility-title">2F 产康中心</text><text class="facility-desc">本层用于产后康复与日常活动，不参与客房预订</text><view class="facility-spaces"><text v-for="space in focusedFloor.spaces" :key="space">{{space}}</text></view></view>
              </view>
              <view v-else class="floor-3d">
                <view class="wall wall-n"></view><view class="wall wall-e"></view><view class="wall wall-s"></view><view class="wall wall-w"></view>
                <text class="map-dir dir-n">北</text><text class="map-dir dir-e">东</text><text class="map-dir dir-s">南</text><text class="map-dir dir-w">西</text>
                <view class="rooms-row north-row"><view v-for="room in directionRooms('北')" :key="room.roomId" :class="roomClass(room)" @tap.stop="choose(room)"><text>{{room.roomNo}}</text><text class="type-small">{{shortType(room.roomType)}}</text></view></view>
                <view class="middle-row">
                  <view class="rooms-side west-row"><view v-for="room in directionRooms('西')" :key="room.roomId" :class="roomClass(room)" @tap.stop="choose(room)"><text>{{room.roomNo}}</text><text class="type-small">{{shortType(room.roomType)}}</text></view></view>
                  <view class="corridor"><text>安静走廊</text><view class="lift">电梯</view></view>
                  <view class="rooms-side east-row"><view v-for="room in directionRooms('东')" :key="room.roomId" :class="roomClass(room)" @tap.stop="choose(room)"><text>{{room.roomNo}}</text><text class="type-small">{{shortType(room.roomType)}}</text></view></view>
                </view>
                <view class="rooms-row south-row"><view v-for="room in directionRooms('南')" :key="room.roomId" :class="roomClass(room)" @tap.stop="choose(room)"><text>{{room.roomNo}}</text><text class="type-small">{{shortType(room.roomType)}}</text></view></view>
              </view>
            </view>
          </view>
          <text class="gesture">左右拖动可 360° 旋转 · 上下拖动调节俯视角度</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="selected" class="mask" @tap.self="selected=null">
      <scroll-view scroll-y class="sheet">
        <image class="photo" mode="aspectFit" :src="photoOf(selected)" />
        <view class="room-head"><view><text class="sheet-title">{{selected.roomNo}} · {{selected.roomType}}</text><text class="room-loc">{{storeShortName(selectedStore&&selectedStore.name)}} · {{selected.floor}}楼 · {{selected.direction}}向</text></view><text class="price">¥{{money(selected.price)}}<text class="price-unit">/日</text></text></view>
        <text class="desc">{{selected.layoutNote || descriptionOf(selected.roomType)}}</text>
        <view v-if="roomFeatures(selected).length" class="room-features"><text v-for="feature in roomFeatures(selected)" :key="feature">{{feature}}</text></view>
        <view class="period"><text>{{dates.checkIn}}</text><text>入住 {{stayDays}} 晚</text><text>{{dates.checkOut}}</text></view>
        <textarea v-model.trim="note" maxlength="200" placeholder="补充需求，如陪住人数、采光偏好（选填）" />
        <view class="amount-line"><text>预计 {{stayDays}} 晚</text><text>合计 ¥{{money(totalAmount)}}</text></view>
        <button class="buy" :loading="submitting" :disabled="submitting" @tap="buy">立即订购并锁定 {{selected.roomNo}}</button>
        <button class="submit" :loading="submitting" :disabled="submitting" @tap="submit">仅预约咨询（不锁房）</button>
        <button class="cancel" @tap="selected=null">继续选房</button>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import { createDirectRequest, loadRoomLayout, loadRoomOrders, createRoomOrder, cancelRoomOrder, sandboxPayRoomOrder } from '@/common/remote.js'
import doubleRoom from '@/static/rooms/double-room.jpg'
import specialRoom from '@/static/rooms/special-room.jpg'
import smallSuite from '@/static/rooms/small-suite.jpg'
import suite from '@/static/rooms/suite.jpg'
import vip302 from '@/static/rooms/vip302.jpg'
import vip512 from '@/static/rooms/vip512.jpg'
import huangheFacade from '@/static/rooms/huanghe/facade.jpg'
import huangheRehab from '@/static/rooms/huanghe/rehab-floor.jpg'
import huangheBase from '@/static/rooms/huanghe/base-room.jpg'
import huangheRepair from '@/static/rooms/huanghe/repair-suite.jpg'
import huanghePresident from '@/static/rooms/huanghe/presidential-suite.jpg'
import huangheQueen from '@/static/rooms/huanghe/queen-suite.jpg'
const ASSETS={
  '大床房':[doubleRoom,'宽敞大床与母婴同室空间，适合重视通透感的家庭'],
  '特价房':[specialRoom,'保留核心母婴照护配置，更注重性价比'],
  '小套房':[smallSuite,'卧室与起居功能兼顾，适合少量家属陪住'],
  '套房':[suite,'独立起居区域，满足家属陪伴与会客需求'],
  'VIP302':[vip302,'尊享楼层房型，兼顾私密、采光与活动空间'],
  'VIP512':[vip512,'高端尊享套房，适合重视空间和家庭陪伴的客户'],
  '基础大床':[huangheBase,'黄河路店4楼北向大床房，母婴同室，空间温暖通透'],
  '基础套餐':[huangheBase,'黄河路店5楼北向大床房，适合偏好安静采光的家庭'],
  '修复套餐':[huangheRepair,'一房一厅布局，休息与家属陪伴区域相互独立'],
  '总统套':[huanghePresident,'5楼最北侧三室三厅，提供更完整的家庭陪住空间'],
  '女王套':[huangheQueen,'6楼整层独立两室两厅，兼顾私密、采光与家庭活动空间'],
}
const HUANGHE_FACILITY={floor:2,name:'产康中心',roomCount:0,availableCount:0,rooms:[],facility:true,image:huangheRehab,spaces:['瑜伽室','洗发区','产康护理室','电梯厅']}
function localDate(add=0){const d=new Date();d.setDate(d.getDate()+add);const p=n=>String(n).padStart(2,'0');return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())}
function normalAngle(n){return((n%360)+360)%360}
function isHuanghe(store){return /黄河路/.test(String(store&&store.name||''))}
export default{
  data(){return{loading:true,submitting:false,stores:[],selectedStoreId:null,floors:[],orders:[],focusedFloor:null,yaw:0,pitch:56,dragStart:{x:0,y:0,yaw:0,pitch:56},dragMoved:false,selected:null,note:'',dates:{checkIn:localDate(30),checkOut:localDate(58)}}},
  computed:{
    selectedStore(){return this.stores.find(store=>Number(store.storeId)===Number(this.selectedStoreId))||null},
    isHuangheStore(){return isHuanghe(this.selectedStore)},
    bookableRoomCount(){return this.floors.reduce((sum,floor)=>sum+(floor.facility?0:Number(floor.roomCount||0)),0)},
    bookableFloorCount(){return this.floors.filter(floor=>!floor.facility&&floor.roomCount).length},
    viewerTitle(){if(!this.focusedFloor)return `${this.storeShortName(this.selectedStore&&this.selectedStore.name)} · 楼体总览`;return this.focusedFloor.facility?'2F 产康功能层':`${this.focusedFloor.floor}F 房间布局`},
    viewerSub(){if(!this.focusedFloor)return '点击露出的楼层或楼层编号进入该层';return this.focusedFloor.facility?'查看瑜伽、洗护与产康护理空间':`${this.focusedFloor.availableCount} 间可选 · 点击房间查看真实效果`},
    sceneTransform(){const scale=this.focusedFloor?1:(this.floors.length>=5?.7:.78);return `transform: perspective(1250rpx) rotateX(${this.pitch}deg) rotateZ(${this.yaw}deg) scale(${scale})`},
    yawLabel(){const a=normalAngle(this.yaw);return a<45||a>=315?'北':a<135?'东':a<225?'南':'西'},
    stayDays(){const a=new Date(this.dates.checkIn+'T00:00:00'),b=new Date(this.dates.checkOut+'T00:00:00');return Math.max(1,Math.round((b-a)/86400000))},
    totalAmount(){return Number(((this.selected&&this.selected.price)||0)*this.stayDays)},
  },
  onLoad(){this.load();this.loadOrders()},
  onBackPress(){if(this.selected){this.selected=null;return true}if(this.focusedFloor){this.exitFloor();return true}return false},
  methods:{
    async load(){
      if(!this.dates.checkIn||!this.dates.checkOut||this.dates.checkIn>=this.dates.checkOut)return uni.showToast({title:'请选择有效入住日期',icon:'none'})
      this.loading=true
      try{
        const data=await loadRoomLayout({...this.dates,...(this.selectedStoreId?{storeId:this.selectedStoreId}:{})})
        const active=this.focusedFloor&&this.focusedFloor.floor
        this.stores=data.stores||[]
        this.selectedStoreId=Number(data.selectedStoreId||this.selectedStoreId||0)||null
        const floors=[...(data.floors||[])]
        if(this.isHuangheStore&&!floors.some(floor=>Number(floor.floor)===2))floors.push({...HUANGHE_FACILITY})
        this.floors=floors.sort((a,b)=>Number(b.floor)-Number(a.floor))
        this.focusedFloor=active?(this.floors.find(f=>Number(f.floor)===Number(active))||null):null
        this.selected=null
      }catch(e){uni.showToast({title:e.message||'房间加载失败',icon:'none'})}finally{this.loading=false}
    },
    async loadOrders(){try{this.orders=await loadRoomOrders()||[]}catch(e){this.orders=[]}},
    async switchStore(store){if(this.loading||Number(store.storeId)===Number(this.selectedStoreId))return;this.selectedStoreId=Number(store.storeId);this.focusedFloor=null;this.selected=null;this.resetView(false);await this.load()},
    changeDate(key,e){this.dates[key]=e.detail.value;if(this.dates.checkIn&&this.dates.checkOut&&this.dates.checkIn<this.dates.checkOut)this.load()},
    previewRooms(floor){return(floor.rooms||[]).slice(0,20)},
    stackFloorStyle(index){const z=(this.floors.length-index)*52,y=index*42,x=index*6;return`transform:translate3d(${x}rpx,${y}rpx,${z}rpx);z-index:${this.floors.length-index}`},
    openFloor(floor){if(this.dragMoved)return;this.focusedFloor=floor;this.selected=null},
    exitFloor(){this.focusedFloor=null;this.selected=null},
    directionRooms(direction){return((this.focusedFloor&&this.focusedFloor.rooms)||[]).filter(r=>r.direction===direction).sort((a,b)=>a.layoutOrder-b.layoutOrder||String(a.roomNo).localeCompare(String(b.roomNo)))},
    shortType(type){const s=String(type||'标准房');return s.length>5?s.slice(0,5):s},
    roomClass(room){return['room-seat',room.available?'free':'busy',/总统/.test(room.roomType)?'president':/女王/.test(room.roomType)?'queen':/基础/.test(room.roomType)?'base':'repair',this.selected&&this.selected.roomId===room.roomId?'chosen':'']},
    choose(room){if(this.dragMoved)return;if(!room.available)return uni.showToast({title:'该房间所选日期已被预订',icon:'none'});this.selected=room;this.note=''},
    turn(step){this.yaw=normalAngle(this.yaw+step)},
    resetView(showToast=true){this.yaw=0;this.pitch=56;if(showToast)uni.showToast({title:'视角已还原',icon:'none'})},
    touchStart(e){const t=e.changedTouches[0];this.dragStart={x:t.clientX,y:t.clientY,yaw:this.yaw,pitch:this.pitch};this.dragMoved=false},
    touchMove(e){const t=e.changedTouches[0],dx=t.clientX-this.dragStart.x,dy=t.clientY-this.dragStart.y;if(Math.abs(dx)>4||Math.abs(dy)>4)this.dragMoved=true;this.yaw=normalAngle(this.dragStart.yaw+dx*1.05);this.pitch=Math.max(25,Math.min(76,this.dragStart.pitch-dy*.28))},
    touchEnd(){setTimeout(()=>{this.dragMoved=false},80)},
    storePhoto(store){return isHuanghe(store)?huangheFacade:suite},
    storeShortName(name){return String(name||'奇德芬芳').replace(/^奇德芬芳[·\s]*/,'').replace(/\(中心店\)/,'')},
    photoOf(room){const local=ASSETS[room.roomType]||ASSETS['套房'];return room.imageUrl||local[0]},
    descriptionOf(type){return(ASSETS[type]||ASSETS['套房'])[1]},
    roomFeatures(room){if(/总统/.test(room.roomType))return['三室三厅','5楼最北侧','家庭陪住'];if(/女王/.test(room.roomType))return['两室两厅','6楼独享','高私密'];if(/修复/.test(room.roomType))return['一房一厅','独立起居','母婴同室'];if(/基础/.test(room.roomType))return['大床房','北向采光','母婴同室'];return[]},
    money(v){return Number(v||0).toLocaleString()},
    stateClass(order){return order.paymentStatus==='已支付'?'paid':order.status==='已取消'?'closed':'pending'},
    async cancelOrder(order){const ok=await new Promise(resolve=>uni.showModal({title:'取消锁房',content:`确认释放 ${order.roomNo} 的所选日期吗？`,success:r=>resolve(r.confirm),fail:()=>resolve(false)}));if(!ok)return;try{await cancelRoomOrder(order.bookingId);uni.showToast({title:'房间已释放',icon:'success'});await Promise.all([this.loadOrders(),this.load()])}catch(e){uni.showToast({title:e.message||'取消失败',icon:'none'})}},
    requestWechatPayment(payload){return new Promise((resolve,reject)=>uni.requestPayment({...payload,success:resolve,fail:reject}))},
    async buy(){if(this.submitting)return;this.submitting=true;const picked=this.selected;try{const order=await createRoomOrder({roomId:picked.roomId,checkIn:this.dates.checkIn,checkOut:this.dates.checkOut,note:this.note});if(order.provider==='sandbox'){await sandboxPayRoomOrder(order.bookingId);uni.showModal({title:'订房成功',content:`${picked.roomNo} 已与您的账号和入住日期绑定。本地演示已模拟支付成功。`,showCancel:false})}else{await this.requestWechatPayment(order.prepay||{});uni.showModal({title:'支付已提交',content:'微信支付结果以服务端回调为准，订单状态会自动更新。',showCancel:false})}this.selected=null;await Promise.all([this.load(),this.loadOrders()])}catch(e){uni.showToast({title:e.message||e.errMsg||'订购失败',icon:'none'});await this.loadOrders()}finally{this.submitting=false}},
    async submit(){if(this.submitting)return;this.submitting=true;try{await createDirectRequest({requestType:'room_booking',roomId:this.selected.roomId,checkIn:this.dates.checkIn,checkOut:this.dates.checkOut,note:this.note});uni.showModal({title:'预约意向已提交',content:`已选择 ${this.selected.roomNo}，顾问确认档期后会联系您。`,showCancel:false});this.selected=null;await this.load()}catch(e){uni.showToast({title:e.message||'提交失败',icon:'none'})}finally{this.submitting=false}},
  }
}
</script>

<style lang="scss" scoped>
.screen{display:flex;flex-direction:column;height:100vh}.topbar{padding:28rpx 36rpx 8rpx}.nm{font-family:$font-display;font-size:35rpx;letter-spacing:3rpx;color:$gold-deep}.scroll{flex:1}.pad{padding:8rpx 28rpx 160rpx}.greet{font-family:$font-cn-serif;font-size:40rpx}.sm{display:block;font-family:$font-sans;font-size:22rpx;color:$ink-3;margin-top:8rpx}.date-card{display:flex;align-items:center;margin-top:24rpx;padding:18rpx 22rpx;background:rgba(255,255,255,.96);border:1rpx solid $hair;border-radius:26rpx;box-shadow:$shadow-soft}.date-card picker{flex:1}.date{display:flex;flex-direction:column;font-size:20rpx;color:$ink-3}.date text:last-child{font-size:25rpx;color:$ink;margin-top:5rpx}.date-line{width:1rpx;height:54rpx;background:$hair;margin:0 24rpx}.legend{display:flex;justify-content:center;gap:24rpx;margin:24rpx 0 8rpx;font-size:18rpx;color:$ink-2}.dot{display:inline-block;width:16rpx;height:16rpx;border-radius:5rpx;margin-right:7rpx}.dot.free{background:#DDEBDD}.dot.busy{background:#D8D2C8}.dot.chosen{background:$gold}.viewer{margin-top:18rpx;background:$platinum-foil;border:1rpx solid $hair;border-radius:34rpx;padding:24rpx 16rpx 28rpx;overflow:hidden;box-shadow:$shadow-soft}.viewer-head{display:flex;align-items:center;justify-content:space-between;padding:0 12rpx}.view-title{display:block;font-family:$font-cn-serif;font-size:27rpx;color:$gold-deep}.view-sub{display:block;color:$ink-3;font-size:18rpx;margin-top:4rpx}.building-btn{margin:0;padding:0 20rpx;height:58rpx;line-height:58rpx;border:1rpx solid $hair;background:#fff;color:$gold-deep;border-radius:30rpx;font-size:20rpx}.building-btn::after{border:0}.control-bar{display:flex;align-items:center;gap:8rpx;margin-top:18rpx;padding:10rpx;border-radius:22rpx;background:rgba(255,255,255,.72)}.control-bar button{margin:0;padding:0 12rpx;height:54rpx;line-height:54rpx;white-space:nowrap;border:1rpx solid $hair;background:#fff;color:$gold-deep;border-radius:28rpx;font-size:18rpx}.control-bar button::after{border:0}.control-bar .reset{background:$foil;color:#fff}.camera-info{flex:1;text-align:center;color:$gold-deep;font-size:18rpx}.camera-info text{display:block}.camera-info text:last-child{font-size:15rpx;color:$ink-3}.stage{height:720rpx;display:flex;align-items:center;justify-content:center;perspective:1400rpx;overflow:visible}.scene{position:relative;width:570rpx;height:500rpx;transform-style:preserve-3d;transition:transform .18s ease-out}.stack-scene{margin-top:-70rpx}.stack-floor{position:absolute;inset:0;box-sizing:border-box;background:linear-gradient(135deg,rgba(255,255,255,.98),rgba(218,214,206,.98));border:4rpx solid $platinum-deep;border-radius:28rpx;transform-style:preserve-3d;box-shadow:0 18rpx 0 #B8B2A8,0 28rpx 30rpx rgba(66,58,44,.18)}.floor-badge{position:absolute;left:-24rpx;bottom:20rpx;z-index:5;min-width:100rpx;padding:10rpx 16rpx;border-radius:12rpx;background:$foil;color:#fff;box-shadow:0 8rpx 14rpx rgba(66,58,44,.22)}.floor-badge text,.floor-badge small{display:block}.floor-badge text{font-family:$font-display;font-size:27rpx}.floor-badge small{font-size:16rpx}.mini-layout{position:absolute;inset:50rpx;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;gap:12rpx;padding:28rpx;border:1rpx dashed rgba(135,109,62,.3);background:repeating-linear-gradient(90deg,rgba(255,255,255,.42) 0 22rpx,rgba(170,164,154,.08) 22rpx 44rpx)}.mini-room{width:50rpx;height:38rpx;border:2rpx solid $platinum-deep;border-radius:7rpx;box-shadow:0 7rpx 0 #B8B2A8}.mini-room.free{background:#E7F1E5}.mini-room.busy{background:#CFC8BC;opacity:.72}.floor-edge{position:absolute;right:20rpx;bottom:14rpx;color:$ink-2;font-size:18rpx}.map-dir{position:absolute;z-index:8;width:42rpx;height:42rpx;line-height:42rpx;text-align:center;border-radius:50%;background:$foil;color:#fff;font-size:18rpx;box-shadow:0 7rpx 12rpx rgba(66,58,44,.2)}.dir-n{left:50%;top:-22rpx;margin-left:-21rpx}.dir-s{left:50%;bottom:-22rpx;margin-left:-21rpx}.dir-w{left:-22rpx;top:50%;margin-top:-21rpx}.dir-e{right:-22rpx;top:50%;margin-top:-21rpx}.focus-scene{width:570rpx;height:500rpx}.floor-3d{position:relative;width:570rpx;height:500rpx;padding:24rpx;box-sizing:border-box;background:$platinum-foil;border:4rpx solid $platinum-deep;border-radius:34rpx;transform-style:preserve-3d;box-shadow:0 46rpx 45rpx -24rpx rgba(66,58,44,.32)}.wall{position:absolute;background:$platinum-deep;opacity:.72}.wall-n,.wall-s{left:12rpx;right:12rpx;height:10rpx}.wall-n{top:10rpx}.wall-s{bottom:10rpx}.wall-e,.wall-w{top:12rpx;bottom:12rpx;width:10rpx}.wall-e{right:10rpx}.wall-w{left:10rpx}.rooms-row{height:112rpx;display:flex;justify-content:center;gap:10rpx}.south-row{position:absolute;left:24rpx;right:24rpx;bottom:18rpx;align-items:flex-end}.middle-row{display:flex;height:245rpx;justify-content:space-between}.rooms-side{width:120rpx;display:flex;flex-direction:column;gap:8rpx;justify-content:center}.east-row{align-items:flex-end}.corridor{flex:1;margin:16rpx;background:repeating-linear-gradient(90deg,rgba(255,255,255,.55) 0 20rpx,rgba(170,164,154,.09) 20rpx 40rpx);border:1rpx dashed rgba(135,109,62,.3);display:flex;align-items:center;justify-content:center;position:relative;color:$ink-3;font-size:18rpx}.lift{position:absolute;bottom:12rpx;background:$platinum-deep;color:#fff;border-radius:8rpx;padding:5rpx 12rpx}.room-seat{width:88rpx;height:86rpx;flex:none;box-sizing:border-box;border-radius:12rpx;border:2rpx solid $platinum-deep;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;transform:translateZ(22rpx);box-shadow:0 12rpx 0 #B8B2A8,0 18rpx 18rpx rgba(66,58,44,.18);transition:.18s}.rooms-side .room-seat{width:108rpx;height:52rpx}.room-seat text{font-family:$font-display;font-size:22rpx;color:$gold-deep;line-height:1}.room-seat .type-small{display:block;font-size:18rpx;margin-top:3rpx;color:$ink-2}.room-seat.busy{background:#D8D2C8;border-color:#B5AEA2;box-shadow:0 8rpx 0 #9E978B;opacity:.7}.room-seat.chosen{background:$foil;border-color:$gold-deep;box-shadow:0 14rpx 0 #9C814F,0 0 28rpx rgba(195,165,101,.5)}.room-seat.chosen text{color:#fff}.gesture{display:block;text-align:center;color:$ink-3;font-size:18rpx}.empty{text-align:center;color:$ink-3;padding:130rpx 20rpx}.mask{position:fixed;inset:0;background:rgba(39,37,33,.38);display:flex;align-items:flex-end;z-index:50}.sheet{width:100%;max-height:88vh;box-sizing:border-box;padding:0 34rpx calc(env(safe-area-inset-bottom) + 28rpx);border-radius:40rpx 40rpx 0 0;background:$paper;overflow:hidden}.photo{width:calc(100% + 68rpx);height:340rpx;margin-left:-34rpx}.room-head{display:flex;justify-content:space-between;align-items:flex-start;margin-top:26rpx}.sheet-title{display:block;font-family:$font-cn-serif;font-size:33rpx}.room-loc{display:block;color:$ink-3;font-size:21rpx;margin-top:6rpx}.price{font-family:$font-display;font-size:34rpx;color:$gold-deep}.price-unit{font-size:22rpx;font-weight:400;color:$ink-2}.desc{display:block;color:$ink-2;font-size:22rpx;line-height:1.7;margin-top:18rpx}.period{display:flex;justify-content:space-between;margin-top:22rpx;padding:20rpx;border-radius:20rpx;background:$platinum-foil;color:$ink-2;font-size:20rpx}.sheet textarea{width:100%;height:120rpx;box-sizing:border-box;margin-top:20rpx;padding:18rpx;border-radius:18rpx;background:$ivory;font-size:22rpx}.submit{margin-top:22rpx;background:$foil;color:#fff;border:0}.cancel{background:transparent;color:$ink-3;border:0}.submit::after,.cancel::after{border:0}
.floor-badge .badge-count{display:block;font-family:$font-sans;font-size:14rpx}.scene{transition:none}.floor-3d{animation:floorZoom .32s ease-out}.viewer-actions{display:flex;align-items:center;gap:8rpx;margin-left:12rpx}.viewer-actions button{margin:0;padding:0 16rpx;height:54rpx;line-height:54rpx;border-radius:28rpx;font-size:18rpx;white-space:nowrap}.viewer-actions button::after{border:0}.reset-head{border:0;background:$gold-deep;color:#fff}.control-bar{max-width:440rpx;margin:16rpx auto 0;padding:7rpx}.control-bar button{width:58rpx;padding:0;font-size:28rpx}.camera-info{min-width:230rpx}.stage{height:700rpx}.stack-scene{margin-top:100rpx;transform-origin:50% 70%}.stack-floor{background:linear-gradient(135deg,rgba(255,252,244,.68),rgba(209,184,140,.58));border-color:rgba(143,108,56,.78);box-shadow:0 12rpx 0 rgba(118,87,47,.78),0 22rpx 26rpx rgba(64,44,17,.16)}.stack-floor .mini-layout{background:rgba(255,255,255,.08);border-color:rgba(140,106,54,.25)}.stack-floor .mini-room{box-shadow:0 5rpx 0 rgba(120,94,54,.85)}.floor-badge{left:-18rpx;bottom:10rpx;z-index:30;min-width:86rpx;padding:6rpx 12rpx}.floor-badge text:first-child{font-size:24rpx}.panorama-south{position:absolute;left:50%;bottom:-66rpx;z-index:999;width:48rpx;height:48rpx;line-height:48rpx;text-align:center;border-radius:50%;background:$gold-deep;color:#fff;font-size:19rpx;box-shadow:0 7rpx 14rpx rgba(52,35,12,.3);transform:translate3d(-50%,0,520rpx)}@keyframes floorZoom{from{transform:translateZ(-120rpx) scale(.78);opacity:.35}to{transform:translateZ(0) scale(1);opacity:1}}
.orders-card{margin-top:18rpx;padding:20rpx 22rpx;background:rgba(255,255,255,.96);border:1rpx solid $hair;border-radius:24rpx;box-shadow:$shadow-soft}.orders-head{display:flex;justify-content:space-between;color:$gold-deep;font-size:23rpx}.orders-head text:last-child{font-size:19rpx}.orders-empty{padding:18rpx 0 4rpx;color:$ink-3;font-size:20rpx}.order-row{display:flex;justify-content:space-between;align-items:center;padding:16rpx 0;border-bottom:1rpx solid $hair}.order-row:last-child{border-bottom:0}.order-room,.order-date{display:block}.order-room{font-size:22rpx}.order-date{margin-top:5rpx;color:$ink-3;font-size:18rpx}.order-state{text-align:right;font-size:19rpx;color:$gold-deep}.order-state text{display:block}.state{margin-bottom:5rpx;padding:3rpx 10rpx;border-radius:12rpx;background:$gold-soft}.state.paid{background:#E2F0E4;color:#39704A}.state.closed{background:#EEE;color:#888}.state.pending{color:#9A6B25}.order-cancel{margin-top:7rpx;color:#A34B40;text-decoration:underline}.amount-line{display:flex;justify-content:space-between;margin-top:18rpx;color:$gold-deep;font-size:23rpx}.buy{margin-top:18rpx;background:$foil;color:#fff;border:0}.submit{margin-top:12rpx;background:$platinum-foil;color:$gold-deep;border:1rpx solid $hair}.buy::after{border:0}
.store-scroll{width:100%;margin-top:22rpx;white-space:nowrap}.store-track{display:flex;width:max-content;padding:2rpx 2rpx 12rpx;gap:16rpx}.store-card{position:relative;display:flex;width:360rpx;height:128rpx;box-sizing:border-box;padding:10rpx;background:#fff;border:2rpx solid $hair;border-radius:24rpx;box-shadow:0 8rpx 20rpx rgba(66,47,19,.06);overflow:hidden}.store-card.active{border-color:$gold-deep;box-shadow:0 10rpx 26rpx rgba(140,106,54,.2)}.store-thumb{width:120rpx;height:108rpx;flex:none;border-radius:17rpx;background:$ivory}.store-copy{display:flex;flex-direction:column;min-width:0;padding:8rpx 10rpx}.store-name{font-family:$font-cn-serif;font-size:24rpx;color:$ink}.store-address{max-width:190rpx;margin-top:5rpx;color:$ink-3;font-size:17rpx;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.store-count{margin-top:auto;color:$gold-deep;font-size:18rpx}.store-check{position:absolute;right:10rpx;top:9rpx;padding:3rpx 8rpx;border-radius:12rpx;background:$gold-deep;color:#fff;font-size:14rpx}.store-hero{position:relative;height:250rpx;margin-top:14rpx;border-radius:28rpx;overflow:hidden;background:#D7C09B}.store-hero>image{width:100%;height:100%}.store-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(24,18,10,.67),rgba(24,18,10,.08) 72%)}.store-hero-copy{position:absolute;left:24rpx;top:28rpx;color:#fff;text-shadow:0 2rpx 8rpx rgba(0,0,0,.3)}.store-hero-copy text{display:block}.store-kicker{font-size:16rpx;letter-spacing:2rpx;opacity:.88}.store-hero-name{margin:9rpx 0 5rpx;font-family:$font-cn-serif;font-size:34rpx}.store-hero-copy text:last-child{font-size:19rpx}.store-stats{position:absolute;left:22rpx;bottom:20rpx;display:flex;gap:12rpx}.store-stats text{padding:7rpx 13rpx;border:1rpx solid rgba(255,255,255,.4);border-radius:18rpx;background:rgba(255,255,255,.17);color:#fff;font-size:17rpx;backdrop-filter:blur(8px)}
.dot.facility{background:#A7C8B2}.facility-floor-card{background:linear-gradient(135deg,rgba(235,247,237,.72),rgba(166,198,175,.6))!important;border-color:rgba(83,123,94,.8)!important;box-shadow:0 12rpx 0 rgba(72,107,82,.75),0 22rpx 26rpx rgba(42,76,51,.15)!important}.facility-floor-card .floor-badge{background:#52765B}.facility-mini{position:absolute;inset:70rpx;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1rpx dashed rgba(71,113,82,.48);border-radius:24rpx;background:rgba(255,255,255,.28);color:#466750}.facility-mini text:first-child{font-family:$font-cn-serif;font-size:34rpx}.facility-mini text:last-child{margin-top:9rpx;font-size:18rpx}.facility-detail{position:relative;width:570rpx;height:500rpx;box-sizing:border-box;border:4rpx solid #6F9277;border-radius:34rpx;overflow:hidden;background:#E4F0E6;box-shadow:0 46rpx 45rpx -24rpx rgba(45,74,51,.48);animation:floorZoom .32s ease-out}.facility-detail>image{width:100%;height:100%}.facility-overlay{position:absolute;left:0;right:0;bottom:0;padding:24rpx;background:linear-gradient(transparent,rgba(24,54,32,.88));color:#fff}.facility-overlay text{display:block}.facility-title{font-family:$font-cn-serif;font-size:30rpx}.facility-desc{margin-top:5rpx;font-size:17rpx;opacity:.9}.facility-spaces{display:flex;flex-wrap:wrap;gap:8rpx;margin-top:12rpx}.facility-spaces text{padding:5rpx 10rpx;border-radius:14rpx;background:rgba(255,255,255,.18);font-size:15rpx}.room-seat.base{border-color:#BBA164}.room-seat.repair{border-color:#9FB29F}.room-seat.president{border-color:#9A7135;background:#FFF4D8}.room-seat.queen{border-color:#A98997;background:#FFF1F6}.room-features{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:14rpx}.room-features text{padding:7rpx 13rpx;border-radius:16rpx;background:#F1E7D5;color:$gold-deep;font-size:18rpx}.photo{background:#fff}
</style>
