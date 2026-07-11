"""
Plot Quebec's share of Canada's population over time, across all three
scenarios. Shows historical census data 1971-2021 plus simulated
projections 2025-2150.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import numpy as np
from canada_sim import CanadaSimulator
from loaders import PROVINCES

LANGUAGES = ["fr", "en", "allo"]

# Empirical Quebec share of Canada (StatCan census)
EMPIRICAL = {
    1951: 28.9,
    1971: 27.9,
    1981: 26.4,
    1991: 25.3,
    2001: 24.1,
    2011: 23.6,
    2021: 23.0,
    2025: 21.7,  # Q1 2025 estimate
}

def qc_share(history):
    years, shares = [], []
    for r in history:
        total = r["total"]
        qc = r["QC_fr"] + r["QC_en"] + r["QC_allo"]
        years.append(r["year"])
        shares.append(100 * qc / total)
    return np.array(years), np.array(shares)


def main():
    # Run all three scenarios
    results = {}
    for scen in ["low", "mid", "high"]:
        print(f"Running {scen} scenario...")
        sim = CanadaSimulator(scenario_name=scen, scale=100, seed=42)
        sim.run(until_year=2150, verbose=False)
        results[scen] = qc_share(sim.history)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Color palette matching prior project aesthetic
    colors = {"low": "#d85a30", "mid": "#fac775", "high": "#5dcaa5"}

    # Plot scenarios — historical portion (1971-2021) overlaid in white
    mid_years, mid_shares = results["mid"]
    hist_mask = mid_years <= 2021
    ax.plot(mid_years[hist_mask], mid_shares[hist_mask],
            color="white", linewidth=3, label="Simulated history (1971–2021)")

    for scen in ["low", "mid", "high"]:
        years, shares = results[scen]
        future = years >= 2021
        ax.plot(years[future], shares[future],
                color=colors[scen], linewidth=2.5,
                label=f"{scen.capitalize()} scenario")

    # Empirical census markers
    emp_years = sorted(EMPIRICAL.keys())
    emp_vals = [EMPIRICAL[y] for y in emp_years]
    ax.scatter(emp_years, emp_vals, color="#5dcaa5", s=80, zorder=5,
               edgecolor="white", linewidth=1.5, label="Census (StatCan)")

    # Annotations
    ax.set_title("Quebec's share of Canada's population\n1971–2150 · agent-based simulation",
                 color="white", fontsize=16, pad=20)
    ax.set_xlabel("Year", color="white", fontsize=12)
    ax.set_ylabel("Quebec share (%)", color="white", fontsize=12)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#444")
    ax.grid(True, color="#222", linewidth=0.5)
    ax.set_xlim(1971, 2150)
    ax.set_ylim(0, 30)

    # Reference lines
    ax.axhline(25, color="#444", linestyle=":", linewidth=0.8)
    ax.axhline(20, color="#444", linestyle=":", linewidth=0.8)
    ax.axhline(15, color="#444", linestyle=":", linewidth=0.8)
    ax.axhline(10, color="#444", linestyle=":", linewidth=0.8)
    ax.axvline(2025, color="#666", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(2025.5, 28, "calibration | projection",
            color="#888", fontsize=9, alpha=0.8)

    # Legend
    leg = ax.legend(loc="upper right", facecolor="#1a1d23",
                    edgecolor="#444", labelcolor="white")
    leg.get_frame().set_alpha(0.9)

    # Source footer
    fig.text(0.02, 0.02,
             "Sources: StatCan Census 1951–2021; Q1 2025 estimate. "
             "Simulation: agent-based model with empirical 1971–2025 calibration.",
             color="#888", fontsize=8)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "qc_share_plot.png")
    plt.savefig(out, dpi=150, facecolor="#0e1117")
    print(f"Saved: {out}")

    # Print summary table
    print("\nQuebec share of Canada (selected years):")
    print(f"  {'year':>4}  {'low':>6}  {'mid':>6}  {'high':>6}")
    for y in [1971, 2001, 2021, 2025, 2050, 2075, 2100, 2150]:
        idx_low = np.where(results["low"][0] == y)[0][0]
        idx_mid = np.where(results["mid"][0] == y)[0][0]
        idx_high = np.where(results["high"][0] == y)[0][0]
        print(f"  {y:>4}  {results['low'][1][idx_low]:>5.2f}%  "
              f"{results['mid'][1][idx_mid]:>5.2f}%  "
              f"{results['high'][1][idx_high]:>5.2f}%")


if __name__ == "__main__":
    main()
