<template>
  <div>
    <div class="bar">
      <h2 class="ph">配餐营养看板</h2>
      <el-button type="primary" size="small" @click="loadAll">刷新</el-button>
    </div>

    <!-- ① 按调养阶段的配餐概览 -->
    <el-card shadow="never" class="pane">
      <template #header><b>调养阶段配餐概览</b><span class="muted"> · 方案库按阶段分布</span></template>
      <div v-loading="loadingP">
        <el-table :data="stageRows" border size="small" empty-text="暂无餐单方案">
          <el-table-column prop="stage" label="调养阶段" width="120" />
          <el-table-column prop="count" label="方案数" width="100" align="right" />
          <el-table-column label="占比" min-width="200">
            <template #default="{ row }"><div class="mr"><div class="mbar"><div class="mfill" :style="{ width: barPct(row.count, maxStage) + '%' }" /></div><span class="mrt">{{ row.count }}</span></div></template>
          </el-table-column>
          <el-table-column label="平均周期" width="120" align="right"><template #default="{ row }">{{ row.avgDays }} 天</template></el-table-column>
          <el-table-column label="启用/停用" width="120" align="center"><template #default="{ row }">{{ row.active }} / {{ row.count - row.active }}</template></el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- ② 菜品库营养构成 -->
    <el-card shadow="never" class="pane">
      <template #header><b>菜品库营养构成</b><span class="muted"> · 按分类分布（共 {{ dishes.length }} 道）</span></template>
      <div v-loading="loadingD">
        <div class="chips">
          <div v-for="c in catRows" :key="c.category" class="chip">
            <span class="ct">{{ c.category }}</span>
            <div class="cbar"><div class="cfill" :style="{ width: barPct(c.count, maxCat) + '%' }" /></div>
            <span class="cn">{{ c.count }}</span>
          </div>
          <el-empty v-if="!catRows.length" description="暂无菜品" :image-size="60" />
        </div>
        <el-table v-if="dishes.length" :data="dishes" border stripe size="small" class="mt" max-height="280">
          <el-table-column prop="name" label="菜品" min-width="140" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="90" />
          <el-table-column prop="nutrients" label="营养 / 功效" min-width="240" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="80" />
        </el-table>
      </div>
    </el-card>

    <!-- ③ 某方案的配菜结构 / 营养构成 -->
    <el-card shadow="never" class="pane">
      <template #header>
        <b>方案配菜结构</b>
        <el-select v-model="curPlanId" placeholder="选择餐单方案" filterable size="small" style="width: 260px; margin-left: 12px" @change="loadItems">
          <el-option v-for="p in plans" :key="p.plan_id" :label="p.name + ' · ' + (p.stage || '') + ' · ' + (p.days || '?') + '天'" :value="p.plan_id" />
        </el-select>
      </template>
      <div v-if="curPlanId" v-loading="loadingI">
        <div class="meal-sum">
          <div v-for="m in mealRows" :key="m.mealType" class="msum">
            <span class="ml">{{ m.mealType }}</span>
            <div class="mbar sm"><div class="mfill" :style="{ width: barPct(m.count, maxMeal) + '%' }" /></div>
            <span class="mn">{{ m.count }} 道</span>
          </div>
        </div>
        <el-table :data="items" border stripe size="small" class="mt" empty-text="该方案尚未配置菜单" max-height="340">
          <el-table-column prop="day_no" label="第几天" width="80" align="center" />
          <el-table-column prop="meal_type" label="餐次" width="90" />
          <el-table-column prop="dish_name" label="菜品" min-width="150" show-overflow-tooltip />
          <el-table-column label="分类" width="90"><template #default="{ row }">{{ dishInfo(row).category || '—' }}</template></el-table-column>
          <el-table-column label="营养 / 功效" min-width="220" show-overflow-tooltip><template #default="{ row }">{{ dishInfo(row).nutrients || '—' }}</template></el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="选择一个方案查看逐天配菜与营养构成" />
    </el-card>
    <p class="note">数据来自 /api/v1/meal-plans、/api/v1/meal-dishes 与 /api/v1/meal-plans/:id/items；营养/功效为菜品库登记文本。只读看板，配置在「月子餐库」。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const STAGES = ['孕期', '月子', '产康', '通用']
const MEALS = ['早餐', '午餐', '晚餐', '加餐']

const plans = ref<any[]>([])
const dishes = ref<any[]>([])
const items = ref<any[]>([])
const curPlanId = ref<number | null>(null)
const loadingP = ref(false)
const loadingD = ref(false)
const loadingI = ref(false)

