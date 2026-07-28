// 登录页演示账号分组搜索（filterAccountGroups 纯函数）——"全部账号显示+搜索"特性回归。
// 运行：node --experimental-strip-types --test apps/admin/test/account-filter.test.ts
import { test } from 'node:test';
import assert from 'node:assert';
import { filterAccountGroups } from '../src/views/accountFilter.ts';

const groups = [
  { role: '店长', list: [{ name: '王店长', phone: '13800000001' }] },
  { role: '前台', list: [{ name: '李前台', phone: '13900000002' }, { name: '赵小美', phone: '13700000003' }] },
  { role: '产康师', list: [{ name: '孙师傅', phone: '13600000004' }] },
];

test('空关键词 → 原样返回全部分组', () => {
  assert.equal(filterAccountGroups(groups, '').length, 3);
  assert.equal(filterAccountGroups(groups, '   ').length, 3, '纯空格视为空');
});

test('命中角色名 → 整组保留', () => {
  const r = filterAccountGroups(groups, '前台');
  assert.equal(r.length, 1);
  assert.equal(r[0].role, '前台');
  assert.equal(r[0].list.length, 2, '角色命中保留整组');
});

test('命中姓名 → 仅匹配账号，空组丢弃', () => {
  const r = filterAccountGroups(groups, '小美');
  assert.equal(r.length, 1);
  assert.equal(r[0].role, '前台');
  assert.equal(r[0].list.length, 1);
  assert.equal(r[0].list[0].name, '赵小美');
});

test('命中手机号子串 → 匹配账号', () => {
  const r = filterAccountGroups(groups, '13800000001');
  assert.equal(r.length, 1);
  assert.equal(r[0].list[0].name, '王店长');
  const p = filterAccountGroups(groups, '0000000');
  assert.ok(p.length >= 1, '公共号段子串匹配多组');
});

test('无匹配 → 空数组（驱动「无匹配账号」提示）', () => {
  assert.deepEqual(filterAccountGroups(groups, '查无此人'), []);
});

test('大小写不敏感 + 缺字段不报错', () => {
  const g = [{ role: 'Manager', list: [{ name: 'Amy' }, {}] }];
  assert.equal(filterAccountGroups(g, 'manager')[0].list.length, 2, '角色大小写不敏感命中整组');
  assert.equal(filterAccountGroups(g, 'amy').length, 1, '姓名大小写不敏感');
  assert.deepEqual(filterAccountGroups(g, '啥也不是'), [], '缺 name/phone 不抛');
});
