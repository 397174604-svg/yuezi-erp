import { applyAuditedSurfaceEvidence } from './audited-surface-adapter'

const stores = ['公共门店', '中心广场旗舰店', '黄河路轻奢店']
const serviceStores = ['中心广场旗舰店', '黄河路轻奢店']
const practitionerTypes = ['月嫂', '育儿嫂', '催乳师', '小儿推拿师', '导乐师']
const serviceTypes = ['会所入住', '到家服务', '医院陪护', '其他服务']

const column = (key, label, width = 130, fixed = false) => ({
  key,
  label,
  width,
  fixed
})

const columns = labels => labels.map((label, index) => column(
  `field_${index + 1}`,
  label,
  /备注|审核记录|档期情况/.test(label) ? 220
    : /时间|日期|预产期|有效期/.test(label) ? 150
      : /名称|类型|状态|金额|奖励|工资|服务/.test(label) ? 140
        : 120,
  index === 0 ? 'left' : false
))

const field = (key, label, type = 'input', extra = {}) => ({
  key,
  label,
  type,
  ...extra
})

const archiveFormSections = [
  {
    title: '人员与执业信息',
    fields: [
      field('name', '护理师姓名', 'picker', { pickerText: '选择护理师' }),
      field('phoneRegion', '联系方式地区', 'select', { options: ['中国大陆', '中国香港', '中国澳门', '中国台湾'], defaultValue: '中国大陆' }),
      field('phone', '联系方式'),
      field('store', '所属分店', 'select', { options: stores, defaultValue: '公共门店' }),
      field('level', '护理师等级', 'select', { options: ['-请选择-', '初级月嫂', '中级月嫂', '高级月嫂'], defaultValue: '-请选择-' }),
      field('practiceType', '执业类型'),
      field('monthlySalary', '护理师工资(月)', 'number'),
      field('serviceType', '服务类型', 'select', { options: ['请选择', ...serviceTypes], defaultValue: '请选择' }),
      field('idCard', '身份证'),
      field('birthDate', '出生日期', 'date'),
      field('entryDate', '入职日期', 'date', { readonly: true }),
      field('insuranceExpire', '保险到期', 'date', { readonly: true }),
      field('healthExpire', '健康证到期', 'date', { readonly: true }),
      field('number', '月嫂编号'),
      field('education', '学历'),
      field('jobStatus', '职位状态', 'select', { options: ['在职', '工作中', '休息中', '离职'], defaultValue: '在职' })
    ]
  },
  {
    title: '个人与联系信息',
    fields: [
      field('bankNumber', '开户卡号'),
      field('bankName', '开户银行'),
      field('previousYears', '入职前从业年限(月)', 'number'),
      field('height', '身高'),
      field('emergencyName', '紧急联系人'),
      field('emergencyPhone', '紧急联系电话'),
      field('marriage', '婚否'),
      field('nativePlace', '籍贯'),
      field('permanentAddress', '户籍地址'),
      field('skill', '技能'),
      field('address', '现居地'),
      field('sort', '排序', 'number'),
      field('socialSecurity', '是否购买社保', 'select', { options: ['未购买', '已购买', '社保补贴'], defaultValue: '未购买' }),
      field('socialSecurityDate', '社保购买时间', 'date'),
      field('introducer', '护理师介绍人'),
      field('nurseCategory', '护理师类别', 'select', { options: ['-请选择-', '员工制', '签约制', '流动制'], defaultValue: '-请选择-' }),
      field('sex', '性别', 'select', { options: ['女', '男'], defaultValue: '女' })
    ]
  },
  {
    title: '介绍与附件',
    fields: [
      field('labels', '标签', 'textarea'),
      field('certificate', '获得职称', 'textarea'),
      field('avatar', '头像(限制一张图片 尺寸：500*300)', 'upload'),
      field('workExperience', '工作经验', 'textarea'),
      field('personalIntroduction', '个人简介', 'textarea'),
      field('note', '备注', 'textarea')
    ]
  }
]

