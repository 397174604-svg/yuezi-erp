<template>
  <div>
    <h2 class="ph">财务收支</h2>
    <el-tabs v-model="tab" @tab-change="onTab">
      <!-- 收支台账 -->
      <el-tab-pane label="收支台账" name="ledger">
        <el-row :gutter="14" class="sum" v-loading="loadingS">
          <el-col :span="6"><div class="kpi inc"><div class="kv serif">{{ money(sum.income) }}</div><div class="kl">总收入（已审核）</div></div></el-col>
          <el-col :span="6"><div class="kpi exp"><div class="kv serif">{{ money(sum.expense) }}</div><div class="kl">总支出（已审核）</div></div></el-col>
          <el-col :span="6"><div class="kpi"><div class="kv serif">{{ money(sum.net) }}</div><div class="kl">净额</div></div></el-col>
          <el-col :span="6"><div class="kpi warn"><div class="kv serif">{{ sum.pending ?? 0 }}</div><div class="kl">待审核</div></div></el-col>
        </el-row>

        <div class="bar">
          <el-select v-model="fDir" placeholder="收/支" clearable size="small" style="width: 110px" @change="loadLedger"><el-option label="收入" value="收入" /><el-option label="支出" value="支出" /></el-select>
          <el-select v-model="fStatus" placeholder="状态" clearable size="small" style="width: 120px" @change="loadLedger"><el-option v-for="s in FIN_STATUS" :key="s" :label="s" :value="s" /></el-select>
          <el-button type="primary" size="small" @click="openCreate">新增收支</el-button>
        </div>
        <el-table :data="rows" v-loading="loadingL" border stripe empty-text="暂无收支记录">
          <el-table-column prop="occurred_at" label="发生日" width="120" />
          <el-table-column label="方向" width="80"><template #default="{ row }"><el-tag :type="row.direction === '收入' ? 'success' : 'danger'" effect="dark" size="small">{{ row.direction }}</el-tag></template></el-table-column>
          <el-table-column prop="category" label="类别 / 费源" min-width="130" />
          <el-table-column label="金额" width="130" align="right"><template #default="{ row }">{{ money(row.amount) }}</template></el-table-column>
          <el-table-column prop="handler" label="经手人" width="100" />
          <el-table-column label="审核状态" width="100"><template #default="{ row }"><el-tag :type="stType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === '待审核'" link type="success" size="small" @click="auditLedger(row, true)">通过</el-button>
              <el-button v-if="row.status === '待审核'" link type="danger" size="small" @click="auditLedger(row, false)">驳回</el-button>
              <el-button link type="danger" size="small" @click="removeLedger(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 审批中台 -->
      <el-tab-pane name="approval">
        <template #label>审批中台 <el-badge v-if="inbox.length" :value="inbox.length" class="bdg" /></template>
        <p class="tip">跨域统一收件箱：合同 / 月嫂派工 / 财务收支 的「待审核」汇总于此，审批即回写各业务域。</p>
        <el-table :data="inbox" v-loading="loadingA" border stripe empty-text="暂无待审批事项">
          <el-table-column label="来源" width="110"><template #default="{ row }"><el-tag effect="plain" size="small">{{ row.domain }}</el-tag></template></el-table-column>
          <el-table-column prop="title" label="事项" min-width="200" show-overflow-tooltip />
          <el-table-column label="金额" width="140" align="right"><template #default="{ row }">{{ money(row.amount) }}</template></el-table-column>
          <el-table-column prop="created_at" label="提交时间" width="180" />
          <el-table-column label="审批" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="success" size="small" @click="approve(row, true)">通过</el-button>
              <el-button link type="danger" size="small" @click="approve(row, false)">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增收支 -->
    <el-dialog v-model="formVisible" title="新增收支" width="440px">
      <el-form label-width="86px">
        <el-form-item label="方向"><el-radio-group v-model="form.direction"><el-radio value="收入">收入</el-radio><el-radio value="支出">支出</el-radio></el-radio-group></el-form-item>
        <el-form-item label="类别 / 费源"><el-input v-model="form.category" placeholder="如 房费 / 食材采购" /></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :step="500" /></el-form-item>
        <el-form-item label="经手人"><el-input v-model="form.handler" /></el-form-item>
        <el-form-item label="发生日"><el-date-picker v-model="form.occurredAt" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible = false">取消</el-button><el-button type="primary" @click="saveForm">提交（待审核）</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const FIN_STATUS = ['待审核', '已审核', '已驳回']
