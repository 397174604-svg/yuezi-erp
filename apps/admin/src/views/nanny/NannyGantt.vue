<template>
  <div>
    <div class="bar"><h2 class="ph">月嫂档期 · 派工结算</h2></div>
    <el-tabs v-model="tab">
      <!-- 档期甘特 -->
      <el-tab-pane label="档期甘特" name="gantt">
        <el-card shadow="never" class="card">
          <el-form :inline="true" size="small">
            <el-form-item label="起"><el-date-picker v-model="g.from" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:150px" /></el-form-item>
            <el-form-item label="止"><el-date-picker v-model="g.to" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:150px" /></el-form-item>
            <el-form-item><el-button type="primary" @click="loadGantt">查询</el-button></el-form-item>
          </el-form>
          <el-alert v-if="conflicts.length" :title="'撞单告警：月嫂 ' + conflicts.join('、') + ' 档期重叠'" type="error" :closable="false" show-icon class="mb" />
          <div v-if="lanes.length" class="gantt">
            <div v-for="lane in lanes" :key="lane.nannyId" class="lane">
              <div class="lane-h"><el-tag :type="lane.overlap ? 'danger' : 'info'" size="small">月嫂#{{ lane.nannyId }}</el-tag><span v-if="lane.overlap" class="warn">撞单</span></div>
              <div class="track">
                <div v-for="(s, i) in lane.segments" :key="i" class="seg" :class="'st-' + s.status" :style="barStyle(s)" :title="'客户#' + s.customer_id + ' ' + (s.start_date || '') + '~' + (s.end_date || '') + ' [' + s.status + ']'">客户#{{ s.customer_id }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="该窗口暂无派工" />
        </el-card>
      </el-tab-pane>

      <!-- 派工奖惩结算 -->
      <el-tab-pane label="派工奖惩结算" name="reward">
        <el-card shadow="never" class="card">
          <el-form :inline="true" size="small">
            <el-form-item label="派工单"><el-select v-model="r.dispatchId" filterable placeholder="选择派工单" style="width:300px" @change="loadReward"><el-option v-for="d in dispatches" :key="d.dispatch_id" :label="dispatchLabel(d)" :value="d.dispatch_id" /></el-select></el-form-item>
          </el-form>
          <template v-if="r.dispatchId">
            <el-form :inline="true" size="small">
              <el-form-item label="类型"><el-select v-model="r.kind" style="width:120px"><el-option v-for="k in KINDS" :key="k" :label="k" :value="k" /></el-select></el-form-item>
              <el-form-item label="金额"><el-input v-model="r.amount" style="width:120px" placeholder="正数" /></el-form-item>
              <el-form-item label="事由"><el-input v-model="r.reason" style="width:160px" /></el-form-item>
              <el-form-item><el-button type="primary" @click="addReward">登记奖惩</el-button></el-form-item>
            </el-form>
            <div v-if="settle" class="settle">
              <el-statistic title="基础工费" :value="settle.baseFee" prefix="¥" />
              <el-statistic title="奖金合计" :value="settle.rewardTotal" prefix="¥" />
              <el-statistic title="惩罚合计" :value="settle.penalty" prefix="¥" />
              <el-statistic title="净结算" :value="settle.net" prefix="¥" />
            </div>
            <el-table :data="rewards" border stripe size="small" empty-text="暂无奖惩" class="mt">
              <el-table-column prop="kind" label="类型" width="100" />
              <el-table-column label="金额" width="120" align="right"><template #default="{ row }"><span :class="Number(row.amount) < 0 ? 'neg' : 'pos'">{{ money(row.amount) }}</span></template></el-table-column>
              <el-table-column prop="reason" label="事由" min-width="160" />
            </el-table>
          </template>
          <el-empty v-else description="先选择派工单" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const KINDS = ['续单奖', '签单奖', '锦旗奖', '其它奖', '惩罚']
