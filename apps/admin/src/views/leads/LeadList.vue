<template>
  <div>
    <h2 class="ph">客户运营</h2>

    <el-tabs v-model="activeTab" class="tabs">
      <!-- Tab1 线索 / 公海 -->
      <el-tab-pane label="线索 / 公海" name="leads">
        <el-form :inline="true" class="filters">
          <el-form-item>
            <el-select v-model="lf.status" placeholder="状态" clearable style="width: 130px">
              <el-option v-for="s in leadStatuses" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-switch v-model="lf.pool" active-text="只看公海" />
          </el-form-item>
          <el-form-item><el-button type="primary" @click="reloadLeads">查询</el-button></el-form-item>
        </el-form>

        <el-table :data="leads" v-loading="leadsLoading" border stripe empty-text="暂无线索">
          <el-table-column prop="name" label="姓名" min-width="100" show-overflow-tooltip />
          <el-table-column prop="phone" label="手机" min-width="130" />
          <el-table-column prop="source" label="来源" width="110" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="leadStatusType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="assignee" label="负责人" width="110">
            <template #default="{ row }">{{ row.assignee || '—' }}</template>
          </el-table-column>
          <el-table-column label="是否公海" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.in_pool ? 'warning' : 'info'" effect="dark" size="small">{{ row.in_pool ? '公海' : '已分配' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160" />
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.in_pool" link type="primary" size="small" @click="doClaim(row)">抢单</el-button>
              <el-dropdown trigger="click" @command="(cmd:string) => doConvert(row, cmd)">
                <el-button link type="primary" size="small">改状态</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item v-for="s in leadStatuses" :key="s" :command="s">{{ s }}</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="leadPage" :page-count="leadPageCount" @current-change="onLeadPage" />
        </div>
      </el-tab-pane>

      <!-- Tab2 邀约话术 -->
      <el-tab-pane label="邀约话术" name="scripts">
        <div class="bar">
          <el-form :inline="true" class="filters">
            <el-form-item>
              <el-input v-model="sf.scene" placeholder="场景" clearable style="width: 150px" @keyup.enter="reloadScripts" />
            </el-form-item>
            <el-form-item>
              <el-select v-model="sf.status" placeholder="状态" clearable style="width: 130px">
                <el-option v-for="s in scriptStatuses" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
            <el-form-item><el-button type="primary" @click="reloadScripts">查询</el-button></el-form-item>
          </el-form>
          <el-button v-if="isMgr" type="primary" @click="openCreate">新建话术</el-button>
          <span v-else class="muted" style="margin-left:8px;color:var(--el-text-color-secondary);font-size:12px">话术仅供查阅 · 维护由管理层</span>
        </div>

        <el-table :data="scripts" v-loading="scriptsLoading" border stripe empty-text="暂无话术">
          <el-table-column prop="scene" label="场景" width="140" show-overflow-tooltip />
          <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
          <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="row.status === '启用' ? 'success' : 'danger'" effect="dark" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column v-if="isMgr" label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="doRemove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 话术 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑话术' : '新建话术'" width="560px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="场景"><el-input v-model="form.scene" placeholder="如：到访邀约 / 转化跟进" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title" placeholder="话术标题" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="5" placeholder="话术正文" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" controls-position="right" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" placeholder="状态" style="width: 160px">
            <el-option v-for="s in scriptStatuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveScript">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const isMgr = computed(() => auth.isManager) // 邀约话术=全租户共享文案,增删改归管理层;一线只读话术,写按钮不显避免死按钮

const activeTab = ref('leads')
const pageSize = 20

// —— Tab1 线索 / 公海 ——
const leadStatuses = ref<string[]>([]) // 线索状态：字典 getDict('lead_status')(库值=未处理/跟进中/关闭/已转化)。此前写死'待跟进/已关闭'致筛空+改状态被后端拒 INVALID_STATUS
async function loadLeadStatuses() { try { const d: any = await api().getDict('lead_status'); leadStatuses.value = (d?.items || []).filter((x: any) => (x.status ?? '启用') === '启用').map((x: any) => x.value).filter(Boolean) } catch { /* 回退空 */ } }
const leads = ref<any[]>([])
const leadsLoading = ref(false)
const lf = reactive<{ status: string; pool: boolean }>({ status: '', pool: false })
const leadPage = ref(1)
const leadHasNext = ref(false)
const leadPageCount = computed(() => (leadHasNext.value ? leadPage.value + 1 : leadPage.value))

