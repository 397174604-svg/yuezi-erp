const text = (key, label, placeholder = '') => ({ key, label, type: 'text', placeholder })
const select = (key, label, options) => ({ key, label, type: 'select', options })
const date = (key, label) => ({ key, label, type: 'date' })
const number = (key, label, min = 0) => ({ key, label, type: 'number', min })

export const marketingPageDefinitions = {
  F038: {
    key: 'lead-operation',
    title: '客户运营',
    eyebrow: '线索培育与跟进闭环',
    description: '按门店维护线索阶段、下次跟进时间和负责人，形成可追踪的客户培育队列。',
    primaryAction: '新建跟进任务',
    emptyText: '暂无待跟进线索，可从客户中台分配线索后创建跟进任务。',
    metrics: [['待跟进', 'pending'], ['今日到期', 'dueToday'], ['已转化', 'converted'], ['已逾期', 'overdue']],
    filters: [text('customer', '客户姓名/手机号', '搜索客户'), select('stage', '线索阶段', ['新线索', '邀约中', '已到店', '已签约', '已关闭']), select('owner', '负责人', ['我的客户', '全部负责人']), date('followDate', '跟进日期')],
    columns: [['customer', '客户'], ['source', '线索来源'], ['stage', '线索阶段'], ['owner', '负责人'], ['nextFollowAt', '下次跟进'], ['status', '跟进状态']],
    formFields: [text('customer', '客户姓名', '请输入客户姓名'), select('stage', '线索阶段', ['新线索', '邀约中', '已到店', '已签约', '已关闭']), select('method', '跟进方式', ['电话', '微信', '到店', '视频']), date('nextFollowAt', '下次跟进日期'), text('result', '跟进结果', '记录沟通结果')],
    statuses: ['待跟进', '跟进中', '已转化', '已关闭']
  },
  F039: {
    key: 'campaign-content-plan',
    title: '营销与内容',
    eyebrow: '活动策划、内容协同与渠道归因',
    description: '将营销活动、内容素材、投放渠道和负责人组织为执行计划；渠道完成配置前仅保存活动草稿。',
    primaryAction: '新建营销计划',
    emptyText: '暂无营销计划。新建后先进入草稿，不会自动发布到外部渠道。',
    metrics: [['草稿计划', 'draft'], ['审核中', 'review'], ['执行中', 'running'], ['已复盘', 'reviewed']],
    filters: [text('campaign', '计划名称', '搜索营销计划'), select('channel', '投放渠道', ['抖音', '小红书', '美团', '私域', '线下活动']), select('status', '执行状态', ['草稿', '待审核', '执行中', '已结束']), date('period', '计划日期')],
    columns: [['campaign', '计划名称'], ['objective', '目标'], ['channel', '投放渠道'], ['owner', '负责人'], ['period', '执行周期'], ['status', '执行状态']],
    formFields: [text('campaign', '计划名称', '请输入营销计划名称'), select('objective', '营销目标', ['获客', '到店', '签约', '复购', '品牌曝光']), select('channel', '投放渠道', ['抖音', '小红书', '美团', '私域', '线下活动']), date('startDate', '开始日期'), date('endDate', '结束日期'), text('owner', '负责人', '请输入负责人')],
    statuses: ['草稿', '待审核', '执行中', '已结束']
  },
  F041: {
    key: 'maternal-content-library',
    title: '内容运营',
    eyebrow: '课程与育儿文章编辑发布',
    description: '管理课程、孕产知识和育儿文章的稿件、审核、发布范围与版本，不复用商品台账。',
    primaryAction: '新建内容稿件',
    emptyText: '暂无内容稿件。稿件审核通过前不会同步至客户终端。',
    metrics: [['草稿', 'draft'], ['待审核', 'review'], ['已发布', 'published'], ['需修订', 'revision']],
    filters: [text('title', '标题/作者', '搜索内容'), select('contentType', '内容类型', ['孕期课程', '产后恢复', '新生儿护理', '喂养指导', '会所活动']), select('publishScope', '发布范围', ['全部会员', '孕期客户', '在住客户', '离店会员']), select('status', '稿件状态', ['草稿', '待审核', '已发布', '需修订'])],
    columns: [['title', '内容标题'], ['contentType', '内容类型'], ['author', '作者'], ['publishScope', '发布范围'], ['updatedAt', '最近更新'], ['status', '稿件状态']],
    formFields: [text('title', '内容标题', '请输入课程或文章标题'), select('contentType', '内容类型', ['孕期课程', '产后恢复', '新生儿护理', '喂养指导', '会所活动']), text('author', '作者', '请输入作者'), select('publishScope', '发布范围', ['全部会员', '孕期客户', '在住客户', '离店会员']), text('summary', '内容摘要', '请输入内容摘要')],
    statuses: ['草稿', '待审核', '已发布', '需修订']
  },
  F042: {
    key: 'sms-campaign',
    title: '短信营销',
    eyebrow: '短信模板、发送审批与回执',
    description: '创建短信发送任务并记录模板审核、发送状态和失败原因；服务商完成配置后方可发送。',
    primaryAction: '新建短信任务',
    emptyText: '暂无短信任务。短信服务商完成配置前，任务保存为待配置。',
    integrationNotice: '短信服务商正在配置：可保存任务和审批状态，配置完成后开放发送。',
    metrics: [['待审批', 'review'], ['待配置', 'integration'], ['发送中', 'sending'], ['失败待重试', 'failed']],
    filters: [text('taskName', '任务名称/模板', '搜索短信任务'), select('audience', '客户人群', ['孕期客户', '在住客户', '离店会员', '自定义名单']), select('sendStatus', '发送状态', ['草稿', '待审批', '待配置', '发送中', '已完成', '失败']), date('plannedAt', '计划发送日期')],
    columns: [['taskName', '任务名称'], ['template', '短信模板'], ['audience', '客户人群'], ['plannedAt', '计划发送'], ['approval', '模板/任务审核'], ['sendStatus', '发送状态']],
    formFields: [text('taskName', '任务名称', '请输入短信任务名称'), text('template', '短信模板', '请输入已审核模板名称'), select('audience', '客户人群', ['孕期客户', '在住客户', '离店会员', '自定义名单']), date('plannedAt', '计划发送日期'), text('signature', '短信签名', '请输入已报备签名')],
    statuses: ['草稿', '待审批', '待配置', '发送中', '已完成', '失败']
  },
  F085: {
    key: 'referral-incentive',
    title: '转介绍/老带新激励',
    eyebrow: '推荐关系与奖励审核',
    description: '登记推荐人、新客户、成单条件与奖励发放状态，避免与优惠券活动混为一页。',
    primaryAction: '登记推荐关系',
    emptyText: '暂无推荐关系。奖励需在新客达成规则后审核发放。',
    metrics: [['推荐关系', 'relations'], ['待达标', 'pending'], ['待审核', 'review'], ['已发放', 'issued']],
    filters: [text('referrer', '推荐人/手机号', '搜索推荐人'), text('newCustomer', '新客户/手机号', '搜索新客户'), select('rewardStatus', '奖励状态', ['待达标', '待审核', '已发放', '已驳回']), date('createdAt', '登记日期')],
    columns: [['referrer', '推荐人'], ['newCustomer', '新客户'], ['rule', '达标规则'], ['contract', '关联合同'], ['reward', '奖励内容'], ['rewardStatus', '奖励状态']],
    formFields: [text('referrer', '推荐人', '请输入推荐人姓名/手机号'), text('newCustomer', '新客户', '请输入新客户姓名/手机号'), select('rule', '达标规则', ['到店参观', '签订合同', '完成首付款', '入住']), text('reward', '奖励内容', '请输入奖励内容')],
    statuses: ['待达标', '待审核', '已发放', '已驳回']
  },
  F090: {
    key: 'limited-promotion',
    title: '拼团/秒杀/限时折扣',
    eyebrow: '限时促销库存与价格控制',
    description: '配置促销对象、活动价、限购数量、有效期和库存占用；未接支付时不生成虚假订单。',
    primaryAction: '新建限时促销',
    emptyText: '暂无限时促销。活动启用前必须完成价格和库存审核。',
    metrics: [['草稿', 'draft'], ['待审核', 'review'], ['进行中', 'running'], ['库存预警', 'stockWarning']],
    filters: [text('promotion', '活动名称', '搜索促销活动'), select('promotionType', '促销类型', ['拼团', '秒杀', '限时折扣']), select('status', '活动状态', ['草稿', '待审核', '进行中', '已结束']), date('period', '活动日期')],
    columns: [['promotion', '活动名称'], ['promotionType', '促销类型'], ['product', '关联套餐/卡项'], ['promotionPrice', '活动价'], ['stock', '活动库存'], ['status', '活动状态']],
    formFields: [text('promotion', '活动名称', '请输入活动名称'), select('promotionType', '促销类型', ['拼团', '秒杀', '限时折扣']), text('product', '关联套餐/卡项', '请输入已启用项目'), number('promotionPrice', '活动价'), number('stock', '活动库存'), date('endAt', '结束日期')],
    statuses: ['草稿', '待审核', '进行中', '已结束']
  },
  F091: {
    key: 'viral-gift-coupon',
    title: '推荐有礼/裂变券',
    eyebrow: '分享链路与券核销追踪',
    description: '管理裂变规则、分享人群、券有效期、领取与核销状态，和老带新现金/实物奖励分开。',
    primaryAction: '新建裂变券活动',
    emptyText: '暂无裂变券活动。分享渠道完成配置前仅保存活动草稿。',
    metrics: [['活动草稿', 'draft'], ['已领取', 'received'], ['已核销', 'redeemed'], ['已过期', 'expired']],
    filters: [text('activity', '活动/券名称', '搜索裂变券'), select('couponType', '券类型', ['满减券', '折扣券', '体验券', '赠送项目券']), select('status', '活动状态', ['草稿', '待审核', '进行中', '已结束']), date('validAt', '有效日期')],
    columns: [['activity', '活动名称'], ['couponName', '券名称'], ['couponType', '券类型'], ['shareAudience', '分享人群'], ['receivedRedeemed', '领取/核销'], ['status', '活动状态']],
    formFields: [text('activity', '活动名称', '请输入活动名称'), text('couponName', '券名称', '请输入券名称'), select('couponType', '券类型', ['满减券', '折扣券', '体验券', '赠送项目券']), select('shareAudience', '分享人群', ['全部会员', '在住客户', '离店会员']), date('validUntil', '有效期至')],
    statuses: ['草稿', '待审核', '进行中', '已结束']
  },
  F092: {
    key: 'first-order-trial',
    title: '体验价/新客首单',
    eyebrow: '新客资格与首单价格校验',
    description: '配置体验项目、适用门店、资格规则、体验价和核销状态，防止老客重复享受新客权益。',
    primaryAction: '新建新客体验方案',
    emptyText: '暂无新客体验方案。启用前需完成价格审核和客户资格规则确认。',
    metrics: [['可用方案', 'available'], ['待审核', 'review'], ['已核销', 'redeemed'], ['资格拦截', 'blocked']],
    filters: [text('plan', '方案名称', '搜索体验方案'), select('projectType', '项目类型', ['产康项目', '护理项目', '膳食体验', '月子服务']), select('status', '方案状态', ['草稿', '待审核', '已启用', '已停用']), date('validAt', '有效日期')],
    columns: [['plan', '方案名称'], ['project', '体验项目'], ['store', '适用门店'], ['trialPrice', '体验价'], ['eligibility', '资格规则'], ['status', '方案状态']],
    formFields: [text('plan', '方案名称', '请输入方案名称'), text('project', '体验项目', '请输入体验项目'), number('trialPrice', '体验价'), select('eligibility', '资格规则', ['从未消费', '新注册30天内', '指定渠道新客']), date('validUntil', '有效期至')],
    statuses: ['草稿', '待审核', '已启用', '已停用']
  },
  F127: {
    key: 'channel-commission',
    title: '分销/渠道佣金',
    eyebrow: '渠道合同、佣金规则与结算批次',
    description: '维护渠道来源、佣金规则、归因订单、结算审批与付款回执，未完成付款的记录保持待处理。',
    primaryAction: '新建佣金规则',
    emptyText: '暂无佣金规则。支付服务配置完成前仅形成待付款结算单。',
    metrics: [['有效渠道', 'channels'], ['待归因', 'attribution'], ['待结算', 'settlement'], ['待付款', 'payment']],
    filters: [text('channel', '渠道名称/编号', '搜索渠道'), select('commissionType', '计佣方式', ['固定金额', '成交额比例', '阶梯比例']), select('settlementStatus', '结算状态', ['待归因', '待核算', '待审核', '待付款', '已完成']), date('period', '结算周期')],
    columns: [['channel', '渠道'], ['rule', '佣金规则'], ['orderCount', '归因订单'], ['commissionAmount', '应计佣金'], ['settlementBatch', '结算批次'], ['settlementStatus', '结算状态']],
    formFields: [text('channel', '渠道名称', '请输入渠道名称'), select('commissionType', '计佣方式', ['固定金额', '成交额比例', '阶梯比例']), number('commissionValue', '佣金值'), date('effectiveAt', '生效日期'), text('approvalOwner', '审批负责人', '请输入审批负责人')],
    statuses: ['待归因', '待核算', '待审核', '待付款', '已完成']
  }
}

export function getMarketingPageDefinition(featureId) {
  return marketingPageDefinitions[featureId] || marketingPageDefinitions.F039
}
