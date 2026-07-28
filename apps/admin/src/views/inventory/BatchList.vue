<template>
  <div>
    <div class="bar">
      <h2 class="ph">批次 · 保质期</h2>
      <div class="ops">
        <el-input v-model="f.storeId" placeholder="门店ID(可空)" size="small" style="width:120px" clearable @change="reload" />
        <el-select v-model="warnDays" size="small" style="width:130px" @change="loadExpiring"><el-option v-for="d in [7,15,30,60,90]" :key="d" :label="'临期 ' + d + ' 天内'" :value="d" /></el-select>
        <el-button size="small" @click="reload">刷新</el-button>
        <el-button size="small" type="primary" @click="openInbound">批次入库</el-button>
      </div>
    </div>

    <el-alert v-if="exp" :type="exp.expiredCount ? 'error' : (exp.count ? 'warning' : 'success')" :closable="false" show-icon class="mb"
      :title="exp.count ? `临期预警：${exp.count} 个批次将在 ${exp.withinDays} 天内到期${exp.expiredCount ? `（其中 ${exp.expiredCount} 个已过期）` : ''}` : '暂无临期批次'" />
    <el-table v-if="exp && exp.items.length" :data="exp.items" border stripe size="small" class="mb">
      <el-table-column prop="itemName" label="品项" min-width="140"><template #default="{ row }">{{ row.itemName || ('物料#' + row.itemId) }}</template></el-table-column>
      <el-table-column prop="batchNo" label="批次号" min-width="150" />
      <el-table-column label="余量" width="90" align="right"><template #default="{ row }">{{ row.qty }} {{ row.unit }}</template></el-table-column>
      <el-table-column prop="expiryDate" label="到期日" width="120" />
      <el-table-column label="剩余天数" width="110" align="right"><template #default="{ row }"><el-tag :type="row.expired ? 'danger' : (row.daysLeft <= 7 ? 'warning' : 'info')" size="small" effect="dark">{{ row.expired ? '已过期 ' + (-row.daysLeft) + ' 天' : row.daysLeft + ' 天' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="90" fixed="right"><template #default="{ row }"><el-button link type="danger" size="small" @click="writeoff(row)">报损</el-button></template></el-table-column>
    </el-table>

    <div class="sec">批次台账（在库）</div>
    <el-table :data="batches" v-loading="loading" border stripe size="small" empty-text="暂无在库批次">
      <el-table-column prop="store_id" label="门店" width="70" />
      <el-table-column label="品项" min-width="140"><template #default="{ row }">{{ row.item_name || ('物料#' + row.item_id) }}</template></el-table-column>
      <el-table-column prop="batch_no" label="批次号" min-width="150" />
      <el-table-column label="余量" width="90" align="right"><template #default="{ row }">{{ row.qty }} {{ row.unit }}</template></el-table-column>
      <el-table-column prop="production_date" label="生产日" width="120"><template #default="{ row }">{{ row.production_date || '—' }}</template></el-table-column>
      <el-table-column prop="expiry_date" label="到期日" width="120"><template #default="{ row }">{{ row.expiry_date || '—' }}</template></el-table-column>
      <el-table-column label="操作" width="150" fixed="right"><template #default="{ row }">
        <el-button link type="warning" size="small" @click="consume(row)">消耗</el-button>
        <el-button link type="danger" size="small" @click="writeoff(row)">报损</el-button>
      </template></el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="批次入库" width="520px">
      <el-form :model="form" label-width="84px" size="small">
        <el-form-item label="门店"><el-select v-model="form.storeId" filterable placeholder="选择" style="width:200px"><el-option v-for="s in stores" :key="s.store_id" :label="s.name || ('门店#' + s.store_id)" :value="s.store_id" /></el-select></el-form-item>
        <el-form-item label="物料"><el-select v-model="form.itemId" filterable placeholder="选择" style="width:220px"><el-option v-for="it in items" :key="it.item_id" :label="it.name || ('物料#' + it.item_id)" :value="it.item_id" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input v-model="form.qty" style="width:120px" /></el-form-item>
        <el-form-item label="批次号"><el-input v-model="form.batchNo" style="width:200px" placeholder="留空自动派生" /></el-form-item>
        <el-form-item label="生产日"><el-date-picker v-model="form.productionDate" type="date" value-format="YYYY-MM-DD" style="width:160px" /></el-form-item>
        <el-form-item label="到期日"><el-date-picker v-model="form.expiryDate" type="date" value-format="YYYY-MM-DD" style="width:160px" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" @click="submitInbound">入库</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const f = ref({ storeId: '' })
const warnDays = ref(30)
const batches = ref<any[]>([]); const exp = ref<any>(null); const loading = ref(false)
const stores = ref<any[]>([]); const items = ref<any[]>([])
const dlg = ref(false)
const blank = () => ({ storeId: '', itemId: '', qty: '', batchNo: '', productionDate: '', expiryDate: '' })
const form = ref<any>(blank())

async function loadBatches() {
  loading.value = true
  try { batches.value = (await api().listBatches({ storeId: f.value.storeId ? Number(f.value.storeId) : undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); batches.value = [] }
  finally { loading.value = false }
}
async function loadExpiring() {
  try { exp.value = await api().expiringBatches({ days: warnDays.value, storeId: f.value.storeId ? Number(f.value.storeId) : undefined }) } catch { exp.value = null }
}
function reload() { loadBatches(); loadExpiring() }
function openInbound() { form.value = blank(); if (f.value.storeId) form.value.storeId = Number(f.value.storeId); dlg.value = true }
async function submitInbound() {
  const v = form.value
  if (!v.storeId || !v.itemId) { ElMessage.warning('请选门店和物料'); return }
  if (!Number.isInteger(Number(v.qty)) || Number(v.qty) <= 0) { ElMessage.warning('数量须为正整数'); return }
  try { const r: any = await api().batchInbound({ storeId: Number(v.storeId), itemId: Number(v.itemId), qty: Number(v.qty), batchNo: v.batchNo || undefined, productionDate: v.productionDate || undefined, expiryDate: v.expiryDate || undefined }); ElMessage.success('已入库 ' + r.batchNo); dlg.value = false; reload() }
  catch (e: any) { ElMessage.error('入库失败：' + (e?.message || '')) }
}
async function consume(row: any) {
  try { const { value } = await ElMessageBox.prompt(`消耗批次 ${row.batch_no || row.batchNo}（余量 ${row.qty}）`, '批次消耗', { inputPattern: /^\d+$/, inputErrorMessage: '须为正整数', inputValue: '1' }); await api().batchConsume(row.batch_id || row.batchId, Number(value)); ElMessage.success('已消耗'); reload() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('消耗失败：' + (e?.message || '')) }
}
async function writeoff(row: any) {
  try { const { value } = await ElMessageBox.prompt('报损原因（整批余量出库）', '批次报损', { inputPlaceholder: '默认「过期」' }); await api().batchWriteoff(row.batch_id || row.batchId, value || '过期'); ElMessage.success('已报损'); reload() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('报损失败：' + (e?.message || '')) }
}
onMounted(async () => {
  try { stores.value = (await api().listStores()) as any[] || [] } catch { stores.value = [] }
  try { items.value = (await api().listItems({})) as any[] || [] } catch { items.value = [] }
  reload()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.mb { margin-bottom: 14px; }
.sec { font-weight: 600; margin: 6px 0 10px; color: var(--el-text-color-secondary); }
</style>
