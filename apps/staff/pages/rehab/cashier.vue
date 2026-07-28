<template>
  <view class="screen">
    <view class="demo-flag">演示数据</view>
    <view class="dhead">
      <text class="back" @tap="back">‹</text>
      <text class="title">产康收银开单</text>
      <text class="act" @tap="toast('核销 / 退款')">核销·退款</text>
    </view>

    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <!-- 客户卡栏（换客户仅限产康客户） -->
        <view class="yz-card cust">
          <view class="pic">{{ (cust.name || '客').charAt(0) }}</view>
          <view class="info">
            <text class="cn">{{ cust.name || '未选客户' }} <text class="yz-tag yz-tag--solid" v-if="cust.level">{{ cust.level }}</text></text>
            <text class="card">{{ cust.hasCard }} · 卡号 {{ cust.cardNo }}</text>
          </view>
          <text class="switch" @tap="pickCustomer">换客户</text>
        </view>

        <view class="kpis">
          <view class="k"><text class="c">储值卡余额</text><text class="v">¥{{ (cust.storedCard || 0).toLocaleString() }}</text></view>
          <view class="k"><text class="c">账户余额</text><text class="v">¥{{ (cust.balance || 0).toLocaleString() }}</text></view>
          <view class="k"><text class="c">积分</text><text class="v">{{ cust.points || 0 }}</text></view>
        </view>

        <!-- 分类页签 -->
        <view class="tabs">
          <text v-for="(t,i) in tabs" :key="t" :class="['chip', cashTab===i?'on':'']" @tap="cashTab=i">{{ t }}</text>
        </view>

        <!-- 项目列表（品项只列产康域；划卡/充值非目录型提示） -->
        <view class="yz-card">
          <view v-if="!shownItems.length" class="empty">{{ emptyHint }}</view>
          <view class="pitem" v-for="p in shownItems" :key="p.id">
            <view class="pinfo">
              <text class="pn">{{ p.name }} <text class="cat">{{ p.cat }}</text></text>
              <text class="pr">¥ {{ p.price.toLocaleString() }}<text class="unit"> /{{ p.unit }}</text></text>
            </view>
            <view class="stepper">
              <text v-if="cart[p.id]" class="sbtn" @tap="dec(p.id)">−</text>
              <text v-if="cart[p.id]" class="q">{{ cart[p.id] }}</text>
              <text class="sbtn" @tap="inc(p.id)">＋</text>
            </view>
          </view>
        </view>

        <!-- 已选 · 业绩人员 -->
        <block v-if="cartCount">
          <view class="sechead"><text class="l">已选 · 业绩人员</text><text class="more" @tap="pickExec">{{ execName || '指定技师 ›' }}</text></view>
          <view class="yz-card">
            <view class="sel" v-for="p in cartItems" :key="p.id">
              <view><text class="sn">{{ p.name }} <text class="x">×{{ cart[p.id] }}</text></text><text class="perf">业绩人员 <text class="who">{{ execName || '未指定' }}</text></text></view>
              <text class="amt">¥ {{ (Math.round(p.price * cart[p.id] * discount * 100) / 100).toLocaleString() }}</text>
            </view>
          </view>
        </block>
      </view>
    </scroll-view>

    <!-- 结算栏（固定底部） -->
    <view class="cartbar">
      <view class="break">
        <text v-if="discount < 1">会员 {{ cust.level }} · {{ (discount * 10).toFixed(discount * 10 % 1 ? 1 : 0) }}折</text>
        <text>折前 ¥{{ cartTotal.toLocaleString() }}</text>
        <text class="r" v-if="discount < 1">已省 ¥{{ (cartTotal - discountedTotal).toLocaleString() }}</text>
      </view>
      <view class="settle">
        <view><text class="sum">{{ cartCount }} 项 · 折后应收{{ discount < 1 ? '（已享' + (discount * 10).toFixed(discount * 10 % 1 ? 1 : 0) + '折）' : '' }}</text><text class="tot">¥ {{ discountedTotal.toLocaleString() }}</text></view>
        <text :class="['pay', cartCount? '' : 'off']" @tap="checkout">确认结算</text>
      </view>
    </view>
  </view>
