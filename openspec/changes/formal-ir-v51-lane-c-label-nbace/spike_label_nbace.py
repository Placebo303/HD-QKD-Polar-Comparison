"""V51 spike: deterministic NB-ACE label optimization on Lane C support (decoder-free).
- reads three Lane C ordinal-2 supports (frozen)
- freezes support, position perm, m2, decoder params
- deterministic label optimizer: minimize degenerate_6, maximize min NB-ACE, minimize degenerate_8
- reports decoder-free metrics original vs optimized
No decoder calls, no formal output.
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
    # NB-ACE per cycle
    def nbace_list(cycles):
        vals=[]
        for cyc in cycles:
            ace=ace_for_cycle(cyc,row_deg)
            is_deg=classify_cycle_algebraic_degeneracy(cyc,H,field)
            # degenerate penalized: NB-ACE = ace - 100 (so degenerate always lower)
            nbace = ace-100 if is_deg else ace
            vals.append((ace,is_deg,nbace))
        return vals
    vals6=nbace_list(c6)
    vals8=nbace_list(c8)
    # min NB-ACE (degenerate penalized) ; if no cycles, None
    min_nbace6 = min(v[2] for v in vals6) if vals6 else None
    min_nbace8 = min(v[2] for v in vals8) if vals8 else None
    # min ACE among degenerate 6 cycles (for lexicographic improvement)
    deg_aces6=[v[0] for v in vals6 if v[1]]
    min_deg_ace6 = min(deg_aces6) if deg_aces6 else None
    deg_aces8=[v[0] for v in vals8 if v[1]]
    min_deg_ace8 = min(deg_aces8) if deg_aces8 else None
    # generalized girth = minimal length of degenerate cycle
    if deg4>0: gg=4
    elif deg6>0: gg=6
    elif deg8>0: gg=8
    else: gg=None
    # also histogram counts for ACE
    return {
        "rank": compute_gf32_rank(H,field),
        "E": int(np.count_nonzero(binary)),
        "row_deg_min": int(row_deg.min()), "row_deg_max": int(row_deg.max()), "row_deg_mean": float(row_deg.mean()),
        "col_deg_min": int(col_deg.min()), "col_deg_max": int(col_deg.max()), "col_deg_mean": float(col_deg.mean()),
        "support_cycles_4": len(c4), "support_cycles_6": len(c6), "support_cycles_8": len(c8),
        "degenerate_4": deg4, "degenerate_6": deg6, "degenerate_8": deg8,
        "min_nbace6": min_nbace6, "min_nbace8": min_nbace8,
        "min_deg_ace6": min_deg_ace6, "min_deg_ace8": min_deg_ace8,
        "generalized_girth": gg,
        "nondeg_frac6": (len(c6)-deg6)/len(c6) if len(c6)>0 else 1.0,
        "nondeg_frac8": (len(c8)-deg8)/len(c8) if len(c8)>0 else 1.0,
        "cycles6": c6, "cycles8": c8, "edge_to_ids": edge_to_ids, "row_deg": row_deg,
        "binary": binary,
    }

def deterministic_nbace_label_optimize(H_init, max_sweeps=2):
    """Greedy deterministic label optimizer lexicographic:
    primary minimize degenerate_6, secondary maximize min_nbace6 (via min_deg_ace6), tertiary minimize degenerate_8, quaternary maximize min_nbace8, tie by smallest label.
    Uses incremental per-edge candidate evaluation.
    """
    field=GF2mField.create(32)
    H=H_init.copy()
    binary=(H!=0).astype(np.uint8)
    c4,c6,c8,edge_to_ids=enumerate_canonical_simple_cycles(binary)
    all_cycles=c4+c6+c8
    # initial degeneracy
    is_deg=[classify_cycle_algebraic_degeneracy(cyc,H,field) for cyc in all_cycles]
    row_deg=np.count_nonzero(binary,axis=1)
    def ace_of(cyc): return sum(int(row_deg[c])-2 for c in cyc.checks)
    # precompute ace per cycle (support fixed so constant)
    ace_per_cycle=[ace_of(cyc) for cyc in all_cycles]

    def global_key():
        # compute counts and mins from current is_deg
        n4=len(c4); n6=len(c6); n8=len(c8)
        d4=sum(is_deg[i] for i in range(n4))
        d6=sum(is_deg[n4+i] for i in range(n6))
        d8=sum(is_deg[n4+n6+i] for i in range(n8))
        # min_deg_ace6 : min ace among degenerate 6
        deg_aces6=[ace_per_cycle[n4+i] for i in range(n6) if is_deg[n4+i]]
        min_deg_ace6 = min(deg_aces6) if deg_aces6 else 999
        # min nbace6 : if degenerate exists, min is min_deg_ace6-100 else min ace among all 6
        if d6>0:
            min_nbace6 = min_deg_ace6-100
        else:
            min_nbace6 = min(ace_per_cycle[n4:n4+n6]) if n6>0 else 999
        deg_aces8=[ace_per_cycle[n4+n6+i] for i in range(n8) if is_deg[n4+n6+i]]
        min_deg_ace8 = min(deg_aces8) if deg_aces8 else 999
        if d8>0:
            min_nbace8 = min_deg_ace8-100
        else:
            min_nbace8 = min(ace_per_cycle[n4+n6:]) if n8>0 else 999
        # lexicographic key: we want to minimize (d6, -min_nbace6, d8, -min_nbace8)
        # So smaller is better. Use tuple (d6, -min_nbace6, d8, -min_nbace8)
        # But to compare candidate keys including cand label, will extend
        return (d6, -min_nbace6, d8, -min_nbace8, d6, min_nbace6) # extra for debug

    curr_key = (sum(is_deg[len(c4):len(c4)+len(c6)]), )  # placeholder

    # We'll do sweeps over canonical edge order
    canonical=get_canonical_support_edges(binary)
    total_updates=0
    sweeps=0
    for sweep in range(1, max_sweeps+1):
        updates=0
        for edge in canonical:
            r,c=edge
            old_val=int(H[r,c])
            incident=[i for i, cyc in enumerate(all_cycles) if edge in cyc.edges]  # slow but ok
            if not incident:
                # no cycles incident, best is 1
                if old_val!=1:
                    H[r,c]=1
                    updates+=1
                continue
            # current global stats
            cur_d6=sum(is_deg[len(c4)+i] for i in range(len(c6)))
            cur_d8=sum(is_deg[len(c4)+len(c6)+i] for i in range(len(c8)))
            # compute current min_deg_ace
            cur_deg_aces6=[ace_per_cycle[len(c4)+i] for i in range(len(c6)) if is_deg[len(c4)+i]]
            cur_min_deg6 = min(cur_deg_aces6) if cur_deg_aces6 else 999
            cur_deg_aces8=[ace_per_cycle[len(c4)+len(c6)+i] for i in range(len(c8)) if is_deg[len(c4)+len(c6)+i]]
            cur_min_deg8 = min(cur_deg_aces8) if cur_deg_aces8 else 999
            cur_min_nb6 = (cur_min_deg6-100) if cur_d6>0 else (min(ace_per_cycle[len(c4):len(c4)+len(c6)]) if len(c6)>0 else 999)
            cur_min_nb8 = (cur_min_deg8-100) if cur_d8>0 else (min(ace_per_cycle[len(c4)+len(c6):]) if len(c8)>0 else 999)

            best_key=None
            best_val=old_val
            best_states=None
            # evaluate each cand 1..31
            for cand in range(1,32):
                if cand==old_val:
                    cand_states=[is_deg[idx] for idx in incident]
                    # global deg counts unchanged
                    cand_d6=cur_d6
                    cand_d8=cur_d8
                    # mins unchanged because degenerate statuses same
                    cand_min_nb6=cur_min_nb6
                    cand_min_nb8=cur_min_nb8
                    # for lexicographic need min_deg as well if tie
                    # compute candidate key
                    cand_key=(cand_d6, -cand_min_nb6, cand_d8, -cand_min_nb8, cand)
                else:
                    H[r,c]=cand
                    cand_states=[classify_cycle_algebraic_degeneracy(all_cycles[idx],H,field) for idx in incident]
                    # compute what global d6/d8 would be with this candidate
                    # need to compute new global is_deg' = old is_deg but with incident replaced
                    new_is_deg=is_deg.copy()
                    for k, idx in enumerate(incident):
                        new_is_deg[idx]=cand_states[k]
                    cand_d6=sum(new_is_deg[len(c4)+i] for i in range(len(c6)))
                    cand_d8=sum(new_is_deg[len(c4)+len(c6)+i] for i in range(len(c8)))
                    # min deg ace for 6/8 with new
                    cand_deg_aces6=[ace_per_cycle[len(c4)+i] for i in range(len(c6)) if new_is_deg[len(c4)+i]]
                    cand_min_deg6 = min(cand_deg_aces6) if cand_deg_aces6 else 999
                    cand_deg_aces8=[ace_per_cycle[len(c4)+len(c6)+i] for i in range(len(c8)) if new_is_deg[len(c4)+len(c6)+i]]
                    cand_min_deg8 = min(cand_deg_aces8) if cand_deg_aces8 else 999
                    cand_min_nb6 = (cand_min_deg6-100) if cand_d6>0 else (min(ace_per_cycle[len(c4):len(c4)+len(c6)]) if len(c6)>0 else 999)
                    cand_min_nb8 = (cand_min_deg8-100) if cand_d8>0 else (min(ace_per_cycle[len(c4)+len(c6):]) if len(c8)>0 else 999)
                    cand_key=(cand_d6, -cand_min_nb6, cand_d8, -cand_min_nb8, cand)
                if best_key is None or cand_key < best_key:
                    best_key=cand_key
                    best_val=cand
                    best_states=cand_states if 'cand_states' in locals() else [is_deg[idx] for idx in incident]
                # restore if we mutated H for evaluation (will be overwritten by best)
                if cand!=old_val:
                    H[r,c]=old_val
            if best_val!=old_val:
                H[r,c]=best_val
                for k, idx in enumerate(incident):
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

def run_spike():
    print("=== V51 NB-ACE label optimization spike (decoder-free) ===")
    field=GF2mField.create(32)
    results=[]
    for src in ["1M","1p5M","2M"]:
        seed=LANE_C_SEEDS[src]
        H_orig,_=construct_lane_c_prototype(source=src, seed=seed, field=field)
        spec_orig=compute_spectrum(H_orig)
        # optimize
        H_opt, sweeps, updates, rank_opt = deterministic_nbace_label_optimize(H_orig, max_sweeps=2)
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
        print(f"  delta deg6 {spec_opt['degenerate_6']-spec_orig['degenerate_6']} deg8 {spec_opt['degenerate_8']-spec_orig['degenerate_8']}")
        print(f"  min_nbace6 orig {spec_orig['min_nbace6']} opt {spec_opt['min_nbace6']}  min_deg_ace6 orig {spec_orig['min_deg_ace6']} opt {spec_opt['min_deg_ace6']}")
        print(f"  min_nbace8 orig {spec_orig['min_nbace8']} opt {spec_opt['min_nbace8']}  min_deg_ace8 orig {spec_orig['min_deg_ace8']} opt {spec_opt['min_deg_ace8']}")
        print(f"  generalized_girth orig {spec_orig['generalized_girth']} opt {spec_opt['generalized_girth']}")
        print(f"  nondeg_frac6 orig {spec_orig['nondeg_frac6']:.4f} opt {spec_opt['nondeg_frac6']:.4f}  nondeg_frac8 orig {spec_orig['nondeg_frac8']:.4f} opt {spec_opt['nondeg_frac8']:.4f}")
        print(f"  row_deg mean orig {spec_orig['row_deg_mean']:.2f} opt {spec_opt['row_deg_mean']:.2f} sweeps {sweeps} updates {updates}")
        # lexicographic improvement?
        improved = (spec_opt['degenerate_6'] < spec_orig['degenerate_6']) or (spec_opt['min_nbace6'] is not None and spec_orig['min_nbace6'] is not None and spec_opt['min_nbace6'] > spec_orig['min_nbace6'])
        print(f"  LEXICO IMPROVED (deg6 or min_nbace6): {improved}")
        results.append((src, spec_orig, spec_opt, improved, support_equal, rank_equal, cycles_equal))
    # overall block?
    any_improved = any(r[3] for r in results)
    print("\n=== SUMMARY ===")
    for src, o, n, imp, se, re, ce in results:
        print(f"{src}: deg6 {o['degenerate_6']}->{n['degenerate_6']}  min_nbace6 {o['min_nbace6']}->{n['min_nbace6']}  improved={imp}  support_eq={se} rank_eq={re} cycles_eq={ce}")
    print(f"\nOVERALL any_improved (deg6 or NB-ACE): {any_improved}")
    if any_improved:
        print("-> Spike verdict: BLOCKER NOT TRIGGERED, may proceed to 45-call paired experiment if approved")
    else:
        print("-> Spike verdict: BLOCKER TRIGGERED — label optimization did not improve degenerate6/NB-ACE, do NOT enter experiment, report blocker")
    # exit code 0 regardless, but report
    return any_improved

if __name__=="__main__":
    ok=run_spike()
    sys.exit(0)
