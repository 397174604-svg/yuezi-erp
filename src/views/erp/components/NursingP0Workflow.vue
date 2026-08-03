<template>
  <el-card class="nursing-workflow" shadow="never">
    <template v-if="resource === 'health-assessments'">
      <div slot="header">产后恢复观察与跟进</div>
      <el-timeline>
        <el-timeline-item v-for="row in rows.slice(0, 6)" :key="row.recordId || row.id" :timestamp="row.assessmentDate || row.createdAt">
          <strong>{{ row.customerName || '未关联客户' }} · {{ row.target || '观察对象' }}</strong>
          <span class="workflow-tag">{{ row.assessmentType || '人工评估' }}</span>
          <p>{{ row.summary || row.content || '待护理人员记录观察内容。' }}</p>
          <small>跟进：{{ row.followUp || row.guidance || '待人工确认' }}</small>
        </el-timeline-item>
      </el-timeline>
    </template>
    <template v-else-if="resource === 'check-in-handover'">
      <div slot="header">入住物品清点与交接</div>
      <el-steps :active="handoverStep" finish-status="success" align-center>
        <el-step title="登记清单" />
        <el-step title="双方核对" />
        <el-step title="确认完成" />
      </el-steps>
      <el-table :data="rows.slice(0, 5)" size="mini" border @current-change="$emit('select', $event)">
        <el-table-column prop="customerName" label="客户" />
        <el-table-column prop="room" label="房间" width="90" />
        <el-table-column prop="items" label="物品清单" />
        <el-table-column prop="status" label="交接状态" width="110" />
      </el-table>
    </template>
    <template v-else>
      <div slot="header">当日护理任务</div>
      <div class="task-summary">
        <div v-for="item in taskMetrics" :key="item.label"><strong>{{ item.value }}</strong><span>{{ item.label }}</span></div>
      </div>
      <p class="workflow-note">看板只汇总当前门店任务；排班调整仍在排班工作台执行。</p>
    </template>
  </el-card>
</template>

<script>
export default {
  name: 'NursingP0Workflow',
  props: { resource: { type: String, default: '' }, rows: { type: Array, default: () => [] }},
  computed: {
    handoverStep() {
      if (this.rows.some(row => /完成|确认/.test(row.status || ''))) return 3
      if (this.rows.some(row => /核对|待确认/.test(row.status || ''))) return 2
      return 1
    },
    taskMetrics() {
      return [
        { label: '待执行', value: this.rows.filter(row => /待/.test(row.status || '')).length },
        { label: '执行中', value: this.rows.filter(row => /执行中/.test(row.status || '')).length },
        { label: '已完成', value: this.rows.filter(row => /完成/.test(row.status || '')).length }
      ]
    }
  }
}
</script>

<style lang="scss" scoped>
.nursing-workflow { margin-bottom: 14px; }
.workflow-tag { margin-left: 8px; color: #8f7cf6; font-size: 12px; }
.workflow-note, small { color: #7a8495; }
.task-summary { display: flex; gap: 12px; }
.task-summary div { flex: 1; padding: 12px; border-radius: 6px; background: #f7f5ff; }
.task-summary strong, .task-summary span { display: block; }
.task-summary strong { color: #6d57d6; font-size: 24px; }
.task-summary span { color: #7a8495; font-size: 12px; }
</style>
