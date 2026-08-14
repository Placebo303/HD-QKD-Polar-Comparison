from __future__ import annotations

import argparse
import time
from pathlib import Path

from ..config import load_config
from ..sweep.runtime import write_manifest
from ..utils.paths import default_output_dir, repo_root
from .make_report_tables import main as make_report_tables_main
from .run_cascade_param_sweep import main as run_cascade_main
from .run_layered_ldpc_param_sweep import main as run_layered_main
from .run_qldpc_param_sweep import main as run_qldpc_main


def _out_dir(cfg: dict) -> Path:
    out = Path((cfg.get("global", {}) or {}).get("output_dir") or default_output_dir())
    if not out.is_absolute():
        out = repo_root() / out
    out.mkdir(parents=True, exist_ok=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Run IR benchmark v3 master workflow.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    start = time.perf_counter()
    cfg = load_config(Path(args.config))
    out_dir = _out_dir(cfg)
    completed: list[str] = []
    failed: list[str] = []
    stages = [
        ("cascade_param_sweep", run_cascade_main, cfg.get("cascade_config")),
        ("layered_ldpc_param_sweep", run_layered_main, cfg.get("layered_ldpc_config")),
        ("qldpc_param_sweep", run_qldpc_main, cfg.get("qldpc_config")),
        ("report_tables_v3", make_report_tables_main, args.config),
    ]
    import sys
    old_argv = sys.argv[:]
    try:
        for stage_name, fn, stage_cfg in stages:
            try:
                sys.argv = [old_argv[0], "--config", str(stage_cfg)]
                fn()
                completed.append(stage_name)
            except Exception:
                failed.append(stage_name)
    finally:
        sys.argv = old_argv

    write_manifest(
        out_dir / "ir_v3_run_manifest.json",
        config=cfg,
        completed_stages=completed,
        failed_stages=failed,
        output_files={name: str(stage_cfg) for name, _, stage_cfg in stages},
        runtime_total_s=time.perf_counter() - start,
        notes="master runner partial completion is acceptable; failed stages logged separately",
    )
    print(f"ir_v3 master complete: completed={completed} failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
