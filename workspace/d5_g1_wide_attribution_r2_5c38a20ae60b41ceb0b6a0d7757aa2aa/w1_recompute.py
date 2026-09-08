"""R2 W1: independent recomputation of R1 facts (0 decoder calls, read-only).

Reads accepted Model-F NPZ + D4R2 audit.json + G1 results.json + R1 diag JSONs.
No CLI --phase, no formal-root write, no VAL, no decoder.
"""
import importlib.util
import json
import math
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")

spec = importlib.util.spec_from_file_location("v72p2d5_core_w1", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

t_all = time.perf_counter()
ev = {"workstream": "W1", "decoder_calls": 0, "checks": {}}

# ---- accepted Model-F input (read-only) ----
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.int64)
pb0 = np.asarray(npz["p_b"], dtype=np.float64)
pb = pb0 / pb0.sum()
N_CAL = int(counts.sum())
Q = 1024
ev["checks"]["counts_sum"] = N_CAL
ev["checks"]["counts_shape"] = list(counts.shape)
ev["checks"]["nonzero_cells"] = int(np.count_nonzero(counts))
ev["checks"]["cell_mean"] = float(counts.mean())
ev["checks"]["cell_max"] = int(counts.max())
ev["checks"]["colsum_min"] = int(counts.sum(axis=0).min())
ev["checks"]["colsum_max"] = int(counts.sum(axis=0).max())
ev["checks"]["colsum_mean"] = float(counts.sum(axis=0).mean())

LAM = float(core.LAMBDA_STAR)
ev["checks"]["lambda_star"] = LAM

# ---- accepted consumer ----
pf_acc = core.build_f_model(counts.astype(np.float64), LAM)
joint, l1, l2, p1, p2 = core._ce_stats(pf_acc, pb)
ev["checks"]["consumer_ce_joint"] = joint
ev["checks"]["consumer_ce_l1"] = l1
ev["checks"]["consumer_ce_l2"] = l2
# column-normalization max err
ev["checks"]["pf_col_norm_maxerr"] = float(np.max(np.abs(pf_acc.sum(axis=0) - 1.0)))
ev["checks"]["pb_sum"] = float(pb.sum())

# H(Alice), H(Bob), I(A;B) under accepted (pb, pf)
pa = (pf_acc * pb[None, :]).sum(axis=1)
pa = pa / pa.sum()
H_A = float(-np.sum(pa * np.log2(np.maximum(pa, 1e-300))))
H_B = float(-np.sum(pb * np.log2(np.maximum(pb, 1e-300))))
ev["checks"]["H_alice_bits"] = H_A
ev["checks"]["H_bob_bits"] = H_B
ev["checks"]["MI_AB_bits"] = float(H_A - joint)

# smoothing contribution: lam=0 raw empirical vs accepted vs backoff
pf_raw = core.build_f_model(counts.astype(np.float64), 0.0)
j0, l1_0, l2_0, _, _ = core._ce_stats(pf_raw, pb)
ev["checks"]["raw_ce_joint"] = j0
ev["checks"]["raw_ce_l1"] = l1_0
ev["checks"]["raw_ce_l2"] = l2_0
# effective prior mass per column under per-cell smoothing (mean col)
n_b_mean = float(counts.sum(axis=0).mean())
eff = (Q * LAM) / (n_b_mean + Q * LAM)
ev["checks"]["percell_added_per_col"] = float(Q * LAM)
ev["checks"]["percell_effective_prior_frac"] = float(eff)
ev["checks"]["percell_dominance_ratio"] = float((Q * LAM) / n_b_mean)

# D4R2-F backoff rebuilt from same counts (frozen math copy, read-only ref)
n_b = counts.sum(axis=0).astype(np.float64)
p_global = counts.sum(axis=1).astype(np.float64) / float(N_CAL)
pf_bo = (counts.astype(np.float64) + LAM * p_global[:, None]) / (n_b[None, :] + LAM)
jb, l1b, l2b, p1b, p2b = core._ce_stats(pf_bo, pb)
ev["checks"]["backoff_ce_joint"] = jb
ev["checks"]["backoff_ce_l1"] = l1b
ev["checks"]["backoff_ce_l2"] = l2b
ev["checks"]["backoff_col_norm_maxerr"] = float(np.max(np.abs(pf_bo.sum(axis=0) - 1.0)))
# chain-split equivalence: consumer marginalize vs D4 cube split
cube = pf_bo.reshape(32, 32, Q)
p_u1_D4 = cube.sum(axis=1).T  # [B,U1]
p1_bo_T = np.asarray(p1b)  # [U1,B]
ev["checks"]["axis_split_maxerr"] = float(np.max(np.abs(p_u1_D4 - p1_bo_T.T)))

