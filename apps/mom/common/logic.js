/* 奇德芬芳 · 宝妈端 — 纯逻辑（无 uni/网络依赖，可单测）。remote.js 与测试共用。*/

// 月子进程：以入住建档日(created_at)为近似起点算第几天，配阶段名。
// nowMs 参数化便于单测（默认当前时间）。真实分娩日字段待机构数据接入。
/** MySQL DATETIME 常返回 yyyy-MM-dd HH:mm:ss；先转为 iOS 支持的 ISO 本地时间格式。 */
export function normalizeDateTime(value) {
  if (typeof value !== 'string') return value;
  const s = value.trim();
  return /^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}/.test(s) ? s.replace(/\s+/, 'T') : s;
}

export function dateTimeMs(value) {
  if (value == null || value === '') return NaN;
  if (typeof value === 'number') return value;
  const s = String(value).trim();
  // 不把 MySQL DATETIME 直接交给 Date/Date.parse。微信开发者工具和部分 iOS
  // 会把 `yyyy-MM-dd HH:mm:ss` 判为不兼容格式，即使先替换成 T 也可能留下警告。
  // 数字参数构造与无时区的 MySQL DATETIME 语义一致：按设备本地时间解释。
  const local = s.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?)?$/);
  if (local) {
    const year = Number(local[1]);
    const month = Number(local[2]);
    const day = Number(local[3]);
    const hour = Number(local[4] || 0);
    const minute = Number(local[5] || 0);
    const second = Number(local[6] || 0);
    const millisecond = Number((local[7] || '').padEnd(3, '0') || 0);
    const date = new Date(year, month - 1, day, hour, minute, second, millisecond);
    // 拒绝 2026-02-31 这类会被 Date 自动滚动到下个月的无效日期。
    if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day
      || date.getHours() !== hour || date.getMinutes() !== minute || date.getSeconds() !== second) return NaN;
    return date.getTime();
  }
  // 带 Z 或 +08:00 的标准 ISO 时间由运行时按明确时区解析。
  return Date.parse(normalizeDateTime(s));
}

export function journeyOf(cust, nowMs = Date.now()) {
  const total = 28;
  if (!cust || !cust.created_at) return { day: 1, total, phase: '产褥期' };
  const ts = dateTimeMs(cust.created_at);
  if (!Number.isFinite(ts)) return { day: 1, total, phase: '产褥期' };
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
