import request from '@/utils/request'

export function getPackageCatalog(params) {
  return request({
    url: '/vue-element-admin/erp/catalog/packages',
    method: 'get',
    params
  })
}

export function getPackageVersion(packageVersionId) {
  return request({
    url: `/vue-element-admin/erp/catalog/packages/${packageVersionId}`,
    method: 'get'
  })
}

export function savePackageVersion(data) {
  return request({
    url: '/vue-element-admin/erp/catalog/packages/save',
    method: 'post',
    data
  })
}

export function publishPackageVersion(packageVersionId) {
  return request({
    url: `/vue-element-admin/erp/catalog/packages/${packageVersionId}/publish`,
    method: 'post'
  })
}

export function deactivatePackageVersion(packageVersionId) {
  return request({
    url: `/vue-element-admin/erp/catalog/packages/${packageVersionId}/deactivate`,
    method: 'post'
  })
}

export function getServiceProjects(params) {
  return request({
    url: '/vue-element-admin/erp/catalog/service-projects',
    method: 'get',
    params
  })
}

export function saveServiceProject(data) {
  return request({
    url: '/vue-element-admin/erp/catalog/service-projects/save',
    method: 'post',
    data
  })
}
