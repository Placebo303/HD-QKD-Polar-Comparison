"""V17 multibit structured feasibility-gate engineering tests T0/T1/T2
(``formal-nonbinary-ldpc-v17-multibit-structured-de-gate``).

- **T0** compile (``ast.parse``; ``__pycache__`` writes are denied in this
  environment, so ``py_compile`` is NOT used) + structural checks: frozen
  constants (schemas, budgets, candidates, point set) and proof that importing
  the v17 modules never loads the real V13 frame/source loader at import time.
- **T1** focused unit: bit-plane marginal derivation (q=4 degenerate 2p/3),
  Anchor A/B tolerance-comparison machinery, channel-model build + schema +
  total-leakage, structured-prior normalization, f computation, convergence
  detection (tiny q=2/q=4 runs), fail-closed / no-overwrite helper.
- **T2** complete fake lifecycle: tiny q=4 / tiny n_samples (200) full Stage
  0/1/2 + gate decision + strict byte replay in a fresh writable root
  ``workspace/nbldpc_v17_<uuid>/``, monkeypatched DE entry points; asserts the
  gate fails closed per file, the channel model is never overwritten, replay
  scientific files are byte-identical, and NO file appears under production
  roots or the change evidence path.

All roots are fresh ``workspace/nbldpc_v17_<uuid>``; no real sidecar, no real
source loader, and no official output root is ever touched.
"""
from __future__ import annotations

import ast
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v17_channel as channel,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v17_mcde as mcde,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v17_stage0 as stage0,
)


def _out(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v17_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / name


def _snapshot_tree(root: str) -> dict:
    root = Path(root)
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# T0 — compile / import + structural
# --------------------------------------------------------------------------- #

_MODULE_PATHS = [
    Path("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v17_stage0.py"),
    Path("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v17_channel.py"),
    Path("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v17_mcde.py"),
    Path("comparison_bench/src/comparison_bench/cli/run_v17_gate.py"),
    Path("comparison_bench/tests/test_nonbinary_v17_gate.py"),
]


def test_t0_compile_ast_parse():
    """All five files parse with ast.parse (no py_compile / pycache writes)."""
    for path in _MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))  # raises on syntax error
        assert isinstance(tree, ast.Module), str(path)


def test_t0_frozen_constants_and_schemas():
    assert channel.CHANNEL_MODEL_SCHEMA == "nbldpc_v17_multibit_channel_model_v1"
    assert channel.Q == 1024 and channel.BIT_PLANES == 10
    assert stage0.ANCHOR_A_Q == 4 and stage0.ANCHOR_A_BITS == 2
    assert stage0.ANCHOR_A_TOL == 0.005
    assert stage0.ANCHOR_A_RATE == 0.75
    assert stage0.ANCHOR_A_N_SAMPLES == 100000 and stage0.ANCHOR_A_MAX_ITER == 150
    assert stage0.STAGE0_PUBLISHED == 0.069 and stage0.STAGE0_TOL == 0.012
    assert mcde.MS == [15, 16, 17, 18]
    assert len(mcde.CANDIDATES) == 3
    assert [c["id"] for c in mcde.CANDIDATES] == ["bitplane", "edgelabel", "planeweight"]
    assert mcde.F_LIMIT == 1.3
    assert mcde.STAGE2_N_SAMPLES == 10000 and mcde.STAGE2_MAX_ITER == 150
    assert mcde.STAGE2_ENTROPY_TOL == 0.01 and mcde.STAGE2_STREAK == 20


def test_t0_no_production_loader_at_import_time():
    # The real V13 source / diagnostics loader must not be imported at import.
    import sys
    assert "ldpc_v4_10db_source" not in sys.modules
    assert "nonbinary_v13_diagnostics" not in sys.modules
    src = Path(channel.__file__).read_text(encoding="utf8")
    top_level = [line for line in src.splitlines()
                 if line.lstrip().startswith(("import", "from"))
                 and "nonbinary_v13_diagnostics" in line
                 and "ldpc_v4_10db_source" in line]
    assert top_level == []


def test_t0_production_loader_requires_authorization():
    with pytest.raises(ValueError):
        channel.load_production_mismatch_rates()  # no production_authorized


# --------------------------------------------------------------------------- #
# T1 — focused unit
# --------------------------------------------------------------------------- #

def test_t1_qsc_bitplane_marginals_q4_degenerate():
    # q=4 QSC(p) gray marginals are the degenerate 2p/3 on BOTH planes.
    p = 0.21
    marg = stage0.qsc_bitplane_marginals(4, p)
    assert marg.shape == (2,)
    assert np.allclose(marg, 2.0 * p / 3.0, atol=1e-12)


