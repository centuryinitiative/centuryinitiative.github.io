"""
Indigenous population of Canada — extra plots + bar-chart-race MP4s.

This is an ADDITIVE, standalone overlay: it does not touch the main simulation
or any existing figure. It layers an Indigenous population track on top of the
coarse simulation's total-population history and tracks TWO definitions:

  identity      — First Nations + Metis + Inuit identity (~5% of Canada today)
  mothertongue  — people with an Indigenous mother tongue (~0.5%, declining)

Method
------
* Total (denominator) population by province/year comes from CanadaSimulator
  (mid scenario) — the same calibrated model the other plots use.
* Indigenous population by province is interpolated (log-linear) between census
  anchors in data/indigenous_population.csv, then projected past 2021 with the
  natural-increase assumptions in data/indigenous_natural_increase.csv.
* Immigrants are treated as non-Indigenous, so the Indigenous SHARE falls where
  immigration inflates the total — this emerges automatically from ind/total.

Outputs (prefix IND):
  plots/IND01_national_share.png        national identity vs mother-tongue share
  plots/IND02_provincial_share.png      identity share, key provinces + national
  plots/IND03_absolute_population.png   absolute identity vs mother-tongue pop
  plots/IND04_transmission_gap.png      mother tongue as % of identity (retention)
  plots/IND_bcr1_prov_ind_share.mp4     provincial Indigenous identity share race
  plots/IND_bcr2_prov_ind_pop.mp4       provincial Indigenous identity pop race

Run: python3 plot_indigenous.py     (requires numpy, matplotlib, ffmpeg)
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

from canada_sim import CanadaSimulator
from loaders import (
    PROVINCES, DATA_DIR, _read_csv, load_historical_provincial_population,
)

# ── Style (matches the rest of the project) ──────────────────────────────────
BG, TEXT, SUBTEXT = "#0e1117", "#e8eaed", "#9aa0a6"
C_IDENTITY = "#c77dff"   # violet  — identity
C_MOTHER   = "#4ecdc4"   # teal    — mother tongue
PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

PROV_COLORS = {
    "NL": "#4e8ef7", "PE": "#a55bf5", "NS": "#f5a623", "NB": "#50c878",
    "QC": "#003f88", "ON": "#d62828", "MB": "#f77f00", "SK": "#2ec4b6",
    "AB": "#e63946", "BC": "#457b9d", "YT": "#b5838d", "NT": "#6b4226",
    "NU": "#4a4e69",
}
PROV_NAMES = {
    "NL": "Nfld & Lab.", "PE": "PEI", "NS": "Nova Scotia", "NB": "New Brunswick",
    "QC": "Quebec", "ON": "Ontario", "MB": "Manitoba", "SK": "Saskatchewan",
    "AB": "Alberta", "BC": "British Columbia", "YT": "Yukon",
    "NT": "Northwest Terr.", "NU": "Nunavut",
}

# Nunavut was carved out of the Northwest Territories only in 1999; before that
# the base model (and the historical population series) carry the whole northern
# region under NT and leave NU at ~0. To get a meaningful, artifact-free share
# across 1971-2150 we merge the two territories for the *provincial* views.
MERGED_PROVS = [p for p in PROVINCES if p != "NU"]
MERGED_NAMES = dict(PROV_NAMES, NT="NT + Nunavut")


def merge_north(d):
    """Combine NT and NU into a single 'NT' entry (values are numpy arrays)."""
    out = {p: d[p] for p in MERGED_PROVS}
    out["NT"] = d["NT"] + d["NU"]
    return out

END_YEAR   = 2150     # static plots run to here
RACE_END   = 2100     # MP4s stop here (keeps them snappy, matches fg_ style)

SOURCE_NOTE = ("Sources: StatCan Census 1971-2021 (Indigenous identity & mother "
               "tongue), approximate provincial anchors — see data/indigenous_*.csv. "
               "Total population from the project's agent-based simulation (mid scenario).")


# =============================================================================
# Build the Indigenous population series
# =============================================================================

def _log_interp(years_a, vals_a, y):
    """Log-linear interpolation (populations don't go negative), flat outside."""
    if y <= years_a[0]:
        return vals_a[0]
    if y >= years_a[-1]:
        return vals_a[-1]
    i = int(np.searchsorted(years_a, y) - 1)
    i = max(0, min(i, len(years_a) - 2))
    t = (y - years_a[i]) / (years_a[i + 1] - years_a[i])
    lo, hi = max(vals_a[i], 1e-6), max(vals_a[i + 1], 1e-6)
    return float(np.exp((1 - t) * np.log(lo) + t * np.log(hi)))


def load_indigenous_anchors():
    """province -> dict(years=[...], identity=[...], mother=[...]) in persons."""
    rows = _read_csv(os.path.join(DATA_DIR, "indigenous_population.csv"))
    out = {p: {"years": [], "identity": [], "mother": []} for p in PROVINCES}
    for r in rows:
        p = r["province_code"]
        out[p]["years"].append(int(r["year"]))
        out[p]["identity"].append(float(r["identity_thousands"]) * 1000.0)
        out[p]["mother"].append(float(r["mothertongue_thousands"]) * 1000.0)
    for p in out:
        for k in ("years", "identity", "mother"):
            out[p][k] = np.array(out[p][k], dtype=float)
    return out


def load_projection_ni():
    """Returns (identity_ni_fn, mother_ni_fn) over year."""
    rows = _read_csv(os.path.join(DATA_DIR, "indigenous_natural_increase.csv"))
    yrs = np.array([int(r["year"]) for r in rows], dtype=float)
    ide = np.array([float(r["identity_ni"]) for r in rows], dtype=float)
    mot = np.array([float(r["mothertongue_ni"]) for r in rows], dtype=float)

    def mk(arr):
        return lambda y: float(np.interp(y, yrs, arr))
    return mk(ide), mk(mot)


def build_indigenous_series(years):
    """
    Returns dict:
      identity[p], mother[p]  -> np.array over `years` (persons)
    Anchors interpolate up to the last census year; beyond that, grow by the
    projected natural-increase rate.
    """
    anchors = load_indigenous_anchors()
    ni_id_fn, ni_mo_fn = load_projection_ni()
    last_anchor = max(anchors[p]["years"].max() for p in PROVINCES)

    identity = {p: np.zeros(len(years)) for p in PROVINCES}
    mother   = {p: np.zeros(len(years)) for p in PROVINCES}

    for p in PROVINCES:
        ya, ia, ma = anchors[p]["years"], anchors[p]["identity"], anchors[p]["mother"]
        for i, y in enumerate(years):
            if y <= last_anchor:
                identity[p][i] = _log_interp(ya, ia, y)
                mother[p][i]   = _log_interp(ya, ma, y)
            else:
                identity[p][i] = identity[p][i - 1] * (1.0 + ni_id_fn(y))
                mother[p][i]   = mother[p][i - 1] * (1.0 + ni_mo_fn(y))
    return identity, mother


# =============================================================================
# Run the base simulation for the denominator
# =============================================================================

def run_base_totals():
    """
    Returns years, prov_total (persons, per province), national.

    Denominator uses the same hybrid the bar-race plots use: REAL census /
    estimate population through 2025, then real-2025 + the simulation's delta
    afterward. This keeps the territories (esp. NT/NU) demographically sane —
    the raw model leaves Nunavut near zero because its 1971 seed is zero.
    """
    print("Running mid scenario for total-population denominator...")
    sim = CanadaSimulator(scenario_name="mid", scale=100, seed=42)
    sim.run(until_year=END_YEAR, verbose=False)
    years = np.array([r["year"] for r in sim.history], dtype=int)
    sim_prov = {
        p: np.array([r[f"{p}_fr"] + r[f"{p}_en"] + r[f"{p}_allo"]
                     for r in sim.history], dtype=float)
        for p in PROVINCES
    }

    hist = load_historical_provincial_population()
    prov_total = {}
    for p in PROVINCES:
        real_2025 = hist[p](2025)
        sim_2025 = sim_prov[p][years == 2025][0]
        vals = np.array([
            hist[p](y) if y <= 2025 else real_2025 + (sim_prov[p][i] - sim_2025)
            for i, y in enumerate(years)
        ], dtype=float)
        prov_total[p] = vals

    national = sum(prov_total.values())
    return years, prov_total, national


# =============================================================================
# Static plots
# =============================================================================

# Empirical Indigenous-identity share of Canada (StatCan census, %)
EMP_IDENTITY = {1971: 1.4, 1996: 2.8, 2006: 3.8, 2016: 4.9, 2021: 5.0}
EMP_MOTHER   = {1971: 0.9, 1996: 0.75, 2006: 0.64, 2016: 0.61, 2021: 0.51}


def _style_ax(ax, xlim=(1971, END_YEAR)):
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT)
    for sp in ax.spines.values():
        sp.set_color("#444")
    ax.grid(True, color="#222", linewidth=0.5)
    ax.set_xlim(*xlim)
    ax.axvline(2025, color="#666", linestyle="--", linewidth=0.8, alpha=0.6)


