<template>
  <el-dialog
    title="客户明细"
    :visible="visible"
    width="96%"
    top="3vh"
    append-to-body
    :close-on-click-modal="false"
    custom-class="resident-detail-dialog"
    @update:visible="$emit('update:visible', $event)"
  >
    <el-tabs v-model="activeTab" type="card" class="resident-tabs">
      <el-tab-pane v-for="tab in tabs" :key="tab" :label="tab" :name="tab">
        <template v-if="tab === '客户详细信息'">
          <section v-for="section in detailSections" :key="section.title" class="resident-section">
            <h3>{{ section.title }}</h3>
            <div class="resident-field-grid">
              <div v-for="field in section.fields" :key="field.label" :class="{ 'is-wide': field.wide }">
                <span>{{ field.label }}</span>
                <strong :class="{ 'is-money': field.money }">{{ field.value || '—' }}</strong>
              </div>
            </div>
            <p v-if="section.hint" class="section-hint">{{ section.hint }}</p>
          </section>
        </template>

        <template v-else>
          <el-table :data="tabRows(tab)" border stripe max-height="350">
            <el-table-column prop="recordName" :label="tab" min-width="180" />
            <el-table-column prop="recordTime" label="记录时间" min-width="150" />
            <el-table-column prop="status" label="状态" min-width="100" />
            <el-table-column prop="summary" label="摘要" min-width="300" show-overflow-tooltip />
          </el-table>
          <p v-if="!tabRows(tab).length" class="tab-evidence-note">暂无数据</p>
        </template>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script>
const tabs = [
  '客户详细信息', '跟踪信息', '合同信息', '宝宝信息', '套餐信息', '额外购信息', '商品购买',
  '续住信息', '房间信息', '服务记录', '收款记录', '护理计划单', '备忘录记录',
  '客户回访记录', '月嫂服务记录', '优惠券记录', '服务综合查询'
]

