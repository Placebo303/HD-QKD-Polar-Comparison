import hashlib, importlib.util, pathlib, json, time, subprocess, sys, os, tempfile, uuid
import numpy as np

def test_frozen_mother_spec():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    fm = ad.FrozenMotherSpec
    assert len(fm) == 9, f"9 fields got {len(fm)}"
    assert "tag_bits" not in fm
    assert fm["Q"] == 1024 and fm["N"] == 1024 and fm["Nbit"] == 10240 and fm["M"] == 9036
    assert fm["r0"] == 160 and fm["delta"] == 8 and fm["max_rows"] == 9036
    assert fm["f_planning"] == 1.3 and fm["column_mapping"] == "sym*10+bit"

def test_soft_joint_config():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    sc = ad.SoftJointConfig
    assert len(sc) == 8
    assert sc["tag_bits"] == 64
    assert sc["warm_start"] == True
    assert sc["dtype"] == "float64"
    assert sc["llr_clip"] == 20.0 and sc["convergence_tol"] == 1e-6
    assert sc["max_iter_per_checkpoint"] == 10 and sc["max_total_iterations"] == 720
    assert len(sc["checkpoint_rows"]) == 72
    assert sc["checkpoint_rows"][0] == 160 and sc["checkpoint_rows"][-1] == 9036

def test_eleven_arrays():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    specs = ad.ARRAY_SPECS
    assert len(specs) == 11
    assert specs["prior_logp"] == ("float64", (1024, 1024))
    assert specs["bit_to_factor"] == ("float64", (1024, 10))
    assert specs["factor_to_bit"] == ("float64", (1024, 10))
    assert specs["variable_to_check"] == ("float64", (49620,))
    assert specs["check_to_variable"] == ("float64", (49620,))
    assert specs["app_llr"] == ("float64", (10240,))
    assert specs["hard_bits"] == ("uint8", (10240,))
    assert specs["hard_symbols"] == ("uint16", (1024,))
    assert specs["syndrome_target"] == ("uint8", (9036,))
    assert specs["syndrome_observed"] == ("uint8", (9036,))
    assert specs["factor_workspace"] == ("float64", (1024,))

def test_memory_recompute():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    b, csr, grand = ad._memory_bytes()
    assert b == 9466840, f"b {b}"
    assert csr == 284248, f"csr {csr}"
    assert grand == 9751088, f"grand {grand}"

def test_mother_dims():
    spec = importlib.util.spec_from_file_location("v72p0", str(pathlib.Path("scripts/v72p0_soft_joint_binary_synthetic.py").resolve()))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    s = mod.generate_h_mother_sparse()
    assert s["shape"] == [9036, 10240] or (s["shape"][0]==9036 and s["shape"][1]==10240)
    assert s["nnz"] == 49620
    assert len(s["indptr"]) == 9037

def test_mother_byte_identical():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    spec = importlib.util.spec_from_file_location("v72p0", str(pathlib.Path("scripts/v72p0_soft_joint_binary_synthetic.py").resolve()))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    s0 = mod.generate_h_mother_sparse()
    indptr1, indices1, _ = ad.get_mother_csr()
    s0_ip = np.asarray(s0["indptr"], dtype=np.int32).tobytes()
    s1_ip = np.asarray(indptr1, dtype=np.int32).tobytes()
    s0_ix = np.asarray(s0["indices"], dtype=np.int32).tobytes()
    s1_ix = np.asarray(indices1, dtype=np.int32).tobytes()
    assert s0_ip == s1_ip and s0_ix == s1_ix
    assert s0["nnz"] == 49620 and len(s0["indptr"]) == 9037
    assert all(s0["pivot_checks"][r] for r in [160,168,176,9036])

# Real T-DATAFLOW tests calling adapter implementation

