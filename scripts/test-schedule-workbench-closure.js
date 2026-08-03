const fs = require('fs')
const path = require('path')

const file = path.resolve(__dirname, '../src/views/erp/schedule-workbench/index.vue')
const source = fs.readFileSync(file, 'utf8')
const failures = []

const requiredProjectGroups = ['产后类', '产康服务', '护理服务', '膳食服务', '客房服务', '增值服务', '软硬件服务', '大礼包', '科研肌肤']
const requiredProjects = ['盆底肌修复', '腹直肌修复', '腺体修复', '疤痕松解', '淋巴疏通', '修复7+21疗程']
const requiredDevices = ['人体雕刻家', '汤姆森颈压床', '绛私细胞焕活仪', '艾灸仪', '暖骨仪', '红外线理疗仪', '太空舱', '能量氧疗舱', '通泽医疗盆底肌', '通泽医疗腹直肌电刺激']

for (const value of [...requiredProjectGroups, ...requiredProjects, ...requiredDevices, '洗头床']) {
  if (!source.includes(value)) failures.push(`missing selectable resource: ${value}`)
}
if (!source.includes('length: 10') || !source.includes('`VIP${index + 1}`')) failures.push('missing VIP1-VIP10 bed range')

const requiredFlows = [
  "performRehabModuleAction('service-appointments', '取消'",
  "saveRehabModuleRecord('staff-schedule-settings'",
  "performRehabModuleAction('staff-schedule-settings', '删除'",
  "shiftStatus: '停诊'",
  'this.businessStoreValue',
  '全部门店仅支持汇总查询'
]
for (const value of requiredFlows) {
  if (!source.includes(value)) failures.push(`missing schedule workflow: ${value}`)
}

if (!source.includes('取消所选预约') || !source.includes('新增排班') || !source.includes('编辑排班')) {
  failures.push('missing appointment/schedule operation entry')
}

if (failures.length) {
  console.error(failures.join('\n'))
  process.exit(1)
}

console.log('schedule workbench closure: project/device/bed/store/action checks passed')
