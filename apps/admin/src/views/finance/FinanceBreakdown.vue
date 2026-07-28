<template>
  <div>
    <div class="bar">
      <h2 class="ph">收支分类分析</h2>
      <div class="filters">
        <el-input v-model="from" size="small" placeholder="起 YYYY-MM-DD" style="width:140px" clearable />
        <el-input v-model="to" size="small" placeholder="止 YYYY-MM-DD" style="width:140px" clearable />
        <el-button type="primary" size="small" @click="load">查询</el-button>
      </div>
    </div>

    <el-row :gutter="14" class="mb">
      <el-col :span="6"><el-card shadow="never" class="stat inc"><div class="lbl">总收入</div><div class="val">¥{{ num(d.totalIncome) }}</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never" class="stat exp"><div class="lbl">总支出</div><div class="val">¥{{ num(d.totalExpense) }}</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never" class="stat" :class="d.balance >= 0 ? 'inc' : 'exp'"><div class="lbl">结余</div><div class="val">¥{{ num(d.balance) }}</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never" class="stat"><div class="lbl">结余率</div><div class="val rate">{{ ratio }}<span class="unit">%</span></div></el-card></el-col>
    </el-row>

    <!-- 收支趋势 -->
    <el-card shadow="never" class="mb" v-loading="loading">
      <div class="sub">收支趋势 · 按日<span class="hint">绿=收入 / 红=支出（仅已审核）</span></div>
      <div v-if="tg.pts.length" class="tw">
        <svg :viewBox="`0 0 ${tg.W} ${tg.H}`" class="tchart" preserveAspectRatio="none">
          <line v-for="gy in tg.grid" :key="'g'+gy.label" :x1="tg.x0" :x2="tg.x1" :y1="gy.y" :y2="gy.y" class="grid" />
          <text v-for="gy in tg.grid" :key="'l'+gy.label" :x="tg.x0-6" :y="gy.y+3" class="ytick">{{ gy.label }}</text>
          <path :d="tg.incArea" class="incArea" />
          <polyline :points="tg.incLine" class="incLine" />
          <polyline :points="tg.expLine" class="expLine" />
          <text v-for="(l,i) in tg.labels" :key="'x'+i" :x="l.x" :y="tg.y1+15" class="xtick">{{ l.d }}</text>
        </svg>
        <div class="legend"><span class="lg"><i class="sw inc" />收入</span><span class="lg"><i class="sw exp" />支出</span></div>
      </div>
      <el-empty v-else description="所选区间暂无已审核收支" :image-size="56" />
    </el-card>

    <!-- 收入构成 / 支出构成 -->
    <div class="panes mb" v-loading="loading">
      <el-card shadow="never" class="pane">
        <template #header><b>收入构成</b><span class="hint">按类别 · 占总收入</span></template>
        <div v-for="c in incomeCats" :key="c.category" class="crow">
          <span class="ck">{{ c.category }}</span>
          <div class="cbar"><i class="inc" :style="{ width: pctOf(c.income, d.totalIncome) }" /></div>
          <span class="cv g">¥{{ num(c.income) }}</span><span class="cp">{{ share(c.income, d.totalIncome) }}%</span>
        </div>
        <el-empty v-if="!incomeCats.length" description="暂无收入" :image-size="48" />
      </el-card>
      <el-card shadow="never" class="pane">
        <template #header><b>支出构成</b><span class="hint">按类别 · 占总支出</span></template>
        <div v-for="c in expenseCats" :key="c.category" class="crow">
          <span class="ck">{{ c.category }}</span>
          <div class="cbar"><i class="exp" :style="{ width: pctOf(c.expense, d.totalExpense) }" /></div>
          <span class="cv r">¥{{ num(c.expense) }}</span><span class="cp">{{ share(c.expense, d.totalExpense) }}%</span>
        </div>
        <el-empty v-if="!expenseCats.length" description="暂无支出" :image-size="48" />
      </el-card>
    </div>

    <el-card shadow="never">
      <div class="sub">按类别 · 轧差台账<span class="hint">仅计已审核 · 收入−支出=净结余</span></div>
      <el-table :data="d.categories" v-loading="loading" border stripe size="small" empty-text="暂无已审核收支" max-height="420">
        <el-table-column prop="category" label="类别" min-width="130" />
        <el-table-column label="收入" width="140" align="right"><template #default="{ row }"><span class="g">¥{{ num(row.income) }}</span></template></el-table-column>
        <el-table-column label="支出" width="140" align="right"><template #default="{ row }"><span class="r">¥{{ num(row.expense) }}</span></template></el-table-column>
        <el-table-column label="结余" width="150" align="right"><template #default="{ row }"><b :class="row.net >= 0 ? 'g' : 'r'">¥{{ num(row.net) }}</b></template></el-table-column>
        <el-table-column label="占比(净额)" min-width="200"><template #default="{ row }">
          <el-progress :percentage="pct(row.net)" :status="row.net >= 0 ? 'success' : 'exception'" :stroke-width="12" />
        </template></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const num = (v: any) => Math.round(Number(v || 0)).toLocaleString()
const from = ref(''); const to = ref('')
const d = ref<any>({ categories: [], totalIncome: 0, totalExpense: 0, balance: 0, trend: [] })
const loading = ref(false)
let maxAbs = 1

