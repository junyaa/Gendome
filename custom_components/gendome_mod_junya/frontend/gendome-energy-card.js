const CARD_TAG = "gendome-mod-junya-card";
const EDITOR_TAG = "gendome-mod-junya-card-editor";
const CARD_VERSION = "2026-11-17.4";

const mdi = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${d}"/></svg>`;
const ICONS = {
  grid: "M8.5 21v-2H4v-3h4.5v-2H6V6h6v8h-1.5v2H15v3h-4.5v2h-2M8 8v4h2V8H8m6 2v2h2v-2h-2M4 2h16v2H4V2Z",
  home: "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8h5Z",
  battery: "M16 20H8V6h8m0-2h-2V2h-4v2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2Z",
  plug: "M16 7V3h-2v4h-4V3H8v4a2 2 0 0 0-2 2v5h3v7l4-7v-3h3V9a2 2 0 0 0-2-2Z",
  temp: "M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0m-3 6a2 2 0 0 1-1-3.73V5a1 1 0 0 1 2 0v10.27A2 2 0 0 1 12 19Z",
};

const fmt = (stateObj) => {
  if (!stateObj) return "—";
  const s = stateObj.state;
  if (s === "unavailable" || s === "unknown") return "—";
  if (stateObj.attributes?.device_class === "timestamp") {
    const d = new Date(s);
    if (!isNaN(d)) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  const u = stateObj.attributes?.unit_of_measurement || "";
  const n = Number(s);
  const val = Number.isFinite(n) && u !== "" ? String(Math.round(n * 10) / 10) : s;
  return u ? `${val} ${u}` : `${val}`;
};
const num = (stateObj) => { if (!stateObj) return null; const n = Number(stateObj.state); return Number.isFinite(n) ? n : null; };
const onOff = (stateObj) => stateObj?.state === "on";
const avail = (stateObj) => stateObj && !["unavailable", "unknown"].includes(stateObj.state);

function findByKey(hass, deviceId, key, domain) {
  if (!hass || !deviceId) return null;
  const entries = Object.values(hass.entities || {}).filter((e) => e.device_id === deviceId);
  const hit = entries.find((e) => (e.translation_key === key || (e.unique_id || "").endsWith(`_${key}`)) && (!domain || e.entity_id.startsWith(domain + ".")));
  return hit ? hass.states[hit.entity_id] : null;
}
function findDevice(hass, cfg) {
  if (cfg?.device_id) return cfg.device_id;
  for (const id of (cfg?.entity_ids || []).filter(Boolean)) {
    const d = hass?.entities?.[id]?.device_id;
    if (d) return d;
  }
  const ents = Object.values(hass?.entities || {}).filter((e) => e.platform === "gendome_mod_junya");
  if (ents.length) return ents[0].device_id;
  return null;
}

const SECTION_ALL = "all";
const SECTION_NAMES = ["all", "battery", "flow", "metrics", "status"];

class GendomeModJunyaCard extends HTMLElement {
  static getConfigElement() { return document.createElement(EDITOR_TAG); }
  static getStubConfig() { return { type: `custom:${CARD_TAG}`, title: "Energy Console", section: "all", entities: {} }; }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    const section = SECTION_NAMES.includes(config.section) ? config.section : SECTION_ALL;
    this._config = { title: "Energy Console", ...config, section, entities: config.entities || {} };
    this._rendered = false;
  }
  set hass(hass) { this._hass = hass; if (!this._rendered) this.render(); this.update(); }
  getCardSize() {
    const s = this._config?.section || SECTION_ALL;
    if (s === "battery") return 4;
    if (s === "metrics") return 3;
    if (s === "flow") return 3;
    if (s === "status") return 2;
    return 7;
  }

  render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card { overflow:hidden; border:1px solid color-mix(in srgb, var(--primary-text-color) 10%, transparent);
          background:
            radial-gradient(140% 100% at 100% -10%, rgba(14,165,233,.20), transparent 45%),
            radial-gradient(120% 90% at -10% 110%, rgba(34,197,94,.16), transparent 40%),
            linear-gradient(160deg, var(--card-background-color) 0%, color-mix(in srgb, var(--card-background-color) 86%, #071018) 100%);
        }
        .wrap { padding:16px; font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
        .hdr { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:14px; }
        .title-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
        .title { font-size:1.05rem; font-weight:700; letter-spacing:.02em; }
        .mod-badge { display:inline-flex; align-items:center; padding:2px 8px; border-radius:999px; font-size:.62rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#071018; background:linear-gradient(135deg,#22d3ee,#34d399); box-shadow:0 0 0 1px rgba(255,255,255,.12) inset; }
        .sub { font-size:.75rem; color:var(--secondary-text-color); margin-top:3px; min-height:1.1em; }
        .pill { display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:999px; font-size:.72rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase;
          background:color-mix(in srgb,var(--primary-text-color) 7%,transparent); border:1px solid color-mix(in srgb,var(--primary-text-color) 10%,transparent); }
        .pill.ok { color:#22c55e; background:rgba(34,197,94,.12); border-color:rgba(34,197,94,.25); }
        .pill.off { color:#94a3b8; }
        .sec + .sec { margin-top:12px; }
        .hero { display:grid; grid-template-columns: 136px 1fr; gap:14px; align-items:center; }
        .hero.solo { grid-template-columns: 1fr; justify-items:center; text-align:center; }
        @media (max-width: 440px){ .hero{ grid-template-columns:1fr; } .ring-wrap{justify-self:center;} }
        .ring-wrap { position:relative; width:136px; height:136px; }
        .ring { width:136px; height:136px; transform:rotate(-90deg); }
        .ring circle { fill:none; stroke-width:10; stroke-linecap:round; }
        .ring .bg { stroke: color-mix(in srgb, var(--primary-text-color) 10%, transparent); }
        .ring .fg { stroke: var(--accent,#22c55e); filter: drop-shadow(0 0 7px color-mix(in srgb, var(--accent,#22c55e) 45%, transparent)); transition: stroke-dashoffset .6s ease, stroke .4s ease; }
        .ring-label { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .ring-val { font-size:1.75rem; font-weight:800; line-height:1; }
        .ring-cap { font-size:.68rem; color:var(--secondary-text-color); text-transform:uppercase; letter-spacing:.08em; margin-top:4px; }
        .metrics { display:grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap:8px; }
        .metric { padding:9px 11px; border-radius:14px; background:color-mix(in srgb,var(--primary-text-color) 5%,transparent); border:1px solid color-mix(in srgb,var(--primary-text-color) 8%,transparent); }
        .m-label { display:flex; align-items:center; gap:6px; font-size:.68rem; color:var(--secondary-text-color); text-transform:uppercase; letter-spacing:.06em; }
        .m-label svg { width:14px; height:14px; fill:currentColor; }
        .m-val { font-size:1.08rem; font-weight:700; margin-top:3px; font-variant-numeric: tabular-nums; }
        .flow { display:grid; grid-template-columns:1fr auto 1fr auto 1fr; gap:6px; align-items:center; }
        .node { text-align:center; padding:9px 6px; border-radius:14px; background:color-mix(in srgb,var(--primary-text-color) 5%,transparent); border:1px solid color-mix(in srgb,var(--primary-text-color) 8%,transparent); }
        .node .ico { width:22px; height:22px; margin:0 auto 4px; color:var(--secondary-text-color); }
        .node .ico svg { width:22px; height:22px; fill:currentColor; }
        .node.active.in .ico { color:#38bdf8; filter: drop-shadow(0 0 6px rgba(56,189,248,.35)); }
        .node.active.mid .ico { color:#22c55e; filter: drop-shadow(0 0 6px rgba(34,197,94,.35)); }
        .node.active.out .ico { color:#f59e0b; filter: drop-shadow(0 0 6px rgba(245,158,11,.35)); }
        .node.charging .ico svg, .node.flow-in .ico svg { animation: ico-pulse 1.6s ease-in-out infinite; }
        .node.discharging .ico svg, .node.flow-out .ico svg { animation: ico-pulse 1.6s ease-in-out infinite; }
        .node.charging.mid .ico svg { animation: battery-charge 1.8s ease-in-out infinite; }
        .node.discharging.mid .ico svg { animation: ico-pulse 1.8s ease-in-out infinite; }
        .node .nlab { font-size:.64rem; color:var(--secondary-text-color); text-transform:uppercase; letter-spacing:.06em; }
        .node .nval { font-size:.9rem; font-weight:700; margin-top:2px; font-variant-numeric: tabular-nums; }
        .arrow { color:var(--secondary-text-color); opacity:.35; font-size:1.1rem; text-align:center; transition: color .3s ease, opacity .3s ease; }
        .arrow.flow { color:#38bdf8; opacity:1; animation: arrow-flow 1.1s linear infinite; text-shadow:0 0 8px rgba(56,189,248,.45); }
        .arrow.flow.out { color:#f59e0b; text-shadow:0 0 8px rgba(245,158,11,.45); }
        .ring.charging .fg { filter: drop-shadow(0 0 10px color-mix(in srgb, var(--accent,#22c55e) 60%, transparent)); }
        .chip.on .dot { background:#22c55e; box-shadow:0 0 0 3px rgba(34,197,94,.18); animation: dot-pulse 2s ease-out infinite; }
        .chip.warn.on .dot { background:#f59e0b; box-shadow:0 0 0 3px rgba(245,158,11,.18); animation: dot-pulse 2s ease-out infinite; }
        @keyframes ico-pulse { 0%,100%{ transform:scale(1); opacity:1; } 50%{ transform:scale(1.12); opacity:.85; } }
        @keyframes battery-charge { 0%,100%{ transform:translateY(0) scale(1); filter:drop-shadow(0 0 0 rgba(34,197,94,0)); } 50%{ transform:translateY(-2px) scale(1.08); filter:drop-shadow(0 0 6px rgba(34,197,94,.55)); } }
        @keyframes arrow-flow { 0%{ transform:translateX(-3px); opacity:.35; } 50%{ transform:translateX(3px); opacity:1; } 100%{ transform:translateX(-3px); opacity:.35; } }
        @keyframes dot-pulse { 0%{ box-shadow:0 0 0 0 rgba(34,197,94,.45); } 70%{ box-shadow:0 0 0 6px rgba(34,197,94,0); } 100%{ box-shadow:0 0 0 0 rgba(34,197,94,0); } }
        @media (prefers-reduced-motion: reduce) {
          .node .ico svg, .arrow, .chip.on .dot, .ring .fg { animation:none !important; transition:none !important; }
        }
        .empty { padding:18px 8px; text-align:center; color:var(--secondary-text-color); font-size:.88rem; line-height:1.4; }
        .foot { margin-top:10px; font-size:.62rem; color:var(--secondary-text-color); opacity:.8; text-align:right; letter-spacing:.04em; }
      </style>
      <ha-card>
        <div class="wrap">
          <div class="hdr"><div><div class="title-row"><div class="title"></div><span class="mod-badge">Mod Junya</span></div><div class="sub"></div></div><div class="status"></div></div>
          <div class="body"></div>
          <div class="foot">gendome_mod_junya · custom card</div>
        </div>
      </ha-card>`;
    this._rendered = true;
  }

  _collect() {
    const h = this._hass, c = this._config || {}, E = c.entities || {};
    const deviceId = findDevice(h, c);
    const get = (key, domain) => (E[key] && h.states[E[key]]) || findByKey(h, deviceId, key, domain) || null;

    const soc = get("battery_soc", "sensor");
    const inP = get("ac_input_power", "sensor") || get("input_total_power", "sensor");
    const outP = get("ac_output_power", "sensor") || get("output_total_power", "sensor");
    const dcP = get("dc_output_power", "sensor");
    const rem = get("remaining_time", "sensor");
    const temp = get("battery_temperature", "sensor") || get("device_temperature", "sensor");
    const last = get("last_update", "sensor");
    const online = get("online", "binary_sensor");
    const charging = get("charging", "binary_sensor");
    const dischg = get("discharging", "binary_sensor");
    const grid = get("grid_connected", "binary_sensor") || get("ac_input_enabled", "binary_sensor");
    const bypass = get("bypass_enabled", "binary_sensor");
    const ups = get("ups_mode", "binary_sensor");
    const acOut = get("ac_output_enabled", "binary_sensor") || get("ac_output", "switch");
    const dcOut = get("dc_output_enabled", "binary_sensor") || get("dc_output", "switch");

    const socV = num(soc), pct = socV == null ? 0 : Math.max(0, Math.min(100, socV));
    const r = 54, circ = 2 * Math.PI * r, off = circ * (1 - pct / 100);
    const accent = pct <= 15 ? "#ef4444" : pct <= 30 ? "#f59e0b" : "#22c55e";
    const onlineOk = avail(online) ? onOff(online) : (avail(soc) || avail(inP) || avail(outP));
    const inAct = (num(inP) || 0) > 5 || onOff(grid);
    const outAct = (num(outP) || 0) > 0 || onOff(acOut) || onOff(dcOut);
    const chargingOn = onOff(charging);
    const dischargingOn = onOff(dischg);
    const flowIn = chargingOn || (inAct && (num(inP) || 0) > 5);
    const flowOut = dischargingOn || (outAct && (num(outP) || 0) > 0);
    const chips = [
      { l: "Grid", on: onOff(grid), v: avail(grid) },
      { l: "Charging", on: onOff(charging), v: avail(charging) },
      { l: "Discharging", on: onOff(dischg), v: avail(dischg), warn: true },
      { l: "Bypass", on: onOff(bypass), v: avail(bypass) },
      { l: "UPS", on: onOff(ups), v: avail(ups) },
      { l: "AC out", on: onOff(acOut), v: avail(acOut) },
      { l: "DC out", on: onOff(dcOut), v: avail(dcOut) },
    ].filter((x) => x.v);
    const hasData = !!deviceId || avail(soc) || avail(inP) || avail(outP);
    return { deviceId, socV, pct, r, circ, off, accent, onlineOk, inP, outP, dcP, temp, rem, last, charging, dischg, soc, inAct, outAct, flowIn, flowOut, chargingOn, dischargingOn, chips, hasData };
  }

  update() {
    if (!this._rendered || !this._hass) return;
    const c = this._config || {};
    const d = this._collect();

    this.shadowRoot.querySelector(".title").textContent = c.title || "Energy Console";
    this.shadowRoot.querySelector(".status").innerHTML = `<span class="pill ${d.onlineOk ? "ok" : "off"}">${d.onlineOk ? "Online" : "Offline"}</span>`;
    const parts = [];
    if (avail(d.rem)) parts.push(`Remaining ${fmt(d.rem)}`);
    if (avail(d.last)) parts.push(`Updated ${fmt(d.last)}`);
    this.shadowRoot.querySelector(".sub").textContent = parts.join(" · ") || (d.deviceId ? "Live power and battery status" : "Configure device to show data");

    if (!d.hasData) {
      this.shadowRoot.querySelector(".body").innerHTML = `<div class="empty">Edit this card and set a <b>Device</b> (recommended) or entity overrides for <b>Gendome (Mod Junya)</b>.</div>`;
      return;
    }

    const section = c.section || SECTION_ALL;
    const show = (name) => section === SECTION_ALL || section === name;
    const solo = section !== SECTION_ALL;
    let html = "";

    if (show("battery")) {
      const ring = `<div class="ring-wrap" style="--accent:${d.accent}">
          <svg class="ring${d.chargingOn ? " charging" : ""}" viewBox="0 0 120 120" role="img" aria-label="Battery ${d.pct}%">
            <circle class="bg" cx="60" cy="60" r="${d.r}"></circle>
            <circle class="fg" cx="60" cy="60" r="${d.r}" stroke-dasharray="${d.circ.toFixed(2)}" stroke-dashoffset="${d.off.toFixed(2)}"></circle>
          </svg>
          <div class="ring-label"><div class="ring-val">${d.socV==null?"—":Math.round(d.pct)+"%"}</div><div class="ring-cap">Battery${d.chargingOn ? " · Charging" : ""}</div></div>
        </div>`;
      if (section === "battery") {
        html += `<div class="sec"><div class="hero solo">${ring}</div></div>`;
      } else {
        html += `<div class="sec"><div class="hero">${ring}<div class="metrics">
            <div class="metric"><div class="m-label">${mdi(ICONS.grid)} Grid / In</div><div class="m-val">${fmt(d.inP)}</div></div>
            <div class="metric"><div class="m-label">${mdi(ICONS.home)} Output</div><div class="m-val">${fmt(d.outP)}</div></div>
            <div class="metric"><div class="m-label">${mdi(ICONS.plug)} DC out</div><div class="m-val">${fmt(d.dcP)}</div></div>
            <div class="metric"><div class="m-label">${mdi(ICONS.temp)} Temp</div><div class="m-val">${fmt(d.temp)}</div></div>
          </div></div></div>`;
      }
    }

    if (show("metrics") && section !== SECTION_ALL) {
      html += `<div class="sec"><div class="metrics">
        <div class="metric"><div class="m-label">${mdi(ICONS.grid)} Grid / In</div><div class="m-val">${fmt(d.inP)}</div></div>
        <div class="metric"><div class="m-label">${mdi(ICONS.home)} Output</div><div class="m-val">${fmt(d.outP)}</div></div>
        <div class="metric"><div class="m-label">${mdi(ICONS.plug)} DC out</div><div class="m-val">${fmt(d.dcP)}</div></div>
        <div class="metric"><div class="m-label">${mdi(ICONS.temp)} Temp</div><div class="m-val">${fmt(d.temp)}</div></div>
      </div></div>`;
    }

    if (show("flow")) {
      const inCls = ["node", d.inAct ? "active in" : "", d.flowIn ? "flow-in" : "", d.chargingOn ? "charging" : ""].filter(Boolean).join(" ");
      const midCls = ["node", (onOff(d.charging) || onOff(d.dischg) || avail(d.soc)) ? "active mid" : "", d.chargingOn ? "charging" : "", d.dischargingOn ? "discharging" : ""].filter(Boolean).join(" ");
      const outCls = ["node", "out", d.outAct ? "active out" : "", d.flowOut ? "flow-out" : "", d.dischargingOn ? "discharging" : ""].filter(Boolean).join(" ");
      const arrIn = `arrow${d.flowIn ? " flow" : ""}`;
      const arrOut = `arrow${d.flowOut ? " flow out" : ""}`;
      html += `<div class="sec"><div class="flow${d.chargingOn ? " charging" : ""}${d.dischargingOn ? " discharging" : ""}">
        <div class="${inCls}"><div class="ico">${mdi(ICONS.grid)}</div><div class="nlab">Input</div><div class="nval">${fmt(d.inP)}</div></div>
        <div class="${arrIn}">→</div>
        <div class="${midCls}"><div class="ico">${mdi(ICONS.battery)}</div><div class="nlab">Station</div><div class="nval">${d.socV==null?"—":Math.round(d.pct)+"%"}</div></div>
        <div class="${arrOut}">→</div>
        <div class="${outCls}"><div class="ico">${mdi(ICONS.home)}</div><div class="nlab">Load</div><div class="nval">${fmt(d.outP)}</div></div>
      </div></div>`;
    }

    if (show("status")) {
      html += d.chips.length ? `<div class="sec"><div class="chips">${d.chips.map(c=>`<span class="chip ${c.on?"on":""} ${c.warn&&c.on?"warn":""}"><span class="dot"></span>${c.l}</span>`).join("")}</div></div>` : (solo ? `<div class="empty">No status entities available.</div>` : "");
    }

    this.shadowRoot.querySelector(".body").innerHTML = html || `<div class="empty">No data for selected section.</div>`;
  }
}

class GendomeModJunyaCardEditor extends HTMLElement {
  setConfig(config){ this._config = { title:"Energy Console", section:"all", ...config, entities: config.entities||{} }; this.render(); }
  set hass(hass){ this._hass = hass; }
  render(){
    if (this._rendered) return;
    this.attachShadow({mode:"open"});
    this.shadowRoot.innerHTML = `
      <style>
        .f{padding:8px 0 0; display:grid; gap:10px; font-family: var(--paper-font-body1_-_font-family, sans-serif);}
        label{font-size:.84rem;color:var(--secondary-text-color);display:block;margin-bottom:4px;}
        input,select{width:100%;box-sizing:border-box;padding:8px 10px;border-radius:8px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);}
        .hint{font-size:.76rem;color:var(--secondary-text-color);line-height:1.4}
      </style>
      <div class="f">
        <div><label>Title</label><input id="title" /></div>
        <div><label>Section</label>
          <select id="section">
            <option value="all">All (combined)</option>
            <option value="battery">Battery</option>
            <option value="metrics">Metrics</option>
            <option value="flow">Power flow</option>
            <option value="status">Status chips</option>
          </select>
        </div>
        <div><label>Device ID (recommended)</label><input id="device_id" placeholder="Auto-detects entities for the device" /></div>
        <div class="hint">Use one card per section and the same Device ID to split the view across dashboard sections.</div>
        <div><label>Battery SOC entity</label><input id="battery_soc" /></div>
        <div><label>Input power entity</label><input id="ac_input_power" /></div>
        <div><label>Output power entity</label><input id="ac_output_power" /></div>
        <div><label>Online entity</label><input id="online" /></div>
      </div>`;
    const q = (id)=>this.shadowRoot.getElementById(id);
    const emit = ()=>{
      const entities = { ...(this._config.entities||{}) };
      ["battery_soc","ac_input_power","ac_output_power","online"].forEach(k=>{ const v=q(k).value.trim(); if(v) entities[k]=v; else delete entities[k]; });
      const cfg = { ...this._config, type:`custom:${CARD_TAG}`, title:q("title").value || "Energy Console", section:q("section").value || "all", device_id:q("device_id").value.trim()||undefined, entities };
      if(!cfg.device_id) delete cfg.device_id;
      this._config = cfg;
      this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:cfg}, bubbles:true, composed:true}));
    };
    ["title","device_id","section","battery_soc","ac_input_power","ac_output_power","online"].forEach(id=>q(id).addEventListener("change", emit));
    const cfg = this._config||{}, e = cfg.entities||{};
    q("title").value = cfg.title || "Energy Console";
    q("section").value = SECTION_NAMES.includes(cfg.section) ? cfg.section : "all";
    q("device_id").value = cfg.device_id || "";
    q("battery_soc").value = e.battery_soc||"";
    q("ac_input_power").value = e.ac_input_power||"";
    q("ac_output_power").value = e.ac_output_power||"";
    q("online").value = e.online||"";
    this._rendered = true;
  }
}

if (!customElements.get(CARD_TAG)) customElements.define(CARD_TAG, GendomeModJunyaCard);
if (!customElements.get(EDITOR_TAG)) customElements.define(EDITOR_TAG, GendomeModJunyaCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Gendome (Mod Junya) Energy Console",
    description: "Visual power-flow, battery ring, and status card for Gendome (Mod Junya). Supports sections (battery, metrics, flow, status).",
    preview: true,
  });
}