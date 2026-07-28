<template>
  <div>
    <h2 class="ph">营销与内容</h2>

    <el-tabs v-model="tab" class="mtabs">
      <!-- Tab1 商城商品 -->
      <el-tab-pane label="商城商品" name="products">
        <div class="bar">
          <el-form :inline="true" class="filters">
            <el-form-item>
              <el-select v-model="pf.status" placeholder="状态" clearable style="width: 120px">
                <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-input v-model="pf.cat" placeholder="分类" clearable style="width: 140px" @keyup.enter="reloadProducts" />
            </el-form-item>
            <el-form-item><el-button type="primary" @click="reloadProducts">查询</el-button></el-form-item>
          </el-form>
          <el-button v-if="isMgr" type="primary" @click="openCreate">上架商品</el-button>
          <span v-else class="muted" style="margin-left:8px;color:var(--el-text-color-secondary);font-size:12px">商品上架/定价由运营维护</span>
        </div>

        <el-table :data="products" v-loading="pLoading" border stripe empty-text="暂无商品">
          <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="cat" label="分类" width="130">
            <template #default="{ row }">{{ row.cat || '—' }}</template>
          </el-table-column>
          <el-table-column label="售价" width="120" align="right">
            <template #default="{ row }">{{ money(row.price) }}</template>
          </el-table-column>
          <el-table-column label="积分价" width="110" align="right">
            <template #default="{ row }">{{ row.points_price != null ? Number(row.points_price).toLocaleString() : '—' }}</template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" width="90" align="center">
            <template #default="{ row }">{{ row.stock ?? '—' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === '在售' ? 'success' : 'danger'" effect="dark" size="small">{{ row.status || '—' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="isMgr" label="操作" width="90" fixed="right">
            <template #default="{ row }"><el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button></template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="pPage" :page-count="pPageCount" @current-change="onPPage" />
        </div>
      </el-tab-pane>

      <!-- Tab2 商城订单 -->
      <el-tab-pane label="商城订单" name="orders">
        <el-table :data="mallOrders" v-loading="oLoading" border stripe empty-text="暂无订单">
          <el-table-column label="商品名" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ row.product_name || '—' }}</template>
          </el-table-column>
          <el-table-column label="客户#" width="120">
            <template #default="{ row }">{{ row.customer_id != null ? '#' + row.customer_id : '—' }}</template>
          </el-table-column>
          <el-table-column label="金额" width="130" align="right">
            <template #default="{ row }">{{ money(row.amount) }}</template>
          </el-table-column>
          <el-table-column label="支付方式" width="120">
            <template #default="{ row }">{{ row.pay_kind || '—' }}</template>
          </el-table-column>
          <el-table-column label="时间" min-width="170">
            <template #default="{ row }">{{ row.created_at || '—' }}</template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination layout="prev, pager, next" :page-size="pageSize" :current-page="oPage" :page-count="oPageCount" @current-change="onOPage" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 上架 / 编辑商品 -->
    <el-dialog v-model="formVisible" :title="editing ? '编辑商品' : '上架商品'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="商品名称" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="form.cat" placeholder="如：母婴用品 / 护理套餐" /></el-form-item>
        <el-form-item label="售价"><el-input-number v-model="form.price" :min="0" :precision="2" :step="10" controls-position="right" style="width: 200px" /></el-form-item>
        <el-form-item label="积分价"><el-input-number v-model="form.pointsPrice" :min="0" :step="100" controls-position="right" style="width: 200px" /></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" :step="1" controls-position="right" style="width: 200px" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 200px">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">{{ editing ? '保存' : '上架' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const isMgr = computed(() => auth.isManager) // 商城商品上架/编辑含定价=运营/管理层配置;一线只做基础营销(发帖/分群),商品写按钮不显避免死按钮

const statuses = ['在售', '下架']
const pageSize = 20
const tab = ref('products')

