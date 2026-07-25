#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.runtime_paths import map_data_path


DEFAULT_DATASETS = [
    r"D:\Data\2026.1.20\Type0_nofilter_1M_3s_2026-01-20_192857",
    r"D:\Data\2026.1.20\Type0_nofilter_2M_3s_2026-01-20_193411",
    r"D:\Data\2026.1.20\Type0_nofilter_500K_3s_2026-01-20_193050",
    r"D:\Data\2026.1.20\Type0_nofilter_1_5M_3s_2026-01-20_193255",
]

DEFAULT_DATASETS = [str(map_data_path(path)) for path in DEFAULT_DATASETS]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _has_valid_singles_coincidences(metrics: dict[str, Any]) -> bool:
    singles = metrics.get("singles") if isinstance(metrics, dict) else None
    coins = metrics.get("coincidences") if isinstance(metrics, dict) else None
    if not isinstance(singles, dict) or not isinstance(coins, dict):
        return False
    required_s = ("count_A", "count_B", "rate_A_hz", "rate_B_hz")
    required_c = ("total_pairs", "coincidence_rate_hz", "delta_t_ps")
    if any(singles.get(k) is None for k in required_s):
        return False
    if any(coins.get(k) is None for k in required_c):
        return False
    dt = coins.get("delta_t_ps")
    if not isinstance(dt, dict):
        return False
    if any(dt.get(k) is None for k in ("mean", "var", "moment4")):
        return False
    return True


def _resolve_ttbin_file(dataset_dir: Path) -> Path:
    if dataset_dir.is_file():
        if dataset_dir.suffix.lower() != ".ttbin":
            raise FileNotFoundError(f"dataset path is not .ttbin: {dataset_dir}")
        return dataset_dir.resolve()

    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"dataset directory not found: {dataset_dir}")

    re_chunk = re.compile(r"\.\d+\.ttbin$", re.IGNORECASE)
    cands = [x for x in sorted(dataset_dir.glob("*.ttbin")) if x.is_file() and not re_chunk.search(x.name)]
    if not cands:
        raise FileNotFoundError(f"no main header .ttbin found under: {dataset_dir}")
    if len(cands) == 1:
        return cands[0].resolve()

    dir_name = dataset_dir.name.lower()
    prefer = [x for x in cands if x.stem.lower() == dir_name]
    if prefer:
        return sorted(prefer)[0].resolve()
    return sorted(cands, key=lambda x: (len(x.name), x.name.lower()))[0].resolve()


def _extract_channels_from_out_root(out_root: Path) -> tuple[int, int]:
    sidecars = out_root / "sidecars"
    if sidecars.exists():
        for meta in sorted(sidecars.glob("d*_bw*/blk0/sidecar_meta.json")):
            m = _read_json(meta)
            source_point_dir = str(m.get("source_point_dir") or "").strip()
            if not source_point_dir:
                continue
            rc = Path(source_point_dir) / "results" / "attempt_0" / "resolved_config.json"
            cfg = _read_json(rc)
            tt = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
            ch = tt.get("channels") if isinstance(tt.get("channels"), dict) else {}
            a = ch.get("A")
            b = ch.get("B")
            if a is not None and b is not None:
                try:
                    return int(a), int(b)
                except Exception:
                    pass
    # Project default for current ttbin datasets.
    return 1, 5


def _metrics_from_out_root_sidecars(out_root: Path, dataset_dir: Path) -> dict[str, Any]:
    sidecars = out_root / "sidecars"
    if not sidecars.exists():
        return {}
    for meta in sorted(sidecars.glob("d*_bw*/blk0/sidecar_meta.json")):
        m = _read_json(meta)
        src_joint = str(m.get("source_joint_path") or "").strip()
        if not src_joint:
            continue
        p = Path(src_joint.split("#", 1)[0].strip())
        # Guard against template/source leakage from old runs.
        try:
            p_res = p.resolve()
            ds_res = dataset_dir.resolve()
            if ds_res not in p_res.parents:
                continue
        except Exception:
            continue
        if p.exists():
            mj = _read_json(p)
            if _has_valid_singles_coincidences(mj):
                return mj
    return {}


