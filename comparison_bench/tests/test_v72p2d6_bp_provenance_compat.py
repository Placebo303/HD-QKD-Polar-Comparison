"""D6 R1d BP provenance compatibility tests (Track A R04).

Tiny explicit in-memory fixtures/fakes only. Zero real decoder: every test
drives ``_worker_main``/``run_cell`` with monkeypatched fakes; the
production ``bind_historical_decoder`` is never bound (patched to a counting
sentinel). No Model-F/CAL/VAL/real/raw reads, no R1d/G1/G2/``--phase``, no
roots, no UUID. Fully in-memory: no files are created.
"""

import importlib.util
import pathlib
import sys
import threading
import time

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]

_MISSING = object()  # marks a legacy result dict with no provenance key


def _load_dev(name):
    for _k in [k for k in list(sys.modules)
               if k == "comparison_bench" or k.startswith("comparison_bench.")]:
        del sys.modules[_k]
    sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
    sp = ROOT / "scripts" / "v72p2d6_graph_mother_development.py"
    spec = importlib.util.spec_from_file_location(name, str(sp))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dev = _load_dev("d6dev_bpcompat")

N = 4
TINY_LOG_BEL = np.log(np.full((N, 32), 1.0 / 32, dtype=np.float64))


class FakeConn:
    """In-memory stand-in for the worker Pipe (no processes, no roots)."""

    def __init__(self, tasks):
        self._tasks = list(tasks)
        self.sent = []

    def send(self, obj):
        self.sent.append(obj)

    def recv(self):
        return self._tasks.pop(0) if self._tasks else None


def _task(return_beliefs=True):
    return {"h": np.ones((N, N), dtype=np.uint8),
            "prior": np.full((N, 32), 1.0 / 32, dtype=np.float64),
            "x_true": np.zeros(N, dtype=np.int64),
            "return_beliefs": bool(return_beliefs)}


def _run_worker(monkeypatch, decode_fake, tasks):
    bind_calls = []

    def fake_bind():
        bind_calls.append(1)
        return object()

    monkeypatch.setattr(dev.d5, "bind_historical_decoder", fake_bind)
    monkeypatch.setattr(dev.d5, "_decode_block", decode_fake)
    conn = FakeConn(tasks)
    dev._worker_main(conn, str(ROOT / "comparison_bench" / "src"))
    assert len(bind_calls) == 1  # fake bind only; real decoder never bound
    return conn.sent


def _six_fake(provenance):
    def _fake(dec, h, prior, xt):
        return (True, True, 5, True, TINY_LOG_BEL.copy(), provenance)

    return _fake


def _five_fake(dec, h, prior, xt):
    return (True, True, 5, True, TINY_LOG_BEL.copy())


# ---------------------------------------------------------------------------
# Worker: six-value success + provenance transport
# ---------------------------------------------------------------------------

def test_six_value_success_carries_provenance(monkeypatch):
    hello, out = _run_worker(monkeypatch, _six_fake("CHECK_UPDATED"),
                             [_task(True), None])
    assert hello["event"] == "ready" and hello["ready"] is True
    assert hello["warmup"] == "ok"
    assert out["crash"] is False and out["error"] == ""
    assert out["exact"] is True and out["iterations"] == 5
    assert out["belief_provenance"] == "CHECK_UPDATED"
    assert np.array_equal(np.asarray(out["beliefs"]), TINY_LOG_BEL)


def test_provenance_flows_even_when_beliefs_not_requested(monkeypatch):
    _, out = _run_worker(monkeypatch, _six_fake("PRIOR_ONLY"),
                         [_task(False), None])
    assert out["crash"] is False
    assert out["beliefs"] is None
    assert out["belief_provenance"] == "PRIOR_ONLY"


def test_five_value_incompatibility_is_loud_and_not_ready(monkeypatch):
    # R01 defect mode after repair: warmup gates loudly (ready=false);
    # any task-path mapping keeps the loud ValueError arity signature.
    hello, out = _run_worker(monkeypatch, _five_fake, [_task(True), None])
    assert hello["ready"] is False
    assert str(hello["warmup"]).startswith("fail:")
    assert "decoder-result-shape-incompatible" in str(hello["warmup"])
    assert out["crash"] is True
    assert "ValueError" in out["error"] and "expected 6, got 5" in out["error"]


