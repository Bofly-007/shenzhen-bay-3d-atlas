'use strict';

/**
 * SZ_3D desktop shell (Electron).
 *
 * The renderer is the same offline web core used by the Android and HarmonyOS
 * builds.  Assets are served from a private, privileged scheme so that
 * fetch(), service-worker-less caching and local file access all behave like a
 * normal secure origin.
 */

const { app, BrowserWindow, protocol, Menu, shell, screen, dialog } = require('electron');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');

const APP_DIR = path.join(__dirname, 'app');
const INDEX = path.join(APP_DIR, 'index.html');
const SCHEME = 'sz3d';
const ORIGIN = `${SCHEME}://app`;
const DEV = process.env.SZ3D_DEV === '1';
const LOG = process.env.SZ3D_LOG === '1' ? path.join(__dirname, 'startup.log') : null;

function log(...args) {
  if (!LOG) return;
  try {
    fs.appendFileSync(LOG, new Date().toISOString() + ' ' + args.join(' ') + '\n');
  } catch (error) {
    /* ignore */
  }
}

log('module loaded; argv=' + process.argv.join(' '));
log('electron=' + process.versions.electron + ' chrome=' + process.versions.chrome);
process.on('uncaughtException', (error) => log('uncaughtException: ' + (error && error.stack)));
process.on('unhandledRejection', (error) => log('unhandledRejection: ' + error));

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.glb': 'model/gltf-binary',
  '.gz': 'application/octet-stream',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
};

protocol.registerSchemesAsPrivileged([
  {
    scheme: SCHEME,
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      stream: true,
      corsEnabled: true,
      allowServiceWorkers: false,
    },
  },
]);
log('schemes registered');

let mainWindow = null;

function stateFile() {
  return path.join(app.getPath('userData'), 'window-state.json');
}

function readState() {
  try {
    const value = JSON.parse(fs.readFileSync(stateFile(), 'utf8'));
    if (value && Number.isFinite(value.width) && Number.isFinite(value.height)) return value;
  } catch (error) {
    /* first run */
  }
  return null;
}

function saveState() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  try {
    const bounds = mainWindow.getNormalBounds();
    fs.mkdirSync(app.getPath('userData'), { recursive: true });
    fs.writeFileSync(
      stateFile(),
      JSON.stringify({ ...bounds, maximized: mainWindow.isMaximized() }, null, 2)
    );
  } catch (error) {
    /* non fatal */
  }
}

function restoreBounds(state) {
  const width = Math.max(960, Math.min(state?.width || 1440, 4096));
  const height = Math.max(640, Math.min(state?.height || 900, 2400));
  if (!state) return { width, height, center: true };
  const area = screen.getDisplayMatching({
    x: state.x || 0,
    y: state.y || 0,
    width,
    height,
  }).workArea;
  const visible =
    state.x >= area.x - 80 &&
    state.x + width <= area.x + area.width + 80 &&
    state.y >= area.y - 40 &&
    state.y + height <= area.y + area.height + 40;
  return visible ? { x: state.x, y: state.y, width, height } : { width, height, center: true };
}

function resolveAsset(requestUrl) {
  const url = new URL(requestUrl);
  if (url.host !== 'app') return null;
  let pathname;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch (error) {
    return null;
  }
  const relative = pathname.replace(/^\/+/, '') || 'index.html';
  const file = path.resolve(APP_DIR, relative);
  if (file !== APP_DIR && !file.startsWith(APP_DIR + path.sep)) return null;
  return file;
}

async function serveAsset(request) {
  const file = resolveAsset(request.url);
  if (!file) return new Response('Forbidden', { status: 403 });
  try {
    const data = await fsp.readFile(file);
    const type = MIME[path.extname(file).toLowerCase()] || 'application/octet-stream';
    return new Response(data, {
      status: 200,
      headers: {
        'content-type': type,
        'content-length': String(data.length),
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      },
    });
  } catch (error) {
    return new Response('Not found: ' + path.basename(file), {
      status: 404,
      headers: { 'content-type': 'text/plain; charset=utf-8' },
    });
  }
}

function openExternal(url) {
  if (/^https?:\/\//i.test(url)) shell.openExternal(url);
}

function createWindow() {
  const state = readState();
  const bounds = restoreBounds(state);

  mainWindow = new BrowserWindow({
    ...bounds,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#edf1f0',
    title: 'SZ_3D',
    icon: path.join(__dirname, 'build', 'icon.ico'),
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: false,
      webgl: true,
      backgroundThrottling: false,
    },
  });

  mainWindow.setMenu(null);
  if (state?.maximized) mainWindow.maximize();

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.loadURL(`${ORIGIN}/index.html?app=desktop&v=${encodeURIComponent(app.getVersion())}`);
  log('loading ' + mainWindow.webContents.getURL());

  mainWindow.webContents.on('did-finish-load', () => log('did-finish-load'));
  mainWindow.webContents.on('render-process-gone', (event, details) => log('render-process-gone ' + JSON.stringify(details)));

  mainWindow.webContents.setVisualZoomLevelLimits(1, 1);
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(ORIGIN + '/')) {
      event.preventDefault();
      openExternal(url);
    }
  });

  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11') {
      mainWindow.setFullScreen(!mainWindow.isFullScreen());
      event.preventDefault();
    } else if (input.key === 'Escape' && mainWindow.isFullScreen()) {
      mainWindow.setFullScreen(false);
      event.preventDefault();
    } else if (DEV && input.control && input.shift && input.key.toLowerCase() === 'i') {
      mainWindow.webContents.toggleDevTools();
      event.preventDefault();
    }
  });

  mainWindow.webContents.on('did-fail-load', (event, code, description, url, isMainFrame) => {
    if (!isMainFrame) return;
    dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: 'SZ_3D',
      message: '界面未能载入',
      detail: `${description}（${code}）\n${url}\n\n请重新安装 SZ_3D。`,
    });
  });

  mainWindow.on('close', saveState);
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

log('requesting single instance lock; ready=' + app.isReady());
const gotLock = process.env.SZ3D_NO_LOCK === '1' ? true : app.requestSingleInstanceLock();
log('single instance lock=' + gotLock);
if (!gotLock) {
  log('single instance lock not acquired; quitting');
  app.quit();
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
  });

  app.whenReady().then(() => {
    log('app ready');
    app.setAppUserModelId('com.sz3d.atlas');
    if (process.platform === 'win32') Menu.setApplicationMenu(null);
    protocol.handle(SCHEME, serveAsset);
    log('protocol handled');

    if (!fs.existsSync(INDEX)) {
      log('missing index ' + INDEX);
      dialog.showErrorBox('SZ_3D 安装不完整', '缺少应用资源 app/index.html，请重新安装。');
      app.quit();
      return;
    }
    createWindow();
    log('window created');

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  }).catch((error) => log('whenReady error ' + (error && error.stack)));

  app.on('window-all-closed', () => app.quit());
}
