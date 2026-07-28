const port = process.argv[2]
const pageUrl = process.argv[3] || 'http://localhost:9527/#/nursing/item-1'

if (!port) {
  throw new Error('Usage: node scripts/smoke-nursing-center.mjs <debug-port> [page-url]')
}

const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

async function getPageTarget() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(response => response.json())
      const target = targets.find(item => item.type === 'page')
      if (target) return target
    } catch (error) {
      // The browser may still be starting.
    }
    await delay(250)
  }
  throw new Error('Chrome DevTools endpoint did not become ready')
}

const target = await getPageTarget()
const socket = new WebSocket(target.webSocketDebuggerUrl)
const pending = new Map()
const runtimeErrors = []
let nextId = 1

await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})

socket.addEventListener('message', event => {
  const message = JSON.parse(event.data)
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id)
    pending.delete(message.id)
    if (message.error) reject(new Error(message.error.message))
    else resolve(message.result)
    return
  }
  if (message.method === 'Runtime.exceptionThrown') {
    runtimeErrors.push(message.params.exceptionDetails.text || 'Runtime exception')
  }
  if (message.method === 'Runtime.consoleAPICalled' && message.params.type === 'error') {
    runtimeErrors.push(message.params.args.map(item => item.value || item.description || '').join(' '))
  }
})

const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = nextId
  nextId += 1
  pending.set(id, { resolve, reject })
  socket.send(JSON.stringify({ id, method, params }))
})

const evaluate = async expression => {
  const response = await send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true
  })
  if (response.exceptionDetails) {
    throw new Error(response.exceptionDetails.text || 'Evaluation failed')
  }
  return response.result.value
}

const waitForText = async(text, timeout = 15000) => {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeout) {
    if (await evaluate(`document.body && document.body.innerText.includes(${JSON.stringify(text)})`)) return
    await delay(300)
  }
  throw new Error(`Timed out waiting for text: ${text}`)
}

const waitForSelector = async(selector, timeout = 15000) => {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeout) {
    if (await evaluate(`Boolean(document.querySelector(${JSON.stringify(selector)}))`)) return
    await delay(300)
  }
  throw new Error(`Timed out waiting for selector: ${selector}`)
}

const closeLegacyDialog = async() => {
  await evaluate(`(() => {
    const button = document.querySelector('.nursing-legacy-action-dialog .el-dialog__headerbtn')
    if (button) button.click()
    return Boolean(button)
  })()`)
  await delay(250)
}

const openMenuAction = async label => {
  await evaluate(`(() => {
    const title = document.querySelector('.customer-card-title')
    if (!title) return false
    title.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }))
    return true
  })()`)
  await delay(350)
  const clicked = await evaluate(`(() => {
    const poppers = [...document.querySelectorAll('.nursing-card-popper')]
      .filter(item => getComputedStyle(item).display !== 'none')
    const button = poppers.flatMap(item => [...item.querySelectorAll('button')])
      .find(item => item.textContent.trim() === ${JSON.stringify(label)})
    if (button) button.click()
    return Boolean(button)
  })()`)
  if (!clicked) throw new Error(`Could not click nursing card action: ${label}`)
  await waitForSelector('.nursing-legacy-action-dialog')
  await delay(250)
}

await send('Page.enable')
await send('Runtime.enable')
await send('Network.enable')
await send('Page.navigate', { url: 'http://localhost:9527/' })
await delay(800)
await send('Network.setCookie', {
  name: 'Admin-Token',
  value: 'admin-token',
  url: 'http://localhost:9527/',
  path: '/'
})
const reloadUrl = pageUrl.replace('http://localhost:9527/', 'http://localhost:9527/?nursing-smoke=1')
await send('Page.navigate', { url: reloadUrl })
await waitForText('护理中心预览')

const initial = await evaluate(`(() => {
  const text = document.body.innerText
  const metricLabels = [
    '在住总人数', '妈妈人数', '宝宝人数', '待查房数', '妈妈待护理', '宝宝待护理',
    '顺产', '剖腹产', '小产', '入住宝宝', '男宝宝', '女宝宝', '正常', '异常',
    '危险', '总服务数', '待服务', '已服务', '一对一护理', '一对多护理'
  ]
  return {
    title: text.includes('护理中心预览'),
    metrics: metricLabels.filter(label => text.includes(label)),
    hasClubTab: text.includes('会所'),
    hasHomeTab: text.includes('到家'),
    hasStatusFilters: ['护理情况：', '正常', '异常', '危险', '外出'].every(label => text.includes(label)),
    floorGroups: document.querySelectorAll('.floor-group').length,
    customerCards: document.querySelectorAll('.customer-card').length
  }
})()`)

await evaluate(`document.querySelector('.level-select .el-input').click()`)
await delay(300)
const careLevelOptions = await evaluate(`document.body.innerText.includes('一级护理') && document.body.innerText.includes('二级护理')`)

await evaluate(`(() => {
  const button = [...document.querySelectorAll('.stay-tabs button')].find(item => item.textContent.trim() === '到家')
  if (button) button.click()
  return Boolean(button)
})()`)
await delay(300)
const homeMode = await evaluate(`document.body.innerText.includes('到家01')`)

await evaluate(`(() => {
  const button = [...document.querySelectorAll('.stay-tabs button')].find(item => item.textContent.trim() === '会所')
  if (button) button.click()
  return Boolean(button)
})()`)
await delay(300)

