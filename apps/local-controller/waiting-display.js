const storageKey = "ye-neuro-queue-controller-v1";
const queueChannel = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel("ye-neuro-queue");
const desktop = window.queueDesktop;
const currentNumber = document.querySelector("#currentNumber");
const updatedAt = document.querySelector("#updatedAt");
let lastAnnouncement = null;

function formatTime(value) {
  if (!value) return "尚未接收到現場叫號資料";
  return `最後叫號：${new Intl.DateTimeFormat("zh-TW", { hour: "2-digit", minute: "2-digit" }).format(new Date(value))}`;
}

function announce(state, current) {
  const marker = `${state.lastEvent || ""}:${state.lastCalledAt || ""}`;
  if (!current || !state.lastEvent || marker === lastAnnouncement || !("speechSynthesis" in window)) return;
  lastAnnouncement = marker;
  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(`請 ${current.number} 號進入診間`);
  speech.lang = "zh-TW";
  speech.rate = 0.8;
  window.speechSynthesis.speak(speech);
}

function render(nextState, shouldAnnounce = false) {
  const state = nextState || JSON.parse(localStorage.getItem(storageKey) || '{"items":[],"current":null}');
  const current = state.items.find((item) => item.number === state.current && item.status === "called");
  currentNumber.textContent = current ? current.number : "—";
  updatedAt.textContent = formatTime(state.lastCalledAt);
  document.title = current ? `請 ${current.number} 號｜葉神經科` : "葉神經科｜候診顯示";
  if (shouldAnnounce) announce(state, current);
}

queueChannel?.addEventListener("message", () => render(null, true));
window.addEventListener("storage", render);
if (desktop) {
  desktop.loadState().then((state) => render(state));
  desktop.onStateUpdate((state) => render(state, true));
} else {
  setInterval(render, 3000);
  render();
}
