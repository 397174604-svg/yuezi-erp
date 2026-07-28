<template>
  <div>
    <div class="bar">
      <h2 class="ph">审批中台 · 收件箱</h2>
      <div class="filters">
        <el-select v-model="bizType" placeholder="业务类型" clearable style="width:150px" @change="load">
          <el-option v-for="t in bizTypes" :key="t" :label="t" :value="t" />
        </el-select>
        <el-radio-group v-model="scope" size="small" @change="load">
          <el-radio-button value="pending">待我审</el-radio-button>
          <el-radio-button value="all">全部</el-radio-button>
        </el-radio-group>
        <el-button @click="load">刷新</el-button>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无待审批单据">
      <el-table-column prop="instance_id" label="#" width="56" />
      <el-table-column prop="biz_type" label="业务" width="100" />
      <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
      <el-table-column label="金额" width="120" align="right"><template #default="{ row }">{{ row.amount != null ? '¥' + Number(row.amount).toLocaleString() : '—' }}</template></el-table-column>
      <el-table-column label="进度" width="100" align="center"><template #default="{ row }">{{ row.current_step }}/{{ row.total_steps }}</template></el-table-column>
      <el-table-column label="状态" width="90"><template #default="{ row }"><span class="stag" :style="stStyle(row.status)">{{ row.status }}</span></template></el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === '待审核' || row.status === '审核中'">
            <el-button link type="success" size="small" @click="act(row, true)">通过</el-button>
            <el-button link type="danger" size="small" @click="act(row, false)">驳回</el-button>
          </template>
          <el-button link type="primary" size="small" @click="openHistory(row)">轨迹</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="hisVisible" :title="'审批轨迹 #' + (curId || '')" size="400px">
      <el-timeline>
        <el-timeline-item v-for="r in history" :key="r.record_id" :timestamp="r.created_at" :type="r.action === '驳回' ? 'danger' : r.action === '通过' ? 'success' : 'primary'">
          第{{ r.step }}步 · {{ r.action }} <span v-if="r.opinion">— {{ r.opinion }}</span>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!history.length" description="暂无记录" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

// 状态色：高奢金白主题下 el-tag 的 primary/warning 都渲染成相近金色，待审核↔审核中难分辨。
// 改用 5 个显式区分的语义色（琥珀/蓝/绿/红/灰）+ 实底胶囊，彼此对比强、不依赖主题、且与其它页 el-tag effect=dark 观感一致。
const ST_COLOR: Record<string, string> = { 待审核: '#D48806', 审核中: '#2563EB', 通过: '#389E0D', 驳回: '#CF1322', 撤回: '#8C8C8C' }
function stStyle(status: string) {
  const c = ST_COLOR[status] || '#8C8C8C'
  return { color: '#fff', background: c, border: `1px solid ${c}` } // 实底白字，观感对齐 effect=dark
}
const bizTypes = ['退款', '费用', '预算', '换货', '收款', '合同', '月嫂派工', '收支']
const bizType = ref('')
const scope = ref<'pending' | 'all'>('pending')
const rows = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = (scope.value === 'pending'
      ? await api().listApprovalPending(bizType.value || undefined)
      : await api().listApprovals({ bizType: bizType.value || undefined })) as any[] || []
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}

async function act(row: any, pass: boolean) {
  try {
    let opinion = ''
    if (!pass) { opinion = (await ElMessageBox.prompt('驳回原因', '驳回审批', { inputPlaceholder: '请填写驳回意见' })).value }
    await api().approveApproval(row.instance_id, { pass, opinion })
    ElMessage.success(pass ? '已通过' : '已驳回'); load()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('操作失败：' + (e?.message || '')) }
}

const hisVisible = ref(false)
const history = ref<any[]>([])
const curId = ref<number | null>(null)
async function openHistory(row: any) {
  curId.value = row.instance_id; history.value = []; hisVisible.value = true
  try { history.value = (await api().approvalRecords(row.instance_id)) as any[] || [] } catch { history.value = [] }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.filters { display: flex; gap: 10px; align-items: center; }
.stag { display: inline-block; padding: 1px 9px; border-radius: 10px; font-size: 12px; line-height: 18px; font-weight: 600; white-space: nowrap; }
</style>