function money(v: any): string {
  return v == null ? '—' : '¥' + Number(v).toLocaleString()
}

// —— Tab1 商城商品 ——
const products = ref<any[]>([])
const pLoading = ref(false)
const pf = reactive<{ status: string; cat: string }>({ status: '', cat: '' })
const pPage = ref(1)
const pHasNext = ref(false)
const pPageCount = computed(() => (pHasNext.value ? pPage.value + 1 : pPage.value))

async function loadProducts() {
  pLoading.value = true
  try {
    const data: any = await api().listProducts({
      status: pf.status || undefined,
      cat: pf.cat || undefined,
      limit: pageSize,
      offset: (pPage.value - 1) * pageSize,
    })
    const list = Array.isArray(data) ? data : (data?.rows || [])
    products.value = list
    pHasNext.value = list.length === pageSize
  } catch (e: any) {
    ElMessage.error('商品加载失败：' + (e?.message || ''))
    products.value = []
    pHasNext.value = false
  } finally {
    pLoading.value = false
  }
}
function reloadProducts() { pPage.value = 1; loadProducts() }
function onPPage(p: number) { pPage.value = p; loadProducts() }

// —— 上架 / 编辑 ——
const formVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const editId = ref<any>(null)
const form = reactive<{ name: string; cat: string; price: number; pointsPrice: number; stock: number; status: string }>({
  name: '', cat: '', price: 0, pointsPrice: 0, stock: 0, status: '在售',
})

function resetForm() {
  form.name = ''
  form.cat = ''
  form.price = 0
  form.pointsPrice = 0
  form.stock = 0
  form.status = '在售'
}
function openCreate() {
  editing.value = false
  editId.value = null
  resetForm()
  formVisible.value = true
}
function openEdit(row: any) {
  editing.value = true
  editId.value = row.product_id
  form.name = row.name || ''
  form.cat = row.cat || ''
  form.price = Number(row.price) || 0
  form.pointsPrice = Number(row.points_price) || 0
  form.stock = Number(row.stock) || 0
  form.status = row.status || '在售'
  formVisible.value = true
}

async function submit() {
  saving.value = true
  try {
    const payload = {
      name: form.name,
      cat: form.cat,
      price: form.price,
      pointsPrice: form.pointsPrice,
      stock: form.stock,
      status: form.status,
    }
    if (editing.value) {
      await api().updateProduct(editId.value, payload)
      ElMessage.success('商品已更新')
    } else {
      await api().createProduct(payload)
      ElMessage.success('商品已上架')
    }
    formVisible.value = false
    loadProducts()
  } catch (e: any) {
    ElMessage.error((editing.value ? '更新' : '上架') + '失败：' + (e?.message || ''))
  } finally {
    saving.value = false
  }
}

// —— Tab2 商城订单 ——
const mallOrders = ref<any[]>([])
const oLoading = ref(false)
const oPage = ref(1)
const oHasNext = ref(false)
const oPageCount = computed(() => (oHasNext.value ? oPage.value + 1 : oPage.value))

async function loadMallOrders() {
  oLoading.value = true
  try {
    const data: any = await api().listMallOrders({
      limit: pageSize,
      offset: (oPage.value - 1) * pageSize,
    })
    const list = Array.isArray(data) ? data : (data?.rows || [])
    mallOrders.value = list
    oHasNext.value = list.length === pageSize
  } catch (e: any) {
    ElMessage.error('商城订单加载失败：' + (e?.message || ''))
    mallOrders.value = []
    oHasNext.value = false
  } finally {
    oLoading.value = false
  }
}
function onOPage(p: number) { oPage.value = p; loadMallOrders() }

onMounted(() => {
  loadProducts()
  loadMallOrders()
})
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 14px; }
.mtabs { margin-top: 4px; }
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.filters { margin: 0; }
.pager { margin-top: 14px; display: flex; justify-content: flex-end; }
</style>
