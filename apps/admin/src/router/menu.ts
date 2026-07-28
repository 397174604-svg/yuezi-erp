// 侧边栏菜单 = 路由表的单一来源。router 与 AppLayout 都从这里取，避免循环依赖。
// 权限模型（后端可配置 RBAC）：
//   - managerOnly=true 的模块 → 仅管理层(is_manager)可见，不可分配给普通角色；
//   - 其余「可分配模块」→ 由后端「角色权限」表的 perms 决定可见性（path 即模块 key）。
// 登录时后端解析 {isManager, perms} 下发，前端 canSee 据此过滤；增删改角色见 RoleManager.vue。
// 可分配模块 path 须与后端 roleService.MODULES 严格对齐。
export interface MenuDef {
  path: string
  title: string
  icon: string
  component: () => Promise<unknown>
  managerOnly?: boolean
  perm?: string // 显式模块权限键：非 managerOnly 页可用它解耦「path≠模块」（如护理评估 path=nursing-assess 但归 nursing 模块），持该 perm 的角色可见
  storeOnly?: boolean // 门店一线运营页（如收银台）：总部(老板/运营)只监督不操作，对其隐藏菜单+拦路由；店级角色(前台/收银/产康师)与店长仍可见
  group?: string // 二级导航分组（见 GROUPS）；缺省归「其他」兜底组，绝不静默丢失
}

