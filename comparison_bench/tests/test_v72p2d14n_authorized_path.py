"""R205 fake authorized-path tests (R2 authorized-path completion).

Fake/test machinery ONLY: injected fake adapters run the TRUE authorized
CLI branch (``--n14-batch --execution-authorized``) against fresh
gitignored ``workspace/`` scratch roots — never the frozen future root,
never the production binder, never the Model-F loader, never the
production decoder. Acceptance per packet: exactly 288 fake calls (72x4),
32 setup units, six files, deterministic plan identities, expected fake
gate/terminal, read-only verifier PASS, and proof of zero production
entry (named v35/loader keys absent from ``sys.modules`` plus a zero-call
production-binder spy).

Process rule (Tests §4): this file must run in a process where the named
production keys are absent at entry — standalone
``pytest -p no:cacheprovider comparison_bench/tests/test_v72p2d14n_authorized_path.py``
first, or in a full-suite run where this file sorts before any
v35-importing suite. Every test here injects ALL adapters (including the
provenance guard and verifier token), so nothing in this file imports the
production modules even mid-run.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d14_discriminator_development.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d14n_calibrated_discriminator as n14  # noqa: E402

runner = _load_module("v72p2d14_runner_r205", RUNNER_PATH)

#: Production entries that must never appear while the fake branch runs:
#: the v35 decoder/provenance module, the Model-F contrast loader module
#: (both registered names), and the R2-runner reuse keys (binder-only).
PRODUCTION_ABSENT_KEYS = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "v72p2d10_r2_runner_reuse_n14",
    "v72p2d10_r2_runner_reuse_d11",
)

FUTURE_ROOT = (ROOT / n14.FUTURE_ROOT).resolve()


def _assert_no_production_entry():
    absent = [key for key in PRODUCTION_ABSENT_KEYS if key in sys.modules]
    assert absent == [], "production entry on fake path: %r" % (absent,)


@pytest.fixture()
def scratch_root():
    path = ROOT / "workspace" / ("r205_fake_authorized_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert path.resolve() != FUTURE_ROOT
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# --------------------------------------------------------------------------- #
# fakes (never the production decoder; never Model-F content)
# --------------------------------------------------------------------------- #
def _fake_l1_graph(profile, seed):
    cell = n14.degree_cell(profile)
    H = np.zeros((cell["m"], cell["n"]), dtype=np.int64)
    for v in range(cell["n"]):
        H[v % cell["m"], v] = 1
    return {"arm": profile, "width": 128, "graph_seed": int(seed),
            "n": cell["n"], "m": cell["m"],
            "E": int(np.count_nonzero(H)), "edges": [], "coefficients": [],
            "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


def _fake_l2_graph(seed):
    cell = n14.degree_cell("L2")
    H = np.zeros((cell["m"], cell["n"]), dtype=np.int64)
    for v in range(cell["n"]):
        H[v % cell["m"], v] = 1
    return {"arm": "L2", "width": 128, "graph_seed": int(seed),
            "n": cell["n"], "m": cell["m"],
            "E": int(np.count_nonzero(H)), "edges": [], "coefficients": [],
            "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


def _fake_block(seed):
    n = 128
    return {"bob": np.zeros(n, dtype=np.int64),
            "u1": np.zeros(n, dtype=np.int64),
            "u2": np.zeros(n, dtype=np.int64),
            "prior": np.full((n, 32), 1.0 / 32.0)}


class _FakeResult:
    def __init__(self, n, provenance="CHECK_UPDATED", beliefs=None):
        self.x_hat = np.zeros(n, dtype=np.uint8)
        self.syndrome_ok = True
        self.iterations = 1
        self.status = "converged_exact"
        self.belief_provenance = provenance
        self.final_beliefs = beliefs


def _fake_guard(provenance):
    if provenance != "CHECK_UPDATED":
        raise n14.ProvenanceRefused(
            "refusing non-CHECK_UPDATED provenance %r" % (provenance,))
    return provenance


def _fake_adapters(calls=None, loads=None, provenance="CHECK_UPDATED",
                   beliefs=None):
    calls = calls if calls is not None else []
    loads = loads if loads is not None else []

    def fake_decode(H, prior, syn, **kw):
        calls.append(tuple(H.shape))
        return _FakeResult(H.shape[1], provenance, beliefs)

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        loads.append(str(root))
        return (None, None, None)

    def fake_sample(p_b, p_f, p1, seed):
        return _fake_block(seed)

    def fake_transfer(belief, block):
        return block["prior"]

    def fake_oracle(block):
        return block["prior"]

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "sample_fn": fake_sample,
            "transfer_fn": fake_transfer, "oracle_prior_fn": fake_oracle,
            "provenance_guard_fn": _fake_guard,
            "build_l1_fn": _fake_l1_graph,
            "build_l2_fn": _fake_l2_graph}


def _spy_on_binder(monkeypatch):
    calls = []

    def boom():
        calls.append(1)
        raise AssertionError("production binder entered on the fake path")

    monkeypatch.setattr(runner, "bind_production_adapters", boom)
    return calls


def _authorized_args(scratch):
    return ["--n14-batch", "--execution-authorized",
            "--out-root", str(scratch)]


def _read_summary(scratch):
    return json.loads((scratch / "summary.json").read_text("utf-8"))


# --------------------------------------------------------------------------- #
# R205 core: true authorized branch, 288/288 fakes, six files, verifier PASS
# --------------------------------------------------------------------------- #
def test_r205_authorized_true_branch_fake_288(monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls, loads = [], []
    adapters = _fake_adapters(calls, loads)
    binder_calls = _spy_on_binder(monkeypatch)
    rc = runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert rc == 0
    assert len(calls) == 288  # 72 L045 + 72 L055 + 72 APP + 72 ORACLE
    assert sorted(shape[0] for shape in calls).count(110) == 144
    assert sorted(shape[0] for shape in calls).count(104) == 144
    assert len(loads) == 1  # injected prior path ran exactly once
    assert binder_calls == []  # production binder never entered
    _assert_no_production_entry()
    assert sorted(p.name for p in scratch_root.iterdir()) == \
        sorted(n14.EVIDENCE_FILES)
    summary = _read_summary(scratch_root)
    assert summary["setup_calls"] == 32  # 18 graphs + 12 blocks + 2 fixed
    assert summary["scientific_calls"] == 288
    assert summary["planned_calls"] == 288
    assert summary["terminal"] == n14.T_SCALE_VALIDATION
    assert summary["pools"] == {"L045": 72, "L055": 72,
                                "L2_APP_joint": 72, "L2_ORACLE": 72}
    assert summary["app_source_profile"] == runner.APP_SOURCE_PROFILE \
        == "L055"
    assert summary["engineering_reason"] == ""
    plan = n14.build_call_plan()
    with open(scratch_root / "decoder_records.csv", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(plan) == 288
    for index, (row, entry) in enumerate(zip(rows, plan)):
        assert int(row["call_idx"]) == index
        for key in ("arm", "pair_idx", "l1_graph_seed", "l2_graph_seed",
                    "block_seed"):
            assert str(row[key]) == str(entry[key]), (index, key)
    assert runner.verify_root(
        str(scratch_root), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph,
        check_updated_token_value="CHECK_UPDATED") is True
    _assert_no_production_entry()
    assert not FUTURE_ROOT.exists()


# --------------------------------------------------------------------------- #
# R205 failure tests: contract stop, existing root, partial root, provenance
# --------------------------------------------------------------------------- #
def test_r205_first_contract_error_stops_before_work(
        monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls = []
    adapters = _fake_adapters(calls)
    del adapters["sample_fn"]  # broken adapter contract
    _spy_on_binder(monkeypatch)
    with pytest.raises(ValueError):
        runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert calls == []  # stopped before any decoder contact
    assert not scratch_root.exists()  # stopped before any root creation
    _assert_no_production_entry()


def test_r205_existing_root_refusal_before_work(
        monkeypatch, scratch_root):
    _assert_no_production_entry()
    scratch_root.mkdir(parents=True)
    (scratch_root / "marker.txt").write_text("pre-existing", "utf-8")
    calls = []
    adapters = _fake_adapters(calls)
    _spy_on_binder(monkeypatch)
    with pytest.raises(FileExistsError):
        runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert calls == []  # refusal before any decoder contact
    assert (scratch_root / "marker.txt").read_text("utf-8") == "pre-existing"
    _assert_no_production_entry()


def test_r205_partial_root_fails_verifier(monkeypatch, scratch_root):
    _assert_no_production_entry()
    adapters = _fake_adapters()
    _spy_on_binder(monkeypatch)
    assert runner.main(_authorized_args(scratch_root),
                        adapters_override=adapters) == 0
    assert sorted(p.name for p in scratch_root.iterdir()) == \
        sorted(n14.EVIDENCE_FILES)
    (scratch_root / "arm_summary.csv").unlink()  # partial root
    assert runner.verify_root(
        str(scratch_root), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph,
        check_updated_token_value="CHECK_UPDATED") is False
    _assert_no_production_entry()


def test_r205_invalid_app_provenance_refusal(monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls = []
    adapters = _fake_adapters(
        calls, provenance="PRIOR_ONLY",
        beliefs=np.zeros((128, 32), dtype=np.float64))
    _spy_on_binder(monkeypatch)
    rc = runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert rc == 0  # blocked root is still written (fail-closed evidence)
    assert len(calls) == 144  # L1 phase only: zero L2 decoder contact
    summary = _read_summary(scratch_root)
    assert summary["terminal"] == n14.T_ENGINEERING_BLOCKED
    assert summary["engineering_reason"].startswith("provenance refusal")
    assert summary["scientific_calls"] == 145  # 144 L1 + 1 refusal record
    with open(scratch_root / "decoder_records.csv", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[-1]["status"] == "provenance_refused"
    assert rows[-1]["arm"] == n14.L2_ARM
    assert runner.verify_root(
        str(scratch_root), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph,
        check_updated_token_value="CHECK_UPDATED") is False
    _assert_no_production_entry()
    assert not FUTURE_ROOT.exists()


def test_r205_nonfinite_l055_belief_stops_before_app(
        monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls = []
    adapters = _fake_adapters(
        calls, beliefs=np.full((128, 32), np.inf))
    _spy_on_binder(monkeypatch)
    with pytest.raises(ValueError, match="nonfinite"):
        runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert len(calls) == 144  # L1 phase ran; zero APP dispatches
    assert not scratch_root.exists()  # loud stop before any write
    _assert_no_production_entry()


def test_r205_app_source_repicks_refused(monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls = []
    adapters = _fake_adapters(calls)
    _spy_on_binder(monkeypatch)
    with pytest.raises(ValueError, match="frozen"):
        runner.run_authorized_batch(
            str(scratch_root), n14.MODEL_F_INPUT_ROOT,
            adapters=adapters, build_l1_fn=_fake_l1_graph,
            build_l2_fn=_fake_l2_graph, app_source_profile="L045")
    assert calls == []  # refused before any decoder contact
    assert not scratch_root.exists()
    assert runner.APP_SOURCE_PROFILE == "L055"
    _assert_no_production_entry()