const salaryFormSections = [
  {
    title: '薪酬标准',
    fields: [
      field('level', '服务人等级', 'select', { options: ['-请选择-', '初级月嫂', '中级月嫂', '高级月嫂'], defaultValue: '-请选择-' }),
      field('serviceForm', '服务形式', 'select', { options: ['-请选择-', '8', '10', '12', '24'], defaultValue: '-请选择-' }),
      field('practiceType', '执业类型', 'select', { options: ['-请选择-', ...practitionerTypes], defaultValue: '-请选择-' }),
      field('employeeStatus', '员工状态', 'select', { options: ['正式员工', '兼职员工'], defaultValue: '正式员工' }),
      field('serviceType', '服务类型', 'select', { options: ['--------全部----------', ...serviceTypes], defaultValue: '--------全部----------' }),
      field('price', '价格', 'number', { defaultValue: '0' }),
      field('referencePrice', '26日参考价', 'number'),
      field('store', '所属门店', 'select', { options: stores, defaultValue: '公共门店' }),
      field('description', '星级简介', 'textarea')
    ]
  }
]

const scheduleFormSections = [
  {
    title: '档期新增',
    fields: [
      field('startDate', '开始时间', 'date'),
      field('endDate', '结束时间', 'date'),
      field('scheduleType', '档期状态', 'radio-group', { options: ['请假'], defaultValue: '请假' }),
      field('visible', '是否显示', 'radio-group', { options: ['是', '否'], defaultValue: '是' }),
      field('leaveReason', '请假理由', 'textarea')
    ]
  }
]

const contractFormSections = [
  {
    title: '合同基本信息',
    fields: [
      field('contractNumber', '合同编号', 'input', { prefixAction: '生成合同编号' }),
      field('expectedDate', '预产期', 'date'),
      field('customer', '选择客户', 'picker', { readonly: true, pickerText: '选择客户' }),
      field('validityDate', '会员有效期', 'date'),
      field('rehabAmount', '产康服务金额', 'number', { defaultValue: '0' }),
      field('contractAmount', '合同金额', 'number', { defaultValue: '0', readonly: true }),
      field('tradeAmount', '合同最终成交金额', 'number'),
      field('signDate', '签订日期', 'date'),
      field('introducer', '介绍人'),
      field('introducerPhone', '介绍人电话'),
      field('department', '签单部门', 'input', { readonly: true }),
      field('salesperson', '签单人', 'input', { readonly: true, defaultValue: '当前登录人' }),
      field('memberDeduction', '会员扣款', 'checkbox', { defaultValue: false }),
      field('store', '签单分店', 'select', { options: serviceStores, defaultValue: '中心广场旗舰店' }),
      field('received', '是否收款', 'select', { options: ['否', '是'], defaultValue: '否' }),
      field('contractName', '合同名称'),
      field('note', '备注', 'textarea')
    ]
  },
  {
    title: '收款信息',
    fields: [
      field('billAmount', '单据金额', 'number'),
      field('settlementMethod', '结算方式', 'select', {
        options: ['请选择', '现金', 'POS机刷卡', '支付宝付款', '银联云闪付', '微信结算', '押金', '会员卡', '优惠券', '积分支付', '星pos支付'],
        defaultValue: '请选择'
      }),
      field('bank', '收款银行', 'select', {
        options: ['请选择', '招商银行', '交通银行', '广发银行', '中国银行', '中国工商银行', '中国建设银行', '中国农业银行', '支付宝', '招商银行（一般户）'],
        defaultValue: '请选择'
      }),
      field('coupon', '优惠券', 'select', { options: ['请选择'], defaultValue: '请选择' }),
      field('couponAmount', '优惠券金额', 'number')
    ]
  }
]

const serviceRecordFormSections = [
  {
    title: '派工服务信息',
    fields: [
      field('customer', '选择客户', 'picker', { readonly: true, pickerText: '选择客户' }),
      field('store', '服务分店', 'select', { options: serviceStores, defaultValue: '中心广场旗舰店' }),
      field('nurse', '选择护理师', 'picker', { readonly: true, pickerText: '选择护理师' }),
      field('phone', '联系方式'),
      field('serviceTypes', '服务类型', 'checkbox-group', { options: serviceTypes, defaultValue: [] }),
      field('serviceForm', '服务形式', 'select', { options: ['请选择', '8', '10', '12', '24'], defaultValue: '请选择' }),
      field('practiceType', '执业类型', 'select', { options: practitionerTypes, defaultValue: '月嫂' }),
      field('startDate', '服务开始时间', 'date', { readonly: true }),
      field('endDate', '服务结束时间', 'date'),
      field('days', '服务天数', 'number'),
      field('note', '备注说明', 'textarea')
    ]
  }
]