export const menu: MenuDef[] = [
  { path: 'dashboard', group: '经营分析', title: '总部驾驶舱', icon: 'DataLine', managerOnly: true, component: () => import('@/views/dashboard/Dashboard.vue') },
  { path: 'cockpit', group: '经营分析', title: '经营大屏', icon: 'Odometer', managerOnly: true, component: () => import('@/views/dashboard/BigScreen.vue') },
  { path: 'customers', group: '客户', title: '客户中台', icon: 'User', component: () => import('@/views/customers/CustomerList.vue') },
  { path: 'customer-tracking', group: '客户', title: '业务跟踪台', icon: 'Bell', component: () => import('@/views/customers/CustomerTracking.vue') },
  { path: 'satisfaction', group: '经营分析', title: '满意度回访', icon: 'ChatLineSquare', managerOnly: true, component: () => import('@/views/customers/SatisfactionStats.vue') },
  { path: 'member-analysis', group: '经营分析', title: '会员来源分析', icon: 'PieChart', managerOnly: true, component: () => import('@/views/customers/MemberAnalysis.vue') },
  { path: 'health-profile', group: '客户', title: '健康建档', icon: 'FirstAidKit', perm: 'nursing', component: () => import('@/views/customers/HealthProfile.vue') },
  { path: 'cashier-desk', group: '交易财务', title: '收银台', icon: 'Wallet', perm: 'orders', storeOnly: true, component: () => import('@/views/cashier/CashierDesk.vue') },
  { path: 'orders', group: '交易财务', title: '收银与订单', icon: 'Tickets', component: () => import('@/views/orders/OrderList.vue') },
  { path: 'appointments', group: '房务护理', title: '预约与排班', icon: 'Calendar', component: () => import('@/views/appointments/AppointmentBoard.vue') },
  { path: 'rooms', group: '房务护理', title: '客房房态', icon: 'House', component: () => import('@/views/rooms/RoomBoard.vue') },
  { path: 'room-assign', group: '房务护理', title: '智能排房', icon: 'Calendar', managerOnly: true, component: () => import('@/views/rooms/RoomAssign.vue') },
  { path: 'room-gantt', group: '房务护理', title: '房态时间轴', icon: 'Calendar', managerOnly: true, component: () => import('@/views/rooms/RoomGantt.vue') },
  { path: 'contracts', group: '交易财务', title: '合同与销售', icon: 'Document', component: () => import('@/views/contracts/ContractList.vue') },
  { path: 'nursing', group: '房务护理', title: '护理中心', icon: 'FirstAidKit', component: () => import('@/views/nursing/NursingCenter.vue') },
  { path: 'nursing-assess', group: '房务护理', title: '护理评估', icon: 'Notebook', perm: 'nursing', component: () => import('@/views/nursing/NursingAssessment.vue') },
  { path: 'nutrition', group: '膳食月嫂', title: '膳食统计', icon: 'Bowl', managerOnly: true, component: () => import('@/views/nursing/NutritionStats.vue') },
  { path: 'nursing-kpi', group: '房务护理', title: '护理看板', icon: 'DataLine', managerOnly: true, component: () => import('@/views/nursing/NursingKPI.vue') },
  { path: 'nursing-sales', group: '房务护理', title: '护理二次销售', icon: 'Sell', managerOnly: true, component: () => import('@/views/nursing/NursingSalesBoard.vue') },
  { path: 'handover', group: '房务护理', title: '入住交接', icon: 'DocumentChecked', perm: 'nursing', component: () => import('@/views/nursing/Handover.vue') },
  { path: 'baby', group: '房务护理', title: '宝宝日志', icon: 'Star', perm: 'nursing', component: () => import('@/views/baby/BabyCenter.vue') },
  { path: 'catering-delivery', group: '膳食月嫂', title: '订餐配送', icon: 'Van', managerOnly: true, component: () => import('@/views/catering/CateringDelivery.vue') },
  { path: 'meal-library', group: '膳食月嫂', title: '月子餐库', icon: 'Bowl', managerOnly: true, component: () => import('@/views/catering/MealLibrary.vue') },
  { path: 'nutrition-board', group: '膳食月嫂', title: '配餐营养看板', icon: 'Histogram', managerOnly: true, component: () => import('@/views/catering/NutritionBoard.vue') },
  { path: 'inventory', group: '库存采购', title: '库房管理', icon: 'Box', component: () => import('@/views/inventory/InventoryList.vue') },
  { path: 'stock-transfer', group: '库存采购', title: '跨店调拨', icon: 'Sort', managerOnly: true, component: () => import('@/views/inventory/StockTransfer.vue') },
  { path: 'stocktake', group: '库存采购', title: '库存盘点', icon: 'List', managerOnly: true, component: () => import('@/views/inventory/StockTake.vue') },
  { path: 'inventory-alert', group: '库存采购', title: '库存预警', icon: 'Warning', managerOnly: true, component: () => import('@/views/inventory/InventoryAlert.vue') },
  { path: 'purchase', group: '库存采购', title: '采购管理', icon: 'ShoppingBag', managerOnly: true, component: () => import('@/views/inventory/Purchase.vue') },
  { path: 'inventory-valuation', group: '库存采购', title: '库存估值', icon: 'Coin', managerOnly: true, component: () => import('@/views/inventory/InventoryValuation.vue') },
  { path: 'batches', group: '库存采购', title: '批次保质期', icon: 'Calendar', managerOnly: true, component: () => import('@/views/inventory/BatchList.vue') },
  { path: 'suppliers', group: '库存采购', title: '供应商', icon: 'OfficeBuilding', managerOnly: true, component: () => import('@/views/inventory/SupplierList.vue') },
  { path: 'leads', group: '客户', title: '客户运营', icon: 'Promotion', component: () => import('@/views/leads/LeadList.vue') },
  { path: 'marketing', group: '营销会员', title: '营销与内容', icon: 'ShoppingCart', component: () => import('@/views/marketing/MarketingList.vue') },
  { path: 'recharge-coupon', group: '营销会员', title: '充值·优惠券', icon: 'Wallet', managerOnly: true, component: () => import('@/views/marketing/RechargeCoupon.vue') },
  { path: 'points-rules', group: '营销会员', title: '积分规则', icon: 'Medal', managerOnly: true, component: () => import('@/views/marketing/PointsRules.vue') },
  { path: 'content-ops', group: '营销会员', title: '内容运营', icon: 'Reading', perm: 'marketing', component: () => import('@/views/marketing/ContentOps.vue') },
  { path: 'asset-library', group: '营销会员', title: '图片素材', icon: 'Picture', managerOnly: true, component: () => import('@/views/marketing/AssetLibrary.vue') },
  // —— 以下为管理层专属（managerOnly，不可分配给普通角色）——
  { path: 'nanny', group: '膳食月嫂', title: '月嫂管理', icon: 'Female', managerOnly: true, component: () => import('@/views/nanny/NannyCenter.vue') },
  { path: 'nanny-gantt', group: '膳食月嫂', title: '月嫂档期', icon: 'Calendar', managerOnly: true, component: () => import('@/views/nanny/NannyGantt.vue') },
  { path: 'nanny-settlement', group: '膳食月嫂', title: '月嫂结算', icon: 'Money', managerOnly: true, component: () => import('@/views/nanny/NannySettlement.vue') },
  { path: 'reports', group: '经营分析', title: '数据报表', icon: 'TrendCharts', managerOnly: true, component: () => import('@/views/reports/ReportsCenter.vue') },
  { path: 'monthly-report', group: '经营分析', title: '经营月报', icon: 'Calendar', managerOnly: true, component: () => import('@/views/reports/MonthlyReport.vue') },
  { path: 'recharge-report', group: '经营分析', title: '充值报表', icon: 'CreditCard', managerOnly: true, component: () => import('@/views/reports/RechargeReport.vue') },
  { path: 'finance', group: '交易财务', title: '财务收支', icon: 'Money', managerOnly: true, component: () => import('@/views/finance/FinanceCenter.vue') },
  { path: 'approval-inbox', group: '交易财务', title: '审批中台', icon: 'Stamp', managerOnly: true, component: () => import('@/views/finance/ApprovalInbox.vue') },
  { path: 'refund-expense', group: '交易财务', title: '退款·报销', icon: 'DocumentDelete', managerOnly: true, component: () => import('@/views/finance/RefundExpense.vue') },
  { path: 'finance-breakdown', group: '交易财务', title: '收支分析', icon: 'PieChart', managerOnly: true, component: () => import('@/views/finance/FinanceBreakdown.vue') },
  { path: 'invoices', group: '交易财务', title: '发票管理', icon: 'Document', managerOnly: true, component: () => import('@/views/finance/InvoiceCenter.vue') },
  { path: 'reconcile', group: '交易财务', title: '交易对账', icon: 'Coin', managerOnly: true, component: () => import('@/views/finance/ReconcileBoard.vue') },
  { path: 'cost-margin', group: '交易财务', title: '成本核算', icon: 'Histogram', managerOnly: true, component: () => import('@/views/finance/CostMargin.vue') },
  { path: 'assets', group: '交易财务', title: '资产账单', icon: 'Wallet', managerOnly: true, component: () => import('@/views/assets/AssetCenter.vue') },
  { path: 'card-value', group: '经营分析', title: '次卡价值', icon: 'CreditCard', managerOnly: true, component: () => import('@/views/assets/CardValueStats.vue') },
  { path: 'sms', group: '营销会员', title: '短信营销', icon: 'ChatDotRound', managerOnly: true, component: () => import('@/views/sms/SmsCenter.vue') },
  { path: 'catalog', group: '商品品控', title: '品项与提成', icon: 'Goods', managerOnly: true, component: () => import('@/views/catalog/CatalogList.vue') },
  { path: 'commission-matrix', group: '商品品控', title: '提成方案', icon: 'Histogram', managerOnly: true, component: () => import('@/views/catalog/CommissionMatrix.vue') },
  { path: 'item-bom', group: '商品品控', title: '项目耗材BOM', icon: 'Connection', managerOnly: true, component: () => import('@/views/catalog/ItemBom.vue') },
  { path: 'bundles', group: '商品品控', title: '套餐管理', icon: 'Present', managerOnly: true, component: () => import('@/views/catalog/BundleList.vue') },
  { path: 'targets', group: '经营分析', title: '目标管理', icon: 'Aim', managerOnly: true, component: () => import('@/views/catalog/TargetManagement.vue') },
  { path: 'stores', group: '系统设置', title: '门店与渠道', icon: 'Shop', managerOnly: true, component: () => import('@/views/stores/StoreList.vue') },
  { path: 'staff', group: '系统设置', title: '员工与组织', icon: 'UserFilled', managerOnly: true, component: () => import('@/views/staff/StaffList.vue') },
  { path: 'roles', group: '系统设置', title: '角色权限', icon: 'Lock', managerOnly: true, component: () => import('@/views/roles/RoleManager.vue') },
  { path: 'qc-check', group: '商品品控', title: '品控检查', icon: 'CircleCheck', managerOnly: true, component: () => import('@/views/qc/QcCheck.vue') },
  { path: 'qc-board', group: '商品品控', title: '品控看板', icon: 'Medal', managerOnly: true, component: () => import('@/views/qc/QcBoard.vue') },
  { path: 'qa-library', group: '营销会员', title: 'AI客服知识库', icon: 'ChatDotRound', managerOnly: true, component: () => import('@/views/qa/QaLibrary.vue') },
  { path: 'settings', group: '系统设置', title: '系统设置', icon: 'Setting', managerOnly: true, component: () => import('@/views/settings/SettingsCenter.vue') },
]

