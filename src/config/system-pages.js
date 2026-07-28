const pendingOptions = ['待原系统二次核验']

const draftField = (key, label, type = 'input') => ({
  key,
  label,
  type,
  options: type === 'select' ? [...pendingOptions] : [],
  verified: false
})

const input = (key, label) => draftField(key, label)
const select = (key, label) => draftField(key, label, 'select')
const date = (key, label) => draftField(key, label, 'date')
const dateRange = (key, label) => draftField(key, label, 'dateRange')
const number = (key, label) => draftField(key, label, 'number')
const textarea = (key, label) => draftField(key, label, 'textarea')
const tree = (key, label) => draftField(key, label, 'tree')
const switchField = (key, label) => draftField(key, label, 'switch')

const draftColumn = (key, label, format = 'text', width = 120) => ({
  key,
  label,
  format,
  width,
  verified: false
})

const text = (key, label, width) => draftColumn(key, label, 'text', width)
const status = (key = 'status', label = '状态') => draftColumn(key, label, 'status', 100)
const dateColumn = (key, label) => draftColumn(key, label, 'date', 145)
const numberColumn = (key, label) => draftColumn(key, label, 'number', 110)

const originalPageEvidence = {
  部门管理: { url: 'sys/Departments.aspx?navid=13', navid: '13' },
  角色管理: { url: 'sys/RoleList.aspx?navid=11', navid: '11' },
  用户管理: { url: 'sys/Users.aspx?navid=12', navid: '12' },
  数据字典: { url: 'sys/datadic.aspx?navid=14', navid: '14' },
  审批流程: { url: 'sys/ApprovalProcess.aspx?navid=316', navid: '316' },
  通知公告: { url: 'OA/GongGao/GongGao.aspx?navid=290', navid: '290' },
  返利设置: { url: 'Page/BasicInfo/RebateSetting.aspx?navid=477', navid: '477' },
  会所介绍: { url: 'Page/BasicInfo/ClubIntroduce.aspx?navid=482', navid: '482' },
  导航菜单: { url: 'sys/NavigationList.aspx?navid=10', navid: '10' },
  移动端导航: { url: 'sys/NavigationListAPP.aspx?navid=674', navid: '674' },
  操作按钮: { url: 'sys/ButtonList.aspx?navid=2', navid: '2' },
  操作日志: { url: 'sys/logs.aspx?navid=15', navid: '15' },
  短信发送设置: { url: 'Page/BasicInfo/SetUserForMsm.aspx?navid=280', navid: '280' },
  生日短信提醒: { url: 'Page/BasicInfo/BrithdayRemind.aspx?navid=426', navid: '426' },
  消息发送日志: { url: 'Page/BasicInfo/MsgSendLog.aspx?navid=439', navid: '439' },
  预警参数设置: { url: 'Page/WarningManager/SetPrameter.aspx?navid=381', navid: '381' },
  报表模板自定义: { url: 'Page/BasicInfo/ReportTemplet.aspx?navid=446', navid: '446' },
  模板设置: { url: 'Page/BasicInfo/TemplateList.aspx?navid=672', navid: '672' },
  计划任务: { url: 'Page/BasicInfo/PlanTaskList.aspx?navid=673', navid: '673' },
  系统参数设置: { url: 'Page/WarningManager/SetSysPram.aspx?navid=384', navid: '384' }
}

const commonEvidence = {
  originalUrl: '',
  originalNavid: '',
  pageIdentityVerified: false,
  evidenceLevel: '内部字段待原系统二次核验',
  completionLevel: 'Visible',
  toolbarActions: [],
  queryActions: [],
  dependencies: [],
  evidenceNote: '菜单标题、顺序、原始 URL 和 navid 已核验；页面模式、字段、控件、选项、默认值、树层级、工具栏、表头、表单、权限和状态机均为结构草案，待原系统二次核验。'
}

const defineSystemPage = page => {
  const identity = originalPageEvidence[page.title] || {}
  return {
    mode: 'list',
    description: `${page.title}的可运行结构草案。`,
    filters: [],
    columns: [],
    formFields: [],
    structure: [],
    ...commonEvidence,
    ...page,
    originalUrl: identity.url || '',
    originalNavid: identity.navid || '',
    pageIdentityVerified: Boolean(identity.url && identity.navid)
  }
}

