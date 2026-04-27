#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.workflow.coarse_grain_joint import dense_from_sparse  # type: ignore


DATA_ROOT_DEFAULT = Path(r"D:\Data\Raw Data\ASENoise_Type0")
DEFAULT_DIMS = "32,64,128,256,512"
DEFAULT_BWS = "30,40,50,60,80,100,120,150,180,200"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_int_list(value: str) -> list[int]:
    out: list[int] = []
    for part in str(value).split(","):
        s = part.strip()
        if not s:
            continue
        out.append(int(s))
    if not out:
        raise ValueError(f"empty integer list: {value!r}")
    return out


def _find_head_ttbin(dataset_dir: Path) -> Path:
    heads = [p for p in sorted(dataset_dir.glob("*.ttbin")) if not any(p.name.lower().endswith(f".{i}.ttbin") for i in range(1000))]
    if len(heads) != 1:
        raise RuntimeError(f"expected exactly one head .ttbin in {dataset_dir}, found {len(heads)}")
    return heads[0]


def _run_logged(cmd: list[str], *, cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="") as log:
        line = f"[RUN] {_now()} cwd={cwd} cmd={' '.join(cmd)}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for out_line in proc.stdout:
            try:
                print(out_line, end="", flush=True)
            except UnicodeEncodeError:
                safe_line = out_line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
                    sys.stdout.encoding or "utf-8",
                    errors="replace",
                )
                print(safe_line, end="", flush=True)
            log.write(out_line)
        code = int(proc.wait())
        done = f"[RUN] {_now()} exit={code}"
        print(done, flush=True)
        log.write(done + "\n")
        return code


