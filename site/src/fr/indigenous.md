---
title: Canada autochtone
toc: false
---

# Canada autochtone

Deux réalités très différentes se cachent sous le mot « autochtone » : l'**identité** (Premières Nations, Métis et Inuits — environ 5 % du Canada aujourd'hui) et la **langue maternelle** (les personnes dont la première langue est une langue autochtone — moins de 1 %, et en recul). La projection suit les deux.

```js
import {indigenousShareRows} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const {years, provinces} = data.meta;
const share = indigenousShareRows(data);
```

```js
const tidy = share.flatMap((d) => [
  {year: d.year, kind: "Identité", value: d.identity},
  {year: d.year, kind: "Langue maternelle", value: d.mothertongue}
]);
```

## Part de la population canadienne

L'identité culmine autour de 2021, puis fléchit : les gains passés liés à la reclassification sont considérés comme épuisés, la fécondité converge vers le niveau national (sous le seuil de remplacement) et l'immigration — entièrement non autochtone — dilue la part.

```js
Plot.plot({
  width,
  height: 420,
  marginLeft: 52,
  x: {label: null, tickFormat: "d"},
  y: {label: "Part du Canada (%)", grid: true, domain: [0, 6]},
  color: {domain: ["Identité", "Langue maternelle"], range: ["#c77dff", "#4ecdc4"], legend: true},
  marks: [
    Plot.line(tidy, {x: "year", y: "value", stroke: "kind", strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "4 4"}),
    Plot.tip(tidy, Plot.pointer({x: "year", y: "value", stroke: "kind", title: (d) => `${d.kind}\n${d.year} : ${d.value.toFixed(2)}%`}))
  ]
})
```

## Population absolue — un pic de momentum

Même avec une fécondité sous le seuil de remplacement, la population selon l'identité continue de croître pendant quelques décennies, portée par la jeunesse de sa structure d'âge ; elle culmine vers le milieu du siècle, puis décline.

```js
const sum = (obj) => provinces.map((p) => obj[p]).reduce((a, b) => a.map((x, i) => x + b[i]));
const id = sum(data.indigenous.identity), mt = sum(data.indigenous.mothertongue);
const absRows = years.flatMap((y, i) => [
  {year: y, kind: "Identité", pop: id[i] / 1e6},
  {year: y, kind: "Langue maternelle", pop: mt[i] / 1e6}
]);
```

```js
Plot.plot({
  width,
  height: 380,
  marginLeft: 52,
  x: {label: null, tickFormat: "d"},
  y: {label: "Population (millions)", grid: true},
  color: {domain: ["Identité", "Langue maternelle"], range: ["#c77dff", "#4ecdc4"], legend: true},
  marks: [
    Plot.line(absRows, {x: "year", y: "pop", stroke: "kind", strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "4 4"})
  ]
})
```

<div class="note">
Les points d'ancrage provinciaux sont approximatifs et calibrés sur les totaux nationaux publiés — voir la <a href="/fr/methodology">Méthodologie</a>. Les territoires (T.N.-O. + Nunavut) sont fusionnés là où un dénominateur par province serait autrement instable.
</div>

<style>
.note { margin: 2rem 0; padding: 1rem 1.25rem; border-left: 3px solid #c77dff; background: var(--theme-background-alt); border-radius: 0 6px 6px 0; }
</style>
