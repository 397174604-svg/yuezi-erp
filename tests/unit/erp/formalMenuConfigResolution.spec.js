jest.mock('@/api/erp-basic', () => ({ getBasicModuleData: jest.fn() }))
jest.mock('@/api/erp-assets', () => ({ getAssetList: jest.fn() }))
jest.mock('@/api/erp-nursing', () => ({ getNursingModuleData: jest.fn(), performNursingModuleAction: jest.fn(), saveNursingModuleRecord: jest.fn() }))
jest.mock('@/api/erp-diet', () => ({ getDietModuleData: jest.fn(), getDietRoomOptions: jest.fn(), getDietStoreReferenceOptions: jest.fn(), performDietModuleAction: jest.fn(), saveDietModuleRecord: jest.fn() }))
jest.mock('@/api/erp-inventory', () => ({ getInventoryModuleData: jest.fn(), getInventoryStoreReferenceOptions: jest.fn(), performInventoryModuleAction: jest.fn(), saveInventoryModuleRecord: jest.fn() }))
jest.mock('@/api/erp-baby', () => ({ getBabyModuleData: jest.fn(), performBabyModuleAction: jest.fn(), saveBabyModuleRecord: jest.fn() }))
jest.mock('@/api/erp-report', () => ({ getReportModuleData: jest.fn() }))
jest.mock('vuex', () => ({ mapGetters: jest.fn(() => ({})) }))

import { erpMenuGroups } from '@/config/erp-menu'
import { getNursingPageConfig, nursingPageConfigs } from '@/config/nursing-pages'
import { getDietPageConfig, dietPageConfigs } from '@/config/diet-pages'
import { getInventoryPageConfig, inventoryPageConfigs } from '@/config/inventory-pages'
import { getBabyPageConfig } from '@/config/baby-pages'
import { getReportPageConfig } from '@/config/report-pages'
import { getApprovalPageConfig } from '@/config/approval-pages'
import PeopleWorkbench from '@/views/erp/people-workbench/index.vue'
import MemberWorkbench from '@/views/erp/member-workbench/index.vue'
import StoreWorkbench from '@/views/erp/store-workbench/index.vue'
import NursingWorkbench from '@/views/erp/nursing-workbench/index.vue'
import DietWorkbench from '@/views/erp/diet-workbench/index.vue'
import InventoryWorkbench from '@/views/erp/inventory-workbench/index.vue'
import BabyWorkbench from '@/views/erp/baby-workbench/index.vue'
import ReportWorkbench from '@/views/erp/report-workbench/index.vue'

const definitionFor = (component, title) => component.computed.definition.call({ pageTitle: title })

