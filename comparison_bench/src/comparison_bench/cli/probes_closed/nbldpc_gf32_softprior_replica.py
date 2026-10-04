"""Independent fresh-frame replica of the frozen GF(32) soft-prior probe."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from comparison_bench.cli.probes_closed import nbldpc_gf32_softprior_rescue as rescue

BATCH_UUID = "cbe151fe-25f7-4990-8895-858091467e2b"
CONTRACT = "NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/PREREG_AND_AUTH.md"
SEED_NAMESPACE = "gf32-softprior-replica-v1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_softprior_replica_cbe151fe"
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_softprior_replica --execute "
    "--out-root workspace/gf32_softprior_replica_cbe151fe"
)
PREDECESSOR_PLAN_NAME = (
    "nbldpc_gf32_softprior_rescue.build_seed_plan/gf32-softprior-v1"
)


def additional_excluded_plans() -> tuple[tuple[str, list[tuple[int, int, int, int]]], ...]:
    return ((PREDECESSOR_PLAN_NAME, rescue.build_seed_plan()),)


def build_seed_plan() -> list[tuple[int, int, int, int]]:
    return rescue.build_seed_plan(SEED_NAMESPACE)


def validate_seed_plan(
        plan: Sequence[Sequence[int]] | None = None,
        ) -> tuple[list[tuple[int, int, int, int]], list[dict[str, Any]]]:
    return rescue.validate_seed_plan(
        plan, seed_namespace=SEED_NAMESPACE,
        additional_excluded_plans=additional_excluded_plans())


def verify_t0(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = rescue.validate_out_root(
        OUT_ROOT_RELATIVE, repo_root=repo_root, official_root=OUT_ROOT_RELATIVE)
    result = rescue.verify_t0(
        batch_uuid=BATCH_UUID, contract=CONTRACT,
        seed_namespace=SEED_NAMESPACE,
        additional_excluded_plans=additional_excluded_plans())
    result["out_root"] = str(root)
    return result


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    return rescue.dry_run(
        out_root, repo_root=repo_root, batch_uuid=BATCH_UUID, contract=CONTRACT,
        seed_namespace=SEED_NAMESPACE, official_root=OUT_ROOT_RELATIVE,
        additional_excluded_plans=additional_excluded_plans())


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]],
        sampler: Callable[..., Any],
        decode_fns: Mapping[str, Callable[..., Any]],
        out_root: str | Path,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    return rescue.execute_batch(
        source_reader=source_reader, sampler=sampler, decode_fns=decode_fns,
        out_root=out_root, repo_root=repo_root, now=now, rss_fn=rss_fn,
        command=command, batch_uuid=BATCH_UUID, contract=CONTRACT,
        seed_namespace=SEED_NAMESPACE, official_root=OUT_ROOT_RELATIVE,
        additional_excluded_plans=additional_excluded_plans())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GF(32) soft-prior independent replica")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true", help="source-free seed/contract checks")
    mode.add_argument("--dry-run", action="store_true", help="validate frozen root; no reads/writes")
    mode.add_argument("--execute", action="store_true", help="run one frozen synthetic replica")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0()
    elif args.dry_run:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            **rescue._bind_production(), out_root=args.out_root, command=COMMAND)
    printable = result.get("summary", result)
    print(json.dumps(printable, sort_keys=True, default=rescue._json_value))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
