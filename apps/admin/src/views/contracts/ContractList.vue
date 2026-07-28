<template>
  <div>
    <div class="bar">
      <h2 class="ph">合同与销售</h2>
      <div class="filters">
        <el-input v-model="q" placeholder="合同号 / 套餐" clearable style="width: 180px" @keyup.enter="reload" />
        <el-select v-model="status" placeholder="审核状态" clearable style="width: 130px">
          <el-option v-for="s in STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button @click="reload">查询</el-button>
        <el-button type="primary" @click="openCreate">新建合同</el-button>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe empty-text="暂无合同">
      <el-table-column prop="contract_no" label="合同编码" width="150" />
      <el-table-column label="客户" width="90"><template #default="{ row }">客#{{ row.customer_id }}</template></el-table-column>
      <el-table-column prop="package_name" label="套餐" min-width="130" show-overflow-tooltip />
      <el-table-column label="成交额" width="120" align="right"><template #default="{ row }">{{ money(row.amount) }}</template></el-table-column>
      <el-table-column label="已收" width="120" align="right"><template #default="{ row }">{{ money(row.paid) }}</template></el-table-column>
      <el-table-column label="欠款" width="120" align="right"><template #default="{ row }"><span :class="{ owe: Number(row.due) > 0 }">{{ money(row.due) }}</span></template></el-table-column>
      <el-table-column label="折扣" width="80" align="center"><template #default="{ row }">{{ row.discount_rate != null ? (Number(row.discount_rate) * 10).toFixed(1) + '折' : '—' }}</template></el-table-column>
      <el-table-column label="审核状态" width="110"><template #default="{ row }"><el-tag :type="stType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button v-if="['待完善','待提交','已驳回'].includes(row.status)" link type="primary" size="small" @click="doSubmit(row)">送审</el-button>
          <el-button v-if="isMgr && row.status === '待审核'" link type="success" size="small" @click="doAudit(row, true)">通过</el-button>
          <el-button v-if="isMgr && row.status === '待审核'" link type="danger" size="small" @click="doAudit(row, false)">驳回</el-button>
          <el-button link type="primary" size="small" @click="openPay(row)">收款</el-button>
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="isMgr" link type="danger" size="small" @click="doRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="page" :page-count="pageCount" @current-change="onPage" />
    </div>

    <!-- 新建 / 编辑 -->
    <el-dialog v-model="formVisible" :title="form.contract_id ? '编辑合同' : '新建合同'" width="500px">
      <el-form label-width="80px">
        <el-form-item v-if="!form.contract_id" label="客户">
          <el-select v-model="form.customerId" filterable placeholder="选择客户" style="width: 100%">
            <el-option v-for="c in customers" :key="c.customer_id" :label="c.name + ' · ' + (c.phone || '')" :value="c.customer_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="套餐"><el-input v-model="form.packageName" placeholder="如 臻享28天套餐" /></el-form-item>
        <el-form-item label="成交额"><el-input-number v-model="form.amount" :min="0" :step="1000" /></el-form-item>
        <el-form-item label="折扣率"><el-input-number v-model="form.discountRate" :min="0" :max="1" :step="0.05" :precision="2" /><span class="hint">1=不打折，0.9=9折</span></el-form-item>
        <el-form-item label="套餐天数"><el-input-number v-model="form.days" :min="0" /></el-form-item>
        <el-form-item label="签约日"><el-date-picker v-model="form.signDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible = false">取消</el-button><el-button type="primary" @click="saveForm">保存</el-button></template>
    </el-dialog>

    <!-- 收款 -->
    <el-dialog v-model="payVisible" :title="'收款 · ' + (payRow?.contract_no || '')" width="380px">
      <p class="paytip">成交额 {{ money(payRow?.amount) }}，已收 {{ money(payRow?.paid) }}，欠款 {{ money(payRow?.due) }}</p>
      <el-input-number v-model="payAmount" :min="0" :max="Number(payRow?.due) || undefined" :step="1000" style="width: 100%" />
      <template #footer><el-button @click="payVisible = false">取消</el-button><el-button type="primary" @click="doPay">确认收款</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const isMgr = computed(() => auth.isManager) // 审核/删除=管理层(销售自建自审隔离);销售只显送审,不显通过/驳回/删除避免死按钮

