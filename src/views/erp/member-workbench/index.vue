<template>
  <div v-loading="loading" class="member-workbench">
    <section class="page-heading">
      <div>
        <div class="eyebrow">会员管理 · {{ definition.featureId }}</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ definition.description }}</p>
      </div>
      <div class="heading-actions">
        <el-button icon="el-icon-refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button icon="el-icon-download" :disabled="!filteredRows.length" @click="exportRows">导出当前结果</el-button>
        <el-button v-if="definition.assetEntry" type="primary" @click="openAssetCenter">进入会员资产中心</el-button>
      </div>
    </section>

    <el-alert
      v-if="definition.notice"
      class="notice"
      type="info"
      :closable="false"
      show-icon
      :title="definition.notice"
    />
    <el-alert v-if="loadError" class="notice" type="warning" :closable="false" show-icon :title="loadError" />

    <section class="metric-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>{{ metric.note }}</small>
      </article>
    </section>

    <el-card shadow="never" class="content-card">
      <div slot="header" class="card-heading">
        <div>
          <h2>{{ definition.tableTitle }}</h2>
          <p>{{ definition.tableHint }}</p>
        </div>
        <el-tag size="small" effect="plain">当前门店范围：{{ storeScopeLabel }}</el-tag>
      </div>

      <el-form inline size="small" class="filter-form" @submit.native.prevent="applyFilters">
        <el-form-item v-for="filter in definition.filters" :key="filter.key" :label="filter.label">
          <el-input
            v-if="filter.type === 'input'"
            v-model.trim="filters[filter.key]"
            clearable
            :placeholder="filter.placeholder || `请输入${filter.label}`"
            @keyup.enter.native="applyFilters"
          />
          <el-select v-else v-model="filters[filter.key]" clearable :placeholder="`请选择${filter.label}`">
            <el-option v-for="option in filter.options" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" icon="el-icon-search" @click="applyFilters">查询</el-button></el-form-item>
        <el-form-item><el-button @click="resetFilters">重置</el-button></el-form-item>
      </el-form>

      <el-table :data="filteredRows" border stripe size="small" class="data-table" :empty-text="definition.emptyText">
        <el-table-column
          v-for="column in definition.columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :min-width="column.width || 120"
          show-overflow-tooltip
        >
          <template slot-scope="scope">
            <el-tag v-if="column.format === 'status'" size="mini" :type="statusType(scope.row[column.key])">{{ scope.row[column.key] || '暂无数据' }}</el-tag>
            <span v-else-if="column.format === 'money'">¥{{ money(scope.row[column.key]) }}</span>
            <span v-else>{{ displayValue(scope.row[column.key]) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!filteredRows.length" class="empty-state">{{ definition.emptyText }}</div>
    </el-card>
  </div>
</template>

<script>
import { getAssetList } from '@/api/erp-assets'
import { mapGetters } from 'vuex'

const input = (key, label, placeholder = '') => ({ key, label, type: 'input', placeholder })
const select = (key, label, options) => ({ key, label, type: 'select', options })

const pageDefinitionByTitle = {
  '会员来源分析': {
    featureId: 'F006',
    description: '查看已建立会员资产关联的客户主档，并识别尚未补录来源归因的会员。',
    notice: '会员来源字段需要由客户主档提供；当前未配置来源归因数据时，只显示真实关联会员并标记“暂无来源记录”。',
    tableTitle: '会员主档与来源归因',
    tableHint: '会员主档跨门店查询；来源归因缺失不会被编造成示例数据。',
    emptyText: '暂无会员主档数据。发卡或建立余额账户后会显示关联客户。',
    filters: [input('keyword', '姓名/手机号/账户号'), select('status', '资产状态', ['正常', '停用'])],
    columns: [
      { key: 'memberNo', label: '会员关联号', width: 160 }, { key: 'memberName', label: '会员姓名', width: 120 },
      { key: 'mobile', label: '手机号', width: 140 }, { key: 'source', label: '来源归因', width: 150 },
      { key: 'storeName', label: '发生门店', width: 160 }, { key: 'status', label: '状态', format: 'status', width: 90 }
    ]
  },
  '充值与优惠券': {
    featureId: 'F008',
    description: '会员充值、扣款与卡资产由会员资产中心处理；本页仅汇总真实账户与卡资产。',
    notice: '优惠券业务规则尚未配置，当前不展示券码或交易流水。可进入会员资产中心办理发卡、充值和扣款。',
    tableTitle: '会员资产概览',
    tableHint: '展示当前权限范围内的真实储值账户和次卡/储值卡。',
    emptyText: '暂无会员资产数据。请先在会员资产中心办理发卡或充值。',
    assetEntry: true,
    filters: [input('keyword', '会员/卡号/账户号'), select('assetType', '资产类型', ['储值卡', '次卡', '余额账户'])],
    columns: [
      { key: 'assetNo', label: '资产编号', width: 170 }, { key: 'memberName', label: '会员', width: 120 },
      { key: 'assetType', label: '资产类型', width: 100 }, { key: 'available', label: '可用资产', width: 120 },
      { key: 'storeName', label: '发生门店', width: 160 }, { key: 'status', label: '状态', format: 'status', width: 90 }
    ]
  },
  '积分体系': {
    featureId: 'F040',
    description: '按真实会员账户展示积分余额；积分规则和兑换规则未配置时保持为空。',
    notice: '当前可查询账户积分余额。积分规则、兑换目录与审批流程配置完成后可登记。',
    tableTitle: '会员积分账户',
    tableHint: '积分余额来自会员资产账户；规则配置数量为 0 时表示尚未接入规则数据。',
    emptyText: '暂无积分账户数据。建立会员资产账户后会显示积分余额。',
    filters: [input('keyword', '会员/账户号'), select('pointsScope', '积分范围', ['有积分', '零积分'])],
    columns: [
      { key: 'accountNo', label: '账户编号', width: 170 }, { key: 'memberName', label: '会员', width: 120 },
      { key: 'points', label: '当前积分', width: 110 }, { key: 'balance', label: '账户余额', format: 'money', width: 120 },
      { key: 'storeName', label: '账户门店', width: 160 }, { key: 'status', label: '状态', format: 'status', width: 90 }
    ]
  },
  '次卡价值分析': {
    featureId: 'F060',
    description: '基于真实次卡总次数、剩余次数和有效期计算核销率，不填充预设分析结果。',
    notice: '分析仅统计当前门店范围内已发放的次卡；无次卡时所有指标为 0。',
    tableTitle: '次卡核销与余量分析',
    tableHint: '核销率 =（总次数 − 剩余次数）÷ 总次数；金额价值需待套餐价格规则接入后展示。',
    emptyText: '暂无次卡数据。发放次卡后会自动生成核销与余量分析。',
    filters: [input('keyword', '会员/卡号/卡名称'), select('status', '卡状态', ['正常', '停用'])],
    columns: [
      { key: 'cardNo', label: '卡号', width: 170 }, { key: 'cardName', label: '次卡名称', width: 170 },
      { key: 'memberName', label: '会员', width: 120 }, { key: 'totalCount', label: '总次数', width: 90 },
      { key: 'remainingCount', label: '剩余次数', width: 100 }, { key: 'writeOffRate', label: '核销率', width: 100 },
      { key: 'validTo', label: '有效期至', width: 120 }, { key: 'status', label: '状态', format: 'status', width: 90 }
    ]
  },
  '会员等级体系': {
    featureId: 'F087',
    description: '维护会员等级、权益和升降级规则；未配置规则时显示为空，避免伪造等级方案。',
    notice: '会员等级与权益规则正在配置，规则确认并审核后方可发布。',
    tableTitle: '等级与权益规则',
    tableHint: '等级规则总部统一维护，门店仅执行已发布权益。',
    emptyText: '暂无会员等级或权益规则数据，待总部配置后显示。',
    filters: [input('keyword', '等级/权益名称'), select('status', '状态', ['草稿', '已发布', '已停用'])],
    columns: [
      { key: 'level', label: '等级', width: 120 }, { key: 'benefitName', label: '权益名称', width: 180 },
      { key: 'upgradeRule', label: '升级条件', width: 200 }, { key: 'status', label: '状态', format: 'status', width: 100 }
    ]
  },
  '会员标签与智能分群': {
    featureId: 'F088',
    description: '管理会员标签与分群定义；未接入标签规则和触达结果前不展示示例人群。',
    notice: '标签、分群条件和触达规则正在配置，确认前暂不统计营销结果。',
    tableTitle: '会员标签与分群',
    tableHint: '会员标签可跨店查询，实际触达必须按具体执行门店留痕。',
    emptyText: '暂无标签或分群数据，待标签规则配置后显示。',
    filters: [input('keyword', '标签/分群名称'), select('status', '状态', ['草稿', '已发布', '已归档'])],
    columns: [
      { key: 'segmentName', label: '分群名称', width: 200 }, { key: 'conditions', label: '筛选条件', width: 260 },
      { key: 'memberCount', label: '会员数', width: 100 }, { key: 'status', label: '状态', format: 'status', width: 100 }
    ]
  }
}

pageDefinitionByTitle['资产账单'] = {
  featureId: 'F059',
  description: '按会员汇总储值账户、储值卡和次卡余额，并保留每笔充值、扣款、核销和调整的发生门店。',
  notice: '会员主档可跨店查询；资产流水必须保留实际发生门店。全部门店仅用于汇总，不允许直接写入。',
  tableTitle: '会员资产账单',
  tableHint: '展示真实会员资产余额和发生门店；未接入的外部支付、短信和跨店迁移不会显示为成功。',
  emptyText: '暂无会员资产账单。完成发卡、充值或次卡核销后会显示真实记录。',
  assetEntry: true,
  filters: [input('keyword', '会员/卡号/账单号'), select('assetType', '资产类型', ['储值账户', '储值卡', '次卡']), select('status', '账单状态', ['正常', '冻结', '已失效'])],
  columns: [
    { key: 'assetNo', label: '资产编号', width: 170 }, { key: 'memberName', label: '会员姓名', width: 120 },
    { key: 'assetType', label: '资产类型', width: 105 }, { key: 'balance', label: '储值余额', format: 'money', width: 120 },
    { key: 'remainingCount', label: '剩余次数', width: 100 }, { key: 'storeName', label: '发生门店', width: 160 },
    { key: 'status', label: '账单状态', format: 'status', width: 100 }
  ]
}

const normalizeFeatureTitle = value => String(value || '')
  .replace(/\s*★\s*$/, '')
  .replace(/\s*[（(][^）)]*[）)]\s*/g, '')
  .trim()

export default {
  name: 'MemberWorkbench',
  data() {
    return { loading: false, loadError: '', accounts: [], cards: [], filters: {}, loadSequence: 0 }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    pageTitle() { return this.$route.meta.configTitle || normalizeFeatureTitle(this.$route.meta.title) },
    definition() { return pageDefinitionByTitle[normalizeFeatureTitle(this.pageTitle)] || pageDefinitionByTitle['会员来源分析'] },
    storeScopeLabel() { return String(this.currentStoreId || 'all') === 'all' ? '全部授权门店' : '当前已选门店' },
    memberRows() {
      const rows = new Map()
      this.accounts.forEach(account => {
        const key = `account-${account.id}`
        rows.set(key, {
          id: key, memberNo: account.account_no || '暂无数据', memberName: account.customer_name || '暂无数据',
          mobile: account.mobile || '暂无数据', source: '暂无来源记录', storeName: account.store_name || '暂无数据', status: account.status || '暂无数据'
        })
      })
      this.cards.forEach(card => {
        const exists = [...rows.values()].some(row => row.memberName === card.customer_name && row.storeName === card.store_name)
        if (!exists) {
          rows.set(`card-${card.id}`, {
            id: `card-${card.id}`, memberNo: card.card_no || '暂无数据', memberName: card.customer_name || '暂无数据',
            mobile: '暂无数据', source: '暂无来源记录', storeName: card.store_name || '暂无数据', status: card.status || '暂无数据'
          })
        }
      })
      return [...rows.values()]
    },
    sourceRows() { return this.memberRows },
    assetRows() {
      return [
        ...this.accounts.map(row => ({ id: `account-${row.id}`, assetNo: row.account_no, memberName: row.customer_name, assetType: '余额账户', available: this.money(row.balance), storeName: row.store_name, status: row.status })),
        ...this.cards.map(row => ({ id: `card-${row.id}`, assetNo: row.card_no, memberName: row.customer_name, assetType: row.card_type, available: row.card_type === '储值卡' ? this.money(row.balance) : `${Number(row.remaining_count || 0)} 次`, storeName: row.store_name, status: row.status }))
      ]
    },
    pointRows() {
      return this.accounts.map(row => ({ id: row.id, accountNo: row.account_no, memberName: row.customer_name, points: Number(row.points || 0), balance: Number(row.balance || 0), storeName: row.store_name, status: row.status }))
    },
    cardRows() {
      return this.cards.filter(row => row.card_type === '次卡').map(row => {
        const total = Number(row.total_count || 0)
        const remaining = Number(row.remaining_count || 0)
        return {
          id: row.id, cardNo: row.card_no, cardName: row.card_name, memberName: row.customer_name,
          totalCount: total, remainingCount: remaining, writeOffRate: total ? `${((total - remaining) / total * 100).toFixed(1)}%` : '暂无数据',
          validTo: row.valid_to || '暂无数据', status: row.status || '暂无数据'
        }
      })
    },
    rows() {
      const id = this.definition.featureId
      if (id === 'F006') return this.sourceRows
      if (id === 'F008') return this.assetRows
      if (id === 'F040') return this.pointRows
      if (id === 'F060') return this.cardRows
      return []
    },
    filteredRows() {
      return this.rows.filter(row => Object.keys(this.filters).every(key => {
        const value = this.filters[key]
        if (!value) return true
        if (key === 'keyword') return Object.values(row).some(item => String(item == null ? '' : item).toLowerCase().includes(String(value).toLowerCase()))
        if (key === 'pointsScope') return value === '有积分' ? Number(row.points || 0) > 0 : Number(row.points || 0) === 0
        if (key === 'assetType') return row.assetType === value
        return String(row.status || '') === value
      }))
    },
    metrics() {
      const id = this.definition.featureId
      const accountBalance = this.accounts.reduce((total, row) => total + Number(row.balance || 0), 0)
      const points = this.accounts.reduce((total, row) => total + Number(row.points || 0), 0)
      const activeCards = this.cards.filter(row => row.status === '正常').length
      if (id === 'F006') {
        return [
          { label: '关联会员', value: this.memberRows.length, note: '账户或卡资产关联客户' },
          { label: '来源已记录', value: 0, note: '来源规则待配置' },
          { label: '待补充来源', value: this.memberRows.length, note: '需从客户主档补录' },
          { label: '关联门店', value: new Set(this.memberRows.map(row => row.storeName).filter(name => name !== '暂无数据')).size, note: '当前查询范围' }
        ]
      }
      if (id === 'F008') {
        return [
          { label: '有效卡资产', value: activeCards, note: '次卡与储值卡' },
          { label: '余额账户', value: this.accounts.length, note: '真实账户数' },
          { label: '账户余额', value: `¥${this.money(accountBalance)}`, note: '当前可用余额' },
          { label: '优惠券数据', value: 0, note: '业务规则待配置' }
        ]
      }
      if (id === 'F040') {
        return [
          { label: '积分账户', value: this.accounts.length, note: '真实账户数' },
          { label: '积分余额', value: points, note: '当前账户累计' },
          { label: '有积分账户', value: this.accounts.filter(row => Number(row.points || 0) > 0).length, note: '余额大于 0' },
          { label: '已配置规则', value: 0, note: '规则待配置' }
        ]
      }
      if (id === 'F060') {
        const total = this.cardRows.reduce((sum, row) => sum + row.totalCount, 0)
        const remaining = this.cardRows.reduce((sum, row) => sum + row.remainingCount, 0)
        return [
          { label: '次卡数量', value: this.cardRows.length, note: '真实发卡记录' },
          { label: '总次数', value: total, note: '已发放次数' },
          { label: '剩余次数', value: remaining, note: '当前可核销' },
          { label: '整体核销率', value: total ? `${((total - remaining) / total * 100).toFixed(1)}%` : '0.0%', note: '按次数计算' }
        ]
      }
      if (id === 'F087') {
        return [
          { label: '已配置等级', value: 0, note: '暂无规则数据' }, { label: '权益规则', value: 0, note: '暂无规则数据' },
          { label: '待审核变更', value: 0, note: '暂无规则数据' }, { label: '已发布版本', value: 0, note: '暂无规则数据' }
        ]
      }
      return [
        { label: '有效标签', value: 0, note: '暂无标签数据' }, { label: '已保存分群', value: 0, note: '暂无分群数据' },
        { label: '待触达任务', value: 0, note: '暂无触达数据' }, { label: '当前查询会员', value: this.memberRows.length, note: '仅用于后续分群' }
      ]
    }
  },
  watch: {
    '$route.fullPath': { immediate: true, handler() { this.resetFilters(); this.loadData() } },
    currentStoreId() { this.loadData() }
  },
  methods: {
    async loadData() {
      const sequence = ++this.loadSequence
      this.loading = true
      this.loadError = ''
      try {
        const params = { storeId: this.currentStoreId || 'all' }
        const [accounts, cards] = await Promise.all([getAssetList('accounts', params), getAssetList('cards', params)])
        if (this.loadSequence !== sequence) return
        this.accounts = (accounts.data && accounts.data.list) || []
        this.cards = (cards.data && cards.data.list) || []
      } catch (error) {
        if (this.loadSequence === sequence) {
          this.accounts = []
          this.cards = []
          this.loadError = '会员数据暂时无法读取，已保留空态；请刷新或联系系统管理员。'
        }
      } finally {
        if (this.loadSequence === sequence) this.loading = false
      }
    },
    resetFilters() { this.filters = this.definition.filters.reduce((result, item) => ({ ...result, [item.key]: '' }), {}) },
    applyFilters() { this.$message.success(`已按当前条件查询，共 ${this.filteredRows.length} 条`) },
    openAssetCenter() { this.$router.push('/customer/member-assets') },
    displayValue(value) { return value === undefined || value === null || value === '' ? '暂无数据' : value },
    money(value) { return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) },
    statusType(status) { return status === '正常' || status === '已发布' ? 'success' : status === '停用' || status === '已停用' ? 'info' : 'warning' },
    exportRows() {
      const columns = this.definition.columns
      const lines = [columns.map(column => column.label).join(','), ...this.filteredRows.map(row => columns.map(column => `"${String(row[column.key] == null ? '' : row[column.key]).replace(/"/g, '""')}"`).join(','))]
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    }
  }
}
</script>

