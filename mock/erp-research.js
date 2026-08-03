const state = [
  { id: 'BEAUTY-001', caseNo: 'RB-202608-001', customerName: '林女士', room: '203', program: '产后腹直肌修复', category: '产康', owner: '陈老师', baseline: '2.8cm', current: '1.9cm', nextReview: '2026-08-05', stage: '复测待安排', risk: '低', consent: '已签署', status: '方案执行中' },
  { id: 'BEAUTY-002', caseNo: 'RB-202608-002', customerName: '周女士', room: '305', program: '肩颈筋膜放松', category: '美容', owner: '何老师', baseline: '疼痛 7/10', current: '疼痛 3/10', nextReview: '2026-08-03', stage: '效果观察', risk: '低', consent: '已签署', status: '方案执行中' },
  { id: 'BEAUTY-003', caseNo: 'RB-202607-018', customerName: '赵女士', room: '401', program: '骨盆闭合管理', category: '产康', owner: '陈老师', baseline: '6.2°', current: '3.4°', nextReview: '2026-08-01', stage: '待医生复核', risk: '中', consent: '已签署', status: '需要复核' },
  { id: 'BEAUTY-004', caseNo: 'RB-202607-012', customerName: '苏女士', room: '208', program: '产后皮肤屏障修护', category: '美容', owner: '何老师', baseline: '水分 31%', current: '水分 43%', nextReview: '2026-08-09', stage: '已归档', risk: '低', consent: '已签署', status: '已完成' }
]

module.exports = [
  {
    url: '/vue-element-admin/erp/research/modules/beauty-cases$',
    type: 'get',
    response: config => {
      const query = config.query || {}
      const list = state.filter(row => Object.keys(query).every(key => !query[key] || String(row[key] || '').includes(String(query[key]))))
      return { code: 20000, data: { list, total: list.length } }
    }
  },
  {
    url: '/vue-element-admin/erp/research/modules/beauty-cases/save$',
    type: 'post',
    response: config => {
      const body = config.body || {}
      const row = { ...body, id: body.id || `BEAUTY-${Date.now()}`, status: body.status || '待制定方案' }
      state.unshift(row)
      return { code: 20000, data: row }
    }
  },
  {
    url: '/vue-element-admin/erp/research/modules/beauty-cases/action$',
    type: 'post',
    response: config => {
      const body = config.body || {}
      const row = state.find(item => item.id === body.id)
      if (row && body.action === '安排复测') row.stage = '复测已预约'
      if (row && body.action === '提交复核') row.status = '待医生复核'
      if (row && body.action === '归档案例') { row.stage = '已归档'; row.status = '已完成' }
      if (row && body.action === '记录跟进') row.stage = '跟进中'
      return { code: 20000, data: row || { id: body.id, action: body.action } }
    }
  }
]
