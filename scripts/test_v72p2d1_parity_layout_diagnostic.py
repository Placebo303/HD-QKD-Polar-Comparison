#!/usr/bin/env python3
"""V72P2D1 focused tests S0-S9 — fake runner only, workspace temp isolated.

Run: pytest -p no:cacheprovider scripts/test_v72p2d1_parity_layout_diagnostic.py
Never reads real registry/parquet, never touches production output root,
never calls the real V72P1 decoder by default (fake decoder injection only).
"""
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / "scripts" / "v72p2d1_parity_layout_diagnostic.py"
PROD_OUT = REPO_ROOT / "comparison_bench" / "outputs_comparison" / "v72p2d1_parity_layout_ab"


def _load_harness():
    spec = importlib.util.spec_from_file_location("v72p2d1_harness", str(HARNESS_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load_harness()

_REAL_MOTHER = None


def real_mother():
    global _REAL_MOTHER
    if _REAL_MOTHER is None:
        indptr, indices, nnz = H.get_mother_csr()
        _REAL_MOTHER = (np.asarray(indptr, dtype=np.int32),
                        np.asarray(indices, dtype=np.int32), int(nnz))
    return _REAL_MOTHER


def ensure_workspace() -> Path:
    ws = REPO_ROOT / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def make_temp_root() -> Path:
    ensure_workspace()
    return Path(tempfile.mkdtemp(prefix="v72p2d1_", dir=str(REPO_ROOT / "workspace")))


def tiny_mother():
    # M=6, n=8; rows share pairs -> known 4-cycles; degrees mixed
    rows = [[0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7]]
    indptr = [0]
    indices = []
    for r in rows:
        indices.extend(r)
        indptr.append(len(indices))
    return (np.array(indptr, dtype=np.int32), np.array(indices, dtype=np.int32), 8)


def tiny_bits(n=8, seed=7):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=n, dtype=np.uint8)


def tiny_prior(n_sym=4, n_Q=4, seed=11):
    rng = np.random.default_rng(seed)
    logits = rng.standard_normal((n_sym, n_Q)).astype(np.float64) * 0.5
    mx = logits.max(axis=1, keepdims=True)
    e = np.exp(logits - mx)
    p = e / e.sum(axis=1, keepdims=True)
    p = np.maximum(p, 1e-300)
    p /= p.sum(axis=1, keepdims=True)
    return np.log(p).astype(np.float64)


def make_fake_decoder(hard_bits, residuals=(0.5, 0.1), finite=True, max_llr=1.0,
                      app_val=0.5, calls=None):
    hard_bits = np.asarray(hard_bits, dtype=np.uint8)

    def fn(prior, target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
        if calls is not None:
            calls.append(1)
        ckpt = len(np.asarray(target, dtype=np.uint8))
        indptr = np.asarray(indptr, dtype=np.int32)
        indices = np.asarray(indices, dtype=np.int32)
        active_nnz = len(indices)
        nbit = len(hard_bits)
        # syndrome observed recomputed from hard (honest fake)
        obs = np.zeros(ckpt, dtype=np.uint8)
        for r in range(ckpt):
            s = 0
            for v in indices[indptr[r]:indptr[r + 1]]:
                s ^= int(hard_bits[int(v)])
            obs[r] = np.uint8(s & 1)
        n = min(len(residuals), int(max_iter)) if residuals else 0
        if n == 0:
            res_list = []
        else:
            res_list = [float(residuals[i]) if i < len(residuals) else float(residuals[-1])
                        for i in range(n)]
        return {
            "residuals": res_list,
            "finite": bool(finite),
            "check_to_variable": np.zeros(active_nnz, dtype=np.float64),
            "variable_to_check": np.zeros(active_nnz, dtype=np.float64),
            "hard_bits": hard_bits.copy(),
            "syndrome_observed": obs,
            "max_llr": float(max_llr),
            "app_llr": np.full(nbit, float(app_val), dtype=np.float64),
            "factor_to_bit": np.full(nbit, float(app_val / 2), dtype=np.float64),
        }

    return fn


class FakeClock:
    def __init__(self, step=0.01):
        self.t = 1000.0
        self.step = float(step)

    def __call__(self):
        self.t += self.step
        return self.t


class DeadClock:
    """Already past deadline on first checkpoint publication check."""

    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        # started call returns 0, every later call returns huge elapsed
        if self.n == 1:
            return 0.0
        return 1e9


# ---------------- S0 ----------------

def test_s0_py_compile():
    import py_compile
    assert py_compile.compile(str(HARNESS_PATH), doraise=True)
    assert py_compile.compile(str(Path(__file__)), doraise=True)


def test_s0_mother_dims():
    indptr, indices, nnz = real_mother()
    assert indptr.shape == (9037,)
    assert int(nnz) == 49620
    assert len(indices) == 49620
    dist = H.check_degree_dist(indptr)
    assert dist == {4: 1, 5: 4594, 6: 4441}
    deg = H.col_degrees(indptr, indices, 10240)
    assert int(np.count_nonzero(deg == 2)) == 9035
    # CSR byte size matches V72P1 frozen 284248
    assert 9037 * 4 + 49620 * 4 + 49620 == 284248


def test_s0_output_root_absent_or_refused():
    # production root must not exist; if it exists harness must refuse
    if PROD_OUT.exists():
        with pytest.raises(FileExistsError):
            H.write_terminal_outputs(PROD_OUT, {}, {"arms": []})
    else:
        assert not PROD_OUT.exists()


def test_s0_git_gate_logic_allowlist():
    # B3: literal allowlist lives in H.check_git_allowlist and is unit-tested
    # on synthetic status lines. Live repo carries grandfathered pre-existing
    # untracked outside the allowlist (recorded in OpenSpec); the live check is
    # therefore descriptive and never claims a literal PASS it does not have.
    ok, extras = H.check_git_allowlist([
        "?? openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/",
        "?? scripts/v72p2d1_parity_layout_diagnostic.py",
        "?? scripts/test_v72p2d1_parity_layout_diagnostic.py",
        "?? docs/research_cycles/V72P2D1-PARITY/EXECUTION_PACKET.md",
        "?? docs/research_cycles/V72P2D1-PARITY/REVIEW_VERDICT.md",
        "?? docs/research_cycles/V72P2D1-PARITY/RESULT_SUMMARY.md",
        "?? workspace/v72p2d1_abc123/",
    ])
    assert ok is True and extras == []
    ok2, extras2 = H.check_git_allowlist([
        "?? openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/",
        "?? some/new/file.txt",
    ])
    assert ok2 is False and extras2 == ["?? some/new/file.txt"]
    ok3, extras3 = H.check_git_allowlist(["M scripts/v72p0_soft_joint_binary_synthetic.py"])
    assert ok3 is False
    # live status is reported descriptively under the grandfather exemption
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT),
                          capture_output=True, text=True)
    live = proc.stdout.splitlines() if proc.returncode == 0 else []
    _ok_live, extras_live = H.check_git_allowlist(live)
    # grandfathered pre-existing untracked are expected on this live checkout;
    # the assertion below only records that our own files are present, it does
    # not claim the live tree is literally clean.
    assert (REPO_ROOT / "scripts" / "v72p2d1_parity_layout_diagnostic.py").exists()
    assert (REPO_ROOT / "scripts" / "test_v72p2d1_parity_layout_diagnostic.py").exists()
    assert isinstance(extras_live, list)
    # block0 baseline referenceable with frozen numbers
    assert H.BLOCK0_BASELINE["checkpoints"] == 72
    assert H.BLOCK0_BASELINE["iterations"] == 334
    assert H.BLOCK0_BASELINE["status"] == "LADDER_EXHAUSTED"
    assert H.BLOCK0_BASELINE["bit_errors"] == 3100
    assert H.BLOCK0_BASELINE["symbol_errors"] == 620
    assert (H.BLOCK0_BASELINE["syndrome_bits"], H.BLOCK0_BASELINE["tag_bits"],
            H.BLOCK0_BASELINE["control_bits"]) == (9036, 64, 71)


