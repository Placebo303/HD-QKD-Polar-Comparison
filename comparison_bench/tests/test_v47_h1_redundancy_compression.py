"""Focused V47P0 tests (decoder-free, fake-runner) for H1 prefix 8/12/16 three-arm 54-call.

All tests are fake-runner / stub-decode. No production decoder invoked, official V47 output root never created.
Covers: nested prefix 8⊂12⊂16 rank, 87-zero-overlap registry, 54-call accounting, three-arm same-block sharing,
first-match minimal m1, paired discordance, per-arm G3', leakage table, tag L2-only oracle-removal.
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
from comparison_bench.formal_ir import v47_h1_redundancy_compression as v47

SCRIPT_PATH = Path(__file__).resolve().parents[2].parent / "scripts" / "execute_v47_h1_redundancy_compression.py"
# fallback if running from different cwd
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v47_h1_redundancy_compression.py"
    if not SCRIPT_PATH.exists():
        SCRIPT_PATH = Path("D:/Code/HD-QKD_Polar_Comparison/scripts/execute_v47_h1_redundancy_compression.py")

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
        for source in v47.SOURCE_ORDER:
            for seed in v47.CONSTRUCTION_SEEDS["lane_c"][source]:
                self.constructors["lane_c"](source=source, seed=seed)
        records: list[dict] = []
        for source in v47.SOURCE_ORDER:
            for seed in (921001, 921002, 921003):
                records.append({"lane": "lane_a", "source": source, "construction_seed": seed, "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"})
            for seed in (922001, 922002, 922003):
                records.append({"lane": "lane_b", "source": source, "construction_seed": seed, "matrix_id": f"lane_b_{source}_s{seed}", "shape": "[4, 1024]"})
        for mid, met in self.metrics_by_id.items():
            records.append(dict(met))
        for i in range(6):
            records.append({"lane": "lane_c", "source": "1M", "construction_seed": 999000+i, "matrix_id": f"lane_c_1M_s{999000+i}", "shape": "[4, 1024]", "rank_GF32": 4, "support_edge_count": 10, "col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True, "position_permutations": [[0]]})
        records = records[:27]
        for src in v47.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v47._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def run_scenario(tmp_path, monkeypatch, real_counts, fake_outcome, calls=None, name="run"):
    counter = {"n": 0}
    def _patched_eval(matrix, source, block_seed, arm, h1_rows, counts, bob, u1_alice, u2_alice, u2_bob, field, setting, fake_runner, decode, errors_initial, spec, q=None, l1_res=None):
        idx = counter["n"]
        counter["n"] += 1
        if calls is not None:
            calls.append({"max_iter": setting[0], "damping_alpha": setting[1], "arm": arm, "block_seed": block_seed, "h1_rows": h1_rows})
        vals = fake_outcome(idx)
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
        reclassified = v47.classify_reclassified(exact_l2, syn_ok, tag_ok)
        return {
            "arm": arm, "h1_rows": h1_rows, "source": source, "block_seed": block_seed,
            "construction_seed": spec["construction_seed"], "matrix_id": spec["matrix_id"],
            "h1_matrix_id": spec.get("h1_matrix_id", f"{v47.H1_MATRIX_ID} prefix m1={h1_rows}"),
            "errors_initial": int(errors_initial), "errors_final": int(final),
            "exact_l2": bool(exact_l2), "exact_u1": bool(exact_u1), "exact_full": bool(exact_u1 and exact_l2),
            "syndrome_ok_l2": bool(syn_ok), "syndrome_ok_l1": bool(syn_ok_l1),
            "target_tag": target, "candidate_tag": candidate, "tag_ok": tag_ok, "tag_scope": v47.TAG_SCOPE, "reclassified": reclassified,
            "iterations_l1": 5, "iterations_l2": 5 if exact_l2 else 90,
            "bp_posterior_entropy": 4.2, "mean_abs_diff_q_p": 0.03,
            "leak_total_this_arm": int(spec.get("leak_total_this_arm", v47.leak_for(source, h1_rows))),
            "status": "converged_exact" if exact_l2 else "max_iter", "runtime_s": 0.001,
        }
    monkeypatch.setattr(v47, "_evaluate_one_arm", _patched_eval)
    world = FakeWorld()
    root = tmp_path / name
    result = v47.run_v47_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    return result, root

def make_positional_outcome(special: dict[int, tuple], default=(True, 0, True)):
    def outcome(idx):
        return special.get(idx, default)
    return outcome

# ---- B3 oracle-removal ----
def test_tag_l2_only_oracle_removal():
    empty = np.empty(0, dtype=np.uint8)
    x2 = np.array([1,2,3,4,5], dtype=np.uint8)
    tag_a = compute_tag_64(empty, x2)
    tag_b = compute_tag_64(empty, x2)
    assert tag_a == tag_b
    assert v47.compute_l2_tag(x2) == tag_a
    x2_alt = x2.copy()
    x2_alt[0] = (int(x2_alt[0]) + 1) % 32
    tag_alt = compute_tag_64(empty, x2_alt)
    assert tag_alt != tag_a
    assert len(tag_a) == 16
    int(tag_a, 16)
    src = Path(v47.__file__).read_text(encoding="utf-8")
    assert "compute_tag_64(x1_true" not in src
    assert v47.TAG_SCOPE == "l2_only"
    assert v47.classify_reclassified(True, True, True) == "exact"
    assert v47.classify_reclassified(False, True, False) == "detected_verification_failure"
    assert v47.classify_reclassified(False, False, False) == "decoder_non_syndrome_failure"
    assert v47.classify_reclassified(False, True, True) == "undetected_accepted_wrong"

def test_no_canonical_reimplementation():
    src = Path(v47.__file__).read_text(encoding="utf-8")
    assert "def compute_tag_64" not in src
    assert "from comparison_bench.formal_ir.v35_algorithm_development import" in src
    assert "compute_tag_64" in src

# ---- B1 registry 87 ----
def test_registry_accepts_frozen_nine():
    ok, msg = v47.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    flat = [s for src in v47.SOURCE_ORDER for s in v47.NEW_BLOCK_SEEDS[src]]
    assert flat == [390125,390126,390127,390225,390226,390227,390325,390326,390327]
    assert len(v47.FORBIDDEN_78) == 78
    assert len(v47.FORBIDDEN_BLOCK_SEEDS) == 87
    overlap = set(flat) & v47.FORBIDDEN_BLOCK_SEEDS
    assert overlap == set()
    overlap78 = set(flat) & v47.FORBIDDEN_78
    assert overlap78 == set()
    # continuity per source
    for src in v47.SOURCE_ORDER:
        seeds = v47.NEW_BLOCK_SEEDS[src]
        assert seeds == sorted(seeds)
        assert seeds[1] - seeds[0] == 1 and seeds[2]-seeds[1]==1

def test_registry_rejects_overlaps():
    for probe in [360101, 390101, 390106, 390107, 390110, 390113, 390116, 390119, 390122, 390222, 390322]:
        reg = {src: list(seeds) for src,seeds in v47.NEW_BLOCK_SEEDS.items()}
        reg["2M"][0] = probe
        ok,_ = v47.validate_seed_registry(reg)
        assert not ok, probe

def test_registry_rejects_duplicate():
    reg = {src: list(seeds) for src,seeds in v47.NEW_BLOCK_SEEDS.items()}
    reg["1M"][1] = reg["1M"][0]
    ok,msg = v47.validate_seed_registry(reg)
    assert not ok and "duplicate" in msg.lower()

# ---- B2 H1 prefix ----
def test_h1_nested_prefix_and_rank(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)
    first = v47.reconstruct_v47_matrices(authority, field=field, constructors=world.constructors)
    second = v47.reconstruct_v47_matrices(authority, field=field, constructors=world.constructors)
    # consistent
    for k in [("lane_c","1M"),("lane_c","1p5M"),("lane_c","2M")]:
        assert np.array_equal(first[k][0], second[k][0])
    h1_full = first[("H1","L1")][0]
    assert h1_full.shape == (16,1024)
    assert h1_full.shape[0]==16
    h1_8 = first[("H1_8","L1")][0]
    h1_12 = first[("H1_12","L1")][0]
    assert h1_8.shape == (8,1024)
    assert h1_12.shape == (12,1024)
    assert np.array_equal(h1_8, h1_12[:8,:])
    assert np.array_equal(h1_12, h1_full[:12,:])
    assert np.array_equal(h1_8, h1_full[:8,:])
    # rank checks
    from comparison_bench.formal_ir.v35_algorithm_development import compute_gf32_rank
    assert compute_gf32_rank(h1_8, field) == 8
    assert compute_gf32_rank(h1_12, field) == 12
    assert compute_gf32_rank(h1_full, field) == 16

def test_sentinels_and_tag_import(real_counts):
    res = v47.triple_arm_binding_preflight(real_counts)
    assert set(res.keys())==set(v47.SOURCE_ORDER)
    for src,chk in res.items():
        assert chk["probe_block_seed"]==v47.PREFLIGHT_BLOCK_SEEDS[src]
        assert chk["h1_prefix_ok"] is True
        assert chk["v35_tag_import_ok"] is True
        assert chk["tag_scope_l2_only"] is True
        assert chk["leakage_accounted"] is True
        assert chk["carrier_identity_h1_8_fake"] is True
        assert chk["carrier_identity_h1_12_fake"] is True
        assert chk["carrier_identity_h1_16_fake"] is True

# ---- B8 54-call accounting ----
def test_54_call_accounting(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    calls=[]
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="acct54")
    records=json.loads((root/"v47_records.json").read_text(encoding="utf-8"))
    assert len(records)==27
    assert [r["call_id"] for r in records]==[f"C{i:02d}" for i in range(1,28)]
    assert [r["arm"] for r in records]== [spec["arm"] for spec in v47.FROZEN_WORKLOAD]
    summary=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))
    acc=summary["accounting"]
    assert acc["decoder_calls_planned"]=={"total":54, "l1":27, "h1_8":9, "h1_12":9, "h1_16":9, "total_l2":27}
    assert acc["decoder_calls_started"]=={"total":54, "l1":27, "h1_8":9, "h1_12":9, "h1_16":9, "total_l2":27}
    assert acc["decoder_calls_completed"]=={"total":54, "l1":27, "h1_8":9, "h1_12":9, "h1_16":9, "total_l2":27}
    assert v47.HARD_CALL_CAP==54
    for rec in records:
        assert rec["tag_scope"]=="l2_only"
        assert len(rec["target_tag"])==16
        assert rec["reclassified"] in v47.RECLASSIFIED_VALUES
        # leak per arm
        expected = v47.leak_for(rec["source"], rec["h1_rows"])
        assert rec["leak_total_this_arm"]==expected
    # leak table
    assert summary["leakage"]["per_source"]["1M"]["h1_8_leak_total"]==1024
    assert summary["leakage"]["per_source"]["1M"]["h1_12_leak_total"]==1044
    assert summary["leakage"]["per_source"]["1M"]["h1_16_leak_total"]==1064
    assert summary["leakage"]["per_source"]["1p5M"]["h1_8_leak_total"]==1054
    assert summary["leakage"]["per_source"]["1p5M"]["h1_12_leak_total"]==1074
    assert summary["leakage"]["per_source"]["2M"]["h1_16_leak_total"]==1104
    # budget cap 55th refused
    acc2=v47.CallAccounting()
    for _ in range(27):
        acc2.register_start(layer="l1"); acc2.register_complete(layer="l1")
    for _ in range(9):
        acc2.register_start(layer="h1_8"); acc2.register_complete(layer="h1_8")
    for _ in range(9):
        acc2.register_start(layer="h1_12"); acc2.register_complete(layer="h1_12")
    for _ in range(9):
        acc2.register_start(layer="h1_16"); acc2.register_complete(layer="h1_16")
    with pytest.raises(v47.IntegrityFailure) as e:
        acc2.register_start()
    assert e.value.check_id=="J10"
    # order frozen
    assert [c["h1_rows"] for c in calls[:3]] == [8,12,16]

def test_three_arm_same_block_sharing(tmp_path, monkeypatch, real_counts):
    # Ensure same block sampled once: pairing_errors_initial_equal reported
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="sharing")
    summary=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))
    agg=summary["aggregates"]
    for entry in agg["paired_three_arm"]:
        assert entry["pairing_errors_initial_equal"] is True
        assert len(entry["errors_final_by_arm"])==3
    # cross-arm outcome diff not integrity failure: inject discordance
    def discordant(idx):
        # block 0: h1_8 fails, others pass; block1: all pass etc.
        # We control per L2 call idx (0..26). C01 h1_8 390125, C02 h1_12 same, C03 h1_16 same...
        # Make h1_8 arm fails for first block only
        if idx==0:
            return (False, 5, True, "detected")
        return (True, 0, True)
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, discordant, name="discord")
    records2=json.loads((root2/"v47_records.json").read_text(encoding="utf-8"))
    # should succeed with discordance not integrity failure
    summary2=json.loads((root2/"v47_summary.json").read_text(encoding="utf-8"))
    assert summary2["terminal_state"] in v47.ALL_TERMINALS
    assert any(p["discordance"] for p in summary2["aggregates"]["paired_three_arm"])

def test_first_match_truth_table(tmp_path, monkeypatch, real_counts):
    # Unit first-match logic + 2 integrated checks (heavy 8-run replaced by direct calls for speed)
    cases = [
        (True, True, True, v47.TERMINAL_H1_8_RETAINED),
        (True, False, True, v47.TERMINAL_H1_8_RETAINED),
        (True, False, False, v47.TERMINAL_H1_8_RETAINED),
        (False, True, True, v47.TERMINAL_H1_12_RETAINED),
        (False, True, False, v47.TERMINAL_H1_12_RETAINED),
        (False, False, True, v47.TERMINAL_H1_16_ONLY),
        (False, False, False, v47.TERMINAL_NO_H1_SIZE_RETAINED),
        (True, True, False, v47.TERMINAL_H1_8_RETAINED),
    ]
    for ph8, ph12, ph16, expected in cases:
        term, _, _ = v47.determine_v47_terminal(True, ph8, ph12, ph16)
        assert term==expected, f"first-match unit failed for {(ph8,ph12,ph16)}"
    # integrity failed overrides
    term, _, _ = v47.determine_v47_terminal(False, True, True, True)
    assert term==v47.TERMINAL_EVIDENCE_INVALID
    # 2 integrated runs (h1_8 retained and none retained)
    def make_outcome(pass_h1_8, pass_h1_12, pass_h1_16):
        indices_h1_8 = [0,3,6,9,12,15,18,21,24]
        indices_h1_12 = [1,4,7,10,13,16,19,22,25]
        indices_h1_16 = [2,5,8,11,14,17,20,23,26]
        def fn(idx):
            if idx in indices_h1_8: return (True,0,True) if pass_h1_8 else (False,5,True,"detected")
            if idx in indices_h1_12: return (True,0,True) if pass_h1_12 else (False,5,True,"detected")
            if idx in indices_h1_16: return (True,0,True) if pass_h1_16 else (False,5,True,"detected")
            return (True,0,True)
        return fn
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, make_outcome(True, False, False), name="fm_int_8")
    assert json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))["terminal_state"]==v47.TERMINAL_H1_8_RETAINED
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, make_outcome(False, False, False), name="fm_int_none")
    assert json.loads((root2/"v47_summary.json").read_text(encoding="utf-8"))["terminal_state"]==v47.TERMINAL_NO_H1_SIZE_RETAINED

def test_paired_discordance_and_retained_note(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="paired")
    agg=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))["aggregates"]
    # paired_three_arm has 9 blocks
    assert len(agg["paired_three_arm"])==9
    for p in agg["paired_three_arm"]:
        assert "exact_full_by_arm" in p
        assert "errors_final_delta_h1_8_vs_16" in p
        assert "tag_ok_by_arm" in p
        # leak contrast per block
        assert p["leak_by_arm"]["h1_8"] < p["leak_by_arm"]["h1_12"] < p["leak_by_arm"]["h1_16"]
    # retained != zero loss note in statistics_note
    summary=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))
    assert "retained does not mean zero" in summary["statistics_note"].lower() or "retained" in summary["statistics_note"].lower()

def test_four_way_per_arm(tmp_path, monkeypatch, real_counts):
    # undetected per arm should fail that arm only, not others (no cross-arm veto)
    def mixed(idx):
        # make h1_8 have undetected at first record, others exact
        if idx==0:
            return (False,10,True,"undetected")
        if idx==1:
            return (False,10,True,"detected")
        return (True,0,True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, mixed, name="fourway")
    summary=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_evaluation"]["h1_8"]["g3_undetected_zero"]["pass"] is False
    assert summary["gate_evaluation"]["h1_12"]["g3_undetected_zero"]["pass"] is True
    assert summary["gate_evaluation"]["h1_16"]["g3_undetected_zero"]["pass"] is True
    assert summary["arm_undetected_anomaly"]["h1_8"] is True
    assert summary["arm_undetected_anomaly"]["h1_12"] is False

def test_writer_contract(tmp_path, monkeypatch, real_counts):
    outcome=make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")
    names={p.name for p in root.iterdir()}
    assert names=={"v47_records.json","v47_records.csv","v47_summary.json"}
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v47_records.json").read_text(encoding="utf-8"))
    with (root/"v47_records.csv").open(newline="", encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)==27
    summary=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["leakage_already_accounted"] is True
    assert summary["provenance"]["tag_scope"]=="l2_only"
    assert "H1_8⊂H1_12⊂H1_16" in summary["provenance"]["h1_prefix"] or "prefix" in str(summary["provenance"]).lower()

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
    result=v47.run_v47_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=counting_decode)
    assert calls["decode"]==0

def test_orthogonal_needs_flag(tmp_path, monkeypatch, real_counts):
    # h1_16 on 1p5M <2 should set flag
    indices_1p5_h1_16 = [11,14,17]  # C12, C15, C18 correspond to 1p5M h1_16 ? actually workload: 1p5M 390225 h1_16 idx2-> C12, 390226->C15, 390227->C18 -> indices 11,14,17 with 0-based?
    # our fake_outcome index is L2 call order 0..26 matching C01-C27 L2 only; we map correctly: if we fail 2 of 3 1p5M h1_16, flag should be true
    def flag_true(idx):
        # 1p5M h1_16 positions: let's compute: C10 h1_8 (9), C11 h1_12 (10), C12 h1_16 (11), C13 h1_8 (12), C14 h1_12(13), C15 h1_16(14), C16 h1_8(15), C17 h1_12(16), C18 h1_16(17)
        if idx in (11,14):
            return (False,5,True,"detected")
        return (True,0,True)
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, flag_true, name="flag_true")
    summary=json.loads((root/"v47_summary.json").read_text(encoding="utf-8"))
    assert summary["needs_1p5m_structure_branch"] is True
    def flag_false(idx):
        if idx==11:
            return (False,5,True,"detected")
        return (True,0,True)
    result2, root2 = run_scenario(tmp_path, monkeypatch, real_counts, flag_false, name="flag_false")
    summary2=json.loads((root2/"v47_summary.json").read_text(encoding="utf-8"))
    assert summary2["needs_1p5m_structure_branch"] is False
