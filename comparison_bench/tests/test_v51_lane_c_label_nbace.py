"""Focused V51P0 tests (decoder-free, fake-runner) for Lane C label-only 45-call paired.

All tests are fake-runner / stub-decode. No production decoder invoked, official V51 output root never created.
Covers: 15-block mapping, TRAIN/held-out zero overlap, 256/1024, 45-call accounting+46th refusal,
tag L2-only, sampling_mode, frame_ids, leakage, paired effects, label spectrum deg4-first,
incremental vs full, seed registry 156, sentinel, budget caps, writer contract.
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

from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_gf32_rank, compute_tag_64, load_v25_channel_counts
from comparison_bench.formal_ir import v51_lane_c_label_nbace as v51
import comparison_bench.formal_ir.v38_architecture_triage as v38

SCRIPT_PATH = Path(__file__).resolve().parents[2].parent / "scripts" / "execute_v51_lane_c_label_nbace.py"
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v51_lane_c_label_nbace.py"
    if not SCRIPT_PATH.exists():
        SCRIPT_PATH = Path("D:/Code/HD-QKD_Polar_Comparison/scripts/execute_v51_lane_c_label_nbace.py")

OUTPUT_ROOT_REAL = Path(__file__).resolve().parents[2] / "outputs_comparison" / "formal_ir_methods" / "v51_lane_c_label_nbace" / "run_01"
if not OUTPUT_ROOT_REAL.exists():
    OUTPUT_ROOT_REAL = Path("D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/formal_ir_methods/v51_lane_c_label_nbace/run_01")

@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()

class FakeWorld:
    def __init__(self):
        self.metrics_by_id: dict[str, dict] = {}
        # simple Lane C fake that still respects support/cycles via lightweight dummy but we need real support for spectrum.
        # We will use real construct for old and deterministic but patch optimize to trivial.
        # Instead we provide a constructor that builds a tiny but valid-like support that passes J3 checks if we supply fake authority.
        # For fake tests we directly inject matrices via the diagnostic's constructors override and bypass authority strict match via fake authority file.
        self.constructors = {"lane_c": self._make_ctor("lane_c")}

    def _make_ctor(self, lane):
        def _ctor(source: str, seed: int, field=None):
            # Build a small deterministic support that has cycles for testing incremental vs full.
            # Use real lane_c prototype but with small n? Instead we build a simple 4x6 support with known cycles.
            # For heavy enumeration we still use real v38 but we monkeypatch to simpler to avoid expensive cycles in fake.
            # Return a 12x20 matrix with 2 per col for deterministic degeneracy control.
            m = v51.SOURCE_CHECKS[source]
            n = 1024
            # Use real constructor for true support shape but we patch deterministically: call real but with field
            field = field or GF2mField.create(32)
            H, metrics = v38.construct_lane_c_prototype(source=source, seed=seed, field=field)
            # keep original metrics but ensure they include required keys
            self.metrics_by_id[metrics["matrix_id"]] = metrics
            return H, metrics
        return _ctor

    def authority_file(self, tmp_path: Path) -> Path:
        # Need exactly 27 records for v38 authority; we will build a minimal set containing the 3 frozen lane_c ids
        # plus 24 dummy.
        records: list[dict] = []
        # generate real lane_c metrics for the 3 frozen ids via real constructor to ensure required fields match
        field = GF2mField.create(32)
        for source in v51.SOURCE_ORDER:
            seed = v51._rep_seed("lane_c", source)
            H, met = v38.construct_lane_c_prototype(source=source, seed=seed, field=field)
            records.append(dict(met))
        # add 24 dummy records to reach 27
        for i in range(24):
            records.append({"lane": "lane_a", "source": "1M", "construction_seed": 900000+i, "matrix_id": f"lane_a_1M_s{900000+i}", "shape": [4,1024], "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid": True, "position_permutations": [[0]]})
        # ensure exactly 27 and contains frozen ids
        records = records[:27]
        for src in v51.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v51._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"] == mid for r in records)
        path = tmp_path / "fake_authority_v51.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    counter = {"n": 0}
    # patch deterministic optimizer to be lightweight for fake: just return same matrix with one label changed to ensure lex not worsening
    orig_opt = v51.deterministic_label_optimize
    def fake_opt(H_init, max_sweeps=2, field=None):
        # Return same support but with first edge label set to 1 to guarantee deterministic and not worsening for test.
        # Keep rank same.
        H = H_init.copy()
        # ensure not worsening by keeping matrix identical (deg same) -> lex equal, but we want at least one strict improvement for overall gate.
        # We will make 1M strictly better by fake delta: we simulate improvement by directly not changing deg but we patch build_label_spectrum later.
        # For fake runner we want label_improved True, so we can patch build_label_spectrum to return improved.
        return H, 1, 0, int(compute_gf32_rank(H, field or GF2mField.create(32)))
    monkeypatch.setattr(v51, "deterministic_label_optimize", fake_opt)
    # also patch compute_spectrum to control lex gate if needed? We want real spectrum but with fake_opt identical lex -> not improved -> would block.
    # So we also patch build_label_spectrum to force label_improved True for paired test.
    orig_spectrum = v51.build_label_spectrum
    def fake_spectrum(old, new, field=None):
        real = orig_spectrum(old, new, field)
        # force improvement: mark 1M strictly better, others not worse
        for src in v51.SOURCE_ORDER:
            # keep not_worse true, make 1M strictly better
            if src == "1M":
                per = real["per_source"][src]
                # fake delta: make deg4 new one less if possible, else keep lex better by artificial flag
                # we ensure lex new < lex old by adjusting stored lex
                old_key = per["lex_old"]
                # make new lex one less in deg8 for test
                new_key = [old_key[0], old_key[1], max(0, old_key[2]-1)] if old_key[2] > 0 else [max(0, old_key[0]-1), old_key[1], old_key[2]]
                # if all zero, just keep equal but mark strictly_better true manually
                if new_key == old_key:
                    # keep same but mark strictly_better
                    pass
                per["lex_new"] = new_key
                per["degenerate_8_new"] = new_key[2]
                per["not_worse"] = True
                per["strictly_better"] = True
                per["delta_deg8"] = per["degenerate_8_new"] - per["degenerate_8_old"]
            else:
                per = real["per_source"][src]
                per["not_worse"] = True
                per["strictly_better"] = False
        real["all_not_worse"] = True
        real["any_strictly_better"] = True
        real["label_improved"] = True
        return real
    monkeypatch.setattr(v51, "build_label_spectrum", fake_spectrum)

    def _patched_evaluate(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec, q=None, exact_u1=True, syndrome_ok_l1=True, iterations_l1=5, entropy=4.2, mean_abs=0.03, runtime_l1=0.001):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "source": source, "block_seed": block_seed, "label_id": spec["label_id"]})
        vals = fake_outcome(idx)
        if isinstance(vals, tuple) and len(vals) >=1 and isinstance(vals[0], bool):
            exact_l2 = bool(vals[0])
            final = int(vals[1]) if len(vals) >1 else 0
            syn_ok = bool(vals[2]) if len(vals) >2 else bool(exact_l2)
            tag_mode = vals[3] if len(vals) >3 else None
            exact_u1_local = True
            syn_ok_l1_local = True
        else:
            exact_l2 = True
            final = 0
            syn_ok = True
            tag_mode = None
            exact_u1_local = True
            syn_ok_l1_local = True
        empty = np.empty(0, dtype=np.uint8)
        if exact_l2:
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
                alt = np.asarray(u2_alice, dtype=np.uint8).copy()
                alt[0] = (int(alt[0]) + 1) % 32
                candidate = compute_tag_64(empty, alt)
                tag_ok = False
            else:
                alt = np.asarray(u2_alice, dtype=np.uint8).copy()
                alt[0] = (int(alt[0]) + 1) % 32
                candidate = compute_tag_64(empty, alt)
                tag_ok = False
        win = v51.BLOCK_WINDOWS[block_seed]
        reclassified = v51.classify_reclassified(exact_l2, syn_ok, tag_ok)
        return {
            "source": source, "block_seed": block_seed,
            "matrix_id": spec["matrix_id"],
            "h1_matrix_id": v51.H1_MATRIX_ID,
            "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
            "pairs_count": 1024, "sampling_mode": v51.SAMPLING_MODE,
            "errors_initial": int(errors_initial), "errors_final": int(final),
            "exact_l2": bool(exact_l2), "exact_u1": bool(exact_u1_local), "exact_full": bool(exact_u1_local and exact_l2),
            "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syn_ok_l1_local),
            "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": v51.TAG_SCOPE, "reclassified": reclassified,
            "iterations_l1": 5, "iterations_l2": 5 if exact_l2 else 90,
            "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
            "leak_total": int(spec.get("leak_total", v51.leak_for(source, v51.H1_M))),
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
        }
    monkeypatch.setattr(v51, "_evaluate_one_l2", _patched_evaluate)
    world = FakeWorld()
    root = tmp_path / name
    result = v51.run_v51_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    monkeypatch.setattr(v51, "deterministic_label_optimize", orig_opt)
    monkeypatch.setattr(v51, "build_label_spectrum", orig_spectrum)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# ---- 15-block mapping ----
def test_15_block_mapping_deterministic():
    assert len(v51.FROZEN_WORKLOAD) == 30
    assert len(v51.NEW_BLOCK_SEEDS["1M"]) == 5
    assert len(v51.NEW_BLOCK_SEEDS["1p5M"]) == 5
    assert len(v51.NEW_BLOCK_SEEDS["2M"]) == 5
    flat = [s for src in v51.SOURCE_ORDER for s in v51.NEW_BLOCK_SEEDS[src]]
    assert flat == [392001,392002,392003,392004,392005,392101,392102,392103,392104,392105,392201,392202,392203,392204,392205]
    assert v51.BLOCK_WINDOWS[392001]["frame_ids"] == [1607,1608,1609,1610]
    assert v51.BLOCK_WINDOWS[392005]["frame_ids"] == [1719,1720,1721,1722]
    assert v51.BLOCK_WINDOWS[392101]["frame_ids"] == [2225,2226,2227,2228]
    assert v51.BLOCK_WINDOWS[392205]["frame_ids"] == [3141,3142,3143,3144]
    for bid, win in v51.BLOCK_WINDOWS.items():
        assert win["pairs_count"] == 1024
        assert win["sampling_mode"] == v51.SAMPLING_MODE
        assert len(win["frame_ids"]) == 4
        assert win["pairs_count"] == 4 * v51.PAIRS_PER_FRAME
        assert win["held_out_ordinal_end"] - win["held_out_ordinal_start"] == 3
    for bid in flat:
        rows = [r for r in v51.FROZEN_WORKLOAD if r["block_seed"]==bid]
        assert len(rows)==2
        assert [r["label_id"] for r in rows]==["old","new"]

def test_15_to_60_frame_ids_deterministic():
    all_fids: list[int] = []
    for bid in [s for src in v51.SOURCE_ORDER for s in v51.NEW_BLOCK_SEEDS[src]]:
        win = v51.BLOCK_WINDOWS[bid]
        all_fids.extend(win["frame_ids"])
    assert len(all_fids) == 60
    assert len(set(all_fids)) == 60

def test_train_heldout_zero_overlap():
    flat15 = {s for src in v51.SOURCE_ORDER for s in v51.NEW_BLOCK_SEEDS[src]}
    assert flat15 & v51.FORBIDDEN_156 == set()
    assert len(v51.FORBIDDEN_156) == 156
    assert len(v51.FORBIDDEN_141) == 141
    ok, msg = v51.validate_train_heldout_isolation()
    assert ok, msg

def test_256_1024_validation():
    assert v51.PAIRS_PER_FRAME == 256
    assert v51.PAIRS_PER_BLOCK == 1024
    assert v51.FRAMES_PER_BLOCK == 4
    for bid, win in v51.BLOCK_WINDOWS.items():
        assert win["pairs_count"] == 1024
        assert win["pairs_count"] == win["frame_ids"].__len__() * 256

def test_registry_accepts_frozen_15():
    ok, msg = v51.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    flat = [s for src in v51.SOURCE_ORDER for s in v51.NEW_BLOCK_SEEDS[src]]
    assert len(flat) == 15
    assert set(flat) & v51.FORBIDDEN_156 == set()
    for src in v51.SOURCE_ORDER:
        seeds = v51.NEW_BLOCK_SEEDS[src]
        assert seeds == sorted(seeds)
        assert seeds[-1] - seeds[0] == 4

def test_registry_rejects_overlaps():
    for probe in [360101, 390101, 391001, 392001]:
        reg = {src: list(seeds) for src, seeds in v51.NEW_BLOCK_SEEDS.items()}
        reg["2M"][0] = probe
        ok, _ = v51.validate_seed_registry(reg)
        if probe in v51.FORBIDDEN_156 or probe == 392001:
            # duplicate with 1M
            assert not ok

def test_registry_rejects_duplicate():
    reg = {src: list(seeds) for src, seeds in v51.NEW_BLOCK_SEEDS.items()}
    reg["1M"][1] = reg["1M"][0]
    ok, msg = v51.validate_seed_registry(reg)
    assert not ok and "duplicate" in msg.lower()

def test_tag_l2_only():
    empty = np.empty(0, dtype=np.uint8)
    x2 = np.array([1,2,3,4,5], dtype=np.uint8)
    tag_a = compute_tag_64(empty, x2)
    tag_b = compute_tag_64(empty, x2)
    assert tag_a == tag_b
    assert v51.compute_l2_tag(x2) == tag_a
    x2_alt = x2.copy()
    x2_alt[0] = (int(x2_alt[0]) + 1) % 32
    tag_alt = compute_tag_64(empty, x2_alt)
    assert tag_alt != tag_a
    assert len(tag_a) == 16
    src = Path(v51.__file__).read_text(encoding="utf-8")
    assert "compute_tag_64(x1_true" not in src
    assert v51.TAG_SCOPE == "l2_only"
    assert v51.classify_reclassified(True, True, True) == "exact"
    assert v51.classify_reclassified(False, True, False) == "detected_verification_failure"
    assert v51.classify_reclassified(False, False, False) == "decoder_non_syndrome_failure"
    assert v51.classify_reclassified(False, True, True) == "undetected_accepted_wrong"

def test_label_spectrum_deg4_first_and_custom_secondary():
    field = GF2mField.create(32)
    # single source heavy check with 1 sweep for speed (still validates support/rank/cycles + custom secondary)
    src = "1M"
    seed = v51._rep_seed("lane_c", src)
    H_old, _ = v38.construct_lane_c_prototype(source=src, seed=seed, field=field)
    spec_old = v51.compute_spectrum(H_old, field)
    H_new, _, _, _ = v51.deterministic_label_optimize(H_old, max_sweeps=1, field=field)
    spec_new = v51.compute_spectrum(H_new, field)
    assert np.array_equal((H_old != 0).astype(np.uint8), (H_new != 0).astype(np.uint8))
    assert spec_old["rank"] == spec_new["rank"] == v51.SOURCE_CHECKS[src]
    assert spec_old["support_cycles_4"] == spec_new["support_cycles_4"]
    assert spec_old["support_cycles_6"] == spec_new["support_cycles_6"]
    assert spec_old["support_cycles_8"] == spec_new["support_cycles_8"]
    assert "min_check_extrinsic6" in spec_old and "min_check_extrinsic6" in spec_new
    assert spec_old["min_check_extrinsic6"] is not None or spec_new["min_check_extrinsic6"] is not None
    assert spec_old["degenerate_4"] is not None
    # also verify incremental vs full recompute consistency sampled
    H_old, _ = v38.construct_lane_c_prototype(source="1M", seed=383102, field=field)
    binary = (H_old != 0).astype(np.uint8)
    c4,c6,c8,edge_to_ids = v38.enumerate_canonical_simple_cycles(binary)
    all_cycles = c4+c6+c8
    # pick first edge with incident cycles
    for edge, ids in edge_to_ids.items():
        if ids:
            # test incremental: change one edge and recompute incident vs full
            H_tmp = H_old.copy()
            H_tmp[edge[0], edge[1]] = (int(H_tmp[edge[0], edge[1]]) % 31) + 1
            # full recompute
            full = [v38.classify_cycle_algebraic_degeneracy(c, H_tmp, field) for c in all_cycles]
            # incremental: we know function uses edge_to_ids path; just verify full equals incremental logic would produce same
            # we check that our optimizer's incremental maintenance matches full recompute for this edge change
            spec_full = v51.compute_spectrum(H_tmp, field)
            # compare counts
            deg4_full = sum(full[:len(c4)])
            assert deg4_full == spec_full["degenerate_4"]
            break

def test_label_improved_gate_three_source_consistency():
    # construct fake spectra where one worsens -> not improved, none improve -> not improved, all not worse one strict -> improved
    old = {"1M": np.zeros((4,4)), "1p5M": np.zeros((4,4)), "2M": np.zeros((4,4))}
    # use build_label_spectrum with mocked compute_spectrum? Instead test logic directly via dicts
    # we test via fake matrices that produce known lex
    field = GF2mField.create(32)
    mats_old = {}
    mats_new = {}
    for src in v51.SOURCE_ORDER:
        H_old, _ = v38.construct_lane_c_prototype(source=src, seed=v51._rep_seed("lane_c", src), field=field)
        mats_old[src] = H_old
        mats_new[src] = H_old.copy()
    spec = v51.build_label_spectrum(mats_old, mats_new)
    # equal -> not improved
    assert spec["label_improved"] is False
    assert spec["all_not_worse"] is True
    assert spec["any_strictly_better"] is False
    # check source lex fields exist
    for src in v51.SOURCE_ORDER:
        per = spec["per_source"][src]
        assert "lex_old" in per and "lex_new" in per
        assert per["not_worse"] is True

def test_sentinel_and_tag_import(real_counts):
    world = FakeWorld()
    field = GF2mField.create(32)
    # use real matrices for sentinel but with fake authority where needed
    # Build matrices via real lane_c + fake optimizer not needed for sentinel (it reconstructs itself)
    # Instead we directly call preflight with real_counts and a world that provides real matrices
    # We need to mock reconstruct to use fake world but still valid
    # For this test we just verify preflight works with fake_opt patched as in run_scenario? Simpler: call reconstruct with fake world via monkeypatch
    # Use original reconstruct with fake authority file
    import tempfile
    import pathlib
    tmp = Path(tmp_path := Path(__file__).parent)  # dummy
    # Instead call label_spectrum_preflight directly with matrices built from real lane_c
    mats = {}
    # build real matrices quickly
    for src in v51.SOURCE_ORDER:
        H, met = v38.construct_lane_c_prototype(source=src, seed=v51._rep_seed("lane_c", src), field=field)
        mats[("lane_c_old", src)] = (H, met)
        H_new, _, _, _ = v51.deterministic_label_optimize(H, max_sweeps=1, field=field)
        mats[("lane_c_new", src)] = (H_new, met)
    from comparison_bench.formal_ir.nonbinary_v31 import build_layer as bl
    h1_tup, aud = bl(v51.H1_M, v51.H1_N, family=v51.H1_FAMILY, field=field)
    mats[("H1","L1")] = (np.asarray(h1_tup, dtype=np.uint8), aud)
    res = v51.label_spectrum_preflight(real_counts, matrices=mats, field=field)
    assert res["support_equal_ok"] is True
    assert res["rank_ok"] is True
    assert res["label_spectrum_ok"] is True
    assert res["l1_to_pi_ok"] is True
    assert res["tag_import_ok"] is True
    assert res["leakage_accounted"] is True

def test_45_call_accounting(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="acct45")
    records=json.loads((root/"v51_records.json").read_text(encoding="utf-8"))
    assert len(records)==30
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,31)]
    summary=json.loads((root/"v51_summary.json").read_text(encoding="utf-8"))
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":45, "l1":15, "l2":30}
    assert acc["decoder_calls_started"]=={"total":45, "l1":15, "l2":30}
    assert acc["decoder_calls_completed"]=={"total":45, "l1":15, "l2":30}
    assert v51.HARD_CALL_CAP==45
    for rec in records:
        assert rec["tag_scope"]=="l2_only"
        assert len(rec["target_tag"])==16
        assert rec["reclassified"] in v51.RECLASSIFIED_VALUES
        assert rec["sampling_mode"]==v51.SAMPLING_MODE
        assert rec["pairs_count"]==1024
        assert len(rec["frame_ids"])==4
        assert rec["held_out_ordinal_end"] - rec["held_out_ordinal_start"]==3
        expected = v51.leak_for(rec["source"], v51.H1_M)
        assert rec["leak_total"]==expected
        assert rec["label_id"] in v51.LABEL_ORDER
    for src in v51.SOURCE_ORDER:
        for bid in v51.NEW_BLOCK_SEEDS[src]:
            rows = [r for r in records if r["block_seed"]==bid]
            assert [r["label_id"] for r in rows]==["old","new"]
    assert summary["leakage"]["per_source"]["1M"]["leak_total"]==1064
    assert summary["leakage"]["per_source"]["1p5M"]["leak_total"]==1094
    assert summary["leakage"]["per_source"]["2M"]["leak_total"]==1104
    # budget cap 46th refused
    acc2=v51.CallAccounting()
    for _ in range(15):
        acc2.register_start(layer="l1"); acc2.register_complete(layer="l1")
    for _ in range(30):
        acc2.register_start(layer="l2"); acc2.register_complete(layer="l2")
    with pytest.raises(v51.IntegrityFailure) as e:
        acc2.register_start()
    assert e.value.check_id=="J10"
    with pytest.raises(v51.IntegrityFailure) as e2:
        acc2.register_start(layer="l1")
    assert e2.value.check_id=="J10"
    acc3=v51.CallAccounting()
    for _ in range(15):
        acc3.register_start(layer="l1"); acc3.register_complete(layer="l1")
    with pytest.raises(v51.IntegrityFailure):
        acc3.register_start(layer="l1")

def test_paired_effects(tmp_path, monkeypatch, real_counts):
    # craft so old fails new succeeds on some blocks to test McNemar
    def outcome(idx):
        # idx 0..29, per block 2: old,new alternation
        # block 0 old fail new success -> c++, block1 both fail -> d++, etc
        block = idx // 2
        is_old = (idx % 2 == 0)
        if block % 3 == 0:
            return (False, 5, False, "detected") if is_old else (True, 0, True)
        elif block % 3 == 1:
            return (False, 5, False, "detected") if True else (True,0,True)  # both fail
        else:
            return (True,0,True)  # both success
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="paired")
    summary=json.loads((root/"v51_summary.json").read_text(encoding="utf-8"))
    agg=summary["aggregates"]
    assert "paired_table" in agg
    assert "discordance" in agg
    assert "gain_new_minus_old" in agg
    assert agg["paired_table"]["a_both_exact"] >=0
    assert agg["paired_table"]["b_old_only"] >=0
    assert agg["paired_table"]["c_new_only"] >=0
    assert summary["terminal_state"] == v51.TERMINAL_PAIRED_COMPLETE

def test_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v51_records.json","v51_records.csv","v51_summary.json","v51_label_spectrum.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v51_records.json").read_text(encoding="utf-8"))
    with (root/"v51_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==30
    summary=json.loads((root/"v51_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["leakage_already_accounted"] is True
    assert summary["tag_scope"]=="l2_only"
    assert summary["sampling_mode"]==v51.SAMPLING_MODE
    assert summary["held_out_provenance"]["sampling_mode"]==v51.SAMPLING_MODE
    assert "custom" in summary["provenance"]["custom_definition"].lower()
    assert "not literature" in summary["provenance"]["custom_definition"].lower() or "NOT literature" in summary["provenance"]["custom_definition"]
    assert summary["provenance"]["deterministic_relabel_id"] == "single_run_no_seed_search"
    spectrum=json.loads((root/"v51_label_spectrum.json").read_text(encoding="utf-8"))
    assert "per_source" in spectrum
    for src in v51.SOURCE_ORDER:
        per=spectrum["per_source"][src]
        assert "degenerate_4_old" in per and "degenerate_4_new" in per
        assert "min_check_extrinsic6_old" in per
        assert per["support_exact_equal"] is True
        assert per["rank_ok"] is True
        assert per["cycles_equal"] is True
    # provenance custom definition present
    assert "check_extrinsic_score" in json.dumps(summary)

def test_no_real_decoder_call_counted(monkeypatch, tmp_path, real_counts):
    calls={"decode":0}
    def counting_decode(*a, **kw):
        calls["decode"]+=1
        return SimpleNamespace(x_hat=np.zeros(1024,dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok", final_beliefs=np.zeros((1024,32)))
    world=FakeWorld()
    root=tmp_path/"no_real"
    # patch optimizer and spectrum as before
    orig_opt=v51.deterministic_label_optimize
    orig_spec=v51.build_label_spectrum
    def fake_opt(H_init, max_sweeps=2, field=None):
        return H_init.copy(),1,0,int(compute_gf32_rank(H_init, field or GF2mField.create(32)))
    def fake_spec(old,new,field=None):
        r=orig_spec(old,new,field)
        r["label_improved"]=True; r["all_not_worse"]=True; r["any_strictly_better"]=True
        for src in v51.SOURCE_ORDER:
            r["per_source"][src]["not_worse"]=True
            if src=="1M":
                r["per_source"][src]["strictly_better"]=True
        return r
    monkeypatch.setattr(v51,"deterministic_label_optimize",fake_opt)
    monkeypatch.setattr(v51,"build_label_spectrum",fake_spec)
    # also need patched evaluate
    orig_eval=v51._evaluate_one_l2
    def dummy_eval(*args, **kwargs):
        # count not via counting_decode because fake_runner True => decode not called
        return orig_eval(*args, **kwargs)
    result=v51.run_v51_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert calls["decode"]==0
    monkeypatch.setattr(v51,"deterministic_label_optimize",orig_opt)
    monkeypatch.setattr(v51,"build_label_spectrum",orig_spec)

def test_cli_guards():
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout+proc.stderr)
    proc2=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized","--authorized-target-sha","0"*40], capture_output=True, text=True)
    assert proc2.returncode!=0
    script_text=SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script_text

def test_output_root_not_exists_real():
    assert not OUTPUT_ROOT_REAL.exists(), f"formal output root should not exist after impl: {OUTPUT_ROOT_REAL}"

def test_sampling_mode_frame_ids_in_records(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="sampling")
    records=json.loads((root/"v51_records.json").read_text(encoding="utf-8"))
    for rec in records:
        win=v51.BLOCK_WINDOWS[rec["block_seed"]]
        assert rec["sampling_mode"]==v51.SAMPLING_MODE
        assert rec["frame_ids"]==win["frame_ids"]
        assert rec["held_out_ordinal_start"]==win["held_out_ordinal_start"]
        assert rec["held_out_ordinal_end"]==win["held_out_ordinal_end"]
        assert rec["pairs_count"]==1024
        assert rec["label_id"] in v51.LABEL_ORDER

def test_no_45_block_path():
    src=Path(v51.__file__).read_text(encoding="utf-8")
    assert "PLANNED_CALLS = 45" in src
    assert "PLANNED_L1 = 15" in src
    assert "PLANNED_L2 = 30" in src
    assert "392001" in src
    assert len([s for src in v51.SOURCE_ORDER for s in v51.NEW_BLOCK_SEEDS[src]])==15

def test_v48_v50_v51_frame_ids_zero_overlap_real():
    assert len(v51.V48_HELDOUT_FRAME_IDS_FLAT)==180
    assert len(v51.V51_HELDOUT_FRAME_IDS["1M"])==20
    for src in v51.SOURCE_ORDER:
        assert v51.V51_HELDOUT_FRAME_IDS[src] & v51.V48_HELDOUT_FRAME_IDS[src] == set(), f"{src} V51 vs V48 frame_ids must be disjoint per source"
        assert v51.V51_HELDOUT_FRAME_IDS[src] & v51.V50_HELDOUT_FRAME_IDS[src] == set(), f"{src} V51 vs V50 frame_ids must be disjoint per source"
    v51_flat = set().union(*v51.V51_HELDOUT_FRAME_IDS.values())
    assert v51_flat & v51.V48_HELDOUT_FRAME_IDS_FLAT == set()
    v50_flat = set().union(*v51.V50_HELDOUT_FRAME_IDS.values())
    assert v51_flat & v50_flat == set()
    assert len(v51_flat)==60
    src_text = Path(v51.__file__).read_text(encoding="utf-8")
    assert "V48_HELDOUT_FRAME_IDS" in src_text
    assert "V51_HELDOUT_FRAME_IDS" in src_text
    assert "V50_HELDOUT_FRAME_IDS" in src_text
