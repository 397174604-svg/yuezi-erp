/* 奇德芬芳 · 员工端 — 数据访问层（纯后端，无 mock）。经共享客户端 api.js(uniTransport) 打中台。
 * 数据全部来自后端：客户/线索/护理/订单/合同等。后端不可用时返回空壳/空数组，绝不显示假数据。
 * 全量小程序联调需微信开发者工具。*/
import { createApi, uniTransport } from './api.js';
import { EMPTY } from './data.js';
import { STAGE } from './logic.js';

export const REMOTE = { baseUrl: '', tenantId: 1, storeId: 1, staffId: 0, token: '', isManager: false, roles: [], perms: [], storeDomain: '' }; // roles/perms/storeDomain：仅用于前端入口门控；真正授权仍由后端校验
const AUTH_STORAGE_KEY = 'yue_staff_auth_v1';

/** 员工登录态跨刷新持久化。uni storage 同时覆盖 H5 localStorage 与小程序本地缓存。 */
function persistAuth() {
  if (!REMOTE.token) return;
  try {
    uni.setStorageSync(AUTH_STORAGE_KEY, {
      token: REMOTE.token,
      tenantId: REMOTE.tenantId,
      storeId: REMOTE.storeId,
      staffId: REMOTE.staffId,
      isManager: REMOTE.isManager,
      roles: REMOTE.roles,
      perms: REMOTE.perms,
      storeDomain: REMOTE.storeDomain,
    });
  } catch (_) { /* 存储不可用时仍允许当前会话继续 */ }
}

function restoreAuth() {
  if (REMOTE.token) return true;
  try {
    const a = uni.getStorageSync(AUTH_STORAGE_KEY);
    if (!a || !a.token || !a.staffId) return false;
    REMOTE.token = a.token;
    REMOTE.tenantId = Number(a.tenantId) || 1;
    REMOTE.storeId = a.storeId != null ? Number(a.storeId) : null;
    REMOTE.staffId = Number(a.staffId) || 0;
    REMOTE.isManager = !!a.isManager;
    REMOTE.roles = Array.isArray(a.roles) ? a.roles : [];
    REMOTE.perms = Array.isArray(a.perms) ? a.perms : [];
    REMOTE.storeDomain = a.storeDomain || '';
    return true;
  } catch (_) { return false; }
}

export function clearAuth() {
  REMOTE.token = '';
  REMOTE.staffId = 0;
  REMOTE.isManager = false;
  REMOTE.roles = [];
  REMOTE.perms = [];
  REMOTE.storeDomain = '';
  try { uni.removeStorageSync(AUTH_STORAGE_KEY); } catch (_) { /* noop */ }
}

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
  REMOTE.isManager = !!r.isManager; REMOTE.roles = Array.isArray(r.roles) ? r.roles : []; REMOTE.perms = Array.isArray(r.perms) ? r.perms : []; REMOTE.storeDomain = r.storeDomain || ''; // 权限来自登录响应/JWT，驱动入口门控
  persistAuth();
}
/** 员工登录（手机号+口令）。供登录页调用；成功后身份来自验签 token。 */
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
    REMOTE.token = t; REMOTE.tenantId = p.tenantId; REMOTE.storeId = p.storeId != null ? p.storeId : null; REMOTE.staffId = p.staffId != null ? p.staffId : 0; REMOTE.isManager = !!p.isManager; REMOTE.roles = Array.isArray(p.roles) ? p.roles : []; REMOTE.perms = Array.isArray(p.perms) ? p.perms : []; REMOTE.storeDomain = p.storeDomain || ''; // JWT payload 直取角色/权限/门店域
    persistAuth();
    // token 只消费一次，随后从地址栏移除；否则用户切换账号后刷新会被旧链接身份覆盖。
    try {
      const clean = new URL(location.href);
      clean.searchParams.delete('token');
      history.replaceState(null, '', clean.pathname + clean.search + clean.hash);
    } catch (_) { /* 非浏览器环境忽略 */ }
    return true;
  } catch (e) { return false; }
}
// #endif
export function ensureAuth() {
  // #ifdef H5
  if (!REMOTE.token && tokenFromUrl()) return Promise.resolve();
  // #endif
  // 页面刷新/小程序重启后优先恢复上次身份，不再自动切回第一个演示账号。
  if (!REMOTE.token && restoreAuth()) return Promise.resolve();
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
    if (e && e.status === 401) { clearAuth(); await ensureAuth(); return await run(); }
    throw e;
  }
}

export async function loadCustomerServiceRequests(status = '') {
  if (!REMOTE.baseUrl) return [];
  return withAuth(() => makeApi().listCustomerServiceRequests(status ? { status } : {}));
}

