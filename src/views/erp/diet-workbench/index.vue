<template>
  <div class="diet-workbench">
    <div class="page-heading">
      <div>
        <div class="title-row">
          <i :class="pageConfig.icon" />
          <h2>{{ title }}</h2>
        </div>
        <p>{{ pageConfig.description }}</p>
      </div>
    </div>

    <el-card v-if="sharedWorkspaceTabs.length" shadow="never" class="shared-workbench-card">
      <div class="shared-workbench-title">{{ pageConfig.workspace.note }}</div>
      <el-tabs :value="title" @tab-click="switchSharedWorkspace">
        <el-tab-pane
          v-for="tab in sharedWorkspaceTabs"
          :key="tab.title"
          :label="tab.label"
          :name="tab.title"
        />
      </el-tabs>
    </el-card>

    <audited-surface-panel
      :config="pageConfig"
      show-action-icons
      @business-action="handleBusinessAction"
      @query-action="handleQueryAction"
    />

    <diet-p0-workflow
      v-if="p0WorkflowResources.includes(pageConfig.key)"
      :resource="pageConfig.key"
      :rows="filteredRows"
      @select="selectedRow = $event"
    />

    <section v-if="dietVisual" class="diet-visual" :class="`diet-${dietVisual.kind}`">
      <div class="diet-visual-copy"><span>{{ dietVisual.kicker }}</span><h3>{{ dietVisual.heading }}</h3><p>{{ dietVisual.description }}</p></div>
      <div class="diet-visual-stages"><article v-for="(stage, index) in dietVisual.stages" :key="stage"><b>{{ index + 1 }}</b><strong>{{ stage }}</strong><small>{{ dietVisual.notes[index] }}</small></article></div>
      <div class="diet-visual-footer"><span>当前查询记录：{{ filteredRows.length }} 条</span><el-button size="mini" @click="handleQueryAction('查询')">刷新</el-button></div>
    </section>

    <div v-if="pageConfig.mode === 'summary'" class="metric-grid">
      <el-card v-for="metric in metrics" :key="metric.label" shadow="hover">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>来自当前业务数据</small>
      </el-card>
    </div>

    <el-card v-if="pageConfig.mode === 'meal-calendar'" shadow="never" class="calendar-card">
      <div slot="header" class="table-header">
        <span>餐次排餐视图</span>
        <span>当前显示 {{ calendarRows.length }} 个餐次</span>
      </div>
      <div class="meal-board">
        <section v-for="item in calendarRows" :key="item.mealType" class="meal-column">
          <header>
            <span>{{ item.mealType }}</span>
            <el-tag size="mini" :type="tagType(item.status)">{{ item.status }}</el-tag>
          </header>
          <div class="meal-time">{{ item.deliveryTime || '待设置配送时间' }}</div>
          <div class="dish-name">{{ item.dishName }}</div>
          <div class="meal-meta">{{ item.room }} · {{ item.customerName }}</div>
          <div class="meal-note">禁忌：{{ item.taboo }}</div>
        </section>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <div slot="header" class="table-header">
        <span>{{ title }}列表</span>
        <span>共 {{ filteredRows.length }} 条</span>
      </div>
      <el-table
        :data="pagedRows"
        border
        stripe
        size="small"
        highlight-current-row
        @current-change="selectedRow = $event"
      >
        <el-table-column type="index" label="序号" width="55" fixed="left" />
        <el-table-column
          v-for="column in pageConfig.columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :width="column.width"
          :min-width="column.width ? undefined : 120"
          show-overflow-tooltip
        >
          <template slot-scope="{ row }">
            <el-tag v-if="column.tag" :type="tagType(row[column.key])" size="mini">
              {{ row[column.key] }}
            </el-tag>
            <span v-else-if="column.money">¥ {{ formatAmount(row[column.key]) }}</span>
            <span v-else>{{ row[column.key] }}</span>
          </template>
        </el-table-column>
      </el-table>
      <pagination
        v-show="filteredRows.length > pageSize"
        :total="filteredRows.length"
        :page.sync="page"
        :limit.sync="pageSize"
        @pagination="noop"
      />
    </el-card>

    <el-dialog
      :title="dialogTitle"
      :visible.sync="dialogVisible"
      width="760px"
      append-to-body
      @closed="resetDialog"
    >
      <el-form ref="recordForm" :model="recordForm" :rules="rules" label-width="110px">
        <el-row :gutter="18">
          <el-col v-for="field in dialogFields" :key="field.key" :span="field.type === 'textarea' ? 24 : 12">
            <el-form-item :label="field.label" :prop="field.key">
              <el-input
                v-if="field.type === 'input'"
                v-model="recordForm[field.key]"
                :placeholder="`请输入${field.label}`"
              />
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="recordForm[field.key]"
                :min="0"
                :precision="field.key.toLowerCase().includes('amount') || field.key.toLowerCase().includes('price') ? 2 : 0"
                controls-position="right"
                class="full-control"
              />
              <el-select
                v-else-if="field.type === 'select'"
                v-model="recordForm[field.key]"
                filterable
                clearable
                class="full-control"
                :placeholder="`请选择${field.label}`"
                @change="field.key === 'store' ? handleDialogStoreChange() : null"
              >
                <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
              </el-select>
              <el-select
                v-else-if="field.type === 'room-select'"
                v-model="recordForm.room"
                filterable
                clearable
                class="full-control"
                :disabled="!recordForm.store || roomOptionsLoading"
                :placeholder="recordForm.store ? '请选择该门店在住客户房间' : '请先选择门店'"
              >
                <el-option v-for="option in roomOptions" :key="option.value" :label="option.label" :value="option.value" />
              </el-select>
              <el-select
                v-else-if="field.type === 'customer-select'"
                v-model="recordForm.customerName"
                filterable
                clearable
                class="full-control"
                :disabled="!recordForm.store || referenceOptionsLoading"
                :placeholder="recordForm.store ? '请选择该门店在住客户' : '请先选择门店'"
                @change="syncCustomerRoom"
              >
                <el-option v-for="option in referenceOptions.customers" :key="option.id" :label="`${option.name} · ${option.room || '未分房'}`" :value="option.name" />
              </el-select>
              <el-select
                v-else-if="field.type === 'dish-select'"
                v-model="recordForm.dishName"
                filterable
                clearable
                class="full-control"
                :disabled="!recordForm.store || referenceOptionsLoading"
                :placeholder="recordForm.store ? '请选择可用菜品/套餐' : '请先选择门店'"
              >
                <el-option v-for="option in referenceOptions.dishes" :key="option.id" :label="option.name" :value="option.name" />
              </el-select>
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="recordForm[field.key]"
                type="date"
                value-format="yyyy-MM-dd"
                class="full-control"
                :placeholder="`请选择${field.label}`"
              />
              <el-switch v-else-if="field.type === 'switch'" v-model="recordForm[field.key]" />
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="recordForm[field.key]"
                type="textarea"
                :rows="3"
                :placeholder="`请输入${field.label}`"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord">保存</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Pagination from '@/components/Pagination'
