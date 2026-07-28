<template>
  <div>
    <div class="bar">
      <h2 class="ph">健康建档</h2>
      <div>
        <el-select v-model="domain" size="small" style="width:110px;margin-right:8px" @change="load">
          <el-option label="全部域" value="" /><el-option label="月子" value="月子" /><el-option label="产康" value="产康" />
        </el-select>
        <el-button @click="load">刷新</el-button>
        <el-button v-if="!isHQ" type="primary" @click="openNew">新建档案</el-button>
        <el-tag v-else type="info" effect="plain" size="small">总部只读 · 建档由护理岗/店长</el-tag>
      </div>
    </div>
    <el-alert title="孕产健康档案（含医疗敏感信息 · 按门店隔离，本店员工可见）。同一客户 × 域 × 评估阶段唯一，重复保存视为更新。" type="info" :closable="false" show-icon class="mb" />
    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无档案">
      <el-table-column label="客户" min-width="96"><template #default="{ row }">{{ nameOf(row.customer_id) }}</template></el-table-column>
      <el-table-column label="门店" width="150" show-overflow-tooltip><template #default="{ row }">{{ storeName(row.store_id) }}</template></el-table-column>
      <el-table-column prop="domain" label="域" width="64" />
      <el-table-column prop="assess_stage" label="评估阶段" width="94" />
      <el-table-column prop="fetus_type" label="胎型" width="70" />
      <el-table-column prop="delivery_type" label="分娩方式" width="96" />
      <el-table-column prop="gestational_weeks" label="孕周" width="64" />
      <el-table-column prop="postpartum_day" label="产后天数" width="80" />
      <el-table-column prop="blood_type" label="血型" width="70" />
      <el-table-column prop="allergy" label="过敏史" min-width="96" show-overflow-tooltip />
      <el-table-column label="建档人" width="90" show-overflow-tooltip><template #default="{ row }">{{ row.created_by || '—' }}</template></el-table-column>
      <el-table-column v-if="!isHQ" label="操作" width="70" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openEdit(row)">编辑</el-button></template></el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="form.profile_id ? '编辑健康档案' : '新建健康档案'" width="640px">
      <el-form :model="form" label-width="92px" size="small">
        <el-form-item label="客户" required>
          <el-select v-model="form.customerId" filterable :disabled="!!form.profile_id" placeholder="选择客户" style="width:100%">
            <el-option v-for="c in customers" :key="c.customer_id" :label="c.name + (c.phone ? ' / ' + c.phone : '')" :value="c.customer_id" />
          </el-select>
        </el-form-item>
        <div class="grid2">
          <el-form-item label="域"><el-select v-model="form.domain" style="width:100%"><el-option v-for="d in DOMAIN" :key="d" :label="d" :value="d" /></el-select></el-form-item>
          <el-form-item label="评估阶段"><el-select v-model="form.assessStage" clearable style="width:100%"><el-option v-for="s in STAGE" :key="s" :label="s" :value="s" /></el-select></el-form-item>
          <el-form-item label="胎型"><el-select v-model="form.fetus_type" clearable style="width:100%"><el-option v-for="x in FETUS" :key="x" :label="x" :value="x" /></el-select></el-form-item>
          <el-form-item label="分娩方式"><el-select v-model="form.delivery_type" clearable style="width:100%"><el-option v-for="x in DELIVERY" :key="x" :label="x" :value="x" /></el-select></el-form-item>
          <el-form-item label="血型"><el-select v-model="form.blood_type" clearable style="width:100%"><el-option v-for="x in BLOOD" :key="x" :label="x" :value="x" /></el-select></el-form-item>
          <el-form-item label="孕周"><el-input v-model="form.gestational_weeks" placeholder="周" /></el-form-item>
          <el-form-item label="产后天数"><el-input v-model="form.postpartum_day" placeholder="天" /></el-form-item>
          <el-form-item label="身高 cm"><el-input v-model="form.height" /></el-form-item>
          <el-form-item label="体重 kg"><el-input v-model="form.weight" /></el-form-item>
          <el-form-item label="孕前体重 kg"><el-input v-model="form.pre_pregnancy_weight" /></el-form-item>
        </div>
        <el-form-item label="既往史"><el-input v-model="form.past_history" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="过敏史"><el-input v-model="form.allergy" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
