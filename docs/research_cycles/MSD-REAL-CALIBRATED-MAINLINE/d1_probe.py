"""D-1 failure-location probe (artifacted): B=100 genie-diff MSD with
per-stage first-fail logging. Supports (not proves) finite-length reading;
1+1 events are UNDECIDED-grade evidence by the single-digit rule.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

import numpy as np


def main() -> None:
    import sys
    sys.path.insert(0, ".")
    from comparison_bench.src.comparison_bench.formal_ir.msd_d1_geniediff import (
        fit_g,
        gen_pairs,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
        plane_conditional_entropies,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (
        build_conditional_prior_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (
        build_mixed_point,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (
        disclose_syndromes,
        _syndrome,
        make_bp_decoder,
    )

    root = Path("workspace/d1_geniediff/d1_20261006")
    R = Path("workspace/s1_proxy/s1_20261006")
    th_a = np.asarray(np.load(R / "T2-1M_tier_tables.npz")["half_a"])
    pa_fit, g_fit = fit_g(th_a)
    aks = np.arange(1024)
    joint = pa_fit[:, None] * g_fit[(aks[None, :] - aks[:, None]) % 1024]
    joint = joint / joint.sum()
    pseudo = joint * th_a.sum()
    model = build_conditional_prior_model(pseudo, encoding="NATURAL",
                                          order="LSB_FIRST")
    h = plane_conditional_entropies(pseudo)
    matrices, factories, _, _ = build_mixed_point(16384, h, 2000, 32, 256)
    bp = functools.partial(make_bp_decoder, max_iter=200)
    rng = np.random.default_rng(20266400)
    jl = root / "d1_probe.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    nf = 0
    from collections import Counter
    firstfail = Counter()
    with jl.open("w", encoding="utf-8", buffering=1) as fh:
        for blk in range(100):
            alice, bob = gen_pairs(pa_fit, g_fit, 16384, rng)
            dis = disclose_syndromes(alice, model, matrices)
            recs, passed, first = [], [], None
            for stage, mat in enumerate(matrices):
                prev = np.stack(recs, axis=0) if recs else np.empty((0, 16384),
                                                                   dtype=np.uint8)
                q = model.query(stage, bob, prev)
                base = (q.p_one > 0.5).astype(np.uint8)
                ch = np.minimum(q.p_one, 1 - q.p_one).copy()
                syn = np.asarray(dis.public_syndromes[stage], dtype=np.uint8)
                delta = np.bitwise_xor(syn, _syndrome(mat, base))
                f = factories[stage](parity_check_matrix=mat, error_channel=ch)
                rec = np.bitwise_xor(base, np.asarray(f.decode(delta.copy())).astype(np.uint8))
                recs.append(rec)
                ok = bool(np.array_equal(_syndrome(mat, rec), syn))
                passed.append(ok)
                if not ok:
                    first = stage
                    firstfail[stage] += 1
                    break
            exact = len(passed) == 10 and all(passed)
            nf += 0 if exact else 1
            fh.write(json.dumps({"block": blk, "exact_ok": exact,
                                 "first_fail_stage": first}) + "\n")
    print("genie fails:", nf, "/100; first-fail:", dict(firstfail), flush=True)


if __name__ == "__main__":
    main()
