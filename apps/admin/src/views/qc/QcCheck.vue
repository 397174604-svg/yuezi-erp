<template>
  <div>
    <div class="bar"><h2 class="ph">品控检查</h2><el-button size="small" type="primary" @click="openNew">+ 发起检查单</el-button></div>
    <el-alert type="info" :closable="false" show-icon class="mb" title="按部门评分表(仪容20%/岗位60%/协作20%)对员工检查，逐项扣分→得分=100-总扣分，同额扣员工积分。店长仅可检查本店员工。" />
    <el-card shadow="never" v-loading="loading">
      <el-table :data="rows" size="small" border>
        <el-table-column prop="qc_id" label="单号" width="70" />
        <el-table-column prop="check_date" label="检查日" width="120" />
        <el-table-column prop="dept" label="部门" width="110" />
        <el-table-column prop="staff_name" label="被检员工" min-width="110" />
        <el-table-column label="得分" width="90" align="right"><template #default="{ row }"><span :class="row.score < 90 ? 'bad' : 'ok'">{{ row.score }}</span></template></el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-dialog v-model="show" title="发起品控检查单" width="620">
      <el-form label-width="90px">
        <el-form-item label="部门"><el-select v-model="form.dept" @change="loadTpl" placeholder="选部门"><el-option v-for="dp in depts" :key="dp" :label="dp" :value="dp" /></el-select></el-form-item>
        <el-form-item label="被检员工"><el-select v-model="form.staffId" filterable placeholder="选员工"><el-option v-for="s in staffList.filter(x => !form.dept || x.department === form.dept)" :key="s.staff_id" :label="s.name + '（' + (s.department || '') + '）'" :value="s.staff_id" /></el-select></el-form-item>
        <el-form-item label="扣分项">
          <div style="width:100%">
            <div v-for="(dt, i) in form.details" :key="i" class="line">
              <el-input v-model="dt.note" size="small" placeholder="问题描述" style="flex:1" />
              <el-input-number v-model="dt.deduct" :min="0" :max="100" size="small" />
              <el-button link type="danger" size="small" @click="form.details.splice(i, 1)">删</el-button>
            </div>
            <el-button size="small" @click="form.details.push({ note: '', deduct: 1 })">+ 加扣分项</el-button>
            <span class="score-hint">预计得分：{{ 100 - form.details.reduce((s, d) => s + (Number(d.deduct) || 0), 0) }}</span>
          </div>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="show = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">提交</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
const rows = ref<any[]>([]); const staffList = ref<any[]>([]); const depts = ref<string[]>([])
const loading = ref(false); const saving = ref(false); const show = ref(false)
const form = ref<any>({ dept: '', staffId: '', details: [], remark: '' })
async function load() { loading.value = true; try { rows.value = await api().qcRecords({}) } catch (e: any) { ElMessage.error(e?.message || '') } finally { loading.value = false } }
function loadTpl() { form.value.staffId = '' }
function openNew() { form.value = { dept: '', staffId: '', details: [], remark: '' }; show.value = true }
async function save() {
  if (!form.value.staffId) { ElMessage.warning('请选被检员工'); return }
  saving.value = true
  try {
    await api().qcCreateRecord({ staffId: Number(form.value.staffId), dept: form.value.dept || undefined, remark: form.value.remark, details: form.value.details.filter((d: any) => d.deduct > 0).map((d: any) => ({ deduct: Number(d.deduct), note: d.note })) })
    ElMessage.success('已提交'); show.value = false; await load()
  } catch (e: any) { ElMessage.error('提交失败：' + (e?.message || '')) } finally { saving.value = false }
}
onMounted(async () => {
  await load()
  try { const t = await api().qcTemplates({}) as { dept: string }[]; depts.value = [...new Set(t.map((x) => x.dept))] } catch {}
  try { staffList.value = await api().listStaff({}) } catch {}
})
</script>
<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; } .mb { margin-bottom: 12px; }
.line { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.score-hint { margin-left: 12px; font-weight: 600; color: var(--el-color-primary); }
.bad { color: var(--el-color-danger); font-weight: 700; } .ok { color: var(--el-color-success); font-weight: 600; }
</style>
