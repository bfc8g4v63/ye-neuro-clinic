const storageKey = "ye-neuro-queue-controller-v1";
let state = JSON.parse(localStorage.getItem(storageKey) || '{"items":[],"current":null}');
const queueChannel = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel("ye-neuro-queue");
const desktop = window.queueDesktop;

const elements = {
  currentNumber: document.querySelector("#currentNumber"),
  currentMeta: document.querySelector("#currentMeta"),
  checkinForm: document.querySelector("#checkinForm"),
  queueNumber: document.querySelector("#queueNumber"),
  returnReadyButton: document.querySelector("#returnReadyButton"),
  openDisplayButton: document.querySelector("#openDisplayButton"),
  formMessage: document.querySelector("#formMessage"),
  todayLabel: document.querySelector("#todayLabel"),
  lists: {
    waiting: document.querySelector("#waitingList"),
    returnReady: document.querySelector("#returnList"),
    noShow: document.querySelector("#noShowList"),
  },
  counts: {
    waiting: document.querySelector("#waitingCount"),
    returnReady: document.querySelector("#returnCount"),
    noShow: document.querySelector("#noShowCount"),
  },
};

const statusLabel = { waiting: "等待中", called: "叫號中", noShow: "過號", returnReady: "回號待叫", done: "已完成" };

function save() {
  localStorage.setItem(storageKey, JSON.stringify(state));
  queueChannel?.postMessage({ type: "queue:update" });
  if (desktop) void desktop.saveState(state);
}
function nowLabel() { return new Intl.DateTimeFormat("zh-TW", { dateStyle: "long" }).format(new Date()); }
function setMessage(message) { elements.formMessage.textContent = message; }
function getNumber() { return Number(elements.queueNumber.value); }
function activeItems(status) { return state.items.filter((item) => item.status === status).sort((a, b) => a.number - b.number); }

function renderList(status, list, count) {
  const items = activeItems(status);
  count.textContent = items.length;
  list.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "目前沒有";
    list.append(empty);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("li");
    row.innerHTML = `<span>${item.number} 號</span><small>${statusLabel[item.status]}</small>`;
    list.append(row);
  });
}

function render() {
  elements.todayLabel.textContent = nowLabel();
  const current = state.items.find((item) => item.number === state.current && item.status === "called");
  elements.currentNumber.textContent = current ? `${current.number} 號` : "尚未叫號";
  elements.currentMeta.textContent = current ? "完成看診後，先在既有系統送出病歷／處方，再按下一個快捷鍵。" : "先由櫃台新增當日候診號碼。";
  renderList("waiting", elements.lists.waiting, elements.counts.waiting);
  renderList("returnReady", elements.lists.returnReady, elements.counts.returnReady);
  renderList("noShow", elements.lists.noShow, elements.counts.noShow);
  save();
}

function callItem(item, message) {
  const previous = state.items.find((candidate) => candidate.status === "called");
  if (previous && previous.number !== item.number) previous.status = "done";
  item.status = "called";
  state.current = item.number;
  state.lastCalledAt = new Date().toISOString();
  state.lastEvent = "call";
  setMessage(message);
  render();
}

function callNext() {
  const next = activeItems("waiting")[0];
  if (!next) return setMessage("沒有一般等待中的號碼。");
  callItem(next, `已叫 ${next.number} 號。`);
}

function callReturn() {
  const next = activeItems("returnReady")[0];
  if (!next) return setMessage("目前沒有回號待叫的病人。");
  callItem(next, `已依原號叫回 ${next.number} 號。`);
}

function recall() {
  const current = state.items.find((item) => item.number === state.current && item.status === "called");
  if (current) {
    state.lastCalledAt = new Date().toISOString();
    state.lastEvent = "recall";
    save();
  }
  setMessage(current ? `請再次播報 ${current.number} 號。` : "目前沒有可重叫的號碼。");
}

function noShow() {
  const current = state.items.find((item) => item.number === state.current && item.status === "called");
  if (!current) return setMessage("目前沒有可標記過號的號碼。");
  current.status = "noShow";
  state.current = null;
  setMessage(`${current.number} 號已標記過號；回來時仍用原號。`);
  render();
}

elements.checkinForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const number = getNumber();
  if (!Number.isInteger(number) || number < 1 || number > 999) return setMessage("請輸入 1 至 999 的號碼。");
  if (state.items.some((item) => item.number === number)) return setMessage("此號碼今日已存在，請使用「過號病人回來」。");
  state.items.push({ number, status: "waiting" });
  elements.queueNumber.value = "";
  setMessage(`${number} 號已新增為等待中。`);
  render();
});

elements.returnReadyButton.addEventListener("click", () => {
  const number = getNumber();
  const item = state.items.find((candidate) => candidate.number === number);
  if (!item || item.status !== "noShow") return setMessage("請輸入目前處於「過號」狀態的原號。\n");
  item.status = "returnReady";
  elements.queueNumber.value = "";
  setMessage(`${number} 號已改為回號待叫，醫師可在適當時機按 F9 叫回。`);
  render();
});

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => ({ "call-next": callNext, "call-return": callReturn, recall, "no-show": noShow }[button.dataset.action])());
});

document.addEventListener("keydown", (event) => {
  const handlers = { F6: () => desktop?.openWaitingDisplay(), F8: callNext, F9: callReturn, F10: recall, F11: noShow };
  if (handlers[event.key]) { event.preventDefault(); handlers[event.key](); }
});

elements.openDisplayButton.addEventListener("click", () => {
  if (!desktop) return setMessage("候診大螢幕僅能從 Windows 桌面程式開啟。");
  void desktop.openWaitingDisplay();
});

if (desktop) {
  desktop.loadState().then((savedState) => { state = savedState; render(); });
  desktop.onStateUpdate((savedState) => { state = savedState; render(); });
}

render();
