<template>
  <div class="status-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">{{ feature.id }} · P0 运营、人事、报表与资产</div>
        <h1>{{ feature.title }}</h1>
        <p>本页说明当前可办理范围、开放条件与后续业务安排。</p>
      </div>
      <el-tag :type="tagType" effect="dark">{{ stateLabel }}</el-tag>
    </div>

    <el-alert
      v-if="feature.blocker"
      :title="feature.blocker"
      type="warning"
      :closable="false"
      show-icon
      class="blocker-alert"
    />

    <el-row :gutter="18">
      <el-col :lg="14" :xs="24">
        <el-card shadow="never" class="status-card">
          <div slot="header" class="card-title">当前可用范围</div>
          <p>{{ feature.scope }}</p>
          <el-button
            v-if="feature.relatedPath"
            type="primary"
            plain
            @click="$router.push(feature.relatedPath)"
          >{{ feature.relatedLabel || '打开关联页面' }}</el-button>
        </el-card>
      </el-col>
      <el-col :lg="10" :xs="24">
        <el-card shadow="never" class="status-card">
          <div slot="header" class="card-title">上线验收规则</div>
          <ul>
            <li>查询、新增、编辑与状态流转应保留完整业务记录。</li>
            <li>刷新后数据仍存在，并按账号权限和门店隔离。</li>
            <li>导出必须与当前筛选范围一致。</li>
            <li>短信、AI、微信、支付等外部服务未配置时保持待处理状态。</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { p0OperationsFeatures } from '@/config/p0-operations-features'

export default {
  name: 'P0OperationsStatus',
  computed: {
    feature() {
      const featureId = this.$route.meta.featureId
      return p0OperationsFeatures.find(item => item.id === featureId) || {
        id: featureId || 'P0',
        title: this.$route.meta.title || '功能状态',
        state: 'blocked',
        scope: '尚无可验收能力。',
        blocker: '功能配置不存在。'
      }
    },
    stateLabel() {
      return {
        real: '真实闭环',
        partial: '部分可用',
        external: '外部服务配置中',
        blocked: '业务规则确认中'
      }[this.feature.state] || '待核验'
    },
    tagType() {
      return {
        real: 'success',
        partial: 'warning',
        external: 'info',
        blocked: 'danger'
      }[this.feature.state] || 'info'
    }
  }
}
</script>

<style lang="scss" scoped>
.status-page {
  min-height: calc(100vh - 84px);
  padding: 24px;
  background: #f5f1e9;
  color: #2f2a24;
}
.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}
.page-heading h1 { margin: 6px 0 8px; font-size: 27px; }
.page-heading p { margin: 0; color: #807667; line-height: 1.7; }
.eyebrow { color: #9a753b; font-size: 12px; font-weight: 700; letter-spacing: .8px; }
.blocker-alert { margin-bottom: 18px; }
.status-card {
  min-height: 230px;
  border: 0;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(74, 58, 36, .07);
}
.status-card p { margin: 0 0 22px; line-height: 1.9; }
.card-title { font-weight: 700; }
ul { margin: 0; padding-left: 20px; color: #665e54; line-height: 2; }
@media (max-width: 640px) {
  .status-page { padding: 14px; }
  .page-heading { flex-direction: column; }
}
</style>
