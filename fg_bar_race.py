"""
Bar chart race animations from the fine-grain simulation (mid scenario).

  fg_BCR1  — Provincial francophone population (# individuals)
  fg_BCR2  — Provincial total population (# individuals)
  fg_BCR3  — National language group populations (# individuals)
  fg_BCR3b — Language composition pies: Quebec vs Rest of Canada
  fg_BCR4  — Provincial francophone share (%)
  fg_BCR5  — Animated age pyramid
  fg_BCR6  — Provincial annual births

Loads pre-computed history from plots/fg_mid_history.pkl (written by fg_sim.py).
Requires: ffmpeg on PATH.
"""
import os
import pickle
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Patch

from loaders import PROVINCES, LANGUAGES, load_historical_provincial_population

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
LANG_COLORS = {"fr": "#3a7ebf", "en": "#e07b39", "allo": "#3abf6e"}
LANG_LABELS = {"fr": "Francophone", "en": "Anglophone", "allo": "Allophone"}
C_M, C_F    = "#4e8ef7", "#f5a623"

# ── Load cached history (written by fg_sim.py) ────────────────────────────────
_cache = os.path.join("plots", "fg_mid_history.pkl")
if not os.path.exists(_cache):
    raise FileNotFoundError(
        f"Cache not found: {_cache}\nRun fg_sim.py (or 'make fg_sim') first."
    )
print(f"Loading history from {_cache}...")
with open(_cache, "rb") as _f:
    history = pickle.load(_f)
print(f"  {len(history)} years loaded.")

years = np.array([r["year"] for r in history])

# ── Optional single-clip selector ─────────────────────────────────────────────
# Render just one animation by setting FG_ONLY, e.g.:  FG_ONLY=3b python3 fg_bar_race.py
# Keys: 1, 2, 3, 3b, 4, 5, 6. Unset (default) renders everything.
_ONLY = os.environ.get("FG_ONLY")
def _do(key):
    return _ONLY is None or _ONLY == key

# ── Build series ──────────────────────────────────────────────────────────────

prov_fr = {
    p: np.array([r.get(f"{p}_fr", 0) for r in history], dtype=float)
    for p in PROVINCES
}

# BCR2: hybrid — real data pre-2025, simulation delta post-2025
_hist_prov_pop = load_historical_provincial_population()
_sim_2025_idx = int(np.where(years == 2025)[0][0])
_sim_2025 = {
    p: sum(history[_sim_2025_idx].get(f"{p}_{l}", 0) for l in LANGUAGES)
    for p in PROVINCES
}
_real_2025 = {p: _hist_prov_pop[p](2025) for p in PROVINCES}

prov_total = {}
for p in PROVINCES:
    vals = np.empty(len(years), dtype=float)
    for i, y in enumerate(years):
        if y <= 2025:
            vals[i] = _hist_prov_pop[p](y)
        else:
            sim_val = sum(history[i].get(f"{p}_{l}", 0) for l in LANGUAGES)
            vals[i] = _real_2025[p] + (sim_val - _sim_2025[p])
    prov_total[p] = vals

lang_total = {
    l: np.array([
        sum(r.get(f"{p}_{l}", 0) for p in PROVINCES)
        for r in history
    ], dtype=float)
    for l in LANGUAGES
}

