"""
Canada Population Simulator (1971–2150)
========================================

Agent-based model. Each agent represents SCALE real people.
All parameters loaded at runtime from data/*.csv files.

Processes:
  1. Language transfer (province-specific 3x3 annual matrix)
  2. Interprovincial migration (13x13 annual matrix)
  3. International immigration (annual inflow with provincial + linguistic comp)

Periods:
  1971–2025 = CALIBRATION (data files use empirical StatCan figures)
  2025–2150 = PROJECTION (data files extrapolate trends, calibrated to
              hit ~100M by 2100 in the mid scenario)
"""
from __future__ import annotations
import os
import time
import numpy as np
from dataclasses import dataclass
from typing import Literal

from loaders import (
    PROVINCES, P_IDX, NP,
    LANGUAGES, L_IDX, NL,
    load_initial_population,
    load_immigration_volume_fn,
    load_immigration_composition_fns,
    load_immigration_provincial_alloc_fn,
    load_language_transfer_fn,
    load_migration_matrix_fn,
    load_migration_lang_multipliers,
    load_natural_increase_fn,
    load_scenarios,
    load_population_targets,
    load_francophone_share_targets,
)

START_YEAR = 1971
END_YEAR = 2150
SCALE = 100  # 1 agent = 100 real people. Lower = more accurate, slower.
             # At SCALE=100: ~30s per scenario, ~90MB RAM, ~1.25M agents by 2150.
             # At SCALE=1000: ~3s per scenario but visible Monte Carlo noise
             # (~0.2pp wobbles) in provincial language shares post-2100.


@dataclass
class Population:
    province: np.ndarray
    language: np.ndarray
    scale: int = SCALE

    @classmethod
    def initial_1971(cls, scale: int, rng: np.random.Generator) -> "Population":
        init = load_initial_population()
        provs, langs = [], []
        for p in PROVINCES:
            d = init[p]
            n_people = int(d["pop_thousands"] * 1000)
            n_agents = n_people // scale
            if n_agents == 0:
                continue
            fr_s, allo_s = d["fr_share"], d["allo_share"]
            en_s = max(0.0, 1 - fr_s - allo_s)
            probs = np.array([fr_s, en_s, allo_s])
            probs /= probs.sum()
            provs.append(np.full(n_agents, P_IDX[p], dtype=np.int16))
            langs.append(rng.choice(NL, size=n_agents, p=probs).astype(np.int8))
        return cls(
            province=np.concatenate(provs),
            language=np.concatenate(langs),
            scale=scale,
        )

    def size(self) -> int:
        return len(self.province)

    def real_population(self) -> int:
        return self.size() * self.scale

    def counts(self) -> dict:
        out = {}
        for p_i, p in enumerate(PROVINCES):
            mask_p = self.province == p_i
            for l_i, l in enumerate(LANGUAGES):
                out[(p, l)] = int((mask_p & (self.language == l_i)).sum()) * self.scale
        return out


