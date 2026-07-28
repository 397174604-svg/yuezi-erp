import request from '@/utils/request'

export function getInventoryModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/inventory/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveInventoryModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/inventory/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performInventoryModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/inventory/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}

