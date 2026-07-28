const column = (key, label, width = 110) => ({ key, label, width })

const contractBaseColumns = [
  column('serviceName', '项目名称', 180),
  column('projectType', '项目类型', 110),
  column('stage', '阶段', 90),
  column('price', '价格', 90),
  column('unit', '单位', 70),
  column('quantity', '数量', 75),
  column('remainingQuantity', '剩余数量', 90)
]

const contractDateColumns = [
  column('validDays', '有效天数', 90),
  column('startDate', '开始日期', 115),
  column('endDate', '结束日期', 115),
  column('remainingDays', '剩余天数', 90)
]

export const serviceCardTabs = [
  {
    key: 'contractInside',
    label: '月子合同套餐内服务',
    originalGridId: 'list2',
    columns: [...contractBaseColumns, ...contractDateColumns]
  },
  {
    key: 'contractOutside',
    label: '月子合同套餐外服务',
    originalGridId: 'list3',
    columns: [
      ...contractBaseColumns,
      column('assignee', '当前分配人', 110),
      ...contractDateColumns
    ]
  },
  {
    key: 'extraPurchase',
    label: '额外购服务',
    originalGridId: 'list4',
    columns: [
      ...contractBaseColumns,
      column('assignee', '当前分配人', 110),
      column('validDays', '有效天数', 90),
      column('startDate', '开始日期', 115),
      column('endDate', '截止日期', 115),
      column('sourceNo', '来源单号', 145),
      column('remainingDays', '剩余天数', 90)
    ]
  },
  {
    key: 'projectCard',
    label: '项目卡服务',
    originalGridId: 'list5',
    columns: [
      column('cardNo', '年卡编号', 135),
      column('cardName', '卡名称', 150),
      column('cardType', '卡类型', 100),
      column('projectType', '项目类型', 110),
      column('customerName', '客户姓名', 110),
      column('price', '价格', 90),
      column('days', '天数', 75),
      column('sourceNo', '来源单号', 145)
    ],
    detailColumns: [
      column('serviceName', '项目名称', 170),
      column('projectType', '项目类型', 105),
      column('unit', '单位', 70),
      column('quantity', '数量', 75),
      column('remainingQuantity', '剩余数量', 90),
      column('endDate', '截止日期', 115)
    ]
  }
]

export const serviceListFilters = [
  { key: 'customerName', label: '客户姓名', type: 'input' },
  { key: 'mobile', label: '手机号', type: 'input' },
  { key: 'serviceName', label: '项目名称', type: 'input' },
  { key: 'technician', label: '产康师', type: 'input' },
  { key: 'remainingMax', label: '剩余次数(<=)', type: 'input' },
  {
    key: 'serviceType',
    label: '类型',
    type: 'select',
    options: ['-全部-', '套餐内', '套餐外', '额外购', '月嫂合同', '产康合同'],
    defaultValue: '-全部-'
  },
  {
    key: 'projectCategory',
    label: '项目类别',
    type: 'select',
    options: ['-请选择-', '产后类', '产康服务', '护理服务', '膳食服务', '客房服务', '增值服务', '软硬件服务', '大礼包', '科颜肌肤'],
    defaultValue: '-请选择-'
  },
  {
    key: 'store',
    label: '意向分店',
    type: 'select',
    options: ['-全部-', '中心广场旗舰店', '黄河路轻奢店'],
    defaultValue: '黄河路轻奢店'
  },
  {
    key: 'customerStatus',
    label: '客户状态',
    type: 'select',
    options: ['-全部-', '正入住', '已出所', '未入住'],
    defaultValue: '正入住'
  }
]

export const serviceListColumns = [
  column('customerName', '姓名', 105),
  column('mobile', '手机号', 125),
  column('room', '房间号', 85),
  column('deliveryMode', '分娩方式', 105),
  column('deliveryDate', '分娩日期', 115),
  column('checkInDate', '入住日期', 115),
  column('checkOutDate', '出所日期', 115),
  column('serviceName', '项目名称', 175),
  column('cardName', '卡名称', 145),
  column('serviceType', '类型', 90),
  column('projectCategory', '项目类别', 105),
  column('duration', '项目时长', 90),
  column('completedCount', '已服务次数', 100),
  column('remainingCount', '剩余次数', 90),
  column('technician', '产康师', 100),
  column('deadline', '截止日期', 125),
  column('store', '销售分店', 145)
]

export const serviceOverviewEvidence = {
  wrapperPath: 'Page/NursingManager/CusServerSearch.aspx?navid=553',
  cardModePath: 'Page/NursingManager/SelectFWByCard.aspx',
  listModePath: 'Page/NursingManager/ComprehensiveServiceSearch.aspx',
  completionLevel: 'Schema-faithful（双模式、查询区与列表）'
}
