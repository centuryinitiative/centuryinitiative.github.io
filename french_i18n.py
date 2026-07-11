"""
French translation layer for all Canada_pop figures/videos.

Used by make_french.py, which monkeypatches matplotlib so every rendered string
is routed through `translate()` and every saved file gets a `_fr` suffix. The
plotting scripts themselves are NOT modified.

`translate(s)` strategy:
  1. exact match in FR          (full titles, labels, legends, footers)
  2. regex PATTERNS             (dynamic titles with interpolated values)
  3. return unchanged           (numbers, codes, format strings) and — if the
                                string looks like prose — record it in MISSES
                                so gaps can be found after a dry run.
Translating twice is safe: French output strings are never keys, so
translate(translate(x)) == translate(x).
"""
import re

# Scenario adjectives (used inside dynamic patterns)
SCEN = {
    "low": "faible", "mid": "intermédiaire", "high": "élevé",
    "Low": "Faible", "Mid": "Intermédiaire", "High": "Élevé",
}

# ── Exact-match dictionary (figure-visible strings only) ─────────────────────
FR = {
    # -- language groups / regions ------------------------------------------
    "Francophone": "Francophones",
    "Anglophone": "Anglophones",
    "Allophone": "Allophones",
    "Allophone (base)": "Allophones (base)",
    "Language group": "Groupe linguistique",
    "ROC": "RDC",
    "ROC (Ontario)": "RDC (Ontario)",
    "ON (repr. ROC)": "ON (représente le RDC)",
    "Rest of Canada": "Reste du Canada",
    "Atlantic": "Atlantique",
    "Central": "Centre",
    "Prairies": "Prairies",
    "Pacific & Territories": "Pacifique et territoires",

    # -- province / territory names -----------------------------------------
    "Quebec": "Québec",
    "New Brunswick": "Nouveau-Brunswick",
    "Nova Scotia": "Nouvelle-Écosse",
    "British Columbia": "Colombie-Britannique",
    "Ontario": "Ontario",
    "Manitoba": "Manitoba",
    "Saskatchewan": "Saskatchewan",
    "Alberta": "Alberta",
    "Yukon": "Yukon",
    "Nunavut": "Nunavut",
    "PEI": "Î.-P.-É.",
    "Nfld & Lab.": "T.-N.-L.",
    "Northwest Terr.": "Terr. du Nord-Ouest",
    "NT + Nunavut": "T.N.-O. + Nunavut",

    # -- common axis labels --------------------------------------------------
    "Year": "Année",
    "Population": "Population",
    "Population (millions)": "Population (millions)",
    "Province": "Province",
    "Share (%)": "Part (%)",
    "Ratio": "Rapport",
    "Thousands": "Milliers",
    "Age": "Âge",
    "Rate (%/yr)": "Taux (%/an)",
    "Rate (‰/yr)": "Taux (‰/an)",
    "Francophone share (%)": "Part francophone (%)",
    "Francophone share in QC (%)": "Part francophone au QC (%)",
    "Francophone share in ROC (%)": "Part francophone dans le RDC (%)",
    "Francophone share of Canada (%)": "Part francophone du Canada (%)",
    "Francophones (millions)": "Francophones (millions)",
    "QC francophone share (%)": "Part francophone du QC (%)",
    "QC francophones / Canada total (%)": "Francophones du QC / total du Canada (%)",
    "Quebec share (%)": "Part du Québec (%)",
    "Quebec share of Canada (%)": "Part du Québec dans le Canada (%)",
    "Share of Canada (%)": "Part du Canada (%)",
    "Annual landings (thousands)": "Arrivées annuelles (milliers)",
    "Share of annual landings (%)": "Part des arrivées annuelles (%)",
    "fr share of annual immigrants (%)": "part fr des immigrants annuels (%)",
    "Francophone share of annual immigrants (%)": "Part francophone des immigrants annuels (%)",
    "Change (thousands)": "Variation (milliers)",
    "Out-migration multiplier (1.0 = same as average)": "Multiplicateur d’émigration (1,0 = identique à la moyenne)",
    "Number of francophones": "Nombre de francophones",
    "Number of individuals": "Nombre d’individus",
    "Total population (individuals)": "Population totale (individus)",
    "Natural increase (thousands/yr, 5-yr avg)": "Accroissement naturel (milliers/an, moy. 5 ans)",
    "Net migration (thousands/yr)": "Migration nette (milliers/an)",
    "Annual births (5-yr avg)": "Naissances annuelles (moy. 5 ans)",
    "Annual change in fr share (pp/yr)": "Variation annuelle de la part fr (pp/an)",
    "Gap (percentage points)": "Écart (points de pourcentage)",
    "Gap (pp, log scale)": "Écart (pp, échelle log)",
    "Gap f(t) − f_imm (linear)": "Écart f(t) − f_imm (linéaire)",
    "Gap f(t) − f_imm (log scale)": "Écart f(t) − f_imm (échelle log)",
    "Millions (◀ M | F ▶)": "Millions (◀ H | F ▶)",

    # -- legends / small labels ---------------------------------------------
    "Male": "Hommes",
    "Female": "Femmes",
    "Female  ▶": "Femmes  ▶",
    "◀  Male": "◀  Hommes",
    "Low scenario": "Scénario faible",
    "Mid scenario": "Scénario intermédiaire",
    "High scenario": "Scénario élevé",
    # bare scenario legend labels (from scen.capitalize())
    "Low": "Faible",
    "Mid": "Intermédiaire",
    "High": "Élevé",
    "Mid baseline": "Référence intermédiaire",
    "Mid baseline (default trajectory)": "Référence intermédiaire (trajectoire par défaut)",
    "4% ROC (back to pre-2015 baseline)": "4 % RDC (retour à la référence d’avant 2015)",
    "6% ROC (partial retrenchment)": "6 % RDC (repli partiel)",
    "8% ROC (near-current level sustained)": "8 % RDC (niveau quasi actuel maintenu)",
    "Census (StatCan)": "Recensement (StatCan)",
    "Simulated history (1971–2021)": "Historique simulé (1971–2021)",
    "calibration | projection": "calage | projection",
    "Proj. start": "Début proj.",
    "Projection start": "Début de la projection",
    "2050 plateau": "plateau 2050",
    "2050 slowdown": "ralentissement 2050",
    "Gap drives dilution": "L’écart provoque la dilution",
    "Incoming immigrant fr% (mid)": "Part fr% des immigrants entrants (intermédiaire)",
    "Immigration dilution": "Dilution par l’immigration",
    "Language transfer + natural increase": "Transfert linguistique + accroissement naturel",
    "Total Δf": "Δf total",
    "← policy gap →": "← écart de politique →",
    "diff%": "écart%",
    # language-transfer shorthand (fr/en/allo codes identical in French)
    "fr→en": "fr→en", "fr→allo": "fr→allo", "en→fr": "en→fr",
    "allo→fr": "allo→fr", "allo→en": "allo→en",
    "Indigenous identity": "Identité autochtone",
    "Indigenous mother tongue": "Langue maternelle autochtone",
    "Canada (all)": "Canada (ensemble)",
    "Age-structured history not stored\n(compute from fg01 pyramid)":
        "Historique par âge non stocké\n(calculer à partir de la pyramide fg01)",

    # -- titles: coarse sim (01–10, P01–P09) --------------------------------
    "Canada Total Population (1971–2150)": "Population totale du Canada (1971–2150)",
    "National Francophone Share (1971–2150)": "Part francophone nationale (1971–2150)",
    "Quebec Francophone Share (1971–2150)": "Part francophone du Québec (1971–2150)",
    "National Language Breakdown — Mid Scenario (1971–2150)":
        "Répartition linguistique nationale — scénario intermédiaire (1971–2150)",
    "Population by Province — Mid Scenario (1971–2150)":
        "Population par province — scénario intermédiaire (1971–2150)",
    "Language Shares — Key Provinces — Mid Scenario (1971–2150)":
        "Parts linguistiques — provinces clés — scénario intermédiaire (1971–2150)",
    "Annual Population Change — Mid Scenario (1971–2150)":
        "Variation annuelle de la population — scénario intermédiaire (1971–2150)",
    "Provincial Language Composition Snapshots — Mid Scenario":
        "Instantanés de composition linguistique provinciale — scénario intermédiaire",
    "Quebec's Share of Canada Total Population (1971–2150)":
        "Part du Québec dans la population totale du Canada (1971–2150)",
    "Quebec Francophones as Share of Canada Total Population (1971–2150)":
        "Francophones du Québec en proportion de la population totale du Canada (1971–2150)",
    "Forces behind post-2050 francophone share deceleration":
        "Forces derrière la décélération de la part francophone après 2050",
    "P01 — Immigration Volume by Scenario": "P01 — Volume d’immigration par scénario",
    "P02 — Language Share of QC immigrants": "P02 — Part linguistique des immigrants du QC",
    "P02 — Language Share of ROC immigrants": "P02 — Part linguistique des immigrants du RDC",
    "P03 — Provincial Allocation of Immigration (key provinces)":
        "P03 — Répartition provinciale de l’immigration (provinces clés)",
    "P04 — Effective Francophone Fraction of Immigration Stream (mid)":
        "P04 — Fraction francophone effective du flux d’immigration (intermédiaire)",
    "P08 — Interprovincial Migration Language Multipliers (static)":
        "P08 — Multiplicateurs linguistiques de migration interprovinciale (statique)",
    "P09 — QC Francophone Share of Immigrants": "P09 — Part francophone des immigrants du QC",
    "P09 — QC Natural Increase Rate": "P09 — Taux d’accroissement naturel du QC",

    # -- titles: extra plots (E01–E07) --------------------------------------
    "E01 — Dilution Gap: National Fr Share minus Immigrant Fr Share":
        "E01 — Écart de dilution : part fr nationale moins part fr des immigrants",
    "E02 — National Francophone Share f(t) vs. Immigrant Fr Share f_imm (1971–2150)":
        "E02 — Part francophone nationale f(t) c. part fr des immigrants f_imm (1971–2150)",
    "E03 — Absolute Francophone Population, Canada (1971–2150)":
        "E03 — Population francophone absolue, Canada (1971–2150)",
    "E04 — ROC Francophone Share (Outside Quebec) (1971–2150)":
        "E04 — Part francophone du RDC (hors Québec) (1971–2150)",
    "E05 — New Brunswick Language Shares (1971–2150)":
        "E05 — Parts linguistiques du Nouveau-Brunswick (1971–2150)",
    "E07 — Stabilization Threshold: Required vs Actual Immigrant Fr Share (1971–2150)":
        "E07 — Seuil de stabilisation : part fr des immigrants requise c. réelle (1971–2150)",

    # -- titles: bar races (coarse) -----------------------------------------
    "Provincial Francophone Population — Mid Scenario (1971–2150)":
        "Population francophone provinciale — scénario intermédiaire (1971–2150)",
    "Provincial Total Population — Mid Scenario (1971–2150)":
        "Population totale provinciale — scénario intermédiaire (1971–2150)",
    "National Language Group Populations — Mid Scenario (1971–2150)":
        "Populations des groupes linguistiques nationaux — scénario intermédiaire (1971–2150)",
    "Provincial Francophone Share — Mid Scenario (1971–2150)":
        "Part francophone provinciale — scénario intermédiaire (1971–2150)",

    # -- titles / labels: fine-grain (fg) -----------------------------------
    "Fine-Grain Canada Population Simulator": "Simulateur détaillé de la population du Canada",
    "Total Canadian Population": "Population canadienne totale",
    "Total Canada Population": "Population totale du Canada",
    "National Francophone Share": "Part francophone nationale",
    "Quebec Francophone Share": "Part francophone du Québec",
    "Births and Deaths": "Naissances et décès",
    "Annual Births": "Naissances annuelles",
    "Annual Deaths": "Décès annuels",
    "Annual Natural Increase (Births − Deaths)": "Accroissement naturel annuel (naissances − décès)",
    "Annual Net Migration (Immigrants − Emigrants)": "Migration nette annuelle (immigrants − émigrants)",
    "Old-Age Dependency Ratio (65+ / 15–64)": "Rapport de dépendance des aînés (65+ / 15–64)",
    "Language Composition — Mid Scenario (1971–2100)":
        "Composition linguistique — scénario intermédiaire (1971–2100)",
    "National Language Group Populations — Mid Scenario (1971–2100)":
        "Populations des groupes linguistiques nationaux — scénario intermédiaire (1971–2100)",
    "Population Age Pyramid — Mid Scenario (1971–2100)":
        "Pyramide des âges de la population — scénario intermédiaire (1971–2100)",
    "Provincial Annual Births — Mid Scenario (1971–2100)":
        "Naissances annuelles provinciales — scénario intermédiaire (1971–2100)",
    "Provincial Francophone Population — Mid Scenario (1971–2100)":
        "Population francophone provinciale — scénario intermédiaire (1971–2100)",
    "Provincial Total Population — Mid Scenario (1971–2100)":
        "Population totale provinciale — scénario intermédiaire (1971–2100)",
    "Provincial Francophone Share — Mid Scenario (1971–2100)":
        "Part francophone provinciale — scénario intermédiaire (1971–2100)",

    # -- titles / labels: Indigenous (IND) ----------------------------------
    "Indigenous share of Canada's population\n1971-2150 · identity vs. mother tongue":
        "Part autochtone de la population du Canada\n1971-2150 · identité c. langue maternelle",
    "Indigenous-identity share by province\nhighest-share provinces + national, 1971-2150":
        "Part d’identité autochtone par province\nprovinces à plus forte part + national, 1971-2150",
    "Indigenous population of Canada (absolute)\nidentity vs. mother tongue, 1971-2150":
        "Population autochtone du Canada (absolue)\nidentité c. langue maternelle, 1971-2150",
    "Indigenous-language retention\nmother-tongue speakers as a share of the identity population":
        "Rétention des langues autochtones\nlocuteurs de langue maternelle en part de la population d’identité",
    "Indigenous-identity share (%)": "Part d’identité autochtone (%)",
    "Mother tongue ÷ identity (%)": "Langue maternelle ÷ identité (%)",
    "Provincial Indigenous-identity Share (%) — 1971-2100":
        "Part d’identité autochtone provinciale (%) — 1971-2100",
    "Provincial Indigenous-identity Population — 1971-2100":
        "Population d’identité autochtone provinciale — 1971-2100",
    "Indigenous identity, share of provincial population (%)":
        "Identité autochtone, part de la population provinciale (%)",
    "Indigenous identity population (individuals)":
        "Population d’identité autochtone (individus)",

    # -- titles: misc standalone --------------------------------------------
    "Immigrant Landings: Quebec vs. Rest of Canada (1971-2150)":
        "Arrivées d’immigrants : Québec c. reste du Canada (1971-2150)",
    "Effective Francophone Share of Immigrants to Canada (1971–2150)":
        "Part francophone effective des immigrants au Canada (1971–2150)",
    "Quebec's share of Canada's population\n1971–2150 · agent-based simulation":
        "Part du Québec dans la population du Canada\n1971–2150 · simulation à base d’agents",
    "National Francophone Share — ROC immigration fr% sensitivity\n1971–2150 · agent-based simulation":
        "Part francophone nationale — sensibilité à la part fr% de l’immigration du RDC\n1971–2150 · simulation à base d’agents",
    "Quebec Francophones as Share of Canada Total Population\nROC immigration fr% sensitivity · 1971–2150":
        "Francophones du Québec en proportion de la population totale du Canada\nsensibilité à la part fr% de l’immigration du RDC · 1971–2150",

    # -- source footers ------------------------------------------------------
    "Sources: StatCan Census 1951–2021; Q1 2025 estimate. "
    "Simulation: agent-based model with empirical 1971–2025 calibration.":
        "Sources : recensements StatCan 1951–2021 ; estimation T1 2025. "
        "Simulation : modèle à base d’agents avec calage empirique 1971–2025.",
    "ROC fr% held flat from 2026 onward. QC selection unchanged. "
    "Immigration volume = mid scenario.":
        "Part fr% du RDC maintenue constante à partir de 2026. Sélection du QC inchangée. "
        "Volume d’immigration = scénario intermédiaire.",
    "Sources: StatCan Census 1971-2021 (Indigenous identity & mother tongue), "
    "approximate provincial anchors — see data/indigenous_*.csv. Total population "
    "from the project's agent-based simulation (mid scenario).":
        "Sources : recensements StatCan 1971-2021 (identité et langue maternelle "
        "autochtones), ancrages provinciaux approximatifs — voir data/indigenous_*.csv. "
        "Population totale issue du modèle à base d’agents du projet (scénario intermédiaire).",
}

