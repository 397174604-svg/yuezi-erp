<template>
  <!-- M-A F074 我的产后记录：护理师每次巡房评估成一条，按日期倒序卡片展示（宝妈只读）。
       页面走原生滚动，pages.json 开 enablePullDownRefresh → 下拉重拉（顺带刷新 15 分钟签名照片 URL）。 -->
  <view class="screen">
    <view class="topbar"><text class="back" @tap="goBack">‹</text><text class="nm">我的产后记录</text><text class="tag">护理评估</text></view>

    <view class="pad">
      <view v-if="loading" class="empty"><text class="et">加载中…</text></view>

      <block v-else-if="cards.length">
        <view class="yz-card ac" v-for="c in cards" :key="c.assess_id">
          <view class="ahead">
            <text class="day" v-if="c.dayN != null">产后第 <text class="n">{{ c.dayN }}</text> 天</text>
            <text class="day" v-else>产后评估</text>
            <text class="ad">{{ c.date }}</text>
          </view>

          <!-- 体征行：体温 / 血压 / 脉搏（缺项显示 —） -->
          <view class="vitals">
            <view class="vi"><text class="vv">{{ c.temperature != null ? c.temperature + '℃' : '—' }}</text><text class="vl">体温</text></view>
            <view class="vi"><text class="vv">{{ c.blood_pressure || '—' }}</text><text class="vl">血压</text></view>
            <view class="vi"><text class="vv">{{ c.pulse != null ? c.pulse + ' 次/分' : '—' }}</text><text class="vl">脉搏</text></view>
          </view>

          <!-- 恢复 chips：恶露色/量/宫底/会阴/乳房/情绪（值即文案，空项不显示） -->
          <view class="tags" v-if="c.chips.length"><text class="tg" v-for="t in c.chips" :key="t">{{ t }}</text></view>

          <text class="note" v-if="c.notes">{{ c.notes }}</text>

          <view class="phs" v-if="c.photos.length">
            <image v-for="(p, pi) in c.photos" :key="p.mediaId" class="ph" :src="p.url" mode="aspectFill" @tap="preview(c, pi)" />
          </view>
        </view>
      </block>

      <view v-else class="empty"><text class="em">☾</text><text class="et">护理师完成产后评估后，您的恢复记录会出现在这里</text></view>
    </view>
  </view>
</template>

<script>
import { loadMyCare } from '@/common/remote.js'

export default {
  data() { return { rows: [], loading: true } },
  async onLoad() { await this.fetch() },
  async onPullDownRefresh() { // 下拉重拉（签名照片 URL 一并续期）
    try { await this.fetch() } finally { uni.stopPullDownRefresh() }
  },
  computed: {
    /** 评估行 → 卡片渲染要点（remote 已反转为日期倒序） */
    cards() {
      return this.rows.map((r) => ({
        assess_id: r.assess_id,
        dayN: r.postpartum_day != null ? r.postpartum_day : null,
        date: (r.assess_date || '').slice(0, 10),
        temperature: r.temperature, blood_pressure: r.blood_pressure, pulse: r.pulse,
        // 恶露色/量/会阴/情绪的枚举值自带语义；宫底、乳房的值单看易歧义，补两字前缀
        chips: [r.lochia_color, r.lochia_amount, r.fundus ? '宫底 ' + r.fundus : '', r.perineum_type, r.perineum_heal, r.breast ? '乳房 ' + r.breast : '', r.mood].filter((v) => v),
        notes: r.notes || '',
        photos: r.photos || [],
      }))
    },
  },
  methods: {
    goBack() { uni.navigateBack() },
    async fetch() { this.loading = true; this.rows = await loadMyCare(); this.loading = false },
    preview(c, pi) {
      const urls = c.photos.map((p) => p.url)
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

.pad { padding: 8rpx 40rpx 40rpx; }
.ac { margin-top: 28rpx; }
.ahead { display: flex; align-items: baseline; }
.day { flex: 1; font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; }
.day .n { font-family: $font-display; font-size: 44rpx; color: $gold-deep; font-weight: 600; }
.ad { font-family: $font-display; font-size: 23rpx; color: $ink-3; letter-spacing: 2rpx; }

.vitals { display: flex; gap: 16rpx; margin-top: 22rpx; }
.vi { flex: 1; background: rgba(231, 212, 172, .14); border: 1rpx solid $hair; border-radius: 22rpx; padding: 18rpx 8rpx; text-align: center; }
.vv { display: block; font-family: $font-display; font-size: 30rpx; color: $gold-deep; font-weight: 600; }
.vl { display: block; font-size: 20rpx; color: $ink-2; margin-top: 6rpx; }

.tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 20rpx; }
.tg { font-size: 21rpx; color: $gold-deep; border: 1rpx solid $hair-s; border-radius: 40rpx; padding: 8rpx 20rpx; background: rgba(231, 212, 172, .12); }

.note { display: block; font-size: 23rpx; color: $ink-2; margin-top: 18rpx; line-height: 1.7; border-top: 1rpx dashed $hair; padding-top: 16rpx; }
.phs { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 16rpx; }
.ph { width: 132rpx; height: 132rpx; border-radius: 18rpx; border: 1rpx solid $hair; background: $ivory-2; }

.empty { text-align: center; padding: 140rpx 40rpx; }
.empty .em { display: block; font-size: 72rpx; color: $gold-soft; }
.empty .et { display: block; font-size: 25rpx; color: $ink-3; margin-top: 24rpx; line-height: 1.8; }

</style>
