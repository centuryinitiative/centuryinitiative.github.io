"""
Plot the effective francophone share of all immigrants to Canada per year,
broken out by scenario (low / mid / high).

Formula:
    f_imm(y) = alloc_QC(y) * fr_qc_scenario(y)
             + (1 − alloc_QC(y)) * fr_roc_scenario(y)

This is the f_imm term in the share-dilution equation and represents the
equilibrium level that the national francophone share converges toward.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from loaders import (
    P_IDX,
    load_immigration_composition_fns,
    load_immigration_provincial_alloc_fn,
    load_scenarios,
)

START_YEAR = 1971
END_YEAR   = 2150
YRS = np.arange(START_YEAR, END_YEAR + 1)

# Load base functions
fr_qc_fn, _en_qc_fn, fr_roc_fn, _en_roc_fn = load_immigration_composition_fns()
alloc_fn = load_immigration_provincial_alloc_fn()
scenarios = load_scenarios()

qc_idx = P_IDX["QC"]

SCENARIO_COLORS = {"low": "#e07b39", "mid": "#3a7ebf", "high": "#3abf6e"}

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

fig, ax = plt.subplots(figsize=(10, 5))

for scen_name in ["low", "mid", "high"]:
    params = scenarios[scen_name]
    offset = params["fr_share_offset_post2025"]
    roc_override = params.get("roc_fr_share_post2025")

    f_imm = []
    for y in YRS:
        alloc = alloc_fn(y)
        qc_share = alloc[qc_idx]

        # QC francophone share of immigrants
        fr_qc = fr_qc_fn(y)
        if y > 2025:
            fr_qc = float(np.clip(fr_qc + offset, 0.0, 1.0))

        # ROC francophone share of immigrants
        if y > 2025 and roc_override is not None:
            fr_roc = roc_override
        else:
            fr_roc = fr_roc_fn(y)
            if y > 2025:
                fr_roc = float(np.clip(fr_roc + offset, 0.0, 1.0))

        f_imm.append(qc_share * fr_qc + (1.0 - qc_share) * fr_roc)

    ax.plot(YRS, 100 * np.array(f_imm),
            color=SCENARIO_COLORS[scen_name],
            label=scen_name.capitalize(),
            linewidth=2)

ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8, label="Projection start")
ax.set_title("Effective Francophone Share of Immigrants to Canada (1971–2150)")
ax.set_xlabel("Year")
ax.set_ylabel("Francophone share of annual immigrants (%)")
ax.legend()
ax.grid(True, alpha=0.3)

out = "plots/imm_fr_share_by_scenario.png"
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="#0e1117")
plt.close(fig)
print(f"Saved {out}")
