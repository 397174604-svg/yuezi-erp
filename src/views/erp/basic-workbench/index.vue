<template>
  <div class="basic-workbench">
    <audited-surface-panel
      :config="config"
      plain
      show-action-icons
      @business-action="handleBusinessAction"
    />

    <el-card
      v-if="visibleGridHeaders.length"
      shadow="never"
      class="legacy-grid-card"
      data-basic-grid
    >
      <el-table
        :data="[]"
        border
        size="small"
        empty-text="无数据显示"
      >
        <el-table-column
          v-for="(label, index) in visibleGridHeaders"
          :key="`${label}-${index}`"
          :label="label"
          :min-width="columnWidth(label)"
          show-overflow-tooltip
        />
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getBasicPageConfig } from '@/config/basic-pages'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'

const hiddenTechnicalHeaders = new Set([
  'rownum',
  'id',
  'fid',
  'custfullname',
  'storeid',
  'fstoreid'
])

export default {
  name: 'BasicWorkbench',
  components: { AuditedSurfacePanel },
  computed: {
    pageTitle() {
      return this.$route.meta.title
    },
    config() {
      return getBasicPageConfig(this.pageTitle)
    },
    visibleGridHeaders() {
      return (this.config.auditedGridHeaders || []).filter(label => {
        const normalized = String(label || '').replace(/\s+/g, '').toLowerCase()
        return normalized && !hiddenTechnicalHeaders.has(normalized)
      })
    }
  },
  methods: {
    columnWidth(label) {
      if (/日期|时间|门店|内容|名称|备注/.test(label)) return 150
      return 110
    },
    handleBusinessAction(action) {
      if (/删除|停用|启用|确认|添加|编辑|设置|导入/.test(action)) {
        this.$message.info('请选择列表记录后执行该操作')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.basic-workbench {
  min-height: 100%;
  padding: 16px;
  background: #f3f5f7;
}

.legacy-grid-card {
  margin-top: 12px;
  border: 0;
  border-radius: 0;
}

.legacy-grid-card ::v-deep .el-card__body {
  padding: 0;
}

.legacy-grid-card ::v-deep .el-table th {
  color: #333;
  background: #f5f5f5;
}
</style>
