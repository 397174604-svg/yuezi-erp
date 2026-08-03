import request from '@/utils/request'

export function getAssetOptions(params) {
  return request({
    url: '/vue-element-admin/erp/assets/options',
    method: 'get',
    params
  })
}

export function getAssetOverview(params) {
  return request({
    url: '/vue-element-admin/erp/assets/overview',
    method: 'get',
    params
  })
}

export function getAssetList(resource, params) {
  return request({
    url: `/vue-element-admin/erp/assets/${resource}`,
    method: 'get',
    params
  })
}

export function createAssetRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/assets/${resource}`,
    method: 'post',
    data
  })
}

export function createAssetCard(data) {
  return createAssetRecord('cards', data)
}

export function performAssetAction(resource, id, action, data = {}) {
  return request({
    url: `/vue-element-admin/erp/assets/${resource}/${id}/${action}`,
    method: 'post',
    data
  })
}
