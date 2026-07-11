"""
Recalibrate per-province net-growth rate (natural_increase.csv nodes) so the
full agent model reproduces the provincial census series 1971->2025.

Method: iterative damped coordinate correction. Each pass runs the real model
to 2025, compares the model's growth over each census period to the target
growth for each province, and nudges the NI node at the end of that period.
Converges because NI directly (multiplicatively) drives provincial growth;
inter-province coupling via migration is a second-order perturbation.

Historical NI nodes fitted: 1981,1991,2001,2011,2021,2024 (1971 held fixed).
Post-2025 projection nodes are re-based afterwards (see rebase_projection).
"""
import csv, numpy as np
from canada_sim import CanadaSimulator
from loaders import PROVINCES, P_IDX, LANGUAGES

SCALE = 100
NODE_YEARS = [1971, 1981, 1991, 2001, 2011, 2021, 2024, 2030, 2050, 2075, 2100, 2150]
FIT_NODES = [1981, 1991, 2001, 2011, 2021, 2024]  # historical nodes we tune
# census period ending at each fit node: (prev_census, cur_census_target)
NODE_PERIOD = {1981: (1971, 1981), 1991: (1981, 1991), 2001: (1991, 2001),
               2011: (2001, 2011), 2021: (2011, 2021), 2024: (2021, 2025)}
# Territories (tiny, one starts at 0 pop in 1971) keep their original NI.
FIT_PROVS = [p for p in PROVINCES if p not in ("YT", "NT", "NU")]


def load_ni():
    rows = {}
    with open("data/natural_increase.csv") as f:
        for row in csv.DictReader(r for r in f if not r.startswith("#")):
            rows[int(row["year"])] = {p: float(row[p]) for p in PROVINCES}
    return rows


def load_targets():
    tgt = {}
    with open("data/historical_provincial_population.csv") as f:
        for row in csv.DictReader(r for r in f if not r.startswith("#")):
            tgt[int(row["year"])] = {p: float(row[p]) * 1000 for p in PROVINCES}
    return tgt


def make_ni_fn(ni_nodes):
    yrs = np.array(NODE_YEARS, float)
    cols = {p: np.array([ni_nodes[y][p] for y in NODE_YEARS], float) for p in PROVINCES}
    def fn(year):
        return np.array([np.interp(year, yrs, cols[p]) for p in PROVINCES])
    return fn


def run_model(ni_nodes, seed=42):
    sim = CanadaSimulator("mid", scale=SCALE, seed=seed)
    sim.natural_increase_fn = make_ni_fn(ni_nodes)
    sim.run(until_year=2025, verbose=False)
    by = {r["year"]: r for r in sim.history}
    prov_pop = {}
    for y in [1971, 1981, 1991, 2001, 2011, 2021, 2025]:
        r = by[y]
        prov_pop[y] = {p: sum(r[f"{p}_{l}"] for l in LANGUAGES) for p in PROVINCES}
    return prov_pop


def calibrate(passes=16, damping=0.65):
    ni = load_ni()
    tgt = load_targets()
    for it in range(passes):
        pp = run_model(ni)
        maxerr = 0.0
        for node in FIT_NODES:
            y0, y1 = NODE_PERIOD[node]
            span = y1 - y0
            for p in FIT_PROVS:
                gm = pp[y1][p] / max(pp[y0][p], 1)
                gt = tgt[y1][p] / max(tgt[y0][p], 1)
                # annual log-growth gap -> additive NI correction at this node
                corr = damping * (np.log(gt) - np.log(gm)) / span
                corr = float(np.clip(corr, -0.02, 0.02))
                ni[node][p] = float(np.clip(ni[node][p] + corr, -0.03, 0.05))
            # track worst provincial error at 2025
        e2025 = max(abs(pp[2025][p] / tgt[2025][p] - 1) for p in FIT_PROVS)
        print(f"  pass {it+1:2d}: max |err| @2025 = {100*e2025:5.2f}%")
        maxerr = e2025
        if maxerr < 0.02:
            break
    return ni, run_model(ni), tgt


