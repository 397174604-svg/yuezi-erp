import { applyOriginalEvidence } from './original-page-evidence'
import { applyAuditedSurfaceEvidence } from './audited-surface-adapter'

const stores = ['中心广场旗舰店', '黄河路轻奢店']

const input = (key, label, required = false) => ({ key, label, type: 'input', required, verified: false })
const select = (key, label, options, required = false) => ({ key, label, type: 'select', options, required, verified: false })
const date = (key, label, required = false) => ({ key, label, type: 'date', required, verified: false })
const dateRange = (key, label) => ({ key, label, type: 'dateRange', verified: false })
const number = (key, label, required = false) => ({ key, label, type: 'number', required, verified: false })
const textarea = (key, label, required = false) => ({ key, label, type: 'textarea', required, verified: false })
const switchField = (key, label) => ({ key, label, type: 'switch', verified: false })
const upload = (key, label, required = false) => ({ key, label, type: 'upload', required, verified: false })
const richText = (key, label, required = false) => ({ key, label, type: 'richText', required, verified: false })
const col = (key, label, width, extra = {}) => ({ key, label, width, verified: false, ...extra })

const commonMeta = {
  evidenceLevel: '待原系统二次核验',
  completionLevel: 'Visible',
  originalUrl: '',
  queryActions: ['查询', '重置'],
  evidenceNote: '菜单名称与顺序来自本地 ERP 菜单；筛选、按钮、列、表单、枚举、默认值和状态流转均为仓库已有妈妈宝盒草图整理，未从原 ERP 页面逐项验证。'
}

const withMeta = config => ({ ...commonMeta, ...config })

const productFields = [
  input('code', '商品编码', true), input('name', '商品名称', true),
  select('store', '所属门店', stores, true), select('category', '商品类别', ['妈妈护理', '宝宝用品', '产康用品', '营养膳食'], true),
  input('spec', '规格型号'), input('unit', '单位', true),
  number('costPrice', '成本价'), number('originalPrice', '原价'), number('salePrice', '销售价', true), number('pointPrice', '积分价'),
  number('stockQuantity', '库存数量'), switchField('inStore', '店内销售'), switchField('integral', '积分商品'),
  switchField('recommended', '是否推荐'), upload('cover', '商品封面'), upload('gallery', '商品图片'),
  richText('description', '商品详情'), textarea('remark', '备注')
]

const orderFields = [
  input('code', '销售单编号'), select('type', '销售类型', ['商城商品', '服务项目', '妈妈课堂'], true),
  input('customer', '客户', true), input('mobile', '手机号'), select('store', '销售分店', stores, true),
  number('amount', '消费金额', true), number('coupon', '优惠金额'), number('debt', '欠款金额'),
  select('payMethod', '支付方式', ['微信结算', '会员卡', '积分支付', '现金', '挂账']),
  select('pickup', '取货方式', ['门店自提', '快递配送', '到店服务']),
  input('deliveryAddress', '收货地址'), input('expressNo', '快递单号'),
  textarea('orderRemark', '订单备注')
]

const projectFields = [
  input('code', '项目编码', true), input('name', '项目名称', true),
  select('store', '所属门店', stores, true), select('category', '项目类别', ['产康项目', '宝宝护理', '妈妈课堂', '营养咨询'], true),
  input('unit', '单位', true), number('costPrice', '进价'), number('salePrice', '销售价', true), number('pointPrice', '积分价'),
  switchField('integral', '积分项目'), switchField('inStore', '店内销售'), switchField('recommended', '是否推荐'),
  upload('cover', '项目封面'), richText('description', '项目详情'), textarea('remark', '备注')
]

const matronFields = [
  input('code', '月嫂编号', true), input('name', '姓名', true), select('store', '所属门店', stores, true),
  number('age', '年龄'), input('mobile', '联系方式'), select('jobType', '职业类型', ['月嫂', '育儿嫂', '催乳师']),
  select('level', '月嫂等级', ['初级月嫂', '中级月嫂', '高级月嫂', '金牌月嫂']),
  number('standardFee', '标准费用'), select('serviceStatus', '服务状态', ['可预约', '服务中', '休假']),
  upload('avatar', '头像'), upload('certificate', '资质证书'), richText('introduction', '个人简介'), switchField('enabled', '是否启用')
]

