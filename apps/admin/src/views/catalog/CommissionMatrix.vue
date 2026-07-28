<template>
  <div>
    <div class="bar">
      <h2 class="ph">提成方案矩阵</h2>
      <div><el-button @click="load">刷新</el-button><el-button type="primary" :loading="saving" @click="saveAll">保存全部</el-button></div>
    </div>
    <el-alert title="按 奖金维度 × 渠道(客户/散客) × 角色(前台/产康师/店长) 配置提成；金额为固定额或百分比，0 表示不发。" type="info" :closable="false" show-icon class="mb" />
    <el-table :data="rows" v-loading="loading" border size="small" :span-method="spanDim" empty-text="加载中">
      <el-table-column prop="dim" label="奖金维度" width="130" />
      <el-table-column prop="channel" label="渠道" width="80" />
      <el-table-column v-for="role in roles" :key="role" :label="role" min-width="170">
        <template #default="{ row }">
          <div class="cell">
            <el-input v-model="row[role].amount" size="small" style="width:90px" placeholder="0" />
            <el-select v-model="row[role].unit" size="small" style="width:72px"><el-option label="固定" value="固定" /><el-option label="%" value="百分比" /></el-select>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="policy">
      <el-card shadow="never" class="pol">
        <template #header><b>购疗程赠项目规则</b><span class="src">真实销售政策</span></template>
        <ul class="rules" v-if="promos.length"><li v-for="p in promos" :key="p.rule_id">{{ p.rule }}</li></ul>
        <el-empty v-else description="暂无" :image-size="40" />
      </el-card>
      <el-card shadow="never" class="pol">
        <template #header><b>销售奖励阶梯</b><span class="src">真实销售政策</span></template>
        <el-table :data="rewards" size="small" border v-if="rewards.length">
          <el-table-column prop="name" label="奖励项" min-width="150" />
          <el-table-column prop="amount" label="奖励(元)" width="90" />
          <el-table-column prop="cond_text" label="条件" min-width="220" />
        </el-table>
        <el-empty v-else description="暂无" :image-size="40" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

// 角色/渠道以接口返回的 m.roles/m.channels 为准(与 dims 一样数据驱动);内置值仅作首屏兜底,防后端改了前端矩阵漏列丢配
const roles = ref<string[]>(['前台', '产康师', '店长'])
const channels = ref<string[]>(['客户', '散客'])
const dims = ref<string[]>([])
const rows = ref<any[]>([])
const promos = ref<any[]>([])
const rewards = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)

function blankRow(dim: string, channel: string) {
  const r: any = { dim, channel }
  for (const role of roles.value) r[role] = { amount: '', unit: '固定' }
  return r
}

async function load() {
  loading.value = true
  try {
    const m: any = await api().commissionMatrix()
    dims.value = m?.dims || []
    if (m?.roles?.length) roles.value = m.roles       // 数据驱动：列头/渠道以接口为准
    if (m?.channels?.length) channels.value = m.channels
    const grid: any[] = []
    for (const dim of dims.value) for (const channel of channels.value) grid.push(blankRow(dim, channel))
    for (const rule of (m?.rules || [])) {
      const row = grid.find(g => g.dim === rule.bonus_dim && g.channel === rule.channel)
      if (row && row[rule.role]) { row[rule.role].amount = String(rule.amount ?? ''); row[rule.role].unit = rule.unit || '固定' }
    }
    rows.value = grid
    // 真实销售政策：促销规则 + 销售奖励阶梯（rehab-catalog.json 导入，只读）
    try { promos.value = (await api().promoRules()) || [] } catch { promos.value = [] }
    try { rewards.value = (await api().salesRewards()) || [] } catch { rewards.value = [] }
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}

// 同一维度的 2 行渠道合并首列
function spanDim({ row, column, rowIndex }: any) {
  if (column.property !== 'dim') return
  return rowIndex % 2 === 0 ? { rowspan: 2, colspan: 1 } : { rowspan: 0, colspan: 0 }
}

async function saveAll() {
  saving.value = true
  let ok = 0; const failed: string[] = []
  try {
    for (const row of rows.value) for (const role of roles.value) {
      const cell = row[role]
      if (cell.amount === '' || !(Number(cell.amount) >= 0)) continue
      // 逐格独立保存：单格失败不中断其余（防批量保存半途而废、静默丢改）
      try { await api().upsertCommissionRule({ bonusDim: row.dim, channel: row.channel, role, amount: Number(cell.amount), unit: cell.unit }); ok++ }
      catch { failed.push(`${row.dim}/${row.channel}/${role}`) }
    }
    if (failed.length) ElMessage.warning(`已保存 ${ok} 项，${failed.length} 项失败：${failed.slice(0, 3).join('、')}${failed.length > 3 ? '…' : ''}`)
    else ElMessage.success(`已保存 ${ok} 项提成规则`)
    load()
  } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.mb { margin-bottom: 12px; }
.cell { display: flex; gap: 6px; }
.policy { display: grid; grid-template-columns: 1fr 1.3fr; gap: 12px; margin-top: 14px; }
.pol .src { margin-left: 8px; font-size: 12px; color: var(--el-color-success); }
.rules { margin: 0; padding-left: 18px; }
.rules li { font-size: 13px; line-height: 1.9; }
@media (max-width: 900px) { .policy { grid-template-columns: 1fr; } }
</style>