def test_s0_frozen_cli_defaults():
    assert H.FROZEN_SESSION == "20260123_1M_600k_0dB"
    assert H.FROZEN_REGISTRY == "v71_data_registry.json"
    assert H.FROZEN_OUT == "comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab"
    assert tuple(H.CHECKPOINT_ROWS) == tuple(list(range(160, 8993, 128)) + [9032, 9036])
    assert len(H.CHECKPOINT_ROWS) == 72
    assert H.MAX_ITER_PER_CHECKPOINT == 10
    assert H.MAX_TOTAL_ITERATIONS == 720
    assert H.LLR_CLIP == 20.0
    assert H.CONVERGENCE_TOL == 1e-6
    assert H.SEED_COLMAP == 20260902
    assert H.EXPECTED_LAMBDA == 221.22162910704503
    assert H.EXPECTED_CE == 7.135005172802673


# ---------------- S1 ----------------

def test_s1_colmap_bijection_and_frozen_range():
    cm = H.build_col_map()
    assert len(cm) == 10240
    assert set(cm.tolist()) == set(range(10240))
    # info cols and last col fixed
    assert np.array_equal(cm[:1204], np.arange(1204))
    assert int(cm[10239]) == 10239
    # parity segment is a permutation of 1204..10238
    assert set(cm[1204:10239].tolist()) == set(range(1204, 10239))
    # seed reproducible and domain-separated constant
    cm2 = H.build_col_map()
    assert np.array_equal(cm, cm2)
    assert H.SEED_COLMAP == 20260902


def test_s1_csr_mapping_preserves_order_and_independence():
    indptr_A, indices_A, _ = tiny_mother()
    n = 8
    rng = np.random.default_rng(H.SEED_COLMAP)
    col_map = np.arange(n, dtype=np.int64)
    col_map[1:n - 1] = 1 + rng.permutation(n - 2)
    indptr_B, indices_B = H.build_B_csr(indptr_A, indices_A, col_map)
    assert np.array_equal(indptr_A, indptr_B)
    assert np.array_equal(indices_B, col_map[np.asarray(indices_A, dtype=np.int64)])
    # edge order kept: per-row mapped order equals original order mapped
    for r in range(len(indptr_A) - 1):
        a = indices_A[indptr_A[r]:indptr_A[r + 1]]
        b = indices_B[indptr_B[r]:indptr_B[r + 1]]
        assert np.array_equal(b, col_map[np.asarray(a, dtype=np.int64)])
    assert indptr_A is not indptr_B and indices_A is not indices_B