// 健康建档=临床建档(建档人=护理员工),基层护理岗(护士/技师)或店长建;总部(老板/运营)只督导查看,不新建/编辑
const isHQ = computed(() => ['老板', '运营'].some((r) => auth.roles.includes(r)))

// 枚举与后端 healthService 导出保持一致（FETUS_TYPE/HEALTH_DELIVERY/BLOOD_TYPE/ASSESS_STAGE/HEALTH_DOMAIN）
const DOMAIN = ['月子', '产康']
const STAGE = ['入住评估', '在住评估', '离所评估']
const FETUS = ['单胎', '双胎', '多胎']
const DELIVERY = ['顺产', '剖宫产', '器械助产', '无痛分娩']
const BLOOD = ['A型', 'B型', 'O型', 'AB型', '未知']

const rows = ref<any[]>([]); const customers = ref<any[]>([]); const loading = ref(false); const saving = ref(false)
const domain = ref(''); const dlg = ref(false)
const custMap = ref<Record<number, string>>({})
const nameOf = (id: number) => custMap.value[id] || ('#' + id)
const storeMap = ref<Record<number, string>>({})
const storeName = (id: number) => (id == null ? '—' : (storeMap.value[id] || ('店#' + id)))
const blank = () => ({ profile_id: 0, customerId: undefined as number | undefined, domain: '月子', assessStage: '', fetus_type: '', delivery_type: '', blood_type: '', gestational_weeks: '', postpartum_day: '', height: '', weight: '', pre_pregnancy_weight: '', past_history: '', allergy: '', notes: '' })
const form = ref(blank())

async function loadCustomers() {
  try {
    const d = (await api().listCustomers({ limit: 500 })) as any
    const list: any[] = Array.isArray(d) ? d : (d?.rows || [])
    customers.value = list
    const m: Record<number, string> = {}
    for (const c of list) m[c.customer_id] = c.name
    custMap.value = m
  } catch { /* 名字映射失败不阻断档案表渲染 */ }
}
async function load() {
  loading.value = true
  try { rows.value = (await api().listHealthProfiles({ domain: domain.value || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}
function openNew() { form.value = blank(); dlg.value = true }
function openEdit(row: any) {
  form.value = { profile_id: row.profile_id, customerId: row.customer_id, domain: row.domain || '月子', assessStage: row.assess_stage || '', fetus_type: row.fetus_type || '', delivery_type: row.delivery_type || '', blood_type: row.blood_type || '', gestational_weeks: row.gestational_weeks ?? '', postpartum_day: row.postpartum_day ?? '', height: row.height ?? '', weight: row.weight ?? '', pre_pregnancy_weight: row.pre_pregnancy_weight ?? '', past_history: row.past_history || '', allergy: row.allergy || '', notes: row.notes || '' }
  dlg.value = true
}
const numOrU = (v: any) => (v === '' || v === null || v === undefined ? undefined : Number(v))
async function save() {
  if (!form.value.customerId) { ElMessage.warning('请选择客户'); return }
  saving.value = true
  try {
    const f = form.value
    await api().upsertHealthProfile({
      customerId: f.customerId, domain: f.domain, assessStage: f.assessStage || undefined,
      fetus_type: f.fetus_type || undefined, delivery_type: f.delivery_type || undefined, blood_type: f.blood_type || undefined,
      gestational_weeks: numOrU(f.gestational_weeks), postpartum_day: numOrU(f.postpartum_day),
      height: numOrU(f.height), weight: numOrU(f.weight), pre_pregnancy_weight: numOrU(f.pre_pregnancy_weight),
      past_history: f.past_history || undefined, allergy: f.allergy || undefined, notes: f.notes || undefined,
    })
    ElMessage.success('已保存'); dlg.value = false; load()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
  finally { saving.value = false }
}
async function loadStores() {
  try {
    const d = (await api().listStores()) as any[] || []
    const m: Record<number, string> = {}
    for (const st of d) m[st.store_id || st.id] = st.name
    storeMap.value = m
  } catch { /* 门店名映射失败不阻断 */ }
}
onMounted(() => { loadCustomers(); loadStores(); load() })
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.mb { margin-bottom: 12px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }
</style>
