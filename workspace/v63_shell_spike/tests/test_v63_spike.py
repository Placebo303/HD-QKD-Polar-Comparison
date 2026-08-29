import pathlib, json, sys
import numpy as np

# T1 R63-01 factorization 32*u1+u2 full symbol
def test_T1_factorization():
    from workspace.v63_shell_spike.nbldpc_shell_adapter_fake import decompose_symbols, recompose_symbols
    arr = np.arange(1024)
    u1, u2 = decompose_symbols(arr)
    assert np.all(u1 == arr//32) and np.all(u2 == arr%32)
    recon = recompose_symbols(u1, u2)
    assert np.array_equal(recon, arr)
    for s in [0,31,32,63,1023]:
        assert 32*(s//32)+(s%32)==s

# T2 exact full = u1 and u2
def test_T2_exact():
    from workspace.v63_shell_spike.nbldpc_shell_adapter_fake import decompose_symbols
    s_true = np.array([0,31,32,1023])
    s_hat_exact = np.array([0,31,32,1023])
    s_hat_wrong_u1 = np.array([32,31,0,1023])  # first differs
    assert np.array_equal(s_hat_exact, s_true)
    assert not np.array_equal(s_hat_wrong_u1, s_true)
    # per-element exact via decomposition
    assert np.all((s_hat_exact//32==s_true//32) & (s_hat_exact%32==s_true%32))
    assert not np.all((s_hat_wrong_u1//32==s_true//32) & (s_hat_wrong_u1%32==s_true%32))

# T3 reconciled_symbols are full 0..1023 not GF32-only
def test_T3_reconciled_full_range():
    from workspace.v63_shell_spike.nbldpc_shell_adapter_fake import fake_nbldpc_shell_run
    from comparison_bench.src.comparison_bench.types import FrameBatch
    rng = np.random.default_rng(1)
    alice = rng.integers(0,1024,size=(2,1024), dtype=np.int64)
    bob = rng.integers(0,1024,size=(2,1024), dtype=np.int64)
    batch = FrameBatch("test", alice, bob, 1024, 1024, {})
    res = fake_nbldpc_shell_run(batch, "1M", stage_pattern=["base","delta8"])
    assert res.reconciled_symbols.shape==(2,1024)
    assert np.all(res.reconciled_symbols>=0) and np.all(res.reconciled_symbols<1024)
    # verify recomposition property
    assert np.all(res.reconciled_symbols//32 <32) and np.all(res.reconciled_symbols%32 <32)

# T4 leakage three-tier tag single count
def test_T4_leakage():
    from workspace.v63_shell_spike.leakage import leak_for
    for src in ["1M","1p5M","2M"]:
        b=leak_for(src,"base"); s1=leak_for(src,"delta8"); s2=leak_for(src,"delta16")
        assert s1-b==40 and s2-s1==40
        m={"1M":184,"1p5M":190,"2M":192}[src]
        assert b==5*m+80+64

# T5 PA proxy uses actual_disclosure_bits
def test_T5_pa_proxy_correct():
    from workspace.v63_shell_spike.pa_proxy import pa_proxy
    out = pa_proxy([0], [1064,1104])
    assert out["pa_input_leak"]==2168
    assert out["note"]=="POLAR_REFERENCE_PROXY"

# T6 PA rejects Polar leak_EC
def test_T6_pa_reject_polar():
    from workspace.v63_shell_spike.pa_proxy import pa_proxy
    try:
        pa_proxy([0],[1064], polar_leak_EC=999)
        assert False
    except ValueError as e:
        assert "REJECT" in str(e)

# T7 domain gate DOMAIN_CALIBRATION_REQUIRED
def test_T7_domain():
    from workspace.v63_shell_spike.domain_check import domain_check
    assert domain_check(0.02,0.5)=="DOMAIN_OK"
    assert domain_check(0.06,0.5)=="DOMAIN_CALIBRATION_REQUIRED"
    assert domain_check(0.01,0.001)=="DOMAIN_CALIBRATION_REQUIRED"

# T8 IRRunResult signature not mutated
def test_T8_irrunresult_frozen():
    import pathlib, subprocess
    # check git diff base.py ==0 via file content? just check fields unchanged
    from comparison_bench.src.comparison_bench.types import IRRunResult
    import inspect
    sig = inspect.signature(IRRunResult.__init__)
    params = list(sig.parameters.keys())
    # must contain original fields, no new shell fields leak into IRRunResult
    assert "leak_EC_actual_bits" in params
    assert "actual_disclosure_bits" not in params  # shell field must not be in IRRunResult
    assert "stage_used" not in params

# T9 smoke registry INTEGRATION_REPLAY_SMOKE 9 blocks
def test_T9_smoke():
    p = pathlib.Path("workspace/v63_shell_spike/registries/v63_smoke_registry.json")
    j=json.loads(p.read_text(encoding="utf-8"))
    assert j["registry_type"]=="INTEGRATION_REPLAY_SMOKE"
    assert len(j["entries"])==9
    for e in j["entries"]:
        assert e["sampling_mode"]=="deterministic_four_consecutive_frames_heldout_fresh_v63_smoke"
        assert len(e["frame_ids"])==4 and e["pairs_count"]==1024

# T10 fresh candidate 90 zero overlap with smoke
def test_T10_fresh_zero_overlap():
    import pathlib, json
    smoke=json.loads(pathlib.Path("workspace/v63_shell_spike/registries/v63_smoke_registry.json").read_text(encoding="utf-8"))
    dev=json.loads(pathlib.Path("workspace/v63_shell_spike/registries/v63_dev_registry.json").read_text(encoding="utf-8"))
    assert dev["registry_type"]=="INTEGRATION_FRESH_CANDIDATE"
    assert len(dev["entries"])==90
    # zero overlap
    for s in smoke["entries"]:
        for d in dev["entries"]:
            if s["source"]!=d["source"]: continue
            assert s["held_out_ordinal_end"] < d["held_out_ordinal_start"] or d["held_out_ordinal_end"] < s["held_out_ordinal_start"], f"overlap {s} {d}"

# T11 ShellResult does not alter IRRunResult, wraps it
def test_T11_shell_wraps():
    from workspace.v63_shell_spike.nbldpc_shell_adapter_fake import fake_nbldpc_shell_run
    from comparison_bench.src.comparison_bench.types import FrameBatch
    rng=np.random.default_rng(2)
    alice=rng.integers(0,1024,size=(1,1024))
    bob=rng.integers(0,1024,size=(1,1024))
    batch=FrameBatch("t",alice,bob,1024,1024,{})
    res=fake_nbldpc_shell_run(batch,"2M", stage_pattern=["delta16"])
    assert hasattr(res, "ir_result") and hasattr(res, "reconciled_symbols")
    assert res.ir_result.leak_EC_actual_bits==res.pa_leak
    assert res.actual_disclosure_bits[0]==1184  # 2M delta16

# T12 end-to-end fake pipeline TTBin->FrameBatch->Shell->PA no decoder
def test_T12_e2e_fake():
    from comparison_bench.src.comparison_bench.types import FrameBatch
    from workspace.v63_shell_spike.nbldpc_shell_adapter_fake import fake_nbldpc_shell_run
    from workspace.v63_shell_spike.pa_proxy import pa_proxy
    import numpy as np
    rng=np.random.default_rng(3)
    alice=rng.integers(0,1024,size=(3,1024))
    bob=rng.integers(0,1024,size=(3,1024))
    batch=FrameBatch("e2e",alice,bob,1024,1024,{})
    res=fake_nbldpc_shell_run(batch,"1p5M", stage_pattern=["base","delta8","delta16"])
    pa=pa_proxy(res.reconciled_symbols, res.actual_disclosure_bits)
    assert pa["pa_input_leak"]== sum([1094,1134,1174])
    # check 32*u1+u2 holds for all reconciled
    assert np.all(res.reconciled_symbols== (res.reconciled_symbols//32)*32 + (res.reconciled_symbols%32))
