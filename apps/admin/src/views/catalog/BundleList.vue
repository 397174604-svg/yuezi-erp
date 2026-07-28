<template>
  <div>
    <div class="bar">
      <h2 class="ph">套餐管理</h2>
      <el-button size="small" type="primary" @click="openNew">+ 新建套餐</el-button>
    </div>
    <el-alert type="info" :closable="false" show-icon class="mb" title="真实销售政策的套餐售卖单元（如「产后黄金三项套餐 7880/30次」）。构成行为套餐包含的项目及次数。" />

    <el-card shadow="never" v-loading="loading">
      <el-table :data="rows" size="small" border @row-click="openEdit">
        <el-table-column prop="bundle_id" label="ID" width="60" />
        <el-table-column prop="name" label="套餐名" min-width="180" />
        <el-table-column prop="domain" label="业务线" width="100" />
        <el-table-column label="打包价" width="120" align="right"><template #default="{ row }">¥{{ Number(row.price).toLocaleString() }}</template></el-table-column>
        <el-table-column prop="times" label="总次数" width="90" align="right" />
        <el-table-column prop="note" label="说明" min-width="220" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-dialog v-model="show" :title="form.bundleId ? '编辑套餐' : '新建套餐'" width="640">
      <el-form label-width="90px">
        <el-form-item label="套餐名"><el-input v-model="form.name" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="打包价"><el-input-number v-model="form.price" :min="0" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="总次数"><el-input-number v-model="form.times" :min="0" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="业务线"><el-select v-model="form.domain"><el-option label="月子" value="月子" /><el-option label="产康" value="产康" /><el-option label="科研美容" value="科研美容" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="说明"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="构成项目">
          <div style="width:100%">
            <div v-for="(l, i) in form.lines" :key="i" class="line">
              <el-select v-model="l.itemId" filterable placeholder="项目" size="small" style="width:60%"><el-option v-for="it in projects" :key="it.item_id" :label="it.name" :value="it.item_id" /></el-select>
              <el-input-number v-model="l.qty" :min="1" size="small" />
              <el-button link type="danger" size="small" @click="form.lines.splice(i, 1)">删</el-button>
            </div>
            <el-button size="small" @click="form.lines.push({ itemId: '', qty: 1 })">+ 加项目</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="show = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const rows = ref<any[]>([]); const projects = ref<any[]>([]); const loading = ref(false); const saving = ref(false)
const show = ref(false)
const form = ref<any>({ bundleId: null, name: '', price: 0, times: 0, domain: '产康', note: '', lines: [] })

async function load() {
  loading.value = true
  try { rows.value = await api().listBundles({}) } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false }
}
function openNew() { form.value = { bundleId: null, name: '', price: 0, times: 0, domain: '产康', note: '', lines: [] }; show.value = true }
async function openEdit(row: any) {
  try { const d = await api().getBundle(row.bundle_id); form.value = { bundleId: d.bundle_id, name: d.name, price: Number(d.price), times: d.times, domain: d.domain, note: d.note, lines: (d.lines || []).map((l: any) => ({ itemId: l.item_id, qty: Number(l.qty) })) }; show.value = true }
  catch (e: any) { ElMessage.error(e?.message || '') }
}
async function save() {
  saving.value = true
  try {
    const payload = { name: form.value.name, price: Number(form.value.price), times: form.value.times ? Number(form.value.times) : undefined, domain: form.value.domain, note: form.value.note, lines: form.value.lines.filter((l: any) => l.itemId).map((l: any) => ({ itemId: Number(l.itemId), qty: Number(l.qty) })) }
    if (form.value.bundleId) await api().updateBundle(form.value.bundleId, payload); else await api().createBundle(payload)
    ElMessage.success('已保存'); show.value = false; await load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) } finally { saving.value = false }
}
onMounted(async () => { await load(); try { projects.value = (await api().listItems({})).filter((i: any) => i.cat === '项目') } catch {} })
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.mb { margin-bottom: 12px; }
.line { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
</style>
