"""
Export simulation output to a compact JSON bundle for the web app
(site/src/data/canada.json). Re-run whenever the model or data changes:

    python3 export_web_data.py

Schema (columnar, one array per year to stay small):
{
  "meta": { years[], provinces[], province_names{}, languages[],
            language_names{}, scenarios[], note },
  "series":     { <scenario>: { <prov>: { <lang>: [pop per year] } } },
  "indigenous": { identity{prov:[]}, mothertongue{prov:[]},
                  denominator{prov:[]} },  # persons; share = identity/denominator
  "calibration": { anchors[], population_thousands{prov:[]} }  # census targets
}
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canada_sim import CanadaSimulator
from loaders import (
    PROVINCES, P_IDX, L_IDX, DATA_DIR, _read_csv,
    load_immigration_volume_fn,
    load_immigration_composition_fns,
    load_immigration_provincial_alloc_fn,
    load_language_transfer_fn,
    load_natural_increase_fn,
    load_migration_lang_multipliers,
    load_scenarios,
)

SCENARIOS = ["low", "mid", "high"]
LANGS = ["fr", "en", "allo"]

PROV_FULL = {
    "NL": "Newfoundland & Labrador", "PE": "Prince Edward Island",
    "NS": "Nova Scotia", "NB": "New Brunswick", "QC": "Quebec",
    "ON": "Ontario", "MB": "Manitoba", "SK": "Saskatchewan",
    "AB": "Alberta", "BC": "British Columbia", "YT": "Yukon",
    "NT": "Northwest Territories", "NU": "Nunavut",
}
LANG_FULL = {"fr": "Francophone", "en": "Anglophone", "allo": "Allophone"}

OUT_PATH = os.path.join("site", "src", "data", "canada.json")


def run_scenario(scen):
    print(f"  running {scen} ...", flush=True)
    sim = CanadaSimulator(scenario_name=scen, scale=100, seed=42)
    sim.run(until_year=2150, verbose=False)
    return sim.history


def build_params(years):
    """Export the model's *input* parameters (not outputs) as year-indexed
    arrays, so the methodology page can render live diagnostic charts that
    mirror the P01–P08 matplotlib plots. Scenario logic mirrors
    CanadaSimulator._imm_volume / _imm_fr_share."""
    r5 = lambda x: round(float(x), 6)

    vol_fn = load_immigration_volume_fn()
    fr_qc_fn, en_qc_fn, fr_roc_fn, en_roc_fn = load_immigration_composition_fns()
    alloc_fn = load_immigration_provincial_alloc_fn()
    lt_fn = load_language_transfer_fn()
    ni_fn = load_natural_increase_fn()
    mult = load_migration_lang_multipliers()          # (NP, NL)
    scen = load_scenarios()

    def imm_volume(scenario, y):
        v = vol_fn(y)
        if y > 2025:
            v *= scen[scenario]["volume_multiplier_post2025"]
        return v

    def fr_share(scenario, region, y):
        base = fr_qc_fn(y) if region == "QC" else fr_roc_fn(y)
        if y > 2025:
            override = scen[scenario].get("roc_fr_share_post2025")
            if region == "ROC" and override is not None:
                return max(0.0, min(1.0, override))
            base += scen[scenario]["fr_share_offset_post2025"]
        return max(0.0, min(1.0, base))

    SC = ["low", "mid", "high"]

    # Immigration volume by scenario (P01)
    immigration_volume = {s: [int(round(imm_volume(s, y))) for y in years] for s in SC}

    # Effective francophone fraction of the whole immigration stream (P04):
    #   alloc_QC * fr_QC + (1 - alloc_QC) * fr_ROC
    def eff_fr(scenario, y):
        aqc = float(alloc_fn(y)[P_IDX["QC"]])
        return aqc * fr_share(scenario, "QC", y) + (1 - aqc) * fr_share(scenario, "ROC", y)
    effective_fr_fraction = {s: [r5(eff_fr(s, y)) for y in years] for s in SC}

    # Francophone share of immigrants, per region, per scenario (P07)
    imm_fr_share = {
        reg: {s: [r5(fr_share(s, reg, y)) for y in years] for s in SC}
        for reg in ("QC", "ROC")
    }

    # QC immigrant composition, base/mid (P02 left): fr / en / allo
    imm_composition_qc = {
        "fr":   [r5(fr_qc_fn(y)) for y in years],
        "en":   [r5(en_qc_fn(y)) for y in years],
        "allo": [r5(max(0.0, 1 - fr_qc_fn(y) - en_qc_fn(y))) for y in years],
    }

    # Provincial allocation of immigration, all provinces (P03)
    provincial_allocation = {
        p: [r5(alloc_fn(y)[P_IDX[p]]) for y in years] for p in PROVINCES
    }

    # Net natural-increase rate, all provinces (P06)
    natural_increase = {
        p: [r5(ni_fn(y)[P_IDX[p]]) for y in years] for p in PROVINCES
    }

    # Annual language-transfer rates for representative provinces (P05)
    lt_pairs = {"fr_en": (0, 1), "fr_allo": (0, 2),
                "en_fr": (1, 0), "allo_en": (2, 1), "allo_fr": (2, 0)}
    language_transfer = {
        prov: {
            name: [r5(lt_fn(y)[P_IDX[prov], fl, tl]) for y in years]
            for name, (fl, tl) in lt_pairs.items()
        }
        for prov in ("QC", "ON", "NB")
    }

    # Static interprovincial migration language multipliers (P08)
    migration_multipliers = {
        p: {l: r5(mult[P_IDX[p], L_IDX[l]]) for l in LANGS} for p in PROVINCES
    }

    return {
        "immigration_volume": immigration_volume,
        "effective_fr_fraction": effective_fr_fraction,
        "imm_fr_share": imm_fr_share,
        "imm_composition_qc": imm_composition_qc,
        "provincial_allocation": provincial_allocation,
        "natural_increase": natural_increase,
        "language_transfer": language_transfer,
        "migration_multipliers": migration_multipliers,
    }


def build_calibration():
    """Export the raw provincial-population calibration targets (the actual
    census / quarterly-estimate anchor values the coarse model is fit to) so
    the methodology page can render them straight from data rather than a
    hand-copied literal. Values are thousands of persons at each anchor year;
    pre-1999 Nunavut (carried under NT) is exported as null."""
    rows = _read_csv(os.path.join(DATA_DIR, "historical_provincial_population.csv"))
    anchors = [int(r["year"]) for r in rows]
    population = {
        p: [(round(float(r[p]), 1) if float(r[p]) != 0.0 else None) for r in rows]
        for p in PROVINCES
    }
    return {"anchors": anchors, "population_thousands": population}


def main():
    print("Running scenarios for web export:")
    histories = {s: run_scenario(s) for s in SCENARIOS}
    years = [int(r["year"]) for r in histories["mid"]]

    series = {
        s: {
            p: {l: [int(r[f"{p}_{l}"]) for r in histories[s]] for l in LANGS}
            for p in PROVINCES
        }
        for s in SCENARIOS
    }

    # Indigenous overlay (identity + mother tongue) with the hybrid real denominator
    print("  computing Indigenous overlay ...", flush=True)
    import plot_indigenous as pi
    iyears, prov_total, _national = pi.run_base_totals()
    assert list(map(int, iyears)) == years, "Indigenous year grid mismatch"
    identity, mother = pi.build_indigenous_series(iyears)
    indigenous = {
        "identity": {p: [int(round(x)) for x in identity[p]] for p in PROVINCES},
        "mothertongue": {p: [int(round(x)) for x in mother[p]] for p in PROVINCES},
        "denominator": {p: [int(round(x)) for x in prov_total[p]] for p in PROVINCES},
    }

    out = {
        "meta": {
            "years": years,
            "provinces": PROVINCES,
            "province_names": PROV_FULL,
            "languages": LANGS,
            "language_names": LANG_FULL,
            "scenarios": SCENARIOS,
            "note": ("Counts are real people. 1971-2025 calibration, "
                     "2025-2150 projection (mid scenario ~100M by 2100)."),
        },
        "series": series,
        "indigenous": indigenous,
        "params": build_params(years),
        "calibration": build_calibration(),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    kb = os.path.getsize(OUT_PATH) / 1024
    print(f"\nWrote {OUT_PATH}  ({kb:.0f} KB, {len(years)} years, "
          f"{len(SCENARIOS)} scenarios)")


if __name__ == "__main__":
    main()
