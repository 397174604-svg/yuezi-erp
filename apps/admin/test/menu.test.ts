// PC 后台 RBAC 可见性矩阵单测（WS5）：给 apps/admin 补最小护栏——59 view 的权限过滤此前零自动化测试，
// 跨域改动打断前端无兜底。canSee 是前端菜单/路由守卫的唯一判定，纯函数可测。
// 运行：node --experimental-strip-types --test apps/admin/test/menu.test.ts（menu.ts 仅含惰性 import() 缩略，node 下可安全导入）
import { test } from 'node:test';
import assert from 'node:assert';
import { menu, canSee, ASSIGNABLE, firstVisiblePath, visibleGroups, GROUPS, dataKind } from '../src/router/menu.ts';

test('canSee：管理层看全部模块', () => {
  for (const m of menu) assert.equal(canSee(m, true, []), true, m.path + ' 管理层应可见');
});

test('canSee：perms 含 * 看全部可分配模块，但 managerOnly 即便通配也隐藏（防 * 越权）', () => {
  for (const m of menu.filter((x) => !x.managerOnly)) assert.equal(canSee(m, false, ['*']), true, m.path + ' 通配 perms 应可见');
  for (const m of menu.filter((x) => x.managerOnly)) assert.equal(canSee(m, false, ['*']), false, m.path + ' managerOnly 即便非管理层带通配也应隐藏');
});

test('canSee：非管理层看不到 managerOnly（即便 perms 显式含它）', () => {
  const mgrOnly = menu.filter((m) => m.managerOnly);
  assert.ok(mgrOnly.length > 0, '应有 managerOnly 模块');
  for (const m of mgrOnly) assert.equal(canSee(m, false, [m.path]), false, m.path + ' 应对非管理层隐藏');
});

test('canSee：可分配模块严格按 perms 命中', () => {
  const assignable = menu.filter((m) => !m.managerOnly);
  assert.ok(assignable.length > 0, '应有可分配模块');
  for (const m of assignable) {
    const key = m.perm ?? m.path; // 显式 perm 解耦 path≠模块（护理评估/交接/健康建档 归 nursing）
    assert.equal(canSee(m, false, [key]), true, m.path + ' perms 命中应可见');
    assert.equal(canSee(m, false, ['__none__']), false, m.path + ' perms 未命中应隐藏');
  }
});

test('ASSIGNABLE = 全部非 managerOnly 模块（供角色权限勾选树，须与后端 roleService.MODULES 对齐）', () => {
  const expect = menu.filter((m) => !m.managerOnly).map((m) => m.path);
  assert.deepEqual(ASSIGNABLE.map((a) => a.key), expect);
});

test('[越权修复] 总部驾驶舱=managerOnly：一线（技师等）看不到全店经营大屏', () => {
  const dash = menu.find((m) => m.path === 'dashboard');
  assert.ok(dash?.managerOnly, '总部驾驶舱须 managerOnly（展示全店累计实收/GMV）');
  // 技师 perms（去 dashboard 后）不含 dashboard，且即便显式含也应被 managerOnly 挡住
  const techPerms = ['customers', 'appointments', 'rooms', 'nursing', 'inventory'];
  assert.equal(canSee(dash!, false, techPerms), false, '一线看不到总部驾驶舱');
  assert.equal(canSee(dash!, false, ['dashboard']), false, 'managerOnly 优先于 perms 命中');
  assert.equal(canSee(dash!, true, []), true, '管理层可见');
  assert.ok(!ASSIGNABLE.some((a) => a.key === 'dashboard'), 'dashboard 不再是可分配模块');
});

test('[越权修复] firstVisiblePath：管理层落总部驾驶舱、一线落其首个业务模块', () => {
  assert.equal(firstVisiblePath(true, []), 'dashboard', '管理层落驾驶舱');
  assert.equal(firstVisiblePath(false, ['customers', 'appointments']), 'customers', '一线落首个可见业务页（非驾驶舱）');
  assert.equal(firstVisiblePath(false, []), '403', '无任何可见模块→403（不死循环）');
});

test('[分组导航] 每个菜单项都有合法分组（在 GROUPS 内，无孤儿/无静默丢失）', () => {
  for (const m of menu) {
    assert.ok(m.group, m.path + ' 应有 group');
    assert.ok(GROUPS.includes(m.group!), m.path + ' 的 group「' + m.group + '」须在 GROUPS 内');
  }
});

