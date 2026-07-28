<template>
  <div>
    <div class="bar">
      <h2 class="ph">次卡价值台账</h2>
      <el-form :inline="true" size="small">
        <el-form-item label="客户ID"><el-input v-model="f.customerId" style="width:100px" placeholder="可空" clearable /></el-form-item>
        <el-form-item label="门店ID"><el-input v-model="f.storeId" style="width:90px" placeholder="可空" clearable /></el-form-item>
        <el-form-item label="起"><el-date-picker v-model="f.from" type="date" value-format="YYYY-MM-DD" placeholder="发卡起" style="width:130px" /></el-form-item>
        <el-form-item label="止"><el-date-picker v-model="f.to" type="date" value-format="YYYY-MM-DD" placeholder="发卡止" style="width:130px" /></el-form-item>
        <el-form-item><el-button type="primary" @click="load">统计</el-button></el-form-item>
      </el-form>
    </div>

    <el-alert title="营收确认口径：次卡售价为「预收」，每核销一次按 单次价(售价÷总次数) 确认为收入；剩余预收 = 未核销次数的价值(负债)。发卡时未填售价的卡按 0 计。" type="info" :closable="false" show-icon class="mb" />

    <template v-if="s">
      <div class="cards" v-loading="loading">
        <el-card shadow="never" class="kpi drill" @click="openDrill('sold')"><div class="t">已售次卡总额 <span class="go">明细 ›</span></div><div class="v">{{ money(s.soldValue) }}</div><div class="x">{{ s.cards }} 张（{{ s.activeCards }} 张生效）</div></el-card>
        <el-card shadow="never" class="kpi drill" @click="openDrill('recognized')"><div class="t">已确认收入 <span class="go">明细 ›</span></div><div class="v ok">{{ money(s.recognizedValue) }}</div><div class="x">已核销部分</div></el-card>
        <el-card shadow="never" class="kpi drill" @click="openDrill('remaining')"><div class="t">剩余预收（负债）<span class="go">明细 ›</span></div><div class="v warn">{{ money(s.remainingValue) }}</div><div class="x">未核销部分</div></el-card>
        <el-card shadow="never" class="kpi drill" @click="openDrill('rate')"><div class="t">收入确认率 <span class="go">明细 ›</span></div><div class="v">{{ s.recognizedRate }}%</div>
          <div class="ratebar"><div class="ratefill" :style="{ width: Math.min(100, s.recognizedRate) + '%' }" /></div>
        </el-card>
      </div>

      <div class="panes" v-loading="loading">
        <el-card shadow="never" class="pane">
          <template #header><b>按卡类型 · 价值台账</b><span class="sub">已确认(绿) / 剩余预收(金)</span></template>
          <div v-for="t in s.byType" :key="t.name" class="tyrow">
            <div class="tyhead"><span class="tyname">{{ t.name }}</span><span class="tycnt">{{ t.count }} 张</span><span class="tyrate">核销 {{ t.rate }}%</span></div>
            <div class="tybar"><i class="rec" :style="{ width: pctOf(t.recognized, t.sold) }" /><i class="rem" :style="{ width: pctOf(t.remaining, t.sold) }" /></div>
            <div class="tyfoot"><span>已售 {{ money(t.sold) }}</span><span class="ok">确认 {{ money(t.recognized) }}</span><span class="warn">剩余 {{ money(t.remaining) }}</span></div>
          </div>
          <el-empty v-if="!s.byType || !s.byType.length" description="暂无次卡" :image-size="60" />
        </el-card>
        <el-card shadow="never" class="pane">
          <template #header><b>次卡明细台账</b><span class="sub">Top 200 · 按售价 · 共 {{ (s.list || []).length }} 张</span></template>
          <div ref="listWrap">
          <el-table :data="s.list" size="small" border :height="tableH" empty-text="暂无次卡">
            <el-table-column prop="customer" label="客户" min-width="76" show-overflow-tooltip />
            <el-table-column prop="name" label="卡名" min-width="108" show-overflow-tooltip />
            <el-table-column label="售价" width="94" align="right"><template #default="{ row }">{{ money(row.sold) }}</template></el-table-column>
            <el-table-column label="核销" width="78" align="center"><template #default="{ row }">{{ row.used }}/{{ row.total }}</template></el-table-column>
            <el-table-column label="已确认" width="94" align="right"><template #default="{ row }"><span class="ok">{{ money(row.recognized) }}</span></template></el-table-column>
            <el-table-column label="剩余预收" width="100" align="right"><template #default="{ row }"><span class="warn">{{ money(row.remaining) }}</span></template></el-table-column>
            <el-table-column label="确认率" width="78" align="center"><template #default="{ row }">{{ row.rate }}%</template></el-table-column>
            <el-table-column prop="status" label="状态" width="66" align="center" />
          </el-table>
          </div>
        </el-card>
      </div>

      <!-- 卡片下钻 · 次卡透视 -->
      <el-drawer v-model="drill.open" :title="`次卡透视 · ${drillTitle}`" size="460px">
        <div class="drill-body">
          <div class="dhead">{{ drillHead }}</div>
          <div class="dsec"><div class="dh">按卡类型 · {{ metricLabel }}</div>
            <div class="dbar" v-for="t in byTypeSorted" :key="t.name"><span class="dk">{{ t.name }}</span><div class="dt"><i :style="{ width: pctOf(metricVal(t), maxType) }" /></div><span class="dv">{{ metric === 'rate' ? t.rate + '%' : money(metricVal(t)) }}</span></div>
            <div v-if="!byTypeSorted.length" class="empty">暂无数据</div>
          </div>
          <div class="dsec"><div class="dh">卡明细 Top 10 · {{ metricLabel }}{{ metric === 'rate' ? '（低→沉睡卡）' : '' }}</div>
            <div class="dbar" v-for="c in cardsSorted" :key="c.cardId"><span class="dk">{{ c.customer }}·{{ c.name }}</span><div class="dt"><i class="g" :style="{ width: pctOf(metricVal(c), maxCard) }" /></div><span class="dv">{{ metric === 'rate' ? c.rate + '%' : money(metricVal(c)) }}</span></div>
            <div v-if="!cardsSorted.length" class="empty">暂无数据</div>
          </div>
          <div class="dnote">口径：售价=预收；已确认收入=已核销次数×单次价；剩余预收=未核销×单次价(负债)。数据接真实 count_cards，店长视角自动仅本店。</div>
        </div>
      </el-drawer>
    </template>
    <el-empty v-else description="点「统计」查看次卡价值台账" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => '¥' + (Math.round((Number(v) || 0) * 100) / 100).toLocaleString()
