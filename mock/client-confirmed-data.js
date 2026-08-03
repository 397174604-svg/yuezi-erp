const CLIENT_DATA_SOURCE = '甲方聊天记录及《奇德芬芳母婴俱乐部·修养套餐价目表》（2026-07-16/17）'
const CENTER_ROOM_SOURCE = '甲方提供的中心广场旗舰店房态及房型截图（2026-07-30）'
const YELLOW_RIVER_ROOM_SOURCE = '甲方黄河路床位聊天记录及原ERP房态/房型筛选结果（2026-07-30）'
const YELLOW_RIVER_PACKAGE_SOURCE = '甲方提供的黄河路套餐PDF（基础/修复/修养/女王/总统，2026-07-30整理）'

const packageDefinitions = [
  {
    code: 'BASE',
    name: '基础套餐',
    nursingType: '未注明',
    roomType: '待甲方确认',
    allowedRoomTypes: ['大床房'],
    prices: {
      28: [35880, 24999, 21999],
      35: [42880, 29999, 26999],
      42: [49880, 34999, 31999],
      56: [62880, 43999, 40999]
    }
  },
  {
    code: 'REC-B',
    name: '修养套餐B',
    nursingType: '护士团队',
    roomType: '待甲方确认',
    allowedRoomTypes: ['套房'],
    prices: {
      28: [39880, 27999, 24999],
      35: [47880, 32999, 30999],
      42: [55880, 38999, 35999],
      56: [69880, 48999, 45999]
    }
  },
  {
    code: 'REC-A',
    name: '修养套餐A',
    nursingType: '7天一对一',
    roomType: '待甲方确认',
    allowedRoomTypes: ['套房'],
    prices: {
      28: [43880, 30999, 27999],
      35: [52880, 36999, 33999],
      42: [61880, 42999, 39999],
      56: [78880, 54999, 51999]
    }
  },
  {
    code: 'PREM-B',
    name: '精致尊享B',
    nursingType: '双师护航',
    roomType: '待甲方确认',
    allowedRoomTypes: ['套房'],
    prices: {
      28: [49880, 34999, 31999],
      35: [59880, 41999, 38999],
      42: [69880, 48999, 45999],
      56: [88880, 61999, 58999]
    }
  },
  {
    code: 'PREM-A',
    name: '精致尊享A',
    nursingType: '双师护航',
    roomType: '待甲方确认',
    allowedRoomTypes: ['套房'],
    prices: {
      28: [52880, 36999, 33999],
      35: [66880, 44999, 41999],
      42: [79880, 53999, 48999],
      56: [100880, 65999, 62999]
    }
  },
  {
    code: 'VIP3',
    name: '臻享套餐VIP3楼',
    nursingType: '双师护航',
    roomType: 'VIP3楼',
    allowedRoomTypes: ['VIP302'],
    prices: {
      28: [59880, 41999, 38999],
      35: [74880, 50999, 47999],
      42: [89880, 58999, 55999],
      56: [118880, 74999, 71999]
    }
  },
  {
    code: 'VIP5',
    name: '至尊套餐VIP5楼',
    nursingType: '双师护航',
    roomType: 'VIP5楼',
    allowedRoomTypes: ['VIP512'],
    prices: {
      28: [79880, 53999, 50999],
      35: [99880, 65999, 62999],
      42: [118880, 75999, 72999],
      56: [159880, 95999, 92999]
    }
  }
]

