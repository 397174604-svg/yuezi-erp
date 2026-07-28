import Vue from 'vue'
import Router from 'vue-router'
import Layout from '@/layout'
import { erpMenuGroups, getPageType } from '@/config/erp-menu'
import { originalPageUrls } from '@/config/original-page-evidence'

Vue.use(Router)

const isMvpMode = process.env.VUE_APP_RUNTIME_MODE === 'mvp'
const modulePage = () => import('@/views/erp/module/index')
const foundationPage = () => import('@/views/erp/foundation/index')
const mamaBoxPage = () => import('@/views/erp/mama-box/index')
const customerEntryPage = () => import('@/views/erp/customer-entry/index')
const customerWorkbenchPage = () => import('@/views/erp/customer-workbench/index')
const salesWorkbenchPage = () => import('@/views/erp/sales-workbench/index')
const financeWorkbenchPage = () => import('@/views/erp/finance-workbench/index')
const roomWorkbenchPage = () => import('@/views/erp/room-workbench/index')
const nursingWorkbenchPage = () => import('@/views/erp/nursing-workbench/index')
const rehabWorkbenchPage = () => import('@/views/erp/rehab-workbench/index')
const dietWorkbenchPage = () => import('@/views/erp/diet-workbench/index')
const inventoryWorkbenchPage = () => import('@/views/erp/inventory-workbench/index')
const mallWorkbenchPage = () => import('@/views/erp/mall-workbench/index')
const riskWorkbenchPage = () => import('@/views/erp/risk-workbench/RiskServiceMatrix')
const reportWorkbenchPage = () => import('@/views/erp/report-workbench/index')
const basicWorkbenchPage = () => import('@/views/erp/basic-workbench/index')
const systemWorkbenchPage = () => import('@/views/erp/system-workbench/index')
const maternityNurseWorkbenchPage = () => import('@/views/erp/maternity-nurse-workbench/index')
const mvpWorkbenchPage = () => import('@/views/erp/mvp-workbench/index')
const foundationPageTypes = ['organization', 'role-permission', 'user-account', 'data-dictionary', 'operation-permission']
const RouterView = { name: 'ErpRouterView', render: h => h('router-view') }
const legacyGroupNavIds = {
  customer: 524,
  sales: 75,
  finance: 89,
  room: 234,
  nursing: -1,
  recovery: 504,
  matron: -1,
  diet: -1,
  warehouse: 336,
  mall: 468,
  risk: -1,
  report: -1,
  basic: -1,
  system: -1
}
const legacyPrimaryPageNavIds = {
  customer: {
    客户中心: 565,
    客户录入: 76,
    线索管理: 522,
    我的客户: 596,
    客户管理: 77,
    跟进记录: 540,
    签单客户: 601,
    预约参观: 469,
    公海客户: 525,
    入住探访记录: 81,
    满意度调查表: 532,
    客户回访记录: 79,
    客户投诉建议: 80,
    消息计划模板: 657,
    客户消息: 658,
    积分设置: 481,
    积分记录: 533,
    发布活动: 527
  },
  sales: {
    合同管理: 85,
    商品销售: 523,
    销售明细: 602,
    套餐管理: 87,
    卡类套餐: 412,
    赠送管理: 237,
    优惠管理: 310,
    优惠券管理: 534,
    赠送项目申请: 556
  },
  finance: {
    新增收款: 521,
    收款管理: 90,
    退款申请: 95,
    退款审核: 96,
    欠款审核: 281,
    换货审核: 653,
    发票管理: 572,
    部门物料预算: 251,
    我的费用: 317,
    费用审核: 607,
    付款管理: 415
  },
  room: {
    房态图: 418,
    房态趋势: 526,
    房型趋势: 587,
    智能排房: 517,
    可售房统计: 567,
    房型列表: 424,
    订房管理: 375,
    入住管理: 558,
    续住信息: 615,
    换房申请: 584,
    物品赠送: 284,
    客房服务: 236,
    外出申请: 113,
    物品借还: 235,
    洗衣管理: 238
  }
}

function legacyPageNavId(groupKey, title) {
  const configured = (legacyPrimaryPageNavIds[groupKey] || {})[title]
  if (configured) return configured
  const originalUrl = (originalPageUrls[groupKey] || {})[title] || ''
  const match = originalUrl.match(/navid=(\d+)/)
  return match ? Number(match[1]) : -1
}

