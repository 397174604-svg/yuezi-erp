<template>
  <view class="page">
    <view class="top"><text class="back" @tap="back">‹</text><text class="title">小程序二维码管理</text><text class="refresh" @tap="load">刷新</text></view>
    <scroll-view scroll-y class="scroll"><view class="pad">
      <view class="intro">创建后可直接生成微信小程序码。密钥只保存在后端，页面不会读取或展示。</view>

      <view class="create-card">
        <view class="section-title">新建业务入口</view>
        <view class="field"><text class="label">业务类型</text><picker :range="typeLabels" :value="typeIndex" @change="onType"><view class="picker">{{typeLabels[typeIndex]}} <text>⌄</text></view></picker></view>
        <view class="field"><text class="label">所属门店</text><picker :range="storeLabels" :value="storeIndex" @change="onStore"><view class="picker">{{storeLabels[storeIndex]||'请选择门店'}} <text>⌄</text></view></picker></view>
        <view v-if="form.sceneType==='room_service'" class="field"><text class="label">绑定房间</text><picker :range="roomLabels" :value="roomIndex" @change="onRoom"><view class="picker">{{roomLabels[roomIndex]||'请选择房间'}} <text>⌄</text></view></picker></view>
        <view class="field column"><text class="label">页面标题</text><input v-model="form.title" maxlength="80" placeholder="例如：一楼前台 · 到店服务" /></view>
        <button class="primary" :loading="creating" @tap="create">创建二维码入口</button>
      </view>

      <view class="toolbar">
        <view><text class="section-title">已创建入口</text><text class="count">{{rows.length}} 个</text></view>
        <picker :range="envLabels" :value="envIndex" @change="onEnv"><view class="env">生成版本：{{envLabels[envIndex]}}⌄</view></picker>
      </view>

      <view v-for="r in rows" :key="r.qr_code_id" class="qr-card">
        <view class="line"><view><text class="kind">{{r.title}}</text><text class="meta">{{typeName(r.scene_type)}} · {{r.store_name||'未绑定门店'}}<text v-if="r.room_no"> · 房间 {{r.room_no}}</text></text></view><text :class="['status',r.status==='启用'?'on':'off']">{{r.status}}</text></view>
        <text class="scene">场景码：{{r.scene_code}}</text>
        <image v-if="r.previewUrl" class="qr-image" :src="r.previewUrl" mode="aspectFit" @tap="preview(r)" />
        <view class="actions">
          <button size="mini" :loading="r.generating" :disabled="r.status!=='启用'" @tap="generate(r)">{{r.previewUrl?'重新生成':'生成并预览'}}</button>
          <button v-if="r.previewUrl" size="mini" @tap="save(r)">保存图片</button>
          <button size="mini" class="switch" @tap="toggle(r)">{{r.status==='启用'?'停用':'启用'}}</button>
        </view>
      </view>
      <view v-if="!rows.length&&!loading" class="empty">还没有二维码，请先在上方创建</view>
    </view></scroll-view>
  </view>
</template>

<script>
import { loadQrManagerData, createManagedQrCode, setManagedQrCodeStatus, generateManagedQrCode } from '@/common/remote.js'

const TYPES = [
  { value: 'front_desk', label: '前台到店服务' },
  { value: 'room_service', label: '房间入住服务' },
  { value: 'rehab', label: '产康预约' },
]
const ENVS = [
  { value: 'develop', label: '开发版' },
  { value: 'trial', label: '体验版' },
  { value: 'release', label: '正式版' },
]

