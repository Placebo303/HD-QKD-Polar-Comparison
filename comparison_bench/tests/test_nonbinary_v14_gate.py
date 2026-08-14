"""V14 q=1024 efficiency-gate engineering tests T0/T1/T2/T3
(``formal-nonbinary-ldpc-v14-efficiency-gate``).

- **T0** compile/import + structural checks: frozen constants (smoothing lambda,
  PROFILES, MS, budgets) and proof that importing the v14 modules never loads
  the real characterization-frame loader at import time.
- **T1** channel model on synthetic frames: histogram normalization, smoothing
  floor (>= lam/q), fold normalization, QSC-limit (uniform-off-diagonal stays
  QSC), entropy monotonicity across fold degree, uniform entropy == log2(q).
- **T2** mechanism: QSC-mode `v14.run_mcde` is within 1e-12 of `v9.run_mcde`
  per-iteration entropy (same seed), and a tiny q=8 structured run finishes
  with finite entropies.
- **T3** fake gate lifecycle: monkeypatch the v14 mcde DE entry points with
  fakes, run the CLI gate action (`_test_only=True`) into a fresh
  ``workspace/nbldpc_v14_<uuid>/`` root, assert the gate-decision schema and
  gate_state computed from the fake inputs, assert strict byte replay works,
  and assert NO file appears under an official output root or the change
  evidence path.

All roots are fresh ``workspace/nbldpc_v14_<uuid>``; no real sidecar, no real
source loader, and no official output root is ever touched.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v14_channel as channel,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v14_mcde as mcde,
)


def _out(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v14_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / name


def _fake_frames(frames: int = 8, *, seed: int = 2026090202, corr: float = 0.6):
    rng = np.random.default_rng(seed)
    out = []
    for f in range(int(frames)):
        alice = rng.integers(0, 1024, size=256)
        bob = rng.integers(0, 1024, size=256)
        structured = rng.random(256) < corr
        diffs = rng.integers(0, 32, size=256) * structured
        bob = np.where(structured, alice ^ diffs, bob)
        out.append({"frame_id": f, "stratum": "d1024_bw200",
                    "role": "characterization", "alice": alice, "bob": bob})
    return out


def _qsc_1024(p: float) -> np.ndarray:
    w = np.full(1024, p / 1023.0)
    w[0] = 1.0 - p
    return w


def _folded_qsc_parameter(folded: np.ndarray, q_small: int) -> float:
    """Best-fit QSC parameter p' for a folded uniform-away-from-zero dist."""
    off = float(np.mean(folded[1:])) if q_small > 1 else 0.0
    return float((q_small - 1.0) * off)


# --------------------------------------------------------------------------- #
# T0
# --------------------------------------------------------------------------- #


def test_t0_modules_import_and_frozen_constants():
    assert channel.CHANNEL_MODEL_SCHEMA == "nbldpc_v14_channel_model_v1"
    assert channel.SMOOTHING_LAMBDA == 0.001
    assert len(mcde.PROFILES) == 3
    assert mcde.MS == [15, 16, 17, 18]
    assert {p["id"] for p in mcde.PROFILES} == {1, 2, 3}
    assert mcde.PROFILES[0]["lambda"] == {2: 0.25, 3: 0.30, 4: 0.45}
    assert mcde.PROFILES[1]["lambda"] == {2: 0.20, 3: 0.25, 5: 0.55}
    assert mcde.PROFILES[2]["lambda"] == {3: 0.3, 4: 0.7}
    # frozen stage-2 budget
    assert mcde.STAGE2_N_SAMPLES == 10000
    assert mcde.STAGE2_MAX_ITER == 150
    assert mcde.STAGE2_ENTROPY_TOL == 0.01
    assert mcde.STAGE2_STREAK == 20
    # frozen stage-0 budget
    assert mcde.STAGE0_Q == 4 and mcde.STAGE0_RATE == 0.75
    assert mcde.STAGE0_N_SAMPLES == 100000 and mcde.STAGE0_MAX_ITER == 150
    assert mcde.STAGE0_PUBLISHED == 0.069 and mcde.STAGE0_TOL == 0.012
    # doc schemas
    assert mcde.V14_GATE_DECISION_SCHEMA == "nbldpc_v14_gate_decision_v1"
    assert mcde.V14_GATE_MANIFEST_SCHEMA == "nbldpc_v14_gate_manifest_v1"


def test_t0_no_real_frame_loader_at_import_time():
    # The real source loader must not be imported at import time; it is lazy
    # only inside load_production_frames.
    assert "ldpc_v4_10db_source" not in sys.modules
    assert "nonbinary_v13_diagnostics" not in sys.modules
    source = Path(channel.__file__).read_text(encoding="utf8")
    top_level = [line for line in source.splitlines()
                 if line.lstrip().startswith("import")
                 and "nonbinary_v13_diagnostics" in line]
    assert top_level == []


