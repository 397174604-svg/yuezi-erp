<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">楼层与选房配置</text><text class="add" @tap="openBatch">新增楼层</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view v-if="stores.length>1" class="store-line"><text>配置门店</text><picker :range="storeNames" :value="storeIndex" @change="onStore"><text>{{storeNames[storeIndex]}} ›</text></picker></view>
        <view class="notice">楼层数由已配置楼层自动生成；每个房间可单独设置朝向、排序、房型、价格、客户可见性和照片。</view>
        <view class="legend"><text>北 ↑</text><text>西 ← 中央走廊 → 东</text><text>南 ↓</text></view>
        <view v-if="!loading&&floors.length" class="preview-card">
          <view class="preview-head">
            <view><text class="preview-title">{{storeNames[storeIndex]}} · {{previewFloor?previewFloor.floor+'F 单层':'3D 楼体'}}</text><text class="preview-sub">{{previewFloor?'点击房间直接编辑配置':'点击露出的楼层进入单层查看'}}</text></view>
            <view class="preview-actions"><button @tap="resetPreview">还原</button><button v-if="previewFloor" @tap="exitPreviewFloor">返回整栋</button></view>
          </view>
          <view class="preview-controls"><button @tap="turnPreview(-45)">↶</button><view><text>方向 {{previewYawLabel}}</text><text>{{Math.round(previewYaw)}}° · 俯视 {{Math.round(previewPitch)}}°</text></view><button @tap="turnPreview(45)">↷</button></view>
          <view class="preview-stage" @touchstart="previewTouchStart" @touchmove.stop.prevent="previewTouchMove" @touchend="previewTouchEnd">
            <view v-if="!previewFloor" class="preview-scene preview-stack" :style="previewTransform">
              <view v-for="(floor,index) in floors" :key="floor.floor" class="preview-floor" :style="previewFloorStyle(index)" @tap="openPreviewFloor(floor)">
                <view class="preview-badge"><text>{{floor.floor}}F</text><text>{{visibleCount(floor.rooms)}} 可见</text></view>
                <view class="preview-rooms"><view v-for="room in floor.rooms.slice(0,24)" :key="room.room_id" :class="Number(room.customer_visible)!==0?'shown':'hidden-room'"></view></view>
              </view>
              <text class="preview-south">南</text>
            </view>
            <view v-else class="preview-scene preview-detail" :style="previewTransform">
              <view class="detail-floor">
                <text class="detail-dir d-n">北</text><text class="detail-dir d-e">东</text><text class="detail-dir d-s">南</text><text class="detail-dir d-w">西</text>
                <view class="detail-row detail-north"><view v-for="room in previewRoomsAt('北')" :key="room.room_id" :class="previewRoomClass(room)" @tap.stop="openPreviewRoom(room)"><text>{{room.room_no}}</text><text>{{shortPreviewType(room.room_type)}}</text></view></view>
                <view class="detail-middle">
                  <view class="detail-side"><view v-for="room in previewRoomsAt('西')" :key="room.room_id" :class="previewRoomClass(room)" @tap.stop="openPreviewRoom(room)"><text>{{room.room_no}}</text><text>{{shortPreviewType(room.room_type)}}</text></view></view>
                  <view class="detail-corridor"><text>中央走廊</text><view>电梯</view></view>
                  <view class="detail-side"><view v-for="room in previewRoomsAt('东')" :key="room.room_id" :class="previewRoomClass(room)" @tap.stop="openPreviewRoom(room)"><text>{{room.room_no}}</text><text>{{shortPreviewType(room.room_type)}}</text></view></view>
                </view>
                <view class="detail-row detail-south"><view v-for="room in previewRoomsAt('南')" :key="room.room_id" :class="previewRoomClass(room)" @tap.stop="openPreviewRoom(room)"><text>{{room.room_no}}</text><text>{{shortPreviewType(room.room_type)}}</text></view></view>
              </view>
            </view>
          </view>
          <text class="preview-tip">左右拖动可 360° 旋转 · 上下拖动调整俯视角</text>
        </view>
        <view v-if="loading" class="empty">正在加载房间配置…</view>
        <view v-for="floor in floors" :key="floor.floor" class="floor-card">
          <view class="floor-head"><view><text class="floor-name">{{floor.floor}}F</text><text class="floor-count">{{floor.rooms.length}} 间 · 客户可见 {{visibleCount(floor.rooms)}} 间</text></view><button @tap="openCreate(floor.floor)">添加房间</button></view>
          <view class="direction" v-for="direction in directions" :key="direction">
            <text class="direction-name">{{direction}}向</text>
            <scroll-view scroll-x class="room-scroll"><view class="room-row">
              <view v-for="room in roomsAt(floor.rooms,direction)" :key="room.room_id" :class="['room',room.customer_visible?'':'hidden']" @tap="openEdit(room)">
                <image v-if="imageOf(room.room_id)" :src="imageOf(room.room_id)" mode="aspectFill" />
                <view v-else class="room-img">{{room.room_no}}</view>
                <text class="room-no">{{room.room_no}}</text><text class="room-type">{{room.room_type||'标准房'}}</text>
                <text class="room-meta">序 {{room.layout_order||0}} · {{room.status}}</text>
              </view>
              <text v-if="!roomsAt(floor.rooms,direction).length" class="direction-empty">暂无房间</text>
            </view></scroll-view>
          </view>
        </view>
        <view v-if="!loading&&!floors.length" class="empty">暂无楼层，点击右上角“新增楼层”开始配置</view>
      </view>
    </scroll-view>

    <view v-if="dialog" class="mask" @tap.self="closeDialog">
      <scroll-view scroll-y class="sheet">
        <text class="sheet-title">{{dialog==='batch'?'批量新增楼层房间':form.roomId?'编辑房间':'新增房间'}}</text>
        <view class="field"><text>楼层</text><input v-model.number="form.floor" type="number" /></view>
        <view v-if="dialog==='batch'" class="field"><text>房间数量</text><input v-model.number="form.count" type="number" /></view>
        <view v-if="dialog==='batch'" class="field"><text>起始序号</text><input v-model.number="form.start" type="number" placeholder="如 1，将生成 301" /></view>
        <view v-else class="field"><text>房间号</text><input v-model.trim="form.roomNo" maxlength="20" /></view>
        <view class="field"><text>朝向</text><picker :range="directions" :value="directionIndex" @change="form.direction=directions[Number($event.detail.value)]"><text>{{form.direction}} ›</text></picker></view>
        <view v-if="dialog!=='batch'" class="field"><text>楼层内顺序</text><input v-model.number="form.layoutOrder" type="number" /></view>
        <view class="field"><text>房型</text><input v-model.trim="form.roomType" maxlength="30" placeholder="如 尊享套房" /></view>
        <view class="field"><text>日房价</text><input v-model.number="form.price" type="digit" /></view>
        <view v-if="dialog!=='batch'" class="field"><text>房态</text><picker :range="statuses" :value="statusIndex" @change="form.status=statuses[Number($event.detail.value)]"><text>{{form.status}} ›</text></picker></view>
        <view v-if="dialog!=='batch'" class="field"><text>在 MOM 端展示</text><switch :checked="form.customerVisible" color="#8C6A36" @change="form.customerVisible=$event.detail.value" /></view>
        <view v-if="form.roomId" class="photo-block">
          <image v-if="imageOf(form.roomId)" :src="imageOf(form.roomId)" mode="aspectFill" />
          <button :loading="uploading" @tap="choosePhoto">{{imageOf(form.roomId)?'更换房间照片':'上传房间照片'}}</button>
        </view>
        <button class="save" :loading="saving" @tap="save">{{dialog==='batch'?'生成房间':'保存配置'}}</button>
        <button v-if="form.roomId" class="remove" @tap="removeCurrent">删除房间</button>
        <button class="cancel" @tap="closeDialog">取消</button>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import { makeApi, REMOTE } from '@/common/remote.js'
