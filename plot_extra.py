"""
Extra diagnostic plots (7 total):

  E01  Gap f(t) − f_imm over time, per scenario (linear + log scale)
  E02  Overlay: national fr share vs. moving f_imm target
  E03  Absolute francophone population (millions), all scenarios
  E04  ROC francophone share over time, all scenarios
  E05  New Brunswick language shares, all scenarios
  E06  Annual Δf decomposed: immigration dilution vs. other (mid scenario)
  E07  Stabilization threshold: required f_imm to hold share constant vs. actual f_imm
"""
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from loaders import (
    PROVINCES, P_IDX, LANGUAGES,
    load_immigration_composition_fns,
    load_immigration_provincial_alloc_fn,
    load_immigration_volume_fn,
    load_scenarios,
)
from canada_sim import CanadaSimulator, SCALE, START_YEAR, END_YEAR

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SCENARIO_COLORS = {"low": "#e07b39", "mid": "#3a7ebf", "high": "#3abf6e"}
SCENARIO_NAMES  = ["low", "mid", "high"]

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
    "legend.facecolor":  "#1a1d23",
    "legend.edgecolor":  "#444444",
    "savefig.facecolor": "#0e1117",
})

def savefig(fig, name, dpi=300):
    path = f"plots/{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="#0e1117")
    plt.close(fig)
    print(f"  Saved {path}")

def col(hist, key):
    return np.array([r[key] for r in hist])

def years(hist):
    return np.array([r["year"] for r in hist])


# ---------------------------------------------------------------------------
# Compute effective f_imm(year) for each scenario
# ---------------------------------------------------------------------------

fr_qc_fn, _en_qc_fn, fr_roc_fn, _en_roc_fn = load_immigration_composition_fns()
alloc_fn  = load_immigration_provincial_alloc_fn()
imm_vol_fn = load_immigration_volume_fn()
scenarios  = load_scenarios()
qc_idx     = P_IDX["QC"]

YRS = np.arange(START_YEAR, END_YEAR + 1)

def compute_f_imm(scen_name):
    """Return array of effective national francophone share of immigrants, shape (n_years,)."""
    params      = scenarios[scen_name]
    offset      = params["fr_share_offset_post2025"]
    roc_override = params.get("roc_fr_share_post2025")
    out = []
    for y in YRS:
        alloc    = alloc_fn(y)
        qc_share = alloc[qc_idx]
        fr_qc = fr_qc_fn(y)
        if y > 2025:
            fr_qc = float(np.clip(fr_qc + offset, 0.0, 1.0))
        if y > 2025 and roc_override is not None:
            fr_roc = roc_override
        else:
            fr_roc = fr_roc_fn(y)
            if y > 2025:
                fr_roc = float(np.clip(fr_roc + offset, 0.0, 1.0))
        out.append(qc_share * fr_qc + (1.0 - qc_share) * fr_roc)
    return np.array(out)

def compute_n_imm(scen_name):
    """Return array of annual immigrant count (real people), shape (n_years,)."""
    mult = scenarios[scen_name]["volume_multiplier_post2025"]
    out = []
    for y in YRS:
        v = imm_vol_fn(y)
        if y > 2025:
            v *= mult
        out.append(v)
    return np.array(out)

f_imm_by_scen = {s: compute_f_imm(s) for s in SCENARIO_NAMES}
n_imm_by_scen = {s: compute_n_imm(s) for s in SCENARIO_NAMES}


# ---------------------------------------------------------------------------
# Run simulations
# ---------------------------------------------------------------------------

print("Running simulations...")
histories = {}
for scen in SCENARIO_NAMES:
    t0 = time.time()
    sim = CanadaSimulator(scenario_name=scen, scale=SCALE, seed=42)
    sim.run(until_year=END_YEAR, verbose=False)
    histories[scen] = sim.history
    print(f"  {scen}: {time.time()-t0:.1f}s")

print("\nGenerating plots...")

# Convenience: national fr share time-series from history
def national_fr_share(hist):
    total = col(hist, "total")
    fr    = np.array([sum(r[f"{p}_fr"] for p in PROVINCES) for r in hist])
    return fr / total

def national_fr_abs(hist):
    return np.array([sum(r[f"{p}_fr"] for p in PROVINCES) for r in hist])


# ---------------------------------------------------------------------------
# E01 — Gap f(t) − f_imm, linear + log
# ---------------------------------------------------------------------------

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

