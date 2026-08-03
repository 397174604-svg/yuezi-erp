import Vue from 'vue'
import Router from 'vue-router'
import Layout from '@/layout'
import { getPageType } from '@/config/erp-menu'
import { erpFeatureRegistry } from '@/config/erp-feature-registry'
import { originalPageUrls } from '@/config/original-page-evidence'
import { p0OperationsFeatures, p1OperationsFeatures } from '@/config/p0-operations-features'

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
const babyWorkbenchPage = () => import('@/views/erp/baby-workbench/index')
const rehabWorkbenchPage = () => import('@/views/erp/rehab-workbench/index')
const researchWorkbenchPage = () => import('@/views/erp/research-workbench/index')
const dietWorkbenchPage = () => import('@/views/erp/diet-workbench/index')
const inventoryWorkbenchPage = () => import('@/views/erp/inventory-workbench/index')
const mallWorkbenchPage = () => import('@/views/erp/mall-workbench/index')
const riskWorkbenchPage = () => import('@/views/erp/risk-workbench/RiskServiceMatrix')
const reportWorkbenchPage = () => import('@/views/erp/report-workbench/index')
const basicWorkbenchPage = () => import('@/views/erp/basic-workbench/index')
const systemWorkbenchPage = () => import('@/views/erp/system-workbench/index')
const maternityNurseWorkbenchPage = () => import('@/views/erp/maternity-nurse-workbench/index')
const mvpWorkbenchPage = () => import('@/views/erp/mvp-workbench/index')
const assetWorkbenchPage = () => import('@/views/erp/asset-workbench/index')
const memberWorkbenchPage = () => import('@/views/erp/member-workbench/index')
const storeWorkbenchPage = () => import('@/views/erp/store-workbench/index')
const peopleWorkbenchPage = () => import('@/views/erp/people-workbench/index')
const approvalWorkbenchPage = () => import('@/views/erp/approval-workbench/index')
const scheduleWorkbenchPage = () => import('@/views/erp/schedule-workbench/index')
const marketingWorkbenchPage = () => import('@/views/erp/marketing-workbench/index')
const satisfactionFollowUpPage = () => import('@/views/erp/customer-service/satisfaction')
const aiKnowledgeBasePage = () => import('@/views/erp/customer-service/knowledge')
const messageNotificationPage = () => import('@/views/erp/customer-service/notification')
const smartCustomerSupportPage = () => import('@/views/erp/customer-service/smart-support')
const p0OperationsStatusPage = () => import('@/views/erp/p0-operations-status/index')
const developmentPlaceholderPage = () => import('@/views/erp/development-placeholder/index')
const foundationPageTypes = ['organization', 'role-permission', 'user-account', 'data-dictionary', 'operation-permission']
const businessGroupPageTypes = {
  approval: 'approval-workbench',
  schedule: 'schedule-workbench',
  baby: 'baby-workbench',
  research: 'research-workbench',
  people: 'people-workbench',
  store: 'store-workbench',
  member: 'member-workbench',
  marketing: 'marketing-workbench'
}
const serviceFeaturePageTypes = {
  满意度回访: 'service-satisfaction',
  AI客服知识库: 'service-knowledge',
  消息通知中心: 'service-notification',
  智能客服: 'service-smart-support'
}
const memberFeaturePageTypes = {
  资产账单: 'asset-workbench'
}
const customerFeaturePageTypes = {
  客户中台: 'customer-center'
}
const integrationFeaturePageTypes = {
  '套餐卡/次卡管理': 'development-placeholder',
  在线支付: 'development-placeholder',
  电子合同: 'development-placeholder',
  '储值卡/折扣卡/微信卡包': 'development-placeholder'
}
// These P0 entries are actual administrative work, rather than generic
// workbench aliases.  Dedicated surfaces keep account, role and store setup
// separate from the operational modules.
const operationalSettingsPageTypes = {
  '员工与组织': 'organization',
  '角色权限': 'role-permission',
  '门店与渠道': 'store-management'
}
const RouterView = { name: 'ErpRouterView', render: h => h('router-view') }
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
const fallbackGroupPermissions = {
  nursing: ['NURSING.VIEW'],
  diet: ['DIET.VIEW', 'DIET.QUERY'],
  warehouse: ['INVENTORY.VIEW', 'LEGACY.WEB.N358.B18']
}

