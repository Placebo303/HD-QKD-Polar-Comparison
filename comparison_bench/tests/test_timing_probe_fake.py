"""Fake-only tests for the TIMING two-arm probe runner (zero decode).

FAKE-ONLY: every timed call here is an injected in-test fake — no real PEG
construction, no real dense-RREF production run, no production timing batch,
no decoder, DE, channel or graph kernel is ever invoked (every ``execute()``
passes explicit fake ``t1_fn`` / ``t2_fn``; the production-constructor test
replaces ``peg_construct`` / ``rank_GF1024`` / ``sparse_to_dense`` /
``make_rho`` with bombs and only feeds off-plan arguments, proving refusal
happens BEFORE any production call; the A4 test only INSPECTS production
source text, never calls it). No real-data path (``.ttbin`` / ``gamma``)
appears as an input; no frozen module is modified (AGENTS.md §10.1
clause 8); all disk use is pytest ``tmp_path`` (zero repo writes).
Run per-file ONLY:

PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_timing_probe_fake.py -q
"""

from __future__ import annotations

import inspect
import json
import time

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import timing_probe_runner as t


# -- fakes (explicit; never production) ----------------------------------------

def _fake_t1():
    """Fake T1 timed call: ``(m, n, seed, repeat) -> segments/info dict``."""

    calls: list[tuple] = []

    def _fn(m, n, seed, repeat):
        calls.append((int(m), int(n), int(seed), int(repeat)))
        return {"segments": {"rref_s": 0.02},   # A4: single timed segment
                "info": {"m": int(m), "n": int(n), "seed": int(seed),
                         "rank_recorded_not_gated": int(m),
                         "rank_eq_m": True}}    # rank==m flag passes through

    _fn.calls = calls
    return _fn


def _fake_t2():
    """Fake T2 timed call: ``(n, m, seed) -> segments/info dict``."""

    calls: list[tuple] = []

    def _fn(n, m, seed):
        calls.append((int(n), int(m), int(seed)))
        return {"segments": {"peg_main_s": 0.04, "bfs_girth_s": 0.01},
                "info": {"n": int(n), "m": int(m), "seed": int(seed),
                         "edges": 2 * int(n),   # λ={2:1} ⇒ len(triples)=2n
                         "status": "ok", "min_girth_constructor": 6,
                         "min_girth_standalone": 6, "girth_agrees": True}}

    _fn.calls = calls
    return _fn


class _Clock:
    """Scripted timer: each call returns t then advances by ``step``."""

    def __init__(self, step: float = 1.0):
        self.t = 0.0
        self.step = float(step)

    def __call__(self):
        v = self.t
        self.t += self.step
        return v


_UUID8 = "deadbeef"
_CAP = 1e6  # generous batch wall ceiling unless a test targets the cap


def _run(tmp_path, monkeypatch, *, t1=None, t2=None, timer=None, rss_fn=None,
         batch_cap_s=_CAP, rss_gib=2.0):
    monkeypatch.chdir(tmp_path)  # relative workspace/TIMING root stays in tmp
    t1 = t1 if t1 is not None else _fake_t1()
    t2 = t2 if t2 is not None else _fake_t2()
    batch = t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=t1, t2_fn=t2,
                      batch_cap_s=batch_cap_s, timer=timer,
                      rss_fn=(rss_fn or (lambda: 0)), rss_gib=rss_gib)
    return batch, t1, t2


def _files_under(tmp_path):
    base = tmp_path / "workspace"
    if not base.exists():
        return []
    return sorted(str(p.relative_to(tmp_path))
                  for p in base.rglob("*") if p.is_file())


def _read(tmp_path, name):
    return (tmp_path / "workspace" / "TIMING" / _UUID8 / name).read_text()


def _records(tmp_path):
    return [json.loads(line)
            for line in _read(tmp_path, t.RECORDS_NAME).splitlines()]


# -- F1/F2/F3/F6/F7 frozen literals ---------------------------------------------

