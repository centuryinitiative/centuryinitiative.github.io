---
title: Methodology
toc: true
---

```js
import {SCEN_COLOR, PROV_COLORS} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const P = data.params;
const years = data.meta.years;
const END = 2100;
const inRange = (y) => y <= END;
const seriesByScen = (obj, scale = 1) =>
  ["low", "mid", "high"].flatMap((s) =>
    years.map((y, i) => ({year: y, scen: s, v: obj[s][i] * scale})).filter((d) => inRange(d.year)));
const seriesByProv = (obj, provs, scale = 1) =>
  provs.flatMap((p) =>
    years.map((y, i) => ({year: y, prov: p, v: obj[p][i] * scale})).filter((d) => inRange(d.year)));
const AX = {background: "transparent", color: "#c7ccd4", fontSize: "12px"};
const SCEN_RANGE = ["low", "mid", "high"].map((s) => SCEN_COLOR[s]);
const capitalize = (s) => s[0].toUpperCase() + s.slice(1);
```

# Methodology

## The question, and the approach

The [Century Initiative](/en/) argues Canada should grow to 100 million people by 2100. This site takes that number seriously as a *demographic scenario* and asks what it implies for French in Canada and for Quebec's weight in the federation. To answer concretely rather than rhetorically, every figure on this site is driven by a single **agent-based demographic microsimulation** — not a spreadsheet of ratios, but a synthetic population that is grown, moved, and re-labeled one year at a time.

## The model

The population is stored as two parallel integer arrays: each simulated **agent** carries a **province** (one of 13) and a **home-language group** (Francophone, Anglophone, Allophone). One agent stands in for **`SCALE = 100`** real people, so the 1971 starting population of ≈21.6 million is about 216,000 agents; by 2100 the mid scenario carries on the order of a million. The model steps one year at a time from **1971 to 2100** (the data run to 2150), applying four processes in order:

<div class="eq eq--flow">state<sub>t+1</sub>&nbsp;=&nbsp;<b>Immigrate</b> ∘ <b>NaturalIncrease</b> ∘ <b>Migrate</b> ∘ <b>Transfer</b> ( state<sub>t</sub> )</div>

Every process is **stochastic**: outcomes are draws from probability distributions whose parameters come from the CSV files in `data/`. Running many agents lets the law of large numbers do the averaging, so aggregate shares come out smooth even though each agent's fate is a coin-flip.

### 1 · Language transfer

Within each province, agents can switch home-language group between years according to a province-specific **3×3 annual transition matrix** *M*<sup>(p)</sup>, where *M*<sup>(p)</sup><sub>ij</sub> is the probability that an agent currently in group *i* is in group *j* one year later (each row sums to 1). For an agent in province *p*, group *i*:

<div class="eq">Pr( group<sub>t+1</sub> = j&nbsp;|&nbsp;group<sub>t</sub> = i ) = M<sup>(p)</sup><sub>ij</sub>(t)</div>

The off-diagonal rates are small — a few per thousand per year (e.g. `allo→en` assimilation in the rest of Canada, `fr→en` outside Quebec) — but compounded over 75 years they matter. Quebec's matrix keeps French comparatively "sticky"; the rest of Canada's pulls allophones and francophones toward English.

### 2 · Interprovincial migration

Movement between provinces uses a **13×13 annual matrix** *A* whose diagonal *A*<sub>pp</sub> is the probability of staying put. An agent that leaves province *p* is distributed across destinations in proportion to the off-diagonal row, renormalised:

<div class="eq">Pr( move to q&nbsp;|&nbsp;leave p ) = A<sub>pq</sub> / Σ<sub>r ≠ p</sub> A<sub>pr</sub></div>

Language groups do not migrate identically. The base leave-probability (1 − *A*<sub>pp</sub>) is scaled by a **language multiplier** *λ*<sub>p,ℓ</sub>:

<div class="eq">Pr( leave p&nbsp;|&nbsp;group ℓ ) = min( 1,&nbsp; (1 − A<sub>pp</sub>) · λ<sub>p,ℓ</sub> )</div>

A multiplier below 1 makes a group "stickier" to its province — e.g. francophones are far less likely to leave Quebec than anglophones are — which is part of why French concentrates rather than disperses.

### 3 · Natural increase

The model does **not** track ages. Instead each province has a single **net provincial growth rate** *r*<sub>p</sub>(t) — births minus deaths *plus the net-migration / non-permanent-resident residual*, **recalibrated (2026) so the model reproduces the provincial census series** in `historical_provincial_population.csv` province by province (Ontario 16.2M, Alberta 5.0M, etc. in 2025). Each year the agent count in province *p* changes by:

<div class="eq">Δn<sub>p</sub> = round( n<sub>p</sub> · r<sub>p</sub>(t) )</div>

