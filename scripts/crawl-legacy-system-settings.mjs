import { constants, publicEncrypt } from 'node:crypto'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

const BASE_URL = (process.env.LEGACY_ERP_BASE_URL || 'http://qd.mm.hxqt.cn').replace(/\/+$/, '')
const USERNAME = process.env.LEGACY_ERP_USER || ''
const PASSWORD = process.env.LEGACY_ERP_PASSWORD || ''
const OUTPUT_DIR = path.resolve(process.cwd(), '.private', 'system-settings-import')

const PUBLIC_KEY_BASE64 =
  'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCC0hrRIjb3noDWNtbDpANbjt5Iwu2NFeDwU16Ec87ToqeoIm2KI+cOs81JP9aTDk/jkAlU97mN8wZkEMDr5utAZtMVht7GLX33Wx9XjqxUsDfsGkqNL8dXJklWDu9Zh80Ui2Ug+340d5dZtKtd+nv09QZqGjdnSp9PTfFDBY133QIDAQAB'

const SYSTEM_PAGES = [
  ['部门管理', '/sys/Departments.aspx?navid=13'],
  ['角色管理', '/sys/RoleList.aspx?navid=11'],
  ['用户管理', '/sys/Users.aspx?navid=12'],
  ['数据字典', '/sys/datadic.aspx?navid=14'],
  ['审批流程', '/sys/ApprovalProcess.aspx?navid=316'],
  ['通知公告', '/OA/GongGao/GongGao.aspx?navid=290'],
  ['返利设置', '/Page/BasicInfo/RebateSetting.aspx?navid=477'],
  ['会所介绍', '/Page/BasicInfo/ClubIntroduce.aspx?navid=482'],
  ['导航菜单', '/sys/NavigationList.aspx?navid=10'],
  ['移动端导航', '/sys/NavigationListAPP.aspx?navid=674'],
  ['操作按钮', '/sys/ButtonList.aspx?navid=2'],
  ['操作日志', '/sys/logs.aspx?navid=15'],
  ['短信发送设置', '/Page/BasicInfo/SetUserForMsm.aspx?navid=280'],
  ['生日短信提醒', '/Page/BasicInfo/BrithdayRemind.aspx?navid=426'],
  ['消息发送日志', '/Page/BasicInfo/MsgSendLog.aspx?navid=439'],
  ['预警参数设置', '/Page/WarningManager/SetPrameter.aspx?navid=381'],
  ['报表模板自定义', '/Page/BasicInfo/ReportTemplet.aspx?navid=446'],
  ['模板设置', '/Page/BasicInfo/TemplateList.aspx?navid=672'],
  ['计划任务', '/Page/BasicInfo/PlanTaskList.aspx?navid=673'],
  ['系统参数设置', '/Page/WarningManager/SetSysPram.aspx?navid=384']
]

const SYSTEM_SETTING_NAV_IDS = [
  13, 11, 12, 14, 316, 290, 477, 482, 10, 674,
  2, 15, 280, 426, 439, 381, 446, 672, 673, 384
]

if (!USERNAME || !PASSWORD) {
  throw new Error('Missing LEGACY_ERP_USER or LEGACY_ERP_PASSWORD environment variable.')
}

const publicKey = [
  '-----BEGIN PUBLIC KEY-----',
  ...PUBLIC_KEY_BASE64.match(/.{1,64}/g),
  '-----END PUBLIC KEY-----'
].join('\n')

function encryptCredential(value) {
  return publicEncrypt(
    {
      key: publicKey,
      padding: constants.RSA_PKCS1_PADDING
    },
    Buffer.from(value, 'utf8')
  ).toString('base64')
}

function decodeHtmlEntities(value) {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
}

