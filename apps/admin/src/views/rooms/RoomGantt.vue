<template>
  <div>
    <div class="bar">
      <h2 class="ph">房态时间轴</h2>
      <div class="ctrl">
        <el-select v-model="storeId" placeholder="全部门店" clearable style="width: 150px" @change="load">
          <el-option v-for="s in stores" :key="s.store_id" :label="s.name" :value="s.store_id" />
        </el-select>
        <el-date-picker v-model="from" type="date" value-format="YYYY-MM-DD" placeholder="起始日" style="width: 140px" @change="clampAndLoad" />
        <span class="tilde">~</span>
        <el-date-picker v-model="to" type="date" value-format="YYYY-MM-DD" placeholder="结束日" style="width: 140px" @change="clampAndLoad" />
        <el-button type="primary" @click="load">查询</el-button>
      </div>
    </div>

    <div class="legend">
      <span class="lg"><i class="seg-dot st-预订" />预订 {{ countStatus('预订') }}</span>
      <span class="lg"><i class="seg-dot st-入住" />在住 {{ countStatus('入住') }}</span>
      <span class="lg"><i class="today-dot" />今日</span>
      <span class="muted">占用 = 预订 + 在住的档期区块（check_in ≤ 当日 &lt; check_out）</span>
    </div>

    <el-card shadow="never" v-loading="loading">
      <!-- 日期刻度头（与轨道等宽对齐） -->
      <div class="row head">
        <div class="lane-h">房间（{{ rooms.length }}）</div>
        <div class="track head-track">
          <div v-for="d in days" :key="d.key" class="day-cell" :class="{ wk: d.weekend }">{{ d.label }}</div>
        </div>
      </div>

      <div v-if="rooms.length" class="body">
        <div v-for="r in rooms" :key="r.room_id" class="row">
          <div class="lane-h">
            <b class="rno">{{ r.room_no }}</b>
            <span class="rt">{{ r.room_type || '—' }}<template v-if="r.floor != null"> · {{ r.floor }}F</template></span>
          </div>
          <div class="track" :style="{ background: gridBg }">
            <div v-if="todayLeft != null" class="today-line" :style="{ left: todayLeft + '%' }" />
            <div
              v-for="(b, i) in bookingsByRoom[r.room_id] || []" :key="i"
              class="seg" :class="'st-' + b.status" :style="barStyle(b)"
              :title="segTitle(b)"
            >{{ custName(b.customer_id) }}</div>
          </div>
        </div>
      </div>
      <el-empty v-else :description="loadedOnce ? '该门店暂无客房（仅月子门店有客房）' : '选择门店与档期后查询'" />
    </el-card>
    <p class="note">房间来自 /api/v1/rooms，档期区块来自 /api/v1/room-bookings（活跃状态 预订/入住），住客姓名取自客户中台。区块按 check_in~check_out 在窗口内定位；总部只读。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const DAY = 86400000
const MAX_DAYS = 60 // 窗口上限：防超长区间渲染过密
const ACTIVE = ['预订', '入住']

const stores = ref<any[]>([])
const rooms = ref<any[]>([])
const bookings = ref<any[]>([])
const custMap = ref<Record<number, string>>({})
const storeId = ref<number | null>(null)
const loading = ref(false)
const loadedOnce = ref(false)

const today = new Date().toISOString().slice(0, 10)
const from = ref(today)
const to = ref(new Date(Date.now() + 13 * DAY).toISOString().slice(0, 10)) // 默认 14 天窗口

