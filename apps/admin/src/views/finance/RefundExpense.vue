<template>
  <div>
    <div class="bar"><h2 class="ph">退款 · 报销</h2></div>
    <el-tabs v-model="tab">
      <!-- 退款单 -->
      <el-tab-pane label="退款单" name="refund">
        <el-card shadow="never" class="card">
          <el-form :inline="true" :model="rf" size="small">
            <el-form-item label="退款类型"><el-select v-model="rf.refundType" style="width:130px"><el-option v-for="t in refundTypes" :key="t" :label="t" :value="t" /></el-select></el-form-item>
            <el-form-item label="客户ID"><el-input v-model="rf.customerId" style="width:90px" placeholder="可选" /></el-form-item>
            <el-form-item label="申请金额"><el-input v-model="rf.applyAmount" style="width:120px" /></el-form-item>
            <el-form-item label="原因"><el-input v-model="rf.reason" style="width:160px" /></el-form-item>
            <el-form-item><el-button type="primary" @click="applyRefund">提交退款</el-button></el-form-item>
          </el-form>
          <el-table :data="refunds" v-loading="rLoading" border stripe size="small" empty-text="暂无退款单">
            <el-table-column prop="refund_no" label="单号" min-width="150" /><el-table-column prop="refund_type" label="类型" width="110" />
            <el-table-column label="申请/实退" width="140" align="right"><template #default="{ row }">{{ money(row.apply_amount) }} / {{ row.actual_amount != null ? money(row.actual_amount) : '—' }}</template></el-table-column>
            <el-table-column label="状态" width="90"><template #default="{ row }"><span class="stag" :style="stStyle(row.status)">{{ row.status }}</span></template></el-table-column>
            <el-table-column label="操作" width="190" fixed="right"><template #default="{ row }">
              <template v-if="row.status === '待审核'"><el-button link type="success" size="small" @click="audit('auditRefund', row, true)">通过</el-button><el-button link type="danger" size="small" @click="audit('auditRefund', row, false)">驳回</el-button></template>
              <el-button v-if="row.status === '待退款'" link type="warning" size="small" @click="payout(row)">打款</el-button>
            </template></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 报销单 -->
      <el-tab-pane label="报销单" name="expense">
        <el-card shadow="never" class="card">
          <el-form :inline="true" :model="ef" size="small">
            <el-form-item label="费用类型"><el-select v-model="ef.expenseType" style="width:130px"><el-option v-for="t in expenseTypes" :key="t" :label="t" :value="t" /></el-select></el-form-item>
            <el-form-item label="报销金额"><el-input v-model="ef.applyAmount" style="width:120px" /></el-form-item>
            <el-form-item label="说明"><el-input v-model="ef.reason" style="width:160px" /></el-form-item>
            <el-form-item><el-button type="primary" @click="applyExpense">提交报销</el-button></el-form-item>
          </el-form>
          <el-table :data="expenses" v-loading="eLoading" border stripe size="small" empty-text="暂无报销单">
            <el-table-column prop="expense_no" label="单号" min-width="150" /><el-table-column prop="expense_type" label="类型" width="110" />
            <el-table-column label="申请/实付" width="140" align="right"><template #default="{ row }">{{ money(row.apply_amount) }} / {{ row.actual_amount != null ? money(row.actual_amount) : '—' }}</template></el-table-column>
            <el-table-column label="状态" width="90"><template #default="{ row }"><span class="stag" :style="stStyle(row.status)">{{ row.status }}</span></template></el-table-column>
            <el-table-column label="操作" width="190" fixed="right"><template #default="{ row }">
              <template v-if="row.status === '待审核'"><el-button link type="success" size="small" @click="audit('auditExpense', row, true)">通过</el-button><el-button link type="danger" size="small" @click="audit('auditExpense', row, false)">驳回</el-button></template>
              <el-button v-if="row.status === '待打款'" link type="warning" size="small" @click="pay(row)">打款</el-button>
            </template></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

