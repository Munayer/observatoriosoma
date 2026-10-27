"""Build report.html — a minimal single-file reading view of docs/00-SOMA.md,
with an EN/PT language toggle. Reads the two source markdown files directly (built by the
assembly scripts) rather than re-splitting the combined docs/00-SOMA.md."""

import re
import markdown

OUT = "report.html"


def convert(md_path, lang):
    src = open(md_path, encoding="utf-8").read()
    md = markdown.Markdown(extensions=["extra", "toc", "sane_lists"],
                            extension_configs={"toc": {"permalink": False}})
    html = md.convert(src)

    # Wrap tables for horizontal scroll
    html = re.sub(r"(<table>)", r'<div class="table-wrap">\1', html)
    html = re.sub(r"(</table>)", r"\1</div>", html)

    # Prefix every heading id and internal anchor with the language, to keep EN/PT ids
    # from colliding when both trees are in the DOM at once.
    html = re.sub(r'(<h[1-4] id=")([^"]*)(")', rf'\1{lang}-\2\3', html)

    # Re-key top-level (H2) section ids to a stable "sec-N" form based on the leading
    # number in the heading text, so the nav can target them without relying on slugs.
    def resec(m):
        num, rest = m.group(2), m.group(3)
        return f'<h2 id="{lang}-sec-{num}"{rest}'
    html = re.sub(r'(<h2 id="[^"]*")( >|>)?\s*(?:)', lambda m: m.group(0), html)  # no-op guard
    html = re.sub(r'<h2 id="[^"]*">(\d+)\s+([^<]*)</h2>',
                  lambda m: f'<h2 id="{lang}-sec-{m.group(1)}">{m.group(1)} {m.group(2)}</h2>',
                  html)

    # Protect fenced code blocks from the citation-linking regex below.
    blocks = []
    def stash(m):
        blocks.append(m.group(0))
        return f"@@BLOCK{len(blocks) - 1}@@"
    html = re.sub(r"<pre>.*?</pre>", stash, html, flags=re.S)

    # Turn [N] / [N, M] citation markers into links to the reference entries, and give
    # each "[N] ..." reference paragraph a matching id.
    html = re.sub(
        r"\[(\d+(?:,\s*\d+)*)\]",
        lambda m: "[" + ", ".join(
            f'<a href="#{lang}-ref-{n.strip()}" class="cite">{n.strip()}</a>'
            for n in m.group(1).split(",")
        ) + "]",
        html,
    )
    html = re.sub(
        r'<p>\[<a href="#' + lang + r'-ref-(\d+)" class="cite">\d+</a>\]',
        lambda m: f'<p id="{lang}-ref-{m.group(1)}">[<a href="#{lang}-ref-{m.group(1)}" class="cite">{m.group(1)}</a>]',
        html,
    )

    for i, b in enumerate(blocks):
        html = html.replace(f"@@BLOCK{i}@@", b)

    # Top-level nav: H2 sections only, in document order, deduplicated.
    nav = []
    seen = set()
    for m in re.finditer(rf'<h2 id="{lang}-sec-(\d+)">(\d+)\s+([^<]*)</h2>', html):
        n = m.group(1)
        if n in seen:
            continue
        seen.add(n)
        nav.append((n, m.group(3)))

    return html, nav


en_html, en_nav = convert("/tmp/en_full.md", "en")
pt_html, pt_nav = convert("/tmp/pt_full.md", "pt")

nav_by_num_en = dict(en_nav)
nav_by_num_pt = dict(pt_nav)
all_nums = sorted(set(nav_by_num_en) | set(nav_by_num_pt), key=int)

nav_html = "\n".join(
    f'<a href="#en-sec-{n}" data-num="{n}">'
    f'<span class="l-en">{nav_by_num_en.get(n, "")}</span>'
    f'<span class="l-pt" hidden>{nav_by_num_pt.get(n, "")}</span>'
    f"</a>"
    for n in all_nums
)