const barPct = (n: number, max: number): number => (max > 0 ? Math.round((Number(n) / max) * 100) : 0)

// ① 阶段概览：按 stage 聚合方案数/平均周期/启用数（含库中出现但不在预设的阶段兜底）。
const stageRows = computed(() => {
  const order = [...STAGES]
  const g: Record<string, { count: number; days: number; active: number }> = {}
  for (const p of plans.value) {
    const st = p.stage || '未分类'
    if (!order.includes(st)) order.push(st)
    const b = (g[st] = g[st] || { count: 0, days: 0, active: 0 })
    b.count++; b.days += Number(p.days) || 0
    if ((p.status ?? '启用') === '启用') b.active++
  }
  return order.filter((s) => g[s]).map((s) => ({ stage: s, count: g[s].count, avgDays: g[s].count ? Math.round(g[s].days / g[s].count) : 0, active: g[s].active }))
})
const maxStage = computed(() => Math.max(1, ...stageRows.value.map((r) => r.count)))

// ② 菜品分类构成
const catRows = computed(() => {
  const g: Record<string, number> = {}
  for (const d of dishes.value) { const c = d.category || '未分类'; g[c] = (g[c] || 0) + 1 }
  return Object.entries(g).map(([category, count]) => ({ category, count })).sort((a, b) => b.count - a.count)
})
const maxCat = computed(() => Math.max(1, ...catRows.value.map((r) => r.count)))

// dish_id / dish_name → {category, nutrients} 映射，供方案菜单补齐营养列。
const dishByKey = computed(() => {
  const m: Record<string, any> = {}
  for (const d of dishes.value) { m['id:' + d.dish_id] = d; if (d.name) m['nm:' + d.name] = d }
  return m
})
function dishInfo(row: any): any { return dishByKey.value['id:' + row.dish_id] || dishByKey.value['nm:' + row.dish_name] || {} }

// ③ 方案餐次分布
const mealRows = computed(() => {
  const g: Record<string, number> = {}
  for (const it of items.value) { const t = it.meal_type || '其它'; g[t] = (g[t] || 0) + 1 }
  const order = [...MEALS]
  for (const k of Object.keys(g)) if (!order.includes(k)) order.push(k)
  return order.filter((t) => g[t]).map((t) => ({ mealType: t, count: g[t] }))
})
const maxMeal = computed(() => Math.max(1, ...mealRows.value.map((r) => r.count)))

async function loadPlans() {
  loadingP.value = true
  try { plans.value = (await api().listMealPlans({}) as any[]) || [] }
  catch (e: any) { ElMessage.error('方案加载失败：' + (e?.message || '')) }
  finally { loadingP.value = false }
}
async function loadDishes() {
  loadingD.value = true
  try { dishes.value = (await api().listMealDishes({}) as any[]) || [] }
  catch (e: any) { ElMessage.error('菜品加载失败：' + (e?.message || '')) }
  finally { loadingD.value = false }
}
async function loadItems() {
  if (!curPlanId.value) { items.value = []; return }
  loadingI.value = true
  try { items.value = (await api().listMealPlanItems(curPlanId.value) as any[]) || [] }
  catch (e: any) { ElMessage.error('配菜加载失败：' + (e?.message || '')); items.value = [] }
  finally { loadingI.value = false }
}
async function loadAll() { await Promise.all([loadPlans(), loadDishes()]); if (curPlanId.value) loadItems() }

onMounted(loadAll)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.pane { margin-bottom: 14px; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; font-weight: 400; }
.mt { margin-top: 12px; }
.mr { display: flex; align-items: center; gap: 8px; }
.mbar { flex: 1; height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.mbar.sm { height: 10px; }
.mfill { height: 100%; background: var(--el-color-primary); border-radius: 6px; }
.mrt { width: 40px; text-align: right; font-size: 12px; }
.chips { display: flex; flex-direction: column; gap: 8px; }
.chip { display: flex; align-items: center; gap: 10px; }
.chip .ct { width: 64px; font-size: 13px; }
.cbar { flex: 1; height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.cfill { height: 100%; background: var(--el-color-success); border-radius: 6px; }
.chip .cn { width: 40px; text-align: right; font-size: 12px; color: var(--el-text-color-secondary); }
.meal-sum { display: flex; flex-wrap: wrap; gap: 18px; }
.msum { display: flex; align-items: center; gap: 8px; min-width: 200px; flex: 1; }
.msum .ml { width: 44px; font-size: 13px; }
.msum .mn { width: 54px; text-align: right; font-size: 12px; color: var(--el-text-color-secondary); }
.note { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 10px; }
</style>
