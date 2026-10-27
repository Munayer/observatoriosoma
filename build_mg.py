"""Build the Minas Gerais strategic-minerals pages from the Observatory's ANM extract.

    python build_mg.py <anm_mg_municipios.xlsx> <relatorio_consolidado.docx>

Reads the workbook (sheet MG_todos_alvo: one row per active ANM process for the seven
strategic minerals) and the consolidated report, and writes:

    data/mg/resumo.json             mineral x phase totals (the report's table 2)
    data/mg/municipios.json         processes per municipality, mineral and phase
    data/mg/municipios-mg.geojson   IBGE municipal mesh for MG (fetched once, cached)
    data/mg/processos-minerais-estrategicos-mg.csv
    mg.html                         the report as a page of the site

Holder names (NOME) are published for legal entities only. Natural persons' names are
left out (see HOLDER_RULES): the site never names a person it has not notified. Every
process also links to its public record in the ANM Cadastro Mineiro.

Needs openpyxl and python-docx.
"""

import csv
import gzip
import html
import json
import re
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import docx
import openpyxl
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "mg"
ASSET_V = "20261027c"   # bump with assets/soma.css and soma.js

IBGE_MESH = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/31"
             "?intrarregiao=municipio&formato=application/vnd.geo%2Bjson&qualidade=minima")
IBGE_LIST = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios"

# Key, label in the workbook, ANM substance spellings (for the live SIGMINE query)
MINERALS = [
    ("litio",        "Lítio",        ["MINÉRIO DE LÍTIO", "LÍTIO"]),
    ("manganes",     "Manganês",     ["MINÉRIO DE MANGANÊS", "MANGANÊS", "FERRO MANGANÊS"]),
    ("terras-raras", "Terras raras", ["TERRAS RARAS"]),
    ("niobio",       "Nióbio",       ["MINÉRIO DE NIÓBIO", "NIÓBIO"]),
    ("niquel",       "Níquel",       ["MINÉRIO DE NÍQUEL", "NÍQUEL"]),
    ("cobre",        "Cobre",        ["MINÉRIO DE COBRE", "COBRE"]),
    ("cobalto",      "Cobalto",      ["MINÉRIO DE COBALTO"]),
]
KEY_BY_LABEL = {label: key for key, label, _ in MINERALS}

# Phase groups, in the order of the administrative procedure
GROUPS = ["pesquisa", "lavra", "disponibilidade", "outros"]
GROUP_OF = {
    "REQUERIMENTO DE PESQUISA": "pesquisa",
    "AUTORIZAÇÃO DE PESQUISA": "pesquisa",
    "DIREITO DE REQUERER A LAVRA": "lavra",
    "REQUERIMENTO DE LAVRA": "lavra",
    "CONCESSÃO DE LAVRA": "lavra",
    "APTO PARA DISPONIBILIDADE": "disponibilidade",
    "DISPONIBILIDADE": "disponibilidade",
}
NAME_FIX = {"Passa-Vinte": "Passa Vinte", "São Thomé das Letras": "São Tomé das Letras"}

# Holder names: shown for legal entities, hidden for natural persons. Patterns run on the
# name folded to unaccented upper case; the same strings drive the map page (in JS).
# A name is hidden when it carries a CPF, is an estate, or has no corporate marker. An
# individual entrepreneur ("Fulano da Silva ME") carries a person's name, so ME/EPP/MEI
# alone do not count as a corporate marker.
HOLDER_RULES = {
    "ocultar": r"CPF|\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11}|^ESPOLIO\b",
    "empresa": (r"\b(LTDA|LIMITADA|EIRELI|EIRELLI|EIRELLE|SLU|CIA|COMPANHIA|MINERA\w*|MINERIOS?|"
                r"MINERAIS|METAIS|METALS?|METALURG\w*|MINING|MINES|MINERALS|RESOURCES|RECURSOS|"
                r"HOLDINGS?|PARTICIPA\w*|EMPREENDIMENTOS?|GEOLOGIA|GEOLOGICA|PESQUISAS|CONSTRU\w*|"
                r"INDUSTRIA\w*|COMERCIO|SERVICOS|TERRAPLENAGEM|PAVIMENTA\w*|INVESTIMENTOS?|"
                r"INCORPORA\w*|INC|CORP\w*|LIMITED|LTD|GMBH|PTY|EXPLORATION|VENTURES|CAPITAL|GROUP|"
                r"GRUPO|NEGOCIOS|CONSULTORIA|ASSESSORIA|INTERMEDIA\w*|TRADING|REFRATARIOS|"
                r"COOPERATIVA|ASSOCIA\w*|SOCIEDADE|PREFEITURA|MUNICIPIO|DEPARTAMENTO|INSTITUTO|"
                r"FUNDACAO|UNIVERSIDADE|CONSORCIO|SECRETARIA)\b"
                # S.A. in its spellings, but not the surname Sá ("Faria de Sá")
                r"|S\.A\.?|S/A|(?<!DE )\bS ?A$|(?<!DE )\bSA [A-Z]+$"),
}
HOLDER_HIDE = re.compile(HOLDER_RULES["ocultar"])
HOLDER_FIRM = re.compile(HOLDER_RULES["empresa"])


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper().strip()


