<template>
  <el-dialog
    :title="dialogTitle"
    :visible.sync="innerVisible"
    width="96%"
    top="2vh"
    append-to-body
    :close-on-click-modal="false"
    custom-class="nursing-legacy-action-dialog"
  >
    <div class="legacy-action-page" :data-action="action">
      <el-alert
        title="兼容页面仅用于字段核对；标记“开发中”的操作不会提交数据，也不代表护理或医疗结论。"
        type="warning"
        :closable="false"
        show-icon
        class="mock-alert"
      />

      <service-booking
        v-if="pageMode === 'booking'"
        :client="client"
        @mock-save="mockSave"
      />

      <service-confirmation
        v-else-if="pageMode === 'service-confirm'"
        :client="client"
        @mock-save="mockSave"
      />

      <nursing-plan-sheet
        v-else-if="pageMode === 'plan-sheet'"
        :client="client"
        @mock-save="mockSave"
      />

      <nursing-plan-confirmation
        v-else-if="pageMode === 'plan-confirm'"
        :client="client"
        @mock-save="mockSave"
      />

      <legacy-record-page
        v-else
        :action="action"
        :client="client"
        @mock-save="mockSave"
      />
    </div>
    <div slot="footer">
      <el-button @click="innerVisible = false">关闭</el-button>
    </div>
  </el-dialog>
</template>

<script>
const STORE_OPTIONS = ['中心广场旗舰店', '黄河路轻奢店']
const STORE_ALL_OPTIONS = ['-全部-', ...STORE_OPTIONS]

const BOOKING_TABS = [
  {
    label: '套餐内服务项目',
    columns: ['选择', '序号', '项目编号', '项目名称', '项目类别', '折扣价', '单位', '数量', '剩余数量', '有效天数', '项目时长', '服务间隔天数', '疗程天数', '状态']
  },
  {
    label: '套餐外服务项目',
    columns: ['选择', '序号', '项目编号', '项目名称', '项目类别', '折扣价', '单位', '数量', '剩余数量', '有效天数', '项目时长', '服务间隔天数', '疗程天数', '状态']
  },
  {
    label: '额外购买项目',
    columns: ['选择', '序号', '项目编号', '项目名称', '项目类别', '折扣价', '单位', '数量', '剩余次数', '有效天数', '项目时长', '服务间隔天数', '疗程天数', '来源单号', '类型', '财务审核', '状态']
  },
  {
    label: '项目卡',
    columns: ['选择', '年卡编号', '卡名称', '卡类型', '项目类型', '客户姓名', '价格', '天数', '来源单号', '类型', '财务审核']
  }
]

const CONFIRM_TABS = [
  {
    label: '套餐内服务项目',
    columns: ['序号', '项目编号', '项目名称', '项目类别', '单位', '折扣价', '总次数', '剩余次数', '启用时间']
  },
  {
    label: '套餐外服务项目',
    columns: ['序号', '合同ID', '客户ID', '项目ID', '项目名称', '项目类型', '阶段', '价格', '单位', '数量', '剩余数量', '分配人', '有效天数', '开始日期', '截止日期', '来源单号', '预约次数', '剩余天数', '操作']
  },
  {
    label: '额外购买服务',
    columns: ['序号', '合同ID', '客户ID', '项目ID', '项目名称', '项目类型', '阶段', '价格', '单位', '数量', '剩余数量', '分配人', '有效天数', '开始日期', '截止日期', '来源单号', '预约次数', '类型', '财务审核', '剩余天数', '操作']
  },
  {
    label: '项目卡',
    columns: ['年卡编号', '卡名称', '卡类型', '项目类型', '客户姓名', '价格', '天数', '来源单号', '类型', '财务审核']
  },
  {
    label: '产康储值卡',
    columns: ['客户ID', '项目名称', '产康等级', '折扣', '总价', '余额', '操作']
  }
]

const FILTER = {
  input(key, label, placeholder = '') {
    return { key, label, type: 'input', placeholder }
  },
  select(key, label, options) {
    return { key, label, type: 'select', options }
  },
  date(key, label) {
    return { key, label, type: 'date' }
  }
}

