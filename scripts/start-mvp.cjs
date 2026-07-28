'use strict'

const { spawn } = require('child_process')
const path = require('path')

if (!process.env.ERP_DB_PASSWORD) {
  console.error('ERP_DB_PASSWORD is required before starting the MVP.')
  process.exit(1)
}

const root = path.resolve(__dirname, '..')
const python = process.env.ERP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3')
const common = {
  cwd: root,
  env: process.env,
  stdio: 'inherit'
}

const api = spawn(python, ['server/mvp_api.py', 'serve'], common)
const web = spawn(
  process.execPath,
  [
    '--openssl-legacy-provider',
    './node_modules/@vue/cli-service/bin/vue-cli-service.js',
    'serve',
    '--mode',
    'mvp'
  ],
  common
)

let closing = false

function close(exitCode) {
  if (closing) return
  closing = true
  if (!api.killed) api.kill()
  if (!web.killed) web.kill()
  setTimeout(() => process.exit(exitCode), 100)
}

api.on('error', error => {
  console.error(`MVP API failed to start with "${python}": ${error.message}`)
  close(1)
})

web.on('error', error => {
  console.error(`Vue development server failed to start: ${error.message}`)
  close(1)
})

api.on('exit', code => {
  if (!closing && code !== 0) close(code || 1)
})

web.on('exit', code => {
  if (!closing) close(code || 0)
})

process.on('SIGINT', () => close(0))
process.on('SIGTERM', () => close(0))

