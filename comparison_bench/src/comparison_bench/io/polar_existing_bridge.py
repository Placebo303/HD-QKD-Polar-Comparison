from __future__ import annotations

import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

from ..metrics.leakage import compute_beta_eff_empirical
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate
from ..utils.paths import default_output_dir, repo_root

DEFAULT_POLAR_RESULTS_ROOT = Path(
    str(os.getenv("POLAR_RESULTS_ROOT") or os.getenv("PROJECT_RESULTS_ROOT") or r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s")
)

POLAR_OUTPUT_NAMES = {
    "real_polar_max_pie_grid.csv",
    "polar_e2e_results.csv",
    "polar_e2e_results_refresh.csv",
    "actual_ir_point_table.csv",
    "polar_diag_summary.csv",
}

PREFERRED_OUTPUT_ORDER = {
    "polar_diag_summary.csv": 0,
    "polar_e2e_results_refresh.csv": 1,
    "polar_e2e_results.csv": 2,
    "actual_ir_point_table.csv": 3,
    "real_polar_max_pie_grid.csv": 4,
}

COMPANION_PATTERNS = [
    "polar_e2e_results.csv",
    "polar_e2e_results_refresh.csv",
    "polar_layer_metrics.csv",
    "*_tmp_grid_table.csv",
    "*_tmp_src_table.csv",
    "_tmp_grid_table.csv",
    "_tmp_src_table.csv",
]

SUPPLEMENT_FIELDS = [
    "leak_EC_actual_bits",
    "runtime_s",
    "n_frames_success",
    "n_frames_failed_decode",
    "n_frames_failed_verify",
    "throughput_input_bits_per_s",
]



def _as_path(value: Any) -> Path | None:
    if value is None or str(value).strip() == "":
        return None
    return Path(str(value))


def _candidate_roots(search_roots: list[Path] | None = None) -> list[Path]:
    roots: list[Path] = []
    if search_roots:
        roots.extend(search_roots)
    roots.extend([repo_root() / "results", repo_root() / "comparison_bench" / "outputs_comparison", DEFAULT_POLAR_RESULTS_ROOT])
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            rp = root.resolve()
        except Exception:
            rp = root
        key = str(rp).lower()
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def locate_existing_polar_outputs(search_roots: list[Path] | None = None) -> list[Path]:
    out: list[Path] = []
    for base in _candidate_roots(search_roots):
        if not base.exists():
            continue
        for p in base.rglob("*.csv"):
            name = p.name.lower()
            if name in POLAR_OUTPUT_NAMES or (
                ("polar" in name or "e2e" in name or "diag" in name or "results" in name)
                and name.endswith(".csv")
            ):
                out.append(p)
    return sorted(set(out), key=lambda p: str(p).lower())


def _read_csv_header(path: Path) -> list[str]:
    try:
        return list(pd.read_csv(path, nrows=0).columns)
    except Exception:
        return []


def _loss_from_path(path: Path) -> float:
    m = re.search(r"(\d+(?:\.\d+)?)dB", str(path), re.IGNORECASE)
    return float(m.group(1)) if m else float("nan")


def _score_candidate(path: Path) -> tuple[int, int, int, float, str]:
    cols = _read_csv_header(path)
    colset = {c.lower() for c in cols}
    name = path.name.lower()
    score = 0
    if name in PREFERRED_OUTPUT_ORDER:
        score += 100 - PREFERRED_OUTPUT_ORDER[name] * 5
    if "raw_ser" in colset:
        score += 40
    if "n_pairs_actual" in colset or "n_eff_pairs" in colset:
        score += 15
    if "threshold_ps" in colset:
        score += 10
    if "processing_rule_version" in colset or "pairing_path_tag" in colset:
        score += 8
    if any("leak" in c for c in colset):
        score += 30
    pass_rows = 0
    rows = 0
    try:
        df = pd.read_csv(path)
        rows = len(df)
        if "status" in df.columns:
            pass_rows = int(df["status"].astype(str).str.upper().eq("PASS").sum())
        elif "sidecar_verdict" in df.columns:
            pass_rows = int(df["sidecar_verdict"].astype(str).str.upper().eq("PASS").sum())
    except Exception:
        pass
    if pass_rows:
        score += 80
    if rows:
        score += min(rows, 20)
    # Prefer the explicitly rerun/refreshed successful tables when otherwise comparable.
    if "rerun" in str(path).lower() or "refresh" in name:
        score += 6
    return (-score, -pass_rows, -rows, -path.stat().st_mtime if path.exists() else 0.0, str(path).lower())


def select_polar_output(candidates: list[Path]) -> Path | None:
    readable = [p for p in candidates if p.exists() and _read_csv_header(p)]
    if not readable:
        return None
    return sorted(readable, key=_score_candidate)[0]


def _first_float(row: pd.Series, names: list[str], default: float = float("nan")) -> float:
    for name in names:
        if name in row.index:
            try:
                v = float(row[name])
            except Exception:
                continue
            if math.isfinite(v):
                return v
    return default


def _first_value(row: pd.Series, names: list[str], default: Any = None) -> Any:
    for name in names:
        if name in row.index:
            value = row[name]
            if pd.notna(value):
                return value.item() if hasattr(value, "item") else value
    return default


def _first_int(row: pd.Series, names: list[str], default: int = 0) -> int:
    v = _first_float(row, names, float("nan"))
    return int(v) if math.isfinite(v) else int(default)


def _missing_fields(columns: list[str], wanted: list[str]) -> list[str]:
    present = set(columns)
    return [c for c in wanted if c not in present]


def _ci_get(row: pd.Series, name: str, default: Any = float("nan")) -> Any:
    wanted = name.lower()
    for col in row.index:
        if str(col).lower() == wanted:
            value = row[col]
            return value.item() if hasattr(value, "item") else value
    return default


def _ci_float(row: pd.Series, name: str, default: float = float("nan")) -> float:
    value = _ci_get(row, name, default)
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _companion_paths(primary: Path) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = {str(primary.resolve()).lower()}
    for pattern in COMPANION_PATTERNS:
        for path in primary.parent.glob(pattern):
            try:
                key = str(path.resolve()).lower()
            except Exception:
                key = str(path).lower()
            if path.is_file() and key not in seen:
                seen.add(key)
                out.append(path)
    return sorted(out, key=lambda p: p.name.lower())


def _join_key_from_row(row: pd.Series, loss_from_path: float) -> tuple[Any, Any, Any]:
    dim = _first_int(row, ["dimension"], 0)
    bin_width = _first_value(row, ["bin_width_ps"], float("nan"))
    loss = _first_float(row, ["loss_db"], loss_from_path)
    def clean(v: Any) -> Any:
        try:
            f = float(v)
            if math.isfinite(f):
                return round(f, 9)
        except Exception:
            pass
        return str(v)
    return (clean(dim), clean(bin_width), clean(loss))


def _load_companion_supplements(primary: Path) -> dict[str, Any]:
    checked = _companion_paths(primary)
    by_key: dict[tuple[Any, Any, Any], dict[str, Any]] = {}
    present_fields: set[str] = set()
    loss_hint = _loss_from_path(primary)
    for path in checked:
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        col_lut = {str(c).lower(): c for c in df.columns}
        exact_fields = [f for f in SUPPLEMENT_FIELDS if f.lower() in col_lut]
        present_fields.update(exact_fields)
        if not exact_fields:
            continue
        for _, row in df.iterrows():
            key = _join_key_from_row(row, loss_hint)
            target = by_key.setdefault(key, {})
            for field in exact_fields:
                value = row[col_lut[field.lower()]]
                if pd.notna(value) and field not in target:
                    target[field] = value.item() if hasattr(value, "item") else value
    return {
        "checked_files": [str(p) for p in checked],
        "by_key": by_key,
        "missing_after_companion_scan": [f for f in SUPPLEMENT_FIELDS if f not in present_fields],
    }


def benchmark_rows_from_polar_output(path: Path, dataset_id: str | None = None, method_variant: str = "read_existing") -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Polar output is empty: {path}")
    rows: list[dict[str, Any]] = []
    cols = list(df.columns)
    wanted = [
        "dataset_id", "loss_db", "dimension", "bin_width_ps", "n_eff_pairs", "frame_len_symbols",
        "processing_rule_version", "pairing_path_tag", "threshold_ps", "effective_pairing_window_ps",
        "raw_ser", "leak_EC_actual_bits", "runtime_s",
    ]
    source_missing = _missing_fields(cols, wanted)
    companion = _load_companion_supplements(path)
    checked_names = [Path(p).name for p in companion["checked_files"]]
    missing_after_scan = companion["missing_after_companion_scan"]
    loss_from_path = _loss_from_path(path)
    for idx, row in df.iterrows():
        dim = _first_int(row, ["dimension"], 0)
        if dim <= 1:
            continue
        frame_len_symbols = _first_int(row, ["frame_len_symbols", "layer_block_symbols", "N"], 0)
        if frame_len_symbols <= 0:
            frame_len_symbols = dim
        frame_len_bits = _first_int(row, ["frame_len_bits"], 0)
        if frame_len_bits <= 0:
            frame_len_bits = frame_len_symbols * max(1, int(math.ceil(math.log2(dim))))
        n_eff_pairs = _first_float(row, ["n_eff_pairs", "n_pairs_actual", "n_pairs_in_clean_frames"], float("nan"))
        n_frames_total = _first_int(row, ["n_frames_total", "audited_block_count"], 0)
        if n_frames_total <= 0 and math.isfinite(n_eff_pairs) and frame_len_symbols > 0:
            n_frames_total = int(max(1, math.floor(n_eff_pairs / frame_len_symbols)))
        raw_ser = _first_float(row, ["raw_ser", "map_ser"], float("nan"))
        raw_ber = _first_float(row, ["raw_ber", "layer_ber"], raw_ser)
        key = _join_key_from_row(row, loss_from_path)
        supplement = companion["by_key"].get(key, {})

        leak = _ci_float(row, "leak_EC_actual_bits", float("nan"))
        if not math.isfinite(leak) and "leak_EC_actual_bits" in supplement:
            try:
                leak = float(supplement["leak_EC_actual_bits"])
            except Exception:
                leak = float("nan")
        runtime = _ci_float(row, "runtime_s", float("nan"))
        if not math.isfinite(runtime) and "runtime_s" in supplement:
            try:
                runtime = float(supplement["runtime_s"])
            except Exception:
                runtime = float("nan")

        def supp_float(field: str) -> float:
            direct = _ci_float(row, field, float("nan"))
            if math.isfinite(direct):
                return direct
            if field in supplement:
                try:
                    val = float(supplement[field])
                    return val if math.isfinite(val) else float("nan")
                except Exception:
                    return float("nan")
            return float("nan")

        n_success = supp_float("n_frames_success")
        if not math.isfinite(n_success):
            verdict = _first_value(row, ["sidecar_verdict", "status"])
            if verdict is not None:
                n_success = float(n_frames_total) if str(verdict).strip().upper() == "PASS" else 0.0
        n_failed_decode = supp_float("n_frames_failed_decode")
        if not math.isfinite(n_failed_decode) and math.isfinite(n_success):
            n_failed_decode = max(0.0, float(n_frames_total) - n_success)
        n_failed_verify = supp_float("n_frames_failed_verify")
        if not math.isfinite(n_failed_verify):
            n_failed_verify = 0.0
        throughput_input = supp_float("throughput_input_bits_per_s")
        throughput_output = _ci_float(row, "throughput_output_bits_per_s", float("nan"))
        n_bits = frame_len_bits * max(1, n_frames_total)
        beta = compute_beta_eff_empirical(leak, n_bits, raw_ber) if math.isfinite(leak) else float("nan")
        if not math.isfinite(throughput_input) and runtime and math.isfinite(runtime) and runtime > 0:
            throughput_input = n_bits / runtime
        if not math.isfinite(throughput_output) and runtime and math.isfinite(runtime) and runtime > 0 and math.isfinite(n_success):
            throughput_output = (n_success * frame_len_bits) / runtime
        accepted = (n_success / n_frames_total) if n_frames_total and math.isfinite(n_success) else float("nan")
        post_ser = _first_float(row, ["post_ir_ser", "post_ser"], float("nan"))
        post_ber = _first_float(row, ["post_ir_ber", "post_ber"], float("nan"))
        source_note = (
            f"source={path}; checked_files={','.join(checked_names) if checked_names else 'none'}; "
            f"source_missing_fields={','.join(source_missing) if source_missing else 'none'}; "
            f"missing_after_companion_scan={','.join(missing_after_scan) if missing_after_scan else 'none'}"
        )
        rows.append({
            "dataset_id": _first_value(row, ["dataset_id"], dataset_id or f"polar_row_{idx}"),
            "source_path": str(path),
            "loss_db": _first_float(row, ["loss_db"], loss_from_path),
            "dimension": dim,
            "bin_width_ps": _first_value(row, ["bin_width_ps"], float("nan")),
            "n_eff_pairs": n_eff_pairs,
            "frame_len_symbols": frame_len_symbols,
            "frame_len_bits": frame_len_bits,
            "method": "polar_existing",
            "method_variant": method_variant,
            "method_status": "ok",
            "processing_rule_version": _first_value(row, ["processing_rule_version"], float("nan")),
            "pairing_path_tag": _first_value(row, ["pairing_path_tag"], float("nan")),
            "threshold_ps": _first_value(row, ["threshold_ps"], float("nan")),
            "effective_pairing_window_ps": _first_value(row, ["effective_pairing_window_ps"], float("nan")),
            "n_frames_total": n_frames_total,
            "n_frames_attempted": n_frames_total,
            "n_frames_success": n_success,
            "n_frames_failed_decode": n_failed_decode,
            "n_frames_failed_verify": n_failed_verify,
            "accepted_frame_fraction": accepted,
            "rejected_frame_fraction": (1.0 - accepted) if math.isfinite(accepted) else float("nan"),
            "raw_ser": raw_ser,
            "raw_ber": raw_ber,
            "post_ir_ser": post_ser,
            "post_ir_ber": post_ber,
            "leak_EC_actual_bits": leak,
            "leak_EC_per_frame": (leak / n_frames_total) if n_frames_total and math.isfinite(leak) else float("nan"),
            "leak_EC_per_input_bit": (leak / n_bits) if n_bits and math.isfinite(leak) else float("nan"),
            "beta_eff_empirical": beta,
            "runtime_s": runtime,
            "throughput_input_bits_per_s": throughput_input,
            "throughput_output_bits_per_s": throughput_output,
            "notes": source_note,
            "backend_status": "read_existing_file",
            "error_message": "",
        })
    if not rows:
        raise ValueError(f"No usable polar rows found in {path}")
    return pd.DataFrame(rows)

def _read_result(path: Path, batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult | None:
    df = pd.read_csv(path)
    if df.empty:
        return None
    work = df.copy()
    if "dimension" in work.columns:
        exact = work[pd.to_numeric(work["dimension"], errors="coerce") == int(batch.dimension)]
        if not exact.empty:
            work = exact
    if "bin_width_ps" in work.columns and "bin_width_ps" in batch.metadata:
        try:
            target_bw = float(batch.metadata["bin_width_ps"])
            exact_bw = work[pd.to_numeric(work["bin_width_ps"], errors="coerce") == target_bw]
            if not exact_bw.empty:
                work = exact_bw
        except Exception:
            pass
    if "dataset_id" in work.columns:
        filt = work[work["dataset_id"].astype(str) == str(batch.dataset_id)]
        if not filt.empty:
            work = filt
    if work.empty:
        return None
    row = work.iloc[0]
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(batch.alice_symbols.shape[0])
    n_bits = int(batch.alice_symbols.size) * bps
    raw_ser = _first_float(row, ["raw_ser", "map_ser"], frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols))
    raw_ber = _first_float(row, ["raw_ber", "layer_ber"], bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension)))
    leak = _first_float(row, ["leak_EC_actual_bits", "total_leak_ec_bits", "total_leak_EC_bits", "leak_ec_bits_or_proxy"], float("nan"))
    success_rate = _first_float(row, ["block_success_rate", "accepted_frame_fraction"], float("nan"))
    if not math.isfinite(success_rate):
        verdict = _first_value(row, ["sidecar_verdict", "status"])
        if verdict is not None:
            success_rate = 1.0 if str(verdict).strip().upper() == "PASS" else 0.0
    n_success = int(round(success_rate * n_frames)) if math.isfinite(success_rate) else 0
    runtime = _first_float(row, ["runtime_s", "runtime_sec", "elapsed_s"], float("nan"))
    missing = _missing_fields(list(work.columns), ["raw_ser", "leak_EC_actual_bits", "runtime_s"])
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="polar_existing",
        method_variant=cfg.method_variant,
        frame_len_symbols=batch.frame_len_symbols,
        frame_len_bits=batch.frame_len_symbols * bps,
        n_frames_total=n_frames,
        n_frames_attempted=n_frames,
        n_frames_success=n_success,
        n_frames_failed_decode=max(0, n_frames - n_success),
        n_frames_failed_verify=0,
        raw_ser=raw_ser,
        raw_ber=raw_ber,
        post_ir_ser=0.0 if n_success else raw_ser,
        post_ir_ber=0.0 if n_success else raw_ber,
        leak_EC_actual_bits=leak,
        leak_EC_per_frame=(leak / n_frames) if n_frames and math.isfinite(leak) else float("nan"),
        leak_EC_per_input_bit=(leak / n_bits) if n_bits and math.isfinite(leak) else float("nan"),
        beta_eff_empirical=compute_beta_eff_empirical(leak, n_bits, raw_ber) if math.isfinite(leak) else float("nan"),
        runtime_s=runtime,
        throughput_input_bits_per_s=(n_bits / runtime) if runtime and math.isfinite(runtime) and runtime > 0 else float("nan"),
        throughput_output_bits_per_s=((n_success * batch.frame_len_symbols * bps) / runtime) if runtime and math.isfinite(runtime) and runtime > 0 else float("nan"),
        metadata={
            "method_status": "ok",
            "source_path": str(path),
            "backend_status": "read_existing_file",
            "notes": f"source={path}; missing_fields={','.join(missing) if missing else 'none'}",
        },
    )


