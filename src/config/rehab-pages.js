import { applyOriginalEvidence } from './original-page-evidence'
import { applyAuditedSurfaceEvidence } from './audited-surface-adapter'
import { serviceListColumns, serviceOverviewEvidence } from './rehab-service-overview'

const stores = ['中心广场旗舰店', '黄河路轻奢店']
const serviceStatuses = ['待预约', '已预约', '待服务', '服务中', '已完成', '已取消']
const customerStatuses = ['未入住', '已订房', '正入住', '已退房']

const input = (key, label, required = false) => ({ key, label, type: 'input', required })
const select = (key, label, options, required = false) => ({ key, label, type: 'select', options, required })
const date = (key, label, required = false) => ({ key, label, type: 'date', required })
const dateRange = (key, label) => ({ key, label, type: 'dateRange' })
const number = (key, label, required = false) => ({ key, label, type: 'number', required })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required })
const col = (key, label, width, tag = false) => ({ key, label, width, tag })

const bookingFields = [
  input('customerName', '客户姓名', true),
  input('mobile', '联系电话'),
  select('store', '服务门店', stores, true),
  select('serviceCategory', '服务类别', ['产后修复', '身体护理', '仪器项目', '健康评估'], true),
  input('serviceItem', '服务项目', true),
  input('technician', '服务人员'),
  date('appointmentDate', '预约日期', true),
  input('appointmentPeriod', '预约时段', true),
  number('serviceCount', '服务次数'),
  textarea('remark', '预约备注')
]

const completionFields = [
  date('serviceDate', '服务日期', true),
  input('servicePeriod', '服务时段', true),
  input('technician', '执行人员', true),
  number('usedCount', '本次耗卡次数', true),
  textarea('serviceResult', '服务结果', true),
  textarea('customerFeedback', '客户反馈')
]

const assessmentFields = [
  input('customerName', '客户姓名', true),
  select('store', '评估门店', stores, true),
  date('assessedAt', '评估日期', true),
  input('assessor', '评估人员', true),
  input('assessmentType', '评估类型', true),
  input('mainConcern', '主要诉求'),
  textarea('assessmentResult', '评估结果', true),
  textarea('recommendation', '项目建议'),
  textarea('contraindication', '禁忌及注意事项')
]