const yellowRiverPackageDefinitions = [
  {
    code: 'BASE',
    name: '基础套餐',
    nursingType: '基础护理',
    accommodationDescription: '敞亮一居室 / 大一居室',
    allowedRoomTypes: ['大床房'],
    prices: { 28: 24999, 35: 29999, 42: 35999, 56: 45999 }
  },
  {
    code: 'BASE-721',
    name: '基础系列7+21',
    nursingType: '7天一对一+21天团队护理',
    accommodationDescription: '敞亮一居室 / 大一居室',
    allowedRoomTypes: ['大床房'],
    prices: { 28: 27999, 35: 33999, 42: 39999, 56: 51999 }
  },
  {
    code: 'REPAIR',
    name: '修复套餐',
    nursingType: '产后修复',
    accommodationDescription: '一房一厅',
    allowedRoomTypes: ['一房一厅'],
    prices: { 28: 27999, 35: 33999, 42: 39999, 56: 51999 }
  },
  {
    code: 'REPAIR-721',
    name: '修复7+21',
    nursingType: '7天一对一+21天团队护理',
    accommodationDescription: '一房一厅',
    allowedRoomTypes: ['一房一厅'],
    prices: { 28: 29999, 35: 35999, 42: 42999, 56: 55999 }
  },
  {
    code: 'RECOVERY',
    name: '修养套餐',
    nursingType: '修养护理',
    accommodationDescription: '一房一厅',
    allowedRoomTypes: ['一房一厅'],
    prices: { 28: 32999, 35: 39999, 42: 46999, 56: 61999 }
  },
  {
    code: 'QUEEN',
    name: '女王套餐',
    nursingType: '专属护理',
    accommodationDescription: '两房两厅（私人花园）',
    allowedRoomTypes: ['女王套房'],
    prices: { 28: 63999, 35: 76999, 42: 92999, 56: 120999 }
  },
  {
    code: 'PRESIDENT',
    name: '总统套餐',
    nursingType: '专属护理',
    accommodationDescription: '三房三厅',
    allowedRoomTypes: ['总统套房'],
    prices: { 28: 83999, 35: 100999, 42: 121999, 56: 158999 }
  }
]

function centerPackageCatalog() {
  return packageDefinitions.flatMap((definition, packageIndex) => (
    Object.entries(definition.prices).map(([daysText, prices], dayIndex) => {
      const days = Number(daysText)
      const [originalPrice, activityPrice, dealPrice] = prices
      return {
        id: packageIndex * 4 + dayIndex + 1,
        packageNo: `QD-${definition.code}-${days}`,
        basePackageCode: `QD-${definition.code}`,
        basePackageName: definition.name,
        packageName: `${definition.name}（${days}天）`,
        days,
        packageDays: days,
        nursingType: definition.nursingType,
        roomType: definition.roomType,
        allowedRoomTypes: definition.allowedRoomTypes || [],
        roomBindingStatus: '临时推荐映射，待甲方确认套餐与具体房型/房号',
        originalPrice,
        referencePrice: originalPrice,
        activityPrice,
        dealPrice,
        salePrice: dealPrice,
        packageAmount: dealPrice,
        store_id: 1,
        store: '中心广场旗舰店',
        versionNo: '2026-07甲方价目表',
        effectiveDate: '待甲方确认',
        status: '已发布',
        auditStatus: '审核通过',
        enabled: '启用',
        visible: '是',
        recommended: '否',
        creator: '甲方资料导入',
        dataSource: CLIENT_DATA_SOURCE,
        dataStatus: '甲方价目表价格已录入；当前推荐房型为联调映射，价格生效日期、升级差价及具体房号待甲方确认',
        lineItems: []
      }
    })
  ))
}

function yellowRiverPackageCatalog() {
  return yellowRiverPackageDefinitions.flatMap((definition, packageIndex) => (
    Object.entries(definition.prices).map(([daysText, price], dayIndex) => {
      const days = Number(daysText)
      return {
        id: 101 + packageIndex * 4 + dayIndex,
        packageNo: `HH-${definition.code}-${days}`,
        basePackageCode: `HH-${definition.code}`,
        basePackageName: definition.name,
        packageName: `${definition.name}（${days}天）`,
        days,
        packageDays: days,
        nursingType: definition.nursingType,
        accommodationDescription: definition.accommodationDescription,
        roomType: definition.allowedRoomTypes.join('、'),
        allowedRoomTypes: definition.allowedRoomTypes,
        roomBindingStatus: '临时联调映射，待甲方确认具体房号绑定',
        originalPrice: price,
        referencePrice: price,
        activityPrice: price,
        dealPrice: price,
        salePrice: price,
        packageAmount: price,
        store_id: 2,
        store: '黄河路轻奢店',
        versionNo: '2026-07甲方PDF资料版',
        effectiveDate: '待甲方确认',
        status: '待确认',
        auditStatus: '待甲方确认',
        enabled: '启用',
        visible: '是',
        recommended: '否',
        creator: '甲方资料导入',
        dataSource: YELLOW_RIVER_PACKAGE_SOURCE,
        dataStatus: '甲方PDF标示价格已逐项核对；价格性质、生效日期及套餐与具体房号绑定待确认',
        lineItems: []
      }
    })
  ))
}