def test_t1_qsc_bitplane_marginals_zero():
    assert np.all(stage0.qsc_bitplane_marginals(4, 0.0) == 0.0)


def test_t1_anchor_a_doc_shape_and_gate():
    # The anchor-A machinery computes a symmetric delta and gates on <= tol.
    a = {"delta": 0.002, "mechanism_verified": True}
    doc = stage0.build_stage0_doc(
        anchor_a=a,
        anchor_b={"delta": 0.003, "mechanism_verified": True})
    assert doc["schema"] == "nbldpc_v17_stage0_v1"
    assert doc["both_anchors_verified"] is True
    assert doc["gate_state"] == "pass"
    # one anchor false -> fail (no boolean fallback)
    doc2 = stage0.build_stage0_doc(
        anchor_a=a, anchor_b={"delta": 0.05, "mechanism_verified": False})
    assert doc2["both_anchors_verified"] is False
    assert doc2["gate_state"] == "fail"


def test_t1_channel_model_build_and_schema():
    rates = [1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3, 5e-3, 2e-2, 3.75e-2]
    doc = channel.build_channel_model_doc(rates, frames_used=128, symbols_used=32768)
    assert doc["schema"] == channel.CHANNEL_MODEL_SCHEMA
    assert doc["q"] == 1024 and doc["bit_planes"] == 10
    assert doc["mapping"] == "gray"
    assert doc["joint_structure"] == channel.JOINT_INDEPENDENT
    assert len(doc["per_bit_plane_error_probability_msb_first"]) == 10
    assert doc["per_bit_plane_error_probability_msb_first"] == [float(x) for x in rates]
    assert doc["entropy_bits"] == pytest.approx(
        sum(channel.binary_entropy_bits(p) for p in rates), abs=1e-12)
    assert doc["diagnostic_only"] is True


def test_t1_channel_model_rejects_non_monotone():
    with pytest.raises(ValueError):
        channel.build_channel_model_doc([0.5, 0.1] + [0.05] * 8)


def test_t1_total_leakage_and_f():
    rates = [1e-4, 2e-4, 4e-4, 8e-4, 1.6e-3, 3.2e-3, 6.4e-3, 1.28e-2, 2.56e-2, 3.75e-2]
    H = channel.total_leakage_bits(rates)
    assert H > 0.0
    # f for m=15..18 must be decreasing in m is NOT guaranteed; but f formula
    # is monotone increasing in m.  Check the V17 f convention denominator.
    f15 = (15 * 10.0 / 256.0) / H
    f18 = (18 * 10.0 / 256.0) / H
    assert f18 > f15


def test_t1_structured_priors_normalize():
    rates = [1e-5, 1e-4, 1e-3, 1e-2, 2e-2, 3e-2, 4e-2, 5e-2, 6e-2, 7e-2]
    w1 = mcde.bitplane_prior(rates)
    w2 = mcde.planeweight_prior(rates)
    assert w1.shape == (1024,)
    assert w2.shape == (1024,)
    assert np.isclose(w1.sum(), 1.0, atol=1e-9)
    assert np.isclose(w2.sum(), 1.0, atol=1e-9)
    assert np.all(np.isfinite(w1)) and np.all(w1 >= 0.0)
    assert np.all(np.isfinite(w2)) and np.all(w2 >= 0.0)
    # Distinct priors (the weighting is a genuine, frozen difference).
    assert not np.allclose(w1, w2, atol=1e-6)


def _struct_rho(rate: float, lam: dict) -> dict:
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v9_common as common
    conc = common.concentrated_check_distribution(rate, lam)
    return {int(k): float(v) for k, v in
            ((conc["dc_lo"], conc["w_lo"]), (conc["dc_hi"], conc["w_hi"])) if float(v) > 0.0}


def test_t1_convergence_detection_tiny_q():
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v14_mcde as v14
    # q=2, tiny n_samples, high crossover -> should NOT converge;
    # very low crossover -> should converge within max_iter.
    lam = {2: 0.5, 3: 0.5}
    rho = _struct_rho(0.5, lam)
    hi = v14.run_mcde(2, lam, rho, channel_mode="qsc", p=0.4,
                      n_samples=200, max_iter=50, seed=1)
    lo = v14.run_mcde(2, lam, rho, channel_mode="qsc", p=0.01,
                      n_samples=200, max_iter=50, seed=1)
    assert not hi["converged"]
    assert lo["converged"]