export async function updateCustomerServiceRequest(requestId, status, handledNote = '') {
  return withAuth(() => makeApi().setCustomerServiceRequestStatus(requestId, status, handledNote));
}

export async function loadRoomTurnoverTasks(status = '') {
  return withAuth(() => makeApi().listRoomTurnoverTasks(status ? { status } : {}));
}

export async function saveRoomTurnoverTask(taskId, input) {
  return withAuth(() => makeApi().updateRoomTurnoverTask(taskId, input));
}

export async function loadServiceRecommendationWorkbench() {
  return withAuth(async () => {
    const api = makeApi();
    const [recommendations, customers, items] = await Promise.all([
      api.listServiceRecommendations({}), api.listCustomers({ limit: 200 }), api.listItems({ status: '启用' }),
    ]);
    return { recommendations: recommendations || [], customers: customers || [], items: items || [] };
  });
}

export async function loadRecommendationBabies(customerId) {
  return withAuth(() => makeApi().listBabies({ customerId }));
}

export async function createServiceRecommendation(input) {
  return withAuth(() => makeApi().createServiceRecommendation(input));
}

export async function loadManagementDashboard() {
  return withAuth(async () => {
    const api = makeApi();
    const [cockpit, forecast] = await Promise.all([api.getManagementCockpit({}), api.getRevenueForecast({ historyDays: 30, forecastDays: 7 })]);
    return { cockpit, forecast };
  });
}

export async function loadQrManagerData() {
  return withAuth(async () => {
    const api = makeApi();
    const [qrCodes, stores, rooms] = await Promise.all([
      api.listMiniappQrCodes({}), api.listStores(), api.listRooms({}),
    ]);
    return { qrCodes: qrCodes || [], stores: stores || [], rooms: rooms || [] };
  });
}

export async function createManagedQrCode(input) {
  return withAuth(() => makeApi().createMiniappQrCode(input));
}

export async function setManagedQrCodeStatus(qrCodeId, status) {
  return withAuth(() => makeApi().setMiniappQrCodeStatus(qrCodeId, status));
}

export async function generateManagedQrCode(qrCodeId, envVersion) {
  return withAuth(() => makeApi().generateMiniappQrCode(qrCodeId, envVersion));
}

// STAGE（客户状态→筛选桶）已抽到 logic.js（可单测），此处 import 使用。
const mapClient = (c) => ({
  id: 'c' + c.customer_id, customerId: c.customer_id, name: c.name, avatar: (c.name || '客')[0],
  room: c.intent_room || '—', roomType: c.intent_room || '—', stage: STAGE(c.status), _status: c.status,
  tags: [c.domain_first].filter(Boolean), phone: c.phone, source: c.source, advisor: c.advisor,
  gender: c.gender, age: c.age, native: c.native, edc: c.edc, parity: c.parity, intentRoom: c.intent_room,
  balance: 0, follow: [], moon: null, lastRound: '—',
});

/** 拉取客户列表（映射为页面同形）；未配置/失败返回空数组（不显示假数据）。 */
export async function loadClients(limit = 200) {
  if (!REMOTE.baseUrl) return [];
  try { return await withAuth(async () => { const cs = await makeApi().listCustomers({ limit }); return (cs || []).map(mapClient); }); }
  catch (e) { return []; }
}

/** 工作台实时数据（全部后端）：经营/漏斗/跟进线索/待巡房/客户列表 + 当前员工。后端不可用 → 空壳。 */
export async function loadDashboard() {
  if (!REMOTE.baseUrl) return EMPTY;
  try {
    return await withAuth(async () => {
    const api = makeApi();
    const can = (perm) => REMOTE.isManager || REMOTE.perms.includes('*') || REMOTE.perms.includes(perm)
    const [stats, funnel, leads, nursing, customers, staff] = await Promise.all([
      api.getBusinessStats({}), can('leads') ? api.getFunnel({}) : Promise.resolve({ total: 0, converted: 0, byStatus: {} }),
      can('leads') ? api.listLeads({ status: '跟进中' }) : Promise.resolve([]),
      can('nursing') ? api.listNursing({ status: '待巡房' }) : Promise.resolve([]),
      can('customers') ? api.listCustomers({ limit: 200 }) : Promise.resolve([]), api.listStaff({}).catch(() => []),
    ]);
    // 按登录 token 中的 staffId 定位本人；列表第一条不是当前登录员工。
    const s0 = (staff || []).find(s => Number(s.staff_id) === Number(REMOTE.staffId));
    return {
      ...EMPTY,
      me: s0 ? { name: s0.name, role: s0.role || '员工', branch: '', avatar: (s0.name || '奇德芬芳')[0] } : {},
      kpis: { inhouse: stats.customerCount, rounds: nursing.length, follow: leads.length },
      funnel: { leads: funnel.total, visits: funnel.byStatus ? funnel.byStatus['跟进中'] : 0, signed: funnel.converted },
      clients: (customers || []).map(mapClient),
    };
    });
  } catch (e) { try { uni.showToast({ title: '加载失败，请检查网络后重试', icon: 'none' }); } catch (_) { } return EMPTY; }
}

