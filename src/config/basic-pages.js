import { applyAuditedSurfaceEvidence } from './audited-surface-adapter'

const draftField = (key, label, type = 'input', options = []) => ({
  key,
  label,
  type,
  options: [...options],
  verified: false
})

const input = (key, label) => draftField(key, label)
const select = (key, label) => draftField(key, label, 'select', ['待原系统核验'])
const date = (key, label) => draftField(key, label, 'date')
const dateRange = (key, label) => draftField(key, label, 'dateRange')
const number = (key, label) => draftField(key, label, 'number')
const textarea = (key, label) => draftField(key, label, 'textarea')
const tree = (key, label) => draftField(key, label, 'tree')

const draftColumn = (key, label, format = 'text', width = 120) => ({
  key,
  label,
  format,
  width,
  verified: false
})

const text = (key, label, width) => draftColumn(key, label, 'text', width)
const status = (key = 'status', label = '状态') => draftColumn(key, label, 'status', 90)
const money = (key, label) => draftColumn(key, label, 'money', 120)
const quantity = (key, label) => draftColumn(key, label, 'quantity', 100)
const dateColumn = (key, label) => draftColumn(key, label, 'date', 130)

const basicOriginalUrls = {
  职员档案: 'Page/BasicInfo/EmpInfo.aspx?navid=149',
  基础项目: 'Page/BasicInfo/BasicProject.aspx?navid=142',
  物料档案: 'Page/BasicInfo/BasicItem.aspx?navid=144',
  客房档案: 'Page/BasicInfo/GuestRoom.aspx?navid=148',
  满意度调查表模板: 'Page/BasicInfo/EvalueContetnList.aspx?navid=531',
  调查表管理: 'Page/BasicInfo/QuestionnaireList.aspx?navid=638',
  仓库档案: 'Page/BasicInfo/StoreFies.aspx?navid=480',
  供应商档案: 'Page/StoreManager/SupplierMassager.aspx?navid=315',
  资金账户: 'Page/BasicInfo/AcountManager.aspx?navid=528',
  报表模板: 'Page/BasicInfo/CustomReportList.aspx?navid=554',
  护理模板: 'Page/BasicInfo/DefinedTempList.aspx?navid=507',
  任务管理: 'Page/BasicInfo/TaskManagerList.aspx?navid=538',
  服务时间设置: 'Page/BasicInfo/ServiceSet.aspx?navid=543',
  项目手工费设置: 'Page/BasicInfo/BasicProjectFeeSet.aspx?navid=550',
  提成比例设置: 'Page/BasicInfo/DeductList.aspx?navid=632',
  设备管理: 'Page/BasicInfo/EquipmentList.aspx?navid=623',
  业绩目标设置: 'Page/BasicInfo/Targetamount.aspx?navid=634',
  优惠金额授权: 'Page/BasicInfo/RoleAmtList.aspx?navid=661',
  床位管理: 'Page/BasicInfo/BunkList.aspx?navid=624'
}

const defineBasicPage = ({
  title,
  key,
  mode = 'list',
  description,
  filters,
  columns,
  formFields = [],
  structure = []
}) => ({
  title,
  key,
  mode,
  description,
  filters,
  columns,
  formFields,
  structure,
  originalUrl: basicOriginalUrls[title] || '',
  originalNavid: ((basicOriginalUrls[title] || '').match(/navid=(\d+)/) || [])[1] || '',
  evidenceLevel: '菜单与 URL 已核验，页面字段待二次核验',
  completionLevel: 'Visible',
  evidenceNote: '菜单标题、顺序、原页面 URL 与 navid 已在原 ERP 登录会话核验；本页模式、字段、控件类型、选项、默认值、树层级、联动、工具栏、表头和表单仍为结构草案。'
})

