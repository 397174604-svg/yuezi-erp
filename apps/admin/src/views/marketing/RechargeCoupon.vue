<template>
  <div>
    <div class="bar"><h2 class="ph">充值 · 优惠券操作台</h2></div>
    <el-tabs v-model="tab">
      <!-- 储值充值赠送 -->
      <el-tab-pane label="储值充值" name="recharge">
        <el-card shadow="never" class="card">
          <el-form :inline="true" :model="rf" size="small">
            <el-form-item label="客户ID"><el-input v-model="rf.customerId" style="width:110px" /></el-form-item>
            <el-form-item label="充值金额"><el-input v-model="rf.amount" style="width:130px" placeholder="￥" /></el-form-item>
            <el-form-item label="支付方式">
              <el-select v-model="rf.payMethod" style="width:120px"><el-option v-for="m in payMethods" :key="m" :label="m" :value="m" /></el-select>
            </el-form-item>
            <el-form-item v-if="!auth.isHQ"><el-button type="primary" :loading="rSaving" @click="doRecharge">充值入账</el-button></el-form-item>
            <el-form-item v-else><el-tag type="info" effect="plain" size="small">总部只读 · 充值入账由门店前台/收银</el-tag></el-form-item>
          </el-form>
          <el-alert v-if="rResult" :title="rResultText" type="success" :closable="false" show-icon class="mb" />
          <div class="sub">赠送阶梯 <el-button link type="primary" size="small" @click="loadTiers">刷新</el-button></div>
          <el-table :data="tiers" size="small" border empty-text="未配置阶梯">
            <el-table-column label="满(元)" prop="threshold" width="120" /><el-table-column label="送(元)" prop="gift" width="120" />
            <el-table-column label="状态" prop="status" width="100" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 优惠券 -->
      <el-tab-pane label="优惠券" name="coupon">
        <el-card shadow="never" class="card">
          <div class="sub">券模板 <el-button link type="success" size="small" @click="tplDialog = true">+ 新建模板</el-button> <el-button link type="primary" size="small" @click="loadTemplates">刷新</el-button></div>
          <el-table :data="templates" size="small" border empty-text="暂无模板">
            <el-table-column prop="tpl_id" label="#" width="56" /><el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="type" label="类型" width="110" /><el-table-column prop="threshold" label="门槛" width="90" />
            <el-table-column prop="benefit" label="权益" width="90" />
            <el-table-column label="发放" width="100"><template #default="{ row }">{{ row.issued_qty }}/{{ row.total_qty || '不限' }}</template></el-table-column>
            <el-table-column label="操作" width="110" fixed="right"><template #default="{ row }"><el-button link type="primary" size="small" @click="openIssue(row)">发券</el-button></template></el-table-column>
          </el-table>
        </el-card>
        <el-card shadow="never" class="card">
          <div class="sub">已发券 <el-button link type="primary" size="small" @click="loadCoupons">刷新</el-button></div>
          <el-table :data="coupons" size="small" border empty-text="暂无券">
            <el-table-column prop="code" label="券码" min-width="140" /><el-table-column prop="type" label="类型" width="110" />
            <el-table-column prop="customer_id" label="客户" width="80" /><el-table-column prop="expire_date" label="到期" width="120" />
            <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="COUPON_TAG[row.status] || 'info'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
            <el-table-column label="操作" width="110" fixed="right"><template #default="{ row }"><el-button v-if="row.status === '未使用'" link type="warning" size="small" @click="doRedeem(row)">核销</el-button></template></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建模板 -->
    <el-dialog v-model="tplDialog" title="新建券模板" width="460px">
      <el-form :model="tplForm" label-width="84px" size="small">
        <el-form-item label="名称"><el-input v-model="tplForm.name" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="tplForm.type"><el-option v-for="t in couponTypes" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="门槛(满)"><el-input v-model="tplForm.threshold" placeholder="满减券必填" /></el-form-item>
        <el-form-item label="权益"><el-input v-model="tplForm.benefit" placeholder="减额；折扣券填0-1" /></el-form-item>
        <el-form-item label="有效天数"><el-input v-model="tplForm.validDays" /></el-form-item>
        <el-form-item label="发放限额"><el-input v-model="tplForm.totalQty" placeholder="0=不限" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="tplDialog = false">取消</el-button><el-button type="primary" @click="saveTpl">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore() // 券模板/发券/积分=管理配置(HQ可);但「充值入账」是收银一线动作,总部不直接给客户充值