const STATUSES = ['待完善', '待提交', '待审核', '审核通过', '已驳回', '已生效', '已完成', '已作废']
const rows = ref<any[]>([])
const customers = ref<any[]>([])
const loading = ref(false)
const q = ref(''); const status = ref('')
const page = ref(1); const pageSize = 20; const hasNext = ref(false)
const pageCount = computed(() => (hasNext.value ? page.value + 1 : page.value))

function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}
function stType(s: string): string {
  if (['审核通过', '已生效', '已完成'].includes(s)) return 'success'
  if (s === '待审核') return 'warning'
  if (['已驳回', '已作废'].includes(s)) return 'danger'
  return 'info' // 待完善 / 待提交（草稿态）
}

async function load() {
  loading.value = true
  try {
    const data: any = await api().listContracts({ q: q.value || undefined, status: status.value || undefined, limit: pageSize, offset: (page.value - 1) * pageSize })
    rows.value = Array.isArray(data) ? data : (data?.rows || [])
    hasNext.value = rows.value.length === pageSize
  } catch (e: any) {
    ElMessage.error('合同加载失败：' + (e?.message || ''))
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }
function onPage(p: number) { page.value = p; load() }

// 新建 / 编辑
const formVisible = ref(false)
const form = reactive<any>({ contract_id: 0, customerId: null, packageName: '', amount: 28800, discountRate: 1, days: 28, signDate: '' })
function openCreate() {
  Object.assign(form, { contract_id: 0, customerId: null, packageName: '臻享28天套餐', amount: 28800, discountRate: 1, days: 28, signDate: '' })
  formVisible.value = true
}
function openEdit(r: any) {
  Object.assign(form, { contract_id: r.contract_id, packageName: r.package_name, amount: Number(r.amount), discountRate: Number(r.discount_rate), days: r.days, signDate: r.sign_date })
  formVisible.value = true
}
async function saveForm() {
  try {
    if (form.contract_id) {
      await api().updateContract(form.contract_id, { packageName: form.packageName, amount: form.amount, discountRate: form.discountRate, days: form.days, signDate: form.signDate || undefined })
    } else {
      if (!form.customerId) { ElMessage.warning('请选择客户'); return }
      await api().createContract({ customerId: form.customerId, packageName: form.packageName, amount: form.amount, discountRate: form.discountRate, days: form.days, signDate: form.signDate || undefined })
    }
    ElMessage.success('已保存'); formVisible.value = false; load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}

// 送审 / 审核 / 删除
async function doSubmit(r: any) {
  try { await api().submitContract(r.contract_id); ElMessage.success('已送审'); load() } catch (e: any) { ElMessage.error('送审失败：' + (e?.message || '')) }
}
async function doAudit(r: any, pass: boolean) {
  try {
    let reason = ''
    if (!pass) { const { value } = await ElMessageBox.prompt('驳回原因', '驳回合同', { inputPlaceholder: '请填写驳回原因' }); reason = value || '' }
    await api().auditContract(r.contract_id, pass, reason)
    ElMessage.success(pass ? '已通过' : '已驳回'); load()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('审核失败：' + e.message) }
}
async function doRemove(r: any) {
  try {
    await ElMessageBox.confirm(`确认删除合同 ${r.contract_no}？`, '确认', { type: 'warning' })
    await api().removeContract(r.contract_id); ElMessage.success('已删除'); load()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('删除失败：' + e.message) }
}

// 收款
const payVisible = ref(false)
const payRow = ref<any>(null)
const payAmount = ref(0)
function openPay(r: any) { payRow.value = r; payAmount.value = Number(r.due) || 0; payVisible.value = true }
async function doPay() {
  if (!(payAmount.value > 0)) { ElMessage.warning('收款金额须大于 0'); return }
  try {
    await api().payContract(payRow.value.contract_id, payAmount.value)
    ElMessage.success('收款成功'); payVisible.value = false; load()
  } catch (e: any) { ElMessage.error('收款失败：' + (e?.message || '')) }
}

onMounted(async () => {
  try { customers.value = (await api().listCustomers({ limit: 200 })) || [] } catch { /* ignore */ }
  await load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.filters { display: flex; gap: 10px; }
.owe { color: var(--danger); font-weight: 600; }
.pager { margin-top: 14px; display: flex; justify-content: flex-end; }
.hint { font-size: 12px; color: var(--ink-3); margin-left: 10px; }
.paytip { font-size: 13px; color: var(--ink-2); margin: 0 0 12px; }
</style>
