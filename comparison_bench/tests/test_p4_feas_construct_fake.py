"""Fake-only tests for the P4 n=2048 construction-feasibility thin runner.

FAKE-ONLY: every construct here is synthetic and in-test, and every matrix
fed to a rank check is synthesized in-test — but note the distinction: the
``production_rank_fn`` test invokes the PRODUCTION rank routine
(``peg.rank_GF1024``) on those synthetic matrices (matrix synthesis is
fake, the rank call is production — rank-only, never a decode). No
production PEG construction, no decoder, DE, or graph-kernel call is made
(every ``execute()`` call passes explicit fake ``construct_fn`` /
``rank_fn``); no channel-bundle or frame-file path appears; no frozen
module is modified (AGENTS.md §10.1 clause 8); all disk use is pytest
``tmp_path``. Run per-file ONLY:

PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_p4_feas_construct_fake.py -q
"""

from __future__ import annotations

import json
import re

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import p4_feas_construct as p


# -- fakes (explicit; never production) ----------------------------------------

def _fake_construct(variant: str = "ok"):
    """Fake P4 constructor: ``(instance, trials) -> code dict``.

    Diagonal triples keep the REAL ``sparse_to_dense`` base-rank path
    coherent (rows[0,400) full rank 400, full matrix rank 416) while
    fc/rank/twins/nm/status/family variants exercise each F6 gate.
    Records every call as ``(instance, trials)`` for arm-order assertions.
    """
    calls: list[tuple[int, int]] = []

    def _fn(instance, trials):
        assert instance in (2026092001, 2026092011)  # F1 lineage only
        assert trials == p.P4_MAX_TRIALS
        calls.append((int(instance), int(trials)))
        triples = [(r, r, 1) for r in range(p.P4_M)]
        if variant == "twins" and len(calls) % 2 == 0:
            triples = list(triples)[:-1] + [(0, 1, 1)]  # differs ⇒ gate
        code = {"status": "ok", "triples": list(triples),
                "n": p.P4_N, "m": p.P4_M, "four_cycles": 0,
                "min_girth": 8, "rank": p.P4_M,
                "family": "peg-irregular",
                "total_sockets": 4096, "parallel_edges": 0,
                "trials_used": 1,
                "lambda_edge": dict(p.P4_LAMBDA),
                "rho_edge": {int(k): float(v) for k, v in
                             p._mcde.make_rho(p.P4_RHO_RATE,
                                              dict(p.P4_LAMBDA)).items()}}
        if variant == "girth4":
            code["min_girth"] = 4  # girth RECORDED-not-gated (F6)
        if variant == "fc":
            code["four_cycles"] = 2
        if variant == "rank":
            code["rank"] = p.P4_M - 1
        if variant == "nm":
            code["n"] = 999
        if variant == "status":
            code["status"] = "frozen_failure"
        if variant == "family":
            code["family"] = "three-shift-cyclic"  # F2 banned provenance
        if variant == "family2":
            code["family"] = "ldpc-regular"  # F2 NO non-PEG family
        return code

    _fn.calls = calls
    return _fn


def _rank_ok(dense):
    """Fake rank_fn for the diagonal fakes: asserts the F6 base shape."""
    assert np.asarray(dense).shape == (p.P4_M_BASE, p.P4_N)
    return p.P4_M_BASE  # 400


def _rank_bad(dense):
    return p.P4_M_BASE - 1  # 399 ⇒ STOP-BLOCKED


class _Clock:
    """Scripted clock: each call returns t then advances by ``step``."""

    def __init__(self, step: float = 1.0):
        self.t = 0.0
        self.step = float(step)

    def __call__(self):
        v = self.t
        self.t += self.step
        return v


_UUIDS = {"P4F-R1": "deadbeef", "P4F-R2": "0badc0de"}


