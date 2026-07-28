/* 奇德芬芳 · 宝妈端 — 数据访问层（纯后端，无 mock）。经共享客户端 api.js(uniTransport) 打中台。
 * 数据全部来自后端：卡额/餐单/商城/订单/积分等。后端不可用时返回空壳/空数组，绝不显示假数据。
 * 全量小程序联调需微信开发者工具。*/
import { createApi, uniTransport } from './api.js';
import { EMPTY } from './data.js';
import { journeyOf, pickLatestMeals } from './logic.js';

export const REMOTE = { baseUrl: '', tenantId: 1, storeId: 1, customerId: 0, token: '' };
const AUTH_KEY = 'mom_customer_auth_v1';
const PENDING_ROUTE_KEY = 'mom_pending_route_v1';

export function makeApi() {
  return createApi({ baseUrl: REMOTE.baseUrl, tenantId: REMOTE.tenantId, storeId: REMOTE.storeId, token: REMOTE.token, transport: uniTransport });
}

export function applyAuth(result) {
  if (!result || !result.token || !result.customerId) throw new Error('登录结果无效');
  REMOTE.token = result.token;
  REMOTE.tenantId = Number(result.tenantId || 1);
  REMOTE.customerId = Number(result.customerId);
  try {
    uni.setStorageSync(AUTH_KEY, {
      token: REMOTE.token,
      tenantId: REMOTE.tenantId,
      customerId: REMOTE.customerId,
      accountId: Number(result.accountId || 0),
      phoneMasked: result.phoneMasked || '',
    });
  } catch (_) { /* storage 不可用时仍保留本次内存登录 */ }
  return result;
}

export function restoreAuth() {
  if (REMOTE.token) return true;
  try {
    const saved = uni.getStorageSync(AUTH_KEY);
    if (!saved || !saved.token || !saved.customerId) return false;
    REMOTE.token = saved.token;
    REMOTE.tenantId = Number(saved.tenantId || 1);
    REMOTE.customerId = Number(saved.customerId);
    return true;
  } catch (_) { return false; }
}

export function clearAuth() {
  REMOTE.token = '';
  REMOTE.customerId = 0;
  try { uni.removeStorageSync(AUTH_KEY); } catch (_) { /* noop */ }
}

export function isAuthenticated() { return Boolean(REMOTE.token || restoreAuth()); }

export function goLogin(redirect = '') {
  if (redirect && /^\/pages\/entry\/qr\?scene=[A-Za-z0-9_%\-]+$/.test(redirect)) {
    try { uni.setStorageSync(PENDING_ROUTE_KEY, redirect); } catch (_) { /* noop */ }
  }
  try { uni.reLaunch({ url: '/pages/login/login' }); } catch (_) { /* noop */ }
}

export function takePendingRoute() {
  try {
    const route = String(uni.getStorageSync(PENDING_ROUTE_KEY) || '');
    uni.removeStorageSync(PENDING_ROUTE_KEY);
    return /^\/pages\/entry\/qr\?scene=[A-Za-z0-9_%\-]+$/.test(route) ? route : '';
  } catch (_) { return ''; }
}

// #ifdef H5
/** 统一演示门户注入（本地 H5）：门户以选中客户身份换取 aud=customer 令牌后带 ?token= 跳入——直填身份免二次登录。
 *  仅接受客户令牌；解析失败静默回退演示登录。生产走微信 code2session 绑定，不经 URL 传令牌。 */
