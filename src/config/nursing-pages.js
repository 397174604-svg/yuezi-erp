import { applyOriginalEvidence } from './original-page-evidence'

const stores = ['中心广场旗舰店', '黄河路轻奢店']

const input = (key, label, placeholder = '') => ({ key, label, type: 'input', placeholder, verified: false })
const select = (key, label, options) => ({ key, label, type: 'select', options, verified: false })
const dateRange = (key, label) => ({ key, label, type: 'dateRange', verified: false })
const checkbox = (key, label, text = '') => ({ key, label, text, type: 'checkbox', verified: false })
const col = (key, label, width, tag = false) => ({ key, label, width, tag, verified: false })
const toolbarAction = (label, icon, selection = 'none', kind = 'dialog') => ({
  label,
  icon,
  selection,
  kind,
  verified: true
})

const commonCustomerFilters = [
  input('room', '房间号'),
  input('customerName', '客户姓名'),
  select('store', '门店', stores)
]

const storeOptions = ['-全部-', ...stores]
const inHouseStatusOptions = ['- 请选择 -', '- 已入住 -', '- 已出院 -']
const scheduleTypeOptions = ['护理排班', '行政排班', '其他排班']

const formatLocalDate = value => {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
const offsetDate = days => {
  const value = new Date()
  value.setDate(value.getDate() + days)
  return formatLocalDate(value)
}

const commonMeta = {
  evidenceLevel: '待原系统二次核验',
  completionLevel: 'Visible',
  originalUrl: '',
  actions: [],
  queryActions: ['查询'],
  evidenceNote: '菜单名称已由仓库菜单证据确认；筛选项、列、按钮、默认值和交互为业务链路预置草案，尚未从原页面核验。'
}

const withMeta = config => ({ ...commonMeta, ...config })

export const nursingPageConfigs = {
  护理中心: withMeta({
    key: 'nursing-center',
    mode: 'care-center',
    icon: 'el-icon-s-data',
    description: '按原妈妈宝盒护理中心展示在住统计、护理风险和楼层客户护理卡片。',
    evidenceLevel: '原系统已核验（2026-07-24）',
    completionLevel: '业务闭环已接入',
    originalUrl: 'Page/NurseManagerNew/NursingCenterList.aspx?navid=571',
    evidenceNote: '页面结构、门店、护理等级、20项统计、会所/到家、护理情况筛选、客户卡片及操作入口已核验。',
    actions: [],
    queryActions: [],
    filters: [],
    columns: []
  }),
  护理计划: withMeta({
    key: 'nursing-plan',
    mode: 'list',
    icon: 'el-icon-s-order',
    description: '按入住客户编排妈妈与宝宝护理项目。',
    evidenceLevel: '主页面及顶部工具栏已核验（2026-07-24）',
    completionLevel: 'Schema-faithful / Interaction-faithful（Mock）',
    evidenceNote: '原页顶部工具栏、筛选、默认值、主表列及八个按钮的选择规则/目标页已核验；本地操作均为脱敏 Mock。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('新增宝宝', 'el-icon-user', 'single'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('设置', 'el-icon-setting', 'single'),
      toolbarAction('月嫂分配', 'el-icon-s-custom', 'single'),
      toolbarAction('移动', 'el-icon-rank', 'single'),
      toolbarAction('确认完成', 'el-icon-check', 'multiple')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      input('room', '房间号'),
      select('store', '门店类别', ['-全部-', ...stores]),
      select('customerStatus', '客户状态', ['- 请选择 -', '- 已入住 -', '- 未入住 -', '- 已退房 -']),
      select('deliveryMode', '分娩方式', ['-请选择-', '顺产分娩', '剖宫产分娩', '小月子', '未生产'])
    ],
    defaults: {
      store: '-全部-',
      customerStatus: '- 已入住 -',
      deliveryMode: '-请选择-'
    },
    columns: [
      col('customerName', '客户姓名', 110), col('babyAlias', '宝宝姓名', 110),
      col('deliveryMode', '分娩方式', 100), col('room', '房间号', 90), col('checkInDate', '入住日期', 110),
      col('nursingDirector', '护理总监', 110), col('nursingManager', '护理主任', 110),
      col('housekeeper', '生活管家', 110), col('gyneDoctor', '妇科保健医师', 120),
      col('pediatricDoctor', '儿科保健医师', 120), col('rehabNurse', '产后康复', 110),
      col('headNurse', '责任护士(长)', 120), col('feedingSpecialist', '母婴喂养师', 120),
      col('nutritionist', '营养师', 100), col('creator', '录单人', 100),
      col('createdAt', '录单日期', 150), col('store', '分店', 150),
      col('matronName', '分配月嫂', 110), col('planSheet', '护理计划单', 110)
    ]
  }),
  护理部排班第二版: withMeta({
    key: 'nursing-roster-v2',
    mode: 'schedule',
    icon: 'el-icon-date',
    description: '按周查看护理人员班次安排。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('打印', 'el-icon-printer', 'none', 'print'),
      toolbarAction('批量新增', 'el-icon-document-add')
    ],
    queryActions: ['查询'],
    filters: [select('scheduleType', '排班类型', scheduleTypeOptions)],
    defaults: { scheduleType: '护理排班' },
    columns: [
      col('employeeName', '护理人员', 110), col('department', '部门', 110), col('monday', '星期一', 120),
      col('tuesday', '星期二', 120), col('wednesday', '星期三', 120), col('thursday', '星期四', 120),
      col('friday', '星期五', 120), col('saturday', '星期六', 120), col('sunday', '星期日', 120),
      col('totalShifts', '班次合计', 100)
    ]
  }),
  宝宝档案: withMeta({
    key: 'baby-files',
    mode: 'list',
    icon: 'el-icon-user',
    description: '维护宝宝入住期间的基础档案与护理关联信息。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('导出', 'el-icon-download', 'none', 'export')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      input('babyAlias', '宝宝姓名'),
      input('room', '房间号'),
      select('customerStatus', '客户状态', ['- 请选择 -', '- 已入住 -', '- 未入住 -', '- 已退房 -', '- 散客 -']),
      select('store', '分店名称', storeOptions),
      dateRange('createdRange', '添加时间')
    ],
    defaults: {
      customerStatus: '- 已入住 -',
      store: '-全部-'
    },
    columns: [
      col('babyCode', '宝宝编号', 140), col('babyAlias', '宝宝称呼', 110), col('gender', '性别', 80),
      col('birthDate', '出生日期', 110), col('birthTime', '出生时间', 100), col('gestationalWeek', '孕周', 90),
      col('birthWeight', '出生体重', 100), col('deliveryMode', '分娩方式', 100), col('customerName', '妈妈姓名', 110),
      col('room', '房间号', 90), col('store', '门店', 150), col('archiveStatus', '档案状态', 100, true)
    ]
  }),
  健康评估: withMeta({
    key: 'health-assessments',
    mode: 'list',
    icon: 'el-icon-first-aid-kit',
    description: '记录妈妈和宝宝的健康评估结果。',
    actionPlacement: 'query-inline',
    actions: [
      toolbarAction('产妇入住评估新增', 'el-icon-plus'),
      toolbarAction('宝宝入住评估新增', 'el-icon-plus'),
      toolbarAction('产妇回家评估新增', 'el-icon-plus'),
      toolbarAction('宝宝回家评估新增', 'el-icon-plus'),
      toolbarAction('母婴指导评估新增', 'el-icon-plus')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      input('babyAlias', '宝宝姓名'),
      input('room', '房间号'),
      select('store', '门店类别', storeOptions),
      select('customerStatus', '客户状态', inHouseStatusOptions)
    ],
    defaults: {
      store: '-全部-',
      customerStatus: '- 已入住 -'
    },
    columns: [
      col('assessmentNo', '评估编号', 150), col('customerName', '客户姓名', 110), col('target', '评估对象', 100),
      col('assessmentDate', '评估日期', 110), col('assessmentType', '评估类型', 140), col('riskLevel', '风险等级', 100, true),
      col('assessor', '评估人员', 110), col('summary', '评估结论', 220), col('followUp', '跟进建议', 200)
    ]
  }),
  膳食评估: withMeta({
    key: 'diet-assessments',
    mode: 'list',
    icon: 'el-icon-dish',
    description: '记录客户膳食需求、禁忌和营养评估。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete')
    ],
    queryActions: ['搜  索'],
    filters: [input('customerName', '客户姓名'), input('room', '房间号')],
    columns: [
      col('assessmentNo', '评估编号', 150), col('customerName', '客户姓名', 110), col('room', '房间号', 90),
      col('assessmentDate', '评估日期', 110), col('dietType', '膳食类型', 120), col('tabooSummary', '饮食禁忌', 180),
      col('nutritionGoal', '营养目标', 180), col('assessor', '评估人员', 110), col('status', '评估状态', 100, true)
    ]
  }),
  自定义查房: withMeta({
    key: 'custom-rounds',
    mode: 'list',
    icon: 'el-icon-document-checked',
    description: '按自定义查房模板登记执行记录。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('护士回复', 'el-icon-chat-dot-round', 'single')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      input('room', '房间号'),
      select('roundType', '查房类型', ['-请选择-', '妇科', '儿科', '中医', '营养师', '客房管家查房', '专家查房']),
      select('store', '门店类别', storeOptions),
      select('customerStatus', '客户状态', inHouseStatusOptions),
      dateRange('roundRange', '查房时间')
    ],
    defaults: {
      roundType: '-请选择-',
      store: '-全部-',
      customerStatus: '- 已入住 -'
    },
    columns: [
      col('roundNo', '查房编号', 150), col('roundDate', '查房日期', 110), col('room', '房间号', 90),
      col('customerName', '客户姓名', 110), col('roundType', '查房类型', 130), col('templateName', '查房模板', 150),
      col('rounder', '查房人员', 110), col('result', '查房结果', 200), col('status', '状态', 100, true)
    ]
  }),
  医生查房记录: withMeta({
    key: 'doctor-rounds',
    mode: 'list',
    icon: 'el-icon-notebook-2',
    description: '登记医生查房时间、观察结果和处理建议。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('护士回复', 'el-icon-chat-dot-round', 'single'),
      toolbarAction('打印', 'el-icon-printer', 'single', 'print')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      input('babyAlias', '宝宝姓名'),
      input('room', '房间号'),
      select('roundType', '查房类型', ['-请选择-', '妇科', '儿科', '客房管家查房']),
      select('store', '门店类别', storeOptions),
      select('customerStatus', '客户状态', inHouseStatusOptions),
      select('exceptionStatus', '异常状态', ['- 请选择 -', '正常', '异常', '危险']),
      dateRange('roundRange', '查房时间')
    ],
    defaults: {
      roundType: '-请选择-',
      store: '-全部-',
      customerStatus: '- 已入住 -',
      exceptionStatus: '- 请选择 -'
    },
    columns: [
      col('roundDate', '查房日期', 110), col('room', '房间号', 90), col('customerName', '客户姓名', 110),
      col('target', '查房对象', 100), col('doctorName', '医生姓名', 110), col('observation', '观察记录', 220),
      col('advice', '处理建议', 220), col('recorder', '记录人', 100), col('recordedAt', '记录时间', 150)
    ]
  }),
  膳食禁忌查房: withMeta({
    key: 'diet-taboo-rounds',
    mode: 'list',
    icon: 'el-icon-warning-outline',
    description: '查核客户饮食禁忌及餐单执行情况。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('编辑', 'el-icon-edit', 'single')
    ],
    queryActions: ['搜  索'],
    filters: [input('customerName', '客户姓名'), input('room', '房间号')],
    columns: [
      col('roundDate', '查房日期', 110), col('room', '房间号', 90), col('customerName', '客户姓名', 110),
      col('tabooSummary', '饮食禁忌', 180), col('mealPlan', '当前餐单', 160), col('finding', '查房发现', 200),
      col('resultStatus', '查房结果', 100, true), col('rounder', '查房人员', 110), col('adjustment', '调整建议', 200)
    ]
  }),
  护理计划确认: withMeta({
    key: 'nursing-plan-confirmations',
    mode: 'list',
    icon: 'el-icon-circle-check',
    description: '确认护理计划内容与执行责任。',
    actions: [],
    queryActions: ['查询', '打印'],
    filters: [
      input('customerName', '客户姓名'),
      input('projectName', '项目名称'),
      select('store', '分店', ['-请选择-', ...stores])
    ],
    defaults: { store: '-请选择-' },
    columns: [
      col('planNo', '计划编号', 150), col('customerName', '客户姓名', 110), col('room', '房间号', 90),
      col('planDate', '计划日期', 110), col('projectCount', '护理项目数', 110), col('confirmStatus', '确认状态', 100, true),
      col('confirmer', '确认人', 100), col('confirmedAt', '确认时间', 150), col('remark', '备注', 180)
    ]
  }),
  护理项目记录: withMeta({
    key: 'nursing-project-records',
    mode: 'list',
    icon: 'el-icon-s-claim',
    description: '记录护理项目计划、执行、完成与异常。',
    actions: [
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('编辑', 'el-icon-edit', 'single')
    ],
    queryActions: ['搜  索', '导出'],
    filters: [
      input('customerName', '客户姓名'),
      input('babyAlias', '宝宝姓名'),
      input('projectName', '项目名称'),
      input('servicePerson', '服务人'),
      input('room', '房间号'),
      select('store', '分店名称', storeOptions),
      select('serviceType', '类型', ['-全部-', '套餐内', '套餐外', '额外购']),
      select('customerType', '客户状态', ['-全部-', '店内客户', '散客客户']),
      select('auditStatus', '审核状态', ['-全部-', '未审核', '已审核']),
      dateRange('completedRange', '完成日期')
    ],
    defaults: {
      store: '中心广场旗舰店',
      serviceType: '-全部-',
      customerType: '-全部-',
      auditStatus: '-全部-',
      completedRange: [offsetDate(-1), offsetDate(0)]
    },
    columns: [
      col('recordNo', '记录编号', 150), col('serviceDate', '服务日期', 110), col('serviceTime', '服务时间', 100),
      col('room', '房间号', 90), col('customerName', '客户姓名', 110), col('target', '护理对象', 100),
      col('projectName', '护理项目', 160), col('nurseName', '执行人员', 110), col('status', '执行状态', 110, true),
      col('result', '执行结果', 200), col('consumables', '耗用物料', 180)
    ]
  }),
  妈妈护理记录: withMeta({
    key: 'mother-nursing-records',
    mode: 'list',
    icon: 'el-icon-female',
    description: '记录妈妈护理项目、体征观察和护理结果。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('打印', 'el-icon-printer', 'single', 'print'),
      toolbarAction('产妇护理导出', 'el-icon-download', 'none', 'export')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      input('babyAlias', '宝宝姓名'),
      input('room', '房间号'),
      select('store', '门店类别', storeOptions),
      select('customerStatus', '客户状态', inHouseStatusOptions)
    ],
    defaults: {
      store: '-全部-',
      customerStatus: '- 已入住 -'
    },
    columns: [
      col('serviceDate', '护理日期', 110), col('serviceTime', '护理时间', 100), col('room', '房间号', 90),
      col('customerName', '客户姓名', 110), col('projectName', '护理项目', 160), col('vitalSummary', '体征摘要', 180),
      col('careResult', '护理结果', 200), col('nurseName', '护理人员', 110), col('recordedAt', '记录时间', 150)
    ]
  }),
  宝宝护理记录: withMeta({
    key: 'baby-nursing-records',
    mode: 'list',
    icon: 'el-icon-s-custom',
    description: '记录宝宝喂养、睡眠、排便、体征与护理项目。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('打印', 'el-icon-printer', 'single', 'print')
    ],
    queryActions: ['搜  索', '导出'],
    filters: [
      input('customerName', '客户姓名'),
      input('babyAlias', '宝宝姓名'),
      input('room', '房间号'),
      select('store', '门店类别', storeOptions),
      select('customerStatus', '客户状态', inHouseStatusOptions),
      checkbox('homeCustomer', '', '到家客户')
    ],
    defaults: {
      store: '-全部-',
      customerStatus: '- 已入住 -',
      homeCustomer: false
    },
    columns: [
      col('serviceDate', '护理日期', 110), col('serviceTime', '护理时间', 100), col('room', '房间号', 90),
      col('babyCode', '宝宝编号', 140), col('projectName', '护理项目', 160), col('feedingSummary', '喂养摘要', 160),
      col('sleepSummary', '睡眠摘要', 160), col('excretionSummary', '排便摘要', 160), col('careResult', '护理结果', 200),
      col('nurseName', '护理人员', 110)
    ]
  }),
  妈妈护理汇总: withMeta({
    key: 'mother-nursing-summary',
    mode: 'summary',
    icon: 'el-icon-data-analysis',
    description: '按客户和时间区间汇总妈妈护理执行情况。',
    filters: [
      input('room', '房间号'),
      input('floor', '房间楼层'),
      input('customerName', '妈妈名称'),
      select('store', '门店', storeOptions),
      dateRange('recordRange', '记录日期'),
      checkbox('homeCustomer', '', '到家客户')
    ],
    actions: [],
    queryActions: ['查询', '导出', '打印'],
    defaults: {
      store: '-全部-',
      recordRange: [offsetDate(-1), offsetDate(0)],
      homeCustomer: false
    },
    columns: [
      col('customerName', '客户姓名', 110), col('room', '房间号', 90), col('store', '门店', 150),
      col('plannedCount', '计划项目数', 110), col('completedCount', '已完成数', 100), col('exceptionCount', '异常数', 90),
      col('completionRate', '完成率', 100), col('lastServiceAt', '最后护理时间', 150), col('primaryNurse', '责任护士', 110)
    ]
  }),
  宝宝护理汇总: withMeta({
    key: 'baby-nursing-summary',
    mode: 'summary',
    icon: 'el-icon-pie-chart',
    description: '按宝宝和时间区间汇总护理、喂养及体征记录。',
    filters: [...commonCustomerFilters, input('babyCode', '宝宝编号'), dateRange('summaryRange', '统计日期')],
    actions: [],
    queryActions: ['查询', '导出', '打印'],
    columns: [
      col('babyCode', '宝宝编号', 140), col('room', '房间号', 90), col('customerName', '妈妈姓名', 110),
      col('careCount', '护理次数', 100), col('feedingCount', '喂养次数', 100), col('bathCount', '沐浴次数', 100),
      col('exceptionCount', '异常数', 90), col('lastWeight', '最近体重', 100), col('lastRecordedAt', '最后记录时间', 150)
    ]
  }),
  护理部排班表: withMeta({
    key: 'nursing-roster',
    mode: 'schedule',
    icon: 'el-icon-date',
    description: '查看护理部人员的日期、班次及负责区域。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('打印', 'el-icon-printer', 'none', 'print'),
      toolbarAction('设置', 'el-icon-setting')
    ],
    queryActions: ['查询'],
    filters: [
      select('scheduleDepartment', '排班部门', []),
      select('scheduleType', '排班类型', scheduleTypeOptions),
      dateRange('scheduleRange', '排班日期')
    ],
    defaults: {
      scheduleType: '护理排班',
      scheduleRange: [offsetDate(0), offsetDate(7)]
    },
    columns: [
      col('shiftDate', '排班日期', 110), col('employeeName', '护理人员', 110), col('department', '部门', 110),
      col('shiftName', '班次', 100), col('startTime', '开始时间', 100), col('endTime', '结束时间', 100),
      col('area', '负责区域', 130), col('roomRange', '负责房间', 160), col('status', '排班状态', 100, true)
    ]
  }),
  入住物品交接: withMeta({
    key: 'check-in-handover',
    mode: 'list',
    icon: 'el-icon-box',
    description: '记录入住物品清单、交接数量和双方确认。',
    actions: [
      toolbarAction('添加', 'el-icon-plus'),
      toolbarAction('编辑', 'el-icon-edit', 'single'),
      toolbarAction('删除', 'el-icon-delete', 'single', 'delete'),
      toolbarAction('确认签收', 'el-icon-circle-check', 'single')
    ],
    queryActions: ['搜  索'],
    filters: [
      input('customerName', '客户姓名'),
      select('receiveStatus', '接收状态', ['请选择', '接收', '送还']),
      dateRange('handoverRange', '交接时间范围')
    ],
    defaults: { receiveStatus: '请选择' },
    columns: [
      col('handoverNo', '交接单号', 150), col('handoverDate', '交接日期', 110), col('room', '房间号', 90),
      col('customerName', '客户姓名', 110), col('itemCount', '物品种类数', 110), col('plannedQuantity', '应交数量', 100),
      col('actualQuantity', '实交数量', 100), col('status', '交接状态', 100, true), col('handoverStaff', '交接人员', 110),
      col('customerConfirmation', '客户确认', 110, true), col('remark', '备注', 180)
    ]
  })
}