const tab = ref('recharge')
const payMethods = ['微信支付', '支付宝', '现金', '银行卡', 'POS机刷卡']
const couponTypes = ['满减券', '折扣券', '代金券', '兑换券']
// 券状态语义色：未使用=可用(绿)、已使用=中性(灰)、已过期/已作废=失效(红)
const COUPON_TAG: Record<string, string> = { 未使用: 'success', 已使用: 'info', 已过期: 'danger', 已作废: 'danger' }

// —— 充值 ——
const rf = ref({ customerId: '', amount: '', payMethod: '微信支付' })
const rSaving = ref(false)
const rResult = ref<any>(null)
const rResultText = ref('')
const tiers = ref<any[]>([])
async function doRecharge() {
  if (!rf.value.customerId || !Number(rf.value.amount)) { ElMessage.warning('客户ID、金额必填'); return }
  rSaving.value = true
  try {
    const r: any = await api().recharge({ customerId: Number(rf.value.customerId), amount: Number(rf.value.amount), payMethod: rf.value.payMethod })
    rResult.value = r
    rResultText.value = `充值 ¥${r.amount} + 赠 ¥${r.gift} = 入账 ¥${r.total}，当前储值余额 ¥${r.balance}`
    ElMessage.success('充值成功')
  } catch (e: any) { ElMessage.error('充值失败：' + (e?.message || '')) }
  finally { rSaving.value = false }
}
async function loadTiers() { try { tiers.value = (await api().listRechargeTiers({})) as any[] || [] } catch { tiers.value = [] } }

// —— 优惠券 ——
const templates = ref<any[]>([])
const coupons = ref<any[]>([])
const tplDialog = ref(false)
const tplForm = ref({ name: '', type: '满减券', threshold: '', benefit: '', validDays: '30', totalQty: '0' })
async function loadTemplates() { try { templates.value = (await api().listCouponTemplates({})) as any[] || [] } catch { templates.value = [] } }
async function loadCoupons() { try { coupons.value = (await api().listCoupons({})) as any[] || [] } catch { coupons.value = [] } }
async function saveTpl() {
  if (!tplForm.value.name || !Number(tplForm.value.benefit)) { ElMessage.warning('名称、权益必填'); return }
  try {
    await api().createCouponTemplate({ name: tplForm.value.name, type: tplForm.value.type, threshold: Number(tplForm.value.threshold) || 0, benefit: Number(tplForm.value.benefit), validDays: Number(tplForm.value.validDays) || 30, totalQty: Number(tplForm.value.totalQty) || 0 })
    ElMessage.success('模板已建'); tplDialog.value = false; loadTemplates()
  } catch (e: any) { ElMessage.error('建模板失败：' + (e?.message || '')) }
}
async function openIssue(row: any) {
  try {
    const { value } = await ElMessageBox.prompt(`给哪位客户发「${row.name}」？填客户ID`, '发券', { inputPattern: /^\d+$/, inputErrorMessage: '请输入客户ID' })
    await api().issueCoupon({ tplId: row.tpl_id, customerId: Number(value) })
    ElMessage.success('发券成功'); loadTemplates(); loadCoupons()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('发券失败：' + (e?.message || '')) }
}
async function doRedeem(row: any) {
  try {
    await api().redeemCoupon(row.coupon_id, row.type === '满减券' ? { orderAmount: Number((await ElMessageBox.prompt('满减券核销需订单金额', '核销', { inputPattern: /^\d+(\.\d+)?$/ })).value) } : {})
    ElMessage.success('核销成功'); loadCoupons()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('核销失败：' + (e?.message || '')) }
}

onMounted(() => { loadTiers(); loadTemplates(); loadCoupons() })
</script>

<style scoped>
.bar { display: flex; align-items: center; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
.sub { font-weight: 600; margin: 6px 0 8px; }
.mb { margin-bottom: 12px; }
</style>
