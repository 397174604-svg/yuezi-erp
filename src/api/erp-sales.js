import request from '@/utils/request'

export function getSalesModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/sales/modules/${resource}`,
    method: 'get',
    params
  }).then(response => {
    if (resource !== 'packages' || !response.data || !Array.isArray(response.data.list)) return response
    response.data.list = response.data.list.map(row => ({
      ...row,
      basePackageName: row.basePackageName || row.packageName,
      packageDisplayName: row.packageDisplayName || row.basePackageName || row.packageName,
      packageDays: row.packageDays || row.validDays,
      originalPrice: row.originalPrice === undefined ? row.packageAmount : row.originalPrice,
      activityPrice: row.activityPrice === undefined ? row.packageAmount : row.activityPrice,
      dealPrice: row.dealPrice === undefined ? row.packageAmount : row.dealPrice
    }))
    return response
  })
}

export function saveSalesModuleRecord(resource, data) {
  const payload = resource === 'packages'
    ? {
      ...data,
      packageName: data.packageName || data.basePackageName,
      packageAmount: data.packageAmount || data.dealPrice || data.activityPrice || data.originalPrice,
      validDays: data.validDays || data.packageDays,
      referencePrice: data.referencePrice || data.originalPrice
    }
    : data
  return request({
    url: `/vue-element-admin/erp/sales/modules/${resource}/save`,
    method: 'post',
    data: payload
  })
}

export function performSalesModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/sales/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}

export function auditSalesModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/sales/modules/${resource}/audit`,
    method: 'post',
    data
  })
}
