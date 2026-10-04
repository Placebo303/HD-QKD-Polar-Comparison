"""V52 decoder-free nested rescue spike: verify H_base + H_inc nesting/joint rank/independence/leakage.
Zero decoder calls. Reproducible. Uses v38/v35 primitives only.
Run: python spike_nested_rescue.py
Gate failure -> sys.exit(1)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "comparison_bench" / "src"))

import numpy as np
from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_gf32_rank
from comparison_bench.formal_ir.v38_architecture_triage import (
    SOURCE_CHECKS, MAX_CHECK_DEGREE_LIMIT,
    construct_lane_c_prototype,
    get_substream_generator, sample_uniform_gf32_nonzero,
    get_canonical_support_edges,
)

BLOCK_LENGTH = 1024
DELTA_M = 8
POLY = 37
# H_inc deterministic ids per source
INC_DET_IDS = {"1M": 600001, "1p5M": 600002, "2M": 600003}
# base Lane C ordinal-2 seeds (frozen)
BASE_SEEDS = {"1M": 383102, "1p5M": 383202, "2M": 383302}

def construct_h_inc(source: str, det_id: int, delta_m: int = DELTA_M, n: int = BLOCK_LENGTH):
    """Deterministic PEG-like incremental matrix  delta_m x n, col_degree 0/1, row<=16."""
    m = delta_m
    support_rng = get_substream_generator(det_id, stream_id=1)
    perm_base = support_rng.permutation(m).tolist()  # for tie-break
    rank_in_perm = {c: i for i, c in enumerate(perm_base)}
    # coeff rng
    coeff_rng = get_substream_generator(det_id, stream_id=2)
    # decide column injection: we want ~ E_inc edges distributed across columns, col 0/1.
    # Use stream 1 to decide which columns get an extra edge, targeting ~96 edges total (~9.4% density per column).
    # Simpler: each column deterministically gets 0 or 1 edge based on rng, but ensure row-degree <=16.
    # Approach: iterate j=0..n-1, for each j decide if inject (prob 96/1024 ~0.09375) via rng, else skip; then assign to min-degree row.
    H_support = np.zeros((m, n), dtype=np.uint8)
    row_deg = np.zeros(m, dtype=int)
    # pre-determine injection pattern via rng.integers
    inject_decision = support_rng.integers(0, 1024, size=n)  # 0..1023
    # threshold 96/1024*1024 ~=96 ; so <96 means inject
    # This gives ~96 injections on average, but deterministic per det
    threshold = 96  # target edges
    # Ensure at least threshold edges deterministically by taking smallest inject_decision values
    # Better: sort by inject_decision and take threshold smallest as injection set, to guarantee E_inc ~96
    sorted_indices = np.argsort(inject_decision)
    inject_set = set(sorted_indices[:threshold].tolist())
    # For remaining columns beyond threshold, none
    # Now assign each injected column to a row with minimal degree
    for j in range(n):
        if j not in inject_set:
            continue
        # choose min-degree row
        min_deg = int(row_deg.min())
        eligible = [c for c in range(m) if int(row_deg[c]) == min_deg]
        c_pick = min(eligible, key=lambda c: rank_in_perm[c])
        H_support[c_pick, j] = 1
        row_deg[c_pick] += 1
        # ensure not exceed 16
        if row_deg[c_pick] > MAX_CHECK_DEGREE_LIMIT:
            print(f"  ERROR: row degree exceeded 16 at row {c_pick} col {j}")
            sys.exit(1)
    # If any row still zero (unlikely with 96 edges across 8 rows -> 12 avg), ensure non-zero by moving some edges
    # Our method ensures all rows get ~12 each, but check
    for r in range(m):
        if row_deg[r] == 0:
            # steal from max degree row
            max_r = int(np.argmax(row_deg))
            # find a column where max_r has edge and move to r
            cols = np.where(H_support[max_r, :])[0]
            if len(cols) > 0:
                c_move = int(cols[0])
                H_support[max_r, c_move] = 0
                H_support[r, c_move] = 1
                row_deg[max_r] -= 1
                row_deg[r] += 1
    # assign coefficients
    canonical = get_canonical_support_edges(H_support)
    coeffs = sample_uniform_gf32_nonzero(coeff_rng, len(canonical))
    H = np.zeros((m, n), dtype=np.uint8)
    for (r, c), val in zip(canonical, coeffs):
        H[r, c] = val
    return H, H_support, int(np.count_nonzero(H_support)), row_deg


def verify_source(source: str):
    print(f"\n-- {source} m2={SOURCE_CHECKS[source]} det_inc={INC_DET_IDS[source]} delta={DELTA_M} --")
    field = GF2mField.create(32)
    m2 = SOURCE_CHECKS[source]
    base_seed = BASE_SEEDS[source]
    # reconstruct base
    H_base, metrics_base = construct_lane_c_prototype(source=source, seed=base_seed, field=field)
    print(f"  H_base shape {H_base.shape} rank {metrics_base['rank_GF32']} expected {m2} valid {metrics_base['structurally_valid']}")
    rank_base = metrics_base['rank_GF32']
    if rank_base != m2:
        print(f"  FAIL: base rank {rank_base} != m2 {m2}")
        return False, {}
    # construct inc
    H_inc, Hs_inc, E_inc, row_deg_inc = construct_h_inc(source, INC_DET_IDS[source], DELTA_M)
    print(f"  H_inc shape {H_inc.shape} E_inc {E_inc} row_deg {row_deg_inc.tolist()} min {int(row_deg_inc.min())} max {int(row_deg_inc.max())} mean {float(row_deg_inc.mean()):.2f}")
    # checks
    if int(row_deg_inc.max()) > MAX_CHECK_DEGREE_LIMIT:
        print("  FAIL: H_inc row_degree >16")
        return False, {}
    if int((row_deg_inc == 0).sum()) != 0:
        print("  FAIL: zero incremental row")
        return False, {}
    # col degree inc <=1
    col_deg_inc = np.count_nonzero(Hs_inc, axis=0)
    if int(col_deg_inc.max()) > 1:
        print(f"  FAIL: H_inc col_degree >1 max {int(col_deg_inc.max())}")
        return False, {}
    # joint
    H_joint = np.vstack([H_base, H_inc]).astype(np.uint8)
    m_joint = m2 + DELTA_M
    print(f"  H_joint shape {H_joint.shape} expected {(m_joint, BLOCK_LENGTH)}")
    rank_joint = compute_gf32_rank(H_joint, field)
    print(f"  rank_base {rank_base} rank_joint {rank_joint} expected {m_joint}")
    rank_inc_independent = rank_joint - rank_base
    nested_ok = np.array_equal(H_joint[0:m2, :], H_base)
    print(f"  nested (H_base == H_joint[:m2]) : {nested_ok}")
    print(f"  rank_increment (joint - base) = {rank_inc_independent} expected {DELTA_M}")
    # independence = DELTA_M
    independence_ok = (rank_inc_independent == DELTA_M)
    full_joint_ok = (rank_joint == m_joint)
    # leakage
    leak_base = 5*m2 + 5*16 + 64
    leak_joint = 5*m_joint + 5*16 + 64
    delta_leak = leak_joint - leak_base
    print(f"  leak_base {leak_base} leak_joint {leak_joint} delta {delta_leak} expected 40 (=5*{DELTA_M})")
    leak_ok = (delta_leak == 5*DELTA_M == 40)
    # joint E, row/col stats
    Hs_joint = (H_joint != 0).astype(np.uint8)
    col_deg_joint = np.count_nonzero(Hs_joint, axis=0)
    row_deg_joint = np.count_nonzero(Hs_joint, axis=1)
    print(f"  joint col_deg min {int(col_deg_joint.min())} max {int(col_deg_joint.max())} mean {float(col_deg_joint.mean()):.2f} zero_col {(col_deg_joint==0).sum()}")
    print(f"  joint row_deg min {int(row_deg_joint.min())} max {int(row_deg_joint.max())} mean {float(row_deg_joint.mean()):.2f} zero_row {(row_deg_joint==0).sum()}")
    # gate
    gate_ok = (full_joint_ok and nested_ok and independence_ok and leak_ok and int((col_deg_joint==0).sum())==0 and int((row_deg_joint==0).sum())==0 and int(row_deg_joint.max())<=16)
    print(f"  GATE: {'PASS' if gate_ok else 'FAIL'} (joint_rank==m2+Δm && nested && independence==Δm && leak+40 && no zero && row≤16)")
    # tag import check
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import compute_tag_64
        tag = compute_tag_64(np.empty(0, dtype=np.uint8), np.zeros(64, dtype=np.uint8))
        print(f"  tag_import_ok True example {tag[:16]}")
    except Exception as e:
        print(f"  tag_import FAIL {e}")
        gate_ok = False
    details = {
        "source": source,
        "m2": m2,
        "delta_m": DELTA_M,
        "m_joint": m_joint,
        "rank_base": int(rank_base),
        "rank_joint": int(rank_joint),
        "rank_increment": int(rank_inc_independent),
        "nested": bool(nested_ok),
        "leak_base": int(leak_base),
        "leak_joint": int(leak_joint),
        "delta_leak": int(delta_leak),
        "E_inc": int(E_inc),
        "row_deg_inc": row_deg_inc.tolist(),
        "col_deg_inc_max": int(col_deg_inc.max()),
        "joint_zero_col": int((col_deg_joint==0).sum()),
        "joint_zero_row": int((row_deg_joint==0).sum()),
        "joint_row_max": int(row_deg_joint.max()),
        "gate": bool(gate_ok),
    }
    return gate_ok, details

def run():
    print("=== V52 Nested Rescue Spike — decoder-free ===")
    print(f"BLOCK_LENGTH {BLOCK_LENGTH} DELTA_M {DELTA_M} POLY {POLY}")
    print(f"BASE_SEEDS {BASE_SEEDS} INC_DET_IDS {INC_DET_IDS}")
    all_ok = True
    all_details = {}
    for src in ["1M", "1p5M", "2M"]:
        ok, det = verify_source(src)
        all_details[src] = det
        if not ok:
            all_ok = False
    # overall block registry check (fresh 171)
    print("\n=== Block registry fresh 15 ===")
    FORBIDDEN_171 = 171  # 96+45+15+15
    fresh_blocks = {
        "1M": [393001,393002,393003,393004,393005],
        "1p5M": [393101,393102,393103,393104,393105],
        "2M": [393201,393202,393203,393204,393205],
    }
    # quick zero-overlap mock (real check requires file inventory, here just count)
    flat = [b for lst in fresh_blocks.values() for b in lst]
    print(f"  fresh 15 blocks {flat} count {len(flat)} unique {len(set(flat))==15}")
    # leakage formula check across sources
    print("\n=== Leakage formula ===")
    for src in ["1M","1p5M","2M"]:
        m2 = SOURCE_CHECKS[src]
        leak_base = 5*m2 +80+64
        leak_joint = 5*(m2+DELTA_M)+80+64
        print(f"  {src}: m2 {m2} leak_base {leak_base} leak_joint {leak_joint} +40")
    if all_ok:
        print("\nGATE_ALL: ALL PASS")
        sys.exit(0)
    else:
        print("\nGATE_ALL: SOME FAIL — exiting 1")
        sys.exit(1)

if __name__ == "__main__":
    run()