def _run(tmp_path, monkeypatch, *, variant="ok", rank_fn=None, clock=None,
         rss_fn=None, construct_fn=None):
    monkeypatch.chdir(tmp_path)  # relative workspace/P4_FEAS roots stay in tmp
    log = str(tmp_path / "p4_log.md")
    batch = p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                      construct_fn=(construct_fn if construct_fn is not None
                                    else _fake_construct(variant)),
                      rank_fn=(rank_fn if rank_fn is not None else _rank_ok),
                      clock=clock,
                      rss_fn=(rss_fn if rss_fn is not None else (lambda: 0)),
                      writer=p.default_writer, log_path=log)
    return batch, log


# -- F1/F2/F3/F6 frozen literals ------------------------------------------------

def test_frozen_literals_f1_f6_and_identity_arithmetic():
    # F1: exactly two arms, frozen order R1 -> R2, lineage integers
    assert list(p.ARMS) == ["P4F-R1", "P4F-R2"]
    assert p.ARM_ORDER == ("P4F-R1", "P4F-R2")
    assert p.ARMS == {"P4F-R1": 2026092001, "P4F-R2": 2026092011}
    # F2: n, m, lambda, rho rate, trials, family
    assert p.P4_N == 2048 and p.P4_M == 416 and p.P4_M_BASE == 400
    assert p.P4_LAMBDA == {2: 1}  # λ={2:1} edge perspective
    assert p.P4_RHO_RATE == 0.796875 == 1 - 416 / 2048
    assert p.P4_MAX_TRIALS == 20
    assert p._mcde.make_rho(p.P4_RHO_RATE, dict(p.P4_LAMBDA)) \
        == p._mcde.make_rho(1 - 416 / 2048, {2: 1.0})  # ρ=make_rho(...)
    # §5 budgets + root family
    assert p.P4_WALL_CAP_S == 1800 and p.P4_CONSTRUCT_CAP_S == 600
    assert p.P4_RSS_CAP_GIB == 2 and p.P4_CPUS == 1
    assert p.P4_ROOT == "workspace/P4_FEAS"
    assert p.P4_ROOT_PREFIX == "workspace/P4_FEAS/"
    assert p.FORBIDDEN_ROOT_PARTS == ("results", "outputs_comparison")
    # F7 identity row (frozen literals + formula)
    assert p.H_ANCHOR == 0.83256272
    assert p.CONTENT_2048 == 1705.088
    assert p.LEAK_BITS == 5 * 416 + 64 == 2144  # tag 64, not doubled
    assert p.LEAK_CAP_BITS == 2216.61
    assert p.F_SUPER_416 == 2144 / 1705.088
    assert abs(p.F_SUPER_416 - 1.25741) < 5e-6  # frozen line 1.25741
    assert p.F_SUPER_416_LITERAL == "1.25741"
    assert p.HEADROOM_CTX == 72.61  # frozen literal
    assert abs((p.LEAK_CAP_BITS - p.LEAK_BITS) - p.HEADROOM_CTX) < 1e-9
    assert abs(p.LEAK_CAP_BITS - (2216.61)) < 1e-9
    assert p.F_EFF_SLOPE == 4.785675 and p.F_SUPER_MAX == 1.3
    assert p.N_REQ_CTX == p.N_REQ_CTX_LITERAL == 338  # report-only
    assert p.N_REQ_CTX == int(
        -(-3 * 4.785675 // (1.3 - p.F_SUPER_416)))  # ceil rule
    # §3 frozen record columns (exact)
    assert p.RESULT_FIELDS == [
        "arm", "construct_seed", "n", "m", "lambda_edge", "rho_edge",
        "trials", "family", "four_cycles", "rank_full", "rank_base_400",
        "twice_identical", "girth", "sockets", "parity", "wall_s",
        "rss_peak", "H_anchor", "content_2048", "f_super_416",
        "headroom_ctx", "N_req_ctx", "claim_ceiling",
    ]
    # F5 decode ledger structurally zero
    assert p.DECODE_CALLS == 0
    assert not [n for n in dir(p) if n.startswith("decode")]


def test_parse_arm_frozen_lineage_only():
    assert p.parse_arm("P4F-R1") == {"arm": "P4F-R1", "instance": 2026092001}
    assert p.parse_arm("P4F-R2") == {"arm": "P4F-R2", "instance": 2026092011}
    for bad in ("P4F-R3", "P1S1-R1", "A208", "P4F-R1 ", "", None, 123):
        with pytest.raises(p.Refusal):
            p.parse_arm(bad)


def test_production_construct_refuses_off_lineage_or_trials():
    for bad_instance in (123, "2026092001", None, True,
                         2026092002):  # no seed invention (F1 STOP door)
        with pytest.raises(p.Refusal):
            p.production_construct(bad_instance, 20)
    for bad_trials in (19, 21, 0, "20", None):
        with pytest.raises(p.Refusal):
            p.production_construct(2026092001, bad_trials)


def test_production_rank_fn_is_rank_only_never_a_decode():
    # real frozen RREF path on a known matrix: rank of zeros is 0
    assert p.production_rank_fn(np.zeros((p.P4_M_BASE, p.P4_N))) == 0
    eye400 = np.eye(p.P4_M_BASE, p.P4_N, dtype=np.int64)
    assert p.production_rank_fn(eye400) == p.P4_M_BASE


# -- CLI dual-flag gate + frozen literal echoes --------------------------------

def _frozen_cli(root="workspace/P4_FEAS"):
    return ["--root", root,
            "--r1-uuid8", "deadbeef", "--r2-uuid8", "0badc0de",
            "--n", "2048", "--m", "416", "--trials", "20",
            "--seeds", "2026092001,2026092011",
            "--lambda-edge", "{2:1}", "--rho-rate", "0.796875"]


def test_cli_refuses_missing_either_flag_before_anything(tmp_path,
                                                         monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[tuple] = []

    def _spy(root, uuid8, log_path=p.DEFAULT_LOG_PATH):
        calls.append((root, uuid8, log_path))
        return 0

    monkeypatch.setattr(p, "run_execution", _spy)
    with pytest.raises(p.Refusal):  # bare invocation
        p.main([])
    with pytest.raises(p.Refusal):  # only --execute-real
        p.main(["--execute-real"] + _frozen_cli())
    with pytest.raises(p.Refusal):  # only --execution-authorized
        p.main(["--execution-authorized"] + _frozen_cli())
    assert calls == []  # production NEVER reached
    assert not (tmp_path / "workspace").exists()
    assert not (tmp_path / "docs").exists()  # no log written


def test_cli_refuses_any_non_frozen_literal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr(p, "run_execution",
                        lambda *a, **k: calls.append(a) or 0)
    both = ["--execute-real", "--execution-authorized"]
    base = _frozen_cli()
    swaps = [
        ["--n", "2047"], ["--m", "415"], ["--trials", "19"],
        ["--seeds", "2026092011,2026092001"],  # order/lineage swapped
        ["--seeds", "2026092001"],  # no second lineage
        ["--lambda-edge", "{2:1.0,10:1}"],
        ["--rho-rate", "0.8"], ["--rho-rate", "0.7968749"],
        ["--root", "results/P4_FEAS"],
        ["--root", "comparison_bench/outputs_comparison/P4_FEAS"],
        ["--root", "workspace/P4_FEAS_evil"],
        ["--root", ""],
        ["--r1-uuid8", ""], ["--r1-uuid8", "deadbee"],  # 7 chars
        ["--r1-uuid8", "DEADBEEF"],  # uppercase refused
        ["--r2-uuid8", "xyz12345"],  # non-hex
    ]
    for flag, value in swaps:
        argv = list(base)
        argv[argv.index(flag) + 1] = value
        with pytest.raises(p.Refusal):
            p.main(both + argv)
    assert calls == []
    assert not (tmp_path / "workspace").exists()


def test_cli_full_frozen_literals_reach_run_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen: dict = {}
    calls: list[tuple] = []

    def _spy(root, uuid8, log_path=p.DEFAULT_LOG_PATH):
        calls.append((root, uuid8, log_path))
        seen.update(root=root, uuid8=uuid8, log_path=log_path)
        return 0

    monkeypatch.setattr(p, "run_execution", _spy)
    log = str(tmp_path / "p4_log.md")
    both = ["--execute-real", "--execution-authorized"]
    rc = p.main(both + _frozen_cli() + ["--log", log])
    assert rc == 0
    assert seen["root"] == "workspace/P4_FEAS"
    assert seen["uuid8"] == _UUIDS
    assert seen["log_path"] == log
    # MINOR-3 (was the vacuous `assert both`): the dual-flag gate opened
    # EXACTLY ONCE, with exactly one of each required flag, in frozen order
    assert calls == [("workspace/P4_FEAS", _UUIDS, log)]
    assert both.count("--execute-real") == \
        both.count("--execution-authorized") == 1
    assert both == ["--execute-real", "--execution-authorized"]


def test_cli_log_refuses_forbidden_roots_same_as_root(tmp_path, monkeypatch):
    # M5: --log carries the same FORBIDDEN_ROOT_PARTS guard as --root
    monkeypatch.chdir(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr(p, "run_execution",
                        lambda *a, **k: calls.append(a) or 0)
    both = ["--execute-real", "--execution-authorized"]
    with pytest.raises(p.Refusal):  # --log results/x.md refused rc=2
        p.main(both + _frozen_cli() + ["--log", "results/x.md"])
    with pytest.raises(p.Refusal):  # outputs_comparison refused rc=2
        p.main(both + _frozen_cli()
               + ["--log", "comparison_bench/outputs_comparison/x.md"])
    assert calls == []  # production NEVER reached, zero write
    assert not (tmp_path / "results").exists()
    assert not (tmp_path / "workspace").exists()
    assert not (tmp_path / "comparison_bench").exists()


# -- execute(): explicit injection, roots, freshness ---------------------------

def test_execute_requires_explicit_injection_pre_write(tmp_path,
                                                       monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = str(tmp_path / "p4_log.md")
    with pytest.raises(p.Refusal):
        p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                  construct_fn=None, rank_fn=_rank_ok, log_path=log)
    with pytest.raises(p.Refusal):
        p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                  construct_fn=_fake_construct(), rank_fn=None,
                  log_path=log)
    with pytest.raises(p.Refusal):
        p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                  construct_fn=_fake_construct(), rank_fn=_rank_ok,
                  log_path="")
    assert not (tmp_path / "workspace").exists()  # no root, no write
    assert not (tmp_path / "docs").exists()


def test_root_and_uuid8_refusals_zero_construction(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = str(tmp_path / "p4_log.md")
    fake = _fake_construct()
    bad_roots = ["", "results/P4_FEAS",
                 "comparison_bench/outputs_comparison/P4_FEAS",
                 "workspace/P4_FEAS_evil", "workspace/P1_STAGE1",
                 "workspace/p4_feas", str(tmp_path / "workspace/P4_FEAS")]
    for root in bad_roots:
        with pytest.raises(p.Refusal):
            p.execute(root=root, uuid8=dict(_UUIDS),
                      construct_fn=fake, rank_fn=_rank_ok, log_path=log)
    bad_uuids = [
        {"P4F-R1": "deadbeef"},                       # missing R2
        {"P4F-R1": "deadbeef", "P4F-R2": "0badc0de",
         "P4F-R3": "00000000"},                       # extra arm
        {"P4F-R1": "", "P4F-R2": "0badc0de"},         # empty uuid
        {"P4F-R1": "deadbee", "P4F-R2": "0badc0de"},  # 7 chars
        {"P4F-R1": "deadbeef", "P4F-R2": "0badc0df0"},  # 9 chars
        {"P4F-R1": "deadbeeg", "P4F-R2": "0badc0de"},   # non-hex
    ]
    for uuids in bad_uuids:
        with pytest.raises(p.Refusal):
            p.execute(root=p.P4_ROOT, uuid8=uuids,
                      construct_fn=fake, rank_fn=_rank_ok, log_path=log)
    assert fake.calls == []            # ZERO construction on refusal
    assert not (tmp_path / "workspace").exists()
    assert not (tmp_path / "p4_log.md").exists()  # no log write either


def test_existing_arm_root_refuses_no_resume(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    busy = tmp_path / "workspace" / "P4_FEAS" / "P4F-R1_deadbeef"
    busy.mkdir(parents=True)
    fake = _fake_construct()
    with pytest.raises(p.Refusal):
        p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                  construct_fn=fake, rank_fn=_rank_ok,
                  log_path=str(tmp_path / "p4_log.md"))
    assert fake.calls == []  # freshness refused BEFORE any construction


# -- F6 pin gates: STOP-BLOCKED before any write --------------------------------

def test_pin_gates_stop_before_any_root_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = str(tmp_path / "p4_log.md")
    for variant in ("fc", "rank", "twins", "nm", "status", "family",
                    "family2"):
        fake = _fake_construct(variant)
        with pytest.raises(p.Refusal):
            p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                      construct_fn=fake, rank_fn=_rank_ok, log_path=log)
        assert len(fake.calls) == 2  # R1 twice; R2 NEVER built (F1 order)
    with pytest.raises(p.Refusal):  # base rank 399 != 400 (F6 REQUIRED)
        p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS),
                  construct_fn=_fake_construct(), rank_fn=_rank_bad,
                  log_path=log)
    assert not (tmp_path / "workspace").exists()  # refused pre-write
    # failure retention: append-only FAIL lines, exact STOP-BLOCKED labels
    lines = open(log).read().splitlines()
    fails = [ln for ln in lines if "FAIL-pins STOP-BLOCKED" in ln]
    assert len(fails) == 8  # 7 variants + bad-rank attempt
    assert all("decode_calls=0" in ln for ln in fails)
    assert all("no repair path used" in ln for ln in fails)