const cleanMenuTitle = title => String(title).replace(/\s*[（(][^）)]*[）)]/g, '').trim()
const p0FeatureTitles = new Set(erpFeatureRegistry.filter(feature => feature.priority === 'P0').map(feature => cleanMenuTitle(feature.title)))
// Existing operational pages use older, shorter names.  Keep their routes and
// add the same test marker so the sidebar still makes the P0 scope obvious.
const p0LegacyAliases = new Set([
  '客户中心', '线索管理', '跟进记录', '预约参观', '满意度调查表', '合同管理', '套餐管理',
  '新增收款', '收款管理', '退款申请', '退款审核', '费用审核', '付款管理', '房态图', '智能排房',
  '订房管理', '入住管理', '护理中心', '护理计划', '宝宝档案', '客户餐单', '菜品管理',
  '采购订单', '采购入库', '调拨管理', '盘点管理(NEW)', '物料库存预警', '库存明细统计',
  '月嫂档案', '月嫂档期', '月嫂结算列表', '员工档案', '部门管理', '角色管理', '数据字典'
])
const markedP0Title = title => {
  const cleanTitle = cleanMenuTitle(title)
  return (p0FeatureTitles.has(cleanTitle) || p0LegacyAliases.has(cleanTitle)) ? `${cleanTitle} ★` : cleanTitle
}
const unmarkedTitle = title => cleanMenuTitle(String(title).replace(/ ★$/, ''))

// Canonical first-release sidebar. Every Web feature from the Excel registry is
// assigned exactly once; old pages are retained as route implementations.
const productMenuDefinitions = [
  // F001（总部驾驶舱）与 F002（经营大屏）共用同一套经营看板。
  // 左侧只保留一个正式入口，避免用户看到两个名称相近的首页。
  ['customer', '客户管理', 'people', '#B8945A', ['F003', 'F004', 'F128']],
  ['service', '客服管理', 'message', '#45B8AC', ['F005', 'F043', 'F084', 'F094']],
  ['member', '会员管理', 'user', '#6F8FF7', ['F006', 'F008', 'F040', 'F059', 'F060', 'F087', 'F088']],
  ['sales', '销售管理', 'shopping', '#D17B57', ['F020', 'F050', 'F082', 'F107']],
  ['finance', '财务管理', 'money', '#C29348', ['F007', 'F009', 'F011', 'F012', 'F013', 'F014', 'F015', 'F016', 'F080', 'F083', 'F089']],
  ['approval', '审批中心', 'clipboard', '#8D7A5A', ['F010', 'F108']],
  ['schedule', '预约与排班', 'form', '#5E9DAB', ['F017', 'F086']],
  ['room', '客房管理', 'component', '#45B8AC', ['F018', 'F019']],
  ['nursing', '护理管理', 'documentation', '#8F7CF6', ['F021', 'F022', 'F024', 'F026', 'F075', 'F078', 'F118', 'F119', 'F125']],
  ['baby', '宝宝照护', 'education', '#A576C8', ['F027', 'F069', 'F111', 'F112', 'F115', 'F120', 'F121', 'F122']],
  ['diet', '膳食管理', 'list', '#58B66F', ['F023', 'F028', 'F029']],
  ['warehouse', '仓存与采购', 'table', '#5886D6', ['F030', 'F031', 'F032', 'F033', 'F034', 'F035', 'F036', 'F037']],
  ['recovery', '产康管理', 'skill', '#C875A0', ['F099', 'F100', 'F101', 'F102', 'F103', 'F104', 'F105', 'F106']],
  ['research', '科研美容', 'guide', '#C77A9A', ['F081']],
  ['matron', '月嫂管理', 'peoples', '#6F8FF7', ['F044', 'F045', 'F046']],
  ['people', '组织与绩效', 'tree', '#7B8A9A', ['F025', 'F047', 'F048', 'F049', 'F051', 'F052', 'F053', 'F054', 'F055', 'F096', 'F126']],
  ['marketing', '营销运营', 'chart', '#D16F94', ['F038', 'F039', 'F041', 'F042', 'F085', 'F090', 'F091', 'F092', 'F127']],
  ['report', '数据报表', 'excel', '#4F8CF7', ['F056', 'F057']],
  ['store', '门店管理', 'international', '#7B8A9A', ['F058', 'F093']],
  ['system', '系统设置', 'lock', '#65758B', ['F061', 'F079', 'F098']]
]

