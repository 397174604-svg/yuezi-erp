const port = process.argv[2]

if (!port) {
  throw new Error('Usage: node scripts/smoke-nursing-toolbars.mjs <debug-port>')
}

const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

async function getPageTarget() {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(response => response.json())
      const target = targets.find(item => item.type === 'page')
      if (target) return target
    } catch (error) {
      // Browser may still be starting.
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
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text || 'Evaluation failed')
  return response.result.value
}

const waitFor = async(expression, label, timeout = 15000) => {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeout) {
    if (await evaluate(expression)) return
    await delay(250)
  }
  throw new Error(`Timed out waiting for ${label}`)
}

const clickByText = async(selector, label) => {
  const clicked = await evaluate(`(() => {
    const element = [...document.querySelectorAll(${JSON.stringify(selector)})]
      .find(item => item.textContent.trim() === ${JSON.stringify(label)})
    if (element) element.click()
    return Boolean(element)
  })()`)
  if (!clicked) throw new Error(`Could not click ${label}`)
}

const closeVisibleDialog = async() => {
  await evaluate(`(() => {
    const wrappers = [...document.querySelectorAll('.el-dialog__wrapper')]
      .filter(item => getComputedStyle(item).display !== 'none')
    const button = wrappers.at(-1)?.querySelector('.el-dialog__headerbtn')
    if (button) button.click()
    return Boolean(button)
  })()`)
  await delay(250)
}

const isoOffset = days => {
  const value = new Date()
  value.setDate(value.getDate() + days)
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const pages = [
  ['护理计划', ['添加', '新增宝宝', '编辑', '删除', '设置', '月嫂分配', '移动', '确认完成']],
  ['护理部排班第二版', ['添加', '删除', '打印', '批量新增']],
  ['宝宝档案', ['添加', '编辑', '删除', '导出']],
  ['健康评估', []],
  ['膳食评估', ['添加', '编辑', '删除']],
  ['自定义查房', ['添加', '编辑', '删除', '护士回复']],
  ['医生查房记录', ['添加', '编辑', '删除', '护士回复', '打印']],
  ['膳食禁忌查房', ['添加', '删除', '编辑']],
  ['护理计划确认', []],
  ['护理项目记录', ['删除', '编辑']],
  ['妈妈护理记录', ['添加', '编辑', '打印', '产妇护理导出']],
  ['宝宝护理记录', ['添加', '编辑', '打印']],
  ['妈妈护理汇总', []],
  ['宝宝护理汇总', []],
  ['护理部排班表', ['添加', '编辑', '删除', '打印', '设置']],
  ['入住物品交接', ['添加', '编辑', '删除', '确认签收']]
]

const queryExpectations = {
  护理计划: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'], ['房间号', 'input'],
      ['门店类别', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 未入住 -', '- 已退房 -'], '- 已入住 -'],
      ['分娩方式', 'select', ['-请选择-', '顺产分娩', '剖宫产分娩', '小月子', '未生产'], '-请选择-']
    ]
  },
  护理部排班第二版: {
    buttons: ['查询'],
    fields: [['排班类型', 'select', ['护理排班', '行政排班', '其他排班'], '护理排班']]
  },
  宝宝档案: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'], ['宝宝姓名', 'input'], ['房间号', 'input'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 未入住 -', '- 已退房 -', '- 散客 -'], '- 已入住 -'],
      ['分店名称', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['添加时间', 'dateRange']
    ]
  },
  健康评估: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'], ['宝宝姓名', 'input'], ['房间号', 'input'],
      ['门店类别', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 已出院 -'], '- 已入住 -']
    ]
  },
  膳食评估: { buttons: ['搜  索'], fields: [['客户姓名', 'input'], ['房间号', 'input']] },
  自定义查房: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'], ['房间号', 'input'],
      ['查房类型', 'select', ['-请选择-', '妇科', '儿科', '中医', '营养师', '客房管家查房', '专家查房'], '-请选择-'],
      ['门店类别', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 已出院 -'], '- 已入住 -'],
      ['查房时间', 'dateRange']
    ]
  },
  医生查房记录: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'], ['宝宝姓名', 'input'], ['房间号', 'input'],
      ['查房类型', 'select', ['-请选择-', '妇科', '儿科', '客房管家查房'], '-请选择-'],
      ['门店类别', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 已出院 -'], '- 已入住 -'],
      ['异常状态', 'select', ['- 请选择 -', '正常', '异常', '危险'], '- 请选择 -'],
      ['查房时间', 'dateRange']
    ]
  },
  膳食禁忌查房: { buttons: ['搜  索'], fields: [['客户姓名', 'input'], ['房间号', 'input']] },
  护理计划确认: {
    buttons: ['查询', '打印'],
    fields: [
      ['客户姓名', 'input'], ['项目名称', 'input'],
      ['分店', 'select', ['-请选择-', '中心广场旗舰店', '黄河路轻奢店'], '-请选择-']
    ]
  },
  护理项目记录: {
    buttons: ['搜  索', '导出'],
    fields: [
      ['客户姓名', 'input'], ['宝宝姓名', 'input'], ['项目名称', 'input'], ['服务人', 'input'], ['房间号', 'input'],
      ['分店名称', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '中心广场旗舰店'],
      ['类型', 'select', ['-全部-', '套餐内', '套餐外', '额外购'], '-全部-'],
      ['客户状态', 'select', ['-全部-', '店内客户', '散客客户'], '-全部-'],
      ['审核状态', 'select', ['-全部-', '未审核', '已审核'], '-全部-'],
      ['完成日期', 'dateRange', [], [isoOffset(-1), isoOffset(0)]]
    ]
  },
  妈妈护理记录: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'], ['宝宝姓名', 'input'], ['房间号', 'input'],
      ['门店类别', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 已出院 -'], '- 已入住 -']
    ]
  },
  宝宝护理记录: {
    buttons: ['搜  索', '导出'],
    fields: [
      ['客户姓名', 'input'], ['宝宝姓名', 'input'], ['房间号', 'input'],
      ['门店类别', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['客户状态', 'select', ['- 请选择 -', '- 已入住 -', '- 已出院 -'], '- 已入住 -'],
      ['到家客户', 'checkbox', [], false]
    ]
  },
  妈妈护理汇总: {
    buttons: ['查询', '导出', '打印'],
    fields: [
      ['房间号', 'input'], ['房间楼层', 'input'], ['妈妈名称', 'input'],
      ['门店', 'select', ['-全部-', '中心广场旗舰店', '黄河路轻奢店'], '-全部-'],
      ['记录日期', 'dateRange', [], [isoOffset(-1), isoOffset(0)]],
      ['到家客户', 'checkbox', [], false]
    ]
  },
  护理部排班表: {
    buttons: ['查询'],
    fields: [
      ['排班部门', 'select', [], ''],
      ['排班类型', 'select', ['护理排班', '行政排班', '其他排班'], '护理排班'],
      ['排班日期', 'dateRange', [], [isoOffset(0), isoOffset(7)]]
    ]
  },
  入住物品交接: {
    buttons: ['搜  索'],
    fields: [
      ['客户姓名', 'input'],
      ['接收状态', 'select', ['请选择', '接收', '送还'], '请选择'],
      ['交接时间范围', 'dateRange']
    ]
  }
}

