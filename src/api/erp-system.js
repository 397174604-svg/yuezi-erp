import request from '@/utils/request'

export function getSystemModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/system/modules/${resource}`,
    method: 'get',
    params
  })
}

export function previewSystemModuleDraft(resource, data) {
  return request({
    url: `/vue-element-admin/erp/system/modules/${resource}/preview`,
    method: 'post',
    data
  })
}
