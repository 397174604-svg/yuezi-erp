import request from '@/utils/request'

export function getRehabOptions(requestOptions = {}) {
  return request({
    url: '/vue-element-admin/erp/rehab/options',
    method: 'get',
    ...requestOptions
  })
}

export function getRehabModuleData(resource, params, requestOptions = {}) {
  return request({
    url: `/vue-element-admin/erp/rehab/modules/${resource}`,
    method: 'get',
    params,
    ...requestOptions
  })
}

export function saveRehabModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/rehab/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performRehabModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/rehab/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}