describe('formal ERP menu titles resolve to their own page configurations', () => {
  test('all legacy nursing menu titles resolve without falling back to nursing center', () => {
    const group = erpMenuGroups.find(item => item.key === 'nursing')
    group.items.forEach(title => {
      expect(nursingPageConfigs[title]).toBeDefined()
      expect(getNursingPageConfig(title)).toBe(nursingPageConfigs[title])
    })
  })

  test('formal nursing features use distinct capability keys', () => {
    const expectations = {
      '护理中心（巡房与记录）': 'nursing-center',
      '护理评估': 'health-assessments',
      '护理看板': 'nursing-dashboard',
      '入住交接': 'check-in-handover',
      '记录可见范围开关': 'record-visibility-scope',
      '漏记提醒与推送': 'missed-record-reminders',
      '交接班管理': 'shift-handover',
      '感染管理': 'infection-management',
      '护理任务工单': 'nursing-task-orders'
    }
    Object.entries(expectations).forEach(([title, key]) => {
      expect(getNursingPageConfig(title).key).toBe(key)
    })
    expect(new Set(Object.values(expectations)).size).toBe(Object.keys(expectations).length)
  })

  test('all legacy diet menu titles resolve directly', () => {
    const group = erpMenuGroups.find(item => item.key === 'diet')
    group.items.forEach(title => {
      expect(dietPageConfigs[title]).toBeDefined()
      expect(getDietPageConfig(title)).toBe(dietPageConfigs[title])
    })
    expect(getDietPageConfig('膳食统计').key).not.toBe(getDietPageConfig('订餐配送').key)
    expect(getDietPageConfig('订餐配送').key).not.toBe(getDietPageConfig('月子餐库').key)
  })

  test('all legacy warehouse menu titles keep their menu-to-config identity', () => {
    const group = erpMenuGroups.find(item => item.key === 'warehouse')
    group.items.forEach(title => {
      expect(inventoryPageConfigs[title]).toBeDefined()
      expect(getInventoryPageConfig(title)).toBe(inventoryPageConfigs[title])
    })
    expect(getInventoryPageConfig('采购计划').key).not.toBe(getInventoryPageConfig('采购订单').key)
    expect(getInventoryPageConfig('采购订单').key).not.toBe(getInventoryPageConfig('跨店调拨').key)
  })

  test('formal warehouse and baby titles survive route parenthesis cleanup', () => {
    expect(getInventoryPageConfig('批次保质期').key).toBe('batch-expiry')
    expect(getBabyPageConfig('宝宝日志补全').key).toBe('baby-log-completion')
    expect(getBabyPageConfig('新生儿护理记录').key).toBe('newborn-care-records')
    expect(getBabyPageConfig('体温监测与异常预警').key).toBe('baby-temperature')
  })

  test('report and approval formal titles do not use their default page', () => {
    expect(getReportPageConfig('数据报表').presentation).toBe('report-builder')
    expect(getReportPageConfig('经营月报').presentation).toBe('monthly-operation')
    expect(getReportPageConfig('数据报表').key).not.toBe('unverified-report-page')
    expect(getApprovalPageConfig('审批中台').featureId).toBe('F010')
    expect(getApprovalPageConfig('审批流引擎').featureId).toBe('F108')
    expect(getApprovalPageConfig('审批流引擎（行政+业务多分类）').featureId).toBe('F108')
  })

  test('people formal titles retain their own feature ids', () => {
    const expectations = {
      '护理二次销售业绩': 'F025',
      '品项与提成': 'F047',
      '提成方案（阶梯系数）': 'F048',
      '项目耗材BOM（成本联动）': 'F049',
      '目标管理': 'F051',
      '员工与组织': 'F052',
      '角色权限': 'F053',
      '品控检查（评分表）': 'F054',
      '品控看板（部门均分+积分榜）': 'F055',
      '员工业绩看板（个人/团队/门店）': 'F096',
      '员工提成/绩效计算': 'F126'
    }
    Object.entries(expectations).forEach(([title, featureId]) => {
      expect(definitionFor(PeopleWorkbench, title).featureId).toBe(featureId)
    })
  })

  test('member and store formal titles retain their own feature ids', () => {
    const memberExpectations = {
      '会员来源分析': 'F006',
      '充值与优惠券': 'F008',
      '积分体系（规则+兑换互通）': 'F040',
      '资产账单（储值卡+次卡余额）': 'F059',
      '次卡价值分析': 'F060',
      '会员等级体系（等级/权益/升降级）': 'F087',
      '会员标签与智能分群': 'F088'
    }
    Object.entries(memberExpectations).forEach(([title, featureId]) => {
      expect(definitionFor(MemberWorkbench, title).featureId).toBe(featureId)
    })
    expect(definitionFor(StoreWorkbench, '门店与渠道').featureId).toBe('F058')
    expect(definitionFor(StoreWorkbench, '连锁多门店管理').featureId).toBe('F093')
  })

  test('route meta titles initialize each reused workbench with the matching config', () => {
    const nursingContext = { $route: { meta: { configTitle: '护理评估' } } }
    const nursingTitle = NursingWorkbench.computed.title.call(nursingContext)
    expect(NursingWorkbench.computed.pageConfig.call({ title: nursingTitle }).key).toBe('health-assessments')

    const dietContext = { $route: { meta: { configTitle: '月子餐库' } } }
    const dietTitle = DietWorkbench.computed.title.call(dietContext)
    expect(DietWorkbench.computed.pageConfig.call({ title: dietTitle }).key).toBe('dishes')

    const inventoryContext = { $route: { meta: { configTitle: '批次保质期' } } }
    const inventoryTitle = InventoryWorkbench.computed.title.call(inventoryContext)
    expect(InventoryWorkbench.computed.pageConfig.call({ title: inventoryTitle }).key).toBe('batch-expiry')

    expect(BabyWorkbench.computed.config.call({ $route: { meta: { configTitle: '宝宝日志补全' } }, title: '宝宝照护' }).key).toBe('baby-log-completion')

    const reportContext = { $route: { meta: { configTitle: '经营月报' } } }
    const reportTitle = ReportWorkbench.computed.pageTitle.call(reportContext)
    expect(ReportWorkbench.computed.config.call({ pageTitle: reportTitle }).presentation).toBe('monthly-operation')
  })
})
