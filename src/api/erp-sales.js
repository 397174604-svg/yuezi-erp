import request from '@/utils/request'

export function getSalesModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/sales/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveSalesModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/sales/modules/${resource}/save`,
    method: 'post',
    data
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
