<template>
  <div>
    <div class="bar">
      <h2 class="ph">积分规则</h2>
      <div><el-button @click="load">刷新</el-button><el-button type="primary" :loading="saving" @click="saveAll">保存全部</el-button></div>
    </div>
    <el-alert title="14 条积分获取途径，可逐条开关；计量「固定」按系数直接计分，「百分比」按 floor(消费额 × 系数%) 计分。门店级规则覆盖租户级。" type="info" :closable="false" show-icon class="mb" />
    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="加载中">
      <el-table-column prop="channel" label="获取途径" min-width="140" />
      <el-table-column label="启用" width="90"><template #default="{ row }"><el-switch v-model="row.enabled" /></template></el-table-column>
      <el-table-column label="计量" width="130"><template #default="{ row }"><el-select v-model="row.mode" size="small" style="width:100px"><el-option label="固定" value="固定" /><el-option label="百分比" value="百分比" /></el-select></template></el-table-column>
      <el-table-column label="系数" width="160"><template #default="{ row }"><el-input v-model="row.value" size="small" style="width:120px" :placeholder="row.mode === '百分比' ? '0~100' : '分值'" /></template></el-table-column>
      <el-table-column label="说明" min-width="170"><template #default="{ row }">{{ row.mode === '百分比' ? '消费额的 ' + (row.value || 0) + '%' : (row.value || 0) + ' 分/次' }}</template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const rows = ref<any[]>([]); const loading = ref(false); const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const data = (await api().listPointsRules()) as any[] || []
    rows.value = data.map(r => ({ channel: r.channel, enabled: !!r.enabled, mode: r.mode || '固定', value: r.value ?? 0 }))
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
async function saveAll() {
  saving.value = true; let n = 0
  try {
    for (const row of rows.value) {
      if (row.mode === '百分比' && Number(row.value) > 100) { ElMessage.warning(row.channel + '：百分比不可超 100'); saving.value = false; return }
      if (Number(row.value) < 0) { ElMessage.warning(row.channel + '：系数不可为负'); saving.value = false; return }
      await api().upsertPointsRule({ channel: row.channel, enabled: row.enabled, mode: row.mode, value: Number(row.value) || 0 })
      n++
    }
    ElMessage.success(`已保存 ${n} 条积分规则`); load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
  finally { saving.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.mb { margin-bottom: 12px; }
</style>
