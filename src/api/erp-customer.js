import request from '@/utils/request'

export function getCustomerEntryOptions() {
  return request({
    url: '/vue-element-admin/erp/customer/entry-options',
    method: 'get'
  })
}

export function checkCustomerDuplicate(data) {
  return request({
    url: '/vue-element-admin/erp/customer/duplicate-check',
    method: 'post',
    data
  })
}

export function saveCustomerDraft(data) {
  return request({
    url: '/vue-element-admin/erp/customer/draft',
    method: 'post',
    data
  })
}

export function createCustomer(data) {
  return request({
    url: '/vue-element-admin/erp/customer',
    method: 'post',
    data
  })
}

export function getCustomerModuleData(resource, params, requestOptions = {}) {
  return request({
    url: `/vue-element-admin/erp/customer/modules/${resource}`,
    method: 'get',
    params,
    ...requestOptions
  })
}

export function saveCustomerModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/customer/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performCustomerModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/customer/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}

export function savePointSettings(data) {
  return request({
    url: '/vue-element-admin/erp/customer/point-settings',
    method: 'post',
    data
  })
}
