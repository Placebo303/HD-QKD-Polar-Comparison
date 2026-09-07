"""D5-G1 attribution R1 — batch 2: AC05(b) direct-recovery sanity (decoder calls).

T-a (adapter path): delta prior on true word -> expect iters=0, exact=1.
T-b (machinery): strong 0.85 prior on true word -> converges iff decoder+graph
    can decode with signal. Same x_true/syndrome path as formal _decode_block.
T-c (control, only if T-b fails): same T-b prior on the known-good G0 tiny
    8x8 cycle fixture -> discriminates G1-prefix defect vs decoder defect.

Direct injected decoder only (bind_historical_decoder, frozen max_iter=90,
damping=1.0). Never a CLI phase entry. Per-call wall recorded (120 s budget;
formal evidence ~0.5 s/call, in-process timing used as the watchdog record).
"""
import importlib.util
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("v72p2d5_core_diag2", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

import numpy as np  # noqa: E402

_rss = core._rss_bytes

t_all = time.perf_counter()
ev = {"batch": 2, "decoder_calls": 0, "watchdog_s": 120, "diagnostics": []}

h1 = core.build_dv3_nested_mother(64, core.G1_L1_K_MIN, core.G1_L1_K_MIN,
                                  core.L1_GRAPH_SEED, None)
h2 = core.build_dv3_nested_mother(64, core.G1_L2_K_MIN, core.G1_L2_K_MIN,
                                  core.L2_GRAPH_SEED, None)
targets = {"H1[:49]": np.asarray(h1[:49], dtype=np.int64),
           "H1[:59]": np.asarray(h1[:59], dtype=np.int64),
           "H2[:43]": np.asarray(h2[:43], dtype=np.int64),
           "H2[:52]": np.asarray(h2[:52], dtype=np.int64)}

dec = core.bind_historical_decoder()  # frozen MAX_ITER=90, DAMPING_ALPHA=1.0
xrng = np.random.default_rng(2026090701)


def watchdog_call(h, prior, syn):
    t0 = time.perf_counter()
    res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
              np.asarray(syn))
    wall = time.perf_counter() - t0
    return res, wall


for name, h in targets.items():
    n = h.shape[1]
    x_true = xrng.integers(0, 32, size=(n,)).astype(np.int64)
    syn = core._gf32_syndrome(h, x_true)
    # T-a: delta prior
    prior_a = np.zeros((n, 32))
    prior_a[np.arange(n), x_true] = 1.0
    (ra, wa) = watchdog_call(h, prior_a, syn)
    xa = np.asarray(ra["x_hat"], dtype=np.int64).ravel()
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": f"T-a@{name}", "decoder_calls": 1, "changed_axis": "none",
        "input": "delta prior on rng(2026090701) word; frozen prefix; "
                 "frozen decoder",
        "n": n, "m": int(h.shape[0]),
        "syndrome_weight": int(np.count_nonzero(syn)),
        "exact": bool(np.array_equal(xa, x_true)),
        "syndrome_ok": bool(ra["syndrome_ok"]), "iterations": int(ra["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(np.asarray(
            ra["final_beliefs"], dtype=np.float64)))),
        "wall_s": wa,
        "rss_bytes": _rss(),
        "result": "adapter-path sanity",
    })
    # T-b: strong 0.85 prior
    prior_b = np.full((n, 32), 0.15 / 31)
    prior_b[np.arange(n), x_true] = 0.85
    (rb, wb) = watchdog_call(h, prior_b, syn)
    xb = np.asarray(rb["x_hat"], dtype=np.int64).ravel()
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": f"T-b@{name}", "decoder_calls": 1, "changed_axis": "none",
        "input": "0.85-on-truth prior on same word; frozen prefix; "
                 "frozen decoder",
        "n": n, "m": int(h.shape[0]),
        "syndrome_weight": int(np.count_nonzero(syn)),
        "exact": bool(np.array_equal(xb, x_true)),
        "syndrome_ok": bool(rb["syndrome_ok"]), "iterations": int(rb["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(np.asarray(
            rb["final_beliefs"], dtype=np.float64)))),
        "wall_s": wb,
        "rss_bytes": _rss(),
        "result": "decode-with-signal machinery",
    })

tb_fail = [d for d in ev["diagnostics"] if d["id"].startswith("T-b") and not d["exact"]]
if tb_fail:
    # T-c control on the known-good G0 tiny fixture matrix (recovery PASS family)
    h_fix, _, _ = core.build_g0_fixture()
    h_tiny = np.asarray(h_fix["L2"], dtype=np.int64)
    n = h_tiny.shape[1]
    x_true = xrng.integers(0, 32, size=(n,)).astype(np.int64)
    syn = core._gf32_syndrome(h_tiny, x_true)
    prior_c = np.full((n, 32), 0.15 / 31)
    prior_c[np.arange(n), x_true] = 0.85
    (rc, wc) = watchdog_call(h_tiny, prior_c, syn)
    xc = np.asarray(rc["x_hat"], dtype=np.int64).ravel()
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": "T-c@G0tiny8x8", "decoder_calls": 1,
        "changed_axis": "matrix only (G1 prefix -> known-good tiny cycle)",
        "input": "0.85-on-truth prior; G0 fixture 8x8; frozen decoder",
        "n": n, "m": int(h_tiny.shape[0]),
        "syndrome_weight": int(np.count_nonzero(syn)),
        "exact": bool(np.array_equal(xc, x_true)),
        "syndrome_ok": bool(rc["syndrome_ok"]),
        "iterations": int(rc["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(np.asarray(
            rc["final_beliefs"], dtype=np.float64)))),
        "wall_s": wc,
        "rss_bytes": _rss(),
        "result": "matrix-vs-decoder control",
    })

ev["wall_s"] = time.perf_counter() - t_all
with open(OUT / "diag02_decode_sanity.json", "w", encoding="utf-8") as fh:
    json.dump(ev, fh, indent=2, sort_keys=True)
print(json.dumps({"calls": ev["decoder_calls"], "wall_s": ev["wall_s"],
                  "summary": [(d["id"], d["exact"], d["syndrome_ok"],
                               d["iterations"], round(d["wall_s"], 3))
                              for d in ev["diagnostics"]]}, indent=1))
