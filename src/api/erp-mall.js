import request from '@/utils/request'

export function getMallModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/mall/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveMallModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/mall/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performMallModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/mall/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}