</template>

<script>
import { loadDashboard, loadCustomers, checkout } from '@/common/rehab.js'
import { discountedTotal as discTotal } from '@/common/logic.js'
export default {
  data() {
    return { cust: { name: '', level: '', cardNo: '—', hasCard: '—', storedCard: 0, balance: 0, points: 0 }, tabs: ['划卡', '购买项目', '购买商品', '购卡', '余额充值'], items: [], custList: [], cart: {}, cashTab: 1, submitting: false, payMethods: ['现金', '刷卡', '微信支付', '支付宝', '储值卡'], discountMap: {}, techs: [], execId: null, execName: '' }
  },
  async onLoad() {
    const d = await loadDashboard() // 收银品项(限产康)/默认客户(首位产康客户)/等级折扣/技师来自后端
    this.cust = d.cashierCustomer; this.tabs = d.cashierTabs; this.items = d.items; this.discountMap = d.discountMap || {}; this.techs = d.techs || []
    this.custList = await loadCustomers(100) // 换客户候选：仅产康客户
  },
  computed: {
    cartCount() { return Object.values(this.cart).reduce((a, b) => a + b, 0) },
    cartTotal() { return this.items.reduce((s, p) => s + (this.cart[p.id] || 0) * p.price, 0) }, // 折前
    discount() { return this.discountMap[this.cust.level] || 1 }, // 会员等级折扣率（后端配置）
    discountedTotal() { return discTotal(this.items, this.cart, this.discount) }, // 折后应收（logic.js，与后端逐行 round2 一致）
    cartItems() { return this.items.filter(p => this.cart[p.id]) },
    shownItems() {
      const cat = { 1: '项目', 2: '商品', 3: '次卡' }[this.cashTab]
      return cat ? this.items.filter(p => p.cat === cat) : []
    },
    emptyHint() {
      if (this.cashTab === 0) return '划卡核销：按客户已购次卡核销（移动端建设中，可在 PC 后台操作）'
      if (this.cashTab === 4) return '余额充值：请在 PC 后台「充值 / 购卡」操作（移动端建设中）'
      return '该类目暂无可售品项'
    }
  },
  methods: {
    back() { uni.navigateBack() },
    inc(id) { this.cart[id] = (this.cart[id] || 0) + 1; this._idemKey = null }, // 购物车变更→幂等键失效（新结算意图）
    dec(id) { if (this.cart[id]) { this.cart[id]--; if (!this.cart[id]) delete this.cart[id] } this._idemKey = null },
    toast(t) { uni.showToast({ title: t + '（示意）', icon: 'none' }) },
    pickCustomer() { // 选客范围限产康（domain_first=产康）→ 开单订单域恒为产康
      const list = this.custList || []
      if (!list.length) return uni.showToast({ title: '无产康客户', icon: 'none' })
      const items = list.slice(0, 20).map(c => c.name + ' · ' + c.level)
      uni.showActionSheet({ itemList: items, success: e => {
        const c = list[e.tapIndex]; if (!c) return
        this.cust = { customerId: c.customerId, name: c.name, level: c.level, cardNo: c.cardNo || '—', hasCard: c.hasCard || '—', storedCard: c.storedCard || 0, balance: c.balance || 0, points: c.points || 0 }
        this.cart = {}; this._idemKey = null // 换客户→清购物车与幂等键
      } })
    },
    pickExec() {
      const list = (this.techs || []).map(t => t.name)
      if (!list.length) return uni.showToast({ title: '无在岗技师', icon: 'none' })
      const items = ['不指定', ...list]
      uni.showActionSheet({ itemList: items, success: e => {
        if (e.tapIndex === 0) { this.execId = null; this.execName = '' }
        else { const t = this.techs[e.tapIndex - 1]; this.execId = t.staffId || t.staff_id || null; this.execName = t.name }
      } })
    },
    async checkout() {
      if (!this.cartCount || this.submitting) return // 防重复点击
      if (!this.cust.customerId) { uni.showToast({ title: '请先选择产康客户', icon: 'none' }); return }
      const n = this.cartCount, t = this.discountedTotal // 折后应收（后端按等级折扣独立算价，此处仅显示/储值卡预检）
      const pm = await new Promise(r => uni.showActionSheet({ itemList: this.payMethods, success: e => r(this.payMethods[e.tapIndex]), fail: () => r(null) }))
      if (!pm) return
      if (pm === '储值卡' && Number(this.cust.storedCard || 0) < t) { uni.showToast({ title: '储值卡余额不足（¥' + Number(this.cust.storedCard || 0).toLocaleString() + '）', icon: 'none' }); return }
      const disTxt = this.discount < 1 ? '（' + (this.discount * 10).toFixed(this.discount * 10 % 1 ? 1 : 0) + '折）' : ''
      const ok = await new Promise(r => uni.showModal({ title: '确认收银', content: n + ' 项 · ' + pm + ' · 实收 ¥' + t.toLocaleString() + disTxt + (this.execName ? ' · 业绩 ' + this.execName : ''), success: e => r(e.confirm), fail: () => r(false) }))
      if (!ok) return
      if (!this._idemKey) this._idemKey = 'idem-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10) // 稳定幂等键：同结算意图失败重试沿用同键，后端命中即返首单，杜绝双花
      this.submitting = true
      try {
        const lines = Object.keys(this.cart).map(id => ({ itemId: Number(String(id).replace(/^i/, '')), qty: this.cart[id] }))
        // 不传 paidAmount → 后端按等级折扣算应收全额收款（前后端折扣口径单一来源，杜绝 OVERPAID）；不传 domain → 订单域由 customer.domain_first 派生
        const r = await checkout(this.cust.customerId, lines, pm, undefined, this._idemKey, this.execId)
        if (pm === '储值卡') this.cust.storedCard = Math.max(0, Number(this.cust.storedCard || 0) - Number(r.paid != null ? r.paid : t))
        this.cart = {}; this._idemKey = null // 成功→开启下一笔新意图
        uni.showToast({ title: '已开单 ' + (r.orderNo || '') + ' · ' + pm + ' ¥' + Number(r.paid != null ? r.paid : t).toLocaleString(), icon: 'none' })
      } catch (e) {
        uni.showToast({ title: '收银失败：' + (e && e.message ? e.message : '请重试'), icon: 'none' }) // 失败保留购物车与幂等键，重试用同键
      } finally { this.submitting = false }
    }
  }
}
</script>

