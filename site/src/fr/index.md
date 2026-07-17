---
title: L'histoire
toc: false
header: false
sidebar: false
---

```js
// Sélecteur de langue flottant (cette page masque l'en-tête global).
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
  valueByCode, METRICS, LANG_COLORS, PROV_COLORS, PROV_FR, SCEN_LABEL_FR, animatedFrenchMap
} from "../components/lib.js";
const data = await FileAttachment("../data/canada.json").json();
const geo = await FileAttachment("../data/canada-provinces.geojson").json();
const naGeo = await FileAttachment("../data/north-america.geojson").json();
const {years, provinces, province_names, scenarios} = data.meta;
const END = 2100;                       // l'horizon de ce récit
const iEnd = years.indexOf(END);
```

```js
// Un seul observateur partagé : une vidéo ne joue que lorsque son acte est à l'écran.
const _vObs = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) e.target.play?.().catch(() => {});
    else e.target.pause?.();
  }
}, {threshold: 0.2});
invalidation.then(() => _vObs.disconnect());

// Construit une <video> pleine largeur à partir de deux FileAttachments (affiche + clip).
function mkVideo(mp4, jpg) {
  const v = document.createElement("video");
  v.muted = true; v.loop = true; v.playsInline = true; v.preload = "metadata";
  v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
  v.className = "act__video";
  Promise.all([mp4.href, jpg.href]).then(([m, p]) => { v.poster = p; v.src = m; });
  _vObs.observe(v);
  return v;
}
```

<div class="cover">
  <div class="cover__inner">
    <p class="kicker">Une projection démographique · 1971 – 2100</p>
    <h1>100&nbsp;millions<br>de Canadiens</h1>
    <p class="dek">Un lobby influent veut voir le Canada presque tripler d'ici 2100.
    Le pays est déjà sur cette trajectoire. Cette projection pose la question que ses promoteurs esquivent :
    qu'advient-il du <span class="tag tag--fr">français</span> dans un Canada de cent millions d'habitants —
    et du poids du <b>Québec</b> au sein de la fédération ?</p>
    <p class="scrollcue">Faites défiler pour commencer ↓</p>
  </div>
</div>

<!-- ============================ PROLOGUE ============================ -->
<section class="prologue">
<div class="prologue__inner">

<p class="section-eyebrow">La prémisse</p>

## Un plan délibéré pour bâtir un pays beaucoup plus grand

Au milieu des années 2010, deux figures du monde des affaires — **Dominic Barton**, ancien directeur général de McKinsey, et **Mark Wiseman**, dirigeant en placements et ancien patron de l'Office d'investissement du Régime de pensions du Canada — cofondent la [**Century Initiative**](https://www.centuryinitiative.ca/) (l'« Initiative du Siècle »), un lobby doté d'un objectif unique et saisissant : porter la population du Canada à **100&nbsp;millions d'habitants d'ici 2100**, contre environ **40&nbsp;millions** aujourd'hui. Barton a ensuite présidé le Conseil consultatif fédéral en matière de croissance économique, dont la recommandation de hausser l'immigration vers 450 000 personnes par an a contribué à orienter la dernière décennie de politiques.

Ce n'est **pas** une cause marginale ni une théorie du complot — elle se situe tout près du centre du pouvoir canadien, tissée dans la machinerie de croissance économique du Parti libéral. **Barton**, qui a présidé ce conseil de croissance de 2016, a plus tard été nommé ambassadeur en Chine. **Mark&nbsp;Carney** — lui-même conseiller économique sous Trudeau — a présidé le groupe de travail du Parti libéral sur la croissance économique en 2024, avant de devenir premier ministre en mars 2025 ; une fois en poste, il a nommé le cofondateur de la Century Initiative aux côtés de Barton, **Wiseman** (que l'on dit un ami personnel), ambassadeur du Canada aux États-Unis, à compter de février 2026. Deux hommes, le même projet de croissance par l'immigration, à quelques années d'intervalle. L'ambition de l'Initiative est, de fait, proche de la politique du parti au pouvoir. L'objection québécoise n'est pas non plus une caricature : Wiseman avait publiquement souscrit à l'idée que le Canada devrait croître à 100 millions *« même si cela fait hurler le Québec »*, et le Bloc Québécois et le Parti Québécois se sont opposés à sa nomination, y voyant une menace pour la place du Québec dans le pays.