class CanadaSimulator:
    def __init__(
        self,
        scenario_name: Literal["low", "mid", "high"] = "mid",
        scale: int = SCALE,
        seed: int = 42,
    ):
        self.rng = np.random.default_rng(seed)
        self.scale = scale
        self.scenario_name = scenario_name

        # Load all data
        self.scenarios = load_scenarios()
        self.scenario_params = self.scenarios[scenario_name]
        self.imm_volume_fn = load_immigration_volume_fn()
        (self.imm_fr_qc_fn, self.imm_en_qc_fn,
         self.imm_fr_roc_fn, self.imm_en_roc_fn) = load_immigration_composition_fns()
        self.imm_alloc_fn = load_immigration_provincial_alloc_fn()
        self.lang_transfer_fn = load_language_transfer_fn()
        self.migration_fn = load_migration_matrix_fn()
        self.migration_lang_mult = load_migration_lang_multipliers()  # (NP, NL)
        self.natural_increase_fn = load_natural_increase_fn()

        # Init population
        self.pop = Population.initial_1971(scale=scale, rng=self.rng)
        self.year = START_YEAR
        self.history: list[dict] = []
        self._record()

    # --- scenario-aware getters -------------------------------------------------

    def _imm_volume(self, year: int) -> float:
        v = self.imm_volume_fn(year)
        if year > 2025:
            v *= self.scenario_params["volume_multiplier_post2025"]
        return v

    def _imm_fr_share(self, year: int, region: str) -> float:
        base = self.imm_fr_qc_fn(year) if region == "QC" else self.imm_fr_roc_fn(year)
        if year > 2025:
            roc_override = self.scenario_params.get("roc_fr_share_post2025")
            if region == "ROC" and roc_override is not None:
                return roc_override
            base += self.scenario_params["fr_share_offset_post2025"]
        return max(0.0, min(1.0, base))

    def _imm_en_share(self, year: int, region: str) -> float:
        return self.imm_en_qc_fn(year) if region == "QC" else self.imm_en_roc_fn(year)

    # --- recording -------------------------------------------------------------

    def _record(self):
        c = self.pop.counts()
        row = {"year": self.year, "total": self.pop.real_population()}
        for p in PROVINCES:
            for l in LANGUAGES:
                row[f"{p}_{l}"] = c[(p, l)]
        self.history.append(row)

    # --- step ------------------------------------------------------------------

    def step(self):
        self._apply_language_transfer()
        self._apply_migration()
        self._apply_natural_increase()
        self._apply_immigration()
        self.year += 1
        self._record()

    def _apply_language_transfer(self):
        M = self.lang_transfer_fn(self.year)  # (NP, NL, NL)
        new_lang = self.pop.language.copy()
        for p_i in range(NP):
            mask = self.pop.province == p_i
            if not mask.any():
                continue
            cur = self.pop.language[mask]
            for l_i in range(NL):
                sub_mask = cur == l_i
                n = int(sub_mask.sum())
                if n == 0:
                    continue
                draws = self.rng.choice(NL, size=n, p=M[p_i, l_i])
                idx_full = np.flatnonzero(mask)[sub_mask]
                new_lang[idx_full] = draws
        self.pop.language = new_lang.astype(np.int8)

    def _apply_migration(self):
        M = self.migration_fn(self.year)  # (NP, NP)
        new_prov = self.pop.province.copy()
        for p_i in range(NP):
            mask_p = self.pop.province == p_i
            if not mask_p.any():
                continue
            base_row = M[p_i].copy()
            base_stay = base_row[p_i]
            base_leave = 1.0 - base_stay
            # Distribution of destinations given that you leave
            if base_leave > 0:
                leave_dest = base_row.copy()
                leave_dest[p_i] = 0
                leave_dest = leave_dest / leave_dest.sum()
            else:
                leave_dest = None

            for l_i in range(NL):
                sub_mask = mask_p & (self.pop.language == l_i)
                n = int(sub_mask.sum())
                if n == 0:
                    continue
                mult = float(self.migration_lang_mult[p_i, l_i])
                leave_p = min(1.0, base_leave * mult)
                if leave_p <= 0 or leave_dest is None:
                    continue
                # For each agent in this group, decide whether to leave
                leaves = self.rng.random(n) < leave_p
                n_leave = int(leaves.sum())
                if n_leave == 0:
                    continue
                dest_draws = self.rng.choice(NP, size=n_leave, p=leave_dest)
                idx_full = np.flatnonzero(sub_mask)
                new_prov[idx_full[leaves]] = dest_draws
        self.pop.province = new_prov.astype(np.int16)

    def _apply_natural_increase(self):
        """Add (or remove) agents based on per-province birth-minus-death rate.
        New births inherit the current language distribution of their province."""
        rates = self.natural_increase_fn(self.year)  # (NP,)
        for p_i in range(NP):
            mask = self.pop.province == p_i
            n_cur = int(mask.sum())
            if n_cur == 0:
                continue
            rate = rates[p_i]
            # Expected change in agent count
            delta = int(round(n_cur * rate))
            if delta == 0:
                continue
            if delta > 0:
                # Births: sample language from current provincial distribution
                cur_langs = self.pop.language[mask]
                lang_counts = np.bincount(cur_langs, minlength=NL).astype(float)
                lang_probs = lang_counts / lang_counts.sum()
                new_langs = self.rng.choice(NL, size=delta, p=lang_probs).astype(np.int8)
                new_provs = np.full(delta, p_i, dtype=np.int16)
                self.pop.province = np.concatenate([self.pop.province, new_provs])
                self.pop.language = np.concatenate([self.pop.language, new_langs])
            else:
                # Net deaths: remove uniformly at random from this province
                n_remove = min(-delta, n_cur)
                idx_in_prov = np.flatnonzero(mask)
                remove_idx = self.rng.choice(idx_in_prov, size=n_remove, replace=False)
                keep_mask = np.ones(self.pop.size(), dtype=bool)
                keep_mask[remove_idx] = False
                self.pop.province = self.pop.province[keep_mask]
                self.pop.language = self.pop.language[keep_mask]

    def _apply_immigration(self):
        total_people = self._imm_volume(self.year)
        n_new = int(total_people // self.scale)
        if n_new == 0:
            return
        alloc = self.imm_alloc_fn(self.year)
        prov_draws = self.rng.choice(NP, size=n_new, p=alloc)

        # Draw language separately per destination region (QC vs ROC)
        new_provs = []
        new_langs = []
        qc_idx = P_IDX["QC"]
        for region, mask in [
            ("QC", prov_draws == qc_idx),
            ("ROC", prov_draws != qc_idx),
        ]:
            n_region = int(mask.sum())
            if n_region == 0:
                continue
            fr_s = self._imm_fr_share(self.year, region)
            en_s = self._imm_en_share(self.year, region)
            allo_s = max(0.0, 1 - fr_s - en_s)
            lang_probs = np.array([fr_s, en_s, allo_s])
            lang_probs /= lang_probs.sum()
            lang_draws = self.rng.choice(NL, size=n_region, p=lang_probs)
            new_provs.append(prov_draws[mask].astype(np.int16))
            new_langs.append(lang_draws.astype(np.int8))

        if new_provs:
            self.pop.province = np.concatenate([self.pop.province] + new_provs)
            self.pop.language = np.concatenate([self.pop.language] + new_langs)

    def run(self, until_year: int = END_YEAR, verbose: bool = True):
        while self.year < until_year:
            self.step()
            if verbose and self.year % 10 == 0:
                total_m = self.pop.real_population() / 1e6
                c = self.pop.counts()
                fr_total = sum(c[(p, "fr")] for p in PROVINCES)
                fr_pct = 100 * fr_total / self.pop.real_population()
                qc_total = sum(c[("QC", l)] for l in LANGUAGES)
                qc_fr_pct = 100 * c[("QC", "fr")] / qc_total if qc_total else 0
                print(f"  {self.year}: {total_m:6.1f}M | fr={fr_pct:5.2f}% | QC fr={qc_fr_pct:5.1f}%")
        return self.history


# ---------------------------------------------------------------------------
# Calibration check helper
# ---------------------------------------------------------------------------

def calibration_report(history: list[dict]):
    """Compare simulated values to empirical targets at census years."""
    target_pop = load_population_targets()
    target_fr_can, target_fr_qc = load_francophone_share_targets()
    print(f"\n  {'year':>4}  {'sim_M':>7}  {'real_M':>7}  {'diff%':>6}  "
          f"{'sim_fr':>7}  {'real_fr':>7}  {'sim_QCfr':>8}  {'real_QCfr':>9}")
    print(f"  {'-'*4}  {'-'*7}  {'-'*7}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*8}  {'-'*9}")
    check_years = [1971, 1991, 2001, 2011, 2021, 2025, 2050, 2100]
    by_year = {r["year"]: r for r in history}
    for y in check_years:
        if y not in by_year:
            continue
        r = by_year[y]
        sim_m = r["total"] / 1e6
        real_m = target_pop(y)
        diff = 100 * (sim_m - real_m) / real_m
        fr_total = sum(r[f"{p}_fr"] for p in PROVINCES)
        sim_fr = fr_total / r["total"]
        real_fr = target_fr_can(y) if y <= 2021 else float('nan')
        qc_total = sum(r[f"QC_{l}"] for l in LANGUAGES)
        sim_qc_fr = r["QC_fr"] / qc_total if qc_total else 0
        real_qc_fr = target_fr_qc(y) if y <= 2021 else float('nan')
        print(f"  {y:>4}  {sim_m:>7.2f}  {real_m:>7.2f}  {diff:>+5.1f}%  "
              f"{sim_fr:>7.3f}  {real_fr:>7.3f}  {sim_qc_fr:>8.3f}  {real_qc_fr:>9.3f}")


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_all(histories: dict[str, list[dict]], out_dir: str = "plots", dpi: int = 300):
    """Generate and save all diagnostic plots as PNG files at *dpi* resolution.

    Parameters
    ----------
    histories : dict mapping scenario name → history list returned by sim.run()
    out_dir   : directory where PNG files are written (created if absent)
    dpi       : output resolution (default 300)
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    plt.rcParams.update({
        "figure.facecolor":  "#0e1117",
        "axes.facecolor":    "#0e1117",
        "axes.edgecolor":    "#444444",
        "axes.labelcolor":   "white",
        "axes.titlecolor":   "white",
        "xtick.color":       "white",
        "ytick.color":       "white",
        "text.color":        "white",
        "grid.color":        "#333333",
        "grid.linewidth":    0.6,
        "grid.alpha":        1.0,
        "legend.facecolor":  "#1a1d23",
        "legend.edgecolor":  "#444444",
        "savefig.facecolor": "#0e1117",
    })

    os.makedirs(out_dir, exist_ok=True)

    SCENARIO_COLORS = {"low": "#e07b39", "mid": "#3a7ebf", "high": "#3abf6e"}
    LANG_COLORS = {"fr": "#003f88", "en": "#d62828", "allo": "#f77f00"}
    LANG_LABELS = {"fr": "Francophone", "en": "Anglophone", "allo": "Allophone"}

    # Convenience: extract a time-series column from a history list
    def col(hist, key):
        return np.array([r[key] for r in hist])

    def years(hist):
        return np.array([r["year"] for r in hist])

    def savefig(fig, name):
        path = os.path.join(out_dir, f"{name}.png")
        fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="#0e1117")
        plt.close(fig)
        print(f"  Saved {path}")

    # ── 1. Total population — all scenarios ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    for scen, hist in histories.items():
        ax.plot(years(hist), col(hist, "total") / 1e6,
                color=SCENARIO_COLORS[scen], label=scen.capitalize(), linewidth=2)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8, label="Projection start")
    ax.set_title("Canada Total Population (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Population (millions)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    savefig(fig, "01_total_population")

    # ── 2. National francophone share — all scenarios ─────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    for scen, hist in histories.items():
        total = col(hist, "total")
        fr = np.array([sum(r[f"{p}_fr"] for p in PROVINCES) for r in hist])
        ax.plot(years(hist), 100 * fr / total,
                color=SCENARIO_COLORS[scen], label=scen.capitalize(), linewidth=2)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8, label="Projection start")
    ax.set_title("National Francophone Share (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Francophone share (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    savefig(fig, "02_national_fr_share")

    # ── 3. Quebec francophone share — all scenarios ───────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    for scen, hist in histories.items():
        qc_fr = col(hist, "QC_fr")
        qc_total = sum(col(hist, f"QC_{l}") for l in LANGUAGES)
        ax.plot(years(hist), 100 * qc_fr / qc_total,
                color=SCENARIO_COLORS[scen], label=scen.capitalize(), linewidth=2)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8, label="Projection start")
    ax.set_title("Quebec Francophone Share (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Francophone share in QC (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    savefig(fig, "03_qc_fr_share")

    # ── 4. National language breakdown — mid scenario (stacked area) ──────────
    hist = histories["mid"]
    total = col(hist, "total")
    fig, ax = plt.subplots(figsize=(10, 5))
    lang_series = {}
    for lang in LANGUAGES:
        lang_series[lang] = np.array([
            sum(r[f"{p}_{lang}"] for p in PROVINCES) for r in hist
        ]) / 1e6
    yr = years(hist)
    ax.stackplot(yr,
                 [lang_series[l] for l in LANGUAGES],
                 labels=[LANG_LABELS[l] for l in LANGUAGES],
                 colors=[LANG_COLORS[l] for l in LANGUAGES],
                 alpha=0.85)
    ax.axvline(2025, color="white", linestyle="--", linewidth=0.8)
    ax.set_title("National Language Breakdown — Mid Scenario (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Population (millions)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.2)
    savefig(fig, "04_national_lang_stacked_mid")

    # ── 5. Population by province — mid scenario ──────────────────────────────
    hist = histories["mid"]
    yr = years(hist)
    fig, ax = plt.subplots(figsize=(12, 6))
    palette = cm.tab20.colors
    for i, prov in enumerate(PROVINCES):
        prov_total = sum(col(hist, f"{prov}_{l}") for l in LANGUAGES)
        ax.plot(yr, prov_total / 1e6, label=prov, color=palette[i % len(palette)], linewidth=1.5)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8)
    ax.set_title("Population by Province — Mid Scenario (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Population (millions)")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(True, alpha=0.3)
    savefig(fig, "05_population_by_province_mid")

    # ── 6. Language shares for key provinces — mid scenario ───────────────────
    key_provs = ["QC", "ON", "NB", "BC", "AB"]
    fig, axes = plt.subplots(len(key_provs), 1, figsize=(10, 3 * len(key_provs)), sharex=True)
    hist = histories["mid"]
    yr = years(hist)
    for ax, prov in zip(axes, key_provs):
        prov_total = sum(col(hist, f"{prov}_{l}") for l in LANGUAGES)
        for lang in LANGUAGES:
            share = 100 * col(hist, f"{prov}_{lang}") / np.maximum(prov_total, 1)
            ax.plot(yr, share, label=LANG_LABELS[lang], color=LANG_COLORS[lang], linewidth=1.8)
        ax.axvline(2025, color="grey", linestyle="--", linewidth=0.7)
        ax.set_title(f"{prov} — Language Shares")
        ax.set_ylabel("%")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Year")
    fig.suptitle("Language Shares — Key Provinces — Mid Scenario (1971–2150)", y=1.01)
    fig.tight_layout()
    savefig(fig, "06_lang_shares_key_provinces_mid")

    # ── 7. Immigration-driven vs. natural growth (approximation) — mid ────────
    # Year-on-year total change
    hist = histories["mid"]
    yr = years(hist)
    total = col(hist, "total")
    delta = np.diff(total) / 1e3  # thousands
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(yr[1:], delta, width=0.8, color="#3a7ebf", alpha=0.7)
    ax.axvline(2025, color="red", linestyle="--", linewidth=0.9, label="Projection start")
    ax.set_title("Annual Population Change — Mid Scenario (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Change (thousands)")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    savefig(fig, "07_annual_pop_change_mid")

    # ── 8. Snapshot bar chart: provincial language shares at 2025 & 2100 ──────
    hist = histories["mid"]
    by_year = {r["year"]: r for r in hist}
    snap_years = [y for y in [2025, 2075, 2150] if y in by_year]
    fig, axes = plt.subplots(1, len(snap_years), figsize=(6 * len(snap_years), 6), sharey=True)
    if len(snap_years) == 1:
        axes = [axes]
    x = np.arange(len(PROVINCES))
    bar_w = 0.25
    for ax, snap_y in zip(axes, snap_years):
        r = by_year[snap_y]
        prov_totals = np.array([sum(r[f"{p}_{l}"] for l in LANGUAGES) for p in PROVINCES])
        bottom = np.zeros(len(PROVINCES))
        for lang in LANGUAGES:
            vals = np.array([r[f"{p}_{lang}"] for p in PROVINCES])
            shares = 100 * vals / np.maximum(prov_totals, 1)
            ax.bar(x, shares, bottom=bottom, label=LANG_LABELS[lang],
                   color=LANG_COLORS[lang], alpha=0.85)
            bottom += shares
        ax.set_title(f"Year {snap_y}")
        ax.set_xticks(x)
        ax.set_xticklabels(PROVINCES, rotation=45, ha="right", fontsize=8)
        ax.set_ylim(0, 100)
        if ax == axes[0]:
            ax.set_ylabel("Share (%)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")
    fig.suptitle("Provincial Language Composition Snapshots — Mid Scenario", y=1.02)
    fig.tight_layout()
    savefig(fig, "08_provincial_lang_snapshots_mid")

    # ── 9. Quebec's share of Canada total population — all scenarios ──────────
    fig, ax = plt.subplots(figsize=(10, 5))
    for scen, hist in histories.items():
        total = col(hist, "total")
        qc_total = sum(col(hist, f"QC_{l}") for l in LANGUAGES)
        ax.plot(years(hist), 100 * qc_total / total,
                color=SCENARIO_COLORS[scen], label=scen.capitalize(), linewidth=2)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8, label="Projection start")
    ax.set_title("Quebec's Share of Canada Total Population (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Quebec share of Canada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    savefig(fig, "09_qc_share_of_canada")

    # ── 10. Quebec francophones as share of Canada total — all scenarios ──────
    fig, ax = plt.subplots(figsize=(10, 5))
    for scen, hist in histories.items():
        total = col(hist, "total")
        qc_fr = col(hist, "QC_fr")
        ax.plot(years(hist), 100 * qc_fr / total,
                color=SCENARIO_COLORS[scen], label=scen.capitalize(), linewidth=2)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8, label="Projection start")
    ax.set_title("Quebec Francophones as Share of Canada Total Population (1971–2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("QC francophones / Canada total (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    savefig(fig, "10_qc_fr_share_of_canada")

    print(f"\nAll plots saved to '{out_dir}/' at {dpi} DPI.")


# ---------------------------------------------------------------------------
# Parameter plots
# ---------------------------------------------------------------------------

def plot_parameters(out_dir: str = "plots", dpi: int = 300):
    """Dump every model input parameter as a time-series plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    plt.rcParams.update({
        "figure.facecolor":  "#0e1117",
        "axes.facecolor":    "#0e1117",
        "axes.edgecolor":    "#444444",
        "axes.labelcolor":   "white",
        "axes.titlecolor":   "white",
        "xtick.color":       "white",
        "ytick.color":       "white",
        "text.color":        "white",
        "grid.color":        "#333333",
        "grid.linewidth":    0.6,
        "grid.alpha":        1.0,
        "legend.facecolor":  "#1a1d23",
        "legend.edgecolor":  "#444444",
        "savefig.facecolor": "#0e1117",
    })

    os.makedirs(out_dir, exist_ok=True)

    YRS = np.arange(START_YEAR, END_YEAR + 1)

    def savefig(fig, name):
        path = os.path.join(out_dir, f"{name}.png")
        fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="#0e1117")
        plt.close(fig)
        print(f"  Saved {path}")

    def vline(ax, year=2025):
        ax.axvline(year, color="#666666", linestyle="--", linewidth=0.8, label="Proj. start")

    # ── P01: Immigration volume — base + scenario bands ──────────────────────
    imm_vol_fn = load_immigration_volume_fn()
    scenarios  = load_scenarios()
    base_vol   = np.array([imm_vol_fn(y) for y in YRS])
    fig, ax = plt.subplots(figsize=(11, 4))
    scen_styles = {"low": ("#e07b39", 0.4), "mid": ("#3a7ebf", 1.0), "high": ("#3abf6e", 0.4)}
    for scen, (col, alpha) in scen_styles.items():
        mult = scenarios[scen]["volume_multiplier_post2025"]
        vol  = base_vol.copy()
        vol[YRS > 2025] *= mult
        lw = 2.0 if scen == "mid" else 1.4
        ax.plot(YRS, vol / 1e3, color=col, alpha=min(alpha + 0.2, 1.0), linewidth=lw, label=scen.capitalize())
    vline(ax)
    ax.set_title("P01 — Immigration Volume by Scenario")
    ax.set_xlabel("Year"); ax.set_ylabel("Annual landings (thousands)")
    ax.legend(); ax.grid(True, alpha=0.3)
    savefig(fig, "P01_immigration_volume")

    # ── P02: QC & ROC francophone share of immigrants ────────────────────────
    fr_qc_fn, en_qc_fn, fr_roc_fn, en_roc_fn = load_immigration_composition_fns()
    fr_qc  = np.array([fr_qc_fn(y)  for y in YRS])
    en_qc  = np.array([en_qc_fn(y)  for y in YRS])
    en_roc = np.array([en_roc_fn(y) for y in YRS])
    fig, axes = plt.subplots(1, 2, figsize=(13, 4), sharey=False)

    # Left panel: QC (single trajectory)
    ax = axes[0]
    ax.plot(YRS, 100*fr_qc,               color="#003f88", linewidth=2, label="Francophone")
    ax.plot(YRS, 100*en_qc,               color="#d62828", linewidth=2, label="Anglophone")
    ax.plot(YRS, 100*(1-fr_qc-en_qc),     color="#f77f00", linewidth=2, label="Allophone")
    vline(ax)
    ax.set_title("P02 — Language Share of QC immigrants")
    ax.set_xlabel("Year"); ax.set_ylabel("Share (%)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    # Right panel: ROC — three scenario lines for francophone share
    ax = axes[1]
    roc_scen_styles = {
        "low":  ("#e07b39", 1.4),
        "mid":  ("#3a7ebf", 2.0),
        "high": ("#3abf6e", 1.4),
    }
    base_fr_roc = np.array([fr_roc_fn(y) for y in YRS])
    for scen, (col, lw) in roc_scen_styles.items():
        roc_override = scenarios[scen]["roc_fr_share_post2025"]
        fr_roc_scen = base_fr_roc.copy()
        if roc_override is not None:
            fr_roc_scen[YRS > 2025] = roc_override
        ax.plot(YRS, 100*fr_roc_scen, color=col, linewidth=lw, label=f"Fr — {scen.capitalize()}")
    ax.plot(YRS, 100*en_roc,          color="#d62828", linewidth=2, label="Anglophone", linestyle="--")
    ax.plot(YRS, 100*(1-base_fr_roc-en_roc), color="#f77f00", linewidth=1.2, label="Allophone (base)", linestyle=":")
    vline(ax)
    ax.set_title("P02 — Language Share of ROC immigrants")
    ax.set_xlabel("Year"); ax.set_ylabel("Share (%)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    fig.tight_layout()
    savefig(fig, "P02_immigration_composition")

    # ── P03: Provincial allocation of immigration — key provinces ─────────────
    alloc_fn = load_immigration_provincial_alloc_fn()
    key_provs_alloc = ["QC", "ON", "AB", "BC", "MB", "SK"]
    alloc_mat = np.array([alloc_fn(y) for y in YRS])   # (n_years, NP)
    palette = cm.tab10.colors
    fig, ax = plt.subplots(figsize=(11, 4))
    for i, p in enumerate(key_provs_alloc):
        ax.plot(YRS, 100*alloc_mat[:, P_IDX[p]], color=palette[i], linewidth=2, label=p)
    vline(ax)
    ax.set_title("P03 — Provincial Allocation of Immigration (key provinces)")
    ax.set_xlabel("Year"); ax.set_ylabel("Share of annual landings (%)")
    ax.legend(ncol=2, fontsize=8); ax.grid(True, alpha=0.3)
    savefig(fig, "P03_immigration_provincial_allocation")

    # ── P04: Effective national immigration fr fraction vs national fr share ──
    # (The "gap" diagnostic — this drives the dilution engine)
    fig, ax = plt.subplots(figsize=(11, 4))
    f_imm = np.array([
        alloc_fn(y)[P_IDX["QC"]] * fr_qc_fn(y) +
        (1 - alloc_fn(y)[P_IDX["QC"]]) * fr_roc_fn(y)
        for y in YRS
    ])
    ax.plot(YRS, 100*f_imm, color="#9b2226", linewidth=2, label="Incoming immigrant fr% (mid)")
    ax.fill_between(YRS, 100*f_imm, alpha=0.12, color="#9b2226")
    ax.annotate("Gap drives dilution", xy=(2060, 100*f_imm[YRS==2060][0]+0.5),
                fontsize=8, color="#9b2226")
    vline(ax)
    ax.set_title("P04 — Effective Francophone Fraction of Immigration Stream (mid)")
    ax.set_xlabel("Year"); ax.set_ylabel("fr share of annual immigrants (%)")
    ax.set_ylim(0, 25)
    ax.legend(); ax.grid(True, alpha=0.3)
    savefig(fig, "P04_immigration_fr_fraction")

    # ── P05: Language transfer rates — ROC ───────────────────────────────────
    lt_fn = load_language_transfer_fn()
    roc_idx = P_IDX["ON"]   # ON is representative ROC province

    transfer_pairs = [
        ("fr→en", 0, 1, "#d62828", "-"),
        ("fr→allo", 0, 2, "#d62828", "--"),
        ("en→fr", 1, 0, "#003f88", "-"),
        ("allo→en", 2, 1, "#f77f00", "-"),
        ("allo→fr", 2, 0, "#f77f00", "--"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4), sharey=False)
    for ax, prov_name, p_idx, title_tag in [
        (axes[0], "ON (repr. ROC)", P_IDX["ON"], "ROC (Ontario)"),
        (axes[1], "QC",             P_IDX["QC"], "Quebec"),
        (axes[2], "NB",             P_IDX["NB"], "New Brunswick"),
    ]:
        for label, fl, tl, col, ls in transfer_pairs:
            if fl == tl:
                continue
            rates = np.array([lt_fn(y)[p_idx, fl, tl] * 1000 for y in YRS])
            ax.plot(YRS, rates, color=col, linestyle=ls, linewidth=1.8, label=label)
        vline(ax)
        ax.set_title(f"P05 — Annual Language Transfer Rates — {title_tag}")
        ax.set_xlabel("Year"); ax.set_ylabel("Rate (‰/yr)")
        ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    savefig(fig, "P05_language_transfer_rates")

    # ── P06: Natural increase rates — all provinces ───────────────────────────
    ni_fn = load_natural_increase_fn()
    ni_mat = np.array([ni_fn(y) for y in YRS])   # (n_years, NP)
    groups = {
        "Atlantic": ["NL", "PE", "NS", "NB"],
        "Central":  ["QC", "ON"],
        "Prairies": ["MB", "SK", "AB"],
        "Pacific & Territories": ["BC", "YT", "NT", "NU"],
    }
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True)
    palette14 = cm.tab20.colors
    for ax, (group_name, provs) in zip(axes.flat, groups.items()):
        for i, p in enumerate(provs):
            ax.plot(YRS, 100*ni_mat[:, P_IDX[p]], label=p,
                    color=palette14[i], linewidth=2)
        ax.axhline(0, color="#888888", linewidth=0.7, linestyle=":")
        vline(ax)
        ax.set_title(f"P06 — Natural Increase Rate — {group_name}")
        ax.set_ylabel("Rate (%/yr)")
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    axes[1][0].set_xlabel("Year"); axes[1][1].set_xlabel("Year")
    fig.tight_layout()
    savefig(fig, "P06_natural_increase_rates")

    # ── P07: Scenario fr_share offsets applied to immigration composition ─────
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    scen_cols    = {"low": "#e07b39", "mid": "#3a7ebf", "high": "#3abf6e"}
    scen_offsets = {s: d["fr_share_offset_post2025"] for s, d in scenarios.items()
                    if s in scen_cols}
    for ax, (region, base_fn) in [
        (axes[0], ("QC", fr_qc_fn)),
        (axes[1], ("ROC", fr_roc_fn)),
    ]:
        base = np.array([base_fn(y) for y in YRS])
        for scen, offset in scen_offsets.items():
            effective = base.copy()
            effective[YRS > 2025] = np.clip(effective[YRS > 2025] + offset, 0, 1)
            lw = 2.2 if scen == "mid" else 1.4
            ax.plot(YRS, 100*effective, color=scen_cols[scen], linewidth=lw,
                    label=f"{scen.capitalize()} (offset {offset:+.3f})")
        vline(ax)
        ax.set_title(f"P07 — Effective fr% of {region} Immigrants by Scenario")
        ax.set_xlabel("Year"); ax.set_ylabel("Francophone share (%)")
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    savefig(fig, "P07_scenario_fr_offsets")

    # ── P08: Migration language multipliers (static heatmap) ──────────────────
    from loaders import load_migration_lang_multipliers
    mult = load_migration_lang_multipliers()   # (NP, NL)
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(mult.T, aspect="auto", cmap="RdYlGn", vmin=0.5, vmax=1.5)
    ax.set_yticks(range(NL)); ax.set_yticklabels(LANGUAGES)
    ax.set_xticks(range(NP)); ax.set_xticklabels(PROVINCES, rotation=45, ha="right")
    for pi in range(NP):
        for li in range(NL):
            ax.text(pi, li, f"{mult[pi,li]:.2f}", ha="center", va="center",
                    fontsize=7, color="black")
    plt.colorbar(im, ax=ax, label="Out-migration multiplier (1.0 = same as average)")
    ax.set_title("P08 — Interprovincial Migration Language Multipliers (static)")
    ax.set_xlabel("Province"); ax.set_ylabel("Language group")
    fig.tight_layout()
    savefig(fig, "P08_migration_language_multipliers")

    # ── P09: Two forces behind the post-2050 fr-share deceleration ───────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))

    # Left: QC natural increase rate
    ni_fn = load_natural_increase_fn()
    ni_qc = np.array([ni_fn(y)[P_IDX["QC"]] for y in YRS])
    ax1.plot(YRS, 100 * ni_qc, color="#3a7ebf", linewidth=2)
    ax1.axhline(0, color="#888888", linewidth=0.7, linestyle=":")
    ax1.axvline(2050, color="#aaaaaa", linewidth=0.8, linestyle="--", label="2050 plateau")
    vline(ax1)
    ax1.set_title("P09 — QC Natural Increase Rate")
    ax1.set_xlabel("Year"); ax1.set_ylabel("Rate (%/yr)")
    ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3)

    # Right: QC francophone immigration share (mid scenario)
    fr_qc_arr = np.array([fr_qc_fn(y) for y in YRS])
    ax2.plot(YRS, 100 * fr_qc_arr, color="#3a7ebf", linewidth=2)
    ax2.axvline(2050, color="#aaaaaa", linewidth=0.8, linestyle="--", label="2050 slowdown")
    vline(ax2)
    ax2.set_title("P09 — QC Francophone Share of Immigrants")
    ax2.set_xlabel("Year"); ax2.set_ylabel("Share (%)")
    ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)

    fig.suptitle("Forces behind post-2050 francophone share deceleration", color="white", fontsize=11)
    fig.tight_layout()
    savefig(fig, "P09_fr_share_deceleration_drivers")

    print(f"\nAll parameter plots saved to '{out_dir}/' at {dpi} DPI.")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    histories = {}
    for scen in ["low", "mid", "high"]:
        print(f"\n=== Scenario: {scen} ===")
        t0 = time.time()
        sim = CanadaSimulator(scenario_name=scen, scale=SCALE, seed=42)
        sim.run(until_year=2150, verbose=True)
        elapsed = time.time() - t0
        print(f"  [{elapsed:.1f}s]")
        calibration_report(sim.history)
        histories[scen] = sim.history

    print("\n=== Generating output plots ===")
    plot_all(histories, out_dir="plots", dpi=300)

    print("\n=== Generating parameter plots ===")
    plot_parameters(out_dir="plots", dpi=300)