def test_frozen_literals_plan_and_budgets():
    # F1 two arms, frozen order
    assert t.ARM_ORDER == ("T1-DENSE-RREF", "T2-SPARSE-PEG")
    # F2 dense-RREF grid + exclusive seeds + forbidden lineage seeds
    assert t.T1_SHAPES == ((400, 1024), (400, 2048), (416, 1024),
                           (416, 2048))
    assert t.T1_REPEATS == 3
    assert t.T1_SEEDS == tuple(range(2026092401, 2026092413))
    assert len(t.T1_SEEDS) == 12 == len(set(t.T1_SEEDS))
    assert t.FORBIDDEN_SEEDS == (2026092001, 2026092011)
    assert not (set(t.T1_SEEDS) | set(t.T2_SEEDS)) & set(t.FORBIDDEN_SEEDS)
    # F3 sparse-PEG cells + seeds + frozen λ/ρ/trials/GF32
    assert t.T2_SHAPES == ((512, 104), (1024, 208))
    assert t.T2_SEEDS == (2026092421, 2026092422)
    assert t.T2_LAMBDA == {2: 1}
    assert t.T2_MAX_TRIALS == 20
    assert t.FIELD_Q == 32 == t.s2.Q
    assert t._mcde.make_rho(1 - 104 / 512, dict(t.T2_LAMBDA)) \
        == t._mcde.make_rho(0.796875, {2: 1.0})  # ρ=make_rho(1−m/n)
    assert 1 - 104 / 512 == 1 - 208 / 1024 == 0.796875
    # F4 timer is literally time.perf_counter; segment key contract — T1 has
    # exactly ONE timed segment (A4: dense construction is untimed)
    assert t.TIMER_DEFAULT is time.perf_counter
    assert t.SEGMENT_KEYS == {
        "T1-DENSE-RREF": ("rref_s",),
        "T2-SPARSE-PEG": ("peg_main_s", "bfs_girth_s"),
    }
    # F6 budgets: single-call deadline enforced; batch ceiling has NO frozen
    # default and is enforced per run via the required --batch-cap-s flag
    assert t.SINGLE_CALL_DEADLINE_S == 600
    assert t.BATCH_CEILING_S is None
    assert "--batch-cap-s" in t.BATCH_CEILING_STATUS
    assert "enforced" in t.BATCH_CEILING_STATUS
    assert "not enforced" not in t.BATCH_CEILING_STATUS
    # A3: exactly three terminal states
    assert t.TERMINALS == ("ok", "INCOMPLETE-call", "error")
    # F7: k=4 whole-100-s report-only proposals + edge-linear endpoints
    assert t.F7_K == 4
    assert (t.F7_EDGE_FROM, t.F7_EDGE_TO) == (2048, 4096)
    # F7 output family + append-only file names + forbidden guard tables
    assert t.ROOT == "workspace/TIMING"
    assert t.ROOT_PREFIX == "workspace/TIMING/"
    assert t.RECORDS_NAME == "timing_records.jsonl"
    assert t.SUMMARY_NAME == "timing_summary.md"
    assert t.FORBIDDEN_ROOT_PARTS == ("results", "outputs_comparison")
    assert t.FORBIDDEN_PATH_TOKENS == (".ttbin", "gamma")
    assert t.UUID8_RE.match("deadbeef") and not t.UUID8_RE.match("DEADBEEF")
    # frozen record field contract (A2: case_id / wall_s_total / terminal / edges)
    assert t.RECORD_FIELDS == [
        "arm", "case_id", "m", "n", "seed", "repeat", "lambda_edge",
        "rho_rate", "trials", "field_q", "segments", "edges", "wall_s_total",
        "deadline_s", "batch_ceiling_s", "batch_ceiling_status", "rss_peak",
        "terminal", "decode_calls", "info", "claim_ceiling",
    ]
    assert "call_index" not in t.RECORD_FIELDS
    assert "total_s" not in t.RECORD_FIELDS
    assert "verdict" not in t.RECORD_FIELDS
    # F5 decode ledger structurally zero
    assert t.DECODE_CALLS == 0
    assert not [n for n in dir(t) if n.startswith("decode")]


def test_plan_shape_order_and_seed_exclusivity():
    plan = t.validate_plan()
    assert len(plan) == 16
    t1 = [c for c in plan if c["arm"] == "T1-DENSE-RREF"]
    t2 = [c for c in plan if c["arm"] == "T2-SPARSE-PEG"]
    # F2: 12 calls, shape-major × 3 repeats, one exclusive seed per call
    assert len(t1) == 12
    assert [(c["m"], c["n"]) for c in t1] == [
        shape for shape in t.T1_SHAPES for _ in range(t.T1_REPEATS)]
    assert [c["repeat"] for c in t1] == [0, 1, 2] * 4
    assert [c["seed"] for c in t1] == list(range(2026092401, 2026092413))
    assert len({c["seed"] for c in t1}) == 12  # exclusive, never reused
    assert [c["case_id"] for c in t1] == list(range(12))
    # F3: 4 calls = 2 shapes × 2 seeds, distinct cells
    assert len(t2) == 4
    assert [(c["n"], c["m"]) for c in t2] == [(512, 104), (512, 104),
                                              (1024, 208), (1024, 208)]
    assert [c["seed"] for c in t2] == [2026092421, 2026092422,
                                       2026092421, 2026092422]
    assert len({(c["n"], c["m"], c["seed"]) for c in t2}) == 4
    assert [c["case_id"] for c in t2] == list(range(4))
    # frozen order: all 12 T1 calls first, then the 4 T2 calls
    assert [c["arm"] for c in plan] == ["T1-DENSE-RREF"] * 12 + \
        ["T2-SPARSE-PEG"] * 4
    # cross-arm seed disjointness + no forbidden lineage seed anywhere
    assert not ({c["seed"] for c in t1} & {c["seed"] for c in t2})
    assert not ({c["seed"] for c in plan} & set(t.FORBIDDEN_SEEDS))


