"""
Francophone-Africa sensitivity: 3 scenarios for ROC immigrant fr_share post-2025.

  roc_4pct  — fr share of ROC immigrants held flat at 4% after 2025
  roc_6pct  — fr share of ROC immigrants held flat at 6% after 2025
  roc_8pct  — fr share of ROC immigrants held flat at 8% after 2025

Plots national francophone share 1971–2150. The mid scenario (default
immigration_composition.csv trajectory, which peaks at 9.5% in 2030 before
declining) is shown as a dashed reference.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from canada_sim import CanadaSimulator
from loaders import PROVINCES, LANGUAGES

SCENARIOS = [
    ("roc_4pct", "#d85a30", "4% ROC (back to pre-2015 baseline)"),
    ("roc_6pct", "#fac775", "6% ROC (partial retrenchment)"),
    ("roc_8pct", "#5dcaa5", "8% ROC (near-current level sustained)"),
]
MID_COLOR  = "#aaaaaa"


def national_fr_share(history):
    years, shares = [], []
    for r in history:
        fr = sum(r[f"{p}_fr"] for p in PROVINCES)
        years.append(r["year"])
        shares.append(100 * fr / r["total"])
    return np.array(years), np.array(shares)


def qc_fr_of_canada(history):
    years, shares = [], []
    for r in history:
        years.append(r["year"])
        shares.append(100 * r["QC_fr"] / r["total"])
    return np.array(years), np.array(shares)


def main():
    results = {}

    histories = {}

    # Run mid baseline
    print("Running mid (baseline)...")
    sim = CanadaSimulator(scenario_name="mid", scale=100, seed=42)
    sim.run(until_year=2150, verbose=False)
    histories["mid"] = sim.history

    # Run the 3 ROC sensitivity scenarios
    for scen, _, label in SCENARIOS:
        print(f"Running {scen}...")
        sim = CanadaSimulator(scenario_name=scen, scale=100, seed=42)
        sim.run(until_year=2150, verbose=False)
        histories[scen] = sim.history

    results     = {k: national_fr_share(h) for k, h in histories.items()}
    results_qcfr = {k: qc_fr_of_canada(h)  for k, h in histories.items()}

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Mid baseline (dashed reference)
    yrs, shr = results["mid"]
    ax.plot(yrs, shr, color=MID_COLOR, linewidth=1.6, linestyle="--",
            label="Mid baseline (default trajectory)", alpha=0.7)

    # Three ROC scenarios — historical portion (≤2021) in white, then coloured
    for scen, color, label in SCENARIOS:
        yrs, shr = results[scen]
        hist_mask = yrs <= 2021
        # Historical (identical across scenarios — show only once via mid, but
        # draw a white segment here too so lines connect cleanly)
        ax.plot(yrs[hist_mask], shr[hist_mask], color="white", linewidth=2.5)
        proj_mask = yrs >= 2021
        ax.plot(yrs[proj_mask], shr[proj_mask], color=color, linewidth=2.5, label=label)

    # Reference lines
    for lvl in [20, 15, 10, 5]:
        ax.axhline(lvl, color="#333", linestyle=":", linewidth=0.7)
    ax.axvline(2025, color="#666", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(2025.5, 22.5, "calibration | projection", color="#888", fontsize=9)

    ax.set_title(
        "National Francophone Share — ROC immigration fr% sensitivity\n"
        "1971–2150 · agent-based simulation",
        color="white", fontsize=15, pad=18,
    )
    ax.set_xlabel("Year", color="white", fontsize=12)
    ax.set_ylabel("Francophone share of Canada (%)", color="white", fontsize=12)
    ax.set_xlim(1971, 2150)
    ax.set_ylim(0, 28)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#444")
    ax.grid(True, color="#222", linewidth=0.5)

    leg = ax.legend(loc="upper right", facecolor="#1a1d23",
                    edgecolor="#444", labelcolor="white", fontsize=10)
    leg.get_frame().set_alpha(0.9)

    fig.text(0.02, 0.02,
             "ROC fr% held flat from 2026 onward. QC selection unchanged. "
             "Immigration volume = mid scenario.",
             color="#888", fontsize=8)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "plots", "roc_fr_sensitivity.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150, facecolor="#0e1117")
    print(f"\nSaved: {out}")

    # ── Plot 2: QC francophones as share of Canada total ──────────────────────
    fig, ax = plt.subplots(figsize=(13, 7), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    yrs, shr = results_qcfr["mid"]
    ax.plot(yrs, shr, color=MID_COLOR, linewidth=1.6, linestyle="--",
            label="Mid baseline", alpha=0.7)

    for scen, color, label in SCENARIOS:
        yrs, shr = results_qcfr[scen]
        hist_mask = yrs <= 2021
        ax.plot(yrs[hist_mask], shr[hist_mask], color="white", linewidth=2.5)
        proj_mask = yrs >= 2021
        ax.plot(yrs[proj_mask], shr[proj_mask], color=color, linewidth=2.5, label=label)

    for lvl in [15, 10, 5]:
        ax.axhline(lvl, color="#333", linestyle=":", linewidth=0.7)
    ax.axvline(2025, color="#666", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(2025.5, 19.5, "calibration | projection", color="#888", fontsize=9)

    ax.set_title(
        "Quebec Francophones as Share of Canada Total Population\n"
        "ROC immigration fr% sensitivity · 1971–2150",
        color="white", fontsize=15, pad=18,
    )
    ax.set_xlabel("Year", color="white", fontsize=12)
    ax.set_ylabel("QC francophones / Canada total (%)", color="white", fontsize=12)
    ax.set_xlim(1971, 2150)
    ax.set_ylim(0, 22)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#444")
    ax.grid(True, color="#222", linewidth=0.5)

    leg = ax.legend(loc="upper right", facecolor="#1a1d23",
                    edgecolor="#444", labelcolor="white", fontsize=10)
    leg.get_frame().set_alpha(0.9)

    fig.text(0.02, 0.02,
             "ROC fr% held flat from 2026 onward. QC selection unchanged. "
             "Immigration volume = mid scenario.",
             color="#888", fontsize=8)

    plt.tight_layout()
    out2 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "plots", "roc_fr_sensitivity_qc_fr_of_canada.png")
    plt.savefig(out2, dpi=150, facecolor="#0e1117")
    print(f"Saved: {out2}")

    # ── Summary table ─────────────────────────────────────────────────────────
    check_years = [2025, 2050, 2075, 2100, 2150]
    header = f"  {'year':>4}  {'mid':>7}  " + "  ".join(
        f"{s:>8}" for s, _, _ in SCENARIOS
    )
    print(f"\nNational francophone share:")
    print(header)
    for y in check_years:
        mid_val = results["mid"][1][results["mid"][0] == y][0]
        row = f"  {y:>4}  {mid_val:>6.2f}%  "
        for scen, _, _ in SCENARIOS:
            val = results[scen][1][results[scen][0] == y][0]
            row += f"  {val:>7.2f}%"
        print(row)


if __name__ == "__main__":
    main()