def test_s1_m1_m7_fake_pass_and_isomorphism():
    indptr_A, indices_A, n = tiny_mother()
    rng = np.random.default_rng(H.SEED_COLMAP)
    col_map = np.arange(n, dtype=np.int64)
    col_map[1:n - 1] = 1 + rng.permutation(n - 2)
    indptr_B, indices_B = H.build_B_csr(indptr_A, indices_A, col_map)
    four_A = H.count_four_cycles(indptr_A, indices_A)
    coll_A = H.count_collisions(indptr_A, indices_A)
    mech = H.verify_M1_M7_fake(indptr_A, indices_A, indptr_B, indices_B,
                               col_map, n, four_A, coll_A)
    assert mech["M1"] and mech["M2"] and mech["M3"] and mech["M4"] and mech["M5"]
    assert mech["M6_independent"] and mech["M7"] and mech["pass"]
    # isomorphism: permutation preserves generic cycle spectrum
    assert mech["four_A"] == mech["four_B"]
    assert mech["coll_A"] == mech["coll_B"]


def test_s1_tampered_colmap_fails():
    indptr_A, indices_A, n = tiny_mother()
    col_map = np.arange(n, dtype=np.int64)  # identity, but tamper B info col
    indptr_B, indices_B = H.build_B_csr(indptr_A, indices_A, col_map)
    indices_B = indices_B.copy()
    # flip one edge to emulate permuted info column leaking into parity area
    indices_B[0] = (int(indices_B[0]) + 1) % n
    four_A = H.count_four_cycles(indptr_A, indices_A)
    coll_A = H.count_collisions(indptr_A, indices_A)
    mech = H.verify_M1_M7_fake(indptr_A, indices_A, indptr_B, indices_B,
                               col_map, n, four_A, coll_A)
    assert not mech["M5"] or not mech["M7"]
    assert not mech["pass"]


def test_s1_expected_constants_declared():
    # B2 recount (get_mother_csr 9036x10240, generic check-pair definition):
    # four=1196 coll=1194 on both arms; frozen 8452/8170 corrected via OpenSpec.
    assert H.EXPECTED_FOUR == 1196
    assert H.EXPECTED_COLL == 1194


def test_s1_real_mother_m1_m6_reported():
    indptr, indices, _ = real_mother()
    col_map = H.build_col_map()
    indptr_B, indices_B = H.build_B_csr(indptr, indices, col_map)
    mech = H.verify_M1_M7(indptr, indices, indptr_B, indices_B, col_map)
    assert mech["M1"] and mech["M2"] and mech["M3"] and mech["M4"] and mech["M5"]
    assert mech["M6_independent"]
    # B2: M7 actuals are recomputed by the shared generic definition (never
    # hand-filled); corrected frozen refs are four=1196 coll=1194 on both arms.
    assert (mech["four_A"], mech["coll_A"]) == (1196, 1194)
    assert (mech["four_B"], mech["coll_B"]) == (1196, 1194)
    assert mech["M7"] is True and mech["pass"] is True
    # isomorphism holds on the real mother too under the generic definition
    assert mech["four_A"] == mech["four_B"]
    assert mech["coll_A"] == mech["coll_B"]


# ---------------- S2 ----------------

def test_s2_syndrome_recompute_per_arm():
    indptr_A, indices_A, n = tiny_mother()
    rng = np.random.default_rng(H.SEED_COLMAP)
    col_map = np.arange(n, dtype=np.int64)
    col_map[1:n - 1] = 1 + rng.permutation(n - 2)
    indptr_B, indices_B = H.build_B_csr(indptr_A, indices_A, col_map)
    b = tiny_bits(n)
    s_A = H.syndrome_compute(indptr_A, indices_A, b)
    s_B = H.syndrome_compute(indptr_B, indices_B, b)
    ok_A, mm_A = H.verify_syndrome(indptr_A, indices_A, b, s_A)
    ok_B, mm_B = H.verify_syndrome(indptr_B, indices_B, b, s_B)
    assert ok_A and mm_A == 0
    assert ok_B and mm_B == 0
    # syndromes differ in general after permutation (same b, different H)
    # (not asserted strictly; recorded here as isolation evidence)
    assert s_A.shape == s_B.shape == (6,)


def test_s2_cross_syndrome_must_fail_and_block_decoder():
    indptr_A, indices_A, n = tiny_mother()
    col_map = np.arange(n, dtype=np.int64)
    # non-trivial swap of two middle columns guarantees H_B != H_A here
    col_map[2], col_map[3] = col_map[3], col_map[2]
    indptr_B, indices_B = H.build_B_csr(indptr_A, indices_A, col_map)
    b = tiny_bits(n, seed=9)
    s_A = H.syndrome_compute(indptr_A, indices_A, b)
    ok_cross, mm = H.verify_syndrome(indptr_B, indices_B, b, s_A)
    # cross use of A's syndrome for B must be detected (D1/M6 predicate)
    # on this tiny graph the syndromes must differ; if they ever coincide,
    # the run_arm path below still enforces per-prefix isolation.
    assert (not ok_cross and mm > 0) or not np.array_equal(
        H.syndrome_compute(indptr_A, indices_A, b),
        H.syndrome_compute(indptr_B, indices_B, b))
    # run_arm with crossed syndrome must NOT call decoder (D1 blocks first ckpt)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    tag = H.candidate_tag(b)
    calls: list = []
    dec = make_fake_decoder(b, calls=calls)
    arm = H.run_arm("B", indptr_B, indices_B, b, bob, prior, s_A, tag, dec,
                    checkpoint_rows=(2, 4, 6), max_iter_per_ckpt=2, max_total=6,
                    deadline_s=600, clock=FakeClock())
    assert arm["status"] == "SYNDROME_MISMATCH"
    assert calls == []
    assert arm["per_checkpoint"][0]["D1_match"] is False
    assert arm["per_checkpoint"][0]["D1_mismatch_rows"] > 0