applyOriginalEvidence('nursing', nursingPageConfigs)

const verifiedToolbarTitles = [
  '护理计划',
  '护理部排班第二版',
  '宝宝档案',
  '健康评估',
  '膳食评估',
  '自定义查房',
  '医生查房记录',
  '膳食禁忌查房',
  '护理计划确认',
  '护理项目记录',
  '妈妈护理记录',
  '宝宝护理记录',
  '妈妈护理汇总',
  '护理部排班表',
  '入住物品交接'
]

verifiedToolbarTitles.forEach(title => {
  const config = nursingPageConfigs[title]
  config.toolbarEvidence = config.actionPlacement === 'query-inline'
    ? '原页查询区业务按钮已核验（2026-07-24）'
    : '原页顶部操作区已核验（2026-07-24）'
  config.evidenceLevel = title === '护理计划'
    ? '主页面及顶部工具栏已核验（2026-07-24）'
    : '菜单、URL 与顶部工具栏已核验'
  config.evidenceNote = title === '护理计划'
    ? '原页顶部工具栏、筛选、默认值、主表列及八个按钮的选择规则和目标页已核验；本地保存仅作用于脱敏 Mock。'
    : `原页操作区的按钮名称、顺序与所在层级已只读核验；${config.actionPlacement === 'query-inline' ? '业务按钮保留在查询区，' : config.actions.length ? '本地顶部按钮按原顺序呈现，' : '原页无独立业务工具栏，查询区按钮已单列，'}其余筛选、表格列和业务数据仍待逐字段核验。`
})

