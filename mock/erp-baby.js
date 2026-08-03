const stores = ['中心广场旗舰店', '黄河路轻奢店']
const names = ['安安', '乐乐', '米粒', '果果', '星星', '朵朵']

const dates = offset => {
  const value = new Date()
  value.setDate(value.getDate() - offset)
  return value.toISOString().slice(0, 10)
}

const seedRows = [
  { id: 'BABY-001', babyName: '安安', room: '301', store: stores[0], logDate: dates(0), careDate: dates(0), measuredAt: `${dates(0)} 08:30`, recordDate: dates(0), handoverDate: dates(2), feeding: '母乳 6 次', sleep: '14.5 小时', diaper: '正常', temperature: '36.7℃', temperatureStatus: '正常', status: '待记录', completionStatus: '待补全', careItem: '脐部护理', nurseName: '李护士', result: '脐部干燥', growthStage: '住中观察', ageDays: 18, weight: '3.8kg', height: '52cm', milestone: '抬头 10 秒', visitNo: 'VIS-001', visitorName: '王女士', relationship: '外婆', visitDate: dates(0), disinfection: '已核验', visitStatus: '已入场', handoverNo: 'HO-001', careSummary: '护理记录齐全', medicine: '无', familySigned: '待签收', handoverStatus: '待家属签收', measurable: true },
  { id: 'BABY-002', babyName: '乐乐', room: '302', store: stores[0], logDate: dates(0), careDate: dates(0), measuredAt: `${dates(0)} 09:00`, recordDate: dates(0), handoverDate: dates(5), feeding: '配方奶 5 次', sleep: '12 小时', diaper: '偏少', temperature: '37.6℃', temperatureStatus: '待复核', status: '需关注', completionStatus: '已补全', careItem: '黄疸观察', nurseName: '周护士', result: '需下午复测', growthStage: '住中观察', ageDays: 12, weight: '3.5kg', height: '50cm', milestone: '目光追随', visitNo: 'VIS-002', visitorName: '陈先生', relationship: '父亲', visitDate: dates(1), disinfection: '已核验', visitStatus: '已离场', handoverNo: 'HO-002', careSummary: '黄疸需复查', medicine: '维生素 D', familySigned: '未签收', handoverStatus: '待评估', measurable: true },
  { id: 'BABY-003', babyName: '米粒', room: '305', store: stores[1], logDate: dates(1), careDate: dates(1), measuredAt: `${dates(1)} 10:10`, recordDate: dates(1), handoverDate: dates(8), feeding: '母乳 7 次', sleep: '15 小时', diaper: '正常', temperature: '36.5℃', temperatureStatus: '已确认', status: '已完成', completionStatus: '已复核', careItem: '沐浴', nurseName: '赵护士', result: '皮肤状态良好', growthStage: '入住初始', ageDays: 25, weight: '4.0kg', height: '53cm', milestone: '笑声回应', visitNo: 'VIS-003', visitorName: '赵女士', relationship: '奶奶', visitDate: dates(2), disinfection: '已核验', visitStatus: '已离场', handoverNo: 'HO-003', careSummary: '资料已归档', medicine: '无', familySigned: '已签收', handoverStatus: '已完成', measurable: true }
]

const state = seedRows.slice()

function normalizeBody(config) {
  return config.body || {}
}

function filteredRows(config) {
  const query = config.query || {}
  return state.filter(row => Object.keys(query).every(key => {
    const value = query[key]
    if (!value || (Array.isArray(value) && !value.length)) return true
    if (Array.isArray(value)) return true
    return String(row[key] || '').includes(String(value))
  }))
}

function saveRow(config) {
  const body = normalizeBody(config)
  const index = state.findIndex(row => row.id === body.id)
  const row = { ...(index >= 0 ? state[index] : {}), ...body, id: body.id || `BABY-${Date.now()}` }
  if (index >= 0) state.splice(index, 1, row)
  else state.unshift(row)
  return row
}

function performAction(config) {
  const body = normalizeBody(config)
  const row = state.find(item => item.id === body.id)
  if (row) {
    if (body.action === '标记完成' || body.action === '完成护理') row.status = '已完成'
    if (body.action === '开始执行') row.status = '执行中'
    if (body.action === '确认异常') row.temperatureStatus = '已确认'
    if (body.action === '完成离场') row.visitStatus = '已离场'
    if (body.action === '确认交接') row.handoverStatus = '已完成'
  }
  return row || { id: body.id, action: body.action }
}

module.exports = [
  {
    url: '/vue-element-admin/erp/baby/modules/[^/]+$',
    type: 'get',
    response: config => ({ code: 20000, data: { list: filteredRows(config), total: filteredRows(config).length, stores } })
  },
  {
    url: '/vue-element-admin/erp/baby/modules/[^/]+/save$',
    type: 'post',
    response: config => ({ code: 20000, data: saveRow(config) })
  },
  {
    url: '/vue-element-admin/erp/baby/modules/[^/]+/action$',
    type: 'post',
    response: config => ({ code: 20000, data: performAction(config) })
  }
]

module.exports.names = names
