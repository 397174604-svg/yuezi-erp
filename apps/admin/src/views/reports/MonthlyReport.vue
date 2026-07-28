<template>
  <div>
    <div class="bar">
      <h2 class="ph">经营月报</h2>
      <div class="ops">
        <el-date-picker v-model="month" type="month" value-format="YYYY-MM" placeholder="选择月份" size="small" style="width:140px" />
        <el-input v-model="storeId" placeholder="门店ID(可空)" size="small" style="width:120px" clearable />
        <el-button size="small" type="primary" :loading="loading" @click="load">生成</el-button>
        <el-button size="small" :disabled="!r" @click="exportCsv">导出 CSV</el-button>
      </div>
    </div>

    <template v-if="r">
      <div class="sec">营收概览（{{ r.month }}{{ r.storeId ? ' · 门店' + r.storeId : ' · 全部门店' }}）</div>
      <div class="cards">
        <el-card shadow="never" class="kpi drill" @click="openDrill('turnover')"><div class="t">实收营业额 <span class="go">透视 ›</span></div><div class="v">{{ money(r.revenue.turnover) }}</div><div v-if="yoy.turnover != null" class="d" :class="yoy.turnover >= 0 ? 'up' : 'down'">环比 {{ yoy.turnover >= 0 ? '+' : '' }}{{ yoy.turnover }}%</div></el-card>
        <el-card shadow="never" class="kpi drill" @click="openDrill('gmv')"><div class="t">成交额(GMV) <span class="go">透视 ›</span></div><div class="v">{{ money(r.revenue.gmv) }}</div><div v-if="yoy.gmv != null" class="d" :class="yoy.gmv >= 0 ? 'up' : 'down'">环比 {{ yoy.gmv >= 0 ? '+' : '' }}{{ yoy.gmv }}%</div></el-card>
        <el-card shadow="never" class="kpi drill" @click="openDrill('due')"><div class="t">应收欠款 <span class="go">透视 ›</span></div><div class="v warn">{{ money(r.revenue.due) }}</div><div class="d muted">占 GMV {{ r.revenue.gmv ? Math.round(r.revenue.due / r.revenue.gmv * 100) : 0 }}%</div></el-card>
        <el-card shadow="never" class="kpi drill" @click="openDrill('order')"><div class="t">订单/客户数 <span class="go">透视 ›</span></div><div class="v">{{ r.revenue.orderCount }} / {{ r.revenue.customerCount }}</div><div v-if="yoy.orderCount != null" class="d" :class="yoy.orderCount >= 0 ? 'up' : 'down'">订单环比 {{ yoy.orderCount >= 0 ? '+' : '' }}{{ yoy.orderCount }}%</div></el-card>
      </div>
      <div class="cards">
        <el-card shadow="never" class="kpi"><div class="t">收入(已审)</div><div class="v ok">{{ money(r.finance.income) }}</div></el-card>
        <el-card shadow="never" class="kpi"><div class="t">支出(已审)</div><div class="v warn">{{ money(r.finance.expense) }}</div></el-card>
        <el-card shadow="never" class="kpi"><div class="t">收支净额</div><div class="v" :class="r.finance.net >= 0 ? 'ok' : 'bad'">{{ money(r.finance.net) }}</div></el-card>
        <el-card shadow="never" class="kpi"><div class="t">新增客户</div><div class="v">+{{ r.customers.newCount }}</div></el-card>
        <el-card shadow="never" class="kpi"><div class="t">入住率</div><div class="v">{{ r.rooms.occupancyRate }}% <span class="muted">({{ r.rooms.occupied }}/{{ r.rooms.total }})</span></div></el-card>
      </div>

      <div class="panes">
        <el-card shadow="never" class="pane">
          <template #header><b>品项销售 TOP10</b></template>
          <el-table :data="r.itemTop" border size="small" empty-text="本月无销售">
            <el-table-column type="index" label="#" width="44" />
            <el-table-column prop="name" label="品项" min-width="130" show-overflow-tooltip />
            <el-table-column prop="qty" label="销量" width="80" align="right" />
            <el-table-column label="销售额" min-width="110" align="right"><template #default="{ row }">{{ money(row.sales) }}</template></el-table-column>
          </el-table>
        </el-card>
        <el-card shadow="never" class="pane">
          <template #header><b>员工业绩 TOP10</b></template>
          <el-table :data="r.staffPerformance" border size="small" empty-text="本月无业绩">
            <el-table-column type="index" label="#" width="44" />
            <el-table-column prop="executor" label="员工" min-width="110" />
            <el-table-column label="业绩" min-width="110" align="right"><template #default="{ row }">{{ money(row.perf) }}</template></el-table-column>
            <el-table-column label="手工费" width="100" align="right"><template #default="{ row }">{{ money(row.handFee) }}</template></el-table-column>
          </el-table>
        </el-card>
      </div>

      <!-- 卡片下钻 · 经营透视 -->
      <el-drawer v-model="drill.open" :title="`经营透视 · ${r.month} · ${drillTitle}`" size="480px">
        <div class="drill-body">
          <div class="dhead" v-if="drillHead">{{ drillHead }}</div>
          <template v-for="key in drillSecs" :key="key">
            <div class="dsec" v-if="key === 'trend'">
              <div class="dh">营收趋势 · 当月按日</div>
              <svg v-if="trendLine.line" viewBox="0 0 520 108" class="dsvg">
                <defs><linearGradient id="mfa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E9D4A4" stop-opacity=".5" /><stop offset="1" stop-color="#E9D4A4" stop-opacity="0" /></linearGradient></defs>
                <path :d="trendLine.area" fill="url(#mfa)" /><path :d="trendLine.line" fill="none" stroke="#9C7838" stroke-width="2" />
                <text v-for="(x, i) in trendLine.xs" :key="i" :x="x.x" :y="106" text-anchor="middle" class="dx">{{ x.l }}</text>
              </svg>
              <div v-else class="empty">本月无营收数据</div>
            </div>
            <div class="dsec" v-else-if="key === 'domain'">
              <div class="dh">收入构成 · 按业务板块</div>
              <div class="dbar" v-for="b in domainBars" :key="b.k"><span class="dk">{{ b.k }}</span><div class="dt"><i :style="{ width: b.pct + '%', background: b.color }" /></div><span class="dv">{{ money(b.v) }}</span><span class="dp">{{ b.pct }}%</span></div>
              <div v-if="!domainBars.length" class="empty">本月无数据</div>
            </div>
            <div class="dsec" v-else-if="key === 'pay'">
              <div class="dh">支付方式 · 实收占比</div>
              <div class="dbar" v-for="b in payBars" :key="b.k"><span class="dk">{{ b.k }}</span><div class="dt"><i :style="{ width: b.pct + '%', background: b.color }" /></div><span class="dv">{{ money(b.v) }}</span><span class="dp">{{ b.pct }}%</span></div>
              <div v-if="!payBars.length" class="empty">本月无收款</div>
            </div>
            <div class="dsec" v-else-if="key === 'status'">
              <div class="dh">订单状态 · 分布</div>
              <div class="dbar" v-for="b in statusBars" :key="b.k"><span class="dk">{{ b.k }}</span><div class="dt"><i :style="{ width: b.pct + '%', background: b.color }" /></div><span class="dv">{{ b.v }} 单</span><span class="dp">{{ b.pct }}%</span></div>
              <div v-if="!statusBars.length" class="empty">本月无订单</div>
            </div>
            <div class="dsec" v-else-if="key === 'store'">
              <div class="dh">门店对比 · 实收</div>
              <div class="dbar" v-for="b in storeBars2" :key="b.k"><span class="dk">{{ b.k }}</span><div class="dt"><i class="gold" :style="{ width: b.w + '%' }" /></div><span class="dv">{{ money(b.v) }}</span><span class="dp">{{ b.orders }}单</span></div>
              <div v-if="storeBars2.length < 2" class="empty">单门店口径</div>
            </div>
            <div class="dsec" v-else-if="key === 'due'">
              <div class="dh">应收欠款 · Top 订单（按客户）</div>
              <div class="dbar" v-for="b in dueList" :key="b.no"><span class="dk">{{ b.name }}</span><div class="dt"><i class="clay" :style="{ width: b.w + '%' }" /></div><span class="dv">{{ money(b.due) }}</span><span class="dp">{{ b.date }}</span></div>
              <div v-if="!dueList.length" class="empty">本月无欠款订单</div>
            </div>
          </template>
          <div class="dnote">透视口径为「{{ r.month }}」当月，图表接真实 orders 聚合；店长视角自动仅本店。</div>
        </div>
      </el-drawer>
    </template>
    <el-empty v-else description="选择月份后点「生成」" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => (Number(v) < 0 ? '-¥' : '¥') + Math.abs(Math.round(Number(v) || 0)).toLocaleString()
