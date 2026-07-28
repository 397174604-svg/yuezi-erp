<template>
  <div>
    <div class="bar">
      <h2 class="ph">内容运营（课堂/社区/公告）</h2>
      <div class="ops">
        <el-select v-model="f.kind" placeholder="全部类型" clearable size="small" style="width:110px" @change="load"><el-option v-for="k in KIND" :key="k" :label="k" :value="k" /></el-select>
        <el-select v-model="f.status" placeholder="全部状态" clearable size="small" style="width:110px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
        <el-button type="primary" @click="openCreate">{{ isMgr ? '发布内容' : '投稿(草稿)' }}</el-button>
      </div>
    </div>
    <el-alert v-if="!isMgr" title="你的投稿将保存为草稿，经管理层审核后发布。" type="info" :closable="false" show-icon class="rev-tip" />

    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无内容">
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" width="90"><template #default="{ row }"><el-tag size="small" effect="plain">{{ row.kind }}</el-tag></template></el-table-column>
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="TAG[row.status] || 'info'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="likes" label="点赞" width="80" align="right" />
      <el-table-column prop="created_at" label="发布时间" min-width="160" />
      <el-table-column label="操作" width="220" fixed="right"><template #default="{ row }">
        <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
        <template v-if="isMgr">
          <el-button v-if="row.status !== '已发布'" link type="success" size="small" @click="setStatus(row, '已发布')">发布</el-button>
          <el-button v-else link type="warning" size="small" @click="setStatus(row, '下架')">下架</el-button>
          <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
        <span v-else-if="row.status === '草稿'" class="rev">待管理层审核</span>
      </template></el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="editId ? '编辑内容' : '发布内容'" width="640px">
      <el-form :model="form" label-width="70px" size="small">
        <el-form-item label="类型"><el-select v-model="form.kind" style="width:160px"><el-option v-for="k in KIND" :key="k" :label="k" :value="k" /></el-select></el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="正文"><el-input v-model="form.body" type="textarea" :rows="6" /></el-form-item>
        <el-form-item v-if="isMgr" label="状态"><el-select v-model="form.status" style="width:160px"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select></el-form-item>
        <el-form-item v-else label="状态"><el-tag type="info" effect="plain" size="small">草稿(待审核发布)</el-tag></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" :loading="saving" @click="submit">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
// 发布/下架/删除=管理层复核动作;非管理层(产康师/销售顾问)只可投稿草稿,由管理层审核后发布(后端 communityService 亦强制)
const isMgr = computed(() => auth.isManager)

const KIND = ['课堂', '社区', '公告']
const STATUS = ['已发布', '草稿', '下架']
const TAG: Record<string, string> = { 已发布: 'success', 草稿: 'info', 下架: 'danger' }
const rows = ref<any[]>([]); const loading = ref(false)
const f = ref({ kind: '', status: '' })
const dlg = ref(false); const saving = ref(false); const editId = ref<any>(null)
const blank = () => ({ kind: '课堂', title: '', body: '', status: auth.isManager ? '已发布' : '草稿' })
const form = ref<any>(blank())

async function load() {
  loading.value = true
  try { rows.value = (await api().listPosts({ kind: f.value.kind || undefined, status: f.value.status || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
function openCreate() { editId.value = null; form.value = blank(); dlg.value = true }
function openEdit(row: any) { editId.value = row.post_id; form.value = { kind: row.kind, title: row.title ?? '', body: row.body ?? '', status: row.status ?? '已发布' }; dlg.value = true }
async function submit() {
  if (!form.value.title?.trim()) { ElMessage.warning('标题必填'); return }
  saving.value = true
  try {
    if (editId.value) { await api().updatePost(editId.value, { title: form.value.title, body: form.value.body, kind: form.value.kind, status: form.value.status }); ElMessage.success('已更新') }
    else { await api().createPost({ title: form.value.title, body: form.value.body, kind: form.value.kind, status: form.value.status }); ElMessage.success('已发布') }
    dlg.value = false; load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
  finally { saving.value = false }
}
async function setStatus(row: any, status: string) {
  try { await api().updatePost(row.post_id, { status }); ElMessage.success(status === '已发布' ? '已发布' : '已下架'); load() }
  catch (e: any) { ElMessage.error('操作失败：' + (e?.message || '')) }
}
async function remove(row: any) {
  try { await ElMessageBox.confirm(`确认删除「${row.title}」？`, '删除'); await api().removePost(row.post_id); ElMessage.success('已删除'); load() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('删除失败：' + (e?.message || '')) }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.rev-tip { margin-bottom: 12px; }
.rev { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
