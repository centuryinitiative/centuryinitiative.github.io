// Shared helpers + palette for the Canada 2150 site.
// Pure functions only (no FileAttachment) — pages load the data and pass it in.

export const LANG_COLORS = { fr: "#3a7ebf", en: "#e07b39", allo: "#3abf6e" };
export const LANG_LABEL = { fr: "Francophone", en: "Anglophone", allo: "Allophone" };
export const LANG_LABEL_FR = { fr: "Francophones", en: "Anglophones", allo: "Allophones" };

export const SCEN_COLOR = { low: "#e07b39", mid: "#3a7ebf", high: "#3abf6e" };
export const SCEN_LABEL = { low: "Low", mid: "Mid", high: "High" };
export const SCEN_LABEL_FR = { low: "Faible", mid: "Intermédiaire", high: "Élevé" };

// French full names for province codes (English names live in canada.json's meta).
export const PROV_FR = {
  NL: "Terre-Neuve-et-Labrador", PE: "Île-du-Prince-Édouard", NS: "Nouvelle-Écosse",
  NB: "Nouveau-Brunswick", QC: "Québec", ON: "Ontario", MB: "Manitoba",
  SK: "Saskatchewan", AB: "Alberta", BC: "Colombie-Britannique", YT: "Yukon",
  NT: "Territoires du Nord-Ouest", NU: "Nunavut"
};

export const PROV_COLORS = {
  NL: "#4e8ef7", PE: "#a55bf5", NS: "#f5a623", NB: "#50c878",
  QC: "#3a7ebf", ON: "#d62828", MB: "#f77f00", SK: "#2ec4b6",
  AB: "#e63946", BC: "#457b9d", YT: "#b5838d", NT: "#6b4226", NU: "#8a5a9e"
};

// fr+en+allo for one province → array over years
export function provTotal(series, prov) {
  const s = series[prov];
  return s.fr.map((_, i) => s.fr[i] + s.en[i] + s.allo[i]);
}

// national total per year across all provinces
export function nationalTotal(series, provinces) {
  return provinces
    .map((p) => provTotal(series, p))
    .reduce((a, b) => a.map((x, i) => x + b[i]));
}

// national total for one language per year
export function nationalLang(series, provinces, lang) {
  return provinces
    .map((p) => series[p][lang])
    .reduce((a, b) => a.map((x, i) => x + b[i]));
}

// Quebec share of Canada (%) per year, tidy rows for a given scenario
export function qcShareRows(data, scenario) {
  const { years, provinces } = data.meta;
  const s = data.series[scenario];
  const qc = provTotal(s, "QC");
  const nat = nationalTotal(s, provinces);
  return years.map((year, i) => ({ year, scenario, share: (100 * qc[i]) / nat[i] }));
}

// Quebec share band across low/high with mid line: {year, lo, hi, mid}
export function qcShareBand(data) {
  const { years } = data.meta;
  const rows = Object.fromEntries(
    data.meta.scenarios.map((sc) => [sc, qcShareRows(data, sc)])
  );
  return years.map((year, i) => ({
    year,
    lo: Math.min(rows.low[i].share, rows.high[i].share),
    hi: Math.max(rows.low[i].share, rows.high[i].share),
    mid: rows.mid[i].share
  }));
}

// National population by language (tidy) for a scenario, in millions
export function nationalLangRows(data, scenario) {
  const { years, provinces, languages } = data.meta;
  const s = data.series[scenario];
  const out = [];
  for (const lang of languages) {
    const arr = nationalLang(s, provinces, lang);
    years.forEach((year, i) => out.push({ year, lang, label: LANG_LABEL[lang], pop: arr[i] / 1e6 }));
  }
  return out;
}

// Province totals (tidy) for a scenario, in millions
export function provinceRows(data, scenario) {
  const { years, provinces, province_names } = data.meta;
  const s = data.series[scenario];
  const out = [];
  for (const p of provinces) {
    const arr = provTotal(s, p);
    years.forEach((year, i) => out.push({ year, prov: p, name: province_names[p], pop: arr[i] / 1e6 }));
  }
  return out;
}