test('[分组导航] visibleGroups：管理层覆盖且仅覆盖全部菜单项、无空组、组序遵循 GROUPS', () => {
  const vg = visibleGroups(true, []);
  const flat = vg.flatMap((g) => g.items.map((m) => m.path));
  assert.deepEqual(flat.slice().sort(), menu.map((m) => m.path).sort(), '管理层分组后应无重无漏覆盖全部菜单项');
  for (const g of vg) assert.ok(g.items.length > 0, g.group + ' 不应为空组');
  const order = vg.map((g) => g.group);
  assert.deepEqual(order, GROUPS.filter((g) => order.includes(g)), '组顺序须是 GROUPS 的子序列');
});

test('[分组导航] visibleGroups：一线只看到有权的组，空组自动隐藏、组内不漏 managerOnly', () => {
  const techPerms = ['customers', 'orders', 'rooms', 'appointments', 'inventory'];
  const vg = visibleGroups(false, techPerms);
  const shown = vg.map((g) => g.group);
  assert.ok(['客户', '交易财务', '房务护理', '库存采购'].every((g) => shown.includes(g)), '有权的组应显示');
  assert.ok(!shown.includes('经营分析'), '无 managerOnly 权限 → 经营分析组隐藏');
  assert.ok(!shown.includes('系统设置') && !shown.includes('膳食月嫂'), '无权组隐藏');
  const trade = vg.find((g) => g.group === '交易财务');
  assert.deepEqual(trade!.items.map((m) => m.path), ['cashier-desk', 'orders'], '交易财务组一线见 收银台(orders权)+收银与订单（finance 等 managerOnly 子项绝不泄漏）');
});

test('[分组导航] visibleGroups：无任何权限 → 空数组（不渲染空壳侧边栏）', () => {
  assert.deepEqual(visibleGroups(false, []), []);
});

test('[storeOnly] 门店运营页(收银台)：总部(isHQ)隐藏，店长(管理层非总部)与一线(orders权)可见', () => {
  const cashier = menu.find((m) => m.path === 'cashier-desk')!;
  assert.ok(cashier.storeOnly, '收银台应标 storeOnly');
  // 总部(老板/运营)：isManager=true 但 isHQ=true → 隐藏（只监督不收银）
  assert.equal(canSee(cashier, true, ['*'], true), false, '总部看不到收银台');
  // 店长(管理层但非总部)：isHQ=false → 可见
  assert.equal(canSee(cashier, true, ['*'], false), true, '店长(管理层)可见收银台');
  // 一线前台/收银/产康师(orders 权，非 HQ)：可见
  assert.equal(canSee(cashier, false, ['orders'], false), true, '前台(orders权)可见收银台');
  // storeOnly 只作用于 HQ：非 storeOnly 页对总部不受影响
  const orders = menu.find((m) => m.path === 'orders')!;
  assert.equal(canSee(orders, true, [], true), true, '非 storeOnly 页(收银与订单)总部仍可见');
  // 总部视角 visibleGroups 不含收银台，但含收银与订单
  const hqTrade = visibleGroups(true, ['*'], true).find((g) => g.group === '交易财务');
  assert.ok(hqTrade && !hqTrade.items.some((m) => m.path === 'cashier-desk'), '总部交易财务组无收银台');
  assert.ok(hqTrade && hqTrade.items.some((m) => m.path === 'orders'), '总部仍见收银与订单');
});

test('[数据标注] dataKind：真实抽取页=real、混合页=mixed、其余默认 demo', () => {
  // 从 seed/real/*.json 抽取或真名硬编码的真实数据页
  for (const p of ['staff', 'stores', 'catalog', 'commission-matrix', 'bundles', 'item-bom', 'qa-library', 'roles']) assert.equal(dataKind(p), 'real', p + ' 应为真实数据');
  // 配置真实、流水演示
  for (const p of ['rooms', 'qc-check', 'qc-board']) assert.equal(dataKind(p), 'mixed', p + ' 应为混合');
  // 合成演示（客户/订单/线索/经营KPI）
  for (const p of ['dashboard', 'customers', 'orders', 'leads', 'appointments', 'inventory', 'finance']) assert.equal(dataKind(p), 'demo', p + ' 应为演示数据');
  // 每个菜单项都能被归类为三态之一，无遗漏
  for (const m of menu) assert.ok(['real', 'demo', 'mixed'].includes(dataKind(m.path)), m.path + ' 须可分类');
});
