#!/usr/bin/env python3
"""V72P2D2 CLI boundary and synthetic layered-kernel cost preflight.

The default command is deliberately limited to the accepted synthetic
preflight.  The future real L/I/P invocation has a separate, explicit CLI
mode and a fail-closed cycle-state gate.  No input-data or production-output
path is touched by the default path.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "comparison_bench"
    / "src"
    / "comparison_bench"
    / "formal_ir"
    / "v72p2d2_orthogonal_triage.py"
)
CYCLE_ID = "V72P2D2-TRIAGE"
ACCEPTED_PLAN_GIT_REVISION = "4592bdad357a02f8f08a880ca0036beaed3ee900"
SEED = 20260902
CYCLE_STATE_PATH = REPO_ROOT / "docs" / "research_cycles" / CYCLE_ID / "cycle_state.yaml"
WORKSPACE_ROOT = (REPO_ROOT / "workspace").resolve()
PRODUCTION_OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench" / "outputs_comparison"
).resolve()
DEFAULT_OUTPUT = WORKSPACE_ROOT / "v72p2d2_orthogonal_preflight" / "cost_preflight.json"
REAL_OUTPUT_ROOT = (
    PRODUCTION_OUTPUT_ROOT / "v72p2d2_orthogonal_oneblock_20260904"
).resolve()


def load_triage_module():
    """Load the core module without importing any data or output runner."""
    spec = importlib.util.spec_from_file_location(
        "v72p2d2_orthogonal_triage", str(MODULE_PATH)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json_value(value: Any) -> Any:
    """Convert NumPy-like scalar/array values for the small JSON report."""
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _resolve_workspace_output(path: str | Path) -> Path:
    """Resolve a synthetic report path and keep it inside ``workspace``."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    output = candidate.resolve()
    try:
        output.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("synthetic preflight output must stay under workspace/") from exc
    if output == PRODUCTION_OUTPUT_ROOT or PRODUCTION_OUTPUT_ROOT in output.parents:
        raise ValueError("synthetic preflight output must stay outside production outputs")
    if output.name != "cost_preflight.json":
        raise ValueError("preflight output must be named cost_preflight.json")
    return output


def _parse_yaml_scalar(value: str) -> Any:
    """Parse the small scalar subset used by the cycle-state file."""
    text = value.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.lower() in {"null", "~"}:
        return None
    if (text.startswith("\"") and text.endswith("\"")) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    return text


def read_cycle_state(path: str | Path = CYCLE_STATE_PATH) -> dict[str, Any]:
    """Read only the flat authorization fields from a cycle-state YAML file.

    The repository cycle state is intentionally tiny and flat.  Avoiding a
    YAML dependency keeps this gate import-safe for the synthetic path.
    """
    state_path = Path(path)
    if not state_path.is_absolute():
        state_path = REPO_ROOT / state_path
    state_path = state_path.resolve()
    if not state_path.is_file():
        raise FileNotFoundError(f"cycle-state file not found: {state_path}")
    values: dict[str, Any] = {}
    for raw_line in state_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_yaml_scalar(value)
    values["_path"] = str(state_path)
    return values


def require_real_authorization(
    *, execute_real: bool, cycle_state_path: str | Path = CYCLE_STATE_PATH
) -> dict[str, Any]:
    """Require explicit intent and the accepted cycle's real-execution gate."""
    if not execute_real:
        raise PermissionError("real L/I/P execution requires --execute-real")
    state = read_cycle_state(cycle_state_path)
    if state.get("cycle_id") != CYCLE_ID:
        raise PermissionError("cycle-state cycle_id does not match V72P2D2-TRIAGE")
    if state.get("accepted_plan_git_revision") != ACCEPTED_PLAN_GIT_REVISION:
        raise PermissionError("cycle-state accepted plan revision is not the accepted V72P2D2 plan")
    if state.get("real_execution_authorized") is not True:
        raise PermissionError("cycle-state real_execution_authorized is not true")
    if state.get("formal_execution_authorized") is not True:
        raise PermissionError("cycle-state formal_execution_authorized is not true")
    return state


