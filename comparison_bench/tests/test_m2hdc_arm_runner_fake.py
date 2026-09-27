"""Fake-only tests for the M2HDC thin arm runner (M2-HDCASCADE-SYNTH).

FAKE-ONLY: every bundle/decode here is synthetic and in-test. No
production cascade call is made (every ``execute()`` call passes an
explicit fake ``decode_fn``; the production per-plane path is
monkeypatched to raise); no frozen module is modified; no raw-dump
file is read; all disk use is in pytest tmp_path. Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import m2hdc_arm_runner as h
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.methods import hd_cascade as hc


# -- fakes (explicit; never production) ---------------------------------------

def _fake_bundle(source_key):
    return {"source": source_key, "fake": "bound"}


def _fake_decode(mode="success", record=None):
    """Fake decode_fn(a_planes, b_planes, schedules, frame_idx, seed)."""
    seen = {"n": 0}

    def _fn(a_planes, b_planes, schedules, frame_idx, seed):
        assert len(a_planes) == 10 and len(b_planes) == 10
        assert len(schedules) == 10
        if record is not None:
            record.append({"frame_idx": int(frame_idx),
                           "seed": int(seed)})
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


def _raise(*a, **k):
    raise AssertionError("production path entered by fake test (must inject)")


def _run(tmp_path, monkeypatch, arm, decode_fn, **kw):
    monkeypatch.chdir(tmp_path)  # relative workspace/m2hdc_ roots stay in tmp
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    spec = h.parse_arm(arm)
    suffix = kw.get("suffix", "a1b2c3d4")
    root = f"workspace/m2hdc_{suffix}"
    summary = h.execute(root=root, arm=arm,
                        bundle=_fake_bundle(spec["source_key"]),
                        decode_fn=decode_fn,
                        block_table=kw.get("block_table"),
                        clock=kw.get("clock"),
                        rss_fn=(kw.get("rss_fn") or (lambda: 0)),
                        writer=h.default_writer,
                        max_blocks=kw.get("max_blocks"))
    return summary, root


# -- R1: arm grid ---------------------------------------------------------------

def test_r1_arm_grid_and_labels():
    good = [("M2HDC-1M-197", "1M", 197), ("M2HDC-1M-201", "1M", 201),
            ("M2HDC-1.5M-203", "1p5M", 203),
            ("M2HDC-1.5M-207", "1p5M", 207),
            ("M2HDC-2M-204", "2M", 204), ("M2HDC-2M-208", "2M", 208)]
    assert len(h.GRID["1M"]) + len(h.GRID["1p5M"]) + len(h.GRID["2M"]) == 6
    for arm, key, m in good:
        s = h.parse_arm(arm)
        assert (s["source_key"], s["m"]) == (key, m)
        assert s["construct_label"] == f"M2HDC-{s['display']}-S{m}-hdcascade"
    assert h.parse_arm("M2HDC-1.5M-203")["source_key"] == "1p5M"
    for bad in ("M2HDC-1M-202", "M2HDC-1M-200", "M2HDC-2M-202",
                "M2HDC-1.5M-208", "M2HDC-3M-200", "M2HDC-1M-197-matched",
                "M2LB-1M-197-matched", "X1-2M-208", "", None):
        with pytest.raises(h.Refusal):
            h.parse_arm(bad)


# -- R2: cross-source + bundle file/key refusal -----------------------------------

def test_r2_cross_source_and_bundle_file_key_refusal(tmp_path):
    dec = _fake_decode("success")
    with pytest.raises(h.Refusal):
        h.bind_source_bundle("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz", "1M", "M2HDC-2M-204")
    with pytest.raises(h.Refusal):
        h.bind_source_bundle("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz", "2M", "M2HDC-1M-197")
    with pytest.raises(h.Refusal):
        h.bind_source_bundle("workspace/m2hdc_bundles_1a2b3c4d/other.npz",
                             "1M", "M2HDC-1M-197")
    assert dec.seen["n"] == 0  # zero decodes on refusal
    # frozen consumer refuses a 2M-label bind on a 1M-only file (fake data)
    rng = np.random.default_rng(7)
    g1 = rng.random((32, 1024)) + 0.01
    g1 /= g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 /= g2.sum(axis=1, keepdims=True)
    pb = rng.random((1024,)) + 0.01
    pb /= pb.sum()
    bundle = tmp_path / "gamma_f03.npz"
    np.savez(str(bundle), **{"1M_gamma1_L1": g1,
                             "1M_gamma2_L2condU1": g2})
    np.savez(str(tmp_path / "gamma_f03_pb.npz"), **{"1M_p_b": pb})
    with pytest.raises(s2c.Refusal):
        s2c.bind_empirical_bundle(str(bundle), "2M")
    bound = s2c.bind_empirical_bundle(str(bundle), "1M")
    assert bound["source"] == "1M" and bound["g1"].shape == (32, 1024)


# -- R3: root fresh + forbidden refusal --------------------------------------------

def test_r3_root_fresh_and_forbidden_refusal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    busy = Path("workspace/m2hdc_b1b2b1b2")
    busy.mkdir(parents=True)
    base = {"bundle": _fake_bundle("2M"),
            "decode_fn": _fake_decode(), "rss_fn": lambda: 0,
            "writer": h.default_writer}
    with pytest.raises(h.Refusal):
        h.execute(root=str(busy), arm="M2HDC-2M-204", **base)
    for bad_root in ("results/m2hdc_deadbeef",
                     "comparison_bench/outputs_comparison/m2hdc_deadbeef",
                     "workspace/x1_deadbeef",
                     "workspace/m2lb_a1b2c3d4",
                     "workspace/m2hdc_short",
                     "workspace/m2hdc_toolong_suffix_extra",
                     ""):
        with pytest.raises(h.Refusal):
            h.execute(root=bad_root, arm="M2HDC-2M-204", **base)


# -- R4: sampler 240 x 64 + Gray-10 + verbatim seeds ---------------------------------

def test_r4_sampler_240_n64_gray10_and_verbatim_seeds(tmp_path, monkeypatch):
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v10_common as common,
    )
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite \
        import split_symbol_bitplanes as _split
    for key, arm in (("1M", "M2HDC-1M-197"),
                     ("1p5M", "M2HDC-1.5M-203"),
                     ("2M", "M2HDC-2M-204")):
        batch = h.sample_frozen_batch(_fake_bundle(key), key, arm=arm)
        assert int(batch.alice_symbols.shape[0]) == 240
        assert int(batch.frame_len_symbols) == 64
        assert int(batch.dimension) == 1024
        planes = _split(np.asarray(batch.alice_symbols[0]),
                        int(batch.dimension), "gray")
        assert len(planes) == 10
    # determinism: same arm streams twice
    b1 = h.sample_frozen_batch(_fake_bundle("1M"), "1M",
                               arm="M2HDC-1M-197")
    b2 = h.sample_frozen_batch(_fake_bundle("1M"), "1M",
                               arm="M2HDC-1M-197")
    assert np.array_equal(b1.alice_symbols, b2.alice_symbols)
    # verbatim per-arm seeds A1-A6 5701-5706 +k 0..239 (packet §7-4)
    assert h.M2HDC_ARM_SEED == {
        "M2HDC-1M-197": 2026095701, "M2HDC-1M-201": 2026095702,
        "M2HDC-1.5M-203": 2026095703, "M2HDC-1.5M-207": 2026095704,
        "M2HDC-2M-204": 2026095705, "M2HDC-2M-208": 2026095706}
    assert h.block_seed(0, arm="M2HDC-1M-197") == 2026095701
    assert h.block_seed(239, arm="M2HDC-1M-197") == 2026095701 + 239
    assert h.block_seed(0, arm="M2HDC-2M-208") == 2026095706
    assert h.block_seed(239, arm="M2HDC-2M-208") == 2026095706 + 239
    # verbatim seed derivation (x1 same family)
    assert h.stream_seed(2026095701) == common.v10_seed("o1_blk:2026095701")
    # 2001 construction instance retained; 5601 obsolete note kept
    assert h.M2HDC_CONSTRUCT_SEED == 2026092001
    assert h.M2HDC_BLOCK_BASE == 2026095601
    assert "obsolete" in Path(h.__file__).read_text().lower()
    with pytest.raises(h.Refusal):
        h.sample_frozen_batch(_fake_bundle("1M"), "2M",
                              arm="M2HDC-1M-197")
    with pytest.raises(h.Refusal):
        h.sample_frozen_batch(_fake_bundle("1M"), "1M",
                              arm="M2HDC-2M-204")
    with pytest.raises(h.Refusal):
        h.sample_frozen_batch(_fake_bundle("1M"), "1M", n_blocks=239,
                              arm="M2HDC-1M-197")


def test_r4b_decode_fn_sees_verbatim_block_seeds(tmp_path, monkeypatch):
    rec = []
    summary, _ = _run(tmp_path, monkeypatch, "M2HDC-1M-197",
                      _fake_decode("success", record=rec),
                      max_blocks=3, suffix="b2c3d4e5")
    assert summary["verdict"] == "PROBE-truncated"
    assert [r["seed"] for r in rec] == [
        h.block_seed(0, arm="M2HDC-1M-197"),
        h.block_seed(1, arm="M2HDC-1M-197"),
        h.block_seed(2, arm="M2HDC-1M-197")]
    assert [r["seed"] for r in rec] == [2026095701, 2026095701 + 1,
                                        2026095701 + 2]


# -- R5: block table fail-closed + provisional pins + H --------------------------------

def test_r5_block_table_missing_plane_fail_closed_and_provisional_pins():
    with pytest.raises(ValueError, match="missing planes"):
        hc.HdCascadeBlockTable({p: [8] for p in range(9)}).planes(10)
    with pytest.raises(ValueError, match="missing plane"):
        hc.HdCascadeBlockTable({p: [8] for p in range(9)}).schedule_for(9)
    with pytest.raises(h.Refusal):
        h.check_block_table(hc.HdCascadeBlockTable(
            {p: [8] for p in range(9)}))
    tab = h.provisional_block_table()
    assert tab.planes(10) == list(range(10))
    assert tab.schedule_for(0) == [8, 4]
    assert h.M2HDC_MAX_PASSES_PROVISIONAL == 4
    # provisional slots are marked assumed in the summary path
    assert h.FROZEN_H == dict(hc.FROZEN_H)
    assert h.FROZEN_H == {"1M": 0.801038, "1p5M": 0.825566,
                          "2M": 0.832563}
    # the placeholder default seed of HdCascadeParams is never referenced here
    src = Path(h.__file__).read_text()
    assert ("2026" + "0415") not in src


# -- R6: production patched + outcome fail-closed + undetected --------------------------

def test_r6_production_patched_outcome_fail_closed_undetected(tmp_path,
                                                              monkeypatch):
    monkeypatch.setattr(hc, "_run_planes_production", _raise)
    rec = []
    summary, _ = _run(tmp_path, monkeypatch, "M2HDC-1M-197",
                      _fake_decode("success", record=rec),
                      max_blocks=3, suffix="c3d4e5f6")
    assert summary["verdict"] == "PROBE-truncated"
    assert summary["max_passes_status"].startswith("provisional")
    with pytest.raises(Exception):
        hc._run_planes_production([], [], {}, 0, 4, "seeded_random")
    # execute requires an explicit decode_fn (no silent production)
    with pytest.raises(h.Refusal):
        h.execute(root="workspace/m2hdc_d4e5f6a7", arm="M2HDC-1M-197",
                  bundle=_fake_bundle("1M"), decode_fn=None,
                  rss_fn=lambda: 0, writer=h.default_writer,
                  max_blocks=1)

    def _bad(a_planes, b_planes, schedules, frame_idx, seed):
        return {"exact_match": True, "accepted": True,
                "toeplitz_verified": True, "leak_ec_bits": 1.0,
                "rescue_bits": 0.0, "control_bits": 0.0,
                "messages_actual": 446.0}  # prior_entropy_bits missing

    with pytest.raises(h.Refusal):
        _run(tmp_path, monkeypatch, "M2HDC-1M-197", _bad,
             max_blocks=1, suffix="e5f6a7b8")
    # R3: thin production wrapper is the sole production call site and
    # read-only delegates; execute(None) still refuses (above); only
    # run_execution defaults None to the wrapper as an explicit param.
    import inspect as _inspect
    src = Path(h.__file__).read_text()
    assert src.count("hc._run_planes_production(") == 1
    assert "def _m2hdc_production_decode_fn" in src
    seen = {}

    def _rec(a_planes, b_planes, table, seed, max_passes, perm):
        seen.update(seed=int(seed), max_passes=int(max_passes),
                    perm=str(perm),
                    sweeps=int(table.max_cross_plane_sweeps),
                    planes=list(table.planes(len(table.schedules))))
        return {"ok": True}

    monkeypatch.setattr(hc, "_run_planes_production", _rec)
    out = h._m2hdc_production_decode_fn(
        [0] * 10, [0] * 10, [[8, 4]] * 10, 3, 2026095701)
    assert out == {"ok": True}
    assert seen == {"seed": 2026095701 + 3 * 104729, "max_passes": 4,
                    "perm": "seeded_random", "sweeps": 1,
                    "planes": list(range(10))}
    sig = _inspect.signature(h.run_execution)
    assert sig.parameters["decode_fn"].default is None
    assert "decode_fn = _m2hdc_production_decode_fn" in src


def test_r6b_undetected_logged_separately_never_success(tmp_path,
                                                        monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "M2HDC-1M-197",
                         _fake_decode("undetected"),
                         max_blocks=5, suffix="d4e5f6a7")
    assert summary["undetected"] == 5 and summary["failures"] == 5
    assert summary["fer"] == 1.0
    body = json.load(open(f"{root}/rows.json"))
    assert all(r["undetected"] is True and r["exact_match"] is False
               for r in body["rows"])
    assert body["summary"]["undetected"] == 5


# -- R7: bar/gate arithmetic + CENSORED + INCOMPLETE + outputs -----------------------------

def test_r7_bar_gate_arithmetic_censored_incomplete_outputs(tmp_path,
                                                            monkeypatch):
    assert h.fail_bar(240) == 12
    assert h.f_super_for("1M", 197) == (5 * 197 + 64) / (1024 * 0.801038)
    assert h.f_notag_for("2M", 204) == (5 * 204) / (1024 * 0.832563)
    assert h.f_eff_for(1.2, 0.05) == 1.2 + 4.785675 * 0.05
    assert h.n_required(1.2) == math.ceil(3 * 4.785675 / (1.3 - 1.2))
    assert h.n_required(1.3) == math.inf
    assert h.lambda_total(100.0, 64, 8.0, 0.0) == 172.0
    # bar-12 early-stop CENSORED, never extrapolated to 240
    summary, root = _run(tmp_path, monkeypatch, "M2HDC-2M-204",
                         _fake_decode("fail"), suffix="e5f6a7b8")
    assert summary["verdict"] == "FAIL-early-stop"
    assert summary["censored"] is True
    assert "CENSORED" in summary["curve_label"]
    assert summary["failures"] == 13 and summary["blocks_done"] == 13
    assert "projected NEVER" in summary["curve_label"]
    body = json.load(open(f"{root}/rows.json"))
    assert len(body["rows"]) == 13
    assert summary["nb_decode_calls"] == 0
    # wall-partial INCOMPLETE, retained, never continued
    calls = {"n": 0}

    def _clock():
        calls["n"] += 1
        return 0.0 if calls["n"] <= 2 else 9999.0
    summary2, _ = _run(tmp_path, monkeypatch, "M2HDC-1M-201",
                       _fake_decode("success"), max_blocks=None,
                       clock=_clock, suffix="f6a7b8c9")
    assert summary2["verdict"] == "INCOMPLETE-wall"
    # no resume: the retained root is no longer fresh
    with pytest.raises(h.Refusal):
        _run(tmp_path, monkeypatch, "M2HDC-1M-201",
             _fake_decode("success"), max_blocks=1, suffix="f6a7b8c9")
    # outputs carry the full machine columns
    summary3, root3 = _run(tmp_path, monkeypatch, "M2HDC-2M-204",
                           _fake_decode("success"), suffix="a7b8c9d0")
    assert summary3["verdict"] in ("PASS", "FAIL")
    assert summary3["f_eff"] == summary3["f_super"]
    assert summary3["nb_decode_calls"] == 0
    md = open(f"{root3}/M2HDC_RESULT_2M_204.md").read()
    assert "M2HDC-2M-204" in md and "f_eff" in md
    assert "f_notag" in md and "lambda_total" in md
    assert "nb_decode_calls 0" in md
    csv_text = open(f"{root3}/block_accounting.csv").read()
    header = csv_text.splitlines()[0]
    for col in ("block,seed,exact_match,undetected", "f_super",
                "f_notag", "lambda_total", "rescue_bits",
                "messages_actual", "n_required", "construct_label"):
        assert col in header


# -- R8: CLI dual-flag gate + no raw-dump reads ----------------------------------------------

def test_r8_dual_flag_cli_gate_and_no_raw_dump(capsys):
    with pytest.raises(h.Refusal):
        h.main([])
    with pytest.raises(h.Refusal):
        h.main(["--execute-real", "--arm", "M2HDC-2M-204"])
    # R1: wall cap 5400; R2: per-arm seeds literal for A5 (2026095705+idx)
    assert h.M2HDC_WALL_CAP_S == 5400
    full = ["--execute-real", "--execution-authorized",
            "--arm", "M2HDC-2M-204", "--bundle", "b",
            "--pb-sidecar", "p", "--source-key", "2M",
            "--construct-instance", "2026092001", "--standalone",
            "--seeds", "2026095705+idx", "--stream", "o1_blk:{seed}",
            "--blocks", "240", "--root", "workspace/m2hdc_a1b2c3d4",
            "--per-decode-timeout-s", "300", "--budget-s", "5400"]
    with pytest.raises(h.Refusal):  # 5400 passes the budget gate
        h.main(full)  # (fails later at the bundle path form, not budget)
    err = capsys.readouterr().err
    assert "budget-s" not in err
    assert "seeds must be" not in err
    for bad_budget in ("1799", "1800", "5401"):  # !=5400 refused
        with pytest.raises(h.Refusal):
            h.main(full[:-1] + [bad_budget])
        assert "budget-s" in capsys.readouterr().err
    with pytest.raises(h.Refusal):  # obsolete 5601 literal refused
        bad_seeds = list(full)
        bad_seeds[bad_seeds.index("2026095705+idx")] = "2026095601+idx"
        h.main(bad_seeds)
    assert "seeds must be" in capsys.readouterr().err
    with pytest.raises(h.Refusal):  # wrong blocks literal
        bad_blocks = list(full)
        bad_blocks[bad_blocks.index("240")] = "239"
        h.main(bad_blocks)
    src = Path(h.__file__).read_text()
    forbidden = "." + "tt" + "bin"
    assert forbidden not in src.lower()