function tokenFromUrl() {
  try {
    const t = new URLSearchParams(location.search).get('token');
    if (!t) return false;
    const p = JSON.parse(decodeURIComponent(escape(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))));
    if (p.aud !== 'customer' || !p.tenantId || p.customerId == null) return false;
    applyAuth({ token: t, tenantId: p.tenantId, customerId: p.customerId });
    return true;
  } catch (e) { return false; }
}
// #endif
/** 恢复本地登录态。正式客户登录必须在登录页主动完成，不再自动选择演示账号。 */
export function ensureAuth() {
  // #ifdef H5
  if (!REMOTE.token && tokenFromUrl()) return Promise.resolve();
  // #endif
  restoreAuth();
  return Promise.resolve();
}
/** 包装一次取数：未登录或 token 过期时清理身份并返回登录页。 */
async function withAuth(run) {
  await ensureAuth();
  if (!REMOTE.token) { goLogin(); throw Object.assign(new Error('请先登录'), { status: 401 }); }
  try { return await run(); }
  catch (e) {
    if (e && e.status === 401) { clearAuth(); goLogin(); }
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
      const [cust, wallet, products, diet, appts, brand, profile] = await Promise.all([
        api.getCustomer(cid).catch(() => null),
        api.getWallet(cid, { month: ym, day: today }).catch(() => ({})),
        api.listProducts({ status: '在售' }).catch(() => []),
        api.listDiet({ customerId: cid, status: '已发布' }).catch(() => []), // 滤草稿
        api.listAppointments({ customerId: cid }).catch(() => []),
        api.getBrand().catch(() => null), // 品牌/运营文案(机构名/标语/积分位)：后端 settings 下发，替代前端写死
        api.getCustomerProfileContext().catch(() => null),
      ]);
      const displayName = (profile && profile.displayName) || (cust && cust.name) || '用户';
      const meals = pickLatestMeals(diet); // 取最近一个已发布日期的餐单，避免历史多日混排冒充今日
      return {
        ...EMPTY,
        brand: brand || { name: '奇德芬芳', latin: 'QIDE FENFANG' },
        me: cust ? { name: displayName, room: cust.intent_room || '', package: cust.intent_package || '', status: cust.status || '', avatar: displayName[0] || '用', guardianRole: profile && profile.guardianRole } : {},
        onboarding: cust ? {
          isNew: cust.status === '咨询' && !cust.intent_room && !cust.intent_package,
          needsProfile: !profile || !profile.profileComplete,
        } : { isNew: true, needsProfile: true },
        journey: journeyOf(cust),
        promo: (brand && brand.promo) || { title: '会员专属 · 我的积分', sub: '查看可用积分，兑换好礼' },
        balance: { pkg: wallet.storedCardBalance || 0, careCard: (wallet.cards || []).reduce((a, c) => a + (c.remain || 0), 0) },
        monthSpent: wallet.monthSpent || 0,
        schedule: (appts || []).slice(0, 6).map(a => ({ time: (a.time || '').slice(11, 16), title: a.project, sub: a.tech || '待分配', status: a.status })),
        mall: (products || []).map(p => ({ productId: p.product_id, name: p.name, cat: p.cat || '', spec: '', price: p.price, point: p.points_price || 0, recommend: p.status === '在售' })),
        todayMeals: meals.map(d => ({ meal: d.meal_type, menu: (JSON.parse(d.dishes_json || '[]')).join(' · '), remark: '', status: d.status })),
      };
    });
  } catch (e) {
    console.error('[mom.loadDashboard]', e);
    try { uni.showToast({ title: e && e.status ? '数据加载失败，请稍后重试' : '页面处理异常，请重新进入', icon: 'none' }); } catch (_) { }
    return EMPTY;
  }
}

