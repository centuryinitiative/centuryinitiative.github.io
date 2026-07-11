---
title: Indigenous Canada
toc: false
---

# Indigenous Canada

Two very different stories sit under the word "Indigenous": **identity** (First Nations, Métis and Inuit — about 5% of Canada today) and **mother tongue** (people whose first language is an Indigenous language — under 1%, and falling). The projection tracks both.

```js
import {indigenousShareRows} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const {years, provinces} = data.meta;
const share = indigenousShareRows(data);
```

```js
const tidy = share.flatMap((d) => [
  {year: d.year, kind: "Identity", value: d.identity},
  {year: d.year, kind: "Mother tongue", value: d.mothertongue}
]);
```

## Share of Canada's population

Identity climbs to a peak around 2021, then eases: past reclassification gains are treated as spent, fertility converges toward the (below-replacement) national level, and immigration — all non-Indigenous — dilutes the share.

```js
Plot.plot({
  width,
  height: 420,
  marginLeft: 52,
  x: {label: null, tickFormat: "d"},
  y: {label: "Share of Canada (%)", grid: true, domain: [0, 6]},
  color: {domain: ["Identity", "Mother tongue"], range: ["#c77dff", "#4ecdc4"], legend: true},
  marks: [
    Plot.line(tidy, {x: "year", y: "value", stroke: "kind", strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "4 4"}),
    Plot.tip(tidy, Plot.pointer({x: "year", y: "value", stroke: "kind", title: (d) => `${d.kind}\n${d.year}: ${d.value.toFixed(2)}%`}))
  ]
})
```

## Absolute population — a momentum peak

Even with below-replacement fertility, the identity population keeps growing for a few decades on the momentum of a young age structure, peaks near mid-century, then declines.

```js
const sum = (obj) => provinces.map((p) => obj[p]).reduce((a, b) => a.map((x, i) => x + b[i]));
const id = sum(data.indigenous.identity), mt = sum(data.indigenous.mothertongue);
const absRows = years.flatMap((y, i) => [
  {year: y, kind: "Identity", pop: id[i] / 1e6},
  {year: y, kind: "Mother tongue", pop: mt[i] / 1e6}
]);
```

```js
Plot.plot({
  width,
  height: 380,
  marginLeft: 52,
  x: {label: null, tickFormat: "d"},
  y: {label: "Population (millions)", grid: true},
  color: {domain: ["Identity", "Mother tongue"], range: ["#c77dff", "#4ecdc4"], legend: true},
  marks: [
    Plot.line(absRows, {x: "year", y: "pop", stroke: "kind", strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "4 4"})
  ]
})
```

<div class="note">
Provincial anchors are approximate and calibrated to published national totals — see the <a href="/en/methodology">Methodology</a>. The territories (NT + Nunavut) are merged where a per-province denominator would otherwise be unstable.
</div>

<style>
.note { margin: 2rem 0; padding: 1rem 1.25rem; border-left: 3px solid #c77dff; background: var(--theme-background-alt); border-radius: 0 6px 6px 0; }
</style>