const now = new Date()
const month = ref(now.toISOString().slice(0, 7))
const storeId = ref('')
const r = ref<any>(null)
const loading = ref(false)

// —— 卡片下钻 · 经营透视（复用 businessCharts / by-store / 上月对比）——
const mc = ref<any>({ trend: [], byDomain: [], byPay: [], byStatus: [] })
const stores = ref<any[]>([])
const prev = ref<any>(null)
const drill = ref<{ open: boolean; metric: string }>({ open: false, metric: 'turnover' })
const DCOL = ['#8C6A36', '#B8945A', '#C2A063', '#E7D4AC', '#EDE0C4', '#D8C39A']
// 每张卡下钻到各自侧重的分析段（顺序即优先级）
const DRILL: Record<string, { title: string; secs: string[] }> = {
  turnover: { title: '实收营业额', secs: ['trend', 'pay', 'store', 'domain'] },
  gmv: { title: '成交额 GMV', secs: ['domain', 'trend', 'store'] },
  due: { title: '应收欠款', secs: ['due', 'status', 'store'] },
  order: { title: '订单 / 客户', secs: ['status', 'trend', 'store'] },
}
function mRange(m: string) { return { from: m + '-01', to: m + '-31' } }
function prevMonth(m: string) { const [y, mo] = m.split('-').map(Number); return mo === 1 ? (y - 1) + '-12' : y + '-' + String(mo - 1).padStart(2, '0') }
function openDrill(metric: string) { drill.value = { open: true, metric } }

