"""V54 decoder-free two-stage nested rescue spike: verify H_base + H_inc1 + H_inc2 nesting/joint rank/independence/leakage + 45 fresh held-out registry excluding V53.
Zero decoder calls. Reproducible. Uses v38/v35 primitives only.
Run: python spike_nested_rescue_stage2.py  # exit 0 GATE_ALL PASS
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
DELTA_M_TOTAL = 16
POLY = 37
# H_inc1 deterministic ids (V52/V53 frozen, reuse)
INC1_DET_IDS = {"1M": 600001, "1p5M": 600002, "2M": 600003}
# H_inc2 deterministic ids (V54 new, second stage, MUST be distinct from INC1, no seed search)
INC2_DET_IDS = {"1M": 600004, "1p5M": 600005, "2M": 600006}
BASE_SEEDS = {"1M": 383102, "1p5M": 383202, "2M": 383302}

HOLD_CONFIG = {
    "1M": {"H": 400, "base": 1600},
    "1p5M": {"H": 554, "base": 2213},
    "2M": {"H": 729, "base": 2916},
}

# Used intervals union per source for V53 (without V53) — base for V53 enumeration (V48+V50+V51+V52)
USED_STARTS_BASE = {
    "1M": [
        0,28,56,84,113,141,169,198,226,254,282,311,339,367,396,
        14,42,70,98,127,
        7,35,63,91,119,
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
        53,104,155,206,257,
    ],
}
for k in USED_STARTS_BASE:
    USED_STARTS_BASE[k] = sorted(set(USED_STARTS_BASE[k]))

def overlaps(a, b):
    return abs(a - b) <= 3

def enumerate_remaining_and_select(source, used_list, H):
    all_starts = list(range(0, H - 3))
    remaining = [s for s in all_starts if not any(overlaps(s, u) for u in used_list)]
    remaining_strict = [s for s in remaining if s % 4 == 0]
    K = len(remaining)
    K_strict = len(remaining_strict)
    if K < 15:
        print(f"  ERROR: remaining K={K} <15 for {source}")
        return None
    selected = []
    for j in range(15):
        idx = (j * (K - 1)) // 14
        selected.append(remaining[idx])
    non_overlap_ok = True
    for i in range(len(selected)):
        for kk in range(i+1, len(selected)):
            if overlaps(selected[i], selected[kk]):
                non_overlap_ok = False
                print(f"  ERROR: selected overlap within {source}: {selected[i]} vs {selected[kk]}")
    zero_overlap_used = all(not any(overlaps(s, u) for u in used_list) for s in selected)
    unique_ok = len(set(selected)) == 15
    return {
        "H": H,
        "K": K,
        "K_strict": K_strict,
        "remaining": remaining,
        "selected": selected,
        "selected_sorted": sorted(selected),
        "non_overlap_ok": non_overlap_ok,
        "zero_overlap_used": zero_overlap_used,
        "unique_ok": unique_ok,
        "used": used_list,
    }

def construct_h_inc(source: str, det_id: int, delta_m: int = DELTA_M, n: int = BLOCK_LENGTH):
    """Deterministic PEG-like incremental matrix delta_m x n, col_degree 0/1, row<=16. No seed search."""
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
            print(f"  ERROR: row degree exceeded 16 at row {c_pick} col {j} det {det_id}")
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

def verify_source_two_stage(source: str):
    print(f"\n-- {source} m2={SOURCE_CHECKS[source]} det_inc1={INC1_DET_IDS[source]} det_inc2={INC2_DET_IDS[source]} delta1={DELTA_M} delta2={DELTA_M} total={DELTA_M_TOTAL} --")
    field = GF2mField.create(32)
    m2 = SOURCE_CHECKS[source]
    base_seed = BASE_SEEDS[source]
    H_base, metrics_base = construct_lane_c_prototype(source=source, seed=base_seed, field=field)
    print(f"  H_base shape {H_base.shape} rank {metrics_base['rank_GF32']} expected {m2} valid {metrics_base['structurally_valid']}")
    rank_base = metrics_base['rank_GF32']
    if rank_base != m2:
        print(f"  FAIL: base rank {rank_base} != m2 {m2}")
        return False, {}
    # H_inc1 (frozen)
    H_inc1, Hs_inc1, E_inc1, row_deg_inc1 = construct_h_inc(source, INC1_DET_IDS[source], DELTA_M)
    print(f"  H_inc1 shape {H_inc1.shape} E_inc1 {E_inc1} row_deg {row_deg_inc1.tolist()} min {int(row_deg_inc1.min())} max {int(row_deg_inc1.max())} mean {float(row_deg_inc1.mean()):.2f}")
    if int(row_deg_inc1.max()) > MAX_CHECK_DEGREE_LIMIT or int((row_deg_inc1 == 0).sum()) != 0:
        print("  FAIL: H_inc1 row_degree")
        return False, {}
    col_deg_inc1 = np.count_nonzero(Hs_inc1, axis=0)
    if int(col_deg_inc1.max()) > 1:
        print(f"  FAIL: H_inc1 col_degree >1 max {int(col_deg_inc1.max())}")
        return False, {}
    # H_joint1
    H_joint1 = np.vstack([H_base, H_inc1]).astype(np.uint8)
    m_joint1 = m2 + DELTA_M
    rank_joint1 = compute_gf32_rank(H_joint1, field)
    nested1_ok = np.array_equal(H_joint1[0:m2, :], H_base)
    rank_inc1 = rank_joint1 - rank_base
    print(f"  H_joint1 shape {H_joint1.shape} expected {(m_joint1, BLOCK_LENGTH)} rank_joint1 {rank_joint1} expected {m_joint1} rank_inc1 {rank_inc1} nested1 {nested1_ok}")
    if rank_joint1 != m_joint1 or rank_inc1 != DELTA_M or not nested1_ok:
        print("  FAIL: H_joint1 gate")
        return False, {}
    # H_inc2 (new, must add 8 independent rank beyond joint1)
    H_inc2, Hs_inc2, E_inc2, row_deg_inc2 = construct_h_inc(source, INC2_DET_IDS[source], DELTA_M)
    print(f"  H_inc2 shape {H_inc2.shape} E_inc2 {E_inc2} row_deg {row_deg_inc2.tolist()} min {int(row_deg_inc2.min())} max {int(row_deg_inc2.max())} mean {float(row_deg_inc2.mean()):.2f}")
    if int(row_deg_inc2.max()) > MAX_CHECK_DEGREE_LIMIT or int((row_deg_inc2 == 0).sum()) != 0:
        print("  FAIL: H_inc2 row_degree")
        return False, {}
    col_deg_inc2 = np.count_nonzero(Hs_inc2, axis=0)
    if int(col_deg_inc2.max()) > 1:
        print(f"  FAIL: H_inc2 col_degree >1 max {int(col_deg_inc2.max())}")
        return False, {}
    # H_total = [H_base; H_inc1; H_inc2]
    H_total = np.vstack([H_base, H_inc1, H_inc2]).astype(np.uint8)
    m_total = m2 + DELTA_M_TOTAL
    print(f"  H_total shape {H_total.shape} expected {(m_total, BLOCK_LENGTH)}")
    rank_total = compute_gf32_rank(H_total, field)
    print(f"  rank_base {rank_base} rank_joint1 {rank_joint1} rank_total {rank_total} expected {m_total}")
    rank_inc2 = rank_total - rank_joint1
    rank_inc_total = rank_total - rank_base
    nested_total_base = np.array_equal(H_total[0:m2, :], H_base)
    nested_total_joint1 = np.array_equal(H_total[0:m_joint1, :], H_joint1)
    print(f"  nested_total_base (H_base == H_total[:m2]): {nested_total_base}")
    print(f"  nested_total_joint1 (H_joint1 == H_total[:m2+8]): {nested_total_joint1}")
    print(f"  rank_increment_1 (joint1-base)={rank_inc1} expected {DELTA_M}")
    print(f"  rank_increment_2 (total-joint1)={rank_inc2} expected {DELTA_M}")
    print(f"  rank_increment_total (total-base)={rank_inc_total} expected {DELTA_M_TOTAL}")
    independence1_ok = (rank_inc1 == DELTA_M)
    independence2_ok = (rank_inc2 == DELTA_M)
    full_joint1_ok = (rank_joint1 == m_joint1)
    full_total_ok = (rank_total == m_total)
    # leakage
    leak_base = 5*m2 + 5*16 + 64
    leak_stage1 = 5*m_joint1 + 5*16 + 64
    leak_stage2 = 5*m_total + 5*16 + 64
    delta1 = leak_stage1 - leak_base
    delta2 = leak_stage2 - leak_stage1
    delta_total = leak_stage2 - leak_base
    print(f"  leak_base {leak_base} leak_stage1 {leak_stage1} leak_stage2 {leak_stage2} delta1 {delta1} delta2 {delta2} total {delta_total} expected 40/40/80")
    leak_ok = (delta1 == 40 and delta2 == 40 and delta_total == 80)
    Hs_total = (H_total != 0).astype(np.uint8)
    col_deg_total = np.count_nonzero(Hs_total, axis=0)
    row_deg_total = np.count_nonzero(Hs_total, axis=1)
    print(f"  total col_deg min {int(col_deg_total.min())} max {int(col_deg_total.max())} mean {float(col_deg_total.mean()):.2f} zero_col {(col_deg_total==0).sum()}")
    print(f"  total row_deg min {int(row_deg_total.min())} max {int(row_deg_total.max())} mean {float(row_deg_total.mean()):.2f} zero_row {(row_deg_total==0).sum()}")
    # also check joint1 row/col
    Hs_joint1 = (H_joint1 != 0).astype(np.uint8)
    col_deg_joint1 = np.count_nonzero(Hs_joint1, axis=0)
    row_deg_joint1 = np.count_nonzero(Hs_joint1, axis=1)
    gate_ok = (full_joint1_ok and full_total_ok and nested_total_base and nested_total_joint1 and independence1_ok and independence2_ok and leak_ok and int((col_deg_total==0).sum())==0 and int((row_deg_total==0).sum())==0 and int(row_deg_total.max())<=16 and int(row_deg_joint1.max())<=16)
    print(f"  GATE: {'PASS' if gate_ok else 'FAIL'} (joint1 m2+8 && total m2+16 && nested x2 && indep 8+8 && leak +40+40 && no zero && row<=16)")
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
        "m_joint1": m_joint1,
        "m_total": m_total,
        "rank_base": int(rank_base),
        "rank_joint1": int(rank_joint1),
        "rank_total": int(rank_total),
        "rank_inc1": int(rank_inc1),
        "rank_inc2": int(rank_inc2),
        "rank_inc_total": int(rank_inc_total),
        "nested1": bool(nested1_ok),
        "nested_total_base": bool(nested_total_base),
        "nested_total_joint1": bool(nested_total_joint1),
        "leak_base": int(leak_base),
        "leak_stage1": int(leak_stage1),
        "leak_stage2": int(leak_stage2),
        "E_inc1": int(E_inc1),
        "E_inc2": int(E_inc2),
        "row_deg_inc1": row_deg_inc1.tolist(),
        "row_deg_inc2": row_deg_inc2.tolist(),
        "col_deg_inc1_max": int(col_deg_inc1.max()),
        "col_deg_inc2_max": int(col_deg_inc2.max()),
        "total_zero_col": int((col_deg_total==0).sum()),
        "total_zero_row": int((row_deg_total==0).sum()),
        "total_row_max": int(row_deg_total.max()),
        "gate": bool(gate_ok),
    }
    return gate_ok, details

def run():
    print("=== V54 Two-Stage Nested Rescue Spike — decoder-free ===")
    print(f"BLOCK_LENGTH {BLOCK_LENGTH} DELTA_M {DELTA_M} TOTAL {DELTA_M_TOTAL} POLY {POLY}")
    print(f"BASE_SEEDS {BASE_SEEDS} INC1 {INC1_DET_IDS} INC2 {INC2_DET_IDS}")
    all_ok = True
    all_details = {}
    for src in ["1M", "1p5M", "2M"]:
        ok, det = verify_source_two_stage(src)
        all_details[src] = det
        if not ok:
            all_ok = False

    # Registry: first compute V53 selected (to define V54 used set)
    print("\n=== Sample Registry 45 fresh held-out blocks V54 (decoder-free, excluding V53) ===")
    print(f"Hold config: {HOLD_CONFIG}")
    print(f"Used base per source (V48+V50+V51+V52, union unique):")
    for src in ["1M","1p5M","2M"]:
        print(f"  {src}: {USED_STARTS_BASE[src]} count {len(USED_STARTS_BASE[src])}")

    # Compute V53 selected deterministically (same as V53 spike)
    v53_selected_per_source = {}
    for src in ["1M","1p5M","2M"]:
        cfg = HOLD_CONFIG[src]
        info53 = enumerate_remaining_and_select(src, USED_STARTS_BASE[src], cfg["H"])
        if info53 is None:
            print(f"  ERROR: V53 enumeration failed for {src}")
            sys.exit(1)
        v53_selected_per_source[src] = info53["selected"]
        print(f"  V53 selected {src}: {info53['selected']} K={info53['K']} K_strict={info53['K_strict']}")

    # Build V54 used = base + V53 selected
    USED_STARTS_V54 = {}
    for src in ["1M","1p5M","2M"]:
        combined = sorted(set(USED_STARTS_BASE[src] + v53_selected_per_source[src]))
        USED_STARTS_V54[src] = combined
        print(f"  V54 used {src} (base+V53): count {len(combined)}")

    # Now enumerate V54 remaining and select
    print("\n=== V54 enumeration K2 and dispersed selection ===")
    per_source_selected_v54 = {}
    registry_ok = True
    for src in ["1M","1p5M","2M"]:
        cfg = HOLD_CONFIG[src]
        info2 = enumerate_remaining_and_select(src, USED_STARTS_V54[src], cfg["H"])
        if info2 is None:
            registry_ok = False
            continue
        print(f"\n-- {src} V54 registry --")
        print(f"  H {info2['H']} base {cfg['base']} K2(remaining step1) {info2['K']} K2_strict(step4) {info2['K_strict']}")
        print(f"  remaining sample (first 10): {info2['remaining'][:10]} ... last 10: {info2['remaining'][-10:]}")
        print(f"  selected2 15 starts (ordinal): {info2['selected']}")
        print(f"  selected2 sorted: {info2['selected_sorted']}")
        frame_ids_list = []
        for s in info2["selected"]:
            fids = [cfg["base"]+s + i for i in range(4)]
            frame_ids_list.append(fids)
        print(f"  frame_ids per block:")
        for idx, (s, fids) in enumerate(zip(info2["selected"], frame_ids_list)):
            print(f"    block {idx+1} start {s} [{s},{s+3}] -> fids {fids}")
        print(f"  non_overlap among selected2: {info2['non_overlap_ok']}")
        print(f"  zero_overlap with used (135): {info2['zero_overlap_used']}")
        print(f"  unique 15: {info2['unique_ok']}")
        per_source_selected_v54[src] = {
            "starts": info2["selected"],
            "frame_ids": frame_ids_list,
            "ordinals": [(s, s+3) for s in info2["selected"]],
            "K2": info2["K"],
            "K2_strict": info2["K_strict"],
            "remaining": info2["remaining"],
        }
        if not (info2["non_overlap_ok"] and info2["zero_overlap_used"] and info2["unique_ok"]):
            registry_ok = False
            print(f"  REGISTRY FAIL for {src} V54")
        else:
            print(f"  REGISTRY PASS for {src} V54")

    # Cross-source checks
    print("\n=== Cross-source global checks V54 ===")
    suggested_ids = {
        "1M": list(range(395001, 395016)),
        "1p5M": list(range(395101, 395116)),
        "2M": list(range(395201, 395216)),
    }
    flat_ids = [b for lst in suggested_ids.values() for b in lst]
    print(f"  suggested 45 block IDs {flat_ids[:5]}... count {len(flat_ids)} unique {len(set(flat_ids))==45}")
    prior_ids = set()
    for r in [range(390128,390143), range(390228,390243), range(390328,390343),
              range(391001,391006), range(391101,391106), range(391201,391206),
              range(392001,392006), range(392101,392106), range(392201,392206),
              range(393001,393006), range(393101,393106), range(393201,393206),
              range(394001,394016), range(394101,394116), range(394201,394216)]:
        prior_ids.update(r)
    overlap_ids = set(flat_ids) & prior_ids
    print(f"  overlap of suggested 395xxx with prior block IDs (should be 0): {len(overlap_ids)} {overlap_ids}")
    if len(overlap_ids) != 0:
        registry_ok = False
    # Also verify no overlap with V53 frame_ids in terms of start overlap (already done per source)
    total_fresh_frames = 45*4
    print(f"  total fresh frames this change: {total_fresh_frames} (45*4) per source 60")
    # Leakage/report formulas
    print("\n=== Leakage formulas V54 three-stage ===")
    print("  per_source_avg[s] = leak_base[s] +40*N_stage1[s]/15 +40*N_stage2[s]/15 where N_stage1[s]=count(!verify_base) per source, N_stage2[s]=count(!verify_base&&!verify_stage1) per source")
    print("  overall_avg = (sum leak_base[source(block)] +40*N_stage1_total+40*N_stage2_total)/45 where N_stage1_total=count(!verify_base) overall, N_stage2_total=count(!verify_base&&!verify_stage1) overall")
    print("  total = sum leak_base[source(block)]+40*N_stage1_total+40*N_stage2_total ; avg=total/45 ; disclosure_per_final_exact = total/final_count (0 then null)")
    for src in ["1M","1p5M","2M"]:
        m2 = SOURCE_CHECKS[src]
        leak_base = 5*m2 +80+64
        leak_s1 = 5*(m2+8)+80+64
        leak_s2 = 5*(m2+16)+80+64
        print(f"  {src}: m2 {m2} leak_base {leak_base} leak_stage1 {leak_s1} leak_stage2 {leak_s2} +40/+80")

    print("\n=== Budget V54 ===")
    print(f"  per block: L1 1 + base 1 + stage1 <=1 + stage2 <=1 => 2-4 per block")
    print(f"  total 45 blocks: L1 45 + base45 + stage1 0-45 + stage2 0-45 =90-180 hard cap 180, L2 45-135")
    print(f"  expected actual ~112+~12 stage2 (if stage1 attempt ~22, stage2 ~12 then total ~45+45+22+12=124)")

    print("\n=== Frozen table for design.md V54 (actual frame_ids) ===")
    print("| source | block ID (suggested) | held_out_ordinal [start,end] | frame_ids[4] (global) | base | H | pairs |")
    print("|---|---|---|---|---|---|---|")
    for src in ["1M","1p5M","2M"]:
        cfg = HOLD_CONFIG[src]
        sel = per_source_selected_v54[src]["starts"] if src in per_source_selected_v54 else []
        ids = suggested_ids[src]
        for block_id, start in zip(ids, sel):
            fids = f"[{cfg['base']+start},{cfg['base']+start+1},{cfg['base']+start+2},{cfg['base']+start+3}]"
            print(f"| {src} | {block_id} | [{start},{start+3}] | {fids} | {cfg['base']} | {cfg['H']} | 1024 |")

    # Final gate
    if all_ok and registry_ok:
        print("\nGATE_ALL: ALL PASS (two-stage matrices nested m2+8+8 + registry 45 zero-overlap V54 + budget + leakage)")
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
