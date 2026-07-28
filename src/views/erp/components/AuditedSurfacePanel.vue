<template>
  <div
    class="audited-surface-panel"
    :class="{ 'is-plain': plain }"
    :data-audited-title="config.title"
  >
    <el-alert
      v-if="!plain"
      :title="config.evidenceNote"
      type="success"
      :closable="false"
      show-icon
      class="surface-alert"
    />

    <el-card
      v-if="config.actions && config.actions.length"
      shadow="never"
      class="surface-card toolbar-card"
      data-audited-toolbar
    >
      <div v-if="!plain" slot="header" class="surface-heading">
        <div>
          <strong>顶部工具栏</strong>
          <span>标签、顺序与位置来自原 ERP 当前账号只读证据</span>
        </div>
        <el-tag size="mini" type="success">Schema-faithful</el-tag>
      </div>
      <div class="toolbar-actions">
        <el-button
          v-for="action in config.actions"
          :key="action"
          size="small"
          :icon="showActionIcons ? actionIcon(action) : undefined"
          :data-toolbar-action="action"
          :data-toolbar-icon="showActionIcons ? actionIcon(action) : undefined"
          @click="runBusinessAction(action)"
        ><span>{{ action }}</span></el-button>
      </div>
    </el-card>

    <el-card
      v-if="hasQuerySurface"
      shadow="never"
      class="surface-card query-card"
      data-audited-query
    >
      <div v-if="!plain" slot="header" class="surface-heading">
        <div>
          <strong>查询条件</strong>
          <span>字段顺序、控件、选项和默认值逐页独立</span>
        </div>
        <el-tag size="mini" type="success">已核验</el-tag>
      </div>
      <el-form :inline="true" :model="model" size="small" class="audited-query-form">
        <el-form-item
          v-for="field in config.filters"
          :key="field.key"
          :label="standaloneChoice(field) ? '' : field.label"
          :data-field="field.legacyId || field.key"
          :data-control-type="field.type"
        >
          <div
            v-if="field.type === 'choice-list'"
            class="legacy-choice-list"
            role="radiogroup"
            :aria-label="field.label"
          >
            <button
              v-for="option in field.options"
              :key="option"
              type="button"
              :class="{ active: model[field.key] === option }"
              :aria-checked="model[field.key] === option ? 'true' : 'false'"
              role="radio"
              @click="model[field.key] = option"
            >{{ option }}</button>
          </div>
          <el-select
            v-else-if="field.type === 'select'"
            v-model="model[field.key]"
            :disabled="field.disabled"
            :placeholder="field.label"
          >
            <el-option
              v-for="option in field.options"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="model[field.key]"
            type="date"
            value-format="yyyy-MM-dd"
            :readonly="field.readonly"
            :disabled="field.disabled"
            :placeholder="field.label"
          />
          <el-checkbox
            v-else-if="field.type === 'checkbox'"
            v-model="model[field.key]"
            :disabled="field.disabled"
          >{{ field.label }}</el-checkbox>
          <el-checkbox-group
            v-else-if="field.type === 'checkbox-group'"
            v-model="model[field.key]"
            :disabled="field.disabled"
          >
            <el-checkbox
              v-for="option in field.options"
              :key="option"
              :label="option"
            />
          </el-checkbox-group>
          <el-radio
            v-else-if="field.type === 'radio'"
            v-model="model[field.key]"
            :label="true"
            :disabled="field.disabled"
          >{{ field.label }}</el-radio>
          <el-radio-group
            v-else-if="field.type === 'radio-group'"
            v-model="model[field.key]"
            :disabled="field.disabled"
          >
            <el-radio
              v-for="option in field.options"
              :key="option"
              :label="option"
            />
          </el-radio-group>
          <el-input
            v-else
            v-model="model[field.key]"
            :readonly="field.readonly"
            :disabled="field.disabled"
            :placeholder="field.label"
          />
        </el-form-item>
        <el-form-item class="query-actions">
          <el-button
            v-for="action in config.queryActions"
            :key="action"
            :type="isPrimaryQuery(action) ? 'primary' : 'default'"
            :data-query-action="action"
            @click="runQueryAction(action)"
          ><span>{{ action }}</span></el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card
      v-if="!plain && !config.actions.length && !hasQuerySurface"
      shadow="never"
      class="surface-card empty-surface"
    >
      原页面当前未发现顶部工具栏或主查询控件；本地未添加通用刷新、查询、导出按钮。
    </el-card>
  </div>
</template>

<script>
import { initialAuditedFilters } from '@/config/audited-surface-adapter'