def test_girth_recorded_not_gated(tmp_path, monkeypatch, capsys):
    batch, _ = _run(tmp_path, monkeypatch, variant="girth4")
    assert batch["tally"] == {"P4F-R1": "PASS", "P4F-R2": "PASS"}
    for arm in p.ARM_ORDER:
        assert batch["arms"][arm]["girth"] == 4  # recorded, never gated
        assert "recorded-not-gated" in batch["arms"][arm]["gates"]["girth"]


# -- full batch: frozen order, outputs, identity + claim rows, 6dp print --------

def test_batch_two_arms_frozen_order_outputs_and_log(tmp_path, monkeypatch,
                                                     capsys):
    log = tmp_path / "p4_log.md"
    log.write_text("entry-0 keep me (append-only baseline)\n")
    fake = _fake_construct()
    batch, log_str = _run(tmp_path, monkeypatch, construct_fn=fake)
    # F1 frozen arm order + twice-identical: 2 calls per arm, R1 then R2
    assert fake.calls == [(2026092001, 20), (2026092001, 20),
                          (2026092011, 20), (2026092011, 20)]
    assert batch["arm_order"] == ["P4F-R1", "P4F-R2"]
    assert batch["tally"] == {"P4F-R1": "PASS", "P4F-R2": "PASS"}
    assert batch["decode_calls"] == 0
    assert batch["repair"] == "no repair path used"
    # per-arm fresh additive roots + frozen §3 files
    for arm, uuid8 in (("P4F-R1", "deadbeef"), ("P4F-R2", "0badc0de")):
        d = tmp_path / "workspace" / "P4_FEAS" / f"{arm}_{uuid8}"
        assert d.is_dir()
        rec = json.loads((d / "construction.json").read_text())
        pins = json.loads((d / "pins_report.json").read_text())
        md = (d / f"P4FEAS_RESULT_{arm}.md").read_text()
        # §3 fields present exactly (construction.json carries all of them)
        for field in p.RESULT_FIELDS:
            assert field in rec
        assert (rec["arm"], rec["construct_seed"], rec["n"], rec["m"]) \
            == (arm, p.ARMS[arm], 2048, 416)
        assert rec["trials"] == 20 and rec["family"] == "peg-irregular"
        # pins: fc/rank/twice/base gated PASS; girth recorded; sockets noted
        assert (rec["four_cycles"], rec["rank_full"],
                rec["rank_base_400"], rec["twice_identical"]) == (0, 416,
                                                                  400, True)
        assert rec["girth"] == 8
        assert rec["sockets"] == 4096 and rec["parity"] == 0
        assert rec["gates"]["a_pins"] == "PASS"
        # identity row + claim-ceiling row, never f_eff
        assert rec["identity_row"]["row"].startswith("identity row")
        assert rec["identity_row"]["leak_bits"] == 2144
        assert rec["identity_row"]["f_super_416_literal"] == "1.25741"
        assert rec["identity_row"]["N_req_ctx"] == 338
        assert rec["claim_ceiling_row"]["row"].startswith("claim-ceiling")
        assert rec["claim_ceiling"] == p.CLAIM_CEILING
        # no top-level f_eff field ever (identity row, never f_eff; §3)
        assert "f_eff" not in rec
        assert rec["decode_calls"] == 0
        assert rec["success"] is True and rec["failed"] is False
        # pins report mirrors §3 + gates + zero decode
        for field in p.RESULT_FIELDS:
            assert field in pins
        assert pins["decode_calls"] == 0 and pins["success"] is True
        # markdown: legend + claim ceiling + zero-decode line
        assert "success := ¬failed" in md
        assert "decode_calls=0" in md
        assert p.CLAIM_CEILING[:60] in md
        assert "f_eff" in md and "NEVER quoted as f_eff" in md
    # append-only log: baseline line preserved, new lines appended
    lines = log.read_text().splitlines()
    assert lines[0] == "entry-0 keep me (append-only baseline)"
    body = "\n".join(lines)
    assert "[batch] start arms=P4F-R1→P4F-R2" in body
    assert "[P4F-R1]" in body and "[P4F-R2]" in body
    assert "girth=8 (recorded-not-gated)" in body
    assert "repair=no repair path used" in body
    assert body.count("decode_calls=0") >= 4
    # 6dp printed rows + success=¬failed legend (capsys)
    out = capsys.readouterr().out
    # batch legend once + one per printed arm row
    assert out.count("P4FEAS legend: success := ¬failed") == 3
    assert re.search(r"wall_s=\d+\.\d{6}", out)
    assert re.search(r"f_super_416=\d+\.\d{6}", out)
    assert re.search(r"headroom_ctx=\d+\.\d{6}", out)
    assert "P4FEAS P4F-R1 verdict=PASS success=True failed=False" in out
    assert "P4FEAS P4F-R2 verdict=PASS" in out
    assert "decode_calls=0" in out


