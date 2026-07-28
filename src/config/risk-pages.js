import { applyOriginalEvidence } from './original-page-evidence'

const stores = ['中心广场旗舰店', '黄河路轻奢店']

const draftField = (key, label, type = 'input', options = []) => ({
  key,
  label,
  type,
  options,
  verified: false,
  evidence: 'ERP_MIGRATION.md 领域草案，待原系统二次核验'
})

const draftColumn = (key, label, width, format = '') => ({
  key,
  label,
  width,
  format,
  verified: false,
  evidence: 'ERP_MIGRATION.md 领域草案，待原系统二次核验'
})

export const riskPageConfigs = {
  悦禧风控: {
    key: 'yuexi-risk',
    mode: 'risk-draft',
    titleVerified: true,
    originalUrl: '',
    navid: '',
    evidenceLevel: '待原系统二次核验',
    completionLevel: 'Visible',
    evidenceNote: '仅“风控服务 → 悦禧风控”菜单名称来自本地菜单证据；页面 URL、布局、筛选、按钮、表格、枚举、弹窗和流程均未从原 ERP 核验。',
    domainDraft: '本地迁移文档将风控领域概括为“异常规则、风险事件和处置”，以下内容仅用于承载后续实证，不代表原系统页面结构。',
    stores,
    draftTabs: [
      {
        key: 'events',
        label: '风险事件草案',
        verified: false,
        filters: [
          draftField('keyword', '事件关键词'),
          draftField('sourceModule', '来源模块', 'select', ['客户', '合同', '财务', '客房', '护理', '产康', '膳食', '仓存']),
          draftField('store', '门店', 'select', stores),
          draftField('riskLevel', '风险等级', 'select', ['低', '中', '高']),
          draftField('status', '处置状态', 'select', ['待确认', '跟进中', '已关闭']),
          draftField('occurredRange', '发现时间', 'dateRange')
        ],
        columns: [
          draftColumn('riskNo', '风控编号', 150),
          draftColumn('sourceModule', '来源模块', 100),
          draftColumn('eventSummary', '风险摘要', 240),
          draftColumn('businessObject', '业务对象', 150),
          draftColumn('store', '门店', 150),
          draftColumn('riskLevel', '风险等级', 95, 'tag'),
          draftColumn('occurredAt', '发现时间', 155),
          draftColumn('owner', '跟进人', 100),
          draftColumn('status', '处置状态', 100, 'tag')
        ]
      },
      {
        key: 'dispositions',
        label: '处置跟进草案',
        verified: false,
        filters: [
          draftField('riskNo', '风控编号'),
          draftField('owner', '跟进人'),
          draftField('status', '处置状态', 'select', ['待确认', '跟进中', '已关闭']),
          draftField('handledRange', '跟进时间', 'dateRange')
        ],
        columns: [
          draftColumn('riskNo', '风控编号', 150),
          draftColumn('eventSummary', '风险摘要', 240),
          draftColumn('owner', '跟进人', 100),
          draftColumn('lastAction', '最近跟进', 220),
          draftColumn('nextActionAt', '下次跟进时间', 155),
          draftColumn('status', '处置状态', 100, 'tag'),
          draftColumn('updatedAt', '更新时间', 155)
        ]
      },
      {
        key: 'rules',
        label: '异常规则草案',
        verified: false,
        filters: [
          draftField('ruleName', '规则名称'),
          draftField('sourceModule', '来源模块', 'select', ['客户', '合同', '财务', '客房', '护理', '产康', '膳食', '仓存']),
          draftField('enabled', '启用状态', 'select', ['启用', '停用'])
        ],
        columns: [
          draftColumn('ruleCode', '规则编号', 140),
          draftColumn('ruleName', '规则名称', 220),
          draftColumn('sourceModule', '来源模块', 100),
          draftColumn('triggerSummary', '触发条件摘要', 260),
          draftColumn('riskLevel', '风险等级', 95, 'tag'),
          draftColumn('enabled', '启用状态', 95, 'tag'),
          draftColumn('updatedBy', '更新人', 100),
          draftColumn('updatedAt', '更新时间', 155)
        ]
      }
    ]
  }
}

applyOriginalEvidence('risk', riskPageConfigs)

export const riskMenuTitles = Object.keys(riskPageConfigs)

export function getRiskPageConfig(title) {
  return riskPageConfigs[title] || riskPageConfigs.悦禧风控
}
