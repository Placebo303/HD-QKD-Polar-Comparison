"""V18-B1 M0 smoke + M1 frozen-plan tests (no production execution)."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v18_b1_repro as core


def _root(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v18_{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_smoke_deterministic():
    root = _root("smoke")
    try:
        a = core.run_smoke(q=4, out_dir=root / "a")
        b = core.run_smoke(q=4, out_dir=root / "b")
        assert a["schema"] == core.SCHEMA
        assert a["result"]["best_lambda"] == b["result"]["best_lambda"]
        assert (root / "a" / "repro.json").exists()
        assert (root / "a" / "de_search" / "run_complete.json").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_production_plan_frozen():
    p = core.production_plan()
    assert p["schema"] == core.SCHEMA + "_plan_v1"
    assert p["mode"] == "production"
    assert p["q"] == 4
    assert p["rate"] == 0.75
    assert p["p_gate"] == 0.069
    assert p["det_published"] == 0.069
    assert p["tol"] == 0.012
    assert p["seed"] == 2026081602
    assert p["pop_size"] == 20 and p["max_gen"] == 29
    assert p["F"] == 0.5 and p["CR"] == 0.9
    assert p["n_samples"] == 100000 and p["max_iter"] == 150
    assert p["threshold_p_lo"] == 0.01
    assert p["threshold_p_hi"] == 0.12
    assert p["threshold_p_tol"] == 0.0025
    assert p["entropy_tol"] == 0.01 and p["streak"] == 20
    assert p["workers"] == 1
    # Seeds must stay disjoint from V8 reproduction and M0 smoke.
    assert core.PRODUCTION_SEED not in (20260816, 2026080418)


def test_evaluate_reproduction_gate():
    assert core.evaluate_reproduction({"threshold_proxy": 0.062421875})["verdict"] == "PASS"
    assert core.evaluate_reproduction({"threshold_proxy": 0.062421875})["delta"] == 0.062421875 - 0.069
    assert core.evaluate_reproduction({"threshold_proxy": 0.090})["verdict"] == "FAIL"
    assert core.evaluate_reproduction({"threshold_proxy": None}) == {
        "threshold_proxy": None, "det_published": 0.069, "tol": 0.012,
        "delta": None, "verdict": "NO_THRESHOLD"}


def test_production_refuses_existing_plan_file():
    # run_production must not overwrite a frozen plan; the guard fires before
    # any DE execution, so this stays CPU-free.
    root = _root("prod_guard")
    try:
        (root / "pre_run_plan.json").write_text(json.dumps({"sentinel": True}), encoding="utf-8")
        try:
            core.run_production(out_dir=root)
            raised = False
        except ValueError as e:
            raised = "pre_run_plan.json" in str(e)
        assert raised
        assert json.loads((root / "pre_run_plan.json").read_text(encoding="utf-8")) == {"sentinel": True}
        assert not (root / "repro.json").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
