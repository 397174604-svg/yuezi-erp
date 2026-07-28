<template>
  <scroll-view scroll-y class="portal">
    <view class="head">
      <text class="logo">☾</text>
      <view class="ht"><text class="ttl">奇德芬芳 · 演示门户</text><text class="note">本地演示 · 生产不部署</text></view>
    </view>

    <input class="search" v-model="kw" placeholder="搜索账号：姓名 / 手机号 / 角色 / 等级" confirm-type="search" />

    <view v-if="loading" class="loading">正在加载账号名录…</view>
    <view v-if="err" class="err">{{ err }}</view>

    <block v-if="!loading && !err">
      <text class="section">员 工 账 号 · 按 角 色</text>
      <view v-for="g in staffGroups" v-show="visStaff(g).length" :key="g.role" class="group">
        <view class="ghead" @tap="toggle(g.role)">
          <text class="grole">{{ g.role }}</text>
          <text class="gn">（{{ kw ? visStaff(g).length + '/' + g.list.length : g.list.length }}）</text>
          <text class="arr">{{ isOpen(g.role) ? '▾' : '›' }}</text>
        </view>
        <view v-if="isOpen(g.role)" class="rows">
          <view v-for="s in visStaff(g)" :key="s.phone" class="row">
            <view class="info"><text class="nm">{{ s.name }}</text><text class="meta">{{ s.position || s.role }}{{ s.department ? ' · ' + s.department : '' }} · {{ s.phone || '—' }}</text></view>
            <view class="btns"><text v-for="e in endsFor(s.role)" :key="e" class="btn" hover-class="btn-h" @tap="goStaff(s.phone, e)">{{ endLabel[e] }}</text></view>
          </view>
        </view>
      </view>

      <text class="section">宝 妈 账 号 · 全 部 客 户</text>
      <view class="group">
        <view class="ghead" @tap="toggle('宝妈')">
          <text class="grole">宝妈</text>
          <text class="gn">（{{ kw ? visMom.length + '/' + customers.length : customers.length }}）</text>
          <text class="arr">{{ isOpen('宝妈') ? '▾' : '›' }}</text>
        </view>
        <view v-if="isOpen('宝妈')" class="rows">
          <view v-for="c in visMom" :key="c.customer_id" class="row">
            <view class="info"><text class="nm">{{ c.name }}</text><text class="meta">{{ c.level || '—' }} · {{ c.status || '' }} · {{ c.phone || '—' }}</text></view>
            <view class="btns"><text class="btn" hover-class="btn-h" @tap="goMom(c.customer_id)">进入</text></view>
          </view>
        </view>
      </view>
      <text class="foot">点账号右侧按钮即以该身份进对应手机端（免登录，身份与数据范围原样生效）。员=员工端 · 产=产康门店端 · 美=科研美容端 · 宝妈组进宝妈端。</text>
    </block>
  </scroll-view>
</template>

<script>
import { REMOTE as R_staff } from '@/common/staff/remote.js'
import { REMOTE as R_rehab } from '@/common/rehab/remote.js'
import { REMOTE as R_beauty } from '@/common/beauty/remote.js'
import { REMOTE as R_mom } from '@/common/mom/remote.js'

const ROLE_ENDS = {
  '老板': ['staff', 'rehab', 'beauty'], '运营': ['staff', 'rehab', 'beauty'], '店长': ['staff', 'rehab', 'beauty'], '店长助理': ['staff', 'rehab', 'beauty'],
  '前台': ['rehab', 'beauty'], '收银': ['rehab', 'beauty'], '产康师': ['rehab', 'beauty'], '销售顾问': ['staff', 'rehab'],
  '护士': ['staff'], '技师': ['staff', 'rehab'],
}
const GROUP_ORDER = ['老板', '运营', '店长', '店长助理', '前台', '收银', '销售顾问', '产康师', '护士', '技师']