function pct(net: number) { return Math.min(100, Math.round(Math.abs(Number(net) || 0) / maxAbs * 100)) }
function pctOf(part: any, whole: any): string { const w = Number(whole) || 0; return (w ? Math.max(2, Math.round((Number(part) || 0) / w * 100)) : 0) + '%' }
function share(part: any, whole: any): string { const w = Number(whole) || 0; return w ? (Math.round((Number(part) || 0) / w * 1000) / 10).toString() : '0' }

const ratio = computed(() => { const i = Number(d.value.totalIncome) || 0; return i ? Math.round(Number(d.value.balance) / i * 1000) / 10 : 0 })
const incomeCats = computed(() => (d.value.categories || []).filter((c: any) => Number(c.income) > 0).slice().sort((a: any, b: any) => b.income - a.income))
const expenseCats = computed(() => (d.value.categories || []).filter((c: any) => Number(c.expense) > 0).slice().sort((a: any, b: any) => b.expense - a.expense))

// 收支趋势几何（收入绿面+线，支出红线）
const tg = computed(() => {
  const t = (d.value.trend || []) as any[]
  const W = 1000, H = 200, x0 = 52, x1 = 992, y0 = 14, y1 = 168
  const maxV = Math.max(1, ...t.map((r) => Math.max(Number(r.income) || 0, Number(r.expense) || 0)))
  const n = t.length
  const xOf = (i: number) => n <= 1 ? (x0 + x1) / 2 : x0 + (x1 - x0) * i / (n - 1)
  const yOf = (v: number) => y1 - (y1 - y0) * (v / maxV)
  const inc = t.map((r, i) => `${xOf(i).toFixed(1)},${yOf(Number(r.income) || 0).toFixed(1)}`)
  const exp = t.map((r, i) => `${xOf(i).toFixed(1)},${yOf(Number(r.expense) || 0).toFixed(1)}`)
  const incLine = inc.join(' '); const expLine = exp.join(' ')
  const incArea = inc.length ? `M${xOf(0).toFixed(1)},${y1} L${inc.join(' L')} L${xOf(n - 1).toFixed(1)},${y1} Z` : ''
  const kNum = (v: number) => v >= 10000 ? Math.round(v / 1000) + 'k' : String(Math.round(v))
  const grid = [1, 0.5, 0].map((f) => ({ y: yOf(maxV * f), label: kNum(maxV * f) }))
  const labIdx = n <= 1 ? [0] : [0, Math.floor(n / 2), n - 1]
  const labels = labIdx.map((i) => ({ x: xOf(i), d: (t[i]?.date || '').slice(5) }))
  return { W, H, x0, x1, y1, pts: t, incLine, expLine, incArea, grid, labels }
})

async function load() {
  loading.value = true
  try {
    const r: any = await api().financeBreakdown({ from: from.value || undefined, to: to.value || undefined })
    d.value = r || { categories: [], totalIncome: 0, totalExpense: 0, balance: 0, trend: [] }
    maxAbs = Math.max(1, ...d.value.categories.map((c: any) => Math.abs(Number(c.net) || 0)))
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.filters { display: flex; gap: 8px; align-items: center; }
.mb { margin-bottom: 14px; }
.stat { text-align: center; }
.stat .lbl { color: var(--ink-3, #999); font-size: 13px; }
.stat .val { font-size: 24px; font-weight: 700; margin-top: 6px; }
.stat .val .unit { font-size: 14px; font-weight: 500; }
.stat .val.rate { color: #B8945A; }
.stat.inc .val { color: var(--ok, #67c23a); }
.stat.exp .val { color: var(--danger, #f56c6c); }
.sub { font-weight: 600; margin-bottom: 8px; }
.hint { font-weight: 400; font-size: 12px; color: var(--ink-3, #999); margin-left: 10px; }
.g { color: var(--ok, #67c23a); }
.r { color: var(--danger, #f56c6c); }

.tw { width: 100%; overflow-x: auto; }
.tchart { width: 100%; height: 210px; display: block; }
.tchart .grid { stroke: var(--el-border-color-lighter); stroke-width: 1; }
.tchart .ytick, .tchart .xtick { fill: var(--ink-3, #999); font-size: 11px; }
.tchart .ytick { text-anchor: end; }
.tchart .xtick { text-anchor: middle; }
.tchart .incArea { fill: rgba(103, 194, 58, .12); }
.tchart .incLine { fill: none; stroke: #67c23a; stroke-width: 2; }
.tchart .expLine { fill: none; stroke: #f56c6c; stroke-width: 2; }
.legend { display: flex; gap: 16px; margin-top: 6px; font-size: 12px; color: var(--ink-3, #999); }
.legend .lg { display: inline-flex; align-items: center; gap: 5px; }
.legend .sw { width: 14px; height: 3px; border-radius: 2px; display: inline-block; }
.legend .sw.inc { background: #67c23a; }
.legend .sw.exp { background: #f56c6c; }

.panes { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pane { min-width: 0; }
.crow { display: grid; grid-template-columns: 84px 1fr auto auto; align-items: center; gap: 10px; margin-bottom: 9px; font-size: 13px; }
.crow .ck { color: var(--el-text-color-regular); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crow .cbar { height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.crow .cbar i { display: block; height: 100%; }
.crow .cbar i.inc { background: linear-gradient(90deg, #a7d98a, #67c23a); }
.crow .cbar i.exp { background: linear-gradient(90deg, #f3b6b6, #f56c6c); }
.crow .cv { font-weight: 600; min-width: 82px; text-align: right; }
.crow .cp { color: var(--ink-3, #999); font-size: 12px; min-width: 40px; text-align: right; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