# ── Regex patterns for dynamic (interpolated) strings ────────────────────────
# Each: (compiled_regex, builder(match) -> french). Captured fragments are
# recursively translated so embedded province/scenario names are handled.
_suffix = {
    "f(t)": "f(t)", "f_imm": "f_imm",
    "required f_imm": "f_imm requis", "actual f_imm": "f_imm réel",
}

def _scen_word(w):
    return SCEN.get(w, w)

PATTERNS = [
    (re.compile(r"^P05 — Annual Language Transfer Rates — (.+)$"),
     lambda m: f"P05 — Taux annuels de transfert linguistique — {translate(m.group(1))}"),
    (re.compile(r"^P06 — Natural Increase Rate — (.+)$"),
     lambda m: f"P06 — Taux d’accroissement naturel — {translate(m.group(1))}"),
    (re.compile(r"^P07 — Effective fr% of (.+) Immigrants by Scenario$"),
     lambda m: f"P07 — Part fr% effective des immigrants {translate(m.group(1))} par scénario"),
    (re.compile(r"^E06 — Annual Δf Decomposition — Mid Scenario \((\d+)-yr smoothed\)$"),
     lambda m: f"E06 — Décomposition annuelle de Δf — scénario intermédiaire (lissé sur {m.group(1)} ans)"),
    (re.compile(r"^Population Pyramid — (.+?) \((\w+) scenario\)$"),
     lambda m: f"Pyramide des âges — {m.group(1)} (scénario {_scen_word(m.group(2))})"),
    (re.compile(r"^Population Pyramid — (.+)$"),
     lambda m: f"Pyramide des âges — {translate(m.group(1))}"),
    (re.compile(r"^(low|mid|high|Low|Mid|High) — (f\(t\)|f_imm|required f_imm|actual f_imm)$"),
     lambda m: f"{_scen_word(m.group(1))} — {_suffix[m.group(2)]}"),
    (re.compile(r"^(Low|Mid|High) \(offset ([+-]?\d+\.\d+)\)$"),
     lambda m: f"{_scen_word(m.group(1))} (décalage {m.group(2)})"),
    (re.compile(r"^(.+) — Language Shares$"),
     lambda m: f"{translate(m.group(1))} — parts linguistiques"),
    (re.compile(r"^Fr — (.+)$"),
     lambda m: f"Fr — {translate(m.group(1))}"),
    (re.compile(r"^Year (\d+)$"),
     lambda m: f"Année {m.group(1)}"),
    # pie-chart centre label: "<region>\n<pop> people"
    (re.compile(r"^(Quebec|Rest of Canada)\n([\d,]+) people$"),
     lambda m: f"{translate(m.group(1))}\n{m.group(2)} personnes"),
]

