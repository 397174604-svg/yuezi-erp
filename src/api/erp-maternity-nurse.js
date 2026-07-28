import request from '@/utils/request'

export function getMaternityNurseModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/maternity-nurse/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveMaternityNurseModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/maternity-nurse/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performMaternityNurseModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/maternity-nurse/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}

