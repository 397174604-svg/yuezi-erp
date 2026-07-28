<template>
  <!-- M-A F073 宝宝记录时间线：多胎切换 + kind 筛选 + 按日分组时间线（护士巡房录入，宝妈只读）。
       页面走原生滚动（非内嵌 scroll-view），pages.json 开 enablePullDownRefresh → 下拉重拉（顺带刷新 15 分钟签名照片 URL）。 -->
  <view class="screen">
    <view class="topbar"><text class="back" @tap="goBack">‹</text><text class="nm">宝宝成长日记</text><text class="tag">护士巡房记录</text></view>

    <!-- 宝宝切换（多胎才显示；单胎隐藏） -->
    <view class="btabs" v-if="babies.length > 1">
      <view v-for="(b, i) in babies" :key="b.baby_id" :class="['bt', i === babyIdx ? 'on' : '']" @tap="pickBaby(i)">{{ babyName(b, i) }}</view>
    </view>

    <!-- kind 筛选 chips（横向滚动） -->
    <scroll-view scroll-x class="chipscroll" :show-scrollbar="false">
      <view v-for="k in kinds" :key="k" :class="['chip', k === kind ? 'on' : '']" @tap="pickKind(k)">{{ k }}</view>
    </scroll-view>

    <view class="pad">
      <view v-if="loading" class="empty"><text class="et">加载中…</text></view>

      <block v-else-if="groups.length">
        <view class="grp" v-for="g in groups" :key="g.date">
          <view class="gdate"><text class="gd">{{ g.label }}</text><text class="gsub">{{ g.date }}</text></view>
          <view class="yz-card">
            <view class="row" v-for="it in g.items" :key="it.log_id">
              <view :class="['ic', it.cls]"><text>{{ it.icon }}</text></view>
              <view class="bd">
                <view class="l1"><text class="sum">{{ it.summary }}</text><text class="tm">{{ it.time }}</text></view>
                <text class="note" v-if="it.noteLine">{{ it.noteLine }}</text>
                <view class="phs" v-if="it.photos.length">
                  <image v-for="(p, pi) in it.photos" :key="p.mediaId" class="ph" :src="p.url" mode="aspectFill" @tap="preview(it, pi)" />
                </view>
              </view>
            </view>
          </view>
        </view>
      </block>

      <view v-else class="empty"><text class="em">☾</text><text class="et">宝宝的记录会在护士巡房后出现在这里</text></view>
    </view>
  </view>
</template>

<script>
import { loadBabies, loadBabyTimeline } from '@/common/remote.js'
import { dateTimeMs } from '@/common/logic.js'

// kind → [图标, 配色类]（配色为金白体系上的低饱和点缀）
const KIND_META = { '喂养': ['🍼', 'feed'], '尿便': ['💧', 'diaper'], '睡眠': ['🌙', 'sleep'], '哭闹': ['😢', 'cry'], '健康': ['🌡️', 'health'], '护理': ['🛁', 'care'] }

export default {
  data() {
    return {
      babies: [], babyIdx: 0,
      kinds: ['全部', '喂养', '尿便', '睡眠', '哭闹', '健康', '护理'],
      kind: '全部',
      rows: [], loading: true,
    }
  },
  async onLoad() { await this.init() },
  async onPullDownRefresh() { // 下拉重拉：宝宝列表 + 当前筛选的时间线（签名照片 URL 一并续期）
    try { await this.init() } finally { uni.stopPullDownRefresh() }
  },
  computed: {
    /** 按日期分组（服务端已按 log_time 倒序，组内保持倒序），并把每条日志加工成渲染要点 */
    groups() {
      const gs = []; const idx = {}
      for (const r of this.rows) {
        const d = (r.log_time || '').slice(0, 10)
        if (!(d in idx)) { idx[d] = gs.length; gs.push({ date: d, label: this.dlabel(d), items: [] }) }
        const meta = KIND_META[r.kind] || ['◦', 'feed']
        gs[idx[d]].items.push({
          log_id: r.log_id, icon: meta[0], cls: meta[1],
          summary: this.summarize(r),
          time: this.hm(r.log_time),
          noteLine: r.kind === '哭闹' ? '' : (r.note || ''), // 哭闹的备注已并入摘要，不重复展示
          photos: r.photos || [],
        })
      }
      return gs
    },
  },
  methods: {
    goBack() { uni.navigateBack() },
    babyName(b, i) { return b.name || ('宝宝' + (i + 1)) },
    async init() {
      this.loading = true
      this.babies = await loadBabies()
      if (this.babyIdx >= this.babies.length) this.babyIdx = 0
      await this.fetchTimeline()
    },
    async fetchTimeline() {
      const b = this.babies[this.babyIdx]
      if (!b) { this.rows = []; this.loading = false; return }
      this.loading = true
      this.rows = await loadBabyTimeline(b.baby_id, this.kind === '全部' ? '' : this.kind)
      this.loading = false
    },
    async pickBaby(i) { if (i === this.babyIdx) return; this.babyIdx = i; await this.fetchTimeline() },
    async pickKind(k) { if (k === this.kind) return; this.kind = k; await this.fetchTimeline() },
    /** 每条日志的要点摘要（按 kind 组装；字段缺失时退回 kind 名，不显示空洞） */
    summarize(r) {
      const k = r.kind
      if (k === '喂养') return [r.feed_type || '喂养', r.amount != null ? r.amount + 'ml' : ''].filter(Boolean).join(' ')
      if (k === '尿便') return [r.diaper_type || '尿便', r.amount_level ? '量' + r.amount_level : ''].filter(Boolean).join(' · ')
      if (k === '睡眠') {
        const s = this.hm(r.log_time)
        if (!r.end_time) return s + ' 入睡 · 还在睡 💤' // 开放睡眠段：下次巡房补醒来时间
        const d = this.dur(r.log_time, r.end_time)
        return s + '-' + this.hm(r.end_time) + (d ? ' 睡 ' + d : '')
      }
      if (k === '哭闹') return [r.duration_min != null ? r.duration_min + ' 分钟' : '哭闹', r.note || ''].filter(Boolean).join(' · ')
      if (k === '健康') return [r.metric || '健康', r.metric_value != null ? r.metric_value + (r.metric === '体温' ? '℃' : '') : ''].filter(Boolean).join(' ')
      if (k === '护理') return r.care_type || '护理'
      return k || '记录'
    },
    hm(t) { return (t || '').slice(11, 16) },
    /** 时长：<1h 显示分钟，≥1h 显示一位小数小时（如 2.5h） */
    dur(a, b) {
      const ms = dateTimeMs(b) - dateTimeMs(a)
      if (!(ms > 0)) return ''
      const m = Math.round(ms / 60000)
      return m < 60 ? m + ' 分钟' : (Math.round(m / 6) / 10) + 'h'
    },
    /** 日期组标题：M月D日（今天/昨天点缀） */
    dlabel(d) {
      const today = new Date().toISOString().slice(0, 10)
      const yest = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
      const mmdd = Number(d.slice(5, 7)) + '月' + Number(d.slice(8, 10)) + '日'
      return d === today ? mmdd + ' · 今天' : (d === yest ? mmdd + ' · 昨天' : mmdd)
    },
    preview(it, pi) {
      const urls = it.photos.map((p) => p.url)
      uni.previewImage({ urls, current: urls[pi] })
    },
  },
}
</script>