const DIRECTIONS=['北','东','南','西'], STATUSES=['空闲','已订','在住','清洁','停用']
const blank=()=>({roomId:0,floor:3,count:8,start:1,roomNo:'',direction:'南',layoutOrder:1,roomType:'大床房',price:1680,status:'空闲',customerVisible:true})
export default{
  data(){return{loading:false,saving:false,uploading:false,dialog:'',rooms:[],media:[],stores:[],storeIndex:0,previewFloor:null,previewYaw:0,previewPitch:58,previewMoved:false,previewDrag:{x:0,y:0,yaw:0,pitch:58},form:blank(),directions:DIRECTIONS,statuses:STATUSES}},
  computed:{
    storeNames(){return this.stores.map(s=>s.name)},
    selectedStoreId(){const s=this.stores[this.storeIndex];return s?Number(s.store_id):(REMOTE.storeId||null)},
    floors(){const map={};for(const r of this.rooms)(map[r.floor||0]=map[r.floor||0]||[]).push(r);return Object.keys(map).map(Number).sort((a,b)=>b-a).map(floor=>({floor,rooms:map[floor]}))},
    directionIndex(){const i=DIRECTIONS.indexOf(this.form.direction);return i<0?2:i},
    statusIndex(){const i=STATUSES.indexOf(this.form.status);return i<0?0:i},
    previewTransform(){const scale=this.previewFloor ? 0.92 : 0.72;return`transform:perspective(1100rpx) rotateX(${this.previewPitch}deg) rotateZ(${this.previewYaw}deg) scale(${scale})`},
    previewYawLabel(){const a=((this.previewYaw%360)+360)%360;return a<45||a>=315?'北':a<135?'东':a<225?'南':'西'},
  },
  onShow(){this.load()},onPullDownRefresh(){this.load().finally(()=>uni.stopPullDownRefresh())},
  onBackPress(){if(this.dialog){this.dialog='';return true}if(this.previewFloor){this.exitPreviewFloor();return true}return false},
  methods:{
    back(){uni.navigateBack()},visibleCount(rows){return rows.filter(r=>Number(r.customer_visible)!==0).length},
    previewFloorStyle(index){const z=(this.floors.length-index)*48,y=index*38;return`transform:translate3d(0,${y}rpx,${z}rpx);z-index:${this.floors.length-index}`},
    turnPreview(step){this.previewYaw=(this.previewYaw+step+360)%360},resetPreview(){this.previewYaw=0;this.previewPitch=58},
    openPreviewFloor(floor){if(this.previewMoved)return;this.previewFloor=floor},exitPreviewFloor(){this.previewFloor=null},
    previewRoomsAt(direction){return this.roomsAt((this.previewFloor&&this.previewFloor.rooms)||[],direction)},
    previewRoomClass(room){return['detail-room',Number(room.customer_visible)!==0?'shown':'hidden-room',room.status==='停用'?'stopped':'']},
    shortPreviewType(type){const value=String(type||'标准房');return value.length>5?value.slice(0,5):value},
    openPreviewRoom(room){if(!this.previewMoved)this.openEdit(room)},
    previewTouchStart(e){const t=e.changedTouches[0];this.previewDrag={x:t.clientX,y:t.clientY,yaw:this.previewYaw,pitch:this.previewPitch};this.previewMoved=false},
    previewTouchMove(e){const t=e.changedTouches[0],dx=t.clientX-this.previewDrag.x,dy=t.clientY-this.previewDrag.y;if(Math.abs(dx)>4||Math.abs(dy)>4)this.previewMoved=true;this.previewYaw=((this.previewDrag.yaw+dx*1.05)%360+360)%360;this.previewPitch=Math.max(25,Math.min(76,this.previewDrag.pitch-dy*.28))},
    previewTouchEnd(){setTimeout(()=>{this.previewMoved=false},80)},
    roomsAt(rows,d){return rows.filter(r=>(r.direction||'南')===d).sort((a,b)=>Number(a.layout_order||0)-Number(b.layout_order||0)||String(a.room_no).localeCompare(String(b.room_no)))},
    imageOf(roomId){const m=this.media.find(x=>Number(x.ref_id)===Number(roomId));return m?(String(m.url).startsWith('http')?m.url:REMOTE.baseUrl+m.url):''},
    async load(){this.loading=true;try{const activeFloor=this.previewFloor&&this.previewFloor.floor,api=makeApi();if(!this.stores.length){this.stores=await api.listStores()||[];const own=this.stores.findIndex(s=>Number(s.store_id)===Number(REMOTE.storeId));this.storeIndex=own>=0?own:0}const [rooms,media]=await Promise.all([api.listRooms({storeId:this.selectedStoreId||undefined}),api.mediaList({refType:'room'})]);this.rooms=rooms||[];this.media=media||[];this.previewFloor=activeFloor?(this.floors.find(f=>Number(f.floor)===Number(activeFloor))||null):null}catch(e){uni.showToast({title:e.message||'加载失败',icon:'none'})}finally{this.loading=false}},
    onStore(e){this.storeIndex=Number(e.detail.value);this.previewFloor=null;this.resetPreview();this.load()},
    openBatch(){this.form=blank();this.dialog='batch'},
    openCreate(floor){this.form={...blank(),floor,layoutOrder:(this.rooms.filter(r=>Number(r.floor)===Number(floor)).length+1)};this.dialog='room'},
    openEdit(r){this.form={roomId:Number(r.room_id),floor:Number(r.floor||1),roomNo:r.room_no||'',direction:r.direction||'南',layoutOrder:Number(r.layout_order||0),roomType:r.room_type||'',price:Number(r.price||0),status:r.status||'空闲',customerVisible:Number(r.customer_visible)!==0};this.dialog='room'},
    closeDialog(){if(!this.saving&&!this.uploading)this.dialog=''},
    async save(){if(this.saving)return;if(!this.selectedStoreId)return uni.showToast({title:'请选择门店',icon:'none'});if(!Number.isInteger(Number(this.form.floor))||Number(this.form.floor)<1)return uni.showToast({title:'请输入正确楼层',icon:'none'});this.saving=true;try{const api=makeApi();if(this.dialog==='batch'){const count=Math.min(Math.max(Number(this.form.count)||0,1),50),start=Math.max(Number(this.form.start)||1,1);for(let i=0;i<count;i++){const seq=start+i;await api.createRoom({storeId:this.selectedStoreId,roomNo:String(this.form.floor)+String(seq).padStart(2,'0'),floor:Number(this.form.floor),direction:this.form.direction,layoutOrder:i+1,roomType:this.form.roomType,price:Number(this.form.price||0),status:'空闲',customerVisible:true})}}else{if(!this.form.roomNo)return uni.showToast({title:'房间号必填',icon:'none'});const input={storeId:this.selectedStoreId,roomNo:this.form.roomNo,floor:Number(this.form.floor),direction:this.form.direction,layoutOrder:Number(this.form.layoutOrder||0),roomType:this.form.roomType,price:Number(this.form.price||0),status:this.form.status,customerVisible:this.form.customerVisible};if(this.form.roomId)await api.updateRoom(this.form.roomId,input);else{const made=await api.createRoom(input);this.form.roomId=Number(made.roomId)}}uni.showToast({title:'配置已保存',icon:'success'});this.dialog='';await this.load()}catch(e){uni.showToast({title:e.message||'保存失败',icon:'none'})}finally{this.saving=false}},
    choosePhoto(){if(!this.form.roomId)return;uni.chooseImage({count:1,sizeType:['compressed'],success:async r=>{this.uploading=true;try{const path=r.tempFilePaths[0];const base64=await new Promise((resolve,reject)=>uni.getFileSystemManager().readFile({filePath:path,encoding:'base64',success:x=>resolve(x.data),fail:reject}));const mime=/\.png$/i.test(path)?'image/png':/\.webp$/i.test(path)?'image/webp':'image/jpeg';const api=makeApi(),old=this.media.find(x=>Number(x.ref_id)===Number(this.form.roomId));await api.uploadMedia({refType:'room',refId:this.form.roomId,tag:this.form.roomType,mime,dataBase64:base64,alt:this.form.roomNo+' '+this.form.roomType,visibility:'public'});if(old)await api.removeMedia(old.media_id);uni.showToast({title:'照片已上传',icon:'success'});await this.load()}catch(e){uni.showToast({title:e.message||'上传失败',icon:'none'})}finally{this.uploading=false}}})},
    async removeCurrent(){const ok=await new Promise(resolve=>uni.showModal({title:'删除房间',content:'确认删除 '+this.form.roomNo+'？已有预订的房间不建议删除。',success:r=>resolve(r.confirm),fail:()=>resolve(false)}));if(!ok)return;try{await makeApi().removeRoom(this.form.roomId);this.dialog='';await this.load()}catch(e){uni.showToast({title:e.message||'删除失败',icon:'none'})}},
  }
}
</script>

