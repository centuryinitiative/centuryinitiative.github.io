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

// metric display config for the hero map
export const METRICS = {
  pop:      { label: "Population",        scheme: "turbo",   type: "log",    domain: [5e4, 3.2e7], fmt: (v) => `${(v / 1e6).toFixed(2)}M` },
  frshare:  { label: "Francophone share", scheme: "YlGnBu",  type: "linear", domain: [0, 85],      fmt: (v) => `${v.toFixed(1)}%` },
  alloshare:{ label: "Allophone share",   scheme: "PuRd",    type: "linear", domain: [0, 60],      fmt: (v) => `${v.toFixed(1)}%` }
};