export default {
  name: 'RoomResidentDialog',
  props: {
    visible: { type: Boolean, default: false },
    room: { type: Object, default: null },
    stay: { type: Object, default: null }
  },
  data() {
    return {
      activeTab: '客户详细信息',
      tabs
    }
  },
  computed: {
    detailSections() {
      const stay = this.stay || {}
      const room = this.room || {}
      return [
        {
          title: '客户基本资料',
          fields: [
            { label: '客户姓名', value: stay.customerName },
            { label: '联系电话', value: stay.mobile },
            { label: 'QQ或微信', value: stay.wechat },
            { label: '会员卡号', value: stay.memberCardNo },
            { label: '证件类别', value: stay.idType },
            { label: '证件号', value: stay.idNo },
            { label: '客户生日', value: stay.birthday },
            { label: '客户性别', value: stay.gender },
            { label: '客户年龄', value: stay.age },
            { label: '客户民族', value: stay.nation },
            { label: '客户籍贯', value: stay.native },
            { label: '电子邮箱', value: stay.email },
            { label: '客户区域', value: stay.region },
            { label: '到店时间', value: stay.plannedCheckInAt },
            { label: '客户职业', value: stay.occupation },
            { label: '工作单位', value: stay.workUnit },
            { label: '现住地址', value: stay.address, wide: true },
            { label: '客户标签', value: stay.customerLevel, wide: true },
            { label: '膳食备注', value: stay.mealPackage, wide: true },
            { label: '禁忌食材', value: stay.dietTaboo, wide: true },
            { label: '客户备注', value: stay.customerRemark, wide: true }
          ]
        },
        {
          title: '账户与收款',
          fields: [
            { label: '会员充值', value: stay.memberRecharge, money: true },
            { label: '会员余额', value: stay.memberBalance, money: true },
            { label: '押金金额', value: Number(room.deposit || 0).toFixed(2), money: true },
            { label: '押金余额', value: Number(room.depositBalance || room.deposit || 0).toFixed(2), money: true },
            { label: '产康储值卡等级', value: stay.recoveryCardLevel },
            { label: '产康储值卡充值', value: stay.recoveryRecharge, money: true },
            { label: '产康储值卡余额', value: stay.recoveryBalance, money: true },
            { label: '合同金额', value: Number(stay.contractAmount || 0).toFixed(2), money: true },
            { label: '服务收款', value: stay.serviceReceipt, money: true },
            { label: '续住收款', value: stay.extensionReceipt, money: true }
          ],
          hint: '* 合同收款是指合同审核通过的、最近一个合同的收款。'
        },
        {
          title: '客户状态',
          fields: [
            { label: '客户状态', value: stay.status === '已入住' ? '已入住' : '已预约' },
            { label: '预产期', value: stay.edc },
            { label: '孕周', value: stay.gestationalWeeks },
            { label: '产检医院', value: stay.prenatalHospital },
            { label: '客户类型', value: stay.customerLevel },
            { label: '客户来源', value: stay.customerSource },
            { label: '胎次', value: stay.parity },
            { label: '胎型', value: stay.fetusType },
            { label: '介绍人类型', value: stay.referrerType },
            { label: '介绍人', value: stay.referrer },
            { label: '介绍人电话', value: stay.referrerPhone },
            { label: '分配人员', value: stay.salesperson },
            { label: '复查时间', value: stay.reviewDate },
            { label: '陪护人', value: stay.escort },
            { label: '陪护人电话', value: stay.escortMobile }
          ]
        },
        {
          title: '意向信息',
          fields: [
            { label: '意向分店', value: room.store },
            { label: '意向房间', value: room.room },
            { label: '意向房型', value: room.roomType },
            { label: '意向天数', value: stay.totalDays },
            { label: '意向预住时间', value: stay.plannedCheckInAt },
            { label: '意向合同金额', value: Number(stay.contractAmount || 0).toFixed(2), money: true },
            { label: '意向套餐', value: stay.packageName },
            { label: '意向月子餐', value: stay.mealPackage }
          ]
        }
      ]
    }
  },
  watch: {
    visible(value) {
      if (value) this.activeTab = '客户详细信息'
    }
  },
  methods: {
    tabRows(tab) {
      const stay = this.stay || {}
      if (tab === '合同信息' && stay.contractNo) {
        return [{
          recordName: stay.contractNo,
          recordTime: stay.plannedCheckInAt,
          status: stay.status,
          summary: `${stay.packageName || '未填写套餐'}，合同金额 ${Number(stay.contractAmount || 0).toFixed(2)}`
        }]
      }
      if (tab === '房间信息') {
        return [{
          recordName: `${(this.room || {}).room || ''} ${(this.room || {}).roomType || ''}`,
          recordTime: stay.checkInAt || stay.plannedCheckInAt,
          status: stay.status,
          summary: `${stay.startAt || ''} 至 ${stay.endAt || ''}`
        }]
      }
      return []
    }
  }
}
</script>

<style lang="scss" scoped>
.resident-alert { margin-bottom: 14px; }
.resident-tabs ::v-deep .el-tabs__header { margin-bottom: 14px; }
.resident-tabs ::v-deep .el-tabs__nav { display: flex; flex-wrap: wrap; float: none; }
.resident-tabs ::v-deep .el-tabs__item { border-bottom: 1px solid #e4e7ed; }
.resident-section + .resident-section { margin-top: 18px; }
.resident-section h3 { margin: 0; padding: 10px 14px; color: #fff; background: #ec6f93; font-size: 14px; }
.resident-field-grid { display: grid; grid-template-columns: repeat(4, minmax(190px, 1fr)); border-top: 1px solid #ebeef5; border-left: 1px solid #ebeef5; }
.resident-field-grid > div { display: grid; grid-template-columns: 105px 1fr; min-height: 42px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.resident-field-grid > div.is-wide { grid-column: span 2; }
.resident-field-grid span { padding: 11px 9px; color: #677489; background: #f7f9fb; }
.resident-field-grid strong { padding: 11px 9px; color: #344257; font-weight: 500; }
.resident-field-grid strong.is-money { color: #d75d67; font-weight: 700; }
.section-hint { margin: 0; padding: 10px 14px; border: 1px solid #ebeef5; border-top: 0; color: #e35e68; font-size: 12px; }
.tab-evidence-note { margin: 12px 0 0; color: #98a2b0; font-size: 12px; }

@media (max-width: 1180px) {
  .resident-field-grid { grid-template-columns: repeat(2, minmax(220px, 1fr)); }
}
</style>
