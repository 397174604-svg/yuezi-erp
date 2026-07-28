/* 奇德芬芳 · 科研美容门店端 — 数据访问层（纯后端，无 mock）
 * 数据全部来自后端：门店/经营/预约/美容师/品项/客户/收银等。经共享客户端 api.js（uniTransport）打中台。
 * 后端不可用时返回空壳/空数组，绝不显示假数据。接入：App.vue onLaunch 注入 REMOTE.baseUrl + 租户身份。
 * 与产康端唯一差异：品项按 DOMAIN='科研美容' 过滤（收银台/品项设置/提成只呈现科颜项目）。*/
import { createApi, uniTransport } from './api.js';
import { EMPTY } from './data.js';
import { levelOf } from './logic.js';

// 本端业务线：收银/品项/提成一律按此域过滤，避免把月子/产康项目混进科颜收银台
export const DOMAIN = '科研美容';

// 由登录态注入（生产从 JWT/storage 取）
export const REMOTE = { baseUrl: '', tenantId: 1, storeId: 1, staffId: 0, token: '', isManager: false };

export function makeApi() {
  return createApi({
    baseUrl: REMOTE.baseUrl, tenantId: REMOTE.tenantId,
    storeId: REMOTE.storeId, staffId: REMOTE.staffId || undefined, token: REMOTE.token, transport: uniTransport,
  });
}

let authing = null; // 并发登录单例：onLaunch 与首页 onLoad 同 tick 触发时复用同一登录
function applyAuth(r) {
  REMOTE.token = r.token; REMOTE.tenantId = r.tenantId;
  REMOTE.storeId = (r.storeId != null ? r.storeId : null); // 含 null（多店管理员）→ 不残留默认门店
  if (r.staffId != null) REMOTE.staffId = r.staffId;
  REMOTE.isManager = !!r.isManager; // 管理层标志：驱动「我的」菜单隐藏管理项（后端已 manager 守卫，前端同步藏入口）
}
/** 员工登录（手机号+口令）。供登录页调用。 */
export async function loginWith(phone, password) { applyAuth(await makeApi().login(phone, password)); return true; }
/** 确保已登录：本地 dev 用演示账号自动登录（生产走登录页）。并发调用复用同一登录 promise。 */
// #ifdef H5
/** 统一前端登录（本地 H5 演示）：PC 后台登录后经顶栏「移动端直达」带 ?token= 跳入，
 *  解析 JWT payload 直填身份——一次登录各端通行。仅接受员工令牌；解析失败静默回退原登录。
 *  生产小程序走各端正式登录（code2session），不经 URL 传递令牌。 */
function tokenFromUrl() {
  try {
    const t = new URLSearchParams(location.search).get('token');
    if (!t) return false;
    const p = JSON.parse(decodeURIComponent(escape(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))));
    if (p.aud !== 'staff' || !p.tenantId) return false;
    REMOTE.token = t; REMOTE.tenantId = p.tenantId; REMOTE.storeId = p.storeId != null ? p.storeId : null; REMOTE.staffId = p.staffId != null ? p.staffId : 0; REMOTE.isManager = !!p.isManager;
    return true;
  } catch (e) { return false; }
}
// #endif
export function ensureAuth() {
  // #ifdef H5
  if (!REMOTE.token && tokenFromUrl()) return Promise.resolve();
  // #endif
  if (REMOTE.token || !REMOTE.baseUrl) return Promise.resolve();
  if (!authing) authing = (async () => {
    const api = makeApi();
    const demo = await api.demoAccounts();
    const acct = (demo.staff || [])[0];
    if (acct) applyAuth(await api.login(acct.phone, demo.password));
  })().catch(() => { /* 生产无演示账号 → 需登录页 */ }).finally(() => { authing = null; });
  return authing;
}
/** 包装一次取数：token 过期(401) 时清 token 重登并重试一次，避免长驻会话卡死不可恢复。 */
async function withAuth(run) {
  await ensureAuth();
  try { return await run(); }
  catch (e) {
    if (e && e.status === 401) { REMOTE.token = ''; await ensureAuth(); return await run(); }
    throw e;
  }
}