def test_warmup_exception_reports_not_ready(monkeypatch):
    def _boom(dec, h, prior, xt):
        raise RuntimeError("injected-warmup-boom")

    hello, out = _run_worker(monkeypatch, _boom, [_task(True), None])
    assert hello["ready"] is False
    assert "injected-warmup-boom" in str(hello["warmup"])
    assert out["crash"] is True and "injected-warmup-boom" in out["error"]


def test_five_unpack_of_six_raises_value_error():
    # R01 mechanism pin: the pre-repair unpack shape cannot hold the
    # accepted six-value result; this must stay a loud ValueError.
    six = (True, True, 5, True, TINY_LOG_BEL, "CHECK_UPDATED")
    with pytest.raises(ValueError, match="too many values to unpack"):
        e, s, it, f, bel = six  # noqa: F841


# ---------------------------------------------------------------------------
# Parent run_cell gate (fake worker, tiny arrays, real d5 math only)
# ---------------------------------------------------------------------------

def _cell_inputs():
    p1 = np.full((32, 8), 1.0 / 32, dtype=np.float64)
    p2 = np.full((32, 8, 32), 1.0 / 32, dtype=np.float64)
    blk = {"bob": np.array([0, 1, 2, 3], dtype=np.int64),
           "u1": np.zeros(N, dtype=np.int64),
           "u2": np.zeros(N, dtype=np.int64)}
    meta = {"arm": "B0_D5_DV3_NATIVE", "n": N, "seed": 1, "point": "f1.2",
            "r1": 2, "r2": 2, "matrix_id": "m"}
    state = {"calls": 0, "setup_calls": 0, "t0": time.perf_counter(),
             "deadline": float(time.perf_counter()) + 3600,
             "records": [], "peak_rss": 0, "budget_stop": False,
             "chunk_wall_blocked": False, "lock": threading.Lock()}
    h = np.ones((N, N), dtype=np.uint8)
    return p1, p2, blk, meta, state, h


class _SeqWorker:
    """First call answers L1 with a canned result; later calls succeed."""

    def __init__(self, l1):
        self._l1 = dict(l1)
        self.calls = []
        self.pids = ["7"]

    def call(self, task, state=None):
        self.calls.append(task)
        if len(self.calls) == 1:
            return dict(self._l1)
        return {"exact": True, "syndrome_ok": True, "iterations": 4,
                "finite": True, "beliefs": None, "crash": False,
                "timeout": False, "wall_timeout": False, "wall_s": 0.01,
                "rss": 1000, "error": ""}


def _l1_result(provenance=_MISSING):
    rec = {"exact": True, "syndrome_ok": True, "iterations": 5,
           "finite": True, "beliefs": TINY_LOG_BEL.copy(), "crash": False,
           "timeout": False, "wall_timeout": False, "wall_s": 0.01,
           "rss": 1000, "error": ""}
    if provenance is not _MISSING:
        rec["belief_provenance"] = provenance
    return rec


def _spy_app(monkeypatch):
    calls = []
    real = dev.d5.app_fed_l2_prior

    def spy(p2, bob, q):
        calls.append(tuple(np.asarray(q).shape))
        return real(p2, bob, q)

    monkeypatch.setattr(dev.d5, "app_fed_l2_prior", spy)
    return calls


def test_check_updated_passthrough_runs_app_and_l2(monkeypatch):
    app_calls = _spy_app(monkeypatch)
    p1, p2, blk, meta, state, h = _cell_inputs()
    worker = _SeqWorker(_l1_result("CHECK_UPDATED"))
    cell = dev.run_cell(worker, h, h, 2, 2, p1, p2, blk, N, meta, state)
    assert app_calls == [(N, 32)]  # mixer saw exactly one APP computation
    assert len(worker.calls) == 3  # L1 + L2-APP + L2-oracle all dispatched
    assert cell["modes"][1]["mode"] == "L2-APP"
    assert int(cell["modes"][1]["call_idx"]) >= 0
    assert cell["modes"][1]["crash"] is False
    assert state["calls"] == 3 and len(state["records"]) == 3


@pytest.mark.parametrize("token", ["PRIOR_ONLY", "WARM_START_UNSPECIFIED",
                                   None, "SOME_UNKNOWN_TOKEN"])
