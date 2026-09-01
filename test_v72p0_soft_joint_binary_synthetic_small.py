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

def test_backend_enum():
    import importlib.util
    spec=importlib.util.spec_from_file_location("a", "scripts/v72p0_backend_audit.py")
    am=importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
    assert am.BackendState.PASS==0
    # ensure no string READY comparison in file
    txt=Path("scripts/v72p0_backend_audit.py").read_text(encoding="utf-8")
    assert '"READY"' not in txt
    assert 'decode_' not in txt

def test_p0a_p0b():
    assert Path("v72p0_results.json").exists()
    j=json.loads(Path("v72p0_results.json").read_text(encoding="utf-8"))
    assert j['P0A']['P0A_PASS']
    assert j['P0B']['P0B_PASS']
    assert j['f_actual']=='NOT_MEASURED'
    assert j['used_2m']==False
    assert j['successor_v72_not_started']==True

def test_registry():
    j=json.loads(Path("v72p0_data_registry_synthetic.json").read_text(encoding="utf-8"))
    assert j['Q']==1024 and j['N']==1024 and j['M']==9036
    assert j['used_2m']==False
    assert j['successor_v72_not_started']==True
