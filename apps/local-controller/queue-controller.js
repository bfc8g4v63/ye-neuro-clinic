const storageKey = "ye-neuro-queue-controller-v2";
const statusLabel = { waiting: "等待中", called: "叫號中", noShow: "過號", returnReady: "回號待叫", done: "已完成" };
const desktop = window.queueDesktop;
const queueChannel = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel("ye-neuro-queue");
const defaultState = { session: null, items: [], current: null, lastCalledAt: null, lastEvent: null, events: [] };
let state = normalize(JSON.parse(localStorage.getItem(storageKey) || "null"));
let settings = { hotkeys: { callNext: "F8", callReturn: "F9", recall: "F10", noShow: "F11" }, deviceChecks: { display: false, voice: false, keypad: false } };

const elements = {
  currentNumber: document.querySelector("#currentNumber"), currentMeta: document.querySelector("#currentMeta"), checkinForm: document.querySelector("#checkinForm"), queueNumber: document.querySelector("#queueNumber"),
  returnReadyButton: document.querySelector("#returnReadyButton"), openDisplayButton: document.querySelector("#openDisplayButton"), startSessionButton: document.querySelector("#startSessionButton"), endSessionButton: document.querySelector("#endSessionButton"),
  undoButton: document.querySelector("#undoButton"), testVoiceButton: document.querySelector("#testVoiceButton"), sessionBadge: document.querySelector("#sessionBadge"), lastAudit: document.querySelector("#lastAudit"),
  settingsForm: document.querySelector("#settingsForm"), callNextKey: document.querySelector("#callNextKey"), callReturnKey: document.querySelector("#callReturnKey"), recallKey: document.querySelector("#recallKey"), noShowKey: document.querySelector("#noShowKey"),
  exportAuditButton: document.querySelector("#exportAuditButton"), shortcutTest: document.querySelector("#shortcutTest"), displayCheck: document.querySelector("#displayCheck"), voiceCheck: document.querySelector("#voiceCheck"), keypadCheck: document.querySelector("#keypadCheck"),
  formMessage: document.querySelector("#formMessage"), todayLabel: document.querySelector("#todayLabel"),
  lists: { waiting: document.querySelector("#waitingList"), returnReady: document.querySelector("#returnList"), noShow: document.querySelector("#noShowList") },
  counts: { waiting: document.querySelector("#waitingCount"), returnReady: document.querySelector("#returnCount"), noShow: document.querySelector("#noShowCount") },
};

function normalize(input) {
  const safe = input && typeof input === "object" ? input : defaultState;
  return { ...defaultState, ...safe, items: Array.isArray(safe.items) ? safe.items.filter((item) => Number.isInteger(item?.number) && statusLabel[item.status]).map((item) => ({ number: item.number, status: item.status })) : [], events: Array.isArray(safe.events) ? safe.events : [] };
}
function dateKey() { return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Taipei" }).format(new Date()); }
function nowLabel() { return new Intl.DateTimeFormat("zh-TW", { dateStyle: "long" }).format(new Date()); }
function activeSession() { return state.session?.status === "active"; }
function setMessage(message) { elements.formMessage.textContent = message; }
function getNumber() { return Number(elements.queueNumber.value); }
function activeItems(status) { return state.items.filter((item) => item.status === status).sort((a, b) => a.number - b.number); }
function snapshot() { return { items: state.items.map((item) => ({ ...item })), current: state.current, lastCalledAt: state.lastCalledAt, lastEvent: state.lastEvent }; }
function save() { localStorage.setItem(storageKey, JSON.stringify(state)); queueChannel?.postMessage({ type: "queue:update" }); if (desktop) void desktop.saveState(state); }
function record(action, actor, number, before) { const at = new Date().toISOString(); state.events.push({ id: `${at}-${action}`, at, action, actor, number: number ?? null, before, undone: false }); state.events = state.events.slice(-250); }
function hotkeyOptions() { return ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]; }
function renderSettings() {
  const fields = { callNext: elements.callNextKey, callReturn: elements.callReturnKey, recall: elements.recallKey, noShow: elements.noShowKey };
  Object.entries(fields).forEach(([name, field]) => { field.innerHTML = hotkeyOptions().map((key) => `<option value="${key}">${key}</option>`).join(""); field.value = settings.hotkeys[name]; });
  elements.displayCheck.checked = settings.deviceChecks.display; elements.voiceCheck.checked = settings.deviceChecks.voice; elements.keypadCheck.checked = settings.deviceChecks.keypad;
}
function saveSettings() { if (desktop) void desktop.saveSettings(settings); else localStorage.setItem("ye-neuro-queue-settings", JSON.stringify(settings)); }