await send('Page.enable')
await send('Runtime.enable')
await send('Network.enable')
await send('Page.navigate', { url: 'http://localhost:9527/' })
await delay(600)
await send('Network.setCookie', {
  name: 'Admin-Token',
  value: 'admin-token',
  url: 'http://localhost:9527/',
  path: '/'
})

const toolbarChecks = {}
const queryChecks = {}

for (let index = 0; index < pages.length; index += 1) {
  const itemNumber = index + 2
  const [title, expected] = pages[index]
  await send('Page.navigate', {
    url: `http://localhost:9527/?toolbar-smoke=${itemNumber}#/nursing/item-${itemNumber}`
  })
  await waitFor(
    `document.querySelector('.page-heading h2')?.textContent.trim() === ${JSON.stringify(title)}`,
    title
  )
  await delay(250)
  const actual = await evaluate(`[
    ...document.querySelectorAll('.business-toolbar .toolbar-action')
  ].map(item => item.textContent.trim())`)
  toolbarChecks[title] = {
    expected,
    actual,
    pass: JSON.stringify(actual) === JSON.stringify(expected)
  }
  const expectedQuery = queryExpectations[title]
  if (expectedQuery) {
    queryChecks[title] = await evaluate(`(() => {
      const expected = ${JSON.stringify(expectedQuery)}
      const actualFields = [...document.querySelectorAll('.filter-card .el-form-item[data-field]')].map(item => {
        const type = item.getAttribute('data-control-type')
        const label = item.querySelector('.el-form-item__label')?.textContent.trim()
          || item.querySelector('.el-checkbox__label')?.textContent.trim()
          || ''
        let value = ''
        let options = []
        if (type === 'select') {
          const root = item.querySelector('.el-select')
          value = root?.querySelector('.el-input__inner')?.value || ''
          options = (root?.__vue__?.options || []).map(option => option.label)
        } else if (type === 'dateRange') {
          value = [...item.querySelectorAll('input')].map(input => input.value)
        } else if (type === 'checkbox') {
          value = Boolean(item.querySelector('input[type=checkbox]')?.checked)
        } else {
          value = item.querySelector('input, textarea')?.value || ''
        }
        return [label, type, options, value]
      })
      const actualButtons = [...document.querySelectorAll('.filter-card .query-action')]
        .map(item => item.textContent.trim())
      const fieldPass = expected.fields.every((field, index) => {
        const actual = actualFields[index] || []
        if (field[0] !== actual[0] || field[1] !== actual[1]) return false
        if (field[2] && JSON.stringify(field[2]) !== JSON.stringify(actual[2])) return false
        if (field.length > 3 && JSON.stringify(field[3]) !== JSON.stringify(actual[3])) return false
        return true
      }) && actualFields.length === expected.fields.length
      return {
        expectedButtons: expected.buttons,
        actualButtons,
        expectedFields: expected.fields,
        actualFields,
        pass: fieldPass && JSON.stringify(expected.buttons) === JSON.stringify(actualButtons)
      }
    })()`)
  }
}

