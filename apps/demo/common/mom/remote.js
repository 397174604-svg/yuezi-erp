/* 奇德芬芳 · 宝妈端 — 数据访问层（纯后端，无 mock）。经共享客户端 api.js(uniTransport) 打中台。
 * 数据全部来自后端：卡额/餐单/商城/订单/积分等。后端不可用时返回空壳/空数组，绝不显示假数据。
 * 全量小程序联调需微信开发者工具。*/
import { createApi, uniTransport } from './api.js';
import { EMPTY } from './data.js';
import { journeyOf, pickLatestMeals } from './logic.js';

export const REMOTE = { baseUrl: '', tenantId: 1, storeId: 1, customerId: 0, token: '' };

export function makeApi() {
  return createApi({ baseUrl: REMOTE.baseUrl, tenantId: REMOTE.tenantId, storeId: REMOTE.storeId, token: REMOTE.token, transport: uniTransport });
}

let authing = null; // 并发登录单例
// #ifdef H5
/** 统一演示门户注入（本地 H5）：门户以选中客户身份换取 aud=customer 令牌后带 ?token= 跳入——直填身份免二次登录。
 *  仅接受客户令牌；解析失败静默回退演示登录。生产走微信 code2session 绑定，不经 URL 传令牌。 */
function tokenFromUrl() {
  try {
    const t = new URLSearchParams(location.search).get('token');
    if (!t) return false;
    const p = JSON.parse(decodeURIComponent(escape(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))));
    if (p.aud !== 'customer' || !p.tenantId || p.customerId == null) return false;
    REMOTE.token = t; REMOTE.tenantId = p.tenantId; REMOTE.customerId = p.customerId;
    return true;
  } catch (e) { return false; }
}
// #endif
/** 确保已登录：宝妈端 dev 用演示客户(或 ?cid)登录换 token；生产换微信 code2session→openid 绑定。并发复用同一登录。 */
export function ensureAuth() {
  // #ifdef H5
  if (!REMOTE.token && tokenFromUrl()) return Promise.resolve();
  // #endif
  if (REMOTE.token || !REMOTE.baseUrl) return Promise.resolve();
  if (!authing) authing = (async () => {
    const api = makeApi();
    let cid = REMOTE.customerId;
    if (!cid) { const demo = await api.demoAccounts(); cid = demo.mom ? demo.mom.customerId : 1; }
    const r = await api.loginCustomer(cid);
    REMOTE.token = r.token; REMOTE.tenantId = r.tenantId; REMOTE.customerId = r.customerId; // 身份来自验签 token
  })().catch(() => { /* 生产未绑定 → 需登录/绑定流程 */ }).finally(() => { authing = null; });
  return authing;
}
/** 包装一次取数：token 过期(401) 时清 token 重登并重试一次，避免长驻会话卡死。 */
async function withAuth(run) {
  await ensureAuth();
  try { return await run(); }
  catch (e) {
    if (e && e.status === 401) { REMOTE.token = ''; await ensureAuth(); return await run(); }
    throw e;
  }
}
// journeyOf / pickLatestMeals 已抽到 logic.js（可单测），此处 import 使用。

