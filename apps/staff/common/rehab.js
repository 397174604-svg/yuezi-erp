/* 奇德芬芳 · 员工端 产康板块数据访问层（独立文件，不污染 remote.js）。
 * 复用 remote.js 的 makeApi/ensureAuth/REMOTE（同一登录态，不重复登录）。
 * R1 收银串域根治：所有品项/客户查询显式限 domain='产康'，产康台绝不列月子品项。
 * 订单域由后端按 customer.domain_first 派生（checkout 不传 domain）→ 故收银选客限定 domain_first='产康' 客户，
 *   这样开出的订单 domain 恒为产康（与后端 cashierService 契约一致，本阶段不改后端）。*/
import { REMOTE, makeApi, ensureAuth, clearAuth } from './remote.js';
import { REHAB_EMPTY } from './data.js';
import { levelOf } from './logic.js';

const DOMAIN = '产康'; // 本板块业务域（R1 域过滤基准）

/** 401 重登重试包装（与 remote.withAuth 同语义；产康板块自持一份，保持文件独立）。 */
async function withAuth(run) {
  await ensureAuth();
  try { return await run(); }
  catch (e) {
    if (e && e.status === 401) { clearAuth(); await ensureAuth(); return await run(); }
    throw e;
  }
}

/** 仅产康客户（domain_first='产康'）原始行。后端 listCustomers 暂不支持 domain_first 过滤 → 前端按域筛（不改后端 customer 契约）。 */
async function rawRehabCustomers(api, limit = 200) {
  const cs = await api.listCustomers({ limit });
  return (cs || []).filter(c => c.domain_first === DOMAIN);
}

/** 产康客户 + 真实钱包（等级/储值/积分）：供收银换客户与客户二级屏。每客户一次 getWallet。 */
async function fetchRehabCustomers(api, limit = 200) {
  const cs = await rawRehabCustomers(api, limit);
  if (!cs.length) return [];
  const wallets = await Promise.all(cs.map(c => api.getWallet(c.customer_id, {}).catch(() => null)));
  return cs.map((c, i) => {
    const w = wallets[i]; const bal = w ? (Number(w.storedCardBalance) || 0) : 0;
    const card0 = (w && (w.cards || [])[0]) || null;
    return {
      customerId: c.customer_id, name: c.name, phone: c.phone, level: levelOf(c.level, bal),
      cardNo: '—', hasCard: card0 ? (card0.name + ' · 余 ' + card0.remain + ' 次') : '—',
      storedCard: bal, balance: bal, points: w ? (w.points || 0) : 0,
      last: (c.last_consume ? String(c.last_consume).slice(0, 10) : '—'), advisor: c.advisor || '—',
    };
  });
}

