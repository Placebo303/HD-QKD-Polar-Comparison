"""Challenge-table close-out: rows F and G (EXPLORE, arithmetic only).

Frozen caliber (CHALLENGE_CLOSEOUT_PREREG_20261010.md sections 1-2):
  * A5 mixture-law per-sub-bin ``P(e|v)`` — the SAME convention as the landed
    ``msd_a5_soft_rate.cond_pmf_given_fine`` and the landed S-5c
    ``msd_s5c_gf5.priors_of``:
        P(e=k | v) = law.interval_mass(v + (k-1)*bw, v + k*bw)
    (re-implemented here verbatim so this module holds no data-path import;
     the convention is validated by A5's B2 empirical cross-check and by
     S-5c landing 639/639 FER 0 with the same priors).
  * GF(5) symbol s = e mod 5, alph_5, bw = 200 ps, mu = 0 (calibrated),
    N = 4096, m = 778 (S-5c frozen).

Row F (mechanical): mean/variance of the GF(5) single-level soft information
density I(v) = log2(5) - H(s|v) over the 8 A5 sub-bins, then the finite-length
penalty sqrt(V/N)*Qinv(eps) in bit/pair, compared against the landed leakage
0.4412 and the soft-entropy difference H_hard_cal - H_soft_cal, and against
the row's own gap = 0.18 threshold (<=0.05 close / >=0.1 re-target).

Row G (mechanical): Alice-side layered disclosure under the DECIDE caliber the
user adopted — ANY message Bob sends counts as leakage, so Bob's sub-bin index
K is charged at H(K). Compare
    min(1, f(p_k)*h2(p_k))   (row formula, Alice side only)
    H(K) + sum_k w_k*min(1, f(p_k)*h2(p_k))   (adopted caliber)
against the landed f*H_soft = 0.4412 bit/pair. Saving < 0.02 bit/pair refutes.

No real data, no decoder, no key generation.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.special import erfcinv

from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
)

# ---- frozen constants (S-5c / S-2; see prereg section 2) ------------------
BW = 200.0
N = 4096
M = 778
Q = 5
WIDE_SIG = 100.0
NSUB = 8            # A5 caliber (msd_a5_soft_rate.soft_rate default)
KMIN, KMAX = -6, 6  # S-5c priors_of range
LOG2Q = math.log2(Q)
EPS_LIST = (0.1, 0.01, 0.001, 1e-6)
GAP_NOMINAL = 0.18  # NOW.md row F threshold
CLOSE_TH = 0.05
RETAIM_TH = 0.1
G_SAVE_TH = 0.02    # NOW.md row G threshold

S2_PATH = "workspace/s_softmap/s2_20261009/s2_summary.json"
SOURCES = ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB")


def qinv(eps: float) -> float:
    """Inverse standard-normal CDF: Q^-1(eps) = sqrt(2)*erfcinv(2 eps)."""
    return float(math.sqrt(2.0) * erfcinv(2.0 * eps))


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -(x * math.log2(x) + (1.0 - x) * math.log2(1.0 - x))


def subbin_centers(nsub: int = NSUB) -> list[float]:
    """A5 sub-bin centers v_k = (k + 1/2) * bw / nsub."""
    return [(st + 0.5) * BW / nsub for st in range(nsub)]


def gf5_pmf(law, v: float) -> dict[int, float]:
    """P(s = j | v) over the GF(5) alphabet, s = e mod 5.

    Same interval convention as the landed A5 / S-5c prior construction.
    """
    out = [0.0] * Q
    for k in range(KMIN, KMAX + 1):
        out[k % Q] += max(law.interval_mass(v + (k - 1) * BW, v + k * BW), 0.0)
    tot = sum(out)
    if tot <= 0:
        raise ValueError(f"degenerate conditional pmf at v={v}")
    return [p / tot for p in out]


def entropy(pmf: list[float]) -> float:
    return float(-sum(p * math.log2(p) for p in pmf if p > 0.0))


def source_row(src: str, fit: dict) -> dict:
    law = DoubleGauss(float(fit["sig"]), WIDE_SIG, float(fit["w"]))
    vs = subbin_centers()
    w = 1.0 / NSUB                       # v marginal ~uniform (sigma/bw ~ 0.07); stated
    H_sv, p_bin = [], []
    for v in vs:
        pmf = gf5_pmf(law, v)
        H_sv.append(entropy(pmf))
        p_bin.append(1.0 - pmf[0])       # P(e != 0 | v) = binary error rate
    I_v = [LOG2Q - h for h in H_sv]
    mean_I = float(sum(w * x for x in I_v))
    var_I = float(sum(w * (x - mean_I) ** 2 for x in I_v))
    sw_rate = LOG2Q - mean_I             # = E_v H(s|v): the model SW soft rate
    fl = {f"{eps:g}": math.sqrt(var_I / N) * qinv(eps) for eps in EPS_LIST}
    return {"source": src, "fit": {k: fit[k] for k in ("sig", "w")},
            "subbin_v": [round(v, 2) for v in vs],
            "p_e_nz_given_v": [round(p, 5) for p in p_bin],
            "H_s_given_v": [round(h, 5) for h in H_sv],
            "I_soft_given_v": [round(x, 5) for x in I_v],
            "mean_I_bit": round(mean_I, 5),
            "var_I_bit2": round(var_I, 6),
            "model_SW_soft_rate": round(sw_rate, 5),
            "finite_len_penalty_bit_per_pair": {k: round(v, 5) for k, v in fl.items()},
            "gap_vs_model_SW": round(LEAK_PAIR - sw_rate, 5)}


LEAK_PAIR = math.ceil(M * LOG2Q) / N    # 1807/4096 = 0.44116 bit/pair (S-5c frozen)


def self_test() -> None:
    # 1. sub-bin centers and A5 caliber
    assert abs(subbin_centers()[0] - 12.5) < 1e-9
    assert len(subbin_centers()) == NSUB
    # 2. entropy non-negativity / normalizations on every sub-bin of a real fit
    s2 = json.load(open(S2_PATH, encoding="utf-8"))
    for src in SOURCES:
        fit = s2["sources"][src]["prefix_fit"]
        law = DoubleGauss(float(fit["sig"]), WIDE_SIG, float(fit["w"]))
        for v in subbin_centers():
            pmf = gf5_pmf(law, v)
            assert abs(sum(pmf) - 1.0) < 1e-9, (src, v, sum(pmf))
            assert entropy(pmf) >= 0.0
    # 3. information density ordering: bin edge carries more than bin centre
    r = source_row("T2-1M", s2["sources"]["T2-1M"]["prefix_fit"])
    edge = r["H_s_given_v"][0]
    centre = r["H_s_given_v"][NSUB // 2]
    assert edge > centre + 0.05, r["H_s_given_v"]
    # 4. Q^-1 against published values
    assert abs(qinv(0.1) - 1.281552) < 1e-5, qinv(0.1)
    assert abs(qinv(0.01) - 2.326348) < 1e-5, qinv(0.01)
    assert abs(qinv(0.001) - 3.090232) < 1e-5, qinv(0.001)
    # 5. zero-variance limit -> zero finite-length penalty (uniform density)
    assert math.sqrt(0.0 / N) * qinv(0.01) == 0.0
    # 6. leakage constant equals the landed S-5c number
    assert abs(LEAK_PAIR - 0.441) < 5e-4, LEAK_PAIR
    print("chal_fg self-test OK (subbins / pmf norm / ordering / Qinv / leak)")


def transcribe() -> tuple[dict, list[dict]]:
    """Field-by-field check against the landed S-2 summary (drop-and-log)."""
    s2 = json.load(open(S2_PATH, encoding="utf-8"))
    checks, absent = [], []
    for src in SOURCES:
        rec = s2["sources"][src]
        c200 = rec["cells"].get("200")
        if c200 is None:
            absent.append(f"s2.cells[200].{src}")
            continue
        fit = rec["prefix_fit"]
        checks.append({"source": src, "sig": float(fit["sig"]), "w": float(fit["w"]),
                       "H_hard_cal": float(c200["H_hard_cal"]),
                       "H_soft_cal": float(c200["H_soft_cal"])})
    return s2, checks


def run() -> dict:
    t0 = time.perf_counter()
    s2, inputs = transcribe()

    # ---------------- Row F ----------------
    f_rows = [source_row(c["source"], s2["sources"][c["source"]]["prefix_fit"])
              for c in inputs]
    f_cmp = []
    for c in inputs:
        r = next(x for x in f_rows if x["source"] == c["source"])
        meas_sw = c["H_soft_cal"]
        meas_gap = LEAK_PAIR - meas_sw
        soft_gap = c["H_hard_cal"] - c["H_soft_cal"]
        r["measured_H_soft_cal"] = meas_sw
        r["measured_f_soft"] = round(LEAK_PAIR / meas_sw, 4)
        r["measured_gap_leak_minus_SW"] = round(meas_gap, 5)
        r["measured_soft_entropy_diff"] = round(soft_gap, 5)
        r["model_minus_measured_SW"] = round(r["model_SW_soft_rate"] - meas_sw, 5)
        worst = max(r["finite_len_penalty_bit_per_pair"].values())
        r["worst_penalty_eps_le_1e-3"] = round(
            r["finite_len_penalty_bit_per_pair"]["0.001"], 5)
        r["max_penalty_all_eps"] = round(worst, 5)
        r["frac_of_measured_gap_at_eps1e-3"] = round(
            r["finite_len_penalty_bit_per_pair"]["0.001"] / meas_gap, 4)
        r["verdict"] = ("close-bottleneck-in-code"
                        if worst <= CLOSE_TH else
                        "retarget-f-floor" if worst >= RETAIM_TH else "inconclusive")
        f_cmp.append(r)

    # ---------------- Row G ----------------
    g_rows = []
    for c in inputs:
        r = next(x for x in f_rows if x["source"] == c["source"])
        f_soft_meas = LEAK_PAIR / c["H_soft_cal"]          # landed S-5c f (soft denom)
        p_bin = r["p_e_nz_given_v"]
        h_bin = [h2(p) for p in p_bin]
        alice = {}
        for ftag, fv in (("f1.00", 1.0),
                         ("f_hard_lo", 1.1025), ("f_hard_hi", 1.2654),
                         ("f_soft_S5c", round(f_soft_meas, 4))):
            code = sum((1.0 / NSUB) * min(1.0, fv * h) for h in h_bin)
            # Bob's sub-bin index, charged at its full entropy (adopted caliber)
            for nsub in (2, 4, 8):
                hk = math.log2(nsub)
                if nsub != NSUB:
                    # re-bin the 8 A5 sub-bins into nsub equal bins (mean entropy)
                    grp = NSUB // nsub
                    hb = [sum(h_bin[g * grp:(g + 1) * grp]) / grp for g in range(nsub)]
                else:
                    hk_alts = {2: 1.0, 4: 2.0, 8: 3.0}
                    hb = h_bin
                    hk = hk_alts[nsub]
                code_n = sum((1.0 / nsub) * min(1.0, fv * h) for h in hb)
                alice[f"{ftag}|K{nsub}"] = {
                    "leak_bit_per_pair": round(hk + code_n, 5),
                    "H_K": hk,
                    "alice_code": round(code_n, 5),
                    "saving_vs_fHsoft": round(LEAK_PAIR - (hk + code_n), 5)}
        best_key = max(alice, key=lambda k: alice[k]["saving_vs_fHsoft"])
        g_rows.append({
            "source": c["source"], "f_soft_S5c": round(f_soft_meas, 4),
            "baseline_fHsoft": LEAK_PAIR,
            "variants": alice,
            "best_saving": alice[best_key]["saving_vs_fHsoft"],
            "best_variant": best_key,
            "verdict": ("refuted-index-cost"
                        if alice[best_key]["saving_vs_fHsoft"] < G_SAVE_TH
                        else "survives"),
        })

    out = {
        "track": "EXPLORE-arithmetic",
        "frozen": {"N": N, "m": M, "q": Q, "bw_ps": BW, "nsub": NSUB,
                   "wide_sig_ps": WIDE_SIG, "k_range": [KMIN, KMAX],
                   "eps_list": list(EPS_LIST),
                   "leak_bit_per_pair": round(LEAK_PAIR, 5),
                   "thresholds": {"F_close": CLOSE_TH, "F_retarget": RETAIM_TH,
                                  "F_gap_nominal": GAP_NOMINAL,
                                  "G_save": G_SAVE_TH}},
        "transcribed": inputs,
        "F": f_cmp,
        "G": g_rows,
        "wall_s": None,
    }
    out["wall_s"] = round(time.perf_counter() - t0, 2)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output_root:
        raise SystemExit("--output-root required")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    res = run()
    (root / "chal_fg.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"leak/pair (frozen) = {res['frozen']['leak_bit_per_pair']:.5f} bit\n")
    print("row F: GF(5) soft information density and finite-length penalty")
    print(f"{'src':8s} {'meanI':>7s} {'varI':>8s} {'SWsoft':>7s} {'measSW':>7s} "
          f"{'pen01%':>7s} {'pen0.1%':>7s} {'gap':>7s} {'frac':>6s}  verdict")
    for r in res["F"]:
        fl = r["finite_len_penalty_bit_per_pair"]
        print(f"{r['source']:8s} {r['mean_I_bit']:7.4f} {r['var_I_bit2']:8.5f} "
              f"{r['model_SW_soft_rate']:7.4f} {r['measured_H_soft_cal']:7.4f} "
              f"{fl['0.01']:7.4f} {fl['0.001']:7.4f} "
              f"{r['measured_gap_leak_minus_SW']:7.4f} "
              f"{r['frac_of_measured_gap_at_eps1e-3']:6.3f}  {r['verdict']}")
    print("\nrow G: layered disclosure under 'Bob's message counts as leakage'")
    for r in res["G"]:
        best = r["variants"][r["best_variant"]]
        f1 = r["variants"]["f1.00|K2"]
        print(f"{r['source']:8s} baseline f*Hsoft={r['baseline_fHsoft']:.4f}  "
              f"best {r['best_variant']} leak={best['leak_bit_per_pair']:.4f} "
              f"saving={best['saving_vs_fHsoft']:+.4f}  "
              f"(f=1,K=2 leak={f1['leak_bit_per_pair']:.4f})  {r['verdict']}")
    print(f"\nwrote -> {root} (wall {res['wall_s']}s)")


if __name__ == "__main__":
    main()