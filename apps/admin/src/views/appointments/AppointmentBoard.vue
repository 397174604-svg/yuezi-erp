<template>
  <div>
    <h2 class="ph">预约与排班</h2>
    <el-tabs v-model="tab">
      <!-- 预约看板 -->
      <el-tab-pane label="预约看板" name="board">
        <div class="bar">
          <el-date-picker v-model="date" type="date" placeholder="按日期筛选" value-format="YYYY-MM-DD" clearable style="width: 180px" @change="loadAppts" />
          <el-button type="primary" @click="loadAppts">刷新</el-button>
          <el-button v-if="canWriteAppt" type="success" @click="openAppt">新增预约</el-button>
          <span class="hint">共 {{ appts.length }} 条{{ canWriteAppt ? ' · 点卡片右上「⋯」改状态' : ' · 只读（预约操作限前台/店长）' }}</span>
        </div>
        <div v-loading="loadingA" class="board">
          <div v-for="col in columns" :key="col" class="col">
            <div class="col-h">{{ col }} <span class="cnt">{{ grouped[col]?.length || 0 }}</span></div>
            <div class="col-b">
              <div v-for="a in (grouped[col] || [])" :key="a.appt_id" class="appt">
                <div class="appt-t">
                  <span class="tm">{{ (a.time || '').slice(11, 16) }}</span>
                  <el-dropdown v-if="canWriteAppt" trigger="click" @command="(s:string) => changeStatus(a, s)">
                    <span class="more">⋯</span>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item v-for="s in flowStatuses" :key="s" :command="s" :disabled="s === a.status">{{ s }}</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
                <div class="proj">{{ a.project }}</div>
                <div class="meta">技师 {{ a.tech || '—' }} · 客#{{ a.customer_id }}</div>
              </div>
              <div v-if="!(grouped[col] || []).length" class="col-empty">—</div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 员工排班：店长/管理层职责，一线角色(前台/护理/产康师)不显 -->
      <el-tab-pane v-if="auth.isManager" label="员工排班" name="schedule">
        <div class="bar">
          <el-date-picker v-model="workDate" type="date" placeholder="按工作日筛选" value-format="YYYY-MM-DD" clearable style="width: 180px" @change="loadSchedules" />
          <el-button type="primary" @click="loadSchedules">刷新</el-button>
          <el-button v-if="canWriteSchedule" type="success" @click="openSchedule()">新增排班</el-button>
          <span v-else class="hint">总部只读 · 排班由店长维护</span>
        </div>
        <el-table :data="schedules" v-loading="loadingS" border stripe empty-text="暂无排班">
          <el-table-column prop="work_date" label="工作日" width="140" />
          <el-table-column label="员工" width="140"><template #default="{ row }">{{ staffName(row.staff_id) }}</template></el-table-column>
          <el-table-column prop="shift" label="班次" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="schType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="note" label="备注" min-width="140" />
          <el-table-column v-if="canWriteSchedule" label="操作" width="150">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openSchedule(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="delSchedule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 排班对话框 -->
    <el-dialog v-model="sDlg" :title="sForm.scheduleId ? '编辑排班' : '新增排班'" width="440px">
      <el-form label-width="82px">
        <el-form-item label="员工"><el-select v-model="sForm.staffId" filterable placeholder="选择员工" :disabled="!!sForm.scheduleId" style="width:100%"><el-option v-for="s in staff" :key="s.staff_id" :label="s.name + '（' + s.role + '）'" :value="s.staff_id" /></el-select></el-form-item>
        <el-form-item label="工作日"><el-date-picker v-model="sForm.workDate" type="date" value-format="YYYY-MM-DD" :disabled="!!sForm.scheduleId" style="width:100%" /></el-form-item>
        <el-form-item label="班次"><el-select v-model="sForm.shift" style="width:100%"><el-option v-for="s in SHIFTS" :key="s" :label="s" :value="s" /></el-select></el-form-item>
        <el-form-item v-if="sForm.scheduleId" label="状态"><el-select v-model="sForm.status" style="width:100%"><el-option v-for="s in SSTATUS" :key="s" :label="s" :value="s" /></el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model="sForm.note" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="sDlg = false">取消</el-button><el-button type="primary" @click="saveSchedule">保存</el-button></template>
    </el-dialog>

    <!-- 新增预约对话框 -->
    <el-dialog v-model="aDlg" title="新增预约" width="440px">
      <el-form label-width="82px">
        <el-form-item label="客户ID"><el-input v-model="aForm.customerId" placeholder="客户编号" /></el-form-item>
        <el-form-item label="项目"><el-input v-model="aForm.project" placeholder="如 盆底修复" /></el-form-item>
        <el-form-item label="技师"><el-select v-model="aForm.tech" filterable clearable placeholder="选择技师" style="width:100%"><el-option v-for="s in staff" :key="s.staff_id" :label="s.name" :value="s.name" /></el-select></el-form-item>
        <el-form-item label="时间"><el-date-picker v-model="aForm.time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="aDlg = false">取消</el-button><el-button type="primary" @click="saveAppt">提交</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
// 预约新增/改状态=门店层操作角色（前台/收银/店长/店长助理）+产康师（服务执行人给本人客户约下次到店，店内数据域限本店）；
// 总部（老板/运营）只监督看板、护士只读——均隐藏建/改动作避免死按钮
const STORE_OPS = ['前台', '收银', '店长', '店长助理', '产康师']
const canWriteAppt = computed(() => STORE_OPS.some((r) => auth.roles.includes(r)))
// 排班=店级管理(店长/店长助理)操作;总部(老板/运营)只在此监督查看,不显新增/编辑/删除
const canWriteSchedule = computed(() => ['店长', '店长助理'].some((r) => auth.roles.includes(r)))
const tab = ref('board')
const flowStatuses = ['待接单', '待到店', '已到店', '已完成', '已取消']
const columns = ['待接单', '待到店', '已到店', '已完成']
const SHIFTS = ['早班', '中班', '晚班', '休息']
const SSTATUS = ['正常', '请假', '调班']
// 排班状态色区分:正常=绿 / 请假=橙 / 调班=蓝灰(此前请假·调班同灰+浅描边难分)
const schType = (s: string) => (s === '正常' ? 'success' : s === '请假' ? 'warning' : 'info')

// 员工（排班/技师下拉 + 名称映射）
const staff = ref<any[]>([])
const staffMap = computed<Record<number, string>>(() => Object.fromEntries(staff.value.map((s) => [s.staff_id, s.name])))
const staffName = (id: number) => staffMap.value[id] || ('员工#' + id)
async function loadStaff() { try { staff.value = (await api().listStaff({}) as any[]) || [] } catch { staff.value = [] } }

// 预约看板
const appts = ref<any[]>([])
const loadingA = ref(false)
const date = ref<string | null>(null)
const grouped = computed<Record<string, any[]>>(() => {
  const g: Record<string, any[]> = {}
  for (const a of appts.value) {
    const k = columns.includes(a.status) ? a.status : (columns[columns.length - 1])
    ;(g[k] = g[k] || []).push(a)
  }
  return g
})
async function loadAppts() {
  loadingA.value = true
  try {
    const data: any = await api().listAppointments({ date: date.value || undefined })
    appts.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) { ElMessage.error('预约加载失败：' + (e?.message || '')) } finally { loadingA.value = false }
}
async function changeStatus(a: any, status: string) {
  try { await api().setAppointmentStatus(a.appt_id, status); a.status = status; ElMessage.success('已更新为「' + status + '」') }
  catch (e: any) { ElMessage.error('更新失败：' + (e?.message || '')) }
}

// 新增预约
const aDlg = ref(false)
const aForm = ref<{ customerId: string; project: string; tech: string; time: string }>({ customerId: '', project: '', tech: '', time: '' })
function openAppt() { aForm.value = { customerId: '', project: '', tech: '', time: '' }; aDlg.value = true }
async function saveAppt() {
  if (!aForm.value.project || !aForm.value.time) { ElMessage.warning('项目与时间必填'); return }
  try {
    await api().createAppointment({ customerId: aForm.value.customerId ? Number(aForm.value.customerId) : undefined, project: aForm.value.project, tech: aForm.value.tech || undefined, time: aForm.value.time })
    ElMessage.success('预约已创建'); aDlg.value = false; loadAppts()
  } catch (e: any) { ElMessage.error('创建失败：' + (e?.message || '')) }
}

// 员工排班
const schedules = ref<any[]>([])
const loadingS = ref(false)
const workDate = ref<string | null>(null)
async function loadSchedules() {
  loadingS.value = true
  try {
    const data: any = await api().listSchedules({ workDate: workDate.value || undefined, limit: 100 })
    schedules.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) { ElMessage.error('排班加载失败：' + (e?.message || '')) } finally { loadingS.value = false }
}
const sDlg = ref(false)
const sForm = ref<{ scheduleId: number | null; staffId: number | null; workDate: string; shift: string; status: string; note: string }>({ scheduleId: null, staffId: null, workDate: '', shift: '早班', status: '正常', note: '' })
function openSchedule(row?: any) {
  sForm.value = row
    ? { scheduleId: row.schedule_id, staffId: row.staff_id, workDate: row.work_date, shift: row.shift, status: row.status, note: row.note || '' }
    : { scheduleId: null, staffId: null, workDate: '', shift: '早班', status: '正常', note: '' }
  sDlg.value = true
}
async function saveSchedule() {
  const f = sForm.value
  try {
    if (f.scheduleId) await api().updateSchedule(f.scheduleId, { shift: f.shift, status: f.status, note: f.note })
    else {
      if (!f.staffId || !f.workDate) { ElMessage.warning('员工与工作日必填'); return }
      await api().createSchedule({ staffId: f.staffId, workDate: f.workDate, shift: f.shift, note: f.note || undefined })
    }
    ElMessage.success('已保存'); sDlg.value = false; loadSchedules()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}
async function delSchedule(row: any) {
  try {
    await ElMessageBox.confirm(`删除 ${staffName(row.staff_id)} ${row.work_date} 的排班？`, '确认', { type: 'warning' })
    await api().removeSchedule(row.schedule_id); ElMessage.success('已删除'); loadSchedules()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('删除失败：' + e.message) }
}

onMounted(() => { loadStaff(); loadAppts(); loadSchedules() })
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 8px; }
.bar { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.hint { font-size: 12px; color: var(--ink-3); }
.board { display: flex; gap: 14px; align-items: flex-start; overflow-x: auto; }
.col { flex: 1; min-width: 220px; background: var(--ivory-2); border: 1px solid var(--hair); border-radius: var(--r-md); }
.col-h { padding: 12px 14px; font-weight: 600; border-bottom: 1px solid var(--hair); color: var(--gold-deep); }
.col-h .cnt { float: right; color: var(--ink-3); font-weight: 400; }
.col-b { padding: 10px; min-height: 80px; }
.appt { background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-sm); padding: 10px 12px; margin-bottom: 10px; }
.appt-t { display: flex; align-items: center; justify-content: space-between; }
.appt-t .tm { font-family: var(--font-display); font-size: 16px; color: var(--gold-deep); }
.appt-t .more { cursor: pointer; color: var(--ink-3); font-weight: 700; padding: 0 6px; }
.proj { font-size: 14px; font-weight: 500; margin-top: 4px; }
.meta { font-size: 12px; color: var(--ink-3); margin-top: 4px; }
.col-empty { text-align: center; color: var(--ink-3); padding: 16px 0; }
</style>
