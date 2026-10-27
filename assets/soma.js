/* Observatório SOMA — shared navigation bar and site deep links.

   The four demonstration sites carry the same id in every view (BR-PA-0001 …), so
   a site travels between pages in the URL fragment: dashboard.html#site=BR-PA-0001.
   Each page reads it on load, writes it back when the user picks a site, and asks
   this file for the links to the same site in the other views. */
(function () {
  var PAGES = [
    { key: "report",    href: "report.html",    en: "Report",    pt: "Relatório" },
    { key: "dashboard", href: "dashboard.html", en: "Dashboard", pt: "Painel" },
    { key: "map",       href: "map.html",       en: "Map",       pt: "Mapa" }
  ];
  var SITE_RE = /^BR-[A-Z]{2}-\d{4}$/;
  var current = null;
  var listeners = [];

  function lang() {
    try { if (localStorage.getItem("soma-lang") === "pt") return "pt"; } catch (e) {}
    return "en";
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
  function href(page, id) {
    return page + (id ? "#site=" + encodeURIComponent(id) : "");
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
      '<nav aria-label="' + (l === "pt" ? "Vistas" : "Views") + '">' +
      PAGES.map(function (p) {
        return '<a href="' + href(p.href, current) + '"' +
          (p.key === here ? ' aria-current="page"' : "") + ">" + p[l] + "</a>";
      }).join("") +
      "</nav>" +
      '<span class="soma-site"' + (current ? "" : " hidden") +
      ' title="' + (l === "pt" ? "Site selecionado" : "Selected site") + '">' +
      (current || "") + "</span>";
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
      return p.key !== skip;
    }).map(function (p) {
      return '<a href="' + href(p.href, id) + '">' + label[p.key][l] + " →</a>";
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
    document.addEventListener("DOMContentLoaded", renderBar);
  } else {
    renderBar();
  }

  window.SOMA = {
    site: function () { return current; },
    setSite: setSite,
    onSite: function (fn) { listeners.push(fn); },
    xlinks: xlinks,
    flash: flash,
    refresh: renderBar,
    lang: lang
  };
})();