const featureById = new Map(erpFeatureRegistry.map(feature => [feature.id, feature]))
const featureByCleanTitle = new Map(erpFeatureRegistry.map(feature => [cleanMenuTitle(feature.title), feature]))
// New product groups do not all have a legacy navigation id.  They must still
// carry an explicit role boundary; otherwise Vue's historical fallback treats
// an unmapped route as public for every signed-in account.
const groupRoleMatrix = {
  customer: ['GENERAL_MANAGER', 'STORE_MANAGER', 'SALES_MANAGER', 'SALES_CONSULTANT', 'RECOVERY_THERAPIST', 'HOUSEKEEPER', 'NURSING_DIRECTOR', 'NURSE'],
  service: ['GENERAL_MANAGER', 'STORE_MANAGER', 'SALES_MANAGER', 'SALES_CONSULTANT', 'NURSING_DIRECTOR', 'NURSE'],
  member: ['GENERAL_MANAGER', 'STORE_MANAGER', 'SALES_MANAGER', 'SALES_CONSULTANT', 'FINANCE_SPECIALIST', 'MARKETING_SPECIALIST'],
  sales: ['GENERAL_MANAGER', 'STORE_MANAGER', 'SALES_MANAGER', 'SALES_CONSULTANT'],
  finance: ['GENERAL_MANAGER', 'STORE_MANAGER', 'FINANCE_SPECIALIST'],
  approval: ['GENERAL_MANAGER', 'STORE_MANAGER', 'FINANCE_SPECIALIST', 'SALES_MANAGER'],
  schedule: ['GENERAL_MANAGER', 'STORE_MANAGER', 'SALES_MANAGER', 'SALES_CONSULTANT', 'RECOVERY_MANAGER', 'RECOVERY_THERAPIST'],
  room: ['GENERAL_MANAGER', 'STORE_MANAGER', 'ROOM_MANAGER', 'HOUSEKEEPER', 'SALES_MANAGER', 'SALES_CONSULTANT'],
  nursing: ['GENERAL_MANAGER', 'STORE_MANAGER', 'NURSING_DIRECTOR', 'NURSE'],
  baby: ['GENERAL_MANAGER', 'STORE_MANAGER', 'NURSING_DIRECTOR', 'NURSE'],
  diet: ['GENERAL_MANAGER', 'STORE_MANAGER', 'DIET_MANAGER', 'KITCHEN_STAFF', 'NURSING_DIRECTOR', 'NURSE'],
  warehouse: ['GENERAL_MANAGER', 'STORE_MANAGER', 'WAREHOUSE_KEEPER'],
  recovery: ['GENERAL_MANAGER', 'STORE_MANAGER', 'RECOVERY_MANAGER', 'RECOVERY_THERAPIST'],
  research: ['GENERAL_MANAGER', 'STORE_MANAGER', 'RECOVERY_MANAGER', 'BEAUTY_TECHNICIAN'],
  matron: ['GENERAL_MANAGER', 'STORE_MANAGER', 'MATRON_MANAGER', 'MATRON', 'HR_MANAGER'],
  people: ['GENERAL_MANAGER', 'STORE_MANAGER', 'HR_MANAGER', 'NURSING_DIRECTOR'],
  marketing: ['GENERAL_MANAGER', 'STORE_MANAGER', 'MARKETING_SPECIALIST', 'SALES_MANAGER'],
  report: ['GENERAL_MANAGER', 'STORE_MANAGER', 'FINANCE_SPECIALIST'],
  store: ['GENERAL_MANAGER', 'STORE_MANAGER'],
  system: []
}
const groupRoles = key => groupRoleMatrix[key] || []
const navigableErpMenuGroups = productMenuDefinitions.map(([key, title, icon, color, ids]) => ({
  key,
  title,
  icon,
  color,
  items: ids.map(id => markedP0Title(featureById.get(id).title))
}))

