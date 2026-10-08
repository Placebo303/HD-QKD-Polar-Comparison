"""C-3 mini (main-thread contingency, EXPLORE synthetic only).

Collision-free complement to the frozen C-3 full matrix (msd_c3_bakeoff):
different filenames, different machine root. Scope: FRESH A3/A4 arms only
at families F1/F2 (k=1 calibrated) + F3 (k=2 exploratory) with the frozen
rate rule evaluated in-driver (C3_LAUNCH §5 table is the acceptance
cross-check, not an input). A1/A2/A5 fresh execution stays with the full
C-3 operator; G-5/F-1 rows enter here ONLY as cross-regime reference
(different p_op), never as OPT competitors.

Reads: accepted C-1/C-2 modules (kbin prior math, A3/A4 codecs, c2
conditional law, runner bookkeeping). No raw data, no DECIDE reruns.
"""

from __future__ import annotations

import argparse
import faulthandler
import json
import math
import time
from pathlib import Path

faulthandler.enable()

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_kbin as KB
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbldpc as A3
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_nbpolar as A4
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as RU
from comparison_bench.src.comparison_bench.formal_ir import msd_c2_fit as C2

GAP_BIN = {1024: 0.08, 2048: 0.06, 4096: 0.05, 8192: 0.04,
           16384: 0.03, 32768: 0.025, 65536: 0.02}
GAP_NB = {1024: 0.10, 2048: 0.08, 4096: 0.07, 8192: 0.06,
          16384: 0.05, 32768: 0.04, 65536: 0.03}
MARGIN_B = 0.01
TAG = 64
N_GRID = (1024, 2048, 4096, 8192, 16384, 32768, 65536)
# F1/F2: C-0 T2-1M optimal rows (C3_LAUNCH §2). p_minus is absolute mass.
FAM_k1 = {
    "F1": {"k": 1, "p": 0.060740, "p_minus": 0.037000},
    "F2": {"k": 1, "p": 0.030413, "p_minus": 0.018564},
}
# F3: k=2 exploratory from T2-1M conditional law (C2 canonical).
F3_SRC = {"bw": 100.0, "sig": 24.882440410661673, "delta": 46.992797566442555}


def entropy_bits(g) -> float:
    return float(-sum(x * math.log2(x) for x in g if x > 0.0))


def family_prior(fam: str):
    """Return (q, prior_g list, H_q, tag_note)."""
    if fam in FAM_k1:
        d = FAM_k1[fam]
        q, g = RU._prior_from_channel(
            {"k": d["k"], "p": d["p"], "p_minus": d["p_minus"]})
        return q, list(g), entropy_bits(g), "C-0-optimal-ternary"
    if fam == "F3":
        q = 5
        _, cover = C2.cond_dist(F3_SRC["bw"], F3_SRC["sig"], F3_SRC["delta"], 0)
        g = [0.0] * q
        for e in range(-2, 3):
            jk, _ = C2.cond_dist(F3_SRC["bw"], F3_SRC["sig"], F3_SRC["delta"], e)
            g[e % q] = jk / cover
        rest = max(0.0, 1.0 - sum(g))
        return q, g, entropy_bits(g + ([rest] if rest > 0 else [])), \
            f"cond-law rest={rest:.6f}"
    raise ValueError(f"unknown family {fam!r}")


def m_for(N: int, q: int, H: float) -> int:
    m = int(math.ceil(N * (H / math.log2(q) + GAP_NB[N] + MARGIN_B)))
    if not (0 < m < N):
        raise ValueError(f"infeasible (N={N},q={q}): m={m}")
    return m


def run_a3(N: int, q: int, g, m: int, B: int, seed: int, fh,
           skip_blocks: set[int] | None = None, family: str = "") -> dict:
    """skip_blocks: already-landed block ids (draws still consumed to keep the
    deterministic RNG stream identical)."""
    skip = skip_blocks or set()
    code = A3.construct(N, m, q, seed)
    rng = np.random.default_rng(seed)
    k_info = N - m
    kept_ok = k_info * math.log2(q)
    n_succ, tds = 0, []
    lec_last = 0
    for b in range(B):
        a = rng.integers(0, q, N)
        e = rng.choice(q, size=N, p=np.asarray(g) / sum(g))
        if b in skip:
            continue
        bb = ((a + e) % q).tolist()
        syn, lec = A3.disclose(code, a.tolist())
        lec_last = int(lec)
        t0 = time.perf_counter()
        hat = A3.decode(code, bb, syn, list(g), 50)
        dt = time.perf_counter() - t0
        tds.append(dt)
        good = hat is not None and list(hat) == a.tolist()
        n_succ += int(good)
        fh.write(json.dumps({
            "method": "A3", "family": family, "N": N, "block": b,
            "ver": int(good), "u": 0,
            "kept": float(kept_ok) if good else 0.0, "L_EC": int(lec),
            "tag": TAG if good else 0, "T_dec": float(dt),
            "code_hash": getattr(code, "code_hash", ""), "undetected": False,
            "status": "ok" if good else "decode_failed"}) + "\n")
        fh.flush()
        if (b + 1) % 50 == 0:
            print(f"  A3 N={N} block {b + 1}/{B} succ={n_succ} last_T={dt:.1f}s",
                  flush=True)
    return {"success": n_succ, "median_T_dec": float(np.median(tds)) if tds else 0.0,
            "L_EC": int(lec_last), "kept_ok": float(kept_ok),
            "resumed_skips": len(skip)}


