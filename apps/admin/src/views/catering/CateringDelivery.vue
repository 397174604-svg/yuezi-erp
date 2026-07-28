<template>
  <div>
    <div class="bar"><h2 class="ph">订餐配送</h2></div>
    <el-tabs v-model="tab" @tab-change="onTab">
      <!-- 今日待配送 -->
      <el-tab-pane label="待配送看板" name="pending">
        <el-card shadow="never" class="card">
          <el-form :inline="true" size="small">
            <el-form-item label="配送日"><el-date-picker v-model="p.date" type="date" value-format="YYYY-MM-DD" style="width:150px" /></el-form-item>
            <el-form-item label="门店ID"><el-input v-model="p.storeId" style="width:90px" placeholder="可空" clearable /></el-form-item>
            <el-form-item><el-button type="primary" @click="loadPending">查询</el-button></el-form-item>
            <el-form-item><span class="muted">共 {{ pending.length }} 餐待配送</span></el-form-item>
          </el-form>
          <el-table :data="pending" v-loading="pLoading" border stripe size="small" empty-text="该日无待配送餐单">
            <el-table-column prop="meal_type" label="餐次" width="90" />
            <el-table-column prop="customer_name" label="客户" min-width="110"><template #default="{ row }">{{ row.customer_name || ('客户#' + row.customer_id) }}</template></el-table-column>
            <el-table-column label="菜品" min-width="200"><template #default="{ row }">{{ dishes(row.dishes_json) }}</template></el-table-column>
            <el-table-column prop="calorie" label="热量" width="90" align="right"><template #default="{ row }">{{ row.calorie != null ? row.calorie + ' kcal' : '—' }}</template></el-table-column>
            <el-table-column label="操作" width="120" fixed="right"><template #default="{ row }">
              <el-button link type="success" size="small" :loading="row._ing" @click="mark(row)">标记已配送</el-button>
            </template></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 配送历史 -->
      <el-tab-pane label="配送历史" name="history">
        <el-card shadow="never" class="card">
          <el-form :inline="true" size="small">
            <el-form-item label="起"><el-date-picker v-model="h.from" type="date" value-format="YYYY-MM-DD" style="width:140px" /></el-form-item>
            <el-form-item label="止"><el-date-picker v-model="h.to" type="date" value-format="YYYY-MM-DD" style="width:140px" /></el-form-item>
            <el-form-item label="门店ID"><el-input v-model="h.storeId" style="width:90px" placeholder="可空" clearable /></el-form-item>
            <el-form-item><el-button type="primary" @click="loadHistory">查询</el-button></el-form-item>
          </el-form>
          <el-table :data="history" v-loading="hLoading" border stripe size="small" empty-text="暂无配送记录">
            <el-table-column prop="meal_date" label="配送日" width="120" />
            <el-table-column prop="meal_type" label="餐次" width="90" />
            <el-table-column prop="customer_name" label="客户" min-width="110"><template #default="{ row }">{{ row.customer_name || ('客户#' + row.customer_id) }}</template></el-table-column>
            <el-table-column prop="calorie" label="热量" width="100" align="right"><template #default="{ row }">{{ row.calorie != null ? row.calorie + ' kcal' : '—' }}</template></el-table-column>
            <el-table-column label="状态" width="90"><template #default><el-tag type="success" size="small" effect="dark">已配送</el-tag></template></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const today = new Date().toISOString().slice(0, 10)
const tab = ref('pending')
const p = ref({ date: today, storeId: '' })
const pending = ref<any[]>([]); const pLoading = ref(false)
const h = ref({ from: today, to: today, storeId: '' })
const history = ref<any[]>([]); const hLoading = ref(false)

function dishes(j: any) { try { const a = JSON.parse(j || '[]'); return Array.isArray(a) ? a.join('、') : String(j || '') } catch { return String(j || '') } }

async function loadPending() {
  pLoading.value = true
  try { const r: any = await api().listTodayDeliveries({ mealDate: p.value.date || undefined, storeId: p.value.storeId ? Number(p.value.storeId) : undefined }); pending.value = (r?.items || []).map((x: any) => ({ ...x, _ing: false })) }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); pending.value = [] }
  finally { pLoading.value = false }
}
async function mark(row: any) {
  row._ing = true
  try { await api().markDelivered(row.plan_id); ElMessage.success('已标记配送'); pending.value = pending.value.filter((x) => x.plan_id !== row.plan_id) }
  catch (e: any) { ElMessage.error('标记失败：' + (e?.message || '')); row._ing = false }
}
async function loadHistory() {
  hLoading.value = true
  try { history.value = (await api().listDeliveryHistory({ from: h.value.from || undefined, to: h.value.to || undefined, storeId: h.value.storeId ? Number(h.value.storeId) : undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); history.value = [] }
  finally { hLoading.value = false }
}
function onTab(name: string) { if (name === 'history') loadHistory() }
onMounted(loadPending)
</script>

<style scoped>
.bar { display: flex; align-items: center; margin-bottom: 8px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
