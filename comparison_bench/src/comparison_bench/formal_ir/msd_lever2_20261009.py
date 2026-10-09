"""msd_lever2_20261009 — LEVER-2: measured-leak lever arithmetic (EXPLORE).

Adapted one-shot of the void LEVER-BUDGET-20261009 packet SS1/SS2, executed under
the current state with the S-4d accepted measured full-chain leak replacing the
f-proxy leak.  Run record: ``docs/research_cycles/C-BATCH/LEVER2_LOG.md``.

Model (plain math, identical to the void packet SS1):
    T_f = 204800 ps;  d = T_f/bw;  n = R_pair(s)*T_cap;  n_k = (1-r_PE)*n
    e_p = (1-V)/2 ;  e_p^U = e_p + sqrt(ln(1/eps_PE) / (2*r_PE*n))
    chi_E = h2(e_p^U) + e_p^U*log2(d-1)  (FK-A) ;  chi_E = h2(e_p) + e_p*log2(d-1) (FK-B)
    H_A = log2 d
    FK-A: ell = y*[ n_k*(H_A - chi_E^U) - leak_EC ]
                - log2(2/eps_cor) - 2*log2(1/(2*eps_PA))
    FK-B: ell = y*n_k*[ H_A - chi_E(e_p) - lam - DFK(n_k) ]
          DFK(n_k) = 4*sqrt(log2(2/eps_sec)/n_k) + 2*log2(2/eps_cor)/n_k
    leak_EC = lam * n_k ;  ell < 0 -> 0 with zero_key=True

LEVER-2 delta vs the void packet: the BASELINE leak term is the S-4d MEASURED
full-chain leak per pair, ``lam = (L_A + L_B) / (blocks*N)`` of the accepted
hard/plain cell (bw=200, calibrated chain, N=4096), instead of ``f*H(A|B)_theta``.
S-4d accepted full-chain nets and S-4d level-A FERs (okA gate, from
``s4d_blocks.jsonl``) are transcribed inputs.

Scope: EXPLORE.  Proxy model; numbers are for LEVER ORDERING only; no FER/SKR/
publication claim.  Franson V stays an ASSUMED sensitivity parameter.
No raw-data read, no decoding, numpy + math only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# INPUTS — every value transcribed with provenance, no invented numbers.
# doc provenance is the accepted cycle document; machine provenance is the
# accepted artifact (cross-checked at runtime, see check_inputs()).
# ---------------------------------------------------------------------------
SOURCES = ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB")

INPUTS = {
    # frame-bin identity of the Z-3 grid: d*bw = T_f = 204.8 ns (=204800 ps)
    "T_F_PS": 204800.0,
    # void packet SS1 epsilon budget
    "eps_sec": 1e-10,
    "eps_cor": 1e-10,

    # (pairs/s) Z-3 surface, accepted: workspace/z3_surface/z3_20261008/z3_surface.json
    # (Z3_INDEPENDENT_ACCEPTANCE.md); identical across bw in that grid.
    "R_pair_s": {
        "T2-1M": 175277.0,
        "T2-1.5M": 245260.0,
        "T2-2M": 327394.0,
        "0dB": 88879.3,
        "4dB": 38463.3,
    },
    # nominal (uncalibrated framing) H(A|B) from the same Z-3 artifact, per bw.
    # NOTE: bw=100/400 rows carry status "UNMEASURED (extrapolation or wide-support
    # regime)" and are transcribed for provenance only — the L-bw lever does NOT use
    # them (void SS2 prescribes the A5 model for calibrated bw != 200).
    "H_AB_nominal_bw": {
        100.0: {"T2-1M": 1.0242, "T2-1.5M": 1.0331, "T2-2M": 1.0424,
                "0dB": 1.0202, "4dB": 1.0060},
        200.0: {"T2-1M": 0.8007, "T2-1.5M": 0.8262, "T2-2M": 0.8306,
                "0dB": 0.8132, "4dB": 0.7923},
        400.0: {"T2-1M": 0.5303, "T2-1.5M": 0.5529, "T2-2M": 0.5555,
                "0dB": 0.5426, "4dB": 0.5283},
    },
    # S-2 2x2 table, bw=200, test-part empirical values (S2_RESULT.md SS2);
    # machine cross-check: workspace/s_softmap/s2_20261009/s2_summary.json
    # sources[src].cells["200"]. H_hard_cal is the denominator S-4d used for
    # f_ref (verified: lam/H_hard_cal reproduces every S-4d f_ref to 1e-4).
    "H_hard_cal": {"T2-1M": 0.3891, "T2-1.5M": 0.4094, "T2-2M": 0.4324,
                   "0dB": 0.3855, "4dB": 0.3746},
    "H_soft_cal": {"T2-1M": 0.2405, "T2-1.5M": 0.2571, "T2-2M": 0.2723,
                   "0dB": 0.2408, "4dB": 0.2326},
    # B2 empirical soft-information gain, bw=200 (B123_RESULT.md SSB2) — used as a
    # consistency column only (H_nominal - G vs S-2 H_soft_cal).
    "G_B2_bw200": {"T2-1M": 0.5633, "T2-1.5M": 0.5711, "T2-2M": 0.5603,
                   "0dB": 0.5780, "4dB": 0.5700},
    # B3 light-source table (B123_RESULT.md SSB3), T2 sources only; 0dB/4dB are
    # ABSENT in B3 -> recorded as absent, never invented.
    "B3": {
        "T2-1M": {"nominal_p": 0.23797, "cal_p": 0.06074, "p_minus": 0.609,
                  "H_e": 0.3892, "H_e_nominal": 0.804},
        "T2-1.5M": {"nominal_p": 0.25426, "cal_p": 0.06449, "p_minus": 0.519,
                    "H_e": 0.4098, "H_e_nominal": 0.8286},
        "T2-2M": {"nominal_p": 0.25571, "cal_p": 0.06917, "p_minus": 0.519,
                  "H_e": 0.4324, "H_e_nominal": 0.8326},
    },
    # S-4a sign-prior diagnostic, bw=200 calibrated (S4A_RESULT.md SS1)
    "S4A_marked_sgn": {"T2-1M": (0.061, 0.609), "T2-1.5M": (0.065, 0.520),
                       "T2-2M": (0.069, 0.520), "0dB": (0.060, 0.529),
                       "4dB": (0.058, 0.609)},
    # A5 Type-II mixed-law model, row law="dg18.5/100.0/0.014", sigma=18.5, mu=0
    # (workspace/swnow_20261009/a5_20261009/a5_rates.json).  Used for the L-bw
    # lever at bw != 200 and for the all-A5 auxiliary variant.
    "A5_R_hard": {100.0: 0.7851, 200.0: 0.4755, 400.0: 0.2777},
    "A5_R_soft": {100.0: 0.5409, 200.0: 0.2762, 400.0: 0.1256},
    "A5_p": {100.0: 0.1538, 200.0: 0.0782, 400.0: 0.0392},

    # S-4d accepted full chain (S4D_RESULT.md SS3; workspace/s4d_rerun/s4d_20261009/
    # s4d_cells.json).  N=4096; blocks 128/179/239/65/28 (S4D_PREEXECUTE.md SS2).
    "S4D_N": 4096,
    "S4D_blocks": {"T2-1M": 128, "T2-1.5M": 179, "T2-2M": 239, "0dB": 65, "4dB": 28},
    "S4D_hard_plain": {
        "T2-1M": {"L_A": 211470, "L_B": 25603, "Net_seg": 4057007, "f_ref": 1.1621},
        "T2-1.5M": {"L_A": 312294, "L_B": 37936, "Net_seg": 5620586, "f_ref": 1.1668},
        "T2-2M": {"L_A": 415288, "L_B": 51415, "Net_seg": 7058161, "f_ref": 1.1025},
        "0dB": {"L_A": 112224, "L_B": 13569, "Net_seg": 2164383, "f_ref": 1.2256},
        "4dB": {"L_A": 48672, "L_B": 5693, "Net_seg": 927139, "f_ref": 1.2654},
    },
    "S4D_soft_plain": {
        "T2-1M": {"L_A": 243694, "L_B": 30131, "Net_seg": 4674591, "f_ref": 2.1716},
        "T2-1.5M": {"L_A": 335823, "L_B": 41485, "Net_seg": 6043364, "f_ref": 2.0016},
        "T2-2M": {"L_A": 440115, "L_B": 55424, "Net_seg": 7479181, "f_ref": 1.8590},
        "0dB": {"L_A": 120240, "L_B": 14693, "Net_seg": 2318827, "f_ref": 2.1047},
        "4dB": {"L_A": 48672, "L_B": 5693, "Net_seg": 927139, "f_ref": 2.0379},
    },
    # S-4d level-A (okA) gate failures / blocks, from s4d_blocks.jsonl
    "S4D_FER_la": {
        "T2-1M": {"hard": (17, 128), "soft": (0, 128)},
        "T2-1.5M": {"hard": (14, 179), "soft": (0, 179)},
        "T2-2M": {"hard": (11, 239), "soft": (0, 239)},
        "0dB": {"hard": (4, 65), "soft": (0, 65)},
        "4dB": {"hard": (0, 28), "soft": (0, 28)},
    },
    # S-4d full-chain FER (S4D_RESULT.md SS3)
    "S4D_FER_full": {
        "T2-1M": {"hard": 0.1797, "soft": 0.0547},
        "T2-1.5M": {"hard": 0.1844, "soft": 0.1229},
        "T2-2M": {"hard": 0.2301, "soft": 0.1841},
        "0dB": {"hard": 0.1385, "soft": 0.0769},
        "4dB": {"hard": 0.1429, "soft": 0.1429},
    },
}

# grid (frozen, void SS2/SS3)
T_CAP_GRID = (3.0, 10.0)
FK_MODES = ("A", "B")
V_GRID = (0.90, 0.95, 0.98)
V_LEVER_GRID = (0.90, 0.98, 0.99)          # 0.90 downside; 0.99 upward idealization
R_PE_B0 = 0.10
R_PE_GRID = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5)
EPS_LEVER = 1e-6
FER_LEVER = (0.05, 0.10)
BW_BASE = 200.0
RPE_ASYM = R_PE_B0

# levers participating in the ranking (one primary variant each; void SS3 excludes
# L-cal+soft and L-T->inf from the ranking, and here also the calibration lever
# itself because it is already absorbed into the measured S-4d baseline).
RANKED_LEVERS = ("L-f", "L-soft", "L-bw", "L-T", "L-V", "L-PE", "L-eps", "L-FER")


# ---------------------------------------------------------------------------
# math
# ---------------------------------------------------------------------------
def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def h2_np(x: np.ndarray) -> np.ndarray:
    xc = np.clip(x, 0.0, 1.0)
    pos = (xc > 0.0) & (xc < 1.0)
    xa = np.clip(xc, 1e-300, 1.0)
    val = -xa * np.log2(xa) - (1.0 - xa) * np.log2(np.clip(1.0 - xa, 1e-300, 1.0))
    return np.where(pos, val, 0.0)


def chi_e(d: float, e: float) -> float:
    """Eve-information proxy, same form as the repository."""
    return h2(e) + e * math.log2(d - 1.0)


def e_upper(V: float, r_pe: float, n: float, eps_pe: float) -> float:
    e_p = (1.0 - V) / 2.0
    if n <= 0.0 or r_pe <= 0.0:
        return e_p
    return e_p + math.sqrt(math.log(1.0 / eps_pe) / (2.0 * r_pe * n))


def delta_fk(n_k: float, eps_sec: float, eps_cor: float) -> float:
    return (4.0 * math.sqrt(math.log2(2.0 / eps_sec) / n_k)
            + 2.0 * math.log2(2.0 / eps_cor) / n_k)


def d_of_bw(bw: float) -> float:
    return INPUTS["T_F_PS"] / bw


def evaluate(src: str, t_cap: float, fk: str, V: float, lam: float, *,
             bw: float = BW_BASE, r_pe: float = R_PE_B0, fer: float = 0.0,
             eps_sec: float = INPUTS["eps_sec"], eps_cor: float = INPUTS["eps_cor"],
             asymptotic: bool = False, n_override: float | None = None,
             rate_t_cap: float | None = None) -> dict:
    """One segment evaluation.  ``lam`` = leak bits per key pair (per-bit)."""
    eps_pe = eps_sec / 2.0
    eps_pa = eps_sec / 2.0
    d = d_of_bw(bw)
    HA = math.log2(d)
    n = n_override if n_override is not None else INPUTS["R_pair_s"][src] * t_cap
    n_k = (1.0 - r_pe) * n
    e_p = (1.0 - V) / 2.0
    if asymptotic:
        chi_u = chi_e(d, e_p)
    else:
        chi_u = chi_e(d, e_upper(V, r_pe, n, eps_pe)) if fk == "A" else chi_e(d, e_p)
    chi_b = chi_e(d, e_p)
    y = 1.0 - fer
    if fk == "A":
        const = 0.0 if asymptotic else (math.log2(2.0 / eps_cor)
                                        + 2.0 * math.log2(1.0 / (2.0 * eps_pa)))
        raw = y * (n_k * (HA - chi_u) - lam * n_k) - const
    else:
        dlt = 0.0 if asymptotic else delta_fk(n_k, eps_sec, eps_cor)
        raw = y * n_k * (HA - chi_b - lam - dlt)
    ell = max(0.0, raw)
    rt = rate_t_cap if rate_t_cap is not None else t_cap
    return {
        "src": src, "fk": fk, "V": V, "bw_ps": bw, "d": d, "HA": HA,
        "chi_E": chi_u if fk == "A" else chi_b, "lam_per_bit": lam,
        "leak_EC_bits": lam * n_k, "n_pairs": n, "n_k": n_k, "r_pe": r_pe,
        "fer": fer, "y": y, "asymptotic": asymptotic,
        "ell_raw_bits": raw, "ell_bits": ell, "zero_key": raw < 0.0,
        "ell_per_pair": (ell / n) if n else float("nan"),
        "ell_per_sec": (ell / rt) if rt else float("nan"),
    }


def _best_rpe(src: str, t_cap: float, fk: str, V: float, lam: float, **kw) -> dict:
    """r_PE grid search (numpy vectorized over the frozen grid)."""
    r = np.array(R_PE_GRID, dtype=float)
    d = d_of_bw(kw.get("bw", BW_BASE))
    HA = math.log2(d)
    bw = kw.get("bw", BW_BASE)
    fer = kw.get("fer", 0.0)
    eps_sec = kw.get("eps_sec", INPUTS["eps_sec"])
    eps_cor = kw.get("eps_cor", INPUTS["eps_cor"])
    eps_pe = eps_sec / 2.0
    eps_pa = eps_sec / 2.0
    n = INPUTS["R_pair_s"][src] * t_cap
    n_k = (1.0 - r) * n
    e_p = (1.0 - V) / 2.0
    y = 1.0 - fer
    if fk == "A":
        e_u = e_p + np.sqrt(math.log(1.0 / eps_pe) / (2.0 * r * n))
        chi = h2_np(e_u) + e_u * math.log2(d - 1.0)
        const = math.log2(2.0 / eps_cor) + 2.0 * math.log2(1.0 / (2.0 * eps_pa))
        raw = y * (n_k * (HA - chi) - lam * n_k) - const
    else:
        chi = np.full_like(r, chi_e(d, e_p))
        dlt = 4.0 * np.sqrt(math.log2(2.0 / eps_sec) / n_k) + 2.0 * math.log2(2.0 / eps_cor) / n_k
        raw = y * n_k * (HA - chi - lam - dlt)
    i = int(np.argmax(raw))
    return evaluate(src, t_cap, fk, V, lam, r_pe=float(r[i]), **kw)


# ---------------------------------------------------------------------------
# input cross-checks against the accepted artifacts (read-only, no raw data)
# ---------------------------------------------------------------------------
def _jload(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - malformed artifact
        return None


def check_inputs(repo: Path) -> dict:
    out: dict = {"checked": [], "mismatches": [], "absent": [], "ok": True}

    def rec(name: str, expected, actual, tol: float, rel: bool = False):
        if actual is None:
            out["absent"].append(f"{name}: artifact entry absent -> transcribed value kept, logged")
            return
        if isinstance(expected, (list, tuple)) or isinstance(actual, (list, tuple)):
            bad = any(abs(float(a) - float(b)) > tol for a, b in zip(expected, actual))
        else:
            den = max(abs(float(expected)), 1.0) if rel else 1.0
            bad = abs(float(actual) - float(expected)) > tol * den
        if bad:
            out["mismatches"].append({"item": name, "transcribed": expected,
                                      "artifact": actual, "tol": tol, "rel": rel})
            out["ok"] = False

    z3 = _jload(repo / "workspace/z3_surface/z3_20261008/z3_surface.json")
    if z3 is None:
        out["absent"].append("z3_surface.json absent -> R_pair/H_AB transcription unverified")
    else:
        idx = {(r["source"], float(r["bw_ps"])): r for r in z3}
        for s in SOURCES:
            r = idx.get((s, 200.0))
            rec(f"z3.R_pair_s[{s}]", INPUTS["R_pair_s"][s],
                None if r is None else r["R_pair_s"], 1e-9, rel=True)
            for bw in (100.0, 200.0, 400.0):
                rr = idx.get((s, bw))
                rec(f"z3.H_AB[{s}][{bw:g}]", INPUTS["H_AB_nominal_bw"][bw][s],
                    None if rr is None else rr["H_AB"], 5e-5)
        out["checked"].append("z3_surface.json")

    s2 = _jload(repo / "workspace/s_softmap/s2_20261009/s2_summary.json")
    if s2 is None:
        out["absent"].append("s2_summary.json absent -> S-2 H transcription unverified")
    else:
        for s in SOURCES:
            c = s2["sources"][s]["cells"]["200"]
            rec(f"s2.H_hard_cal[{s}]", INPUTS["H_hard_cal"][s], c["H_hard_cal"], 5e-5)
            rec(f"s2.H_soft_cal[{s}]", INPUTS["H_soft_cal"][s], c["H_soft_cal"], 5e-5)
        out["checked"].append("s2_summary.json")

    a5 = _jload(repo / "workspace/swnow_20261009/a5_20261009/a5_rates.json")
    if a5 is None:
        out["absent"].append("a5_rates.json absent -> A5 transcription unverified")
    else:
        for row in a5:
            if (row.get("law") == "dg18.5/100.0/0.014" and float(row.get("sigma", -1)) == 18.5
                    and float(row.get("mu", -1)) == 0.0 and float(row["bw"]) in (100.0, 200.0, 400.0)):
                bw = float(row["bw"])
                rec(f"a5.R_hard[{bw:g}]", INPUTS["A5_R_hard"][bw], row["R_hard"], 5e-5)
                rec(f"a5.R_soft[{bw:g}]", INPUTS["A5_R_soft"][bw], row["R_soft"], 5e-5)
                rec(f"a5.p[{bw:g}]", INPUTS["A5_p"][bw], row["p"], 5e-5)
        out["checked"].append("a5_rates.json")

    s4d = _jload(repo / "workspace/s4d_rerun/s4d_20261009/s4d_cells.json")
    if s4d is None:
        out["absent"].append("s4d_cells.json absent -> S-4d net transcription unverified")
    else:
        for s in SOURCES:
            for arm, key in (("hard", "S4D_hard_plain"), ("soft", "S4D_soft_plain")):
                c = s4d["cells"].get(f"{s}/{arm}/plain")
                if c is None:
                    out["absent"].append(f"s4d.cells[{s}/{arm}/plain] absent")
                    continue
                rec(f"s4d.{key}[{s}].L_A", INPUTS[key][s]["L_A"], c["L_A"], 0.5)
                rec(f"s4d.{key}[{s}].L_B", INPUTS[key][s]["L_B"], c["L_B"], 0.5)
                rec(f"s4d.{key}[{s}].Net_seg", INPUTS[key][s]["Net_seg"], c["Net_seg"], 0.5)
                rec(f"s4d.{key}[{s}].f_ref", INPUTS[key][s]["f_ref"], c["f_ref"], 2e-4)
        out["checked"].append("s4d_cells.json")

    blk = repo / "workspace/s4d_rerun/s4d_20261009/s4d_blocks.jsonl"
    if not blk.exists():
        out["absent"].append("s4d_blocks.jsonl absent -> level-A FER unverified")
    else:
        cnt: dict = {}
        tot: dict = {}
        for line in blk.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            cell = o["cell"]
            tot[cell] = tot.get(cell, 0) + 1
            if o.get("okA") is True:
                cnt[cell] = cnt.get(cell, 0) + 1
        for s in SOURCES:
            for arm in ("hard", "soft"):
                cell = f"{s}/{arm}"
                if tot.get(cell):
                    fails = tot[cell] - cnt.get(cell, 0)
                    rec(f"s4d.FER_la[{s}/{arm}]", INPUTS["S4D_FER_la"][s][arm],
                        (fails, tot[cell]), 0.5)
                else:
                    out["absent"].append(f"s4d_blocks[{cell}] absent")
        out["checked"].append("s4d_blocks.jsonl")

    b123 = _jload(repo / "workspace/b123_stats/b123_20261009/b123_summary.json")
    if b123 is None:
        out["absent"].append("b123_summary.json absent -> B3 transcription unverified")
    else:
        for s in ("T2-1M", "T2-1.5M", "T2-2M"):
            row = b123["b3"].get(s)
            if row is None:
                out["absent"].append(f"b123.b3[{s}] absent")
                continue
            rec(f"b3.nominal_p[{s}]", INPUTS["B3"][s]["nominal_p"], row["nominal"]["p"], 5e-5)
            rec(f"b3.cal_p[{s}]", INPUTS["B3"][s]["cal_p"], row["calibrated"]["p"], 5e-5)
            rec(f"b3.p_minus[{s}]", INPUTS["B3"][s]["p_minus"],
                row["calibrated"]["p_minus_cond"], 1e-3)
            rec(f"b3.H_e[{s}]", INPUTS["B3"][s]["H_e"], row["calibrated"]["H_e"], 5e-4)
            rec(f"b3.H_e_nominal[{s}]", INPUTS["B3"][s]["H_e_nominal"],
                row["nominal"]["H_e"], 5e-4)
        for s in ("0dB", "4dB"):
            if s not in b123["b3"]:
                out["absent"].append(f"b123.b3[{s}]: B3 table has no 0dB/4dB row "
                                     "(drop-and-log; calibrated H comes from S-2/S-4a)")
        out["checked"].append("b123_summary.json")

    s4a = _jload(repo / "workspace/s4_diag/s4a_20261009/s4a_summary.json")
    if s4a is None:
        out["absent"].append("s4a_summary.json absent -> S-4a transcription unverified")
    else:
        for s in SOURCES:
            c = s4a["sources"][s]["cells"].get("200/cal")
            if c is None:
                out["absent"].append(f"s4a.sources[{s}]['200/cal'] absent")
                continue
            rec(f"s4a.marked_rate[{s}]", INPUTS["S4A_marked_sgn"][s][0], c["marked_rate"], 1e-3)
            rec(f"s4a.sgn_rate[{s}]", INPUTS["S4A_marked_sgn"][s][1], c["sgn_rate"], 1e-3)
        out["checked"].append("s4a_summary.json")

    return out


# ---------------------------------------------------------------------------
# levers
# ---------------------------------------------------------------------------
def measured_lams(src: str) -> dict:
    n_pairs = INPUTS["S4D_blocks"][src] * INPUTS["S4D_N"]
    h = INPUTS["S4D_hard_plain"][src]
    s = INPUTS["S4D_soft_plain"][src]
    return {
        "n_pairs": n_pairs,
        "hard": (h["L_A"] + h["L_B"]) / n_pairs,
        "soft": (s["L_A"] + s["L_B"]) / n_pairs,
        "f_hard": (h["L_A"] + h["L_B"]) / n_pairs / INPUTS["H_hard_cal"][src],
        "f_soft": (s["L_A"] + s["L_B"]) / n_pairs / INPUTS["H_soft_cal"][src],
    }


def unit_states(src: str, t_cap: float, fk: str, V: float) -> list[dict]:
    """All evaluated states of one (src, T_cap, FK, V) unit."""
    lam_meas = measured_lams(src)
    lam_h, lam_s = lam_meas["hard"], lam_meas["soft"]
    f_m = lam_meas["f_hard"]
    HC_h, HC_s = INPUTS["H_hard_cal"][src], INPUTS["H_soft_cal"][src]
    HN200 = INPUTS["H_AB_nominal_bw"][200.0][src]
    st: list[dict] = []

    def add(lever, variant, **kw):
        d = {"lever": lever, "variant": variant, "in_ranking": False, "notes": ""}
        d.update(kw)
        st.append(d)

    add("B0", "measured hard/plain leak (S-4d)", lam=lam_h, bw=BW_BASE,
        in_ranking=False, notes="baseline")

    # L-f : f-proxy leak at f=1.05 / 1.00 on the S-2 measured calibrated H
    add("L-f", "f=1.05", lam=1.05 * HC_h, bw=BW_BASE,
        notes="f-proxy leak f*H_hard_cal; reconciliation-cost idealization")
    add("L-f", "f=1.00", lam=1.00 * HC_h, bw=BW_BASE, in_ranking=True,
        notes="Q1 lever")

    # L-cal : calibration is already inside the measured S-4d leak.  Reported as a
    # realized-gain counterfactual (nominal-proxy leak), NOT an available lever.
    add("L-cal", "nominal-proxy leak (Z-3 H_AB bw200), realized-gain counterfactual",
        lam=f_m * HN200, bw=BW_BASE,
        notes="absorbed: B0 leak is already measured on the calibrated chain")
    for s in ("T2-1M", "T2-1.5M", "T2-2M"):
        if s == src:
            add("L-cal-B3", "nominal-proxy leak (B3 H_e nominal)", lam=f_m * INPUTS["B3"][s]["H_e_nominal"],
                bw=BW_BASE, notes="B3-provenance cross-variant (T2 sources only)")

    # L-soft : void SS2 definition — same f, H(A|B_bin)->H(A|B_fine)
    add("L-soft", "same-f, H_soft_cal (S-2 measured)", lam=f_m * HC_s, bw=BW_BASE,
        in_ranking=True, notes="void SS2 'same f' form")
    add("L-soft-meas", "measured soft/plain arm leak (S-4d)", lam=lam_s, bw=BW_BASE,
        notes="not ranked: S-4d soft level-A rate is not matched to the soft arm "
              "(S4D_RESULT SS3 f_ref caveat)")
    add("L-cal+soft", "= L-soft (calibration already applied)", lam=f_m * HC_s,
        bw=BW_BASE, notes="non-independent per void SS2; not ranked")

    # L-bw : candidates bw=200 (measured) + bw=100/400 (A5 model, void SS2)
    cand = [(BW_BASE, HC_h, lam_h, "measured"),
            (100.0, INPUTS["A5_R_hard"][100.0], f_m * INPUTS["A5_R_hard"][100.0], "A5-model"),
            (400.0, INPUTS["A5_R_hard"][400.0], f_m * INPUTS["A5_R_hard"][400.0], "A5-model")]
    best = None
    for bw, _h, lam, tag in cand:
        e = evaluate(src, t_cap, fk, V, lam, bw=bw, r_pe=R_PE_B0)
        if best is None or e["ell_raw_bits"] > best[0]["ell_raw_bits"]:
            best = (e, bw, lam, tag)
    add("L-bw", f"best of bw={{100,200,400}} -> bw={best[1]:g} ({best[3]})",
        lam=best[2], bw=best[1], in_ranking=True,
        notes=f"ell={best[0]['ell_bits']:.1f}; candidates 200 measured / 100,400 A5 model")
    best_a5 = None
    for bw in (100.0, 200.0, 400.0):
        lam = f_m * INPUTS["A5_R_hard"][bw]
        e = evaluate(src, t_cap, fk, V, lam, bw=bw, r_pe=R_PE_B0)
        if best_a5 is None or e["ell_raw_bits"] > best_a5[0]["ell_raw_bits"]:
            best_a5 = (e, bw, lam)
    add("L-bw", f"all-A5 model variant -> bw={best_a5[1]:g}", lam=best_a5[2], bw=best_a5[1],
        notes=f"auxiliary (all three bws from A5): ell={best_a5[0]['ell_bits']:.1f}")

    # L-T : T_cap -> 10 s (ranked) and asymptotic reference (finite-size terms off)
    add("L-T", "T_cap=10 s", lam=lam_h, bw=BW_BASE, t_cap_override=10.0, in_ranking=True,
        notes="same lam (per-bit leak is length-independent)")
    add("L-T", "asymptotic ref (finite-size terms removed, n_k at T_cap)", lam=lam_h,
        bw=BW_BASE, asymptotic=True,
        notes="reference only, not ranked (n_k kept at the cell T_cap)")

    # L-V : V grid; 0.99 is the upward idealization (ranked)
    for vv in V_LEVER_GRID:
        add("L-V", f"V={vv:.2f}", lam=lam_h, bw=BW_BASE, V_override=vv,
            in_ranking=(vv == 0.99), notes="ASSUMED parameter (value of information only)")

    # L-PE : best r_PE over the frozen grid (numpy grid search)
    add("L-PE", f"best r_PE in {R_PE_GRID}", lam=lam_h, bw=BW_BASE, rpe_search=True,
        in_ranking=True, notes="grid search on ell")

    # L-eps : eps -> 1e-6 (sensitivity)
    add("L-eps", "eps=1e-6", lam=lam_h, bw=BW_BASE, eps_override=EPS_LEVER,
        in_ranking=True, notes="sensitivity only")

    # L-FER : downside sensitivity
    for fv in FER_LEVER:
        add("L-FER", f"FER={fv:.2f}", lam=lam_h, bw=BW_BASE, fer_override=fv,
            in_ranking=(fv == FER_LEVER[0]),
            notes="downside sensitivity" + (" (ranked representative)" if fv == FER_LEVER[0] else ""))

    # measured-gate report (level-A FER from S-4d; not a lever)
    for arm in ("hard", "soft"):
        f_la = INPUTS["S4D_FER_la"][src][arm][0] / INPUTS["S4D_FER_la"][src][arm][1]
        lam = lam_s if arm == "soft" else lam_h
        add("measured-gate", f"y=1-FER_LA({arm})={1 - f_la:.4f}", lam=lam, bw=BW_BASE,
            fer_override=f_la,
            notes="reality-check column (S-4d level-A FER), not ranked")

    return st


def unit_eval(src: str, t_cap: float, fk: str, V: float, s: dict) -> dict:
    kw = {"bw": s.get("bw", BW_BASE), "r_pe": R_PE_B0, "fer": s.get("fer_override", 0.0)}
    if "eps_override" in s:
        kw["eps_sec"] = s["eps_override"]
        kw["eps_cor"] = s["eps_override"]
    if "fer_override" in s:
        kw["fer"] = s["fer_override"]
    vv = s.get("V_override", V)
    tc = s.get("t_cap_override", t_cap)
    asym = bool(s.get("asymptotic", False))
    if s.get("rpe_search"):
        e = _best_rpe(src, tc, fk, vv, s["lam"], **{k: v for k, v in kw.items() if k != "r_pe"})
    else:
        e = evaluate(src, tc, fk, vv, s["lam"], asymptotic=asym, rate_t_cap=tc, **kw)
    e["lever"] = s["lever"]
    e["variant"] = s["variant"]
    e["in_ranking"] = bool(s.get("in_ranking", False))
    e["notes"] = s.get("notes", "")
    e["t_cap_s"] = t_cap
    return e


def leave_one_out(src: str, t_cap: float, fk: str, V: float, lam_meas: dict) -> list[dict]:
    """All levers ideal, then revert one lever's own parameter back to B0.

    Ideal set: L-f->1.00, L-soft->same-f H_fine, L-V->0.99, L-PE->best, L-eps->1e-6.
    L-bw and L-T are excluded from the LOO set (bw is entangled with the H-model
    provenance, and T_cap defines the segment/accounting unit); stated in the log.
    """
    HC_h, HC_s = INPUTS["H_hard_cal"][src], INPUTS["H_soft_cal"][src]
    f_m = lam_meas["f_hard"]
    rows = []

    def ev(f_fac, h_fine, v, rpe_best, eps):
        lam = f_fac * (HC_s if h_fine else HC_h)
        kw = {"bw": BW_BASE, "r_pe": rpe_best, "fer": 0.0,
              "eps_sec": eps, "eps_cor": eps}
        return evaluate(src, t_cap, fk, v, lam, **kw)

    base = ev(1.00, True, 0.99, 0.10, EPS_LEVER)
    # r_PE best under the ideal lam
    best = None
    for rp in R_PE_GRID:
        e = ev(1.00, True, 0.99, rp, EPS_LEVER)
        if best is None or e["ell_raw_bits"] > best[0]["ell_raw_bits"]:
            best = (e, rp)
    ideal = best[0]
    rows.append({"lever": "ALL-IDEAL", "variant": f"r_PE={best[1]:g}", "ell": ideal,
                 "delta": ideal["ell_bits"] - base["ell_bits"], "in_ranking": False,
                 "notes": "all idealizations together (L-f1.00, soft same-f, V=.99, best r_PE, eps=1e-6, T at cell)"})
    reverts = [
        ("LOO-L-f", "f back to measured f_ref", ev(f_m / 1.0, True, 0.99, best[1], EPS_LEVER)),
        ("LOO-L-soft", "soft back to hard H", ev(1.00, False, 0.99, best[1], EPS_LEVER)),
        ("LOO-L-V", "V back to cell baseline", ev(1.00, True, V, best[1], EPS_LEVER)),
        ("LOO-L-PE", "r_PE back to 0.10", ev(1.00, True, 0.99, R_PE_B0, EPS_LEVER)),
        ("LOO-L-eps", "eps back to 1e-10", ev(1.00, True, 0.99, best[1], INPUTS["eps_sec"])),
    ]
    for name, variant, e in reverts:
        e2 = dict(e)
        e2["lever"] = name
        e2["variant"] = variant
        rows.append({"lever": name, "variant": variant, "ell": e2,
                     "delta": inner_delta(ideal, e2), "in_ranking": False,
                     "notes": "leave-one-out drop from the all-ideal state"})
    return rows


def inner_delta(a: dict, b: dict) -> float:
    return b["ell_bits"] - a["ell_bits"]


# ---------------------------------------------------------------------------
# ranking / Q1-Q4
# ---------------------------------------------------------------------------
def rank_levers(rows: list[dict]) -> dict:
    """rows: lever-summary dicts of one unit (lever, variant, ell, delta, ratio)."""
    cand = [r for r in rows if r["lever"] in RANKED_LEVERS and r["in_ranking"]]
    cand.sort(key=lambda r: (-r["delta_over_ellB0"], r["lever"]))
    rank: dict = {}
    for i, r in enumerate(cand):
        if i > 0 and abs(r["delta_over_ellB0"] - cand[i - 1]["delta_over_ellB0"]) < 1e-12:
            rank[r["lever"]] = rank[cand[i - 1]["lever"]]
        else:
            rank[r["lever"]] = i + 1
    return rank


def q4_bw_optima(src: str, t_cap: float, fk: str, V: float) -> dict:
    """L-bw candidate table: argmax ell vs argmin lam/H_A."""
    lam_meas = measured_lams(src)
    f_m = lam_meas["f_hard"]
    cands = [("bw200-measured", BW_BASE, INPUTS["H_hard_cal"][src], lam_meas["hard"]),
             ("bw100-A5", 100.0, INPUTS["A5_R_hard"][100.0], f_m * INPUTS["A5_R_hard"][100.0]),
             ("bw400-A5", 400.0, INPUTS["A5_R_hard"][400.0], f_m * INPUTS["A5_R_hard"][400.0])]
    tab = []
    for tag, bw, _H, lam in cands:
        e = evaluate(src, t_cap, fk, V, lam, bw=bw, r_pe=R_PE_B0)
        tab.append({"cand": tag, "bw_ps": bw, "HA": e["HA"], "lam": lam,
                    "cost_ratio": lam / e["HA"], "ell_bits": e["ell_bits"]})
    argmax_ell = max(tab, key=lambda r: r["ell_bits"])["cand"]
    argmin_cost = min(tab, key=lambda r: r["cost_ratio"])["cand"]
    return {"table": tab, "argmax_ell": argmax_ell, "argmin_cost": argmin_cost,
            "agree": argmax_ell == argmin_cost}


# ---------------------------------------------------------------------------
# self-test (limits / large-n / asymptotic / monotonicity)
# ---------------------------------------------------------------------------
def self_test() -> None:
    src, t_cap, fk, V = "T2-1M", 3.0, "A", 0.95
    lam = 0.45
    # T-1 limit: V=1, n->inf, f->1 (lam->H?), r_PE fixed -> ell/n_k -> H_A - lam
    n_big = 1e20
    for fkm in FK_MODES:
        e = evaluate(src, t_cap, fkm, 1.0, lam, n_override=n_big, r_pe=R_PE_B0)
        got = e["ell_bits"] / e["n_k"]
        assert abs(got - (e["HA"] - lam)) < 1e-6, (fkm, got, e["HA"] - lam)
    # asymptotic flag reproduces the same limit at finite n
    for fkm in FK_MODES:
        e = evaluate(src, t_cap, fkm, V, lam, asymptotic=True)
        n_k = e["n_k"]
        expect = n_k * (e["HA"] - chi_e(e["d"], (1 - V) / 2.0) - lam)
        assert abs(e["ell_bits"] - expect) < 1e-9 * max(1.0, abs(expect)), (fkm, e["ell_bits"], expect)
    # T-2 monotonicity
    a = evaluate(src, t_cap, fk, V, 0.30)["ell_bits"]
    b = evaluate(src, t_cap, fk, V, 0.50)["ell_bits"]
    assert a > b, "ell must decrease in lam"
    c = evaluate(src, t_cap, "B", V, 0.45, fer=0.10)["ell_bits"]
    d = evaluate(src, t_cap, "B", V, 0.45, fer=0.0)["ell_bits"]
    assert c < d, "ell must decrease in FER"
    e1 = evaluate(src, t_cap, fk, 0.90, lam)["ell_bits"]
    e2 = evaluate(src, t_cap, fk, 0.99, lam)["ell_bits"]
    assert e2 > e1, "ell must increase in V"
    f1 = evaluate(src, t_cap, fk, V, lam, n_override=1e6)["ell_bits"]
    f2 = evaluate(src, t_cap, fk, V, lam, n_override=1e9)["ell_bits"]
    assert f2 > f1, "ell must increase in n"
    # T-3 finite-size terms -> 0 (FK-B penalty)
    assert delta_fk(1e19, INPUTS["eps_sec"], INPUTS["eps_cor"]) < 1e-8
    # T-4 clamp / zero_key
    z = evaluate(src, t_cap, "A", V, 100.0)
    assert z["zero_key"] and z["ell_bits"] == 0.0 and z["ell_raw_bits"] < 0.0
    # T-5 n_k convention and d = T_f/bw
    e = evaluate(src, t_cap, fk, V, lam, r_pe=0.25)
    assert abs(e["n_k"] - 0.75 * e["n_pairs"]) < 1e-9
    assert abs(d_of_bw(100.0) - 2048.0) < 1e-9 and abs(d_of_bw(400.0) - 512.0) < 1e-9
    # T-6 r_PE search returns a grid member
    e = _best_rpe(src, t_cap, fk, V, lam)
    assert e["r_pe"] in R_PE_GRID
    print("lever2 self-test OK (limits T-1..T-6)")


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def run(repo: Path, out_root: Path) -> dict:
    t0 = time.perf_counter()
    checks = check_inputs(repo)
    if not checks["ok"]:
        raise SystemExit("INPUT transcription mismatch vs accepted artifacts: "
                         + json.dumps(checks["mismatches"], indent=1))

    cells: list[dict] = []
    lever_rows: list[dict] = []
    units: list[dict] = []
    b0_table: list[dict] = []
    q1 = {"rank1": 0, "rank_ge3": 0, "n": 0, "rows": []}
    q2 = {"combos": [], "sensitive": 0, "n": 0}
    q3 = {"zero_key_units": 0, "n": 0, "by_tcap": {}}
    q4 = {"combos": [], "agree": 0, "n": 0}

    for src in SOURCES:
        lam_meas = measured_lams(src)
        for t_cap in T_CAP_GRID:
            for fk in FK_MODES:
                for V in V_GRID:
                    unit_id = f"{src}|T{t_cap:g}|FK{fk}|V{V:.2f}"
                    states = unit_states(src, t_cap, fk, V)
                    evals = [unit_eval(src, t_cap, fk, V, s) for s in states]
                    b0 = evals[0]
                    assert b0["lever"] == "B0"
                    for e in evals:
                        cells.append(row_of_cell(unit_id, e, b0))
                    b0_table.append({
                        "unit": unit_id, "src": src, "t_cap_s": t_cap, "fk": fk, "V": V,
                        "ell_bits": round(b0["ell_bits"], 1),
                        "ell_raw_bits": round(b0["ell_raw_bits"], 1),
                        "lam_per_bit": round(b0["lam_per_bit"], 6),
                        "zero_key": b0["zero_key"],
                        "ell_per_pair": b0["ell_per_pair"], "ell_per_sec": b0["ell_per_sec"],
                    })
                    q3["n"] += 1
                    q3["by_tcap"].setdefault(f"{t_cap:g}", [0, 0])
                    q3["by_tcap"][f"{t_cap:g}"][1] += 1
                    if b0["zero_key"]:
                        q3["zero_key_units"] += 1
                        q3["by_tcap"][f"{t_cap:g}"][0] += 1

                    lrows = []
                    for e in evals:
                        delta = e["ell_bits"] - b0["ell_bits"]
                        ratio = delta / max(b0["ell_bits"], 1.0)
                        r = {
                            "unit": unit_id, "src": src, "t_cap_s": t_cap, "fk": fk, "V": V,
                            "lever": e["lever"], "variant": e["variant"],
                            "lam_per_bit": e["lam_per_bit"], "bw_ps": e["bw_ps"],
                            "ell_bits": e["ell_bits"], "delta_ell_bits": delta,
                            "delta_over_ellB0": ratio, "in_ranking": e["in_ranking"],
                            "notes": e["notes"],
                        }
                        lrows.append(r)
                    rank = rank_levers(lrows)
                    for r in lrows:
                        r["rank"] = rank.get(r["lever"]) if r["lever"] in RANKED_LEVERS else ""
                    lever_rows.extend(lrows)

                    loo = leave_one_out(src, t_cap, fk, V, lam_meas)
                    for r in loo:
                        lever_rows.append({
                            "unit": unit_id, "src": src, "t_cap_s": t_cap, "fk": fk, "V": V,
                            "lever": r["lever"], "variant": r["variant"],
                            "lam_per_bit": r["ell"]["lam_per_bit"],
                            "bw_ps": r["ell"]["bw_ps"],
                            "ell_bits": r["ell"]["ell_bits"],
                            "delta_ell_bits": r["delta"],
                            "delta_over_ellB0": r["delta"] / max(b0["ell_bits"], 1.0),
                            "rank": "", "in_ranking": False,
                            "notes": "LOO: delta is vs the ALL-IDEAL state, not vs B0; "
                                     + r["notes"],
                        })

                    top = sorted([(r["delta_over_ellB0"], r["lever"]) for r in lrows
                                  if r["lever"] in RANKED_LEVERS and r["in_ranking"]],
                                 key=lambda x: (-x[0], x[1]))
                    units.append({"unit": unit_id, "rank1": top[0][1] if top else None,
                                  "lf_rank": rank.get("L-f", ""), "rank_of": rank})
                    q1["n"] += 1
                    r_lf = rank.get("L-f")
                    if r_lf == 1:
                        q1["rank1"] += 1
                    if isinstance(r_lf, int) and r_lf >= 3:
                        q1["rank_ge3"] += 1
                    q1["rows"].append({"unit": unit_id, "rank_L-f": r_lf,
                                       "rank1": top[0][1] if top else None})

                    if (src, t_cap, fk) not in [(c["src"], c["t_cap_s"], c["fk"]) for c in q2["combos"]]:
                        q2["combos"].append({"src": src, "t_cap_s": t_cap, "fk": fk,
                                             "rank1_by_V": {}})
                    combo = [c for c in q2["combos"]
                             if (c["src"], c["t_cap_s"], c["fk"]) == (src, t_cap, fk)][0]
                    combo["rank1_by_V"][f"{V:.2f}"] = top[0][1] if top else None

                    q4c = q4_bw_optima(src, t_cap, fk, V)
                    q4["n"] += 1
                    if q4c["agree"]:
                        q4["agree"] += 1
                    q4["combos"].append({"unit": unit_id, **q4c})

    for c in q2["combos"]:
        vals = set(c["rank1_by_V"].values())
        c["sensitive"] = len(vals) > 1
        q2["n"] += 1
        if c["sensitive"]:
            q2["sensitive"] += 1

    # model-vs-real check (proxy vs S-4d accepted net), informational
    mvr = []
    for src in SOURCES:
        lp = measured_lams(src)
        b0 = evaluate(src, 3.0, "A", 0.95, lp["hard"])
        b0b = evaluate(src, 3.0, "B", 0.95, lp["hard"])
        real = INPUTS["S4D_hard_plain"][src]["Net_seg"]
        mvr.append({
            "src": src, "n_pairs_S4d": lp["n_pairs"],
            "lam_hard": lp["hard"], "lam_soft": lp["soft"],
            "f_ref_hard_transcribed": INPUTS["S4D_hard_plain"][src]["f_ref"],
            "f_recomputed": lp["f_hard"],
            "Net_seg_soft_plain": INPUTS["S4D_soft_plain"][src]["Net_seg"],
            "ell_B0_FK-A_3s_V.95": b0["ell_bits"], "ell_B0_FK-B_3s_V.95": b0b["ell_bits"],
            "ratio_FK-A_over_real": b0["ell_bits"] / real,
            "FER_LA_hard": INPUTS["S4D_FER_la"][src]["hard"][0] / INPUTS["S4D_FER_la"][src]["hard"][1],
            "FER_LA_soft": INPUTS["S4D_FER_la"][src]["soft"][0] / INPUTS["S4D_FER_la"][src]["soft"][1],
            "FER_full_hard": INPUTS["S4D_FER_full"][src]["hard"],
            "FER_full_soft": INPUTS["S4D_FER_full"][src]["soft"],
        })

    # lever aggregate ranking (mean ratio over the 60 units)
    agg: dict = {}
    for r in lever_rows:
        if r["lever"] not in RANKED_LEVERS or not r["in_ranking"]:
            continue
        a = agg.setdefault(r["lever"], {"n": 0, "sum_ratio": 0.0, "rank1": 0, "ranks": []})
        a["n"] += 1
        a["sum_ratio"] += r["delta_over_ellB0"]
        if r["rank"] == 1:
            a["rank1"] += 1
        a["ranks"].append(r["rank"])
    for k, a in agg.items():
        a["mean_ratio"] = a["sum_ratio"] / a["n"]
        a["mean_rank"] = sum(a["ranks"]) / a["n"]
        del a["sum_ratio"]
    order = sorted(agg.items(), key=lambda kv: -kv[1]["mean_ratio"])

    # Q verdicts (void SS3 rules)
    n = q1["n"]
    if q1["rank1"] >= (2.0 / 3.0) * n:
        v1 = "f dominant"
    elif q1["rank_ge3"] >= (2.0 / 3.0) * n:
        v1 = "f not dominant"
    else:
        v1 = "mixed"
    v2 = ("V is a high-value unknown (rank-1 lever changes with V in >=1/3 of "
          "source x T_cap x FK combos); recommend a conjugate-basis (Franson) "
          "visibility measurement entry in C4_PLAN.md"
          if q2["sensitive"] >= q2["n"] / 3.0 else
          "V-sensitivity below the 1/3 threshold: no visibility-measurement recommendation")
    zero3 = q3["by_tcap"].get("3", [0, 0])
    v3 = (f"zero_key units = {q3['zero_key_units']}/{q3['n']}"
          + ("" if zero3[0] == 0 else
             f"; at T_cap=3 s {zero3[0]}/{zero3[1]} units are zero -> levers are a "
             "necessary condition, not an improvement item"))
    v4 = ("framing optimum depends on the target: argmax ell != argmin lam/H_A in "
          f"{q4['n'] - q4['agree']}/{q4['n']} units -> challenge direction C survives"
          if q4["agree"] < q4["n"] else
          "framing optimum agrees between the two targets in all units -> direction C is downgraded")

    summary = {
        "packet": "LEVER-2 adapted one-shot (void LEVER-BUDGET-20261009 SS1/SS2 reused; "
                  "S-4d measured leak replaces the f-proxy leak)",
        "track": "EXPLORE",
        "branch_note": "formal-ir-v72p1-addendum-clean (no switch, no commit, no push)",
        "inputs": INPUTS,
        "input_crosschecks": checks,
        "excluded": [
            "T0-500K / T0-1M: not in the frozen LEVER-2 source set (and absent from the "
            "Z-3 surface) -> excluded",
            "10dB: present in Z-3/S-2/S-4a but not in the LEVER-2 source list -> excluded "
            "(drop-and-log, no invented numbers)",
            "B123 B3 has no 0dB/4dB row -> calibrated H for those sources comes from the "
            "S-2 measured table (cross-checked with S-4a marked/sgn rates), not invented",
            "Z-3 H_AB at bw=100/400 carry status 'UNMEASURED (extrapolation or "
            "wide-support regime)' -> transcribed for provenance only; the L-bw lever uses "
            "the A5 model for bw != 200 per void SS2",
            "L-cal: calibration is already inside the measured S-4d baseline -> reported as "
            "a realized-gain counterfactual, not ranked as an available lever",
            "L-cal+soft: not independent (identical to L-soft here) -> single report, not ranked",
            "L-soft-meas: the S-4d soft level-A rate is not matched to the soft arm "
            "(S4D_RESULT SS3 f_ref caveat) -> reported, not ranked",
            "L-T->inf: reference only (finite-size terms removed, n_k kept at T_cap), not ranked",
            "raw data: not read; decoding: not run (EXPLORE, proxy arithmetic only)",
        ],
        "units": units,
        "Q1_f_dominant": {"verdict": v1, "rank1_count": q1["rank1"],
                          "rank_ge3_count": q1["rank_ge3"], "n_units": n,
                          "definition": "L-f(f->1.00) rank 1 in >=2/3 -> dominant; rank >=3 in "
                                        ">=2/3 -> not dominant; else mixed",
                          "rows": q1["rows"]},
        "Q2_V_sensitivity": {"verdict": v2, "sensitive_combos": q2["sensitive"],
                             "n_combos": q2["n"], "threshold": ">=1/3",
                             "combos": q2["combos"]},
        "Q3_zero_key": {"verdict": v3, "zero_key_units": q3["zero_key_units"],
                        "n_units": q3["n"], "by_tcap": q3["by_tcap"]},
        "Q4_framing_optimum": {"verdict": v4, "agree": q4["agree"], "n_units": q4["n"],
                               "rule": "compare argmax ell (L-bw) with argmin lam/H_A "
                                       "(f*H(A|B)/H_A)", "combos": q4["combos"]},
        "B0_table_key": "full B0 table in lb2_cells.csv (row addressing: lever=B0)",
        "B0_table_compact": b0_table,
        "lever_aggregate": {k: v for k, v in order},
        "S4D_transcribed": {
            "hard_plain": INPUTS["S4D_hard_plain"], "soft_plain": INPUTS["S4D_soft_plain"],
            "FER_LA": INPUTS["S4D_FER_la"], "FER_full": INPUTS["S4D_FER_full"],
            "blocks": INPUTS["S4D_blocks"], "N": INPUTS["S4D_N"],
            "derived_lams": {s: {k: v for k, v in measured_lams(s).items()} for s in SOURCES},
        },
        "model_vs_real_check": mvr,
        "counts": {"cells_rows": len(cells), "lever_rows": len(lever_rows)},
        "wall_s": round(time.perf_counter() - t0, 3),
    }
    return {"summary": summary, "cells": cells, "levers": lever_rows}


CELL_COLS = ["row_id", "unit", "src", "t_cap_s", "fk", "V", "state", "lever", "variant",
             "bw_ps", "d", "HA", "chi_E", "lam_per_bit", "leak_EC_bits", "n_pairs", "n_k",
             "r_pe", "fer", "y", "asymptotic", "ell_raw_bits", "ell_bits", "zero_key",
             "ell_per_pair", "ell_per_sec", "in_ranking", "notes"]
LEVER_COLS = ["unit", "src", "t_cap_s", "fk", "V", "lever", "variant", "lam_per_bit",
              "bw_ps", "ell_bits", "delta_ell_bits", "delta_over_ellB0", "rank",
              "in_ranking", "notes"]


def row_of_cell(unit_id: str, e: dict, b0: dict) -> dict:
    d = dict(e)
    d["row_id"] = f"{unit_id}|{e['lever']}|{e['variant']}"
    d["unit"] = unit_id
    d["state"] = e["variant"]
    return {k: d[k] for k in CELL_COLS if k in d}


def write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.10g}" if isinstance(v, float) else v)
                        for k, v in r.items()})


def main() -> None:
    ap = argparse.ArgumentParser(description="LEVER-2 measured-leak lever arithmetic (EXPLORE)")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output_root:
        raise SystemExit("lever2 requires --output-root")
    repo = Path(args.repo_root)
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    res = run(repo, root)
    root.mkdir(parents=True, exist_ok=True)
    write_csv(root / "lb2_cells.csv", CELL_COLS, res["cells"])
    write_csv(root / "lb2_levers.csv", LEVER_COLS, res["levers"])
    (root / "lb2_summary.json").write_text(json.dumps(res["summary"], indent=1),
                                           encoding="utf-8")
    s = res["summary"]
    print(f"lever2 done wall={s['wall_s']}s -> {root}")
    print(f"  cells={s['counts']['cells_rows']} lever_rows={s['counts']['lever_rows']}")
    print(f"  Q1={s['Q1_f_dominant']['verdict']} Q2={s['Q2_V_sensitivity']['verdict'][:60]}")
    print(f"  Q3={s['Q3_zero_key']['verdict'][:60]}")
    print(f"  Q4={s['Q4_framing_optimum']['verdict'][:60]}")
    print("  lever ranking (mean delta/max(ell_B0,1)): "
          + ", ".join(f"{k}={v['mean_ratio']:+.4f}" for k, v in s["lever_aggregate"].items()))


if __name__ == "__main__":
    main()