<style lang="scss" scoped>
.page{height:100vh;background:$ivory;display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 32rpx 14rpx;display:flex;align-items:center;justify-content:space-between}.back{width:90rpx;font-size:52rpx;color:$gold-deep}.title{font-family:$font-cn-serif;font-size:30rpx}.add{width:120rpx;text-align:right;color:$gold-deep;font-size:22rpx}.scroll{flex:1}.pad{padding:18rpx 28rpx 100rpx}.store-line,.notice,.legend{background:#fff;border:1rpx solid $hair;border-radius:24rpx;padding:22rpx 24rpx;margin-bottom:18rpx}.store-line{display:flex;justify-content:space-between}.notice{color:$ink-2;font-size:21rpx;line-height:1.7}.legend{display:flex;justify-content:space-between;color:$gold-deep;font-size:20rpx}.floor-card{background:#fff;border:1rpx solid $hair;border-radius:30rpx;padding:26rpx;margin-bottom:24rpx}.floor-head{display:flex;align-items:center;justify-content:space-between}.floor-name{font-family:$font-display;font-size:40rpx;color:$gold-deep}.floor-count{display:block;color:$ink-3;font-size:20rpx}.floor-head button{margin:0;background:$gold-deep;color:#fff;border:0;border-radius:40rpx;font-size:20rpx}.direction{margin-top:22rpx}.direction-name{font-size:21rpx;color:$ink-2}.room-scroll{width:100%;white-space:nowrap;margin-top:10rpx}.room-row{display:flex;gap:14rpx}.room{width:174rpx;flex:none;border:1rpx solid $hair;border-radius:20rpx;padding:12rpx;box-sizing:border-box;background:$ivory}.room.hidden{opacity:.45}.room image,.room-img{width:150rpx;height:90rpx;border-radius:14rpx;background:#E9D9BD;display:flex;align-items:center;justify-content:center;color:$gold-deep}.room-no,.room-type,.room-meta{display:block}.room-no{font-family:$font-display;font-size:28rpx;margin-top:8rpx}.room-type{font-size:20rpx;color:$ink-2}.room-meta{font-size:18rpx;color:$ink-3}.direction-empty{padding:20rpx;color:$ink-3;font-size:20rpx}.empty{text-align:center;padding:100rpx 20rpx;color:$ink-3}.mask{position:fixed;inset:0;background:rgba(26,21,15,.55);z-index:50;display:flex;align-items:flex-end}.sheet{max-height:86vh;width:100%;box-sizing:border-box;background:#fff;border-radius:38rpx 38rpx 0 0;padding:38rpx 36rpx calc(env(safe-area-inset-bottom) + 30rpx)}.sheet-title{display:block;font-family:$font-cn-serif;font-size:32rpx;margin-bottom:20rpx}.field{display:flex;align-items:center;justify-content:space-between;border-bottom:1rpx solid $hair;padding:20rpx 0;font-size:23rpx}.field input{text-align:right;width:360rpx}.photo-block{margin-top:24rpx}.photo-block image{width:100%;height:260rpx;border-radius:22rpx}.photo-block button{margin-top:12rpx;background:$ivory;color:$gold-deep;border:1rpx solid $hair}.save{margin-top:28rpx;background:$gold-deep;color:#fff;border:0}.remove{background:#FFF1EE;color:#A04545;border:0}.cancel{background:transparent;color:$ink-3;border:0}.save::after,.remove::after,.cancel::after{border:0}.preview-card{background:linear-gradient(150deg,#fff,#EFE1C8);border:1rpx solid $hair;border-radius:30rpx;padding:24rpx;margin-bottom:24rpx;overflow:hidden}.preview-head{display:flex;align-items:flex-start;justify-content:space-between}.preview-title{display:block;font-family:$font-cn-serif;font-size:27rpx;color:$gold-deep}.preview-sub{display:block;margin-top:4rpx;color:$ink-3;font-size:18rpx}.preview-actions{display:flex;gap:6rpx}.preview-head button{margin:0;padding:0 14rpx;height:52rpx;line-height:52rpx;border:0;border-radius:26rpx;background:$gold-deep;color:#fff;font-size:17rpx}.preview-head button::after,.preview-controls button::after{border:0}.preview-controls{width:360rpx;margin:14rpx auto 0;padding:7rpx;display:flex;align-items:center;justify-content:space-between;border-radius:24rpx;background:rgba(255,255,255,.72);color:$gold-deep;font-size:18rpx}.preview-controls>view{text-align:center}.preview-controls text{display:block}.preview-controls text:last-child{font-size:14rpx;color:$ink-3}.preview-controls button{margin:0;padding:0;width:54rpx;height:48rpx;line-height:48rpx;border:1rpx solid $hair;border-radius:50%;background:#fff;color:$gold-deep}.preview-stage{height:560rpx;display:flex;align-items:center;justify-content:center}.preview-scene{position:relative;width:500rpx;height:360rpx;transform-style:preserve-3d}.preview-floor{position:absolute;inset:0;border:3rpx solid rgba(140,106,54,.75);border-radius:22rpx;background:linear-gradient(135deg,rgba(255,253,247,.65),rgba(210,184,138,.5));box-shadow:0 10rpx 0 rgba(117,84,41,.75);transform-style:preserve-3d}.preview-badge{position:absolute;left:-12rpx;bottom:6rpx;z-index:10;padding:5rpx 10rpx;border-radius:9rpx;background:$gold-deep;color:#fff}.preview-badge text{display:block;font-size:14rpx}.preview-badge text:first-child{font-family:$font-display;font-size:21rpx}.preview-rooms{position:absolute;inset:35rpx;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;gap:8rpx}.preview-rooms view{width:34rpx;height:24rpx;border:1rpx solid #A68B60;border-radius:5rpx;background:#E5F0E2;box-shadow:0 4rpx 0 #9C8055}.preview-rooms .hidden-room{opacity:.3;background:#C9C3B8}.preview-south{position:absolute;left:50%;bottom:-42rpx;z-index:99;width:38rpx;height:38rpx;line-height:38rpx;text-align:center;border-radius:50%;background:$gold-deep;color:#fff;font-size:15rpx;transform:translate3d(-50%,0,500rpx)}.preview-tip{display:block;text-align:center;color:$ink-3;font-size:17rpx}.detail-floor{position:relative;width:500rpx;height:360rpx;box-sizing:border-box;padding:20rpx;border:4rpx solid #97703A;border-radius:28rpx;background:linear-gradient(135deg,#F8F0E1,#D7C09B);box-shadow:0 26rpx 0 #806033,0 38rpx 36rpx rgba(64,42,15,.3);transform-style:preserve-3d}.detail-row{height:68rpx;display:flex;align-items:center;justify-content:center;gap:5rpx}.detail-south{position:absolute;left:20rpx;right:20rpx;bottom:15rpx}.detail-middle{height:190rpx;display:flex;justify-content:space-between}.detail-side{width:138rpx;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;gap:5rpx}.detail-corridor{flex:1;margin:10rpx;border:1rpx dashed rgba(140,106,54,.4);background:rgba(255,255,255,.3);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#957747;font-size:15rpx}.detail-corridor view{margin-top:12rpx;padding:4rpx 9rpx;border-radius:6rpx;background:$gold-deep;color:#fff}.detail-room{width:48rpx;height:50rpx;flex:none;box-sizing:border-box;border:1rpx solid #AC9168;border-radius:8rpx;background:#E7F1E5;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 7rpx 0 #947649;transform:translateZ(16rpx)}.detail-side .detail-room{width:62rpx;height:34rpx}.detail-room text{display:block;color:$gold-deep;font-family:$font-display;font-size:15rpx;line-height:1}.detail-room text:last-child{margin-top:3rpx;font-family:$font-sans;font-size:10rpx}.detail-room.hidden-room{opacity:.4}.detail-room.stopped{background:#CBC5BB}.detail-dir{position:absolute;z-index:20;width:34rpx;height:34rpx;line-height:34rpx;text-align:center;border-radius:50%;background:$gold-deep;color:#fff;font-size:14rpx}.d-n{top:-17rpx;left:50%;margin-left:-17rpx}.d-s{bottom:-17rpx;left:50%;margin-left:-17rpx}.d-w{left:-17rpx;top:50%;margin-top:-17rpx}.d-e{right:-17rpx;top:50%;margin-top:-17rpx}
.detail-row{gap:4rpx}.detail-row .detail-room{width:45rpx}
</style>
