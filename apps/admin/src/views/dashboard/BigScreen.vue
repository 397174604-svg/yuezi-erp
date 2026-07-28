<template>
  <div class="screen">
    <div class="hd">
      <div class="ttl">经营大屏 <span class="sub">实时经营驾驶舱</span></div>
      <div class="ops">
        <el-input v-model="storeId" placeholder="门店ID(可空=全部)" size="small" style="width:150px" clearable @change="load" />
        <el-switch v-model="auto" size="small" active-text="自动刷新" />
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
        <span class="asof">{{ asOf }}</span>
      </div>
    </div>

    <div v-loading="loading" class="grid">
      <div class="kpi hero clk" @click="openCard('revenue')"><div class="t">本月营收<span class="arr">›</span></div><div class="v">{{ money(d.revenue?.month) }}</div><div class="x">今日 {{ money(d.revenue?.today) }}</div></div>
      <div class="kpi clk" @click="openCard('due')"><div class="t">应收欠款<span class="arr">›</span></div><div class="v warn">{{ money(d.revenue?.due) }}</div></div>
      <div class="kpi"><div class="t">储值余额池</div><div class="v">{{ money(d.walletPool) }}</div></div>
      <div class="kpi clk" @click="openCard('inHouse')"><div class="t">在住客户<span class="arr">›</span></div><div class="v">{{ d.customers?.inHouse ?? 0 }}</div><div class="x">入住率 {{ d.rooms?.occupancyRate ?? 0 }}%</div></div>
      <div class="kpi clk" @click="openCard('customers')"><div class="t">客户总数<span class="arr">›</span></div><div class="v">{{ d.customers?.total ?? 0 }}</div><div class="x">今日新增 +{{ d.customers?.newToday ?? 0 }}</div></div>
      <div class="kpi clk" @click="openCard('rooms')"><div class="t">房态<span class="arr">›</span></div><div class="v">{{ d.rooms?.occupied ?? 0 }}<span class="slash">/{{ d.rooms?.total ?? 0 }}</span></div><div class="x">空闲 {{ d.rooms?.free ?? 0 }}</div></div>
      <div class="kpi clk" @click="openCard('appts')"><div class="t">今日预约<span class="arr">›</span></div><div class="v">{{ d.todayAppointments ?? 0 }}</div></div>
      <div class="kpi clk" @click="openCard('nanny')"><div class="t">月嫂在岗<span class="arr">›</span></div><div class="v">{{ d.nannyOnDuty ?? 0 }}</div></div>
      <div class="kpi clk" @click="openCard('approvals')"><div class="t">待审批<span class="arr">›</span></div><div class="v" :class="(d.pendingApprovals || 0) > 0 ? 'warn' : ''">{{ d.pendingApprovals ?? 0 }}</div></div>
    </div>

    <el-card shadow="never" class="trend-card">
      <template #header><b>近 14 日营收趋势</b><span class="muted"> 合计 {{ trendSum }}</span></template>
      <svg v-if="pts.length" :viewBox="`0 0 ${CW} ${CH}`" class="chart" preserveAspectRatio="none">
        <polygon :points="areaPoints" class="area" />
        <polyline :points="linePoints" class="line" />
        <circle v-for="(p, i) in pts" :key="i" :cx="p.x" :cy="p.y" r="2.5" class="dot"><title>{{ p.date }}：{{ money(p.v) }}</title></circle>
      </svg>
      <div v-if="pts.length" class="xaxis"><span>{{ pts[0].date.slice(5) }}</span><span>{{ pts[Math.floor(pts.length / 2)].date.slice(5) }}</span><span>{{ pts[pts.length - 1].date.slice(5) }}</span></div>
    </el-card>

    <el-card shadow="never" class="trend-card" v-if="fc">
      <template #header>
        <b>营收预测</b>
        <span class="muted"> 下周预测 ¥{{ Math.round(fc.summary.nextWeekForecast).toLocaleString() }}</span>
        <el-tag :type="fc.summary.wowPct >= 0 ? 'success' : 'danger'" size="small" effect="plain" style="margin-left:8px">环比 {{ fc.summary.wowPct >= 0 ? '+' : '' }}{{ fc.summary.wowPct }}%</el-tag>
        <span class="muted forecast-note"> · {{ fc.note }}</span>
      </template>
      <svg v-if="fpts.length" :viewBox="`0 0 ${CW} ${CH}`" class="chart" preserveAspectRatio="none">
        <polyline :points="fActualLine" class="line" />
        <polyline :points="fForecastLine" class="line fline" />
        <circle v-for="(p, i) in fpts" :key="i" :cx="p.x" :cy="p.y" r="2" :class="p.forecast ? 'dot fdot' : 'dot'"><title>{{ p.date }}：{{ money(p.v) }}{{ p.forecast ? '（预测）' : '' }}</title></circle>
      </svg>
      <div class="flegend"><span class="lg"><i class="sw actual" />实际</span><span class="lg"><i class="sw pred" />预测(趋势外推)</span></div>
    </el-card>

    <div class="panes">
      <el-card shadow="never" class="pane">
        <template #header><b>门店业绩排名</b></template>
        <el-table :data="d.storeRanking || []" border size="small" empty-text="暂无门店业绩">
          <el-table-column type="index" label="#" width="48" />
          <el-table-column prop="storeName" label="门店" min-width="120" />
          <el-table-column label="实收" min-width="120" align="right"><template #default="{ row }">{{ money(row.turnover) }}</template></el-table-column>
          <el-table-column prop="orders" label="订单" width="70" align="right" />
          <el-table-column label="" min-width="120"><template #default="{ row }"><div class="rbar"><div class="rfill" :style="{ width: rbpct(row.turnover) + '%' }" /></div></template></el-table-column>
        </el-table>
      </el-card>
      <el-card shadow="never" class="pane">
        <template #header><b>会员等级分布</b></template>
        <div v-if="(d.memberLevels || []).length" class="levels">
          <div v-for="l in d.memberLevels" :key="l.level" class="lv">
            <span class="ln">{{ l.level }}</span>
            <div class="bar"><div class="fill" :style="{ width: pct(l.count) + '%' }" /></div>
            <span class="lc">{{ l.count }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无会员等级数据" :image-size="60" />
      </el-card>
    </div>

    <!-- 补充信息密度：次卡核销 / 库存预警 / 客户生命周期（复用现有接口，随门店联动） -->
    <div class="panes3" v-loading="loading">
      <el-card shadow="never" class="pane">
        <template #header><b>次卡核销台账</b><span class="muted"> 已确认 {{ money(cardStats?.recognizedValue) }} · 整体 {{ cardStats?.recognizedRate ?? 0 }}%</span></template>
        <div v-if="(cardStats?.byType || []).length" class="cclist">
          <div v-for="t in (cardStats.byType || []).slice(0, 6)" :key="t.name" class="ccrow">
            <div class="cchead"><span class="ccn">{{ t.name }}</span><span class="ccc">{{ t.count }}张</span><span class="ccr">核销{{ t.rate }}%</span></div>
            <div class="ccbar"><i class="rec" :style="{ width: barPct(t.recognized, t.sold) }" /><i class="rem" :style="{ width: barPct(t.remaining, t.sold) }" /></div>
          </div>
        </div>
        <el-empty v-else description="暂无次卡" :image-size="52" />
      </el-card>

      <el-card shadow="never" class="pane">
        <template #header><b>库存预警</b><span class="muted"> 低于安全线 {{ invAlerts?.count ?? 0 }} · 缺货 {{ invAlerts?.outOfStock ?? 0 }}</span></template>
        <div v-if="(invAlerts?.items || []).length" class="ivlist">
          <div v-for="(it, i) in (invAlerts.items || []).slice(0, 7)" :key="i" class="ivrow" :class="{ oos: it.qty === 0 }">
            <span class="ivn">{{ it.name }}</span>
            <span class="ivq"><b :class="{ danger: it.qty === 0 }">{{ it.qty }}</b>/{{ it.warnQty }}</span>
            <span class="ivg">补 {{ it.suggestedQty }}</span>
          </div>
        </div>
        <el-empty v-else description="库存充足，无预警" :image-size="52" />
      </el-card>

      <el-card shadow="never" class="pane">
        <template #header><b>客户生命周期</b><span class="muted"> 共 {{ d.customers?.total ?? custTotal }} 位</span></template>
        <div v-if="custByStage.length" class="lclist">
          <div v-for="s in custByStage" :key="s.key" class="lcrow">
            <span class="lcn">{{ s.key }}</span>
            <div class="lcbar"><i :class="s.cls" :style="{ width: stagePct(s.count) }" /></div>
            <span class="lcc">{{ s.count }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无客户" :image-size="52" />
      </el-card>
    </div>

    <!-- 二级抽屉：点卡片就地看来源/明细，不离开大屏；Esc 或「返回」关闭 -->
    <el-drawer v-model="drawer" :title="dTitle" size="46%" direction="rtl">
      <div v-loading="dLoading">
        <el-table v-if="dMode === 'breakdown'" :data="dRows" border stripe size="small" empty-text="暂无数据">
          <el-table-column prop="key" :label="dDimLabel" min-width="118" />
          <el-table-column prop="count" :label="dCountLabel" align="right" width="90" />
          <el-table-column v-if="dHasAmount" :label="dAmountLabel" align="right" width="140"><template #default="{ row }">¥{{ Number(row.amount).toLocaleString() }}</template></el-table-column>
          <el-table-column label="占比" min-width="170"><template #default="{ row }"><el-progress :percentage="Math.round(row.pct)" :stroke-width="14" /></template></el-table-column>
        </el-table>
        <el-table v-else :data="dRows" border stripe size="small" height="calc(100vh - 190px)" empty-text="暂无数据">
          <el-table-column v-for="col in dCols" :key="col.label" :label="col.label" :width="col.width || undefined" :min-width="col.width ? undefined : 110" :align="col.money ? 'right' : 'left'" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="col.money">¥{{ Number(row[col.prop] || 0).toLocaleString() }}</span>
              <span v-else-if="col.date">{{ String(row[col.prop] || '').slice(0, 10) }}</span>
              <span v-else-if="col.fn">{{ col.fn(row) }}</span>
              <span v-else>{{ row[col.prop] }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div class="dcount">共 {{ dMode === 'breakdown' ? dTotalCount + ' ' + dCountLabel : dRows.length + ' 条' }}<span v-if="dSumLabel"> · {{ dSumLabel }} ¥{{ dTotalAmount.toLocaleString() }}</span></div>
      </div>
      <template #footer><el-button type="primary" @click="drawer = false">返回</el-button></template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => '¥' + Math.round(Number(v) || 0).toLocaleString()
const d = ref<any>({})
const loading = ref(false)
const storeId = ref('')
const auto = ref(false)
const asOf = computed(() => (d.value.asOf ? '更新于 ' + String(d.value.asOf).slice(0, 19).replace('T', ' ') : ''))
const maxLevel = computed(() => Math.max(1, ...((d.value.memberLevels || []).map((l: any) => Number(l.count) || 0))))
const pct = (n: number) => Math.round((Number(n) / maxLevel.value) * 100)

// —— 卡片下钻（UI/UX 一致于总部驾驶舱：点卡片就地弹抽屉看来源/明细，带「返回」+ Esc）——
const stores = ref<any[]>([])
const storeName = (id: any): string => { const s = stores.value.find((x: any) => (x.store_id || x.id) === id); return s ? s.name : (id != null ? '店#' + id : '—') }
const custMap = ref<Record<number, string>>({}) // 客户 id→名，在住房间抽屉里显示入住客户名
const custName = (id: any): string => custMap.value[id] || (id != null ? '客户#' + id : '—')
const drawer = ref(false); const dTitle = ref(''); const dLoading = ref(false); const dRows = ref<any[]>([])
const dMode = ref<'breakdown' | 'list'>('list')
const dDimLabel = ref(''); const dCountLabel = ref(''); const dAmountLabel = ref(''); const dSumLabel = ref(''); const dCols = ref<any[]>([])
const dHasAmount = computed(() => !!dAmountLabel.value)
const dTotalCount = computed(() => dRows.value.reduce((s, r) => s + (r.count || 0), 0))
const dTotalAmount = computed(() => dRows.value.reduce((s, r) => s + (r.amount || 0), 0))
function groupBy(rows: any[], dim: string, amountCol?: string) {
  const m = new Map<string, any>()
  for (const r of rows) { const k = String(r[dim] || '未分类'); if (!m.has(k)) m.set(k, { key: k, count: 0, amount: 0, pct: 0 }); const g = m.get(k); g.count++; if (amountCol) g.amount += Number(r[amountCol]) || 0 }
  const arr = [...m.values()]; const tA = arr.reduce((s, g) => s + g.amount, 0), tC = arr.reduce((s, g) => s + g.count, 0)
  for (const g of arr) g.pct = amountCol ? (tA ? g.amount / tA * 100 : 0) : (tC ? g.count / tC * 100 : 0)
  arr.sort((a, b) => amountCol ? b.amount - a.amount : b.count - a.count); return arr
}
const sid = () => storeId.value ? Number(storeId.value) : undefined
const monthStart = () => String(d.value.asOf || new Date().toISOString()).slice(0, 7) + '-01'
const asArr = (x: any) => Array.isArray(x) ? x : (x?.rows || [])
const C = (prop: string, label: string, width?: number, opt: any = {}) => ({ prop, label, width, ...opt })
const DRILL: Record<string, any> = {
  revenue: { title: '本月营收 · 支付方式构成', mode: 'breakdown', dim: 'pay_method', dimLabel: '支付方式', amountCol: 'paid_amount', amountLabel: '实收', countLabel: '单数', sumLabel: '本月实收合计', load: async () => asArr(await api().listOrders({ limit: 500, storeId: sid(), dateFrom: monthStart() })) },
  due: { title: '应收欠款 · 欠款订单', mode: 'list', cols: [C('order_no', '单号', 150), C('store_id', '门店', 118, { fn: (r: any) => storeName(r.store_id) }), C('due_amount', '欠款', 108, { money: true }), C('order_status', '状态', 86), C('created_at', '日期', 100, { date: true })], load: async () => asArr(await api().listOrders({ limit: 500, storeId: sid() })).filter((o: any) => Number(o.due_amount) > 0) },
  inHouse: { title: '在住客户 · 在住房间(占用房)', mode: 'list', cols: [C('room_no', '房号', 90), C('room_type', '房型', 120), C('floor', '楼层', 66), C('customer_id', '入住客户', 120, { fn: (r: any) => custName(r.customer_id) }), C('store_id', '门店', 110, { fn: (r: any) => storeName(r.store_id) })], load: async () => { const rooms = asArr(await api().listRooms({ storeId: sid() })).filter((x: any) => String(x.status) === '在住'); const cs = asArr(await api().listCustomers({ limit: 500, storeId: sid() })); const m: Record<number, string> = {}; for (const c of cs) m[c.customer_id] = c.name; custMap.value = m; return rooms } },
  customers: { title: '客户总数 · 按状态', mode: 'breakdown', dim: 'status', dimLabel: '客户状态', countLabel: '客户数', load: async () => asArr(await api().listCustomers({ limit: 500, storeId: sid() })) },
  rooms: { title: '房态 · 按状态', mode: 'breakdown', dim: 'status', dimLabel: '房间状态', countLabel: '间数', load: async () => asArr(await api().listRooms({ storeId: sid() })) },
  appts: { title: '今日预约', mode: 'list', cols: [C('project', '项目', 0), C('tech', '技师', 100), C('time', '时间', 150), C('status', '状态', 90)], load: async () => { const t = String(d.value.asOf || new Date().toISOString()).slice(0, 10); return asArr(await api().listAppointments({ storeId: sid() })).filter((a: any) => String(a.time || '').slice(0, 10) === t) } },
  nanny: { title: '月嫂在岗 · 派工中', mode: 'list', cols: [C('nanny_name', '月嫂', 100), C('customer_name', '客户', 100), C('status', '状态', 90), C('fee', '月费', 100, { money: true }), C('start_date', '起始', 110, { date: true })], load: async () => asArr(await api().listDispatch({ limit: 200, storeId: sid() })).filter((x: any) => ['已派工', '服务中'].includes(String(x.status))) },
  approvals: { title: '待审批 · 待审明细', mode: 'list', cols: [C('domain', '类型', 90), C('title', '标题', 0), C('amount', '金额', 110, { money: true }), C('created_at', '提交', 108, { date: true })], load: async () => asArr(await api().financePending()) },
}
async function openCard(key: string) {
  const cfg = DRILL[key]; if (!cfg) return
  dTitle.value = cfg.title; dMode.value = cfg.mode; dRows.value = []
  dDimLabel.value = cfg.dimLabel || ''; dCountLabel.value = cfg.countLabel || ''; dAmountLabel.value = cfg.amountLabel || ''; dSumLabel.value = cfg.sumLabel || ''; dCols.value = cfg.cols || []
  drawer.value = true; dLoading.value = true
  try { const recs = await cfg.load(); dRows.value = cfg.mode === 'breakdown' ? groupBy(recs, cfg.dim, cfg.amountCol) : recs }
  catch (e: any) { ElMessage.error('明细加载失败：' + (e?.message || '')) } finally { dLoading.value = false }
}

// 近14日营收趋势折线（零依赖 SVG）
const CW = 700, CH = 150
const pts = computed<any[]>(() => {
  const tr = d.value.trend || []
  if (!tr.length) return []
  const max = Math.max(1, ...tr.map((x: any) => Number(x.turnover) || 0))
  return tr.map((x: any, i: number) => ({ x: 10 + (i / Math.max(1, tr.length - 1)) * (CW - 20), y: CH - 18 - ((Number(x.turnover) || 0) / max) * (CH - 36), v: Number(x.turnover) || 0, date: x.date }))
})
const linePoints = computed(() => pts.value.map((p: any) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '))
const areaPoints = computed(() => pts.value.length ? `${pts.value[0].x.toFixed(1)},${CH - 18} ${linePoints.value} ${pts.value[pts.value.length - 1].x.toFixed(1)},${CH - 18}` : '')
const trendSum = computed(() => '¥' + Math.round((d.value.trend || []).reduce((s: number, x: any) => s + (Number(x.turnover) || 0), 0)).toLocaleString())
const maxTurnover = computed(() => Math.max(1, ...((d.value.storeRanking || []).map((s: any) => Number(s.turnover) || 0))))
const rbpct = (v: any) => Math.round((Number(v) / maxTurnover.value) * 100)

// U1e 营收预测：实际(近14日 ma7)+预测(未来7日)两段折线
const fc = ref<any>(null)
const fpts = computed<any[]>(() => {
  if (!fc.value) return []
  const act = (fc.value.actual || []).slice(-14).map((x: any) => ({ v: Number(x.turnover) || 0, date: x.date, forecast: false }))
  const fut = (fc.value.forecast || []).map((x: any) => ({ v: Number(x.forecast) || 0, date: x.date, forecast: true }))
  const all = [...act, ...fut]; if (!all.length) return []
  const max = Math.max(1, ...all.map((x) => x.v))
  return all.map((x, i) => ({ ...x, x: 10 + (i / Math.max(1, all.length - 1)) * (CW - 20), y: CH - 18 - (x.v / max) * (CH - 36) }))
})
const fActualLine = computed(() => fpts.value.filter((p: any) => !p.forecast).map((p: any) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '))
const fForecastLine = computed(() => {
  const a = fpts.value.filter((p: any) => !p.forecast); const f = fpts.value.filter((p: any) => p.forecast)
  const join = a.length ? [a[a.length - 1], ...f] : f  // 从最后一个实际点连出预测段
  return join.map((p: any) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
})

// —— 补充面板：次卡核销 / 库存预警 / 客户生命周期（复用现有接口，随门店联动）——
const cardStats = ref<any>(null)
const invAlerts = ref<any>(null)
const custByStage = ref<any[]>([])
const custTotal = ref(0)
const barPct = (part: any, whole: any): string => { const w = Number(whole) || 0; return (w ? Math.max(1, Math.round((Number(part) || 0) / w * 100)) : 0) + '%' }
const STAGE: Array<{ key: string; cls: string; match: (s: string) => boolean }> = [
  { key: '意向', cls: 'st-lead', match: (s) => /^意向/.test(s) },
  { key: '签约在途', cls: 'st-sign', match: (s) => /签合同|订房/.test(s) },
  { key: '在住', cls: 'st-live', match: (s) => s === '已入住' },
  { key: '已离所', cls: 'st-left', match: (s) => /已退房/.test(s) },
  { key: '流失/散客', cls: 'st-lost', match: (s) => /流失|散客/.test(s) },
]
const maxStage = computed(() => Math.max(1, ...custByStage.value.map((s: any) => Number(s.count) || 0)))
const stagePct = (n: number): string => Math.max(2, Math.round((Number(n) / maxStage.value) * 100)) + '%'

async function loadExtras() {
  const f = { storeId: storeId.value ? Number(storeId.value) : undefined }
  const [cv, ia, cs] = await Promise.all([
    api().cardValueStats(f).catch(() => null),
    api().inventoryAlerts(f).catch(() => null),
    api().listCustomers({ limit: 500, ...f }).catch(() => []),
  ])
  cardStats.value = cv
  invAlerts.value = ia
  const arr = Array.isArray(cs) ? cs : ((cs as any)?.rows || [])
  custTotal.value = arr.length
  custByStage.value = STAGE.map((st) => ({ key: st.key, cls: st.cls, count: arr.filter((c: any) => st.match(String(c.status || ''))).length }))
}

let timer: any = null
async function load() {
  loading.value = true
  try { d.value = await api().getCockpit({ storeId: storeId.value ? Number(storeId.value) : undefined }) || {} }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
  try { fc.value = await api().getRevenueForecast({ storeId: storeId.value ? Number(storeId.value) : undefined, historyDays: 90, forecastDays: 7 }) }
  catch { fc.value = null }
  loadExtras().catch(() => { /* 补充面板失败不阻断主大屏 */ })
}
function tick() { if (auto.value) load() }
onMounted(async () => { try { stores.value = (await api().listStores()) || [] } catch { /* 门店名映射失败不阻断 */ } load(); timer = setInterval(tick, 30000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.screen { padding: 4px 2px; }
.hd { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
.ttl { font-size: 22px; font-weight: 700; letter-spacing: 1px; }
.ttl .sub { font-size: 13px; font-weight: 400; color: var(--el-text-color-secondary); margin-left: 8px; }
.ops { display: flex; align-items: center; gap: 10px; }
.asof { font-size: 12px; color: var(--el-text-color-secondary); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 14px; }
.kpi { background: var(--el-bg-color-overlay); border: 1px solid var(--el-border-color-lighter); border-radius: var(--r-sm); padding: 14px 16px; }
.kpi.hero { grid-column: span 2; background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%); color: #fff; border: none; }
.kpi .t { font-size: 13px; color: var(--el-text-color-secondary); }
.kpi.hero .t { color: rgba(255,255,255,.85); }
.kpi .v { font-size: 28px; font-weight: 700; margin-top: 6px; line-height: 1.1; }
.kpi .v.warn { color: var(--el-color-danger); }
.kpi .v .slash { font-size: 16px; color: var(--el-text-color-secondary); font-weight: 400; }
.kpi .x { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; }
.kpi.hero .x { color: rgba(255,255,255,.8); }
.kpi.clk { cursor: pointer; transition: box-shadow .18s, transform .18s; }
.kpi.clk:hover { box-shadow: 0 10px 26px -16px rgba(0,0,0,.4); transform: translateY(-2px); }
.kpi .arr { font-size: 13px; opacity: .5; margin-left: 5px; }
.kpi.clk:hover .arr { opacity: 1; }
.dcount { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 10px; text-align: right; }
.panes { display: grid; grid-template-columns: 1.4fr 1fr; gap: 12px; }
.pane { min-width: 0; }
.levels { display: flex; flex-direction: column; gap: 10px; }
.lv { display: flex; align-items: center; gap: 10px; }
.lv .ln { width: 48px; font-size: 13px; }
.lv .bar { flex: 1; height: 14px; background: var(--el-fill-color-light); border-radius: 7px; overflow: hidden; }
.lv .fill { height: 100%; background: var(--el-color-primary); border-radius: 7px; }
.lv .lc { width: 44px; text-align: right; font-size: 13px; font-weight: 600; }
.trend-card { margin-bottom: 14px; }
.fline { stroke: var(--el-color-warning); stroke-dasharray: 5 4; }
.fdot { fill: var(--el-color-warning); }
.forecast-note { font-size: 12px; }
.flegend { display: flex; gap: 16px; margin-top: 6px; font-size: 12px; color: var(--el-text-color-secondary); }
.flegend .lg { display: flex; align-items: center; gap: 4px; }
.flegend .sw { width: 14px; height: 3px; display: inline-block; border-radius: 2px; }
.flegend .sw.actual { background: var(--el-color-primary); }
.flegend .sw.pred { background: var(--el-color-warning); }
.muted { color: var(--el-text-color-secondary); font-size: 12px; font-weight: 400; }
.chart { width: 100%; height: 150px; display: block; }
.chart .area { fill: var(--el-color-primary); opacity: .12; }
.chart .line { fill: none; stroke: var(--el-color-primary); stroke-width: 2; }
.chart .dot { fill: var(--el-color-primary); }
.xaxis { display: flex; justify-content: space-between; font-size: 11px; color: var(--el-text-color-secondary); margin-top: 2px; }
.rbar { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.rfill { height: 100%; background: var(--el-color-primary); border-radius: 5px; }

/* —— 补充三面板 —— */
.panes3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 14px; }
.cclist, .ivlist, .lclist { display: flex; flex-direction: column; gap: 9px; }
.ccrow { border-bottom: 1px solid var(--el-border-color-lighter); padding-bottom: 8px; }
.ccrow:last-child { border-bottom: 0; padding-bottom: 0; }
.cchead { display: flex; align-items: baseline; gap: 8px; font-size: 12px; }
.cchead .ccn { font-weight: 600; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cchead .ccc { color: var(--el-text-color-secondary); }
.cchead .ccr { color: #B8945A; font-weight: 600; }
.ccbar { display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 5px; background: var(--el-fill-color-light); }
.ccbar i { height: 100%; }
.ccbar i.rec { background: var(--el-color-success); }
.ccbar i.rem { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.ivrow { display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 8px; font-size: 13px; padding: 5px 0; border-bottom: 1px dashed var(--el-border-color-lighter); }
.ivrow:last-child { border-bottom: 0; }
.ivrow.oos { background: rgba(245, 108, 108, .06); border-radius: 4px; }
.ivrow .ivn { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ivrow .ivq { color: var(--el-text-color-secondary); font-size: 12px; }
.ivrow .ivq b { color: var(--el-color-warning); }
.ivrow .ivq b.danger { color: var(--el-color-danger); }
.ivrow .ivg { color: var(--el-text-color-secondary); font-size: 11px; min-width: 44px; text-align: right; }
.lcrow { display: grid; grid-template-columns: 66px 1fr auto; align-items: center; gap: 10px; font-size: 13px; }
.lcrow .lcn { color: var(--el-text-color-regular); }
.lcrow .lcbar { height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.lcrow .lcbar i { display: block; height: 100%; }
.lcrow .lcc { font-weight: 700; min-width: 30px; text-align: right; }
.st-lead { background: linear-gradient(90deg, #d8c39a, #b89a63); }
.st-sign { background: linear-gradient(90deg, #cbb184, #9c7838); }
.st-live { background: var(--el-color-success); }
.st-left { background: linear-gradient(90deg, #b7bcc4, #8a8f96); }
.st-lost { background: var(--el-color-info); }
@media (max-width: 1100px) { .panes3 { grid-template-columns: 1fr; } }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