<style lang="scss" scoped>
.screen { min-height: 100vh; padding-bottom: 60rpx; }
.topbar { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; padding: 28rpx 40rpx 16rpx; background: $ivory; }
.back { font-size: 44rpx; color: $gold-deep; margin-right: 18rpx; line-height: 1; }
.nm { font-family: $font-cn-serif; font-size: 36rpx; font-weight: 600; }
.tag { margin-left: auto; font-size: 20rpx; color: $gold-deep; border: 1rpx solid $hair-s; border-radius: 20rpx; padding: 4rpx 14rpx; } /* 靠右，避开居中的演示浮标 */

.btabs { display: flex; gap: 16rpx; padding: 8rpx 40rpx 0; flex-wrap: wrap; }
.bt { font-size: 25rpx; color: $ink-2; background: $paper; border: 1rpx solid $hair; border-radius: 40rpx; padding: 12rpx 30rpx; }
.bt.on { background: $foil; color: #fff; border-color: transparent; font-weight: 600; }

.chipscroll { white-space: nowrap; padding: 20rpx 0 4rpx; }
.chip { display: inline-block; font-size: 23rpx; color: $gold-deep; border: 1rpx solid $hair-s; border-radius: 40rpx; padding: 10rpx 26rpx; background: $paper; margin-left: 16rpx; }
.chip:first-child { margin-left: 40rpx; }
.chip:last-child { margin-right: 40rpx; }
.chip.on { background: $foil; color: #fff; border-color: transparent; }

.pad { padding: 12rpx 40rpx 40rpx; }
.grp { margin-top: 28rpx; }
.gdate { display: flex; align-items: baseline; margin: 0 4rpx 18rpx; }
.gd { font-family: $font-cn-serif; font-size: 29rpx; font-weight: 600; padding-left: 20rpx; border-left: 6rpx solid $gold; }
.gsub { margin-left: 16rpx; font-family: $font-display; font-size: 21rpx; color: $ink-3; letter-spacing: 2rpx; }

.row { display: flex; padding: 24rpx 0; border-bottom: 1rpx solid $hair; }
.row:last-child { border-bottom: 0; padding-bottom: 4rpx; }
.row:first-child { padding-top: 4rpx; }
.ic { width: 64rpx; height: 64rpx; border-radius: 22rpx; display: flex; align-items: center; justify-content: center; font-size: 32rpx; margin-right: 22rpx; flex-shrink: 0; }
.ic.feed   { background: rgba(184, 148, 90, .14); }
.ic.diaper { background: rgba(110, 139, 106, .16); }
.ic.sleep  { background: rgba(84, 98, 133, .14); }
.ic.cry    { background: rgba(160, 69, 69, .12); }
.ic.health { background: rgba(196, 124, 60, .14); }
.ic.care   { background: rgba(139, 110, 160, .12); }
.bd { flex: 1; min-width: 0; }
.l1 { display: flex; align-items: baseline; }
.sum { flex: 1; font-size: 27rpx; font-weight: 500; }
.tm { font-family: $font-display; font-size: 24rpx; color: $gold-deep; margin-left: 16rpx; }
.note { display: block; font-size: 22rpx; color: $ink-3; margin-top: 8rpx; line-height: 1.6; }
.phs { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 14rpx; }
.ph { width: 132rpx; height: 132rpx; border-radius: 18rpx; border: 1rpx solid $hair; background: $ivory-2; }

.empty { text-align: center; padding: 140rpx 40rpx; }
.empty .em { display: block; font-size: 72rpx; color: $gold-soft; }
.empty .et { display: block; font-size: 25rpx; color: $ink-3; margin-top: 24rpx; line-height: 1.8; }

</style>