def test_plan_validation_refuses_mutations():
    base = lambda: t.t1_plan() + t.t2_plan()  # noqa: E731

    reused = base()
    reused[1]["seed"] = reused[0]["seed"]  # T1 seed reuse
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(reused)

    forbidden = base()
    forbidden[0]["seed"] = 2026092001  # F2 forbidden lineage seed
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(forbidden)
    forbidden2 = base()
    forbidden2[13]["seed"] = 2026092011  # F3 side forbidden seed
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(forbidden2)

    invented = base()
    invented[5]["seed"] = 2026092413  # no seed invention (off-plan)
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(invented)

    short = base()[:15]  # count gate
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(short)

    stranger = base()
    stranger[3]["arm"] = "T3-WHATEVER"  # unknown arm
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(stranger)

    dup_cell = base()
    dup_cell[14]["n"], dup_cell[14]["m"] = 512, 104  # duplicate T2 cell
    with pytest.raises(t.Refusal):
        t._validate_plan_calls(dup_cell)


# -- F2 seed-exclusive RNG ------------------------------------------------------

def test_seeded_rng_is_exclusive_and_off_plan_refused():
    a = t.seeded_rng(2026092401)
    b = t.seeded_rng(2026092401)  # same seed ⇒ identical fresh stream
    assert np.array_equal(a.integers(0, 32, size=8),
                          b.integers(0, 32, size=8))
    c = t.seeded_rng(2026092402)  # different seed ⇒ different stream
    assert not np.array_equal(a.integers(0, 32, size=8),
                              c.integers(0, 32, size=8))
    # global numpy.random stream is never touched (no cross-call leakage)
    np.random.seed(12345)
    before = np.random.get_state()
    t.seeded_rng(2026092403).integers(0, 32, size=16)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1])
    # forbidden / off-plan seeds refused before any RNG exists
    for bad in (2026092001, 2026092011, 2026092413, 1, "2026092401", None):
        with pytest.raises(t.Refusal):
            t.seeded_rng(bad)


# -- F8 dual-flag gate ----------------------------------------------------------

def _both_flags():
    return ["--execute-real", "--execution-authorized"]


def _frozen_cli(root=t.ROOT, uuid8=_UUID8):
    # A5: --batch-cap-s is REQUIRED on every production CLI invocation
    return _both_flags() + ["--root", root, "--uuid8", uuid8,
                            "--batch-cap-s", "1000"]