export const rehabPageConfigs = {
  未预约客户服务: {
    key: 'unbooked-customer-services',
    mode: 'list',
    description: '查看已有可用服务但尚未安排预约的客户。',
    actions: ['预约'],
    filters: [
      input('customerName', '客户姓名'), input('mobile', '联系电话'),
      select('store', '门店', stores), select('customerStatus', '客户状态', customerStatuses),
      input('serviceItem', '服务项目'), dateRange('validRange', '有效日期')
    ],
    columns: [
      col('customerName', '客户姓名', 110), col('mobile', '联系电话', 130),
      col('room', '房间号', 90), col('store', '所属门店', 150),
      col('customerStatus', '客户状态', 100, true), col('serviceItem', '服务项目', 180),
      col('totalCount', '项目总次数', 105), col('usedCount', '已使用次数', 105),
      col('remainingCount', '剩余次数', 95), col('validUntil', '有效期至', 115),
      col('salesDocumentNo', '销售单号', 150)
    ],
    formFields: bookingFields
  },
  服务预约列表: {
    key: 'service-appointments',
    mode: 'list',
    description: '管理产康服务预约、预约确认、执行和取消状态。',
    actions: ['添加', '编辑', '删除', '预约确认', '开始服务', '完成服务', '取消'],
    filters: [
      input('customerName', '客户姓名'), input('mobile', '联系电话'),
      select('store', '门店', stores), input('serviceItem', '服务项目'),
      input('technician', '服务人员'), select('serviceStatus', '服务状态', serviceStatuses),
      dateRange('appointmentRange', '预约日期')
    ],
    columns: [
      col('appointmentNo', '预约单号', 150), col('customerName', '客户姓名', 110),
      col('mobile', '联系电话', 130), col('room', '房间号', 90), col('store', '服务门店', 150),
      col('serviceItem', '服务项目', 180), col('appointmentDate', '预约日期', 115),
      col('appointmentPeriod', '预约时段', 115), col('technician', '服务人员', 105),
      col('serviceStatus', '服务状态', 100, true), col('createdBy', '预约人', 100),
      col('createdAt', '预约时间', 155), col('remark', '备注', 180)
    ],
    formFields: bookingFields,
    completionFields
  },
  服务综合查询: {
    key: 'service-overview-query',
    mode: 'service-overview',
    description: '按会员卡或客户查看四类可用服务，并可切换到综合列表模式按客户、项目、产康师、次数、类别、门店和状态查询。',
    actions: [],
    filters: [],
    columns: serviceListColumns
  },
  服务人员任务表: {
    key: 'staff-task-board',
    mode: 'task-board',
    description: '汇总服务人员在指定日期的预约、待执行与已完成任务。',
    actions: ['导出', '打印'],
    filters: [
      select('store', '门店', stores), input('staffName', '服务人员'),
      input('serviceItem', '服务项目'), date('taskDate', '任务日期'),
      select('taskStatus', '任务状态', ['待执行', '执行中', '已完成', '已取消'])
    ],
    columns: [
      col('staffName', '服务人员', 110), col('department', '所属部门', 120),
      col('taskDate', '任务日期', 115), col('timePeriod', '服务时段', 110),
      col('customerName', '客户姓名', 110), col('room', '房间号', 90),
      col('serviceItem', '服务项目', 180), col('taskStatus', '任务状态', 100, true),
      col('servicePlace', '服务地点', 130), col('remark', '备注', 180)
    ]
  },
  人员排班设置: {
    key: 'staff-schedule-settings',
    mode: 'schedule',
    description: '设置产康服务人员的日期、班次、可预约时段和休息状态。',
    actions: ['添加排班', '复制排班', '删除'],
    filters: [
      select('store', '门店', stores), input('staffName', '服务人员'),
      dateRange('scheduleRange', '排班日期'), select('shiftStatus', '排班状态', ['出勤', '休息', '请假', '停诊'])
    ],
    columns: [
      col('staffName', '服务人员', 110), col('jobTitle', '岗位', 110),
      col('store', '所属门店', 150), col('scheduleDate', '排班日期', 115),
      col('shiftName', '班次', 95), col('startTime', '开始时间', 95),
      col('endTime', '结束时间', 95), col('maxBookings', '可预约人数', 105),
      col('bookedCount', '已预约人数', 105), col('shiftStatus', '排班状态', 100, true),
      col('remark', '备注', 180)
    ],
    formFields: [
      input('staffName', '服务人员', true), select('store', '所属门店', stores, true),
      date('scheduleDate', '排班日期', true), input('shiftName', '班次', true),
      input('startTime', '开始时间', true), input('endTime', '结束时间', true),
      number('maxBookings', '可预约人数'), select('shiftStatus', '排班状态', ['出勤', '休息', '请假', '停诊'], true),
      textarea('remark', '备注')
    ]
  },
  技师人员任务表: {
    key: 'technician-task-board',
    mode: 'task-board',
    description: '按技师查看预约项目、服务时段、执行状态和耗卡信息。',
    actions: ['导出', '打印', '完成服务'],
    filters: [
      select('store', '门店', stores), input('technician', '技师'),
      input('serviceItem', '服务项目'), dateRange('taskRange', '任务日期'),
      select('taskStatus', '任务状态', ['待执行', '执行中', '已完成', '已取消'])
    ],
    columns: [
      col('technician', '技师', 105), col('taskDate', '任务日期', 115),
      col('timePeriod', '服务时段', 110), col('customerName', '客户姓名', 110),
      col('room', '房间号', 90), col('serviceItem', '服务项目', 180),
      col('serviceCount', '项目次数', 90), col('usedCount', '本次耗卡', 90),
      col('taskStatus', '任务状态', 100, true), col('servicePlace', '服务地点', 130),
      col('remark', '备注', 180)
    ],
    completionFields
  },
  客户服务查询: {
    key: 'customer-service-query',
    mode: 'list',
    description: '以客户为主线查询购买项目、预约、执行和剩余次数。',
    actions: ['查看详情', '导出'],
    filters: [
      input('customerName', '客户姓名'), input('mobile', '联系电话'),
      select('store', '所属门店', stores), select('customerStatus', '客户状态', customerStatuses),
      input('serviceItem', '服务项目'), select('serviceStatus', '服务状态', serviceStatuses)
    ],
    columns: [
      col('customerName', '客户姓名', 110), col('mobile', '联系电话', 130),
      col('room', '房间号', 90), col('store', '所属门店', 150),
      col('customerStatus', '客户状态', 100, true), col('serviceItem', '服务项目', 180),
      col('totalCount', '购买次数', 95), col('bookedCount', '预约次数', 95),
      col('usedCount', '完成次数', 95), col('remainingCount', '剩余次数', 95),
      col('lastServiceAt', '最近服务日期', 125), col('nextAppointmentAt', '下次预约日期', 125)
    ]
  },
  产康服务记录表: {
    key: 'rehab-service-records',
    mode: 'list',
    description: '查询产康项目的实际执行人员、耗卡次数与服务结果。',
    actions: ['添加', '编辑', '删除', '导出', '打印'],
    filters: [
      input('customerName', '客户姓名'), input('mobile', '联系电话'), select('store', '服务门店', stores),
      input('serviceItem', '服务项目'), input('technician', '服务人员'), dateRange('serviceRange', '服务日期')
    ],
    columns: [
      col('recordNo', '服务记录号', 150), col('customerName', '客户姓名', 110),
      col('mobile', '联系电话', 130), col('room', '房间号', 90), col('store', '服务门店', 150),
      col('serviceItem', '服务项目', 180), col('serviceDate', '服务日期', 115),
      col('servicePeriod', '服务时段', 110), col('technician', '服务人员', 105),
      col('usedCount', '耗卡次数', 90), col('serviceResult', '服务结果', 200),
      col('createdBy', '记录人', 100), col('createdAt', '记录时间', 155)
    ],
    formFields: completionFields
  },
  完成项目消耗表: {
    key: 'completed-service-consumption',
    mode: 'list',
    description: '统计已完成项目的服务次数、物料消耗和库存扣减结果。',
    actions: ['导出'],
    filters: [
      input('customerName', '客户姓名'), select('store', '服务门店', stores),
      input('serviceItem', '服务项目'), input('materialName', '消耗物料'),
      input('technician', '服务人员'), dateRange('serviceRange', '完成日期')
    ],
    columns: [
      col('documentNo', '消耗单号', 150), col('customerName', '客户姓名', 110),
      col('store', '服务门店', 150), col('serviceItem', '完成项目', 180),
      col('completedAt', '完成日期', 125), col('technician', '服务人员', 105),
      col('usedCount', '耗卡次数', 90), col('materialName', '消耗物料', 160),
      col('materialQuantity', '消耗数量', 95), col('unit', '单位', 70),
      col('warehouse', '扣减仓库', 130), col('stockStatus', '库存状态', 100, true)
    ]
  },
  产康健康评估: {
    key: 'rehab-health-assessments',
    mode: 'list',
    description: '维护客户产康健康评估、主要诉求、项目建议及注意事项。',
    actions: ['添加', '编辑', '删除', '打印'],
    filters: [
      input('customerName', '客户姓名'), input('mobile', '联系电话'),
      select('store', '评估门店', stores), input('assessmentType', '评估类型'),
      input('assessor', '评估人员'), dateRange('assessmentRange', '评估日期')
    ],
    columns: [
      col('assessmentNo', '评估单号', 150), col('customerName', '客户姓名', 110),
      col('mobile', '联系电话', 130), col('store', '评估门店', 150),
      col('assessmentType', '评估类型', 130), col('assessedAt', '评估日期', 115),
      col('assessor', '评估人员', 105), col('mainConcern', '主要诉求', 180),
      col('assessmentResult', '评估结果', 220), col('recommendation', '项目建议', 200),
      col('createdAt', '录入时间', 155)
    ],
    formFields: assessmentFields
  }
}

applyOriginalEvidence('recovery', rehabPageConfigs)
applyAuditedSurfaceEvidence('recovery', rehabPageConfigs)
Object.assign(rehabPageConfigs.服务综合查询, {
  mode: 'service-overview',
  actions: [],
  filters: [],
  columns: serviceListColumns,
  evidenceLevel: '双模式字段级核验',
  completionLevel: serviceOverviewEvidence.completionLevel,
  evidenceNote: '已核验图形/列表模式、会员卡与客户选择区、四类服务列表、综合筛选项、下拉全集和结果表头。',
  internalVerified: true
})

export function getRehabPageConfig(title) {
  return rehabPageConfigs[title] || rehabPageConfigs.未预约客户服务
}
