import request from '@/utils/request'

export function getMvpOptions() {
  return request({
    url: '/vue-element-admin/erp/mvp/options',
    method: 'get'
  })
}

export function getMvpOverview() {
  return request({
    url: '/vue-element-admin/erp/mvp/overview',
    method: 'get'
  })
}

export function getMvpList(resource) {
  return request({
    url: `/vue-element-admin/erp/mvp/${resource}`,
    method: 'get'
  })
}

export function createMvpRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/mvp/${resource}`,
    method: 'post',
    data
  })
}

export function performMvpAction(resource, id, action) {
  return request({
    url: `/vue-element-admin/erp/mvp/${resource}/${id}/${action}`,
    method: 'post'
  })
}
