import request from '@/utils/request'

export function getFoundationOverview() {
  return request({
    url: '/vue-element-admin/erp/foundation/overview',
    method: 'get'
  })
}

export function saveFoundationRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/foundation/${resource}/save`,
    method: 'post',
    data
  })
}