function parseAttributes(tag) {
  const attrs = {}
  for (const attr of tag.matchAll(/([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g)) {
    attrs[attr[1].toLowerCase()] = decodeHtmlEntities(attr[2] ?? attr[3] ?? attr[4] ?? '')
  }
  return attrs
}

function parseHiddenInputs(html) {
  const values = {}
  for (const match of html.matchAll(/<input\b[^>]*>/gi)) {
    const attrs = parseAttributes(match[0])
    if ((attrs.type || '').toLowerCase() === 'hidden' && attrs.name) {
      values[attrs.name] = attrs.value || ''
    }
  }
  return values
}

function stripHtml(value) {
  return decodeHtmlEntities(
    value
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  )
}

function parseRolePermissionPage(html, roleId, roleName, surface) {
  const catalog = []
  const grants = []
  const chunks = html.split(/(?=<div\b[^>]*class=["'][^"']*\blist\b[^"']*["'])/i).slice(1)

  for (const chunk of chunks) {
    const menuId = chunk.match(/selectAll\(this\s*,\s*(\d+)\s*\)/i)?.[1] || ''
    const strongHtml = chunk.match(/<strong\b[^>]*>([\s\S]*?)<\/strong>/i)?.[1] || ''
    const menuName = stripHtml(strongHtml).replace(/\s*\+\s*$/, '')
    if (!menuId || !menuName) continue

    for (const match of chunk.matchAll(
      /<label\b[^>]*>([\s\S]*?<input\b[^>]*onchange=["']save\(this\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)["'][^>]*>[\s\S]*?)<\/label>/gi
    )) {
      const buttonId = match[2]
      const observedMenuId = match[3]
      const observedRoleId = match[4]
      const buttonName = stripHtml(match[1])
      if (!buttonId || !buttonName) continue

      const row = {
        surface,
        menuId: observedMenuId || menuId,
        menuName,
        buttonId,
        buttonName
      }
      catalog.push(row)
      if (/\bchecked(?:\s|=|>)/i.test(match[0])) {
        grants.push({
          roleId: observedRoleId || String(roleId),
          roleName,
          ...row
        })
      }
    }
  }

  return { catalog, grants }
}

function isSensitiveField(name) {
  return /(password|passwd|pwd|passsalt|salt|hash|secret|token|private|apikey|api_key|accesskey|access_key|viewstate|eventvalidation|cookie|imei|validate)/i.test(name)
}

function resolvePageUrl(pagePath, candidate) {
  return new URL(candidate, new URL(pagePath, `${BASE_URL}/`)).href
}

function parsePageSchema(pageTitle, pagePath, html) {
  const controls = []
  const options = []
  const actions = []
  const headers = []
  const tableRows = []
  const scripts = []
  const inlineHints = []
  const inlineEndpoints = []
  const gridColumns = []

  for (const match of html.matchAll(/<input\b[^>]*>/gi)) {
    const attrs = parseAttributes(match[0])
    const type = (attrs.type || 'text').toLowerCase()
    const key = attrs.name || attrs.id || ''
    if (type === 'hidden' || isSensitiveField(key)) continue
    controls.push({
      pageTitle,
      pagePath,
      tag: 'input',
      type,
      id: attrs.id || '',
      name: attrs.name || '',
      value: attrs.value || '',
      placeholder: attrs.placeholder || '',
      checked: /\bchecked(?:\s|=|>)/i.test(match[0]) ? '1' : '0',
      disabled: /\bdisabled(?:\s|=|>)/i.test(match[0]) ? '1' : '0'
    })
  }

  for (const match of html.matchAll(/<textarea\b([^>]*)>([\s\S]*?)<\/textarea>/gi)) {
    const attrs = parseAttributes(`<textarea ${match[1]}>`)
    const key = attrs.name || attrs.id || ''
    if (isSensitiveField(key)) continue
    controls.push({
      pageTitle,
      pagePath,
      tag: 'textarea',
      type: 'textarea',
      id: attrs.id || '',
      name: attrs.name || '',
      value: stripHtml(match[2]),
      placeholder: attrs.placeholder || '',
      checked: '0',
      disabled: /\bdisabled(?:\s|=|>)/i.test(match[0]) ? '1' : '0'
    })
  }

  for (const match of html.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select>/gi)) {
    const attrs = parseAttributes(`<select ${match[1]}>`)
    const selectKey = attrs.name || attrs.id || ''
    if (isSensitiveField(selectKey)) continue
    controls.push({
      pageTitle,
      pagePath,
      tag: 'select',
      type: attrs.multiple != null ? 'select-multiple' : 'select-one',
      id: attrs.id || '',
      name: attrs.name || '',
      value: '',
      placeholder: '',
      checked: '0',
      disabled: /\bdisabled(?:\s|=|>)/i.test(match[0]) ? '1' : '0'
    })
    let optionIndex = 0
    for (const optionMatch of match[2].matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/gi)) {
      const optionAttrs = parseAttributes(`<option ${optionMatch[1]}>`)
      options.push({
        pageTitle,
        pagePath,
        selectId: attrs.id || '',
        selectName: attrs.name || '',
        optionIndex: optionIndex++,
        optionValue: optionAttrs.value || '',
        optionText: stripHtml(optionMatch[2]),
        selected: /\bselected(?:\s|=|>)/i.test(optionMatch[0]) ? '1' : '0',
        disabled: /\bdisabled(?:\s|=|>)/i.test(optionMatch[0]) ? '1' : '0'
      })
    }
  }

  for (const match of html.matchAll(/<(a|button)\b([^>]*)>([\s\S]*?)<\/\1>/gi)) {
    const attrs = parseAttributes(`<${match[1]} ${match[2]}>`)
    const text = stripHtml(match[3])
    if (!text) continue
    actions.push({
      pageTitle,
      pagePath,
      tag: match[1].toLowerCase(),
      text,
      id: attrs.id || '',
      href: attrs.href || '',
      onclick: (attrs.onclick || '').slice(0, 500)
    })
  }

  for (const match of html.matchAll(/<th\b[^>]*>([\s\S]*?)<\/th>/gi)) {
    const text = stripHtml(match[1])
    if (text && !headers.includes(text)) headers.push(text)
  }

  if (!['操作日志', '消息发送日志', '通知公告', '生日短信提醒'].includes(pageTitle)) {
    let tableIndex = 0
    for (const tableMatch of html.matchAll(/<table\b[^>]*>([\s\S]*?)<\/table>/gi)) {
      const tableHtml = tableMatch[1]
      const tableHeaders = [...tableHtml.matchAll(/<th\b[^>]*>([\s\S]*?)<\/th>/gi)]
        .map(match => stripHtml(match[1]))
        .filter(Boolean)
      if (tableHeaders.length === 0) {
        tableIndex++
        continue
      }
      let rowIndex = 0
      for (const rowMatch of tableHtml.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)) {
        const cells = [...rowMatch[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)]
          .map(match => stripHtml(match[1]))
        if (cells.length > 0 && cells.some(Boolean)) {
          tableRows.push({
            pageTitle,
            pagePath,
            tableIndex,
            rowIndex: rowIndex++,
            headers: tableHeaders.join(' | '),
            cells: JSON.stringify(cells)
          })
        }
      }
      tableIndex++
    }
  }

  for (const match of html.matchAll(/<script\b([^>]*)>/gi)) {
    const attrs = parseAttributes(`<script ${match[1]}>`)
    if (attrs.src) scripts.push(resolvePageUrl(pagePath, attrs.src))
  }

  let inlineIndex = 0
  let gridIndex = 0
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const attrs = parseAttributes(`<script ${match[1]}>`)
    if (attrs.src) continue
    const source = match[2]
    for (const endpointMatch of source.matchAll(/['"]([^'"]+\.(?:ashx|aspx)(?:\?[^'"]*)?)['"]/gi)) {
      const endpoint = decodeHtmlEntities(endpointMatch[1])
      if (!inlineEndpoints.includes(endpoint)) inlineEndpoints.push(endpoint)
    }
    for (const gridMatch of source.matchAll(
      /colNames\s*:\s*\[([\s\S]*?)\]\s*,\s*colModel\s*:\s*\[([\s\S]*?)\]\s*(?:,|\})/gi
    )) {
      const labels = [...gridMatch[1].matchAll(/['"]([^'"]*)['"]/g)].map(item => item[1])
      const models = [...gridMatch[2].matchAll(/\{([\s\S]*?)\}/g)].map(item => item[1])
      const count = Math.max(labels.length, models.length)
      for (let columnIndex = 0; columnIndex < count; columnIndex++) {
        const model = models[columnIndex] || ''
        const property = name => model.match(
          new RegExp(`\\b${name}\\s*:\\s*["']([^"']*)["']`, 'i')
        )?.[1] || ''
        const numericProperty = name => model.match(
          new RegExp(`\\b${name}\\s*:\\s*([\\d.]+)`, 'i')
        )?.[1] || ''
        gridColumns.push({
          pageTitle,
          pagePath,
          inlineIndex,
          gridIndex,
          columnIndex,
          label: labels[columnIndex] || '',
          fieldName: property('name'),
          indexName: property('index'),
          width: numericProperty('width'),
          align: property('align'),
          hidden: /\bhidden\s*:\s*true\b/i.test(model) ? '1' : '0'
        })
      }
      gridIndex++
    }
    const lines = source.split(/\r?\n/)
    let captured = 0
    for (let lineNumber = 0; lineNumber < lines.length && captured < 120; lineNumber++) {
      const line = lines[lineNumber].trim()
      if (!line || line.length > 2000) continue
      if (!/(?:url|api|ashx|requestMethod|ajax|grid|column|colNames|colModel|sortname|sortorder|sidx|sord|rowNum|dataSource|pageMethod|loadData|template|templet|webMethod|\bname\s*:)/i.test(line)) {
        continue
      }
      inlineHints.push({
        pageTitle,
        pagePath,
        inlineIndex,
        lineNumber: lineNumber + 1,
        line: line.slice(0, 2000)
      })
      captured++
    }
    inlineIndex++
  }

  return {
    inventory: {
      pageTitle,
      pagePath,
      authenticated: html.includes('请输入账号') ? '0' : '1',
      formAction: parseAttributes(html.match(/<form\b[^>]*>/i)?.[0] || '').action || '',
      controlCount: controls.length,
      optionCount: options.length,
      actionCount: actions.length,
      tableHeaders: headers.join(' | '),
      scriptCount: scripts.length
    },
    controls,
    options,
    actions,
    tableRows,
    scripts: [...new Set(scripts)],
    inlineHints,
    inlineEndpoints,
    gridColumns
  }
}

class CookieJar {
  constructor() {
    this.values = new Map()
  }

  absorb(headers) {
    const values = typeof headers.getSetCookie === 'function'
      ? headers.getSetCookie()
      : [headers.get('set-cookie')].filter(Boolean)

    for (const header of values) {
      const pair = header.split(';', 1)[0]
      const separator = pair.indexOf('=')
      if (separator > 0) {
        this.values.set(pair.slice(0, separator).trim(), pair.slice(separator + 1).trim())
      }
    }
  }

  toHeader() {
    return [...this.values.entries()].map(([name, value]) => `${name}=${value}`).join('; ')
  }
}

const jar = new CookieJar()

async function request(relativeUrl, options = {}, redirectDepth = 0) {
  if (redirectDepth > 10) {
    throw new Error(`Too many redirects while requesting ${relativeUrl}`)
  }

  const url = new URL(relativeUrl, `${BASE_URL}/`)
  const headers = new Headers(options.headers || {})
  headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138 Safari/537.36')
  headers.set('Accept-Language', 'zh-CN,zh;q=0.9')
  if (jar.toHeader()) headers.set('Cookie', jar.toHeader())

  const response = await fetch(url, {
    ...options,
    headers,
    redirect: 'manual',
    signal: options.signal || AbortSignal.timeout(20_000)
  })
  jar.absorb(response.headers)

  if (response.status >= 300 && response.status < 400) {
    const location = response.headers.get('location')
    if (!location) return response
    const nextMethod = response.status === 307 || response.status === 308
      ? options.method
      : 'GET'
    return request(new URL(location, url).href, {
      method: nextMethod,
      headers: nextMethod === 'GET' ? {} : headers,
      body: nextMethod === 'GET' ? undefined : options.body
    }, redirectDepth + 1)
  }

  return response
}

async function authenticate() {
  const loginPath = '/Page/Login/Login3.aspx'
  const loginPage = await request(loginPath)
  const loginHtml = await loginPage.text()
  const hidden = parseHiddenInputs(loginHtml)

  const form = new URLSearchParams({
    ...hidden,
    __EVENTTARGET: 'btnLogin',
    __EVENTARGUMENT: '',
    lgtype: '0',
    codeId: '',
    aurocodeId: '0',
    cookyzm: '',
    userLogin: encryptCredential(USERNAME),
    passWord: encryptCredential(PASSWORD)
  })

  await request(loginPath, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Referer: `${BASE_URL}${loginPath}`
    },
    body: form
  })

  const home = await request('/Default.aspx', {
    headers: { Referer: `${BASE_URL}${loginPath}` }
  })
  const homeHtml = await home.text()
  const authenticated = home.url.includes('/Default.aspx') &&
    !homeHtml.includes('请输入账号') &&
    homeHtml.includes('系统设置')

  if (!authenticated) {
    throw new Error('Legacy ERP authentication failed.')
  }
}

