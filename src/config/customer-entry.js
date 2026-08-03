export const customerStatusOptions = ['意向A', '意向B', '意向C', '意向D', '意向E', '流失客户', '散客客户', '同意签合同']

export const countryCodeOptions = [
  { label: '中国大陆 +86', value: '+86' },
  { label: '中国香港 +852', value: '+852' },
  { label: '中国澳门 +853', value: '+853' },
  { label: '中国台湾 +886', value: '+886' }
]

export const legacyCustomerTags = ['重点关注', '有钱', '重男轻女', '新晋辣妈', '备孕']

export const legacyCustomerSources = [
  '客户介绍',
  '住附近',
  '电话来访',
  '大众点评',
  '美团咨询',
  '地推拓客',
  '抖音咨询',
  '小红书咨询',
  '自然上门',
  '网络搜索',
  '市场渠道',
  '二胎入住',
  '内部资源'
]

export const stores = ['中心广场旗舰店', '黄河路轻奢店']

export const roomTypes = [
  '豪华套房', '舒适大床', '温馨雅间', '尊享套房', '舒适小套', '5楼VIP', '3楼VIP', '臻享套房',
  '至尊女王', '精致尊享A', '精致尊享B', '总统套房', '基础套餐', '修复套餐', '修养套餐',
  '私享套餐', '女王套餐（私人定制）', '总统套餐（私人定制）'
]

export const mealPackages = ['标准28天套餐', '28天月子膳食套餐']

export const documentTypes = [
  '中国大陆居民身份证', '香港来往大陆通行证', '澳门来往大陆通行证', '台湾来往大陆通行证', '护照'
]

export const deliveryMethods = ['顺产分娩', '剖宫产分娩', '小月子', '未生产']
export const introducerTypes = ['客户介绍', '同行介绍', '员工介绍', '自定义介绍']
export const fetusTypes = ['单胎', '双胎', '三胎', '多胎', '不详']
export const pregnancyCounts = ['一胎', '二胎', '三胎', '四胎', '五胎', '六胎']

export const sectionFieldKeys = {
  customer: ['name', 'mobile', 'wechat', 'status', 'source', 'memberCard', 'tags', 'isToStore'],
  intention: ['intendedStore', 'dueDate', 'intendedDays', 'plannedStayDate', 'room', 'roomType', 'contractAmount', 'packageName', 'packageAmount', 'mealPackage', 'recoveryStore'],
  detail: ['documentType', 'documentNo', 'deliveryMethod', 'sex', 'birthday', 'age', 'introducerType', 'introducerName', 'introducerPhone', 'reviewDate', 'companionName', 'companionPhone', 'prenatalHospital', 'fetusType', 'pregnancyCount', 'area', 'firstVisitAt', 'trackerName', 'ethnicity', 'nativePlace', 'workUnit', 'occupation', 'email', 'entryTime', 'address', 'dietNote', 'customerNote']
}

export function createEmptyCustomer(entryTime) {
  return {
    name: '',
    countryCode: '+86',
    mobile: '',
    wechat: '',
    status: '',
    source: '',
    sourceId: '',
    memberCard: '',
    tags: [],
    isToStore: false,
    intendedStore: '中心广场旗舰店',
    dueDate: '',
    intendedDays: 28,
    plannedStayDate: '',
    room: '',
    roomId: '',
    roomType: '',
    roomTypeId: '',
    contractAmount: '',
    packageName: '',
    packageId: '',
    packageVersionId: '',
    packagePriceRuleId: '',
    packageAmount: '',
    mealPackage: '',
    recoveryStore: '中心广场旗舰店',
    documentType: '中国大陆居民身份证',
    documentNo: '',
    deliveryMethod: '',
    sex: '女',
    birthday: '',
    age: '',
    introducerType: '',
    introducerName: '',
    introducerId: '',
    introducerPhone: '',
    reviewDate: '',
    companionName: '',
    companionPhone: '',
    prenatalHospital: '',
    fetusType: '单胎',
    pregnancyCount: '一胎',
    area: '',
    areaId: '',
    firstVisitAt: '',
    trackerName: '',
    trackerId: '',
    trackerDepartment: '',
    ethnicity: '',
    nativePlace: '',
    workUnit: '',
    occupation: '',
    email: '',
    entryTime,
    address: '',
    dietNote: '',
    customerNote: ''
  }
}
