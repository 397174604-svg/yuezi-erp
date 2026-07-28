<template>
  <div class="rec">
    <!-- 头部 + 筛选 -->
    <div class="bar">
      <h2 class="ph">交易对账</h2>
      <el-form :inline="true" size="small" class="filters">
        <el-form-item label="起"><el-date-picker v-model="f.from" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:138px" /></el-form-item>
        <el-form-item label="止"><el-date-picker v-model="f.to" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:138px" /></el-form-item>
        <el-form-item label="门店"><el-input v-model="f.storeId" style="width:84px" placeholder="全部" clearable /></el-form-item>
        <el-form-item><el-button type="primary" :loading="loading" @click="load(true)">对账</el-button></el-form-item>
      </el-form>
    </div>

    <!-- 概览条：轧平率为锚 + 关键金额 -->
    <el-card v-if="totals" shadow="never" class="summary">
      <div class="sm-health">
        <div class="hn"><span class="num" :class="rateClass">{{ balancedRate }}</span><span class="unit">%</span></div>
        <div class="hb"><i :class="rateClass" :style="{ width: balancedRate + '%' }" /></div>
        <div class="hl">轧平率 · {{ balancedDays }}/{{ days.length }} 天</div>
      </div>
      <div class="sm-metrics">
        <div class="m"><div class="ml">网关已收</div><div class="mv">{{ money(totals.gatewayPaid) }}</div></div>
        <div class="m"><div class="ml">账面收入</div><div class="mv">{{ money(totals.bookIncome) }}</div></div>
        <div class="m"><div class="ml">区间差额</div><div class="mv" :class="totals.balanced ? 'ok' : 'bad'">{{ money(totals.diff) }}</div></div>
        <div class="m"><div class="ml">差异天数</div><div class="mv" :class="diffDays ? 'bad' : 'ok'">{{ diffDays }}<span class="sub"> / {{ days.length }}</span></div></div>
        <div class="m"><div class="ml">异常支付单</div><div class="mv" :class="exceptions.length ? 'warn' : 'ok'">{{ exceptions.length }}</div></div>
      </div>
    </el-card>

    <p class="note">网关已收(已支付支付单) ↔ 账面已审核收入 逐日轧差。<b>差额 ≠ 0</b> 仅为「需人工核对」信号（账面含现金等非网关来源）；右侧 <b>异常支付单</b> 才是确定性问题。</p>

    <div class="split" v-loading="loading">
      <!-- 左：日终对账明细（趋势迷你图 + 只看差异 + 差额可排序，取代原趋势/TOP 两块） -->
      <el-card shadow="never" class="pane">
        <template #header>
          <div class="ph-row">
            <div><b>日终对账明细</b><span class="muted">逐日轧差</span></div>
            <div class="tgl"><span>只看差异</span><el-switch v-model="showDiffOnly" size="small" style="--el-switch-on-color: var(--el-color-danger)" /></div>
          </div>
        </template>
        <div v-if="trend.bars.length" class="spark">
          <svg :viewBox="`0 0 ${trend.W} ${trend.H}`" preserveAspectRatio="none">
            <line :x1="trend.x0" :x2="trend.x1" :y1="trend.y1" :y2="trend.y1" class="axis" />
            <rect v-for="(b, i) in trend.bars" :key="i" :x="b.x" :y="b.y" :width="b.w" :height="b.h" :class="b.bad ? 'rbad' : 'rok'"><title>{{ b.date }} · 差额 {{ money(b.diff) }}</title></rect>
          </svg>
          <span class="spark-lbl">差额趋势 · 红=差异日</span>
        </div>
        <el-table :data="shownDays" border stripe size="small" empty-text="暂无数据" max-height="460" :default-sort="{ prop: 'date', order: 'descending' }">
          <el-table-column prop="date" label="日期" width="104" sortable />
          <el-table-column label="网关已收" min-width="140" align="right"><template #default="{ row }">{{ money(row.gatewayPaid) }} <span class="muted">({{ row.gatewayCount }})</span></template></el-table-column>
          <el-table-column label="账面收入" min-width="110" align="right"><template #default="{ row }">{{ money(row.bookIncome) }}</template></el-table-column>
          <el-table-column prop="diff" label="差额" min-width="118" align="right" sortable :sort-method="diffSort"><template #default="{ row }"><span :class="row.balanced ? 'ok' : 'bad'">{{ money(row.diff) }}</span></template></el-table-column>
          <el-table-column label="状态" width="76" align="center"><template #default="{ row }"><el-tag :type="row.balanced ? 'success' : 'danger'" effect="dark" size="small">{{ row.balanced ? '轧平' : '差异' }}</el-tag></template></el-table-column>
        </el-table>
      </el-card>

      <!-- 右：异常支付单 —— 确定性问题，提升为焦点面板 -->
      <el-card shadow="never" class="pane exc">
        <template #header>
          <div class="ph-row">
            <div><b>异常支付单</b><span class="muted">确定性问题 · 需处理</span></div>
            <el-tag v-if="exceptions.length" type="danger" effect="dark" size="small">{{ exceptions.length }} 笔</el-tag>
          </div>
        </template>
        <div v-if="exceptions.length" class="exc-list">
          <div v-for="e in exceptions" :key="e.payNo" class="exc-item">
            <div class="ei-top"><span class="pno">{{ e.payNo }}</span><span class="amt">{{ money(e.amount) }}</span></div>
            <div class="ei-meta">门店 {{ e.storeId }} · {{ e.notifyAt }}</div>
            <div class="ei-tags"><el-tag v-for="i in e.issues" :key="i" type="warning" effect="dark" size="small">{{ i }}</el-tag></div>
          </div>
        </div>
        <el-empty v-else description="无异常 · 全部核对通过" :image-size="60" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => (Number(v) < 0 ? '-¥' : '¥') + Math.abs(Number(v) || 0).toLocaleString()
