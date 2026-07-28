<template>
  <div>
    <div class="bar">
      <h2 class="ph">项目耗材 BOM</h2>
      <div class="ops">
        <el-select v-model="itemId" filterable placeholder="选项目" size="small" style="width:240px" @change="load">
          <el-option v-for="it in projects" :key="it.item_id" :label="it.name + '（' + it.domain + '）'" :value="it.item_id" />
        </el-select>
        <el-button size="small" type="primary" :disabled="!itemId" @click="addLine">+ 加耗材</el-button>
        <el-button size="small" :loading="saving" :disabled="!itemId" @click="save">保存 BOM</el-button>
      </div>
    </div>
    <el-alert type="info" :closable="false" show-icon class="mb"
      title="每个项目消耗的耗材+用量（来自产品配料表）。收银消费该项目时自动按 BOM 扣库存 + 耗材成本入财务（毛利更准）。库存不足降级不阻断收银。" />

    <el-card shadow="never" v-loading="loading">
      <el-table :data="lines" size="small" border>
        <el-table-column label="耗材" min-width="220">
          <template #default="{ row }">
            <el-select v-model="row.materialItemId" filterable placeholder="选耗材" size="small" style="width:100%">
              <el-option v-for="m in materials" :key="m.item_id" :label="m.name" :value="m.item_id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="用量" width="140"><template #default="{ row }"><el-input-number v-model="row.qty" :min="0.001" :step="1" size="small" /></template></el-table-column>
        <el-table-column label="单位" width="120"><template #default="{ row }"><el-input v-model="row.unit" size="small" placeholder="ml/g/个" /></template></el-table-column>
        <el-table-column label="" width="70"><template #default="{ $index }"><el-button link type="danger" size="small" @click="lines.splice($index, 1)">删</el-button></template></el-table-column>
      </el-table>
      <el-empty v-if="itemId && !lines.length" description="该项目暂无 BOM，点「加耗材」添加" :image-size="60" />
      <el-empty v-if="!itemId" description="请先选择项目" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const projects = ref<any[]>([]); const materials = ref<any[]>([])
const itemId = ref<number | ''>(''); const lines = ref<any[]>([])
const loading = ref(false); const saving = ref(false)

function addLine() { lines.value.push({ materialItemId: '', qty: 1, unit: 'ml' }) }

async function load() {
  if (!itemId.value) return
  loading.value = true
  try { const b = await api().getBom(itemId.value); lines.value = (b.lines || []).map((l: any) => ({ materialItemId: l.material_item_id, qty: Number(l.qty), unit: l.unit || '' })) }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false }
}
async function save() {
  saving.value = true
  try {
    const payload = lines.value.filter((l) => l.materialItemId && l.qty > 0).map((l) => ({ materialItemId: Number(l.materialItemId), qty: Number(l.qty), unit: l.unit || undefined }))
    await api().setBom(itemId.value, payload); ElMessage.success('已保存'); await load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) } finally { saving.value = false }
}
onMounted(async () => {
  try {
    const all = await api().listItems({})
    projects.value = (all || []).filter((i: any) => i.cat === '项目')
    materials.value = (all || []).filter((i: any) => i.cat === '耗材')
  } catch (e: any) { ElMessage.error('加载品项失败：' + (e?.message || '')) }
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; gap: 8px; }
.mb { margin-bottom: 12px; }
</style>
