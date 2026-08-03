<template>
  <div class="approval-workbench">
    <section class="hero-panel">
      <div>
        <div class="eyebrow"><i class="el-icon-s-check" /> 审批中心 · {{ config.featureId }}</div>
        <h1>{{ config.title }}</h1>
        <p>{{ config.description }}</p>
      </div>
      <el-tag type="warning" effect="dark">{{ config.integrationStatus }}</el-tag>
    </section>

    <el-alert
      title="当前未接入审批聚合接口：本页不会回退为收款管理，也不会伪造审批成功。"
      type="warning"
      :closable="false"
      show-icon
    />

    <section class="metric-grid">
      <article v-for="queue in config.queues" :key="queue.key" class="metric-card" :class="queue.color">
        <i :class="queue.icon" /><div><span>{{ queue.title }}</span><strong>待接入</strong><small>{{ queue.source }}</small></div>
      </article>
    </section>

    <el-card shadow="never" class="content-card queue-card">
      <div slot="header" class="card-heading">
        <div><h2>审批待办队列</h2><p>按业务类型分道展示：每类申请都有独立来源、字段与审批动作，不使用一张通用业务表代替。</p></div>
        <el-tag type="info" effect="plain">当前暂无记录</el-tag>
      </div>
      <div class="queue-lanes">
        <article v-for="queue in config.queues" :key="queue.key" class="queue-lane" :class="queue.color">
          <div class="lane-title"><i :class="queue.icon" /><strong>{{ queue.title }}</strong><el-tag size="mini" type="info">0 待办</el-tag></div>
          <p>{{ queue.description }}</p>
          <dl><template v-for="field in queue.fields"><dt :key="`${queue.key}-${field}-label`">{{ field }}</dt><dd :key="`${queue.key}-${field}-value`">待接口回传</dd></template></dl>
          <el-button size="mini" plain @click="notifyPending(queue.action)">{{ queue.action }}</el-button>
        </article>
      </div>
    </el-card>

    <el-card shadow="never" class="content-card">
      <div slot="header" class="card-heading"><div><h2>审批轨迹</h2><p>审批聚合只接收来源业务的真实申请单，处理后回写来源状态并保留审计记录。</p></div></div>
      <div class="step-list">
        <div v-for="(step, index) in config.tracks" :key="step" class="step"><b>{{ index + 1 }}</b><div><strong>{{ step }}</strong><small>{{ trackNotes[index] }}</small></div></div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { getApprovalPageConfig } from '@/config/approval-pages'

export default {
  name: 'ApprovalWorkbench',
  computed: {
    pageTitle() { return this.$route.meta.configTitle || this.$route.meta.title.replace(/\s*★$/, '') },
    config() { return getApprovalPageConfig(this.pageTitle) },
    trackNotes() { return ['来源业务未提交申请时，审批中心不虚构待办。', '普通业务按发生门店隔离，审批人仅看到权限范围内的申请。', '审批结论、意见、操作人和时间需要完整留痕。', '只回写真实来源单据，不把审批页作为收款或合同的替代页面。'] }
  },
  methods: {
    notifyPending(action) { this.$message.info(`“${action}”需等待审批聚合接口与角色权限映射接入后执行。`) }
  }
}
</script>

<style lang="scss" scoped>
.approval-workbench { min-height: calc(100vh - 84px); padding: 22px; color: #26354c; background: #f3f6fa; }.hero-panel { display:flex; align-items:center; justify-content:space-between; gap:24px; padding:24px 28px; color:#fff; background:linear-gradient(125deg,#38455a,#677b96); border-radius:14px; }.eyebrow { margin-bottom:7px; color:#dce9f7; font-size:13px; font-weight:700; }.hero-panel h1 { margin:0 0 8px; font-size:27px; }.hero-panel p { margin:0; color:#f1f5f9; font-size:14px; }.approval-workbench > .el-alert { margin-top:14px; }.metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:14px; }.metric-card { display:flex; gap:11px; align-items:center; padding:17px; background:#fff; border:1px solid #e4eaf0; border-radius:10px; }.metric-card i { padding:10px; color:#4d6f94; background:#edf4fb; border-radius:9px; font-size:19px; }.metric-card.gold i { color:#9b7130; background:#fff5df; }.metric-card.rose i { color:#b95e6e; background:#fff0f2; }.metric-card.green i { color:#3e8a68; background:#eaf7f0; }.metric-card span,.metric-card strong,.metric-card small { display:block; }.metric-card span,.metric-card small { color:#758190; font-size:12px; }.metric-card strong { margin:4px 0; color:#3d5873; font-size:19px; }.content-card { margin-top:14px; border:0; border-radius:12px; }.card-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; }.card-heading h2 { margin:0 0 4px; font-size:16px; }.card-heading p { margin:0; color:#8894a1; font-size:12px; }.queue-lanes { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }.queue-lane { padding:14px; border:1px solid #dfe7ef; border-top:3px solid #5c7d9d; border-radius:10px; background:#fbfdff; }.queue-lane.gold { border-top-color:#bf913e; background:#fffdf8; }.queue-lane.rose { border-top-color:#c77883; background:#fffafa; }.queue-lane.green { border-top-color:#5a9b79; background:#fbfefc; }.lane-title { display:flex; align-items:center; gap:7px; }.lane-title i { color:#587895; }.lane-title strong { flex:1; }.queue-lane p { min-height:58px; margin:10px 0; color:#768391; font-size:12px; line-height:1.55; }.queue-lane dl { display:grid; grid-template-columns:1fr; margin:0 0 12px; }.queue-lane dt { margin-top:7px; color:#4f6276; font-size:12px; }.queue-lane dd { margin:3px 0 0; color:#a1abb6; font-size:12px; }.step-list { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }.step { display:flex; gap:10px; padding:14px; background:#f5f8fb; border-radius:9px; }.step b { display:inline-flex; align-items:center; justify-content:center; flex:0 0 25px; width:25px; height:25px; color:#fff; background:#5b7898; border-radius:50%; }.step strong,.step small { display:block; }.step small { margin-top:5px; color:#73808d; font-size:12px; line-height:1.55; } @media (max-width:1100px) { .metric-grid,.queue-lanes,.step-list { grid-template-columns:repeat(2,1fr); } } @media (max-width:700px) { .approval-workbench { padding:12px; }.hero-panel { align-items:flex-start; flex-direction:column; }.metric-grid,.queue-lanes,.step-list { grid-template-columns:1fr; } }
</style>
