const $ = (id) => document.getElementById(id);

const state = {
  running: false,
  timer: null,
  statusPoller: null,
};

const els = {
  enableModelService: $("enableModelService"),
  personRatioThreshold: $("personRatioThreshold"),
  ratioOutput: $("ratioOutput"),
  speakText: $("speakText"),
  speakInterval: $("speakInterval"),
  startBtn: $("startBtn"),
  stopBtn: $("stopBtn"),
  modelStatus: $("modelStatus"),
  speakStatus: $("speakStatus"),
  decision: $("decision"),
  lastError: $("lastError"),
};

function setError(msg) {
  els.lastError.textContent = msg || "-";
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message || JSON.stringify(body) || `HTTP ${res.status}`);
  }
  return res.json();
}

async function runOneRound() {
  const enable = els.enableModelService.checked;
  const threshold = Number(els.personRatioThreshold.value);
  const text = els.speakText.value.trim();

  if (!text) {
    throw new Error("播报文本不能为空");
  }

  if (enable) {
    els.modelStatus.textContent = "checking";
    const decisionRes = await api("/api/detect/person-decision", {
      method: "POST",
      body: JSON.stringify({ person_ratio_threshold: threshold }),
    });
    els.decision.textContent = String(decisionRes.result);
    els.modelStatus.textContent = "done";
    if (!decisionRes.result) {
      return;
    }
  }

  const playRes = await api("/api/speech/play", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  els.speakStatus.textContent = playRes.request_status;
}

async function refreshSpeechStatus() {
  try {
    const statusRes = await api("/api/speech/status");
    els.speakStatus.textContent = statusRes.status;
    return statusRes.status;
  } catch (err) {
    setError(err.message);
    return "error";
  }
}

async function loop() {
  if (!state.running) return;
  try {
    await runOneRound();
    setError("");
  } catch (err) {
    setError(err.message);
  }

  const intervalMs = Number(els.speakInterval.value || 3000);
  state.timer = setTimeout(loop, intervalMs);
}

async function start() {
  if (state.running) return;
  state.running = true;
  state.statusPoller = setInterval(refreshSpeechStatus, 800);
  await loop();
}

async function stop() {
  state.running = false;
  if (state.timer) clearTimeout(state.timer);
  if (state.statusPoller) clearInterval(state.statusPoller);
  try {
    const stopRes = await api("/api/speech/stop", { method: "POST" });
    els.speakStatus.textContent = stopRes.request_status;
  } catch (err) {
    setError(err.message);
  }
}

els.personRatioThreshold.addEventListener("input", () => {
  els.ratioOutput.textContent = Number(els.personRatioThreshold.value).toFixed(2);
});
els.startBtn.addEventListener("click", start);
els.stopBtn.addEventListener("click", stop);

refreshSpeechStatus();
