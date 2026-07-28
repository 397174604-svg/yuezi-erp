<template>
  <div>
    <div class="bar">
      <h2 class="ph">员工与组织</h2>
      <div class="filters">
        <el-form :inline="true">
          <el-form-item>
            <el-input v-model="f.department" placeholder="部门关键字" clearable style="width: 160px" @keyup.enter="reload" />
          </el-form-item>
          <el-form-item>
            <el-select v-model="f.status" placeholder="状态" clearable style="width: 120px">
              <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item><el-button type="primary" @click="reload">查询</el-button></el-form-item>
          <el-form-item><el-button type="primary" plain @click="openCreate">新增员工</el-button></el-form-item>
        </el-form>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe class="tbl" empty-text="暂无员工">
      <el-table-column prop="name" label="姓名" min-width="100" show-overflow-tooltip />
      <el-table-column prop="phone" label="手机" min-width="130" />
      <el-table-column prop="role" label="角色" width="120" />
      <el-table-column prop="position" label="职位" width="120" />
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column label="门店" width="110">
        <template #default="{ row }">{{ row.store_id != null ? '门店#' + row.store_id : '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '在职' ? 'success' : 'danger'" effect="dark" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" size="small" @click="resetPwd(row)">重置密码</el-button>
          <el-button
            link
            :type="row.status === '在职' ? 'danger' : 'success'"
            size="small"
            @click="toggleStatus(row)"
          >{{ row.status === '在职' ? '停用' : '启用' }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="page" :page-count="pageCount" @current-change="onPage" />
    </div>

    <!-- 新增 / 编辑员工 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑员工' : '新增员工'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="员工姓名" />
        </el-form-item>
        <el-form-item label="手机" prop="phone">
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="选择角色" clearable style="width: 100%">
            <el-option v-for="r in roles" :key="r.role_id" :label="r.name" :value="r.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="职位" prop="position">
          <el-input v-model="form.position" placeholder="职位" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="form.department" placeholder="部门" />
        </el-form-item>
        <el-form-item label="门店" prop="storeId">
          <el-input v-model="form.storeId" placeholder="门店ID" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" placeholder="状态" style="width: 100%">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { api } from '@/api'

const statuses = ['在职', '离职']

const rows = ref<any[]>([])
const loading = ref(false)
const f = reactive<{ department: string; status: string }>({ department: '', status: '' })
const page = ref(1)
const pageSize = 20
const hasNext = ref(false)
const pageCount = computed(() => (hasNext.value ? page.value + 1 : page.value))

const roles = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const data: any = await api().listStaff({
      department: f.department || undefined,
      status: f.status || undefined,
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    })
    const list = Array.isArray(data) ? data : (data?.rows || [])
    rows.value = list
    hasNext.value = list.length === pageSize
  } catch (e: any) {
    ElMessage.error('员工列表加载失败：' + (e?.message || ''))
    rows.value = []
    hasNext.value = false
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }
function onPage(p: number) { page.value = p; load() }

async function loadRoles() {
  try {
    const data: any = await api().listRoles()
    roles.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) {
    ElMessage.error('角色加载失败：' + (e?.message || ''))
  }
}

// —— 新增 / 编辑 ——
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref(false)
const editingId = ref<any>(null)
const formRef = ref<FormInstance>()
const form = reactive<{ name: string; phone: string; role: string; position: string; department: string; storeId: string; status: string }>({
  name: '', phone: '', role: '', position: '', department: '', storeId: '', status: '在职',
})
const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

function resetForm() {
  form.name = ''
  form.phone = ''
  form.role = ''
  form.position = ''
  form.department = ''
  form.storeId = ''
  form.status = '在职'
}

function openCreate() {
  editing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function openEdit(row: any) {
  editing.value = true
  editingId.value = row.staff_id
  form.name = row.name ?? ''
  form.phone = row.phone ?? ''
  form.role = row.role ?? ''
  form.position = row.position ?? ''
  form.department = row.department ?? ''
  form.storeId = row.store_id != null ? String(row.store_id) : ''
  form.status = row.status ?? '在职'
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload = {
        name: form.name,
        phone: form.phone || undefined,
        role: form.role || undefined,
        position: form.position || undefined,
        department: form.department || undefined,
        storeId: form.storeId || undefined,
        status: form.status,
      }
      if (editing.value) {
        await api().updateStaff(editingId.value, payload)
        ElMessage.success('员工已更新')
      } else {
        await api().createStaff(payload)
        ElMessage.success('员工已创建')
      }
      dialogVisible.value = false
      load()
    } catch (e: any) {
      ElMessage.error('保存失败：' + (e?.message || ''))
    } finally {
      saving.value = false
    }
  })
}

async function toggleStatus(row: any) {
  const next = row.status === '在职' ? '离职' : '在职'
  const verb = next === '离职' ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确认${verb}员工「${row.name}」？`, `${verb}确认`, {
      confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning',
    })
    await api().setStaffStatus(row.staff_id, next)
    ElMessage.success(`${verb}成功`)
    load()
  } catch (e: any) {
    if (e !== 'cancel' && e?.message) ElMessage.error(`${verb}失败：` + e.message)
  }
}

async function resetPwd(row: any) {
  try {
    const { value } = await ElMessageBox.prompt(`为员工「${row.name}」设置新登录口令（至少 6 位）`, '重置密码', {
      confirmButtonText: '重置', cancelButtonText: '取消', inputPlaceholder: '新口令', inputPattern: /.{6,}/, inputErrorMessage: '至少 6 位',
    })
    await api().resetStaffPassword(row.staff_id, value)
    ElMessage.success('已重置，员工可用新口令登录')
  } catch (e: any) {
    if (e !== 'cancel' && e?.message) ElMessage.error('重置失败：' + e.message)
  }
}

onMounted(() => { loadRoles(); load() })
</script>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.ph {
  font-family: var(--font-cn-serif);
  font-weight: 600;
  margin: 0;
}
.filters {
  display: flex;
  gap: 10px;
}
.tbl {
  background: var(--paper);
  border-radius: var(--r-sm);
}
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
</style>
