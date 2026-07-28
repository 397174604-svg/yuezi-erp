<template>
  <div>
    <div class="bar">
      <h2 class="ph">客户中台</h2>
      <div class="filters">
        <el-input v-model="q" placeholder="搜索姓名 / 手机" clearable style="width: 180px" @keyup.enter="reload" />
        <el-select v-model="status" placeholder="状态" clearable style="width: 110px">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-input v-model="source" placeholder="来源" clearable style="width: 120px" @keyup.enter="reload" />
        <el-input v-model="tag" placeholder="标签" clearable style="width: 120px" @keyup.enter="reload" />
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button type="success" @click="openCreate">+ 新建建档</el-button>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe class="tbl" empty-text="暂无客户">
      <el-table-column type="index" label="#" width="56" :index="(i:number) => (page - 1) * pageSize + i + 1" />
      <el-table-column prop="name" label="姓名" min-width="100" show-overflow-tooltip />
      <el-table-column prop="phone" label="手机" min-width="130" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="level" label="会员等级" width="110" />
      <el-table-column label="累计消费" width="130" align="right">
        <template #default="{ row }">{{ row.total_spend != null ? '¥' + Number(row.total_spend).toLocaleString() : '—' }}</template>
      </el-table-column>
      <el-table-column prop="visit_count" label="到店次数" width="100" align="center" />
      <el-table-column prop="source" label="来源" width="110" />
      <el-table-column prop="advisor" label="顾问" width="100" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openCustomer(row)">详情</el-button>
          <el-button link type="warning" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="isMgr" link type="info" size="small" @click="openTransfer(row)">转店</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 客户 360 画像抽屉 -->
    <el-drawer v-model="drawerVisible" :title="cur?.name || '客户详情'" size="460px">
      <div v-loading="detailLoading" class="detail">
        <div v-if="lifecycle.length" class="lc">
          <el-tag v-for="t in lifecycle" :key="t" :type="LC_TYPE[t] || 'info'" effect="dark" size="small" round>{{ t }}</el-tag>
          <span class="muted s">客户生命周期</span>
        </div>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="手机">{{ cur?.phone || '—' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ cur?.status || '—' }}</el-descriptions-item>
          <el-descriptions-item label="等级">{{ cur?.level || '—' }}</el-descriptions-item>
          <el-descriptions-item label="顾问">{{ cur?.advisor || '—' }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ cur?.source || '—' }}</el-descriptions-item>
          <el-descriptions-item label="到店次数">{{ cur?.visit_count ?? '—' }}</el-descriptions-item>
        </el-descriptions>

        <div class="sec">钱包 / 卡额</div>
        <div class="wallet">
          <div class="wcell"><span class="wl">储值卡余额</span><span class="wv serif">{{ money(wallet?.storedCardBalance) }}</span></div>
          <div class="wcell"><span class="wl">积分</span><span class="wv serif">{{ wallet?.points ?? '—' }}</span></div>
        </div>
        <el-table v-if="wallet?.cards?.length" :data="wallet.cards" size="small" border style="margin-top: 8px">
          <el-table-column label="次卡" min-width="120"><template #default="{ row }">{{ row.name }}</template></el-table-column>
          <el-table-column label="剩余/总" width="90" align="center"><template #default="{ row }">{{ row.remain }}/{{ row.total }}</template></el-table-column>
          <el-table-column label="状态" width="70" align="center"><template #default="{ row }">{{ row.expired ? '已过期' : '有效' }}</template></el-table-column>
        </el-table>

        <div class="sec">标签</div>
        <div class="tags">
          <el-tag v-for="t in tags" :key="t" effect="plain" class="t">{{ t }}</el-tag>
          <span v-if="!tags.length" class="muted">暂无标签</span>
        </div>

        <div class="sec">近期订单</div>
        <el-table v-if="recentOrders.length" :data="recentOrders" size="small" border>
          <el-table-column prop="order_no" label="订单号" min-width="140" />
          <el-table-column label="金额" width="110" align="right"><template #default="{ row }">{{ money(row.order_amount) }}</template></el-table-column>
          <el-table-column prop="order_status" label="状态" width="90" />
        </el-table>
        <span v-else class="muted">暂无订单</span>

        <div class="sec">次卡资产</div>
        <el-table v-if="cards.length" :data="cards" size="small" border>
          <el-table-column prop="name" label="次卡" min-width="120" />
          <el-table-column label="剩余/总" width="90" align="right"><template #default="{ row }">{{ row.remain_count }}/{{ row.total_count }}</template></el-table-column>
          <el-table-column prop="status" label="状态" width="80" />
        </el-table>
        <span v-else class="muted">暂无次卡</span>

        <div class="sec">账单</div>
        <el-table v-if="bills.length" :data="bills" size="small" border>
          <el-table-column prop="bill_no" label="账单号" min-width="130" show-overflow-tooltip />
          <el-table-column label="应收/实收" width="130" align="right"><template #default="{ row }">{{ money(row.amount) }} / {{ money(row.paid_amount) }}</template></el-table-column>
          <el-table-column prop="status" label="状态" width="90" />
        </el-table>
        <span v-else class="muted">暂无账单</span>

        <div class="sec">宝宝</div>
        <div v-if="babies.length"><el-tag v-for="b in babies" :key="b.baby_id" effect="plain" class="bt">{{ b.name }}（{{ b.gender }}）</el-tag></div>
        <span v-else class="muted">暂无宝宝档案</span>
      </div>
    </el-drawer>

    <div class="pager">
      <el-pagination
        layout="total, prev, pager, next"
        :page-size="pageSize"
        :current-page="page"
        :total="total"
        @current-change="onPage"
      />
    </div>
    <p class="note">列表已接 /api/v1/customers（员工 token，租户隔离）。后端列表暂无 total 总数，分页按「满页则有下一页」推断；C2 阶段后端补 count 后转精确分页。</p>
    <!-- 转店 -->
    <el-dialog v-model="transferVisible" title="客户转店" width="420px">
      <el-form label-width="82px" size="small">
        <el-form-item label="客户">{{ transferRow?.name }}（{{ transferRow?.phone }}）</el-form-item>
        <el-form-item label="目标门店"><el-select v-model="transferStore" placeholder="选择门店" style="width:100%"><el-option v-for="s in stores" :key="s.store_id" :label="s.name" :value="s.store_id" /></el-select></el-form-item>
        <el-form-item label="转店原因"><el-input v-model="transferReason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="transferVisible = false">取消</el-button><el-button type="primary" :loading="transferring" @click="submitTransfer">确认转店</el-button></template>
    </el-dialog>

    <!-- 三段式建档 / 编辑表单（借鉴#12 接出 create / update endpoint） -->
    <el-dialog v-model="formVisible" :title="editId ? '编辑客户档案' : '客户三段式建档'" width="640px">
      <el-form :model="form" label-width="92px" size="small">
        <el-divider content-position="left">① 基本信息</el-divider>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="手机" required><el-input v-model="form.phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="性别"><el-select v-model="form.gender"><el-option label="女" value="女" /><el-option label="男" value="男" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="证件类别"><el-select v-model="form.id_type" clearable><el-option v-for="t in idTypes" :key="t" :label="t" :value="t" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="证件号"><el-input v-model="form.id_no" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="来源"><el-input v-model="form.source" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="顾问"><el-input v-model="form.advisor" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="首要域"><el-select v-model="form.domain_first"><el-option label="月子" value="月子" /><el-option label="产康" value="产康" /><el-option label="科研美容" value="科研美容" /></el-select></el-form-item></el-col>
        </el-row>
        <el-divider content-position="left">② 分娩 / 孕产</el-divider>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="分娩方式"><el-select v-model="form.delivery_type" clearable><el-option v-for="d in deliveryTypes" :key="d" :label="d" :value="d" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="胎次"><el-input v-model="form.parity" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="预产期"><el-input v-model="form.edc" placeholder="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="产检医院"><el-input v-model="form.prenatal_hospital" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="复查时间"><el-input v-model="form.review_date" placeholder="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-divider content-position="left">③ 意向 / 介绍人</el-divider>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="意向房型"><el-input v-model="form.intent_room" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="意向套餐"><el-input v-model="form.intent_package" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="膳食套餐"><el-input v-model="form.meal_package" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="介绍人"><el-input v-model="form.referrer" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="介绍人关系"><el-input v-model="form.referrer_relation" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="介绍人电话"><el-input v-model="form.referrer_phone" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="formVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitForm">{{ editId ? '保存修改' : '保存建档' }}</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isMgr = computed(() => auth.isManager) // 转店=客户跨店分配,店长/管理层专属(后端 manager 门)