def holder(name):
    """(display name, kind) for a NOME value: kind is empresa, pessoa or nao-cadastrado."""
    if not name or fold(name) == "DADO NAO CADASTRADO":
        return "", "nao-cadastrado"
    f = fold(name)
    if HOLDER_HIDE.search(f) or not HOLDER_FIRM.search(f):
        return "", "pessoa"
    return name.strip(), "empresa"


def fetch(url):
    raw = urllib.request.urlopen(url, timeout=120).read()
    return gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw


def read_processes(xlsx):
    ws = openpyxl.load_workbook(xlsx, read_only=True)["MG_todos_alvo"]
    rows = ws.iter_rows(values_only=True)
    head = [h for h in next(rows)]
    out = []
    for r in rows:
        rec = dict(zip(head, r))
        if not rec.get("PROCESSO"):
            continue
        out.append(rec)
    return out


def summarise(procs):
    by = {key: {"n": 0, "area": 0.0, "desde2020": 0, "fases": Counter(), "area_fases": Counter(),
                "grupos": Counter()} for key, _, _ in MINERALS}
    for p in procs:
        s = by[KEY_BY_LABEL[p["MINERAL_ALVO"]]]
        a = float(p["AREA_HA"] or 0)
        s["n"] += 1
        s["area"] += a
        s["desde2020"] += int(p["ANO"] or 0) >= 2020
        s["fases"][p["FASE"]] += 1
        s["area_fases"][p["FASE"]] += a
        s["grupos"][GROUP_OF.get(p["FASE"], "outros")] += 1
    return by


def municipalities(procs, ibge_list):
    code = {m["nome"]: str(m["id"]) for m in ibge_list}
    out = defaultdict(lambda: {"nome": "", "m": {}})
    missing = Counter()
    for p in procs:
        name = NAME_FIX.get(p["MUNICIPIO_DOM"], p["MUNICIPIO_DOM"])
        c = code.get(name)
        if not c:
            missing[name] += 1
            continue
        rec = out[c]
        rec["nome"] = name
        key = KEY_BY_LABEL[p["MINERAL_ALVO"]]
        cell = rec["m"].setdefault(key, [0, 0, 0, 0, 0.0])   # pesquisa, lavra, disp., outros, ha
        cell[GROUPS.index(GROUP_OF.get(p["FASE"], "outros"))] += 1
        cell[4] = round(cell[4] + float(p["AREA_HA"] or 0), 2)
    return dict(out), missing