// The legacy ERP exposed more than 200 page entries. The current Web delivery
// keeps only the entries that map to the Excel feature list or to an essential
// operating flow. Source components stay in the repository for later migration.
const legacyExcelMenuTitles = {
  customer: ['客户中心', '客户录入', '线索管理', '跟进记录', '预约参观', '满意度调查表', '客户回访记录', '客户投诉建议', '积分设置', '积分记录', '发布活动'],
  sales: ['合同管理', '商品销售', '销售明细', '套餐管理', '卡类套餐', '优惠管理', '优惠券管理', 'F107 电子合同（开发中）'],
  finance: ['新增收款', '收款管理', '退款申请', '退款审核', '欠款审核', '发票管理', '交易对账', '我的费用', '费用审核', '付款管理', 'F080 厂商并行期对账帮手（开发中）', 'F082 套餐卡/次卡管理（开发中）', 'F083 在线支付（开发中）', 'F089 储值卡/折扣卡/微信卡包（开发中）'],
  room: ['房态图', '智能排房', '房型列表', '订房管理', '入住管理', '续住信息', '换房申请', '客房服务'],
  nursing: ['护理中心', '护理计划', '护理部排班第二版', '宝宝档案', '健康评估', '自定义查房', '宝宝护理记录', '入住物品交接'],
  recovery: ['服务预约列表', '服务综合查询', '人员排班设置', '产康服务记录表', '产康健康评估'],
  matron: ['月嫂档案', '月嫂档期', '月嫂派工审核', '月嫂结算列表'],
  diet: ['客户餐单', '菜品管理', '膳食套餐', '膳食统计', '订餐列表'],
  warehouse: ['采购订单', '采购入库', '领料申请', '调拨管理', '盘点管理(NEW)', '物料库存预警', '库存明细统计', '仓库库存查询'],
  mall: ['商品管理', '商品订单', '项目管理', '商品类别设置', '妈妈课堂'],
  risk: ['悦禧风控'],
  report: ['S1 销售排行榜报表', 'S2客户简报', 'S6销售统计报表', 'S13销售业绩报表', 'F1 月度入住率报表', 'F2 房态统计总体分析', 'C0经营日报表', 'C1 会员充值汇总明细表', 'C3 付款汇总分析表', 'C4 资金收支余额表', 'C4 资金收支出余额表', 'C7 门店收入与成本统计表', 'C8 商品毛利分析表', 'C13收款退款汇总表'],
  basic: ['职员档案', '基础项目', '物料档案', '客房档案', '供应商档案', '资金账户', '护理模板', '服务时间设置'],
  system: ['部门管理', '角色管理', '用户管理', '数据字典', '审批流程', '通知公告', '操作日志', '系统参数设置']
}
// Retained only as traceable evidence for the legacy-to-new menu migration.
Object.freeze(legacyExcelMenuTitles)

// The legacy title table stays as source evidence. The visible menu uses the
// canonical 104-item assignment above, preventing duplicate entries.
const excelMenuTitles = navigableErpMenuGroups.reduce((result, group) => {
  result[group.key] = group.items
  return result
}, {})

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
  if (pageType === 'baby-workbench') return babyWorkbenchPage
  if (pageType === 'rehab-workbench') return rehabWorkbenchPage
  if (pageType === 'research-workbench') return researchWorkbenchPage
  if (pageType === 'diet-workbench') return dietWorkbenchPage
  if (pageType === 'inventory-workbench') return inventoryWorkbenchPage
  if (pageType === 'mall-workbench') return mallWorkbenchPage
  if (pageType === 'risk-workbench') return riskWorkbenchPage
  if (pageType === 'report-workbench') return reportWorkbenchPage
  if (pageType === 'basic-workbench') return basicWorkbenchPage
  if (pageType === 'asset-workbench') return assetWorkbenchPage
  if (pageType === 'member-workbench') return memberWorkbenchPage
  if (pageType === 'store-workbench') return storeWorkbenchPage
  if (pageType === 'store-management') return storeWorkbenchPage
  if (pageType === 'people-workbench') return peopleWorkbenchPage
  if (pageType === 'approval-workbench') return approvalWorkbenchPage
  if (pageType === 'schedule-workbench') return scheduleWorkbenchPage
  if (pageType === 'marketing-workbench') return marketingWorkbenchPage
  if (pageType === 'system-workbench') return systemWorkbenchPage
  if (pageType === 'maternity-nurse-workbench') return maternityNurseWorkbenchPage
  if (pageType === 'service-satisfaction') return satisfactionFollowUpPage
  if (pageType === 'service-knowledge') return aiKnowledgeBasePage
  if (pageType === 'service-notification') return messageNotificationPage
  if (pageType === 'service-smart-support') return smartCustomerSupportPage
  if (pageType === 'development-placeholder') return developmentPlaceholderPage
  if (pageType.startsWith('mama-')) return mamaBoxPage
  return modulePage
}

