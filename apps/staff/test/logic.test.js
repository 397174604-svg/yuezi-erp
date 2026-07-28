import { test } from 'node:test';
import assert from 'node:assert';
import { STAGE, hasAccess } from '../common/logic.js';

test('员工端 STAGE：客户状态→筛选桶（含「已签合同但未入住」子串 bug 回归）', () => {
  assert.equal(STAGE('已入住'), '在住');
  assert.equal(STAGE('已签合同但未入住'), '签单', '含「入住」子串但必须归签单，不能误入在住桶');
  assert.equal(STAGE('已订房'), '签单');
  assert.equal(STAGE('同意签合同'), '签单');
  assert.equal(STAGE('意向A'), '到访');
  assert.equal(STAGE('意向E'), '到访');
  assert.equal(STAGE('散客客户'), '线索');
  assert.equal(STAGE(''), '线索');
  assert.equal(STAGE(null), '线索');
  assert.equal(STAGE(undefined), '线索');
});

test('员工端 STAGE：分桶后在住桶不含「未入住」客户（防虚高）', () => {
  const statuses = ['已入住', '已入住', '已签合同但未入住', '已签合同但未入住', '已订房', '意向A', '散客客户'];
  const buckets = statuses.reduce((m, s) => { const k = STAGE(s); m[k] = (m[k] || 0) + 1; return m; }, {});
  assert.equal(buckets['在住'], 2, '在住=2（仅真已入住），不含 2 个未入住');
  assert.equal(buckets['签单'], 3, '签单=2 未入住 + 1 订房');
  assert.equal(buckets['到访'], 1);
  assert.equal(buckets['线索'], 1);
});

test('员工端菜单权限：普通岗位只见已授权模块，管理层全部可见', () => {
  const nurse = ['customers', 'appointments', 'rooms', 'nursing'];
  assert.equal(hasAccess(nurse, false, 'nursing'), true);
  assert.equal(hasAccess(nurse, false, 'contracts'), false);
  assert.equal(hasAccess(nurse, false, undefined, true), false, '普通岗位不能见管理入口');
  assert.equal(hasAccess([], true, 'contracts'), true, '管理层全通');
  assert.equal(hasAccess(['*'], false, undefined, true), true, '通配权限等同管理层入口');
});
