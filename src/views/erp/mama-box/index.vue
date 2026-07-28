<template>
  <div class="mama-box-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">妈妈宝盒 · 运营后台</div>
        <h1>{{ title }}</h1>
        <p>{{ pageConfig.description }}</p>
      </div>
      <div class="heading-actions">
        <el-tag effect="plain">妈妈端同步</el-tag>
        <el-button icon="el-icon-refresh" @click="loadData">刷新</el-button>
        <el-button type="primary" icon="el-icon-plus" @click="openCreate">{{ pageConfig.primaryAction }}</el-button>
      </div>
    </div>

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.label" class="metric-card">
        <i :class="metric.icon" :style="{ color: metric.color, background: metric.color + '16' }" />
        <div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div>
        <small>{{ metric.note }}</small>
      </div>
    </div>

    <template v-if="pageType === 'mama-schedule'">
      <el-card v-loading="loading" shadow="never" class="content-card schedule-card">
        <div slot="header" class="schedule-header"><div><el-button-group><el-button size="small" icon="el-icon-arrow-left">上一周</el-button><el-button size="small">本周</el-button><el-button size="small">下一周<i class="el-icon-arrow-right el-icon--right" /></el-button></el-button-group><b>{{ schedule.start }} 至 {{ schedule.end }}</b></div><div><el-button size="small" icon="el-icon-plus" @click="openCreate">添加</el-button><el-button size="small" icon="el-icon-delete">删除</el-button><el-button size="small" icon="el-icon-rank">移动</el-button></div></div>
        <div class="schedule-grid">
          <div class="schedule-corner">时段</div><div v-for="day in schedule.days" :key="day" class="schedule-day">{{ day }}</div>
          <template v-for="row in schedule.rows">
            <div :key="row.period" class="period-cell">{{ row.period }}</div>
            <div v-for="(slot,index) in row.slots" :key="row.period + index" class="schedule-slot" :class="{ occupied: slot }" @dblclick="slot && openSchedule(slot, row.period, index)"><span v-if="slot">{{ slot }}</span><small v-if="slot">查看报名</small><i v-else class="el-icon-plus" @click="openCreate" /></div>
          </template>
        </div>
        <p class="schedule-tip"><i class="el-icon-info" /> 双击已排课程查看报名详情；课程可按周复制，也可拖动调整时段。</p>
      </el-card>
    </template>

    <template v-else-if="pageType === 'mama-categories'">
      <el-row v-loading="loading" :gutter="16">
        <el-col :lg="7" :xs="24"><el-card shadow="never" class="content-card category-tree"><div slot="header" class="card-title"><span>商城分类</span><el-button type="text" @click="openCreate">新增分类</el-button></div><el-tree :data="categoryTree" node-key="id" default-expand-all :expand-on-click-node="false" /></el-card></el-col>
        <el-col :lg="17" :xs="24"><el-card shadow="never" class="content-card"><div slot="header" class="card-title"><span>分类配置</span><small>分类同时用于商品筛选与妈妈端导航</small></div><el-table :data="categories" stripe><el-table-column prop="name" label="分类名称" min-width="130" /><el-table-column prop="parent" label="上级分类" min-width="120" /><el-table-column prop="sort" label="排序" width="80" /><el-table-column prop="products" label="商品/项目数" width="110" /><el-table-column label="状态" width="90"><template slot-scope="scope"><el-switch v-model="scope.row.status" active-value="启用" inactive-value="停用" /></template></el-table-column><el-table-column label="操作" width="120"><template slot-scope="scope"><el-button type="text" @click="openEdit(scope.row)">编辑</el-button><el-button type="text">子分类</el-button></template></el-table-column></el-table></el-card></el-col>
      </el-row>
    </template>

    <template v-else>
      <el-card shadow="never" class="content-card filter-card">
        <div class="filter-line">
          <el-input v-model="keyword" clearable prefix-icon="el-icon-search" :placeholder="`搜索${title}关键词`" />
          <el-select v-model="storeFilter" clearable placeholder="全部门店"><el-option label="中心广场旗舰店" value="中心广场旗舰店" /><el-option label="黄河路轻奢店" value="黄河路轻奢店" /><el-option label="全部门店" value="全部门店" /></el-select>
          <el-select v-model="statusFilter" clearable placeholder="全部状态"><el-option v-for="status in pageConfig.statuses" :key="status" :label="status" :value="status" /></el-select>
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
          <el-button type="primary" icon="el-icon-search">查询</el-button><el-button @click="resetFilters">重置</el-button>
        </div>
      </el-card>

      <el-card v-loading="loading" shadow="never" class="content-card">
        <div slot="header" class="card-title"><span>{{ title }}列表</span><div><el-button size="small" icon="el-icon-download">导出</el-button><el-button v-if="pageType === 'mama-orders'" size="small" type="primary">批量确认出库</el-button></div></div>
        <el-table :data="filteredRows" stripe>
          <el-table-column type="index" label="#" width="48" />
          <el-table-column v-for="column in pageConfig.columns" :key="column.prop" :prop="column.prop" :label="column.label" :min-width="column.width || 105" show-overflow-tooltip>
            <template slot-scope="scope">
              <el-tag v-if="column.tag" :type="tagType(scope.row[column.prop])" size="mini">{{ scope.row[column.prop] }}</el-tag>
              <el-rate v-else-if="column.score" :value="scope.row[column.prop]" disabled show-score text-color="#f5ba35" />
              <span v-else-if="column.money" class="money">¥ {{ scope.row[column.prop] }}</span>
              <span v-else>{{ scope.row[column.prop] }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" :width="pageConfig.actionWidth || 190" fixed="right">
            <template slot-scope="scope">
              <el-button v-for="action in rowActions(scope.row)" :key="action.key" type="text" size="mini" @click="handleRowAction(action.key, scope.row)">{{ action.label }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="table-footer"><span>共 {{ filteredRows.length }} 条演示记录</span><el-pagination background layout="prev, pager, next" :total="filteredRows.length" :page-size="10" /></div>
      </el-card>
    </template>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="680px">
      <template v-if="dialogMode === 'reply'">
        <div class="question-box"><b>用户内容</b><p>{{ activeRecord.question || activeRecord.content }}</p><small>{{ activeRecord.nickname || activeRecord.customer }} · {{ activeRecord.askedAt || activeRecord.createdAt }}</small></div>
        <el-form label-width="90px"><el-form-item label="回复内容"><el-input v-model="form.reply" type="textarea" :rows="6" placeholder="请输入正式、清晰的回复内容" /></el-form-item><el-form-item label="展示范围"><el-radio-group v-model="form.visibility"><el-radio label="公开" /><el-radio label="仅提问人" /></el-radio-group></el-form-item></el-form>
      </template>
      <template v-else-if="dialogMode === 'schedule'">
        <el-descriptions :column="2" border><el-descriptions-item label="课程">{{ activeRecord.name }}</el-descriptions-item><el-descriptions-item label="时段">{{ activeRecord.period }}</el-descriptions-item><el-descriptions-item label="日期">{{ activeRecord.day }}</el-descriptions-item><el-descriptions-item label="报名人数">12 人</el-descriptions-item></el-descriptions>
        <el-table :data="registrationRows" size="small" style="margin-top:16px"><el-table-column prop="name" label="报名用户" /><el-table-column prop="mobile" label="联系电话" /><el-table-column prop="status" label="签到状态" /></el-table>
      </template>
      <el-form v-else :model="form" label-width="100px">
        <el-row :gutter="18"><el-col :span="12"><el-form-item label="名称/标题"><el-input v-model="form.name" /></el-form-item></el-col><el-col :span="12"><el-form-item label="业务编码"><el-input v-model="form.code" /></el-form-item></el-col></el-row>
        <el-row :gutter="18"><el-col :span="12"><el-form-item label="所属门店"><el-select v-model="form.store" style="width:100%"><el-option label="中心广场旗舰店" value="中心广场旗舰店" /><el-option label="黄河路轻奢店" value="黄河路轻奢店" /><el-option label="全部门店" value="全部门店" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="类别"><el-input v-model="form.category" /></el-form-item></el-col></el-row>
        <el-row :gutter="18"><el-col :span="8"><el-form-item label="销售价"><el-input v-model="form.salePrice" /></el-form-item></el-col><el-col :span="8"><el-form-item label="积分价"><el-input v-model="form.pointPrice" /></el-form-item></el-col><el-col :span="8"><el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" :max="999" /></el-form-item></el-col></el-row>
        <el-form-item label="内容说明"><el-input v-model="form.description" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="妈妈端状态"><el-radio-group v-model="form.status"><el-radio label="已发布" /><el-radio label="草稿" /><el-radio label="已下架" /></el-radio-group></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="dialogVisible = false">关闭</el-button><el-button v-if="dialogMode !== 'schedule'" type="primary" :loading="saving" @click="saveRecord">保存并同步妈妈端</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import { getMamaBoxOverview, saveMamaBoxRecord, updateMamaBoxStatus } from '@/api/mama-box'

const pageConfigs = {
  'mama-products': { resource: 'products', description: '维护商城商品的门店、类别、规格、价格、积分、上架与推荐状态', primaryAction: '新增商品', statuses: ['已上架', '已下架'], columns: [{ prop: 'code', label: '商品编码', width: 130 }, { prop: 'name', label: '商品名称', width: 160 }, { prop: 'store', label: '门店', width: 150 }, { prop: 'category', label: '商品类别', width: 110 }, { prop: 'spec', label: '规格型号' }, { prop: 'unit', label: '单位', width: 60 }, { prop: 'originalPrice', label: '原价', money: true }, { prop: 'salePrice', label: '销售价', money: true }, { prop: 'pointPrice', label: '积分价' }, { prop: 'status', label: '上架状态', tag: true }, { prop: 'integral', label: '积分商品' }, { prop: 'recommended', label: '推荐' }] },
  'mama-orders': { resource: 'orders', description: '贯通下单、支付、优惠、欠款、配送或自提、出库与退货状态', primaryAction: '补录订单', statuses: ['未支付', '已支付', '部分支付', '待出库', '已出库', '退货', '已取消'], actionWidth: 220, columns: [{ prop: 'code', label: '销售单编号', width: 155 }, { prop: 'type', label: '销售类型' }, { prop: 'payMethod', label: '支付方式', width: 110 }, { prop: 'amount', label: '消费金额', money: true }, { prop: 'coupon', label: '优惠金额', money: true }, { prop: 'debt', label: '欠款金额', money: true }, { prop: 'orderedAt', label: '下单日期', width: 145 }, { prop: 'store', label: '销售分店', width: 150 }, { prop: 'customer', label: '客户' }, { prop: 'mobile', label: '手机号', width: 115 }, { prop: 'pickup', label: '取货方式' }, { prop: 'payStatus', label: '支付状态', tag: true }, { prop: 'stockStatus', label: '出库状态', tag: true }, { prop: 'status', label: '订单状态', tag: true }] },
  'mama-projects': { resource: 'projects', description: '维护妈妈端可购买服务项目的类别、门店、成本、售价、积分价与推荐位', primaryAction: '新增项目', statuses: ['已上架', '已下架'], columns: [{ prop: 'code', label: '项目编码', width: 125 }, { prop: 'name', label: '项目名称', width: 160 }, { prop: 'store', label: '门店', width: 150 }, { prop: 'category', label: '项目类别' }, { prop: 'unit', label: '单位', width: 65 }, { prop: 'costPrice', label: '进价', money: true }, { prop: 'salePrice', label: '销售价', money: true }, { prop: 'pointPrice', label: '积分价' }, { prop: 'status', label: '上架状态', tag: true }, { prop: 'integral', label: '积分项目' }, { prop: 'inStore', label: '店内销售' }, { prop: 'recommended', label: '推荐' }] },
  'mama-matrons': { resource: 'matrons', description: '管理妈妈端展示的月嫂、育儿嫂、催乳师等服务人员与预约状态', primaryAction: '新增人员', statuses: ['可预约', '服务中', '休假', '启用', '停用'], columns: [{ prop: 'code', label: '月嫂编号', width: 115 }, { prop: 'name', label: '姓名' }, { prop: 'store', label: '门店', width: 150 }, { prop: 'age', label: '年龄', width: 65 }, { prop: 'mobile', label: '联系方式', width: 115 }, { prop: 'jobType', label: '职业类型' }, { prop: 'level', label: '月嫂等级' }, { prop: 'standardFee', label: '标准费用', money: true }, { prop: 'serviceStatus', label: '服务状态', tag: true }, { prop: 'status', label: '启用状态', tag: true }] },
  'mama-categories': { resource: 'categories', description: '配置商品与服务项目分类，以及妈妈端商城导航顺序', primaryAction: '新增分类', statuses: ['启用', '停用'], columns: [] },
  'mama-parenting': { resource: 'parenting', description: '按新生儿、婴儿、幼儿和学龄前阶段发布育儿与护理内容', primaryAction: '发布内容', statuses: ['已发布', '草稿'], columns: [{ prop: 'title', label: '标题', width: 220 }, { prop: 'section', label: '内容栏目' }, { prop: 'stage', label: '成长阶段' }, { prop: 'contentType', label: '数据类型' }, { prop: 'author', label: '制单人' }, { prop: 'publishedAt', label: '制单日期', width: 145 }, { prop: 'pinned', label: '置顶' }, { prop: 'status', label: '发布状态', tag: true }] },
  'mama-questions': { resource: 'questions', description: '接收妈妈端提问，分派指定专家并跟踪回复与展示范围', primaryAction: '新增问答', statuses: ['待回复', '已回复'], actionWidth: 210, columns: [{ prop: 'question', label: '问题', width: 260 }, { prop: 'nickname', label: '客户昵称' }, { prop: 'mobile', label: '联系电话', width: 115 }, { prop: 'askedAt', label: '提问时间', width: 145 }, { prop: 'expert', label: '指定专家' }, { prop: 'replyStatus', label: '回复状态', tag: true }, { prop: 'visibility', label: '展示范围' }] },
  'mama-reviews': { resource: 'reviews', description: '审核妈妈端服务评语、图片及公开状态，形成口碑内容池', primaryAction: '新增评语', statuses: ['待审核', '已公开', '已隐藏'], columns: [{ prop: 'content', label: '妈妈评语', width: 280 }, { prop: 'nickname', label: '客户昵称' }, { prop: 'mobile', label: '联系电话', width: 115 }, { prop: 'images', label: '图片数' }, { prop: 'createdAt', label: '创建时间', width: 145 }, { prop: 'status', label: '公开状态', tag: true }] },
  'mama-community': { resource: 'community', description: '管理辣妈社区帖子、审核状态、置顶、推荐与浏览量', primaryAction: '发布帖子', statuses: ['正常', '待审核', '已隐藏'], actionWidth: 230, columns: [{ prop: 'content', label: '发帖内容', width: 260 }, { prop: 'nickname', label: '客户昵称' }, { prop: 'mobile', label: '联系电话', width: 115 }, { prop: 'postedAt', label: '发帖时间', width: 145 }, { prop: 'status', label: '帖子状态', tag: true }, { prop: 'pinned', label: '置顶' }, { prop: 'recommended', label: '推荐' }, { prop: 'views', label: '浏览量' }] },
  'mama-content': { resource: 'content', description: '维护会所简介、住所服务、轮播图、特色服务、Logo 与专家头图', primaryAction: '新增图文', statuses: ['已发布', '待发布'], columns: [{ prop: 'title', label: '标题', width: 220 }, { prop: 'type', label: '图文类别', width: 125 }, { prop: 'store', label: '门店', width: 150 }, { prop: 'author', label: '制单人' }, { prop: 'createdAt', label: '制单日期', width: 145 }, { prop: 'remark', label: '备注', width: 180 }, { prop: 'status', label: '发布状态', tag: true }] },
  'mama-comments': { resource: 'comments', description: '集中处理项目、物料和膳食评价及商品、包装、配送、服务评分', primaryAction: '新增回复', statuses: ['待回复', '已回复'], actionWidth: 190, columns: [{ prop: 'content', label: '评论内容', width: 230 }, { prop: 'type', label: '评论类型' }, { prop: 'target', label: '商品/项目名称', width: 180 }, { prop: 'productScore', label: '商品评价', score: true, width: 150 }, { prop: 'serviceScore', label: '服务评分', score: true, width: 150 }, { prop: 'customer', label: '评价客户' }, { prop: 'createdAt', label: '评价时间', width: 145 }, { prop: 'replyStatus', label: '回复状态', tag: true }] },
  'mama-classes': { resource: 'classes', description: '维护课程名称、地点、费用、活动对象、课程描述及关联基础项目', primaryAction: '新增课程', statuses: ['启用', '停用'], columns: [{ prop: 'name', label: '课程名称', width: 180 }, { prop: 'location', label: '地点', width: 180 }, { prop: 'fee', label: '费用' }, { prop: 'audience', label: '活动对象', width: 140 }, { prop: 'description', label: '课程描述', width: 220 }, { prop: 'baseProject', label: '基础项目', width: 130 }, { prop: 'registrations', label: '报名人数' }, { prop: 'status', label: '状态', tag: true }] },
  'mama-schedule': { resource: 'schedule', description: '按周维护上午、下午、晚上课程排班，并查看妈妈端报名详情', primaryAction: '添加排班', statuses: [], columns: [] }
}

export default {
  name: 'MamaBoxPage',
  data() {
    return {
      loading: false,
      saving: false,
      keyword: '',
      storeFilter: '',
      statusFilter: '',
      dateRange: [],
      products: [], orders: [], projects: [], matrons: [], categories: [], parenting: [], questions: [], reviews: [], community: [], content: [], comments: [], classes: [],
      schedule: { start: '', end: '', days: [], rows: [] },
      dialogVisible: false,
      dialogMode: 'edit',
      activeRecord: {},
      form: { name: '', code: '', store: '中心广场旗舰店', category: '', salePrice: '', pointPrice: '', sort: 10, description: '', status: '草稿', reply: '', visibility: '公开' },
      registrationRows: [{ name: '报名用户 A', mobile: '138****7102', status: '已签到' }, { name: '报名用户 B', mobile: '138****7265', status: '待签到' }, { name: '报名用户 C', mobile: '138****7381', status: '待签到' }]
    }
  },
  computed: {
    pageType() { return this.$route.meta.pageType },
    title() { return this.$route.meta.title },
    pageConfig() { return pageConfigs[this.pageType] || pageConfigs['mama-products'] },
    sourceRows() { return Array.isArray(this[this.pageConfig.resource]) ? this[this.pageConfig.resource] : [] },
    filteredRows() {
      const keyword = this.keyword.trim().toLowerCase()
      return this.sourceRows.filter(row => (!keyword || JSON.stringify(row).toLowerCase().includes(keyword)) && (!this.storeFilter || row.store === this.storeFilter) && (!this.statusFilter || Object.values(row).includes(this.statusFilter)))
    },
    metrics() {
      const allCount = this.sourceRows.length
      const pending = this.questions.filter(item => item.replyStatus === '待回复').length + this.reviews.filter(item => item.status === '待审核').length + this.community.filter(item => item.status === '待审核').length
      return [
        { label: '当前记录', value: this.pageType === 'mama-schedule' ? this.schedule.rows.reduce((sum, row) => sum + row.slots.filter(Boolean).length, 0) : allCount, note: '当前页面', icon: 'el-icon-document', color: '#4f8cf7' },
        { label: '待处理内容', value: pending, note: '问答 / 审核', icon: 'el-icon-bell', color: '#f5ba35' },
        { label: '在售商品项目', value: this.products.filter(item => item.status === '已上架').length + this.projects.filter(item => item.status === '已上架').length, note: '妈妈端可见', icon: 'el-icon-goods', color: '#45b8ac' },
        { label: '本周课堂报名', value: this.classes.reduce((sum, item) => sum + item.registrations, 0), note: '脱敏演示数据', icon: 'el-icon-date', color: '#ff6f9c' }
      ]
    },
    categoryTree() { return [{ id: 'root-1', label: '商城商品', children: this.categories.filter(item => item.parent === '商城商品').map(item => ({ id: item.id, label: `${item.name}（${item.products}）` })) }, { id: 'root-2', label: '服务项目', children: this.categories.filter(item => item.parent === '服务项目').map(item => ({ id: item.id, label: `${item.name}（${item.products}）` })) }] },
    dialogTitle() { return this.dialogMode === 'reply' ? '内容回复' : this.dialogMode === 'schedule' ? '课堂报名详情' : `${this.title}配置` }
  },
  watch: {
    '$route.path'() { this.dialogVisible = false }
  },
  created() { this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const { data } = await getMamaBoxOverview()
        Object.keys(data).forEach(key => { this[key] = data[key] })
      } finally { this.loading = false }
    },
    resetFilters() { this.keyword = ''; this.storeFilter = ''; this.statusFilter = ''; this.dateRange = [] },
    openCreate() {
      this.dialogMode = 'edit'; this.activeRecord = {}; this.form = { name: '', code: '', store: '中心广场旗舰店', category: '', salePrice: '', pointPrice: '', sort: 10, description: '', status: '草稿', reply: '', visibility: '公开' }; this.dialogVisible = true
    },
    openEdit(row) {
      this.dialogMode = 'edit'; this.activeRecord = row; this.form = { ...this.form, ...row, name: row.name || row.title || '', description: row.description || row.content || '' }; this.dialogVisible = true
    },
    openSchedule(name, period, index) {
      this.dialogMode = 'schedule'; this.activeRecord = { name, period, day: this.schedule.days[index] }; this.dialogVisible = true
    },
    rowActions(row) {
      if (['mama-questions', 'mama-comments'].includes(this.pageType)) return [{ key: 'reply', label: row.replyStatus === '已回复' ? '查看回复' : '回复' }, { key: 'edit', label: '编辑' }, { key: 'hide', label: '隐藏' }]
      if (this.pageType === 'mama-community') return [{ key: 'audit', label: row.status === '待审核' ? '审核' : '查看' }, { key: 'top', label: row.pinned === '是' ? '取消置顶' : '置顶' }, { key: 'recommend', label: row.recommended === '是' ? '取消推荐' : '推荐' }]
      if (this.pageType === 'mama-orders') return [{ key: 'detail', label: '详情' }, { key: 'stock', label: row.stockStatus === '已出库' ? '查看出库' : '确认出库' }, { key: 'cancel', label: '取消' }]
      if (['mama-parenting', 'mama-content', 'mama-reviews'].includes(this.pageType)) return [{ key: 'edit', label: '编辑' }, { key: 'publish', label: '发布/审核' }, { key: 'preview', label: '预览' }]
      return [{ key: 'edit', label: '编辑' }, { key: 'publish', label: '上架/下架' }, { key: 'recommend', label: '推荐' }]
    },
    async handleRowAction(action, row) {
      if (action === 'edit' || action === 'detail' || action === 'audit' || action === 'preview') { this.openEdit(row); return }
      if (action === 'reply') { this.dialogMode = 'reply'; this.activeRecord = row; this.form.reply = ''; this.form.visibility = '公开'; this.dialogVisible = true; return }
      if (action === 'top') row.pinned = row.pinned === '是' ? '否' : '是'
      if (action === 'recommend') row.recommended = row.recommended === '是' ? '否' : '是'
      if (action === 'publish') row.status = ['已上架', '已发布', '已公开'].includes(row.status) ? '已下架' : this.pageType === 'mama-reviews' ? '已公开' : this.pageType.includes('products') || this.pageType.includes('projects') ? '已上架' : '已发布'
      if (action === 'stock') row.stockStatus = '已出库'
      if (action === 'cancel') row.status = '已取消'
      await updateMamaBoxStatus(this.pageConfig.resource, row.id, action)
      this.$message.success('状态已更新并同步妈妈端（模拟接口）')
    },
    async saveRecord() {
      this.saving = true
      try {
        await saveMamaBoxRecord(this.pageConfig.resource, this.dialogMode === 'reply' ? { id: this.activeRecord.id, reply: this.form.reply, visibility: this.form.visibility } : this.form)
        if (this.dialogMode === 'reply') this.activeRecord.replyStatus = '已回复'
        this.dialogVisible = false
        this.$message.success('保存成功并进入妈妈端同步队列（模拟接口）')
      } finally { this.saving = false }
    },
    tagType(value) {
      if (['已上架', '已支付', '已出库', '已发布', '已公开', '已回复', '启用', '正常', '可预约'].includes(value)) return 'success'
      if (['待审核', '待回复', '部分支付', '待出库', '待发布', '服务中'].includes(value)) return 'warning'
      if (['已下架', '停用', '已取消', '休假'].includes(value)) return 'info'
      return ''
    }
  }
}
</script>