await evaluate(`(() => {
  const title = document.querySelector('.customer-card-title')
  if (!title) return false
  title.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }))
  return true
})()`)
await delay(500)
const cardMenu = await evaluate(`(() => {
  const text = [...document.querySelectorAll('.nursing-card-popper')]
    .filter(item => getComputedStyle(item).display !== 'none')
    .map(item => item.innerText)
    .join(' ')
  return ['产康服务预约', '产康服务确认', '护理计划单', '妈妈护理记录', '产康服务记录',
    '月嫂服务记录', '医生查房记录', '健康评估', '外出申请'].every(label => text.includes(label))
})()`)

await evaluate(`document.querySelector('.customer-card-footer button[title="服务预约"]').click()`)
await waitForSelector('.nursing-legacy-action-dialog')
const serviceBookingDialog = await evaluate(`(() => {
  const text = document.querySelector('.nursing-legacy-action-dialog').innerText
  return [
    '客户名称：', '预约完成日期：', '预约分店：', '预约床位：', '预约设备：',
    '微信', '短信', '选择服务人及时间段', '项目类型：', '套餐内服务项目',
    '套餐外服务项目', '额外购买项目', '项目卡'
  ].every(label => text.includes(label))
})()`)
await closeLegacyDialog()

await evaluate(`document.querySelector('.customer-card-footer button[title="护理服务确认"]').click()`)
await waitForSelector('.nursing-legacy-action-dialog')
const planConfirmationDialog = await evaluate(`(() => {
  const text = document.querySelector('.nursing-legacy-action-dialog').innerText
  return [
    '客户姓名：', '项目名称：', '分店：', '查询', '打印', '确定完成',
    '日历', '列表', '白班', '休班', '晚班', '行政班'
  ].every(label => text.includes(label))
})()`)
await closeLegacyDialog()

const actionChecks = {}
const actionExpectations = {
  '产康服务确认': ['当前合同：', '选择服务：', '完成时间：', '完成次数：', '服务员工：', '手 工 费：', '服务分店：', '套餐内服务项目', '产康储值卡'],
  '护理计划单': ['模板：', '打印', '确认更新护理计划单', '计划日期：', '客户姓名：', '分娩医院：', '护理服务计划明细', '护理团队确认'],
  '妈妈护理记录': ['客户姓名', '宝宝姓名', '房间号', '门店类别', '客户状态', '新增', '编辑', '打印', '护理记录', '体温(C°)', '血压(mmHg)'],
  '产康服务记录': ['客户姓名', '宝宝姓名', '项目名称', '服务人', '分店名称', '审核状态', '是否自动生成', '编辑', '审核', '反审核', '项目服务评价'],
  '月嫂服务记录': ['客户姓名', '护理师名称', '完成状态', '服务类型', '派工审核', '新增', '派遣护理师', '上户', '下户', '更换护理师', '确认结算'],
  '医生查房记录': ['客户姓名', '宝宝姓名', '科别', '异常状态', '查房时间', '新增', '护士回复', '一般情况', '处理情况'],
  '健康评估': ['客户姓名', '宝宝姓名', '房间号', '门店类别', '产妇入住评估新增', '宝宝入住评估新增', '母婴指导评估新增', '健康评估记录'],
  '外出申请': ['客户姓名', '外出状态', '外出时间', '新增', '编辑', '审核', '确定客户已返回', '外出原因', '审核状态']
}

for (const [action, expected] of Object.entries(actionExpectations)) {
  await openMenuAction(action)
  actionChecks[action] = await evaluate(`(() => {
    const dialog = document.querySelector('.nursing-legacy-action-dialog')
    const text = dialog ? dialog.innerText : ''
    return ${JSON.stringify(expected)}.every(label => text.includes(label))
  })()`)
  await closeLegacyDialog()
}

await evaluate(`document.querySelector('.customer-card .person-button').click()`)
await waitForText('新增新妈妈护理记录')
const motherDialog = await evaluate(`document.body.innerText.includes('体征信息') && document.body.innerText.includes('乳汁(奶量)：') && document.body.innerText.includes('附件：')`)
await evaluate(`document.querySelector('.el-dialog__wrapper:not([style*="display: none"]) .el-dialog__headerbtn').click()`)
await delay(250)

await evaluate(`document.querySelector('.customer-card .add-baby-button').click()`)
await waitForText('新增宝宝信息')
const babyDialog = await evaluate(`document.body.innerText.includes('怀孕周期：') && document.body.innerText.includes('分娩医院：') && document.body.innerText.includes('出院诊断：')`)
await evaluate(`document.querySelector('.el-dialog__wrapper:not([style*="display: none"]) .el-dialog__headerbtn').click()`)
await delay(250)

await evaluate(`document.querySelectorAll('.customer-card .person-button')[1].click()`)
await waitForText('宝宝护理记录表')
const babyCareDialog = await evaluate(`['体征记录', '宝宝进食', '更换尿布', '洗澡游泳', '宝宝用药', '护理交接'].every(label => document.body.innerText.includes(label))`)

const result = {
  url: await evaluate('location.href'),
  initial,
  careLevelOptions,
  homeMode,
  cardMenu,
  serviceBookingDialog,
  planConfirmationDialog,
  actionChecks,
  motherDialog,
  babyDialog,
  babyCareDialog,
  runtimeErrors
}

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
socket.close()