// 可分配模块（managerOnly=false），供「角色权限」管理页生成勾选树；须与后端 roleService.MODULES 一致。
export const ASSIGNABLE = menu.filter((m) => !m.managerOnly).map((m) => ({ key: m.path, title: m.title }))

// 模块可见性：storeOnly 页对总部(isHQ)隐藏；managerOnly 恒以 is_manager 为准；其余管理层/perms 含 '*' 全见，或按 perms 命中。
export function canSee(item: MenuDef, isManager: boolean, perms: string[], isHQ = false): boolean {
  if (item.storeOnly && isHQ) return false // 门店一线运营页(如收银台)：总部只监督不操作，即便是管理层也不给（店长非总部，仍可见）
  if (item.managerOnly) return isManager // managerOnly 恒以 is_manager 为准：通配 '*' / 显式 perms 都不能放宽（防非管理层拿到 * 越权看驾驶舱/财务）
  if (isManager || perms.includes('*')) return true
  return perms.includes(item.perm ?? item.path) // 默认按 path 判模块；显式 perm 解耦 path≠模块（护理评估/交接/健康建档 归 nursing）
}

// 登录落地/守卫兜底用：当前身份第一个可见模块（管理层→总部驾驶舱；一线→其首个有权模块；无则 403）。
// 取代此前「死跳 /dashboard + 守卫对 dashboard 兜底放行」——否则一线登录仍会落在管理层驾驶舱页看到全店数据。
export function firstVisiblePath(isManager: boolean, perms: string[], isHQ = false): string {
  const m = menu.find((x) => canSee(x, isManager, perms, isHQ))
  return m ? m.path : '403'
}