def _compute_metrics_from_ttbin(dataset_dir: Path, out_root: Path) -> tuple[dict[str, Any], str]:
    try:
        from src.qkd_io.ttbin_pipeline import compute_ttbin_metrics, read_ttbin_events  # type: ignore
    except Exception as exc:
        return {}, f"import_ttbin_pipeline_failed:{type(exc).__name__}:{exc}"

    try:
        ttbin_file = _resolve_ttbin_file(dataset_dir)
    except Exception as exc:
        return {}, f"resolve_ttbin_failed:{type(exc).__name__}:{exc}"

    ch_a, ch_b = _extract_channels_from_out_root(out_root)
    cfg = {
        "channels": {"A": int(ch_a), "B": int(ch_b), "sync": None},
        "pairing": {"coin_window_ps": 200, "offset_ps": 0, "policy": "nearest_unique"},
        "framing": {"bin_width_ps": 20, "frame_bins": 256, "align": "sync", "postselect": "1click_each"},
    }
    try:
        events = read_ttbin_events(ttbin_file)
        metrics = compute_ttbin_metrics(events=events, cfg=cfg)
        if _has_valid_singles_coincidences(metrics):
            return metrics, f"computed_from_ttbin:{ttbin_file}#chA={ch_a},chB={ch_b}"
        return metrics, f"computed_but_incomplete:{ttbin_file}#chA={ch_a},chB={ch_b}"
    except Exception as exc:
        return {}, f"compute_ttbin_metrics_failed:{type(exc).__name__}:{exc}"


def _load_metrics_with_fallback(dataset_dir: Path, out_root: Path) -> tuple[dict[str, Any], str]:
    direct = dataset_dir / "results" / "ttbin_parsing" / "ttbin_metrics.json"
    if direct.exists():
        m = _read_json(direct)
        if _has_valid_singles_coincidences(m):
            return m, f"dataset_metrics:{direct}"

    # Prefer computing from current dataset ttbin to avoid stale template metrics.
    comp, source = _compute_metrics_from_ttbin(dataset_dir, out_root)
    if _has_valid_singles_coincidences(comp):
        return comp, source

    # Final fallback: source_joint_path from sidecar, but only if it belongs to current dataset.
    sidecar_metrics = _metrics_from_out_root_sidecars(out_root, dataset_dir)
    if _has_valid_singles_coincidences(sidecar_metrics):
        return sidecar_metrics, "sidecar_source_joint_path_in_dataset"

    return comp, source


def _extract_quick_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    events = metrics.get("events_summary") if isinstance(metrics.get("events_summary"), dict) else {}
    singles = metrics.get("singles") if isinstance(metrics.get("singles"), dict) else {}
    coins = metrics.get("coincidences") if isinstance(metrics.get("coincidences"), dict) else {}
    delta = coins.get("delta_t_ps") if isinstance(coins.get("delta_t_ps"), dict) else {}
    return {
        "acquisition_duration_s": events.get("acquisition_duration_s"),
        "singles": {
            "count_A": singles.get("count_A"),
            "count_B": singles.get("count_B"),
            "rate_A_hz": singles.get("rate_A_hz"),
            "rate_B_hz": singles.get("rate_B_hz"),
        },
        "coincidences": {
            "total_pairs": coins.get("total_pairs"),
            "coincidence_rate_hz": coins.get("coincidence_rate_hz"),
            "delta_t_ps": {
                "mean": delta.get("mean"),
                "var": delta.get("var"),
                "moment4": delta.get("moment4"),
            },
        },
    }