const tab = ref('ledger')
const sum = ref<any>({ income: 0, expense: 0, net: 0, pending: 0 })
const rows = ref<any[]>([])
const inbox = ref<any[]>([])
const loadingS = ref(false); const loadingL = ref(false); const loadingA = ref(false)
const fDir = ref(''); const fStatus = ref('')

function money(v: any): string { return v == null ? '—' : '¥' + Number(v).toLocaleString() }
function stType(s: string): string { return s === '已审核' ? 'success' : (s === '已驳回' ? 'danger' : 'warning') }

async function loadSummary() { loadingS.value = true; try { sum.value = await api().getFinanceSummary({}) || {} } catch (e: any) { ElMessage.error('汇总失败：' + (e?.message || '')) } finally { loadingS.value = false } }
async function loadLedger() { loadingL.value = true; try { rows.value = await api().listFinance({ direction: fDir.value || undefined, status: fStatus.value || undefined, limit: 100 }) || [] } catch (e: any) { ElMessage.error('台账失败：' + (e?.message || '')) } finally { loadingL.value = false } }
async function loadApprovals() { loadingA.value = true; try { inbox.value = await api().listApprovals() || [] } catch (e: any) { ElMessage.error('审批收件箱失败：' + (e?.message || '')) } finally { loadingA.value = false } }
function onTab(name: string) { if (name === 'approval') loadApprovals() }
function refreshLedger() { loadSummary(); loadLedger() }

// 新增收支
const formVisible = ref(false)
const form = reactive<any>({ direction: '收入', category: '', amount: 1000, handler: '财务部', occurredAt: '' })
function openCreate() { Object.assign(form, { direction: '收入', category: '', amount: 1000, handler: '财务部', occurredAt: '' }); formVisible.value = true }
async function saveForm() {
  if (!form.category) { ElMessage.warning('类别必填'); return }
  if (!(form.amount > 0)) { ElMessage.warning('金额须大于 0'); return }
  try { await api().createFinance({ direction: form.direction, category: form.category, amount: form.amount, handler: form.handler, occurredAt: form.occurredAt || undefined }); ElMessage.success('已提交，待审核'); formVisible.value = false; refreshLedger() }
  catch (e: any) { ElMessage.error('提交失败：' + (e?.message || '')) }
}

async function auditLedger(row: any, pass: boolean) {
  try {
    let reason = ''
    if (!pass) { const { value } = await ElMessageBox.prompt('驳回原因', '驳回', { inputPlaceholder: '请填写' }); reason = value || '' }
    await api().auditFinance(row.finance_id, pass, reason)
    ElMessage.success(pass ? '已通过' : '已驳回'); refreshLedger()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('审核失败：' + e.message) }
}
async function removeLedger(row: any) {
  try { await ElMessageBox.confirm('确认删除该收支记录？', '确认', { type: 'warning' }); await api().removeFinance(row.finance_id); ElMessage.success('已删除'); refreshLedger() }
  catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('删除失败：' + e.message) }
}

// 审批中台：按 domain 路由到对应域的 audit
async function approve(row: any, pass: boolean) {
  try {
    let reason = ''
    if (!pass) { const { value } = await ElMessageBox.prompt(`驳回「${row.domain}」原因`, '驳回', { inputPlaceholder: '请填写' }); reason = value || '' }
    if (row.domain === '合同') await api().auditContract(row.ref_id, pass, reason)
    else if (row.domain === '月嫂派工') await api().auditDispatch(row.ref_id, pass, reason)
    else if (row.domain === '财务') await api().auditFinance(row.ref_id, pass, reason)
    ElMessage.success(pass ? '已通过' : '已驳回')
    loadApprovals(); refreshLedger()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('审批失败：' + e.message) }
}

onMounted(() => { refreshLedger(); loadApprovals() })
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 8px; }
.sum { margin-bottom: 16px; }
.kpi { background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-md); padding: 18px; text-align: center; }
.kpi .kv { font-size: 26px; color: var(--gold-deep); font-weight: 600; }
.kpi .kl { font-size: 13px; color: var(--ink-3); margin-top: 4px; }
.kpi.inc .kv { color: #577053; } .kpi.exp .kv { color: var(--danger); } .kpi.warn { border-color: var(--warn); }
.bar { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.tip { font-size: 13px; color: var(--ink-3); margin: 0 0 14px; }
.bdg { margin-left: 4px; }
</style>
