import { createReadStream, existsSync, statSync } from 'node:fs'
import { createServer } from 'node:http'
import { extname, join, normalize, resolve } from 'node:path'

const port = Number(process.argv[2] || 9527)
const distRoot = resolve(process.cwd(), 'dist')
const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
}

createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, `http://127.0.0.1:${port}`).pathname)
  const requested = pathname === '/' ? 'index.html' : normalize(pathname).replace(/^([/\\])+/, '')
  let filePath = resolve(join(distRoot, requested))
  if (!filePath.startsWith(distRoot) || !existsSync(filePath) || statSync(filePath).isDirectory()) {
    filePath = join(distRoot, 'index.html')
  }
  response.writeHead(200, { 'Content-Type': contentTypes[extname(filePath)] || 'application/octet-stream' })
  createReadStream(filePath).pipe(response)
}).listen(port, '127.0.0.1', () => {
  process.stdout.write(`dist server listening on ${port}\n`)
})