def plot_national_share(years, identity, mother, national):
    id_tot = sum(identity[p] for p in PROVINCES)
    mo_tot = sum(mother[p] for p in PROVINCES)
    id_share = 100 * id_tot / national
    mo_share = 100 * mo_tot / national

    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
    _style_ax(ax)
    ax.plot(years, id_share, color=C_IDENTITY, lw=2.5, label="Indigenous identity")
    ax.plot(years, mo_share, color=C_MOTHER, lw=2.5, label="Indigenous mother tongue")

    for emp, col in ((EMP_IDENTITY, C_IDENTITY), (EMP_MOTHER, C_MOTHER)):
        ys = sorted(emp)
        ax.scatter(ys, [emp[y] for y in ys], color=col, s=70, zorder=5,
                   edgecolor="white", linewidth=1.3)

    ax.set_title("Indigenous share of Canada's population\n"
                 "1971-2150 · identity vs. mother tongue",
                 color=TEXT, fontsize=16, pad=18)
    ax.set_xlabel("Year", color=TEXT, fontsize=12)
    ax.set_ylabel("Share of Canada (%)", color=TEXT, fontsize=12)
    ax.set_ylim(0, max(id_share.max(), 6) * 1.1)
    ax.text(2026, ax.get_ylim()[1] * 0.95, "calibration | projection",
            color="#888", fontsize=9)
    leg = ax.legend(loc="center right", facecolor="#1a1d23",
                    edgecolor="#444", labelcolor=TEXT)
    leg.get_frame().set_alpha(0.9)
    fig.text(0.02, 0.02, SOURCE_NOTE, color="#888", fontsize=7.5)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "IND01_national_share.png")