TEMPLATE = """<title>Observatório SOMA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,500&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --paper: #f6f6f3;
  --paper-raised: #ffffff;
  --ink: #181b1f;
  --muted: #5c6169;
  --faint: #8a8f96;
  --line: #dfe0dc;
  --accent: #1f5fa6;
  --accent-ink: #ffffff;
  --accent-soft: #e7eef7;
  --code-bg: #eceae4;
  --shadow: rgba(20, 24, 28, 0.08);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #14171b;
    --paper-raised: #1a1e23;
    --ink: #e9e7e1;
    --muted: #9a9fa4;
    --faint: #6b7076;
    --line: #282d33;
    --accent: #7db0e8;
    --accent-ink: #0e1114;
    --accent-soft: #1c2733;
    --code-bg: #1e2328;
    --shadow: rgba(0, 0, 0, 0.35);
  }
}
:root[data-theme="dark"] {
  --paper: #14171b;
  --paper-raised: #1a1e23;
  --ink: #e9e7e1;
  --muted: #9a9fa4;
  --faint: #6b7076;
  --line: #282d33;
  --accent: #7db0e8;
  --accent-ink: #0e1114;
  --accent-soft: #1c2733;
  --code-bg: #1e2328;
  --shadow: rgba(0, 0, 0, 0.35);
}

* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Public Sans", -apple-system, "Segoe UI", sans-serif;
  font-size: 16.5px;
  line-height: 1.65;
}

.shell {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  gap: 56px;
  padding: 0 32px;
}
@media (max-width: 900px) {
  .shell { grid-template-columns: 1fr; padding: 0 20px; }
}

.rail {
  position: sticky;
  top: 0;
  align-self: start;
  padding: 48px 0 40px;
  max-height: 100vh;
  overflow-y: auto;
  scrollbar-width: thin;
}
.mark {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 20px;
}
.mark .brand { display: flex; align-items: baseline; gap: 8px; }
.mark .glyph {
  font-family: "Newsreader", Georgia, serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--accent);
}
.mark .word {
  font-family: "Newsreader", Georgia, serif;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.langswitch {
  display: inline-flex;
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 24px;
}
.langswitch button {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  border: none;
  background: var(--paper-raised);
  color: var(--muted);
  padding: 6px 14px;
  cursor: pointer;
}
.langswitch button + button { border-left: 1px solid var(--line); }
.langswitch button.active { background: var(--accent); color: var(--accent-ink); }
.langswitch button:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }

.rail nav { display: flex; flex-direction: column; gap: 2px; }
.rail nav a {
  font-size: 0.86rem;
  color: var(--muted);
  text-decoration: none;
  padding: 6px 10px;
  border-radius: 3px;
  border-left: 2px solid transparent;
  line-height: 1.35;
}
.rail nav a:hover { color: var(--ink); background: var(--accent-soft); }
.rail nav a.active {
  color: var(--accent);
  border-left-color: var(--accent);
  background: var(--accent-soft);
  font-weight: 600;
}
.rail-foot {
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  font-size: 0.74rem;
  color: var(--faint);
  line-height: 1.6;
}

.mobile-toc { display: none; }
@media (max-width: 900px) {
  .rail { position: static; padding: 28px 0 8px; max-height: none; }
  .rail nav { display: none; }
  .mobile-toc {
    display: block;
    width: 100%;
    text-align: left;
    background: var(--paper-raised);
    border: 1px solid var(--line);
    color: var(--ink);
    font-family: inherit;
    font-size: 0.85rem;
    padding: 10px 14px;
    border-radius: 6px;
    margin-top: 4px;
  }
  .rail.open nav { display: flex; margin-top: 10px; }
}

article { padding: 48px 0 120px; min-width: 0; }
.doc[hidden] { display: none; }
article > .front { margin-bottom: 40px; }
article h1 {
  font-family: "Newsreader", Georgia, serif;
  font-size: 2.3rem;
  font-weight: 600;
  line-height: 1.18;
  text-wrap: balance;
  margin: 0 0 10px;
}
article > p:first-of-type { color: var(--muted); font-size: 1rem; margin-top: 0; }

h2 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 600;
  font-size: 1.55rem;
  text-wrap: balance;
  margin: 3.2em 0 0.9em;
  padding-top: 1.4em;
  border-top: 1px solid var(--line);
  scroll-margin-top: 20px;
}
.doc > h2:first-of-type { border-top: none; padding-top: 0; margin-top: 0.4em; }
h3 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 600;
  font-size: 1.22rem;
  text-wrap: balance;
  margin: 2.2em 0 0.6em;
  scroll-margin-top: 20px;
}
h4 {
  font-family: "Public Sans", sans-serif;
  font-weight: 700;
  font-size: 0.92rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  margin: 1.8em 0 0.5em;
  scroll-margin-top: 20px;
}
p, li { max-width: 68ch; }
p { margin: 0.85em 0; }
ul, ol { padding-left: 1.3em; margin: 0.85em 0; }
li { margin: 0.35em 0; }
li > p { margin: 0.3em 0; }
strong { font-weight: 700; }
em { font-style: italic; }
a { color: var(--accent); }
a.cite { font-feature-settings: "sups"; font-size: 0.92em; text-decoration: none; }
a.cite:hover { text-decoration: underline; }
blockquote {
  margin: 1.3em 0;
  padding: 0.2em 1.3em;
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  border-radius: 0 4px 4px 0;
  max-width: 68ch;
}
blockquote p { color: var(--ink); }
hr { border: none; border-top: 1px solid var(--line); margin: 3em 0; }

code {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.86em;
  background: var(--code-bg);
  padding: 0.12em 0.4em;
  border-radius: 3px;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 16px 18px;
  overflow-x: auto;
  max-width: 100%;
}
pre code { background: none; padding: 0; font-size: 0.84em; line-height: 1.55; }

.table-wrap { overflow-x: auto; margin: 1.4em 0; }
table {
  border-collapse: collapse;
  width: 100%;
  min-width: 560px;
  font-size: 0.87rem;
}
th, td {
  border: 1px solid var(--line);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
  font-variant-numeric: tabular-nums;
}
th {
  background: var(--accent-soft);
  font-family: "Public Sans", sans-serif;
  font-weight: 700;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--muted);
}
tr:nth-child(even) td { background: color-mix(in srgb, var(--paper-raised) 60%, transparent); }

@media (prefers-reduced-motion: no-preference) {
  html { scroll-behavior: smooth; }
}
</style>

<div class="shell">
  <aside class="rail" id="rail">
    <div class="mark">
      <div class="brand"><span class="glyph">S</span><span class="word">Observatório SOMA</span></div>
    </div>
    <div class="langswitch" role="group" aria-label="Language / Idioma">
      <button type="button" data-lang="en" id="btnEn">EN</button>
      <button type="button" data-lang="pt" id="btnPt">PT</button>
    </div>
    <button class="mobile-toc" id="tocToggle" type="button">
      <span class="l-en">Contents ▾</span><span class="l-pt" hidden>Sumário ▾</span>
    </button>
    <nav id="tocNav">
      __NAV__
    </nav>
    <div class="rail-foot">
      <span class="l-en">Single-document edition · 19 Aug 2026<br>Companion: <code>map.html</code>, <code>dashboard.html</code>, <code>03-catalogues.xlsx</code></span>
      <span class="l-pt" hidden>Edição em documento único · 19 ago 2026<br>Companheiros: <code>map.html</code>, <code>dashboard.html</code>, <code>03-catalogues.xlsx</code></span>
    </div>
  </aside>
  <article>
    <div class="doc" id="doc-en">__BODY_EN__</div>
    <div class="doc" id="doc-pt" hidden>__BODY_PT__</div>
  </article>
</div>

<script>
(function () {
  var LANG_KEY = "soma-lang";
  var lang = "en";
  try {
    var saved = localStorage.getItem(LANG_KEY);
    if (saved === "en" || saved === "pt") lang = saved;
  } catch (e) {}

  var docEn = document.getElementById("doc-en");
  var docPt = document.getElementById("doc-pt");
  var btnEn = document.getElementById("btnEn");
  var btnPt = document.getElementById("btnPt");

  function applyLang(l, scroll) {
    lang = l;
    var isEn = l === "en";
    docEn.hidden = !isEn;
    docPt.hidden = isEn;
    btnEn.classList.toggle("active", isEn);
    btnPt.classList.toggle("active", !isEn);
    document.querySelectorAll(".l-en").forEach(function (el) { el.hidden = !isEn; });
    document.querySelectorAll(".l-pt").forEach(function (el) { el.hidden = isEn; });
    document.querySelectorAll("#tocNav a").forEach(function (a) {
      a.href = "#" + l + "-sec-" + a.getAttribute("data-num");
    });
    try { localStorage.setItem(LANG_KEY, l); } catch (e) {}
    setupObserver();
  }

  btnEn.addEventListener("click", function () { applyLang("en"); });
  btnPt.addEventListener("click", function () { applyLang("pt"); });

  var toggle = document.getElementById("tocToggle");
  var rail = document.getElementById("rail");
  if (toggle) {
    toggle.addEventListener("click", function () { rail.classList.toggle("open"); });
  }

  var currentObserver = null;
  function setupObserver() {
    if (currentObserver) { currentObserver.disconnect(); }
    var links = Array.prototype.slice.call(document.querySelectorAll("#tocNav a"));
    var targets = links.map(function (a) {
      return document.getElementById(lang + "-sec-" + a.getAttribute("data-num"));
    }).filter(Boolean);
    if (!("IntersectionObserver" in window) || !targets.length) return;
    var byNum = {};
    links.forEach(function (a) { byNum[a.getAttribute("data-num")] = a; });
    currentObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var num = entry.target.id.replace(lang + "-sec-", "");
        var link = byNum[num];
        if (!link) return;
        if (entry.isIntersecting) {
          links.forEach(function (l) { l.classList.remove("active"); });
          link.classList.add("active");
        }
      });
    }, { rootMargin: "-10% 0px -75% 0px", threshold: 0 });
    targets.forEach(function (t) { currentObserver.observe(t); });
  }

  applyLang(lang);
})();
</script>
"""

html_out = (TEMPLATE
            .replace("__NAV__", nav_html)
            .replace("__BODY_EN__", en_html)
            .replace("__BODY_PT__", pt_html))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"written {OUT}, {len(html_out)} bytes, {len(all_nums)} nav items")