/** 产康工作台实时数据：门店/经营 KPI/今日预约/在岗技师/收银品项(限产康)/默认收银客户(首位产康客户)/等级折扣。 */
export async function loadDashboard() {
  if (!REMOTE.baseUrl) return REHAB_EMPTY;
  try {
    return await withAuth(async () => {
      const api = makeApi();
      const [stats, appts, items, stores, staff, custs, levels] = await Promise.all([
        api.getBusinessStats({}), api.listAppointments({}),
        api.listItems({ domain: DOMAIN, status: '启用' }),               // R1：收银品项显式限产康域
        api.listStores().catch(() => []), api.listStaff({}).catch(() => []),
        rawRehabCustomers(api, 50).catch(() => []), api.listMemberLevels().catch(() => []),
      ]);
      const discountMap = {}; (levels || []).forEach(l => { discountMap[l.name] = Number(l.discount); }); // 等级→折扣率，供收银算价显示
      const store = (stores || []).find(s => s.store_id === REMOTE.storeId) || (stores || [])[0] || {};
      let cashierCustomer = { ...REHAB_EMPTY.cashierCustomer };
      const c0 = (custs || [])[0]; // 默认收银客户=首位产康客户（换客户仍限产康，见 cashier.vue）
      if (c0) {
        const w = await api.getWallet(c0.customer_id, {}).catch(() => null);
        const card0 = (w && (w.cards || [])[0]) || null;
        cashierCustomer = {
          customerId: c0.customer_id, name: c0.name, level: c0.level || '—', cardNo: '—',
          hasCard: card0 ? (card0.name + ' · 余 ' + card0.remain + ' 次') : '—',
          balance: w ? (Number(w.storedCardBalance) || 0) : 0, storedCard: w ? (Number(w.storedCardBalance) || 0) : 0,
          points: w ? (w.points || 0) : 0, lastConsume: c0.last_consume || '—',
        };
      }
      return {
        ...REHAB_EMPTY,
        store: { name: store.name || '', manager: store.manager || '', expire: '' },
        kpis: { turnover: stats.turnover, appts: appts.length, members: stats.customerCount },
        appointments: (appts || []).slice(0, 12).map(a => ({ time: (a.time || '').slice(11, 16), project: a.project, customer: '客户#' + a.customer_id, tech: a.tech || '待分配', status: a.status })),
        techs: (staff || []).filter(s => ['技师', '产康师', '护士'].includes(s.role) && (s.status || '在职') === '在职').slice(0, 12).map(s => ({ staffId: s.staff_id, name: s.name, status: s.status || '在职' })),
        cashierCustomer, discountMap,
        items: (items || []).map(it => ({ id: 'i' + it.item_id, name: it.name, cat: it.cat, price: it.sale_price, unit: it.unit })),
      };
    });
  } catch (e) { try { uni.showToast({ title: '加载失败，请检查网络后重试', icon: 'none' }); } catch (_) { } return REHAB_EMPTY; }
}

/** 产康客户列表（真实储值→等级）：供收银换客户选客 + 客户二级屏。仅 domain_first='产康'。 */
export async function loadCustomers(limit = 200) {
  if (!REMOTE.baseUrl) return [];
  try { return await withAuth(() => fetchRehabCustomers(makeApi(), limit)); } catch (e) { return []; }
}

/** 收银结算（真实下单）：不传 domain，订单域由后端按 customer.domain_first 派生（选客已限产康 → 订单恒为产康）。
 *  idempotencyKey 由收银页按「一次结算意图」稳定生成透传，失败/超时重试沿用同键 → 后端幂等命中，杜绝重复下单/重复扣储值卡。 */
export async function checkout(customerId, lines, payMethod, paidAmount, idempotencyKey, executorId) {
  await ensureAuth();
  return makeApi().checkout({ customerId, lines, payMethod, paidAmount, executorId }, idempotencyKey);
}

/** 二级「更多」屏按 key 取实时数据（平移 rehab 的 9 屏 + 产康客户）。品项类一律限 domain='产康'（R1）。 */
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
          const its = await api.listItems({ domain: DOMAIN }); // R1：品项设置只列产康域
          return { rows: its.slice(0, 40).map(it => [it.name, it.cat, it.domain || '—', it.sale_price, it.exp_price, (it.duration || '—') + 'min', it.status]) };
        }
        case 'commission': {
          const its = await api.listItems({ domain: DOMAIN, status: '启用' }); // R1：提成只列产康域
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
          const [cs, stats] = await Promise.all([rawRehabCustomers(api, 300), api.getBusinessStats({})]);
          const cnt = (lv) => cs.filter(c => c.level === lv).length;
          return { metrics: [['产康会员', cs.length], ['黑金卡', cnt('黑金')], ['钻石卡', cnt('钻石')], ['白银卡', cnt('白银')], ['体验卡', cnt('体验')], ['营业额', Math.round(stats.turnover || 0)]] };
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
        case 'rehabCustomers': {
          const cs = await fetchRehabCustomers(api, 200);
          return { rows: cs.map(c => [c.name, c.phone || '—', c.level, c.balance, c.last, c.advisor]) };
        }
        default: return null;
      }
    });
  } catch (e) { return null; }
}
