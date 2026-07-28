const products = [
  { id: 'P001', code: 'MBX-1001', name: '母婴护理组合装', store: '中心广场旗舰店', category: '妈妈护理', spec: '标准装', unit: '套', originalPrice: '298.00', salePrice: '268.00', pointPrice: '2680', status: '已上架', inStore: '是', integral: '是', recommended: '是' },
  { id: 'P002', code: 'MBX-1002', name: '新生儿呵护礼盒', store: '中心广场旗舰店', category: '宝宝用品', spec: '礼盒装', unit: '盒', originalPrice: '199.00', salePrice: '179.00', pointPrice: '1790', status: '已上架', inStore: '是', integral: '是', recommended: '否' },
  { id: 'P003', code: 'MBX-1003', name: '产后舒缓护理包', store: '黄河路轻奢店', category: '产康用品', spec: '5件套', unit: '套', originalPrice: '368.00', salePrice: '328.00', pointPrice: '3280', status: '已下架', inStore: '否', integral: '是', recommended: '否' }
]

const orders = [
  { id: 'O001', code: 'SO-20260723-0018', type: '商城商品', payMethod: '微信结算', amount: '268.00', coupon: '20.00', debt: '0.00', store: '中心广场旗舰店', customer: '演示客户 A', mobile: '138****2108', pickup: '门店自提', payStatus: '已支付', stockStatus: '已出库', status: '正常', orderedAt: '2026-07-23 10:26' },
  { id: 'O002', code: 'SO-20260723-0017', type: '护理项目', payMethod: '会员卡', amount: '680.00', coupon: '0.00', debt: '80.00', store: '中心广场旗舰店', customer: '演示客户 B', mobile: '138****2361', pickup: '到店服务', payStatus: '部分支付', stockStatus: '待核销', status: '正常', orderedAt: '2026-07-23 09:48' },
  { id: 'O003', code: 'SO-20260722-0096', type: '商城商品', payMethod: '积分支付', amount: '179.00', coupon: '179.00', debt: '0.00', store: '黄河路轻奢店', customer: '演示客户 C', mobile: '138****2514', pickup: '快递配送', payStatus: '已支付', stockStatus: '待出库', status: '正常', orderedAt: '2026-07-22 17:03' }
]

const projects = [
  { id: 'S001', code: 'SV-0101', name: '产后舒缓护理', store: '中心广场旗舰店', category: '产康项目', unit: '次', costPrice: '180.00', salePrice: '680.00', pointPrice: '6800', status: '已上架', integral: '是', inStore: '是', recommended: '是' },
  { id: 'S002', code: 'SV-0102', name: '宝宝抚触体验', store: '中心广场旗舰店', category: '宝宝护理', unit: '次', costPrice: '60.00', salePrice: '198.00', pointPrice: '1980', status: '已上架', integral: '否', inStore: '是', recommended: '否' },
  { id: 'S003', code: 'SV-0103', name: '母乳喂养指导', store: '黄河路轻奢店', category: '妈妈课堂', unit: '课时', costPrice: '80.00', salePrice: '299.00', pointPrice: '2990', status: '已下架', integral: '否', inStore: '否', recommended: '否' }
]

const matrons = [
  { id: 'M001', code: 'YS-0086', name: '月嫂 A', store: '中心广场旗舰店', age: 42, mobile: '138****3086', jobType: '月嫂', level: '高级月嫂', standardFee: '12800.00', serviceStatus: '可预约', status: '启用' },
  { id: 'M002', code: 'YS-0091', name: '月嫂 B', store: '中心广场旗舰店', age: 38, mobile: '138****3191', jobType: '育儿嫂', level: '中级月嫂', standardFee: '9800.00', serviceStatus: '服务中', status: '启用' },
  { id: 'M003', code: 'YS-0107', name: '月嫂 C', store: '黄河路轻奢店', age: 45, mobile: '138****3307', jobType: '催乳师', level: '高级月嫂', standardFee: '680.00/次', serviceStatus: '休假', status: '停用' }
]

const categories = [
  { id: 'C01', name: '妈妈护理', parent: '商城商品', sort: 10, products: 18, status: '启用' },
  { id: 'C02', name: '宝宝用品', parent: '商城商品', sort: 20, products: 26, status: '启用' },
  { id: 'C03', name: '产康用品', parent: '商城商品', sort: 30, products: 12, status: '启用' },
  { id: 'C04', name: '营养膳食', parent: '商城商品', sort: 40, products: 9, status: '启用' },
  { id: 'C05', name: '课程服务', parent: '服务项目', sort: 50, products: 7, status: '启用' }
]

const parenting = [
  { id: 'A001', title: '新生儿居家护理清单', section: '育儿知识', stage: '新生儿', contentType: '图文', author: '内容运营', publishedAt: '2026-07-22 16:20', pinned: '是', status: '已发布' },
  { id: 'A002', title: '婴儿期睡眠规律指南', section: '护理知识', stage: '婴儿期', contentType: '图文', author: '护理主管', publishedAt: '2026-07-21 11:08', pinned: '否', status: '已发布' },
  { id: 'A003', title: '亲子互动小游戏', section: '妈咪课堂', stage: '幼儿期', contentType: '视频', author: '课堂老师', publishedAt: '2026-07-20 09:36', pinned: '否', status: '草稿' }
]