const RECORD_PAGE_CONFIGS = {
  妈妈护理记录: {
    pageTitle: '新妈妈护理记录',
    filters: [
      FILTER.input('customerName', '客户姓名'),
      FILTER.input('babyName', '宝宝姓名'),
      FILTER.input('room', '房间号'),
      FILTER.select('store', '门店类别', STORE_ALL_OPTIONS),
      FILTER.select('customerStatus', '客户状态', ['- 请选择 -', '- 已入住 -', '- 已出院 -'])
    ],
    toolbar: ['新增', '编辑', '打印', '产妇护理单', '导出'],
    tables: [
      {
        title: '客户列表',
        columns: ['序号', '客户ID', '合同ID', '客户姓名', '宝宝姓名', '房间号', '分娩方式', '分娩日期', '入住日期', '退房时间', '所属门店']
      },
      {
        title: '护理记录',
        columns: ['序号', '姓名', '记录日期', '产后天数', '体温(C°)', '体重(kg)', '脉搏(次/分)', '血压(mmHg)', '呼吸(次/分)', '心率(次/分)', '创建人', '创建时间', '操作']
      }
    ],
    detailTitle: '新增新妈妈护理记录',
    detailFields: [
      FILTER.date('recordedAt', '记录日期'),
      FILTER.input('postpartumDays', '产后天数'),
      FILTER.input('temperature', '体温(C°)'),
      FILTER.input('weight', '体重(kg)'),
      FILTER.input('pulse', '脉搏(次/分)'),
      FILTER.input('bloodPressure', '血压(mmHg)'),
      FILTER.input('breathing', '呼吸(次/分)'),
      FILTER.input('heartRate', '心率(次/分)'),
      FILTER.select('risk', '异常情况', ['正常', '异常', '危险']),
      { key: 'careContent', label: '护理记录', type: 'textarea', span: 24 },
      { key: 'attachment', label: '附件', type: 'upload', span: 24 }
    ]
  },
  产康服务记录: {
    pageTitle: '产康服务记录',
    filters: [
      FILTER.input('customerName', '客户姓名'),
      FILTER.input('babyName', '宝宝姓名'),
      FILTER.input('projectName', '项目名称'),
      FILTER.input('serviceUser', '服务人'),
      FILTER.input('room', '房间号'),
      FILTER.select('store', '分店名称', STORE_ALL_OPTIONS),
      FILTER.select('serviceType', '类型', ['-全部-', '套餐内', '套餐外', '额外购', '产康储值卡']),
      FILTER.select('customerStatus', '客户状态', ['-全部-', '店内客户', '散客客户']),
      FILTER.select('projectSource', '项目来源', ['-全部-', '销售', '赠送']),
      FILTER.select('auditStatus', '审核状态', ['-全部-', '未审核', '已审核']),
      FILTER.select('autoCreated', '是否自动生成', ['-全部-', '手动', '自动']),
      FILTER.date('completedFrom', '完成日期'),
      FILTER.date('completedTo', '到')
    ],
    toolbar: ['编辑', '删除', '审核', '反审核', '批量修改', '项目服务评价', '退款', '打印', '导出'],
    tables: [
      {
        title: '产康服务记录列表',
        columns: ['序号', '姓名', '手机号', '宝宝姓名', '房间号', '项目名称', '类型', '次数', '服务人', '价格', '手工费', '制单人', '状态', '完成时间', '制单时间', '销售时间', '备注', '星级', '审核', '来源单号', '销售类型', '项目来源', '客户来源', '操作']
      },
      {
        title: '项目服务评价',
        columns: ['序号', '评价星级', '评价内容', '评价时间', '评价人', '签字图片']
      }
    ],
    detailTitle: '服务完成修改',
    detailFields: [
      FILTER.date('completedAt', '完成时间'),
      FILTER.input('completedCount', '完成次数'),
      { key: 'serviceUsers', label: '选择人员', type: 'staff' },
      FILTER.input('manualFee', '手工费'),
      FILTER.select('serviceStore', '服务分店', STORE_OPTIONS),
      { key: 'remark', label: '备注', type: 'textarea', span: 24 }
    ]
  },
  月嫂服务记录: {
    pageTitle: '月嫂服务记录',
    filters: [
      FILTER.input('customerName', '客户姓名'),
      FILTER.input('nurseName', '护理师名称'),
      FILTER.input('room', '房间号'),
      FILTER.select('store', '门店类别', STORE_ALL_OPTIONS),
      FILTER.select('completion', '完成状态', ['- 请选择 -', '- 未派工 -', '- 已派工 -', '- 已接单 -', '- 已上户 -', '- 已下户 -']),
      FILTER.select('customerStatus', '客户状态', ['- 请选择 -', '- 已入住 -', '- 已退房 -']),
      FILTER.select('serviceType', '服务类型', ['-请选择-', '会所入住', '到家服务', '医院陪护', '其他服务']),
      FILTER.select('dispatchAudit', '派工审核', ['- 请选择 -', '- 待提交 -', '- 待审核 -', '- 已审核 -', '- 驳回 -']),
      FILTER.select('documentStatus', '单据状态', ['- 请选择 -', '- 正常 -', '- 取消 -']),
      FILTER.date('completedFrom', '完成时间'),
      FILTER.date('completedTo', '到'),
      FILTER.date('serviceFrom', '开始服务时间'),
      FILTER.date('serviceTo', '到')
    ],
    toolbar: ['新增', '编辑', '删除', '派遣护理师', '提交审核', '上户', '下户', '更换护理师', '确认结算', '重置', '附件', '导出'],
    tables: [
      {
        title: '月嫂服务记录列表',
        columns: ['序号', '客户姓名', '房间号', '护理师名称', '手机号', '护理师等级', '形式(小时/天)', '收费标准', '标准工资', '下次工资', '已上户天数', '工资金额', '参考工资', '奖励金额', '惩罚金额', '所属门店', '开始服务时间', '实际完成时间', '是否完成', '是否结算', '预计完成时间', '派工审核', '来源', '月子合同号', '合同欠款', '护理师欠款', '执业类型', '录入时间', '附件', '操作']
      }
    ],
    detailTitle: '月嫂服务操作',
    detailFields: [
      FILTER.input('nurseName', '护理师名称'),
      FILTER.input('nursePhone', '联系方式'),
      FILTER.date('serviceStart', '服务时间'),
      FILTER.date('serviceEnd', '到'),
      FILTER.input('workDays', '服务天数'),
      FILTER.select('changeReason', '更换原因', ['-请选择-', '更换月嫂原因01', '更换月嫂原因02', '更换月嫂原因03']),
      FILTER.select('settlement', '结算方式', ['- 请选择 -', '- 护理师工资 -', '- 薪酬标准 -', '- 按天标准 -']),
      FILTER.select('monthlyDays', '护理师每月工作天数', ['- 26 -', '- 28 -']),
      FILTER.select('serviceType', '服务类型', ['会所入住', '到家服务', '医院陪护', '其他服务']),
      FILTER.select('operationType', '服务形式', ['8', '10', '12', '24']),
      FILTER.input('currentSalary', '当前工资'),
      FILTER.input('nextSalary', '下次工资'),
      FILTER.input('vacation', '休假请假'),
      FILTER.input('renewReward', '续单奖励'),
      FILTER.input('signReward', '签单奖励'),
      FILTER.input('bannerReward', '锦旗奖励'),
      FILTER.input('otherReward', '其他奖励'),
      FILTER.input('referenceSalary', '参考工资'),
      FILTER.input('penalty', '惩罚金额'),
      FILTER.input('finalSalary', '最终金额'),
      { key: 'remark', label: '备注', type: 'textarea', span: 24 }
    ]
  },
  医生查房记录: {
    pageTitle: '医生查房记录',
    filters: [
      FILTER.input('customerName', '客户姓名'),
      FILTER.input('babyName', '宝宝姓名'),
      FILTER.input('room', '房间号'),
      FILTER.select('department', '科别', ['-请选择-', '妇科', '儿科', '客房管家查房']),
      FILTER.select('store', '分店', STORE_ALL_OPTIONS),
      FILTER.select('customerStatus', '客户状态', ['- 请选择 -', '- 已入住 -', '- 已出院 -']),
      FILTER.select('risk', '异常状态', ['- 请选择 -', '正常', '异常', '危险']),
      FILTER.date('roundFrom', '查房时间'),
      FILTER.date('roundTo', '到')
    ],
    toolbar: ['新增', '编辑', '删除', '打印', '护士回复'],
    tables: [
      {
        title: '医生查房记录列表',
        columns: ['序号', '客户姓名', '宝宝姓名', '房间号', '分娩日期', '查房时间', '查房人姓名', '一般情况', '医生查房情况', '其他异常情况', '处理情况', '制单时间', '科别类型', '制单人', '是否回复', '护理等级', '操作']
      }
    ],
    detailTitle: '医生查房记录',
    detailFields: [
      FILTER.input('room', '房间号'),
      FILTER.input('customerName', '客户姓名'),
      FILTER.input('babyName', '宝宝姓名'),
      FILTER.date('roundAt', '查房时间'),
      { key: 'doctor', label: '查房人姓名', type: 'staff' },
      FILTER.select('department', '科别', ['妇科', '儿科', '客房管家查房']),
      { key: 'general', label: '一般情况', type: 'textarea', span: 24, placeholder: '请填写黄疸指数、体温及其他相关信息' },
      { key: 'roundContent', label: '医生查房情况', type: 'textarea', span: 24 },
      { key: 'otherAbnormal', label: '其他异常情况', type: 'textarea', span: 24 },
      { key: 'handling', label: '处理情况', type: 'textarea', span: 24 },
      FILTER.select('risk', '异常情况', ['正常', '异常', '危险'])
    ]
  },
  健康评估: {
    pageTitle: '健康评估',
    filters: [
      FILTER.input('customerName', '客户姓名'),
      FILTER.input('babyName', '宝宝姓名'),
      FILTER.input('room', '房间号'),
      FILTER.select('store', '门店类别', STORE_ALL_OPTIONS),
      FILTER.select('customerStatus', '客户状态', ['- 请选择 -', '- 已入住 -', '- 已出院 -'])
    ],
    toolbar: ['产妇入住评估新增', '宝宝入住评估新增', '产妇回家评估新增', '宝宝回家评估新增', '母婴指导评估新增', '删除'],
    tables: [
      {
        title: '客户列表',
        columns: ['客户ID', '客户姓名', '手机号', '房间号', '宝宝名称', '胎型', '分娩日期', '分娩方式', '入住时间', '退房时间', '客户状态', '查看合同']
      },
      {
        title: '健康评估记录',
        columns: ['客户名称', '宝宝名称', '评估类型', '录入时间', '录入人', '是否签名', '签名时间', '功能']
      }
    ],
    detailTitle: '新增健康评估',
    detailFields: [
      FILTER.select('assessmentType', '评估类型', ['产妇入住评估', '宝宝入住评估', '产妇回家评估', '宝宝回家评估', '母婴指导评估']),
      FILTER.date('assessedAt', '评估时间'),
      { key: 'assessor', label: '评估人', type: 'staff' },
      FILTER.select('risk', '评估结果', ['正常', '异常', '危险']),
      { key: 'content', label: '评估内容', type: 'textarea', span: 24 },
      { key: 'guidance', label: '指导建议', type: 'textarea', span: 24 },
      { key: 'signature', label: '客户签名', type: 'signature', span: 24 }
    ]
  },
  外出申请: {
    pageTitle: '外出申请',
    filters: [
      FILTER.input('customerName', '客户姓名'),
      FILTER.select('outStatus', '外出状态', ['请选择', '从未被审核', '审核已通过', '已返回', '审核不通过']),
      FILTER.date('outFrom', '外出时间'),
      FILTER.date('outTo', '到')
    ],
    toolbar: ['新增', '编辑', '删除', '打印', '审核', '确定客户已返回'],
    tables: [
      {
        title: '外出申请列表',
        columns: ['序号', '外出客户', '外出时间', '外出天数', '外出原因', '外出陪护人', '制单部门', '制单时间', '制单人', '审核状态', '外出人类型', '返回时间', '分店', '操作']
      }
    ],
    detailTitle: '外出申请单',
    detailFields: [
      FILTER.input('customerName', '外出人姓名'),
      FILTER.input('companion', '外出陪护人'),
      FILTER.date('outStart', '外出时间范围'),
      FILTER.date('outEnd', '至'),
      FILTER.select('personType', '外出人员类型', ['妈妈', '宝宝', '母婴']),
      { key: 'reason', label: '外出原因', type: 'textarea', span: 24 },
      { key: 'doctorOpinion', label: '护理部保健医师审核及意见', type: 'textarea', span: 24 },
      { key: 'headNurseOpinion', label: '护士长意见及审核', type: 'textarea', span: 24 },
      FILTER.select('auditStatus', '审核状态', ['通过', '不通过']),
      FILTER.input('outDays', '外出天数'),
      FILTER.date('returnAt', '返回时间'),
      { key: 'autoExtend', label: '是否自动延期入住', type: 'checkbox' }
    ]
  }
}

