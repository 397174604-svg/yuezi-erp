<template>
  <view class="screen">
    <view class="dhead">
      <text class="back" @tap="back">‹</text>
      <text class="title">{{ page.title || '' }}</text>
      <view class="acts" v-if="page.actions">
        <text class="act" v-for="a in page.actions" :key="a" @tap="onAction(a)">{{ a }}</text>
      </view>
    </view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view v-if="page.note" class="note">{{ page.note }}</view>

        <!-- cards -->
        <view v-if="page.type==='cards'" class="mgrid">
          <view class="mc" v-for="(m,i) in page.metrics" :key="i">
            <text class="v">{{ fmt(m[1]) }}</text><text class="l">{{ m[0] }}</text>
          </view>
        </view>

        <!-- board -->
        <block v-else-if="page.type==='board'">
          <view class="brow">
            <view class="bk" v-for="(b,i) in page.buckets" :key="i"><text class="n">{{ b[1] }}</text><text class="k">{{ b[0] }}</text></view>
          </view>
          <view class="yz-card">
            <view class="cline" v-for="(c,i) in page.cols" :key="i"><text class="dot"></text><text class="ct">{{ c }}</text></view>
          </view>
        </block>

        <!-- list（默认） -->
        <view v-else class="yz-card">
          <view class="lrow" v-for="(row,ri) in page.rows" :key="ri">
            <view class="linfo">
              <text class="ltitle">{{ row[0] }}</text>
              <text class="lmeta">
                <text v-for="(col,ci) in page.columns" :key="ci"><text v-if="ci>0 && !isStatus(col)">{{ col }} {{ fmt(row[ci]) }}　</text></text>
              </text>
            </view>
            <text v-if="statusIdx>=0" :class="['stage', live(row[statusIdx])?'on':'']">{{ row[statusIdx] }}</text>
            <text v-else-if="key==='forum'" class="like" @tap="onLike(row)">♥ {{ fmt(row[3]) }}</text>
          </view>
          <view v-if="!page.rows || !page.rows.length" class="empty">暂无数据</view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { PAGES } from '@/common/data.js'
import { loadPage, pageAction, likePost } from '@/common/remote.js'
// header 动作→真实写：键 'page:动作标签' → {act, ph 输入提示}
const HEADER_ACT = {
  'apptMom:预约': { act: 'book', ph: '预约项目（如 盆底修复）' },
  'expertQA:提问': { act: 'ask', ph: '请输入您的问题' },
  'forum:发帖': { act: 'post', ph: '说点什么…' },
}
export default {
  data() { return { page: {}, key: '', busy: false } },
  async onLoad(q) {
    this.key = q.key
    this.page = PAGES[q.key] || { title: '建设中', type: 'list', columns: [], rows: [] }
    const live = await loadPage(q.key)
    if (live) this.page = { ...this.page, ...live }
  },
  computed: {
    statusIdx() { return (this.page.columns || []).findIndex(c => /状态|是否/.test(c)) },
  },
  methods: {
    back() { uni.navigateBack() },
    toast(a) { uni.showToast({ title: a + '（示意）', icon: 'none' }) },
    async onAction(a) {
      const cfg = HEADER_ACT[this.key + ':' + a]
      if (!cfg) return this.toast(a) // 未接后端的动作仍示意
      if (this.busy) return
      const input = await new Promise(r => uni.showModal({ title: a, editable: true, placeholderText: cfg.ph, success: e => r(e.confirm ? e.content : null), fail: () => r(null) }))
      if (!input || !input.trim()) return
      this.busy = true
      const r = await pageAction(this.key, cfg.act, input.trim())
      this.busy = false
      if (r.ok) { uni.showToast({ title: a + '成功', icon: 'none' }); const live = await loadPage(this.key); if (live) this.page = { ...this.page, ...live } }
      else uni.showToast({ title: r.msg || (a + '失败'), icon: 'none' })
    },
    async onLike(row) {
      const pid = row[4]; if (pid == null || this.busy) return
      this.busy = true
      const r = await likePost(pid)
      this.busy = false
      if (r.ok) { uni.showToast({ title: '已赞', icon: 'none' }); const live = await loadPage(this.key); if (live) this.page = { ...this.page, ...live } }
      else uni.showToast({ title: r.msg || '点赞失败', icon: 'none' })
    },
    isStatus(c) { return /状态|是否/.test(c) },
    live(v) { return ['启用', '已支付', '已完成', '正常', '已到店', '审核通过', '在职'].includes(v) },
    fmt(v) { return (typeof v === 'number' && Math.abs(v) >= 1000) ? v.toLocaleString() : v }
  }
}
</script>

<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.dhead { display: flex; align-items: center; padding: 28rpx 40rpx 16rpx; }
.back { font-size: 48rpx; color: $gold-deep; width: 56rpx; }
.title { font-family: $font-cn-serif; font-size: 32rpx; font-weight: 600; }
.acts { margin-left: auto; display: flex; gap: 12rpx; }
.act { font-size: 22rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 12rpx 22rpx; border-radius: 40rpx; }
.scroll { flex: 1; }
.pad { padding: 8rpx 40rpx 60rpx; }
.note { font-size: 23rpx; color: $ink-2; background: rgba(231,212,172,.16); border: 1rpx solid $hair; border-radius: 20rpx; padding: 18rpx 24rpx; margin-bottom: 20rpx; }

.mgrid { display: flex; flex-wrap: wrap; gap: 20rpx; }
.mc { width: calc(33.33% - 14rpx); box-sizing: border-box; background: $paper; border: 1rpx solid $hair; border-radius: 28rpx; padding: 28rpx 16rpx; text-align: center; }
.mc .v { font-family: $font-display; font-size: 46rpx; color: $gold-deep; font-weight: 600; }
.mc .l { display: block; font-size: 21rpx; color: $ink-2; margin-top: 10rpx; }

.brow { display: flex; flex-wrap: wrap; gap: 16rpx; margin-bottom: 22rpx; }
.bk { flex: 1; min-width: 120rpx; background: $paper; border: 1rpx solid $hair; border-radius: 24rpx; padding: 22rpx 8rpx; text-align: center; }
.bk .n { font-family: $font-display; font-size: 40rpx; color: $gold-deep; font-weight: 600; }
.bk .k { display: block; font-size: 20rpx; color: $ink-2; margin-top: 6rpx; }
.cline { display: flex; padding: 20rpx 0; border-bottom: 1rpx solid $hair; }
.cline:last-child { border-bottom: 0; }
.cline .dot { width: 14rpx; height: 14rpx; border-radius: 50%; background: $gold; margin: 10rpx 18rpx 0 0; }
.cline .ct { flex: 1; font-size: 25rpx; }

.lrow { display: flex; align-items: center; padding: 24rpx 0; border-bottom: 1rpx solid $hair; }
.lrow:last-child { border-bottom: 0; }
.linfo { flex: 1; }
.ltitle { font-family: $font-cn-serif; font-size: 28rpx; font-weight: 600; }
.lmeta { display: block; font-size: 22rpx; color: $ink-3; margin-top: 8rpx; }
.stage { font-size: 20rpx; padding: 8rpx 16rpx; border-radius: 12rpx; background: rgba(184,148,90,.14); color: $gold-deep; }
.stage.on { background: rgba(110,139,106,.16); color: #577053; }
.like { font-size: 22rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 8rpx 20rpx; border-radius: 40rpx; white-space: nowrap; }
.like:active { opacity: .6; }
.empty { text-align: center; color: $ink-3; font-size: 24rpx; padding: 80rpx 0; }

</style>