const confirmedPackageCatalog = [
  ...centerPackageCatalog(),
  ...yellowRiverPackageCatalog()
]

const SOUTH_FACING_ROOM_NOS = new Set([
  '202', '206', '208', '210',
  'VIP302', '306', '308', '310', '312',
  'F02', 'F06', 'F08', 'F10',
  '510', '506', '508', 'VIP512'
])

function confirmedRoomSlot(id, roomNo, roomType, floor, roomStyle, options = {}) {
  return {
    id,
    store_id: options.storeId || 1,
    room_no: roomNo,
    room_type: roomType,
    room_style: roomStyle || roomType,
    floor: String(floor),
    direction: options.direction || (SOUTH_FACING_ROOM_NOS.has(roomNo) ? '南' : '北'),
    daily_price: 0,
    status: options.status || '空闲',
    room_no_confirmed: true,
    room_type_confirmed: options.roomTypeConfirmed !== false,
    algorithm_enabled: options.algorithmEnabled !== false,
    allowed_package_codes: options.allowedPackageCodes || [],
    classification_note: options.classificationNote || '',
    data_source: options.dataSource || CENTER_ROOM_SOURCE
  }
}

const confirmedCenterRoomSlots = [
  confirmedRoomSlot(201, '201', '大床房', 2),
  confirmedRoomSlot(203, '203', '大床房', 2),
  confirmedRoomSlot(205, '205', '大床房', 2),
  confirmedRoomSlot(207, '207', '大床房', 2),
  confirmedRoomSlot(209, '209', '套房', 2, '豪华套房'),
  confirmedRoomSlot(211, '211', '小套房', 2),
  confirmedRoomSlot(213, '213', '特价房', 2, '特价房', {
    roomTypeConfirmed: false,
    classificationNote: '未出现在已提供的大床房、小套房、尊享套房和豪华套房筛选图中，按36间总量及原2间特价房口径暂定'
  }),
  confirmedRoomSlot(202, '202', '套房', 2, '豪华套房'),
  confirmedRoomSlot(206, '206', '套房', 2, '豪华套房'),
  confirmedRoomSlot(208, '208', '小套房', 2),
  confirmedRoomSlot(210, '210', '特价房', 2, '特价房', {
    roomTypeConfirmed: false,
    classificationNote: '未出现在已提供的大床房、小套房、尊享套房和豪华套房筛选图中，按36间总量及原2间特价房口径暂定'
  }),
  confirmedRoomSlot(301, '301', '大床房', 3),
  confirmedRoomSlot(303, '303', '大床房', 3),
  confirmedRoomSlot(305, '305', '套房', 3, '豪华套房'),
  confirmedRoomSlot(307, '307', '套房', 3, '豪华套房'),
  confirmedRoomSlot(309, '309', '套房', 3, '豪华套房'),
  confirmedRoomSlot(302, 'VIP302', 'VIP302', 3, 'VIP专属房', { status: '已预订' }),
  confirmedRoomSlot(306, '306', '套房', 3, '豪华套房'),
  confirmedRoomSlot(308, '308', '套房', 3, '豪华套房'),
  confirmedRoomSlot(310, '310', '套房', 3, '豪华套房'),
  confirmedRoomSlot(312, '312', '套房', 3, '豪华套房'),
  confirmedRoomSlot(4001, 'F01', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4003, 'F03', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4005, 'F05', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4007, 'F07', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4009, 'F09', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4002, 'F02', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4006, 'F06', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4008, 'F08', '套房', 4, '豪华套房'),
  confirmedRoomSlot(4010, 'F10', '套房', 4, '豪华套房'),
  confirmedRoomSlot(501, '501', '套房', 5, '尊享套房'),
  confirmedRoomSlot(503, '503', '套房', 5, '尊享套房'),
  confirmedRoomSlot(510, '510', '套房', 5, '尊享套房'),
  confirmedRoomSlot(506, '506', '套房', 5, '尊享套房'),
  confirmedRoomSlot(508, '508', '套房', 5, '尊享套房'),
  confirmedRoomSlot(512, 'VIP512', 'VIP512', 5, 'VIP专属房')
]

