/* Observatório SOMA — shared navigation bar, language, EU funding footer and site
   deep links.

   The four demonstration sites carry the same id in every view (BR-PA-0001 …), so
   a site travels between pages in the URL fragment: dashboard.html#site=BR-PA-0001.
   Each page reads it on load, writes it back when the user picks a site, and asks
   this file for the links to the same site in the other views.

   Language: "en" or "pt", remembered under "soma-lang". Elements marked
   data-lang="en" / data-lang="pt" are shown for their language only. Pages with
   their own language logic (the report) listen for the "soma:lang" event. */
(function () {
  var PAGES = [
    { key: "report",    href: "report.html",    en: "Report",    pt: "Relatório" },
    { key: "dashboard", href: "dashboard.html", en: "Dashboard", pt: "Painel" },
    { key: "map",       href: "map.html",       en: "Map",       pt: "Mapa" },
    { key: "team",      href: "team.html",      en: "Team",      pt: "Equipe" }
  ];
  var SITE_KEYS = ["report", "dashboard", "map"];
  var SITE_RE = /^BR-[A-Z]{2}-\d{4}$/;
  var LANG_KEY = "soma-lang";
  var current = null;
  var listeners = [];

  var DISCLAIMER = {
    en: "Co-funded by the European Union. Views and opinions expressed are however " +
        "those of the author(s) only and do not necessarily reflect those of the European " +
        "Union or the European Education and Culture Executive Agency (EACEA). Neither the " +
        "European Union nor EACEA can be held responsible for them.",
    pt: "Cofinanciado pela União Europeia. Os pontos de vista e as opiniões expressas são " +
        "as do(s) autor(es) e não refletem necessariamente a posição da União Europeia ou da " +
        "Agência de Execução Europeia da Educação e da Cultura (EACEA). Nem a União Europeia " +
        "nem a EACEA podem ser tidas como responsáveis por essas opiniões."
  };

  function lang() {
    try {
      var saved = localStorage.getItem(LANG_KEY);
      if (saved === "en" || saved === "pt") return saved;
    } catch (e) {}
    return /^pt\b/i.test(navigator.language || "") ? "pt" : "en";
  }
  function pageKey() {
    var f = location.pathname.split("/").pop().replace(/\.html$/, "");
    return f === "" || f === "index" ? "home" : f;
  }
  function siteFromHash() {
    var m = /(?:^|[#&])site=([^&]+)/.exec(location.hash);
    var id = m ? decodeURIComponent(m[1]) : null;
    return id && SITE_RE.test(id) ? id : null;
  }
  function href(page, key, id) {
    return page + (id && SITE_KEYS.indexOf(key) >= 0 ? "#site=" + encodeURIComponent(id) : "");
  }

  function renderBar() {
    var bar = document.querySelector(".soma-bar");
    if (!bar) {
      bar = document.createElement("header");
      bar.className = "soma-bar";
      document.body.insertBefore(bar, document.body.firstChild);
    }
    var l = lang(), here = pageKey();
    bar.innerHTML =
      '<a class="soma-brand" href="index.html"><span>Observatório </span><b>SOMA</b></a>' +
      '<nav aria-label="' + (l === "pt" ? "Páginas" : "Pages") + '">' +
      PAGES.map(function (p) {
        return '<a href="' + href(p.href, p.key, current) + '"' +
          (p.key === here ? ' aria-current="page"' : "") + ">" + p[l] + "</a>";
      }).join("") +
      "</nav>" +
      '<div class="soma-tools">' +
      '<span class="soma-site"' + (current ? "" : " hidden") +
      ' title="' + (l === "pt" ? "Site selecionado" : "Selected site") + '">' +
      (current || "") + "</span>" +
      '<span class="soma-lang" role="group" aria-label="Language / Idioma">' +
      '<button type="button" data-set-lang="en" aria-pressed="' + (l === "en") + '">EN</button>' +
      '<button type="button" data-set-lang="pt" aria-pressed="' + (l === "pt") + '">PT</button>' +
      "</span></div>";
    Array.prototype.forEach.call(bar.querySelectorAll("[data-set-lang]"), function (b) {
      b.addEventListener("click", function () { setLang(b.getAttribute("data-set-lang")); });
    });
  }

  function renderFoot() {
    var foot = document.querySelector(".soma-foot");
    if (!foot) {
      foot = document.createElement("footer");
      foot.className = "soma-foot";
      document.body.appendChild(foot);
    }
    var l = lang();
    var alt = l === "pt" ? "Cofinanciado pela União Europeia" : "Co-funded by the European Union";
    foot.innerHTML =
      '<div class="soma-foot-in">' +
      '<div><img class="soma-emblem pos" src="assets/eu/co-funded-' + l + '-pos.png" alt="' + alt + '" width="240" height="56">' +
      '<img class="soma-emblem neg" src="assets/eu/co-funded-' + l + '-neg.png" alt="' + alt + '" width="240" height="56"></div>' +
      "<p>" + DISCLAIMER[l] + "</p>" +
      '<div class="soma-foot-meta">' +
      "<span>" + (l === "pt"
        ? "Projeto desenvolvido no âmbito das Ações Jean Monnet do programa Erasmus+."
        : "Developed under the Jean Monnet Actions of the Erasmus+ programme.") + "</span>" +
      '<a href="https://codeberg.org/Munayer/observatoriosoma">' + (l === "pt" ? "Código-fonte" : "Source code") + "</a>" +
      '<a href="LICENSE">' + (l === "pt" ? "Licença Apache-2.0" : "Apache-2.0 licence") + "</a>" +
      '<a href="team.html">' + (l === "pt" ? "Equipe" : "Team") + "</a>" +
      "</div></div>";
  }

  function applyLangBlocks() {
    var l = lang();
    document.documentElement.lang = l === "pt" ? "pt-BR" : "en";
    Array.prototype.forEach.call(document.querySelectorAll("[data-lang]:not(button)"), function (el) {
      el.hidden = el.getAttribute("data-lang") !== l;
    });
  }

  function setLang(l) {
    if (l !== "en" && l !== "pt") return;
    try { localStorage.setItem(LANG_KEY, l); } catch (e) {}
    refresh();
    document.dispatchEvent(new CustomEvent("soma:lang", { detail: l }));
  }

  function refresh() {
    renderBar();
    renderFoot();
    applyLangBlocks();
  }

  /* Links to the same site in the other views, as an HTML string. */
  function xlinks(id, opts) {
    var l = (opts && opts.lang) || lang(), skip = (opts && opts.skip) || pageKey();
    var label = {
      report:    { en: "Read in report",    pt: "Ler no relatório" },
      dashboard: { en: "Open case",         pt: "Abrir o caso" },
      map:       { en: "Show on map",       pt: "Ver no mapa" }
    };
    return '<div class="soma-xlinks">' + PAGES.filter(function (p) {
      return SITE_KEYS.indexOf(p.key) >= 0 && p.key !== skip;
    }).map(function (p) {
      return '<a href="' + href(p.href, p.key, id) + '">' + label[p.key][l] + " →</a>";
    }).join("") + "</div>";
  }

  /* Record the selected site in the URL and the bar, without adding history. */
  function setSite(id) {
    if (id && !SITE_RE.test(id)) return;
    current = id || null;
    var url = location.pathname + location.search + (current ? "#site=" + current : "");
    try { history.replaceState(history.state, "", url); } catch (e) {}
    renderBar();
  }

  function flash(el) {
    if (!el) return;
    el.classList.remove("soma-flash");
    void el.offsetWidth;
    el.classList.add("soma-flash");
  }

  window.addEventListener("hashchange", function () {
    var id = siteFromHash();
    if (!id || id === current) return;
    current = id;
    renderBar();
    listeners.forEach(function (fn) { fn(id); });
  });

  current = siteFromHash();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", refresh);
  } else {
    refresh();
  }

  window.SOMA = {
    site: function () { return current; },
    setSite: setSite,
    onSite: function (fn) { listeners.push(fn); },
    xlinks: xlinks,
    flash: flash,
    refresh: refresh,
    lang: lang,
    setLang: setLang
  };
})();
