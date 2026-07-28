import { readFileSync } from 'node:fs'

const debugPort = process.argv[2]
const appPort = process.argv[3] || '9532'

if (!debugPort) {
  throw new Error('Usage: node scripts/smoke-audited-remaining-surfaces.mjs <debug-port> [app-port]')
}

const evidence = JSON.parse(
  readFileSync(new URL('../src/config/audited-legacy-surfaces.json', import.meta.url), 'utf8')
)
const moduleOrder = ['recovery', 'matron', 'diet', 'warehouse', 'mall', 'risk', 'basic']
const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

function parseDate(value) {
  const match = String(value || '').match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/)
  return match ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])) : null
}

function formatDate(date) {
  const pad = value => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function dynamicDateDefault(value) {
  const target = parseDate(value)
  const audited = parseDate(evidence.auditedOn)
  if (!target || !audited) return value || ''
  const today = new Date()
  if (
    target.getDate() === 1 &&
    target.getFullYear() === audited.getFullYear() &&
    target.getMonth() === audited.getMonth()
  ) {
    return formatDate(new Date(today.getFullYear(), today.getMonth(), 1))
  }
  const offset = Math.round((target.getTime() - audited.getTime()) / 86400000)
  today.setDate(today.getDate() + offset)
  return formatDate(today)
}

function fieldType(field) {
  const type = String(field.type || '').toLowerCase()
  if (['select', 'checkbox', 'radio'].includes(type)) return type
  const identity = `${field.id || ''} ${field.name || ''}`.toLowerCase()
  if (parseDate(field.value) || /(date|time|start|end|billdate|expecte)/.test(identity)) return 'date'
  return 'input'
}

function groupedRun(controls, start) {
  const first = controls[start]
  const type = fieldType(first)
  if (!['checkbox', 'radio'].includes(type)) return [first]
  const name = first.name || ''
  const run = [first]
  for (let index = start + 1; index < controls.length; index += 1) {
    const candidate = controls[index]
    if (fieldType(candidate) !== type || (candidate.name || '') !== name) break
    run.push(candidate)
  }
  return run
}

function cleanGroupLabel(type, label, options) {
  const text = String(label || '').trim()
  if (!text || type === 'checkbox') return ''
  if (options.some(option => option === text || text.includes(option))) return ''
  return text.length <= 20 ? text : ''
}

function expectedFields(controls) {
  const result = []
  for (let index = 0; index < controls.length;) {
    const field = controls[index]
    const type = fieldType(field)
    const run = groupedRun(controls, index)
    if (run.length > 1) {
      const options = run.map(item => item.label).filter(Boolean)
      const selected = run.filter(item => item.checked).map(item => item.label).filter(Boolean)
      result.push({
        label: cleanGroupLabel(type, field.groupLabel, options),
        type: `${type}-group`,
        options,
        value: type === 'radio' ? (selected[0] || '') : selected
      })
      index += run.length
      continue
    }
    let value = field.value && field.value !== '<non-empty>' ? field.value : ''
    if (type === 'select') value = (field.selected && field.selected[0]) || ''
    if (type === 'checkbox' || type === 'radio') value = Boolean(field.checked)
    if (type === 'date') value = dynamicDateDefault(value)
    result.push({
      label: field.label || '',
      type,
      options: field.options || [],
      value
    })
    index += 1
  }
  return result
}

async function getPageTarget() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const targets = await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(response => response.json())
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
    const resolver = pending.get(message.id)
    pending.delete(message.id)
    if (message.error) resolver.reject(new Error(message.error.message))
    else resolver.resolve(message.result)
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
    await delay(200)
  }
  throw new Error(`Timed out waiting for ${label}`)
}

await send('Page.enable')
await send('Runtime.enable')
await send('Network.enable')
await send('Page.navigate', { url: `http://127.0.0.1:${appPort}/` })
await delay(500)
await send('Network.setCookie', {
  name: 'Admin-Token',
  value: 'admin-token',
  url: `http://127.0.0.1:${appPort}/`,
  path: '/'
})

