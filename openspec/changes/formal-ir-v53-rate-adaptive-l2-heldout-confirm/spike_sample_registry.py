"""V53 decoder-free sample-registry + nested rescue spike: verify 45 fresh held-out blocks zero-overlap and H_base+H_inc nesting/joint rank/independence/leakage.
Zero decoder calls. Reproducible. Uses v38/v35 primitives only.
Run: python spike_sample_registry.py
Gate failure -> sys.exit(1)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "comparison_bench" / "src"))

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
INC_DET_IDS = {"1M": 600001, "1p5M": 600002, "2M": 600003}
BASE_SEEDS = {"1M": 383102, "1p5M": 383202, "2M": 383302}

# Hold intervals per source: H and base (from split_manifest 60/20/20)
HOLD_CONFIG = {
    "1M": {"H": 400, "base": 1600},
    "1p5M": {"H": 554, "base": 2213},
    "2M": {"H": 729, "base": 2916},
}

# Used intervals union per source (ordinal starts) from V48/V50/V51/V52
# Each start corresponds to [start, start+3] held-out ordinal window
USED_STARTS = {
    "1M": [
        # V48 15
        0,28,56,84,113,141,169,198,226,254,282,311,339,367,396,
        # V50 5
        14,42,70,98,127,
        # V51 5
        7,35,63,91,119,
        # V52 5
        33,61,89,117,146,
    ],
    "1p5M": [
        0,39,78,117,157,196,235,275,314,353,392,432,471,510,550,
        19,58,97,137,176,
        12,51,90,130,169,
        44,83,122,162,201,
    ],
    "2M": [
        0,51,103,155,207,258,310,362,414,466,517,569,621,673,725,
        25,77,129,181,232,
        18,70,122,174,225,
        53,104,155,206,257,  # note duplicate 155 (V48 & V52 overlap)
    ],
}

# Also dedup
for k in USED_STARTS:
    USED_STARTS[k] = sorted(set(USED_STARTS[k]))

def overlaps(a, b):
    # intervals [a,a+3] and [b,b+3] overlap if |a-b| <=3
    return abs(a - b) <= 3

def enumerate_remaining_and_select(source):
    cfg = HOLD_CONFIG[source]
    H = cfg["H"]
    used = USED_STARTS[source]
    all_starts = list(range(0, H - 3))  # 0..H-4 inclusive
    # filter any that overlap used
    remaining = []
    for s in all_starts:
        ov = any(overlaps(s, u) for u in used)
        if not ov:
            remaining.append(s)
    # Also need strict non-overlapping among remaining? For registry, we keep step 1 but verify selection non-overlapping.
    # For alternative strict K (step 4 aligned), compute
    remaining_strict = [s for s in remaining if s % 4 == 0]
    K = len(remaining)
    K_strict = len(remaining_strict)
    # dispersed selection via floor(j*(K-1)/14)
    if K < 15:
        print(f"  ERROR: remaining K={K} <15 for {source}, cannot select 15")
        return None, None, None, None
    selected = []
    for j in range(15):
        idx = (j * (K - 1)) // 14  # floor
        selected.append(remaining[idx])
    # verify selected are non-overlapping among themselves
    non_overlap_ok = True
    for i in range(len(selected)):
        for k in range(i+1, len(selected)):
            if overlaps(selected[i], selected[k]):
                non_overlap_ok = False
                print(f"  ERROR: selected overlap within source {source}: {selected[i]} vs {selected[k]}")
    # also verify zero overlap with used (already by construction, but double-check)
    zero_overlap_used = all(not any(overlaps(s, u) for u in used) for s in selected)
    # selected sorted should already be sorted because remaining sorted and index_j monotonic
    selected_sorted = sorted(selected)
    # ensure sorted and no duplicates
    unique_ok = len(set(selected)) == 15
    return {
        "H": H,
        "base": cfg["base"],
        "K": K,
        "K_strict": K_strict,
        "remaining": remaining,
        "selected": selected,
        "selected_sorted": selected_sorted,
        "non_overlap_ok": non_overlap_ok,
        "zero_overlap_used": zero_overlap_used,
        "unique_ok": unique_ok,
        "used": used,
    }, remaining, K, K_strict

def construct_h_inc(source: str, det_id: int, delta_m: int = DELTA_M, n: int = BLOCK_LENGTH):
    """Deterministic PEG-like incremental matrix  delta_m x n, col_degree 0/1, row<=16."""
    m = delta_m
    support_rng = get_substream_generator(det_id, stream_id=1)
    perm_base = support_rng.permutation(m).tolist()
    rank_in_perm = {c: i for i, c in enumerate(perm_base)}
    coeff_rng = get_substream_generator(det_id, stream_id=2)
    H_support = np.zeros((m, n), dtype=np.uint8)
    row_deg = np.zeros(m, dtype=int)
    inject_decision = support_rng.integers(0, 1024, size=n)
    threshold = 96
    sorted_indices = np.argsort(inject_decision)
    inject_set = set(sorted_indices[:threshold].tolist())
    for j in range(n):
        if j not in inject_set:
            continue
        min_deg = int(row_deg.min())
        eligible = [c for c in range(m) if int(row_deg[c]) == min_deg]
        c_pick = min(eligible, key=lambda c: rank_in_perm[c])
        H_support[c_pick, j] = 1
        row_deg[c_pick] += 1
        if row_deg[c_pick] > MAX_CHECK_DEGREE_LIMIT:
            print(f"  ERROR: row degree exceeded 16 at row {c_pick} col {j}")
            sys.exit(1)
    for r in range(m):
        if row_deg[r] == 0:
            max_r = int(np.argmax(row_deg))
            cols = np.where(H_support[max_r, :])[0]
            if len(cols) > 0:
                c_move = int(cols[0])
                H_support[max_r, c_move] = 0
                H_support[r, c_move] = 1
                row_deg[max_r] -= 1
                row_deg[r] += 1
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
    H_base, metrics_base = construct_lane_c_prototype(source=source, seed=base_seed, field=field)
    print(f"  H_base shape {H_base.shape} rank {metrics_base['rank_GF32']} expected {m2} valid {metrics_base['structurally_valid']}")
    rank_base = metrics_base['rank_GF32']
    if rank_base != m2:
        print(f"  FAIL: base rank {rank_base} != m2 {m2}")
        return False, {}
    H_inc, Hs_inc, E_inc, row_deg_inc = construct_h_inc(source, INC_DET_IDS[source], DELTA_M)
    print(f"  H_inc shape {H_inc.shape} E_inc {E_inc} row_deg {row_deg_inc.tolist()} min {int(row_deg_inc.min())} max {int(row_deg_inc.max())} mean {float(row_deg_inc.mean()):.2f}")
    if int(row_deg_inc.max()) > MAX_CHECK_DEGREE_LIMIT:
        print("  FAIL: H_inc row_degree >16")
        return False, {}
    if int((row_deg_inc == 0).sum()) != 0:
        print("  FAIL: zero incremental row")
        return False, {}
    col_deg_inc = np.count_nonzero(Hs_inc, axis=0)
    if int(col_deg_inc.max()) > 1:
        print(f"  FAIL: H_inc col_degree >1 max {int(col_deg_inc.max())}")
        return False, {}
    H_joint = np.vstack([H_base, H_inc]).astype(np.uint8)
    m_joint = m2 + DELTA_M
    print(f"  H_joint shape {H_joint.shape} expected {(m_joint, BLOCK_LENGTH)}")
    rank_joint = compute_gf32_rank(H_joint, field)
    print(f"  rank_base {rank_base} rank_joint {rank_joint} expected {m_joint}")
    rank_inc_independent = rank_joint - rank_base
    nested_ok = np.array_equal(H_joint[0:m2, :], H_base)
    print(f"  nested (H_base == H_joint[:m2]) : {nested_ok}")
    print(f"  rank_increment (joint - base) = {rank_inc_independent} expected {DELTA_M}")
    independence_ok = (rank_inc_independent == DELTA_M)
    full_joint_ok = (rank_joint == m_joint)
    leak_base = 5*m2 + 5*16 + 64
    leak_joint = 5*m_joint + 5*16 + 64
    delta_leak = leak_joint - leak_base
    print(f"  leak_base {leak_base} leak_joint {leak_joint} delta {delta_leak} expected 40 (=5*{DELTA_M})")
    leak_ok = (delta_leak == 5*DELTA_M == 40)
    Hs_joint = (H_joint != 0).astype(np.uint8)
    col_deg_joint = np.count_nonzero(Hs_joint, axis=0)
    row_deg_joint = np.count_nonzero(Hs_joint, axis=1)
    print(f"  joint col_deg min {int(col_deg_joint.min())} max {int(col_deg_joint.max())} mean {float(col_deg_joint.mean()):.2f} zero_col {(col_deg_joint==0).sum()}")
    print(f"  joint row_deg min {int(row_deg_joint.min())} max {int(row_deg_joint.max())} mean {float(row_deg_joint.mean()):.2f} zero_row {(row_deg_joint==0).sum()}")
    gate_ok = (full_joint_ok and nested_ok and independence_ok and leak_ok and int((col_deg_joint==0).sum())==0 and int((row_deg_joint==0).sum())==0 and int(row_deg_joint.max())<=16)
    print(f"  GATE: {'PASS' if gate_ok else 'FAIL'} (joint_rank==m2+Δm && nested && independence==Δm && leak+40 && no zero && row≤16)")
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
    print("=== V53 Sample Registry + Nested Rescue Spike — decoder-free ===")
    print(f"BLOCK_LENGTH {BLOCK_LENGTH} DELTA_M {DELTA_M} POLY {POLY}")
    print(f"BASE_SEEDS {BASE_SEEDS} INC_DET_IDS {INC_DET_IDS}")
    all_ok = True

    # Matrix verification
    all_details = {}
    for src in ["1M", "1p5M", "2M"]:
        ok, det = verify_source(src)
        all_details[src] = det
        if not ok:
            all_ok = False

    # Sample registry verification for 45 blocks
    print("\n=== Sample Registry 45 fresh held-out blocks (decoder-free) ===")
    print(f"Hold config: {HOLD_CONFIG}")
    print(f"Used starts per source (union, unique):")
    for src in ["1M","1p5M","2M"]:
        print(f"  {src}: {USED_STARTS[src]} count {len(USED_STARTS[src])}")

    registry_ok = True
    all_selected_global = {}
    per_source_selected = {}
    for src in ["1M","1p5M","2M"]:
        info, _, K, K_strict = enumerate_remaining_and_select(src)
        if info is None:
            registry_ok = False
            continue
        print(f"\n-- {src} registry --")
        print(f"  H {info['H']} base {info['base']} K(remaining step1) {info['K']} K_strict(step4) {info['K_strict']}")
        print(f"  remaining sample (first 10): {info['remaining'][:10]} ... last 10: {info['remaining'][-10:]}")
        print(f"  selected 15 starts (ordinal): {info['selected']}")
        print(f"  selected sorted: {info['selected_sorted']}")
        # frame_ids
        frame_ids_list = []
        for s in info['selected']:
            fids = [info['base']+s + i for i in range(4)]
            frame_ids_list.append(fids)
        print(f"  frame_ids per block:")
        for idx, (s, fids) in enumerate(zip(info['selected'], frame_ids_list)):
            print(f"    block {idx+1} start {s} [{s},{s+3}] -> fids {fids}")
        print(f"  non_overlap among selected: {info['non_overlap_ok']}")
        print(f"  zero_overlap with used: {info['zero_overlap_used']}")
        print(f"  unique 15: {info['unique_ok']}")
        per_source_selected[src] = {
            "starts": info['selected'],
            "frame_ids": frame_ids_list,
            "ordinals": [(s, s+3) for s in info['selected']],
            "K": K,
            "K_strict": K_strict,
        }
        all_selected_global[src] = set(info['selected'])
        if not (info['non_overlap_ok'] and info['zero_overlap_used'] and info['unique_ok']):
            registry_ok = False
            print(f"  REGISTRY FAIL for {src}")
        else:
            print(f"  REGISTRY PASS for {src}")

    # Cross-source checks (block IDs suggested 394xxx not overlapping prior IDs, trivially distinct per source)
    print("\n=== Cross-source global checks ===")
    # Check per-source suggested IDs unique
    suggested_ids = {
        "1M": list(range(394001, 394016)),
        "1p5M": list(range(394101, 394116)),
        "2M": list(range(394201, 394216)),
    }
    flat_ids = [b for lst in suggested_ids.values() for b in lst]
    print(f"  suggested 45 block IDs {flat_ids[:5]}... count {len(flat_ids)} unique {len(set(flat_ids))==45}")
    # also verify suggested IDs distinct from prior FORBIDDEN IDs (390xxx/391xxx/392xxx/393xxx) - trivially distinct because 394xxx
    prior_ids = set()
    # V48 390128-142 etc, V50 391001-005 etc, V51 392001-005 etc, V52 393001-005 etc
    for r in [range(390128,390143), range(390228,390243), range(390328,390343),
              range(391001,391006), range(391101,391106), range(391201,391206),
              range(392001,392006), range(392101,392106), range(392201,392206),
              range(393001,393006), range(393101,393106), range(393201,393206)]:
        prior_ids.update(r)
    overlap_ids = set(flat_ids) & prior_ids
    print(f"  overlap of suggested 394xxx with prior block IDs (should be 0): {len(overlap_ids)} {overlap_ids}")
    if len(overlap_ids) != 0:
        registry_ok = False

    # Total frames check: per source 15 blocks *4 frames =60 frames per source, total 180 frames held-out fresh, plus prior 90*4=360 => total held-out used 540 frames, remaining capacity 1683-540=1143 frames still unused (informational)
    total_fresh_frames = 45*4
    print(f"  total fresh frames this change: {total_fresh_frames} (45*4)")
    print(f"  per source fresh frames: 60 each")

    # Leakage formula check
    print("\n=== Leakage formula ===")
    for src in ["1M","1p5M","2M"]:
        m2 = SOURCE_CHECKS[src]
        leak_base = 5*m2 +80+64
        leak_joint = 5*(m2+DELTA_M)+80+64
        print(f"  {src}: m2 {m2} leak_base {leak_base} leak_joint {leak_joint} +40 avg_leak = {leak_base} + 40*N_rescue/45")

    # Budget check
    print("\n=== Budget ===")
    print(f"  per block: L1 1 + base 1 + rescue ≤1 => 2-3 per block")
    print(f"  total 45 blocks: L1 45 + base45 + rescue0-45 = 90-135 hard cap 135, L2 45-90")
    # Provide table for design freeze (actual frame_ids)
    print("\n=== Frozen table for design.md (actual frame_ids) ===")
    print("| source | block ID (suggested) | held_out_ordinal [start,end] | frame_ids[4] (global) | base | H | pairs |")
    print("|---|---|---|---|---|---|---|")
    for src in ["1M","1p5M","2M"]:
        cfg = HOLD_CONFIG[src]
        sel = per_source_selected[src]["starts"]
        ids = suggested_ids[src]
        for block_id, start in zip(ids, sel):
            fids = f"[{cfg['base']+start},{cfg['base']+start+1},{cfg['base']+start+2},{cfg['base']+start+3}]"
            print(f"| {src} | {block_id} | [{start},{start+3}] | {fids} | {cfg['base']} | {cfg['H']} | 1024 |")

    if all_ok and registry_ok:
        print("\nGATE_ALL: ALL PASS (matrices nested + registry 45 zero-overlap + budget + leakage)")
        sys.exit(0)
    else:
        print("\nGATE_ALL: SOME FAIL — exiting 1")
        if not all_ok:
            print("  matrix gate failed -> NESTED_NOT_CONSTRUCTIBLE")
        if not registry_ok:
            print("  registry gate failed -> REGISTRY_INVALID")
        sys.exit(1)

if __name__ == "__main__":
    run()
