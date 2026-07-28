<template>
  <div>
    <div class="bar">
      <h2 class="ph">护理评估</h2>
      <div>
        <el-input v-model="f.customerId" placeholder="客户ID筛选" size="small" style="width:130px" clearable @change="load" />
        <el-input v-model="f.date" placeholder="日期 YYYY-MM-DD" size="small" style="width:170px" clearable @change="load" />
        <el-button v-if="canRecord" type="primary" @click="openDlg">录入评估</el-button>
        <el-tag v-else type="info" effect="plain" size="small" style="margin-left:8px">只读 · 评估由护理岗录入</el-tag>
      </div>
    </div>

    <el-card v-if="board" shadow="never" class="card">
      <div class="board">
        <span class="bt">护理团队在岗：</span>
        <el-popover v-for="p in board.posts" :key="p.post" trigger="click" placement="bottom-start" :width="248">
          <template #reference>
            <el-tag :type="p.alert ? 'danger' : 'success'" size="small" effect="dark" class="pt clk">{{ p.post }} {{ p.onDuty }}</el-tag>
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
        <el-alert v-if="board.alerts && board.alerts.length" :title="'缺岗告警：' + board.alerts.join('、')" type="warning" :closable="false" show-icon class="al" />
      </div>
    </el-card>

    <el-table :data="rows" v-loading="loading" border stripe size="small" empty-text="暂无评估记录">
      <el-table-column prop="assess_date" label="评估日" width="110" />
      <el-table-column prop="customer_id" label="客户" width="70" />
      <el-table-column prop="postpartum_day" label="产后天数" width="80" align="center" />
      <el-table-column prop="lochia_color" label="恶露色" width="90" />
      <el-table-column prop="lochia_amount" label="恶露量" width="80" />
      <el-table-column prop="fundus" label="宫底" width="90" />
      <el-table-column prop="perineum_heal" label="会阴愈合" width="90" />
      <el-table-column prop="breast" label="乳房" width="90" />
      <el-table-column prop="mood" label="情绪" width="90" />
      <el-table-column label="体征" min-width="140"><template #default="{ row }">{{ vitals(row) }}</template></el-table-column>
      <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
    </el-table>

    <el-dialog v-model="dlg" title="录入产后护理评估" width="680px">
      <el-form :model="form" label-width="84px" size="small">
        <el-form-item label="客户ID"><el-input v-model="form.customerId" style="width:140px" /></el-form-item>
        <el-form-item label="产后天数"><el-input v-model="form.postpartumDay" style="width:120px" /></el-form-item>
        <el-form-item v-for="(opts, key) in tpl" :key="key" :label="LABELS[key] || key">
          <el-select v-model="form[key]" clearable style="width:200px" placeholder="—"><el-option v-for="o in opts" :key="o" :label="o" :value="o" /></el-select>
        </el-form-item>
        <el-form-item label="体温℃"><el-input v-model="form.temperature" style="width:120px" /></el-form-item>
        <el-form-item label="血压"><el-input v-model="form.bloodPressure" style="width:140px" placeholder="如 120/80" /></el-form-item>
        <el-form-item label="脉搏"><el-input v-model="form.pulse" style="width:120px" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" style="width:420px" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" @click="submit">保存评估</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
// 录入评估=临床护理岗(护士/技师)行为,须本人署名;总部(老板/运营)与店级管理(店长)只督导查看,不代录
const canRecord = computed(() => ['护士', '技师'].some((r) => auth.roles.includes(r)))

const LABELS: Record<string, string> = { lochia_color: '恶露颜色', lochia_amount: '恶露量', fundus: '宫底', perineum_heal: '会阴愈合', perineum_type: '会阴类型', breast: '乳房', mood: '情绪' }
const rows = ref<any[]>([]); const loading = ref(false)
const tpl = ref<Record<string, string[]>>({})
const board = ref<any>(null)
const f = ref({ customerId: '', date: '' })
const dlg = ref(false)
const blank = (): any => ({ customerId: '', postpartumDay: '', temperature: '', bloodPressure: '', pulse: '', notes: '', lochia_color: '', lochia_amount: '', fundus: '', perineum_heal: '', perineum_type: '', breast: '', mood: '' })
const form = ref<any>(blank())
const vitals = (r: any) => [r.temperature != null ? r.temperature + '℃' : '', r.blood_pressure || '', r.pulse != null ? r.pulse + '次' : ''].filter(Boolean).join(' / ') || '—'

async function load() {
  loading.value = true
  try { rows.value = (await api().listNursingAssessments({ customerId: f.value.customerId ? Number(f.value.customerId) : undefined, date: f.value.date || undefined })) as any[] || [] }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); rows.value = [] }
  finally { loading.value = false }
}
function openDlg() { form.value = blank(); dlg.value = true }
async function submit() {
  const v = form.value
  if (!Number(v.customerId)) { ElMessage.warning('客户ID必填'); return }
  const input: any = { customerId: Number(v.customerId) }
  if (v.postpartumDay !== '') input.postpartumDay = Number(v.postpartumDay)
  if (v.temperature !== '') input.temperature = Number(v.temperature)
  if (v.pulse !== '') input.pulse = Number(v.pulse)
  if (v.bloodPressure) input.bloodPressure = v.bloodPressure
  if (v.notes) input.notes = v.notes
  for (const k of Object.keys(LABELS)) if (v[k]) input[k] = v[k]
  try { await api().createNursingAssessment(input); ElMessage.success('评估已保存'); dlg.value = false; load() }
  catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}
onMounted(async () => {
  try { tpl.value = (await api().nursingTemplate()) as any || {} } catch { tpl.value = {} }
  try { board.value = await api().nursingTeamBoard() } catch { board.value = null }
  load()
})
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; }
.ph { margin: 0; font-size: 18px; }
.bar .el-input, .bar .el-button { margin-left: 8px; }
.card { margin-bottom: 14px; }
.board { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.bt { font-weight: 600; }
.pt { margin-right: 2px; }
.pt.clk { cursor: pointer; }
.al { margin-left: 12px; flex: 1 1 240px; }
.pop-h { font-weight: 600; font-size: 13px; padding-bottom: 6px; margin-bottom: 6px; border-bottom: 1px solid var(--el-border-color-lighter); }
.pop-list { display: flex; flex-direction: column; gap: 4px; max-height: 260px; overflow-y: auto; }
.pop-row { display: flex; align-items: center; justify-content: space-between; font-size: 13px; }
.pop-row .nm { color: var(--el-text-color-primary); }
.pop-row .st { color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px; white-space: nowrap; }
.pop-empty { font-size: 13px; color: var(--el-text-color-secondary); padding: 4px 0; }
</style>
