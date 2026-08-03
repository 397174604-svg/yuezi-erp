<template><service-workbench :definition="definition" /></template>

<script>
import ServiceWorkbench from './components/ServiceWorkbench'

export default {
  name: 'SmartCustomerSupport',
  components: { ServiceWorkbench },
  data() {
    return {
      definition: {
        featureCode: 'F094', priority: 'P2', title: '智能客服', createLabel: '新建客服会话', listTitle: '在线会话与工单',
        description: '承接客户咨询、人工回复和工单流转；AI 未配置时不生成虚假回复。',
        integrationNotice: '当前支持人工接单、回复、等待客户、转工单与关闭。AI 自动回复需要单独配置模型和知识检索服务。',
        searchPlaceholder: '搜索客户、手机号、咨询主题或编号', storeRequired: true,
        statuses: ['待接入', '处理中', '等待客户', '已转工单', '已关闭'],
        columns: [{ prop: 'contactName', label: '客户' }, { prop: 'channel', label: '咨询渠道' }, { prop: 'subject', label: '咨询主题', width: 180 }, { prop: 'priority', label: '优先级' }, { prop: 'status', label: '会话状态', tag: true }, { prop: 'assignedName', label: '客服' }],
        fields: [
          { key: 'subject', label: '咨询主题', required: true, maxlength: 120 },
          { key: 'contactName', label: '客户姓名', required: true, maxlength: 64 },
          { key: 'mobile', label: '联系电话', maxlength: 11 },
          { key: 'channel', label: '咨询渠道', type: 'select', required: true, options: ['网页客服', '电话', '微信', '现场咨询'] },
          { key: 'category', label: '问题分类', type: 'select', required: true, options: ['预约订房', '套餐价格', '护理服务', '膳食服务', '售后投诉', '其他'] },
          { key: 'priority', label: '优先级', type: 'select', options: ['普通', '重要', '紧急'] },
          { key: 'content', label: '客户问题', type: 'textarea', required: true, rows: 4 },
          { key: 'replyContent', label: '最近人工回复', type: 'textarea', rows: 3 }
        ],
        actions: [
          { code: 'ACCEPT', label: '人工接单', states: ['待接入'], type: 'primary' },
          { code: 'REPLY', label: '记录人工回复', states: ['处理中', '等待客户'], type: 'success', requiresNote: true, notePrompt: '请输入实际发送给客户的人工回复' },
          { code: 'WAIT', label: '等待客户', states: ['处理中'] },
          { code: 'TRANSFER', label: '转为工单', states: ['待接入', '处理中', '等待客户'], type: 'warning', requiresNote: true, notePrompt: '请输入转工单原因和处理部门' },
          { code: 'AI_REPLY', label: '尝试AI回复', states: ['处理中'], requiresNote: true, notePrompt: '请输入需要 AI 处理的问题' },
          { code: 'CLOSE', label: '关闭会话', states: ['处理中', '等待客户', '已转工单'], type: 'danger', requiresNote: true }
        ],
        metrics: [
          { label: '待接入', statuses: ['待接入'], icon: 'el-icon-chat-dot-round', color: '#B8945A', note: '待接单' },
          { label: '处理中', statuses: ['处理中'], icon: 'el-icon-service', color: '#E6A23C', note: '人工服务' },
          { label: '等待客户', statuses: ['等待客户'], icon: 'el-icon-time', color: '#6F8FF7', note: '待回复' },
          { label: '已闭环', statuses: ['已转工单', '已关闭'], icon: 'el-icon-circle-check', color: '#45B8AC', note: '已流转' }
        ]
      }
    }
  }
}
</script>
