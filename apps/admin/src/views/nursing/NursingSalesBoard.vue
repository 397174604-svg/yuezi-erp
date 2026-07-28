<template>
  <div>
    <div class="bar">
      <h2 class="ph">护理二次销售业绩</h2>
      <div class="ops">
        <el-input v-model="storeId" placeholder="门店ID(可空)" size="small" style="width:130px" clearable @change="load" />
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>
    <el-alert type="info" :closable="false" show-icon class="mb"
      title="护理人员在服务过程中二次销售产康/商品的业绩与提成（会议纪要：护理部二次销售业绩统计）。仅统计护理岗执行人；店长仅见本店。" />

    <div v-if="d" class="grid">
      <div class="kpi hero"><div class="t">护理二次销售总额</div><div class="v">¥{{ fmt(d.total.sales) }}</div></div>
      <div class="kpi"><div class="t">提成合计</div><div class="v ok">¥{{ fmt(d.total.handFee) }}</div></div>
      <div class="kpi"><div class="t">业绩合计</div><div class="v">¥{{ fmt(d.total.perf) }}</div></div>
      <div class="kpi"><div class="t">成交行数</div><div class="v">{{ d.total.lines }}</div></div>
      <div class="kpi"><div class="t">护理销售人数</div><div class="v">{{ d.total.staffCount }}</div></div>
    </div>

    <el-card shadow="never" v-loading="loading">
      <template #header><b>护理人员二次销售排行</b></template>
      <el-table :data="d ? d.list : []" size="small" stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="护理人员" width="120" />
        <el-table-column prop="role" label="岗位" width="100" />
        <el-table-column prop="lines" label="成交行" width="90" align="right" />
        <el-table-column prop="qty" label="件数" width="90" align="right" />
        <el-table-column label="销售额" width="130" align="right"><template #default="{ row }">¥{{ fmt(row.sales) }}</template></el-table-column>
        <el-table-column label="业绩额" width="130" align="right"><template #default="{ row }">¥{{ fmt(row.perf) }}</template></el-table-column>
        <el-table-column label="提成" width="120" align="right"><template #default="{ row }"><span class="ok">¥{{ fmt(row.handFee) }}</span></template></el-table-column>
      </el-table>
      <el-empty v-if="d && !d.list.length" description="暂无护理二次销售记录" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const d = ref<any>(null); const loading = ref(false); const storeId = ref('')
const fmt = (n: any) => Number(n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

async function load() {
  loading.value = true
  try { d.value = await api().getNursingSales({ storeId: storeId.value ? Number(storeId.value) : undefined }) }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; gap: 8px; }
.mb { margin-bottom: 12px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 14px; }
.kpi { background: var(--el-bg-color-overlay); border: 1px solid var(--el-border-color-lighter); border-radius: 8px; padding: 12px 14px; text-align: center; }
.kpi.hero { background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%); color: #fff; border: none; }
.kpi .t { font-size: 13px; color: var(--el-text-color-secondary); }
.kpi.hero .t { color: rgba(255,255,255,.85); }
.kpi .v { font-size: 24px; font-weight: 700; margin-top: 4px; }
.kpi .v.ok { color: var(--el-color-success); }
.ok { color: var(--el-color-success); font-weight: 600; }
</style>
