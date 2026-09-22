"""Focused V48P0 tests (decoder-free, fake-runner) for held-out 45-block deterministic spread.

All tests are fake-runner / stub-decode. No production decoder invoked, official V48 output root never created.
Covers: 45-block mapping, TRAIN/held-out zero overlap, 256/1024 validation, 90-call accounting+91st refusal, tag L2-only,
sampling_mode, frame_ids, leakage, gates 35/45 & 10/15, CLI guards, writer contract, sentinel.
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

from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_tag_64, load_v25_channel_counts
from comparison_bench.formal_ir import v48_heldout_confirm as v48

SCRIPT_PATH = Path(__file__).resolve().parents[2].parent / "scripts" / "execute_v48_heldout_confirm.py"
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v48_heldout_confirm.py"
    if not SCRIPT_PATH.exists():
        SCRIPT_PATH = Path("D:/Code/HD-QKD_Polar_Comparison/scripts/execute_v48_heldout_confirm.py")

OUTPUT_ROOT_REAL = Path(__file__).resolve().parents[2] / "outputs_comparison" / "formal_ir_methods" / "v48_heldout_confirm" / "run_01"
if not OUTPUT_ROOT_REAL.exists():
    OUTPUT_ROOT_REAL = Path("D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01")

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
        for source in v48.SOURCE_ORDER:
            for seed in v48.CONSTRUCTION_SEEDS["lane_c"][source]:
                self.constructors["lane_c"](source=source, seed=seed)
        records: list[dict] = []
        for source in v48.SOURCE_ORDER:
            for seed in (921001, 921002, 921003):
                records.append({"lane": "lane_a", "source": source, "construction_seed": seed, "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"})
            for seed in (922001, 922002, 922003):
                records.append({"lane": "lane_b", "source": source, "construction_seed": seed, "matrix_id": f"lane_b_{source}_s{seed}", "shape": "[4, 1024]"})
        for mid, met in self.metrics_by_id.items():
            records.append(dict(met))
        for i in range(6):
            records.append({"lane": "lane_c", "source": "1M", "construction_seed": 999000+i, "matrix_id": f"lane_c_1M_s{999000+i}", "shape": "[4, 1024]", "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True, "position_permutations": [[0]]})
        records = records[:27]
        for src in v48.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v48._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    counter = {"n": 0}
    def _patched_eval(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec, q=None, exact_u1=True, syndrome_ok_l1=True, iterations_l1=5, entropy=4.2, mean_abs=0.03, runtime_l1=0.001):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "source": source, "block_seed": block_seed})
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
        win = v48.BLOCK_WINDOWS[block_seed]
        reclassified = v48.classify_reclassified(exact_l2, syn_ok, tag_ok)
        return {
            "source": source, "block_seed": block_seed,
            "construction_seed": spec["construction_seed"], "matrix_id": spec["matrix_id"],
            "h1_matrix_id": v48.H1_MATRIX_ID,
            "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
            "pairs_count": 1024, "sampling_mode": v48.SAMPLING_MODE,
            "errors_initial": int(errors_initial), "errors_final": int(final),
            "exact_l2": bool(exact_l2), "exact_u1": bool(exact_u1_local), "exact_full": bool(exact_u1_local and exact_l2),
            "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syn_ok_l1_local),
            "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": v48.TAG_SCOPE, "reclassified": reclassified,
            "iterations_l1": 5, "iterations_l2": 5 if exact_l2 else 90,
            "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
            "leak_total": int(spec.get("leak_total", v48.leak_for(source, v48.H1_M))),
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
        }
    monkeypatch.setattr(v48, "_evaluate_one_l2", _patched_eval)
    world = FakeWorld()
    root = tmp_path / name
    result = v48.run_v48_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# ---- 45-block mapping ----
def test_45_block_mapping_deterministic():
    assert len(v48.FROZEN_WORKLOAD) == 45
    assert len(v48.NEW_BLOCK_SEEDS["1M"]) == 15
    assert len(v48.NEW_BLOCK_SEEDS["1p5M"]) == 15
    assert len(v48.NEW_BLOCK_SEEDS["2M"]) == 15
    flat = [s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]]
    assert flat == [390128,390129,390130,390131,390132,390133,390134,390135,390136,390137,390138,390139,390140,390141,390142,
                    390228,390229,390230,390231,390232,390233,390234,390235,390236,390237,390238,390239,390240,390241,390242,
                    390328,390329,390330,390331,390332,390333,390334,390335,390336,390337,390338,390339,390340,390341,390342]
    # window mapping 1M
    assert v48.HELDOUT_STARTS["1M"] == [0,28,56,84,113,141,169,198,226,254,282,311,339,367,396]
    assert v48.HELDOUT_STARTS["1p5M"] == [0,39,78,117,157,196,235,275,314,353,392,432,471,510,550]
    assert v48.HELDOUT_STARTS["2M"] == [0,51,103,155,207,258,310,362,414,466,517,569,621,673,725]
    # per block ordinal binding
    for src in v48.SOURCE_ORDER:
        for idx, bid in enumerate(v48.NEW_BLOCK_SEEDS[src]):
            win = v48.BLOCK_WINDOWS[bid]
            assert win["held_out_ordinal_start"] == v48.HELDOUT_STARTS[src][idx]
            assert win["held_out_ordinal_end"] == win["held_out_ordinal_start"] + 3
            assert win["pairs_count"] == 1024
            assert win["sampling_mode"] == v48.SAMPLING_MODE
            assert len(win["frame_ids"]) == 4
            # 256 per frame
            assert win["pairs_count"] == 4 * v48.PAIRS_PER_FRAME
            # start formula floor(j*(H-4)/14)
            H = v48.HELDOUT_H[src]
            expected = (idx * (H - 4)) // 14
            assert win["held_out_ordinal_start"] == expected
    # windows non-overlap per source and cover full hold
    for src in v48.SOURCE_ORDER:
        windows = [(v48.BLOCK_WINDOWS[bid]["held_out_ordinal_start"], v48.BLOCK_WINDOWS[bid]["held_out_ordinal_end"]) for bid in v48.NEW_BLOCK_SEEDS[src]]
        for i in range(len(windows)-1):
            assert windows[i][1] < windows[i+1][0], f"overlap {src} {windows[i]} vs {windows[i+1]}"
        assert windows[0][0] == 0
        assert windows[-1][1] == v48.HELDOUT_H[src] - 1

def test_45_to_180_frame_ids_deterministic():
    all_fids: list[int] = []
    for bid in [s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]]:
        win = v48.BLOCK_WINDOWS[bid]
        fids = win["frame_ids"]
        assert len(fids) == 4
        all_fids.extend(fids)
    assert len(all_fids) == 180
    # frame_ids unique across 45 blocks (since windows non-overlap and base separated)
    assert len(set(all_fids)) == 180
    # exact mapping for first and last per source
    assert v48.BLOCK_WINDOWS[390128]["frame_ids"] == [v48.HELDOUT_BASE_GLOBAL["1M"]+0, v48.HELDOUT_BASE_GLOBAL["1M"]+1, v48.HELDOUT_BASE_GLOBAL["1M"]+2, v48.HELDOUT_BASE_GLOBAL["1M"]+3]
    assert v48.BLOCK_WINDOWS[390142]["frame_ids"] == [v48.HELDOUT_BASE_GLOBAL["1M"]+396, v48.HELDOUT_BASE_GLOBAL["1M"]+397, v48.HELDOUT_BASE_GLOBAL["1M"]+398, v48.HELDOUT_BASE_GLOBAL["1M"]+399]
    assert v48.BLOCK_WINDOWS[390328]["frame_ids"][0] == v48.HELDOUT_BASE_GLOBAL["2M"]+0
    assert v48.BLOCK_WINDOWS[390342]["frame_ids"][-1] == v48.HELDOUT_BASE_GLOBAL["2M"]+728

# ---- TRAIN/held-out zero overlap ----
def test_train_heldout_zero_overlap():
    # FORBIDDEN 96 must be disjoint from new 45
    flat45 = {s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]}
    assert flat45 & v48.FORBIDDEN_96 == set()
    assert len(v48.FORBIDDEN_96) == 96
    assert len(v48.FORBIDDEN_78) == 78
    assert len(v48.FORBIDDEN_87) == 87
    # also held-out frames vs TRAIN counts provenance: loader string must be TRAIN
    src_text = Path(v48.__file__).read_text(encoding="utf-8")
    assert "load_v25_channel_counts" in src_text
    assert "channel_counts.npz" in src_text
    # sampling_mode must not be random
    assert v48.SAMPLING_MODE == "deterministic_spread_four_consecutive_frames"
    assert "sample_empirical_block(held_out_pool" not in src_text

def test_no_random_sampling_path():
    src = Path(v48.__file__).read_text(encoding="utf-8")
    # ensure the banned string not present as call with held_out_pool random extraction
    assert "sample_empirical_block(held_out_pool" not in src

# ---- 256/1024 validation ----
def test_256_1024_validation():
    assert v48.PAIRS_PER_FRAME == 256
    assert v48.PAIRS_PER_BLOCK == 1024
    assert v48.FRAMES_PER_BLOCK == 4
    for bid, win in v48.BLOCK_WINDOWS.items():
        assert win["pairs_count"] == 1024
        assert win["pairs_count"] == win["frame_ids"].__len__() * 256
        assert win["held_out_ordinal_end"] - win["held_out_ordinal_start"] == 3

# ---- registry ----
def test_registry_accepts_frozen_45():
    ok, msg = v48.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    flat = [s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]]
    assert len(flat) == 45
    overlap = set(flat) & v48.FORBIDDEN_96
    assert overlap == set()
    for src in v48.SOURCE_ORDER:
        seeds = v48.NEW_BLOCK_SEEDS[src]
        assert seeds == sorted(seeds)
        assert seeds[-1] - seeds[0] == 14
        assert seeds[1] - seeds[0] == 1

def test_registry_rejects_overlaps():
    for probe in [360101, 390101, 390106, 390107, 390110, 390113, 390116, 390119, 390122, 390125, 390225, 390325]:
        reg = {src: list(seeds) for src, seeds in v48.NEW_BLOCK_SEEDS.items()}
        reg["2M"][0] = probe
        ok, _ = v48.validate_seed_registry(reg)
        assert not ok, probe

def test_registry_rejects_duplicate():
    reg = {src: list(seeds) for src, seeds in v48.NEW_BLOCK_SEEDS.items()}
    reg["1M"][1] = reg["1M"][0]
    ok, msg = v48.validate_seed_registry(reg)
    assert not ok and "duplicate" in msg.lower()

# ---- H1 rebuild ----
def test_h1_rebuild_and_leakage(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    first = v48.reconstruct_v48_matrices(authority, field=field, constructors=world.constructors)
    second = v48.reconstruct_v48_matrices(authority, field=field, constructors=world.constructors)
    for k in [("lane_c","1M"),("lane_c","1p5M"),("lane_c","2M")]:
        assert np.array_equal(first[k][0], second[k][0])
    h1_full = first[("H1","L1")][0]
    assert h1_full.shape == (16,1024)
    from comparison_bench.formal_ir.v35_algorithm_development import compute_gf32_rank
    assert compute_gf32_rank(h1_full, field) == 16
    # leakage single-arm
    assert v48.leak_for("1M") == 1064
    assert v48.leak_for("1p5M") == 1094
    assert v48.leak_for("2M") == 1104

def test_sentinel_and_tag_import(real_counts):
    res = v48.single_arm_binding_preflight(real_counts)
    assert set(res.keys()) == set(v48.SOURCE_ORDER)
    for src, chk in res.items():
        assert chk["probe_block_seed"] == v48.PREFLIGHT_BLOCK_SEEDS[src]
        assert chk["v35_tag_import_ok"] is True
        assert chk["tag_scope_l2_only"] is True
        assert chk["leakage_accounted"] is True
        assert chk["heldout_reachable_ok"] is True
        assert chk["prior_train_only_ok"] is True
        assert chk["sampling_mode"] == v48.SAMPLING_MODE
        assert chk["pairs_count"] == 1024
        assert len(chk["frame_ids"]) == 4

# ---- tag L2-only ----
def test_tag_l2_only_oracle_removal():
    empty = np.empty(0, dtype=np.uint8)
    x2 = np.array([1,2,3,4,5], dtype=np.uint8)
    tag_a = compute_tag_64(empty, x2)
    tag_b = compute_tag_64(empty, x2)
    assert tag_a == tag_b
    assert v48.compute_l2_tag(x2) == tag_a
    x2_alt = x2.copy()
    x2_alt[0] = (int(x2_alt[0]) + 1) % 32
    tag_alt = compute_tag_64(empty, x2_alt)
    assert tag_alt != tag_a
    assert len(tag_a) == 16
    int(tag_a, 16)
    src = Path(v48.__file__).read_text(encoding="utf-8")
    assert "compute_tag_64(x1_true" not in src
    assert v48.TAG_SCOPE == "l2_only"
    assert v48.classify_reclassified(True, True, True) == "exact"
    assert v48.classify_reclassified(False, True, False) == "detected_verification_failure"
    assert v48.classify_reclassified(False, False, False) == "decoder_non_syndrome_failure"
    assert v48.classify_reclassified(False, True, True) == "undetected_accepted_wrong"

def test_no_canonical_reimplementation():
    src = Path(v48.__file__).read_text(encoding="utf-8")
    assert "def compute_tag_64" not in src
    assert "from comparison_bench.formal_ir.v35_algorithm_development import" in src
    assert "compute_tag_64" in src

# ---- 90-call accounting ----
def test_90_call_accounting(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="acct90")
    records=json.loads((root/"v48_records.json").read_text(encoding="utf-8"))
    assert len(records)==45
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,46)]
    summary=json.loads((root/"v48_summary.json").read_text(encoding="utf-8"))
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":90, "l1":45, "l2":45}
    assert acc["decoder_calls_started"]=={"total":90, "l1":45, "l2":45}
    assert acc["decoder_calls_completed"]=={"total":90, "l1":45, "l2":45}
    assert v48.HARD_CALL_CAP==90
    for rec in records:
        assert rec["tag_scope"]=="l2_only"
        assert len(rec["target_tag"])==16
        assert rec["reclassified"] in v48.RECLASSIFIED_VALUES
        assert rec["sampling_mode"]==v48.SAMPLING_MODE
        assert rec["pairs_count"]==1024
        assert len(rec["frame_ids"])==4
        assert rec["held_out_ordinal_end"] - rec["held_out_ordinal_start"]==3
        expected = v48.leak_for(rec["source"], v48.H1_M)
        assert rec["leak_total"]==expected
    # leakage table
    assert summary["leakage"]["per_source"]["1M"]["leak_total"]==1064
    assert summary["leakage"]["per_source"]["1p5M"]["leak_total"]==1094
    assert summary["leakage"]["per_source"]["2M"]["leak_total"]==1104
    # budget cap 91st refused
    acc2=v48.CallAccounting()
    for _ in range(45):
        acc2.register_start(layer="l1"); acc2.register_complete(layer="l1")
    for _ in range(45):
        acc2.register_start(layer="l2"); acc2.register_complete(layer="l2")
    with pytest.raises(v48.IntegrityFailure) as e:
        acc2.register_start()
    assert e.value.check_id=="J10"
    with pytest.raises(v48.IntegrityFailure) as e2:
        acc2.register_start(layer="l1")
    assert e2.value.check_id=="J10"
    # also l1 46th alone refused
    acc3=v48.CallAccounting()
    for _ in range(45):
        acc3.register_start(layer="l1"); acc3.register_complete(layer="l1")
    with pytest.raises(v48.IntegrityFailure):
        acc3.register_start(layer="l1")

def test_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v48_records.json","v48_records.csv","v48_summary.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v48_records.json").read_text(encoding="utf-8"))
    with (root/"v48_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==45
    summary=json.loads((root/"v48_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["leakage_already_accounted"] is True
    assert summary["tag_scope"]=="l2_only"
    assert summary["sampling_mode"]==v48.SAMPLING_MODE
    assert summary["held_out_provenance"]["sampling_mode"]==v48.SAMPLING_MODE

def test_gate_truth_table(tmp_path, monkeypatch, real_counts):
    cases = [
        (True, v48.TERMINAL_HELDOUT_PASS),
        (False, v48.TERMINAL_HELDOUT_FAIL),
    ]
    for passed, expected in cases:
        term, _, _ = v48.determine_v48_terminal(True, passed)
        assert term==expected
    term, _, _ = v48.determine_v48_terminal(False, True)
    assert term==v48.TERMINAL_EVIDENCE_INVALID
    # integrated: 35/45 pass
    def make_exact_map(n_exact):
        def fn(idx):
            return (True,0,True) if idx < n_exact else (False,5,True,"detected")
        return fn
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, make_exact_map(35), name="gate35")
    summary=json.loads((root/"v48_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_evaluation"]["g1_overall_exact_full_ge_35_of_45"]["pass"] is True
    # per source 10/15: make 1M 10, 1p5M 10, 2M 15 = pass
    # We'll craft explicit: first 15 calls are 1M (0-14), next 15 1p5M (15-29), last 15 2M (30-44)
    def mixed_gate(idx):
        # 1M 10/15 pass, 1p5M 10/15, 2M 15/15
        if idx <10: return (True,0,True)
        if idx <15: return (False,5,True,"detected")
        if 15 <= idx <25: return (True,0,True)
        if 25 <= idx <30: return (False,5,True,"detected")
        return (True,0,True)
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, mixed_gate, name="gate_per_source")
    summary2=json.loads((root2/"v48_summary.json").read_text(encoding="utf-8"))
    assert summary2["gate_evaluation"]["g2_every_source_ge_10_of_15"]["pass"] is True
    assert summary2["terminal_state"]==v48.TERMINAL_HELDOUT_PASS

def test_wrong_undetected_two_states(tmp_path, monkeypatch, real_counts):
    def mixed(idx):
        if idx==0:
            return (False,10,True,"undetected")
        if idx==1:
            return (False,10,True,"detected")
        return (True,0,True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, mixed, name="undet")
    summary=json.loads((root/"v48_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_evaluation"]["g3_undetected_zero"]["pass"] is False
    assert summary["gate_evaluation"]["undetected_accepted_wrong"] == 1
    assert summary["undetected_anomaly"] is True
    assert summary["terminal_state"]==v48.TERMINAL_HELDOUT_FAIL

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
    result=v48.run_v48_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert calls["decode"]==0

def test_output_root_not_exists_real():
    # formal run_01 must not exist after implementation (decoder-free)
    assert not OUTPUT_ROOT_REAL.exists(), f"formal output root should not exist after impl: {OUTPUT_ROOT_REAL}"

def test_p3_registry_zero_overlap():
    flat45 = {s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]}
    assert flat45.isdisjoint(v48.FORBIDDEN_96)
    assert len(flat45)==45
    # per source x28+ continuity
    for src in v48.SOURCE_ORDER:
        seeds = v48.NEW_BLOCK_SEEDS[src]
        assert seeds[0] % 100 == 28  # 390128 etc
        assert seeds[-1] - seeds[0] == 14

def test_p1_rebuild_strict_match(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    auth = world.authority_file(tmp_path)
    mats = v48.reconstruct_v48_matrices(auth, field=field, constructors=world.constructors)
    # strict match: 3 L2 + 1 H1
    assert len(mats)==4
    assert ("H1","L1") in mats
    for src in v48.SOURCE_ORDER:
        assert ("lane_c", src) in mats
    # tag import
    empty=np.empty(0,dtype=np.uint8)
    x2=np.array([1,2,3], dtype=np.uint8)
    t=compute_tag_64(empty, x2)
    assert len(t)==16

def test_sampling_mode_frame_ids_in_records(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="sampling")
    records=json.loads((root/"v48_records.json").read_text(encoding="utf-8"))
    for rec in records:
        win=v48.BLOCK_WINDOWS[rec["block_seed"]]
        assert rec["sampling_mode"]==v48.SAMPLING_MODE
        assert rec["frame_ids"]==win["frame_ids"]
        assert rec["held_out_ordinal_start"]==win["held_out_ordinal_start"]
        assert rec["held_out_ordinal_end"]==win["held_out_ordinal_end"]
        assert rec["pairs_count"]==1024

def test_no_30_block_path():
    src=Path(v48.__file__).read_text(encoding="utf-8")
    # ensure 60-call / 30-block strings not present as active path (except maybe comments)
    # We check that PLANNED_CALLS is 90 not 60, and no G1 24/30
    assert "PLANNED_CALLS = 90" in src
    assert "G1_MIN_EXACT_TOTAL = 35" in src
    assert "G2_MIN_PER_SOURCE = 10" in src
    # 30-block ids should not be defined as limit
    flat=len([s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]])
    assert flat==45

# ---- Task 7: real parquet anchor tests ----

def test_real_parquet_anchor_390128():
    # Task 7.1: read 390128 frame 1600-1603 assert 1024 pairs and head/tail consistency
    import pandas as pd
    v48._clear_heldout_cache()
    alice, bob = v48.load_heldout_block(390128)
    assert len(alice) == 1024
    assert len(bob) == 1024
    # symbol range 0..1023
    assert int(alice.min()) >= 0 and int(alice.max()) < 1024
    assert int(bob.min()) >= 0 and int(bob.max()) < 1024
    # direct parquet query for ground truth
    parquet_path = v48._heldout_parquet_path("1M")
    df = pd.read_parquet(parquet_path)
    win = v48.BLOCK_WINDOWS[390128]
    fids = win["frame_ids"]
    assert fids == [1600, 1601, 1602, 1603]
    filt = df[df["frame_id"].isin(fids)].sort_values(["frame_id", "pair_idx"])
    assert len(filt) == 1024
    alice_direct = filt["alice_symbol"].to_numpy()
    bob_direct = filt["bob_symbol"].to_numpy()
    assert (alice == alice_direct).all()
    assert (bob == bob_direct).all()
    # head/tail consistency
    assert int(alice[0]) == int(filt.iloc[0]["alice_symbol"])
    assert int(bob[0]) == int(filt.iloc[0]["bob_symbol"])
    assert int(alice[-1]) == int(filt.iloc[-1]["alice_symbol"])
    assert int(bob[-1]) == int(filt.iloc[-1]["bob_symbol"])
    # per-frame 256 and ordering
    for fid in fids:
        sub = filt[filt["frame_id"] == fid]
        assert len(sub) == 256
        assert list(sub["pair_idx"]) == list(range(256))

def test_monkeypatch_sample_empirical_block_still_succeeds(tmp_path, monkeypatch, real_counts):
    # Task 7.2: monkeypatch sample_empirical_block to throw, production/fake still must succeed
    def _boom(*a, **kw):
        raise RuntimeError("sample_empirical_block should not be called in V48 production")
    monkeypatch.setattr(v48, "sample_empirical_block", _boom)
    # also patch the original module import path that sentinel might use
    import comparison_bench.formal_ir.v35_algorithm_development as v35mod
    monkeypatch.setattr(v35mod, "sample_empirical_block", _boom)
    v48._clear_heldout_cache()
    # fake runner
    outcome = make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="monkey_fake")
    records = json.loads((root / "v48_records.json").read_text(encoding="utf-8"))
    assert len(records) == 45
    # production-like fake also uses parquet; real sentinel should also not have called boom
    # explicit check: load one more block directly still works despite boom
    alice, bob = v48.load_heldout_block(390228)
    assert len(alice) == 1024
    v48._clear_heldout_cache()

def test_tamper_frame_id_or_missing_row_fails_before_decoder(tmp_path, monkeypatch, real_counts):
    # Task 7.3: tamper frame ID or delete row must fail before decoder call
    import pandas as pd
    v48._clear_heldout_cache()
    real_df = v48._load_heldout_df("1M")
    # tamper 1: change one frame_id
    tampered = real_df.copy()
    # pick first row of frame 1600 and change to illegal frame 9999
    mask = tampered["frame_id"] == 1600
    first_idx = tampered[mask].index[0]
    tampered.loc[first_idx, "frame_id"] = 9999
    # inject tampered cache
    v48._HELDOUT_DF_CACHE["1M"] = tampered
    with pytest.raises(v48.IntegrityFailure) as exc:
        v48.load_heldout_block(390128)
    assert exc.value.check_id == "J4"
    v48._clear_heldout_cache()
    # tamper 2: delete one row from 1600
    real_df2 = v48._load_heldout_df("1M")
    tampered2 = real_df2[~((real_df2["frame_id"] == 1600) & (real_df2["pair_idx"] == 0))].copy()
    v48._HELDOUT_DF_CACHE["1M"] = tampered2
    with pytest.raises(v48.IntegrityFailure) as exc2:
        v48.load_heldout_block(390128)
    assert exc2.value.check_id == "J4"
    v48._clear_heldout_cache()
    # tamper via workload must fail before decoder invoked
    # inject tampered again and run diagnostic with counting decoder
    v48._HELDOUT_DF_CACHE["1M"] = tampered  # frame_id tamper
    calls = {"decode": 0}
    def counting_decode(*a, **kw):
        calls["decode"] += 1
        return SimpleNamespace(x_hat=np.zeros(1024, dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok", final_beliefs=np.zeros((1024, 32)))
    world = FakeWorld()
    root = tmp_path / "tamper_before_decode"
    # run should raise IntegrityFailure before any decode call (caught as invalid evidence)
    # use direct _run_workload_calls path via run_v48_diagnostic fake
    # monkeypatch _load_heldout_df to return tampered for 1M
    def _fake_load(source):
        if source == "1M":
            return tampered
        return v48._HELDOUT_DF_CACHE.get(source) or real_df2
    # Instead use cache injection already; run diagnostic
    try:
        result = v48.run_v48_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
        # If it returned invalid evidence, decode should still be zero
        assert calls["decode"] == 0
        assert result["terminal_state"] == v48.TERMINAL_EVIDENCE_INVALID
    finally:
        v48._clear_heldout_cache()
        # ensure cache cleared for subsequent tests
        if "1M" in v48._HELDOUT_DF_CACHE:
            v48._clear_heldout_cache()

def test_validate_train_heldout_isolation_real():
    ok, msg = v48.validate_train_heldout_isolation()
    assert ok, msg
    # check zero overlap explicitly per source
    for src in v48.SOURCE_ORDER:
        tr_lo, tr_hi = v48.TRAIN_FRAME_RANGES[src]
        ho_lo, ho_hi = v48.HELDOUT_FRAME_RANGES[src]
        assert tr_hi < ho_lo, f"{src} train {tr_hi} must be < held-out {ho_lo}"
        for bid in v48.NEW_BLOCK_SEEDS[src]:
            for fid in v48.BLOCK_WINDOWS[bid]["frame_ids"]:
                assert ho_lo <= fid <= ho_hi
                assert not (tr_lo <= fid <= tr_hi)
    # seed registry still checked separately (forbidden 96) but not used as isolation proof
    flat45 = {s for src in v48.SOURCE_ORDER for s in v48.NEW_BLOCK_SEEDS[src]}
    assert flat45.isdisjoint(v48.FORBIDDEN_96)

# ---- new preload tests (task 4) ----

def test_preload_all_45_blocks_180_frame_ids_46080_pairs():
    v48._clear_heldout_cache()
    all_45_block_ids = [bid for src in v48.SOURCE_ORDER for bid in v48.NEW_BLOCK_SEEDS[src]]
    assert len(all_45_block_ids) == 45
    heldout_blocks = {block_id: v48.load_heldout_block(block_id) for block_id in all_45_block_ids}
    assert len(heldout_blocks) == 45
    # total pairs 46080
    total_pairs = sum(len(v[0]) for v in heldout_blocks.values())
    assert total_pairs == 46080
    # 180 unique frame IDs across all blocks
    all_fids = [fid for bid in all_45_block_ids for fid in v48.BLOCK_WINDOWS[bid]["frame_ids"]]
    assert len(all_fids) == 180
    assert len(set(all_fids)) == 180
    # per-block checks already inside load_heldout_block, but verify symbol range and TRAIN zero overlap here
    for bid, (alice, bob) in heldout_blocks.items():
        assert len(alice) == 1024 and len(bob) == 1024
        assert int(alice.min()) >= 0 and int(alice.max()) < 1024
        assert int(bob.min()) >= 0 and int(bob.max()) < 1024
        win = v48.BLOCK_WINDOWS[bid]
        src = win["source"]
        tr_lo, tr_hi = v48.TRAIN_FRAME_RANGES[src]
        for fid in win["frame_ids"]:
            assert not (tr_lo <= fid <= tr_hi)
    v48._clear_heldout_cache()

def test_preload_mapping_used_by_workload():
    src = Path(v48.__file__).read_text(encoding="utf-8")
    # required exact preload line
    assert "heldout_blocks = {block_id: load_heldout_block(block_id) for block_id in all_45_block_ids}" in src
    # workload must read from mapping, not re-read parquet
    assert "alice, bob = heldout_blocks[block_id]" in src
    # alternative exact string with block_seed
    assert "heldout_blocks[block_seed]" in src or "heldout_blocks[block_id]" in src
    # heldout_blocks must be passed into _run_workload_calls
    assert "heldout_blocks" in src
    # all_45_block_ids must be defined before preload
    assert "all_45_block_ids" in src
    # HELDOUT_BASE_GLOBAL comment must be corrected
    assert "actual per-source parquet hold-start frame_id" in src
    assert "synthetic global frame offset" not in src
    # _run_workload_calls must accept heldout_blocks param
    assert "heldout_blocks" in src

def test_delete_last_window_one_row_fails_before_decoder_zero_calls(tmp_path, monkeypatch, real_counts):
    # delete one row from last window 390342 (2M last frame 3644)
    v48._clear_heldout_cache()
    real_df = v48._load_heldout_df("2M")
    # 390342 frames [3641,3642,3643,3644]; delete pair_idx 0 of 3644
    tampered = real_df[~((real_df["frame_id"] == 3644) & (real_df["pair_idx"] == 0))].copy()
    assert len(tampered) == len(real_df) - 1
    v48._HELDOUT_DF_CACHE["2M"] = tampered
    calls = {"decode": 0}
    def counting_decode(*a, **kw):
        calls["decode"] += 1
        return SimpleNamespace(x_hat=np.zeros(1024, dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok", final_beliefs=np.zeros((1024, 32)))
    world = FakeWorld()
    root = tmp_path / "delete_last_window"
    try:
        result = v48.run_v48_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
        assert result["terminal_state"] == v48.TERMINAL_EVIDENCE_INVALID
        assert calls["decode"] == 0
        # accounting must be zero at failure before any decoder call
        summary = json.loads((root / "v48_summary.json").read_text(encoding="utf-8"))
        assert summary["accounting"]["decoder_calls_started"]["total"] == 0
        assert summary["accounting"]["decoder_calls_started"]["l1"] == 0
        assert summary["accounting"]["decoder_calls_started"]["l2"] == 0
        assert summary["terminal_state"] == v48.TERMINAL_EVIDENCE_INVALID
        # invalid notice also present
        assert (root / "v48_invalid_notice.json").exists()
    finally:
        v48._clear_heldout_cache()
