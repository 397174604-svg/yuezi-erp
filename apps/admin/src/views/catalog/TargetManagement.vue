<template>
  <div>
    <div class="bar">
      <h2 class="ph">目标管理</h2>
      <div class="qbar">
        <el-input v-model="qPeriod" size="small" placeholder="按周期筛 YYYY-MM" style="width:150px" @keyup.enter="load" clearable @clear="load" />
        <el-button size="small" type="primary" @click="load">查询</el-button>
      </div>
    </div>

    <el-card shadow="never" class="card">
      <div class="sub">设定目标</div>
      <el-form :inline="true" :model="form" size="small">
        <el-form-item label="目标类型"><el-select v-model="form.targetType" style="width:140px"><el-option v-for="t in targetTypes" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="周期"><el-select v-model="form.periodType" style="width:80px" @change="syncPeriod"><el-option label="月" value="月" /><el-option label="年" value="年" /></el-select></el-form-item>
        <el-form-item label=""><el-input v-model="form.period" :placeholder="form.periodType === '月' ? 'YYYY-MM' : 'YYYY'" style="width:120px" /></el-form-item>
        <el-form-item label="门店ID"><el-input v-model="form.storeId" style="width:80px" placeholder="可选" /></el-form-item>
        <el-form-item label="员工ID" v-if="form.targetType.startsWith('员工')"><el-input v-model="form.staffId" style="width:90px" placeholder="可选" /></el-form-item>
        <el-form-item label="目标值"><el-input v-model="form.targetValue" style="width:130px" placeholder="金额/数量" /></el-form-item>
        <el-form-item><el-button type="primary" :loading="saving" @click="submit">设定</el-button></el-form-item>
      </el-form>
    </el-card>

    <!-- KPI 概览（可下钻）—— 全部由 targetProgress 客户端派生 -->
    <div class="cards" v-loading="loading">
      <el-card shadow="never" class="kpi drill" @click="openDrill('total')">
        <div class="t">目标总数 <span class="go">明细 ›</span></div>
        <div class="v">{{ sum.total }}</div>
        <div class="x">自动核算 {{ sum.autoN }} · 手工 {{ sum.manualN }}</div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('reached')">
        <div class="t">已达标 <span class="go">明细 ›</span></div>
        <div class="v ok">{{ sum.reached }}<span class="unit">/{{ sum.autoN }}</span></div>
        <div class="x">达成率 ≥ 100% 的门店目标</div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('rate')">
        <div class="t">平均达成率 <span class="go">明细 ›</span></div>
        <div class="v" :class="rateCls(sum.avgRate)">{{ sum.avgRate == null ? '—' : sum.avgRate + '%' }}</div>
        <div class="ratebar"><div class="ratefill" :class="rateCls(sum.avgRate)" :style="{ width: Math.min(100, sum.avgRate || 0) + '%' }" /></div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('behind')">
        <div class="t">预警 · 落后 <span class="go">明细 ›</span></div>
        <div class="v warn">{{ sum.behind }}</div>
        <div class="x">达成率 &lt; 80%，需重点跟进</div>
      </el-card>
    </div>

    <div class="panes" v-loading="loading">
      <!-- 左：门店目标达成 · 进度台账（自动核算，有实时实绩） -->
      <el-card shadow="never" class="pane">
        <template #header><b>门店目标达成 · 进度台账</b><span class="sub">实绩由订单流实时核算 · 目标为管理层设定</span></template>
        <div v-for="r in autoRows" :key="r.targetId" class="prow">
          <div class="phd">
            <span class="pname">{{ storeLabel(r.storeId) }} · {{ r.targetType }}</span>
            <span class="pper">{{ r.period }}</span>
            <span class="prate" :class="rateCls(r.rate)">{{ r.rate == null ? '—' : r.rate + '%' }}</span>
          </div>
          <div class="pbar"><i :class="rateCls(r.rate)" :style="{ width: Math.min(100, r.rate || 0) + '%' }" /></div>
          <div class="pft"><span>实绩 {{ fmt(r.actual, r.targetType) }}</span><span class="tgt">目标 {{ fmt(r.target, r.targetType) }}</span></div>
        </div>
        <el-empty v-if="!autoRows.length" description="暂无可自动核算的门店目标" :image-size="56" />
      </el-card>

      <!-- 右：达成分布 + 员工目标（手工核算） -->
      <el-card shadow="never" class="pane">
        <template #header><b>达成分布 · 员工目标</b><span class="sub">自动核算门店目标的达成结构</span></template>
        <div class="dist">
          <div class="distbar">
            <i v-for="b in bands" :key="b.key" :class="b.key" :style="{ width: distPct(b.key) }" :title="b.label + ' ' + bandCount(b.key)" />
          </div>
          <div class="distleg">
            <span v-for="b in bands" :key="b.key" class="lg"><i :class="b.key" /> {{ b.label }} <b>{{ bandCount(b.key) }}</b></span>
          </div>
        </div>
        <div class="mtitle">员工业绩目标 · 手工核算 <span class="sub2">（无自动实绩源，录得分后按手工登记）</span></div>
        <div v-for="r in manualRows" :key="r.targetId" class="mrow">
          <span class="mk">{{ staffLabel(r.staffId, r.storeId) }}</span>
          <span class="mp">{{ r.period }}</span>
          <span class="mv">目标 {{ fmt(r.target, r.targetType) }}</span>
          <el-tag size="small" type="info" effect="plain">手工</el-tag>
        </div>
        <el-empty v-if="!manualRows.length" description="暂无员工级目标" :image-size="48" />
      </el-card>
    </div>

    <!-- 目标达成明细表 -->
    <el-card shadow="never" class="card">
      <div class="sub">目标达成明细
        <span class="hint">门店业绩/客数/客次自动核算；其余类型与员工级暂按手工核算。</span>
      </div>
      <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无目标" :default-sort="{ prop: 'rate', order: 'ascending' }">
        <el-table-column prop="targetType" label="目标类型" min-width="110" />
        <el-table-column prop="period" label="区间" width="94" />
        <el-table-column label="门店/员工" width="120"><template #default="{ row }">{{ row.staffId ? staffLabel(row.staffId, row.storeId) : storeLabel(row.storeId) }}</template></el-table-column>
        <el-table-column label="目标值" width="120" align="right"><template #default="{ row }">{{ fmt(row.target, row.targetType) }}</template></el-table-column>
        <el-table-column label="实绩" width="120" align="right"><template #default="{ row }">{{ row.autoCalc ? fmt(row.actual, row.targetType) : '—' }}</template></el-table-column>
        <el-table-column label="达成率" min-width="190" prop="rate" sortable><template #default="{ row }">
          <el-progress v-if="row.autoCalc && row.rate != null" :percentage="Math.min(Number(row.rate), 100)" :format="() => row.rate + '%'" :status="row.rate >= 100 ? 'success' : (row.rate >= 80 ? '' : 'warning')" />
          <el-tag v-else size="small" type="info">手工核算</el-tag>
        </template></el-table-column>
      </el-table>
    </el-card>

    <!-- 卡片下钻 · 目标透视 -->
    <el-drawer v-model="drill.open" :title="`目标透视 · ${drillTitle}`" size="470px">
      <div class="drill-body">
        <div class="dhead">{{ drillHead }}</div>
        <div class="dsec">
          <div class="dh">{{ drillListTitle }}</div>
          <div class="dbar" v-for="r in drillList" :key="r.targetId">
            <span class="dk">{{ (r.staffId ? staffLabel(r.staffId, r.storeId) : storeLabel(r.storeId)) }}·{{ r.targetType }}·{{ r.period }}</span>
            <div class="dt"><i :class="rateCls(r.rate)" :style="{ width: Math.min(100, r.rate || 0) + '%' }" /></div>
            <span class="dv" :class="rateCls(r.rate)">{{ r.rate == null ? '手工' : r.rate + '%' }}</span>
          </div>
          <div v-if="!drillList.length" class="empty">暂无数据</div>
        </div>
        <div class="dsec" v-if="drill.metric === 'total'">
          <div class="dh">按目标类型</div>
          <div class="dbar" v-for="g in byType" :key="g.type"><span class="dk">{{ g.type }}</span><div class="dt"><i :style="{ width: pctOf(g.count, maxTypeCount) }" /></div><span class="dv">{{ g.count }} 条</span></div>
        </div>
        <div class="dnote">{{ drillNote }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const targetTypes = ['门店业绩', '门店耗卡', '门店客流', '门店客次', '门店客数', '门店项目数', '员工业绩', '员工耗卡', '员工客流', '员工客次', '员工项目数']
const form = ref({ targetType: '门店业绩', periodType: '月', period: '', storeId: '', staffId: '', targetValue: '' })
const saving = ref(false)
const rows = ref<any[]>([])
const loading = ref(false)
const qPeriod = ref('')

// 金额类=业绩(¥)；其余=数量。门店业绩/员工业绩/门店耗卡/员工耗卡 视为金额。
const isMoney = (type: string) => /业绩|耗卡/.test(String(type || ''))
function fmt(v: any, type: string) { const n = Number(v) || 0; return (isMoney(type) ? '¥' : '') + n.toLocaleString() }
function rateCls(rate: any) { if (rate == null) return 'manual'; const r = Number(rate); return r >= 100 ? 'ok' : (r >= 80 ? 'near' : 'warn') }
function pctOf(part: any, whole: any): string { const w = Number(whole) || 0; return (w ? Math.max(3, Math.round((Number(part) || 0) / w * 100)) : 0) + '%' }

function storeLabel(id: any) { return id ? '店#' + id : '全租户' }
function staffLabel(staffId: any, storeId: any) { return '员工#' + staffId + (storeId ? '·店' + storeId : '') }

const autoRows = computed(() => rows.value.filter(r => r.autoCalc).slice().sort((a, b) => (a.rate ?? 999) - (b.rate ?? 999)))
const manualRows = computed(() => rows.value.filter(r => !r.autoCalc))

const sum = computed(() => {
  const auto = autoRows.value
  const rated = auto.filter(r => r.rate != null)
  const avg = rated.length ? Math.round(rated.reduce((s, r) => s + Number(r.rate), 0) / rated.length * 10) / 10 : null
  return {
    total: rows.value.length,
    autoN: auto.length,
    manualN: manualRows.value.length,
    reached: rated.filter(r => Number(r.rate) >= 100).length,
    behind: rated.filter(r => Number(r.rate) < 80).length,
    avgRate: avg,
  }
})

// 达成分布段
const bands = [
  { key: 'ok', label: '达标 ≥100%' },
  { key: 'near', label: '接近 80–100%' },
  { key: 'warn', label: '落后 <80%' },
]
function bandCount(key: string) { return autoRows.value.filter(r => r.rate != null && rateCls(r.rate) === key).length }
function distPct(key: string) { const tot = autoRows.value.filter(r => r.rate != null).length; return (tot ? Math.round(bandCount(key) / tot * 100) : 0) + '%' }

const byType = computed(() => {
  const m: Record<string, number> = {}
  for (const r of rows.value) m[r.targetType] = (m[r.targetType] || 0) + 1
  return Object.entries(m).map(([type, count]) => ({ type, count })).sort((a, b) => b.count - a.count)
})
const maxTypeCount = computed(() => Math.max(1, ...byType.value.map(g => g.count)))

// —— 卡片下钻 · 目标透视 ——
const drill = ref<{ open: boolean; metric: string }>({ open: false, metric: 'total' })
function openDrill(metric: string) { drill.value = { open: true, metric } }
const DRILL: Record<string, { title: string; listTitle: string; note: string }> = {
  total: { title: '全部目标', listTitle: '门店目标达成（自动核算，按达成率）', note: '目标为管理层设定值；门店业绩/客数/客次的实绩由后端复用 statsService.business 从订单流实时核算，达成率非写死。' },
  reached: { title: '已达标目标', listTitle: '达成率 ≥ 100% 的目标（超额在前）', note: '达标=实绩≥目标。可沉淀为高绩效样板，复制到落后门店/员工。' },
  rate: { title: '平均达成率', listTitle: '全部自动核算目标（按达成率升序）', note: '平均达成率仅统计可自动核算的门店级目标；员工级目标无实时实绩源，不计入均值。' },
  behind: { title: '落后目标预警', listTitle: '达成率 < 80% 的目标（最差在前）', note: '落后目标建议优先干预：核对目标合理性、加投营销/排班、复盘转化漏斗。' },
}
const drillTitle = computed(() => DRILL[drill.value.metric]?.title || '')
const drillListTitle = computed(() => DRILL[drill.value.metric]?.listTitle || '')
const drillNote = computed(() => DRILL[drill.value.metric]?.note || '')
const drillList = computed(() => {
  const m = drill.value.metric
  if (m === 'reached') return autoRows.value.filter(r => r.rate != null && Number(r.rate) >= 100).slice().sort((a, b) => Number(b.rate) - Number(a.rate))
  if (m === 'behind') return autoRows.value.filter(r => r.rate != null && Number(r.rate) < 80).slice().sort((a, b) => Number(a.rate) - Number(b.rate))
  if (m === 'rate') return autoRows.value.filter(r => r.rate != null)
  return rows.value.slice().sort((a, b) => (a.rate ?? 999) - (b.rate ?? 999)) // total
})
const drillHead = computed(() => {
  const s = sum.value; const m = drill.value.metric
  if (m === 'reached') return `已达标 ${s.reached} / ${s.autoN} 个自动核算目标`
  if (m === 'behind') return `落后 ${s.behind} 个 · 平均达成率 ${s.avgRate == null ? '—' : s.avgRate + '%'}`
  if (m === 'rate') return `平均达成率 ${s.avgRate == null ? '—' : s.avgRate + '%'} · 覆盖 ${s.autoN} 个门店目标`
  return `共 ${s.total} 个目标 · 自动核算 ${s.autoN} · 手工 ${s.manualN}`
})

function syncPeriod() { form.value.period = '' }

async function submit() {
  if (!form.value.period || !Number(form.value.targetValue)) { ElMessage.warning('周期、目标值必填'); return }
  saving.value = true
  try {
    const input: any = { targetType: form.value.targetType, periodType: form.value.periodType, period: form.value.period, targetValue: Number(form.value.targetValue) }
    if (form.value.storeId) input.storeId = Number(form.value.storeId)
    if (form.value.targetType.startsWith('员工') && form.value.staffId) input.staffId = Number(form.value.staffId)
    await api().upsertTarget(input)
    ElMessage.success('目标已设定'); load()
  } catch (e: any) { ElMessage.error('设定失败：' + (e?.message || '')) }
  finally { saving.value = false }
}

async function load() {
  loading.value = true
  try { rows.value = (await api().targetProgress({ period: qPeriod.value || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.qbar { display: flex; gap: 8px; align-items: center; }
.card { margin-bottom: 14px; }
.sub { font-weight: 600; margin-bottom: 8px; }
.hint { font-weight: 400; font-size: 12px; color: var(--el-text-color-secondary); margin-left: 10px; }

.cards { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.kpi { flex: 1; min-width: 168px; text-align: center; }
.kpi .t { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .v { font-size: 26px; font-weight: 700; margin-top: 4px; }
.kpi .v .unit { font-size: 14px; font-weight: 500; color: var(--el-text-color-secondary); }
.kpi .v.ok { color: var(--el-color-success); }
.kpi .v.near { color: #B8945A; }
.kpi .v.warn { color: var(--el-color-warning); }
.kpi .x { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; }
.ratebar { height: 8px; background: var(--el-fill-color-light); border-radius: 4px; overflow: hidden; margin-top: 10px; }
.ratefill { height: 100%; border-radius: 4px; background: var(--el-color-primary); }
.ratefill.ok { background: var(--el-color-success); }
.ratefill.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.ratefill.warn { background: var(--el-color-warning); }

.kpi.drill { cursor: pointer; transition: box-shadow .15s, transform .15s; }
.kpi.drill:hover { box-shadow: 0 8px 22px -14px rgba(140, 106, 54, .55); transform: translateY(-1px); }
.kpi .t .go { font-size: 11px; color: var(--el-color-primary); font-weight: 400; opacity: 0; transition: opacity .15s; }
.kpi.drill:hover .t .go { opacity: 1; }

.panes { display: grid; grid-template-columns: 1.15fr 1fr; gap: 14px; margin-bottom: 14px; }
.pane .sub { font-size: 12px; color: var(--el-text-color-secondary); margin-left: 10px; font-weight: 400; }
.prow { padding: 9px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.prow:last-child { border-bottom: 0; }
.phd { display: flex; align-items: baseline; gap: 10px; font-size: 13px; }
.phd .pname { font-weight: 600; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.phd .pper { color: var(--el-text-color-secondary); font-size: 12px; }
.phd .prate { font-weight: 700; font-size: 13px; }
.pbar { height: 12px; border-radius: 6px; overflow: hidden; margin: 6px 0; background: var(--el-fill-color-light); }
.pbar i { display: block; height: 100%; background: var(--el-color-primary); }
.pbar i.ok { background: var(--el-color-success); }
.pbar i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.pbar i.warn { background: var(--el-color-warning); }
.pft { display: flex; justify-content: space-between; font-size: 12px; color: var(--el-text-color-secondary); }
.pft .tgt { color: var(--el-text-color-primary); }
.ok { color: var(--el-color-success); }
.near { color: #B8945A; }
.warn { color: var(--el-color-warning); }
.manual { color: var(--el-text-color-secondary); }

.dist { margin-bottom: 14px; }
.distbar { display: flex; height: 16px; border-radius: 8px; overflow: hidden; background: var(--el-fill-color-light); }
.distbar i { height: 100%; }
.distbar i.ok { background: var(--el-color-success); }
.distbar i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.distbar i.warn { background: var(--el-color-warning); }
.distleg { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; font-size: 12px; color: var(--el-text-color-secondary); }
.distleg .lg { display: inline-flex; align-items: center; gap: 5px; }
.distleg .lg i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.distleg .lg i.ok { background: var(--el-color-success); }
.distleg .lg i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.distleg .lg i.warn { background: var(--el-color-warning); }
.mtitle { font-weight: 600; font-size: 13px; margin: 6px 0 8px; }
.mtitle .sub2 { font-weight: 400; font-size: 12px; color: var(--el-text-color-secondary); }
.mrow { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px dashed var(--el-border-color-lighter); font-size: 13px; }
.mrow:last-child { border-bottom: 0; }
.mrow .mk { font-weight: 600; }
.mrow .mp { color: var(--el-text-color-secondary); font-size: 12px; }
.mrow .mv { flex: 1; color: var(--el-text-color-primary); }

.drill-body { display: flex; flex-direction: column; gap: 18px; }
.dhead { font-size: 13px; font-weight: 600; color: var(--el-color-primary); background: var(--el-fill-color-lighter); border-radius: 8px; padding: 8px 12px; }
.dsec .dh { font-weight: 600; font-size: 14px; margin-bottom: 10px; padding-left: 9px; border-left: 3px solid var(--el-color-primary); }
.dbar { display: grid; grid-template-columns: 160px 1fr auto; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 12px; }
.dbar .dk { color: var(--el-text-color-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dbar .dt { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.dbar .dt i { display: block; height: 100%; background: linear-gradient(90deg, #D8BE8A, #8C6A36); }
.dbar .dt i.ok { background: var(--el-color-success); }
.dbar .dt i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.dbar .dt i.warn { background: var(--el-color-warning); }
.dbar .dv { font-weight: 600; min-width: 54px; text-align: right; }
.empty { color: var(--el-text-color-secondary); font-size: 12px; padding: 8px 0; }
.dnote { font-size: 11px; color: var(--el-text-color-secondary); border-top: 1px dashed var(--el-border-color); padding-top: 10px; line-height: 1.6; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