const rows = ref<any[]>([])
const loading = ref(false)
const q = ref('')
const status = ref('')
const source = ref('')
const tag = ref('')
const statuses = ref<string[]>([]) // 客户状态：从字典中心 getDict('customer_status') 取，与后端库值一致(此前写死一套库中不存在的状态致筛选全废)
async function loadStatuses() { try { const d: any = await api().getDict('customer_status'); statuses.value = (d?.items || []).filter((x: any) => (x.status ?? '启用') === '启用').map((x: any) => x.value).filter(Boolean) } catch { /* 回退空 */ } }
const page = ref(1)
const pageSize = 20
const total = ref(0)
const stores = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const data: any = await api().listCustomers({
      q: q.value || undefined,
      status: status.value || undefined,
      source: source.value || undefined,
      tag: tag.value || undefined,
      withTotal: 1, // 取真实总数做精确分页
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    })
    rows.value = data?.rows || (Array.isArray(data) ? data : [])
    total.value = data?.total ?? rows.value.length
  } catch (e: any) {
    ElMessage.error('客户列表加载失败：' + (e?.message || ''))
    rows.value = []
  } finally {
    loading.value = false
  }
}
async function loadStores() { try { stores.value = (await api().listStores({}) as any[]) || [] } catch { stores.value = [] } }

