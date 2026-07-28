<template>
  <div>
    <div class="bar">
      <h2 class="ph">客房房态</h2>
      <div class="ctrl">
        <el-select v-model="storeId" placeholder="全部门店" clearable style="width: 160px" @change="load">
          <el-option v-for="s in stores" :key="s.store_id" :label="s.name" :value="s.store_id" />
        </el-select>
        <el-button v-if="isMgr" type="primary" @click="openCreate">新建房间</el-button>
      </div>
    </div>

    <div class="legend">
      <span v-for="st in ROOM_STATUS" :key="st" class="lg"><i :class="['dot', cls(st)]" />{{ st }} {{ countOf(st) }}</span>
    </div>

    <div v-loading="loading">
      <div v-for="fl in floors" :key="fl" class="floor">
        <div class="fl-h">{{ fl }} 楼</div>
        <div class="fl-b">
          <el-dropdown v-for="r in byFloor[fl]" :key="r.room_id" trigger="click" @command="(c:string) => onCmd(c, r)">
            <div :class="['room', cls(r.status)]">
              <img v-if="imgByType[r.room_type]" :src="imgByType[r.room_type]" class="rimg" loading="lazy" :alt="r.room_type" />
              <div class="rn">{{ r.room_no }}</div>
              <div class="rt">{{ r.room_type || '—' }}</div>
              <div class="rs">{{ r.status }}</div>
              <div v-if="r.status === '在住' && r.customer_id" class="rcust">住 · {{ custName(r.customer_id) }}</div>
              <div class="rc">{{ money(r.price) }}<span class="unit">/日</span></div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="canFrontDesk && ['空闲','已订'].includes(r.status)" command="checkin">办理入住</el-dropdown-item>
                <el-dropdown-item v-if="canFrontDesk && r.status === '在住'" command="checkout">办理退房</el-dropdown-item>
                <el-dropdown-item v-if="isMgr" command="edit" divided>编辑房间</el-dropdown-item>
                <el-dropdown-item v-if="!isHQ" command="st-空闲" :divided="!isMgr">置为空闲</el-dropdown-item>
                <el-dropdown-item v-if="!isHQ" command="st-清洁">置为清洁</el-dropdown-item>
                <el-dropdown-item v-if="!isHQ" command="st-停用">置为停用</el-dropdown-item>
                <el-dropdown-item v-if="isMgr" command="remove" divided>删除房间</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <el-empty v-if="!rooms.length && !loading" description="暂无客房（仅月子门店有客房）" />
    </div>

    <!-- 新建/编辑房间 -->
    <el-dialog v-model="formVisible" :title="form.room_id ? '编辑房间' : '新建房间'" width="460px">
      <el-form label-width="76px">
        <el-form-item label="房间号"><el-input v-model="form.roomNo" placeholder="如 301" /></el-form-item>
        <el-form-item label="楼层"><el-input-number v-model="form.floor" :min="1" :max="99" /></el-form-item>
        <el-form-item label="房型"><el-input v-model="form.roomType" placeholder="如 尊享套房" /></el-form-item>
        <el-form-item label="日房价"><el-input-number v-model="form.price" :min="0" :step="100" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="st in ROOM_STATUS" :key="st" :label="st" :value="st" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible = false">取消</el-button><el-button type="primary" @click="saveForm">保存</el-button></template>
    </el-dialog>

    <!-- 办理入住 -->
    <el-dialog v-model="ciVisible" :title="'办理入住 · ' + (ciRoom?.room_no || '')" width="420px">
      <el-select v-model="ciCustomer" filterable placeholder="选择入住客户" style="width: 100%">
        <el-option v-for="c in customers" :key="c.customer_id" :label="c.name + ' · ' + (c.phone || '')" :value="c.customer_id" />
      </el-select>
      <template #footer><el-button @click="ciVisible = false">取消</el-button><el-button type="primary" @click="doCheckIn">确认入住</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
