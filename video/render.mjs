// Снимает кадры фильма детерминированно: каждый кадр — render(t), затем скриншот.
// node render.mjs [fps] [seconds] [outDir]
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const FILM = 'http://127.0.0.1:8140/video/film.html?rec=1';
const FPS = Number(process.argv[2] || 30);
const DUR = Number(process.argv[3] || 78);
const OUT = process.argv[4] || 'C:/Users/HP/tumar/video/frames';
const PORT = 9333 + Math.floor(Math.random() * 300);
const UD = 'C:/Users/HP/AppData/Local/Temp/chpf-cdp-' + Date.now();

mkdirSync(OUT, { recursive: true });

const chrome = spawn(CHROME, [
  '--headless=new', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--mute-audio', '--disable-gpu', '--allow-file-access-from-files',
  '--window-size=1920,1080', '--force-device-scale-factor=1',
  '--remote-debugging-port=' + PORT, '--user-data-dir=' + UD, 'about:blank'
], { stdio: 'ignore' });

let wsUrl = null;
for (let i = 0; i < 60; i++) {
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
    const j = await r.json();
    if (j.webSocketDebuggerUrl) { wsUrl = j.webSocketDebuggerUrl; break; }
  } catch {}
  await sleep(300);
}
if (!wsUrl) { chrome.kill(); throw new Error('chrome devtools не поднялся'); }

const targetRes = await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' });
const target = await targetRes.json();
const ws = new WebSocket(target.webSocketDebuggerUrl);

let nextId = 1;
const pending = new Map();
const waiters = [];
ws.addEventListener('message', ev => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
  } else if (msg.method) {
    for (let i = waiters.length - 1; i >= 0; i--) {
      if (waiters[i].method === msg.method) { waiters.splice(i, 1)[0].resolve(msg.params); }
    }
  }
});
await new Promise(r => ws.addEventListener('open', r, { once: true }));

const cdp = (method, params = {}) => new Promise((resolve, reject) => {
  const id = nextId++;
  pending.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params }));
});
const once = method => new Promise(resolve => waiters.push({ method, resolve }));

await cdp('Page.enable');
await cdp('Runtime.enable');
await cdp('Emulation.setDeviceMetricsOverride', {
  width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false
});
const loaded = once('Page.loadEventFired');
await cdp('Page.navigate', { url: FILM });
await loaded;
await sleep(700);

const ev = async (expression, awaitPromise = false) =>
  (await cdp('Runtime.evaluate', { expression, awaitPromise, returnByValue: true })).result?.value;

// ставим кадр и ждём, пока браузер его действительно отрисует
const seek = t => ev(`new Promise(r=>{__seek(${t});requestAnimationFrame(()=>requestAnimationFrame(()=>r(1)))})`, true);

const total = Math.round(FPS * DUR);
const started = Date.now();
for (let i = 0; i < total; i++) {
  const t = i / FPS;
  await seek(t);
  const shot = await cdp('Page.captureScreenshot', {
    format: 'jpeg', quality: 94, captureBeyondViewport: false, fromSurface: true
  });
  writeFileSync(`${OUT}/${String(i).padStart(5, '0')}.jpg`, Buffer.from(shot.data, 'base64'));
  if (i % 120 === 0) {
    const el = (Date.now() - started) / 1000;
    console.log(`кадр ${i}/${total} · ${t.toFixed(1)}s · ${(i / Math.max(el, .001)).toFixed(1)} fps`);
  }
}

console.log(`готово: ${total} кадров за ${((Date.now() - started) / 1000).toFixed(1)}s → ${OUT}`);
ws.close();
chrome.kill();
await sleep(400);
try { rmSync(UD, { recursive: true, force: true }); } catch {}
process.exit(0);
