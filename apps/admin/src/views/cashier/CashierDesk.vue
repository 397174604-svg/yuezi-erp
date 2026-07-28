<template>
  <div>
    <div class="bar">
      <h2 class="ph">收银台</h2>
      <span class="hint">接待建档 → 结账收银 / 核销次卡 / 储值充值 · 一线闭环(与小程序同一后端·双端同步)</span>
    </div>

    <!-- 选客户 -->
    <el-card shadow="never" class="mb">
      <div class="pick">
        <span class="lbl">客户</span>
        <el-select v-model="custId" filterable placeholder="搜姓名/手机号选客户" style="width:280px" @change="onPickCustomer">
          <el-option v-for="c in customers" :key="c.customer_id" :label="`${c.name}（${c.phone || '—'}）`" :value="c.customer_id" />
        </el-select>
        <template v-if="wallet">
          <span class="wchip">储值余额 <b>¥{{ num(wallet.stored_card_balance) }}</b></span>
          <span class="wchip">积分 <b>{{ num(wallet.points) }}</b></span>
        </template>
        <span v-else class="muted">— 选客户后显示余额 —</span>
      </div>
    </el-card>

    <div class="split">
      <!-- 结账收银 -->
      <el-card shadow="never" class="pane">
        <template #header><b>结账收银</b><span class="muted">选项目加入清单 → 收款</span></template>
        <div class="addln">
          <el-select v-model="pickItem" filterable placeholder="选项目/商品" style="flex:1" @change="addLine">
            <el-option v-for="it in items" :key="it.item_id" :label="`${it.name} · ¥${num(it.sale_price)}`" :value="it.item_id" />
          </el-select>
        </div>
        <el-table :data="lines" size="small" border empty-text="未添加项目" class="mbs">
          <el-table-column prop="name" label="项目" min-width="140" />
          <el-table-column label="单价" width="90" align="right"><template #default="{ row }">¥{{ num(row.price) }}</template></el-table-column>
          <el-table-column label="数量" width="110" align="center"><template #default="{ row }"><el-input-number v-model="row.qty" :min="1" :max="99" size="small" controls-position="right" style="width:90px" /></template></el-table-column>
          <el-table-column label="小计" width="100" align="right"><template #default="{ row }">¥{{ num(row.price * row.qty) }}</template></el-table-column>
          <el-table-column width="50"><template #default="{ $index }"><el-button link type="danger" size="small" @click="lines.splice($index,1)">删</el-button></template></el-table-column>
        </el-table>
        <div class="foot">
          <div class="tot">合计 <b>¥{{ num(total) }}</b></div>
          <el-select v-model="payMethod" size="small" style="width:120px"><el-option v-for="m in PAY_METHODS" :key="m" :label="m" :value="m" /></el-select>
          <el-button type="primary" :loading="paying" :disabled="!custId || !lines.length" @click="doCheckout">结账收款</el-button>
        </div>
      </el-card>

      <div class="side">
        <!-- 储值充值 -->
        <el-card shadow="never" class="pane">
          <template #header><b>储值充值</b></template>
          <div class="rrow">
            <el-input-number v-model="rechargeAmt" :min="0" :step="500" :precision="2" placeholder="充值金额" style="width:150px" />
            <el-select v-model="rechargePay" size="small" style="width:110px"><el-option v-for="m in PAY_METHODS.filter(x=>x!=='储值卡')" :key="m" :label="m" :value="m" /></el-select>
            <el-button type="primary" :loading="recharging" :disabled="!custId || !(rechargeAmt>0)" @click="doRecharge">充值</el-button>
          </div>
        </el-card>

        <!-- 次卡核销 -->
        <el-card shadow="never" class="pane">
          <template #header><b>次卡核销</b><span class="muted">{{ custId ? cards.length + ' 张' : '选客户' }}</span></template>
          <div v-if="custId">
            <div v-for="c in cards" :key="c.card_id" class="crow">
              <div class="ci"><span class="cn">{{ c.name }}</span><span class="cr">剩 {{ c.remain_count }}/{{ c.total_count }}</span></div>
              <el-button type="primary" link size="small" :disabled="!(c.remain_count>0)" @click="doConsume(c)">核销1次</el-button>
            </div>
            <el-empty v-if="!cards.length" description="该客户暂无次卡" :image-size="46" />
          </div>
          <el-empty v-else description="选客户后显示次卡" :image-size="46" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const PAY_METHODS = ['现金', '刷卡', '微信支付', '支付宝', '储值卡']
