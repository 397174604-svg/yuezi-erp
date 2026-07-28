<template>
  <div>
    <div class="bar">
      <h2 class="ph">护理看板 · KPI</h2>
      <div class="ops">
        <el-input v-model="storeId" placeholder="门店ID(可空)" size="small" style="width:130px" clearable @change="load" />
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div v-if="d" class="grid">
      <div class="kpi hero"><div class="t">巡房总数</div><div class="v">{{ d.nursingTotal }}</div></div>
      <div class="kpi"><div class="t">待巡房</div><div class="v" :class="d.pendingRounds ? 'warn' : ''">{{ d.pendingRounds }}</div></div>
      <div class="kpi"><div class="t">进行中</div><div class="v">{{ d.inProgress }}</div></div>
      <div class="kpi"><div class="t">已完成</div><div class="v ok">{{ d.done }}</div></div>
      <div class="kpi"><div class="t">异常</div><div class="v" :class="d.abnormal ? 'bad' : ''">{{ d.abnormal }}</div></div>
      <div class="kpi"><div class="t">母婴同室</div><div class="v">{{ d.roomingIn }}</div></div>
      <div class="kpi"><div class="t">在住房间</div><div class="v">{{ d.liveRooms }}</div></div>
    </div>

    <!-- M-C F078 照护漏记告警：red 红底白字 / amber 金色（7-09 语义色实底规范），空态=暂无漏记 -->
    <el-card shadow="never" class="pane alert-pane" v-loading="loadingA">
      <template #header>
        <b>照护漏记告警</b>
        <el-tag v-if="redCount" type="danger" effect="dark" size="small" class="ml">红灯 {{ redCount }}</el-tag>
        <el-tag v-if="amberCount" type="warning" effect="dark" size="small" class="ml">临近 {{ amberCount }}</el-tag>
        <span v-if="alertData" class="thres">阈值 {{ alertData.thresholdHours }} 小时（系统设置·护理设置可调）</span>
      </template>
      <div v-if="alerts.length" class="alert-list">
        <div v-for="a in alerts" :key="a.customerId" class="alert-row" :class="a.level">
          <span class="an">{{ a.name || '客户#' + a.customerId }}</span>
          <span class="ar">{{ a.roomNo || '未排房' }}</span>
          <span class="ah">已 {{ a.hoursSince }} 小时无照护记录</span>
          <span class="at">最近记录 {{ fmtTime(a.lastRecordAt) }}</span>
        </div>
      </div>
      <el-empty v-else description="暂无漏记 ✓" :image-size="50" />
    </el-card>

    <div class="panes">
      <el-card shadow="never" class="pane" v-loading="loadingT">
        <template #header><b>护理团队在岗</b><el-tag v-if="team && team.alerts && team.alerts.length" type="danger" size="small" class="ml">缺岗 {{ team.alerts.length }}</el-tag></template>
        <div v-if="team" class="posts">
          <el-popover v-for="p in team.posts" :key="p.post" trigger="click" placement="bottom-start" :width="248">
            <template #reference>
              <el-tag :type="p.alert ? 'danger' : 'success'" effect="dark" class="pt clk">{{ p.post }} · {{ p.onDuty }}</el-tag>
            </template>
            <div class="pop">
              <div class="pop-h">{{ p.post }} · 在岗 {{ p.onDuty }} 人</div>
              <div v-if="p.members && p.members.length" class="pop-list">
                <div v-for="m in p.members" :key="m.staffId" class="pop-row">
                  <span class="nm">{{ m.name }}</span>
                  <span v-if="m.store" class="st">{{ m.store }}</span>
                </div>
              </div>
              <div v-else class="pop-empty">该岗位暂无在岗（缺岗）</div>
            </div>
          </el-popover>
        </div>
        <el-alert v-if="team && team.alerts && team.alerts.length" :title="'缺岗岗位：' + team.alerts.join('、')" type="warning" :closable="false" show-icon class="mt" />
      </el-card>
      <el-card shadow="never" class="pane">
        <template #header><b>分娩方式分布</b></template>
        <div v-if="d && Object.keys(d.delivery || {}).length" class="dist">
          <div v-for="(c, k) in d.delivery" :key="k" class="dl"><span class="dn">{{ k }}</span><div class="dbar"><div class="dfill" :style="{ width: delPct(c) + '%' }" /></div><span class="dc">{{ c }}</span></div>
        </div>
        <el-empty v-else description="暂无分娩方式数据" :image-size="50" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const d = ref<any>(null); const team = ref<any>(null); const loading = ref(false); const loadingT = ref(false); const storeId = ref('')
