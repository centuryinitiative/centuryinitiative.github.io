---
title: The story
toc: false
header: false
sidebar: false
---

```js
// Floating language switch (this page hides the global header).
{
  const isEn = /^\/en(\/|$)/.test(location.pathname);
  const rest = location.pathname.replace(/^\/(fr|en)/, "") || "/";
  const link = (l, on) => `<a href="/${l}${rest}" class="${on ? "on" : ""}" onclick="localStorage.setItem('lang','${l}')">${l.toUpperCase()}</a>`;
  const el = document.createElement("div");
  el.className = "storyswitch";
  el.innerHTML = link("fr", !isEn) + '<span>|</span>' + link("en", isEn);
  document.body.appendChild(el);
  invalidation.then(() => el.remove());
}
```

```js
import {
  nationalLang, provinceRows, nationalTotal, provTotal, qcShareBand,
  valueByCode, METRICS, LANG_COLORS, PROV_COLORS, animatedFrenchMap
} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const geo = await FileAttachment("../data/canada-provinces.geojson").json();
const naGeo = await FileAttachment("../data/north-america.geojson").json();
const {years, provinces, province_names, scenarios} = data.meta;
const END = 2100;                       // the horizon this story is about
const iEnd = years.indexOf(END);
```

```js
// One shared observer: a video plays only while its act is on screen.
const _vObs = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) e.target.play?.().catch(() => {});
    else e.target.pause?.();
  }
}, {threshold: 0.2});
invalidation.then(() => _vObs.disconnect());

// Build a full-bleed <video> from two FileAttachments (poster + clip).
// On mobile a fullscreen button is overlaid so users can tap to expand.
function mkVideo(mp4, jpg) {
  const v = document.createElement("video");
  v.muted = true; v.loop = true; v.playsInline = true; v.preload = "metadata";
  v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
  v.className = "act__video";
  Promise.all([mp4.href, jpg.href]).then(([m, p]) => { v.poster = p; v.src = m; });
  _vObs.observe(v);
  const btn = document.createElement("button");
  btn.className = "act__fs-btn";
  btn.setAttribute("aria-label", "Fullscreen");
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>`;
  btn.addEventListener("click", () => {
    if (v.webkitEnterFullscreen) v.webkitEnterFullscreen(); // iOS Safari
    else if (v.requestFullscreen) v.requestFullscreen();
    else if (v.webkitRequestFullscreen) v.webkitRequestFullscreen();
  });
  const wrap = document.createElement("div");
  wrap.className = "act__video-wrap";
  wrap.appendChild(v);
  wrap.appendChild(btn);
  return wrap;
}
```

<div class="cover">
  <div class="cover__inner">
    <p class="kicker">A demographic projection · 1971 – 2100</p>
    <h1>100&nbsp;million<br>Canadians</h1>
    <p class="dek">One influential lobby wants Canada to nearly triple in size by 2100.
    The country is already on that path. This projection asks the question its boosters skip:
    what does a hundred-million Canada do to <span class="tag tag--fr">French</span> —
    and to the weight of <b>Quebec</b> inside the federation?</p>
    <p class="scrollcue">Scroll to begin ↓</p>
  </div>
</div>

<!-- ============================ PROLOGUE ============================ -->
<section class="prologue">
<div class="prologue__inner">

<p class="section-eyebrow">The premise</p>

## A deliberate plan to build a much bigger country

In the mid-2010s a pair of business figures — former McKinsey managing director **Dominic Barton** and investment executive **Mark Wiseman**, the former head of the Canada Pension Plan Investment Board — co-founded the [**Century Initiative**](https://www.centuryinitiative.ca/), a lobby with a single, arresting goal: grow Canada's population to **100&nbsp;million people by 2100**, from roughly **40&nbsp;million** today. Barton went on to chair the federal Advisory Council on Economic Growth, whose recommendation to lift immigration toward 450,000 a year helped set the direction of the last decade of policy.

This is **not** a fringe cause or a conspiracy theory — it sits close to the center of Canadian power, woven into the Liberal Party's economic-growth machinery. **Barton**, who chaired that 2016 growth council, was later named ambassador to China. **Mark&nbsp;Carney** — himself a Trudeau-era economic adviser — went on to chair the Liberal Party's own Task Force on Economic Growth in 2024, then became prime minister in March 2025; once in office he named Barton's Century Initiative co-founder, **Wiseman** (reportedly a personal friend), Canada's ambassador to the United States, effective February 2026. Two men, the same growth-through-immigration project, a few years apart. The Initiative's ambition is, in effect, close to governing-party policy. Nor is the Quebec objection a caricature: Wiseman had publicly endorsed the view that Canada should grow to 100 million *"even if it makes Quebec howl,"* and the Bloc Québécois and Parti Québécois opposed his ambassadorship as a threat to Quebec's place in the country.

The engine is immigration, and lots of it — because it has to be. Canada's fertility rate has sat below the 2.1 replacement level ever since <b>1972</b> (1971 was the last year Canadian women averaged replacement-level fertility), and it has since fallen to a record-low ≈1.25. With births no longer keeping the population steady on their own, essentially <em>all</em> future growth — and all of the Century Initiative's 100 million — must come from newcomers. And that is precisely where the arithmetic collides with the country's other founding fact — that Canada is home to a French-speaking nation concentrated in Quebec.

<p class="watchnote">▶&nbsp; New to the premise? CaspianReport lays it out in <a href="https://www.youtube.com/watch?v=M1jat2-zI98">“Canada wants 100 million people by 2100.”</a></p>

<div class="stakes">
<div class="stakes__item">
  <span class="stakes__big">40M&nbsp;→&nbsp;~100M</span>
  <span class="stakes__lab">Canada's population, today to 2100 — the Century Initiative's target, and roughly where current trends already lead.</span>
</div>
<div class="stakes__item">
  <span class="stakes__big">1&nbsp;in&nbsp;4&nbsp;→&nbsp;1&nbsp;in&nbsp;10</span>
  <span class="stakes__lab">French as a share of Canadians (home language), 1971 to 2100 — from a quarter to a tenth.</span>
</div>
<div class="stakes__item">
  <span class="stakes__big">27.9%&nbsp;→&nbsp;~13%</span>
  <span class="stakes__lab">Quebec's weight in the federation — its share of all Canadians — over the same span.</span>
</div>
</div>

Immigration overwhelmingly adds English- and other-language speakers, and it settles overwhelmingly outside Quebec. Grow the whole to 100 million on that fuel and the francophone quarter of the country is diluted almost mechanically — not through anyone abandoning French, but through simple addition elsewhere. That is why the plan is fought hardest in Quebec: in 2023 Premier **François Legault** called it *"a threat to Quebec,"* and the Bloc Québécois and Parti Québécois lined up against it.

This site does not argue for or against 100 million. It **runs the demographics forward** — one agent, one year at a time, calibrated to the census — to show, concretely, what that number means for French in Canada and for Quebec's place in it. Scroll to watch it unfold.

</div>
</section>

<!-- ============================ ACT 1 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr2_prov_total_pop.mp4"), FileAttachment("../media/fg_bcr2_prov_total_pop.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>In <b>1971</b>, the year of the census this model starts from, Canada was a country of <b>21.6&nbsp;million</b>.</p></div>
<div class="step"><p>By <b>2025</b> it had reached <b>41.7&nbsp;million</b> — almost doubling in a little over half a century.</p></div>
<div class="step"><p>Carry the same forces forward and, in the middle scenario, Canada crosses <b>100&nbsp;million by 2100</b> — roughly <b>89 to 108&nbsp;million</b> across the range of assumptions. In other words, the <b>Century Initiative's 100&nbsp;million</b> is not a stretch goal; it is close to the default.</p></div>
<div class="step"><p>But the growth is not shared. <b>Ontario</b> more than doubles again, to <b>34&nbsp;million</b>. <b>Alberta</b> multiplies nearly ten-fold since 1971, to <b>16&nbsp;million</b>. <b>British&nbsp;Columbia</b> reaches <b>20&nbsp;million</b>.</p></div>
<div class="step"><p>The Atlantic and the territories barely move. Four provinces absorb almost all of the century's people — and, with them, almost all of its future.</p></div>
</div>
</section>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">The 2100 balance sheet</span>Where a century of growth lands

```js
const scenario = view(Inputs.radio(scenarios, {value: "mid", label: "Scenario", format: (s) => s[0].toUpperCase() + s.slice(1)}));
```

```js
const provRows = provinceRows(data, scenario).filter((d) => d.year <= END);
```

```js
Plot.plot({
  width, height: width < 560 ? 380 : 460, marginLeft: 48, marginRight: width < 560 ? 52 : 88,
  style: {background: "transparent", color: "#c7ccd4", fontSize: "13px"},
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Population (millions)", grid: true},
  color: {domain: provinces, range: provinces.map((p) => PROV_COLORS[p])},
  marks: [
    Plot.line(provRows, {x: "year", y: "pop", z: "prov", stroke: "prov", strokeWidth: 1.6}),
    Plot.text(provRows.filter((d) => d.year === END), {x: "year", y: "pop", text: "prov", dx: 8, textAnchor: "start", fill: "prov", fontSize: 10}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.tip(provRows, Plot.pointer({x: "year", y: "pop", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${province_names[d.prov]}\n${d.year}: ${d.pop.toFixed(1)}M`}))
  ]
})
```

<p class="caption caption--wide">Left of the dashed line (1971–2025) is calibrated to the census; right of it is projection. Each province's post-2025 path is driven by immigration plus a net-growth rate set at a few <a href="/en/methodology">anchor years</a> and interpolated between them — which is why the lines bend at round dates rather than curving smoothly. Quebec's visible <b>plateau around 2030</b> is grounded in official projections, not a modeling quirk: Statistics Canada's 2024-based projections and the Institut de la statistique du Québec both have Quebec's natural increase turning negative in the late 2020s — ISQ reports deaths exceeding births since 2024 and projects negative natural increase from 2027. In the model its net natural increase crosses zero in the late 2020s and briefly cancels immigration (≈−125k births-minus-deaths against ≈+110k newcomers) before growth resumes. Read the <em>trend</em>, not the year-by-year kinks — see the <a href="/en/methodology">Methodology</a>.</p>

<div class="grid grid-cols-3 statgrid">
  <div class="card"><h2>Canada's population</h2><span class="big">42M → ${(nationalTotal(data.series.mid, provinces)[iEnd]/1e6).toFixed(0)}M</span><span class="muted">2025 → 2100 (mid)</span></div>
  <div class="card"><h2>Quebec's share of Canada</h2><span class="big">22.0% → ${(100*provTotal(data.series.mid,"QC")[iEnd]/nationalTotal(data.series.mid, provinces)[iEnd]).toFixed(1)}%</span><span class="muted">2025 → 2100 (mid)</span></div>
  <div class="card"><h2>French, share of Canada</h2><span class="big">18.5% → ${(100*nationalLang(data.series.mid,provinces,"fr")[iEnd]/nationalTotal(data.series.mid, provinces)[iEnd]).toFixed(1)}%</span><span class="muted">home language, 2025 → 2100 (mid)</span></div>
</div>

</div>

<!-- ============================ ACT 2 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr3_lang_group_pop.mp4"), FileAttachment("../media/fg_bcr3_lang_group_pop.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>That population speaks three languages at home: <span class="tag tag--fr">French</span>, <span class="tag tag--en">English</span>, and <span class="tag tag--allo">everything else</span>.</p></div>
<div class="step"><p>Immigration overwhelmingly adds to the last two. The <span class="tag tag--allo">allophone</span> group — neither French nor English at home — climbs from <b>6.2&nbsp;million</b> in 2025 to <b>32&nbsp;million</b> in 2100, the fastest-growing part of the country.</p></div>
<div class="step"><p><span class="tag tag--en">Anglophones</span> keep pace and stay the majority, reaching about <b>58&nbsp;million</b>.</p></div>
<div class="step"><p><span class="tag tag--fr">Francophones</span> grow far more slowly — from <b>7.7&nbsp;million</b> to <b>9.7&nbsp;million</b>. In absolute numbers French still gains ground. As a <em>share</em> of Canada, it loses it everywhere.</p></div>
</div>
</section>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">The number that moves</span>French as a share of Canada

```js
const frBand = years.filter((y) => y <= END).map((year, idx) => {
  const v = scenarios.map((sc) => 100 * nationalLang(data.series[sc], provinces, "fr")[idx] / nationalTotal(data.series[sc], provinces)[idx]);
  const mid = 100 * nationalLang(data.series.mid, provinces, "fr")[idx] / nationalTotal(data.series.mid, provinces)[idx];
  return {year, lo: Math.min(...v), hi: Math.max(...v), mid};
});
const frCensus = [{year: 1971, share: 25.8}, {year: 2001, share: 22.4}, {year: 2021, share: 20.6}];
```

```js
Plot.plot({
  width, height: width < 560 ? 460 : 620, marginLeft: 56, marginRight: 24,
  style: {background: "transparent", color: "#c7ccd4", fontSize: "14px"},
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "French, % of Canada (home language)", domain: [0, 28], grid: true, ticks: 6},
  marks: [
    Plot.areaY(frBand, {x: "year", y1: "lo", y2: "hi", fill: LANG_COLORS.fr, fillOpacity: 0.14}),
    Plot.lineY(frBand, {x: "year", y: "mid", stroke: LANG_COLORS.fr, strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.dot(frCensus, {x: "year", y: "share", fill: "#e8eaed", stroke: LANG_COLORS.fr, strokeWidth: 1.5, r: 4}),
    Plot.text([{year: 2027, share: 26.5}], {x: "year", y: "share", text: ["projection →"], fill: "#8b93a1", textAnchor: "start", fontSize: 12}),
    Plot.text([{year: 2023, share: 26.5}], {x: "year", y: "share", text: ["census ←"], fill: "#8b93a1", textAnchor: "end", fontSize: 12}),
    Plot.tip(frBand, Plot.pointerX({x: "year", y: "mid", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.year}\nmid  ${d.mid.toFixed(1)}%\nrange  ${d.lo.toFixed(1)}–${d.hi.toFixed(1)}%`}))
  ]
})
```

<p class="caption caption--wide">Home-language French falls from <b>25.8%</b> of Canada in 1971 to <b>18.5%</b> in 2025 and <b>8–12%</b> by 2100 (band = low-to-high scenario, line = mid). White dots are census benchmarks the model is calibrated against.</p>

</div>

<!-- ============================ ACT 3 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr3b_lang_pie.mp4"), FileAttachment("../media/fg_bcr3b_lang_pie.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>Two very different linguistic worlds sit inside that one number: <b>Quebec</b>, and the <b>rest of Canada</b>.</p></div>
<div class="step"><p>In Quebec, French is still the language of the majority — but a shrinking one. Home-language French inside Quebec slides from <b>81%</b> in 1971 to about <b>50%</b> in 2100 as allophones grow.</p></div>
<div class="step"><p>Outside Quebec, French is already a rounding error and keeps falling — to roughly <b>4%</b> of the population. Even Acadian New&nbsp;Brunswick drops from <b>31%</b> French to <b>12%</b>.</p></div>
<div class="step"><p>Quebec's weight in the federation shrinks in step: from <b>27.9%</b> of all Canadians in 1971 to about <b>13%</b> in 2100.</p></div>
</div>
</section>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">The seats, the vetoes, the money</span>Quebec's weight in Canada

```js
const qcBand = qcShareBand(data).filter((d) => d.year <= END);
const qcCensus = [{year: 1971, share: 27.9}, {year: 2001, share: 24.1}, {year: 2021, share: 22.5}];
```

```js
Plot.plot({
  width, height: width < 560 ? 460 : 620, marginLeft: 56, marginRight: 24,
  style: {background: "transparent", color: "#c7ccd4", fontSize: "13px"},
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Quebec, % of Canada's population", domain: [0, 30], grid: true, ticks: 6},
  marks: [
    Plot.areaY(qcBand, {x: "year", y1: "lo", y2: "hi", fill: PROV_COLORS.QC, fillOpacity: 0.14}),
    Plot.lineY(qcBand, {x: "year", y: "mid", stroke: PROV_COLORS.QC, strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.dot(qcCensus, {x: "year", y: "share", fill: "#e8eaed", stroke: PROV_COLORS.QC, strokeWidth: 1.5, r: 4}),
    Plot.tip(qcBand, Plot.pointerX({x: "year", y: "mid", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.year}\nmid  ${d.mid.toFixed(1)}%\nrange  ${d.lo.toFixed(1)}–${d.hi.toFixed(1)}%`}))
  ]
})
```

<p class="caption caption--wide">Because immigration flows disproportionately to Ontario, Alberta and B.C., a bigger Canada is a <em>proportionally smaller Quebec</em>. Its share of the national population — and with it seats in the Commons, weight at first ministers' tables, and its constitutional gravity — falls from <b>27.9%</b> in 1971 toward <b>~13%</b> by 2100 (band = scenario range, line = mid; white dots are census benchmarks).</p>

</div>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">The two forces, combined</span>Quebec francophones as a share of Canada

```js
const qcfrBand = years.filter((y) => y <= END).map((year, idx) => {
  const v = scenarios.map((sc) => 100 * data.series[sc].QC.fr[idx] / nationalTotal(data.series[sc], provinces)[idx]);
  const mid = 100 * data.series.mid.QC.fr[idx] / nationalTotal(data.series.mid, provinces)[idx];
  return {year, lo: Math.min(...v), hi: Math.max(...v), mid};
});
```

```js
Plot.plot({
  width, height: width < 560 ? 460 : 620, marginLeft: 56, marginRight: 24,
  style: {background: "transparent", color: "#c7ccd4", fontSize: "13px"},
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Quebec francophones, % of all Canadians", domain: [0, 25], grid: true, ticks: 6},
  marks: [
    Plot.areaY(qcfrBand, {x: "year", y1: "lo", y2: "hi", fill: LANG_COLORS.fr, fillOpacity: 0.14}),
    Plot.lineY(qcfrBand, {x: "year", y: "mid", stroke: LANG_COLORS.fr, strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.tip(qcfrBand, Plot.pointerX({x: "year", y: "mid", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.year}\nmid  ${d.mid.toFixed(1)}%\nrange  ${d.lo.toFixed(1)}–${d.hi.toFixed(1)}%`}))
  ]
})
```

<p class="caption caption--wide">This is where the two declines meet: Quebec shrinking as a share of Canada <em>and</em> French shrinking inside Quebec. Together they take Quebec's francophones — <b>home-language French living in Quebec</b> — from <b>22.6%</b> of all Canadians in 1971 (nearly one in four) to about <b>6%</b> by 2100 (roughly one in sixteen). A projection of the model's home-language groups; the francophone share <em>inside</em> Quebec is calibration-sensitive, so read the shape, not the last decimal.</p>

</div>

<!-- ============================ ACT 4 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr4_prov_fr_share.mp4"), FileAttachment("../media/fg_bcr4_prov_fr_share.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>Watch the francophone share fall province by province across the century.</p></div>
<div class="step"><p>Quebec stays on top throughout — but every bar recedes. The decline is broad, steady, and driven less by assimilation than by <em>arithmetic</em>: newcomers arrive faster than French can absorb them.</p></div>
<div class="step"><p>The scenarios differ only in <em>how much</em>. Send more francophone immigration to the rest of Canada and the slide slows; it does not reverse.</p></div>
</div>
</section>

<!-- ============================ ACT 5 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr5_age_pyramid.mp4"), FileAttachment("../media/fg_bcr5_age_pyramid.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>One more thing changes: <b>age</b>.</p></div>
<div class="step"><p>The pyramid that was bottom-heavy in 1971 turns into a column. Even with steady immigration, the top of the age structure fills in as Canadians live longer and have fewer children.</p></div>
<div class="step"><p>A bigger, older, more linguistically plural country — that is the shape the current trends draw for 2100.</p></div>
</div>
</section>

<!-- ============================ EXPLORE ============================ -->
<div class="explore">

## <span class="section-eyebrow">The map that says it all</span>The retreat of French across North America

<p class="mapintro">Colored by the language spoken at home. Only <b>Quebec</b> and <b>New Brunswick</b> — the home of Canada's French — carry a color: the deeper the <span class="tag tag--fr">blue</span>, the higher the share of people speaking French at home. As that share falls they slide toward <span class="tag tag--en">red</span>, until they are barely distinguishable from the rest of a continent that never spoke much French to begin with. Watch the two provinces fade from <b>1971 to 2100</b>. <em>Click the map to pause.</em></p>

```js
import * as d3 from "npm:d3";
```

```js
animatedFrenchMap({d3, geo: naGeo, series: data.series.mid, years, END, width, invalidation,
  labels: {zoom: "Zoom · Québec · New England · Ontario · N.B.", lessFr: "0% French", moreFr: "100% French", qc: "Québec", nb: "N.B."}})
```

<p class="caption caption--wide">Mid scenario. Only Quebec and New Brunswick are colored by the model's home-language projection; the rest of North America is a flat backdrop (the model does not project the United States). The panel on the right zooms the northeast — Quebec, eastern Ontario, New Brunswick and the New England border.</p>

<div class="note">
Explore any year, metric and province on the interactive map in the <a href="/en/explorer">Explorer</a>, see <a href="/en/indigenous">Indigenous&nbsp;Canada</a>, or read the <a href="/en/methodology">Methodology</a> and its caveats. The videos above are the model's own bar-chart-races, 1971&nbsp;→&nbsp;2100, mid scenario.
</div>

</div>

```js
// Fade each text step up as it crosses the center of the viewport.
document.body.classList.add("scrolly-ready");
const _sObs = new IntersectionObserver((entries) => {
  for (const e of entries) e.target.classList.toggle("is-active", e.isIntersecting);
}, {rootMargin: "-45% 0px -45% 0px"});
for (const s of document.querySelectorAll(".step")) _sObs.observe(s);
invalidation.then(() => { _sObs.disconnect(); document.body.classList.remove("scrolly-ready"); });
```

<style>
/* ---- floating language switch (story page hides the global header) ---- */
.storyswitch { position: fixed; top: 14px; right: 16px; z-index: 50;
  display: flex; gap: 0.4rem; align-items: center; font: 600 0.8rem system-ui, sans-serif;
  background: rgba(9,12,17,0.6); backdrop-filter: blur(6px);
  padding: 0.25rem 0.55rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }
.storyswitch a { color: #8b93a1; text-decoration: none; padding: 0 0.25rem; border-radius: 3px; }
.storyswitch a.on { color: #e8eaed; background: rgba(138,180,248,0.18); }
.storyswitch a:hover { color: #8ab4f8; }
.storyswitch span { color: #3a3f48; }

/* ---- full-bleed story: widen the content column ---- */
#observablehq-main.observablehq { max-width: none; }
#observablehq-main { margin: 0; padding: 0; }
:root { --story-bg: #0e1117; --ink: #e8eaed; --ink-muted: #9aa2ad; }

/* ---- cover ---- */
.cover {
  min-height: 100vh; display: grid; place-items: center; text-align: center;
  padding: 6vh 1.25rem; position: relative;
  background:
    radial-gradient(80% 60% at 50% 12%, rgba(58,126,191,0.18), transparent 70%),
    radial-gradient(70% 55% at 50% 100%, rgba(58,191,110,0.10), transparent 70%),
    var(--story-bg);
}
.cover__inner { max-width: 60rem; }
.kicker { text-transform: uppercase; letter-spacing: 0.22em; font-size: 0.78rem;
  color: var(--ink-muted); margin: 0 0 1.4rem; }
.cover h1 { font-size: clamp(3rem, 12vw, 8rem); line-height: 0.94; margin: 0;
  letter-spacing: -0.04em; font-weight: 800;
  background: linear-gradient(92deg, #e8eaed 25%, #8ab4f8 75%);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.dek { font-size: clamp(1.05rem, 2.4vw, 1.5rem); color: #c7ccd4;
  max-width: 40ch; margin: 1.8rem auto 0; line-height: 1.5; }
.scrollcue { margin-top: 3rem; color: var(--ink-muted); font-size: 0.9rem;
  letter-spacing: 0.05em; animation: bob 2.4s ease-in-out infinite; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(6px); } }

/* ---- prologue: the Century Initiative framing ---- */
.prologue { background: var(--story-bg); padding: 7rem 1.25rem 6rem; }
.prologue__inner { max-width: 44rem; margin: 0 auto; }
.prologue h2 { font-size: clamp(1.7rem, 4.5vw, 2.6rem); letter-spacing: -0.02em;
  line-height: 1.12; font-weight: 700; margin: 0 0 1.6rem; color: var(--ink); }
.prologue p { font-size: clamp(1.05rem, 2.1vw, 1.22rem); line-height: 1.65;
  color: #cbd2dc; margin: 0 0 1.4rem; }
.prologue p b { color: #fff; font-weight: 650; }
.prologue a { color: #8ab4f8; text-decoration: none; border-bottom: 1px solid rgba(138,180,248,0.35); }
.prologue a:hover { border-bottom-color: #8ab4f8; }
.watchnote { font-size: 0.95rem !important; color: var(--ink-muted) !important;
  border-left: 2px solid rgba(138,180,248,0.5); padding: 0.1rem 0 0.1rem 0.9rem;
  margin: 1.6rem 0 !important; }
.watchnote a { color: #8ab4f8; text-decoration: none; border-bottom: 1px solid rgba(138,180,248,0.35); }
.watchnote a:hover { border-bottom-color: #8ab4f8; }
.stakes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px; overflow: hidden; margin: 2.4rem 0 2.6rem; }
.stakes__item { background: #12161d; padding: 1.4rem 1.2rem; display: flex; flex-direction: column; gap: 0.5rem; }
.stakes__big { font-size: clamp(1.2rem, 3vw, 1.6rem); font-weight: 750; letter-spacing: -0.01em;
  color: #fff; font-variant-numeric: tabular-nums; line-height: 1.1; }
.stakes__lab { font-size: 0.82rem; line-height: 1.45; color: var(--ink-muted); }
@media (max-width: 640px) { .stakes { grid-template-columns: 1fr; } }

/* ---- scrollytelling act: sticky video, steps scroll over it ---- */
.act { position: relative; background: var(--story-bg); }
.act__media {
  position: sticky; top: 0; height: 100vh; width: 100%;
  display: flex; align-items: center; justify-content: center;
  background: var(--story-bg); overflow: hidden;
}
.act__media > * { display: flex; align-items: center; justify-content: center;
  width: 100%; height: 100%; margin: 0; }
.act__video { max-width: 100%; max-height: 94vh; object-fit: contain; background: var(--story-bg); }
.act__video-wrap { position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.act__fs-btn {
  display: none; /* desktop: hidden */
  position: absolute; bottom: 10px; right: 10px; z-index: 5;
  background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.18);
  border-radius: 6px; color: #e8eaed; padding: 7px 8px; cursor: pointer;
  touch-action: manipulation; line-height: 0;
}
.act__fs-btn:hover { background: rgba(0,0,0,0.78); }
.act__steps { position: relative; z-index: 2; margin-top: -100vh;
  padding-bottom: 8vh; pointer-events: none; }
.step { min-height: 92vh; display: flex; align-items: flex-end;
  padding: 0 clamp(1rem, 6vw, 6rem) 6vh; }
.step--lead { min-height: 62vh; align-items: center; }
.step p {
  pointer-events: auto; max-width: 30rem; margin: 0;
  font-size: clamp(1.15rem, 2.6vw, 1.7rem); line-height: 1.45; color: #eef1f5;
  background: rgba(9, 12, 17, 0.82); border: 1px solid rgba(255,255,255,0.08);
  border-left: 3px solid #3a7ebf; border-radius: 4px;
  padding: 1.1rem 1.3rem; backdrop-filter: blur(6px);
  transition: opacity 0.5s ease, transform 0.5s ease;
  box-shadow: 0 18px 50px -20px rgba(0,0,0,0.9);
}
/* dimming only engages once the observer is live, so text stays readable without JS */
.scrolly-ready .step p { opacity: 0.32; transform: translateY(10px); }
.scrolly-ready .step.is-active p { opacity: 1; transform: none; }
.step p b { color: #fff; font-weight: 700; }
.step p em { color: #cdd4de; font-style: italic; }

/* language tags echo the video palette */
.tag { font-weight: 700; padding: 0 0.28em; border-radius: 3px; white-space: nowrap; }
.tag--fr   { color: #8fc0ef; }
.tag--en   { color: #f0b184; }
.tag--allo { color: #86e0ab; }

/* ---- interstitial chart + explore section ---- */
.section-eyebrow {
  display: block; text-transform: uppercase; letter-spacing: 0.14em;
  font-size: 0.72rem; color: var(--ink-muted); font-weight: 600; margin-bottom: 0.3rem;
}
.chartwrap, .explore { max-width: 960px; margin: 0 auto; padding: 6rem 1.25rem; }
.chartwrap--wide { max-width: none; padding-left: 2rem; padding-right: 2rem; }
/* the map section is full-bleed like the wide charts, so its intro/note match the map */
.explore { max-width: none; padding-left: 2rem; padding-right: 2rem; }
.explore .note { max-width: none; }
.chartwrap h2, .explore h2 { font-size: clamp(1.5rem, 4vw, 2.2rem); letter-spacing: -0.02em;
  margin: 0 0 1.5rem; font-weight: 700; line-height: 1.1; }
.explore h2 { margin-top: 4rem; }
.caption { color: var(--ink-muted); font-size: 0.9rem; margin: 1rem 0 0; max-width: 68ch; line-height: 1.5; }
.caption--wide { max-width: none; text-align: center; margin-left: auto; margin-right: auto; }

/* ---- explore map ---- */
.mapwrap { position: relative; margin-top: 1rem; }
.mapyear { position: absolute; top: 0; left: 4px; z-index: 2; pointer-events: none;
  font-size: clamp(3.5rem, 11vw, 8rem); font-weight: 800; line-height: 0.85;
  letter-spacing: -0.05em; color: #e8eaed; opacity: 0.12; font-variant-numeric: tabular-nums; }
.mapscrub { position: absolute; top: 8px; right: 4px; z-index: 2; }

/* ---- animated North America French-decline map ---- */
.mapintro { color: #cbd2dc; font-size: clamp(1rem, 2.1vw, 1.18rem); line-height: 1.6;
  max-width: none; margin: 0 0 1.6rem; }
.namap { margin: 0.5rem 0 0; cursor: pointer; }
.namap__panes { display: flex; gap: 14px; align-items: stretch; }
.namap__panes--stack { flex-direction: column; }
.namap__pane { position: relative; flex: 0 0 auto; }
.namap__pane--main { flex: 1 1 60%; }
.namap__pane--inset { flex: 1 1 40%; }
.namap__year { position: absolute; top: 4px; left: 12px; z-index: 2; pointer-events: none;
  font-size: clamp(2.6rem, 7vw, 5.5rem); font-weight: 800; line-height: 0.85;
  letter-spacing: -0.05em; color: #e8eaed; opacity: 0.55; font-variant-numeric: tabular-nums;
  text-shadow: 0 2px 18px rgba(0,0,0,0.85); }
.namap__hint { position: absolute; top: 6px; left: 10px; z-index: 2; pointer-events: none;
  font-size: 0.7rem; letter-spacing: 0.04em; color: #c7ccd4; opacity: 0.85;
  background: rgba(9,12,17,0.55); padding: 2px 7px; border-radius: 4px; }
.namap__legend { display: flex; align-items: center; justify-content: center; gap: 0.6rem;
  margin-top: 0.9rem; font-size: 0.78rem; color: var(--ink-muted); }
.namap__bar { display: inline-block; width: min(240px, 45vw); height: 10px; border-radius: 5px;
  border: 1px solid rgba(255,255,255,0.12); }
.namap.is-paused .namap__pane--main::after { content: "❚❚"; position: absolute; top: 8px; right: 12px;
  color: #e8eaed; opacity: 0.5; font-size: 0.9rem; z-index: 2; }

/* ---- stat cards ---- */
.statgrid { margin-top: 1.5rem; }
.card h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--ink-muted); font-weight: 600; margin: 0; }
.big { display: block; font-size: 1.6rem; font-weight: 700; line-height: 1.2;
  margin: 0.3rem 0; font-variant-numeric: tabular-nums; color: var(--ink); }
.muted { color: var(--ink-muted); font-size: 0.8rem; }
.note { margin: 3rem 0 1rem; padding: 1rem 1.25rem; border-left: 3px solid var(--theme-foreground-focus);
  background: var(--theme-background-alt); border-radius: 0 6px 6px 0; line-height: 1.6; }

@media (max-width: 640px) {
  /* The framework insets ALL content by 2rem (#observablehq-center margin) and
     caps the body width; that inset box is what the reactive `width` measures,
     so it was shrinking every chart and video. Reclaim the full phone screen. */
  body { max-width: none; margin: 0; }
  #observablehq-center { margin: 0; }
  #observablehq-main { margin: 0; }

  /* charts + prose reclaim the screen width */
  .chartwrap, .explore { padding-left: 0.6rem; padding-right: 0.6rem; }
  .chartwrap--wide { padding-left: 0.3rem; padding-right: 0.3rem; }
  .prologue { padding-left: 1rem; padding-right: 1rem; }

  /* Acts: drop the full-height sticky-overlay design. Wide-format videos are
     letterboxed to a tiny band inside a 100vh frame on a portrait phone, so
     instead stack each video full-width with its captions flowing beneath it. */
  .act__media { position: static; height: auto; overflow: visible; }
  .act__media > * { height: auto; }
  .act__video { max-width: 100%; max-height: none; width: 100%; }
  .act__video-wrap { height: auto; }
  .act__fs-btn { display: flex; }
  .act__steps { margin-top: 0; padding-bottom: 1.5rem; }
  .step, .step--lead { min-height: 0; display: block; align-items: initial;
    padding: 1.1rem 0.9rem 0; }
  .step p { max-width: none; font-size: 1.05rem; backdrop-filter: none; }
  /* captions must stay fully legible without the scroll-driven dimming */
  .scrolly-ready .step p { opacity: 1; transform: none; }
}
</style>