import { getDietModuleData, getDietRoomOptions, getDietStoreReferenceOptions, performDietModuleAction, saveDietModuleRecord } from '@/api/erp-diet'
import { getDietPageConfig } from '@/config/diet-pages'
import { findErpRouteByTitle, workspaceTabs } from '@/utils/erp-workbench-tabs'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'
import DietP0Workflow from '@/views/erp/components/DietP0Workflow'

const stores = ['中心广场旗舰店', '黄河路轻奢店']
const mealTypes = ['早餐', '上午加餐', '午餐', '下午加餐', '晚餐', '晚间加餐']
const mealTimes = ['07:30', '10:00', '12:00', '15:30', '18:00', '20:30']

export default {
  name: 'DietWorkbench',
  components: { AuditedSurfacePanel, DietP0Workflow, Pagination },
  data() {
    return {
      filters: {},
      rows: [],
      page: 1,
      pageSize: 10,
      selectedRow: null,
      dialogVisible: false,
      dialogTitle: '',
      dialogFields: [],
      recordForm: {},
      saving: false,
      roomOptions: [],
      roomOptionsLoading: false,
      referenceOptions: { customers: [], dishes: [] },
      referenceOptionsLoading: false,
      loadSequence: 0,
      p0WorkflowResources: ['diet-statistics', 'meal-orders', 'dishes']
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    businessStoreId() {
      return String(this.currentStoreId || 'all')
    },
    isAllStores() {
      return this.businessStoreId === 'all'
    },
    title() {
      const meta = this.$route.meta || {}
      return String(meta.configTitle || meta.title || '客户餐单').replace(/\s*★\s*$/, '')
    },
    pageConfig() {
      return getDietPageConfig(this.title)
    },
    sharedWorkspaceTabs() {
      return workspaceTabs(this.pageConfig)
    },
    filteredRows() {
      const entries = Object.entries(this.filters).filter(([, value]) => {
        if (Array.isArray(value)) return value.length > 0
        return value !== '' && value !== null && value !== undefined
      })
      if (!entries.length) return this.rows
      return this.rows.filter(row => entries.every(([key, value]) => {
        if (Array.isArray(value)) {
          const target = String(
            row[key] || row.mealDate || row.deliveryDate || row.supplyDate ||
            row.purchaseDate || row.saleDate || row.transactionAt || ''
          ).slice(0, 10)
          return (!value[0] || target >= value[0]) && (!value[1] || target <= value[1])
        }
        return String(row[key] || '').includes(String(value))
      }))
    },
    pagedRows() {
      const start = (this.page - 1) * this.pageSize
      return this.filteredRows.slice(start, start + this.pageSize)
    },
    calendarRows() {
      const byMeal = []
      mealTypes.forEach(type => {
        const row = this.filteredRows.find(item => item.mealType === type)
        if (row) byMeal.push(row)
      })
      return byMeal
    },
    metrics() {
      const quantity = this.filteredRows.reduce((sum, row) => (
        sum + Number(row.plannedCount || row.taskCount || row.plannedQuantity || 0)
      ), 0)
      const completed = this.filteredRows.reduce((sum, row) => (
        sum + Number(row.signedCount || row.signedQuantity || row.deliveredCount || 0)
      ), 0)
      const exceptions = this.filteredRows.reduce((sum, row) => (
        sum + Number(row.returnedCount || row.returnedQuantity || row.timeoutCount || 0)
      ), 0)
      return [
        { label: '统计记录', value: this.filteredRows.length },
        { label: '计划数量', value: quantity },
        { label: '完成数量', value: completed },
        { label: '异常/退回', value: exceptions }
      ]
    },
    dietVisual() {
      const views = {
        'customer-meal-plans': { kind: 'weekly', kicker: '周餐单视图', heading: '客户餐单与禁忌校验', description: '先按入住客户和日期排定餐次，再由营养师核对禁忌与配送时间。', stages: ['早餐', '午餐', '下午加餐', '晚餐'], notes: ['客户餐单', '营养搭配', '禁忌核验', '配送时间'] },
        'meal-orders': { kind: 'delivery', kicker: '配送任务流', heading: '订餐、备餐与签收', description: '配送状态应从订单生成，签收、退餐和超时信息独立留痕。', stages: ['客户订餐', '厨房备餐', '配送出餐', '客户签收'], notes: ['确认餐次', '制作清单', '配送人员', '异常回传'] },
        'guest-meal-supply': { kind: 'delivery', kicker: '供餐执行流', heading: '供餐、配送与签收', description: '客餐供餐与月子餐单分开核算，按客户和门店保留供餐记录。', stages: ['生成供餐单', '厨房出餐', '配送核验', '签收留痕'], notes: ['供餐对象', '出餐数量', '配送时间', '签收状态'] },
        dishes: { kind: 'library', kicker: '菜品库', heading: '菜品、食材与禁忌标签', description: '菜品库维护的是可用菜品与营养标签，不等同于客户的某一次配送订单。', stages: ['菜品建档', '营养标签', '禁忌规则', '启停管理'], notes: ['名称与类别', '营养信息', '适用限制', '可售状态'] },
        'nutrition-soups': { kind: 'library', kicker: '汤品库', heading: '营养汤品与供应规则', description: '按汤品配方、供应周期和适用客户维护，配送记录另行生成。', stages: ['汤品建档', '适用规则', '供应周期', '启停管理'], notes: ['汤品名称', '禁忌信息', '餐次设置', '当前状态'] }
      }
      return views[this.pageConfig.key] || null
    },
    rules() {
      return this.dialogFields.reduce((rules, field) => {
        if (field.required) {
          rules[field.key] = [{ required: true, message: `请填写${field.label}`, trigger: field.type === 'select' ? 'change' : 'blur' }]
        }
        return rules
      }, {})
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.initializePage()
      }
    },
    currentStoreId(value, previous) {
      if (String(value) !== String(previous)) this.initializePage()
    }
  },
  methods: {
    switchSharedWorkspace(tab) {
      if (!tab.name || tab.name === this.title) return
      const target = findErpRouteByTitle(this.$router.options.routes, tab.name)
      if (!target) {
        this.$message.error('未找到对应工作台入口，请联系管理员核对菜单配置。')
        return
      }
      this.$router.push({ name: target.name, query: { ...this.$route.query }})
    },
    async initializePage() {
      this.filters = {}
      this.page = 1
      this.selectedRow = null
      await this.loadModuleData()
    },
    async loadModuleData() {
      const sequence = ++this.loadSequence
      const resource = this.pageConfig.key
      try {
        const response = await getDietModuleData(resource, {
          ...this.filters,
          storeId: this.businessStoreId,
          page: 1,
          pageSize: this.pageSize
        })
        if (this.loadSequence === sequence) this.rows = response.data.list || []
      } catch (error) {
        if (this.loadSequence === sequence) this.rows = []
      }
    },
    createDemoRow(index) {
      const day = String((index % 9) + 14).padStart(2, '0')
      const dateValue = `2026-07-${day}`
      const mealType = mealTypes[index % mealTypes.length]
      const status = ['待排餐', '已排餐', '备餐中', '配送中', '已签收', '已退餐'][index % 6]
      const amount = 36 + index * 4
      return {
        id: `DIET-DEMO-${String(index + 1).padStart(4, '0')}`,
        store: stores[index % stores.length],
        customerName: `演示客户${String.fromCharCode(65 + index % 6)}`,
        customerType: ['入住客户', '散客', '陪护人员', '员工'][index % 4],
        mobile: `138****${String(1200 + index).slice(-4)}`,
        room: `${2 + index % 4}0${1 + index % 8}`,
        mealDate: dateValue,
        statDate: dateValue,
        deliveryDate: dateValue,
        supplyDate: dateValue,
        purchaseDate: dateValue,
        saleDate: dateValue,
        transactionAt: `${dateValue} ${mealTimes[index % mealTimes.length]}`,
        mealType,
        dishCode: `DISH-${String(index + 1).padStart(4, '0')}`,
        dishName: ['山药小米粥', '银耳红枣羹', '莲藕排骨汤', '清蒸时蔬', '菌菇鸡汤', '时令水果'][index % 6],
        dishCategory: ['主食', '汤羹', '荤菜', '素菜', '点心', '水果'][index % 6],
        ingredients: '当日新鲜食材组合',
        nutrition: '均衡营养',
        tabooTag: index % 4 ? '无' : '需关注',
        taboo: index % 4 ? '暂无饮食禁忌' : '需按客户档案核对禁忌',
        dietitian: '刘营养师',
        unit: '份',
        quantity: 1 + index % 3,
        standardPrice: amount,
        enabled: index % 5 ? '启用' : '停用',
        creator: '演示录入人',
        createdAt: `${dateValue} 09:00`,
        packageCode: `DP-${String(index + 1).padStart(4, '0')}`,
        packageName: ['标准月子膳食套餐', '调理膳食套餐', '陪护餐套餐'][index % 3],
        cycleDays: [28, 42, 7][index % 3],
        mealStandard: '每日三餐三加餐',
        packageAmount: 1680 + index * 50,
        effectiveDate: '2026-07-01',
        expiryDate: '2026-12-31',
        status,
        deliveryTime: mealTimes[index % mealTimes.length],
        remark: '仅用于前端字段与交互演示。',
        plannedCount: 35 + index,
        preparedCount: 32 + index,
        deliveredCount: 30 + index,
        signedCount: 28 + index,
        returnedCount: index % 3,
        completionRate: `${92 + index % 6}%`,
        customerCount: 25 + index,
        deliveryStaff: `演示配送员${String.fromCharCode(65 + index % 3)}`,
        taskCount: 30 + index,
        timeoutCount: index % 2,
        firstDeliveryAt: `${dateValue} 07:20`,
        lastSignedAt: `${dateValue} 18:45`,
        soupCode: `SOUP-${String(index + 1).padStart(4, '0')}`,
        soupName: ['红枣银耳汤', '莲藕排骨汤', '菌菇鸡汤'][index % 3],
        supplyType: ['常规营养汤', '产后调理汤', '特殊医嘱汤'][index % 3],
        supplyPeriod: ['上午', '午间', '晚间'][index % 3],
        applicableCustomer: '入住客户（演示）',
        contraindication: index % 3 ? '无' : '待营养师确认',
        plannedQuantity: 20 + index,
        preparedQuantity: 19 + index,
        deliveredQuantity: 18 + index,
        signedQuantity: 17 + index,
        returnedQuantity: index % 2,
        supplyNo: `GS-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        amount,
        paymentMethod: ['合同套餐', '餐卡', '微信', '挂账'][index % 4],
        supplyStatus: ['待供应', '已供应', '已签收', '已取消'][index % 4],
        signedAt: index % 4 === 2 ? `${dateValue} 12:35` : '—',
        purchaseNo: `CG-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        ingredientName: ['东北小米', '新鲜莲藕', '排骨', '时令蔬菜'][index % 4],
        specification: ['25kg/袋', '5kg/筐', '10kg/箱', '15kg/筐'][index % 4],
        purchaseQuantity: 10 + index,
        unitPrice: 12 + index,
        supplier: `演示供应商${String.fromCharCode(65 + index % 3)}`,
        auditStatus: index % 3 ? '已审核' : '待审核',
        arrivalStatus: ['待到货', '部分到货', '已到货'][index % 3],
        saleNo: `XS-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        saleType: ['膳食套餐', '单点餐品', '营养汤', '客餐'][index % 4],
        itemName: ['标准月子膳食套餐', '山药小米粥', '红枣银耳汤', '陪护午餐'][index % 4],
        saleAmount: amount * 3,
        receivedAmount: index % 3 ? amount * 3 : amount,
        paymentStatus: ['未收款', '部分收款', '已收款', '已退款'][index % 4],
        salesperson: '李顾问',
        orderNo: `DC-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        deliveryAddress: `${2 + index % 4}楼演示房间`,
        orderStatus: ['待确认', '待备餐', '备餐中', '配送中', '已签收', '已退餐'][index % 6],
        orderedAt: `${dateValue} 08:30`,
        cardNo: `MEAL-${String(80001 + index)}`,
        openedAt: dateValue,
        totalRecharge: 2000 + index * 100,
        totalConsume: 320 + index * 20,
        balance: 1680 + index * 80,
        cardStatus: ['正常', '正常', '挂失', '已退卡'][index % 4],
        operator: '演示操作员',
        lastOperatedAt: `${dateValue} 15:20`,
        transactionNo: `LS-${dateValue.replace(/-/g, '')}-${String(index + 1).padStart(3, '0')}`,
        transactionType: ['开卡', '充值', '消费', '退款', '退卡'][index % 5],
        beforeBalance: 1800 + index * 80,
        afterBalance: 1800 + index * 80 + (index % 2 ? amount : -amount),
        relatedDocumentNo: `REF-DEMO-${String(index + 1).padStart(4, '0')}`
      }
    },
    async handleQueryAction(action, filters = {}) {
      if (/查询|搜索/.test(String(action).replace(/\s+/g, ''))) {
        this.filters = filters
        this.page = 1
        await this.loadModuleData()
        this.$message.success(`已按当前门店和查询条件加载 ${this.filteredRows.length} 条记录`)
      } else if (action === '导出') {
        this.exportCsv()
      } else if (action === '打印') {
        window.print()
      }
    },
    handleBusinessAction(action) {
      if (this.isAllStores && !['导出', '打印'].includes(action)) {
        this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
        return
      }
      if (action === '导出') return this.exportCsv()
      if (action === '打印') return window.print()
      if (['添加', '开卡'].includes(action)) return this.openRecordDialog(action)
      if (action === '编辑') {
        if (!this.requireSelection()) return
        return this.openRecordDialog(action, this.selectedRow)
      }
      if (['删除', '启用', '停用', '提交', '审核', '反审核', '确认供应', '确认签收', '确认下单', '开始备餐', '开始配送', '退餐', '挂失', '恢复', '退卡', '收款', '退款'].includes(action)) {
        if (!this.requireSelection()) return
      }
      this.$confirm(`确认对当前记录执行“${action}”？操作将写入当前门店并保留审计记录。`, '业务操作', {
        type: 'warning'
      }).then(async() => {
        await performDietModuleAction(this.pageConfig.key, action, {
          recordId: this.selectedRow && this.selectedRow.recordId,
          storeId: (this.selectedRow && this.selectedRow.storeId) || this.businessStoreId
        })
        await this.loadModuleData()
        this.$message.success(`${action}已完成`)
      }).catch(error => {
        if (error && error !== 'cancel' && error !== 'close') {
          this.$message.warning(error.message || '操作失败，请核对门店权限和业务状态')
        }
      })
    },
    requireSelection() {
      if (this.selectedRow && this.selectedRow.recordId) return true
      if (this.selectedRow) {
        this.$message.warning('历史记录为只读，请选择可处理的业务记录')
        return false
      }
      this.$message.warning('请先选择一条业务记录')
      return false
    },
    openRecordDialog(action, row = {}) {
      const fields = this.pageConfig.formFields || []
      if (!fields.length) {
        this.$message.warning('该动作表单尚待原系统二次核验')
        return
      }
      this.dialogTitle = `${action}${this.title}`
      this.dialogFields = fields
      this.recordForm = fields.reduce((form, field) => {
        const value = row[field.key]
        form[field.key] = value !== undefined ? value : (field.type === 'number' ? 0 : field.type === 'switch' ? true : '')
        return form
      }, {})
      if (fields.some(field => field.key === 'store') && !this.recordForm.store) {
        this.recordForm.store = stores[Number(this.businessStoreId) - 1] || ''
      }
      this.loadRoomOptions()
      this.loadStoreReferenceOptions()
      this.dialogVisible = true
    },
    async handleDialogStoreChange() {
      this.recordForm.room = ''
      this.recordForm.customerName = ''
      this.recordForm.dishName = ''
      await Promise.all([this.loadRoomOptions(), this.loadStoreReferenceOptions()])
    },
    async loadRoomOptions() {
      if (!this.dialogFields.some(field => field.type === 'room-select')) return
      if (!this.recordForm.store) {
        this.roomOptions = []
        return
      }
      this.roomOptionsLoading = true
      try {
        const response = await getDietRoomOptions({ store: this.recordForm.store, storeId: this.businessStoreId })
        this.roomOptions = (response.data.list || []).map(item => ({
          value: item.room,
          label: `${item.room} · ${item.customerName}`
        }))
      } catch (error) {
        this.roomOptions = []
        this.$message.warning(error.message || '无法加载当前门店在住客户房间')
      } finally {
        this.roomOptionsLoading = false
      }
    },
    async loadStoreReferenceOptions() {
      if (!this.recordForm.store) {
        this.referenceOptions = { customers: [], dishes: [] }
        return
      }
      this.referenceOptionsLoading = true
      try {
        const response = await getDietStoreReferenceOptions({
          store: this.recordForm.store,
          storeId: this.businessStoreId
        })
        this.referenceOptions = {
          customers: response.data.customers || [],
          dishes: response.data.dishes || []
        }
      } catch (error) {
        this.referenceOptions = { customers: [], dishes: [] }
        this.$message.warning(error.message || '无法加载当前门店客户和菜品选项')
      } finally {
        this.referenceOptionsLoading = false
      }
    },
    syncCustomerRoom(customerName) {
      const customer = this.referenceOptions.customers.find(item => item.name === customerName)
      if (customer && customer.room) this.recordForm.room = customer.room
    },
    saveRecord() {
      this.$refs.recordForm.validate(async valid => {
        if (!valid) return
        if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
        this.saving = true
        try {
          if (this.dialogFields.some(field => field.type === 'room-select')) {
            const requiresRoom = this.pageConfig.key === 'customer-meal-plans' || this.recordForm.customerType === '入住客户'
            if (requiresRoom && !this.recordForm.room) {
              this.$message.warning('请从当前门店在住客户房间列表中选择房间')
              return
            }
          }
          await saveDietModuleRecord(this.pageConfig.key, {
            ...this.recordForm,
            recordId: this.dialogTitle.startsWith('编辑') && this.selectedRow
              ? this.selectedRow.recordId
              : undefined,
            storeId: (this.selectedRow && this.selectedRow.storeId) || this.businessStoreId
          })
          await this.loadModuleData()
          this.dialogVisible = false
          this.$message.success('已保存到当前门店')
        } catch (error) {
          this.$message.warning(error.message || '保存失败，请核对门店、房间归属和入住状态')
        } finally {
          this.saving = false
        }
      })
    },
    applyLocalAction(action) {
      if (!this.selectedRow) return
      const actionMapping = {
        启用: ['enabled', '启用'],
        停用: ['enabled', '停用'],
        提交: ['auditStatus', '待审核'],
        审核: ['auditStatus', '已审核'],
        反审核: ['auditStatus', '待审核'],
        确认供应: ['supplyStatus', '已供应'],
        确认签收: ['orderStatus', '已签收'],
        确认下单: ['orderStatus', '待备餐'],
        开始备餐: ['orderStatus', '备餐中'],
        开始配送: ['orderStatus', '配送中'],
        退餐: ['orderStatus', '已退餐'],
        挂失: ['cardStatus', '挂失'],
        恢复: ['cardStatus', '正常'],
        退卡: ['cardStatus', '已退卡'],
        收款: ['paymentStatus', '已收款'],
        退款: ['paymentStatus', '已退款']
      }
      if (action === '删除') {
        this.rows = this.rows.filter(row => row.id !== this.selectedRow.id)
        this.selectedRow = null
      } else if (actionMapping[action]) {
        this.$set(this.selectedRow, actionMapping[action][0], actionMapping[action][1])
      }
    },
    resetDialog() {
      this.dialogFields = []
      this.recordForm = {}
      this.$nextTick(() => {
        if (this.$refs.recordForm) this.$refs.recordForm.clearValidate()
      })
    },
    tagType(value) {
      if (['启用', '已审核', '已到货', '已供应', '已签收', '正常', '已收款', '充值'].includes(value)) return 'success'
      if (['停用', '已取消', '已退餐', '已退卡', '已退款', '退卡'].includes(value)) return 'danger'
      if (['待排餐', '备餐中', '配送中', '待审核', '部分到货', '挂失', '部分收款'].includes(value)) return 'warning'
      return 'info'
    },
    formatAmount(value) {
      const amount = Number(value || 0)
      return amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    exportCsv() {
      const columns = this.pageConfig.columns
      const lines = [
        columns.map(item => item.label).join(','),
        ...this.filteredRows.map(row => columns.map(item => `"${String(row[item.key] || '').replace(/"/g, '""')}"`).join(','))
      ]
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.title}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    },
    noop() {}
  }
}
</script>

