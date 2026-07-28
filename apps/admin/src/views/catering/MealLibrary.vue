<template>
  <div>
    <h2 class="ph">月子餐库</h2>
    <el-tabs v-model="tab">
      <!-- 月子餐方案库 -->
      <el-tab-pane label="餐单方案" name="plans">
        <div class="bar">
          <el-select v-model="planStage" placeholder="阶段" clearable style="width: 120px" @change="loadPlans"><el-option v-for="s in STAGES" :key="s" :label="s" :value="s" /></el-select>
          <el-button type="primary" @click="loadPlans">刷新</el-button>
          <el-button type="success" @click="planDlg = true">新增方案</el-button>
        </div>
        <el-table :data="plans" v-loading="loadingP" border stripe empty-text="暂无餐单方案">
          <el-table-column prop="plan_id" label="#" width="60" />
          <el-table-column prop="name" label="方案名" min-width="160" />
          <el-table-column prop="stage" label="阶段" width="100" />
          <el-table-column prop="days" label="周期(天)" width="100" align="center" />
          <el-table-column prop="note" label="备注" min-width="140" />
          <el-table-column prop="status" label="状态" width="80" />
          <el-table-column label="操作" width="170" fixed="right"><template #default="{ row }">
            <el-button link type="primary" @click="openItems(row)">配菜单</el-button>
            <el-button link type="success" @click="openGen(row)">一键配餐</el-button>
          </template></el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 菜品库 -->
      <el-tab-pane label="菜品库" name="dishes">
        <div class="bar">
          <el-select v-model="dishCat" placeholder="分类" clearable style="width: 120px" @change="loadDishes"><el-option v-for="c in CATS" :key="c" :label="c" :value="c" /></el-select>
          <el-button type="primary" @click="loadDishes">刷新</el-button>
          <el-button type="success" @click="dishDlg = true">新增菜品</el-button>
        </div>
        <el-table :data="dishes" v-loading="loadingD" border stripe empty-text="暂无菜品">
          <el-table-column prop="dish_id" label="#" width="60" />
          <el-table-column prop="name" label="菜品名" min-width="160" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="nutrients" label="营养/功效" min-width="200" />
          <el-table-column prop="status" label="状态" width="90" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="planDlg" title="新增餐单方案" width="420px">
      <el-form label-width="82px">
        <el-form-item label="方案名"><el-input v-model="planForm.name" /></el-form-item>
        <el-form-item label="阶段"><el-select v-model="planForm.stage" style="width:100%"><el-option v-for="s in STAGES" :key="s" :label="s" :value="s" /></el-select></el-form-item>
        <el-form-item label="周期(天)"><el-input v-model="planForm.days" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="planForm.note" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="planDlg = false">取消</el-button><el-button type="primary" @click="savePlan">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="dishDlg" title="新增菜品" width="420px">
      <el-form label-width="82px">
        <el-form-item label="菜品名"><el-input v-model="dishForm.name" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="dishForm.category" style="width:100%"><el-option v-for="c in CATS" :key="c" :label="c" :value="c" /></el-select></el-form-item>
        <el-form-item label="营养/功效"><el-input v-model="dishForm.nutrients" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="dishForm.note" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dishDlg = false">取消</el-button><el-button type="primary" @click="saveDish">保存</el-button></template>
    </el-dialog>

    <!-- 配菜单：方案 × 天 × 餐次 → 菜品 -->
    <el-dialog v-model="itemsDlg" :title="'配菜单 · ' + (curPlan?.name || '')" width="660px">
      <el-form :inline="true" size="small" class="mb">
        <el-form-item label="第几天"><el-input v-model="itemForm.dayNo" style="width:64px" /></el-form-item>
        <el-form-item label="餐次"><el-select v-model="itemForm.mealType" style="width:96px"><el-option v-for="m in MEALS" :key="m" :label="m" :value="m" /></el-select></el-form-item>
        <el-form-item label="菜品"><el-select v-model="itemForm.dishId" filterable placeholder="选择菜品" style="width:190px"><el-option v-for="d in dishes" :key="d.dish_id" :label="d.name" :value="d.dish_id" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="addItem">加入</el-button></el-form-item>
      </el-form>
      <el-table :data="items" border stripe size="small" empty-text="尚未配置菜单，先加入菜品">
        <el-table-column prop="day_no" label="第几天" width="80" align="center" />
        <el-table-column prop="meal_type" label="餐次" width="90" />
        <el-table-column prop="dish_name" label="菜品" min-width="180" />
      </el-table>
    </el-dialog>

    <!-- 一键配餐：按方案为客户逐天生成每日配餐 -->
    <el-dialog v-model="genDlg" :title="'一键配餐 · ' + (curPlan?.name || '')" width="470px">
      <el-form label-width="88px" size="small">
        <el-form-item label="客户"><el-select v-model="genForm.customerId" filterable placeholder="选择客户" style="width:100%"><el-option v-for="c in customers" :key="c.customer_id" :label="c.name + (c.phone ? ' / ' + c.phone : '')" :value="c.customer_id" /></el-select></el-form-item>
        <el-form-item label="起始日期"><el-date-picker v-model="genForm.startDate" type="date" value-format="YYYY-MM-DD" placeholder="YYYY-MM-DD" style="width:100%" /></el-form-item>
      </el-form>
      <el-alert title="按方案菜单结构逐天展开写入该客户每日配餐；同日同餐次已排则自动跳过（不重复）。" type="info" :closable="false" show-icon />
      <template #footer><el-button @click="genDlg = false">取消</el-button><el-button type="primary" :loading="genLoading" @click="doGenerate">生成</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const STAGES = ['孕期', '月子', '产康', '通用']