// 状态色：高奢金白主题下 el-tag 的 primary/warning 都是相近金色，待审核↔待退款/待打款难分辨。
// 改用显式区分的语义色 + 实底胶囊（琥珀待审 / 蓝待付款 / 绿已完成 / 红驳回），不依赖主题、且与其它页 el-tag effect=dark 观感一致。
const ST_COLOR: Record<string, string> = { 待审核: '#D48806', 待退款: '#2563EB', 待打款: '#2563EB', 已退款: '#389E0D', 已打款: '#389E0D', 驳回: '#CF1322' }
function stStyle(status: string) {
  const c = ST_COLOR[status] || '#8C8C8C'
  return { color: '#fff', background: c, border: `1px solid ${c}` }
}
const money = (v: any) => v != null ? '¥' + Number(v).toLocaleString() : '—'
const refundTypes = ['合同退款', '订金退款', '押金退款', '会员卡退款', '预付款退款', '服务升级退款', '销售退款', '其他退款']
const EXPENSE_DEFAULTS = ['房租物业', '水电能耗', '人员工资', '物料采购', '市场推广', '办公费用', '设备维修', '其他费用']
const expenseTypes = ref<string[]>(EXPENSE_DEFAULTS) // 可配置：优先取租户字典 expense_type，取不到回退默认
const tab = ref('refund')

const rf = ref({ refundType: '合同退款', customerId: '', applyAmount: '', reason: '' })
const refunds = ref<any[]>([]); const rLoading = ref(false)
const ef = ref({ expenseType: '物料采购', applyAmount: '', reason: '' })
const expenses = ref<any[]>([]); const eLoading = ref(false)

async function loadR() { rLoading.value = true; try { refunds.value = (await api().listRefunds({})) as any[] || [] } catch { refunds.value = [] } finally { rLoading.value = false } }
async function loadE() { eLoading.value = true; try { expenses.value = (await api().listExpenses({})) as any[] || [] } catch { expenses.value = [] } finally { eLoading.value = false } }

async function applyRefund() {
  if (!Number(rf.value.applyAmount)) { ElMessage.warning('申请金额必填'); return }
  try { await api().applyRefund({ refundType: rf.value.refundType, customerId: rf.value.customerId ? Number(rf.value.customerId) : undefined, applyAmount: Number(rf.value.applyAmount), reason: rf.value.reason }); ElMessage.success('退款单已提交'); loadR() }
  catch (e: any) { ElMessage.error('提交失败：' + (e?.message || '')) }
}
async function applyExpense() {
  if (!Number(ef.value.applyAmount)) { ElMessage.warning('报销金额必填'); return }
  try { await api().applyExpense({ expenseType: ef.value.expenseType, applyAmount: Number(ef.value.applyAmount), reason: ef.value.reason }); ElMessage.success('报销单已提交'); loadE() }
  catch (e: any) { ElMessage.error('提交失败：' + (e?.message || '')) }
}

async function audit(fn: 'auditRefund' | 'auditExpense', row: any, pass: boolean) {
  try {
    let opinion = ''
    if (!pass) opinion = (await ElMessageBox.prompt('驳回原因', '驳回')).value
    const id = row.refund_id ?? row.expense_id
    await (api() as any)[fn](id, { pass, opinion })
    ElMessage.success(pass ? '已通过' : '已驳回'); fn === 'auditRefund' ? loadR() : loadE()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('操作失败：' + (e?.message || '')) }
}
async function payout(row: any) {
  try { const { value } = await ElMessageBox.prompt('实退金额(可部分退，≤申请额)', '打款', { inputValue: String(row.apply_amount), inputPattern: /^\d+(\.\d+)?$/ }); await api().payoutRefund(row.refund_id, { actualAmount: Number(value), payee: '财务' }); ElMessage.success('已打款'); loadR() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('打款失败：' + (e?.message || '')) }
}
async function pay(row: any) {
  try { const { value } = await ElMessageBox.prompt('实付金额(≤申请额)', '打款', { inputValue: String(row.apply_amount), inputPattern: /^\d+(\.\d+)?$/ }); await api().payExpense(row.expense_id, { actualAmount: Number(value), payee: '出纳' }); ElMessage.success('已打款'); loadE() }
  catch (e: any) { if (e !== 'cancel') ElMessage.error('打款失败：' + (e?.message || '')) }
}

async function loadExpenseTypes() {
  try {
    const items = (await api().getDict('expense_type')) as any[]
    const vals = (items || []).filter((x: any) => (x.status ?? '启用') === '启用').map((x: any) => x.value ?? x.item_value).filter(Boolean)
    if (vals.length) { expenseTypes.value = vals; if (!vals.includes(ef.value.expenseType)) ef.value.expenseType = vals[0] }
  } catch { /* 回退内置默认 */ }
}
onMounted(() => { loadR(); loadE(); loadExpenseTypes() })
</script>

<style scoped>
.bar { display: flex; align-items: center; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
.stag { display: inline-block; padding: 1px 9px; border-radius: 10px; font-size: 12px; line-height: 18px; font-weight: 600; white-space: nowrap; }
</style>
