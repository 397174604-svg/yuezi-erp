import request from '@/utils/request'

export function getRiskModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/risk/modules/${resource}`,
    method: 'get',
    params
  })
}
