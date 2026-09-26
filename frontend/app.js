const map = L.map("map").setView([16.9891, 82.2475], 9);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

const coords = {
  Kakinada: [16.9891, 82.2475],
  Visakhapatnam: [17.6868, 83.2185],
  Chennai: [13.0827, 80.2707]
};

let boatMarker = L.marker(coords.Kakinada)
  .addTo(map)
  .bindPopup("Query location");

let pfzMarker = null;
let routeLine = null;
let riskCircle = null;

function usePrompt(prompt) {
  const input = document.getElementById("query");
  input.value = prompt;
  input.focus();
}

async function ask() {
  const queryInput = document.getElementById("query");
  const locationInput = document.getElementById("location");
  const button = document.querySelector('button[onclick="ask()"]');

  const query = queryInput.value.trim();
  const location = locationInput.value;

  if (!query) {
    queryInput.focus();
    return;
  }

  const messages = document.getElementById("messages");
  const result = document.getElementById("result");

  messages.innerHTML +=
    '<div class="bubble"><b>You:</b> ' +
    escapeHtml(query) +
    "</div>";

  const loadingId = "orca-loading-" + Date.now();
  messages.innerHTML +=
    '<div id="' + loadingId + '" class="bubble bot">' +
    "ORCA is coordinating Ocean, Weather and Geo agents…" +
    "</div>";

  messages.scrollTop = messages.scrollHeight;

  if (button) {
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.textContent = "Thinking…";
  }

  try {
    const url =
      "http://127.0.0.1:8000/api/query?q=" +
      encodeURIComponent(query) +
      "&location=" +
      encodeURIComponent(location);

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error("API returned HTTP " + response.status);
    }

    const data = await response.json();

    if (!data || !data.risk || !data.agents) {
      throw new Error("Invalid ORCA response received from backend.");
    }

    const loadingBubble = document.getElementById(loadingId);
    if (loadingBubble) {
      loadingBubble.className = "bubble bot";
      loadingBubble.innerHTML =
        "✓ ORCA completed analysis using Ocean, Weather and Geo agents.";
    }

    renderResult(data);

    result.scrollIntoView({
      behavior: "smooth",
      block: "nearest"
    });
  } catch (error) {
    const loadingBubble = document.getElementById(loadingId);

    if (loadingBubble) {
      loadingBubble.className = "bubble bot error";
      loadingBubble.innerHTML =
        "✕ ORCA could not complete the analysis.";
    }

    result.innerHTML =
      '<div class="error">' +
      "<b>Backend request failed.</b><br>" +
      "Make sure FastAPI is running on port 8000." +
      "<pre>" +
      escapeHtml(error.message) +
      "</pre>" +
      "</div>";

    console.error("ORCA request error:", error);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = button.dataset.originalText || "Ask ORCA";
    }
  }
}

