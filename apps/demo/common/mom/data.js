/* 奇德芬芳 · 宝妈端 — 静态 UI 配置（我的菜单 / 二级屏列定义）。
 * ⚠ 本文件不含任何写死的业务数据：卡额/餐单/商城/订单/积分等全部来自后端 API（common/remote.js + api.js）。
 * EMPTY 仅为渲染初值占位；onLaunch 经 loadDashboard 用后端真实数据填充，后端不可用时保持空（不显示假数据）。*/

// 渲染安全空壳（数值字段给 0、对象字段给定形，避免 .toLocaleString() 等在数据到达前报错）
export const EMPTY = { me: {}, journey: {}, balance: { pkg: 0, careCard: 0 }, schedule: [], monthSpent: 0, promo: {}, todayMeals: [], mall: [] };

export const MEMENU = [
  { l: '个人中心 / 合同', k: 'profileMom' }, { l: '卡额 / 餐卡', k: 'mealCard' }, { l: '消费账单', k: 'consume' },
  { l: '护理记录', k: 'careRecords' }, { l: '产康预约', k: 'apptMom' }, { l: '我的商品订单', k: 'productOrders' },
  { l: '我的积分', k: 'points' }, { l: '月嫂 / 育儿嫂', k: 'nannies' }, { l: '育儿知识', k: 'parenting' },
  { l: 'AI 育儿问答 · 秒回', page: '/pages/qa/qa' },
  { l: '专家问答', k: 'expertQA' }, { l: '辣妈贴吧', k: 'forum' }, { l: '消息中心', k: 'notices' }, { l: '设置' }
];

// 二级「更多」屏：仅标题/类型/列定义（rows/metrics 由 remote.loadPage 从后端实时填充；后端无数据则空）。
export const PAGES = {
  mealCard: { title: '卡额 / 餐卡', type: 'cards', note: '会员卡额', metrics: [] },
  consume: { title: '消费账单', type: 'list', columns: ['项目', '日期', '支付方式', '金额'], rows: [] },
  careRecords: { title: '护理记录', type: 'list', columns: ['类型', '日期', '明细'], rows: [] },
  apptMom: { title: '产康预约', type: 'list', actions: ['预约'], columns: ['项目', '预约时间', '技师', '状态'], rows: [] },
  productOrders: { title: '我的商品订单', type: 'list', columns: ['销售单号', '支付方式', '金额', '下单日期', '快递', '状态'], rows: [] },
  points: { title: '我的积分', type: 'list', note: '', columns: ['标题', '类别', '积分', '时间', '备注'], rows: [] },
  nannies: { title: '月嫂 / 育儿嫂', type: 'list', actions: ['预约'], columns: ['姓名', '年龄', '职业类型', '等级', '标准费用', '状态'], rows: [] },
  parenting: { title: '育儿知识', type: 'list', columns: ['标题', '类别', '类型', '置顶'], rows: [] },
  expertQA: { title: '专家问答', type: 'list', actions: ['提问'], columns: ['问题', '指定专家', '提问时间', '是否回复'], rows: [] },
  forum: { title: '辣妈贴吧', type: 'list', actions: ['发帖'], columns: ['内容', '作者', '发送时间', '浏览量'], rows: [] },
  notices: { title: '消息中心', type: 'list', columns: ['标题', '时间', '状态'], rows: [] },
  profileMom: { title: '个人中心 / 合同', type: 'cards', note: '', metrics: [] }
};