/** 工作台实时数据（全部后端）：门店/经营 KPI/今日预约/技师/收银品项/默认收银客户。后端不可用 → 空壳。 */
export async function loadDashboard() {
  if (!REMOTE.baseUrl) return EMPTY;
  try {
    return await withAuth(async () => {
    const api = makeApi();
    const [stats, appts, items, stores, staff, customers, levels] = await Promise.all([
      api.getBusinessStats({}), api.listAppointments({}), api.listItems({ status: '启用', domain: DOMAIN }),
      api.listStores().catch(() => []), api.listStaff({}).catch(() => []), api.listCustomers({ limit: 1 }).catch(() => []),
      api.listMemberLevels().catch(() => []),
    ]);
    const discountMap = {}; (levels || []).forEach(l => { discountMap[l.name] = Number(l.discount); }); // 等级→折扣率，供收银算价显示
    const store = (stores || []).find(s => s.store_id === REMOTE.storeId) || (stores || [])[0] || {};
    // 默认收银客户：取首位真实客户 + 钱包（真实流程应由收银台选客，此处给真实默认）
    let cashierCustomer = {};
    const c0 = (customers || [])[0];
    if (c0) {
      const w = await api.getWallet(c0.customer_id, {}).catch(() => null);
      cashierCustomer = { customerId: c0.customer_id, name: c0.name, level: c0.level || '—', cardNo: '—', hasCard: (w && (w.cards || [])[0]) ? (w.cards[0].name + ' · 余 ' + w.cards[0].remain + ' 次') : '—', balance: w ? (Number(w.storedCardBalance) || 0) : 0, storedCard: w ? (Number(w.storedCardBalance) || 0) : 0, points: w ? (w.points || 0) : 0, lastConsume: c0.last_consume || '—' };
    }
    return {
      ...EMPTY,
      store: { name: store.name || '', manager: store.manager || '', expire: '' },
      kpis: { turnover: stats.turnover, appts: appts.length, members: stats.customerCount },
      appointments: (appts || []).slice(0, 12).map(a => ({ time: (a.time || '').slice(11, 16), project: a.project, customer: '客户#' + a.customer_id, tech: a.tech || '待分配', status: a.status })),
      techs: (staff || []).filter(s => (s.role === '美容师' || s.role === '技师' || s.role === '产康师') && (s.status || '在职') === '在职').slice(0, 12).map(s => ({ staffId: s.staff_id, name: s.name, status: s.status || '在职' })),
      cashierCustomer,
      discountMap,
      // 收银目录排除「耗材」：耗材是 BOM 投入（收银时按项目自动扣减），不作可售单品，避免堆满收银台
      items: (items || []).filter(it => it.cat !== '耗材').map(it => ({ id: 'i' + it.item_id, name: it.name, cat: it.cat, price: it.sale_price, unit: it.unit })),
    };
    });
  } catch (e) { try { uni.showToast({ title: '加载失败，请检查网络后重试', icon: 'none' }); } catch (_) { } return EMPTY; }
}

/** 客户列表（含真实储值余额→推会员等级，映射为客户管理页同形）；未配置/失败返回空数组（不显示假数据）。 */
export async function loadCustomers(limit = 200) {
  if (!REMOTE.baseUrl) return [];
  try {
    return await withAuth(async () => {
      const api = makeApi();
      const cs = await api.listCustomers({ limit });
      if (!cs || !cs.length) return [];
      const wallets = await Promise.all(cs.map(c => api.getWallet(c.customer_id, {}).catch(() => null)));
      return cs.map((c, i) => {
        const bal = wallets[i] ? (Number(wallets[i].storedCardBalance) || 0) : 0;
        const level = levelOf(c.level, bal); // 等级口径与「会员数据」屏统一：优先 DB level，缺失按余额兜底
        return { customerId: c.customer_id, name: c.name, phone: c.phone, level, tags: [c.domain_first].filter(Boolean), balance: bal, last: (c.last_consume ? String(c.last_consume).slice(0, 10) : '—'), visitCount: c.visit_count || 0, totalSpend: Number(c.total_spend) || 0, advisor: c.advisor || '—' };
      });
    });
  } catch (e) { return []; }
}

