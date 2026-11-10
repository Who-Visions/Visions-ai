// Desktop shell: runs the local Vite server (it hosts the API proxies) and
// shows the app in a native window.
const { app, BrowserWindow, shell } = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const PORT = process.env.GEV_DESKTOP_PORT || '5190';
const URL_BASE = `http://127.0.0.1:${PORT}/`;
let server = null;

function startServer() {
  server = spawn(
    process.execPath,
    [path.join(ROOT, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', PORT, '--strictPort'],
    { cwd: ROOT, env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, stdio: 'inherit' },
  );
  server.on('exit', (code) => {
    server = null;
    if (!app.isQuitting) {
      console.error(`[desktop] server exited (${code})`);
      app.quit();
    }
  });
}

async function waitForServer(timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(URL_BASE)).ok) return;
    } catch { /* not up yet */ }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error('Timed out waiting for the local server');
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1000,
    minHeight: 640,
    backgroundColor: '#0b0d12',
    title: 'NouGen//Eye',
    webPreferences: { contextIsolation: true, sandbox: true, nodeIntegration: false },
  });
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  await win.loadURL(URL_BASE);

  // Test hook: GEV_DESKTOP_SCREENSHOT=/path.png captures the window after load.
  const shot = process.env.GEV_DESKTOP_SCREENSHOT;
  if (shot) {
    setTimeout(async () => {
      fs.writeFileSync(shot, (await win.webContents.capturePage()).toPNG());
      app.quit();
    }, 20000);
  }
}

app.whenReady().then(async () => {
  startServer();
  await waitForServer();
  await createWindow();
}).catch((error) => {
  console.error('[desktop]', error);
  app.quit();
});

app.on('before-quit', () => {
  app.isQuitting = true;
  server?.kill();
});
app.on('window-all-closed', () => app.quit());