function asArray(value) {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.rows)) return value.rows
  if (value == null || value === '') return []
  throw new Error('Unexpected dictionary API payload shape.')
}

async function readJsonResponse(response, label) {
  const text = (await response.text()).replace(/^\uFEFF/, '').trim()
  if (!text) throw new Error(`${label} returned an empty response.`)
  try {
    return JSON.parse(text)
  } catch {
    const summary = text.startsWith('<')
      ? stripHtml(text).slice(0, 240)
      : text.slice(0, 240)
    throw new Error(`${label} did not return JSON${summary ? `: ${summary}` : '.'}`)
  }
}

async function fetchDictionary() {
  const categoriesResponse = await request('/sys/ashx/dichandler.ashx?action=category&Keyword=', {
    method: 'GET',
    headers: { Referer: `${BASE_URL}/sys/datadic.aspx?navid=14` }
  })
  const categoryPayload = await readJsonResponse(categoriesResponse, 'Dictionary category query')
  const categories = asArray(categoryPayload)

  const items = []
  for (const category of categories) {
    const response = await request('/sys/ashx/dichandler.ashx', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        Referer: `${BASE_URL}/sys/datadic.aspx?navid=14`,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: new URLSearchParams({ categoryId: String(category.id) })
    })
    const rows = asArray(await readJsonResponse(response, `Dictionary item query ${category.id}`))
    for (const row of rows) {
      items.push({
        categoryId: String(category.id),
        categoryTitle: category.text || '',
        categoryCode: category.attributes?.Code || '',
        ...row
      })
    }
  }

  return { categories, items }
}