const settlementFormSections = [
  {
    title: '月嫂服务结算',
    fields: [
      field('settlementType', '结算方式', 'select', { options: ['- 请选择 -', '- 护理师工资 -', '- 薪酬标准 -'], defaultValue: '- 请选择 -' }),
      field('serviceType', '服务类型', 'select', { options: serviceTypes, defaultValue: '会所入住' }),
      field('serviceForm', '服务形式', 'select', { options: ['8', '10', '12', '24'], defaultValue: '8' }),
      field('serviceStart', '服务开始', 'date'),
      field('serviceEnd', '服务结束', 'date'),
      field('duration', '工作时长', 'number'),
      field('leave', '休假请假', 'number', { defaultValue: '0' }),
      field('renewalReward', '续单奖励', 'number', { defaultValue: '0' }),
      field('signReward', '签单奖励', 'number', { defaultValue: '0' }),
      field('bannerReward', '锦旗奖励', 'number', { defaultValue: '0' }),
      field('otherReward', '其他奖励', 'number', { defaultValue: '0' }),
      field('multipleBirthReward', '多胎奖励', 'number', { defaultValue: '0' }),
      field('continuousOrderReward', '连续上单/顶单', 'number', { defaultValue: '0' }),
      field('certificateReward', '证书/工龄', 'number', { defaultValue: '0' }),
      field('praiseReward', '好评奖励', 'number', { defaultValue: '0' }),
      field('penalty', '惩罚金额', 'number', { defaultValue: '0' }),
      field('socialSecurity', '社保金额', 'number', { defaultValue: '0' }),
      field('serviceScore', '服务打分', 'number', { defaultValue: '0' }),
      field('serviceAmount', '服务金额', 'number'),
      field('motherOnly', '只护理妈妈', 'checkbox', { defaultValue: false }),
      field('tripleSalary', '3倍工资', 'checkbox', { defaultValue: false }),
      field('tripleSalaryHours', '3倍加班时长', 'number'),
      field('tripleSalaryAmount', '3倍工资金额', 'number'),
      field('doubleSalary', '2倍工资', 'checkbox', { defaultValue: false }),
      field('doubleSalaryHours', '2倍加班时长', 'number'),
      field('doubleSalaryAmount', '2倍工资金额', 'number'),
      field('abnormalLeave', '是否非正常离职', 'checkbox', { defaultValue: false }),
      field('finalAmount', '最终金额', 'number'),
      field('settlementLevel', '结算等级', 'select', { options: ['初级月嫂', '中级月嫂', '高级月嫂'], defaultValue: '初级月嫂' }),
      field('note', '备注', 'textarea')
    ]
  }
]

const contractLineTabs = [
  {
    label: '产康项目',
    columns: columns(['项目编号', '项目名称', '项目类别', '折扣价', '单位', '数量', '总价', '功能'])
  },
  {
    label: '商品',
    columns: columns(['物料编码', '物料名称', '物料类别', '规格型号', '单位', '单价', '数量', '总价', '备注', '功能'])
  },
  {
    label: '卡类',
    columns: columns(['卡片编号', '卡片名称', '套餐总金额', '是否启用', '卡类别', '有效天数', '卡类型', '启用时间', '分店'])
  },
  {
    label: '赠送清单',
    columns: columns(['清单编号', '清单名称', '是否启用', '启用时间', '赠送物品'])
  }
]

