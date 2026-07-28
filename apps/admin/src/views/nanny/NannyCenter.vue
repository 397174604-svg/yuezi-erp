<template>
  <div>
    <h2 class="ph">月嫂管理</h2>
    <el-tabs v-model="tab">
      <!-- 月嫂名册（复用 nannies） -->
      <el-tab-pane label="月嫂名册" name="roster">
        <div class="bar">
          <el-select v-model="rType" placeholder="职业类型" clearable size="small" style="width: 130px" @change="loadRoster">
            <el-option v-for="t in NANNY_TYPE" :key="t" :label="t" :value="t" />
          </el-select>
          <el-button type="primary" size="small" @click="openNanny()">新增月嫂</el-button>
        </div>
        <el-table :data="nannies" v-loading="loadingR" border stripe empty-text="暂无名册">
          <el-table-column prop="name" label="姓名" width="110" />
          <el-table-column prop="type" label="职业类型" width="110" />
          <el-table-column prop="level" label="等级" width="100" />
          <el-table-column prop="age" label="年龄" width="80" align="center" />
          <el-table-column label="标准费用" width="120" align="right"><template #default="{ row }">{{ money(row.fee) }}</template></el-table-column>
          <el-table-column prop="phone" label="电话" width="140" />
          <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.status === '可约' ? 'success' : row.status === '停用' ? 'danger' : row.status === '休息' ? 'info' : 'warning'" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="90" fixed="right"><template #default="{ row }"><el-button link type="primary" size="small" @click="openNanny(row)">编辑</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 派工审核（新域 nanny_dispatch） -->
      <el-tab-pane label="派工审核" name="dispatch">
        <div class="bar">
          <el-select v-model="dStatus" placeholder="派工状态" clearable size="small" style="width: 130px" @change="loadDispatch">
            <el-option v-for="s in DISPATCH_STATUS" :key="s" :label="s" :value="s" />
          </el-select>
          <el-button type="primary" size="small" @click="openDispatch">新建派工</el-button>
        </div>
        <el-table :data="dispatches" v-loading="loadingD" border stripe empty-text="暂无派工单">
          <el-table-column prop="nanny_name" label="月嫂" width="120"><template #default="{ row }">{{ row.nanny_name }} <span class="sub">{{ row.nanny_type }}</span></template></el-table-column>
          <el-table-column prop="customer_name" label="客户" width="110" />
          <el-table-column label="服务期" min-width="170"><template #default="{ row }">{{ row.start_date || '—' }} ~ {{ row.end_date || '—' }}</template></el-table-column>
          <el-table-column label="费用" width="110" align="right"><template #default="{ row }">{{ money(row.fee) }}</template></el-table-column>
          <el-table-column label="签到" width="70" align="center"><template #default="{ row }">{{ row.checked_in ? '✓' : '—' }}</template></el-table-column>
          <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="dType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === '待审核'" link type="success" size="small" @click="audit(row, true)">通过</el-button>
              <el-button v-if="row.status === '待审核'" link type="danger" size="small" @click="audit(row, false)">驳回</el-button>
              <el-button v-if="row.status === '已派工'" link type="primary" size="small" @click="act(row, 'checkin')">签到</el-button>
              <el-button v-if="['已派工','服务中'].includes(row.status)" link type="primary" size="small" @click="act(row, 'complete')">完成</el-button>
              <el-button link type="danger" size="small" @click="act(row, 'remove')">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 月嫂 新增/编辑 -->
    <el-dialog v-model="nannyVisible" :title="nForm.nanny_id ? '编辑月嫂' : '新增月嫂'" width="440px">
      <el-form label-width="80px">
        <el-form-item label="姓名"><el-input v-model="nForm.name" :disabled="!!nForm.nanny_id" /></el-form-item>
        <el-form-item label="职业类型"><el-select v-model="nForm.type" style="width: 100%"><el-option v-for="t in NANNY_TYPE" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="等级"><el-input v-model="nForm.level" placeholder="如 金牌 / 高级" /></el-form-item>
        <el-form-item label="年龄"><el-input-number v-model="nForm.age" :min="18" :max="70" /></el-form-item>
        <el-form-item label="标准费用"><el-input-number v-model="nForm.fee" :min="0" :step="500" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="nForm.phone" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="nForm.status" style="width: 100%"><el-option v-for="s in NANNY_STATUS" :key="s" :label="s" :value="s" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="nannyVisible = false">取消</el-button><el-button type="primary" @click="saveNanny">保存</el-button></template>
    </el-dialog>

    <!-- 新建派工 -->
    <el-dialog v-model="dispVisible" title="新建派工" width="460px">
      <el-form label-width="80px">
        <el-form-item label="月嫂"><el-select v-model="dForm.nannyId" filterable placeholder="选择月嫂" style="width: 100%"><el-option v-for="x in nannies" :key="x.nanny_id" :label="x.name + ' · ' + (x.type || '')" :value="x.nanny_id" /></el-select></el-form-item>
        <el-form-item label="客户"><el-select v-model="dForm.customerId" filterable placeholder="选择客户" style="width: 100%"><el-option v-for="c in customers" :key="c.customer_id" :label="c.name + ' · ' + (c.phone || '')" :value="c.customer_id" /></el-select></el-form-item>
        <el-form-item label="开始日"><el-date-picker v-model="dForm.startDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
        <el-form-item label="结束日"><el-date-picker v-model="dForm.endDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
        <el-form-item label="费用"><el-input-number v-model="dForm.fee" :min="0" :step="500" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dispVisible = false">取消</el-button><el-button type="primary" @click="saveDispatch">提交（待审核）</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const NANNY_TYPE = ['月嫂', '育儿嫂', '催乳师', '护理员']
