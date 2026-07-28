<template>
  <div>
    <div class="bar">
      <h2 class="ph">库存预警 · 自动补货</h2>
      <div class="ops">
        <el-input v-model="storeId" placeholder="门店ID(可空)" size="small" style="width:130px" clearable @change="load" />
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
        <el-button size="small" type="primary" :disabled="!items.length" @click="exportCsv">导出补货单</el-button>
      </div>
    </div>

    <el-alert :title="summary" :type="data.outOfStock ? 'error' : (data.count ? 'warning' : 'success')" :closable="false" show-icon class="mb" />

    <el-table :data="items" v-loading="loading" border stripe size="small" empty-text="无低库存预警（已设预警线的品项库存充足）">
      <el-table-column prop="storeId" label="门店" width="70" />
      <el-table-column prop="name" label="品项" min-width="150"><template #default="{ row }">{{ row.name || ('物料#' + row.itemId) }}</template></el-table-column>
      <el-table-column prop="cat" label="分类" width="100" />
      <el-table-column prop="unit" label="单位" width="70" />
      <el-table-column label="当前库存" width="110" align="right"><template #default="{ row }"><span :class="row.qty <= 0 ? 'oos' : 'low'">{{ row.qty }}</span></template></el-table-column>
      <el-table-column prop="warnQty" label="预警线" width="90" align="right" />
      <el-table-column prop="gap" label="缺口" width="90" align="right"><template #default="{ row }">{{ row.gap > 0 ? '-' + row.gap : 0 }}</template></el-table-column>
      <el-table-column label="建议补货量" width="120" align="right"><template #default="{ row }"><b>{{ row.suggestedQty }}</b> {{ row.unit }}</template></el-table-column>
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.qty <= 0 ? 'danger' : 'warning'" size="small" effect="dark">{{ row.qty <= 0 ? '缺货' : '偏低' }}</el-tag></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const data = ref<any>({ count: 0, outOfStock: 0, items: [] })
const items = computed<any[]>(() => data.value.items || [])
const loading = ref(false)
const storeId = ref('')
const summary = computed(() => data.value.count ? `${data.value.count} 个品项低于预警线${data.value.outOfStock ? `（其中 ${data.value.outOfStock} 个已缺货）` : ''}，建议按下表补货` : '当前无低库存预警')

async function load() {
  loading.value = true
  try { data.value = await api().inventoryAlerts({ storeId: storeId.value ? Number(storeId.value) : undefined }) || { count: 0, outOfStock: 0, items: [] } }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
function exportCsv() {
  const head = ['门店', '品项', '分类', '单位', '当前库存', '预警线', '缺口', '建议补货量']
  const body = items.value.map((r) => [r.storeId, r.name, r.cat, r.unit, r.qty, r.warnQty, r.gap, r.suggestedQty])
  const csv = [head, ...body].map((row) => row.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '补货单.csv'; a.click(); URL.revokeObjectURL(a.href)
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.mb { margin-bottom: 14px; }
.oos { color: var(--el-color-danger); font-weight: 700; }
.low { color: var(--el-color-warning); font-weight: 600; }
</style>
