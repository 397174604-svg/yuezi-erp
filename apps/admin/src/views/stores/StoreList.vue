<template>
  <div>
    <div class="bar">
      <h2 class="ph">门店与渠道</h2>
      <el-button type="primary" @click="openCreate">新建门店</el-button>
    </div>

    <el-form :inline="true" class="filters">
      <el-form-item><el-input v-model="q" placeholder="搜索店名 / 负责人 / 电话" clearable style="width: 220px" @keyup.enter="reload" /></el-form-item>
      <el-form-item>
        <el-select v-model="status" placeholder="状态" clearable style="width: 130px">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="domain" placeholder="业务" clearable style="width: 130px">
          <el-option v-for="d in domains" :key="d" :label="d" :value="d" />
        </el-select>
      </el-form-item>
      <el-form-item><el-button type="primary" @click="reload">查询</el-button></el-form-item>
    </el-form>

    <el-table :data="rows" v-loading="loading" border stripe class="tbl" empty-text="暂无门店">
      <el-table-column prop="name" label="店名" min-width="140" show-overflow-tooltip />
      <el-table-column prop="manager" label="负责人" width="110" />
      <el-table-column prop="phone" label="电话" min-width="130" />
      <el-table-column prop="region" label="地区" width="120" />
      <el-table-column prop="industry" label="行业" width="120" />
      <el-table-column prop="domain" label="业务" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="sort_weight" label="排序权重" width="100" align="right">
        <template #default="{ row }"><span class="serif">{{ row.sort_weight ?? '—' }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }"><el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>

    <!-- 新建 / 编辑门店 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑门店' : '新建门店'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="店名" prop="name">
          <el-input v-model="form.name" placeholder="门店名称" maxlength="40" />
        </el-form-item>
        <el-form-item label="负责人" prop="manager">
          <el-input v-model="form.manager" placeholder="负责人姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="门店地址" />
        </el-form-item>
        <el-form-item label="地区" prop="region">
          <el-input v-model="form.region" placeholder="所在地区" />
        </el-form-item>
        <el-form-item label="行业" prop="industry">
          <el-input v-model="form.industry" placeholder="行业" />
        </el-form-item>
        <el-form-item label="业务" prop="domain">
          <el-select v-model="form.domain" placeholder="业务线" clearable style="width: 100%">
            <el-option v-for="d in domains" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" placeholder="状态" style="width: 100%">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序权重" prop="sort_weight">
          <el-input-number v-model="form.sort_weight" :min="0" :step="1" controls-position="right" style="width: 160px" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { api } from '@/api'

const statuses = ['正常', '停用']
const domains = ['月子', '产康', '科研美容'] // U1b 三业务板块

const all = ref<any[]>([])
const rows = ref<any[]>([])
const loading = ref(false)
const q = ref('')
const status = ref('')
const domain = ref('')

function statusType(s: string): string {
  return s === '停用' ? 'danger' : 'success'
}

function applyFilter() {
  const kw = q.value.trim().toLowerCase()
  rows.value = all.value.filter((r) => {
    if (status.value && r.status !== status.value) return false
    if (domain.value && r.domain !== domain.value) return false
    if (kw) {
      const hay = [r.name, r.manager, r.phone].map((x: any) => String(x || '').toLowerCase()).join(' ')
      if (!hay.includes(kw)) return false
    }
    return true
  })
}

async function load() {
  loading.value = true
  try {
    const data: any = await api().listStores()
    all.value = Array.isArray(data) ? data : (data?.rows || [])
    applyFilter()
  } catch (e: any) {
    ElMessage.error('门店列表加载失败：' + (e?.message || ''))
    all.value = []
    rows.value = []
  } finally {
    loading.value = false
  }
}

function reload() {
  applyFilter()
}

// —— 新建 / 编辑 ——
const dialogVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const curId = ref<any>(null)

const form = reactive<{
  name: string
  manager: string
  phone: string
  address: string
  region: string
  industry: string
  domain: string
  status: string
  sort_weight: number
}>({
  name: '',
  manager: '',
  phone: '',
  address: '',
  region: '',
  industry: '',
  domain: '',
  status: '正常',
  sort_weight: 0,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入店名', trigger: 'blur' }],
}

function resetForm() {
  form.name = ''
  form.manager = ''
  form.phone = ''
  form.address = ''
  form.region = ''
  form.industry = ''
  form.domain = ''
  form.status = '正常'
  form.sort_weight = 0
}

function openCreate() {
  editing.value = false
  curId.value = null
  resetForm()
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

function openEdit(row: any) {
  editing.value = true
  curId.value = row.store_id
  form.name = row.name ?? ''
  form.manager = row.manager ?? ''
  form.phone = row.phone ?? ''
  form.address = row.address ?? ''
  form.region = row.region ?? ''
  form.industry = row.industry ?? ''
  form.domain = row.domain ?? ''
  form.status = row.status ?? '正常'
  form.sort_weight = row.sort_weight ?? 0
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (ok) => {
    if (!ok) return
    saving.value = true
    try {
      const payload = {
        name: form.name,
        manager: form.manager || undefined,
        phone: form.phone || undefined,
        address: form.address || undefined,
        region: form.region || undefined,
        industry: form.industry || undefined,
        domain: form.domain || undefined,
        status: form.status,
        // 后端 storeService 取 camelCase（sortWeight→sort_weight 列）；此前误传 snake_case 致排序权重静默丢失（建店恒为0、编辑改不动），一并修正。
        sortWeight: form.sort_weight,
      }
      if (editing.value) {
        await api().updateStore(curId.value, payload)
        ElMessage.success('门店已更新')
      } else {
        await api().createStore(payload)
        ElMessage.success('门店已创建')
      }
      dialogVisible.value = false
      await load()
    } catch (e: any) {
      ElMessage.error((editing.value ? '更新' : '创建') + '失败：' + (e?.message || ''))
    } finally {
      saving.value = false
    }
  })
}

onMounted(load)
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
  margin-bottom: 6px;
}
.tbl {
  background: var(--paper);
  border-radius: var(--r-sm);
}
.serif {
  color: var(--gold-deep);
}
</style>