def plot_provincial_share(years, identity, prov_total, national):
    id_m = merge_north(identity)
    tot_m = merge_north(prov_total)
    key = ["NT", "YT", "MB", "SK", "NL"]   # highest-share regions
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
    _style_ax(ax)
    for p in key:
        share = 100 * id_m[p] / np.maximum(tot_m[p], 1)
        ax.plot(years, share, color=PROV_COLORS[p], lw=2.3, label=MERGED_NAMES[p])
    nat = 100 * sum(identity[p] for p in PROVINCES) / national
    ax.plot(years, nat, color=TEXT, lw=2.2, ls="--", label="Canada (all)")

    ax.set_title("Indigenous-identity share by province\n"
                 "highest-share provinces + national, 1971-2150",
                 color=TEXT, fontsize=16, pad=18)
    ax.set_xlabel("Year", color=TEXT, fontsize=12)
    ax.set_ylabel("Indigenous-identity share (%)", color=TEXT, fontsize=12)
    ax.set_ylim(0, 100)
    leg = ax.legend(loc="center right", facecolor="#1a1d23",
                    edgecolor="#444", labelcolor=TEXT)
    leg.get_frame().set_alpha(0.9)
    fig.text(0.02, 0.02, SOURCE_NOTE, color="#888", fontsize=7.5)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "IND02_provincial_share.png")


