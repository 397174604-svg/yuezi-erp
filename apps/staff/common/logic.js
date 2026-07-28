/* 奇德芬芳 · 员工端 — 纯逻辑（无 uni/网络依赖，可单测）。
 * 抽出便于自动化测试锁定回归。remote.js 与测试共用。*/

// 真实 ERP 客户状态 → 客户追踪页筛选桶（在住/签单/到访/线索）。
// ⚠ 必须先判签单再判在住：『已签合同但未入住』含子串『入住』，先判在住会误归在住桶。
export const STAGE = (s) => !s ? '线索'
  : ((s.includes('签合同') || s.includes('订房')) ? '签单'
    : (s.includes('入住') ? '在住'
      : (s.includes('意向') ? '到访' : '线索')));

// 员工端入口可见性：管理层/通配权限全通；managerOnly 仅管理层；其余按模块权限。
export function hasAccess(perms, isManager, perm, managerOnly = false) {
  const list = Array.isArray(perms) ? perms : [];
  if (isManager || list.includes('*')) return true;
  if (managerOnly) return false;
  return !perm || list.includes(perm);
}

/* —— 产康板块收银/会员纯逻辑（平移自 apps/rehab/common/logic.js，与后端 cashierService 算价口径一致，可单测）—— */

export const round2 = (n) => Math.round((Number(n) || 0) * 100) / 100;

// 客户会员等级：优先用 DB level（与会员数据屏统一口径），缺失才按储值余额兜底。
export function levelOf(dbLevel, balance) {
  if (dbLevel) return dbLevel;
  const b = Number(balance) || 0;
  return b >= 5000 ? '黑金' : (b >= 2000 ? '钻石' : (b >= 500 ? '白银' : '体验'));
}

// 折后行金额：单价 × 数量 × 折扣率，逐行 round2（与后端 cashierService 逐行算价一致）。
export function lineAmount(price, qty, discount) {
  return round2((Number(price) || 0) * (qty || 0) * (discount == null ? 1 : discount));
}

// 折后应收：购物车各行折后金额求和再 round2。items=[{id,price}]，cart={id:qty}。
export function discountedTotal(items, cart, discount) {
  return round2((items || []).reduce((s, p) => { const q = (cart || {})[p.id] || 0; return q ? s + lineAmount(p.price, q, discount) : s; }, 0));
}