prov_fr_share = {
    p: np.array([
        100.0 * r.get(f"{p}_fr", 0) / max(1, sum(r.get(f"{p}_{l}", 0) for l in LANGUAGES))
        for r in history
    ])
    for p in PROVINCES
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def compute_ranks(series: dict, n_years: int) -> list[dict]:
    labels = list(series.keys())
    result = []
    for yi in range(n_years):
        vals = {l: series[l][yi] for l in labels}
        ordered = sorted(labels, key=lambda l: vals[l])
        result.append({l: i for i, l in enumerate(ordered)})
    return result


def fmt_pop(n: float) -> str:
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
    label_fontsize: int = 10,
    value_fontsize: int = 9,
    title_fontsize: int = 13,
    tick_fontsize: int = 8,
    xlabel_fontsize: int = 10,
    left_margin: float = 0.13,
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
    fig.subplots_adjust(left=left_margin, right=0.97)
    for sp in ax.spines.values():
        sp.set_visible(False)

    def draw_frame(frame: int):
        ax.cla()
        ax.set_facecolor(BG)
        for sp in ax.spines.values():
            sp.set_visible(False)

        yr_idx   = min(frame // n_interp, n_years - 1)
        raw_frac = (frame % n_interp) / n_interp if yr_idx < n_years - 1 else 0.0
        next_idx = min(yr_idx + 1, n_years - 1)

        frac_pos = smoothstep(raw_frac)
        frac_val = raw_frac

        vals = {
            l: series[l][yr_idx] + frac_val * (series[l][next_idx] - series[l][yr_idx])
            for l in labels
        }
        ypos = {
            l: ranks_by_year[yr_idx][l]
               + frac_pos * (ranks_by_year[next_idx][l] - ranks_by_year[yr_idx][l])
            for l in labels
        }

        current_year = years[yr_idx] + raw_frac * (years[next_idx] - years[yr_idx])
        max_val = max(vals.values()) if vals else 1.0

        bar_h = 0.72
        for l in labels:
            y = ypos[l]
            v = vals[l]
            col = colors.get(l, "#888888")
            ax.barh([y], [v], height=bar_h, color=col, edgecolor="none", alpha=0.92)

            ax.text(
                -max_val * 0.012, y,
                label_map[l],
                ha="right", va="center",
                fontsize=label_fontsize, fontweight="bold", color=TEXT,
                clip_on=False,
            )
            ax.text(
                v + max_val * 0.012, y,
                value_fmt_fn(v),
                ha="left", va="center",
                fontsize=value_fontsize, color=SUBTEXT,
            )

        ax.set_xlim(0, max_val * 1.28)
        ax.set_ylim(-0.7, n_labels - 0.3)
        ax.set_yticks([])
        ax.tick_params(axis="x", colors=SUBTEXT, labelsize=tick_fontsize)
        ax.set_xlabel(xlabel, color=SUBTEXT, fontsize=xlabel_fontsize)
        ax.grid(axis="x", color="#2a2a2a", linewidth=0.6)
        ax.set_title(title, color=TEXT, fontsize=title_fontsize, pad=10, fontweight="bold")

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
print("\nfg_BCR1 — Provincial francophone population")
_do("1") and build_bar_race(
    series=prov_fr,
    colors=PROV_COLORS,
    title="Provincial Francophone Population — Mid Scenario (1971–2100)",
    xlabel="Number of francophones",
    out_path="plots/fg_bcr1_prov_fr_pop.mp4",
    value_fmt_fn=fmt_pop,
    label_fontsize=15,
    value_fontsize=12,
)

print("\nfg_BCR2 — Provincial total population")
_do("2") and build_bar_race(
    series=prov_total,
    colors=PROV_COLORS,
    title="Provincial Total Population — Mid Scenario (1971–2100)",
    xlabel="Total population (individuals)",
    out_path="plots/fg_bcr2_prov_total_pop.mp4",
    value_fmt_fn=fmt_pop,
)

print("\nfg_BCR3 — National language group populations")
_do("3") and build_bar_race(
    series=lang_total,
    colors=LANG_COLORS,
    label_map=LANG_LABELS,
    title="National Language Group Populations — Mid Scenario (1971–2100)",
    xlabel="Number of individuals",
    out_path="plots/fg_bcr3_lang_group_pop.mp4",
    value_fmt_fn=fmt_pop,
    label_fontsize=16,
    value_fontsize=15,
    title_fontsize=16,
    tick_fontsize=12,
    xlabel_fontsize=13,
    left_margin=0.19,
)

# ── fg_BCR3b: Side-by-side pie chart animation (QC vs ROC) ───────────────────

def build_pie_animation(
    history: list,
    years: np.ndarray,
    out_path: str,
    fps: int = 20,
    n_interp: int = 13,
    figsize=(14, 7),
):
    """
    Two animated pies side by side: Quebec (left) and Rest of Canada (right).
    Each pie shows fr / en / allo shares evolving over time.
    Wedge sizes interpolate smoothly between year snapshots.
    """
    PROV_QC_CODE = "QC"
    ROC_PROVS    = [p for p in PROVINCES if p != PROV_QC_CODE]

    n_years      = len(years)
    total_frames = (n_years - 1) * n_interp + 1

    # Pre-compute shares per year for QC and ROC
    def shares(provs, lang):
        return np.array([
            sum(r.get(f"{p}_{lang}", 0) for p in provs)
            for r in history
        ], dtype=float)

    qc_fr  = shares([PROV_QC_CODE], "fr")
    qc_en  = shares([PROV_QC_CODE], "en")
    qc_al  = shares([PROV_QC_CODE], "allo")
    qc_tot = qc_fr + qc_en + qc_al

    roc_fr  = shares(ROC_PROVS, "fr")
    roc_en  = shares(ROC_PROVS, "en")
    roc_al  = shares(ROC_PROVS, "allo")
    roc_tot = roc_fr + roc_en + roc_al

    fig, (ax_qc, ax_roc) = plt.subplots(1, 2, figsize=figsize, facecolor=BG)
    fig.subplots_adjust(wspace=0.05, top=0.80, bottom=0.12)

    pie_colors = [LANG_COLORS["fr"], LANG_COLORS["en"], LANG_COLORS["allo"]]

    # Static elements drawn once outside the frame loop
    legend_handles = [
        Patch(color=LANG_COLORS["fr"],   label="Francophone"),
        Patch(color=LANG_COLORS["en"],   label="Anglophone"),
        Patch(color=LANG_COLORS["allo"], label="Allophone"),
    ]
    _legend = fig.legend(
        handles=legend_handles,
        loc="lower center", ncol=3,
        framealpha=0, labelcolor=TEXT, fontsize=15,
        bbox_to_anchor=(0.5, 0.01),
    )
    _suptitle = fig.suptitle(
        "Language Composition — Mid Scenario (1971–2100)",
        color=TEXT, fontsize=15, fontweight="bold", y=0.985,
    )
    _year_text = fig.text(
        0.98, 0.04, "",
        ha="right", va="bottom",
        fontsize=52, fontweight="bold",
        color=TEXT, alpha=0.15,
        transform=fig.transFigure,
    )

    def interp(arr, yi, t):
        ni = min(yi + 1, n_years - 1)
        return arr[yi] + t * (arr[ni] - arr[yi])

    def draw_pie(ax, pct, total_pop, region_label):
        _, _, autotexts = ax.pie(
            pct,
            colors=pie_colors,
            startangle=90,
            counterclock=False,
            autopct=lambda p: f"{p:.1f}%" if p > 2 else "",
            pctdistance=0.72,
            wedgeprops=dict(linewidth=1.2, edgecolor=BG),
        )
        for at in autotexts:
            at.set_color(TEXT)
            at.set_fontsize(13)
            at.set_fontweight("bold")
        ax.set_facecolor(BG)
        ax.set_title(
            f"{region_label}\n{fmt_pop(total_pop)} people",
            color=TEXT, fontsize=14, fontweight="bold", pad=12,
        )

    def draw_frame(frame: int):
        ax_qc.cla()
        ax_roc.cla()

        yr_idx   = min(frame // n_interp, n_years - 1)
        raw_frac = (frame % n_interp) / n_interp if yr_idx < n_years - 1 else 0.0
        t        = smoothstep(raw_frac)

        current_year = years[yr_idx] + raw_frac * (
            years[min(yr_idx + 1, n_years - 1)] - years[yr_idx]
        )
        _year_text.set_text(f"{int(current_year)}")

        qc_vals = np.array([
            interp(qc_fr, yr_idx, t),
            interp(qc_en, yr_idx, t),
            interp(qc_al, yr_idx, t),
        ])
        roc_vals = np.array([
            interp(roc_fr, yr_idx, t),
            interp(roc_en, yr_idx, t),
            interp(roc_al, yr_idx, t),
        ])

        draw_pie(ax_qc,  qc_vals  / max(qc_vals.sum(),  1), qc_vals.sum(),  "Quebec")
        draw_pie(ax_roc, roc_vals / max(roc_vals.sum(), 1), roc_vals.sum(), "Rest of Canada")

    print(f"  Rendering {total_frames} frames → {out_path}")
    t0 = time.time()
    anim = FuncAnimation(fig, draw_frame, frames=total_frames, interval=1000 / fps)
    writer = FFMpegWriter(
        fps=fps, codec="libx264",
        extra_args=["-pix_fmt", "yuv420p", "-crf", "20"],
    )
    anim.save(out_path, writer=writer, dpi=120, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    dt = time.time() - t0
    print(f"  Saved in {dt:.1f}s  ({total_frames/dt:.0f} fps render speed)")


print("\nfg_BCR3b — Language composition pies (QC vs ROC)")
_do("3b") and build_pie_animation(
    history=history,
    years=years,
    out_path="plots/fg_bcr3b_lang_pie.mp4",
)

print("\nfg_BCR4 — Provincial francophone share")
_do("4") and build_bar_race(
    series=prov_fr_share,
    colors=PROV_COLORS,
    title="Provincial Francophone Share — Mid Scenario (1971–2100)",
    xlabel="Francophone share (%)",
    out_path="plots/fg_bcr4_prov_fr_share.mp4",
    value_fmt_fn=fmt_pct,
)

# ── fg_BCR5: Animated age pyramid ─────────────────────────────────────────────

def build_age_pyramid(
    history: list,
    years: np.ndarray,
    out_path: str,
    fps: int = 20,
    n_interp: int = 13,
    figsize=(12, 8),
):
    """
    Animated population pyramid: male bars extend left, female bars right.
    Age groups (5-yr bands) on y-axis; bars sized by population (millions).
    Bars interpolate smoothly between year snapshots.
    """
    age_labels = [
        "0–4", "5–9", "10–14", "15–19", "20–24", "25–29",
        "30–34", "35–39", "40–44", "45–49", "50–54", "55–59",
        "60–64", "65–69", "70–74", "75–79", "80–84", "85–89", "90+",
    ]
    n_bands  = len(age_labels)
    n_years  = len(years)

    # Extract arrays: shape (n_years, n_bands)
    hist_M = np.array([r["age_hist_M"] for r in history], dtype=float) / 1e6
    hist_F = np.array([r["age_hist_F"] for r in history], dtype=float) / 1e6

    total_frames = (n_years - 1) * n_interp + 1

    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    ax.set_facecolor(BG)
    for sp in ax.spines.values():
        sp.set_visible(False)

    y_positions = np.arange(n_bands)

    # Fixed x-axis extent across the whole animation. Recomputing this per
    # frame from the current year's data makes the axis rescale every frame,
    # which reads as a once-per-year pulsation. Use the global maximum so the
    # scale stays constant and the bars genuinely grow/shrink against it.
    max_val = max(hist_M.max(), hist_F.max()) * 1.15

    def draw_frame(frame: int):
        ax.cla()
        ax.set_facecolor(BG)
        for sp in ax.spines.values():
            sp.set_visible(False)

        yr_idx   = min(frame // n_interp, n_years - 1)
        raw_frac = (frame % n_interp) / n_interp if yr_idx < n_years - 1 else 0.0
        next_idx = min(yr_idx + 1, n_years - 1)
        # Linear (constant-velocity) interpolation. smoothstep eases to zero
        # velocity at each year boundary, which on a steadily growing pyramid
        # reads as a once-per-year throb/pulse. The pyramid is a continuous
        # quantity, so it should flow at a constant rate between snapshots.
        t        = raw_frac

        m_vals = hist_M[yr_idx] + t * (hist_M[next_idx] - hist_M[yr_idx])
        f_vals = hist_F[yr_idx] + t * (hist_F[next_idx] - hist_F[yr_idx])

        current_year = years[yr_idx] + raw_frac * (years[next_idx] - years[yr_idx])

        # Male bars (left, negative x)
        ax.barh(y_positions, -m_vals, height=0.75,
                color=C_M, alpha=0.85, edgecolor="none", label="Male")
        # Female bars (right, positive x)
        ax.barh(y_positions, f_vals, height=0.75,
                color=C_F, alpha=0.85, edgecolor="none", label="Female")

        # Age group labels on centre spine
        for i, lbl in enumerate(age_labels):
            ax.text(0, i, lbl, ha="center", va="center",
                    fontsize=7.5, color=TEXT, fontweight="bold",
                    bbox=dict(facecolor=BG, edgecolor="none", pad=1.5))

        # Value labels outside bars
        for i in range(n_bands):
            if m_vals[i] > max_val * 0.02:
                ax.text(-m_vals[i] - max_val * 0.01, i,
                        f"{m_vals[i]:.2f}M", ha="right", va="center",
                        fontsize=6.5, color=SUBTEXT)
            if f_vals[i] > max_val * 0.02:
                ax.text(f_vals[i] + max_val * 0.01, i,
                        f"{f_vals[i]:.2f}M", ha="left", va="center",
                        fontsize=6.5, color=SUBTEXT)

        ax.set_xlim(-max_val, max_val)
        ax.set_ylim(-0.6, n_bands - 0.4)
        ax.set_yticks([])
        ax.axvline(0, color=SUBTEXT, linewidth=0.7)

        # x-axis ticks (absolute values)
        xt = np.linspace(0, max_val, 5)[1:]
        ax.set_xticks(list(-xt[::-1]) + list(xt))
        ax.set_xticklabels(
            [f"{v:.1f}M" for v in xt[::-1]] + [f"{v:.1f}M" for v in xt],
            color=SUBTEXT, fontsize=7,
        )
        ax.tick_params(axis="x", colors=SUBTEXT)

        ax.set_title(
            "Population Age Pyramid — Mid Scenario (1971–2100)",
            color=TEXT, fontsize=13, pad=10, fontweight="bold",
        )

        # Column headers
        ax.text(-max_val * 0.98, n_bands - 0.1, "◀  Male",
                color=C_M, fontsize=10, fontweight="bold", va="bottom")
        ax.text( max_val * 0.98, n_bands - 0.1, "Female  ▶",
                color=C_F, fontsize=10, fontweight="bold", va="bottom", ha="right")

        # Year watermark
        ax.text(0.98, 0.04, f"{int(current_year)}",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=48, fontweight="bold", color=TEXT, alpha=0.18)

    print(f"  Rendering {total_frames} frames → {out_path}")
    t0 = time.time()
    anim = FuncAnimation(fig, draw_frame, frames=total_frames, interval=1000 / fps)
    writer = FFMpegWriter(
        fps=fps, codec="libx264",
        extra_args=["-pix_fmt", "yuv420p", "-crf", "20"],
    )
    anim.save(out_path, writer=writer, dpi=120, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    dt = time.time() - t0
    print(f"  Saved in {dt:.1f}s  ({total_frames/dt:.0f} fps render speed)")


print("\nfg_BCR5 — Animated age pyramid")
_do("5") and build_age_pyramid(
    history=history,
    years=years,
    out_path="plots/fg_bcr5_age_pyramid.mp4",
)


# ── fg_BCR6: Provincial annual births bar chart race ───────────────────────────

# 5-year rolling mean to smooth out Poisson noise
def _smooth(arr: np.ndarray, window: int = 5) -> np.ndarray:
    kernel = np.ones(window) / window
    return np.convolve(arr, kernel, mode="same")


prov_births = {
    p: _smooth(np.array([r.get(f"{p}_births", 0) for r in history], dtype=float))
    for p in PROVINCES
}

print("\nfg_BCR6 — Provincial annual births")
_do("6") and build_bar_race(
    series=prov_births,
    colors=PROV_COLORS,
    title="Provincial Annual Births — Mid Scenario (1971–2100)",
    xlabel="Annual births (5-yr avg)",
    out_path="plots/fg_bcr6_prov_births.mp4",
    value_fmt_fn=fmt_pop,
)

print("\nAll done.")