const categoryFields = [
  input('name', '分类名称', true), select('parent', '上级分类', ['商城商品', '服务项目', '妈妈课堂'], true),
  number('sort', '排序'), upload('icon', '分类图标'), input('navigationName', '妈妈端导航名称'),
  switchField('enabled', '是否启用'), textarea('remark', '备注')
]

const parentingFields = [
  input('title', '标题', true), select('section', '内容栏目', ['育儿知识', '护理知识', '妈咪课堂'], true),
  select('stage', '成长阶段', ['请选择', '新生儿', '婴儿期', '幼儿期', '学龄前']),
  select('contentType', '数据类型', ['图文', '视频', '音频']), input('author', '制单人'),
  upload('cover', '封面图片'), richText('content', '内容正文', true), switchField('pinned', '是否置顶'),
  date('publishDate', '发布日期'), textarea('remark', '备注')
]

const questionFields = [
  textarea('question', '问题', true), input('nickname', '客户昵称'), input('mobile', '联系电话'),
  input('expert', '指定专家'), select('visibility', '展示范围', ['公开', '仅本人']),
  textarea('reply', '回复内容'), upload('attachment', '回复附件')
]

const reviewFields = [
  textarea('content', '妈妈评语', true), input('nickname', '客户昵称'), input('mobile', '联系电话'),
  upload('images', '评语图片'), select('status', '公开状态', ['待审核', '已公开', '已隐藏']),
  textarea('auditRemark', '审核备注')
]

const communityFields = [
  textarea('content', '发帖内容', true), input('nickname', '客户昵称'), input('mobile', '联系电话'),
  upload('images', '帖子图片'), switchField('pinned', '是否置顶'), switchField('recommended', '是否推荐'),
  select('status', '帖子状态', ['正常', '待审核', '已隐藏']), textarea('auditRemark', '审核备注')
]

const contentFields = [
  input('title', '标题', true), select('contentType', '图文类别', ['会所简介', '特色服务', '轮播图', 'Logo', '专家头图'], true),
  select('store', '所属门店', [...stores, '全部门店']), input('author', '制单人'),
  upload('cover', '展示图片'), richText('content', '图文内容', true), number('sort', '排序'),
  select('status', '发布状态', ['待发布', '已发布']), textarea('remark', '备注')
]

const commentFields = [
  textarea('content', '评论内容'), select('commentType', '评论类型', ['物料', '项目', '膳食']),
  input('target', '商品/项目名称'), input('customer', '评价客户'), number('productScore', '商品评价'),
  number('packageScore', '包装评分'), number('speedScore', '配送评分'), number('serviceScore', '服务评分'),
  textarea('reply', '回复内容', true), select('visibility', '展示范围', ['公开', '仅评价人'])
]

const classFields = [
  input('name', '课程名称', true), select('store', '所属门店', stores, true), input('location', '地点', true),
  number('fee', '费用'), input('audience', '活动对象'), input('baseProject', '基础项目'),
  number('capacity', '人数上限'), upload('cover', '课程封面'), richText('description', '课程描述'),
  switchField('enabled', '是否启用')
]

const scheduleFields = [
  input('className', '课程名称', true), select('store', '所属门店', stores, true), date('classDate', '上课日期', true),
  select('period', '时段', ['上午', '下午', '晚上'], true), input('startTime', '开始时间', true),
  input('endTime', '结束时间', true), input('teacher', '授课老师'), input('location', '上课地点'),
  number('capacity', '人数上限'), textarea('remark', '排班备注')
]

