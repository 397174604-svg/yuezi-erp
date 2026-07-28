<template>
  <div>
    <div class="bar">
      <h2 class="ph">数据报表</h2>
      <div class="filters">
        <el-select v-model="storeId" placeholder="全部门店" clearable style="width: 150px" @change="loadAll">
          <el-option v-for="s in stores" :key="s.store_id" :label="s.name" :value="s.store_id" />
        </el-select>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width: 240px" @change="loadAll" />
      </div>
    </div>

    <el-tabs v-model="tab" @tab-change="ensure">
      <!-- 门店对比 -->
      <el-tab-pane label="门店对比" name="store">
        <el-table :data="storeRows" v-loading="loading.store" border stripe empty-text="暂无门店数据">
          <el-table-column type="index" label="#" width="56" />
          <el-table-column prop="storeName" label="门店" min-width="130" />
          <el-table-column label="实收" width="140" align="right"><template #default="{ row }">{{ money(row.turnover) }}</template></el-table-column>
          <el-table-column label="GMV" width="140" align="right"><template #default="{ row }">{{ money(row.gmv) }}</template></el-table-column>
          <el-table-column label="欠款" width="130" align="right"><template #default="{ row }">{{ money(row.due) }}</template></el-table-column>
          <el-table-column prop="orders" label="订单数" width="100" align="center" />
          <el-table-column prop="customers" label="成交客户" width="100" align="center" />
        </el-table>
      </el-tab-pane>

      <!-- 经营数据 · 月相版 -->
      <el-tab-pane label="经营数据" name="biz">
        <div v-loading="loading.biz" class="bizc">
          <!-- 夜空营收趋势 -->
          <div class="sky">
            <div class="sky-h"><div class="st-t"><span class="moon">☾</span>营收趋势</div><div class="st-s">实收 · GMV / 按日</div></div>
            <div class="charts-scroll">
              <svg class="skysvg" :viewBox="`0 0 ${VB.w} ${VB.h}`" preserveAspectRatio="xMidYMid meet" role="img" aria-label="营收趋势">
                <defs>
                  <linearGradient id="cfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EAD3A0" stop-opacity=".6" /><stop offset="1" stop-color="#EAD3A0" stop-opacity=".04" /></linearGradient>
                  <radialGradient id="cmoon" cx="35%" cy="35%" r="70%"><stop offset="0" stop-color="#FBEFCF" /><stop offset="1" stop-color="#D9B978" /></radialGradient>
                </defs>
                <g stroke="rgba(234,211,160,.13)"><line v-for="(gy, i) in trendGeo.grid" :key="i" :x1="VB.x0" :y1="gy" :x2="VB.x1" :y2="gy" /></g>
                <path :d="trendGeo.area" fill="url(#cfill)" />
                <path :d="trendGeo.line" fill="none" stroke="#EAD3A0" stroke-width="2.5" />
                <path :d="trendGeo.gmv" fill="none" stroke="#C2A063" stroke-width="1.4" stroke-dasharray="5 4" opacity=".85" />
                <template v-if="trendGeo.last">
                  <g :transform="`translate(${trendGeo.last.x},${trendGeo.last.y})`"><circle r="15" fill="url(#cmoon)" /><circle cx="6" cy="-3" r="14" fill="#2A2620" /></g>
                  <text :x="trendGeo.last.x - 22" :y="trendGeo.last.y - 12" text-anchor="end" class="skyval">{{ moneyW(trendGeo.last.val) }}</text>
                </template>
                <text v-for="(x, i) in trendGeo.xs" :key="i" :x="x.x" :y="VB.h - 12" text-anchor="middle" class="skyx">{{ x.label }}</text>
              </svg>
            </div>
          </div>

          <!-- 5 月相环 KPI -->
          <div class="gauges">
            <div class="gz" v-for="g in gauges" :key="g.label">
              <svg viewBox="0 0 72 72" width="64" height="64">
                <g transform="rotate(-90 36 36)" fill="none" stroke-width="6">
                  <circle cx="36" cy="36" r="30" stroke="#F0E6D2" />
                  <circle cx="36" cy="36" r="30" :stroke="g.color" stroke-linecap="round" :stroke-dasharray="`${(g.ratio * 188.5).toFixed(0)} 999`" />
                </g>
                <text x="36" y="41" text-anchor="middle" class="gzicon" :fill="g.color">☾</text>
              </svg>
              <div class="gz-v" :style="{ color: g.color }">{{ g.value }}</div>
              <div class="gz-l">{{ g.label }}</div>
              <div class="gz-s">{{ g.sub }}</div>
            </div>
          </div>

          <!-- 门店对比 -->
          <div class="panel" v-if="storeBars.length">
            <div class="stt">门店对比 <small>各店实收</small></div>
            <div class="storebars">
              <div class="sb" v-for="s in storeBars" :key="s.name">
                <span class="sbk">{{ s.name }}</span>
                <div class="sbtrack"><i class="sbfill" :style="{ width: s.w }" /></div>
                <span class="sbv num">{{ money(s.turnover) }}</span>
                <span class="sbo">{{ s.orders }} 单</span>
              </div>
            </div>
          </div>

          <!-- 收入构成 + 支付方式 -->
          <div class="grid2">
            <div class="panel">
              <div class="stt">收入构成 <small>按业务板块</small></div>
              <div class="donut-wrap">
                <div class="donut-c">
                  <svg viewBox="0 0 160 160" width="128" height="128">
                    <g transform="rotate(-90 80 80)" fill="none" stroke-width="20">
                      <circle v-for="s in domainSegs" :key="s.k" cx="80" cy="80" r="60" :stroke="s.color" :stroke-dasharray="`${s.len} 999`" :stroke-dashoffset="s.off" />
                    </g>
                  </svg>
                  <div class="ctr"><b class="num">{{ domainSegs[0] ? domainSegs[0].pct : 0 }}%</b><span>{{ domainSegs[0] ? domainSegs[0].k : '暂无' }}</span></div>
                </div>
                <div class="leg">
                  <div class="row" v-for="s in domainSegs" :key="s.k"><i class="dot" :style="{ background: s.color }" />{{ s.k }}<span class="amt num">{{ money(s.amount) }}</span></div>
                  <div class="row" v-if="!domainSegs.length" style="color:var(--ink-3)">暂无数据</div>
                </div>
              </div>
            </div>
            <div class="panel">
              <div class="stt">支付方式 <small>实收占比</small></div>
              <div class="pbar">
                <div class="r" v-for="p in payRows" :key="p.k"><span class="k">{{ p.k }}</span><div class="track"><i class="fill" :style="{ width: p.w }" /></div><span class="v num">{{ p.pct }}%</span></div>
                <div v-if="!payRows.length" style="color:var(--ink-3);font-size:13px">暂无数据</div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 会员数据 -->
      <el-tab-pane label="会员数据" name="member">
        <div v-loading="loading.member" class="dist">
          <div class="dcol">
            <div class="dh">会员等级分布（共 {{ member.total }} 人）</div>
            <div v-for="x in member.byLevel" :key="x.key" class="drow">
              <span class="dk">{{ x.key }}</span>
              <div class="dbar"><div class="dfill" :style="{ width: pct(x.count, member.total) }" /></div>
              <span class="dv">{{ x.count }}</span>
            </div>
          </div>
          <div class="dcol">
            <div class="dh">客户来源分析</div>
            <div v-for="x in member.bySource" :key="x.key" class="drow">
              <span class="dk">{{ x.key }}</span>
              <div class="dbar"><div class="dfill src" :style="{ width: pct(x.count, member.total) }" /></div>
              <span class="dv">{{ x.count }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 员工业绩 -->
      <el-tab-pane label="员工业绩" name="staff">
        <el-table :data="staffRows" v-loading="loading.staff" border stripe empty-text="暂无业绩数据">
          <el-table-column type="index" label="#" width="56" />
          <el-table-column prop="executor" label="执行人" min-width="110" />
          <el-table-column label="业绩" width="120" align="right"><template #default="{ row }">{{ money(row.perf) }}</template></el-table-column>
          <el-table-column label="销售额" width="130" align="right"><template #default="{ row }">{{ money(row.sales) }}</template></el-table-column>
          <el-table-column label="手工费" width="120" align="right"><template #default="{ row }">{{ money(row.handFee) }}</template></el-table-column>
          <el-table-column prop="qty" label="服务次数" width="100" align="center" />
          <el-table-column prop="lines" label="开单项数" width="100" align="center" />
        </el-table>
      </el-tab-pane>

      <!-- 品项销量 -->
      <el-tab-pane label="品项销量" name="item">
        <el-table :data="itemRows" v-loading="loading.item" border stripe empty-text="暂无品项数据">
          <el-table-column type="index" label="#" width="56" />
          <el-table-column prop="name" label="品项" min-width="160" />
          <el-table-column prop="qty" label="销量" width="100" align="center" />
          <el-table-column label="销售额" width="140" align="right"><template #default="{ row }">{{ money(row.sales) }}</template></el-table-column>
          <el-table-column prop="orders" label="订单数" width="100" align="center" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const tab = ref('biz')
const stores = ref<any[]>([])
const storeId = ref<number | null>(null)
const dateRange = ref<string[] | null>(null)
const loading = reactive({ biz: false, member: false, staff: false, item: false, store: false })

const biz = ref<any>({})
const bizCharts = ref<any>({ trend: [], byDomain: [], byPay: [], byStatus: [] })
const bizMargin = ref<any>(null)
const bizStores = ref<any[]>([])
const VB = { w: 1000, h: 244, x0: 56, x1: 944, y0: 44, y1: 200 }
const member = ref<any>({ total: 0, byLevel: [], bySource: [] })
const staffRows = ref<any[]>([])
const itemRows = ref<any[]>([])
const storeRows = ref<any[]>([])

function money(v: any): string { return v == null ? '—' : '¥' + Number(v).toLocaleString() }
function pct(c: number, total: number): string { return total ? Math.max(4, Math.round((c / total) * 100)) + '%' : '0%' }
function filt() { return { storeId: storeId.value || undefined, from: dateRange.value?.[0] || undefined, to: dateRange.value?.[1] || undefined } }

function moneyW(v: any): string { const n = Number(v) || 0; return n >= 10000 ? '¥' + (n / 10000).toFixed(1) + '万' : '¥' + Math.round(n).toLocaleString() }
function moneyK(v: any): string { const n = Number(v) || 0; if (n >= 1e6) return '¥' + (n / 1e6).toFixed(2) + 'M'; if (n >= 1e3) return '¥' + (n / 1e3).toFixed(0) + 'K'; return '¥' + Math.round(n) }
const DCOL = ['#8C6A36', '#B8945A', '#C2A063', '#E7D4AC', '#EDE0C4', '#D8C39A']
const SCOL: Record<string, string> = { '已支付': '#8C6A36', '已完成': '#9C7838', '已发货': '#B8945A', '部分支付': '#C2A063', '未支付': '#D8C39A', '待支付': '#D8C39A', '已退款': '#AE6E56', '已取消': '#C9BBA0' }

// 营收趋势 SVG 几何：从 trend 动态算 area/line/gmv 路径 + 收尾点 + x 轴标签（点数自适应）
const trendGeo = computed(() => {
  const t: any[] = bizCharts.value.trend || []
  const grid = [VB.y0, (VB.y0 + VB.y1) / 2, VB.y1]
  if (!t.length) return { area: '', line: '', gmv: '', last: null as any, xs: [] as any[], grid }
  const pts = t.length === 1 ? [t[0], t[0]] : t
  const n = pts.length
  const max = Math.max(1, ...pts.map((p) => Number(p.gmv) || 0))
  const X = (i: number) => VB.x0 + i * (VB.x1 - VB.x0) / (n - 1)
  const Y = (v: number) => VB.y1 - (Number(v) / max) * (VB.y1 - VB.y0)
  const line = 'M' + pts.map((p, i) => `${X(i).toFixed(1)},${Y(p.turnover).toFixed(1)}`).join(' L')
  const area = line + ` L${X(n - 1).toFixed(1)},${VB.y1} L${X(0).toFixed(1)},${VB.y1} Z`
  const gmv = 'M' + pts.map((p, i) => `${X(i).toFixed(1)},${Y(p.gmv).toFixed(1)}`).join(' L')
  const lab = (p: any) => { const a = (p.ym || '').split('-'); return a.length >= 3 ? Number(a[1]) + '/' + Number(a[2]) : Number(a[1] || 0) + '月' }
  const step = Math.max(1, Math.ceil(t.length / 6))
  const xs = t.length === 1
    ? [{ x: (VB.x0 + VB.x1) / 2, label: lab(t[0]) }]
    : t.map((p, i) => ({ x: X(i), label: lab(p), keep: i % step === 0 || i === t.length - 1 })).filter((o) => o.keep)
  return { area, line, gmv, last: { x: X(n - 1), y: Y(pts[n - 1].turnover), val: pts[n - 1].turnover }, xs, grid }
})

// 5 枚月相环：金环按真实占比填充，中心值 + 副标（收款率/欠款率/客单价/人均）
const gauges = computed(() => {
  const b = biz.value || {}
  const gmv = Number(b.gmv) || 0, turn = Number(b.turnover) || 0, due = Number(b.due) || 0
  const oc = Number(b.orderCount) || 0, cc = Number(b.customerCount) || 0
  const st: any[] = bizCharts.value.byStatus || []
  const stotal = st.reduce((a, x) => a + x.count, 0) || 1
  const paidRate = (st.find((x) => x.k === '已支付')?.count || 0) / stotal
  const collect = gmv ? turn / gmv : 0, dueR = gmv ? due / gmv : 0
  const mg = bizMargin.value
  const hasCost = !!(mg && mg.cogs > 0) // 有真实成本才显真毛利率；演示成本≈0 时兜底「待成本」，不撒 100% 的谎
  return [
    { label: '实收', value: moneyK(turn), ratio: Math.min(1, collect), sub: '收款率 ' + Math.round(collect * 100) + '%', color: '#8C6A36' },
    { label: 'GMV', value: moneyK(gmv), ratio: 1, sub: '总流水', color: '#B8945A' },
    { label: '毛利率', value: hasCost ? mg.marginRate + '%' : '待成本', ratio: hasCost ? Math.min(1, mg.marginRate / 100) : 0, sub: hasCost ? '营收 − 成本' : '演示未铺成本价', color: '#9C7838' },
    { label: '欠款', value: moneyK(due), ratio: Math.min(1, dueR), sub: '占 GMV ' + Math.round(dueR * 100) + '%', color: '#AE6E56' },
    { label: '订单数', value: oc + ' 单', ratio: paidRate, sub: '客单价 ' + moneyK(oc ? turn / oc : 0), color: '#8C6A36' },
    { label: '客户数', value: cc + ' 人', ratio: 1, sub: '人均 ' + moneyK(cc ? turn / cc : 0), color: '#C2A063' },
  ]
})

// 收入构成环 / 支付方式条 / 订单状态分段
const donutC = 2 * Math.PI * 60
const domainSegs = computed(() => {
  const arr: any[] = bizCharts.value.byDomain || []
  const total = arr.reduce((a, x) => a + x.amount, 0) || 1
  let cum = 0
  return arr.map((x, i) => { const len = x.amount / total * donutC; const s = { k: x.k, amount: x.amount, pct: Math.round(x.amount / total * 100), color: DCOL[i % DCOL.length], len: +len.toFixed(1), off: +(-cum).toFixed(1) }; cum += len; return s })
})
const payRows = computed(() => {
  const arr: any[] = bizCharts.value.byPay || []
  const total = arr.reduce((a, x) => a + x.amount, 0) || 1
  return arr.map((x) => ({ k: x.k, pct: Math.round(x.amount / total * 100), w: Math.max(3, Math.round(x.amount / total * 100)) + '%' }))
})
const statusTotal = computed(() => (bizCharts.value.byStatus || []).reduce((a: number, x: any) => a + x.count, 0))
const statusSegs = computed(() => {
  const arr: any[] = bizCharts.value.byStatus || []
  const total = statusTotal.value || 1
  return arr.map((x) => ({ k: x.k, count: x.count, w: Math.max(2, x.count / total * 100) + '%', color: SCOL[x.k] || '#C9BBA0' }))
})
// 门店对比：各店实收横向条（取前 6，按实收降序）
const storeBars = computed(() => {
  const arr = (bizStores.value || []).slice().sort((a, b) => (b.turnover || 0) - (a.turnover || 0)).slice(0, 6)
  const max = Math.max(1, ...arr.map((x) => Number(x.turnover) || 0))
  return arr.map((x) => ({ name: x.storeName || ('门店' + (x.storeId ?? '')), turnover: Number(x.turnover) || 0, orders: x.orders || 0, w: Math.max(3, Math.round((Number(x.turnover) || 0) / max * 100)) + '%' }))
})

async function loadBiz() {
  loading.biz = true
  try {
    const [b, c, gm, st] = await Promise.all([
      api().getBusinessStats(filt()), api().getBusinessCharts(filt()),
      api().getGrossMargin(filt()).catch(() => null), api().getStoreCompare({ from: filt().from, to: filt().to }).catch(() => []),
    ])
    biz.value = b || {}
    bizCharts.value = c || { trend: [], byDomain: [], byPay: [], byStatus: [] }
    bizMargin.value = gm?.totals ?? null
    bizStores.value = st || []
  } catch (e: any) { ElMessage.error('经营数据失败：' + (e?.message || '')) } finally { loading.biz = false }
}
async function loadMember() { loading.member = true; try { member.value = await api().getMemberStats(filt()) || { total: 0, byLevel: [], bySource: [] } } catch (e: any) { ElMessage.error('会员数据失败：' + (e?.message || '')) } finally { loading.member = false } }
async function loadStaff() { loading.staff = true; try { staffRows.value = await api().getStaffPerf(filt()) || [] } catch (e: any) { ElMessage.error('员工业绩失败：' + (e?.message || '')) } finally { loading.staff = false } }
async function loadItem() { loading.item = true; try { itemRows.value = await api().getItemSales(filt()) || [] } catch (e: any) { ElMessage.error('品项销量失败：' + (e?.message || '')) } finally { loading.item = false } }
async function loadStore() { loading.store = true; try { storeRows.value = await api().getStoreCompare({ from: filt().from, to: filt().to }) || [] } catch (e: any) { ElMessage.error('门店对比失败：' + (e?.message || '')) } finally { loading.store = false } }

function ensure(name: string) {
  if (name === 'member' && !member.value.byLevel.length) loadMember()
  if (name === 'staff' && !staffRows.value.length) loadStaff()
  if (name === 'item' && !itemRows.value.length) loadItem()
  if (name === 'store' && !storeRows.value.length) loadStore()
}
function loadAll() { loadBiz(); loadMember(); loadStaff(); loadItem(); loadStore() }

onMounted(async () => {
  try { stores.value = (await api().listStores()) || [] } catch { /* ignore */ }
  loadAll()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.filters { display: flex; gap: 10px; }
.kpi { background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-md); padding: 20px; text-align: center; }
.kpi .kv { font-size: 26px; color: var(--gold-deep); font-weight: 600; }
.kpi .kl { font-size: 13px; color: var(--ink-3); margin-top: 4px; }
.dist { display: flex; gap: 30px; }
.dcol { flex: 1; }
.dh { font-family: var(--font-cn-serif); font-weight: 600; margin-bottom: 14px; padding-left: 10px; border-left: 3px solid var(--gold); }
.drow { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.drow .dk { width: 90px; font-size: 13px; color: var(--ink-2); text-align: right; }
.drow .dbar { flex: 1; height: 16px; background: var(--ivory-2); border-radius: var(--r-sm); overflow: hidden; }
.drow .dfill { height: 100%; background: var(--foil); }
.drow .dfill.src { background: linear-gradient(90deg, #cdbfa0, #8c7a55); }
.drow .dv { width: 44px; font-family: var(--font-display); font-weight: 600; color: var(--gold-deep); }

/* —— 经营数据 · 月相版 —— */
.bizc { display: flex; flex-direction: column; gap: 16px; }
.num { font-variant-numeric: tabular-nums; }
.charts-scroll { overflow-x: auto; }
.sky { background: radial-gradient(120% 150% at 82% 0%, #3B342A, #2A2620 62%); border-radius: var(--r-md); padding: 18px 22px 6px; }
.sky-h { display: flex; align-items: baseline; justify-content: space-between; }
.sky-h .st-t { font-family: var(--font-cn-serif); font-weight: 600; font-size: 16px; color: #EAD3A0; }
.sky-h .st-t .moon { margin-right: 8px; }
.sky-h .st-s { font-size: 12px; color: #B9A87E; letter-spacing: .04em; }
.skysvg { width: 100%; min-width: 560px; height: auto; display: block; margin-top: 4px; }
.skyval { font-family: var(--font-display); font-size: 15px; fill: #EAD3A0; font-weight: 600; }
.skyx { font-size: 12px; fill: #B9A87E; }
.gauges { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; }
.gz { border: 1px solid var(--hair); border-radius: var(--r-md); padding: 14px 10px; text-align: center; background: var(--paper); }
.gz svg { display: block; margin: 0 auto; }
.gzicon { font-size: 15px; }
.gz-v { font-family: var(--font-cn-serif); font-weight: 600; font-size: 19px; margin-top: 6px; }
.gz-l { font-size: 12px; color: var(--ink-3); letter-spacing: .1em; margin-top: 2px; }
.gz-s { font-size: 11px; color: var(--ink-2); margin-top: 3px; }
.panel { border: 1px solid var(--hair); border-radius: var(--r-md); padding: 16px 18px; background: var(--paper); }
.stt { font-family: var(--font-cn-serif); font-weight: 600; font-size: 15px; padding-left: 10px; border-left: 3px solid var(--gold); margin-bottom: 12px; }
.stt small { font-weight: 400; font-size: 12px; color: var(--ink-3); margin-left: 8px; }
.seg { display: flex; height: 20px; border-radius: 6px; overflow: hidden; }
.seg i { height: 100%; }
.seg-leg { display: flex; flex-wrap: wrap; gap: 9px 16px; margin-top: 12px; }
.seg-leg span { font-size: 12px; color: var(--ink-2); display: flex; align-items: center; gap: 6px; }
.seg-leg .d { width: 9px; height: 9px; border-radius: 2px; }
.grid2 { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }
.donut-wrap { display: flex; align-items: center; gap: 20px; }
.donut-c { position: relative; width: 128px; height: 128px; flex: none; }
.donut-c .ctr { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.donut-c .ctr b { font-family: var(--font-cn-serif); font-size: 20px; color: var(--gold-deep); }
.donut-c .ctr span { font-size: 11px; color: var(--ink-3); }
.leg { display: flex; flex-direction: column; gap: 9px; flex: 1; }
.leg .row { display: flex; align-items: center; gap: 9px; font-size: 13px; color: var(--ink-2); }
.leg .dot { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.leg .amt { margin-left: auto; font-family: var(--font-cn-serif); font-weight: 600; color: var(--ink); }
.pbar { display: flex; flex-direction: column; gap: 13px; }
.pbar .r { display: grid; grid-template-columns: 76px 1fr 48px; align-items: center; gap: 12px; }
.pbar .k { font-size: 13px; color: var(--ink-2); text-align: right; }
.pbar .track { height: 14px; background: var(--ivory-2); border-radius: 7px; overflow: hidden; }
.pbar .fill { height: 100%; background: linear-gradient(90deg, #E9D4A4, #C2A063 60%, #9C7838); }
.pbar .v { font-family: var(--font-cn-serif); font-weight: 600; font-size: 14px; color: var(--gold-deep); text-align: right; }
.storebars { display: flex; flex-direction: column; gap: 12px; }
.sb { display: grid; grid-template-columns: 120px 1fr auto auto; align-items: center; gap: 12px; }
.sb .sbk { font-size: 13px; color: var(--ink-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sb .sbtrack { height: 14px; background: var(--ivory-2); border-radius: 7px; overflow: hidden; }
.sb .sbfill { display: block; height: 100%; background: linear-gradient(90deg, #E9D4A4, #C2A063 60%, #9C7838); }
.sb .sbv { font-family: var(--font-cn-serif); font-weight: 600; font-size: 13px; color: var(--gold-deep); text-align: right; min-width: 92px; }
.sb .sbo { font-size: 12px; color: var(--ink-3); min-width: 44px; text-align: right; }
@media (max-width: 1100px) { .gauges { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .gauges { grid-template-columns: repeat(2, 1fr); } .grid2 { grid-template-columns: 1fr; } .sb { grid-template-columns: 90px 1fr auto; } .sb .sbo { display: none; } }
</style>
