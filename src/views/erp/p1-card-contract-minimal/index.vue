<template>
  <div v-loading="loading" class="p1-page">
    <section class="hero">
      <div>
        <el-tag type="warning" effect="dark">P1 最小可用</el-tag>
        <h1>{{ pageTitle }}</h1>
        <p>{{ description }}</p>
      </div>
      <el-button icon="el-icon-refresh" :loading="loading" @click="loadData">刷新</el-button>
    </section>

    <el-alert
      :title="externalNotice"
      type="warning"
      :closable="false"
      show-icon
      class="external-alert"
    />
    <el-alert v-if="isAllStores" title="当前为全部门店：仅允许汇总查询。请选择具体门店后查看或登记卡项、合同归档等交易明细。" type="warning" :closable="false" show-icon class="external-alert" />
    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      :closable="false"
      show-icon
      class="external-alert"
    />

    <template v-if="featureId === 'F082'">
      <el-card shadow="never" class="content-card">
        <div slot="header" class="card-header">
          <div><b>套餐卡 / 次卡</b><span>仅以已审核收款单为发卡依据</span></div>
          <div>
            <el-button size="small" icon="el-icon-download" :disabled="!rows.length" @click="exportRows">导出当前结果</el-button>
            <el-button size="small" type="primary" icon="el-icon-plus" :disabled="isAllStores" @click="cardDialogVisible = true">新建待启用卡</el-button>
          </div>
        </div>
        <el-table :data="filteredRows" border stripe empty-text="当前权限门店暂无套餐卡">
          <el-table-column prop="cardNo" label="卡号" min-width="160" />
          <el-table-column prop="cardName" label="卡名称" min-width="140" />
          <el-table-column prop="customerName" label="客户" min-width="100" />
          <el-table-column prop="store" label="门店" min-width="160" />
          <el-table-column label="剩余次数" min-width="105">
            <template slot-scope="{ row }">{{ row.remainingCount }} / {{ row.totalCount }}</template>
          </el-table-column>
          <el-table-column prop="receiptNo" label="收款单号" min-width="175" />
          <el-table-column prop="validTo" label="有效期" min-width="110" />
          <el-table-column prop="status" label="状态" min-width="100">
            <template slot-scope="{ row }"><el-tag size="mini" :type="cardStatusType(row.status)">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="190">
            <template slot-scope="{ row }">
              <el-button v-if="row.status === '待启用'" type="text" @click="cardAction(row, 'activate')">启用</el-button>
              <el-button v-if="row.status === '正常'" type="text" @click="cardAction(row, 'consume')">核销一次</el-button>
              <el-button v-if="['待启用', '正常'].includes(row.status)" type="text" class="danger" @click="cardAction(row, 'deactivate')">停用</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-dialog title="新建待启用套餐卡" :visible.sync="cardDialogVisible" width="520px" @closed="resetCardForm">
        <el-alert title="此操作只创建待启用的服务权益，不会生成任何在线支付或收款成功结果。请填写已审核的线下收款单号。" type="warning" :closable="false" show-icon class="dialog-alert" />
        <el-form ref="cardForm" :model="cardForm" :rules="cardRules" label-width="110px">
          <el-form-item label="客户" prop="customerId">
            <el-select v-model="cardForm.customerId" filterable placeholder="请选择当前权限门店客户" class="full">
              <el-option v-for="item in customers" :key="item.id" :label="`${item.name} · ${item.storeName} · ${item.phone || ''}`" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="已审核收款单" prop="receiptNo"><el-input v-model.trim="cardForm.receiptNo" placeholder="例如 SK-20260731-0001" /></el-form-item>
          <el-form-item label="卡名称" prop="cardName"><el-input v-model.trim="cardForm.cardName" placeholder="例如 12次产康服务卡" /></el-form-item>
          <el-form-item label="总次数" prop="totalCount"><el-input-number v-model="cardForm.totalCount" :min="1" :max="10000" /></el-form-item>
          <el-form-item label="有效期至" prop="validTo"><el-date-picker v-model="cardForm.validTo" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" /></el-form-item>
        </el-form>
        <div slot="footer"><el-button @click="cardDialogVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="saveCard">创建待启用卡</el-button></div>
      </el-dialog>
    </template>

    <template v-else>
      <el-card shadow="never" class="content-card">
        <div slot="header" class="card-header">
          <div><b>合同签署归档</b><span>登记线下纸质合同原件；电子签服务尚未接入</span></div>
          <el-button size="small" icon="el-icon-download" :disabled="!rows.length" @click="exportRows">导出当前结果</el-button>
        </div>
        <el-table :data="filteredRows" border stripe empty-text="当前权限门店暂无合同">
          <el-table-column prop="contractNo" label="合同编号" min-width="160" />
          <el-table-column prop="customerName" label="客户" min-width="100" />
          <el-table-column prop="store" label="门店" min-width="160" />
          <el-table-column prop="contractStatus" label="合同状态" min-width="105" />
          <el-table-column prop="archiveStatus" label="归档状态" min-width="120">
            <template slot-scope="{ row }"><el-tag size="mini" :type="archiveStatusType(row.archiveStatus)">{{ row.archiveStatus }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="electronicSignStatus" label="电子签状态" min-width="185" />
          <el-table-column prop="archiveReference" label="线下归档编号" min-width="150" />
          <el-table-column prop="signedAt" label="签署日期" min-width="105" />
          <el-table-column label="操作" fixed="right" width="160">
            <template slot-scope="{ row }">
              <el-button v-if="['已审核', '审核通过'].includes(row.contractStatus) && ['待线下归档', '已作废'].includes(row.archiveStatus)" type="text" @click="openArchiveDialog(row)">登记线下归档</el-button>
              <el-button v-if="row.archiveStatus === '线下已归档'" type="text" class="danger" @click="revokeArchive(row)">作废归档</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-dialog title="登记线下签署归档" :visible.sync="archiveDialogVisible" width="520px" @closed="resetArchiveForm">
        <el-alert title="这不是电子签署。系统只登记已签纸质合同的原件位置和归档编号，不会返回任何外部签署成功状态。" type="warning" :closable="false" show-icon class="dialog-alert" />
        <el-form ref="archiveForm" :model="archiveForm" :rules="archiveRules" label-width="110px">
          <el-form-item label="合同"><b>{{ archiveTarget && archiveTarget.contractNo }}</b></el-form-item>
          <el-form-item label="签署日期" prop="signedAt"><el-date-picker v-model="archiveForm.signedAt" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" /></el-form-item>
          <el-form-item label="线下归档编号" prop="archiveReference"><el-input v-model.trim="archiveForm.archiveReference" placeholder="纸质合同档案编号" /></el-form-item>
          <el-form-item label="原件存放位置" prop="originalLocation"><el-input v-model.trim="archiveForm.originalLocation" placeholder="例如 中心店档案室A柜-03" /></el-form-item>
        </el-form>
        <div slot="footer"><el-button @click="archiveDialogVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="saveArchive">确认登记</el-button></div>
      </el-dialog>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import {
  archiveContract,
  createCountCard,
  getContractArchives,
  getCountCardOptions,
  getCountCards,
  performCountCardAction,
  revokeContractArchive
} from '@/api/erp-p1-minimal'

export default {
  name: 'P1CardContractMinimal',
  props: { featureId: { type: String, required: true }, pageTitle: { type: String, required: true }},
  data() {
    return {
      loading: false, submitting: false, loadError: '', rows: [], customers: [],
      cardDialogVisible: false, archiveDialogVisible: false, archiveTarget: null,
      cardForm: { customerId: '', receiptNo: '', cardName: '', totalCount: 1, validTo: '' },
      archiveForm: { signedAt: '', archiveReference: '', originalLocation: '' },
      cardRules: {
        customerId: [{ required: true, message: '请选择客户', trigger: 'change' }],
        receiptNo: [{ required: true, message: '请填写已审核收款单号', trigger: 'blur' }],
        cardName: [{ required: true, message: '请填写卡名称', trigger: 'blur' }],
        totalCount: [{ required: true, message: '请填写总次数', trigger: 'change' }],
        validTo: [{ required: true, message: '请选择有效期', trigger: 'change' }]
      },
      archiveRules: {
        signedAt: [{ required: true, message: '请选择签署日期', trigger: 'change' }],
        archiveReference: [{ required: true, message: '请填写归档编号', trigger: 'blur' }],
        originalLocation: [{ required: true, message: '请填写原件位置', trigger: 'blur' }]
      }
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    isAllStores() { return String(this.currentStoreId || 'all') === 'all' },
    description() { return this.featureId === 'F082' ? '以已审核收款单为依据，完成待启用、启用、核销、耗尽和停用的卡权益状态管理。' : '登记已签纸质合同的归档状态；电子签署由已配置的签约服务办理。' },
    externalNotice() { return this.featureId === 'F082' ? '不接入在线支付：发卡仅绑定已审核收款单，不产生付款成功结果。' : '电子签服务未接入：本页仅管理线下纸质合同归档，电子签状态始终明确为未接入。' },
    filteredRows() { return this.rows }
  },
  watch: { currentStoreId() { this.loadData() } },
  created() { this.loadData() },
  methods: {
    async loadData() {
      if (this.isAllStores) { this.rows = []; return }
      this.loading = true; this.loadError = ''
      try {
        if (this.featureId === 'F082') {
          const [cards, options] = await Promise.all([getCountCards({ storeId: this.currentStoreId }), getCountCardOptions({ storeId: this.currentStoreId })])
          this.rows = (cards.data && cards.data.list) || []
          this.customers = (options.data && options.data.customers) || []
        } else {
          const response = await getContractArchives({ storeId: this.currentStoreId })
          this.rows = (response.data && response.data.list) || []
        }
      } catch (error) { this.loadError = (error && error.message) || '真实业务数据加载失败，请检查权限、迁移和数据库连接' } finally { this.loading = false }
    },
    cardStatusType(status) { return status === '正常' ? 'success' : status === '待启用' ? 'warning' : 'info' },
    archiveStatusType(status) { return status === '线下已归档' ? 'success' : status === '已作废' ? 'danger' : 'warning' },
    resetCardForm() { this.cardForm = { customerId: '', receiptNo: '', cardName: '', totalCount: 1, validTo: '' }; if (this.$refs.cardForm) this.$refs.cardForm.clearValidate() },
    saveCard() {
      this.$refs.cardForm.validate(async valid => {
        if (!valid) return
        this.submitting = true
        try { await createCountCard({ ...this.cardForm, storeId: this.currentStoreId }); this.cardDialogVisible = false; this.$message.success('已创建待启用套餐卡'); await this.loadData() } finally { this.submitting = false }
      })
    },
    cardAction(row, action) {
      const label = { activate: '启用', consume: '核销一次', deactivate: '停用' }[action]
      this.$confirm(`确认${label}卡 ${row.cardNo}？`, '套餐卡状态操作', { type: action === 'deactivate' ? 'warning' : 'info' }).then(async() => {
        await performCountCardAction(row.id, action, { ...(action === 'consume' ? { count: 1 } : {}), storeId: this.currentStoreId })
        this.$message.success(`${label}成功`); await this.loadData()
      }).catch(() => {})
    },
    openArchiveDialog(row) { this.archiveTarget = row; this.archiveDialogVisible = true },
    resetArchiveForm() { this.archiveTarget = null; this.archiveForm = { signedAt: '', archiveReference: '', originalLocation: '' }; if (this.$refs.archiveForm) this.$refs.archiveForm.clearValidate() },
    saveArchive() {
      this.$refs.archiveForm.validate(async valid => {
        if (!valid || !this.archiveTarget) return
        this.submitting = true
        try { await archiveContract(this.archiveTarget.id, { ...this.archiveForm, storeId: this.currentStoreId }); this.archiveDialogVisible = false; this.$message.success('线下合同归档已登记'); await this.loadData() } finally { this.submitting = false }
      })
    },
    revokeArchive(row) {
      this.$prompt('请输入作废原因（2至500字符）', '作废线下归档', { inputPattern: /[\s\S]{2,500}/, inputErrorMessage: '请填写2至500个字符' }).then(async({ value }) => {
        await revokeContractArchive(row.id, { reason: value.trim(), storeId: this.currentStoreId }); this.$message.success('归档已作废'); await this.loadData()
      }).catch(() => {})
    },
    exportRows() {
      const columns = this.featureId === 'F082'
        ? [['cardNo', '卡号'], ['cardName', '卡名称'], ['customerName', '客户'], ['store', '门店'], ['totalCount', '总次数'], ['remainingCount', '剩余次数'], ['receiptNo', '收款单号'], ['validTo', '有效期'], ['status', '状态']]
        : [['contractNo', '合同编号'], ['customerName', '客户'], ['store', '门店'], ['contractStatus', '合同状态'], ['archiveStatus', '归档状态'], ['electronicSignStatus', '电子签状态'], ['archiveReference', '线下归档编号'], ['signedAt', '签署日期']]
      const csv = [columns.map(([, label]) => label), ...this.rows.map(row => columns.map(([key]) => String(row[key] || '').replace(/"/g, '""')))].map(line => line.map(value => `"${value}"`).join(',')).join('\n')
      const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }); const link = document.createElement('a')
      link.href = URL.createObjectURL(blob); link.download = `${this.featureId}-${new Date().toISOString().slice(0, 10)}.csv`; link.click(); URL.revokeObjectURL(link.href)
    }
  }
}
</script>

<style lang="scss" scoped>
.p1-page { min-height: calc(100vh - 84px); padding: 24px; color: #26354c; background: #f3f6fa; }
.hero { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 28px; border-radius: 14px; color: #fff; background: linear-gradient(125deg, #354767, #5579b0); }
.hero h1 { margin: 10px 0 6px; font-size: 26px; }.hero p { margin: 0; color: #e6eefb; line-height: 1.7; }.external-alert { margin-top: 16px; }.content-card { margin-top: 16px; border: 0; }.card-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }.card-header b { margin-right: 12px; font-size: 16px; }.card-header span { color: #8a96a8; font-size: 12px; }.full { width: 100%; }.dialog-alert { margin-bottom: 16px; }.danger { color: #d9534f; }
@media (max-width: 760px) { .p1-page { padding: 12px; }.hero, .card-header { align-items: flex-start; flex-direction: column; } }
</style>
