import request from '@/utils/request'

export function getReportModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/report/modules/${resource}`,
    method: 'get',
    params
  })
}

