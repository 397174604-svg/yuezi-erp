const stores = ['中心广场旗舰店', '黄河路轻奢店']

const babyPageConfigs = {
  宝宝日志: {
    key: 'baby-log',
    apiAvailable: true,
    kind: 'log',
    eyebrow: 'F027 · 宝宝膳食 / 母婴照护',
    description: '以宝宝为主线记录喂养、睡眠、排便和异常观察，形成每日照护闭环。',
    actions: ['新增照护记录', '标记完成', '异常上报'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'room', label: '房间号', type: 'input' },
      { key: 'logDate', label: '记录日期', type: 'date' },
      { key: 'status', label: '任务状态', type: 'select', options: ['待记录', '已记录', '需关注', '已完成'] }
    ],
    columns: ['babyName', 'room', 'logDate', 'feeding', 'sleep', 'diaper', 'temperature', 'status']
  },
  '宝宝日志补全（睡眠/哭闹/排便量）': {
    key: 'baby-log-completion',
    apiAvailable: true,
    kind: 'log',
    eyebrow: 'F069 · 宝宝日志补全',
    description: '补全睡眠、哭闹与排便量等高频指标，支持按班次追溯漏记项目。',
    actions: ['补录日志', '标记完成', '异常上报'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'nurseName', label: '责任护士', type: 'input' },
      { key: 'logDate', label: '记录日期', type: 'date' },
      { key: 'completionStatus', label: '补全状态', type: 'select', options: ['待补全', '已补全', '已复核'] }
    ],
    columns: ['babyName', 'room', 'logDate', 'sleepHours', 'cryCount', 'stoolAmount', 'nurseName', 'completionStatus']
  },
  新生儿护理记录: {
    key: 'newborn-care-records',
    apiAvailable: true,
    kind: 'care',
    eyebrow: 'F111 · 新生儿护理记录',
    description: '记录沐浴、脐部、黄疸、喂养等新生儿护理项目，按护理任务追踪执行结果。',
    actions: ['新增护理记录', '开始执行', '完成护理', '异常上报'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'careItem', label: '护理项目', type: 'select', options: ['沐浴', '脐部护理', '黄疸观察', '喂养指导'] },
      { key: 'careDate', label: '护理日期', type: 'date' },
      { key: 'status', label: '执行状态', type: 'select', options: ['待执行', '执行中', '已完成', '需复核'] }
    ],
    columns: ['recordNo', 'babyName', 'room', 'careItem', 'careDate', 'nurseName', 'result', 'status']
  },
  体温监测与异常预警: {
    key: 'baby-temperature',
    apiAvailable: true,
    kind: 'temperature',
    eyebrow: 'F112 · 体温监测与异常预警',
    description: '按时间轴查看体温趋势，自动突出异常值并进入护士复核与通知流程。',
    actions: ['录入体温', '确认异常', '通知家属'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'room', label: '房间号', type: 'input' },
      { key: 'measuredAt', label: '监测日期', type: 'date' },
      { key: 'temperatureStatus', label: '预警状态', type: 'select', options: ['正常', '待复核', '已确认'] }
    ],
    columns: ['babyName', 'room', 'measuredAt', 'temperature', 'measurer', 'temperatureStatus', 'actionNote']
  },
  药品管理: {
    key: 'baby-medications',
    apiAvailable: true,
    kind: 'medication',
    eyebrow: 'F120 · 药品管理',
    description: '维护宝宝用药医嘱、发药核对和服用记录，区分待执行、已执行与需复核状态。',
    actions: ['新增用药记录', '确认发药', '完成服用', '异常上报'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'medicineName', label: '药品名称', type: 'input' },
      { key: 'medicationDate', label: '用药日期', type: 'date' },
      { key: 'medicationStatus', label: '用药状态', type: 'select', options: ['待执行', '已发药', '已服用', '需复核'] }
    ],
    columns: ['medicineNo', 'babyName', 'room', 'medicineName', 'dose', 'medicationDate', 'operator', 'medicationStatus']
  },
  宝宝成长档案: {
    key: 'baby-growth-profile',
    apiAvailable: true,
    kind: 'growth',
    eyebrow: 'F115 · 宝宝成长档案',
    description: '汇总出生信息、体重身长和里程碑，支持按宝宝查看阶段性成长变化。',
    actions: ['新增成长记录', '生成成长摘要', '打印档案'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'room', label: '房间号', type: 'input' },
      { key: 'recordDate', label: '记录日期', type: 'date' },
      { key: 'growthStage', label: '成长阶段', type: 'select', options: ['入住初始', '住中观察', '离所评估'] }
    ],
    columns: ['babyName', 'room', 'recordDate', 'ageDays', 'weight', 'height', 'milestone', 'growthStage']
  },
  访客管理: {
    key: 'baby-visitors',
    apiAvailable: true,
    kind: 'visitor',
    eyebrow: 'F121 · 访客管理',
    description: '登记访客、探访时段与消毒核验结果，保证母婴区域访客可追溯。',
    actions: ['新增访客登记', '核验入场', '完成离场'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'visitorName', label: '访客姓名', type: 'input' },
      { key: 'visitDate', label: '探访日期', type: 'date' },
      { key: 'visitStatus', label: '访客状态', type: 'select', options: ['待核验', '已入场', '已离场', '拒绝入场'] }
    ],
    columns: ['visitNo', 'babyName', 'visitorName', 'relationship', 'visitDate', 'disinfection', 'visitStatus']
  },
  离所评估与交接: {
    key: 'baby-discharge-handover',
    apiAvailable: true,
    kind: 'handover',
    eyebrow: 'F122 · 离所评估与交接',
    description: '以离所清单核对护理、用药、成长资料和家属签收，避免交接遗漏。',
    actions: ['新增离所评估', '确认交接', '打印交接单'],
    filters: [
      { key: 'babyName', label: '宝宝姓名', type: 'input' },
      { key: 'room', label: '房间号', type: 'input' },
      { key: 'handoverDate', label: '计划离所日', type: 'date' },
      { key: 'handoverStatus', label: '交接状态', type: 'select', options: ['待评估', '待家属签收', '已完成'] }
    ],
    columns: ['handoverNo', 'babyName', 'room', 'handoverDate', 'careSummary', 'medicine', 'familySigned', 'handoverStatus']
  }
}

const babyTitleAliases = {
  宝宝日志补全: '宝宝日志补全（睡眠/哭闹/排便量）'
}

export function getBabyPageConfig(title) {
  return babyPageConfigs[babyTitleAliases[title] || title] || babyPageConfigs.宝宝日志
}

export { stores as babyStores }
