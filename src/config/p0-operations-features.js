export const p0OperationsFeatures = [
  { id: 'F038', title: '客户运营（线索跟进）', component: 'marketing', permissions: ['CUSTOMER.VIEW'], state: 'partial', scope: '独立维护客户培育阶段、负责人、跟进时间与结果；记录按门店保存，客户主档联动规则正在确认。' },
  { id: 'F039', title: '营销与内容', component: 'marketing', permissions: ['CUSTOMER.VIEW'], state: 'partial', scope: '独立维护营销计划、目标、渠道、执行周期与状态；外部渠道配置完成前仅保存内部草稿。' },
  { id: 'F040', title: '积分体系（规则+兑换互通）', component: 'customer', configTitle: '积分设置', canonicalPath: '/customer/member/item-1', permissions: ['CUSTOMER.VIEW'], state: 'partial', scope: '已收口到客户管理的正式积分规则入口，保留 F040 直达别名；月子、产康兑换互通和规则写入尚未闭环。' },
  { id: 'F041', title: '内容运营（课程/育儿文章）', component: 'marketing', permissions: ['MALL.VIEW'], state: 'partial', scope: '独立维护课程和育儿文章稿件、作者、发布范围与审核状态；客户终端同步完成前保持待发布。' },
  { id: 'F042', title: '短信营销', component: 'marketing', permissions: ['SYSTEM.VIEW'], state: 'external', scope: '独立维护短信模板、目标人群、发送计划与审批状态。', blocker: '短信服务商、签名和模板尚未完成业务配置，当前任务保持待发送。' },
  { id: 'F043', title: 'AI客服知识库', component: 'status', permissions: ['SYSTEM.VIEW'], state: 'external', scope: '知识库能力入口已保留。', blocker: '知识检索、人工转接与内容审核服务正在配置。' },
  { id: 'F044', title: '月嫂管理', component: 'matron', configTitle: '月嫂档案', canonicalPath: '/matron/item-1', permissions: ['MATRON.VIEW', 'NURSING.VIEW'], state: 'partial', scope: '已收口到月嫂管理的正式档案入口；档案维护规则正在确认。' },
  { id: 'F045', title: '月嫂档期（派工）', component: 'matron', configTitle: '月嫂档期', canonicalPath: '/matron/item-2', permissions: ['MATRON.VIEW', 'NURSING.VIEW'], state: 'partial', scope: '已收口到月嫂管理的正式档期入口，保留 F045 直达别名；派工写入、冲突锁定和消息通知尚未闭环。' },
  { id: 'F046', title: '月嫂结算', component: 'matron', configTitle: '月嫂结算列表', canonicalPath: '/matron/item-3', permissions: ['MATRON.VIEW', 'NURSING.VIEW'], state: 'partial', scope: '已收口到月嫂管理的正式结算入口，保留 F046 直达别名；结算确认、薪酬入账和审计写入尚未开放。' },
  { id: 'F047', title: '品项与提成', component: 'basic', configTitle: '基础项目', canonicalPath: '/basic/item-2', permissions: ['BASIC.VIEW'], state: 'partial', scope: '已收口到基础资料的服务品项入口；售价与提成规则确认后开放维护。' },
  { id: 'F048', title: '提成方案（阶梯系数）', component: 'basic', configTitle: '提成比例设置', permissions: ['BASIC.VIEW'], state: 'partial', scope: '提成比例页面可见；阶梯系数计算、版本生效和薪酬联动尚未闭环。' },
  { id: 'F049', title: '项目耗材BOM（成本联动）', component: 'status', permissions: ['BASIC.VIEW', 'WAREHOUSE.VIEW'], state: 'blocked', scope: 'BOM功能入口已建立。', blocker: '项目耗材清单、自动扣料和成本联动规则正在确认。' },
  { id: 'F050', title: '套餐管理', component: 'sales', configTitle: '套餐管理', canonicalPath: '/sales/item-4', permissions: ['SALES.VIEW'], state: 'partial', scope: '已收口到销售管理的正式套餐入口，保留 F050 直达别名；保存前/服务端均校验天数、门店及原价≥活动价≥成交价，权益版本、房型定价规则仍待业务口径确认。' },
  { id: 'F051', title: '目标管理', component: 'basic', configTitle: '业绩目标设置', permissions: ['BASIC.VIEW'], state: 'partial', scope: '目标配置页面可见；目标写入、月度冻结和实际完成额联动尚未开放。' },
  { id: 'F052', title: '员工与组织', component: 'foundation', pageType: 'organization', configTitle: '员工与组织', canonicalPath: '/people/item-6', permissions: ['SYSTEM.VIEW', 'BASIC.VIEW'], state: 'partial', scope: '已收口到组织与绩效的正式员工与组织入口；具备相应管理权限的账号可新增或编辑部门，并维护员工登录账号、默认门店和角色；排班规则正在完善。' },
  { id: 'F053', title: '角色权限', component: 'foundation', pageType: 'role-permission', configTitle: '角色权限', canonicalPath: '/people/item-7', permissions: ['SYSTEM.VIEW'], state: 'partial', scope: '已收口到组织与绩效的正式角色权限入口，保留 F053 直达别名；具备 SYSTEM.EDIT/BASIC.EDIT 的账号可保存授权矩阵，按租户隔离并写审计。' },
  { id: 'F054', title: '品控检查（评分表）', component: 'status', permissions: ['RISK.VIEW', 'SYSTEM.VIEW'], state: 'blocked', scope: '品控检查入口已建立。', blocker: '评分模板、检查单、整改闭环和门店评分规则正在确认。' },
  { id: 'F055', title: '品控看板（部门均分+积分榜）', component: 'status', permissions: ['RISK.VIEW', 'REPORT.VIEW'], state: 'blocked', scope: '品控看板入口已建立。', blocker: '完成品控检查记录后展示部门均分与积分榜。' },
  { id: 'F056', title: '数据报表（自定义+导出）', component: 'report', configTitle: 'S13销售业绩报表', canonicalPath: '/report/item-13', permissions: ['REPORT.VIEW'], state: 'partial', scope: '已收口到查询报表的正式销售业绩入口，保留 F056 直达别名；自定义列、公式和打印模板尚未闭环。' },
  { id: 'F057', title: '经营月报', component: 'report', configTitle: 'C0经营月报', permissions: ['REPORT.VIEW'], state: 'partial', scope: '经营月报按租户和门店范围汇总收款流水，可查询和导出当前结果；退款、付款、成本和月结口径仍待业务确认。' },
  { id: 'F058', title: '门店与渠道（含转店）', component: 'foundation', pageType: 'store-management', configTitle: '门店与渠道（含转店）', canonicalPath: '/store/item-1', permissions: ['SYSTEM.VIEW', 'CUSTOMER.VIEW'], state: 'partial', scope: '已收口到门店管理的正式门店与渠道入口；具备写权限可编辑既有门店并写审计。渠道、客户转店、资产与合同迁移事务尚未建立。' },
  { id: 'F059', title: '资产账单（储值卡+次卡余额）', component: 'asset', permissions: ['CUSTOMER.VIEW', 'FINANCE.VIEW'], state: 'partial', scope: '会员资产账单使用独立的资产卡、余额账户和交易流水；发卡、充值、扣款与次卡核销均保留审计记录。', blocker: '支付、短信和跨门店资产迁移规则正在配置；未完成的外部服务保持待处理状态。' },
  { id: 'F060', title: '次卡价值分析', component: 'status', permissions: ['REPORT.VIEW', 'FINANCE.VIEW'], state: 'blocked', scope: '次卡价值分析入口已建立。', blocker: '资产账户和核销流水完整后计算销量、消耗、递延与毛利指标。' },
  { id: 'F061', title: '系统设置', component: 'system', configTitle: '系统设置', canonicalPath: '/system/item-1', permissions: ['SYSTEM.VIEW'], state: 'partial', scope: '已收口到系统设置的正式参数入口，保留 F061 直达别名；审批、支付和消息外部服务配置尚未开放。' }
]

