import { createApi, fetchTransport } from '@shared/api'
import { useAuthStore } from '@/stores/auth'

// 复用三端共享的 framework-agnostic API 客户端（apps/shared/api.js），
// 已覆盖 70+ 后端接口；PC 端只需注入 baseUrl + 当前 token + 一个带 401 拦截的 transport。
// 后端地址优先级：URL ?api= 运行时覆盖（与三端 H5 同约定，便于后端改端口/避开占用） > 构建期 VITE_API_BASE > 默认本地 8799。
// hash 路由下 ?api= 写在 # 前（如 /admin/?api=http://127.0.0.1:8893#/login），location.search 可读到。
// 生产走同域 /api；若后台挂在 /yuezi/admin 子路径，API 用同前缀 /yuezi（nginx 反代该前缀→后端）。本地 dev 默认 8799。
function prodBase(): string {
  const seg = location.pathname.split('/').filter(Boolean)[0]      // /yuezi/admin/... → 'yuezi'；/admin/... → 'admin'
  const pfx = (seg && seg !== 'admin' && seg.indexOf('.') < 0) ? '/' + seg : ''
  return location.origin + pfx
}
const BASE = (typeof location !== 'undefined' && new URLSearchParams(location.search).get('api'))
  || import.meta.env.VITE_API_BASE
  || (typeof location !== 'undefined' && !/^5\d\d\d$/.test(location.port) ? prodBase() : 'http://127.0.0.1:8799')

// transport 包一层：401 → 清登录态并跳登录页（hash 路由，避免与 router 形成循环依赖）。
const transport = async (method: string, url: string, opt: any) => {
  const r = await fetchTransport(method, url, opt)
  if (r.status === 401) {
    try { useAuthStore().logout() } catch { /* ignore */ }
    if (!location.hash.startsWith('#/login')) location.hash = '#/login'
  }
  return r
}

// 每次取当前登录态构建 api（token 实时、零缓存负担）。
// 注意：不传 roles —— createApi 会把 roles 拼成 x-roles 头，而角色是中文串（如「店长」），
// HTTP 头只允许 ISO-8859-1，会让 fetch 直接抛错。带 token 时后端从 JWT 读 roles，无需该头。
export function api() {
  const auth = useAuthStore()
  return createApi({
    baseUrl: BASE,
    token: auth.token || undefined,
    tenantId: auth.tenantId ?? 1,
    storeId: auth.storeId ?? undefined,
    staffId: auth.staffId ?? undefined,
    transport,
  })
}

// —— 图片素材（P1 收口）——
// 三端共享客户端 shared/api.js 暂未含 media 方法（且不在本任务可改范围），此处 admin 侧直连 POST/GET /media。
function mediaHeaders(): Record<string, string> {
  const auth = useAuthStore()
  const h: Record<string, string> = { 'content-type': 'application/json', 'x-tenant-id': String(auth.tenantId ?? 1) }
  if (auth.token) h['authorization'] = 'Bearer ' + auth.token
  if (auth.storeId) h['x-store-id'] = String(auth.storeId)
  if (auth.staffId) h['x-staff-id'] = String(auth.staffId)
  return h
}
async function mediaReq(method: string, path: string, body?: unknown): Promise<any> {
  const r = await transport(method, BASE + path, { headers: mediaHeaders(), body: body ? JSON.stringify(body) : undefined })
  if (r.status >= 400) { const e: any = new Error((r.json && r.json.msg) || ('HTTP ' + r.status)); e.code = r.json && r.json.code; throw e }
  return r.json && r.json.data
}
export interface MediaUpload { refType: string; refId?: number | null; tag?: string | null; mime: string; dataBase64: string; alt?: string; sort?: number; visibility?: string; filename?: string }
export const mediaApi = {
  list: (p: { refType?: string; refId?: number; tag?: string } = {}): Promise<any[]> => {
    const q = Object.entries(p).filter(([, v]) => v !== undefined && v !== null && v !== '').map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&')
    return mediaReq('GET', '/api/v1/media' + (q ? '?' + q : ''))
  },
  upload: (p: MediaUpload): Promise<{ mediaId: number; url: string }> => mediaReq('POST', '/api/v1/media', p),
  remove: (id: number): Promise<{ removed: boolean }> => mediaReq('POST', `/api/v1/media/${id}/remove`),
}
// 媒体相对 url（/api/v1/media/:id）→ 绝对可加载地址（供 <img>/el-image src）。
export function mediaSrc(url: string): string { return /^https?:/.test(url) ? url : BASE + url }