def test_dual_flag_gate_refuses_either_missing_before_anything(tmp_path,
                                                               monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr(t, "run_execution",
                        lambda *a, **k: calls.append(a) or 0)
    with pytest.raises(t.Refusal):  # bare invocation
        t.main([])
    with pytest.raises(t.Refusal):  # only --execute-real
        t.main(["--execute-real", "--root", t.ROOT, "--uuid8", _UUID8])
    with pytest.raises(t.Refusal):  # only --execution-authorized
        t.main(["--execution-authorized", "--root", t.ROOT,
                "--uuid8", _UUID8])
    assert calls == []  # production NEVER reached
    assert not (tmp_path / "workspace").exists()
    assert not (tmp_path / "results").exists()


def test_cli_frozen_args_reach_run_execution_bad_args_refused(tmp_path,
                                                              monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr(t, "run_execution",
                        lambda *a, **k: calls.append(a) or 0)
    rc = t.main(_frozen_cli())
    assert rc == 0
    assert calls == [(t.ROOT, _UUID8, 1000.0, 2.0)]  # one gated entry, A5 args
    # A5: --batch-cap-s missing (everything else valid) ⇒ rc=2 pre-anything
    with pytest.raises(t.Refusal):
        t.main(_both_flags() + ["--root", t.ROOT, "--uuid8", _UUID8])
    bad = [
        ["--root", "results/TIMING"],                    # forbidden tree
        ["--root", "comparison_bench/outputs_comparison/T"],
        ["--root", "workspace/TIMING_frame.ttbin"],       # real .ttbin token
        ["--root", "workspace/TIMING/gamma_run"],         # real gamma token
        ["--root", "workspace/TIMING_evil"],
        ["--root", ""],
        ["--uuid8", ""], ["--uuid8", "deadbee"],          # 7 chars
        ["--uuid8", "DEADBEEF"],                          # uppercase refused
        ["--uuid8", "xyz12345"],                          # non-hex
        ["--batch-cap-s", ""],                            # required, empty
        ["--batch-cap-s", "0"],                           # not > 0
        ["--batch-cap-s", "-1"],                          # negative
        ["--batch-cap-s", "abc"],                         # not a number
        ["--batch-cap-s", "nan"],                         # not finite
    ]
    for swap in bad:
        argv = _frozen_cli()
        argv[argv.index(swap[0]) + 1] = swap[1]
        with pytest.raises(t.Refusal):
            t.main(argv)
    # --rss-gib invalid values (flag absent from _frozen_cli ⇒ default path
    # above already proved the 2.0 default reaches run_execution)
    for bad_rss in ("0", "-2", "nan", "fast"):
        with pytest.raises(t.Refusal):
            t.main(_frozen_cli() + ["--rss-gib", bad_rss])
    assert calls == [(t.ROOT, _UUID8, 1000.0, 2.0)]  # refusals never re-enter
    assert not (tmp_path / "workspace").exists()
    assert not (tmp_path / "results").exists()
    assert not (tmp_path / "comparison_bench").exists()


# -- F8 forbidden path guard ----------------------------------------------------

def test_forbidden_path_guard_results_outputs_ttbin_gamma():
    for bad in ("results", "results/TIMING", "workspace/results/x",
                "comparison_bench/outputs_comparison",
                "workspace/TIMING/records.ttbin", "data/frame.TTBIN",
                "workspace/TIMING/gamma_f03.csv", "data/Gamma_run",
                "", None, 7):
        with pytest.raises(t.Refusal):
            t._check_path(bad, "path")
    # allowed destinations still pass
    assert t._check_path("workspace/TIMING") == "workspace/TIMING"
    assert t._check_path("workspace/TIMING/deadbeef/timing_records.jsonl")


def test_execute_forbidden_root_refused_with_zero_calls(tmp_path,
                                                        monkeypatch):
    monkeypatch.chdir(tmp_path)
    t1, t2 = _fake_t1(), _fake_t2()
    for bad_root in ("results/TIMING",
                     "comparison_bench/outputs_comparison/TIMING",
                     "workspace/TIMING.ttbin"):
        with pytest.raises(t.Refusal):
            t.execute(root=bad_root, uuid8=_UUID8, t1_fn=t1, t2_fn=t2,
                      batch_cap_s=_CAP, rss_fn=lambda: 0)
    assert t1.calls == [] and t2.calls == []  # no timed call ever started
    assert _files_under(tmp_path) == []


def test_append_writers_guard_and_are_append_only(tmp_path):
    d = tmp_path / "appendx"
    d.mkdir()
    t.append_record(str(d), {"a": 1})
    t.append_record(str(d), {"b": 2})  # append mode, never truncates
    assert [json.loads(line)
            for line in (d / t.RECORDS_NAME).read_text().splitlines()] == \
        [{"a": 1}, {"b": 2}]
    t.append_summary(str(d), "# first\n")
    t.append_summary(str(d), "# second\n")
    text = (d / t.SUMMARY_NAME).read_text()
    assert text.startswith("# first\n") and "# second\n" in text
    # write-boundary guard: forbidden destinations are refused pre-open
    with pytest.raises(t.Refusal):
        t.append_record(str(tmp_path / "results"), {"c": 3})
    with pytest.raises(t.Refusal):
        t.append_summary(str(tmp_path / "gamma_dir"), "nope")
    assert not (tmp_path / "results").exists()
    assert not (tmp_path / "gamma_dir").exists()


# -- execute(): injection, freshness, full fake batch ----------------------------

def test_execute_requires_injection_and_cap_pre_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for t1_fn, t2_fn in ((None, _fake_t2()), (_fake_t1(), None),
                         (None, None)):
        with pytest.raises(t.Refusal):
            t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=t1_fn, t2_fn=t2_fn,
                      batch_cap_s=_CAP, rss_fn=lambda: 0)
    # A5: batch_cap_s required (no default) + rss budget sanity, pre-write
    for bad_cap in (None, 0, -1, float("nan"), "abc"):
        with pytest.raises(t.Refusal):
            t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=_fake_t1(),
                      t2_fn=_fake_t2(), batch_cap_s=bad_cap,
                      rss_fn=lambda: 0)
    for bad_rss in (0, -1, float("nan")):
        with pytest.raises(t.Refusal):
            t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=_fake_t1(),
                      t2_fn=_fake_t2(), batch_cap_s=_CAP, rss_gib=bad_rss,
                      rss_fn=lambda: 0)
    assert _files_under(tmp_path) == []  # no root, no write, no call


def test_execute_refuses_bad_uuid_or_stale_root_pre_write(tmp_path,
                                                          monkeypatch):
    monkeypatch.chdir(tmp_path)
    t1, t2 = _fake_t1(), _fake_t2()
    for bad_uuid in ("DEADBEEF", "deadbee", "", None, 0):
        with pytest.raises(t.Refusal):
            t.execute(root=t.ROOT, uuid8=bad_uuid, t1_fn=t1, t2_fn=t2,
                      batch_cap_s=_CAP, rss_fn=lambda: 0)
    assert t1.calls == [] and _files_under(tmp_path) == []
    # fresh root then stale root: second run refused, records untouched
    t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=_fake_t1(), t2_fn=_fake_t2(),
              batch_cap_s=_CAP, rss_fn=lambda: 0)
    before = _read(tmp_path, t.RECORDS_NAME)
    with pytest.raises(t.Refusal):
        t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=_fake_t1(),
                  t2_fn=_fake_t2(), batch_cap_s=_CAP, rss_fn=lambda: 0)
    after = _read(tmp_path, t.RECORDS_NAME)
    assert after == before  # no resume/continue, no append on refusal
    assert len(after.splitlines()) == 16


