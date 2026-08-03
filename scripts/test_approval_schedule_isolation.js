const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')
const read = file => fs.readFileSync(path.join(root, file), 'utf8')
const requireText = (file, text) => {
  if (!read(file).includes(text)) throw new Error(`${file} missing: ${text}`)
}
const forbidText = (file, text) => {
  if (read(file).includes(text)) throw new Error(`${file} must not contain: ${text}`)
}

requireText('src/config/approval-pages.js', "featureId: 'F010'")
requireText('src/config/schedule-pages.js', "featureId: 'F017'")
requireText('src/config/schedule-pages.js', "featureId: 'F086'")
requireText('src/views/erp/approval-workbench/index.vue', '不会回退为收款管理')
requireText('src/views/erp/schedule-workbench/index.vue', 'getRehabModuleData')
requireText('src/views/erp/schedule-workbench/index.vue', "'service-appointments'")
requireText('src/views/erp/schedule-workbench/index.vue', "'staff-schedule-settings'")
forbidText('src/views/erp/schedule-workbench/index.vue', 'room-workbench')
forbidText('src/views/erp/schedule-workbench/index.vue', 'smart-rooms')
console.log('approval/schedule isolation static checks passed')