/** 客户标签（真实 getTags，点开客户时按需拉，避免列表 N 次调用）+ 打/去标签 + 转店。id 可带 'c' 前缀。 */
const cid = (id) => Number(String(id).replace(/^c/, ''));
export async function getClientTags(id) {
  const t = await withAuth(() => makeApi().getTags(cid(id))).catch(() => []);
  return (Array.isArray(t) ? t : []).map((x) => (typeof x === 'string' ? x : (x.tag || x.name))).filter(Boolean);
}
export async function addClientTag(id, tag) { return withAuth(() => makeApi().addTag(cid(id), tag)); }
export async function removeClientTag(id, tag) { return withAuth(() => makeApi().removeTag(cid(id), tag)); }
export async function transferClient(id, toStoreId, reason) { return withAuth(() => makeApi().transfer(cid(id), Number(toStoreId), reason)); }

/** 二级「更多」屏按 key 取实时数据（经营数据/预约看板/品项/提成）。 */
export async function loadPage(key, filters) {
  if (!REMOTE.baseUrl) return null;
  try {
    return await withAuth(async () => {
    const api = makeApi();
    switch (key) {
      case 'bizData': {
        const [s, f, appts] = await Promise.all([api.getBusinessStats({}), api.getFunnel({}).catch(() => null), api.listAppointments({}).catch(() => [])]);
        return { metrics: [['营业额', Math.round(s.turnover || 0)], ['会员数', s.customerCount || 0], ['今日预约', appts.length], ['线索', f ? f.total : 0], ['到访', (f && f.byStatus) ? (f.byStatus['跟进中'] || 0) : 0], ['转化率', f ? (Math.round((f.conversionRate || 0) * 100) + '%') : '—']] };
      }
      case 'apptBoard': {
        const as = await api.listAppointments({});
        const by = (st) => as.filter(a => a.status === st).length;
        return {
          buckets: [['待接单', by('待接单')], ['待到店', by('待到店')], ['已到店', by('已到店')], ['已完成', by('已完成')], ['暂停占', by('暂停占')], ['未指定', by('未指定')], ['新客', by('新客')], ['全部', as.length]],
          cols: as.slice(0, 10).map(a => (a.time || '').slice(11, 16) + ' ' + a.project + ' · 客户#' + a.customer_id + ' · ' + (a.tech || '待分配') + ' · ' + a.status),
        };
      }
      case 'itemSettings': {
        const its = await api.listItems({ domain: DOMAIN });
        return { rows: its.slice(0, 40).map(it => [it.name, it.cat, it.domain || '—', it.sale_price, it.exp_price, (it.duration || '—') + 'min', it.status]) };
      }
      case 'commission': {
        const its = await api.listItems({ status: '启用', domain: DOMAIN });
        return { rows: its.slice(0, 40).map(it => [it.name, Math.round((it.member_commission || 0) * 100) + '%', Math.round((it.walkin_commission || 0) * 100) + '%', it.member_bonus || 0]) };
      }
      case 'payOrders': {
        const ff = { limit: 50, storeId: REMOTE.storeId || undefined }; // 按当前门店过滤
        if (filters) {
          if (filters.q) { if (/^XS/i.test(filters.q)) ff.orderNo = filters.q; else ff.q = filters.q; } // XS 前缀→订单号，否则客户名/手机号
          if (filters.payMethod) ff.payMethod = filters.payMethod;
          if (filters.date) { ff.dateFrom = filters.date; ff.dateTo = filters.date + 'T23:59:59'; } // 单日区间
        }
        const os = await api.listOrders(ff);
        return { rows: (os || []).map(o => [o.order_no, '客户#' + o.customer_id, o.domain || '—', o.order_amount, o.pay_method || '—', o.order_status, (o.created_at || '').slice(5, 16)]) };
      }
      case 'transferLog': {
        const ts = await api.listTransfers({});
        return { rows: (ts || []).slice(0, 50).map(t => ['客户#' + t.customer_id, '门店#' + t.from_store, '门店#' + t.to_store, t.reason || '—', (t.time || '').slice(5, 16)]) };
      }
      case 'memberStats': {
        const [cs, stats] = await Promise.all([api.listCustomers({ limit: 300 }), api.getBusinessStats({})]);
        const cnt = (lv) => (cs || []).filter(c => c.level === lv).length;
        return { metrics: [['会员总数', (cs || []).length], ['黑金卡', cnt('黑金')], ['钻石卡', cnt('钻石')], ['白银卡', cnt('白银')], ['体验卡', cnt('体验')], ['营业额', Math.round(stats.turnover || 0)]] };
      }
      case 'stockMgmt': {
        const inv = await api.listInventory({});
        return { rows: (inv || []).slice(0, 60).map(i => [i.name || ('品项#' + i.item_id), i.qty, i.warn_qty, i.low ? '⚠ 低库存' : '正常']) };
      }
      case 'scheduleBoard': {
        const [ss, staff] = await Promise.all([api.listSchedules({}), api.listStaff({}).catch(() => [])]);
        const nm = {}; (staff || []).forEach(s => { nm[s.staff_id] = s.name; });
        return { rows: (ss || []).slice(0, 50).map(s => [nm[s.staff_id] || ('员工#' + s.staff_id), s.work_date || '—', s.shift || '—', s.status || '正常']) };
      }
      default: return null;
    }
    });
  } catch (e) { return null; }
}