// —— 数据来源标注（demo 明示）——
// real：从奇德芬芳真实源系统抽取导入（seed/real/*.json：员工花名册/项目目录/提成/套餐/耗材BOM/房型/品控标准/问答语料；门店真名；手机号一律脱敏）。
// mixed：配置真实、流水演示（如房型为真、房态为演示；品控标准为真、检查评分为演示）。
// demo：合成演示数据（客户/订单/账单/线索/漏斗/预约/护理/排班/库存流水/营销活动/各类经营KPI 等，非真实经营数据）。
const REAL_PAGES = new Set(['staff', 'stores', 'catalog', 'commission-matrix', 'bundles', 'item-bom', 'qa-library', 'roles'])
const MIXED_PAGES = new Set(['rooms', 'qc-check', 'qc-board'])
export function dataKind(path: string): 'real' | 'demo' | 'mixed' {
  if (REAL_PAGES.has(path)) return 'real'
  if (MIXED_PAGES.has(path)) return 'mixed'
  return 'demo'
}

// 二级导航分组顺序（侧边栏父级）。末尾「其他」兜底任何未归组模块，绝不静默丢失。
export const GROUPS = ['经营分析', '客户', '交易财务', '房务护理', '膳食月嫂', '库存采购', '营销会员', '商品品控', '系统设置', '其他']

// 按分组返回当前身份可见的菜单：组内保持 menu 原顺序，空组（当前身份无任一可见子项）自动隐藏。
// 一线角色因此只看到自己有权的那几组；管理层看到全部有内容的组。
export function visibleGroups(isManager: boolean, perms: string[], isHQ = false): Array<{ group: string; items: MenuDef[] }> {
  return GROUPS
    .map((g) => ({ group: g, items: menu.filter((m) => (m.group || '其他') === g && canSee(m, isManager, perms, isHQ)) }))
    .filter((g) => g.items.length > 0)
}