function createPageRoute(group, title, path, name, section) {
  const sourceTitle = unmarkedTitle(title)
  const feature = featureByCleanTitle.get(sourceTitle)
  const pageType = operationalSettingsPageTypes[sourceTitle] || integrationFeaturePageTypes[sourceTitle] || serviceFeaturePageTypes[sourceTitle] || memberFeaturePageTypes[sourceTitle] || customerFeaturePageTypes[sourceTitle] || businessGroupPageTypes[group.key] || getPageType(group.key, sourceTitle)
  const legacyNavId = legacyPageNavId(group.key, sourceTitle)
  return {
    path,
    component: getPageComponent(pageType),
    name,
    meta: {
      title,
      featureId: feature ? feature.id : '',
      configTitle: sourceTitle,
      displayMode: '',
      group: group.title,
      groupKey: group.key,
      section: section || '',
      pageType,
      ...(legacyNavId > 0
        ? { legacyNavId }
        : fallbackGroupPermissions[group.key]
          ? { permissions: fallbackGroupPermissions[group.key] }
          : {}),
      color: group.color,
      roles: groupRoles(group.key),
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
        meta: legacyNavId > 0 ? { legacyNavId } : {}
      })
      return createPageRoute(group, title, childPath, `Erp${group.key}${entry.key}${childIndex + 1}`, entry.title)
    })

    children.push({
      path: entry.key,
      component: RouterView,
      redirect: 'noRedirect',
      name: `Erp${group.key}Section${index + 1}`,
      alwaysShow: true,
      meta: { title: entry.title, icon: entry.icon, color: group.color, roles: groupRoles(group.key) },
      children: sectionChildren
    })
  })

  return [...children, ...legacyRedirects]
}

function filterExcelMenuChildren(children, groupKey) {
  const allowed = new Set(excelMenuTitles[groupKey] || [])
  return children.reduce((result, route) => {
    if (route.children) {
      const sectionChildren = filterExcelMenuChildren(route.children, groupKey)
      if (sectionChildren.length) result.push({ ...route, children: sectionChildren })
      return result
    }
    if (route.meta && (allowed.has(route.meta.title) || allowed.has(unmarkedTitle(route.meta.title)))) result.push(route)
    return result
  }, [])
}

const erpRoutes = navigableErpMenuGroups.map(group => {
  const children = filterExcelMenuChildren(createGroupChildren(group), group.key)

  if (group.key === 'customer') {
    children.unshift(
      {
        path: 'signing-workbench',
        component: mvpWorkbenchPage,
        name: 'CustomerSigningWorkbench',
        meta: { title: '客户签约办理', icon: 'form', noCache: true }
      },
      {
        path: 'member-assets',
        component: assetWorkbenchPage,
        name: 'CustomerMemberAssets',
        meta: {
          title: '会员资产',
          icon: 'money',
          permissions: ['CUSTOMER.VIEW', 'FINANCE.VIEW'],
          noCache: true
        }
      }
    )
  }

  return {
    path: `/${group.key}`,
    component: Layout,
    redirect: 'noRedirect',
    name: `Erp${group.key}`,
    alwaysShow: true,
    hidden: false,
    meta: {
      title: group.title,
      icon: group.icon,
      color: group.color,
      roles: groupRoles(group.key)
    },
    children
  }
})