When Δ*n*<sub>p</sub> > 0, that many **new agents** are created and assigned a language by sampling the province's *current* language mix (children inherit the local distribution). When Δ*n*<sub>p</sub> < 0, agents are removed uniformly at random. Post-2025 the rate reverts to a below-replacement natural path, so late-century provincial growth depends almost entirely on immigration. (Folding net migration into this rate is a modeling shortcut: interprovincial moves are *also* simulated explicitly for their language selectivity — this rate carries the residual needed to hit each province's census total.)

### 4 · Immigration

Each year a volume *V*(t) of newcomers arrives. They are allocated to provinces by a time-varying **allocation vector** *α*(t) (which sums to 1), then assigned a language using **region-specific** francophone and anglophone shares — one set for Quebec, one for the rest of Canada (ROC) — with the allophone share taking the remainder:

<div class="eq">allophone share = 1 − f<sub>region</sub>(t) − e<sub>region</sub>(t)</div>

This is the central dilution engine. Only ≈2% of newcomers report French, they settle ≈8% in Quebec, and so the **effective francophone fraction of the whole immigration stream** sits far below the francophone share of the existing population. Pour a large, mostly non-francophone inflow into a 40-million base and grow it toward 100 million, and the francophone *share* falls by arithmetic even as the francophone *count* keeps rising.

## Model parameters

| Parameter | Symbol | Source file | Notes |
|---|---|---|---|
| Agent scale | `SCALE` = 100 | `canada_sim.py` | 1 agent = 100 people; lower = finer but slower |
| Provinces / territories | 13 | `initial_population_1971.csv` | NT & NU split; merged only in the Indigenous denominator |
| Language groups | 3 | — | Francophone, Anglophone, Allophone (home language) |
| Initial population | — | `initial_population_1971.csv` | 1971 counts + fr / allo shares per province |
| Language-transfer matrices | *M*<sup>(p)</sup>(t) | `language_transfer_matrices.csv` | province × year, 3×3, rows sum to 1 |
| Migration matrix | *A*(t) | `interprovincial_migration.csv` | 13×13 annual stay / move probabilities |
| Migration language multipliers | *λ*<sub>p,ℓ</sub> | `migration_language_multipliers.csv` | static; 1.0 = provincial average |
| Net provincial growth rate | *r*<sub>p</sub>(t) | `natural_increase.csv` | births−deaths + net-migration residual, fit to the provincial census series |
| Immigration volume | *V*(t) | `immigration_volume.csv` | annual landings; interpolated between anchors |
| Immigration composition | *f*, *e* | `immigration_composition.csv` | fr / en shares, separately for QC and ROC |
| Provincial allocation | *α*(t) | `immigration_provincial_allocation.csv` | share of landings to each province |

All time-varying inputs are given at a handful of **anchor years** and **linearly interpolated** in between, so a parameter like immigration volume is a piecewise-linear curve, e.g. 122k (1971) → 500k (2025) → 1.09M (2030) → 1.49M (2100) — the sustained ~1.1–1.5M-a-year intake a 100-million Canada actually requires once natural change is below replacement.

### Anchor years, by input

The table below lists the exact anchor years for each time-varying input. For the **province-varying** inputs (net growth, migration, provincial allocation), the *same* anchor years apply identically across all 13 provinces — each row is a year, with one column per province — and the provincial values at each historical anchor are taken from the cited source; **projection-year anchors (post-2025) are the modeller's assumptions**, not sourced values. Reference numbers `[n]` point to the [Sources](#sources) list below.

| Input | Historical / calibration anchors | Projection anchors | Interp. | Source |
|---|---|---|---|---|
| Provincial net-growth rate (`natural_increase.csv`) | 1971, 1981, 1991, 2001, 2011, 2021, 2024 | 2030, 2050, 2075, 2100, 2150 | linear | fit to StatCan provincial series [2] |
| Provincial populations, calibration target (`historical_provincial_population.csv`) | 1971, 1981, 1991, 2001, 2006, 2011, 2016, 2021, 2025 | — | — | Census [1]; Table 17-10-0009-01 (Q1 2025) [2] |
| Interprovincial migration (`interprovincial_migration.csv`) | 1971, 2000, 2024 | (held constant after 2024) | linear | Table 17-10-0015-01 [6] |
| Immigration volume (`immigration_volume.csv`) | 1971, 1975, 1980, …, 2020 (5-yr), then 2021, 2022, 2023, 2024, 2025 | 2030, 2040, 2050, 2075, 2100, 2150 | linear | IRCC / StatCan landings [3] |
| Provincial allocation of immigration (`immigration_provincial_allocation.csv`) | 1971, 1990, 2010, 2023 | 2030, 2040, 2050, 2100, 2150 | linear | IRCC by province of destination [3] |
| Immigration fr/en composition, QC & ROC (`immigration_composition.csv`) | 1971, 1981, 1990, 2001, 2003, 2011, 2015, 2016, 2021, 2022, 2025 | 2030, 2035, 2040, 2050, 2075, 2100, 2150 | linear | OQLF [4] / MIFI [5] (QC); IRCC targets [3] (ROC) |
| Language-transfer matrices (`language_transfer_matrices.csv`) | 1971, 1996, 2021 | 2050, 2100 | linear | StatCan Language Projections 89-657-X [8]; OQLF [4] |
| French-at-home share, calibration (`historical_francophone_share.csv`) | 1971, 1991, 1996, 2001, 2006, 2011, 2016, 2021 | — | — | Census [1] |
| Indigenous population anchors (`indigenous_population.csv`) | 1971, 1996, 2006, 2016, 2021 | projected via `indigenous_natural_increase.csv` | log-linear | Census [1] |

