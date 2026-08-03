import request from '@/utils/request'

export function getBabyModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/baby/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveBabyModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/baby/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performBabyModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/baby/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}
