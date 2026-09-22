"""Fake-only tests for the S0.1 m=200 thin runner (packet §10(b), G-S01M200).

FAKE-ONLY: every construct / decode / rank / channel here is synthetic and
in-test. No production decoder, DE, or graph-kernel call is made (every
``execute()`` call passes explicit fake ``construct_fn`` / ``decode_fn`` /
``rank_fn``); no real-data path appears; no frozen module is modified
(AGENTS.md §10.1 clause 8); all disk use is pytest ``tmp_path`` (the real
frozen channel is never read here — ``--dry`` is exercised against a tmp
fake channel). Run per-file ONLY:

PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_s01_m200_runner.py -q
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import s01_m200_runner as s
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_common as common,
)


# -- fakes (explicit; never production) ----------------------------------------

def _fake_construct(variant: str = "ok"):
    """Fake A208 constructor: ``(instance, trials) -> code dict``.

    Diagonal triples keep the REAL ``sparse_to_dense`` rank path coherent
    (full rank 208, base rank 200), while fc/rank/twins variants exercise
    each F6 gate.
    """
    calls = {"n": 0}

    def _fn(instance, trials):
        assert instance in (2026092001, 2026092011)
        assert trials == s.S01_MAX_TRIALS
        calls["n"] += 1
        triples = [(r, r, 1) for r in range(s.S01_A208_M)]
        if variant == "twins" and calls["n"] == 2:
            triples = list(triples)[:-1] + [(0, 1, 1)]  # differs ⇒ gate
        code = {"status": "ok", "triples": list(triples),
                "n": s.S01_N, "m": s.S01_A208_M, "four_cycles": 0,
                "min_girth": 8, "rank": s.S01_A208_M,
                "family": "peg-irregular"}
        if variant == "fc":
            code["four_cycles"] = 2
        if variant == "rank":
            code["rank"] = s.S01_A208_M - 1
        if variant == "nm":
            code["n"] = 999
        return code

    _fn.calls = calls
    return _fn


def _rank_ok(dense):
    """Fake rank_fn for the diagonal fakes: asserts the F6 base shape."""
    assert np.asarray(dense).shape == (s.S01_M, s.S01_N)
    return s.S01_M  # 200


def _rank_bad(dense):
    return s.S01_M - 1  # 199 ⇒ STOP-BLOCKED


def _fake_decode(mode: str = "success", clock=None, bump: float = 0.0):
    """Fake decode_fn: success / fail / undetected / mixed (i%3).

    Asserts the F2/F10 contract on EVERY call: base m=200 construction,
    rescue rows never present, strictly sequential frozen seeds.
    """
    seen = {"n": 0}

    def _fn(construction, seed):
        assert construction["m"] == s.S01_M
        assert construction["n"] == s.S01_N
        assert all(int(t[0]) < s.S01_M
                   for t in construction["triples"])  # no rescue rows
        assert seed == s.S01_BLOCK_BASE + seen["n"]
        if clock is not None and bump:
            clock.t += float(bump)
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


class _Clock:
    """Scripted clock: each call returns t then advances by ``step``."""

    def __init__(self, step: float = 1.0):
        self.t = 0.0
        self.step = float(step)

    def __call__(self):
        v = self.t
        self.t += self.step
        return v


def _run(tmp_path, monkeypatch, arm, decode_fn, *, construct_fn=None,
         rank_fn=None, clock=None, rss_fn=None):
    monkeypatch.chdir(tmp_path)  # relative workspace/S0_1 roots stay in tmp
    root = f"{s.S01_ROOT_PREFIX}{arm}_deadbeef"
    summary = s.execute(root=root, arm=arm,
                        construct_fn=(construct_fn if construct_fn is not None
                                      else _fake_construct()),
                        decode_fn=decode_fn,
                        rank_fn=(rank_fn if rank_fn is not None
                                 else _rank_ok),
                        clock=clock,
                        rss_fn=(rss_fn if rss_fn is not None
                                else (lambda: 0)),
                        writer=s.default_writer)
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
    assert s.parse_arm("S01-R1")["instance"] == 2026092001
    assert s.parse_arm("S01-R2")["instance"] == 2026092011
    assert s.ARMS == {"S01-R1": 2026092001, "S01-R2": 2026092011}
    for bad in ("S01-R3", "S01-R0", "S01-R1 ", "F208", "X1-2M-200", "",
                None, 123):
        with pytest.raises(s.Refusal):
            s.parse_arm(bad)


# -- F3/F5/F7/F8 frozen literals ---------------------------------------------------

def test_frozen_literals_seeds_budget_accounting():
    # F3 seeds / stream
    assert s.block_seed(0) == 2026095601
    assert s.block_seed(239) == 2026095601 + 239 == 2026095840
    assert s.stream_seed(2026095601) == common.v10_seed("o1_blk:2026095601")
    assert s.S01_STREAM == "o1_blk:{seed}"
    for bad_idx in (240, -1, None, True):
        with pytest.raises(s.Refusal):
            s.block_seed(bad_idx)
    # F3/F5/F9 widths and caps
    assert s.S01_N_BLOCKS == 240
    assert s.S01_M == 200 and s.S01_A208_M == 208
    assert s.S01_MAX_ITER == 300 and s.S01_STREAK == 3
    assert s.S01_MAX_TRIALS == 20
    # F4 channel literal
    assert s.CHANNEL_NPZ == ("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz")
    assert s.CHANNEL_SOURCE == "2M"
    # §5 budgets
    assert s.S01_WALL_CAP_S == 3600
    assert s.S01_BATCH_CEILING_S == 7200
    assert s.S01_PER_DECODE_CAP_S == 300
    assert s.S01_RSS_CAP_GIB == 2 and s.S01_CPUS == 1
    assert s.BAR12 == 12 == s.fail_bar(240)
    # F7/F8 accounting
    assert s.LEAK_BITS == 1064 and s.CONTENT_BITS == 852.544
    assert s.F_SUPER == 1064 / 852.544
    assert abs(s.F_SUPER - 1.24803) < 5e-6
    assert s.f_super_for() == 1064 / 852.544
    assert s.f_eff_for(6 / 240) == s.F_SUPER + 4.785675 * (6 / 240)
    assert s.F_EFF_SLOPE == 4.785675 and s.F_SUPER_MAX == 1.3
    assert s.N_REQ == 277
    assert s.n_required_frozen() == 277 == math.ceil(
        3 * 4.785675 / (1.3 - 1.24803))
    # §3 column contract (exact)
    assert s.CSV_COLUMNS == ["block_idx", "seed", "iters", "wall_s",
                             "decoded", "failed", "undetected",
                             "prior_entropy_bits", "u1_mismatches"]


# -- §10(b) explicit injection: NO default production decode -----------------------

def test_execute_requires_explicit_injection_no_default_decode(tmp_path,
                                                               monkeypatch):
    monkeypatch.chdir(tmp_path)
    construct = _fake_construct()
    base = dict(arm="S01-R1",
                root=f"{s.S01_ROOT_PREFIX}S01-R1_deadbeef")
    with pytest.raises(s.Refusal):
        s.execute(construct_fn=construct, decode_fn=None, rank_fn=_rank_ok,
                  **base)
    with pytest.raises(s.Refusal):
        s.execute(construct_fn=None, decode_fn=_fake_decode(),
                  rank_fn=_rank_ok, **base)
    with pytest.raises(s.Refusal):
        s.execute(construct_fn=construct, decode_fn=_fake_decode(),
                  rank_fn=None, **base)
    assert construct.calls["n"] == 0  # refused BEFORE any construction
    assert not (tmp_path / "workspace").exists()  # no root, no write


# -- §5 root policy ---------------------------------------------------------------

def test_root_refusals_zero_construction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    construct = _fake_construct()
    decode = _fake_decode()
    fresh = f"{s.S01_ROOT_PREFIX}S01-R1_deadbeef"
    bad_roots = ["", "results/S01-R1_deadbeef",
                 "comparison_bench/outputs_comparison/S01-R1_deadbeef",
                 "workspace/b2f_deadbeef", "workspace/S0_1",
                 f"{s.S01_ROOT_PREFIX}S01-R2_deadbeef",  # arm mismatch
                 "workspace/S0_1/S01-R1"]  # no _<uuid8> prefix part
    for root in bad_roots:
        with pytest.raises(s.Refusal):
            s.execute(root=root, arm="S01-R1", construct_fn=construct,
                      decode_fn=decode, rank_fn=_rank_ok)
    busy = tmp_path / fresh
    busy.mkdir(parents=True)
    with pytest.raises(s.Refusal):  # not fresh ⇒ no resume ever
        s.execute(root=fresh, arm="S01-R1", construct_fn=construct,
                  decode_fn=decode, rank_fn=_rank_ok)
    assert construct.calls["n"] == 0 and decode.seen["n"] == 0
    assert not (tmp_path / "results").exists()


# -- F6 construction pins (zero decode) --------------------------------------------

def test_f6_construct_gates_stop_before_any_decode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for variant in ("fc", "rank", "twins", "nm"):
        decode = _fake_decode()
        with pytest.raises(s.Refusal):
            s.execute(root=f"{s.S01_ROOT_PREFIX}S01-R1_deadbeef",
                      arm="S01-R1", construct_fn=_fake_construct(variant),
                      decode_fn=decode, rank_fn=_rank_ok)
        assert decode.seen["n"] == 0
    decode = _fake_decode()
    with pytest.raises(s.Refusal):  # base rank(rows[0,200)) != 200
        s.execute(root=f"{s.S01_ROOT_PREFIX}S01-R1_deadbeef",
                  arm="S01-R1", construct_fn=_fake_construct(),
                  decode_fn=decode, rank_fn=_rank_bad)
    assert decode.seen["n"] == 0
    assert not (tmp_path / "workspace").exists()  # refused pre-write


def test_f6_base_code_excludes_rescue_rows():
    base = s.construct_and_pin("S01-R2", _fake_construct(), _rank_ok)
    assert base["m"] == 200 and base["n"] == 1024
    assert base["construct_instance"] == 2026092011
    assert base["source_arm"] == "A208"
    assert all(int(t[0]) < 200 for t in base["triples"])  # rows[200,208) out
    assert len(base["triples"]) == 200
    assert base["a208_pins"] == {"four_cycles": 0, "rank": 208,
                                 "girth": 8, "twice_identical": True}
    assert base["base_rank"] == 200 and base["measured_girth"] == 8
    assert "never disclosed" in base["nested_base"]


# -- F9 no early stop: all 240 always ------------------------------------------------

def test_no_early_stop_all_240_even_all_fail(tmp_path, monkeypatch):
    decode = _fake_decode("fail")
    summary, _ = _run(tmp_path, monkeypatch, "S01-R1", decode)
    assert decode.seen["n"] == 240  # bar-12 NEVER stopped anything
    assert summary["blocks_done"] == 240
    assert summary["verdict"] == "COMPLETE"
    assert summary["failures"] == 240 and summary["fer"] == 1.0
    assert summary["undetected"] == 0
    assert "route-ctx FAIL" in summary["route_ctx"]
    assert "report-only" in summary["route_ctx"]
    assert summary["gate_contribution"].startswith("PASS-component")
    assert summary["f_eff"] == s.F_SUPER + s.F_EFF_SLOPE * 1.0


# -- F10 undetected separation + mixed accounting -------------------------------------

def test_undetected_separate_never_merged_no_early_stop(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "S01-R2",
                         _fake_decode("mixed"))
    assert summary["blocks_done"] == 240  # 160 fails > 12, still no stop
    assert summary["verdict"] == "COMPLETE"
    assert summary["failures"] == 160 and summary["undetected"] == 80
    body = json.load(open(f"{root}/rows.json"))
    assert body["summary"]["undetected"] == 80
    und = [r for r in body["rows"] if r["undetected"] == 1]
    assert len(und) == 80
    assert all(r["failed"] == 1 and r["decoded"] == 1 for r in und)
    ok = [r for r in body["rows"] if r["undetected"] == 0
          and r["failed"] == 0]
    assert len(ok) == 80
    md = open(f"{root}/S01_RESULT_S01-R2_m200.md").read()
    assert "NEVER merged" in md and "undetected: 80" in md


# -- outputs: exact §3 contract ----------------------------------------------------------

def test_all_success_outputs_and_markdown_contract(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "S01-R1",
                         _fake_decode("success"))
    assert summary["verdict"] == "COMPLETE"
    assert summary["failures"] == 0 and summary["fer"] == 0.0
    assert summary["undetected"] == 0
    assert summary["f_eff"] == summary["f_super"]  # FER 0, still DISTINCT lines
    assert summary["iters_min"] == summary["iters_max"] == 7
    assert summary["pins"] == {"four_cycles": 0, "rank": 208, "girth": 8,
                               "twice_identical": True}
    assert summary["base_rank"] == 200
    assert summary["n_req_report_only"] == 277
    assert summary["bar12_report_only"] == 12
    csv_text = open(f"{root}/block_accounting.csv").read()
    lines = csv_text.splitlines()
    assert lines[0] == ("block_idx,seed,iters,wall_s,decoded,failed,"
                        "undetected,prior_entropy_bits,u1_mismatches")
    assert len(lines) == 241  # header + 240 rows
    body = json.load(open(f"{root}/rows.json"))
    assert sorted(body.keys()) == ["rows", "summary"]
    assert len(body["rows"]) == 240
    md = open(f"{root}/S01_RESULT_S01-R1_m200.md").read()
    assert "S01_RESULT_S01-R1_m200" not in md  # title names the arm
    f_super_line = next(ln for ln in md.splitlines()
                        if ln.startswith("- f_super (F7)"))
    f_eff_line = next(ln for ln in md.splitlines()
                      if ln.startswith("- f_eff (F7)"))
    assert f_super_line != f_eff_line  # DISTINCT lines, never one number
    assert "1064/852.544" in f_super_line
    assert "4.785675·FER" in f_eff_line
    assert "N_req = 277" in md
    assert "bar-12 context (REPORT-ONLY" in md
    assert "S0.1-gate: PASS-component" in md
    assert "claim ceiling" in md
    assert "pooling incl. 6+4 FORBIDDEN" in md
    assert "2026092001" in md and "girth 8" in md
    assert "rows[0,200)" in md and "never disclosed" in md
    assert "route-ctx PASS" in md and "report-only" in md


# -- budget terminals ---------------------------------------------------------------------

def test_wall_cap_gives_incomplete_wall_partial_retained(tmp_path,
                                                         monkeypatch):
    clock = _Clock(step=50.0)
    decode = _fake_decode("success", clock=clock)
    summary, root = _run(tmp_path, monkeypatch, "S01-R1", decode,
                         clock=clock)
    assert summary["verdict"] == "INCOMPLETE-wall"
    assert 1 <= summary["blocks_done"] < 240
    assert decode.seen["n"] == summary["blocks_done"]  # halted, no overrun
    body = json.load(open(f"{root}/rows.json"))
    assert len(body["rows"]) == summary["blocks_done"]  # retained partial
    assert summary["gate_contribution"].startswith("NOT satisfied")


def test_per_decode_overrun_terminal_block_counts_fail(tmp_path,
                                                       monkeypatch):
    clock = _Clock(step=1.0)
    decode = _fake_decode("success", clock=clock, bump=400.0)
    summary, root = _run(tmp_path, monkeypatch, "S01-R1", decode,
                         clock=clock)
    assert summary["verdict"] == "INCOMPLETE-decode-cap"
    assert summary["blocks_done"] == 1 and decode.seen["n"] == 1  # no continue
    body = json.load(open(f"{root}/rows.json"))
    row = body["rows"][0]
    assert row["status"] == "overrun"
    assert row["decoded"] == 0 and row["failed"] == 1
    assert row["wall_s"] > s.S01_PER_DECODE_CAP_S


def test_decode_error_terminal_no_retry(tmp_path, monkeypatch):
    calls = {"n": 0}

    def _boom(construction, seed):
        calls["n"] += 1
        raise ValueError("boom")

    summary, root = _run(tmp_path, monkeypatch, "S01-R1", _boom)
    assert summary["verdict"] == "INCOMPLETE-error"
    assert calls["n"] == 1  # no retry / no resume
    assert summary["blocks_done"] == 1
    body = json.load(open(f"{root}/rows.json"))
    row = body["rows"][0]
    assert row["status"] == "error" and "boom" in row["error"]
    assert row["decoded"] == 0 and row["failed"] == 1


def test_rss_budget_terminal_before_any_decode(tmp_path, monkeypatch):
    summary, _ = _run(tmp_path, monkeypatch, "S01-R1",
                      _fake_decode("success"),
                      rss_fn=lambda: 3 * 1024 ** 3)
    assert summary["verdict"] == "INCOMPLETE-budget"
    assert summary["blocks_done"] == 0


def test_missing_report_only_fields_fail_closed(tmp_path, monkeypatch):
    with pytest.raises(s.Refusal):
        _run(tmp_path, monkeypatch, "S01-R1", _fake_decode("broken"))


# -- dry pins (zero decode) ---------------------------------------------------------------

def test_dry_pins_literal_gates_and_rank200_placeholder(tmp_path,
                                                        monkeypatch):
    monkeypatch.chdir(tmp_path)
    channel = _write_fake_channel(tmp_path)
    monkeypatch.setattr(s, "CHANNEL_NPZ", str(channel))
    out = s.dry_pins()  # zero decode by construction (no decode_fn exists)
    assert out["mode"] == "dry-zero-decode" and out["decode_calls"] == 0
    assert out["verdict"].startswith("DRY-PASS")
    assert out["channel"]["source"] == "2M"
    assert out["channel"]["g1_shape"] == [32, 1024]
    assert out["channel"]["g2_shape"] == [32, 32, 1024]
    assert out["channel"]["access"].startswith("read-only")
    assert out["seeds"] == {"block_base": 2026095601, "blocks": 240,
                            "first": 2026095601, "last": 2026095840,
                            "stream": "o1_blk:{seed}",
                            "stream_first_matches_frozen": True}
    assert out["budget"] == {"wall_cap_s_per_arm": 3600,
                             "batch_ceiling_s": 7200,
                             "per_decode_cap_s": 300, "rss_cap_gib": 2,
                             "cpus": 1, "bar12_report_only": 12,
                             "n_req_report_only": 277}
    assert out["arms"]["arms"] == s.ARMS and out["arms"]["m"] == 200
    assert out["roots"] == {"family": "workspace/S0_1/",
                            "family_exists": False}
    assert out["frozen_accounting"]["f_super"] == 1064 / 852.544
    pins = out["construction_pins"]
    assert pins["status"].startswith("PENDING")  # rank==200 dry placeholder
    assert "rank==200" in pins["status"]
    assert pins["gates"]["base_rank_required"] == 200
    assert "--dry --construct-pins" in pins["command"]
    assert not (tmp_path / "workspace").exists()  # dry writes NOTHING


def test_dry_pins_refuse_unnormalized_channel(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    channel = _write_fake_channel(tmp_path)
    bad = tmp_path / "bad.npz"
    g1 = np.full((32, 1024), 1.0 / 32.0)
    g2 = np.full((32, 32, 1024), 1.0 / 32.0)  # axis-1 rowsum = 1 ok…
    g2[..., 0] = 0.5  # …corrupt one slice's rowsums ⇒ bind refuses
    np.savez(str(bad), **{"2M_gamma1_L1": g1,
                          "2M_gamma2_L2condU1": g2})
    # s2c.bind refuses with its own SystemExit subclass (distinct class);
    # the contract here is fail-closed rc=2 before any decode/write.
    with pytest.raises(SystemExit):
        s.dry_pins(channel_path=str(bad))


# -- CLI: dual-flag gate, frozen literals, dry path ---------------------------------

def _prod_argv(**over):
    argv = ["--execute-real", "--execution-authorized", "--arm", "S01-R1",
            "--m", "200", "--instance", "2026092001", "--blocks", "240",
            "--seed-base", "2026095601",
            "--root", f"{s.S01_ROOT_PREFIX}S01-R1_deadbeef"]
    for key, val in over.items():
        flag = "--" + key.replace("_", "-")
        i = argv.index(flag)
        argv[i + 1] = str(val)
    return argv


def test_cli_refuses_before_anything(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def _spy(*_a, **_k):
        raise AssertionError("run_execution reached despite refusal")

    monkeypatch.setattr(s, "run_execution", _spy)
    with pytest.raises(s.Refusal):
        s.main([])
    template = ["--arm", "S01-R1", "--m", "200", "--instance",
                "2026092001", "--blocks", "240", "--seed-base",
                "2026095601", "--root",
                f"{s.S01_ROOT_PREFIX}S01-R1_deadbeef"]
    with pytest.raises(s.Refusal):  # bare template = NO default decode
        s.main(template)
    with pytest.raises(s.Refusal):  # one flag only
        s.main(["--execute-real"] + template)
    # NB: the fully-valid dual-flag argv intentionally PASSES the CLI gates
    # (it is the post-grant command); only frozen-literal deviations here.
    for over in ({"m": 201}, {"blocks": 239}, {"seed_base": 1},
                 {"instance": 2026092011}, {"arm": "S01-R3"},
                 {"root": ""}, {"root": "results/x"},
                 {"root": f"{s.S01_ROOT_PREFIX}S01-R2_deadbeef"}):
        with pytest.raises(s.Refusal):
            s.main(_prod_argv(**over))
    with pytest.raises(s.Refusal):  # construct-pins is dry-only
        s.main(_prod_argv() + ["--construct-pins"])
    with pytest.raises(s.Refusal):  # dry never executes
        s.main(["--dry", "--execute-real"])
    with pytest.raises(s.Refusal):
        s.main(["--dry", "--arm", "S01-R1"])
    assert not (tmp_path / "workspace").exists()


def test_cli_dry_returns_zero_json(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    channel = _write_fake_channel(tmp_path)
    monkeypatch.setattr(s, "CHANNEL_NPZ", str(channel))
    rc = s.main(["--dry"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["decode_calls"] == 0
    assert out["verdict"].startswith("DRY-PASS")
    assert out["construction_pins"]["status"].startswith("PENDING")


# -- no real-data / heavy-workflow path in the runner -----------------------------------

def test_source_has_no_realdata_or_heavy_workflow_paths():
    src = Path(s.__file__).read_text(encoding="utf-8")
    assert "Raw Data" not in src
    assert "D:\\" not in src
    assert "experiments/" not in src
    assert "longrun" not in src
    assert "minrerun" not in src
    assert "routeA" not in src
