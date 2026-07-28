<template>
  <div>
    <div class="bar">
      <h2 class="ph">护理中心</h2>
      <el-select v-model="storeId" placeholder="全部门店" clearable style="width: 160px" @change="loadAll">
        <el-option v-for="s in stores" :key="s.store_id" :label="s.name" :value="s.store_id" />
      </el-select>
    </div>

    <!-- 仪表盘指标 -->
    <el-row :gutter="14" v-loading="loadingStats" class="kpis">
      <el-col :span="4" v-for="k in kpis" :key="k.label">
        <div :class="['kpi', k.warn && k.value ? 'warn' : '']">
          <div class="kv serif">{{ k.value }}</div>
          <div class="kl">{{ k.label }}</div>
        </div>
      </el-col>
    </el-row>
    <div class="delivery" v-if="deliveryList.length">
      分娩方式：<el-tag v-for="d in deliveryList" :key="d.k" effect="plain" class="dt">{{ d.k }} {{ d.c }}</el-tag>
    </div>

    <!-- 护理记录 -->
    <div class="rec-head">
      <span class="t">护理 / 巡房记录</span>
      <el-select v-model="recStatus" placeholder="状态" clearable size="small" style="width: 120px" @change="loadRecords">
        <el-option v-for="s in NURSE_STATUS" :key="s" :label="s" :value="s" />
      </el-select>
    </div>
    <el-table :data="records" v-loading="loadingRec" border stripe empty-text="暂无护理记录">
      <el-table-column label="客户" width="80"><template #default="{ row }">客#{{ row.customer_id }}</template></el-table-column>
      <el-table-column prop="type" label="类型" width="110" />
      <el-table-column prop="room_no" label="房间" width="90" />
      <el-table-column prop="baby_name" label="宝宝" width="100" />
      <el-table-column prop="tech" label="护理员" width="100" />
      <el-table-column label="异常" min-width="120"><template #default="{ row }"><span v-if="row.abnormal" class="abn">{{ row.abnormal }}</span><span v-else class="ok">正常</span></template></el-table-column>
      <el-table-column label="母婴同室" width="90" align="center"><template #default="{ row }">{{ row.rooming_in ? '是' : '否' }}</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="stType(row.status)" effect="dark" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-dropdown v-if="!isHQ" trigger="click" @command="(s:string) => changeStatus(row, s)">
            <el-button link type="primary" size="small">改状态<el-icon><ArrowDown /></el-icon></el-button>
            <template #dropdown><el-dropdown-menu>
              <el-dropdown-item v-for="s in NURSE_STATUS" :key="s" :command="s" :disabled="s === row.status">{{ s }}</el-dropdown-item>
            </el-dropdown-menu></template>
          </el-dropdown>
          <span v-else class="muted" style="color:var(--el-text-color-secondary);font-size:12px">只读</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
// 巡房状态流转=护士/技师临床操作(店长可督办),总部(老板/运营)只监督不改
const isHQ = computed(() => ['老板', '运营'].some((r) => auth.roles.includes(r)))

const NURSE_STATUS = ['待巡房', '进行中', '已完成', '异常']
const stores = ref<any[]>([])
const storeId = ref<number | null>(null)
const stats = ref<any>({})
const records = ref<any[]>([])
const loadingStats = ref(false)
const loadingRec = ref(false)
const recStatus = ref('')

const kpis = computed(() => [
  { label: '在住客房', value: stats.value.liveRooms ?? 0 },
  { label: '护理记录', value: stats.value.nursingTotal ?? 0 },
  { label: '待巡房', value: stats.value.pendingRounds ?? 0 },
  { label: '进行中', value: stats.value.inProgress ?? 0 },
  { label: '母婴同室', value: stats.value.roomingIn ?? 0 },
  { label: '异常', value: stats.value.abnormal ?? 0, warn: true },
])
const deliveryList = computed(() => Object.entries(stats.value.delivery || {}).map(([k, c]) => ({ k, c })))

function stType(s: string): string {
  if (s === '已完成') return 'success'
  if (s === '进行中') return 'warning'
  if (s === '异常') return 'danger'
  return 'info'
}

async function loadStats() {
  loadingStats.value = true
  try { stats.value = await api().getNursingStats({ storeId: storeId.value || undefined }) || {} }
  catch (e: any) { ElMessage.error('护理仪表盘加载失败：' + (e?.message || '')) }
  finally { loadingStats.value = false }
}
async function loadRecords() {
  loadingRec.value = true
  try { records.value = await api().listNursing({ storeId: storeId.value || undefined, status: recStatus.value || undefined }) || [] }
  catch (e: any) { ElMessage.error('护理记录加载失败：' + (e?.message || '')) }
  finally { loadingRec.value = false }
}
function loadAll() { loadStats(); loadRecords() }

async function changeStatus(row: any, status: string) {
  try {
    await api().setNursingStatus(row.service_id, status)
    row.status = status
    ElMessage.success('已更新为「' + status + '」')
    loadStats()
  } catch (e: any) { ElMessage.error('更新失败：' + (e?.message || '')) }
}

onMounted(async () => {
  try { stores.value = (await api().listStores()) || [] } catch { /* ignore */ }
  loadAll()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.kpis { margin-bottom: 10px; }
.kpi { background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-md); padding: 18px; text-align: center; }
.kpi.warn { border-color: var(--danger); background: rgba(176,106,87,.06); }
.kpi .kv { font-size: 30px; color: var(--gold-deep); font-weight: 600; }
.kpi.warn .kv { color: var(--danger); }
.kpi .kl { font-size: 13px; color: var(--ink-3); margin-top: 4px; }
.delivery { font-size: 13px; color: var(--ink-2); margin: 6px 0 18px; }
.delivery .dt { margin-left: 8px; }
.rec-head { display: flex; align-items: center; justify-content: space-between; margin: 8px 0 12px; }
.rec-head .t { font-family: var(--font-cn-serif); font-weight: 600; padding-left: 10px; border-left: 3px solid var(--gold); }
.abn { color: var(--danger); font-weight: 500; }
.ok { color: var(--ink-3); }
</style>