const basicDefinitions = [
  defineBasicPage({
    title: '职员档案',
    key: 'employee-records',
    description: '职员身份、组织归属与任职信息结构草案。',
    filters: [input('keyword', '姓名/工号/手机号'), tree('organization', '组织机构'), select('employmentStatus', '任职状态')],
    columns: [text('employeeNo', '职员工号'), text('employeeName', '职员姓名'), text('mobile', '联系电话'), text('store', '所属门店', 150), text('department', '所属部门'), text('position', '职位'), dateColumn('hireDate', '入职日期'), status()],
    formFields: [input('employeeNo', '职员工号'), input('employeeName', '职员姓名'), input('mobile', '联系电话'), select('gender', '性别'), date('birthday', '出生日期'), tree('organization', '组织机构'), select('position', '职位'), date('hireDate', '入职日期'), select('employmentStatus', '任职状态'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '基础项目',
    key: 'basic-items',
    mode: 'tree-list',
    description: '服务项目分类、计价与业务属性结构草案。',
    filters: [input('keyword', '项目名称/编码'), tree('category', '项目分类'), select('enabled', '启用状态')],
    columns: [text('itemCode', '项目编码'), text('itemName', '项目名称', 170), text('category', '项目分类'), text('unit', '单位'), money('referencePrice', '参考价格'), text('businessType', '业务类型'), status()],
    formFields: [tree('parentCategory', '上级分类'), input('itemCode', '项目编码'), input('itemName', '项目名称'), select('businessType', '业务类型'), select('unit', '单位'), number('referencePrice', '参考价格'), select('enabled', '启用状态'), textarea('description', '项目说明')],
    structure: ['项目分类树', '项目列表']
  }),
  defineBasicPage({
    title: '物料档案',
    key: 'material-records',
    mode: 'tree-list',
    description: '物料分类、规格、单位与库存属性结构草案。',
    filters: [input('keyword', '物料名称/编码/条码'), tree('category', '物料分类'), select('enabled', '启用状态')],
    columns: [text('materialCode', '物料编码'), text('materialName', '物料名称', 170), text('category', '物料分类'), text('specification', '规格型号'), text('unit', '计量单位'), text('barcode', '条码'), money('referenceCost', '参考成本'), status()],
    formFields: [tree('category', '物料分类'), input('materialCode', '物料编码'), input('materialName', '物料名称'), input('specification', '规格型号'), select('unit', '计量单位'), input('barcode', '条码'), number('referenceCost', '参考成本'), number('safetyStock', '安全库存'), select('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['物料分类树', '物料列表']
  }),
  defineBasicPage({
    title: '客房档案',
    key: 'room-records',
    mode: 'tree-list',
    description: '门店、楼层、房型与客房基础信息结构草案。',
    filters: [select('store', '门店'), tree('floor', '楼层'), select('roomType', '房型'), select('roomStatus', '房间状态')],
    columns: [text('roomNo', '房间号'), text('store', '门店', 150), text('floor', '楼层'), text('roomType', '房型'), text('roomStyle', '房间风格'), text('orientation', '房间朝向'), text('window', '是否带窗'), status('roomStatus', '房间状态')],
    formFields: [select('store', '门店'), tree('floor', '楼层'), input('roomNo', '房间号'), select('roomType', '房型'), select('roomStyle', '房间风格'), select('orientation', '房间朝向'), select('window', '是否带窗'), select('roomStatus', '房间状态'), textarea('remark', '备注')],
    structure: ['门店/楼层树', '客房列表']
  }),
  defineBasicPage({
    title: '满意度调查表模板',
    key: 'satisfaction-survey-templates',
    mode: 'template',
    description: '满意度问卷模板与题目编排结构草案。',
    filters: [input('templateName', '模板名称'), select('templateType', '模板类型'), select('enabled', '启用状态')],
    columns: [text('templateCode', '模板编码'), text('templateName', '模板名称', 180), text('templateType', '模板类型'), quantity('questionCount', '题目数量'), text('applicableScope', '适用范围'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('templateCode', '模板编码'), input('templateName', '模板名称'), select('templateType', '模板类型'), select('applicableScope', '适用范围'), textarea('description', '模板说明'), select('enabled', '启用状态')],
    structure: ['模板信息', '题目明细', '评分规则']
  }),
  defineBasicPage({
    title: '调查表管理',
    key: 'survey-management',
    mode: 'template',
    description: '通用调查表及题目、选项和发布范围结构草案。',
    filters: [input('surveyName', '调查表名称'), select('surveyType', '调查类型'), select('publishStatus', '发布状态')],
    columns: [text('surveyCode', '调查表编码'), text('surveyName', '调查表名称', 180), text('surveyType', '调查类型'), quantity('questionCount', '题目数量'), text('publishScope', '发布范围'), dateColumn('effectiveDate', '生效日期'), status('publishStatus', '发布状态')],
    formFields: [input('surveyCode', '调查表编码'), input('surveyName', '调查表名称'), select('surveyType', '调查类型'), select('publishScope', '发布范围'), dateRange('effectiveRange', '有效期'), textarea('description', '说明')],
    structure: ['调查表信息', '题目明细', '选项设置', '发布范围']
  }),
  defineBasicPage({
    title: '仓库档案',
    key: 'warehouse-records',
    mode: 'tree-list',
    description: '仓库、库区与业务归属结构草案。',
    filters: [input('keyword', '仓库名称/编码'), select('store', '所属门店'), select('warehouseType', '仓库类型'), select('enabled', '启用状态')],
    columns: [text('warehouseCode', '仓库编码'), text('warehouseName', '仓库名称', 170), text('store', '所属门店', 150), text('warehouseType', '仓库类型'), text('manager', '负责人'), text('location', '仓库地址', 180), status()],
    formFields: [input('warehouseCode', '仓库编码'), input('warehouseName', '仓库名称'), select('store', '所属门店'), select('warehouseType', '仓库类型'), input('manager', '负责人'), input('phone', '联系电话'), input('location', '仓库地址'), select('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['仓库列表', '库区设置']
  }),
  defineBasicPage({
    title: '供应商档案',
    key: 'supplier-records',
    description: '供应商主体、联系人与结算信息结构草案。',
    filters: [input('keyword', '供应商名称/编码'), select('supplierType', '供应商类型'), select('cooperationStatus', '合作状态')],
    columns: [text('supplierCode', '供应商编码'), text('supplierName', '供应商名称', 180), text('supplierType', '供应商类型'), text('contactName', '联系人'), text('contactPhone', '联系电话'), text('settlementMethod', '结算方式'), status('cooperationStatus', '合作状态')],
    formFields: [input('supplierCode', '供应商编码'), input('supplierName', '供应商名称'), select('supplierType', '供应商类型'), input('contactName', '联系人'), input('contactPhone', '联系电话'), input('address', '联系地址'), input('taxNo', '税号'), input('bankAccount', '银行账号'), select('settlementMethod', '结算方式'), select('cooperationStatus', '合作状态'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '资金账户',
    key: 'fund-accounts',
    description: '收付款账户、开户信息与适用门店结构草案。',
    filters: [input('keyword', '账户名称/账号'), select('accountType', '账户类型'), select('store', '适用门店'), select('enabled', '启用状态')],
    columns: [text('accountCode', '账户编码'), text('accountName', '账户名称', 170), text('accountType', '账户类型'), text('bankName', '开户银行', 150), text('accountNo', '账号', 170), text('store', '适用门店', 150), status()],
    formFields: [input('accountCode', '账户编码'), input('accountName', '账户名称'), select('accountType', '账户类型'), input('bankName', '开户银行'), input('accountNo', '账号'), input('accountHolder', '账户户名'), select('store', '适用门店'), select('enabled', '启用状态'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '报表模板',
    key: 'report-templates',
    mode: 'template',
    description: '业务打印或导出模板定义结构草案。',
    filters: [input('templateName', '模板名称'), select('businessType', '业务类型'), select('templateFormat', '模板格式'), select('enabled', '启用状态')],
    columns: [text('templateCode', '模板编码'), text('templateName', '模板名称', 180), text('businessType', '业务类型'), text('templateFormat', '模板格式'), text('version', '版本'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('templateCode', '模板编码'), input('templateName', '模板名称'), select('businessType', '业务类型'), select('templateFormat', '模板格式'), input('version', '版本'), textarea('templateContent', '模板内容'), select('enabled', '启用状态')],
    structure: ['模板信息', '模板内容/文件', '参数占位符']
  }),
  defineBasicPage({
    title: '护理模板',
    key: 'nursing-templates',
    mode: 'template',
    description: '护理计划或护理记录模板结构草案。',
    filters: [input('templateName', '模板名称'), select('nursingType', '护理类型'), select('applicableObject', '适用对象'), select('enabled', '启用状态')],
    columns: [text('templateCode', '模板编码'), text('templateName', '模板名称', 180), text('nursingType', '护理类型'), text('applicableObject', '适用对象'), quantity('itemCount', '项目数量'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('templateCode', '模板编码'), input('templateName', '模板名称'), select('nursingType', '护理类型'), select('applicableObject', '适用对象'), textarea('description', '模板说明'), select('enabled', '启用状态')],
    structure: ['模板信息', '护理项目明细', '频次/时间规则']
  }),
  defineBasicPage({
    title: '任务管理',
    key: 'task-management',
    mode: 'tree-list',
    description: '基础任务类型、归属部门与执行规则结构草案。',
    filters: [input('keyword', '任务名称/编码'), tree('taskCategory', '任务分类'), select('department', '执行部门'), select('enabled', '启用状态')],
    columns: [text('taskCode', '任务编码'), text('taskName', '任务名称', 180), text('taskCategory', '任务分类'), text('department', '执行部门'), text('frequency', '执行频次'), text('duration', '标准时长'), status()],
    formFields: [tree('taskCategory', '任务分类'), input('taskCode', '任务编码'), input('taskName', '任务名称'), select('department', '执行部门'), select('frequency', '执行频次'), number('duration', '标准时长'), select('enabled', '启用状态'), textarea('executionStandard', '执行标准')],
    structure: ['任务分类树', '任务列表']
  }),
  defineBasicPage({
    title: '服务时间设置',
    key: 'service-time-settings',
    mode: 'settings',
    description: '门店或项目可预约服务时段结构草案。',
    filters: [select('store', '门店'), select('serviceType', '服务类型'), input('serviceName', '服务项目'), select('enabled', '启用状态')],
    columns: [text('store', '门店', 150), text('serviceType', '服务类型'), text('serviceName', '服务项目', 170), text('weekday', '适用星期'), text('timeRange', '服务时段', 170), quantity('capacity', '时段容量'), status()],
    formFields: [select('store', '门店'), select('serviceType', '服务类型'), select('serviceName', '服务项目'), select('weekday', '适用星期'), input('startTime', '开始时间'), input('endTime', '结束时间'), number('capacity', '时段容量'), select('enabled', '启用状态')]
  }),
  defineBasicPage({
    title: '项目手工费设置',
    key: 'project-labor-fee-settings',
    mode: 'settings',
    description: '服务项目手工费规则结构草案。',
    filters: [select('store', '门店'), select('projectType', '项目类型'), input('projectName', '项目名称'), select('enabled', '启用状态')],
    columns: [text('projectCode', '项目编码'), text('projectName', '项目名称', 170), text('projectType', '项目类型'), text('store', '门店', 150), text('feeRule', '计费规则'), money('laborFee', '手工费'), dateColumn('effectiveDate', '生效日期'), status()],
    formFields: [select('store', '门店'), select('projectType', '项目类型'), select('projectName', '项目名称'), select('feeRule', '计费规则'), number('laborFee', '手工费'), dateRange('effectiveRange', '有效期'), select('enabled', '启用状态'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '提成比例设置',
    key: 'commission-rate-settings',
    mode: 'settings',
    description: '销售或服务提成比例规则结构草案。',
    filters: [select('store', '门店'), select('businessType', '业务类型'), select('employeeScope', '人员范围'), select('enabled', '启用状态')],
    columns: [text('ruleName', '规则名称', 170), text('store', '门店', 150), text('businessType', '业务类型'), text('employeeScope', '人员范围'), text('calculationBase', '计算基数'), text('commissionRate', '提成比例'), dateColumn('effectiveDate', '生效日期'), status()],
    formFields: [input('ruleName', '规则名称'), select('store', '门店'), select('businessType', '业务类型'), select('employeeScope', '人员范围'), select('calculationBase', '计算基数'), number('commissionRate', '提成比例'), dateRange('effectiveRange', '有效期'), select('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['规则信息', '比例阶梯/明细']
  }),
  defineBasicPage({
    title: '设备管理',
    key: 'equipment-management',
    description: '设备资产、位置与维护状态结构草案。',
    filters: [input('keyword', '设备名称/编号'), select('equipmentType', '设备类型'), select('store', '所属门店'), select('equipmentStatus', '设备状态')],
    columns: [text('equipmentNo', '设备编号'), text('equipmentName', '设备名称', 170), text('equipmentType', '设备类型'), text('store', '所属门店', 150), text('location', '存放位置'), dateColumn('purchaseDate', '购置日期'), dateColumn('nextMaintenanceDate', '下次维护日期'), status('equipmentStatus', '设备状态')],
    formFields: [input('equipmentNo', '设备编号'), input('equipmentName', '设备名称'), select('equipmentType', '设备类型'), input('brandModel', '品牌型号'), select('store', '所属门店'), input('location', '存放位置'), date('purchaseDate', '购置日期'), date('warrantyEndDate', '保修截止日期'), date('nextMaintenanceDate', '下次维护日期'), select('equipmentStatus', '设备状态'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '业绩目标设置',
    key: 'performance-target-settings',
    mode: 'settings',
    description: '组织或人员周期业绩目标结构草案。',
    filters: [select('targetPeriod', '目标周期'), select('store', '门店'), tree('organization', '组织/人员'), select('targetType', '目标类型')],
    columns: [text('targetPeriod', '目标周期'), text('store', '门店', 150), text('targetObject', '目标对象'), text('targetType', '目标类型'), money('targetAmount', '目标金额'), quantity('targetQuantity', '目标数量'), text('updatedBy', '设置人'), dateColumn('updatedAt', '设置时间')],
    formFields: [select('targetPeriod', '目标周期'), select('store', '门店'), tree('targetObject', '目标对象'), select('targetType', '目标类型'), number('targetAmount', '目标金额'), number('targetQuantity', '目标数量'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '优惠金额授权',
    key: 'discount-amount-authorization',
    mode: 'settings',
    description: '角色或人员优惠金额权限结构草案。',
    filters: [select('store', '门店'), tree('authorizedObject', '授权对象'), select('businessType', '业务类型'), select('enabled', '启用状态')],
    columns: [text('authorizedObject', '授权对象', 160), text('objectType', '对象类型'), text('store', '门店', 150), text('businessType', '业务类型'), money('singleLimit', '单笔优惠上限'), money('periodLimit', '周期优惠上限'), dateColumn('effectiveDate', '生效日期'), status()],
    formFields: [select('store', '门店'), tree('authorizedObject', '授权对象'), select('businessType', '业务类型'), number('singleLimit', '单笔优惠上限'), number('periodLimit', '周期优惠上限'), dateRange('effectiveRange', '有效期'), select('enabled', '启用状态'), textarea('remark', '备注')]
  }),
  defineBasicPage({
    title: '床位管理',
    key: 'bed-management',
    mode: 'tree-list',
    description: '房间内床位与可用状态结构草案。',
    filters: [select('store', '门店'), tree('room', '楼层/房间'), input('bedNo', '床位号'), select('bedStatus', '床位状态')],
    columns: [text('bedNo', '床位号'), text('roomNo', '房间号'), text('floor', '楼层'), text('store', '门店', 150), text('bedType', '床位类型'), text('occupantType', '适用对象'), status('bedStatus', '床位状态')],
    formFields: [select('store', '门店'), tree('room', '楼层/房间'), input('bedNo', '床位号'), select('bedType', '床位类型'), select('occupantType', '适用对象'), select('bedStatus', '床位状态'), textarea('remark', '备注')],
    structure: ['门店/楼层/房间树', '床位列表']
  })
]

export const BASIC_EXPECTED_MENU_COUNT = 19
export const BASIC_REPOSITORY_MENU_COUNT = basicDefinitions.length
export const basicMenuTitles = basicDefinitions.map(page => page.title)

export const basicPageConfigs = basicDefinitions.reduce((result, page) => {
  result[page.title] = page
  return result
}, {})

applyAuditedSurfaceEvidence('basic', basicPageConfigs)

export function getBasicPageConfig(title) {
  return basicPageConfigs[title] || {
    ...basicDefinitions[0],
    title,
    key: 'unverified-basic-page',
    description: '当前标题未进入基础资料证据清单，待原系统二次核验。',
    filters: [],
    columns: [],
    formFields: [],
    structure: []
  }
}
