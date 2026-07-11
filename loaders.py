"""
Data loaders for the Canada Population Simulator.

Reads the heavily-commented CSV files in data/ and turns them into
numpy arrays / interpolation functions usable by the simulator.

All CSVs allow `#`-prefixed comment lines and inline comments are not
supported (use the `note` column instead).
"""
from __future__ import annotations
import csv
import os
from typing import Callable
import numpy as np

PROVINCES = [
    "NL", "PE", "NS", "NB", "QC", "ON",
    "MB", "SK", "AB", "BC", "YT", "NT", "NU",
]
P_IDX = {p: i for i, p in enumerate(PROVINCES)}
NP = len(PROVINCES)

LANGUAGES = ["fr", "en", "allo"]
L_IDX = {l: i for i, l in enumerate(LANGUAGES)}
NL = len(LANGUAGES)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_csv(path: str) -> list[dict]:
    """Read CSV, skipping `#` comment lines and blank lines."""
    rows = []
    with open(path, "r") as f:
        # Filter comment/blank lines before passing to DictReader
        clean = [line for line in f if line.strip() and not line.lstrip().startswith("#")]
    reader = csv.DictReader(clean)
    for row in reader:
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Initial population
# ---------------------------------------------------------------------------

def load_initial_population() -> dict:
    """Returns dict: province -> {pop_thousands, fr_share, allo_share}."""
    rows = _read_csv(os.path.join(DATA_DIR, "initial_population_1971.csv"))
    out = {}
    for row in rows:
        p = row["province_code"]
        out[p] = {
            "pop_thousands": float(row["population_thousands"]),
            "fr_share": float(row["fr_share"]),
            "allo_share": float(row["allo_share"]),
        }
    return out


# ---------------------------------------------------------------------------
# Generic linear interpolation helper
# ---------------------------------------------------------------------------

def _interp_fn(years: list[float], values: list[float]) -> Callable[[int], float]:
    """Returns a function that linearly interpolates values at any year, with
    constant extrapolation outside the bounds."""
    years_a = np.array(years, dtype=float)
    values_a = np.array(values, dtype=float)
    order = np.argsort(years_a)
    years_a = years_a[order]
    values_a = values_a[order]

    def f(y: int) -> float:
        if y <= years_a[0]:
            return float(values_a[0])
        if y >= years_a[-1]:
            return float(values_a[-1])
        return float(np.interp(y, years_a, values_a))
    return f


# ---------------------------------------------------------------------------
# Immigration volume
# ---------------------------------------------------------------------------

def load_immigration_volume_fn() -> Callable[[int], float]:
    rows = _read_csv(os.path.join(DATA_DIR, "immigration_volume.csv"))
    years = [int(r["year"]) for r in rows]
    values = [float(r["mid_volume"]) for r in rows]
    return _interp_fn(years, values)


# ---------------------------------------------------------------------------
# Immigration composition (fr_share, en_share)
# ---------------------------------------------------------------------------

def load_immigration_composition_fns() -> tuple[Callable, Callable, Callable, Callable]:
    """Returns (fr_qc_fn, en_qc_fn, fr_roc_fn, en_roc_fn)."""
    rows = _read_csv(os.path.join(DATA_DIR, "immigration_composition.csv"))
    qc_rows = [r for r in rows if r["region"] == "QC"]
    roc_rows = [r for r in rows if r["region"] == "ROC"]
    fr_qc = _interp_fn([int(r["year"]) for r in qc_rows], [float(r["fr_share"]) for r in qc_rows])
    en_qc = _interp_fn([int(r["year"]) for r in qc_rows], [float(r["en_share"]) for r in qc_rows])
    fr_roc = _interp_fn([int(r["year"]) for r in roc_rows], [float(r["fr_share"]) for r in roc_rows])
    en_roc = _interp_fn([int(r["year"]) for r in roc_rows], [float(r["en_share"]) for r in roc_rows])
    return fr_qc, en_qc, fr_roc, en_roc


# ---------------------------------------------------------------------------
# Provincial allocation of immigration
# ---------------------------------------------------------------------------

def load_immigration_provincial_alloc_fn() -> Callable[[int], np.ndarray]:
    rows = _read_csv(os.path.join(DATA_DIR, "immigration_provincial_allocation.csv"))
    years = sorted({int(r["year"]) for r in rows})
    matrix = np.zeros((len(years), NP))
    for ri, r in enumerate(rows):
        y_idx = years.index(int(r["year"]))
        for p_i, p in enumerate(PROVINCES):
            matrix[y_idx, p_i] = float(r[p])
    # normalize each row
    matrix = matrix / matrix.sum(axis=1, keepdims=True)
    years_a = np.array(years, dtype=float)

    def f(y: int) -> np.ndarray:
        if y <= years_a[0]:
            return matrix[0].copy()
        if y >= years_a[-1]:
            return matrix[-1].copy()
        # find bracketing rows
        i = int(np.searchsorted(years_a, y) - 1)
        i = max(0, min(i, len(years_a) - 2))
        t = (y - years_a[i]) / (years_a[i + 1] - years_a[i])
        out = (1 - t) * matrix[i] + t * matrix[i + 1]
        return out / out.sum()
    return f


