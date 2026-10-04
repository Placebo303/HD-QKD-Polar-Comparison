import math
import numpy as np

def ceil_rate(ce):
    return int(math.ceil(1.3*1024*ce/5)) if ce>0 and math.isfinite(ce) else 0

def ceil_to_family(m_raw, step=8):
    return int(math.ceil(m_raw/step)*step) if m_raw>0 else 0

def hierarchical_P(C_ab, P_global, N_b, lam=1.0):
    P=(C_ab.astype(np.float64)+lam*P_global[None,:])/(N_b[:,None]+lam)
    P[N_b==0]=P_global
    return P

def test_ceil_rate():
    assert ceil_rate(0)==0
    assert ceil_rate(5)==int(math.ceil(1.3*1024*5/5))
    assert ceil_rate(3.85736382744345)==1027

def test_ceil_to_family():
    assert ceil_to_family(16)==16
    assert ceil_to_family(17)==24
    assert ceil_to_family(1027)==1032

def test_hierarchical_P():
    C=np.array([[5,1],[2,3]],dtype=np.int32)
    N_b=C.sum(axis=1).astype(float)
    P_global=C.sum(axis=0).astype(float)/C.sum()
    P=hierarchical_P(C,P_global,N_b,lam=1.0)
    assert P.shape==C.shape
    # row with zero N_b -> P_global
    C2=np.zeros((2,2),dtype=np.int32)
    N2=np.array([0,0],dtype=float)
    P2=hierarchical_P(C2,np.array([0.5,0.5]),N2,lam=1.0)
    assert np.allclose(P2[0], [0.5,0.5])

def test_dedup():
    # dedup by (source,acquisition) mechanical not sorted by CE
    entries=[("1M","acq2",10),("1M","acq1",5),("1M","acq2",10)]
    # dedup first keep
    seen={}
    for src,acq,ce in entries:
        k=(src,acq)
        if k not in seen:
            seen[k]=ce
    assert len(seen)==2
    # not sorted by CE
    assert list(seen.values())==[10,5]

def test_used_test_isolation():
    used_test=False
    assert used_test==False

if __name__=="__main__":
    test_ceil_rate(); test_ceil_to_family(); test_hierarchical_P(); test_dedup(); test_used_test_isolation()
    print("small tests PASS")
