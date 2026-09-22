"""V80 S2b FER campaign executor tests (EXPLORE, FAKE-ONLY, no real campaign).

Frozen spec: S2B_EXPERIMENT_PACKET_20260920.md (G-S2B, single arm S2b).
Every test injects fake construct/decode/clock/rss/writer — zero
production ``construct_l2`` / ``smoke_decode_frame`` calls, zero disk
writes (the writer is an in-memory capture; nonexistent-root paths are
never created). Wall: milliseconds.
"""
import json

import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2_fer_campaign as c,
)


def _fake_construct_ok(seed, trials):
    # S2b arm: fixed constructor seed 2026092001, 20 trials, 0 four-cycles,
    # min_girth 6, rank 47 (mirrors real construct_l2 output keys).
    assert (seed, trials) == (2026092001, 20)
    return {"four_cycles": 0, "min_girth": 6, "rank": 47,
            "family": "peg-irregular"}


def _decode_ok(construction, seed):
    return {"status": "success", "iterations": 10,
            "reconstruction_ok": True, "exact_match": True}


def _decode_fail(construction, seed):
    return {"status": "max_iter_reached", "iterations": 300,
            "reconstruction_ok": False, "exact_match": False}


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class MemWriter:
    """In-memory capture: path -> blob. Never touches disk."""

    def __init__(self):
        self.store = {}
        self.calls = 0

    def __call__(self, root, files):
        self.calls += 1
        for name, blob in files.items():
            self.store[f"{root}/{name}"] = blob


def _run(root, writer, clock, decode_fn, **kw):
    return c.execute(root=root, construct_fn=_fake_construct_ok,
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


def test_t1_dual_flag_refusal():
    with pytest.raises(c.Refusal):
        c.main([])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--root",
                "workspace/s2_fer_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execution-authorized", "--root",
                "workspace/s2_fer_deadbeef"])
    # Bad root prefix refuses even with both flags (rc2 pre-anything).
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--root", "workspace/wrong_deadbeef"])
    # Old-prefix root refuses even with both flags (S2b uses s2b_ prefix).
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--root", "workspace/s2_fer_deadbeef"])
    # Non-S2b variant refuses even with both flags (single arm, rc2).
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--root", "workspace/s2b_deadbeef",
                "--variant", "V2"])
    # resume/root mismatch refuses.
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--root", "workspace/s2b_aaaaaaaa",
                "--resume-from", "workspace/s2b_bbbbbbbb"])


def test_t2_root_absent_present_matrix(tmp_path):
    w, clk = MemWriter(), FakeClock()
    # Absent fake root (never created on disk): fresh run proceeds.
    mf = _run("/tmp/opencode/s2_fer_fake_absent_01", w, clk, _decode_ok,
              max_groups=1)
    assert mf["verdict"] == "PROBE-truncated"
    # Existing root refuses fresh run (tmp_path exists on disk).
    with pytest.raises(c.Refusal):
        _run(str(tmp_path), MemWriter(), FakeClock(), _decode_ok,
             max_groups=1)
    # Resume of an absent partial refuses.
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2_fer_fake_absent_02",
                  resume_from="/tmp/opencode/s2_fer_fake_absent_02",
                  construct_fn=_fake_construct_ok, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    # root/resume-from mismatch refuses.
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2_fer_fake_a",
                  resume_from="/tmp/opencode/s2_fer_fake_b",
                  construct_fn=_fake_construct_ok, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())


def test_t3_checkpoint_per_group_all_ok():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/s2_fer_fake_allok", w, clk, _decode_ok)
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 0
    assert mf["groups_completed"] == 60
    assert mf["ledger"] == {"decodes": 240, "groups_completed": 60}
    assert mf["fer_groups"] == pytest.approx(0.0)
    rows = json.loads(w.store["/tmp/opencode/s2_fer_fake_allok/rows.json"])
    assert len(rows) == 60
    assert [r["group"] for r in rows] == list(range(60))
    assert all(r["group_accept"] for r in rows)
    # Checkpoint per COMPLETED group: 60 group flushes + 1 final write.
    assert w.calls == 61
    assert mf["verify"] == {"four_cycles_ok": True, "ledger_ok": True,
                            "rows_ok": True}
    assert len(mf["wall_windows"]) == 1
    assert mf["resume"] == {"continuations_used": 0,
                            "max_continuations": 1}