export default {
  data(){return{loading:false,creating:false,rows:[],stores:[],rooms:[],typeIndex:0,storeIndex:0,roomIndex:0,envIndex:0,form:{sceneType:'front_desk',storeId:null,roomId:null,title:''}}},
  computed:{
    typeLabels(){return TYPES.map(x=>x.label)},envLabels(){return ENVS.map(x=>x.label)},
    storeLabels(){return this.stores.map(x=>x.name||('门店 '+x.store_id))},
    visibleRooms(){const sid=Number(this.form.storeId);return this.rooms.filter(x=>!sid||Number(x.store_id)===sid)},
    roomLabels(){return this.visibleRooms.map(x=>(x.room_no||('房间 '+x.room_id))+(x.room_type?' · '+x.room_type:''))},
  },
  onShow(){this.load()},onPullDownRefresh(){this.load().finally(()=>uni.stopPullDownRefresh())},
  methods:{
    back(){uni.navigateBack()},typeName(v){const x=TYPES.find(y=>y.value===v);return x?x.label:v},
    async load(){this.loading=true;try{const d=await loadQrManagerData();this.rows=(d.qrCodes||[]).map(x=>({...x,previewUrl:'',localPath:'',generating:false}));this.stores=d.stores||[];this.rooms=d.rooms||[];if(this.stores.length&&!this.form.storeId){this.storeIndex=0;this.form.storeId=Number(this.stores[0].store_id)}}catch(e){uni.showToast({title:e.message||'加载失败',icon:'none'})}finally{this.loading=false}},
    onType(e){this.typeIndex=Number(e.detail.value);this.form.sceneType=TYPES[this.typeIndex].value;this.form.roomId=null;this.roomIndex=0},
    onStore(e){this.storeIndex=Number(e.detail.value);this.form.storeId=Number(this.stores[this.storeIndex].store_id);this.form.roomId=null;this.roomIndex=0},
    onRoom(e){this.roomIndex=Number(e.detail.value);const r=this.visibleRooms[this.roomIndex];this.form.roomId=r?Number(r.room_id):null},
    onEnv(e){this.envIndex=Number(e.detail.value)},
    async create(){
      if(!this.form.storeId)return uni.showToast({title:'请选择门店',icon:'none'});
      if(this.form.sceneType==='room_service'&&!this.form.roomId)return uni.showToast({title:'请选择房间',icon:'none'});
      this.creating=true;try{await createManagedQrCode({...this.form});uni.showToast({title:'创建成功',icon:'success'});this.form.title='';await this.load()}catch(e){uni.showToast({title:e.message||'创建失败',icon:'none'})}finally{this.creating=false}
    },
    async toggle(r){const status=r.status==='启用'?'停用':'启用';try{await setManagedQrCodeStatus(r.qr_code_id,status);r.status=status;if(status==='停用'){r.previewUrl='';r.localPath=''}uni.showToast({title:'已'+status,icon:'success'})}catch(e){uni.showToast({title:e.message||'更新失败',icon:'none'})}},
    async generate(r){
      r.generating=true;try{const img=await generateManagedQrCode(r.qr_code_id,ENVS[this.envIndex].value);const dataUrl='data:'+img.mime+';base64,'+img.imageBase64;r.previewUrl=dataUrl;r.localPath='';
        // #ifdef MP-WEIXIN
        const ext=img.mime==='image/jpeg'?'.jpg':'.png';const path=wx.env.USER_DATA_PATH+'/qdfd-qr-'+r.qr_code_id+ext;await new Promise((resolve,reject)=>wx.getFileSystemManager().writeFile({filePath:path,data:img.imageBase64,encoding:'base64',success:resolve,fail:reject}));r.localPath=path;r.previewUrl=path;
        // #endif
        uni.showToast({title:'生成成功',icon:'success'})
      }catch(e){uni.showToast({title:e.message||'生成失败',icon:'none'})}finally{r.generating=false}
    },
    preview(r){uni.previewImage({urls:[r.localPath||r.previewUrl],current:r.localPath||r.previewUrl})},
    save(r){
      // #ifdef MP-WEIXIN
      if(!r.localPath)return;uni.saveImageToPhotosAlbum({filePath:r.localPath,success:()=>uni.showToast({title:'已保存到相册',icon:'success'}),fail:()=>uni.showToast({title:'请允许保存到相册',icon:'none'})})
      // #endif
      // #ifndef MP-WEIXIN
      this.preview(r);uni.showToast({title:'请长按图片保存',icon:'none'})
      // #endif
    },
  }
}
</script>

<style lang="scss" scoped>
.page{height:100vh;background:$ivory;display:flex;flex-direction:column}.top{padding:calc(env(safe-area-inset-top) + 20rpx) 34rpx 12rpx;display:flex;align-items:center;justify-content:space-between}.back{font-size:52rpx;color:$gold-deep;width:60rpx}.title{font-family:$font-cn-serif;font-size:31rpx}.refresh{width:60rpx;text-align:right;color:$gold-deep;font-size:22rpx}.scroll{flex:1}.pad{padding:20rpx 30rpx 90rpx}.intro{font-size:22rpx;line-height:1.7;color:$ink-2;background:#F2E5CC;border-radius:22rpx;padding:20rpx 24rpx}.create-card,.qr-card{background:#fff;border:1rpx solid $hair;border-radius:28rpx;padding:28rpx;margin-top:20rpx}.section-title{font-family:$font-cn-serif;font-size:29rpx;font-weight:600}.field{display:flex;align-items:center;justify-content:space-between;border-bottom:1rpx solid $hair;padding:22rpx 0}.field.column{display:block}.label{font-size:23rpx;color:$ink-2}.picker{font-size:24rpx;color:$gold-deep;text-align:right}.field input{margin-top:14rpx;background:$ivory;border-radius:16rpx;padding:18rpx 20rpx;font-size:24rpx}.primary{margin-top:26rpx;background:$gold-deep;color:#fff;border-radius:50rpx;font-size:25rpx}.primary::after,.actions button::after{border:0}.toolbar{display:flex;align-items:center;justify-content:space-between;margin:42rpx 4rpx 8rpx}.count{font-size:20rpx;color:$ink-3;margin-left:12rpx}.env{font-size:21rpx;color:$gold-deep;background:#F2E5CC;padding:10rpx 16rpx;border-radius:24rpx}.line{display:flex;justify-content:space-between;gap:16rpx}.line>view{flex:1}.kind,.meta,.scene{display:block}.kind{font-family:$font-cn-serif;font-size:28rpx}.meta{font-size:21rpx;color:$ink-3;margin-top:7rpx}.status{font-size:20rpx;padding:7rpx 15rpx;border-radius:25rpx;height:fit-content}.status.on{background:#E8F3EA;color:#46734C}.status.off{background:#EEEAE3;color:$ink-3}.scene{font-size:19rpx;color:$ink-3;margin-top:18rpx;word-break:break-all}.qr-image{display:block;width:380rpx;height:380rpx;margin:24rpx auto 10rpx;background:#fff}.actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:12rpx;margin-top:22rpx}.actions button{margin:0;background:#F2E5CC;color:$gold-deep;border:0}.actions .switch{background:#EEEAE3;color:$ink-2}.empty{text-align:center;color:$ink-3;padding:120rpx 20rpx}
</style>
