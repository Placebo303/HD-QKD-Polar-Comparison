"""Fake-only tests for the M2REAL HD-Cascade real arm.

FAKE-ONLY: every series/bundle/decode/construct here is synthetic and
in-test. No production decode runs (every ``execute()`` call passes
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

def _mock_series(n_sf=2, remainder=10, seed=7):
    n = n_sf * 1024 + remainder
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 1024, size=n, dtype=np.int64)
    b = rng.integers(0, 1024, size=n, dtype=np.int64)
    return {"a": a, "b": b, "dataset": "T2-1M", "member": "<mock-member>",
            "offset_ps": -50, "n_pairs_total": n, "n_pairs_eval": n,
            "eval_first_frame": 0, "read_wall_s": 0.0}


def _mock_bundle(source):
    return {"path": f"<mock-bundle-{source}>", "source": source}


def _fake_hdc_decode(mode="success", record=None):
    seen = {"n": 0}

    def _fn(a_planes, b_planes, schedules, frame_idx, seed):
        assert len(a_planes) == 10 and len(b_planes) == 10
        assert len(schedules) == 10
        assert int(frame_idx) == 0  # per-block 1-frame calls
        if record is not None:
            record.append(int(seed))
        seen["n"] += 1
        i = seen["n"] - 1
        if mode == "success":
            exact, acc, toe = True, True, True
        elif mode == "fail":
            exact, acc, toe = False, False, False
        elif mode == "undetected":
            exact, acc, toe = False, True, False
        else:  # mixed: success, fail, undetected repeating
            if i % 3 == 0:
                exact, acc, toe = True, True, True
            elif i % 3 == 1:
                exact, acc, toe = False, False, False
            else:
                exact, acc, toe = False, True, False
        return {"exact_match": exact, "accepted": acc,
                "toeplitz_verified": toe, "leak_ec_bits": 5.0,
                "rescue_bits": 2.0, "control_bits": 0.0,
                "messages_actual": 446.0, "prior_entropy_bits": 10.0}
    _fn.seen = seen
    return _fn


def _fake_lb_construct(allocations, record=None):
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
        if record is not None:
            record.append(int(stages.m_init))
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
         hdc_record=None, lb_construct_record=None, **kw):
    monkeypatch.chdir(tmp_path)  # relative workspace/m2real_ roots stay in tmp
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    monkeypatch.setattr(lay, "_construct_plane_production", _raise)
    monkeypatch.setattr(lay, "_spa_decode_production", _raise)
    series = _mock_series(n_sf=n_sf, remainder=remainder)
    root = f"workspace/m2real_{suffix}"
    summary = r.execute(
        source=source, root=root,
        series_fn=lambda s: series, bundle_fn=_mock_bundle,
        hdc_decode_fn=_fake_hdc_decode(hdc_mode, record=hdc_record),
        lb_construct_fn=_fake_lb_construct(None,
                                           record=lb_construct_record),
        lb_decode_fn=_fake_lb_decode(lb_mode),
        clock=kw.get("clock"), rss_fn=(kw.get("rss_fn") or (lambda: 0)),
        writer=r.default_writer, max_blocks=kw.get("max_blocks"))
    return summary, root


# -- R0: grid + frozen slice constants ------------------------------------------

def test_r0_grid_and_slice_constants():
    assert r.GRID == {"1M": (197, 201), "1p5M": (203, 207),
                      "2M": (204, 208)}
    assert r.FROZEN_SLICE["1M"] == {"superframes": 205, "remainder": 407,
                                    "blocks": 3280}
    assert r.FROZEN_SLICE["1p5M"] == {"superframes": 287, "remainder": 405,
                                      "blocks": 4592}
    assert r.FROZEN_SLICE["2M"] == {"superframes": 383, "remainder": 529,
                                    "blocks": 6128}
    assert r.BLOCKS_PER_SUPERFRAME == 16
    assert r.DIMENSION == 1024 and r.BLOCK_LEN == 64


# -- R1: CLI dual-flag gate + root gate ------------------------------------------

def test_r1_dual_flag_cli_gate(tmp_path, monkeypatch):
    with pytest.raises(r.Refusal):
        r.main([])
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_a1b2c3d4"])
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_a1b2c3d4",
                "--execute-real"])
    # --with-production-fns gate: dual flags without the switch still refuse
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_a1b2c3d4",
                "--execute-real", "--execution-authorized"])
    # switch without either dual flag still refuses rc2
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_a1b2c3d4",
                "--with-production-fns"])
    with pytest.raises(r.Refusal):
        r.main(["--source", "1M", "--root", "workspace/m2real_a1b2c3d4",
                "--execute-real", "--with-production-fns"])
    # switch + dual flags + fake injection passes (probe-capped, tmp root)
    monkeypatch.chdir(tmp_path)
    series = _mock_series()
    rc = r.main(
        ["--source", "1M", "--root", "workspace/m2real_a1b2c3d4",
         "--execute-real", "--execution-authorized",
         "--with-production-fns"],
        series_fn=lambda s: series, bundle_fn=_mock_bundle,
        hdc_decode_fn=_fake_hdc_decode(),
        lb_construct_fn=_fake_lb_construct(None),
        lb_decode_fn=_fake_lb_decode(),
        rss_fn=lambda: 0, writer=r.default_writer, max_blocks=1)
    assert rc == 0
    body = json.load(open("workspace/m2real_a1b2c3d4/rows.json"))
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
        ["--source", "1M", "--root", "workspace/m2real_b2c3d4e5",
         "--execute-real", "--execution-authorized",
         "--with-production-fns"],
        series_fn=lambda s: series2, bundle_fn=_mock_bundle,
        hdc_decode_fn=_fake_hdc_decode(),
        lb_construct_fn=_fake_lb_construct(None),
        lb_decode_fn=_fake_lb_decode(),
        rss_fn=lambda: 0, writer=r.default_writer, max_blocks=1)
    assert rc2 == 0
    body2 = json.load(open("workspace/m2real_b2c3d4e5/rows.json"))
    assert len(body2["rows"]) == 4 * 1
    assert body2["summary"]["verdict"] == "PROBE-truncated"


def test_r1b_root_fresh_and_forbidden_refusal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    monkeypatch.setattr(lay, "_construct_plane_production", _raise)
    monkeypatch.setattr(lay, "_spa_decode_production", _raise)
    busy = Path("workspace/m2real_b1b2b1b2")
    busy.mkdir(parents=True)
    series = _mock_series()
    base = {"source": "1M", "series_fn": lambda s: series,
            "bundle_fn": _mock_bundle,
            "hdc_decode_fn": _fake_hdc_decode(),
            "lb_construct_fn": _fake_lb_construct(None),
            "lb_decode_fn": _fake_lb_decode(), "rss_fn": lambda: 0,
            "writer": r.default_writer}
    with pytest.raises(r.Refusal):
        r.execute(root=str(busy), **base)
    for bad_root in ("results/m2real_deadbeef",
                     "comparison_bench/outputs_comparison/m2real_deadbeef",
                     "workspace/m2hdc_a1b2c3d4",
                     "workspace/m2real_short",
                     "workspace/m2real_toolong_suffix_extra",
                     ""):
        with pytest.raises(r.Refusal):
            r.execute(root=bad_root, **base)


def test_r2_missing_fakes_refuse(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    series = _mock_series()
    with pytest.raises(r.Refusal):
        r.execute(source="1M", root="workspace/m2real_c3d4e5f6",
                  series_fn=lambda s: series, bundle_fn=_mock_bundle,
                  hdc_decode_fn=None,
                  lb_construct_fn=_fake_lb_construct(None),
                  lb_decode_fn=_fake_lb_decode(),
                  rss_fn=lambda: 0, writer=r.default_writer)


# -- R3: real slicing on mock small arrays ----------------------------------------

def test_r3_slicing_small_arrays(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, n_sf=2, remainder=10,
                         suffix="d4e5f6a7")
    assert summary["slice_actual"] == {"superframes": 2, "remainder": 10,
                                       "blocks": 32}
    assert summary["slice_match"] is False  # small mock, recorded not refused
    assert summary["verdict"] == "COMPLETE"
    for arm in summary["arms"]:
        assert arm["blocks_done"] == 32
        assert arm["sf_total"] == 2
    body = json.load(open(f"{root}/rows.json"))
    assert len(body["rows"]) == 4 * 32
    # consecutive 16x64 slicing: block 0 == input[0:64], block 16 == sf1[0:64]
    series = _mock_series(n_sf=2, remainder=10)
    b0 = [x for x in body["rows"] if x["family"] == "hdc"
          and x["m"] == 197 and x["block"] == 0][0]
    assert b0["superframe"] == 0 and b0["block_in_sf"] == 0
    assert b0["seed"] == 2026095701 and b0["stream"] == "o1_blk:2026095701"
    b16 = [x for x in body["rows"] if x["family"] == "hdc"
           and x["m"] == 197 and x["block"] == 16][0]
    assert (b16["superframe"], b16["block_in_sf"]) == (1, 0)
    assert b16["seed"] == 2026095701 + 16
    assert series["a"].size == 2 * 1024 + 10


def test_r3b_fullsize_slice_shapes_no_decode():
    for source, n_sf, rem, n_blk in (("1M", 205, 407, 3280),
                                     ("1p5M", 287, 405, 4592),
                                     ("2M", 383, 529, 6128)):
        rng = np.random.default_rng(3)
        n = n_sf * 1024 + rem
        a = rng.integers(0, 1024, size=n, dtype=np.int64)
        b = rng.integers(0, 1024, size=n, dtype=np.int64)
        out = r.slice_real_blocks(a, b)
        assert out["n_superframes"] == n_sf
        assert out["remainder_symbols"] == rem
        assert out["n_blocks"] == n_blk
        assert r.FROZEN_SLICE[source] == {"superframes": n_sf,
                                          "remainder": rem, "blocks": n_blk}
        assert all(x["block_in_sf"] < 16 for x in out["blocks"])
        assert [x["g"] for x in out["blocks"]] == list(range(n_blk))


# -- R4: HDC 5701-series seeds, global increment -----------------------------------

def test_r4_hdc_seed_series_and_stream(tmp_path, monkeypatch):
    rec: list[int] = []
    summary, _ = _run(tmp_path, monkeypatch, hdc_record=rec,
                      suffix="e5f6a7b8")
    # one shared fake spans both hdc arms in GRID order: first 32 -> m=197
    assert rec[:32] == list(range(2026095701, 2026095701 + 32))
    assert rec[32:64] == list(range(2026095702, 2026095702 + 32))
    assert r.hdc_block_seed("1M", 197, 0) == 2026095701
    assert r.hdc_block_seed("1M", 201, 31) == 2026095702 + 31
    assert r.stream_label(2026095701) == "o1_blk:2026095701"
    hdc_arms = [a for a in summary["arms"] if a["family"] == "hdc"]
    assert [a["seed_base"] for a in hdc_arms] == [2026095701, 2026095702]
    assert all(a["stream"] == "o1_blk:{seed}" for a in hdc_arms)
    lb_arms = [a for a in summary["arms"] if a["family"] == "lb"]
    assert [a["seed_base"] for a in lb_arms] == [2026095601, 2026095601]
    with pytest.raises(r.Refusal):
        r.hdc_base_for("1M", 999)


# -- R5: assumed-v1 Mueller table + STOP on true-value fill -------------------------

def test_r5_assumed_v1_table_and_mueller_stop(tmp_path, monkeypatch):
    tab = m2hdc.provisional_block_table()
    assert tab.schedule_for(0) == [8, 4]
    assert int(tab.max_cross_plane_sweeps) == 1
    assert r.HDC_MAX_PASSES_ASSUMED_V1 == 4
    r.require_assumed_block_table(tab)
    summary, _ = _run(tmp_path, monkeypatch, suffix="f6a7b8c9")
    hdc_arms = [a for a in summary["arms"] if a["family"] == "hdc"]
    assert all("assumed-v1" in str(a["block_table"]) for a in hdc_arms)

    class _Other:
        max_cross_plane_sweeps = 1

        def planes(self, n):
            return list(range(n))

        def schedule_for(self, p):
            return [8, 8]  # filled true values: no longer assumed-v1

    monkeypatch.setattr(m2hdc, "provisional_block_table",
                        lambda: _Other())
    series = _mock_series()
    with pytest.raises(r.Refusal):
        r.execute(source="1M", root="workspace/m2real_a9b8c7d6",
                  series_fn=lambda s: series, bundle_fn=_mock_bundle,
                  hdc_decode_fn=_fake_hdc_decode(),
                  lb_construct_fn=_fake_lb_construct(None),
                  lb_decode_fn=_fake_lb_decode(),
                  rss_fn=lambda: 0, writer=r.default_writer)


# -- R6: block classes + undetected isolation + A-CMPE columns -----------------------

def test_r6_mixed_outcomes_and_acmpe_columns(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, hdc_mode="mixed",
                         lb_mode="success", suffix="a7b8c9d0")
    h197 = [a for a in summary["arms"] if a["family"] == "hdc"
            and a["m"] == 197][0]
    # 32 blocks cycled success/fail/undetected: 11/11/10
    assert h197["fails"] == 21 and h197["undetected"] == 10
    assert h197["fer_blocks"] == pytest.approx(21 / 32)
    assert h197["sf_success"] == 0  # no superframe is 16/16 exact
    body = json.load(open(f"{root}/rows.json"))
    # shared mixed fake cycles across arms: m=197 (i=0..31) holds 10 und;
    # m=201 (i=32..63) holds 11 und; total hdc und = 21
    und197 = [x for x in body["rows"] if x.get("family") == "hdc"
              and x["m"] == 197 and x["undetected"] is True]
    assert len(und197) == 10
    und_rows = [x for x in body["rows"] if x["undetected"] is True]
    assert len(und_rows) == 21
    assert all(x["exact_match"] is False and x["block_fail"] == 1
               for x in und_rows)
    csv_text = open(f"{root}/block_accounting.csv").read()
    header = csv_text.splitlines()[0]
    for col in ("block", "seed", "exact_match", "undetected", "superframe",
                "block_in_sf", "stream", "leak_ec_bits", "blind_stage_bits",
                "rescue_bits", "control_bits", "tag_bits", "lambda_total",
                "prior_entropy_bits", "prior_1p50_reportonly",
                "messages_actual", "f_super", "f_notag", "f_eff",
                "n_required", "H_basis", "H_column", "d_dim", "q_alphabet",
                "n_ir_bits", "construct_label", "bundle_path"):
        assert col in header.split(",")
    lb_rows = [x for x in body["rows"] if x["family"] == "lb"]
    assert all(x["blind_stage_bits"] != "" for x in lb_rows)
    hdc_rows = [x for x in body["rows"] if x["family"] == "hdc"]
    assert all(x["blind_stage_bits"] == "" for x in hdc_rows)


# -- R7: H_corr f basis, D2/F9/ceiling annotations, budgets ---------------------------

def test_r7_f_basis_and_annotations(tmp_path, monkeypatch):
    from comparison_bench.src.comparison_bench.cli.probes_closed import m0_realframe_runner as m0mod
    assert abs(m0mod.H_CORR["1M"] - 0.8012690084416184) < 1e-12
    assert r.f_super_for("1M", 197) == (5 * 197 + 64) / (1024 * 0.8012690084416184)
    assert r.f_notag_for("1M", 197) == (5 * 197) / (1024 * 0.8012690084416184)
    assert r.f_eff_for(1.2, 0.05) == 1.2 + 4.785675 * 0.05
    assert r.WALL_CAP_S == 5400 and r.PER_DECODE_CAP_S == 300
    assert r.RSS_CAP_GIB == 4
    summary, root = _run(tmp_path, monkeypatch, suffix="b8c9d0e1")
    assert summary["H_column"].startswith("measured")
    assert summary["d2"]["status"].startswith("DEFERRED")
    assert len(summary["d2"]["arm_inputs"]) == 4
    assert summary["f9_note"] == r.F9_NOTE
    md = open(f"{root}/M2REAL_RESULT_1M.md").read()
    assert r.F9_NOTE in md
    assert "禁止 SKR" in md
    assert "0.05" in md  # D2 frozen threshold restated
    assert "DEFERRED" in md
    assert "f_notag" in md and "lambda_total" in md
    assert summary["verdict"] == "COMPLETE"


# -- R8: no forbidden strings; production never entered -------------------------------

def test_r8_no_forbidden_strings():
    src = Path(r.__file__).read_text()
    assert ".ttbin" not in src.lower()
    assert "sample_frozen_batch" not in src
    assert "empirical_triple_sampler" not in src


def test_r8b_overrun_terminal(tmp_path, monkeypatch):
    vals = iter([0.0, 0.0, 0.0, 301.0, 301.0, 301.0, 602.0])

    def _clock():
        try:
            return next(vals)
        except StopIteration:
            return 99999.0

    summary, root = _run(tmp_path, monkeypatch, suffix="c9d0e1f2",
                         clock=_clock, max_blocks=1)
    body = json.load(open(f"{root}/rows.json"))
    assert all(x["status"] == "overrun" for x in body["rows"])
    assert all(x["exact_match"] is False for x in body["rows"])
    first = [a for a in summary["arms"] if a["family"] == "hdc"
             and a["m"] == 197][0]
    assert first["fails"] == 1 and first["fer_blocks"] == 1.0


def test_r9_wall_and_rss_budgets(tmp_path, monkeypatch):
    calls = {"n": 0}

    def _clock():
        calls["n"] += 1
        return 0.0 if calls["n"] <= 2 else 99999.0

    summary, root = _run(tmp_path, monkeypatch, suffix="d0e1f2a3",
                         clock=_clock)
    assert summary["verdict"] == "INCOMPLETE-wall"
    assert Path(root, "rows.json").exists()
    summary2, _ = _run(tmp_path, monkeypatch, suffix="e1f2a3b4",
                       rss_fn=lambda: 5 * 1024 ** 3)
    assert summary2["verdict"] == "FAIL(budget-rss)"


def test_m2lb_helpers_still_verbatim():
    assert m2lb.M2LB_BLOCK_BASE == 2026095601
    assert r.lb_block_seed(0) == 2026095601
    assert r.lb_block_seed(100) == 2026095601 + 100
