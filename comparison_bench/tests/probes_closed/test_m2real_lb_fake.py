"""Fake-only tests for the M2REAL layered-binary real arm.

FAKE-ONLY: every series/bundle/construct/decode here is synthetic and
in-test. No production decoder runs (every ``execute()`` call passes
explicit fakes; production kernels are monkeypatched to raise); no
frozen module is modified; no real data file is read; all disk use is
in pytest tmp_path. Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import m2real_runner as r
from comparison_bench.src.comparison_bench.cli import m2hdc_arm_runner as m2hdc
from comparison_bench.src.comparison_bench.cli import m2lb_arm_runner as m2lb
from comparison_bench.src.comparison_bench.methods import hd_cascade as hc
from comparison_bench.src.comparison_bench.methods import layered_binary as lay


# -- fakes (explicit; never production) ---------------------------------------

def _mock_series(n_sf=2, remainder=10, seed=11):
    n = n_sf * 1024 + remainder
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 1024, size=n, dtype=np.int64)
    b = rng.integers(0, 1024, size=n, dtype=np.int64)
    return {"a": a, "b": b, "dataset": "T2-1M", "member": "<mock-member>",
            "offset_ps": -50, "n_pairs_total": n, "n_pairs_eval": n,
            "eval_first_frame": 0, "read_wall_s": 0.0}


def _mock_bundle(source):
    return {"path": f"<mock-bundle-{source}>", "source": source}


def _fake_hdc_decode(mode="success"):
    seen = {"n": 0}

    def _fn(a_planes, b_planes, schedules, frame_idx, seed):
        assert len(a_planes) == 10 and len(b_planes) == 10
        seen["n"] += 1
        if mode == "success":
            exact, acc, toe = True, True, True
        elif mode == "undetected":
            exact, acc, toe = False, True, False
        else:
            exact, acc, toe = False, False, False
        return {"exact_match": exact, "accepted": acc,
                "toeplitz_verified": toe, "leak_ec_bits": 5.0,
                "rescue_bits": 2.0, "control_bits": 0.0,
                "messages_actual": 446.0, "prior_entropy_bits": 10.0}
    _fn.seen = seen
    return _fn


def _fake_lb_construct(expected, record=None):
    """expected: {(m, plane): m_rows} per allocation under test."""
    def _fn(n_len, m_rows, seed_const, frame_idx, plane):
        assert int(seed_const) == 2026092001
        assert int(frame_idx) == 0  # per-block 1-frame calls
        assert 0 <= int(plane) < 10
        if record is not None:
            record.append((int(m_rows), int(plane)))
        return {"triples": [], "m": int(m_rows)}
    return _fn


def _fake_lb_decode(mode="success", record=None):
    seen = {"n": 0}

    def _fn(a_planes, b_planes, constructions, stages, frame_idx,
            max_iter, streak):
        assert int(max_iter) == 300 and int(streak) == 3
        assert len(a_planes) == 10 and len(b_planes) == 10
        assert len(constructions) == 10
        assert len(list(stages.delta_steps)) == 5
        if record is not None:
            record.append((int(stages.m_init), int(frame_idx)))
        seen["n"] += 1
        if mode == "success":
            exact, acc, syn, toe = True, True, True, True
        elif mode == "fail":
            exact, acc, syn, toe = False, False, False, False
        elif mode == "undetected":
            exact, acc, syn, toe = False, True, True, True
        else:
            i = seen["n"] - 1
            if i % 3 == 0:
                exact, acc, syn, toe = True, True, True, True
            elif i % 3 == 1:
                exact, acc, syn, toe = False, False, False, False
            else:
                exact, acc, syn, toe = False, True, True, True
        return {"exact_match": exact, "accepted": acc,
                "syndrome_consistent": syn, "toeplitz_verified": toe,
                "leak_ec_bits": 5.0,
                "blind_stage_bits": [1.0, 1.0, 1.0, 1.0, 1.0],
                "rescue_bits": 2.0, "control_bits": 0.0,
                "messages_actual": 3.14, "prior_entropy_bits": 10.0,
                "construction": {}}
    _fn.seen = seen
    return _fn


def _raise(*a, **k):
    raise AssertionError("production path entered by fake test (must inject)")


def _run(tmp_path, monkeypatch, source="1M", hdc_mode="success",
         lb_mode="success", suffix="a1b2c3d4", n_sf=2, remainder=10,
         lb_construct_record=None, lb_decode_record=None,
         lb_construct_fn=None, lb_decode_fn=None, **kw):
    monkeypatch.chdir(tmp_path)  # relative workspace/m2real_ roots stay in tmp
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    monkeypatch.setattr(lay, "_construct_plane_production", _raise)
    monkeypatch.setattr(lay, "_spa_decode_production", _raise)
    series = _mock_series(n_sf=n_sf, remainder=remainder)
    root = f"workspace/m2real_{suffix}"
    summary = r.execute(
        source=source, root=root,
        series_fn=lambda s: series, bundle_fn=_mock_bundle,
        hdc_decode_fn=_fake_hdc_decode(hdc_mode),
        lb_construct_fn=(lb_construct_fn
                         or _fake_lb_construct(None,
                                               record=lb_construct_record)),
        lb_decode_fn=(lb_decode_fn
                      or _fake_lb_decode(lb_mode,
                                         record=lb_decode_record)),
        clock=kw.get("clock"), rss_fn=(kw.get("rss_fn") or (lambda: 0)),
        writer=r.default_writer, max_blocks=kw.get("max_blocks"))
    return summary, root


# -- R1: allocation/blind verbatim + LayeredParams 300/3 -----------------------------

def test_r1_allocation_blind_verbatim_and_pins():
    for m in (197, 201):
        rows = m2lb.allocation_for("1M", m)
        assert sorted(rows) == list(range(10))
        assert sum(rows.values()) == m
        assert all(v <= 64 for v in rows.values())
        tab = m2lb.blind_table_for(m)
        assert tab == {"m_init": m - 20,
                       "delta_steps": [4, 4, 4, 4, 4]}
        assert m2lb.blind_levels_for(m)[-1] == m
    assert m2lb.M2LB_MAX_ITER == 300 and m2lb.M2LB_STREAK == 3
    assert m2lb.M2LB_CONSTRUCT_SEED == 2026092001
    with pytest.raises(m2lb.Refusal):
        m2lb.allocation_for("1M", 197, h_basis=0.8012690084416184)


def test_r1b_construct_sees_verbatim_allocations(tmp_path, monkeypatch):
    rec: list[tuple[int, int]] = []
    summary, _ = _run(tmp_path, monkeypatch, lb_construct_record=rec,
                      suffix="b2c3d4e5")
    assert summary["verdict"] == "COMPLETE"
    got = {(mr, pl) for mr, pl in rec}
    for m in (197, 201):
        rows = m2lb.allocation_for("1M", m)
        for plane in range(10):
            assert (rows[plane], plane) in got
    lb_arms = [a for a in summary["arms"] if a["family"] == "lb"]
    assert [a["mode"] for a in lb_arms] == ["matched", "matched"]
    assert [a["construct_label"] for a in lb_arms] == [
        "M2REAL-1M-S197-layered", "M2REAL-1M-S201-layered"]
    assert all("verbatim F2" in str(a["allocation_status"])
               for a in lb_arms)
    assert all("verbatim F3" in str(a["blind_status"]) for a in lb_arms)


def test_r1c_decode_pins_and_frame_idx(tmp_path, monkeypatch):
    rec: list[tuple[int, int]] = []
    _run(tmp_path, monkeypatch, lb_decode_record=rec, suffix="c3d4e5f6")
    assert len(rec) == 2 * 32  # two lb arms x 32 blocks
    assert {m_init for m_init, _ in rec} == {177, 181}
    assert {fidx for _, fidx in rec} == {0}  # per-block 1-frame calls


# -- R2: LB 5601-series seeds, global increment -----------------------------------------

def test_r2_lb_seed_series(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, suffix="d4e5f6a7")
    body = json.load(open(f"{root}/rows.json"))
    lb197 = sorted(x["block"] for x in body["rows"]
                   if x["family"] == "lb" and x["m"] == 197)
    assert lb197 == list(range(32))
    seeds = sorted(x["seed"] for x in body["rows"]
                   if x["family"] == "lb" and x["m"] == 197)
    assert seeds == list(range(2026095601, 2026095601 + 32))
    assert all(x["stream"] == f"o1_blk:{x['seed']}" for x in body["rows"]
               if x["family"] == "lb")
    lb_arms = [a for a in summary["arms"] if a["family"] == "lb"]
    assert [a["seed_base"] for a in lb_arms] == [2026095601, 2026095601]


# -- R3: LB outcomes, undetected isolation, leak sums ------------------------------------

def test_r3_mixed_outcomes_and_leak_sums(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, hdc_mode="success",
                         lb_mode="mixed", suffix="e5f6a7b8")
    l197 = [a for a in summary["arms"] if a["family"] == "lb"
            and a["m"] == 197][0]
    assert l197["fails"] == 21 and l197["undetected"] == 10
    assert l197["fer_blocks"] == pytest.approx(21 / 32)
    # leak per block = 5.0 + 5x1.0 stages; lambda adds tag 64 + rescue 2.0
    assert l197["lambda_parts"]["leak_EC"] == pytest.approx(32 * 10.0)
    assert l197["lambda_parts"]["tag"] == pytest.approx(32 * 64)
    assert l197["lambda_total"] == pytest.approx(32 * (10.0 + 64 + 2.0))
    body = json.load(open(f"{root}/rows.json"))
    # shared mixed fake cycles across arms: m=197 (i=0..31) 10 und,
    # m=201 (i=32..63) 11 und
    und = [x for x in body["rows"] if x["family"] == "lb"
           and x["undetected"] is True]
    assert len(und) == 21
    und197 = [x for x in und if x["m"] == 197]
    und201 = [x for x in und if x["m"] == 201]
    assert len(und197) == 10 and len(und201) == 11
    assert all(x["exact_match"] is False and x["block_fail"] == 1
               for x in und)


def test_r3b_outcome_fail_closed_no_defaults(tmp_path, monkeypatch):
    def _bad(a_planes, b_planes, constructions, stages, frame_idx,
             max_iter, streak):
        return {"exact_match": True, "accepted": True,
                "syndrome_consistent": True, "toeplitz_verified": True,
                "leak_ec_bits": 1.0, "blind_stage_bits": [0.0] * 5,
                "rescue_bits": 0.0, "control_bits": 0.0,
                "messages_actual": 3.14, "prior_entropy_bits": 1.0}
        # missing "construction" key: method fails closed, no defaults

    summary, root = _run(tmp_path, monkeypatch, lb_decode_fn=_bad,
                         suffix="f6a7b8c9", max_blocks=2)
    body = json.load(open(f"{root}/rows.json"))
    # error rows carry no family key (fail-closed: first bad block halts
    # the arm, no retry, retained)
    err_rows = [x for x in body["rows"] if x.get("status") == "error"]
    assert len(err_rows) == 1
    assert all("family" not in x for x in err_rows)
    lb197 = [a for a in summary["arms"] if a["family"] == "lb"
             and a["m"] == 197][0]
    assert lb197["verdict"] == "FAIL(budget)"
    assert lb197["blocks_done"] == 1  # the retained error row is attempted
    assert lb197["fails"] == 0  # error halts before any success/fail verdict


# -- R4: superframe rollup (16/16 exact) --------------------------------------------------

def test_r4_superframe_rollup(tmp_path, monkeypatch):
    summary, _ = _run(tmp_path, monkeypatch, hdc_mode="success",
                      lb_mode="success", suffix="a7b8c9d0")
    for arm in summary["arms"]:
        assert arm["sf_total"] == 2
        assert arm["sf_success"] == 2
        assert arm["fer_blocks"] == 0.0
        assert arm["f_eff"] == arm["f_super"]
    summary2, _ = _run(tmp_path, monkeypatch, hdc_mode="fail",
                       lb_mode="fail", suffix="b8c9d0e1")
    for arm in summary2["arms"]:
        assert arm["sf_success"] == 0
        assert arm["fer_blocks"] == 1.0


# -- R5: CLI/root gates + annotations on the LB side ---------------------------------------

def test_r5_cli_and_root_gates(tmp_path, monkeypatch):
    with pytest.raises(r.Refusal):
        r.main([])
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_a1b2c3d4",
                "--execute-real"])
    # --with-production-fns gate: dual flags without the switch still refuse
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_c1d2e3f4",
                "--execute-real", "--execution-authorized"])
    # switch without either dual flag still refuses rc2
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_c1d2e3f4",
                "--with-production-fns"])
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_c1d2e3f4",
                "--execution-authorized", "--with-production-fns"])
    # switch + dual flags + fake injection passes (probe-capped, tmp root)
    monkeypatch.chdir(tmp_path)
    series = _mock_series()
    rc = r.main(
        ["--source", "1M", "--root", "workspace/m2real_c1d2e3f4",
         "--execute-real", "--execution-authorized",
         "--with-production-fns"],
        series_fn=lambda s: series, bundle_fn=_mock_bundle,
        hdc_decode_fn=_fake_hdc_decode(),
        lb_construct_fn=_fake_lb_construct(None),
        lb_decode_fn=_fake_lb_decode(),
        rss_fn=lambda: 0, writer=r.default_writer, max_blocks=1)
    assert rc == 0
    body = json.load(open("workspace/m2real_c1d2e3f4/rows.json"))
    assert len(body["rows"]) == 4 * 1
    assert body["summary"]["verdict"] == "PROBE-truncated"
    # production entries monkeypatched to raise: fakes still carry the run
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    monkeypatch.setattr(lay, "_construct_plane_production", _raise)
    monkeypatch.setattr(lay, "_spa_decode_production", _raise)
    monkeypatch.setattr(m2hdc, "_m2hdc_production_decode_fn", _raise)
    monkeypatch.setattr(m2lb, "construct_plane_production", _raise)
    monkeypatch.setattr(m2lb, "spa_decode_with_explicit_fallback", _raise)
    series2 = _mock_series()
    rc2 = r.main(
        ["--source", "1M", "--root", "workspace/m2real_d2e3f4a5",
         "--execute-real", "--execution-authorized",
         "--with-production-fns"],
        series_fn=lambda s: series2, bundle_fn=_mock_bundle,
        hdc_decode_fn=_fake_hdc_decode(),
        lb_construct_fn=_fake_lb_construct(None),
        lb_decode_fn=_fake_lb_decode(),
        rss_fn=lambda: 0, writer=r.default_writer, max_blocks=1)
    assert rc2 == 0
    body2 = json.load(open("workspace/m2real_d2e3f4a5/rows.json"))
    assert len(body2["rows"]) == 4 * 1
    assert body2["summary"]["verdict"] == "PROBE-truncated"
    series = _mock_series()
    with pytest.raises(r.Refusal):
        r.execute(source="9M", root="workspace/m2real_c9d0e1f2",
                  series_fn=lambda s: series, bundle_fn=_mock_bundle,
                  hdc_decode_fn=_fake_hdc_decode(),
                  lb_construct_fn=_fake_lb_construct(None),
                  lb_decode_fn=_fake_lb_decode(),
                  rss_fn=lambda: 0, writer=r.default_writer)


def test_r5b_annotations_and_no_forbidden_strings(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, suffix="c9d0e1f2")
    md = open(f"{root}/M2REAL_RESULT_1M.md").read()
    assert r.F9_NOTE in md
    assert "禁止 SKR" in md
    assert "DEFERRED" in md
    assert "f_notag" in md and "f_eff" in md
    assert summary["verdict"] == "COMPLETE"
    src = Path(r.__file__).read_text()
    assert ".ttbin" not in src.lower()
    assert "sample_frozen_batch" not in src
    assert "empirical_triple_sampler" not in src
