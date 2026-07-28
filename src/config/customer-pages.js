const customerStatuses = ['意向A', '意向B', '意向C', '意向D', '意向E', '流失客户', '散客客户', '同意签合同', '已签合同但未审核', '已签合同但未入住', '已订房', '已入住', '已退房已结账', '已退房但未结账']
const customerSources = ['客户介绍', '住附近', '电话来访', '大众点评', '美团咨询', '地推拓客', '抖音咨询', '小红书咨询', '自然上门', '网络搜索', '市场渠道', '二胎入住', '内部资源']
const stores = ['中心广场旗舰店', '黄河路轻奢店']

const input = (key, label, placeholder = '') => ({ key, label, type: 'input', placeholder })
const select = (key, label, options) => ({ key, label, type: 'select', options })
const dateRange = (key, label) => ({ key, label, type: 'dateRange' })
const date = (key, label, format = 'date') => ({ key, label, type: 'date', dateType: format })
const checkbox = (key, label) => ({ key, label, type: 'checkbox' })
const textarea = (key, label) => ({ key, label, type: 'textarea' })
const col = (key, label, width = 120, tag = false) => ({ key, label, width, tag })

const customerBaseColumns = [
  col('name', '客户姓名', 110), col('birthday', '客户生日', 110), col('age', '年龄', 70), col('mobile', '客户电话', 125),
  col('babyName', '宝宝姓名', 100), col('wechat', '微信(QQ)', 115), col('memberCard', '会员卡号', 120), col('balance', '账户余额', 100),
  col('points', '积分余额', 90), col('creator', '登记人', 90), col('lastEditor', '最后编辑人', 100), col('status', '客户状态', 135, true),
  col('source', '客户来源', 105), col('salesperson', '销售员', 90), col('intendedStore', '意向分店', 145), col('stayStore', '入住分店', 145),
  col('createdAt', '录入时间', 150), col('dueDate', '预产期', 110), col('followedAt', '跟踪时间', 150), col('followContent', '跟踪内容', 180),
  col('appointment', '预约参观', 100), col('area', '客户区域', 100), col('companion', '陪护人', 90), col('companionPhone', '陪护电话', 120),
  col('firstVisitAt', '到店时间', 150), col('tags', '客户标签', 150)
]

const customerFilters = [
  input('name', '客户姓名'), input('mobile', '手机号'), input('wechat', '微信号'), select('status', '客户状态', customerStatuses),
  select('source', '客户来源', customerSources), select('store', '意向分店', stores), dateRange('createdRange', '登记时间'), dateRange('dueRange', '预产期')
]

const followForm = [
  input('customerName', '客户名称'), date('followedAt', '跟踪时间', 'datetime'), select('status', '跟踪状态', customerStatuses.slice(0, 8)),
  select('followType', '跟踪类型', ['销售跟踪', '咨询跟踪', '回访跟踪', '探访跟踪', '投诉跟踪']),
  select('contactType', '接触方式', ['微信交流', '店外面谈', '电话交流', '来店参观']), date('nextFollowAt', '下一跟踪时间', 'datetime'), textarea('content', '跟踪信息')
]