const systemDefinitions = [
  defineSystemPage({
    title: '部门管理',
    key: 'department-management',
    mode: 'tree-list',
    description: '部门、上级组织及门店归属结构草案。',
    filters: [input('keyword', '部门名称/编码'), tree('parentDepartment', '上级部门'), select('enabled', '启用状态')],
    columns: [text('departmentCode', '部门编码'), text('departmentName', '部门名称', 170), text('parentDepartment', '上级部门', 160), text('store', '所属门店', 150), text('manager', '负责人'), numberColumn('sortOrder', '排序'), status()],
    formFields: [tree('parentDepartment', '上级部门'), input('departmentCode', '部门编码'), input('departmentName', '部门名称'), select('store', '所属门店'), input('manager', '负责人'), number('sortOrder', '排序'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['组织树草案', '部门列表草案'],
    dependencies: ['上级部门 → 可选下级节点规则待原系统二次核验', '门店 → 部门归属范围待原系统二次核验']
  }),
  defineSystemPage({
    title: '角色管理',
    key: 'role-management',
    mode: 'permission-matrix',
    description: '角色档案、数据范围和菜单/按钮权限矩阵草案。',
    filters: [input('keyword', '角色名称/编码'), select('dataScope', '数据范围'), select('enabled', '启用状态')],
    columns: [text('roleCode', '角色编码'), text('roleName', '角色名称', 170), text('dataScope', '数据范围'), numberColumn('userCount', '用户数'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('roleCode', '角色编码'), input('roleName', '角色名称'), select('dataScope', '数据范围'), tree('organizationScope', '组织范围'), tree('menuPermissions', '菜单权限'), tree('buttonPermissions', '操作权限'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['角色列表草案', '组织数据范围树草案', '菜单权限树草案', '操作按钮权限树草案'],
    dependencies: ['数据范围 → 组织范围树启用规则待原系统二次核验', '菜单节点 → 操作按钮权限待原系统二次核验']
  }),
  defineSystemPage({
    title: '用户管理',
    key: 'user-management',
    mode: 'account-list',
    description: '用户账号、人员绑定、角色和组织归属结构草案。',
    filters: [input('keyword', '账号/姓名/手机号'), tree('organization', '组织机构'), select('role', '角色'), select('accountStatus', '账号状态')],
    columns: [text('account', '登录账号'), text('displayName', '用户姓名'), text('mobile', '手机号'), text('store', '所属门店', 150), text('department', '所属部门'), text('roles', '角色', 160), dateColumn('lastLoginAt', '最后登录时间'), status('accountStatus', '账号状态')],
    formFields: [input('account', '登录账号'), input('displayName', '用户姓名'), input('mobile', '手机号'), input('employee', '绑定职员'), select('store', '所属门店'), tree('department', '所属部门'), select('roles', '角色'), select('dataScope', '数据范围'), switchField('accountStatus', '账号状态'), textarea('remark', '备注')],
    structure: ['用户列表草案', '角色分配草案', '组织数据范围草案'],
    dependencies: ['所属门店 → 部门 → 绑定职员待原系统二次核验', '角色 → 数据权限待原系统二次核验']
  }),
  defineSystemPage({
    title: '数据字典',
    key: 'data-dictionary',
    mode: 'tree-list',
    description: '字典类型、字典项、排序与启用状态结构草案。',
    filters: [input('keyword', '字典名称/编码/字典项'), tree('dictionaryType', '字典类型'), select('enabled', '启用状态')],
    columns: [text('dictionaryCode', '字典编码'), text('dictionaryName', '字典名称', 170), text('itemValue', '字典值'), text('itemLabel', '显示名称'), numberColumn('sortOrder', '排序'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [tree('parentDictionary', '上级字典'), input('dictionaryCode', '字典编码'), input('dictionaryName', '字典名称'), input('itemValue', '字典值'), input('itemLabel', '显示名称'), number('sortOrder', '排序'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['字典类型树草案', '字典项列表草案'],
    dependencies: ['字典类型 → 字典项待原系统二次核验', '上级字典 → 可选子项待原系统二次核验']
  }),
  defineSystemPage({
    title: '审批流程',
    key: 'approval-workflow',
    mode: 'workflow',
    description: '审批业务、节点顺序、条件和处理人结构草案。',
    filters: [input('keyword', '流程名称/编码'), select('businessType', '业务类型'), select('enabled', '启用状态')],
    columns: [text('workflowCode', '流程编码'), text('workflowName', '流程名称', 180), text('businessType', '业务类型'), numberColumn('nodeCount', '节点数'), text('applicableScope', '适用范围'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('workflowCode', '流程编码'), input('workflowName', '流程名称'), select('businessType', '业务类型'), select('applicableScope', '适用范围'), tree('approverScope', '审批人范围'), textarea('conditionExpression', '节点条件'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['流程基本信息草案', '审批节点编排草案', '条件分支草案', '抄送/消息草案'],
    dependencies: ['业务类型 → 可配置流程节点待原系统二次核验', '节点条件 → 审批人/下一节点待原系统二次核验']
  }),
  defineSystemPage({
    title: '通知公告',
    key: 'notice-announcement',
    mode: 'content-list',
    description: '公告内容、发布范围与有效期结构草案。',
    filters: [input('keyword', '标题/发布人'), select('noticeType', '公告类型'), select('publishStatus', '发布状态'), dateRange('publishRange', '发布时间')],
    columns: [text('noticeTitle', '公告标题', 200), text('noticeType', '公告类型'), text('publishScope', '发布范围', 160), text('publisher', '发布人'), dateColumn('publishAt', '发布时间'), dateColumn('expireAt', '失效时间'), status('publishStatus', '发布状态')],
    formFields: [input('noticeTitle', '公告标题'), select('noticeType', '公告类型'), tree('publishScope', '发布范围'), textarea('noticeContent', '公告内容'), date('publishAt', '发布时间'), date('expireAt', '失效时间'), select('publishStatus', '发布状态'), textarea('remark', '备注')],
    structure: ['公告列表草案', '公告编辑器草案', '发布范围树草案']
  }),
  defineSystemPage({
    title: '返利设置',
    key: 'rebate-settings',
    mode: 'settings',
    description: '返利对象、计算规则、比例和有效期结构草案。',
    filters: [input('keyword', '规则名称/编码'), select('rebateType', '返利类型'), select('applicableScope', '适用范围'), select('enabled', '启用状态')],
    columns: [text('ruleCode', '规则编码'), text('ruleName', '规则名称', 180), text('rebateType', '返利类型'), text('applicableScope', '适用范围'), text('calculationRule', '计算规则', 170), text('rebateValue', '返利值'), dateColumn('effectiveDate', '生效日期'), status()],
    formFields: [input('ruleCode', '规则编码'), input('ruleName', '规则名称'), select('rebateType', '返利类型'), select('applicableScope', '适用范围'), select('calculationBase', '计算基数'), number('rebateValue', '返利值'), dateRange('effectiveRange', '有效期'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['规则信息草案', '返利阶梯/明细草案'],
    dependencies: ['返利类型 → 计算基数/数值控件待原系统二次核验', '适用范围 → 对象选择器待原系统二次核验']
  }),
  defineSystemPage({
    title: '会所介绍',
    key: 'club-introduction',
    mode: 'content-editor',
    description: '门店会所介绍、图文内容和发布状态结构草案。',
    filters: [select('store', '门店'), select('publishStatus', '发布状态')],
    columns: [text('store', '门店', 160), text('title', '标题', 190), text('cover', '封面'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status('publishStatus', '发布状态')],
    formFields: [select('store', '门店'), input('title', '标题'), input('cover', '封面附件'), textarea('summary', '摘要'), textarea('content', '介绍内容'), select('publishStatus', '发布状态')],
    structure: ['门店选择草案', '图文编辑器草案', '发布预览草案']
  }),
  defineSystemPage({
    title: '导航菜单',
    key: 'navigation-menu',
    mode: 'tree-list',
    description: '后台导航层级、路由与可见权限结构草案。',
    filters: [input('keyword', '菜单名称/编码/路由'), tree('parentMenu', '上级菜单'), select('enabled', '启用状态')],
    columns: [text('menuCode', '菜单编码'), text('menuName', '菜单名称', 170), text('parentMenu', '上级菜单'), text('routePath', '路由地址', 180), text('icon', '图标'), numberColumn('sortOrder', '排序'), status()],
    formFields: [tree('parentMenu', '上级菜单'), input('menuCode', '菜单编码'), input('menuName', '菜单名称'), input('routePath', '路由地址'), input('componentPath', '组件地址'), input('icon', '图标'), number('sortOrder', '排序'), switchField('visible', '是否显示'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['导航菜单树草案', '菜单详情草案', '关联操作权限草案'],
    dependencies: ['菜单类型 → 路由/组件字段待原系统二次核验', '父菜单 → 可用层级待原系统二次核验']
  }),
  defineSystemPage({
    title: '移动端导航',
    key: 'mobile-navigation',
    mode: 'tree-list',
    description: '移动端导航层级、入口与可见范围结构草案。',
    filters: [input('keyword', '导航名称/编码'), tree('parentNavigation', '上级导航'), select('clientType', '客户端类型'), select('enabled', '启用状态')],
    columns: [text('navigationCode', '导航编码'), text('navigationName', '导航名称', 170), text('parentNavigation', '上级导航'), text('clientType', '客户端类型'), text('target', '跳转目标', 180), numberColumn('sortOrder', '排序'), status()],
    formFields: [tree('parentNavigation', '上级导航'), input('navigationCode', '导航编码'), input('navigationName', '导航名称'), select('clientType', '客户端类型'), select('targetType', '跳转类型'), input('target', '跳转目标'), input('icon', '图标'), number('sortOrder', '排序'), switchField('visible', '是否显示'), switchField('enabled', '启用状态')],
    structure: ['移动端导航树草案', '导航详情草案'],
    dependencies: ['客户端类型 → 可用导航节点待原系统二次核验', '跳转类型 → 跳转目标控件待原系统二次核验']
  }),
  defineSystemPage({
    title: '操作按钮',
    key: 'operation-buttons',
    mode: 'permission-list',
    description: '页面操作、权限编码和菜单归属结构草案。',
    filters: [input('keyword', '按钮名称/权限编码'), tree('menu', '所属菜单'), select('enabled', '启用状态')],
    columns: [text('buttonCode', '按钮编码'), text('buttonName', '按钮名称', 150), text('permissionCode', '权限编码', 170), text('menu', '所属菜单', 160), text('buttonType', '按钮类型'), numberColumn('sortOrder', '排序'), status()],
    formFields: [tree('menu', '所属菜单'), input('buttonCode', '按钮编码'), input('buttonName', '按钮名称'), input('permissionCode', '权限编码'), select('buttonType', '按钮类型'), input('icon', '图标'), number('sortOrder', '排序'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['菜单树草案', '操作按钮列表草案'],
    dependencies: ['所属菜单 → 可用操作按钮待原系统二次核验', '按钮权限码 → 角色权限矩阵待原系统二次核验']
  }),
  defineSystemPage({
    title: '操作日志',
    key: 'operation-log',
    mode: 'audit-log',
    description: '用户操作审计、请求结果与异常信息结构草案。',
    filters: [input('keyword', '账号/姓名/操作内容'), tree('module', '业务模块'), select('operationType', '操作类型'), select('result', '执行结果'), dateRange('operationRange', '操作时间')],
    columns: [text('operator', '操作人'), text('account', '登录账号'), text('module', '业务模块'), text('operationType', '操作类型'), text('operationContent', '操作内容', 200), text('ipAddress', 'IP 地址'), dateColumn('operationAt', '操作时间'), status('result', '执行结果')],
    formFields: [input('operator', '操作人'), input('account', '登录账号'), input('module', '业务模块'), input('operationType', '操作类型'), textarea('operationContent', '操作内容'), input('ipAddress', 'IP 地址'), textarea('requestSummary', '请求摘要'), textarea('resultMessage', '结果信息')],
    structure: ['操作日志列表草案', '日志只读详情草案']
  }),
  defineSystemPage({
    title: '短信发送设置',
    key: 'sms-send-settings',
    mode: 'settings',
    description: '短信通道、签名、模板和发送策略结构草案。',
    filters: [input('keyword', '配置名称/签名'), select('channelType', '通道类型'), select('enabled', '启用状态')],
    columns: [text('configName', '配置名称', 170), text('channelType', '通道类型'), text('smsSignature', '短信签名'), text('provider', '服务商'), text('sender', '发送账号'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('configName', '配置名称'), select('channelType', '通道类型'), input('provider', '服务商'), input('smsSignature', '短信签名'), input('accessKey', '接口账号/密钥'), input('endpoint', '接口地址'), select('sendStrategy', '发送策略'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['短信通道配置草案', '短信模板关联草案', '发送策略草案'],
    dependencies: ['通道类型 → 接口参数待原系统二次核验', '短信模板 → 签名/变量待原系统二次核验']
  }),
  defineSystemPage({
    title: '生日短信提醒',
    key: 'birthday-sms-reminder',
    mode: 'settings',
    description: '生日提醒对象、模板、提前天数与发送时段结构草案。',
    filters: [input('keyword', '规则名称'), select('recipientType', '接收对象'), select('enabled', '启用状态')],
    columns: [text('ruleName', '规则名称', 170), text('recipientType', '接收对象'), text('smsTemplate', '短信模板', 170), numberColumn('advanceDays', '提前天数'), text('sendTime', '发送时间'), text('applicableScope', '适用范围'), status()],
    formFields: [input('ruleName', '规则名称'), select('recipientType', '接收对象'), select('smsTemplate', '短信模板'), number('advanceDays', '提前天数'), input('sendTime', '发送时间'), tree('applicableScope', '适用范围'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['生日提醒规则草案', '接收范围草案'],
    dependencies: ['接收对象 → 可用短信变量待原系统二次核验', '短信模板 → 签名/通道待原系统二次核验']
  }),
  defineSystemPage({
    title: '消息发送日志',
    key: 'message-send-log',
    mode: 'audit-log',
    description: '消息通道、接收人、发送结果与重试信息结构草案。',
    filters: [input('keyword', '接收人/手机号/消息标题'), select('messageType', '消息类型'), select('sendStatus', '发送状态'), dateRange('sendRange', '发送时间')],
    columns: [text('messageType', '消息类型'), text('recipient', '接收人'), text('recipientAddress', '接收地址', 150), text('messageTitle', '消息标题', 180), text('template', '消息模板'), dateColumn('sendAt', '发送时间'), numberColumn('retryCount', '重试次数'), status('sendStatus', '发送状态')],
    formFields: [input('messageType', '消息类型'), input('recipient', '接收人'), input('recipientAddress', '接收地址'), input('messageTitle', '消息标题'), textarea('messageContent', '消息内容'), input('template', '消息模板'), input('channel', '发送通道'), textarea('resultMessage', '结果信息')],
    structure: ['发送日志列表草案', '消息只读详情草案', '重试轨迹草案']
  }),
  defineSystemPage({
    title: '预警参数设置',
    key: 'warning-parameter-settings',
    mode: 'settings',
    description: '预警类型、阈值、通知对象和触发策略结构草案。',
    filters: [input('keyword', '参数名称/编码'), select('warningType', '预警类型'), select('enabled', '启用状态')],
    columns: [text('parameterCode', '参数编码'), text('parameterName', '参数名称', 180), text('warningType', '预警类型'), text('threshold', '预警阈值'), text('notificationScope', '通知范围', 160), text('triggerStrategy', '触发策略'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('parameterCode', '参数编码'), input('parameterName', '参数名称'), select('warningType', '预警类型'), select('comparisonRule', '比较规则'), number('threshold', '预警阈值'), input('unit', '单位'), tree('notificationScope', '通知范围'), select('triggerStrategy', '触发策略'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['预警参数列表草案', '通知对象草案'],
    dependencies: ['预警类型 → 阈值单位/比较规则待原系统二次核验', '触发策略 → 通知对象待原系统二次核验']
  }),
  defineSystemPage({
    title: '报表模板自定义',
    key: 'custom-report-template',
    mode: 'template-designer',
    description: '报表数据源、字段、分组、格式与权限结构草案。',
    filters: [input('keyword', '模板名称/编码'), select('reportType', '报表类型'), select('publishStatus', '发布状态')],
    columns: [text('templateCode', '模板编码'), text('templateName', '模板名称', 190), text('reportType', '报表类型'), text('dataSource', '数据源'), numberColumn('fieldCount', '字段数'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status('publishStatus', '发布状态')],
    formFields: [input('templateCode', '模板编码'), input('templateName', '模板名称'), select('reportType', '报表类型'), select('dataSource', '数据源'), tree('reportFields', '报表字段'), textarea('filterExpression', '筛选条件'), textarea('groupingRule', '分组/汇总规则'), tree('permissionScope', '查看权限'), select('publishStatus', '发布状态')],
    structure: ['模板基本信息草案', '字段设计器草案', '筛选/分组草案', '预览与权限草案'],
    dependencies: ['数据源 → 可用字段待原系统二次核验', '字段类型 → 格式/汇总方式待原系统二次核验']
  }),
  defineSystemPage({
    title: '模板设置',
    key: 'template-settings',
    mode: 'template',
    description: '通用业务模板分类、内容和适用范围结构草案。',
    filters: [input('keyword', '模板名称/编码'), select('templateType', '模板类型'), select('enabled', '启用状态')],
    columns: [text('templateCode', '模板编码'), text('templateName', '模板名称', 190), text('templateType', '模板类型'), text('applicableScope', '适用范围', 160), text('version', '版本'), text('updatedBy', '更新人'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [input('templateCode', '模板编码'), input('templateName', '模板名称'), select('templateType', '模板类型'), tree('applicableScope', '适用范围'), textarea('templateContent', '模板内容'), input('version', '版本'), switchField('enabled', '启用状态'), textarea('remark', '备注')],
    structure: ['模板分类草案', '模板内容编辑器草案', '变量/适用范围草案'],
    dependencies: ['模板类型 → 可用变量/编辑器待原系统二次核验', '适用范围 → 可用模板待原系统二次核验']
  }),
  defineSystemPage({
    title: '计划任务',
    key: 'scheduled-task',
    mode: 'scheduler',
    description: '定时任务、调度表达式、执行状态和日志结构草案。',
    filters: [input('keyword', '任务名称/编码'), select('taskType', '任务类型'), select('taskStatus', '任务状态'), dateRange('executionRange', '执行时间')],
    columns: [text('taskCode', '任务编码'), text('taskName', '任务名称', 180), text('taskType', '任务类型'), text('scheduleExpression', '调度表达式', 160), dateColumn('lastRunAt', '上次执行时间'), dateColumn('nextRunAt', '下次执行时间'), text('lastResult', '上次结果'), status('taskStatus', '任务状态')],
    formFields: [input('taskCode', '任务编码'), input('taskName', '任务名称'), select('taskType', '任务类型'), input('taskHandler', '任务处理器'), input('scheduleExpression', '调度表达式'), select('failureStrategy', '失败策略'), number('retryCount', '重试次数'), switchField('taskStatus', '任务状态'), textarea('parameter', '任务参数'), textarea('remark', '备注')],
    structure: ['任务列表草案', '调度配置草案', '执行日志草案'],
    dependencies: ['任务类型 → 处理器/参数待原系统二次核验', '失败策略 → 重试设置待原系统二次核验']
  }),
  defineSystemPage({
    title: '系统参数设置',
    key: 'system-parameter-settings',
    mode: 'settings',
    description: '系统参数分类、键值、数据类型和生效范围结构草案。',
    filters: [input('keyword', '参数名称/编码'), tree('parameterCategory', '参数分类'), select('enabled', '启用状态')],
    columns: [text('parameterCode', '参数编码'), text('parameterName', '参数名称', 180), text('parameterCategory', '参数分类'), text('parameterValue', '参数值', 160), text('dataType', '数据类型'), text('effectiveScope', '生效范围'), dateColumn('updatedAt', '更新时间'), status()],
    formFields: [tree('parameterCategory', '参数分类'), input('parameterCode', '参数编码'), input('parameterName', '参数名称'), select('dataType', '数据类型'), input('parameterValue', '参数值'), input('defaultValue', '默认值'), select('effectiveScope', '生效范围'), switchField('enabled', '启用状态'), textarea('description', '参数说明')],
    structure: ['参数分类树草案', '参数列表草案'],
    dependencies: ['数据类型 → 参数值控件/校验待原系统二次核验', '生效范围 → 组织/门店选择待原系统二次核验']
  })
]

export const SYSTEM_EXPECTED_MENU_COUNT = 20
export const SYSTEM_REPOSITORY_MENU_COUNT = systemDefinitions.length
export const systemMenuTitles = systemDefinitions.map(page => page.title)

export const systemPageConfigs = systemDefinitions.reduce((result, page) => {
  result[page.title] = page
  return result
}, {})

export function getSystemPageConfig(title) {
  return systemPageConfigs[title] || {
    ...systemDefinitions[0],
    title,
    key: 'unverified-system-page',
    description: '当前标题未进入系统设置菜单证据清单，待原系统二次核验。',
    filters: [],
    columns: [],
    formFields: [],
    structure: [],
    dependencies: []
  }
}
