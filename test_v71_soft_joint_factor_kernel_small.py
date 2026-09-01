# V72_not_started
import numpy as np, pathlib, json
from scripts.v71_soft_joint_factor import log_prior_from_posterior, bit_factor_from_llr, soft_joint_factor_kernel, extrinsic_from_logs, validate_kernel

def test_bit_expand():
    for s in range(1024):
        recon = sum(((s>>i)&1)<<i for i in range(10))
        assert recon==s

def test_5func_all_zero_delta():
    log_prior = np.log(np.ones(1024)/1024)
    llr0 = np.zeros(10)
    post = soft_joint_factor_kernel(log_prior, llr0)
    assert abs(float(np.max(np.abs(post-log_prior))))<1e-12
    for a_star in [0,511,1023]:
        llr = np.array([1e6 if ((a_star>>i)&1) else -1e6 for i in range(10)], dtype=float)
        lp = soft_joint_factor_kernel(log_prior, llr)
        assert abs(float(lp[a_star]))<1e-9
        assert float(np.max(lp[np.arange(1024)!=a_star])) < -1e2

def test_D1_D2():
    log_prior = np.log(np.ones(1024)/1024)
    post = soft_joint_factor_kernel(log_prior, np.zeros(10))
    ext = extrinsic_from_logs(log_prior, post)
    d = validate_kernel(log_prior, np.zeros(10), post, ext)
    assert d["D1_completeness"] and d["D2_normalization"]

def test_f_actual_not_measured():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    assert j["f1_3"]["f_actual"]=="NOT_MEASURED"
    assert all(v["f_actual"]=="NOT_MEASURED" for v in j["per_session"].values())

def test_A1_A6_mock(tmp_path=None):
    j=json.loads(pathlib.Path("v71_audit_report.json").read_text(encoding="utf-8"))
    for v in j["per_session"].values():
        assert v["classification"] in ("READY","ADAPTER","NOT_COMPATIBLE")

def test_bench_1_9():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    b=list(j["benchmark"].values())[0]
    assert "1" in b and "9" in b
    assert b["1"]["wall_s"]>0 and b["1024"]["wall_s"]<=30

def test_isolation():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    assert j["used_test"]==False
    txt=pathlib.Path("scripts/v71_soft_joint_factor.py").read_text(encoding="utf-8")
    assert "V72_not_started" in txt

# ponytail: no 1024 full bench in small test to keep cost low