The fine-grain demographic inputs use their own period anchors — fertility and mortality at **1971, 2001, 2021, 2050, 2100** (with 1971/1991 historical for life tables) [9][10][11], emigration at **1971, 2001, 2021, 2050, 2100** [13] — interpolated the same way.

### Anchor values, by province

Because the anchor *years* are shared, the province-specific content is just the **value** at each anchor. Three province-varying tables are given below: the **calibration-target populations** the model is fit to (the actual census/estimate figures), the net provincial growth rate (§3), and the provincial allocation of immigration (§4). Cells show the calibrated (≤2025) or assumed (>2025) input at each anchor; the model linearly interpolates between them. Tables scroll horizontally on narrow screens.

```js
// Calibration-target provincial population, thousands of persons, straight from
// data/historical_provincial_population.csv via export_web_data.py.
// StatCan Census of Canada 1971–2021 [1]; Population estimates, quarterly,
// Table 17-10-0009-01, Q1 2025 (April 1 2025) [2]. Pre-1999 Nunavut is
// included in NT (exported as null, shown "—" for NU in 1971–1991).
const CALIB_ANCHORS = data.calibration.anchors;
const CALIB_POP = data.calibration.population_thousands;
const calibTable = () => html`<div style="overflow-x:auto"><table class="anchortab">
  <thead><tr><th>Prov.</th>${CALIB_ANCHORS.map((y) => html`<th>${y}</th>`)}</tr></thead>
  <tbody>${data.meta.provinces.map((p) => html`<tr>
    <td class="prov" title=${data.meta.province_names[p]}>${p}</td>
    ${CALIB_POP[p].map((v) => html`<td>${v == null ? "—" : v.toLocaleString("en-US", {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>`)}
  </tr>`)}</tbody>
</table></div>`;
```

<div class="anchorcap">Calibration-target provincial population — thousands of persons (<code>historical_provincial_population.csv</code>). StatCan Census 1971–2021 [1]; quarterly estimates Table 17-10-0009-01, Q1 2025 [2]. Pre-1999 Nunavut is included in NT.</div>

```js
calibTable()
```

Because the anchor *years* are shared, the two province-varying **input** parameters that shape the projection most directly are tabulated below — the net provincial growth rate (§3) and the provincial allocation of immigration (§4).

```js
const NI_ANCHORS = [1971, 1981, 1991, 2001, 2011, 2021, 2024, 2030, 2050, 2075, 2100];
const ALLOC_ANCHORS = [1971, 1990, 2010, 2023, 2030, 2040, 2050, 2100];
const anchorTable = (obj, anchors, scale, digits, {neg = false} = {}) => {
  const yi = (y) => years.indexOf(y);
  return html`<div style="overflow-x:auto"><table class="anchortab">
    <thead><tr><th>Prov.</th>${anchors.map((y) => html`<th class=${y > 2025 ? "proj" : ""}>${y}</th>`)}</tr></thead>
    <tbody>${data.meta.provinces.map((p) => html`<tr>
      <td class="prov" title=${data.meta.province_names[p]}>${p}</td>
      ${anchors.map((y) => {
        const i = yi(y);
        const v = i < 0 ? null : obj[p][i] * scale;
        return html`<td class=${neg && v < 0 ? "n" : ""}>${v == null ? "—" : v.toFixed(digits)}</td>`;
      })}</tr>`)}</tbody>
  </table></div>`;
};
```

<div class="anchorcap">Net provincial growth rate <b>r<sub>p</sub>(t)</b> — % per year (<code>natural_increase.csv</code>). Post-2025 anchors shaded.</div>

```js
anchorTable(P.natural_increase, NI_ANCHORS, 100, 2, {neg: true})
```

<div class="anchorcap">Provincial allocation of immigration <b>α(t)</b> — % of annual landings (<code>immigration_provincial_allocation.csv</code>). Post-2025 anchors shaded.</div>

```js
anchorTable(P.provincial_allocation, ALLOC_ANCHORS, 100, 1)
```

## Scenarios

The three headline scenarios share an **identical 1971–2025 calibration**, then diverge only in two post-2025 knobs applied on top of the base immigration inputs:

| Scenario | Volume × (post-2025) | Fr-share offset | ROC fr-share | Meaning for French |
|---|---|---|---|---|
| **Low** | 1.10 | −0.040 | 0.010 | Pessimistic — more volume, fewer francophones |
| **Mid** | 1.00 | 0.000 | 0.040 | Trend continuation; reaches ~100M by 2100 |
| **High** | 0.85 | +0.040 | 0.089 | Optimistic — less volume, sustained francophone selection |

Formally, `volume_multiplier_post2025` scales *V*(t) for t > 2025, and `fr_share_offset_post2025` is added to *f*<sub>region</sub>(t) (clamped to [0, 1]). The `roc_*` scenarios instead **pin** the rest-of-Canada francophone intake at a flat value (4%, 6%, 8%) to test the "francophone Africa" sensitivity. Note the counter-intuitive sign: *higher* total volume is *worse* for the French share, because it adds mostly non-francophones — so **"Low" is the pessimistic-for-French case**.

## Parameter diagnostics

The charts below plot the model's *inputs* directly — the curves that the four processes read each year. They are the levers; everything on the rest of the site is what happens when you pull them. All are drawn from the same `canada.json` bundle that feeds the story, and clamp to the 2100 horizon.

### Immigration volume

The single biggest driver. Historical landings through 2024, then a projected ramp calibrated so the mid scenario lands near 100 million by 2100. The scenario knob scales the post-2025 portion (Low ×1.10, High ×0.85).

```js
const volRows = seriesByScen(P.immigration_volume, 1 / 1000);
```

```js
Plot.plot({
  width, height: 300, marginRight: 66, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Annual landings (thousands)", grid: true},
  color: {domain: ["low", "mid", "high"], range: SCEN_RANGE, legend: true, tickFormat: capitalize},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(volRows, {x: "year", y: "v", z: "scen", stroke: "scen", strokeWidth: (d) => d.scen === "mid" ? 2.4 : 1.5}),
    Plot.tip(volRows, Plot.pointer({x: "year", y: "v", z: "scen", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${capitalize(d.scen)}\n${d.year}: ${d.v.toFixed(0)}k`}))
  ]
})
```

### The dilution engine: francophone fraction of the immigration stream

This is the mechanism behind the whole story. Weighting the Quebec and rest-of-Canada francophone intakes by where immigrants actually settle gives the **effective French share of all newcomers**. It sits far below French's ≈20% share of the existing population — so every year of immigration pulls the national French share down, by arithmetic, before any assimilation.

```js
const effRows = seriesByScen(P.effective_fr_fraction, 100);
```

```js
Plot.plot({
  width, height: 300, marginRight: 66, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "French, % of the immigration stream", grid: true, domain: [0, 22]},
  color: {domain: ["low", "mid", "high"], range: SCEN_RANGE, legend: true, tickFormat: capitalize},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(effRows, {x: "year", y: "v", z: "scen", stroke: "scen", strokeWidth: (d) => d.scen === "mid" ? 2.4 : 1.5}),
    Plot.tip(effRows, Plot.pointer({x: "year", y: "v", z: "scen", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${capitalize(d.scen)}\n${d.year}: ${d.v.toFixed(1)}%`}))
  ]
})
```

### Provincial allocation of immigration

Where newcomers land. Ontario, B.C. and Alberta take the lion's share; Quebec's slice (≈14% and drifting down) is well below its ≈22% of the population — the second reason a bigger Canada is a proportionally smaller Quebec.

```js
const allocProvs = ["ON", "QC", "BC", "AB", "MB", "SK"];
const allocRows = seriesByProv(P.provincial_allocation, allocProvs, 100);
```

```js
Plot.plot({
  width, height: 320, marginRight: 44, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Share of annual landings (%)", grid: true},
  color: {domain: allocProvs, range: allocProvs.map((p) => PROV_COLORS[p]), legend: true},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(allocRows, {x: "year", y: "v", z: "prov", stroke: "prov", strokeWidth: 1.8}),
    Plot.text(allocRows.filter((d) => d.year === END), {x: "year", y: "v", text: "prov", dx: 8, textAnchor: "start", fill: "prov", fontSize: 10}),
    Plot.tip(allocRows, Plot.pointer({x: "year", y: "v", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.prov}\n${d.year}: ${d.v.toFixed(1)}%`}))
  ]
})
```

### Natural increase

The recalibrated **net provincial growth rate** (births−deaths + net-migration residual), fit so the model reproduces each province's census population. The 2021→2025 spike is the immigration/NPR boom; it decays after 2025 back to a below-replacement path, so late-century provincial growth rests almost entirely on immigration. Provinces the raw migration matrix over-drains (the Prairies, Atlantic) carry a positive residual; Alberta carries a negative one.

```js
const niProvs = ["QC", "ON", "AB", "BC", "NB", "NL"];
const niRows = seriesByProv(P.natural_increase, niProvs, 100);
```

```js
Plot.plot({
  width, height: 320, marginRight: 44, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Net natural increase (%/yr)", grid: true},
  color: {domain: niProvs, range: niProvs.map((p) => PROV_COLORS[p]), legend: true},
  marks: [
    Plot.ruleY([0], {stroke: "#6b7280"}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(niRows, {x: "year", y: "v", z: "prov", stroke: "prov", strokeWidth: 1.8}),
    Plot.tip(niRows, Plot.pointer({x: "year", y: "v", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.prov}\n${d.year}: ${d.v.toFixed(2)}%/yr`}))
  ]
})
```

#### How the post-2025 nodes are set — and how far they can be sourced

Because *r*<sub>p</sub>(t) is a **net** rate — natural change *plus* the migration/NPR residual the model carries nowhere else — its projection anchors are built structurally, not read off a published table. Each node is:

<div class="eq"><b>r<sub>p</sub>(2030)</b> = [ 2021 structural level, <i>fitted</i> to the 2011→2021 census ] + [ ≈ −0.2 pts/decade below-replacement drift, <i>assumed</i> ]</div>

`calibrate_ni.py` fits the 2021 node to the census; `rebase_projection` then re-applies the original file's below-replacement *shape* onto that fitted base. So every province's projection carries an **empirical base** and an **assumed slope**. How far the resulting node can be tied to an external projection depends on which component dominates:

- **Natural-decline provinces (Quebec, Newfoundland & Labrador, New Brunswick).** The negative node reflects genuinely negative projected natural change. Corroborated: ISQ has Quebec deaths exceeding births since 2024 and projects **negative natural increase from 2027** [15]; StatCan's 2024-based projections show natural increase turning negative first in the **oldest provinces — the Atlantic region and Quebec** [14].
- **Alberta is the honest exception.** Its −2.6 %/yr node is **not** a demographic claim: StatCan estimates give Alberta the **youngest age structure and clearly positive** natural increase [16]. The negative rate is the calibration residual offsetting the model's explicit over-allocation of immigration/NPR to Alberta during the 2021–25 boom — a **bookkeeping offset, not projected natural decline**. Ontario and B.C. sit in between.
- **Small provinces with a positive residual (PE, SK, MB, NS).** The raw interprovincial-migration matrix over-drains these, so the net rate stays positive to hold their census totals. This too is a calibration residual, not a natural-increase forecast.

Projection nodes by province (%/yr), with the empirical 2021 base separated from the assumed drift:

| Prov | 2021 (fitted) | 2030 | 2050 | Dominant driver | External corroboration |
|---|---:|---:|---:|---|---|
| QC | −1.07 | −1.27 | −1.37 | natural decline | ISQ: neg. nat. increase from 2027 [15]; StatCan [14] |
| NL | −0.64 | −0.84 | −0.94 | natural decline + out-migration | StatCan: Atlantic nat. increase negative [14] |
| NB | −0.83 | −0.93 | −1.03 | natural decline + out-migration | StatCan [14] |
| ON | −0.49 | −0.69 | −0.79 | mixed — largely residual | (calibration residual) |
| BC | +0.09 | −0.11 | −0.21 | ~balanced residual | (calibration residual) |
| NS | +0.92 | +0.72 | +0.62 | over-drain residual | (calibration residual) |
| MB | +0.45 | +0.30 | +0.20 | over-drain residual | (calibration residual) |
| SK | +1.36 | +1.21 | +1.11 | over-drain residual | (calibration residual) |
| PE | +2.03 | +1.83 | +1.73 | over-drain residual | (calibration residual) |
| AB | −2.38 | −2.63 | −2.73 | post-boom NPR residual | AB nat. increase **positive** [16] — node is a bookkeeping offset |

Territories (YT, NT, NU) keep their small original positive rates. **Bottom line:** the *shape* (a steady post-2025 slide toward below-replacement) is grounded in ISQ [15] and StatCan [14]; the per-province *level* is a calibration residual, and for immigration-heavy provinces it must **not** be equated with projected natural increase.

### Language transfer: how "sticky" French is

The rate at which allophones shift to speaking English at home (`allo→en`, per thousand per year), for three provinces. It is an order of magnitude weaker inside **Quebec** than in Ontario or New Brunswick — the assimilation pull toward English is a rest-of-Canada phenomenon, and it is why French holds far better in Quebec than beyond it.

```js
const ltProvs = ["QC", "ON", "NB"];
const ltRows = ltProvs.flatMap((p) =>
  years.map((y, i) => ({year: y, prov: p, v: P.language_transfer[p].allo_en[i] * 1000})).filter((d) => inRange(d.year)));
```

```js
Plot.plot({
  width, height: 300, marginRight: 44, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "allophone → English (‰ per year)", grid: true},
  color: {domain: ltProvs, range: ltProvs.map((p) => PROV_COLORS[p]), legend: true},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(ltRows, {x: "year", y: "v", z: "prov", stroke: "prov", strokeWidth: 2}),
    Plot.tip(ltRows, Plot.pointer({x: "year", y: "v", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.prov}\n${d.year}: ${d.v.toFixed(1)}‰`}))
  ]
})
```

### Interprovincial migration multipliers

A static tweak: how much more or less likely each language group is to leave a given province, relative to that province's average (1.0). Note Quebec's column — francophones are strongly *stickier* (below 1) and anglophones far more mobile, which keeps French concentrated in Quebec rather than dispersing.

```js
const multProvs = data.meta.provinces;
const multRows = multProvs.flatMap((p) =>
  ["fr", "en", "allo"].map((l) => ({prov: p, lang: l, v: P.migration_multipliers[p][l]})));