function renderResult(data) {
  const risk = data.risk || {};
  const agents = data.agents || {};
  const weather = agents.weather || {};
  const ocean = agents.ocean || {};
  const geo = agents.geo || {};
  const pfz = ocean.pfz || {};

  const status = String(risk.status || "UNKNOWN");
  const riskClass = status.toLowerCase();
  const generatedAt = data.generated_at
    ? new Date(data.generated_at).toLocaleString()
    : "Not available";

  const oceanSource = ocean.source || {};
  const advisory = ocean.advisory || {};
  const weatherSource = weather.source || {};
  const geoSource = geo.source || {};

  const result = document.getElementById("result");

  result.innerHTML = `
    <div class="result-topline">
      <div class="risk ${riskClass}">
        ${escapeHtml(status)}
      </div>
      <span class="decision-mode">
        ${escapeHtml(risk.decision_mode || "deterministic")}
      </span>
    </div>

    <p>
      <b>ORCA Decision:</b>
      ${escapeHtml(data.explanation || "No explanation returned.")}
    </p>

    <div class="grid">
      <div class="card">
        🌬 Wind<br>
        <b>${value(weather.wind_speed_kmh, "km/h")}</b>
      </div>

      <div class="card">
        🌊 Waves<br>
        <b>${value(weather.wave_height_m, "m")}</b>
      </div>

      <div class="card">
        🌡 Temperature<br>
        <b>${value(weather.temperature_c, "°C")}</b>
      </div>

      <div class="card">
        🌧 Rain Probability<br>
        <b>${value(weather.rain_probability_pct, "%")}</b>
      </div>

      <div class="card">
        🎣 PFZ Reference<br>
        <b>${value(pfz.distance_km, "km")} ${escapeHtml(pfz.direction || "")}</b>
      </div>

      <div class="card">
        📡 INCOIS Advisory<br>
        <b>${advisory.available ? "LIVE" : "FALLBACK"}</b>
      </div>

      <div class="card">
        🚧 Restricted Zone<br>
        <b>${geo.restricted_zone ? "YES" : "NO"}</b>
      </div>
    </div>

    <h3>Agent Status</h3>

    <div class="grid">
      <div class="card">
        🌊 Ocean Agent<br>
        <b>✓ ${escapeHtml(ocean.data_mode || "unknown")}</b>
      </div>

      <div class="card">
        🌦 Weather Agent<br>
        <b>✓ ${escapeHtml(weather.data_mode || "unknown")}</b>
      </div>

      <div class="card">
        🗺 Geo Agent<br>
        <b>✓ ${escapeHtml(geo.data_mode || "unknown")}</b>
      </div>

      <div class="card">
        📡 Weather Provider<br>
        <b>${escapeHtml(weather.provider || "unknown")}</b>
      </div>
    </div>

    <h3>Why?</h3>

    <ul>
      ${(risk.reasons || [])
        .map(reason => "<li>" + escapeHtml(reason) + "</li>")
        .join("")}
    </ul>

    <h3>Route Recommendation</h3>

    <p>
      <b>${escapeHtml(data.route?.destination || "PFZ")}</b><br>
      Direction: ${escapeHtml(data.route?.direction || "N/A")}<br>
      Distance: ${value(data.route?.distance_km, "km")}<br>
      ${escapeHtml(data.route?.note || "")}
    </p>

    <h3>INCOIS Advisory</h3>

    <div class="provenance">
      <div><b>Status:</b> ${escapeHtml(advisory.available ? "Live advisory metadata available" : "Using local fallback geometry")}</div>
      <div><b>Forecast date:</b> ${escapeHtml(advisory.forecast_date || "Not available")}</div>
      <div><b>Valid upto:</b> ${escapeHtml(advisory.valid_upto || "Not available")}</div>
      <div><b>Geometry:</b> ${escapeHtml(ocean.geometry_mode || "unknown")}</div>
    </div>

    <h3>Data Provenance</h3>

    <div class="provenance">
      <div><b>Ocean:</b> ${escapeHtml(oceanSource.provider || "Unknown")} · ${escapeHtml(oceanSource.mode || "unknown")}</div>
      <div><b>INCOIS WebGIS:</b> <a class="source-link" href="https://www.incois.gov.in/MarineFisheries/PfzWebGis" target="_blank" rel="noopener">PFZ WebGIS ↗</a></div>
      <div><b>Weather:</b> ${escapeHtml(weatherSource.provider || weather.provider || "Unknown")} · ${escapeHtml(weatherSource.mode || weather.data_mode || "unknown")}</div>
      <div><b>Geo:</b> ${escapeHtml(geoSource.provider || "Unknown")} · ${escapeHtml(geoSource.mode || geo.data_mode || "unknown")}</div>
      <div><b>Response generated:</b> ${escapeHtml(generatedAt)}</div>
    </div>

    <h3>Evidence</h3>

    <pre>${escapeHtml(JSON.stringify(agents, null, 2))}</pre>
  `;

  updateMap(data, pfz);
}

function updateMap(data, pfz) {
  const start = coords[data.location] || coords.Kakinada;
  const status = String(data.risk?.status || "UNKNOWN");

  if (riskCircle) {
    map.removeLayer(riskCircle);
    riskCircle = null;
  }

  const radiusByRisk = {
    SAFE: 2500,
    CAUTION: 4500,
    UNSAFE: 6500,
    BLOCKED: 6500,
    DATA_UNAVAILABLE: 3000
  };

  riskCircle = L.circle(start, {
    radius: radiusByRisk[status] || 3000,
    fillOpacity: 0.08,
    weight: 2
  }).addTo(map).bindPopup(
    "<b>ORCA Risk Area</b><br>" + escapeHtml(status)
  );

  boatMarker.setLatLng(start);
  boatMarker.bindPopup(
    "<b>" + escapeHtml(data.location || "Query location") + "</b>"
  );

  if (pfz.latitude && pfz.longitude) {
    if (pfzMarker) {
      map.removeLayer(pfzMarker);
    }

    pfzMarker = L.marker([pfz.latitude, pfz.longitude])
      .addTo(map)
      .bindPopup(
        "<b>" +
        escapeHtml(pfz.name || "PFZ") +
        "</b><br>" +
        escapeHtml((data.agents?.ocean?.source?.provider || "INCOIS PFZ reference")) +
        " · " +
        escapeHtml(data.agents?.ocean?.source?.mode || "unknown")
      );

    if (routeLine) {
      map.removeLayer(routeLine);
    }

    routeLine = L.polyline(
      [start, [pfz.latitude, pfz.longitude]],
      { dashArray: "8 8" }
    ).addTo(map);

    map.fitBounds(
      L.latLngBounds([
        start,
        [pfz.latitude, pfz.longitude]
      ]),
      { padding: [40, 40] }
    );
  } else {
    map.setView(start, 9);

    if (routeLine) {
      map.removeLayer(routeLine);
      routeLine = null;
    }
  }
}

function value(v, unit) {
  if (v === null || v === undefined || v === "") {
    return "N/A";
  }

  return escapeHtml(String(v)) + " " + escapeHtml(unit);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.getElementById("query").addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();
    ask();
  }
});