/** 客户档案详情（getCustomer + 余额 + 时间线→跟进记录）；未配置/失败返回 null（页面保留 mock）。 */
export async function loadClient(id) {
  if (!REMOTE.baseUrl) return null;
  const cid = String(id).replace(/^c/, '');
  try {
    return await withAuth(async () => {
    const api = makeApi();
    const [c, wallet, timeline, tagList] = await Promise.all([
      api.getCustomer(cid), api.getWallet(cid, {}).catch(() => null), api.getTimeline(cid).catch(() => null), api.getTags(cid).catch(() => []),
    ]);
    if (!c) return null;
    // 真实标签（getTags）优先；取不到才回退 domain_first 单标签
    const realTags = (Array.isArray(tagList) && tagList.length) ? tagList.map((x) => (typeof x === 'string' ? x : (x.tag || x.name))).filter(Boolean) : [c.domain_first].filter(Boolean);
    const follow = (timeline && timeline.orders ? timeline.orders : []).slice(0, 6).map(o => ({
      date: (o.created_at || '').slice(5, 10), type: (o.domain || '') + '消费', by: '系统',
      note: '订单 ' + o.order_no + ' · ' + o.order_status + ' · ¥' + o.order_amount,
    }));
    return {
      id: 'c' + c.customer_id, customerId: c.customer_id, name: c.name, avatar: (c.name || '客')[0], phone: c.phone,
      wechat: c.wechat, idcard: c.id_no, gender: c.gender, age: c.age, native: c.native, edc: c.edc, parity: c.parity,
      source: c.source, channel: c.source, advisor: c.advisor, stage: STAGE(c.status), tags: realTags,
      intentLevel: c.level || 'A', intentRoom: c.intent_room, pkg: c.intent_package || '—',
      balance: wallet ? (Number(wallet.storedCardBalance) || 0) : 0, room: c.intent_room || '—', roomType: c.intent_room || '—',
      moon: null, follow,
    };
    });
  } catch (e) { return null; }
}

/** 客户打标签 / 去标签 / 转店（员工端写操作，供 client 页调用）。id 可带 'c' 前缀。 */
export async function addClientTag(id, tag) { return withAuth(() => makeApi().addTag(Number(String(id).replace(/^c/, '')), tag)); }
export async function removeClientTag(id, tag) { return withAuth(() => makeApi().removeTag(Number(String(id).replace(/^c/, '')), tag)); }
export async function transferClient(id, toStoreId, reason) { return withAuth(() => makeApi().transfer(Number(String(id).replace(/^c/, '')), Number(toStoreId), reason)); }