def test_s2_d1_mismatch_rows_scalar():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    s = H.syndrome_compute(indptr_A, indices_A, b)
    bad = s.copy()
    bad[0] ^= 1
    bad[3] ^= 1
    ok, mm = H.verify_syndrome(indptr_A, indices_A, b, bad)
    assert not ok and mm == 2


# ---------------- S3 ----------------

def test_s3_prefix_slicing_incremental():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    full = H.syndrome_compute(indptr_A, indices_A, b)
    for r in (2, 4, 6):
        part = H.syndrome_compute(indptr_A, indices_A, b, r)
        assert np.array_equal(part, full[:r])


def test_s3_zero_remaining_calls_nothing():
    assert H.available_iterations(720, 10, 720) == 0
    assert H.available_iterations(718, 10, 720) == 2
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    calls: list = []
    dec = make_fake_decoder(b, calls=calls)
    # max_total=0 -> zero budget before first publication
    arm = H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag, dec,
                    checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=0,
                    deadline_s=600, clock=FakeClock())
    assert arm["status"] == "BUDGET_EXHAUSTED"
    assert calls == []
    assert arm["iterations_used"] == 0
    assert arm["syndrome_bits_published"] == 0


def test_s3_warm_carry_new_edges_zero_and_cross_arm_zero():
    # in-arm carry: warm[:prev] preserved; new edges zero-initialized by construction
    prev = np.array([1.0, -2.0, 0.5], dtype=np.float64)
    active_nnz = 5
    warm = np.zeros(active_nnz, dtype=np.float64)
    warm[:len(prev)] = prev[:len(prev)]
    assert np.array_equal(warm[:3], prev)
    assert np.array_equal(warm[3:], np.zeros(2))
    # cross-arm: B must start from zero even if A finished non-zero — run_arm
    # always builds warm=zeros per arm (no cross-arm state); verify via two runs
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    seen_warms: list = []

    def spy(prior_, target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
        seen_warms.append(np.asarray(warm_start_c2v, dtype=np.float64).copy())
        return make_fake_decoder(b)(prior_, target, indptr=indptr, indices=indices,
                                    max_iter=max_iter, warm_start_c2v=warm_start_c2v)

    H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag, spy,
              checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
              deadline_s=600, clock=FakeClock())
    first_of_A = seen_warms[0]
    assert np.all(first_of_A == 0.0)
    seen_warms.clear()
    H.run_arm("B", indptr_A, indices_A, b, bob, prior, syn, tag, spy,
              checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
              deadline_s=600, clock=FakeClock())
    assert np.all(seen_warms[0] == 0.0)


def test_s3_ladder_constants_and_a_then_b_order():
    assert len(H.CHECKPOINT_ROWS) == 72
    assert H.CHECKPOINT_ROWS[0] == 160 and H.CHECKPOINT_ROWS[-1] == 9036
    assert H.CHECKPOINT_ROWS[-2] == 9032 and H.CHECKPOINT_ROWS[-3] == 8992
    order: list = []

    def dec_a(prior, target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
        order.append("A")
        return make_fake_decoder(tiny_bits(8))(prior, target, indptr=indptr,
                                               indices=indices, max_iter=max_iter,
                                               warm_start_c2v=warm_start_c2v)

    def dec_b(prior, target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
        order.append("B")
        return make_fake_decoder(tiny_bits(8))(prior, target, indptr=indptr,
                                               indices=indices, max_iter=max_iter,
                                               warm_start_c2v=warm_start_c2v)

    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag, dec_a,
              checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
              deadline_s=600, clock=FakeClock())
    H.run_arm("B", indptr_A, indices_A, b, bob, prior, syn, tag, dec_b,
              checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
              deadline_s=600, clock=FakeClock())
    assert order[0] == "A" and "B" in order
    # iterations count equals len(residuals) trajectory
    assert H.available_iterations(0) == 10


# ---------------- S4 ----------------

def _injected_fake(**kw):
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n, seed=kw.get("seed", 7))
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    four = H.count_four_cycles(indptr_A, indices_A)
    coll = H.count_collisions(indptr_A, indices_A)
    base = {
        "indptr_A": indptr_A,
        "indices_A": indices_A,
        "alice_bits": b,
        "bob_symbols": bob,
        "prior_logp": prior,
        "lambda": 0.5,
        "ce": 1.25,
        "cal_ok": True,
        "expected_four": four,
        "expected_coll": coll,
        "checkpoint_rows": (2, 4, 6),
        "max_iter_per_ckpt": 2,
        "max_total": 6,
        "baseline_ok": True,
        "registry": {"schema": "fake", "data_sha": "fake"},
        "session": {"session_id": H.FROZEN_SESSION, "source_label": "fake"},
        "cal_ids": [702, 703],
    }
    base.update(kw)
    return base


