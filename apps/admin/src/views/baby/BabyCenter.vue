<template>
  <div>
    <div class="bar">
      <h2 class="ph">宝宝日志</h2>
      <div>
        <el-input v-model="custFilter" placeholder="客户号" clearable size="small" style="width: 130px" @keyup.enter="load" />
        <el-button type="primary" size="small" @click="load">查询</el-button>
        <el-button v-if="!auth.isHQ" size="small" @click="openCreate">建档</el-button>
        <el-tag v-else type="info" effect="plain" size="small" style="margin-left:8px">总部只读 · 建档/录入由护士·育婴师</el-tag>
      </div>
    </div>
    <el-table :data="babies" v-loading="loading" border stripe empty-text="暂无宝宝档案">
      <el-table-column prop="name" label="宝宝" min-width="120" />
      <el-table-column prop="customer_id" label="客户" width="80" />
      <el-table-column prop="gender" label="性别" width="70" />
      <el-table-column prop="birth_date" label="出生日" width="120" />
      <el-table-column label="出生体重" width="100" align="right"><template #default="{ row }">{{ row.birth_weight ? row.birth_weight + 'kg' : '—' }}</template></el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openTimeline(row)">日志时间线</el-button>
          <el-button v-if="!auth.isHQ" link type="success" size="small" @click="openLog(row)">录入</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 时间线抽屉 -->
    <el-drawer v-model="tlVisible" :title="(cur.name || '宝宝') + ' · 日志时间线'" size="460px">
      <el-radio-group v-model="tlKind" size="small" @change="loadTimeline" style="margin-bottom: 12px">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button v-for="k in KINDS" :key="k" :value="k">{{ k }}</el-radio-button>
      </el-radio-group>
      <el-timeline v-loading="tlLoading">
        <el-timeline-item v-for="l in logs" :key="l.log_id" :timestamp="l.log_time" placement="top" :type="kindType(l.kind)">
          <b>{{ l.kind }}</b>
          <span class="d">{{ logDetail(l) }}</span>
        </el-timeline-item>
        <el-empty v-if="!logs.length && !tlLoading" description="暂无日志" :image-size="60" />
      </el-timeline>
    </el-drawer>

    <!-- 建档 -->
    <el-dialog v-model="createVisible" title="宝宝建档" width="440px">
      <el-form label-width="90px">
        <el-form-item label="客户号"><el-input-number v-model="cForm.customerId" :min="1" controls-position="right" style="width: 180px" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="cForm.name" placeholder="如 王宝宝" /></el-form-item>
        <el-form-item label="性别"><el-select v-model="cForm.gender" style="width: 120px"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select></el-form-item>
        <el-form-item label="出生日"><el-date-picker v-model="cForm.birthDate" type="date" value-format="YYYY-MM-DD" style="width: 180px" /></el-form-item>
        <el-form-item label="出生体重"><el-input-number v-model="cForm.birthWeight" :min="0" :step="0.1" :precision="2" controls-position="right" style="width: 160px" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="createVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitCreate">建档</el-button></template>
    </el-dialog>

    <!-- 录入日志 -->
    <el-dialog v-model="logVisible" :title="(cur.name || '宝宝') + ' · 录入日志'" width="440px">
      <el-form label-width="90px">
        <el-form-item label="类型"><el-radio-group v-model="lForm.kind"><el-radio-button v-for="k in KINDS" :key="k" :value="k">{{ k }}</el-radio-button></el-radio-group></el-form-item>
        <el-form-item v-if="lForm.kind === '喂养'" label="喂养方式"><el-select v-model="lForm.feedType" style="width: 140px"><el-option v-for="t in ['母乳', '配方奶', '混合']" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item v-if="lForm.kind === '喂养'" label="奶量(ml)"><el-input-number v-model="lForm.amount" :min="0" :step="10" controls-position="right" style="width: 140px" /></el-form-item>
        <el-form-item v-if="lForm.kind === '尿便'" label="类型"><el-select v-model="lForm.diaperType" style="width: 140px"><el-option v-for="t in ['小便', '大便', '混合']" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item v-if="lForm.kind === '健康'" label="指标"><el-select v-model="lForm.metric" style="width: 140px"><el-option v-for="t in ['体温', '体重', '黄疸', '身长', '头围']" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item v-if="lForm.kind === '健康'" label="数值"><el-input-number v-model="lForm.metricValue" :step="0.1" :precision="1" controls-position="right" style="width: 140px" /></el-form-item>
        <el-form-item v-if="lForm.kind === '护理'" label="护理项"><el-select v-model="lForm.careType" style="width: 140px"><el-option v-for="t in ['洗澡', '抚触', '游泳', '脐部', '疫苗']" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model="lForm.note" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="logVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitLog">提交</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore() // 宝宝建档/日志录入=护士·育婴师床边一线记录,总部(老板/运营)只监督时间线

const KINDS = ['喂养', '尿便', '健康', '护理']
const kindType = (k: string) => ({ 喂养: 'primary', 尿便: 'warning', 健康: 'success', 护理: 'info' } as any)[k] || 'primary'
const logDetail = (l: any) => l.kind === '喂养' ? `${l.feed_type || ''} ${l.amount ? l.amount + 'ml' : ''}` : l.kind === '尿便' ? (l.diaper_type || '') : l.kind === '健康' ? `${l.metric || ''} ${l.metric_value ?? ''}` : (l.care_type || '') + (l.note ? ' · ' + l.note : '')

const babies = ref<any[]>([]); const loading = ref(false); const custFilter = ref(''); const saving = ref(false); const cur = ref<any>({})
async function load() {
  loading.value = true
  try { babies.value = (await api().listBabies({ customerId: custFilter.value || undefined })) as any[] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); babies.value = [] } finally { loading.value = false }
}

// 时间线
const tlVisible = ref(false); const logs = ref<any[]>([]); const tlLoading = ref(false); const tlKind = ref('')
function openTimeline(row: any) { cur.value = row; tlKind.value = ''; tlVisible.value = true; loadTimeline() }
async function loadTimeline() {
  tlLoading.value = true
  try { logs.value = (await api().babyTimeline(cur.value.baby_id, { kind: tlKind.value || undefined })) as any[] }
  catch (e: any) { ElMessage.error('时间线加载失败：' + (e?.message || '')); logs.value = [] } finally { tlLoading.value = false }
}

// 建档
const createVisible = ref(false)
const cForm = reactive<any>({ customerId: 1, name: '', gender: '男', birthDate: '', birthWeight: 3.2 })
function openCreate() { createVisible.value = true }
async function submitCreate() {
  saving.value = true
  try { await api().createBaby({ ...cForm }); ElMessage.success('建档成功'); createVisible.value = false; await load() }
  catch (e: any) { ElMessage.error('建档失败：' + (e?.message || '')) } finally { saving.value = false }
}

// 录入日志
const logVisible = ref(false)
const lForm = reactive<any>({ kind: '喂养', feedType: '母乳', amount: 60, diaperType: '小便', metric: '体温', metricValue: 36.7, careType: '洗澡', note: '' })
function openLog(row: any) { cur.value = row; logVisible.value = true }
async function submitLog() {
  saving.value = true
  try { await api().addBabyLog(cur.value.baby_id, { ...lForm }); ElMessage.success('已录入'); logVisible.value = false }
  catch (e: any) { ElMessage.error('录入失败：' + (e?.message || '')) } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.d { color: var(--ink-2); margin-left: 8px; }
</style>