const money = (v: any) => (Number(v) < 0 ? '-¥' : '¥') + Math.abs(Number(v) || 0).toLocaleString()
const tab = ref('gantt')

const g = ref({ from: '', to: '' })
const lanes = ref<any[]>([]); const conflicts = ref<number[]>([])
const r = ref<any>({ dispatchId: '', kind: '续单奖', amount: '', reason: '' })
const dispatches = ref<any[]>([]); const rewards = ref<any[]>([]); const settle = ref<any>(null)

// 把派工日期段映射成轨道内的 left%/width%；缺省窗口=今天起 30 天。
function win() {
  const from = g.value.from || new Date().toISOString().slice(0, 10)
  const f = new Date(from + 'T00:00:00').getTime()
  const t = g.value.to ? new Date(g.value.to + 'T00:00:00').getTime() : f + 30 * 864e5
  return { f, span: Math.max(t - f, 864e5) }
}
function barStyle(s: any) {
  const { f, span } = win()
  const norm = (d: string) => d ? new Date(String(d).replace(/\//g, '-').slice(0, 10) + 'T00:00:00').getTime() : f
  const a = norm(s.start_date), b = Math.max(norm(s.end_date), a + 864e5)
  const left = Math.max(0, Math.min(100, ((a - f) / span) * 100))
  const width = Math.max(4, Math.min(100 - left, ((b - a) / span) * 100))
  return { left: left + '%', width: width + '%' }
}

async function loadGantt() {
  try { const res: any = await api().nannyGantt({ from: g.value.from || undefined, to: g.value.to || undefined }); lanes.value = res?.lanes || []; conflicts.value = res?.conflicts || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); lanes.value = []; conflicts.value = [] }
}
function dispatchLabel(d: any) { return `#${d.dispatch_id} 月嫂${d.nanny_id ?? '?'}→客户${d.customer_id ?? '?'} ${d.start_date || ''}` }
async function loadDispatches() { try { dispatches.value = (await api().listDispatch({})) as any[] || [] } catch { dispatches.value = [] } }
async function loadReward() {
  if (!r.value.dispatchId) return
  try { settle.value = await api().dispatchSettlement(r.value.dispatchId); rewards.value = (await api().listDispatchRewards({ dispatchId: Number(r.value.dispatchId) })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
}
async function addReward() {
  if (!Number(r.value.amount)) { ElMessage.warning('金额必填（正数，惩罚类自动转负）'); return }
  try { await api().addDispatchReward(r.value.dispatchId, { kind: r.value.kind, amount: Number(r.value.amount), reason: r.value.reason || undefined }); ElMessage.success('已登记'); r.value.amount = ''; r.value.reason = ''; loadReward() }
  catch (e: any) { ElMessage.error('登记失败：' + (e?.message || '')) }
}
onMounted(() => { loadGantt(); loadDispatches() })
</script>

<style scoped>
.bar { display: flex; align-items: center; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
.mb { margin-bottom: 12px; }
.mt { margin-top: 12px; }
.gantt { display: flex; flex-direction: column; gap: 10px; }
.lane { display: flex; align-items: center; gap: 10px; }
.lane-h { width: 120px; flex: 0 0 120px; display: flex; align-items: center; gap: 6px; }
.warn { color: var(--el-color-danger); font-size: 12px; }
.track { position: relative; height: 26px; flex: 1; background: var(--el-fill-color-light); border-radius: 4px; }
.seg { position: absolute; top: 3px; height: 20px; line-height: 20px; font-size: 11px; color: #fff; border-radius: 3px; padding: 0 4px; overflow: hidden; white-space: nowrap; box-sizing: border-box; background: var(--el-color-primary); }
.st-上户, .st-在户 { background: var(--el-color-success); }
.st-预约, .st-待派工 { background: var(--el-color-warning); }
.st-请假 { background: var(--el-color-info); }
.settle { display: flex; gap: 32px; margin: 8px 0 4px; }
.neg { color: var(--el-color-danger); }
.pos { color: var(--el-color-success); }
</style>
