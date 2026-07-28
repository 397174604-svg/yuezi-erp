<template>
  <div>
    <div class="bar">
      <h2 class="ph">会员来源分析</h2>
      <div class="ops">
        <el-input v-model="storeId" placeholder="门店ID(可空)" size="small" style="width:130px" clearable @change="load" />
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="cards" v-loading="loading">
      <el-card shadow="never" class="kpi drill" @click="openDrill('total')">
        <div class="t">会员总数 <span class="go">明细 ›</span></div>
        <div class="v">{{ d ? d.total : 0 }}</div>
        <div class="x">{{ (d && d.bySource || []).length }} 渠道 · {{ (d && d.byAdvisor || []).length }} 顾问</div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('referral')">
        <div class="t">转介绍占比 <span class="go">明细 ›</span></div>
        <div class="v gold">{{ d ? d.referralRate : 0 }}%</div>
        <div class="x">{{ d ? d.referredCount : 0 }} 位由老客介绍</div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('conversion')">
        <div class="t">整体转化率 <span class="go">明细 ›</span></div>
        <div class="v ok">{{ overallConv }}%</div>
        <div class="ratebar"><div class="ratefill ok" :style="{ width: Math.min(100, overallConv) + '%' }" /></div>
      </el-card>
      <el-card shadow="never" class="kpi drill" @click="openDrill('advisor')">
        <div class="t">介绍人数 <span class="go">明细 ›</span></div>
        <div class="v">{{ (d && d.byReferrer || []).length }}</div>
        <div class="x">带来转介绍的老客数</div>
      </el-card>
    </div>

    <div class="panes" v-loading="loading">
      <!-- 来源渠道 · 转化 -->
      <el-card shadow="never" class="pane">
        <template #header><b>来源渠道 · 获客与转化</b><span class="sub">客户数（条）/ 转化率（金）</span></template>
        <div v-for="s in bySourceSorted" :key="s.source" class="chrow">
          <div class="chhead"><span class="chname">{{ s.source }}</span><span class="chcnt">{{ s.count }} 人</span><span class="chconv">转化 {{ s.conversionRate }}%</span></div>
          <div class="chbar"><i class="cnt" :style="{ width: pctOf(s.count, maxSourceCount) }" /></div>
          <div class="chbar sm"><i class="conv" :style="{ width: Math.max(2, s.conversionRate) + '%' }" /></div>
        </div>
        <el-empty v-if="!bySourceSorted.length" description="暂无来源数据" :image-size="50" />
      </el-card>

      <!-- 获客顾问榜 -->
      <el-card shadow="never" class="pane">
        <template #header><b>获客顾问榜</b><span class="sub">获客数 · 转化率 Top</span></template>
        <div v-for="(a, i) in (d ? d.byAdvisor : [])" :key="a.advisor" class="adrow">
          <span class="ark" :class="{ top: i < 3 }">{{ i + 1 }}</span>
          <span class="aname">{{ a.advisor }}</span>
          <div class="abar"><i :style="{ width: pctOf(a.count, maxAdvCount) }" /></div>
          <span class="acnt">{{ a.count }}人</span>
          <span class="aconv" :class="convCls(a.conversionRate)">{{ a.conversionRate }}%</span>
        </div>
        <el-empty v-if="!d || !d.byAdvisor.length" description="暂无顾问数据" :image-size="50" />
      </el-card>
    </div>

    <div class="panes" v-loading="loading">
      <!-- 介绍人贡献榜 -->
      <el-card shadow="never" class="pane">
        <template #header><b>介绍人贡献榜</b><span class="sub">转介绍老客 · 带来人数 Top15</span></template>
        <div v-for="(r, i) in (d ? d.byReferrer : [])" :key="r.referrer" class="rfrow">
          <span class="rrk" :class="{ top: i < 3 }">{{ i + 1 }}</span>
          <span class="rname">{{ r.referrer }}</span>
          <div class="rbar"><i :style="{ width: pctOf(r.count, maxRefCount) }" /></div>
          <span class="rcnt">{{ r.count }} 位</span>
        </div>
        <el-empty v-if="!d || !d.byReferrer.length" description="暂无转介绍数据" :image-size="50" />
      </el-card>

      <!-- 会员等级分布 -->
      <el-card shadow="never" class="pane">
        <template #header><b>会员等级分布</b><span class="sub">按等级人数</span></template>
        <div class="lv" v-for="l in (d ? d.byLevel : [])" :key="l.level">
          <span class="ln" :class="lvCls(l.level)">{{ l.level }}</span>
          <div class="lbar"><div class="lfill" :class="lvCls(l.level)" :style="{ width: lvPct(l.count) + '%' }" /></div>
          <span class="lc">{{ l.count }}</span>
        </div>
        <el-empty v-if="!d || !d.byLevel.length" description="暂无等级数据" :image-size="50" />
      </el-card>
    </div>

    <!-- 卡片下钻 -->
    <el-drawer v-model="drill.open" :title="`会员来源透视 · ${drillTitle}`" size="470px">
      <div class="drill-body" v-if="d">
        <div class="dhead">{{ drillHead }}</div>

        <template v-if="drill.metric === 'total'">
          <div class="dsec"><div class="dh">会员等级分布</div>
            <div class="dbar2" v-for="l in d.byLevel" :key="l.level"><span class="dk">{{ l.level }}</span><div class="dt"><i :style="{ width: pctOf(l.count, maxLvCount) }" /></div><span class="dv">{{ l.count }}</span></div>
          </div>
          <div class="dsec"><div class="dh">来源渠道 · 客户数</div>
            <div class="dbar2" v-for="s in bySourceSorted" :key="s.source"><span class="dk">{{ s.source }}</span><div class="dt"><i :style="{ width: pctOf(s.count, maxSourceCount) }" /></div><span class="dv">{{ s.count }}</span></div>
          </div>
        </template>

        <template v-else-if="drill.metric === 'referral'">
          <div class="dsec"><div class="dh">介绍人贡献榜</div>
            <div class="dbar2" v-for="r in d.byReferrer" :key="r.referrer"><span class="dk">{{ r.referrer }}</span><div class="dt"><i :style="{ width: pctOf(r.count, maxRefCount) }" /></div><span class="dv">{{ r.count }} 位</span></div>
          </div>
          <div class="dsec"><div class="dh">转介绍客户链（{{ d.referredCount }}）</div>
            <div class="rlrow" v-for="(r, i) in d.referredList.slice(0, 16)" :key="i"><span class="rlc">{{ r.name }}</span><span class="rlarrow">←</span><span class="rlref">{{ r.referrer }}</span><span class="rlrel">{{ r.relation || '' }}</span><span class="rllv" :class="lvCls(r.level)">{{ r.level }}</span></div>
            <div v-if="!d.referredList.length" class="empty">暂无</div>
          </div>
        </template>

        <template v-else-if="drill.metric === 'conversion'">
          <div class="dsec"><div class="dh">各来源转化率（高→低）</div>
            <div class="dbar2" v-for="s in bySourceByConv" :key="s.source"><span class="dk">{{ s.source }}</span><div class="dt"><i class="cv" :style="{ width: Math.max(2, s.conversionRate) + '%' }" /></div><span class="dv" :class="convCls(s.conversionRate)">{{ s.conversionRate }}%</span></div>
          </div>
        </template>

        <template v-else-if="drill.metric === 'advisor'">
          <div class="dsec"><div class="dh">顾问获客 · 转化</div>
            <div class="advrow" v-for="a in d.byAdvisor" :key="a.advisor"><span class="avn">{{ a.advisor }}</span><div class="avt"><i :style="{ width: pctOf(a.count, maxAdvCount) }" /></div><span class="avc">{{ a.count }}人</span><span class="avr" :class="convCls(a.conversionRate)">{{ a.conversionRate }}%</span></div>
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

