"""P0 decoder-free spike: actually construct 3 matrices, report rank/E/deg/4-6-8-cycle/chain-ring.
Zero decoder calls. Reproducible. Uses v38/v35 primitives only.
Run: python spike_construct.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "comparison_bench" / "src"))

import numpy as np
from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_gf32_rank
from comparison_bench.formal_ir.v38_architecture_triage import (
    SOURCE_CHECKS, MAX_CHECK_DEGREE_LIMIT,
    get_substream_generator, sample_uniform_gf32_nonzero,
    get_canonical_support_edges, enumerate_canonical_simple_cycles,
    classify_cycle_algebraic_degeneracy,
)

POLY=37
BLOCK_LENGTH=1024
# Deterministic ids per source for spike (no seed search)
DET_IDS = {"1M":500001, "1p5M":500002, "2M":500003}

def degree2_chain_and_pure_ring(binary_support):
    """Compute max degree-2 chain length (vars) and pure ring count len<=12.
    Chain: maximal path where internal checks have degree 2 within G2 induced subgraph.
    Pure ring: cycle where every var has dv==2 and cycle length <=12 (i.e. 4,6,8,10,12 in terms of vars*2?).
    For our dv mixed case, only vars with dv==2 contribute.
    We approximate:
      - Build G2 = subgraph induced by dv==2 vars + all checks (but edges only to G2 vars)
      - Find connected components, classify.
    Simplified metrics:
      max_chain = longest path length in vars where internal checks degree==2 (within G2).
      pure_ring_count = number of simple cycles length<=12 where all vars dv==2 (using enumerated 4/6/8 cycles filtered).
    """
    m,n = binary_support.shape
    col_deg = np.count_nonzero(binary_support, axis=0)
    row_deg_g2 = np.count_nonzero(binary_support[:, col_deg==2], axis=1)  # degree within G2
    # For max chain: we need to find paths.
    # Build adjacency: check -> list of dv2 vars, var -> list of checks (size 2)
    dv2_cols = np.where(col_deg==2)[0]
    # var to checks
    var_to_checks = {}
    for v in dv2_cols:
        checks = np.where(binary_support[:, v])[0].tolist()
        var_to_checks[int(v)] = checks
    # check to vars (G2 only)
    check_to_vars = {c: np.where(binary_support[c, dv2_cols])[0] for c in range(m)}
    # Actually map check idx -> list of dv2 var ids
    check_to_vars_list = {}
    for c in range(m):
        vars_c = [int(v) for v in dv2_cols if binary_support[c, v]]
        check_to_vars_list[c]=vars_c

    # Find max chain via BFS on line graph: vars connected via checks of degree 2 within G2
    # A chain is sequence v0 - c0 - v1 - c1 - v2 ... where internal c degree==2 in G2
    # We can do DFS limited.
    visited_vars=set()
    max_chain=0
    pure_ring_len12=0
    # Enumerate cycles already gives pure cycles for len 4,6,8 ; we will filter later.
    # For chain: find components and traverse.
    # Simple approach: build graph where vars are nodes, edge exists if they share a check that has degree==2 within G2
    # Then chain length = size of path component where internal degree etc. Approx use BFS to find longest path in each component (NP-hard but small)
    # For spike, do brute DFS for components up to maybe 20 vars.
    from collections import defaultdict, deque
    # Build var-var adjacency via degree-2 checks
    var_adj=defaultdict(list)
    for c, vars_c in check_to_vars_list.items():
        if len(vars_c)==2: # degree 2 within G2 -> connects its two vars
            v1,v2=vars_c[0],vars_c[1]
            var_adj[v1].append(v2)
            var_adj[v2].append(v1)
        elif len(vars_c)>2:
            # check degree >2 within G2, branching, not part of chain
            pass
    # Find connected components in var_adj
    seen=set()
    for v in dv2_cols:
        v=int(v)
        if v in seen: continue
        # BFS component
        comp=[]
        stack=[v]
        seen.add(v)
        while stack:
            cur=stack.pop()
            comp.append(cur)
            for nb in var_adj.get(cur,[]):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        # component size is candidate chain length if it's a path (max degree <=2)
        # check if component forms a simple path or cycle
        degs=[len(var_adj.get(x,[])) for x in comp]
        if len(comp)==0:
            continue
        if max(degs, default=0) <=2:
            # path or cycle
            # chain length = len(comp) if path, else handle ring separately
            # For ring, all degs==2 -> cycle
            if all(d==2 for d in degs) and len(comp)>=3:
                # cycle -> pure ring if length*2 <=12? Actually cycle length in bipartite terms = 2*|comp| (vars+checks)
                # For var-only cycle, bipartite length = 2*len(comp). So condition 2*len<=12 => len<=6
                if 2*len(comp) <=12:
                    pure_ring_len12+=1
                # for chain metric, cycle not counted as chain
                max_chain = max(max_chain, len(comp)-1 if len(comp)>1 else 1)
            else:
                max_chain = max(max_chain, len(comp))
        else:
            # branching component, find longest path via brute DFS limited to component size
            # simple DFS from each endpoint
            endpoints=[x for x in comp if len(var_adj.get(x,[]))==1]
            if not endpoints:
                endpoints=comp[:1]
            best=1
            for ep in endpoints:
                # DFS
                stack=[(ep, set([ep]), 1)]
                while stack:
                    cur, visited, length = stack.pop()
                    best=max(best,length)
                    for nb in var_adj.get(cur,[]):
                        if nb not in visited:
                            stack.append((nb, visited|{nb}, length+1))
            max_chain=max(max_chain,best)
    return max_chain, pure_ring_len12

def construct_mixed(source, det_id, dv_list=None):
    m=SOURCE_CHECKS[source]
    n=BLOCK_LENGTH
    if dv_list is None:
        # mixed 512x2 +512x3
        dv_list=[2]*512+[3]*512
    assert len(dv_list)==n
    E=sum(dv_list)
    field=GF2mField.create(32)
    support_rng=get_substream_generator(det_id, stream_id=1)
    coeff_rng=get_substream_generator(det_id, stream_id=2)
    # frozen permutation for tie-break
    perm = support_rng.permutation(m).tolist()
    rank_in_perm={c:i for i,c in enumerate(perm)}
    check_degrees=np.zeros(m, dtype=int)
    H_support=np.zeros((m,n), dtype=np.uint8)
    check_pairs=set()
    for j, d in enumerate(dv_list):
        chosen=[]
        for k in range(d):
            # eligible checks not yet chosen for this col
            eligible=[c for c in range(m) if c not in chosen]
            # minimal degree
            min_deg=min(check_degrees[c] for c in eligible)
            min_set=[c for c in eligible if check_degrees[c]==min_deg]
            # prefer those that don't create duplicate pair with already chosen
            if chosen:
                # for each candidate, count duplicate pairs with chosen
                scored=[]
                for c in min_set:
                    dup=sum(1 for pc in chosen if (min(pc,c), max(pc,c)) in check_pairs)
                    scored.append((dup, rank_in_perm[c], c))
                scored.sort()
                # pick smallest dup then rank
                c_pick=scored[0][2]
                # if best dup>0 and there exists alternative with higher degree but zero dup? We strictly enforce degree first, so keep min degree
            else:
                c_pick=min(min_set, key=lambda c: rank_in_perm[c])
            chosen.append(c_pick)
            check_degrees[c_pick]+=1
        # after choosing d checks, record pairs
        for i in range(len(chosen)):
            for k in range(i+1, len(chosen)):
                a,b=chosen[i],chosen[k]
                check_pairs.add((min(a,b), max(a,b)))
        for c in chosen:
            H_support[c,j]=1
    # assign coefficients
    canonical=get_canonical_support_edges(H_support)
    coeffs=sample_uniform_gf32_nonzero(coeff_rng, len(canonical))
    H=np.zeros((m,n), dtype=np.uint8)
    for (r,c),val in zip(canonical, coeffs):
        H[r,c]=val
    return H, H_support, E, check_degrees

def metrics_for(H, H_support, E):
    field=GF2mField.create(32)
    m,n=H.shape
    rank=compute_gf32_rank(H, field)
    col_deg=np.count_nonzero(H_support, axis=0)
    row_deg=np.count_nonzero(H_support, axis=1)
    # cycles
    c4,c6,c8,edge_map=enumerate_canonical_simple_cycles(H_support)
    deg4=sum(classify_cycle_algebraic_degeneracy(c,H,field) for c in c4)
    deg6=sum(classify_cycle_algebraic_degeneracy(c,H,field) for c in c6)
    deg8=sum(classify_cycle_algebraic_degeneracy(c,H,field) for c in c8)
    max_chain, pure_ring = degree2_chain_and_pure_ring(H_support)
    # also count pure cycles len<=12 among enumerated: filter cycles where all vars dv==2
    col_deg_map=col_deg
    pure4=sum(1 for cyc in c4 if all(col_deg_map[v]==2 for v in cyc.vars))
    pure6=sum(1 for cyc in c6 if all(col_deg_map[v]==2 for v in cyc.vars))
    pure8=sum(1 for cyc in c8 if all(col_deg_map[v]==2 for v in cyc.vars))
    pure_total_len12 = pure4+pure6+pure8  # 4,6,8 only; 10,12 not enumerated
    return {
        "shape": (m,n),
        "rank": rank,
        "E": int(np.count_nonzero(H_support)),
        "expected_E": E,
        "col_deg_min": int(col_deg.min()),
        "col_deg_max": int(col_deg.max()),
        "col_deg_mean": float(col_deg.mean()),
        "col_deg_dist": {int(k): int((col_deg==k).sum()) for k in sorted(set(col_deg))},
        "row_deg_min": int(row_deg.min()),
        "row_deg_max": int(row_deg.max()),
        "row_deg_mean": float(row_deg.mean()),
        "dc_max_ok": int(row_deg.max())<=MAX_CHECK_DEGREE_LIMIT,
        "support_cycles_4": len(c4),
        "support_cycles_6": len(c6),
        "support_cycles_8": len(c8),
        "degenerate_4": deg4,
        "degenerate_6": deg6,
        "degenerate_8": deg8,
        "pure_4": pure4,
        "pure_6": pure6,
        "pure_8": pure8,
        "max_degree2_chain": max_chain,
        "pure_ring_len12_enumerated": pure_total_len12,
        "pure_ring_via_graph": pure_ring,
        "full_row_rank": rank==m,
        "zero_col": int((col_deg==0).sum()),
        "zero_row": int((row_deg==0).sum()),
    }

def run_once(label, dv_list):
    print(f"\n=== {label} ===")
    for src in ["1M","1p5M","2M"]:
        det=DET_IDS[src]
        H, Hs, E,_=construct_mixed(src, det, dv_list)
        met=metrics_for(H, Hs, E)
        print(f"\n-- {src} m={SOURCE_CHECKS[src]} det={det} --")
        for k,v in met.items():
            print(f"  {k}: {v}")
        # gate checks
        ok = (met["full_row_rank"] and met["zero_col"]==0 and met["zero_row"]==0 and met["dc_max_ok"] and met["support_cycles_4"]==0 and met["max_degree2_chain"]<=4 and met["pure_ring_via_graph"]==0)
        print(f"  GATE_ALL: {'PASS' if ok else 'FAIL'} (rank/zero/dc<=16/4-cycle==0/chain<=4/ring==0)")
        if met["support_cycles_4"]!=0:
            print("  -> 4-cycle hard gate FAILED")
        if met["max_degree2_chain"]>4:
            print(f"  -> chain {met['max_degree2_chain']} >4 FAILED")
        if met["pure_ring_via_graph"]!=0:
            print(f"  -> pure ring {met['pure_ring_via_graph']} !=0 FAILED")

if __name__=="__main__":
    # Test 1: all dv=2 (PEG-dv2) E=2048
    run_once("PEG-dv2 (dv=2 *1024) E=2048", [2]*1024)
    # Test 2: mixed MET {512x2,512x3} E=2560
    run_once("MET-mixed {dv2:512,dv3:512} E=2560", [2]*512+[3]*512)
    # Test 3: interleaved mixed for balance
    interleaved=[]
    for i in range(512):
        interleaved.extend([2,3])
    # interleaved length 1024, 512 each alternating -> same E
    run_once("MET-mixed-interleaved 2,3 alternating E=2560", interleaved)