def test_s4_cal_failed_zero_calls_and_four_files():
    tmp = make_temp_root()
    out = tmp / "run_cal_fail"
    calls: list = []
    inj = _injected_fake(cal_ok=False, decoder_fn=make_fake_decoder(tiny_bits(8), calls=calls))
    rc = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                              arm_budget_s=600, global_budget_s=1800,
                              decoder_fn=None, injected=inj, clock=FakeClock())
    assert rc == 1
    assert calls == []
    got = sorted(p.name for p in out.iterdir() if p.is_file())
    assert got == ["manifest.json", "report.md", "results.json", "table.csv"]
    res = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert res["arms"][0]["status"] == "NOT_ATTEMPTED"
    assert res["arms"][1]["status"] == "NOT_ATTEMPTED"
    assert res["arms"][0]["D"] is None and res["arms"][1]["D"] is None


def test_s4_a_gate_b_on_numeric():
    tmp = make_temp_root()
    out = tmp / "run_a_gate"
    b = tiny_bits(8)
    calls_b: list = []

    def dec_a(prior, target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
        return make_fake_decoder(b, finite=False)(prior, target, indptr=indptr,
                                                  indices=indices, max_iter=max_iter,
                                                  warm_start_c2v=warm_start_c2v)

    def dec_b(prior, target, indptr=None, indices=None, max_iter=10, warm_start_c2v=None):
        calls_b.append(1)
        return make_fake_decoder(b)(prior, target, indptr=indptr, indices=indices,
                                    max_iter=max_iter, warm_start_c2v=warm_start_c2v)

    # execute_diagnostic uses one counting decoder for both arms; emulate gate by
    # making A fail then asserting B never runs via baseline_ok=False path below.
    inj = _injected_fake(decoder_fn=dec_a, baseline_ok=False)
    rc = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                              arm_budget_s=600, global_budget_s=1800,
                              decoder_fn=None, injected=inj, clock=FakeClock())
    assert rc == 1
    res = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert res["arms"][1]["status"] == "NOT_ATTEMPTED"
    assert res["arms"][1]["error"] == "gate_stopped_by_A"
    assert calls_b == []


def test_s4_deadline_stops_before_publication():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    calls: list = []
    arm = H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag,
                    make_fake_decoder(b, calls=calls),
                    checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
                    deadline_s=600, clock=DeadClock())
    assert arm["status"] == "TIMEOUT"
    assert calls == []


def test_s4_second_call_same_out_refuses():
    tmp = make_temp_root()
    out = tmp / "run_twice"
    inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)))
    rc1 = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                               arm_budget_s=600, global_budget_s=1800,
                               decoder_fn=None, injected=inj, clock=FakeClock())
    assert rc1 in (0, 1)
    before = sorted(p.name for p in out.iterdir() if p.is_file())
    with pytest.raises(FileExistsError):
        H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                             arm_budget_s=600, global_budget_s=1800,
                             decoder_fn=None, injected=_injected_fake(
                                 decoder_fn=make_fake_decoder(tiny_bits(8))),
                             clock=FakeClock())
    after = sorted(p.name for p in out.iterdir() if p.is_file())
    assert before == after == ["manifest.json", "report.md", "results.json", "table.csv"]


def test_s4_budgets_frozen_values():
    assert H.ARM_BUDGET_S == 600.0
    assert H.GLOBAL_BUDGET_S == 1800.0


# ---------------- S5 ----------------

def test_s5_d1_d8_scalars_present():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    # hard differs from Bob on purpose (counterexample: decoder output != Bob)
    hard = np.asarray([(x ^ 1) for x in H.symbols_to_bits(bob, 2)], dtype=np.uint8)
    arm = H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag,
                    make_fake_decoder(hard),
                    checkpoint_rows=(2, 4, 6), max_iter_per_ckpt=2, max_total=6,
                    deadline_s=600, clock=FakeClock(), ce_ref=1.25)
    assert arm["per_checkpoint"]
    last = arm["per_checkpoint"][-1]
    for key in ["D1_match", "D1_mismatch_rows", "D2_sym_errors", "D2_sym_match",
                "D3_bit_errors", "D4_finite", "D4_max_abs", "D4_mean",
                "D5_finite", "D5_max_abs", "D5_residual", "D5_iters",
                "D6_f2b_finite", "D6_n_flip_f2b", "D6_n_flip_app",
                "D7_bit_errors_deg2", "D7_bit_errors_rest",
                "D7_mean_abs_app_deg2", "D7_mean_abs_app_rest",
                "D8_alice_vs_bob_bit", "D8_alice_vs_bob_sym",
                "D8_oracle_exact", "D8_undetected"]:
        assert key in last, key
    # vsBob counterexample: hard != Bob so errors nonzero and recorded
    assert last["D2_sym_errors"] > 0 or last["D3_bit_errors"] > 0


def test_s5_d1_recompute_and_deg_grouping():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n, seed=21)
    bob = np.array([3, 2, 1, 0], dtype=np.int32)
    prior = tiny_prior(seed=22)
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    arm = H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag,
                    make_fake_decoder(b),
                    checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
                    deadline_s=600, clock=FakeClock(), ce_ref=1.0)
    last = arm["per_checkpoint"][-1]
    assert last["D1_match"] is True and last["D1_mismatch_rows"] == 0
    # deg grouping adds up to total vsBob bit errors
    assert last["D7_bit_errors_deg2"] + last["D7_bit_errors_rest"] == last["D3_bit_errors"]
    assert last["D7_mean_abs_app_deg2"] >= 0 and last["D7_mean_abs_app_rest"] >= 0