<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.dhead { display: flex; align-items: center; padding: 28rpx 40rpx 12rpx; }
.back { font-size: 48rpx; color: $gold-deep; width: 56rpx; }
.title { font-family: $font-cn-serif; font-size: 32rpx; font-weight: 600; }
.act { margin-left: auto; font-size: 22rpx; color: $gold-deep; }
.scroll { flex: 1; }
.pad { padding: 8rpx 40rpx 280rpx; }

.cust { display: flex; align-items: center; }
.cust .pic { width: 92rpx; height: 92rpx; border-radius: 28rpx; background: linear-gradient(135deg,#F3E7CF,#E3CDA0); border: 1rpx solid $hair; display: flex; align-items: center; justify-content: center; font-family: $font-cn-serif; color: $gold-deep; font-size: 34rpx; }
.cust .info { flex: 1; margin-left: 22rpx; } .cust .cn { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; } .cust .card { display: block; font-size: 21rpx; color: $ink-3; margin-top: 8rpx; }
.cust .switch { font-size: 22rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 12rpx 22rpx; border-radius: 60rpx; }

.kpis { display: flex; gap: 16rpx; margin-top: 18rpx; }
.kpis .k { flex: 1; background: $paper; border: 1rpx solid $hair; border-radius: 28rpx; padding: 24rpx 12rpx; text-align: center; }
.kpis .c { font-size: 21rpx; color: $ink-3; } .kpis .v { display: block; font-family: $font-display; font-size: 40rpx; color: $gold-deep; font-weight: 600; margin-top: 8rpx; }

.tabs { display: flex; flex-wrap: wrap; gap: 16rpx; margin: 28rpx 0 8rpx; }
.chip { font-size: 24rpx; padding: 14rpx 28rpx; border-radius: 40rpx; border: 1rpx solid $hair; color: $ink-2; background: $paper; }
.chip.on { background: $ink; color: $gold-soft; border: none; }

.pitem { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 0; border-bottom: 1rpx solid $hair; }
.pitem:last-child { border-bottom: 0; }
.pitem .pn { font-size: 27rpx; font-weight: 500; } .pitem .cat { font-size: 19rpx; color: $gold-deep; border: 1rpx solid $hair-s; border-radius: 30rpx; padding: 3rpx 12rpx; margin-left: 10rpx; }
.pitem .pr { display: block; font-family: $font-display; font-size: 32rpx; color: $gold-deep; font-weight: 600; margin-top: 8rpx; } .pitem .unit { font-family: $font-sans; font-size: 20rpx; color: $ink-3; }
.stepper { display: flex; align-items: center; }
.stepper .sbtn { width: 52rpx; height: 52rpx; border-radius: 50%; border: 1rpx solid $hair-s; color: $gold-deep; font-size: 32rpx; text-align: center; line-height: 48rpx; }
.stepper .q { font-family: $font-display; font-size: 32rpx; min-width: 44rpx; text-align: center; }

.sechead { margin: 36rpx 4rpx 18rpx; display: flex; justify-content: space-between; align-items: baseline; } .sechead .l { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; padding-left: 22rpx; border-left: 6rpx solid $gold; } .sechead .more { font-size: 22rpx; color: $gold-deep; }
.sel { display: flex; align-items: center; justify-content: space-between; padding: 20rpx 0; border-bottom: 1rpx solid $hair; } .sel:last-child { border-bottom: 0; }
.sel .sn { font-size: 26rpx; font-weight: 500; } .sel .x { color: $ink-3; font-weight: 400; } .sel .perf { display: block; font-size: 21rpx; color: $ink-3; margin-top: 6rpx; } .sel .who { color: $gold-deep; }
.sel .amt { font-family: $font-display; font-size: 30rpx; color: $gold-deep; font-weight: 600; }

.cartbar { position: fixed; left: 0; right: 0; bottom: var(--window-bottom, 0); background: $night; padding: 22rpx 40rpx 28rpx; }
.empty { font-size: 23rpx; color: $ink-3; padding: 34rpx 0; text-align: center; }
.cartbar .break { display: flex; gap: 24rpx; font-size: 21rpx; color: $gold-soft; flex-wrap: wrap; } .cartbar .break .r { margin-left: auto; }
.cartbar .settle { display: flex; align-items: center; justify-content: space-between; margin-top: 16rpx; }
.cartbar .sum { font-size: 21rpx; color: #D9CBB0; } .cartbar .tot { display: block; font-family: $font-display; font-size: 52rpx; color: #EAD3A0; font-weight: 600; line-height: 1; margin-top: 6rpx; }
.cartbar .pay { background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; border-radius: 60rpx; padding: 22rpx 52rpx; font-size: 28rpx; font-weight: 500; } .cartbar .pay.off { opacity: .4; }

.demo-flag { position: fixed; top: calc(env(safe-area-inset-top) + 10rpx); left: 50%; transform: translateX(-50%); z-index: 999; font-size: 20rpx; color: #8C6A36; background: rgba(231,212,172,.92); border: 1rpx solid rgba(184,148,90,.42); padding: 4rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 16rpx -10rpx rgba(74,56,24,.4); }
</style>