function reload() {
  page.value = 1
  load()
}

// —— 三段式建档表单（借鉴#12） ——
const idTypes = ['身份证', '护照', '港澳台通行证', '军官证', '其他']
const deliveryTypes = ['顺产', '剖宫产', '器械助产', '无痛分娩']
const formVisible = ref(false)
const saving = ref(false)
const blankForm = () => ({ name: '', phone: '', gender: '女', id_type: '', id_no: '', source: '', advisor: '', domain_first: '月子', delivery_type: '', parity: '', edc: '', prenatal_hospital: '', review_date: '', intent_room: '', intent_package: '', meal_package: '', referrer: '', referrer_relation: '', referrer_phone: '' })
const form = ref<any>(blankForm())
const editId = ref<number | null>(null)
function openCreate() { editId.value = null; form.value = blankForm(); formVisible.value = true }
function openEdit(row: any) {
  editId.value = row.customer_id
  const f = blankForm()
  for (const k in f) if (row[k] != null) f[k] = row[k] // 用行数据回填已有字段
  form.value = f
  formVisible.value = true
}
async function submitForm() {
  if (!form.value.name || !form.value.phone) { ElMessage.warning('姓名、手机为必填'); return }
  saving.value = true
  try {
    const payload: any = {}
    for (const k in form.value) { if (form.value[k] !== '' && form.value[k] != null) payload[k] = form.value[k] } // 只发非空字段
    if (editId.value) { await api().updateCustomer(editId.value, payload); ElMessage.success('已保存修改') }
    else { await api().createCustomer(payload); ElMessage.success('建档成功') }
    formVisible.value = false
    reload()
  } catch (e: any) { ElMessage.error((editId.value ? '保存失败：' : '建档失败：') + (e?.message || '')) }
  finally { saving.value = false }
}

