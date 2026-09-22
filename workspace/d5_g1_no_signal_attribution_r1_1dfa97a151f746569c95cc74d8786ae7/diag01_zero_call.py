"""D5-G1 attribution R1 — batch 1: zero decoder-call diagnostics (AC04 support + AC05 a/c/d).

Reads only: accepted Model-F NPZ, frozen core source (by file path, no phase
entry), valid G1 scalars (hardcoded literals from direct reads, not recomputed
via CLI). Writes only to this attribution workspace dir.

D1: actual Model-F CE vs frozen CE constants + implied disclosure rows.
D2: rebuild G1-width mothers exactly as formal defaults; audit frozen prefixes.
D3: GF32 arithmetic cross-check core vs historical v35 tables + syndrome/rank.
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("v72p2d5_core_diag", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

import numpy as np  # noqa: E402

t0 = time.perf_counter()
ev = {"batch": 1, "decoder_calls": 0, "diagnostics": []}

# ---- D1: Model-F actual CE vs frozen constants (read-only NPZ) ----
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb_raw = np.asarray(npz["p_b"], dtype=np.float64)
pb = pb_raw / pb_raw.sum()
pf = core.build_f_model(counts, core.LAMBDA_STAR)
joint, l1, l2, p1, p2 = core._ce_stats(pf, pb)
rows = {}
for f in (1.0, 1.2):
    rows[str(f)] = {
        "m1_actual": int(__import__("math").ceil(64 * l1 * f / 5.0)),
        "m2_actual": int(__import__("math").ceil(64 * l2 * f / 5.0)),
        "m1_frozen": core._rows_required(core.CE_L1_MEAN, 64, f),
        "m2_frozen": core._rows_required(core.CE_L2_ORACLE_MEAN, 64, f),
    }
# prior sharpness texture: E[max P1(.|B)], E[entropy P1], oracle-L2 entropy
colmax = p1.max(axis=0)
sharp = float((pb * colmax).sum())
ent1 = float(-(pb * (np.maximum(p1, 1e-300) * np.log2(np.maximum(p1, 1e-300))).sum(axis=0)).sum())
p2mv = np.moveaxis(p2, 1, 0)  # (B, U1, U2)
ent2 = float(-(pb[:, None, None]
               * np.moveaxis(p1, 1, 0)[:, :, None]
               * np.maximum(p2mv, 1e-300) * np.log2(np.maximum(p2mv, 1e-300))).sum())
ev["diagnostics"].append({
    "id": "D1", "decoder_calls": 0, "changed_axis": "none (read-only)",
    "input": "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz",
    "pb_sum_raw": float(pb_raw.sum()),
    "pf_col_norm_maxerr": float(np.max(np.abs(pf.sum(axis=0) - 1.0))),
    "joint_actual": joint, "l1_actual": l1, "l2_actual": l2,
    "frozen": {"ce_l1": core.CE_L1_MEAN, "ce_l2_oracle": core.CE_L2_ORACLE_MEAN,
               "ce_joint": core.CE_JOINT_MEAN},
    "rows_width64": rows,
    "prior_E_maxP1": sharp, "entropy_P1_bits": ent1, "entropy_P2_bits": ent2,
})

# ---- D2: rebuild G1-width mothers as formal defaults; audit frozen prefixes ----
h1 = core.build_dv3_nested_mother(64, core.G1_L1_K_MIN, core.G1_L1_K_MIN,
                                  core.L1_GRAPH_SEED, None)
h2 = core.build_dv3_nested_mother(64, core.G1_L2_K_MIN, core.G1_L2_K_MIN,
                                  core.L2_GRAPH_SEED, None)
assert h1.shape == (59, 64) and h2.shape == (52, 64)
prefixes = {"H1[:49]": (h1, 49), "H1[:59]": (h1, 59),
            "H2[:43]": (h2, 43), "H2[:52]": (h2, 52)}
aud = {}
for name, (h, k) in prefixes.items():
    a = core.audit_prefix(h, k)
    aud[name] = {kk: a[kk] for kk in (
        "prefix_rows", "total_edges", "rank", "zero_rows", "zero_columns",
        "variable_degree_min", "variable_degree_median", "variable_degree_max",
        "degree1_variables", "degree2_variables", "degree3_variables",
        "connected_components", "largest_component_fraction",
        "isolated_variables", "four_cycles",
        "four_cycle_variable_incidence_max", "duplicate_projective_columns",
        "base_pair_duplicates", "support_triple_duplicates",
        "coefficients_nonzero", "passed", "status")}
ev["diagnostics"].append({"id": "D2", "decoder_calls": 0,
                          "changed_axis": "none (construction = formal defaults)",
                          "input": "L1 mother (64,59,59,seed 2026090501); "
                                   "L2 mother (64,52,52,seed 2026090502)",
                          "h1_shape": list(h1.shape), "h2_shape": list(h2.shape),
                          "prefix_audits": aud})

# ---- D3: GF32 cross-check core vs historical v35 (import only, no decode) ----
src_root = str(CORE_PATH.resolve().parents[2])
if src_root not in sys.path:
    sys.path.insert(0, src_root)
v35 = importlib.import_module(
    "comparison_bench.formal_ir.v35_algorithm_development")
from comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
    GF2mField, get_field_spec)
spec37 = get_field_spec(32)
fld = GF2mField.create(32)
mul_tab, add_tab, inv_tab = v35._get_gf32_tables(fld)
mm = np.zeros((32, 32), dtype=np.uint8)
for i in range(32):
    for j in range(32):
        mm[i, j] = core._gf32_mul_raw(i, j)
mul_match = bool(np.array_equal(mm, mul_tab))
add_match = bool(np.all(add_tab == (np.arange(32)[:, None] ^ np.arange(32)[None, :])))
rng = np.random.default_rng(20260907)
syn_match, rank_match = True, True
for (h, k) in prefixes.values():
    pk = np.asarray(h[:k], dtype=np.int64)
    for _ in range(3):
        x = rng.integers(0, 32, size=(pk.shape[1],))
        s_core = core._gf32_syndrome(pk, x)
        s_v35 = np.asarray(v35.syndrome_of_gf32(
            pk.astype(np.uint8), x.astype(np.uint8), fld), dtype=np.int64)
        if not np.array_equal(s_core, s_v35):
            syn_match = False
    if core._gf32_rank(pk) != int(v35.compute_gf32_rank(
            pk.astype(np.uint8), fld)):
        rank_match = False
ev["diagnostics"].append({
    "id": "D3", "decoder_calls": 0, "changed_axis": "none (table/code read)",
    "input": "core GF32 fns vs v35 GF2mField.create(32) + frozen G1 prefixes",
    "field_spec": str(spec37), "mul_table_match": mul_match,
    "add_is_xor": add_match, "syndrome_match_12trials": syn_match,
    "rank_match_4prefixes": rank_match})

ev["wall_s"] = time.perf_counter() - t0
with open(OUT / "diag01_zero_call.json", "w", encoding="utf-8") as fh:
    json.dump(ev, fh, indent=2, sort_keys=True)
print(json.dumps({"D1": ev["diagnostics"][0], "D2": {
    k: {kk: v[kk] for kk in ("rank", "zero_rows", "zero_columns",
                             "variable_degree_min", "connected_components",
                             "largest_component_fraction", "four_cycles",
                             "duplicate_projective_columns",
                             "base_pair_duplicates",
                             "support_triple_duplicates", "passed", "status")}
    for k, v in aud.items()},
    "D3": ev["diagnostics"][2], "wall_s": ev["wall_s"]}, indent=1))