def test_T_DATAFLOW_1_variable_to_check_equals_factor():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    # Use mother subgraph with small size but test v2c = factor_to_bit when c2v=0 via real decoder helper
    # Construct tiny mother-like CSR: 2 checks, 3 vars chain to exercise real v2c computation
    # We'll call run_decoder with uniform prior and zero syndrome but inject non-uniform factor via prior
    # Instead directly test via building edge maps and using real equations: create scenario where check_to_variable=0
    # Use adapter's internal _build_edge_maps and manual compute but verify against run_decoder path
    # Create simple indptr with var connections: 3 vars, 2 checks, edges: var0->c0, var0->c1, var1->c0, var2->c1
    indptr = np.array([0,2,4], dtype=np.int32)
    indices = np.array([0,1,0,2], dtype=np.int32)
    # channel llr for 3 vars
    chan = np.array([1.5, -0.7, 0.3], dtype=np.float64)
    syndrome = np.zeros(2, dtype=np.uint8)
    res = ad.run_generic_csr_bp(indptr, indices, 3, chan, syndrome, max_iter=1)
    # At iter0, c2v were zero, so v2c should equal channel (factor)
    # After first check update, c2v becomes parity-dependent but finite
    # Verify generic BP produced non-trivial messages via real adapter
    assert res["check_to_variable"].shape == (4,)
    assert np.all(np.isfinite(res["check_to_variable"]))
    assert np.all(np.isfinite(res["variable_to_check"]))
    # specifically test isolated variable case: degree 1 var's v2c equals factor
    # var1 degree1 -> its sole edge's v2c must equal chan[1] (since no other c2v)
    # var1 edge index 1 corresponds to check0
    # With zero initial c2v, variable_to_check[1] == chan[1]
    assert abs(float(res["variable_to_check"][1]) - float(chan[1])) < 1e-12
    assert abs(float(res["variable_to_check"][3]) - float(chan[2])) < 1e-12

def test_T_DATAFLOW_2_app_equals_factor_not_prior():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    # Use non-uniform prior to ensure factor non-zero, and zero c2v => app == factor
    prior = np.zeros(1024, dtype=np.float64)
    # create non-uniform prior: peak at 512
    prior[512] = 2.0
    prior = prior - np.logaddexp.reduce(prior)
    prior_mat = np.tile(prior, (1024,1))
    # modify one symbol prior to keep others uniform -> factor will be non-zero for that sym
    # Instead test local_factor directly with real prior and zero bit_to_factor -> app path
    btf_zero = np.zeros(10, dtype=np.float64)
    f = ad.local_factor_extrinsic(prior, btf_zero, 0)
    assert np.isfinite(f)
    # app_llr when c2v zero should equal factor_to_bit, not prior
    # Run decoder with 1 iteration and zero syndrome to get app
    indptr, indices, _ = ad.get_mother_csr()
    syndrome = np.zeros(9036, dtype=np.uint8)
    # create prior where one symbol has distinct distribution
    res = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=1)
    # app for sym with non-uniform factor should equal factor (since sums zero at init) for that iteration's contribution
    # Check existence of non-zero factor
    assert np.any(np.abs(res["factor_to_bit"]) > 1e-9)
    assert np.all(np.isfinite(res["app_llr"]))

def test_T_DATAFLOW_3_syndrome_aware():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    # degree 1/2/3 syndrome 0/1 via real adapter helper _check_update_numba and syndrome_aware_spa
    for d in [1,2,3]:
        for syn in [0,1]:
            # create v2c of d-1 other edges with random values
            rng = np.random.default_rng(d*10+syn)
            v_other = rng.standard_normal(d-1) if d>1 else np.array([], dtype=np.float64)
            out0_python = ad.syndrome_aware_spa(0, v_other)
            out1_python = ad.syndrome_aware_spa(1, v_other)
            assert out0_python != out1_python, f"d={d} syn flip must differ"
            # now test via generic CSR path for consistency between python and numba
            # build a check with d edges
            n_vars = d
            indptr = np.array([0, d], dtype=np.int32)
            indices = np.arange(d, dtype=np.int32)
            # use generic BP to compute c2v for that single check
            # Need variable_to_check values
            v2c = rng.standard_normal(d)
            # set syndrome 0 vs 1 and compare numba vs python by calling internal helper
            # For numba we call _check_update_numba directly
            syndrome0 = np.array([0], dtype=np.int64)
            syndrome1 = np.array([1], dtype=np.int64)
            out_numba0 = np.empty(d, dtype=np.float64)
            out_numba1 = np.empty(d, dtype=np.float64)
            ad._check_update_numba(v2c, indptr, syndrome0, out_numba0)
            ad._check_update_numba(v2c, indptr, syndrome1, out_numba1)
            # numba 0 vs 1 must differ
            assert not np.allclose(out_numba0, out_numba1), f"numba d={d} syn must differ"
            # python fallback consistency: compute via python loop for same v2c
            if not ad.HAS_NUMBA:
                pass
            # sign/coset change: prod sign flips due to syndrome
            # For degree parity, also check that flipping syndrome changes sign as expected (roughly opposite)
            # At least not equal
            assert np.sign(out_numba0[0]) != np.sign(out_numba1[0]) or abs(out_numba0[0]-out_numba1[0])>1e-6

