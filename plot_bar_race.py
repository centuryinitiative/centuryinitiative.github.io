"""
Four bar chart race animations from the Canada Pop simulation (mid scenario).

  BCR1 — Provincial francophone population (# individuals)
  BCR2 — Provincial total population (# individuals)
  BCR3 — National language group populations (# individuals)
  BCR4 — Provincial francophone share (%)

Improvements over v1:
  - Smooth position interpolation: ranks are pre-computed at each year
    boundary; bar y-positions interpolate between consecutive ranks using a
    smoothstep easing function, so bars glide past each other rather than
    jumping.
  - ~2-minute runtime at 20 fps (n_interp=13 sub-frames per year).
  - Population values shown as formatted individual counts (e.g. 7,523,400).

Output: plots/bcr{1..4}_*.mp4
Requires: ffmpeg on PATH.
"""
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

from loaders import PROVINCES, LANGUAGES, load_historical_provincial_population
from canada_sim import CanadaSimulator, SCALE, END_YEAR

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0e1117"
TEXT    = "#e8eaed"
SUBTEXT = "#9aa0a6"

PROV_COLORS = {
    "NL": "#4e8ef7", "PE": "#a55bf5", "NS": "#f5a623", "NB": "#50c878",
    "QC": "#003f88", "ON": "#d62828", "MB": "#f77f00", "SK": "#2ec4b6",
    "AB": "#e63946", "BC": "#457b9d", "YT": "#b5838d", "NT": "#6b4226",
    "NU": "#4a4e69",
}
LANG_COLORS  = {"fr": "#3a7ebf", "en": "#e07b39", "allo": "#3abf6e"}
LANG_LABELS  = {"fr": "Francophone", "en": "Anglophone", "allo": "Allophone"}

# ── Simulation ────────────────────────────────────────────────────────────────
print("Running mid scenario simulation...")
t0 = time.time()
sim = CanadaSimulator(scenario_name="mid", scale=SCALE, seed=42)
sim.run(until_year=END_YEAR, verbose=False)
history = sim.history
print(f"  Done in {time.time()-t0:.1f}s  ({len(history)} years)")

years = np.array([r["year"] for r in history])

# Raw individual counts (not millions)
prov_fr = {
    p: np.array([r[f"{p}_fr"] for r in history], dtype=float)
    for p in PROVINCES
}
# ── BCR2: hybrid provincial total population ──────────────────────────────────
# Pre-2025  → interpolated StatCan census / quarterly estimates (real data).
# Post-2025 → simulation delta grafted onto the correct 2025 baseline, so the
#             growth dynamics come from the model but absolute levels are anchored
#             to the real 2025 provincial populations.
_hist_prov_pop = load_historical_provincial_population()

# Simulation values at 2025 (used as the delta baseline)
_sim_2025_idx = int(np.where(years == 2025)[0][0])
_sim_2025 = {p: sum(history[_sim_2025_idx][f"{p}_{l}"] for l in LANGUAGES)
             for p in PROVINCES}
_real_2025 = {p: _hist_prov_pop[p](2025) for p in PROVINCES}

prov_total = {}
for p in PROVINCES:
    vals = np.empty(len(years), dtype=float)
    for i, y in enumerate(years):
        if y <= 2025:
            vals[i] = _hist_prov_pop[p](y)
        else:
            sim_val = sum(history[i][f"{p}_{l}"] for l in LANGUAGES)
            vals[i] = _real_2025[p] + (sim_val - _sim_2025[p])
    prov_total[p] = vals