<style lang="scss" scoped>
.member-workbench { min-height: calc(100vh - 84px); padding: 20px; color: #2f2a24; background: #f5f6f8; }
.page-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:20px; padding:20px 24px; background:linear-gradient(110deg,#47351f,#8d6b37); border-radius:12px; color:#fff; }.eyebrow { color:#f0d49b; font-size:12px; font-weight:700; letter-spacing:1px; }.page-heading h1 { margin:6px 0; font-size:26px; }.page-heading p { margin:0; color:#f8f0e1; font-size:13px; }.heading-actions { display:flex; gap:8px; }.notice { margin-top:14px; }.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-top:14px; }.metric-card { min-height:88px; padding:15px 18px; border:1px solid #ece5da; border-radius:10px; background:#fff; }.metric-card span,.metric-card strong,.metric-card small { display:block; }.metric-card span,.metric-card small { color:#7d8798; font-size:12px; }.metric-card strong { margin:7px 0; color:#513b1e; font-size:23px; }.content-card { margin-top:14px; border-color:#ece5da; border-radius:10px; }.card-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; }.card-heading h2 { margin:0 0 5px; font-size:16px; }.card-heading p { margin:0; color:#8791a1; font-size:12px; }.filter-form { margin-bottom:10px; }.data-table ::v-deep th { color:#5f523e; background:#f6efe3; }.empty-state { padding:26px 0 10px; color:#8b95a5; text-align:center; } @media(max-width:1000px) { .metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.page-heading { flex-direction:column; } } @media(max-width:640px) { .member-workbench { padding:12px; }.metric-grid { grid-template-columns:1fr; }.heading-actions { flex-wrap:wrap; } }
</style>
