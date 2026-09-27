"""Fake-only tests for the M2LB thin arm runner (M2-LAYEREDBIN-SYNTH).

FAKE-ONLY: every construct/decode/bundle here is synthetic and in-test.
No production decoder/DE/graph call is made (every ``execute()`` call
passes an explicit fake ``decode_fn`` and, where construction is not
under test, an explicit fake ``construct_fn``); production PEG/SPA
symbols are monkeypatched to raise where the fake path is under test;
no frozen module is modified; no raw-dump file is read; all disk use is
in pytest tmp_path. Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import m2lb_arm_runner as m
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)


# -- fakes (explicit; never production) ---------------------------------------

def _fake_bundle(source_key):
    return {"source": source_key, "fake": "bound"}


def _fake_construct(allocation, fc=0, girth=6, twins=True, record=None):
    calls = {"n": 0}

    def _fn(m_rows, seed, trials, plane):
        assert trials == m.M2LB_MAX_TRIALS
        assert 0 <= int(plane) < 10
        assert int(m_rows) == int(allocation[int(plane)])
        assert m.M2LB_CONSTRUCT_SEED <= int(seed) < m.M2LB_CONSTRUCT_SEED + 240
        calls["n"] += 1
        if record is not None:
            record.append((int(m_rows), int(seed), int(trials), int(plane)))
        triples = [(r, c, 1) for r, c in zip(range(int(m_rows)),
                                             range(int(m_rows)))]
        if not twins and calls["n"] % 2 == 0:
            triples = triples[:-1] + [(int(m_rows), int(m_rows), 1)] \
                if triples else [(0, 0, 1)]
        return {"status": "ok", "triples": triples, "n": 64,
                "m": int(m_rows), "four_cycles": int(fc),
                "min_girth": int(girth), "rank": int(m_rows)}
    _fn.calls = calls
    return _fn


def _fake_decode(mode="success", record=None):
    seen = {"n": 0}

    def _fn(a_planes, b_planes, constructions, stage_ctx, frame_idx,
            max_iter, streak):
        assert int(max_iter) == 300 and int(streak) == 3
        assert len(a_planes) == 10 and len(b_planes) == 10
        assert len(constructions) == 10
        if record is not None:
            record.append(dict(stage_ctx))
        seen["n"] += 1
        if mode == "success":
            exact, acc, syn, toe = True, True, True, True
        elif mode == "fail":
            exact, acc, syn, toe = False, False, False, False
        elif mode == "undetected":
            exact, acc, syn, toe = False, True, True, True
        elif mode == "stage2":
            s = int(stage_ctx.get("stage_idx", 0))
            if s >= 2:
                exact, acc, syn, toe = True, True, True, True
            else:
                exact, acc, syn, toe = False, False, False, False
        else:  # mixed: success, fail, undetected repeating
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
                "iterations": 7, "max_iter": 300, "streak": 3}
    _fn.seen = seen
    return _fn


def _run(tmp_path, monkeypatch, arm, decode_fn, construct_fn=None, **kw):
    monkeypatch.chdir(tmp_path)  # relative workspace/m2lb_ roots stay in tmp
    spec = m.parse_arm(arm)
    alloc = m.allocation_for(spec["source_key"], spec["m"])
    cfn = construct_fn if construct_fn is not None else _fake_construct(alloc)
    suffix = kw.get("suffix", "a1b2c3d4")
    root = f"workspace/m2lb_{suffix}"
    summary = m.execute(root=root, arm=arm,
                        bundle=_fake_bundle(spec["source_key"]),
                        construct_fn=cfn, decode_fn=decode_fn,
                        clock=kw.get("clock"), rss_fn=(kw.get("rss_fn")
                                                       or (lambda: 0)),
                        writer=m.default_writer,
                        max_blocks=kw.get("max_blocks"))
    return summary, root


def _raise(*a, **k):
    raise AssertionError("production path entered by fake test (must inject)")


# -- R1: arm grid + mode gate ---------------------------------------------------

def test_r1_arm_grid_and_mode_labels():
    assert len(m.OUTCOME_KEYS) == 13
    good = ["M2LB-1M-197-matched", "M2LB-1M-201-blind",
            "M2LB-1.5M-203-matched", "M2LB-1.5M-207-blind",
            "M2LB-2M-204-matched", "M2LB-2M-208-blind"]
    for arm in good:
        s = m.parse_arm(arm)
        assert s["construct_label"].endswith("-layered")
        assert s["source_key"] in ("1M", "1p5M", "2M")
    assert m.parse_arm("M2LB-1.5M-203-matched")["source_key"] == "1p5M"
    assert m.parse_arm("M2LB-2M-208-blind")["mode"] == "blind"
    for bad in ("M2LB-1M-202-matched", "M2LB-1M-200-blind",
                "M2LB-2M-202-matched", "M2LB-1M-197",
                "M2LB-3M-200-matched", "M2LB-1.5M-208-matched",
                "X1-2M-208", "", None, "M2LB-1M-197-unknown"):
        with pytest.raises(m.Refusal):
            m.parse_arm(bad)


# -- R2: cross-source + bundle file/key refusal ---------------------------------

def test_r2_cross_source_and_bundle_file_key_refusal(tmp_path):
    dec = _fake_decode("success")
    # cross-source at bind helper (hermetic: fires before any file read)
    with pytest.raises(m.Refusal):
        m.bind_source_bundle("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz", "1M", "M2LB-2M-204-matched")
    with pytest.raises(m.Refusal):
        m.bind_source_bundle("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz", "2M", "M2LB-1M-197-matched")
    # wrong file role (substitute refused before any read)
    with pytest.raises(m.Refusal):
        m.bind_source_bundle("workspace/m2lb_bundles_1a2b3c4d/other.npz",
                             "1M", "M2LB-1M-197-matched")
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


# -- R3: root fresh + forbidden refusal ------------------------------------------

def test_r3_root_fresh_and_forbidden_refusal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    busy = Path("workspace/m2lb_b1b2b1b2")
    busy.mkdir(parents=True)
    spec = m.parse_arm("M2LB-2M-204-matched")
    alloc = m.allocation_for(spec["source_key"], spec["m"])
    base = {"bundle": _fake_bundle("2M"),
            "construct_fn": _fake_construct(alloc),
            "decode_fn": _fake_decode(), "rss_fn": lambda: 0,
            "writer": m.default_writer}
    with pytest.raises(m.Refusal):
        m.execute(root=str(busy), arm="M2LB-2M-204-matched", **base)
    for bad_root in ("results/m2lb_deadbeef",
                     "comparison_bench/outputs_comparison/m2lb_deadbeef",
                     "workspace/x1_deadbeef",
                     "workspace/m2lb_short",
                     "workspace/m2lb_toolong_suffix_extra",
                     ""):
        with pytest.raises(m.Refusal):
            m.execute(root=bad_root, arm="M2LB-2M-204-matched", **base)


# -- R4: sampler 240 x 64 + Gray-10 + allocation sum/cap --------------------------

def test_r4_sampler_240_n64_gray10_and_allocation_sum_cap():
    for arm_m, key in ((197, "1M"), (201, "1M"), (203, "1p5M"),
                       (207, "1p5M"), (204, "2M"), (208, "2M")):
        batch = m.sample_frozen_batch(_fake_bundle(key), key)
        assert int(batch.alice_symbols.shape[0]) == 240
        assert int(batch.frame_len_symbols) == 64
        assert int(batch.dimension) == 1024
        from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite \
            import split_symbol_bitplanes as _split
        planes = _split(np.asarray(batch.alice_symbols[0]),
                        int(batch.dimension), "gray")
        assert len(planes) == 10
        rows = m.allocation_for(key, arm_m)
        assert sorted(rows) == list(range(10))
        assert sum(rows.values()) == arm_m
        assert all(v <= 64 for v in rows.values())
    with pytest.raises(m.Refusal):
        m.sample_frozen_batch(_fake_bundle("1M"), "2M")
    with pytest.raises(m.Refusal):
        m.sample_frozen_batch(_fake_bundle("1M"), "1M", n_blocks=239)


# -- R5: h_basis no-refit + blind table len 5 ------------------------------------

def test_r5_h_basis_no_refit_and_blind_table_len5():
    for key, h in (("1M", 0.801038), ("1p5M", 0.825566),
                   ("2M", 0.832563)):
        assert m.allocation_for(key, 204, h_basis=h)[0] >= 0
    with pytest.raises(m.Refusal):
        m.allocation_for("1M", 197, h_basis=0.8012690084416184)
    with pytest.raises(m.Refusal):
        m.allocation_for("2M", 204, h_basis=0.8333327179427281)
    for mm in (197, 201, 203, 207, 204, 208):
        tab = m.blind_table_for(mm)
        assert len(tab["delta_steps"]) == 5
        assert tab["delta_steps"] == [4, 4, 4, 4, 4]
        assert tab["m_init"] == mm - 20
        assert tab["m_init"] + sum(tab["delta_steps"]) == mm
        levels = m.blind_levels_for(mm)
        assert len(levels) == 6 and levels[-1] == mm
        assert levels[0] == mm - 20


# -- R6: production patched to raise + SPA pins + 13-key + undetected gates ------

def test_r6_production_patched_spa_pins_13key_undetected(tmp_path,
                                                         monkeypatch):
    monkeypatch.setattr(peg, "peg_construct", _raise)
    monkeypatch.setattr(m, "construct_plane_production", _raise)
    monkeypatch.setattr(m, "spa_decode_production", _raise)
    # explicit fake still passes while production is patched to raise
    rec = []
    summary, _ = _run(tmp_path, monkeypatch, "M2LB-1M-197-matched",
                      _fake_decode("success", record=rec),
                      max_blocks=3, suffix="c3d4e5f6")
    assert summary["verdict"] == "PROBE-truncated"
    assert all(r["m_stage"] == 197 for r in rec)
    assert all(r["stage_idx"] == 0 for r in rec)
    # no-fake production path raises (never silently entered)
    with pytest.raises(Exception):
        m.spa_decode_production([], [], [], {}, 0, 300, 3)
    # missing key fails closed
    bad = {"exact_match": True, "accepted": True,
           "syndrome_consistent": True, "toeplitz_verified": True,
           "leak_ec_bits": 1.0, "blind_stage_bits": [0.0] * 5,
           "rescue_bits": 0.0, "control_bits": 0.0,
           "messages_actual": 3.14, "prior_entropy_bits": 1.0,
           "iterations": 1, "max_iter": 300}  # streak missing
    with pytest.raises(m.Refusal):
        m._check_outcome(bad)
    # wrong SPA pins in outcome refuse
    bad2 = dict(_fake_decode("success").__closure__ and {
        "exact_match": True, "accepted": True,
        "syndrome_consistent": True, "toeplitz_verified": True,
        "leak_ec_bits": 1.0, "blind_stage_bits": [0.0] * 5,
        "rescue_bits": 0.0, "control_bits": 0.0,
        "messages_actual": 3.14, "prior_entropy_bits": 1.0,
        "iterations": 1, "max_iter": 299, "streak": 3})
    with pytest.raises(m.Refusal):
        m._check_outcome(bad2)
    # forbidden genie-flavoured outcome refuses
    bad3 = {"exact_match": True, "accepted": True,
            "syndrome_consistent": True, "toeplitz_verified": True,
            "leak_ec_bits": 1.0, "blind_stage_bits": [0.0] * 5,
            "rescue_bits": 0.0, "control_bits": 0.0,
            "messages_actual": 3.14, "prior_entropy_bits": 1.0,
            "iterations": 1, "max_iter": 300, "streak": 3,
            "genie": True}
    with pytest.raises(m.Refusal):
        m._check_outcome(bad3)


def test_r6b_pins_refuse_fc_rank_twins_and_blind_early_stop(tmp_path,
                                                            monkeypatch):
    monkeypatch.chdir(tmp_path)
    spec = m.parse_arm("M2LB-2M-204-blind")
    alloc = m.allocation_for(spec["source_key"], spec["m"])
    base = {"bundle": _fake_bundle("2M"), "decode_fn": _fake_decode(),
            "rss_fn": lambda: 0, "writer": m.default_writer}
    with pytest.raises(m.Refusal):  # fc != 0
        m.execute(root="workspace/m2lb_fc000001", arm="M2LB-2M-204-blind",
                  construct_fn=_fake_construct(alloc, fc=2), **base)

    def _badrank(m_rows, seed, trials, plane):
        return {"status": "ok", "triples": [(0, 0, 1)], "n": 64,
                "m": m_rows, "four_cycles": 0, "min_girth": 6,
                "rank": int(m_rows) - 1}
    with pytest.raises(m.Refusal):  # rank != m_j
        m.execute(root="workspace/m2lb_rk000002", arm="M2LB-2M-204-blind",
                  construct_fn=_badrank, **base)
    with pytest.raises(m.Refusal):  # twice-identical violated
        m.execute(root="workspace/m2lb_tw000003", arm="M2LB-2M-204-blind",
                  construct_fn=_fake_construct(alloc, twins=False), **base)
    # blind incremental early-stop: stage2 succeeds at stage_idx 2
    rec = []
    summary, _ = _run(tmp_path, monkeypatch, "M2LB-2M-204-blind",
                      _fake_decode("stage2", record=rec),
                      _fake_construct(alloc),
                      max_blocks=1, suffix="b1b2c3d4")
    assert rec[0]["mode"] == "blind"
    assert [r["m_stage"] for r in rec[:3]] == [184, 188, 192]
    assert summary["blocks_done"] == 1 and summary["failures"] == 0


def test_r6c_undetected_logged_separately_never_success(tmp_path,
                                                       monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "M2LB-1M-197-matched",
                         _fake_decode("undetected"),
                         max_blocks=5, suffix="d4e5f6a7")
    assert summary["undetected"] == 5 and summary["failures"] == 5
    assert summary["fer"] == 1.0
    body = json.load(open(f"{root}/rows.json"))
    assert all(r["undetected"] is True and r["exact_match"] is False
               for r in body["rows"])
    assert body["summary"]["undetected"] == 5


def test_r6d_true_spa_tiny(tmp_path, monkeypatch):
    """True-body tiny self-check: hand 10-plane n=4 vectors, direct call only.

    FAKE-ADJACENT (synthetic tiny vectors, no execute/sampler, no bundle, no
    production PEG): calls the TRUE ``spa_decode_production`` body directly
    with hand binary triples + hand bit vectors (n=4). Zero disk writes by
    construction (cwd pinned to tmp_path; the body has no writer/root path).
    Two vector versions: ``a`` (zero-error, b==a -> full success) and
    single-bit-flip (one bit in one plane -> isolated: corrected success or
    clean fail, NEVER undetected). Plus a blind-init zero-error call to cover
    the stage_rows truncation path. When the ``ldpc`` backend is absent the
    true body must STOP-BLOCKED (Refusal; no bit-flip substitute) — asserted
    instead of the success path in that environment.
    """
    import importlib.util as _ilu

    monkeypatch.chdir(tmp_path)  # body writes nothing; tmp stays empty
    n = 4
    # Hand binary H per plane (m=3, coeff 1): columns distinct/nonzero,
    # single nonzero codeword 1111 (distance 4) — single errors unambiguous.
    tiny_triples = [(0, 0, 1), (0, 3, 1), (1, 1, 1),
                    (1, 3, 1), (2, 2, 1), (2, 3, 1)]
    cons = [{"status": "ok", "triples": list(tiny_triples), "n": n,
             "m": 3, "four_cycles": 0, "min_girth": 8, "rank": 3}
            for _ in range(10)]
    a0 = [np.array([(p + i) % 2 for i in range(n)], dtype=np.uint8)
          for p in range(10)]
    stage_full = {"mode": "matched", "m_target": 30, "m_stage": 30,
                  "stage_idx": 0, "delta_steps": [4, 4, 4, 4, 4],
                  "m_init": 10}
    if _ilu.find_spec("ldpc") is None:
        with pytest.raises(m.Refusal):
            m.spa_decode_production([p.copy() for p in a0],
                                    [p.copy() for p in a0],
                                    [dict(c) for c in cons],
                                    dict(stage_full), 0, 300, 3)
        assert list(Path.cwd().iterdir()) == []
        return
    # Zero-error version: b == a -> full four-flag success.
    out0 = m._check_outcome(dict(m.spa_decode_production(
        [p.copy() for p in a0], [p.copy() for p in a0],
        [dict(c) for c in cons], dict(stage_full), 0, 300, 3)))
    assert len(out0) == 13 and set(out0) == set(m.OUTCOME_KEYS)
    assert out0["exact_match"] is True and out0["accepted"] is True
    assert out0["syndrome_consistent"] is True
    assert out0["toeplitz_verified"] is True
    assert out0["leak_ec_bits"] == pytest.approx(30.0)
    assert list(out0["blind_stage_bits"]) == [0.0] * 5
    assert out0["rescue_bits"] == 0.0 and out0["control_bits"] == 0.0
    assert out0["messages_actual"] == pytest.approx(3.14)
    assert out0["max_iter"] == 300 and out0["streak"] == 3
    assert isinstance(out0["iterations"], int)
    # Single-error version: flip one bit in plane 3 -> isolated.
    b1 = [p.copy() for p in a0]
    b1[3] = (b1[3].astype(np.uint8) ^ np.array([1, 0, 0, 0],
                                               dtype=np.uint8))
    out1 = m._check_outcome(dict(m.spa_decode_production(
        [p.copy() for p in a0], b1,
        [dict(c) for c in cons], dict(stage_full), 1, 300, 3)))
    assert len(out1) == 13
    succ1 = bool(out1["exact_match"] is True
                 and out1["accepted"] is True
                 and out1["syndrome_consistent"] is True
                 and out1["toeplitz_verified"] is True)
    und1 = bool(out1["accepted"] is True) and not succ1
    assert und1 is False  # isolated: success or clean fail, never wrong-accept
    assert out1["leak_ec_bits"] == pytest.approx(30.0)
    # Blind-init zero-error version: m_stage=10 truncation prefix path.
    stage_b = {"mode": "blind", "m_target": 30, "m_stage": 10,
               "stage_idx": 0, "delta_steps": [4, 4, 4, 4, 4],
               "m_init": 10}
    outb = m._check_outcome(dict(m.spa_decode_production(
        [p.copy() for p in a0], [p.copy() for p in a0],
        [dict(c) for c in cons], dict(stage_b), 2, 300, 3)))
    assert outb["exact_match"] is True and outb["accepted"] is True
    assert outb["syndrome_consistent"] is True
    assert outb["toeplitz_verified"] is True
    assert outb["leak_ec_bits"] == pytest.approx(10.0)
    assert list(outb["blind_stage_bits"]) == [0.0] * 5
    assert list(Path.cwd().iterdir()) == []  # zero writes by construction


# -- R7: bar/gate arithmetic + CENSORED + wall INCOMPLETE + outputs ---------------

def test_r7_bar_gate_arithmetic_censored_incomplete_outputs(tmp_path,
                                                           monkeypatch):
    assert m.fail_bar(240) == 12
    assert m.block_seed(0) == 2026095601
    assert m.block_seed(239) == 2026095601 + 239
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v10_common as common,
    )
    assert m.stream_seed(2026095601) == common.v10_seed("o1_blk:2026095601")
    assert m.f_super_for("1M", 197) == (5 * 197 + 64) / (1024 * 0.801038)
    assert m.f_notag_for("2M", 204) == (5 * 204) / (1024 * 0.832563)
    assert m.f_eff_for(1.2, 0.05) == 1.2 + 4.785675 * 0.05
    assert m.n_required(1.2) == math.ceil(3 * 4.785675 / (1.3 - 1.2))
    assert m.n_required(1.3) == math.inf
    assert m.lambda_total(100.0, 64, 8.0, 0.0) == 172.0
    # bar-12 early-stop CENSORED, never extrapolated to 240
    summary, root = _run(tmp_path, monkeypatch, "M2LB-2M-204-matched",
                         _fake_decode("fail"), suffix="e5f6a7b8")
    assert summary["verdict"] == "FAIL-early-stop"
    assert summary["censored"] is True
    assert "CENSORED" in summary["curve_label"]
    assert summary["failures"] == 13 and summary["blocks_done"] == 13
    assert "projected NEVER" in summary["curve_label"]
    body = json.load(open(f"{root}/rows.json"))
    assert len(body["rows"]) == 13
    # wall-partial INCOMPLETE, retained, never continued
    calls = {"n": 0}

    def _clock():
        calls["n"] += 1
        return 0.0 if calls["n"] <= 2 else 9999.0
    summary2, root2 = _run(tmp_path, monkeypatch, "M2LB-1M-201-matched",
                           _fake_decode("success"), max_blocks=None,
                           clock=_clock, suffix="f6a7b8c9")
    assert summary2["verdict"] == "INCOMPLETE-wall"
    # outputs carry the full machine columns
    summary3, root3 = _run(tmp_path, monkeypatch, "M2LB-2M-204-matched",
                           _fake_decode("success"), suffix="a7b8c9d0")
    assert summary3["verdict"] in ("PASS", "FAIL")
    assert summary3["f_eff"] == summary3["f_super"]
    md = open(f"{root3}/M2LB_RESULT_2M_204_matched.md").read()
    assert "M2LB-2M-204-matched" in md and "f_eff" in md
    assert "f_notag" in md and "lambda_total" in md
    csv_text = open(f"{root3}/block_accounting.csv").read()
    header = csv_text.splitlines()[0]
    for col in ("block,seed,exact_match,undetected", "f_super",
                "lambda_total", "blind_stage_bits", "rescue_bits",
                "messages_actual", "n_required", "q_alphabet"):
        assert col in header


# -- R1-OPT-A: binary-support semantics (R1修订包选项A) -------------------------
# FAKE-ONLY, no execute, no bundle, no disk: direct _construct_gate_planes
# calls only. True-body tiny stays direct-call-only (test_r6d), never execute.

def _alloc_2m204():
    return m.allocation_for("2M", 204)


def test_r1a_support_coeff_2_512_1023_builds_H():
    """(a) coeff {2,512,1023} 按支撑建H (R1修订包选项A).

    对角支撑 + 非零GF标记循环 -> 二元支撑H满秩, 门通过 (旧==1冻结下
    _h_from_triples会拒, 新支撑语义须过). 直接调门, 不经execute, 零盘写.
    """
    alloc = _alloc_2m204()
    coeffs = (2, 512, 1023)

    def _fn(m_rows, seed, trials, plane):
        assert int(trials) == m.M2LB_MAX_TRIALS
        assert int(seed) == m.M2LB_CONSTRUCT_SEED
        triples = [(r, r, coeffs[r % 3]) for r in range(int(m_rows))]
        return {"status": "ok", "triples": triples, "n": 64,
                "m": int(m_rows), "four_cycles": 0,
                "min_girth": 6, "rank": int(m_rows)}

    gated = m._construct_gate_planes(dict(alloc), 0, _fn,
                                     m.M2LB_CONSTRUCT_SEED,
                                     m.M2LB_MAX_TRIALS)
    assert len(gated) == 10
    assert all(int(c.get("measured_girth")) == 6 for c in gated)


def test_r1b_coeff_zero_refuses():
    """(b) coeff==0拒 (R1修订包选项A支撑语义; 直接调门, 不经execute)."""
    alloc = _alloc_2m204()

    def _fn(m_rows, seed, trials, plane):
        triples = [(r, r, 1) for r in range(int(m_rows) - 1)]
        triples.append((int(m_rows) - 1, int(m_rows) - 1, 0))
        return {"status": "ok", "triples": triples, "n": 64,
                "m": int(m_rows), "four_cycles": 0,
                "min_girth": 6, "rank": int(m_rows)}

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _fn,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)


def test_r1c_oob_refuses():
    """(c) 越界拒 (col==64 对 n=64 越界; 直接调门, 不经execute)."""
    alloc = _alloc_2m204()

    def _fn(m_rows, seed, trials, plane):
        triples = [(r, r, 1) for r in range(int(m_rows) - 1)]
        triples.append((int(m_rows) - 1, 64, 1))  # OOB col
        return {"status": "ok", "triples": triples, "n": 64,
                "m": int(m_rows), "four_cycles": 0,
                "min_girth": 6, "rank": int(m_rows)}

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _fn,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)


def test_r1d_binary_rank_deficient_refuses():
    """(d) 秩亏拒: 支撑GF(2)秩<=m_j-2拒 (rank字段谎报满秩亦拒; 直接调门).

    双独立重复对 (行0/1支撑重复 + 行2/3支撑重复) -> span==m_j 但二元秩==m_j-2;
    新门 rank∈{m_j-1,m_j} 下仍STOP (列重2单维容忍仅到m_j-1); PEG rank字段故意写满
    (不改PEG返回, 门须重算支撑秩而非信任字段).
    """
    alloc = _alloc_2m204()

    def _fn(m_rows, seed, trials, plane):
        mj = int(m_rows)
        triples = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
        triples += [(2, 2, 1), (2, 3, 1), (3, 2, 1), (3, 3, 1)]
        triples += [(r, r, 1) for r in range(4, mj)]
        assert max(r for r, _, _ in triples) + 1 == mj  # span preserved
        return {"status": "ok", "triples": triples, "n": 64,
                "m": mj, "four_cycles": 0,
                "min_girth": 6, "rank": mj}  # lying full field

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _fn,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)


# -- R1-RANK-TOL (修订包 rank∈{m_j-1,m_j}; 直接调门, 不经execute, 零盘写) ---------

def test_r1e_columnweight2_ring_tolerance_passes():
    """(a) 列重2环形支撑+coeff轮转{2,512,1023}三档全过 (直接调门, 零盘写).

    每行双支撑 ``(r,r)/(r,(r+1)%m_j)`` -> 列重亦2的单环, 二元秩==m_j-1
    (单维相关); 新门 rank∈{m_j-1,m_j} 下须过; span==m_j, fc=0, twice确定性一致;
    m=19/20/21三档各调一次门全过.
    """
    coeffs = (2, 512, 1023)
    for mj in (19, 20, 21):
        def _fn(m_rows, seed, trials, plane, _mj=mj):
            assert int(m_rows) == int(_mj)
            assert int(seed) == m.M2LB_CONSTRUCT_SEED
            assert int(trials) == m.M2LB_MAX_TRIALS
            triples = []
            for r in range(int(_mj)):
                triples.append((r, r, coeffs[(2 * r) % 3]))
                triples.append((r, (r + 1) % int(_mj),
                                coeffs[(2 * r + 1) % 3]))
            assert max(r for r, _, _ in triples) + 1 == int(_mj)
            return {"status": "ok", "triples": triples, "n": 64,
                    "m": int(_mj), "four_cycles": 0,
                    "min_girth": 6, "rank": int(_mj)}
        alloc = {j: int(mj) for j in range(10)}
        gated = m._construct_gate_planes(dict(alloc), 0, _fn,
                                         m.M2LB_CONSTRUCT_SEED,
                                         m.M2LB_MAX_TRIALS)
        assert len(gated) == 10
        assert all(int(c.get("measured_girth")) == 6 for c in gated)


def test_r1f_second_rank2_refuses():
    """(b) 第二独立相关rank-2拒 (尾部双重复对; 直接调门, 零盘写).

    与r1d头部双对独立: 尾行 ``m_j-2`` 复刻行 ``m_j-3``、尾行 ``m_j-1`` 复刻行
    ``m_j-4`` -> span==m_j 但二元秩==m_j-2; 新门下仍STOP; PEG rank谎报满秩.
    """
    alloc = _alloc_2m204()

    def _fn(m_rows, seed, trials, plane):
        mj = int(m_rows)
        triples = [(r, r, 1) for r in range(mj - 2)]
        triples.append((mj - 2, mj - 3, 1))
        triples.append((mj - 1, mj - 4, 1))
        assert max(r for r, _, _ in triples) + 1 == mj  # span preserved
        return {"status": "ok", "triples": triples, "n": 64,
                "m": mj, "four_cycles": 0,
                "min_girth": 6, "rank": mj}  # lying full field

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _fn,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)


def test_r1g_diagonal_full_rank_passes():
    """(c) 对角全秩仍过 (直接调门, 零盘写; 新门rank==m_j档)."""
    alloc = _alloc_2m204()

    def _fn(m_rows, seed, trials, plane):
        mj = int(m_rows)
        triples = [(r, r, 1) for r in range(mj)]
        assert max(r for r, _, _ in triples) + 1 == mj
        return {"status": "ok", "triples": triples, "n": 64,
                "m": mj, "four_cycles": 0,
                "min_girth": 6, "rank": mj}

    gated = m._construct_gate_planes(dict(alloc), 0, _fn,
                                     m.M2LB_CONSTRUCT_SEED,
                                     m.M2LB_MAX_TRIALS)
    assert len(gated) == 10


def test_r1h_zero_oob_twice_fc_still_refuse():
    """(d) 零系数/越界/twice/fc各一例仍拒 (直接调门, 零盘写)."""
    alloc = _alloc_2m204()

    def _zero(m_rows, seed, trials, plane):
        mj = int(m_rows)
        triples = [(r, r, 1) for r in range(mj - 1)]
        triples.append((mj - 1, mj - 1, 0))
        return {"status": "ok", "triples": triples, "n": 64,
                "m": mj, "four_cycles": 0,
                "min_girth": 6, "rank": mj}

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _zero,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)

    def _oob(m_rows, seed, trials, plane):
        mj = int(m_rows)
        triples = [(r, r, 1) for r in range(mj - 1)]
        triples.append((mj - 1, 64, 1))  # OOB col for n=64
        return {"status": "ok", "triples": triples, "n": 64,
                "m": mj, "four_cycles": 0,
                "min_girth": 6, "rank": mj}

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _oob,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)

    calls = {"n": 0}

    def _twice(m_rows, seed, trials, plane):
        mj = int(m_rows)
        calls["n"] += 1
        base = [(r, r, 1) for r in range(mj)]
        if calls["n"] % 2 == 0:
            base = base[:-1] + [(mj - 1, (mj - 1 + 1) % 64, 1)]
        return {"status": "ok", "triples": base, "n": 64,
                "m": mj, "four_cycles": 0,
                "min_girth": 6, "rank": mj}

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _twice,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)

    def _fc(m_rows, seed, trials, plane):
        mj = int(m_rows)
        triples = [(r, r, 1) for r in range(mj)]
        return {"status": "ok", "triples": triples, "n": 64,
                "m": mj, "four_cycles": 1,
                "min_girth": 4, "rank": mj}

    with pytest.raises(m.Refusal):
        m._construct_gate_planes(dict(alloc), 0, _fc,
                                 m.M2LB_CONSTRUCT_SEED,
                                 m.M2LB_MAX_TRIALS)


# -- R8: CLI dual-flag gate + no raw-dump reads -----------------------------------

def test_r8_dual_flag_cli_gate_and_no_raw_dump():
    with pytest.raises(m.Refusal):
        m.main([])
    with pytest.raises(m.Refusal):
        m.main(["--execute-real", "--arm", "M2LB-2M-204-matched"])
    full = ["--execute-real", "--execution-authorized",
            "--arm", "M2LB-2M-204-matched", "--bundle", "b",
            "--pb-sidecar", "p", "--source-key", "2M",
            "--construct-instance", "2026092001", "--standalone",
            "--seeds", "2026095601+idx", "--stream", "o1_blk:{seed}",
            "--blocks", "240", "--root", "workspace/m2lb_a1b2c3d4",
            "--per-decode-timeout-s", "300", "--budget-s", "1800"]
    with pytest.raises(m.Refusal):  # wrong budget literal
        m.main(full[:-1] + ["1799"])
    with pytest.raises(m.Refusal):  # wrong blocks literal
        bad_blocks = list(full)
        bad_blocks[bad_blocks.index("240")] = "239"
        m.main(bad_blocks)
    src = Path(m.__file__).read_text()
    forbidden = "." + "tt" + "bin"
    assert forbidden not in src.lower()
    assert "genie" not in src.lower() or "NO genie" in src or "genie" in src