const mainColumns = {
  月嫂档案: columns([
    '护理师编号', '护理师名称', '身份证号', '联系方式', '护理师年龄', '执业类型', '状态', '护理师等级',
    '服务类型', '入职时间', '工龄（月）', '所属分店', '是否显示', '录入人', '录入时间', '职员名称',
    '健康证到期', '护理师介绍人', '是否更新', '健康证是否过期', '操作'
  ]),
  薪酬标准: columns(['星级', '服务形式', '执业类型', '价格(元/小时)', '所属部门', '26日参考价', '员工类型', '服务类型']),
  月嫂档期: columns(['护理师名称', '联系方式', '档期情况']),
  月嫂合同: columns([
    '编号', '客户名称', '客户电话', '预产期', '预计上户时间', '预计下户时间', '最终成交金额', '未入账金额',
    '已收款', '欠款金额', '月嫂合同名称', '服务形式', '天数', '单天价格', '产康项目金额', '商品金额',
    '卡类销售金额', '是否赠送', '所属部门', '签单人', '签单时间', '介绍人', '介绍人电话', '审核状态',
    '审核人', '合同状态', '当前服务月嫂', '远程签约', '备注', '客户来源', '门店', '缴费信息', '审核记录'
  ]),
  月嫂服务记录: columns([
    '客户姓名', '房间号', '护理师名称', '手机号', '护理师等级', '形式(小时/天)', '已上户天数',
    '开始服务时间', '实际完成时间', '是否完成', '是否结算', '预计完成时间', '入住分店', '状态', '备注',
    '是否购买保险', '制单人', '服务类型', '下一审核节点', '派工审核', '来源', '月子合同号', '合同欠款',
    '护理师欠款', '执业类型', '录入时间', '附件', '操作'
  ]),
  月嫂派工审核: columns([
    '客户姓名', '房间号', '护理师名称', '手机号', '护理师等级', '服务形式(小时/天)', '收费标准', '工作天数',
    '工资金额', '参考工资', '续单奖励', '签单奖励', '锦旗奖励', '其它奖励', '惩罚金额', '开始服务时间',
    '完成时间', '是否完成', '预计完成时间', '入住分店', '状态', '备注', '服务类型', '下一审核节点',
    '审核状态', '审核记录'
  ]),
  月嫂结算列表: columns([
    '护理师名称', '手机号', '结算等级', '客户姓名', '合同开始时间', '合同结束时间', '合同金额', '合同天数',
    '服务类型', '服务开始', '服务结束', '时长', '休假', '单位', '天数', '续单奖励', '签单奖励',
    '锦旗奖励', '其它奖励', '多胎奖励', '连续上单/顶单', '证书/工龄', '好评奖励', '服务打分',
    '惩罚金额', '社保金额', '参考工资', '只护理妈妈', '3倍工资', '2倍工资', '3倍加班时长',
    '2倍加班时长', '是否非正常离职', '最终金额', '备注', '录入时间', '录入人', '状态', '审核时间',
    '审核人', '审核意见', '分店'
  ]),
  月嫂预约记录: columns([
    '客户名称', '客户称呼', '电话号码', '预产期', '预约护理师', '护理师电话', '护理师类型',
    '服务日期', '天数', '预约分店', '录入日期', '备注', '客户地址'
  ])
}

const page = (key, mode, originalPath, navid, extra = {}) => ({
  key,
  mode,
  originalUrl: `http://qd.mm.hxqt.cn/${originalPath}?navid=${navid}`,
  navid,
  menuVerified: true,
  internalVerified: true,
  actions: [],
  filters: [],
  queryActions: [],
  columns: [],
  formFields: [],
  dialogFields: [],
  dependencies: [],
  completionLevel: 'Schema-faithful（工具栏/查询区/主列表）',
  verificationNote: '菜单、工具栏、查询区、下拉默认值和主列表可见列已按原 ERP 只读核验；本地业务写入保持 Mock。',
  ...extra
})

export const maternityNursePageOrder = [
  '月嫂档案',
  '薪酬标准',
  '月嫂档期',
  '月嫂合同',
  '月嫂服务记录',
  '月嫂派工审核',
  '月嫂结算列表',
  '月嫂预约记录'
]

