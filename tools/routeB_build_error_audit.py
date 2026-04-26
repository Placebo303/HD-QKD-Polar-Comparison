#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from _longrun_common import candidate_dir_for_loss
from _security_round_common import candidate_sidecar_root, infer_loss_db_from_path, point_id, write_summary


FORMULA_TAG = "union_bound_over_blocks_universal_hash"
MODEL_SOURCE_TAG = "same_routeA_formal_sidecar_a_eff_b_eff"
EVAL_SOURCE_TAG = "routeA_formal_replay_blocks_same_point"
REUSE_RISK_TAG = "same_a_eff_b_eff_for_model_and_eval"
ERASURE_SOURCE_TAG = "sidecar_frame_accounting_proxy_not_symbol_erasure"
P_CLIP = 1e-6


def _h2(p: float) -> float:
    if not math.isfinite(p):
        return float("nan")
    p = min(1.0, max(0.0, float(p)))
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p)))


def _binary_mi(p01: float, p10: float, prior_a1: float) -> float:
    if not all(math.isfinite(x) for x in (p01, p10, prior_a1)):
        return float("nan")
    pi1 = min(1.0, max(0.0, float(prior_a1)))
    pi0 = 1.0 - pi1
    py1 = pi0 * p01 + pi1 * (1.0 - p10)
    return float(_h2(py1) - pi0 * _h2(p01) - pi1 * _h2(p10))


def _clip_prob(p: float) -> tuple[float, int]:
    if not math.isfinite(p):
        return float("nan"), 0
    pc = min(1.0 - P_CLIP, max(P_CLIP, float(p)))
    return float(pc), int(abs(pc - float(p)) > 0.0)


def _bit_layer(symbols: np.ndarray, *, dimension: int, layer_idx: int) -> np.ndarray:
    bits = int(round(math.log2(int(dimension))))
    shift = bits - 1 - int(layer_idx)
    arr = np.asarray(symbols, dtype=np.int64)
    return ((arr >> shift) & 1).astype(np.uint8, copy=False)


def _safe_float(v: Any) -> float:
    try:
        out = float(v)
    except Exception:
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _load_master(routea_dir: Path) -> pd.DataFrame:
    p = routea_dir / "cross_loss_security_master_table.csv"
    if not p.exists():
        raise SystemExit(f"missing Route A cross-loss master: {p}")
    master = pd.read_csv(p)
    if "point_id" not in master.columns:
        master["point_id"] = master.apply(
            lambda r: point_id(loss_db=int(r["loss_db"]), dimension=int(r["dimension"]), bin_width_ps=int(r["bin_width_ps"])),
            axis=1,
        )
    return master


def _load_replay_eval(routea_dir: Path, loss_db: int) -> pd.DataFrame:
    stage1 = routea_dir / f"loss_{int(loss_db)}dB" / "stage1_actual_ir"
    block_path = stage1 / "actual_ir_block_table.csv"
    layer_path = stage1 / "replay_index_layer_table.csv"
    if not block_path.exists() or not layer_path.exists():
        return pd.DataFrame()
    block = pd.read_csv(block_path)
    layer = pd.read_csv(layer_path)
    ok = block[block["replay_status"].astype(str).str.startswith("ok")].copy()
    for c in ("decode_fail_flag", "block_success_flag"):
        ok[c] = pd.to_numeric(ok.get(c), errors="coerce").fillna(0)
    agg = ok.groupby(["point_id", "layer_id"], as_index=False).agg(
        replay_ok_block_count=("block_index", "count"),
        decode_fail_count_layer=("decode_fail_flag", "sum"),
        block_success_count_layer=("block_success_flag", "sum"),
    )
    layer_keep = layer[["point_id", "layer_id", "layer_block_symbols", "layer_replay_ready_tag"]].copy()
    layer_keep["layer_block_symbols"] = pd.to_numeric(layer_keep["layer_block_symbols"], errors="coerce")
    out = agg.merge(layer_keep, on=["point_id", "layer_id"], how="left")
    out["n_pairs_eval_available"] = (
        pd.to_numeric(out["replay_ok_block_count"], errors="coerce").fillna(0)
        * pd.to_numeric(out["layer_block_symbols"], errors="coerce").fillna(0)
    ).astype(int)
    out["decoder_fail_rate_oracle_layer"] = np.where(
        out["replay_ok_block_count"] > 0,
        out["decode_fail_count_layer"] / out["replay_ok_block_count"],
        np.nan,
    )
    out["block_success_rate_layer"] = np.where(
        out["replay_ok_block_count"] > 0,
        out["block_success_count_layer"] / out["replay_ok_block_count"],
        np.nan,
    )
    return out


