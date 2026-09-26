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
  "Disaster Team": "Give me a disaster-response marine situation brief focusing on hazards, weather, ocean conditions and data limitations."
};

function App() {
  const [query, setQuery] = useState("Is it safe to fish near Kakinada tomorrow morning?");
  const [location, setLocation] = useState("Kakinada");
  const [language, setLanguage] = useState("en-IN");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [system, setSystem] = useState(null);
  const [watch, setWatch] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const timer = useRef(null);

  useEffect(() => {
    fetch(API + "/api/system/status").then(r => r.json()).then(setSystem).catch(() => {});
    return () => timer.current && clearInterval(timer.current);
  }, []);

  async function ask(customQuery=query) {
    setLoading(true);
    try {
      const url = API + "/api/query?q=" + encodeURIComponent(customQuery) +
        "&location=" + encodeURIComponent(location) +
        "&language=" + encodeURIComponent(language);
      const response = await fetch(url);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || "Request failed");
      setResult(data);
    } catch (error) {
      setAlerts(a => [{type:"error", text:error.message, time:new Date().toLocaleTimeString()}, ...a].slice(0,6));
    } finally {
      setLoading(false);
    }
  }

  function runMission(name) {
    const text = MISSIONS[name];
    setQuery(text);
    ask(text);
  }

  async function checkAlert() {
    try {
      const url = API + "/api/query?q=" + encodeURIComponent("Check current marine risk and identify any condition that should trigger a proactive alert.") +
        "&location=" + encodeURIComponent(location) + "&language=en-IN";
      const data = await (await fetch(url)).json();
      const status = data.risk?.status || "UNKNOWN";
      setResult(data);
      setAlerts(a => [{type:status.toLowerCase(), text:location + " risk: " + status, time:new Date().toLocaleTimeString()}, ...a].slice(0,6));
    } catch {}
  }

  function toggleWatch() {
    if (watch) {
      clearInterval(timer.current);
      timer.current = null;
      setWatch(false);
    } else {
      checkAlert();
      timer.current = setInterval(checkAlert, 60000);
      setWatch(true);
    }
  }

  const risk = result?.risk?.status || "READY";
  const weather = result?.agents?.weather || {};
  const ocean = result?.agents?.ocean || {};
  const geo = result?.agents?.geo || {};
  const pfz = ocean.pfz || {};

  return <div className="app">
    <header>
      <div>
        <div className="brand"><span>ORCA</span><b>PROTOTYPE</b></div>
        <p>Marine EcOsystem Reasoning with Collaborative Agents · SIH-26176</p>
      </div>
      <div className="header-status">● MULTI-AGENT INTELLIGENCE</div>
    </header>

    <div className="architecture">
      USER QUERY <i>→</i> INTENT <i>→</i> ORCHESTRATOR <i>→</i> OCEAN + WEATHER + GEO <i>→</i> DETERMINISTIC RISK ENGINE <i>→</i> EXPLANATION
    </div>

    <main>
      <section className="hero panel">
        <div>
          <small>CONVERSATIONAL MARINE DECISION SUPPORT</small>
          <h1>Ask the ocean. <em>See the evidence.</em></h1>
          <p>ORCA coordinates specialized agents, applies explicit safety rules, and returns an auditable marine intelligence brief.</p>
        </div>
        <div className={"risk-badge " + risk.toLowerCase()}>{risk}</div>
      </section>

      <section className="panel ask-panel">
        <div className="section-head"><h2>Ask ORCA</h2><span>{loading ? "● PROCESSING" : "● READY"}</span></div>
        <textarea value={query} onChange={e=>setQuery(e.target.value)} />
        <div className="controls">
          <select value={location} onChange={e=>setLocation(e.target.value)}>{Object.keys(LOCATIONS).map(x=><option key={x}>{x}</option>)}</select>
          <select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en-IN">English</option><option value="te-IN">తెలుగు</option><option value="hi-IN">हिन्दी</option></select>
          <button onClick={()=>ask()} disabled={loading}>{loading ? "Working…" : "Ask ORCA"}</button>
        </div>
        <div className="chips">
          {Object.keys(MISSIONS).map(m=><button key={m} onClick={()=>runMission(m)}>{m}</button>)}
          <button onClick={()=>ask("Find the PFZ reference near " + location)}>🛰 PFZ</button>
          <button onClick={()=>ask("Check marine sea conditions near " + location)}>🌊 Sea State</button>
        </div>
      </section>

      <section className="grid-3">
        <AgentCard title="Ocean Agent" icon="🌊" data={ocean} />
        <AgentCard title="Weather Agent" icon="🌤" data={weather} />
        <AgentCard title="Geo Agent" icon="🗺" data={geo} />
      </section>

      {result && <section className="panel decision">
        <div className="section-head"><h2>Decision & Evidence</h2><span>{result.orchestration || "workflow"}</span></div>
        <div className="metrics">
          <Metric label="Wind" value={weather.wind_speed_kmh} unit="km/h" />
          <Metric label="Wave" value={weather.wave_height_m} unit="m" />
          <Metric label="Rain" value={weather.rain_probability_pct} unit="%" />
          <Metric label="Forecast" value={weather.forecast_time || "Demo"} unit="" />
        </div>
        <div className="explanation">{result.explanation}</div>
        <div className="flow">{(result.trace || []).map((x,i)=><React.Fragment key={x.stage}><div><b>{i+1}. {x.stage}</b><small>{x.detail}</small></div>{i<5 && <i>→</i>}</React.Fragment>)}</div>
        <div className="two-col">
          <div><h3>Risk Factors</h3>{(result.risk.factors || []).map((f,i)=><div className="factor" key={i}><b>{f.effect}</b><span>{f.factor}: {JSON.stringify(f.value)}</span></div>)}</div>
          <div><h3>Provenance</h3><div className="provenance">
            <p><b>Ocean:</b> {ocean.source?.provider} · {ocean.source?.mode}</p>
            <p><b>Weather:</b> {weather.source?.provider} · {weather.source?.mode}</p>
            <p><b>Geo:</b> {geo.source?.provider} · {geo.source?.mode}</p>
            <p><b>PFZ geometry:</b> {ocean.geometry_mode || "unknown"}</p>
            <p><b>Cache:</b> {result.cache?.backend} / {result.cache?.hit ? "HIT" : "MISS"}</p>
            <p><b>Persistence:</b> {result.persistence || "disabled"}</p>
          </div></div>
        </div>
      </section>}

      <section className="panel">
        <div className="section-head"><h2>Marine Map</h2><span>Evidence visualization · not navigation</span></div>
        <Map location={location} pfz={pfz} risk={risk} />
      </section>

      <section className="panel">
        <div className="section-head"><h2>Marine Alert Watch</h2><button onClick={toggleWatch}>{watch ? "Stop Watch" : "Enable Watch"}</button></div>
        <p className="muted">{watch ? "Active: checking approximately every 60 seconds." : "Opt-in prototype monitoring."}</p>
        <div className="alerts">{alerts.map((a,i)=><div className={"alert " + a.type} key={i}><time>{a.time}</time>{a.text}</div>)}</div>
      </section>

      <section className="panel">
        <div className="section-head"><h2>System & Data Gateways</h2><span>{system?.orchestration || "loading"}</span></div>
        <div className="gateway-grid">
          <Gateway name="INCOIS PFZ" href="https://www.incois.gov.in/MarineFisheries/PfzWebGis" live={ocean.source?.mode==="live"} />
          <Gateway name="INCOIS Ocean State Forecast" href="https://www.incois.gov.in/oceanservices/osfforecast.jsp" />
          <Gateway name="IMD Marine" href="https://mausam.imd.gov.in/responsive/marine_forecast.php" live={system?.imd_configured} />
          <Gateway name="MOSDAC" href="https://mosdac.gov.in/" />
        </div>
        <div className="status-grid">
          <Status name="LangGraph" value={system?.orchestration || "configured"} />
          <Status name="Redis" value={system?.redis_configured ? "connected/configured" : "memory fallback"} />
          <Status name="PostgreSQL" value={system?.postgres_configured ? "configured" : "optional"} />
          <Status name="LLM" value={system?.llm_configured ? "configured" : "deterministic fallback"} />
        </div>
      </section>
    </main>

    <footer>ORCA prototype · Deterministic Risk Engine remains authoritative · Demo/fallback data must not be treated as navigation guidance.</footer>
  </div>;
}

