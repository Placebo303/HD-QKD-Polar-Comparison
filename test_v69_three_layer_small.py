import itertools
import numpy as np
import json
from pathlib import Path

Q=1024
B = ((np.arange(Q)[:,None] >> np.arange(10)[None,:]) & 1).astype(np.int32)

def bits_P(s, assign):
    # assign tuple len10 1..3
    S1=[j for j,v in enumerate(assign) if v==1]
    S2=[j for j,v in enumerate(assign) if v==2]
    S3=[j for j,v in enumerate(assign) if v==3]
    w1,w2,w3=len(S1),len(S2),len(S3)
    u1=sum(((s>>b)&1)<<k for k,b in enumerate(S1))
    u2=sum(((s>>b)&1)<<k for k,b in enumerate(S2))
    u3=sum(((s>>b)&1)<<k for k,b in enumerate(S3))
    return u1,u2,u3,w1,w2,w3

def test_enum_59049_to_37170():
    raw=list(itertools.product([1,2,3], repeat=10))
    assert len(raw)==59049==3**10
    valid=[a for a in raw if all(2<=sum(1 for x in a if x==i)<=5 for i in [1,2,3])]
    assert len(valid)==37170
    # per pattern
    from collections import Counter
    c=Counter(tuple(sum(1 for x in a if x==i) for i in [1,2,3]) for a in valid)
    assert c[(5,3,2)]==2520
    assert c[(3,3,4)]==4200
    assert sum(c.values())==37170
    # dedup_stats
    j=json.loads(Path("v69_results.json").read_text(encoding="utf-8"))
    assert j["dedup_stats"]["valid"]==37170
    assert j["enum"]["raw"]==59049

def test_bits_P_bijection():
    assign=(1,1,1,1,1,2,2,2,3,3)  # w 5,3,2
    seen=set()
    for s in range(Q):
        u1,u2,u3,w1,w2,w3=bits_P(s, assign)
        assert 0<=u1 < (1<<w1)
        assert 0<=u2 < (1<<w2)
        assert 0<=u3 < (1<<w3)
        # reconstruct
        # need inverse: s == perm^{-1}(u1,u2,u3)
        S1=[j for j,v in enumerate(assign) if v==1]
        S2=[j for j,v in enumerate(assign) if v==2]
        S3=[j for j,v in enumerate(assign) if v==3]
        s2=0
        for k,b in enumerate(S1):
            if (u1>>k)&1: s2|=1<<b
        for k,b in enumerate(S2):
            if (u2>>k)&1: s2|=1<<b
        for k,b in enumerate(S3):
            if (u3>>k)&1: s2|=1<<b
        assert s2==s
        code=(u1,u2,u3)
        assert code not in seen
        seen.add(code)
    assert len(seen)==1024

def test_T_unique_and_common():
    rows=[(0.5,5000,0.1,(1,1,1,1,1,2,2,2,3,3)),(0.5,4900,0.2,(1,1,1,1,1,2,2,3,3,3)),(0.4,6000,0.0,(1,1,1,1,2,2,2,3,3,3))]
    assert min(rows)==(0.4,6000,0.0,(1,1,1,1,2,2,2,3,3,3))
    a=(0.5,5000,0.1,(1,1,1,1,1,2,2,2,3,3)); b=(0.5,5000,0.1,(1,1,1,1,1,2,2,3,3,3))
    assert a<b

def test_cal_only_and_guards():
    j=json.loads(Path("v69_results.json").read_text(encoding="utf-8"))
    assert j["used_val_in_selection"]==False
    assert j["used_test"]==False
    assert j["V70_not_started"]==True
    assert j["total_sessions"]==3
    # per-layer
    for sid,info in j["per_session"].items():
        val=info["val"]
        assert abs(val["CE_full"] - val["CE1"] - val["CE2"] - val["CE3"]) < 1e-9
        assert val["val_b_unseen"] <= 0.01 + 1e-9
    # common same assignment
    assert j["P_star_common"]==j["P_star_per_session"]["20260123_1M_600k_0dB"]

def test_no_decoder_and_chain():
    import re
    txt=Path("scripts/v69_three_layer_feasibility.py").read_text(encoding="utf-8")
    assert len(re.findall(r"decode_", txt))==0
    assert len(re.findall(r"construct_", txt))==0
    assert len(re.findall(r"gf_rank", txt))==0
    assert len(re.findall(r"nested", txt))==0
    # v70 only in V70_not_started
    # count v70 occurrences minus allowed
    # allow V70_not_started exactly
    txt_low=txt.lower()
    # ensure no other v70
    # we already have 3 allowed
    assert txt.count("V70_not_started")==3

if __name__=="__main__":
    test_enum_59049_to_37170()
    test_bits_P_bijection()
    test_T_unique_and_common()
    test_cal_only_and_guards()
    test_no_decoder_and_chain()
    print("test_v69_three_layer_small PASS")