def test_batch_fake_pass_records_order_outputs_and_zero_decode(tmp_path,
                                                               monkeypatch,
                                                               capsys):
    batch, t1, t2 = _run(tmp_path, monkeypatch, timer=_Clock(step=0.5))
    plan = t.validate_plan()
    # frozen call order + one fake invocation per plan cell
    assert t1.calls == [(c["m"], c["n"], c["seed"], c["repeat"])
                        for c in plan if c["arm"] == "T1-DENSE-RREF"]
    assert t2.calls == [(c["n"], c["m"], c["seed"])
                        for c in plan if c["arm"] == "T2-SPARSE-PEG"]
    assert batch["tally"] == {"T1-DENSE-RREF": "ok",
                              "T2-SPARSE-PEG": "ok",
                              "batch": "ok"}
    assert batch["batch_state"] == "ok"
    assert batch["stop_reason"] == "complete"
    assert batch["decode_calls"] == 0
    assert batch["record_count"] == 16 == batch["planned_count"]
    assert batch["root"] == f"workspace/TIMING/{_UUID8}"
    assert batch["deadline_s"] == 600
    assert batch["batch_ceiling_s"] == _CAP  # per-run --batch-cap-s value
    assert batch["rss_gib"] == 2.0           # --rss-gib default
    assert batch["records_name"] == "timing_records.jsonl"
    assert batch["summary_name"] == "timing_summary.md"
    # A1/F7: exactly the two renamed append-only files under the run root
    assert _files_under(tmp_path) == [
        f"workspace/TIMING/{_UUID8}/timing_records.jsonl",
        f"workspace/TIMING/{_UUID8}/timing_summary.md",
    ]
    records = _records(tmp_path)
    assert len(records) == 16
    assert [r["case_id"] for r in records] == [c["case_id"] for c in plan]
    assert [r["seed"] for r in records] == [c["seed"] for c in plan]
    assert [(r["m"], r["n"]) for r in records] == \
        [(c["m"], c["n"]) for c in plan]
    for rec in records:
        for field in t.RECORD_FIELDS:
            assert field in rec
        # A2: legacy field names are gone entirely
        assert not ({"call_index", "total_s", "verdict"} & set(rec))
        assert rec["decode_calls"] == 0
        assert rec["terminal"] == "ok"
        assert rec["terminal"] in t.TERMINALS
        assert rec["deadline_s"] == 600
        assert rec["wall_s_total"] == pytest.approx(0.5)  # scripted timer
        assert rec["rss_peak"] == 0.0
        assert rec["batch_ceiling_s"] == _CAP
        assert rec["claim_ceiling"] == t.CLAIM_CEILING
        if rec["arm"] == "T1-DENSE-RREF":
            assert set(rec["segments"]) == {"rref_s"}   # A4 single segment
            assert rec["edges"] == rec["m"] * rec["n"]  # A2 T1 edges = m*n
            assert rec["info"]["rank_eq_m"] is True     # A4 rank==m in info
            assert rec["lambda_edge"] is None and rec["trials"] is None
        else:
            assert set(rec["segments"]) == {"peg_main_s", "bfs_girth_s"}
            assert rec["edges"] == 2 * rec["n"]         # A2 len(triples)
            assert rec["lambda_edge"] == {"2": 1.0}     # JSON key stringified
            assert rec["rho_rate"] == pytest.approx(0.796875)
            assert rec["trials"] == 20
    # A3: NOT-RUN / INCOMPLETE-batch never appear as record rows
    assert "NOT-RUN" not in _read(tmp_path, t.RECORDS_NAME)
    assert "INCOMPLETE-batch" not in _read(tmp_path, t.RECORDS_NAME)
    # summary.md content: tally, zero decode, claim ceiling, both files
    summary = _read(tmp_path, t.SUMMARY_NAME)
    assert '"T1-DENSE-RREF": "ok"' in summary
    assert '"batch": "ok"' in summary
    assert "decode_calls=0" in summary
    assert "timing_records.jsonl" in summary
    assert "timing_summary.md" in summary
    assert t.CLAIM_CEILING[:60] in summary
    assert "600 s" in summary
    # A5: required batch ceiling + RSS budget recorded on the summary
    assert "batch-cap-s" in summary
    assert f"{_CAP}" in summary
    assert "`--rss-gib` = 2.0 GiB" in summary
    # 6dp printed rows: one per case + zero-decode stamp
    out = capsys.readouterr().out
    assert out.count("TIMING T1-DENSE-RREF case=") == 12
    assert out.count("TIMING T2-SPARSE-PEG case=") == 4
    assert out.count("decode_calls=0") == 16