// Indigenous national share (%) per year: {year, identity, mothertongue}
export function indigenousShareRows(data) {
  const { years, provinces } = data.meta;
  const ind = data.indigenous;
  const sum = (obj) => provinces.map((p) => obj[p]).reduce((a, b) => a.map((x, i) => x + b[i]));
  const id = sum(ind.identity), mt = sum(ind.mothertongue), den = sum(ind.denominator);
  return years.map((year, i) => ({
    year,
    identity: (100 * id[i]) / den[i],
    mothertongue: (100 * mt[i]) / den[i]
  }));
}

// value at a given year from tidy [{year, ...}] rows
export function atYear(rows, year, key) {
  const r = rows.find((d) => d.year === year);
  return r ? r[key] : undefined;
}

export const fmtPct = (x) => `${x.toFixed(1)}%`;
export const fmtM = (x) => `${(x / 1e6).toFixed(1)}M`;

// value per province code at a given year index, for the map hero
export function valueByCode(data, scenario, metric, i) {
  const s = data.series[scenario];
  const m = new Map();
  for (const p of data.meta.provinces) {
    const tot = s[p].fr[i] + s[p].en[i] + s[p].allo[i];
    let v;
    if (metric === "pop") v = tot;
    else if (metric === "frshare") v = tot ? (100 * s[p].fr[i]) / tot : 0;
    else if (metric === "alloshare") v = tot ? (100 * s[p].allo[i]) / tot : 0;
    else v = tot;
    m.set(p, v);
  }
  return m;
}