const verifiedQueryTitles = [
  '护理计划',
  '护理部排班第二版',
  '宝宝档案',
  '健康评估',
  '膳食评估',
  '自定义查房',
  '医生查房记录',
  '膳食禁忌查房',
  '护理计划确认',
  '护理项目记录',
  '妈妈护理记录',
  '宝宝护理记录',
  '妈妈护理汇总',
  '护理部排班表',
  '入住物品交接'
]

verifiedQueryTitles.forEach(title => {
  const config = nursingPageConfigs[title]
  config.queryEvidence = '原页主查询区已核验（2026-07-24）'
  config.filters = config.filters.map(field => ({ ...field, verified: true }))
  config.evidenceLevel = title === '护理计划'
    ? '主页面、工具栏与查询区已核验（2026-07-24）'
    : '菜单、URL、工具栏与查询区已核验'
  config.evidenceNote = `${config.evidenceNote} 主查询区字段、控件类型、选项顺序、默认值及按钮文字已逐页核验。`
})

nursingPageConfigs.宝宝护理汇总.toolbarEvidence = '原页当前 HTTP 500，顶部操作区未核验'
nursingPageConfigs.宝宝护理汇总.queryEvidence = '原页当前 HTTP 500，查询区未核验'
nursingPageConfigs.宝宝护理汇总.evidenceNote = '原菜单 URL 已核验，但原页面当前返回 HTTP 500，顶部工具栏和查询区按钮仍为暂存草案，未作为原页证据。'

