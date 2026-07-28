import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { menu, canSee, firstVisiblePath } from '@/router/menu'
import AppLayout from '@/layout/AppLayout.vue'

const moduleRoutes: RouteRecordRaw[] = menu.map((m) => ({
  path: m.path,
  name: m.path,
  component: m.component as any,
  meta: { title: m.title, icon: m.icon, moduleKey: m.path, managerOnly: !!m.managerOnly, perm: m.perm, storeOnly: !!m.storeOnly, isModule: true },
}))

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: AppLayout,
    redirect: '/dashboard',
    children: [
      ...moduleRoutes,
      { path: '403', name: 'forbidden', component: () => import('@/views/error/Forbidden.vue'), meta: { title: '无权访问', hidden: true } },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'notfound', component: () => import('@/views/error/NotFound.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫：登录态 + 模块级 RBAC（与侧栏 canSee 同源）。管理层放行全部；
// managerOnly 模块非管理层拒；其余按后端下发 perms 命中。前端只管「能看到/能进」，
// 真正的数据权限由后端 requireManager + RLS 兜底。
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta?.public) return true
  if (!auth.isAuthed) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.meta?.isModule) {
    const item = { path: to.meta.moduleKey as string, managerOnly: to.meta.managerOnly as boolean, perm: to.meta.perm as string | undefined, storeOnly: to.meta.storeOnly as boolean } as never
    if (!canSee(item, auth.isManager, auth.perms, auth.isHQ)) {
      // 越权访问 → 重定向到当前身份第一个可见模块（一线访问 /dashboard 会落到其业务首页，不再兜底放行看到全店数据）
      const fb = '/' + firstVisiblePath(auth.isManager, auth.perms, auth.isHQ)
      return to.path !== fb ? { path: fb } : { path: '/403' }
    }
  }
  return true
})

export default router