lang_total = {
    l: np.array([sum(r[f"{p}_{l}"] for p in PROVINCES) for r in history], dtype=float)
    for l in LANGUAGES
}
prov_fr_share = {
    p: np.array([
        100.0 * r[f"{p}_fr"] / max(1, sum(r[f"{p}_{l}"] for l in LANGUAGES))
        for r in history
    ])
    for p in PROVINCES
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def smoothstep(x: float) -> float:
    """Cubic smoothstep — zero first-derivative at 0 and 1."""
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def compute_ranks(series: dict, n_years: int) -> list[dict]:
    """
    Return a list of length n_years; each element is a dict {label: rank}
    where rank 0 = smallest value (bottom of chart).
    """
    labels = list(series.keys())
    result = []
    for yi in range(n_years):
        vals = {l: series[l][yi] for l in labels}
        ordered = sorted(labels, key=lambda l: vals[l])
        result.append({l: i for i, l in enumerate(ordered)})
    return result


def fmt_pop(n: float) -> str:
    """Format a raw individual count with comma separators."""
    return f"{int(round(n)):,}"


def fmt_pct(n: float) -> str:
    return f"{n:.1f}%"


# ── Core animation builder ────────────────────────────────────────────────────

def build_bar_race(
    series: dict,
    colors: dict,
    title: str,
    xlabel: str,
    out_path: str,
    value_fmt_fn=fmt_pop,
    label_map: dict = None,
    fps: int = 20,
    n_interp: int = 13,
    figsize=(14, 8),
):
    labels    = list(series.keys())
    n_labels  = len(labels)
    n_years   = len(years)
    if label_map is None:
        label_map = {l: l for l in labels}

    ranks_by_year = compute_ranks(series, n_years)
    total_frames  = (n_years - 1) * n_interp + 1

    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    ax.set_facecolor(BG)
    for sp in ax.spines.values():
        sp.set_visible(False)

    def draw_frame(frame: int):
        ax.cla()
        ax.set_facecolor(BG)
        for sp in ax.spines.values():
            sp.set_visible(False)

        yr_idx = min(frame // n_interp, n_years - 1)
        raw_frac = (frame % n_interp) / n_interp if yr_idx < n_years - 1 else 0.0
        next_idx = min(yr_idx + 1, n_years - 1)

        # Eased fraction for position; raw fraction for values (more natural)
        frac_pos = smoothstep(raw_frac)
        frac_val = raw_frac

        # Interpolated values
        vals = {
            l: series[l][yr_idx] + frac_val * (series[l][next_idx] - series[l][yr_idx])
            for l in labels
        }

        # Smoothly interpolated y-positions (float ranks)
        ypos = {
            l: ranks_by_year[yr_idx][l]
               + frac_pos * (ranks_by_year[next_idx][l] - ranks_by_year[yr_idx][l])
            for l in labels
        }

        current_year = years[yr_idx] + raw_frac * (years[next_idx] - years[yr_idx])
        max_val = max(vals.values()) if vals else 1.0

        # Draw each bar individually at its float y-position
        bar_h = 0.72
        for l in labels:
            y = ypos[l]
            v = vals[l]
            col = colors.get(l, "#888888")
            ax.barh([y], [v], height=bar_h, color=col, edgecolor="none",
                    alpha=0.92)

            # Label left of bar
            ax.text(
                -max_val * 0.012, y,
                label_map[l],
                ha="right", va="center",
                fontsize=10, fontweight="bold", color=TEXT,
                clip_on=False,
            )
            # Value right of bar
            ax.text(
                v + max_val * 0.012, y,
                value_fmt_fn(v),
                ha="left", va="center",
                fontsize=9, color=SUBTEXT,
            )

        ax.set_xlim(0, max_val * 1.28)
        ax.set_ylim(-0.7, n_labels - 0.3)
        ax.set_yticks([])
        ax.tick_params(axis="x", colors=SUBTEXT, labelsize=8)
        ax.set_xlabel(xlabel, color=SUBTEXT, fontsize=10)
        ax.grid(axis="x", color="#2a2a2a", linewidth=0.6)
        ax.set_title(title, color=TEXT, fontsize=13, pad=10, fontweight="bold")

        # Big year watermark
        ax.text(
            0.98, 0.05, f"{int(current_year)}",
            transform=ax.transAxes,
            ha="right", va="bottom",
            fontsize=48, fontweight="bold",
            color=TEXT, alpha=0.18,
        )

    print(f"  Rendering {total_frames} frames → {out_path}")
    t0 = time.time()
    anim = FuncAnimation(fig, draw_frame, frames=total_frames, interval=1000 / fps)
    writer = FFMpegWriter(
        fps=fps,
        codec="libx264",
        extra_args=["-pix_fmt", "yuv420p", "-crf", "20"],
    )
    anim.save(out_path, writer=writer, dpi=120, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    dt = time.time() - t0
    print(f"  Saved in {dt:.1f}s  ({total_frames/dt:.0f} fps render speed)")


# ═════════════════════════════════════════════════════════════════════════════
print("\nBCR1 — Provincial francophone population")
build_bar_race(
    series=prov_fr,
    colors=PROV_COLORS,
    title="Provincial Francophone Population — Mid Scenario (1971–2150)",
    xlabel="Number of francophones",
    out_path="plots/bcr1_prov_fr_pop.mp4",
    value_fmt_fn=fmt_pop,
)

print("\nBCR2 — Provincial total population")
build_bar_race(
    series=prov_total,
    colors=PROV_COLORS,
    title="Provincial Total Population — Mid Scenario (1971–2150)",
    xlabel="Total population (individuals)",
    out_path="plots/bcr2_prov_total_pop.mp4",
    value_fmt_fn=fmt_pop,
)

print("\nBCR3 — National language group populations")
build_bar_race(
    series=lang_total,
    colors=LANG_COLORS,
    label_map=LANG_LABELS,
    title="National Language Group Populations — Mid Scenario (1971–2150)",
    xlabel="Number of individuals",
    out_path="plots/bcr3_lang_group_pop.mp4",
    value_fmt_fn=fmt_pop,
)

print("\nBCR4 — Provincial francophone share")
build_bar_race(
    series=prov_fr_share,
    colors=PROV_COLORS,
    title="Provincial Francophone Share — Mid Scenario (1971–2150)",
    xlabel="Francophone share (%)",
    out_path="plots/bcr4_prov_fr_share.mp4",
    value_fmt_fn=fmt_pct,
)

print("\nAll done.")