// 建/删/编辑房间(含房价)=资产配置,店长/管理层;设房态(空闲/清洁/停用)=门店日常(护士/技师/店长);
// 办理入住/退房=前台接待事务(前台/收银+店长,护理岗不办),总部(老板/运营)只监督不办理
const isMgr = computed(() => auth.isManager)
const isHQ = computed(() => ['老板', '运营'].some((r) => auth.roles.includes(r)))
// 入住/退房=接待事务：前台/收银 + 店级管理层(店长/助理，非总部)；护士/技师不办(仅管房态)
const canFrontDesk = computed(() => !isHQ.value && (auth.isManager || ['前台', '收银'].some((r) => auth.roles.includes(r))))

const ROOM_STATUS = ['空闲', '已订', '在住', '清洁', '停用']
const rooms = ref<any[]>([])
const stores = ref<any[]>([])
const customers = ref<any[]>([])
const imgByType = ref<Record<string, string>>({}) // 房型 → 首张真实实拍图 url（media.db）
const loading = ref(false)
const storeId = ref<number | null>(null)

const byFloor = computed<Record<number, any[]>>(() => {
  const g: Record<number, any[]> = {}
  for (const r of rooms.value) (g[r.floor ?? 0] = g[r.floor ?? 0] || []).push(r)
  return g
})
const floors = computed(() => Object.keys(byFloor.value).map(Number).sort((a, b) => a - b))

function cls(st: string): string {
  return ({ 空闲: 'free', 已订: 'booked', 在住: 'live', 清洁: 'clean', 停用: 'off' } as Record<string, string>)[st] || 'free'
}
function countOf(st: string): number {
  return rooms.value.filter((r) => r.status === st).length
}
function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString()
}
// 在住房显示住客姓名（客户列表已在 onMounted 加载）；查不到才回退 客#id
function custName(id: number): string {
  return customers.value.find((c) => c.customer_id === id)?.name || ('客#' + id)
}

async function load() {
  loading.value = true
  try {
    rooms.value = await api().listRooms({ storeId: storeId.value || undefined }) || []
  } catch (e: any) {
    ElMessage.error('房态加载失败：' + (e?.message || ''))
  } finally {
    loading.value = false
  }
}

// —— 新建/编辑 ——
const formVisible = ref(false)
const form = reactive<any>({ room_id: 0, roomNo: '', floor: 3, roomType: '', price: 1680, status: '空闲' })
function openCreate() {
  Object.assign(form, { room_id: 0, roomNo: '', floor: 3, roomType: '', price: 1680, status: '空闲' })
  formVisible.value = true
}
function openEdit(r: any) {
  Object.assign(form, { room_id: r.room_id, roomNo: r.room_no, floor: r.floor, roomType: r.room_type, price: r.price, status: r.status })
  formVisible.value = true
}
async function saveForm() {
  if (!form.roomNo) { ElMessage.warning('房间号必填'); return }
  try {
    if (form.room_id) {
      await api().updateRoom(form.room_id, { roomNo: form.roomNo, floor: form.floor, roomType: form.roomType, price: form.price, status: form.status })
    } else {
      await api().createRoom({ roomNo: form.roomNo, floor: form.floor, roomType: form.roomType, price: form.price, status: form.status, storeId: storeId.value || undefined })
    }
    ElMessage.success('已保存')
    formVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.message || ''))
  }
}