# truth prior mass on paired frozen seeds (sampling only, 0 decoder calls)
masses = []
for sd in (2026090600, 2026090601, 2026090602, 2026090603):
    blk = core.sample_matched_block(pb, pf_acc, 64, sd)
    m1v = float(np.mean(p1[blk["u1"], blk["bob"]]))
    po = core.oracle_l2_prior(p2, blk["bob"], blk["u1"])
    m2v = float(np.mean(po[np.arange(64), blk["u2"]]))
    masses.append({"seed": sd, "p1_mass": m1v, "oracle_p2_mass": m2v})
ev["checks"]["truth_mass_accepted"] = masses

# ---- D4R2 provenance (read-only audit.json) ----
audit = json.loads((REPO / "comparison_bench/outputs_comparison"
                    / "v72p2d4r2_cal_gf32_model_rate_audit_20260905"
                    / "audit.json").read_text(encoding="utf-8"))
folds = audit["outer_results"]
ml1 = sum(r["F"]["ce_l1"] for r in folds) / 4
ml2 = sum(r["F"]["ce_l2_oracle"] for r in folds) / 4
mj = sum(r["F"]["ce_joint"] for r in folds) / 4
ev["checks"]["d4_outer_F_means"] = {"ce_l1": ml1, "ce_l2": ml2, "ce_joint": mj}
ev["checks"]["d4_frozen_match"] = {
    "ce_l1": abs(ml1 - core.CE_L1_MEAN) < 1e-9,
    "ce_l2": abs(ml2 - core.CE_L2_ORACLE_MEAN) < 1e-9,
    "ce_joint": abs(mj - core.CE_JOINT_MEAN) < 1e-9,
}
ev["checks"]["d4_selected"] = audit["selection"]["selected"]
ev["checks"]["d4_inner_lams"] = [s["selected_lam"] for s in audit["inner_selections"]]

# ---- G1 rows formula ----
ev["checks"]["g1_rows_recomputed"] = {
    str(f): {"m1": core._rows_required(core.CE_L1_MEAN, 64, f),
             "m2": core._rows_required(core.CE_L2_ORACLE_MEAN, 64, f)}
    for f in (1.0, 1.2)
}
g1 = json.loads((REPO / "workspace/v72p2d5_g1/20260907_r2/results.json")
                .read_text(encoding="utf-8"))
ev["checks"]["g1_frozen_rows_match"] = (
    g1["frozen_rows"] == ev["checks"]["g1_rows_recomputed"])
ev["checks"]["g1_calls_match"] = (g1["decoder_calls"] == 440)
ev["checks"]["g1_app_calls_arith"] = (100 * 2 * 2 == 400)
ev["checks"]["g1_oracle_calls_arith"] = (20 * 1 * 2 == 40)

# ---- R1 scalars + accounting ----
R1 = REPO / "workspace/d5_g1_no_signal_attribution_r1_1dfa97a151f746569c95cc74d8786ae7"
d1 = json.loads((R1 / "diag01_zero_call.json").read_text(encoding="utf-8"))
d2 = json.loads((R1 / "diag02_decode_sanity.json").read_text(encoding="utf-8"))
d3 = json.loads((R1 / "diag03_paired_controls.json").read_text(encoding="utf-8"))
ev["checks"]["r1_d1_l1_match"] = abs(d1["diagnostics"][0]["l1_actual"] - l1) < 1e-9
ev["checks"]["r1_d1_l2_match"] = abs(d1["diagnostics"][0]["l2_actual"] - l2) < 1e-9
ev["checks"]["r1_d1_joint_match"] = abs(d1["diagnostics"][0]["joint_actual"] - joint) < 1e-9
calls = d1["decoder_calls"] + d2["decoder_calls"] + d3["decoder_calls"]
ev["checks"]["r1_total_calls"] = calls
ev["checks"]["r1_calls_is_29"] = (calls == 29)

ev["wall_s"] = time.perf_counter() - t_all
ev["rss_bytes"] = core._rss_bytes()
(OUT / "w1_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                      encoding="utf-8")
print(json.dumps(ev["checks"], indent=1)[:4000])
print("W1 wall", ev["wall_s"], "rss", ev["rss_bytes"])
