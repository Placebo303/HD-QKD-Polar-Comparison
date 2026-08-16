"""V18-B2 M2 prep tests (no production run)."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v18_b2_structured_de as core


def test_m2_plan_schema():
    plan = core.build_m2_plan()
    assert plan["schema"] == core.SCHEMA
    assert plan["gate_dependency"] == "V18-B1 M1 reproduction PASS"


def test_m2_plan_written():
    root = Path("workspace") / f"nbldpc_v18_b2_{uuid.uuid4().hex}"
    try:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "comparison_bench.src.comparison_bench.cli.run_v18_b2_structured_de",
                        "--out-dir", str(root)], check=True, cwd=Path.cwd())
        assert (root / "m2_plan.json").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_m2_smoke_runs():
    root = Path("workspace") / f"nbldpc_v18_b2_smoke_{uuid.uuid4().hex}"
    try:
        doc = core.run_smoke(q=8, out_dir=root, n_samples=200, max_iter=3)
        assert doc["schema"] == "nbldpc_v18_b2_structured_de_smoke_v1"
        assert (root / "smoke.json").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_m2_search_smoke_runs():
    root = Path("workspace") / f"nbldpc_v18_b2_search_{uuid.uuid4().hex}"
    try:
        doc = core.run_search_smoke(q=8, out_dir=root, n_samples=100, max_iter=3,
                                    pop_size=4, max_gen=1)
        assert doc["schema"] == "nbldpc_v18_b2_structured_de_search_v1"
        assert (root / "search_result.json").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_real_folded_w():
    import numpy as np
    w = core.build_folded_w(16)
    assert w.shape == (16,)
    assert abs(float(w.sum()) - 1.0) < 1e-9
    assert np.all(w >= 0.0)
