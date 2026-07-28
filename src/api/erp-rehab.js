import request from '@/utils/request'

export function getRehabOptions() {
  return request({
    url: '/vue-element-admin/erp/rehab/options',
    method: 'get'
  })
}

export function getRehabModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/rehab/modules/${resource}`,
    method: 'get',
    params
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
