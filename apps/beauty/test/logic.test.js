import { test } from 'node:test';
import assert from 'node:assert';
import { levelOf, lineAmount, discountedTotal, round2 } from '../common/logic.js';

test('科研美容端 levelOf：优先 DB level，缺失按余额兜底（等级口径统一回归）', () => {
  assert.equal(levelOf('体验', 7894), '体验', '有 DB level 时用 DB level，不被高余额改写');
  assert.equal(levelOf('黑金', 0), '黑金');
  assert.equal(levelOf(null, 6000), '黑金', '无 level → 余额≥5000=黑金');
  assert.equal(levelOf('', 2500), '钻石');
  assert.equal(levelOf(undefined, 800), '白银');
  assert.equal(levelOf(null, 0), '体验');
});

test('科研美容端 lineAmount / discountedTotal：等级折扣逐行 round2（与后端口径一致）', () => {
  assert.equal(lineAmount(208.01, 2, 0.9), 374.42, '208.01×2×0.9 折后逐行 round2');
  assert.equal(lineAmount(208.01, 2, 0.8), 332.82);
  assert.equal(lineAmount(100, 1, 1), 100, '不打折');
  assert.equal(lineAmount(100, 1, null), 100, 'discount 缺省=1');
  const items = [{ id: 'a', price: 208.01 }, { id: 'b', price: 100 }];
  assert.equal(discountedTotal(items, { a: 2, b: 1 }, 0.9), 464.42, '374.42 + 90');
  assert.equal(discountedTotal(items, {}, 0.9), 0, '空购物车=0');
  assert.equal(round2(99.999), 100, 'round2 进位');
  assert.equal(round2(374.418), 374.42);
});