function AgentCard({title,icon,data}) {
  return <div className="panel agent"><div className="agent-title"><span>{icon}</span><b>{title}</b><small>{data.data_mode || data.source?.mode || "unknown"}</small></div><p>{data.source?.provider || data.provider || "No provider"}</p><pre>{JSON.stringify({pfz:data.pfz,forecast_time:data.forecast_time,eez_status:data.eez_status}, null, 2)}</pre></div>;
}
function Metric({label,value,unit}) { return <div className="metric"><small>{label}</small><b>{value ?? "N/A"} {unit}</b></div>; }
function Gateway({name,href,live}) { return <a className="gateway" href={href} target="_blank" rel="noreferrer"><b>{name}</b><small>{live ? "Provider reachable/configured" : "Official gateway"}</small></a>; }
function Status({name,value}) { return <div className="status"><small>{name}</small><b>{String(value)}</b></div>; }

function Map({location,pfz,risk}) {
  const ref = useRef(null);
  useEffect(() => {
    const map = L.map(ref.current).setView(LOCATIONS[location], 8);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {attribution:"© OpenStreetMap contributors"}).addTo(map);
    L.marker(LOCATIONS[location]).addTo(map).bindPopup(location);
    if (pfz.latitude && pfz.longitude) {
      L.marker([pfz.latitude,pfz.longitude]).addTo(map).bindPopup(pfz.name || "PFZ reference");
      L.polyline([LOCATIONS[location],[pfz.latitude,pfz.longitude]], {dashArray:"8 8"}).addTo(map);
      map.fitBounds(L.latLngBounds([LOCATIONS[location],[pfz.latitude,pfz.longitude]]), {padding:[30,30]});
    }
    return () => map.remove();
  }, [location, pfz.latitude, pfz.longitude]);
  return <div className="map-wrap"><div className="map" ref={ref}></div><div className={"map-label " + risk.toLowerCase()}>{risk} · prototype evidence map</div></div>;
}

export default App;
