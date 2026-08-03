import request from '@/utils/request'

const featurePath = featureCode => String(featureCode || '').toLowerCase()

export function getServiceRecords(featureCode, params) {
  return request({
    url: `/vue-element-admin/erp/service/${featurePath(featureCode)}`,
    method: 'get',
    params
  })
}

export function getServiceRecord(featureCode, id) {
  return request({
    url: `/vue-element-admin/erp/service/${featurePath(featureCode)}/${id}`,
    method: 'get'
  })
}

export function saveServiceRecord(featureCode, data) {
  return request({
    url: `/vue-element-admin/erp/service/${featurePath(featureCode)}`,
    method: 'post',
    data
  })
}

export function performServiceAction(featureCode, id, action, data = {}) {
  return request({
    url: `/vue-element-admin/erp/service/${featurePath(featureCode)}/${id}/action`,
    method: 'post',
    data: { action, ...data }
  })
}
