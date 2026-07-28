<template>
  <div>
    <div class="bar">
      <h2 class="ph">月嫂结算</h2>
      <el-form :inline="true" size="small">
        <el-form-item label="月嫂"><el-select v-model="q.nannyId" filterable placeholder="选择月嫂" style="width:160px"><el-option v-for="n in nannies" :key="n.nanny_id" :label="n.name || ('月嫂#' + n.nanny_id)" :value="n.nanny_id" /></el-select></el-form-item>
        <el-form-item label="起"><el-date-picker v-model="q.from" type="date" value-format="YYYY-MM-DD" style="width:140px" /></el-form-item>
        <el-form-item label="止"><el-date-picker v-model="q.to" type="date" value-format="YYYY-MM-DD" style="width:140px" /></el-form-item>
        <el-form-item><el-button type="primary" :disabled="!q.nannyId" @click="preview">预览工资条</el-button></el-form-item>
      </el-form>
    </div>

    <el-card v-if="pv" shadow="never" class="card">
      <template #header><b>{{ pv.nannyName }} 工资条</b><span class="muted"> {{ q.from }} ~ {{ q.to }} · {{ pv.dispatchCount }} 笔派工</span>
        <el-button style="float:right" type="success" size="small" :disabled="!q.from || !q.to" :loading="settling" @click="doSettle">生成结算单</el-button></template>
      <div class="settle">
        <el-statistic title="基础工费" :value="pv.baseFee" prefix="¥" />
        <el-statistic title="奖金合计" :value="pv.rewardTotal" prefix="¥" />
        <el-statistic title="惩罚合计" :value="pv.penalty" prefix="¥" />
        <el-statistic title="应发净额" :value="pv.net" prefix="¥" />
      </div>
      <el-table :data="pv.dispatches" border size="small" class="mt" empty-text="该周期无派工">
        <el-table-column prop="dispatch_id" label="派工#" width="80" />
        <el-table-column prop="customer_id" label="客户" width="80" />
        <el-table-column label="档期" min-width="200"><template #default="{ row }">{{ row.start_date }} ~ {{ row.end_date || '—' }}</template></el-table-column>
        <el-table-column label="工费" width="120" align="right"><template #default="{ row }">{{ money(row.fee) }}</template></el-table-column>
        <el-table-column prop="status" label="状态" width="90" />
      </el-table>
    </el-card>

    <div class="bar2"><h3 class="ph3">结算单历史</h3></div>
    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无结算单">
      <el-table-column prop="settle_no" label="结算单号" min-width="170" />
      <el-table-column prop="nanny_name" label="月嫂" width="110" />
      <el-table-column label="周期" min-width="200"><template #default="{ row }">{{ row.period_from }} ~ {{ row.period_to }}</template></el-table-column>
      <el-table-column label="基础工费" width="120" align="right"><template #default="{ row }">{{ money(row.base_fee) }}</template></el-table-column>
      <el-table-column label="奖/惩" width="130" align="right"><template #default="{ row }">{{ money(row.reward_total) }} / {{ money(row.penalty) }}</template></el-table-column>
      <el-table-column label="应发净额" width="130" align="right"><template #default="{ row }"><b>{{ money(row.net) }}</b></template></el-table-column>
      <el-table-column label="操作" width="90" fixed="right"><template #default="{ row }"><el-button link type="danger" size="small" @click="voidIt(row)">作废</el-button></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => (Number(v) < 0 ? '-¥' : '¥') + Math.abs(Number(v) || 0).toLocaleString()
const nannies = ref<any[]>([])
const q = ref<any>({ nannyId: '', from: new Date().toISOString().slice(0, 8) + '01', to: new Date().toISOString().slice(0, 10) })
const pv = ref<any>(null); const settling = ref(false)
const rows = ref<any[]>([]); const loading = ref(false)

async function preview() {
  try { pv.value = await api().previewNannySettlement({ nannyId: Number(q.value.nannyId), from: q.value.from || undefined, to: q.value.to || undefined }) }
  catch (e: any) { ElMessage.error('预览失败：' + (e?.message || '')) }
}
async function doSettle() {
  try {
    await ElMessageBox.confirm(`确认为 ${pv.value.nannyName} 生成 ${q.value.from}~${q.value.to} 结算单（应发 ${money(pv.value.net)}）？同周期不可重复结算`, '生成结算单')
    settling.value = true
    const r: any = await api().settleNanny({ nannyId: Number(q.value.nannyId), from: q.value.from, to: q.value.to })
    ElMessage.success(`已生成 ${r.settleNo}（应发 ${money(r.net)}）`); load()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('结算失败：' + (e?.message || '')) }
  finally { settling.value = false }
}
async function load() {
  loading.value = true
  try { rows.value = (await api().listNannySettlements({})) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
async function voidIt(row: any) {
  try { await ElMessageBox.confirm(`确认作废结算单 ${row.settle_no}？`, '作废'); await api().voidNannySettlement(row.settlement_id); ElMessage.success('已作废'); load() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('作废失败：' + (e?.message || '')) }
}
onMounted(async () => {
  try { nannies.value = (await api().listNannies({})) as any[] || [] } catch { nannies.value = [] }
  load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 16px; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.settle { display: flex; gap: 36px; }
.mt { margin-top: 12px; }
.bar2 { margin: 8px 0 10px; }
.ph3 { margin: 0; font-size: 15px; }
</style>
