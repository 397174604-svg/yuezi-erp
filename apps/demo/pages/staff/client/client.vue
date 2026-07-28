<template>
  <view class="screen" v-if="c">
    <view class="dhead"><text class="back" @tap="back">‹</text><text class="title">{{ c.name }} · 客户档案</text></view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="yz-card">
          <view class="mom"><view class="pic">{{ c.avatar }}</view>
            <view class="info"><text class="cn">{{ c.name }} <text class="ph">{{ c.phone }}</text></text>
              <view class="tags"><text v-for="t in c.tags" :key="t" :class="['yz-tag', t==='VIP'?'yz-tag--solid':'']">{{ t }}</text><text class="yz-tag dash">+ 标签</text></view></view>
            <text :class="['stage', c.stage==='在住'?'on':'']">{{ c.stage }}</text></view>
          <view class="subline" v-if="c.moon"><text class="moon">☾ 月子第 {{ c.moon.day }} / {{ c.moon.total }} 天</text><text>{{ c.room }} · {{ c.roomType }}</text></view>
        </view>

        <view class="sechead"><text class="l">基本信息</text><text class="more">编辑</text></view>
        <view class="yz-card">
          <view class="kv"><text class="k">性别 · 年龄</text><text class="v">{{ c.gender }} · {{ c.age }} 岁</text></view>
          <view class="kv"><text class="k">籍贯</text><text class="v">{{ c.native }}</text></view>
          <view class="kv"><text class="k">预产期 / 胎次</text><text class="v">{{ c.edc }} · {{ c.parity }}</text></view>
          <view class="kv"><text class="k">微信</text><text class="v">{{ c.wechat }}</text></view>
          <view class="kv last"><text class="k">身份证</text><text class="v">{{ c.idcard }}</text></view>
        </view>

        <view class="sechead"><text class="l">来源 / 销售意向</text></view>
        <view class="yz-card">
          <view class="kv"><text class="k">来源 / 渠道</text><text class="v">{{ c.source }} · {{ c.channel }}</text></view>
          <view class="kv"><text class="k">销售顾问</text><text class="v">{{ c.advisor }}</text></view>
          <view class="kv"><text class="k">意向等级</text><text class="v"><text class="yz-tag yz-tag--solid">{{ c.intentLevel }} 级</text></text></view>
          <view class="kv last"><text class="k">意向房型</text><text class="v">{{ c.intentRoom }}</text></view>
        </view>

        <view class="sechead"><text class="l">合同 / 卡额</text></view>
        <view class="yz-card">
          <view class="kv"><text class="k">套餐</text><text class="v">{{ c.pkg }}</text></view>
          <view class="kv last"><text class="k">余额</text><text class="v gold">¥ {{ c.balance.toLocaleString() }}</text></view>
        </view>

        <view class="sechead"><text class="l">跟进记录</text><text class="more">+ 新增</text></view>
        <view class="yz-card">
          <view class="tline" v-for="(f,i) in c.follow" :key="i"><text class="dot"></text>
            <view class="bd"><text class="t">{{ f.note }}</text><text class="s">{{ f.date }} · {{ f.type }} · {{ f.by }}</text></view></view>
        </view>
      </view>
    </scroll-view>
  </view>
  <!-- 兜底空态：客户不存在/越权/已转出（如失效深链）。绝不白屏。 -->
  <view class="screen" v-else-if="loaded">
    <view class="dhead"><text class="back" @tap="back">‹</text><text class="title">客户档案</text></view>
    <view class="notfound">
      <text class="nf-ic">⚇</text>
      <text class="nf-t">未找到该客户</text>
      <text class="nf-s">客户可能已转出本店或链接已失效，请回客户列表重新进入。</text>
      <text class="nf-btn" @tap="back">返回</text>
    </view>
  </view>
</template>
<script>
import { loadClient } from '@/common/staff/remote.js'
export default {
  data() { return { c: null, loaded: false } },
  async onLoad(q) {
    this.c = getApp().globalData.data.clients.find(x => x.id === q.id) || null
    const live = await loadClient(q.id)
    if (live) this.c = live
    this.loaded = true
  },
  methods: { back() { uni.navigateBack() } }
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.dhead { display: flex; align-items: center; padding: 28rpx 40rpx 12rpx; } .back { font-size: 48rpx; color: $gold-deep; width: 56rpx; } .title { font-family: $font-cn-serif; font-size: 32rpx; font-weight: 600; }
.notfound { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 80rpx; text-align: center; }
.nf-ic { font-size: 88rpx; color: $gold; } .nf-t { font-family: $font-cn-serif; font-size: 34rpx; font-weight: 600; margin-top: 24rpx; }
.nf-s { font-size: 24rpx; color: $ink-3; margin-top: 14rpx; line-height: 1.7; }
.nf-btn { margin-top: 40rpx; background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; border-radius: 60rpx; padding: 18rpx 72rpx; font-size: 27rpx; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 60rpx; }
.mom { display: flex; align-items: center; } .mom .pic { width: 92rpx; height: 92rpx; border-radius: 28rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; color: $gold-deep; font-size: 34rpx; }
.mom .info { flex: 1; margin-left: 22rpx; } .mom .cn { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; } .mom .cn .ph { font-size: 22rpx; color: $ink-3; font-weight: 400; margin-left: 10rpx; }
.mom .tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 14rpx; } .dash { border-style: dashed; }
.stage { font-size: 20rpx; padding: 8rpx 16rpx; border-radius: 12rpx; background: rgba(184,148,90,.14); color: $gold-deep; } .stage.on { background: rgba(110,139,106,.16); color: #577053; }
.subline { display: flex; justify-content: space-between; border-top: 1rpx solid $hair; margin-top: 22rpx; padding-top: 20rpx; font-size: 22rpx; color: $ink-2; }
.sechead { margin: 40rpx 4rpx 20rpx; display: flex; justify-content: space-between; align-items: baseline; } .sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; } .sechead .more { font-size: 22rpx; color: $gold-deep; }
.kv { display: flex; justify-content: space-between; padding: 20rpx 0; border-bottom: 1rpx solid $hair; font-size: 26rpx; } .kv.last { border-bottom: 0; } .kv .k { color: $ink-3; } .kv .v { color: $ink; font-weight: 500; } .kv .v.gold { font-family: $font-display; color: $gold-deep; font-size: 32rpx; }
.tline { display: flex; padding: 22rpx 0; border-bottom: 1rpx solid $hair; } .tline:last-child { border-bottom: 0; } .tline .dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: $gold; margin: 10rpx 22rpx 0 0; box-shadow: 0 0 0 6rpx rgba(184,148,90,.16); }
.tline .bd { flex: 1; } .tline .t { font-size: 26rpx; } .tline .s { display: block; font-size: 21rpx; color: $ink-3; margin-top: 6rpx; }
</style>
