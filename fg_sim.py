"""
Fine-grain Canada Population Simulator.

Each agent carries: province (int8), language (int8), age (int16), sex (int8).
Explicit demographic processes per year:
  1. Deaths      — age × sex specific mortality from life tables
  2. Emigration  — age × sex specific annual rates
  3. Births      — ASFR-driven, with language inherited from mother
  4. Language transfer — same matrices as coarse model
  5. Interprovincial migration — same matrices as coarse model
  6. Immigration  — scenario-driven volume + age/sex/language composition
  7. Age all      — increment every agent's age by 1

Output prefix: fg_  (plots saved to plots/fg*.png)

Requires: fg_life_tables.csv, fg_fertility.csv, fg_age_sex_1971.csv,
          fg_immigrant_age_sex.csv, fg_emigration.csv
          plus the standard loaders.py data files.

Runtime: ~10–25 min depending on SCALE (default FG_SCALE=200).
"""

from __future__ import annotations
import os
import time
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Reuse province/language constants and CSV loaders from coarse model
from loaders import (
    PROVINCES, P_IDX, NP,
    LANGUAGES, L_IDX, NL,
    DATA_DIR,
    _read_csv, _interp_fn,
    load_initial_population,
    load_immigration_volume_fn,
    load_immigration_composition_fns,
    load_immigration_provincial_alloc_fn,
    load_language_transfer_fn,
    load_migration_matrix_fn,
    load_migration_lang_multipliers,
    load_scenarios,
)

# ── Constants ─────────────────────────────────────────────────────────────────
FG_SCALE   = 200          # 1 agent = 200 real people (coarser than coarse for speed)
START_YEAR = 1971
END_YEAR   = 2100         # shorter horizon — age structure needs time to equilibrate
MAX_AGE    = 110
SEX_M, SEX_F = 0, 1
PROV_QC   = P_IDX["QC"]

PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
BG, TEXT, SUBTEXT = "#0e1117", "#e8eaed", "#9aa0a6"
C_FR, C_EN, C_ALLO = "#3a7ebf", "#e07b39", "#3abf6e"
C_M, C_F = "#4e8ef7", "#f5a623"

SCENARIO_STYLES = {
    "low":  {"color": "#e07b39", "ls": "--"},
    "mid":  {"color": "#3a7ebf", "ls": "-"},
    "high": {"color": "#3abf6e", "ls": "-."},
}


# =============================================================================
# Fine-grain data loaders
# =============================================================================

def load_life_tables() -> dict:
    """
    Returns dict keyed by (sex_int, age_int) -> interpolation function(year)->q.
    Builds a 2 × (MAX_AGE+1) lookup array per year via interpolation.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "fg_life_tables.csv"))
    # Collect period anchors
    periods = sorted({int(r["period_year"]) for r in rows})
    # q_table[period_idx, sex, age] = annual prob of dying
    q_raw = np.zeros((len(periods), 2, MAX_AGE + 1))

    for r in rows:
        yi = periods.index(int(r["period_year"]))
        s  = SEX_M if r["sex"] == "M" else SEX_F
        a0, a1 = int(r["age_from"]), min(int(r["age_to"]), MAX_AGE)
        q  = float(r["q_annual"])
        q_raw[yi, s, a0:a1+1] = q

    periods_a = np.array(periods, dtype=float)

    def q_fn(year: int) -> np.ndarray:
        """Returns q[sex, age] array for the given year."""
        if year <= periods_a[0]:
            return q_raw[0].copy()
        if year >= periods_a[-1]:
            return q_raw[-1].copy()
        i = int(np.searchsorted(periods_a, year) - 1)
        i = max(0, min(i, len(periods_a) - 2))
        t = (year - periods_a[i]) / (periods_a[i+1] - periods_a[i])
        return (1 - t) * q_raw[i] + t * q_raw[i+1]

    return q_fn


def load_fertility() -> callable:
    """
    Returns f(year, is_qc: bool) -> ndarray of shape (MAX_AGE+1,) giving ASFR
    per woman per year for each single age, derived from 5-yr band midpoints.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "fg_fertility.csv"))
    periods = sorted({int(r["period_year"]) for r in rows})
    groups  = ["QC", "ROC"]
    # asfr_raw[period_idx, group_idx, 7 age midpoints]
    age_mids = [17, 22, 27, 32, 37, 42, 47]
    asfr_raw = np.zeros((len(periods), 2, len(age_mids)))

    for r in rows:
        yi  = periods.index(int(r["period_year"]))
        gi  = 0 if r["province_group"] == "QC" else 1
        ami = age_mids.index(int(r["age_midpoint"]))
        asfr_raw[yi, gi, ami] = float(r["asfr"])

    # Pre-build full-age ASFR arrays via step-function expansion
    # Each midpoint covers a 5-year band centred on it; zero outside 15-49
    asfr_full = np.zeros((len(periods), 2, MAX_AGE + 1))
    bands = [(15, 19), (20, 24), (25, 29), (30, 34), (35, 39), (40, 44), (45, 49)]
    for yi in range(len(periods)):
        for gi in range(2):
            for bi, (lo, hi) in enumerate(bands):
                asfr_full[yi, gi, lo:hi+1] = asfr_raw[yi, gi, bi]

    periods_a = np.array(periods, dtype=float)

    def f(year: int, is_qc: bool) -> np.ndarray:
        gi = 0 if is_qc else 1
        if year <= periods_a[0]:
            return asfr_full[0, gi].copy()
        if year >= periods_a[-1]:
            return asfr_full[-1, gi].copy()
        i = int(np.searchsorted(periods_a, year) - 1)
        i = max(0, min(i, len(periods_a) - 2))
        t = (year - periods_a[i]) / (periods_a[i+1] - periods_a[i])
        return (1 - t) * asfr_full[i, gi] + t * asfr_full[i+1, gi]

    return f


