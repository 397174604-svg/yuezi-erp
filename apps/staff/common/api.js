// 奇德芬芳 · 三端共享 API 客户端（框架无关）。
// transport 可插拔：H5/测试用 fetchTransport，微信小程序用 uniTransport。
// 三端把 common/data.js 的 mock 切真实接口时统一走此客户端（onLaunch 注入 baseUrl + 租户身份）。

/** @typedef {{status:number, json:any}} Resp */
/** @typedef {(method:string, url:string, opt:{headers:Record<string,string>, body?:string})=>Promise<Resp>} Transport */

function qs(obj) {
  if (!obj) return '';
  const p = Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => encodeURIComponent(k) + '=' + encodeURIComponent(String(v)));
  return p.length ? '?' + p.join('&') : '';
}
function rid() { // 幂等键：时间+随机，符合 ^[A-Za-z0-9_-]{1,128}$
  return 'idem-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
}

/**
 * @param {{baseUrl:string, tenantId:number, storeId?:number, staffId?:number, roles?:string[], transport:Transport}} cfg
 */
export function createApi(cfg) {
  const base = cfg.baseUrl.replace(/\/$/, '');
  const hdr = (extra = {}) => ({
    ...(cfg.token ? { authorization: 'Bearer ' + cfg.token } : {}),
    'x-tenant-id': String(cfg.tenantId),
    ...(cfg.storeId ? { 'x-store-id': String(cfg.storeId) } : {}),
    ...(cfg.staffId ? { 'x-staff-id': String(cfg.staffId) } : {}),
    ...(cfg.roles ? { 'x-roles': cfg.roles.join(',') } : {}),
    'content-type': 'application/json',
    ...extra,
  });
  const unwrap = (r) => { if (r.status >= 400) { const e = new Error((r.json && r.json.msg) || ('HTTP ' + r.status)); e.code = r.json && r.json.code; e.status = r.status; throw e; } return r.json && r.json.data; };

  return {
    listCustomers: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/customers' + qs(filter), { headers: hdr() })),
    getCustomer: async (id) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id, { headers: hdr() })),
    checkout: async (input, idempotencyKey = rid()) =>
      unwrap(await cfg.transport('POST', base + '/api/v1/cashier/checkout', { headers: hdr({ 'idempotency-key': idempotencyKey }), body: JSON.stringify(input) })),
    transfer: async (id, toStoreId, reason) =>
      unwrap(await cfg.transport('POST', base + '/api/v1/customers/' + id + '/transfer', { headers: hdr(), body: JSON.stringify({ toStoreId, reason }) })),
    listOrders: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/orders' + qs(filter), { headers: hdr() })),
    getOrder: async (orderNo) => unwrap(await cfg.transport('GET', base + '/api/v1/orders/' + orderNo, { headers: hdr() })),
    getWallet: async (id, opt) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id + '/wallet' + qs(opt), { headers: hdr() })),
    getBusinessStats: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/stats/business' + qs(filter), { headers: hdr() })),
    getManagementCockpit: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/stats/cockpit' + qs(filter), { headers: hdr() })),
    getRevenueForecast: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/stats/revenue-forecast' + qs(filter), { headers: hdr() })),
    listAppointments: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/appointments' + qs(filter), { headers: hdr() })),
    createAppointment: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/appointments', { headers: hdr(), body: JSON.stringify(input) })),
    setAppointmentStatus: async (apptId, status) => unwrap(await cfg.transport('PATCH', base + '/api/v1/appointments/' + apptId, { headers: hdr(), body: JSON.stringify({ status }) })),
    listCustomerServiceRequests: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/customer-service-requests' + qs(filter), { headers: hdr() })),
    setCustomerServiceRequestStatus: async (requestId, status, handledNote = '') => unwrap(await cfg.transport('PATCH', base + '/api/v1/customer-service-requests/' + requestId, { headers: hdr(), body: JSON.stringify({ status, handledNote }) })),
    listServiceRecommendations: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/service-recommendations' + qs(filter), { headers: hdr() })),
    createServiceRecommendation: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/service-recommendations', { headers: hdr(), body: JSON.stringify(input) })),
    listMiniappQrCodes: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/miniapp-qr-codes' + qs(filter), { headers: hdr() })),
    createMiniappQrCode: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/miniapp-qr-codes', { headers: hdr(), body: JSON.stringify(input) })),
    setMiniappQrCodeStatus: async (qrCodeId, status) => unwrap(await cfg.transport('PATCH', base + '/api/v1/miniapp-qr-codes/' + qrCodeId, { headers: hdr(), body: JSON.stringify({ status }) })),
    generateMiniappQrCode: async (qrCodeId, envVersion) => unwrap(await cfg.transport('POST', base + '/api/v1/miniapp-qr-codes/' + qrCodeId + '/image', { headers: hdr(), body: JSON.stringify({ envVersion }) })),
    listInventory: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/inventory' + qs(filter), { headers: hdr() })),
    stockInbound: async (itemId, qty, ref) => unwrap(await cfg.transport('POST', base + '/api/v1/inventory/inbound', { headers: hdr(), body: JSON.stringify({ itemId, qty, ref }) })),
    stockOutbound: async (itemId, qty, ref) => unwrap(await cfg.transport('POST', base + '/api/v1/inventory/outbound', { headers: hdr(), body: JSON.stringify({ itemId, qty, ref }) })),
    listStockMovements: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/inventory/movements' + qs(filter), { headers: hdr() })),
    listItems: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/items' + qs(filter), { headers: hdr() })),
    createItem: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/items', { headers: hdr(), body: JSON.stringify(input) })),
    updateItem: async (itemId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/items/' + itemId, { headers: hdr(), body: JSON.stringify(patch) })),
    getTags: async (id) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id + '/tags', { headers: hdr() })),
    addTag: async (id, tag) => unwrap(await cfg.transport('POST', base + '/api/v1/customers/' + id + '/tags', { headers: hdr(), body: JSON.stringify({ tag }) })),
    removeTag: async (id, tag) => unwrap(await cfg.transport('POST', base + '/api/v1/customers/' + id + '/untag', { headers: hdr(), body: JSON.stringify({ tag }) })),
    listLeads: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/leads' + qs(filter), { headers: hdr() })),
    createLead: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/leads', { headers: hdr(), body: JSON.stringify(input) })),
    claimLead: async (leadId, assignee) => unwrap(await cfg.transport('POST', base + '/api/v1/leads/' + leadId + '/claim', { headers: hdr(), body: JSON.stringify({ assignee }) })),
    convertLeadStatus: async (leadId, status) => unwrap(await cfg.transport('PATCH', base + '/api/v1/leads/' + leadId, { headers: hdr(), body: JSON.stringify({ status }) })),
    getFunnel: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/stats/funnel' + qs(filter), { headers: hdr() })),
    listStores: async () => unwrap(await cfg.transport('GET', base + '/api/v1/stores', { headers: hdr() })),
    listRooms: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/rooms' + qs(filter), { headers: hdr() })),
    listRoomTurnoverTasks: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/room-turnover-tasks' + qs(filter), { headers: hdr() })),
    updateRoomTurnoverTask: async (taskId, input) => unwrap(await cfg.transport('PATCH', base + '/api/v1/room-turnover-tasks/' + taskId, { headers: hdr(), body: JSON.stringify(input) })),
    createRoom: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/rooms', { headers: hdr(), body: JSON.stringify(input) })),
    updateRoom: async (roomId, input) => unwrap(await cfg.transport('PATCH', base + '/api/v1/rooms/' + roomId, { headers: hdr(), body: JSON.stringify(input) })),
    removeRoom: async (roomId) => unwrap(await cfg.transport('POST', base + '/api/v1/rooms/' + roomId + '/remove', { headers: hdr() })),
    mediaList: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/media' + qs(filter), { headers: hdr() })),
    uploadMedia: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/media', { headers: hdr(), body: JSON.stringify(input) })),
    removeMedia: async (mediaId) => unwrap(await cfg.transport('POST', base + '/api/v1/media/' + mediaId + '/remove', { headers: hdr() })),
    createStore: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/stores', { headers: hdr(), body: JSON.stringify(input) })),
    updateStore: async (storeId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/stores/' + storeId, { headers: hdr(), body: JSON.stringify(patch) })),
    listStaff: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/staff' + qs(filter), { headers: hdr() })),
    createStaff: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/staff', { headers: hdr(), body: JSON.stringify(input) })),
    updateStaff: async (staffId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/staff/' + staffId, { headers: hdr(), body: JSON.stringify(patch) })),
    setStaffStatus: async (staffId, status) => unwrap(await cfg.transport('PATCH', base + '/api/v1/staff/' + staffId, { headers: hdr(), body: JSON.stringify({ status }) })),
    listRoles: async () => unwrap(await cfg.transport('GET', base + '/api/v1/roles', { headers: hdr() })),
    listMemberLevels: async () => unwrap(await cfg.transport('GET', base + '/api/v1/member-levels', { headers: hdr() })), // 会员等级折扣（只读，供产康收银算价展示；设折扣属管理 CRUD 归 PC 后台）
    listScripts: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/scripts' + qs(filter), { headers: hdr() })),
    createScript: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/scripts', { headers: hdr(), body: JSON.stringify(input) })),
    updateScript: async (scriptId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/scripts/' + scriptId, { headers: hdr(), body: JSON.stringify(patch) })),
    removeScript: async (scriptId) => unwrap(await cfg.transport('POST', base + '/api/v1/scripts/' + scriptId + '/remove', { headers: hdr() })),
    pushNotice: async (id, type, title) => unwrap(await cfg.transport('POST', base + '/api/v1/customers/' + id + '/notices', { headers: hdr(), body: JSON.stringify({ type, title }) })),
    listNotices: async (id) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id + '/notices', { headers: hdr() })),
    markNoticeRead: async (noticeId) => unwrap(await cfg.transport('POST', base + '/api/v1/notices/' + noticeId + '/read', { headers: hdr() })),
    listNursing: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/nursing' + qs(filter), { headers: hdr() })),
    createNursing: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/nursing', { headers: hdr(), body: JSON.stringify(input) })),
    setNursingStatus: async (serviceId, status) => unwrap(await cfg.transport('PATCH', base + '/api/v1/nursing/' + serviceId, { headers: hdr(), body: JSON.stringify({ status }) })),
    listHandovers: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/handovers' + qs(filter), { headers: hdr() })),
    createHandover: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/handovers', { headers: hdr(), body: JSON.stringify(input) })),
    confirmHandover: async (handoverId) => unwrap(await cfg.transport('POST', base + '/api/v1/handovers/' + handoverId + '/confirm', { headers: hdr() })),
    listSchedules: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/schedules' + qs(filter), { headers: hdr() })),
    createSchedule: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/schedules', { headers: hdr(), body: JSON.stringify(input) })),
    updateSchedule: async (scheduleId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/schedules/' + scheduleId, { headers: hdr(), body: JSON.stringify(patch) })),
    removeSchedule: async (scheduleId) => unwrap(await cfg.transport('POST', base + '/api/v1/schedules/' + scheduleId + '/remove', { headers: hdr() })),
    getTimeline: async (id) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id + '/timeline', { headers: hdr() })),
    listTransfers: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/transfers' + qs(filter), { headers: hdr() })),
    listDiet: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/diet' + qs(filter), { headers: hdr() })),
    createDiet: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/diet', { headers: hdr(), body: JSON.stringify(input) })),
    updateDiet: async (planId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/diet/' + planId, { headers: hdr(), body: JSON.stringify(patch) })),
    removeDiet: async (planId) => unwrap(await cfg.transport('POST', base + '/api/v1/diet/' + planId + '/remove', { headers: hdr() })),
    listProducts: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/products' + qs(filter), { headers: hdr() })),
    createProduct: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/products', { headers: hdr(), body: JSON.stringify(input) })),
    updateProduct: async (productId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/products/' + productId, { headers: hdr(), body: JSON.stringify(patch) })),
    mallPurchase: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/mall/purchase', { headers: hdr(), body: JSON.stringify(input) })),
    getPoints: async (id) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id + '/points', { headers: hdr() })),
    listPointLedger: async (id) => unwrap(await cfg.transport('GET', base + '/api/v1/customers/' + id + '/points/ledger', { headers: hdr() })),
    earnPoints: async (id, amount, reason) => unwrap(await cfg.transport('POST', base + '/api/v1/customers/' + id + '/points/earn', { headers: hdr(), body: JSON.stringify({ amount, reason }) })),
    redeemPoints: async (id, amount, reason) => unwrap(await cfg.transport('POST', base + '/api/v1/customers/' + id + '/points/redeem', { headers: hdr(), body: JSON.stringify({ amount, reason }) })),
    listPosts: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/posts' + qs(filter), { headers: hdr() })),
    createPost: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/posts', { headers: hdr(), body: JSON.stringify(input) })),
    updatePost: async (postId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/posts/' + postId, { headers: hdr(), body: JSON.stringify(patch) })),
    likePost: async (postId) => unwrap(await cfg.transport('POST', base + '/api/v1/posts/' + postId + '/like', { headers: hdr() })),
    removePost: async (postId) => unwrap(await cfg.transport('POST', base + '/api/v1/posts/' + postId + '/remove', { headers: hdr() })),
    listMallOrders: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/mall/orders' + qs(filter), { headers: hdr() })),
    listOpsRecords: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/ops/records' + qs(filter), { headers: hdr() })),
    createOpsRecord: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/ops/records', { headers: hdr(), body: JSON.stringify(input) })),
    updateOpsRecord: async (recordId, patch) => unwrap(await cfg.transport('PATCH', base + '/api/v1/ops/records/' + recordId, { headers: hdr(), body: JSON.stringify(patch) })),
    listNannies: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/nannies' + qs(filter), { headers: hdr() })),
    login: async (phone, password) => unwrap(await cfg.transport('POST', base + '/api/v1/auth/login', { headers: hdr(), body: JSON.stringify({ phone, password }) })),
    loginCustomer: async (customerId) => unwrap(await cfg.transport('POST', base + '/api/v1/auth/login-customer', { headers: hdr(), body: JSON.stringify({ customerId }) })),
    demoAccounts: async () => unwrap(await cfg.transport('GET', base + '/api/v1/auth/demo-accounts', { headers: hdr() })),
    logout: async () => unwrap(await cfg.transport('POST', base + '/api/v1/auth/logout', { headers: hdr() })),
    // —— M-A 结构化巡房（F070/F071/F072）：整包提交 / 评估模板 / 宝宝日志 / 照护拍照 ——（命名对齐 apps/shared/api.js）
    roundFull: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/nursing/round-full', { headers: hdr(), body: JSON.stringify(input) })),
    nursingTemplate: async () => unwrap(await cfg.transport('GET', base + '/api/v1/nursing-assessments/template', { headers: hdr() })),
    listBabies: async (filter) => unwrap(await cfg.transport('GET', base + '/api/v1/babies' + qs(filter), { headers: hdr() })),
    babyTimeline: async (babyId, filter) => unwrap(await cfg.transport('GET', base + '/api/v1/babies/' + babyId + '/timeline' + qs(filter), { headers: hdr() })),
    closeBabyLog: async (babyId, logId, endTime) => unwrap(await cfg.transport('POST', base + '/api/v1/babies/' + babyId + '/logs/' + logId + '/close', { headers: hdr(), body: JSON.stringify(endTime ? { endTime } : {}) })),
    uploadCareMedia: async (input) => unwrap(await cfg.transport('POST', base + '/api/v1/media/care', { headers: hdr(), body: JSON.stringify(input) })),
    attachMedia: async (mediaId, refType, refId) => unwrap(await cfg.transport('POST', base + '/api/v1/media/' + mediaId + '/attach', { headers: hdr(), body: JSON.stringify({ refType, refId }) })),
    _raw: cfg.transport, // 需要原始 {status,json} 时
  };
}

/** H5 / 测试：基于全局 fetch（15s 超时，弱网/挂起自动中止 → 上层 catch 提示重试）。 */
export const fetchTransport = async (method, url, opt) => {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const r = await fetch(url, { method, headers: opt.headers, body: opt.body, signal: ctrl.signal });
    let json = null; try { json = await r.json(); } catch { /* 非 JSON */ }
    return { status: r.status, json };
  } finally { clearTimeout(timer); }
};

/** 微信小程序：基于 uni.request（mp 运行时全局 uni；15s 超时）。 */
export const uniTransport = (method, url, opt) => new Promise((resolve, reject) => {
  // eslint-disable-next-line no-undef
  uni.request({
    url, method, header: opt.headers, data: opt.body ? JSON.parse(opt.body) : undefined, timeout: 15000,
    success: (res) => resolve({ status: res.statusCode, json: res.data }),
    fail: reject,
  });
});