export default {
  name: 'AuditedSurfacePanel',
  props: {
    config: {
      type: Object,
      required: true
    },
    plain: {
      type: Boolean,
      default: false
    },
    showActionIcons: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      model: {}
    }
  },
  computed: {
    hasQuerySurface() {
      return Boolean(
        (this.config.filters && this.config.filters.length) ||
        (this.config.queryActions && this.config.queryActions.length)
      )
    }
  },
  watch: {
    'config.key': {
      immediate: true,
      handler() {
        this.resetModel()
      }
    }
  },
  methods: {
    resetModel() {
      this.model = initialAuditedFilters(this.config.filters || [])
    },
    isPrimaryQuery(action) {
      return /查询|搜索/.test(String(action).replace(/\s+/g, ''))
    },
    standaloneChoice(field) {
      return field.type === 'checkbox' || field.type === 'radio'
    },
    actionIcon(action) {
      const normalized = String(action || '').replace(/\s+/g, '')
      if (/添加|新增|开卡|添加排班|创建盘点单/.test(normalized)) return 'el-icon-plus'
      if (/编辑|修改|批量修改/.test(normalized)) return 'el-icon-edit'
      if (/删除|销卡/.test(normalized)) return 'el-icon-delete'
      if (/导出/.test(normalized)) return 'el-icon-download'
      if (/导入/.test(normalized)) return 'el-icon-upload2'
      if (/打印|二维码/.test(normalized)) return 'el-icon-printer'
      if (/设置/.test(normalized)) return 'el-icon-setting'
      if (/读卡|查看详情/.test(normalized)) return 'el-icon-search'
      if (/复制/.test(normalized)) return 'el-icon-document-copy'
      if (/预约|预产期|更改时间/.test(normalized)) return 'el-icon-date'
      if (/反审核|反结账|重置|撤回|回收|退单|退餐|退款|退货/.test(normalized)) return 'el-icon-refresh-left'
      if (/屏蔽|取消|停用|下架|退卡/.test(normalized)) return 'el-icon-circle-close'
      if (/是否启用/.test(normalized)) return 'el-icon-switch-button'
      if (/确认完成|完成服务|审核|提交|流程审批|核销|确认供应|确认签收|确认下单|确认接单|确认配送/.test(normalized)) return 'el-icon-circle-check'
      if (/启用|上架|开始服务|上户|下户/.test(normalized)) return 'el-icon-circle-check'
      if (/收款|充值|结算|星支付/.test(normalized)) return 'el-icon-money'
      if (/派工|分配|加到系统用户/.test(normalized)) return 'el-icon-user'
      if (/回复|医生建议/.test(normalized)) return 'el-icon-chat-dot-round'
      if (/推荐/.test(normalized)) return 'el-icon-star-on'
      if (/置顶/.test(normalized)) return 'el-icon-top'
      if (/移动/.test(normalized)) return 'el-icon-rank'
      if (/计划下达/.test(normalized)) return 'el-icon-s-promotion'
      if (/生成.+单/.test(normalized)) return 'el-icon-document-add'
      if (/出库|入库/.test(normalized)) return 'el-icon-box'
      if (/远程签约/.test(normalized)) return 'el-icon-monitor'
      if (/挂失/.test(normalized)) return 'el-icon-warning-outline'
      return 'el-icon-setting'
    },
    runBusinessAction(action) {
      this.$emit('business-action', action)
    },
    runQueryAction(action) {
      if (action === '重置') {
        this.resetModel()
        this.$message.success('已恢复查询默认值')
      }
      this.$emit('query-action', action, { ...this.model })
    }
  }
}
</script>

<style lang="scss" scoped>
.surface-alert,
.surface-card {
  margin-top: 16px;
}

.surface-card {
  border: 0;
  border-radius: 12px;
}

.is-plain {
  margin: 0;
  border: 1px solid #dfe4ea;
  background: #fff;
}

.is-plain .surface-card {
  margin: 0;
  border-radius: 0;
}

.is-plain .toolbar-card {
  border-bottom: 1px solid #e6e9ee;
}

.is-plain ::v-deep .el-card__body {
  padding: 12px 14px;
}

.is-plain .query-actions {
  padding-top: 24px;
}

.surface-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.surface-heading > div {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.surface-heading strong {
  color: #304057;
  font-size: 15px;
}

.surface-heading span,
.empty-surface {
  color: #7b899c;
  font-size: 12px;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-actions .el-button + .el-button {
  margin-left: 0;
}

.legacy-choice-list {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 32px;
  align-items: center;
}

.legacy-choice-list button {
  padding: 5px 11px;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  color: #606266;
  background: #fff;
  cursor: pointer;
}

.legacy-choice-list button:hover {
  color: #f45d91;
  border-color: #f7a5bf;
}

.legacy-choice-list button.active {
  color: #fff;
  border-color: #f45d91;
  background: #f45d91;
}

.toolbar-actions ::v-deep .el-button span,
.query-actions ::v-deep .el-button span {
  white-space: pre;
}

.audited-query-form ::v-deep .el-form-item {
  margin: 0 14px 12px 0;
  vertical-align: bottom;
}

.audited-query-form ::v-deep .el-form-item__label {
  display: block;
  float: none;
  padding: 0 0 4px;
  color: #5b6b80;
  font-size: 12px;
  line-height: 20px;
  text-align: left;
}

.audited-query-form ::v-deep .el-select,
.audited-query-form ::v-deep .el-date-editor,
.audited-query-form ::v-deep .el-input {
  width: 190px;
}

.audited-query-form ::v-deep .el-checkbox,
.audited-query-form ::v-deep .el-radio {
  min-width: 95px;
  line-height: 32px;
}

.query-actions {
  padding-top: 24px;
}

@media (max-width: 760px) {
  .surface-heading,
  .surface-heading > div {
    align-items: flex-start;
    flex-direction: column;
  }

  .audited-query-form ::v-deep .el-select,
  .audited-query-form ::v-deep .el-date-editor,
  .audited-query-form ::v-deep .el-input {
    width: 100%;
  }
}
</style>
