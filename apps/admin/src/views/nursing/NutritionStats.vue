<template>
  <div>
    <div class="bar">
      <h2 class="ph">膳食营养统计</h2>
      <el-form :inline="true" size="small">
        <el-form-item label="起"><el-date-picker v-model="f.from" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:140px" /></el-form-item>
        <el-form-item label="止"><el-date-picker v-model="f.to" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:140px" /></el-form-item>
        <el-form-item label="门店ID"><el-input v-model="f.storeId" style="width:90px" placeholder="可空" clearable /></el-form-item>
        <el-form-item><el-button type="primary" @click="load">统计</el-button></el-form-item>
      </el-form>
    </div>

    <div v-if="t" class="cards">
      <el-card shadow="never" class="kpi"><div class="ct">餐单总数</div><div class="cv">{{ t.totalPlans }}</div></el-card>
      <el-card shadow="never" class="kpi"><div class="ct">总热量</div><div class="cv">{{ (t.totalCalorie || 0).toLocaleString() }} <span class="u">kcal</span></div></el-card>
      <el-card shadow="never" class="kpi"><div class="ct">平均热量/餐</div><div class="cv">{{ t.avgCalorie }} <span class="u">kcal</span></div></el-card>
      <el-card shadow="never" class="kpi"><div class="ct">配送完成率</div><div class="cv" :class="t.deliveryRate >= 90 ? 'ok' : ''">{{ t.deliveryRate }}% <span class="u">({{ t.deliveredCount }}/{{ t.totalPlans }})</span></div></el-card>
    </div>

    <el-card shadow="never" class="pane">
      <template #header><b>按餐次分布</b></template>
      <el-table :data="byMealType" border size="small" v-loading="loading" empty-text="暂无数据">
        <el-table-column prop="mealType" label="餐次" width="100" />
        <el-table-column prop="count" label="餐单数" width="110" align="right" />
        <el-table-column label="占比" min-width="180">
          <template #default="{ row }"><div class="mr"><div class="mbar"><div class="mfill" :style="{ width: pct(row.count) + '%' }" /></div><span class="mrt">{{ pct(row.count) }}%</span></div></template>
        </el-table-column>
        <el-table-column label="总热量" width="130" align="right"><template #default="{ row }">{{ (row.totalCalorie || 0).toLocaleString() }} kcal</template></el-table-column>
        <el-table-column label="平均热量" width="120" align="right"><template #default="{ row }">{{ row.avgCalorie }} kcal</template></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const now = new Date()
const f = ref({ from: now.toISOString().slice(0, 8) + '01', to: now.toISOString().slice(0, 10), storeId: '' })
const data = ref<any>(null)
const t = computed(() => data.value?.totals)
const byMealType = computed<any[]>(() => data.value?.byMealType || [])
const loading = ref(false)
const maxCount = computed(() => Math.max(1, ...byMealType.value.map((x: any) => Number(x.count) || 0)))
const pct = (n: number) => Math.round((Number(n) / maxCount.value) * 100)

async function load() {
  loading.value = true
  try { data.value = await api().getNutritionStats({ from: f.value.from || undefined, to: f.value.to || undefined, storeId: f.value.storeId ? Number(f.value.storeId) : undefined }) }
  catch (e: any) { ElMessage.error('统计失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.cards { display: flex; gap: 12px; margin-bottom: 14px; }
.kpi { flex: 1; text-align: center; }
.kpi .ct { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .cv { font-size: 22px; font-weight: 600; margin-top: 4px; }
.kpi .cv .u { font-size: 12px; color: var(--el-text-color-secondary); font-weight: 400; }
.kpi .cv.ok { color: var(--el-color-success); }
.pane { min-width: 0; }
.mr { display: flex; align-items: center; gap: 8px; }
.mbar { flex: 1; height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.mfill { height: 100%; background: var(--el-color-primary); border-radius: 6px; }
.mrt { width: 44px; text-align: right; font-size: 12px; }
</style>
