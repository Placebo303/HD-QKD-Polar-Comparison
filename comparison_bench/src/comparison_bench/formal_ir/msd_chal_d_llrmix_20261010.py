"""Challenge-table close-out, row D: Gaussian vs mixture-law LLR (EXPLORE).

Frozen scientific contract (CHALLENGE_CLOSEOUT_PREREG_20261010.md section 1-2):
run the S-5c code and parameters on a SYNTHETIC mixture-law channel and compare
  * FER, and
  * the minimum feasible rate (lowest disclosure that still meets a 1% block
    error target, B >= 300 blocks)
between a pure-Gaussian per-symbol LLR model and the frozen A5 mixture-law LLR
model. Row D closes if the disclosure reduction the mixture LLR buys is
< 0.02 bit/pair.

Everything here is synthetic: no ``D:/Data`` read, no ``real_blocks``, no key
generation, no FER/SKR/qualification claim about the real chain. Blocks are
regenerated per worker from a per-block seed so results are order-independent
and reproducible.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from concurrent import futures as _cf
from pathlib import Path

import numpy as np
import scipy.stats as st

from comparison_bench.src.comparison_bench.formal_ir import (
    msd_c1_nbldpc as A3,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
    Gauss,
)

# ---- frozen (S-5c / S-2) --------------------------------------------------
BW = 200.0
N = 4096
M0 = 778                 # S-5c frac 0.19
Q = 5
WIDE_SIG = 100.0
CODE_SEED = 12192
MAX_ITER = 100           # A3 QSPA max_iter (S-5c frozen)
LOG2Q = math.log2(Q)
B_MIN = 300              # user-specified minimum block count
FER_TARGET = 0.01        # "minimum feasible rate" target block error
SEED0 = 20261010
# Rate grid. Row D asks how much LESS disclosure the mixture LLR allows, so the
# grid must sweep m DOWNWARD from the frozen S-5c point (m=778, leak 0.4412
# bit/pair) toward the asymptotic model bound H_soft ~ 0.19-0.26 bit/pair
# (m ~ 335-460), i.e. f -> 1. The first --full attempt (killed, root discarded)
# swept m upward, where both arms already sit at FER 0 and the criterion is
# therefore undecidable; retained in CHALLENGE_CLOSEOUT_LOG.md section 5.
DM_GRID_A = (778,)                      # stage A: the frozen operating point
DM_GRID_B = (706, 562, 490)             # stage B: downward rate scan
SCAN_B = 80                             # stage-B blocks per cell (budgeted)
EARLY_EXIT_FER = 0.05                   # reporting only; stop rule is the CP bound
EARLY_EXIT_MIN_BLOCKS = 32
ARMS = ("mix", "gauss_mm", "gauss_fitp")
DM_SOURCE_LAWS = ("T2-1M", "T2-2M")   # narrow and wide mixture, both from S-2 prefix fit
S2_PATH = "workspace/s_softmap/s2_20261009/s2_summary.json"
BUDGET_CAP_S = 2400.0
NPROC = 16

_G: dict = {}


# ---- channel + prior construction ----------------------------------------
def prior_gf5(law, v: np.ndarray) -> np.ndarray:
    """P(s=v | fine position) over GF(5), s = e mod 5.

    Same interval convention as the landed A5 tool and the landed S-5c prior
    (``msd_s5c_gf5.priors_of``): P(e=k | v) = mass of [v+(k-1)bw, v+k*bw).
    """
    n = v.shape[0]
    out = np.zeros((n, Q))
    for i in range(n):
        vi = float(v[i])
        for k in range(-6, 7):
            out[i, k % Q] += max(law.interval_mass(vi + (k - 1) * BW, vi + k * BW), 0.0)
        out[i] /= max(out[i].sum(), 1e-300)
    return out


def marginal_p(law) -> float:
    """Model-marginal P(e != 0) at mu=0, by direct averaging over the 8 A5 sub-bins."""
    ps = [1.0 - prior_gf5(law, np.array([(st + 0.5) * BW / 8.0]))[0, 0] for st in range(8)]
    return float(np.mean(ps))


def sig_for_p(law, target_p: float) -> float:
    """Gaussian sigma whose marginal P(e!=0) matches ``target_p`` (bisection)."""
    lo, hi = 1.0, 200.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if marginal_p(Gauss(mid)) < target_p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def gen_block(rng: np.random.Generator, sig: float, w: float) -> tuple[np.ndarray, np.ndarray]:
    """One synthetic frame: v uniform in the bin, mixture-law residual, s = e mod 5."""
    v = rng.uniform(0.0, BW, size=N)
    wide = rng.random(N) < w
    delta = np.where(wide, rng.normal(0.0, WIDE_SIG, size=N), rng.normal(0.0, sig, size=N))
    e = -np.floor((v - delta) / BW).astype(np.int64)
    return v, (e % Q).astype(np.int64)


# ---- worker ----------------------------------------------------------------
def _w_init(n, code_seed, sig, w, sig_gauss_mm, sig_gauss_p):
    _G.update(n=n, sig=sig, w=w, sig_gauss_mm=sig_gauss_mm, sig_gauss_fitp=sig_gauss_p,
              code_seed=code_seed, laws={
                  "mix": DoubleGauss(sig, WIDE_SIG, w),
                  "gauss_mm": Gauss(sig_gauss_mm),
                  "gauss_fitp": Gauss(sig_gauss_p),
              }, codes={})


def _code(m: int):
    if m not in _G["codes"]:
        _G["codes"][m] = A3.construct(_G["n"], m, Q, seed=_G["code_seed"])
    return _G["codes"][m]


def _w_task(task: tuple[int, int, tuple]) -> dict:
    """Decode one block under the requested arms (paired: identical code, v, error).

    The block seed depends on (m, bi) only, so every arm sees the identical
    realisation at a given rate point -- that pairing is what makes the McNemar
    comparison valid. ``armmask`` lets one arm be decoded alone so it can be
    stopped early without stranding the others. No per-arm adaptation, no seed
    search, no retry.
    """
    m, bi, armmask = task
    code = _code(m)
    rng = np.random.default_rng(SEED0 + 1009 * bi + 7919 * m)
    v, s = gen_block(rng, _G["sig"], _G["w"])
    syn, bits = A3.disclose(code, s)
    out = {"m": m, "block": bi, "bits": bits}
    for arm in armmask:
        t0 = time.perf_counter()
        prior = prior_gf5(_G["laws"][arm], v)
        shat = A3.decode(code, np.zeros(code.n, dtype=np.int64), syn, prior, MAX_ITER)
        out[arm] = bool(shat is not None and np.array_equal(shat, s))
        out[f"t_{arm}"] = round(time.perf_counter() - t0, 3)
    return out


# ---- driver ----------------------------------------------------------------
def self_test(n: int = 256, blocks: int = 4) -> None:
    rng = np.random.default_rng(7)
    law_mix = DoubleGauss(13.34, WIDE_SIG, 0.0069)
    sig = 13.34
    # 1. prior rows are proper distributions
    pr = prior_gf5(law_mix, np.array([12.5, 100.0, 187.5]))
    assert np.allclose(pr.sum(axis=1), 1.0, atol=1e-9), pr.sum(axis=1)
    assert np.all(pr >= 0.0)
    # 2. edge sub-bins carry more information than the centre
    h = [-(lambda p: (p[p > 0] * np.log2(p[p > 0])).sum())(row) for row in pr]
    assert h[0] > h[1] + 0.2 and h[2] > h[1] + 0.2, h
    # 3. wider mixture law -> strictly higher marginal error rate
    assert marginal_p(DoubleGauss(16.31, WIDE_SIG, 0.0192)) > marginal_p(law_mix)
    # 4. sig_for_p inverts marginal_p on a pure Gaussian (identity round-trip),
    #    and matching the MIXTURE marginal forces a WIDER Gaussian than the core
    #    (this is the model-mismatch mechanism D is about, in one line).
    assert abs(sig_for_p(Gauss(13.34), marginal_p(Gauss(13.34))) - 13.34) < 0.01
    assert sig_for_p(Gauss(sig), marginal_p(law_mix)) > sig
    # 5. GF(5) decode roundtrip on synthetic truth at the FROZEN frac 0.19
    #    (m/n = 0.19 as in S-5c). Retained failed attempt: at n=64, m=12
    #    (rate 0.81) the PEG instance is degenerate and both arms fail even
    #    with a near-noiseless channel -- a tiny-code artifact, not a prior
    #    bug (the landed S-5c self-test likewise uses m=n/2 at n=64).
    code = A3.construct(n, int(n * M0 / N), Q, seed=3)
    rr = np.random.default_rng(11)
    vs, ss = gen_block_small(rr, n, 13.34, 0.0069)
    syn, bits = A3.disclose(code, ss)
    assert bits == math.ceil(int(n * M0 / N) * LOG2Q)
    assert float(prior_gf5(law_mix, vs).argmax(axis=1).__eq__(ss).mean()) > 0.85
    for law in (law_mix, Gauss(15.0)):
        pr2 = prior_gf5_small(law, vs, n)
        shat = A3.decode(code, np.zeros(n, dtype=np.int64), syn, pr2, MAX_ITER)
        assert shat is not None and np.array_equal(shat, ss)
    # 6. sigma_gap relation: moment-matched Gaussian is wider than the core
    assert math.sqrt(0.9931 * 13.34 ** 2 + 0.0069 * WIDE_SIG ** 2) > 13.34
    print("chal_d self-test OK (priors / ordering / marginals / inversion / decode)")


def gen_block_small(rng, n, sig, w):
    v = rng.uniform(0.0, BW, size=n)
    wide = rng.random(n) < w
    delta = np.where(wide, rng.normal(0.0, WIDE_SIG, size=n), rng.normal(0.0, sig, size=n))
    e = -np.floor((v - delta) / BW).astype(np.int64)
    return v, (e % Q).astype(np.int64)


def prior_gf5_small(law, v, n):
    return prior_gf5(law, v)


def mcnemar(a_only: int, b_only: int) -> float:
    from math import comb
    nd, k = a_only + b_only, min(a_only, b_only)
    if nd == 0:
        return 1.0
    return min(1.0, 2.0 * sum(comb(nd, i) for i in range(k + 1)) / 2.0 ** nd)


def fer_lower95(fa: int, ok: int) -> float:
    """Clopper-Pearson 95% lower bound on FER."""
    return 0.0 if fa == 0 else float(st.beta.ppf(0.025, fa, ok + 1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--blocks", type=int, default=B_MIN)
    ap.add_argument("--probe", type=int, default=0,
                    help="sweep grids A+B on B=n blocks per cell, print FER only")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tiny", action="store_true",
                    help="smoke the driver: 2 sources x 2 rate points x 20 blocks")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.tiny:
        global DM_GRID_A, DM_GRID_B, SCAN_B, DM_SOURCE_LAWS, EARLY_EXIT_MIN_BLOCKS
        DM_GRID_A, DM_GRID_B = (778, 562), ()
        SCAN_B, DM_SOURCE_LAWS, EARLY_EXIT_MIN_BLOCKS = 20, ("T2-1M",), 10
        args.blocks = 20

    if args.probe:
        sig, w = 13.34, 0.0069
        mm = math.sqrt((1 - w) * sig ** 2 + w * WIDE_SIG ** 2)
        laws = {"mix": DoubleGauss(sig, WIDE_SIG, w), "gauss_mm": Gauss(mm),
                "gauss_fitp": Gauss(sig_for_p(Gauss(sig), marginal_p(DoubleGauss(sig, WIDE_SIG, w))))}
        nprobe = args.probe
        for m in DM_GRID_A + DM_GRID_B:
            code = A3.construct(N, m, Q, seed=CODE_SEED)
            ok = {a: 0 for a in laws}
            for bi in range(nprobe):
                rng = np.random.default_rng(SEED0 + 1009 * bi)
                v, s = gen_block(rng, sig, w)
                syn, _ = A3.disclose(code, s)
                for arm, law in laws.items():
                    pr = prior_gf5(law, v)
                    shat = A3.decode(code, np.zeros(N, dtype=np.int64), syn, pr, MAX_ITER)
                    ok[arm] += int(shat is not None and np.array_equal(shat, s))
            print(f"m={m} leak={math.ceil(m*LOG2Q)/N:.4f} "
                  + " ".join(f"{a}={ok[a]}/{nprobe}" for a in laws), flush=True)
        return

    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    s2 = json.load(open(S2_PATH, encoding="utf-8"))
    t_start = time.perf_counter()
    results: dict = {"track": "EXPLORE-synthetic",
                     "frozen": {"N": N, "q": Q, "code_seed": CODE_SEED,
                                "max_iter": MAX_ITER,
                                "grid_A": list(DM_GRID_A), "blocks_A": args.blocks,
                                "grid_B": list(DM_GRID_B), "blocks_B": SCAN_B,
                                "grid_direction": "m downward from frozen 778 toward f~1",
                                "fer_target": FER_TARGET,
                                "early_exit": {"rule": "stop an arm once the Clopper-Pearson 95% LOWER "
                                               "bound on FER exceeds the 1% target",
                                               "min_blocks": EARLY_EXIT_MIN_BLOCKS,
                                               "stage_A": "disabled (B>=300 required there)",
                                               "rationale": "infeasible is already "
                                                            "conclusive for the min-feasible-"
                                                            "rate question; stops the 65 s "
                                                            "failure-path decodes"}},
                     "sources": {}}
    jlf = (root / "chal_d_rows.jsonl").open("w", encoding="utf-8")

    def run_cell(src, sig, w, mm, sp, m, blocks, early_exit=True):
        """Decode paired blocks, ONE INDEPENDENT STREAM PER ARM.

        With early_exit, an arm stops on its own once its Clopper-Pearson 95%
        LOWER bound on FER already exceeds the 1% target -- for the
        minimum-feasible-rate question that is a decided outcome, and the failure
        path costs ~65 s per block (100 QSPA iterations), so continuing would buy
        nothing. Block seeds depend on (m, bi) only, so the surviving streams stay
        paired on their common prefix; the paired count is recorded per cell.
        """
        res = {a: {} for a in ARMS}
        WINDOW = NPROC * 2     # sliding window: keep every worker fed, because a
        with _cf.ProcessPoolExecutor(   # failing block costs ~65 s while the
                max_workers=NPROC, initializer=_w_init,  # other 15 would idle
                initargs=(N, CODE_SEED, sig, w, mm, sp)) as ex:
            for arm in ARMS:
                got, inflight, nxt, stopped = res[arm], {}, 0, False
                while not stopped and (nxt < blocks or inflight):
                    while nxt < blocks and len(inflight) < WINDOW:
                        inflight[ex.submit(_w_task, (m, nxt, (arm,)))] = nxt
                        nxt += 1
                    fin, _ = _cf.wait(list(inflight), return_when=_cf.FIRST_COMPLETED)
                    for f in fin:
                        r = f.result()
                        got[r["block"]] = r
                        del inflight[f]
                    if early_exit and len(got) >= EARLY_EXIT_MIN_BLOCKS:
                        fa = sum(1 for x in got.values() if not x[arm])
                        if fer_lower95(fa, len(got) - fa) > FER_TARGET:
                            stopped = True
                            for f in inflight:
                                f.cancel()
                            inflight.clear()
        common = sorted(set.intersection(*(set(res[a]) for a in ARMS)))
        rows = []
        for bi in common:
            rows.append({"m": m, "block": bi, "bits": res[ARMS[0]][bi]["bits"],
                         **{a: res[a][bi][a] for a in ARMS},
                         **{f"t_{a}": res[a][bi][f"t_{a}"] for a in ARMS}})
        return rows, {a: len(res[a]) for a in ARMS}

    def summarize(rows, m, per_arm_n):
        """FER per arm over the blocks THAT ARM actually ran (paired McNemar is
        computed separately over the common prefix)."""
        cell = {"m": m, "leak_bit_per_pair": round(math.ceil(m * LOG2Q) / N, 5),
                "bits_per_block": rows[0]["bits"], "paired_blocks": len(rows),
                "per_arm_blocks": dict(per_arm_n)}
        for arm in ARMS:
            nb = per_arm_n[arm]
            fa = sum(1 for r in rows if not r[arm])
            ok = nb - fa
            lo = 0.0 if fa == 0 else float(st.beta.ppf(0.025, fa, ok + 1))
            hi = 1.0 if fa == nb else float(st.beta.ppf(0.975, fa + 1, ok))
            cell[arm] = {"blocks": nb, "ok": ok, "fail": fa,
                         "FER": round(fa / nb, 5),
                         "FER_CP95": [round(lo, 5), round(hi, 5)],
                         "T_med": float(np.median([r[f"t_{arm}"] for r in rows
                                                   if r["block"] < nb])),
                         "feasible": (fa / nb) <= FER_TARGET,
                         "conclusive_infeasible": lo > FER_TARGET}
        for arm in ARMS[1:]:
            mo = sum(1 for r in rows if r["mix"] and not r[arm])
            ao = sum(1 for r in rows if r[arm] and not r["mix"])
            cell[f"mcnemar_mix_vs_{arm}"] = {"paired_blocks": len(rows),
                                             "mix_only": mo, f"{arm}_only": ao,
                                             "p": round(mcnemar(mo, ao), 6)}
        return cell

    for src in DM_SOURCE_LAWS:
        fit = s2["sources"][src]["prefix_fit"]
        sig, w = float(fit["sig"]), float(fit["w"])
        mm = math.sqrt((1 - w) * sig ** 2 + w * WIDE_SIG ** 2)
        sp = sig_for_p(Gauss(sig), marginal_p(DoubleGauss(sig, WIDE_SIG, w)))
        cells = []
        # ---- stage A: frozen S-5c operating point, full block budget ----
        for m in DM_GRID_A:
            if time.perf_counter() - t_start > BUDGET_CAP_S:
                cells.append({"m": m, "stopped": "budget-cap"})
                continue
            rows, per_arm = run_cell(src, sig, w, mm, sp, m, args.blocks, early_exit=False)
            for r in rows:
                jlf.write(json.dumps({"source": src, "stage": "A", **r}) + "\n")
            jlf.flush()
            cell = summarize(rows, m, per_arm)
            cell["stage"] = "A"
            cells.append(cell)
            print(f"[A] {src} m={m} leak={cell['leak_bit_per_pair']:.4f} "
                  f"B={cell['paired_blocks']}/{cell['per_arm_blocks']} "
                  f"mix FER={cell['mix']['FER']} gmm={cell['gauss_mm']['FER']} "
                  f"gfp={cell['gauss_fitp']['FER']} "
                  f"p(mix vs gmm)={cell['mcnemar_mix_vs_gauss_mm']['p']} "
                  f"wall={time.perf_counter()-t_start:.0f}s", flush=True)
            results["sources"][src] = {"sig": sig, "w": w, "sig_gauss_mm": round(mm, 4),
                                       "sig_gauss_fitp": round(sp, 4), "cells": cells}
            (root / "chal_d_cells.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
        # ---- stage B: downward rate scan, budgeted blocks ----
        for m in DM_GRID_B:
            if time.perf_counter() - t_start > BUDGET_CAP_S:
                cells.append({"m": m, "stage": "B", "stopped": "budget-cap"})
                print(f"[B] {src} m={m}: STOPPED budget-cap", flush=True)
                results["sources"][src]["cells"] = cells
                (root / "chal_d_cells.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
                continue
            rows, per_arm = run_cell(src, sig, w, mm, sp, m, SCAN_B)
            for r in rows:
                jlf.write(json.dumps({"source": src, "stage": "B", **r}) + "\n")
            jlf.flush()
            cell = summarize(rows, m, per_arm)
            cell["stage"] = "B"
            cells.append(cell)
            print(f"[B] {src} m={m} leak={cell['leak_bit_per_pair']:.4f} "
                  f"B={cell['paired_blocks']}/{cell['per_arm_blocks']} "
                  f"mix FER={cell['mix']['FER']} gmm={cell['gauss_mm']['FER']} "
                  f"gfp={cell['gauss_fitp']['FER']} wall={time.perf_counter()-t_start:.0f}s",
                  flush=True)
            results["sources"][src]["cells"] = cells
            (root / "chal_d_cells.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
        # ---- row D verdict: minimum feasible rate per arm over A+B ----
        done = [c for c in cells if "mix" in c]
        leak_hi = max((c["leak_bit_per_pair"] for c in done), default=None)
        v = {"source": src, "n_cells": len(done),
             "leak_highest_tested": leak_hi}
        for arm in ARMS:
            feas = [c for c in done if c[arm]["feasible"]]
            v[f"min_feasible_m_{arm}"] = min((c["m"] for c in feas), default=None)
            v[f"min_feasible_leak_{arm}"] = min((c["leak_bit_per_pair"] for c in feas), default=None)
        base = v.get("min_feasible_leak_mix")
        # A Gaussian arm with no feasible rate anywhere in the grid needs MORE
        # disclosure than the largest leak tested, so the saving it concedes is a
        # LOWER BOUND (leak_highest_tested - min_feasible_leak_mix), not zero.
        for arm in ARMS[1:]:
            a = v.get(f"min_feasible_leak_{arm}")
            if a is not None and base is not None:
                v[f"disclosure_reduction_vs_{arm}"] = round(a - base, 5)
                v[f"disclosure_reduction_bound_kind_{arm}"] = "exact"
            elif base is not None and leak_hi is not None:
                v[f"disclosure_reduction_vs_{arm}"] = round(leak_hi - base, 5)
                v[f"disclosure_reduction_bound_kind_{arm}"] = "lower_bound(no feasible rate in grid)"
            else:
                v[f"disclosure_reduction_vs_{arm}"] = None
                v[f"disclosure_reduction_bound_kind_{arm}"] = "undetermined"
        vals = [v.get(f"disclosure_reduction_vs_{a}") for a in ARMS[1:]]
        vals = [x for x in vals if x is not None]
        v["max_disclosure_reduction"] = round(max(vals), 5) if vals else None
        v["min_disclosure_reduction"] = round(min(vals), 5) if vals else None
        v["verdict"] = ("keep-open" if vals and min(vals) >= 0.02
                        else "close" if vals and max(vals) < 0.02
                        else "inconclusive")
        v["verdict_basis"] = ("mixture LLR concedes >= 0.02 bit/pair less disclosure at the "
                              "1% block-error target"
                              if v["verdict"] == "keep-open" else
                              "disclosure reduction < 0.02 bit/pair"
                              if v["verdict"] == "close" else
                              "grid did not bracket both arms")
        results["sources"][src]["rowD"] = v
        print(f"{src} rowD: {json.dumps(v)}", flush=True)
        (root / "chal_d_cells.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    results["wall_s_total"] = round(time.perf_counter() - t_start, 1)
    (root / "chal_d_cells.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    jlf.close()
    print(f"chal_d done wall={results['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()