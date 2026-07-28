import request from '@/utils/request'

export function getRoomModuleData(resource, params) {
  return request({
    url: `/vue-element-admin/erp/room/modules/${resource}`,
    method: 'get',
    params
  })
}

export function saveRoomModuleRecord(resource, data) {
  return request({
    url: `/vue-element-admin/erp/room/modules/${resource}/save`,
    method: 'post',
    data
  })
}

export function performRoomModuleAction(resource, action, data) {
  return request({
    url: `/vue-element-admin/erp/room/modules/${resource}/action`,
    method: 'post',
    data: { action, ...data }
  })
}