const YELLOW_RIVER_BED_ROOMS = new Set(['F05', 'F07', 'F09', '505', '507', '509'])

function confirmedYellowRiverRoomSlot(id, roomNo, floor) {
  const commonOptions = {
    storeId: 2,
    direction: YELLOW_RIVER_BED_ROOMS.has(roomNo) ? '北' : '待确认',
    dataSource: YELLOW_RIVER_ROOM_SOURCE
  }
  if (YELLOW_RIVER_BED_ROOMS.has(roomNo)) {
    const roomStyle = floor === 4 ? '基础大床（4楼）' : '基础套餐大床（5楼）'
    return confirmedRoomSlot(id, roomNo, '大床房', floor, roomStyle, {
      ...commonOptions,
      allowedPackageCodes: ['HH-BASE', 'HH-BASE-721'],
      classificationNote: floor === 4
        ? '原ERP“舒适大床”筛选命中；甲方聊天称4楼北侧从东数3间为“基础大床”'
        : '原ERP“舒适大床”筛选命中；甲方聊天称5楼北侧从东数3间为“大床（基础套餐）”'
    })
  }
  if (roomNo === 'VIP999') {
    return confirmedRoomSlot(id, roomNo, '总统套房', floor, '三房三厅（总统套）', {
      ...commonOptions,
      allowedPackageCodes: ['HH-PRESIDENT'],
      classificationNote: '原ERP“总统套房”筛选命中，甲方聊天确认位于5楼最北边'
    })
  }
  if (roomNo === 'VIP777') {
    return confirmedRoomSlot(id, roomNo, '女王套房', floor, '两房两厅（女王套）', {
      ...commonOptions,
      allowedPackageCodes: ['HH-QUEEN'],
      classificationNote: '原ERP“至尊女王”筛选命中，甲方聊天确认6楼单独一间'
    })
  }
  return confirmedRoomSlot(id, roomNo, '一房一厅', floor, '一房一厅', {
    ...commonOptions,
    allowedPackageCodes: ['HH-REPAIR', 'HH-REPAIR-721', 'HH-RECOVERY'],
    classificationNote: '甲方确认除6间大床、总统套和女王套以外，其余房间均为一房一厅'
  })
}

const confirmedYellowRiverRoomSlots = [
  confirmedYellowRiverRoomSlot(2302, '302', 3),
  confirmedYellowRiverRoomSlot(2306, '306', 3),
  confirmedYellowRiverRoomSlot(2308, '308', 3),
  confirmedYellowRiverRoomSlot(2310, '310', 3),
  confirmedYellowRiverRoomSlot(2301, '301', 3),
  confirmedYellowRiverRoomSlot(2303, '303', 3),
  confirmedYellowRiverRoomSlot(2305, '305', 3),
  confirmedYellowRiverRoomSlot(2307, '307', 3),
  confirmedYellowRiverRoomSlot(2402, 'F02', 4),
  confirmedYellowRiverRoomSlot(2406, 'F06', 4),
  confirmedYellowRiverRoomSlot(2408, 'F08', 4),
  confirmedYellowRiverRoomSlot(2410, 'F10', 4),
  confirmedYellowRiverRoomSlot(2412, 'F12', 4),
  confirmedYellowRiverRoomSlot(2416, 'F16', 4),
  confirmedYellowRiverRoomSlot(2401, 'F01', 4),
  confirmedYellowRiverRoomSlot(2403, 'F03', 4),
  confirmedYellowRiverRoomSlot(2405, 'F05', 4),
  confirmedYellowRiverRoomSlot(2407, 'F07', 4),
  confirmedYellowRiverRoomSlot(2409, 'F09', 4),
  confirmedYellowRiverRoomSlot(2502, '502', 5),
  confirmedYellowRiverRoomSlot(2506, '506', 5),
  confirmedYellowRiverRoomSlot(2508, '508', 5),
  confirmedYellowRiverRoomSlot(2510, '510', 5),
  confirmedYellowRiverRoomSlot(2512, '512', 5),
  confirmedYellowRiverRoomSlot(2501, '501', 5),
  confirmedYellowRiverRoomSlot(2503, '503', 5),
  confirmedYellowRiverRoomSlot(2505, '505', 5),
  confirmedYellowRiverRoomSlot(2507, '507', 5),
  confirmedYellowRiverRoomSlot(2509, '509', 5),
  confirmedYellowRiverRoomSlot(2999, 'VIP999', 5),
  confirmedYellowRiverRoomSlot(2777, 'VIP777', 6)
]

