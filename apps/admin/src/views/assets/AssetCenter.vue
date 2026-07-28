<template>
  <div>
    <h2 class="ph">资产与账单</h2>
    <el-tabs v-model="tab" @tab-change="onTab">
      <!-- 账单（应收实收分离） -->
      <el-tab-pane label="账单" name="bills">
        <div class="bar">
          <el-input v-model="billCustomer" placeholder="客户号" clearable size="small" style="width: 130px" @keyup.enter="loadBills" />
          <el-select v-model="billStatus" placeholder="状态" clearable size="small" style="width: 130px" @change="loadBills">
            <el-option v-for="s in BILL_STATUS" :key="s" :label="s" :value="s" />
          </el-select>
          <el-button type="primary" size="small" @click="loadBills">查询</el-button>
          <el-button size="small" @click="openIssueBill">开账单</el-button>
        </div>
        <el-table :data="bills" v-loading="loadingB" border stripe empty-text="暂无账单">
          <el-table-column prop="bill_no" label="账单号" min-width="150" show-overflow-tooltip />
          <el-table-column prop="customer_id" label="客户" width="80" />
          <el-table-column prop="bill_type" label="类型" width="90" />
          <el-table-column label="应收" width="110" align="right"><template #default="{ row }">{{ money(row.amount) }}</template></el-table-column>
          <el-table-column label="实收" width="110" align="right"><template #default="{ row }"><span class="paid">{{ money(row.paid_amount) }}</span></template></el-table-column>
          <el-table-column label="待收" width="110" align="right"><template #default="{ row }"><span class="due">{{ money(row.due) }}</span></template></el-table-column>
          <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="billTag(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status !== '已结清' && row.status !== '已退款'" link type="primary" size="small" @click="openPay(row)">收款</el-button>
              <el-button v-if="row.status !== '已结清' && row.status !== '已退款'" link type="warning" size="small" @click="onlinePay(row)">在线支付</el-button>
              <el-button v-if="row.status !== '已退款'" link type="danger" size="small" @click="onRefundBill(row)">退款</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 次卡 -->
      <el-tab-pane label="次卡" name="cards">
        <div class="bar">
          <el-input v-model="cardCustomer" placeholder="客户号" clearable size="small" style="width: 130px" @keyup.enter="loadCards" />
          <el-button type="primary" size="small" @click="loadCards">查询</el-button>
          <el-button size="small" @click="openIssueCard">发卡</el-button>
        </div>
        <el-table :data="cards" v-loading="loadingC" border stripe empty-text="暂无次卡">
          <el-table-column prop="name" label="次卡" min-width="140" />
          <el-table-column prop="customer_id" label="客户" width="80" />
          <el-table-column prop="total_count" label="总次" width="80" align="right" />
          <el-table-column prop="used_count" label="已用" width="80" align="right" />
          <el-table-column label="剩余" width="90" align="right"><template #default="{ row }"><span class="remain serif">{{ row.remain_count }}</span></template></el-table-column>
          <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.status === '生效' ? 'success' : 'info'" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }"><el-button v-if="row.status === '生效'" link type="primary" size="small" @click="openConsume(row)">核销</el-button></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 支付单 -->
      <el-tab-pane label="支付单" name="pays">
        <div class="bar"><el-button type="primary" size="small" @click="loadPays">刷新</el-button><span class="muted">线上支付单（宝妈端发起，回调幂等入账）；PC 仅查看 / 退款</span></div>
        <el-table :data="pays" v-loading="loadingP" border stripe empty-text="暂无支付单">
          <el-table-column prop="pay_no" label="支付单号" min-width="180" show-overflow-tooltip />
          <el-table-column prop="provider" label="渠道" width="90" />
          <el-table-column label="金额" width="110" align="right"><template #default="{ row }">{{ money(row.amount) }}</template></el-table-column>
          <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="payTag(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
          <el-table-column prop="created_at" label="创建" min-width="160" />
          <el-table-column label="操作" width="90" fixed="right"><template #default="{ row }"><el-button v-if="row.status === '已支付'" link type="danger" size="small" @click="onRefundPay(row)">退款</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 收款 -->
    <el-dialog v-model="payVisible" title="账单收款" width="420px">
      <el-form label-width="90px">
        <el-form-item label="账单号"><span>{{ cur.bill_no }}</span></el-form-item>
        <el-form-item label="待收"><span class="due">{{ money(cur.due) }}</span></el-form-item>
        <el-form-item label="本次收款"><el-input-number v-model="payAmount" :min="0.01" :max="Number(cur.due) || undefined" :step="100" controls-position="right" style="width: 180px" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="payVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitPay">确认收款</el-button></template>
    </el-dialog>

    <!-- 开账单 -->
    <el-dialog v-model="billVisible" title="开账单" width="440px">
      <el-form label-width="90px">
        <el-form-item label="客户号"><el-input-number v-model="billForm.customerId" :min="1" controls-position="right" style="width: 180px" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="billForm.billType" style="width: 180px"><el-option v-for="t in BILL_TYPE" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="应收金额"><el-input-number v-model="billForm.amount" :min="0" :step="1000" controls-position="right" style="width: 180px" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="billVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitBill">开单</el-button></template>
    </el-dialog>

    <!-- 发卡 -->
    <el-dialog v-model="cardVisible" title="发次卡" width="440px">
      <el-form label-width="90px">
        <el-form-item label="客户号"><el-input-number v-model="cardForm.customerId" :min="1" controls-position="right" style="width: 180px" /></el-form-item>
        <el-form-item label="次卡名"><el-input v-model="cardForm.name" placeholder="如 盆底修复10次" /></el-form-item>
        <el-form-item label="总次数"><el-input-number v-model="cardForm.totalCount" :min="1" :step="1" controls-position="right" style="width: 180px" /></el-form-item>
        <el-form-item label="售价(预收)"><el-input-number v-model="cardForm.totalAmount" :min="0" :precision="2" :step="100" controls-position="right" style="width: 180px" /><span class="unit-hint">单次 ¥{{ cardForm.totalCount > 0 ? (Math.round(cardForm.totalAmount / cardForm.totalCount * 100) / 100).toLocaleString() : 0 }}</span></el-form-item>
      </el-form>
      <template #footer><el-button @click="cardVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitCard">发卡</el-button></template>
    </el-dialog>

    <!-- 核销 -->
    <el-dialog v-model="consumeVisible" title="次卡核销" width="400px">
      <el-form label-width="90px">
        <el-form-item label="次卡"><span>{{ cur.name }}</span></el-form-item>
        <el-form-item label="剩余"><span class="remain">{{ cur.remain_count }}</span></el-form-item>
        <el-form-item label="本次核销"><el-input-number v-model="consumeN" :min="1" :max="Number(cur.remain_count) || 1" :step="1" controls-position="right" style="width: 160px" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="consumeVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitConsume">确认核销</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const BILL_STATUS = ['待支付', '部分支付', '已结清', '已退款']
