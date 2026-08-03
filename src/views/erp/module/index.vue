<template>
  <div class="erp-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">{{ group }} · 业务工作台</div>
        <h1>{{ title }}</h1>
        <p>{{ pageDescription }}</p>
      </div>
      <div class="heading-actions">
        <el-button icon="el-icon-refresh" @click="refreshPage">刷新</el-button>
        <el-button type="primary" icon="el-icon-plus" @click="handleAdd">新增{{ shortTitle }}</el-button>
      </div>
    </div>

    <template v-if="pageType === 'customer-center'">
      <div class="metric-grid">
        <div v-for="metric in customerMetrics" :key="metric.label" class="metric-card">
          <span class="metric-dot" :style="{ background: metric.color }" />
          <div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div>
          <small>{{ metric.note }}</small>
        </div>
      </div>
      <el-card shadow="never" class="content-card pipeline-card">
        <div slot="header" class="card-title"><span>客户转化漏斗</span><el-tag size="small">当前</el-tag></div>
        <div class="pipeline">
          <div v-for="(stage, index) in pipeline" :key="stage.name" class="pipeline-step">
            <div class="pipeline-index">{{ index + 1 }}</div>
            <b>{{ stage.value }}</b><span>{{ stage.name }}</span>
          </div>
        </div>
      </el-card>
      <el-card shadow="never" class="content-card chain-card">
        <div slot="header" class="card-title"><span>客户 → 入住主链路</span><el-tag size="small" type="success" effect="plain">状态已建模</el-tag></div>
        <div class="business-chain">
          <div v-for="(stage, index) in primaryBusinessChain" :key="stage.key" class="chain-stage">
            <div class="chain-top"><i>{{ index + 1 }}</i><span>{{ stage.label }}</span><el-tag size="mini" :type="index < 2 ? 'success' : 'warning'">{{ stage.status }}</el-tag></div>
            <b>{{ stage.code }}</b>
            <small>{{ stage.required.slice(0, 3).join(' · ') }}</small>
          </div>
        </div>
      </el-card>
      <el-card shadow="never" class="content-card customer-record-card">
        <div slot="header" class="customer-record-header">
          <div class="customer-record-title">
            <b>客户档案</b>
            <span>全部客户，保存后自动入档</span>
          </div>
          <div class="customer-record-actions">
            <el-input v-model.trim="customerKeyword" size="small" clearable prefix-icon="el-icon-search" placeholder="搜索姓名、电话、来源或业务员" />
            <el-select v-model="customerStatusFilter" size="small" clearable placeholder="全部客户状态">
              <el-option v-for="status in customerStatusFilters" :key="status" :label="status" :value="status" />
            </el-select>
            <el-button size="small" icon="el-icon-download" @click="exportCustomers">导出</el-button>
          </div>
        </div>
        <el-table :data="visibleCustomerRows" stripe class="customer-record-table">
          <el-table-column type="index" label="#" width="52" />
          <el-table-column v-for="column in customerColumns" :key="column.prop" :prop="column.prop" :label="column.label" :min-width="column.width || 110">
            <template slot-scope="scope">
              <el-tag v-if="column.tag" :type="scope.row[column.prop] === '同意签合同' ? 'success' : scope.row[column.prop] === '意向A' ? 'warning' : ''" size="mini">{{ scope.row[column.prop] }}</el-tag>
              <span v-else>{{ scope.row[column.prop] }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" size="mini" @click="openRecord(scope.row)">查看</el-button>
              <el-button type="text" size="mini" @click="openRecord(scope.row)">编辑</el-button>
              <el-dropdown>
                <span class="more-link">更多<i class="el-icon-arrow-down" /></span>
                <el-dropdown-menu slot="dropdown">
                  <el-dropdown-item>打印</el-dropdown-item>
                  <el-dropdown-item>查看日志</el-dropdown-item>
                </el-dropdown-menu>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
        <div class="table-footer customer-record-footer">
          <span>共 {{ visibleCustomerRows.length }} 条记录</span>
          <span v-if="customerKeyword || customerStatusFilter">当前为筛选结果</span>
        </div>
      </el-card>
    </template>

    <template v-else-if="pageType === 'room-map'">
      <el-card shadow="never" class="content-card filter-card">
        <div class="room-legend">
          <div class="legend-filters">
            <el-select v-model="filters.store" class="small-control"><el-option label="中心广场旗舰店" value="中心广场旗舰店" /><el-option label="黄河路轻奢店" value="黄河路轻奢店" /></el-select>
            <el-date-picker v-model="filters.date" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" />
          </div>
          <div class="legend-items"><span v-for="item in roomLegend" :key="item.label"><i :style="{ background: item.color }" />{{ item.label }} {{ item.count }}</span></div>
        </div>
      </el-card>
      <div class="room-layout">
        <div v-for="floor in roomFloors" :key="floor.floor" class="floor-card">
          <div class="floor-title"><b>{{ floor.floor }}</b><span>{{ floor.rooms.length }} 间</span></div>
          <div class="room-grid">
            <div v-for="room in floor.rooms" :key="room.no" class="room-card" :class="`room-${room.status}`" @click="openRoom(room)">
              <div><b>{{ room.no }}</b><el-tag size="mini" effect="plain">{{ room.type }}</el-tag></div>
              <span>{{ room.label }}</span><small>{{ room.guest }}</small>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="pageType === 'nursing-center'">
      <div class="metric-grid compact">
        <div v-for="metric in nursingMetrics" :key="metric.label" class="metric-card">
          <span class="metric-icon" :style="{ color: metric.color, background: `${metric.color}18` }"><i :class="metric.icon" /></span>
          <div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div>
        </div>
      </div>
      <el-row :gutter="16">
        <el-col :lg="16" :xs="24"><record-table title="今日护理任务" :rows="nursingRows" :columns="nursingColumns" @action="openRecord" /></el-col>
        <el-col :lg="8" :xs="24">
          <el-card shadow="never" class="content-card schedule-card">
            <div slot="header" class="card-title"><span>护理动态</span><el-button type="text">查看全部</el-button></div>
            <div v-for="event in nursingEvents" :key="event.time + event.text" class="timeline-row"><b>{{ event.time }}</b><span><i />{{ event.text }}</span></div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <template v-else-if="pageType === 'meal-plan'">
      <el-card shadow="never" class="content-card meal-card">
        <div class="meal-toolbar"><el-date-picker v-model="filters.week" type="week" format="yyyy 第 WW 周" placeholder="选择周" /><el-select v-model="filters.store" class="small-control"><el-option label="中心广场旗舰店" value="中心广场旗舰店" /></el-select><el-button type="primary" plain>批量生成餐单</el-button></div>
        <div class="week-tabs"><button v-for="day in weekDays" :key="day.date" :class="{active: day.active}"><span>{{ day.week }}</span><b>{{ day.date }}</b></button></div>
        <div class="meal-grid">
          <div v-for="meal in mealPlan" :key="meal.type" class="meal-column"><h3>{{ meal.type }}<small>{{ meal.time }}</small></h3><div v-for="dish in meal.dishes" :key="dish" class="dish-row"><i class="el-icon-food" /><span>{{ dish }}</span><el-tag size="mini" type="success">已排</el-tag></div></div>
        </div>
      </el-card>
    </template>

    <template v-else-if="pageType === 'report'">
      <el-card shadow="never" class="content-card filter-card">
        <div class="filter-line"><el-select v-model="filters.store" class="small-control"><el-option label="全部门店" value="全部门店" /><el-option label="中心广场旗舰店" value="中心广场旗舰店" /></el-select><el-date-picker v-model="filters.range" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" /><el-button type="primary" icon="el-icon-search">查询</el-button><el-button icon="el-icon-download">导出</el-button></div>
      </el-card>
      <el-row :gutter="16">
        <el-col :lg="16" :xs="24"><el-card shadow="never" class="content-card chart-card"><div slot="header" class="card-title"><span>{{ title }}</span><el-radio-group v-model="chartMode" size="mini"><el-radio-button label="趋势" /><el-radio-button label="占比" /></el-radio-group></div><div class="fake-chart"><div class="chart-axis"><span>100%</span><span>75%</span><span>50%</span><span>25%</span><span>0</span></div><div v-for="bar in reportBars" :key="bar.label" class="chart-bar"><div :style="{height: bar.value + '%'}"><span>{{ bar.amount }}</span></div><small>{{ bar.label }}</small></div></div></el-card></el-col>
        <el-col :lg="8" :xs="24"><el-card shadow="never" class="content-card rank-card"><div slot="header" class="card-title"><span>关键指标</span><el-tag type="success" size="mini">实时</el-tag></div><div v-for="(rank,index) in reportRanks" :key="rank.name" class="rank-row"><i>{{ index + 1 }}</i><span>{{ rank.name }}</span><b>{{ rank.value }}</b></div></el-card></el-col>
      </el-row>
      <record-table title="数据明细" :rows="reportRows" :columns="reportColumns" @action="openRecord" />
    </template>

    <template v-else-if="pageType === 'form'">
      <el-card shadow="never" class="content-card form-card">
        <div slot="header" class="card-title"><span>{{ title }}</span><small>请按业务流程完整填写资料</small></div>
        <el-form ref="businessForm" :model="businessForm" label-width="110px" class="business-form">
          <div class="form-section"><h3>基本信息</h3><el-row :gutter="22"><el-col v-for="field in formFields.slice(0,6)" :key="field.key" :md="8" :xs="24"><el-form-item :label="field.label"><el-input v-model="businessForm[field.key]" :placeholder="`请输入${field.label}`" /></el-form-item></el-col></el-row></div>
          <div class="form-section"><h3>业务信息</h3><el-row :gutter="22"><el-col v-for="field in formFields.slice(6)" :key="field.key" :md="8" :xs="24"><el-form-item :label="field.label"><el-input v-model="businessForm[field.key]" :placeholder="`请输入${field.label}`" /></el-form-item></el-col></el-row><el-form-item label="备注"><el-input v-model="businessForm.remark" type="textarea" :rows="4" placeholder="补充说明" /></el-form-item></div>
          <div class="form-actions"><el-button>保存草稿</el-button><el-button type="primary" @click="saveForm">提交审核</el-button></div>
        </el-form>
      </el-card>
    </template>

    <template v-else-if="pageType === 'menu-tree'">
      <el-row :gutter="16">
        <el-col :lg="7" :xs="24"><el-card shadow="never" class="content-card tree-card"><div slot="header" class="card-title"><span>导航结构</span><el-button type="text">新增一级菜单</el-button></div><el-tree :data="menuTree" node-key="id" default-expand-all :expand-on-click-node="false" /></el-card></el-col>
        <el-col :lg="17" :xs="24"><el-card shadow="never" class="content-card form-card"><div slot="header" class="card-title"><span>菜单配置</span><el-tag size="mini">客户中心</el-tag></div><el-form label-width="100px"><el-form-item label="菜单名称"><el-input value="客户中心" /></el-form-item><el-form-item label="访问路径"><el-input value="/customer/item-1" /></el-form-item><el-form-item label="显示图标"><el-input value="peoples" /></el-form-item><el-form-item label="菜单状态"><el-switch :value="true" active-text="启用" /></el-form-item><el-form-item><el-button type="primary">保存配置</el-button><el-button>取消</el-button></el-form-item></el-form></el-card></el-col>
      </el-row>
    </template>

    <template v-else>
      <el-card shadow="never" class="content-card filter-card">
        <div class="filter-line"><el-input v-model="filters.keyword" clearable prefix-icon="el-icon-search" :placeholder="`搜索${title}关键词`" /><el-select v-model="filters.status" clearable placeholder="全部状态"><el-option label="全部状态" value="" /><el-option label="进行中" value="进行中" /><el-option label="已完成" value="已完成" /><el-option label="待审核" value="待审核" /></el-select><el-date-picker v-model="filters.range" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" /><el-button type="primary" icon="el-icon-search" @click="search">查询</el-button><el-button @click="resetFilters">重置</el-button></div>
      </el-card>
      <record-table :title="`${title}列表`" :rows="genericRows" :columns="genericColumns" @action="openRecord" />
    </template>

    <el-dialog :title="`${title}详情`" :visible.sync="dialogVisible" width="620px">
      <el-form label-width="96px"><el-row :gutter="18"><el-col :span="12"><el-form-item label="业务编号"><el-input v-model="dialogForm.code" /></el-form-item></el-col><el-col :span="12"><el-form-item label="当前状态"><el-select v-model="dialogForm.status" style="width:100%"><el-option label="进行中" value="进行中" /><el-option label="待审核" value="待审核" /><el-option label="已完成" value="已完成" /></el-select></el-form-item></el-col></el-row><el-form-item label="名称/对象"><el-input v-model="dialogForm.name" /></el-form-item><el-form-item label="负责人"><el-input v-model="dialogForm.owner" /></el-form-item><el-form-item label="备注"><el-input v-model="dialogForm.remark" type="textarea" :rows="4" /></el-form-item></el-form>
      <span slot="footer"><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="saveDialog">保存</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import { primaryBusinessChain } from '@/config/erp-workflows'
import { getCustomerModuleData } from '@/api/erp-customer'

const localCustomerSourceReplacements = {
  '客户中心测试-王女士': '抖音咨询',
  '客户中心测试-张女士': '客户介绍',
  '客户中心测试-李女士': '自然上门'
}

const RecordTable = {
  props: {
    title: String,
    subtitle: String,
    rows: Array,
    columns: Array,
    showAdd: { type: Boolean, default: true },
    showExport: { type: Boolean, default: true }
  },
  template: `<el-card shadow="never" class="content-card table-card"><div slot="header" class="card-title table-card-title"><span><b>{{ title }}</b><small v-if="subtitle">{{ subtitle }}</small></span><div><el-button v-if="showExport" size="mini" icon="el-icon-download" @click="$emit('export')">导出</el-button><el-button v-if="showAdd" size="mini" type="primary" icon="el-icon-plus" @click="$emit('add')">新增</el-button></div></div><slot name="toolbar" /><el-table :data="rows" stripe style="width:100%"><el-table-column type="index" label="#" width="52" /><el-table-column v-for="column in columns" :key="column.prop" :prop="column.prop" :label="column.label" :min-width="column.width || 110"><template slot-scope="scope"><el-tag v-if="column.tag" :type="scope.row[column.prop] === '同意签合同' ? 'success' : scope.row[column.prop] === '意向A' ? 'warning' : ''" size="mini">{{ scope.row[column.prop] }}</el-tag><span v-else>{{ scope.row[column.prop] }}</span></template></el-table-column><el-table-column label="操作" width="150" fixed="right"><template slot-scope="scope"><el-button type="text" size="mini" @click="$emit('action', scope.row)">查看</el-button><el-button type="text" size="mini" @click="$emit('action', scope.row)">编辑</el-button><el-dropdown><span class="more-link">更多<i class="el-icon-arrow-down" /></span><el-dropdown-menu slot="dropdown"><el-dropdown-item>打印</el-dropdown-item><el-dropdown-item>查看日志</el-dropdown-item></el-dropdown-menu></el-dropdown></template></el-table-column></el-table><div class="table-footer"><span>共 {{ rows.length }} 条记录</span></div></el-card>`
}

export default {
  name: 'ErpModulePage',
  components: { RecordTable },
  data() {
    return {
      filters: { keyword: '', status: '', store: '中心广场旗舰店', date: '2026-07-22', range: [], week: '' },
      chartMode: '趋势',
      dialogVisible: false,
      customerRecords: [],
      customerLoading: false,
      customerKeyword: '',
      customerStatusFilter: '',
      dialogForm: { code: 'ERP-20260722-001', name: '', owner: '当前用户', status: '进行中', remark: '' },
      businessForm: { name: '', mobile: '', source: '', dueDate: '', consultant: '', store: '', amount: '', payType: '', account: '', remark: '' }
    }
  },
  computed: {
    title() { return this.$route.meta.title || '业务管理' },
    group() { return this.$route.meta.group || 'ERP' },
    groupKey() { return this.$route.meta.groupKey || '' },
    pageType() { return this.$route.meta.pageType || 'list' },
    primaryBusinessChain() { return primaryBusinessChain },
    shortTitle() {
      if (this.pageType === 'customer-center') return '客户'
      return this.title.replace(/管理|列表|记录|报表/g, '') || '记录'
    },
    pageDescription() {
      const descriptions = { customer: '统一沉淀客户线索、跟进轨迹与签约状态', sales: '覆盖套餐、合同、商品与优惠的完整销售链路', finance: '贯通收款、退款、费用、发票与审核流程', room: '以房态为核心协调预订、入住与客房服务', nursing: '围绕母婴档案执行护理计划与健康评估', recovery: '管理产后康复预约、排班、执行与耗卡', matron: '管理月嫂档案、档期、派工、合同与结算', diet: '从营养方案到采购、制餐、送餐全程管理', warehouse: '连接采购、入库、领料、盘点与库存预警', report: '汇总经营关键指标，支持多维度查询与导出' }
      return descriptions[this.groupKey] || `维护${this.title}资料、状态及审批记录`
    },
    genericColumns() {
      const common = [{ prop: 'code', label: '业务编号', width: 150 }, { prop: 'name', label: this.groupKey === 'customer' ? '客户名称' : '业务对象', width: 150 }]
      const middle = this.groupKey === 'finance' ? [{ prop: 'amount', label: '金额（元）' }] : this.groupKey === 'warehouse' ? [{ prop: 'quantity', label: '数量' }] : [{ prop: 'type', label: '类型' }]
      return [...common, ...middle, { prop: 'owner', label: '负责人' }, { prop: 'date', label: '更新时间', width: 150 }, { prop: 'status', label: '状态', tag: true }]
    },
    genericRows() {
      const names = ['业务记录 01', '业务记录 02', '业务记录 03', '业务记录 04', '业务记录 05', '业务记录 06', '业务记录 07', '业务记录 08']
      return names.map((name, i) => ({ code: `${this.groupKey.toUpperCase() || 'ERP'}-${String(i + 1).padStart(4, '0')}`, name, type: this.title, owner: ['李顾问', '王主管', '张护士', '陈专员'][i % 4], date: `2026-07-${22 - i} 10:${String(i * 7).padStart(2, '0')}`, status: ['进行中', '待审核', '已完成'][i % 3], amount: `${(2680 + i * 760).toLocaleString()}.00`, quantity: 12 + i * 3 }))
    },
    formFields() {
      return [{ key: 'name', label: this.groupKey === 'finance' ? '客户名称' : '姓名/名称' }, { key: 'mobile', label: '联系电话' }, { key: 'source', label: '来源渠道' }, { key: 'dueDate', label: '预产日期' }, { key: 'consultant', label: '所属顾问' }, { key: 'store', label: '所属门店' }, { key: 'amount', label: '业务金额' }, { key: 'payType', label: '结算方式' }, { key: 'account', label: '资金账户' }]
    },
    customerMetrics() {
      const today = this.formatDate(new Date())
      const active = this.customerRecords.filter(item => !['流失客户', '散客客户'].includes(item.status))
      return [
        { label: '今日新增客户', value: this.customerRecords.filter(item => String(item.createdAt || '').startsWith(today)).length, note: '来自真实客户档案', color: '#B8945A' },
        { label: '当前有效客户', value: active.length, note: '不含流失与散客', color: '#8C6A36' },
        { label: '重点跟进', value: this.customerRows.length, note: '需优先联系', color: '#f5ba35' },
        { label: '同意签合同', value: this.customerRecords.filter(item => item.status === '同意签合同').length, note: '进入合同签订流程', color: '#45b8ac' }
      ]
    },
    pipeline() {
      const count = statuses => this.customerRecords.filter(item => statuses.includes(item.status)).length
      return [
        { name: '客户总数', value: this.customerRecords.length },
        { name: '高意向', value: count(['意向A', '意向B']) },
        { name: '持续跟进', value: count(['意向C', '意向D', '意向E']) },
        { name: '同意签合同', value: count(['同意签合同']) },
        { name: '散客客户', value: count(['散客客户']) },
        { name: '流失客户', value: count(['流失客户']) }
      ]
    },
    customerColumns() { return [{ prop: 'name', label: '客户姓名', width: 150 }, { prop: 'mobile', label: '联系电话', width: 135 }, { prop: 'source', label: '客户来源', width: 120 }, { prop: 'consultant', label: '所属业务员', width: 150 }, { prop: 'createdAt', label: '录入时间', width: 150 }, { prop: 'status', label: '客户状态', width: 110, tag: true }] },
    customerRows() {
      const priority = { '同意签合同': 0, '意向A': 1, '意向B': 2, '意向C': 3, '意向D': 4, '意向E': 5, '散客客户': 6, '流失客户': 7 }
      const rank = status => Object.prototype.hasOwnProperty.call(priority, status) ? priority[status] : 99
      return [...this.customerRecords]
        .sort((a, b) => rank(a.status) - rank(b.status) || String(b.createdAt || '').localeCompare(String(a.createdAt || '')))
        .slice(0, 3)
    },
    customerStatusFilters() {
      return ['意向A', '意向B', '意向C', '意向D', '意向E', '同意签合同', '散客客户', '流失客户']
    },
    visibleCustomerRows() {
      const keyword = this.customerKeyword.toLowerCase()
      return this.customerRecords.filter(item => {
        const matchesStatus = !this.customerStatusFilter || item.status === this.customerStatusFilter
        const searchable = [item.name, item.mobile, item.source, item.consultant].join(' ').toLowerCase()
        return matchesStatus && (!keyword || searchable.includes(keyword))
      })
    },
    roomLegend() { return [{ label: '在住', count: 21, color: '#45b8ac' }, { label: '预订', count: 9, color: '#6f8ff7' }, { label: '待清洁', count: 3, color: '#f5ba35' }, { label: '空闲', count: 2, color: '#dfe7ee' }, { label: '维修', count: 1, color: '#ef6b6b' }] },
    roomFloors() {
      const states = ['occupied', 'reserved', 'cleaning', 'empty', 'occupied', 'occupied']
      return ['三层', '四层', '五层'].map((floor, fi) => ({ floor, rooms: Array.from({ length: 8 }, (_, i) => { const status = states[(i + fi) % states.length]; return { no: `${fi + 3}0${i + 1}`, type: i % 3 === 0 ? 'VIP' : '标准', status, label: { occupied: '在住', reserved: '已预订', cleaning: '待清洁', empty: '空闲' }[status], guest: status === 'occupied' ? `入住第 ${i + 2} 天` : status === 'reserved' ? '07-25 入住' : '—' } }) }))
    },
    nursingMetrics() { return [{ label: '今日任务', value: 36, icon: 'el-icon-s-order', color: '#6f8ff7' }, { label: '待执行', value: 12, icon: 'el-icon-time', color: '#f5ba35' }, { label: '执行中', value: 7, icon: 'el-icon-loading', color: '#4f8cf7' }, { label: '已完成', value: 17, icon: 'el-icon-circle-check', color: '#45b8ac' }] },
    nursingColumns() { return [{ prop: 'time', label: '计划时间' }, { prop: 'room', label: '房间' }, { prop: 'project', label: '护理项目', width: 160 }, { prop: 'target', label: '服务对象' }, { prop: 'nurse', label: '执行护士' }, { prop: 'status', label: '状态', tag: true }] },
    nursingRows() { return ['08:30', '09:00', '09:30', '10:00', '10:30', '11:00'].map((time, i) => ({ time, room: `${3 + i % 3}0${i + 1}`, project: ['宝宝沐浴', '产妇伤口观察', '乳房护理', '宝宝抚触'][i % 4], target: i % 2 ? '宝宝' : '妈妈', nurse: ['张护士', '李护士', '王护士'][i % 3], status: ['已完成', '进行中', '待审核'][i % 3] })) },
    nursingEvents() { return [{ time: '10:20', text: '张护士完成 301 房宝宝沐浴' }, { time: '09:55', text: '新增 405 房健康评估任务' }, { time: '09:32', text: '李护士提交护理记录' }, { time: '08:48', text: '护理主管调整今日排班' }] },
    weekDays() { return [{ week: '周一', date: '07-20' }, { week: '周二', date: '07-21' }, { week: '周三', date: '07-22', active: true }, { week: '周四', date: '07-23' }, { week: '周五', date: '07-24' }, { week: '周六', date: '07-25' }, { week: '周日', date: '07-26' }] },
    mealPlan() { return [{ type: '早餐', time: '07:30', dishes: ['山药小米粥', '水蒸蛋', '清炒时蔬'] }, { type: '上午加餐', time: '10:00', dishes: ['银耳红枣羹', '时令水果'] }, { type: '午餐', time: '12:00', dishes: ['莲藕排骨汤', '清蒸鲈鱼', '杂粮饭'] }, { type: '下午加餐', time: '15:30', dishes: ['低糖酸奶', '坚果拼盘'] }, { type: '晚餐', time: '18:00', dishes: ['菌菇鸡汤', '西兰花牛肉', '软米饭'] }] },
    reportBars() { return [{ label: '1月', value: 45, amount: '12.6万' }, { label: '2月', value: 62, amount: '18.3万' }, { label: '3月', value: 55, amount: '16.8万' }, { label: '4月', value: 78, amount: '24.5万' }, { label: '5月', value: 69, amount: '21.2万' }, { label: '6月', value: 88, amount: '28.6万' }, { label: '7月', value: 73, amount: '23.4万' }] },
    reportRanks() { return [{ name: '合同总额', value: '¥ 326,800' }, { name: '回款总额', value: '¥ 248,500' }, { name: '入住率', value: '58.33%' }, { name: '新增客户', value: '42 人' }, { name: '客户满意度', value: '96.8%' }] },
    reportColumns() { return [{ prop: 'period', label: '统计周期' }, { prop: 'store', label: '门店' }, { prop: 'count', label: '业务量' }, { prop: 'amount', label: '金额' }, { prop: 'rate', label: '环比' }, { prop: 'status', label: '状态', tag: true }] },
    reportRows() { return ['2026-07', '2026-06', '2026-05', '2026-04', '2026-03'].map((period, i) => ({ period, store: i % 2 ? '黄河路轻奢店' : '中心广场旗舰店', count: 42 - i * 3, amount: `¥ ${(23.4 - i * 1.7).toFixed(1)} 万`, rate: `${i % 2 ? '-' : '+'}${3 + i}.2%`, status: i ? '已完成' : '进行中' })) },
    menuTree() { return [{ id: 1, label: '客户管理', children: [{ id: 11, label: '客户中心' }, { id: 12, label: '客户录入' }, { id: 13, label: '线索管理' }] }, { id: 2, label: '销售管理', children: [{ id: 21, label: '合同管理' }, { id: 22, label: '套餐管理' }] }, { id: 3, label: '系统设置', children: [{ id: 31, label: '用户管理' }, { id: 32, label: '角色管理' }] }] }
  },
  watch: {
    '$route.fullPath'() {
      if (this.pageType === 'customer-center') this.loadCustomerCenter()
    }
  },
  created() {
    if (this.pageType === 'customer-center') this.loadCustomerCenter()
  },
  methods: {
    formatDate(value) {
      const date = new Date(value)
      const pad = number => String(number).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    },
    async loadCustomerCenter() {
      this.customerLoading = true
      try {
        const response = await getCustomerModuleData('customers')
        this.customerRecords = (response.data.list || []).map(item => ({
          ...item,
          source: item.source === '本地数据库测试'
            ? (localCustomerSourceReplacements[item.name] || '客户介绍')
            : item.source,
          consultant: item.salesperson || '未分配',
          createdAt: item.createdAt ? String(item.createdAt).slice(0, 16) : '—'
        }))
      } finally {
        this.customerLoading = false
      }
    },
    handleAdd() {
      if (this.pageType === 'customer-center') {
        this.$router.push('/customer/item-2')
        return
      }
      this.dialogVisible = true
    },
    exportCustomers() {
      if (!this.visibleCustomerRows.length) {
        this.$message.warning('暂无可导出的客户数据')
        return
      }
      const headers = this.customerColumns.map(column => column.label)
      const escapeCell = value => `"${String(value === null || value === undefined ? '' : value).replace(/"/g, '""')}"`
      const lines = [
        headers.map(escapeCell).join(','),
        ...this.visibleCustomerRows.map(row => this.customerColumns.map(column => escapeCell(row[column.prop])).join(','))
      ]
      const blob = new Blob([`\uFEFF${lines.join('\r\n')}`], { type: 'text/csv;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `客户档案列表-${this.formatDate(new Date())}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      this.$message.success(`已导出 ${this.visibleCustomerRows.length} 条客户数据`)
    },
    search() { this.$message.success(`已更新${this.title}查询结果`) },
    resetFilters() { this.filters.keyword = ''; this.filters.status = ''; this.filters.range = [] },
    async refreshPage() {
      if (this.pageType === 'customer-center') await this.loadCustomerCenter()
      this.$message.success('数据已刷新')
    },
    openRecord(row) { this.dialogForm = { ...this.dialogForm, ...row }; this.dialogVisible = true },
    openRoom(room) { this.dialogForm = { ...this.dialogForm, code: `ROOM-${room.no}`, name: `${room.no} 房`, status: room.label }; this.dialogVisible = true },
    saveDialog() { this.dialogVisible = false; this.$message.success('保存成功') },
    saveForm() { this.$message.success('已提交审核') }
  }
}
</script>

<style lang="scss" scoped>
.erp-page { min-height: calc(100vh - 84px); padding: 24px; background: #f4f6f9; color: #253247; }
.page-heading { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-heading h1 { margin:5px 0 7px; font-size:25px; color:#1f2d3d; }
.page-heading p { margin:0; color:#8a96a8; font-size:13px; }
.eyebrow { color:#8c6a36; font-size:12px; font-weight:700; letter-spacing:1px; }
.heading-actions { display:flex; gap:8px; }
.content-card { border:0; border-radius:10px; margin-bottom:16px; box-shadow:0 2px 12px rgba(27,45,75,.055); }
.card-title { display:flex; align-items:center; justify-content:space-between; font-weight:700; color:#263445; }
.card-title small { margin-left:10px; color:#9aa5b4; font-weight:400; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:14px; }
.metric-card { position:relative; display:grid; grid-template-columns:auto auto minmax(90px,1fr); align-items:center; min-height:88px; padding:15px 18px; background:#fff; border:1px solid #eee7da; border-radius:10px; box-shadow:0 2px 10px rgba(27,45,75,.045); overflow:hidden; }
.metric-card:after { content:""; position:absolute; width:70px; height:70px; border-radius:50%; right:-24px; bottom:-30px; background:#f3f6f9; }
.metric-dot { width:7px; height:38px; border-radius:5px; margin-right:14px; }
.metric-card div { display:flex; flex-direction:column; }
.metric-card b { font-size:25px; line-height:1.1; }
.metric-card span { color:#7b8797; font-size:13px; margin-top:5px; }
.metric-card small { margin-left:14px; color:#9aa5b4; justify-self:end; text-align:right; }
.metric-icon { width:48px; height:48px; border-radius:12px; display:grid; place-items:center; margin-right:16px; font-size:22px; }
.pipeline { display:flex; padding:2px 10px 4px; }
.pipeline-step { flex:1; min-width:100px; position:relative; display:flex; flex-direction:column; align-items:center; }
.pipeline-step:not(:last-child):after { content:""; position:absolute; height:2px; top:17px; left:60%; right:-40%; background:#edf0f5; }
.pipeline-index { z-index:1; width:30px; height:30px; display:grid; place-items:center; color:#fff; border-radius:50%; background:linear-gradient(135deg,#d9bf8b,#8c6a36); box-shadow:0 8px 16px -12px rgba(111,84,43,.85); }
.pipeline-step b { font-size:19px; margin:7px 0 3px; }.pipeline-step span { color:#7f8b9c; font-size:13px; }
.business-chain { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; }.chain-stage { position:relative; padding:14px; border:1px solid #e7dfd2; border-radius:8px; background:#fffdf9; }.chain-stage:not(:last-child):after { content:""; position:absolute; right:-9px; top:31px; width:8px; height:8px; border-top:2px solid #c9aa70; border-right:2px solid #c9aa70; transform:rotate(45deg); z-index:1; }.chain-top { display:flex; align-items:center; gap:7px; }.chain-top>i { display:grid; place-items:center; width:22px; height:22px; border-radius:50%; color:#fff; background:#b8945a; font-size:11px; font-style:normal; }.chain-top>span { flex:1; font-weight:700; }.chain-stage>b,.chain-stage>small { display:block; }.chain-stage>b { margin:12px 0 6px; color:#425268; font-size:12px; }.chain-stage>small { min-height:32px; color:#8995a5; line-height:1.5; }
.table-card-title>span { display:flex; align-items:baseline; gap:12px; }
.table-card-title>span>b { font-size:15px; }
.table-card-title small { margin-left:0; }
.customer-record-card ::v-deep .el-card__header { padding:14px 18px; }
.customer-record-card ::v-deep .el-card__body { padding:0; }
.customer-record-header { display:flex; align-items:center; justify-content:space-between; gap:20px; }
.customer-record-title { display:flex; align-items:baseline; gap:12px; min-width:240px; }
.customer-record-title b { color:#263445; font-size:16px; }
.customer-record-title span { color:#96a0ae; font-size:12px; }
.customer-record-actions { display:flex; align-items:center; justify-content:flex-end; gap:9px; flex:1; }
.customer-record-actions .el-input { width:min(360px,34vw); }
.customer-record-actions .el-select { width:180px; }
.customer-record-table { width:100%; }
.customer-record-footer { padding:10px 18px; background:#fffdf9; }
.filter-line,.room-legend,.meal-toolbar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }.filter-line .el-input { width:240px; }.small-control { width:190px; }
.room-legend { justify-content:space-between; }.legend-filters,.legend-items { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }.legend-items span { color:#6f7b8c; font-size:13px; }.legend-items i { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:5px; }
.room-layout { display:flex; flex-direction:column; gap:14px; }.floor-card { padding:18px; background:#fff; border-radius:10px; box-shadow:0 2px 12px rgba(27,45,75,.055); }.floor-title { display:flex; justify-content:space-between; margin-bottom:14px; }.floor-title b { font-size:16px; }.floor-title span { color:#9aa5b4; font-size:12px; }.room-grid { display:grid; grid-template-columns:repeat(8,minmax(105px,1fr)); gap:10px; }.room-card { padding:12px; min-height:88px; border-radius:8px; border-left:4px solid #dfe7ee; background:#f8fafc; cursor:pointer; transition:.2s; }.room-card:hover { transform:translateY(-2px); box-shadow:0 6px 18px rgba(27,45,75,.1); }.room-card div { display:flex; justify-content:space-between; }.room-card>span,.room-card>small { display:block; margin-top:9px; color:#778397; }.room-card>small { font-size:11px; }.room-occupied { border-color:#45b8ac; background:#f2fbf9; }.room-reserved { border-color:#6f8ff7; background:#f4f6ff; }.room-cleaning { border-color:#f5ba35; background:#fffaf0; }.room-empty { border-color:#dfe7ee; }.room-maintenance { border-color:#ef6b6b; }
.schedule-card { min-height:440px; }.timeline-row { display:flex; gap:18px; padding:15px 0; border-bottom:1px solid #eee7da; }.timeline-row>b { color:#8d99a8; font-size:12px; }.timeline-row span { position:relative; color:#4b596c; }.timeline-row i { position:absolute; width:8px; height:8px; border-radius:50%; background:#b8945a; left:-13px; top:5px; }
.week-tabs { display:grid; grid-template-columns:repeat(7,1fr); gap:8px; margin:18px 0; }.week-tabs button { padding:12px; border:1px solid #e7dfd2; border-radius:8px; color:#7b8797; background:#fffdf9; cursor:pointer; }.week-tabs button span,.week-tabs button b { display:block; }.week-tabs button b { margin-top:4px; }.week-tabs button.active { color:#fff; border-color:#b8945a; background:linear-gradient(135deg,#d9bf8b,#8c6a36); }.meal-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }.meal-column { padding:15px; background:#f8f6f1; border-radius:9px; }.meal-column h3 { margin:0 0 14px; font-size:15px; }.meal-column h3 small { float:right; color:#99a4b2; }.dish-row { display:flex; align-items:center; gap:8px; padding:10px 0; border-top:1px solid #e7dfd2; font-size:13px; }.dish-row span { flex:1; }
.chart-card,.rank-card { min-height:410px; }.fake-chart { height:310px; display:flex; align-items:flex-end; gap:22px; padding:25px 20px 28px 55px; position:relative; background:repeating-linear-gradient(to top,#eee7da 0,#eee7da 1px,transparent 1px,transparent 62px); }.chart-axis { position:absolute; left:10px; top:15px; bottom:24px; display:flex; flex-direction:column; justify-content:space-between; color:#a1abba; font-size:11px; }.chart-bar { flex:1; height:100%; display:flex; align-items:center; justify-content:flex-end; flex-direction:column; }.chart-bar>div { width:58%; min-width:26px; background:linear-gradient(to top,#8c6a36,#d9bf8b); border-radius:7px 7px 0 0; position:relative; }.chart-bar>div span { position:absolute; top:-22px; left:50%; transform:translateX(-50%); white-space:nowrap; color:#5f6c7c; font-size:11px; }.chart-bar small { margin-top:9px; color:#7f8b9c; }.rank-row { display:flex; align-items:center; padding:16px 0; border-bottom:1px solid #eee7da; }.rank-row i { display:grid; place-items:center; width:25px; height:25px; border-radius:50%; background:#f6efdf; color:#8c6a36; font-style:normal; font-size:12px; }.rank-row:nth-child(-n+3) i { color:#fff; background:#b8945a; }.rank-row span { flex:1; margin-left:12px; color:#5e6b7b; }.rank-row b { color:#28384d; }
.form-section { padding:4px 0 16px; }.form-section+ .form-section { border-top:1px solid #edf0f4; padding-top:18px; }.form-section h3 { margin:0 0 20px; font-size:15px; padding-left:10px; border-left:3px solid #b8945a; }.form-actions { text-align:center; padding-top:10px; }.tree-card { min-height:560px; }
.table-footer { display:flex; justify-content:space-between; align-items:center; padding-top:18px; color:#8b96a6; font-size:12px; }.more-link { margin-left:10px; color:#409eff; font-size:12px; cursor:pointer; }
@media (max-width:1200px){.room-grid{grid-template-columns:repeat(4,1fr)}.meal-grid{grid-template-columns:repeat(2,1fr)}.business-chain{grid-template-columns:repeat(3,1fr)}}
@media (max-width:768px){.erp-page{padding:14px}.page-heading{align-items:flex-start;gap:14px}.heading-actions{display:none}.metric-grid{grid-template-columns:repeat(2,1fr)}.metric-card{display:flex;padding:14px}.metric-card small{display:none}.pipeline{overflow:auto}.business-chain{grid-template-columns:1fr}.chain-stage:not(:last-child):after{display:none}.table-card-title>span{align-items:flex-start;flex-direction:column;gap:4px}.customer-record-header{align-items:stretch;flex-direction:column;gap:10px}.customer-record-title{min-width:0}.customer-record-actions{align-items:stretch;flex-direction:column}.customer-record-actions .el-input,.customer-record-actions .el-select{width:100%}.room-grid{grid-template-columns:repeat(2,1fr)}.meal-grid{grid-template-columns:1fr}.week-tabs{overflow:auto;grid-template-columns:repeat(7,90px)}.filter-line .el-input,.small-control{width:100%}}
</style>