def test_t0_production_loader_requires_authorization():
    with pytest.raises(ValueError):
        channel.load_production_frames()  # no production_authorized
    assert "ldpc_v4_10db_source" not in sys.modules


# --------------------------------------------------------------------------- #
# T1
# --------------------------------------------------------------------------- #


def test_t1_diff_histogram_normalizes():
    frames = _fake_frames(8, seed=99)
    w_emp = channel.build_diff_distribution(frames, q=channel.Q)
    assert w_emp.shape == (1024,)
    assert np.isclose(w_emp.sum(), 1.0, atol=1e-9)
    assert np.all(w_emp >= 0.0)


def test_t1_smoothing_floor_not_below_lam_over_q():
    frames = _fake_frames(8, seed=101)
    w_emp = channel.build_diff_distribution(frames, q=channel.Q)
    w_s = channel.smooth(w_emp, q=channel.Q)
    assert np.isclose(w_s.sum(), 1.0, atol=1e-6)
    assert np.all(w_s >= channel.SMOOTHING_LAMBDA / channel.Q - 1e-15)
    assert w_s.min() >= channel.SMOOTHING_LAMBDA / channel.Q


def test_t1_fold_normalized():
    w = np.full(1024, np.logspace(-2, 0, 1024))
    w /= w.sum()
    for m in (2, 3, 4):
        folded = channel.fold(w, m)
        assert folded.shape == (1 << m,)
        assert np.isclose(folded.sum(), 1.0, atol=1e-9)
        assert np.all(folded >= 0.0)


def test_t1_qsc_limit_fold_preserves_qsc():
    # Folding a QSC-1024 (uniform away from zero) stays a QSC.
    p = 0.2
    ws = _qsc_1024(p)
    for m in (2, 3, 4):
        folded = channel.fold(ws, m)
        q_small = 1 << m
        p_eff = _folded_qsc_parameter(folded, q_small)
        assert channel._validate_qsc_consistent(folded, q_small, p_eff)
    # off-diagonal mass is conserved: sum over all bins stays 1
    assert np.isclose(channel.fold(ws, 4).sum(), 1.0, atol=1e-12)


def test_t1_entropy_monotone_across_fold_degree():
    rng = np.random.default_rng(0)
    w = rng.random(1024) ** 3
    w /= w.sum()
    h2 = channel.entropy_bits(channel.fold(w, 2))
    h3 = channel.entropy_bits(channel.fold(w, 3))
    h4 = channel.entropy_bits(channel.fold(w, 4))
    assert h3 >= h2 - 1e-12
    assert h4 >= h3 - 1e-12


def test_t1_uniform_entropy_equals_log2q():
    uniform = np.full(1024, 1.0 / 1024.0)
    assert abs(channel.entropy_bits(uniform) - np.log2(1024)) < 1e-9


def test_t1_channel_model_doc_schema():
    frames = _fake_frames(8, seed=7)
    w_emp = channel.build_diff_distribution(frames, q=channel.Q)
    w_s = channel.smooth(w_emp)
    doc = channel.build_channel_model_doc(w_s, frames_used=len(frames))
    assert doc["schema"] == channel.CHANNEL_MODEL_SCHEMA
    assert doc["q"] == 1024
    assert doc["smoothing_lambda"] == pytest.approx(0.001)
    assert len(doc["w"]) == 1024
    assert doc["fit_source"] == "v13 characterization frames"
    assert doc["diagnostic_only"] is True
    assert [f["m_bits"] for f in doc["folding"]] == [2, 3, 4]
    assert np.isclose(sum(doc["folding"][0]["w_small"]), 1.0, atol=1e-6)


# --------------------------------------------------------------------------- #
# T2
# --------------------------------------------------------------------------- #


def _tiny_config(q=8, n_samples=100):
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v9_common as common,
    )
    lam = {2: 0.5, 3: 0.5}
    conc = common.concentrated_check_distribution(0.5, lam)
    rho = {int(k): float(v) for k, v in
           ((conc["dc_lo"], conc["w_lo"]), (conc["dc_hi"], conc["w_hi"])) if v > 0.0}
    return lam, rho


def test_t2_qsc_equivalence_with_v9():
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v9_mcde as v9,
    )
    q = 8
    p = 0.2
    lam, rho = _tiny_config(q=q)
    seed = 1234
    r9 = v9.run_mcde(q, lam, rho, p, n_samples=100, max_iter=3, seed=seed)
    r14 = mcde.run_mcde(q, lam, rho, channel_mode="qsc", p=p,
                        n_samples=100, max_iter=3, seed=seed)
    assert len(r9["entropy_trace"]) == len(r14["entropy_trace"])
    for e9, e14 in zip(r9["entropy_trace"], r14["entropy_trace"]):
        assert abs(e9 - e14) <= 1e-12
    assert r9["error_trace"] == pytest.approx(r14["error_trace"], abs=1e-12)


