<template><service-workbench :definition="definition" /></template>

<script>
import ServiceWorkbench from './components/ServiceWorkbench'

export default {
  name: 'SatisfactionFollowUp',
  components: { ServiceWorkbench },
  data() {
    return {
      definition: {
        featureCode: 'F005', priority: 'P0', title: '满意度回访', createLabel: '新建回访任务', listTitle: '客户回访任务',
        description: '记录客户联系、满意度结果与问题升级过程，形成可追溯的回访闭环。',
        searchPlaceholder: '搜索客户、手机号、回访主题或编号', storeRequired: true,
        statuses: ['待回访', '跟进中', '已完成', '已升级'],
        columns: [{ prop: 'contactName', label: '客户', width: 110 }, { prop: 'mobile', label: '手机号', width: 125 }, { prop: 'category', label: '回访类型' }, { prop: 'score', label: '满意度' }, { prop: 'status', label: '状态', tag: true }, { prop: 'assignedName', label: '负责人' }],
        fields: [
          { key: 'subject', label: '回访主题', required: true, maxlength: 120 },
          { key: 'contactName', label: '客户姓名', required: true, maxlength: 64 },
          { key: 'mobile', label: '联系电话', maxlength: 11 },
          { key: 'category', label: '回访类型', type: 'select', required: true, options: ['入住回访', '服务回访', '离所回访', '投诉后回访'] },
          { key: 'priority', label: '优先级', type: 'select', options: ['普通', '重要', '紧急'] },
          { key: 'score', label: '满意度评分', type: 'number', min: 0, max: 100 },
          { key: 'content', label: '回访问题', type: 'textarea', required: true, rows: 3 },
          { key: 'result', label: '回访结果', type: 'textarea', rows: 3 }
        ],
        actions: [
          { code: 'START', label: '开始回访', states: ['待回访'], type: 'primary' },
          { code: 'COMPLETE', label: '完成回访', states: ['待回访', '跟进中'], type: 'success', requiresNote: true, notePrompt: '请输入本次回访结论' },
          { code: 'ESCALATE', label: '升级处理', states: ['待回访', '跟进中'], type: 'danger', requiresNote: true, notePrompt: '请输入需要升级的问题' },
          { code: 'REOPEN', label: '重新跟进', states: ['已完成', '已升级'], requiresNote: true }
        ],
        metrics: [
          { label: '待回访', statuses: ['待回访'], icon: 'el-icon-phone-outline', color: '#B8945A', note: '待联系' },
          { label: '跟进中', statuses: ['跟进中'], icon: 'el-icon-time', color: '#E6A23C', note: '处理中' },
          { label: '已完成', statuses: ['已完成'], icon: 'el-icon-circle-check', color: '#45B8AC', note: '已闭环' },
          { label: '已升级', statuses: ['已升级'], icon: 'el-icon-warning-outline', color: '#D16F6F', note: '需协同' }
        ]
      }
    }
  }
}
</script>
