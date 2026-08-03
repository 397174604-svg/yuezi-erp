import request from '@/utils/request'

export function getCountCardOptions(params) {
  return request({ url: '/vue-element-admin/erp/assets/cards/options', method: 'get', params })
}

export function getCountCards(params) {
  return request({ url: '/vue-element-admin/erp/assets/cards', method: 'get', params })
}

export function createCountCard(data) {
  return request({ url: '/vue-element-admin/erp/assets/cards', method: 'post', data })
}

export function performCountCardAction(id, action, data = {}) {
  return request({
    url: `/vue-element-admin/erp/assets/cards/${id}/${action}`,
    method: 'post',
    data
  })
}

export function getContractArchives(params) {
  return request({ url: '/vue-element-admin/erp/contract-archives', method: 'get', params })
}

export function archiveContract(id, data) {
  return request({
    url: `/vue-element-admin/erp/contract-archives/${id}/archive`,
    method: 'post',
    data
  })
}

export function revokeContractArchive(id, data) {
  return request({
    url: `/vue-element-admin/erp/contract-archives/${id}/revoke`,
    method: 'post',
    data
  })
}