export const customerPageConfigs = {
  '线索管理': {
    key: 'clues', icon: 'el-icon-connection', description: '管理未转化客资，完成分配、跟踪、共享、公海同步与客户转化。',
    actions: ['添加', '编辑', '删除', '客资分配', '客户跟踪', '线索转让', '分享', '同步公海客户', '转化', '关闭', '导入', '导出'],
    filters: [input('name', '姓名'), input('wechat', '微信'), input('mobile', '手机号码'), select('followStatus', '跟踪状态', ['未处理', '跟进中', '关闭', '已转化']), input('unfollowedDays', '未跟踪天数'), input('assignee', '分配人'), dateRange('dueRange', '预产日期'), dateRange('createdRange', '录入日期'), select('source', '客户来源', customerSources), input('description', '线索说明')],
    columns: [col('name', '姓名'), col('mobile', '电话'), col('wechat', '微信'), col('source', '线索来源'), col('salesperson', '业务员'), col('creator', '录入人'), col('followStatus', '跟进状态', 100, true), col('convertStore', '转化分店', 140), col('sharedBy', '共享人'), col('appointment', '预约参观'), col('followCount', '跟踪次数'), col('followedAt', '跟踪时间', 150), col('createdAt', '线索时间', 150), col('dueDate', '预产期'), col('description', '线索说明', 180), col('autoAssigned', '自动分配'), col('convertedCustomer', '转化客户'), col('customerMobile', '客户电话')],
    formFields: [input('name', '线索姓名'), input('mobile', '手机号码'), input('wechat', '微信'), select('source', '线索来源', customerSources), date('dueDate', '预产日期'), input('assignee', '分配人'), textarea('description', '线索说明')]
  },
  '我的客户': {
    key: 'my-customers', icon: 'el-icon-user', description: '查看当前账号负责的客户及最近跟踪、到店和预约情况。',
    actions: ['客户跟踪', '导出'], filters: customerFilters, columns: [...customerBaseColumns, col('autoAssigned', '自动分配')], formFields: followForm
  },
  '客户管理': {
    key: 'customers', icon: 'el-icon-s-custom', description: '客户全生命周期总台，贯通合同、结账、分房、欠款和服务消息。',
    actions: ['添加', '创建合同', '二维码打印', '编辑', '删除', '导入', '导出', '打印', '设置', '客资分配', '回收', '客户跟踪', '结账', '反结账', '欠款授权', '生成采购计划', '转化', '分享'],
    stages: ['全部', '意向客户', '进店客户', '已签约客户', '待入住客户', '已入住客户', '已退房客户', '流失客户', '零散客户'],
    filters: [input('name', '客户姓名'), input('mobile', '手机号'), dateRange('createdRange', '录入日期'), select('isToStore', '是否到店', ['是', '否']), input('wechat', '微信(QQ)'), input('salesperson', '销售员'), dateRange('dueRange', '预产期'), select('store', '意向分店', stores), select('status', '客户状态', customerStatuses), select('source', '客户来源', customerSources), input('creator', '登记人'), input('memo', '备忘录'), input('memberCard', '会员卡号'), checkbox('delivered', '是否分娩')],
    columns: [...customerBaseColumns, col('delivered', '是否分娩'), col('contractNo', '合同编号', 140), col('contractAmount', '合同金额', 115), col('debtAmount', '欠款金额', 105), col('room', '预订房间', 100)],
    formFields: [input('customerName', '客户名称'), input('mobile', '客户电话'), input('amount', '可欠款金额'), select('paymentType', '款项类型', ['合同款', '续房款', '会员充值']), textarea('remark', '操作备注')]
  },
  '跟进记录': {
    key: 'follow-records', icon: 'el-icon-chat-line-round', description: '统一查询销售、咨询、回访、探访和投诉跟踪记录及未来计划。',
    actions: ['编辑', '删除', '导出'], filters: [input('follower', '跟进人'), input('customerName', '跟进客户'), input('mobile', '电话'), input('wechat', '微信'), select('store', '意向分店', stores), select('status', '跟踪状态', customerStatuses), select('followType', '跟踪类型', ['销售跟踪', '咨询跟踪', '回访跟踪', '探访跟踪', '投诉跟踪']), select('source', '客户来源', customerSources), dateRange('followRange', '跟踪时间'), checkbox('showSystem', '显示系统跟踪')],
    columns: [col('follower', '跟进人'), col('department', '跟进部门'), col('customerName', '跟进客户'), col('mobile', '客户电话'), col('wechat', '微信'), col('appointment', '是否预约'), col('dueDate', '预产期'), col('source', '客户来源'), col('status', '跟进状态', 100, true), col('followType', '跟进类型'), col('contactType', '跟进方式'), col('content', '跟进内容', 220), col('followedAt', '跟进时间', 150), col('nextFollowAt', '下次跟进时间', 150), col('nextContent', '下次跟进内容', 180), col('attachment', '附件')], formFields: followForm
  },
  '签单客户': {
    key: 'signed-customers', icon: 'el-icon-document-checked', description: '集中查看已签约客户、合同签订日期、客户等级及欠款授权。',
    actions: ['导出', '欠款授权', '客户跟踪', '打印'], filters: [input('name', '客户姓名'), input('mobile', '手机号'), input('wechat', '微信(QQ)'), input('status', '客户状态'), select('source', '客户来源', customerSources), select('store', '意向分店', stores), dateRange('dueRange', '预产期'), input('salesperson', '销售员'), input('unfollowedDays', '未跟踪天数'), input('creator', '登记人'), dateRange('createdRange', '录入日期'), input('tags', '标签'), input('memo', '备忘录'), dateRange('signedRange', '合同签订日期')],
    columns: [...customerBaseColumns, col('levelScore', '客户等级值'), col('autoLevel', '是否自动升降级', 125), col('customerLevel', '客户等级'), col('pregnancyCount', '胎次'), col('sharedBy', '共享人'), col('address', '地址', 180), col('signedAt', '签订日期', 120), col('contractMobile', '手机号', 125)], formFields: followForm
  },
  '预约参观': {
    key: 'appointments', icon: 'el-icon-date', description: '管理到店邀约、预约确认、试吃安排、接待人与转化结果。',
    actions: ['添加', '编辑', '删除', '客资分配', '预约确认', '转化', '导出'], filters: [input('visitor', '预约人'), input('mobile', '联系电话'), select('store', '参观分店', stores), select('arrivalStatus', '到店状态', ['是', '否', '已邀约']), dateRange('appointmentRange', '预约时间'), select('directArrival', '直接到店', ['昨日', '今日', '明日'])],
    columns: [col('visitor', '预约人'), col('mobile', '联系电话'), col('wechat', '微信号(QQ)'), col('source', '了解途径'), col('visitorCount', '参观人数'), col('arrivalCount', '总到店次数'), col('receptionist', '接待人'), col('vehicle', '车辆信息'), col('appointmentAt', '预约时间', 150), col('arrivalStatus', '到店状态', 100, true), col('directArrival', '直接到店'), col('store', '参观分店', 140), col('appointmentType', '预约类型'), col('tastingCount', '试吃人数'), col('tastingAt', '试吃时间', 150), col('menu', '试吃菜单', 180), col('remark', '备注', 180), col('clueName', '线索名字'), col('clueMobile', '线索电话'), col('creator', '制单人'), col('converted', '是否转化')],
    formFields: [input('visitor', '预约人'), input('mobile', '联系电话'), input('wechat', '微信号(QQ)'), select('source', '了解途径', customerSources), input('visitorCount', '参观人数'), input('receptionist', '接待人'), input('vehicle', '车辆信息'), date('appointmentAt', '预约时间', 'datetime'), select('store', '参观分店', stores), input('appointmentType', '预约类型'), input('tastingCount', '试吃人数'), date('tastingAt', '试吃时间', 'datetime'), textarea('menu', '试吃菜单'), textarea('remark', '备注')]
  },
  '公海客户': {
    key: 'public-customers', icon: 'el-icon-s-opportunity', description: '管理无明确归属或已回收客资，支持抢单、分配和重新跟踪。',
    actions: ['添加', '编辑', '删除', '客资分配', '客户跟踪', '抢单', '导出'], filters: [input('name', '客户姓名'), input('mobile', '手机号'), dateRange('createdRange', '录入时间')], columns: customerBaseColumns.slice(0, 20), formFields: followForm
  },
  '入住探访记录': {
    key: 'visits', icon: 'el-icon-house', description: '登记客户入住期间家属或访客的探访信息。',
    actions: ['添加', '编辑', '删除'], filters: [input('customerName', '客户姓名'), dateRange('visitRange', '探访日期')],
    columns: [col('visitor', '探访人'), col('customerName', '客户姓名'), col('mobile', '探访人电话'), col('location', '探访地点'), col('visitAt', '探访时间', 150), col('remark', '备注', 220)],
    formFields: [input('visitor', '探访人'), input('customerName', '客户姓名'), input('mobile', '探访人电话'), input('location', '探访地点'), date('visitAt', '探访时间', 'datetime'), textarea('remark', '备注')]
  },
  '满意度调查表': {
    key: 'satisfaction', icon: 'el-icon-medal', description: '按门店、房间和调查类型查询客户满意度及打分结果。',
    actions: ['删除', '导出'], filters: [input('customerName', '客户姓名'), input('room', '房间号'), input('surveyType', '调查表类型'), select('store', '门店', stores), dateRange('surveyRange', '调查日期')],
    columns: [col('room', '房间号'), col('store', '门店', 140), col('customerName', '客户名称'), col('surveyAt', '调查日期', 120), col('satisfaction', '满意度'), col('score', '当前打分'), col('createdAt', '创建日期', 150), col('surveyType', '调查表类型', 150)], formFields: []
  },
  '客户回访记录': {
    key: 'callbacks', icon: 'el-icon-phone-outline', description: '登记客户阶段回访、回访部门、详情及入住离院时间。',
    actions: ['添加', '编辑', '删除'], filters: [input('customerName', '客户姓名'), select('store', '分店', stores), dateRange('callbackRange', '回访日期'), select('callbackType', '回访类型', ['第一阶段', '第二阶段', '第三阶段', '出院回访'])],
    columns: [col('customerName', '客户姓名'), col('mobile', '电话'), col('store', '回访分店', 140), col('admittedAt', '入院时间', 120), col('dischargedAt', '出院时间', 120), col('callbackType', '回访类型'), col('callbackAt', '回访时间', 150), col('creator', '录入人'), col('department', '回访部门'), col('details', '回访详情', 240)],
    formFields: [input('customerName', '客户姓名'), input('mobile', '电话'), select('store', '回访分店', stores), date('admittedAt', '入院时间'), date('dischargedAt', '出院时间'), select('callbackType', '回访类型', ['第一阶段', '第二阶段', '第三阶段', '出院回访']), date('callbackAt', '回访时间', 'datetime'), input('department', '回访部门'), textarea('details', '回访详情')]
  },
  '客户投诉建议': {
    key: 'complaints', icon: 'el-icon-warning-outline', description: '登记投诉对象、等级和内容，并形成审核、处理、回访闭环。',
    actions: ['添加', '审核', '编辑', '删除'], filters: [select('complaintType', '投诉类型', ['专业性', '服务及时性', '服务态度', '责任心', '沟通问题', '过度销售']), input('department', '被投诉部门'), select('handled', '审核状态', ['未处理', '已处理']), select('store', '分店', stores), dateRange('complaintRange', '投诉日期')],
    columns: [col('customerName', '客户姓名'), col('target', '投诉对象'), col('complaintType', '投诉类型'), col('level', '投诉等级', 100, true), col('content', '投诉内容', 220), col('complaintAt', '投诉时间', 150), col('handled', '是否处理', 100, true), col('handleMethod', '处理方式', 180), col('handledAt', '处理时间', 150), col('handler', '处理人'), col('department', '被投诉部门', 120), col('functionName', '功能')],
    formFields: [input('customerName', '客户姓名'), input('target', '投诉对象'), select('complaintType', '投诉类型', ['专业性', '服务及时性', '服务态度', '责任心', '沟通问题', '过度销售']), select('level', '投诉等级', ['一般', '重要', '紧急']), input('department', '被投诉部门'), date('complaintAt', '投诉时间', 'datetime'), textarea('content', '投诉内容'), select('handled', '处理状态', ['未处理', '已处理']), textarea('handleMethod', '处理方式')]
  },
  '消息计划模板': {
    key: 'message-templates', icon: 'el-icon-tickets', description: '配置孕产、产康和宝宝服务节点的自动消息提醒模板。',
    actions: ['添加', '编辑', '删除'], filters: [select('templateType', '类型', ['产后康复', '孕产健康管理', '宝宝舒畅健康发育'])],
    columns: [col('templateType', '类型', 150), col('projectName', '项目名称', 150), col('days', '提醒时间（天）', 120), col('dateType', '提醒日期类型', 140), col('content', '提醒内容', 260), col('sendType', '发送类型'), col('reminderType', '提醒类型')],
    formFields: [select('templateType', '类型', ['产后康复', '孕产健康管理', '宝宝舒畅健康发育']), input('projectName', '项目名称'), input('days', '提醒时间（天）'), select('dateType', '提醒日期类型', ['预产期', '分娩日期', '入住日期', '离店日期']), select('sendType', '发送类型', ['短信', '微信', '站内消息']), select('reminderType', '提醒类型', ['提前提醒', '当日提醒', '延后提醒']), textarea('content', '提醒内容')]
  },
  '客户消息': {
    key: 'messages', icon: 'el-icon-message', description: '查询按消息计划生成的客户触达任务、发送状态与失败原因。',
    actions: ['新增消息', '立即发送', '取消发送', '重新发送'], filters: [input('customerName', '客户姓名'), input('mobile', '手机号'), select('channel', '发送渠道', ['短信', '微信', '站内消息']), select('sendStatus', '发送状态', ['待发送', '已发送', '发送失败', '已取消']), dateRange('plannedRange', '计划发送时间')],
    columns: [col('customerName', '客户姓名'), col('mobile', '客户电话'), col('messageTitle', '消息标题', 180), col('content', '消息内容', 260), col('channel', '发送渠道'), col('plannedAt', '计划发送时间', 150), col('sentAt', '实际发送时间', 150), col('sendStatus', '发送状态', 100, true), col('failureReason', '失败原因', 180), col('creator', '创建人')],
    formFields: [input('customerName', '客户姓名'), input('mobile', '客户电话'), input('messageTitle', '消息标题'), select('channel', '发送渠道', ['短信', '微信', '站内消息']), date('plannedAt', '计划发送时间', 'datetime'), textarea('content', '消息内容')]
  },
  '积分设置': {
    key: 'point-settings', icon: 'el-icon-setting', description: '配置销售、收款、转介绍和会员行为的积分生成规则。',
    actions: [], filters: [], columns: [], formFields: []
  },
  '积分记录': {
    key: 'point-records', icon: 'el-icon-coin', description: '登记和追溯客户获取积分、使用积分、推广码及备注。',
    actions: ['添加', '删除'], filters: [input('customerName', '客户名称'), select('pointType', '积分类型', ['获取积分', '使用积分'])],
    columns: [col('customerName', '客户名称'), col('title', '标题'), col('code', '编码', 130), col('pointValue', '积分数值'), col('pointType', '类别', 100, true), col('promoCode', '推广码'), col('promoCustomer', '推广码客户'), col('promoMobile', '推广码客户电话', 130), col('createdAt', '创建时间', 150), col('remark', '备注', 200)],
    formFields: [input('customerName', '姓名'), input('promoCode', '推广码'), input('pointValue', '积分'), select('pointType', '积分类型', ['获取积分', '使用积分']), textarea('remark', '备注')]
  },
  '发布活动': {
    key: 'activities', icon: 'el-icon-present', description: '管理会员活动发布、报名、渠道、问卷、推荐和置顶状态。',
    actions: ['添加', '报名', '编辑', '设置', '启用', '停用', '推荐/取消', '设置渠道'], filters: [],
    columns: [col('title', '标题', 180), col('targetAudience', '活动对象'), col('gift', '赠送礼品', 140), col('activityStatus', '状态', 90, true), col('publisher', '发布人'), col('startsAt', '活动开始时间', 150), col('endsAt', '结束时间', 150), col('createdAt', '录入时间', 150), col('store', '活动门店', 140), col('recommended', '是否推荐'), col('signupCount', '报名人数'), col('surveyCount', '问卷调查人数', 120), col('commentCount', '评论人数'), col('topped', '是否置顶')],
    formFields: [input('title', '活动标题'), input('targetAudience', '活动对象'), input('gift', '赠送礼品'), select('store', '活动门店', stores), date('startsAt', '开始时间', 'datetime'), date('endsAt', '结束时间', 'datetime'), select('activityStatus', '状态', ['草稿', '启用', '停用']), input('survey', '活动调查表'), textarea('description', '活动说明')]
  }
}

export const pointSettingGroups = [
  { key: 'serviceSale', label: '服务销售' }, { key: 'materialSale', label: '物料销售' }, { key: 'mealSale', label: '膳食销售' },
  { key: 'cardSale', label: '卡类销售' }, { key: 'contractSale', label: '合同销售' }, { key: 'memberRecharge', label: '会员充值' },
  { key: 'roomExtension', label: '续房收款' }, { key: 'upgradePayment', label: '升级收款' }, { key: 'referral', label: '转介绍积分' },
  { key: 'referred', label: '被转介绍积分' }, { key: 'login', label: '登录积分' }, { key: 'register', label: '注册积分' },
  { key: 'comment', label: '评论积分' }, { key: 'share', label: '分享积分' }, { key: 'activitySignup', label: '活动报名积分' }
]

export function getCustomerPageConfig(title) {
  return customerPageConfigs[title] || customerPageConfigs['客户管理']
}
