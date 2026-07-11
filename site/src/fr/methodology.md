---
title: Méthodologie
toc:
  label: Sommaire
---

```js
import {SCEN_COLOR, PROV_COLORS, PROV_FR, SCEN_LABEL_FR} from "../components/lib.js";
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
const scenLabel = (s) => SCEN_LABEL_FR[s];
```

# Méthodologie

## La question, et l'approche

La [Century Initiative](/fr/) soutient que le Canada devrait croître à 100 millions d'habitants d'ici 2100. Ce site prend ce nombre au sérieux comme *scénario démographique* et se demande ce qu'il implique pour le français au Canada et pour le poids du Québec dans la fédération. Pour répondre concrètement plutôt que de façon rhétorique, chaque figure de ce site est produite par une seule **microsimulation démographique à base d'agents** — non pas un tableur de ratios, mais une population synthétique que l'on fait croître, déplacer et réétiqueter une année à la fois.

## Le modèle

La population est stockée sous forme de deux tableaux d'entiers parallèles : chaque **agent** simulé porte une **province** (parmi 13) et un **groupe de langue d'usage** (francophone, anglophone, allophone). Un agent représente **`SCALE = 100`** personnes réelles ; ainsi la population de départ de 1971 (≈21,6 millions) correspond à environ 216 000 agents ; d'ici 2100, le scénario intermédiaire en compte de l'ordre du million. Le modèle avance une année à la fois de **1971 à 2100** (les données vont jusqu'en 2150), en appliquant quatre processus dans l'ordre :

<div class="eq eq--flow">état<sub>t+1</sub>&nbsp;=&nbsp;<b>Immigration</b> ∘ <b>AccroissementNaturel</b> ∘ <b>Migration</b> ∘ <b>Transfert</b> ( état<sub>t</sub> )</div>

Chaque processus est **stochastique** : les issues sont des tirages dans des lois de probabilité dont les paramètres proviennent des fichiers CSV du dossier `data/`. Faire tourner de nombreux agents laisse la loi des grands nombres faire la moyenne, si bien que les parts agrégées ressortent lisses même si le sort de chaque agent est un pile ou face.

### 1 · Transfert linguistique

À l'intérieur de chaque province, les agents peuvent changer de groupe de langue d'usage d'une année à l'autre selon une **matrice de transition annuelle 3×3** propre à la province, *M*<sup>(p)</sup>, où *M*<sup>(p)</sup><sub>ij</sub> est la probabilité qu'un agent actuellement dans le groupe *i* se retrouve dans le groupe *j* un an plus tard (chaque ligne somme à 1). Pour un agent de la province *p*, groupe *i* :

<div class="eq">Pr( groupe<sub>t+1</sub> = j&nbsp;|&nbsp;groupe<sub>t</sub> = i ) = M<sup>(p)</sup><sub>ij</sub>(t)</div>

Les taux hors diagonale sont faibles — quelques pour mille par an (p. ex. l'assimilation `allo→en` dans le reste du Canada, ou `fr→en` hors Québec) — mais composés sur 75 ans, ils comptent. La matrice du Québec garde le français comparativement « collant » ; celle du reste du Canada tire les allophones et les francophones vers l'anglais.

### 2 · Migration interprovinciale

Les déplacements entre provinces utilisent une **matrice annuelle 13×13** *A* dont la diagonale *A*<sub>pp</sub> est la probabilité de rester sur place. Un agent qui quitte la province *p* est réparti entre les destinations en proportion de la ligne hors diagonale, renormalisée :

<div class="eq">Pr( aller vers q&nbsp;|&nbsp;quitter p ) = A<sub>pq</sub> / Σ<sub>r ≠ p</sub> A<sub>pr</sub></div>

Les groupes linguistiques ne migrent pas de manière identique. La probabilité de départ de base (1 − *A*<sub>pp</sub>) est pondérée par un **multiplicateur linguistique** *λ*<sub>p,ℓ</sub> :

<div class="eq">Pr( quitter p&nbsp;|&nbsp;groupe ℓ ) = min( 1,&nbsp; (1 − A<sub>pp</sub>) · λ<sub>p,ℓ</sub> )</div>

Un multiplicateur inférieur à 1 rend un groupe plus « collant » à sa province — p. ex. les francophones sont bien moins susceptibles de quitter le Québec que les anglophones — ce qui explique en partie pourquoi le français se concentre plutôt qu'il ne se disperse.

### 3 · Accroissement naturel

Le modèle **ne suit pas** les âges. À la place, chaque province possède un unique **taux de croissance provincial net** *r*<sub>p</sub>(t) — naissances moins décès *plus le résidu net de migration / résidents non permanents*, **recalibré (2026) pour que le modèle reproduise la série provinciale du recensement** dans `historical_provincial_population.csv`, province par province (Ontario 16,2 M, Alberta 5,0 M, etc. en 2025). Chaque année, le nombre d'agents de la province *p* varie de :

<div class="eq">Δn<sub>p</sub> = arrondi( n<sub>p</sub> · r<sub>p</sub>(t) )</div>

Lorsque Δ*n*<sub>p</sub> > 0, ce nombre de **nouveaux agents** est créé et se voit attribuer une langue en échantillonnant le mélange linguistique *actuel* de la province (les enfants héritent de la distribution locale). Lorsque Δ*n*<sub>p</sub> < 0, des agents sont retirés uniformément au hasard. Après 2025, le taux revient à une trajectoire naturelle sous le seuil de remplacement, de sorte que la croissance provinciale de fin de siècle dépend presque entièrement de l'immigration. (Replier la migration nette dans ce taux est un raccourci de modélisation : les déplacements interprovinciaux sont *aussi* simulés explicitement pour leur sélectivité linguistique — ce taux porte le résidu nécessaire pour atteindre le total de recensement de chaque province.)

### 4 · Immigration

Chaque année, un volume *V*(t) de nouveaux arrivants se présente. Ils sont répartis entre les provinces par un **vecteur d'allocation** variable dans le temps *α*(t) (qui somme à 1), puis se voient attribuer une langue à l'aide de parts francophone et anglophone **propres à la région** — un jeu pour le Québec, un pour le reste du Canada (RDC) — la part allophone prenant le reste :

<div class="eq">part allophone = 1 − f<sub>région</sub>(t) − e<sub>région</sub>(t)</div>

C'est le moteur central de la dilution. Seulement ≈2 % des nouveaux arrivants déclarent le français, ils s'installent à ≈8 % au Québec, et la **fraction francophone effective de l'ensemble du flux migratoire** se situe donc bien en dessous de la part francophone de la population existante. Versez un afflux important, majoritairement non francophone, dans une base de 40 millions et faites-la croître vers 100 millions : la *part* francophone chute par arithmétique même si le *nombre* de francophones continue d'augmenter.

## Paramètres du modèle

| Paramètre | Symbole | Fichier source | Notes |
|---|---|---|---|
| Échelle des agents | `SCALE` = 100 | `canada_sim.py` | 1 agent = 100 personnes ; plus bas = plus fin mais plus lent |
| Provinces / territoires | 13 | `initial_population_1971.csv` | T.N.-O. et Nunavut séparés ; fusionnés seulement au dénominateur autochtone |
| Groupes linguistiques | 3 | — | Francophone, anglophone, allophone (langue d'usage) |
| Population initiale | — | `initial_population_1971.csv` | effectifs de 1971 + parts fr / allo par province |
| Matrices de transfert linguistique | *M*<sup>(p)</sup>(t) | `language_transfer_matrices.csv` | province × année, 3×3, lignes sommant à 1 |
| Matrice de migration | *A*(t) | `interprovincial_migration.csv` | probabilités annuelles de rester / partir, 13×13 |
| Multiplicateurs linguistiques de migration | *λ*<sub>p,ℓ</sub> | `migration_language_multipliers.csv` | statiques ; 1,0 = moyenne provinciale |
| Taux de croissance provincial net | *r*<sub>p</sub>(t) | `natural_increase.csv` | naissances−décès + résidu de migration nette, ajusté à la série provinciale du recensement |
| Volume d'immigration | *V*(t) | `immigration_volume.csv` | arrivées annuelles ; interpolées entre les ancres |
| Composition de l'immigration | *f*, *e* | `immigration_composition.csv` | parts fr / en, séparément pour QC et RDC |
| Allocation provinciale | *α*(t) | `immigration_provincial_allocation.csv` | part des arrivées vers chaque province |

Toutes les entrées variables dans le temps sont données à quelques **années d'ancrage** et **interpolées linéairement** entre elles ; ainsi un paramètre comme le volume d'immigration est une courbe linéaire par morceaux, p. ex. 122 k (1971) → 500 k (2025) → 1,09 M (2030) → 1,49 M (2100) — l'apport soutenu d'environ 1,1 à 1,5 M par an qu'un Canada de 100 millions exige réellement une fois l'accroissement naturel passé sous le seuil de remplacement.

### Années d'ancrage, par entrée

Le tableau ci-dessous liste les années d'ancrage exactes pour chaque entrée variable dans le temps. Pour les entrées **variant selon la province** (croissance nette, migration, allocation provinciale), les *mêmes* années d'ancrage s'appliquent à l'identique aux 13 provinces — chaque ligne est une année, avec une colonne par province — et les valeurs provinciales à chaque ancre historique proviennent de la source citée ; **les ancres des années de projection (après 2025) sont les hypothèses du modélisateur**, non des valeurs sourcées. Les numéros de référence `[n]` renvoient à la liste des [Sources](#sources) ci-dessous.

| Entrée | Ancres historiques / de calibration | Ancres de projection | Interp. | Source |
|---|---|---|---|---|
| Taux de croissance provincial net (`natural_increase.csv`) | 1971, 1981, 1991, 2001, 2011, 2021, 2024 | 2030, 2050, 2075, 2100, 2150 | linéaire | ajusté à la série provinciale de StatCan [2] |
| Populations provinciales, cible de calibration (`historical_provincial_population.csv`) | 1971, 1981, 1991, 2001, 2006, 2011, 2016, 2021, 2025 | — | — | Recensement [1] ; tableau 17-10-0009-01 (T1 2025) [2] |
| Migration interprovinciale (`interprovincial_migration.csv`) | 1971, 2000, 2024 | (maintenue constante après 2024) | linéaire | tableau 17-10-0015-01 [6] |
| Volume d'immigration (`immigration_volume.csv`) | 1971, 1975, 1980, …, 2020 (aux 5 ans), puis 2021, 2022, 2023, 2024, 2025 | 2030, 2040, 2050, 2075, 2100, 2150 | linéaire | arrivées IRCC / StatCan [3] |
| Allocation provinciale de l'immigration (`immigration_provincial_allocation.csv`) | 1971, 1990, 2010, 2023 | 2030, 2040, 2050, 2100, 2150 | linéaire | IRCC par province de destination [3] |
| Composition fr/en de l'immigration, QC et RDC (`immigration_composition.csv`) | 1971, 1981, 1990, 2001, 2003, 2011, 2015, 2016, 2021, 2022, 2025 | 2030, 2035, 2040, 2050, 2075, 2100, 2150 | linéaire | OQLF [4] / MIFI [5] (QC) ; cibles IRCC [3] (RDC) |
| Matrices de transfert linguistique (`language_transfer_matrices.csv`) | 1971, 1996, 2021 | 2050, 2100 | linéaire | Projections linguistiques StatCan 89-657-X [8] ; OQLF [4] |
| Part du français à la maison, calibration (`historical_francophone_share.csv`) | 1971, 1991, 1996, 2001, 2006, 2011, 2016, 2021 | — | — | Recensement [1] |
| Ancres de population autochtone (`indigenous_population.csv`) | 1971, 1996, 2006, 2016, 2021 | projetées via `indigenous_natural_increase.csv` | log-linéaire | Recensement [1] |

Les entrées démographiques à grain fin utilisent leurs propres ancres de période — fécondité et mortalité à **1971, 2001, 2021, 2050, 2100** (avec 1971/1991 comme historique pour les tables de mortalité) [9][10][11], émigration à **1971, 2001, 2021, 2050, 2100** [13] — interpolées de la même façon.

### Valeurs d'ancrage, par province

Comme les *années* d'ancrage sont communes, le contenu propre à chaque province se résume à la **valeur** à chaque ancre. Trois tableaux variant selon la province sont donnés ci-dessous : les **populations cibles de calibration** auxquelles le modèle est ajusté (les chiffres réels de recensement/estimation), le taux de croissance provincial net (§3), et l'allocation provinciale de l'immigration (§4). Les cellules montrent l'entrée calibrée (≤2025) ou supposée (>2025) à chaque ancre ; le modèle interpole linéairement entre elles. Les tableaux défilent horizontalement sur les écrans étroits.

```js
// Population provinciale cible de calibration, en milliers de personnes, directement
// tirée de data/historical_provincial_population.csv via export_web_data.py.
// Recensement du Canada StatCan 1971–2021 [1] ; Estimations de la population,
// trimestrielles, tableau 17-10-0009-01, T1 2025 (1er avril 2025) [2]. Le Nunavut
// d'avant 1999 est inclus dans les T.N.-O. (exporté à null, affiché « — » pour NU
// en 1971–1991).
const CALIB_ANCHORS = data.calibration.anchors;
const CALIB_POP = data.calibration.population_thousands;
const calibTable = () => html`<div style="overflow-x:auto"><table class="anchortab">
  <thead><tr><th>Prov.</th>${CALIB_ANCHORS.map((y) => html`<th>${y}</th>`)}</tr></thead>
  <tbody>${data.meta.provinces.map((p) => html`<tr>
    <td class="prov" title=${PROV_FR[p]}>${p}</td>
    ${CALIB_POP[p].map((v) => html`<td>${v == null ? "—" : v.toLocaleString("fr-CA", {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>`)}
  </tr>`)}</tbody>
</table></div>`;
```

<div class="anchorcap">Population provinciale cible de calibration — milliers de personnes (<code>historical_provincial_population.csv</code>). Recensement StatCan 1971–2021 [1] ; estimations trimestrielles tableau 17-10-0009-01, T1 2025 [2]. Le Nunavut d'avant 1999 est inclus dans les T.N.-O.</div>

```js
calibTable()
```

Comme les *années* d'ancrage sont communes, les deux paramètres **d'entrée** variant selon la province qui façonnent le plus directement la projection sont présentés ci-dessous — le taux de croissance provincial net (§3) et l'allocation provinciale de l'immigration (§4).

```js
const NI_ANCHORS = [1971, 1981, 1991, 2001, 2011, 2021, 2024, 2030, 2050, 2075, 2100];
const ALLOC_ANCHORS = [1971, 1990, 2010, 2023, 2030, 2040, 2050, 2100];
const anchorTable = (obj, anchors, scale, digits, {neg = false} = {}) => {
  const yi = (y) => years.indexOf(y);
  return html`<div style="overflow-x:auto"><table class="anchortab">
    <thead><tr><th>Prov.</th>${anchors.map((y) => html`<th class=${y > 2025 ? "proj" : ""}>${y}</th>`)}</tr></thead>
    <tbody>${data.meta.provinces.map((p) => html`<tr>
      <td class="prov" title=${PROV_FR[p]}>${p}</td>
      ${anchors.map((y) => {
        const i = yi(y);
        const v = i < 0 ? null : obj[p][i] * scale;
        return html`<td class=${neg && v < 0 ? "n" : ""}>${v == null ? "—" : v.toFixed(digits)}</td>`;
      })}</tr>`)}</tbody>
  </table></div>`;
};
```

<div class="anchorcap">Taux de croissance provincial net <b>r<sub>p</sub>(t)</b> — % par an (<code>natural_increase.csv</code>). Ancres postérieures à 2025 ombrées.</div>

```js
anchorTable(P.natural_increase, NI_ANCHORS, 100, 2, {neg: true})
```

<div class="anchorcap">Allocation provinciale de l'immigration <b>α(t)</b> — % des arrivées annuelles (<code>immigration_provincial_allocation.csv</code>). Ancres postérieures à 2025 ombrées.</div>

```js
anchorTable(P.provincial_allocation, ALLOC_ANCHORS, 100, 1)
```

## Scénarios

Les trois scénarios phares partagent une **calibration 1971–2025 identique**, puis ne divergent que par deux réglages post-2025 appliqués par-dessus les entrées d'immigration de base :

| Scénario | Volume × (après 2025) | Décalage de part fr | Part fr du RDC | Signification pour le français |
|---|---|---|---|---|
| **Faible** | 1,10 | −0,040 | 0,010 | Pessimiste — plus de volume, moins de francophones |
| **Intermédiaire** | 1,00 | 0,000 | 0,040 | Prolongation de la tendance ; atteint ~100 M vers 2100 |
| **Élevé** | 0,85 | +0,040 | 0,089 | Optimiste — moins de volume, sélection francophone soutenue |

Formellement, `volume_multiplier_post2025` met à l'échelle *V*(t) pour t > 2025, et `fr_share_offset_post2025` est ajouté à *f*<sub>région</sub>(t) (borné à [0, 1]). Les scénarios `roc_*` **fixent** plutôt l'apport francophone du reste du Canada à une valeur constante (4 %, 6 %, 8 %) pour tester la sensibilité « Afrique francophone ». Notez le signe contre-intuitif : un volume total *plus élevé* est *pire* pour la part du français, car il ajoute surtout des non-francophones — donc **« Faible » est le cas pessimiste pour le français**.

## Diagnostics des paramètres

Les graphiques ci-dessous tracent directement les *entrées* du modèle — les courbes que les quatre processus lisent chaque année. Ce sont les leviers ; tout le reste du site est ce qui arrive quand on les actionne. Toutes proviennent du même paquet `canada.json` qui alimente le récit, et sont bornées à l'horizon 2100.

### Volume d'immigration

Le plus grand moteur, et de loin. Arrivées historiques jusqu'en 2024, puis une rampe projetée calibrée pour que le scénario intermédiaire atteigne près de 100 millions d'ici 2100. Le réglage de scénario met à l'échelle la portion post-2025 (Faible ×1,10, Élevé ×0,85).

```js
const volRows = seriesByScen(P.immigration_volume, 1 / 1000);
```

```js
Plot.plot({
  width, height: 300, marginRight: 66, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Arrivées annuelles (milliers)", grid: true},
  color: {domain: ["low", "mid", "high"], range: SCEN_RANGE, legend: true, tickFormat: scenLabel},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(volRows, {x: "year", y: "v", z: "scen", stroke: "scen", strokeWidth: (d) => d.scen === "mid" ? 2.4 : 1.5}),
    Plot.tip(volRows, Plot.pointer({x: "year", y: "v", z: "scen", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${scenLabel(d.scen)}\n${d.year} : ${d.v.toFixed(0)}k`}))
  ]
})
```

### Le moteur de dilution : la fraction francophone du flux migratoire

C'est le mécanisme derrière toute l'histoire. En pondérant les apports francophones du Québec et du reste du Canada par le lieu réel d'installation des immigrants, on obtient la **part effective du français chez tous les nouveaux arrivants**. Elle se situe bien en dessous de la part d'≈20 % du français dans la population existante — de sorte que chaque année d'immigration tire la part nationale du français vers le bas, par arithmétique, avant toute assimilation.

```js
const effRows = seriesByScen(P.effective_fr_fraction, 100);
```

```js
Plot.plot({
  width, height: 300, marginRight: 66, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Français, % du flux migratoire", grid: true, domain: [0, 22]},
  color: {domain: ["low", "mid", "high"], range: SCEN_RANGE, legend: true, tickFormat: scenLabel},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(effRows, {x: "year", y: "v", z: "scen", stroke: "scen", strokeWidth: (d) => d.scen === "mid" ? 2.4 : 1.5}),
    Plot.tip(effRows, Plot.pointer({x: "year", y: "v", z: "scen", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${scenLabel(d.scen)}\n${d.year} : ${d.v.toFixed(1)}%`}))
  ]
})
```

### Allocation provinciale de l'immigration

Où atterrissent les nouveaux arrivants. L'Ontario, la C.-B. et l'Alberta prennent la part du lion ; la tranche du Québec (≈14 % et en baisse) est bien inférieure à ses ≈22 % de la population — la deuxième raison pour laquelle un Canada plus grand est un Québec proportionnellement plus petit.

```js
const allocProvs = ["ON", "QC", "BC", "AB", "MB", "SK"];
const allocRows = seriesByProv(P.provincial_allocation, allocProvs, 100);
```

```js
Plot.plot({
  width, height: 320, marginRight: 44, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Part des arrivées annuelles (%)", grid: true},
  color: {domain: allocProvs, range: allocProvs.map((p) => PROV_COLORS[p]), legend: true},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(allocRows, {x: "year", y: "v", z: "prov", stroke: "prov", strokeWidth: 1.8}),
    Plot.text(allocRows.filter((d) => d.year === END), {x: "year", y: "v", text: "prov", dx: 8, textAnchor: "start", fill: "prov", fontSize: 10}),
    Plot.tip(allocRows, Plot.pointer({x: "year", y: "v", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.prov}\n${d.year} : ${d.v.toFixed(1)}%`}))
  ]
})
```

### Accroissement naturel

Le **taux de croissance provincial net** recalibré (naissances−décès + résidu de migration nette), ajusté pour que le modèle reproduise la population de recensement de chaque province. Le pic 2021→2025 est le boom de l'immigration / des RNP ; il décroît après 2025 vers une trajectoire sous le seuil de remplacement, de sorte que la croissance provinciale de fin de siècle repose presque entièrement sur l'immigration. Les provinces que la matrice de migration brute vide trop (Prairies, Atlantique) portent un résidu positif ; l'Alberta en porte un négatif.

```js
const niProvs = ["QC", "ON", "AB", "BC", "NB", "NL"];
const niRows = seriesByProv(P.natural_increase, niProvs, 100);
```

```js
Plot.plot({
  width, height: 320, marginRight: 44, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "Accroissement naturel net (%/an)", grid: true},
  color: {domain: niProvs, range: niProvs.map((p) => PROV_COLORS[p]), legend: true},
  marks: [
    Plot.ruleY([0], {stroke: "#6b7280"}),
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(niRows, {x: "year", y: "v", z: "prov", stroke: "prov", strokeWidth: 1.8}),
    Plot.tip(niRows, Plot.pointer({x: "year", y: "v", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.prov}\n${d.year} : ${d.v.toFixed(2)}%/an`}))
  ]
})
```

#### Comment les nœuds post-2025 sont fixés — et jusqu'où on peut les sourcer

Parce que *r*<sub>p</sub>(t) est un taux **net** — changement naturel *plus* le résidu de migration / RNP que le modèle ne porte nulle part ailleurs — ses ancres de projection sont construites structurellement, et non lues dans un tableau publié. Chaque nœud est :

<div class="eq"><b>r<sub>p</sub>(2030)</b> = [ niveau structurel de 2021, <i>ajusté</i> au recensement 2011→2021 ] + [ dérive d'≈ −0,2 pt/décennie sous le remplacement, <i>supposée</i> ]</div>

`calibrate_ni.py` ajuste le nœud 2021 au recensement ; `rebase_projection` réapplique ensuite la *forme* sous-remplacement du fichier d'origine sur cette base ajustée. Ainsi la projection de chaque province porte une **base empirique** et une **pente supposée**. Jusqu'où le nœud obtenu peut être rattaché à une projection externe dépend de la composante dominante :

- **Provinces en déclin naturel (Québec, Terre-Neuve-et-Labrador, Nouveau-Brunswick).** Le nœud négatif reflète un changement naturel réellement négatif projeté. Corroboré : l'ISQ compte plus de décès que de naissances au Québec depuis 2024 et projette un **accroissement naturel négatif dès 2027** [15] ; les projections de StatCan (base 2024) montrent l'accroissement naturel devenant négatif d'abord dans les **provinces les plus âgées — la région de l'Atlantique et le Québec** [14].
- **L'Alberta est l'exception honnête.** Son nœud de −2,6 %/an n'est **pas** une affirmation démographique : les estimations de StatCan donnent à l'Alberta la **structure d'âge la plus jeune et un accroissement naturel nettement positif** [16]. Le taux négatif est le résidu de calibration compensant la sur-allocation explicite d'immigration / RNP à l'Alberta durant le boom de 2021–25 — un **ajustement comptable, non un déclin naturel projeté**. L'Ontario et la C.-B. se situent entre les deux.
- **Petites provinces à résidu positif (Î.-P.-É., Sask., Man., N.-É.).** La matrice brute de migration interprovinciale les vide trop, si bien que le taux net reste positif pour maintenir leurs totaux de recensement. Là encore, c'est un résidu de calibration, non une prévision d'accroissement naturel.

Nœuds de projection par province (%/an), avec la base empirique de 2021 séparée de la dérive supposée :

| Prov | 2021 (ajusté) | 2030 | 2050 | Facteur dominant | Corroboration externe |
|---|---:|---:|---:|---|---|
| QC | −1,07 | −1,27 | −1,37 | déclin naturel | ISQ : accr. nat. nég. dès 2027 [15] ; StatCan [14] |
| NL | −0,64 | −0,84 | −0,94 | déclin naturel + émigration | StatCan : accr. nat. de l'Atlantique négatif [14] |
| NB | −0,83 | −0,93 | −1,03 | déclin naturel + émigration | StatCan [14] |
| ON | −0,49 | −0,69 | −0,79 | mixte — surtout résiduel | (résidu de calibration) |
| BC | +0,09 | −0,11 | −0,21 | résidu ~équilibré | (résidu de calibration) |
| NS | +0,92 | +0,72 | +0,62 | résidu de sur-drainage | (résidu de calibration) |
| MB | +0,45 | +0,30 | +0,20 | résidu de sur-drainage | (résidu de calibration) |
| SK | +1,36 | +1,21 | +1,11 | résidu de sur-drainage | (résidu de calibration) |
| PE | +2,03 | +1,83 | +1,73 | résidu de sur-drainage | (résidu de calibration) |
| AB | −2,38 | −2,63 | −2,73 | résidu RNP post-boom | accr. nat. de l'AB **positif** [16] — le nœud est un ajustement comptable |

Les territoires (Yn, T.N.-O., Nt) conservent leurs petits taux positifs d'origine. **En résumé :** la *forme* (une glissade régulière après 2025 vers le sous-remplacement) est fondée sur l'ISQ [15] et StatCan [14] ; le *niveau* par province est un résidu de calibration, et pour les provinces à forte immigration il ne doit **pas** être assimilé à un accroissement naturel projeté.

### Transfert linguistique : à quel point le français est « collant »

Le rythme auquel les allophones passent à l'anglais à la maison (`allo→en`, pour mille par an), pour trois provinces. Il est d'un ordre de grandeur plus faible à l'intérieur du **Québec** qu'en Ontario ou au Nouveau-Brunswick — l'attraction assimilatrice vers l'anglais est un phénomène du reste du Canada, et c'est pourquoi le français tient bien mieux au Québec qu'ailleurs.

```js
const ltProvs = ["QC", "ON", "NB"];
const ltRows = ltProvs.flatMap((p) =>
  years.map((y, i) => ({year: y, prov: p, v: P.language_transfer[p].allo_en[i] * 1000})).filter((d) => inRange(d.year)));
```

```js
Plot.plot({
  width, height: 300, marginRight: 44, style: AX,
  x: {label: null, tickFormat: "d", domain: [1971, END]},
  y: {label: "allophone → anglais (‰ par an)", grid: true},
  color: {domain: ltProvs, range: ltProvs.map((p) => PROV_COLORS[p]), legend: true},
  marks: [
    Plot.ruleX([2025], {stroke: "#6b7280", strokeDasharray: "3 4"}),
    Plot.line(ltRows, {x: "year", y: "v", z: "prov", stroke: "prov", strokeWidth: 2}),
    Plot.tip(ltRows, Plot.pointer({x: "year", y: "v", z: "prov", fill: "#161a20", stroke: "#2a2f38",
      title: (d) => `${d.prov}\n${d.year} : ${d.v.toFixed(1)}‰`}))
  ]
})
```

### Multiplicateurs de migration interprovinciale

Un ajustement statique : à quel point chaque groupe linguistique est plus ou moins susceptible de quitter une province donnée, par rapport à la moyenne de cette province (1,0). Notez la colonne du Québec — les francophones sont fortement plus *collants* (sous 1) et les anglophones bien plus mobiles, ce qui maintient le français concentré au Québec plutôt qu'il ne se disperse.

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
  color: {scheme: "RdYlGn", domain: [0.5, 1.5], legend: true, label: "Départ × (1,0 = moyenne provinciale)"},
  marks: [
    Plot.cell(multRows, {x: "prov", y: "lang", fill: "v"}),
    Plot.text(multRows, {x: "prov", y: "lang", text: (d) => d.v.toFixed(1), fontSize: 9, fill: "#111"})
  ]
})
```

## Calibration et projection

- **1971–2025** est une fenêtre de *calibration* : les entrées utilisent des chiffres empiriques de Statistique Canada (recensements et estimations trimestrielles), et le modèle est ajusté pour reproduire le dossier historique. Il suit désormais de près la population nationale et la série **provinciale** du recensement (tableau 17-10-0009-01, T1 2025) — Ontario 16,2 M, Québec 9,1 M, Alberta 5,0 M — et la part nationale du français à environ un point près. (La part du français à la maison *à l'intérieur* du Québec est une calibration distincte et plus ardue, actuellement un peu basse — voir les réserves.)
- **2025–2100** est une *projection* : les entrées extrapolent les tendances actuelles. Le scénario intermédiaire atteint **~100 millions d'ici 2100** (99,6 M) — correspondant à la cible de la Century Initiative, raison pour laquelle nous traitons cette cible comme un scénario réel plutôt qu'une fantaisie. L'atteindre exige désormais ~1,1 à 1,5 M d'immigrants par an, car le changement naturel sous le remplacement n'aide plus.

## Superposition autochtone

Les figures autochtones suivent deux définitions — l'**identité** (Premières Nations + Métis + Inuits) et la **langue maternelle** (première langue autochtone) — en superposition sur la simulation principale. Choix clés :

- Les ancres provinciales sont interpolées entre les années de recensement et sont **approximatives** : elles sont calibrées sur les totaux nationaux publiés (≈312 k en 1971 grimpant à ≈1,81 M en 2021) et sur les concentrations territoriales connues, mais non réconciliées cellule par cellule.
- Le dénominateur utilise la population provinciale **réelle**, et **les T.N.-O. + le Nunavut sont fusionnés** pour éviter l'artefact de la scission territoriale de 1999.
- La projection suppose que la fécondité converge vers le niveau national **sous le remplacement** : l'accroissement naturel reste positif pendant quelques décennies par momentum de la structure d'âge, puis devient négatif — de sorte que la population culmine vers le milieu du siècle et décline.

## Réserves à énoncer clairement

- Une projection à 2100 est une **illustration d'hypothèses**, non une prévision. De petits changements au volume d'immigration ou à la fécondité se composent sur 75 ans.
- Comme le modèle ne porte aucune structure d'âge, l'accroissement naturel est un unique taux net par province — il ne peut capter le momentum d'une pyramide des âges jeune ou vieille que dans la mesure où la courbe de ce taux est dessinée en conséquence.
- Le *plateau* apparent de fin de siècle dans la part du Québec est un **transitoire figé** : il reflète le choix de modélisation de maintenir le volume d'immigration à peu près constant après 2050. Sous une hypothèse d'immigration proportionnelle à la population, la part continuerait de chuter vers la part d'≈8 % des arrivées au Québec.
- **Les coudes visibles suivent les années d'ancrage, pas des événements.** Parce que chaque entrée est une courbe linéaire par morceaux entre quelques années d'ancrage (§Paramètres du modèle), la sortie peut plier brusquement là où deux segments se rejoignent. La *population totale* du Québec, par exemple, semble **plafonner vers 2030** — non pas parce que quelque chose survient cette année-là, mais parce que son taux de croissance nette est ancré à environ **+2,7 %/an en 2024 et −1,3 %/an en 2030, sans point entre les deux**. La descente interpolée croise le zéro à la fin des années 2020, de sorte que pendant quelques années le changement naturel négatif de la province (≈−125 k/an) annule presque exactement son afflux d'immigration (≈+110 k/an) ; la croissance reprend ensuite à mesure que la rampe d'immigration continue de monter. Le « coude » de 2030 est donc un artefact de la position des ancres — déplacez ou ajoutez des ancres et il se déplace avec elles — alors lisez ces courbes pour leur tendance, non pour leur forme d'une année à l'autre. La **direction** de cette ancre QC post-2025 (le changement naturel devenant négatif à la fin des années 2020) n'est pas arbitraire : l'Institut de la statistique du Québec a déjà enregistré plus de décès que de naissances au Québec en 2024–2025 et projette un **accroissement naturel négatif dès 2027** [15], et les projections officielles de StatCan (cat. 91-520-X) montrent le poids démographique du Québec en baisse jusqu'en 2048 [14]. La **magnitude** du modèle (≈ −1,3 %/an, plus abrupte que ces projections officielles) demeure l'hypothèse propre du modélisateur, non un chiffre sourcé.
- Les groupes linguistiques désignent la **langue d'usage**, non l'origine ethnique ou l'ascendance. Un ménage trilingue déclarant l'anglais à la maison compte ici comme anglophone.
- Les trajectoires de **population** sont calibrées sur le recensement provincial ; la dimension **linguistique** l'est plus librement. En particulier, la part du français à la maison *à l'intérieur du Québec* dans le modèle est de quelques points sous le recensement (≈69 % contre ≈78 % en 2021) et, après que la recalibration de la croissance nette de 2026 a rendu le changement naturel du Québec plus négatif, son déclin projeté du français au Québec est du côté abrupt. Traitez les courbes du français québécois comme directionnelles (le français baissant en part) plutôt que comme des niveaux précis.

## Sources

Chaque fichier d'entrée nomme sa base empirique dans son commentaire d'en-tête ; cette section les rassemble. Deux mises en garde honnêtes d'emblée : (a) les valeurs de la **calibration 1971–2025** sont tirées des sources ci-dessous, mais (b) les valeurs de la **projection post-2025** sont les *hypothèses de prolongation de tendance* du modélisateur bâties par-dessus — non elles-mêmes des données sourcées — et plusieurs paramètres de calibration (taux de transfert linguistique et de migration, cellules provinciales autochtones) sont des ajustements **stylisés ou approximatifs** aux études citées plutôt que des transcriptions verbatim. Tous les liens **consultés le 8 juillet 2026**.

| Entrée (`data/…`) | Ce qu'elle définit | Source |
|---|---|---|
| `initial_population_1971.csv` | populations provinciales de 1971 + parts linguistiques | StatCan, Recensement du Canada de 1971 (cat. 92-715) [1] |
| `historical_provincial_population.csv` | population provinciale 1971–2025 (calibration) | Recensement StatCan 1971–2021 [1] ; Estimations de la population, trimestrielles, tableau 17-10-0009-01 (T1 2025) [2] |
| `historical_population.csv` | cibles de population nationale | Recensement StatCan [1] ; estimations trimestrielles, tableau 17-10-0009-01 [2] |
| `historical_francophone_share.csv` | part du français à la maison (calibration) | Recensement StatCan 1971–2021, langue parlée le plus souvent à la maison [1] |
| `immigration_volume.csv` | arrivées annuelles de résidents permanents | données d'arrivées IRCC ; Plan des niveaux d'immigration et Rapport annuel au Parlement [3] |
| `immigration_composition.csv` | part fr/en des immigrants (QC vs RDC) | OQLF [4] / MIFI du Québec [5] (QC) ; cibles d'immigration francophone IRCC [3] (RDC) |
| `immigration_provincial_allocation.csv` | part provinciale des arrivées | arrivées IRCC par province de destination prévue [3] |
| `natural_increase.csv` | taux de croissance provincial net | ajusté à la série de population provinciale StatCan, tableau 17-10-0009-01 [2] ; trajectoire sous-remplacement post-2025 corroborée par les Projections de population StatCan (cat. 91-520-X) [14] et, pour le Québec, les projections de l'ISQ [15] |
| `interprovincial_migration.csv` | probabilités annuelles de déplacement | StatCan tableau 17-10-0015-01, migrants interprovinciaux [6] |
| `migration_language_multipliers.csv` | mobilité conditionnelle à la langue | études de mobilité linguistique du Recensement StatCan / BDIM [1][7] |
| `language_transfer_matrices.csv` | taux annuels de substitution linguistique | StatCan, Projections linguistiques pour le Canada 2011–2036 (cat. 89-657-X) [8] ; OQLF [4] |
| `indigenous_population.csv` | ancres d'identité et de langue maternelle autochtones | Recensement StatCan 1971–2021 (identité autochtone ; langue maternelle autochtone) [1] |
| `indigenous_natural_increase.csv` | accroissement naturel autochtone après 2021 | projections de population autochtone StatCan [1] ; hypothèse de convergence des PPNU 2022 [9] |
| `fg_age_sex_1971.csv` | structure par âge et sexe de 1971 | StatCan, Recensement de 1971 (cat. 92-715) [1] |
| `fg_fertility.csv` | fécondité par âge | StatCan tableau 13-10-0418-01 [10] ; PPNU 2022 (projections) [9] |
| `fg_life_tables.csv` | mortalité *q*(âge, sexe) | Tables de mortalité StatCan 2018–2020 (cat. 84-537-X) [11] ; Human Mortality Database [12] ; PPNU 2022 [9] |
| `fg_emigration.csv` | taux d'émigration | Programme des estimations démographiques StatCan (91-209-X) [13] ; OCDE |
| `fg_immigrant_age_sex.csv` | profil âge-sexe des immigrants | BDIM StatCan [7] ; rapports annuels IRCC [3] ; PPNU 2022 [9] |

**Liens de référence** (consultés le 8 juillet 2026) :

1. Statistique Canada — Programme du recensement — <https://www12.statcan.gc.ca/census-recensement/index-fra.cfm>
2. StatCan tableau 17-10-0009-01, *Estimations de la population, trimestrielles* — <https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1710000901>
3. Immigration, Réfugiés et Citoyenneté Canada (IRCC) — *Plan des niveaux d'immigration / Rapport annuel au Parlement* — <https://www.canada.ca/fr/immigration-refugies-citoyennete.html>
4. Office québécois de la langue française (OQLF) — <https://www.oqlf.gouv.qc.ca/>
5. Québec — Ministère de l'Immigration, de la Francisation et de l'Intégration (MIFI) — <https://www.quebec.ca/immigration>
6. StatCan tableau 17-10-0015-01, *Migrants interprovinciaux* — <https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1710001501>
7. StatCan — Base de données longitudinales sur l'immigration (BDIM) — <https://www.statcan.gc.ca/fr/sujets-debut/immigration_et_diversite_ethnoculturelle>
8. StatCan — *Projections linguistiques pour le Canada, 2011 à 2036* (cat. 89-657-X) — <https://www150.statcan.gc.ca/n1/fr/catalogue/89-657-X>
9. Nations Unies — *Perspectives de la population mondiale 2022* — <https://population.un.org/wpp/>
10. StatCan tableau 13-10-0418-01, *Taux de fécondité par âge* — <https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1310041801>
11. StatCan — *Tables de mortalité, Canada, provinces et territoires* (cat. 84-537-X) — <https://www150.statcan.gc.ca/n1/fr/catalogue/84-537-X>
12. Human Mortality Database — <https://www.mortality.org/>
13. StatCan — *Programme des estimations démographiques* (cat. 91-209-X) — <https://www150.statcan.gc.ca/n1/fr/catalogue/91-209-X>
14. StatCan — *Projections de la population du Canada, des provinces et des territoires* (cat. 91-520-X) — <https://www150.statcan.gc.ca/n1/fr/catalogue/91-520-X>
15. Institut de la statistique du Québec (ISQ) — *Perspectives démographiques, Québec* (2021→2071 ; mise à jour 2025) — <https://statistique.quebec.ca/fr/document/perspectives-demographiques-du-quebec>
16. StatCan tableau 17-10-0008-01, *Estimations des composantes de l'accroissement démographique, annuelles* (naissances, décès, accroissement naturel par province) — <https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1710000801>

Les publications à numéro de catalogue (p. ex. 92-715, le Recensement de 1971) sont identifiées par leur numéro de catalogue StatCan et accessibles via le Programme du recensement [1] et le catalogue de StatCan. Là où un commentaire d'en-tête cite une valeur comme « stylisée », « approximative » ou « illustrative », traitez la source comme la *référence de calibration* de ce paramètre, non comme une citation cellule par cellule.

## Données

Toutes les entrées vivent dans de simples fichiers CSV et l'ensemble du site fonctionne à partir d'un unique export JSON de **185 Ko** de la simulation — sans dorsale, sans base de données, sans analytique.

Le code source complet — code de simulation, données d'entrée et ce site web — est disponible sur GitHub à [github.com/centuryinitiative/centuryinitiative.github.io](https://github.com/centuryinitiative/centuryinitiative.github.io).

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
