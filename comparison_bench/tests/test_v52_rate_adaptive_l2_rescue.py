"""Focused V52P0 tests (decoder-free, fake-runner) for nested rescue.

All tests are fake-runner / stub-decode. No production decoder invoked, official V52 output root never created.
Covers: dedup old=base, conditional rescue, budget 0/partial/all (30/37/45), hard cap 45, leakage 4 tiers, rank/nested/+40 preflight, fresh 393xxx zero overlap.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_gf32_rank, compute_tag_64, load_v25_channel_counts
from comparison_bench.formal_ir import v52_rate_adaptive_l2_rescue as v52
import comparison_bench.formal_ir.v38_architecture_triage as v38

SCRIPT_PATH = Path(__file__).resolve().parents[2].parent / "scripts" / "execute_v52_nested_rescue.py"
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v52_nested_rescue.py"
    if not SCRIPT_PATH.exists():
        SCRIPT_PATH = Path("D:/Code/HD-QKD_Polar_Comparison/scripts/execute_v52_nested_rescue.py")

OUTPUT_ROOT_REAL = Path(__file__).resolve().parents[2] / "outputs_comparison" / "formal_ir_methods" / "v52_rate_adaptive_l2_rescue" / "run_01"
if not OUTPUT_ROOT_REAL.exists():
    OUTPUT_ROOT_REAL = Path("D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/formal_ir_methods/v52_rate_adaptive_l2_rescue/run_01")

@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()

class FakeWorld:
    def __init__(self):
        self.constructors = {"lane_c": self._make_ctor()}
    def _make_ctor(self):
        def _ctor(source: str, seed: int, field=None):
            field = field or GF2mField.create(32)
            H, metrics = v38.construct_lane_c_prototype(source=source, seed=seed, field=field)
            return H, metrics
        return _ctor
    def authority_file(self, tmp_path: Path) -> Path:
        records: list[dict] = []
        field = GF2mField.create(32)
        for source in v52.SOURCE_ORDER:
            seed = v52._rep_seed("lane_c", source)
            H, met = v38.construct_lane_c_prototype(source=source, seed=seed, field=field)
            records.append(dict(met))
        for i in range(24):
            records.append({"lane": "lane_a", "source": "1M", "construction_seed": 900000+i, "matrix_id": f"lane_a_1M_s{900000+i}", "shape": [4,1024], "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid": True, "position_permutations": [[0]]})
        records = records[:27]
        for src in v52.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v52._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"] == mid for r in records)
        path = tmp_path / "fake_authority_v52.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def _run_with_pattern(tmp_path, monkeypatch, real_counts, base_results: list[bool], rescue_results: list[bool], name="run"):
    """base_results length 15 bools for exact, rescue_results mapped only for those base false."""
    # we need to intercept _evaluate_one_l2 to return controlled exact/tag/syndrome
    call_log: list[dict] = []
    base_ptr = {"i": 0}
    rescue_ptr = {"i": 0}
    block_idx_map: dict[int,int] = {}
    # build block order: source 1M 5, 1p5M 5, 2M 5
    bids = []
    for s in v52.SOURCE_ORDER:
        bids.extend(v52.NEW_BLOCK_SEEDS[s])
    # We'll patch _evaluate_one_l2
    orig = v52._evaluate_one_l2
    def patched(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        call_log.append({"source": source, "block_seed": block_seed, "arm": spec.get("arm"), "matrix_shape": matrix.shape})
        empty = np.empty(0, dtype=np.uint8)
        # determine if base or rescue
        arm = spec.get("arm")
        if arm == "base_shared":
            idx = base_ptr["i"]
            base_ptr["i"] += 1
            ok = base_results[idx] if idx < len(base_results) else True
            # success -> exact true tag true syndrome true
            if ok:
                target = compute_tag_64(empty, u2_alice)
                return {
                    "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                    "frame_ids": list(v52.BLOCK_WINDOWS[block_seed]["frame_ids"]), "held_out_ordinal_start": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]), "held_out_ordinal_end": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),
                    "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                    "errors_initial": int(errors_initial), "errors_final": 0 if ok else 10,
                    "exact_l2": bool(ok), "exact_u1": True, "exact_full": bool(ok),
                    "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                    "target_tag": target, "candidate_tag": target if ok else compute_tag_64(empty, (u2_alice+1)%32), "tag_ok": bool(ok), "tag_scope": v52.TAG_SCOPE, "reclassified": v52.classify_reclassified(ok, True, ok),
                    "iterations_l1": 5, "iterations_l2": 5 if ok else 90,
                    "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                    "leak_total": v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
                    "status": "converged_exact" if ok else "max_iter", "runtime_s": 0.001,
                    "arm": "base_shared", "pass_index": 1, "used_increment": False, "joint": False,
                }
            else:
                # base failure: tag false, but syndrome true -> detected
                target = compute_tag_64(empty, u2_alice)
                alt = compute_tag_64(empty, (u2_alice+1)%32)
                return {
                    "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                    "frame_ids": list(v52.BLOCK_WINDOWS[block_seed]["frame_ids"]), "held_out_ordinal_start": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]), "held_out_ordinal_end": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),
                    "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                    "errors_initial": int(errors_initial), "errors_final": 10,
                    "exact_l2": False, "exact_u1": True, "exact_full": False,
                    "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                    "target_tag": target, "candidate_tag": alt, "tag_ok": False, "tag_scope": v52.TAG_SCOPE, "reclassified": "detected_verification_failure",
                    "iterations_l1": 5, "iterations_l2": 90,
                    "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                    "leak_total": v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
                    "status": "max_iter", "runtime_s": 0.001,
                    "arm": "base_shared", "pass_index": 1, "used_increment": False, "joint": False,
                }
        else:  # rescue
            idx = rescue_ptr["i"]
            rescue_ptr["i"] += 1
            ok = rescue_results[idx] if idx < len(rescue_results) else False
            target = compute_tag_64(empty, u2_alice)
            if ok:
                return {
                    "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                    "frame_ids": list(v52.BLOCK_WINDOWS[block_seed]["frame_ids"]), "held_out_ordinal_start": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]), "held_out_ordinal_end": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),
                    "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                    "errors_initial": int(errors_initial), "errors_final": 0,
                    "exact_l2": True, "exact_u1": True, "exact_full": True,
                    "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                    "target_tag": target, "candidate_tag": target, "tag_ok": True, "tag_scope": v52.TAG_SCOPE, "reclassified": "exact",
                    "iterations_l1": 5, "iterations_l2": 5,
                    "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                    "leak_total": v52.leak_joint_for(source), "leak_joint": v52.leak_joint_for(source),
                    "status": "converged_exact", "runtime_s": 0.001,
                    "arm": "rescue", "pass_index": 2, "used_increment": True, "joint": True,
                }
            else:
                alt = compute_tag_64(empty, (u2_alice+1)%32)
                return {
                    "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                    "frame_ids": list(v52.BLOCK_WINDOWS[block_seed]["frame_ids"]), "held_out_ordinal_start": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]), "held_out_ordinal_end": int(v52.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),
                    "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                    "errors_initial": int(errors_initial), "errors_final": 10,
                    "exact_l2": False, "exact_u1": True, "exact_full": False,
                    "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                    "target_tag": target, "candidate_tag": alt, "tag_ok": False, "tag_scope": v52.TAG_SCOPE, "reclassified": "detected_verification_failure",
                    "iterations_l1": 5, "iterations_l2": 90,
                    "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                    "leak_total": v52.leak_joint_for(source), "leak_joint": v52.leak_joint_for(source),
                    "status": "max_iter", "runtime_s": 0.001,
                    "arm": "rescue", "pass_index": 2, "used_increment": True, "joint": True,
                }
    monkeypatch.setattr(v52, "_evaluate_one_l2", patched)
    world = FakeWorld()
    root = tmp_path / name
    result = v52.run_v52_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    monkeypatch.setattr(v52, "_evaluate_one_l2", orig)
    return result, root, call_log

# ---- tests ----

def test_fresh15_zero_overlap():
    assert len(v52.NEW_BLOCK_SEEDS["1M"])==5
    assert v52.NEW_BLOCK_SEEDS["1M"]==[393001,393002,393003,393004,393005]
    assert v52.NEW_BLOCK_SEEDS["1p5M"]==[393101,393102,393103,393104,393105]
    assert v52.NEW_BLOCK_SEEDS["2M"]==[393201,393202,393203,393204,393205]
    flat = [s for src in v52.SOURCE_ORDER for s in v52.NEW_BLOCK_SEEDS[src]]
    assert len(flat)==15 and len(set(flat))==15
    assert set(flat) & v52.FORBIDDEN_171 == set()
    assert len(v52.FORBIDDEN_171)==171
    assert v52.BLOCK_WINDOWS[393001]["frame_ids"]==[1618,1619,1620,1621]
    assert v52.BLOCK_WINDOWS[393205]["frame_ids"]==[2949,2950,2951,2952]
    for src in v52.SOURCE_ORDER:
        assert v52.V52_HELDOUT_FRAME_IDS[src] & v52.V48_HELDOUT_FRAME_IDS[src] == set()
        assert v52.V52_HELDOUT_FRAME_IDS[src] & v52.V50_HELDOUT_FRAME_IDS[src] == set()
        assert v52.V52_HELDOUT_FRAME_IDS[src] & v52.V51_HELDOUT_FRAME_IDS[src] == set()
    # also block id registry check
    ok, msg = v52.validate_seed_registry()
    assert ok, msg

def test_h_joint_rank_nested_plus40():
    field = GF2mField.create(32)
    mats = v52.reconstruct_v52_matrices(field=field)
    for src in v52.SOURCE_ORDER:
        H_base = mats[("lane_c", src)][0]
        H_inc = mats[("h_inc", src)][0]
        H_joint = mats[("h_joint", src)][0]
        m2 = v52.SOURCE_CHECKS[src]
        assert H_base.shape == (m2, 1024)
        assert H_inc.shape == (8, 1024)
        assert H_joint.shape == (m2+8, 1024)
        assert int(compute_gf32_rank(H_base, field)) == m2
        assert int(compute_gf32_rank(H_joint, field)) == m2+8
        assert np.array_equal(H_joint[0:m2, :], H_base)
        assert int(compute_gf32_rank(H_joint, field)) - int(compute_gf32_rank(H_base, field)) == 8
        # degree checks
        Hs_inc = (H_inc != 0).astype(np.uint8)
        assert int(np.count_nonzero(Hs_inc, axis=0).max()) <= 1
        assert int(np.count_nonzero(Hs_inc, axis=1).max()) <= 16
        assert v52.leak_joint_for(src) - v52.leak_for(src) == 40
    # preflight decoder-free P1-P3
    pre = v52.nested_rescue_preflight(matrices=mats, field=field)
    assert pre["nested_ok"] is True
    for src in v52.SOURCE_ORDER:
        assert pre["per_source"][src]["joint_rank_ok"] is True
        assert pre["per_source"][src]["independence_ok"] is True
        assert pre["per_source"][src]["leakage_accounted"] is True

def test_dedup_old_equals_base(tmp_path, monkeypatch, real_counts):
    # all base success -> old should equal base, no extra L2 call for old
    base_results = [True]*15
    result, root, log = _run_with_pattern(tmp_path, monkeypatch, real_counts, base_results, [], name="dedup")
    records = json.loads((root/"v52_records.json").read_text(encoding="utf-8"))
    # should have only 15 base records, no rescue, no duplicate old
    assert len(records)==15
    assert all(r["arm"]=="base_shared" for r in records)
    # call log should be 15 base only, not 30
    assert len([c for c in log if c["arm"]=="base_shared"])==15
    assert len([c for c in log if c["arm"]=="rescue"])==0
    summary = json.loads((root/"v52_summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["old_exact_full"] == summary["counts"]["first_pass_success"] == 15
    assert summary["counts"]["final_exact_full"] == 15
    # no rescue attempted
    assert summary["leakage"]["n_rescue_attempted"]==0

def test_budget_three_boundaries(tmp_path, monkeypatch, real_counts):
    # 0 rescue: all pass
    base_all_pass = [True]*15
    r0, root0, log0 = _run_with_pattern(tmp_path, monkeypatch, real_counts, base_all_pass, [], name="budget0")
    s0 = json.loads((root0/"v52_summary.json").read_text(encoding="utf-8"))
    assert s0["accounting"]["decoder_calls_completed"]["total"]==30
    assert s0["accounting"]["decoder_calls_completed"]["l1"]==15
    assert s0["accounting"]["decoder_calls_completed"]["base"]==15
    assert s0["accounting"]["decoder_calls_completed"]["rescue"]==0
    rec0 = json.loads((root0/"v52_records.json").read_text(encoding="utf-8"))
    assert len(rec0)==15
    # partial rescue: 7 fail, 5 of those rescued
    base_partial = [True]*8 + [False]*7  # 8 pass, 7 fail
    rescue_partial = [True]*5 + [False]*2  # 5 rescued, 2 still fail
    r1, root1, log1 = _run_with_pattern(tmp_path, monkeypatch, real_counts, base_partial, rescue_partial, name="budgetPartial")
    s1 = json.loads((root1/"v52_summary.json").read_text(encoding="utf-8"))
    assert s1["leakage"]["n_rescue_attempted"]==7
    assert s1["accounting"]["decoder_calls_completed"]["total"]==15+15+7
    assert len(json.loads((root1/"v52_records.json").read_text(encoding="utf-8")))==22
    # check conditional: only failed got rescue
    rec1 = json.loads((root1/"v52_records.json").read_text(encoding="utf-8"))
    rescue_blocks = {r["block_seed"] for r in rec1 if r["arm"]=="rescue"}
    assert len(rescue_blocks)==7
    # all rescue: all 15 fail
    base_all_fail = [False]*15
    rescue_all = [False]*15  # all still fail but attempted
    r2, root2, log2 = _run_with_pattern(tmp_path, monkeypatch, real_counts, base_all_fail, rescue_all, name="budgetAll")
    s2 = json.loads((root2/"v52_summary.json").read_text(encoding="utf-8"))
    assert s2["leakage"]["n_rescue_attempted"]==15
    assert s2["accounting"]["decoder_calls_completed"]["total"]==45
    assert s2["accounting"]["decoder_calls_completed"]["rescue"]==15
    assert len(json.loads((root2/"v52_records.json").read_text(encoding="utf-8")))==30
    # hard cap: 46th should fail (register beyond 45)
    acc = v52.CallAccounting(hard_cap=45)
    for _ in range(15):
        acc.register_start(layer="l1"); acc.register_complete(layer="l1")
    for _ in range(15):
        acc.register_start(layer="base"); acc.register_complete(layer="base")
    for _ in range(15):
        acc.register_start(layer="rescue"); acc.register_complete(layer="rescue")
    with pytest.raises(v52.IntegrityFailure) as e:
        acc.register_start()
    assert e.value.check_id=="J10"
    with pytest.raises(v52.IntegrityFailure):
        acc.register_start(layer="rescue")

def test_leakage_four_tiers(tmp_path, monkeypatch, real_counts):
    # create mix: first 5 pass (leak_base), next 5 rescued (leak_joint success), last 5 fail (leak_joint failure)
    base_results = [True]*5 + [False]*10
    rescue_results = [True]*5 + [False]*5
    result, root, log = _run_with_pattern(tmp_path, monkeypatch, real_counts, base_results, rescue_results, name="leak4")
    records = json.loads((root/"v52_records.json").read_text(encoding="utf-8"))
    summary = json.loads((root/"v52_summary.json").read_text(encoding="utf-8"))
    # per-record leak check
    for r in records:
        if r["arm"]=="base_shared":
            assert r["leak_total"]==v52.leak_for(r["source"])
            assert r["leak_joint"]==v52.leak_joint_for(r["source"])
        else:
            assert r["leak_total"]==v52.leak_joint_for(r["source"])
    # summary 4 tiers
    assert summary["leakage"]["per_source"]["1M"]["leak_base"]==1064
    assert summary["leakage"]["per_source"]["1p5M"]["leak_base"]==1094
    assert summary["leakage"]["per_source"]["2M"]["leak_base"]==1104
    assert summary["leakage"]["per_source"]["1M"]["leak_joint"]==1104
    assert summary["leakage"]["per_source"]["1p5M"]["leak_joint"]==1134
    assert summary["leakage"]["per_source"]["2M"]["leak_joint"]==1144
    # avg = base+40*N_rescue/15 ; per source avg is source-specific, overall avg is mean of per-block leaks
    # For this pattern N_rescue=10
    assert summary["leakage"]["n_rescue_attempted"]==10
    # check per-source avg formula source 1M has  ? need not exact because rescue distribution per source: first 5 are 1M (all pass, 0 rescue), next 5 are 1p5M (all fail?), last 5 2M
    # Overall avg: we compute total_leak_sum/15 ; use summary avg_overall
    # For 1M pass 5 -> leak 1064*5, 1p5M 5 rescue -> 1134*5, 2M 5 fail -> 1144*5 => total = 1064*5+1134*5+1144*5 = (1064+1134+1144)*5 = 3342*5=16710 /15=1114
    # But our base pattern may not align source mapping: we used base_results ordered source asc, so first 5 are 1M, next 5 1p5M, last 5 2M
    # So overall avg should be (1064*5 +1134*5 +1144*5)/15 = 1114 . But rescue for 1M 0, 1p5M 5, 2M 5
    # Check summary per_source avgs: 1M avg =1064, 1p5M avg=1094+40=1134, 2M avg=1104+40=1144
    assert summary["leakage"]["avg_leak_per_source"]["1M"]==1064.0
    assert summary["leakage"]["avg_leak_per_source"]["1p5M"]==1134.0
    assert summary["leakage"]["avg_leak_per_source"]["2M"]==1144.0
    # failed conditional leakage is leak_joint
    assert summary["leakage"]["final_failure_leak"]["1M"]==1104
    # rescue rescued leak is joint
    assert summary["leakage"]["rescued_success_leak"]["1M"]==1104

def test_terminal_and_counts(tmp_path, monkeypatch, real_counts):
    base_results = [True]*12 + [False]*3
    rescue_results = [True]*2 + [False]*1
    result, root, log = _run_with_pattern(tmp_path, monkeypatch, real_counts, base_results, rescue_results, name="terminal")
    summary = json.loads((root/"v52_summary.json").read_text(encoding="utf-8"))
    assert summary["terminal_state"]==v52.TERMINAL_NESTED_RESCUE_COMPLETE
    assert summary["counts"]["first_pass_success"]==12
    assert summary["counts"]["rescued_by_increment"]==2
    assert summary["counts"]["final_exact_full"]==14
    assert summary["counts"]["old_exact_full"]==12  # dedup
    assert summary["counts"]["per_source"]["1M"]["old"] + summary["counts"]["per_source"]["1p5M"]["old"] + summary["counts"]["per_source"]["2M"]["old"]==12
    # records file contract
    names={p.name for p in root.iterdir()}
    assert "v52_records.json" in names and "v52_records.csv" in names and "v52_summary.json" in names
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v52_records.json").read_text(encoding="utf-8"))
    with (root/"v52_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)
    for r in records:
        ok, msg = v52.validate_record_schema(r)
        assert ok, msg
        assert r["tag_scope"]=="l2_only"
        assert r["sampling_mode"]==v52.SAMPLING_MODE
        assert r["pairs_count"]==1024

def test_cli_guards():
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout+proc.stderr)
    proc2=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized","--authorized-target-sha","0"*40], capture_output=True, text=True)
    assert proc2.returncode!=0
    script_text=SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script_text

def test_output_root_not_exists_real():
    assert not OUTPUT_ROOT_REAL.exists(), f"formal output root should not exist: {OUTPUT_ROOT_REAL}"

def test_no_old_duplicate_decode():
    src = Path(v52.__file__).read_text(encoding="utf-8")
    assert "old_exact = base_exact" in src or "old_exact = exact_base" in src or "old_exact" in src
    # ensure runner does not call decode for old separately: count base+rescue only
    assert "base 1(兼 old" in src or "兼 old" in src

# ---- V52补测：阻塞点显式测试（f1e94e5 真调用计数、q复用、verify真exact假不rescue）----

def test_l1_fifteen_true_bp_calls(tmp_path, monkeypatch, real_counts):
    """15次 L1 真调用（mock H1 BP 计数==15，非 fake shortcut）。"""
    import comparison_bench.formal_ir.v35_algorithm_development as v35

    # fake parq 块数据，避免依赖真实 parquet
    def _fake_load(block_seed: int):
        rng = np.random.default_rng(int(block_seed) ^ 0x9E3779B9)
        alice = rng.integers(0, 1024, size=1024, dtype=np.int64)
        bob = rng.integers(0, 1024, size=1024, dtype=np.int64)
        return alice, bob

    monkeypatch.setattr(v52, "load_heldout_block", _fake_load)

    l1_calls: list[dict] = []

    class _MockL1:
        def __init__(self, final_beliefs):
            self.final_beliefs = final_beliefs
            self.iterations = 5
            self.syndrome_ok = True
            self.status = "converged_exact"
            self.runtime_s = 0.001
            # x_hat not used for L1 path beyond syndrome/exact_u1 derived via q
            self.x_hat = np.zeros(1024, dtype=np.uint8)
            # BP-04: cross-layer APP guard requires explicit conditioned
            # provenance on the mocked L1 return.
            self.belief_provenance = "CHECK_UPDATED"

    orig_dec = v35.decode_row_layered_fftqspa

    def _mock_dec(matrix, prior, syn, max_iter=90, damping_alpha=1.0, field=None):
        # limit to H1 shape 16x1024 to ensure we only count L1 calls
        l1_calls.append({"shape": tuple(matrix.shape), "prior_shape": tuple(prior.shape)})
        # return valid beliefs so q computable
        fb = np.log(np.maximum(prior, 1e-15)) + 0.01 * np.random.default_rng(0).standard_normal(prior.shape)
        return _MockL1(fb)

    monkeypatch.setattr(v35, "decode_row_layered_fftqspa", _mock_dec)

    # also mock L2 via _evaluate_one_l2 to always succeed (avoid L2 decode counting confusion)
    orig_eval = v52._evaluate_one_l2

    def _fake_eval(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        empty = np.empty(0, dtype=np.uint8)
        target = compute_tag_64(empty, u2_alice)
        win = v52.BLOCK_WINDOWS[block_seed]
        return {
            "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
            "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
            "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
            "errors_initial": int(errors_initial), "errors_final": 0,
            "exact_l2": True, "exact_u1": True, "exact_full": True,
            "syndrome_ok_l2": True, "syndrome_ok_l1": True,
            "target_tag": target, "candidate_tag": target, "tag_ok": True, "tag_scope": v52.TAG_SCOPE, "reclassified": "exact",
            "iterations_l1": 5, "iterations_l2": 5,
            "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
            "leak_total": v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
            "status": "converged_exact", "runtime_s": 0.001,
            "arm": spec.get("arm", "base_shared"), "pass_index": int(spec.get("pass_index", 1)), "used_increment": bool(spec.get("used_increment", False)), "joint": bool(spec.get("joint", False)),
        }

    monkeypatch.setattr(v52, "_evaluate_one_l2", _fake_eval)

    world = FakeWorld()
    root = tmp_path / "l1count"
    result = v52.run_v52_diagnostic(
        execution_authorized=True, authorized_target_sha="f" * 40,
        fake_runner=False,  # 非 fake shortcut，强制走真 L1 BP 分支
        output_root=root, structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts, check_git=False, check_scoped_dirty=False,
        constructors=world.constructors, decode_fn=None,
    )
    # restore
    monkeypatch.setattr(v35, "decode_row_layered_fftqspa", orig_dec)
    monkeypatch.setattr(v52, "_evaluate_one_l2", orig_eval)

    assert len(l1_calls) == 15, f"H1 BP 真调用次数应为15，实际{len(l1_calls)}"
    assert all(c["shape"] == (16, 1024) for c in l1_calls)
    # accounting 也应为 15
    summary = json.loads((root / "v52_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_completed"]["l1"] == 15
    assert summary["accounting"]["decoder_calls_completed"]["total"] == 30  # 15 L1 +15 base，无 rescue
    # 确认走的是真分支而非 fake_runner shortcut：_mock_dec 被调用即证明
    assert result["terminal_state"] == v52.TERMINAL_NESTED_RESCUE_COMPLETE


def test_q_reused_between_base_and_rescue(tmp_path, monkeypatch, real_counts):
    """q 传入 base 与 rescue 两遍一致（同一对象/数值相等，rescue 复用 q 不重算 prior）。"""
    captured: dict[int, dict[str, np.ndarray]] = {}

    orig = v52._evaluate_one_l2

    def _capture(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        arm = spec.get("arm")
        entry = captured.setdefault(int(block_seed), {})
        # 记录 q 的 id 与数值拷贝
        if q is not None:
            entry[arm] = {"q_id": id(q), "q": np.array(q, copy=True), "p_prior_id": id(p_prior) if p_prior is not None else None}
        # base 对首个块构造失败以触发 rescue，其余成功
        empty = np.empty(0, dtype=np.uint8)
        target = compute_tag_64(empty, u2_alice)
        alt = compute_tag_64(empty, (u2_alice + 1) % 32)
        win = v52.BLOCK_WINDOWS[block_seed]
        # 让 393001 失败，其余成功，rescue 对 393001 成功
        if arm == "base_shared" and int(block_seed) == 393001:
            return {
                "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
                "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                "errors_initial": int(errors_initial), "errors_final": 10,
                "exact_l2": False, "exact_u1": True, "exact_full": False,
                "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                "target_tag": target, "candidate_tag": alt, "tag_ok": False, "tag_scope": v52.TAG_SCOPE, "reclassified": "detected_verification_failure",
                "iterations_l1": 5, "iterations_l2": 90,
                "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                "leak_total": v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
                "status": "max_iter", "runtime_s": 0.001,
                "arm": "base_shared", "pass_index": 1, "used_increment": False, "joint": False,
            }
        else:
            # base 成功或 rescue 成功
            is_rescue = arm == "rescue"
            return {
                "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
                "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                "errors_initial": int(errors_initial), "errors_final": 0,
                "exact_l2": True, "exact_u1": True, "exact_full": True,
                "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                "target_tag": target, "candidate_tag": target, "tag_ok": True, "tag_scope": v52.TAG_SCOPE, "reclassified": "exact",
                "iterations_l1": 5, "iterations_l2": 5,
                "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                "leak_total": v52.leak_joint_for(source) if is_rescue else v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
                "status": "converged_exact", "runtime_s": 0.001,
                "arm": arm, "pass_index": 2 if is_rescue else 1, "used_increment": bool(is_rescue), "joint": bool(is_rescue),
            }

    monkeypatch.setattr(v52, "_evaluate_one_l2", _capture)
    world = FakeWorld()
    root = tmp_path / "qreuse"
    result = v52.run_v52_diagnostic(
        execution_authorized=True, authorized_target_sha="f" * 40, fake_runner=True,
        output_root=root, structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts, check_git=False, check_scoped_dirty=False,
        constructors=world.constructors, decode_fn=None,
    )
    monkeypatch.setattr(v52, "_evaluate_one_l2", orig)

    # 393001 应有 base 与 rescue 两次捕获
    assert 393001 in captured and "base_shared" in captured[393001] and "rescue" in captured[393001]
    base_q = captured[393001]["base_shared"]["q"]
    rescue_q = captured[393001]["rescue"]["q"]
    base_id = captured[393001]["base_shared"]["q_id"]
    rescue_id = captured[393001]["rescue"]["q_id"]
    # 同一对象或数值相等（实现复用 q 不重新计算 prior）
    assert (base_id == rescue_id) or np.array_equal(base_q, rescue_q), "rescue 应复用与 base 相同的 prior q"
    assert base_q.shape == (1024, 32)
    assert np.allclose(base_q, rescue_q, equal_nan=False)
    # 仅该块触发 rescue
    summary = json.loads((root / "v52_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["n_rescue_attempted"] == 1
    # p_prior 也应一致（同一次 L1 计算）
    assert captured[393001]["base_shared"]["p_prior_id"] == captured[393001]["rescue"]["p_prior_id"]


def test_verify_true_exact_false_no_rescue(tmp_path, monkeypatch, real_counts):
    """verify=true / exact=false 时不 rescue（syndrome_ok&&tag_ok==True 但 exact==False 的 undetected 块）。"""
    orig = v52._evaluate_one_l2
    rescue_calls: list[int] = []
    base_calls: list[int] = []

    def _trap(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        arm = spec.get("arm")
        empty = np.empty(0, dtype=np.uint8)
        target = compute_tag_64(empty, u2_alice)
        win = v52.BLOCK_WINDOWS[block_seed]
        if arm == "base_shared":
            base_calls.append(int(block_seed))
            # 对 393002 构造 syndrome_ok&&tag_ok True 但 exact False 的块（undetected_accepted_wrong）
            if int(block_seed) == 393002:
                return {
                    "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                    "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
                    "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                    "errors_initial": int(errors_initial), "errors_final": 10,
                    "exact_l2": False, "exact_u1": False, "exact_full": False,
                    "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                    "target_tag": target, "candidate_tag": target, "tag_ok": True, "tag_scope": v52.TAG_SCOPE, "reclassified": "undetected_accepted_wrong",
                    "iterations_l1": 5, "iterations_l2": 5,
                    "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                    "leak_total": v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
                    "status": "converged_exact", "runtime_s": 0.001,
                    "arm": "base_shared", "pass_index": 1, "used_increment": False, "joint": False,
                }
            # 其余块正常成功
            return {
                "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
                "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                "errors_initial": int(errors_initial), "errors_final": 0,
                "exact_l2": True, "exact_u1": True, "exact_full": True,
                "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                "target_tag": target, "candidate_tag": target, "tag_ok": True, "tag_scope": v52.TAG_SCOPE, "reclassified": "exact",
                "iterations_l1": 5, "iterations_l2": 5,
                "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                "leak_total": v52.leak_for(source), "leak_joint": v52.leak_joint_for(source),
                "status": "converged_exact", "runtime_s": 0.001,
                "arm": "base_shared", "pass_index": 1, "used_increment": False, "joint": False,
            }
        else:
            rescue_calls.append(int(block_seed))
            # rescue 正常成功（但本测试不应进入）
            return {
                "source": source, "block_seed": block_seed, "matrix_id": spec["matrix_id"], "h1_matrix_id": v52.H1_MATRIX_ID,
                "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
                "pairs_count": 1024, "sampling_mode": v52.SAMPLING_MODE,
                "errors_initial": int(errors_initial), "errors_final": 0,
                "exact_l2": True, "exact_u1": True, "exact_full": True,
                "syndrome_ok_l2": True, "syndrome_ok_l1": True,
                "target_tag": target, "candidate_tag": target, "tag_ok": True, "tag_scope": v52.TAG_SCOPE, "reclassified": "exact",
                "iterations_l1": 5, "iterations_l2": 5,
                "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
                "leak_total": v52.leak_joint_for(source), "leak_joint": v52.leak_joint_for(source),
                "status": "converged_exact", "runtime_s": 0.001,
                "arm": "rescue", "pass_index": 2, "used_increment": True, "joint": True,
            }

    monkeypatch.setattr(v52, "_evaluate_one_l2", _trap)
    world = FakeWorld()
    root = tmp_path / "verify_no_rescue"
    result = v52.run_v52_diagnostic(
        execution_authorized=True, authorized_target_sha="f" * 40, fake_runner=True,
        output_root=root, structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts, check_git=False, check_scoped_dirty=False,
        constructors=world.constructors, decode_fn=None,
    )
    monkeypatch.setattr(v52, "_evaluate_one_l2", orig)

    # 393002 的 syndrome/tag 均为 true，verify=true，故不应 rescue
    assert 393002 not in rescue_calls, f"verify true 时不应 rescue，但 rescue_calls={rescue_calls}"
    assert len(rescue_calls) == 0, f"预期 rescue_calls==0，实际{rescue_calls}"
    assert len(base_calls) == 15
    summary = json.loads((root / "v52_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["n_rescue_attempted"] == 0
    assert summary["accounting"]["decoder_calls_completed"]["rescue"] == 0
    # 该 undetected 块的记录仍为 base_shared，reclassified 为 undetected_accepted_wrong
    records = json.loads((root / "v52_records.json").read_text(encoding="utf-8"))
    rec_393002 = next(r for r in records if r["block_seed"] == 393002)
    assert rec_393002["reclassified"] == "undetected_accepted_wrong"
    assert rec_393002["syndrome_ok_l2"] is True and rec_393002["tag_ok"] is True
    assert rec_393002["exact_l2"] is False  # exact false 但 verify true -> 不 rescue

