"""V51 spike: deterministic label optimization on Lane C support (decoder-free).
- reads three Lane C ordinal-2 supports (frozen)
- freezes support, position perm, m2, decoder params
- deterministic label optimizer: primary lexicographic (degenerate_4, degenerate_6, degenerate_8, cand) — deg4 first
- custom check_extrinsic_score = ACE-100 if degenerate else ACE (secondary report only, NOT literature NB-ACE)
- reports decoder-free metrics original vs optimized
No decoder calls, no formal output.
Efficient: reuses edge_to_cycle_ids, only recomputes incident cycles, incrementally maintains global deg4/6/8.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "comparison_bench/src"))

import numpy as np
from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_gf32_rank
from comparison_bench.formal_ir.v38_architecture_triage import (
    SOURCE_CHECKS, MAX_CHECK_DEGREE_LIMIT,
    get_substream_generator, sample_uniform_gf32_nonzero,
    get_canonical_support_edges, enumerate_canonical_simple_cycles,
    classify_cycle_algebraic_degeneracy, construct_lane_c_prototype,
    compute_cycle_submatrix_rank
)

POLY=37
BLOCK_LENGTH=1024

# V51 lane C seeds ordinal-2
LANE_C_SEEDS = {"1M":383102, "1p5M":383202, "2M":383302}

def ace_for_cycle(cycle, row_deg):
    # ACE = sum_{c in checks} (deg(c)-2)  ; for dv=2 regular this captures extrinsic checks
    return sum(int(row_deg[c])-2 for c in cycle.checks)

def compute_spectrum(H):
    field=GF2mField.create(32)
    m,n=H.shape
    binary=(H!=0).astype(np.uint8)
    row_deg=np.count_nonzero(binary,axis=1)
    col_deg=np.count_nonzero(binary,axis=0)
    c4,c6,c8,edge_to_ids=enumerate_canonical_simple_cycles(binary)
    deg4=sum(classify_cycle_algebraic_degeneracy(c,H,field) for c in c4)
    deg6=sum(classify_cycle_algebraic_degeneracy(c,H,field) for c in c6)
    deg8=sum(classify_cycle_algebraic_degeneracy(c,H,field) for c in c8)
    # custom check_extrinsic_score per cycle (NOT literature NB-ACE)
    def score_list(cycles):
        vals=[]
        for cyc in cycles:
            ace=ace_for_cycle(cyc,row_deg)
            is_deg=classify_cycle_algebraic_degeneracy(cyc,H,field)
            # custom: degenerate penalized -100 (secondary report only)
            score = ace-100 if is_deg else ace
            vals.append((ace,is_deg,score))
        return vals
    vals4=score_list(c4)
    vals6=score_list(c6)
    vals8=score_list(c8)
    # min custom score (degenerate penalized); if no cycles, None
    min_check_extrinsic4 = min(v[2] for v in vals4) if vals4 else None
    min_check_extrinsic6 = min(v[2] for v in vals6) if vals6 else None
    min_check_extrinsic8 = min(v[2] for v in vals8) if vals8 else None
    # min ACE among degenerate cycles (secondary)
    deg_aces4=[v[0] for v in vals4 if v[1]]
    min_deg_ace4 = min(deg_aces4) if deg_aces4 else None
    deg_aces6=[v[0] for v in vals6 if v[1]]
    min_deg_ace6 = min(deg_aces6) if deg_aces6 else None
    deg_aces8=[v[0] for v in vals8 if v[1]]
    min_deg_ace8 = min(deg_aces8) if deg_aces8 else None
    # generalized girth = minimal length of degenerate cycle
    if deg4>0: gg=4
    elif deg6>0: gg=6
    elif deg8>0: gg=8
    else: gg=None
    return {
        "rank": compute_gf32_rank(H,field),
        "E": int(np.count_nonzero(binary)),
        "row_deg_min": int(row_deg.min()), "row_deg_max": int(row_deg.max()), "row_deg_mean": float(row_deg.mean()),
        "col_deg_min": int(col_deg.min()), "col_deg_max": int(col_deg.max()), "col_deg_mean": float(col_deg.mean()),
        "support_cycles_4": len(c4), "support_cycles_6": len(c6), "support_cycles_8": len(c8),
        "degenerate_4": deg4, "degenerate_6": deg6, "degenerate_8": deg8,
        # custom secondary (NOT NB-ACE) — keep min_nbace* as alias for backward compat
        "min_check_extrinsic4": min_check_extrinsic4, "min_check_extrinsic6": min_check_extrinsic6, "min_check_extrinsic8": min_check_extrinsic8,
        "min_nbace4": min_check_extrinsic4, "min_nbace6": min_check_extrinsic6, "min_nbace8": min_check_extrinsic8,
        "min_deg_ace4": min_deg_ace4, "min_deg_ace6": min_deg_ace6, "min_deg_ace8": min_deg_ace8,
        "generalized_girth": gg,
        "nondeg_frac4": (len(c4)-deg4)/len(c4) if len(c4)>0 else 1.0,
        "nondeg_frac6": (len(c6)-deg6)/len(c6) if len(c6)>0 else 1.0,
        "nondeg_frac8": (len(c8)-deg8)/len(c8) if len(c8)>0 else 1.0,
        "cycles4": c4, "cycles6": c6, "cycles8": c8, "edge_to_ids": edge_to_ids, "row_deg": row_deg,
        "binary": binary,
    }

def deterministic_label_optimize(H_init, max_sweeps=2):
    """Greedy deterministic label optimizer primary lexicographic (deg4,deg6,deg8,cand).
    Custom check_extrinsic_score is secondary report only, not in primary key.
    Efficient incremental: reuse edge_to_cycle_ids, only recompute incident cycles, maintain global deg counts.
    """
    field=GF2mField.create(32)
    H=H_init.copy()
    binary=(H!=0).astype(np.uint8)
    c4,c6,c8,edge_to_ids=enumerate_canonical_simple_cycles(binary)
    all_cycles=c4+c6+c8
    n4=len(c4); n6=len(c6); n8=len(c8)
    num_cycles=len(all_cycles)
    # initial degeneracy
    is_deg=[classify_cycle_algebraic_degeneracy(cyc,H,field) for cyc in all_cycles]
    def _count_degeneracies():
        d4=sum(is_deg[i] for i in range(n4))
        d6=sum(is_deg[i] for i in range(n4, n4+n6))
        d8=sum(is_deg[i] for i in range(n4+n6, num_cycles))
        return d4,d6,d8
    curr_d4,curr_d6,curr_d8=_count_degeneracies()
    row_deg=np.count_nonzero(binary,axis=1)
    # canonical edge order
    canonical=get_canonical_support_edges(binary)
    total_updates=0
    sweeps=0
    for sweep in range(1, max_sweeps+1):
        updates=0
        for edge in canonical:
            r,c=edge
            old_val=int(H[r,c])
            incident_ids=edge_to_ids.get(edge, [])
            if not incident_ids:
                # no cycles incident: best is 1 (smallest cand gives minimal key)
                if old_val!=1:
                    H[r,c]=1
                    updates+=1
                continue
            # precompute old incident counts for incremental update
            old_inc_4=sum(is_deg[idx] for idx in incident_ids if all_cycles[idx].length==4)
            old_inc_6=sum(is_deg[idx] for idx in incident_ids if all_cycles[idx].length==6)
            old_inc_8=sum(is_deg[idx] for idx in incident_ids if all_cycles[idx].length==8)
            best_key=None
            best_val=old_val
            best_states=None
            # evaluate each cand 1..31 — only recompute incident cycles
            for cand in range(1,32):
                if cand==old_val:
                    cand_states=[is_deg[idx] for idx in incident_ids]
                    cand_d4,cand_d6,cand_d8=curr_d4,curr_d6,curr_d8
                else:
                    H[r,c]=cand
                    cand_states=[classify_cycle_algebraic_degeneracy(all_cycles[idx],H,field) for idx in incident_ids]
                    cand_inc_4=sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length==4)
                    cand_inc_6=sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length==6)
                    cand_inc_8=sum(cand_states[k] for k, idx in enumerate(incident_ids) if all_cycles[idx].length==8)
                    cand_d4=curr_d4 - old_inc_4 + cand_inc_4
                    cand_d6=curr_d6 - old_inc_6 + cand_inc_6
                    cand_d8=curr_d8 - old_inc_8 + cand_inc_8
                # primary lexicographic key (deg4,deg6,deg8,cand) — smaller is better
                cand_key=(cand_d4, cand_d6, cand_d8, cand)
                if best_key is None or cand_key < best_key:
                    best_key=cand_key
                    best_val=cand
                    best_states=cand_states
                if cand!=old_val:
                    H[r,c]=old_val
            if best_val!=old_val:
                H[r,c]=best_val
                # incrementally update global counts via best_key
                curr_d4,curr_d6,curr_d8,_ = best_key
                for k, idx in enumerate(incident_ids):
                    is_deg[idx]=best_states[k]
                updates+=1
            else:
                H[r,c]=old_val
        total_updates+=updates
        sweeps=sweep
        if updates==0:
            break
    final_rank=compute_gf32_rank(H,field)
    return H, sweeps, total_updates, final_rank

# backward compat alias (old name)
def deterministic_nbace_label_optimize(H_init, max_sweeps=2):
    return deterministic_label_optimize(H_init, max_sweeps)

def _lex_le(a, b):
    """lexicographic <= for tuples"""
    return a <= b

def _lex_lt(a, b):
    return a < b

def run_spike():
    print("=== V51 label optimization spike (decoder-free, deg4-first, incremental) ===")
    print("Note: check_extrinsic_score is CUSTOM (ACE-100 if degenerate), NOT literature NB-ACE; primary key is (deg4,deg6,deg8,cand)")
    field=GF2mField.create(32)
    results=[]
    for src in ["1M","1p5M","2M"]:
        seed=LANE_C_SEEDS[src]
        H_orig,_=construct_lane_c_prototype(source=src, seed=seed, field=field)
        spec_orig=compute_spectrum(H_orig)
        # optimize
        H_opt, sweeps, updates, rank_opt = deterministic_label_optimize(H_orig, max_sweeps=2)
        spec_opt=compute_spectrum(H_opt)
        # checks
        binary_orig=(H_orig!=0).astype(np.uint8)
        binary_opt=(H_opt!=0).astype(np.uint8)
        support_equal = np.array_equal(binary_orig, binary_opt)
        rank_equal = spec_orig["rank"]==spec_opt["rank"] and spec_opt["rank"]==SOURCE_CHECKS[src]
        cycles_equal = (spec_orig["support_cycles_4"]==spec_opt["support_cycles_4"] and spec_orig["support_cycles_6"]==spec_opt["support_cycles_6"] and spec_orig["support_cycles_8"]==spec_opt["support_cycles_8"])
        print(f"\n--- {src} m={SOURCE_CHECKS[src]} seed={seed} ---")
        print(f"  support_equal: {support_equal}  rank orig {spec_orig['rank']} opt {spec_opt['rank']} rank_ok {rank_equal}  E {spec_orig['E']}")
        print(f"  4/6/8 orig: {spec_orig['support_cycles_4']}/{spec_orig['support_cycles_6']}/{spec_orig['support_cycles_8']}")
        print(f"  4/6/8 opt : {spec_opt['support_cycles_4']}/{spec_opt['support_cycles_6']}/{spec_opt['support_cycles_8']} cycles_equal {cycles_equal}")
        print(f"  degenerate orig: 4:{spec_orig['degenerate_4']} 6:{spec_orig['degenerate_6']} 8:{spec_orig['degenerate_8']}")
        print(f"  degenerate opt : 4:{spec_opt['degenerate_4']} 6:{spec_opt['degenerate_6']} 8:{spec_opt['degenerate_8']}")
        print(f"  delta deg4 {spec_opt['degenerate_4']-spec_orig['degenerate_4']} deg6 {spec_opt['degenerate_6']-spec_orig['degenerate_6']} deg8 {spec_opt['degenerate_8']-spec_orig['degenerate_8']}")
        print(f"  custom check_extrinsic6 orig {spec_orig['min_check_extrinsic6']} opt {spec_opt['min_check_extrinsic6']}  min_deg_ace6 orig {spec_orig['min_deg_ace6']} opt {spec_opt['min_deg_ace6']} (secondary)")
        print(f"  custom check_extrinsic8 orig {spec_orig['min_check_extrinsic8']} opt {spec_opt['min_check_extrinsic8']}  min_deg_ace8 orig {spec_orig['min_deg_ace8']} opt {spec_opt['min_deg_ace8']} (secondary)")
        print(f"  generalized_girth orig {spec_orig['generalized_girth']} opt {spec_opt['generalized_girth']}")
        print(f"  nondeg_frac6 orig {spec_orig['nondeg_frac6']:.4f} opt {spec_opt['nondeg_frac6']:.4f}  nondeg_frac8 orig {spec_orig['nondeg_frac8']:.4f} opt {spec_opt['nondeg_frac8']:.4f}")
        print(f"  row_deg mean orig {spec_orig['row_deg_mean']:.2f} opt {spec_opt['row_deg_mean']:.2f} sweeps {sweeps} updates {updates}")
        # per-source lexicographic improvement (primary)
        orig_key=(spec_orig['degenerate_4'], spec_orig['degenerate_6'], spec_orig['degenerate_8'])
        new_key=(spec_opt['degenerate_4'], spec_opt['degenerate_6'], spec_opt['degenerate_8'])
        not_worse = _lex_le(new_key, orig_key)
        strictly_better = _lex_lt(new_key, orig_key)
        print(f"  LEXICO (deg4,deg6,deg8) orig {orig_key} -> new {new_key}  not_worse={not_worse} strictly_better={strictly_better}")
        results.append((src, spec_orig, spec_opt, not_worse, strictly_better, support_equal, rank_equal, cycles_equal))
    # overall gate: all not worse and at least one strictly better
    all_not_worse = all(r[3] for r in results)
    any_strict = any(r[4] for r in results)
    label_improved = all_not_worse and any_strict
    print("\n=== SUMMARY (three-source lexicographic consistency) ===")
    for src, o, n, nw, sb, se, re, ce in results:
        print(f"{src}: (deg4,deg6,deg8) {o['degenerate_4'],o['degenerate_6'],o['degenerate_8']}->{n['degenerate_4'],n['degenerate_6'],n['degenerate_8']}  not_worse={nw} strictly_better={sb}  support_eq={se} rank_eq={re} cycles_eq={ce}")
    print(f"\nOVERALL all_not_worse={all_not_worse} any_strictly_better={any_strict} -> label_improved={label_improved}")
    if label_improved:
        print("-> Spike verdict: BLOCKER NOT TRIGGERED (three-source consistency satisfied), may proceed to 45-call paired experiment if approved")
    else:
        if not all_not_worse:
            print("-> Spike verdict: BLOCKER TRIGGERED — at least one source worsened lexicographically, do NOT enter experiment")
        else:
            print("-> Spike verdict: BLOCKER TRIGGERED — no source strictly improved, do NOT enter experiment, report V51_LABEL_NO_IMPROVEMENT")
    return label_improved

if __name__=="__main__":
    ok=run_spike()
    sys.exit(0)
