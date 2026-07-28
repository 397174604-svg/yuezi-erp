<template>
  <div>
    <div class="head">
      <h2 class="ph">总部驾驶舱</h2>
      <el-select v-model="storeId" placeholder="全部门店" clearable style="width: 180px" @change="loadStats">
        <el-option v-for="s in stores" :key="s.store_id || s.id" :label="s.name" :value="s.store_id || s.id" />
      </el-select>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="6" v-for="k in kpis" :key="k.label">
        <div class="kpi" :class="{ clk: !!KPI_META[k.label] }" :title="KPI_META[k.label] ? '点击看' + k.label + '来源明细' : ''" @click="openKpi(k.label)">
          <div class="kl">{{ k.label }}<span v-if="KPI_META[k.label]" class="arr">›</span></div>
          <div class="kv serif">{{ k.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card class="funnel" shadow="never">
      <template #header><b>销售漏斗 · 本月</b><span class="fhint">点击各环节看明细</span></template>
      <el-row>
        <el-col :span="6" v-for="f in funnel" :key="f.label" class="fcol clk" :title="'点击看' + f.label + '线索明细'" @click="openFunnel(f.label)">
          <div class="fv serif">{{ f.value }}</div>
          <div class="fl">{{ f.label }}<span class="arr">›</span></div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 营收趋势 + 收入构成 -->
    <div class="grid2" v-loading="cLoading">
      <el-card class="panel" shadow="never">
        <template #header><b>营收趋势 · 按日</b><span class="fhint">实收(金线) / GMV(柱)</span></template>
        <div v-if="dtg.pts.length" class="tw">
          <svg :viewBox="`0 0 ${dtg.W} ${dtg.H}`" class="tchart" preserveAspectRatio="none">
            <rect v-for="(p,i) in dtg.pts" :key="'b'+i" :x="p.x-5" :y="p.gy" width="10" :height="dtg.y1-p.gy" class="gbar" />
            <path :d="dtg.area" class="tarea" />
            <polyline :points="dtg.line" class="tline" />
            <text v-for="(l,i) in dtg.labels" :key="'x'+i" :x="l.x" :y="dtg.y1+15" class="tx">{{ l.d }}</text>
          </svg>
        </div>
        <div v-else class="ph2">暂无趋势数据</div>
      </el-card>
      <el-card class="panel" shadow="never">
        <template #header><b>收入构成</b><span class="fhint">按业务板块 / 支付方式</span></template>
        <div class="csec">按业务板块</div>
        <div v-for="r in domainRows" :key="r.k" class="crow"><span class="ck">{{ r.k }}</span><div class="cbar"><i :style="{ width: pctA(r.amount, maxDomain) }" /></div><span class="cv">{{ money(r.amount) }}</span></div>
        <div class="csec">按支付方式</div>
        <div v-for="r in payRows" :key="r.k" class="crow"><span class="ck">{{ r.k }}</span><div class="cbar"><i class="pay" :style="{ width: pctA(r.amount, maxPay) }" /></div><span class="cv">{{ money(r.amount) }}</span></div>
        <div v-if="!domainRows.length" class="ph2">暂无构成数据</div>
      </el-card>
    </div>

    <!-- 门店排名 + 客户等级 -->
    <div class="grid2" v-loading="cLoading">
      <el-card class="panel" shadow="never">
        <template #header><b>门店排名 · 实收</b><span class="fhint">点门店按其筛选看板</span></template>
        <div v-for="(s,i) in storeRank" :key="s.storeId" class="srow" :class="{ on: storeId === s.storeId }" @click="pickStore(s.storeId)">
          <div class="stop">
            <span class="srk" :class="{ top: i === 0 }">{{ i + 1 }}</span>
            <span class="sn">{{ s.storeName }}</span>
            <span class="sv">{{ money(s.turnover) }}</span>
            <span class="so">{{ s.orders }}单</span>
          </div>
          <div class="sbar"><i :style="{ width: pctA(s.turnover, maxStore) }" /></div>
        </div>
        <div v-if="!storeRank.length" class="ph2">暂无门店数据</div>
      </el-card>
      <el-card class="panel" shadow="never">
        <template #header><b>客户等级构成</b><span class="fhint">全租户会员分层</span></template>
        <div v-for="l in levelRows" :key="l.level" class="lrow">
          <span class="ln2" :class="lvCls(l.level)">{{ l.level }}</span>
          <div class="lbar2"><i :class="lvCls(l.level)" :style="{ width: pctA(l.count, maxLevel) }" /></div>
          <span class="lc2">{{ l.count }}</span>
        </div>
        <div v-if="!levelRows.length" class="ph2">暂无等级数据</div>
      </el-card>
    </div>

    <p class="note">数据来自后端 stats/business 与 stats/funnel（产康口径）。多门店汇总与月子会所口径将在 C2 阶段补聚合层。点各卡片就地下钻看该指标的来源记录：客户数→客户列表、订单数/GMV/实收→订单列表（各合计）、漏斗→线索列表；点门店排名行按该门店筛选整个看板。</p>

    <!-- 二级抽屉：就地看该指标的来源构成，不离开驾驶舱；Esc 或「返回」关闭 -->
    <el-drawer v-model="drawer" :title="dTitle" size="46%" direction="rtl">
      <div v-loading="dLoading">
        <!-- 来源构成（按维度分组：实收→支付方式、GMV/订单数→状态、客户数→客户状态）-->
        <el-table v-if="dMode === 'breakdown'" :data="dRows" border stripe size="small" empty-text="暂无数据">
          <el-table-column prop="key" :label="dDimLabel" min-width="118" />
          <el-table-column prop="count" :label="dCountLabel" align="right" width="88" />
          <el-table-column v-if="dHasAmount" :label="dAmountLabel" align="right" width="140"><template #default="{ row }">¥{{ Number(row.amount).toLocaleString() }}</template></el-table-column>
          <el-table-column label="占比" min-width="170"><template #default="{ row }"><el-progress :percentage="Math.round(row.pct)" :stroke-width="14" /></template></el-table-column>
        </el-table>
        <!-- 线索明细（漏斗）-->
        <el-table v-else :data="dRows" border stripe size="small" height="calc(100vh - 190px)" empty-text="暂无线索">
          <el-table-column prop="name" label="姓名" min-width="80" />
          <el-table-column prop="phone" label="手机" min-width="118" />
          <el-table-column prop="status" label="状态" width="84" />
          <el-table-column prop="source" label="来源" min-width="90" />
          <el-table-column prop="assignee" label="顾问" min-width="80" />
        </el-table>
        <div v-if="dMode === 'breakdown'" class="dcount">共 {{ dTotalCount }} {{ dCountLabel }}<span v-if="dSumLabel"> · {{ dSumLabel }} ¥{{ dTotalAmount.toLocaleString() }}</span></div>
        <div v-else class="dcount">共 {{ dRows.length }} 条</div>
      </div>
      <template #footer><el-button type="primary" @click="drawer = false">返回</el-button></template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

// 二级入口：点 KPI → 就地弹抽屉看**该指标的来源构成**（按不同维度分组聚合，每个 KPI 明细都不同）；漏斗→线索列表。带「返回」+ Esc 关闭。
//   累计实收→按支付方式(渠道)构成；累计GMV→按订单状态构成；订单数→按订单状态构成；客户数→按客户状态构成。
const KPI_META: Record<string, { source: 'orders' | 'customers'; dim: string; dimLabel: string; amountCol?: string; countLabel: string; amountLabel?: string; sumLabel?: string }> = {
  累计实收: { source: 'orders', dim: 'pay_method', dimLabel: '支付方式', amountCol: 'paid_amount', countLabel: '单数', amountLabel: '实收', sumLabel: '实收合计' },
  '累计 GMV': { source: 'orders', dim: 'order_status', dimLabel: '订单状态', amountCol: 'order_amount', countLabel: '单数', amountLabel: 'GMV', sumLabel: 'GMV 合计' },
  订单数: { source: 'orders', dim: 'order_status', dimLabel: '订单状态', countLabel: '单数' },
  客户数: { source: 'customers', dim: 'status', dimLabel: '客户状态', countLabel: '客户数' },
}
const drawer = ref(false)
const dTitle = ref('')
const dMode = ref<'breakdown' | 'leads'>('breakdown')
const dLoading = ref(false)
const dRows = ref<any[]>([])
const dDimLabel = ref(''); const dCountLabel = ref(''); const dAmountLabel = ref(''); const dSumLabel = ref('')
const dHasAmount = computed(() => !!dAmountLabel.value)
const dTotalCount = computed(() => dRows.value.reduce((s, r) => s + (r.count || 0), 0))
const dTotalAmount = computed(() => dRows.value.reduce((s, r) => s + (r.amount || 0), 0))

// 按维度分组聚合：{维度值, 单数, 金额, 占比%}，按金额(或单数)降序
function groupBy(rows: any[], dim: string, amountCol?: string) {
  const m = new Map<string, { key: string; count: number; amount: number; pct: number }>()
  for (const r of rows) {
    const k = String(r[dim] || '未分类')
    if (!m.has(k)) m.set(k, { key: k, count: 0, amount: 0, pct: 0 })
    const g = m.get(k)!; g.count++; if (amountCol) g.amount += Number(r[amountCol]) || 0
  }
  const arr = [...m.values()]
  const tA = arr.reduce((s, g) => s + g.amount, 0), tC = arr.reduce((s, g) => s + g.count, 0)
  for (const g of arr) g.pct = amountCol ? (tA ? g.amount / tA * 100 : 0) : (tC ? g.count / tC * 100 : 0)
  arr.sort((a, b) => amountCol ? b.amount - a.amount : b.count - a.count)
  return arr
}

async function openKpi(label: string) {
  const meta = KPI_META[label]; if (!meta) return
  dTitle.value = label + ' · 来源构成'; dMode.value = 'breakdown'
  dDimLabel.value = meta.dimLabel; dCountLabel.value = meta.countLabel; dAmountLabel.value = meta.amountLabel || ''; dSumLabel.value = meta.sumLabel || ''
  dRows.value = []; drawer.value = true; dLoading.value = true
  const f: any = { limit: 500, ...(storeId.value ? { storeId: storeId.value } : {}) }
  try {
    let recs: any[] = []
    if (meta.source === 'orders') recs = (await api().listOrders(f) as any[]) || []
    else { const d = await api().listCustomers(f) as any; recs = Array.isArray(d) ? d : (d?.rows || []) }
    dRows.value = groupBy(recs, meta.dim, meta.amountCol)
  } catch (e: any) { ElMessage.error('明细加载失败：' + (e?.message || '')) } finally { dLoading.value = false }
}
async function openFunnel(label: string) {
  dMode.value = 'leads'; dTitle.value = label + ' · 线索明细'; dDimLabel.value = ''; dAmountLabel.value = ''; dSumLabel.value = ''; dRows.value = []; drawer.value = true; dLoading.value = true
  const f: any = { ...(storeId.value ? { storeId: storeId.value } : {}) }
  if (label === '跟进中') f.status = '跟进中'; else if (label === '已转化') f.status = '已转化' // 其余环节看全部线索
  try { dRows.value = (await api().listLeads(f) as any[]) || [] }
  catch (e: any) { ElMessage.error('线索明细加载失败：' + (e?.message || '')) } finally { dLoading.value = false }
}

const loading = ref(false)
const stores = ref<any[]>([])
const storeId = ref<number | null>(null)
const kpis = ref<Array<{ label: string; value: string }>>([
  { label: '累计实收', value: '—' },
  { label: '累计 GMV', value: '—' },
  { label: '订单数', value: '—' },
  { label: '客户数', value: '—' },
])
const funnel = ref<Array<{ label: string; value: string | number }>>([
  { label: '线索总数', value: '—' },
  { label: '跟进中', value: '—' },
  { label: '已转化', value: '—' },
  { label: '转化率', value: '—' },
])

function money(v: any): string {
  if (v == null) return '—'
  return typeof v === 'number' ? '¥' + Math.round(v).toLocaleString() : String(v)
}

// —— 看板填充：营收趋势 / 收入构成 / 门店排名 / 客户等级（复用现有接口，无新后端）——
const cLoading = ref(false)
const charts = ref<any>(null)
const storeRank = ref<any[]>([])
const levelRows = ref<any[]>([])
const domainRows = computed(() => (charts.value?.byDomain || []) as any[])
const payRows = computed(() => (charts.value?.byPay || []) as any[])
const maxDomain = computed(() => Math.max(1, ...domainRows.value.map((r: any) => Number(r.amount) || 0)))
const maxPay = computed(() => Math.max(1, ...payRows.value.map((r: any) => Number(r.amount) || 0)))
const maxStore = computed(() => Math.max(1, ...storeRank.value.map((r: any) => Number(r.turnover) || 0)))
const maxLevel = computed(() => Math.max(1, ...levelRows.value.map((r: any) => Number(r.count) || 0)))
function pctA(part: any, whole: any): string { const w = Number(whole) || 0; return (w ? Math.max(2, Math.round((Number(part) || 0) / w * 100)) : 0) + '%' }
function lvCls(level: string) { return ({ 黑金: 'lv-black', 钻石: 'lv-dia', 白银: 'lv-silver', 体验: 'lv-exp' } as Record<string, string>)[level] || 'lv-exp' }

const dtg = computed(() => {
  const t = (charts.value?.trend || []) as any[]
  const W = 1000, H = 190, x0 = 8, x1 = 992, y0 = 14, y1 = 158
  const maxV = Math.max(1, ...t.map((r) => Math.max(Number(r.turnover) || 0, Number(r.gmv) || 0)))
  const n = t.length
  const xOf = (i: number) => n <= 1 ? (x0 + x1) / 2 : x0 + (x1 - x0) * i / (n - 1)
  const yOf = (v: number) => y1 - (y1 - y0) * (v / maxV)
  const pts = t.map((r, i) => ({ x: xOf(i), y: yOf(Number(r.turnover) || 0), gy: yOf(Number(r.gmv) || 0), ym: r.ym }))
  const line = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  const area = pts.length ? `M${pts[0].x.toFixed(1)},${y1} ` + pts.map((p) => `L${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + ` L${pts[pts.length - 1].x.toFixed(1)},${y1} Z` : ''
  const labIdx = n <= 1 ? [0] : [0, Math.floor(n / 2), n - 1]
  const labels = labIdx.map((i) => ({ x: xOf(i), d: (t[i]?.ym || '').slice(5) }))
  return { W, H, y1, pts, line, area, labels }
})

function pickStore(id: number) { storeId.value = storeId.value === id ? null : id; loadStats(); loadCharts() }

async function loadCharts() {
  cLoading.value = true
  const filter = storeId.value ? { storeId: storeId.value } : {}
  try {
    const [c, byStore, cockpit] = await Promise.all([
      api().getBusinessCharts(filter).catch(() => null),
      api().getStoreCompare(filter).catch(() => []),
      api().getCockpit(filter).catch(() => null),
    ])
    charts.value = c
    storeRank.value = (Array.isArray(byStore) ? byStore : []).slice().sort((a: any, b: any) => Number(b.turnover) - Number(a.turnover))
    levelRows.value = ((cockpit as any)?.memberLevels || []).slice().sort((a: any, b: any) => Number(b.count) - Number(a.count))
  } catch { /* 图表失败不阻断主看板 */ } finally { cLoading.value = false }
}

async function loadStats() {
  loading.value = true
  const filter = storeId.value ? { storeId: storeId.value } : {}
  try {
    const b: any = await api().getBusinessStats(filter)
    kpis.value = [
      // 口径修正：stats/business 的 turnover/gmv 为【累计】口径——原「今日实收/本月GMV」标签与数值不符（今日口径见经营大屏）
      { label: '累计实收', value: money(b?.turnover ?? b?.paid) },
      { label: '累计 GMV', value: money(b?.gmv ?? b?.amount) },
      { label: '订单数', value: b?.orders ?? b?.orderCount ?? '—' },
      { label: '客户数', value: b?.customers ?? b?.customerCount ?? '—' },
    ]
  } catch (e: any) {
    ElMessage.error('经营统计加载失败：' + (e?.message || ''))
  } finally {
    loading.value = false
  }
  try {
    const f: any = await api().getFunnel(filter)
    const by = f?.byStatus || {}
    const rate = f?.conversionRate ?? f?.rate
    funnel.value = [
      { label: '线索总数', value: f?.total ?? f?.leads ?? '—' },
      { label: '跟进中', value: by['跟进中'] ?? '—' },
      { label: '已转化', value: f?.converted ?? by['已转化'] ?? '—' },
      { label: '转化率', value: rate != null ? Math.round(Number(rate) * (Number(rate) <= 1 ? 100 : 1)) + '%' : '—' },
    ]
  } catch { /* 漏斗失败不阻断 */ }
}

onMounted(async () => {
  try { stores.value = (await api().listStores()) || [] } catch { /* 门店列表失败不阻断 */ }
  await Promise.all([loadStats(), loadCharts()])
})
</script>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.ph {
  font-family: var(--font-cn-serif);
  font-weight: 600;
  margin: 0;
}
.kpi {
  background: var(--paper);
  border: 1px solid var(--hair);
  border-radius: var(--r-md);
  padding: 22px;
  transition: border-color .18s, box-shadow .18s, transform .18s;
}
.kpi.clk, .fcol.clk { cursor: pointer; }
.kpi.clk:hover {
  border-color: var(--gold);
  box-shadow: 0 10px 28px -18px rgba(140, 106, 54, .55);
  transform: translateY(-2px);
}
.fcol.clk { border-radius: var(--r-md); transition: background .18s; }
.fcol.clk:hover { background: rgba(184, 148, 90, .08); }
.arr { color: var(--gold); font-weight: 700; margin-left: 6px; opacity: .55; }
.kpi.clk:hover .arr, .fcol.clk:hover .arr { opacity: 1; }
.fhint { font-size: 12px; color: var(--ink-3); font-weight: 400; margin-left: 10px; }
.dcount { font-size: 12px; color: var(--ink-3); margin-top: 10px; text-align: right; }
:deep(.el-table .hl) { background: rgba(184, 148, 90, .1); font-weight: 600; color: var(--gold-deep); }
.kl {
  font-size: 13px;
  color: var(--ink-3);
}
.kv {
  font-size: 30px;
  color: var(--gold-deep);
  font-weight: 600;
  margin-top: 8px;
}
.funnel {
  margin-top: 18px;
  border: 1px solid var(--hair);
  border-radius: var(--r-md);
}
.fcol {
  text-align: center;
}
.fv {
  font-size: 28px;
  color: var(--gold-deep);
  font-weight: 600;
}
.fl {
  font-size: 13px;
  color: var(--ink-3);
  margin-top: 4px;
}
.note {
  font-size: 12px;
  color: var(--ink-3);
  margin-top: 16px;
}

/* —— 看板填充面板 —— */
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 18px; }
.panel { border: 1px solid var(--hair); border-radius: var(--r-md); }
.panel :deep(.el-card__header) { font-size: 14px; }
.ph2 { color: var(--ink-3); font-size: 13px; padding: 18px 0; text-align: center; }
.tw { width: 100%; overflow-x: auto; }
.tchart { width: 100%; height: 200px; display: block; }
.tchart .gbar { fill: rgba(184, 148, 90, .16); }
.tchart .tarea { fill: rgba(184, 148, 90, .12); }
.tchart .tline { fill: none; stroke: var(--gold); stroke-width: 2; }
.tchart .tx { fill: var(--ink-3); font-size: 11px; text-anchor: middle; }
.csec { font-size: 12px; color: var(--ink-3); font-weight: 600; margin: 8px 0 8px; }
.csec:first-child { margin-top: 0; }
.crow { display: grid; grid-template-columns: 74px 1fr auto; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 13px; }
.crow .ck { color: var(--ink-2, var(--ink-3)); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crow .cbar { height: 12px; background: var(--fill, rgba(0,0,0,.05)); border-radius: 6px; overflow: hidden; }
.crow .cbar i { display: block; height: 100%; background: linear-gradient(90deg, #C2A063, #8C6A36); }
.crow .cbar i.pay { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.crow .cv { font-weight: 600; min-width: 88px; text-align: right; color: var(--gold-deep); }
.srow { padding: 8px 6px; border-radius: var(--r-md); cursor: pointer; transition: background .15s; }
.srow:hover { background: rgba(184, 148, 90, .07); }
.srow.on { background: rgba(184, 148, 90, .13); }
.srow .stop { display: grid; grid-template-columns: 24px 1fr auto auto; align-items: center; gap: 10px; margin-bottom: 6px; }
.srow .srk { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 50%; background: rgba(0,0,0,.05); font-size: 12px; font-weight: 700; color: var(--ink-3); }
.srow .srk.top { background: linear-gradient(135deg, #E9D4A4, #B8945A); color: #fff; }
.srow .sn { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.srow .sbar { height: 8px; background: rgba(0,0,0,.05); border-radius: 4px; overflow: hidden; }
.srow .sbar i { display: block; height: 100%; background: linear-gradient(90deg, #C2A063, #8C6A36); }
.srow .sv { font-weight: 700; color: var(--gold-deep); }
.srow .so { color: var(--ink-3); font-size: 12px; }
.lrow { display: grid; grid-template-columns: 52px 1fr auto; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 13px; }
.lrow .ln2 { font-weight: 600; }
.lrow .lbar2 { height: 12px; background: rgba(0,0,0,.05); border-radius: 6px; overflow: hidden; }
.lrow .lbar2 i { display: block; height: 100%; }
.lrow .lc2 { font-weight: 700; min-width: 34px; text-align: right; }
.lv-black { color: #8C6A36; } .lbar2 i.lv-black { background: linear-gradient(90deg, #C2A063, #8C6A36); }
.lv-dia { color: #4a7a9c; } .lbar2 i.lv-dia { background: linear-gradient(90deg, #9cc4d8, #4a7a9c); }
.lv-silver { color: #8a8f96; } .lbar2 i.lv-silver { background: linear-gradient(90deg, #c3c8cf, #8a8f96); }
.lv-exp { color: var(--ink-3); } .lbar2 i.lv-exp { background: #cfc7ba; }
@media (max-width: 960px) { .grid2 { grid-template-columns: 1fr; } }
</style>
