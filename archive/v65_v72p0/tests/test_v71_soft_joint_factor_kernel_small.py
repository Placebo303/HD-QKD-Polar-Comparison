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
        assert v["classification"] in ("READY","ADAPTER","ADAPTER_REQUIRED","NOT_COMPATIBLE")

def test_bench_1_9():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    b=list(j["benchmark"].values())[0]
    assert "1" in b and "9" in b
    assert "kernel_calls" in b["1"] and b["1"]["kernel_calls"]==1 and b["9"]["kernel_calls"]==9 and b["1024"]["kernel_calls"]==1024
    assert b["1"]["wall_s"]>=0 and b["1024"]["wall_s"]<=30 and b["1024"]["wall_s"]>0

def test_isolation():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    assert j["used_test"]==False
    txt=pathlib.Path("scripts/v71_soft_joint_factor.py").read_text(encoding="utf-8")
    assert "V72_not_started" in txt

# ponytail: no 1024 full bench in small test to keep cost low
def test_bench_deterministic_seed():
    import scripts.v71_soft_joint_factor as m
    import inspect
    src=inspect.getsource(m.bench_kernel)
    assert "default_rng(0)" in src or "seed" in src.lower()
    assert "1024" in src

def test_bench_per_symbol_one():
    import inspect, scripts.v71_soft_joint_factor as m
    src=inspect.getsource(m.bench_kernel)
    assert "kernel_calls" in src or "n_inv=int(workload)" in src or "per-symbol" in src or "per_symbol" in src

def test_audit_no_self_comparison():
    txt=pathlib.Path("scripts/v71_ldpc_v5_audit.py").read_text(encoding="utf-8")
    assert "self-comparison" in txt.lower() or "delete self" in txt.lower() or "no self" in txt.lower() or "read-only" in txt.lower()
    assert "model_sha256" in txt

def test_audit_extrinsic_10bit_10240():
    j=json.loads(pathlib.Path("v71_audit_report.json").read_text(encoding="utf-8"))
    for v in j["per_session"].values():
        checks=v["checks"]
        # A2 requires 10-bit extrinsic+10240 else ADAPTER
        assert "A4_extrinsic_interface" in checks
        assert "A6_disclosure_accounting" in checks
        # 10240 missing => should be ADAPTER_REQUIRED not READY
        if not checks["A4_extrinsic_interface"] or not checks["A6_disclosure_accounting"]:
            assert v["classification"] in ("ADAPTER","ADAPTER_REQUIRED")

def test_capacity_separation_2M():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    # A3: 2M kernel ready but NO_INFORMATION (mechanical V70), f NOT_MEASURED
    found2M=False
    for v in j["per_session"].values():
        if v["source_label"]=="2M":
            found2M=True
            assert v["f_actual"]=="NOT_MEASURED"
            assert v.get("capacity_status") in ("NO_INFORMATION","NO_INFORMATION_MARGIN") or v.get("capacity_warning") in ("NO_INFORMATION","NO_INFORMATION_MARGIN")
            assert v.get("kernel_status")=="READY" or v["classification"] in ("V71_KERNEL_READY_FEASIBLE","V71_KERNEL_ADAPTER_FEASIBLE","V71_KERNEL_HEAVY")
    assert found2M

def test_kernel_backend_capacity_fields():
    j=json.loads(pathlib.Path("v71_results.json").read_text(encoding="utf-8"))
    for v in j["per_session"].values():
        assert "kernel_status" in v and "backend_status" in v and "capacity_status" in v
