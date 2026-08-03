import request from '@/utils/request'

export function getMvpOptions(requestOptions = {}) {
  return request({
    url: '/vue-element-admin/erp/mvp/options',
    method: 'get',
    ...requestOptions
  })
}

export function getMvpOverview(requestOptions = {}) {
  return request({
    url: '/vue-element-admin/erp/mvp/overview',
    method: 'get',
    ...requestOptions
  })
}

export function getMvpList(resource, requestOptions = {}) {
  return request({
    url: `/vue-element-admin/erp/mvp/${resource}`,
    method: 'get',
    ...requestOptions
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