def plot_absolute(years, identity, mother):
    id_tot = sum(identity[p] for p in PROVINCES)
    mo_tot = sum(mother[p] for p in PROVINCES)
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
    _style_ax(ax)
    ax.plot(years, id_tot / 1e6, color=C_IDENTITY, lw=2.5, label="Indigenous identity")
    ax.plot(years, mo_tot / 1e6, color=C_MOTHER, lw=2.5, label="Indigenous mother tongue")
    ax.fill_between(years, mo_tot / 1e6, id_tot / 1e6, color=C_IDENTITY, alpha=0.10)

    ax.set_title("Indigenous population of Canada (absolute)\n"
                 "identity vs. mother tongue, 1971-2150",
                 color=TEXT, fontsize=16, pad=18)
    ax.set_xlabel("Year", color=TEXT, fontsize=12)
    ax.set_ylabel("Population (millions)", color=TEXT, fontsize=12)
    ax.set_ylim(0, id_tot.max() / 1e6 * 1.1)
    leg = ax.legend(loc="upper left", facecolor="#1a1d23",
                    edgecolor="#444", labelcolor=TEXT)
    leg.get_frame().set_alpha(0.9)
    fig.text(0.02, 0.02, SOURCE_NOTE, color="#888", fontsize=7.5)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "IND03_absolute_population.png")


def plot_transmission_gap(years, identity, mother):
    id_tot = sum(identity[p] for p in PROVINCES)
    mo_tot = sum(mother[p] for p in PROVINCES)
    retention = 100 * mo_tot / np.maximum(id_tot, 1)
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
    _style_ax(ax)
    ax.plot(years, retention, color=C_MOTHER, lw=2.6)
    ax.fill_between(years, 0, retention, color=C_MOTHER, alpha=0.12)

    ax.set_title("Indigenous-language retention\n"
                 "mother-tongue speakers as a share of the identity population",
                 color=TEXT, fontsize=16, pad=18)
    ax.set_xlabel("Year", color=TEXT, fontsize=12)
    ax.set_ylabel("Mother tongue ÷ identity (%)", color=TEXT, fontsize=12)
    ax.set_ylim(0, max(retention.max(), 10) * 1.15)
    fig.text(0.02, 0.02, SOURCE_NOTE, color="#888", fontsize=7.5)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, "IND04_transmission_gap.png")


def _save(fig, name):
    out = os.path.join(PLOT_DIR, name)
    fig.savefig(out, dpi=300, facecolor=BG)
    plt.close(fig)
    print(f"  Saved {out}")


# =============================================================================
# Bar chart race (self-contained; mirrors fg_bar_race.build_bar_race)
# =============================================================================

def _smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def _ranks(series, n):
    labels = list(series)
    return [
        {l: i for i, l in enumerate(sorted(labels, key=lambda l: series[l][yi]))}
        for yi in range(n)
    ]


