"""E-2 confirmatory: B=300 NB corrected-diff on diff channel (pooled).
E-2 analytic: same A208 m200/208 + u1 working point; B=300 with 0 fails gives
f-upper 1.524 <= 1.55 (nominal cost 1.382). This run tests exactly that.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

N_NB = 1024
B = 300
SEED = 20266700


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("E-2 runs only with --full")
    import concurrent.futures as cf
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_d3_nbworker import (  # noqa: E402
        _nb_init,
        _nb_one,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        wilson_upper,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    th_a = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_a"])
    th_b = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_b"])
    assert th_a.sum() > 100000, "proxy tables"
    from comparison_bench.src.comparison_bench.formal_ir.msd_s2_prior import (  # noqa: E402
        diffpmf_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_d3_physproxy import (  # noqa: E402
        fit_diff,
    )
    pa_ch, g_ch = fit_diff(th_a)
    _, pseudo = diffpmf_model(th_b, 1.0)
    payload = pickle.dumps((pseudo, pa_ch.tolist(), g_ch.tolist()))
    jl = root / "blocks_e2.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=12, initializer=_nb_init,
                                initargs=(payload,)) as ex:
        recs = list(ex.map(_nb_one, [(b, SEED) for b in range(B)]))
    wall = time.perf_counter() - t0
    with jl.open("w", encoding="utf-8", buffering=1) as fh:
        for r in recs:
            fh.write(json.dumps({"prior": "diffpmf-a1", **r}) + "\n")
    nf = sum(0 if r["exact_u2"] else 1 for r in recs)
    nu = sum(1 for r in recs if r["undetected"])
    e_u2 = sum(r["L_u2"] for r in recs) / len(recs)
    # full-symbol composition with S-3' u1 (50.0, 0/95) + D-4 (50.0, 0/260)
    e_l = e_u2 + 50.0
    fer = nf / len(recs)
    HA, HAB, N, TAG = 9.9976919099, 0.7981344445, 1024, 64
    f_p = (e_l + TAG + (N * HA - e_l) * fer) / (N * HAB)
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        read_p1_scalars as _rs,
    )
    wu = wilson_upper(nf, len(recs))
    f_up = (e_l + TAG + (N * HA - e_l) * wu) / (N * HAB)
    row = {"prior": "diffpmf-a1", "blocks": len(recs), "u2_failures": nf,
           "undetected": nu, "E_u2": e_u2, "E_L_full": e_l, "FER": fer,
           "FER_wilson_upper95": wu, "f_point": f_p, "f_upper95": f_up,
           "nominal_cost_FER0": (e_l + TAG) / (N * HAB),
           "u1_inputs": "S-3' 0/95 + D-4 0/260 @50.0 (composed, stated)",
           "wall_s": wall}
    (root / "e2_summary.json").write_text(json.dumps([row], indent=2),
                                          encoding="utf-8")
    print(json.dumps([row], indent=2))


if __name__ == "__main__":
    main()