def _symbol_offset_row(*, loss_db: int, d: int, bw: int, pid: str, a: np.ndarray, b: np.ndarray, master_row: dict[str, Any]) -> dict[str, Any]:
    n = int(min(a.size, b.size))
    q = int(d)
    if n <= 0:
        return {
            "loss_db": loss_db,
            "dimension": d,
            "bin_width_ps": bw,
            "point_id": pid,
            "n_pairs_modeling": 0,
            "symbol_match_rate": np.nan,
            "symbol_substitution_rate": np.nan,
            "offset_like_mismatch_flag": 0,
        }
    aa = np.clip(np.asarray(a[:n], dtype=np.int64), 0, q - 1)
    bb = np.clip(np.asarray(b[:n], dtype=np.int64), 0, q - 1)
    delta = (bb - aa) % q
    hist = np.bincount(delta, minlength=q)
    order = np.argsort(hist)[::-1]
    mismatch = aa != bb
    mismatch_count = int(np.sum(mismatch))
    nonzero_order = [int(x) for x in order if int(x) != 0]
    nonzero_top_delta = nonzero_order[0] if nonzero_order else -1
    nonzero_top_delta_count = int(hist[nonzero_top_delta]) if nonzero_top_delta >= 0 else 0
    nonzero_top_frac_among_mismatch = float(nonzero_top_delta_count / mismatch_count) if mismatch_count > 0 else 0.0
    nn = {0}
    if q > 1:
        nn.update({1, q - 1})
    if q > 2:
        nn.update({2, q - 2})
    row = {
        "loss_db": loss_db,
        "dimension": d,
        "bin_width_ps": bw,
        "point_id": pid,
        "n_pairs_modeling": n,
        "symbol_match_rate": float(np.mean(~mismatch)),
        "symbol_substitution_rate": float(np.mean(mismatch)),
        "mismatch_count": mismatch_count,
        "nonzero_top_delta": nonzero_top_delta,
        "nonzero_top_delta_frac": float(nonzero_top_delta_count / n),
        "nonzero_top_delta_frac_among_mismatch": nonzero_top_frac_among_mismatch,
        "near_neighbor_delta_frac": float(sum(int(hist[k]) for k in nn) / n),
        "offset_like_mismatch_flag": int(nonzero_top_frac_among_mismatch >= 0.50),
        "erasure_proxy_rate": _safe_float(master_row.get("rejected_frame_fraction")),
        "erasure_source_tag": ERASURE_SOURCE_TAG,
    }
    for idx in range(3):
        key = int(order[idx]) if idx < len(order) else -1
        row[f"top_delta_{idx}"] = key
        row[f"top_delta_{idx}_frac"] = float(hist[key] / n) if key >= 0 else np.nan
    return row


