import { defineStore } from 'pinia'

// 登录态：复用后端 HS256 JWT（员工/管理员 token）。
// token 仅作请求凭证 + 展示用字段；真正的数据域/越权拦截由后端 RLS + 角色校验兜底。
export interface AuthSession {
  token: string
  tenantId: number | null
  storeId: number | null
  staffId: number | null
  role: string
  roles: string[]
  perms: string[] // 后端按角色解析的可访问模块 key；管理层为 ['*']
  managerFlag: boolean // 后端 is_manager 标志（角色权限表配置）
  expireAt: number // 毫秒时间戳
}

const KEY = 'yue-admin-auth'

export const useAuthStore = defineStore('auth', {
  state: (): AuthSession => ({
    token: '',
    tenantId: null,
    storeId: null,
    staffId: null,
    role: '',
    roles: [],
    perms: [],
    managerFlag: false,
    expireAt: 0,
  }),
  getters: {
    isAuthed: (s): boolean => !!s.token && s.expireAt > Date.now(),
    // 管理层：优先用后端 is_manager 标志；兜底用内置管理角色名（防旧会话/解析缺失漏权）
    isManager: (s): boolean => s.managerFlag || s.roles.some((r) => ['店长', '管理员', '老板', '店长助理', '运营', '跨店授权'].includes(r)),
    // 总部(老板/运营)：是管理层但只监督不做门店一线操作。用于 storeOnly 页隐藏 + 各页写按钮 !isHQ 门。店长/店长助理不属总部。
    isHQ: (s): boolean => s.roles.some((r) => ['老板', '运营'].includes(r)),
    // 模块可见性：管理层或 perms 含 '*' → 全部；否则按 perms 列表
    canModule: (s) => (key: string): boolean =>
      s.managerFlag || s.perms.includes('*') || s.perms.includes(key) ||
      s.roles.some((r) => ['店长', '管理员', '老板', '店长助理', '运营', '跨店授权'].includes(r)),
  },
  actions: {
    // 接收 /api/v1/auth/login 返回的会话对象
    setSession(p: any) {
      this.token = p?.token || ''
      this.tenantId = p?.tenantId ?? null
      this.storeId = p?.storeId ?? null
      this.staffId = p?.staffId ?? null
      this.role = p?.role || ''
      this.roles = Array.isArray(p?.roles) ? p.roles : (p?.role ? [p.role] : [])
      this.perms = Array.isArray(p?.perms) ? p.perms : []
      this.managerFlag = !!p?.isManager
      this.expireAt = Date.now() + (Number(p?.expiresIn) || 7200) * 1000
      this.persist()
    },
    logout() {
      this.$reset()
      try { localStorage.removeItem(KEY) } catch { /* ignore */ }
    },
    persist() {
      try { localStorage.setItem(KEY, JSON.stringify(this.$state)) } catch { /* ignore */ }
    },
    restore() {
      try {
        const raw = localStorage.getItem(KEY)
        if (!raw) return
        const s = JSON.parse(raw)
        if (s && s.token && s.expireAt > Date.now()) Object.assign(this.$state, s)
        else localStorage.removeItem(KEY)
      } catch { /* ignore */ }
    },
  },
})
