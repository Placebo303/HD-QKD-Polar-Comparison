"""Fake-only tests for the X1 thin arm runner (T-X1S-4 / X1-RUN-3).

FAKE-ONLY: every construct/decode/bundle here is synthetic and in-test.
No production decoder/DE/graph call is made (every ``execute()`` call
passes an explicit fake ``decode_fn`` and, where construction is not
under test, an explicit fake ``construct_fn``); no ``.ttbin`` path
appears; no frozen module is modified (AGENTS.md §10.1 clause 8); all
disk use is in pytest tmp_path. Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import x1_arm_runner as x
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_common as common,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as s2c,
)


# -- fakes (explicit; never production) ---------------------------------------

def _fake_construction(m, fc=0, girth=6, twins=True):
    triples = [(r, c, 1) for r, c in zip(range(m), range(m))]
    code = {"status": "ok", "triples": triples, "n": 1024, "m": m,
            "four_cycles": fc, "min_girth": girth, "rank": m}
    other = dict(code, triples=(list(triples) if twins
                                else list(triples)[:-1] + [(m, m, 1)]))
    calls = {"n": 0}

    def _fn(mm, seed, trials):
        assert mm == m and seed == x.X1_CONSTRUCT_SEED \
            and trials == x.X1_MAX_TRIALS
        calls["n"] += 1
        return code if calls["n"] == 1 else other
    _fn.calls = calls
    return _fn


def _fake_decode(mode="success"):
    """Fake decode_fn: success / fail / undetected / mixed(i%3)."""
    seen = {"n": 0}

    def _fn(construction, seed):
        seen["n"] += 1
        i = seen["n"] - 1
        if mode == "success":
            exact, conv = True, True
        elif mode == "fail":
            exact, conv = False, False
        elif mode == "undetected":
            exact, conv = False, True
        else:  # mixed: success, fail, undetected repeating
            exact, conv = (True, True) if i % 3 == 0 else (
                (False, False) if i % 3 == 1 else (False, True))
        return {"status": "success" if conv else "max_iter_reached",
                "iterations": 7, "reconstruction_ok": conv,
                "exact_match": exact, "seed": seed,
                "prior_entropy_bits": 850.0, "u1_mismatches": 3}
    _fn.seen = seen
    return _fn


def _run(tmp_path, monkeypatch, arm, decode_fn, construct_fn=None, **kw):
    monkeypatch.chdir(tmp_path)  # relative workspace/x1_ roots stay in tmp
    root = f"workspace/x1_{arm.replace('.', 'p').replace('-', '_')}"
    return x.execute(root=root, arm=arm, bundle={"fake": "bound"},
                     construct_fn=(construct_fn if construct_fn is not None
                                   else _fake_construction(x.parse_arm(arm)["m"])),
                     decode_fn=decode_fn, clock=kw.get("clock"),
                     rss_fn=(kw.get("rss_fn") or (lambda: 0)),
                     writer=x.default_writer,
                     max_blocks=kw.get("max_blocks")), root


# -- arm parse / grid gate -----------------------------------------------------

def test_parse_arm_grid_and_labels():
    s = x.parse_arm("X1-1.5M-199")
    assert (s["display"], s["source_key"], s["m"]) == ("1.5M", "1p5M", 199)
    assert s["construct_label"] == "X1-1.5M-S199-standalone"
    assert x.parse_arm("X1-1M-201")["source_key"] == "1M"
    assert x.parse_arm("X1-2M-208")["source_key"] == "2M"


def test_parse_arm_refuses_off_grid_and_bad_form():
    for bad in ("X1-1M-202", "X1-1M-200", "X1-2M-202", "F208",
                "X1-3M-200", "X1-1.5M-208", "", None):
        with pytest.raises(x.Refusal):
            x.parse_arm(bad)


# -- cross-source refusal (source-label mismatch) -------------------------------

def test_execute_refuses_cross_source_key_before_any_decode(tmp_path):
    dec = _fake_decode("success")
    with pytest.raises(x.Refusal):
        x.execute(root=str(tmp_path / "x1_probe"), arm="X1-2M-200",
                  bundle={"fake": "bound"},
                  construct_fn=_fake_construction(200), decode_fn=dec)
    # bind-level: source_key must equal the arm key — drive via helper.
    with pytest.raises(x.Refusal):
        x.bind_source_bundle("workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz",
                             "1M", "X1-2M-200")
    assert dec.seen["n"] == 0  # zero decodes on refusal


def test_frozen_gate_refuses_missing_source_key(tmp_path):
    """Frozen ``bind_empirical_bundle`` refuses a 2M-label bind on a
    1M-only file (the frozen KeyError→refuse path, fake data)."""
    rng = np.random.default_rng(7)
    g1 = rng.random((32, 1024)) + 0.01
    g1 /= g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 /= g2.sum(axis=1, keepdims=True)
    pb = rng.random((1024,)) + 0.01
    pb /= pb.sum()
    bundle = tmp_path / "x1_gamma_f03r1.npz"
    np.savez(str(bundle), **{"1M_gamma1_L1": g1,
                             "1M_gamma2_L2condU1": g2, "1M_p_b": pb})
    np.savez(str(tmp_path / "gamma_f03_pb.npz"), **{"1M_p_b": pb})
    with pytest.raises(s2c.Refusal):
        s2c.bind_empirical_bundle(str(bundle), "2M")
    bound = s2c.bind_empirical_bundle(str(bundle), "1M")
    assert bound["source"] == "1M" and bound["g1"].shape == (32, 1024)


def test_bind_refuses_verify_only_file():
    with pytest.raises(x.Refusal):
        x.bind_source_bundle(
            "workspace/x1_bundles_7c1d4a2b/" + x.X1_VERIFY_FILENAME,
            "2M", "X1-2M-200")


def test_bind_refuses_wrong_file_role_per_source():
    """File-role gate (packet §2.6/F2 + §5 vintage ban): 1M/1.5M arms bind
    ONLY the §2.6-built bundle; 2M arms bind ONLY the frozen file. The
    gate fires BEFORE any file read (hermetic — no bundle I/O here)."""
    with pytest.raises(x.Refusal):
        x.bind_source_bundle("docs/research_cycles/V80-NBLDPC-JAN21/"
                             "gamma_f03.npz", "1M", "X1-1M-185")
    with pytest.raises(x.Refusal):
        x.bind_source_bundle("workspace/x1_bundles_7c1d4a2b/"
                             "x1_gamma_f03r1.npz", "2M", "X1-2M-200")


# -- standalone-construct pins ---------------------------------------------------

def test_pins_pass_and_girth_recorded_not_gated(tmp_path, monkeypatch):
    summary, _ = _run(tmp_path, monkeypatch, "X1-2M-192", _fake_decode("success"),
                      _fake_construction(192, fc=0, girth=4),
                      max_blocks=3)
    assert summary["verdict"] == "PROBE-truncated"
    assert summary["gates"]["a"] == "PASS"


def test_pins_refuse_fc_rank_twins(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # relative workspace/x1_ roots stay in tmp
    base = {"bundle": {"fake": "bound"}, "decode_fn": _fake_decode(),
            "rss_fn": lambda: 0, "writer": x.default_writer}
    with pytest.raises(x.Refusal):  # fc != 0
        x.execute(root="workspace/x1_a", arm="X1-2M-192",
                  construct_fn=_fake_construction(192, fc=2), **base)
    def _badrank(mm, seed, trials):
        c = {"status": "ok", "triples": [(0, 0, 1)], "n": 1024,
             "m": mm, "four_cycles": 0, "min_girth": 6,
             "rank": mm - 1}
        return c
    with pytest.raises(x.Refusal):  # rank != m
        x.execute(root="workspace/x1_c", arm="X1-2M-192",
                  construct_fn=_badrank, **base)
    with pytest.raises(x.Refusal):  # twice-identical violated
        x.execute(root="workspace/x1_d", arm="X1-2M-192",
                  construct_fn=_fake_construction(192, twins=False),
                  **base)


# -- bar / gate arithmetic incl. rule (c) -----------------------------------------

def test_bar12_and_seed_stream_derivation():
    assert x.fail_bar(240) == 12
    assert x.block_seed(0) == 2026095601
    assert x.block_seed(239) == 2026095601 + 239
    assert x.stream_seed(2026095601) == common.v10_seed("o1_blk:2026095601")


def test_f_super_own_basis_and_f_eff():
    for key, h in (("1M", 0.8012690084416184),
                   ("1p5M", 0.8272902027770036),
                   ("2M", 0.8333327179427281)):
        assert x.f_super_for(key, 200) == (5 * 200 + 64) / (1024 * h)
    assert x.f_eff_for(1.2, 0.05) == 1.2 + 4.785675 * 0.05
    # 2M m=200 on own H: f_super ≈ 1.246875...; f_eff at FER 6/240.
    f = x.f_super_for("2M", 200)
    assert abs(f - 1.2468755) < 1e-5
    assert abs(x.f_eff_for(f, 6 / 240) - (f + 4.785675 * 0.025)) < 1e-12


def test_rule_c_and_inf_case():
    assert x.n_required(1.2) == math.ceil(3 * 4.785675 / (1.3 - 1.2))
    assert x.n_required(1.3) == math.inf
    assert x.n_required(1.4) == math.inf
    # 1M m=201 (retained-frozen grid top): f_super > 1.3 ⇒ EXPECTED-OUT,
    # rule (c) unsatisfiable ⇒ inf.
    f201 = x.f_super_for("1M", 201)
    assert f201 > 1.3
    assert x.n_required(f201) == math.inf


# -- root refusal ------------------------------------------------------------------

def test_root_refusal(tmp_path):
    busy = tmp_path / "x1_busy"
    busy.mkdir()
    with pytest.raises(x.Refusal):
        x.execute(root=str(busy), arm="X1-2M-192",
                  bundle={"fake": "bound"},
                  construct_fn=_fake_construction(192),
                  decode_fn=_fake_decode())
    for bad_root in ("results/x1_deadbeef",
                     "comparison_bench/outputs_comparison/x1_deadbeef",
                     "workspace/b2f_deadbeef", ""):
        with pytest.raises(x.Refusal):
            x.execute(root=bad_root, arm="X1-2M-192",
                      bundle={"fake": "bound"},
                      construct_fn=_fake_construction(192),
                      decode_fn=_fake_decode())


# -- bar-12 CENSORED + undetected separation + outputs ------------------------------

def test_bar12_early_stop_censored_never_extrapolated(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "X1-2M-192", _fake_decode("fail"),
                         _fake_construction(192))
    assert summary["verdict"] == "FAIL-early-stop"
    assert summary["censored"] is True
    assert "CENSORED" in summary["curve_label"]
    assert summary["failures"] == 13 and summary["blocks_done"] == 13
    assert "projected NEVER" in summary["curve_label"]
    body = json.load(open(f"{root}/rows.json"))
    assert len(body["rows"]) == 13  # retained partials only; no 240-fill


def test_undetected_logged_separately_never_success(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "X1-1M-185",
                         _fake_decode("undetected"),
                         _fake_construction(185), max_blocks=5)
    assert summary["undetected"] == 5 and summary["failures"] == 5
    assert summary["fer"] == 1.0
    body = json.load(open(f"{root}/rows.json"))
    assert all(r["undetected"] is True and r["exact_match"] is False
               for r in body["rows"])
    assert body["summary"]["undetected"] == 5


def test_all_success_pass_and_outputs(tmp_path, monkeypatch):
    summary, root = _run(tmp_path, monkeypatch, "X1-2M-192", _fake_decode("success"),
                         _fake_construction(192))
    assert summary["verdict"] == "PASS"
    assert summary["gates"] == {"a": "PASS", "b": "PASS",
                                "c": summary["gates"]["c"]}
    assert summary["undetected"] == 0 and summary["fer"] == 0.0
    assert summary["f_eff"] == summary["f_super"]  # FER 0 ⇒ equal, stated
    md = open(f"{root}/X1_RESULT_2M_192.md").read()
    assert "X1-2M-192" in md and "f_eff" in md and "f_super" in md
    assert "undetected 0" in md
    csv_text = open(f"{root}/block_accounting.csv").read()
    assert csv_text.splitlines()[0].startswith("block,seed,exact_match,")
    assert len(csv_text.splitlines()) == 241  # header + 240 rows


def test_gate_b_fail_on_expected_out_arm(tmp_path, monkeypatch):
    summary, _ = _run(tmp_path, monkeypatch, "X1-1M-201", _fake_decode("success"),
                      _fake_construction(201))
    assert summary["gates"]["b"] == "FAIL"  # f_super > 1.3 EXPECTED-OUT
    assert summary["verdict"] == "FAIL"


# -- CLI dual-flag gate (no silent production path) ----------------------------------

def test_main_refuses_without_flags_and_bad_literals():
    with pytest.raises(x.Refusal):
        x.main([])
    with pytest.raises(x.Refusal):
        x.main(["--execute-real", "--arm", "X1-2M-192"])
    full = ["--execute-real", "--execution-authorized",
            "--arm", "X1-2M-192", "--bundle", "b", "--pb-sidecar", "p",
            "--source-key", "2M", "--construct-instance", "2026092001",
            "--standalone", "--seeds", "2026095601+idx",
            "--stream", "o1_blk:{seed}", "--blocks", "240",
            "--root", "workspace/x1_probe", "--per-decode-timeout-s", "300",
            "--budget-s", "1800"]
    with pytest.raises(x.Refusal):  # wrong budget literal
        x.main(full[:-1] + ["1799"])
