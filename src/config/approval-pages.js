const approvalPageConfigs = {
  '审批中台': {
    featureId: 'F010',
    title: '审批中台',
    description: '统一承接合同、收款、退款及门店申请的审批待办；不复用收款管理页面。',
    statuses: ['待提交', '待处理', '已通过', '已驳回'],
    integrationStatus: '业务审批配置',
    queues: [
      { key: 'contract', title: '合同审批', icon: 'el-icon-document-checked', color: 'blue', source: '客户签约办理', fields: ['合同编号', '客户 / 门店', '套餐与成交金额'], action: '审核合同', description: '合同保存后生成审批申请，审核通过后才允许进入收款节点。' },
      { key: 'receipt', title: '收款确认', icon: 'el-icon-wallet', color: 'gold', source: '收款审核', fields: ['收款单号', '实收金额 / 方式', '收款门店'], action: '确认收款', description: '财务核对到账信息并留痕，不能由审批中台伪造到账结果。' },
      { key: 'refund', title: '退款与结算', icon: 'el-icon-refresh-left', color: 'rose', source: '退房 / 结算', fields: ['结算单号', '退款原因', '应退金额'], action: '审核退款', description: '退房结算完成后提交，须保留原收款、审批意见与操作人。' },
      { key: 'store', title: '门店申请', icon: 'el-icon-office-building', color: 'green', source: '门店运营', fields: ['申请单号', '申请门店', '申请事项'], action: '处理申请', description: '采购、调拨及门店事项按门店权限进入对应审批人待办。' }
    ],
    tracks: ['业务提交申请', '按门店与角色匹配审批人', '审批意见与结果留痕', '回写来源业务状态']
  },
  '审批流引擎': {
    featureId: 'F108',
    title: '审批流引擎',
    description: '维护行政与业务审批分类、节点、角色和启停状态；流程发布后生成版本，历史单据继续保留原版本。',
    statuses: ['草稿', '待发布', '已启用', '已停用'],
    integrationStatus: '审批流程配置',
    queues: [
      { key: 'business-flow', title: '业务审批流程', icon: 'el-icon-connection', color: 'blue', source: '合同 / 收款 / 退款', fields: ['流程分类', '适用门店', '审批节点'], action: '维护流程', description: '按业务类型配置节点和角色，不复用审批中台的待办列表。' },
      { key: 'admin-flow', title: '行政审批流程', icon: 'el-icon-office-building', color: 'gold', source: '人事 / 采购 / 门店', fields: ['流程分类', '发起角色', '审批角色'], action: '维护流程', description: '行政流程独立配置，并保留版本、生效时间和停用原因。' }
    ],
    tracks: ['新建流程草稿', '配置分类与节点', '校验角色和门店范围', '发布版本并保留审计记录']
  }
}

approvalPageConfigs['审批流引擎（行政+业务多分类）'] = approvalPageConfigs.审批流引擎

const fallbackConfig = {
  featureId: 'F010',
  title: '审批中台',
  description: '统一承接各业务域审批待办；不复用收款管理页面。',
  statuses: ['待提交', '待处理', '已通过', '已驳回'],
  integrationStatus: '业务审批配置',
  queues: [],
  tracks: []
}

export function getApprovalPageConfig(title) {
  return approvalPageConfigs[title] || fallbackConfig
}