export const p0OperationsFeatureIds = p0OperationsFeatures.map(item => item.id)

// P1 items are deliberately kept in this branch-scoped acceptance group. They
// do not alter the main ERP menu configuration, but remain visible and never
// resolve to a 404 while their production data models are being completed.
export const p1OperationsFeatures = [
  { id: 'F096', title: '组织架构', component: 'foundation', pageType: 'organization', configTitle: '组织架构（P1）', permissions: ['SYSTEM.VIEW', 'BASIC.VIEW'], state: 'partial', scope: '复用真实组织、门店、部门和员工查询入口；部门和既有门店编辑受写权限、门店范围和审计约束。岗位、编制和审批关系尚未完成。' },
  { id: 'F126', title: '门店目标', component: 'status', permissions: ['SYSTEM.VIEW', 'REPORT.VIEW'], state: 'blocked', scope: '门店目标入口已建立。', blocker: '目标版本、月度冻结、实际完成额和审批规则正在确认，当前暂不保存完成率。' },
  { id: 'F127', title: '分销/渠道佣金', component: 'marketing', permissions: ['CUSTOMER.VIEW', 'SYSTEM.VIEW'], state: 'partial', scope: '独立维护渠道、佣金规则、结算批次与审批状态；支付服务配置完成前仅形成待付款记录。' },
  { id: 'F128', title: '线索分发', component: 'status', permissions: ['CUSTOMER.VIEW', 'SYSTEM.VIEW'], state: 'blocked', scope: '线索分发入口已建立。', blocker: '分发规则、容量控制、公海回收和冲突处理规则正在确认。' }
]