def test_batch_rss_probe_and_budget_recorded(tmp_path, monkeypatch):
    batch, _, _ = _run(tmp_path, monkeypatch,
                       rss_fn=lambda: 3 * 1024 ** 3, rss_gib=4.0)
    for rec in batch["records"]:
        assert rec["rss_peak"] == pytest.approx(3.0)  # recorded, not gated
    assert batch["rss_gib"] == 4.0
    summary = _read(tmp_path, t.SUMMARY_NAME)
    assert "`--rss-gib` = 4.0 GiB" in summary  # A5 --rss-gib lands in summary


def test_t2_fake_segments_and_diagnostics_recorded(tmp_path, monkeypatch):
    batch, _, _ = _run(tmp_path, monkeypatch)
    t2_recs = [r for r in batch["records"] if r["arm"] == "T2-SPARSE-PEG"]
    assert len(t2_recs) == 4
    for rec in t2_recs:
        assert set(rec["segments"]) == {"peg_main_s", "bfs_girth_s"}
        assert rec["segments"]["peg_main_s"] == pytest.approx(0.04)
        assert rec["segments"]["bfs_girth_s"] == pytest.approx(0.01)
        assert rec["info"]["girth_agrees"] is True
        assert rec["info"]["status"] == "ok"
        assert rec["edges"] == 2 * rec["n"]     # info edges = len(triples)


def test_t2_success_without_edges_refused_fail_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def _no_edges(n, m, seed):
        return {"segments": {"peg_main_s": 0.0, "bfs_girth_s": 0.0},
                "info": {"n": int(n)}}  # missing edges ⇒ refused (A2/F3)

    with pytest.raises(t.Refusal):
        t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=_fake_t1(),
                  t2_fn=_no_edges, batch_cap_s=_CAP, rss_fn=lambda: 0)
    # A3: terminal must be one of the frozen three states
    with pytest.raises(t.Refusal):
        t.build_record(t.t1_plan()[0], segments={"rref_s": 0.0},
                       wall_s_total=0.0, info={}, rss_gib=0.0,
                       terminal="PASS", batch_cap_s=_CAP)


# -- F6 deadlines/budgets: retained rows, no continuation, NO NOT-RUN rows -------

def test_single_call_deadline_retained_no_continuation(tmp_path, monkeypatch):
    # 700 s per executed case > 600 s deadline ⇒ first row terminal
    t1, t2 = _fake_t1(), _fake_t2()
    batch, _, _ = _run(tmp_path, monkeypatch, t1=t1, t2=t2,
                       timer=_Clock(step=700.0))
    assert len(t1.calls) == 1          # only the first call ever ran
    assert t2.calls == []              # T2 never started (gate did not permit)
    assert batch["batch_state"] == "INCOMPLETE-batch"
    assert batch["stop_reason"] == "single-call-deadline"
    assert batch["tally"] == {"T1-DENSE-RREF": "INCOMPLETE-call",
                              "T2-SPARSE-PEG": "NOT-RUN",
                              "batch": "INCOMPLETE-batch"}
    records = _records(tmp_path)
    assert len(records) == 1                       # A3: no NOT-RUN rows
    assert records[0]["terminal"] == "INCOMPLETE-call"
    assert records[0]["wall_s_total"] == pytest.approx(700.0)
    assert records[0]["segments"] == {"rref_s": 0.02}
    text = _read(tmp_path, t.RECORDS_NAME)
    assert "NOT-RUN" not in text and "INCOMPLETE-batch" not in text
    assert all(r["decode_calls"] == 0 for r in records)
    summary = _read(tmp_path, t.SUMMARY_NAME)
    assert "INCOMPLETE-call" in summary
    assert '"T2-SPARSE-PEG": "NOT-RUN"' in summary      # tally/summary only
    assert "INCOMPLETE-batch" in summary


def test_batch_wall_cap_enforced_incomplete_batch_no_not_run_rows(
        tmp_path, monkeypatch):
    # batch wall clock: 150 s elapsed after case 1 > 10 s cap ⇒ stop
    t1, t2 = _fake_t1(), _fake_t2()
    batch, _, _ = _run(tmp_path, monkeypatch, t1=t1, t2=t2,
                       timer=_Clock(step=50.0), batch_cap_s=10.0)
    assert len(t1.calls) == 1 and t2.calls == []
    assert batch["batch_state"] == "INCOMPLETE-batch"
    assert batch["stop_reason"] == "batch-cap"
    assert batch["batch_ceiling_s"] == 10.0
    assert batch["tally"] == {"T1-DENSE-RREF": "INCOMPLETE-batch",
                              "T2-SPARSE-PEG": "NOT-RUN",
                              "batch": "INCOMPLETE-batch"}
    records = _records(tmp_path)
    assert len(records) == 1                       # A3: no NOT-RUN rows
    assert records[0]["terminal"] == "ok"          # executed case passed
    assert records[0]["wall_s_total"] == pytest.approx(50.0)
    text = _read(tmp_path, t.RECORDS_NAME)
    assert "NOT-RUN" not in text and "INCOMPLETE-batch" not in text
    summary = _read(tmp_path, t.SUMMARY_NAME)
    assert "INCOMPLETE-batch" in summary
    assert '"T2-SPARSE-PEG": "NOT-RUN"' in summary
    assert "batch-cap" in summary
    assert "600 s" in summary                      # per-call deadline intact