# ---------------------------------------------------------------------------
# Language transfer matrices
# ---------------------------------------------------------------------------

def load_language_transfer_fn() -> Callable[[int], np.ndarray]:
    """
    Returns f(year) -> ndarray of shape (NP, NL, NL) of annual transition
    probabilities. M[p, from, to] is the prob that an agent in province p
    with home language `from` shifts to `to` in one year. Diagonal entries
    (P(stay)) are computed as 1 - sum(transitions out).
    """
    rows = _read_csv(os.path.join(DATA_DIR, "language_transfer_matrices.csv"))
    # Group by period_year, then accumulate transitions per (province, from, to)
    periods = sorted({int(r["period_year"]) for r in rows})
    # period_matrices[year_idx] = ndarray (NP, NL, NL) of OFF-DIAGONAL probs
    period_matrices = np.zeros((len(periods), NP, NL, NL))

    for r in rows:
        y_idx = periods.index(int(r["period_year"]))
        prov = r["province"]
        f_l = L_IDX[r["from_lang"]]
        t_l = L_IDX[r["to_lang"]]
        prob = float(r["annual_prob"])
        if prov == "ROC":
            # Apply to all provinces that don't have an explicit entry for
            # this period+from+to combo. We do this in a second pass.
            continue
        period_matrices[y_idx, P_IDX[prov], f_l, t_l] = prob

    # Second pass for ROC defaults — only fill if cell still 0
    for r in rows:
        if r["province"] != "ROC":
            continue
        y_idx = periods.index(int(r["period_year"]))
        f_l = L_IDX[r["from_lang"]]
        t_l = L_IDX[r["to_lang"]]
        prob = float(r["annual_prob"])
        for p_i in range(NP):
            if period_matrices[y_idx, p_i, f_l, t_l] == 0:
                period_matrices[y_idx, p_i, f_l, t_l] = prob

    # Compute diagonals
    for y_idx in range(len(periods)):
        for p_i in range(NP):
            for from_l in range(NL):
                off_diag_sum = 0.0
                for to_l in range(NL):
                    if to_l != from_l:
                        off_diag_sum += period_matrices[y_idx, p_i, from_l, to_l]
                period_matrices[y_idx, p_i, from_l, from_l] = 1.0 - off_diag_sum

    # Sanity
    assert np.allclose(period_matrices.sum(axis=3), 1.0), "Lang transfer rows must sum to 1"
    periods_a = np.array(periods, dtype=float)

    def f(y: int) -> np.ndarray:
        if y <= periods_a[0]:
            return period_matrices[0].copy()
        if y >= periods_a[-1]:
            return period_matrices[-1].copy()
        i = int(np.searchsorted(periods_a, y) - 1)
        i = max(0, min(i, len(periods_a) - 2))
        t = (y - periods_a[i]) / (periods_a[i + 1] - periods_a[i])
        out = (1 - t) * period_matrices[i] + t * period_matrices[i + 1]
        # Renormalize each row to be safe
        out = out / out.sum(axis=2, keepdims=True)
        return out
    return f


# ---------------------------------------------------------------------------
# Interprovincial migration matrix
# ---------------------------------------------------------------------------