function createRows(columns, prefix = 'DEMO') {
  return [0, 1].map(index => {
    const row = {}
    columns.forEach((column, columnIndex) => {
      let value = `${prefix}-${String(index + 1).padStart(2, '0')}`
      if (/序号/.test(column)) value = index + 1
      else if (/客户姓名|姓名|外出客户/.test(column)) value = `演示客户0${index + 1}`
      else if (/宝宝/.test(column)) value = `演示宝宝0${index + 1}`
      else if (/房间/.test(column)) value = `A30${index + 1}`
      else if (/项目名称/.test(column)) value = index ? '产后舒缓护理' : '母婴基础护理'
      else if (/手机号|电话/.test(column)) value = '138****0000'
      else if (/门店|分店/.test(column)) value = STORE_OPTIONS[index % 2]
      else if (/日期|时间/.test(column)) value = `2026-07-${24 + index} 10:00`
      else if (/状态|审核/.test(column)) value = index ? '已审核' : '未审核'
      else if (/次数|数量|天数/.test(column)) value = index + 1
      else if (/金额|价格|工资|手工费|余额/.test(column)) value = `${180 + columnIndex}.00`
      else if (/操作|功能/.test(column)) value = '查看'
      row[`c${columnIndex}`] = value
    })
    return row
  })
}