def test_t4_resume_continuation_single_wall_window():
    root = "/tmp/opencode/s2_fer_fake_resume"
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 300.0  # max non-overrun advance: wall exhausts at g=4
        return _decode_ok(construction, seed)

    part = c.execute(root=root, construct_fn=_fake_construct_ok,
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    assert part["groups_completed"] == 4
    assert part["next_group"] == 4
    assert part["ledger"]["decodes"] == 16
    rows_p = json.loads(w1.store[f"{root}/rows.json"])

    # Continuation: fresh clock, small advance; completed groups untouched.
    w2, clk2 = MemWriter(), FakeClock()

    def _fast(construction, seed):
        clk2.t += 1.0
        return _decode_ok(construction, seed)

    # Resume reads the partial from a disk-backed shim: replay w1 blobs
    # through a reader-writer that serves the stored partial first.
    import os as _os
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    try:
        done = c.execute(root=root, resume_from=root,
                         construct_fn=_fake_construct_ok,
                         decode_fn=_fast, clock=clk2,
                         rss_fn=lambda: 0, writer=w2)
    finally:
        _os.remove(f"{root}/manifest.json")
        _os.remove(f"{root}/rows.json")
        _os.rmdir(root)
    assert done["verdict"] == "PASS"
    assert done["ledger"]["decodes"] == 240  # continues, no double charge
    assert done["groups_completed"] == 60
    assert len(done["wall_windows"]) == 2  # ledger continues, wall fresh
    assert done["resume"] == {"continuations_used": 1,
                              "max_continuations": 1}
    rows_d = json.loads(w2.store[f"{root}/rows.json"])
    # Completed groups byte-identical mod elapsed/wall bookkeeping.
    assert (json.dumps(rows_d[:4], sort_keys=True)
            == json.dumps(rows_p, sort_keys=True))


def test_t5_early_stop_fourth_failure():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/s2_fer_fake_early", w, clk, _decode_fail)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["groups_completed"] == 4
    assert mf["failures"] == 4
    assert mf["ledger"]["decodes"] == 16
    assert mf["next_group"] == 4
    assert mf["partial"] is True


def test_t6_group_math_and_dblind_plumb():
    # 1.274% rule pin: 1-(1-0.05)^(1/4).
    assert c.PER_FRAME_FER_FOR_SUPERFRAME_5PCT == pytest.approx(0.01274,
                                                               abs=1e-5)
    basis = c.leak_basis()
    assert basis["leak_bits"] == 1044.0
    assert basis["f_super_basis"] == pytest.approx(1.2246, abs=1e-4)
    assert "BUDGET MAPPING" in basis["f_super_label"]
    assert "not measured efficiency" in basis["f_super_label"]
    # S2b layer-local informational pin (packet §3): 235/206.586≈1.1376.
    assert basis["f_L2_basis"] == pytest.approx(1.1376, abs=1e-4)
    assert "INFORMATIONAL ONLY" in basis["f_L2_label"]
    assert "235/206.586" in basis["f_L2_label"]
    assert basis["h_channel"] == pytest.approx(0.80698, abs=1e-5)
    assert basis["d_blind"] == 0.0
    assert "NEVER" in basis["d_blind_label"]
    assert "+0.019" in basis["sensitivity"]
    # S2b channel point pins: sampler AND prior both at p*=0.081.
    assert c.QSTAR == pytest.approx(0.081)
    assert c.H_CHANNEL_S2B == pytest.approx(0.80698, abs=1e-5)
    assert c.MAX_ITER == 300
    # Frozen literal seeds (S2b packet §4): 2026097001+idx, idx=0..239.
    assert c.frame_seed("S2b", 0, 0) == 2026097001
    assert c.frame_seed("S2b", 59, 3) == 2026097001 + 239
    assert c.S2B_FRAME_BASE == 2026097001
    assert c.S2B_CONSTRUCT_SEED == 2026092001
    # Any non-S2b variant refuses at the seed hook (fail closed, rc2).
    for bad in ("V1", "V2", "v1"):
        with pytest.raises(c.Refusal) as exc:
            c.frame_seed(bad, 0, 0)
        assert exc.value.code == 2


def test_t7_four_cycle_gate_and_single_arm(capsys):
    # S2b gate is ==0 (fixed constructor seed 2026092001, 20 trials);
    # any nonzero value refuses rc=2 with STOP-BLOCKED on stderr.
    def _bad(seed, trials):
        assert (seed, trials) == (2026092001, 20)
        return {"four_cycles": 1, "min_girth": 6, "rank": 47,
                "family": "peg-irregular"}

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/s2b_fake_gate",
                  construct_fn=_bad, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)
    assert exc.value.code == 2
    assert "STOP-BLOCKED" in capsys.readouterr().err

    # Old 1158 count also refuses (no legacy predicate remains).
    def _legacy(seed, trials):
        return {"four_cycles": 1158, "min_girth": 4, "rank": 47,
                "family": "peg-irregular"}

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/s2b_fake_legacy",
                  construct_fn=_legacy, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)
    assert exc.value.code == 2

    # Single arm S2b: V1/V2/V2-style variants refuse rc=2 with ZERO
    # decode calls (fail closed; V2 arm + <predicate deleted).
    for bad_variant in ("V1", "V2"):
        calls = []

        def _counting(construction, seed):
            calls.append(seed)
            return _decode_ok(construction, seed)

        with pytest.raises(c.Refusal) as exc:
            c.execute(root=f"/tmp/opencode/s2b_fake_{bad_variant.lower()}",
                      variant=bad_variant,
                      construct_fn=_fake_construct_ok,
                      decode_fn=_counting, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_groups=1)
        assert exc.value.code == 2
        assert calls == []