// ---------------------------------------------------------------------------
// Animated "French across North America" map (blue = French, red = the rest).
// Colour intensity = % of home-language French. Canadian provinces animate from
// the model (mid scenario); US states / Central America are static context using
// approximate census French-at-home shares (the model does not project them).
//
// Receives `d3` and `invalidation` from the caller so lib.js stays import-free.
// Returns a DOM node (two panes: full continent + a NE zoom) that auto-plays
// 1971→END on a loop, interpolating between years. Click to pause/resume.
// ---------------------------------------------------------------------------
export function animatedFrenchMap({d3, geo, series, years, END, width, invalidation, labels = {}}) {
  const iEnd = years.indexOf(END);
  const n = iEnd + 1;
  const START = years[0];

  const RED = "#d64550";      // 0% French
  const BLUE = "#2f7ec4";     // 100% French  (matches the site's fr accent)
  const ramp = d3.interpolateLab(RED, BLUE);
  const color = (pct) => ramp(Math.max(0, Math.min(1, pct / 100)));

  // Only Québec and New Brunswick carry the live francophone-share colour; the
  // whole rest of the continent (all other provinces, every US state, Mexico) is
  // one uniform red so the two French provinces are the only thing that stands out.
  const HILITE = new Set(["QC", "NB"]);
  const REST = color(0);

  // Per-feature French-share series: an array (animated) or a number (static).
  const share = new Map();
  for (const f of geo.features) {
    const p = f.properties;
    if (p.kind === "ca" && series[p.code]) {
      const s = series[p.code];
      const arr = new Float64Array(n);
      for (let i = 0; i < n; i++) {
        const tot = s.fr[i] + s.en[i] + s.allo[i];
        arr[i] = tot ? (100 * s.fr[i]) / tot : 0;
      }
      share.set(p.code, arr);
    } else {
      share.set(p.code, p.frstatic ?? 0);
    }
  }
  // Fractional-year lookup so motion is smooth between annual data points.
  const shareAt = (f, i0, i1, t) => {
    const v = share.get(f.properties.code);
    if (typeof v === "number") return v;
    return v[i0] * (1 - t) + v[i1] * t;
  };

  // ---- layout ----
  const wide = width >= 760;
  const gap = 14;
  const wMain = wide ? Math.round((width - gap) * 0.60) : width;
  const hMain = wide ? Math.round(wMain * 0.74) : Math.round(width * 0.62);
  const wIn = wide ? width - gap - wMain : width;
  const hIn = wide ? hMain : Math.round(width * 0.62);

  // ---- projections ----
  // Equal-area conic (Albers-style): stable across the full 14°N–83°N span,
  // unlike conic-conformal which diverges near the pole.
  const projMain = d3.geoConicEqualArea().rotate([100, 0]).center([0, 52]).parallels([20, 60])
    .fitSize([wMain, hMain], geo);
  // NE zoom: fit to the real northeastern features (Quebec, the Maritimes and
  // New England) — fitSize on a FeatureCollection is reliable, unlike fitting a
  // bare lat/lon rectangle, whose interpolated edges throw the scale off.
  const NE_CODES = new Set(["QC", "NB", "NS", "PE", "US-Maine", "US-New Hampshire",
    "US-Vermont", "US-Massachusetts", "US-Connecticut", "US-Rhode Island", "US-New York"]);
  const neFocus = {type: "FeatureCollection",
    features: geo.features.filter((f) => NE_CODES.has(f.properties.code))};
  // Dashed rectangle drawn on the main pane to mark the zoom.
  const neBox = {type: "Polygon", coordinates: [[[-83, 41], [-58, 41], [-58, 53], [-83, 53], [-83, 41]]]};
  const projIn = d3.geoConicEqualArea().rotate([71, 0]).parallels([43, 50])
    .fitSize([wIn - 12, hIn - 12], neFocus);

  // Every feature is drawn identically (same stroke, full opacity) so the only
  // thing that varies is the fill — and only Québec/NB carry a non-red fill.
  // ---- one pane (svg + coloured paths), returns {svg, paths} ----
  function pane(proj, w, h, extraBox) {
    const path = d3.geoPath(proj);
    const svg = d3.create("svg")
      .attr("viewBox", `0 0 ${w} ${h}`)
      .attr("width", w).attr("height", h)
      .attr("style", "max-width:100%;height:auto;display:block;background:#0e1117;border-radius:8px;overflow:hidden");
    const paths = svg.append("g").selectAll("path").data(geo.features).join("path")
      .attr("d", path)
      .attr("stroke", "#0b0e13").attr("stroke-width", 0.6);
    if (extraBox) {
      svg.append("path").datum(neBox).attr("d", path)
        .attr("fill", "none").attr("stroke", "#e8eaed").attr("stroke-width", 1)
        .attr("stroke-dasharray", "4 3").attr("stroke-opacity", 0.55);
    }
    return {svg, paths};
  }

  const A = pane(projMain, wMain, hMain, true);
  const B = pane(projIn, wIn, hIn, false);

  // ---- live francophone-% callouts for Québec & New Brunswick (zoom pane) ----
  // A dot on the province + a short leader tick to a label whose % updates each
  // frame. Anchors are geographic so they track the projection.
  const CALLOUTS = [
    {code: "QC", name: labels.qc || "Québec", at: [-72, 48],    dx: 0,  dy: -20, anchor: "middle"},
    {code: "NB", name: labels.nb || "N.B.",   at: [-66.3, 46.3], dx: 52, dy: 30,  anchor: "start"}
  ];
  const gAnn = B.svg.append("g").attr("class", "namap__ann").attr("pointer-events", "none");
  const annEls = CALLOUTS.map((c) => {
    const feat = geo.features.find((f) => f.properties.code === c.code);
    const [mx, my] = projIn(c.at);
    const lx = mx + c.dx, ly = my + c.dy;
    gAnn.append("line").attr("x1", mx).attr("y1", my).attr("x2", lx).attr("y2", ly)
      .attr("stroke", "#e8eaed").attr("stroke-width", 1.1).attr("stroke-opacity", 0.8);
    gAnn.append("circle").attr("cx", mx).attr("cy", my).attr("r", 3.6)
      .attr("fill", "#e8eaed").attr("stroke", "#0b0e13").attr("stroke-width", 1);
    const text = gAnn.append("text").attr("x", lx).attr("y", ly).attr("dy", "0.32em")
      .attr("text-anchor", c.anchor)
      .attr("style", "paint-order:stroke;stroke:#0b0e13;stroke-width:4px;fill:#fff;" +
        "font:800 20px system-ui,-apple-system,sans-serif;font-variant-numeric:tabular-nums");
    return {feat, name: c.name, text};
  });

  // ---- year label + hint overlays ----
  const yearEl = document.createElement("div");
  yearEl.className = "namap__year";
  const hintEl = document.createElement("div");
  hintEl.className = "namap__hint";
  hintEl.textContent = labels.zoom || "Zoom: Québec · New England · Ontario · N.B.";

  // ---- container ----
  const root = d3.create("div").attr("class", "namap");
  const panes = root.append("div").attr("class", "namap__panes" + (wide ? "" : " namap__panes--stack"));
  const paneA = panes.append("div").attr("class", "namap__pane namap__pane--main");
  paneA.node().appendChild(yearEl);
  paneA.node().appendChild(A.svg.node());
  const paneB = panes.append("div").attr("class", "namap__pane namap__pane--inset");
  paneB.node().appendChild(hintEl);
  paneB.node().appendChild(B.svg.node());

  // legend (red → blue gradient)
  const legend = root.append("div").attr("class", "namap__legend");
  legend.html(
    `<span>${labels.lessFr || "less French"}</span>` +
    `<span class="namap__bar"></span>` +
    `<span>${labels.moreFr || "more French"}</span>`
  );
  legend.select(".namap__bar").style("background",
    `linear-gradient(90deg, ${color(0)}, ${color(25)}, ${color(50)}, ${color(75)}, ${color(100)})`);

  // ---- animation ----
  const SPEED = 9;            // years per second
  let raf, t0, paused = false, pausedAt = 0;
  function draw(f) {                          // f = fractional year index [0, n-1]
    const i0 = Math.floor(f), i1 = Math.min(i0 + 1, iEnd), t = f - i0;
    const fill = (d) => HILITE.has(d.properties.code) ? color(shareAt(d, i0, i1, t)) : REST;
    A.paths.attr("fill", fill);
    B.paths.attr("fill", fill);
    for (const a of annEls) a.text.text(`${a.name} ${shareAt(a.feat, i0, i1, t).toFixed(0)}%`);
    yearEl.textContent = Math.round(START + f);
  }
  function tick(now) {
    if (!t0) t0 = now;
    const f = ((now - t0) / 1000 * SPEED) % n;
    draw(f);
    raf = requestAnimationFrame(tick);
  }
  draw(0);
  raf = requestAnimationFrame(tick);
  root.node().addEventListener("click", () => {
    paused = !paused;
    if (paused) { cancelAnimationFrame(raf); pausedAt = performance.now() - t0; }
    else { t0 = performance.now() - pausedAt; raf = requestAnimationFrame(tick); }
    root.classed("is-paused", paused);
  });
  invalidation?.then(() => cancelAnimationFrame(raf));

  return root.node();
}

// metric display config for the hero map
export const METRICS = {
  pop:      { label: "Population",        scheme: "turbo",   type: "log",    domain: [5e4, 3.2e7], fmt: (v) => `${(v / 1e6).toFixed(2)}M` },
  frshare:  { label: "Francophone share", scheme: "YlGnBu",  type: "linear", domain: [0, 85],      fmt: (v) => `${v.toFixed(1)}%` },
  alloshare:{ label: "Allophone share",   scheme: "PuRd",    type: "linear", domain: [0, 60],      fmt: (v) => `${v.toFixed(1)}%` }
};
