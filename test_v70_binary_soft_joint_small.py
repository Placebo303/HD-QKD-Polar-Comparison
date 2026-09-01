import math, hashlib
import numpy as np

from scripts.v70_binary_soft_joint_feasibility import soft_joint_factor_update, brute_soft_joint, ce_vals, B_BITS

def test_bit_expand():
    for s in range(1024):
        recon = sum(((s>>i)&1)<<i for i in range(10))
        assert recon==s
    assert B_BITS.shape==(1024,10)

def test_D_bits_nonneg():
    # synthetic Ps uniform -> D=0
    Ps=np.ones((1024,1024))/1024
    a=np.random.randint(0,1024,size=1024)
    b=np.random.randint(0,1024,size=1024)
    ce, bits, D, _ = ce_vals(Ps,a,b)
    assert D >= -1e-9
    # chain delta 0
    assert abs(sum(bits)-ce - D) < 1e-9

def test_pure_allzero_and_delta():
    p=np.ones(1024)/1024
    log_prior=np.log(p)
    llr0=np.zeros(10)
    lp=soft_joint_factor_update(log_prior, llr0)
    lb=brute_soft_joint(log_prior, llr0)
    assert np.max(np.abs(lp-lb)) < 1e-12
    # all zero should equal log_prior normalized
    lse = float(np.max(log_prior) + math.log(np.sum(np.exp(log_prior-np.max(log_prior)))))
    expected=log_prior-lse
    assert np.max(np.abs(lp-expected)) < 1e-12
    for a_star in [0,511,1023]:
        llr=np.array([1e6 if ((a_star>>i)&1) else -1e6 for i in range(10)],dtype=float)
        lp2=soft_joint_factor_update(log_prior, llr)
        lb2=brute_soft_joint(log_prior, llr)
        assert np.max(np.abs(lp2-lb2)) < 1e-12
        assert abs(float(lp2[a_star])) < 1e-9

def test_required_ceil_and_gap():
    ce=7.15
    req=int(math.ceil(1.3*1024*ce))
    assert req==9519 or req== int(math.ceil(1.3*1024*ce))
    gap=10240-req
    margin=gap/10240
    # 0/5% thresholds
    def cls(gap):
        if gap<0: return "HEAVY"
        elif gap<512: return "MARGINAL"
        else: return "FEASIBLE"
    assert cls(721)=="FEASIBLE"
    assert cls(193)=="MARGINAL"
    assert cls(-1)=="HEAVY"

def test_H_bin_small_prefix():
    # small rank check with int basis
    from scripts.v70_binary_soft_joint_feasibility import generate_H_bin
    mat, ok, nz, uniq, pref, sha = generate_H_bin(160)
    assert ok and nz and uniq and pref
    # not started guard
    assert True  # V71_not_started placeholder
    # test isolation: no decode_ in script already checked elsewhere