Le moteur, c'est l'immigration, et à forte dose — parce qu'il le faut. L'indice de fécondité du Canada est sous le seuil de remplacement de 2,1 depuis <b>1972</b> (1971 fut la dernière année où les Canadiennes atteignaient en moyenne la fécondité de remplacement), et il est depuis tombé à un creux record d'environ 1,25. Les naissances ne suffisant plus à stabiliser la population à elles seules, c'est essentiellement <em>toute</em> la croissance future — et tout le 100 millions de la Century Initiative — qui devra venir des nouveaux arrivants. Et c'est précisément là que l'arithmétique entre en collision avec l'autre fait fondateur du pays : le Canada abrite une nation francophone concentrée au Québec.

<p class="watchnote">▶&nbsp; Sujet nouveau pour vous ? CaspianReport l'expose dans <a href="https://www.youtube.com/watch?v=M1jat2-zI98">« Canada wants 100 million people by 2100 ».</a></p>

<div class="stakes">
<div class="stakes__item">
  <span class="stakes__big">40M&nbsp;→&nbsp;~100M</span>
  <span class="stakes__lab">La population du Canada, d'aujourd'hui à 2100 — la cible de la Century Initiative, et à peu près là où mènent déjà les tendances actuelles.</span>
</div>
<div class="stakes__item">
  <span class="stakes__big">1&nbsp;sur&nbsp;4&nbsp;→&nbsp;1&nbsp;sur&nbsp;10</span>
  <span class="stakes__lab">Le français comme part des Canadiens (langue d'usage à la maison), de 1971 à 2100 — d'un quart à un dixième.</span>
</div>
<div class="stakes__item">
  <span class="stakes__big">27,9&nbsp;%&nbsp;→&nbsp;~13&nbsp;%</span>
  <span class="stakes__lab">Le poids du Québec dans la fédération — sa part de l'ensemble des Canadiens — sur la même période.</span>
</div>
</div>

L'immigration ajoute massivement des locuteurs de l'anglais et d'autres langues, et elle s'installe massivement hors du Québec. Portez l'ensemble à 100 millions avec ce carburant, et le quart francophone du pays se trouve dilué presque mécaniquement — non pas parce que quiconque abandonne le français, mais par simple addition ailleurs. Voilà pourquoi le plan est combattu avec le plus d'énergie au Québec : en 2023, le premier ministre **François Legault** l'a qualifié de *« menace pour le Québec »*, et le Bloc Québécois et le Parti Québécois s'y sont opposés.

Ce site ne plaide ni pour ni contre les 100 millions. Il **fait tourner la démographie vers l'avant** — un agent, une année à la fois, calibré sur le recensement — pour montrer concrètement ce que ce nombre signifie pour le français au Canada et pour la place du Québec en son sein. Faites défiler pour voir la suite se dérouler.

</div>
</section>

<!-- ============================ ACTE 1 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr2_prov_total_pop_fr.mp4"), FileAttachment("../media/fg_bcr2_prov_total_pop_fr.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>En <b>1971</b>, année du recensement dont part ce modèle, le Canada comptait <b>21,6&nbsp;millions</b> d'habitants.</p></div>
<div class="step"><p>En <b>2025</b>, il atteignait <b>41,7&nbsp;millions</b> — presque le double en un peu plus d'un demi-siècle.</p></div>
<div class="step"><p>Prolongez les mêmes forces et, dans le scénario intermédiaire, le Canada franchit <b>100&nbsp;millions dès 2100</b> — soit environ <b>89 à 108&nbsp;millions</b> selon l'éventail des hypothèses. Autrement dit, le <b>100&nbsp;millions de la Century Initiative</b> n'est pas un objectif ambitieux ; il est proche du scénario par défaut.</p></div>
<div class="step"><p>Mais la croissance n'est pas partagée. L'<b>Ontario</b> plus que redouble encore, à <b>34&nbsp;millions</b>. L'<b>Alberta</b> se multiplie près de dix fois depuis 1971, à <b>16&nbsp;millions</b>. La <b>Colombie-Britannique</b> atteint <b>20&nbsp;millions</b>.</p></div>
<div class="step"><p>L'Atlantique et les territoires bougent à peine. Quatre provinces absorbent la quasi-totalité des habitants du siècle — et, avec eux, presque tout son avenir.</p></div>
</div>
</section>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">Le bilan de 2100</span>Où atterrit un siècle de croissance

```js
const scenario = view(Inputs.radio(scenarios, {value: "mid", label: "Scénario", format: (s) => SCEN_LABEL_FR[s]}));
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
      title: (d) => `${PROV_FR[d.prov]}\n${d.year} : ${d.pop.toFixed(1)}M`}))
  ]
})
```

<p class="caption caption--wide">À gauche de la ligne pointillée (1971–2025), le modèle est calibré sur le recensement ; à droite, c'est une projection. La trajectoire de chaque province après 2025 est déterminée par l'immigration et par un taux de croissance nette fixé à quelques <a href="/fr/methodology">années d'ancrage</a> et interpolé entre elles — d'où des lignes qui plient à des dates rondes plutôt que de s'incurver en douceur. Le <b>plateau visible du Québec vers 2030</b> en est un artefact : son accroissement naturel net est ancré haut en 2024 et négatif dès 2030, si bien qu'il croise le zéro à la fin des années 2020 et annule brièvement l'immigration (≈−125 000 naissances-moins-décès contre ≈+110 000 arrivées) avant que la croissance ne reprenne. Lisez la <em>tendance</em>, pas les soubresauts d'une année à l'autre — voir la <a href="/fr/methodology">Méthodologie</a>.</p>

<div class="grid grid-cols-3 statgrid">
  <div class="card"><h2>Population du Canada</h2><span class="big">42M → ${(nationalTotal(data.series.mid, provinces)[iEnd]/1e6).toFixed(0)}M</span><span class="muted">2025 → 2100 (interm.)</span></div>
  <div class="card"><h2>Part du Québec dans le Canada</h2><span class="big">22,0 % → ${(100*provTotal(data.series.mid,"QC")[iEnd]/nationalTotal(data.series.mid, provinces)[iEnd]).toFixed(1).replace(".", ",")} %</span><span class="muted">2025 → 2100 (interm.)</span></div>
  <div class="card"><h2>Français, part du Canada</h2><span class="big">18,5 % → ${(100*nationalLang(data.series.mid,provinces,"fr")[iEnd]/nationalTotal(data.series.mid, provinces)[iEnd]).toFixed(1).replace(".", ",")} %</span><span class="muted">langue d'usage, 2025 → 2100 (interm.)</span></div>
</div>

</div>

<!-- ============================ ACTE 2 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr3_lang_group_pop_fr.mp4"), FileAttachment("../media/fg_bcr3_lang_group_pop_fr.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>Cette population parle trois langues à la maison : le <span class="tag tag--fr">français</span>, l'<span class="tag tag--en">anglais</span> et <span class="tag tag--allo">tout le reste</span>.</p></div>
<div class="step"><p>L'immigration alimente massivement les deux derniers groupes. Les <span class="tag tag--allo">allophones</span> — ni français ni anglais à la maison — passent de <b>6,2&nbsp;millions</b> en 2025 à <b>32&nbsp;millions</b> en 2100, la composante du pays qui croît le plus vite.</p></div>
<div class="step"><p>Les <span class="tag tag--en">anglophones</span> suivent le rythme et restent majoritaires, atteignant environ <b>58&nbsp;millions</b>.</p></div>
<div class="step"><p>Les <span class="tag tag--fr">francophones</span> croissent bien plus lentement — de <b>7,7&nbsp;millions</b> à <b>9,7&nbsp;millions</b>. En chiffres absolus, le français gagne encore du terrain. En <em>part</em> du Canada, il en perd partout.</p></div>
</div>
</section>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">Le chiffre qui bouge</span>Le français comme part du Canada

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
  y: {label: "Français, % du Canada (langue d'usage)", domain: [0, 28], grid: true, ticks: 6},
  marks: [
    Plot.areaY(frBand, {x: "year", y1: "lo", y2: "hi", fill: LANG_COLORS.fr, fillOpacity: 0.14}),
    Plot.lineY(frBand, {x: "year", y: "mid", stroke: LANG_COLORS.fr, strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.dot(frCensus, {x: "year", y: "share", fill: "#e8eaed", stroke: LANG_COLORS.fr, strokeWidth: 1.5, r: 4}),
    Plot.text([{year: 2027, share: 26.5}], {x: "year", y: "share", text: ["projection →"], fill: "#8b93a1", textAnchor: "start", fontSize: 12}),
    Plot.text([{year: 2023, share: 26.5}], {x: "year", y: "share", text: ["← recensement"], fill: "#8b93a1", textAnchor: "end", fontSize: 12}),
    Plot.tip(frBand, Plot.pointerX({x: "year", y: "mid", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.year}\ninterm.  ${d.mid.toFixed(1)}%\nplage  ${d.lo.toFixed(1)}–${d.hi.toFixed(1)}%`}))
  ]
})
```

<p class="caption caption--wide">Le français comme langue d'usage passe de <b>25,8 %</b> du Canada en 1971 à <b>18,5 %</b> en 2025, puis à <b>8–12 %</b> d'ici 2100 (la bande = scénario faible à élevé, la ligne = intermédiaire). Les points blancs sont les repères de recensement sur lesquels le modèle est calibré.</p>

</div>

<!-- ============================ ACTE 3 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr3b_lang_pie_fr.mp4"), FileAttachment("../media/fg_bcr3b_lang_pie_fr.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>Deux mondes linguistiques très différents se cachent dans ce seul chiffre : le <b>Québec</b> et le <b>reste du Canada</b>.</p></div>
<div class="step"><p>Au Québec, le français demeure la langue de la majorité — mais une majorité qui rétrécit. Le français comme langue d'usage au Québec glisse de <b>81 %</b> en 1971 à environ <b>50 %</b> en 2100 à mesure que croissent les allophones.</p></div>
<div class="step"><p>Hors Québec, le français est déjà une quantité négligeable et continue de reculer — vers environ <b>4 %</b> de la population. Même le Nouveau-Brunswick acadien passe de <b>31 %</b> de français à <b>12 %</b>.</p></div>
<div class="step"><p>Le poids du Québec dans la fédération diminue au même rythme : de <b>27,9 %</b> de l'ensemble des Canadiens en 1971 à environ <b>13 %</b> en 2100.</p></div>
</div>
</section>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">Les sièges, les vetos, l'argent</span>Le poids du Québec dans le Canada

```js
const qcBand = qcShareBand(data).filter((d) => d.year <= END);
const qcCensus = [{year: 1971, share: 27.9}, {year: 2001, share: 24.1}, {year: 2021, share: 22.5}];
```

```js
Plot.plot({
  width, height: width < 560 ? 460 : 620, marginLeft: 56, marginRight: 24,
  style: {background: "transparent", color: "#c7ccd4", fontSize: "13px"},
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Québec, % de la population canadienne", domain: [0, 30], grid: true, ticks: 6},
  marks: [
    Plot.areaY(qcBand, {x: "year", y1: "lo", y2: "hi", fill: PROV_COLORS.QC, fillOpacity: 0.14}),
    Plot.lineY(qcBand, {x: "year", y: "mid", stroke: PROV_COLORS.QC, strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.dot(qcCensus, {x: "year", y: "share", fill: "#e8eaed", stroke: PROV_COLORS.QC, strokeWidth: 1.5, r: 4}),
    Plot.tip(qcBand, Plot.pointerX({x: "year", y: "mid", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.year}\ninterm.  ${d.mid.toFixed(1)}%\nplage  ${d.lo.toFixed(1)}–${d.hi.toFixed(1)}%`}))
  ]
})
```

<p class="caption caption--wide">Parce que l'immigration afflue de façon disproportionnée vers l'Ontario, l'Alberta et la C.-B., un Canada plus grand est un <em>Québec proportionnellement plus petit</em>. Sa part de la population nationale — et avec elle ses sièges aux Communes, son poids aux tables des premiers ministres et sa gravité constitutionnelle — chute de <b>27,9 %</b> en 1971 vers <b>~13 %</b> d'ici 2100 (la bande = éventail des scénarios, la ligne = intermédiaire ; les points blancs sont des repères de recensement).</p>

</div>

<div class="chartwrap chartwrap--wide">

## <span class="section-eyebrow">Les deux forces réunies</span>Les francophones du Québec en part du Canada

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
  y: {label: "Francophones du Québec, % de l'ensemble des Canadiens", domain: [0, 25], grid: true, ticks: 6},
  marks: [
    Plot.areaY(qcfrBand, {x: "year", y1: "lo", y2: "hi", fill: LANG_COLORS.fr, fillOpacity: 0.14}),
    Plot.lineY(qcfrBand, {x: "year", y: "mid", stroke: LANG_COLORS.fr, strokeWidth: 2.5}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.tip(qcfrBand, Plot.pointerX({x: "year", y: "mid", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.year}\ninterm.  ${d.mid.toFixed(1)}%\nplage  ${d.lo.toFixed(1)}–${d.hi.toFixed(1)}%`}))
  ]
})
```

<p class="caption caption--wide">C'est ici que les deux déclins se rejoignent : le Québec qui rétrécit comme part du Canada <em>et</em> le français qui rétrécit à l'intérieur du Québec. Ensemble, ils font passer les francophones du Québec — le <b>français comme langue d'usage vivant au Québec</b> — de <b>22,6 %</b> de l'ensemble des Canadiens en 1971 (près d'un sur quatre) à environ <b>6 %</b> d'ici 2100 (environ un sur seize). C'est une projection des groupes de langue d'usage du modèle ; la part francophone <em>à l'intérieur</em> du Québec est sensible à la calibration, alors lisez la forme, pas la dernière décimale.</p>

</div>

<!-- ============================ ACTE 4 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr4_prov_fr_share_fr.mp4"), FileAttachment("../media/fg_bcr4_prov_fr_share_fr.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>Regardez la part francophone reculer, province par province, au fil du siècle.</p></div>
<div class="step"><p>Le Québec reste en tête du début à la fin — mais chaque barre recule. Le déclin est large, régulier, et tient moins de l'assimilation que de l'<em>arithmétique</em> : les nouveaux arrivants affluent plus vite que le français ne peut les absorber.</p></div>
<div class="step"><p>Les scénarios ne diffèrent que par l'<em>ampleur</em>. Envoyez davantage d'immigration francophone vers le reste du Canada et la glissade ralentit ; elle ne s'inverse pas.</p></div>
</div>
</section>

<!-- ============================ ACTE 5 ============================ -->
<section class="act">
<div class="act__media">

```js
mkVideo(FileAttachment("../media/fg_bcr5_age_pyramid_fr.mp4"), FileAttachment("../media/fg_bcr5_age_pyramid_fr.jpg"))
```

</div>
<div class="act__steps">
<div class="step step--lead"><p>Une dernière chose change : l'<b>âge</b>.</p></div>
<div class="step"><p>La pyramide, à large base en 1971, se transforme en colonne. Même avec une immigration soutenue, le sommet de la structure d'âge se remplit à mesure que les Canadiens vivent plus longtemps et ont moins d'enfants.</p></div>
<div class="step"><p>Un pays plus grand, plus vieux et plus pluriel sur le plan linguistique — voilà la forme que les tendances actuelles dessinent pour 2100.</p></div>
</div>
</section>

<!-- ============================ EXPLORER ============================ -->
<div class="explore">

## <span class="section-eyebrow">La carte qui dit tout</span>Le recul du français en Amérique du Nord

<p class="mapintro">Colorée selon la langue parlée à la maison. Seuls le <b>Québec</b> et le <b>Nouveau-Brunswick</b> — le cœur du français au Canada — portent une couleur : plus le <span class="tag tag--fr">bleu</span> est intense, plus la part de gens parlant français à la maison est élevée. À mesure que cette part chute, ils glissent vers le <span class="tag tag--en">rouge</span>, jusqu'à se confondre presque avec le reste d'un continent qui n'a jamais beaucoup parlé français. Regardez les deux provinces s'estomper de <b>1971 à 2100</b>. <em>Cliquez sur la carte pour la mettre en pause.</em></p>

```js
import * as d3 from "npm:d3";
```

```js
animatedFrenchMap({d3, geo: naGeo, series: data.series.mid, years, END, width, invalidation,
  labels: {zoom: "Zoom · Québec · Nouvelle-Angleterre · Ontario · N.-B.", lessFr: "0 % français", moreFr: "100 % français", qc: "Québec", nb: "N.-B."}})
