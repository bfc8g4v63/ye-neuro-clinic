const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("queueDesktop", {
  loadState: () => ipcRenderer.invoke("queue:load-state"),
  saveState: (state) => ipcRenderer.invoke("queue:save-state", state),
  openWaitingDisplay: () => ipcRenderer.invoke("queue:open-display"),
  onStateUpdate: (callback) => ipcRenderer.on("queue-state-updated", (_event, state) => callback(state)),
});