def _confusion_rows_for_point(
    *,
    loss_db: int,
    d: int,
    bw: int,
    pid: str,
    a: np.ndarray,
    b: np.ndarray,
    eval_by_layer: pd.DataFrame,
    master_row: dict[str, Any],
) -> list[dict[str, Any]]:
    n = int(min(a.size, b.size))
    if n <= 0:
        return []
    bits = int(round(math.log2(int(d))))
    eval_map = {
        int(r["layer_id"]): r
        for _, r in eval_by_layer[eval_by_layer["point_id"].astype(str).eq(pid)].iterrows()
    }
    rows: list[dict[str, Any]] = []
    aa = np.asarray(a[:n], dtype=np.int64)
    bb = np.asarray(b[:n], dtype=np.int64)
    for layer_idx in range(bits):
        abit = _bit_layer(aa, dimension=d, layer_idx=layer_idx)
        bbit = _bit_layer(bb, dimension=d, layer_idx=layer_idx)
        n00 = int(np.sum((abit == 0) & (bbit == 0)))
        n01 = int(np.sum((abit == 0) & (bbit == 1)))
        n10 = int(np.sum((abit == 1) & (bbit == 0)))
        n11 = int(np.sum((abit == 1) & (bbit == 1)))
        count_a0 = n00 + n01
        count_a1 = n10 + n11
        min_cond = min(count_a0, count_a1)
        p01_raw = float(n01 / count_a0) if count_a0 > 0 else np.nan
        p10_raw = float(n10 / count_a1) if count_a1 > 0 else np.nan
        p01_model, p01_clip = _clip_prob(p01_raw)
        p10_model, p10_clip = _clip_prob(p10_raw)
        ber = float((n01 + n10) / n)
        p_a1 = float(count_a1 / n)
        asym_mi = _binary_mi(p01_model, p10_model, 0.5)
        bsc_cap = 1.0 - _h2(ber)
        eval_row = eval_map.get(layer_idx)
        n_eval = int(_safe_float(eval_row.get("n_pairs_eval_available"))) if eval_row is not None else 0
        dec_fail = _safe_float(eval_row.get("decoder_fail_rate_oracle_layer")) if eval_row is not None else np.nan
        blk_success = _safe_float(eval_row.get("block_success_rate_layer")) if eval_row is not None else np.nan
        insufficient = int(n < 4096 or min_cond < 512)
        conservative_ok = int(n >= 8192 and min_cond >= 1024)
        clipped = int(p01_clip or p10_clip)
        eligible_b2 = int(insufficient == 0)
        eligible_b3 = int(eligible_b2 == 1 and clipped == 0 and math.isfinite(dec_fail))
        rows.append(
            {
                "loss_db": loss_db,
                "dimension": d,
                "bin_width_ps": bw,
                "point_id": pid,
                "layer_idx": layer_idx,
                "n_pairs": n,
                "n_pairs_modeling": n,
                "n_pairs_eval_available": n_eval,
                "modeling_sample_source_tag": MODEL_SOURCE_TAG,
                "eval_sample_source_tag": EVAL_SOURCE_TAG,
                "sample_reuse_bias_risk_tag": REUSE_RISK_TAG,
                "n00": n00,
                "n01": n01,
                "n10": n10,
                "n11": n11,
                "min_count_a0": count_a0,
                "min_count_a1": count_a1,
                "min_conditional_count": min_cond,
                "ber_symmetric": ber,
                "p01_raw": p01_raw,
                "p10_raw": p10_raw,
                "p01_model": p01_model,
                "p10_model": p10_model,
                "p01_clipped_flag": p01_clip,
                "p10_clipped_flag": p10_clip,
                "p_a0": float(count_a0 / n),
                "p_a1": p_a1,
                "p_a0_empirical": float(count_a0 / n),
                "p_a1_empirical": p_a1,
                "asymmetry_abs_gap": float(abs(p01_model - p10_model)) if math.isfinite(p01_model) and math.isfinite(p10_model) else np.nan,
                "asymmetry_ratio": float(max(p01_model, p10_model) / max(P_CLIP, min(p01_model, p10_model))) if math.isfinite(p01_model) and math.isfinite(p10_model) else np.nan,
                "binary_mutual_info_empirical": _binary_mi(p01_model, p10_model, p_a1),
                "uniform_prior_asym_mi": asym_mi,
                "bsc_capacity_1_minus_h2_ber": bsc_cap,
                "capacity_delta_asym_minus_bsc": asym_mi - bsc_cap,
                "capacity_delta_abs": abs(asym_mi - bsc_cap),
                "layer_ber_legacy": ber,
                "decoder_fail_rate_oracle_layer": dec_fail,
                "block_success_rate_layer": blk_success,
                "insufficient_for_model_flag": insufficient,
                "conservative_8192_1024_eligible_flag": conservative_ok,
                "eligible_for_B2_flag": eligible_b2,
                "eligible_for_B3_flag": eligible_b3,
                "audit_source_tag": "routeB_error_audit_v1",
                "epsilon_EC_bound_point": _safe_float(master_row.get("epsilon_EC_bound")),
                "decoder_fail_rate_oracle_point": _safe_float(master_row.get("decoder_fail_rate_oracle")),
            }
        )
    return rows