const LegacyTable = {
  name: 'LegacyTable',
  props: {
    columns: { type: Array, default: () => [] },
    title: { type: String, default: '' },
    selectable: { type: Boolean, default: false }
  },
  data() {
    return { currentRow: null }
  },
  computed: {
    rows() {
      return createRows(this.columns, this.title || 'DEMO')
    }
  },
  methods: {
    selectRow(row) {
      this.currentRow = row
      this.$emit('selected', row)
    }
  },
  template: `
    <section class="legacy-table-section">
      <h3 v-if="title">{{ title }}</h3>
      <el-table
        :data="rows"
        border
        stripe
        size="mini"
        height="225"
        highlight-current-row
        @current-change="selectRow"
      >
        <el-table-column v-if="selectable" type="selection" width="44" fixed="left" />
        <el-table-column
          v-for="(column, index) in columns"
          :key="column + index"
          :prop="'c' + index"
          :label="column"
          :min-width="/备注|内容|情况|原因/.test(column) ? 180 : /姓名|项目|时间|日期/.test(column) ? 120 : 86"
          show-overflow-tooltip
        />
      </el-table>
    </section>
  `
}

const StaffPicker = {
  name: 'StaffPicker',
  props: {
    visible: { type: Boolean, default: false },
    withSchedule: { type: Boolean, default: false }
  },
  data() {
    return {
      selected: [],
      filters: { userName: '', department: '' },
      rows: [
        { account: 'admin-demo', name: '演示员工01', role: '护理师', department: '护理部', rank: '五星', shift: '白班', time: '09:00-10:00' },
        { account: 'nurse-demo', name: '演示员工02', role: '产康师', department: '产康部', rank: '四星', shift: '行政班', time: '10:00-11:00' }
      ]
    }
  },
  computed: {
    innerVisible: {
      get() { return this.visible },
      set(value) { this.$emit('update:visible', value) }
    }
  },
  methods: {
    confirm() {
      if (!this.selected.length) {
        this.$message.warning('请选择职员')
        return
      }
      this.$emit('confirm', this.selected)
      this.innerVisible = false
    }
  },
  template: `
    <el-dialog
      :title="withSchedule ? '选择技师和时间段' : '选择现有职员'"
      :visible.sync="innerVisible"
      width="800px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form :inline="true" size="small" class="staff-search">
        <el-form-item label="用户姓名"><el-input v-model="filters.userName" /></el-form-item>
        <el-form-item label="部门"><el-input v-model="filters.department" readonly /></el-form-item>
        <el-button size="small" type="primary">搜 索</el-button>
        <el-button size="small">选择部门</el-button>
      </el-form>
      <el-table :data="rows" border size="mini" @selection-change="selected = $event">
        <el-table-column type="selection" width="44" />
        <el-table-column prop="account" label="用户名" min-width="100" />
        <el-table-column prop="name" label="真实姓名" min-width="100" />
        <el-table-column prop="role" label="角色" min-width="90" />
        <el-table-column prop="department" label="部门" min-width="90" />
        <el-table-column prop="rank" label="星级" min-width="70" />
        <el-table-column v-if="withSchedule" prop="shift" label="班次" min-width="80" />
        <el-table-column v-if="withSchedule" prop="time" label="可预约时间段" min-width="120" />
      </el-table>
      <div slot="footer">
        <el-button @click="innerVisible = false">取消</el-button>
        <el-button type="primary" @click="confirm">确定</el-button>
      </div>
    </el-dialog>
  `
}

