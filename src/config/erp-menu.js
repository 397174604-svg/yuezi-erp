export const erpMenuGroups = [
  {
    key: 'customer',
    title: '客户管理',
    icon: 'peoples',
    color: '#B8945A',
    items: [
      '客户中心', '客户录入', '线索管理', '我的客户', '客户管理', '跟进记录', '签单客户', '预约参观', '公海客户',
      {
        key: 'service',
        title: '客服管理',
        icon: 'nested',
        items: ['入住探访记录', '满意度调查表', '客户回访记录', '客户投诉建议', '消息计划模板', '客户消息']
      },
      {
        key: 'member',
        title: '会员管理',
        icon: 'user',
        items: ['积分设置', '积分记录', '发布活动']
      }
    ]
  },
  {
    key: 'sales',
    title: '销售管理',
    icon: 'shopping',
    color: '#ff9f55',
    items: ['合同管理', '商品销售', '销售明细', '套餐管理', '卡类套餐', '赠送管理', '优惠管理', '优惠券管理', '赠送项目申请']
  },
  {
    key: 'finance',
    title: '财务管理',
    icon: 'money',
    color: '#f5ba35',
    items: ['新增收款', '收款管理', '退款申请', '退款审核', '欠款审核', '换货审核', '发票管理', '部门物料预算', '我的费用', '费用审核', '付款管理']
  },
  {
    key: 'room',
    title: '客房管理',
    icon: 'component',
    color: '#45b8ac',
    items: ['房态图', '房态趋势', '房型趋势', '智能排房', '可售房统计', '房型列表', '订房管理', '入住管理', '续住信息', '换房申请', '物品赠送', '客房服务', '外出申请', '物品借还', '洗衣管理']
  },
  {
    key: 'nursing',
    title: '护理管理',
    icon: 'star',
    color: '#8f7cf6',
    items: ['护理中心', '护理计划', '护理部排班第二版', '宝宝档案', '健康评估', '膳食评估', '自定义查房', '医生查房记录', '膳食禁忌查房', '护理计划确认', '护理项目记录', '妈妈护理记录', '宝宝护理记录', '妈妈护理汇总', '宝宝护理汇总', '护理部排班表', '入住物品交接']
  },
  {
    key: 'recovery',
    title: '产康管理',
    icon: 'skill',
    color: '#f0719d',
    items: ['未预约客户服务', '服务预约列表', '服务综合查询', '服务人员任务表', '人员排班设置', '技师人员任务表', '客户服务查询', '产康服务记录表', '完成项目消耗表', '产康健康评估']
  },
  {
    key: 'matron',
    title: '月嫂管理',
    icon: 'user',
    color: '#6f8ff7',
    items: ['月嫂档案', '薪酬标准', '月嫂档期', '月嫂合同', '月嫂服务记录', '月嫂派工审核', '月嫂结算列表', '月嫂预约记录']
  },
  {
    key: 'diet',
    title: '膳食管理',
    icon: 'nested',
    color: '#58b66f',
    items: ['客户餐单', '菜品管理', '膳食套餐', '膳食统计', '送餐统计', '营养汤设置', '营养汤统计', '客餐供应', '食材采购', '膳食销售', '订餐列表', '餐卡管理', '餐卡消费报表']
  },
  {
    key: 'warehouse',
    title: '仓存管理',
    icon: 'table',
    color: '#5886d6',
    items: ['采购计划', '采购订单', '采购单审核', '其他入库', '采购入库', '领料申请', '销售出库', '领料申请(去金额)', '调拨管理', '退货管理', '盘点管理(NEW)', '报损管理', '期初数据导入', '物料库存预警', '期初数据查询', '赠送清单计划', '收发存汇总统计', '库存明细统计', '部门领料统计', '仓库库存查询', '采购明细报表', '预付款列表', '付款单列表', '应付账款明细表']
  },
  {
    key: 'mall',
    title: '商城管理',
    icon: 'wechat',
    color: '#35b7bd',
    items: ['商品管理', '商品订单', '项目管理', '月嫂管理', '商品类别设置', '育儿档案', '专家问答', '妈妈评语', '辣妈贴吧', '图文介绍', '评论回复列表', '妈妈课堂', '妈妈课堂排班']
  },
  {
    key: 'risk',
    title: '风控服务',
    icon: 'lock',
    color: '#e66573',
    items: ['悦禧风控']
  },
  {
    key: 'report',
    title: '查询报表',
    icon: 'chart',
    color: '#4f8cf7',
    items: ['S1 销售排行榜报表', 'S2客户简报', 'S3 畅销排行榜报表', 'S4 (DM)客户合同汇总报表', 'S5商品消费汇总明细表', 'S6销售统计报表', 'S7服务销售汇总明细表', 'S8 卡类销售汇总明细表', 'S9跨店消费报表', 'S10SML销售日报表', 'S11赠送物品明细表', 'S12客户跨店服务消费表', 'S13销售业绩报表', 'F1 月度入住率报表', 'F2 房态统计总体分析', 'F3月度预定明细报表', 'F4月度出中心明细报表', 'F5预住客户采购报表', 'F6入住率', 'C0经营日报表', 'C1 会员充值汇总明细表', 'C2 收款结算类型汇总表', 'C3 付款汇总分析表', 'C4 资金收支出余额表', 'C5 月间天统计分析', 'C6 客户收款跟踪明细表', 'C7 门店收入与成本统计表', 'C8 商品毛利分析表', 'C9 推荐人报表', 'C12 返现消费查询', 'C10 收款款项汇总明细表', 'C11 项目消费收入报表', 'C13收款退款汇总表', 'C14合同业绩报表', 'C15资金账户收支明细表', 'C16收款及结算类型报表', 'H1 客户服务记录报表', 'H2 宝宝体征统计表', 'H3 妈妈的体温与体重变化表', 'H4 产康项目工作汇总表', '企业微信客服报表', '妈妈端分享报表']
  },
  {
    key: 'basic',
    title: '基础资料',
    icon: 'clipboard',
    color: '#7b8a9a',
    items: ['职员档案', '基础项目', '物料档案', '客房档案', '满意度调查表模板', '调查表管理', '仓库档案', '供应商档案', '资金账户', '报表模板', '护理模板', '任务管理', '服务时间设置', '项目手工费设置', '提成比例设置', '设备管理', '业绩目标设置', '优惠金额授权', '床位管理']
  },
  {
    key: 'system',
    title: '系统设置',
    icon: 'theme',
    color: '#65758b',
    items: ['部门管理', '角色管理', '用户管理', '数据字典', '审批流程', '通知公告', '返利设置', '会所介绍', '导航菜单', '移动端导航', '操作按钮', '操作日志', '短信发送设置', '生日短信提醒', '消息发送日志', '预警参数设置', '报表模板自定义', '模板设置', '计划任务', '系统参数设置']
  }
]

