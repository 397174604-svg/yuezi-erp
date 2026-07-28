<template>
  <div>
    <div class="bar">
      <h2 class="ph">成本核算 · 毛利分析</h2>
      <el-form :inline="true" size="small">
        <el-form-item label="门店ID"><el-input v-model="f.storeId" style="width:90px" placeholder="可空" clearable /></el-form-item>
        <el-form-item label="起"><el-date-picker v-model="f.from" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:140px" /></el-form-item>
        <el-form-item label="止"><el-date-picker v-model="f.to" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:140px" /></el-form-item>
        <el-form-item><el-button type="primary" @click="load">分析</el-button></el-form-item>
      </el-form>
    </div>

    <el-alert v-if="t" :type="t.costedItems < t.totalItems ? 'warning' : 'success'" :closable="false" show-icon class="mb"
      :title="t.costedItems < t.totalItems ? `成本覆盖 ${t.costedItems}/${t.totalItems} 个品项——未录成本价的品项毛利按营收全额计（偏乐观），请在「品项与提成」维护成本价后再看` : `全部 ${t.totalItems} 个品项已录成本价`" />

    <div v-if="t" class="cards">
      <el-card shadow="never" class="kpi"><div class="ct">营业收入</div><div class="cv">{{ money(t.revenue) }}</div></el-card>
      <el-card shadow="never" class="kpi"><div class="ct">商品成本(COGS)</div><div class="cv">{{ money(t.cogs) }}</div></el-card>
      <el-card shadow="never" class="kpi"><div class="ct">毛利</div><div class="cv" :class="t.margin >= 0 ? 'ok' : 'bad'">{{ money(t.margin) }}</div></el-card>
      <el-card shadow="never" class="kpi"><div class="ct">毛利率</div><div class="cv">{{ t.marginRate }}%</div></el-card>
    </div>

    <el-table :data="items" v-loading="loading" border stripe size="small" empty-text="暂无销售数据" :default-sort="{ prop: 'margin', order: 'descending' }">
      <el-table-column prop="name" label="品项" min-width="160" show-overflow-tooltip />
      <el-table-column prop="qty" label="销量" width="90" align="right" />
      <el-table-column label="营收" width="130" align="right" sortable :sort-by="(r:any)=>r.revenue"><template #default="{ row }">{{ money(row.revenue) }}</template></el-table-column>
      <el-table-column label="成本" width="130" align="right"><template #default="{ row }">{{ row.cogs > 0 ? money(row.cogs) : '未录' }}</template></el-table-column>
      <el-table-column prop="margin" label="毛利" width="130" align="right" sortable><template #default="{ row }"><span :class="row.margin >= 0 ? 'ok' : 'bad'">{{ money(row.margin) }}</span></template></el-table-column>
      <el-table-column label="毛利率" min-width="160">
        <template #default="{ row }">
          <div class="mr"><div class="mbar"><div class="mfill" :style="{ width: Math.max(0, Math.min(100, row.marginRate)) + '%' }" /></div><span class="mrt">{{ row.marginRate }}%</span></div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => (Number(v) < 0 ? '-¥' : '¥') + Math.abs(Math.round(Number(v) || 0)).toLocaleString()
const f = ref({ storeId: '', from: '', to: '' })
const items = ref<any[]>([])
const totals = ref<any>(null)
const t = computed(() => totals.value)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const r: any = await api().getGrossMargin({ storeId: f.value.storeId ? Number(f.value.storeId) : undefined, from: f.value.from || undefined, to: f.value.to || undefined })
    items.value = r?.items || []; totals.value = r?.totals || null
  } catch (e: any) { ElMessage.error('分析失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.mb { margin-bottom: 12px; }
.cards { display: flex; gap: 12px; margin-bottom: 14px; }
.kpi { flex: 1; text-align: center; }
.kpi .ct { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .cv { font-size: 22px; font-weight: 600; margin-top: 4px; }
.ok { color: var(--el-color-success); }
.bad { color: var(--el-color-danger); }
.mr { display: flex; align-items: center; gap: 8px; }
.mbar { flex: 1; height: 10px; background: var(--el-fill-color-light); border-radius: 5px; overflow: hidden; }
.mfill { height: 100%; background: var(--el-color-success); border-radius: 5px; }
.mrt { width: 44px; text-align: right; font-size: 12px; }
</style>
