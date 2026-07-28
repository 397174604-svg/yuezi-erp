<template>
  <div v-loading="loading" class="mvp-page">
    <div class="summary-row">
      <div v-for="item in visibleSummaryCards" :key="item.key" class="summary-card">
        <div class="summary-label">{{ item.label }}</div>
        <div class="summary-value">{{ overview[item.key] || 0 }}</div>
      </div>
    </div>

    <el-alert
      title="请按“客户建档 → 合同审核 → 收款审核 → 订房入住”的顺序办理"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-tabs v-model="activeTab" class="business-tabs">
      <el-tab-pane v-if="hasPermission('CUSTOMER.VIEW')" label="1 客户建档" name="customers">
        <el-form
          v-if="hasPermission('CUSTOMER.CREATE')"
          ref="customerForm"
          :model="customerForm"
          :rules="customerRules"
          label-width="92px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="customerForm.storeId" filterable>
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户姓名" prop="name">
                <el-input v-model.trim="customerForm.name" maxlength="50" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="手机号" prop="phone">
                <el-input v-model.trim="customerForm.phone" maxlength="11" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="微信号">
                <el-input v-model.trim="customerForm.wechat" maxlength="80" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户状态">
                <el-select v-model="customerForm.status">
                  <el-option v-for="status in customerStatuses" :key="status" :label="status" :value="status" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户来源">
                <el-input v-model.trim="customerForm.source" maxlength="80" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="业务员">
                <el-select v-model="customerForm.salesStaffId" clearable filterable>
                  <el-option
                    v-for="staff in customerStaff"
                    :key="staff.id"
                    :label="`${staff.name}（${staff.department || staff.position || '员工'}）`"
                    :value="staff.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="预产期">
                <el-date-picker v-model="customerForm.edc" type="date" value-format="yyyy-MM-dd" />
              </el-form-item>
            </el-col>
            <el-col :span="18">
              <el-form-item label="备注">
                <el-input v-model.trim="customerForm.remark" maxlength="500" />
              </el-form-item>
            </el-col>
            <el-col :span="6" class="form-actions">
              <el-button type="primary" icon="el-icon-plus" @click="submitCustomer">保存客户</el-button>
            </el-col>
          </el-row>
        </el-form>

        <el-table :data="customers" border stripe>
          <el-table-column prop="customer_no" label="客户编号" width="150" />
          <el-table-column prop="name" label="客户姓名" width="110" />
          <el-table-column prop="phone" label="手机号" width="125" />
          <el-table-column prop="store_name" label="门店" min-width="170" />
          <el-table-column prop="salesperson" label="业务员" width="110" />
          <el-table-column prop="source" label="客户来源" width="120" />
          <el-table-column prop="edc" label="预产期" width="110" />
          <el-table-column label="状态" width="150">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="录入时间" min-width="160" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="hasPermission('SALES.VIEW')" label="2 合同签订" name="contracts">
        <el-form
          v-if="hasPermission('SALES.CREATE')"
          ref="contractForm"
          :model="contractForm"
          :rules="contractRules"
          label-width="100px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="contractForm.storeId">
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择客户" prop="customerId">
                <el-select v-model="contractForm.customerId" filterable>
                  <el-option
                    v-for="customer in contractCustomers"
                    :key="customer.id"
                    :label="`${customer.name}（${customer.customer_no}）`"
                    :value="customer.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="合同类型" prop="contractType">
                <el-select v-model="contractForm.contractType">
                  <el-option v-for="type in options.contractTypes" :key="type" :label="type" :value="type" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="套餐名称">
                <el-input v-model.trim="contractForm.packageName" maxlength="100" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="参考价格" prop="referenceAmount">
                <el-input-number v-model="contractForm.referenceAmount" :min="0" :precision="2" :controls="false" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="成交金额" prop="amount">
                <el-input-number v-model="contractForm.amount" :min="0" :precision="2" :controls="false" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="折扣率">
                <el-input :value="discountRateText" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="入住天数" prop="days">
                <el-input-number v-model="contractForm.days" :min="1" :max="365" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="预住日期" prop="stayRange">
                <el-date-picker
                  v-model="contractForm.stayRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="预住日期"
                  end-placeholder="预离日期"
                  value-format="yyyy-MM-dd"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="签单日期">
                <el-date-picker v-model="contractForm.signDate" type="date" value-format="yyyy-MM-dd" />
              </el-form-item>
            </el-col>
            <el-col :span="8" class="form-actions">
              <el-button type="primary" icon="el-icon-plus" @click="submitContract">新增合同</el-button>
            </el-col>
          </el-row>
          <div class="formula-tip">
            <span>折扣率=成交金额/参考价格</span>
            <span>未入账金额=已收款未审核的金额</span>
          </div>
        </el-form>

        <el-table :data="contracts" border stripe>
          <el-table-column prop="contract_no" label="合同编号" width="175" />
          <el-table-column prop="customer_name" label="客户姓名" width="110" />
          <el-table-column prop="contract_type" label="合同类型" width="110" />
          <el-table-column prop="reference_amount" label="参考价格" width="105" align="right" />
          <el-table-column prop="amount" label="成交金额" width="105" align="right" />
          <el-table-column label="折扣率" width="90" align="right">
            <template slot-scope="{ row }">{{ formatPercent(row.discount_rate) }}</template>
          </el-table-column>
          <el-table-column prop="paid" label="已入账" width="95" align="right" />
          <el-table-column prop="unposted_amount" label="未入账" width="95" align="right" />
          <el-table-column prop="outstanding_amount" label="欠款" width="95" align="right" />
          <el-table-column label="状态" width="145">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template slot-scope="{ row }">
              <el-button
                v-if="row.status === '已签合同但未审核' && hasPermission('SALES.APPROVE')"
                type="text"
                @click="approveContract(row)"
              >审核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="hasPermission('FINANCE.VIEW')" label="3 收款审核" name="receipts">
        <el-form
          v-if="hasPermission('FINANCE.CREATE')"
          ref="receiptForm"
          :model="receiptForm"
          :rules="receiptRules"
          label-width="96px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="receiptForm.storeId">
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择合同" prop="contractId">
                <el-select v-model="receiptForm.contractId" filterable>
                  <el-option
                    v-for="contract in receiptContracts"
                    :key="contract.id"
                    :label="`${contract.customer_name}（${contract.contract_no}）`"
                    :value="contract.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="收款类型" prop="receiptType">
                <el-select v-model="receiptForm.receiptType">
                  <el-option v-for="type in options.receiptTypes" :key="type" :label="type" :value="type" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="收款金额" prop="amount">
                <el-input-number v-model="receiptForm.amount" :min="0" :precision="2" :controls="false" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="支付方式" prop="paymentMethod">
                <el-select v-model="receiptForm.paymentMethod">
                  <el-option v-for="method in options.paymentMethods" :key="method" :label="method" :value="method" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="收款时间">
                <el-date-picker
                  v-model="receiptForm.receivedAt"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="备注">
                <el-input v-model.trim="receiptForm.remark" maxlength="500" />
              </el-form-item>
            </el-col>
            <el-col :span="6" class="form-actions">
              <el-button type="primary" icon="el-icon-plus" @click="submitReceipt">登记收款</el-button>
            </el-col>
          </el-row>
        </el-form>

        <el-table :data="receipts" border stripe>
          <el-table-column prop="receipt_no" label="收款单号" width="175" />
          <el-table-column prop="customer_name" label="客户姓名" width="110" />
          <el-table-column prop="contract_no" label="合同编号" width="175" />
          <el-table-column prop="receipt_type" label="收款类型" width="120" />
          <el-table-column prop="amount" label="收款金额" width="110" align="right" />
          <el-table-column prop="payment_method" label="支付方式" width="95" />
          <el-table-column prop="receiver" label="收款人" width="100" />
          <el-table-column prop="received_at" label="收款时间" min-width="160" />
          <el-table-column label="状态" width="90">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template slot-scope="{ row }">
              <el-button
                v-if="row.status === '待审核' && hasPermission('FINANCE.APPROVE')"
                type="text"
                @click="approveReceipt(row)"
              >审核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="hasPermission('ROOM.VIEW')" label="4 订房入住" name="bookings">
        <el-form
          v-if="hasPermission('ROOM.CREATE')"
          ref="bookingForm"
          :model="bookingForm"
          :rules="bookingRules"
          label-width="92px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="bookingForm.storeId">
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择合同" prop="contractId">
                <el-select v-model="bookingForm.contractId" filterable>
                  <el-option
                    v-for="contract in bookingContracts"
                    :key="contract.id"
                    :label="`${contract.customer_name}（${contract.contract_no}）`"
                    :value="contract.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择房间" prop="roomId">
                <el-select v-model="bookingForm.roomId" filterable>
                  <el-option
                    v-for="room in bookingRooms"
                    :key="room.id"
                    :label="`${room.room_no}（${room.room_type} / ${room.status}）`"
                    :value="room.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="入住日期" prop="stayRange">
                <el-date-picker
                  v-model="bookingForm.stayRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="入住日期"
                  end-placeholder="离店日期"
                  value-format="yyyy-MM-dd"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24" class="form-actions">
              <el-button type="primary" icon="el-icon-plus" @click="submitBooking">办理订房</el-button>
            </el-col>
          </el-row>
        </el-form>

        <el-table :data="bookings" border stripe>
          <el-table-column prop="booking_no" label="订房单号" width="175" />
          <el-table-column prop="customer_name" label="客户姓名" width="110" />
          <el-table-column prop="contract_no" label="合同编号" width="175" />
          <el-table-column prop="store_name" label="门店" min-width="170" />
          <el-table-column prop="room_no" label="房间号" width="90" />
          <el-table-column prop="check_in" label="入住日期" width="110" />
          <el-table-column prop="check_out" label="离店日期" width="110" />
          <el-table-column label="状态" width="90">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="actual_check_in_at" label="实际入住时间" min-width="160" />
          <el-table-column label="操作" width="100" fixed="right">
            <template slot-scope="{ row }">
              <el-button
                v-if="row.status === '已订房' && hasPermission('ROOM.EXECUTE')"
                type="text"
                @click="checkIn(row)"
              >办理入住</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import {
  getMvpOptions,
  getMvpOverview,
  getMvpList,
  createMvpRecord,
  performMvpAction
} from '@/api/erp-mvp'