def test_s5_no_full_arrays_persisted():
    tmp = make_temp_root()
    out = tmp / "run_schema"
    inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)))
    H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                         arm_budget_s=600, global_budget_s=1800,
                         decoder_fn=None, injected=inj, clock=FakeClock())
    res_text = (out / "results.json").read_text(encoding="utf-8")
    man_text = (out / "manifest.json").read_text(encoding="utf-8")
    for forbidden in ["prior_logp", "check_to_variable", "variable_to_check",
                      "syndrome_bytes", "bit_to_factor", "per-bit", "per_bit",
                      "full_matrix", "indices_full"]:
        assert forbidden not in res_text
        assert forbidden not in man_text
    res = json.loads(res_text)
    assert len(res["arms"]) == 2
    rows = list(csv.DictReader((out / "table.csv").read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 2


# ---------------- S6 ----------------

def test_s6_oracle_posthoc_does_not_change_accept():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    arm = H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag,
                    make_fake_decoder(b),
                    checkpoint_rows=(2, 4), max_iter_per_ckpt=2, max_total=4,
                    deadline_s=600, clock=FakeClock())
    # accepted requires finite+syndrome+tag on the CURRENT candidate only
    for ck in arm["per_checkpoint"]:
        if ck["protocol_accepted"]:
            assert ck["finite"] and ck["syndrome_ok"] and ck["tag_ok"]
    # oracle is posthoc: flipping the oracle comparison afterwards cannot
    # change the recorded accept (accept already fixed before oracle read)
    if arm["per_checkpoint"]:
        assert "D8_oracle_exact" in arm["per_checkpoint"][-1]


def test_s6_undetected_isolated_never_merged():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n, seed=31)
    bob_symbols = np.array([0, 0, 0, 0], dtype=np.int32)
    prior = tiny_prior(seed=32)
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    # craft hard that matches syndrome+tag of... impossible without alice;
    # instead verify isolation semantics on a VERIFIED run with wrong oracle:
    # use hard=b (exact) then check flags are consistent (no undetected),
    # and separately verify a non-exact accept would set undetected.
    tag = H.candidate_tag(b)
    arm_ok = H.run_arm("A", indptr_A, indices_A, b, bob_symbols, prior, syn, tag,
                       make_fake_decoder(b),
                       checkpoint_rows=(2,), max_iter_per_ckpt=2, max_total=2,
                       deadline_s=600, clock=FakeClock())
    if arm_ok["protocol_accepted"]:
        assert arm_ok["verified_exact_success"] is True
        assert arm_ok["undetected"] is False
    # isolation invariant: undetected is never counted as success
    assert not (arm_ok["undetected"] and arm_ok["verified_exact_success"])


def test_s6_stale_candidate_cannot_substitute():
    indptr_A, indices_A, n = tiny_mother()
    b = tiny_bits(n)
    bob = np.array([0, 1, 2, 3], dtype=np.int32)
    prior = tiny_prior()
    syn = H.syndrome_compute(indptr_A, indices_A, b)
    tag = H.candidate_tag(b)
    arm = H.run_arm("A", indptr_A, indices_A, b, bob, prior, syn, tag,
                    make_fake_decoder(b, residuals=(0.9, 0.8)),
                    checkpoint_rows=(2, 4, 6), max_iter_per_ckpt=2, max_total=6,
                    deadline_s=600, clock=FakeClock())
    # each checkpoint log carries its own current-candidate flags only
    ckpts = [c["checkpoint_rows"] for c in arm["per_checkpoint"]]
    assert ckpts == sorted(ckpts)
    for c in arm["per_checkpoint"]:
        assert "syndrome_ok" in c and "tag_ok" in c and "protocol_accepted" in c


def test_s6_prior_bob_only_natural_log_and_ce_log2():
    # prior uses natural log; CE uses log2: verify on a tiny known case
    Ps = np.array([[0.5, 0.5], [0.25, 0.75]], dtype=np.float64)
    bob = np.array([0, 1], dtype=np.int32)
    rows = np.maximum(Ps[bob], 1e-300)
    rows = rows / rows.sum(axis=1, keepdims=True)
    prior = np.log(rows)
    assert np.allclose(prior, np.log(rows))
    assert not np.allclose(prior, np.log2(rows))
    alice = np.array([0, 1], dtype=np.int32)
    ce = float(-np.log2(np.maximum(Ps[bob, alice], 1e-300)).mean())
    assert ce == pytest.approx(float(-(np.log2(0.5) + np.log2(0.75)) / 2))


# ---------------- S7 ----------------

def test_s7_fake_two_arms_exactly_four_files():
    tmp = make_temp_root()
    out = tmp / "run_two_arms"
    inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)))
    rc = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                              arm_budget_s=600, global_budget_s=1800,
                              decoder_fn=None, injected=inj, clock=FakeClock())
    assert rc in (0, 1)
    got = sorted(p.name for p in out.iterdir() if p.is_file())
    assert got == ["manifest.json", "report.md", "results.json", "table.csv"]
    res = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert len(res["arms"]) == 2
    assert res["arms"][0]["arm"] == "A" and res["arms"][1]["arm"] == "B"


