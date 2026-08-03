<template>
  <div v-loading="loading" class="asset-page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">MEMBER ASSET MANAGEMENT</span>
        <h2>会员资产中心</h2>
        <p>统一管理套餐卡、次卡、储值卡和会员余额，支持发卡、核销、充值与扣款。</p>
      </div>
      <div class="heading-actions">
        <el-button size="small" icon="el-icon-back" @click="$router.push('/mvp/workbench')">返回客户签约</el-button>
        <el-button size="small" icon="el-icon-refresh" :loading="loading" @click="loadAll">刷新数据</el-button>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      :closable="false"
      show-icon
      class="load-error"
    />

    <div class="summary-grid">
      <div v-for="item in summaryCards" :key="item.key" class="summary-card">
        <i :class="item.icon" :style="{ color: item.color, background: item.background }" />
        <div>
          <span>{{ item.label }}</span>
          <b>{{ overview[item.key] || 0 }}</b>
          <small>{{ item.hint }}</small>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="asset-tabs">
      <el-tab-pane label="套餐卡 / 次卡" name="cards">
        <div class="tab-toolbar">
          <div>
            <h3>客户卡资产</h3>
            <p>发卡后可直接核销次数或扣减储值余额。</p>
          </div>
          <el-button type="primary" icon="el-icon-bank-card" @click="openCardDialog">新建发卡</el-button>
        </div>

        <el-table :data="cards" border stripe empty-text="暂无卡资产，请点击“新建发卡”">
          <el-table-column prop="card_no" label="卡号" min-width="145" />
          <el-table-column prop="customer_name" label="客户" min-width="100" />
          <el-table-column prop="card_name" label="卡名称" min-width="160" />
          <el-table-column prop="card_type" label="卡类型" min-width="90">
            <template slot-scope="{ row }">
              <el-tag size="mini" :type="row.card_type === '储值卡' ? 'warning' : 'primary'">{{ row.card_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="可用资产" min-width="130">
            <template slot-scope="{ row }">
              <span v-if="row.card_type === '储值卡'">¥ {{ money(row.balance) }}</span>
              <span v-else>{{ row.remaining_count }} / {{ row.total_count }} 次</span>
            </template>
          </el-table-column>
          <el-table-column prop="valid_to" label="有效期至" min-width="110" />
          <el-table-column prop="status" label="状态" min-width="90">
            <template slot-scope="{ row }">
              <el-tag size="mini" :type="statusType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="150">
            <template slot-scope="{ row }">
              <el-button
                type="text"
                :loading="actionKey === `cards-${row.id}-consume`"
                :disabled="row.status !== '正常' || !cardCanConsume(row)"
                @click="consumeCard(row)"
              >
                {{ row.card_type === '储值卡' ? '余额扣款' : '核销一次' }}
              </el-button>
              <el-button type="text" @click="showCardDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="余额资产" name="accounts">
        <div class="tab-toolbar">
          <div>
            <h3>客户余额账户</h3>
            <p>账户充值和消费即时反映到可用余额。</p>
          </div>
        </div>

        <el-table :data="accounts" border stripe empty-text="暂无余额账户">
          <el-table-column prop="account_no" label="账户编号" min-width="145" />
          <el-table-column prop="customer_name" label="客户" min-width="110" />
          <el-table-column prop="mobile" label="手机号" min-width="125" />
          <el-table-column prop="store_name" label="门店" min-width="150" />
          <el-table-column label="可用余额" min-width="120">
            <template slot-scope="{ row }"><b class="money">¥ {{ money(row.balance) }}</b></template>
          </el-table-column>
          <el-table-column label="冻结金额" min-width="105">
            <template slot-scope="{ row }">¥ {{ money(row.frozen_amount) }}</template>
          </el-table-column>
          <el-table-column prop="points" label="积分" min-width="90" />
          <el-table-column prop="status" label="状态" min-width="90">
            <template slot-scope="{ row }">
              <el-tag size="mini" :type="statusType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="145">
            <template slot-scope="{ row }">
              <el-button type="text" @click="openMoneyDialog('top-up', row)">充值</el-button>
              <el-button type="text" :disabled="Number(row.balance) <= 0" @click="openMoneyDialog('deduct', row)">扣款</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="integrationPreviewEnabled" label="支付配置" name="payments">
        <div class="tab-toolbar">
          <div>
            <h3>支付通道</h3>
            <p>统一维护支付通道、商户信息和启用状态。</p>
          </div>
        </div>

        <el-alert
          title="支付密钥仅允许保存在服务器安全配置中，不在页面或业务数据中展示。"
          type="warning"
          :closable="false"
          show-icon
          class="inline-alert"
        />

        <el-table :data="payments" border stripe>
          <el-table-column prop="config_name" label="配置名称" min-width="150" />
          <el-table-column prop="channel" label="支付通道" min-width="110" />
          <el-table-column prop="merchant_no" label="商户号" min-width="150" />
          <el-table-column prop="fee_rate" label="费率" min-width="85">
            <template slot-scope="{ row }">{{ row.fee_rate }}%</template>
          </el-table-column>
          <el-table-column prop="test_status" label="通道测试" min-width="105">
            <template slot-scope="{ row }">
              <el-tag size="mini" :type="statusType(row.test_status)">{{ row.test_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="启用状态" min-width="95">
            <template slot-scope="{ row }">
              <el-tag size="mini" :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '已启用' : '已停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" min-width="150" />
          <el-table-column label="操作" fixed="right" width="150">
            <template slot-scope="{ row }">
              <el-button
                type="text"
                :loading="actionKey === `payments-${row.id}-test`"
                @click="runAction('payments', row, 'test', {}, '通道测试通过')"
              >测试</el-button>
              <el-button
                type="text"
                :loading="actionKey === `payments-${row.id}-toggle`"
                @click="runAction('payments', row, 'toggle', {}, row.enabled ? '支付通道已停用' : '支付通道已启用')"
              >{{ row.enabled ? '停用' : '启用' }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="integrationPreviewEnabled" label="消息中心" name="messages">
        <div class="tab-toolbar">
          <div>
            <h3>客户消息任务</h3>
            <p>统一创建、发送、取消或重试客户消息任务。</p>
          </div>
          <el-button type="primary" icon="el-icon-message" @click="openMessageDialog">新建消息</el-button>
        </div>

        <el-table :data="messages" border stripe empty-text="暂无消息任务">
          <el-table-column prop="message_no" label="任务编号" min-width="145" />
          <el-table-column prop="customer_name" label="客户" min-width="100" />
          <el-table-column prop="message_title" label="消息标题" min-width="180" />
          <el-table-column prop="channel" label="渠道" min-width="90" />
          <el-table-column prop="planned_at" label="计划发送" min-width="150" />
          <el-table-column prop="sent_at" label="实际发送" min-width="150" />
          <el-table-column prop="send_status" label="状态" min-width="95">
            <template slot-scope="{ row }">
              <el-tag size="mini" :type="statusType(row.send_status)">{{ row.send_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="retry_count" label="重试" min-width="70" />
          <el-table-column label="操作" fixed="right" width="180">
            <template slot-scope="{ row }">
              <el-button
                v-if="row.send_status === '待发送'"
                type="text"
                :loading="actionKey === `messages-${row.id}-send`"
                @click="runAction('messages', row, 'send', {}, '消息任务已发送')"
              >立即发送</el-button>
              <el-button
                v-if="row.send_status === '待发送'"
                type="text"
                @click="runAction('messages', row, 'cancel', {}, '消息任务已取消')"
              >取消</el-button>
              <el-button
                v-if="row.send_status === '发送失败'"
                type="text"
                :loading="actionKey === `messages-${row.id}-retry`"
                @click="runAction('messages', row, 'retry', {}, '消息重试成功')"
              >重新发送</el-button>
              <el-button type="text" @click="showMessage(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog title="新建发卡" :visible.sync="cardDialogVisible" width="560px" @closed="resetCardForm">
      <el-form ref="cardForm" :model="cardForm" :rules="cardRules" label-width="105px">
        <el-form-item label="客户" prop="customerId">
          <el-select v-model="cardForm.customerId" filterable placeholder="请选择客户">
            <el-option v-for="item in options.customers" :key="item.id" :label="`${item.name} · ${item.phone}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="卡名称" prop="cardName">
          <el-input v-model.trim="cardForm.cardName" maxlength="128" placeholder="例如：12 次产后修复卡" />
        </el-form-item>
        <el-form-item label="卡类型" prop="cardType">
          <el-radio-group v-model="cardForm.cardType">
            <el-radio v-for="item in options.cardTypes" :key="item" :label="item">{{ item }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="售卡金额" prop="amount">
          <el-input-number v-model="cardForm.amount" :min="0" :precision="2" :step="100" />
        </el-form-item>
        <el-form-item v-if="cardForm.cardType !== '储值卡'" label="总次数" prop="totalCount">
          <el-input-number v-model="cardForm.totalCount" :min="1" :step="1" />
        </el-form-item>
        <el-form-item label="有效期至" prop="validTo">
          <el-date-picker v-model="cardForm.validTo" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="cardDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCard">确认发卡</el-button>
      </div>
    </el-dialog>

    <el-dialog :title="moneyDialogTitle" :visible.sync="moneyDialogVisible" width="460px">
      <el-form label-width="100px">
        <el-form-item label="操作对象"><b>{{ moneyTargetLabel }}</b></el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="moneyAmount" :min="0.01" :precision="2" :step="100" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="moneyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMoneyAction">确认</el-button>
      </div>
    </el-dialog>

    <el-dialog title="新建客户消息" :visible.sync="messageDialogVisible" width="580px" @closed="resetMessageForm">
      <el-form ref="messageForm" :model="messageForm" :rules="messageRules" label-width="100px">
        <el-form-item label="客户" prop="customerId">
          <el-select v-model="messageForm.customerId" filterable placeholder="请选择客户">
            <el-option v-for="item in options.customers" :key="item.id" :label="`${item.name} · ${item.phone}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息标题" prop="messageTitle">
          <el-input v-model.trim="messageForm.messageTitle" maxlength="50" />
        </el-form-item>
        <el-form-item label="发送渠道" prop="channel">
          <el-radio-group v-model="messageForm.channel">
            <el-radio v-for="item in options.messageChannels" :key="item" :label="item">{{ item }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="计划发送" prop="plannedAt">
          <el-date-picker v-model="messageForm.plannedAt" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" placeholder="选择发送时间" />
        </el-form-item>
        <el-form-item label="消息内容" prop="content">
          <el-input v-model.trim="messageForm.content" type="textarea" :rows="4" maxlength="300" show-word-limit />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="messageDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMessage">保存任务</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  createAssetCard,
  createAssetRecord,
  getAssetList,
  getAssetOptions,
  getAssetOverview,
  performAssetAction
} from '@/api/erp-assets'
import { mapGetters } from 'vuex'

export default {
  name: 'AssetWorkbench',
  data() {
    return {
      loading: false,
      submitting: false,
      loadError: '',
      actionKey: '',
      activeTab: 'accounts',
      integrationPreviewEnabled: process.env.VUE_APP_ENABLE_INTEGRATION_PREVIEW === 'true',
      overview: {},
      options: {
        customers: [],
        cardTypes: [],
        cardPackages: [],
        messageChannels: []
      },
      cards: [],
      accounts: [],
      payments: [],
      messages: [],
      cardDialogVisible: false,
      moneyDialogVisible: false,
      messageDialogVisible: false,
      moneyMode: '',
      moneyTarget: null,
      moneyAmount: 1000,
      cardForm: {
        customerId: '',
        cardName: '',
        cardType: '次卡',
        amount: 0,
        totalCount: 12,
        validTo: '2027-07-29'
      },
      messageForm: {
        customerId: '',
        messageTitle: '',
        channel: '站内消息',
        plannedAt: '2026-07-29 10:00:00',
        content: ''
      },
      cardRules: {
        customerId: [{ required: true, message: '请选择客户', trigger: 'change' }],
        cardName: [{ required: true, message: '请输入卡名称', trigger: 'blur' }],
        cardType: [{ required: true, message: '请选择卡类型', trigger: 'change' }],
        amount: [{ required: true, message: '请输入售卡金额', trigger: 'blur' }],
        totalCount: [{ required: true, message: '请输入总次数', trigger: 'blur' }],
        validTo: [{ required: true, message: '请选择有效期', trigger: 'change' }]
      },
      messageRules: {
        customerId: [{ required: true, message: '请选择客户', trigger: 'change' }],
        messageTitle: [{ required: true, message: '请输入消息标题', trigger: 'blur' }],
        channel: [{ required: true, message: '请选择发送渠道', trigger: 'change' }],
        plannedAt: [{ required: true, message: '请选择发送时间', trigger: 'change' }],
        content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }]
      }
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    hasConcreteStore() { return this.currentStoreId && String(this.currentStoreId) !== 'all' },
    summaryCards() {
      const cards = [
        { key: 'activeCards', label: '有效卡资产', hint: '套餐卡 / 次卡 / 储值卡', icon: 'el-icon-bank-card', color: '#5b7cfa', background: '#edf1ff' },
        { key: 'accountBalance', label: '客户余额', hint: '可用余额合计（元）', icon: 'el-icon-wallet', color: '#f29b38', background: '#fff4e7' }
      ]
      if (this.integrationPreviewEnabled) {
        cards.push(
          { key: 'enabledPayments', label: '启用通道', hint: '支付通道配置', icon: 'el-icon-coin', color: '#2baa82', background: '#e9f8f3' },
          { key: 'pendingMessages', label: '待发消息', hint: '计划任务', icon: 'el-icon-message', color: '#d85c83', background: '#fdeef3' }
        )
      }
      return cards
    },
    moneyDialogTitle() {
      if (this.moneyMode === 'top-up') return '余额充值'
      if (this.moneyMode === 'deduct') return '余额扣款'
      return '储值卡扣款'
    },
    moneyTargetLabel() {
      if (!this.moneyTarget) return ''
      return this.moneyTarget.customer_name || this.moneyTarget.card_name || ''
    }
  },
  watch: {
    currentStoreId() { this.loadAll() }
  },
  created() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      this.loading = true
      this.loadError = ''
      try {
        const params = { storeId: this.currentStoreId || 'all' }
        const [options, overview, cards, accounts] = await Promise.all([
          getAssetOptions(params),
          getAssetOverview(params),
          getAssetList('cards', params),
          getAssetList('accounts', params)
        ])
        this.options = options.data || this.options
        this.overview = overview.data || {}
        this.cards = (cards.data && cards.data.list) || []
        this.accounts = (accounts.data && accounts.data.list) || []
        this.payments = []
        this.messages = []
      } catch (error) {
        this.loadError = (error && error.message) || '资产中心数据加载失败，请联系系统管理员'
      } finally {
        this.loading = false
      }
    },
    money(value) {
      return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    statusType(status) {
      if (['正常', '已启用', '已完成', '已通过', '测试通过', '已发送'].includes(status)) return 'success'
      if (['待发送', '待配置', '未测试'].includes(status)) return 'warning'
      if (['发送失败', '已停用', '已冻结'].includes(status)) return 'danger'
      return 'info'
    },
    cardCanConsume(row) {
      return row.card_type === '储值卡' ? Number(row.balance) > 0 : Number(row.remaining_count) > 0
    },
    openCardDialog() {
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再发卡')
      this.cardDialogVisible = true
    },
    applyPackagePreset(packageId) {
      const preset = this.options.cardPackages.find(item => Number(item.id) === Number(packageId))
      if (!preset) return
      this.cardForm.cardType = preset.cardType
      this.cardForm.amount = preset.amount
      this.cardForm.totalCount = preset.totalCount
    },
    resetCardForm() {
      this.cardForm = {
        customerId: '',
        cardName: '',
        cardType: '次卡',
        amount: 0,
        totalCount: 12,
        validTo: '2027-07-29'
      }
      if (this.$refs.cardForm) this.$refs.cardForm.clearValidate()
    },
    submitCard() {
      this.$refs.cardForm.validate(async valid => {
        if (!valid) return
        this.submitting = true
        try {
          if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再发卡')
          await createAssetCard({ ...this.cardForm, selectedStoreId: this.currentStoreId })
          this.cardDialogVisible = false
          this.$message.success('发卡成功，客户资产已更新')
          await this.loadAll()
        } finally {
          this.submitting = false
        }
      })
    },
    consumeCard(row) {
      if (row.card_type === '储值卡') {
        this.openMoneyDialog('card-consume', row)
        return
      }
      this.$confirm(`确认核销 ${row.customer_name} 的 ${row.card_name} 1 次？`, '次卡核销', {
        confirmButtonText: '确认核销',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => this.runAction('cards', row, 'consume', { count: 1 }, '核销成功，剩余次数已更新')).catch(() => {})
    },
    showCardDetail(row) {
      const asset = row.card_type === '储值卡'
        ? `可用余额 ¥${this.money(row.balance)}`
        : `剩余 ${row.remaining_count}/${row.total_count} 次`
      this.$alert(`${row.customer_name} · ${row.card_name}<br>${asset}<br>有效期至 ${row.valid_to}`, '卡资产详情', {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '知道了'
      })
    },
    openMoneyDialog(mode, row) {
      this.moneyMode = mode
      this.moneyTarget = row
      this.moneyAmount = mode === 'card-consume' ? 100 : 1000
      this.moneyDialogVisible = true
    },
    async submitMoneyAction() {
      if (!this.moneyTarget || Number(this.moneyAmount) <= 0) return this.$message.warning('请输入有效金额')
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再办理交易')
      this.submitting = true
      try {
        const resource = this.moneyMode === 'card-consume' ? 'cards' : 'accounts'
        const action = this.moneyMode === 'card-consume'
          ? 'consume'
          : this.moneyMode === 'top-up' ? 'top-up' : 'deduct'
        await performAssetAction(resource, this.moneyTarget.id, action, { amount: Number(this.moneyAmount), selectedStoreId: this.currentStoreId })
        this.moneyDialogVisible = false
        this.$message.success(this.moneyMode === 'top-up' ? '充值成功，余额已更新' : '扣款成功，余额已更新')
        await this.loadAll()
      } finally {
        this.submitting = false
      }
    },
    openMessageDialog() {
      this.messageDialogVisible = true
    },
    resetMessageForm() {
      this.messageForm = {
        customerId: '',
        messageTitle: '',
        channel: '站内消息',
        plannedAt: '2026-07-29 10:00:00',
        content: ''
      }
      if (this.$refs.messageForm) this.$refs.messageForm.clearValidate()
    },
    submitMessage() {
      this.$refs.messageForm.validate(async valid => {
        if (!valid) return
        this.submitting = true
        try {
          await createAssetRecord('messages', this.messageForm)
          this.messageDialogVisible = false
          this.$message.success('消息任务已创建')
          await this.loadAll()
        } finally {
          this.submitting = false
        }
      })
    },
    showMessage(row) {
      this.$alert(row.content, row.message_title, {
        confirmButtonText: '关闭',
        callback: () => {}
      })
    },
    async runAction(resource, row, action, data, message) {
      if (!this.hasConcreteStore) return this.$message.warning('全部门店仅支持汇总查询，请先选择具体门店再操作')
      const key = `${resource}-${row.id}-${action}`
      this.actionKey = key
      try {
        await performAssetAction(resource, row.id, action, { ...data, selectedStoreId: this.currentStoreId })
        this.$message.success(message)
        await this.loadAll()
      } finally {
        if (this.actionKey === key) this.actionKey = ''
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-page {
  min-height: calc(100vh - 84px);
  padding: 24px;
  background: #f4f6f9;
  color: #263445;
}
.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}
.page-heading h2 { margin: 5px 0 7px; font-size: 25px; }
.page-heading p, .tab-toolbar p { margin: 0; color: #8a96a8; font-size: 13px; }
.eyebrow { color: #5576ea; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
.heading-actions { display: flex; align-items: center; gap: 8px; }
.load-error, .inline-alert { margin-bottom: 16px; }
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}
.summary-card {
  display: flex;
  align-items: center;
  min-height: 108px;
  padding: 18px 20px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(27, 45, 75, .055);
}
.summary-card i {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin-right: 15px;
  border-radius: 12px;
  font-size: 22px;
}
.summary-card div { display: flex; flex-direction: column; }
.summary-card span { color: #718096; font-size: 13px; }
.summary-card b { margin: 3px 0; color: #253247; font-size: 27px; }
.summary-card small { color: #a0a9b6; }
.asset-tabs {
  border: 0;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(27, 45, 75, .055);
}
.tab-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.tab-toolbar h3 { margin: 0 0 4px; font-size: 17px; }
.money { color: #e18b27; }
::v-deep .el-tabs__content { padding: 20px; }
::v-deep .el-table th { background: #f7f9fc; color: #56657a; }
::v-deep .el-dialog { border-radius: 10px; }
::v-deep .el-form .el-select,
::v-deep .el-form .el-date-editor { width: 100%; }
@media (max-width: 1000px) {
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
  .page-heading { align-items: flex-start; }
  .heading-actions { flex-wrap: wrap; justify-content: flex-end; }
}
@media (max-width: 640px) {
  .asset-page { padding: 14px; }
  .page-heading { flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
  .summary-grid { grid-template-columns: 1fr; }
}
</style>
