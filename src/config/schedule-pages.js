const schedulePageConfigs = {
  '预约与排班': {
    featureId: 'F017',
    title: '预约与排班',
    description: '按门店管理服务预约与人员档期；预约和排班使用同一产康业务接口，不进入客房房态页面。',
    defaultTab: 'appointments',
    mode: 'operations',
    primaryAction: '新建预约',
    filterFields: ['storeId', 'date'],
    statusColumns: ['serviceStatus', 'shiftStatus']
  },
  '在线预约看板（技师/时段/多渠道）': {
    featureId: 'F086',
    title: '在线预约看板（技师/时段/多渠道）',
    description: '按门店、技师和日期查看预约资源占用；不复用客房房态页面。',
    defaultTab: 'appointments',
    mode: 'online-board',
    primaryAction: '刷新看板',
    filterFields: ['storeId', 'date', 'technician', 'channel'],
    statusColumns: ['channel', 'appointmentPeriod', 'serviceStatus']
  }
}

const fallbackConfig = schedulePageConfigs['预约与排班']
const schedulePageAliases = {
  在线预约看板: '在线预约看板（技师/时段/多渠道）'
}

export function getSchedulePageConfig(title) {
  return schedulePageConfigs[schedulePageAliases[title] || title] || fallbackConfig
}