const d = ref<any>(null); const loading = ref(false); const storeId = ref('')

function pctOf(part: any, whole: any): string { const w = Number(whole) || 0; return (w ? Math.max(3, Math.round((Number(part) || 0) / w * 100)) : 0) + '%' }
function convCls(v: any) { const n = Number(v) || 0; return n >= 60 ? 'ok' : (n >= 40 ? 'near' : 'warn') }
function lvCls(level: string) { return ({ 黑金: 'lv-black', 钻石: 'lv-dia', 白银: 'lv-silver', 体验: 'lv-exp' } as Record<string, string>)[level] || 'lv-exp' }

const bySourceSorted = computed(() => (d.value?.bySource || []).slice().sort((a: any, b: any) => b.count - a.count))
const bySourceByConv = computed(() => (d.value?.bySource || []).slice().sort((a: any, b: any) => b.conversionRate - a.conversionRate))
const maxSourceCount = computed(() => Math.max(1, ...bySourceSorted.value.map((x: any) => x.count)))
const maxAdvCount = computed(() => Math.max(1, ...((d.value?.byAdvisor || []).map((x: any) => x.count))))
const maxRefCount = computed(() => Math.max(1, ...((d.value?.byReferrer || []).map((x: any) => x.count))))
const maxLvCount = computed(() => Math.max(1, ...((d.value?.byLevel || []).map((x: any) => x.count))))
const lvPct = (n: number) => Math.round((Number(n) / maxLvCount.value) * 100)
const overallConv = computed(() => {
  const src = d.value?.bySource || []
  const c = src.reduce((s: number, x: any) => s + Number(x.count), 0)
  const v = src.reduce((s: number, x: any) => s + Number(x.converted), 0)
  return c ? Math.round(v / c * 100) : 0
})