const num = (v: any) => Math.round(Number(v || 0)).toLocaleString()

const customers = ref<any[]>([])
const items = ref<any[]>([])
const custId = ref<number | null>(null)
const wallet = ref<any>(null)
const cards = ref<any[]>([])

const lines = ref<any[]>([])
const pickItem = ref<number | null>(null)
const payMethod = ref('现金')
const paying = ref(false)
const total = computed(() => lines.value.reduce((s, l) => s + Number(l.price) * Number(l.qty), 0))

const rechargeAmt = ref<number>(0)
const rechargePay = ref('现金')
const recharging = ref(false)

async function loadBase() {
  try { customers.value = (await api().listCustomers({ limit: 500 }) as any[]) || [] } catch { customers.value = [] }
  try { items.value = ((await api().listItems({ status: '启用' }) as any[]) || []).filter((i) => Number(i.sale_price) > 0) } catch { items.value = [] }
}

async function onPickCustomer() {
  wallet.value = null; cards.value = []
  if (!custId.value) return
  try { wallet.value = await api().getWallet(custId.value, {}) } catch { wallet.value = null }
  try { cards.value = (await api().listCards({ customerId: custId.value }) as any[]) || [] } catch { cards.value = [] }
}

function addLine(itemId: number) {
  const it = items.value.find((i) => i.item_id === itemId); if (!it) return
  const ex = lines.value.find((l) => l.itemId === itemId)
  if (ex) ex.qty += 1
  else lines.value.push({ itemId, name: it.name, price: Number(it.sale_price), qty: 1 })
  pickItem.value = null
}

async function doCheckout() {
  paying.value = true
  try {
    const r: any = await api().checkout({ customerId: custId.value, lines: lines.value.map((l) => ({ itemId: l.itemId, qty: l.qty })), payMethod: payMethod.value })
    ElMessage.success(`结账成功 · 单号 ${r.orderNo} · 实收 ¥${num(r.paid)}`)
    lines.value = []; await onPickCustomer()
  } catch (e: any) { ElMessage.error('结账失败：' + (e?.message || '')) }
  finally { paying.value = false }
}

async function doRecharge() {
  recharging.value = true
  try {
    await api().recharge({ customerId: custId.value, amount: rechargeAmt.value, payMethod: rechargePay.value })
    ElMessage.success(`充值成功 · ¥${num(rechargeAmt.value)}`)
    rechargeAmt.value = 0; await onPickCustomer()
  } catch (e: any) { ElMessage.error('充值失败：' + (e?.message || '')) }
  finally { recharging.value = false }
}

async function doConsume(c: any) {
  try {
    await ElMessageBox.confirm(`确认核销「${c.name}」1 次？`, '次卡核销', { confirmButtonText: '核销', cancelButtonText: '取消' })
    await api().consumeCard(c.card_id, { count: 1, bizRef: 'pc-收银台' })
    ElMessage.success('核销成功'); await onPickCustomer()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('核销失败：' + (e?.message || '')) }
}

onMounted(loadBase)
</script>

<style scoped>
.bar { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
.mb { margin-bottom: 14px; }
.mbs { margin-bottom: 10px; }
.pick { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.pick .lbl { font-weight: 600; }
.wchip, .pick .wchip { background: var(--el-fill-color-light); border-radius: 14px; padding: 4px 12px; font-size: 13px; }
.wchip b, .pick b { color: #B8945A; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.split { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(280px, 1fr); gap: 14px; align-items: start; }
.pane :deep(.el-card__header) { padding: 10px 14px; }
.pane :deep(.el-card__header) .muted { margin-left: 8px; font-weight: 400; }
.side { display: flex; flex-direction: column; gap: 14px; }
.addln { margin-bottom: 10px; display: flex; }
.foot { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.foot .tot { margin-right: auto; font-size: 14px; }
.foot .tot b { font-size: 20px; color: #B8945A; }
.rrow { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.crow { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 7px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.crow:last-child { border-bottom: 0; }
.crow .cn { font-size: 13px; }
.crow .cr { color: var(--el-text-color-secondary); font-size: 12px; margin-left: 8px; }
@media (max-width: 1100px) { .split { grid-template-columns: 1fr; } }
</style>