# strings we intentionally leave alone (matplotlib loc keywords etc.)
_SKIP = {
    "upper left", "upper right", "lower left", "lower right",
    "center", "center left", "center right", "upper center",
    "lower center", "best",
}

MISSES = set()
# Everything translate() has ever emitted — matplotlib re-calls set_text with
# the already-French string during draw/save, so we must not flag those.
_OUTPUTS = set(FR.values())

def _looks_like_prose(s):
    if s in _SKIP:
        return False
    if s.startswith("$") or "\\mathdefault" in s:   # mathtext tick labels
        return False
    if len(s.strip()) < 4:
        return False
    if not re.search(r"[A-Za-z]{2,}", s):
        return False
    # skip obvious codes / format specs / paths / pure numbers
    if re.fullmatch(r"[\w.\-]+", s) and " " not in s and "\n" not in s:
        # single token — only flag if it has ≥2 words worth of letters and a space
        return False
    if re.search(r"\.(png|mp4|csv|pkl)$", s):
        return False
    return True


def translate(s):
    if not isinstance(s, str) or not s:
        return s
    if s in FR:
        return FR[s]
    if s in _OUTPUTS:          # already-French (re-set during draw/save)
        return s
    for rx, fn in PATTERNS:
        m = rx.match(s)
        if m:
            out = fn(m)
            _OUTPUTS.add(out)
            return out
    if _looks_like_prose(s):
        MISSES.add(s)
    return s
