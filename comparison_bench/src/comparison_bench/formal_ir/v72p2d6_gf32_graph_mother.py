"""V72P2D6 GF32 graph/mother successor — standalone D6 module.

Reuse D5 arithmetic/prior/sampler/adapter/audit by import, never copy.
Graph/mother is the only axis; 8 arms frozen per prereg.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from collections import Counter, deque
import numpy as np

try:
    import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5
except ModuleNotFoundError:
    import importlib.util, pathlib, sys
    _p = pathlib.Path(__file__).resolve().parent / "v72p2d5_gf32_rate_mother.py"
    _spec = importlib.util.spec_from_file_location("v72p2d5_gf32_rate_mother", str(_p))
    assert _spec and _spec.loader
    d5 = importlib.util.module_from_spec(_spec)
    sys.modules["v72p2d5_gf32_rate_mother"] = d5
    _spec.loader.exec_module(d5)

# Frozen identifiers (R1c: unchanged; parallel-only revision, no semantic change)
ARMS = ["B0_D5_DV3_NATIVE","B1_D5_DV3_COMMON_LABELS","T1_PEG_DV3","T2_CYCLE_GREEDY_DV3","T3_SC_DV3_W4","T4_SC_DV3_W8","M1_ACCUMULATOR_FOREST_MAX","M2_ACCUMULATOR_FOREST_HALF"]
T_ARMS = ["T1_PEG_DV3","T2_CYCLE_GREEDY_DV3","T3_SC_DV3_W4","T4_SC_DV3_W8"]
M_ARMS = ["M1_ACCUMULATOR_FOREST_MAX","M2_ACCUMULATOR_FOREST_HALF"]

Q = 32
POLY = 37
ROW_BUDGETS = {
 64: {"L1":(49,59,64),"L2":(43,52,64),"k_min":{"L1":49,"L2":43}},
 128: {"L1":(98,118,128),"L2":(86,104,128),"k_min":{"L1":98,"L2":86}},
 256: {"L1":(196,236,256),"L2":(172,208,256),"k_min":{"L1":196,"L2":172}},
}
F_POINTS = {"f1.0":0,"f1.2":1,"square":2}  # index in prefix tuple

# N2 table per spec §5.3
N2_TABLE = {
 64: {"L1":{"MAX":48,"HALF":24},"L2":{"MAX":42,"HALF":21}},
 128: {"L1":{"MAX":97,"HALF":48},"L2":{"MAX":85,"HALF":42}},
 256: {"L1":{"MAX":195,"HALF":97},"L2":{"MAX":171,"HALF":85}},
}

COEFF_SEED_L1 = 202609120100
COEFF_SEED_L2 = 202609120200

# Formal roots to guard (reuse D5 constants + D6 dev root pattern)
FORMAL_ROOTS_GUARD = [
 d5.G0_FORMAL_ROOT, d5.G1_FORMAL_ROOT, d5.G2_FORMAL_ROOT,
 d5.G0_RECOVERY_FORMAL_ROOT, d5.MODEL_F_INPUT_FORMAL_ROOT,
 d5.P0_FORMAL_ROOT, "workspace/v72p2d5_structure/20260905_r2",
]

CANARY_SEEDS = tuple(range(2026091000,2026091004))
CONF_SEEDS = tuple(range(2026091010,2026091026))
SCALING_SEEDS = tuple(range(2026091100,2026091104))

class D6StructureBlocked(ValueError):
    pass

# R1c: read-only cache for the common coefficient stream (same array reused).
_COMMON_COEFFS_CACHE = {}

def _common_coeffs(n, layer):
    # R1c: cache reused across arm×layer parallel tasks (same (n,layer) stream).
    key = (int(n), str(layer))
    hit = _COMMON_COEFFS_CACHE.get(key)
    if hit is not None:
        return hit
    seed = (COEFF_SEED_L1 if layer=="L1" else COEFF_SEED_L2) + int(n)
    rng = np.random.default_rng(seed)
    vals = rng.integers(1,32,size=(n,3), dtype=np.int64)
    _COMMON_COEFFS_CACHE[key] = vals
    return vals

def _assign_common_coeffs(support, n, layer, m_max):
    vals = _common_coeffs(n, layer)
    # support shape (n, deg) where deg 2 or 3 per col; canonical ascending per col for degree3 but for M degree2 cols size2
    # For uniform handling, support arrays for B/T are (n,3); for M we handle (n,3) with -1 filler for degree2 third edge?
    # Here we provide helper for (n,3) with exactly 3 rows per col; M degree2 cols will use first two entries only.
    sup = np.asarray(support, dtype=np.int64)
    out = np.zeros((m_max, n), dtype=np.uint8)
    for v in range(n):
        # degree detection: if sup has 2 columns? second case
        if sup.ndim==2 and sup.shape[1]==2:
            rows = [int(sup[v,0]), int(sup[v,1])]
            for ei, r in enumerate(rows):
                if out[r,v]!=0:
                    raise ValueError("duplicate position")
                out[r,v]=np.uint8(int(vals[v,ei]))
        else:
            # sup shape (n,3) maybe with -1 sentinel
            cols = []
            for j in range(sup.shape[1]):
                r = int(sup[v,j])
                if r==-1:
                    continue
                cols.append(r)
            for ei, r in enumerate(cols):
                if out[r,v]!=0:
                    raise ValueError("duplicate position")
                # for M degree2 cols, ei 0,1 maps to vals 0,1
                out[r,v]=np.uint8(int(vals[v,ei]))
            # degree-3 cols use vals 0..2, degree2 use 0..1 (above)
    return out

# ponytail: deterministic support builders, O(n * candidates) naive, acceptable for n<=256
def _build_T1_support(n, m_max, k_min):
    B = list(range(k_min))
    C = list(range(m_max))
    support = np.full((n,3), -1, dtype=np.int64)
    deg = np.zeros(m_max, dtype=np.int64)
    used_pairs=set()
    used_triples=set()
    # adjacency for BFS: need per variable adjacency to checks
    # For PEG BFS we rebuild adjacency per variable from support built so far
    def bfs_distances(var):
        # build adjacency lists
        var_adj=[[] for _ in range(n)]
        chk_adj=[[] for _ in range(m_max)]
        for vv in range(n):
            for j in range(3):
                r=int(support[vv,j])
                if r!=-1:
                    var_adj[vv].append(r)
                    chk_adj[r].append(vv)
        # BFS from var
        INF=10**9
        # nodes: 0..n-1 vars, n..n+m_max-1 checks (offset)
        # but simple two-type BFS using queues
        dist_var=[INF]*n
        dist_chk=[INF]*m_max
        q=deque()
        dist_var[var]=0
        q.append(("v",var))
        # also consider edges of current var already placed (already in adjacency)
        while q:
            typ, idx = q.popleft()
            if typ=="v":
                d=dist_var[idx]
                for c in var_adj[idx]:
                    if dist_chk[c]==INF:
                        dist_chk[c]=d+1
                        q.append(("c",c))
            else:
                d=dist_chk[idx]
                for v2 in chk_adj[idx]:
                    if dist_var[v2]==INF:
                        dist_var[v2]=d+1
                        q.append(("v",v2))
        return dist_chk
    for v in range(n):
        # two base edges
        for edge_idx in range(2):
            dist = bfs_distances(v)
            cand = [c for c in B if c not in [int(support[v,0]), int(support[v,1])]]
            # filter duplicate pair for second edge later
            # need ordering by (distance desc, deg asc, index asc)
            def key(c):
                d=dist[c]
                inf = 10**9
                dd = inf if d>=inf else d
                # distance desc => -dd for sort asc, but inf largest => want inf first => -inf smallest
                return (-dd, int(deg[c]), c)
            cand_sorted = sorted(cand, key=key)
            placed=False
            for c in cand_sorted:
                if edge_idx==1:
                    b1=int(support[v,0])
                    pair=tuple(sorted((b1,c)))
                    if pair in used_pairs:
                        continue
                # also check no parallel edge (already ensuring not in chosen)
                support[v,edge_idx]=c
                # tentative check for duplicate pair/triple at expansion stage later
                deg[c]+=1
                if edge_idx==1:
                    used_pairs.add(tuple(sorted((int(support[v,0]), int(support[v,1])))))
                placed=True
                break
            if not placed:
                raise D6StructureBlocked("T1 PEG no base candidate")
        # expansion edge
        dist = bfs_distances(v)
        cand = [c for c in C if c not in [int(support[v,0]), int(support[v,1])]]
        def key2(c):
            d=dist[c]
            INF=10**9
            dd=INF if d>=INF else d
            return (-dd, int(deg[c]), c)
        cand_sorted = sorted(cand, key=key2)
        placed=False
        for c in cand_sorted:
            triple=tuple(sorted((int(support[v,0]), int(support[v,1]), c)))
            if triple in used_triples:
                continue
            support[v,2]=c
            deg[c]+=1
            used_triples.add(triple)
            placed=True
            break
        if not placed:
            raise D6StructureBlocked("T1 PEG no expansion candidate")
    # final checks: shape etc
    return support

def _build_T2_support(n, m_max, k_min):
    # incremental greedy per spec — ponytail: incremental O(candidates * avg_affected) instead of brute O(candidates*n)
    # R1c: adjacency bit-sets + support reuse; girth NOT computed inside loop
    # (final audit per packet §6 only). Choice key identical to R1.
    support = np.full((n,3), -1, dtype=np.int64)
    deg = np.zeros(m_max, dtype=np.int64)
    used_pairs=set()
    used_triples=set()
    pair_counts={}
    pair_to_cols={}  # pair -> set of cols containing it
    inc_per_col=[0]*n
    total_four=0
    max_pair=0
    incid_max=0
    B = list(range(k_min))
    C = list(range(m_max))
    for v in range(n):
        # enumerate legal triples quickly
        # ponytail: still O(B^2*C) per var, acceptable for n=64 but heavy; incremental evaluation keeps per-candidate cheap
        # Build candidate list
        candidates=[]
        for i,b1 in enumerate(B):
            for b2 in B[i+1:]:
                if tuple(sorted((b1,b2))) in used_pairs:
                    continue
                for e in C:
                    if e==b1 or e==b2:
                        continue
                    if tuple(sorted((b1,b2,e))) in used_triples:
                        continue
                    candidates.append((b1,b2,e))
        if not candidates:
            raise D6StructureBlocked("T2 no triple candidate")
        old_rmax = int(deg.max()) if v>0 or True else 0
        old_sumsq = int(np.sum(deg.astype(np.int64)**2))
        best=None; best_key=None
        best_inc=None
        for (b1,b2,e) in candidates:
            pairs=[tuple(sorted((b1,b2))), tuple(sorted((b1,e))), tuple(sorted((b2,e)))]
            occ=[pair_counts.get(p,0) for p in pairs]
            four = total_four + sum(occ)
            mpair = max(max_pair, occ[0]+1, occ[1]+1, occ[2]+1)
            inc_cand = sum(occ)
            affected=set()
            for p in pairs:
                if p in pair_to_cols:
                    affected.update(pair_to_cols[p])
            affected_max=0
            for col in affected:
                bb1=int(support[col,0]); bb2=int(support[col,1]); ee=int(support[col,2])
                share=sum(1 for pr in [tuple(sorted((bb1,bb2))), tuple(sorted((bb1,ee))), tuple(sorted((bb2,ee)))] if pr in pairs)
                new_inc = inc_per_col[col] + share
                if new_inc > affected_max:
                    affected_max=new_inc
            cur_incid = max(incid_max, inc_cand, affected_max)
            rmax_tmp = max(old_rmax, int(deg[b1])+1, int(deg[b2])+1, int(deg[e])+1)
            # sumsq delta: (d+1)^2 - d^2 = 2d+1
            rsumsq_tmp = old_sumsq + (2*int(deg[b1])+1) + (2*int(deg[b2])+1) + (2*int(deg[e])+1)
            stup=tuple(sorted((b1,b2,e)))
            key=(four, mpair, cur_incid, rmax_tmp, rsumsq_tmp, stup)
            if best_key is None or key < best_key:
                best_key=key
                best=(b1,b2,e)
                best_inc=(inc_cand, affected, pairs, occ)
        b1,b2,e = best
        support[v,0]=b1; support[v,1]=b2; support[v,2]=e
        deg[b1]+=1; deg[b2]+=1; deg[e]+=1
        used_pairs.add(tuple(sorted((b1,b2))))
        used_triples.add(tuple(sorted((b1,b2,e))))
        # update global structures
        # pair counts and total_four/mpair/inc per col
        pairs_best=[tuple(sorted((b1,b2))), tuple(sorted((b1,e))), tuple(sorted((b2,e)))]
        for p in pairs_best:
            before=pair_counts.get(p,0)
            pair_counts[p]=before+1
            if before>0:
                total_four+=before  # increment by occ
            if before+1 > max_pair:
                max_pair=before+1
            pair_to_cols.setdefault(p, set()).add(v)
        # incidence for new col
        inc_per_col[v]= sum(pair_counts[p]-1 for p in pairs_best)
        # update existing affected cols incidence
        # we already have affected set from best_inc
        _, affected_set, _, _ = best_inc
        for col in affected_set:
            bb1=int(support[col,0]); bb2=int(support[col,1]); ee=int(support[col,2])
            # recompute inc for col from scratch using pair_counts
            tot=0
            for pr in [tuple(sorted((bb1,bb2))), tuple(sorted((bb1,ee))), tuple(sorted((bb2,ee)))]:
                tot+= pair_counts.get(pr,0)-1
                if tot<0:
                    tot=0
            inc_per_col[col]=tot
        # update global incid_max
        incid_max = max(inc_per_col[:v+1]) if v>=0 else 0
    return support

# R1c-A6: exact-equivalent T2 acceleration switch. Reference
# _build_T2_support above is kept intact; production dispatches here.
_T2_FAST_ENABLED = True

def _build_T2_support_fast(n, m_max, k_min, trace=None):
    # Same candidate set, same integer key
    # (four, max_pair, incid_max, rmax, rsumsq, sorted_triple), same greedy
    # variable order and state updates as _build_T2_support. The key's last
    # field is the sorted triple, unique per candidate, so the lexicographic
    # argmin is unique and order-independent: staged filtering (cheap `four`
    # prefix first, later fields only for ties), vectorized enumeration,
    # integer-encoded pair/triple membership, incremental maintenance, and
    # skipping the affected rebuild for early-eliminated candidates all
    # preserve the exact argmin. No float arithmetic anywhere. Grid/index
    # arithmetic is int32 throughout: provably safe for m<=256 (pair ids
    # <2^16, triple ids <2^24, pair counts/degrees/sumsq/four <<2^31).
    n=int(n); m=int(m_max); k=int(k_min)
    support = np.full((n,3), -1, dtype=np.int64)
    deg = np.zeros(m, dtype=np.int32)
    UB = bytearray(m*m)
    UT = bytearray(m*m*m)
    UBN = np.frombuffer(UB, dtype=np.uint8)
    UTN = np.frombuffer(UT, dtype=np.uint8)
    PC = np.zeros(m*m, dtype=np.int32)
    cols_of_pair = [[] for _ in range(m*m)]
    inc_per_col=[0]*n
    total_four=0; max_pair=0; incid_max=0; old_rmax=0; old_sumsq=0
    QA=[]; QB=[]
    for _b1 in range(k):
        for _b2 in range(_b1+1, k):
            QA.append(_b1); QB.append(_b2)
    QA=np.asarray(QA, dtype=np.int32); QB=np.asarray(QB, dtype=np.int32)
    CVALS=np.arange(m, dtype=np.int32)
    QIDX=(QA.astype(np.int32)*np.int32(m)+QB).astype(np.int64)
    def _pid(a, b):
        return int(a)*m+int(b) if a<b else int(b)*m+int(a)
    for v in range(n):
        _vp = np.nonzero(UBN[QIDX]==0)[0]
        if _vp.size==0:
            raise D6StructureBlocked("T2 no triple candidate")
        _q1=QA[_vp]; _q2=QB[_vp]; _npairs=int(_q1.shape[0])
        _B1=np.repeat(_q1, m); _B2=np.repeat(_q2, m); _E=np.tile(CVALS, _npairs)
        _keep=(_E!=_B1)&(_E!=_B2)
        _B1=_B1[_keep]; _B2=_B2[_keep]; _E=_E[_keep]
        _i1=np.minimum(np.minimum(_B1, _B2), _E)
        _i3=np.maximum(np.maximum(_B1, _B2), _E)
        _i2=(_B1+_B2+_E-_i1-_i3)
        _tids=(_i1*m+_i2)*m+_i3
        _keep2=UTN[_tids]==0
        if not bool(np.any(_keep2)):
            raise D6StructureBlocked("T2 no triple candidate")
        _B1=_B1[_keep2]; _B2=_B2[_keep2]; _E=_E[_keep2]; _tids=_tids[_keep2]
        _b1i=_B1; _b2i=_B2; _ei=_E
        _pA=_b1i*m+_b2i
        _pB=np.where(_b1i<_ei, _b1i*m+_ei, _ei*m+_b1i)
        _pC=np.where(_b2i<_ei, _b2i*m+_ei, _ei*m+_b2i)
        _o1=PC[_pA]; _o2=PC[_pB]; _o3=PC[_pC]
        _four=total_four+_o1+_o2+_o3
        _F0=int(np.min(_four))
        _S1=_four==_F0
        _mp=np.maximum(np.maximum(_o1+1, _o2+1), _o3+1)
        _mp=np.maximum(_mp, max_pair)
        _M0=int(np.min(_mp[_S1]))
        _idx=np.nonzero(_S1&(_mp==_M0))[0]
        _base=np.maximum(incid_max, _o1[_idx]+_o2[_idx]+_o3[_idx])
        _rmax=np.maximum(np.maximum(deg[_b1i[_idx]]+1, deg[_b2i[_idx]]+1),
                         np.maximum(deg[_ei[_idx]]+1, old_rmax))
        _rsq=(old_sumsq+(2*deg[_b1i[_idx]]+1)+(2*deg[_b2i[_idx]]+1)+(2*deg[_ei[_idx]]+1))
        _order=np.lexsort((_tids[_idx], _rsq, _rmax, _base))
        _best=None; _choice=None
        for _t, _j in enumerate(_order):
            _bb=int(_base[_j]); _rr=int(_rmax[_j]); _ss=int(_rsq[_j]); _tt=int(_tids[_idx[_j]])
            if _best is not None:
                _Kb=_best
                if _bb>_Kb[2] or (_bb==_Kb[2] and (_rr>_Kb[3] or (_rr==_Kb[3] and (_ss>_Kb[4] or (_ss==_Kb[4] and _tt>=_Kb[5]))))):
                    break  # lexsorted: every later candidate is worse
            _lim=None if _best is None else int(_best[2])
            _affmax=0; _seen=set()
            _cb1=int(_b1i[_idx[_j]]); _cb2=int(_b2i[_idx[_j]]); _ce=int(_ei[_idx[_j]])
            for _p in (_pid(_cb1, _cb2), _pid(_cb1, _ce), _pid(_cb2, _ce)):
                for _col in cols_of_pair[_p]:
                    if _col in _seen:
                        continue
                    _seen.add(_col)
                    _qb1=int(support[_col,0]); _qb2=int(support[_col,1]); _qe=int(support[_col,2])
                    _nv=inc_per_col[_col]+((_pid(_qb1, _qb2)==_p)+(_pid(_qb1, _qe)==_p)+(_pid(_qb2, _qe)==_p))
                    if _nv>_affmax:
                        _affmax=_nv
                        if _lim is not None and _affmax>_lim:
                            break
                if _lim is not None and _affmax>_lim:
                    break
            _cur=_bb if _bb>_affmax else _affmax
            if _cur<incid_max:
                _cur=incid_max
            _full=(_F0, _M0, _cur, _rr, _ss, _tt)
            if _best is None or _full<_best:
                _best=_full; _choice=(_cb1, _cb2, _ce)
        b1,b2,e=_choice
        if trace is not None:
            trace.append((b1,b2,e))
        support[v,0]=b1; support[v,1]=b2; support[v,2]=e
        deg[b1]+=1; deg[b2]+=1; deg[e]+=1
        UB[_pid(b1,b2)]=1
        _lo=b1 if b1<b2 and b1<e else (b2 if b2<e else e)
        _hi=b1 if b1>b2 and b1>e else (b2 if b2>e else e)
        _mid=b1+b2+e-_lo-_hi
        UT[(_lo*m+_mid)*m+_hi]=1
        for _p in (_pid(b1,b2), _pid(b1,e), _pid(b2,e)):
            _before=int(PC[_p])
            PC[_p]=_before+1
            if _before>0:
                total_four+=_before
            if _before+1>max_pair:
                max_pair=_before+1
            cols_of_pair[_p].append(v)
        inc_per_col[v]=int(PC[_pid(b1,b2)]-1)+int(PC[_pid(b1,e)]-1)+int(PC[_pid(b2,e)]-1)
        _aff=set()
        for _p in (_pid(b1,b2), _pid(b1,e), _pid(b2,e)):
            _aff.update(cols_of_pair[_p])
        _aff.discard(v)
        for _col in _aff:
            _qb1=int(support[_col,0]); _qb2=int(support[_col,1]); _qe=int(support[_col,2])
            _tot=0
            for _pr in (_pid(_qb1,_qb2), _pid(_qb1,_qe), _pid(_qb2,_qe)):
                _tot+=int(PC[_pr])-1
                if _tot<0:
                    _tot=0
            inc_per_col[_col]=_tot
            if _tot>incid_max:
                incid_max=_tot
        if inc_per_col[v]>incid_max:
            incid_max=inc_per_col[v]
        if int(deg[b1])>old_rmax:
            old_rmax=int(deg[b1])
        if int(deg[b2])>old_rmax:
            old_rmax=int(deg[b2])
        if int(deg[e])>old_rmax:
            old_rmax=int(deg[e])
        old_sumsq+=(2*(int(deg[b1])-1)+1)+(2*(int(deg[b2])-1)+1)+(2*(int(deg[e])-1)+1)
    return support

def _build_SC_support(n, m_max, k_min, w):
    support=np.full((n,3), -1, dtype=np.int64)
    deg=np.zeros(m_max, dtype=np.int64)
    used_pairs=set()
    used_triples=set()
    window_overflow=0
    for v in range(n):
        a_v=(v*k_min)//n
        b_v=(v*m_max)//n
        Wb=[x for x in range(a_v, a_v+w) if 0 <= x < k_min]
        We=[x for x in range(b_v, b_v+w) if 0 <= x < m_max]
        # base pair: order Wb by (deg,index), try pairs lexicographically
        Wb_sorted=sorted(Wb, key=lambda x: (int(deg[x]), x))
        placed_pair=None
        for i in range(len(Wb_sorted)):
            for j in range(i+1, len(Wb_sorted)):
                b1=Wb_sorted[i]; b2=Wb_sorted[j]
                if tuple(sorted((b1,b2))) in used_pairs:
                    continue
                placed_pair=(b1,b2)
                break
            if placed_pair:
                break
        if placed_pair is None:
            # extend to full B
            Ball=list(range(k_min))
            Ball_sorted=sorted(Ball, key=lambda x: (int(deg[x]), x))
            for i in range(len(Ball_sorted)):
                for j in range(i+1, len(Ball_sorted)):
                    b1=Ball_sorted[i]; b2=Ball_sorted[j]
                    if b1 not in Wb or b2 not in Wb:
                        pass
                    if tuple(sorted((b1,b2))) in used_pairs:
                        continue
                    placed_pair=(b1,b2)
                    window_overflow+=1
                    break
                if placed_pair:
                    break
            # if still none, blocked
            if placed_pair is None:
                raise D6StructureBlocked(f"SC w{w} no base pair")
            else:
                # count overflow already
                pass
        b1,b2=placed_pair
        # expansion: order We - {b1,b2} by deg
        We_cand=[c for c in We if c not in (b1,b2)]
        We_cand_sorted=sorted(We_cand, key=lambda x: (int(deg[x]), x))
        placed_e=None
        for c in We_cand_sorted:
            if tuple(sorted((b1,b2,c))) in used_triples:
                continue
            placed_e=c
            break
        if placed_e is None:
            # extend to full C - base
            Call=[c for c in range(m_max) if c not in (b1,b2)]
            Call_sorted=sorted(Call, key=lambda x: (int(deg[x]), x))
            for c in Call_sorted:
                if c in We_cand:
                    continue
                if tuple(sorted((b1,b2,c))) in used_triples:
                    continue
                placed_e=c
                window_overflow+=1
                break
            if placed_e is None:
                raise D6StructureBlocked(f"SC w{w} no expansion")
        support[v,0]=b1; support[v,1]=b2; support[v,2]=placed_e
        deg[b1]+=1; deg[b2]+=1; deg[placed_e]+=1
        used_pairs.add(tuple(sorted((b1,b2))))
        used_triples.add(tuple(sorted((b1,b2,placed_e))))
    # store overflow diagnostic as attribute? We'll return and record externally
    support = np.asarray(support)
    # attach overflow via function attribute hack: store in global dict? Simpler: return tuple
    return support, window_overflow

def _build_M_support(n, m_max, k_min, mode):
    # mode MAX -> N2=k_min-1 else floor((k_min-1)/2)
    if mode=="MAX":
        N2=k_min-1
    else:
        N2=(k_min-1)//2
    # Use N2_TABLE validation but compute directly
    support = np.full((n,3), -1, dtype=np.int64)
    deg=np.zeros(m_max, dtype=np.int64)
    used_pairs=set()
    used_triples=set()
    # degree-2 chain edges (i,i+1) for variables 0..N2-1
    for v in range(N2):
        r1=v
        r2=v+1
        # chain must be within first k_min checks: v up to N2-1 => v+1 <= k_min-1 ensured because N2=k_min-1
        if r2>=k_min:
            raise D6StructureBlocked("M chain out of B zone")
        support[v,0]=r1; support[v,1]=r2
        # leave third col -1
        deg[r1]+=1; deg[r2]+=1
        # M degree-2: no pair/triple tracking for base pair duplicates? still need pair duplicates zero globally
        # pair is (r1,r2)
        pair=tuple(sorted((r1,r2)))
        if pair in used_pairs:
            raise D6StructureBlocked("M duplicate chain pair")
        used_pairs.add(pair)
        # triple not applicable (degree2 has no expansion)
    # degree-3 variables N2..n-1: 2 base +1 expansion with degree-balanced lexicographic
    for v in range(N2, n):
        # base pair: first unused pair from B ordered by (deg,index) lexicographic combination order
        # Approach: generate all pairs b1<b2 from B, sort by (deg[b1]+deg[b2]? No spec says combination order by (deg, index) lexicographic — meaning order pairs by tuple of sorted W? We interpret: order individual rows by (deg,index), then pairs in lexicographic order of that ranking.
        B_sorted=sorted(range(k_min), key=lambda x: (int(deg[x]), x))
        placed=None
        # generate pairs in lexicographic order of B_sorted order
        for i in range(len(B_sorted)):
            for j in range(i+1, len(B_sorted)):
                b1=B_sorted[i]; b2=B_sorted[j]
                # for deterministic need sorted b1<b2? The spec says first unused pair from B ordered by (deg,index) lexicographic combination order. So keep order as per sorted list order, not numeric sort. But triple duplicate check uses sorted triple, so order inside pair not important.
                pair=tuple(sorted((b1,b2)))
                if pair in used_pairs:
                    continue
                placed=(b1,b2)
                break
            if placed:
                break
        if placed is None:
            raise D6StructureBlocked("M no base pair")
        b1,b2=placed
        # expansion: first row of C - base in (deg,index) order with triple unused
        Call=[c for c in range(m_max) if c not in (b1,b2)]
        Call_sorted=sorted(Call, key=lambda x: (int(deg[x]), x))
        placed_e=None
        for c in Call_sorted:
            if tuple(sorted((b1,b2,c))) in used_triples:
                continue
            placed_e=c
            break
        if placed_e is None:
            raise D6StructureBlocked("M no expansion")
        support[v,0]=b1; support[v,1]=b2; support[v,2]=placed_e
        deg[b1]+=1; deg[b2]+=1; deg[placed_e]+=1
        used_pairs.add(tuple(sorted((b1,b2))))
        used_triples.add(tuple(sorted((b1,b2,placed_e))))
    # For remaining degree2 vars, support third column stays -1; caller must handle coefficient mapping (use first two vals)
    return support

def support_window_overflow(arm, n, layer):
    # Diagnostic replay of the T3/T4 window-overflow counter (0 for others).
    # Rebuilds deterministically; caller compares with the primary build.
    k_min=ROW_BUDGETS[int(n)]["k_min"][layer]
    m_max=int(n)
    if arm=="T3_SC_DV3_W4":
        _, ov = _build_SC_support(int(n), m_max, k_min, 4)
        return int(ov)
    if arm=="T4_SC_DV3_W8":
        _, ov = _build_SC_support(int(n), m_max, k_min, 8)
        return int(ov)
    return 0

# Public builders
def build_support(arm, n, layer):
    k_min=ROW_BUDGETS[int(n)]["k_min"][layer]
    m_max=int(n)
    if arm=="B0_D5_DV3_NATIVE":
        seed = d5.L1_GRAPH_SEED if layer=="L1" else d5.L2_GRAPH_SEED
        # use D5 support builder for exact D5 support
        sup = d5.build_dv3_nested_support(int(n), int(m_max), int(k_min), int(seed))
        return sup
    elif arm=="B1_D5_DV3_COMMON_LABELS":
        # same support as B0 but coefficients later will be common stream; support same
        seed = d5.L1_GRAPH_SEED if layer=="L1" else d5.L2_GRAPH_SEED
        sup = d5.build_dv3_nested_support(int(n), int(m_max), int(k_min), int(seed))
        return sup
    elif arm=="T1_PEG_DV3":
        return _build_T1_support(int(n), int(m_max), int(k_min))
    elif arm=="T2_CYCLE_GREEDY_DV3":
        if _T2_FAST_ENABLED:
            return _build_T2_support_fast(int(n), int(m_max), int(k_min))
        return _build_T2_support(int(n), int(m_max), int(k_min))
    elif arm=="T3_SC_DV3_W4":
        sup,_ = _build_SC_support(int(n), int(m_max), int(k_min), 4)
        return sup
    elif arm=="T4_SC_DV3_W8":
        sup,_ = _build_SC_support(int(n), int(m_max), int(k_min), 8)
        return sup
    elif arm=="M1_ACCUMULATOR_FOREST_MAX":
        return _build_M_support(int(n), int(m_max), int(k_min), "MAX")
    elif arm=="M2_ACCUMULATOR_FOREST_HALF":
        return _build_M_support(int(n), int(m_max), int(k_min), "HALF")
    else:
        raise ValueError(f"unknown arm {arm}")

def assign_mother_from_support(arm, n, layer, sup, m_max):
    # R1c-A4: pure coefficient assignment from an exact support (math moved
    # verbatim from build_mother; outputs bit-identical to build_mother).
    if arm=="B0_D5_DV3_NATIVE":
        seed = d5.L1_GRAPH_SEED if layer=="L1" else d5.L2_GRAPH_SEED
        return d5.assign_gf32_coefficients(sup, int(seed), None, int(m_max))
    # Use common stream; handle M degree2 -1 sentinel
    # Build H via helper that maps support to matrix
    # For sup with -1 sentinel (M degree2), we call _assign_common_coeffs
    return _assign_common_coeffs(sup, int(n), layer, int(m_max))

def build_mother(arm, n, layer):
    sup = build_support(arm, n, layer)
    m_max=int(n)
    return assign_mother_from_support(arm, int(n), layer, sup, m_max), sup

def build_support_with_overflow(arm, n, layer):
    # R1c-A4: (support, window_overflow) from the single primary build.
    # The SC builder already counts overflow; build_support discards it and
    # support_window_overflow rebuilt it — this passthrough removes that
    # diagnostic rebuild. Identical support to build_support.
    k_min=ROW_BUDGETS[int(n)]["k_min"][layer]
    m_max=int(n)
    if arm=="T3_SC_DV3_W4":
        sup, ov = _build_SC_support(int(n), m_max, k_min, 4)
        return sup, int(ov)
    if arm=="T4_SC_DV3_W8":
        sup, ov = _build_SC_support(int(n), m_max, k_min, 8)
        return sup, int(ov)
    return build_support(arm, n, layer), 0

# Girth via BFS from each variable node
def compute_girth(H):
    # H shape (m,n) ; bipartite graph: vars 0..n-1 checks 0..m-1
    m,n = H.shape
    # build adjacency
    var_adj=[np.flatnonzero(H[:,v]).tolist() if False else [] for v in range(n)] # placeholder
    # better: use row-wise
    var_adj=[[] for _ in range(n)]
    chk_adj=[[] for _ in range(m)]
    rows, cols = np.nonzero(H)
    for r,c in zip(rows, cols):
        var_adj[int(c)].append(int(r))
        chk_adj[int(r)].append(int(c))
    INF=10**9
    best=INF
    for start in range(n):
        # BFS with parent tracking to detect cycle
        dist_v=[-1]*n
        dist_c=[-1]*m
        parent_v=[-1]*n
        parent_c=[-1]*m
        q=deque()
        dist_v[start]=0
        q.append(("v",start))
        while q:
            typ, idx = q.popleft()
            if typ=="v":
                d=dist_v[idx]
                if d+1 >= best:
                    continue
                for c in var_adj[idx]:
                    if dist_c[c]==-1:
                        dist_c[c]=d+1
                        parent_c[c]=idx
                        q.append(("c",c))
                    elif parent_v[idx]!=c:  # found cycle via edge v-c where c already visited from another var path
                        # cycle length = dist_v[idx]+dist_c[c]+1
                        cl = dist_v[idx]+dist_c[c]+1
                        if cl < best:
                            best=cl
            else:
                d=dist_c[idx]
                if d+1 >= best:
                    continue
                for v in chk_adj[idx]:
                    if dist_v[v]==-1:
                        dist_v[v]=d+1
                        parent_v[v]=idx
                        q.append(("v",v))
                    elif parent_c[idx]!=v:
                        cl = dist_c[idx]+dist_v[v]+1
                        if cl < best:
                            best=cl
        if best==4:
            break
    if best==INF:
        return None, "acyclic"
    return int(best), None

def m_cycle_rank(H, k_min):
    # degree-2 subgraph cycle rank for M arms: edges - vertices + components over touched checks?
    # For M, degree-2 variables are first N2 vars with edges (i,i+1) etc plus any? But we compute degree-2 subgraph as those columns with degree2 (support -1 sentinel would be degree2)
    # Instead compute from H prefix k? For M, the degree-2 edges are only over first k_min checks, but we can computeTouched checks: those rows that have degree from degree2 columns only? Simpler: use support derived but we reconstruct from H: columns with degree 2 in prefix k_min are degree-2 vars, others degree 3. Build DSU over checks involved in degree2 edges.
    # H shape (m_max,n), we consider prefix k = k_min (relevant prefix). Count edges = sum deg of degree2 columns within prefix; vertices = number of distinct checks touched by degree2 edges; components via DSU.
    # For our M constructions, degree2 subgraph is a forest => cycle rank 0.
    # For general detection, implement DSU over checks.
    m,n = H.shape
    k=int(k_min)
    # find degree2 columns: those with exactly 2 nonzeros in full matrix but within prefix maybe?
    # Use full H column degree; but per spec: degree-2 subgraph over first k_min checks at every relevant prefix. So for prefix k, degree2 columns are those with both edges inside [0,k). Our stored H has all m_max rows; for prefix k, we should count only edges with row<k.
    # For cycle rank check, we evaluate at prefix k (k_min). So edges are degree2 variables' edges that lie inside [0,k).
    # For MAX/HALF, they are chain inside B, so all their edges inside.
    # We'll just consider all columns that have degree 2 total and both rows < k
    total_deg=(H!=0).sum(axis=0)
    deg_inside=(H[:k,:]!=0).sum(axis=0)
    dsu_parent=list(range(k))
    def find(x):
        while dsu_parent[x]!=x:
            dsu_parent[x]=dsu_parent[dsu_parent[x]]
            x=dsu_parent[x]
        return x
    def union(a,b):
        ra=find(a); rb=find(b)
        if ra!=rb:
            dsu_parent[ra]=rb
    edges=0
    touched=set()
    for v in range(n):
        if int(total_deg[v])==2 and int(deg_inside[v])==2:
            rows=np.flatnonzero(H[:k,v]).tolist()
            if len(rows)!=2:
                continue
            a,b = int(rows[0]), int(rows[1])
            edges+=1
            touched.add(a); touched.add(b)
            ra=find(a); rb=find(b)
            if ra!=rb:
                dsu_parent[ra]=rb
    if not touched:
        return 0
    comps=len(set(find(x) for x in touched))
    verts=len(touched)
    rank = edges - verts + comps
    return int(rank)

def audit_extra(H, k, arm=None):
    # wrapper returning extra diagnostics beyond d5 audit_prefix
    m,n=H.shape
    girth, reason = compute_girth(H[:k,:])
    row_deg = (H[:k,:]!=0).sum(axis=1)
    rmax=int(row_deg.max()) if row_deg.size else 0
    rsumsq=int(np.sum(row_deg.astype(np.int64)**2))
    # R1c-A5 I1: check-node degree invariant diagnostics (exposed, not persisted).
    rmin=int(row_deg.min()) if row_deg.size else 0
    nbelow=int((row_deg < 2).sum()) if row_deg.size else 0
    # M cycle rank if arm is M
    if arm in M_ARMS:
        k_min = k  # for current prefix, but spec says forest over first k_min checks at every relevant prefix; using current prefix k as k_min for that layer? We'll compute using k_min of that prefix? For simplicity use k (since prefix == k_min for f1.0)
        cr=m_cycle_rank(H, k)
    else:
        cr=None
    # determinism replay: build twice already handled externally; here just flag
    # window overflow tracked elsewhere
    return {"girth": girth, "girth_reason": reason, "row_degree_max": rmax, "row_degree_sumsq": rsumsq, "m_cycle_rank": cr, "row_degree_min": rmin, "rows_below_degree_2": nbelow}

# R1c-A5 I1 (frozen): every dispatched check row has degree >= 2.
I1_MIN_CHECK_DEGREE = 2

def check_I1_row_degree(H, k):
    """Structure-only I1 check: (row_degree_min, rows_below_degree_2) for H[:k]."""
    import numpy as _np
    _H = _np.asarray(H)
    _rd = (_H[:int(k), :] != 0).sum(axis=1)
    if _rd.size == 0:
        return (0, 0)
    return (int(_rd.min()), int((_rd < int(I1_MIN_CHECK_DEGREE)).sum()))

def assert_dispatchable_matrices(h1, h2):
    """Dispatch-time fail-closed I1 guard (structure-only, zero decoder).

    Raises ValueError with a clear message if any check row of either slice
    has degree < 2. Call before any decoder invocation.
    """
    import numpy as _np
    for _name, _h in (("L1", h1), ("L2", h2)):
        _a = _np.asarray(_h)
        if _a.size == 0:
            raise ValueError("D6 I1 dispatch guard: empty %s matrix" % _name)
        _rd = (_a != 0).sum(axis=1)
        if int(_rd.min()) < int(I1_MIN_CHECK_DEGREE):
            raise ValueError("D6 I1 dispatch guard: %s check row degree < 2 (min=%d, rows_below=%d)" % (_name, int(_rd.min()), int((_rd < 2).sum())))

def execution_block_terminal(counted_rows):
    """R1c-A5 execution-integrity terminal override (verifier/runner shared rule).

    Scans counted (call_idx>=0) decoder records for crash/nonfinite. None if
    clean; else D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED for degree-ValueError,
    else D6_GRAPH_ATTEMPTED_CELL_INVALID. Placeholders excluded by caller.
    """
    _deg = 0
    _other = 0
    for _r in (counted_rows or []):
        try:
            _ci = int(_r.get("call_idx", -1))
        except (TypeError, ValueError):
            continue
        if _ci < 0:
            continue
        _crash = str(_r.get("crash", "False")) == "True"
        _finite = str(_r.get("finite", "True")) == "True"
        if (not _crash) and _finite:
            continue
        if "Check node requires degree" in str(_r.get("error", "")):
            _deg += 1
        else:
            _other += 1
    if _deg:
        return "D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED"
    if _other:
        return "D6_GRAPH_ATTEMPTED_CELL_INVALID"
    return None

def assert_no_formal_write(out_root):
    rp = Path(out_root).resolve() if out_root else None
    for f in FORMAL_ROOTS_GUARD:
        cand = Path(f)
        if not cand.is_absolute():
            repo = Path(__file__).resolve().parents[4]
            cand = (repo / cand).resolve()
        else:
            cand = cand.resolve()
        if rp is not None and str(rp) == str(cand):
            raise ValueError(f"refusing to write to formal root {cand}")
        # also prefix guard
        if rp is not None:
            try:
                rp.relative_to(cand)
                raise ValueError(f"out_root {rp} is inside formal root {cand}")
            except ValueError:
                pass

def _structural_key(structure_summary, arm):
    # Frozen §6 key from the f1.2-prefix audits of both layers:
    # (four_sum, incidence_max, -girth, row_max, sumsq, arm_id).
    # NOT_COMPUTED girth acts as -1 (worst), i.e. key 1.
    layers=structure_summary.get(arm, {})
    total_four=0
    max_inc=0
    min_girth=10**9
    max_rmax=0
    sumsq=0
    for layer, rec in layers.items():
        audits=rec.get("prefix_audits", [])
        if len(audits)>=2:
            a=audits[1]
        elif audits:
            a=audits[0]
        else:
            a={}
        total_four+=int(a.get("four_cycles",0))
        max_inc=max(max_inc, int(a.get("four_cycle_variable_incidence_max",0)))
        g=a.get("girth")
        if g is not None and g!=-1:
            if g < min_girth:
                min_girth=g
        else:
            min_girth=-1  # NOT_COMPUTED sentinel, worst
        max_rmax=max(max_rmax, int(a.get("row_degree_max",0)))
        sumsq+=int(a.get("row_degree_sumsq",0))
    girth_key = -min_girth if min_girth!=-1 and min_girth!=10**9 else 1
    return (total_four, max_inc, girth_key, max_rmax, sumsq, arm)

def structural_rank_list(structure_summary, arms):
    # Frozen structural ordering over any arm subset (T finalists, M fallback).
    return sorted(arms, key=lambda a: _structural_key(structure_summary, a))

def select_advancement(canary, structural_order):
    # Frozen §8.2 advancement: pool = new T/M finalists only (caller excludes
    # B0/B1); advance on f1.2 end-to-end APP exact >= 1/4 (of 4 canary seeds),
    # at most two, ordered by (f1.2 exact desc, f1.2 iter-total asc,
    # square exact desc, structural rank, arm_id).
    # canary: arm -> {"f12_exact":int, "f12_iter":int, "sq_exact":int}.
    order_index = {a: i for i, a in enumerate(structural_order)}
    cands = [a for a, s in canary.items() if int(s.get("f12_exact", 0)) >= 1]
    cands.sort(key=lambda a: (-int(canary[a].get("f12_exact", 0)),
                              int(canary[a].get("f12_iter", 0)),
                              -int(canary[a].get("sq_exact", 0)),
                              order_index.get(a, 10**9), a))
    return cands[:2]

def select_decoder_arms(structure_summary):
    # structure_summary: dict arm -> dict layer -> per-prefix metrics
    # Returns frozen selection per spec §6: B0+B1+best2 T + both M if eligible
    eligible = {}
    for arm, layers in structure_summary.items():
        ok=True
        for layer, rec in layers.items():
            for pref in rec.get("prefix_audits", []):
                if not pref.get("eligible", False):
                    ok=False
        eligible[arm]=ok
    # selection: B0 always, B1 control
    selected=["B0_D5_DV3_NATIVE"]
    if eligible.get("B1_D5_DV3_COMMON_LABELS", False):
        selected.append("B1_D5_DV3_COMMON_LABELS")
    else:
        # even if not eligible? spec says freeze B1 label control; but hard gate applies to all arms; if ineligible still recorded
        # keep it if built but ineligible? Still freeze per spec but eligible check will decide; we keep for decoder set only if eligible
        pass
    # T ranking: eligible only, frozen §6 key via structural_rank_list.
    t_elig = [arm for arm in T_ARMS if eligible.get(arm, False)]
    for arm in structural_rank_list(structure_summary, t_elig)[:2]:
        selected.append(arm)
    for arm in M_ARMS:
        if eligible.get(arm, False):
            selected.append(arm)
    # max 6
    selected = selected[:6]
    return selected, eligible

def classify_terminal(per_f, nonfinite, crashes, rss_ok, syndrome_disagreement):
    # per_f list of dicts for f1.0,f1.2,square app_exact counts
    if crashes or nonfinite or syndrome_disagreement or not rss_ok:
        return "D6_GRAPH_N64_SIGNAL_INVALID"
    f1_0 = per_f[0]["exact"] if len(per_f)>0 else 0
    f1_2 = per_f[1]["exact"] if len(per_f)>1 else 0
    square = per_f[2]["exact"] if len(per_f)>2 else 0
    if not (f1_0 <= f1_2 <= square):
        return "D6_GRAPH_N64_SIGNAL_INVALID"
    if f1_2 >= 12:
        return "D6_GRAPH_STRONG_N64_RECOVERY"
    if 1 <= f1_2 <= 11:
        return "D6_GRAPH_PARTIAL_N64_SIGNAL"
    if square>0:
        return "D6_GRAPH_SQUARE_ONLY_DIAGNOSTIC"
    return "D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY"

def write_structure_records(path, records):
    # records: list of dicts per (arm,n,layer,prefix)
    header="arm,n,layer,prefix_rows,rank,zero_rows,zero_columns,connected_components,largest_component_fraction,four_cycles,four_cycle_variable_incidence_max,duplicate_projective_columns,base_pair_duplicates,support_triple_duplicates,row_degree_max,row_degree_sumsq,girth,girth_reason,m_cycle_rank,window_overflow,eligible,determinism_ok\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header)
        for r in records:
            fh.write(",".join(str(r.get(k,"")) for k in ["arm","n","layer","prefix_rows","rank","zero_rows","zero_columns","connected_components","largest_component_fraction","four_cycles","four_cycle_variable_incidence_max","duplicate_projective_columns","base_pair_duplicates","support_triple_duplicates","row_degree_max","row_degree_sumsq","girth","girth_reason","m_cycle_rank","window_overflow","eligible","determinism_ok"])+"\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception as ex:  # R1c-A2 fail closed
            raise RuntimeError("fsync-failed structure_records: %r" % (ex,))

# ---------------------------------------------------------------------------
# R1d Option C (eligible-only successor, frozen; no SC/M knob lift).
# Additive only: every builder, gate, and writer above is untouched.
# ---------------------------------------------------------------------------
R1D_ARMS = ["B0_D5_DV3_NATIVE", "B1_D5_DV3_COMMON_LABELS", "T1_PEG_DV3"]
R1D_NEW_ARM = "T1_PEG_DV3"  # sole new arm; B0/B1 are controls, never advance
R1D_SCALING_FALLBACKS = ["T1_PEG_DV3"]  # T1-only scaling fallback; no M leg
R1D_STRUCTURE_SCHEMA = "r1d-v2"
R1D_ELIGIBLE_SEMANTICS = "frozen-AND-I1"
# Frozen R1d dispatch subset: every distinct (arm,n,layer,prefix_rows) the
# unchanged schedule can dispatch (22 distinct cells: canary n64 f1.2+square
# x3 arms; confirmation n64 f1.0/f1.2/square xT1, sharing the 4 T1 f1.2/square
# cells with canary; scaling n128/n256 f1.2+square xT1), proven
# frozen-eligible AND I1-passing in D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv.
R1D_VALID_SUBSET = frozenset([
    ("B0_D5_DV3_NATIVE", 64, "L1", 59), ("B0_D5_DV3_NATIVE", 64, "L1", 64),
    ("B0_D5_DV3_NATIVE", 64, "L2", 52), ("B0_D5_DV3_NATIVE", 64, "L2", 64),
    ("B1_D5_DV3_COMMON_LABELS", 64, "L1", 59),
    ("B1_D5_DV3_COMMON_LABELS", 64, "L1", 64),
    ("B1_D5_DV3_COMMON_LABELS", 64, "L2", 52),
    ("B1_D5_DV3_COMMON_LABELS", 64, "L2", 64),
    ("T1_PEG_DV3", 64, "L1", 49), ("T1_PEG_DV3", 64, "L1", 59),
    ("T1_PEG_DV3", 64, "L1", 64), ("T1_PEG_DV3", 64, "L2", 43),
    ("T1_PEG_DV3", 64, "L2", 52), ("T1_PEG_DV3", 64, "L2", 64),
    ("T1_PEG_DV3", 128, "L1", 118), ("T1_PEG_DV3", 128, "L1", 128),
    ("T1_PEG_DV3", 128, "L2", 104), ("T1_PEG_DV3", 128, "L2", 128),
    ("T1_PEG_DV3", 256, "L1", 236), ("T1_PEG_DV3", 256, "L1", 256),
    ("T1_PEG_DV3", 256, "L2", 208), ("T1_PEG_DV3", 256, "L2", 256),
])
# Immutable history R1d must never overwrite or ingest as science input:
# the R1c-A2 six-file root plus the three VOID_RETAINED_ZERO_REUSE roots.
R1D_REFUSED_ROOTS = (
    "workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b",
    "workspace/d6_graph_mother_r1c_923a25897087495ab4605870e561f3cc",
    "workspace/d6_graph_mother_r1c_e8ee45a4669c4738bf7e96d926ba7e5c",
    "workspace/d6_graph_mother_r1c_f15cfa29baa2458e804c80a9f1045140",
)

def assert_r1d_arm(arm):
    """R1d arm-set gate: SC/M/T2 are structurally inadmissible as frozen."""
    if str(arm) not in R1D_ARMS:
        raise ValueError(
            "D6 R1d inadmissible arm %r (eligible-only %s)"
            % (str(arm), ",".join(R1D_ARMS)))

def assert_r1d_dispatchable(arm, n, layer, prefix_rows, h_slice=None):
    """R1d fail-closed dispatch guard: frozen-subset membership AND live I1.

    Raises ValueError for any cell outside R1D_VALID_SUBSET or with a live
    check row degree < 2. Call before any decoder invocation.
    """
    _key = (str(arm), int(n), str(layer), int(prefix_rows))
    assert_r1d_arm(arm)
    if _key not in R1D_VALID_SUBSET:
        raise ValueError(
            "D6 R1d dispatch refused (outside validity subset): %s" % (_key,))
    if h_slice is not None:
        _rmin, _nbelow = check_I1_row_degree(h_slice, int(prefix_rows))
        if int(_rmin) < int(I1_MIN_CHECK_DEGREE):
            raise ValueError(
                "D6 R1d dispatch refused (live I1): %s min=%d below=%d"
                % (_key, int(_rmin), int(_nbelow)))

def assert_r1d_out_root(out_root, repo_root):
    """Refuse the immutable A2/VOID roots as an R1d output root (by name)."""
    import pathlib as _pl
    try:
        _rp = _pl.Path(out_root).resolve()
    except Exception:  # noqa: BLE001 - unresolvable path refuses closed
        raise ValueError("D6 R1d refusing unresolvable out_root %r" % (out_root,))
    for _rel in R1D_REFUSED_ROOTS:
        _cand = (_pl.Path(repo_root) / _rel).resolve()
        if str(_rp) == str(_cand):
            raise ValueError(
                "D6 R1d refusing historical root %s" % (_cand,))

def enrich_r1d_records(records, mothers):
    """Add schema-v2 I1 fields to copies of the frozen record dicts.

    Slices the in-memory mothers (no rebuild); the shared frozen dicts are
    never mutated, so the old six-file writer output is unchanged.
    """
    import numpy as _np
    out = []
    for _r in (records or []):
        _d = dict(_r)
        try:
            _H = _np.asarray(mothers[(str(_r.get("arm", "")),
                                      str(_r.get("layer", "")))])
            _rmin, _nbelow = check_I1_row_degree(
                _H, int(_r.get("prefix_rows", -1)))
        except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
            raise ValueError("D6 R1d enrich failed for %r: %r"
                             % (str(_r.get("arm", "")), ex))
        _d["row_degree_min"] = int(_rmin)
        _d["rows_below_degree_2"] = int(_nbelow)
        out.append(_d)
    return out

_R1D_STRUCTURE_FIELDS = ["arm", "n", "layer", "prefix_rows", "rank",
    "zero_rows", "zero_columns", "connected_components",
    "largest_component_fraction", "four_cycles",
    "four_cycle_variable_incidence_max", "duplicate_projective_columns",
    "base_pair_duplicates", "support_triple_duplicates", "row_degree_max",
    "row_degree_sumsq", "girth", "girth_reason", "m_cycle_rank",
    "window_overflow", "eligible", "determinism_ok",
    "row_degree_min", "rows_below_degree_2"]
R1D_STRUCTURE_HEADER = ",".join(_R1D_STRUCTURE_FIELDS) + "\n"

def write_structure_records_r1d(path, records):
    """Schema-v2 writer for NEW R1d roots only (historical roots untouched)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(R1D_STRUCTURE_HEADER)
        for r in (records or []):
            fh.write(",".join(str(r.get(k, "")) for k in _R1D_STRUCTURE_FIELDS) + "\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception as ex:  # R1c-A2 fail closed
            raise RuntimeError("fsync-failed structure_records: %r" % (ex,))