def _load_joint_sparse(path: Path) -> tuple[int, list[Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    d_eff = int(payload.get("d_eff") or 0)
    sparse = payload.get("joint_counts_sparse")
    if not isinstance(sparse, list):
        raise ValueError(f"joint_counts_sparse missing or not a list: {path}")
    if d_eff <= 0:
        raise ValueError(f"d_eff missing or invalid: {path}")
    return d_eff, sparse


def _format_count(value: float) -> str:
    v = float(value)
    if not math.isfinite(v):
        return ""
    nearest = round(v)
    if abs(v - nearest) <= 1e-9:
        return str(int(nearest))
    return f"{v:.12g}"


def _write_dense_jti_csv(path: Path, dense: np.ndarray) -> None:
    arr = np.asarray(dense, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"dense JTI must be square, got {arr.shape}")
    d = int(arr.shape[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["", *[str(i) for i in range(d)]])
        for i in range(d):
            w.writerow([str(i), *[_format_count(x) for x in arr[i, :].tolist()]])


def _validate_dense_csv(path: Path, *, dimension: int, expected_total: float) -> dict[str, Any]:
    rows = list(csv.reader(path.open("r", encoding="utf-8", newline="")))
    d = int(dimension)
    errors: list[str] = []
    if len(rows) != d + 1:
        errors.append(f"row_count={len(rows)} expected={d + 1}")
    if rows and rows[0] != ["", *[str(i) for i in range(d)]]:
        errors.append("bad_header")
    total = 0.0
    for idx, row in enumerate(rows[1:], start=0):
        if len(row) != d + 1:
            errors.append(f"row_{idx}_col_count={len(row)} expected={d + 1}")
            continue
        if row[0] != str(idx):
            errors.append(f"row_{idx}_label={row[0]!r}")
        for value in row[1:]:
            total += float(value) if str(value).strip() else 0.0
    if abs(total - float(expected_total)) > max(1e-6, abs(float(expected_total)) * 1e-9):
        errors.append(f"total={total:.12g} expected={float(expected_total):.12g}")
    return {
        "csv_path": str(path),
        "dimension": d,
        "row_count": len(rows),
        "col_count": len(rows[0]) if rows else 0,
        "total_counts": total,
        "expected_total_counts": float(expected_total),
        "ok": not errors,
        "errors": errors,
    }


def export_jti_csvs(*, run_root: Path, dataset_label: str, dims: list[int], bws: list[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    e2e_root = run_root / "e2e_center_aligned"
    sidecars_root = e2e_root / "sidecars"
    jti_root = run_root / "jti_csv"
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for d in dims:
        for bw in bws:
            joint_path = sidecars_root / f"d{int(d)}_bw{int(bw)}" / "blk0" / "joint_counts_sparse.json"
            if not joint_path.exists():
                raise FileNotFoundError(f"missing joint_counts_sparse.json: {joint_path}")
            d_eff, sparse = _load_joint_sparse(joint_path)
            if int(d_eff) != int(d):
                raise ValueError(f"d_eff mismatch for {joint_path}: {d_eff} != {d}")
            dense = dense_from_sparse(sparse, int(d))
            total = float(np.sum(dense))
            csv_path = jti_root / f"d{int(d)}_bw{int(bw)}_jti.csv"
            _write_dense_jti_csv(csv_path, dense)
            check = _validate_dense_csv(csv_path, dimension=int(d), expected_total=total)
            checks.append(check)
            if not check["ok"]:
                raise RuntimeError(f"JTI CSV validation failed for {csv_path}: {check['errors']}")
            rows.append(
                {
                    "dataset_label": dataset_label,
                    "dimension": int(d),
                    "bin_width_ps": int(bw),
                    "csv_path": str(csv_path),
                    "source_joint_json": str(joint_path),
                    "total_counts": _format_count(total),
                    "shape_rows": int(d),
                    "shape_cols": int(d),
                }
            )
    index_path = jti_root / "jti_csv_index.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "dataset_label",
            "dimension",
            "bin_width_ps",
            "csv_path",
            "source_joint_json",
            "total_counts",
            "shape_rows",
            "shape_cols",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return rows, checks


def _has_expected_joint_sidecars(*, run_root: Path, dims: list[int], bws: list[int]) -> bool:
    sidecars_root = run_root / "e2e_center_aligned" / "sidecars"
    return all((sidecars_root / f"d{int(d)}_bw{int(bw)}" / "blk0" / "joint_counts_sparse.json").exists() for d in dims for bw in bws)


def run_dataset(*, dataset_dir: Path, out_name: str, dims_s: str, bws_s: str, workers: int, jobs: int) -> dict[str, Any]:
    dims = _parse_int_list(dims_s)
    bws = _parse_int_list(bws_s)
    run_root = dataset_dir / out_name
    e2e_root = run_root / "e2e_center_aligned"
    log_path = run_root / "run.log"
    run_root.mkdir(parents=True, exist_ok=True)
    head = _find_head_ttbin(dataset_dir)
    item: dict[str, Any] = {
        "dataset_label": dataset_dir.name,
        "dataset_dir": str(dataset_dir),
        "head_ttbin": str(head),
        "run_root": str(run_root),
        "e2e_root": str(e2e_root),
        "jti_csv_root": str(run_root / "jti_csv"),
        "started_at": _now(),
        "channels": {"A": 3, "B": 2},
        "dims": dims,
        "bws": bws,
        "errors": [],
    }
    if _has_expected_joint_sidecars(run_root=run_root, dims=dims, bws=bws):
        item["e2e_exit_code"] = "skipped_existing_complete_sidecars"
        item["e2e_cmd"] = []
        print(f"[JTI] reuse existing complete sidecars: {run_root}", flush=True)
    else:
        cmd = [
            sys.executable,
            "experiments/run_e2e_pipeline.py",
            "--ttbin",
            str(head),
            "--ttbin-ch-a-override",
            "3",
            "--ttbin-ch-b-override",
            "2",
            "--dims",
            dims_s,
            "--bws",
            bws_s,
            "--force-align",
            "--skip-polar",
            "--extract-workers",
            str(int(workers)),
            "--jobs",
            str(int(jobs)),
            "--out-root",
            str(e2e_root),
        ]
        code = _run_logged(cmd, cwd=REPO_ROOT, log_path=log_path)
        item["e2e_exit_code"] = code
        item["e2e_cmd"] = cmd
        if code != 0:
            item["errors"].append(f"e2e_failed:{code}")
            item["finished_at"] = _now()
            _write_json(run_root / "jti_run_manifest.json", item)
            return item
    try:
        rows, checks = export_jti_csvs(run_root=run_root, dataset_label=dataset_dir.name, dims=dims, bws=bws)
        item["jti_csv_count"] = len(rows)
        item["jti_csv_index"] = str(run_root / "jti_csv" / "jti_csv_index.csv")
        item["validation"] = {
            "expected_csv_count": len(dims) * len(bws),
            "actual_csv_count": len(rows),
            "all_csv_ok": all(bool(c.get("ok")) for c in checks),
            "checks": checks,
        }
    except Exception as exc:
        item["errors"].append(f"jti_export_failed:{type(exc).__name__}:{exc}")
    item["finished_at"] = _now()
    _write_json(run_root / "jti_run_manifest.json", item)
    return item


def main() -> int:
    ap = argparse.ArgumentParser(description="Run ASENoise Type0 ch3/ch2 center-aligned sidecars and export dense JTI CSVs.")
    ap.add_argument("--data-root", default=str(DATA_ROOT_DEFAULT))
    ap.add_argument("--dims", default=DEFAULT_DIMS)
    ap.add_argument("--bws", default=DEFAULT_BWS)
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=15)
    ap.add_argument("--timestamp", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    ap.add_argument("--datasets", default="", help="optional comma-separated dataset directory names")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    data_root = Path(args.data_root)
    selected = {x.strip() for x in str(args.datasets).split(",") if x.strip()}
    datasets = [p for p in sorted(data_root.iterdir(), key=lambda x: x.name) if p.is_dir() and (not selected or p.name in selected)]
    out_name = f"hdqkd_asenoise_type0_ch3_2_jti_center_aligned_{args.timestamp}"
    manifest_path = data_root / f"asenoise_type0_jti_dense_manifest_{args.timestamp}.json"
    dims = _parse_int_list(str(args.dims))
    bws = _parse_int_list(str(args.bws))

    results: list[dict[str, Any]] = []
    for ds in datasets:
        run_root = ds / out_name
        if run_root.exists() and any(run_root.iterdir()):
            if (not bool(args.overwrite)) and (not _has_expected_joint_sidecars(run_root=run_root, dims=dims, bws=bws)):
                raise SystemExit(f"output exists: {run_root} (use --overwrite)")
            if bool(args.overwrite):
                shutil.rmtree(run_root)
        result = run_dataset(
            dataset_dir=ds,
            out_name=out_name,
            dims_s=str(args.dims),
            bws_s=str(args.bws),
            workers=int(args.workers),
            jobs=int(args.jobs),
        )
        results.append(result)
        _write_json(manifest_path, {"created_at": _now(), "results": results})

    expected_total = len(datasets) * len(dims) * len(bws)
    actual_total = sum(int(r.get("jti_csv_count") or 0) for r in results)
    payload = {
        "created_at": _now(),
        "data_root": str(data_root),
        "out_name": out_name,
        "dims": dims,
        "bws": bws,
        "channels": {"A": 3, "B": 2},
        "expected_total_jti_csv": expected_total,
        "actual_total_jti_csv": actual_total,
        "ok": bool(actual_total == expected_total and all(not r.get("errors") for r in results)),
        "results": results,
    }
    _write_json(manifest_path, payload)
    print(f"[JTI] manifest={manifest_path}")
    print(f"[JTI] expected_total={expected_total} actual_total={actual_total} ok={payload['ok']}")
    return 0 if bool(payload["ok"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
