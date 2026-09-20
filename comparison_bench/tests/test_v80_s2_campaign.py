"""V80 S2 FER campaign executor tests (EXPLORE, FAKE-ONLY, no real campaign).

Frozen spec: S2_FER_CAMPAIGN_PACKET_20260920.md (G-S2FER). Every test
injects fake construct/decode/clock/rss/writer — zero production
``construct_l2`` / ``smoke_decode_frame`` calls, zero disk writes (the
writer is an in-memory capture; nonexistent-root paths are never
created). Wall: milliseconds.
"""
import json

import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2_fer_campaign as c,
)


def _fake_construct_ok(seed, trials):
    return {"four_cycles": 1158, "min_girth": 6,
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
    # resume/root mismatch refuses.
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--root", "workspace/s2_fer_aaaaaaaa",
                "--resume-from", "workspace/s2_fer_bbbbbbbb"])


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
    assert basis["d_blind"] == 0.0
    assert "NEVER" in basis["d_blind_label"]
    assert "+0.019" in basis["sensitivity"]
    # Frozen literal seeds (packet §2): V1 2026096001+idx, V2 2026096301+idx.
    assert c.frame_seed("V1", 0, 0) == 2026096001
    assert c.frame_seed("V1", 59, 3) == 2026096001 + 239
    assert c.frame_seed("V2", 0, 0) == 2026096301
    assert c.frame_seed("V2", 59, 3) == 2026096301 + 239


def test_t7_four_cycle_gate_and_variant_v2(capsys):
    def _bad(seed, trials):
        return {"four_cycles": 1157, "min_girth": 6,
                "family": "peg-irregular"}

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/s2_fer_fake_gate",
                  construct_fn=_bad, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)
    assert exc.value.code == 2
    assert "STOP-BLOCKED" in capsys.readouterr().err

    def _v2(seed, trials):
        assert (seed, trials) == (2026096101, 100)
        return {"four_cycles": 1150, "min_girth": 6,
                "family": "peg-irregular"}

    mf = c.execute(root="/tmp/opencode/s2_fer_fake_v2", variant="V2",
                   construct_fn=_v2, decode_fn=_decode_ok,
                   clock=FakeClock(), rss_fn=lambda: 0,
                   writer=MemWriter(), max_groups=1)
    assert mf["variant"] == "V2"
    assert mf["construct"]["four_cycles"] == 1150

    def _v2_bad(seed, trials):
        return {"four_cycles": 1158, "min_girth": 6,
                "family": "peg-irregular"}

    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/s2_fer_fake_v2bad", variant="V2",
                  construct_fn=_v2_bad, decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0,
                  writer=MemWriter(), max_groups=1)


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