export const mallPageConfigs = {
  商品管理: withMeta({
    key: 'products',
    mode: 'list',
    description: '维护妈妈端商城商品、价格、库存、积分与上下架信息。',
    actions: ['新增', '编辑', '删除', '上架', '下架', '推荐', '取消推荐', '导出'],
    filters: [
      input('code', '商品编码'), input('name', '商品名称'), select('store', '门店', stores),
      select('category', '商品类别', ['妈妈护理', '宝宝用品', '产康用品', '营养膳食']),
      select('status', '上架状态', ['已上架', '已下架']), select('recommended', '是否推荐', ['是', '否'])
    ],
    columns: [
      col('code', '商品编码', 130), col('name', '商品名称', 170), col('store', '门店', 150),
      col('category', '商品类别', 110), col('spec', '规格型号', 110), col('unit', '单位', 65),
      col('originalPrice', '原价', 95, { money: true }), col('salePrice', '销售价', 95, { money: true }),
      col('pointPrice', '积分价', 90), col('stockQuantity', '库存数量', 90),
      col('status', '上架状态', 95, { tag: true }), col('integral', '积分商品', 90),
      col('recommended', '推荐', 70)
    ],
    formFields: productFields
  }),
  商品订单: withMeta({
    key: 'orders',
    mode: 'list',
    description: '查看妈妈端订单的支付、优惠、欠款、配送、出库与取消状态。',
    actions: ['补录订单', '查看详情', '确认支付', '确认出库', '取消订单', '退款', '导出'],
    filters: [
      input('code', '销售单编号'), input('customer', '客户'), input('mobile', '手机号'),
      select('store', '销售分店', stores), select('type', '销售类型', ['商城商品', '服务项目', '妈妈课堂']),
      select('payStatus', '支付状态', ['未支付', '部分支付', '已支付', '已退款']),
      select('stockStatus', '出库状态', ['待出库', '已出库', '待核销']), dateRange('orderRange', '下单日期')
    ],
    columns: [
      col('code', '销售单编号', 155), col('type', '销售类型', 105), col('payMethod', '支付方式', 110),
      col('amount', '消费金额', 100, { money: true }), col('coupon', '优惠金额', 100, { money: true }),
      col('debt', '欠款金额', 100, { money: true }), col('orderedAt', '下单日期', 150),
      col('store', '销售分店', 150), col('customer', '客户', 110), col('mobile', '手机号', 125),
      col('pickup', '取货方式', 105), col('payStatus', '支付状态', 100, { tag: true }),
      col('stockStatus', '出库状态', 100, { tag: true }), col('status', '订单状态', 100, { tag: true })
    ],
    formFields: orderFields
  }),
  项目管理: withMeta({
    key: 'projects',
    mode: 'list',
    description: '维护妈妈端可购买服务项目及其价格、积分、销售与推荐状态。',
    actions: ['新增', '编辑', '删除', '上架', '下架', '推荐', '取消推荐', '导出'],
    filters: [
      input('code', '项目编码'), input('name', '项目名称'), select('store', '门店', stores),
      select('category', '项目类别', ['产康项目', '宝宝护理', '妈妈课堂', '营养咨询']),
      select('status', '上架状态', ['已上架', '已下架']), select('recommended', '是否推荐', ['是', '否'])
    ],
    columns: [
      col('code', '项目编码', 130), col('name', '项目名称', 170), col('store', '门店', 150),
      col('category', '项目类别', 110), col('unit', '单位', 65),
      col('costPrice', '进价', 95, { money: true }), col('salePrice', '销售价', 95, { money: true }),
      col('pointPrice', '积分价', 90), col('status', '上架状态', 95, { tag: true }),
      col('integral', '积分项目', 90), col('inStore', '店内销售', 90), col('recommended', '推荐', 70)
    ],
    formFields: projectFields
  }),
  月嫂管理: withMeta({
    key: 'matrons',
    mode: 'list',
    description: '维护妈妈端展示的月嫂、育儿嫂及催乳师人员资料。',
    actions: ['新增', '编辑', '删除', '启用', '停用', '设置可预约', '导出'],
    filters: [
      input('code', '月嫂编号'), input('name', '姓名'), select('store', '门店', stores),
      select('jobType', '职业类型', ['月嫂', '育儿嫂', '催乳师']),
      select('level', '月嫂等级', ['初级月嫂', '中级月嫂', '高级月嫂', '金牌月嫂']),
      select('serviceStatus', '服务状态', ['可预约', '服务中', '休假']),
      select('enabled', '启用状态', ['启用', '停用'])
    ],
    columns: [
      col('code', '月嫂编号', 120), col('name', '姓名', 100), col('store', '门店', 150),
      col('age', '年龄', 65), col('mobile', '联系方式', 125), col('jobType', '职业类型', 100),
      col('level', '月嫂等级', 100), col('standardFee', '标准费用', 105, { money: true }),
      col('serviceStatus', '服务状态', 100, { tag: true }), col('enabled', '启用状态', 95, { tag: true })
    ],
    formFields: matronFields
  }),
  商品类别设置: withMeta({
    key: 'categories',
    mode: 'tree',
    description: '维护商城商品、服务项目与课堂的分类层级及妈妈端导航顺序。',
    actions: ['新增分类', '编辑分类', '新增子分类', '删除分类', '启用', '停用'],
    filters: [input('name', '分类名称'), select('parent', '上级分类', ['商城商品', '服务项目', '妈妈课堂']), select('enabled', '启用状态', ['启用', '停用'])],
    columns: [
      col('name', '分类名称', 150), col('parent', '上级分类', 120), col('navigationName', '妈妈端导航名称', 160),
      col('sort', '排序', 75), col('products', '商品/项目数', 110), col('enabled', '状态', 90, { tag: true })
    ],
    formFields: categoryFields
  }),
  育儿档案: withMeta({
    key: 'parenting',
    mode: 'content',
    description: '按成长阶段发布育儿、护理及课堂图文或视频内容。',
    actions: ['发布内容', '编辑', '删除', '发布', '撤回', '置顶', '取消置顶', '预览'],
    filters: [
      input('title', '标题'), select('section', '内容栏目', ['育儿知识', '护理知识', '妈咪课堂']),
      select('stage', '成长阶段', ['请选择', '新生儿', '婴儿期', '幼儿期', '学龄前']),
      select('contentType', '数据类型', ['图文', '视频', '音频']), select('status', '发布状态', ['草稿', '已发布']), dateRange('publishRange', '制单日期')
    ],
    columns: [
      col('title', '标题', 230), col('section', '内容栏目', 110), col('stage', '成长阶段', 100),
      col('contentType', '数据类型', 90), col('author', '制单人', 100), col('publishedAt', '制单日期', 150),
      col('pinned', '置顶', 70), col('status', '发布状态', 95, { tag: true })
    ],
    formFields: parentingFields
  }),
  专家问答: withMeta({
    key: 'questions',
    mode: 'content',
    description: '接收妈妈端问题，分配专家并维护回复与展示范围。',
    actions: ['新增问答', '查看', '回复', '编辑回复', '隐藏', '公开', '删除'],
    filters: [
      input('question', '问题关键词'), input('nickname', '客户昵称'), input('mobile', '联系电话'),
      input('expert', '指定专家'), select('replyStatus', '回复状态', ['待回复', '已回复']),
      select('visibility', '展示范围', ['公开', '仅本人']), dateRange('askedRange', '提问时间')
    ],
    columns: [
      col('question', '问题', 280), col('nickname', '客户昵称', 105), col('mobile', '联系电话', 125),
      col('askedAt', '提问时间', 150), col('expert', '指定专家', 110),
      col('replyStatus', '回复状态', 95, { tag: true }), col('visibility', '展示范围', 95)
    ],
    formFields: questionFields,
    replyFields: questionFields.slice(3)
  }),
  妈妈评语: withMeta({
    key: 'reviews',
    mode: 'content',
    description: '审核妈妈端服务评语、图片及公开状态。',
    actions: ['新增评语', '查看', '审核通过', '隐藏', '删除', '预览'],
    filters: [
      input('content', '评语关键词'), input('nickname', '客户昵称'), input('mobile', '联系电话'),
      select('status', '公开状态', ['待审核', '已公开', '已隐藏']), dateRange('createdRange', '创建时间')
    ],
    columns: [
      col('content', '妈妈评语', 300), col('nickname', '客户昵称', 105), col('mobile', '联系电话', 125),
      col('images', '图片数', 80), col('createdAt', '创建时间', 150), col('status', '公开状态', 95, { tag: true })
    ],
    formFields: reviewFields
  }),
  辣妈贴吧: withMeta({
    key: 'community',
    mode: 'content',
    description: '维护妈妈端社区帖子、审核、置顶、推荐与展示状态。',
    actions: ['发布帖子', '查看', '审核通过', '隐藏', '置顶', '取消置顶', '推荐', '取消推荐', '删除'],
    filters: [
      input('content', '帖子关键词'), input('nickname', '客户昵称'), input('mobile', '联系电话'),
      select('status', '帖子状态', ['正常', '待审核', '已隐藏']), select('pinned', '是否置顶', ['是', '否']),
      select('recommended', '是否推荐', ['是', '否']), dateRange('postedRange', '发帖时间')
    ],
    columns: [
      col('content', '发帖内容', 280), col('nickname', '客户昵称', 105), col('mobile', '联系电话', 125),
      col('postedAt', '发帖时间', 150), col('status', '帖子状态', 95, { tag: true }),
      col('pinned', '置顶', 70), col('recommended', '推荐', 70), col('views', '浏览量', 80)
    ],
    formFields: communityFields
  }),
  图文介绍: withMeta({
    key: 'content',
    mode: 'content',
    description: '维护会所介绍、特色服务、轮播图、Logo 与专家头图等妈妈端内容。',
    actions: ['新增图文', '编辑', '删除', '发布', '撤回', '预览', '调整排序'],
    filters: [
      input('title', '标题'), select('contentType', '图文类别', ['会所简介', '特色服务', '轮播图', 'Logo', '专家头图']),
      select('store', '门店', [...stores, '全部门店']), select('status', '发布状态', ['待发布', '已发布']),
      dateRange('createdRange', '制单日期')
    ],
    columns: [
      col('title', '标题', 230), col('contentType', '图文类别', 125), col('store', '门店', 150),
      col('author', '制单人', 100), col('createdAt', '制单日期', 150), col('sort', '排序', 75),
      col('remark', '备注', 180), col('status', '发布状态', 95, { tag: true })
    ],
    formFields: contentFields
  }),
  评论回复列表: withMeta({
    key: 'comments',
    mode: 'content',
    description: '集中处理物料、项目与膳食评论及各评分项。',
    actions: ['查看', '回复', '编辑回复', '隐藏', '公开', '删除', '导出'],
    filters: [
      input('content', '评论关键词'), select('commentType', '评论类型', ['物料', '项目', '膳食']),
      input('target', '商品/项目名称'), input('customer', '评价客户'),
      select('replyStatus', '回复状态', ['待回复', '已回复']), dateRange('createdRange', '评价时间')
    ],
    columns: [
      col('content', '评论内容', 250), col('commentType', '评论类型', 95), col('target', '商品/项目名称', 180),
      col('productScore', '商品评价', 100, { score: true }), col('packageScore', '包装评分', 100, { score: true }),
      col('speedScore', '配送评分', 100, { score: true }), col('serviceScore', '服务评分', 100, { score: true }),
      col('customer', '评价客户', 105), col('createdAt', '评价时间', 150),
      col('replyStatus', '回复状态', 95, { tag: true })
    ],
    formFields: commentFields,
    replyFields: commentFields.slice(-2)
  }),
  妈妈课堂: withMeta({
    key: 'classes',
    mode: 'list',
    description: '维护课程、地点、费用、活动对象、人数限制和关联基础项目。',
    actions: ['新增课程', '编辑', '删除', '启用', '停用', '查看报名', '导出'],
    filters: [
      input('name', '课程名称'), select('store', '门店', stores), input('location', '地点'),
      input('baseProject', '基础项目'), select('enabled', '状态', ['启用', '停用'])
    ],
    columns: [
      col('name', '课程名称', 190), col('store', '门店', 150), col('location', '地点', 180),
      col('fee', '费用', 90, { money: true }), col('audience', '活动对象', 150),
      col('description', '课程描述', 230), col('baseProject', '基础项目', 140),
      col('capacity', '人数上限', 90), col('registrations', '报名人数', 90), col('enabled', '状态', 90, { tag: true })
    ],
    formFields: classFields
  }),
  妈妈课堂排班: withMeta({
    key: 'class-schedule',
    mode: 'schedule',
    description: '按周维护课堂的日期、时段、授课老师、地点与报名容量。',
    actions: ['添加排班', '编辑排班', '删除排班', '复制本周', '上一周', '本周', '下一周', '查看报名'],
    filters: [
      select('store', '门店', stores), input('className', '课程名称'), input('teacher', '授课老师'),
      dateRange('classRange', '上课日期'), select('period', '时段', ['上午', '下午', '晚上'])
    ],
    columns: [
      col('classDate', '上课日期', 115), col('period', '时段', 85), col('className', '课程名称', 190),
      col('store', '门店', 150), col('teacher', '授课老师', 110), col('location', '上课地点', 150),
      col('startTime', '开始时间', 90), col('endTime', '结束时间', 90),
      col('capacity', '人数上限', 90), col('registrations', '报名人数', 90), col('status', '排班状态', 95, { tag: true })
    ],
    formFields: scheduleFields
  })
}

applyOriginalEvidence('mall', mallPageConfigs)
applyAuditedSurfaceEvidence('mall', mallPageConfigs)

export const mallMenuTitles = Object.keys(mallPageConfigs)

export function getMallPageConfig(title) {
  return mallPageConfigs[title] || mallPageConfigs.商品管理
}