export const maternityNursePageConfigs = {
  月嫂档案: page('maternity-matron-archives', 'list-form', 'Page/BasicInfo/MaternityMatronList.aspx', 422, {
    columns: mainColumns.月嫂档案,
    formTitle: '护理师档案',
    formSections: archiveFormSections,
    formActions: ['保存', '关闭'],
    hint: '绿色表示健康证超期提醒',
    rowActions: ['服务照片', '证书', '体检报告', '学习经历', '工作经历', '视频']
  }),
  薪酬标准: page('maternity-salary-standards', 'list-form', 'Page/BasicInfo/MaternityPriceList.aspx', 588, {
    columns: mainColumns.薪酬标准,
    formTitle: '薪酬标准',
    formSections: salaryFormSections,
    formActions: ['保存', '关闭']
  }),
  月嫂档期: page('maternity-schedules', 'schedule', 'Page/BasicInfo/TimeManagement.aspx', 593, {
    columns: mainColumns.月嫂档期,
    formTitle: '月嫂档期',
    formSections: scheduleFormSections,
    formActions: ['保存', '关闭'],
    scheduleLegend: [
      { label: '空闲中', color: '#e9f7ef' },
      { label: '预约中', color: '#fff3cd' },
      { label: '上户中', color: '#dceeff' },
      { label: '请假/休假', color: '#f6d8dc' },
      { label: '重叠', color: '#eadcf8' }
    ],
    selectionRules: { 添加: 'single' }
  }),
  月嫂合同: page('maternity-contracts', 'contract', 'Page/MaternityContract/ContractList.aspx', 599, {
    columns: mainColumns.月嫂合同,
    formTitle: '月嫂合同',
    formSections: contractFormSections,
    formActions: ['保存并提交', '暂 存', '重 置'],
    lineTabs: contractLineTabs,
    cellActions: { 审核记录: ['审批记录'] },
    selectionRules: {
      编辑: 'single',
      编辑模板: 'single',
      删除: 'single',
      打印: 'single',
      提交: 'single',
      审核: 'single',
      反审核: 'single',
      收款: 'single',
      月嫂派工: 'single',
      远程签约: 'single',
      修改预产期: 'single',
      更改时间: 'single'
    }
  }),
  月嫂服务记录: page('maternity-service-records', 'list-form', 'Page/NursingManager/MomServerLogList.aspx', 423, {
    columns: mainColumns.月嫂服务记录,
    formTitle: '月嫂服务记录',
    formSections: serviceRecordFormSections,
    formActions: ['确  定', '关  闭'],
    settlementTitle: '月嫂服务结算',
    settlementSections: settlementFormSections,
    settlementActions: ['查看服务详情', '确定', '取消', '提交'],
    rowActions: ['审核记录', '打卡记录'],
    selectionRules: {
      编辑: 'single',
      取消: 'single',
      上户: 'single',
      下户: 'single',
      重置: 'single',
      结算: 'single'
    }
  }),
  月嫂派工审核: page('maternity-dispatch-audits', 'list', 'Page/MaternityContract/MomServerLogSH.aspx', 666, {
    columns: mainColumns.月嫂派工审核,
    cellActions: { 审核记录: ['审批记录'] }
  }),
  月嫂结算列表: page('maternity-settlements', 'list', 'Page/NursingManager/MomServerSalary.aspx', 665, {
    columns: mainColumns.月嫂结算列表,
    selectionRules: { 删除: 'single' }
  }),
  月嫂预约记录: page('maternity-appointments', 'list', 'Page/MaternityContract/MaternityYYList.aspx', 641, {
    columns: mainColumns.月嫂预约记录
  })
}

applyAuditedSurfaceEvidence('matron', maternityNursePageConfigs)

Object.values(maternityNursePageConfigs).forEach(config => {
  config.internalVerified = true
  config.evidenceLevel = '工具栏、查询区、主列表与可打开新增表单已核验'
  config.completionLevel = 'Schema-faithful（列表表面）'
  config.evidenceNote = '顶部工具栏、查询字段、下拉全集、默认值、主列表可见列与可安全打开的新增表单来自原 ERP admin 只读证据；本地数据及写入动作仍为脱敏 Mock。'
})

export function getMaternityNursePageConfig(title) {
  return maternityNursePageConfigs[title] || maternityNursePageConfigs[maternityNursePageOrder[0]]
}