def _candidate_dirs(args: argparse.Namespace) -> list[Path]:
    if args.candidate_dirs:
        return [Path(p) for p in args.candidate_dirs]
    return [candidate_dir_for_loss(x) for x in (6, 10, 16, 20)]


def _process_point_spec(
    *,
    cand: Path,
    loss_db: int,
    d: int,
    bw: int,
    eval_by_layer: pd.DataFrame,
    master_row: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]:
    pid = point_id(loss_db=loss_db, dimension=d, bin_width_ps=bw)
    sidecar = candidate_sidecar_root(cand, d, bw)
    a_path = sidecar / "a_eff.npy"
    b_path = sidecar / "b_eff.npy"
    if not a_path.exists() or not b_path.exists():
        return None, [], f"{pid}: missing a_eff/b_eff"
    a = np.load(a_path, mmap_mode="r")
    b = np.load(b_path, mmap_mode="r")
    symbol_row = _symbol_offset_row(loss_db=loss_db, d=d, bw=bw, pid=pid, a=a, b=b, master_row=master_row)
    layer_rows = _confusion_rows_for_point(
        loss_db=loss_db,
        d=d,
        bw=bw,
        pid=pid,
        a=a,
        b=b,
        eval_by_layer=eval_by_layer,
        master_row=master_row,
    )
    return symbol_row, layer_rows, None


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Route B-lite B1 error audit tables.")
    ap.add_argument("--candidate-dirs", nargs="*", default=[])
    ap.add_argument("--routeA-cross-loss-dir", default="results/_tmp_routeA_correctness_formal_stageD_cross_loss")
    ap.add_argument("--output-dir", default="results/_tmp_routeB_lite_error_audit")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    routea_dir = Path(args.routeA_cross_loss_dir)
    master = _load_master(routea_dir)
    master_by_pid = {str(r["point_id"]): r.to_dict() for _, r in master.iterrows()}

    layer_rows: list[dict[str, Any]] = []
    symbol_rows: list[dict[str, Any]] = []
    eval_cache: dict[int, pd.DataFrame] = {}
    point_failures: list[str] = []
    tasks: list[dict[str, Any]] = []

    for cand in _candidate_dirs(args):
        loss_db = infer_loss_db_from_path(cand)
        eval_cache.setdefault(loss_db, _load_replay_eval(routea_dir, loss_db))
        main = pd.read_csv(cand / "polar_e2e_results.csv")
        for _, row in main.iterrows():
            d = int(row["dimension"])
            bw = int(row["bin_width_ps"])
            pid = point_id(loss_db=loss_db, dimension=d, bin_width_ps=bw)
            tasks.append(
                {
                    "cand": cand,
                    "loss_db": loss_db,
                    "d": d,
                    "bw": bw,
                    "eval_by_layer": eval_cache[loss_db],
                    "master_row": master_by_pid.get(pid, {}),
                }
            )

    max_workers = max(1, int(args.workers))
    if max_workers == 1:
        for spec in tasks:
            symbol_row, local_layers, failure = _process_point_spec(**spec)
            if failure:
                point_failures.append(failure)
            if symbol_row is not None:
                symbol_rows.append(symbol_row)
            layer_rows.extend(local_layers)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(_process_point_spec, **spec) for spec in tasks]
            for fut in as_completed(futures):
                symbol_row, local_layers, failure = fut.result()
                if failure:
                    point_failures.append(failure)
                if symbol_row is not None:
                    symbol_rows.append(symbol_row)
                layer_rows.extend(local_layers)

    layer_df = pd.DataFrame(layer_rows)
    symbol_df = pd.DataFrame(symbol_rows)
    if layer_df.empty:
        raise SystemExit("no layer audit rows generated")

    layer_df.to_csv(output_dir / "routeB_layer_confusion_table.csv", index=False)
    symbol_df.to_csv(output_dir / "routeB_symbol_offset_table.csv", index=False)

    point_summary = layer_df.groupby(["loss_db", "dimension", "bin_width_ps", "point_id"], as_index=False).agg(
        layer_count=("layer_idx", "count"),
        eligible_B2_layers=("eligible_for_B2_flag", "sum"),
        eligible_B3_layers=("eligible_for_B3_flag", "sum"),
        mean_asymmetry_abs_gap=("asymmetry_abs_gap", "mean"),
        max_asymmetry_abs_gap=("asymmetry_abs_gap", "max"),
        mean_capacity_delta_asym_minus_bsc=("capacity_delta_asym_minus_bsc", "mean"),
        max_capacity_delta_abs=("capacity_delta_abs", "max"),
        mean_decoder_fail_rate_oracle_layer=("decoder_fail_rate_oracle_layer", "mean"),
        min_n_pairs_modeling=("n_pairs_modeling", "min"),
        min_conditional_count=("min_conditional_count", "min"),
        clipped_layer_count=("p01_clipped_flag", "sum"),
    )
    point_summary = point_summary.merge(
        symbol_df[["point_id", "symbol_substitution_rate", "nonzero_top_delta_frac_among_mismatch", "offset_like_mismatch_flag", "erasure_proxy_rate"]],
        on="point_id",
        how="left",
    )
    master_keep = [c for c in ("point_id", "decoder_fail_rate_oracle", "epsilon_EC_bound", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps") if c in master.columns]
    point_summary = point_summary.merge(master[master_keep], on="point_id", how="left")
    point_summary.to_csv(output_dir / "routeB_point_error_summary.csv", index=False)

    diag = point_summary.copy()
    diag["bsc_ok_flag"] = (
        (pd.to_numeric(diag["mean_asymmetry_abs_gap"], errors="coerce") < 0.01)
        & (pd.to_numeric(diag["max_capacity_delta_abs"], errors="coerce") < 0.005)
    ).astype(int)
    diag["asym_binary_candidate_flag"] = (
        (pd.to_numeric(diag["max_asymmetry_abs_gap"], errors="coerce") >= 0.02)
        & (pd.to_numeric(diag["eligible_B2_layers"], errors="coerce") > 0)
    ).astype(int)
    diag["offset_like_candidate_flag"] = (pd.to_numeric(diag["nonzero_top_delta_frac_among_mismatch"], errors="coerce") >= 0.50).astype(int)
    diag["erasure_proxy_dominant_flag"] = (pd.to_numeric(diag["erasure_proxy_rate"], errors="coerce") >= 0.20).astype(int)
    diag["diagnostic_only_flag"] = (
        (pd.to_numeric(diag["eligible_B2_layers"], errors="coerce") <= 0)
        | (pd.to_numeric(diag["clipped_layer_count"], errors="coerce") > 0)
    ).astype(int)
    diag.to_csv(output_dir / "routeB_model_diagnosis_table.csv", index=False)

    summary = [
        f"routeA_cross_loss_dir: {routea_dir}",
        f"candidate_dirs: {', '.join(str(p) for p in _candidate_dirs(args))}",
        f"point_rows: {len(point_summary)}",
        f"layer_rows: {len(layer_df)}",
        f"symbol_rows: {len(symbol_df)}",
        f"workers: {max_workers}",
        f"eligible_B2_layers_4096_512: {int(layer_df['eligible_for_B2_flag'].sum())}",
        f"eligible_B3_layers_strict_no_clipping: {int(layer_df['eligible_for_B3_flag'].sum())}",
        f"eligible_layers_conservative_8192_1024: {int(layer_df['conservative_8192_1024_eligible_flag'].sum())}",
        f"asym_binary_candidate_points: {int(diag['asym_binary_candidate_flag'].sum())}",
        f"offset_like_candidate_points: {int(diag['offset_like_candidate_flag'].sum())}",
        f"diagnostic_only_points: {int(diag['diagnostic_only_flag'].sum())}",
        f"point_failures: {len(point_failures)}",
        "bias_note: B-lite v1 uses same-point modeling and replay evaluation; layer-level sample sufficiency gates reduce optimistic bias but do not eliminate it.",
        "erasure_note: erasure_proxy_rate is sourced from rejected_frame_fraction and is not a true symbol-erasure observation.",
        "claim_boundary: B1 is diagnostic only; it does not imply decoder, PIE, or SKR improvement.",
    ]
    if point_failures:
        summary.append("point_failure_examples:")
        summary.extend([f"  - {x}" for x in point_failures[:10]])
    write_summary(output_dir / "routeB_error_audit_summary.txt", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