def test_refused_provenance_blocks_without_crash_or_l2(monkeypatch, token):
    app_calls = _spy_app(monkeypatch)
    p1, p2, blk, meta, state, h = _cell_inputs()
    worker = _SeqWorker(_l1_result(token))
    cell = dev.run_cell(worker, h, h, 2, 2, p1, p2, blk, N, meta, state)
    assert app_calls == []  # mixer never ran
    assert len(worker.calls) == 2  # L1 + L2-oracle only; no L2-APP decode
    blocked = cell["modes"][1]
    assert blocked["mode"] == "L2-APP" and int(blocked["call_idx"]) == -1
    assert blocked["crash"] is False  # named refusal, never a crash cell
    assert "provenance-blocked" in blocked["error"]
    assert repr(token) in blocked["error"]  # reproducible token marker
    assert blocked["note"] == dev.PROVENANCE_BLOCKED_NOTE
    assert state["calls"] == 2 and len(state["records"]) == 2  # no budget
    assert [m["mode"] for m in cell["modes"]] == ["L1", "L2-APP", "L2-oracle"]
    assert int(cell["modes"][2]["call_idx"]) >= 0  # oracle untouched


def test_missing_provenance_key_blocks_like_none(monkeypatch):
    # Legacy worker dicts with no provenance key at all must fail closed.
    app_calls = _spy_app(monkeypatch)
    p1, p2, blk, meta, state, h = _cell_inputs()
    l1 = _l1_result()
    assert "belief_provenance" not in l1
    worker = _SeqWorker(l1)
    cell = dev.run_cell(worker, h, h, 2, 2, p1, p2, blk, N, meta, state)
    assert app_calls == [] and len(worker.calls) == 2
    blocked = cell["modes"][1]
    assert blocked["crash"] is False
    assert "provenance-blocked" in blocked["error"] and "None" in blocked["error"]


def test_l1_crash_keeps_legacy_skip_record(monkeypatch):
    # No beliefs (crashed L1) keeps the pre-existing skip path unchanged:
    # crash placeholder, NOT the provenance-blocked marker.
    app_calls = _spy_app(monkeypatch)
    p1, p2, blk, meta, state, h = _cell_inputs()
    l1 = _l1_result("CHECK_UPDATED")
    l1.update({"beliefs": None, "crash": True, "exact": False,
               "syndrome_ok": False, "iterations": -1, "finite": False})
    worker = _SeqWorker(l1)
    cell = dev.run_cell(worker, h, h, 2, 2, p1, p2, blk, N, meta, state)
    assert app_calls == []
    skipped = cell["modes"][1]
    assert skipped["crash"] is True  # legacy unavailable-L1 placeholder
    assert skipped["note"] == "app-undefined-l1-unavailable"
    assert "provenance-blocked" not in skipped["error"]


# ---------------------------------------------------------------------------
# Frozen dispatch/matrix/schema pins (no scientific drift)
# ---------------------------------------------------------------------------

def test_frozen_schema_and_dispatch_unchanged():
    assert dev.DECODER_FIELDNAMES == [
        "call_idx", "arm", "n", "seed", "point", "rows_l1", "rows_l2",
        "mode", "matrix_id", "exact", "syndrome_ok", "iterations",
        "finite", "crash", "timeout", "wall_timeout",
        "prior_mass_on_truth", "wall_s", "rss_bytes", "watchdog_ok",
        "worker_pid", "respawn_pid", "error"]
    assert list(dev.R1D_ARMS) == ["B0_D5_DV3_NATIVE",
                                  "B1_D5_DV3_COMMON_LABELS", "T1_PEG_DV3"]
    assert len(dev.R1D_VALID_SUBSET) == 22
    assert dev.MODES == ("L1", "L2-APP", "L2-oracle")
    assert dev.POINTS == ("f1.0", "f1.2", "square")
    assert dev.PROVENANCE_BLOCKED_NOTE == \
        "provenance-blocked-l1-not-check-updated"


def test_source_wiring_pins():
    src = (ROOT / "scripts" / "v72p2d6_graph_mother_development.py"
           ).read_text(encoding="utf-8")
    assert "e, s, it, f, bel, prov = core._decode_block" in src
    assert "require_check_updated_provenance" in src
    assert '"belief_provenance": prov' in src
    assert '"belief_provenance": res.get("belief_provenance")' in src
    # Worker crash-mapping except not broadened (exact legacy clause kept).
    assert "except Exception as ex:  # noqa: BLE001 - crash consumes the cell" in src
