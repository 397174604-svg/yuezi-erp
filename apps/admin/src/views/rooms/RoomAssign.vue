<template>
  <div>
    <div class="bar">
      <h2 class="ph">智能排房</h2>
      <span v-if="auth.isHQ" class="muted hqtip">总部只监督 · 排房/入住/退房由门店办理</span>
    </div>

    <!-- 档期查询 → 智能推荐可用房 -->
    <el-card shadow="never" class="card">
      <el-form :inline="true" :model="qf" size="small">
        <el-form-item label="入住日期"><el-input v-model="qf.checkIn" placeholder="YYYY-MM-DD" style="width:140px" /></el-form-item>
        <el-form-item label="退房日期"><el-input v-model="qf.checkOut" placeholder="YYYY-MM-DD" style="width:140px" /></el-form-item>
        <el-form-item label="房型"><el-input v-model="qf.roomType" placeholder="不限" clearable style="width:130px" /></el-form-item>
        <el-form-item label="客户ID"><el-input v-model="qf.customerId" placeholder="排房用" style="width:110px" /></el-form-item>
        <el-form-item><el-button type="primary" @click="doRecommend">查可用房</el-button></el-form-item>
      </el-form>
      <el-table :data="available" v-loading="recLoading" border stripe size="small" empty-text="先查档期可用房">
        <el-table-column prop="room_no" label="房号" width="100" />
        <el-table-column prop="room_type" label="房型" min-width="120" />
        <el-table-column prop="floor" label="楼层" width="80" align="center" />
        <el-table-column label="价格" width="110" align="right"><template #default="{ row }">{{ row.price != null ? '¥' + Number(row.price).toLocaleString() : '—' }}</template></el-table-column>
        <el-table-column label="操作" width="100" fixed="right"><template #default="{ row }"><el-button v-if="!auth.isHQ" link type="primary" size="small" @click="doAssign(row)">排房</el-button><span v-else class="muted">只读</span></template></el-table-column>
      </el-table>
    </el-card>

    <!-- 预订列表 + 生命周期动作 -->
    <el-card shadow="never" class="card">
      <div class="sub">预订单 <el-button link type="primary" size="small" @click="loadBookings">刷新</el-button></div>
      <el-table :data="bookings" v-loading="bkLoading" border stripe size="small" empty-text="暂无预订">
        <el-table-column prop="booking_id" label="#" width="60" />
        <el-table-column prop="room_id" label="房间" width="80" align="center" />
        <el-table-column prop="customer_id" label="客户" width="80" align="center" />
        <el-table-column label="档期" min-width="190"><template #default="{ row }">{{ row.check_in }} ~ {{ row.check_out }}</template></el-table-column>
        <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="TAG[row.status] || 'info'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <template v-if="!auth.isHQ">
              <el-button v-if="row.status === '预订'" link type="success" size="small" @click="act('checkInRoomBooking', row, '入住')">入住</el-button>
              <el-button v-if="row.status === '预订' || row.status === '入住'" link type="warning" size="small" @click="act('checkOutRoomBooking', row, '退房')">退房</el-button>
              <el-button v-if="row.status === '预订' || row.status === '入住'" link type="danger" size="small" @click="doCancel(row)">取消</el-button>
            </template>
            <span v-else class="muted">总部只读</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore() // 排房/入住/退房/取消=门店房务一线动作,总部(老板/运营)只监督查看(查可用房保留)

const TAG: Record<string, string> = { 预订: 'warning', 入住: 'success', 已退: 'info', 已取消: 'danger' }
const qf = ref({ checkIn: '', checkOut: '', roomType: '', customerId: '' })
const available = ref<any[]>([])
const recLoading = ref(false)
const bookings = ref<any[]>([])
const bkLoading = ref(false)

async function doRecommend() {
  if (!qf.value.checkIn || !qf.value.checkOut) { ElMessage.warning('请填入住/退房日期'); return }
  recLoading.value = true
  try {
    const r: any = await api().recommendRooms({ checkIn: qf.value.checkIn, checkOut: qf.value.checkOut, roomType: qf.value.roomType || undefined })
    available.value = r?.available || []
    if (!available.value.length) ElMessage.info('该档期无可用房')
  } catch (e: any) { ElMessage.error('查询失败：' + (e?.message || '')) }
  finally { recLoading.value = false }
}

async function doAssign(row: any) {
  if (!qf.value.customerId) { ElMessage.warning('请先填客户ID'); return }
  try {
    await api().assignRoom({ roomId: row.room_id, customerId: Number(qf.value.customerId), checkIn: qf.value.checkIn, checkOut: qf.value.checkOut })
    ElMessage.success('排房成功：' + row.room_no)
    doRecommend(); loadBookings()
  } catch (e: any) { ElMessage.error('排房失败：' + (e?.message || '')) }
}

async function act(fn: 'checkInRoomBooking' | 'checkOutRoomBooking', row: any, label: string) {
  try { await (api() as any)[fn](row.booking_id); ElMessage.success(label + '成功'); loadBookings() }
  catch (e: any) { ElMessage.error(label + '失败：' + (e?.message || '')) }
}

async function doCancel(row: any) {
  try {
    await ElMessageBox.confirm(`确认取消预订 #${row.booking_id}？`, '取消预订', { type: 'warning' })
    await api().cancelRoomBooking(row.booking_id, {})
    ElMessage.success('已取消'); loadBookings()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('取消失败：' + (e?.message || '')) }
}

async function loadBookings() {
  bkLoading.value = true
  try { bookings.value = (await api().listRoomBookings({})) as any[] || [] }
  catch (e: any) { ElMessage.error('预订列表加载失败：' + (e?.message || '')); bookings.value = [] }
  finally { bkLoading.value = false }
}

onMounted(loadBookings)
</script>

<style scoped>
.bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.card { margin-bottom: 14px; }
.sub { font-weight: 600; margin-bottom: 8px; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.hqtip { font-weight: 400; }
</style>
