/* 奇德芬芳 · 员工端 — 静态 UI 配置（菜单/快捷网格/巡房清单/二级屏列定义）。
 * ⚠ 本文件不含任何写死的业务数据：客户/线索/合同/护理等全部来自后端 API（common/remote.js + api.js）。
 * EMPTY 仅为渲染初值占位；onLaunch 经 loadDashboard 用后端真实数据填充，后端不可用时保持空（不显示假数据）。*/

export const EMPTY = { me: {}, kpis: {}, funnel: {}, clients: [], roundItems: ['体温·血压', '伤口/恶露', '乳房评估', '宝宝黄疸', '情绪问询'] };

export const GRID = [
  { t: '开单', s: '商品销售', k: 'goodsSale', c: '单', perm: 'orders' }, { t: '合同', s: '签约审核', k: 'contracts', c: '约', perm: 'contracts' },
  { t: '房态', s: '订房入住', k: 'roomBoard', c: '房', perm: 'rooms' }, { t: '审批', s: '待办收件箱', k: 'approvals', c: '审', manager: true },
  { t: '线索', s: '公海跟进', k: 'leads', c: '索', perm: 'leads' }, { t: '护理中心', s: '巡房记录', k: 'careDash', c: '护', perm: 'nursing' },
  { t: '录客户', s: '新建档案', k: 'clientForm', c: '录', perm: 'customers' }, { t: '宝宝档案', s: '母婴信息', k: 'baby', c: '婴', perm: 'nursing' }
  ,{ t: '到店服务', s: '扫码需求待办', k: '__service_requests__', c: '服', perm: 'appointments' }
  ,{ t: '专家建议', s: '人工选服务', k: '__recommendations__', c: '荐', perm: 'customers', roles: ['专家', '产康师'] }
  ,{ t: '管理看板', s: '经营核心数据', k: '__admin_dashboard__', c: '管', manager: true }
  ,{ t: '二维码', s: '创建与预览', k: '__qr_manager__', c: '码', manager: true }
  ,{ t: '选房配置', s: '楼层·朝向·房型', k: '__room_layout__', c: '层', manager: true }
  ,{ t: '客房周转', s: '清洁·检查·清点', k: '__room_turnover__', c: '洁', perm: 'rooms', roles: ['客房管理'] }
];
export const MEMENU = [
  { l: '专家服务建议', page: '/pages/recommendations/recommendations', perm: 'customers', roles: ['专家', '产康师'] },
  { l: '管理经营看板', page: '/pages/admin/dashboard', manager: true },
  { l: '到店服务待办', page: '/pages/service-requests/service-requests', perm: 'appointments' },
  { l: '小程序二维码管理', page: '/pages/qr-manager/qr-manager', manager: true },
  { l: '楼层与选房配置', page: '/pages/admin/room-layout', manager: true },
  { l: '客房清洁与检查', page: '/pages/housekeeping/turnover', perm: 'rooms', roles: ['客房管理'] },
  { l: '我的业绩 / 提成', k: 'perfReport' }, { l: '审批待办', k: 'approvals', manager: true }, { l: '我的费用', k: 'fees' },
  { l: '客户回访记录', k: 'visitReturn', perm: 'customer-tracking' }, { l: '客户投诉建议', k: 'complaint', perm: 'customer-tracking' }, { l: '满意度调查', k: 'satisfaction', perm: 'customer-tracking' },
  { l: '健康评估', k: 'healthAssess', perm: 'nursing' }, { l: '月嫂服务/派工', k: 'momServe', perm: 'nursing' }, { l: '设置', manager: true }
];