def test_t8_no_writes_outside_root():
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/s2_fer_fake_nowrite"
    _run(root, w, clk, _decode_ok, max_groups=1)
    assert set(w.store) == {f"{root}/manifest.json", f"{root}/rows.json"}
    for bad in ("/tmp/opencode/results/s2_fer_fake_x",
                "/tmp/opencode/comparison_bench/outputs_comparison/"
                "s2_fer_fake_x"):
        with pytest.raises(c.Refusal):
            c.execute(root=bad, construct_fn=_fake_construct_ok,
                      decode_fn=_decode_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_groups=1)


def test_t9_second_resume_refuses_zero_decodes():
    """SCE-02: exactly ONE continuation; a second --resume-from refuses
    rc=2 with ZERO decode calls (wall_windows len!=1 gate)."""
    import os as _os
    root = "/tmp/opencode/s2_fer_fake_second_resume"
    w1, clk1 = MemWriter(), FakeClock()

    def _slow1(construction, seed):
        clk1.t += 300.0  # wall exhausts at g=4 (T4 pattern)
        return _decode_ok(construction, seed)

    part1 = c.execute(root=root, construct_fn=_fake_construct_ok,
                      decode_fn=_slow1, clock=clk1,
                      rss_fn=lambda: 0, writer=w1)
    assert part1["verdict"] == "INCOMPLETE-wall"
    assert part1["groups_completed"] == 4
    assert len(part1["wall_windows"]) == 1
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    try:
        # First continuation: slow again -> wall halts with 2 windows.
        w2, clk2 = MemWriter(), FakeClock()

        def _slow2(construction, seed):
            clk2.t += 300.0
            return _decode_ok(construction, seed)

        part2 = c.execute(root=root, resume_from=root,
                          construct_fn=_fake_construct_ok,
                          decode_fn=_slow2, clock=clk2,
                          rss_fn=lambda: 0, writer=w2)
        assert part2["verdict"] == "INCOMPLETE-wall"
        assert part2["groups_completed"] == 8
        assert len(part2["wall_windows"]) == 2
        with open(f"{root}/manifest.json", "w") as fh:
            fh.write(w2.store[f"{root}/manifest.json"])
        with open(f"{root}/rows.json", "w") as fh:
            fh.write(w2.store[f"{root}/rows.json"])
        # Second continuation: refuses rc=2, zero decode calls.
        calls = []

        def _counting(construction, seed):
            calls.append(seed)
            return _decode_ok(construction, seed)

        with pytest.raises(c.Refusal) as exc:
            c.execute(root=root, resume_from=root,
                      construct_fn=_fake_construct_ok,
                      decode_fn=_counting, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter())
        assert exc.value.code == 2
        assert calls == []
    finally:
        for _name in ("manifest.json", "rows.json"):
            try:
                _os.remove(f"{root}/{_name}")
            except OSError:
                pass
        try:
            _os.rmdir(root)
        except OSError:
            pass