const integratedAlias = (baseTitle, overrides) => ({
  ...nursingPageConfigs[baseTitle],
  evidenceLevel: '业务数据闭环',
  completionLevel: '已启用',
  evidenceNote: '新增、编辑与状态操作按门店保存业务记录并保留审计事件；不替代医疗诊断或医嘱。',
  ...overrides
})

nursingPageConfigs['护理评估（产后恢复）'] = integratedAlias('健康评估', {
  key: 'health-assessments',
  description: '记录由护理人员人工录入的产后恢复观察与跟进建议；系统不自动形成诊断结论。'
})
nursingPageConfigs.护理看板 = integratedAlias('护理部排班第二版', {
  key: 'nursing-dashboard',
  mode: 'dashboard',
  description: '按当前门店查看护理排班、当天任务与状态。'
})
nursingPageConfigs.护理二次销售业绩 = integratedAlias('护理项目记录', {
  key: 'nursing-sales-performance',
  mode: 'summary',
  description: '按护理服务订单统计执行人员、项目、销售额与业绩金额。',
  actions: [],
  queryActions: ['查询', '导出'],
  columns: [
    col('performanceNo', '业绩单号', 155),
    col('performanceDate', '业务日期', 110),
    col('store', '门店', 150),
    col('nurseName', '护理人员', 110),
    col('itemName', '项目/商品', 170),
    col('quantity', '数量', 80),
    col('saleAmount', '销售金额', 110),
    col('performanceAmount', '业绩金额', 110),
    col('status', '订单状态', 100, true)
  ]
})
nursingPageConfigs['入住交接（物品清点）'] = integratedAlias('入住物品交接', {
  key: 'check-in-handover',
  description: '按门店记录入住物品清单、交接人员和客户确认状态。'
})
nursingPageConfigs.宝宝日志 = integratedAlias('宝宝护理记录', {
  key: 'baby-nursing-records',
  description: '记录宝宝喂养、排便、睡眠与护理事项；异常信息仅作为人工观察记录。'
})
nursingPageConfigs['记录可见范围开关（三档）'] = integratedAlias('自定义查房', {
  key: 'record-visibility-scope',
  mode: 'settings',
  description: '按总部、门店和本人三档维护护理记录可见范围；规则变更必须保留操作人和生效时间。',
  actions: [toolbarAction('新增范围规则', 'el-icon-plus'), toolbarAction('启用', 'el-icon-check', 'single'), toolbarAction('停用', 'el-icon-close', 'single')],
  filters: [select('scopeLevel', '可见范围', ['总部', '本门店', '本人']), select('status', '规则状态', ['启用', '停用'])],
  columns: [col('ruleNo', '规则编号', 140), col('recordType', '记录类型', 150), col('scopeLevel', '可见范围', 110), col('applicableRole', '适用角色', 130), col('effectiveAt', '生效时间', 150), col('operator', '操作人', 100), col('status', '状态', 90, true)]
})
nursingPageConfigs.漏记提醒与推送 = integratedAlias('护理计划', {
  key: 'missed-record-reminders',
  mode: 'reminder',
  description: '识别到期仍未完成的护理记录，生成门店内提醒和处理留痕；未配置外部通道时不显示为已发送。',
  actions: [toolbarAction('生成提醒', 'el-icon-bell'), toolbarAction('确认处理', 'el-icon-check', 'single')],
  filters: [input('customerName', '客户姓名'), input('room', '房间号'), select('reminderStatus', '提醒状态', ['待处理', '处理中', '已完成'])],
  columns: [col('reminderNo', '提醒编号', 150), col('customerName', '客户姓名', 110), col('room', '房间号', 90), col('recordType', '缺失记录', 150), col('dueAt', '应完成时间', 150), col('owner', '责任人', 100), col('reminderStatus', '状态', 100, true)]
})
nursingPageConfigs.交接班管理 = integratedAlias('护理部排班第二版', {
  key: 'shift-handover',
  mode: 'handover',
  description: '按班次登记待交接客户、风险事项、物品和接班确认，形成交班人与接班人双向留痕。',
  actions: [toolbarAction('发起交班', 'el-icon-plus'), toolbarAction('确认接班', 'el-icon-check', 'single')],
  filters: [dateRange('shiftRange', '班次日期'), input('handoverBy', '交班人'), select('handoverStatus', '交接状态', ['待接班', '已接班', '需补充'])],
  columns: [col('handoverNo', '交接编号', 150), col('shiftName', '班次', 110), col('handoverBy', '交班人', 100), col('receiveBy', '接班人', 100), col('riskSummary', '重点事项', 220), col('handoverAt', '交班时间', 150), col('handoverStatus', '状态', 100, true)]
})
nursingPageConfigs.感染管理 = integratedAlias('健康评估', {
  key: 'infection-management',
  mode: 'risk',
  description: '登记感染风险筛查、隔离措施、消毒记录和复核结果；系统只记录人工判断，不自动形成医疗诊断。',
  actions: [toolbarAction('新增风险记录', 'el-icon-plus'), toolbarAction('复核', 'el-icon-check', 'single'), toolbarAction('关闭', 'el-icon-circle-close', 'single')],
  filters: [input('customerName', '客户姓名'), input('room', '房间号'), select('riskStatus', '风险状态', ['待复核', '处理中', '已关闭'])],
  columns: [col('riskNo', '风险编号', 150), col('customerName', '客户姓名', 110), col('room', '房间号', 90), col('riskType', '风险类型', 140), col('measure', '处理措施', 200), col('reviewer', '复核人', 100), col('riskStatus', '状态', 100, true)]
})
nursingPageConfigs.护理任务工单 = integratedAlias('护理计划', {
  key: 'nursing-task-orders',
  mode: 'task-order',
  description: '把护理计划、异常和临时需求转为可指派工单，跟踪接单、执行、复核和完成状态。',
  actions: [toolbarAction('新增工单', 'el-icon-plus'), toolbarAction('指派', 'el-icon-user', 'single'), toolbarAction('确认完成', 'el-icon-check', 'single')],
  filters: [input('taskNo', '工单编号'), input('customerName', '客户姓名'), select('taskStatus', '工单状态', ['待指派', '待执行', '执行中', '待复核', '已完成'])],
  columns: [col('taskNo', '工单编号', 150), col('customerName', '客户姓名', 110), col('room', '房间号', 90), col('taskType', '任务类型', 140), col('assignee', '执行人', 100), col('dueAt', '要求完成时间', 150), col('taskStatus', '状态', 100, true)]
})