/** 管理页数据：人员/店铺/话术/库房（带 id 供行级操作）。未配置/失败返回 null。 */
export async function loadManage(key) {
  if (!REMOTE.baseUrl) return null;
  try {
    return await withAuth(async () => {
    const api = makeApi();
    if (key === 'staff') {
      const [staff, rolesResp] = await Promise.all([api.listStaff({}), api.listRoles().catch(() => [])]);
      const roles = (rolesResp && rolesResp.roles) || rolesResp || []; // /roles 返回 {roles:[...]}，兼容裸数组
      return {
        title: '人员管理', kind: 'list', addLabel: '新增员工',
        roleOptions: (Array.isArray(roles) ? roles : []).map(r => r.name).filter(Boolean),
        columns: ['姓名', '角色/部门', '职位', '电话', '状态'],
        rows: (staff || []).map(s => ({ id: s.staff_id, cells: [s.name, (s.role || '—') + (s.department ? ' · ' + s.department : ''), s.position || '—', s.phone || '—', (s.status || '在职') + (s.wx_notify ? ' · 微信✓' : '')], status: s.status || '在职', role: s.role })),
      };
    }
    if (key === 'store') {
      const list = (await api.listStores()) || [];
      const cur = REMOTE.storeId;
      // 多店列表：本店置顶；每行带完整字段供编辑；支持新增门店
      const sorted = [...list].sort((a, b) => (a.store_id === cur ? -1 : 0) - (b.store_id === cur ? -1 : 0));
      return {
        title: '店铺管理', kind: 'storeList', addLabel: '新增门店',
        rows: sorted.map(s => ({ id: s.store_id, cells: [s.name + (s.store_id === cur ? ' · 本店' : '') + (s.status === '停用' ? ' · 停用' : ''), (s.manager || '—') + ' · ' + (s.phone || '—') + (s.region ? ' · ' + s.region : '')], name: s.name || '', manager: s.manager || '', phone: s.phone || '', address: s.address || '', industry: s.industry || '', region: s.region || '', status: s.status || '正常', sortWeight: s.sort_weight ?? 0 })),
      };
    }
    if (key === 'scripts') {
      const sc = await api.listScripts({});
      return {
        title: '邀约话术', kind: 'list', addLabel: '新增话术',
        columns: ['场景', '标题', '状态'],
        rows: (sc || []).map(x => ({ id: x.script_id, cells: [x.scene || '—', x.title || '—', x.status || '启用'], status: x.status || '启用', title: x.title, content: x.content, scene: x.scene })),
      };
    }
    if (key === 'stock') {
      const inv = await api.listInventory({});
      return { title: '库房入出库', kind: 'stock', columns: ['品项', '库存', '预警'], rows: (inv || []).map(i => ({ itemId: i.item_id, cells: [i.name || ('品项#' + i.item_id), i.qty, i.warn_qty], qty: i.qty, low: i.low })) };
    }
    if (key === 'levels') {
      const ls = await api.listMemberLevels();
      const fmt = (d) => d >= 1 ? '不打折' : (Math.round(d * 1000) / 100) + ' 折'; // 0.85→8.5 折
      return { title: '会员等级折扣', kind: 'levels', rows: (ls || []).map(l => ({ name: l.name, discount: Number(l.discount), cells: [l.name, fmt(Number(l.discount))] })) };
    }
    return null;
    });
  } catch (e) { return null; }
}

