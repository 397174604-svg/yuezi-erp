<template>
  <div>
    <div class="bar">
      <h2 class="ph">发票管理</h2>
      <div>
        <el-select v-model="f.status" placeholder="全部状态" clearable size="small" style="width:120px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
        <el-select v-model="f.sourceType" placeholder="全部来源" clearable size="small" style="width:120px" @change="load"><el-option v-for="s in SOURCES" :key="s" :label="s" :value="s" /></el-select>
        <el-button type="primary" @click="openDlg">开具发票</el-button>
      </div>
    </div>
    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无发票">
      <el-table-column prop="invoice_no" label="发票号" min-width="180" />
      <el-table-column prop="invoice_type" label="类型" width="150" />
      <el-table-column prop="title" label="抬头" min-width="140" show-overflow-tooltip />
      <el-table-column label="金额" width="120" align="right"><template #default="{ row }">{{ money(row.amount) }}</template></el-table-column>
      <el-table-column label="税率/税额" width="130" align="right"><template #default="{ row }">{{ row.tax_rate != null ? (Number(row.tax_rate) * 100).toFixed(0) + '%' : '—' }} / {{ row.tax_amount != null ? money(row.tax_amount) : '—' }}</template></el-table-column>
      <el-table-column prop="source_type" label="来源" width="80" />
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.red_flush_of != null ? 'info' : (row.status === '已红冲' ? 'danger' : 'success')" effect="dark" size="small">{{ row.red_flush_of != null ? '冲销单' : row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="90" fixed="right"><template #default="{ row }">
        <el-button v-if="row.status === '正常' && row.red_flush_of == null" link type="danger" size="small" @click="redFlush(row)">红冲</el-button>
      </template></el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="开具发票" width="640px">
      <el-form :model="form" label-width="92px" size="small">
        <el-form-item label="发票类型"><el-select v-model="form.invoiceType" style="width:220px"><el-option v-for="t in TYPES" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="来源"><el-select v-model="form.sourceType" style="width:160px"><el-option v-for="s in SOURCES" :key="s" :label="s" :value="s" /></el-select></el-form-item>
        <el-form-item label="抬头"><el-input v-model="form.title" style="width:320px" /></el-form-item>
        <el-form-item label="金额(含税)"><el-input v-model="form.amount" style="width:160px" /></el-form-item>
        <el-form-item label="税率"><el-input v-model="form.taxRate" style="width:160px" placeholder="0~1，如 0.06，可空（含税倒算税额）" /></el-form-item>
        <el-form-item label="税号"><el-input v-model="form.taxNo" style="width:320px" :placeholder="form.invoiceType === '增值税专用发票' ? '专票必填' : '可选'" /></el-form-item>
        <el-form-item label="注册地址"><el-input v-model="form.regAddress" style="width:320px" /></el-form-item>
        <el-form-item label="注册电话"><el-input v-model="form.regPhone" style="width:200px" /></el-form-item>
        <el-form-item label="开户行"><el-input v-model="form.bank" style="width:320px" /></el-form-item>
        <el-form-item label="银行账号"><el-input v-model="form.bankAccount" style="width:240px" /></el-form-item>
        <el-form-item label="客户ID"><el-input v-model="form.customerId" style="width:140px" placeholder="可选" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" @click="submit">开具</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const TYPES = ['增值税专用发票', '增值税普通发票', '电子普通发票']
const SOURCES = ['收入', '费用', '采购']
const STATUS = ['正常', '已红冲']
const money = (v: any) => v != null ? '¥' + Number(v).toLocaleString() : '—'

const rows = ref<any[]>([]); const loading = ref(false)
const f = ref({ status: '', sourceType: '' })
const dlg = ref(false)
const blank = () => ({ invoiceType: '增值税普通发票', sourceType: '收入', title: '', amount: '', taxRate: '', taxNo: '', regAddress: '', regPhone: '', bank: '', bankAccount: '', customerId: '' })
const form = ref(blank())

async function load() {
  loading.value = true
  try { rows.value = (await api().listInvoices({ status: f.value.status || undefined, sourceType: f.value.sourceType || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
function openDlg() { form.value = blank(); dlg.value = true }
async function submit() {
  const v = form.value
  if (!v.title) { ElMessage.warning('抬头必填'); return }
  if (!Number(v.amount) || Number(v.amount) <= 0) { ElMessage.warning('金额须>0'); return }
  if (v.invoiceType === '增值税专用发票' && !v.taxNo) { ElMessage.warning('专票必须填税号'); return }
  if (v.taxRate !== '' && (!(Number(v.taxRate) >= 0) || Number(v.taxRate) >= 1)) { ElMessage.warning('税率须在 [0,1) 区间'); return }
  try {
    const r: any = await api().createInvoice({
      invoiceType: v.invoiceType, sourceType: v.sourceType, title: v.title, amount: Number(v.amount),
      taxRate: v.taxRate !== '' ? Number(v.taxRate) : undefined, taxNo: v.taxNo || undefined,
      regAddress: v.regAddress || undefined, regPhone: v.regPhone || undefined, bank: v.bank || undefined, bankAccount: v.bankAccount || undefined,
      customerId: v.customerId ? Number(v.customerId) : undefined,
    })
    ElMessage.success(`已开具 ${r?.invoiceNo || ''}（税额 ${r?.taxAmount ?? '—'}）`); dlg.value = false; load()
  } catch (e: any) { ElMessage.error('开票失败：' + (e?.message || '')) }
}
async function redFlush(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('红冲原因（生成负数冲销单，原票标「已红冲」）', '红冲 ' + row.invoice_no, { inputPlaceholder: '可空' })
    await api().redFlushInvoice(row.invoice_id, { reason: value || '' }); ElMessage.success('已红冲'); load()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('红冲失败：' + (e?.message || '')) }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.bar .el-select, .bar .el-button { margin-left: 8px; }
</style>
