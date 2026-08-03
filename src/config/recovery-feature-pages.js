const stores = ['奇德芬芳·建设路店（中心店）', '奇德芬芳·黄河路店']

const input = (key, label, required = false) => ({ key, label, type: 'input', required })
const select = (key, label, options, required = false) => ({ key, label, type: 'select', options, required })
const date = (key, label, required = false) => ({ key, label, type: 'date', required })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required })

export const recoveryFeaturePages = {
  '产康项目管理（疗程/套餐/卡项）': {
    key: 'recovery-programs', kind: 'catalog', eyebrow: 'F099 · 产康项目管理', title: '产康项目与卡项',
    description: '维护单项、疗程、套餐和次卡的销售状态、适用人群与服务次数。',
    actions: ['新增项目', '上架项目', '停用项目'],
    filters: [input('programName', '项目名称'), select('category', '项目类别', ['单项', '疗程', '套餐', '次卡']), select('status', '项目状态', ['草稿', '已上架', '已停用'])],
    columns: ['programName', 'category', 'sessions', 'price', 'validity', 'store', 'status'],
    formFields: [input('programName', '项目名称', true), select('category', '项目类别', ['单项', '疗程', '套餐', '次卡'], true), input('sessions', '服务次数', true), input('price', '售价', true), input('validity', '有效期', true), select('store', '适用门店', stores, true), textarea('remark', '销售说明')]
  },
  '产康预约与排班': {
    key: 'recovery-schedule', kind: 'schedule', eyebrow: 'F100 · 产康预约与排班', title: '产康预约排班',
    description: '按门店、产康师与时间段管理预约容量，实时识别冲突并推进到店服务。',
    actions: ['新增预约', '确认预约', '开始服务', '完成服务', '改期'],
    filters: [input('customerName', '客户姓名'), input('technician', '产康师'), select('store', '门店', stores), select('status', '预约状态', ['待确认', '已确认', '服务中', '已完成'])],
    columns: ['appointmentNo', 'appointmentDate', 'timePeriod', 'customerName', 'programName', 'technician', 'store', 'status'],
    formFields: [input('customerName', '客户姓名', true), input('programName', '服务项目', true), input('technician', '产康师', true), select('store', '服务门店', stores, true), date('appointmentDate', '预约日期', true), input('timePeriod', '预约时段', true), textarea('remark', '备注')]
  },
  '产后评估记录': {
    key: 'postpartum-assessments', kind: 'assessment', eyebrow: 'F101 · 产后评估记录', title: '产后评估档案',
    description: '以评估量表记录腹直肌、骨盆、疼痛与体态结果，形成项目建议和复测计划。',
    actions: ['新增评估', '提交复核', '生成方案'],
    filters: [input('customerName', '客户姓名'), input('assessor', '评估师'), select('riskLevel', '风险等级', ['低', '中', '高']), select('status', '评估状态', ['待评估', '已完成', '待复核'])],
    columns: ['assessmentNo', 'customerName', 'assessedAt', 'assessor', 'coreScore', 'pelvisScore', 'painScore', 'riskLevel', 'status'],
    formFields: [input('customerName', '客户姓名', true), select('store', '评估门店', stores, true), input('assessor', '评估师', true), date('assessedAt', '评估日期', true), input('coreScore', '腹直肌结果', true), input('pelvisScore', '骨盆结果', true), input('painScore', '疼痛评分', true), select('riskLevel', '风险等级', ['低', '中', '高'], true), textarea('recommendation', '项目建议', true)]
  },
  '产康服务记录与效果跟踪': {
    key: 'recovery-service-tracking', kind: 'tracking', eyebrow: 'F102 · 产康服务记录与效果跟踪', title: '服务效果跟踪',
    description: '记录每次服务的执行结果、客户反馈和前后指标变化，支持按疗程追踪效果。',
    actions: ['新增服务记录', '开始服务', '完成服务', '记录反馈'],
    filters: [input('customerName', '客户姓名'), input('programName', '服务项目'), input('technician', '产康师'), select('status', '服务状态', ['待执行', '服务中', '已完成'])],
    columns: ['recordNo', 'customerName', 'programName', 'serviceDate', 'technician', 'beforeValue', 'afterValue', 'feedback', 'status'],
    formFields: [input('customerName', '客户姓名', true), select('store', '服务门店', stores, true), input('programName', '服务项目', true), input('technician', '产康师', true), date('serviceDate', '服务日期', true), input('beforeValue', '服务前指标'), input('afterValue', '服务后指标'), textarea('feedback', '客户反馈')]
  },
  '产康门店经营看板': {
    key: 'recovery-store-dashboard', kind: 'dashboard', eyebrow: 'F103 · 产康门店经营看板', title: '产康门店经营看板',
    description: '聚合预约、到店、完成、收入与复购指标，帮助店长快速识别经营机会。',
    actions: ['导出经营摘要', '打印看板'], filters: [select('store', '门店', stores), select('period', '统计周期', ['今日', '本周', '本月'])],
    columns: ['store', 'period', 'appointments', 'completed', 'revenue', 'repurchaseRate', 'topProgram', 'alert']
  },
  '产康二次销售与升单': {
    key: 'recovery-upsell', kind: 'upsell', eyebrow: 'F104 · 产康二次销售与升单', title: '产康升单机会台',
    description: '根据剩余次数、效果反馈和客户需求识别升单机会，跟进推荐结果与成交状态。',
    actions: ['新增机会', '记录跟进', '推荐方案', '标记成交'],
    filters: [input('customerName', '客户姓名'), input('currentProgram', '当前项目'), select('opportunityStatus', '机会状态', ['待跟进', '跟进中', '已成交', '暂不考虑'])],
    columns: ['opportunityNo', 'customerName', 'currentProgram', 'remainingSessions', 'recommendation', 'owner', 'nextFollowUp', 'opportunityStatus'],
    formFields: [input('customerName', '客户姓名', true), select('store', '业务门店', stores, true), input('currentProgram', '当前项目', true), input('remainingSessions', '剩余次数', true), input('recommendation', '推荐方案', true), input('owner', '跟进人', true), date('nextFollowUp', '下次跟进日', true), textarea('note', '沟通记录')]
  },
  '产康耗材与设备管理': {
    key: 'recovery-assets', kind: 'assets', eyebrow: 'F105 · 产康耗材与设备管理', title: '产康耗材设备台账',
    description: '维护设备保养、耗材批次与领用状态，服务完成后可追溯到具体设备和物料。',
    actions: ['新增设备/耗材', '领用登记', '发起报修', '盘点完成'],
    filters: [input('assetName', '设备/耗材名称'), select('assetType', '类型', ['设备', '耗材']), select('assetStatus', '状态', ['在用', '低库存', '维修中', '已停用'])],
    columns: ['assetNo', 'assetName', 'assetType', 'specification', 'quantity', 'store', 'lastMaintenance', 'assetStatus'],
    formFields: [input('assetName', '设备/耗材名称', true), select('assetType', '类型', ['设备', '耗材'], true), input('specification', '规格型号', true), input('quantity', '数量', true), select('store', '所属门店', stores, true), date('lastMaintenance', '最近保养日'), textarea('remark', '备注')]
  },
  '产康师绩效与排班': {
    key: 'recovery-staff-performance', kind: 'performance', eyebrow: 'F106 · 产康师绩效与排班', title: '产康师绩效排班',
    description: '结合排班容量、服务完成、客户评分和升单结果查看产康师工作负荷与绩效。',
    actions: ['新增排班', '调整排班', '确认绩效'],
    filters: [input('technician', '产康师'), select('store', '门店', stores), select('shiftStatus', '排班状态', ['出勤', '休息', '请假']), select('period', '统计周期', ['本周', '本月'])],
    columns: ['technician', 'store', 'shiftDate', 'shiftPeriod', 'completedCount', 'rating', 'upsellAmount', 'shiftStatus'],
    formFields: [input('technician', '产康师', true), select('store', '所属门店', stores, true), date('shiftDate', '排班日期', true), input('shiftPeriod', '班次时段', true), input('capacity', '可预约人数', true), select('shiftStatus', '排班状态', ['出勤', '休息', '请假'], true)]
  }
}

export function getRecoveryFeaturePageConfig(title) {
  const featureAliases = {
    产康项目管理: '产康项目管理（疗程/套餐/卡项）'
  }
  return recoveryFeaturePages[featureAliases[title] || title] || null
}