async function fetchSystemPageInventory() {
  const inventory = []
  const controls = []
  const options = []
  const actions = []
  const tableRows = []
  const pageScripts = []
  const inlineHints = []
  const scriptEndpoints = []
  const gridColumns = []

  for (const [pageTitle, pagePath] of SYSTEM_PAGES) {
    const response = await request(pagePath, {
      headers: { Referer: `${BASE_URL}/Default.aspx` }
    })
    const html = await response.text()
    const schema = parsePageSchema(pageTitle, pagePath, html)
    inventory.push(schema.inventory)
    controls.push(...schema.controls)
    options.push(...schema.options)
    actions.push(...schema.actions)
    tableRows.push(...schema.tableRows)
    inlineHints.push(...schema.inlineHints)
    gridColumns.push(...schema.gridColumns)

    for (const endpoint of schema.inlineEndpoints) {
      scriptEndpoints.push({
        pageTitle,
        pagePath,
        scriptUrl: '[inline]',
        endpoint
      })
    }

    for (const scriptUrl of schema.scripts) {
      pageScripts.push({ pageTitle, pagePath, scriptUrl })
      if (!scriptUrl.startsWith(`${BASE_URL}/`)) continue
      if (/\/Common\/|jquery|easyui|layer|lodop|timer/i.test(scriptUrl)) continue
      let source = ''
      try {
        const scriptResponse = await request(scriptUrl, {
          headers: { Referer: new URL(pagePath, `${BASE_URL}/`).href }
        })
        source = await scriptResponse.text()
      } catch {
        continue
      }
      const seen = new Set()
      for (const match of source.matchAll(/['"]([^'"]+\.(?:ashx|aspx)(?:\?[^'"]*)?)['"]/gi)) {
        const endpoint = decodeHtmlEntities(match[1])
        if (seen.has(endpoint)) continue
        seen.add(endpoint)
        scriptEndpoints.push({
          pageTitle,
          pagePath,
          scriptUrl,
          endpoint
        })
      }
    }
  }

  return {
    inventory,
    controls,
    options,
    actions,
    tableRows,
    pageScripts,
    inlineHints,
    scriptEndpoints,
    gridColumns
  }
}

function sanitizeRecord(record) {
  const output = {}
  for (const [key, value] of Object.entries(record || {})) {
    if (isSensitiveField(key)) continue
    output[key] = value
  }
  return output
}

function flattenTreeRows(rows, parentKeyId = '', depth = 0, output = []) {
  for (const row of rows) {
    const children = Array.isArray(row?.children)
      ? row.children
      : Array.isArray(row?.Children)
        ? row.Children
        : []
    const clean = sanitizeRecord(row)
    delete clean.children
    delete clean.Children
    output.push({
      _parentKeyId: parentKeyId,
      _depth: depth,
      ...clean
    })
    const rowId = row?.KeyId ?? row?.id ?? row?.keyid ?? ''
    flattenTreeRows(children, String(rowId), depth + 1, output)
  }
  return output
}

function mapCellRows(rows, columns) {
  return rows.map(row => {
    if (!Array.isArray(row.cell)) return row
    const mapped = { ...row }
    delete mapped.cell
    for (let index = 0; index < columns.length; index++) {
      mapped[columns[index]] = row.cell[index] ?? ''
    }
    return mapped
  })
}