const NANNY_STATUS = ['可约', '已约', '休息', '停用']
const DISPATCH_STATUS = ['待审核', '已派工', '服务中', '已完成', '已驳回', '已取消']

const tab = ref('roster')
const nannies = ref<any[]>([])
const customers = ref<any[]>([])
const dispatches = ref<any[]>([])
const loadingR = ref(false); const loadingD = ref(false)
const rType = ref(''); const dStatus = ref('')

function money(v: any): string { return v == null ? '—' : '¥' + Number(v).toLocaleString() }
function dType(s: string): string {
  if (s === '已完成') return 'success'       // 绿 · 完成
  if (s === '服务中') return 'primary'       // 蓝 · 服务进行中
  if (s === '待审核') return 'warning'       // 金 · 待审核
  if (['已驳回', '已取消'].includes(s)) return 'danger' // 红 · 驳回/取消
  return 'info'                              // 灰 · 已派工/其它(待上户)
}

async function loadRoster() {
  loadingR.value = true
  try { nannies.value = await api().listNannies({ type: rType.value || undefined, limit: 200 }) || [] }
  catch (e: any) { ElMessage.error('名册加载失败：' + (e?.message || '')) }
  finally { loadingR.value = false }
}
async function loadDispatch() {
  loadingD.value = true
  try { dispatches.value = await api().listDispatch({ status: dStatus.value || undefined, limit: 200 }) || [] }
  catch (e: any) { ElMessage.error('派工加载失败：' + (e?.message || '')) }
  finally { loadingD.value = false }
}

// 月嫂 新增/编辑
const nannyVisible = ref(false)
const nForm = reactive<any>({ nanny_id: 0, name: '', type: '月嫂', level: '', age: 35, fee: 12800, phone: '', status: '可约' })
function openNanny(row?: any) {
  if (row) Object.assign(nForm, { nanny_id: row.nanny_id, name: row.name, type: row.type, level: row.level, age: row.age, fee: Number(row.fee), phone: row.phone, status: row.status })
  else Object.assign(nForm, { nanny_id: 0, name: '', type: '月嫂', level: '', age: 35, fee: 12800, phone: '', status: '可约' })
  nannyVisible.value = true
}
async function saveNanny() {
  if (!nForm.name) { ElMessage.warning('姓名必填'); return }
  try {
    if (nForm.nanny_id) await api().updateNanny(nForm.nanny_id, { level: nForm.level, fee: nForm.fee, phone: nForm.phone, status: nForm.status })
    else await api().createNanny({ name: nForm.name, type: nForm.type, level: nForm.level, age: nForm.age, fee: nForm.fee, phone: nForm.phone, status: nForm.status })
    ElMessage.success('已保存'); nannyVisible.value = false; loadRoster()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}

// 派工
const dispVisible = ref(false)
const dForm = reactive<any>({ nannyId: null, customerId: null, startDate: '', endDate: '', fee: 9800 })
function openDispatch() { Object.assign(dForm, { nannyId: null, customerId: null, startDate: '', endDate: '', fee: 9800 }); dispVisible.value = true }
async function saveDispatch() {
  if (!dForm.nannyId || !dForm.customerId) { ElMessage.warning('请选择月嫂和客户'); return }
  try {
    await api().createDispatch({ nannyId: dForm.nannyId, customerId: dForm.customerId, startDate: dForm.startDate || undefined, endDate: dForm.endDate || undefined, fee: dForm.fee })
    ElMessage.success('已提交，待审核'); dispVisible.value = false; loadDispatch()
  } catch (e: any) { ElMessage.error('提交失败：' + (e?.message || '')) }
}
async function audit(row: any, pass: boolean) {
  try {
    let reason = ''
    if (!pass) { const { value } = await ElMessageBox.prompt('驳回原因', '驳回派工', { inputPlaceholder: '请填写原因' }); reason = value || '' }
    await api().auditDispatch(row.dispatch_id, pass, reason)
    ElMessage.success(pass ? '已通过派工' : '已驳回'); loadDispatch()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('审核失败：' + e.message) }
}
async function act(row: any, kind: 'checkin' | 'complete' | 'remove') {
  try {
    if (kind === 'remove') await ElMessageBox.confirm('确认删除该派工单？', '确认', { type: 'warning' })
    if (kind === 'checkin') await api().checkinDispatch(row.dispatch_id)
    if (kind === 'complete') await api().completeDispatch(row.dispatch_id)
    if (kind === 'remove') await api().removeDispatch(row.dispatch_id)
    ElMessage.success('操作成功'); loadDispatch()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('操作失败：' + e.message) }
}

onMounted(async () => {
  try { customers.value = (await api().listCustomers({ limit: 200 })) || [] } catch { /* ignore */ }
  loadRoster(); loadDispatch()
})
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 8px; }
.bar { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.sub { font-size: 12px; color: var(--ink-3); }
</style>
