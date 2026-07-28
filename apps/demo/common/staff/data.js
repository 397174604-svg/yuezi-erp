/* 奇德芬芳 · 员工端 — 静态 UI 配置（菜单/快捷网格/巡房清单/二级屏列定义）。
 * ⚠ 本文件不含任何写死的业务数据：客户/线索/合同/护理等全部来自后端 API（common/remote.js + api.js）。
 * EMPTY 仅为渲染初值占位；onLaunch 经 loadDashboard 用后端真实数据填充，后端不可用时保持空（不显示假数据）。*/

export const EMPTY = { me: {}, kpis: {}, funnel: {}, clients: [], roundItems: ['体温·血压', '伤口/恶露', '乳房评估', '宝宝黄疸', '情绪问询'] };

export const GRID = [
  { t: '开单', s: '商品销售', k: 'goodsSale', c: '单' }, { t: '合同', s: '签约审核', k: 'contracts', c: '约' },
  { t: '房态', s: '订房入住', k: 'roomBoard', c: '房' }, { t: '审批', s: '待办收件箱', k: 'approvals', c: '审' },
  { t: '线索', s: '公海跟进', k: 'leads', c: '索' }, { t: '护理中心', s: '巡房记录', k: 'careDash', c: '护' },
  { t: '录客户', s: '新建档案', k: 'clientForm', c: '录' }, { t: '宝宝档案', s: '母婴信息', k: 'baby', c: '婴' }
];
export const MEMENU = [
  { l: '我的业绩 / 提成', k: 'perfReport' }, { l: '审批待办', k: 'approvals' }, { l: '我的费用', k: 'fees' },
  { l: '客户回访记录', k: 'visitReturn' }, { l: '客户投诉建议', k: 'complaint' }, { l: '满意度调查', k: 'satisfaction' },
  { l: '健康评估', k: 'healthAssess' }, { l: '月嫂服务/派工', k: 'momServe' }, { l: '设置' }
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
  fees: { title: '我的费用', type: 'list', actions: ['报销申请'], columns: ['费用单号', '费用类型', '申请事由', '打款类别', '申请金额', '申请时间', '状态'], rows: [] }
};
