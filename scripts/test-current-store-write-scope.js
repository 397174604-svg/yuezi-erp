const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')
const surfaces = [
  'src/views/erp/research-workbench/index.vue',
  'src/views/erp/rehab-workbench/index.vue',
  'src/views/erp/rehab-workbench/AppointmentWorkbench.vue',
  'src/views/erp/rehab-workbench/RecoveryOperationsBoard.vue',
  'src/views/erp/nursing-workbench/index.vue',
  'src/views/erp/nursing-workbench/NursingCenter.vue',
  'src/views/erp/diet-workbench/index.vue',
  'src/views/erp/inventory-workbench/index.vue',
  'src/views/erp/finance-workbench/index.vue',
  'src/views/erp/schedule-workbench/index.vue'
]

const failures = []
for (const relative of surfaces) {
  const source = fs.readFileSync(path.join(root, relative), 'utf8')
  if (!source.includes('currentStoreId')) failures.push(`${relative}: missing Vuex currentStoreId`)
  if (!source.includes("=== 'all'")) failures.push(`${relative}: missing all-store write guard`)
  if (/storeId:\s*this\.\$route\.query\.storeId/.test(source)) {
    failures.push(`${relative}: write payload still depends on route query storeId`)
  }
  if (/\$route\.query\.storeId\s*\|\|\s*['"]all['"]/.test(source)) {
    failures.push(`${relative}: route query still falls back to all for business scope`)
  }
}

if (failures.length) {
  console.error(failures.join('\n'))
  process.exit(1)
}

console.log(`current-store write scope: ${surfaces.length}/${surfaces.length} surfaces passed`)
