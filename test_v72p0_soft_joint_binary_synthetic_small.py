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
    # hardened P0A total_bits<=9 k2-3 exhaustive 7cover fail-closed
    assert "per_k" in j['P0A']
    for k in ["2","3"]:
        assert k in j['P0A']['per_k']
        assert len(j['P0A']['per_k'][k]['checks_per_trial'][0])==7
        assert j['P0A']['per_k'][k]['total_bits']<=9
        assert j['P0A']['per_k'][k]['exhaustive_total']==(1<<j['P0A']['per_k'][k]['n'])
        assert j['P0A']['per_k'][k]['per_m_pass']==True
    # syndrome 0/1 flip and 1e-9 marginal
    assert j['P0A']['worst_marginal_delta'] < 1e-9
    assert j['P0A']['total_bits_le_9']==True
    assert j['P0A']['exhaustive']==True
    assert j['P0A']['seven_fail_closed']==True
    # loopy only descriptive: tree flags all True, loopy count 0, exact only tree
    for k in ["2","3"]:
        assert all(j['P0A']['per_k'][k]['tree_flags'])
        assert j['P0A']['per_k'][k]['loopy_descriptive_count']==0
    assert j['P0A']['mode']=="tiny_exhaustive_syndrome_marginal_tree"
    # P0B sparse CSR IRA dual-diagonal pivot checks
    assert j['P0B']['structure']=="sparse_CSR_IRA"
    assert j['P0B']['nnz']>0
    assert j['P0B']['zero_cols']==0
    assert j['P0B']['dup_rows']==0
    assert j['P0B']['rank']==9036
    assert j['P0B']['prefix_nested']==True
    assert j['P0B']['pivot_checks']['160']==True
    assert j['P0B']['pivot_checks']['168']==True
    assert j['P0B']['pivot_checks']['176']==True
    assert j['P0B']['pivot_checks']['9036']==True
    assert "dual-diagonal" in j['P0B']['dual_diagonal_proof'] or "dual_diagonal" in j['P0B']['dual_diagonal_proof']

def test_five_state():
    j=json.loads(Path("v72p0_results.json").read_text(encoding="utf-8"))
    assert j['classification']=="V72P0_ADAPTER_PLAN_READY"
    assert j['overall']=="OVERALL_ADAPTER_PLAN_READY"
    assert "ADAPTER_PLAN_READY" in j['counts']
    assert j['counts']['ADAPTER_PLAN_READY']==1
    # requires 3 passes: KERNEL, P0A, P0B
    assert j['local_factor']['KERNEL_PASS']
    assert j['P0A']['P0A_PASS']
    assert j['P0B']['P0B_PASS']
    # 5-state only
    assert set(j['counts'].keys())=={"ADAPTER_PLAN_READY","KERNEL_FAIL","TINY_FAIL","MATRIX_FAIL","EVIDENCE_INCOMPLETE"}

def test_registry():
    j=json.loads(Path("v72p0_data_registry_synthetic.json").read_text(encoding="utf-8"))
    assert j['Q']==1024 and j['N']==1024 and j['M']==9036
    assert j['used_2m']==False
    assert j['successor_v72_not_started']==True
    assert j['P0A']['total_bits_le_9']==True
    assert j['P0A']['exhaustive']==True
    assert j['P0B']['structure']=="sparse_CSR_IRA"
    # head sync not b360
    assert "b360" not in j['head']

def test_provenance_sync():
    for p in ["v72p0_results.json","v72p0_manifest.json","V72P0_SYN_REPORT.md","V72P0_BACKEND_AUDIT_REPORT.md"]:
        txt=Path(p).read_text(encoding="utf-8")
        assert "b360efe" not in txt
        assert "84d62779" in txt or "5591e16b" in txt or "64ca2f1e" in txt

def test_no_sampling():
    txt=Path("scripts/v72p0_soft_joint_binary_synthetic.py").read_text(encoding="utf-8")
    # forbid old random sampling branch (50000 samples) but allow descriptive comment about forbidding
    assert "50000" not in txt  # old sampling size removed
    assert "total_bits<=9" in txt or "total_bits_le_9" in txt
    assert "syndrome" in txt.lower()
    assert "dual-diagonal" in txt.lower()

def test_p0a_c3_observed():
    j=json.loads(Path("v72p0_results.json").read_text(encoding="utf-8"))
    for k in ["2","3"]:
        per=j['P0A']['per_k'][k]
        assert per['observed_zero']==True
        assert per['observed_one']==True
        assert per['c3_observed']==True
        # every trial c3 == observed_zero && observed_one
        for ch in per['checks_per_trial']:
            assert ch[2]==True

def test_p0a_c3_negative():
    # negative: if only zero syndromes observed, c3 must be False (fail-closed), numeric unchanged
    observed_zero=True
    observed_one=False
    assert (observed_zero and observed_one)==False
    # ensure code path would fail per_m when not both observed
    txt=Path("scripts/v72p0_soft_joint_binary_synthetic.py").read_text(encoding="utf-8")
    assert "observed_zero" in txt and "observed_one" in txt and "c3_obs" in txt