// 二级「更多」屏：仅标题/类型/列定义/操作（rows/metrics 由 remote.loadPage 从后端实时填充；后端无数据则空）。
export const PAGES = {
  perfReport: { title: '我的业绩 · S13', type: 'cards', note: '本月汇总', metrics: [] },
  contracts: { title: '合同管理', type: 'list', actions: ['添加', '提交'], columns: ['合同编码', '客户', '套餐', '合同类型', '最终成交', '已收款', '欠款', '签单人', '审核状态'], rows: [] },
  leads: { title: '线索管理', type: 'list', actions: ['添加', '抢单'], columns: ['姓名', '电话', '微信', '线索来源', '业务员', '跟进状态', '预产期'], rows: [] },
  approvals: { title: '审批待办', type: 'list', actions: ['通过', '驳回'], columns: ['单据类型', '关联客户/房间', '申请人', '金额', '提交时间', '状态'], rows: [] },
  careDash: { title: '护理中心', type: 'cards', note: '实时', metrics: [] },
  goodsSale: { title: '商品销售 / 开单', type: 'list', actions: ['加入单据', '结算'], columns: ['商品名称', '单位', '单价', '折后单价', '折扣率', '数量', '商品总价'], rows: [] },
  roomBoard: { title: '房态 / 订房', type: 'list', actions: ['订房', '入住'], columns: ['房间', '房型', '客户', '房间状态', '入住', '离开', '余款'], rows: [] },
  healthAssess: { title: '健康评估', type: 'list', actions: ['新增评估'], columns: ['客户姓名', '房间号', '宝宝名称', '胎型', '分娩方式', '入住时间', '客户状态'], rows: [] },
  visitReturn: { title: '客户回访记录', type: 'list', actions: ['新增回访'], columns: ['客户姓名', '电话', '回访分店', '回访类型', '回访时间', '回访部门', '状态'], rows: [] },
  complaint: { title: '客户投诉建议', type: 'list', actions: ['处理'], columns: ['客户姓名', '投诉对象', '投诉类型', '投诉等级', '投诉时间', '处理人', '是否处理'], rows: [] },
  satisfaction: { title: '满意度调查', type: 'list', actions: ['导出'], columns: ['客户名称', '房间号', '调查表类型', '调查日期', '满意度', '当前打分', '状态'], rows: [] },
  momServe: { title: '月嫂服务 / 派工', type: 'list', actions: ['派工'], columns: ['月嫂姓名', '服务客户', '服务项目', '服务时间', '工时', '派工状态'], rows: [] },
  fees: { title: '我的费用', type: 'list', actions: ['报销申请'], columns: ['费用单号', '费用类型', '申请事由', '打款类别', '申请金额', '申请时间', '状态'], rows: [] },
  // —— 产康板块二级屏（平移自 apps/rehab；数据由 common/rehab.js.loadPage 填充，sub.vue 以 scope=rehab 路由）——
  bizData: { title: '产康经营数据', type: 'cards', metrics: [] },
  apptBoard: { title: '项目预约', type: 'board', note: '实时', buckets: [], cols: [] },
  itemSettings: { title: '产康品项', type: 'list', columns: ['项目名称', '项目分类', '所属部门', '销售价', '体验价', '时长', '状态'], rows: [] },
  commission: { title: '产康提成', type: 'list', columns: ['项目名称', '客户提成', '散客提成', '客户奖金'], rows: [] },
  payOrders: { title: '支付 / 订单管理', type: 'list', filterable: true, columns: ['订单号', '客户', '业务', '金额', '支付渠道', '状态', '下单时间'], rows: [] },
  transferLog: { title: '转店记录', type: 'list', columns: ['客户', '原门店', '目标门店', '原因', '时间'], rows: [] },
  memberStats: { title: '产康会员数据', type: 'cards', note: '会员等级分布 / 经营', metrics: [] },
  stockMgmt: { title: '库房查询', type: 'list', columns: ['品项', '当前库存', '预警线', '状态'], rows: [] },
  scheduleBoard: { title: '技师排班', type: 'list', columns: ['员工', '日期', '班次', '状态'], rows: [] },
  rehabCustomers: { title: '产康客户', type: 'list', columns: ['姓名', '电话', '会员等级', '储值余额', '最近消费', '顾问'], rows: [] }
};

// 产康工作台渲染安全空壳（数值字段给 0、对象定形，避免数据到达前 .toLocaleString()/.charAt() 报错）。
export const REHAB_EMPTY = {
  store: { name: '', manager: '', expire: '' },
  kpis: { turnover: 0, appts: 0, members: 0 },
  appointments: [], techs: [],
  cashierTabs: ['划卡', '购买项目', '购买商品', '购卡', '余额充值'],
  cashierCustomer: { customerId: 0, name: '', level: '', cardNo: '', hasCard: '', storedCard: 0, balance: 0, points: 0 },
  items: [], discountMap: {}
};