// Hidden compatibility routes keep the acceptance matrix addressable without
// duplicating the formal 104-item sidebar.
const p0OperationsComponentMap = {
  customer: customerWorkbenchPage,
  mall: mallWorkbenchPage,
  matron: maternityNurseWorkbenchPage,
  basic: basicWorkbenchPage,
  sales: salesWorkbenchPage,
  foundation: foundationPage,
  report: reportWorkbenchPage,
  system: systemWorkbenchPage,
  asset: assetWorkbenchPage,
  marketing: marketingWorkbenchPage,
  status: p0OperationsStatusPage
}
const p0OperationsRoute = {
  path: '/p0-operations',
  component: Layout,
  redirect: 'noRedirect',
  name: 'P0OperationsAcceptance',
  hidden: true,
  children: [...p0OperationsFeatures, ...p1OperationsFeatures].map(feature => ({
    path: feature.id.toLowerCase(),
    component: p0OperationsComponentMap[feature.component] || p0OperationsStatusPage,
    ...(feature.canonicalPath ? { redirect: feature.canonicalPath } : {}),
    name: `P0Operations${feature.id}`,
    meta: {
      title: `${feature.id} ${feature.title}`,
      featureId: feature.id,
      configTitle: feature.configTitle,
      pageType: feature.pageType,
      permissions: feature.permissions,
      deliveryState: feature.state,
      noCache: true
    }
  }))
}
const erpDeliveryRoutes = [...erpRoutes, p0OperationsRoute]
const useProtectedErpRoutes = process.env.VUE_APP_ENABLE_MOCK !== 'true'

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
    redirect: '/dashboard',
    hidden: false,
    children: [{
      path: 'dashboard',
      component: () => import('@/views/dashboard/index'),
      name: 'Dashboard',
      meta: {
        title: '总部驾驶舱 ★',
        icon: 'dashboard',
        affix: true,
        // 经营大屏是驾驶舱的数据视图，不单独生成重复导航项。
        featureId: 'F001,F002',
        priority: 'P0'
      }
    }]
  },
  {
    path: '/business',
    component: Layout,
    redirect: '/mvp/workbench',
    hidden: true,
    children: [{ path: 'index', redirect: '/mvp/workbench', hidden: true }]
  },
  {
    path: '/mvp',
    component: Layout,
    redirect: '/mvp/workbench',
    name: 'OperationsCenter',
    hidden: true,
    meta: { title: '会所运营', icon: 'dashboard' },
    children: [
      {
        path: 'workbench',
        component: mvpWorkbenchPage,
        name: 'MvpWorkbench',
        meta: { title: '客户签约', icon: 'form', noCache: true }
      },
      {
        path: 'appointments',
        component: rehabWorkbenchPage,
        name: 'MvpAppointments',
        meta: {
          title: '预约排班',
          configTitle: '服务预约列表',
          icon: 'date',
          group: '产康管理',
          groupKey: 'recovery',
          pageType: 'rehab-workbench',
          legacyNavId: 257,
          noCache: true
        }
      },
      {
        path: 'room-map',
        component: roomWorkbenchPage,
        name: 'MvpRoomMap',
        meta: {
          title: '客房房态',
          configTitle: '房态图',
          icon: 'table',
          group: '客房管理',
          groupKey: 'room',
          pageType: 'room-workbench',
          legacyNavId: 418,
          noCache: true
        }
      },
      {
        path: 'smart-rooms',
        component: roomWorkbenchPage,
        name: 'MvpSmartRooms',
        meta: {
          title: '智能排房',
          configTitle: '智能排房',
          icon: 'guide',
          group: '客房管理',
          groupKey: 'room',
          pageType: 'room-workbench',
          legacyNavId: 517,
          noCache: true
        }
      }
    ]
  },
  ...(isMvpMode ? [] : (useProtectedErpRoutes ? erpDeliveryRoutes : [])),
  {
    path: '/profile',
    component: Layout,
    redirect: '/profile/index',
    hidden: true,
    children: [{ path: 'index', component: () => import('@/views/profile/index'), name: 'Profile', meta: { title: '个人中心', noCache: true }}]
  }
]

export const asyncRoutes = [
  ...(isMvpMode ? (useProtectedErpRoutes ? erpDeliveryRoutes : []) : []),
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
