import { test } from 'node:test';
import assert from 'node:assert';
import { journeyOf, pickLatestMeals, normalizeDateTime, dateTimeMs } from '../common/logic.js';
import { createApi } from '../common/api.js';

const DAY = 86400000;
const now = Date.parse('2026-06-28T00:00:00.000Z');

test('宝妈端 journeyOf：按建档日算第N天 + 阶段（修「永久空白」回归）', () => {
  assert.deepEqual(journeyOf({ created_at: '2026-06-28T00:00:00.000Z' }, now), { day: 1, total: 28, phase: '产褥初期' });
  assert.deepEqual(journeyOf({ created_at: new Date(now - 9 * DAY).toISOString() }, now), { day: 10, total: 28, phase: '调理期' });
  const j = journeyOf({ created_at: new Date(now - 40 * DAY).toISOString() }, now);
  assert.equal(j.day, 28, '超 28 天封顶');
  assert.equal(j.phase, '巩固期');
  // 无 cust / 无日期 / 损坏日期串 → 不空白、不 NaN，给定形占位
  assert.deepEqual(journeyOf(null, now), { day: 1, total: 28, phase: '产褥期' });
  assert.deepEqual(journeyOf({}, now), { day: 1, total: 28, phase: '产褥期' });
  assert.deepEqual(journeyOf({ created_at: 'not-a-date' }, now), { day: 1, total: 28, phase: '产褥期' }, '损坏日期串→day:1 非 NaN');
});

test('宝妈端日期：MySQL DATETIME 转为 iOS 可解析 ISO 格式', () => {
  assert.equal(normalizeDateTime('2026-06-01 00:00:00'), '2026-06-01T00:00:00');
  assert.ok(Number.isFinite(dateTimeMs('2026-06-01 00:00:00')));
  assert.equal(normalizeDateTime('2026-06-01T00:00:00+08:00'), '2026-06-01T00:00:00+08:00');
});

test('宝妈端日期：MySQL DATETIME 不经过字符串 Date.parse', () => {
  const originalParse = Date.parse;
  Date.parse = () => { throw new Error('MySQL DATETIME 不应调用 Date.parse'); };
  try {
    assert.equal(
      dateTimeMs('2026-06-01 00:00:00'),
      new Date(2026, 5, 1, 0, 0, 0, 0).getTime(),
    );
    assert.ok(Number.isNaN(dateTimeMs('2026-02-31 00:00:00')), '无效日期不自动滚动');
  } finally {
    Date.parse = originalParse;
  }
});

test('宝妈端 pickLatestMeals：只取最近一天，不把历史多日混排成今日', () => {
  const diet = [
    { meal_date: '2026-06-24', meal_type: '早餐' },
    { meal_date: '2026-06-26', meal_type: '早餐' },
    { meal_date: '2026-06-26', meal_type: '午餐' },
    { meal_date: '2026-06-25', meal_type: '晚餐' },
  ];
  const meals = pickLatestMeals(diet);
  assert.equal(meals.length, 2, '只取 06-26 的两餐');
  assert.ok(meals.every(m => m.meal_date === '2026-06-26'));
  assert.deepEqual(pickLatestMeals([]), [], '空餐单→空');
  assert.deepEqual(pickLatestMeals(null), [], 'null→空');
});

test('宝妈端 API：品牌方法存在并请求 /api/v1/brand', async () => {
  let requested = '';
  const api = createApi({
    baseUrl: 'http://local', tenantId: 1,
    transport: async (_method, url) => { requested = url; return { status: 200, json: { data: { name: '奇德芬芳' } } }; },
  });
  assert.equal(typeof api.getBrand, 'function');
  assert.equal((await api.getBrand()).name, '奇德芬芳');
  assert.equal(requested, 'http://local/api/v1/brand');
});
