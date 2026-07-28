<template>
  <div>
    <h2 class="ph">库房管理</h2>

    <el-tabs v-model="activeTab" class="tabs">
      <!-- Tab1 库存总览 -->
      <el-tab-pane label="库存总览" name="stock">
        <el-table :data="invRows" v-loading="invLoading" border stripe empty-text="暂无库存">
          <el-table-column prop="name" label="品名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="store_id" label="门店#" width="90" align="center" />
          <el-table-column label="账面" width="110" align="right">
            <template #default="{ row }"><span class="num">{{ row.qty ?? '—' }}</span></template>
          </el-table-column>
          <el-table-column prop="warn_qty" label="预警线" width="100" align="right" />
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.low ? 'danger' : 'success'" effect="dark" size="small">{{ row.low ? '低库存' : '正常' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openMove(row, '入库')">入库</el-button>
              <el-button link type="warning" size="small" @click="openMove(row, '出库')">出库</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab2 出入库流水 -->
      <el-tab-pane label="出入库流水" name="movements">
        <el-form :inline="true" class="filters">
          <el-form-item>
            <el-select v-model="moveType" placeholder="类型" clearable style="width: 130px" @change="loadMovements">
              <el-option v-for="t in moveTypes" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item><el-button type="primary" @click="loadMovements">查询</el-button></el-form-item>
        </el-form>

        <el-table :data="moveRows" v-loading="moveLoading" border stripe empty-text="暂无流水">
          <el-table-column prop="created_at" label="时间" min-width="170" />
          <el-table-column label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.type === '入库' ? 'success' : 'warning'" effect="dark" size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="item_id" label="品项#" width="100" align="center" />
          <el-table-column label="数量" width="110" align="right">
            <template #default="{ row }"><span class="num">{{ row.qty ?? '—' }}</span></template>
          </el-table-column>
          <el-table-column prop="ref" label="单据号" min-width="160" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 入/出库对话框 -->
    <el-dialog v-model="moveVisible" :title="moveDir + ' · ' + (moveTarget?.name || '')" width="420px">
      <el-form label-width="80px">
        <el-form-item label="品项">{{ moveTarget?.name }}（#{{ moveTarget?.item_id }}）</el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="moveForm.qty" :min="1" :step="1" style="width: 180px" />
        </el-form-item>
        <el-form-item label="单据号">
          <el-input v-model="moveForm.ref" placeholder="单据号 / 备注" clearable style="width: 220px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moveVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMove">确认{{ moveDir }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const activeTab = ref('stock')

function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString()
}

// —— Tab1 库存总览 ——
const invRows = ref<any[]>([])
const invLoading = ref(false)

async function loadInventory() {
  invLoading.value = true
  try {
    const data: any = await api().listInventory({})
    invRows.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) {
    ElMessage.error('库存加载失败：' + (e?.message || ''))
    invRows.value = []
  } finally {
    invLoading.value = false
  }
}

// —— Tab2 出入库流水 ——
const moveRows = ref<any[]>([])
const moveLoading = ref(false)
const moveType = ref('')
const moveTypes = ['入库', '出库']

async function loadMovements() {
  moveLoading.value = true
  try {
    const data: any = await api().listStockMovements({ type: moveType.value || undefined, limit: 100 })
    moveRows.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) {
    ElMessage.error('流水加载失败：' + (e?.message || ''))
    moveRows.value = []
  } finally {
    moveLoading.value = false
  }
}

// —— 入/出库 ——
const moveVisible = ref(false)
const moveDir = ref<'入库' | '出库'>('入库')
const moveTarget = ref<any>(null)
const submitting = ref(false)
const moveForm = reactive<{ qty: number; ref: string }>({ qty: 1, ref: '' })

function openMove(row: any, dir: '入库' | '出库') {
  moveTarget.value = row
  moveDir.value = dir
  moveForm.qty = 1
  moveForm.ref = ''
  moveVisible.value = true
}

async function submitMove() {
  if (!moveTarget.value) return
  if (!moveForm.qty || moveForm.qty <= 0) { ElMessage.error('数量须大于 0'); return }
  submitting.value = true
  try {
    const itemId = moveTarget.value.item_id
    if (moveDir.value === '入库') {
      await api().stockInbound(itemId, moveForm.qty, moveForm.ref || undefined)
    } else {
      await api().stockOutbound(itemId, moveForm.qty, moveForm.ref || undefined)
    }
    ElMessage.success(moveDir.value + '成功')
    moveVisible.value = false
    await loadInventory()
    if (activeTab.value === 'movements') await loadMovements()
  } catch (e: any) {
    ElMessage.error(moveDir.value + '失败：' + (e?.message || ''))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadInventory()
  loadMovements()
})
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 14px; }
.tabs { margin-top: 4px; }
.filters { margin-bottom: 6px; }
.num { color: var(--gold-deep); font-weight: 600; }
</style>
