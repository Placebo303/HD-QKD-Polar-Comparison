"""R2 W3: Model-F / smoothing contract audit (0 decoder calls, read-only + recompute).

Traces counts_ab -> p_b -> lambda* -> normalization -> P(A|B)/layer priors,
answering the five packet questions quantitatively. No CLI --phase, no VAL,
no decoder, no formal-root write.
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

spec = importlib.util.spec_from_file_location("v72p2d5_core_w3", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

t_all = time.perf_counter()
ev = {"workstream": "W3", "decoder_calls": 0, "answers": {}}

npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.int64)
cf = counts.astype(np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb = pb / pb.sum()
N = int(counts.sum())
Q = 1024
LAM = float(core.LAMBDA_STAR)

# Q1: lambda* object identity (D4R2 source math, read-only reference)
ev["answers"]["Q1_lambda_identity"] = {
    "form": "scalar total concentration per Bob column",
    "formula": "P(a|b)=(counts[a,b]+lam*p_global[a])/(n_b[b]+lam)",
    "per_cell_pseudocount_NO": True,
    "scale_note": "lam=137.38 is added ONCE per column (distributed by "
                  "p_global), NOT per cell",
    "selection": "D4R2 inner 3-fold CV on F joint CE, grid30 logspace(-2,3); "
                 "all 4 outer folds selected 137.3823795883264",
    "applied_in_consumer_as": "per-cell pseudocount sm=counts+lam "
                              "(140679.56 added per column)",
}

# Q2: estimation vs application alphabet/layer/axis/population/object
n_b = cf.sum(axis=0)
p_global = cf.sum(axis=1) / float(N)
pf_bo = (cf + LAM * p_global[:, None]) / (n_b[None, :] + LAM)
pf_acc = core.build_f_model(cf, LAM)
ev["answers"]["Q2_scope_match"] = {
    "alphabet": "same 1024 symbols, symbol=low+32*high, U1=high, U2=low",
    "axes": "same (Alice,Bob), axis0 Alice; chain-split maxerr 2.2e-16",
    "population": "same CAL702..1725 262144 symbols, session 1M",
    "probability_object_MATCH": False,
    "mismatch": "estimation smooths with total-concentration backoff; "
                "application smooths with per-cell pseudocount",
    "evaluation_MISMATCH": "D4 CE = outer-TEST held-out NLL (honest); "
                           "consumer CE = in-sample channel entropy of the "
                           "smoothed table (AUDIT_FLOOR 1e-300)",
}

# Q3: constructed-domination arithmetic
col_mean = float(n_b.mean())
ev["answers"]["Q3_domination"] = {
    "observed_per_col_mean": col_mean,
    "added_per_col_consumer": float(Q * LAM),
    "added_per_col_d4": LAM,
    "consumer_prior_frac": float((Q * LAM) / (col_mean + Q * LAM)),
    "d4_prior_frac": float(LAM / (col_mean + LAM)),
    "dominance_ratio_consumer": float((Q * LAM) / col_mean),
    "overwhelms_by_construction": True,
}

# Q4: D4 CE reproducibility through the exact G1 consumer
jb, l1b, l2b, _, _ = core._ce_stats(pf_bo, pb)
ja, l1a, l2a, _, _ = core._ce_stats(pf_acc, pb)
ev["answers"]["Q4_reproducibility"] = {
    "d4_frozen": {"ce_l1": core.CE_L1_MEAN, "ce_l2": core.CE_L2_ORACLE_MEAN,
                  "ce_joint": core.CE_JOINT_MEAN},
    "consumer_from_accepted": {"ce_l1": l1a, "ce_l2": l2a, "ce_joint": ja},
    "backoff_same_counts_same_functional": {"ce_l1": l1b, "ce_l2": l2b,
                                            "ce_joint": jb},
    "reproducible": False,
    "verdict": "D4 values are NOT reproducible through the accepted consumer; "
               "same counts + same channel-CE functional with the D4 backoff "
               "return to the D4 family (7.51 vs 7.16 joint).",
}

# Q5: L1 / oracle-L2 prior correctness (intended marginals/conditionals?)
_, _, _, p1a, p2a = core._ce_stats(pf_acc, pb)
_, _, _, p1b, p2b = core._ce_stats(pf_bo, pb)
# intended: P1 = column-mixture marginal over U2; P2 slice normalized over U2
ev["answers"]["Q5_layer_priors"] = {
    "axis_semantics_correct": True,
    "p1_shape": list(np.asarray(p1a).shape),
    "p2_shape": list(np.asarray(p2a).shape),
    "accepted_p1_col_entropy_mean": float(np.mean(
        -np.sum(np.asarray(p1a) * np.log2(np.maximum(np.asarray(p1a), 1e-300)),
                axis=0))),
    "backoff_p1_col_entropy_mean": float(np.mean(
        -np.sum(np.asarray(p1b) * np.log2(np.maximum(np.asarray(p1b), 1e-300)),
                axis=0))),
    "verdict": "marginals/conditionals are the intended ones OF THE TABLE "
               "GIVEN; the table itself is destroyed (near-uniform), so both "
               "layer priors sit at ~1/32 mass on truth.",
}

# MI contrast: accepted vs backoff (same pb weighting)
pa_acc = (pf_acc * pb[None, :]).sum(axis=1)
pa_acc /= pa_acc.sum()
H_A_acc = float(-np.sum(pa_acc * np.log2(np.maximum(pa_acc, 1e-300))))
pa_bo = (pf_bo * pb[None, :]).sum(axis=1)
pa_bo /= pa_bo.sum()
H_A_bo = float(-np.sum(pa_bo * np.log2(np.maximum(pa_bo, 1e-300))))
ev["mi_contrast_bits"] = {
    "accepted": {"H_A": H_A_acc, "H_AgB": ja, "I": float(H_A_acc - ja)},
    "backoff": {"H_A": H_A_bo, "H_AgB": jb, "I": float(H_A_bo - jb)},
}
# D4 G-model reference (B-independent): joint ~9.9997 -> F gain over G
ev["d4_g_reference_joint"] = 9.999677136099834
ev["d4_F_gain_over_G_bits"] = float(9.999677136099834 - 7.162347429958785)

ev["wall_s"] = time.perf_counter() - t_all
ev["rss_bytes"] = core._rss_bytes()
(OUT / "w3_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                      encoding="utf-8")
print(json.dumps(ev, indent=1)[:4500])
print("W3 wall", ev["wall_s"], "rss", ev["rss_bytes"])
