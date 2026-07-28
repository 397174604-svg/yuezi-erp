<template>
  <div>
    <div class="bar">
      <h2 class="ph">角色权限</h2>
      <el-button type="primary" @click="openCreate">新建角色</el-button>
    </div>
    <p class="hint">
      对标金螺云产康真实角色（店长 / 前台=收银员 / 产康师=导购员）+ 月子侧（销售顾问 / 护士 / 技师）。
      管理层恒见全部模块；普通角色按勾选的模块控制可见性。数据写权限另由后端兜底。
    </p>

    <el-table :data="rows" v-loading="loading" border stripe class="tbl" empty-text="暂无角色">
      <el-table-column prop="name" label="角色" width="130">
        <template #default="{ row }">
          <span class="rname">{{ row.name }}</span>
          <el-tag v-if="row.isSystem" size="small" effect="plain" type="info" class="t">内置</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.isManager" size="small" type="warning" effect="dark">管理层</el-tag>
          <el-tag v-else size="small" type="success" effect="plain">普通</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="可访问模块" min-width="320">
        <template #default="{ row }">
          <span v-if="row.isManager" class="all">全部模块（管理层）</span>
          <template v-else>
            <el-tag v-for="k in row.perms" :key="k" size="small" effect="plain" class="mt">{{ titleOf(k) }}</el-tag>
            <span v-if="!row.perms.length" class="muted">— 未分配 —</span>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="数据范围" width="110">
        <template #default="{ row }"><el-tag size="small" effect="plain" :type="row.dataScope === 4 ? 'danger' : 'info'">{{ SCOPE_LABEL[row.dataScope] || '本店' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="description" label="说明" min-width="150" show-overflow-tooltip />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" :disabled="row.isSystem" @click="onRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建 / 编辑角色 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色 · ' + form.name : '新建角色'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="角色名" prop="name">
          <el-input v-model="form.name" placeholder="如：区域督导" maxlength="20" :disabled="editing" />
          <span v-if="editing" class="muted s">角色名是员工关联键，不可修改</span>
        </el-form-item>
        <el-form-item label="管理层">
          <el-switch v-model="form.isManager" />
          <span class="muted s">开启后恒见全部模块，无需逐项勾选</span>
        </el-form-item>
        <el-form-item label="可访问模块">
          <div v-if="form.isManager" class="all">管理层 — 全部 {{ menuCount }} 个模块</div>
          <el-checkbox-group v-else v-model="form.perms" class="perms">
            <el-checkbox v-for="m in assignable" :key="m.key" :value="m.key" border>{{ m.title }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="数据范围">
          <el-select v-model="form.dataScope" style="width: 220px">
            <el-option v-for="o in SCOPE_OPTIONS" :key="o.val" :label="o.lbl" :value="o.val" />
          </el-select>
          <span class="muted s">行级数据权限（与"管理层"正交：店长可管理但仅见本店）</span>
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="该角色职责说明" maxlength="60" />
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
import { ASSIGNABLE, menu } from '@/router/menu'

const assignable = ASSIGNABLE
const menuCount = menu.length
const SCOPE_LABEL: Record<number, string> = { 1: '仅本人', 2: '本店', 3: '本店及子', 4: '全部门店', 5: '自定义' }
// 可选数据范围去掉「仅本人」(scope=1)：除员工积分外各域服务层未接 ownerCol，选它会走 store 分支→visibleStoreIds 空→1=0 fail-closed 见 0 行；
// 且行业实践(美业)会员用「全店共享池+归属标记(提成)」而非硬性本人可见(硬本人可见=客户私藏/离职带走隐患)。SCOPE_LABEL 仍保留 1 供历史值展示。
const SCOPE_OPTIONS = [2, 3, 4, 5].map((v) => ({ val: v, lbl: SCOPE_LABEL[v] }))
const titleMap = Object.fromEntries(menu.map((m) => [m.path, m.title]))
const titleOf = (k: string): string => titleMap[k] || k

const rows = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data: any = await api().listRoles()
    rows.value = Array.isArray(data) ? data : (data?.roles || [])
  } catch (e: any) {
    ElMessage.error('角色列表加载失败：' + (e?.message || ''))
    rows.value = []
  } finally {
    loading.value = false
  }
}

// —— 新建 / 编辑 ——
const dialogVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const curId = ref<any>(null)

const form = reactive<{ name: string; isManager: boolean; perms: string[]; dataScope: number; description: string }>({
  name: '', isManager: false, perms: [], dataScope: 2, description: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入角色名', trigger: 'blur' }],
}

function reset() {
  form.name = ''
  form.isManager = false
  form.perms = []
  form.dataScope = 2
  form.description = ''
}

function openCreate() {
  editing.value = false
  curId.value = null
  reset()
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

function openEdit(row: any) {
  editing.value = true
  curId.value = row.roleId
  form.name = row.name
  form.isManager = row.isManager
  form.perms = [...(row.perms || [])]
  form.dataScope = row.dataScope ?? 2
  form.description = row.description ?? ''
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (ok) => {
    if (!ok) return
    saving.value = true
    try {
      if (editing.value) {
        await api().updateRole(curId.value, { perms: form.perms, isManager: form.isManager, dataScope: form.dataScope, description: form.description })
        ElMessage.success('角色已更新（员工下次登录生效）')
      } else {
        await api().createRole({ name: form.name.trim(), perms: form.perms, isManager: form.isManager, dataScope: form.dataScope, description: form.description })
        ElMessage.success('角色已创建')
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

async function onRemove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除角色「${row.name}」？该角色下有员工或为内置角色将被拒绝。`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await api().removeRole(row.roleId)
    ElMessage.success('角色已删除')
    await load()
  } catch (e: any) {
    ElMessage.error('删除失败：' + (e?.message || ''))
  }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.hint { color: var(--ink-2); font-size: 13px; margin: 0 0 14px; line-height: 1.6; }
.tbl { background: var(--paper); border-radius: var(--r-sm); }
.rname { font-weight: 600; }
.t { margin-left: 6px; }
.mt { margin: 2px 4px 2px 0; }
.all { color: var(--gold-deep); font-weight: 600; }
.muted { color: var(--ink-3); }
.s { margin-left: 10px; font-size: 12px; }
.perms { display: flex; flex-wrap: wrap; gap: 8px; }
.perms :deep(.el-checkbox) { margin: 0; }
</style>