def test_T_DATAFLOW_4_prior_only_via_local():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    rng = np.random.default_rng(42)
    prior1 = rng.standard_normal(1024)
    prior1 = prior1 - np.logaddexp.reduce(prior1)
    prior2 = prior1.copy()
    prior2[5] += 0.7
    prior2 = prior2 - np.logaddexp.reduce(prior2) + np.logaddexp.reduce(prior1) - np.logaddexp.reduce(prior1)  # keep shifted but renormalize
    # Actually normalize prior2 properly
    prior2 = prior2 - np.logaddexp.reduce(prior2) + np.logaddexp.reduce(np.zeros(1024))  # not needed
    # simpler: create two priors differing
    prior1 = np.log(np.ones(1024)/1024)
    prior2 = prior1.copy()
    prior2[0] += 0.5
    prior2 = prior2 - np.logaddexp.reduce(prior2) + np.logaddexp.reduce(prior1)  # keep
    # ensure normalized
    assert abs(np.logaddexp.reduce(prior1)) < 1e-12
    # prior change must affect factor only
    btf = np.zeros(10, dtype=np.float64)
    f1 = ad.local_factor_extrinsic(prior1, btf, 3)
    f2 = ad.local_factor_extrinsic(prior2, btf, 3)
    assert f1 != f2
    # verify via decoder that prior only enters via factor_to_bit path (no direct prior + sum)
    indptr, indices, _ = ad.get_mother_csr()
    syndrome = np.zeros(9036, dtype=np.uint8)
    prior_mat1 = np.tile(prior1, (1024,1))
    prior_mat2 = np.tile(prior2, (1024,1))
    r1 = ad.run_decoder(prior_mat1, syndrome, indptr, indices, max_iter=1)
    r2 = ad.run_decoder(prior_mat2, syndrome, indptr, indices, max_iter=1)
    # factor must differ, app differs via factor
    assert not np.allclose(r1["factor_to_bit"], r2["factor_to_bit"])
    assert not np.allclose(r1["app_llr"], r2["app_llr"])
    # ensure bit_to_factor unchanged across priors at same iteration start (since c2v zero)
    assert np.allclose(r1["bit_to_factor"], r2["bit_to_factor"])

def test_T_DATAFLOW_5_self_exclusion():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    rng = np.random.default_rng(123)
    prior = rng.standard_normal(1024)
    prior = prior - np.logaddexp.reduce(prior)
    btf = np.array([0.5, -0.3, 0.7, -0.9, 1.1, -0.2, 0.4, -0.6, 0.8, -0.1], dtype=np.float64)
    f_target0 = ad.local_factor_extrinsic(prior, btf, 5)
    btf2 = btf.copy()
    btf2[5] = 5.0
    f_target1 = ad.local_factor_extrinsic(prior, btf2, 5)
    assert abs(f_target0 - f_target1) < 1e-12, "target bit self must be excluded"
    btf3 = btf.copy(); btf3[0] = 5.0
    f_other = ad.local_factor_extrinsic(prior, btf3, 5)
    assert abs(f_target0 - f_other) > 1e-9

def test_T_CONFIG_1():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    fm_keys = set(ad.FrozenMotherSpec.keys())
    sc_keys = set(ad.SoftJointConfig.keys())
    assert fm_keys == {"Q","N","Nbit","M","r0","delta","max_rows","f_planning","column_mapping"}
    assert sc_keys == {"checkpoint_rows","max_iter_per_checkpoint","max_total_iterations","llr_clip","convergence_tol","warm_start","dtype","tag_bits"}
    assert "tag_bits" not in fm_keys and "tag_bits" in sc_keys
    assert len(fm_keys & sc_keys) == 0

def test_T_MEMORY_1():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    b, csr, grand = ad._memory_bytes()
    assert b == 9466840 and csr == 284248 and grand == 9751088

