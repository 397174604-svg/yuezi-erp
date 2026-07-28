<template>
  <div>
    <div class="bar">
      <h2 class="ph">跨店调拨</h2>
      <el-select v-model="f.status" placeholder="全部状态" clearable size="small" style="width:130px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
    </div>
    <el-card shadow="never" class="card">
      <el-form :inline="true" :model="form" size="small">
        <el-form-item label="调出门店"><el-select v-model="form.fromStore" filterable placeholder="选择" style="width:150px"><el-option v-for="s in stores" :key="s.store_id" :label="s.name || ('门店#' + s.store_id)" :value="s.store_id" /></el-select></el-form-item>
        <el-form-item label="调入门店"><el-select v-model="form.toStore" filterable placeholder="选择" style="width:150px"><el-option v-for="s in stores" :key="s.store_id" :label="s.name || ('门店#' + s.store_id)" :value="s.store_id" /></el-select></el-form-item>
        <el-form-item label="物料"><el-select v-model="form.itemId" filterable placeholder="选择" style="width:180px"><el-option v-for="it in items" :key="it.item_id" :label="it.name || ('物料#' + it.item_id)" :value="it.item_id" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input v-model="form.qty" style="width:90px" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" style="width:140px" /></el-form-item>
        <el-form-item><el-button type="primary" @click="submit">发起调拨</el-button></el-form-item>
      </el-form>
    </el-card>
    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无调拨单">
      <el-table-column prop="transfer_no" label="调拨单号" min-width="190" />
      <el-table-column label="调出 → 调入" min-width="190"><template #default="{ row }">{{ storeName(row.from_store) }} → {{ storeName(row.to_store) }}</template></el-table-column>
      <el-table-column label="物料" min-width="120"><template #default="{ row }">{{ itemName(row.item_id) }}</template></el-table-column>
      <el-table-column prop="qty" label="数量" width="80" align="right" />
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="TAG[row.status] || 'info'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="note" label="备注" min-width="120" show-overflow-tooltip />
      <el-table-column label="操作" width="150" fixed="right"><template #default="{ row }">
        <template v-if="row.status === '待收货'"><el-button link type="success" size="small" @click="receive(row)">收货</el-button><el-button link type="danger" size="small" @click="reject(row)">驳回</el-button></template>
      </template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const STATUS = ['待收货', '已收货', '已驳回']
const TAG: Record<string, string> = { 待收货: 'warning', 已收货: 'success', 已驳回: 'danger' }
const rows = ref<any[]>([]); const loading = ref(false)
const stores = ref<any[]>([]); const items = ref<any[]>([])
const f = ref({ status: '' })
const form = ref<any>({ fromStore: '', toStore: '', itemId: '', qty: '', note: '' })
const storeName = (id: number) => stores.value.find(s => s.store_id === id)?.name || ('门店#' + id)
const itemName = (id: number) => items.value.find(i => i.item_id === id)?.name || ('物料#' + id)

async function load() {
  loading.value = true
  try { rows.value = (await api().listStockTransfers({ status: f.value.status || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
async function submit() {
  const v = form.value
  if (!v.fromStore || !v.toStore) { ElMessage.warning('请选择调出/调入门店'); return }
  if (v.fromStore === v.toStore) { ElMessage.warning('调出/调入门店不能相同'); return }
  if (!v.itemId) { ElMessage.warning('请选择物料'); return }
  if (!Number.isInteger(Number(v.qty)) || Number(v.qty) <= 0) { ElMessage.warning('数量须为正整数'); return }
  try { await api().createTransfer({ fromStore: Number(v.fromStore), toStore: Number(v.toStore), itemId: Number(v.itemId), qty: Number(v.qty), note: v.note || undefined }); ElMessage.success('调拨已发起'); form.value.qty = ''; form.value.note = ''; load() }
  catch (e: any) { ElMessage.error('发起失败：' + (e?.message || '')) }
}
async function receive(row: any) {
  try { await api().receiveTransfer(row.transfer_id); ElMessage.success('已收货入库'); load() }
  catch (e: any) { ElMessage.error('收货失败：' + (e?.message || '')) }
}
async function reject(row: any) {
  try { const { value } = await ElMessageBox.prompt('驳回原因（退库回发出店）', '驳回', { inputPlaceholder: '可空' }); await api().rejectTransfer(row.transfer_id, { reason: value || '' }); ElMessage.success('已驳回退库'); load() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('驳回失败：' + (e?.message || '')) }
}
onMounted(async () => {
  try { stores.value = (await api().listStores()) as any[] || [] } catch { stores.value = [] }
  try { items.value = (await api().listItems({})) as any[] || [] } catch { items.value = [] }
  load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
</style>
