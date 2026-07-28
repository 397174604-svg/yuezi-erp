<template>
  <div>
    <div class="bar">
      <h2 class="ph">供应商管理</h2>
      <div class="ops">
        <el-input v-model="f.keyword" placeholder="名称/联系人/电话" size="small" style="width:180px" clearable @keyup.enter="load" />
        <el-select v-model="f.status" placeholder="全部状态" clearable size="small" style="width:110px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
        <el-button size="small" @click="load">查询</el-button>
        <el-button type="primary" size="small" @click="openCreate">新建供应商</el-button>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无供应商">
      <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="contact" label="联系人" width="110" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.status === '启用' ? 'success' : 'danger'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="180" fixed="right"><template #default="{ row }">
        <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
        <el-button link :type="row.status === '启用' ? 'warning' : 'success'" size="small" @click="toggle(row)">{{ row.status === '启用' ? '停用' : '启用' }}</el-button>
        <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
      </template></el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="editId ? '编辑供应商' : '新建供应商'" width="520px">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" :loading="saving" @click="submit">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const STATUS = ['启用', '停用']
const rows = ref<any[]>([]); const loading = ref(false)
const f = ref({ keyword: '', status: '' })
const dlg = ref(false); const saving = ref(false); const editId = ref<any>(null)
const blank = () => ({ name: '', contact: '', phone: '', address: '', note: '' })
const form = ref<any>(blank())

async function load() {
  loading.value = true
  try { rows.value = (await api().listSuppliers({ keyword: f.value.keyword || undefined, status: f.value.status || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
function openCreate() { editId.value = null; form.value = blank(); dlg.value = true }
function openEdit(row: any) { editId.value = row.supplier_id; form.value = { name: row.name, contact: row.contact ?? '', phone: row.phone ?? '', address: row.address ?? '', note: row.note ?? '' }; dlg.value = true }
async function submit() {
  if (!form.value.name?.trim()) { ElMessage.warning('名称必填'); return }
  saving.value = true
  try {
    if (editId.value) { await api().updateSupplier(editId.value, { name: form.value.name, contact: form.value.contact, phone: form.value.phone, address: form.value.address, note: form.value.note }); ElMessage.success('已更新') }
    else { await api().createSupplier({ name: form.value.name, contact: form.value.contact || undefined, phone: form.value.phone || undefined, address: form.value.address || undefined, note: form.value.note || undefined }); ElMessage.success('已创建') }
    dlg.value = false; load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
  finally { saving.value = false }
}
async function toggle(row: any) {
  try { await api().setSupplierStatus(row.supplier_id, row.status === '启用' ? '停用' : '启用'); load() }
  catch (e: any) { ElMessage.error('操作失败：' + (e?.message || '')) }
}
async function remove(row: any) {
  try { await ElMessageBox.confirm(`确认删除供应商「${row.name}」？`, '删除'); await api().removeSupplier(row.supplier_id); ElMessage.success('已删除'); load() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('删除失败：' + (e?.message || '')) }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
</style>
