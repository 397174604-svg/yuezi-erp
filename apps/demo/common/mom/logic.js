/* 奇德芬芳 · 宝妈端 — 纯逻辑（无 uni/网络依赖，可单测）。remote.js 与测试共用。*/

// 月子进程：以入住建档日(created_at)为近似起点算第几天，配阶段名。
// nowMs 参数化便于单测（默认当前时间）。真实分娩日字段待机构数据接入。
export function journeyOf(cust, nowMs = Date.now()) {
  const total = 28;
  if (!cust || !cust.created_at) return { day: 1, total, phase: '产褥期' };
  const ts = new Date(cust.created_at).getTime();
  if (!Number.isFinite(ts)) return { day: 1, total, phase: '产褥期' }; // new Date(损坏串)→NaN（不抛错），显式兜底避免 day:NaN
  const day = Math.min(total, Math.max(1, Math.floor((nowMs - ts) / 86400000) + 1));
  const phase = day <= 7 ? '产褥初期' : day <= 14 ? '调理期' : day <= 21 ? '恢复期' : '巩固期';
  return { day, total, phase };
}

// 今日餐单：从（已发布的）餐单里取最近一个日期的全部餐别，避免历史多日混排冒充今日。
export function pickLatestMeals(diet) {
  const arr = diet || [];
  const latest = arr.reduce((mx, d) => (d.meal_date || '') > mx ? d.meal_date : mx, '');
  return arr.filter(d => !latest || d.meal_date === latest);
}
