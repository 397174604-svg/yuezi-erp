// 合一演示自绘底栏组件逻辑（tabsForEnd/tabUrl 纯函数）——四端页签正确、未知端不越界、路径拼接稳定。
import { test } from 'node:test';
import assert from 'node:assert';
import { MENU, tabsForEnd, tabUrl } from '../components/demo-tabbar/tabs.js';

test('demo-tabbar：四端各恰 4 个 tab，字段齐（path/label/icon）', () => {
  for (const end of ['staff', 'rehab', 'beauty', 'mom']) {
    const tabs = tabsForEnd(end);
    assert.equal(tabs.length, 4, end + ' 应 4 tab');
    for (const t of tabs) assert.ok(t.path && t.label && t.icon, end + ' 每个 tab 字段齐');
  }
});

test('demo-tabbar：未知端/空返回空数组（防越界渲染）', () => {
  assert.deepEqual(tabsForEnd('unknown'), []);
  assert.deepEqual(tabsForEnd(undefined), []);
});

test('demo-tabbar：每端末位统一为「我的」me/me（切身份口固定末位）', () => {
  for (const end of ['staff', 'rehab', 'beauty', 'mom']) {
    assert.equal(tabsForEnd(end).at(-1).path, 'me/me', end + ' 末位应为 me/me');
  }
});

test('demo-tabbar：首位工作台/我的月子（首页锚点）', () => {
  assert.equal(tabsForEnd('staff')[0].path, 'home/home');
  assert.equal(tabsForEnd('mom')[0].label, '我的月子');
});

test('demo-tabbar：reLaunch 路径拼接 /pages/{end}/{path}', () => {
  assert.equal(tabUrl('staff', 'home/home'), '/pages/staff/home/home');
  assert.equal(tabUrl('mom', 'diet/diet'), '/pages/mom/diet/diet');
});

test('demo-tabbar：MENU 只含四端，无脏键', () => {
  assert.deepEqual(Object.keys(MENU).sort(), ['beauty', 'mom', 'rehab', 'staff']);
});