for scen in SCENARIO_NAMES:
    hist = histories[scen]
    yr   = years(hist)
    ft   = national_fr_share(hist)                  # f(t), length = len(yr)
    fi   = f_imm_by_scen[scen]                      # f_imm, length = len(YRS)
    # Align: YRS and yr both start at START_YEAR
    gap  = ft - fi[:len(yr)]

    ax1.plot(yr, 100 * gap, color=SCENARIO_COLORS[scen],
             label=scen.capitalize(), linewidth=2)
    # Log scale: only plot where gap > 0
    pos = gap > 0
    ax2.semilogy(yr[pos], 100 * gap[pos], color=SCENARIO_COLORS[scen],
                 label=scen.capitalize(), linewidth=2)

for ax in (ax1, ax2):
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8,
               label="Projection start")
    ax.set_xlabel("Year")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

ax1.set_title("Gap f(t) − f_imm (linear)")
ax1.set_ylabel("Gap (percentage points)")
ax2.set_title("Gap f(t) − f_imm (log scale)")
ax2.set_ylabel("Gap (pp, log scale)")

fig.suptitle("E01 — Dilution Gap: National Fr Share minus Immigrant Fr Share",
             color="white")
fig.tight_layout()
savefig(fig, "E01_dilution_gap")


# ---------------------------------------------------------------------------
# E02 — Overlay: f(t) vs f_imm
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5))

for scen in SCENARIO_NAMES:
    hist = histories[scen]
    yr   = years(hist)
    ft   = national_fr_share(hist)
    fi   = f_imm_by_scen[scen][:len(yr)]

    ax.plot(yr, 100 * ft, color=SCENARIO_COLORS[scen],
            label=f"{scen.capitalize()} — f(t)", linewidth=2)
    ax.plot(yr, 100 * fi, color=SCENARIO_COLORS[scen],
            label=f"{scen.capitalize()} — f_imm", linewidth=1.5,
            linestyle="--", alpha=0.7)

ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8)
ax.set_title("E02 — National Francophone Share f(t) vs. Immigrant Fr Share f_imm (1971–2150)")
ax.set_xlabel("Year")
ax.set_ylabel("Francophone share (%)")
ax.legend(fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)
savefig(fig, "E02_ft_vs_fimm_overlay")


# ---------------------------------------------------------------------------
# E03 — Absolute francophone population
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5))

for scen in SCENARIO_NAMES:
    hist = histories[scen]
    yr   = years(hist)
    fr_m = national_fr_abs(hist) / 1e6
    ax.plot(yr, fr_m, color=SCENARIO_COLORS[scen],
            label=scen.capitalize(), linewidth=2)

ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8,
           label="Projection start")
ax.set_title("E03 — Absolute Francophone Population, Canada (1971–2150)")
ax.set_xlabel("Year")
ax.set_ylabel("Francophones (millions)")
ax.legend()
ax.grid(True, alpha=0.3)
savefig(fig, "E03_absolute_francophone_pop")


# ---------------------------------------------------------------------------
# E04 — ROC francophone share
# ---------------------------------------------------------------------------

roc_provs = [p for p in PROVINCES if p != "QC"]

def roc_fr_share(hist):
    roc_fr    = np.array([sum(r[f"{p}_fr"]  for p in roc_provs) for r in hist])
    roc_total = np.array([sum(r[f"{p}_{l}"] for p in roc_provs for l in LANGUAGES)
                          for r in hist])
    return roc_fr / np.maximum(roc_total, 1)

fig, ax = plt.subplots(figsize=(10, 5))

for scen in SCENARIO_NAMES:
    hist = histories[scen]
    yr   = years(hist)
    ax.plot(yr, 100 * roc_fr_share(hist), color=SCENARIO_COLORS[scen],
            label=scen.capitalize(), linewidth=2)

ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8,
           label="Projection start")
ax.set_title("E04 — ROC Francophone Share (Outside Quebec) (1971–2150)")
ax.set_xlabel("Year")
ax.set_ylabel("Francophone share in ROC (%)")
ax.legend()
ax.grid(True, alpha=0.3)
savefig(fig, "E04_roc_fr_share")


# ---------------------------------------------------------------------------
# E05 — New Brunswick language shares
# ---------------------------------------------------------------------------

LANG_COLORS  = {"fr": "#003f88", "en": "#d62828", "allo": "#f77f00"}
LANG_LABELS  = {"fr": "Francophone", "en": "Anglophone", "allo": "Allophone"}

fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)

for ax, scen in zip(axes, SCENARIO_NAMES):
    hist = histories[scen]
    yr   = years(hist)
    nb_total = sum(col(hist, f"NB_{l}") for l in LANGUAGES)
    for lang in LANGUAGES:
        share = 100 * col(hist, f"NB_{lang}") / np.maximum(nb_total, 1)
        ax.plot(yr, share, color=LANG_COLORS[lang],
                label=LANG_LABELS[lang], linewidth=1.8)
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.7)
    ax.set_title(f"{scen.capitalize()}")
    ax.set_xlabel("Year")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

axes[0].set_ylabel("Share (%)")
fig.suptitle("E05 — New Brunswick Language Shares (1971–2150)", color="white")
fig.tight_layout()
savefig(fig, "E05_nb_language_shares")


# ---------------------------------------------------------------------------
# E06 — Δf decomposition: immigration vs. other (mid scenario, smoothed)
# ---------------------------------------------------------------------------

SMOOTH = 10   # year rolling average to reduce Monte Carlo noise

def rolling_mean(arr, w):
    return np.convolve(arr, np.ones(w) / w, mode="same")

hist_mid = histories["mid"]
yr_mid   = years(hist_mid)
ft_mid   = national_fr_share(hist_mid)
fi_mid   = f_imm_by_scen["mid"][:len(yr_mid)]
ni_mid   = n_imm_by_scen["mid"][:len(yr_mid)]   # immigrants per year (real people)
nt_mid   = col(hist_mid, "total")                # total population (real people)

# Year-on-year total Δf
delta_f_total = np.diff(ft_mid)
yr_d          = yr_mid[1:]

# Immigration contribution each year:
#   Δf_imm = (f_imm(t) − f(t)) × N_imm(t) / N(t+1)
f_gap      = fi_mid[:-1] - ft_mid[:-1]
r_imm      = ni_mid[:-1] / np.maximum(nt_mid[1:], 1)
delta_f_imm   = f_gap * r_imm
delta_f_other = delta_f_total - delta_f_imm

# Smooth
delta_f_total_s = rolling_mean(delta_f_total, SMOOTH)
delta_f_imm_s   = rolling_mean(delta_f_imm,   SMOOTH)
delta_f_other_s = rolling_mean(delta_f_other, SMOOTH)

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(yr_d, 100 * delta_f_imm_s,   color="#9b2226", linewidth=2,
        label="Immigration dilution")
ax.plot(yr_d, 100 * delta_f_other_s, color="#3a7ebf", linewidth=2,
        label="Language transfer + natural increase")
ax.plot(yr_d, 100 * delta_f_total_s, color="white",   linewidth=1.5,
        linestyle="--", alpha=0.6, label="Total Δf")
ax.axhline(0, color="#555555", linewidth=0.7)
ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8,
           label="Projection start")
ax.set_title(f"E06 — Annual Δf Decomposition — Mid Scenario ({SMOOTH}-yr smoothed)")
ax.set_xlabel("Year")
ax.set_ylabel("Annual change in fr share (pp/yr)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
savefig(fig, "E06_delta_f_decomposition_mid")


# ---------------------------------------------------------------------------
# E07 — Stabilization threshold vs actual f_imm
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5))

for scen in SCENARIO_NAMES:
    hist = histories[scen]
    yr   = years(hist)
    ft   = national_fr_share(hist)
    fi   = f_imm_by_scen[scen][:len(yr)]

    # Threshold = f(t) itself (what f_imm would need to equal to hold share flat)
    ax.plot(yr, 100 * ft, color=SCENARIO_COLORS[scen],
            label=f"{scen.capitalize()} — required f_imm", linewidth=2)
    ax.plot(yr, 100 * fi, color=SCENARIO_COLORS[scen],
            label=f"{scen.capitalize()} — actual f_imm",
            linewidth=1.5, linestyle="--", alpha=0.7)

ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8)
ax.set_title("E07 — Stabilization Threshold: Required vs Actual Immigrant Fr Share (1971–2150)")
ax.set_xlabel("Year")
ax.set_ylabel("Francophone share (%)")
ax.legend(fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)

# Annotate the gap at 2025
ax.annotate("← policy gap →", xy=(2040, 12), fontsize=8,
            color="#aaaaaa", ha="center")

savefig(fig, "E07_stabilization_threshold")

print("\nDone. All plots saved to plots/")
