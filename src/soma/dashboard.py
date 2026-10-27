"""Build the operator-facing dashboard as one self-contained HTML file.

Self-contained is a requirement, not a convenience. The people who most need
this — a state environment agency, a public prosecutor's office in a mining
town, a municipal council — often cannot install anything, cannot reach the
open internet from the machine that holds the case file, and need to put the
thing on a USB stick and take it into a hearing. A single HTML file with no
external requests works in all of those places.

Charts are drawn client-side as SVG from embedded JSON so that every value is
hoverable and every chart has a table view; the satellite imagery is embedded
as data URIs.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Dict

from PIL import Image

MAX_IMAGE_WIDTH = 560


def _img_data_uri(path: Path, max_width: int = MAX_IMAGE_WIDTH) -> str:
    img = Image.open(path)
    if img.width > max_width:
        h = int(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=86, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def build(out_dir: str | Path, dest: str | Path) -> Path:
    out_dir = Path(out_dir)
    bundle = json.loads((out_dir / "portfolio.json").read_text(encoding="utf-8"))

    images: Dict[str, Dict[str, str]] = {}
    for site in bundle["sites"]:
        figs = site.get("figures", {})
        entry: Dict[str, str] = {}
        for key in ("image_overlay", "image_first", "image_latest",
                    "chart_deformation", "chart_deformation_dark"):
            name = figs.get(key)
            if name and (out_dir / name).exists():
                entry[key] = _img_data_uri(out_dir / name)
        images[site["site_id"]] = entry

    payload = json.dumps({"bundle": bundle, "images": images},
                         ensure_ascii=False, separators=(",", ":"))
    html = _TEMPLATE.replace("__PAYLOAD__", payload)
    dest = Path(dest)
    dest.write_text(html, encoding="utf-8")
    return dest


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Observatório SOMA — public mining oversight (simulated data)</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="assets/soma.css?v=20261027c">
<script src="assets/soma.js?v=20261027c"></script>
<style>
  :root{
    color-scheme: light;
    --surface-1:#fcfcfb; --page:#f9f9f7;
    --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,.10);
    --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a;
    --good:#0ca30c; --warning:#fab219; --serious:#ec835a; --critical:#d03b3b;
    --shadow:0 1px 2px rgba(11,11,11,.05), 0 6px 18px rgba(11,11,11,.05);
  }
  html[data-theme="dark"]{
    color-scheme: dark;
    --surface-1:#1a1a19; --page:#0d0d0d;
    --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
    --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 6px 18px rgba(0,0,0,.35);
  }
  /* Observatório SOMA identity (EU funding guidelines palette) */
  html[data-theme="light"]{--page:#f1f2f2;--surface-1:#ffffff;--text-primary:#383837;
    --text-secondary:#545453;--series-1:#1765b1;--heading:#0d3d92}
  html[data-theme="dark"]{--page:#10151c;--surface-1:#161c25;--heading:#b7cdf0}
  *{box-sizing:border-box}
  body{
    margin:0; background:var(--page); color:var(--text-primary);
    font:15px/1.55 "Noto Sans",Arial,"Helvetica Neue",sans-serif;
  }
  h1,.card h2{color:var(--heading)}
  h1{font-weight:600}
  .card h2{font-weight:600}
  .wrap{max-width:1180px;margin:0 auto;padding:28px 20px 80px}
  header.top{display:flex;gap:18px;align-items:flex-start;justify-content:space-between;
    flex-wrap:wrap;margin-bottom:6px}
  h1{font-size:23px;margin:0 0 4px;letter-spacing:-.01em}
  .sub{color:var(--text-secondary);font-size:14px;max-width:62ch;margin:0}
  .banner{margin:18px 0 22px;padding:11px 14px;border-radius:10px;
    background:color-mix(in srgb, var(--warning) 16%, var(--surface-1));
    border:1px solid color-mix(in srgb, var(--warning) 45%, transparent);
    font-size:13.5px;color:var(--text-primary)}
  .banner strong{font-weight:650}
  button,select{font:inherit;color:inherit}
  .ghost{background:var(--surface-1);border:1px solid var(--border);border-radius:8px;
    padding:6px 11px;cursor:pointer}
  .ghost:hover{background:color-mix(in srgb,var(--text-primary) 5%,var(--surface-1))}
  .filters{display:flex;gap:10px;align-items:center;flex-wrap:wrap;
    padding:12px 14px;background:var(--surface-1);border:1px solid var(--border);
    border-radius:12px;margin-bottom:20px;box-shadow:var(--shadow)}
  .filters label{font-size:12.5px;color:var(--text-muted);margin-right:2px}
  .filters select{background:transparent;border:1px solid var(--border);
    border-radius:7px;padding:5px 8px}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:14px;margin-bottom:22px}
  .tile{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;
    padding:14px 16px;box-shadow:var(--shadow)}
  .tile .k{font-size:12.5px;color:var(--text-muted);margin-bottom:6px}
  .tile .v{font-size:29px;line-height:1.1;letter-spacing:-.02em}
  .tile .u{font-size:13px;color:var(--text-secondary);margin-left:3px}
  .tile .n{font-size:12.5px;color:var(--text-secondary);margin-top:6px}
  .card{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;
    padding:18px;margin-bottom:18px;box-shadow:var(--shadow)}
  .card h2{font-size:16px;margin:0 0 4px}
  .card h3{font-size:14px;margin:18px 0 6px;color:var(--text-secondary);
    font-weight:600}
  .card p.note{color:var(--text-secondary);font-size:13.5px;margin:2px 0 12px}
  table{border-collapse:collapse;width:100%;font-size:13.5px}
  .tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--grid);
    vertical-align:top}
  th{color:var(--text-muted);font-weight:600;font-size:12.5px;
    text-transform:uppercase;letter-spacing:.03em}
  tbody tr.q{cursor:pointer}
  tbody tr.q:hover{background:color-mix(in srgb,var(--text-primary) 4%,transparent)}
  tbody tr.q[aria-selected="true"]{background:color-mix(in srgb,var(--series-1) 12%,transparent)}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  .pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;
    padding:2px 9px;border-radius:999px;border:1px solid var(--border);
    white-space:nowrap}
  .dot{width:8px;height:8px;border-radius:50%;flex:none}
  .sev-critical .dot{background:var(--critical)} .sev-high .dot{background:var(--serious)}
  .sev-medium .dot{background:var(--warning)} .sev-low .dot{background:var(--good)}
  .grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}
  @media(max-width:880px){.grid2{grid-template-columns:1fr}}
  figure{margin:0}
  figure img{width:100%;border-radius:10px;border:1px solid var(--border);display:block}
  figcaption{font-size:12.5px;color:var(--text-secondary);margin-top:8px}
  .chartbox{position:relative}
  .chart-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
    margin-bottom:2px}
  .chart-head .t{font-size:14px}
  .legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;
    color:var(--text-secondary);margin:6px 0 2px}
  .legend i{display:inline-block;width:14px;height:2px;border-radius:1px;
    margin-right:6px;vertical-align:middle}
  .legend i.ring{width:9px;height:9px;border-radius:50%;background:transparent;
    border:1.5px solid var(--text-muted)}
  svg{display:block;width:100%;height:auto;overflow:visible}
  .tip{position:absolute;pointer-events:none;opacity:0;transition:opacity .08s;
    background:var(--surface-1);border:1px solid var(--border);border-radius:8px;
    padding:7px 10px;font-size:12.5px;box-shadow:var(--shadow);z-index:5;
    white-space:nowrap}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13.5px}
  .kv dt{color:var(--text-muted)}
  .kv dd{margin:0;font-variant-numeric:tabular-nums;word-break:break-all}
  .timeline{list-style:none;margin:0;padding:0;font-size:13.5px}
  .timeline li{padding:8px 0 8px 18px;border-left:2px solid var(--grid);
    margin-left:4px;position:relative}
  .timeline li::before{content:"";position:absolute;left:-5px;top:14px;width:8px;
    height:8px;border-radius:50%;background:var(--series-1)}
  .timeline .when{color:var(--text-muted);font-size:12px}
  ul.plain{margin:6px 0;padding-left:18px;font-size:13.5px;color:var(--text-secondary)}
  ul.plain li{margin:3px 0}
  .muted{color:var(--text-secondary)}
  code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
  .hide{display:none}
  footer{color:var(--text-secondary);font-size:13px;margin-top:26px;
    border-top:1px solid var(--grid);padding-top:16px}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div>
    <h1>Observatório SOMA — mining oversight from public data</h1>
    <p class="sub">An open mirror of the mining operator's software stack, built for
    the public sector. Every figure below is derived from freely licensed satellite
    imagery and public registry data, and every one of them carries the manifest
    needed to reproduce it.</p>
  </div>
  <button class="ghost" id="theme">Dark mode</button>
</header>

<div class="banner" id="banner"></div>

<div class="filters">
  <label for="fsev">Severity</label>
  <select id="fsev">
    <option value="all">All</option><option value="critical">Critical</option>
    <option value="high">High</option><option value="medium">Medium</option>
    <option value="low">Low</option>
  </select>
  <label for="fstate">Case state</label>
  <select id="fstate"><option value="all">All</option></select>
  <label for="frange">Period</label>
  <select id="frange">
    <option value="all">Full record</option>
    <option value="24">Last 24 months</option>
    <option value="12">Last 12 months</option>
    <option value="6">Last 6 months</option>
  </select>
  <span class="muted" id="filterNote" style="font-size:12.5px"></span>
</div>

<div class="tiles" id="tiles"></div>

<div class="card">
  <h2>Case queue</h2>
  <p class="note">Ranked by what is at stake, not by hectares. A structure whose crest
  is accelerating outranks everything else on the list.</p>
  <div class="tscroll"><table><thead><tr>
    <th>Site</th><th>Title of record</th><th>Severity</th><th>State</th>
    <th class="num">Disturbed</th><th class="num">Outside title</th>
    <th class="num">Current rate</th>
  </tr></thead><tbody id="queue"></tbody></table></div>
</div>

<div id="detail"></div>

<footer>
  <strong>Method.</strong> Monthly median composites of Sentinel-2 L2A surface
  reflectance; disturbed surface delineated by a published spectral rule with a
  0.5 ha minimum mapping unit; boundary attribution against the mining cadastre with
  a ±25 m tolerance applied in the title holder's favour; ground movement from
  Sentinel-1 interferometry. <br>
  <strong>Sources.</strong> Copernicus Sentinel data (free, full and open);
  national mining cadastre; protected-area register; royalty declarations.<br>
  <strong>Reproducibility.</strong> Every figure carries a sealed manifest listing
  its inputs, algorithm versions, parameters and hashes. The manifests are chained,
  so removal or alteration of a past finding is detectable.
</footer>
</div>

<div class="tip" id="tip"></div>

<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const SITES = DATA.bundle.sites, IMAGES = DATA.images;
const fmt = (n,d=1)=> (n==null||isNaN(n)) ? '—' : Number(n).toLocaleString(undefined,
  {minimumFractionDigits:d,maximumFractionDigits:d});
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const SEV_ORDER = {critical:0,high:1,medium:2,low:3};
const NAV = window.SOMA || null;  // shared nav (assets/soma.js); absent when opened standalone
const known = id => SITES.some(s=>s.site_id===id);
let selected = NAV && known(NAV.site()) ? NAV.site() : SITES[0].site_id;

document.getElementById('banner').innerHTML =
  '<strong>Simulated data.</strong> This dashboard is driven by a deterministic '+
  'simulator, not by real imagery of real sites. Every company, title number and '+
  'structure below is invented. The software refuses to issue an administrative '+
  'notice or a judicial dossier from simulated evidence — that guard is a test in '+
  'the suite, not a promise. Generated ' + esc(DATA.bundle.generated_utc) + '.';

// state filter options
const states = [...new Set(SITES.map(s=>s.state))].sort();
const fstate = document.getElementById('fstate');
states.forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;fstate.appendChild(o);});

function monthsBack(){const v=document.getElementById('frange').value;return v==='all'?null:+v;}
function clipSeries(site){
  const s = site.series, m = monthsBack();
  if(!m || !s.dates.length) return s;
  const last = new Date(s.dates[s.dates.length-1]);
  const cut = new Date(last); cut.setMonth(cut.getMonth()-m);
  const keep = s.dates.map((d,i)=>[d,i]).filter(([d])=> new Date(d)>=cut).map(([,i])=>i);
  return {
    dates: keep.map(i=>s.dates[i]),
    disturbed_ha: keep.map(i=>s.disturbed_ha[i]),
    outside_ha: s.outside_ha.length? keep.map(i=>s.outside_ha[i]) : [],
    degraded: s.degraded.filter(([d])=> new Date(d)>=cut),
    pond_ha: s.pond_ha.filter(([d])=> new Date(d)>=cut)
  };
}
function visible(){
  const sev=document.getElementById('fsev').value, st=fstate.value;
  return SITES.filter(s=>(sev==='all'||s.severity===sev)&&(st==='all'||s.state===st));
}

/* ---------- tiles ---------- */
function renderTiles(){
  const v = visible();
  const outside = v.reduce((a,s)=>a+(s.verdict.outside_title_ha||0),0);
  const restricted = v.reduce((a,s)=>a+(s.verdict.restricted_overlaps||[])
      .reduce((b,o)=>b+o.overlap_ha,0),0);
  const flagged = v.filter(s=>s.deformation && (s.deformation.detail.flags||[]).length).length;
  const cleared = v.filter(s=>s.state==='closed'||s.state==='dismissed').length;
  const tiles=[
    ['Sites under observation', v.length, '', 'continuous, at no marginal data cost'],
    ['Disturbance outside title', fmt(outside), 'ha', 'after a ±25 m tolerance in the holder’s favour'],
    ['Inside protected areas', fmt(restricted), 'ha', 'conservation units and equivalent'],
    ['Structures flagged', flagged, '', 'crest movement warranting an engineering visit'],
    ['Cases cleared', cleared, '', 'raised, examined, and closed without action'],
  ];
  document.getElementById('tiles').innerHTML = tiles.map(([k,val,u,n])=>
    `<div class="tile"><div class="k">${esc(k)}</div>
     <div class="v">${esc(val)}<span class="u">${esc(u)}</span></div>
     <div class="n">${esc(n)}</div></div>`).join('');
  document.getElementById('filterNote').textContent =
    v.length===SITES.length ? '' : `showing ${v.length} of ${SITES.length} sites`;
}

/* ---------- queue ---------- */
function renderQueue(){
  const v = visible().slice().sort((a,b)=>SEV_ORDER[a.severity]-SEV_ORDER[b.severity]);
  document.getElementById('queue').innerHTML = v.map(s=>`
    <tr class="q" data-id="${esc(s.site_id)}" aria-selected="${s.site_id===selected}" tabindex="0">
      <td><strong>${esc(s.site_id)}</strong><div class="muted" style="font-size:12.5px">${esc(s.holder)}</div></td>
      <td><code>${esc(s.title_id)}</code><div class="muted" style="font-size:12.5px">${esc(s.title_status)}</div></td>
      <td><span class="pill sev-${esc(s.severity)}"><span class="dot"></span>${esc(s.severity)}</span></td>
      <td>${esc(s.state)}</td>
      <td class="num">${fmt(s.verdict.total_disturbed_ha)} ha</td>
      <td class="num">${fmt(s.verdict.outside_title_ha)} ha</td>
      <td class="num">${fmt(s.trend.current_rate_per_month,2)} ha/mo</td>
    </tr>`).join('') || '<tr><td colspan="7" class="muted">No sites match these filters.</td></tr>';
  document.querySelectorAll('tr.q').forEach(tr=>{
    const pick=()=>{selected=tr.dataset.id;if(NAV)NAV.setSite(selected);render();};
    tr.addEventListener('click',pick);
    tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}});
  });
}

/* ---------- charts ---------- */
const TIP = document.getElementById('tip');
function showTip(host,x,y,html){
  TIP.innerHTML=html; TIP.style.opacity=1;
  const r=host.getBoundingClientRect();
  TIP.style.left=(r.left+window.scrollX+x+14)+'px';
  TIP.style.top=(r.top+window.scrollY+y-10)+'px';
}
function hideTip(){TIP.style.opacity=0;}

function lineChart(host, cfg){
  const W=680,H=cfg.height||230,P={l:46,r:118,t:14,b:30};
  const all=cfg.series.flatMap(s=>s.values).concat(cfg.points?cfg.points.map(p=>p[1]):[]);
  const ymax=Math.max(1,...all)*1.12, ymin=0;
  const xs=cfg.dates.map(d=>+new Date(d))
    .concat((cfg.points||[]).map(p=>+new Date(p[0])));
  const x0=Math.min(...xs), x1=Math.max(...xs);
  const X=t=>P.l+(W-P.l-P.r)*((+new Date(t))-x0)/Math.max(x1-x0,1);
  const Y=v=>H-P.b-(H-P.t-P.b)*(v-ymin)/(ymax-ymin);
  const ticks=[0,.25,.5,.75,1].map(f=>ymin+f*(ymax-ymin));
  let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(cfg.title)}">`;
  ticks.forEach(t=>{svg+=`<line x1="${P.l}" x2="${W-P.r}" y1="${Y(t)}" y2="${Y(t)}"
    stroke="var(--grid)" stroke-width="1"/>
    <text x="${P.l-8}" y="${Y(t)+4}" text-anchor="end" font-size="11"
      fill="var(--text-muted)" style="font-variant-numeric:tabular-nums">${fmt(t,0)}</text>`;});
  // x labels: first, middle, last
  [0,Math.floor(cfg.dates.length/2),cfg.dates.length-1].forEach(i=>{
    if(i<0||i>=cfg.dates.length)return;
    const d=new Date(cfg.dates[i]);
    svg+=`<text x="${X(cfg.dates[i])}" y="${H-8}" text-anchor="middle" font-size="11"
      fill="var(--text-muted)">${d.toLocaleDateString(undefined,{month:'short',year:'numeric'})}</text>`;});
  if(cfg.marker){
    const mx=X(cfg.marker.date);
    if(mx>P.l&&mx<W-P.r){
      svg+=`<line x1="${mx}" x2="${mx}" y1="${P.t}" y2="${H-P.b}" stroke="var(--text-muted)" stroke-width="1"/>
      <text x="${mx+6}" y="${P.t+12}" font-size="11" fill="var(--text-secondary)">${esc(cfg.marker.label)}</text>`;}
  }
  (cfg.points||[]).forEach(([d,v])=>{
    svg+=`<circle cx="${X(d)}" cy="${Y(v)}" r="3.4" fill="none"
      stroke="var(--text-muted)" stroke-width="1.4"/>`;});
  cfg.series.forEach(s=>{
    if(!s.values.length)return;
    const pts=cfg.dates.map((d,i)=>`${X(d)},${Y(s.values[i])}`).join(' ');
    svg+=`<polyline points="${pts}" fill="none" stroke="${s.colour}" stroke-width="2"
      stroke-linejoin="round" stroke-linecap="round"/>`;
    const li=cfg.dates.length-1;
    svg+=`<text x="${X(cfg.dates[li])+10}" y="${Y(s.values[li])+4}" font-size="12"
      fill="var(--text-primary)">${fmt(s.values[li])} ${esc(cfg.unit)}</text>`;
  });
  svg+=`<line x1="${P.l}" x2="${W-P.r}" y1="${H-P.b}" y2="${H-P.b}" stroke="var(--axis)"/>`;
  svg+=`<rect id="hit" x="${P.l}" y="${P.t}" width="${W-P.l-P.r}" height="${H-P.t-P.b}" fill="transparent"/>`;
  svg+=`<line id="cross" x1="0" x2="0" y1="${P.t}" y2="${H-P.b}" stroke="var(--axis)"
    stroke-width="1" opacity="0"/></svg>`;
  host.innerHTML=svg;
  const el=host.querySelector('svg'), cross=host.querySelector('#cross');
  el.addEventListener('pointermove',ev=>{
    const r=el.getBoundingClientRect();
    const sx=(ev.clientX-r.left)*W/r.width;
    if(sx<P.l||sx>W-P.r){hideTip();cross.setAttribute('opacity',0);return;}
    let best=0,bd=Infinity;
    cfg.dates.forEach((d,i)=>{const dd=Math.abs(X(d)-sx);if(dd<bd){bd=dd;best=i;}});
    const px=X(cfg.dates[best]);
    cross.setAttribute('x1',px);cross.setAttribute('x2',px);cross.setAttribute('opacity',1);
    const rows=cfg.series.map(s=>`<div><span style="display:inline-block;width:9px;height:9px;
      border-radius:2px;background:${s.colour};margin-right:6px"></span>${esc(s.label)}:
      <strong>${fmt(s.values[best])} ${esc(cfg.unit)}</strong></div>`).join('');
    showTip(host, px*r.width/W, (ev.clientY-r.top),
      `<div class="muted" style="margin-bottom:3px">${new Date(cfg.dates[best])
        .toLocaleDateString(undefined,{month:'long',year:'numeric'})}</div>${rows}`);
  });
  el.addEventListener('pointerleave',()=>{hideTip();cross.setAttribute('opacity',0);});
}

function chartCard(id,title,note,legend,tableHtml){
  return `<div class="chartbox">
    <div class="chart-head"><div class="t">${esc(title)}</div>
      <button class="ghost" data-toggle="${id}-tbl" style="font-size:12px;padding:3px 9px">Table view</button></div>
    <div class="legend">${legend}</div>
    <div id="${id}"></div>
    <div id="${id}-tbl" class="hide" style="margin-top:10px;max-height:230px;overflow:auto">${tableHtml}</div>
    <p class="note" style="margin-top:8px">${note}</p></div>`;
}

/* ---------- detail ---------- */
function renderDetail(){
  const s = SITES.find(x=>x.site_id===selected) || visible()[0];
  if(!s){document.getElementById('detail').innerHTML='';return;}
  const ser = clipSeries(s), img = IMAGES[s.site_id]||{};
  const v = s.verdict, t = s.trend;

  const rows = ser.dates.map((d,i)=>`<tr><td>${esc(d)}</td>
    <td class="num">${fmt(ser.disturbed_ha[i])}</td>
    <td class="num">${ser.outside_ha.length?fmt(ser.outside_ha[i]):'—'}</td></tr>`).join('');
  const fpTable = `<table><thead><tr><th>Date</th><th class="num">Disturbed ha</th>
    <th class="num">Outside title ha</th></tr></thead><tbody>${rows}</tbody></table>`;
  const pondTable = `<table><thead><tr><th>Date</th><th class="num">Impounded water ha</th>
    </tr></thead><tbody>${ser.pond_ha.map(([d,x])=>`<tr><td>${esc(d)}</td>
    <td class="num">${fmt(x)}</td></tr>`).join('')}</tbody></table>`;

  const overlaps = (v.restricted_overlaps||[]).map(o=>
    `<li><strong>${fmt(o.overlap_ha)} ha</strong> inside ${esc(o.name)}
     (${esc(o.kind)}) — ${esc(o.legal_basis)}</li>`).join('');

  const recon = s.reconciliation ? `
    <h3>Declaration screening</h3>
    <p class="note">${esc(s.reconciliation.status)}</p>
    <dl class="kv">
      <dt>Declared</dt><dd>${s.reconciliation.declared_tonnes==null?'nothing for the period'
        :fmt(s.reconciliation.declared_tonnes,0)+' t'}</dd>
      <dt>Intensity</dt><dd>${s.reconciliation.intensity_t_per_ha_month==null?'—'
        :fmt(s.reconciliation.intensity_t_per_ha_month,1)+' t/ha/month'}</dd>
      <dt>Peer decile</dt><dd>${s.reconciliation.intensity_decile ?? '—'} of 10
        <span class="muted">(${esc(s.reconciliation.peer_basis||'')})</span></dd>
      <dt>Audit priority</dt><dd>${fmt(s.reconciliation.audit_priority_score,2)}</dd>
    </dl>
    <ul class="plain">${(s.reconciliation.reasons||[]).map(r=>`<li>${esc(r)}</li>`).join('')}</ul>`
    : '';

  const filings = (s.filing_notes||[]).length ? `<h3>Consistency between the operator's own filings</h3>
    <ul class="plain">${s.filing_notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul>` : '';

  const def = s.deformation ? `
    <h3>Tailings structure — ${esc(s.deformation.detail.structure||'')}</h3>
    <dl class="kv">
      <dt>Recent velocity</dt><dd>${fmt(s.deformation.detail.median_velocity_recent_mm_yr,1)} mm/yr</dd>
      <dt>Whole history</dt><dd>${fmt(s.deformation.detail.median_velocity_whole_history_mm_yr,1)} mm/yr</dd>
      <dt>Coherent points</dt><dd>${s.deformation.detail.points_used}</dd>
      <dt>Flags</dt><dd>${(s.deformation.detail.flags||[]).map(f=>
        `<span class="pill sev-${(s.deformation.detail.flags||[]).length?'high':'low'}">
         <span class="dot"></span>${esc(f)}</span>`).join(' ')||'none'}</dd>
    </dl>
    <p class="note">${esc(s.deformation.detail.caveat||'')}</p>
    ${img.chart_deformation?`<figure><img id="defimg" src="${
      document.documentElement.dataset.theme==='dark'&&img.chart_deformation_dark
        ? img.chart_deformation_dark : img.chart_deformation}" alt="Crest displacement">
      </figure>`:''}` : '';

  const vol = s.volume ? `
    <h3>Material moved</h3>
    <dl class="kv">
      <dt>Net excavated</dt><dd>${fmt(s.volume.detail.net_m3,0)} m³
        <span class="muted">(95% interval ${fmt(s.volume.detail.net_m3_interval_95[0],0)}
        – ${fmt(s.volume.detail.net_m3_interval_95[1],0)})</span></dd>
    </dl>
    <p class="note">${esc(s.volume.detail.caveat||'')}</p>` : '';

  const hist = (s.history||[]).map(h=>`<li><div>${esc(h.frm)} → <strong>${esc(h.to)}</strong>
    — ${esc(h.actor)}, ${esc(h.actor_role)}</div>
    ${h.note?`<div class="muted">${esc(h.note)}</div>`:''}
    <div class="when">${esc(h.at_utc)}</div></li>`).join('');

  const resp = s.response ? `
    <h3>Response of the notified party</h3>
    <dl class="kv">
      <dt>Received</dt><dd>${esc(s.response.received_utc)}</dd>
      <dt>From</dt><dd>${esc(s.response.submitted_by)}</dd>
      <dt>Channel</dt><dd>${esc(s.response.channel)}</dd>
      <dt>Documents</dt><dd>${(s.response.documents||[]).map(esc).join(', ')||'none'}</dd>
      <dt>Digest</dt><dd><code>${esc((s.response.digest||'').slice(0,32))}…</code></dd>
    </dl>
    <p>${esc(s.response.summary)}</p>`
    : `<h3>Response of the notified party</h3><p class="muted">None recorded.
       ${s.state==='notified'?'The response window is open; the case cannot advance until it closes.':''}</p>`;

  document.getElementById('detail').innerHTML = `
  <div class="card">
    <h2>${esc(s.site_id)} — ${esc(s.case_id)}
      <span class="pill sev-${esc(s.severity)}"><span class="dot"></span>${esc(s.severity)}</span></h2>
    <p class="note">${esc(s.narrative)}</p>
    ${NAV?NAV.xlinks(s.site_id):''}
    <div class="grid2">
      <figure>
        ${img.image_overlay?`<img src="${img.image_overlay}" alt="Attributed footprint over the latest composite">`:''}
        <figcaption>Latest fully observed composite with the disturbed surface
        attributed against the cadastre. Green: inside the titled polygon.
        Red: outside it. Amber: within the ±25 m boundary tolerance, and therefore
        not counted against the holder.</figcaption>
      </figure>
      <div>
        <h3>What was found</h3>
        <dl class="kv">
          <dt>Disturbed</dt><dd>${fmt(v.total_disturbed_ha)} ha</dd>
          <dt>Inside title</dt><dd>${fmt(v.inside_title_ha)} ha</dd>
          <dt>Outside title</dt><dd>${fmt(v.outside_title_ha)} ha</dd>
          <dt>Indeterminate</dt><dd>${fmt(v.indeterminate_boundary_ha)} ha
            <span class="muted">(within tolerance)</span></dd>
          <dt>Current rate</dt><dd>${fmt(t.current_rate_per_month,2)} ha/month</dd>
          <dt>Whole period</dt><dd>${fmt(t.slope_per_month,2)} ha/month
            <span class="muted">(68% of pairwise slopes ${fmt(t.slope_ci68[0],2)}–${fmt(t.slope_ci68[1],2)})</span></dd>
          ${t.breakpoint?`<dt>Rate change</dt><dd>${esc(t.breakpoint)}:
            ${fmt(t.slope_before_breakpoint,2)} → ${fmt(t.slope_after_breakpoint,2)} ha/month</dd>`:''}
          <dt>Observations</dt><dd>${t.observations_used} used,
            ${t.observations_excluded_cloud_limited} cloud-limited</dd>
        </dl>
        ${overlaps?`<h3>Overlaps with restricted areas</h3><ul class="plain">${overlaps}</ul>`:''}
        ${(v.notes||[]).length?`<h3>Registry notes</h3><ul class="plain">${
          v.notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul>`:''}
      </div>
    </div>

    <h3>Change over time</h3>
    ${chartCard('fp','Disturbed surface',
      'Only fully observed dates form the line. Dates where cloud hid part of the '+
      'assessment area are drawn as unconnected rings, because a measurement taken '+
      'through a gap in the cloud is a lower bound, not the same quantity.',
      `<span><i style="background:var(--series-1)"></i>Total disturbed</span>
       <span><i style="background:var(--series-2)"></i>Outside licensed polygon</span>
       <span><i class="ring"></i>Cloud-limited (lower bound)</span>`, fpTable)}

    ${ser.pond_ha.length?`<h3>Impounded water</h3>`+chartCard('pond','Impounded water inside the licensed area',
      'Pond extent is a freeboard proxy, not a substitute for the operator’s '+
      'instrumented crest survey.',
      `<span><i style="background:var(--series-1)"></i>Impounded water inside the licence</span>`, pondTable):''}

    ${def}${vol}${recon}${filings}

    <h3>Evidence</h3>
    <dl class="kv">
      <dt>Manifest</dt><dd><code>${esc(s.manifest.id)}</code></dd>
      <dt>Hash</dt><dd><code>${esc(s.manifest.hash)}</code></dd>
      <dt>Chains to</dt><dd><code>${esc(s.manifest.prev_hash)}</code></dd>
      <dt>Sealed</dt><dd>${esc(s.manifest.created_utc)}</dd>
      <dt>Inputs</dt><dd>${s.manifest.inputs} identified sources</dd>
      <dt>Algorithms</dt><dd>${s.manifest.algorithms.map(esc).join('<br>')}</dd>
    </dl>
    <h3>Stated limitations</h3>
    <ul class="plain">${s.manifest.limitations.map(l=>`<li>${esc(l)}</li>`).join('')}</ul>

    <h3>Procedure</h3>
    <ul class="timeline">${hist||'<li class="muted">No transitions recorded.</li>'}</ul>
    ${resp}

    <h3>What may be published today</h3>
    <p class="note">${s.public_card.publishable
      ? 'Publication state <strong>'+esc(s.publication)+'</strong>. '+esc(s.public_card.what_this_is_not)
      : esc(s.public_card.reason)}</p>
  </div>`;

  lineChart(document.getElementById('fp'), {
    title:'Disturbed surface', unit:'ha', dates:ser.dates,
    points:ser.degraded,
    marker: t.breakpoint && ser.dates.length && new Date(t.breakpoint)>=new Date(ser.dates[0])
      ? {date:t.breakpoint,label:'rate change'} : null,
    series:[{label:'Total disturbed',values:ser.disturbed_ha,colour:'var(--series-1)'}]
      .concat(ser.outside_ha.length?[{label:'Outside licensed polygon',
        values:ser.outside_ha,colour:'var(--series-2)'}]:[])
  });
  if(ser.pond_ha.length){
    lineChart(document.getElementById('pond'), {
      title:'Impounded water', unit:'ha', height:190,
      dates:ser.pond_ha.map(p=>p[0]),
      series:[{label:'Impounded water',values:ser.pond_ha.map(p=>p[1]),colour:'var(--series-1)'}]
    });
  }
  document.querySelectorAll('[data-toggle]').forEach(b=>b.addEventListener('click',()=>{
    const el=document.getElementById(b.dataset.toggle);
    el.classList.toggle('hide');
    b.textContent = el.classList.contains('hide')?'Table view':'Hide table';
  }));
}

function render(){renderTiles();renderQueue();renderDetail();}
['fsev','fstate','frange'].forEach(id=>
  document.getElementById(id).addEventListener('change',()=>{
    if(!visible().some(s=>s.site_id===selected) && visible().length){
      selected=visible()[0].site_id; if(NAV) NAV.setSite(selected);}
    render();}));
document.getElementById('theme').addEventListener('click',()=>{
  const root=document.documentElement;
  const dark = root.dataset.theme==='dark';
  root.dataset.theme = dark?'light':'dark';
  document.getElementById('theme').textContent = dark?'Dark mode':'Light mode';
  renderDetail();
});
render();
if(NAV){
  const reveal=(jump)=>{const c=document.querySelector('#detail .card');
    if(c){c.scrollIntoView({behavior:jump||matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});NAV.flash(c);}};
  NAV.onSite(id=>{if(known(id)){selected=id;render();reveal();}});
  // Scroll once images and fonts have settled, so the card stays where we put it.
  if(known(NAV.site())){
    const land=()=>reveal(true);
    if(document.readyState==='complete') land(); else window.addEventListener('load',land);
  }
}
</script>
</body>
</html>
"""
