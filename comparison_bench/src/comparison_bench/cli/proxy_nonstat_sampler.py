"""Synthetic nonstationary proxy sampler (PROXY-NONSTATIONARY-FAITHFULNESS).

EXPLORE synthetic double-gate driver. Stdlib + numpy only; zero decoder
calls by construction (DECODE_COUNT is hardcoded 0 and asserted before any
draw). Frozen inputs F-1..F-8, proxy S-N1..S-N6, metric S4 and rule S5 come
from docs/research_cycles/PROXY-NONSTATIONARY-FAITHFULNESS/PREREG_AND_AUTH.md;
this module transcribes them and performs no other science.

Refusal lines below (input path-gate, root gate, flag gate) are the only
places naming refused decoder/timing/data extensions; there are no
read-shaped paths to them anywhere in this file.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ---- Frozen inputs F-1..F-8 (transcribed, see PREREG_AND_AUTH.md S2) ----
N = 383  # F-1 eval-region length
Z_MEASURED = -1.74066440  # F-2 (context; gate uses the band only)
Z_BAND = 3.0  # F-2 null band |z| <= 3
R_MEASURED = 0.12224678  # F-3 (context; gate uses the band only)
R_BAND = 0.15329284  # F-3 null band |r1| <= 3/sqrt(383)
D_MEASURED = 0.80642234  # F-4 (context; gate uses the band only)
D_BAND = 1.21707238  # F-4 upper-only band D <= 1+3*sqrt(2/382)
FLOOR = 1e-6  # F-5 detection floor
SEG_CAP = 1800.0  # F-6 per-segment cap (seconds)
TOTAL_CAP = 10800.0  # F-6 total cap (seconds)
PER_SEG = 40  # F-6 frames per segment
N_COST = 240  # F-6 partition size
U_MEAN = 51.0  # F-7 descriptive per-block wall label (NOT performance)
U_MAX = 80.8  # F-7 descriptive per-block max label (NOT performance)
MEAN_CTX = 259.8486  # F-8 context mean (never a gate target)
MIN_CTX = 202  # F-8 context min
MAX_CTX = 299  # F-8 context max

# ---- Frozen proxy S-N1/S-N2 ----
R_REP = 500  # S-N1 replicates per arm
SEED_BASE = 2026099001  # S-N1 seed base, replicate r uses base + r
N_SYM = 1024  # S-N2 symbols per position
P_BASE = 0.25375836  # S-N2 count scale
DELTA_CTRL = 0.0  # S-N2 control arm (stationary)
DELTA_DRIFT = 0.02  # S-N2 drift arm (absolute peak-to-peak, frozen)
TOL = 0.003  # S5.3 carried ser tolerance (descriptive count mean only)

# Zero-decoder construction (S-N5): hardcoded count with assertion.
DECODE_COUNT = 0

CEILING = (
    "> This stage produces a synthetic proxy-faithfulness + arithmetic-cost "
    "result about a generator, nothing more. It establishes NO FER, NO "
    "efficiency, NO leakage, NO f, NO SKR and NO key figure for any method; "
    "NO method comparison, NO ranking and NO combined table; NO claim that "
    "any code improves; NO claim that the proxy equals the real channel; "
    "and NO real-recal license of any kind. The value 0.098260 is never "
    "cited as a measurement. The void HDC and void Layered-Binary figures "
    "are never used as a baseline in any form. The number 51.0 s is a "
    "descriptive per-block wall label, never a throughput or performance "
    "figure. No 10/240 comparison is made and no 35/35 trend sentence is "
    "written. A FAITHFUL_AND_COST_FEASIBLE word licenses only an "
    "application for a DECIDE recal packet; it licenses no performance "
    "claim, no decoder claim, and no execution."
)


class Refusal(Exception):
    """Raised on any gate refusal (path, root, flag, formula, collision)."""


# ---- Frozen statistics S-N3 (general two-half split; n1 = n//2) ----

def compute_z(x) -> float:
    """Two-half mean-difference drift statistic (S-N3).

    First half X_0..n1-1 vs second half X_n1..n-1 with n1 = n // 2
    (n = 383 gives the frozen 191 / 192 split). Returns 0.0 on a
    degenerate zero-variance input (never occurs for binomial draws).
    """
    v = [float(t) for t in x]
    n = len(v)
    if n < 4:
        raise Refusal(f"compute_z needs n >= 4, got {n}")
    n1 = n // 2
    n2 = n - n1
    a = v[:n1]
    b = v[n1:]
    m1 = sum(a) / n1
    m2 = sum(b) / n2
    s1 = sum((t - m1) ** 2 for t in a) / (n1 - 1)
    s2 = sum((t - m2) ** 2 for t in b) / (n2 - 1)
    den = s1 / n1 + s2 / n2
    if den <= 0.0:
        return 0.0
    return (m2 - m1) / math.sqrt(den)


def compute_r1(x) -> float:
    """Lag-1 Pearson autocorrelation of the sequence (S-N3)."""
    v = [float(t) for t in x]
    n = len(v)
    if n < 3:
        raise Refusal(f"compute_r1 needs n >= 3, got {n}")
    m = sum(v) / n
    d = [t - m for t in v]
    den = sum(t * t for t in d)
    if den == 0.0:
        return 0.0
    num = sum(d[i] * d[i + 1] for i in range(n - 1))
    return num / den


def compute_D(x) -> float:
    """Dispersion s^2 / m with sample variance ddof=1 (S-N3)."""
    v = [float(t) for t in x]
    n = len(v)
    if n < 2:
        raise Refusal(f"compute_D needs n >= 2, got {n}")
    m = sum(v) / n
    if m == 0.0:
        return 0.0
    s2 = sum((t - m) ** 2 for t in v) / (n - 1)
    return s2 / m


def median_of(vals) -> float:
    """Median across replicates (S-N3 aggregation; single gate statistic)."""
    v = sorted(float(t) for t in vals)
    if not v:
        raise Refusal("median_of empty input")
    n = len(v)
    mid = n // 2
    if n % 2 == 1:
        return v[mid]
    return (v[mid - 1] + v[mid]) / 2.0


# ---- Front-loaded cost arithmetic S3.5 ----

def cost_block_cap(seg_cap: float, per_seg: int,
                   total_cap: float, n_cost: int) -> float:
    """Required per-block upper forced by the partition (S3.5)."""
    return min(seg_cap / per_seg, total_cap / n_cost)


def cost_extrapolation(u_assume: float, n_cost: int) -> float:
    """Whole-partition extrapolation ceiling E = n_cost * u_assume."""
    return n_cost * u_assume


# ---- Honesty flag S5.3 ----

def honesty_flags(p_med_drift: float, u_used: float):
    """Optimistic-proxy flag FLAG = O_err AND O_cost (S5.3, frozen)."""
    o_err = p_med_drift < (P_BASE - TOL)
    o_cost = u_used < U_MEAN
    return o_err, o_cost, (o_err and o_cost)


# ---- Single mechanical verdict S5 (priority C1 > C2 > C3) ----

def decide_word(zc, rc, dc, zd, rd, dd,
                p_med_drift: float, u_assume: float):
    """Exactly one verdict word with the fired clause cited (S5)."""
    c1a = abs(zc) > Z_BAND or abs(rc) > R_BAND or dc > D_BAND
    c1b = DELTA_DRIFT < FLOOR
    drift_quiet = (abs(zd) <= Z_BAND and abs(rd) <= R_BAND
                   and dd <= D_BAND)
    if c1a or c1b or drift_quiet:
        if c1a:
            clause = "S5.1 K-C1a control reproduction fails"
        elif c1b:
            clause = "S5.1 K-C1b injected drift below detection floor"
        else:
            clause = "S5.1 K-C1c drift insensitive (drift arm all-quiet)"
        return "UNFAITHFUL_PROXY_KILL", clause
    c_req = cost_block_cap(SEG_CAP, PER_SEG, TOTAL_CAP, N_COST)
    if u_assume > c_req or cost_extrapolation(u_assume, N_COST) > TOTAL_CAP:
        return ("STRUCTURALLY_INCOMPLETE_KILL",
                "S5.2 K-C2 arithmetic bound already exceeded")
    _, _, flag = honesty_flags(p_med_drift, u_assume)
    if flag:
        return ("OPTIMISTIC_PROXY_KILL",
                "S5.3 K-C3 optimistic-proxy flag true")
    return ("FAITHFUL_AND_COST_FEASIBLE",
            "S5.4 none of K-C1/K-C2/K-C3 fires")


# ---- Gates: input path, root format, CLI flags ----

FORBIDDEN_SUFFIXES = (".ttbin", ".npz", ".parquet")
FORBIDDEN_NAME = "rows.json"
FORBIDDEN_FLAG_HINTS = ("decod", "ldpc", "max_iter", "timing",
                        "construct", "graph", "warm", "stage")


def check_input_path(path, root) -> None:
    """Refuse any input path outside the fresh root or naming a refused
    data extension (refusal-gate; called before any read)."""
    s = str(path)
    if FORBIDDEN_NAME in s:
        raise Refusal(f"refused data name in path: {s}")
    if s.endswith(FORBIDDEN_SUFFIXES):
        raise Refusal(f"refused data extension in path: {s}")
    try:
        Path(s).resolve().relative_to(Path(root).resolve())
    except ValueError:
        raise Refusal(f"path outside fresh root: {s}")
    return None


def check_root_format(root) -> None:
    """Accept only workspace/proxy_nonstat_<8 hex> (refusal-gate)."""
    if not re.fullmatch(r"workspace/proxy_nonstat_[0-9a-f]{8}", str(root)):
        raise Refusal(f"root pattern refused: {root}")
    return None


def parse_args(argv):
    """Argv takes --root plus both execution flags; any decoder/timing
    flag hint is refused (refusal-gate)."""
    for a in argv:
        if a.startswith("--"):
            norm = a[2:].replace("-", "_")
            if any(h in norm for h in FORBIDDEN_FLAG_HINTS):
                raise Refusal(f"refused decoder/timing flag: {a}")
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--execute-synthetic", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    ns = ap.parse_args(argv)
    if not (ns.execute_synthetic and ns.execution_authorized):
        raise Refusal("need both --execute-synthetic --execution-authorized")
    check_root_format(ns.root)
    return ns


# ---- Synthetic draws S-N1/S-N2 ----

def draw_replicate(rng, delta: float):
    """One 383-position count sequence: Binomial(1024, p_i) with the
    frozen linear drift injection (S-N2)."""
    pos = np.arange(N, dtype=float)
    p = P_BASE + delta * (pos / (N - 1) - 0.5)
    np.clip(p, 0.0, 1.0, out=p)
    return rng.binomial(N_SYM, p).astype(float)


def run_arm(delta: float):
    """Run one arm: R paired replicates; per-replicate z/r1/D plus
    emergent ser; medians are the single gate statistics (S-N1..S-N3)."""
    zs, rs, ds, ps = [], [], [], []
    for r in range(R_REP):
        rng = np.random.default_rng(SEED_BASE + r)
        x = draw_replicate(rng, delta)
        zs.append(compute_z(x))
        rs.append(compute_r1(x))
        ds.append(compute_D(x))
        ps.append(float(np.mean(x)) / N_SYM)
    return {"z_med": median_of(zs), "r_med": median_of(rs),
            "d_med": median_of(ds), "p_med": median_of(ps)}


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main(argv=None) -> int:
    ns = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(ns.root)
    root.mkdir(parents=False, exist_ok=True)
    d1 = root / "PROXY_NONSTAT_RESULT.json"
    d2 = root / "PROXY_NONSTAT_SUMMARY.md"
    d3 = root / "EXPLORATION_LOG.md"
    if d1.exists() or d2.exists():
        raise Refusal("output collision: D-1/D-2 already exist")
    assert DECODE_COUNT == 0, "zero-decoder construction violated"

    # T-3a front arithmetic record FIRST: pure derivation, zero draws,
    # zero timing (S3.5). Recorded before the first synthetic draw.
    c_req = cost_block_cap(SEG_CAP, PER_SEG, TOTAL_CAP, N_COST)
    e_req = cost_extrapolation(c_req, N_COST)
    e_assume = cost_extrapolation(U_MEAN, N_COST)
    k_c2 = (U_MEAN > c_req) or (e_assume > TOTAL_CAP)
    with open(d3, "a", encoding="utf-8") as f:
        f.write(f"## T-3a front cost arithmetic (recorded {utcnow()}, "
                "before any draw)\n");
        f.write(f"C_req = min({SEG_CAP}/{PER_SEG}, "
                f"{TOTAL_CAP}/{N_COST}) = {c_req} s/block\n")
        f.write(f"E_req = {N_COST} x {c_req} = {e_req} s\n")
        f.write(f"U_assume(0) = U_mean = {U_MEAN} s/block (descriptive "
                "label, lenient assumption alpha = 0)\n")
        f.write(f"U_max = {U_MAX} s/block (descriptive context only)\n")
        f.write(f"{U_MEAN} > {c_req} = {U_MEAN > c_req}; "
                f"{N_COST} x {U_MEAN} = {e_assume} > {TOTAL_CAP} = "
                f"{e_assume > TOTAL_CAP}\n")
        f.write(f"K-C2 arithmetic verdict: "
                f"{'FIRES' if k_c2 else 'not fired'} (zero timing, "
                "zero draws so far)\n")

    # T-2 draws (numpy only; decode count stays 0).
    t0 = time.perf_counter()
    ctrl = run_arm(DELTA_CTRL)
    drift = run_arm(DELTA_DRIFT)
    wall_s = time.perf_counter() - t0
    assert DECODE_COUNT == 0, "zero-decoder construction violated"
    peak_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    o_err, o_cost, flag = honesty_flags(drift["p_med"], U_MEAN)
    word, clause = decide_word(
        ctrl["z_med"], ctrl["r_med"], ctrl["d_med"],
        drift["z_med"], drift["r_med"], drift["d_med"],
        drift["p_med"], U_MEAN)

    def margin(med, band):
        return band - abs(med)

    result = {
        "inputs": {
            "F-1 n": N, "F-2 z": Z_MEASURED, "F-2 band": Z_BAND,
            "F-3 r1": R_MEASURED, "F-3 band": R_BAND,
            "F-4 D": D_MEASURED, "F-4 band_upper_only": D_BAND,
            "F-5 floor": FLOOR,
            "F-6 segCap": SEG_CAP, "F-6 totalCap": TOTAL_CAP,
            "F-6 partition": [6, PER_SEG], "F-6 N_cost": N_COST,
            "F-7 U_mean_descriptive": U_MEAN,
            "F-7 U_max_descriptive": U_MAX,
            "F-8 mean_ctx": MEAN_CTX, "F-8 min_ctx": MIN_CTX,
            "F-8 max_ctx": MAX_CTX,
            "doc pointers": ["docs/decision-log.md:5227",
                             "PROXY-RECAL-R2 S8"],
        },
        "proxy": {
            "S-N1": {"N": N, "R": R_REP, "seeds": f"{SEED_BASE}+r r=0..499",
                     "streams": "nonstat:{arm}:{r}, paired both arms"},
            "S-N2": {"n_sym": N_SYM, "p_base": P_BASE,
                     "delta_ctrl": DELTA_CTRL, "delta_drift": DELTA_DRIFT},
            "S-N3": "frozen z/r1/D formulas, median aggregation",
            "S-N4": "D upper-only, no lower bound",
            "S-N5": "numpy-only, zero-decoder",
            "S-N6": "synthetic sensitivity probe only",
        },
        "fidelity": {
            "control": {
                "z_med": ctrl["z_med"], "z_margin": margin(ctrl["z_med"], Z_BAND),
                "r_med": ctrl["r_med"], "r_margin": margin(ctrl["r_med"], R_BAND),
                "d_med": ctrl["d_med"], "d_margin": D_BAND - ctrl["d_med"],
                "p_med": ctrl["p_med"],
                "quiet": (abs(ctrl["z_med"]) <= Z_BAND
                          and abs(ctrl["r_med"]) <= R_BAND
                          and ctrl["d_med"] <= D_BAND),
            },
            "drift": {
                "z_med": drift["z_med"],
                "z_margin": margin(drift["z_med"], Z_BAND),
                "r_med": drift["r_med"],
                "r_margin": margin(drift["r_med"], R_BAND),
                "d_med": drift["d_med"],
                "d_margin": D_BAND - drift["d_med"],
                "p_med": drift["p_med"],
                "all_quiet": (abs(drift["z_med"]) <= Z_BAND
                              and abs(drift["r_med"]) <= R_BAND
                              and drift["d_med"] <= D_BAND),
            },
        },
        "cost": {
            "C_req": c_req, "E_req": e_req,
            "U_mean_descriptive": U_MEAN, "U_max_descriptive": U_MAX,
            "U_assume_alpha0": U_MEAN,
            "E_assume": e_assume, "totalCap": TOTAL_CAP,
            "k_c2_fires": k_c2,
        },
        "honesty": {
            "p_med_drift": drift["p_med"], "p_base": P_BASE,
            "tol": TOL, "O_err": o_err,
            "U_used": U_MEAN, "U_mean": U_MEAN, "O_cost": o_cost,
            "FLAG": flag,
        },
        "decision": {"word": word, "clause": clause,
                     "priority": "C1 > C2 > C3"},
        "resources": {
            "numpy wall_s": wall_s, "peak_rss_kb": peak_rss_kb,
            "cpu": os.cpu_count(),
            "thread_pin_env": {
                "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
                "OPENBLAS_NUM_THREADS": os.environ.get(
                    "OPENBLAS_NUM_THREADS"),
                "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
                "NUMEXPR_NUM_THREADS": os.environ.get(
                    "NUMEXPR_NUM_THREADS"),
                "NUMBA_NUM_THREADS": os.environ.get("NUMBA_NUM_THREADS"),
            },
            "decode_count": DECODE_COUNT,
        },
    }
    with open(d1, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    lines = [
        "# PROXY-NONSTATIONARY-FAITHFULNESS summary",
        "",
        "## Triple table (medians across 500 paired replicates)",
        "",
        "| arm | z_med (|z|<=3) | r_med (|r|<=0.15329284) | "
        "D_med (<=1.21707238) | p_med |",
        "|---|---|---|---|---|",
        f"| control (drift 0) | {ctrl['z_med']:.6f} | {ctrl['r_med']:.6f} "
        f"| {ctrl['d_med']:.6f} | {ctrl['p_med']:.8f} |",
        f"| drift (0.02) | {drift['z_med']:.6f} | {drift['r_med']:.6f} "
        f"| {drift['d_med']:.6f} | {drift['p_med']:.8f} |",
        "",
        "## Cost table (front arithmetic, descriptive labels)",
        "",
        f"C_req = 45 s/block; U_mean = 51.0 s/block (descriptive); "
        f"51.0 > 45 fires K-C2; 240 x 51.0 = 12240 > 10800 fires K-C2.",
        "",
        "## Honesty table",
        "",
        f"O_err = {o_err} (p_med_drift {drift['p_med']:.8f} vs "
        f"p_base - 0.003 = {P_BASE - TOL:.8f}); O_cost = {o_cost} "
        f"(U_used 51.0 vs U_mean 51.0); FLAG = {flag}.",
        "",
        "## Verdict",
        "",
        f"{word} ({clause}; priority C1 > C2 > C3).",
        "",
        "## Claim ceiling (verbatim)",
        "",
        CEILING,
        "",
    ]
    with open(d2, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(d3, "a", encoding="utf-8") as f:
        f.write(f"\n## T-2 draws (recorded {utcnow()})\n")
        f.write(f"control medians z/r/D/p = {ctrl['z_med']:.6f} / "
                f"{ctrl['r_med']:.6f} / {ctrl['d_med']:.6f} / "
                f"{ctrl['p_med']:.8f}\n")
        f.write(f"drift medians z/r/D/p = {drift['z_med']:.6f} / "
                f"{drift['r_med']:.6f} / {drift['d_med']:.6f} / "
                f"{drift['p_med']:.8f}\n")
        f.write(f"O_err={o_err} O_cost={o_cost} FLAG={flag}\n")
        f.write(f"verdict: {word} ({clause})\n")
        f.write(f"resources: numpy wall_s={wall_s:.1f} "
                f"peak_rss_kb={peak_rss_kb} decode_count={DECODE_COUNT}\n")
    print(f"verdict: {word} ({clause})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as e:
        print(f"REFUSAL: {e}", file=sys.stderr)
        sys.exit(2)