function getPageComponent(pageType) {
  if (foundationPageTypes.includes(pageType)) return foundationPage
  if (pageType === 'customer-entry') return customerEntryPage
  if (pageType === 'customer-workbench') return customerWorkbenchPage
  if (pageType === 'sales-workbench') return salesWorkbenchPage
  if (pageType === 'finance-workbench') return financeWorkbenchPage
  if (pageType === 'room-workbench') return roomWorkbenchPage
  if (pageType === 'nursing-workbench') return nursingWorkbenchPage
  if (pageType === 'rehab-workbench') return rehabWorkbenchPage
  if (pageType === 'diet-workbench') return dietWorkbenchPage
  if (pageType === 'inventory-workbench') return inventoryWorkbenchPage
  if (pageType === 'mall-workbench') return mallWorkbenchPage
  if (pageType === 'risk-workbench') return riskWorkbenchPage
  if (pageType === 'report-workbench') return reportWorkbenchPage
  if (pageType === 'basic-workbench') return basicWorkbenchPage
  if (pageType === 'system-workbench') return systemWorkbenchPage
  if (pageType === 'maternity-nurse-workbench') return maternityNurseWorkbenchPage
  if (pageType.startsWith('mama-')) return mamaBoxPage
  return modulePage
}

function createPageRoute(group, title, path, name, section) {
  const pageType = getPageType(group.key, title)
  const legacyNavId = legacyPageNavId(group.key, title)
  return {
    path,
    component: getPageComponent(pageType),
    name,
    meta: {
      title,
      group: group.title,
      groupKey: group.key,
      section: section || '',
      pageType,
      legacyNavId,
      color: group.color,
      noCache: true
    }
  }
}

function createGroupChildren(group) {
  const children = []
  const legacyRedirects = []
  let legacyIndex = 0

  group.items.forEach((entry, index) => {
    if (typeof entry === 'string') {
      legacyIndex += 1
      children.push(createPageRoute(group, entry, `item-${legacyIndex}`, `Erp${group.key}${legacyIndex}`))
      return
    }

    const sectionChildren = entry.items.map((title, childIndex) => {
      legacyIndex += 1
      const childPath = `item-${childIndex + 1}`
      const target = `/${group.key}/${entry.key}/${childPath}`
      const legacyNavId = legacyPageNavId(group.key, title)
      legacyRedirects.push({
        path: `item-${legacyIndex}`,
        redirect: target,
        hidden: true,
        meta: { legacyNavId }
      })
      return createPageRoute(group, title, childPath, `Erp${group.key}${entry.key}${childIndex + 1}`, entry.title)
    })

    children.push({
      path: entry.key,
      component: RouterView,
      redirect: 'noRedirect',
      name: `Erp${group.key}Section${index + 1}`,
      alwaysShow: true,
      meta: { title: entry.title, icon: entry.icon, color: group.color },
      children: sectionChildren
    })
  })

  return [...children, ...legacyRedirects]
}

const erpRoutes = erpMenuGroups.map(group => ({
  path: `/${group.key}`,
  component: Layout,
  redirect: 'noRedirect',
  name: `Erp${group.key}`,
  alwaysShow: true,
  meta: {
    title: group.title,
    icon: group.icon,
    color: group.color,
    // Some legacy groups have no stable parent navid. In that case leave the
    // parent neutral and let its real child navids decide visibility; using
    // N-1 here incorrectly removed the whole authorized group.
    ...(legacyGroupNavIds[group.key] > 0
      ? { legacyNavId: legacyGroupNavIds[group.key] }
      : {})
  },
  children: createGroupChildren(group)
}))

export const constantRoutes = [
  {
    path: '/redirect',
    component: Layout,
    hidden: true,
    children: [{ path: '/redirect/:path(.*)', component: () => import('@/views/redirect/index') }]
  },
  { path: '/login', component: () => import('@/views/login/index'), hidden: true },
  { path: '/auth-redirect', component: () => import('@/views/login/auth-redirect'), hidden: true },
  { path: '/404', component: () => import('@/views/error-page/404'), hidden: true },
  { path: '/401', component: () => import('@/views/error-page/401'), hidden: true },
  {
    path: '/',
    component: Layout,
    redirect: isMvpMode ? '/mvp/workbench' : '/dashboard',
    hidden: isMvpMode,
    children: [{
      path: 'dashboard',
      component: () => import('@/views/dashboard/index'),
      name: 'Dashboard',
      meta: { title: '系统首页', icon: 'dashboard', affix: true }
    }]
  },
  {
    path: '/mvp',
    component: Layout,
    redirect: '/mvp/workbench',
    children: [{
      path: 'workbench',
      component: mvpWorkbenchPage,
      name: 'MvpWorkbench',
      meta: { title: '业务办理', icon: 'form', noCache: true }
    }]
  },
  ...(isMvpMode ? [] : erpRoutes),
  {
    path: '/profile',
    component: Layout,
    redirect: '/profile/index',
    hidden: true,
    children: [{ path: 'index', component: () => import('@/views/profile/index'), name: 'Profile', meta: { title: '个人中心', noCache: true }}]
  }
]

export const asyncRoutes = [
  ...(isMvpMode ? erpRoutes : []),
  { path: '*', redirect: '/404', hidden: true }
]

const createRouter = () => new Router({
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher
}

export default router