const f = ref({ customerId: '', storeId: '', from: '', to: '' })
const data = ref<any>(null)
const s = computed(() => data.value)
const loading = ref(false)

// 次卡明细台账高度自适应：填满到视口底部（消除右列大片留白、多显行），随窗口/数据变化重算。
const listWrap = ref<HTMLElement>()
const tableH = ref(420)
function fitTable() {
  const el = listWrap.value
  if (!el) return
  const top = el.getBoundingClientRect().top
  tableH.value = Math.max(320, Math.floor(window.innerHeight - top - 20))
}

function pctOf(part: any, whole: any): string { const w = Number(whole) || 0; return (w ? Math.max(2, Math.round((Number(part) || 0) / w * 100)) : 0) + '%' }

// —— 卡片下钻 · 次卡透视 ——
const drill = ref<{ open: boolean; metric: string }>({ open: false, metric: 'sold' })
function openDrill(metric: string) { drill.value = { open: true, metric } }
const METRIC: Record<string, { label: string; title: string; asc: boolean }> = {
  sold: { label: '已售(预收)', title: '已售次卡', asc: false },
  recognized: { label: '已确认收入', title: '已确认收入', asc: false },
  remaining: { label: '剩余预收(负债)', title: '剩余预收', asc: false },
  rate: { label: '核销率', title: '收入确认率', asc: true },
}
const metric = computed(() => drill.value.metric)
const metricLabel = computed(() => METRIC[metric.value]?.label || '')
const drillTitle = computed(() => METRIC[metric.value]?.title || '')
function metricVal(x: any): number { return Number(x?.[metric.value]) || 0 }
function sortByMetric(arr: any[]): any[] { const a = (arr || []).slice(); const asc = METRIC[metric.value]?.asc; a.sort((x, y) => asc ? metricVal(x) - metricVal(y) : metricVal(y) - metricVal(x)); return a }
const byTypeSorted = computed(() => sortByMetric(s.value?.byType || []))
const cardsSorted = computed(() => sortByMetric(s.value?.list || []).slice(0, 10))
const maxType = computed(() => Math.max(1, ...byTypeSorted.value.map(metricVal)))
const maxCard = computed(() => Math.max(1, ...cardsSorted.value.map(metricVal)))
const drillHead = computed(() => {
  const v = s.value; if (!v) return ''
  const m = metric.value
  if (m === 'sold') return `${v.cards} 张 · ${v.activeCards} 张生效 · 已售 ${money(v.soldValue)}`
  if (m === 'recognized') return `已确认 ${money(v.recognizedValue)} · 整体确认率 ${v.recognizedRate}%`
  if (m === 'remaining') return `剩余预收(负债) ${money(v.remainingValue)} · 待核销价值`
  if (m === 'rate') return `整体核销率 ${v.recognizedRate}% · 低核销=沉睡卡，可促核销/激活`
  return ''
})