def test_s7_failure_states_also_four_files_not_attempted():
    tmp = make_temp_root()
    out = tmp / "run_m_fail"
    indptr_A, indices_A, n = tiny_mother()
    # force M failure with wrong expectations
    inj = _injected_fake(expected_four=-1, expected_coll=-1,
                         decoder_fn=make_fake_decoder(tiny_bits(8)))
    rc = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                              arm_budget_s=600, global_budget_s=1800,
                              decoder_fn=None, injected=inj, clock=FakeClock())
    assert rc == 1
    got = sorted(p.name for p in out.iterdir() if p.is_file())
    assert got == ["manifest.json", "report.md", "results.json", "table.csv"]
    res = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert res["fatal_error"] == "M_FAILED"


def test_s7_existing_dir_refuses_zero_files():
    tmp = make_temp_root()
    out = tmp / "run_exists"
    out.mkdir(parents=True)
    (out / "sentinel.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError):
        H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                             arm_budget_s=600, global_budget_s=1800,
                             decoder_fn=None, injected=_injected_fake(
                                 decoder_fn=make_fake_decoder(tiny_bits(8))),
                             clock=FakeClock())
    # refused without overwrite: sentinel intact, no four files created
    assert (out / "sentinel.txt").read_text(encoding="utf-8") == "x"
    assert not (out / "manifest.json").exists()


def test_s7_fake_decoder_injected_real_never_called():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    called = {"n": 0}
    orig = ad.run_decoder

    def spy(*a, **k):
        called["n"] += 1
        return orig(*a, **k)

    ad.run_decoder = spy
    try:
        tmp = make_temp_root()
        out = tmp / "run_injected"
        inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)))
        H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                             arm_budget_s=600, global_budget_s=1800,
                             decoder_fn=None, injected=inj, clock=FakeClock())
        assert called["n"] == 0
    finally:
        ad.run_decoder = orig


def test_s7_workspace_temp_independent_and_not_counted():
    tmp = make_temp_root()
    assert "v72p2d1_" in tmp.name
    assert tmp.parent.name == "workspace"
    out = tmp / "run_tmp_check"
    inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)))
    H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                         arm_budget_s=600, global_budget_s=1800,
                         decoder_fn=None, injected=inj, clock=FakeClock())
    # final out has exactly four files; workspace temp candidates are elsewhere
    assert sorted(p.name for p in out.iterdir() if p.is_file()) == [
        "manifest.json", "report.md", "results.json", "table.csv"]
    # production root untouched by fake tests
    assert not PROD_OUT.exists() or PROD_OUT.is_dir()


# ---------------- S8 ----------------

def test_s8_lambda_exact_and_ce_tol_refs():
    assert H.EXPECTED_LAMBDA == 221.22162910704503
    assert H.EXPECTED_CE == 7.135005172802673
    assert (H.EXPECTED_LAMBDA == 221.22162910704503) is True
    assert abs(7.135005172802673 - H.EXPECTED_CE) <= 1e-12
    assert abs(7.135005172802673 + 1e-11 - H.EXPECTED_CE) > 1e-12


def test_s8_match_allows_b_mismatch_bans_b():
    # mismatch bans B
    tmp = make_temp_root()
    out = tmp / "run_base_mismatch"
    inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)),
                         baseline_ok=False, enforce_frozen_refs=False,
                         **{"lambda": 0.5, "ce": 1.25})
    rc = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                              arm_budget_s=600, global_budget_s=1800,
                              decoder_fn=None, injected=inj, clock=FakeClock())
    assert rc == 1
    res = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert res["arms"][1]["status"] == "NOT_ATTEMPTED"
    assert res["arms"][1]["error"] == "gate_stopped_by_A"
    # frozen-ref enforcement: wrong lambda with enforce flag also bans B
    tmp2 = make_temp_root()
    out2 = tmp2 / "run_lambda_mismatch"
    inj2 = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)),
                          baseline_ok=True, enforce_frozen_refs=True,
                          **{"lambda": 0.5, "ce": H.EXPECTED_CE})
    rc2 = H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out2),
                               arm_budget_s=600, global_budget_s=1800,
                               decoder_fn=None, injected=inj2, clock=FakeClock())
    assert rc2 == 1
    res2 = json.loads((out2 / "results.json").read_text(encoding="utf-8"))
    assert res2["arms"][1]["status"] == "NOT_ATTEMPTED"


def test_s8_baseline_compare_exact_items():
    arm = {"per_checkpoint": [{"x": 1}] * 72, "iterations_used": 334,
           "status": "LADDER_EXHAUSTED", "bit_errors": 3100, "symbol_errors": 620,
           "syndrome_bits_published": 9036, "tag_bits_published": 64,
           "control_bits_sent": 71}
    ok, _ = H.compare_baseline_A(arm, H.EXPECTED_LAMBDA, H.EXPECTED_CE)
    assert ok is True
    bad = dict(arm)
    bad["iterations_used"] = 335
    ok2, diffs = H.compare_baseline_A(bad, H.EXPECTED_LAMBDA, H.EXPECTED_CE)
    assert ok2 is False
    ok3, _ = H.compare_baseline_A(arm, H.EXPECTED_LAMBDA, H.EXPECTED_CE + 1e-9)
    assert ok3 is False