/** 二级「更多」屏按 key 取实时数据（有后端的接，没有的返回 null 保留 mock）。返回 {rows} 或 {metrics} 合并进 PAGES[key]。 */
export async function loadPage(key) {
  if (!REMOTE.baseUrl) return null;
  try {
    return await withAuth(async () => {
    const api = makeApi();
    switch (key) {
      case 'leads': {
        const ls = await api.listLeads({});
        return {
          rows: ls.map(l => [l.name, l.phone, l.wechat || '—', l.source, l.assignee || '待分配', l.status, l.edc || '—']),
          rowMeta: ls.map(l => ({ id: l.lead_id, actions: l.in_pool ? [{ label: '抢单', act: 'claim' }] : [] })), // 公海未领→可抢
        };
      }
      case 'contracts': {
        const os = await api.listOrders({ limit: 50 });
        return { rows: os.slice(0, 40).map(o => [o.order_no, '客户#' + o.customer_id, (o.domain || '') + '套餐', (o.domain || '') + '合同', o.order_amount, o.paid_amount, o.due_amount, '—', o.order_status === '已支付' ? '审核通过' : '待审核']) };
      }
      case 'goodsSale': {
        const its = await api.listItems({ status: '启用' });
        return { rows: its.slice(0, 40).map(it => [it.name, it.unit, it.sale_price, it.sale_price, '1.0', 1, it.sale_price]) };
      }
      case 'careDash': {
        const [stats, pend, all] = await Promise.all([api.getBusinessStats({}), api.listNursing({ status: '待巡房' }), api.listNursing({})]);
        const done = all.filter(n => n.status === '已完成').length;
        const abn = all.filter(n => n.abnormal && n.abnormal !== '正常').length;
        return { metrics: [['在住总数', stats.customerCount], ['待查房', pend.length], ['总服务', all.length], ['已服务', done], ['待服务', Math.max(0, all.length - done)], ['异常', abn]] };
      }
      case 'roomBoard': {
        const cs = await api.listCustomers({ limit: 200 });
        const ih = cs.filter(c => STAGE(c.status) === '在住'); // 用修正后的 STAGE，排除『已签合同但未入住』
        return { rows: ih.slice(0, 30).map(c => [c.intent_room || '—', c.intent_room || '—', c.name, '入住', c.edc || '—', '—', 0]) };
      }
      case 'healthAssess': {
        const cs = await api.listCustomers({ limit: 200 });
        const ih = cs.filter(c => STAGE(c.status) === '在住');
        return { rows: ih.slice(0, 30).map(c => [c.name, c.intent_room || '—', (c.name || '').replace('女士', '宝宝'), c.parity || '单胎', c.delivery_type || '—', c.edc || '—', c.status]) };
      }
      case 'approvals': {
        const rs = await api.listOpsRecords({ kind: '审批' });
        return {
          rows: rs.map(r => [r.title, r.customer_id ? '客户#' + r.customer_id : '—', r.staff_name || '—', r.amount || 0, (r.ts || '').slice(5, 16), r.status]),
          rowMeta: rs.map(r => ({ id: r.record_id, actions: !['审核通过', '已驳回'].includes(r.status) ? [{ label: '通过', act: 'approve' }, { label: '驳回', act: 'reject', danger: true }] : [] })),
        };
      }
      case 'visitReturn': {
        const rs = await api.listOpsRecords({ kind: '回访' });
        return { rows: rs.map(r => [r.customer_id ? '客户#' + r.customer_id : '—', '—', '本店', r.title, (r.ts || '').slice(5, 10), r.category || '客服部', r.status]) };
      }
      case 'complaint': {
        const rs = await api.listOpsRecords({ kind: '投诉' });
        return { rows: rs.map(r => [r.customer_id ? '客户#' + r.customer_id : '—', '—', r.title, r.category || '一般', (r.ts || '').slice(5, 10), r.handler || '—', r.status]) };
      }
      case 'satisfaction': {
        const rs = await api.listOpsRecords({ kind: '满意度' });
        return { rows: rs.map(r => [r.customer_id ? '客户#' + r.customer_id : '—', '—', r.title, (r.ts || '').slice(5, 10), (r.score >= 90 ? '非常满意' : '满意'), r.score, r.status]) };
      }
      case 'fees': {
        const rs = await api.listOpsRecords({ kind: '费用' });
        return { rows: rs.map(r => [r.ref_no || '—', r.title, r.title, r.category || '—', r.amount || 0, (r.ts || '').slice(5, 10), r.status]) };
      }
      case 'momServe': {
        const rs = await api.listOpsRecords({ kind: '月嫂派工' });
        return { rows: rs.map(r => [r.staff_name || '—', r.customer_id ? '客户#' + r.customer_id : '—', r.title, (r.ts || '').slice(5, 10), '8h', r.status]) };
      }
      case 'perfReport': {
        const os = await api.listOrders({ limit: 300 });
        const sum = (f) => os.filter(f).reduce((a, o) => a + (o.order_amount || 0), 0);
        return { metrics: [['订单数', os.length], ['销售合计', Math.round(sum(() => true))], ['月子销售', Math.round(sum(o => o.domain === '月子'))], ['产康销售', Math.round(sum(o => o.domain === '产康'))], ['已收款', Math.round(os.reduce((a, o) => a + (o.paid_amount || 0), 0))], ['待收款', Math.round(os.reduce((a, o) => a + (o.due_amount || 0), 0))]] };
      }
      default: return null; // 无对应后端 → 保留 mock
    }
    });
  } catch (e) { try { uni.showToast({ title: '加载失败，请检查网络后重试', icon: 'none' }); } catch (_) { } return null; }
}

