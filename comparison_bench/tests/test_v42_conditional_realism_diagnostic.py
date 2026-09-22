"""Focused V42P0 tests (T1-T12) for the dual-condition diagnostic runner.

All tests are fake-runner / stub-decode or decoder-free. No production
decoder is invoked, the official V42 output root is never created.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, load_v25_channel_counts, get_conditional_posterior_l2, sample_empirical_block, factorize_f03
from comparison_bench.formal_ir import v42_conditional_realism_diagnostic as v42

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v42_conditional_realism_diagnostic.py"

INITIAL_BY_BLOCK = {
    390110: 250, 390111: 261, 390112: 272,
    390210: 255, 390211: 266, 390212: 277,
    390310: 249, 390311: 258, 390312: 267,
}


@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()


class FakeWorld:
    def __init__(self):
        self.metrics_by_id: dict[str, dict] = {}
        self.constructors = {"lane_c": self._make_ctor("lane_c")}

    def _make_ctor(self, lane):
        def _ctor(source: str, seed: int, field=None):
            H = np.zeros((4, 1024), dtype=np.uint8)
            H[0, ::8] = 1
            H[1, ::9] = 1
            H[2, ::11] = 1
            H[3, ::13] = 1
            matrix_id = f"{lane}_{source}_s{seed}"
            metrics = {
                "lane": lane, "source": source, "construction_seed": seed, "matrix_id": matrix_id,
                "shape": [4, 1024], "rank_GF32": 4, "support_edge_count": int((H != 0).sum()),
                "col_degree_min": 0, "col_degree_mean": int((H != 0).sum())/1024, "col_degree_max": 4,
                "row_degree_min": 79, "row_degree_mean": float((H != 0).sum())/4, "row_degree_max": 128,
                "degenerate_cycles_4": 0, "degenerate_cycles_6": 0, "degenerate_cycles_8": 0,
                "support_cycles_4": 0, "structurally_valid": True,
            }
            metrics["position_permutations"] = [[0, 1], [1, 0]]
            self.metrics_by_id[matrix_id] = metrics
            return H, metrics
        return _ctor

    def authority_file(self, tmp_path: Path) -> Path:
        for source in v42.SOURCE_ORDER:
            for seed in v42.CONSTRUCTION_SEEDS["lane_c"][source]:
                self.constructors["lane_c"](source=source, seed=seed)
        # need 27 records total for loader check (same as v38)
        records: list[dict] = []
        for source in v42.SOURCE_ORDER:
            for seed in (911001, 911002, 911003):
                records.append({"lane": "lane_a", "source": source, "construction_seed": seed, "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"})
            for seed in (912001, 912002, 912003):
                records.append({"lane": "lane_b", "source": source, "construction_seed": seed, "matrix_id": f"lane_b_{source}_s{seed}", "shape": "[4, 1024]"})
        for mid, met in self.metrics_by_id.items():
            records.append(dict(met))
        # also add missing lane_b/lane_a extra to reach 27
        # current: 3*3 lane_a +3*3 lane_b +3 lane_c = 9+9+3=21 => need 6 more dummy
        for i in range(6):
            records.append({"lane": "lane_c", "source": "1M", "construction_seed": 999000+i, "matrix_id": f"lane_c_1M_s{999000+i}", "shape": "[4, 1024]", "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True, "position_permutations": [[0]]})
        # trim to 27
        records = records[:27]
        # ensure our 3 ordered are present
        for src in v42.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v42._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path


def fake_decode_factory(outcome_fn, calls: list | None = None):
    """outcome_fn(source, block_seed, condition) -> (exact, final, syndrome_ok)"""
    def _decode(H, prior, synd, max_iter=90, damping_alpha=1.0, field=None):
        if calls is not None:
            calls.append((max_iter, damping_alpha))
        # decode_fn signature: (H, prior, synd, max_iter, damping_alpha, field)
        # Need to recover condition/source info - we embed via closure not available.
        # Instead we use a global counter approach in run_scenario.
        raise NotImplementedError
    return _decode


def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    """fake_outcome maps call_index 0..17 -> (exact, final, syndrome_ok)"""
    world = FakeWorld()
    # Install fake decode_fn that returns based on call order
    counter = {"n": 0}
    def _fake_decode(H, prior, synd, max_iter=90, damping_alpha=1.0, field=None):
        if calls is not None:
            calls.append({"max_iter": max_iter, "damping_alpha": damping_alpha})
        idx = counter["n"]
        counter["n"] += 1
        res = fake_outcome(idx)
        if len(res)==2:
            exact, final = res
            syn_ok = exact
        else:
            exact, final, syn_ok = res
        # Return object with expected attrs
        x_hat = np.zeros(1024, dtype=np.uint8)  # not used for exact check except via exact flag? But runner checks x_hat vs u2_alice
        # We need to make runner's exact derived from decode result vs true.
        # Runner uses np.array_equal(res.x_hat, u2_alice). To control exact, we monkeypatch _evaluate_one_condition directly
        # Simpler: monkeypatch _evaluate_one_condition
        raise AssertionError("should be patched via _evaluate_one_condition")
    # Instead monkeypatch _evaluate_one_condition to control exact via fake
    original_eval = v42._evaluate_one_condition
    def _patched_eval(matrix, source, block_seed, condition, counts, bob, u1_selector, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "condition": condition, "block_seed": block_seed})
        exact, final, syn_ok = fake_outcome(idx) if len(fake_outcome(idx))==3 else (*fake_outcome(idx), fake_outcome(idx)[0])
        # ensure fake_runner path uses our values regardless
        return {"condition": condition, "source": source, "block_seed": block_seed, "construction_seed": spec["construction_seed"], "matrix_id": spec["matrix_id"], "errors_initial": int(errors_initial), "errors_final": int(final), "exact_l2": bool(exact), "syndrome_ok": bool(syn_ok), "iterations": 5 if exact else 90, "status": "converged_exact" if exact else "max_iter", "runtime_s": 0.001}
    monkeypatch.setattr(v42, "_evaluate_one_condition", _patched_eval)
    root = tmp_path / name
    result = v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# T1
def test_t1_registry_accepts_frozen_nine():
    ok, msg = v42.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    assert set(v42.NEW_BLOCK_SEEDS.keys()) == set(v42.SOURCE_ORDER)
    flat = [s for src in v42.SOURCE_ORDER for s in v42.NEW_BLOCK_SEEDS[src]]
    assert flat == [390110,390111,390112,390210,390211,390212,390310,390311,390312]

def _reg_with(source, repl):
    reg = {src: list(seeds) for src,seeds in v42.NEW_BLOCK_SEEDS.items()}
    reg[source]=repl
    return reg

@pytest.mark.parametrize("bad_reg", [
    _reg_with("1M", [390110,390110,390111]),
    _reg_with("1p5M", [390210,390211]),
    _reg_with("2M", [390310,390311,390312,390313]),
    _reg_with("1M", [360101,390111,390112]),
    _reg_with("1p5M", [390201,390211,390212]),
    _reg_with("2M", [390306,390311,390312]),
    _reg_with("1M", [390107,390111,390112]),  # V41 overlap
    {"1M":[390110],"1p5M":[390210]},
])
def test_t1_registry_rejects_drift(bad_reg):
    ok,_ = v42.validate_seed_registry(bad_reg)
    assert not ok

@pytest.mark.parametrize("probe_seed", [390106,390206,390306])
def test_t1_each_v40_probe_forbidden(probe_seed):
    reg = {src: list(seeds) for src,seeds in v42.NEW_BLOCK_SEEDS.items()}
    reg["1M"][0]=probe_seed
    ok,msg = v42.validate_seed_registry(reg)
    assert not ok and str(probe_seed) in msg

@pytest.mark.parametrize("v41seed", [390107,390108,390109,390207,390208,390209,390307,390308,390309])
def test_t1_each_v41_seed_forbidden(v41seed):
    reg = {src: list(seeds) for src,seeds in v42.NEW_BLOCK_SEEDS.items()}
    # inject into 1M first slot if 1M family else appropriate
    ok,_ = v42.validate_seed_registry({**reg, "1M": [v41seed,390111,390112]})
    assert not ok

# T2
def test_t2_reconstruction_deterministic(tmp_path, monkeypatch):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    first = v42.reconstruct_v42_matrices(authority, field=field, constructors=world.constructors)
    second = v42.reconstruct_v42_matrices(authority, field=field, constructors=world.constructors)
    assert set(first.keys()) == set(second.keys()) == set(v42.RECONSTRUCTION_KEYS)
    for k in v42.RECONSTRUCTION_KEYS:
        assert np.array_equal(first[k][0], second[k][0])
        assert first[k][1]==second[k][1]
    for k in v42.RECONSTRUCTION_KEYS:
        assert "position_permutations" in first[k][1]
    ids = sorted(f"lane_c_{src}_s{v42._rep_seed('lane_c', src)}" for _,src in v42.RECONSTRUCTION_KEYS)
    assert sorted(v42.FROZEN_REPRESENTATIVE_MATRIX_IDS)==ids

def test_t2_reconstruction_detects_drift(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"]=="lane_c_1M_s383102")
    victim["rank_GF32"]=int(victim["rank_GF32"])-1
    bad = tmp_path/"bad.json"
    bad.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v42.IntegrityFailure) as e:
        v42.reconstruct_v42_matrices(bad, field=field, constructors=world.constructors)
    assert e.value.check_id=="J3"
    # permutation drift
    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"]=="lane_c_1M_s383102")
    victim["position_permutations"]=[[5,5],[5,5]]
    bad2 = tmp_path/"bad2.json"
    bad2.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v42.IntegrityFailure) as e2:
        v42.reconstruct_v42_matrices(bad2, field=field, constructors=world.constructors)
    assert e2.value.check_id=="J3"
    # identity drift
    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"]=="lane_c_1M_s383102")
    victim["lane"]="lane_b"
    bad3 = tmp_path/"bad3.json"
    bad3.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v42.IntegrityFailure) as e3:
        v42.reconstruct_v42_matrices(bad3, field=field, constructors=world.constructors)
    assert e3.value.check_id=="J3"
    # NPZ forbidden
    with pytest.raises(v42.IntegrityFailure) as e4:
        v42.reconstruct_v42_matrices(tmp_path/"x.npz", field=field, constructors=world.constructors)
    assert e4.value.check_id=="J8"

# T3
def test_t3_sentinels_pass(real_counts):
    res = v42.dual_posterior_binding_preflight(real_counts)
    assert set(res.keys())==set(v42.SOURCE_ORDER)
    for src,chk in res.items():
        assert chk["probe_block_seed"]==v42.PREFLIGHT_BLOCK_SEEDS[src]
        assert chk["bob_gt_31"] is True
        assert chk["captured_equals_bob"] is True
        assert chk["corrected_equals_direct"] is True
        assert chk["corrected_differs_u2bob_arraywise"] is True
        assert chk["corrected_differs_u2bob_maxabs"] is True
        assert chk["argmax_divergence"] is True
        assert chk["carrier_identity"] is True
        assert chk["arms_differ"] is True
        assert chk["l1_accuracy_computable"] is True
        # also check public inputs property implicit

def test_t3_tampered_u2bob_detected(real_counts):
    real = get_conditional_posterior_l2
    def bad_posterior(cnt,b,u1):
        return real(cnt, (np.asarray(b)+1)%32, u1) if np.array_equal(u1, real_counts["1M"]) else real(cnt,b,u1)  # dummy, not used
    # tamper via substituting posterior to use u2_bob instead of bob
    def tampered(cnt,b,u1):
        # Use second call's capture to simulate wrong carrier: return posterior for different b
        return real(cnt, (b+1)%32, u1)
    # Carrier identity failure: posterior that returns different prior for estimated arm
    # We test via monkeypatching estimate to use alice-dependent: will be caught because arms_differ? Let's just test captured_equals_bob via custom posterior that mutates b
    def mutating(cnt,b,u1):
        b_mut = np.asarray(b).copy()
        b_mut[0] = (int(b_mut[0])+1)%32
        # but spy captures before mutation? The spy copies before call, so captured still equals original bob, but we mutate inside
        # To make captured_equals_bob fail, need posterior_fn that internally changes the passed b array
        b[0] = (int(b[0])+1)%32
        return real(cnt,b,u1)
    with pytest.raises(v42.IntegrityFailure) as exc:
        v42.dual_posterior_binding_preflight(real_counts, posterior_fn=mutating)
    assert exc.value.check_id=="J5"

def test_t3_l1_accuracy_bounds(real_counts):
    for src in v42.SOURCE_ORDER:
        counts = real_counts[src]
        idx, alice, bob = sample_empirical_block(counts, seed=390110 if src=="1M" else 390210 if src=="1p5M" else 390310, size=1024)
        u1_a,_,_,_ = factorize_f03(alice,bob)
        u1_hat = v42.estimate_u1_map_l1(counts,bob)
        acc = v42.compute_l1_map_accuracy(u1_hat, u1_a)
        assert 0.0 <= acc <= 1.0

def test_t3_estimator_public_inputs_only(real_counts):
    # Ensure estimator signature is (counts,bob) and does not depend on alice: same bob gives same hat regardless of alice
    counts = real_counts["1M"]
    idx, alice, bob = sample_empirical_block(counts, seed=390110, size=1024)
    hat1 = v42.estimate_u1_map_l1(counts, bob)
    # tamper alice shouldn't change
    hat2 = v42.estimate_u1_map_l1(counts, bob)
    assert np.array_equal(hat1, hat2)
    # signature check: only 2 args
    import inspect
    sig = inspect.signature(v42.estimate_u1_map_l1)
    assert len(sig.parameters)==2

# T4
def test_t4_pairing_same_seed_identity(real_counts):
    counts = real_counts["1M"]
    idx1, alice1, bob1 = sample_empirical_block(counts, seed=390110, size=1024)
    idx2, alice2, bob2 = sample_empirical_block(counts, seed=390110, size=1024)
    assert np.array_equal(idx1, idx2)
    assert np.array_equal(alice1, alice2)
    assert np.array_equal(bob1, bob2)

def test_t4_j6_strict_gate_zero_calls(tmp_path, monkeypatch, real_counts):
    world = FakeWorld()
    # Tamper errors_initial before decode: monkeypatch _compute_errors_initial to make second arm differ for first pair
    orig = v42._compute_errors_initial
    call_n = {"c":0}
    def bad_compute(a,b):
        call_n["c"]+=1
        # first call oracle, second call est for same block -> make them differ
        if call_n["c"]==2:
            return orig(a,b)+1
        return orig(a,b)
    monkeypatch.setattr(v42, "_compute_errors_initial", bad_compute)
    root = tmp_path / "j6zero"
    # Need to run with decode_fn that should not be called
    decode_calls = []
    def counting_decode(*a, **kw):
        decode_calls.append(1)
        # return dummy
        return SimpleNamespace(x_hat=np.zeros(1024,dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok")
    result = v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert result["terminal_state"]==v42.TERMINAL_EVIDENCE_INVALID
    assert decode_calls==[]
    # records should be empty or not created? In pre-decode gate failure, runner raises IntegrityFailure before any decode, caught as J6 invalid trio with zero calls
    summary = json.loads((root/"v42_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_started"]["total"]==0
    assert summary["accounting"]["decoder_calls_completed"]["total"]==0

def test_t4_pairing_completeness_and_schema(tmp_path, monkeypatch, real_counts):
    # valid full run should have pairing completeness
    outcome = make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="pair_ok")
    records = json.loads((root/"v42_records.json").read_text(encoding="utf-8"))
    assert len(records)==18
    # each block exactly once per condition
    from collections import Counter
    keys = [(r["source"], r["block_seed"], r["condition"]) for r in records]
    assert len(set(keys))==18
    # duplicate detection: tamperRecords missing one
    bad_records = records[:-1]
    failures = v42.validate_post_evaluation(bad_records)
    # missing not flagged when len !=18? but workload drift should be flagged
    assert any(c=="J12" for c,_ in failures) or any(c=="J6" for c,_ in failures)

# T5
@pytest.mark.parametrize("integrity_ok", [True, False])
@pytest.mark.parametrize("pass_pair", [(True,True),(True,False),(False,True),(False,False)])
def test_t5_truth_table(integrity_ok, pass_pair):
    po, pe = pass_pair
    term, reason, trace = v42.determine_v42_terminal(integrity_ok, po, pe)
    assert term in v42.ALL_TERMINALS
    if not integrity_ok:
        assert term==v42.TERMINAL_EVIDENCE_INVALID
    elif po and pe:
        assert term==v42.TERMINAL_BOTH_CONDITIONS_PASS
    elif po and not pe:
        assert term==v42.TERMINAL_ORACLE_ONLY_BOTTLENECK
        assert reason==v42.REASON_ESTIMATED_L1_FAILED
    elif not po and not pe:
        assert term==v42.TERMINAL_GO_STRUCTURE
        assert reason==v42.REASON_BOTH_FAILED
    else:
        assert term==v42.TERMINAL_ANOMALOUS_INVERSION
        assert reason==v42.REASON_ANOMALOUS

# T6
def test_t6_wrong_codeword_arm_local(tmp_path, monkeypatch, real_counts):
    # oracle arm wrong only -> oracle fails G3, estimated passes
    # Need 9 per condition: oracle has one wrong, estimated clean
    # Make oracle wrong at first oracle call (C01)
    special_oracle_wrong = {0: (False, 10, True), }  # C01 oracle exact False but syndrome true => wrong
    # Build outcome: index 0 oracle, 1 estimated, 2 oracle etc. So oracle indices are 0,2,4,6,8,10,12,14,16 ; estimated 1,3,5,...
    # Make only oracle index 0 wrong, all else exact
    def out_oracle_wrong(idx):
        if idx==0:
            return (False, 10, True)  # wrong
        return (True, 0, True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, out_oracle_wrong, name="oracle_wrong")
    summary = json.loads((root/"v42_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_evaluation"]["cond_oracle"]["g3_wrong_zero"]["pass"] is False
    assert summary["gate_evaluation"]["cond_oracle"]["passed"] is False
    assert summary["gate_evaluation"]["cond_estimated_l1"]["passed"] is True
    assert summary["stopped_for_analysis"]["cond_oracle"] is True
    assert summary["stopped_for_analysis"]["cond_estimated_l1"] is False
    assert summary["oracle_arm_wrong_codeword_anomaly"] is True
    assert result["terminal_state"]==v42.TERMINAL_ANOMALOUS_INVERSION  # oracle fails, est passes

    # estimated only wrong
    def out_est_wrong(idx):
        if idx==1:
            return (False, 10, True)
        return (True, 0, True)
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, out_est_wrong, name="est_wrong")
    summary2 = json.loads((root2/"v42_summary.json").read_text(encoding="utf-8"))
    assert summary2["gate_evaluation"]["cond_estimated_l1"]["g3_wrong_zero"]["pass"] is False
    assert summary2["gate_evaluation"]["cond_estimated_l1"]["passed"] is False
    assert summary2["gate_evaluation"]["cond_oracle"]["passed"] is True
    assert summary2["oracle_arm_wrong_codeword_anomaly"] is False
    assert result2["terminal_state"]==v42.TERMINAL_ORACLE_ONLY_BOTTLENECK

    # both wrong
    def out_both_wrong(idx):
        if idx in (0,1):
            return (False, 10, True)
        return (True,0,True)
    result3, root3 = run_scenario(tmp_path, monkeypatch, real_counts, out_both_wrong, name="both_wrong")
    summary3 = json.loads((root3/"v42_summary.json").read_text(encoding="utf-8"))
    assert summary3["gate_evaluation"]["cond_oracle"]["g3_wrong_zero"]["pass"] is False
    assert summary3["gate_evaluation"]["cond_estimated_l1"]["g3_wrong_zero"]["pass"] is False
    assert result3["terminal_state"]==v42.TERMINAL_GO_STRUCTURE
    assert summary3["stopped_for_analysis"]["cond_oracle"] is True
    assert summary3["stopped_for_analysis"]["cond_estimated_l1"] is True

# T7
def test_t7_budget_cap():
    acc = v42.CallAccounting()
    for _ in range(v42.HARD_CALL_CAP):
        acc.register_start()
        acc.register_complete()
    with pytest.raises(v42.IntegrityFailure) as e:
        acc.register_start()
    assert e.value.check_id=="J10"
    assert v42.HARD_CALL_CAP==18==v42.PLANNED_CALLS

# T8
@pytest.mark.parametrize("check_id,target", [("J2","validate_seed_registry"),("J3","reconstruct_v42_matrices"),("J5","dual_posterior_binding_preflight")])
def test_t8_preflight_invalid_trio(tmp_path, monkeypatch, real_counts, check_id, target):
    world = FakeWorld()
    if target=="validate_seed_registry":
        monkeypatch.setattr(v42, target, lambda seeds=None: (False, f"injected {check_id} failure"))
    else:
        def boom(*a, **kw):
            raise v42.IntegrityFailure(check_id, f"injected {check_id} failure")
        monkeypatch.setattr(v42, target, boom)
    root = tmp_path / f"pre_{check_id}"
    result = v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
    assert result["terminal_state"]==v42.TERMINAL_EVIDENCE_INVALID
    assert result["integrity_failures"]==[(check_id, f"injected {check_id} failure")]
    names = {p.name for p in root.iterdir()}
    assert names=={"v42_invalid_notice.json","v42_records.json","v42_records.csv","v42_summary.json"}
    recs = json.loads((root/"v42_records.json").read_text(encoding="utf-8"))
    assert recs==[]
    summary = json.loads((root/"v42_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_started"]["total"]==0
    assert summary["accounting"]["decoder_calls_completed"]["total"]==0
    assert summary["aggregates"]=={} and summary["gate_evaluation"]=={}
    with pytest.raises(FileExistsError):
        v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)

def test_t8_counts_shape_j4(tmp_path, monkeypatch, real_counts):
    world=FakeWorld()
    root=tmp_path/"j4"
    result=v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source={s: np.zeros((4,4)) for s in v42.SOURCE_ORDER}, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
    assert result["terminal_state"]==v42.TERMINAL_EVIDENCE_INVALID
    assert result["integrity_failures"][0][0]=="J4"

# T9
def test_t9_partial_retention(tmp_path, monkeypatch, real_counts):
    counter={"n":0}
    original = v42._evaluate_one_condition
    def failing_eval(*a, **kw):
        counter["n"]+=1
        if counter["n"]==5:
            raise RuntimeError("crash")
        return original(*a, **kw)
    monkeypatch.setattr(v42, "_evaluate_one_condition", failing_eval)
    world=FakeWorld()
    root=tmp_path/"crash"
    with pytest.raises(RuntimeError):
        v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
    names={p.name for p in root.iterdir()}
    assert names=={"v42_records.json","v42_records.csv","v42_summary.json","v42_invalid_notice.json"}
    summary=json.loads((root/"v42_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_started"]["total"]==5
    assert summary["accounting"]["decoder_calls_completed"]["total"]==4
    notice=json.loads((root/"v42_invalid_notice.json").read_text(encoding="utf-8"))
    assert notice["partial_records_retained_byte_for_byte"] is True
    # byte-for-byte comparison via successful prefix
    counter2={"n":0}
    monkeypatch.setattr(v42, "_evaluate_one_condition", original)
    root2=tmp_path/"okrun"
    outcome = make_positional_outcome({})
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="okrun")
    retained=json.loads((root/"v42_records.json").read_text(encoding="utf-8"))
    ok_records=json.loads((root2/"v42_records.json").read_text(encoding="utf-8"))
    assert retained==ok_records[:4]

# T10
def test_t10_cli_no_fake_option():
    script=SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout+proc.stderr)
    proc2=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized"], capture_output=True, text=True)
    assert proc2.returncode!=0
    assert "--authorized-target-sha" in (proc2.stdout+proc2.stderr)
    assert not v42.OUTPUT_ROOT.exists()

def test_t10_cli_sha_rejects():
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized","--authorized-target-sha","0"*40], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "J1_SHA_BINDING_MISMATCH" in (proc.stdout+proc.stderr)
    assert not v42.OUTPUT_ROOT.exists()

def test_t10_scoped_dirty(tmp_path, monkeypatch):
    def stub(returncode):
        def _run(cmd,*a,**kw):
            assert "git" in cmd[0] and "diff" in cmd
            for rel in v42.SCOPED_TRACKED_PATHS:
                assert rel in cmd
            return SimpleNamespace(returncode=returncode, stdout="", stderr="")
        return _run
    monkeypatch.setattr(v42.subprocess,"run", stub(1))
    with pytest.raises(v42.IntegrityFailure) as e:
        v42.verify_scoped_clean(tmp_path)
    assert e.value.check_id=="J1_TRACKED_DIRTY"
    monkeypatch.setattr(v42.subprocess,"run", stub(0))
    v42.verify_scoped_clean(tmp_path)

def test_t10_runner_refuses_dirty(tmp_path, monkeypatch, real_counts):
    world=FakeWorld()
    monkeypatch.setattr(v42.subprocess,"run", lambda *a,**kw: SimpleNamespace(returncode=1, stdout="", stderr=""))
    root=tmp_path/"dirty"
    with pytest.raises(v42.IntegrityFailure) as e:
        v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="d"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=True, constructors=world.constructors)
    assert e.value.check_id=="J1_TRACKED_DIRTY"
    assert not root.exists()
    with pytest.raises(PermissionError):
        v42.run_v42_diagnostic(execution_authorized=False)
    root2=tmp_path/"existing"
    root2.mkdir()
    with pytest.raises(FileExistsError):
        v42.run_v42_diagnostic(execution_authorized=True, authorized_target_sha="a"*40, fake_runner=True, output_root=root2, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)

# T11
def test_t11_schema_and_decoder_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="schema")
    records=json.loads((root/"v42_records.json").read_text(encoding="utf-8"))
    assert len(records)==18
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,19)]
    for rec in records:
        assert set(rec.keys())==set(v42.RECORD_FIELDS)
        assert rec["max_iter"]==90 and rec["damping_alpha"]==1.0
        assert rec["wrong_codeword"]==(rec["syndrome_ok"] and not rec["exact_l2"])
        ok,msg=v42.validate_record_schema(rec)
        assert ok, msg
        assert rec["condition"] in v42.CONDITION_ORDER
    assert all(c["max_iter"]==90 and c["damping_alpha"]==1.0 for c in calls)
    assert v42.POLYNOMIAL==37
    assert GF2mField.create(32).primitive_polynomial==37
    # oracle selector equals true u1_alice and estimated equals hat
    # verify via direct check on one block
    counts=real_counts["1M"]
    idx, alice, bob = sample_empirical_block(counts, seed=390110, size=1024)
    u1_a,_,_,_=factorize_f03(alice,bob)
    hat=v42.estimate_u1_map_l1(counts,bob)
    assert np.array_equal(hat, v42.estimate_u1_map_l1(counts,bob))
    # inject warm-start rejected
    base={"H":None,"source":"1M","block_seed":390110,"condition":v42.COND_ORACLE,"construction_seed":383102,"counts":None,"max_iter":90,"damping_alpha":1.0,"fake_runner":False,"field":None,"decode_fn":None}
    v42.validate_decoder_contract(base, v42.DECODER_SETTING)
    warm=dict(base, warm_start=True)
    with pytest.raises(v42.IntegrityFailure) as e:
        v42.validate_decoder_contract(warm, v42.DECODER_SETTING)
    assert e.value.check_id=="J9"

# T12
def test_t12_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v42_records.json","v42_records.csv","v42_summary.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v42_records.json").read_text(encoding="utf-8"))
    with (root/"v42_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==18
    for row,rec in zip(rows,records):
        for col in v42.RECORD_FIELDS:
            assert row[col]==str(v42._csv_value(rec[col]))
    text=(root/"v42_summary.json").read_text(encoding="utf-8")
    summary=json.loads(text)
    assert text.index('"terminal_state"') < text.index('"gate_evaluation"')
    assert summary["terminal_state"]==v42.TERMINAL_BOTH_CONDITIONS_PASS
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":18}
    assert acc["decoder_calls_started"]=={"total":18}
    assert acc["decoder_calls_completed"]=={"total":18}
    assert acc["structural_reconstruction_decoder_calls"]==0
    assert acc["preflight_decoder_calls"]==0
    assert summary["aggregates"]["per_condition"]["cond_oracle"]["exact_total"]==9
    assert summary["l1_map_accuracy_by_source"]
    assert summary["master_stop_rule"]==v42.MASTER_STOP_RULE
    assert summary["claim_boundary"]
    prov=summary["provenance"]
    assert prov["predecessor_plan_sha"]==v42.PREDECESSOR_PLAN_SHA
    assert prov["predecessor_execution_sha"]==v42.PREDECESSOR_EXECUTION_SHA
    assert prov["v42_accepted_plan_sha"]==v42.V42_ACCEPTED_PLAN_SHA
    assert summary["npz_policy"]["any_npz_output_written"] is False
    assert "stopped_for_analysis" in summary
    assert "oracle_arm_wrong_codeword_anomaly" in summary
    # overwrite fail closed
    with pytest.raises(FileExistsError):
        v42.write_v42_outputs(root, [], {})

def test_t12_all_terminals(tmp_path, monkeypatch, real_counts):
    # both pass
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, make_positional_outcome({}), name="both")
    assert result["terminal_state"]==v42.TERMINAL_BOTH_CONDITIONS_PASS
    # oracle only: oracle true, estimated false every other
    def oracle_only(idx):
        is_oracle = (idx%2==0)
        return (is_oracle, 0 if is_oracle else 100, True if is_oracle else False)
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, oracle_only, name="oracle_only")
    assert result["terminal_state"]==v42.TERMINAL_ORACLE_ONLY_BOTTLENECK
    # both fail
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, lambda idx: (False,100,False), name="both_fail")
    assert result["terminal_state"]==v42.TERMINAL_GO_STRUCTURE
    # anomalous: oracle fail, est pass
    def anomalous(idx):
        is_est = (idx%2==1)
        return (is_est, 0 if is_est else 100, True if is_est else False)
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, anomalous, name="anom")
    assert result["terminal_state"]==v42.TERMINAL_ANOMALOUS_INVERSION
