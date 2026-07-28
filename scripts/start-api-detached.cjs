'use strict'

const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

if (!process.env.ERP_DB_PASSWORD) {
  console.error('ERP_DB_PASSWORD is required.')
  process.exit(1)
}

const root = path.resolve(__dirname, '..')
const python =
  process.env.ERP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3')
const logDirectory = path.join(root, '.tmp')
fs.mkdirSync(logDirectory, { recursive: true })
const stdout = fs.openSync(path.join(logDirectory, 'api-3000.out.log'), 'a')
const stderr = fs.openSync(path.join(logDirectory, 'api-3000.err.log'), 'a')
const api = spawn(python, ['server/mvp_api.py', 'serve'], {
  cwd: root,
  env: process.env,
  detached: true,
  windowsHide: true,
  stdio: ['ignore', stdout, stderr]
})

api.unref()
process.stdout.write(`${api.pid}\n`)