const checks = []
for (const moduleKey of moduleOrder) {
  const pages = evidence.modules[moduleKey]
  const titles = Object.keys(pages)
  for (let index = 0; index < titles.length; index += 1) {
    const title = titles[index]
    const schema = pages[title].schema
    const url = `http://127.0.0.1:${appPort}/?surface-smoke=${moduleKey}-${index + 1}#/${moduleKey}/item-${index + 1}`
    await send('Page.navigate', { url })
    if (moduleKey === 'risk') {
      await waitFor(
        `document.querySelector('.risk-service-matrix h1')?.textContent.trim() === ${JSON.stringify(title)}`,
        `${moduleKey}/${title}`
      )
      const riskActual = await evaluate(`(() => ({
        toolbar: [...document.querySelectorAll('[data-toolbar-action]')].map(item => item.textContent.trim()),
        query: [...document.querySelectorAll('[data-query-action]')].map(item => item.textContent.trim()),
        tableCount: document.querySelectorAll('.matrix-card .el-table').length,
        rowCount: document.querySelectorAll('.matrix-card .el-table__body-wrapper tbody tr').length,
        headers: [...document.querySelectorAll('.matrix-card:first-child .el-table__header-wrapper th')]
          .map(item => item.textContent.trim()).filter(Boolean)
      }))()`)
      const expectedRows = (schema.staticTables || []).reduce((total, table) => total + Math.max(0, table.length - 1), 0)
      const pass = (
        riskActual.toolbar.length === 0 &&
        riskActual.query.length === 0 &&
        riskActual.tableCount === (schema.staticTables || []).length &&
        riskActual.rowCount === expectedRows &&
        JSON.stringify(riskActual.headers) === JSON.stringify(['序号', '服务项目', '白银会员', '黄金会员'])
      )
      checks.push({ moduleKey, title, pass, expectedRows, actual: riskActual })
      continue
    }

    await waitFor(
      `document.querySelector('.audited-surface-panel')?.getAttribute('data-audited-title') === ${JSON.stringify(title)}`,
      `${moduleKey}/${title}`
    )
    await delay(80)
    const actual = await evaluate(`(() => ({
      toolbar: [...document.querySelectorAll('[data-toolbar-action]')].map(item => item.textContent.trim()),
      queryActions: [...document.querySelectorAll('[data-query-action]')].map(item => item.textContent.trim()),
      fields: [...document.querySelectorAll('[data-audited-query] .el-form-item[data-field]')].map(item => {
        const type = item.getAttribute('data-control-type')
        const formLabel = item.querySelector('.el-form-item__label')?.textContent.trim() || ''
        const choiceLabels = [...item.querySelectorAll('.el-checkbox__label, .el-radio__label')]
          .map(label => label.textContent.trim())
        let options = []
        let value = ''
        if (type === 'select') {
          const root = item.querySelector('.el-select')
          options = (root?.__vue__?.options || []).map(option => option.label)
          value = root?.querySelector('.el-input__inner')?.value || ''
        } else if (type === 'checkbox-group') {
          options = choiceLabels
          value = [...item.querySelectorAll('.el-checkbox.is-checked .el-checkbox__label')]
            .map(label => label.textContent.trim())
        } else if (type === 'radio-group') {
          options = choiceLabels
          value = item.querySelector('.el-radio.is-checked .el-radio__label')?.textContent.trim() || ''
        } else if (type === 'checkbox' || type === 'radio') {
          value = Boolean(item.querySelector('input')?.checked)
        } else {
          value = item.querySelector('input, textarea')?.value || ''
        }
        return {
          label: formLabel || (['checkbox', 'radio'].includes(type) ? choiceLabels[0] || '' : ''),
          type,
          options,
          value
        }
      })
    }))()`)
    const expected = {
      toolbar: (schema.toolbar || []).map(item => item.text),
      queryActions: schema.query.actions || [],
      fields: expectedFields(schema.query.controls || [])
    }
    checks.push({
      moduleKey,
      title,
      pass: JSON.stringify(actual) === JSON.stringify(expected),
      expected,
      actual
    })
  }
}

socket.close()
const failures = checks.filter(check => !check.pass)
const result = {
  pageCount: checks.length,
  passed: checks.length - failures.length,
  failed: failures.length,
  runtimeErrors: [...new Set(runtimeErrors)].filter(Boolean),
  failures
}
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
if (failures.length || result.runtimeErrors.length) process.exitCode = 1
