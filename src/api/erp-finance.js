import request from '@/utils/request'

export function getFinanceOptions() {
  return request({
    url: '/vue-element-admin/erp/finance/options',
    method: 'get'
  })
}

export function getFinanceModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/finance/modules/${resource}`,
    method: 'get',
    params
  })
}

export function getFinancePickerData(pickerType) {
  return request({
    url: `/vue-element-admin/erp/finance/pickers/${pickerType}`,
    method: 'get'
  })
}

export function saveFinanceModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/finance/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performFinanceModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/finance/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}