def build_bar_race(years, series, colors, title, xlabel, out_path,
                   value_fmt, label_map, fps=20, n_interp=8):
    labels = list(series)
    n_labels = len(labels)
    n_years = len(years)
    ranks = _ranks(series, n_years)
    total_frames = (n_years - 1) * n_interp + 1

    fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)

    def draw(frame):
        ax.cla()
        ax.set_facecolor(BG)
        for sp in ax.spines.values():
            sp.set_visible(False)
        yi = min(frame // n_interp, n_years - 1)
        raw = (frame % n_interp) / n_interp if yi < n_years - 1 else 0.0
        nxt = min(yi + 1, n_years - 1)
        fp = _smoothstep(raw)
        vals = {l: series[l][yi] + raw * (series[l][nxt] - series[l][yi]) for l in labels}
        ypos = {l: ranks[yi][l] + fp * (ranks[nxt][l] - ranks[yi][l]) for l in labels}
        cur_year = years[yi] + raw * (years[nxt] - years[yi])
        mx = max(vals.values()) if vals else 1.0

        for l in labels:
            ax.barh([ypos[l]], [vals[l]], height=0.72,
                    color=colors.get(l, "#888"), edgecolor="none", alpha=0.92)
            ax.text(-mx * 0.012, ypos[l], label_map[l], ha="right", va="center",
                    fontsize=11, fontweight="bold", color=TEXT, clip_on=False)
            ax.text(vals[l] + mx * 0.012, ypos[l], value_fmt(vals[l]),
                    ha="left", va="center", fontsize=10, color=SUBTEXT)

        ax.set_xlim(0, mx * 1.28)
        ax.set_ylim(-0.7, n_labels - 0.3)
        ax.set_yticks([])
        ax.tick_params(axis="x", colors=SUBTEXT, labelsize=9)
        ax.set_xlabel(xlabel, color=SUBTEXT, fontsize=11)
        ax.grid(axis="x", color="#2a2a2a", linewidth=0.6)
        ax.set_title(title, color=TEXT, fontsize=14, pad=10, fontweight="bold")
        ax.text(0.98, 0.05, f"{int(cur_year)}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=48, fontweight="bold",
                color=TEXT, alpha=0.18)

    print(f"  Rendering {total_frames} frames -> {out_path}")
    t0 = time.time()
    anim = FuncAnimation(fig, draw, frames=total_frames, interval=1000 / fps)
    writer = FFMpegWriter(fps=fps, codec="libx264",
                          extra_args=["-pix_fmt", "yuv420p", "-crf", "20"])
    anim.save(out_path, writer=writer, dpi=120, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print(f"  Saved in {time.time() - t0:.1f}s")


# =============================================================================
# Main
# =============================================================================

def main():
    years, prov_total, national = run_base_totals()
    identity, mother = build_indigenous_series(years)

    print("Static plots...")
    plot_national_share(years, identity, mother, national)
    plot_provincial_share(years, identity, prov_total, national)
    plot_absolute(years, identity, mother)
    plot_transmission_gap(years, identity, mother)

    # Bar chart races (merge NT+NU, truncate to RACE_END)
    id_m = merge_north(identity)
    tot_m = merge_north(prov_total)
    mask = years <= RACE_END
    ry = years[mask]
    id_share = {p: 100 * id_m[p][mask] / np.maximum(tot_m[p][mask], 1)
                for p in MERGED_PROVS}
    id_pop = {p: id_m[p][mask] for p in MERGED_PROVS}

    print("Bar chart races...")
    build_bar_race(
        ry, id_share, PROV_COLORS,
        title="Provincial Indigenous-identity Share (%) — 1971-2100",
        xlabel="Indigenous identity, share of provincial population (%)",
        out_path=os.path.join(PLOT_DIR, "IND_bcr1_prov_ind_share.mp4"),
        value_fmt=lambda v: f"{v:.1f}%", label_map=MERGED_NAMES,
    )
    build_bar_race(
        ry, id_pop, PROV_COLORS,
        title="Provincial Indigenous-identity Population — 1971-2100",
        xlabel="Indigenous identity population (individuals)",
        out_path=os.path.join(PLOT_DIR, "IND_bcr2_prov_ind_pop.mp4"),
        value_fmt=lambda v: f"{int(round(v)):,}", label_map=MERGED_NAMES,
    )

    # Console summary
    print("\nIndigenous-identity share of Canada (selected years):")
    id_tot = sum(identity[p] for p in PROVINCES)
    mo_tot = sum(mother[p] for p in PROVINCES)
    for y in [1971, 2001, 2021, 2050, 2100, 2150]:
        i = int(np.where(years == y)[0][0])
        print(f"  {y}:  identity {100*id_tot[i]/national[i]:5.2f}%   "
              f"mother tongue {100*mo_tot[i]/national[i]:4.2f}%")


if __name__ == "__main__":
    main()
