import json, hashlib, math
from pathlib import Path
import numpy as np

def test_bit_expand():
    for s in range(1024):
        r=0
        for i in range(10): r|=((s>>i)&1)<<i
        assert r==s

def test_local_factor_small():
    import importlib.util, pathlib
    spec=importlib.util.spec_from_file_location("m", "scripts/v72p0_soft_joint_binary_synthetic.py")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    log_prior=np.log(np.ones(1024)/1024)
    for llr in [np.zeros(10), np.random.default_rng(1).standard_normal(10)]:
        v=m.validate_local_factor(log_prior, llr)
        assert v['T_LF01_completeness']
        assert v['T_LF02_normalization']
        assert v['T_LF03_marginal']
        assert v['T_LF05_self_exclusion']
        assert v['T_LF08_brute']

def test_self_exclusion_1e12():
    import importlib.util
    spec=importlib.util.spec_from_file_location("m2", "scripts/v72p0_soft_joint_binary_synthetic.py")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    log_prior=np.log(np.ones(1024)/1024)
    llr=np.array([0.5,-0.3,0.7,-0.9,1.1,-0.2,0.4,-0.6,0.8,-0.1])
    v=m.validate_local_factor(log_prior, llr)
    assert v['T_LF05_maxDelta']<1e-12
    assert v['T_LF08_maxDelta']<1e-12

def test_kernel_pass_preserved():
    j=json.loads(Path("v72p0_results.json").read_text(encoding="utf-8"))
    assert j['local_factor']['KERNEL_PASS']==True
    assert j['local_factor']['T_LF01'] and j['local_factor']['T_LF08']

def test_backend_enum():
    import importlib.util
    spec=importlib.util.spec_from_file_location("a", "scripts/v72p0_backend_audit.py")
    am=importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
    assert am.BackendState.PASS==0
    txt=Path("scripts/v72p0_backend_audit.py").read_text(encoding="utf-8")
    assert '"READY"' not in txt
    assert 'decode_' not in txt
    txt2=Path("scripts/v72p0_soft_joint_binary_synthetic.py").read_text(encoding="utf-8")
    assert '"READY"' not in txt2
    assert 'decode_' not in txt2

def test_p0a_p0b():
    assert Path("v72p0_results.json").exists()
    j=json.loads(Path("v72p0_results.json").read_text(encoding="utf-8"))
    assert j['P0A']['P0A_PASS']
    assert j['P0B']['P0B_PASS']
    assert j['f_actual']=='NOT_MEASURED'
    assert j['used_2m']==False
    assert j['successor_v72_not_started']==True
    # new P0A k=2/3 7cover
    assert "per_k" in j['P0A']
    for k in ["2","3"]:
        assert k in j['P0A']['per_k']
        assert len(j['P0A']['per_k'][k]['seven'])==7
    # no true bits self compare: ensure P0A mode is BP vs brute
    assert j['P0A']['mode']=="tiny_bp_vs_brute_k2_3_7cover"
    # P0B sparse
    assert j['P0B']['structure']=="sparse_CSR_IRA"
    assert j['P0B']['nnz']>0
    assert j['P0B']['zero_cols']==0
    assert j['P0B']['dup_rows']==0
    assert j['P0B']['rank']==9036
    assert j['P0B']['prefix_nested']==True

def test_five_state():
    j=json.loads(Path("v72p0_results.json").read_text(encoding="utf-8"))
    assert j['classification']=="V72P0_ADAPTER_PLAN_READY"
    assert j['overall']=="OVERALL_ADAPTER_PLAN_READY"
    assert "ADAPTER_PLAN_READY" in j['counts']
    assert j['counts']['ADAPTER_PLAN_READY']==1
    # requires 3 passes
    assert j['local_factor']['KERNEL_PASS']
    assert j['P0A']['P0A_PASS']
    assert j['P0B']['P0B_PASS']

def test_registry():
    j=json.loads(Path("v72p0_data_registry_synthetic.json").read_text(encoding="utf-8"))
    assert j['Q']==1024 and j['N']==1024 and j['M']==9036
    assert j['used_2m']==False
    assert j['successor_v72_not_started']==True
    assert j['head']=="b360efe9828484c1022c90c5a14819ebbb9dadcb"
    assert j['P0A']['N_small']==[2,3]
    assert j['P0B']['structure']=="sparse_CSR_IRA"

def test_provenance_sync():
    h="b360efe9828484c1022c90c5a14819ebbb9dadcb"
    for p in ["v72p0_results.json","v72p0_manifest.json","V72P0_SYN_REPORT.md","V72P0_BACKEND_AUDIT_REPORT.md"]:
        txt=Path(p).read_text(encoding="utf-8")
        assert h in txt
        assert "8dfd7c91" not in txt
