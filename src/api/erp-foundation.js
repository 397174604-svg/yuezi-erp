import request from '@/utils/request'

export function getFoundationOverview(params) {
  return request({
    url: '/vue-element-admin/erp/foundation/overview',
    method: 'get',
    params
  })
}

export function saveFoundationRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/foundation/${resource}/save`,
    method: 'post',
    data
  })
}

export function saveRolePermissions(roleId, data) {
  return request({
    url: `/vue-element-admin/erp/foundation/roles/${roleId}/permissions`,
    method: 'post',
    data
  })
}