function today() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}

function nowText() {
  const now = new Date()
  const pad = value => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

export default {
  name: 'MvpWorkbench',
  data() {
    return {
      loading: false,
      activeTab: 'customers',
      overview: {},
      options: {
        stores: [],
        staff: [],
        contractTypes: [],
        receiptTypes: [],
        paymentMethods: [],
        permissions: [],
        roles: [],
        bookingContracts: []
      },
      customers: [],
      contracts: [],
      receipts: [],
      rooms: [],
      bookings: [],
      summaryCards: [
        { key: 'customers', label: '客户数', permission: 'CUSTOMER.VIEW' },
        { key: 'contracts', label: '合同数', permission: 'SALES.VIEW' },
        { key: 'pendingContracts', label: '待审合同', permission: 'SALES.VIEW' },
        { key: 'pendingReceipts', label: '待审收款', permission: 'FINANCE.VIEW' },
        { key: 'bookings', label: '订房/入住', permission: 'ROOM.VIEW' }
      ],
      customerStatuses: ['意向A', '意向B', '意向C', '意向D', '意向E', '流失客户', '散客客户', '同意签合同'],
      customerForm: {
        storeId: '',
        name: '',
        phone: '',
        wechat: '',
        status: '意向A',
        source: '',
        salesStaffId: '',
        edc: '',
        remark: ''
      },
      contractForm: {
        storeId: '',
        customerId: '',
        contractType: '月子合同',
        packageName: '',
        referenceAmount: 0,
        amount: 0,
        days: 28,
        stayRange: [],
        signDate: today()
      },
      receiptForm: {
        storeId: '',
        contractId: '',
        receiptType: '合同首付',
        amount: 0,
        paymentMethod: '转账',
        receivedAt: nowText(),
        remark: ''
      },
      bookingForm: {
        storeId: '',
        contractId: '',
        roomId: '',
        stayRange: []
      },
      customerRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
        ]
      },
      contractRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        customerId: [{ required: true, message: '请选择客户', trigger: 'change' }],
        contractType: [{ required: true, message: '请选择合同类型', trigger: 'change' }],
        referenceAmount: [{ required: true, type: 'number', min: 0.01, message: '请输入参考价格', trigger: 'blur' }],
        amount: [{ required: true, type: 'number', min: 0.01, message: '请输入成交金额', trigger: 'blur' }],
        days: [{ required: true, type: 'number', min: 1, message: '请输入入住天数', trigger: 'blur' }],
        stayRange: [{ required: true, type: 'array', min: 2, message: '请选择预住日期', trigger: 'change' }]
      },
      receiptRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        contractId: [{ required: true, message: '请选择合同', trigger: 'change' }],
        receiptType: [{ required: true, message: '请选择收款类型', trigger: 'change' }],
        amount: [{ required: true, type: 'number', min: 0.01, message: '请输入收款金额', trigger: 'blur' }],
        paymentMethod: [{ required: true, message: '请选择支付方式', trigger: 'change' }]
      },
      bookingRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        contractId: [{ required: true, message: '请选择已审核合同', trigger: 'change' }],
        roomId: [{ required: true, message: '请选择房间', trigger: 'change' }],
        stayRange: [{ required: true, type: 'array', min: 2, message: '请选择入住日期', trigger: 'change' }]
      }
    }
  },
  computed: {
    visibleSummaryCards() {
      return this.summaryCards.filter(item => this.hasPermission(item.permission))
    },
    customerStaff() {
      return this.options.staff.filter(item => !this.customerForm.storeId || Number(item.store_id) === Number(this.customerForm.storeId))
    },
    contractCustomers() {
      return this.customers.filter(item => !this.contractForm.storeId || Number(item.store_id) === Number(this.contractForm.storeId))
    },
    receiptContracts() {
      return this.contracts.filter(item => !this.receiptForm.storeId || Number(item.store_id) === Number(this.receiptForm.storeId))
    },
    bookingContracts() {
      return this.options.bookingContracts.filter(item => !this.bookingForm.storeId || Number(item.store_id) === Number(this.bookingForm.storeId))
    },
    bookingRooms() {
      return this.rooms.filter(item => !this.bookingForm.storeId || Number(item.store_id) === Number(this.bookingForm.storeId))
    },
    discountRateText() {
      if (!this.contractForm.referenceAmount) return '0.00%'
      return `${(this.contractForm.amount / this.contractForm.referenceAmount * 100).toFixed(2)}%`
    }
  },
  created() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      this.loading = true
      try {
        const options = await getMvpOptions()
        this.options = options.data
        const emptyList = () => Promise.resolve({ data: { list: [], total: 0 }})
        const [overview, customers, contracts, receipts, rooms, bookings] = await Promise.all([
          getMvpOverview(),
          this.hasPermission('CUSTOMER.VIEW') ? getMvpList('customers') : emptyList(),
          this.hasPermission('SALES.VIEW') ? getMvpList('contracts') : emptyList(),
          this.hasPermission('FINANCE.VIEW') ? getMvpList('receipts') : emptyList(),
          this.hasPermission('ROOM.VIEW') ? getMvpList('rooms') : emptyList(),
          this.hasPermission('ROOM.VIEW') ? getMvpList('bookings') : emptyList()
        ])
        this.overview = overview.data
        this.customers = customers.data.list
        this.contracts = contracts.data.list
        this.receipts = receipts.data.list
        this.rooms = rooms.data.list
        this.bookings = bookings.data.list
        this.applyDefaultStores()
        this.ensureActiveTab()
      } finally {
        this.loading = false
      }
    },
    ensureActiveTab() {
      const tabs = [
        { name: 'customers', permission: 'CUSTOMER.VIEW' },
        { name: 'contracts', permission: 'SALES.VIEW' },
        { name: 'receipts', permission: 'FINANCE.VIEW' },
        { name: 'bookings', permission: 'ROOM.VIEW' }
      ]
      const allowed = tabs.filter(item => this.hasPermission(item.permission))
      if (!allowed.some(item => item.name === this.activeTab) && allowed.length) {
        this.activeTab = allowed[0].name
      }
    },
    hasPermission(permission) {
      return this.options.permissions.includes(permission)
    },
    applyDefaultStores() {
      if (!this.options.stores.length) return
      const defaultStore = this.options.stores[0].id
      const formKeys = ['customerForm', 'contractForm', 'receiptForm', 'bookingForm']
      formKeys.forEach(key => {
        if (!this[key].storeId) this[key].storeId = defaultStore
      })
    },
    validate(ref) {
      return new Promise(resolve => this.$refs[ref].validate(valid => resolve(valid)))
    },
    async submitCustomer() {
      if (!await this.validate('customerForm')) return
      await createMvpRecord('customers', this.customerForm)
      this.$message.success('客户已保存')
      const storeId = this.customerForm.storeId
      Object.assign(this.customerForm, { storeId, name: '', phone: '', wechat: '', status: '意向A', source: '', salesStaffId: '', edc: '', remark: '' })
      this.$refs.customerForm.clearValidate()
      await this.loadAll()
    },
    async submitContract() {
      if (!await this.validate('contractForm')) return
      if (this.contractForm.amount > this.contractForm.referenceAmount) {
        return this.$message.warning('成交金额不能大于参考价格')
      }
      await createMvpRecord('contracts', {
        ...this.contractForm,
        expectedCheckIn: this.contractForm.stayRange[0],
        expectedCheckOut: this.contractForm.stayRange[1]
      })
      this.$message.success('合同已保存，等待审核')
      await this.loadAll()
    },
    async approveContract(row) {
      await this.$confirm(`确认审核合同 ${row.contract_no}？`, '合同审核', { type: 'warning' })
      await performMvpAction('contracts', row.id, 'approve')
      this.$message.success('合同审核完成')
      await this.loadAll()
    },
    async submitReceipt() {
      if (!await this.validate('receiptForm')) return
      await createMvpRecord('receipts', this.receiptForm)
      this.$message.success('收款已登记，等待审核')
      await this.loadAll()
    },
    async approveReceipt(row) {
      await this.$confirm(`确认审核收款单 ${row.receipt_no}？`, '收款审核', { type: 'warning' })
      await performMvpAction('receipts', row.id, 'approve')
      this.$message.success('收款审核完成，合同已入账')
      await this.loadAll()
    },
    async submitBooking() {
      if (!await this.validate('bookingForm')) return
      await createMvpRecord('bookings', {
        ...this.bookingForm,
        checkIn: this.bookingForm.stayRange[0],
        checkOut: this.bookingForm.stayRange[1]
      })
      this.$message.success('订房办理完成')
      await this.loadAll()
    },
    async checkIn(row) {
      await this.$confirm(`确认客户 ${row.customer_name} 入住 ${row.room_no} 房？`, '办理入住', { type: 'warning' })
      await performMvpAction('bookings', row.id, 'check-in')
      this.$message.success('入住办理完成，房态已更新')
      await this.loadAll()
    },
    formatPercent(value) {
      return `${(Number(value || 0) * 100).toFixed(2)}%`
    }
  }
}
</script>

<style lang="scss" scoped>
.mvp-page {
  min-height: calc(100vh - 84px);
  padding: 16px;
  background: #f4f1ea;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.summary-card {
  padding: 14px 16px;
  border: 1px solid #ded0b4;
  border-radius: 4px;
  background: #fffdf8;
}

.summary-label {
  color: #7d6c52;
  font-size: 13px;
}

.summary-value {
  margin-top: 6px;
  color: #6e4f20;
  font-size: 28px;
  font-weight: 600;
}

.business-tabs {
  margin-top: 12px;
  padding: 0 16px 16px;
  border: 1px solid #ded0b4;
  background: #fff;
}

.business-form {
  margin-bottom: 14px;
  padding: 14px 12px 2px;
  background: #faf7f0;

  ::v-deep .el-select,
  ::v-deep .el-date-editor,
  ::v-deep .el-input-number {
    width: 100%;
  }
}

.form-actions {
  padding-bottom: 16px;
  text-align: right;
}

.formula-tip {
  display: flex;
  gap: 28px;
  padding: 0 0 12px 100px;
  color: #9b6b20;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .summary-row {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
