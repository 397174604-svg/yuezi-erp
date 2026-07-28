<template>
  <div>
    <div class="bar">
      <h2 class="ph">采购管理</h2>
      <div class="ops">
        <el-select v-model="f.status" placeholder="全部状态" clearable size="small" style="width:120px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
        <el-button type="primary" @click="openCreate">新建采购单</el-button>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无采购单">
      <el-table-column prop="po_no" label="采购单号" min-width="170" />
      <el-table-column label="门店" width="110"><template #default="{ row }">{{ storeName(row.store_id) }}</template></el-table-column>
      <el-table-column prop="supplier" label="供应商" min-width="120" show-overflow-tooltip />
      <el-table-column label="金额" width="120" align="right"><template #default="{ row }">{{ money(row.total_cost) }}</template></el-table-column>
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="TAG[row.status] || 'info'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="170" />
      <el-table-column label="操作" width="190" fixed="right"><template #default="{ row }">
        <el-button link type="primary" size="small" @click="openDetail(row)">查看</el-button>
        <template v-if="row.status === '待入库'">
          <el-button link type="success" size="small" @click="receive(row)">收货入库</el-button>
          <el-button link type="danger" size="small" @click="cancel(row)">取消</el-button>
        </template>
      </template></el-table-column>
    </el-table>

    <!-- 新建采购单 -->
    <el-dialog v-model="dlg" title="新建采购单" width="720px">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="采购门店"><el-select v-model="form.storeId" filterable placeholder="选择" style="width:200px"><el-option v-for="s in stores" :key="s.store_id" :label="s.name || ('门店#' + s.store_id)" :value="s.store_id" /></el-select></el-form-item>
        <el-form-item label="供应商"><el-select v-model="form.supplierId" filterable clearable placeholder="选择供应商(可空)" style="width:260px"><el-option v-for="s in suppliers" :key="s.supplier_id" :label="s.name" :value="s.supplier_id" /></el-select></el-form-item>
        <el-form-item label="采购明细">
          <div class="lines">
            <div v-for="(ln, idx) in form.lines" :key="idx" class="line">
              <el-select v-model="ln.itemId" filterable placeholder="物料" size="small" style="width:200px"><el-option v-for="it in items" :key="it.item_id" :label="it.name || ('物料#' + it.item_id)" :value="it.item_id" /></el-select>
              <el-input v-model="ln.qty" size="small" style="width:90px" placeholder="数量" />
              <el-input v-model="ln.unitCost" size="small" style="width:100px" placeholder="单价" />
              <span class="sub">{{ money((Number(ln.qty) || 0) * (Number(ln.unitCost) || 0)) }}</span>
              <el-button link type="danger" size="small" @click="form.lines.splice(idx, 1)" :disabled="form.lines.length <= 1">删</el-button>
            </div>
            <el-button link type="primary" size="small" @click="form.lines.push({ itemId: '', qty: '', unitCost: '' })">+ 加一行</el-button>
          </div>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" style="width:320px" /></el-form-item>
        <el-form-item label="合计"><b class="total">{{ money(total) }}</b></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" :loading="saving" @click="submit">提交（待入库）</el-button></template>
    </el-dialog>

    <!-- 详情 -->
    <el-dialog v-model="detailDlg" :title="cur ? cur.po_no + '（' + cur.status + '）' : '采购单'" width="640px">
      <p v-if="cur" class="meta">门店 {{ storeName(cur.store_id) }} · 供应商 {{ cur.supplier || '—' }} · 合计 {{ money(cur.total_cost) }}</p>
      <el-table :data="curLines" border size="small" empty-text="无明细">
        <el-table-column prop="item_name" label="物料" min-width="160"><template #default="{ row }">{{ row.item_name || ('物料#' + row.item_id) }}</template></el-table-column>
        <el-table-column prop="qty" label="数量" width="90" align="right" />
        <el-table-column label="单价" width="100" align="right"><template #default="{ row }">{{ money(row.unit_cost) }}</template></el-table-column>
        <el-table-column label="小计" width="110" align="right"><template #default="{ row }">{{ money(Number(row.qty) * Number(row.unit_cost)) }}</template></el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const STATUS = ['待入库', '已入库', '已取消']