```

<p class="caption caption--wide">Scénario intermédiaire. Seuls le Québec et le Nouveau-Brunswick sont colorés selon la projection du modèle (langue parlée à la maison) ; le reste de l'Amérique du Nord n'est qu'un fond uni (le modèle ne projette pas les États-Unis). Le panneau de droite zoome sur le nord-est — Québec, est de l'Ontario, Nouveau-Brunswick et la frontière de la Nouvelle-Angleterre.</p>

<div class="note">
Explorez chaque année, mesure et province sur la carte interactive de l'<a href="/fr/explorer">Explorateur</a>, découvrez le <a href="/fr/indigenous">Canada&nbsp;autochtone</a>, ou lisez la <a href="/fr/methodology">Méthodologie</a> et ses réserves. Les vidéos ci-dessus sont les courses de barres du modèle lui-même, 1971&nbsp;→&nbsp;2100, scénario intermédiaire.
</div>

</div>

```js
// Fait apparaître chaque bloc de texte en fondu lorsqu'il traverse le centre de l'écran.
document.body.classList.add("scrolly-ready");
const _sObs = new IntersectionObserver((entries) => {
  for (const e of entries) e.target.classList.toggle("is-active", e.isIntersecting);
}, {rootMargin: "-45% 0px -45% 0px"});
for (const s of document.querySelectorAll(".step")) _sObs.observe(s);
invalidation.then(() => { _sObs.disconnect(); document.body.classList.remove("scrolly-ready"); });
```

<style>
/* ---- sélecteur de langue flottant (la page-récit masque l'en-tête global) ---- */
.storyswitch { position: fixed; top: 14px; right: 16px; z-index: 50;
  display: flex; gap: 0.4rem; align-items: center; font: 600 0.8rem system-ui, sans-serif;
  background: rgba(9,12,17,0.6); backdrop-filter: blur(6px);
  padding: 0.25rem 0.55rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }
.storyswitch a { color: #8b93a1; text-decoration: none; padding: 0 0.25rem; border-radius: 3px; }
.storyswitch a.on { color: #e8eaed; background: rgba(138,180,248,0.18); }
.storyswitch a:hover { color: #8ab4f8; }
.storyswitch span { color: #3a3f48; }

/* ---- récit pleine largeur : on élargit la colonne de contenu ---- */
#observablehq-main.observablehq { max-width: none; }
#observablehq-main { margin: 0; padding: 0; }
:root { --story-bg: #0e1117; --ink: #e8eaed; --ink-muted: #9aa2ad; }

/* ---- couverture ---- */
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
  max-width: 44ch; margin: 1.8rem auto 0; line-height: 1.5; }
.scrollcue { margin-top: 3rem; color: var(--ink-muted); font-size: 0.9rem;
  letter-spacing: 0.05em; animation: bob 2.4s ease-in-out infinite; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(6px); } }

/* ---- prologue : le cadrage Century Initiative ---- */
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

/* ---- acte scrollytelling : vidéo fixe, le texte défile par-dessus ---- */
.act { position: relative; background: var(--story-bg); }
.act__media {
  position: sticky; top: 0; height: 100vh; width: 100%;
  display: flex; align-items: center; justify-content: center;
  background: var(--story-bg); overflow: hidden;
}
.act__media > * { display: flex; align-items: center; justify-content: center;
  width: 100%; height: 100%; margin: 0; }
.act__video { max-width: 100%; max-height: 94vh; object-fit: contain; background: var(--story-bg); }
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
/* le fondu ne s'active qu'une fois l'observateur en place, pour rester lisible sans JS */
.scrolly-ready .step p { opacity: 0.32; transform: translateY(10px); }
.scrolly-ready .step.is-active p { opacity: 1; transform: none; }
.step p b { color: #fff; font-weight: 700; }
.step p em { color: #cdd4de; font-style: italic; }

/* les étiquettes de langue reprennent la palette des vidéos */
.tag { font-weight: 700; padding: 0 0.28em; border-radius: 3px; white-space: nowrap; }
.tag--fr   { color: #8fc0ef; }
.tag--en   { color: #f0b184; }
.tag--allo { color: #86e0ab; }

/* ---- graphique intercalaire + section explorer ---- */
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

/* ---- carte explorer ---- */
.mapwrap { position: relative; margin-top: 1rem; }
.mapyear { position: absolute; top: 0; left: 4px; z-index: 2; pointer-events: none;
  font-size: clamp(3.5rem, 11vw, 8rem); font-weight: 800; line-height: 0.85;
  letter-spacing: -0.05em; color: #e8eaed; opacity: 0.12; font-variant-numeric: tabular-nums; }
.mapscrub { position: absolute; top: 8px; right: 4px; z-index: 2; }

/* ---- carte animée du recul du français en Amérique du Nord ---- */
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

/* ---- cartes statistiques ---- */
.statgrid { margin-top: 1.5rem; }
.card h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--ink-muted); font-weight: 600; margin: 0; }
.big { display: block; font-size: 1.6rem; font-weight: 700; line-height: 1.2;
  margin: 0.3rem 0; font-variant-numeric: tabular-nums; color: var(--ink); }
.muted { color: var(--ink-muted); font-size: 0.8rem; }
.note { margin: 3rem 0 1rem; padding: 1rem 1.25rem; border-left: 3px solid var(--theme-foreground-focus);
  background: var(--theme-background-alt); border-radius: 0 6px 6px 0; line-height: 1.6; }

@media (max-width: 640px) {
  /* Le framework insère TOUT le contenu de 2rem (#observablehq-center) et plafonne
     la largeur du corps ; c'est cette boîte que mesure la variable réactive `width`,
     ce qui rétrécissait chaque graphique et vidéo. On récupère tout l'écran. */
  body { max-width: none; margin: 0; }
  #observablehq-center { margin: 0; }
  #observablehq-main { margin: 0; }

  /* graphiques + texte récupèrent la largeur de l'écran */
  .chartwrap, .explore { padding-left: 0.6rem; padding-right: 0.6rem; }
  .chartwrap--wide { padding-left: 0.3rem; padding-right: 0.3rem; }
  .prologue { padding-left: 1rem; padding-right: 1rem; }

  /* Actes : on abandonne le design d'overlay fixe pleine hauteur. Les vidéos au
     format large sont réduites à une mince bande dans un cadre 100vh sur un
     téléphone en portrait ; on empile plutôt chaque vidéo pleine largeur avec ses
     légendes en dessous. */
  .act__media { position: static; height: auto; overflow: visible; }
  .act__media > * { height: auto; }
  .act__video { max-width: 100%; max-height: none; width: 100%; }
  .act__steps { margin-top: 0; padding-bottom: 1.5rem; }
  .step, .step--lead { min-height: 0; display: block; align-items: initial;
    padding: 1.1rem 0.9rem 0; }
  .step p { max-width: none; font-size: 1.05rem; backdrop-filter: none; }
  /* les légendes doivent rester lisibles sans le fondu piloté au défilement */
  .scrolly-ready .step p { opacity: 1; transform: none; }
}
</style>