def write_mesh(ibge_mesh, ibge_list):
    names = {str(m["id"]): m["nome"] for m in ibge_list}
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 4), round(c[1], 4)]
    feats = []
    for f in ibge_mesh["features"]:
        cod = f["properties"]["codarea"]
        g = f["geometry"]
        feats.append({"type": "Feature", "properties": {"cod": cod, "nome": names.get(cod, "")},
                      "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}})
    fc = {"type": "FeatureCollection",
          "source": "IBGE, malha municipal de Minas Gerais (API de malhas v3, qualidade mínima)",
          "features": feats}
    (OUT / "municipios-mg.geojson").write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")),
                                                encoding="utf-8")


# ---------------------------------------------------------------- report (docx) ---

def docx_blocks(path):
    """Paragraphs, list items and tables of the report, in document order."""
    d = docx.Document(path)
    tables = iter(d.tables)
    paras = {p._p: p for p in d.paragraphs}
    blocks = []
    for el in d.element.body.iterchildren():
        if el.tag == qn("w:p"):
            p = paras[el]
            text = p.text.strip()
            if not text:
                continue
            style = p.style.name
            kind = ("h1" if style == "Heading 1" else "h2" if style == "Heading 2"
                    else "li" if style.startswith("List") else "p")
            blocks.append((kind, text))
        elif el.tag == qn("w:tbl"):
            t = next(tables)
            blocks.append(("table", [[c.text.strip() for c in r.cells] for r in t.rows]))
    return blocks


def esc(s):
    return html.escape(s, quote=False)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


SECTION_MINERAL = {"4": "litio", "5": "manganes", "6": "terras-raras", "7": "niobio",
                   "8": "niquel", "9": "cobre"}


def render_report(blocks):
    """HTML for the report body; returns (title, byline, body_html, toc)."""
    title, byline = blocks[0][1], blocks[1][1]
    body, toc, in_list = [], [], False
    section = None
    for kind, val in blocks[2:]:
        if kind != "li" and in_list:
            body.append("</ul>")
            in_list = False
        if kind == "h2":
            num = val.split(".")[0] if val[0].isdigit() else ""
            section = num
            sid = "s-" + (num or slug(val))
            toc.append((sid, val))
            body.append(f'<h2 class="label" id="{sid}">{esc(val)}</h2>')
            if num in SECTION_MINERAL:
                k = SECTION_MINERAL[num]
                body.append(f'<p class="maplink"><a href="mg-mapa.html#mineral={k}">'
                            f'Ver {esc(val.split(". ", 1)[1].lower())} no mapa (dados ao vivo da ANM) →</a></p>')
        elif kind == "p":
            body.append(f"<p>{esc(val)}</p>")
            if section == "3" and val.startswith("Os sete minerais somam"):
                body.append('<div id="chart-fases" class="chart" role="img" '
                            'aria-label="Distribuição dos processos de cada mineral por fase"></div>')
        elif kind == "li":
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{esc(val)}</li>")
        elif kind == "table":
            head, *rows = val
            num_cols = {i for i in range(len(head))
                        if all(re.fullmatch(r"[\d.,]+( \(.*\))?", r[i] or "0") for r in rows)}
            th = "".join(f'<th{" class=num" if i in num_cols else ""}>{esc(h)}</th>'
                         for i, h in enumerate(head))
            trs = "".join("<tr>" + "".join(f'<td{" class=num" if i in num_cols else ""}>{esc(c)}</td>'
                                            for i, c in enumerate(r)) + "</tr>" for r in rows)
            body.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead>'
                        f"<tbody>{trs}</tbody></table></div>")
    if in_list:
        body.append("</ul>")
    return title, byline, "\n".join(body), toc


PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Minerais estratégicos em MG — Observatório SOMA</title>
<meta name="description" content="Relatório consolidado do Observatório sobre os processos minerários ativos de sete minerais estratégicos em Minas Gerais, com base nos dados abertos da ANM.">
<link rel="stylesheet" href="assets/soma.css?v=__V__">
<script src="assets/soma.js?v=__V__"></script>
<style>
  *{box-sizing:border-box}
  body{margin:0;background:var(--soma-paper);color:var(--soma-text);font:400 16px/1.7 var(--soma-font)}
  a{color:var(--soma-link)}
  .cover{background:var(--soma-band);color:#fff;padding:52px 0 0}
  .in{max-width:1080px;margin:0 auto;padding:0 20px}
  .cover .eyebrow{font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.82);margin:0}
  .cover h1{font:700 clamp(28px,4.8vw,44px)/1.15 var(--soma-font);color:var(--soma-mint);margin:12px 0 24px;max-width:820px}
  .cover .strip{display:inline-block;background:var(--soma-mint);color:var(--soma-navy);font-size:15.5px;padding:9px 16px;margin:0 0 -20px;position:relative}
  .layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:48px;padding-top:56px;padding-bottom:72px}
  @media(max-width:900px){.layout{grid-template-columns:1fr;gap:0}}
  nav.toc{position:sticky;top:calc(var(--soma-bar-h) + 20px);align-self:start;font-size:13.5px}
  nav.toc p{font-weight:600;color:var(--soma-heading);margin:0 0 8px}
  nav.toc a{display:block;padding:4px 8px;color:var(--soma-text-2);text-decoration:none;border-left:3px solid transparent}
  nav.toc a:hover{color:var(--soma-heading);border-left-color:var(--soma-mint)}
  @media(max-width:900px){nav.toc{position:static;margin-bottom:28px}}
  article{min-width:0;max-width:760px}
  article p, article li{color:var(--soma-text-2);overflow-wrap:break-word}
  article > p:first-of-type{font-size:17px;color:var(--soma-text)}
  h2.label{display:inline-block;background:var(--soma-mint);color:var(--soma-navy);
    font:400 clamp(20px,3vw,25px)/1.25 var(--soma-font);padding:7px 15px;margin:2.6em 0 .7em}
  h2.label:first-child{margin-top:0}
  .maplink{margin:-.2em 0 1em;font-size:14.5px;font-weight:600}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:0 0 36px}
  .tile{border-top:4px solid var(--soma-mint);background:var(--soma-grey);padding:14px 16px}
  .tile .k{font-size:12.5px;color:var(--soma-text-2)}
  .tile .v{font-size:28px;line-height:1.15;color:var(--soma-heading);font-weight:600;margin:4px 0}
  .tile .n{font-size:12.5px;color:var(--soma-text-2)}
  .live{display:flex;align-items:flex-start;gap:10px;margin:0 0 36px;padding:12px 16px;
    border:1px solid var(--soma-line);border-left:4px solid var(--soma-navy);font-size:14px}
  .live b{color:var(--soma-heading)}
  .live .dot{width:9px;height:9px;border-radius:50%;background:#898781;flex:none;margin-top:7px}
  .live.ok .dot{background:#0ca30c} .live.err .dot{background:#d03b3b}
  .table-wrap{overflow-x:auto;margin:1.2em 0 1.6em}
  table{border-collapse:collapse;width:100%;font-size:13.5px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--soma-line);vertical-align:top}
  th{color:var(--soma-heading);font-weight:600;background:var(--soma-grey)}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .downloads{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 0}
  .downloads a{padding:8px 14px;border:1px solid var(--soma-line);text-decoration:none;font-size:14px;font-weight:600}
  .downloads a:hover{border-color:var(--soma-navy)}
  .lang-note{font-size:14px;background:var(--soma-mint-soft);border-left:4px solid var(--soma-mint);padding:10px 14px;margin:0 0 28px}
  /* chart: share of each mineral's processes by phase group */
  .chart{margin:1.4em 0 2em;
    --ph-pesquisa:#2a78d6;--ph-lavra:#eb6834;--ph-disponibilidade:#1baf7a;--ph-outros:#b4b2a9}
  @media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .chart{
    --ph-pesquisa:#3987e5;--ph-lavra:#d95926;--ph-disponibilidade:#199e70;--ph-outros:#5f5e5a}}
  :root[data-theme="dark"] .chart{--ph-pesquisa:#3987e5;--ph-lavra:#d95926;--ph-disponibilidade:#199e70;--ph-outros:#5f5e5a}
  .legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--soma-text-2);margin:0 0 10px}
  .legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
  .bars{display:grid;grid-template-columns:110px minmax(0,1fr) 70px;gap:8px 12px;align-items:center;font-size:13.5px}
  .bars .lab{color:var(--soma-text)}
  .bars .tot{text-align:right;color:var(--soma-text-2);font-variant-numeric:tabular-nums}
  .bar{display:flex;gap:2px;height:18px}
  .bar span{height:100%;min-width:2px;outline:none}
  .bar span:first-child{border-radius:4px 0 0 4px} .bar span:last-child{border-radius:0 4px 4px 0}
  .bar span:only-child{border-radius:4px}
  .bar span:hover,.bar span:focus-visible{filter:brightness(1.12);box-shadow:0 0 0 2px var(--soma-paper),0 0 0 3px var(--soma-text-2)}
  .chart .axis{grid-column:2;display:flex;justify-content:space-between;font-size:11.5px;color:#898781;font-variant-numeric:tabular-nums}
  .tip{position:fixed;z-index:2000;pointer-events:none;background:var(--soma-paper);color:var(--soma-text);
    border:1px solid var(--soma-line);box-shadow:0 4px 14px rgba(0,0,0,.12);padding:8px 10px;font-size:12.5px;line-height:1.45;opacity:0;transition:opacity .1s}
  .tip b{color:var(--soma-heading)}
  @media (prefers-reduced-motion: reduce){.tip{transition:none}}
</style>
</head>
<body>

<div class="cover">
  <div class="in">
    <p class="eyebrow"><span data-lang="pt">Relatório consolidado · base ANM</span><span data-lang="en" hidden>Consolidated report · ANM data</span></p>
    <h1>__TITLE__</h1>
    <div class="strip">__BYLINE__</div>
  </div>
</div>

<div class="in layout">
  <nav class="toc" aria-label="Sumário">
    <p><span data-lang="pt">Sumário</span><span data-lang="en" hidden>Contents</span></p>
    __TOC__
    <p style="margin-top:18px"><a href="mg-mapa.html" style="border:0;padding-left:0;color:var(--soma-link);font-weight:600"><span data-lang="pt">Abrir o mapa →</span><span data-lang="en" hidden>Open the map →</span></a></p>
  </nav>
  <article>
    <p class="lang-note" data-lang="en" hidden>This report is available in Portuguese only. Figures, the chart and the map labels follow the language switch.</p>
    <div class="tiles">
      <div class="tile"><div class="k"><span data-lang="pt">Processos ativos</span><span data-lang="en" hidden>Active processes</span></div><div class="v">__N__</div><div class="n"><span data-lang="pt">sete minerais, MG</span><span data-lang="en" hidden>seven minerals, MG</span></div></div>
      <div class="tile"><div class="k"><span data-lang="pt">Área requerida</span><span data-lang="en" hidden>Area under title</span></div><div class="v">__AREA__</div><div class="n"><span data-lang="pt">milhões de hectares</span><span data-lang="en" hidden>million hectares</span></div></div>
      <div class="tile"><div class="k"><span data-lang="pt">Em fase de pesquisa</span><span data-lang="en" hidden>At exploration stage</span></div><div class="v">__PESQ__</div><div class="n"><span data-lang="pt">requerimento ou autorização</span><span data-lang="en" hidden>application or permit</span></div></div>
      <div class="tile"><div class="k"><span data-lang="pt">Concessões de lavra</span><span data-lang="en" hidden>Mining concessions</span></div><div class="v">__CONC__</div><div class="n"><span data-lang="pt">em vigor</span><span data-lang="en" hidden>in force</span></div></div>
    </div>
    <div class="live" id="live" aria-live="polite">
      <span class="dot"></span>
      <span id="live-text"><span data-lang="pt">Verificando a base ao vivo da ANM…</span><span data-lang="en" hidden>Checking the live ANM database…</span></span>
    </div>
__BODY__
    <h2 class="label" id="s-dados"><span data-lang="pt">Dados e downloads</span><span data-lang="en" hidden>Data and downloads</span></h2>
    <p><span data-lang="pt">Os números desta página vêm da extração do SIGMINE feita pelo Observatório em __EXTRACT__. No CSV e no mapa aparecem os nomes dos titulares que são empresas ou órgãos públicos; os de pessoas físicas não são republicados. Cada processo pode ser consultado no Cadastro Mineiro da ANM pelo seu número.</span><span data-lang="en" hidden>The figures on this page come from the Observatory's SIGMINE extract of __EXTRACT__. The CSV and the map show holders that are companies or public bodies; natural persons' names are not republished. Every process can be looked up by number in ANM's Cadastro Mineiro.</span></p>
    <div class="downloads">
      <a href="data/mg/processos-minerais-estrategicos-mg.csv" download>Processos (.csv)</a>
      <a href="data/mg/resumo.json">Resumo (.json)</a>
      <a href="data/mg/municipios.json">Municípios (.json)</a>
      <a href="mg-mapa.html"><span data-lang="pt">Mapa interativo</span><span data-lang="en" hidden>Interactive map</span></a>
    </div>
  </article>
</div>

<div class="tip" id="tip" role="tooltip"></div>
<script>
(function () {
  var RESUMO = __RESUMO__;
  var L = function () { return window.SOMA ? SOMA.lang() : "pt"; };
  var T = {
    pesquisa: {pt: "Pesquisa", en: "Exploration"}, lavra: {pt: "Lavra", en: "Mining"},
    disponibilidade: {pt: "Disponibilidade", en: "Available"}, outros: {pt: "Outras", en: "Other"}
  };
  var fmt = function (n) { return n.toLocaleString(L() === "pt" ? "pt-BR" : "en-GB"); };

  /* Share of each mineral's processes by phase group: 100% stacked bars, total at the end. */
  function chart() {
    var host = document.getElementById("chart-fases");
    if (!host) return;
    var l = L(), groups = RESUMO.grupos;
    var legend = '<div class="legend">' + groups.map(function (g) {
      return '<span><i style="background:var(--ph-' + g + ')"></i>' + T[g][l] + "</span>";
    }).join("") + "</div>";
    var rows = RESUMO.minerais.map(function (m) {
      var segs = groups.map(function (g, i) {
        var v = m.grupos[i]; if (!v) return "";
        var pct = 100 * v / m.n;
        return '<span tabindex="0" style="flex:' + v + ' 1 0;background:var(--ph-' + g + ')" data-tip="' +
          "<b>" + m.nome + "</b><br>" + T[g][l] + ": " + fmt(v) + " (" + pct.toFixed(pct < 1 ? 1 : 0) + "%)" + '"></span>';
      }).join("");
      return '<div class="lab">' + m.nome + '</div><div class="bar">' + segs + '</div><div class="tot">' + fmt(m.n) + "</div>";
    }).join("");
    host.innerHTML = legend + '<div class="bars">' + rows +
      '<div class="axis"><span>0%</span><span>50%</span><span>100%</span></div><div></div></div>';
    var tip = document.getElementById("tip");
    var show = function (e) {
      var t = e.target.closest("[data-tip]"); if (!t) return;
      tip.innerHTML = t.getAttribute("data-tip"); tip.style.opacity = 1;
      var r = t.getBoundingClientRect(), x = e.clientX || (r.left + r.width / 2), y = e.clientY || r.top;
      tip.style.left = Math.min(x + 12, innerWidth - tip.offsetWidth - 8) + "px";
      tip.style.top = (y - tip.offsetHeight - 12 < 8 ? y + 18 : y - tip.offsetHeight - 12) + "px";
    };
    host.addEventListener("pointermove", show);
    host.addEventListener("focusin", show);
    host.addEventListener("pointerleave", function () { tip.style.opacity = 0; });
    host.addEventListener("focusout", function () { tip.style.opacity = 0; });
  }

  /* Live check against ANM's SIGMINE service: same filter as the extract. */
  function live() {
    var box = document.getElementById("live"), txt = document.getElementById("live-text");
    var subs = RESUMO.minerais.reduce(function (a, m) { return a.concat(m.subs); }, []);
    var where = "UF='MG' AND SUBS IN (" + subs.map(function (s) { return "'" + s + "'"; }).join(",") + ")";
    var url = RESUMO.api + "/query?where=" + encodeURIComponent(where) + "&returnCountOnly=true&f=json";
    var t0 = performance.now();
    fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
      if (typeof d.count !== "number") throw new Error("resposta");
      var ms = Math.round(performance.now() - t0), diff = d.count - RESUMO.total.n, l = L();
      box.className = "live ok";
      txt.innerHTML = l === "pt"
        ? "<b>API da ANM conectada</b> · agora há <b>" + fmt(d.count) + "</b> processos ativos destes minerais em MG (" +
          (diff === 0 ? "igual à" : (diff > 0 ? "+" : "") + fmt(diff) + " em relação à") + " extração de " + RESUMO.extracao + ") · " + ms + " ms"
        : "<b>ANM API connected</b> · <b>" + fmt(d.count) + "</b> active processes for these minerals in MG right now (" +
          (diff === 0 ? "same as" : (diff > 0 ? "+" : "") + fmt(diff) + " against") + " the " + RESUMO.extracao + " extract) · " + ms + " ms";
    }).catch(function () {
      box.className = "live err";
      txt.textContent = L() === "pt" ? "Não foi possível consultar a API da ANM agora. Os números da página são os da extração."
                                     : "The ANM API could not be reached just now. The page shows the extract's figures.";
    });
  }

  chart(); live();
  document.addEventListener("soma:lang", function () { chart(); live(); });
})();
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    xlsx, report = sys.argv[1], sys.argv[2]
    OUT.mkdir(parents=True, exist_ok=True)

    procs = read_processes(xlsx)
    by = summarise(procs)

    ibge_list_path = OUT / ".ibge-municipios.json"
    if not ibge_list_path.exists():
        ibge_list_path.write_bytes(fetch(IBGE_LIST))
    ibge_list = json.loads(ibge_list_path.read_text(encoding="utf-8"))
    if not (OUT / "municipios-mg.geojson").exists():
        write_mesh(json.loads(fetch(IBGE_MESH)), ibge_list)

    muni, missing = municipalities(procs, ibge_list)
    if missing:
        print("municipalities not matched to IBGE:", dict(missing))

    total_n = sum(s["n"] for s in by.values())
    total_area = sum(s["area"] for s in by.values())
    resumo = {
        "fonte": "ANM, SIGMINE PROCESSOS_MINERARIOS, MG.zip",
        "extracao": "16/10/2026",
        "relatorio": "17/10/2026",
        "api": "https://geo.anm.gov.br/arcgis/rest/services/SIGMINE/dados_anm/MapServer/0",
        "grupos": GROUPS,
        "titular_regras": HOLDER_RULES,
        "total": {"n": total_n, "area_ha": round(total_area)},
        "minerais": [{
            "chave": key, "nome": label, "subs": subs,
            "n": by[key]["n"], "area_ha": round(by[key]["area"]),
            "desde2020": by[key]["desde2020"],
            "grupos": [by[key]["grupos"][g] for g in GROUPS],
            "fases": {f: [n, round(by[key]["area_fases"][f])] for f, n in by[key]["fases"].most_common()},
        } for key, label, subs in MINERALS],
    }
    (OUT / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "municipios.json").write_text(json.dumps(
        {"campos": GROUPS + ["area_ha"], "minerais": [k for k, _, _ in MINERALS], "municipios": muni},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    cols = ["PROCESSO", "ANO", "AREA_HA", "FASE", "ULT_EVENTO", "SUBS", "USO",
            "MUNICIPIO_DOM", "MUNICIPIOS", "MINERAL_ALVO"]
    with open(OUT / "processos-minerais-estrategicos-mg.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cols + ["TITULAR", "TITULAR_TIPO"])
        for p in procs:
            w.writerow([p.get(c) if p.get(c) is not None else "" for c in cols] + list(holder(p.get("NOME"))))

    title, byline, body, toc = render_report(docx_blocks(report))
    byline = byline.replace("Oct 17, 2026", "17 out. 2026").replace("@Bernardo", "Bernardo Máximo Munayer")
    conc = sum(s["fases"]["CONCESSÃO DE LAVRA"] for s in by.values())
    pesq = sum(s["grupos"]["pesquisa"] for s in by.values())
    page = (PAGE.replace("__V__", ASSET_V)
            .replace("__TITLE__", esc(title))
            .replace("__BYLINE__", esc(byline))
            .replace("__TOC__", "\n    ".join(f'<a href="#{sid}">{esc(t)}</a>' for sid, t in toc))
            .replace("__N__", f"{total_n:,}".replace(",", "."))
            .replace("__AREA__", f"{total_area / 1e6:.2f}".replace(".", ","))
            .replace("__PESQ__", f"{100 * pesq / total_n:.0f}%")
            .replace("__CONC__", str(conc))
            .replace("__EXTRACT__", resumo["extracao"])
            .replace("__BODY__", body)
            .replace("__RESUMO__", json.dumps(resumo, ensure_ascii=False, separators=(",", ":"))))
    (ROOT / "mg.html").write_text(page, encoding="utf-8")

    for m in resumo["minerais"]:
        print(f'{m["nome"]:13} {m["n"]:5} proc  {m["area_ha"]:>9} ha  grupos {m["grupos"]}  desde2020 {m["desde2020"]}')
    print("total", total_n, round(total_area), "| municipalities", len(muni), "| concessions", conc)
    kinds = Counter(holder(p.get("NOME"))[1] for p in procs)
    print("holders per process:", dict(kinds))


if __name__ == "__main__":
    main()