def test_t10_overrun_rss_fail_budget_terminal_nonresumable():
    """SCE-02: per-decode overrun (>300 s) and RSS>=4 GiB halt as
    FAIL(budget) terminal; the FAIL(budget) partial is NOT resumable
    (refuses rc=2 with zero decode calls)."""
    import os as _os
    # Overrun arm: first decode exceeds the per-decode cap.
    w, clk = MemWriter(), FakeClock()

    def _overrun(construction, seed):
        clk.t += 301.0
        return _decode_ok(construction, seed)

    mf = _run("/tmp/opencode/s2_fer_fake_overrun", w, clk, _overrun)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(w.store["/tmp/opencode/s2_fer_fake_overrun/rows.json"])
    assert len(rows) == 1 and rows[0]["status"] == "overrun"
    # RSS arm: 5 GiB from the start -> halt before any decode.
    w2 = MemWriter()
    seen = []

    def _should_not_run(construction, seed):
        seen.append(seed)
        return _decode_ok(construction, seed)

    mf2 = c.execute(root="/tmp/opencode/s2_fer_fake_rss",
                    construct_fn=_fake_construct_ok,
                    decode_fn=_should_not_run, clock=FakeClock(),
                    rss_fn=lambda: 5 * 1024 ** 3, writer=w2)
    assert mf2["verdict"] == "FAIL(budget)"
    assert mf2["partial"] is True
    assert seen == []
    assert mf2["ledger"]["decodes"] == 0
    # Non-resumability: publish the overrun FAIL(budget) partial to a
    # disk shim and refuse the resume with zero decode calls.
    root = "/tmp/opencode/s2_fer_fake_budget_noresume"
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/s2_fer_fake_overrun/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/s2_fer_fake_overrun/rows.json"])
    try:
        calls = []

        def _counting(construction, seed):
            calls.append(seed)
            return _decode_ok(construction, seed)

        with pytest.raises(c.Refusal) as exc:
            c.execute(root=root, resume_from=root,
                      construct_fn=_fake_construct_ok,
                      decode_fn=_counting, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter())
        assert exc.value.code == 2
        assert calls == []
    finally:
        for _name in ("manifest.json", "rows.json"):
            try:
                _os.remove(f"{root}/{_name}")
            except OSError:
                pass
        try:
            _os.rmdir(root)
        except OSError:
            pass


def test_t11_budget_fail_retains_partial_rows():
    """SCE-02(c): budget-fail path retains partial rows (completed-group
    prefix + the failing record) with partial=True and ledger intact."""
    w, clk = MemWriter(), FakeClock()
    calls = {"n": 0}

    def _fail_at_group1(construction, seed):
        calls["n"] += 1
        if calls["n"] <= 4:  # group 0 decodes clean
            return _decode_ok(construction, seed)
        clk.t += 301.0  # first decode of group 1 overruns
        return _decode_ok(construction, seed)

    mf = _run("/tmp/opencode/s2_fer_fake_budget_rows", w, clk,
              _fail_at_group1)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(
        w.store["/tmp/opencode/s2_fer_fake_budget_rows/rows.json"])
    assert len(rows) == 2
    assert rows[0]["group"] == 0 and rows[0]["group_accept"] is True
    assert rows[1]["status"] == "overrun"
    assert mf["groups_completed"] == 2
    assert mf["ledger"] == {"decodes": 4, "groups_completed": 2}
    assert mf["next_group"] == 1


def test_t12_s2b_manifest_labels():
    """S2b manifest carries the frozen E1/E4/E5 labels: single arm S2b,
    construct seed 2026092001 + four_cycles==0 gate (+min_girth/rank),
    frame base 2026097001, decoder qber=0.081 + arithmetic line,
    f_L2 informational + f_super budget-mapping wording."""
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/s2b_fake_manifest"
    mf = _run(root, w, clk, _decode_ok, max_groups=1)
    assert mf["variant"] == "S2b"
    assert mf["verdict"] == "PROBE-truncated"
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["variant"] == "S2b"
    con = mani["construct"]
    assert con["seed"] == 2026092001
    assert con["max_trials"] == 20
    assert con["four_cycles"] == 0
    assert con["min_girth"] == 6
    assert con["rank"] == 47
    assert "==0" in con["four_cycle_gate"]
    assert "STOP-BLOCKED" in con["four_cycle_gate"]
    assert mani["seeds"]["frame_base"] == 2026097001
    assert mani["seeds"]["frame_rule"] == \
        "base+idx, idx=0..239 (group g frame f → idx=4g+f)"
    dec = mani["decoder"]
    assert dec["qber"] == pytest.approx(0.081)
    assert dec["max_iter"] == 300
    assert "0.40569+0.081×4.954196=0.80698" in dec["channel"]
    assert mani["f_L2"] == pytest.approx(1.1376, abs=1e-4)
    assert "INFORMATIONAL ONLY" in mani["f_L2_label"]
    assert "235/206.586" in mani["f_L2_label"]
    assert mani["f_super"] == pytest.approx(1.2246, abs=1e-4)
    assert "BUDGET MAPPING" in mani["f_super_label"]
    assert "not measured efficiency" in mani["f_super_label"]
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert rows[0]["frames"][0]["seed"] == 2026097001
