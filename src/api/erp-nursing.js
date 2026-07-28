import request from '@/utils/request'

export function getNursingModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/nursing/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveNursingModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/nursing/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performNursingModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/nursing/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}

