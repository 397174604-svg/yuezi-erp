import request from '@/utils/request'

export function getDietModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/diet/modules/${resource}`,
    method: 'get',
    params
  })
}

export function getDietRoomOptions(params) {
  return request({
    url: '/vue-element-admin/erp/diet/modules/room-options',
    method: 'get',
    params
  })
}

export function getDietStoreReferenceOptions(params) {
  return request({
    url: '/vue-element-admin/erp/diet/modules/reference-options',
    method: 'get',
    params
  })
}

export function saveDietModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/diet/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performDietModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/diet/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}
