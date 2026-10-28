const { app, BrowserWindow, Menu, ipcMain, screen, dialog } = require("electron");
const fs = require("node:fs/promises");
const path = require("node:path");

let controllerWindow;
let displayWindow;

const allowedStatuses = new Set(["waiting", "called", "noShow", "returnReady", "done"]);
const allowedActions = new Set(["checkin", "call", "recall", "no_show", "return_ready", "undo", "session_started", "session_closed"]);
const defaultState = { session: null, items: [], current: null, lastCalledAt: null, lastEvent: null, events: [] };
const defaultSettings = { hotkeys: { callNext: "F8", callReturn: "F9", recall: "F10", noShow: "F11" }, deviceChecks: { display: false, voice: false, keypad: false } };

function pagesPath() {
  return path.join(__dirname, "..", "local-controller");
}

function statePath() {
  return path.join(app.getPath("userData"), "queue-state.json");
}

function snapshotPath() {
  return path.join(app.getPath("userData"), "backups", "queue-latest.json");
}

function archivePath(session) {
  const date = session?.dateKey || new Date().toISOString().slice(0, 10);
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  return path.join(app.getPath("userData"), "archives", `queue-${date}-${stamp}.json`);
}

function settingsPath() {
  return path.join(app.getPath("userData"), "queue-settings.json");
}

function sanitizeSettings(input) {
  const supported = new Set(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]);
  const requested = input?.hotkeys || {};
  const hotkeys = Object.fromEntries(Object.entries(defaultSettings.hotkeys).map(([name, fallback]) => [name, supported.has(requested[name]) ? requested[name] : fallback]));
  return { hotkeys, deviceChecks: { display: Boolean(input?.deviceChecks?.display), voice: Boolean(input?.deviceChecks?.voice), keypad: Boolean(input?.deviceChecks?.keypad) } };
}

async function loadSettings() {
  try { return sanitizeSettings(JSON.parse(await fs.readFile(settingsPath(), "utf8"))); } catch { return sanitizeSettings(defaultSettings); }
}

async function saveSettings(nextSettings) {
  const settings = sanitizeSettings(nextSettings);
  await fs.mkdir(path.dirname(settingsPath()), { recursive: true });
  await fs.writeFile(settingsPath(), JSON.stringify(settings, null, 2), "utf8");
  return settings;
}

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

async function exportAudit(nextState) {
  const state = sanitizeState(nextState);
  const rows = [["時間", "角色", "動作", "候診號碼", "是否已復原"]];
  state.events.forEach((event) => rows.push([event.at, event.actor === "reception" ? "櫃台" : "醫師", event.action, event.number ?? "", event.undone ? "是" : "否"]));
  const { canceled, filePath } = await dialog.showSaveDialog(controllerWindow, { defaultPath: `葉神經科_候診操作紀錄_${new Date().toISOString().slice(0, 10)}.csv`, filters: [{ name: "CSV", extensions: ["csv"] }] });
  if (canceled || !filePath) return null;
  await fs.writeFile(filePath, `\uFEFF${rows.map((row) => row.map(csvCell).join(",")).join("\r\n")}\r\n`, "utf8");
  return filePath;
}

function sanitizeState(input) {
  const items = Array.isArray(input?.items) ? input.items : [];
  const sanitizedItems = items
    .filter((item) => Number.isInteger(item?.number) && item.number >= 1 && item.number <= 999 && allowedStatuses.has(item.status))
    .map((item) => ({ number: item.number, status: item.status }));
  const current = sanitizedItems.some((item) => item.number === input?.current && item.status === "called") ? input.current : null;
  const session = input?.session && (input.session.status === "active" || input.session.status === "closed")
    ? {
      status: input.session.status,
      dateKey: typeof input.session.dateKey === "string" ? input.session.dateKey.slice(0, 10) : null,
      startedAt: typeof input.session.startedAt === "string" ? input.session.startedAt : null,
      closedAt: typeof input.session.closedAt === "string" ? input.session.closedAt : null,
    }
    : null;
  const events = (Array.isArray(input?.events) ? input.events : []).slice(-250).flatMap((event) => {
    if (!allowedActions.has(event?.action) || typeof event?.at !== "string") return [];
    const beforeItems = Array.isArray(event.before?.items)
      ? event.before.items.filter((item) => Number.isInteger(item?.number) && allowedStatuses.has(item.status)).map((item) => ({ number: item.number, status: item.status }))
      : undefined;
    return [{
      id: typeof event.id === "string" ? event.id.slice(0, 64) : `${event.at}-${event.action}`,
      at: event.at,
      action: event.action,
      actor: event.actor === "reception" ? "reception" : "doctor",
      number: Number.isInteger(event.number) ? event.number : null,
      undone: Boolean(event.undone),
      before: beforeItems ? { items: beforeItems, current: Number.isInteger(event.before.current) ? event.before.current : null, lastCalledAt: event.before.lastCalledAt || null, lastEvent: event.before.lastEvent || null } : undefined,
    }];
  });
  return {
    session,
    items: sanitizedItems,
    current,
    lastCalledAt: typeof input?.lastCalledAt === "string" ? input.lastCalledAt : null,
    lastEvent: input?.lastEvent === "call" || input?.lastEvent === "recall" ? input.lastEvent : null,
    events,
  };
}