const f = ref({ from: '', to: '', storeId: '' })
const totals = ref<any>(null)
const days = ref<any[]>([])
const exceptions = ref<any[]>([])
const loading = ref(false)
const showDiffOnly = ref(false)

const balancedDays = computed(() => days.value.filter((d) => d.balanced).length)
const diffDays = computed(() => days.value.length - balancedDays.value)
const balancedRate = computed(() => (days.value.length ? Math.round((balancedDays.value / days.value.length) * 100) : 0))
const rateClass = computed(() => (balancedRate.value >= 80 ? 'ok' : balancedRate.value >= 50 ? 'warn' : 'bad'))
const shownDays = computed(() => (showDiffOnly.value ? days.value.filter((d) => !d.balanced) : days.value))
const diffSort = (a: any, b: any) => Math.abs(Number(a.diff) || 0) - Math.abs(Number(b.diff) || 0) // 差额列按 |差额| 排序 → 取代独立「差异 TOP」

// 迷你趋势几何（时间升序，一柱一天，柱高=|差额|/区间max）；slim 版内嵌明细卡头下
const trend = computed(() => {
  const arr = days.value.slice().reverse()
  const W = 560, H = 46, x0 = 6, x1 = 554, y0 = 6, y1 = 40
  const n = arr.length
  const maxAbs = Math.max(1, ...arr.map((d) => Math.abs(Number(d.diff) || 0)))
  const slot = n ? (x1 - x0) / n : 0
  const bw = Math.max(3, Math.min(18, slot * 0.68))
  const bars = arr.map((d, i) => {
    const xc = n <= 1 ? (x0 + x1) / 2 : x0 + slot * (i + 0.5)
    const h = (Math.abs(Number(d.diff) || 0) / maxAbs) * (y1 - y0)
    return { x: xc - bw / 2, y: y1 - Math.max(1, h), w: bw, h: Math.max(1, h), bad: !d.balanced, date: d.date, diff: d.diff }
  })
  return { W, H, x0, x1, y1, bars }
})