const CATS = ['主食', '汤品', '菜肴', '点心', '茶饮']
const tab = ref('plans')

const plans = ref<any[]>([]); const loadingP = ref(false); const planStage = ref('')
async function loadPlans() {
  loadingP.value = true
  try { plans.value = (await api().listMealPlans({ stage: planStage.value || undefined }) as any[]) || [] }
  catch (e: any) { ElMessage.error('方案加载失败：' + (e?.message || '')) } finally { loadingP.value = false }
}
const planDlg = ref(false)
const planForm = ref<{ name: string; stage: string; days: string; note: string }>({ name: '', stage: '月子', days: '', note: '' })
async function savePlan() {
  if (!planForm.value.name) { ElMessage.warning('方案名必填'); return }
  try {
    await api().createMealPlan({ name: planForm.value.name, stage: planForm.value.stage, days: planForm.value.days ? Number(planForm.value.days) : undefined, note: planForm.value.note || undefined })
    ElMessage.success('已保存'); planDlg.value = false; planForm.value = { name: '', stage: '月子', days: '', note: '' }; loadPlans()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}

const dishes = ref<any[]>([]); const loadingD = ref(false); const dishCat = ref('')
async function loadDishes() {
  loadingD.value = true
  try { dishes.value = (await api().listMealDishes({ category: dishCat.value || undefined }) as any[]) || [] }
  catch (e: any) { ElMessage.error('菜品加载失败：' + (e?.message || '')) } finally { loadingD.value = false }
}
const dishDlg = ref(false)
const dishForm = ref<{ name: string; category: string; nutrients: string; note: string }>({ name: '', category: '汤品', nutrients: '', note: '' })
async function saveDish() {
  if (!dishForm.value.name) { ElMessage.warning('菜品名必填'); return }
  try {
    await api().createMealDish({ name: dishForm.value.name, category: dishForm.value.category, nutrients: dishForm.value.nutrients || undefined, note: dishForm.value.note || undefined })
    ElMessage.success('已保存'); dishDlg.value = false; dishForm.value = { name: '', category: '汤品', nutrients: '', note: '' }; loadDishes()
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}

// —— 配菜单 + 一键配餐 ——
const MEALS = ['早餐', '午餐', '晚餐', '加餐']
const curPlan = ref<any>(null)
const itemsDlg = ref(false); const items = ref<any[]>([])
const itemForm = ref<{ dayNo: string; mealType: string; dishId: number | undefined }>({ dayNo: '1', mealType: '早餐', dishId: undefined })
const genDlg = ref(false); const genLoading = ref(false)
const genForm = ref<{ customerId: number | undefined; startDate: string }>({ customerId: undefined, startDate: '' })
const customers = ref<any[]>([])

async function loadItems(planId: number) {
  try { items.value = (await api().listMealPlanItems(planId) as any[]) || [] }
  catch (e: any) { ElMessage.error('菜单加载失败：' + (e?.message || '')) }
}
async function openItems(row: any) {
  curPlan.value = row
  if (!dishes.value.length) await loadDishes()
  await loadItems(row.plan_id); itemsDlg.value = true
}
async function addItem() {
  if (!itemForm.value.dishId) { ElMessage.warning('请选择菜品'); return }
  try {
    await api().addMealPlanItem(curPlan.value.plan_id, { dayNo: Number(itemForm.value.dayNo) || 1, mealType: itemForm.value.mealType, dishId: itemForm.value.dishId })
    ElMessage.success('已加入'); loadItems(curPlan.value.plan_id)
  } catch (e: any) { ElMessage.error('加入失败：' + (e?.message || '')) }
}
async function openGen(row: any) {
  curPlan.value = row
  if (!customers.value.length) {
    try { const d = await api().listCustomers({ limit: 500 }) as any; customers.value = Array.isArray(d) ? d : (d?.rows || []) } catch { /* 名单加载失败不阻断 */ }
  }
  genForm.value = { customerId: undefined, startDate: '' }; genDlg.value = true
}
async function doGenerate() {
  if (!genForm.value.customerId || !genForm.value.startDate) { ElMessage.warning('客户、起始日期必填'); return }
  genLoading.value = true
  try {
    const r = await api().generateMealPlan(curPlan.value.plan_id, { customerId: genForm.value.customerId, startDate: genForm.value.startDate }) as { generated: number; skipped: number; days: number }
    ElMessage.success(`已生成 ${r.generated} 餐（跳过 ${r.skipped}，覆盖 ${r.days} 天）`); genDlg.value = false
  } catch (e: any) { ElMessage.error('生成失败：' + (e?.message || '')) }
  finally { genLoading.value = false }
}

onMounted(() => { loadPlans(); loadDishes() })
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 8px; }
.bar { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.mb { margin-bottom: 8px; }
</style>
