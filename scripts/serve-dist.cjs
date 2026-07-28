const fs = require('fs')
const http = require('http')
const path = require('path')

const distDirectory = path.resolve(__dirname, '..', 'dist')
const port = Number(process.env.ERP_PREVIEW_PORT || 9527)
const mimeTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
}

http.createServer((request, response) => {
  const pathname = decodeURIComponent((request.url || '/').split('?')[0])
  const requestedPath = path.resolve(distDirectory, `.${pathname}`)
  const safePath = requestedPath.startsWith(distDirectory) && fs.existsSync(requestedPath) && fs.statSync(requestedPath).isFile()
    ? requestedPath
    : path.join(distDirectory, 'index.html')

  response.setHeader('Content-Type', mimeTypes[path.extname(safePath).toLowerCase()] || 'application/octet-stream')
  fs.createReadStream(safePath).pipe(response)
}).listen(port, '127.0.0.1', () => {
  console.log(`ERP preview ready at http://localhost:${port}`)
})