function configureSharedWorkbench(titles, primaryTitle, capabilityId, capabilityName) {
  const tabs = titles.map(title => ({
    title,
    label: title === primaryTitle ? `${title}（${capabilityId}）` : `${title}（兼容入口）`
  }))
  titles.forEach(title => {
    const config = nursingPageConfigs[title]
    config.workspace = {
      primaryTitle,
      capabilityId,
      capabilityName,
      tabs,
      note: `${capabilityId} ${capabilityName}已收敛为同一工作台；兼容入口与正式入口读取、写入同一门店业务记录。`
    }
  })
}

configureSharedWorkbench(['护理评估（产后恢复）', '健康评估'], '护理评估（产后恢复）', 'F022', '护理评估（产后恢复）')
configureSharedWorkbench(['入住交接（物品清点）', '入住物品交接'], '入住交接（物品清点）', 'F026', '入住交接（物品清点）')
configureSharedWorkbench(['宝宝日志', '宝宝护理记录'], '宝宝日志', 'F027', '宝宝日志')

const nursingTitleAliases = {
  '护理中心（巡房与记录）': '护理中心',
  护理评估: '护理评估（产后恢复）',
  入住交接: '入住交接（物品清点）',
  记录可见范围开关: '记录可见范围开关（三档）'
}

export const nursingMenuTitles = Object.keys(nursingPageConfigs)

export function getNursingPageConfig(title) {
  return nursingPageConfigs[nursingTitleAliases[title] || title] || nursingPageConfigs.护理中心
}
