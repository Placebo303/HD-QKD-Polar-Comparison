"""D-3 NB pool worker (importable module; Windows spawn-safe).

Moved out of msd_d3_physproxy __main__ so spawn children can import it.
"""

from __future__ import annotations

import numpy as np

N_NB = 1024
NOISE_EPS = 1e-3

_NBW = {}


def _nb_init(payload):
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
        derive_bundle,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_s2c_campaign as _s2c,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_peg as _peg,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_fftqspa as _qq,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_b2f_campaign as _b2f,
    )
    from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
        p1_stage1_runner as _p1,
    )
    counts, pa_l, g_l = pickle.loads(payload)
    _NBW["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(counts))
    field = _GF.create(32)
    _NBW["field"] = field
    pinned = _p1.construct_and_pin("P1S1-R1", _p1.PRODUCTION_CONSTRUCT["P1S1-R1"],
                                   _p1.production_rank_fn)
    _NBW["dense"] = {}
    for key, m in (("base", 200), ("full", 208)):
        sub = [(r, c, v) for r, c, v in pinned["full"]["triples"] if int(r) < m]
        _NBW["dense"][key] = _peg.sparse_to_dense(sub, N_NB, m, field)
    _NBW["pa_l"], _NBW["g_l"] = pa_l, g_l
    _NBW["_qq"], _NBW["_v28"], _NBW["_b2f"], _NBW["_s2c"] = _qq, _v28, _b2f, _s2c


def _nb_one(args) -> dict:
    blk, seed = args
    import numpy as _np
    rng = _np.random.default_rng(seed + blk)
    aks = _np.arange(1024)
    pa_l = _np.asarray(_NBW["pa_l"])
    g_l = _np.asarray(_NBW["g_l"])
    a = rng.choice(aks, size=N_NB, p=pa_l)
    u = rng.random(size=N_NB)
    delta = _np.where(u < NOISE_EPS, rng.integers(0, 1024, size=N_NB),
                      rng.choice(aks, size=N_NB, p=g_l))
    alice = a.astype(_np.int64)
    bob = ((a + delta) % 1024).astype(_np.int64)
    bundle, field = _NBW["bundle"], _NBW["field"]
    dense = _NBW["dense"]
    _qq, _v28, _b2f, _s2c = _NBW["_qq"], _NBW["_v28"], _NBW["_b2f"], _NBW["_s2c"]
    x = alice & 31
    y = bob & 31
    outs = []
    for key in ("base", "full"):
        if key == "full" and outs and bool(outs[0]["exact_match"]):
            break
        prior = _s2c.center_rows_prior(_b2f.marginal_prior_l2(bundle, bob), y)
        sxx = _qq.syndrome_of(field, dense[key], x.tolist())
        res = _v28.decode_error_domain_posterior(field, y.tolist(), dense[key],
                                                 sxx, prior, 300)
        xh = res.get("x_hat")
        ex = xh is not None and bool(_np.array_equal(_np.asarray(xh), x))
        outs.append({"exact_match": ex,
                     "reconstruction_ok": bool(res.get("reconstruction_ok", False))})
    ok = bool(outs[0]["exact_match"]) or (len(outs) > 1 and bool(outs[1]["exact_match"]))
    rok = bool(outs[-1].get("reconstruction_ok", False))
    return {"block": blk, "exact_u2": ok,
            "undetected": bool((not ok) and rok),
            "rescued": len(outs) > 1,
            "L_u2": 5 * (200 if len(outs) == 1 else 208)}
