"""Focused V50P0 tests (decoder-free, fake-runner) for 2x2 factorial 90-call.

All tests are fake-runner / stub-decode. No production decoder invoked, official V50 output root never created.
Covers: 15-block mapping, TRAIN/held-out zero overlap, 256/1024, 90-call accounting+91st refusal, tag L2-only,
sampling_mode, frame_ids, leakage, factorial effects, CLI guards, writer contract, sentinel chain/ring/4-cycle, budget caps.
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
from comparison_bench.formal_ir import v50_l2_structure_factorial as v50

SCRIPT_PATH = Path(__file__).resolve().parents[2].parent / "scripts" / "execute_v50_structure_factorial.py"
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v50_structure_factorial.py"
    if not SCRIPT_PATH.exists():
        SCRIPT_PATH = Path("D:/Code/HD-QKD_Polar_Comparison/scripts/execute_v50_structure_factorial.py")

OUTPUT_ROOT_REAL = Path(__file__).resolve().parents[2] / "outputs_comparison" / "formal_ir_methods" / "v50_l2_structure_factorial" / "run_01"
if not OUTPUT_ROOT_REAL.exists():
    OUTPUT_ROOT_REAL = Path("D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/formal_ir_methods/v50_l2_structure_factorial/run_01")

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
        for source in v50.SOURCE_ORDER:
            for seed in v50.CONSTRUCTION_SEEDS["lane_c"][source]:
                self.constructors["lane_c"](source=source, seed=seed)
        records: list[dict] = []
        for source in v50.SOURCE_ORDER:
            for seed in (921001, 921002, 921003):
                records.append({"lane": "lane_a", "source": source, "construction_seed": seed, "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"})
            for seed in (922001, 922002, 922003):
                records.append({"lane": "lane_b", "source": source, "construction_seed": seed, "matrix_id": f"lane_b_{source}_s{seed}", "shape": "[4, 1024]"})
        for mid, met in self.metrics_by_id.items():
            records.append(dict(met))
        for i in range(6):
            records.append({"lane": "lane_c", "source": "1M", "construction_seed": 999000+i, "matrix_id": f"lane_c_1M_s{999000+i}", "shape": "[4, 1024]", "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True, "position_permutations": [[0]]})
        records = records[:27]
        for src in v50.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v50._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    counter = {"n": 0}
    # monkeypatch construct_p0 to lightweight dummy to avoid heavy cycle enumeration in fake tests
    orig_construct = v50.construct_p0_met_prototype
    def dummy_p0(source, det_id, dv_list=None, field=None):
        m = v50.SOURCE_CHECKS[source]
        n = 1024
        H = np.zeros((m, n), dtype=np.uint8)
        # simple construction: 2 per col deterministically, ensure rank etc not needed for fake because reconstruct will validate metrics
        # Instead we return a matrix that passes metrics_for_p0 with dummy support
        # Build support with dv_list
        if dv_list is None:
            dv_list = v50.P0_DV_LIST
        H_supp = np.zeros((m,n), dtype=np.uint8)
        rng = np.random.default_rng(det_id)
        for j,d in enumerate(dv_list):
            rows = rng.choice(m, size=d, replace=False)
            for r in rows:
                H_supp[r,j]=1
        # assign coefficients 1
        H = H_supp.astype(np.uint8)
        # make nonzero entries 1..31 (use 1)
        H[H_supp==1]=1
        return H, H_supp, sum(dv_list), np.zeros(m,dtype=int)
    # also patch metrics to force pass
    orig_metrics = v50.metrics_for_p0
    def dummy_metrics(H, Hs, E, field=None):
        return {"shape": H.shape, "rank": H.shape[0], "E": v50.P0_E, "expected_E": v50.P0_E, "col_deg_min":2, "col_deg_max":3, "row_deg_min":1, "row_deg_max":14, "support_cycles_4":0, "support_cycles_6":8000, "support_cycles_8":90000, "max_degree2_chain":1, "pure_ring_via_graph":0, "full_row_rank":True, "zero_col":0, "zero_row":0, "dc_max_ok":True}
    monkeypatch.setattr(v50, "construct_p0_met_prototype", dummy_p0)
    monkeypatch.setattr(v50, "metrics_for_p0", dummy_metrics)
    def _patched_evaluate(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec, q=None, exact_u1=True, syndrome_ok_l1=True, iterations_l1=5, entropy=4.2, mean_abs=0.03, runtime_l1=0.001):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "source": source, "block_seed": block_seed, "prior_id": spec["prior_id"], "structure_id": spec["structure_id"]})
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
        win = v50.BLOCK_WINDOWS[block_seed]
        reclassified = v50.classify_reclassified(exact_l2, syn_ok, tag_ok)
        return {
            "source": source, "block_seed": block_seed,
            "matrix_id": spec["matrix_id"],
            "h1_matrix_id": v50.H1_MATRIX_ID,
            "frame_ids": list(win["frame_ids"]), "held_out_ordinal_start": int(win["held_out_ordinal_start"]), "held_out_ordinal_end": int(win["held_out_ordinal_end"]),
            "pairs_count": 1024, "sampling_mode": v50.SAMPLING_MODE,
            "errors_initial": int(errors_initial), "errors_final": int(final),
            "exact_l2": bool(exact_l2), "exact_u1": bool(exact_u1_local), "exact_full": bool(exact_u1_local and exact_l2),
            "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syn_ok_l1_local),
            "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": v50.TAG_SCOPE, "reclassified": reclassified,
            "iterations_l1": 5, "iterations_l2": 5 if exact_l2 else 90,
            "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
            "leak_total": int(spec.get("leak_total", v50.leak_for(source, v50.H1_M))),
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
        }
    monkeypatch.setattr(v50, "_evaluate_one_l2", _patched_evaluate)
    world = FakeWorld()
    root = tmp_path / name
    result = v50.run_v50_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    # restore patches for other tests? will be re-patched per call
    monkeypatch.setattr(v50, "construct_p0_met_prototype", orig_construct)
    monkeypatch.setattr(v50, "metrics_for_p0", orig_metrics)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# ---- 15-block mapping ----
def test_15_block_mapping_deterministic():
    assert len(v50.FROZEN_WORKLOAD) == 60
    assert len(v50.NEW_BLOCK_SEEDS["1M"]) == 5
    assert len(v50.NEW_BLOCK_SEEDS["1p5M"]) == 5
    assert len(v50.NEW_BLOCK_SEEDS["2M"]) == 5
    flat = [s for src in v50.SOURCE_ORDER for s in v50.NEW_BLOCK_SEEDS[src]]
    assert flat == [391001,391002,391003,391004,391005,391101,391102,391103,391104,391105,391201,391202,391203,391204,391205]
    # window mapping
    assert v50.BLOCK_WINDOWS[391001]["frame_ids"] == [1614,1615,1616,1617]
    assert v50.BLOCK_WINDOWS[391005]["frame_ids"] == [1727,1728,1729,1730]
    assert v50.BLOCK_WINDOWS[391101]["frame_ids"] == [2232,2233,2234,2235]
    assert v50.BLOCK_WINDOWS[391205]["frame_ids"] == [3148,3149,3150,3151]
    for bid, win in v50.BLOCK_WINDOWS.items():
        assert win["pairs_count"] == 1024
        assert win["sampling_mode"] == v50.SAMPLING_MODE
        assert len(win["frame_ids"]) == 4
        assert win["pairs_count"] == 4 * v50.PAIRS_PER_FRAME
        assert win["held_out_ordinal_end"] - win["held_out_ordinal_start"] == 3
    # per block 4 L2 rows
    for bid in flat:
        rows = [r for r in v50.FROZEN_WORKLOAD if r["block_seed"]==bid]
        assert len(rows)==4
        assert [r["prior_id"] for r in rows]==["TRAIN","TRAIN_VAL","TRAIN","TRAIN_VAL"]
        assert [r["structure_id"] for r in rows]==["lane_c","lane_c","p0_met","p0_met"]

def test_15_to_60_frame_ids_deterministic():
    all_fids: list[int] = []
    for bid in [s for src in v50.SOURCE_ORDER for s in v50.NEW_BLOCK_SEEDS[src]]:
        win = v50.BLOCK_WINDOWS[bid]
        fids = win["frame_ids"]
        all_fids.extend(fids)
    assert len(all_fids) == 60
    assert len(set(all_fids)) == 60

def test_train_heldout_zero_overlap():
    flat15 = {s for src in v50.SOURCE_ORDER for s in v50.NEW_BLOCK_SEEDS[src]}
    assert flat15 & v50.FORBIDDEN_141 == set()
    assert len(v50.FORBIDDEN_141) == 141
    assert len(v50.FORBIDDEN_96) == 96
    # also held-out frames vs TRAIN zero overlap via isolation helper
    ok, msg = v50.validate_train_heldout_isolation()
    assert ok, msg

def test_256_1024_validation():
    assert v50.PAIRS_PER_FRAME == 256
    assert v50.PAIRS_PER_BLOCK == 1024
    assert v50.FRAMES_PER_BLOCK == 4
    for bid, win in v50.BLOCK_WINDOWS.items():
        assert win["pairs_count"] == 1024
        assert win["pairs_count"] == win["frame_ids"].__len__() * 256

def test_registry_accepts_frozen_15():
    ok, msg = v50.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    flat = [s for src in v50.SOURCE_ORDER for s in v50.NEW_BLOCK_SEEDS[src]]
    assert len(flat) == 15
    overlap = set(flat) & v50.FORBIDDEN_141
    assert overlap == set()
    for src in v50.SOURCE_ORDER:
        seeds = v50.NEW_BLOCK_SEEDS[src]
        assert seeds == sorted(seeds)
        assert seeds[-1] - seeds[0] == 4

def test_registry_rejects_overlaps():
    for probe in [360101, 390101, 390106, 390107, 390110, 390113, 390116, 390119, 390122, 390125, 390128, 391001]:
        reg = {src: list(seeds) for src, seeds in v50.NEW_BLOCK_SEEDS.items()}
        # inject overlap into 2M
        reg["2M"][0] = probe
        ok, _ = v50.validate_seed_registry(reg)
        # if probe is not the expected frozen, should fail when overlap with forbidden or duplicate
        # For 391001 which is already in 1M, should fail duplicate
        if probe in v50.FORBIDDEN_141 or probe == 391001:
            assert not ok

def test_registry_rejects_duplicate():
    reg = {src: list(seeds) for src, seeds in v50.NEW_BLOCK_SEEDS.items()}
    reg["1M"][1] = reg["1M"][0]
    ok, msg = v50.validate_seed_registry(reg)
    assert not ok and "duplicate" in msg.lower()

def test_p0_rebuild_matches(tmp_path):
    # dummy metrics already tested via reconstruct, but check E etc via direct construction with light dummy
    # Use real construction for one source but with dummy metrics bypass to avoid heavy cycles: just check dv list
    assert v50.P0_E == 2560
    assert v50.P0_DV_LIST.count(2)==512 and v50.P0_DV_LIST.count(3)==512
    assert v50.P0_DET_IDS["1M"]==500001

def test_tag_l2_only():
    empty = np.empty(0, dtype=np.uint8)
    x2 = np.array([1,2,3,4,5], dtype=np.uint8)
    tag_a = compute_tag_64(empty, x2)
    tag_b = compute_tag_64(empty, x2)
    assert tag_a == tag_b
    assert v50.compute_l2_tag(x2) == tag_a
    x2_alt = x2.copy()
    x2_alt[0] = (int(x2_alt[0]) + 1) % 32
    tag_alt = compute_tag_64(empty, x2_alt)
    assert tag_alt != tag_a
    assert len(tag_a) == 16
    src = Path(v50.__file__).read_text(encoding="utf-8")
    assert "compute_tag_64(x1_true" not in src
    assert v50.TAG_SCOPE == "l2_only"
    assert v50.classify_reclassified(True, True, True) == "exact"
    assert v50.classify_reclassified(False, True, False) == "detected_verification_failure"
    assert v50.classify_reclassified(False, False, False) == "decoder_non_syndrome_failure"
    assert v50.classify_reclassified(False, True, True) == "undetected_accepted_wrong"

def test_sentinel_and_tag_import(real_counts):
    tv = v50.build_train_val_merged_counts(real_counts)
    # patch heavy P0 for speed in sentinel
    orig_c = v50.construct_p0_met_prototype
    orig_m = v50.metrics_for_p0
    def dummy_p0(source, det_id, dv_list=None, field=None):
        m = v50.SOURCE_CHECKS[source]
        n=1024
        H = np.zeros((m,n),dtype=np.uint8)
        Hs=np.zeros((m,n),dtype=np.uint8)
        Hs[0,0]=1
        H[0,0]=1
        return H,Hs,2560,np.zeros(m)
    def dummy_metrics(H,Hs,E,field=None):
        return {"support_cycles_4":0,"max_degree2_chain":1,"pure_ring_via_graph":0,"rank":H.shape[0],"zero_col":0,"zero_row":0,"E":2560,"dc_max_ok":True,"full_row_rank":True,"row_deg_max":14}
    v50.construct_p0_met_prototype = dummy_p0
    v50.metrics_for_p0 = dummy_metrics
    try:
        res = v50.dual_prior_binding_preflight(real_counts, tv)
        assert set(res.keys()) == set(v50.SOURCE_ORDER)
        for src, chk in res.items():
            assert chk["prior_train_ok"] is True
            assert chk["prior_train_val_ok"] is True
            assert chk["priors_differ"] is True
            assert chk["v35_tag_import_ok"] is True
            assert chk["tag_scope_l2_only"] is True
            assert chk["leakage_accounted"] is True
            assert chk["chain_ring_ok"] is True
            assert chk["four_cycle_zero"] is True
            assert chk["sampling_mode"] == v50.SAMPLING_MODE
            assert chk["pairs_count"] == 1024
    finally:
        v50.construct_p0_met_prototype = orig_c
        v50.metrics_for_p0 = orig_m

def test_90_call_accounting(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="acct90")
    records=json.loads((root/"v50_records.json").read_text(encoding="utf-8"))
    assert len(records)==60
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,61)]
    summary=json.loads((root/"v50_summary.json").read_text(encoding="utf-8"))
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":90, "l1":30, "l2":60}
    assert acc["decoder_calls_started"]=={"total":90, "l1":30, "l2":60}
    assert acc["decoder_calls_completed"]=={"total":90, "l1":30, "l2":60}
    assert v50.HARD_CALL_CAP==90
    for rec in records:
        assert rec["tag_scope"]=="l2_only"
        assert len(rec["target_tag"])==16
        assert rec["reclassified"] in v50.RECLASSIFIED_VALUES
        assert rec["sampling_mode"]==v50.SAMPLING_MODE
        assert rec["pairs_count"]==1024
        assert len(rec["frame_ids"])==4
        assert rec["held_out_ordinal_end"] - rec["held_out_ordinal_start"]==3
        expected = v50.leak_for(rec["source"], v50.H1_M)
        assert rec["leak_total"]==expected
        assert rec["prior_id"] in v50.PRIOR_ORDER
        assert rec["structure_id"] in v50.STRUCTURE_ORDER
    # per block order A,B,C,D
    flat = [s for src in v50.SOURCE_ORDER for s in v50.NEW_BLOCK_SEEDS[src]]
    for bid in flat:
        rows = [r for r in records if r["block_seed"]==bid]
        assert [r["prior_id"] for r in rows]==["TRAIN","TRAIN_VAL","TRAIN","TRAIN_VAL"]
        assert [r["structure_id"] for r in rows]==["lane_c","lane_c","p0_met","p0_met"]
    # leakage table
    assert summary["leakage"]["per_source"]["1M"]["leak_total"]==1064
    assert summary["leakage"]["per_source"]["1p5M"]["leak_total"]==1094
    assert summary["leakage"]["per_source"]["2M"]["leak_total"]==1104
    # budget cap 91st refused
    acc2=v50.CallAccounting()
    for _ in range(30):
        acc2.register_start(layer="l1"); acc2.register_complete(layer="l1")
    for _ in range(60):
        acc2.register_start(layer="l2"); acc2.register_complete(layer="l2")
    with pytest.raises(v50.IntegrityFailure) as e:
        acc2.register_start()
    assert e.value.check_id=="J10"
    with pytest.raises(v50.IntegrityFailure) as e2:
        acc2.register_start(layer="l1")
    assert e2.value.check_id=="J10"
    acc3=v50.CallAccounting()
    for _ in range(30):
        acc3.register_start(layer="l1"); acc3.register_complete(layer="l1")
    with pytest.raises(v50.IntegrityFailure):
        acc3.register_start(layer="l1")

def test_factorial_effects(tmp_path, monkeypatch, real_counts):
    # craft so A=10 B=12 C=15 D=17 etc to test effects computed
    # 60 rows: order is block-major, 4 per block. For simplicity make all succeed for C/D, half for A/B
    def outcome(idx):
        # idx 0..59, per block 0:A 1:B 2:C 3:D
        mod = idx % 4
        if mod==0: return (True,0,True) if idx%8==0 else (False,5,True,"detected")
        if mod==1: return (True,0,True)
        if mod==2: return (True,0,True)
        if mod==3: return (True,0,True)
        return (True,0,True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="factorial")
    summary=json.loads((root/"v50_summary.json").read_text(encoding="utf-8"))
    agg=summary["aggregates"]
    assert "factor_counts" in agg
    assert "main_effects" in agg
    assert "E_structure" in agg["main_effects"]
    assert "E_prior" in agg["main_effects"]
    assert "E_interaction" in agg["main_effects"]
    assert "simple_effects" in agg
    # also structure_gain etc descriptive flags via simple
    assert agg["factor_counts"]["A_TRAIN_lane_c"] >=0

def test_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v50_records.json","v50_records.csv","v50_summary.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v50_records.json").read_text(encoding="utf-8"))
    with (root/"v50_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==60
    summary=json.loads((root/"v50_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["leakage_already_accounted"] is True
    assert summary["tag_scope"]=="l2_only"
    assert summary["sampling_mode"]==v50.SAMPLING_MODE
    assert summary["held_out_provenance"]["sampling_mode"]==v50.SAMPLING_MODE
    assert summary["provenance"]["p0_material"].startswith("P0-MET-1")
    assert "401001" not in json.dumps(summary)  # sanity

def test_no_real_decoder_call_counted(monkeypatch, tmp_path, real_counts):
    calls={"decode":0}
    def counting_decode(*a, **kw):
        calls["decode"]+=1
        return SimpleNamespace(x_hat=np.zeros(1024,dtype=np.uint8), syndrome_ok=True, iterations=1, runtime_s=0.001, status="ok", final_beliefs=np.zeros((1024,32)))
    world=FakeWorld()
    root=tmp_path/"no_real"
    # patch heavy P0 as before
    orig_c=v50.construct_p0_met_prototype
    orig_m=v50.metrics_for_p0
    def dummy_p0(source, det_id, dv_list=None, field=None):
        m=v50.SOURCE_CHECKS[source]; n=1024
        H=np.zeros((m,n),dtype=np.uint8); Hs=np.zeros((m,n),dtype=np.uint8); Hs[0,0]=1; H[0,0]=1
        return H,Hs,2560,np.zeros(m)
    def dummy_metrics(H,Hs,E,field=None):
        return {"support_cycles_4":0,"max_degree2_chain":1,"pure_ring_via_graph":0,"rank":H.shape[0],"zero_col":0,"zero_row":0,"E":2560,"dc_max_ok":True,"full_row_rank":True,"row_deg_max":14}
    monkeypatch.setattr(v50, "construct_p0_met_prototype", dummy_p0)
    monkeypatch.setattr(v50, "metrics_for_p0", dummy_metrics)
    result=v50.run_v50_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert calls["decode"]==0
    monkeypatch.setattr(v50, "construct_p0_met_prototype", orig_c)
    monkeypatch.setattr(v50, "metrics_for_p0", orig_m)

def test_cli_guards():
    proc=subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert proc.returncode!=0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout+proc.stderr)
    proc2=subprocess.run([sys.executable, str(SCRIPT_PATH), "--execution-authorized","--authorized-target-sha","0"*40], capture_output=True, text=True)
    assert proc2.returncode!=0
    # it will fail sha binding mismatch or missing authority? but at least not success
    assert proc2.returncode!=0
    script_text=SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script_text

def test_output_root_not_exists_real():
    assert not OUTPUT_ROOT_REAL.exists(), f"formal output root should not exist after impl: {OUTPUT_ROOT_REAL}"

def test_sampling_mode_frame_ids_in_records(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="sampling")
    records=json.loads((root/"v50_records.json").read_text(encoding="utf-8"))
    for rec in records:
        win=v50.BLOCK_WINDOWS[rec["block_seed"]]
        assert rec["sampling_mode"]==v50.SAMPLING_MODE
        assert rec["frame_ids"]==win["frame_ids"]
        assert rec["held_out_ordinal_start"]==win["held_out_ordinal_start"]
        assert rec["held_out_ordinal_end"]==win["held_out_ordinal_end"]
        assert rec["pairs_count"]==1024
        assert rec["prior_id"] in v50.PRIOR_ORDER
        assert rec["structure_id"] in v50.STRUCTURE_ORDER

def test_no_45_block_path():
    src=Path(v50.__file__).read_text(encoding="utf-8")
    assert "PLANNED_CALLS = 90" in src
    assert "PLANNED_L1 = 30" in src
    assert "PLANNED_L2 = 60" in src
    # ensure 45 not as frozen workload for V50
    assert len([s for src in v50.SOURCE_ORDER for s in v50.NEW_BLOCK_SEEDS[src]])==15