const TAG: Record<string, string> = { 待入库: 'warning', 已入库: 'success', 已取消: 'danger' }
const money = (v: any) => '¥' + (Math.round((Number(v) || 0) * 100) / 100).toLocaleString()
const rows = ref<any[]>([]); const loading = ref(false)
const stores = ref<any[]>([]); const items = ref<any[]>([]); const suppliers = ref<any[]>([])
const f = ref({ status: '' })
const storeName = (id: number) => stores.value.find(s => s.store_id === id)?.name || ('门店#' + id)

const dlg = ref(false); const saving = ref(false)
const blank = () => ({ storeId: '', supplierId: '', note: '', lines: [{ itemId: '', qty: '', unitCost: '' }] as any[] })
const form = ref<any>(blank())
const total = computed(() => form.value.lines.reduce((s: number, l: any) => s + (Number(l.qty) || 0) * (Number(l.unitCost) || 0), 0))

const detailDlg = ref(false); const cur = ref<any>(null); const curLines = ref<any[]>([])

async function load() {
  loading.value = true
  try { rows.value = (await api().listPurchases({ status: f.value.status || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
function openCreate() { form.value = blank(); dlg.value = true }
async function submit() {
  const v = form.value
  if (!v.storeId) { ElMessage.warning('请选择采购门店'); return }
  const lines = v.lines.filter((l: any) => l.itemId && Number(l.qty) > 0).map((l: any) => ({ itemId: Number(l.itemId), qty: Number(l.qty), unitCost: Number(l.unitCost) || 0 }))
  if (!lines.length) { ElMessage.warning('请填写至少一条有效明细'); return }
  for (const l of lines) if (!Number.isInteger(l.qty)) { ElMessage.warning('采购数量须为整数'); return }
  saving.value = true
  try { const r: any = await api().createPurchase({ storeId: Number(v.storeId), supplierId: v.supplierId ? Number(v.supplierId) : undefined, note: v.note || undefined, lines }); ElMessage.success(`已建 ${r.poNo}（合计 ${money(r.totalCost)}）`); dlg.value = false; load() }
  catch (e: any) { ElMessage.error('提交失败：' + (e?.message || '')) }
  finally { saving.value = false }
}
async function receive(row: any) {
  try { await ElMessageBox.confirm(`确认 ${row.po_no} 收货入库？将按明细增加库存（不可撤销）`, '收货入库'); await api().receivePurchase(row.po_id); ElMessage.success('已收货入库'); load() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('收货失败：' + (e?.message || '')) }
}
async function cancel(row: any) {
  try { await ElMessageBox.confirm(`确认取消 ${row.po_no}？`, '取消采购单'); await api().cancelPurchase(row.po_id); ElMessage.success('已取消'); load() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('取消失败：' + (e?.message || '')) }
}
async function openDetail(row: any) {
  cur.value = row
  try { const d: any = await api().getPurchase(row.po_id); curLines.value = d.lines || []; detailDlg.value = true }
  catch (e: any) { ElMessage.error('加载明细失败：' + (e?.message || '')) }
}
onMounted(async () => {
  try { stores.value = (await api().listStores()) as any[] || [] } catch { stores.value = [] }
  try { items.value = (await api().listItems({})) as any[] || [] } catch { items.value = [] }
  try { suppliers.value = (await api().listSuppliers({ status: '启用' })) as any[] || [] } catch { suppliers.value = [] }
  load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.lines { display: flex; flex-direction: column; gap: 8px; }
.line { display: flex; align-items: center; gap: 8px; }
.line .sub { width: 90px; text-align: right; color: var(--el-text-color-secondary); font-size: 12px; }
.total { font-size: 18px; color: var(--el-color-primary); }
.meta { color: var(--el-text-color-secondary); font-size: 13px; margin: 0 0 10px; }
</style>