const ServiceBooking = {
  name: 'ServiceBooking',
  components: { LegacyTable, StaffPicker },
  props: {
    client: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      storeOptions: STORE_OPTIONS,
      bunkOptions: ['-请选择-', 'VIP1', 'VIP2', 'VIP3', 'VIP4', 'VIP5', 'VIP6', 'VIP7', 'VIP8', 'VIP9', 'VIP10', '洗头床'],
      equipmentOptions: ['-请选择-', '身体雕刻家', '汤姆森顿压床', '缪私细胞焕活仪', '艾灸仪', '髋骨仪', '红外线理疗仪', '太空舱', '能量熏蒸房', '通泽医疗盆底肌', '通泽医疗腹直肌电刺激'],
      projectTypes: ['请选择', '产后类', '产康服务', '护理服务', '膳食服务', '客房服务', '增值服务', '软硬件服务', '大礼包', '科颜肌肤'],
      form: {
        appointmentDate: '',
        store: STORE_OPTIONS[0],
        bunk: '-请选择-',
        equipment: '-请选择-',
        wechat: true,
        sms: false,
        projectType: '请选择'
      },
      activeTab: BOOKING_TABS[0].label,
      tabs: BOOKING_TABS,
      selectedProjects: [],
      staffVisible: false,
      selectedStaff: []
    }
  },
  methods: {
    selectProject(row) {
      this.selectedProjects = [row]
    },
    openStaff() {
      if (!this.form.appointmentDate) {
        this.$message.warning('请填写预约日期！！')
        return
      }
      if (!this.selectedProjects.length) {
        this.$message.warning('请选择要预约的项目！！')
        return
      }
      this.staffVisible = true
    },
    setStaff(rows) {
      this.selectedStaff = rows
    },
    save() {
      if (!this.form.appointmentDate) return this.$message.warning('请填写预约日期！！')
      if (!this.selectedProjects.length) return this.$message.warning('请选择要预约的项目！！')
      if (!this.selectedStaff.length) return this.$message.warning('请先选择服务人及预约时间段！！')
      this.$emit('mock-save', '服务预约')
    }
  },
  template: `
    <div class="business-page service-booking-page">
      <el-form label-width="104px" size="small" class="legacy-form">
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="客户名称：" required><el-input :value="client.customerName || '演示客户'" readonly /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="预约完成日期：" required><el-date-picker v-model="form.appointmentDate" type="date" value-format="yyyy-MM-dd" class="full-control" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="预约分店："><el-select v-model="form.store" class="full-control"><el-option v-for="item in storeOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="预约床位："><el-select v-model="form.bunk" class="full-control"><el-option v-for="item in bunkOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="预约设备："><el-select v-model="form.equipment" class="full-control"><el-option v-for="item in equipmentOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="消息："><el-checkbox v-model="form.wechat">微信</el-checkbox><el-checkbox v-model="form.sms">短信</el-checkbox></el-form-item></el-col>
        </el-row>
      </el-form>
      <div class="primary-action-row">
        <el-button size="small" @click="openStaff">选择服务人及时间段</el-button>
        <el-button size="small" type="primary" @click="save">确定</el-button>
        <span v-if="selectedStaff.length">已选择：{{ selectedStaff.map(item => item.name + ' ' + item.time).join('；') }}</span>
      </div>
      <div class="project-type-row">
        <span>项目类型：</span>
        <el-select v-model="form.projectType" size="small">
          <el-option v-for="item in projectTypes" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane v-for="tab in tabs" :key="tab.label" :label="tab.label" :name="tab.label">
          <legacy-table :columns="tab.columns" :title="tab.label" selectable @selected="selectProject" />
        </el-tab-pane>
      </el-tabs>
      <staff-picker :visible.sync="staffVisible" with-schedule @confirm="setStaff" />
    </div>
  `
}

const ServiceConfirmation = {
  name: 'ServiceConfirmation',
  components: { LegacyTable, StaffPicker },
  props: {
    client: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      storeOptions: STORE_OPTIONS,
      tabs: CONFIRM_TABS,
      activeTab: CONFIRM_TABS[0].label,
      staffVisible: false,
      selectedStaff: [],
      selectedProject: null,
      form: {
        contract: '演示休养计划【DEMO-202607-001】',
        projectName: '',
        completedAt: '',
        count: 1,
        manualFee: '0.00',
        store: STORE_OPTIONS[0],
        remark: '',
        wechat: true,
        sms: false
      }
    }
  },
  methods: {
    selectProject(row) {
      this.selectedProject = row
      this.form.projectName = '母婴基础护理（演示）'
    },
    setStaff(rows) {
      this.selectedStaff = rows
    },
    save() {
      if (!this.form.completedAt) return this.$message.warning('请选择完成时间!')
      if (!this.form.count || Number(this.form.count) < 1) return this.$message.warning('完成次数必须大于0!')
      if (!this.selectedProject) return this.$message.warning('请选择具体的项目!')
      if (!this.selectedStaff.length) return this.$message.warning('请选择职员')
      this.$emit('mock-save', '服务确认')
    }
  },
  template: `
    <div class="business-page service-confirm-page">
      <el-form label-width="100px" size="small" class="legacy-form">
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="当前合同："><el-select v-model="form.contract" class="full-control"><el-option :label="form.contract" :value="form.contract" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="选择服务："><el-input v-model="form.projectName" readonly placeholder="请从下方项目列表选择" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="完成时间：" required><el-date-picker v-model="form.completedAt" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" class="full-control" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="完成次数：" required><el-input-number v-model="form.count" :min="1" class="full-control" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="服务员工："><el-input :value="selectedStaff.map(item => item.name).join('、')" readonly><el-button slot="append" @click="staffVisible = true">点我更改</el-button></el-input></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="手 工 费："><el-input v-model="form.manualFee" readonly /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="服务分店：" required><el-select v-model="form.store" class="full-control"><el-option v-for="item in storeOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="消息："><el-checkbox v-model="form.wechat">发送服务微信消息</el-checkbox><el-checkbox v-model="form.sms">发送服务短信消息</el-checkbox></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备 注："><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <div class="primary-action-row">
        <el-button size="small" type="primary" @click="save">确定完成</el-button>
        <el-button size="small">关闭</el-button>
      </div>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane v-for="tab in tabs" :key="tab.label" :label="tab.label" :name="tab.label">
          <legacy-table :columns="tab.columns" :title="tab.label" @selected="selectProject" />
        </el-tab-pane>
      </el-tabs>
      <staff-picker :visible.sync="staffVisible" @confirm="setStaff" />
    </div>
  `
}

