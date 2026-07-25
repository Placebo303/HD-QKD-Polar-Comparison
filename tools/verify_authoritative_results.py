#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.runtime_paths import default_project_results_root


SCHEMA = "hdqkd-authoritative-pack-digest-v1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def pack_digest(pack_dir: Path, *, workers: int = 4) -> dict[str, Any]:
    files = sorted(
        (path for path in pack_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(pack_dir).as_posix(),
    )
    workers = max(1, int(workers))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        hashes = list(pool.map(_sha256_file, files))

    tree = hashlib.sha256()
    total_bytes = 0
    for path, file_hash in zip(files, hashes):
        relative = path.relative_to(pack_dir).as_posix()
        size = path.stat().st_size
        total_bytes += size
        tree.update(f"{relative}\t{size}\t{file_hash}\n".encode("utf-8"))
    return {
        "name": pack_dir.name,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "tree_sha256": tree.hexdigest(),
    }


def build_manifest(authoritative_root: Path, *, workers: int = 4) -> dict[str, Any]:
    root = authoritative_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"authoritative result root not found: {root}")
    packs = []
    for pack_dir in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.name):
        print(f"[HASH] {pack_dir.name}", flush=True)
        packs.append(pack_digest(pack_dir, workers=workers))
    return {
        "schema": SCHEMA,
        "algorithm": "sha256",
        "logical_root": "results/authoritative",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "packs": packs,
    }


def _comparable(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": manifest.get("schema"),
        "algorithm": manifest.get("algorithm"),
        "logical_root": manifest.get("logical_root"),
        "packs": manifest.get("packs"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or verify deterministic SHA-256 digests for authoritative result packs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=default_project_results_root(REPO_ROOT) / "authoritative",
        help="authoritative results root (default: PROJECT_RESULTS_ROOT/authoritative or results/authoritative)",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", type=Path, help="write a JSON manifest")
    action.add_argument("--verify", type=Path, help="verify against an existing JSON manifest")
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    args = parser.parse_args()

    actual = build_manifest(args.root, workers=args.workers)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote {args.write}")
        return 0

    expected = json.loads(args.verify.read_text(encoding="utf-8"))
    if _comparable(actual) != _comparable(expected):
        print("[FAIL] authoritative result manifest mismatch")
        return 1
    print(f"[OK] verified {len(actual['packs'])} authoritative packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