function leadStatusType(s: string): string {
  // 字典库值：未处理 / 跟进中 / 关闭 / 已转化。每状态独立语义色，避免多状态挤同色。
  if (s === '已转化') return 'success'   // 转化=绿
  if (s === '跟进中') return 'warning'   // 进行中=金
  if (s === '关闭' || s === '已关闭') return 'danger'  // 流失/关闭=红
  if (s === '未处理') return 'info'      // 未开始=灰
  return 'primary'
}

async function loadLeads() {
  leadsLoading.value = true
  try {
    const data: any = await api().listLeads({
      status: lf.status || undefined,
      pool: lf.pool ? true : undefined,
      limit: pageSize,
      offset: (leadPage.value - 1) * pageSize,
    })
    const list = Array.isArray(data) ? data : (data?.rows || [])
    leads.value = list
    leadHasNext.value = list.length === pageSize
  } catch (e: any) {
    ElMessage.error('线索加载失败：' + (e?.message || ''))
    leads.value = []
    leadHasNext.value = false
  } finally {
    leadsLoading.value = false
  }
}
function reloadLeads() { leadPage.value = 1; loadLeads() }
function onLeadPage(p: number) { leadPage.value = p; loadLeads() }

async function doClaim(row: any) {
  try {
    await api().claimLead(row.lead_id)
    ElMessage.success('抢单成功')
    loadLeads()
  } catch (e: any) {
    ElMessage.error('抢单失败：' + (e?.message || ''))
  }
}

async function doConvert(row: any, status: string) {
  try {
    await api().convertLeadStatus(row.lead_id, status)
    ElMessage.success('状态已更新为「' + status + '」')
    loadLeads()
  } catch (e: any) {
    ElMessage.error('改状态失败：' + (e?.message || ''))
  }
}

// —— Tab2 邀约话术 ——
const scriptStatuses = ['启用', '停用']
const scripts = ref<any[]>([])
const scriptsLoading = ref(false)
const sf = reactive<{ scene: string; status: string }>({ scene: '', status: '' })

async function loadScripts() {
  scriptsLoading.value = true
  try {
    const data: any = await api().listScripts({
      scene: sf.scene || undefined,
      status: sf.status || undefined,
    })
    scripts.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) {
    ElMessage.error('话术加载失败：' + (e?.message || ''))
    scripts.value = []
  } finally {
    scriptsLoading.value = false
  }
}
function reloadScripts() { loadScripts() }

const dialogVisible = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const form = reactive<{ scene: string; title: string; content: string; sort: number; status: string }>({
  scene: '', title: '', content: '', sort: 0, status: '启用',
})

function resetForm() {
  form.scene = ''
  form.title = ''
  form.content = ''
  form.sort = 0
  form.status = '启用'
}

function openCreate() {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: any) {
  editing.value = row
  form.scene = row.scene || ''
  form.title = row.title || ''
  form.content = row.content || ''
  form.sort = row.sort ?? 0
  form.status = row.status || '启用'
  dialogVisible.value = true
}

async function saveScript() {
  saving.value = true
  try {
    const payload = { scene: form.scene, title: form.title, content: form.content, sort: form.sort, status: form.status }
    if (editing.value) {
      await api().updateScript(editing.value.script_id, payload)
      ElMessage.success('话术已更新')
    } else {
      await api().createScript(payload)
      ElMessage.success('话术已创建')
    }
    dialogVisible.value = false
    loadScripts()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.message || ''))
  } finally {
    saving.value = false
  }
}

async function doRemove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除话术「${row.title || ''}」？`, '删除确认', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
    await api().removeScript(row.script_id)
    ElMessage.success('已删除')
    loadScripts()
  } catch (e: any) {
    if (e !== 'cancel' && e?.message) ElMessage.error('删除失败：' + e.message)
  }
}

onMounted(() => { loadLeads(); loadScripts(); loadLeadStatuses() })
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 14px; }
.tabs { margin-top: 4px; }
.bar { display: flex; align-items: center; justify-content: space-between; }
.filters { margin-bottom: 6px; }
.pager { margin-top: 14px; display: flex; justify-content: flex-end; }
</style>
