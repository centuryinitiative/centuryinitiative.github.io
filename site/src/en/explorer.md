---
title: Explorer
toc: false
---

# Explorer

Build your own view. Pick a scenario, a metric, and the provinces or territories you want to compare.

```js
import {provTotal, nationalTotal, PROV_COLORS, valueByCode, METRICS} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const geo = await FileAttachment("../data/canada-provinces.geojson").json();
const {years, provinces, province_names, scenarios} = data.meta;
const END = 2100;
```

```js
const scenario = view(Inputs.radio(scenarios, {value: "mid", label: "Scenario", format: (s) => s[0].toUpperCase() + s.slice(1)}));
const metric = view(Inputs.select(
  new Map([["Population (millions)", "pop"], ["Share of Canada (%)", "share"], ["Francophone share of province (%)", "frshare"]]),
  {label: "Metric", value: "pop"}
));
const picked = view(Inputs.checkbox(provinces, {
  label: "Provinces",
  value: ["QC", "ON", "AB", "BC"],
  format: (p) => province_names[p]
}));
```

```js
const s = data.series[scenario];
const nat = nationalTotal(s, provinces);
const rows = [];
for (const p of picked) {
  const tot = provTotal(s, p);
  years.forEach((year, i) => {
    let value;
    if (metric === "pop") value = tot[i] / 1e6;
    else if (metric === "share") value = (100 * tot[i]) / nat[i];
    else value = (100 * s[p].fr[i]) / tot[i];
    rows.push({year, prov: p, name: province_names[p], value});
  });
}
const yLabel = metric === "pop" ? "Population (millions)"
  : metric === "share" ? "Share of Canada (%)" : "Francophone share (%)";
```

```js
Plot.plot({
  width,
  height: 480,
  marginLeft: 56,
  marginRight: 90,
  x: {label: null, tickFormat: "d"},
  y: {label: yLabel, grid: true},
  color: {domain: picked, range: picked.map((p) => PROV_COLORS[p]), legend: true, tickFormat: (p) => province_names[p]},
  marks: [
    Plot.line(rows, {x: "year", y: "value", z: "prov", stroke: "prov", strokeWidth: 1.8}),
    Plot.text(rows.filter((d) => d.year === 2150), {x: "year", y: "value", text: "prov", dx: 8, textAnchor: "start", fill: "prov", fontSize: 10}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "4 4"}),
    Plot.tip(rows, Plot.pointer({x: "year", y: "value", z: "prov", title: (d) => `${d.name}\n${d.year}: ${d.value.toFixed(metric === "pop" ? 2 : 1)}${metric === "pop" ? "M" : "%"}`}))
  ]
})
```

## The map, any year to 2100

```js
const mapMetric = view(Inputs.radio(
  new Map([["Population", "pop"], ["Francophone share", "frshare"], ["Allophone share", "alloshare"]]),
  {value: "frshare", label: "Metric"}
));
```

```js
const yearInput = Inputs.range([1971, END], {step: 1, value: 1971, width: 320});
yearInput.querySelector("input").style.width = "min(320px, 70vw)";
const mapYear = Generators.input(yearInput);
```

```js
const i = years.indexOf(Math.min(Math.round(mapYear), END));
const vals = valueByCode(data, "mid", mapMetric, i);
const cfg = METRICS[mapMetric];
```

<div class="mapwrap">
  <div class="mapyear">${Math.round(mapYear)}</div>
  <div class="mapscrub">${yearInput}</div>

```js
Plot.plot({
  width,
  height: width < 560 ? 400 : 520,
  marginLeft: 0, marginRight: 0,
  projection: {type: "conic-conformal", domain: geo, rotate: [96, 0], parallels: [49, 77]},
  color: {
    type: cfg.type, scheme: cfg.scheme, domain: cfg.domain, clamp: true,
    legend: true, label: cfg.label, tickFormat: mapMetric === "pop" ? "~s" : ((d) => d + "%")
  },
  marks: [
    Plot.geo(geo, {
      fill: (d) => vals.get(d.properties.code),
      stroke: "#0e1117", strokeWidth: 0.8,
      title: (d) => `${d.properties.name}\n${cfg.label}: ${cfg.fmt(vals.get(d.properties.code))}`,
      tip: true
    })
  ]
})
```

</div>

<p class="caption">Mid scenario. Population is on a log scale — watch Ontario, Alberta and British Columbia ignite while the Atlantic stays dim; switch to <em>Francophone share</em> and Quebec glows alone against a fading country.</p>

<div class="note">
Everything here is client-side over a single 185&nbsp;KB data file — no server, no tracking. Values come from the same agent-based simulation described in the <a href="/en/methodology">Methodology</a>.
</div>

<style>
.note { margin: 2rem 0; padding: 1rem 1.25rem; border-left: 3px solid var(--theme-foreground-focus); background: var(--theme-background-alt); border-radius: 0 6px 6px 0; }
.mapwrap { position: relative; margin-top: 1rem; }
.mapyear { position: absolute; top: 0; left: 4px; z-index: 2; pointer-events: none;
  font-size: clamp(3rem, 10vw, 7rem); font-weight: 800; line-height: 0.85;
  letter-spacing: -0.05em; color: var(--theme-foreground); opacity: 0.12; font-variant-numeric: tabular-nums; }
.mapscrub { position: absolute; top: 8px; right: 4px; z-index: 2; }
.caption { color: var(--theme-foreground-muted); font-size: 0.9rem; margin: 1rem 0 0; line-height: 1.5; }
</style>
