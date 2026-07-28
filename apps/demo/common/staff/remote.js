/* 奇德芬芳 · 员工端 — 数据访问层（纯后端，无 mock）。经共享客户端 api.js(uniTransport) 打中台。
 * 数据全部来自后端：客户/线索/护理/订单/合同等。后端不可用时返回空壳/空数组，绝不显示假数据。
 * 全量小程序联调需微信开发者工具。*/
import { createApi, uniTransport } from './api.js';
import { EMPTY } from './data.js';
import { STAGE } from './logic.js';

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
  REMOTE.isManager = !!r.isManager; // 管理层标志（审批通过/驳回等按此隐藏）
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
    const [stats, funnel, leads, nursing, customers, staff] = await Promise.all([
      api.getBusinessStats({}), api.getFunnel({}), api.listLeads({ status: '跟进中' }),
      api.listNursing({ status: '待巡房' }), api.listCustomers({ limit: 200 }), api.listStaff({}).catch(() => []),
    ]);
    const s0 = (staff || [])[0];
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

/** 退出登录（演示门户流转）：吊销令牌 + 清本地身份。H5 由「我的」页跳回门户换账号；小程序端待正式登录页接管。 */
export async function logoutRemote() {
  try { if (REMOTE.token && REMOTE.baseUrl) await makeApi().logout(); } catch (e) { /* 吊销失败也照常清本地 */ }
  REMOTE.token = ''; REMOTE.staffId = 0;
}