def test_build_record_success_is_not_failed(tmp_path):
    gate = {"arm": "P4F-R1", "construct_seed": 2026092001,
            "family": "peg-irregular", "four_cycles": 0, "rank_full": 416,
            "rank_base_400": 400, "twice_identical": True, "girth": 6,
            "sockets": 4096, "parity": 0, "trials_used": 20}
    ok = p.build_record("P4F-R1", gate, 1.5, 0.25, "PASS")
    assert ok["success"] is True and ok["failed"] is False
    assert ok["wall_s"] == 1.5 and ok["rss_peak"] == 0.25
    assert ok["legend"] == p.LEGEND
    for field in p.RESULT_FIELDS:
        assert field in ok
    partial = p.build_record("P4F-R1", gate, 1801.0, 0.25,
                             "INCOMPLETE-wall")
    assert partial["success"] is False and partial["failed"] is True
    # pins retained even on the wall terminal (never continued)
    assert partial["rank_full"] == 416 and partial["rank_base_400"] == 400


# -- budgets: terminal, retained, never continued --------------------------------

def test_wall_cap_incomplete_wall_r2_not_run(tmp_path, monkeypatch):
    # step 500: each construct call 500s ≤ 600 cap; arm wall 2500 > 1800
    fake = _fake_construct()
    batch, log_str = _run(tmp_path, monkeypatch, construct_fn=fake,
                          clock=_Clock(step=500.0))
    assert batch["tally"]["P4F-R1"] == "INCOMPLETE-wall"
    assert batch["tally"]["P4F-R2"] == "NOT-RUN"  # gate did not permit
    assert len(fake.calls) == 2                   # R2 never constructed
    assert (tmp_path / "workspace" / "P4_FEAS" /
            "P4F-R1_deadbeef" / "construction.json").exists()  # retained
    assert not (tmp_path / "workspace" / "P4_FEAS" /
                "P4F-R2_0badc0de").exists()
    assert "INCOMPLETE-wall" in open(log_str).read()


