// 合一演示自绘底栏的页签数据（纯函数，可测；组件 import 它，避免 .vue 内联逻辑无测漂移）。
export const MENU = {
  staff: [['home/home', '工作台', '🏠'], ['clients/clients', '客户', '👥'], ['round/round', '巡房', '📋'], ['me/me', '我的', '👤']],
  rehab: [['home/home', '工作台', '🏠'], ['cashier/cashier', '收银', '💰'], ['customers/customers', '客户', '👥'], ['me/me', '我的', '👤']],
  beauty: [['home/home', '工作台', '🏠'], ['cashier/cashier', '收银', '💰'], ['customers/customers', '客户', '👥'], ['me/me', '我的', '👤']],
  mom: [['home/home', '我的月子', '🌙'], ['diet/diet', '膳食', '🍲'], ['mall/mall', '商城', '🎁'], ['me/me', '我的', '👤']],
}

// 某端的 tab 列表；未知端返回空数组（防越界渲染）。
export function tabsForEnd(end) {
  return (MENU[end] || []).map(([path, label, icon]) => ({ path, label, icon }))
}

// reLaunch 目标路径（组件与测试共用同一拼接规则）。
export function tabUrl(end, path) {
  return '/pages/' + end + '/' + path
}