def _unavailable(batch: FrameBatch, cfg: IRRunConfig, message: str) -> IRRunResult:
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(batch.alice_symbols.shape[0])
    raw_ser = frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols)
    raw_ber = bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension))
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="polar_existing",
        method_variant=cfg.method_variant,
        frame_len_symbols=batch.frame_len_symbols,
        frame_len_bits=batch.frame_len_symbols * bps,
        n_frames_total=n_frames,
        n_frames_attempted=0,
        n_frames_success=0,
        n_frames_failed_decode=0,
        n_frames_failed_verify=0,
        raw_ser=raw_ser,
        raw_ber=raw_ber,
        post_ir_ser=raw_ser,
        post_ir_ber=raw_ber,
        leak_EC_actual_bits=float("nan"),
        leak_EC_per_frame=float("nan"),
        leak_EC_per_input_bit=float("nan"),
        beta_eff_empirical=float("nan"),
        runtime_s=float("nan"),
        throughput_input_bits_per_s=float("nan"),
        throughput_output_bits_per_s=float("nan"),
        metadata={"method_status": "unavailable", "backend_status": "no_existing_output", "error_message": message},
    )


def resolve_polar_output_from_metadata(metadata: dict[str, Any]) -> Path | None:
    explicit = _as_path(metadata.get("polar_existing_output")) or _as_path(metadata.get("polar_results_file"))
    if explicit:
        return explicit if explicit.exists() else None
    root = _as_path(metadata.get("polar_results_root"))
    candidates = locate_existing_polar_outputs([root] if root else None)
    return select_polar_output(candidates)


def run_polar_existing(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
    mode = str(batch.metadata.get("polar_existing_mode") or "read").lower()
    selected = resolve_polar_output_from_metadata(batch.metadata)
    candidates = [selected] if selected else []
    for path in candidates:
        if path and path.exists():
            result = _read_result(path, batch, cfg)
            if result is not None:
                return result
    if mode == "cli":
        start = time.perf_counter()
        out_dir = default_output_dir() / "polar_existing_cli"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_csv = out_dir / "real_polar_max_pie_grid.csv"
        cmd = [sys.executable, str(repo_root() / "experiments" / "run_real_polar_max_pie.py"), "--out-csv", str(out_csv)]
        proc = subprocess.run(cmd, cwd=str(repo_root()))
        if proc.returncode != 0:
            return _unavailable(batch, cfg, f"polar CLI failed rc={proc.returncode}")
        result = _read_result(out_csv, batch, cfg)
        if result is not None:
            result.runtime_s = time.perf_counter() - start
            result.metadata["method_status"] = "ok"
            return result
    searched = batch.metadata.get("polar_results_root") or DEFAULT_POLAR_RESULTS_ROOT
    return _unavailable(batch, cfg, f"No existing polar output matched search root/file: {searched}")