```

```js
Plot.plot({
  width, height: 190, marginLeft: 52, marginBottom: 34, style: AX,
  x: {label: null, domain: multProvs},
  y: {label: null, domain: ["fr", "en", "allo"], tickFormat: (l) => ({fr: "Fr", en: "En", allo: "Allo"}[l])},
  color: {scheme: "RdYlGn", domain: [0.5, 1.5], legend: true, label: "Out-migration × (1.0 = provincial average)"},
  marks: [
    Plot.cell(multRows, {x: "prov", y: "lang", fill: "v"}),
    Plot.text(multRows, {x: "prov", y: "lang", text: (d) => d.v.toFixed(1), fontSize: 9, fill: "#111"})
  ]
})
```

## Calibration and projection

- **1971–2025** is a *calibration* window: inputs use empirical Statistics Canada figures (censuses and quarterly estimates), and the model is tuned to reproduce the historical record. It now tracks national population and the **provincial** census series (Table 17-10-0009-01, Q1 2025) closely — Ontario 16.2M, Quebec 9.1M, Alberta 5.0M — and national French share to about a point. (Quebec's French-at-home share *inside* Quebec is a separate, harder calibration and currently runs a few points low — see the caveats.)
- **2025–2100** is a *projection*: inputs extrapolate current trends. The mid scenario reaches **~100 million by 2100** (99.6M) — matching the Century Initiative's target, which is why we treat that target as a live scenario rather than a fantasy. Reaching it now requires ~1.1–1.5M immigrants a year, because below-replacement natural change no longer helps.

## Indigenous overlay

The Indigenous figures track two definitions — **identity** (First Nations + Métis + Inuit) and **mother tongue** (Indigenous first language) — as an overlay on the main simulation. Key choices:

- Provincial anchors are interpolated between census years and are **approximate**: they are calibrated to published national totals (≈312k in 1971 rising to ≈1.81M in 2021) and to known territorial concentrations, but not reconciled cell by cell.
- The denominator uses **real** provincial population, and **NT + Nunavut are merged** to avoid the 1999 territory-split artifact.
- Projection assumes fertility converges to the national **below-replacement** level: natural increase stays positive for a couple of decades on age-structure momentum, then turns negative — so the population peaks near mid-century and declines.

## Caveats worth stating plainly

- A projection to 2100 is an **illustration of assumptions**, not a forecast. Small changes to immigration volume or fertility compound over 75 years.
- Because the model carries no age structure, natural increase is a single net rate per province — it cannot capture momentum from a young or old age pyramid except insofar as that rate curve is drawn to.
- The apparent late-century *plateau* in Quebec's share is a **frozen transient**: it reflects the modeling choice to hold immigration volume roughly constant after 2050. Under a population-scaled immigration assumption the share would keep falling toward Quebec's ≈8% intake share.
- **Visible kinks track anchor years, not events.** Because every input is a piecewise-linear curve between a handful of anchor years (§Model parameters), the output can bend sharply wherever two segments meet. Quebec's *total population*, for example, appears to **plateau around 2030** — not because anything happens that year, but because its net-growth rate is anchored at roughly **+2.7%/yr in 2024 and −1.3%/yr in 2030 with no points between**. The interpolated descent crosses zero in the late 2020s, so for a few years the province's negative natural change (≈−125k/yr) almost exactly cancels its immigration inflow (≈+110k/yr); growth then resumes as the immigration ramp keeps climbing. The 2030 "elbow" is therefore an artifact of where the anchors sit — move or add anchors and it moves with them — so read these curves for their trend, not their year-by-year shape. The **direction** of that post-2025 QC anchor (natural change turning negative in the late 2020s) is not arbitrary: the Institut de la statistique du Québec already recorded deaths outnumbering births in Quebec in 2024–2025 and projects **negative natural increase from 2027 on** [15], and StatCan's official projections (Cat. 91-520-X) show Quebec's demographic weight declining through 2048 [14]. The model's **magnitude** (≈ −1.3 %/yr, steeper than those official projections) remains the modeller's own assumption, not a sourced figure.
- Language groups are **home language**, not ethnicity or ancestry. A trilingual household reporting English at home counts as anglophone here.
- The **population** trajectories are calibrated to the provincial census; the **language** dimension is calibrated more loosely. In particular the model's French-at-home share *inside Quebec* runs a few points below the census (≈69% vs ≈78% in 2021) and, after the 2026 net-growth recalibration made Quebec's natural change more negative, its projected in-Quebec French decline is on the steep side. Treat the Quebec-French curves as directional (French falling as a share) rather than precise levels.

## Sources

Every input file names its empirical basis in its header comment; this section collects them. Two honest qualifications up front: (a) the **1971–2025 calibration** values are drawn from the sources below, but (b) the **post-2025 projection** values are the modeller's *trend-continuation assumptions* built on top of them — not themselves sourced data — and several calibration parameters (language-transfer and migration rates, Indigenous provincial cells) are **stylised or approximate** fits to the cited studies rather than verbatim transcriptions. All links **accessed 8 July 2026**.

| Input (`data/…`) | What it sets | Source |
|---|---|---|
| `initial_population_1971.csv` | 1971 provincial populations + language shares | StatCan, 1971 Census of Canada (Cat. 92-715) [1] |
| `historical_provincial_population.csv` | provincial population 1971–2025 (calibration) | StatCan Census 1971–2021 [1]; Population estimates, quarterly, Table 17-10-0009-01 (Q1 2025) [2] |
| `historical_population.csv` | national population targets | StatCan Census [1]; quarterly estimates, Table 17-10-0009-01 [2] |
| `historical_francophone_share.csv` | French-at-home share (calibration) | StatCan Census 1971–2021, language spoken most often at home [1] |
| `immigration_volume.csv` | annual permanent-resident landings | IRCC landings data; Immigration Levels Plan & Annual Report to Parliament [3] |
| `immigration_composition.csv` | fr/en share of immigrants (QC vs ROC) | OQLF [4] / Quebec MIFI [5] (QC); IRCC francophone-immigration targets [3] (ROC) |
| `immigration_provincial_allocation.csv` | provincial share of landings | IRCC landings by province of intended destination [3] |
| `natural_increase.csv` | net provincial growth rate | Fitted to StatCan provincial population series, Table 17-10-0009-01 [2]; post-2025 below-replacement path corroborated by StatCan Population Projections (Cat. 91-520-X) [14] and, for Quebec, ISQ projections [15] |
| `interprovincial_migration.csv` | annual move probabilities | StatCan Table 17-10-0015-01, interprovincial migrants [6] |
| `migration_language_multipliers.csv` | language-conditional mobility | StatCan Census / IMDB language-mobility studies [1][7] |
| `language_transfer_matrices.csv` | annual language-shift rates | StatCan, Language Projections for Canada 2011–2036 (Cat. 89-657-X) [8]; OQLF [4] |
| `indigenous_population.csv` | Indigenous identity & mother-tongue anchors | StatCan Census 1971–2021 (Aboriginal identity; Indigenous mother tongue) [1] |
| `indigenous_natural_increase.csv` | post-2021 Indigenous natural increase | StatCan Indigenous population projections [1]; UN WPP 2022 convergence assumption [9] |
| `fg_age_sex_1971.csv` | 1971 age-sex structure | StatCan, 1971 Census (Cat. 92-715) [1] |
| `fg_fertility.csv` | age-specific fertility | StatCan Table 13-10-0418-01 [10]; UN WPP 2022 (projections) [9] |
| `fg_life_tables.csv` | mortality *q*(age, sex) | StatCan Life Tables 2018–2020 (Cat. 84-537-X) [11]; Human Mortality Database [12]; UN WPP 2022 [9] |
| `fg_emigration.csv` | emigration rates | StatCan Demographic Estimates Program (91-209-X) [13]; OECD |
| `fg_immigrant_age_sex.csv` | immigrant age-sex profile | StatCan IMDB [7]; IRCC annual reports [3]; UN WPP 2022 [9] |

**Reference links** (accessed 8 July 2026):

1. Statistics Canada — Census Program — <https://www12.statcan.gc.ca/census-recensement/index-eng.cfm>
2. StatCan Table 17-10-0009-01, *Population estimates, quarterly* — <https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901>
3. Immigration, Refugees and Citizenship Canada (IRCC) — *Immigration Levels Plan / Annual Report to Parliament* — <https://www.canada.ca/en/immigration-refugees-citizenship.html>
4. Office québécois de la langue française (OQLF) — <https://www.oqlf.gouv.qc.ca/>
5. Quebec — Ministère de l'Immigration, de la Francisation et de l'Intégration (MIFI) — <https://www.quebec.ca/en/immigration>
6. StatCan Table 17-10-0015-01, *Interprovincial migrants* — <https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710001501>
7. StatCan — Longitudinal Immigration Database (IMDB) — <https://www.statcan.gc.ca/en/topics-start/immigration_and_ethnocultural_diversity>
8. StatCan — *Language Projections for Canada, 2011 to 2036* (Cat. 89-657-X) — <https://www150.statcan.gc.ca/n1/en/catalogue/89-657-X>
9. United Nations — *World Population Prospects 2022* — <https://population.un.org/wpp/>
10. StatCan Table 13-10-0418-01, *Age-specific fertility rates* — <https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310041801>
11. StatCan — *Life Tables, Canada, Provinces and Territories* (Cat. 84-537-X) — <https://www150.statcan.gc.ca/n1/en/catalogue/84-537-X>
12. Human Mortality Database — <https://www.mortality.org/>
13. StatCan — *Demographic Estimates Program* (Cat. 91-209-X) — <https://www150.statcan.gc.ca/n1/en/catalogue/91-209-X>
14. StatCan — *Population Projections for Canada, Provinces and Territories* (Cat. 91-520-X) — <https://www150.statcan.gc.ca/n1/en/catalogue/91-520-X>
15. Institut de la statistique du Québec (ISQ) — *Population projections, Québec* (2021→2071; 2025 update) — <https://statistique.quebec.ca/en/document/population-projections-quebec>
16. StatCan Table 17-10-0008-01, *Estimates of the components of demographic growth, annual* (births, deaths, natural increase by province) — <https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000801>

Catalogue-number publications (e.g. 92-715, the 1971 Census) are identified by their StatCan catalogue number and reachable through the Census Program [1] and the StatCan catalogue. Where a header comment cites a value as "stylized," "approximate," or "illustrative," treat the source as the *calibration reference* for that parameter, not a cell-by-cell citation.

## Data

All inputs live in plain CSV files and the whole site runs off a single **185 KB** JSON export of the simulation — no backend, no database, no analytics.

The complete source — simulation code, input data, and this website — is available on GitHub at [github.com/centuryinitiative/centuryinitiative.github.io](https://github.com/centuryinitiative/centuryinitiative.github.io).

<style>
.eq {
  margin: 1.4rem 0; padding: 0.9rem 1.1rem;
  background: var(--theme-background-alt, #1a1d23);
  border: 1px solid color-mix(in srgb, currentColor 12%, transparent);
  border-left: 3px solid #3a7ebf; border-radius: 0 6px 6px 0;
  font-family: var(--serif, Georgia, "Times New Roman", serif);
  font-size: 1.08rem; line-height: 1.5; letter-spacing: 0.01em;
  overflow-x: auto; white-space: nowrap;
}
.eq sub, .eq sup { font-size: 0.72em; }
.eq b { font-weight: 600; font-style: normal; }
.eq--flow { font-family: inherit; }

.anchorcap {
  margin: 1.3rem 0 0.35rem; font-size: 0.9rem;
  color: var(--theme-foreground-muted, #9aa0a6);
}
.anchorcap code { font-size: 0.82em; }
.anchortab {
  border-collapse: collapse; font-size: 0.82rem;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.anchortab th, .anchortab td {
  padding: 3px 9px; text-align: right;
  border-bottom: 1px solid color-mix(in srgb, currentColor 10%, transparent);
}
.anchortab thead th { font-weight: 600; }
.anchortab thead th.proj { color: var(--theme-foreground-muted, #9aa0a6); font-weight: 400; }
.anchortab th:first-child, .anchortab td.prov {
  text-align: left; font-weight: 600; position: sticky; left: 0;
  background: var(--theme-background, #0e1117);
}
.anchortab tbody tr:hover td { background: color-mix(in srgb, currentColor 6%, transparent); }
.anchortab td.n { color: #e06a5a; }
</style>