def _preflight_status(report: Mapping[str, Any]) -> tuple[str, int]:
    """Apply the frozen synthetic cost gate without changing its threshold.

    The core's frozen arithmetic and 600-second threshold are retained.  The
    synthetic preflight reports ``PLAN_REVISE_REQUIRED`` when the projection
    exceeds that threshold.  ``RESOURCE_BLOCKED`` is reserved for a future
    real L timeout and is not a synthetic preflight result.
    """
    projected = float(report["projected_L_wall_s"])
    if projected > 600.0:
        return "PLAN_REVISE_REQUIRED", 2
    return "PASS", 0


def run_synthetic_preflight(
    *, output: str | Path = DEFAULT_OUTPUT, seed: int = SEED
) -> int:
    """Run only the five-point synthetic layered cost preflight."""
    if int(seed) != SEED:
        raise ValueError(f"synthetic preflight seed is frozen at {SEED}")
    output_path = _resolve_workspace_output(output)
    module = load_triage_module()
    indptr, indices, nnz = module.get_mother_csr()
    if (
        int(nnz) != module.NNZ
        or indptr.shape != (module.M + 1,)
        or indices.shape != (module.NNZ,)
    ):
        raise ValueError("mother dimensions do not match the frozen contract")

    report = dict(module.cost_preflight(indptr, indices, seed=SEED))
    status, exit_code = _preflight_status(report)
    report["cli_mode"] = "synthetic-preflight"
    report["cycle_id"] = CYCLE_ID
    report["hard_wall_limit_s"] = 600.0
    report["core_preflight_status"] = report.get("status")
    report["status"] = status
    report["exit_code"] = exit_code
    report["real_decoder_executed"] = False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(_json_value(report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        "output": str(output_path),
        "status": status,
        "projected_L_wall_s": float(report["projected_L_wall_s"]),
        "peak_rss_bytes": int(report["peak_rss_bytes"]),
        "exit_code": exit_code,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


def run_real_orchestration(*, cycle_state_path: str | Path = CYCLE_STATE_PATH) -> int:
    """Guard the future real L/I/P orchestration without entering it here.

    This implementation candidate is limited to synthetic/test execution.
    Even an explicitly supplied but currently unauthorized cycle state must
    not cause data loading or creation of the formal output root.
    """
    require_real_authorization(execute_real=True, cycle_state_path=cycle_state_path)
    raise RuntimeError(
        "real L/I/P orchestration is not enabled in the synthetic-only implementation scope"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("synthetic-preflight", "real"),
        default="synthetic-preflight",
        help="synthetic preflight is the only phase enabled by default; real requires authorization",
    )
    parser.add_argument(
        "--execute-real",
        action="store_true",
        help="explicitly request the future real L/I/P path; cycle-state authorization is also required",
    )
    parser.add_argument(
        "--cycle-state",
        type=Path,
        default=CYCLE_STATE_PATH,
        help="cycle_state.yaml used only by the explicit real-execution gate",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.phase == "real" and not args.execute_real:
        print("--phase real requires --execute-real; no real run was started", file=sys.stderr)
        return 2
    if args.phase != "real" and args.execute_real:
        print("--execute-real requires --phase real; no synthetic run was started", file=sys.stderr)
        return 2
    if args.phase == "real":
        try:
            return run_real_orchestration(cycle_state_path=args.cycle_state)
        except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
            print(f"REAL_EXECUTION_BLOCKED: {exc}", file=sys.stderr)
            return 2
    try:
        return run_synthetic_preflight(output=args.out, seed=args.seed)
    except (FileNotFoundError, ImportError, ValueError, RuntimeError) as exc:
        print(f"SYNTHETIC_PREFLIGHT_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
