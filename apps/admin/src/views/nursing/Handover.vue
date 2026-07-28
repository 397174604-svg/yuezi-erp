<template>
  <div>
    <div class="bar">
      <h2 class="ph">入住 / 退房交接</h2>
      <div class="filters">
        <el-select v-model="kind" placeholder="类型" clearable style="width: 120px" @change="load"><el-option v-for="k in KINDS" :key="k" :label="k" :value="k" /></el-select>
        <el-select v-model="statusF" placeholder="状态" clearable style="width: 120px" @change="load"><el-option v-for="s in STATUS" :key="s" :label="s" :value="s" /></el-select>
        <el-button type="primary" @click="load">刷新</el-button>
        <el-button v-if="!auth.isHQ" type="success" @click="openNew">新建交接单</el-button>
        <el-tag v-else type="info" effect="plain" size="small">总部只读 · 交接由护理/月嫂现场经办</el-tag>
      </div>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe empty-text="暂无交接单">
      <el-table-column prop="handover_id" label="单号" width="80" />
      <el-table-column label="客户" width="90"><template #default="{ row }">客#{{ row.customer_id }}</template></el-table-column>
      <el-table-column prop="kind" label="类型" width="90">
        <template #default="{ row }"><el-tag :type="row.kind === '入住' ? 'success' : 'info'" effect="dark" size="small">{{ row.kind }}</el-tag></template>
      </el-table-column>
      <el-table-column label="物品清单" min-width="220"><template #default="{ row }">{{ itemsText(row.items_json) }}</template></el-table-column>
      <el-table-column prop="operator" label="经办" width="110" />
      <el-table-column prop="time" label="时间" width="170" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.status === '已确认' ? 'success' : 'warning'" effect="dark" size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }"><el-button v-if="!auth.isHQ && row.status !== '已确认'" link type="primary" size="small" @click="confirm(row)">确认</el-button></template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="新建交接单" width="460px">
      <el-form label-width="86px">
        <el-form-item label="客户ID"><el-input v-model="form.customerId" placeholder="客户编号" /></el-form-item>
        <el-form-item label="类型"><el-radio-group v-model="form.kind"><el-radio-button v-for="k in KINDS" :key="k" :value="k">{{ k }}</el-radio-button></el-radio-group></el-form-item>
        <el-form-item label="物品清单"><el-input v-model="form.items" type="textarea" :rows="4" placeholder="每行一项，如：待产包、母乳储奶袋、婴儿服×3" /></el-form-item>
        <el-form-item label="经办人"><el-input v-model="form.operator" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dlg = false">取消</el-button><el-button type="primary" @click="submit">提交</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore() // 新建/确认交接=护理·月嫂现场经办(有经办人署名),总部(老板/运营)只监督查看

const KINDS = ['入住', '退房']
const STATUS = ['待确认', '已确认']
const rows = ref<any[]>([])
const loading = ref(false)
const kind = ref('')
const statusF = ref('')

function itemsText(j: string): string {
  try { const a = JSON.parse(j || '[]'); return Array.isArray(a) ? a.join('、') : String(j || '—') } catch { return j || '—' }
}
async function load() {
  loading.value = true
  try {
    const data: any = await api().listHandovers({ kind: kind.value || undefined, status: statusF.value || undefined })
    rows.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false }
}

const dlg = ref(false)
const form = ref<{ customerId: string; kind: string; items: string; operator: string }>({ customerId: '', kind: '入住', items: '', operator: '' })
function openNew() { form.value = { customerId: '', kind: '入住', items: '', operator: '' }; dlg.value = true }
async function submit() {
  if (!form.value.customerId) { ElMessage.warning('客户ID必填'); return }
  const items = form.value.items.split('\n').map((s) => s.trim()).filter(Boolean)
  try {
    await api().createHandover({ customerId: Number(form.value.customerId), kind: form.value.kind, items, operator: form.value.operator || undefined })
    ElMessage.success('交接单已创建'); dlg.value = false; load()
  } catch (e: any) { ElMessage.error('创建失败：' + (e?.message || '')) }
}
async function confirm(row: any) {
  try { await api().confirmHandover(row.handover_id); ElMessage.success('已确认'); load() }
  catch (e: any) { ElMessage.error('确认失败：' + (e?.message || '')) }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0; }
.filters { display: flex; gap: 10px; }
</style>