async function loadState() {
  try {
    return sanitizeState(JSON.parse(await fs.readFile(statePath(), "utf8")));
  } catch {
    return { ...defaultState };
  }
}

async function saveState(nextState) {
  const state = sanitizeState(nextState);
  const target = statePath();
  await fs.mkdir(path.dirname(target), { recursive: true });
  const temporary = `${target}.tmp`;
  await fs.writeFile(temporary, JSON.stringify(state, null, 2), "utf8");
  await fs.rename(temporary, target);
  await fs.mkdir(path.dirname(snapshotPath()), { recursive: true });
  await fs.writeFile(snapshotPath(), JSON.stringify(state, null, 2), "utf8");
  for (const window of [controllerWindow, displayWindow]) {
    if (window && !window.isDestroyed()) window.webContents.send("queue-state-updated", state);
  }
  return state;
}

async function archiveAndClose(nextState) {
  const state = sanitizeState(nextState);
  if (state.session?.status !== "active") throw new Error("沒有進行中的診次可結束。");
  const at = new Date().toISOString();
  state.session = { ...state.session, status: "closed", closedAt: at };
  state.events.push({ id: `session-closed-${at}`, at, action: "session_closed", actor: "doctor", number: null, undone: false });
  const archived = sanitizeState(state);
  const target = archivePath(archived.session);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, JSON.stringify(archived, null, 2), "utf8");
  return saveState(archived);
}

function secureOptions() {
  return {
    preload: path.join(__dirname, "preload.cjs"),
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
  };
}

function protectWindow(window) {
  window.webContents.on("will-navigate", (event, target) => {
    if (!target.startsWith("file:")) event.preventDefault();
  });
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
}

function createController() {
  controllerWindow = new BrowserWindow({
    width: 1240,
    height: 880,
    minWidth: 900,
    minHeight: 680,
    title: "葉神經科｜現場候診控制器",
    webPreferences: secureOptions(),
  });
  protectWindow(controllerWindow);
  controllerWindow.loadFile(path.join(pagesPath(), "index.html"));
}

function openDisplay() {
  if (displayWindow && !displayWindow.isDestroyed()) {
    displayWindow.focus();
    return;
  }
  const external = screen.getAllDisplays()[1];
  displayWindow = new BrowserWindow({
    width: external?.workAreaSize.width || 1280,
    height: external?.workAreaSize.height || 720,
    x: external?.bounds.x,
    y: external?.bounds.y,
    title: "葉神經科｜候診顯示",
    backgroundColor: "#0d4054",
    autoHideMenuBar: true,
    webPreferences: secureOptions(),
  });
  protectWindow(displayWindow);
  displayWindow.loadFile(path.join(pagesPath(), "waiting-display.html"));
  displayWindow.once("ready-to-show", () => displayWindow.maximize());
  displayWindow.on("closed", () => { displayWindow = undefined; });
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  ipcMain.handle("queue:load-state", loadState);
  ipcMain.handle("queue:save-state", (_event, state) => saveState(state));
  ipcMain.handle("queue:archive-and-close", (_event, state) => archiveAndClose(state));
  ipcMain.handle("queue:load-settings", loadSettings);
  ipcMain.handle("queue:save-settings", (_event, settings) => saveSettings(settings));
  ipcMain.handle("queue:export-audit", (_event, state) => exportAudit(state));
  ipcMain.handle("queue:open-display", () => openDisplay());
  ipcMain.handle("queue:test-voice", () => {
    if (displayWindow && !displayWindow.isDestroyed()) {
      displayWindow.webContents.send("queue:test-voice");
      return true;
    }
    return false;
  });
  createController();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createController(); });
});

app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