export default {
  data() {
    return {
      kw: '', loading: true, err: '', pass: '123456',
      staffGroups: [],   // [{role, list:[...]}]
      customers: [],
      open: {},          // 折叠状态
      endLabel: { staff: '员', rehab: '产', beauty: '美' },
    }
  },
  computed: {
    visMom() {
      const k = this.kw.trim().toLowerCase()
      if (!k) return this.customers
      return this.customers.filter((c) => [c.name, c.phone, c.level, '宝妈'].filter(Boolean).join('|').toLowerCase().includes(k))
    },
  },
  async onLoad() {
    try {
      const base = R_staff.baseUrl || 'http://127.0.0.1:8799'
      this.base = base
      const demo = await this.req('/auth/demo-accounts', 'GET')
      this.pass = (demo && demo.password) || '123456'
      const boss = ((demo && demo.staff) || []).find((s) => s.role === '老板') || (demo && demo.staff || [])[0]
      const bt = (await this.req('/auth/login', 'POST', null, { phone: boss.phone, password: this.pass })).token
      const [staff, customers] = await Promise.all([
        this.req('/staff', 'GET', bt),
        this.req('/customers?limit=500', 'GET', bt),
      ])
      const active = (staff || []).filter((s) => (s.status || '在职') === '在职')
      const byRole = {}
      for (const s of active) (byRole[s.role || '其他'] = byRole[s.role || '其他'] || []).push(s)
      const groups = []
      const seen = new Set()
      for (const role of GROUP_ORDER) { if (byRole[role]) { groups.push({ role, list: byRole[role] }); seen.add(role) } }
      for (const role of Object.keys(byRole)) if (!seen.has(role)) groups.push({ role, list: byRole[role] })
      this.staffGroups = groups
      this.customers = customers || []
      const open = {}; for (const g of groups) open[g.role] = (g.role === '老板' || g.role === '店长'); open['宝妈'] = false
      this.open = open
      this.loading = false
    } catch (e) {
      this.loading = false
      this.err = '门户初始化失败（后端未启动 / 连不上）：' + (e && e.errMsg || e && e.message || e)
    }
  },
  methods: {
    req(path, method, token, data) {
      return new Promise((resolve, reject) => {
        uni.request({
          url: this.base + '/api/v1' + path, method, timeout: 15000,
          header: { 'content-type': 'application/json', 'x-tenant-id': '1', ...(token ? { authorization: 'Bearer ' + token } : {}) },
          data,
          success: (r) => { const b = r.data || {}; if (r.statusCode >= 400 || (b.code && b.code !== 'OK')) reject(new Error(b.msg || ('HTTP ' + r.statusCode))); else resolve(b.data) },
          fail: reject,
        })
      })
    },
    isOpen(role) { return this.kw ? true : !!this.open[role] },
    toggle(role) { if (this.kw) return; this.open = { ...this.open, [role]: !this.open[role] } },
    endsFor(role) { return ROLE_ENDS[role] || ['staff'] },
    visStaff(g) {
      const k = this.kw.trim().toLowerCase()
      if (!k) return g.list
      if (g.role.toLowerCase().includes(k)) return g.list
      return g.list.filter((s) => [s.name, s.phone, s.role, s.position, s.department].filter(Boolean).join('|').toLowerCase().includes(k))
    },
    async goStaff(phone, end) {
      try {
        uni.showLoading({ title: '登录中', mask: true })
        const r = await this.req('/auth/login', 'POST', null, { phone, password: this.pass })
        const R = { staff: R_staff, rehab: R_rehab, beauty: R_beauty }[end]
        R.token = r.token; R.tenantId = r.tenantId; R.storeId = (r.storeId != null ? r.storeId : null); R.staffId = r.staffId; R.isManager = !!r.isManager
        uni.hideLoading()
        uni.reLaunch({ url: '/pages/' + end + '/home/home' })
      } catch (e) { uni.hideLoading(); uni.showToast({ title: '登录失败：' + (e.message || e), icon: 'none' }) }
    },
    async goMom(customerId) {
      try {
        uni.showLoading({ title: '进入中', mask: true })
        const r = await this.req('/auth/login-customer', 'POST', null, { customerId })
        R_mom.token = r.token; R_mom.tenantId = r.tenantId; R_mom.customerId = r.customerId
        uni.hideLoading()
        uni.reLaunch({ url: '/pages/mom/home/home' })
      } catch (e) { uni.hideLoading(); uni.showToast({ title: '进入失败：' + (e.message || e), icon: 'none' }) }
    },
  },
}
</script>

<style lang="scss" scoped>
.portal { height: 100vh; background: linear-gradient(180deg, #F7F1E6, #FBF7F0); box-sizing: border-box; padding: 0 28rpx 60rpx; }
.head { display: flex; align-items: center; gap: 18rpx; padding: 56rpx 8rpx 24rpx; }
.head .logo { font-size: 56rpx; color: #9C7838; }
.head .ttl { font-size: 38rpx; color: #8C6A36; font-weight: 600; letter-spacing: 2rpx; }
.head .ht { display: flex; flex-direction: column; }
.head .note { font-size: 20rpx; color: #B6AC98; margin-top: 4rpx; }
.search { background: #FFFDF9; border: 1rpx solid #EAe0cf; border-radius: 40rpx; padding: 22rpx 30rpx; font-size: 26rpx; color: #4A3818; margin-bottom: 24rpx; }
.loading, .err { text-align: center; color: #A89E8D; font-size: 26rpx; padding: 60rpx 0; }
.err { color: #A04545; }
.section { display: block; font-size: 24rpx; letter-spacing: 6rpx; color: #9C7838; margin: 20rpx 6rpx 14rpx; }
.group { background: #FFFDF9; border: 1rpx solid #EAe0cf; border-radius: 24rpx; margin-bottom: 18rpx; overflow: hidden; }
.ghead { display: flex; align-items: center; padding: 28rpx 28rpx; }
.ghead .grole { font-size: 28rpx; color: #4A3818; font-weight: 600; }
.ghead .gn { font-size: 24rpx; color: #A89E8D; margin-left: 8rpx; flex: 1; }
.ghead .arr { font-size: 30rpx; color: #C9B896; }
.rows { border-top: 1rpx solid #F1E9DA; }
.row { display: flex; align-items: center; padding: 22rpx 28rpx; border-bottom: 1rpx solid #F5EFE3; }
.row .info { flex: 1; display: flex; flex-direction: column; }
.row .nm { font-size: 28rpx; color: #4A3818; }
.row .meta { font-size: 20rpx; color: #A89E8D; margin-top: 4rpx; }
.btns { display: flex; gap: 12rpx; }
.btn { font-size: 24rpx; color: #8C6A36; border: 1rpx solid #D9C39A; border-radius: 30rpx; padding: 10rpx 24rpx; background: #FBF5EA; }
.btn-h { background: #E9D4A4; }
.foot { display: block; font-size: 20rpx; color: #B6AC98; line-height: 1.7; margin-top: 28rpx; padding: 0 6rpx; }
</style>
