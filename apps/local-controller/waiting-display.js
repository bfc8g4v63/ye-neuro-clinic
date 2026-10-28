const storageKey = "ye-neuro-queue-controller-v1";
const queueChannel = new BroadcastChannel("ye-neuro-queue");
const currentNumber = document.querySelector("#currentNumber");
const updatedAt = document.querySelector("#updatedAt");

function formatTime(value) {
  if (!value) return "尚未接收到現場叫號資料";
  return `最後叫號：${new Intl.DateTimeFormat("zh-TW", { hour: "2-digit", minute: "2-digit" }).format(new Date(value))}`;
}

function render() {
  const state = JSON.parse(localStorage.getItem(storageKey) || '{"items":[],"current":null}');
  const current = state.items.find((item) => item.number === state.current && item.status === "called");
  currentNumber.textContent = current ? current.number : "—";
  updatedAt.textContent = formatTime(state.lastCalledAt);
  document.title = current ? `請 ${current.number} 號｜葉神經科` : "葉神經科｜候診顯示";
}

queueChannel.addEventListener("message", render);
window.addEventListener("storage", render);
setInterval(render, 3000);
render();