const alertData = ref<any>(null); const loadingA = ref(false)
const alerts = computed(() => alertData.value?.alerts || [])
const redCount = computed(() => alerts.value.filter((a: any) => a.level === 'red').length)
const amberCount = computed(() => alerts.value.filter((a: any) => a.level === 'amber').length)
const fmtTime = (t: string) => (t || '').replace('T', ' ').slice(5, 16) // ISO → MM-DD HH:mm
const maxDel = computed(() => Math.max(1, ...Object.values(d.value?.delivery || {}).map((x: any) => Number(x) || 0)))
const delPct = (n: any) => Math.round((Number(n) / maxDel.value) * 100)

async function load() {
  loading.value = true; loadingT.value = true; loadingA.value = true
  const sid = storeId.value ? Number(storeId.value) : undefined
  try { d.value = await api().getNursingStats({ storeId: sid }) } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false }
  try { team.value = await api().nursingTeamBoard(sid) } catch { team.value = null } finally { loadingT.value = false }
  try { alertData.value = await api().nursingCareAlerts({ storeId: sid }) } catch { alertData.value = null } finally { loadingA.value = false }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; gap: 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; margin-bottom: 14px; }
.kpi { background: var(--el-bg-color-overlay); border: 1px solid var(--el-border-color-lighter); border-radius: 8px; padding: 12px 14px; text-align: center; }
.kpi.hero { background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%); color: #fff; border: none; }
.kpi .t { font-size: 13px; color: var(--el-text-color-secondary); }
.kpi.hero .t { color: rgba(255,255,255,.85); }
.kpi .v { font-size: 26px; font-weight: 700; margin-top: 4px; }
.kpi .v.warn { color: var(--el-color-warning); }
.kpi .v.bad { color: var(--el-color-danger); }
.kpi .v.ok { color: var(--el-color-success); }
.panes { display: grid; grid-template-columns: 1.3fr 1fr; gap: 12px; }
.pane { min-width: 0; }
.posts { display: flex; flex-wrap: wrap; gap: 8px; }
.pt { margin: 0; }
.pt.clk { cursor: pointer; }
.pop-h { font-weight: 600; font-size: 13px; padding-bottom: 6px; margin-bottom: 6px; border-bottom: 1px solid var(--el-border-color-lighter); }
.pop-list { display: flex; flex-direction: column; gap: 4px; max-height: 260px; overflow-y: auto; }
.pop-row { display: flex; align-items: center; justify-content: space-between; font-size: 13px; }
.pop-row .st { color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px; white-space: nowrap; }
.pop-empty { font-size: 13px; color: var(--el-text-color-secondary); padding: 4px 0; }
.mt { margin-top: 12px; } .ml { margin-left: 8px; }
.alert-pane { margin-bottom: 12px; }
.alert-pane .thres { margin-left: 10px; font-size: 12px; font-weight: 400; color: var(--el-text-color-secondary); }
.alert-list { display: flex; flex-direction: column; gap: 8px; }
.alert-row { display: flex; align-items: center; gap: 14px; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.alert-row.red { background: var(--el-color-danger); color: #fff; }   /* 红灯：红底白字（7-09 实底规范） */
.alert-row.amber { background: #c8930a; color: #fff; }                /* 临近：金色实底 */
.alert-row .an { font-weight: 700; min-width: 64px; }
.alert-row .ar { min-width: 56px; }
.alert-row .ah { flex: 1; font-weight: 600; }
.alert-row .at { font-size: 12px; opacity: .85; }
.dist { display: flex; flex-direction: column; gap: 8px; }
.dl { display: flex; align-items: center; gap: 10px; }
.dl .dn { width: 72px; font-size: 13px; }
.dl .dbar { flex: 1; height: 12px; background: var(--el-fill-color-light); border-radius: 6px; overflow: hidden; }
.dl .dfill { height: 100%; background: var(--el-color-primary); border-radius: 6px; }
.dl .dc { width: 40px; text-align: right; font-size: 13px; font-weight: 600; }
@media (max-width: 900px) { .panes { grid-template-columns: 1fr; } }
</style>
