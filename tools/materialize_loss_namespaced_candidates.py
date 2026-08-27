#!/usr/bin/env python3
"""Materialize candidate sequences into loss-namespaced pools (fix-candidate-loss-namespace).

Rebuilds per-loss-tier candidate sequence pools from the original raw ttbin records
using the frozen baseline toolchain (`export_sidecar_for_point`), writing into the
namespaced layout (design.md section 2/5):

    <pool-root>/<src_tag>/d{d}_bw{bw}/blk{b}/{a_eff.npy,b_eff.npy,materialize_meta.json}
    <pool-root>/MANIFEST.csv

Pinned degrees of freedom (design.md section 3, must not drift):
    pairing_v2 / nearest / occupancy_filter=0 / max_pairs=0 (uncapped)
    HDQKD_NEAREST_FRAME_THRESHOLD_PS=40000 / HDQKD_ALIGN_DEBUG=0
    channel overrides cleared (defaults A=1,B=5); no delay/offset/frame_start/coinc overrides.

src_tag mapping: Type2_5s_<loss>dB_* record dirs ->
    {20dB: loss20dB_t15, 16dB: loss16dB, 10dB: loss10dB, 6dB: loss6dB}

NOTE: like the original 2026-03 runs, this relies on resolve_point_sources'
override branch, which reuses/rebuilds ttbin_metrics.json under
results/archive/workspace_override_points. Do not run against real data without
the Phase 2/3 go-ahead; use --dry-run to inspect the plan.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.workflow.export_joint_sequence_sidecar import export_sidecar_for_point  # type: ignore
from tools.verify_candidate_namespace_gates import (  # type: ignore
    MANIFEST_HEADER,
    SRC_TAG_BY_TIER,
    TIER_TTBIN_DIRS,
    normalize_tier,
    sha256_file,
)

DEFAULT_RAW_ROOT = r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s"
DEFAULT_POOL_ROOT = "results/real_sequences_ns"
DEFAULT_OUT_ROOT_TEMPLATE = (
    "results/authoritative_nsfix/e2e_{tier}_fullgrid_pairing_v2_candidate_lossfix_v1"
)
DEFAULT_DIMS = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
DEFAULT_BWS = [20, 30, 40, 50, 60, 80, 100, 120, 150, 180, 200]

PINNED_ENV = {
    "HDQKD_NEAREST_FRAME_THRESHOLD_PS": "40000",
    "HDQKD_ALIGN_DEBUG": "0",
}
PARAMS_TAG = "pairing_v2-nearest_occ0_maxpairs0_thr40000_aligndebug0"


def _resolve(p: str | Path) -> Path:
    pp = Path(p)
    return pp if pp.is_absolute() else REPO_ROOT / pp


def parse_points(spec: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for part in str(spec).split(";"):
        part = part.strip()
        if not part:
            continue
        d_s, bw_s = part.split(",")
        out.append((int(d_s), int(bw_s)))
    return out


def pin_environment() -> list[str]:
    notes: list[str] = []
    for k, v in PINNED_ENV.items():
        os.environ[k] = v
        notes.append(f"env {k}={v} (pinned)")
    for k in ("HDQKD_TTBIN_CH_A_OVERRIDE", "HDQKD_TTBIN_CH_B_OVERRIDE"):
        if os.environ.pop(k, None) is not None:
            notes.append(f"env {k} cleared (pinned to defaults A=1,B=5)")
    return notes


def append_manifest_row(pool_root: Path, row: dict[str, Any]) -> None:
    """Create-or-update MANIFEST.csv, replacing any prior row with the same pool key."""
    manifest = pool_root / "MANIFEST.csv"
    rows: list[dict[str, Any]] = []
    if manifest.exists():
        with manifest.open("r", newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f)]
    key = (row["src_tag"], row["d"], row["bw"], row["blk"])
    rows = [r for r in rows if (r.get("src_tag"), r.get("d"), r.get("bw"), r.get("blk")) != key]
    rows.append(row)
    rows.sort(key=lambda r: (str(r["src_tag"]), int(r["d"]), int(r["bw"]), int(r["blk"])))
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_HEADER)
        w.writeheader()
        w.writerows(rows)


def cell_materialized(blk_dir: Path) -> bool:
    """True only when sidecar_meta.json parses and records materialize_ok==1;
    missing meta, unparsable JSON, or an explicit FAIL all count as NOT done,
    so --resume reruns failed/interrupted cells."""
    try:
        meta = json.loads((blk_dir / "sidecar_meta.json").read_text(encoding="utf-8"))
    except Exception:
        return False
    return int(meta.get("materialize_ok", 0)) == 1


def materialize_tier(
    tier: str,
    *,
    raw_root: Path,
    pool_root: Path,
    out_root: Path,
    points: list[tuple[int, int]],
    factor: int,
    block_index: int,
    resume: bool,
    dry_run: bool,
) -> tuple[int, int]:
    dirname = TIER_TTBIN_DIRS[tier]
    src_tag = SRC_TAG_BY_TIER[tier]
    main_ttbin = raw_root / dirname / f"{dirname}.ttbin"
    if not main_ttbin.is_file() or main_ttbin.stat().st_size == 0:
        raise FileNotFoundError(f"[{tier}] raw ttbin missing or empty: {main_ttbin}")

    tier_pool_root = pool_root / src_tag
    tier_out_root = out_root
    print(f"\n=== tier {tier} -> src_tag={src_tag}")
    print(f"    ttbin      : {main_ttbin}")
    print(f"    pool_root  : {tier_pool_root}")
    print(f"    out_root   : {tier_out_root}")
    print(f"    points     : {len(points)}")
    print(f"    params_tag : {PARAMS_TAG}")

    existing_cells = 0
    sc_root = tier_out_root / "sidecars"
    if sc_root.is_dir():
        existing_cells = sum(1 for _ in sc_root.glob(f"d*_bw*/blk{block_index}/sidecar_meta.json"))
    if dry_run:
        print(f"[dry-run] would write up to {len(points)} cells "
              f"(existing sidecars found: {existing_cells}, resume={resume})")
        return 0, 0
    if existing_cells and not resume:
        raise RuntimeError(
            f"[{tier}] out_root already contains {existing_cells} sidecar(s); "
            "refusing to mix vintages. Use --resume to keep existing cells and fill gaps."
        )

    os.environ["HDQKD_TTBIN_FILE_OVERRIDE"] = str(main_ttbin)
    n_ok = n_fail = 0
    ttbin_sha = sha256_file(main_ttbin)
    for d, bw in points:
        cell_sidecar = tier_out_root / "sidecars" / f"d{d}_bw{bw}" / f"blk{block_index}"
        if resume and cell_materialized(cell_sidecar):
            print(f"[{tier}] ({d},{bw}) skip (sidecar present, materialize_ok=1)")
            continue
        if resume:
            print(f"[{tier}] ({d},{bw}) rerun (no meta or materialize_ok!=1)")
        res = export_sidecar_for_point(
            point=f"{d},{bw}",
            factor=int(factor),
            block_index=int(block_index),
            out_root=str(cell_sidecar),
            sequence_source_mode="strict",
            materialize_missing_real_seq=1,
            joint_source_mode="from_ttbin",
            materialize_diagnostics=1,
            materialize_pairing_mode="nearest",
            materialize_processing_rule_version="pairing_v2",
            materialize_max_pairs=0,
            materialize_occupancy_filter=0,
            pool_root=str(tier_pool_root),
        )
        ok_flag = int(res.get("materialize_ok", 0)) == 1
        verdict = res.get("verdict")
        map_ser = res.get("map_ser")
        status = "ok" if ok_flag else f"MATERIALIZE_FAIL({res.get('materialize_error')})"
        print(f"[{tier}] ({d},{bw}) {status} verdict={verdict} map_ser={map_ser}")
        if not ok_flag:
            n_fail += 1
            continue
        n_ok += 1
        blk_dir = tier_pool_root / f"d{d}_bw{bw}" / f"blk{block_index}"
        chan_ll = cell_sidecar / "chan_ll_table.npy"
        append_manifest_row(pool_root, {
            "src_tag": src_tag,
            "d": d,
            "bw": bw,
            "blk": block_index,
            "ttbin_path": str(main_ttbin),
            "ttbin_sha256": ttbin_sha,
            "a_eff_sha256": sha256_file(blk_dir / "a_eff.npy"),
            "b_eff_sha256": sha256_file(blk_dir / "b_eff.npy"),
            "params_tag": PARAMS_TAG,
            "chan_ll_sha256": sha256_file(chan_ll) if chan_ll.is_file() else "",
        })
    return n_ok, n_fail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--tiers", required=True,
                    help="comma list among 6dB,10dB,16dB,20dB (e.g. \"6dB,10dB\")")
    ap.add_argument("--raw-root", default=DEFAULT_RAW_ROOT)
    ap.add_argument("--pool-root", default=DEFAULT_POOL_ROOT)
    ap.add_argument("--out-root-template", default=DEFAULT_OUT_ROOT_TEMPLATE)
    ap.add_argument("--dims", default=",".join(map(str, DEFAULT_DIMS)))
    ap.add_argument("--bws", default=",".join(map(str, DEFAULT_BWS)))
    ap.add_argument("--points", default="",
                    help='explicit subset "d,bw;d,bw" overriding --dims/--bws')
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--block-index", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="skip cells whose sidecar exists AND recorded materialize_ok=1; "
                         "missing meta or FAIL cells are rerun")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    tiers = [normalize_tier(t) for t in str(args.tiers).split(",") if t.strip()]
    raw_root = _resolve(args.raw_root)
    pool_root = _resolve(args.pool_root)
    points = parse_points(args.points) if args.points else [
        (d, bw) for d in (int(x) for x in str(args.dims).split(",")) for bw in (int(x) for x in str(args.bws).split(","))
    ]

    print(f"[nsfix] tiers={tiers}")
    print(f"[nsfix] pinned: {PARAMS_TAG}")
    env_notes = pin_environment()
    for note in env_notes:
        print(f"[nsfix] {note}")

    total_ok = total_fail = 0
    started = datetime.now().isoformat()
    for tier in tiers:
        out_root = _resolve(str(args.out_root_template).format(tier=tier))
        n_ok, n_fail = materialize_tier(
            tier,
            raw_root=raw_root,
            pool_root=pool_root,
            out_root=out_root,
            points=points,
            factor=int(args.factor),
            block_index=int(args.block_index),
            resume=bool(args.resume),
            dry_run=bool(args.dry_run),
        )
        total_ok += n_ok
        total_fail += n_fail

    print(f"\n[nsfix] started={started} finished={datetime.now().isoformat()}")
    print(f"[nsfix] materialized ok={total_ok} fail={total_fail}")
    if total_fail:
        print("[nsfix] FAILING CELLS PRESENT — do not silently rerun; report per stop rules.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
