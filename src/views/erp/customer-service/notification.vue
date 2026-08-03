<template><service-workbench :definition="definition" /></template>

<script>
import ServiceWorkbench from './components/ServiceWorkbench'

export default {
  name: 'MessageNotificationCenter',
  components: { ServiceWorkbench },
  data() {
    return {
      definition: {
        featureCode: 'F084', priority: 'P2', title: '消息通知中心', createLabel: '新建通知', listTitle: '通知任务与发送记录',
        description: '统一管理站内通知、短信和微信消息；外部通道未配置时保留失败状态和操作记录。',
        integrationNotice: '站内消息可在本系统内完成发送；短信、微信必须先配置供应商通道，未配置时会返回失败并记录“待通道配置”。',
        searchPlaceholder: '搜索标题、接收人、手机号或编号', storeRequired: true,
        statuses: ['草稿', '待发送', '已发送', '待通道配置', '已取消'],
        columns: [{ prop: 'subject', label: '通知标题', width: 180 }, { prop: 'contactName', label: '接收人' }, { prop: 'channel', label: '发送渠道' }, { prop: 'status', label: '发送状态', tag: true }, { prop: 'externalStatusLabel', label: '通道状态' }],
        fields: [
          { key: 'subject', label: '通知标题', required: true, maxlength: 120 },
          { key: 'contactName', label: '接收人', required: true, maxlength: 64 },
          { key: 'mobile', label: '联系电话', maxlength: 11 },
          { key: 'channel', label: '发送渠道', type: 'select', required: true, options: ['站内消息', '短信', '微信'] },
          { key: 'category', label: '消息类型', type: 'select', required: true, options: ['服务提醒', '预约提醒', '缴费提醒', '护理通知', '系统通知'] },
          { key: 'priority', label: '优先级', type: 'select', options: ['普通', '重要', '紧急'] },
          { key: 'content', label: '通知内容', type: 'textarea', required: true, rows: 4 }
        ],
        actions: [
          { code: 'QUEUE', label: '提交发送', states: ['草稿'], type: 'primary' },
          { code: 'SEND', label: '执行发送', states: ['待发送', '待通道配置'], type: 'success' },
          { code: 'CANCEL', label: '取消通知', states: ['草稿', '待发送', '待通道配置'], type: 'danger', requiresNote: true }
        ],
        metrics: [
          { label: '草稿', statuses: ['草稿'], icon: 'el-icon-edit-outline', color: '#8B95A5', note: '待提交' },
          { label: '待发送', statuses: ['待发送'], icon: 'el-icon-time', color: '#E6A23C', note: '待执行' },
          { label: '已发送', statuses: ['已发送'], icon: 'el-icon-message', color: '#45B8AC', note: '站内/回执' },
          { label: '通道待配置', statuses: ['待通道配置'], icon: 'el-icon-warning-outline', color: '#D16F6F', note: '未发送' }
        ]
      }
    }
  }
}
</script>