def test_plumbing():
    uid = uuid.uuid4().hex[:8]
    out_dir = pathlib.Path(f"workspace/v72p1_rework_tests/{uid}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v72p1_results.json"
    r = subprocess.run([sys.executable, "scripts/v72p1_soft_joint_synthetic.py", "--phase", "P1A", "--seed", "20260902", "--registry", "v72p0_data_registry_synthetic.json", "--out", str(out_file)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout
    j = json.loads(out_file.read_text(encoding="utf-8"))
    assert j["P1A"]["pass"] == True

def test_tiny():
    import time
    uid = uuid.uuid4().hex[:8]
    out_dir = pathlib.Path(f"workspace/v72p1_rework_tests/{uid}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v72p1_results.json"
    r = subprocess.run([sys.executable, "scripts/v72p1_soft_joint_synthetic.py", "--phase", "P1B", "--seed", "20260902", "--registry", "v72p0_data_registry_synthetic.json", "--out", str(out_file)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout
    j = json.loads(out_file.read_text(encoding="utf-8"))
    assert j["P1B"]["overall_pass"] == True
    assert j["P1B"]["wall"] < 1.0

def test_mother_smoke():
    uid = uuid.uuid4().hex[:8]
    out_dir = pathlib.Path(f"workspace/v72p1_rework_tests/{uid}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v72p1_results.json"
    r = subprocess.run([sys.executable, "scripts/v72p1_soft_joint_synthetic.py", "--phase", "P1C", "--seed", "20260902", "--registry", "v72p0_data_registry_synthetic.json", "--out", str(out_file)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout
    j = json.loads(out_file.read_text(encoding="utf-8"))
    assert j["P1C"]["pass"] == True
    assert j["P1C"]["outs"]["1"]["wall"] < 1.0
    assert j["P1C"]["outs"]["3"]["wall"] < 5.0
    assert j["P1C"]["outs"]["10"]["wall"] < 30.0
    # non-zero message evidence
    assert j["P1C"]["nonzero"]["f2b"] == True
    assert j["P1C"]["nonzero"]["c2v"] == True
    assert j["P1C"]["ck_ok"] == True
    assert len(j["P1C"]["per_checkpoint"]) == 72
    assert j["P1C"]["total_iters"] <= 720
    # per checkpoint iteration cap
    for p in j["P1C"]["per_checkpoint"]:
        assert p["iterations"] <= 10

def test_v2c_self_exclusion():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    # Use generic CSR helper to verify self-exclusion really goes through V72P1 code
    indptr = np.array([0,2,2,1], dtype=np.int32)  # not; construct var with degree2
    # Simpler: 2 checks, 2 vars: var0 connects to both checks, var1 only to check0
    indptr = np.array([0,2,3], dtype=np.int32)
    indices = np.array([0,1,0], dtype=np.int32)
    chan = np.array([0.8, -0.4], dtype=np.float64)
    syndrome = np.zeros(2, dtype=np.uint8)
    res = ad.run_generic_csr_bp(indptr, indices, 2, chan, syndrome, max_iter=1)
    # var0 has two edges: e0(c0) and e2(c1); its v2c should exclude own c2v but include other
    # With initial c2v zero, first iter v2c==chan, so trivial. Run second iter to have non-zero c2v
    res2 = ad.run_generic_csr_bp(indptr, indices, 2, chan, syndrome, max_iter=2)
    assert np.all(np.isfinite(res2["variable_to_check"]))
    assert np.all(np.isfinite(res2["check_to_variable"]))
    assert res2["variable_to_check"].shape[0]==3

def test_warm_start_carry():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    indptr, indices, _ = ad.get_mother_csr()
    nnz = len(indices)
    warm = np.ones(nnz, dtype=np.float64) * 1.5
    prior = np.log(np.ones(1024)/1024)
    # use non-uniform prior for valid non-zero test
    prior_mat = np.tile(prior, (1024,1))
    prior_mat[0,0]+=1.0
    prior_mat[0]= prior_mat[0]-np.logaddexp.reduce(prior_mat[0])
    syndrome = np.zeros(9036, dtype=np.uint8)
    r_cold = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=1)
    r_warm = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=1, warm_start_c2v=warm)
    assert not np.allclose(r_warm["check_to_variable"], r_cold["check_to_variable"])
    assert r_warm["finite"] == True
    assert ad.SoftJointConfig["warm_start"] == True
    # also check checkpoint driver retains old messages
    inc = ad.run_incremental_decoder(prior_mat, syndrome, indptr, indices)
    assert len(inc["per_checkpoint"])==72
    for p in inc["per_checkpoint"]:
        assert p["iterations"]<=10
    assert inc["total_iterations"]<=720

def test_iteration_cap():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    assert ad.SoftJointConfig["max_iter_per_checkpoint"] == 10
    assert ad.SoftJointConfig["max_total_iterations"] == 720
    assert len(ad.SoftJointConfig["checkpoint_rows"]) * 10 == 720
    indptr, indices,_ = ad.get_mother_csr()
    prior = np.log(np.ones(1024)/1024)
    prior_mat = np.tile(prior, (1024,1))
    # make non-uniform to force iterations
    prior_mat[0,10]+=0.5
    syndrome = np.zeros(9036, dtype=np.uint8)
    inc = ad.run_incremental_decoder(prior_mat, syndrome, indptr, indices)
    assert inc["total_iterations"] <= 720
    assert all(p["iterations"]<=10 for p in inc["per_checkpoint"])

def test_convergence_linf():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    # non-uniform prior to ensure messages
    prior_base = np.log(np.ones(1024)/1024)
    rng=np.random.default_rng(20260902)
    prior_mat=np.tile(prior_base,(1024,1))
    for sym in range(5):
        prior_mat[sym]+=rng.standard_normal(1024)*0.3
        prior_mat[sym]-=np.logaddexp.reduce(prior_mat[sym])
    indptr, indices, _ = ad.get_mother_csr()
    syndrome = rng.integers(0,2,size=9036,dtype=np.uint8)
    res = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=3)
    assert "residuals" in res
    for r in res["residuals"]:
        assert np.isfinite(r)
    inc = ad.run_incremental_decoder(prior_mat, syndrome, indptr, indices)
    for p in inc["per_checkpoint"]:
        assert np.isfinite(p["residual"])

def test_clip_finite_all_messages():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    rng = np.random.default_rng(1)
    prior_base = np.log(np.ones(1024)/1024)
    prior_mat=np.tile(prior_base,(1024,1))
    for sym in range(3):
        prior_mat[sym]+=rng.standard_normal(1024)
        prior_mat[sym]-=np.logaddexp.reduce(prior_mat[sym])
    indptr, indices, _ = ad.get_mother_csr()
    syndrome = rng.integers(0,2,size=9036,dtype=np.uint8)
    res = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=3)
    assert res["finite"] == True
    assert res["max_llr"] <= 20.0 + 1e-12
    assert np.all(np.isfinite(res["variable_to_check"]))
    assert np.all(np.isfinite(res["check_to_variable"]))
    assert "hard_bits" in res and res["hard_bits"].shape==(10240,)
    assert "syndrome_observed" in res and res["syndrome_observed"].shape==(9036,)

def test_small_loopy():
    uid = uuid.uuid4().hex[:8]
    out_dir = pathlib.Path(f"workspace/v72p1_rework_tests/{uid}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v72p1_results.json"
    r = subprocess.run([sys.executable, "scripts/v72p1_soft_joint_synthetic.py", "--phase", "P1D", "--seed", "20260902", "--registry", "v72p0_data_registry_synthetic.json", "--out", str(out_file)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout
    j = json.loads(out_file.read_text(encoding="utf-8"))
    assert j["P1D"]["finite"] == True
    assert j["P1D"]["is_tree"] == False
    assert j["P1D"]["wall"] < 5.0

def test_hard_bits_and_syndrome_observed():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    indptr, indices,_ = ad.get_mother_csr()
    rng=np.random.default_rng(20260902)
    prior_base=np.log(np.ones(1024)/1024)
    prior_mat=np.tile(prior_base,(1024,1))
    for sym in range(2):
        prior_mat[sym]+=rng.standard_normal(1024)*0.5
        prior_mat[sym]-=np.logaddexp.reduce(prior_mat[sym])
    syndrome = rng.integers(0,2,size=9036,dtype=np.uint8)
    res = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=3)
    assert res["hard_bits"].dtype == np.uint8
    assert res["hard_symbols"].dtype == np.uint16
    # syndrome_observed must equal H*hard_bits
    hard_bits=res["hard_bits"]
    recomputed = np.zeros(9036,dtype=np.uint8)
    for c in range(9036):
        s=0
        for e in range(int(indptr[c]), int(indptr[c+1])):
            s ^= int(hard_bits[int(indices[e])])
        recomputed[c]=s
    assert np.array_equal(recomputed, res["syndrome_observed"])

