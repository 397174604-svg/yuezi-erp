<template>
  <view class="screen">
    <view class="topbar"><text class="back" @tap="goBack">‹</text><text class="nm">AI 育儿问答</text><text class="tag">秒回</text></view>
    <scroll-view scroll-y class="scroll" :scroll-into-view="anchor" scroll-with-animation>
      <view class="pad">
        <view class="hint yz-card">
          <text class="ht">有问题随时问，AI 客服即时回复</text>
          <text class="hs">答案来自会所问答库（含通用育儿常识与院内流程），仅供参考、不构成医疗诊断；答不上的问题会自动转给护理主任人工回复。</text>
        </view>
        <!-- 常见问题引导（点即问） -->
        <view class="chips" v-if="!items.length">
          <view class="chip" v-for="q in quickQs" :key="q" @tap="askQuick(q)">{{ q }}</view>
        </view>
        <!-- 对话流 -->
        <view v-for="(it, i) in items" :key="i" :id="'m' + i" class="msg">
          <view class="q"><text>{{ it.q }}</text></view>
          <view class="a yz-card" v-if="it.pending"><text class="thinking">正在检索问答库…</text></view>
          <view class="a yz-card" v-else-if="it.matched">
            <text class="at">{{ it.answer }}</text>
            <view class="meta"><text class="src">{{ it.category }} · 来源：{{ it.source }}</text></view>
            <view class="alts" v-if="it.alternatives && it.alternatives.length">
              <text class="alt-t">你可能还想问：</text>
              <view class="alt" v-for="al in it.alternatives" :key="al.qaId" @tap="askQuick(al.question)">{{ al.question }}</view>
            </view>
            <text class="disc">{{ it.disclaimer }}</text>
          </view>
          <view class="a yz-card miss" v-else>
            <text class="at">{{ it.msg }}</text>
            <text class="disc" v-if="it.disclaimer">{{ it.disclaimer }}</text>
          </view>
        </view>
        <view style="height: 40rpx" />
      </view>
    </scroll-view>
    <!-- 输入条 -->
    <view class="askbar">
      <input class="ipt" v-model="draft" placeholder="例如：宝宝脸上起小红疹怎么办" confirm-type="send" @confirm="ask" :disabled="busy" />
      <view class="send" :class="{ off: busy || !draft.trim() }" @tap="ask">问</view>
    </view>
  </view>
</template>
<script>
import { askQa } from '@/common/remote.js'
export default {
  data() {
    return {
      draft: '', busy: false, items: [], anchor: '',
      quickQs: ['宝宝皮肤有点黄是黄疸吗', '涨奶有硬块怎么疏通', '恶露多久排干净', '入所需要带什么', '产后多久能开始做产康'],
    }
  },
  onLoad() {
    // 首次使用知情提示（入口级知情确认，PIPL/内容责任审计项）：确认一次后记忆，不再打扰
    try {
      if (!uni.getStorageSync('qaNoticeAck')) {
        uni.showModal({
          title: '使用须知', showCancel: false, confirmText: '我知道了',
          content: '本会所非医疗机构。AI 问答的答案来自会所问答库，仅供参考、不构成医疗诊断；答不上的问题会转给护理主任在工作时间内回复。如宝宝或您出现异常症状，请及时就医。',
          success: () => { try { uni.setStorageSync('qaNoticeAck', '1') } catch (e) { /* 存储失败下次再提示 */ } },
        })
      }
    } catch (e) { /* 无存储环境时静默 */ }
  },
  methods: {
    goBack() { uni.navigateBack() },
    askQuick(q) { this.draft = q; this.ask() },
    async ask() {
      const q = this.draft.trim()
      if (!q || this.busy) return
      if (q.length < 2) { uni.showToast({ title: '问题至少 2 个字', icon: 'none' }); return }
      this.busy = true; this.draft = ''
      const it = { q, pending: true }
      this.items.push(it)
      this.anchor = 'm' + (this.items.length - 1)
      try {
        const r = await askQa(q) // 后端检索式硬校验：未命中即转人工，绝不编造
        Object.assign(it, r, { pending: false })
      } catch (e) {
        Object.assign(it, { pending: false, matched: false, msg: (e && e.message) || '提问失败，请稍后重试', disclaimer: '' })
      }
      this.items = [...this.items] // 触发渲染
      this.busy = false
      this.anchor = 'm' + (this.items.length - 1)
    },
  },
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; padding: 28rpx 40rpx 8rpx; }
.back { font-size: 44rpx; color: $gold-deep; margin-right: 18rpx; line-height: 1; }
.nm { font-family: $font-cn-serif; font-size: 36rpx; font-weight: 600; }
.tag { margin-left: 14rpx; font-size: 20rpx; color: #fff; background: $foil; border-radius: 20rpx; padding: 4rpx 14rpx; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 40rpx; }
.hint { margin-top: 16rpx; }
.ht { display: block; font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; }
.hs { display: block; font-size: 22rpx; color: $ink-3; margin-top: 10rpx; line-height: 1.7; }
.chips { display: flex; flex-wrap: wrap; gap: 16rpx; margin-top: 24rpx; }
.chip { font-size: 24rpx; color: $gold-deep; border: 1rpx solid $hair-s; border-radius: 40rpx; padding: 12rpx 24rpx; background: $paper; }
.msg { margin-top: 28rpx; }
.q { display: flex; justify-content: flex-end; }
.q text { max-width: 78%; background: $foil; color: #fff; font-size: 27rpx; border-radius: 28rpx 28rpx 6rpx 28rpx; padding: 18rpx 26rpx; line-height: 1.6; }
.a { margin-top: 16rpx; }
.a.miss { border-style: dashed; }
.at { display: block; font-size: 27rpx; line-height: 1.8; }
.thinking { font-size: 25rpx; color: $ink-3; }
.meta { margin-top: 14rpx; } .src { font-size: 21rpx; color: $gold-deep; }
.alts { margin-top: 16rpx; border-top: 1rpx solid $hair; padding-top: 14rpx; }
.alt-t { font-size: 22rpx; color: $ink-3; }
.alt { font-size: 24rpx; color: $gold-deep; padding: 10rpx 0; text-decoration: underline; }
.disc { display: block; font-size: 20rpx; color: $ink-3; margin-top: 14rpx; line-height: 1.6; }
.askbar { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 32rpx calc(16rpx + env(safe-area-inset-bottom)); background: $paper; border-top: 1rpx solid $hair; }
.ipt { flex: 1; background: $ivory; border: 1rpx solid $hair; border-radius: 40rpx; padding: 16rpx 28rpx; font-size: 26rpx; }
.send { width: 88rpx; height: 72rpx; border-radius: 36rpx; background: $foil; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28rpx; }
.send.off { opacity: 0.45; }

</style>