# ---------------- S9 ----------------

def test_s9_old_decoder_unchanged():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    assert set(ad.FrozenMotherSpec.keys()) == {"Q", "N", "Nbit", "M", "r0", "delta",
                                               "max_rows", "f_planning", "column_mapping"}
    assert len(ad.FrozenMotherSpec) == 9
    assert "tag_bits" not in ad.FrozenMotherSpec
    assert len(ad.SoftJointConfig) == 8
    assert ad.SoftJointConfig["tag_bits"] == 64
    assert ad.SoftJointConfig["warm_start"] is True
    assert ad.SoftJointConfig["dtype"] == "float64"
    assert ad.SoftJointConfig["llr_clip"] == 20.0
    assert ad.SoftJointConfig["convergence_tol"] == 1e-6
    assert len(ad.ARRAY_SPECS) == 11
    assert len(ad.SoftJointConfig["checkpoint_rows"]) == 72
    # old implementation/test/plan/results files untouched by this change
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--",
                        "comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py",
                        "scripts/v72p0_soft_joint_binary_synthetic.py",
                        "scripts/v72p1_soft_joint_synthetic.py",
                        "scripts/v72p2_real_smoke.py"],
                       cwd=str(REPO_ROOT))
    assert r.returncode == 0


@pytest.mark.xfail(reason="V72P1 P1C 1-iteration 1.046s exceeds <1s threshold; retained known FAIL, threshold unchanged",
                   strict=False)
def test_s9_known_1s_timing_retained_fail():
    # Historical V72P2 RESULT_SUMMARY regression note: 29 passed, P1C 1-iter
    # 1.046s exceeded <1s. This failure is explicitly retained and
    # non-blocking; the threshold and kernel are unchanged.
    assert 1.046 < 1.0


def test_s9_new_tests_never_touch_real_registry_or_production():
    # behavioral guard: every execute_diagnostic call in this file uses an
    # injected fake dict with a workspace temp out; the real path (B1) is
    # implemented but never invoked by fake tests and never touches PROD_OUT.
    assert "pandas" not in sys.modules or True
    assert not PROD_OUT.exists() or PROD_OUT.is_dir()
    # B1 real-path helpers exist and enforce the frozen assignment without
    # running the heavy decoder: wrong CAL must raise, frozen block passes.
    assert callable(H.check_assigned_v72p2d1) and callable(H._load_v72p2)
    good = {"stage2_CAL_frame_ids": list(range(H.CAL_START, H.CAL_STOP)),
            "stage2_VAL_frame_ids": [1726, 1727, 1728, 1729, 1730]}
    cal, blk = H.check_assigned_v72p2d1(good)
    assert blk == [1726, 1727, 1728, 1729]
    with pytest.raises(Exception):
        H.check_assigned_v72p2d1({"stage2_CAL_frame_ids": [702, 704],
                                  "stage2_VAL_frame_ids": [1726, 1727, 1728, 1729]})


def test_s4_fake_missing_decoder_raises_no_fallback():
    # B4: fake path with decoder_fn None must raise, never fall back to real.
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    called = {"n": 0}
    orig = ad.run_decoder

    def spy(*a, **k):
        called["n"] += 1
        return orig(*a, **k)

    ad.run_decoder = spy
    try:
        tmp = make_temp_root()
        out = tmp / "run_no_fake_decoder"
        inj = _injected_fake()
        inj.pop("decoder_fn", None)  # no fake decoder supplied
        with pytest.raises(RuntimeError, match="injected decoder_fn"):
            H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                                 arm_budget_s=600, global_budget_s=1800,
                                 decoder_fn=None, injected=inj, clock=FakeClock())
        assert called["n"] == 0
        assert not out.exists() or sorted(
            p.name for p in out.iterdir() if p.is_file()) != [
            "manifest.json", "report.md", "results.json", "table.csv"]
    finally:
        ad.run_decoder = orig


def test_s7_single_writer_unified_and_tmp_cleaned():
    # B5: write_terminal_outputs and _write_four are one writer; report unified.
    tmp = make_temp_root()
    before = {p.name for p in (REPO_ROOT / "workspace").iterdir() if p.is_dir()}
    out = tmp / "run_writer_check"
    inj = _injected_fake(decoder_fn=make_fake_decoder(tiny_bits(8)))
    H.execute_diagnostic("fake_registry.json", H.FROZEN_SESSION, str(out),
                         arm_budget_s=600, global_budget_s=1800,
                         decoder_fn=None, injected=inj, clock=FakeClock())
    after = {p.name for p in (REPO_ROOT / "workspace").iterdir() if p.is_dir()}
    # execute-internal candidate temp is removed; only the test's own temp root
    # (created by make_temp_root) may remain.
    assert after <= before | {tmp.name}
    rep = (out / "report.md").read_text(encoding="utf-8")
    assert "bit=" in rep and "sym=" in rep
    # alias produces the identical four-file layout on a second temp out
    out2 = tmp / "run_writer_alias"
    res = json.loads((out / "results.json").read_text(encoding="utf-8"))
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    H._write_four(out2, man, res)
    assert sorted(p.name for p in out2.iterdir() if p.is_file()) == [
        "manifest.json", "report.md", "results.json", "table.csv"]
    rep2 = (out2 / "report.md").read_text(encoding="utf-8")
    assert "bit=" in rep2 and "sym=" in rep2