const NursingPlanSheet = {
  name: 'NursingPlanSheet',
  props: {
    client: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      template: '护理计划单',
      templates: ['护理计划单', '营养师访视记录单'],
      overview: [
        ['计划日期', '2026-07-24'],
        ['客户姓名', '演示客户01'],
        ['分娩医院', '演示医院'],
        ['房型', '豪华套房'],
        ['年龄', '30'],
        ['分娩方式', '顺产'],
        ['房号', 'A301'],
        ['胎数', '单胎'],
        ['分娩日期', '2026-07-18'],
        ['入住日期', '2026-07-18'],
        ['护理类型', '一对一护理'],
        ['预计退房日期', '2026-08-15'],
        ['入住天数', '28'],
        ['套餐名称', '演示休养计划']
      ],
      roles: ['生活管家', '责任护士长', '妇科保健医生', '儿科保健医生', '营养师', '产康护理', '母婴喂养师', '护理主任', '护理总监', '护士区', '客服区'],
      planRows: [
        { category: '妈妈护理', project: '产妇体征观察', count: '每日1次', frequency: '每日', owner: '责任护士', date: '入住期间', note: '演示计划' },
        { category: '宝宝护理', project: '宝宝沐浴抚触', count: '每日1次', frequency: '每日', owner: '护理师', date: '入住期间', note: '演示计划' }
      ]
    }
  },
  methods: {
    print() {
      window.print()
    }
  },
  template: `
    <div class="business-page plan-sheet-page">
      <div class="sheet-toolbar">
        <span>模板：</span>
        <el-select v-model="template" size="small">
          <el-option v-for="item in templates" :key="item" :label="item" :value="item" />
        </el-select>
        <el-button size="small" @click="print">打印</el-button>
        <el-button size="small" type="primary" @click="$emit('mock-save', '更新护理计划单')">确认更新护理计划单</el-button>
      </div>
      <section class="print-sheet">
        <h2>{{ template }}</h2>
        <div class="overview-grid">
          <div v-for="item in overview" :key="item[0]"><span>{{ item[0] }}：</span><b>{{ item[0] === '客户姓名' ? (client.customerName || item[1]) : item[1] }}</b></div>
          <div class="wide"><span>客户备注：</span><b>按客户档案及护理交接记录执行</b></div>
          <div class="wide"><span>宝宝信息：</span><b>单胎 / 健康信息待护理人员评估</b></div>
        </div>
        <h3>护理服务计划明细</h3>
        <el-table :data="planRows" border size="mini">
          <el-table-column prop="category" label="服务类别" />
          <el-table-column prop="project" label="服务项目" min-width="140" />
          <el-table-column prop="count" label="计划次数" />
          <el-table-column prop="frequency" label="执行频次" />
          <el-table-column prop="owner" label="责任岗位" />
          <el-table-column prop="date" label="计划日期" />
          <el-table-column prop="note" label="备注" />
        </el-table>
        <h3>护理团队确认</h3>
        <div class="role-grid">
          <div v-for="role in roles" :key="role"><span>{{ role }}</span><i>待确认</i></div>
        </div>
      </section>
    </div>
  `
}

const NursingPlanConfirmation = {
  name: 'NursingPlanConfirmation',
  components: { LegacyTable },
  props: {
    client: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      activeTab: 'calendar',
      filters: { customerName: '', projectName: '', store: '-请选择-' },
      stores: ['-请选择-', ...STORE_OPTIONS],
      weekOffset: 0,
      shifts: ['白班', '休班', '晚班', '行政班'],
      columns: ['序号', '编号', '合同ID', '排班id', '客户名字', '手机号', '项目名称', '项目类型', '类型', '班次', '预完成时间', '分店', '剩余次数', '已预约次数', '剩余天数', '客户id', '项目id', '项目类别', '功能']
    }
  },
  computed: {
    days() {
      const base = new Date(2026, 6, 20 + this.weekOffset * 7)
      const names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
      return names.map((name, index) => {
        const date = new Date(base)
        date.setDate(base.getDate() + index)
        return `${date.getMonth() + 1}月${date.getDate()}日（${name}）`
      })
    },
    weekLabel() {
      return `${this.days[0].replace(/（.*$/, '')} - ${this.days[6].replace(/（.*$/, '')}`
    }
  },
  methods: {
    complete() {
      this.$emit('mock-save', '护理计划确定完成')
    }
  },
  template: `
    <div class="business-page plan-confirm-page">
      <el-form :inline="true" size="small" class="search-bar">
        <el-form-item label="客户姓名："><el-input v-model="filters.customerName" /></el-form-item>
        <el-form-item label="项目名称："><el-input v-model="filters.projectName" /></el-form-item>
        <el-form-item label="分店："><el-select v-model="filters.store"><el-option v-for="item in stores" :key="item" :label="item" :value="item" /></el-select></el-form-item>
        <el-button size="small" type="primary">查询</el-button>
        <el-button size="small">打印</el-button>
        <el-button size="small" @click="complete">确定完成</el-button>
      </el-form>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="日历" name="calendar">
          <div class="week-switcher"><el-button size="mini" @click="weekOffset -= 1">&lt;</el-button><b>{{ weekLabel }}</b><el-button size="mini" @click="weekOffset += 1">&gt;</el-button></div>
          <div class="schedule-grid">
            <div class="corner" />
            <div v-for="day in days" :key="day" class="day-head">{{ day }}</div>
            <template v-for="shift in shifts">
              <div :key="shift + '-label'" class="shift-label">{{ shift }}</div>
              <div v-for="(day, index) in days" :key="shift + day" class="schedule-cell">
                <button v-if="shift === '白班' && index < 2" type="button" @click="complete">{{ client.customerName || '演示客户' }}<br>母婴护理</button>
              </div>
            </template>
          </div>
        </el-tab-pane>
        <el-tab-pane label="列表" name="list">
          <legacy-table :columns="columns" title="护理计划确认列表" />
        </el-tab-pane>
      </el-tabs>
    </div>
  `
}

