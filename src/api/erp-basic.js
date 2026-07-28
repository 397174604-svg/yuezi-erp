import request from '@/utils/request'

export function getBasicModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/basic/modules/${resource}`,
    method: 'get',
    params
  })
}

export function previewBasicModuleDraft(resource, data) {
  return request({
    url: `/vue-element-admin/erp/basic/modules/${resource}/preview`,
    method: 'post',
    data
  })
}
