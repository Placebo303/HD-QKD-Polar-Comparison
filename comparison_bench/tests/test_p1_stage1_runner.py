"""Fake-only tests for the P1 Stage-1 rescue thin runner (packet §10(b), G-P1S1).

FAKE-ONLY: every construct / decode / rescue-decode / rank / channel here is
synthetic and in-test. No production decoder, DE, or graph-kernel call is
made (every ``execute()`` call passes explicit fake ``construct_fn`` /
``decode_fn`` / ``rescue_decode_fn`` / ``rank_fn``); no real-data path
appears; no frozen module is modified (AGENTS.md §10.1 clause 8); all disk
use is pytest ``tmp_path`` (the real frozen channel is never read here —
``--dry`` is exercised against a tmp fake channel). Run per-file ONLY:

PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_p1_stage1_runner.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_common as common,
)


# -- fakes (explicit; never production) ----------------------------------------

def _fake_construct(variant: str = "ok"):
    """Fake A208 constructor: ``(instance, trials) -> code dict``.

    Diagonal triples keep the REAL ``sparse_to_dense`` rank path coherent
    (full rank 208, base rank 200), while fc/rank/twins/nm variants exercise
    each F6 gate.
    """
    calls = {"n": 0}

    def _fn(instance, trials):
        assert instance in (2026092001, 2026092011)
        assert trials == p.P1_MAX_TRIALS
        calls["n"] += 1
        triples = [(r, r, 1) for r in range(p.P1_M_TOTAL)]
        if variant == "twins" and calls["n"] == 2:
            triples = list(triples)[:-1] + [(0, 1, 1)]  # differs ⇒ gate
        code = {"status": "ok", "triples": list(triples),
                "n": p.P1_N, "m": p.P1_M_TOTAL, "four_cycles": 0,
                "min_girth": 8, "rank": p.P1_M_TOTAL,
                "family": "peg-irregular"}
        if variant == "fc":
            code["four_cycles"] = 2
        if variant == "rank":
            code["rank"] = p.P1_M_TOTAL - 1
        if variant == "nm":
            code["n"] = 999
        return code

    _fn.calls = calls
    return _fn


def _rank_ok(dense):
    """Fake rank_fn for the diagonal fakes: asserts the F6 base shape."""
    assert np.asarray(dense).shape == (p.P1_M_BASE, p.P1_N)
    return p.P1_M_BASE  # 200


def _rank_bad(dense):
    return p.P1_M_BASE - 1  # 199 ⇒ STOP-BLOCKED


def _fake_decode(mode: str = "success"):
    """Fake Stage-1 decode_fn: success / fail / undetected / mixed (i%3).

    Asserts the F2/F10 contract on EVERY call: nested base m=200
    construction, rescue rows never present, strictly sequential frozen
    seeds from 2026096401.
    """
    seen = {"n": 0}

    def _fn(construction, seed):
        assert construction["m"] == p.P1_M_BASE
        assert construction["n"] == p.P1_N
        assert all(int(t[0]) < p.P1_M_BASE
                   for t in construction["triples"])  # no rescue rows
        assert seed == p.P1_BLOCK_BASE + seen["n"]
        seen["n"] += 1
        i = seen["n"] - 1
        if mode == "success":
            exact, conv = True, True
        elif mode == "fail":
            exact, conv = False, False
        elif mode == "undetected":
            exact, conv = False, True
        elif mode == "broken":  # missing report-only fields ⇒ fail closed
            return {"status": "success", "iterations": 7,
                    "reconstruction_ok": True, "exact_match": True}
        else:  # mixed: success, fail, undetected repeating
            exact, conv = (True, True) if i % 3 == 0 else (
                (False, False) if i % 3 == 1 else (False, True))
        return {"status": "success" if conv else "max_iter_reached",
                "iterations": 7, "reconstruction_ok": conv,
                "exact_match": exact, "seed": seed,
                "prior_entropy_bits": 850.0, "u1_mismatches": 3}

    _fn.seen = seen
    return _fn


def _fake_rescue(mode: str = "all"):
    """Fake Stage-2 rescue_decode_fn: all / none / even (by block_idx).

    Asserts the F2 COLD full-matrix contract on EVERY call: full m=208
    construction WITH rescue rows rows[200,208) present, frozen seed range.
    """
    seen = {"n": 0, "seeds": []}

    def _fn(construction, seed):
        assert construction["m"] == p.P1_M_TOTAL
        assert construction["n"] == p.P1_N
        assert any(int(t[0]) >= p.P1_M_BASE
                   for t in construction["triples"])  # rescue rows present
        assert p.P1_BLOCK_BASE <= seed < p.P1_BLOCK_BASE + p.P1_N_BLOCKS
        seen["n"] += 1
        seen["seeds"].append(seed)
        idx = seed - p.P1_BLOCK_BASE
        if mode == "all":
            exact, conv = True, True
        elif mode == "none":
            exact, conv = False, False
        else:  # even: even block_idx rescued, odd stays failed
            exact, conv = (True, True) if idx % 2 == 0 else (False, False)
        return {"status": "success" if conv else "max_iter_reached",
                "iterations": 5, "reconstruction_ok": conv,
                "exact_match": exact, "seed": seed,
                "prior_entropy_bits": 840.0, "u1_mismatches": 1}

    _fn.seen = seen
    return _fn


class _Clock:
    """Scripted clock: each call returns t then advances by ``step``."""

    def __init__(self, step: float = 1.0):
        self.t = 0.0
        self.step = float(step)

    def __call__(self):
        v = self.t
        self.t += self.step
        return v


def _run(tmp_path, monkeypatch, arm, decode_fn, rescue_fn, *,
         construct_fn=None, rank_fn=None, clock=None, rss_fn=None):
    monkeypatch.chdir(tmp_path)  # relative workspace/P1_STAGE1 roots in tmp
    root = f"{p.P1_ROOT_PREFIX}{arm}_deadbeef"
    summary = p.execute(root=root, arm=arm,
                        construct_fn=(construct_fn if construct_fn is not None
                                      else _fake_construct()),
                        decode_fn=decode_fn,
                        rescue_decode_fn=rescue_fn,
                        rank_fn=(rank_fn if rank_fn is not None
                                 else _rank_ok),
                        clock=clock,
                        rss_fn=(rss_fn if rss_fn is not None
                                else (lambda: 0)),
                        writer=p.default_writer)
    return summary, root


def _write_fake_channel(tmp_path: Path) -> Path:
    rng = np.random.default_rng(7)
    g1 = rng.random((32, 1024)) + 0.01
    g1 /= g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 /= g2.sum(axis=1, keepdims=True)
    pb = rng.random((1024,)) + 0.01
    pb /= pb.sum()
    main = tmp_path / "gamma_f03.npz"
    np.savez(str(main), **{"2M_gamma1_L1": g1, "2M_gamma2_L2condU1": g2,
                           "2M_p_b": pb})
    np.savez(str(tmp_path / "gamma_f03_pb.npz"), **{"2M_p_b": pb})
    return main


# -- F1 two-arm table ------------------------------------------------------------

def test_parse_arm_frozen_two_arm_table():
    assert p.parse_arm("P1S1-R1")["instance"] == 2026092001
    assert p.parse_arm("P1S1-R2")["instance"] == 2026092011
    assert p.ARMS == {"P1S1-R1": 2026092001, "P1S1-R2": 2026092011}
    for bad in ("P1S1-R3", "P1S1-R0", "P1S1-R1 ", "F208", "S01-R1", "",
                None, 123):
        with pytest.raises(p.Refusal):
            p.parse_arm(bad)


# -- F2/F3/F5/F7/F8 frozen literals -----------------------------------------------

def test_frozen_literals_seeds_rows_budget_accounting():
    # F3 seeds / stream (FRESH interval — outside every prior family)
    assert p.block_seed(0) == 2026096401
    assert p.block_seed(239) == 2026096401 + 239 == 2026096640
    assert p.stream_seed(2026096401) == common.v10_seed("o1_blk:2026096401")
    assert p.P1_STREAM == "o1_blk:{seed}"
    for bad_idx in (240, -1, None, True):
        with pytest.raises(p.Refusal):
            p.block_seed(bad_idx)
    # F2 rows: m_base=200 + Δm=8 = total 208, HARD cap ≤208
    assert p.P1_M_BASE == 200 and p.P1_DELTA_M == 8
    assert p.P1_M_TOTAL == 208
    assert p.P1_M_BASE + p.P1_DELTA_M == p.P1_M_TOTAL <= 208
    assert p.P1_N_BLOCKS == 240
    assert p.P1_MAX_ITER == 300 and p.P1_STREAK == 3
    assert p.P1_MAX_TRIALS == 20
    # F4 channel literal
    assert p.CHANNEL_NPZ == ("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz")
    assert p.CHANNEL_SOURCE == "2M"
    # §5 budgets
    assert p.P1_WALL_CAP_S == 3600
    assert p.P1_BATCH_CEILING_S == 7200
    assert p.P1_PER_DECODE_CAP_S == 300
    assert p.P1_RSS_CAP_GIB == 2 and p.P1_CPUS == 1
    assert p.BAR12 == 12 == p.fail_bar(240)
    # F7 accounting: frozen-style f_super=(5*208+64)/852.544 worst-case line
    assert p.LEAK_BASE_BITS == 1064 and p.LEAK_FULL_BITS == 1104
    assert p.CONTENT_BITS == 852.544
    assert p.F_SUPER_BASE == 1064 / 852.544
    assert abs(p.F_SUPER_BASE - 1.24803) < 5e-6
    assert p.F_SUPER_FULL == (5 * 208 + 64) / 852.544 == 1104 / 852.544
    assert abs(p.F_SUPER_FULL - 1.294947) < 5e-6
    assert p.f_super_for() == 1104 / 852.544
    assert p.f_super_for(200) == 1064 / 852.544
    assert p.F_EFF_SLOPE == 4.785675 and p.F_SUPER_MAX == 1.3
    assert p.LEAK_CAP_BITS == 1108.31
    # F7 derived rules on this arm's OWN counts
    assert p.expected_leak_for(80) == 1064 + 40.0 * (80 / 240)
    assert p.f_exp_for(80) == p.expected_leak_for(80) / 852.544
    assert p.f_eff_for(80, 80) == p.f_exp_for(80) + 4.785675 * (80 / 240)
    # §3 column contract (X1/S0.1-isomorphic + Stage marker, exact)
    assert p.CSV_COLUMNS == ["block_idx", "seed", "stage", "iters",
                             "wall_s", "decoded", "failed", "undetected",
                             "prior_entropy_bits", "u1_mismatches"]


# -- §10(b) explicit injection: NO default production decode -----------------------

def test_execute_requires_explicit_injection_no_default_decode(tmp_path,
                                                               monkeypatch):
    monkeypatch.chdir(tmp_path)
    construct = _fake_construct()
    base = dict(arm="P1S1-R1",
                root=f"{p.P1_ROOT_PREFIX}P1S1-R1_deadbeef")
    with pytest.raises(p.Refusal):
        p.execute(construct_fn=construct, decode_fn=None,
                  rescue_decode_fn=_fake_rescue(), rank_fn=_rank_ok,
                  **base)
    with pytest.raises(p.Refusal):
        p.execute(construct_fn=construct, decode_fn=_fake_decode(),
                  rescue_decode_fn=None, rank_fn=_rank_ok, **base)
    with pytest.raises(p.Refusal):
        p.execute(construct_fn=None, decode_fn=_fake_decode(),
                  rescue_decode_fn=_fake_rescue(), rank_fn=_rank_ok,
                  **base)
    with pytest.raises(p.Refusal):
        p.execute(construct_fn=construct, decode_fn=_fake_decode(),
                  rescue_decode_fn=_fake_rescue(), rank_fn=None, **base)
    assert not (tmp_path / "workspace").exists()  # no root, no write


def test_root_refusals_zero_construction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fresh = f"{p.P1_ROOT_PREFIX}P1S1-R1_deadbeef"
    bad_roots = ["", "results/P1S1-R1_deadbeef",
                 "comparison_bench/outputs_comparison/P1S1-R1_deadbeef",
                 "workspace/S0_1/P1S1-R1_deadbeef",  # wrong family
                 f"{p.P1_ROOT_PREFIX}P1S1-R2_deadbeef",  # arm mismatch
                 f"{p.P1_ROOT_PREFIX}other_deadbeef"]
    for root in bad_roots:
        with pytest.raises(p.Refusal):
            p.execute(root=root, arm="P1S1-R1",
                      construct_fn=_fake_construct(),
                      decode_fn=_fake_decode(),
                      rescue_decode_fn=_fake_rescue(), rank_fn=_rank_ok)
    busy = tmp_path / fresh
    busy.mkdir(parents=True)  # existing root ⇒ no resume
    with pytest.raises(p.Refusal):
        p.execute(root=fresh, arm="P1S1-R1",
                  construct_fn=_fake_construct(),
                  decode_fn=_fake_decode(),
                  rescue_decode_fn=_fake_rescue(), rank_fn=_rank_ok)
    assert not (tmp_path / "results").exists()


def test_f6_construct_gates_stop_before_any_decode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    decode, rescue = _fake_decode(), _fake_rescue()
    for variant in ("fc", "rank", "twins", "nm"):
        with pytest.raises(p.Refusal):
            p.execute(root=f"{p.P1_ROOT_PREFIX}P1S1-R1_deadbeef",
                      arm="P1S1-R1", construct_fn=_fake_construct(variant),
                      decode_fn=decode, rescue_decode_fn=rescue,
                      rank_fn=_rank_ok)
    with pytest.raises(p.Refusal):
        p.execute(root=f"{p.P1_ROOT_PREFIX}P1S1-R1_deadbeef",
                  arm="P1S1-R1", construct_fn=_fake_construct(),
                  decode_fn=decode, rescue_decode_fn=rescue,
                  rank_fn=_rank_bad)
    assert not (tmp_path / "workspace").exists()  # refused pre-write
    assert decode.seen["n"] == 0 and rescue.seen["n"] == 0  # zero decode


# -- Stage-1 + Stage-2 rescue semantics (fake) ---------------------------------------

def test_mixed_stage1_rescue_subset_math_and_columns(tmp_path, monkeypatch):
    decode, rescue = _fake_decode("mixed"), _fake_rescue("even")
    summary, root = _run(tmp_path, monkeypatch, "P1S1-R1", decode, rescue)
    # mixed i%3 over 240: 80 success / 80 fail / 80 undetected ⇒ k=160
    assert summary["verdict"] == "COMPLETE"
    assert summary["blocks_done"] == 240  # F9: no early stop (k=160>12)
    assert summary["stage1_fails"] == 160
    assert summary["k_over_240"] == "160/240"
    assert summary["attempted"] == 160 == summary["stage1_fails"]
    # rescue set = exactly the 160 non-success; even idx rescued (80)
    assert rescue.seen["n"] == 160
    assert summary["rescued"] == 80
    assert summary["final_fails"] == 80
    assert summary["f_over_240"] == "80/240"
    assert summary["trigger_rate"] == 80 / 240
    assert summary["e_leak"] == 1064 + 40.0 * (80 / 240)
    assert summary["f_exp"] == summary["e_leak"] / 852.544
    assert summary["f_eff"] == summary["f_exp"] + 4.785675 * (80 / 240)
    assert summary["headroom"] == 1108.31 - summary["e_leak"]
    # F10: undetected separate — exactly the 80 Stage-1 i%3==2 blocks
    # (odd-idx rescue failures are conv=False, never undetected)
    assert summary["undetected"] == 80
    # exact rescue-seed identity: non-success seeds only
    expected = {p.P1_BLOCK_BASE + i for i in range(240) if i % 3 != 0}
    assert set(rescue.seen["seeds"]) == expected
    # outputs: per-arm files with stage markers and exact columns
    d = tmp_path / root
    assert (d / "P1S1_RESULT_P1S1-R1.md").exists()
    body = json.loads((d / "rows.json").read_text())
    assert len(body["rows"]) == 240 + 160
    s1 = [r for r in body["rows"] if r["stage"] == "stage1"]
    s2 = [r for r in body["rows"] if r["stage"] == "stage2-rescue"]
    assert len(s1) == 240 and len(s2) == 160
    csv_text = (d / "block_accounting.csv").read_text().splitlines()
    assert csv_text[0] == ",".join(p.CSV_COLUMNS)
    assert len(csv_text) == 1 + 240 + 160


def test_all_success_stage1_no_rescue_calls(tmp_path, monkeypatch):
    decode, rescue = _fake_decode("success"), _fake_rescue("all")
    summary, _ = _run(tmp_path, monkeypatch, "P1S1-R2", decode, rescue)
    assert summary["verdict"] == "COMPLETE"
    assert summary["stage1_fails"] == 0
    assert summary["attempted"] == 0
    assert rescue.seen["n"] == 0  # empty rescue set ⇒ zero rescue decodes
    assert summary["rescued"] == 0 and summary["final_fails"] == 0
    assert summary["trigger_rate"] == 0.0
    assert summary["e_leak"] == 1064.0
    assert summary["undetected"] == 0
    assert summary["n_req"] is not None  # F=0 ⇒ report-only N rule applies


def test_full_rescue_zero_final(tmp_path, monkeypatch):
    decode, rescue = _fake_decode("fail"), _fake_rescue("all")
    summary, _ = _run(tmp_path, monkeypatch, "P1S1-R1", decode, rescue)
    assert summary["verdict"] == "COMPLETE"
    assert summary["blocks_done"] == 240  # all-fail still runs all 240
    assert summary["stage1_fails"] == 240
    assert summary["attempted"] == 240
    assert rescue.seen["n"] == 240
    assert summary["rescued"] == 240 and summary["final_fails"] == 0
    assert summary["trigger_rate"] == 1.0
    assert summary["e_leak"] == 1104.0
    assert summary["f_exp"] == p.F_SUPER_FULL  # worst-case line by identity


def test_no_rescue_conversion_keeps_final_equal_k(tmp_path, monkeypatch):
    decode, rescue = _fake_decode("mixed"), _fake_rescue("none")
    summary, _ = _run(tmp_path, monkeypatch, "P1S1-R1", decode, rescue)
    assert summary["stage1_fails"] == 160
    assert summary["rescued"] == 0
    assert summary["final_fails"] == 160  # cliff unrescued ⇒ FAIL-branch input
    assert summary["trigger_rate"] == 0.0
    assert summary["e_leak"] == 1064.0


def test_missing_report_only_fields_fail_closed(tmp_path, monkeypatch):
    with pytest.raises(p.Refusal):
        _run(tmp_path, monkeypatch, "P1S1-R1", _fake_decode("broken"),
             _fake_rescue("all"))


# -- budgets: terminal, retained, never resumed ---------------------------------------

def test_wall_cap_gives_incomplete_wall_partial_retained(tmp_path,
                                                         monkeypatch):
    clock = _Clock(step=100.0)  # exhausts 3600 s mid-Stage-1
    summary, root = _run(tmp_path, monkeypatch, "P1S1-R1",
                         _fake_decode("success"), _fake_rescue("all"),
                         clock=clock)
    assert summary["verdict"] == "INCOMPLETE-wall"
    assert summary["blocks_done"] < 240
    assert (tmp_path / root / "rows.json").exists()  # partial retained


def test_per_decode_overrun_terminal_block_counts_fail(tmp_path,
                                                       monkeypatch):
    clock = _Clock(step=0.0)
    clock.step = 400.0  # first decode exceeds the 300 s terminal cap
    summary, _ = _run(tmp_path, monkeypatch, "P1S1-R1",
                      _fake_decode("success"), _fake_rescue("all"),
                      clock=clock)
    assert summary["verdict"] == "INCOMPLETE-decode-cap"


def test_decode_error_terminal_no_retry(tmp_path, monkeypatch):
    def _boom(construction, seed):
        raise RuntimeError("fake infra failure")

    summary, _ = _run(tmp_path, monkeypatch, "P1S1-R1", _boom,
                      _fake_rescue("all"))
    assert summary["verdict"] == "INCOMPLETE-error"


# -- --dry: zero decode by construction -------------------------------------------------

def test_dry_pins_literal_gates_and_rank200_placeholder(tmp_path,
                                                        monkeypatch):
    monkeypatch.chdir(tmp_path)
    channel = _write_fake_channel(tmp_path)
    monkeypatch.setattr(p, "CHANNEL_NPZ", str(channel))
    out = p.dry_pins()
    assert out["mode"] == "dry-zero-decode" and out["decode_calls"] == 0
    assert out["seeds"]["first"] == 2026096401
    assert out["seeds"]["last"] == 2026096640
    assert out["seeds"]["stream_first_matches_frozen"] is True
    assert out["budget"]["wall_cap_s_per_arm"] == 3600
    assert out["budget"]["batch_ceiling_s"] == 7200
    assert out["arms"]["m_base"] == 200 and out["arms"]["m_total"] == 208
    assert out["frozen_accounting"]["f_super_full"] == 1104 / 852.544
    assert out["construction_pins"]["status"].startswith("PENDING")
    assert out["construction_pins"]["gates"]["base_rank_required"] == 200
    assert not (tmp_path / "workspace").exists()  # dry writes NOTHING


# -- CLI dual-flag gate: refuse rc=2 BEFORE anything --------------------------------------

def test_cli_refuses_before_anything(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = {"n": 0}

    def _spy(root, arm):
        calls["n"] += 1
        return 0

    monkeypatch.setattr(p, "run_execution", _spy)
    frozen = ["--arm", "P1S1-R1", "--m-base", "200", "--m-total", "208",
              "--instance", "2026092001", "--blocks", "240",
              "--seed-base", "2026096401",
              "--root", f"{p.P1_ROOT_PREFIX}P1S1-R1_deadbeef"]
    with pytest.raises(p.Refusal):  # bare: no flags at all
        p.main([])
    with pytest.raises(p.Refusal):  # only one of the two flags
        p.main(["--execute-real"] + frozen)
    with pytest.raises(p.Refusal):
        p.main(["--execution-authorized"] + frozen)
    with pytest.raises(p.Refusal):  # --dry + execution flag
        p.main(["--dry", "--execute-real"])
    with pytest.raises(p.Refusal):  # wrong m-total (HARD cap probe)
        p.main(["--execute-real", "--execution-authorized"] +
               [a if a != "208" else "209" for a in frozen])
    with pytest.raises(p.Refusal):  # wrong seed-base
        p.main(["--execute-real", "--execution-authorized"] +
               [a if a != "2026096401" else "2026095601" for a in frozen])
    with pytest.raises(p.Refusal):  # arm/instance mismatch
        p.main(["--execute-real", "--execution-authorized"] +
               [a if a != "2026092001" else "2026092011" for a in frozen])
    assert calls["n"] == 0  # production NEVER reached
    assert not (tmp_path / "workspace").exists()


def test_cli_dry_returns_zero_json(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    channel = _write_fake_channel(tmp_path)
    monkeypatch.setattr(p, "CHANNEL_NPZ", str(channel))
    assert p.main(["--dry"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["decode_calls"] == 0
    assert out["verdict"].startswith("DRY-PASS")
    assert not (tmp_path / "workspace").exists()
