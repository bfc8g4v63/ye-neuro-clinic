const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("queueDesktop", {
  loadState: () => ipcRenderer.invoke("queue:load-state"),
  saveState: (state) => ipcRenderer.invoke("queue:save-state", state),
  archiveAndClose: (state) => ipcRenderer.invoke("queue:archive-and-close", state),
  loadSettings: () => ipcRenderer.invoke("queue:load-settings"),
  saveSettings: (settings) => ipcRenderer.invoke("queue:save-settings", settings),
  exportAudit: (state) => ipcRenderer.invoke("queue:export-audit", state),
  openWaitingDisplay: () => ipcRenderer.invoke("queue:open-display"),
  testVoice: () => ipcRenderer.invoke("queue:test-voice"),
  onStateUpdate: (callback) => ipcRenderer.on("queue-state-updated", (_event, state) => callback(state)),
  onVoiceTest: (callback) => ipcRenderer.on("queue:test-voice", callback),
});