def _write_quick_analysis(dataset_dir: Path, out_root: Path, run_rc: int, run_elapsed_s: float) -> None:
    metrics, metrics_source = _load_metrics_with_fallback(dataset_dir, out_root)
    quick = _extract_quick_metrics(metrics)
    report = {
        "dataset_dir": str(dataset_dir),
        "out_root": str(out_root),
        "run_exit_code": int(run_rc),
        "run_elapsed_s": float(run_elapsed_s),
        "generated_at": datetime.now().isoformat(),
        "metrics_source": str(metrics_source),
        "quick_metrics": quick,
    }

    json_path = out_root / "ttbin_quick_analysis.json"
    md_path = out_root / "ttbin_quick_analysis.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    s = quick.get("singles", {})
    c = quick.get("coincidences", {})
    dt = c.get("delta_t_ps", {}) if isinstance(c, dict) else {}
    md = [
        "# TTBIN Quick Analysis",
        "",
        f"- dataset_dir: `{dataset_dir}`",
        f"- out_root: `{out_root}`",
        f"- run_exit_code: `{run_rc}`",
        f"- run_elapsed_s: `{run_elapsed_s:.2f}`",
        f"- metrics_source: `{metrics_source}`",
        "",
        "## Singles",
        "",
        f"- count_A: `{s.get('count_A')}`",
        f"- count_B: `{s.get('count_B')}`",
        f"- rate_A_hz: `{s.get('rate_A_hz')}`",
        f"- rate_B_hz: `{s.get('rate_B_hz')}`",
        "",
        "## Coincidences",
        "",
        f"- total_pairs: `{c.get('total_pairs')}`",
        f"- coincidence_rate_hz: `{c.get('coincidence_rate_hz')}`",
        f"- delta_t_ps.mean: `{dt.get('mean')}`",
        f"- delta_t_ps.var: `{dt.get('var')}`",
        f"- delta_t_ps.moment4: `{dt.get('moment4')}`",
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")


def _run_one(dataset_dir: Path, extract_workers: int, jobs: int, force_align: bool) -> tuple[int, Path, float]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = dataset_dir / f"e2e_new_ttbin_fullgrid_{ts}"
    out_root.mkdir(parents=True, exist_ok=True)

    dims = "4,8,16,32,64,128,256,512,1024,2048,4096"
    bws = "20,30,40,50,60,80,100,120,150,180,200"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "experiments" / "run_e2e_pipeline.py"),
        "--dims",
        dims,
        "--bws",
        bws,
        "--ttbin-override",
        str(dataset_dir),
        "--extract-workers",
        str(max(1, min(int(extract_workers), 15))),
        "--jobs",
        str(max(1, int(jobs))),
        "--out-root",
        str(out_root),
    ]
    if force_align:
        cmd.append("--force-align")

    print(f"[MULTI] start dataset={dataset_dir}")
    print(f"[MULTI] out_root={out_root}")
    print(f"[MULTI] cmd={' '.join(cmd)}")

    t0 = time.perf_counter()
    rc = subprocess.call(cmd, cwd=str(REPO_ROOT))
    elapsed_s = time.perf_counter() - t0

    print(f"[MULTI] done dataset={dataset_dir} rc={rc} elapsed_s={elapsed_s:.2f}")
    _write_quick_analysis(dataset_dir=dataset_dir, out_root=out_root, run_rc=rc, run_elapsed_s=elapsed_s)
    return int(rc), out_root, float(elapsed_s)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run full golden sweeps for four ttbin datasets.")
    ap.add_argument("--extract-workers", type=int, default=12)
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--force-align", action="store_true", default=True)
    ap.add_argument("--datasets", default=";".join(DEFAULT_DATASETS), help="semicolon-separated dataset directories")
    args = ap.parse_args()

    datasets = [Path(x.strip()) for x in str(args.datasets).split(";") if x.strip()]
    if not datasets:
        raise SystemExit("No dataset directories provided.")

    total_start = time.perf_counter()
    summary: list[dict[str, Any]] = []
    worst_rc = 0
    for ds in datasets:
        rc, out_root, elapsed_s = _run_one(
            dataset_dir=ds,
            extract_workers=int(args.extract_workers),
            jobs=int(args.jobs),
            force_align=bool(args.force_align),
        )
        summary.append(
            {
                "dataset_dir": str(ds),
                "out_root": str(out_root),
                "rc": int(rc),
                "elapsed_s": float(elapsed_s),
            }
        )
        if rc != 0 and worst_rc == 0:
            worst_rc = rc

    total_elapsed = time.perf_counter() - total_start
    summary_path = REPO_ROOT / "results" / f"golden_four_sweep_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "extract_workers": int(args.extract_workers),
                "jobs": int(args.jobs),
                "force_align": bool(args.force_align),
                "total_elapsed_s": float(total_elapsed),
                "runs": summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[MULTI] summary={summary_path}")
    print(f"[MULTI] total_elapsed_s={total_elapsed:.2f}")
    return int(worst_rc)


if __name__ == "__main__":
    raise SystemExit(main())