const LegacyRecordPage = {
  name: 'LegacyRecordPage',
  components: { LegacyTable, StaffPicker },
  props: {
    action: { type: String, required: true },
    client: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      filters: {},
      detailVisible: false,
      detailAction: '',
      detailForm: {},
      staffVisible: false,
      staffTarget: '',
      selectedRow: null
    }
  },
  computed: {
    config() {
      return RECORD_PAGE_CONFIGS[this.action] || RECORD_PAGE_CONFIGS.妈妈护理记录
    },
    detailTitle() {
      return this.detailAction || this.config.detailTitle
    }
  },
  watch: {
    action: {
      immediate: true,
      handler() {
        const next = {}
        this.config.filters.forEach(field => {
          next[field.key] = field.type === 'select' ? field.options[0] : ''
        })
        if (this.client.customerName) next.customerName = this.client.customerName
        if (this.client.room) next.room = this.client.room
        this.filters = next
      }
    }
  },
  methods: {
    selectRow(row) {
      this.selectedRow = row
    },
    toolbarAction(action) {
      if (action === '打印' || action === '产妇护理单') {
        window.print()
        return
      }
      if (action === '导出') {
        this.$message.warning('该兼容页面导出仍在开发中，本次未生成文件')
        return
      }
      if (['删除', '审核', '反审核', '提交审核', '重置'].includes(action)) {
        if (!this.selectedRow) return this.$message.warning('请选中一行数据！')
        this.$message.warning(`${action}仍在开发中，本次未提交任何业务数据`)
        return
      }
      this.detailAction = action
      this.detailForm = {}
      this.config.detailFields.forEach(field => {
        this.$set(this.detailForm, field.key, field.type === 'checkbox' ? false : '')
      })
      if (this.client.customerName) this.$set(this.detailForm, 'customerName', this.client.customerName)
      if (this.client.room) this.$set(this.detailForm, 'room', this.client.room)
      this.detailVisible = true
    },
    openStaff(field) {
      this.staffTarget = field.key
      this.staffVisible = true
    },
    setStaff(rows) {
      this.$set(this.detailForm, this.staffTarget, rows.map(item => item.name).join('、'))
    },
    saveDetail() {
      this.$emit('mock-save', `${this.config.pageTitle}-${this.detailTitle}`)
      this.detailVisible = false
    }
  },
  template: `
    <div class="business-page record-page">
      <h2 class="record-page-title">{{ config.pageTitle }}</h2>
      <el-form :inline="true" size="small" class="record-filter-bar">
        <el-form-item v-for="field in config.filters" :key="field.key" :label="field.label">
          <el-input v-if="field.type === 'input'" v-model="filters[field.key]" :placeholder="field.placeholder" />
          <el-select v-else-if="field.type === 'select'" v-model="filters[field.key]">
            <el-option v-for="item in field.options" :key="item" :label="item" :value="item" />
          </el-select>
          <el-date-picker v-else v-model="filters[field.key]" type="date" value-format="yyyy-MM-dd" />
        </el-form-item>
        <el-button size="small" type="primary">搜 索</el-button>
      </el-form>
      <div class="legacy-toolbar">
        <el-button v-for="item in config.toolbar" :key="item" size="mini" @click="toolbarAction(item)">{{ item }}</el-button>
      </div>
      <legacy-table
        v-for="table in config.tables"
        :key="table.title"
        :title="table.title"
        :columns="table.columns"
        @selected="selectRow"
      />

      <el-dialog
        :title="detailTitle"
        :visible.sync="detailVisible"
        width="900px"
        append-to-body
        :close-on-click-modal="false"
      >
        <el-form label-width="142px" size="small">
          <el-row :gutter="12">
            <el-col v-for="field in config.detailFields" :key="field.key" :span="field.span || 12">
              <el-form-item :label="field.label">
                <el-input v-if="field.type === 'input'" v-model="detailForm[field.key]" :readonly="/客户姓名|房间号/.test(field.label)" />
                <el-select v-else-if="field.type === 'select'" v-model="detailForm[field.key]" class="full-control">
                  <el-option v-for="item in field.options" :key="item" :label="item" :value="item" />
                </el-select>
                <el-date-picker v-else-if="field.type === 'date'" v-model="detailForm[field.key]" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" class="full-control" />
                <el-input v-else-if="field.type === 'textarea'" v-model="detailForm[field.key]" type="textarea" :rows="3" :placeholder="field.placeholder || ''" />
                <el-input v-else-if="field.type === 'staff'" v-model="detailForm[field.key]" readonly><el-button slot="append" @click="openStaff(field)">选择职员</el-button></el-input>
                <el-checkbox v-else-if="field.type === 'checkbox'" v-model="detailForm[field.key]">{{ field.label }}</el-checkbox>
                <el-upload v-else-if="field.type === 'upload'" action="#" :auto-upload="false"><el-button size="small">选择文件</el-button></el-upload>
                <div v-else-if="field.type === 'signature'" class="signature-box">电子签名开发中（不会提交）</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        <div slot="footer">
          <el-button @click="detailVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDetail">确定</el-button>
        </div>
      </el-dialog>
      <staff-picker :visible.sync="staffVisible" @confirm="setStaff" />
    </div>
  `
}

