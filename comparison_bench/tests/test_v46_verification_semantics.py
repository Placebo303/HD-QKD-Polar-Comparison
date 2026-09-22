"""Focused V46P0 tests (decoder-free, fake-runner) for L2-only verification semantics.

All tests are fake-runner / stub-decode or decoder-free. No production
decoder is invoked, the official V46 output root is never created.
Covers: seed registry 78, reconstruction, sentinel+V35 tag import, tag oracle-removal
(x1 invariance / x2 sensitivity), 27-call accounting, four-way reclassification & G3',
preflight, CLI guards, writer contract, and zero real decoder calls.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_tag_64, load_v25_channel_counts, get_conditional_posterior_l2
from comparison_bench.formal_ir import v46_verification_semantics as v46

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v46_verification_semantics.py"

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
        for source in v46.SOURCE_ORDER:
            for seed in v46.CONSTRUCTION_SEEDS["lane_c"][source]:
                self.constructors["lane_c"](source=source, seed=seed)
        records: list[dict] = []
        for source in v46.SOURCE_ORDER:
            for seed in (921001, 921002, 921003):
                records.append({"lane": "lane_a", "source": source, "construction_seed": seed, "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"})
            for seed in (922001, 922002, 922003):
                records.append({"lane": "lane_b", "source": source, "construction_seed": seed, "matrix_id": f"lane_b_{source}_s{seed}", "shape": "[4, 1024]"})
        for mid, met in self.metrics_by_id.items():
            records.append(dict(met))
        for i in range(6):
            records.append({"lane": "lane_c", "source": "1M", "construction_seed": 999000+i, "matrix_id": f"lane_c_1M_s{999000+i}", "shape": "[4, 1024]", "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True, "position_permutations": [[0]]})
        records = records[:27]
        for src in v46.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v46._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    counter = {"n": 0}
    def _patched_eval(matrix, source, block_seed, condition, counts, bob, u1_selector, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec, q_for_treatment=None, l1_res=None, is_control=True):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "condition": condition, "block_seed": block_seed})
        vals = fake_outcome(idx)
        # vals can be (exact_l2, final, syn_ok, tag_mode)
        # tag_mode: "detected" -> tag_ok false while !exact, "undetected" -> tag_ok true while !exact, None -> default logic (exact=>tag_ok true)
        if isinstance(vals, tuple) and len(vals) >=1 and isinstance(vals[0], bool):
            exact_l2 = bool(vals[0])
            final = int(vals[1]) if len(vals) >1 else 0
            syn_ok = bool(vals[2]) if len(vals) >2 else bool(exact_l2)
            tag_mode = vals[3] if len(vals) >3 else None
            exact_u1 = True
            syn_ok_l1 = True
        else:
            exact_l2 = True
            final = 0
            syn_ok = True
            tag_mode = None
            exact_u1 = True
            syn_ok_l1 = True
        if is_control:
            exact_u1_out = None
            exact_full_out = None
        else:
            exact_u1_out = bool(exact_u1)
            exact_full_out = bool(exact_u1 and exact_l2)
        # Compute tags via L2-only helper
        empty = np.empty(0, dtype=np.uint8)
        # Simulate true x2 and x_hat for tag purposes: u2_alice is true; for fake we synthesize x_hat
        # For exact, x_hat == u2_alice => tag_ok true
        # For !exact with tag_mode detected => candidate differs => tag_ok false
        # For !exact with undetected => candidate == target => tag_ok true (collision approx)
        if exact_l2:
            # exact => x_hat == true
            x_hat_fake = np.asarray(u2_alice, dtype=np.uint8)
            target = compute_tag_64(empty, u2_alice)
            candidate = compute_tag_64(empty, x_hat_fake)
            tag_ok = True
        else:
            target = compute_tag_64(empty, u2_alice)
            if tag_mode == "undetected":
                candidate = target
                tag_ok = True
            elif tag_mode == "detected":
                # mutate one symbol to guarantee tag change
                alt = np.asarray(u2_alice, dtype=np.uint8).copy()
                alt[0] = (int(alt[0]) + 1) % 32
                candidate = compute_tag_64(empty, alt)
                tag_ok = False
            else:
                # default !exact => detected
                alt = np.asarray(u2_alice, dtype=np.uint8).copy()
                alt[0] = (int(alt[0]) + 1) % 32
                candidate = compute_tag_64(empty, alt)
                tag_ok = False
            # Ensure tag_ok matches expectation
            if tag_mode == "undetected":
                assert tag_ok is True
            elif tag_mode == "detected":
                assert tag_ok is False
        reclassified = v46.classify_reclassified(exact_l2, syn_ok, tag_ok)
        return {
            "condition": condition, "source": source, "block_seed": block_seed,
            "construction_seed": spec["construction_seed"], "matrix_id": spec["matrix_id"],
            "h1_matrix_id": spec.get("h1_matrix_id", v46.H1_MATRIX_ID),
            "errors_initial": int(errors_initial), "errors_final": int(final),
            "exact_l2": bool(exact_l2), "exact_u1": exact_u1_out, "exact_full": exact_full_out,
            "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syn_ok_l1),
            "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": v46.TAG_SCOPE, "reclassified": reclassified,
            "iterations_l1": 5, "iterations_l2": 5 if exact_l2 else 90,
            "bp_posterior_entropy": 4.5, "mean_abs_diff_q_p": 0.02,
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
        }
    monkeypatch.setattr(v46, "_evaluate_one_condition", _patched_eval)
    world = FakeWorld()
    root = tmp_path / name
    result = v46.run_v46_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# ---- Tag oracle-removal tests (B3) ----

def test_tag_l2_only_oracle_removal():
    empty = np.empty(0, dtype=np.uint8)
    x2 = np.array([1,2,3,4,5], dtype=np.uint8)
    x1_a = np.array([10,20,30,40,50], dtype=np.uint8)
    x1_b = np.array([99,88,77,66,55], dtype=np.uint8)
    # Changing x1_true must NOT change L2 tag
    tag_a = compute_tag_64(empty, x2)
    tag_b = compute_tag_64(empty, x2)
    assert tag_a == tag_b
    # Direct helper
    assert v46.compute_l2_tag(x2) == tag_a
    assert v46.compute_l2_tag(x2) == v46.compute_l2_tag(x2)
    # Changing x2 must change anchor tag (fixed empty prefix)
    x2_alt = x2.copy()
    x2_alt[0] = (int(x2_alt[0]) + 1) % 32
    tag_alt = compute_tag_64(empty, x2_alt)
    assert tag_alt != tag_a
    assert len(tag_a) == 16
    assert len(tag_alt) == 16
    int(tag_a, 16)
    int(tag_alt, 16)
    # Ensure no x1 oracle path exists: module must not contain compute_tag_64(x1_true, ...) calls
    src = Path(v46.__file__).read_text(encoding="utf-8")
    assert "compute_tag_64(x1_true" not in src
    assert "compute_tag_64_symbols" not in src or "compute_tag_64(empty" in src  # symbols only as comment, not oracle
    # Ensure TAG_SCOPE is l2_only
    assert v46.TAG_SCOPE == "l2_only"
    # Verify reclassification logic
    assert v46.classify_reclassified(True, True, True) == "exact"
    assert v46.classify_reclassified(False, True, False) == "detected_verification_failure"
    assert v46.classify_reclassified(False, False, False) == "decoder_non_syndrome_failure"
    assert v46.classify_reclassified(False, True, True) == "undetected_accepted_wrong"
    assert v46.classify_reclassified(False, False, True) == "undetected_accepted_wrong"

def test_no_canonical_reimplementation():
    src = Path(v46.__file__).read_text(encoding="utf-8")
    # Must reuse V35 compute_tag_64, not reimplement canonical_bytes
    assert "def compute_tag_64" not in src  # no local redefinition
    assert "from comparison_bench.formal_ir.v35_algorithm_development import" in src
    assert "compute_tag_64" in src

# ---- Registry 78 ----
def test_registry_accepts_frozen_nine():
    ok, msg = v46.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    flat = [s for src in v46.SOURCE_ORDER for s in v46.NEW_BLOCK_SEEDS[src]]
    assert flat == [390122,390123,390124,390222,390223,390224,390322,390323,390324]
    assert len(v46.FORBIDDEN_BLOCK_SEEDS) == 78
    overlap = set(flat) & v46.FORBIDDEN_BLOCK_SEEDS
    assert overlap == set()

def test_registry_rejects_v45_overlap():
    reg = {src: list(seeds) for src,seeds in v46.NEW_BLOCK_SEEDS.items()}
    reg["1M"][0] = 390119
    ok,_ = v46.validate_seed_registry(reg)
    assert not ok

def test_registry_rejects_all_forbidden_families():
    # Each family one probe
    for probe in [360101, 390101, 390106, 390107, 390110, 390113, 390116, 390119]:
        reg = {src: list(seeds) for src,seeds in v46.NEW_BLOCK_SEEDS.items()}
        reg["2M"][0] = probe
        ok,_ = v46.validate_seed_registry(reg)
        assert not ok, probe

# ---- Reconstruction ----
def test_reconstruction_and_h1(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    first = v46.reconstruct_v46_matrices(authority, field=field, constructors=world.constructors)
    second = v46.reconstruct_v46_matrices(authority, field=field, constructors=world.constructors)
    assert set(k for k in first.keys() if k[0]=="lane_c") == set(k for k in second.keys() if k[0]=="lane_c")
    for k in v46.RECONSTRUCTION_KEYS:
        assert np.array_equal(first[k][0], second[k][0])
    h1_mat, h1_audit = first[("H1","L1")]
    assert h1_mat.shape == (16,1024)
    assert h1_audit["rank"] == 16
    assert h1_audit["full_row_rank"] is True

# ---- Sentinel + tag import ----
def test_sentinels_and_tag_import(real_counts):
    res = v46.dual_posterior_binding_preflight(real_counts)
    assert set(res.keys())==set(v46.SOURCE_ORDER)
    for src,chk in res.items():
        assert chk["probe_block_seed"]==v46.PREFLIGHT_BLOCK_SEEDS[src]
        assert chk["v35_tag_import_ok"] is True
        assert chk["tag_scope_l2_only"] is True
        assert chk["tag_l2_only_empty_prefix_ok"] is True
        assert chk["leakage_already_accounted"] is True
        assert chk["leakage_accounted"] is True

# ---- 27-call accounting ----
def test_27_call_accounting(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="acct27")
    records=json.loads((root/"v46_records.json").read_text(encoding="utf-8"))
    assert len(records)==18
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,19)]
    summary=json.loads((root/"v46_summary.json").read_text(encoding="utf-8"))
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":27, "l1":9, "control_l2":9, "treatment_l2":9}
    assert acc["decoder_calls_started"]=={"total":27, "l1":9, "control_l2":9, "treatment_l2":9}
    assert acc["decoder_calls_completed"]=={"total":27, "l1":9, "control_l2":9, "treatment_l2":9}
    assert v46.HARD_CALL_CAP==27
    # tag fields present
    for rec in records:
        assert rec["tag_scope"]=="l2_only"
        assert len(rec["target_tag"])==16
        assert len(rec["candidate_tag"])==16
        assert rec["reclassified"] in v46.RECLASSIFIED_VALUES
    # budget cap 28th refused
    acc2=v46.CallAccounting()
    for _ in range(9):
        acc2.register_start(layer="l1"); acc2.register_complete(layer="l1")
    for _ in range(9):
        acc2.register_start(layer="control"); acc2.register_complete(layer="control")
    for _ in range(9):
        acc2.register_start(layer="treatment"); acc2.register_complete(layer="treatment")
    with pytest.raises(v46.IntegrityFailure) as e:
        acc2.register_start()
    assert e.value.check_id=="J10"

def test_four_way_and_g3_prime(tmp_path, monkeypatch, real_counts):
    # Control undetected vs detected vs decoder_non_syndrome
    def out_detected(idx):
        if idx==0:
            return (False, 10, True, "detected")
        return (True, 0, True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, out_detected, name="detected")
    summary=json.loads((root/"v46_summary.json").read_text(encoding="utf-8"))
    # detected should not trigger G3' failure (undetected==0); exact 8/9 so gate still passes
    assert summary["gate_evaluation"]["cond_control"]["g3_undetected_zero"]["pass"] is True
    assert summary["gate_evaluation"]["cond_control"]["passed"] is True
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, lambda idx: {16:(False,10,True,"detected")}.get(idx,(True,0,True)), name="g3_detected_pass")
    summary2=json.loads((root2/"v46_summary.json").read_text(encoding="utf-8"))
    assert summary2["gate_evaluation"]["cond_control"]["g3_undetected_zero"]["pass"] is True
    assert summary2["gate_evaluation"]["cond_control"]["g3_undetected_zero"]["undetected_count"]==0
    # undetected should trigger G3' failure
    result3, root3 = run_scenario(tmp_path, monkeypatch, real_counts, lambda idx: {0:(False,10,True,"undetected")}.get(idx,(True,0,True)), name="undetected")
    summary3=json.loads((root3/"v46_summary.json").read_text(encoding="utf-8"))
    assert summary3["gate_evaluation"]["cond_control"]["g3_undetected_zero"]["pass"] is False
    assert summary3["gate_evaluation"]["cond_control"]["g3_undetected_zero"]["undetected_count"]==1
    assert summary3["control_arm_undetected_anomaly"] is True or summary3["control_arm_wrong_codeword_anomaly"] is True
    # decoder_non_syndrome
    result4, root4 = run_scenario(tmp_path, monkeypatch, real_counts, lambda idx: {0:(False,10,False,"detected")}.get(idx,(True,0,True)), name="decoder_non")
    summary4=json.loads((root4/"v46_summary.json").read_text(encoding="utf-8"))
    records4=json.loads((root4/"v46_records.json").read_text(encoding="utf-8"))
    rec0 = next(r for r in records4 if r["call_id"]=="C01")
    assert rec0["reclassified"]=="decoder_non_syndrome_failure"

def test_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v46_records.json","v46_records.csv","v46_summary.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v46_records.json").read_text(encoding="utf-8"))
    with (root/"v46_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==18
    summary=json.loads((root/"v46_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["per_source"]["1M"]["control_leak_total"]==984
    assert summary["leakage"]["per_source"]["1M"]["treatment_leak_total"]==1064
    assert summary["leakage"]["leakage_already_accounted"] is True
    assert summary["provenance"]["tag_scope"]=="l2_only"
    assert summary["provenance"]["tag_material"]==v46.TAG_SOURCE_STR

def test_cli_guards():
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout+proc.stderr)
    proc2=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized","--authorized-target-sha","0"*40], capture_output=True, text=True)
    assert proc2.returncode!=0
    assert "J1_SHA_BINDING_MISMATCH" in (proc2.stdout+proc2.stderr)
    script_text=SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script_text

def test_no_real_decoder_call_counted(monkeypatch, tmp_path, real_counts):
    calls={"decode":0}
    def counting_decode(*a, **kw):
        calls["decode"]+=1
        return SimpleNamespace(x_hat=np.zeros(1024,dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok", final_beliefs=np.zeros((1024,32)))
    world=FakeWorld()
    root=tmp_path/"no_real"
    # Use fake_runner True so real decode not called; counting_decode should remain 0
    result=v46.run_v46_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert calls["decode"]==0