function renderList(status, list, count) {
  const items = activeItems(status); count.textContent = items.length; list.innerHTML = "";
  if (!items.length) { const empty = document.createElement("li"); empty.className = "empty"; empty.textContent = "目前沒有"; list.append(empty); return; }
  items.forEach((item) => { const row = document.createElement("li"); row.innerHTML = `<span>${item.number} 號</span><small>${statusLabel[item.status]}</small>`; list.append(row); });
}

function render() {
  const active = activeSession(); elements.todayLabel.textContent = nowLabel();
  elements.sessionBadge.textContent = active ? `診次進行中｜${state.session.dateKey}` : state.session?.status === "closed" ? "診次已封存" : "尚未開始診次";
  const current = state.items.find((item) => item.number === state.current && item.status === "called");
  elements.currentNumber.textContent = current ? `${current.number} 號` : active ? "尚未叫號" : "—";
  elements.currentMeta.textContent = current ? "完成看診後，先在既有系統送出病歷／處方，再按下一個快捷鍵。" : active ? "櫃台可新增候診號碼；醫師以快捷鍵叫號。" : "請先開始今日診次。";
  [...elements.checkinForm.querySelectorAll("input, button"), ...document.querySelectorAll("[data-action]"), elements.undoButton].forEach((control) => { control.disabled = !active; });
  elements.startSessionButton.disabled = active; elements.endSessionButton.disabled = !active;
  const last = state.events.at(-1);
  elements.lastAudit.textContent = last ? `最近紀錄：${new Intl.DateTimeFormat("zh-TW", { hour: "2-digit", minute: "2-digit" }).format(new Date(last.at))}｜${last.actor === "reception" ? "櫃台" : "醫師"}｜${last.action}` : "尚無操作紀錄";
  renderList("waiting", elements.lists.waiting, elements.counts.waiting); renderList("returnReady", elements.lists.returnReady, elements.counts.returnReady); renderList("noShow", elements.lists.noShow, elements.counts.noShow);
}

function requireSession() { if (!activeSession()) { setMessage("請先開始今日診次。"); return false; } return true; }
function callItem(item, message, action = "call") {
  if (!requireSession()) return; const before = snapshot(); const previous = state.items.find((candidate) => candidate.status === "called");
  if (previous && previous.number !== item.number) previous.status = "done";
  item.status = "called"; state.current = item.number; state.lastCalledAt = new Date().toISOString(); state.lastEvent = action; record(action, "doctor", item.number, before); setMessage(message); save(); render();
}
function callNext() { const next = activeItems("waiting")[0]; if (!next) return setMessage("沒有一般等待中的號碼。"); callItem(next, `已叫 ${next.number} 號。`); }
function callReturn() { const next = activeItems("returnReady")[0]; if (!next) return setMessage("目前沒有回號待叫的病人。"); callItem(next, `已依原號叫回 ${next.number} 號。`); }
function recall() { if (!requireSession()) return; const current = state.items.find((item) => item.number === state.current && item.status === "called"); if (!current) return setMessage("目前沒有可重叫的號碼。"); const before = snapshot(); state.lastCalledAt = new Date().toISOString(); state.lastEvent = "recall"; record("recall", "doctor", current.number, before); setMessage(`請再次播報 ${current.number} 號。`); save(); render(); }
function noShow() { if (!requireSession()) return; const current = state.items.find((item) => item.number === state.current && item.status === "called"); if (!current) return setMessage("目前沒有可標記過號的號碼。"); const before = snapshot(); current.status = "noShow"; state.current = null; record("no_show", "doctor", current.number, before); setMessage(`${current.number} 號已標記過號；回來時仍用原號。`); save(); render(); }
function undoLast() {
  if (!requireSession()) return; const event = [...state.events].reverse().find((item) => item.before && !item.undone && !["undo", "session_started", "session_closed"].includes(item.action));
  if (!event) return setMessage("沒有可復原的操作。"); state.items = event.before.items.map((item) => ({ ...item })); state.current = event.before.current; state.lastCalledAt = event.before.lastCalledAt; state.lastEvent = event.before.lastEvent; event.undone = true; record("undo", "doctor", event.number); setMessage(`已復原 ${event.number ?? "上一筆"} 號相關操作。`); save(); render();
}
function startSession() { if (activeSession()) return; const at = new Date().toISOString(); state = { ...defaultState, session: { status: "active", dateKey: dateKey(), startedAt: at, closedAt: null }, events: [{ id: `session-started-${at}`, at, action: "session_started", actor: "doctor", number: null, undone: false }] }; setMessage("今日診次已開始。可由櫃台新增候診號碼。"); save(); render(); }
async function endSession() {
  if (!activeSession() || !window.confirm("確定結束並封存今日匿名候診資料？此動作不能直接復原。")) return;
  if (desktop) { state = normalize(await desktop.archiveAndClose(state)); setMessage("今日診次已封存，已建立本機備份。"); render(); return; }
  state.session.status = "closed"; state.session.closedAt = new Date().toISOString(); record("session_closed", "doctor", null); setMessage("今日診次已封存。"); save(); render();
}