def load_age_sex_init() -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (ages_M, ages_F): two arrays of age values (one per agent group)
    representing the cumulative distribution used to draw initial ages.
    Format: parallel lists of (age_lower, share) — returned as arrays.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "fg_age_sex_1971.csv"))
    m_rows = [(int(r["age_group"]), float(r["share"])) for r in rows if r["sex"] == "M"]
    f_rows = [(int(r["age_group"]), float(r["share"])) for r in rows if r["sex"] == "F"]

    def to_cdf(pairs):
        ages   = np.array([p[0] for p in pairs])
        shares = np.array([p[1] for p in pairs])
        shares /= shares.sum()
        return ages, np.cumsum(shares)

    return to_cdf(m_rows), to_cdf(f_rows)


def load_immigrant_age_sex() -> callable:
    """
    Returns f(year, sex_int) -> (ages_lower, cdf) arrays for sampling
    immigrant ages.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "fg_immigrant_age_sex.csv"))
    periods = sorted({int(r["period_year"]) for r in rows})

    # imm_raw[period, sex, age_band_idx]
    age_bands = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
    NB = len(age_bands)
    imm_raw = np.zeros((len(periods), 2, NB))

    for r in rows:
        yi = periods.index(int(r["period_year"]))
        s  = SEX_M if r["sex"] == "M" else SEX_F
        bi = age_bands.index(int(r["age_group"]))
        imm_raw[yi, s, bi] = float(r["share"])

    # Normalize
    imm_raw /= imm_raw.sum(axis=2, keepdims=True)

    periods_a = np.array(periods, dtype=float)
    bands_a   = np.array(age_bands)

    def f(year: int, sex: int) -> tuple[np.ndarray, np.ndarray]:
        if year <= periods_a[0]:
            shares = imm_raw[0, sex].copy()
        elif year >= periods_a[-1]:
            shares = imm_raw[-1, sex].copy()
        else:
            i = int(np.searchsorted(periods_a, year) - 1)
            i = max(0, min(i, len(periods_a) - 2))
            t = (year - periods_a[i]) / (periods_a[i+1] - periods_a[i])
            shares = (1 - t) * imm_raw[i, sex] + t * imm_raw[i+1, sex]
        shares /= shares.sum()
        return bands_a, np.cumsum(shares)

    return f


def load_emigration_rates() -> callable:
    """
    Returns f(year) -> ndarray[sex, age] annual emigration probability.
    """
    rows = _read_csv(os.path.join(DATA_DIR, "fg_emigration.csv"))
    periods  = sorted({int(r["period_year"]) for r in rows})
    age_bands = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]

    emig_raw = np.zeros((len(periods), 2, MAX_AGE + 1))
    for r in rows:
        yi = periods.index(int(r["period_year"]))
        s  = SEX_M if r["sex"] == "M" else SEX_F
        lo = int(r["age_group"])
        hi = age_bands[age_bands.index(lo) + 1] - 1 if lo < 65 else MAX_AGE
        emig_raw[yi, s, lo:hi+1] = float(r["annual_prob"])

    periods_a = np.array(periods, dtype=float)

    def f(year: int) -> np.ndarray:
        if year <= periods_a[0]:
            return emig_raw[0].copy()
        if year >= periods_a[-1]:
            return emig_raw[-1].copy()
        i = int(np.searchsorted(periods_a, year) - 1)
        i = max(0, min(i, len(periods_a) - 2))
        t = (year - periods_a[i]) / (periods_a[i+1] - periods_a[i])
        return (1 - t) * emig_raw[i] + t * emig_raw[i+1]

    return f


# =============================================================================
# Population container
# =============================================================================

class FinePop:
    """
    Four parallel int arrays, one element per agent.
      province  int8   0-12  (index into PROVINCES list)
      language  int8   0-2   (0=fr, 1=en, 2=allo)
      age       int16  0-110
      sex       int8   0=M, 1=F
    """

    def __init__(self, n: int = 0):
        self.province = np.empty(n, dtype=np.int8)
        self.language = np.empty(n, dtype=np.int8)
        self.age      = np.empty(n, dtype=np.int16)
        self.sex      = np.empty(n, dtype=np.int8)

    def __len__(self) -> int:
        return len(self.province)

    def append_agents(self, province, language, age, sex):
        """Append new agents given scalar or array arguments."""
        province = np.asarray(province, dtype=np.int8)
        language = np.asarray(language, dtype=np.int8)
        age      = np.asarray(age,      dtype=np.int16)
        sex      = np.asarray(sex,      dtype=np.int8)
        self.province = np.concatenate([self.province, province])
        self.language = np.concatenate([self.language, language])
        self.age      = np.concatenate([self.age,      age])
        self.sex      = np.concatenate([self.sex,      sex])

    def remove_mask(self, keep: np.ndarray):
        """Remove agents where keep==False."""
        self.province = self.province[keep]
        self.language = self.language[keep]
        self.age      = self.age[keep]
        self.sex      = self.sex[keep]

    def tally(self) -> dict:
        """Return counts dict: {province}_{lang} -> count (in real people)."""
        out = {}
        for pi, p in enumerate(PROVINCES):
            mask_p = self.province == pi
            for li, l in enumerate(LANGUAGES):
                out[f"{p}_{l}"] = int(np.sum(mask_p & (self.language == li))) * FG_SCALE
        return out


# =============================================================================
# Fine-grain Simulator
# =============================================================================

class FineSimulator:

    def __init__(
        self,
        scenario_name: str = "mid",
        scale: int = FG_SCALE,
        seed: int = 0,
    ):
        self.scenario_name = scenario_name
        self.scale = scale
        self.rng   = np.random.default_rng(seed)

        # Load all data functions
        self.q_fn        = load_life_tables()
        self.fert_fn     = load_fertility()
        self.imm_age_fn  = load_immigrant_age_sex()
        self.emig_fn     = load_emigration_rates()
        (self.ages_M_lower, self.cdf_M), (self.ages_F_lower, self.cdf_F) = load_age_sex_init()

        self.vol_fn      = load_immigration_volume_fn()
        self.fr_qc_fn, self.en_qc_fn, self.fr_roc_fn, self.en_roc_fn = (
            load_immigration_composition_fns()
        )
        self.prov_alloc_fn = load_immigration_provincial_alloc_fn()
        self.lang_tr_fn    = load_language_transfer_fn()
        self.mig_fn        = load_migration_matrix_fn()
        self.mig_mult      = load_migration_lang_multipliers()
        self.scenarios     = load_scenarios()
        self.scen          = self.scenarios[scenario_name]

        self.pop     = FinePop()
        self.history = []
        self.year    = None

        self._initialize()

    # ── Initialization ────────────────────────────────────────────────────────

    def _initialize(self):
        init = load_initial_population()
        for pi, prov in enumerate(PROVINCES):
            d = init[prov]
            total_agents = max(1, round(d["pop_thousands"] * 1000 / self.scale))
            fr_n   = round(total_agents * d["fr_share"])
            allo_n = round(total_agents * d["allo_share"])
            en_n   = total_agents - fr_n - allo_n

            for li, n in enumerate([fr_n, en_n, allo_n]):
                if n <= 0:
                    continue
                # Split 50/50 M/F then draw ages from 1971 distribution
                n_m = n // 2
                n_f = n - n_m
                ages_m = self._draw_init_ages(SEX_M, n_m)
                ages_f = self._draw_init_ages(SEX_F, n_f)
                self.pop.append_agents(
                    province=np.full(n_m, pi, dtype=np.int8),
                    language=np.full(n_m, li, dtype=np.int8),
                    age=ages_m,
                    sex=np.full(n_m, SEX_M, dtype=np.int8),
                )
                self.pop.append_agents(
                    province=np.full(n_f, pi, dtype=np.int8),
                    language=np.full(n_f, li, dtype=np.int8),
                    age=ages_f,
                    sex=np.full(n_f, SEX_F, dtype=np.int8),
                )

        self.year = START_YEAR
        init_tally = {"year": self.year, **self.pop.tally()}
        _bin_edges = list(range(0, 91, 5)) + [MAX_AGE + 1]
        hist_M, _ = np.histogram(
            self.pop.age[self.pop.sex == SEX_M], bins=_bin_edges
        )
        hist_F, _ = np.histogram(
            self.pop.age[self.pop.sex == SEX_F], bins=_bin_edges
        )
        init_tally["age_hist_M"] = (hist_M * self.scale).tolist()
        init_tally["age_hist_F"] = (hist_F * self.scale).tolist()
        for pi, p in enumerate(PROVINCES):
            init_tally[f"{p}_births"] = 0
        self.history.append(init_tally)

    def _draw_init_ages(self, sex: int, n: int) -> np.ndarray:
        if n == 0:
            return np.empty(0, dtype=np.int16)
        if sex == SEX_M:
            lowers, cdf = self.ages_M_lower, self.cdf_M
        else:
            lowers, cdf = self.ages_F_lower, self.cdf_F
        u = self.rng.random(n)
        band_idx = np.searchsorted(cdf, u)
        band_idx = np.clip(band_idx, 0, len(lowers) - 1)
        lo = lowers[band_idx]
        # 85+ open band: draw uniformly up to 95
        hi = np.where(lo < 85, lo + 4, 95)
        ages = lo + (self.rng.random(n) * (hi - lo + 1)).astype(int)
        return ages.astype(np.int16)

    # ── Step ──────────────────────────────────────────────────────────────────

    def step(self):
        y = self.year

        # ── 1. Deaths ─────────────────────────────────────────────────────────
        q = self.q_fn(y)                           # shape (2, MAX_AGE+1)
        ages_cl = np.clip(self.pop.age, 0, MAX_AGE)
        death_probs = q[self.pop.sex, ages_cl]
        alive = self.rng.random(len(self.pop)) >= death_probs
        self.pop.remove_mask(alive)

        # Track deaths for history
        n_deaths = int(np.sum(~alive)) * self.scale

        # ── 2. Emigration ─────────────────────────────────────────────────────
        e = self.emig_fn(y)                        # shape (2, MAX_AGE+1)
        ages_cl = np.clip(self.pop.age, 0, MAX_AGE)
        emig_probs = e[self.pop.sex, ages_cl]
        stay = self.rng.random(len(self.pop)) >= emig_probs
        self.pop.remove_mask(stay)

        n_emigrants = int(np.sum(~stay)) * self.scale

        # ── 3. Births ─────────────────────────────────────────────────────────
        new_prov, new_lang, new_age, new_sex = [], [], [], []
        n_births = 0
        births_by_prov = np.zeros(NP, dtype=np.int64)

        for pi in range(NP):
            is_qc   = (pi == PROV_QC)
            asfr    = self.fert_fn(y, is_qc)       # shape (MAX_AGE+1,)
            f_mask  = (self.pop.province == pi) & (self.pop.sex == SEX_F)
            f_ages  = self.pop.age[f_mask].astype(int)
            f_langs = self.pop.language[f_mask]

            if len(f_ages) == 0:
                continue

            # Expected new agents = Σ ASFR[age] (SCALE cancels)
            rates = asfr[np.clip(f_ages, 0, MAX_AGE)]
            expected = rates.sum()
            # Draw Poisson-distributed number of new agents
            n_new = int(self.rng.poisson(expected))

            if n_new == 0:
                continue
            births_by_prov[pi] = n_new * self.scale
            n_births += n_new * self.scale

            # Pick n_new mothers proportional to their ASFR
            probs = rates / rates.sum() if rates.sum() > 0 else np.ones(len(rates)) / len(rates)
            mother_idx = self.rng.choice(len(f_ages), size=n_new, p=probs)
            # Inherit mother's language; 50/50 sex
            infant_lang = f_langs[mother_idx]
            infant_sex  = self.rng.integers(0, 2, size=n_new, dtype=np.int8)
            new_prov.extend([pi] * n_new)
            new_lang.extend(infant_lang.tolist())
            new_age.extend([0] * n_new)
            new_sex.extend(infant_sex.tolist())

        if new_prov:
            self.pop.append_agents(
                province=np.array(new_prov, dtype=np.int8),
                language=np.array(new_lang, dtype=np.int8),
                age=np.zeros(len(new_prov), dtype=np.int16),
                sex=np.array(new_sex, dtype=np.int8),
            )

        # ── 4. Language transfer ──────────────────────────────────────────────
        T = self.lang_tr_fn(y)                     # shape (NP, NL, NL)
        u = self.rng.random(len(self.pop))
        new_lang_arr = self.pop.language.copy()

        for pi in range(NP):
            for li in range(NL):
                mask = (self.pop.province == pi) & (self.pop.language == li)
                if not mask.any():
                    continue
                row = T[pi, li]
                thresholds = np.cumsum(row)
                draws = u[mask]
                # Find target language: first threshold exceeded
                result = np.searchsorted(thresholds, draws, side="right")
                new_lang_arr[mask] = np.clip(result, 0, NL - 1).astype(np.int8)

        self.pop.language = new_lang_arr

        # ── 5. Interprovincial migration ──────────────────────────────────────
        M = self.mig_fn(y)                         # shape (NP, NP)
        mult = self.mig_mult                       # shape (NP, NL)
        u = self.rng.random(len(self.pop))
        new_prov_arr = self.pop.province.copy()

        for pi in range(NP):
            row_base = M[pi]
            for li in range(NL):
                mask = (self.pop.province == pi) & (self.pop.language == li)
                if not mask.any():
                    continue
                m = mult[pi, li]
                row = row_base.copy()
                # Scale off-diagonal by multiplier; redistribute remainder to diag
                off_mask = np.arange(NP) != pi
                row[off_mask] *= m
                row[pi] = max(0.0, 1.0 - row[off_mask].sum())
                row /= row.sum()
                thresholds = np.cumsum(row)
                draws = u[mask]
                result = np.searchsorted(thresholds, draws, side="right")
                new_prov_arr[mask] = np.clip(result, 0, NP - 1).astype(np.int8)

        self.pop.province = new_prov_arr

        # ── 6. Immigration ────────────────────────────────────────────────────
        vol_mult = 1.0
        fr_offset = 0.0
        if y >= 2025:
            vol_mult  = self.scen["volume_multiplier_post2025"]
            fr_offset = self.scen["fr_share_offset_post2025"]

        annual_vol = self.vol_fn(y) * vol_mult     # real individuals
        n_imm_agents = max(0, round(annual_vol / self.scale))

        alloc = self.prov_alloc_fn(y)
        fr_qc  = np.clip(self.fr_qc_fn(y) + fr_offset, 0, 1)
        en_qc  = np.clip(self.en_qc_fn(y), 0, 1 - fr_qc)
        fr_roc_raw = (
            self.scen.get("roc_fr_share_post2025") if y >= 2025 else None
        )
        fr_roc = fr_roc_raw if fr_roc_raw is not None else np.clip(
            self.fr_roc_fn(y) + fr_offset, 0, 1
        )
        en_roc = np.clip(self.en_roc_fn(y), 0, 1 - fr_roc)

        n_imm = round(n_imm_agents)
        if n_imm > 0:
            # Province selection weighted by alloc
            prov_choices = self.rng.choice(NP, size=n_imm, p=alloc)
            # Sex 50/50
            sex_choices  = self.rng.integers(0, 2, size=n_imm, dtype=np.int8)

            # Age by sex
            age_arr = np.empty(n_imm, dtype=np.int16)
            for s_i in (SEX_M, SEX_F):
                s_mask = sex_choices == s_i
                n_s = int(s_mask.sum())
                if n_s == 0:
                    continue
                bands_a, cdf_a = self.imm_age_fn(y, s_i)
                u_a = self.rng.random(n_s)
                bi  = np.clip(np.searchsorted(cdf_a, u_a), 0, len(bands_a) - 1)
                lo  = bands_a[bi]
                hi  = np.where(lo < 65, lo + 4, MAX_AGE)
                drawn = (lo + self.rng.random(n_s) * (hi - lo + 1)).astype(int)
                age_arr[s_mask] = np.clip(drawn, 0, MAX_AGE).astype(np.int16)

            # Language by province
            lang_arr = np.full(n_imm, L_IDX["allo"], dtype=np.int8)
            for idx in range(n_imm):
                pi = int(prov_choices[idx])
                is_qc = (pi == PROV_QC)
                fr_p = fr_qc if is_qc else fr_roc
                en_p = en_qc if is_qc else en_roc
                al_p = max(0.0, 1.0 - fr_p - en_p)
                u_l  = self.rng.random()
                if u_l < fr_p:
                    lang_arr[idx] = L_IDX["fr"]
                elif u_l < fr_p + en_p:
                    lang_arr[idx] = L_IDX["en"]
                else:
                    lang_arr[idx] = L_IDX["allo"]

            self.pop.append_agents(
                province=prov_choices.astype(np.int8),
                language=lang_arr,
                age=age_arr,
                sex=sex_choices,
            )

        # ── National age histogram by sex (5-year bins 0–4, 5–9, …, 85+) ──────
        # Computed BEFORE the year-end aging so this year's newborns occupy the
        # age-0 cohort. If taken after aging, age 0 is always empty (births get
        # bumped to age 1) and the 0–4 bin holds only 4 single-year cohorts,
        # leaving the pyramid base permanently ~20% too narrow.
        _bin_edges = list(range(0, 91, 5)) + [MAX_AGE + 1]
        hist_M, _ = np.histogram(
            self.pop.age[self.pop.sex == SEX_M], bins=_bin_edges
        )
        hist_F, _ = np.histogram(
            self.pop.age[self.pop.sex == SEX_F], bins=_bin_edges
        )

        # ── 7. Age everyone ───────────────────────────────────────────────────
        self.pop.age = np.clip(self.pop.age + 1, 0, MAX_AGE).astype(np.int16)

        # ── Record ────────────────────────────────────────────────────────────
        tally = self.pop.tally()
        tally["year"]        = y + 1
        tally["n_births"]    = n_births
        tally["n_deaths"]    = n_deaths
        tally["n_emigrants"] = n_emigrants
        tally["n_immigrants"]= n_imm * self.scale

        # Per-province births
        for pi, p in enumerate(PROVINCES):
            tally[f"{p}_births"] = int(births_by_prov[pi])

        tally["age_hist_M"] = (hist_M * self.scale).tolist()
        tally["age_hist_F"] = (hist_F * self.scale).tolist()

        self.history.append(tally)
        self.year += 1

    def run(self, until_year: int = END_YEAR, verbose: bool = True):
        t0 = time.time()
        while self.year < until_year:
            self.step()
            if verbose and self.year % 10 == 0:
                n = len(self.pop) * self.scale
                elapsed = time.time() - t0
                print(f"  {self.year}  pop={n/1e6:.2f}M  elapsed={elapsed:.0f}s")
        if verbose:
            print(f"Done — {len(self.history)} years in {time.time()-t0:.0f}s")


# =============================================================================
# Helper: compute age-group tallies from history
# =============================================================================

def age_group_tally(sim: FineSimulator, year: int) -> dict:
    """
    Return dict with population by age group × language × province for a
    specific simulation year. Reads live pop arrays (only valid at current year).
    """
    if sim.year != year:
        raise ValueError("Snapshot only available at current sim.year")
    groups = {
        "0-14":  (0,  14),
        "15-24": (15, 24),
        "25-64": (25, 64),
        "65+":   (65, MAX_AGE),
    }
    out = {}
    for gname, (lo, hi) in groups.items():
        age_mask = (sim.pop.age >= lo) & (sim.pop.age <= hi)
        for li, l in enumerate(LANGUAGES):
            lang_mask = sim.pop.language == li
            out[f"{gname}_{l}"] = int(np.sum(age_mask & lang_mask)) * sim.scale
    return out


# =============================================================================
# Plotting
# =============================================================================

def _setup_ax(ax):
    ax.set_facecolor(BG)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=SUBTEXT)
    ax.xaxis.label.set_color(SUBTEXT)
    ax.yaxis.label.set_color(SUBTEXT)
    ax.title.set_color(TEXT)


def _fig(rows=1, cols=1, figsize=None):
    if figsize is None:
        figsize = (7 * cols, 4.5 * rows)
    fig, axes = plt.subplots(rows, cols, figsize=figsize, facecolor=BG)
    return fig, axes


def save(fig, name: str, dpi: int = 150):
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  Saved {path}")


# ── fg01: Population Pyramid Snapshots ────────────────────────────────────────

def plot_population_pyramid(sim: FineSimulator, snapshot_years=(1971, 2000, 2025, 2060, 2100)):
    """
    Horizontal bar pyramid: M left, F right.
    Each panel one year, using the agent arrays at END of simulation.
    We reconstruct from history by replaying age cohorts — instead we use
    the single snapshot at END_YEAR stored in live arrays, and for past
    years we approximate via history tallies of total pop by age (not stored).
    So: only plot the final-year pyramid from live pop, plus totals from history.
    """
    # Plot pyramid for the final simulated year
    age_bins = np.arange(0, MAX_AGE + 1, 5)
    ages_live = sim.pop.age
    sex_live  = sim.pop.sex
    lang_live = sim.pop.language

    fig, axes = plt.subplots(1, 3, figsize=(16, 7), facecolor=BG,
                             gridspec_kw={"wspace": 0.05})
    fig.suptitle(
        f"Population Pyramid — {sim.year} ({sim.scenario_name} scenario)",
        color=TEXT, fontsize=13, fontweight="bold",
    )

    for ax_idx, (lang_code, col) in enumerate(
        zip(["fr", "en", "allo"], [C_FR, C_EN, C_ALLO])
    ):
        ax = axes[ax_idx]
        _setup_ax(ax)
        li = L_IDX[lang_code]
        ax.set_title(["Francophone", "Anglophone", "Allophone"][ax_idx],
                     color=TEXT, fontsize=10, fontweight="bold")

        for s, side, mult in [(SEX_M, "M", -1), (SEX_F, "F", 1)]:
            mask = (sex_live == s) & (lang_live == li)
            counts, _ = np.histogram(ages_live[mask], bins=np.append(age_bins, MAX_AGE + 1))
            counts = counts * sim.scale / 1e6  # millions
            y_pos = age_bins
            ax.barh(y_pos, mult * counts, height=4.2,
                    color=col, alpha=0.8 if s == SEX_F else 0.55,
                    edgecolor="none", align="edge")

        ax.axvline(0, color=SUBTEXT, linewidth=0.5)
        ax.set_yticks(age_bins[::2])
        ax.set_yticklabels([f"{a}" for a in age_bins[::2]], color=SUBTEXT, fontsize=7)
        ax.set_xlabel("Millions (◀ M | F ▶)", color=SUBTEXT, fontsize=8)
        ax.set_ylabel("Age", color=SUBTEXT, fontsize=8)

        # Legend
        from matplotlib.patches import Patch
        ax.legend(
            [Patch(color=col, alpha=0.55, label="Male"),
             Patch(color=col, alpha=0.8,  label="Female")],
            ["Male", "Female"], framealpha=0, labelcolor=TEXT, fontsize=7,
            loc="lower right",
        )

    save(fig, f"fg01_pyramid_{sim.scenario_name}.png")


# ── fg02: Births vs Deaths ────────────────────────────────────────────────────

def plot_births_deaths(sims: dict):
    fig, axes = _fig(1, 2, figsize=(14, 5))
    fig.suptitle("Births and Deaths", color=TEXT,
                 fontsize=13, fontweight="bold")

    for ax, key, title in zip(axes, ["n_births", "n_deaths"], ["Annual Births", "Annual Deaths"]):
        _setup_ax(ax)
        ax.set_title(title, color=TEXT, fontsize=10)
        for sname, sim in sims.items():
            st = SCENARIO_STYLES[sname]
            years = np.array([r["year"] for r in sim.history[1:]])
            vals  = np.array([r.get(key, 0) for r in sim.history[1:]]) / 1e3  # thousands
            ax.plot(years, vals, color=st["color"], ls=st["ls"], lw=1.8,
                    label=sname.capitalize())
        ax.set_xlabel("Year", fontsize=9)
        ax.set_ylabel("Thousands", fontsize=9)
        ax.legend(framealpha=0, labelcolor=TEXT, fontsize=8)
        ax.grid(axis="y", color="#2a2a2a", linewidth=0.5)

    save(fig, "fg02_births_deaths.png")


# ── fg03: Dependency Ratio ────────────────────────────────────────────────────

def plot_dependency_ratio(sims: dict):
    """
    Old-age dependency ratio = (65+) / (15-64)
    Youth dependency ratio   = (0-14) / (15-64)
    """
    fig, ax = _fig(1, 1, figsize=(10, 5))
    _setup_ax(ax)
    ax.set_title("Old-Age Dependency Ratio (65+ / 15–64)",
                 color=TEXT, fontsize=12, fontweight="bold")

    for sname, sim in sims.items():
        st = SCENARIO_STYLES[sname]
        years, oadr = [], []
        for r in sim.history:
            y = r["year"]
            # Approximate from tally: we stored province×language, not age groups.
            # We derive total pop from tally and use birth/death counts to track
            # cohort structure. Instead: we reconstruct from the final pop arrays only
            # at the last year; for intermediate years we skip this plot.
            # NOTE: Full age-by-year tracking would require storing age histograms.
            pass
        # Nothing to plot without age histograms in history — placeholder message
        ax.text(0.5, 0.5, "Age-structured history not stored\n(compute from fg01 pyramid)",
                transform=ax.transAxes, ha="center", va="center",
                color=SUBTEXT, fontsize=10)
        break  # avoid repeating

    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Ratio", fontsize=9)
    save(fig, "fg03_dependency_ratio.png")


# ── fg04: Francophone share by national total ─────────────────────────────────

def plot_fr_share(sims: dict):
    fig, ax = _fig(1, 1, figsize=(10, 5))
    _setup_ax(ax)
    ax.set_title("National Francophone Share",
                 color=TEXT, fontsize=12, fontweight="bold")

    for sname, sim in sims.items():
        st = SCENARIO_STYLES[sname]
        years, shares = [], []
        for r in sim.history:
            tot_fr  = sum(r.get(f"{p}_fr",  0) for p in PROVINCES)
            tot_all = sum(r.get(f"{p}_{l}", 0) for p in PROVINCES for l in LANGUAGES)
            years.append(r["year"])
            shares.append(100.0 * tot_fr / max(1, tot_all))
        ax.plot(years, shares, color=st["color"], ls=st["ls"], lw=2,
                label=sname.capitalize())

    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Francophone share (%)", fontsize=9)
    ax.legend(framealpha=0, labelcolor=TEXT, fontsize=9)
    ax.grid(axis="y", color="#2a2a2a", linewidth=0.5)
    save(fig, "fg04_fr_share.png")


# ── fg05: Quebec francophone share ────────────────────────────────────────────

def plot_qc_fr_share(sims: dict):
    fig, ax = _fig(1, 1, figsize=(10, 5))
    _setup_ax(ax)
    ax.set_title("Quebec Francophone Share",
                 color=TEXT, fontsize=12, fontweight="bold")

    for sname, sim in sims.items():
        st = SCENARIO_STYLES[sname]
        years, shares = [], []
        for r in sim.history:
            tot_fr  = r.get("QC_fr",  0)
            tot_all = sum(r.get(f"QC_{l}", 0) for l in LANGUAGES)
            years.append(r["year"])
            shares.append(100.0 * tot_fr / max(1, tot_all))
        ax.plot(years, shares, color=st["color"], ls=st["ls"], lw=2,
                label=sname.capitalize())

    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("QC francophone share (%)", fontsize=9)
    ax.legend(framealpha=0, labelcolor=TEXT, fontsize=9)
    ax.grid(axis="y", color="#2a2a2a", linewidth=0.5)
    save(fig, "fg05_qc_fr_share.png")


# ── fg06: Total population ────────────────────────────────────────────────────

def plot_total_population(sims: dict):
    fig, ax = _fig(1, 1, figsize=(10, 5))
    _setup_ax(ax)
    ax.set_title("Total Canadian Population",
                 color=TEXT, fontsize=12, fontweight="bold")

    for sname, sim in sims.items():
        st = SCENARIO_STYLES[sname]
        years = [r["year"] for r in sim.history]
        totals = [
            sum(r.get(f"{p}_{l}", 0) for p in PROVINCES for l in LANGUAGES) / 1e6
            for r in sim.history
        ]
        ax.plot(years, totals, color=st["color"], ls=st["ls"], lw=2,
                label=sname.capitalize())

    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Population (millions)", fontsize=9)
    ax.legend(framealpha=0, labelcolor=TEXT, fontsize=9)
    ax.grid(axis="y", color="#2a2a2a", linewidth=0.5)
    save(fig, "fg06_total_population.png")


# ── fg07: Natural increase (births - deaths) ──────────────────────────────────

def plot_natural_increase(sims: dict):
    fig, ax = _fig(1, 1, figsize=(10, 5))
    _setup_ax(ax)
    ax.set_title("Annual Natural Increase (Births − Deaths)",
                 color=TEXT, fontsize=12, fontweight="bold")

    for sname, sim in sims.items():
        st = SCENARIO_STYLES[sname]
        years = np.array([r["year"] for r in sim.history[1:]])
        ni = np.array([
            r.get("n_births", 0) - r.get("n_deaths", 0)
            for r in sim.history[1:]
        ]) / 1e3

        # 5-yr rolling mean
        kernel = np.ones(5) / 5
        ni_sm = np.convolve(ni, kernel, mode="same")
        ax.plot(years, ni_sm, color=st["color"], ls=st["ls"], lw=2,
                label=sname.capitalize())

    ax.axhline(0, color=SUBTEXT, linewidth=0.7, linestyle=":")
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Natural increase (thousands/yr, 5-yr avg)", fontsize=9)
    ax.legend(framealpha=0, labelcolor=TEXT, fontsize=9)
    ax.grid(axis="y", color="#2a2a2a", linewidth=0.5)
    save(fig, "fg07_natural_increase.png")


# ── fg08: Net migration balance ───────────────────────────────────────────────

def plot_net_migration(sims: dict):
    fig, ax = _fig(1, 1, figsize=(10, 5))
    _setup_ax(ax)
    ax.set_title("Annual Net Migration (Immigrants − Emigrants)",
                 color=TEXT, fontsize=12, fontweight="bold")

    for sname, sim in sims.items():
        st = SCENARIO_STYLES[sname]
        years = np.array([r["year"] for r in sim.history[1:]])
        net = np.array([
            r.get("n_immigrants", 0) - r.get("n_emigrants", 0)
            for r in sim.history[1:]
        ]) / 1e3

        ax.plot(years, net, color=st["color"], ls=st["ls"], lw=2,
                label=sname.capitalize())

    ax.axhline(0, color=SUBTEXT, linewidth=0.7, linestyle=":")
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Net migration (thousands/yr)", fontsize=9)
    ax.legend(framealpha=0, labelcolor=TEXT, fontsize=9)
    ax.grid(axis="y", color="#2a2a2a", linewidth=0.5)
    save(fig, "fg08_net_migration.png")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import pickle

    print("=" * 60)
    print("Fine-Grain Canada Population Simulator")
    print(f"  FG_SCALE={FG_SCALE}  ({FG_SCALE} real people per agent)")
    print(f"  Period: {START_YEAR}–{END_YEAR}")
    print("=" * 60)

    sims = {}
    for scen in ("low", "mid", "high"):
        print(f"\nScenario: {scen}")
        sim = FineSimulator(scenario_name=scen, scale=FG_SCALE, seed=42)
        sim.run(until_year=END_YEAR, verbose=True)
        sims[scen] = sim

    # Save mid-scenario history so fg_bar_race.py can load it without re-running
    cache_path = os.path.join(PLOT_DIR, "fg_mid_history.pkl")
    with open(cache_path, "wb") as f:
        pickle.dump(sims["mid"].history, f)
    print(f"  Saved history cache → {cache_path}")

    print("\nGenerating plots...")
    plot_population_pyramid(sims["mid"])
    plot_births_deaths(sims)
    plot_dependency_ratio(sims)
    plot_fr_share(sims)
    plot_qc_fr_share(sims)
    plot_total_population(sims)
    plot_natural_increase(sims)
    plot_net_migration(sims)
    print("\nAll done.")