<style lang="scss" scoped>
.mama-box-page { min-height:calc(100vh - 84px); padding:24px; background:#f4f6f9; color:#253247; }.page-heading { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }.page-heading h1 { margin:5px 0 7px; font-size:25px; }.page-heading p { margin:0; color:#8a96a8; font-size:13px; }.eyebrow { color:#ff6f9c; font-size:12px; font-weight:700; letter-spacing:1px; }.heading-actions { display:flex; align-items:center; gap:8px; }
.content-card { border:0; border-radius:10px; margin-bottom:16px; box-shadow:0 2px 12px rgba(27,45,75,.055); }.card-title { display:flex; align-items:center; justify-content:space-between; font-weight:700; }.card-title>div { display:flex; gap:8px; }.card-title small { color:#9aa5b4; font-weight:400; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-bottom:16px; }.metric-card { display:flex; align-items:center; min-height:96px; padding:18px 20px; background:#fff; border-radius:10px; box-shadow:0 2px 12px rgba(27,45,75,.055); }.metric-card>i { display:grid; place-items:center; width:48px; height:48px; margin-right:14px; border-radius:12px; font-size:22px; }.metric-card div { display:flex; flex-direction:column; }.metric-card b { font-size:25px; }.metric-card span { color:#7d8998; font-size:12px; }.metric-card small { margin-left:auto; color:#a1aab6; align-self:flex-end; }
.filter-line { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }.filter-line .el-input { width:240px; }.filter-line .el-select { width:165px; }.money { color:#ef6b6b; font-weight:700; }.table-footer { display:flex; justify-content:space-between; align-items:center; padding-top:18px; color:#8b96a6; font-size:12px; }
.category-tree { min-height:530px; }.schedule-header { display:flex; align-items:center; justify-content:space-between; }.schedule-header>div { display:flex; align-items:center; gap:14px; }.schedule-grid { display:grid; grid-template-columns:95px repeat(7,minmax(105px,1fr)); margin-top:18px; border-top:1px solid #e8edf3; border-left:1px solid #e8edf3; }.schedule-grid>div { min-height:72px; padding:10px; border-right:1px solid #e8edf3; border-bottom:1px solid #e8edf3; }.schedule-corner,.schedule-day,.period-cell { display:grid; place-items:center; color:#65758b; background:#f8fafc; font-weight:700; font-size:12px; }.period-cell { min-height:104px!important; }.schedule-slot { min-height:104px!important; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#c0c7d1; cursor:pointer; }.schedule-slot.occupied { align-items:flex-start; justify-content:flex-start; color:#435268; background:#fff4f8; border-top:3px solid #ff6f9c; }.schedule-slot.occupied span { font-weight:700; line-height:1.5; }.schedule-slot.occupied small { margin-top:10px; color:#ff6f9c; }.schedule-tip { color:#8793a3; font-size:12px; }.schedule-tip i { color:#4f8cf7; }.question-box { padding:14px; margin-bottom:18px; background:#f8fafc; border-radius:8px; }.question-box p { color:#435268; line-height:1.7; }.question-box small { color:#9aa5b4; }
@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(2,1fr)}.schedule-card{overflow:auto}.schedule-grid{min-width:950px}}
@media(max-width:700px){.mama-box-page{padding:14px}.heading-actions{display:none}.metric-grid{grid-template-columns:1fr}.filter-line .el-input,.filter-line .el-select{width:100%}}
</style>