async function load() {
  loading.value = true
  try { data.value = await api().cardValueStats({ customerId: f.value.customerId ? Number(f.value.customerId) : undefined, storeId: f.value.storeId ? Number(f.value.storeId) : undefined, from: f.value.from || undefined, to: f.value.to || undefined }) }
  catch (e: any) { ElMessage.error('统计失败：' + (e?.message || '')) }
  finally { loading.value = false }
  await nextTick(); fitTable()
}
onMounted(async () => { await load(); await nextTick(); fitTable(); window.addEventListener('resize', fitTable) })
onBeforeUnmount(() => window.removeEventListener('resize', fitTable))
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.mb { margin-bottom: 14px; }
.cards { display: flex; gap: 12px; flex-wrap: wrap; }
.kpi { flex: 1; min-width: 160px; text-align: center; }
.kpi .t { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .v { font-size: 24px; font-weight: 700; margin-top: 4px; }
.kpi .v.ok { color: var(--el-color-success); }
.kpi .v.warn { color: var(--el-color-warning); }
.kpi .x { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; }
.ratebar { height: 8px; background: var(--el-fill-color-light); border-radius: 4px; overflow: hidden; margin-top: 8px; }
.ratefill { height: 100%; background: var(--el-color-primary); border-radius: 4px; }

/* —— 下钻卡 + 填满面板 —— */
.kpi.drill { cursor: pointer; transition: box-shadow .15s, transform .15s; }
.kpi.drill:hover { box-shadow: 0 8px 22px -14px rgba(140, 106, 54, .55); transform: translateY(-1px); }
.kpi .t .go { font-size: 11px; color: var(--el-color-primary); font-weight: 400; opacity: 0; transition: opacity .15s; }
.kpi.drill:hover .t .go { opacity: 1; }
.panes { display: grid; grid-template-columns: 1fr 1.15fr; gap: 14px; margin-top: 14px; }
.pane .sub { font-size: 12px; color: var(--el-text-color-secondary); margin-left: 10px; font-weight: 400; }
.tyrow { padding: 9px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.tyrow:last-child { border-bottom: 0; }
.tyhead { display: flex; align-items: baseline; gap: 10px; font-size: 13px; }
.tyhead .tyname { font-weight: 600; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tyhead .tycnt { color: var(--el-text-color-secondary); font-size: 12px; }
.tyhead .tyrate { color: var(--el-color-primary); font-size: 12px; }
.tybar { display: flex; height: 12px; border-radius: 6px; overflow: hidden; margin: 6px 0; background: var(--el-fill-color-light); }
.tybar i { height: 100%; }
.tybar i.rec { background: var(--el-color-success); }
.tybar i.rem { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.tyfoot { display: flex; gap: 16px; font-size: 12px; color: var(--el-text-color-secondary); }
.tyfoot .ok { color: var(--el-color-success); }
.tyfoot .warn { color: var(--el-color-warning); }
.drill-body { display: flex; flex-direction: column; gap: 18px; }
.dhead { font-size: 13px; font-weight: 600; color: var(--el-color-primary); background: var(--el-fill-color-lighter); border-radius: 8px; padding: 8px 12px; }
.dsec .dh { font-weight: 600; font-size: 14px; margin-bottom: 10px; padding-left: 9px; border-left: 3px solid var(--el-color-primary); }
.dbar { display: grid; grid-template-columns: 120px 1fr auto; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 12px; }
.dbar .dk { color: var(--el-text-color-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dbar .dt { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.dbar .dt i { display: block; height: 100%; background: linear-gradient(90deg, #D8BE8A, #8C6A36); }
.dbar .dt i.g { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.dbar .dv { font-weight: 600; min-width: 72px; text-align: right; }
.empty { color: var(--el-text-color-secondary); font-size: 12px; padding: 8px 0; }
.dnote { font-size: 11px; color: var(--el-text-color-secondary); border-top: 1px dashed var(--el-border-color); padding-top: 10px; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
