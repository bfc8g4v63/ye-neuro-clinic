const { app, BrowserWindow, Menu, ipcMain, screen } = require("electron");
const fs = require("node:fs/promises");
const path = require("node:path");

let controllerWindow;
let displayWindow;

const allowedStatuses = new Set(["waiting", "called", "noShow", "returnReady", "done"]);
const defaultState = { items: [], current: null, lastCalledAt: null, lastEvent: null };

function pagesPath() {
  return path.join(__dirname, "..", "local-controller");
}

function statePath() {
  return path.join(app.getPath("userData"), "queue-state.json");
}

function sanitizeState(input) {
  const items = Array.isArray(input?.items) ? input.items : [];
  const sanitizedItems = items
    .filter((item) => Number.isInteger(item?.number) && item.number >= 1 && item.number <= 999 && allowedStatuses.has(item.status))
    .map((item) => ({ number: item.number, status: item.status }));
  const current = sanitizedItems.some((item) => item.number === input?.current && item.status === "called") ? input.current : null;
  return {
    items: sanitizedItems,
    current,
    lastCalledAt: typeof input?.lastCalledAt === "string" ? input.lastCalledAt : null,
    lastEvent: input?.lastEvent === "call" || input?.lastEvent === "recall" ? input.lastEvent : null,
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
  for (const window of [controllerWindow, displayWindow]) {
    if (window && !window.isDestroyed()) window.webContents.send("queue-state-updated", state);
  }
  return state;
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
  ipcMain.handle("queue:open-display", () => openDisplay());
  createController();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createController(); });
});

app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