<style lang="scss" scoped>
.diet-workbench {
  min-height: calc(100vh - 84px);
  padding: 20px;
  background: #f5f7fa;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;

  .title-row {
    display: flex;
    align-items: center;
    gap: 10px;

    i {
      color: #58b66f;
      font-size: 24px;
    }

    h2 {
      margin: 0;
      color: #303133;
      font-size: 22px;
    }
  }

  p {
    margin: 8px 0 0 34px;
    color: #7a8495;
  }
}

.evidence-alert,
.action-card,
.filter-card,
.metric-grid,
.calendar-card {
  margin-bottom: 14px;
}

.shared-workbench-card {
  margin-bottom: 14px;
}

.shared-workbench-title {
  margin-bottom: 4px;
  color: #606266;
  font-size: 13px;
}

.action-card ::v-deep .el-card__body {
  padding: 12px 16px;
}

.demo-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.filter-card ::v-deep .el-card__body {
  padding-bottom: 4px;
}

.filter-card ::v-deep .el-input,
.filter-card ::v-deep .el-select {
  width: 180px;
}

.filter-card ::v-deep .el-date-editor--daterange {
  width: 260px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;

  .el-card ::v-deep .el-card__body {
    display: grid;
    gap: 7px;
  }

  span,
  small {
    color: #8b94a4;
  }

  strong {
    color: #303133;
    font-size: 30px;
  }
}
.diet-visual { margin-bottom: 14px; padding: 18px; border: 1px solid #e8dfca; border-radius: 12px; background: #fffdf8; }.diet-visual-copy span { color: #a77932; font-size: 12px; font-weight: 700; }.diet-visual-copy h3 { margin: 5px 0; color: #6c532c; }.diet-visual-copy p { margin: 0; color: #8f7e65; font-size: 12px; }.diet-visual-stages { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px; }.diet-visual-stages article { position: relative; padding: 12px; border-radius: 9px; background: #fff; border-bottom: 3px solid #d2a557; }.diet-visual-stages article:not(:last-child)::after { position: absolute; top: 50%; left: calc(100% + 1px); width: 8px; height: 1px; background: #e1cfab; content: ''; }.diet-visual-stages b { display: inline-grid; width: 21px; height: 21px; border-radius: 50%; color: #fff; background: #b88b43; place-items: center; font-size: 11px; }.diet-visual-stages strong, .diet-visual-stages small { display: block; }.diet-visual-stages strong { margin-top: 7px; color: #6b5535; font-size: 13px; }.diet-visual-stages small { margin-top: 3px; color: #9c8d77; font-size: 11px; }.diet-visual-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; padding-top: 12px; border-top: 1px solid #efe5d1; color: #98876f; font-size: 12px; }.diet-library .diet-visual-stages article { border-bottom-color: #69a07d; background: #fbfefb; }.diet-library .diet-visual-stages b { background: #5d9673; }.diet-delivery .diet-visual-stages article { border-bottom-color: #6a9cbd; background: #fbfdff; }.diet-delivery .diet-visual-stages b { background: #5b8eaf; }

.table-header {
  display: flex;
  justify-content: space-between;
  color: #606266;
}

.meal-board {
  display: grid;
  grid-template-columns: repeat(6, minmax(160px, 1fr));
  gap: 12px;
  overflow-x: auto;
}

.meal-column {
  min-width: 160px;
  padding: 14px;
  border: 1px solid #e6efe8;
  border-radius: 8px;
  background: #f7fcf8;

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    color: #2f7041;
    font-weight: 600;
  }
}

.meal-time,
.meal-meta,
.meal-note {
  color: #8a949f;
  font-size: 12px;
}

.dish-name {
  margin: 8px 0;
  color: #303133;
  font-size: 15px;
  font-weight: 600;
}

.meal-note {
  margin-top: 8px;
}

.dialog-alert {
  margin-bottom: 18px;
}

.full-control {
  width: 100%;
}

@media (max-width: 1000px) {
  .page-heading {
    display: block;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