const specialPageTypes = {
  '客户中心': 'customer-center',
  '客户录入': 'customer-entry',
  '新增收款': 'form',
  '房态图': 'room-map',
  '护理中心': 'nursing-center',
  '客户餐单': 'meal-plan',
  '悦禧风控': 'risk',
  '导航菜单': 'menu-tree',
  '部门管理': 'organization',
  '角色管理': 'role-permission',
  '用户管理': 'user-account',
  '数据字典': 'data-dictionary',
  '操作按钮': 'operation-permission'
}

export function getPageType(groupKey, title) {
  if (groupKey === 'diet') return 'diet-workbench'
  if (groupKey === 'mall') return 'mall-workbench'
  if (groupKey === 'finance') return 'finance-workbench'
  if (groupKey === 'room') return 'room-workbench'
  if (groupKey === 'nursing') return 'nursing-workbench'
  if (groupKey === 'recovery') return 'rehab-workbench'
  if (groupKey === 'matron') return 'maternity-nurse-workbench'
  if (groupKey === 'risk') return 'risk-workbench'
  if (specialPageTypes[title]) return specialPageTypes[title]
  if (groupKey === 'customer') return 'customer-workbench'
  if (groupKey === 'sales') return 'sales-workbench'
  if (groupKey === 'report') return 'report-workbench'
  if (groupKey === 'basic') return 'basic-workbench'
  if (groupKey === 'warehouse') return 'inventory-workbench'
  if (title.includes('统计') || title.includes('报表') || title.includes('趋势') || title.includes('汇总')) return 'report'
  if (groupKey === 'system') return 'system-workbench'
  return 'list'
}