def test_call_failure_error_row_traceback_and_summary_still_written(
        tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[int] = []

    def _boom(m, n, seed, repeat):
        calls.append(1)
        if len(calls) == 3:
            raise RuntimeError("synthetic fake failure")
        return {"segments": {"rref_s": 0.0}, "info": {}}

    batch = t.execute(root=t.ROOT, uuid8=_UUID8, t1_fn=_boom,
                      t2_fn=_fake_t2(), batch_cap_s=_CAP, rss_fn=lambda: 0)
    root = tmp_path / "workspace" / "TIMING" / _UUID8
    records = [json.loads(line) for line in
               (root / t.RECORDS_NAME).read_text().splitlines()]
    assert len(records) == 3                       # 2 ok + 1 retained error
    assert [r["terminal"] for r in records] == ["ok", "ok", "error"]
    err = records[2]
    assert err["info"]["error_type"] == "RuntimeError"
    assert err["info"]["error"] == "synthetic fake failure"
    assert "Traceback (most recent call last)" in err["info"]["traceback"]
    assert "synthetic fake failure" in err["info"]["traceback"]
    assert err["segments"] == {}                   # no measured segments
    assert err["edges"] == 400 * 1024              # T1 edges still m*n
    assert all(r["decode_calls"] == 0 for r in records)
    assert len(calls) == 3                         # stopped at the failure
    # A3: gate closed ⇒ break, NO NOT-RUN rows, summary STILL written
    text = (root / t.RECORDS_NAME).read_text()
    assert "NOT-RUN" not in text and "INCOMPLETE-batch" not in text
    assert (root / t.SUMMARY_NAME).exists()
    summary = (root / t.SUMMARY_NAME).read_text()
    assert '"T1-DENSE-RREF": "error"' in summary
    assert '"T2-SPARSE-PEG": "NOT-RUN"' in summary
    assert '"batch": "INCOMPLETE-batch"' in summary
    assert batch["stop_reason"] == "call-error"
    assert batch["batch_state"] == "INCOMPLETE-batch"
    assert batch["tally"] == {"T1-DENSE-RREF": "error",
                              "T2-SPARSE-PEG": "NOT-RUN",
                              "batch": "INCOMPLETE-batch"}


# -- A4: T1 single segment, construction untimed, rank==m in info ---------------

def test_t1_single_segment_construction_untimed_rank_eq_m_source():
    assert t.SEGMENT_KEYS["T1-DENSE-RREF"] == ("rref_s",)  # ONE timed segment
    src = inspect.getsource(t.production_t1_call)
    # exact code-level assertions (source inspection only — never executed)
    assert '"rref_s": t2 - t1' in src
    assert '"matrix_build_s"' not in src            # construction not timed
    assert '"rank_eq_m": bool(rank == int(m))' in src  # rank==m → info
    i_build = src.index("rng.integers")             # dense build happens
    i_start = src.index("time.perf_counter()")      # BEFORE the timed window
    i_rank = src.rindex("peg.rank_GF1024")          # code call, not docstring
    assert i_build < i_start < i_rank
    # T2 info carries edges = len(triples)
    src2 = inspect.getsource(t.production_t2_call)
    assert '"edges": len(triples)' in src2


# -- A6: F7 three report-only lines + edge-linear extrapolation -----------------

def test_f7_three_lines_k4_round100_report_only_and_edge_extrapolation(
        tmp_path, monkeypatch):
    batch, _, _ = _run(tmp_path, monkeypatch, timer=_Clock(step=30.0))
    f7 = batch["f7_proposed"]
    assert f7["k"] == 4 and f7["report_only"] is True
    assert f7["measured_cases"] == 16 == f7["planned_cases"]
    assert f7["max_call_wall_s"] == pytest.approx(30.0)
    assert f7["t1_wall_sum_s"] == pytest.approx(360.0)   # 12 × 30 s
    assert f7["t2_wall_sum_s"] == pytest.approx(120.0)   # 4 × 30 s
    # F7 formula with measured substitution, k=4, rounded to whole 100 s:
    # cap_single = 30×4 = 120 → 100; cap_arm = (360+2×120)×4 = 2400;
    # batch_ceiling = 2 × cap_arm = 4800
    assert f7["cap_single_call_s"] == 100.0
    assert f7["cap_arm_s"] == 2400.0
    assert f7["batch_ceiling_s"] == 4800.0
    for value in (f7["cap_single_call_s"], f7["cap_arm_s"],
                  f7["batch_ceiling_s"]):
        assert value % 100 == 0  # 整百
    # edge-linear extrapolation: measured n=1024 (2048 edges) peg_main × 2
    extrap = batch["edge_extrapolation"]
    assert [e["case_id"] for e in extrap] == [2, 3]  # T2 n=1024 cells
    for e in extrap:
        assert e["edges_measured"] == 2048 and e["edges_target"] == 4096
        assert e["measured_peg_main_s"] == pytest.approx(0.04)
        assert e["extrapolated_peg_main_s"] == pytest.approx(0.08)
    summary = _read(tmp_path, t.SUMMARY_NAME)
    assert summary.count("F7-") == 3                 # exactly three F7 lines
    assert summary.count("report-only") >= 4         # 3 lines + extrapolation
    assert "k=4" in summary
    assert "whole 100 s" in summary
    assert "**100 s**" in summary
    assert "**2400 s**" in summary
    assert "**4800 s**" in summary
    assert "4096 edges / 2048 edges" in summary      # edge-linear formula
    assert "0.080000 s" in summary                   # measured × 2
    assert "never automatic" in summary              # report-only, not a cap


# -- production wiring: refusal BEFORE any real construction/rank call ----------

def test_production_refuses_off_plan_before_any_real_call(monkeypatch):
    hits: list[str] = []

    def _boom(*args, **kwargs):
        hits.append("called")
        raise AssertionError("production routine must never be reached")

    monkeypatch.setattr(t.peg, "peg_construct", _boom)
    monkeypatch.setattr(t.peg, "rank_GF1024", _boom)
    monkeypatch.setattr(t.peg, "sparse_to_dense", _boom)
    monkeypatch.setattr(t._mcde, "make_rho", _boom)
    # T1: off-plan seeds (incl. forbidden lineage) / shapes / repeat
    for bad_seed in (2026092001, 2026092011, 2026092413, 1, "2026092401",
                     None, True):
        with pytest.raises(t.Refusal):
            t.production_t1_call(400, 1024, bad_seed, 0)
    with pytest.raises(t.Refusal):
        t.production_t1_call(400, 1025, 2026092401, 0)   # off-grid shape
    with pytest.raises(t.Refusal):
        t.production_t1_call(400, 1024, 2026092401, 3)   # repeat out of range
    with pytest.raises(t.Refusal):
        t.production_t1_call(400, 1024, 2026092401, None)
    # T2: off-plan cells / seeds
    for bad_seed in (2026092001, 2026092011, 2026092401, 1, None):
        with pytest.raises(t.Refusal):
            t.production_t2_call(512, 104, bad_seed)
    with pytest.raises(t.Refusal):
        t.production_t2_call(512, 105, 2026092421)       # off-grid shape
    with pytest.raises(t.Refusal):
        t.production_t2_call(1024, 104, 2026092421)      # seed/shape mismatch
    with pytest.raises(t.Refusal):
        t.production_t2_call(512, 104, None)
    assert hits == []  # ZERO production construction / rank / rho calls


# -- F3 standalone BFS girth (pure tiny graphs) ---------------------------------

def test_bfs_girth_tiny_graphs():
    # 4-cycle: two variables fully connected to two checks
    quad = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
    assert t.bfs_girth(quad, 2, 2) == 4
    # acyclic forest ⇒ None sentinel (frozen v10 semantics)
    assert t.bfs_girth([(0, 0, 1), (1, 1, 1)], 2, 2) is None
    assert t.bfs_girth([], 4, 2) is None
    # 6-cycle: v0-c0-v1-c1-v2-c2-v0
    six = [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 2, 1),
           (2, 2, 1), (2, 0, 1)]
    assert t.bfs_girth(six, 3, 3) == 6
    # 4-cycle plus pendant edge ⇒ still 4
    with_pendant = quad + [(2, 2, 1)]
    assert t.bfs_girth(with_pendant, 3, 3) == 4
    with pytest.raises(ValueError):
        t.bfs_girth([(0, 5, 1)], 2, 2)  # out-of-bounds triple


# -- F5: zero decode, zero channel/real-data paths in the runner source ---------

def test_zero_decode_no_channel_or_decoder_paths_in_source():
    src = open(t.__file__, encoding="utf-8").read()
    banned = ["decode_error_domain", "fftqspa", "smoke_decode", "max_iter",
              "bind_empirical", ".npz", "gamma_f03", "PROJECT_DATA_ROOT",
              "Raw Data", "qsc_pair_sampler", "exact_match",
              "run_mcde_posterior"]
    present = [tok for tok in banned if tok in src]
    assert present == [], f"forbidden channel/decoder tokens present: {present}"
    # no callable starting with "decode" exists; ledger frozen at zero
    assert not [n for n in dir(t) if n.startswith("decode")]
    assert t.DECODE_CALLS == 0
    # the only real-data mention is the FORWARDING guard, never a read path
    assert t.FORBIDDEN_PATH_TOKENS == (".ttbin", "gamma")
