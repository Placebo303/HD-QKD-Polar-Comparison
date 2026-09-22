import itertools
import numpy as np

def bits_maps(S):
    T = tuple(sorted(set(range(10)) - set(S)))
    mu1 = np.zeros(1024, dtype=np.int32)
    for s in range(1024):
        u1 = 0
        for k,b in enumerate(S):
            if (s>>b)&1: u1|=1<<k
        mu1[s]=u1
    return mu1, T

def test_S_enum():
    L = list(itertools.combinations(range(10),5))
    assert len(L)==252 and L[0]==(0,1,2,3,4) and L[-1]==(5,6,7,8,9)
    assert L.index((5,6,7,8,9))==251

def test_bits_natural():
    S_nat=(5,6,7,8,9)
    mu1,_=bits_maps(S_nat)
    for s in range(1024):
        assert mu1[s]==(s>>5)
        # u2 check quickly
        T=(0,1,2,3,4)
        u2=0
        for k,b in enumerate(T):
            if (s>>b)&1: u2|=1<<k
        assert u2==(s&31)

def test_T_unique():
    # T = (max,sum,abs,S_lex) unique lexicographic
    rows=[(10,20,2,(0,1,2,3,4)),(10,19,3,(0,1,2,3,5)),(9,30,1,(0,1,2,3,6))]
    assert min(rows)==(9,30,1,(0,1,2,3,6))
    # same max,sum,abs lex tie
    a=(10,20,2,(0,1,2,3,4)); b=(10,20,2,(0,1,2,3,5))
    assert a<b

def test_bijection():
    for S in [(0,1,2,3,4),(5,6,7,8,9),(4,5,7,8,9)]:
        T = tuple(sorted(set(range(10))-set(S)))
        seen=set()
        for s in range(1024):
            u1=0
            for k,b in enumerate(S):
                if (s>>b)&1: u1|=1<<k
            u2=0
            for k,b in enumerate(T):
                if (s>>b)&1: u2|=1<<k
            code=(u1,u2)
            assert code not in seen
            seen.add(code)
        assert len(seen)==1024

def test_cal_only_flag():
    import json, pathlib
    j=json.loads(pathlib.Path("v68_results.json").read_text(encoding="utf-8"))
    assert j["used_val_in_selection"]==False
    assert j["used_test"]==False
    assert j["enum"]["count"]==252

if __name__=="__main__":
    test_S_enum(); test_bits_natural(); test_T_unique(); test_bijection(); test_cal_only_flag()
    print("test_v68_spike_small PASS")