def test_t1_fail_closed_write_evidence():
    from comparison_bench.src.comparison_bench.cli import run_v17_gate as cli
    out = _out("evidence")
    out.mkdir(parents=True, exist_ok=True)
    target = out / "probe.json"
    cli._write_evidence(str(target), {"x": 1})
    with pytest.raises(FileExistsError):
        cli._write_evidence(str(target), {"x": 2})


# --------------------------------------------------------------------------- #
# T2 — complete fake lifecycle (tiny q / tiny n_samples)
# --------------------------------------------------------------------------- #

def test_t2_fake_gate_lifecycle_and_replay(monkeypatch):
    from comparison_bench.src.comparison_bench.cli import run_v17_gate as cli
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v14_mcde as v14

    # Fake the DE entry points the gate reads from, so T2 is tiny + independent
    # of the production thresholds.
    def fake_threshold_binary_search(q, rate, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.068, "grid_points": [0.01],
                "probes": [{"p": 0.099, "converged": True, "final_entropy": 0.0}],
                "converged_at_lo": True}

    def fake_run_mcde(q, lambda_edge, rho_edge, **kw):
        return {"converged": True, "iterations": 21,
                "entropy_trace": [0.0] * 21, "final_entropy": 0.0,
                "error_trace": [0.0] * 21,
                "channel_mode": kw.get("channel_mode", "qsc")}

    def fake_bitplane_threshold(q, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.066, "grid_points": [0.005],
                "probes": [{"p": 0.005, "joint_converged": True, "planes": []}],
                "n_planes": 2, "converged_at_lo": True}

    monkeypatch.setattr(stage0, "threshold_binary_search", fake_threshold_binary_search)
    monkeypatch.setattr(stage0, "bitplane_decomposed_threshold", fake_bitplane_threshold)
    monkeypatch.setattr(mcde, "run_mcde", fake_run_mcde)

    out = _out("evidence")
    out.mkdir(parents=True, exist_ok=True)

    output_root = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    openspec_evidence = Path(
        "openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate")
    before_output = _snapshot_tree(str(output_root))
    before_openspec = _snapshot_tree(str(openspec_evidence))

    result = cli.run_gate(str(out), production_authorized=False, _test_only=True,
                          n_samples=200, max_iter=30, command="pytest T2")

    files = sorted(p.name for p in out.iterdir())
    assert "v17_gate_decision.json" in files
    assert "v17_gate_manifest.json" in files
    assert "v17_stage0.json" in files
    assert "v17_stage2.json" in files
    assert "v17_multibit_channel_model.json" in files
    assert len(files) == 5

    decision = json.loads((out / "v17_gate_decision.json").read_text(encoding="utf8"))
    assert decision["schema"] == "nbldpc_v17_gate_decision_v1"
    assert decision["stage0_mechanism_verified"] is True
    assert decision["stage1_model_built"] is True
    assert decision["stage2_point_count"] == 3 * 4  # 3 candidates x 4 m
    assert decision["gate_state"] == "pass"
    assert result["gate_state"] == "pass"

    stage0_doc = json.loads((out / "v17_stage0.json").read_text(encoding="utf8"))
    assert stage0_doc["schema"] == "nbldpc_v17_stage0_v1"

    stage2_doc = json.loads((out / "v17_stage2.json").read_text(encoding="utf8"))
    assert stage2_doc["schema"] == "nbldpc_v17_stage2_v1"
    assert [c["candidate"] for c in stage2_doc["candidates"]] == \
        ["bitplane", "edgelabel", "planeweight"]
    for cand in stage2_doc["candidates"]:
        assert [p["m"] for p in cand["points"]] == [15, 16, 17, 18]

    model_doc = json.loads((out / "v17_multibit_channel_model.json").read_text(encoding="utf8"))
    assert model_doc["schema"] == channel.CHANNEL_MODEL_SCHEMA

    manifest = json.loads((out / "v17_gate_manifest.json").read_text(encoding="utf8"))
    assert manifest["schema"] == "nbldpc_v17_gate_manifest_v1"
    assert manifest["command"] == "pytest T2"

    # Strict byte replay against a sibling replay dir.
    replay_root = out.parent / "replay"
    shutil.copytree(str(out), str(replay_root))
    report = cli.replay_evidence(str(out), str(replay_root))
    assert report["ok"] is True
    assert report["evidence_files"] == 5
    assert report["matched"] == 5
    assert report["mismatches"] == [] and report["missing_in_replay"] == []

    # Tamper one byte -> replay fails.
    target = replay_root / "v17_stage0.json"
    data = bytearray(target.read_bytes())
    data[0] ^= 0xFF
    target.write_bytes(bytes(data))
    assert cli.replay_evidence(str(out), str(replay_root))["ok"] is False

    # No production output written.
    assert _snapshot_tree(str(output_root)) == before_output
    assert _snapshot_tree(str(openspec_evidence)) == before_openspec


