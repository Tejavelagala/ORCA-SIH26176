const map = L.map("map").setView([16.9891, 82.2475], 9);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

const coords = {
  Kakinada: [16.9891, 82.2475],
  Visakhapatnam: [17.6868, 83.2185]
};

let boatMarker = L.marker(coords.Kakinada).addTo(map).bindPopup("Query location");
let pfzMarker = null;
let routeLine = null;

async function ask() {
  const query = document.getElementById("query").value.trim();
  const location = document.getElementById("location").value;
  if (!query) return;

  const messages = document.getElementById("messages");
  messages.innerHTML += '<div class="bubble"><b>You:</b> ' + escapeHtml(query) + '</div>';
  messages.innerHTML += '<div class="bubble bot">ORCA is coordinating Ocean, Weather and Geo agents…</div>';
  messages.scrollTop = messages.scrollHeight;

  try {
    const url = "http://127.0.0.1:8000/api/query?q=" +
      encodeURIComponent(query) + "&location=" + encodeURIComponent(location);

    const response = await fetch(url);
    if (!response.ok) throw new Error("API " + response.status);

    const data = await response.json();
    renderResult(data);
  } catch (error) {
    document.getElementById("result").innerHTML =
      '<p class="error">Backend request failed. Make sure FastAPI is running on port 8000.</p>' +
      '<pre>' + escapeHtml(error.message) + '</pre>';
  }
}

function renderResult(data) {
  const risk = data.risk || {};
  const weather = data.agents.weather || {};
  const ocean = data.agents.ocean || {};
  const geo = data.agents.geo || {};
  const pfz = ocean.pfz || {};
  const riskClass = String(risk.status || "UNKNOWN").toLowerCase();

  document.getElementById("result").innerHTML = `
    <div class="risk ${riskClass}">${escapeHtml(risk.status || "UNKNOWN")}</div>
    <p>${escapeHtml(data.explanation || "")}</p>

    <div class="grid">
      <div class="card">🌬 Wind<br><b>${value(weather.wind_speed_kmh, "km/h")}</b></div>
      <div class="card">🌊 Waves<br><b>${value(weather.wave_height_m, "m")}</b></div>
      <div class="card">🌡 Temperature<br><b>${value(weather.temperature_c, "°C")}</b></div>
      <div class="card">🎣 PFZ Demo<br><b>${value(pfz.distance_km, "km")} ${escapeHtml(pfz.direction || "")}</b></div>
    </div>

    <h3>Agent Status</h3>
    <div class="grid">
      <div class="card">🌊 Ocean<br><b>✓ ${escapeHtml(ocean.data_mode || "unknown")}</b></div>
      <div class="card">🌦 Weather<br><b>✓ ${escapeHtml(weather.data_mode || "unknown")}</b></div>
      <div class="card">🗺 Geo<br><b>✓ ${escapeHtml(geo.data_mode || "unknown")}</b></div>
      <div class="card">🚧 Restricted<br><b>${geo.restricted_zone ? "YES" : "NO"}</b></div>
    </div>

    <h3>Why?</h3>
    <ul>${(risk.reasons || []).map(r => "<li>" + escapeHtml(r) + "</li>").join("")}</ul>

    <h3>Evidence</h3>
    <pre>${escapeHtml(JSON.stringify(data.agents, null, 2))}</pre>

    <h3>Route</h3>
    <p>${escapeHtml(data.route?.note || "")}</p>
  `;

  const start = coords[data.location] || coords.Kakinada;
  boatMarker.setLatLng(start);
  map.setView(start, 9);

  if (pfz.latitude && pfz.longitude) {
    if (pfzMarker) map.removeLayer(pfzMarker);
    pfzMarker = L.marker([pfz.latitude, pfz.longitude])
      .addTo(map)
      .bindPopup((pfz.name || "PFZ") + " — DEMO DATA");
  }

  if (routeLine) map.removeLayer(routeLine);
  if (pfz.latitude && pfz.longitude) {
    routeLine = L.polyline([start, [pfz.latitude, pfz.longitude]], {dashArray: "8 8"})
      .addTo(map);
  }
}

function value(v, unit) {
  return v === null || v === undefined ? "N/A" : v + " " + unit;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.getElementById("query").addEventListener("keydown", e => {
  if (e.key === "Enter") ask();
});