await send('Page.navigate', {
  url: 'http://localhost:9527/?toolbar-smoke=plan#/nursing/item-2'
})
await waitFor(
  `document.querySelector('.page-heading h2')?.textContent.trim() === '护理计划'`,
  '护理计划'
)

await clickByText('.business-toolbar .toolbar-action', '添加')
await waitFor(`document.body.innerText.includes('新增护理计划单')`, '新增护理计划单')
const addDialog = await evaluate(`[
  '选择客户：', '护理总监：', '护理主任：', '生活管家：', '妇科保健医：',
  '儿科保健医：', '产后康复：', '责任护士(长)：', '母婴喂养师：',
  '营 养 师：', '护士组成员：', '客房组成员：', '备注：', '产妇出院诊断：',
  '制单人：', '制单日期：'
].every(label => document.body.innerText.includes(label))`)
await closeVisibleDialog()

await clickByText('.business-toolbar .toolbar-action', '编辑')
await waitFor(`document.body.innerText.includes('请选中一行数据！')`, 'single-selection warning')

await evaluate(`document.querySelector('.el-table__body-wrapper .el-checkbox__inner')?.click()`)
await waitFor(
  `Boolean(document.querySelector('.el-table__body-wrapper .el-checkbox__input.is-checked'))`,
  'selected nursing plan row'
)
await clickByText('.business-toolbar .toolbar-action', '新增宝宝')
await waitFor(`document.body.innerText.includes('新增宝宝信息')`, '新增宝宝信息')
await closeVisibleDialog()

const planDialogChecks = {}
for (const [action, title, fields] of [
  ['设置', '设置有效期', ['套餐内服务', '项目名称', '有效天数', '次数', '备注']],
  ['月嫂分配', '新增月嫂服务记录', ['选择客户：', '服务分店：', '选择护理师：', '服务类型：', '服务形式：', '执业类型：', '服务时间：', '服务天数：']],
  ['移动', '调整护理计划', ['当前护理计划项目', '项目移动的目标框', '妈妈护理项目', '护理计划框A']]
]) {
  await clickByText('.business-toolbar .toolbar-action', action)
  await waitFor(`document.body.innerText.includes(${JSON.stringify(title)})`, title)
  planDialogChecks[action] = await evaluate(
    `${JSON.stringify(fields)}.every(label => document.body.innerText.includes(label))`
  )
  await closeVisibleDialog()
}

await clickByText('.business-toolbar .toolbar-action', '确认完成')
await waitFor(`document.body.innerText.includes('护理计划确认')`, '护理计划确认')
const confirmationDialog = await evaluate(`[
  '客户姓名：', '项目名称：', '分店：', '查询', '打印', '确定完成',
  '日历', '列表', '白班', '休班', '晚班', '行政班'
].every(label => document.body.innerText.includes(label))`)

await send('Page.navigate', {
  url: 'http://localhost:9527/?toolbar-smoke=health#/nursing/item-5'
})
await waitFor(
  `document.querySelector('.page-heading h2')?.textContent.trim() === '健康评估'`,
  '健康评估'
)
const healthPlacement = await evaluate(`(() => {
  const expected = [
    '产妇入住评估新增', '宝宝入住评估新增', '产妇回家评估新增',
    '宝宝回家评估新增', '母婴指导评估新增'
  ]
  const actual = [...document.querySelectorAll('.filter-card .inline-business-action')]
    .map(item => item.textContent.trim())
  return {
    noTopToolbar: !document.querySelector('.business-toolbar'),
    hasSearch: [...document.querySelectorAll('.filter-card button')]
      .some(item => item.textContent.trim() === '搜  索'),
    actual,
    pass: JSON.stringify(actual) === JSON.stringify(expected)
  }
})()`)

const result = {
  toolbarChecks,
  queryChecks,
  planActions: {
    addDialog,
    zeroSelectionWarning: true,
    planDialogChecks,
    confirmationDialog
  },
  healthPlacement,
  runtimeErrors
}

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)

const failedToolbar = Object.values(toolbarChecks).some(item => !item.pass)
const failedQuery = Object.values(queryChecks).some(item => !item.pass)
const failedDialog = !addDialog || !confirmationDialog || Object.values(planDialogChecks).some(value => !value)
if (failedToolbar || failedQuery || failedDialog || !healthPlacement.pass || !healthPlacement.noTopToolbar || !healthPlacement.hasSearch || runtimeErrors.length) {
  process.exitCode = 1
}

socket.close()