/** 二级屏行级写动作（真实后端）：线索抢单 / 审批通过驳回。返回 {ok, msg}。 */
export async function pageAction(key, act, id) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  await ensureAuth();
  const api = makeApi();
  try {
    const k = key + ':' + act;
    if (k === 'leads:claim') await api.claimLead(id, String(REMOTE.staffId || '我'));
    else if (k === 'approvals:approve') await api.updateOpsRecord(id, { status: '审核通过' });
    else if (k === 'approvals:reject') await api.updateOpsRecord(id, { status: '已驳回' });
    else return { ok: false, msg: '未接入' };
    return { ok: true };
  } catch (e) { return { ok: false, msg: (e && e.message) || '操作失败' }; }
}

/** 公海抢单（真实写）。供线索页直接调用。 */
export async function claimLead(leadId, assignee) { await ensureAuth(); return makeApi().claimLead(leadId, assignee); }

/** 巡房：为指定客户建一条护理巡房记录（createNursing，record_kind=nursing）。返回 {ok, msg}。 */
export async function startRound(customerId, note) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  await ensureAuth();
  try {
    await makeApi().createNursing({ customerId, type: '巡房', status: '已完成', abnormal: note || '正常' });
    return { ok: true };
  } catch (e) { return { ok: false, msg: (e && e.message) || '操作失败' }; }
}

/* —— M-A 结构化巡房工作台（F070/F071/F072）——工作台页专用数据函数。 */

/** 评估枚举模板（恶露色/量/宫底/会阴/乳房/情绪 chip 选项，SOT 在后端）。失败返回 null（页面按未加载降级，不显示假选项）。 */
export async function loadAssessTemplate() {
  if (!REMOTE.baseUrl) return null;
  try { return await withAuth(() => makeApi().nursingTemplate()); } catch (e) { return null; }
}

/** 某客户的宝宝档案列表（多胎 → 工作台 tab）。失败返回空数组。 */
export async function loadBabies(customerId) {
  if (!REMOTE.baseUrl) return [];
  try { return (await withAuth(() => makeApi().listBabies({ customerId }))) || []; } catch (e) { return []; }
}

/** 查开放睡眠段（上次巡房记了「入睡」、end_time 还空）：timeline?kind=睡眠 第一条 end_time 为空的。无则 null。 */
export async function loadOpenSleep(babyId) {
  if (!REMOTE.baseUrl) return null;
  try {
    return await withAuth(async () => {
      const rows = await makeApi().babyTimeline(babyId, { kind: '睡眠' });
      const open = (rows || []).find((r) => !r.end_time);
      return open ? { logId: Number(open.log_id), logTime: open.log_time } : null;
    });
  } catch (e) { return null; }
}

/** 闭合开放睡眠段（记录醒来，endTime 缺省=服务端当前时间）。返回 {ok,msg}。 */
export async function closeSleepLog(babyId, logId, endTime) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  try { await withAuth(() => makeApi().closeBabyLog(babyId, logId, endTime)); return { ok: true }; }
  catch (e) { return { ok: false, msg: (e && e.message) || '操作失败' }; }
}

/** 巡房整包提交（服务端单事务：宝妈评估 + N 条宝宝日志 + 巡房完成记录，任一步非法整包回滚）。
 *  成功返回 {ok, nursingId, assessId?, logIds[]}（logIds 与提交 babyLogs 同序，供照片回填）。 */
export async function submitRoundFull(payload) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  try { const r = await withAuth(() => makeApi().roundFull(payload)); return { ok: true, ...r }; }
  catch (e) { return { ok: false, msg: (e && e.message) || '提交失败' }; }
}

/** 照护拍照上传（F072：先传图得 mediaId 存草稿，记录落库后 attachPhoto 回填 refId）。dataBase64 可带 data: 前缀。 */
export async function uploadCarePhoto(refType, mime, dataBase64) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  try { const r = await withAuth(() => makeApi().uploadCareMedia({ refType, mime, dataBase64 })); return { ok: true, ...r }; }
  catch (e) { return { ok: false, msg: (e && e.message) || '上传失败' }; }
}

/** 照片回填挂载到已落库记录（失败可重试，不阻塞巡房主流程）。refType: baby_log | postpartum_assessment。 */
export async function attachPhoto(mediaId, refType, refId) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  try { await withAuth(() => makeApi().attachMedia(mediaId, refType, refId)); return { ok: true }; }
  catch (e) { return { ok: false, msg: (e && e.message) || '回填失败' }; }
}

/** 退出登录（演示门户流转）：吊销令牌 + 清本地身份。H5 由「我的」页跳回门户换账号；小程序端待正式登录页接管。 */
export async function logoutRemote() {
  try { if (REMOTE.token && REMOTE.baseUrl) await makeApi().logout(); } catch (e) { /* 吊销失败也照常清本地 */ }
  clearAuth();
}