def test_t2_gate_fails_closed_per_file(monkeypatch):
    from comparison_bench.src.comparison_bench.cli import run_v17_gate as cli
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v14_mcde as v14

    def fake_threshold_binary_search(q, rate, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.068, "grid_points": [0.01],
                "probes": [{"p": 0.099, "converged": True, "final_entropy": 0.0}],
                "converged_at_lo": True}

    def fake_bitplane_threshold(q, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.066, "grid_points": [0.005],
                "probes": [{"p": 0.005, "joint_converged": True, "planes": []}],
                "n_planes": 2, "converged_at_lo": True}

    def fake_run_mcde(q, lambda_edge, rho_edge, **kw):
        return {"converged": True, "iterations": 21, "entropy_trace": [0.0] * 21,
                "final_entropy": 0.0, "error_trace": [0.0] * 21,
                "channel_mode": kw.get("channel_mode", "qsc")}

    monkeypatch.setattr(stage0, "threshold_binary_search", fake_threshold_binary_search)
    monkeypatch.setattr(stage0, "bitplane_decomposed_threshold", fake_bitplane_threshold)
    monkeypatch.setattr(mcde, "run_mcde", fake_run_mcde)

    out = _out("evidence")
    out.mkdir(parents=True, exist_ok=True)
    # Pre-existing gate own-output -> fail closed before any write.
    (out / "v17_gate_decision.json").write_text(json.dumps({"stub": True}), encoding="utf8")
    with pytest.raises(FileExistsError):
        cli.run_gate(str(out), production_authorized=False, _test_only=True,
                     n_samples=200, max_iter=30, command="pytest T2 exists")
    assert not (out / "v17_stage0.json").exists()
    assert not (out / "v17_stage2.json").exists()
    assert not (out / "v17_multibit_channel_model.json").exists()


def test_t2_model_file_never_overwritten(monkeypatch):
    from comparison_bench.src.comparison_bench.cli import run_v17_gate as cli
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v14_mcde as v14

    def fake_threshold_binary_search(q, rate, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.068, "grid_points": [0.01],
                "probes": [{"p": 0.099, "converged": True, "final_entropy": 0.0}],
                "converged_at_lo": True}

    def fake_bitplane_threshold(q, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.066, "grid_points": [0.005],
                "probes": [{"p": 0.005, "joint_converged": True, "planes": []}],
                "n_planes": 2, "converged_at_lo": True}

    def fake_run_mcde(q, lambda_edge, rho_edge, **kw):
        return {"converged": True, "iterations": 21, "entropy_trace": [0.0] * 21,
                "final_entropy": 0.0, "error_trace": [0.0] * 21,
                "channel_mode": kw.get("channel_mode", "qsc")}

    monkeypatch.setattr(stage0, "threshold_binary_search", fake_threshold_binary_search)
    monkeypatch.setattr(stage0, "bitplane_decomposed_threshold", fake_bitplane_threshold)
    monkeypatch.setattr(mcde, "run_mcde", fake_run_mcde)

    out = _out("evidence")
    out.mkdir(parents=True, exist_ok=True)
    # Pre-existing channel model (same evidence set) must be READ, never rewritten.
    rates = channel.synthetic_mismatch_rates(seed=1)
    model_doc = channel.build_channel_model_doc(rates, frames_used=None, symbols_used=None)
    model_path = out / cli.CHANNEL_MODEL_FILE
    model_path.write_text(json.dumps(model_doc, indent=2, sort_keys=True), encoding="utf8")
    model_before = model_path.read_bytes()

    cli.run_gate(str(out), production_authorized=False, _test_only=True,
                 n_samples=200, max_iter=30, command="pytest T2 model")
    assert model_path.read_bytes() == model_before


def test_t2_invalid_model_fails_closed():
    from comparison_bench.src.comparison_bench.cli import run_v17_gate as cli
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v14_mcde as v14

    out = _out("evidence")
    out.mkdir(parents=True, exist_ok=True)
    # A stage2 action against a bad model (wrong schema) fails closed.
    (out / cli.CHANNEL_MODEL_FILE).write_text(
        json.dumps({"schema": "wrong", "per_bit_plane_error_probability_msb_first": []}),
        encoding="utf8")
    # stage2 reads the model and reads its rates; a wrong schema yields a
    # missing rates key -> the rates read fails.
    with pytest.raises(Exception):
        cli.run_stage2_action(str(out), production_authorized=False, _test_only=True)
