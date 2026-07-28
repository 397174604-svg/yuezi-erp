/* 奇德芬芳 · 产康店铺端 — 纯逻辑（无 uni/网络依赖，可单测）。remote.js / cashier.vue 与测试共用。*/

export const round2 = (n) => Math.round((Number(n) || 0) * 100) / 100;

// 客户会员等级：优先用 DB level（与会员数据屏统一口径），缺失才按储值余额兜底。
export function levelOf(dbLevel, balance) {
  if (dbLevel) return dbLevel;
  const b = Number(balance) || 0;
  return b >= 5000 ? '黑金' : (b >= 2000 ? '钻石' : (b >= 500 ? '白银' : '体验'));
}

// 折后行金额：单价 × 数量 × 折扣率，逐行 round2（与后端 cashierService 算价口径一致）。
export function lineAmount(price, qty, discount) {
  return round2((Number(price) || 0) * (qty || 0) * (discount == null ? 1 : discount));
}

// 折后应收：购物车各行折后金额求和再 round2。items=[{id,price}]，cart={id:qty}。
export function discountedTotal(items, cart, discount) {
  return round2((items || []).reduce((s, p) => { const q = (cart || {})[p.id] || 0; return q ? s + lineAmount(p.price, q, discount) : s; }, 0));
}
