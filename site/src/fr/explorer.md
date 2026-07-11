---
title: Explorateur
toc: false
---

# Explorateur

Composez votre propre vue. Choisissez un scénario, une mesure, puis les provinces ou territoires à comparer.

```js
import {provTotal, nationalTotal, PROV_COLORS, PROV_FR, SCEN_LABEL_FR} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const {years, provinces, province_names, scenarios} = data.meta;
```

```js
const scenario = view(Inputs.radio(scenarios, {value: "mid", label: "Scénario", format: (s) => SCEN_LABEL_FR[s]}));
const metric = view(Inputs.select(
  new Map([["Population (millions)", "pop"], ["Part du Canada (%)", "share"], ["Part francophone de la province (%)", "frshare"]]),
  {label: "Mesure", value: "pop"}
));
const picked = view(Inputs.checkbox(provinces, {
  label: "Provinces",
  value: ["QC", "ON", "AB", "BC"],
  format: (p) => PROV_FR[p]
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
    rows.push({year, prov: p, name: PROV_FR[p], value});
  });
}
const yLabel = metric === "pop" ? "Population (millions)"
  : metric === "share" ? "Part du Canada (%)" : "Part francophone (%)";
```

```js
Plot.plot({
  width,
  height: 480,
  marginLeft: 56,
  marginRight: 90,
  x: {label: null, tickFormat: "d"},
  y: {label: yLabel, grid: true},
  color: {domain: picked, range: picked.map((p) => PROV_COLORS[p]), legend: true, tickFormat: (p) => PROV_FR[p]},
  marks: [
    Plot.line(rows, {x: "year", y: "value", z: "prov", stroke: "prov", strokeWidth: 1.8}),
    Plot.text(rows.filter((d) => d.year === 2150), {x: "year", y: "value", text: "prov", dx: 8, textAnchor: "start", fill: "prov", fontSize: 10}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "4 4"}),
    Plot.tip(rows, Plot.pointer({x: "year", y: "value", z: "prov", title: (d) => `${d.name}\n${d.year} : ${d.value.toFixed(metric === "pop" ? 2 : 1)}${metric === "pop" ? "M" : "%"}`}))
  ]
})
```

<div class="note">
Tout est calculé côté client à partir d'un seul fichier de données de 185&nbsp;Ko — sans serveur, sans pistage. Les valeurs proviennent de la même simulation à base d'agents décrite dans la <a href="/fr/methodology">Méthodologie</a>.
</div>

<style>
.note { margin: 2rem 0; padding: 1rem 1.25rem; border-left: 3px solid var(--theme-foreground-focus); background: var(--theme-background-alt); border-radius: 0 6px 6px 0; }
</style>
