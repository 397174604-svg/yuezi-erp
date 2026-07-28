import auditedLegacySurfaces from './audited-legacy-surfaces.json'

const placeholderPattern = /^\s*-*\s*(全部|请选择|请选[^-]*)\s*-*\s*$/

function pad(value) {
  return String(value).padStart(2, '0')
}

function formatDate(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function parseDate(value) {
  const match = String(value || '').match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/)
  if (!match) return null
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
}

function dynamicDateDefault(value) {
  const target = parseDate(value)
  const audited = parseDate(auditedLegacySurfaces.auditedOn)
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
  if (type === 'select') return 'select'
  if (type === 'choice-list') return 'choice-list'
  if (type === 'checkbox') return 'checkbox'
  if (type === 'radio') return 'radio'
  const identity = `${field.id || ''} ${field.name || ''}`.toLowerCase()
  if (parseDate(field.value) || /(date|time|start|end|billdate|expecte)/.test(identity)) return 'date'
  return 'input'
}

function fieldDefault(field, type) {
  if (type === 'select') return (field.selected && field.selected[0]) || ''
  if (type === 'choice-list') return (field.selected && field.selected[0]) || (field.options && field.options[0]) || ''
  if (type === 'checkbox' || type === 'radio') return Boolean(field.checked)
  if (type === 'date') return dynamicDateDefault(field.value)
  return field.value && field.value !== '<non-empty>' ? field.value : ''
}

function uniqueFieldKey(field, index, used) {
  const raw = field.id || field.name || `field_${index + 1}`
  const normalized = `legacy_${String(raw).replace(/[^\w]+/g, '_') || `field_${index + 1}`}`
  let key = normalized
  let suffix = 2
  while (used.has(key)) {
    key = `${normalized}_${suffix}`
    suffix += 1
  }
  used.add(key)
  return key
}

function groupedControlRun(controls, start) {
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
  if (!text) return ''
  if (type === 'checkbox') return ''
  if (options.some(option => option === text || text.includes(option))) return ''
  return text.length <= 20 ? text : ''
}

function mapFilters(controls = []) {
  const used = new Set()
  const mapped = []
  for (let index = 0; index < controls.length;) {
    const field = controls[index]
    const type = fieldType(field)
    const run = groupedControlRun(controls, index)
    if (run.length > 1) {
      const groupedType = `${type}-group`
      const options = run.map(item => item.label).filter(Boolean)
      const selected = run.filter(item => item.checked).map(item => item.label).filter(Boolean)
      mapped.push({
        key: uniqueFieldKey(field, index, used),
        legacyId: field.id || '',
        legacyName: field.name || '',
        label: cleanGroupLabel(type, field.groupLabel, options),
        type: groupedType,
        options,
        defaultValue: type === 'radio' ? (selected[0] || '') : selected,
        readonly: false,
        disabled: run.every(item => Boolean(item.disabled)),
        verified: true
      })
      index += run.length
      continue
    }
    const defaultValue = fieldDefault(field, type)
    mapped.push({
      key: uniqueFieldKey(field, index, used),
      legacyId: field.id || '',
      legacyName: field.name || '',
      label: field.label || '',
      type,
      options: field.options || [],
      defaultValue,
      placeholderDefault: type === 'select' && placeholderPattern.test(defaultValue),
      checked: Boolean(field.checked),
      readonly: Boolean(field.readonly),
      disabled: Boolean(field.disabled),
      verified: true
    })
    index += 1
  }
  return mapped
}

function buildSurface(moduleKey, title, page) {
  const schema = page && page.schema
  const query = schema && schema.query
  const status = page && page.status
  const verified = status === 200 && Boolean(schema)
  return {
    moduleKey,
    title,
    path: page ? page.path : '',
    status,
    verified,
    toolbarActions: verified ? schema.toolbar.map(item => item.text) : [],
    queryActions: verified ? query.actions : [],
    filters: verified ? mapFilters(query.controls) : [],
    gridHeaders: verified ? schema.gridHeaders : [],
    staticTables: verified ? (schema.staticTables || []) : [],
    toolbarContainers: verified ? schema.toolbarContainers : [],
    evidenceLevel: verified ? '工具栏与查询区已核验' : '原页读取异常，保持未知',
    completionLevel: verified ? 'Schema-faithful（工具栏/查询区）' : 'Unknown',
    evidenceNote: verified
      ? '顶部业务工具栏、主查询字段、下拉选项、默认值与查询区按钮来自原 ERP admin 只读会话；列表技术列、表单、弹窗和真实写入流程仍需独立核验。'
      : '原 ERP 页面未成功返回可核验证据，本地没有从相似页面补造按钮或查询条件。'
  }
}

export function getAuditedSurface(moduleKey, title) {
  const pages = auditedLegacySurfaces.modules[moduleKey] || {}
  const page = pages[title]
  if (!page) {
    return buildSurface(moduleKey, title, null)
  }
  return buildSurface(moduleKey, title, page)
}

export function applyAuditedSurfaceEvidence(moduleKey, configs) {
  Object.keys(configs).forEach(title => {
    const surface = getAuditedSurface(moduleKey, title)
    if (!surface.verified) return
    Object.assign(configs[title], {
      title,
      actions: surface.toolbarActions,
      queryActions: surface.queryActions,
      filters: surface.filters,
      auditedGridHeaders: surface.gridHeaders,
      toolbarVerified: true,
      queryVerified: true,
      surfaceVerified: true,
      evidenceLevel: surface.evidenceLevel,
      completionLevel: surface.completionLevel,
      evidenceNote: surface.evidenceNote,
      verificationNote: surface.evidenceNote,
      originalUrl: surface.path,
      internalVerified: false
    })
  })
  return configs
}

export function initialAuditedFilters(fields) {
  return fields.reduce((result, field) => {
    result[field.key] = field.defaultValue
    return result
  }, {})
}

export { auditedLegacySurfaces }