def rebase_projection(ni):
    """Re-base post-2025 nodes onto the fitted 2021 *structural* level (the net
    migration/natural compensation, BEFORE the 2021-25 immigration/NPR boom),
    preserving the original below-replacement decline shape. This keeps each
    province's structural growth correction while letting the transient boom
    (captured in the 2024 node) decay out by 2030 -- consistent with the sharp
    post-2025 slowdown StatCan is already observing."""
    old = load_ni()
    for p in PROVINCES:
        base_new = ni[2021][p]        # pre-boom structural level
        base_old = old[2021][p]
        for y in [2030, 2050, 2075, 2100, 2150]:
            ni[y][p] = base_new + (old[y][p] - base_old)
    return ni


def write_ni(ni, path="data/natural_increase.csv"):
    header = (
        "# =============================================================================\n"
        "# NET PROVINCIAL GROWTH RATE (annual) -- was 'natural increase'\n"
        "# =============================================================================\n"
        "# Net endogenous provincial growth as a fraction of current population per\n"
        "# year: births minus deaths PLUS the net-migration / non-permanent-resident\n"
        "# residual, RECALIBRATED so the agent model reproduces the provincial census\n"
        "# series in historical_provincial_population.csv (1971-2025) province by\n"
        "# province. (Interprovincial moves are still modelled explicitly for their\n"
        "# language selectivity; this rate absorbs the net total-population residual.)\n"
        "#\n"
        "# Fitted historical nodes: 1981,1991,2001,2011,2021,2024.\n"
        "# Post-2025 nodes = fitted 2021 structural level + a ~-0.2pt/decade\n"
        "# below-replacement drift (shape preserved by rebase_projection). The\n"
        "# DIRECTION of that drift is grounded in StatCan Population Projections\n"
        "# (Cat. 91-520-X) and, for Quebec, ISQ (neg. natural increase from 2027).\n"
        "# NOTE: this is a NET rate (natural change + migration/NPR residual), so\n"
        "# for immigration-heavy provinces the negative sign is a calibration\n"
        "# residual, NOT projected natural decline -- e.g. Alberta's negative node\n"
        "# offsets over-allocated immigration; AB's true natural increase is\n"
        "# positive. See methodology.md 'How the post-2025 nodes are set'.\n"
        "#\n"
        "# New people inherit the current language distribution of their province.\n"
        "# Linear interpolation between rows.\n"
        "#\n"
        "# Columns: year," + ",".join(PROVINCES) + "\n"
        "# =============================================================================\n"
    )
    with open(path, "w") as f:
        f.write(header)
        f.write("year," + ",".join(PROVINCES) + "\n")
        for y in NODE_YEARS:
            vals = ",".join(f"{ni[y][p]:.4f}" for p in PROVINCES)
            f.write(f"{y},{vals}\n")


if __name__ == "__main__":
    ni, pp, tgt = calibrate()
    print("\n  2025 fit (model/target, thousands):")
    for p in PROVINCES:
        print(f"    {p}: {pp[2025][p]/1e3:7.1f} / {tgt[2025][p]/1e3:7.1f}  "
              f"{100*(pp[2025][p]/tgt[2025][p]-1):+5.1f}%")
    ni = rebase_projection(ni)
    write_ni(ni)
    print("\n  wrote data/natural_increase.csv")
    print("  fitted NI nodes (%/yr):")
    print("    year " + " ".join(f"{p:>6}" for p in ["QC","ON","AB","BC","MB","SK","NS"]))
    for y in [1981,2001,2021,2024]:
        print(f"    {y} " + " ".join(f"{100*ni[y][p]:6.2f}" for p in ["QC","ON","AB","BC","MB","SK","NS"]))