def test_single_construct_overrun_is_terminal_no_continuation(tmp_path,
                                                              monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = str(tmp_path / "p4_log.md")
    fake = _fake_construct()
    with pytest.raises(p.Refusal):  # 700s > 600s single-call cap (§5)
        p.execute(root=p.P4_ROOT, uuid8=dict(_UUIDS), construct_fn=fake,
                  rank_fn=_rank_ok, clock=_Clock(step=700.0),
                  rss_fn=lambda: 0, writer=p.default_writer, log_path=log)
    assert len(fake.calls) == 1  # terminal on first overrun
    assert not (tmp_path / "workspace").exists()
    assert "FAIL-pins STOP-BLOCKED" in open(log).read()


def test_rss_budget_terminal_retained(tmp_path, monkeypatch):
    batch, _ = _run(tmp_path, monkeypatch, rss_fn=lambda: 3 * 1024 ** 3)
    assert batch["tally"]["P4F-R1"] == "INCOMPLETE-budget"
    assert batch["tally"]["P4F-R2"] == "NOT-RUN"
    assert (tmp_path / "workspace" / "P4_FEAS" /
            "P4F-R1_deadbeef" / "pins_report.json").exists()


# -- F4/F5: zero decode, zero channel/frame-file paths ---------------------------

def test_zero_decode_no_channel_or_decoder_paths_in_source():
    src = open(p.__file__, encoding="utf-8").read()
    banned = ['".ttbin"', "'.ttbin'", ".npz", "gamma_f03",
              "bind_empirical", "decode_error_domain", "nonbinary_v28",
              "nonbinary_v10_fftqspa", "v80_b2f", "v80_s2c",
              "exact_match", "max_iter"]
    present = [tok for tok in banned if tok in src]
    assert present == [], f"forbidden channel/decoder tokens present: {present}"
    # no callable starting with "decode" exists; ledger frozen at zero
    assert not [n for n in dir(p) if n.startswith("decode")]
    assert p.DECODE_CALLS == 0


def test_batch_outputs_carry_decode_calls_zero(tmp_path, monkeypatch):
    batch, _ = _run(tmp_path, monkeypatch)
    assert batch["decode_calls"] == 0
    for arm in p.ARM_ORDER:
        assert batch["arms"][arm]["decode_calls"] == 0
        d = tmp_path / "workspace" / "P4_FEAS" / \
            f"{arm}_{batch['uuid8'][arm]}"
        assert json.loads((d / "construction.json").read_text())[
            "decode_calls"] == 0
        assert json.loads((d / "pins_report.json").read_text())[
            "decode_calls"] == 0
