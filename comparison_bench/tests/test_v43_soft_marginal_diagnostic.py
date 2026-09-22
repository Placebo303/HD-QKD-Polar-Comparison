"""Focused V43P0 tests (T1-T12) for the soft-marginal diagnostic runner.

All tests are fake-runner / stub-decode or decoder-free. No production
decoder is invoked, the official V43 output root is never created.
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
from comparison_bench.formal_ir import v43_soft_marginal_diagnostic as v43

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v43_soft_marginal_diagnostic.py"

INITIAL_BY_BLOCK = {
    390113: 250, 390114: 261, 390115: 272,
    390213: 255, 390214: 266, 390215: 277,
    390313: 249, 390314: 258, 390315: 267,
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
        for source in v43.SOURCE_ORDER:
            for seed in v43.CONSTRUCTION_SEEDS["lane_c"][source]:
                self.constructors["lane_c"](source=source, seed=seed)
        records: list[dict] = []
        for source in v43.SOURCE_ORDER:
            for seed in (921001, 921002, 921003):
                records.append({"lane": "lane_a", "source": source, "construction_seed": seed, "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"})
            for seed in (922001, 922002, 922003):
                records.append({"lane": "lane_b", "source": source, "construction_seed": seed, "matrix_id": f"lane_b_{source}_s{seed}", "shape": "[4, 1024]"})
        for mid, met in self.metrics_by_id.items():
            records.append(dict(met))
        for i in range(6):
            records.append({"lane": "lane_c", "source": "1M", "construction_seed": 999000+i, "matrix_id": f"lane_c_1M_s{999000+i}", "shape": "[4, 1024]", "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True, "position_permutations": [[0]]})
        records = records[:27]
        for src in v43.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v43._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path


def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    counter = {"n": 0}
    original_eval = v43._evaluate_one_condition
    def _patched_eval(matrix, source, block_seed, condition, counts, bob, u1_selector, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec, soft=False):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "condition": condition, "block_seed": block_seed})
        vals = fake_outcome(idx)
        if len(vals)==2:
            exact, final = vals
            syn_ok = bool(exact)
        else:
            exact, final, syn_ok = vals
        return {"condition": condition, "source": source, "block_seed": block_seed, "construction_seed": spec["construction_seed"], "matrix_id": spec["matrix_id"], "errors_initial": int(errors_initial), "errors_final": int(final), "exact_l2": bool(exact), "syndrome_ok": bool(syn_ok), "iterations": 5 if exact else 90, "status": "converged_exact" if exact else "max_iter", "runtime_s": 0.001}
    monkeypatch.setattr(v43, "_evaluate_one_condition", _patched_eval)
    world = FakeWorld()
    root = tmp_path / name
    result = v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# T1
def test_t1_registry_accepts_frozen_nine():
    ok, msg = v43.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    assert set(v43.NEW_BLOCK_SEEDS.keys()) == set(v43.SOURCE_ORDER)
    flat = [s for src in v43.SOURCE_ORDER for s in v43.NEW_BLOCK_SEEDS[src]]
    assert flat == [390113,390114,390115,390213,390214,390215,390313,390314,390315]

def _reg_with(source, repl):
    reg = {src: list(seeds) for src,seeds in v43.NEW_BLOCK_SEEDS.items()}
    reg[source]=repl
    return reg

@pytest.mark.parametrize("bad_reg", [
    _reg_with("1M", [390113,390113,390114]),
    _reg_with("1p5M", [390213,390214]),
    _reg_with("2M", [390313,390314,390315,390316]),
    _reg_with("1M", [360101,390114,390115]),
    _reg_with("1p5M", [390201,390214,390215]),
    _reg_with("2M", [390306,390314,390315]),
    _reg_with("1M", [390107,390114,390115]),
    {"1M":[390113],"1p5M":[390213]},
])
def test_t1_registry_rejects_drift(bad_reg):
    ok,_ = v43.validate_seed_registry(bad_reg)
    assert not ok

@pytest.mark.parametrize("probe_seed", [390106,390206,390306])
def test_t1_each_v40_probe_forbidden(probe_seed):
    reg = {src: list(seeds) for src,seeds in v43.NEW_BLOCK_SEEDS.items()}
    reg["1M"][0]=probe_seed
    ok,msg = v43.validate_seed_registry(reg)
    assert not ok and str(probe_seed) in msg

@pytest.mark.parametrize("v41seed", [390107,390108,390109,390207,390208,390209,390307,390308,390309])
def test_t1_each_v41_seed_forbidden(v41seed):
    reg = {src: list(seeds) for src,seeds in v43.NEW_BLOCK_SEEDS.items()}
    ok,_ = v43.validate_seed_registry({**reg, "1M": [v41seed,390114,390115]})
    assert not ok

@pytest.mark.parametrize("v42seed", [390110,390111,390112,390210,390211,390212,390310,390311,390312])
def test_t1_each_v42_seed_forbidden(v42seed):
    reg = {src: list(seeds) for src,seeds in v43.NEW_BLOCK_SEEDS.items()}
    ok,_ = v43.validate_seed_registry({**reg, "2M": [390313,390314,v42seed]})
    assert not ok

# T2
def test_t2_reconstruction_deterministic(tmp_path, monkeypatch):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    first = v43.reconstruct_v43_matrices(authority, field=field, constructors=world.constructors)
    second = v43.reconstruct_v43_matrices(authority, field=field, constructors=world.constructors)
    assert set(first.keys()) == set(second.keys()) == set(v43.RECONSTRUCTION_KEYS)
    for k in v43.RECONSTRUCTION_KEYS:
        assert np.array_equal(first[k][0], second[k][0])
        assert first[k][1]==second[k][1]
    for k in v43.RECONSTRUCTION_KEYS:
        assert "position_permutations" in first[k][1]
    ids = sorted(f"lane_c_{src}_s{v43._rep_seed('lane_c', src)}" for _,src in v43.RECONSTRUCTION_KEYS)
    assert sorted(v43.FROZEN_REPRESENTATIVE_MATRIX_IDS)==ids

def test_t2_reconstruction_detects_drift(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"]=="lane_c_1M_s383102")
    victim["rank_GF32"]=int(victim["rank_GF32"])-1
    bad = tmp_path/"bad.json"
    bad.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v43.IntegrityFailure) as e:
        v43.reconstruct_v43_matrices(bad, field=field, constructors=world.constructors)
    assert e.value.check_id=="J3"
    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"]=="lane_c_1M_s383102")
    victim["position_permutations"]=[[5,5],[5,5]]
    bad2 = tmp_path/"bad2.json"
    bad2.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v43.IntegrityFailure) as e2:
        v43.reconstruct_v43_matrices(bad2, field=field, constructors=world.constructors)
    assert e2.value.check_id=="J3"
    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"]=="lane_c_1M_s383102")
    victim["lane"]="lane_b"
    bad3 = tmp_path/"bad3.json"
    bad3.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v43.IntegrityFailure) as e3:
        v43.reconstruct_v43_matrices(bad3, field=field, constructors=world.constructors)
    assert e3.value.check_id=="J3"
    with pytest.raises(v43.IntegrityFailure) as e4:
        v43.reconstruct_v43_matrices(tmp_path/"x.npz", field=field, constructors=world.constructors)
    assert e4.value.check_id=="J8"

# T3
def test_t3_sentinels_pass(real_counts):
    res = v43.dual_posterior_binding_preflight(real_counts)
    assert set(res.keys())==set(v43.SOURCE_ORDER)
    for src,chk in res.items():
        assert chk["probe_block_seed"]==v43.PREFLIGHT_BLOCK_SEEDS[src]
        assert chk["bob_gt_31"] is True
        assert chk["captured_equals_bob"] is True
        assert chk["corrected_equals_direct"] is True
        assert chk["corrected_differs_u2bob_arraywise"] is True
        assert chk["corrected_differs_u2bob_maxabs"] is True
        assert chk["argmax_divergence"] is True
        assert chk["carrier_identity_soft"] is True
        assert chk["arms_differ"] is True
        assert chk["soft_marginal_normalization_ok"] is True
        assert chk["soft_marginal_public_inputs"] is True

def test_t3_tampered_u2bob_detected(real_counts):
    def mutating(cnt,b,u1):
        b[0] = (int(b[0])+1)%32
        return get_conditional_posterior_l2(cnt,b,u1)
    with pytest.raises(v43.IntegrityFailure) as exc:
        v43.dual_posterior_binding_preflight(real_counts, posterior_fn=mutating)
    assert exc.value.check_id=="J5"

def test_t3_soft_estimator_rejects_alice_dep(real_counts):
    # alice-dependent soft variant with 3 args should be rejected via public inputs check
    def alice_dependent(counts, bob, alice):  # 3 args -> should fail soft_marginal_public_inputs
        return v43.get_soft_marginal_posterior_l2(counts, bob)
    with pytest.raises(v43.IntegrityFailure) as exc:
        v43.dual_posterior_binding_preflight(real_counts, soft_posterior_fn=alice_dependent)
    assert exc.value.check_id=="J5"

def test_t3_carrier_identity_soft_spy(real_counts):
    # replace soft prior with oracle-like (same as oracle) -> arms_differ fails
    def oracle_like(counts, bob):
        # return oracle posterior with dummy u1=0
        return get_conditional_posterior_l2(counts, bob, np.zeros_like(bob))
    with pytest.raises(v43.IntegrityFailure) as exc:
        # need oracle posterior to be different from this oracle_like on at least one source; if by chance equal then test would not fail, but oracle_like uses u1=0 vs true u1_alice which varies, so differs
        v43.dual_posterior_binding_preflight(real_counts, soft_posterior_fn=oracle_like)
    # Could be carrier_identity_soft fails or arms_differ? Both are J5
    assert exc.value.check_id=="J5"

def test_t3_soft_normalization_fail(real_counts):
    def bad_norm(counts, bob):
        p = v43.get_soft_marginal_posterior_l2(counts, bob)
        p[:] = p * 2  # break normalization
        return p
    with pytest.raises(v43.IntegrityFailure) as exc:
        v43.dual_posterior_binding_preflight(real_counts, soft_posterior_fn=bad_norm)
    assert exc.value.check_id=="J5"

def test_t3_soft_marginal_posterior_binding(real_counts):
    for src in v43.SOURCE_ORDER:
        counts = real_counts[src]
        idx, alice, bob = sample_empirical_block(counts, seed=v43.PREFLIGHT_BLOCK_SEEDS[src], size=1024)
        p = v43.get_soft_marginal_posterior_l2(counts, bob)
        assert p.shape == (1024, 32)
        assert np.allclose(p.sum(axis=1), 1.0, atol=1e-9)
        # each row should be derived from counts sum over u1
        # verify manual marginal
        arr = counts
        reshaped = arr.reshape(32,32,1024)
        marginal = reshaped.sum(axis=0)
        col_sums = marginal.sum(axis=0)
        p_cols = marginal / col_sums[None, :]
        manual = p_cols[:, bob].T
        manual = np.maximum(manual, 1e-15)
        manual = manual / manual.sum(axis=1, keepdims=True)
        assert np.allclose(p, manual, atol=1e-9)

# T4
def test_t4_pairing_same_seed_identity(real_counts):
    counts = real_counts["1M"]
    idx1, alice1, bob1 = sample_empirical_block(counts, seed=390113, size=1024)
    idx2, alice2, bob2 = sample_empirical_block(counts, seed=390113, size=1024)
    assert np.array_equal(idx1, idx2)
    assert np.array_equal(alice1, alice2)
    assert np.array_equal(bob1, bob2)

def test_t4_j6_strict_gate_zero_calls(tmp_path, monkeypatch, real_counts):
    world = FakeWorld()
    orig = v43._compute_errors_initial
    call_n = {"c":0}
    def bad_compute(a,b):
        call_n["c"]+=1
        if call_n["c"]==2:
            return orig(a,b)+1
        return orig(a,b)
    monkeypatch.setattr(v43, "_compute_errors_initial", bad_compute)
    root = tmp_path / "j6zero"
    decode_calls = []
    def counting_decode(*a, **kw):
        decode_calls.append(1)
        return SimpleNamespace(x_hat=np.zeros(1024,dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok")
    result = v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert result["terminal_state"]==v43.TERMINAL_EVIDENCE_INVALID
    assert decode_calls==[]
    summary = json.loads((root/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_started"]["total"]==0
    assert summary["accounting"]["decoder_calls_completed"]["total"]==0

def test_t4_pairing_completeness_and_schema(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="pair_ok")
    records = json.loads((root/"v43_records.json").read_text(encoding="utf-8"))
    assert len(records)==18
    from collections import Counter
    keys = [(r["source"], r["block_seed"], r["condition"]) for r in records]
    assert len(set(keys))==18
    bad_records = records[:-1]
    failures = v43.validate_post_evaluation(bad_records)
    assert any(c=="J12" for c,_ in failures) or any(c=="J6" for c,_ in failures)
    # cross condition outcome difference should NOT be integrity failure
    # paired outcomes differ but still valid
    assert not any("outcome" in msg for _,msg in failures)

# T5
@pytest.mark.parametrize("integrity_ok", [True, False])
@pytest.mark.parametrize("pass_pair", [(True,True),(True,False),(False,True),(False,False)])
def test_t5_truth_table(integrity_ok, pass_pair):
    po, ps = pass_pair
    term, reason, trace = v43.determine_v43_terminal(integrity_ok, po, ps)
    assert term in v43.ALL_TERMINALS
    if not integrity_ok:
        assert term==v43.TERMINAL_EVIDENCE_INVALID
    elif po and ps:
        assert term==v43.TERMINAL_BOTH_CONDITIONS_PASS
    elif po and not ps:
        assert term==v43.TERMINAL_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK
        assert reason==v43.REASON_SOFT_MARGINAL_FAILED
    elif not po and not ps:
        assert term==v43.TERMINAL_GO_STRUCTURE
        assert reason==v43.REASON_BOTH_FAILED
    else:
        assert term==v43.TERMINAL_ANOMALOUS_INVERSION
        assert reason==v43.REASON_ANOMALOUS

def test_t5_needs_flag_orthogonal(tmp_path, monkeypatch, real_counts):
    # oracle exact on 1p5M <2 should set needs_1p5m_structure_branch true regardless of terminal
    # make oracle 1p5M exact only 1/3
    def outcome(idx):
        # idx mapping: C01 C02 1M 113, C03 C04 114, C05 C06 115, C07 C08 1p5M 213, C09 C10 214, C11 C12 215, C13..2M
        # oracle indices even: 0,2,4,6,8,10,12,14,16
        if idx in (6,):  # only one oracle 1p5M pass
            return (True,0,True)
        if idx %2==0:
            return (False,10,False)
        # soft arms: make them fail too to get both fail terminal
        return (False,10,False)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="needs_true")
    summary = json.loads((root/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary["needs_1p5m_structure_branch"] is True
    # make 2/3 exactly -> flag false
    def outcome2(idx):
        if idx in (6,8):
            return (True,0,True)
        if idx%2==0:
            return (False,10,False)
        return (False,10,False)
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, outcome2, name="needs_false")
    summary2 = json.loads((root2/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary2["needs_1p5m_structure_branch"] is False

# T6
def test_t6_wrong_codeword_arm_local(tmp_path, monkeypatch, real_counts):
    def out_oracle_wrong(idx):
        if idx==0:
            return (False, 10, True)
        return (True, 0, True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, out_oracle_wrong, name="oracle_wrong")
    summary = json.loads((root/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_evaluation"]["cond_oracle"]["g3_wrong_zero"]["pass"] is False
    assert summary["gate_evaluation"]["cond_oracle"]["passed"] is False
    assert summary["gate_evaluation"]["cond_soft_marginal"]["passed"] is True
    assert summary["stopped_for_analysis"]["cond_oracle"] is True
    assert summary["stopped_for_analysis"]["cond_soft_marginal"] is False
    assert summary["oracle_arm_wrong_codeword_anomaly"] is True
    assert result["terminal_state"]==v43.TERMINAL_ANOMALOUS_INVERSION

    def out_soft_wrong(idx):
        if idx==1:
            return (False, 10, True)
        return (True, 0, True)
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, out_soft_wrong, name="soft_wrong")
    summary2 = json.loads((root2/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary2["gate_evaluation"]["cond_soft_marginal"]["g3_wrong_zero"]["pass"] is False
    assert summary2["gate_evaluation"]["cond_soft_marginal"]["passed"] is False
    assert summary2["gate_evaluation"]["cond_oracle"]["passed"] is True
    assert summary2["oracle_arm_wrong_codeword_anomaly"] is False
    assert result2["terminal_state"]==v43.TERMINAL_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK

    def out_both_wrong(idx):
        if idx in (0,1):
            return (False, 10, True)
        return (True,0,True)
    result3, root3 = run_scenario(tmp_path, monkeypatch, real_counts, out_both_wrong, name="both_wrong")
    summary3 = json.loads((root3/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary3["gate_evaluation"]["cond_oracle"]["g3_wrong_zero"]["pass"] is False
    assert summary3["gate_evaluation"]["cond_soft_marginal"]["g3_wrong_zero"]["pass"] is False
    assert result3["terminal_state"]==v43.TERMINAL_GO_STRUCTURE
    assert summary3["stopped_for_analysis"]["cond_oracle"] is True
    assert summary3["stopped_for_analysis"]["cond_soft_marginal"] is True

# T7
def test_t7_budget_cap():
    acc = v43.CallAccounting()
    for _ in range(v43.HARD_CALL_CAP):
        acc.register_start()
        acc.register_complete()
    with pytest.raises(v43.IntegrityFailure) as e:
        acc.register_start()
    assert e.value.check_id=="J10"
    assert v43.HARD_CALL_CAP==18==v43.PLANNED_CALLS

# T8
@pytest.mark.parametrize("check_id,target", [("J2","validate_seed_registry"),("J3","reconstruct_v43_matrices"),("J5","dual_posterior_binding_preflight")])
def test_t8_preflight_invalid_trio(tmp_path, monkeypatch, real_counts, check_id, target):
    world = FakeWorld()
    if target=="validate_seed_registry":
        monkeypatch.setattr(v43, target, lambda seeds=None: (False, f"injected {check_id} failure"))
    else:
        def boom(*a, **kw):
            raise v43.IntegrityFailure(check_id, f"injected {check_id} failure")
        monkeypatch.setattr(v43, target, boom)
    root = tmp_path / f"pre_{check_id}"
    result = v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
    assert result["terminal_state"]==v43.TERMINAL_EVIDENCE_INVALID
    assert result["integrity_failures"]==[(check_id, f"injected {check_id} failure")]
    names = {p.name for p in root.iterdir()}
    assert names=={"v43_invalid_notice.json","v43_records.json","v43_records.csv","v43_summary.json"}
    recs = json.loads((root/"v43_records.json").read_text(encoding="utf-8"))
    assert recs==[]
    summary = json.loads((root/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_started"]["total"]==0
    assert summary["accounting"]["decoder_calls_completed"]["total"]==0
    assert summary["aggregates"]=={} and summary["gate_evaluation"]=={}
    with pytest.raises(FileExistsError):
        v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)

def test_t8_counts_shape_j4(tmp_path, monkeypatch, real_counts):
    world=FakeWorld()
    root=tmp_path/"j4"
    result=v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source={s: np.zeros((4,4)) for s in v43.SOURCE_ORDER}, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
    assert result["terminal_state"]==v43.TERMINAL_EVIDENCE_INVALID
    assert result["integrity_failures"][0][0]=="J4"

# T9
def test_t9_partial_retention(tmp_path, monkeypatch, real_counts):
    counter={"n":0}
    original = v43._evaluate_one_condition
    def failing_eval(*a, **kw):
        counter["n"]+=1
        if counter["n"]==5:
            raise RuntimeError("crash")
        return original(*a, **kw)
    monkeypatch.setattr(v43, "_evaluate_one_condition", failing_eval)
    world=FakeWorld()
    root=tmp_path/"crash"
    with pytest.raises(RuntimeError):
        v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
    names={p.name for p in root.iterdir()}
    assert names=={"v43_records.json","v43_records.csv","v43_summary.json","v43_invalid_notice.json"}
    summary=json.loads((root/"v43_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_started"]["total"]==5
    assert summary["accounting"]["decoder_calls_completed"]["total"]==4
    notice=json.loads((root/"v43_invalid_notice.json").read_text(encoding="utf-8"))
    assert notice["partial_records_retained_byte_for_byte"] is True
    counter2={"n":0}
    monkeypatch.setattr(v43, "_evaluate_one_condition", original)
    outcome = make_positional_outcome({})
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="okrun")
    retained=json.loads((root/"v43_records.json").read_text(encoding="utf-8"))
    ok_records=json.loads((root2/"v43_records.json").read_text(encoding="utf-8"))
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
    assert not v43.OUTPUT_ROOT.exists()

def test_t10_cli_sha_rejects():
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized","--authorized-target-sha","0"*40], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "J1_SHA_BINDING_MISMATCH" in (proc.stdout+proc.stderr)
    assert not v43.OUTPUT_ROOT.exists()

def test_t10_scoped_dirty(tmp_path, monkeypatch):
    def stub(returncode):
        def _run(cmd,*a,**kw):
            assert "git" in cmd[0] and "diff" in cmd
            for rel in v43.SCOPED_TRACKED_PATHS:
                assert rel in cmd
            return SimpleNamespace(returncode=returncode, stdout="", stderr="")
        return _run
    monkeypatch.setattr(v43.subprocess,"run", stub(1))
    with pytest.raises(v43.IntegrityFailure) as e:
        v43.verify_scoped_clean(tmp_path)
    assert e.value.check_id=="J1_TRACKED_DIRTY"
    monkeypatch.setattr(v43.subprocess,"run", stub(0))
    v43.verify_scoped_clean(tmp_path)

def test_t10_runner_refuses_dirty(tmp_path, monkeypatch, real_counts):
    world=FakeWorld()
    monkeypatch.setattr(v43.subprocess,"run", lambda *a,**kw: SimpleNamespace(returncode=1, stdout="", stderr=""))
    root=tmp_path/"dirty"
    with pytest.raises(v43.IntegrityFailure) as e:
        v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="d"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=True, constructors=world.constructors)
    assert e.value.check_id=="J1_TRACKED_DIRTY"
    assert not root.exists()
    with pytest.raises(PermissionError):
        v43.run_v43_diagnostic(execution_authorized=False)
    root2=tmp_path/"existing"
    root2.mkdir()
    with pytest.raises(FileExistsError):
        v43.run_v43_diagnostic(execution_authorized=True, authorized_target_sha="a"*40, fake_runner=True, output_root=root2, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)

# T11
def test_t11_schema_and_decoder_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="schema")
    records=json.loads((root/"v43_records.json").read_text(encoding="utf-8"))
    assert len(records)==18
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,19)]
    for rec in records:
        assert set(rec.keys())==set(v43.RECORD_FIELDS)
        assert rec["max_iter"]==90 and rec["damping_alpha"]==1.0
        assert rec["wrong_codeword"]==(rec["syndrome_ok"] and not rec["exact_l2"])
        ok,msg=v43.validate_record_schema(rec)
        assert ok, msg
        assert rec["condition"] in v43.CONDITION_ORDER
    assert all(c["max_iter"]==90 and c["damping_alpha"]==1.0 for c in calls)
    assert v43.POLYNOMIAL==37
    assert GF2mField.create(32).primitive_polynomial==37
    # oracle selector equals true u1_alice and soft selector equals marginal
    counts=real_counts["1M"]
    idx, alice, bob = sample_empirical_block(counts, seed=390113, size=1024)
    u1_a,_,_,_=factorize_f03(alice,bob)
    # verify soft posterior matches frozen definition
    p_soft = v43.get_soft_marginal_posterior_l2(counts, bob)
    assert p_soft.shape==(1024,32)
    assert np.allclose(p_soft.sum(axis=1), 1.0, atol=1e-9)
    # inject warm-start rejected
    base={"H":None,"source":"1M","block_seed":390113,"condition":v43.COND_ORACLE,"construction_seed":383102,"counts":None,"max_iter":90,"damping_alpha":1.0,"fake_runner":False,"field":None,"decode_fn":None}
    v43.validate_decoder_contract(base, v43.DECODER_SETTING)
    warm=dict(base, warm_start=True)
    with pytest.raises(v43.IntegrityFailure) as e:
        v43.validate_decoder_contract(warm, v43.DECODER_SETTING)
    assert e.value.check_id=="J9"

# T12
def test_t12_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v43_records.json","v43_records.csv","v43_summary.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v43_records.json").read_text(encoding="utf-8"))
    with (root/"v43_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==18
    for row,rec in zip(rows,records):
        for col in v43.RECORD_FIELDS:
            assert row[col]==str(v43._csv_value(rec[col]))
    text=(root/"v43_summary.json").read_text(encoding="utf-8")
    summary=json.loads(text)
    assert text.index('"terminal_state"') < text.index('"gate_evaluation"')
    assert summary["terminal_state"]==v43.TERMINAL_BOTH_CONDITIONS_PASS
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":18}
    assert acc["decoder_calls_started"]=={"total":18}
    assert acc["decoder_calls_completed"]=={"total":18}
    assert acc["structural_reconstruction_decoder_calls"]==0
    assert acc["preflight_decoder_calls"]==0
    assert summary["aggregates"]["per_condition"]["cond_oracle"]["exact_total"]==9
    assert summary["soft_marginal_diagnostics_by_source"]
    assert summary["master_stop_rule"]==v43.MASTER_STOP_RULE
    assert summary["claim_boundary"]
    prov=summary["provenance"]
    assert prov["predecessor_plan_sha"]==v43.PREDECESSOR_PLAN_SHA
    assert prov["predecessor_execution_sha"]==v43.PREDECESSOR_EXECUTION_SHA
    assert prov["predecessor_result_sha"]==v43.PREDECESSOR_RESULT_SHA
    assert summary["npz_policy"]["any_npz_output_written"] is False
    assert "stopped_for_analysis" in summary
    assert "oracle_arm_wrong_codeword_anomaly" in summary
    assert "needs_1p5m_structure_branch" in summary
    # orthogonal
    oracle_1p5 = summary["gate_evaluation"]["cond_oracle"]["g2_every_source_ge_2_of_3"]["exact_by_source"]["1p5M"]
    assert summary["needs_1p5m_structure_branch"] == (oracle_1p5 < 2)
    with pytest.raises(FileExistsError):
        v43.write_v43_outputs(root, [], {})

def test_t12_all_terminals(tmp_path, monkeypatch, real_counts):
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, make_positional_outcome({}), name="both")
    assert result["terminal_state"]==v43.TERMINAL_BOTH_CONDITIONS_PASS
    def oracle_only(idx):
        is_oracle = (idx%2==0)
        return (is_oracle, 0 if is_oracle else 100, True if is_oracle else False)
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, oracle_only, name="oracle_only")
    assert result["terminal_state"]==v43.TERMINAL_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, lambda idx: (False,100,False), name="both_fail")
    assert result["terminal_state"]==v43.TERMINAL_GO_STRUCTURE
    def anomalous(idx):
        is_soft = (idx%2==1)
        return (is_soft, 0 if is_soft else 100, True if is_soft else False)
    result,_ = run_scenario(tmp_path, monkeypatch, real_counts, anomalous, name="anom")
    assert result["terminal_state"]==v43.TERMINAL_ANOMALOUS_INVERSION