/** 我的月子实时数据（全部后端）：本人档案/卡额/本月消费 + 今日日程 + 商城 + 今日餐单。后端不可用 → 空壳。 */
export async function loadDashboard() {
  if (!REMOTE.baseUrl) return EMPTY;
  try {
    return await withAuth(async () => {
      if (!REMOTE.customerId) return EMPTY;
      const api = makeApi(); const cid = REMOTE.customerId;
      const today = new Date().toISOString().slice(0, 10); const ym = today.slice(0, 7);
      // 各调用独立 .catch 降级：单接口失败只缺对应板块，不清空整页
      const [cust, wallet, products, diet, appts] = await Promise.all([
        api.getCustomer(cid).catch(() => null),
        api.getWallet(cid, { month: ym, day: today }).catch(() => ({})),
        api.listProducts({ status: '在售' }).catch(() => []),
        api.listDiet({ customerId: cid, status: '已发布' }).catch(() => []), // 滤草稿
        api.listAppointments({ customerId: cid }).catch(() => []),
      ]);
      const meals = pickLatestMeals(diet); // 取最近一个已发布日期的餐单，避免历史多日混排冒充今日
      return {
        ...EMPTY,
        me: cust ? { name: cust.name, room: cust.intent_room || '', avatar: (cust.name || '奇德芬芳')[0] } : {},
        journey: journeyOf(cust),
        promo: { title: '会员专属 · 我的积分', sub: '查看可用积分，兑换好礼' },
        balance: { pkg: wallet.storedCardBalance || 0, careCard: (wallet.cards || []).reduce((a, c) => a + (c.remain || 0), 0) },
        monthSpent: wallet.monthSpent || 0,
        schedule: (appts || []).slice(0, 6).map(a => ({ time: (a.time || '').slice(11, 16), title: a.project, sub: a.tech || '待分配', status: a.status })),
        mall: (products || []).map(p => ({ productId: p.product_id, name: p.name, cat: p.cat || '', spec: '', price: p.price, point: p.points_price || 0, recommend: p.status === '在售' })),
        todayMeals: meals.map(d => ({ meal: d.meal_type, menu: (JSON.parse(d.dishes_json || '[]')).join(' · '), remark: '', status: d.status })),
      };
    });
  } catch (e) { try { uni.showToast({ title: '加载失败，请检查网络后重试', icon: 'none' }); } catch (_) { } return EMPTY; }
}

/** 商城在售商品（映射为商城页同形）；未配置/失败返回空数组（不显示假数据）。 */
export async function loadMall() {
  if (!REMOTE.baseUrl) return [];
  try {
    return await withAuth(async () => {
      const ps = await makeApi().listProducts({ status: '在售' });
      return (ps || []).map(p => ({ productId: p.product_id, name: p.name, cat: p.cat || '', spec: p.spec || '', price: p.price, point: p.points_price || 0, recommend: p.status === '在售' }));
    });
  } catch (e) { return []; }
}

/** 二级「更多」屏按 key 取实时数据（有后端的接，没有的返回 null 保留 mock）。 */
export async function loadPage(key) {
  if (!REMOTE.baseUrl) return null;
  try {
    return await withAuth(async () => {
    if (!REMOTE.customerId) return null;
    const api = makeApi(); const cid = REMOTE.customerId;
    const today = new Date().toISOString().slice(0, 10); const ym = today.slice(0, 7);
    const careCnt = (w) => (w.cards || []).reduce((a, c) => a + (c.remain || 0), 0);
    switch (key) {
      case 'mealCard': {
        const w = await api.getWallet(cid, { month: ym, day: today });
        return { metrics: [['套餐余额', w.storedCardBalance || 0], ['餐卡余额', w.storedCardBalance || 0], ['护理卡(次)', careCnt(w)], ['本月消费', w.monthSpent || 0], ['今日消费', w.todaySpent || 0], ['积分', w.points || 0]] };
      }
      case 'profileMom': {
        const [w, c] = await Promise.all([api.getWallet(cid, { month: ym, day: today }), api.getCustomer(cid)]);
        return { note: c.name + ' · ' + (c.intent_room || ''), metrics: [['套餐余额', w.storedCardBalance || 0], ['护理卡(次)', careCnt(w)], ['本月消费', w.monthSpent || 0], ['积分', w.points || 0]] };
      }
      case 'consume': {
        const t = await api.getTimeline(cid); const os = (t && t.orders) || [];
        return { rows: os.slice(0, 30).map(o => [(o.domain || '') + '消费', (o.created_at || '').slice(5, 10), o.pay_method || '—', -(o.paid_amount || o.order_amount || 0)]) };
      }
      case 'careRecords': {
        const ns = await api.listNursing({ customerId: cid });
        return { rows: ns.slice(0, 20).map(n => [n.type || '护理', (n.time || '').slice(5, 10), ((n.abnormal && n.abnormal !== '正常') ? '⚠' + n.abnormal : '正常') + (n.baby_name ? ' · ' + n.baby_name : '')]) };
      }
      case 'apptMom': {
        const as = await api.listAppointments({ customerId: cid });
        return { rows: as.slice(0, 20).map(a => [a.project, a.time, a.tech || '待分配', a.status]) };
      }
      case 'points': {
        const [p, led] = await Promise.all([api.getPoints(cid).catch(() => null), api.listPointLedger(cid).catch(() => [])]);
        return { note: '当前可用 ' + ((p && p.points != null) ? p.points : 0) + ' 分 · 获取途径：消费/登录/评论/分享/转介绍', rows: (led || []).slice(0, 30).map(x => [x.reason || '积分', x.delta > 0 ? '获取积分' : '使用积分', x.delta, (x.created_at || '').slice(5, 10), '']) };
      }
      case 'notices': {
        const ns = await api.listNotices(cid);
        return { rows: (ns || []).slice(0, 30).map(n => [n.title, (n.time || '').slice(5, 16), n.read ? '已读' : '未读']) };
      }
      case 'forum': {
        const ps = await api.listPosts({});
        return { rows: (ps || []).slice(0, 20).map(p => [p.title, p.customer_id != null ? '客户#' + p.customer_id : '官方', (p.created_at || '').slice(5, 16), p.likes || 0]) };
      }
      case 'productOrders': {
        const os = await api.listMallOrders({ customerId: cid });
        return { rows: (os || []).map(o => ['DD' + o.mall_order_id, o.pay_kind || '—', o.amount || 0, (o.created_at || '').slice(5, 10), '—', '已完成']) };
      }
      case 'nannies': {
        const ns = await api.listNannies({});
        return { rows: (ns || []).map(n => [n.name, n.age, n.type, n.level || '—', n.fee || 0, n.status]) };
      }
      case 'parenting': {
        const rs = await api.listOpsRecords({ kind: '育儿知识' });
        return { rows: (rs || []).map(r => [r.title, r.category || '—', '图文', r.status === '置顶' ? '是' : '否']) };
      }
      case 'expertQA': {
        const rs = await api.listOpsRecords({ kind: '专家问答' });
        return { rows: (rs || []).map(r => [r.title, r.expert || '—', (r.ts || '').slice(5, 10), r.status]) };
      }
      default: return null;
    }
    });
  } catch (e) { try { uni.showToast({ title: '加载失败，请检查网络后重试', icon: 'none' }); } catch (_) { } return null; }
}

