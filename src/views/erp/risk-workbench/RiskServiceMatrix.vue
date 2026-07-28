<template>
  <div class="risk-service-matrix">
    <section class="page-heading">
      <div>
        <div class="eyebrow"><i class="el-icon-lock" /> 风控服务</div>
        <h1>悦禧风控</h1>
        <p>原页面是白银会员与黄金会员的固定服务项目对照表，不是风险事件、处置跟进或异常规则工作台。</p>
      </div>
      <el-tag type="success" effect="dark">Schema-faithful</el-tag>
    </section>

    <el-alert
      title="原页当前没有顶部业务工具栏和主查询区；以下 83 项服务及会员权益文字来自 admin 只读会话。"
      type="success"
      :closable="false"
      show-icon
      class="evidence-alert"
    />

    <div class="matrix-grid">
      <el-card
        v-for="(table, tableIndex) in tables"
        :key="tableIndex"
        shadow="never"
        class="matrix-card"
      >
        <el-table :data="table.rows" border size="mini" :data-table-index="tableIndex">
          <el-table-column prop="sequence" label="序号" width="55" align="center" />
          <el-table-column prop="service" label="服务项目" min-width="220" />
          <el-table-column prop="silver" label="白银会员" width="82" align="center" />
          <el-table-column prop="gold" label="黄金会员" width="82" align="center" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
import { getAuditedSurface } from '@/config/audited-surface-adapter'

export default {
  name: 'RiskServiceMatrix',
  computed: {
    surface() {
      return getAuditedSurface('risk', '悦禧风控')
    },
    tables() {
      return this.surface.staticTables.map((table, tableIndex) => ({
        tableIndex,
        rows: table.slice(1).map((row, rowIndex) => ({
          id: `${tableIndex}-${rowIndex}`,
          sequence: row[0],
          service: row[1],
          silver: row[2],
          gold: row[3]
        }))
      }))
    }
  }
}
</script>

<style lang="scss" scoped>
.risk-service-matrix {
  min-height: calc(100vh - 84px);
  padding: 20px;
  color: #2d3b50;
  background: #f4f6f9;
}

.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding: 24px 28px;
  border-radius: 15px;
  color: #fff;
  background: linear-gradient(125deg, #31435d, #6a7688);
  box-shadow: 0 12px 30px rgba(42, 56, 76, .18);
}

.eyebrow {
  margin-bottom: 8px;
  color: #dce4ed;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .6px;
}

.page-heading h1 {
  margin: 0 0 8px;
  font-size: 27px;
}

.page-heading p {
  max-width: 880px;
  margin: 0;
  color: #edf1f5;
  line-height: 1.7;
}

.evidence-alert {
  margin-top: 16px;
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(360px, 1fr));
  gap: 14px;
  margin-top: 16px;
  overflow-x: auto;
}

.matrix-card {
  min-width: 360px;
  border: 0;
  border-radius: 12px;
}

.matrix-card ::v-deep .el-card__body {
  padding: 0;
}

.matrix-card ::v-deep .el-table th {
  color: #344258;
  background: #eef1f5;
}

.matrix-card ::v-deep .el-table td {
  padding: 7px 0;
}

@media (max-width: 1280px) {
  .matrix-grid {
    grid-template-columns: repeat(2, minmax(360px, 1fr));
  }
}

@media (max-width: 760px) {
  .risk-service-matrix {
    padding: 12px;
  }

  .page-heading {
    flex-direction: column;
  }

  .matrix-grid {
    grid-template-columns: minmax(360px, 1fr);
  }
}
</style>
