<template><service-workbench :definition="definition" /></template>

<script>
import ServiceWorkbench from './components/ServiceWorkbench'

export default {
  name: 'AiKnowledgeBase',
  components: { ServiceWorkbench },
  data() {
    return {
      definition: {
        featureCode: 'F043', priority: 'P0', title: 'AI客服知识库', createLabel: '新建知识条目', listTitle: '知识条目',
        description: '维护经过审核的标准问答与适用场景；发布不代表外部 AI 模型已经接通。',
        integrationNotice: '当前仅完成知识内容管理与审核发布。AI 检索/生成服务需配置后才能调用，页面不会伪造模型回答。',
        searchPlaceholder: '搜索标题、分类、关键词或编号', storeRequired: false,
        statuses: ['草稿', '待审核', '已发布', '已停用'],
        columns: [{ prop: 'subject', label: '知识标题', width: 180 }, { prop: 'category', label: '分类' }, { prop: 'keywords', label: '关键词', width: 150 }, { prop: 'status', label: '发布状态', tag: true }, { prop: 'assignedName', label: '维护人' }],
        fields: [
          { key: 'subject', label: '知识标题', required: true, maxlength: 120 },
          { key: 'category', label: '知识分类', type: 'select', required: true, options: ['入住与订房', '套餐与价格', '护理服务', '膳食服务', '售后与投诉', '其他'] },
          { key: 'keywords', label: '检索关键词', required: true, placeholder: '多个关键词用顿号分隔', maxlength: 255 },
          { key: 'priority', label: '内容级别', type: 'select', options: ['普通', '重要', '敏感'] },
          { key: 'content', label: '标准答案', type: 'textarea', required: true, rows: 5 },
          { key: 'sourceReference', label: '依据/来源', type: 'textarea', required: true, rows: 2 }
        ],
        actions: [
          { code: 'SUBMIT', label: '提交审核', states: ['草稿'], type: 'primary' },
          { code: 'PUBLISH', label: '审核并发布', states: ['待审核'], type: 'success', requiresNote: true, notePrompt: '请输入审核意见' },
          { code: 'DISABLE', label: '停用', states: ['已发布'], type: 'danger', requiresNote: true, notePrompt: '请输入停用原因' },
          { code: 'REOPEN', label: '退回草稿', states: ['待审核', '已停用'], requiresNote: true }
        ],
        metrics: [
          { label: '草稿', statuses: ['草稿'], icon: 'el-icon-edit-outline', color: '#8B95A5', note: '待完善' },
          { label: '待审核', statuses: ['待审核'], icon: 'el-icon-view', color: '#E6A23C', note: '待复核' },
          { label: '已发布', statuses: ['已发布'], icon: 'el-icon-collection-tag', color: '#45B8AC', note: '可检索' },
          { label: '已停用', statuses: ['已停用'], icon: 'el-icon-circle-close', color: '#D16F6F', note: '不可用' }
        ]
      }
    }
  }
}
</script>
