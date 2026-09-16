"""D7 root-cause R1 focused tests: consistency, multi-graph, ladder, G2.

Fake decoders only. No production decoder, no CAL/VAL, no Model-F read, no
formal root write. Multi-graph output roots are fresh additive
``workspace/<task>/<uuid>`` directories under a temporary repo root.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d7_consistency_multigraph.py")
_SPEC = importlib.util.spec_from_file_location(
    "d7_r1_consistency_multigraph_test", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)
d5 = mod.d5
d7c = mod.d7c
d7e = mod.d7e

CHECK = "CHECK_UPDATED"
PRIOR_ONLY = "PRIOR_ONLY"


# --------------------------------------------------------------------------
# shared tiny fixtures (Q=32 paths only; fake decoders only)
# --------------------------------------------------------------------------
def _tiny_tables():
    rng = np.random.default_rng(11)
    raw = rng.random((64, 8)) + 0.5
    p_f = raw / raw.sum(axis=0)
    p_b = np.full(8, 1.0 / 8)
    return p_b, p_f


def _wide_h():
    h1 = np.array([[1, 1, 0, 0, 0, 0, 0, 0],
                   [0, 1, 2, 0, 0, 0, 0, 0],
                   [0, 0, 1, 1, 0, 0, 0, 0],
                   [0, 0, 0, 1, 2, 0, 0, 0],
                   [0, 0, 0, 0, 1, 1, 0, 0],
                   [0, 0, 0, 0, 0, 1, 2, 0],
                   [0, 0, 0, 0, 0, 0, 1, 1]], dtype=np.int64)
    h2 = np.array([[1, 2, 0, 0, 0, 0, 0, 0],
                   [0, 1, 1, 0, 0, 0, 0, 0],
                   [0, 0, 1, 2, 0, 0, 0, 0],
                   [0, 0, 0, 1, 1, 0, 0, 0],
                   [0, 0, 0, 0, 1, 2, 0, 0],
                   [0, 0, 0, 0, 0, 1, 1, 0],
                   [0, 0, 0, 0, 0, 0, 1, 2],
                   [0, 0, 0, 0, 0, 0, 0, 1]], dtype=np.int64)
    return {"L1": h1, "L2": h2}


class FakeDecoder:
    """Deterministic CHECK_UPDATED fake with explicit provenance."""

    def __init__(self, x_hat_value=0, syndrome_ok=False, iterations=1,
                 provenance=CHECK):
        self.x_hat_value = x_hat_value
        self.syndrome_ok = syndrome_ok
        self.iterations = iterations
        self.provenance = provenance
        self.calls = []

    def __call__(self, h, prior, syndrome, layer=None):
        prior = np.asarray(prior, dtype=np.float64)
        self.calls.append((np.shape(h), prior.shape, layer))
        n = prior.shape[0]
        out = {"x_hat": np.full(n, self.x_hat_value, dtype=np.int64),
               "syndrome_ok": self.syndrome_ok,
               "iterations": self.iterations,
               "final_beliefs": np.zeros_like(prior)}
        if self.provenance is not None:
            out["belief_provenance"] = self.provenance
        return out


def _b_fixture(n=6, b_dim=4, seed=7):
    rng = np.random.default_rng(seed)
    raw = rng.random((1024, b_dim)) + 1e-6
    pf = raw / raw.sum(axis=0, keepdims=True)
    block = {"bob": rng.integers(0, b_dim, size=n),
             "u1": rng.integers(0, 32, size=n),
             "u2": rng.integers(0, 32, size=n)}
    h1 = rng.integers(0, 32, size=(4, n))
    h2 = rng.integers(0, 32, size=(5, n))
    beliefs = rng.normal(size=(n, 32)) * 2.0
    return pf, block, h1, h2, beliefs


def _res(x_hat, beliefs, provenance=CHECK, iterations=2, syndrome_ok=True):
    out = {"x_hat": np.asarray(x_hat, dtype=np.int64).copy(),
           "syndrome_ok": bool(syndrome_ok),
           "iterations": int(iterations),
           "final_beliefs": (None if beliefs is None
                             else np.asarray(beliefs, dtype=np.float64).copy())}
    if provenance is not None:
        out["belief_provenance"] = provenance
    return out


class _SeqFake:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, h, prior, syndrome, layer=None):
        self.calls.append({"prior": np.asarray(prior, dtype=np.float64).copy(),
                           "syndrome": np.asarray(syndrome).copy(),
                           "shape": np.shape(h), "layer": layer})
        return self.results[len(self.calls) - 1]


# --------------------------------------------------------------------------
# T0: import and frozen matrix
# --------------------------------------------------------------------------
def test_t0_import_and_frozen_matrix():
    slots = mod.frozen_slots()
    assert len(slots) == 384 == mod.MAX_CALLS
    assert mod.GRAPH_PAIRS == ((2026090501, 2026090502),
                               (2026091401, 2026091402),
                               (2026091501, 2026091502))
    assert mod.BLOCK_SEEDS == tuple(range(2026091300, 2026091316))
    assert mod.F_VALUES == (1.2, 1.0)
    assert mod.F_ROWS == {1.2: {"L1": 59, "L2": 52},
                          1.0: {"L1": 49, "L2": 43}}
    assert mod.ARM_IDS == ("L1_MARGINAL", "L1_TO_L2_TRANSFER",
                           "L2_MARGINAL", "L2_TO_L1_TRANSFER")
    per_graph = sum(1 for s in slots if s["graph_idx"] == 0)
    per_graph_f = sum(1 for s in slots if s["graph_idx"] == 0
                      and s["f"] == 1.2)
    assert per_graph == 128 and per_graph_f == 64
    # every (graph, f, seed) block holds the four arms in frozen order
    seen = {}
    for slot in slots:
        seen.setdefault((slot["graph_idx"], slot["f"], slot["seed"]),
                        []).append(slot["arm"])
    assert len(seen) == 3 * 2 * 16
    for arms in seen.values():
        assert tuple(arms) == mod.ARM_IDS
    assert mod.TERMINALS == (
        "GRAPH_SENSITIVITY_OBSERVED",
        "NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE",
        "INCONCLUSIVE", "MULTIGRAPH_ENGINEERING_BLOCKED")
    assert mod.SCOPE_TAG == "EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION"


# --------------------------------------------------------------------------
# B01/B02: canonical helpers and same-input equivalence
# --------------------------------------------------------------------------
def test_b01_canonical_helpers_match_d7_formulas():
    pf, block, h1, h2, beliefs = _b_fixture()
    joint = pf.reshape(32, 32, pf.shape[1])
    p2 = d5.conditionalize_f_to_p2(pf)
    q = d5.canonical_source_q(beliefs)
    assert np.array_equal(q, d7e.softmax_source_q(beliefs))
    left = d5.canonical_transfer_l2_prior(p2, block["bob"], q)
    right = d7e.transfer_prior_l1_to_l2(joint, block["bob"], q)
    assert float(np.max(np.abs(left - right))) < 1e-12
    # malformed returns are refused, never repaired
    with pytest.raises(ValueError):
        d5.canonical_source_q(np.zeros((3, 1)))
    with pytest.raises(ValueError):
        d5.canonical_source_q(np.array([[0.0, np.inf] + [0.0] * 30]))
    with pytest.raises(ValueError):
        d5.canonical_source_q(np.zeros(32))


def test_b02_same_input_equivalence_report():
    pf, block, h1, h2, beliefs = _b_fixture()
    fake = _SeqFake([_res(block["u1"], beliefs), _res(block["u2"], beliefs),
                     _res(block["u1"], beliefs), _res(block["u2"], beliefs)])
    report = mod.compare_same_input(p_f=pf, block=block, h1=h1, h2=h2,
                                    beliefs=beliefs, decode_fn=fake)
    assert report["ok"] is True
    assert report["first_mismatch"] is None
    assert report["items"]["q"]["mode"] == "exact"
    assert report["items"]["q"]["max_abs_diff"] == 0.0
    assert report["items"]["l1_input_prior"]["mode"] == "atol"
    assert report["items"]["l1_input_prior"]["equal"] is True
    assert report["items"]["l2_transfer_prior"]["equal"] is True
    assert report["items"]["l1_input_prior"]["max_abs_diff"] < 1e-12
    assert report["items"]["l2_transfer_prior"]["max_abs_diff"] < 1e-12
    for name in ("l1_syndrome", "l2_syndrome", "l1_decoded_target",
                 "l2_decoded_target", "l1_counters", "l2_counters"):
        assert report["items"][name]["equal"] is True, name
    assert len(fake.calls) == 4
    # the paths consume identical decoder inputs (priors within the frozen
    # 1e-12 reassociation bound; syndromes exactly)
    assert np.allclose(fake.calls[0]["prior"], fake.calls[2]["prior"],
                       rtol=0, atol=1e-12)
    assert np.allclose(fake.calls[1]["prior"], fake.calls[3]["prior"],
                       rtol=0, atol=1e-12)
    assert np.array_equal(fake.calls[0]["syndrome"], fake.calls[2]["syndrome"])
    assert np.array_equal(fake.calls[1]["syndrome"], fake.calls[3]["syndrome"])


def test_b02_g1_layered_capture_matches_d7_priors():
    pf, block, h1, h2, beliefs = _b_fixture()
    joint = pf.reshape(32, 32, pf.shape[1])
    results = [_res(block["u1"], beliefs), _res(block["u2"], beliefs)]
    cap = mod.g1_layered_capture(p_f=pf, block=block, h1=h1, h2=h2,
                                 decode_results=results)
    d7_prior1 = d7c.decoder_prior(
        d7c.condition_prior_qn(joint, "L1_MARGINAL", block))
    d7_prior2 = d7e.build_transfer_prior(
        joint, "L1_TO_L2", block["bob"],
        d7e.softmax_source_q(beliefs))
    assert float(np.max(np.abs(cap["calls"][0]["prior"] - d7_prior1))) < 1e-12
    assert float(np.max(np.abs(cap["calls"][1]["prior"] - d7_prior2))) < 1e-12
    assert np.array_equal(cap["calls"][0]["syndrome"],
                          d5._gf32_syndrome(h1, block["u1"]))
    assert np.array_equal(cap["calls"][1]["syndrome"],
                          d5._gf32_syndrome(h2, block["u2"]))
    counters = cap["counters"]
    assert counters["app_l1_exact"] and counters["app_l2_exact"]
    assert counters["transfer_invoked"] is True
    assert counters["app_l1_provenance"] == CHECK


# --------------------------------------------------------------------------
# B03/B04: provenance boundary and mismatch localization
# --------------------------------------------------------------------------
@pytest.mark.parametrize("case", ["check", "missing", "none", "prior_only",
                                  "unknown", "it0_prior_only"])
def test_b03_provenance_boundary_both_paths(case):
    pf, block, h1, h2, beliefs = _b_fixture()
    p1 = d5.marginalize_f_to_p1(pf)
    p2 = d5.conditionalize_f_to_p2(pf)
    tokens = {"check": CHECK, "missing": None, "none": None,
              "prior_only": PRIOR_ONLY, "unknown": "BOGUS",
              "it0_prior_only": PRIOR_ONLY}
    token = tokens[case]
    iterations = 0 if case == "it0_prior_only" else 1
    calls = []

    def _l1_result():
        out = _res(block["u1"], beliefs, provenance=token,
                   iterations=iterations)
        if case == "missing":
            out.pop("belief_provenance", None)
        elif case == "none":
            out["belief_provenance"] = None
        return out

    def fake(h, prior, syndrome, layer=None):
        if len(calls) > 0 and case != "check":
            raise AssertionError("L2 decoder must never be reached")
        calls.append(np.asarray(prior).copy())
        return _l1_result()

    if case == "check":
        out = d5._run_layered_block(fake, h1, h2, p1, p2, block, False)
        assert out["transfer_invoked"] is True
        assert len(calls) == 2
    else:
        with pytest.raises(RuntimeError) as exc:
            d5._run_layered_block(fake, h1, h2, p1, p2, block, False)
        assert type(exc.value).__name__ == "UnconditionedBeliefProvenanceError"
        assert len(calls) == 1  # fail closed before the L2 decoder
    # D7 path: identical refusal boundary
    if case == "check":
        assert d7e.require_check_updated(token) == CHECK
        eligible, reason = d7e.check_source_eligibility(
            status="ok", finite=True, belief_shape_ok=True, provenance=token)
        assert eligible is True and reason == "ELIGIBLE"
    else:
        with pytest.raises(RuntimeError) as exc:
            d7e.require_check_updated(token)
        assert "CHECK_UPDATED" in str(exc.value)
        # The D7-E scalar gate's refusal branch is already covered by the
        # accepted D7-E/F tests; here the run-level blocked non-invocation is
        # covered end-to-end by test_c_runner_blocked_transfer_recorded_not_invoked.


def test_b03_record_mode_blocks_transfer_without_consumption():
    pf, block, h1, h2, beliefs = _b_fixture()
    p1 = d5.marginalize_f_to_p1(pf)
    p2 = d5.conditionalize_f_to_p2(pf)
    seen = []

    def fake(h, prior, syndrome, layer=None):
        seen.append(np.asarray(prior).copy())
        return _res(block["u1"], beliefs, provenance=PRIOR_ONLY, iterations=0)

    out = d5._run_layered_block(fake, h1, h2, p1, p2, block, False,
                                on_blocked_transfer="record")
    assert out["transfer_invoked"] is False
    assert out["transfer_blocked_reason"] == "UnconditionedBeliefProvenanceError"
    assert out["app_l1_exact"] is True  # L1 truth happened; source exact
    assert out["app_exact"] is False
    assert len(seen) == 1
    with pytest.raises(ValueError):
        d5._run_layered_block(fake, h1, h2, p1, p2, block, False,
                              on_blocked_transfer="bogus")


def test_b04_first_mismatch_localizes_value_and_mapping():
    pf, block, h1, h2, beliefs = _b_fixture()
    q = d5.canonical_source_q(beliefs)
    left = d5.canonical_transfer_l2_prior(
        d5.conditionalize_f_to_p2(pf), block["bob"], q)
    right = left.copy()
    right[2, 5] += 1e-6
    mismatch = mod.first_mismatch("l2_transfer_prior", left, right)
    assert mismatch["reason"] == "value"
    assert mismatch["tensor"] == "l2_transfer_prior"
    assert mismatch["max_abs_diff"] > 0
    assert mismatch["flat_index"] == 2 * left.shape[1] + 5
    assert mod.first_mismatch("l2_transfer_prior", left, right,
                              atol=1e-3) is None
    assert mod.first_mismatch("q", np.zeros(3), np.ones(3))["reason"] == "value"
    assert mod.first_mismatch("q", np.zeros(3), np.ones(4))["reason"] == "shape"
    a = {"exact": True, "syndrome_ok": True, "iterations": 1}
    b = {"exact": True, "syndrome_ok": False, "iterations": 1}
    mapping = mod.first_mismatch("l1_counters", a, b)
    assert mapping["key"] == "syndrome_ok"
    assert mapping["left"] is True and mapping["right"] is False


# --------------------------------------------------------------------------
# B06: no-write decoder probe
# --------------------------------------------------------------------------
def test_b06_probe_accepts_check_updated_without_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = FakeDecoder(provenance=CHECK)
    report = d5.probe_historical_decoder_provenance(decode_fn=fake)
    assert report["accepted_check_updated"] is True
    assert report["provenance"] == CHECK
    assert report["resolved_is_historical"] is False
    assert report["belief_shape_ok"] is True
    assert report["created_output_root"] is False
    assert report["wrote_files"] is False
    assert list(tmp_path.rglob("*")) == []
    assert len(fake.calls) == 1


def test_b06_probe_refuses_missing_provenance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = FakeDecoder(provenance=None)
    report = d5.probe_historical_decoder_provenance(decode_fn=fake)
    assert report["accepted_check_updated"] is False
    assert report["provenance"] is None
    assert list(tmp_path.rglob("*")) == []


def test_b06_probe_never_resolves_historical_when_injected(monkeypatch):
    def _boom():
        raise AssertionError("historical decoder must not be resolved")

    monkeypatch.setattr(d5, "bind_historical_decoder", _boom)
    report = d5.probe_historical_decoder_provenance(
        decode_fn=FakeDecoder(provenance=CHECK))
    assert report["resolved_is_historical"] is False


# --------------------------------------------------------------------------
# C: statistics helpers
# --------------------------------------------------------------------------
def test_c_statistics_exact_and_wilson():
    assert mod.mcnemar_exact_two_sided(0, 0) == 1.0
    assert mod.mcnemar_exact_two_sided(2, 0) == 0.5
    assert abs(mod.mcnemar_exact_two_sided(3, 1) - 0.625) < 1e-15
    assert abs(mod.mcnemar_exact_two_sided(1, 3) - 0.625) < 1e-15
    lo, hi = mod.wilson_interval(0, 0)
    assert lo is None and hi is None
    lo, hi = mod.wilson_interval(5, 5)
    assert 0.0 <= lo < 1.0 and hi == 1.0
    lo, hi = mod.wilson_interval(5, 10)
    assert lo < 0.5 < hi


# --------------------------------------------------------------------------
# C: multi-graph runner
# --------------------------------------------------------------------------
def _c_context(seed=5, jb=4):
    rng = np.random.default_rng(seed)
    joint = rng.random((32, 32, jb)) + 1e-3
    joint = joint / joint.sum(axis=(0, 1), keepdims=True)
    blocks = {}
    for s in mod.BLOCK_SEEDS:
        r = np.random.default_rng(s)
        blocks[int(s)] = {"bob": r.integers(0, jb, size=64),
                          "u1": r.integers(0, 32, size=64),
                          "u2": r.integers(0, 32, size=64)}
    mothers = []
    for g in range(len(mod.GRAPH_PAIRS)):
        rg = np.random.default_rng(100 + g)
        mothers.append({"L1": rg.integers(0, 32, size=(64, 64)),
                        "L2": rg.integers(0, 32, size=(64, 64))})
    return joint, blocks, mothers


class _ScriptedFake:
    """Returns a pre-scripted x_hat per call; provenance CHECK_UPDATED."""

    def __init__(self, x_hats):
        self.x_hats = list(x_hats)
        self.n = 0

    def __call__(self, h, prior, syndrome, layer=None):
        x = self.x_hats[self.n]
        self.n += 1
        return {"x_hat": np.asarray(x, dtype=np.int64),
                "syndrome_ok": True,
                "iterations": 1,
                "final_beliefs": np.zeros_like(
                    np.asarray(prior, dtype=np.float64)),
                "belief_provenance": CHECK}


def _scripted_truth(blocks, graphs):
    x_hats = []
    for slot in mod.frozen_slots():
        block = blocks[int(slot["seed"])]
        truth = block["u1"] if slot["layer"] == "L1" else block["u2"]
        if slot["graph_idx"] in graphs:
            x_hats.append(np.asarray(truth).copy())
        else:
            x_hats.append(np.zeros_like(np.asarray(truth)))
    return x_hats


def _run_c(tmp_path, fake, name, monkeypatch=None):
    joint, blocks, mothers = _c_context()
    out_root = tmp_path / "workspace" / (mod.OUT_ROOT_PREFIX + name)
    result = mod.run_multigraph_diagnostic(
        out_root=str(out_root), authorized=True, joint=joint, blocks=blocks,
        mothers=mothers, decoder_fns={"SOURCE": fake, "TARGET": fake},
        repo_root=str(tmp_path), command_str="pytest fake run " + name)
    return result, out_root


def test_c_runner_no_sensitivity_all_fail(tmp_path):
    joint, blocks, mothers = _c_context()
    fake = _ScriptedFake([np.zeros(64, dtype=np.int64)
                          for _ in mod.frozen_slots()])
    result, out_root = _run_c(tmp_path, fake, "nosens")
    assert result["terminal"] == "NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE"
    assert result["decoder_calls"] == 384
    assert sorted(p.name for p in out_root.iterdir()) == sorted(
        mod.EVIDENCE_FILES)
    across = json.loads((out_root / "across_graph_summary.json").read_text(
        encoding="utf-8"))
    assert across["terminal"] == result["terminal"]
    assert across["scope"] == mod.SCOPE_TAG
    assert across["statistics_note"].startswith("descriptive only")
    prim = across["per_graph_primary"]
    assert len(prim) == 3
    for row in prim:
        assert row["neither"] == 16
        assert row["mcnemar_exact_p"] == 1.0
    with open(out_root / "call_records.csv", newline="",
              encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 384
    assert rows[0]["arm"] == "L1_MARGINAL"
    assert rows[1]["arm"] == "L1_TO_L2_TRANSFER"


def test_c_runner_graph_sensitivity_observed(tmp_path):
    joint, blocks, mothers = _c_context()
    fake = _ScriptedFake(_scripted_truth(blocks, graphs={1}))
    result, out_root = _run_c(tmp_path, fake, "sens")
    assert result["terminal"] == "GRAPH_SENSITIVITY_OBSERVED"
    across = json.loads((out_root / "across_graph_summary.json").read_text(
        encoding="utf-8"))
    prim = {row["graph_idx"]: row for row in across["per_graph_primary"]}
    assert prim[1]["both"] == 16
    assert prim[1]["neither"] == 0
    assert prim[0]["neither"] == 16
    assert prim[2]["neither"] == 16
    report = (out_root / "report.md").read_text(encoding="utf-8")
    assert "GRAPH_SENSITIVITY_OBSERVED" in report
    manifest = json.loads((out_root / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["max_calls"] == 384
    assert manifest["arms"] == list(mod.ARM_IDS)
    assert manifest["no_overwrite"] is True
    assert (out_root / "command_log.txt").read_text(
        encoding="utf-8").startswith("command: pytest fake run sens")


def test_c_runner_refusals_and_no_production_bind(tmp_path, monkeypatch):
    joint, blocks, mothers = _c_context()
    out_root = tmp_path / "workspace" / (mod.OUT_ROOT_PREFIX + "gate")

    def _boom(*a, **k):
        raise AssertionError("production decoder bind must not be entered")

    monkeypatch.setattr(d7e, "bind_row_layered_decoders", _boom)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_multigraph_diagnostic(
            out_root=str(out_root), authorized=False, joint=joint,
            blocks=blocks, mothers=mothers,
            decoder_fns={"SOURCE": FakeDecoder(), "TARGET": FakeDecoder()},
            repo_root=str(tmp_path))
    assert not out_root.exists()
    fake = _ScriptedFake([np.zeros(64, dtype=np.int64)
                          for _ in mod.frozen_slots()])
    result = mod.run_multigraph_diagnostic(
        out_root=str(out_root), authorized=True, joint=joint, blocks=blocks,
        mothers=mothers, decoder_fns={"SOURCE": fake, "TARGET": fake},
        repo_root=str(tmp_path))
    assert result["terminal"] in mod.TERMINALS
    with pytest.raises(FileExistsError):
        mod.run_multigraph_diagnostic(
            out_root=str(out_root), authorized=True, joint=joint,
            blocks=blocks, mothers=mothers,
            decoder_fns={"SOURCE": fake, "TARGET": fake},
            repo_root=str(tmp_path))
    # bad root name refuses before any work
    with pytest.raises(ValueError):
        mod.run_multigraph_diagnostic(
            out_root=str(tmp_path / "workspace" / "not_prefixed"),
            authorized=True, joint=joint, blocks=blocks, mothers=mothers,
            decoder_fns={"SOURCE": fake, "TARGET": fake},
            repo_root=str(tmp_path))


def test_c_runner_never_loads_model_f_when_injected(tmp_path, monkeypatch):
    joint, blocks, mothers = _c_context()

    def _boom(*a, **k):
        raise AssertionError("Model-F loader must not be entered")

    monkeypatch.setattr(mod, "_default_model_f_loader", _boom)
    monkeypatch.setattr(d5, "_load_model_f_input_or_blocked", _boom)
    fake = _ScriptedFake([np.zeros(64, dtype=np.int64)
                          for _ in mod.frozen_slots()])
    result = mod.run_multigraph_diagnostic(
        out_root=str(tmp_path / "workspace" / (mod.OUT_ROOT_PREFIX + "nof")),
        authorized=True, joint=joint, blocks=blocks, mothers=mothers,
        decoder_fns={"SOURCE": fake, "TARGET": fake}, repo_root=str(tmp_path))
    assert result["decoder_calls"] == 384


def test_c_runner_blocked_transfer_recorded_not_invoked(tmp_path):
    joint, blocks, mothers = _c_context()

    class PriorOnlyFake(_ScriptedFake):
        def __call__(self, h, prior, syndrome, layer=None):
            out = super().__call__(h, prior, syndrome, layer=layer)
            out["belief_provenance"] = PRIOR_ONLY
            out["iterations"] = 0
            return out

    fake = PriorOnlyFake([np.zeros(64, dtype=np.int64)
                          for _ in mod.frozen_slots()])
    result, out_root = _run_c(tmp_path, fake, "blocked")
    with open(out_root / "call_records.csv", newline="",
              encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    transfer_rows = [r for r in rows if r["role"] == "TARGET"]
    assert len(transfer_rows) == 192
    assert all(r["invoked"] == "False" for r in transfer_rows)
    assert all(r["transfer_block_reason"] == d7e.BLOCK_PROVENANCE
               for r in transfer_rows)
    assert result["decoder_calls"] == 192
    across = json.loads((out_root / "across_graph_summary.json").read_text(
        encoding="utf-8"))
    assert across["terminal"] == "INCONCLUSIVE"
    assert all(row["provenance_blocked_count"] == 16
               for row in across["per_graph_primary"])


def test_c_runner_resource_stop_is_engineering_blocked(tmp_path):
    joint, blocks, mothers = _c_context()
    fake = _ScriptedFake([np.zeros(64, dtype=np.int64)
                          for _ in mod.frozen_slots()])
    out_root = tmp_path / "workspace" / (mod.OUT_ROOT_PREFIX + "res")
    result = mod.run_multigraph_diagnostic(
        out_root=str(out_root), authorized=True, joint=joint, blocks=blocks,
        mothers=mothers, decoder_fns={"SOURCE": fake, "TARGET": fake},
        repo_root=str(tmp_path), wall_budget_s=-1.0)
    assert result["terminal"] == "MULTIGRAPH_ENGINEERING_BLOCKED"
    assert result["stop_reason"] == "WALL_BUDGET_EXHAUSTED"
    assert result["decoder_calls"] == 0


# --------------------------------------------------------------------------
# D: reference ladder
# --------------------------------------------------------------------------
def test_d_exact_enumeration_matches_independent_bruteforce():
    h = np.array([[1, 1]], dtype=np.int64)
    uniform = np.full((2, 32), 1.0 / 32)
    scores = mod.exact_posterior_scores(h, uniform, np.zeros(1),
                                        [np.array([3, 3]), np.array([0, 1])])
    assert scores[(3, 3)]["syndrome_consistent"] is True
    assert abs(scores[(3, 3)]["posterior"] - 1.0 / 32.0) < 1e-15
    assert scores[(0, 1)]["syndrome_consistent"] is False
    assert scores[(0, 1)]["posterior"] == 0.0
    # independent brute force over all 1024 states; GF(32) addition is XOR
    valid_mass = 0.0
    valid_states = 0
    for x1 in range(32):
        for x2 in range(32):
            if (x1 ^ x2) == 0:
                valid_mass += uniform[0, x1] * uniform[1, x2]
                valid_states += 1
    assert valid_states == 32
    assert abs(valid_mass - 1.0 / 32.0) < 1e-15
    # concentrated prior: (5, 5) is syndrome-consistent and rank 1
    prior = np.full((2, 32), 0.1 / 31)
    prior[0, 5] = 0.9
    prior[1, 5] = 0.9
    prior /= prior.sum(axis=1, keepdims=True)
    scores = mod.exact_posterior_scores(h, prior, np.zeros(1),
                                        [np.array([5, 5]),
                                         np.array([0, 0])])
    assert scores[(5, 5)]["rank"] == 1
    assert scores[(0, 0)]["rank"] > 1
    assert (scores[(5, 5)]["posterior"]
            > scores[(0, 0)]["posterior"])
    with pytest.raises(ValueError):
        mod.exact_posterior_scores(h, prior, np.zeros(1),
                                   [np.array([5, 5])], max_states=16)


def test_d_residual_syndrome_weight():
    h = np.array([[1, 0], [0, 1]], dtype=np.int64)
    x_true = np.array([4, 7], dtype=np.int64)
    syndrome = d5._gf32_syndrome(h, x_true)
    assert mod.residual_syndrome_weight(h, x_true, syndrome) == 0
    bad = np.array([5, 7], dtype=np.int64)
    assert mod.residual_syndrome_weight(h, bad, syndrome) == 1
    worse = np.array([5, 6], dtype=np.int64)
    assert mod.residual_syndrome_weight(h, worse, syndrome) == 2


def test_d_ladder_arms_and_changed_outcome():
    h = np.array([[1, 1], [1, 2]], dtype=np.int64)
    prior = np.full((2, 32), 1.0 / 32)
    x_true = np.zeros(2, dtype=np.int64)
    syndrome = d5._gf32_syndrome(h, x_true)
    zeros = _res(x_true, prior)
    ones = _res(np.ones(2, dtype=np.int64), prior)
    fakes = {"ROW_LAYERED_90": lambda hh, p, s: ones,
             "ROW_LAYERED_360": lambda hh, p, s: zeros,
             "FLOODING_90": lambda hh, p, s: ones}
    out = mod.run_reference_ladder(h=h, prior=prior, syndrome=syndrome,
                                   x_true=x_true, decoder_fns=fakes,
                                   f=1.2, seed=mod.BLOCK_SEEDS[0],
                                   authorized=True)
    arms = out["arms"]
    assert [a["arm_id"] for a in arms] == list(mod.LADDER_ARM_IDS)
    assert arms[0]["exact"] is False and arms[0]["changed_vs_current"] is False
    assert arms[1]["exact"] is True and arms[1]["changed_vs_current"] is True
    assert arms[1]["max_iter"] == 360
    assert arms[2]["exact"] is False and arms[2]["changed_vs_current"] is False
    for arm in arms:
        assert arm["scope_label"] == "STRONG_REFERENCE_DIAGNOSTIC"
        assert arm["posterior_score_computable"] is True
        assert arm["posterior_scores"][(0, 0)]["rank"] == 1


def test_d_ladder_scope_and_authorization():
    h = np.array([[1, 1]], dtype=np.int64)
    prior = np.full((2, 32), 1.0 / 32)
    x_true = np.zeros(2, dtype=np.int64)
    syndrome = d5._gf32_syndrome(h, x_true)
    fakes = {"ROW_LAYERED_90": lambda hh, p, s: _res(x_true, prior),
             "ROW_LAYERED_360": lambda hh, p, s: _res(x_true, prior),
             "FLOODING_90": lambda hh, p, s: _res(x_true, prior)}
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_reference_ladder(h=h, prior=prior, syndrome=syndrome,
                                 x_true=x_true, decoder_fns=fakes,
                                 authorized=False)
    with pytest.raises(ValueError):
        mod.run_reference_ladder(h=h, prior=prior, syndrome=syndrome,
                                 x_true=x_true, decoder_fns=fakes,
                                 f=1.0, authorized=True)
    with pytest.raises(ValueError):
        mod.run_reference_ladder(h=h, prior=prior, syndrome=syndrome,
                                 x_true=x_true, decoder_fns=fakes,
                                 seed=1, authorized=True)


# --------------------------------------------------------------------------
# E: G2 readiness
# --------------------------------------------------------------------------
def test_e_g2_frozen_matrix_matches_accepted_plan():
    assert d5.G2_WIDTH == 256
    assert d5.G2_F == (1.0, 1.1, 1.2)
    assert d5.G2_BLOCKS == 200 and d5.G2_ORACLE_SUBSET == 40
    assert tuple(d5.G2_SEEDS) == tuple(range(2026091000, 2026091200))
    assert (d5.L1_GRAPH_SEED, d5.L2_GRAPH_SEED) == (2026090501, 2026090502)
    assert d5.G2_L1_K_MIN == 235 and d5.G2_L2_K_MIN == 206
    assert d5.G2_TOTAL_BUDGET_S == 3600.0
    for f, m1, m2 in ((1.0, 196, 172), (1.1, 215, 189), (1.2, 235, 206)):
        assert d5._rows_required(d5.CE_L1_MEAN, 256, f) == m1
        assert d5._rows_required(d5.CE_L2_ORACLE_MEAN, 256, f) == m2
    assert d5._grade_g2(0.95, True, 0) == "G2_SYNTHETIC_QUALIFIED"
    assert d5._grade_g2(0.70, True, 0) == "G2_INCONCLUSIVE"
    assert d5._grade_g2(0.20, True, 0) == "G2_CURRENT_CONFIGURATION_FAILED"
    assert d5._grade_g2(0.95, True, 1) == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
    assert d5._grade_g2(
        0.95, True, 0,
        wall_seconds=d5.G2_TOTAL_BUDGET_S + 1.0
    ) == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
    assert d5._grade_g2(
        0.95, True, 0, peak_rss_bytes=2 * 1024**3
    ) == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
    assert d5._grade_g2(0.95, True, 0, wall_seconds=10.0,
                        peak_rss_bytes=1000) == "G2_SYNTHETIC_QUALIFIED"


def test_e_g2_fake_run_counts_budget_and_per_layer_metrics():
    p_b, p_f = _tiny_tables()
    h = _wide_h()
    res = d5.run_g2_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    assert res["decoder_calls"] == 1320
    assert [item["f"] for item in res["per_f"]] == [1.0, 1.1, 1.2]
    assert res["grade"] == "G2_CURRENT_CONFIGURATION_FAILED"
    assert res["runtime_status"] == "G2_RUNTIME_UNVERIFIED"
    assert res["wall_seconds"] >= 0.0
    assert res["peak_rss_bytes"] is not None
    for item in res["per_f"]:
        assert item["attempted"] == 200
        assert item["transfer_invoked_count"] == 200
        assert item["transfer_blocked_count"] == 0
        assert item["provenance_check_updated_count"] == 200
        assert "app_l1_exact_count" in item and "app_l2_exact_count" in item
        assert "app_l1_syndrome_ok_count" in item
        assert "app_l2_syndrome_ok_count" in item


def test_e_g2_rss_unavailable_blocks_the_grade(monkeypatch):
    p_b, p_f = _tiny_tables()
    monkeypatch.setattr(d5, "_rss_bytes", lambda: None)
    res = d5.run_g2_phase(h=_wide_h(), p_b=p_b, p_f=p_f,
                          decode_fn=FakeDecoder(), authorized=True)
    assert res["grade"] == "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
    assert res["peak_rss_bytes"] is None


def test_e_g2_additive_evidence_and_no_overwrite(tmp_path):
    p_b, p_f = _tiny_tables()
    res = d5.run_g2_phase(h=_wide_h(), p_b=p_b, p_f=p_f,
                          decode_fn=FakeDecoder(), authorized=True)
    out = tmp_path / "g2"
    assert d5.write_g2_evidence(out, res) == list(d5.STAGE_EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        d5.write_g2_evidence(out, res)
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    for key in ("phase", "formal_root", "block_length", "f_list",
                "frozen_rows", "seeds", "per_f", "monotonic", "crashes",
                "nonfinite", "decoder_calls", "grade", "passed",
                "output_files"):
        assert key in payload, key
    assert payload["wall_seconds"] >= 0.0
    assert payload["runtime_status"] == "G2_RUNTIME_UNVERIFIED"
    assert payload["frozen_rows"]["1.2"] == {"m1": 235, "m2": 206}
    for item in payload["per_f"]:
        assert "app_l1_exact_count" in item
        assert "transfer_invoked_count" in item
    header = (out / "table.csv").read_text(
        encoding="utf-8").splitlines()[0]
    assert header.startswith(
        "f,attempted,app_exact_count,app_exact_rate,"
        "app_failure_fraction,oracle_exact_count")
    assert "app_l1_exact_count" in header


def test_e_g1_additive_schema_and_blocked_counts(tmp_path):
    p_b, p_f = _tiny_tables()
    h = _wide_h()
    res = d5.run_g1_phase(h=h, p_b=p_b, p_f=p_f, decode_fn=FakeDecoder(),
                          authorized=True)
    assert res["decoder_calls"] == 440
    for item in res["per_f"]:
        assert item["attempted"] == 100
        assert item["transfer_invoked_count"] == 100
        assert item["transfer_blocked_count"] == 0
        assert item["provenance_check_updated_count"] == 100
        assert item["app_l1_exact_count"] >= item["app_exact_count"]
        assert item["app_l2_exact_count"] >= item["app_exact_count"]
    out = tmp_path / "g1"
    assert d5.write_g1_evidence(out, res) == list(d5.STAGE_EVIDENCE_FILES)
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    for item in payload["per_f"]:
        for key in ("app_l2_exact_count", "app_l1_syndrome_ok_count",
                    "app_l2_syndrome_ok_count", "app_l1_iterations_total",
                    "app_l2_iterations_total",
                    "provenance_check_updated_count",
                    "transfer_invoked_count", "transfer_blocked_count"):
            assert key in item, key
    header = (out / "table.csv").read_text(
        encoding="utf-8").splitlines()[0]
    assert header.startswith(
        "f,attempted,app_exact_count,app_exact_rate,"
        "app_failure_fraction,oracle_exact_count,app_syndrome_ok_count,"
        "app_iterations_total,app_iterations_max,oracle_syndrome_ok_count,"
        "oracle_iterations_total,nonfinite_count,peak_rss_bytes")
    assert header.endswith("transfer_invoked_count,transfer_blocked_count")
    # provenance-blocked phase run counts blocked transfers, skips L2+oracle
    blocked = d5.run_g1_phase(h=h, p_b=p_b, p_f=p_f,
                              decode_fn=FakeDecoder(provenance=PRIOR_ONLY,
                                                    iterations=0),
                              authorized=True)
    assert blocked["decoder_calls"] == 200
    assert blocked["per_f"][0]["transfer_blocked_count"] == 100
    assert blocked["per_f"][0]["transfer_invoked_count"] == 0
    assert blocked["per_f"][0]["app_exact_count"] == 0


def test_e_g2_unauthorized_never_calls_decoder(tmp_path, monkeypatch):
    p_b, p_f = _tiny_tables()
    called = []

    def _boom(*a, **k):
        called.append("decoder")
        raise AssertionError("decoder must not be called")

    with pytest.raises(d5.NotAuthorizedError):
        d5.run_g2_phase(h=_wide_h(), p_b=p_b, p_f=p_f,
                        decode_fn=_boom, authorized=False)
    with pytest.raises(d5.NotAuthorizedError):
        d5.run_g2_synthetic(authorized=False)
    assert called == []


# --------------------------------------------------------------------------
# CLI: dry-run and authorization gating
# --------------------------------------------------------------------------
CLI_PATH = ROOT / "scripts" / "v72p2d7_consistency_multigraph.py"
_CSPEC = importlib.util.spec_from_file_location(  # noqa: E402
    "d7_r1_consistency_multigraph_cli", str(CLI_PATH))
assert _CSPEC is not None and _CSPEC.loader is not None
cli = importlib.util.module_from_spec(_CSPEC)
_CSPEC.loader.exec_module(cli)


def test_cli_dry_run_prints_frozen_matrix(capsys):
    assert cli.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "slots=384 max_calls=384" in out
    assert "graph_pairs=" in out
    assert "f=" in out


def test_cli_refuses_unauthorized_without_creating_root(tmp_path, capsys):
    out_root = tmp_path / "workspace" / (mod.OUT_ROOT_PREFIX + "cli")
    rc = cli.main(["--out-root", str(out_root),
                   "--model-f-root", mod.MODEL_F_ROOT])
    assert rc == 3
    assert not out_root.exists()
    assert "not authorized" in capsys.readouterr().out


def test_cli_consistency_refuses_unauthorized(capsys):
    assert cli.main(["--consistency"]) == 3
    assert "not authorized" in capsys.readouterr().out


def test_cli_missing_out_root_refuses(capsys):
    assert cli.main([]) == 3
    assert "missing --out-root" in capsys.readouterr().out