const normDate = (d: any): string => {
  if (!d) return ''
  const s = String(d).replace(/\//g, '-').slice(0, 10)
  const m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  return m ? `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}` : s
}
const ms = (d: string): number => new Date(d + 'T00:00:00').getTime()

// 窗口起止（毫秒）与天数；to<from 时自动兜正为 14 天。
const win = computed(() => {
  const f = ms(normDate(from.value) || today)
  let t = ms(normDate(to.value) || today)
  if (!(t > f)) t = f + 13 * DAY
  let n = Math.round((t - f) / DAY) + 1
  n = Math.max(1, Math.min(MAX_DAYS, n))
  return { f, span: n * DAY, n }
})

const days = computed(() => {
  const { f, n } = win.value
  const arr: Array<{ key: string; label: string; weekend: boolean }> = []
  for (let i = 0; i < n; i++) {
    const d = new Date(f + i * DAY)
    const wd = d.getDay()
    arr.push({ key: d.toISOString().slice(0, 10), label: (d.getMonth() + 1) + '/' + d.getDate(), weekend: wd === 0 || wd === 6 })
  }
  return arr
})

// 每日一条竖向网格线（单一背景，全轨道复用）。
const gridBg = computed(() => {
  const w = 100 / win.value.n
  return `repeating-linear-gradient(90deg, transparent 0, transparent calc(${w}% - 1px), var(--el-border-color-lighter) calc(${w}% - 1px), var(--el-border-color-lighter) ${w}%)`
})

// 今日在窗口内的位置（%），不在窗口则不画。
const todayLeft = computed<number | null>(() => {
  const { f, span } = win.value
  const t = ms(today)
  if (t < f || t >= f + span) return null
  return ((t - f) / span) * 100
})

const bookingsByRoom = computed<Record<number, any[]>>(() => {
  const { f, span } = win.value
  const g: Record<number, any[]> = {}
  for (const b of bookings.value) {
    if (!ACTIVE.includes(b.status)) continue
    const ci = ms(normDate(b.check_in)); const co = Math.max(ms(normDate(b.check_out)), ci + DAY)
    if (co <= f || ci >= f + span) continue // 与窗口无交集
    ;(g[b.room_id] = g[b.room_id] || []).push(b)
  }
  return g
})

function barStyle(b: any) {
  const { f, span } = win.value
  const ci = ms(normDate(b.check_in)); const co = Math.max(ms(normDate(b.check_out)), ci + DAY)
  const left = Math.max(0, ((ci - f) / span) * 100)
  const right = Math.min(100, ((co - f) / span) * 100)
  return { left: left + '%', width: Math.max(2, right - left) + '%' }
}
function custName(id: number): string { return custMap.value[id] || ('客#' + id) }
function segTitle(b: any): string { return `${custName(b.customer_id)} · ${normDate(b.check_in)}~${normDate(b.check_out)} [${b.status}]` }
function countStatus(st: string): number { return bookings.value.filter((b: any) => b.status === st).length }

function clampAndLoad() { load() }

async function load() {
  loading.value = true
  try {
    const [rs, bk] = await Promise.all([
      api().listRooms({ storeId: storeId.value || undefined }),
      api().listRoomBookings({}),
    ])
    rooms.value = ((rs as any[]) || []).slice().sort((a: any, z: any) => (a.floor ?? 0) - (z.floor ?? 0) || String(a.room_no).localeCompare(String(z.room_no)))
    bookings.value = (bk as any[]) || []
    loadedOnce.value = true
  } catch (e: any) {
    ElMessage.error('房态时间轴加载失败：' + (e?.message || ''))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try { stores.value = (await api().listStores()) || [] } catch { /* ignore */ }
  try {
    const d: any = await api().listCustomers({ limit: 500 })
    const list = Array.isArray(d) ? d : (d?.rows || [])
    const m: Record<number, string> = {}
    for (const c of list) m[c.customer_id] = c.name
    custMap.value = m
  } catch { /* 无名单则回退 客#id */ }
  await load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.ctrl { display: flex; align-items: center; gap: 8px; }
.tilde { color: var(--ink-3); }
.legend { display: flex; align-items: center; gap: 18px; margin-bottom: 12px; font-size: 13px; color: var(--el-text-color-secondary); flex-wrap: wrap; }
.seg-dot { display: inline-block; width: 12px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
.today-dot { display: inline-block; width: 2px; height: 12px; background: var(--el-color-danger); margin-right: 6px; vertical-align: middle; }
.muted { color: var(--el-text-color-secondary); }
.row { display: flex; align-items: stretch; border-bottom: 1px solid var(--el-border-color-lighter); }
.row:last-child { border-bottom: none; }
.head { border-bottom: 2px solid var(--el-border-color); position: sticky; top: 0; background: var(--el-bg-color); z-index: 2; }
.lane-h { width: 150px; flex: 0 0 150px; padding: 6px 10px; display: flex; flex-direction: column; justify-content: center; gap: 2px; border-right: 1px solid var(--el-border-color-lighter); }
.head .lane-h { font-weight: 600; }
.rno { font-family: var(--font-display, inherit); font-size: 16px; }
.rt { font-size: 12px; color: var(--el-text-color-secondary); }
.track { position: relative; flex: 1; min-height: 34px; }
.head-track { display: flex; }
.day-cell { flex: 1; text-align: center; font-size: 11px; color: var(--el-text-color-secondary); padding: 6px 0; border-right: 1px solid var(--el-border-color-lighter); overflow: hidden; }
.day-cell.wk { background: var(--el-fill-color-lighter); color: var(--el-color-warning); }
.today-line { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--el-color-danger); opacity: .7; z-index: 1; }
.seg { position: absolute; top: 6px; height: 22px; line-height: 22px; font-size: 11px; color: #fff; border-radius: 4px; padding: 0 6px; overflow: hidden; white-space: nowrap; box-sizing: border-box; z-index: 1; }
.st-预订 { background: var(--el-color-warning); }
.st-入住 { background: var(--el-color-success); }
</style>