// —— 下钻 ——
const drill = ref<{ open: boolean; metric: string }>({ open: false, metric: 'total' })
function openDrill(metric: string) { drill.value = { open: true, metric } }
const DRILL: Record<string, { title: string; note: string }> = {
  total: { title: '会员构成', note: '会员按来源/顾问/等级多维聚合。来源为客户建档时登记渠道，均接真实客户记录。' },
  referral: { title: '转介绍链', note: '转介绍=customers.referrer 有值（老客介绍）。介绍人榜识别核心传播老客，可重点维系/激励。' },
  conversion: { title: '来源转化', note: '转化=签约/订房/入住/退房（意向/流失/散客不计）。对比各渠道转化率，优化投放与承接。' },
  advisor: { title: '顾问业绩', note: '顾问获客数与转化率并列，识别高转化顾问（可复制打法）与待提升顾问。' },
}
const drillTitle = computed(() => DRILL[drill.value.metric]?.title || '')
const drillNote = computed(() => DRILL[drill.value.metric]?.note || '')
const drillHead = computed(() => {
  if (!d.value) return ''
  const m = drill.value.metric
  if (m === 'total') return `会员 ${d.value.total} · ${(d.value.bySource || []).length} 渠道 · ${(d.value.byAdvisor || []).length} 顾问`
  if (m === 'referral') return `转介绍 ${d.value.referredCount} 位（${d.value.referralRate}%）· ${(d.value.byReferrer || []).length} 位介绍人`
  if (m === 'conversion') return `整体转化率 ${overallConv.value}% · 覆盖 ${(d.value.bySource || []).length} 个渠道`
  if (m === 'advisor') return `${(d.value.byAdvisor || []).length} 位顾问 · 按获客数排序`
  return ''
})

async function load() {
  loading.value = true
  try { d.value = await api().getMemberAnalysis({ storeId: storeId.value ? Number(storeId.value) : undefined }) }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; gap: 8px; }

