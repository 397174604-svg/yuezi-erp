<template>
  <div>
    <div class="bar">
      <h2 class="ph">充值经营报表</h2>
      <div class="ops">
        <el-date-picker v-model="f.from" type="date" value-format="YYYY-MM-DD" placeholder="开始" size="small" style="width:140px" />
        <el-date-picker v-model="f.to" type="date" value-format="YYYY-MM-DD" placeholder="结束" size="small" style="width:140px" />
        <el-input v-model="f.storeId" placeholder="门店ID" size="small" style="width:90px" clearable />
        <el-button size="small" type="primary" :loading="loading" @click="load">统计</el-button>
        <el-button size="small" :disabled="!d" @click="exportCsv">导出CSV</el-button>
      </div>
    </div>

    <div v-if="s" class="cards">
      <el-card shadow="never" class="kpi"><div class="t">充值总额</div><div class="v">{{ money(s.totalAmount) }}</div><div class="x">{{ s.rechargeCount }} 笔 · {{ s.customerCount }} 人</div></el-card>
      <el-card shadow="never" class="kpi"><div class="t">赠送总额</div><div class="v warn">{{ money(s.totalGift) }}</div><div class="x">营销成本</div></el-card>
      <el-card shadow="never" class="kpi"><div class="t">入账合计</div><div class="v">{{ money(s.totalCredited) }}</div><div class="x">均充 {{ money(s.avgRecharge) }}</div></el-card>
      <el-card shadow="never" class="kpi hero"><div class="t">储值余额池</div><div class="v">{{ money(d.walletPool.totalBalance) }}</div><div class="x">{{ d.walletPool.customerCount }} 位会员未消费</div></el-card>
    </div>

    <div class="panes">
      <el-card shadow="never" class="pane">
        <template #header><b>按充值档位</b></template>
        <el-table :data="d ? d.byTier : []" v-loading="loading" border size="small" empty-text="暂无充值">
          <el-table-column label="档位门槛" min-width="120"><template #default="{ row }">{{ row.threshold != null ? '满' + money(row.threshold) : '无档位' }}</template></el-table-column>
          <el-table-column prop="count" label="笔数" width="80" align="right" />
          <el-table-column label="充值额" min-width="120" align="right"><template #default="{ row }">{{ money(row.totalAmount) }}</template></el-table-column>
          <el-table-column label="赠金" width="110" align="right"><template #default="{ row }">{{ money(row.totalGift) }}</template></el-table-column>
        </el-table>
      </el-card>
      <el-card shadow="never" class="pane">
        <template #header><b>按支付方式</b></template>
        <el-table :data="d ? d.byPayMethod : []" border size="small" empty-text="暂无">
          <el-table-column prop="payMethod" label="方式" min-width="100" />
          <el-table-column prop="count" label="笔数" width="80" align="right" />
          <el-table-column label="入账" min-width="120" align="right"><template #default="{ row }">{{ money(row.totalCredited) }}</template></el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const money = (v: any) => '¥' + (Math.round((Number(v) || 0) * 100) / 100).toLocaleString()
const now = new Date()
const f = ref({ from: now.toISOString().slice(0, 8) + '01', to: now.toISOString().slice(0, 10), storeId: '' })
const d = ref<any>(null)
const s = computed(() => d.value?.summary)
const loading = ref(false)

async function load() {
  loading.value = true
  try { d.value = await api().getRechargeReport({ from: f.value.from || undefined, to: f.value.to || undefined, storeId: f.value.storeId ? Number(f.value.storeId) : undefined }) }
  catch (e: any) { ElMessage.error('统计失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
function exportCsv() {
  if (!d.value) return
  const rows: any[][] = [['充值经营报表', f.value.from + '~' + f.value.to], [], ['指标', '值'],
    ['充值笔数', s.value.rechargeCount], ['充值总额', s.value.totalAmount], ['赠送总额', s.value.totalGift], ['入账合计', s.value.totalCredited], ['平均充值', s.value.avgRecharge], ['储值余额池', d.value.walletPool.totalBalance],
    [], ['档位门槛', '笔数', '充值额', '赠金'], ...d.value.byTier.map((x: any) => [x.threshold ?? '无', x.count, x.totalAmount, x.totalGift])]
  const csv = rows.map((r) => r.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '充值报表.csv'; a.click(); URL.revokeObjectURL(a.href)
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.cards { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.kpi { flex: 1; min-width: 150px; }
.kpi .t { color: var(--el-text-color-secondary); font-size: 13px; }
.kpi .v { font-size: 22px; font-weight: 700; margin-top: 4px; }
.kpi .v.warn { color: var(--el-color-warning); }
.kpi .x { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px; }
.kpi.hero { background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%); color: #fff; }
.kpi.hero .t, .kpi.hero .x { color: rgba(255,255,255,.85); }
.panes { display: grid; grid-template-columns: 1.4fr 1fr; gap: 12px; }
.pane { min-width: 0; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
