import request from '@/utils/request'

export function getResearchModuleData(params) {
  return request({
    url: '/vue-element-admin/erp/research/modules/beauty-cases',
    method: 'get',
    params
  })
}

export function saveResearchCase(data) {
  return request({
    url: '/vue-element-admin/erp/research/modules/beauty-cases/save',
    method: 'post',
    data
  })
}

export function performResearchAction(action, data) {
  return request({
    url: '/vue-element-admin/erp/research/modules/beauty-cases/action',
    method: 'post',
    data: { action, ...data }
  })
}