.cards { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.kpi { flex: 1; min-width: 168px; text-align: center; }
.kpi .t { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .v { font-size: 26px; font-weight: 700; margin-top: 4px; }
.kpi .v.ok { color: var(--el-color-success); }
.kpi .v.gold { color: #B8945A; }
.kpi .x { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; }
.ratebar { height: 8px; background: var(--el-fill-color-light); border-radius: 4px; overflow: hidden; margin-top: 10px; }
.ratefill { height: 100%; border-radius: 4px; }
.ratefill.ok { background: var(--el-color-success); }
.kpi.drill { cursor: pointer; transition: box-shadow .15s, transform .15s; }
.kpi.drill:hover { box-shadow: 0 8px 22px -14px rgba(140, 106, 54, .55); transform: translateY(-1px); }
.kpi .t .go { font-size: 11px; color: var(--el-color-primary); font-weight: 400; opacity: 0; transition: opacity .15s; }
.kpi.drill:hover .t .go { opacity: 1; }

.panes { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.pane { min-width: 0; }
.sub { font-size: 12px; color: var(--el-text-color-secondary); margin-left: 10px; font-weight: 400; }
.ok { color: var(--el-color-success); }
.near { color: #B8945A; }
.warn { color: var(--el-color-warning); }

.chrow { padding: 8px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.chrow:last-child { border-bottom: 0; }
.chhead { display: flex; align-items: baseline; gap: 10px; font-size: 13px; }
.chhead .chname { font-weight: 600; flex: 1; }
.chhead .chcnt { color: var(--el-text-color-secondary); font-size: 12px; }
.chhead .chconv { color: #B8945A; font-size: 12px; font-weight: 600; }
.chbar { height: 10px; border-radius: 5px; overflow: hidden; margin-top: 6px; background: var(--el-fill-color-light); }
.chbar.sm { height: 6px; margin-top: 4px; }
.chbar i { display: block; height: 100%; }
.chbar i.cnt { background: var(--el-color-primary); }
.chbar i.conv { background: linear-gradient(90deg, #E9D4A4, #9C7838); }

.adrow, .rfrow { display: grid; align-items: center; gap: 8px; padding: 6px 0; font-size: 13px; }
.adrow { grid-template-columns: 24px 66px 1fr auto auto; }
.rfrow { grid-template-columns: 24px 66px 1fr auto; }
.ark, .rrk { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 50%; background: var(--el-fill-color-light); font-size: 12px; font-weight: 700; color: var(--el-text-color-secondary); }
.ark.top, .rrk.top { background: linear-gradient(135deg, #E9D4A4, #B8945A); color: #fff; }
.aname, .rname { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.abar, .rbar { height: 9px; border-radius: 5px; overflow: hidden; background: var(--el-fill-color-light); }
.abar i { display: block; height: 100%; background: var(--el-color-primary); }
.rbar i { display: block; height: 100%; background: linear-gradient(90deg, #E9D4A4, #9C7838); }
.acnt, .rcnt { color: var(--el-text-color-secondary); font-size: 12px; min-width: 34px; text-align: right; }
.aconv { font-weight: 700; min-width: 40px; text-align: right; }

.lv { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.lv .ln { width: 52px; font-size: 13px; font-weight: 600; }
.lv .lbar { flex: 1; height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.lv .lfill { height: 100%; border-radius: 6px; background: var(--el-color-primary); }
.lv .lc { width: 40px; text-align: right; font-size: 13px; font-weight: 600; }
.lv-black { color: #8C6A36; } .lfill.lv-black { background: linear-gradient(90deg, #C2A063, #8C6A36); }
.lv-dia { color: #4a7a9c; } .lfill.lv-dia { background: linear-gradient(90deg, #9cc4d8, #4a7a9c); }
.lv-silver { color: #8a8f96; } .lfill.lv-silver { background: linear-gradient(90deg, #c3c8cf, #8a8f96); }
.lv-exp { color: var(--el-text-color-secondary); } .lfill.lv-exp { background: var(--el-fill-color-dark); }

.drill-body { display: flex; flex-direction: column; gap: 18px; }
.dhead { font-size: 13px; font-weight: 600; color: var(--el-color-primary); background: var(--el-fill-color-lighter); border-radius: 8px; padding: 8px 12px; }
.dsec .dh { font-weight: 600; font-size: 14px; margin-bottom: 10px; padding-left: 9px; border-left: 3px solid var(--el-color-primary); }
.dbar2 { display: grid; grid-template-columns: 92px 1fr auto; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 12px; }
.dbar2 .dk { color: var(--el-text-color-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dbar2 .dt { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.dbar2 .dt i { display: block; height: 100%; background: linear-gradient(90deg, #D8BE8A, #8C6A36); }
.dbar2 .dt i.cv { background: var(--el-color-success); }
.dbar2 .dv { font-weight: 600; min-width: 44px; text-align: right; }
.rlrow { display: grid; grid-template-columns: auto auto 1fr auto auto; align-items: center; gap: 6px; font-size: 12px; padding: 5px 0; border-bottom: 1px dashed var(--el-border-color-lighter); }
.rlrow .rlc { font-weight: 600; }
.rlrow .rlarrow { color: var(--el-text-color-secondary); }
.rlrow .rlref { color: var(--el-text-color-secondary); }
.rlrow .rlrel { color: #B8945A; font-size: 11px; }
.rlrow .rllv { font-weight: 600; font-size: 11px; }
.advrow { display: grid; grid-template-columns: 68px 1fr auto auto; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 8px; }
.advrow .avn { font-weight: 600; }
.advrow .avt { height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.advrow .avt i { display: block; height: 100%; background: linear-gradient(90deg, #D8BE8A, #8C6A36); }
.advrow .avc { color: var(--el-text-color-secondary); min-width: 34px; text-align: right; }
.advrow .avr { font-weight: 700; min-width: 40px; text-align: right; }
.empty { color: var(--el-text-color-secondary); font-size: 12px; padding: 8px 0; }
.dnote { font-size: 11px; color: var(--el-text-color-secondary); border-top: 1px dashed var(--el-border-color); padding-top: 10px; line-height: 1.6; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