// —— 入住 / 退房 / 状态 / 删除 ——
const ciVisible = ref(false)
const ciRoom = ref<any>(null)
const ciCustomer = ref<number | null>(null)
function openCheckIn(r: any) {
  ciRoom.value = r
  ciCustomer.value = null
  ciVisible.value = true
}
async function doCheckIn() {
  if (!ciCustomer.value) { ElMessage.warning('请选择客户'); return }
  try {
    await api().checkInRoom(ciRoom.value.room_id, ciCustomer.value)
    ElMessage.success('入住成功')
    ciVisible.value = false
    load()
  } catch (e: any) {
    ElMessage.error('入住失败：' + (e?.message || ''))
  }
}
async function onCmd(cmd: string, r: any) {
  if (cmd === 'checkin') return openCheckIn(r)
  if (cmd === 'edit') return openEdit(r)
  if (cmd === 'checkout') {
    try { await api().checkOutRoom(r.room_id); ElMessage.success('已退房'); load() } catch (e: any) { ElMessage.error('退房失败：' + (e?.message || '')) }
    return
  }
  if (cmd === 'remove') {
    try {
      await ElMessageBox.confirm(`确认删除房间 ${r.room_no}？`, '确认', { type: 'warning' })
      await api().removeRoom(r.room_id); ElMessage.success('已删除'); load()
    } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error('删除失败：' + e.message) }
    return
  }
  if (cmd.startsWith('st-')) {
    try { await api().setRoomStatus(r.room_id, cmd.slice(3)); ElMessage.success('房态已更新'); load() } catch (e: any) { ElMessage.error('更新失败：' + (e?.message || '')) }
  }
}

onMounted(async () => {
  try { stores.value = (await api().listStores()) || [] } catch { /* ignore */ }
  try { customers.value = (await api().listCustomers({ limit: 200 })) || [] } catch { /* ignore */ }
  try { // 房型实拍图（media.db）：每个房型取首张
    const media = await api().mediaList({ refType: 'roomtype' }) || []
    const map: Record<string, string> = {}
    for (const m of media) if (m.tag && !map[m.tag]) map[m.tag] = m.url
    imgByType.value = map
  } catch { /* 无图不影响房态 */ }
  await load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.ctrl { display: flex; gap: 10px; }
.legend { display: flex; gap: 18px; margin-bottom: 14px; font-size: 13px; color: var(--ink-2); }
.legend .dot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }
.floor { margin-bottom: 16px; }
.fl-h { font-family: var(--font-cn-serif); font-weight: 600; color: var(--gold-deep); margin-bottom: 10px; padding-left: 10px; border-left: 3px solid var(--gold); }
.fl-b { display: flex; flex-wrap: wrap; gap: 12px; }
.room { width: 138px; border-radius: var(--r-sm); border: 1px solid var(--hair); padding: 10px; cursor: pointer; transition: transform .1s; background: var(--paper); overflow: hidden; }
.room:hover { transform: translateY(-2px); }
.room .rimg { width: 100%; height: 74px; object-fit: cover; border-radius: 8px; margin-bottom: 8px; display: block; background: var(--ivory-2); }
.room .rn { font-family: var(--font-display); font-size: 22px; font-weight: 600; }
.room .rt { font-size: 12px; color: var(--ink-3); margin-top: 2px; }
.room .rs { font-size: 12px; margin-top: 8px; font-weight: 500; }
.room .rcust { font-size: 12px; color: var(--gold-deep); margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.room .rc { font-size: 13px; color: var(--ink-2); margin-top: 3px; font-weight: 600; }
.room .rc .unit { font-size: 11px; color: var(--ink-3); font-weight: 400; margin-left: 1px; }

/* 房态色块（金白低饱和） */
.dot.free, .room.free { background: rgba(110,139,106,.14); }
.room.free { border-color: rgba(110,139,106,.4); } .room.free .rs { color: var(--ok); } .dot.free { background: var(--ok); }
.dot.live, .room.live { background: rgba(184,148,90,.16); }
.room.live { border-color: var(--gold); } .room.live .rs { color: var(--gold-deep); } .dot.live { background: var(--gold); }
.dot.booked, .room.booked { background: rgba(192,145,63,.14); }
.room.booked { border-color: rgba(192,145,63,.5); } .room.booked .rs { color: var(--warn); } .dot.booked { background: var(--warn); }
.dot.clean, .room.clean { background: var(--ivory-2); }
.room.clean .rs { color: var(--ink-2); } .dot.clean { background: #c9bfa9; }
.dot.off, .room.off { background: var(--ivory); }
.room.off { opacity: .65; } .room.off .rs { color: var(--ink-3); } .dot.off { background: var(--ink-3); }
</style>
