import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import http from 'http';
import { fileURLToPath } from 'url';
import WebSocket from 'ws';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PROOF = path.join(ROOT, 'proof');
fs.mkdirSync(PROOF, { recursive: true });
const CDP_PORT = 9223;
const BASE = 'http://127.0.0.1:8765';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function httpJson(url) {
  return new Promise((res, rej) => {
    http.get(url, (r) => {
      let d = '';
      r.on('data', (c) => (d += c));
      r.on('end', () => {
        try { res(JSON.parse(d)); } catch (e) { rej(e); }
      });
    }).on('error', rej);
  });
}

function cdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  const ready = new Promise((res, rej) => {
    ws.on('open', res);
    ws.on('error', rej);
  });
  ws.on('message', (raw) => {
    const msg = JSON.parse(raw.toString());
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    }
  });
  async function send(method, params = {}) {
    await ready;
    const i = ++id;
    ws.send(JSON.stringify({ id: i, method, params }));
    return new Promise((resolve, reject) => {
      pending.set(i, { resolve, reject });
      setTimeout(() => reject(new Error('timeout ' + method)), 45000);
    });
  }
  return { send, close: () => ws.close() };
}

async function withChrome(fn) {
  const userData = `/tmp/terra-chrome-${process.pid}-${Date.now()}`;
  fs.mkdirSync(userData, { recursive: true });
  const chrome = spawn('google-chrome', [
    '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage',
    '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader',
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${userData}`,
    '--window-size=390,844',
    '--force-device-scale-factor=2',
    'about:blank',
  ], { stdio: 'ignore' });
  try {
    let ver;
    for (let i = 0; i < 40; i++) {
      try { ver = await httpJson(`http://127.0.0.1:${CDP_PORT}/json/version`); break; }
      catch { await sleep(150); }
    }
    if (!ver) throw new Error('CDP not up');
    const list = await httpJson(`http://127.0.0.1:${CDP_PORT}/json/list`);
    const page = list.find((t) => t.type === 'page') || list[0];
    const client = cdp(page.webSocketDebuggerUrl);
    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 390, height: 844, deviceScaleFactor: 2, mobile: true,
    });
    await fn(client);
    client.close();
  } finally {
    chrome.kill('SIGKILL');
    await sleep(200);
  }
}

async function captureOne(client, url, outPath) {
  await client.send('Page.navigate', { url });
  let ready = false;
  for (let i = 0; i < 60; i++) {
    await sleep(200);
    try {
      const r = await client.send('Runtime.evaluate', {
        expression: 'window.__terraReady === true',
        returnByValue: true,
      });
      if (r.result?.value) { ready = true; break; }
    } catch {}
  }
  if (!ready) console.warn('WARN not ready', url);
  await sleep(1200);
  // drain ease animations for S5
  await sleep(700);
  const shot = await client.send('Page.captureScreenshot', { format: 'png', fromSurface: true });
  fs.writeFileSync(outPath, Buffer.from(shot.data, 'base64'));
  console.log('OK', path.basename(outPath), fs.statSync(outPath).size, ready ? 'ready' : 'NOT_READY');
}

await withChrome(async (client) => {
  for (const plat of ['ios', 'android']) {
    for (const mode of ['S0', 'S1', 'S3', 'S5']) {
      const url = `${BASE}/?platform=${plat}&mode=${mode}`;
      const out = path.join(PROOF, `${mode.toLowerCase()}-${plat}.png`);
      await captureOne(client, url, out);
    }
  }
});

// S5 closeup crop via python
import { spawnSync } from 'child_process';
spawnSync('python3', ['-c', `
from PIL import Image
from pathlib import Path
p=Path("${PROOF}/s5-ios.png")
im=Image.open(p)
w,h=im.size
cw,ch=int(w*0.62),int(h*0.42)
left=(w-cw)//2+int(w*0.02); top=(h-ch)//2
im.crop((left,top,left+cw,top+ch)).save("${PROOF}/s5-closeup.png")
print("OK s5-closeup", Path("${PROOF}/s5-closeup.png").stat().st_size)
`], { encoding: 'utf8' });
console.log('all done');
