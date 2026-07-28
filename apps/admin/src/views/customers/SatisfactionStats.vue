<template>
  <div>
    <div class="bar">
      <h2 class="ph">满意度 · 回访统计</h2>
      <el-form :inline="true" size="small">
        <el-form-item label="起"><el-date-picker v-model="f.from" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:138px" /></el-form-item>
        <el-form-item label="止"><el-date-picker v-model="f.to" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:138px" /></el-form-item>
        <el-form-item label="门店ID"><el-input v-model="f.storeId" style="width:88px" placeholder="可空" clearable /></el-form-item>
        <el-form-item><el-button type="primary" @click="load">统计</el-button></el-form-item>
      </el-form>
    </div>

    <!-- KPI 概览（可下钻） -->
    <div class="cards" v-loading="loading">
      <el-card shadow="never" class="kpi drill" @click="openDrill('avg')">
        <div class="t">平均满意度 <span class="go">明细 ›</span></div>
        <div class="v">{{ sat ? sat.avgScore : '—' }}<span class="unit"> 分</span></div>
        <div class="x">{{ sat ? sat.count : 0 }} 份评价 · {{ sat ? sat.minScore : 0 }}~{{ sat ? sat.maxScore : 0 }} 分</div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('good')">
        <div class="t">好评率（≥90分）<span class="go">明细 ›</span></div>
        <div class="v ok">{{ sat ? sat.goodRate : 0 }}%</div>
        <div class="ratebar"><div class="ratefill ok" :style="{ width: Math.min(100, sat ? sat.goodRate : 0) + '%' }" /></div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('followup')">
        <div class="t">回访完成率 <span class="go">明细 ›</span></div>
        <div class="v" :class="fu && fu.completionRate >= 80 ? 'ok' : 'near'">{{ fu ? fu.completionRate : 0 }}%</div>
        <div class="x">已回访 {{ fu ? fu.completed : 0 }} / 合计 {{ fu ? fu.total : 0 }}</div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('pending')">
        <div class="t">待跟进回访 <span class="go">明细 ›</span></div>
        <div class="v warn">{{ fu ? fu.pending : 0 }}</div>
        <div class="x">未回访，需联系客户</div>
      </el-card>
    </div>

    <!-- 满意度趋势 -->
    <el-card shadow="never" class="card" v-loading="loading">
      <template #header><b>满意度趋势</b><span class="sub">按日均分（柱=当日评价量 · 线=当日平均分）</span></template>
      <div v-if="tg.pts.length" class="trendwrap">
        <svg :viewBox="`0 0 ${tg.W} ${tg.H}`" class="trend" preserveAspectRatio="none">
          <line v-for="tk in tg.ticks" :key="'g'+tk.v" :x1="tg.x0" :x2="tg.x1" :y1="tk.y" :y2="tk.y" class="grid" />
          <text v-for="tk in tg.ticks" :key="'l'+tk.v" :x="tg.x0-8" :y="tk.y+3" class="ytick">{{ tk.v }}</text>
          <rect v-for="(p,i) in tg.pts" :key="'b'+i" :x="p.x-6" :y="tg.y1-p.bh" width="12" :height="p.bh" class="vol" />
          <path :d="tg.area" class="area" />
          <polyline :points="tg.line" class="ln" />
          <circle v-for="(p,i) in tg.pts" :key="'c'+i" :cx="p.x" :cy="p.y" r="3" class="dot"><title>{{ p.date }} · {{ p.avg }}分 · {{ p.c }}份</title></circle>
          <text v-for="(p,i) in tg.labels" :key="'x'+i" :x="p.x" :y="tg.y1+16" class="xtick">{{ p.d }}</text>
        </svg>
      </div>
      <el-empty v-else description="所选区间暂无评价" :image-size="56" />
    </el-card>

    <div class="panes" v-loading="loading">
      <!-- 维度矩阵：按服务类型 -->
      <el-card shadow="never" class="pane">
        <template #header><b>满意度维度矩阵</b><span class="sub">按服务类型 · 均分/份数</span></template>
        <div v-for="t in (sat ? sat.byType : [])" :key="t.type" class="tyrow">
          <div class="tyhead"><span class="tyname">{{ t.type }}</span><span class="tycnt">{{ t.count }} 份</span><span class="tyavg" :class="scoreCls(t.avg)">{{ t.avg }} 分</span></div>
          <div class="tybar"><i :class="scoreCls(t.avg)" :style="{ width: scorePct(t.avg) }" /></div>
        </div>
        <el-empty v-if="!sat || !sat.byType.length" description="暂无维度数据" :image-size="50" />
      </el-card>

      <!-- 员工满意度榜 -->
      <el-card shadow="never" class="pane">
        <template #header><b>员工满意度榜</b><span class="sub">被评价一线员工 · 均分 Top10</span></template>
        <div v-for="(s, i) in (sat ? sat.byStaff : [])" :key="s.staff" class="strow">
          <span class="srk" :class="{ top: i < 3 }">{{ i + 1 }}</span>
          <span class="sname">{{ s.staff }}</span>
          <div class="sbar"><i :class="scoreCls(s.avg)" :style="{ width: scorePct(s.avg) }" /></div>
          <span class="savg" :class="scoreCls(s.avg)">{{ s.avg }}</span>
          <span class="scnt">{{ s.count }}份</span>
        </div>
        <el-empty v-if="!sat || !sat.byStaff.length" description="暂无员工评价" :image-size="50" />
      </el-card>
    </div>

    <div class="panes" v-loading="loading">
      <!-- 回访完成 -->
      <el-card shadow="never" class="pane">
        <template #header><b>回访完成情况</b><span class="sub">按回访类型完成率</span></template>
        <div class="fuwrap" v-if="fu">
          <el-progress type="dashboard" :width="112" :percentage="fu.completionRate" :color="fu.completionRate >= 80 ? '#67c23a' : '#B8945A'" />
          <div class="futy">
            <div v-for="t in fu.byType" :key="t.type" class="futyrow">
              <span class="ftn">{{ t.type }}</span>
              <div class="ftbar"><i :style="{ width: Math.max(3, t.rate) + '%' }" /></div>
              <span class="ftr">{{ t.rate }}%</span><span class="ftc">{{ t.done }}/{{ t.count }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 评分分布 + 门店对比 -->
      <el-card shadow="never" class="pane">
        <template #header><b>评分分布 · 门店对比</b></template>
        <div class="dist" v-if="sat && sat.distribution.length">
          <div v-for="d in sat.distribution" :key="d.score" class="dl">
            <span class="dn">{{ d.score }}</span>
            <div class="dbar"><div class="dfill" :style="{ width: distPct(d.count) + '%' }" /></div>
            <span class="dc">{{ d.count }}</span>
          </div>
        </div>
        <div class="stores" v-if="sat && sat.byStore.length">
          <div v-for="s in sat.byStore" :key="s.storeId" class="storow">
            <span class="son">店#{{ s.storeId }}</span>
            <div class="sobar"><i :class="scoreCls(s.avg)" :style="{ width: scorePct(s.avg) }" /></div>
            <span class="soavg" :class="scoreCls(s.avg)">{{ s.avg }}分</span><span class="socnt">{{ s.count }}份</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 客户留言样本 -->
    <el-card shadow="never" class="card" v-loading="loading">
      <template #header><b>客户留言样本</b><span class="sub">近期真实反馈（{{ sat ? sat.recent.length : 0 }} 条，展示前 9）</span></template>
      <div class="fbgrid" v-if="sat && sat.recent.length">
        <div v-for="r in sat.recent.slice(0, 9)" :key="r.id" class="fbcard">
          <div class="fbhead"><span class="fbscore" :class="scoreCls(r.score)">{{ r.score }}分</span><span class="fbtype">{{ r.type }}</span></div>
          <div class="fbnote">{{ r.note || '—' }}</div>
          <div class="fbfoot">{{ r.cust || '客户' }} · {{ r.staff || '—' }} · {{ (r.at || '').slice(5, 10) }}</div>
        </div>
      </div>
      <el-empty v-else description="暂无留言" :image-size="50" />
    </el-card>

    <!-- 卡片下钻 -->
    <el-drawer v-model="drill.open" :title="`满意度透视 · ${drillTitle}`" size="460px">
      <div class="drill-body" v-if="sat">
        <div class="dhead">{{ drillHead }}</div>

        <template v-if="drill.metric === 'avg' || drill.metric === 'good'">
          <div class="dsec"><div class="dh">评分分布</div>
            <div class="dbar2" v-for="d in sat.distribution" :key="d.score"><span class="dk">{{ d.score }} 分</span><div class="dt"><i :class="scoreCls(d.score)" :style="{ width: distPct(d.count) + '%' }" /></div><span class="dv">{{ d.count }}</span></div>
          </div>
          <div class="dsec"><div class="dh">按服务类型 · 均分</div>
            <div class="dbar2" v-for="t in sat.byType" :key="t.type"><span class="dk">{{ t.type }}</span><div class="dt"><i :class="scoreCls(t.avg)" :style="{ width: scorePct(t.avg) }" /></div><span class="dv" :class="scoreCls(t.avg)">{{ t.avg }}</span></div>
          </div>
        </template>

        <template v-else-if="drill.metric === 'followup'">
          <div class="dsec"><div class="dh">按回访类型 · 完成率</div>
            <div class="dbar2" v-for="t in (fu ? fu.byType : [])" :key="t.type"><span class="dk">{{ t.type }}</span><div class="dt"><i :style="{ width: Math.max(3, t.rate) + '%' }" /></div><span class="dv">{{ t.rate }}%</span></div>
          </div>
          <div class="dsec"><div class="dh">待跟进清单（{{ fu ? fu.pending : 0 }}）</div>
            <div class="pdrow" v-for="p in (fu ? fu.pendingList.slice(0, 12) : [])" :key="p.id"><span class="pdc">{{ p.cust || '客户' }}</span><span class="pdt">{{ p.title }}</span><span class="pdh">{{ p.handler || '—' }}</span></div>
            <div v-if="fu && !fu.pendingList.length" class="empty">无待跟进</div>
          </div>
        </template>

        <template v-else-if="drill.metric === 'pending'">
          <div class="dsec"><div class="dh">待跟进回访清单（{{ fu ? fu.pending : 0 }}）</div>
            <div class="pdrow" v-for="p in (fu ? fu.pendingList : [])" :key="p.id"><span class="pdc">{{ p.cust || '客户' }}</span><span class="pdt">{{ p.title }}</span><span class="pdh">{{ p.handler || '—' }}</span><span class="pda">{{ (p.at || '').slice(5, 10) }}</span></div>
            <div v-if="fu && !fu.pendingList.length" class="empty">无待跟进</div>
          </div>
        </template>

        <div class="dnote">{{ drillNote }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const now = new Date()
const iso = (d: Date) => d.toISOString().slice(0, 10)
const f = ref({ from: iso(new Date(now.getTime() - 30 * 86400000)), to: iso(now), storeId: '' })
const sat = ref<any>(null); const fu = ref<any>(null); const loading = ref(false)

const maxDist = computed(() => Math.max(1, ...((sat.value?.distribution || []).map((x: any) => Number(x.count) || 0))))
const distPct = (n: number) => Math.round((Number(n) / maxDist.value) * 100)
// 均分映射到 70~100 视觉区间（低于 70 截到 3%），供维度/员工/门店进度条
const scorePct = (v: any) => { const s = Number(v) || 0; return Math.max(3, Math.min(100, Math.round((s - 70) / 30 * 100))) + '%' }
function scoreCls(v: any) { const s = Number(v) || 0; return s >= 92 ? 'ok' : (s >= 84 ? 'near' : 'warn') }

// 满意度趋势几何
const tg = computed(() => {
  const t = (sat.value?.trend || []) as any[]
  const W = 1000, H = 196, x0 = 40, x1 = 980, y0 = 16, y1 = 156
  const yLo = 70, yHi = 100
  const yOf = (v: number) => y1 - (y1 - y0) * ((Math.max(yLo, Math.min(yHi, v)) - yLo) / (yHi - yLo))
  const n = t.length
  const xOf = (i: number) => n <= 1 ? (x0 + x1) / 2 : x0 + (x1 - x0) * i / (n - 1)
  const maxC = Math.max(1, ...t.map((r) => Number(r.count) || 0))
  const pts = t.map((r, i) => ({ x: xOf(i), y: yOf(Number(r.avg) || 0), c: Number(r.count) || 0, avg: r.avg, date: r.date, bh: (y1 - y0) * 0.55 * ((Number(r.count) || 0) / maxC) }))
  const line = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  const area = pts.length ? `M${pts[0].x.toFixed(1)},${y1} ` + pts.map((p) => `L${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + ` L${pts[pts.length - 1].x.toFixed(1)},${y1} Z` : ''
  const ticks = [70, 80, 90, 100].map((v) => ({ v, y: yOf(v) }))
  const labIdx = n <= 1 ? [0] : [0, Math.floor(n / 2), n - 1]
  const labels = labIdx.map((i) => ({ x: xOf(i), d: (t[i]?.date || '').slice(5) }))
  return { W, H, x0, x1, y0, y1, pts, line, area, ticks, labels }
})

// —— 下钻 ——
const drill = ref<{ open: boolean; metric: string }>({ open: false, metric: 'avg' })
function openDrill(metric: string) { drill.value = { open: true, metric } }
const DRILL: Record<string, { title: string; note: string }> = {
  avg: { title: '满意度构成', note: '评分为 100 分制客户评价（ops_records kind=满意度）。均分/分布/维度均按真实评价聚合，非写死。' },
  good: { title: '好评结构', note: '好评=评分≥90 分的占比。可对标各服务类型均分，识别哪类服务最受认可、哪类待提升。' },
  followup: { title: '回访完成', note: '回访完成=状态属「已回访/已完成/已处理」。按回访类型看完成率，待跟进清单可直接指派联系。' },
  pending: { title: '待跟进回访', note: '未回访客户清单，建议按满月/出所时点优先联系，闭环满意度回访。' },
}
const drillTitle = computed(() => DRILL[drill.value.metric]?.title || '')
const drillNote = computed(() => DRILL[drill.value.metric]?.note || '')
const drillHead = computed(() => {
  const m = drill.value.metric
  if (!sat.value) return ''
  if (m === 'avg') return `平均 ${sat.value.avgScore} 分 · ${sat.value.count} 份 · ${sat.value.minScore}~${sat.value.maxScore} 分`
  if (m === 'good') return `好评率 ${sat.value.goodRate}% · ${sat.value.goodCount}/${sat.value.count} 份 ≥90 分`
  if (m === 'followup') return `完成率 ${fu.value?.completionRate ?? 0}% · 已回访 ${fu.value?.completed ?? 0}/${fu.value?.total ?? 0}`
  if (m === 'pending') return `待跟进 ${fu.value?.pending ?? 0} 单`
  return ''
})

async function load() {
  loading.value = true
  const flt = { from: f.value.from || undefined, to: f.value.to || undefined, storeId: f.value.storeId ? Number(f.value.storeId) : undefined }
  try { sat.value = await api().getSatisfactionStats(flt); fu.value = await api().getFollowupStats(flt) }
  catch (e: any) { ElMessage.error('统计失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
.sub { font-size: 12px; color: var(--el-text-color-secondary); margin-left: 10px; font-weight: 400; }

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
.ratefill { height: 100%; border-radius: 4px; }
.ratefill.ok { background: var(--el-color-success); }
.kpi.drill { cursor: pointer; transition: box-shadow .15s, transform .15s; }
.kpi.drill:hover { box-shadow: 0 8px 22px -14px rgba(140, 106, 54, .55); transform: translateY(-1px); }
.kpi .t .go { font-size: 11px; color: var(--el-color-primary); font-weight: 400; opacity: 0; transition: opacity .15s; }
.kpi.drill:hover .t .go { opacity: 1; }

.ok { color: var(--el-color-success); }
.near { color: #B8945A; }
.warn { color: var(--el-color-warning); }

.trendwrap { width: 100%; overflow-x: auto; }
.trend { width: 100%; height: 210px; display: block; }
.trend .grid { stroke: var(--el-border-color-lighter); stroke-width: 1; }
.trend .ytick, .trend .xtick { fill: var(--el-text-color-secondary); font-size: 11px; }
.trend .ytick { text-anchor: end; }
.trend .xtick { text-anchor: middle; }
.trend .vol { fill: var(--el-fill-color); }
.trend .area { fill: rgba(184, 148, 90, .12); }
.trend .ln { fill: none; stroke: #B8945A; stroke-width: 2; }
.trend .dot { fill: #8C6A36; }

.panes { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.pane { min-width: 0; }
.tyrow { padding: 8px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.tyrow:last-child { border-bottom: 0; }
.tyhead { display: flex; align-items: baseline; gap: 10px; font-size: 13px; }
.tyhead .tyname { font-weight: 600; flex: 1; }
.tyhead .tycnt { color: var(--el-text-color-secondary); font-size: 12px; }
.tyhead .tyavg { font-weight: 700; }
.tybar { height: 10px; border-radius: 5px; overflow: hidden; margin-top: 6px; background: var(--el-fill-color-light); }
.tybar i { display: block; height: 100%; }
.tybar i.ok { background: var(--el-color-success); }
.tybar i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.tybar i.warn { background: var(--el-color-warning); }

.strow { display: grid; grid-template-columns: 24px 68px 1fr auto auto; align-items: center; gap: 8px; padding: 6px 0; font-size: 13px; }
.strow .srk { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 50%; background: var(--el-fill-color-light); font-size: 12px; font-weight: 700; color: var(--el-text-color-secondary); }
.strow .srk.top { background: linear-gradient(135deg, #E9D4A4, #B8945A); color: #fff; }
.strow .sname { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.strow .sbar { height: 9px; border-radius: 5px; overflow: hidden; background: var(--el-fill-color-light); }
.strow .sbar i { display: block; height: 100%; }
.strow .sbar i.ok { background: var(--el-color-success); }
.strow .sbar i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.strow .sbar i.warn { background: var(--el-color-warning); }
.strow .savg { font-weight: 700; min-width: 34px; text-align: right; }
.strow .scnt { color: var(--el-text-color-secondary); font-size: 11px; min-width: 30px; text-align: right; }

.fuwrap { display: flex; align-items: center; gap: 18px; }
.futy { flex: 1; min-width: 0; }
.futyrow { display: grid; grid-template-columns: 84px 1fr auto auto; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 8px; }
.futyrow .ftn { color: var(--el-text-color-secondary); white-space: nowrap; }
.futyrow .ftbar { height: 9px; border-radius: 5px; overflow: hidden; background: var(--el-fill-color-light); }
.futyrow .ftbar i { display: block; height: 100%; background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.futyrow .ftr { font-weight: 700; min-width: 34px; text-align: right; }
.futyrow .ftc { color: var(--el-text-color-secondary); min-width: 40px; text-align: right; }

.dist { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; }
.dl { display: flex; align-items: center; gap: 8px; }
.dl .dn { width: 26px; font-size: 12px; text-align: right; color: var(--el-text-color-secondary); }
.dl .dbar { flex: 1; height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.dl .dfill { height: 100%; background: linear-gradient(90deg, #E9D4A4, #B8945A); border-radius: 5px; }
.dl .dc { width: 28px; text-align: right; font-size: 12px; font-weight: 600; }
.stores { border-top: 1px dashed var(--el-border-color-lighter); padding-top: 10px; }
.storow { display: grid; grid-template-columns: 52px 1fr auto auto; align-items: center; gap: 8px; font-size: 13px; margin-bottom: 7px; }
.storow .son { font-weight: 600; }
.storow .sobar { height: 9px; border-radius: 5px; overflow: hidden; background: var(--el-fill-color-light); }
.storow .sobar i { display: block; height: 100%; }
.storow .sobar i.ok { background: var(--el-color-success); }
.storow .sobar i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.storow .sobar i.warn { background: var(--el-color-warning); }
.storow .soavg { font-weight: 700; min-width: 40px; text-align: right; }
.storow .socnt { color: var(--el-text-color-secondary); font-size: 11px; min-width: 30px; text-align: right; }

.fbgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.fbcard { border: 1px solid var(--el-border-color-lighter); border-radius: 10px; padding: 12px; background: var(--el-fill-color-blank); }
.fbhead { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.fbscore { font-weight: 700; font-size: 15px; }
.fbscore.ok { color: var(--el-color-success); }
.fbscore.near { color: #B8945A; }
.fbscore.warn { color: var(--el-color-warning); }
.fbtype { font-size: 12px; color: var(--el-text-color-secondary); background: var(--el-fill-color-light); padding: 1px 8px; border-radius: 10px; }
.fbnote { font-size: 13px; line-height: 1.6; color: var(--el-text-color-primary); min-height: 42px; }
.fbfoot { font-size: 11px; color: var(--el-text-color-secondary); margin-top: 8px; }

.drill-body { display: flex; flex-direction: column; gap: 18px; }
.dhead { font-size: 13px; font-weight: 600; color: var(--el-color-primary); background: var(--el-fill-color-lighter); border-radius: 8px; padding: 8px 12px; }
.dsec .dh { font-weight: 600; font-size: 14px; margin-bottom: 10px; padding-left: 9px; border-left: 3px solid var(--el-color-primary); }
.dbar2 { display: grid; grid-template-columns: 78px 1fr auto; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 12px; }
.dbar2 .dk { color: var(--el-text-color-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dbar2 .dt { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.dbar2 .dt i { display: block; height: 100%; background: linear-gradient(90deg, #D8BE8A, #8C6A36); }
.dbar2 .dt i.ok { background: var(--el-color-success); }
.dbar2 .dt i.near { background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.dbar2 .dt i.warn { background: var(--el-color-warning); }
.dbar2 .dv { font-weight: 600; min-width: 40px; text-align: right; }
.pdrow { display: grid; grid-template-columns: 68px 1fr auto auto; gap: 8px; font-size: 12px; padding: 6px 0; border-bottom: 1px dashed var(--el-border-color-lighter); }
.pdrow .pdc { font-weight: 600; }
.pdrow .pdt { color: var(--el-text-color-secondary); }
.pdrow .pdh, .pdrow .pda { color: var(--el-text-color-secondary); }
.empty { color: var(--el-text-color-secondary); font-size: 12px; padding: 8px 0; }
.dnote { font-size: 11px; color: var(--el-text-color-secondary); border-top: 1px dashed var(--el-border-color); padding-top: 10px; line-height: 1.6; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } .fbgrid { grid-template-columns: 1fr; } }
</style>
