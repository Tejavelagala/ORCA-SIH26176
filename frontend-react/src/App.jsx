import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const LOCATIONS = {
  Kakinada: [16.9891, 82.2475],
  Visakhapatnam: [17.6868, 83.2185],
  Chennai: [13.0827, 80.2707],
};

const MISSIONS = {
  Fisher: "Give me a fishing safety brief including PFZ reference, sea conditions, weather and geographic restrictions.",
  "Ship Operator": "Give me a marine operating brief including weather, wave conditions, ocean evidence and route context.",
  "Coast Guard": "Give me a coastal safety brief focusing on hazards, restricted zones, weather and ocean evidence.",
  "Disaster Team": "Give me a disaster-response marine situation brief focusing on hazards, weather, ocean conditions and data limitations.",
};

const DEMOS = ["safe", "caution", "unsafe", "cyclone_alert", "blocked", "data_unavailable"];

function App() {
  const [query, setQuery] = useState("Is it safe to fish near Kakinada tomorrow morning?");
  const [location, setLocation] = useState("Kakinada");
  const [language, setLanguage] = useState("en-IN");
  const [result, setResult] = useState(null);
  const [system, setSystem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [watch, setWatch] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const timer = useRef(null);
  const lastRisk = useRef(null);

  useEffect(() => {
    fetch(API + "/api/system/status").then(r => r.json()).then(setSystem).catch(() => {});
    return () => timer.current && clearInterval(timer.current);
  }, []);

  async function request(url, replaceQuery = false) {
    setLoading(true);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeout);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || data.detail || "Request failed");
      setResult(data);
      if (replaceQuery && data.query) setQuery(data.query);
      return data;
    } catch (error) {
      const message = error.name === "AbortError"
        ? "ORCA request timed out. Check that the backend is running."
        : error.message || "Unable to reach ORCA backend.";
      addAlert("error", message);
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function postAction(path, payload) {
    try {
      const response = await fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Action failed");
      addAlert("neutral", data.message || data.status || "ORCA action completed.");
      return data;
    } catch (error) {
      addAlert("error", error.message || "ORCA action failed.");
      return null;
    }
  }

  async function sendFallback(channel) {
    if (!result) return;
    await postAction("/api/fallback/message", { channel, result });
  }

  async function escalate(target) {
    if (!result) return;
    const data = await postAction("/api/escalate", { target, result });
    if (data) addAlert("neutral", "Human review queued for " + target.replace("_", " ") + ".");
  }

  async function loadOfflineSnapshot() {
    try {
      const response = await fetch(API + "/api/offline/snapshot?location=" + encodeURIComponent(location));
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "No offline snapshot available");
      setResult(data);
      addAlert("neutral", "Last-known-good offline snapshot loaded.");
    } catch (error) {
      addAlert("error", error.message || "Offline snapshot unavailable.");
    }
  }

  async function ask(text = query) {
    const url = API + "/api/query?q=" + encodeURIComponent(text) +
      "&location=" + encodeURIComponent(location) +
      "&language=" + encodeURIComponent(language);
    return request(url);
  }

  async function runDemo(scenario) {
    const url = API + "/api/demo?scenario=" + encodeURIComponent(scenario) +
      "&location=" + encodeURIComponent(location);
    return request(url, true);
  }

  function runMission(name) {
    const text = MISSIONS[name];
    setQuery(text);
    ask(text);
  }

  function addAlert(type, text) {
    setAlerts(items => [
      { type, text, time: new Date().toLocaleTimeString() },
      ...items,
    ].slice(0, 8));
  }

  async function checkAlert() {
    const text = "Check current marine risk and identify any condition that should trigger a proactive alert.";
    const data = await ask(text);
    if (!data) return;
    const status = data.risk?.status || "UNKNOWN";
    const changed = lastRisk.current !== null && lastRisk.current !== status;
    if (lastRisk.current === null) addAlert("neutral", location + " initial risk: " + status);
    else if (changed) addAlert(status.toLowerCase(), location + " risk changed: " + lastRisk.current + " → " + status);
    lastRisk.current = status;
  }

  function toggleWatch() {
    if (watch) {
      clearInterval(timer.current);
      timer.current = null;
      lastRisk.current = null;
      setWatch(false);
      addAlert("neutral", "Marine Alert Watch stopped.");
    } else {
      setWatch(true);
      addAlert("neutral", "Marine Alert Watch enabled for " + location + ".");
      checkAlert();
      timer.current = setInterval(checkAlert, 60000);
    }
  }

  function startVoice() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      addAlert("error", "Voice input is not supported by this browser.");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = language;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = e => setQuery(e.results[0][0].transcript);
    recognition.onerror = () => addAlert("error", "Voice input could not be captured.");
    recognition.start();
  }

  function speak() {
    if (!result?.explanation || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(result.explanation);
    u.lang = language;
    window.speechSynthesis.speak(u);
  }

  const risk = result?.risk?.status || "READY";
  const weather = result?.agents?.weather || {};
  const ocean = result?.agents?.ocean || {};
  const geo = result?.agents?.geo || {};
  const pfz = ocean.pfz || {};
  const advisory = ocean.advisory || {};
  const route = result?.route || {};

  return <div className="app">
    <header>
      <div>
        <div className="brand"><span>ORCA</span><b>SIH-26176</b></div>
        <p>Marine EcOsystem Reasoning with Collaborative Agents</p>
      </div>
      <div className="header-status">● MULTI-AGENT INTELLIGENCE</div>
    </header>

    <div className="architecture">
      USER QUERY <i>→</i> INTENT <i>→</i> LANGGRAPH ORCHESTRATOR <i>→</i> OCEAN + WEATHER + GEO <i>→</i> RISK ENGINE <i>→</i> EXPLANATION
    </div>

    <main>
      <section className="hero panel">
        <div>
          <small>CONVERSATIONAL MARINE DECISION SUPPORT</small>
          <h1>Ask the ocean. <em>See the evidence.</em></h1>
          <p>ORCA coordinates specialized agents, applies explicit deterministic rules, and returns an auditable marine intelligence brief.</p>
        </div>
        <div className={"risk-badge " + risk.toLowerCase()}><b>{risk}</b><small>{result?.risk?.score ?? "—"} / 100 risk</small></div>
      </section>

      <section className="panel ask-panel">
        <div className="section-head"><h2>Ask ORCA</h2><span>{loading ? "● PROCESSING" : "● READY"}</span></div>
        <textarea value={query} onChange={e => setQuery(e.target.value)} />
        <div className="controls">
          <select value={location} onChange={e => setLocation(e.target.value)}>
            {Object.keys(LOCATIONS).map(x => <option key={x}>{x}</option>)}
          </select>
          <select value={language} onChange={e => setLanguage(e.target.value)}>
            <option value="en-IN">English</option><option value="te-IN">తెలుగు</option><option value="hi-IN">हिन्दీ</option>
          </select>
          <button onClick={startVoice}>🎙 Voice</button>
          <button onClick={() => ask()} disabled={loading || !query.trim()}>{loading ? "Working…" : "Ask ORCA"}</button>
        </div>
        <div className="chips">
          {Object.keys(MISSIONS).map(m => <button key={m} onClick={() => runMission(m)}>{m}</button>)}
          <button onClick={() => ask("Find the PFZ reference near " + location)}>🛰 PFZ Search</button>
          <button onClick={() => ask("Check marine sea conditions near " + location)}>🌊 Sea State</button>
        </div>
      </section>

      <section className="panel">
        <div className="section-head"><h2>Presentation Scenarios</h2><span>Same deterministic Risk Engine</span></div>
        <div className="chips">
          {DEMOS.map(s => <button key={s} onClick={() => runDemo(s)}>{s.replace("_", " ").toUpperCase()}</button>)}
        </div>
      </section>

      <section className="grid-3">
        <AgentCard title="Ocean Agent" icon="🌊" data={ocean} />
        <AgentCard title="Weather Agent" icon="🌤" data={weather} />
        <AgentCard title="Geo Agent" icon="🗺" data={geo} />
      </section>

      {result && <section className="panel decision">
        <div className="section-head"><h2>Decision & Evidence</h2><span>{result.orchestration || "workflow"} · {result.intent?.intent || "general"}</span></div>
        <div className="metrics">
          <Metric label="Wind" value={weather.wind_speed_kmh} unit="km/h" />
          <Metric label="Wave" value={weather.wave_height_m} unit="m" />
          <Metric label="Rain" value={weather.rain_probability_pct} unit="%" />
          <Metric label="Risk Score" value={result.risk?.score} unit="/100" />
          <Metric label="Confidence" value={result.risk?.confidence != null ? Math.round(result.risk.confidence * 100) : null} unit="%" />
          <Metric label="Forecast" value={weather.forecast_time ? formatDate(weather.forecast_time) : "Demo"} unit="" />
        </div>
        <div className="evidence-strip">
          <div><small>PFZ Advisory</small><b>{advisory.available ? "Available" : "Not available"}</b></div>
          <div><small>Forecast Period</small><b>{weather.forecast_period || "Not specified"}</b></div>
          <div><small>Geo Status</small><b>{geo.eez_status || "Unknown"}</b></div>
          <div><small>Route</small><b>{route.safe_to_navigate ? "Reference available" : "Restricted / unavailable"}</b></div>
        </div>
        <div className="explanation">{result.explanation}<button className="speak" onClick={speak}>🔊</button></div><div className="two-col intelligence-row">
          <div className="fishing-card"><h3>🎣 Fishing Intelligence</h3><p><b>Score:</b> {ocean.fishing_intelligence?.fishing_score ?? "N/A"} / 100 · {ocean.fishing_intelligence?.band || "Unavailable"}</p>{(ocean.fishing_intelligence?.candidates || []).map((x) => <div className="factor" key={x.rank}><b>#{x.rank} {x.name}</b><span>SST {x.sst_c}°C · Chl-a {x.chlorophyll_mg_m3} · {x.distance_km} km · {x.best_window}</span></div>)}<small>{ocean.fishing_intelligence?.disclaimer}</small></div>
          <div><h3>📈 Risk Timeline</h3><div className="timeline">{(result.risk_timeline || []).map((x, i) => <div className="timeline-item" key={i}><b>{x.status}</b><span>{x.score ?? "—"}/100 · {x.confidence != null ? Math.round(x.confidence*100) : "—"}%</span><small>{x.time || "demo"}</small></div>)}</div></div>
        </div>
        <div className="action-bar">
          <button onClick={() => sendFallback("sms")}>📱 SMS Fallback</button>
          <button onClick={() => sendFallback("ivr")}>☎ IVR Fallback</button>
          <button onClick={() => escalate("coast_guard")}>🚨 Coast Guard Review</button>
          <button onClick={() => escalate("incois")}>🌊 INCOIS Review</button>
          <button onClick={loadOfflineSnapshot}>💾 Last-Known-Good</button>
        </div>
        <div className="route-card">
          <div><b>Route Context</b><span>Prototype reference · not navigation</span></div>
          <div className="route-metrics">
            <Metric label="Distance" value={result.route?.distance_km} unit="km" />
            <Metric label="Bearing" value={result.route?.computed_bearing_degrees} unit="°" />
            <Metric label="Direction" value={result.route?.computed_direction || "N/A"} unit="" />
            <Metric label="Navigation" value={result.route?.safe_to_navigate ? "Reference available" : "Do not navigate"} unit="" />
          </div>
          <small>{result.route?.disclaimer || "Straight-line prototype route context only."}</small>
        </div>
        <div className="flow">{(result.trace || []).map((x, i) => <React.Fragment key={x.stage}><div><b>{i + 1}. {x.stage}</b><small>{x.detail}</small></div>{i < (result.trace || []).length - 1 && <i>→</i>}</React.Fragment>)}</div>
        <div className="advisory-card">
          <div><b>INCOIS PFZ Evidence</b><span>{advisory.available ? "Live advisory metadata" : "No live advisory metadata"}</span></div>
          <p>Forecast date: {advisory.forecast_date || "Not available"}</p>
          <p>Valid up to: {advisory.valid_upto || "Not available"}</p>
          <small>{ocean.source?.note || "PFZ geometry and advisory scope are shown with provenance."}</small>
        </div>
        <div className="two-col">
          <div><h3>Risk Factors</h3>{(result.risk?.factors || []).map((f, i) => <div className="factor" key={i}><b>{f.effect}</b><span>{f.factor}: {JSON.stringify(f.value)}</span></div>)}</div>
          <div><h3>Provenance</h3><div className="provenance">
            <p><b>Ocean:</b> {ocean.source?.provider} · {ocean.source?.mode}</p>
            <p><b>Weather:</b> {weather.source?.provider} · {weather.source?.mode}</p>
            <p><b>Geo:</b> {geo.source?.provider} · {geo.source?.mode}</p>
            <p><b>PFZ geometry:</b> {ocean.geometry_mode || "unknown"}</p>
            <p><b>Forecast period:</b> {weather.forecast_period || "not specified"}</p>
            <p><b>Cache:</b> {result.cache?.backend || "n/a"} / {result.cache?.hit ? "HIT" : "MISS"}</p>
            <p><b>Persistence:</b> {result.persistence || "disabled"}</p>
            <p><b>Risk authority:</b> {result.evidence_summary?.risk_authority || "deterministic_risk_engine"}</p>
            <p><b>Knowledge:</b> {result.knowledge?.provider || "ChromaDB"} · {result.knowledge?.results?.length ?? 0} context items</p>
            <p><b>Evidence ledger:</b> {result.evidence_ledger?.length ?? 0} auditable metrics</p>
          </div></div>
        </div>
      </section>}

      <section className="panel">
        <div className="section-head"><h2>Marine Evidence Map</h2><span>Visualization only · not navigation</span></div>
        <Map location={location} pfz={pfz} risk={risk} geo={geo} />
      </section>

      <section className="panel">
        <div className="section-head"><h2>Marine Alert Watch</h2><button onClick={toggleWatch}>{watch ? "Stop Watch" : "Enable Watch"}</button></div>
        <p className="muted">{watch ? "Active · approximately every 60 seconds" : "Opt-in prototype monitoring"}</p><div className="provenance"><b>Proactive geofencing:</b> risk changes are detected by the watch layer; external SMS/IVR notifications remain adapter-based unless configured.</div>
        <div className="alerts">{alerts.map((a, i) => <div className={"alert " + a.type} key={i}><time>{a.time}</time>{a.text}</div>)}</div>
      </section>

      <section className="panel">
        <div className="section-head"><h2>ORCA Knowledge & Evidence Layer</h2><span>ChromaDB / deterministic fallback</span></div>
        <p className="muted">The knowledge layer stores source/product context for grounded explanations. It does not make the safety decision.</p>
        <div className="gateway-grid">
          <Gateway name="INCOIS PFZ" href="https://www.incois.gov.in/MarineFisheries/PfzWebGis" />
          <Gateway name="Ocean State Forecast" href="https://www.incois.gov.in/oceanservices/osfforecast.jsp" />
          <Gateway name="MOSDAC" href="https://mosdac.gov.in/" />
          <Gateway name="Bhuvan / GIS" href="https://bhuvan.nrsc.gov.in/" />
        </div>
        <div className="provenance">
          <p><b>Knowledge provider:</b> {system?.knowledge_base?.provider || "ChromaDB"}</p>
          <p><b>Mode:</b> {system?.knowledge_base?.mode || "loading"}</p>
          <p><b>Indexed documents:</b> {system?.knowledge_base?.documents ?? "loading"}</p>
          <p><b>Risk authority:</b> deterministic Risk Engine</p>
        </div>
      </section>

      <section className="panel">
        <div className="section-head"><h2>System & Authoritative Gateways</h2><span>{system?.orchestration || "loading"}</span></div>
        <div className="gateway-grid">
          <Gateway name="INCOIS PFZ" href="https://www.incois.gov.in/MarineFisheries/PfzWebGis" />
          <Gateway name="INCOIS Ocean State Forecast" href="https://www.incois.gov.in/oceanservices/osfforecast.jsp" />
          <Gateway name="IMD Marine" href="https://mausam.imd.gov.in/responsive/marine_forecast.php" live={system?.imd_configured} />
          <Gateway name="MOSDAC" href="https://mosdac.gov.in/" />
        </div>
        <div className="status-grid">
          <Status name="LangGraph" value={system?.orchestration || "configured"} />
          <Status name="Redis" value={system?.redis_configured ? "configured" : "memory fallback"} />
          <Status name="PostgreSQL" value={system?.postgres_configured ? "configured" : "optional"} />
          <Status name="LLM" value={system?.llm_configured ? "configured" : "deterministic fallback"} />
          <Status name="GIS" value={system?.gis_configured ? "configured" : "not configured"} />
          <Status name="IMD" value={system?.imd_configured ? "configured" : "adapter ready"} />
          <Status name="Knowledge" value={system?.knowledge_base?.mode || "fallback"} />
          <Status name="Bhashini" value={system?.language_layer?.mode || "local fallback"} />
          <Status name="MOSDAC" value={system?.satellite?.mode || "gateway"} />
          <Status name="SMS / IVR" value={system?.channels?.sms || "adapter"} />
        </div>
      </section>
    </main>

    <footer>ORCA · SIH-26176 · multi-agent marine intelligence · deterministic Risk Engine remains authoritative · provider/demo provenance is explicit.</footer>
  </div>;
}

function AgentCard({ title, icon, data }) {
  return <div className="panel agent">
    <div className="agent-title"><span>{icon}</span><b>{title}</b><small>{data.data_mode || data.source?.mode || "unknown"}</small></div>
    <p>{data.source?.provider || data.provider || "No provider"}</p>
    <pre>{JSON.stringify({
      pfz: data.pfz,
      forecast_time: data.forecast_time,
      forecast_period: data.forecast_period,
      eez_status: data.eez_status,
      restricted_zone: data.restricted_zone,
      satellite: data.satellite
    }, null, 2)}</pre>
  </div>;
}
function Metric({ label, value, unit }) { return <div className="metric"><small>{label}</small><b>{value ?? "N/A"} {unit}</b></div>; }
function Gateway({ name, href, live }) { return <a className="gateway" href={href} target="_blank" rel="noreferrer"><b>{name}</b><small>{live ? "Configured" : "Official gateway"}</small></a>; }
function formatDate(value) {
  try {
    return new Date(value).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return value;
  }
}

function Status({ name, value }) { return <div className="status"><small>{name}</small><b>{String(value)}</b></div>; }

function Map({ location, pfz, risk, geo }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const map = L.map(ref.current).setView(LOCATIONS[location], 8);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors" }).addTo(map);
    L.marker(LOCATIONS[location]).addTo(map).bindPopup(location);
    if (pfz.latitude && pfz.longitude) {
      L.marker([pfz.latitude, pfz.longitude]).addTo(map).bindPopup(pfz.name || "PFZ reference");
      L.polyline([LOCATIONS[location], [pfz.latitude, pfz.longitude]], { dashArray: "8 8" }).addTo(map);
      map.fitBounds(L.latLngBounds([LOCATIONS[location], [pfz.latitude, pfz.longitude]]), { padding: [30, 30] });
    }
    const layers = geo?.matched_layers || [];
    layers.forEach(layer => {
      const geometry = layer.geometry;
      if (geometry?.type === "Polygon") {
        const rings = geometry.coordinates?.[0] || [];
        if (rings.length) {
          L.polygon(rings.map(([lon, lat]) => [lat, lon]), { dashArray: "6 4" })
            .addTo(map)
            .bindPopup(layer.name || "Configured geofence");
        }
      }
    });
    return () => map.remove();
  }, [location, pfz.latitude, pfz.longitude, JSON.stringify(geo?.matched_layers || [])]);
  return <div className="map-wrap"><div className="map" ref={ref}></div><div className={"map-label " + risk.toLowerCase()}>{risk} · evidence + geofence map</div></div>;
}

export default App;
