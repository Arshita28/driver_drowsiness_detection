const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = __dirname;
const port = Number(process.env.PORT || 8000);
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.wasm': 'application/wasm' };
const publicFiles = new Set(['index.html', 'style.css', 'app.js', 'alarm.js']);
const server = http.createServer((req, res) => {
  let name;
  try { name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/^\//, '') || 'index.html'; }
  catch { res.writeHead(400); res.end('Invalid request'); return; }
  if (!publicFiles.has(name)) { res.writeHead(404); res.end('Not found'); return; }
  fs.readFile(path.join(root, name), (error, content) => {
    if (error) { res.writeHead(404); res.end('File not found'); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(name)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(content);
  });
});
server.on('error', error => {
  console.error(error.code === 'EADDRINUSE' ? 'Port 8000 is busy. Close the other server or choose another PORT.' : error.message);
  process.exitCode = 1;
});
server.listen(port, '127.0.0.1', () => {
  console.log(`DriveAware is ready: http://localhost:${port}`);
  console.log('Open this address in Chrome or Edge, click Start webcam, and allow camera access.');
  console.log('Press Ctrl+C to stop.');
});
