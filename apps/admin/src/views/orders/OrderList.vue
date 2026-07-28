<template>
  <div>
    <h2 class="ph">收银与订单</h2>

    <el-form :inline="true" class="filters">
      <el-form-item><el-input v-model="f.orderNo" placeholder="订单号" clearable style="width: 160px" @keyup.enter="reload" /></el-form-item>
      <el-form-item>
        <el-select v-model="f.status" placeholder="订单状态" clearable style="width: 130px">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="f.payMethod" placeholder="支付方式" clearable style="width: 130px">
          <el-option v-for="p in payMethods" :key="p" :label="p" :value="p" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width: 240px" />
      </el-form-item>
      <el-form-item><el-button type="primary" @click="reload">查询</el-button></el-form-item>
    </el-form>

    <el-table :data="rows" v-loading="loading" border stripe empty-text="暂无订单">
      <el-table-column prop="order_no" label="订单号" width="150" />
      <el-table-column prop="domain" label="业务" width="80" />
      <el-table-column prop="order_status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="statusType(row.order_status)" effect="dark" size="small">{{ row.order_status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="订单额" width="120" align="right"><template #default="{ row }">{{ money(row.order_amount) }}</template></el-table-column>
      <el-table-column label="已收" width="120" align="right"><template #default="{ row }">{{ money(row.paid_amount) }}</template></el-table-column>
      <el-table-column label="待收" width="120" align="right"><template #default="{ row }">{{ money(row.due_amount) }}</template></el-table-column>
      <el-table-column prop="pay_method" label="支付方式" width="110" />
      <el-table-column prop="created_at" label="下单时间" min-width="160" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
          <el-button v-if="isMgr && refundable(row)" link type="danger" size="small" @click="doRefund(row)">退款</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="page" :page-count="pageCount" @current-change="onPage" />
    </div>

    <!-- 订单详情 -->
    <el-dialog v-model="detailVisible" :title="'订单 ' + (detail?.order_no || '')" width="560px">
      <el-descriptions v-if="detail" :column="2" border size="small">
        <el-descriptions-item label="状态">{{ detail.order_status }}</el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ detail.pay_method }}</el-descriptions-item>
        <el-descriptions-item label="订单额">{{ money(detail.order_amount) }}</el-descriptions-item>
        <el-descriptions-item label="已收">{{ money(detail.paid_amount) }}</el-descriptions-item>
        <el-descriptions-item label="待收">{{ money(detail.due_amount) }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ detail.created_at }}</el-descriptions-item>
      </el-descriptions>
      <el-table v-if="detail?.items?.length" :data="detail.items" size="small" border style="margin-top: 14px">
        <el-table-column label="项目/商品" min-width="140"><template #default="{ row }">{{ row.item_name || row.name || row.title || '—' }}</template></el-table-column>
        <el-table-column label="数量" width="70" align="center"><template #default="{ row }">{{ row.qty ?? row.quantity ?? 1 }}</template></el-table-column>
        <el-table-column label="单价" width="100" align="right"><template #default="{ row }">{{ money(row.unit_price ?? row.price) }}</template></el-table-column>
        <el-table-column label="小计" width="100" align="right"><template #default="{ row }">{{ money(row.amount ?? row.subtotal) }}</template></el-table-column>
      </el-table>
      <p v-else-if="detail" class="empty-items">（无明细行）</p>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const isMgr = computed(() => auth.isManager) // 退款=敏感资金冲销,管理层专属;一线不显退款按钮避免死按钮

const statuses = ref<string[]>([])   // 字典 order_status(含已取消/已完成/已发货,此前写死缺一半致 58% 订单不可筛)
const payMethods = ref<string[]>([]) // 字典 pay_method(此前漏'刷卡'多'银行卡')
async function loadDicts() {
  try { const d: any = await api().getDict('order_status'); statuses.value = (d?.items || []).filter((x: any) => (x.status ?? '启用') === '启用').map((x: any) => x.value).filter(Boolean) } catch { /* 回退空 */ }
  try { const d: any = await api().getDict('pay_method'); payMethods.value = (d?.items || []).filter((x: any) => (x.status ?? '启用') === '启用').map((x: any) => x.value).filter(Boolean) } catch { /* 回退空 */ }
}

const rows = ref<any[]>([])
const loading = ref(false)
const f = reactive<{ orderNo: string; status: string; payMethod: string }>({ orderNo: '', status: '', payMethod: '' })
const dateRange = ref<string[] | null>(null)
const page = ref(1)
const pageSize = 20
const hasNext = ref(false)
const pageCount = computed(() => (hasNext.value ? page.value + 1 : page.value))

const detailVisible = ref(false)
const detail = ref<any>(null)

function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function statusType(s: string): string {
  if (['已支付', '已完成'].includes(s)) return 'success'
  if (['部分支付', '待支付', '未支付', '已发货'].includes(s)) return 'warning'
  if (['已退款', '已取消', '已关闭', '已作废'].includes(s)) return 'danger'
  return 'info'
}
function refundable(row: any): boolean {
  return ['已支付', '部分支付'].includes(row.order_status)
}

async function load() {
  loading.value = true
  try {
    const data: any = await api().listOrders({
      orderNo: f.orderNo || undefined,
      status: f.status || undefined,
      payMethod: f.payMethod || undefined,
      dateFrom: dateRange.value?.[0] || undefined,
      dateTo: dateRange.value?.[1] || undefined,
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    })
    const list = Array.isArray(data) ? data : (data?.rows || [])
    rows.value = list
    hasNext.value = list.length === pageSize
  } catch (e: any) {
    ElMessage.error('订单加载失败：' + (e?.message || ''))
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }
function onPage(p: number) { page.value = p; load() }

async function openDetail(row: any) {
  detail.value = row
  detailVisible.value = true
  try { detail.value = await api().getOrder(row.order_no) } catch { /* 用列表行兜底 */ }
}

async function doRefund(row: any) {
  try {
    const { value: reason } = await ElMessageBox.prompt(`确认对订单 ${row.order_no}（${money(row.paid_amount)}）发起退款？`, '退款确认', {
      confirmButtonText: '确认退款', cancelButtonText: '取消', inputPlaceholder: '退款原因（可选）', inputValue: '',
    })
    await api().refundOrder(row.order_no, reason || '后台退款')
    ElMessage.success('退款成功')
    load()
  } catch (e: any) {
    if (e !== 'cancel' && e?.message) ElMessage.error('退款失败：' + e.message)
  }
}

onMounted(() => { load(); loadDicts() })
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 14px; }
.filters { margin-bottom: 6px; }
.pager { margin-top: 14px; display: flex; justify-content: flex-end; }
.empty-items { color: var(--ink-3); font-size: 13px; margin: 12px 0 0; }
</style>
