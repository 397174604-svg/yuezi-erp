jest.mock('@/layout', () => ({ name: 'LayoutStub', render: () => null }))

import { constantRoutes, asyncRoutes } from '@/router'
import { erpFeatureRegistry } from '@/config/erp-feature-registry'
import { getRehabPageConfig } from '@/config/rehab-pages'
import { getRecoveryFeaturePageConfig } from '@/config/recovery-feature-pages'

function joinPath(parent, child) {
  if (!child) return parent || '/'
  if (child.startsWith('/')) return child
  return `${String(parent || '').replace(/\/$/, '')}/${child}`.replace(/\/+/g, '/')
}

function flatten(routes, parent = '') {
  return routes.flatMap(route => {
    const path = joinPath(parent, route.path)
    return [{ route, path }, ...flatten(route.children || [], path)]
  })
}

const featureIds = value => String(value || '').split(',').map(item => item.trim()).filter(Boolean)

describe('ERP 104 canonical route integrity', () => {
  const allRoutes = flatten([...constantRoutes, ...asyncRoutes])
  const canonicalRoutes = allRoutes.filter(({ path }) => !path.startsWith('/p0-operations/'))
  const featureRoutes = canonicalRoutes.filter(({ route }) => route.meta && route.meta.featureId)

  test('registry contains exactly 104 unique feature IDs', () => {
    expect(erpFeatureRegistry).toHaveLength(104)
    expect(new Set(erpFeatureRegistry.map(feature => feature.id)).size).toBe(104)
  })

  test('canonical routes account for every registry feature exactly once', () => {
    const assignments = featureRoutes.flatMap(({ route, path }) =>
      featureIds(route.meta.featureId).map(id => ({ id, path }))
    )
    const registryIds = new Set(erpFeatureRegistry.map(feature => feature.id))
    const counts = assignments.filter(item => registryIds.has(item.id)).reduce((result, item) => {
      result[item.id] = [...(result[item.id] || []), item.path]
      return result
    }, {})
    const missing = [...registryIds].filter(id => !counts[id])
    const duplicated = Object.entries(counts).filter(([, paths]) => paths.length !== 1)

    expect({ missing, duplicated }).toEqual({ missing: [], duplicated: [] })
  })

  test('formal feature routes have unique paths and route-specific config titles', () => {
    const formal = featureRoutes.filter(({ path }) => path !== '/dashboard')
    const paths = formal.map(item => item.path)
    expect(new Set(paths).size).toBe(paths.length)
    formal.forEach(({ route, path }) => {
      if (!route.meta.configTitle) throw new Error(`${path} has no configTitle`)
      if (!route.meta.pageType) throw new Error(`${path} has no pageType`)
      if (!route.component) throw new Error(`${path} has no component`)
    })
  })

  test.todo('customer formal features do not collapse to one API resource')

  test('recovery formal features use their own load resource', () => {
    const titles = [
      '产康项目管理', '产康预约与排班', '产后评估记录', '产康服务记录与效果跟踪',
      '产康门店经营看板', '产康二次销售与升单', '产康耗材与设备管理', '产康师绩效与排班'
    ]
    titles.forEach(title => expect(getRecoveryFeaturePageConfig(title)).toBeTruthy())
    const loadKeys = titles.map(title => getRehabPageConfig(title).key)
    expect(new Set(loadKeys).size).toBe(titles.length)
  })
})
