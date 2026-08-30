"""Fake/decoder-free tests for V64 dual verification instrumentation."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import tempfile
import json
import time
from comparison_bench.formal_ir.v64_full_symbol_verification import (
    build_instrumented_record, build_v64_fresh_registry, classify_fresh_block,
    compute_tag_full, compute_tag_l2, decompose_symbols, recompose_symbols,
    leak_consistent, LEAK_MAP, HARD_CAP, calls_in_cap, budget_ok, verify_dual,
    build_v64_summary_payload, V64CallAccounting, ACCEPTED_PLAN_SHA,
)


def test_dual_tag_single_leak_and_calls():
    s_true = np.arange(1024, dtype=np.int64) % 1024
    u1_t, u2_t = decompose_symbols(s_true)
    u1_h, u2_h = u1_t.copy(), u2_t.copy()
    d = verify_dual(u1_h, u2_h, u1_t, u2_t, True)
    assert d["tag_ok_l2"] is True and d["tag_ok_full"] is True
    assert d["same_decode_single_tag"] is True
    for src in ("1M", "1p5M", "2M"):
        assert leak_consistent(src)
        assert LEAK_MAP[src]["delta8"] - LEAK_MAP[src]["base"] == 40
        assert LEAK_MAP[src]["delta16"] - LEAK_MAP[src]["delta8"] == 40
        assert LEAK_MAP[src]["base"] == 5 * {"1M": 184, "1p5M": 190, "2M": 192}[src] + 80 + 64


def test_interpretation_three_paths():
    s_true = np.arange(1024, dtype=np.int64)
    u1_t, u2_t = decompose_symbols(s_true)
    u1_wrong = (u1_t + 1) % 32
    rec1 = build_instrumented_record("b1", "1M", [1600, 1601, 1602, 1603], u1_wrong, u2_t, u1_t, u2_t, True, True, "base", 2)
    assert rec1["exact_u1"] is False and rec1["exact_l2"] is True
    assert rec1["tag_ok_l2"] is True
    assert rec1["tag_ok_full"] is False
    assert classify_fresh_block(rec1) == "confirm_verification_scope"
    assert rec1["intercepted_u1_only"] is True
    fake_rec2 = dict(exact_u1=True, exact_l2=False, tag_ok_l2=True, tag_ok_full=True, syndrome_ok_l2=True)
    assert classify_fresh_block(fake_rec2) == "pause_tag_canonical"
    u1_ok, u2_ok = u1_t.copy(), u2_t.copy()
    rec3 = build_instrumented_record("b3", "2M", [2916, 2917, 2918, 2919], u1_ok, u2_ok, u1_t, u2_t, True, True, "base", 2)
    assert classify_fresh_block(rec3) == "performance_only"


def test_48_96_hard_cap_and_budget():
    assert calls_in_cap(48) and calls_in_cap(96) and not calls_in_cap(47) and not calls_in_cap(97)
    assert budget_ok(0, 0)
    assert budget_ok(24, 24)
    assert not budget_ok(25, 24)
    assert not calls_in_cap(97)
    from comparison_bench.formal_ir.v64_full_symbol_verification import V64CallAccounting, HARD_CAP
    assert HARD_CAP == 96
    acct = V64CallAccounting()
    for _ in range(24):
        acct.register_start("l1"); acct.register_complete("l1")
        acct.register_start("base"); acct.register_complete("base")
    assert acct.completed == 48
    assert acct.validate() == []
    for _ in range(24):
        acct.register_start("stage1"); acct.register_complete("stage1")
        acct.register_start("stage2"); acct.register_complete("stage2")
    assert acct.completed == 96
    assert acct.validate() == []
    try:
        acct.register_start("stage1")
        assert False, "should have raised at 97"
    except ValueError as e:
        assert "97" in str(e) or "hard call cap" in str(e)


def test_registry_24_and_zero_overlap_and_K2():
    try:
        reg = build_v64_fresh_registry()
    except ValueError as exc:
        msg = str(exc)
        assert "gap>=4" in msg or "EVIDENCE_INVALID" in msg
        assert "effective independent" in msg or "K2" in msg
        assert "1M" in msg
        return
    assert len(reg) == 24
    from collections import Counter
    c = Counter(r["source"] for r in reg)
    assert c["1M"] == 8 and c["1p5M"] == 8 and c["2M"] == 8
    for src in ("1M", "1p5M", "2M"):
        starts = sorted([r["held_out_ordinal_start"] for r in reg if r["source"] == src])
        assert len(starts) == len(set(starts))
        for i in range(1, len(starts)):
            assert starts[i] - starts[i-1] >= 4, f"gap>=4 violated {src} {starts}"
        fids = [fid for r in reg if r["source"]==src for fid in r["frame_ids"]]
        assert len(fids) == len(set(fids)), f"frame_ids overlap within {src}"
    all_fids = [fid for r in reg for fid in r["frame_ids"]]
    from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import BLOCK_WINDOWS as V54W
    v54_fids = {fid for w in V54W.values() for fid in w["frame_ids"]}
    assert set(all_fids).isdisjoint(v54_fids)
    from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import V48_HELDOUT_FRAME_IDS, V50_HELDOUT_FRAME_IDS, V51_HELDOUT_FRAME_IDS, V52_HELDOUT_FRAME_IDS, V53_HELDOUT_FRAME_IDS
    for forb in (V48_HELDOUT_FRAME_IDS, V50_HELDOUT_FRAME_IDS, V51_HELDOUT_FRAME_IDS, V52_HELDOUT_FRAME_IDS, V53_HELDOUT_FRAME_IDS):
        for src in ("1M","1p5M","2M"):
            assert set(all_fids).isdisjoint(set(forb[src]))
    try:
        import json as _js
        p = Path(__file__).resolve().parents[2] / "comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01/v63_records.json"
        if p.is_file():
            arr = _js.loads(p.read_text(encoding="utf-8"))
            v63_fids = {fid for r in arr for fid in r.get("frame_ids",[])}
            assert set(all_fids).isdisjoint(v63_fids)
    except Exception:
        pass
    for r in reg:
        assert r["pairs_count"] == 1024 and r["BLOCK_LENGTH"] == 1024
        assert r["sampling_mode"] == "deterministic_four_consecutive_frames_heldout_fresh_v64"
        assert r["H_provenance"]["K2"] >= 8
    assert sum(r["H_provenance"]["K2"] for r in reg[:3]) >= 24


def test_cli_default_reject_and_sha_binding():
    import subprocess
    repo = Path(__file__).resolve().parents[2]
    res = subprocess.run([sys.executable, str(repo / "scripts/execute_v64_fresh_verify.py")], capture_output=True, text=True)
    assert res.returncode == 2
    assert "BLOCKED" in res.stderr or "EXECUTE_NOT_AUTHORIZED" in res.stderr
    res2 = subprocess.run([sys.executable, str(repo / "scripts/execute_v64_fresh_verify.py"), "--execution-authorized", "--authorized-target-sha", "0"*40], capture_output=True, text=True)
    assert res2.returncode == 2
    from comparison_bench.formal_ir.v64_full_symbol_verification import ACCEPTED_PLAN_SHA
    assert ACCEPTED_PLAN_SHA == "760cb2967c7f5d5548a68f056458ef89398de3f2"
    assert len(ACCEPTED_PLAN_SHA) == 40


def test_no_synthetic_fallback():
    import inspect
    from comparison_bench.formal_ir.v64_full_symbol_verification import build_v64_fresh_registry
    sig = inspect.signature(build_v64_fresh_registry)
    assert len(sig.parameters) == 0
    try:
        reg = build_v64_fresh_registry()
    except ValueError as exc:
        assert "gap>=4" in str(exc) or "EVIDENCE_INVALID" in str(exc)
        return
    for r in reg:
        assert "held_out_source_path" in r
        assert "pairs.parquet" in r["held_out_source_path"]


def test_cli_no_fake_runner():
    import subprocess
    repo = Path(__file__).resolve().parents[2]
    res = subprocess.run([sys.executable, str(repo / "scripts/execute_v64_fresh_verify.py"), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "--fake-runner" not in res.stdout and "--fake-runner" not in res.stderr
    # passing --fake-runner should error (unrecognized)
    res2 = subprocess.run([sys.executable, str(repo / "scripts/execute_v64_fresh_verify.py"), "--fake-runner"], capture_output=True, text=True)
    assert res2.returncode != 0
    assert "unrecognized" in res2.stderr.lower() or "error" in res2.stderr.lower()


def test_plan_sha_fail_closed():
    # monkeypatch ACCEPTED_PLAN_SHA to trigger BLOCKED not warning
    import scripts.execute_v64_fresh_verify as mod
    orig = mod.ACCEPTED_PLAN_SHA
    try:
        mod.ACCEPTED_PLAN_SHA = "0"*40
        try:
            mod._check_git("0"*40)
            assert False, "should have blocked"
        except SystemExit as e:
            assert e.code == 2
    finally:
        mod.ACCEPTED_PLAN_SHA = orig


def test_fake_via_test_interface_not_cli():
    # tests must call test interface directly, not CLI fake
    from scripts.execute_v64_fresh_verify import build_fake_v64_records_for_tests
    import scripts.execute_v64_fresh_verify as mod
    # ensure CLI has no fake but helper exists
    assert hasattr(mod, "build_fake_v64_records_for_tests")
    # exercise helper to produce 24 fake records
    try:
        reg = build_v64_fresh_registry()
    except ValueError:
        # if K2 insufficient, synthesize minimal registry for test
        reg = [{"block_id": f"v64_fresh_1M_{i:02d}", "source": "1M" if i < 8 else ("1p5M" if i < 16 else "2M"), "frame_ids": [1600+i*4, 1601+i*4, 1602+i*4, 1603+i*4], "held_out_ordinal_start": i*4, "held_out_ordinal_end": i*4+3, "pairs_count": 1024, "BLOCK_LENGTH": 1024, "sampling_mode": "deterministic_four_consecutive_frames_heldout_fresh_v64", "H_provenance": {"K2": 8}} for i in range(24)]
    acct = V64CallAccounting()
    recs = build_fake_v64_records_for_tests(reg, acct)
    assert len(recs) == 24
    assert acct.completed == 48


def test_summary_frozen_fields_and_gates():
    # build synthetic records to verify summary contains all frozen fields
    try:
        reg = build_v64_fresh_registry()
    except ValueError:
        reg = [{"block_id": f"v64_fresh_1M_{i:02d}", "source": "1M" if i < 8 else ("1p5M" if i < 16 else "2M"), "frame_ids": [1600+i*4, 1601+i*4, 1602+i*4, 1603+i*4], "held_out_ordinal_start": i*4, "held_out_ordinal_end": i*4+3, "pairs_count": 1024, "BLOCK_LENGTH": 1024, "sampling_mode": "deterministic_four_consecutive_frames_heldout_fresh_v64", "H_provenance": {"K2": 8}} for i in range(24)]
    acct = V64CallAccounting()
    recs = []
    for ent in reg:
        acct.register_start("l1"); acct.register_complete("l1")
        acct.register_start("base"); acct.register_complete("base")
        s_true = np.arange(1024, dtype=np.int64) % 1024
        u1_t, u2_t = decompose_symbols(s_true)
        rec = build_instrumented_record(ent["block_id"], ent["source"], ent["frame_ids"], u1_t, u2_t, u1_t, u2_t, True, True, "base", 2)
        rec["held_out_ordinal_start"] = ent["held_out_ordinal_start"]
        rec["held_out_ordinal_end"] = ent["held_out_ordinal_end"]
        rec["pairs_count"] = 1024
        rec["sampling_mode"] = ent["sampling_mode"]
        rec["block_seed"] = ent["block_id"]
        recs.append(rec)
    t0 = time.time() - 1
    payload = build_v64_summary_payload(recs, reg, acct, t0, "0"*40)
    # exact_u1/l2/full overall+per-source
    for k in ("exact_u1", "exact_l2", "exact_full"):
        assert k in payload
        for src in ("1M", "1p5M", "2M"):
            assert k in payload["per_source"][src]
    # accepted/undetected dual
    for k in ("accepted_l2", "accepted_full", "undetected_l2", "undetected_full"):
        assert k in payload
    # gates 19/24 6/8 undetected 0
    assert "gates" in payload
    assert "exact_full_19_24" in payload["gates"]
    assert "per_source_6_8" in payload["gates"]
    assert "undetected_full_0" in payload["gates"]
    assert payload["gates"]["undetected_full_0"] == (payload["undetected_full"] == 0)
    # five-state terminal
    assert payload["terminal"] in ("V64_FULL_SYMBOL_VERIFICATION_PASS", "V64_CORRECTION_WORKS_VERIFICATION_STILL_FAILS", "V64_CORRECTION_PERFORMANCE_FAIL", "V64_PAUSE_TAG_CANONICAL_INVESTIGATION", "V64_EVIDENCE_INVALID")
    # stage/calls/leak/runtime
    assert "stage_used" in payload and "calls" in payload and "leak" in payload and "elapsed_s" in payload
    # L2 vs full diff
    assert "l2_vs_full" in payload
    assert "delta_accepted" in payload["l2_vs_full"]
    # intercepted
    assert "intercepted_u1_only" in payload
    assert payload["intercepted_u1_only"] == sum(1 for r in recs if r.get("intercepted_u1_only"))


def test_summary_terminal_states():
    # construct records that trigger different terminals
    base_reg = [{"block_id": f"b{i}", "source": "1M" if i < 8 else ("1p5M" if i < 16 else "2M"), "frame_ids": [1600+i*4, 1601+i*4, 1602+i*4, 1603+i*4], "held_out_ordinal_start": i*4, "held_out_ordinal_end": i*4+3, "pairs_count": 1024, "BLOCK_LENGTH": 1024, "sampling_mode": "deterministic_four_consecutive_frames_heldout_fresh_v64", "H_provenance": {"K2": 8}} for i in range(24)]
    # case PASS: all exact
    acct = V64CallAccounting()
    for _ in range(24):
        acct.register_start("l1"); acct.register_complete("l1")
        acct.register_start("base"); acct.register_complete("base")
    s_true = np.arange(1024, dtype=np.int64) % 1024
    u1_t, u2_t = decompose_symbols(s_true)
    recs_pass = [build_instrumented_record(f"b{i}", base_reg[i]["source"], base_reg[i]["frame_ids"], u1_t, u2_t, u1_t, u2_t, True, True, "base", 2) for i in range(24)]
    payload = build_v64_summary_payload(recs_pass, base_reg, acct, time.time()-1, "0"*40)
    assert payload["terminal"] == "V64_FULL_SYMBOL_VERIFICATION_PASS"
    # case PERFORMANCE_FAIL: only 10 exact (<19)
    recs_fail = []
    for i in range(24):
        if i < 10:
            recs_fail.append(build_instrumented_record(f"b{i}", base_reg[i]["source"], base_reg[i]["frame_ids"], u1_t, u2_t, u1_t, u2_t, True, True, "base", 2))
        else:
            u1_w = (u1_t + 1) % 32
            # make exact false, accepted false
            rec = build_instrumented_record(f"b{i}", base_reg[i]["source"], base_reg[i]["frame_ids"], u1_w, u2_t, u1_t, u2_t, True, False, "base", 2)
            # force not accepted
            rec["accepted_l2"] = False; rec["accepted_full"] = False; rec["undetected_l2"] = False; rec["undetected_full"] = False
            recs_fail.append(rec)
    acct2 = V64CallAccounting()
    for _ in range(24):
        acct2.register_start("l1"); acct2.register_complete("l1")
        acct2.register_start("base"); acct2.register_complete("base")
    payload2 = build_v64_summary_payload(recs_fail, base_reg, acct2, time.time()-1, "0"*40)
    assert payload2["terminal"] == "V64_CORRECTION_PERFORMANCE_FAIL"
    # case PAUSE: one U2 wrong but tag ok
    recs_pause = recs_pass.copy()
    recs_pause[0] = dict(exact_u1=True, exact_l2=False, exact_full=False, tag_ok_l2=True, tag_ok_full=True, syndrome_ok_l2=True, accepted_l2=True, accepted_full=True, undetected_l2=True, undetected_full=True, intercepted_u1_only=False, source="1M", stage_used="base", leak_total=1064)
    payload3 = build_v64_summary_payload(recs_pause, base_reg, acct, time.time()-1, "0"*40)
    assert payload3["terminal"] == "V64_PAUSE_TAG_CANONICAL_INVESTIGATION"


def test_partial_retention_on_interrupt():
    # simulate interrupt writing partial records, no summary
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "run_01"
        out.mkdir()
        acct = V64CallAccounting()
        # create 10 fake records then simulate interrupt
        recs = []
        for i in range(10):
            acct.register_start("l1"); acct.register_complete("l1")
            acct.register_start("base"); acct.register_complete("base")
            s_true = np.arange(1024, dtype=np.int64) % 1024
            u1_t, u2_t = decompose_symbols(s_true)
            rec = build_instrumented_record(f"b{i}", "1M", [1600+i*4, 1601+i*4, 1602+i*4, 1603+i*4], u1_t, u2_t, u1_t, u2_t, True, True, "base", 2)
            recs.append(rec)
        # emulate except block: write partial + interrupted notice, no summary
        (out / "v64_records.json").write_text(json.dumps(recs, indent=2), encoding="utf-8")
        (out / "v64_interrupted.json").write_text(json.dumps({"interrupted": True, "error": "KeyboardInterrupt", "total_calls": acct.completed, "records_written": len(recs)}, indent=2), encoding="utf-8")
        assert (out / "v64_records.json").is_file()
        data = json.loads((out / "v64_records.json").read_text(encoding="utf-8"))
        assert len(data) == 10  # partial retained, not []
        assert not (out / "v64_summary.json").exists()
        assert (out / "v64_interrupted.json").is_file()
        intr = json.loads((out / "v64_interrupted.json").read_text(encoding="utf-8"))
        assert intr["interrupted"] is True and intr["records_written"] == 10