elements.checkinForm.addEventListener("submit", (event) => {
  event.preventDefault(); if (!requireSession()) return; const number = getNumber();
  if (!Number.isInteger(number) || number < 1 || number > 999) return setMessage("請輸入 1 至 999 的號碼。");
  if (state.items.some((item) => item.number === number)) return setMessage("此號碼今日已存在，請使用「過號病人回來」。");
  const before = snapshot(); state.items.push({ number, status: "waiting" }); record("checkin", "reception", number, before); elements.queueNumber.value = ""; setMessage(`${number} 號已新增為等待中。`); save(); render();
});
elements.returnReadyButton.addEventListener("click", () => { if (!requireSession()) return; const number = getNumber(); const item = state.items.find((candidate) => candidate.number === number); if (!item || item.status !== "noShow") return setMessage("請輸入目前處於「過號」狀態的原號。"); const before = snapshot(); item.status = "returnReady"; record("return_ready", "reception", number, before); elements.queueNumber.value = ""; setMessage(`${number} 號已改為回號待叫，醫師可在適當時機叫回。`); save(); render(); });
document.querySelectorAll("[data-action]").forEach((button) => button.addEventListener("click", () => ({ "call-next": callNext, "call-return": callReturn, recall, "no-show": noShow }[button.dataset.action])()));
document.addEventListener("keydown", (event) => {
  elements.shortcutTest.textContent = `程式收到按鍵：${event.key}`;
  const handlers = { [settings.hotkeys.callNext]: callNext, [settings.hotkeys.callReturn]: callReturn, [settings.hotkeys.recall]: recall, [settings.hotkeys.noShow]: noShow, F6: () => desktop?.openWaitingDisplay() };
  if (handlers[event.key]) { event.preventDefault(); handlers[event.key](); }
});
elements.openDisplayButton.addEventListener("click", () => { if (!desktop) return setMessage("候診大螢幕僅能從 Windows 桌面程式開啟。"); void desktop.openWaitingDisplay(); });
elements.startSessionButton.addEventListener("click", startSession); elements.endSessionButton.addEventListener("click", () => void endSession()); elements.undoButton.addEventListener("click", undoLast);
elements.testVoiceButton.addEventListener("click", async () => { if (!desktop) return setMessage("語音測試僅能從 Windows 桌面程式執行。"); setMessage(await desktop.testVoice() ? "已送出候診螢幕語音測試。" : "請先開啟候診大螢幕，再測試語音。"); });
elements.settingsForm.addEventListener("submit", (event) => { event.preventDefault(); settings.hotkeys = { callNext: elements.callNextKey.value, callReturn: elements.callReturnKey.value, recall: elements.recallKey.value, noShow: elements.noShowKey.value }; saveSettings(); setMessage("快捷鍵設定已儲存；請在診所系統旁實測無衝突後再啟用。 "); });
elements.exportAuditButton.addEventListener("click", async () => { if (!desktop) return setMessage("CSV 匯出僅能從 Windows 桌面程式執行。"); const path = await desktop.exportAudit(state); setMessage(path ? "匿名操作紀錄已匯出。" : "已取消匯出。 "); });
[[elements.displayCheck, "display"], [elements.voiceCheck, "voice"], [elements.keypadCheck, "keypad"]].forEach(([field, name]) => field.addEventListener("change", () => { settings.deviceChecks[name] = field.checked; saveSettings(); }));
if (desktop) {
  desktop.loadState().then((saved) => { state = normalize(saved); render(); }); desktop.onStateUpdate((saved) => { state = normalize(saved); render(); });
  desktop.loadSettings().then((saved) => { settings = saved; renderSettings(); });
} else { settings = JSON.parse(localStorage.getItem("ye-neuro-queue-settings") || JSON.stringify(settings)); renderSettings(); }
render();