const centerRoomInventoryEvidence = {
  store: '中心广场旗舰店',
  typeCounts: [
    { roomType: '大床房', count: 6 },
    { roomType: '小套房', count: 2 },
    { roomType: '特价房', count: 2 },
    { roomType: '套房', count: 24 },
    { roomType: 'VIP302', count: 1 },
    { roomType: 'VIP512', count: 1 }
  ],
  enumeratedTotal: 36,
  confirmedRoomNoTotal: 36,
  pendingRoomNoTotal: 0,
  floorCounts: [
    { floor: '2', count: 11 },
    { floor: '3', count: 10 },
    { floor: '4', count: 9 },
    { floor: '5', count: 6 }
  ],
  directionCounts: [
    { direction: '南', count: 17 },
    { direction: '北', count: 19 }
  ],
  classificationNotes: [
    '尊享套房5间与豪华套房19间暂统一归入“套房”，保留room_style便于后续拆分',
    '213、210按排除法及原2间特价房口径暂归“特价房”，待甲方确认'
  ],
  algorithmReadyTotal: 36,
  summary: '36间具体房号、楼层和南北朝向均已录入并可进入排房算法；尊享套房和豪华套房暂统一按“套房”，213、210暂按“特价房”待甲方确认。',
  pendingFields: ['213、210的特价房归类', '尊享套房与豪华套房的正式分类口径', '各房型对应价格与可售套餐'],
  dataSource: CENTER_ROOM_SOURCE
}

const yellowRiverRoomInventoryEvidence = {
  store: '黄河路轻奢店',
  typeCounts: [
    { roomType: '一房一厅', count: 23 },
    { roomType: '大床房', count: 6 },
    { roomType: '总统套房', count: 1 },
    { roomType: '女王套房', count: 1 }
  ],
  enumeratedTotal: 31,
  confirmedRoomNoTotal: 31,
  pendingRoomNoTotal: 0,
  algorithmReadyTotal: 31,
  floorCounts: [
    { floor: '3', count: 8 },
    { floor: '4', count: 11 },
    { floor: '5', count: 11 },
    { floor: '6', count: 1 }
  ],
  directionCounts: [
    { direction: '北', count: 6 },
    { direction: '待确认', count: 25 }
  ],
  classificationNotes: [
    'F05、F07、F09由原ERP“舒适大床”筛选确认，按聊天口径标为4楼基础大床',
    '505、507、509由原ERP“舒适大床”筛选确认，按聊天口径标为5楼基础套餐大床',
    'VIP999由原ERP“总统套房”筛选确认；VIP777由原ERP“至尊女王”筛选确认',
    '除上述8间外，其余23间按甲方最新口径归为一房一厅（修复套餐）',
    '2楼为产康室，不纳入可售客房和智能排房'
  ],
  summary: '31个真实房号已录入并进入本地智能排房；当前仅6间大床确认北向，其余25间朝向待甲方补充。原ERP中的客户姓名、历史入住和收款数据未复制。',
  pendingFields: ['其余25间房的南北朝向', '房型与正式销售套餐/价格的绑定规则'],
  dataSource: YELLOW_RIVER_ROOM_SOURCE
}

const roomInventoryEvidence = {
  stores: [centerRoomInventoryEvidence, yellowRiverRoomInventoryEvidence],
  dataSource: `${CENTER_ROOM_SOURCE}；${YELLOW_RIVER_ROOM_SOURCE}`
}

module.exports = {
  CLIENT_DATA_SOURCE,
  CENTER_ROOM_SOURCE,
  YELLOW_RIVER_ROOM_SOURCE,
  YELLOW_RIVER_PACKAGE_SOURCE,
  confirmedPackageCatalog,
  confirmedCenterRoomSlots,
  confirmedYellowRiverRoomSlots,
  roomInventoryEvidence
}
