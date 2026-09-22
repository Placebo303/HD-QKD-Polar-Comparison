"""R2 W6 candidate diagnostics: committed candidate path on accepted NPZ.

Uses ONLY the newly committed prepare_model_f_prior_candidate (0 decoder
calls, read-only NPZ). Pass criteria (from W4a C1, same math):
joint~7.5094, l1~4.2867, l2~3.2227, truth-mass mean ~0.254 (8x uniform).
"""
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")

spec = importlib.util.spec_from_file_location("v72p2d5_core_w6", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

t_all = time.perf_counter()
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"])
pb_in = np.asarray(npz["p_b"], dtype=np.float64)

pb, pf = core.prepare_model_f_prior_candidate(counts, pb_in)
joint, l1, l2, p1, p2 = core._ce_stats(pf, pb)
masses = []
for sd in (2026090600, 2026090601, 2026090602, 2026090603):
    blk = core.sample_matched_block(pb, pf, 64, sd)
    po = core.oracle_l2_prior(p2, blk["bob"], blk["u1"])
    masses.append(float(np.mean(po[np.arange(64), blk["u2"]])))
tm = sum(masses) / len(masses)
ok = (abs(joint - 7.5094403148357545) < 1e-9
      and abs(l1 - 4.286720430201375) < 1e-9
      and abs(l2 - 3.222719884634378) < 1e-9
      and abs(tm - 0.25444987775455336) < 1e-9)
ev = {"workstream": "W6-diagnostics", "decoder_calls": 0,
      "ce_joint": joint, "ce_l1": l1, "ce_l2": l2, "truth_mass_mean": tm,
      "pass": bool(ok), "wall_s": time.perf_counter() - t_all,
      "rss_bytes": core._rss_bytes()}
(OUT / "w6_candidate_check.json").write_text(json.dumps(ev, indent=2) + "\n",
                                             encoding="utf-8")
print(json.dumps(ev, indent=1))
assert ok, "candidate diagnostics FAIL"
print("CANDIDATE_DIAGNOSTICS_PASS")
