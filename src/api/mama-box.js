import request from '@/utils/request'

export function getMamaBoxOverview() {
  return request({
    url: '/vue-element-admin/erp/mama-box/overview',
    method: 'get'
  })
}

export function saveMamaBoxRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/mama-box/${resource}/save`,
    method: 'post',
    data
  })
}

export function updateMamaBoxStatus(resource, id, action) {
  return request({
    url: `/vue-element-admin/erp/mama-box/${resource}/${id}/${action}`,
    method: 'post'
  })
}