export default {
  name: 'NursingLegacyActionDialog',
  components: {
    LegacyRecordPage,
    NursingPlanConfirmation,
    NursingPlanSheet,
    ServiceBooking,
    ServiceConfirmation
  },
  props: {
    visible: { type: Boolean, default: false },
    action: { type: String, default: '' },
    client: { type: Object, default: () => ({}) }
  },
  computed: {
    innerVisible: {
      get() { return this.visible },
      set(value) { this.$emit('update:visible', value) }
    },
    pageMode() {
      if (this.action === '产康服务预约') return 'booking'
      if (this.action === '产康服务确认') return 'service-confirm'
      if (this.action === '护理计划单') return 'plan-sheet'
      if (this.action === '护理计划确认') return 'plan-confirm'
      return 'record'
    },
    dialogTitle() {
      const titles = {
        产康服务预约: '服务预约',
        产康服务确认: '服务确认',
        护理计划单: '查看护理计划单',
        妈妈护理记录: '新妈妈护理记录',
        产康服务记录: '产康服务记录',
        月嫂服务记录: '月嫂服务记录',
        医生查房记录: '医生查房记录',
        健康评估: '健康评估',
        外出申请: '外出申请',
        护理计划确认: '护理计划确认'
      }
      return titles[this.action] || this.action
    }
  },
  methods: {
    mockSave(label) {
      this.$message.warning(`${label}仍在开发中，本次未提交任何业务数据`)
    }
  }
}
</script>

<style lang="scss">
.nursing-legacy-action-dialog {
  min-width: 1000px;
  max-width: 1520px;
}
.nursing-legacy-action-dialog > .el-dialog__body {
  max-height: 83vh;
  padding: 12px 16px;
  overflow: auto;
}
.legacy-action-page {
  color: #3f4b5a;
}
.legacy-action-page .mock-alert {
  margin-bottom: 12px;
}
.legacy-action-page .full-control {
  width: 100%;
}
.legacy-action-page .legacy-form,
.legacy-action-page .search-bar,
.legacy-action-page .record-filter-bar {
  padding: 12px 12px 0;
  border: 1px solid #e2e7ec;
  background: #f8fafc;
}
.legacy-action-page .primary-action-row,
.legacy-action-page .sheet-toolbar,
.legacy-action-page .legacy-toolbar {
  display: flex;
  align-items: center;
  min-height: 44px;
  gap: 8px;
}
.legacy-action-page .primary-action-row span {
  margin-left: 8px;
  color: #718096;
  font-size: 12px;
}
.legacy-action-page .project-type-row {
  display: flex;
  align-items: center;
  padding: 6px 0 10px;
  gap: 8px;
}
.legacy-table-section {
  margin: 8px 0 14px;
}
.legacy-table-section h3,
.record-page-title,
.print-sheet h3 {
  margin: 8px 0;
  color: #344257;
  font-size: 14px;
}
.staff-search {
  padding: 10px 10px 0;
  border: 1px solid #e4e7eb;
  background: #fafbfc;
}
.print-sheet {
  padding: 16px;
  border: 1px solid #8d99a6;
  background: #fff;
}
.print-sheet h2 {
  margin: 2px 0 16px;
  text-align: center;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid #b8c0c8;
  border-left: 1px solid #b8c0c8;
}
.overview-grid > div {
  min-height: 38px;
  padding: 8px;
  border-right: 1px solid #b8c0c8;
  border-bottom: 1px solid #b8c0c8;
}
.overview-grid .wide {
  grid-column: span 2;
}
.overview-grid span {
  color: #6e7782;
}
.role-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid #c6cdd4;
  border-left: 1px solid #c6cdd4;
}
.role-grid div {
  display: flex;
  justify-content: space-between;
  min-height: 42px;
  padding: 10px;
  border-right: 1px solid #c6cdd4;
  border-bottom: 1px solid #c6cdd4;
}
.role-grid i {
  color: #a4adb6;
  font-style: normal;
}
.week-switcher {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 5px 0 12px;
  gap: 18px;
}
.schedule-grid {
  display: grid;
  grid-template-columns: 86px repeat(7, minmax(120px, 1fr));
  border-top: 1px solid #cfd6dd;
  border-left: 1px solid #cfd6dd;
  overflow-x: auto;
}
.schedule-grid > div {
  min-height: 72px;
  padding: 7px;
  border-right: 1px solid #cfd6dd;
  border-bottom: 1px solid #cfd6dd;
}
.schedule-grid .corner,
.schedule-grid .day-head,
.schedule-grid .shift-label {
  min-height: 42px;
  background: #f2f5f7;
  font-weight: 600;
  text-align: center;
}
.schedule-cell button {
  width: 100%;
  padding: 6px;
  border: 1px solid #8eb6d8;
  border-radius: 3px;
  color: #356f9d;
  background: #eef7ff;
  cursor: pointer;
}
.record-page-title {
  font-size: 16px;
}
.legacy-toolbar {
  padding: 0 8px;
  border-right: 1px solid #e2e7ec;
  border-bottom: 1px solid #e2e7ec;
  border-left: 1px solid #e2e7ec;
  background: #fff;
}
.signature-box {
  height: 74px;
  padding: 24px;
  border: 1px dashed #b7c0ca;
  color: #9aa4ae;
  text-align: center;
}
@media (max-width: 1100px) {
  .overview-grid,
  .role-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
