const ORCA_MISSION_PROMPTS = {
  fisher: "Give me a fishing safety brief near the selected location, including PFZ reference, sea conditions, weather and any geographic restrictions.",
  ship: "Give me a marine operating brief near the selected location, including weather, wave conditions, ocean evidence and route context.",
  coastguard: "Give me a coastal safety brief near the selected location, focusing on hazards, restricted zones, weather and ocean evidence.",
  disaster: "Give me a disaster-response marine situation brief near the selected location, focusing on hazards, weather, ocean conditions and data limitations."
};

let alertWatchTimer = null;
let alertWatchBusy = false;
let alertLastStatus = null;

function runMission(mode) {
  const prompt = ORCA_MISSION_PROMPTS[mode];
  if (!prompt) return;
  const input = document.getElementById("query");
  if (input) input.value = prompt;
  const messages = document.getElementById("messages");
  if (messages) {
    messages.innerHTML += '<div class="bubble"><b>Mission Mode:</b> ' +
      escapeHtml(mode.toUpperCase()) + ' brief selected.</div>';
    messages.scrollTop = messages.scrollHeight;
  }
  ask();
}

function toggleAlertWatch() {
  if (alertWatchTimer) {
    stopAlertWatch();
  } else {
    startAlertWatch();
  }
}

function startAlertWatch() {
  const location = document.getElementById("location").value;
  alertLastStatus = null;
  alertWatchTimer = setInterval(runAlertCheck, 60000);
  updateAlertUi(true, "Watching " + location + " every 60 seconds.");
  addAlert("neutral", "Alert Watch enabled for " + location + ".");
  runAlertCheck();
}

function stopAlertWatch() {
  clearInterval(alertWatchTimer);
  alertWatchTimer = null;
  alertLastStatus = null;
  updateAlertUi(false, "Opt-in prototype monitoring is stopped.");
  addAlert("neutral", "Alert Watch stopped.");
}

async function runAlertCheck() {
  if (alertWatchBusy) return;
  alertWatchBusy = true;

  const location = document.getElementById("location").value;
  const query = "Check current marine risk and identify any condition that should trigger a proactive alert.";

  try {
    const url = "http://127.0.0.1:8000/api/query?q=" +
      encodeURIComponent(query) +
      "&location=" + encodeURIComponent(location) +
      "&language=en-IN";

    const response = await fetch(url);
    if (!response.ok) throw new Error("HTTP " + response.status);

    const data = await response.json();
    const status = String(data.risk?.status || "UNKNOWN");
    const reasons = data.risk?.reasons || [];

    const changed = alertLastStatus !== null && alertLastStatus !== status;
    const firstCheck = alertLastStatus === null;
    alertLastStatus = status;

    if (firstCheck) {
      addAlert("neutral", "Initial risk status for " + location + ": " + status + ".");
    } else if (changed) {
      if (status === "CAUTION") {
        addAlert("caution", "Risk changed to CAUTION at " + location + ": " + (reasons[0] || "Elevated conditions detected."));
      } else if (status === "UNSAFE" || status === "BLOCKED") {
        addAlert("danger", "Risk changed to " + status + " at " + location + ": " + (reasons[0] || "Risk condition detected."));
      } else if (status === "DATA_UNAVAILABLE") {
        addAlert("unknown", "Risk changed to DATA_UNAVAILABLE at " + location + ".");
      } else {
        addAlert("safe", "Risk returned to SAFE at " + location + ".");
      }
    }

    updateAlertUi(true, "Last checked " + new Date().toLocaleTimeString() + " · status " + status);
  } catch (error) {
    addAlert("unknown", "Alert check failed: " + error.message);
    updateAlertUi(true, "Watch is active; latest check failed.");
  } finally {
    alertWatchBusy = false;
  }
}

function updateAlertUi(active, detail) {
  const button = document.getElementById("alert-toggle");
  const indicator = document.getElementById("alert-indicator");
  const state = document.getElementById("alert-state");
  const detailNode = document.getElementById("alert-detail");

  if (button) button.textContent = active ? "Stop Alert Watch" : "Enable Alert Watch";
  if (indicator) indicator.className = "alert-indicator " + (active ? "on" : "off");
  if (state) state.textContent = active ? "Watch is active" : "Watch is off";
  if (detailNode) detailNode.textContent = detail;
}

function addAlert(type, message) {
  const feed = document.getElementById("alert-feed");
  if (!feed) return;

  const item = document.createElement("div");
  item.className = "alert-item " + type;
  item.innerHTML =
    '<span class="alert-time">' + escapeHtml(new Date().toLocaleTimeString()) + '</span>' +
    '<span>' + escapeHtml(message) + '</span>';

  feed.prepend(item);

  while (feed.children.length > 5) {
    feed.removeChild(feed.lastElementChild);
  }
}
