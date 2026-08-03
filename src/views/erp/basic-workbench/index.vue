<template>
  <div class="basic-workbench">
    <audited-surface-panel
      :config="config"
      plain
      show-action-icons
      @query-action="handleQueryAction"
      @business-action="handleBusinessAction"
    />

    <el-card
      v-if="visibleColumns.length"
      shadow="never"
      class="legacy-grid-card"
      data-basic-grid
    >
      <el-table
        v-loading="loading"
        :data="filteredRows"
        border
        stripe
        size="small"
        :empty-text="emptyText"
      >
        <el-table-column
          v-for="column in visibleColumns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :min-width="column.width || columnWidth(column.label)"
          show-overflow-tooltip
        >
          <template slot-scope="scope">
            <el-tag
              v-if="column.format === 'status'"
              size="mini"
              :type="statusType(scope.row[column.key])"
            >{{ displayValue(scope.row[column.key], column) }}</el-tag>
            <span v-else>{{ displayValue(scope.row[column.key], column) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="grid-footer">
        <span>共 {{ filteredRows.length }} 条记录</span>
        <el-button size="mini" icon="el-icon-refresh" @click="loadData">刷新</el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
import { getBasicPageConfig } from '@/config/basic-pages'
import { getBasicModuleData } from '@/api/erp-basic'
import AuditedSurfacePanel from '@/views/erp/components/AuditedSurfacePanel'
import { mapGetters } from 'vuex'

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
  data() {
    return {
      rows: [],
      loading: false,
      loadError: '',
      appliedFilters: {}
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    pageTitle() {
      return this.$route.meta.configTitle || this.$route.meta.title
    },
    config() {
      return getBasicPageConfig(this.pageTitle)
    },
    visibleColumns() {
      const configured = (this.config.columns || []).filter(column => {
        const normalized = String(column.key || '').replace(/\s+/g, '').toLowerCase()
        return normalized && !hiddenTechnicalHeaders.has(normalized)
      })
      if (configured.length) return configured
      return (this.config.auditedGridHeaders || []).filter(label => {
        const normalized = String(label || '').replace(/\s+/g, '').toLowerCase()
        return normalized && !hiddenTechnicalHeaders.has(normalized)
      }).map((label, index) => ({ key: `legacy-${index}`, label }))
    },
    filteredRows() {
      const filters = Object.entries(this.appliedFilters).filter(([, value]) => {
        return value !== '' && value !== null && value !== undefined && (!Array.isArray(value) || value.length)
      })
      if (!filters.length) return this.rows
      return this.rows.filter(row => filters.every(([key, value]) => {
        const actual = row[key]
        if (Array.isArray(value)) return value.every(item => JSON.stringify(row).includes(String(item)))
        if (actual !== undefined && actual !== null) return String(actual).includes(String(value))
        return JSON.stringify(row).includes(String(value))
      }))
    },
    emptyText() {
      if (this.loadError) return this.loadError
      return `当前“${this.pageTitle}”暂无业务记录`
    }
  },
  watch: {
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.appliedFilters = {}
        this.loadData()
      }
    },
    currentStoreId() {
      this.loadData()
    }
  },
  methods: {
    columnWidth(label) {
      if (/日期|时间|门店|内容|名称|备注/.test(label)) return 150
      return 110
    },
    async loadData() {
      if (!this.config.key || this.config.key === 'unverified-basic-page') {
        this.rows = []
        this.loadError = '该基础资料尚未配置独立数据资源'
        return
      }
      this.loading = true
      this.loadError = ''
      try {
        const response = await getBasicModuleData(this.config.key, {
          storeId: this.currentStoreId || 'all'
        })
        const payload = response && response.data ? response.data : {}
        this.rows = Array.isArray(payload.list) ? payload.list : []
      } catch (error) {
        this.rows = []
        this.loadError = '数据加载失败，请刷新后重试'
      } finally {
        this.loading = false
      }
    },
    handleQueryAction(action, filters) {
      if (action === '重置') this.appliedFilters = {}
      else this.appliedFilters = { ...(filters || {}) }
    },
    handleBusinessAction(action) {
      if (/导出/.test(action)) {
        this.exportRows()
        return
      }
      if (/删除|停用|启用|确认|添加|编辑|设置|导入/.test(action)) {
        this.$message.info('请选择列表记录后执行该操作')
      }
    },
    exportRows() {
      if (!this.filteredRows.length) {
        this.$message.warning('当前没有可导出的业务记录')
        return
      }
      const columns = this.visibleColumns
      const quote = value => `"${String(value === null || value === undefined ? '' : value).replace(/"/g, '""')}"`
      const lines = [columns.map(column => quote(column.label)).join(',')]
      this.filteredRows.forEach(row => lines.push(columns.map(column => quote(row[column.key])).join(',')))
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${this.pageTitle}-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    },
    displayValue(value, column) {
      if (value === null || value === undefined || value === '') return '-'
      if (column.format === 'money') return `¥${Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
      return value
    },
    statusType(status) {
      if (/正常|启用|可用|在职|已完成/.test(String(status || ''))) return 'success'
      if (/停用|离职|异常|禁用/.test(String(status || ''))) return 'danger'
      return 'warning'
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

.grid-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  color: #7b8490;
  font-size: 12px;
}
</style>