/** 管理页写操作（真实后端）。返回 {ok, msg}。 */
export async function manageAction(key, action, payload) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  try {
    return await withAuth(async () => {
    const api = makeApi();
    const k = key + ':' + action;
    if (k === 'staff:create') await api.createStaff({ name: payload.name, phone: payload.phone, role: payload.role, position: payload.position, department: payload.department, wxNotify: payload.wxNotify === '开', storeId: REMOTE.storeId });
    else if (k === 'staff:toggle') await api.setStaffStatus(payload.id, payload.status === '在职' ? '离职' : '在职');
    else if (k === 'staff:role') await api.updateStaff(payload.id, { role: payload.role });
    else if (k === 'store:edit') await api.updateStore(payload.id, { name: payload.name, manager: payload.manager, phone: payload.phone, address: payload.address, industry: payload.industry, region: payload.region, status: payload.status, sortWeight: payload.sortWeight !== undefined && payload.sortWeight !== '' ? Number(payload.sortWeight) : undefined });
    else if (k === 'store:create') await api.createStore({ name: payload.name, manager: payload.manager, phone: payload.phone, address: payload.address, industry: payload.industry, region: payload.region, status: payload.status, sortWeight: payload.sortWeight !== undefined && payload.sortWeight !== '' ? Number(payload.sortWeight) : undefined });
    else if (k === 'scripts:create') await api.createScript({ scene: payload.scene, title: payload.title, content: payload.content });
    else if (k === 'scripts:toggle') await api.updateScript(payload.id, { status: payload.status === '启用' ? '停用' : '启用' });
    else if (k === 'scripts:remove') await api.removeScript(payload.id);
    else if (k === 'stock:inbound') await api.stockInbound(payload.itemId, payload.qty, payload.ref || '入库');
    else if (k === 'stock:outbound') await api.stockOutbound(payload.itemId, payload.qty, payload.ref || '出库');
    else if (k === 'levels:setDiscount') await api.setMemberLevelDiscount(payload.name, payload.discount);
    else return { ok: false, msg: '未知操作' };
    return { ok: true };
    });
  } catch (e) { return { ok: false, msg: (e && e.message) || '操作失败' }; }
}

/** 收银结算（真实下单）。idempotencyKey 由收银页按「一次结算意图」稳定生成并透传，
 *  失败/超时重试沿用同一键 → 后端幂等命中，杜绝重复下单/重复扣储值卡。 */
export async function checkout(customerId, lines, payMethod, paidAmount, idempotencyKey, executorId) {
  await ensureAuth();
  return makeApi().checkout({ customerId, lines, payMethod, paidAmount, executorId }, idempotencyKey);
}

/** 会员等级折扣配置：列表 + 设折扣（设置页用）。 */
export async function loadLevels() {
  if (!REMOTE.baseUrl) return [];
  try { return await withAuth(() => makeApi().listMemberLevels()) || []; } catch (e) { return []; }
}
export async function setLevelDiscount(name, discount) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  try { await withAuth(() => makeApi().setMemberLevelDiscount(name, discount)); return { ok: true }; }
  catch (e) { return { ok: false, msg: (e && e.message) || '设置失败' }; }
}

/** 退出登录（演示门户流转）：吊销令牌 + 清本地身份。H5 由「我的」页跳回门户换账号；小程序端待正式登录页接管。 */
export async function logoutRemote() {
  try { if (REMOTE.token && REMOTE.baseUrl) await makeApi().logout(); } catch (e) { /* 吊销失败也照常清本地 */ }
  REMOTE.token = ''; REMOTE.staffId = 0;
}