async function loadAnalysis() {
  const m = month.value; const sid = storeId.value ? Number(storeId.value) : undefined
  const [c, ss, pv] = await Promise.all([
    api().getBusinessCharts({ ...mRange(m), storeId: sid }).catch(() => null),
    api().getStoreCompare(mRange(m)).catch(() => []),
    api().getBusinessStats({ ...mRange(prevMonth(m)), storeId: sid }).catch(() => null),
  ])
  mc.value = c || { trend: [], byDomain: [], byPay: [], byStatus: [] }
  stores.value = ss || []; prev.value = pv
}

// 环比上月（%）
const yoy = computed(() => {
  const cur = r.value?.revenue, p = prev.value
  const pct = (c: number, o: number) => (o ? Math.round(((c - o) / o) * 100) : null)
  if (!cur || !p) return {} as Record<string, number | null>
  return { turnover: pct(cur.turnover, p.turnover), gmv: pct(cur.gmv, p.gmv), orderCount: pct(cur.orderCount, p.orderCount) }
})
// 当月按日趋势迷你折线
const trendLine = computed(() => {
  const t: any[] = mc.value.trend || []; const x0 = 8, x1 = 512, y0 = 10, y1 = 96
  if (!t.length) return { line: '', area: '', xs: [] as any[] }
  const pts = t.length === 1 ? [t[0], t[0]] : t; const n = pts.length
  const max = Math.max(1, ...pts.map((p) => p.gmv))
  const X = (i: number) => x0 + i * (x1 - x0) / (n - 1); const Y = (v: number) => y1 - (v / max) * (y1 - y0)
  const line = 'M' + pts.map((p, i) => `${X(i).toFixed(1)},${Y(p.turnover).toFixed(1)}`).join(' L')
  const area = line + ` L${X(n - 1).toFixed(1)},${y1} L${x0},${y1} Z`
  const step = Math.max(1, Math.ceil(t.length / 5))
  const xs = t.length === 1 ? [] : t.map((p, i) => ({ x: X(i), l: Number((p.ym || '0-0').split('-')[2]) })).filter((_, i) => i % step === 0 || i === t.length - 1)
  return { line, area, xs }
})
function bars(arr: any[], key: string, vk: string) {
  const total = arr.reduce((a, x) => a + (Number(x[vk]) || 0), 0) || 1
  return arr.map((x, i) => ({ k: x[key], v: Number(x[vk]) || 0, pct: Math.round((Number(x[vk]) || 0) / total * 100), color: DCOL[i % DCOL.length] }))
}
const domainBars = computed(() => bars(mc.value.byDomain || [], 'k', 'amount'))
const payBars = computed(() => bars(mc.value.byPay || [], 'k', 'amount'))
const statusBars = computed(() => bars(mc.value.byStatus || [], 'k', 'count'))
const storeBars2 = computed(() => {
  const arr = (stores.value || []).slice().sort((a, b) => (b.turnover || 0) - (a.turnover || 0)).slice(0, 8)
  const max = Math.max(1, ...arr.map((x) => x.turnover || 0))
  return arr.map((x) => ({ k: x.storeName, v: Number(x.turnover) || 0, orders: x.orders || 0, w: Math.max(3, Math.round((Number(x.turnover) || 0) / max * 100)) }))
})
// 欠款订单明细（当月 Top）
const dueList = computed(() => {
  const arr: any[] = mc.value.topDue || []
  const max = Math.max(1, ...arr.map((x) => x.due || 0))
  return arr.map((x) => ({ no: x.orderNo, name: x.name, due: Number(x.due) || 0, date: x.date, w: Math.max(3, Math.round((Number(x.due) || 0) / max * 100)) }))
})
// 下钻视图：标题 / 分段顺序 / 头部摘要（随点击的卡而异）
const drillTitle = computed(() => DRILL[drill.value.metric]?.title || '')
const drillSecs = computed(() => DRILL[drill.value.metric]?.secs || ['trend'])
const drillHead = computed(() => {
  const rv = r.value?.revenue; if (!rv) return ''
  const cap = rv.orderCount ? Math.round(rv.turnover / rv.orderCount) : 0
  const st: any[] = mc.value.byStatus || []; const stot = st.reduce((a, x) => a + x.count, 0) || 1
  const paidRate = Math.round((st.find((x) => x.k === '已支付')?.count || 0) / stot * 100)
  const m = drill.value.metric
  if (m === 'turnover') return `收款率 ${rv.gmv ? Math.round(rv.turnover / rv.gmv * 100) : 0}% · 客单价 ¥${cap.toLocaleString()}`
  if (m === 'gmv') return `实收 ${money(rv.turnover)} · 欠款率 ${rv.gmv ? Math.round(rv.due / rv.gmv * 100) : 0}%`
  if (m === 'due') return `占 GMV ${rv.gmv ? Math.round(rv.due / rv.gmv * 100) : 0}% · 待收 ${dueList.value.length} 单(Top)`
  if (m === 'order') return `已支付率 ${paidRate}% · 客单价 ¥${cap.toLocaleString()}`
  return ''
})

