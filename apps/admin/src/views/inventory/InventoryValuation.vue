<template>
  <div>
    <div class="bar">
      <h2 class="ph">库存估值</h2>
      <div class="ops">
        <el-input v-model="storeId" placeholder="门店ID(可空)" size="small" style="width:130px" clearable @change="load" />
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
        <el-button size="small" type="primary" :disabled="!items.length" @click="exportCsv">导出 CSV</el-button>
      </div>
    </div>

    <div class="cards">
      <el-card shadow="never" class="kpi"><div class="t">库存总金额</div><div class="v">{{ money(data.totalValue) }}</div></el-card>
      <el-card shadow="never" class="kpi"><div class="t">在库品项数</div><div class="v">{{ data.totalItems || 0 }}</div></el-card>
      <el-card shadow="never" class="kpi"><div class="t">成本覆盖</div><div class="v" :class="data.costedItems < data.totalItems ? 'warn' : 'ok'">{{ data.costedItems || 0 }}/{{ data.totalItems || 0 }}</div></el-card>
    </div>
    <el-alert v-if="data.totalItems && data.costedItems < data.totalItems" type="warning" :closable="false" show-icon class="mb"
      :title="`${data.totalItems - data.costedItems} 个在库品项未录成本价，其库存金额按 0 计——请在「品项与提成」维护成本价后估值才完整`" />

    <el-table :data="items" v-loading="loading" border stripe size="small" empty-text="无在库品项">
      <el-table-column prop="storeId" label="门店" width="70" />
      <el-table-column prop="name" label="品项" min-width="150"><template #default="{ row }">{{ row.name || ('物料#' + row.itemId) }}</template></el-table-column>
      <el-table-column prop="cat" label="分类" width="100" />
      <el-table-column prop="qty" label="数量" width="90" align="right"><template #default="{ row }">{{ row.qty }} {{ row.unit }}</template></el-table-column>
      <el-table-column label="单位成本" min-width="170" align="right"><template #default="{ row }">
        <span v-if="row.unitCost > 0">{{ money(row.unitCost) }} <el-tag size="small" :type="row.costSource === '移动加权' ? 'success' : 'info'" effect="plain">{{ row.costSource }}</el-tag></span>
        <span v-else class="muted">未录</span>
      </template></el-table-column>
      <el-table-column label="库存金额" width="130" align="right"><template #default="{ row }"><b>{{ money(row.value) }}</b></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => '¥' + (Math.round((Number(v) || 0) * 100) / 100).toLocaleString()
const data = ref<any>({ totalValue: 0, totalItems: 0, costedItems: 0, items: [] })
const items = computed<any[]>(() => data.value.items || [])
const loading = ref(false)
const storeId = ref('')

async function load() {
  loading.value = true
  try { data.value = await api().inventoryValuation({ storeId: storeId.value ? Number(storeId.value) : undefined }) || { totalValue: 0, totalItems: 0, costedItems: 0, items: [] } }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
function exportCsv() {
  const head = ['门店', '品项', '分类', '数量', '单位', '单位成本', '计价来源', '库存金额']
  const body = items.value.map((r) => [r.storeId, r.name, r.cat, r.qty, r.unit, r.unitCost, r.costSource, r.value])
  const csv = [head, ...body].map((row) => row.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '库存估值.csv'; a.click(); URL.revokeObjectURL(a.href)
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.cards { display: flex; gap: 12px; margin-bottom: 12px; }
.kpi { flex: 1; text-align: center; }
.kpi .t { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .v { font-size: 22px; font-weight: 600; margin-top: 4px; }
.kpi .v.warn { color: var(--el-color-warning); }
.kpi .v.ok { color: var(--el-color-success); }
.mb { margin-bottom: 14px; }
</style>
