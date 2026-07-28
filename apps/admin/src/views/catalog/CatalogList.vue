<template>
  <div>
    <div class="bar">
      <h2 class="ph">品项与提成</h2>
      <el-button type="primary" @click="openCreate">新建品项</el-button>
    </div>

    <el-form :inline="true" class="filters">
      <el-form-item>
        <el-select v-model="f.domain" placeholder="业务" clearable style="width: 130px">
          <el-option v-for="d in domains" :key="d" :label="d" :value="d" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="f.status" placeholder="状态" clearable style="width: 120px">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-input v-model="f.cat" placeholder="分类关键字" clearable style="width: 150px" @keyup.enter="reload" />
      </el-form-item>
      <el-form-item><el-button type="primary" @click="reload">查询</el-button></el-form-item>
    </el-form>

    <el-table :data="rows" v-loading="loading" border stripe empty-text="暂无品项">
      <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
      <el-table-column prop="domain" label="业务" width="90" />
      <el-table-column prop="cat" label="分类" width="120" show-overflow-tooltip />
      <el-table-column label="销售价" width="120" align="right"><template #default="{ row }">{{ money(row.sale_price) }}</template></el-table-column>
      <el-table-column label="体验价" width="120" align="right"><template #default="{ row }">{{ money(row.exp_price) }}</template></el-table-column>
      <el-table-column label="成本价" width="110" align="right"><template #default="{ row }">{{ Number(row.cost_price) > 0 ? money(row.cost_price) : '未录' }}</template></el-table-column>
      <el-table-column label="时长" width="90" align="center"><template #default="{ row }">{{ row.duration != null ? row.duration + ' 分钟' : '—' }}</template></el-table-column>
      <el-table-column label="客户提成" width="120" align="right"><template #default="{ row }">{{ money(row.member_commission) }}</template></el-table-column>
      <el-table-column label="散客提成" width="120" align="right"><template #default="{ row }">{{ money(row.walkin_commission) }}</template></el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }"><el-tag :type="row.status === '启用' ? 'success' : 'danger'" effect="dark" size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }"><el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="page" :page-count="pageCount" @current-change="onPage" />
    </div>

    <!-- 新建 / 编辑品项 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑品项' : '新建品项'" width="640px" @closed="resetForm">
      <el-form :model="form" label-width="92px">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="品项名称" /></el-form-item>
        <el-form-item label="业务">
          <el-select v-model="form.domain" placeholder="业务" style="width: 100%">
            <el-option v-for="d in domains" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类"><el-input v-model="form.cat" placeholder="分类" /></el-form-item>
        <el-form-item label="销售价"><el-input-number v-model="form.sale_price" :min="0" :precision="2" :step="100" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="体验价"><el-input-number v-model="form.exp_price" :min="0" :precision="2" :step="100" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="成本价"><el-input-number v-model="form.cost_price" :min="0" :precision="2" :step="50" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="时长(分钟)"><el-input-number v-model="form.duration" :min="0" :step="5" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="客户提成"><el-input-number v-model="form.member_commission" :min="0" :precision="2" :step="10" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="散客提成"><el-input-number v-model="form.walkin_commission" :min="0" :precision="2" :step="10" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="客户奖金"><el-input-number v-model="form.member_bonus" :min="0" :precision="2" :step="10" controls-position="right" style="width: 100%" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" placeholder="如 次 / 项 / 套" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
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
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const domains = ['月子', '产康', '科研美容'] // U1b 三业务板块
const statuses = ['启用', '停用']

const rows = ref<any[]>([])
const loading = ref(false)
const f = reactive<{ domain: string; status: string; cat: string }>({ domain: '', status: '', cat: '' })
const page = ref(1)
const pageSize = 20
const hasNext = ref(false)
const pageCount = computed(() => (hasNext.value ? page.value + 1 : page.value))

function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString()
}

async function load() {
  loading.value = true
  try {
    const data: any = await api().listItems({
      domain: f.domain || undefined,
      status: f.status || undefined,
      cat: f.cat || undefined,
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    })
    const list = Array.isArray(data) ? data : (data?.rows || [])
    rows.value = list
    hasNext.value = list.length === pageSize
  } catch (e: any) {
    ElMessage.error('品项加载失败：' + (e?.message || ''))
    rows.value = []
    hasNext.value = false
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }
function onPage(p: number) { page.value = p; load() }

// —— 新建 / 编辑 ——
const dialogVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const editId = ref<any>(null)

function blankForm() {
  return {
    name: '',
    domain: '月子',
    cat: '',
    sale_price: 0,
    exp_price: 0,
    cost_price: 0,
    duration: 0,
    member_commission: 0,
    walkin_commission: 0,
    member_bonus: 0,
    unit: '',
    status: '启用',
  }
}
const form = reactive<any>(blankForm())

function resetForm() {
  Object.assign(form, blankForm())
  editing.value = false
  editId.value = null
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: any) {
  editing.value = true
  editId.value = row.item_id
  Object.assign(form, {
    name: row.name ?? '',
    domain: row.domain ?? '月子',
    cat: row.cat ?? '',
    sale_price: row.sale_price ?? 0,
    exp_price: row.exp_price ?? 0,
    cost_price: row.cost_price ?? 0,
    duration: row.duration ?? 0,
    member_commission: row.member_commission ?? 0,
    walkin_commission: row.walkin_commission ?? 0,
    member_bonus: row.member_bonus ?? 0,
    unit: row.unit ?? '',
    status: row.status ?? '启用',
  })
  dialogVisible.value = true
}

async function submit() {
  if (!form.name) { ElMessage.error('请填写品项名称'); return }
  saving.value = true
  try {
    // 后端 catalogService 取 camelCase（salePrice/expPrice/…）；此前误传 snake_case 致价格静默存 0，一并修正。
    const payload = {
      name: form.name,
      domain: form.domain,
      cat: form.cat || undefined,
      salePrice: form.sale_price,
      expPrice: form.exp_price,
      costPrice: form.cost_price,
      duration: form.duration,
      memberCommission: form.member_commission,
      walkinCommission: form.walkin_commission,
      memberBonus: form.member_bonus,
      unit: form.unit || undefined,
      status: form.status,
    }
    if (editing.value) {
      await api().updateItem(editId.value, payload)
      ElMessage.success('品项已更新')
    } else {
      await api().createItem(payload)
      ElMessage.success('品项已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.message || ''))
  } finally {
    saving.value = false
  }
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
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
</style>
