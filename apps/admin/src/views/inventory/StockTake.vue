<template>
  <div>
    <div class="bar">
      <h2 class="ph">库存盘点</h2>
      <div class="ops">
        <el-select v-model="f.status" placeholder="全部状态" clearable size="small" style="width:120px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
        <el-select v-model="newStore" placeholder="选择门店发起盘点" filterable size="small" style="width:200px"><el-option v-for="s in stores" :key="s.store_id" :label="s.name || ('门店#' + s.store_id)" :value="s.store_id" /></el-select>
        <el-button type="primary" :disabled="!newStore" @click="startTake">发起盘点</el-button>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无盘点单">
      <el-table-column prop="stocktake_no" label="盘点单号" min-width="170" />
      <el-table-column label="门店" width="120"><template #default="{ row }">{{ storeName(row.store_id) }}</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.status === '已完成' ? 'success' : (row.status === '已作废' ? 'danger' : 'warning')" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="170" />
      <el-table-column prop="committed_at" label="提交时间" min-width="170" />
      <el-table-column label="操作" width="130" fixed="right"><template #default="{ row }">
        <el-button link type="primary" size="small" @click="open(row)">{{ row.status === '盘点中' ? '录入/提交' : '查看' }}</el-button>
      </template></el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="cur ? cur.stocktake_no + '（' + cur.status + '）' : '盘点明细'" width="720px">
      <el-table :data="lines" border size="small" max-height="440" empty-text="该门店暂无库存品项">
        <el-table-column prop="item_name" label="品项" min-width="160"><template #default="{ row }">{{ row.item_name || ('物料#' + row.item_id) }}</template></el-table-column>
        <el-table-column prop="book_qty" label="账面" width="90" align="right" />
        <el-table-column label="实盘" width="130">
          <template #default="{ row }">
            <el-input v-if="editable" v-model="row._counted" size="small" style="width:100px" placeholder="未盘" />
            <span v-else>{{ row.counted_qty ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="差异" width="100" align="right"><template #default="{ row }">
          <span v-if="row.variance != null" :class="row.variance > 0 ? 'gain' : (row.variance < 0 ? 'loss' : '')">{{ row.variance > 0 ? '+' + row.variance : row.variance }}</span>
          <span v-else-if="editable && row._counted !== '' && row._counted != null" class="muted">{{ preview(row) }}</span>
          <span v-else>—</span>
        </template></el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="dlg = false">关闭</el-button>
        <el-button v-if="editable" type="primary" :loading="submitting" @click="submit">提交盘点（差异调整入库存）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const STATUS = ['盘点中', '已完成', '已作废']
const rows = ref<any[]>([]); const loading = ref(false)
const stores = ref<any[]>([])
const f = ref({ status: '' })
const newStore = ref<any>('')
const dlg = ref(false); const cur = ref<any>(null); const lines = ref<any[]>([]); const submitting = ref(false)
const editable = computed(() => cur.value?.status === '盘点中')
const storeName = (id: number) => stores.value.find(s => s.store_id === id)?.name || ('门店#' + id)
const preview = (row: any) => { const d = Number(row._counted) - Number(row.book_qty); return d > 0 ? '+' + d : String(d) }

async function load() {
  loading.value = true
  try { rows.value = (await api().listStocktakes({ status: f.value.status || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
async function startTake() {
  if (!newStore.value) return
  try { const r: any = await api().createStocktake({ storeId: Number(newStore.value) }); ElMessage.success(`已发起 ${r.stocktakeNo}（快照 ${r.lineCount} 个品项）`); newStore.value = ''; await load(); const row = rows.value.find(x => x.stocktake_id === r.stocktakeId); if (row) open(row) }
  catch (e: any) { ElMessage.error('发起失败：' + (e?.message || '')) }
}
async function open(row: any) {
  cur.value = row
  try { const d: any = await api().getStocktake(row.stocktake_id); lines.value = (d.lines || []).map((l: any) => ({ ...l, _counted: l.counted_qty != null ? String(l.counted_qty) : '' })); dlg.value = true }
  catch (e: any) { ElMessage.error('加载明细失败：' + (e?.message || '')) }
}
async function submit() {
  const dirty = lines.value.filter(l => l._counted !== '' && l._counted != null)
  if (!dirty.length) { ElMessage.warning('请先录入实盘数'); return }
  for (const l of dirty) { const n = Number(l._counted); if (!Number.isInteger(n) || n < 0) { ElMessage.warning(`${l.item_name || l.item_id} 实盘数须为非负整数`); return } }
  try {
    await ElMessageBox.confirm(`确认提交？将按差异调整 ${dirty.length} 个品项的库存（盘盈/盘亏写流水，不可撤销）`, '提交盘点')
    submitting.value = true
    for (const l of dirty) await api().countStocktake(cur.value.stocktake_id, { itemId: l.item_id, countedQty: Number(l._counted) })
    const r: any = await api().commitStocktake(cur.value.stocktake_id)
    ElMessage.success(`盘点完成：调整 ${r.adjustedLines} 项，盘盈 ${r.gain} / 盘亏 ${r.loss}`)
    dlg.value = false; load()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('提交失败：' + (e?.message || '')) }
  finally { submitting.value = false }
}
onMounted(async () => {
  try { stores.value = (await api().listStores()) as any[] || [] } catch { stores.value = [] }
  load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.gain { color: var(--el-color-success); font-weight: 600; }
.loss { color: var(--el-color-danger); font-weight: 600; }
.muted { color: var(--el-text-color-secondary); }
</style>