def test_t2_tiny_structured_run_finite():
    q = 8
    lam, rho = _tiny_config(q=q)
    # a structured prior concentrated at diff 0 (identical symbols) over GF(8)
    w = np.full(q, 0.05)
    w[0] = 0.65
    run = mcde.run_mcde(q, lam, rho, channel_mode="structured", w=w,
                        n_samples=100, max_iter=3, seed=7)
    assert all(np.isfinite(e) for e in run["entropy_trace"])
    assert np.isfinite(run["final_entropy"])
    assert run["channel_mode"] == "structured"


# --------------------------------------------------------------------------- #
# T3
# --------------------------------------------------------------------------- #


def _snapshot_tree(root: str) -> dict:
    root = Path(root)
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def test_t3_fake_gate_lifecycle_and_replay(monkeypatch):
    from comparison_bench.src.comparison_bench.cli import run_v14_gate as cli

    # Fake DE entry points injected into the mcde module the CLI reads from.
    def fake_threshold_binary_search(q, rate, lambda_edge, rho_edge, **kw):
        return {"threshold_proxy": 0.062, "grid_points": [0.01],
                "probes": [{"p": 0.099, "converged": True, "final_entropy": 0.0}],
                "converged_at_lo": True}

    def fake_run_mcde(q, lambda_edge, rho_edge, **kw):
        return {"converged": True, "iterations": 21,
                "entropy_trace": [0.0] * 21, "final_entropy": 0.0,
                "channel_mode": "structured"}

    monkeypatch.setattr(mcde, "threshold_binary_search", fake_threshold_binary_search)
    monkeypatch.setattr(mcde, "run_mcde", fake_run_mcde)

    out = _out("evidence")  # workspace/nbldpc_v14_<uuid>/evidence (fresh)

    # Production roots snapshot before (the specific roots the gate could write).
    output_root = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    openspec_evidence = Path("openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate")
    before_output = _snapshot_tree(str(output_root))
    before_openspec = _snapshot_tree(str(openspec_evidence))

    result = cli.run_gate(str(out), production_authorized=False, _test_only=True,
                          command="pytest T3")

    files = sorted(p.name for p in out.iterdir())
    assert "v14_gate_decision.json" in files
    assert "v14_gate_manifest.json" in files
    assert "v14_stage0_q4_qsc_regression.json" in files
    assert "v14_stage1_structured_smallq.json" in files
    assert "v14_stage2_q1024_threshold.json" in files
    assert "v14_structured_channel_model.json" in files

    decision = json.loads((out / "v14_gate_decision.json").read_text(encoding="utf8"))
    assert decision["schema"] == "nbldpc_v14_gate_decision_v1"
    # stage0 fake proxy 0.062 vs published 0.069: delta 0.007 <= 0.012
    assert decision["stage0_mechanism_verified"] is True
    # all 12 fake points converge and f_achieved <= 1.3
    assert decision["gate_state"] == "pass"
    assert decision["stage2_point_count"] == 12
    assert result["gate_state"] == "pass"

    manifest = json.loads((out / "v14_gate_manifest.json").read_text(encoding="utf8"))
    assert manifest["schema"] == "nbldpc_v14_gate_manifest_v1"
    assert manifest["command"] == "pytest T3"

    # Stage-0 doc schema
    stage0 = json.loads((out / "v14_stage0_q4_qsc_regression.json").read_text(encoding="utf8"))
    assert stage0["schema"] == "nbldpc_v14_stage0_v1"

    # Strict byte replay against a sibling replay dir.
    replay_root = out.parent / "replay"
    shutil.copytree(str(out), str(replay_root))
    report = cli.replay_evidence(str(out), str(replay_root))
    assert report["ok"] is True
    assert report["evidence_files"] == 6
    assert report["matched"] == 6
    assert report["mismatches"] == [] and report["missing_in_replay"] == []

    # Tamper: mutate one byte in the replay -> replay must fail byte-compare.
    target = replay_root / STAGE3_REPLAY_TARGET
    if target.exists():
        data = bytearray(target.read_bytes())
        data[0] ^= 0xFF
        target.write_bytes(bytes(data))
        report_fail = cli.replay_evidence(str(out), str(replay_root))
        assert report_fail["ok"] is False

    # No-overwrite is fail closed for the evidence files themselves.
    with pytest.raises(FileExistsError):
        cli._write_evidence(str(out / "v14_gate_decision.json"), decision)

    # Nothing was created under official output roots or the change evidence.
    assert _snapshot_tree(str(output_root)) == before_output
    assert _snapshot_tree(str(openspec_evidence)) == before_openspec


STAGE3_REPLAY_TARGET = "v14_structured_channel_model.json"