// —— 转店 ——
const transferVisible = ref(false)
const transferRow = ref<any>(null)
const transferStore = ref<number | null>(null)
const transferReason = ref('')
const transferring = ref(false)
function openTransfer(row: any) { transferRow.value = row; transferStore.value = null; transferReason.value = ''; transferVisible.value = true; if (!stores.value.length) loadStores() }
async function submitTransfer() {
  if (!transferStore.value) { ElMessage.warning('请选择目标门店'); return }
  transferring.value = true
  try {
    await api().transfer(transferRow.value.customer_id, transferStore.value, transferReason.value || undefined)
    ElMessage.success('已转店'); transferVisible.value = false; reload()
  } catch (e: any) { ElMessage.error('转店失败：' + (e?.message || '')) }
  finally { transferring.value = false }
}
function onPage(p: number) {
  page.value = p
  load()
}

// —— 360 画像抽屉 ——
const drawerVisible = ref(false)
const detailLoading = ref(false)
const cur = ref<any>(null)
const wallet = ref<any>(null)
const tags = ref<string[]>([])
const recentOrders = ref<any[]>([])
const cards = ref<any[]>([])
const bills = ref<any[]>([])
const babies = ref<any[]>([])
const lifecycle = ref<string[]>([])
const LC_TYPE: Record<string, string> = { 成: 'success', 预: 'warning', 新: 'primary', 沉: 'info' }

function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function openCustomer(row: any) {
  cur.value = row
  wallet.value = null
  tags.value = []
  recentOrders.value = []
  cards.value = []; bills.value = []; babies.value = []; lifecycle.value = []
  drawerVisible.value = true
  detailLoading.value = true
  const id = row.customer_id
  const [w, tl, tg, cd, bl, bb, lc] = await Promise.all([
    api().getWallet(id).catch(() => null),
    api().getTimeline(id).catch(() => null),
    api().getTags(id).catch(() => []),
    api().listCards({ customerId: id }).catch(() => []),
    api().listBills({ customerId: id }).catch(() => []),
    api().listBabies({ customerId: id }).catch(() => []),
    api().customerLifecycle(id).catch(() => null),
  ])
  lifecycle.value = (lc as any)?.lifecycle || []
  wallet.value = w
  tags.value = Array.isArray(tg) ? tg.map((x: any) => (typeof x === 'string' ? x : x.tag || x.name)).filter(Boolean) : []
  recentOrders.value = (tl?.orders || []).slice(0, 8)
  cards.value = (cd as any[]) || []; bills.value = (bl as any[]) || []; babies.value = (bb as any[]) || []
  detailLoading.value = false
}

onMounted(() => { load(); loadStores(); loadStatuses() })
</script>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.ph {
  font-family: var(--font-cn-serif);
  font-weight: 600;
  margin: 0;
}
.filters {
  display: flex;
  gap: 10px;
}
.tbl {
  background: var(--paper);
  border-radius: var(--r-sm);
}
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
.note {
  font-size: 12px;
  color: var(--ink-3);
  margin-top: 12px;
}
.detail .sec {
  font-family: var(--font-cn-serif);
  font-weight: 600;
  margin: 20px 0 10px;
  padding-left: 10px;
  border-left: 3px solid var(--gold);
}
.wallet {
  display: flex;
  gap: 12px;
}
.wcell {
  flex: 1;
  background: var(--ivory-2);
  border: 1px solid var(--hair);
  border-radius: var(--r-sm);
  padding: 12px 14px;
}
.wcell .wl {
  display: block;
  font-size: 12px;
  color: var(--ink-3);
}
.wcell .wv {
  display: block;
  font-size: 22px;
  color: var(--gold-deep);
  font-weight: 600;
  margin-top: 4px;
}
.tags .t {
  margin: 0 8px 8px 0;
}
.muted {
  color: var(--ink-3);
  font-size: 13px;
}
</style>