async function load() {
  if (!month.value) { ElMessage.warning('请选择月份'); return }
  loading.value = true
  try { r.value = await api().getMonthlyReport({ month: month.value, storeId: storeId.value ? Number(storeId.value) : undefined }); await loadAnalysis() }
  catch (e: any) { ElMessage.error('生成失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
function exportCsv() {
  if (!r.value) return
  const d = r.value
  const rows: any[][] = [
    ['经营月报', d.month, d.storeId ? '门店' + d.storeId : '全部门店'],
    [],
    ['指标', '值'],
    ['实收营业额', d.revenue.turnover], ['成交额GMV', d.revenue.gmv], ['应收欠款', d.revenue.due],
    ['订单数', d.revenue.orderCount], ['客户数', d.revenue.customerCount],
    ['收入(已审)', d.finance.income], ['支出(已审)', d.finance.expense], ['收支净额', d.finance.net],
    ['新增客户', d.customers.newCount], ['入住率%', d.rooms.occupancyRate],
    [],
    ['品项TOP', '销量', '销售额'],
    ...d.itemTop.map((x: any) => [x.name, x.qty, x.sales]),
    [],
    ['员工业绩TOP', '业绩', '手工费'],
    ...d.staffPerformance.map((x: any) => [x.executor, x.perf, x.handFee]),
  ]
  const csv = rows.map((row) => row.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `经营月报_${d.month}.csv`; a.click(); URL.revokeObjectURL(a.href)
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.sec { font-weight: 600; margin: 6px 0 10px; color: var(--el-text-color-secondary); }
.cards { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.kpi { flex: 1; min-width: 130px; text-align: center; }
.kpi .t { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .v { font-size: 20px; font-weight: 600; margin-top: 4px; }
.kpi .v.warn { color: var(--el-color-danger); }
.kpi .v.ok { color: var(--el-color-success); }
.kpi .v.bad { color: var(--el-color-danger); }
.muted { color: var(--el-text-color-secondary); font-size: 12px; font-weight: 400; }
.panes { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 4px; }
.pane { min-width: 0; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }

/* —— 卡片下钻 · 经营透视 —— */
.kpi.drill { cursor: pointer; transition: box-shadow .15s, transform .15s; }
.kpi.drill:hover { box-shadow: 0 8px 22px -14px rgba(140, 106, 54, .55); transform: translateY(-1px); }
.kpi .t .go { font-size: 11px; color: var(--el-color-primary); font-weight: 400; opacity: 0; transition: opacity .15s; }
.kpi.drill:hover .t .go { opacity: 1; }
.kpi .d { font-size: 11px; margin-top: 3px; }
.kpi .d.up { color: var(--el-color-success); }
.kpi .d.down { color: var(--el-color-danger); }
.kpi .d.muted { color: var(--el-text-color-secondary); }
.drill-body { display: flex; flex-direction: column; gap: 20px; }
.dsec .dh { font-weight: 600; font-size: 14px; margin-bottom: 10px; padding-left: 9px; border-left: 3px solid var(--el-color-primary); }
.dsvg { width: 100%; height: auto; }
.dx { font-size: 9px; fill: var(--el-text-color-secondary); }
.dbar { display: grid; grid-template-columns: 88px 1fr auto auto; align-items: center; gap: 10px; margin-bottom: 9px; font-size: 12px; }
.dbar .dk { color: var(--el-text-color-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dbar .dt { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.dbar .dt i { display: block; height: 100%; }
.dbar .dt i.gold { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.dbar .dt i.clay { background: linear-gradient(90deg, #D9B08E, #AE6E56); }
.dhead { font-size: 13px; color: var(--el-color-primary); background: var(--el-fill-color-lighter); border-radius: 8px; padding: 8px 12px; font-weight: 600; }
.dbar .dv { font-weight: 600; min-width: 76px; text-align: right; }
.dbar .dp { color: var(--el-text-color-secondary); min-width: 40px; text-align: right; }
.empty { color: var(--el-text-color-secondary); font-size: 13px; padding: 12px 0; }
.dnote { font-size: 11px; color: var(--el-text-color-secondary); border-top: 1px dashed var(--el-border-color); padding-top: 10px; }
</style>