// manual=true 时（点「对账」按钮）给成功反馈；onMounted 自动加载不弹提示，避免每次进页面都 toast
async function load(manual = false) {
  loading.value = true
  const filter: any = { from: f.value.from || undefined, to: f.value.to || undefined, storeId: f.value.storeId ? Number(f.value.storeId) : undefined }
  try {
    const r: any = await api().reconcileGatewayVsBook(filter)
    totals.value = r?.totals || null; days.value = r?.days || []
    const ex: any = await api().reconcileExceptions(filter)
    exceptions.value = ex?.exceptions || []
    if (manual) {
      const dd = days.value.filter((d) => !d.balanced).length
      ElMessage.success(`对账完成 · ${days.value.length} 天，${dd ? dd + ' 天有差异、' : '全部轧平，'}${exceptions.value.length} 笔异常支付单`)
    }
  } catch (e: any) { ElMessage.error('对账失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.rec { padding-bottom: 8px; }
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 12px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; font-family: var(--font-cn-serif); font-weight: 600; }
.filters { margin: 0; }
.filters :deep(.el-form-item) { margin-bottom: 0; }

/* —— 概览条 —— */
.summary { margin-bottom: 12px; }
.summary :deep(.el-card__body) { display: flex; align-items: center; gap: 8px; padding: 16px 22px; flex-wrap: wrap; }
.sm-health { display: flex; flex-direction: column; gap: 6px; min-width: 172px; }
.sm-health .hn { line-height: 1; }
.sm-health .hn .num { font-size: 40px; font-weight: 700; font-variant-numeric: tabular-nums; }
.sm-health .hn .unit { font-size: 16px; font-weight: 600; margin-left: 3px; color: var(--el-text-color-secondary); }
.sm-health .hb { height: 8px; border-radius: 4px; background: var(--el-fill-color); overflow: hidden; }
.sm-health .hb i { display: block; height: 100%; border-radius: 4px; transition: width .4s ease; }
.sm-health .hb i.ok { background: var(--el-color-success); }
.sm-health .hb i.warn { background: var(--el-color-warning); }
.sm-health .hb i.bad { background: var(--el-color-danger); }
.sm-health .hl { font-size: 12px; color: var(--el-text-color-secondary); }
.sm-metrics { display: flex; gap: 40px; flex-wrap: wrap; margin-left: 26px; padding-left: 30px; border-left: 1px solid var(--el-border-color-lighter); }
.sm-metrics .m .ml { font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 5px; }
.sm-metrics .m .mv { font-size: 21px; font-weight: 600; font-variant-numeric: tabular-nums; }
.sm-metrics .m .mv .sub { font-size: 13px; color: var(--el-text-color-secondary); font-weight: 400; }

.note { margin: 0 0 14px; font-size: 12px; color: var(--el-text-color-secondary); line-height: 1.6; }
.note b { color: var(--el-text-color-regular); font-weight: 600; }

/* —— 主体两栏 —— */
.split { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(300px, 1fr); gap: 14px; align-items: start; }
.pane { min-width: 0; }
.pane :deep(.el-card__header) { padding: 10px 14px; }
.ph-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; margin-left: 8px; font-weight: 400; }
.tgl { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--el-text-color-secondary); }

/* 迷你趋势条 */
.spark { position: relative; margin: 2px 2px 12px; }
.spark svg { width: 100%; height: 44px; display: block; }
.spark .axis { stroke: var(--el-border-color-lighter); stroke-width: 1; }
.spark .rok { fill: var(--el-color-success-light-5); }
.spark .rbad { fill: var(--el-color-danger); }
.spark-lbl { position: absolute; top: -2px; right: 2px; font-size: 11px; color: var(--el-text-color-placeholder); }

/* 异常单卡列表 */
.exc :deep(.el-card__body) { padding: 10px; }
.exc-list { display: flex; flex-direction: column; gap: 8px; max-height: 520px; overflow-y: auto; }
.exc-item { border: 1px solid var(--el-border-color-lighter); border-left: 3px solid var(--el-color-warning); border-radius: 7px; padding: 10px 12px; background: var(--el-color-warning-light-9); }
.ei-top { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.ei-top .pno { font-family: var(--el-font-family-mono, ui-monospace, monospace); font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); }
.ei-top .amt { font-size: 16px; font-weight: 700; font-variant-numeric: tabular-nums; }
.ei-meta { font-size: 12px; color: var(--el-text-color-secondary); margin: 3px 0 7px; }
.ei-tags { display: flex; flex-wrap: wrap; gap: 4px; }

.ok { color: var(--el-color-success); }
.warn { color: var(--el-color-warning); }
.bad { color: var(--el-color-danger); }
@media (max-width: 1100px) { .split { grid-template-columns: 1fr; } .sm-metrics { margin-left: 0; padding-left: 0; border-left: 0; } }
</style>