export async function loadProfileContext() { return withAuth(() => makeApi().getCustomerProfileContext()); }
export async function saveProfileContext(input) { return withAuth(() => makeApi().updateCustomerProfileContext(input)); }
export async function createFamilyInvite(input = {}) { return withAuth(() => makeApi().createCustomerFamilyInvite(input)); }
export async function loadFamilyBindings() { return withAuth(() => makeApi().listCustomerFamilyBindings()); }
export async function acceptFamilyInvite(input) { return withAuth(() => makeApi().acceptCustomerFamilyInvite(input)); }
export async function loadRoomTypes() { return withAuth(() => makeApi().listCustomerRoomTypes()); }
export async function loadRoomLayout(filter) {
  return withAuth(async () => {
    const data = await makeApi().getCustomerRoomLayout(filter);
    return {
      ...(data || {}),
      floors: ((data && data.floors) || []).map(floor => ({
        ...floor,
        rooms: (floor.rooms || []).map(room => ({
          ...room,
          imageUrl: room.imageUrl && room.imageUrl.indexOf('/') === 0 ? REMOTE.baseUrl + room.imageUrl : room.imageUrl,
        })),
      })),
    };
  });
}
export async function loadRoomOrders() { return withAuth(() => makeApi().listCustomerRoomOrders()); }
export async function createRoomOrder(input) { return withAuth(() => makeApi().createCustomerRoomOrder(input)); }
export async function cancelRoomOrder(bookingId) { return withAuth(() => makeApi().cancelCustomerRoomOrder(bookingId)); }
export async function sandboxPayRoomOrder(bookingId) { return withAuth(() => makeApi().sandboxPayCustomerRoomOrder(bookingId)); }
export async function loadRehabCatalog() { return withAuth(() => makeApi().getCustomerRehabCatalog()); }
export async function createDirectRequest(input) { return withAuth(() => makeApi().createCustomerDirectRequest(input)); }
export async function resolveQrContext(scene) { return withAuth(() => makeApi().resolveQrContext(scene)); }
export async function createServiceRequest(input) { return withAuth(() => makeApi().createCustomerServiceRequest(input)); }
export async function loadServiceRequests() { return withAuth(() => makeApi().listCustomerServiceRequests({ customerId: REMOTE.customerId })); }
export async function loadServiceRecommendations() { return withAuth(() => makeApi().listServiceRecommendations({ customerId: REMOTE.customerId })); }
export async function chooseServiceRecommendation(recommendationId, input) { return withAuth(() => makeApi().chooseServiceRecommendation(recommendationId, input)); }

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
        // row[4]=post_id 供点赞用（通用列表只渲染前 4 列，row[4] 不显示）
        return { rows: (ps || []).slice(0, 20).map(p => [p.title, p.customer_id != null ? '客户#' + p.customer_id : '官方', (p.created_at || '').slice(5, 16), p.likes || 0, p.post_id]) };
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

/** 照片签名 URL 补前缀：后端回带签名的相对路径（15 分钟过期），拼 baseUrl 后 <image> 可直加载；过期后重拉接口刷新。 */
const absPhotos = (rows) => (rows || []).map((r) => ({
  ...r,
  photos: (r.photos || []).map((p) => ({ ...p, url: p.url && p.url.indexOf('/') === 0 ? REMOTE.baseUrl + p.url : p.url })),
}));

/** M-A F073：本人宝宝列表（多胎切换用）。服务端按令牌锁本人；失败/未配置返回空数组。 */
export async function loadBabies() {
  if (!REMOTE.baseUrl) return [];
  try {
    return await withAuth(async () => {
      if (!REMOTE.customerId) return [];
      return (await makeApi().listBabies({ customerId: REMOTE.customerId })) || [];
    });
  } catch (e) { return []; }
}

/** M-A F073：宝宝日志时间线（kind 可选：喂养|尿便|健康|护理|睡眠|哭闹，空=全部）。服务端已按 log_time 倒序。 */
export async function loadBabyTimeline(babyId, kind) {
  if (!REMOTE.baseUrl || !babyId) return [];
  try {
    return await withAuth(async () => absPhotos(await makeApi().getBabyTimeline(babyId, kind ? { kind } : undefined)));
  } catch (e) { return []; }
}

/** M-A F074：本人产后评估时间线。服务端按产后天数升序 → 反转为日期倒序供卡片渲染。 */
export async function loadMyCare() {
  if (!REMOTE.baseUrl) return [];
  try {
    return await withAuth(async () => {
      if (!REMOTE.customerId) return [];
      return absPhotos(await makeApi().getNursingTimeline(REMOTE.customerId)).reverse();
    });
  } catch (e) { return []; }
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

/** 贴吧点赞（原子自增，登录后调）。返回 {ok, msg}。 */
export async function likePost(postId) {
  if (!REMOTE.baseUrl) return { ok: false, msg: '未连接后端' };
  await ensureAuth();
  try { await makeApi().likePost(postId); return { ok: true }; }
  catch (e) { return { ok: false, msg: (e && e.message) || '点赞失败' }; }
}

/** 退出登录：尽量吊销服务端令牌，并清除本机保存的登录态。 */
export async function logoutRemote() {
  try { if (REMOTE.token && REMOTE.baseUrl) await makeApi().logout(); } catch (e) { /* 吊销失败也照常清本地 */ }
  clearAuth();
}