def load_migration_matrix_fn(default_other: float = 0.0008) -> Callable[[int], np.ndarray]:
    """
    Returns f(year) -> ndarray (NP, NP) of annual interprovincial move probs.
    Diagonal computed automatically as 1 - sum(off-diagonal).

    The unlisted-pair "trickle" is gravity-weighted by destination population
    share rather than applied as a flat constant. A flat constant lets a
    Quebecer move to Yukon (pop 40k) as readily as the model treats any other
    corridor, which under symmetric exchange diffuses the whole country toward
    EQUAL provincial populations — ballooning the territories ~30x and draining
    QC/ON. Weighting destinations by size keeps `default_other` as the trickle
    for an average-sized destination while scaling tiny territories down and
    large provinces up.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "interprovincial_migration.csv"))
    periods = sorted({int(r["period_year"]) for r in rows})

    # Destination population weights (1971 census shares as a static proxy for
    # the trickle's destination preference). pop_w[j] sums to 1 over provinces.
    init_pop = load_initial_population()
    pop_w = np.array([init_pop[p]["pop_thousands"] for p in PROVINCES], dtype=float)
    pop_w = pop_w / pop_w.sum()
    # default cell[i, j] = default_other * NP * pop_w[j]: preserves the overall
    # trickle budget (mean cell == default_other) but routes it by destination size.
    default_cells = default_other * NP * pop_w[np.newaxis, :]
    period_matrices = np.broadcast_to(
        default_cells, (len(periods), NP, NP)
    ).copy()
    for y_idx in range(len(periods)):
        for i in range(NP):
            period_matrices[y_idx, i, i] = 0.0  # diagonal handled later

    for r in rows:
        y_idx = periods.index(int(r["period_year"]))
        f_p = P_IDX[r["from_province"]]
        t_p = P_IDX[r["to_province"]]
        period_matrices[y_idx, f_p, t_p] = float(r["annual_prob"])

    # Compute diagonal
    for y_idx in range(len(periods)):
        for i in range(NP):
            off = period_matrices[y_idx, i].sum() - period_matrices[y_idx, i, i]
            period_matrices[y_idx, i, i] = 1.0 - off

    assert np.allclose(period_matrices.sum(axis=2), 1.0), "Migration rows must sum to 1"
    periods_a = np.array(periods, dtype=float)

    def f(y: int) -> np.ndarray:
        if y <= periods_a[0]:
            return period_matrices[0].copy()
        if y >= periods_a[-1]:
            return period_matrices[-1].copy()
        i = int(np.searchsorted(periods_a, y) - 1)
        i = max(0, min(i, len(periods_a) - 2))
        t = (y - periods_a[i]) / (periods_a[i + 1] - periods_a[i])
        out = (1 - t) * period_matrices[i] + t * period_matrices[i + 1]
        out = out / out.sum(axis=1, keepdims=True)
        return out
    return f


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def load_scenarios() -> dict:
    rows = _read_csv(os.path.join(DATA_DIR, "scenarios.csv"))
    out = {}
    for r in rows:
        roc_override = r.get("roc_fr_share_post2025", "").strip()
        out[r["scenario"]] = {
            "volume_multiplier_post2025": float(r["volume_multiplier_post2025"]),
            "fr_share_offset_post2025": float(r["fr_share_offset_post2025"]),
            "roc_fr_share_post2025": float(roc_override) if roc_override else None,
        }
    return out


# ---------------------------------------------------------------------------
# Calibration targets
# ---------------------------------------------------------------------------

def load_migration_lang_multipliers() -> np.ndarray:
    """Returns (NP, NL) array of multipliers for out-migration by (province, language). Default 1.0."""
    mult = np.ones((NP, NL))
    path = os.path.join(DATA_DIR, "migration_language_multipliers.csv")
    if not os.path.exists(path):
        return mult
    rows = _read_csv(path)
    for r in rows:
        p_i = P_IDX[r["province"]]
        l_i = L_IDX[r["language"]]
        mult[p_i, l_i] = float(r["multiplier"])
    return mult


def load_natural_increase_fn() -> Callable[[int], np.ndarray]:
    """Returns f(year) -> ndarray (NP,) of annual natural increase rates per province."""
    rows = _read_csv(os.path.join(DATA_DIR, "natural_increase.csv"))
    years = sorted({int(r["year"]) for r in rows})
    matrix = np.zeros((len(years), NP))
    for r in rows:
        y_idx = years.index(int(r["year"]))
        for p_i, p in enumerate(PROVINCES):
            matrix[y_idx, p_i] = float(r[p])
    years_a = np.array(years, dtype=float)

    def f(y: int) -> np.ndarray:
        if y <= years_a[0]:
            return matrix[0].copy()
        if y >= years_a[-1]:
            return matrix[-1].copy()
        i = int(np.searchsorted(years_a, y) - 1)
        i = max(0, min(i, len(years_a) - 2))
        t = (y - years_a[i]) / (years_a[i + 1] - years_a[i])
        return (1 - t) * matrix[i] + t * matrix[i + 1]
    return f


def load_population_targets() -> Callable[[int], float]:
    rows = _read_csv(os.path.join(DATA_DIR, "historical_population.csv"))
    years = [int(r["year"]) for r in rows]
    values = [float(r["target_total_millions"]) for r in rows]
    return _interp_fn(years, values)


def load_historical_provincial_population() -> dict[str, Callable[[int], float]]:
    """
    Returns dict: province_code -> f(year) giving real population (persons)
    interpolated from Statistics Canada census / quarterly estimates.
    Only valid for 1971–2025 (the calibration window); extrapolation beyond
    2025 returns the 2025 value unchanged.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "historical_provincial_population.csv"))
    years_list = [int(r["year"]) for r in rows]
    result = {}
    for p in PROVINCES:
        values = [float(r[p]) * 1000 for r in rows]   # thousands → persons
        result[p] = _interp_fn(years_list, values)
    return result


def load_francophone_share_targets() -> tuple[Callable, Callable]:
    rows = _read_csv(os.path.join(DATA_DIR, "historical_francophone_share.csv"))
    years = [int(r["year"]) for r in rows]
    fr_can = [float(r["fr_share_canada"]) for r in rows]
    fr_qc = [float(r["fr_share_quebec"]) for r in rows]
    return _interp_fn(years, fr_can), _interp_fn(years, fr_qc)
