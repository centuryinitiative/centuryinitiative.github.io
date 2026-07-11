"""
Plot the share of annual immigrant landings going to Quebec vs. the Rest of
Canada (ROC), 1971-2150.

QC share comes directly from data/immigration_provincial_allocation.csv;
ROC is its complement (1 - QC).

    python3 plot_qc_roc_immigration.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from canada_sim import START_YEAR, END_YEAR
from loaders import P_IDX, load_immigration_provincial_alloc_fn

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


def main(out_dir: str = "plots", dpi: int = 300):
    os.makedirs(out_dir, exist_ok=True)
    yrs = np.arange(START_YEAR, END_YEAR + 1)
    alloc_fn = load_immigration_provincial_alloc_fn()
    qc_share = np.array([alloc_fn(y)[P_IDX["QC"]] for y in yrs])
    roc_share = 1.0 - qc_share

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(yrs, 100 * roc_share, color="#d62828", linewidth=2,
            label="Rest of Canada")
    ax.plot(yrs, 100 * qc_share, color="#3a7ebf", linewidth=2, label="Quebec")
    ax.axvline(2025, color="grey", linestyle="--", linewidth=0.8,
               label="Projection start")
    ax.set_title("Immigrant Landings: Quebec vs. Rest of Canada (1971-2150)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of annual landings (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(True, alpha=0.3)

    path = os.path.join(out_dir, "P10_immigration_qc_vs_roc.png")
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="#0e1117")
    plt.close(fig)
    print(f"  Saved {path}")


if __name__ == "__main__":
    main()
