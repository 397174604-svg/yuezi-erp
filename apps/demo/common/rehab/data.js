/* 奇德芬芳 · 产康门店端 — 静态 UI 配置（收银页签 / 二级屏列定义）。
 * ⚠ 本文件不含任何写死的业务数据：客户/预约/技师/品项/提成等全部来自后端 API（common/remote.js + api.js）。
 * EMPTY 仅为渲染初值占位；onLaunch 经 loadDashboard 用后端真实数据填充，后端不可用时保持空（不显示假数据）。*/

// 渲染安全空壳（数值字段给 0、对象字段给定形，避免 .toLocaleString()/.charAt() 等在数据到达前报错）
export const EMPTY = {
  brand: { name: '奇德芬芳', latin: 'QIDE FENFANG' },               // 品牌字样（UI 文案）
  store: { name: '', manager: '', expire: '' },
  kpis: { turnover: 0, appts: 0, members: 0 },              // 定形数值壳：避免后端不可用时 .toLocaleString() 崩溃
  appointments: [], techs: [],
  cashierTabs: ['划卡', '购买项目', '购买商品', '购卡', '余额充值'], // 收银页签（UI 配置）
  cashierCustomer: { name: '', level: '', cardNo: '', hasCard: '', storedCard: 0, balance: 0, points: 0 }, items: [], discountMap: {}
};

// 二级「更多」屏：仅标题/类型/列定义/操作（rows/metrics/buckets/cols 由 remote.loadPage 从后端实时填充）。
export const PAGES = {
  bizData: { title: '经营数据', type: 'cards', metrics: [] },
  apptBoard: { title: '项目预约', type: 'board', note: '实时', buckets: [], cols: [] },
  itemSettings: { title: '品项设置', type: 'list', actions: ['新增', '导入'], columns: ['项目名称', '项目分类', '所属部门', '销售价', '体验价', '时长', '状态'], rows: [] },
  commission: { title: '提成设置', type: 'list', columns: ['项目名称', '客户提成', '散客提成', '客户奖金'], rows: [] },
  // —— 店铺端 MVP 补充（后端已有，前端展示页）——
  payOrders: { title: '支付 / 订单管理', type: 'list', filterable: true, columns: ['订单号', '客户', '业务', '金额', '支付渠道', '状态', '下单时间'], rows: [] },
  transferLog: { title: '转店记录', type: 'list', columns: ['客户', '原门店', '目标门店', '原因', '时间'], rows: [] },
  memberStats: { title: '会员数据', type: 'cards', note: '会员等级分布 / 经营', metrics: [] },
  stockMgmt: { title: '库房管理', type: 'list', actions: ['入库', '出库'], columns: ['品项', '当前库存', '预警线', '状态'], rows: [] },
  scheduleBoard: { title: '员工排班', type: 'list', actions: ['排班'], columns: ['员工', '日期', '班次', '状态'], rows: [] }
};
