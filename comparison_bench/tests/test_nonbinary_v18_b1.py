"""V18-B1 M0 smoke tests."""
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