const BILL_TYPE = ['套餐款', '加项', '房费', '赔偿', '退款']
const money = (n: any) => '¥' + Number(n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
// 待支付=info(中性起始) / 部分支付=warning(进行中) / 已结清=success / 已退款=danger —— 四态四色
const billTag = (s: string) => (s === '已结清' ? 'success' : s === '部分支付' ? 'warning' : s === '已退款' ? 'danger' : 'info')

const tab = ref('bills')
const cur = ref<any>({})
const saving = ref(false)

// 账单
const bills = ref<any[]>([]); const loadingB = ref(false)
const billCustomer = ref(''); const billStatus = ref('')
async function loadBills() {
  loadingB.value = true
  try { bills.value = (await api().listBills({ customerId: billCustomer.value || undefined, status: billStatus.value || undefined })) as any[] }
  catch (e: any) { ElMessage.error('账单加载失败：' + (e?.message || '')); bills.value = [] } finally { loadingB.value = false }
}
const payVisible = ref(false); const payAmount = ref(0)
function openPay(row: any) { cur.value = row; payAmount.value = Number(row.due) || 0; payVisible.value = true }
async function submitPay() {
  saving.value = true
  try { await api().payBill(cur.value.bill_id, { amount: payAmount.value }); ElMessage.success('收款成功'); payVisible.value = false; await loadBills() }
  catch (e: any) { ElMessage.error('收款失败：' + (e?.message || '')) } finally { saving.value = false }
}
// 在线支付：开账单→建支付单(sandbox)→模拟到账→回调幂等收款落账单（串联 M3+M4）
async function onlinePay(row: any) {
  const due = Number(row.due) || 0
  if (due <= 0) { ElMessage.warning('该账单无待收金额'); return }
  try { await ElMessageBox.confirm(`为账单「${row.bill_no}」生成在线支付单 ${money(due)}（sandbox 演示，将模拟到账并自动收款）？`, '在线支付', { type: 'info' }) } catch { return }
  saving.value = true
  try {
    const pay: any = await api().createPayment({ amount: due, provider: 'sandbox', billId: row.bill_id, customerId: row.customer_id })
    await api().sandboxPay(pay.payNo)
    ElMessage.success('支付成功，账单已收款')
    await loadBills(); pays.value = []
  } catch (e: any) { ElMessage.error('在线支付失败：' + (e?.message || '')) } finally { saving.value = false }
}
async function onRefundBill(row: any) {
  try { await ElMessageBox.confirm(`确认退款账单「${row.bill_no}」？`, '退款确认', { type: 'warning' }) } catch { return }
  try { await api().refundBill(row.bill_id, {}); ElMessage.success('已退款'); await loadBills() } catch (e: any) { ElMessage.error('退款失败：' + (e?.message || '')) }
}
const billVisible = ref(false); const billForm = reactive({ customerId: 1, billType: '套餐款', amount: 28800 })
function openIssueBill() { billVisible.value = true }
async function submitBill() {
  saving.value = true
  try { await api().issueBill({ ...billForm }); ElMessage.success('账单已开'); billVisible.value = false; await loadBills() }
  catch (e: any) { ElMessage.error('开单失败：' + (e?.message || '')) } finally { saving.value = false }
}

// 次卡
const cards = ref<any[]>([]); const loadingC = ref(false); const cardCustomer = ref('')
async function loadCards() {
  loadingC.value = true
  try { cards.value = (await api().listCards({ customerId: cardCustomer.value || undefined })) as any[] }
  catch (e: any) { ElMessage.error('次卡加载失败：' + (e?.message || '')); cards.value = [] } finally { loadingC.value = false }
}
const cardVisible = ref(false); const cardForm = reactive({ customerId: 1, name: '盆底修复10次', totalCount: 10, totalAmount: 2800 })
function openIssueCard() { cardVisible.value = true }
async function submitCard() {
  saving.value = true
  try { await api().issueCard({ ...cardForm }); ElMessage.success('次卡已发'); cardVisible.value = false; await loadCards() }
  catch (e: any) { ElMessage.error('发卡失败：' + (e?.message || '')) } finally { saving.value = false }
}
const consumeVisible = ref(false); const consumeN = ref(1)
function openConsume(row: any) { cur.value = row; consumeN.value = 1; consumeVisible.value = true }
async function submitConsume() {
  saving.value = true
  try { await api().consumeCard(cur.value.card_id, { count: consumeN.value, bizRef: 'pc-admin' }); ElMessage.success('核销成功'); consumeVisible.value = false; await loadCards() }
  catch (e: any) { ElMessage.error('核销失败：' + (e?.message || '')) } finally { saving.value = false }
}

// 支付单
const pays = ref<any[]>([]); const loadingP = ref(false)
// 已支付=success / 已退款=danger(资金冲销) / 已关闭=info(中性终态) / 其它(待支付·处理中)=warning
const payTag = (s: string) => (s === '已支付' ? 'success' : s === '已退款' ? 'danger' : s === '已关闭' ? 'info' : 'warning')
async function loadPays() {
  loadingP.value = true
  try { pays.value = (await api().listPayments({})) as any[] }
  catch (e: any) { ElMessage.error('支付单加载失败：' + (e?.message || '')); pays.value = [] } finally { loadingP.value = false }
}
async function onRefundPay(row: any) {
  try { await ElMessageBox.confirm(`确认退款支付单「${row.pay_no}」？`, '退款确认', { type: 'warning' }) } catch { return }
  try { await api().refundPayment(row.pay_no, {}); ElMessage.success('已退款'); await loadPays() } catch (e: any) { ElMessage.error('退款失败：' + (e?.message || '')) }
}

function onTab(name: string) { if (name === 'cards' && !cards.value.length) loadCards(); if (name === 'pays' && !pays.value.length) loadPays() }
onMounted(loadBills)
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 10px; }
.bar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.paid { color: var(--gold-deep); font-weight: 600; }
.due { color: var(--danger); font-weight: 600; }
.remain { color: var(--gold-deep); font-weight: 700; }
</style>
