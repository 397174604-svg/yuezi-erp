<template>
  <div>
    <div class="bar"><h2 class="ph">品控看板</h2><el-button size="small" :loading="loading" @click="load">刷新</el-button></div>
    <el-alert type="info" :closable="false" show-icon class="mb" title="部门品控平均分（越低越需改进）+ 员工品控积分榜。品控扣分同额扣员工积分（会议：品控挂钩绩效）。" />
    <div class="panes">
      <el-card shadow="never" class="pane" v-loading="loading">
        <template #header><b>部门品控平均分</b></template>
        <el-table :data="d ? d.deptScores : []" size="small" border empty-text="暂无检查记录">
          <el-table-column prop="dept" label="部门" min-width="120" />
          <el-table-column prop="avgScore" label="平均分" width="100" align="right">
            <template #default="{ row }"><span :class="Number(row.avgScore) < 90 ? 'bad' : 'ok'">{{ row.avgScore }}</span></template>
          </el-table-column>
          <el-table-column prop="checks" label="检查次数" width="100" align="right" />
        </el-table>
      </el-card>
      <el-card shadow="never" class="pane" v-loading="loading">
        <template #header><b>员工品控积分榜</b></template>
        <el-table :data="d ? d.staffPoints : []" size="small" border empty-text="暂无员工积分">
          <el-table-column type="index" label="#" width="48" />
          <el-table-column prop="name" label="员工" min-width="100" />
          <el-table-column prop="department" label="部门" width="110" />
          <el-table-column prop="points" label="积分" width="90" align="right">
            <template #default="{ row }"><span :class="Number(row.points) < 90 ? 'warn' : ''">{{ row.points }}</span></template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    <el-card shadow="never" class="pane monthly" v-loading="loading" v-if="monthly.rows.length">
      <template #header><b>部门月度品控真实得分</b><span class="src">奇德芬芳 2026 品控得分统计表（真实）</span></template>
      <el-table :data="monthly.rows" size="small" border>
        <el-table-column prop="dept" label="部门" min-width="110" fixed />
        <el-table-column v-for="m in monthly.months" :key="m" :label="m + '月'" width="76" align="right">
          <template #default="{ row }">
            <span v-if="row.m[m] != null" :class="Number(row.m[m]) < 95 ? 'warn' : 'ok'">{{ row.m[m] }}</span>
            <span v-else class="dash">—</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
const d = ref<any>(null); const loading = ref(false)
// 部门月度真实得分透视：dept 行 × 月 列（源自 qc_dept_scores，qc-scores.json 导入）
const monthly = computed(() => {
  const list: any[] = d.value?.deptMonthly || []
  const months = [...new Set(list.map((x: any) => Number(x.month)))].sort((a, b) => a - b)
  const byDept: Record<string, any> = {}
  for (const x of list) { (byDept[x.dept] = byDept[x.dept] || { dept: x.dept, m: {} }).m[Number(x.month)] = x.score }
  return { months, rows: Object.values(byDept) }
})
async function load() { loading.value = true; try { d.value = await api().qcBoard() } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false } }
onMounted(load)
</script>
<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; } .mb { margin-bottom: 12px; }
.panes { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pane { min-width: 0; }
.bad { color: var(--el-color-danger); font-weight: 700; } .ok { color: var(--el-color-success); font-weight: 600; } .warn { color: var(--el-color-warning); font-weight: 600; }
.monthly { margin-top: 12px; } .monthly .src { margin-left: 8px; font-size: 12px; color: var(--el-color-success); } .dash { color: var(--el-text-color-disabled); }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