def cell_summary(method: str, fam: str, N: int, B: int, res: dict,
                 C_total: float, h_op: float, i_op: float) -> dict:
    return {"method": method, "family": fam, "N": N, "B": B,
            "evidence": "fresh-mini", **RU.net_of_cell(
                kept_bits=res["kept_ok"], L_EC_bits=res["L_EC"],
                tag_bits=TAG, n_fail=B - res["success"], n_blocks=B,
                C_total=C_total, N=N, n_undetected=0,
                h_op=h_op, I_op=i_op),
            "median_T_dec": res["median_T_dec"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--families", default="F1,F2,F3")
    ap.add_argument("--methods", default="A3,A4")
    ap.add_argument("--N-list", default=",".join(map(str, N_GRID)))
    ap.add_argument("--B", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20261008)
    ap.add_argument("--list-size", type=int, default=1,
                    help="A4 SCL list size (1 = SC). Recorded per cell.")
    ap.add_argument("--budget-s", type=float, default=10800.0)
    ap.add_argument("--resume", default="",
                    help="old root to resume from (rows copied/skipped, "
                         "deterministic seeds keep streams identical)")
    ap.add_argument("--resume-families", default="",
                    help="comma list of families the OLD root ran (old rows "
                         "lack family tags and match only these families)")
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("mini runs only with --full")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    fams = args.families.split(",")
    meths = args.methods.split(",")
    Ns = [int(x) for x in args.N_list.split(",")]
    B, t_all = args.B, time.perf_counter()
    C_plan = 5_000_000.0  # planning acquisition length per point (C4_PLAN)
    # Resume index from old root (block sets per (family, method, N)).
    # Old rows may lack family tags: they match only --resume-families.
    res_fams = set(x for x in args.resume_families.split(",") if x)
    landed: dict[tuple[str, str, int], dict[int, dict]] = {}

    def _fam_match(row_fam: str | None, fam: str) -> bool:
        return row_fam == fam or (not row_fam and fam in res_fams)
    if args.resume:
        old = Path(args.resume)
        for part in ("mini_rows_a3.jsonl", "mini_rows_a4.jsonl",
                     "mini_rows.jsonl"):
            p = old / part
            if not p.exists():
                continue
            for line in p.open(encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue  # torn tail of crashed run
                landed.setdefault((r["method"], int(r["N"])), {})[int(r["block"])] = r
        print(f"resume: {len(landed)} cells with rows from {old}", flush=True)

    def _have(fam: str, meth: str, N: int) -> dict[int, dict]:
        return {b: r for b, r in landed.get((meth, N), {}).items()
                if _fam_match(r.get("family"), fam)}
    out: list[dict] = []
    # Single-writer discipline (lesson 20261008: never share one JSONL between
    # a held buffered handle and run_cell's append handle — flushed buffers
    # clobber appended rows). A3 writes mini_rows_a3.jsonl, A4 mini_rows_a4.jsonl;
    # merged (documented order) into mini_rows.jsonl at the end.
    jl3 = (root / "mini_rows_a3.jsonl").open("w", encoding="utf-8")
    for fam in fams:
        q, g, H, note = family_prior(fam)
        for N in Ns:
            m = m_for(N, q, H)
            ch = {"q": q, "p": 1.0 - g[0],
                  "p_minus": g[q - 1], "m": m}
            for meth in meths:
                if time.perf_counter() - t_all > args.budget_s:
                    out.append({"method": meth, "family": fam, "N": N,
                                "status": "budget-stop", "evidence": "fresh-mini"})
                    continue
                if meth == "A4":
                    have = _have(fam, "A4", N)
                    if len(have) >= B:
                        with (root / "mini_rows_a4.jsonl").open(
                                "a", encoding="utf-8") as fh4:
                            for b in sorted(have)[:B]:
                                fh4.write(json.dumps(have[b]) + "\n")
                        rr = [have[b] for b in sorted(have)[:B]]
                        succ = sum(x["ver"] for x in rr)
                        med = float(np.median([x["T_dec"] for x in rr]))
                        lec0 = int(rr[0]["L_EC"])
                        kept0 = float(max(x["kept"] for x in rr))
                        summ = {"method": "A4", "family": fam, "N": N,
                                "B": B, "evidence": "fresh-mini",
                                **RU.net_of_cell(
                                    kept_bits=kept0, L_EC_bits=lec0,
                                    tag_bits=TAG, n_fail=B - succ,
                                    n_blocks=B, C_total=C_plan, N=N,
                                    n_undetected=0, h_op=H,
                                    I_op=math.log2(q) - H),
                                "median_T_dec": med,
                                "list_size": 1,
                                "exploratory": fam == "F3",
                                "resumed": True}
                    else:
                        if args.resume and args.list_size != 1:
                            raise SystemExit(
                                "L8 resume unsupported (rows lack list-size "
                                "tags); use a fresh root")
                        s = RU.run_cell("A4", N, ch, B, args.seed,
                                        str(root / "mini_rows_a4.jsonl"),
                                        list_size=args.list_size,
                                        C_total=C_plan)
                        summ = {"method": "A4", "family": fam, "N": N,
                                "B": B, "evidence": "fresh-mini", **s["net"],
                                "median_T_dec": s["median_T_dec"],
                                "list_size": args.list_size,
                                "exploratory": fam == "F3"}
                elif meth == "A3":
                    have = _have(fam, "A3", N)
                    if len(have) >= B:
                        for b in sorted(have)[:B]:
                            jl3.write(json.dumps(have[b]) + "\n")
                        jl3.flush()
                        rr = [have[b] for b in sorted(have)[:B]]
                        r = {"success": sum(x["ver"] for x in rr),
                             "median_T_dec": float(np.median(
                                 [x["T_dec"] for x in rr])),
                             "L_EC": int(rr[0]["L_EC"]),
                             "kept_ok": float(max(x["kept"] for x in rr)),
                             "resumed_skips": B}
                        summ = cell_summary("A3", fam, N, B, r, C_plan, H,
                                            math.log2(q) - H)
                        summ["exploratory"] = (fam == "F3")
                        summ["resumed"] = True
                    else:
                        skips = set(have) if have else None
                        if skips:
                            print(f"resuming A3 N={N} from block "
                                  f"{max(skips) + 1}/{B}", flush=True)
                        r = run_a3(N, q, g, m, B, args.seed, jl3,
                                   skip_blocks=skips, family=fam)
                        jl3.flush()
                        summ = cell_summary("A3", fam, N, B, r, C_plan, H,
                                            math.log2(q) - H)
                        summ["exploratory"] = (fam == "F3")
                else:
                    raise SystemExit(f"mini supports A3/A4 only, got {meth}")
                out.append(summ)
                print(fam, meth, f"N={N}", "m=", m,
                      "net=", round(summ.get("Net_seg", float("nan")), 1)
                      if summ.get("Net_seg") is not None else None,
                      flush=True)
    jl3.close()
    # Merge per-method files into mini_rows.jsonl (documented order A3 then A4).
    with (root / "mini_rows.jsonl").open("w", encoding="utf-8") as out_jl:
        for part in ("mini_rows_a3.jsonl", "mini_rows_a4.jsonl"):
            p = root / part
            if p.exists():
                with open(p, encoding="utf-8") as fh:
                    out_jl.write(fh.read())
    # OPT per (family, method): max Net_seg over feasible N<=16384 (N_valid@5M).
    opt = []
    for fam in fams:
        for meth in meths:
            cand = [c for c in out if c.get("family") == fam
                    and c.get("method") == meth and c.get("Net_seg") is not None
                    and c["N"] <= 16384]
            if cand:
                best = max(cand, key=lambda c: c["Net_seg"])
                opt.append({"family": fam, "method": meth,
                            "opt_N": best["N"], "Net_seg": best["Net_seg"],
                            "Net_per_coin": best["Net_per_coin"],
                            "f_full": best.get("f_full"),
                            "FER_hat": best.get("FER_hat"),
                            "exploratory": fam == "F3"})
    (root / "mini_summary.json").write_text(json.dumps(
        {"families": fams, "note": "main-thread contingency; full matrix with C-3 op",
         "wall_s": round(time.perf_counter() - t_all, 1),
         "cells": out, "opt": opt}, indent=2), encoding="utf-8")
    print(f"wrote {len(out)} cells, {len(opt)} opt rows")


if __name__ == "__main__":
    main()
