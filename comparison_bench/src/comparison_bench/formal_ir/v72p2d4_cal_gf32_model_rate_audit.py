"""V72P2D4 CAL GF32 model rate audit — CAL-only descriptive audit.

Reuses the frozen V72P2D3 model math (mapping, stage priors, log losses,
resubstitution, 4-fold held-out, rate budgets) for CAL frames 702..1725
only. No VAL fit, no iterative kernel call, no parquet VAL read for the
model, no authorization flag, single audit output only.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from comparison_bench.formal_ir.v72p2d3_gf32_contrast import (
        CAL_END,
        CAL_START,
        PREP_LIMIT_S,
        G_LIMIT_S,
        INV_LIMIT_S,
        N,
        PREPARE_LAM,
        Q,
        Q_SUB,
        R5_CV_SEED,
        R5_H1_BITS,
        R5_L2_TOTAL_BITS,
        R5_N,
        R5_N_FOLDS,
        R5_RATE,
        R5_TOTAL_BITS,
        REAL_CAL_IDS,
        REGISTRY_SCHEMA,
        REQUIRED_PARQUET_COLUMNS,
        RSS_LIMIT_BYTES,
        SESSION_ID,
        build_canonical_counts,
        build_stage1_P,
        build_stage2_P,
        cal_4fold_cv_heldout_nll,
        cal_resubstitution_nll_descriptive,
        ce_joint_log2,
        ce_stage1_log2,
        ce_stage2_log2,
        rate_audit_r5,
        symbols_to_layers,
        validate_prepare_registry,
    )
except ImportError:  # pragma: no cover
    from comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast import (  # type: ignore[no-redef]
        CAL_END,
        CAL_START,
        PREP_LIMIT_S,
        G_LIMIT_S,
        INV_LIMIT_S,
        N,
        PREPARE_LAM,
        Q,
        Q_SUB,
        R5_CV_SEED,
        R5_H1_BITS,
        R5_L2_TOTAL_BITS,
        R5_N,
        R5_N_FOLDS,
        R5_RATE,
        R5_TOTAL_BITS,
        REAL_CAL_IDS,
        REGISTRY_SCHEMA,
        REQUIRED_PARQUET_COLUMNS,
        RSS_LIMIT_BYTES,
        SESSION_ID,
        build_canonical_counts,
        build_stage1_P,
        build_stage2_P,
        cal_4fold_cv_heldout_nll,
        cal_resubstitution_nll_descriptive,
        ce_joint_log2,
        ce_stage1_log2,
        ce_stage2_log2,
        rate_audit_r5,
        symbols_to_layers,
        validate_prepare_registry,
    )

CYCLE_ID = "V72P2D4-CAL-GF32-MODEL-RATE"
AUDIT_SCHEMA = "v72p2d4_cal_gf32_model_rate_audit_v1"
MANIFEST_SCHEMA = "v72p2d4_cal_gf32_model_rate_manifest_v1"
OUT_DIR_NAME = "v72p2d4_cal_gf32_model_rate_audit_20260905"
DEFAULT_LAM = float(PREPARE_LAM)
CV_SEED = int(R5_CV_SEED)
N_FOLDS = int(R5_N_FOLDS)
# ponytail: scalar-only summary; shapes are frozen scalars, not data.
SUMMARY_BANNED_KEYS = (
    "alice_symbols",
    "bob_symbols",
    "prior_logp",
    "syndrome_target",
    "syndrome_observed",
    "syndrome_bytes",
    "candidate",
    "messages",
    "check_to_variable",
    "alice_bits",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _workspace_root() -> Path:
    return (_repo_root() / "workspace").resolve()


def _production_root() -> Path:
    return (
        _repo_root() / "comparison_bench" / "outputs_comparison" / OUT_DIR_NAME
    ).resolve()


def validate_output_target(out_dir: str | Path) -> Path:
    """D4 output guard: exact pre-registered root or fresh workspace dir only.

    Existing paths refuse; any path containing run_01 refuses; any other
    outside path refuses. Comparison is resolve() equality/relative_to only.
    """
    raw = Path(out_dir)
    if not raw.is_absolute():
        cand = (_repo_root() / raw).resolve()
    else:
        cand = raw.resolve()
    prod = _production_root()
    ws = _workspace_root()
    if cand.exists():
        raise FileExistsError(f"output directory already exists: {cand}")
    if cand.name == "run_01" or "run_01" in cand.parts:
        raise ValueError("audit output must not be run_01")
    if cand == prod:
        return cand
    try:
        cand.relative_to(ws)
    except ValueError as exc:
        raise ValueError(
            "audit output must be the pre-registered root or under workspace/"
        ) from exc
    return cand


def _resolve_parquet(raw: Any, registry_dir: Path) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("registry parquet_path must be a non-empty string")
    cand = Path(raw.strip())
    if not cand.is_absolute():
        cand = (registry_dir / cand).resolve()
        if not cand.exists():
            alt = (_repo_root() / raw.strip()).resolve()
            if alt.exists():
                cand = alt
    return cand.resolve()


def load_cal_arrays(
    parquet_path: str | Path, cal_ids: list[int] | None = None
) -> dict[str, Any]:
    """CAL-only filtered read: 1024 frames x 256 pairs, symbols 0..1023."""
    import pandas as pd

    cal = list(REAL_CAL_IDS) if cal_ids is None else [int(v) for v in cal_ids]
    if cal != [int(v) for v in REAL_CAL_IDS]:
        raise ValueError("CAL ids must be the frozen 702..1725 sequence")
    cols = list(REQUIRED_PARQUET_COLUMNS)
    try:
        df = pd.read_parquet(Path(parquet_path), columns=cols)
    except Exception as exc:
        raise ValueError(f"parquet unreadable: {type(exc).__name__}: {exc}") from exc
    n_read = int(len(df))
    if set(df.columns) != set(cols):
        raise ValueError(f"parquet columns must be exactly {cols}")
    if int(df.isna().sum().sum()) != 0:
        raise ValueError("parquet contains NaN")
    for col in cols:
        vals = df[col].to_numpy()
        if not np.all(vals == np.floor(vals.astype(np.float64))):
            raise ValueError(f"parquet column {col} must be integral")
    keep = df[df["frame_id"].isin(cal)]
    n_retained = int(len(keep))
    if n_retained != 1024 * 256:
        raise ValueError(f"CAL retained rows must be 262144, got {n_retained}")
    bundle: dict[int, dict[str, np.ndarray]] = {}
    for fid in cal:
        sub = keep[keep["frame_id"] == fid].sort_values("pair_idx")
        if len(sub) != 256:
            raise ValueError(f"frame {fid} must hold 256 rows")
        pairs = sub["pair_idx"].to_numpy(dtype=np.int64)
        if not np.array_equal(pairs, np.arange(256, dtype=np.int64)):
            raise ValueError(f"frame {fid} pair_idx must be sorted 0..255 with no dup")
        for col in ("alice_symbol", "bob_symbol"):
            syms = sub[col].to_numpy(dtype=np.int64)
            if np.any(syms < 0) or np.any(syms >= Q):
                raise ValueError(f"frame {fid} {col} outside 0..1023")
        bundle[int(fid)] = {
            "alice_symbols": sub["alice_symbol"].to_numpy(dtype=np.int64),
            "bob_symbols": sub["bob_symbol"].to_numpy(dtype=np.int64),
        }
    alice_cal = np.concatenate([bundle[f]["alice_symbols"] for f in cal])
    bob_cal = np.concatenate([bundle[f]["bob_symbols"] for f in cal])
    return {
        "n_read_rows": n_read,
        "n_retained_rows": n_retained,
        "n_cal_frames": len(cal),
        "n_cal_symbols": int(alice_cal.size),
        "alice_cal": alice_cal.astype(np.int64),
        "bob_cal": bob_cal.astype(np.int64),
        "cal_bundle": bundle,
    }


def fit_cal_model(
    alice_cal: np.ndarray, bob_cal: np.ndarray, lam: float = DEFAULT_LAM
) -> dict[str, Any]:
    """CAL-only fit: P1(high|B), P2(low|high,B), canonical counts."""
    a = np.asarray(alice_cal, dtype=np.int64).reshape(-1)
    b = np.asarray(bob_cal, dtype=np.int64).reshape(-1)
    if a.shape != b.shape or a.size == 0:
        raise ValueError("CAL arrays must be non-empty equal length")
    if np.any(a < 0) or np.any(a >= Q) or np.any(b < 0) or np.any(b >= Q):
        raise ValueError("CAL symbols outside 0..1023")
    lam_f = float(lam)
    if not np.isfinite(lam_f) or lam_f <= 0:
        raise ValueError("lam must be finite positive")
    a_low, a_high = symbols_to_layers(a)
    p1 = build_stage1_P(b, a_high, lam_f, n_b_states=Q, q_sub=Q_SUB)
    p2 = build_stage2_P(a_high, b, a_low, lam_f, n_b_states=Q, q_sub=Q_SUB)
    counts = build_canonical_counts(a, b, q=Q)
    return {
        "P1": p1,
        "P2": p2,
        "counts": counts,
        "lam": float(lam_f),
        "n_cal": int(a.size),
    }


def _sample_rss(rss_reader: Any = None) -> int | None:
    if rss_reader is not None:
        try:
            return int(rss_reader())
        except Exception:
            return None
    try:
        import psutil as _psutil
        import os as _os

        return int(_psutil.Process(_os.getpid()).memory_info().rss)
    except Exception:
        return None


def build_audit_summary(
    *,
    registry_path: str | Path,
    loaded: dict[str, Any],
    fit: dict[str, Any],
    resub: dict[str, Any],
    cv: dict[str, Any],
    rate: dict[str, Any],
    prep_wall_s: float,
    g_wall_s: float,
    inv_wall_s: float,
    peak_rss: int | None,
) -> dict[str, Any]:
    """Assemble the scalar-only audit summary (no data rows or values)."""
    return {
        "schema": AUDIT_SCHEMA,
        "status": "READY",
        "cycle": CYCLE_ID,
        "session": SESSION_ID,
        "registry": str(Path(registry_path).resolve()),
        "cal": [int(CAL_START), int(CAL_END)],
        "rows": {
            "n_cal_frames": int(loaded["n_cal_frames"]),
            "n_cal_symbols": int(loaded["n_cal_symbols"]),
            "n_read_rows": int(loaded["n_read_rows"]),
            "n_retained_rows": int(loaded["n_retained_rows"]),
        },
        "lambda": float(fit["lam"]),
        "cv_seed": int(CV_SEED),
        "n_folds": int(N_FOLDS),
        "prior_shapes": {"P1": [int(Q), int(Q_SUB)], "P2": [int(Q_SUB), int(Q), int(Q_SUB)], "counts": [int(Q), int(Q)]},
        "resub": {
            "ce_l1": float(resub["ce_l1"]),
            "ce_l2_oracle": float(resub["ce_l2_oracle"]),
            "ce_joint": float(resub["ce_joint"]),
            "n": int(resub["n"]),
            "kind": str(resub.get("kind", "cal_resubstitution_nll_descriptive")),
        },
        "cv": {
            "mean_ce_l1": float(cv["mean_ce_l1"]),
            "mean_ce_l2_oracle": float(cv["mean_ce_l2_oracle"]),
            "mean_ce_joint": float(cv["mean_ce_joint"]),
            "n_cal": int(cv["n_cal"]),
            "n_folds": int(cv["n_folds"]),
            "seed": int(cv["seed"]),
            "folds": [
                {
                    "fold": int(f["fold"]),
                    "n_train": int(f["n_train"]),
                    "n_heldout": int(f["n_heldout"]),
                    "ce_l1": float(f["ce_l1"]),
                    "ce_l2_oracle": float(f["ce_l2_oracle"]),
                    "ce_joint": float(f["ce_joint"]),
                }
                for f in cv["folds"]
            ],
        },
        "rate": {
            "n": int(rate["n"]),
            "budget": dict(rate["budget"]),
            "layers": {
                k: {
                    "ce_bit_per_symbol": float(v["ce_bit_per_symbol"]),
                    "required_bits": float(v["required_bits"]),
                    "available_bits": float(v["available_bits"]),
                    "margin_bits": float(v["margin_bits"]),
                    "ratio": float(v["ratio"]),
                }
                for k, v in rate["layers"].items()
            },
            "status": str(rate["status"]),
            "note": str(rate["note"]),
        },
        "rate_status": str(rate["status"]),
        "wall": {"prep_s": float(prep_wall_s), "g_s": float(g_wall_s), "inv_s": float(inv_wall_s)},
        "rss": {"peak_bytes": None if peak_rss is None else int(peak_rss)},
        "decoder_calls": 0,
        "published_bits": 0,
        "formal": False,
        "cal_only": True,
    }


def _check_summary_allowed(summary: dict[str, Any]) -> None:
    payload = json.dumps(summary, ensure_ascii=False)
    lowered = payload.lower()
    for banned in SUMMARY_BANNED_KEYS:
        if banned.lower() in lowered:
            raise ValueError(f"audit summary must not store {banned}")
    if '"protocol"' in lowered:
        raise ValueError("audit summary must not define protocol")


def write_audit_outputs(
    out_dir: str | Path,
    summary: dict[str, Any],
) -> Path:
    """Write exactly manifest.json, audit.json, table.csv, report.md."""
    import csv

    out = validate_output_target(out_dir)
    if not isinstance(summary, dict):
        raise ValueError("summary must be a mapping")
    if summary.get("schema") != AUDIT_SCHEMA:
        raise ValueError(f"summary schema must be {AUDIT_SCHEMA}")
    if summary.get("cycle") != CYCLE_ID:
        raise ValueError("summary belongs to another cycle")
    _check_summary_allowed(summary)
    out.mkdir(parents=True, exist_ok=False)
    rate = summary["rate"]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "cycle": CYCLE_ID,
        "session": SESSION_ID,
        "cal": [int(CAL_START), int(CAL_END)],
        "model_reuse": "v72p2d3_gf32_contrast stage priors/CE/CV/rate",
        "mapping": "low=bits0..4/high=bits5..9/bit0=LSB/symbol=low+32*high",
        "field": {"q": int(Q_SUB), "poly": 37},
        "budget": dict(rate["budget"]),
        "rate_status": str(rate["status"]),
        "cal_only": True,
        "decoder_calls": 0,
        "formal": False,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "audit.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fields = ["layer", "ce_bit_per_symbol", "required_bits", "available_bits", "margin_bits", "ratio"]
    with (out / "table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for layer in ("l1", "l2_oracle", "joint"):
            row = rate["layers"][layer]
            writer.writerow(
                {
                    "layer": layer,
                    "ce_bit_per_symbol": row["ce_bit_per_symbol"],
                    "required_bits": row["required_bits"],
                    "available_bits": row["available_bits"],
                    "margin_bits": row["margin_bits"],
                    "ratio": row["ratio"],
                }
            )
    lines = [
        "# V72P2D4 CAL GF32 model rate audit (CAL-only)",
        "",
        "Descriptive only; not a lower bound; not a failure verdict.",
        "",
        f"- cycle: `{CYCLE_ID}`",
        f"- session: `{SESSION_ID}`",
        f"- cal: `{CAL_START}..{CAL_END}`",
        f"- n_cal_symbols: `{summary['rows']['n_cal_symbols']}`",
        f"- resub ce_joint: `{summary['resub']['ce_joint']:.6f}` bit/symbol",
        f"- cv mean ce_joint: `{summary['cv']['mean_ce_joint']:.6f}` bit/symbol",
        f"- rate: `{summary['rate_status']}`",
    ]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    names = {item.name for item in out.iterdir()}
    if names != {"manifest.json", "audit.json", "table.csv", "report.md"}:
        raise RuntimeError("audit output root must contain exactly four files")
    return out


def run_cal_audit(
    *,
    registry_path: str | Path,
    out_dir: str | Path,
    lam: float = DEFAULT_LAM,
    clock: Any = None,
    rss_reader: Any = None,
) -> dict[str, Any]:
    """CAL-only audit chain: guard -> registry -> CAL load -> fit -> audit -> files.

    Takes only in-memory CAL arrays for the model; never fits VAL, never
    touches the iterative kernel, never publishes bits.
    """
    now = clock if clock is not None else time.monotonic
    inv_start = float(now())
    rss_peak: list[int] = []

    def _sample() -> None:
        value = _sample_rss(rss_reader)
        if value is not None:
            rss_peak.append(int(value))

    _sample()
    prep_start = float(now())
    out = validate_output_target(out_dir)
    try:
        reg_raw = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"registry file is missing: {registry_path}") from exc
    validated = validate_prepare_registry(reg_raw, registry_path)
    loaded = load_cal_arrays(validated["parquet_path"], validated["cal_ids"])
    fit = fit_cal_model(loaded["alice_cal"], loaded["bob_cal"], float(lam))
    prep_wall = float(now()) - prep_start
    _sample()
    if prep_wall > float(PREP_LIMIT_S):
        raise TimeoutError(f"prep wall {prep_wall:.3f}s exceeds {PREP_LIMIT_S}s")
    g_start = float(now())
    a_low, a_high = symbols_to_layers(loaded["alice_cal"])
    resub = cal_resubstitution_nll_descriptive(
        fit["P1"], fit["P2"], loaded["bob_cal"], a_high, a_low
    )
    cv = cal_4fold_cv_heldout_nll(
        loaded["alice_cal"], loaded["bob_cal"], float(lam),
        n_folds=int(N_FOLDS), seed=int(CV_SEED),
    )
    rate = rate_audit_r5(resub["ce_l1"], resub["ce_l2_oracle"], resub["ce_joint"])
    g_wall = float(now()) - g_start
    _sample()
    if g_wall > float(G_LIMIT_S):
        raise TimeoutError(f"audit wall {g_wall:.3f}s exceeds {G_LIMIT_S}s")
    peak = max(rss_peak) if rss_peak else None
    inv_wall = float(now()) - inv_start
    if inv_wall > float(INV_LIMIT_S):
        raise TimeoutError(f"invocation wall {inv_wall:.3f}s exceeds {INV_LIMIT_S}s")
    if peak is not None and peak >= int(RSS_LIMIT_BYTES):
        raise MemoryError("peak RSS exceeds 2GiB")
    summary = build_audit_summary(
        registry_path=registry_path,
        loaded=loaded,
        fit=fit,
        resub=resub,
        cv=cv,
        rate=rate,
        prep_wall_s=prep_wall,
        g_wall_s=g_wall,
        inv_wall_s=inv_wall,
        peak_rss=peak,
    )
    written = write_audit_outputs(out, summary)
    _sample()
    return {
        "status": "READY",
        "cycle": CYCLE_ID,
        "session": SESSION_ID,
        "rate_status": str(rate["status"]),
        "n_cal_frames": int(loaded["n_cal_frames"]),
        "n_cal_symbols": int(loaded["n_cal_symbols"]),
        "n_read_rows": int(loaded["n_read_rows"]),
        "n_retained_rows": int(loaded["n_retained_rows"]),
        "resub_ce_joint": float(resub["ce_joint"]),
        "cv_mean_ce_joint": float(cv["mean_ce_joint"]),
        "decoder_calls": 0,
        "published_bits": 0,
        "formal": False,
        "cal_only": True,
        "prep_wall_s": float(prep_wall),
        "g_wall_s": float(g_wall),
        "inv_wall_s": float(inv_wall),
        "peak_rss_bytes": peak,
        "output": str(written.resolve()),
    }
