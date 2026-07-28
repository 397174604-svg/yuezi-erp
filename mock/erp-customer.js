const sources = [
  { id: 'SRC01', name: '客户介绍', group: '转介绍' },
  { id: 'SRC02', name: '住附近', group: '自然客流' },
  { id: 'SRC03', name: '电话来访', group: '电话咨询' },
  { id: 'SRC04', name: '大众点评', group: '线上平台' },
  { id: 'SRC05', name: '美团咨询', group: '线上平台' },
  { id: 'SRC06', name: '地推拓客', group: '市场活动' },
  { id: 'SRC07', name: '抖音咨询', group: '内容平台' },
  { id: 'SRC08', name: '小红书咨询', group: '内容平台' },
  { id: 'SRC09', name: '自然上门', group: '自然客流' },
  { id: 'SRC10', name: '网络搜索', group: '搜索引擎' },
  { id: 'SRC11', name: '市场渠道', group: '渠道合作' },
  { id: 'SRC12', name: '二胎入住', group: '老客复购' },
  { id: 'SRC13', name: '内部资源', group: '内部资源' }
]

const rooms = [
  { id: 'R0301', name: '301', type: '豪华套房', store: '中心广场旗舰店', dailyPrice: 1188, status: '可预订' },
  { id: 'R0302', name: '302', type: '舒适大床', store: '中心广场旗舰店', dailyPrice: 968, status: '可预订' },
  { id: 'R0501', name: '501', type: '5楼VIP', store: '中心广场旗舰店', dailyPrice: 1588, status: '待清洁' },
  { id: 'R0601', name: '601', type: '至尊女王', store: '黄河路轻奢店', dailyPrice: 1988, status: '可预订' },
  { id: 'R0602', name: '602', type: '总统套房', store: '黄河路轻奢店', dailyPrice: 2688, status: '已预订' }
]

const packages = [
  { id: 'PKG01', name: '基础套餐', days: 28, amount: 36800, roomType: '舒适大床' },
  { id: 'PKG02', name: '修复套餐', days: 28, amount: 56800, roomType: '豪华套房' },
  { id: 'PKG03', name: '修养套餐', days: 42, amount: 86800, roomType: '尊享套房' },
  { id: 'PKG04', name: '私享套餐', days: 28, amount: 108800, roomType: '臻享套房' },
  { id: 'PKG05', name: '女王套餐（私人定制）', days: 42, amount: 168800, roomType: '至尊女王' },
  { id: 'PKG06', name: '总统套餐（私人定制）', days: 56, amount: 268800, roomType: '总统套房' }
]

const trackers = [
  { id: 'U0001', name: '管理员', department: '管理部', store: '全部门店' },
  { id: 'U0106', name: '李顾问', department: '销售一部', store: '中心广场旗舰店' },
  { id: 'U0108', name: '王顾问', department: '销售一部', store: '中心广场旗舰店' },
  { id: 'U0203', name: '陈顾问', department: '销售二部', store: '黄河路轻奢店' }
]

const introducers = [
  { id: 'REF01', name: '演示介绍人 A', type: '客户介绍', mobile: '138****1208' },
  { id: 'REF02', name: '演示同行 B', type: '同行介绍', mobile: '138****2361' },
  { id: 'REF03', name: '演示员工 C', type: '员工介绍', mobile: '138****3514' }
]

const areas = [
  { id: 'AREA01', name: '金水区' },
  { id: 'AREA02', name: '郑东新区' },
  { id: 'AREA03', name: '中原区' },
  { id: 'AREA04', name: '二七区' },
  { id: 'AREA05', name: '管城回族区' },
  { id: 'AREA06', name: '惠济区' }
]

const hospitals = ['郑州大学第一附属医院', '河南省人民医院', '郑州市妇幼保健院', '郑州大学第三附属医院']

module.exports = [
  {
    url: '/vue-element-admin/erp/customer/entry-options',
    type: 'get',
    response: _ => ({ code: 20000, data: { sources, rooms, packages, trackers, introducers, areas, hospitals }})
  },
  {
    url: '/vue-element-admin/erp/customer/duplicate-check',
    type: 'post',
    response: config => {
      const mobile = (config.body.mobile || '').replace(/\s/g, '')
      const wechat = (config.body.wechat || '').trim()
      const matched = mobile.endsWith('0000') || wechat.toLowerCase() === 'demo'
      return {
        code: 20000,
        data: {
          matched,
          records: matched ? [{ code: 'KH-2026-00086', name: '演示客户', mobile: '138****0000', status: '意向B', trackerName: '李顾问' }] : []
        }
      }
    }
  },
  {
    url: '/vue-element-admin/erp/customer/draft',
    type: 'post',
    response: config => ({ code: 20000, data: { draftId: config.body.draftId || `DRAFT-${Date.now()}`, savedAt: new Date().toLocaleString('zh-CN', { hour12: false }) }})
  },
  {
    url: '/vue-element-admin/erp/customer$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: {
        customerId: `CUST-${Date.now()}`,
        customerCode: `KH-${new Date().getFullYear()}-${String(Date.now()).slice(-5)}`,
        status: config.body.status,
        createdAt: new Date().toLocaleString('zh-CN', { hour12: false })
      }
    })
  },
  {
    url: '/vue-element-admin/erp/customer/modules/[^/]+$',
    type: 'get',
    response: config => ({
      code: 20000,
      data: { resource: config.url.split('/').pop(), list: [], total: 0, loadedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/customer/modules/[^/]+/save$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { id: config.body.id || `RECORD-${Date.now()}`, savedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/customer/modules/[^/]+/action$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { action: config.body.action, auditId: `AUDIT-${Date.now()}`, processedAt: Date.now() }
    })
  },
  {
    url: '/vue-element-admin/erp/customer/point-settings$',
    type: 'post',
    response: config => ({
      code: 20000,
      data: { rules: Object.keys(config.body).length, savedAt: Date.now() }
    })
  }
]