const questions = [
  { id: 'Q001', question: '产后如何安排循序渐进的恢复训练？', nickname: '用户 A', mobile: '138****4102', askedAt: '2026-07-23 09:16', expert: '产康专家', replyStatus: '待回复', visibility: '公开' },
  { id: 'Q002', question: '宝宝日常抚触需要注意哪些细节？', nickname: '用户 B', mobile: '138****4265', askedAt: '2026-07-22 18:32', expert: '护理专家', replyStatus: '已回复', visibility: '公开' },
  { id: 'Q003', question: '月子餐怎样兼顾清淡与营养？', nickname: '用户 C', mobile: '138****4387', askedAt: '2026-07-22 15:07', expert: '营养师', replyStatus: '已回复', visibility: '仅本人' }
]

const reviews = [
  { id: 'R001', content: '服务安排很细致，护理记录清晰。', nickname: '用户 A', mobile: '138****5103', images: 2, createdAt: '2026-07-23 10:08', status: '已公开' },
  { id: 'R002', content: '课堂内容实用，希望增加更多场次。', nickname: '用户 B', mobile: '138****5258', images: 0, createdAt: '2026-07-22 16:40', status: '待审核' }
]

const community = [
  { id: 'T001', content: '分享一份待产物品准备清单', nickname: '用户 A', mobile: '138****6104', postedAt: '2026-07-23 08:56', status: '正常', pinned: '是', recommended: '是', views: 268 },
  { id: 'T002', content: '记录宝宝入住第七天的变化', nickname: '用户 B', mobile: '138****6271', postedAt: '2026-07-22 20:15', status: '待审核', pinned: '否', recommended: '否', views: 96 },
  { id: 'T003', content: '妈妈课堂笔记分享', nickname: '用户 C', mobile: '138****6395', postedAt: '2026-07-22 14:22', status: '正常', pinned: '否', recommended: '是', views: 183 }
]

const content = [
  { id: 'I001', title: '奇德芬芳会所介绍', type: '会所简介', store: '中心广场旗舰店', author: '系统管理员', createdAt: '2026-07-20 14:00', remark: '妈妈端关于我们', status: '已发布' },
  { id: 'I002', title: '夏季入住专属服务', type: '特色服务', store: '中心广场旗舰店', author: '运营专员', createdAt: '2026-07-21 10:28', remark: '首页推荐位', status: '已发布' },
  { id: 'I003', title: '产康专家团队', type: '专家Head图片', store: '全部门店', author: '运营专员', createdAt: '2026-07-22 09:10', remark: '专家页头图', status: '待发布' }
]

const comments = [
  { id: 'E001', content: '包装完整，配送及时。', type: '物料', target: '新生儿呵护礼盒', productScore: 5, packageScore: 5, speedScore: 5, serviceScore: 5, customer: '用户 A', createdAt: '2026-07-23 09:48', replyStatus: '待回复' },
  { id: 'E002', content: '服务手法专业，讲解也很清楚。', type: '项目', target: '产后舒缓护理', productScore: 5, packageScore: 0, speedScore: 0, serviceScore: 5, customer: '用户 B', createdAt: '2026-07-22 17:20', replyStatus: '已回复' },
  { id: 'E003', content: '口味清淡，搭配丰富。', type: '膳食', target: '滋养月子餐', productScore: 4, packageScore: 4, speedScore: 5, serviceScore: 5, customer: '用户 C', createdAt: '2026-07-22 12:35', replyStatus: '已回复' }
]

const classes = [
  { id: 'CL01', name: '新生儿护理入门', location: '中心广场店·课堂 A', fee: '免费', audience: '准妈妈及家属', description: '基础喂养、拍嗝与日常护理', baseProject: '妈妈课堂体验', registrations: 16, status: '启用' },
  { id: 'CL02', name: '产后科学恢复', location: '中心广场店·产康教室', fee: '99.00', audience: '产后妈妈', description: '恢复节奏、运动和注意事项', baseProject: '产康体验课', registrations: 12, status: '启用' },
  { id: 'CL03', name: '月子膳食公开课', location: '黄河路店·多功能厅', fee: '免费', audience: '孕期及产后家庭', description: '营养搭配与常见误区', baseProject: '营养咨询', registrations: 9, status: '启用' }
]

const schedule = {
  start: '2026-07-20',
  end: '2026-07-26',
  days: ['7月20日（周一）', '7月21日（周二）', '7月22日（周三）', '7月23日（周四）', '7月24日（周五）', '7月25日（周六）', '7月26日（周日）'],
  rows: [
    { period: '上午', slots: ['新生儿护理入门', '', '月子膳食公开课', '', '新生儿护理入门', '产后科学恢复', ''] },
    { period: '下午', slots: ['', '产后科学恢复', '', '新生儿护理入门', '', '月子膳食公开课', ''] },
    { period: '晚上', slots: ['', '', '', '产后科学恢复', '', '', '家庭护理问答'] }
  ]
}

module.exports = [
  {
    url: '/vue-element-admin/erp/mama-box/overview',
    type: 'get',
    response: _ => ({ code: 20000, data: { products, orders, projects, matrons, categories, parenting, questions, reviews, community, content, comments, classes, schedule }})
  },
  {
    url: '/vue-element-admin/erp/mama-box/.*?/save',
    type: 'post',
    response: config => ({ code: 20000, data: { ...config.body, updatedAt: '2026-07-23 11:00' }, message: '保存成功' })
  },
  {
    url: '/vue-element-admin/erp/mama-box/.*?/.*?/(publish|reply|recommend|top|cancel)',
    type: 'post',
    response: _ => ({ code: 20000, data: 'success' })
  }
]
