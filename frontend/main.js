const $ = (id) => document.getElementById(id);

const state = {
  running: false,
  timer: null,
  statusPoller: null,
  useModelMode: true,
};

const els = {
  modeToggleBtn: $("modeToggleBtn"),
  personRatioThreshold: $("personRatioThreshold"),
  ratioOutput: $("ratioOutput"),
  speakText: $("speakText"),
  speakInterval: $("speakInterval"),
  leftArmIp: $("leftArmIp"),
  leftArmPort: $("leftArmPort"),
  leftTrajectoryName: $("leftTrajectoryName"),
  rightArmIp: $("rightArmIp"),
  rightArmPort: $("rightArmPort"),
  rightTrajectoryName: $("rightTrajectoryName"),
  startBtn: $("startBtn"),
  stopBtn: $("stopBtn"),
  runLeftTrajectoryBtn: $("runLeftTrajectoryBtn"),
  runRightTrajectoryBtn: $("runRightTrajectoryBtn"),
  modelStatus: $("modelStatus"),
  speakStatus: $("speakStatus"),
  decision: $("decision"),
  leftArmStatus: $("leftArmStatus"),
  rightArmStatus: $("rightArmStatus"),
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
  const threshold = Number(els.personRatioThreshold.value);
  const text = els.speakText.value.trim();

  if (!text) {
    throw new Error("播报文本不能为空");
  }

  if (state.useModelMode) {
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
  } else {
    els.modelStatus.textContent = "bypassed";
    els.decision.textContent = "skipped";
  }

  const playRes = await api("/api/speech/play", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  els.speakStatus.textContent = playRes.request_status;
  await runTrajectory("left", { failOnEmpty: false });
  await runTrajectory("right", { failOnEmpty: false });
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

async function runTrajectory(side, options = { failOnEmpty: true }) {
  const arm_ip = side === "left" ? els.leftArmIp.value.trim() : els.rightArmIp.value.trim();
  const arm_port = Number(side === "left" ? els.leftArmPort.value : els.rightArmPort.value) || 8080;
  const trajectory_name = side === "left" ? els.leftTrajectoryName.value.trim() : els.rightTrajectoryName.value.trim();
  if (!arm_ip) {
    if (!options.failOnEmpty) {
      return;
    }
    setError(`${side === "left" ? "左" : "右"}机械臂IP不能为空`);
    return;
  }
  if (!trajectory_name) {
    if (!options.failOnEmpty) {
      return;
    }
    setError("轨迹名称不能为空");
    return;
  }

  try {
    const res = await api("/api/arm/run-trajectory", {
      method: "POST",
      body: JSON.stringify({ arm_ip, arm_port, trajectory_name }),
    });
    if (side === "left") {
      els.leftArmStatus.textContent = res.request_status;
    } else {
      els.rightArmStatus.textContent = res.request_status;
    }
    setError("");
  } catch (err) {
    setError(err.message);
    if (side === "left") {
      els.leftArmStatus.textContent = "error";
    } else {
      els.rightArmStatus.textContent = "error";
    }
  }
}

els.personRatioThreshold.addEventListener("input", () => {
  els.ratioOutput.textContent = Number(els.personRatioThreshold.value).toFixed(2);
});

els.modeToggleBtn.addEventListener("click", () => {
  state.useModelMode = !state.useModelMode;
  els.modeToggleBtn.textContent = state.useModelMode ? "模式：模型联动模式" : "模式：非模型循环模式";
});

els.startBtn.addEventListener("click", start);
els.stopBtn.addEventListener("click", stop);
els.runLeftTrajectoryBtn.addEventListener("click", () => runTrajectory("left"));
els.runRightTrajectoryBtn.addEventListener("click", () => runTrajectory("right"));

refreshSpeechStatus();