/** 商城购买（真实下单，支持积分支付）。idempotencyKey 由商城页按一次购买意图稳定生成→失败重试不重复下单。 */
export async function buy(productId, qty, payKind, idempotencyKey) { await ensureAuth(); return makeApi().mallPurchase({ customerId: REMOTE.customerId, productId, qty, payKind }, idempotencyKey); }

/** AI 育儿问答（U3a）：检索式硬校验——命中返回库内答案+免责声明；未命中后端记录并转人工，前端如实展示，绝不编造。 */
export async function askQa(query) {
  if (!REMOTE.baseUrl) return { matched: false, msg: '未连接后端', disclaimer: '' };
  return withAuth(() => makeApi().qaAsk(query, REMOTE.customerId));
}

/** 二级屏 header 写动作（真实后端）：产康预约 / 专家提问 / 贴吧发帖。返回 {ok, msg}。 */
export async function pageAction(key, act, input) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  await ensureAuth();
  const api = makeApi(); const cid = REMOTE.customerId;
  try {
    if (key === 'apptMom' && act === 'book') {
      const t = new Date(Date.now() + 86400000).toISOString().slice(0, 10) + 'T10:00:00'; // 默认次日 10:00，待门店接单
      await api.createAppointment({ customerId: cid, project: input, time: t, status: '待接单' });
    } else if (key === 'expertQA' && act === 'ask') {
      await api.createOpsRecord({ kind: '专家问答', title: input, customerId: cid });
    } else if (key === 'forum' && act === 'post') {
      await api.createPost({ title: input, kind: '社区', customerId: cid }); // 贴吧=社区类
    } else return { ok: false, msg: '未接入' };
    return { ok: true };
  } catch (e) { return { ok: false, msg: (e && e.message) || '操作失败' }; }
}

/** 退出登录（演示门户流转）：吊销令牌 + 清本地身份。H5 由「我的」页跳回门户换账号；小程序端待正式登录页接管。 */
export async function logoutRemote() {
  try { if (REMOTE.token && REMOTE.baseUrl) await makeApi().logout(); } catch (e) { /* 吊销失败也照常清本地 */ }
  REMOTE.token = ''; REMOTE.customerId = 0;
}