async function queryConfigRows(label, relativeUrl, {
  method = 'POST',
  body = {},
  referer = '/Default.aspx'
} = {}) {
  const requestBody = method === 'GET' ? undefined : new URLSearchParams(body)
  const response = await request(relativeUrl, {
    method,
    headers: {
      ...(method === 'GET'
        ? {}
        : { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' }),
      Referer: new URL(referer, `${BASE_URL}/`).href,
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: requestBody
  })
  const payload = await readJsonResponse(response, label)
  return flattenTreeRows(asArray(payload))
}

async function fetchCoreConfigDatasets() {
  const datasets = {}
  const status = []
  const specs = [
    {
      key: 'departments',
      label: '部门管理',
      path: '/sys/ashx/departmenthandler.ashx',
      referer: '/sys/Departments.aspx?navid=13'
    },
    {
      key: 'roles',
      label: '角色管理',
      path: '/sys/ashx/rolehandler.ashx',
      referer: '/sys/RoleList.aspx?navid=11'
    },
    {
      key: 'users',
      label: '用户管理',
      path: `/sys/ashx/userhandler.ashx?json=${encodeURIComponent(JSON.stringify({
        jsonEntity: '[]',
        action: 'getLoginNew',
        keyid: null
      }))}&islogin=0`,
      body: { page: '1', rows: '5000' },
      referer: '/sys/Users.aspx?navid=12'
    },
    {
      key: 'navigation',
      label: '导航菜单',
      path: '/sys/ashx/NavigationHandler.ashx',
      referer: '/sys/NavigationList.aspx?navid=10'
    },
    {
      key: 'mobileNavigation',
      label: '移动端导航',
      path: '/sys/ashx/NavigationAPPHandler.ashx',
      referer: '/sys/NavigationListAPP.aspx?navid=674'
    },
    {
      key: 'buttons',
      label: '操作按钮',
      path: '/sys/ashx/ButtonHandler.ashx',
      body: { page: '1', rows: '5000' },
      referer: '/sys/ButtonList.aspx?navid=2'
    },
    {
      key: 'warningParameters',
      label: '预警参数设置',
      path: '/Page/WarningManager/ajax/GetData.aspx?requestMethod=GetPramter&page=1&rows=5000&sidx=KeyId&sord=asc',
      method: 'GET',
      columns: ['KeyId', 'warningId', 'warningName', 'waringNum', 'remark'],
      referer: '/Page/WarningManager/SetPrameter.aspx?navid=381'
    },
    {
      key: 'reportTemplates',
      label: '报表模板自定义',
      path: '/Page/BasicInfo/ajax/GetData.aspx?requestMethod=GetReportTemplet&page=1&rows=5000&sidx=id&sord=asc',
      method: 'GET',
      columns: ['id', 'TypeName', 'Title', 'Memo', 'Creater', 'CreateDate', 'Sort', 'shopname'],
      referer: '/Page/BasicInfo/ReportTemplet.aspx?navid=446'
    },
    {
      key: 'templates',
      label: '模板设置',
      path: '/Page/BasicInfo/ajax/GetData.aspx?RequestMethod=GetTemplateList&page=1&rows=5000&sidx=id&sord=desc',
      method: 'GET',
      columns: ['id', 'TempName', 'TempCode', 'TemplateId', 'TypeName', 'TempFiled', 'TempExplain', 'Remark'],
      referer: '/Page/BasicInfo/TemplateList.aspx?navid=672'
    },
    {
      key: 'planTasks',
      label: '计划任务',
      path: '/Page/BasicInfo/ajax/GetData.aspx?RequestMethod=GetPlanTaskList&page=1&rows=5000&sidx=id&sord=asc',
      method: 'GET',
      columns: ['id', 'TaskCode', 'TaskTitle', 'StartTime', 'EndTime', 'IntervalDays', 'RecipientType', 'Recipient', 'MContent'],
      referer: '/Page/BasicInfo/PlanTaskList.aspx?navid=673'
    },
    {
      key: 'systemParameters',
      label: '系统参数设置',
      path: '/Page/WarningManager/ajax/GetData.aspx?requestMethod=GetSetPram&page=1&rows=5000&sidx=KeyId&sord=asc',
      method: 'GET',
      columns: ['KeyId', 'SysType', 'SysName', 'SysValue', 'remark', 'SysLeavel', 'ntype'],
      referer: '/Page/WarningManager/SetSysPram.aspx?navid=384'
    }
  ]

  for (const spec of specs) {
    try {
      const queriedRows = await queryConfigRows(spec.label, spec.path, {
        method: spec.method || 'POST',
        body: { page: '1', rows: '5000', ...(spec.body || {}) },
        referer: spec.referer
      })
      const rows = spec.columns ? mapCellRows(queriedRows, spec.columns) : queriedRows
      datasets[spec.key] = rows
      status.push({ dataset: spec.key, pageTitle: spec.label, status: 'ok', rowCount: rows.length, error: '' })
    } catch (error) {
      datasets[spec.key] = []
      status.push({
        dataset: spec.key,
        pageTitle: spec.label,
        status: 'error',
        rowCount: 0,
        error: String(error.message || error).slice(0, 500)
      })
    }
  }

  try {
    const categoriesResponse = await request('/sys/ashx/ApprovalProcessHandler.ashx?action=category', {
      method: 'GET',
      headers: { Referer: `${BASE_URL}/sys/ApprovalProcess.aspx?navid=316` }
    })
    const categories = asArray(await readJsonResponse(categoriesResponse, '审批流程类别'))
    const categoryRows = flattenTreeRows(categories)
    datasets.approvalCategories = categoryRows
    const processRows = []
    for (const category of categories) {
      const rows = await queryConfigRows(
        `审批流程 ${category.id}`,
        '/sys/ashx/ApprovalProcessHandler.ashx',
        {
          body: { categoryId: String(category.id) },
          referer: '/sys/ApprovalProcess.aspx?navid=316'
        }
      )
      for (const row of rows) {
        processRows.push({
          categoryId: category.id,
          categoryTitle: category.text || '',
          ...row
        })
      }
    }
    datasets.approvalProcesses = processRows
    status.push({
      dataset: 'approvalCategories',
      pageTitle: '审批流程',
      status: 'ok',
      rowCount: categoryRows.length,
      error: ''
    })
    status.push({
      dataset: 'approvalProcesses',
      pageTitle: '审批流程',
      status: 'ok',
      rowCount: processRows.length,
      error: ''
    })
  } catch (error) {
    datasets.approvalCategories = []
    datasets.approvalProcesses = []
    status.push({
      dataset: 'approvalProcesses',
      pageTitle: '审批流程',
      status: 'error',
      rowCount: 0,
      error: String(error.message || error).slice(0, 500)
    })
  }

  try {
    const smsPageResponse = await request('/Page/BasicInfo/SetUserForMsm.aspx?navid=280', {
      headers: { Referer: `${BASE_URL}/Default.aspx` }
    })
    const smsHtml = await smsPageResponse.text()
    const smsNodes = []
    for (const match of smsHtml.matchAll(/<tr\b([^>]*)\bname=["']ShowFL["']([^>]*)>([\s\S]*?)<\/tr>/gi)) {
      const attrs = parseAttributes(`<tr ${match[1]} name="ShowFL" ${match[2]}>`)
      const code = stripHtml(match[3].match(/<span\b[^>]*name=["']smsCode["'][^>]*>([\s\S]*?)<\/span>/i)?.[1] || '')
      const name = stripHtml(match[3].match(/<span\b[^>]*name=["']smsName["'][^>]*>([\s\S]*?)<\/span>/i)?.[1] || '')
      smsNodes.push({
        id: attrs.mid || '',
        sortnum: attrs.sortnum || '',
        code,
        name,
        template: attrs.msgsms || ''
      })
    }
    const smsStores = []
    for (const match of smsHtml.matchAll(/<tr\b([^>]*)\bname=["']DepartmentNameTr["']([^>]*)>([\s\S]*?)<\/tr>/gi)) {
      const attrs = parseAttributes(`<tr ${match[1]} name="DepartmentNameTr" ${match[2]}>`)
      smsStores.push({
        storeId: attrs.keyid || '',
        storeName: stripHtml(match[3])
      })
    }
    const smsAssignments = []
    for (const node of smsNodes) {
      for (const store of smsStores) {
        const smsQuery = new URLSearchParams({
          SMSBoxID: node.id,
          DepartmentNameID: store.storeId,
          RequestMethod: 'GetUserList'
        })
        const response = await request(`/Page/BasicInfo/ashx/GetData.ashx?${smsQuery}`, {
          method: 'GET',
          headers: {
            Referer: `${BASE_URL}/Page/BasicInfo/SetUserForMsm.aspx?navid=280`,
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        const text = (await response.text()).replace(/^\uFEFF/, '').trim()
        let assignmentRows = []
        try {
          assignmentRows = asArray(JSON.parse(text))
        } catch {
          const summary = stripHtml(text)
          if (summary) {
            const selectedNames = summary.includes('|')
              ? summary
                  .split('|')
                  .slice(1)
                  .join('|')
                  .split(/[,，]/)
                  .map(value => value.trim())
                  .filter(Boolean)
              : []
            assignmentRows = selectedNames.length > 0
              ? selectedNames.map(recipientName => ({ recipientName }))
              : [{
                  responseText: /服务器错误|Exception|堆栈跟踪/.test(summary)
                    ? 'server_error'
                    : summary.slice(0, 2000)
                }]
          }
        }
        if (assignmentRows.length === 0) {
          smsAssignments.push({
            smsNodeId: node.id,
            smsCode: node.code,
            storeId: store.storeId,
            storeName: store.storeName,
            assignmentCount: 0
          })
          continue
        }
        for (const assignment of assignmentRows) {
          const matchedUser = assignment.recipientName
            ? datasets.users.find(user => String(user.TrueName || '').trim() === assignment.recipientName)
            : null
          smsAssignments.push({
            smsNodeId: node.id,
            smsCode: node.code,
            storeId: store.storeId,
            storeName: store.storeName,
            assignmentCount: assignmentRows.length,
            userKeyId: matchedUser?.KeyId || '',
            ...sanitizeRecord(assignment)
          })
        }
      }
    }
    datasets.smsNodes = smsNodes
    datasets.smsAssignments = smsAssignments
    status.push({
      dataset: 'smsNodes',
      pageTitle: '短信发送设置',
      status: 'ok',
      rowCount: smsNodes.length,
      error: ''
    })
    status.push({
      dataset: 'smsAssignments',
      pageTitle: '短信发送设置',
      status: 'ok',
      rowCount: smsAssignments.length,
      error: ''
    })
  } catch (error) {
    datasets.smsNodes = []
    datasets.smsAssignments = []
    status.push({
      dataset: 'smsNodes',
      pageTitle: '短信发送设置',
      status: 'error',
      rowCount: 0,
      error: String(error.message || error).slice(0, 500)
    })
  }

  try {
    const rebateResponse = await request(
      '/Page/BasicInfo/ajax/UpData.aspx?requestMethod=GetCustomerRebateSettingInfo',
      {
        method: 'GET',
        headers: {
          Referer: `${BASE_URL}/Page/BasicInfo/RebateSetting.aspx?navid=477`,
          'X-Requested-With': 'XMLHttpRequest'
        }
      }
    )
    const rebatePayload = await readJsonResponse(rebateResponse, '返利设置')
    let rebateData = rebatePayload?.data ?? rebatePayload?.rows ?? rebatePayload
    if (typeof rebateData === 'string') {
      try {
        rebateData = JSON.parse(rebateData)
      } catch {
        rebateData = [{ value: rebateData }]
      }
    }
    const rebateRows = (Array.isArray(rebateData) ? rebateData : [rebateData])
      .filter(value => value && typeof value === 'object')
      .map(sanitizeRecord)
    datasets.rebateSettings = rebateRows
    status.push({
      dataset: 'rebateSettings',
      pageTitle: '返利设置',
      status: 'ok',
      rowCount: rebateRows.length,
      error: ''
    })

    const rebatePagePath = '/Page/BasicInfo/RebateSetting.aspx?navid=477'
    const rebatePageResponse = await request(rebatePagePath, {
      headers: { Referer: `${BASE_URL}/Default.aspx` }
    })
    const rebatePageHtml = await rebatePageResponse.text()
    const rebateSchema = parsePageSchema('返利设置', rebatePagePath, rebatePageHtml)
    const rebateControls = new Map(rebateSchema.controls.map(control => [control.id, control]))
    datasets.rebateCategorySettings = [
      ['FW', '服务销售', 'chkFw', 'FW', 'txtFWValue'],
      ['WL', '物料销售', 'chkWl', 'WL', 'txtWLValue'],
      ['SS', '膳食销售', 'chkSs', 'SS', 'txtSSValue'],
      ['KL', '卡类销售', 'chkKl', 'Kl', 'txtKLValue'],
      ['HT', '合同销售', 'chkHt', 'Ht', 'txtHTValue'],
      ['HY', '会员充值', 'chkHy', 'Hy', 'txtHyValue'],
      ['XF', '续房收款', 'chkXf', 'Xf', 'txtXFValue']
    ].map(([code, categoryName, checkboxId, radioToken, valueId]) => {
      const enabledControl = rebateControls.get(checkboxId)
      const percentControl = rebateControls.get(
        `ctl00_ContentPlaceHolder1_rbl${radioToken}Bl`
      )
      const fixedControl = rebateControls.get(
        `ctl00_ContentPlaceHolder1_rbl${radioToken}Je`
      )
      const valueControl = rebateControls.get(valueId)
      const mode = percentControl?.checked === '1'
        ? 'percentage'
        : fixedControl?.checked === '1'
          ? 'fixed_amount'
          : ''
      return {
        categoryCode: code,
        categoryName,
        enabled: enabledControl?.checked || '0',
        mode,
        modeValue: percentControl?.checked === '1'
          ? percentControl.value
          : fixedControl?.checked === '1'
            ? fixedControl.value
            : '',
        rebateValue: valueControl?.value || '',
        inputHint: '按百分比输入小数，按固定值输入数字'
      }
    })
    status.push({
      dataset: 'rebateCategorySettings',
      pageTitle: '返利设置-业务类别',
      status: 'ok',
      rowCount: datasets.rebateCategorySettings.length,
      error: ''
    })
  } catch (error) {
    datasets.rebateSettings = []
    datasets.rebateCategorySettings = []
    status.push({
      dataset: 'rebateSettings',
      pageTitle: '返利设置',
      status: 'error',
      rowCount: 0,
      error: String(error.message || error).slice(0, 500)
    })
  }

  try {
    const clubPath = '/Page/BasicInfo/ClubIntroduce.aspx?navid=482'
    const clubResponse = await request(clubPath, {
      headers: { Referer: `${BASE_URL}/Default.aspx` }
    })
    const clubHtml = await clubResponse.text()
    const schema = parsePageSchema('会所介绍', clubPath, clubHtml)
    const controls = new Map(schema.controls.map(control => [control.id, control]))
    const imagePath = clubHtml.match(
      /\bvar\s+environmenUrl\s*=\s*["']([^"']*)["']/i
    )?.[1] || ''
    datasets.clubProfile = [{
      clubName: controls.get('txtName')?.value || '',
      city: controls.get('txtCity')?.value || '',
      address: controls.get('txtAddress')?.value || '',
      telephone: controls.get('txtTel')?.value || '',
      introduction: controls.get('ctl00_ContentPlaceHolder1_txtRemark')?.value || '',
      imagePath
    }]
    status.push({
      dataset: 'clubProfile',
      pageTitle: '会所介绍',
      status: 'ok',
      rowCount: 1,
      error: ''
    })
  } catch (error) {
    datasets.clubProfile = []
    status.push({
      dataset: 'clubProfile',
      pageTitle: '会所介绍',
      status: 'error',
      rowCount: 0,
      error: String(error.message || error).slice(0, 500)
    })
  }

  datasets.recordHandlingSummary = [
    {
      pageTitle: '通知公告',
      handling: 'schema_and_count_only',
      storedRecords: 0,
      reason: '公告正文属于真实业务记录；仅保留列表字段和查询结构。'
    },
    {
      pageTitle: '生日短信提醒',
      handling: 'schema_only',
      storedRecords: 0,
      reason: '结果包含客户姓名、电话、生日及短信内容；不复制客户记录。'
    },
    {
      pageTitle: '操作日志',
      handling: 'schema_only',
      storedRecords: 0,
      reason: '仅保留操作日志的筛选项和列表结构。'
    },
    {
      pageTitle: '消息发送日志',
      handling: 'schema_only',
      storedRecords: 0,
      reason: '仅保留消息日志的筛选项和列表结构。'
    }
  ]
  status.push({
    dataset: 'recordHandlingSummary',
    pageTitle: '真实记录安全边界',
    status: 'ok',
    rowCount: datasets.recordHandlingSummary.length,
    error: ''
  })

  try {
    const roleByName = new Map(datasets.roles.map(role => [String(role.RoleName || '').trim(), role]))
    datasets.userRoleRelations = datasets.users.flatMap(user => {
      const names = String(user.RoleName || '')
        .split(/[,，]/)
        .map(value => value.trim())
        .filter(Boolean)
      return names.map(roleName => ({
        userKeyId: user.KeyId || '',
        userName: user.UserName || '',
        trueName: user.TrueName || '',
        roleKeyId: roleByName.get(roleName)?.KeyId || '',
        roleName
      }))
    })
    status.push({
      dataset: 'userRoleRelations',
      pageTitle: '用户管理',
      status: 'ok',
      rowCount: datasets.userRoleRelations.length,
      error: ''
    })

    const webCatalog = new Map()
    const appCatalog = new Map()
    const webGrants = []
    const appGrants = []

    const rolePermissionChecks = datasets.roles.flatMap(role => {
      const roleId = String(role.KeyId || '')
      if (!roleId) return []
      return [
        { role, surface: 'web', path: `/sys/RoleEdit.aspx?id=${encodeURIComponent(roleId)}` },
        { role, surface: 'app', path: `/sys/RoleAppEdit.aspx?id=${encodeURIComponent(roleId)}` }
      ]
    })
    const rolePermissionConcurrency = 6
    for (let offset = 0; offset < rolePermissionChecks.length; offset += rolePermissionConcurrency) {
      const batch = rolePermissionChecks.slice(offset, offset + rolePermissionConcurrency)
      const results = await Promise.all(batch.map(async spec => {
        const response = await request(spec.path, {
          headers: { Referer: `${BASE_URL}/sys/RoleList.aspx?navid=11` }
        })
        const html = await response.text()
        if (/Login3\.aspx|用户登录|name=["']username["']/i.test(html)) {
          throw new Error(
            `Authentication expired while reading ${spec.surface} permissions for role ${spec.role.KeyId}.`
          )
        }
        return {
          spec,
          parsed: parseRolePermissionPage(
            html,
            spec.role.KeyId,
            spec.role.RoleName,
            spec.surface
          )
        }
      }))

      for (const { spec, parsed } of results) {
        const targetCatalog = spec.surface === 'web' ? webCatalog : appCatalog
        const targetGrants = spec.surface === 'web' ? webGrants : appGrants
        for (const row of parsed.catalog) {
          targetCatalog.set(`${row.menuId}:${row.buttonId}`, row)
        }
        targetGrants.push(...parsed.grants)
      }
    }

    datasets.roleWebPermissionCatalog = [...webCatalog.values()]
    datasets.roleWebPermissionGrants = webGrants
    datasets.roleAppPermissionCatalog = [...appCatalog.values()]
    datasets.roleAppPermissionGrants = appGrants
    for (const [dataset, pageTitle, rows] of [
      ['roleWebPermissionCatalog', '角色管理-后台权限目录', datasets.roleWebPermissionCatalog],
      ['roleWebPermissionGrants', '角色管理-后台授权关系', datasets.roleWebPermissionGrants],
      ['roleAppPermissionCatalog', '角色管理-移动端权限目录', datasets.roleAppPermissionCatalog],
      ['roleAppPermissionGrants', '角色管理-移动端授权关系', datasets.roleAppPermissionGrants]
    ]) {
      status.push({ dataset, pageTitle, status: 'ok', rowCount: rows.length, error: '' })
    }

    const navigationById = new Map(
      datasets.navigation.map(item => [String(item.KeyId || ''), String(item.NavTitle || '')])
    )
    const dataScopeRows = []
    let dataScopeErrors = 0
    const systemSettingNavIds = new Set(SYSTEM_SETTING_NAV_IDS.map(String))
    const roleById = new Map(datasets.roles.map(role => [String(role.KeyId || ''), role]))
    const checks = []
    const seenChecks = new Set()
    for (const grant of webGrants) {
      if (!systemSettingNavIds.has(String(grant.menuId))) continue
      const role = roleById.get(String(grant.roleId))
      if (!role) continue
      const key = `${role.KeyId}:${grant.menuId}`
      if (seenChecks.has(key)) continue
      seenChecks.add(key)
      checks.push({ role, navId: Number(grant.menuId) })
    }
    const concurrency = 16
    for (let offset = 0; offset < checks.length; offset += concurrency) {
      const batch = checks.slice(offset, offset + concurrency)
      const results = await Promise.all(batch.map(async ({ role, navId }) => {
        const query = new URLSearchParams({
          act: 'navlist',
          rid: String(role.KeyId || ''),
          nid: String(navId),
          tid: '0'
        })
        try {
          const response = await request(`/sys/ashx/PermissionsDetails.ashx?${query}`, {
            headers: {
              Referer: `${BASE_URL}/sys/DataPermissionsDetails.aspx?tid=0&rid=${encodeURIComponent(role.KeyId || '')}`,
              'X-Requested-With': 'XMLHttpRequest'
            }
          })
          const payload = await readJsonResponse(
            response,
            `数据权限 role=${role.KeyId} nav=${navId}`
          )
          return {
            role,
            navId,
            rows: asArray(payload?.data ?? payload)
          }
        } catch {
          return { role, navId, rows: null }
        }
      }))

      for (const result of results) {
        if (result.rows == null) {
          dataScopeErrors++
          continue
        }
        if (result.rows.length === 0) {
          dataScopeRows.push({
            roleId: result.role.KeyId || '',
            roleName: result.role.RoleName || '',
            navId: result.navId,
            navTitle: navigationById.get(String(result.navId)) || '',
            departmentId: '',
            parentDepartmentId: '',
            departmentName: '',
            granted: '0',
            emptyResult: '1'
          })
          continue
        }
        for (const row of result.rows) {
          dataScopeRows.push({
            roleId: result.role.KeyId || '',
            roleName: result.role.RoleName || '',
            navId: result.navId,
            navTitle: navigationById.get(String(result.navId)) || '',
            departmentId: row.id ?? row.KeyId ?? '',
            parentDepartmentId: row.pId ?? row.ParentId ?? '',
            departmentName: row.name ?? row.Title ?? '',
            granted: row.checked === true || row.checked === 1 || row.checked === '1' ? '1' : '0',
            emptyResult: '0'
          })
        }
      }
    }
    datasets.roleSystemSettingDataScopes = dataScopeRows
    status.push({
      dataset: 'roleSystemSettingDataScopes',
      pageTitle: '角色管理-系统设置数据权限',
      status: dataScopeErrors === 0 ? 'ok' : 'partial',
      rowCount: dataScopeRows.length,
      error: dataScopeErrors === 0 ? '' : `${dataScopeErrors} read-only permission queries failed`
    })
  } catch (error) {
    for (const key of [
      'userRoleRelations',
      'roleWebPermissionCatalog',
      'roleWebPermissionGrants',
      'roleAppPermissionCatalog',
      'roleAppPermissionGrants',
      'roleSystemSettingDataScopes'
    ]) {
      datasets[key] = datasets[key] || []
    }
    status.push({
      dataset: 'rolePermissionRelations',
      pageTitle: '角色管理',
      status: 'error',
      rowCount: 0,
      error: String(error.message || error).slice(0, 500)
    })
  }

  return { datasets, status }
}

function csvCell(value) {
  const text = value == null
    ? ''
    : typeof value === 'object'
      ? JSON.stringify(value)
      : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

function toCsv(rows, columns) {
  return [
    columns.map(csvCell).join(','),
    ...rows.map(row => columns.map(column => csvCell(row[column])).join(','))
  ].join('\r\n')
}

function columnsForRows(rows) {
  const keys = []
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!keys.includes(key) && !isSensitiveField(key)) keys.push(key)
    }
  }
  return keys
}

await authenticate()
const dictionary = await fetchDictionary()
const systemPages = await fetchSystemPageInventory()
const coreConfig = await fetchCoreConfigDatasets()
await mkdir(OUTPUT_DIR, { recursive: true })

const categoryRows = dictionary.categories.map(category => ({
  id: category.id,
  title: category.text || '',
  code: category.attributes?.Code || '',
  sortnum: category.attributes?.Sortnum ?? '',
  remark: category.attributes?.Remark || ''
}))

const itemColumns = [
  'categoryId',
  'categoryTitle',
  'categoryCode',
  'KeyId',
  'ParentId',
  'Title',
  'Code',
  'Sortnum',
  'Status',
  'ShopID',
  'Remark',
  'Fnote1',
  'Fnote2',
  'Fnote3',
  'Fnote4'
]

await writeFile(
  path.join(OUTPUT_DIR, 'data-dictionary-categories.csv'),
  `\uFEFF${toCsv(categoryRows, ['id', 'title', 'code', 'sortnum', 'remark'])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-inventory.csv'),
  `\uFEFF${toCsv(systemPages.inventory, [
    'pageTitle',
    'pagePath',
    'authenticated',
    'formAction',
    'controlCount',
    'optionCount',
    'actionCount',
    'tableHeaders',
    'scriptCount'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-controls.csv'),
  `\uFEFF${toCsv(systemPages.controls, [
    'pageTitle',
    'pagePath',
    'tag',
    'type',
    'id',
    'name',
    'value',
    'placeholder',
    'checked',
    'disabled'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-options.csv'),
  `\uFEFF${toCsv(systemPages.options, [
    'pageTitle',
    'pagePath',
    'selectId',
    'selectName',
    'optionIndex',
    'optionValue',
    'optionText',
    'selected',
    'disabled'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-actions.csv'),
  `\uFEFF${toCsv(systemPages.actions, [
    'pageTitle',
    'pagePath',
    'tag',
    'text',
    'id',
    'href',
    'onclick'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-server-table-rows.csv'),
  `\uFEFF${toCsv(systemPages.tableRows, [
    'pageTitle',
    'pagePath',
    'tableIndex',
    'rowIndex',
    'headers',
    'cells'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-inline-hints.csv'),
  `\uFEFF${toCsv(systemPages.inlineHints, [
    'pageTitle',
    'pagePath',
    'inlineIndex',
    'lineNumber',
    'line'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-scripts.csv'),
  `\uFEFF${toCsv(systemPages.pageScripts, [
    'pageTitle',
    'pagePath',
    'scriptUrl'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-script-endpoints.csv'),
  `\uFEFF${toCsv(systemPages.scriptEndpoints, [
    'pageTitle',
    'pagePath',
    'scriptUrl',
    'endpoint'
  ])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'system-page-grid-columns.csv'),
  `\uFEFF${toCsv(systemPages.gridColumns, [
    'pageTitle',
    'pagePath',
    'inlineIndex',
    'gridIndex',
    'columnIndex',
    'label',
    'fieldName',
    'indexName',
    'width',
    'align',
    'hidden'
  ])}`,
  'utf8'
)
for (const [dataset, rows] of Object.entries(coreConfig.datasets)) {
  const columns = columnsForRows(rows)
  await writeFile(
    path.join(OUTPUT_DIR, `config-${dataset}.csv`),
    `\uFEFF${toCsv(rows, columns)}`,
    'utf8'
  )
}
await writeFile(
  path.join(OUTPUT_DIR, 'config-dataset-status.csv'),
  `\uFEFF${toCsv(coreConfig.status, ['dataset', 'pageTitle', 'status', 'rowCount', 'error'])}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'data-dictionary-items.csv'),
  `\uFEFF${toCsv(dictionary.items, itemColumns)}`,
  'utf8'
)
await writeFile(
  path.join(OUTPUT_DIR, 'manifest.txt'),
  [
    `captured_at=${new Date().toISOString()}`,
    `base_url=${BASE_URL}`,
    `dictionary_category_count=${dictionary.categories.length}`,
    `dictionary_item_count=${dictionary.items.length}`,
    `system_page_count=${systemPages.inventory.length}`,
    `system_control_count=${systemPages.controls.length}`,
    `system_option_count=${systemPages.options.length}`,
    `system_action_count=${systemPages.actions.length}`,
    `system_script_endpoint_count=${systemPages.scriptEndpoints.length}`,
    `system_grid_column_count=${systemPages.gridColumns.length}`,
    ...coreConfig.status.map(row => `config_${row.dataset}_count=${row.rowCount}`),
    'credentials_persisted=false',
    'cookies_persisted=false'
  ].join('\r\n'),
  'utf8'
)

console.log(JSON.stringify({
  authenticated: true,
  dictionaryCategoryCount: dictionary.categories.length,
  dictionaryItemCount: dictionary.items.length,
  systemPageCount: systemPages.inventory.length,
  systemControlCount: systemPages.controls.length,
  systemOptionCount: systemPages.options.length,
  systemActionCount: systemPages.actions.length,
  systemScriptEndpointCount: systemPages.scriptEndpoints.length,
  systemGridColumnCount: systemPages.gridColumns.length,
  coreConfigDatasets: coreConfig.status,
  outputDirectory: OUTPUT_DIR
}))
