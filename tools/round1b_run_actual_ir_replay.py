#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.run_real_polar_max_pie import _polar_weight_order  # type: ignore
from src.reconciliation.cpp_scl_wrapper import PolarSCLDecoder  # type: ignore
from src.reconciliation.real_polar_sc_rescue import (  # type: ignore
    polar_encode_non_systematic,
    polar_sc_decode_with_frozen,
)
from src.reconciliation.verification import (  # type: ignore
    VERIFICATION_FAMILY,
    VERIFICATION_PROTOCOL_ID,
    VERIFICATION_PUBLIC_MESSAGE_RULE,
    VERIFICATION_SCOPE,
    VERIFICATION_SEED_POLICY,
    VERIFICATION_TRANSCRIPT_SOURCE_TAG,
    verification_transcript,
)
from _security_round_common import (
    bit_layer_from_symbols,
    ensure_output_dir,
    infer_loss_db_from_path,
    write_summary,
)


def _default_candidate_dirs() -> list[Path]:
    return [REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15"]


def _default_replay_index_dir() -> Path:
    return REPO_ROOT / "results" / "_tmp_round1a_replay_index"


def _llr_from_side_info(bits_b: np.ndarray, ber: float) -> np.ndarray:
    p = float(min(1.0 - 1e-6, max(1e-6, float(ber))))
    lam = float(math.log((1.0 - p) / p))
    return np.where(bits_b.astype(np.uint8) == 0, lam, -lam).astype(np.float64)


def _llr_from_asym_binary(bits_b: np.ndarray, p01: float, p10: float) -> tuple[np.ndarray, float, float]:
    p01c = float(min(1.0 - 1e-6, max(1e-6, float(p01))))
    p10c = float(min(1.0 - 1e-6, max(1e-6, float(p10))))
    llr_b0 = float(math.log((1.0 - p01c) / p10c))
    llr_b1 = float(math.log(p01c / (1.0 - p10c)))
    return np.where(bits_b.astype(np.uint8) == 0, llr_b0, llr_b1).astype(np.float64), llr_b0, llr_b1


def _load_channel_model(path_text: str) -> dict[tuple[str, int], dict[str, Any]]:
    if not str(path_text).strip():
        return {}
    path = Path(path_text)
    if not path.exists():
        raise SystemExit(f"channel model table not found: {path}")
    df = pd.read_csv(path)
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for _, row in df.iterrows():
        pid = str(row.get("point_id", "")).strip()
        if not pid:
            continue
        try:
            layer_id = int(float(row.get("layer_idx", row.get("layer_id"))))
        except Exception:
            continue
        out[(pid, layer_id)] = row.to_dict()
    return out


def _full_u_from_info(info_bits: np.ndarray, frozen_values: np.ndarray, info_idx_sorted: np.ndarray) -> np.ndarray:
    u_hat = frozen_values.astype(np.int8, copy=True)
    u_hat[info_idx_sorted] = info_bits.astype(np.int8)
    return u_hat


def _decode_block(
    *,
    decoder_mode: str,
    llr: np.ndarray,
    mask_u8: np.ndarray,
    frozen_values_u8: np.ndarray,
    info_idx_sorted: np.ndarray,
    n_log: int,
    decoder: PolarSCLDecoder | None,
) -> tuple[np.ndarray, str]:
    if decoder_mode == "sc":
        u_hat = polar_sc_decode_with_frozen(
            llr.astype(np.float64),
            mask_u8.astype(np.int8),
            frozen_values_u8.astype(np.int8),
            n_log,
        )
        return u_hat.astype(np.uint8), "actual_zero"
    if decoder_mode == "scl":
        if decoder is None:
            raise RuntimeError("SCL replay requested but replay decoder is unavailable")
        info_bits = decoder.decode_batch_frozen(
            int(llr.size),
            int(np.sum(mask_u8)),
            1,
            mask_u8,
            frozen_values_u8.reshape(1, -1),
            llr.reshape(1, -1).astype(np.float32),
        )[0]
        u_hat = _full_u_from_info(info_bits, frozen_values_u8, info_idx_sorted)
        return u_hat.astype(np.uint8), "configured_crc_budget"
    raise ValueError(f"unsupported decoder_mode={decoder_mode}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run frozen-value-aware actual IR replay over indexed Polar layers.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--replay-index-dir", default=str(_default_replay_index_dir()))
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--force-rebuild-decoder", action="store_true")
    ap.add_argument("--verification-tag-bits", type=int, default=32)
    ap.add_argument("--channel-model-table", default="")
    ap.add_argument("--channel-model-tag", default="bsc_legacy", choices=["bsc_legacy", "asym_binary_v1"])
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    candidate_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else _default_candidate_dirs()
    replay_index_dir = Path(args.replay_index_dir)
    channel_model = _load_channel_model(args.channel_model_table)

    point_index = pd.read_csv(replay_index_dir / "replay_index_point_table.csv")
    layer_index = pd.read_csv(replay_index_dir / "replay_index_layer_table.csv")
    point_index["loss_db"] = pd.to_numeric(point_index["loss_db"], errors="coerce").astype(int)
    point_index["dimension"] = pd.to_numeric(point_index["dimension"], errors="coerce").astype(int)
    point_index["bin_width_ps"] = pd.to_numeric(point_index["bin_width_ps"], errors="coerce").astype(int)
    layer_index["loss_db"] = pd.to_numeric(layer_index["loss_db"], errors="coerce").astype(int)
    layer_index["dimension"] = pd.to_numeric(layer_index["dimension"], errors="coerce").astype(int)
    layer_index["bin_width_ps"] = pd.to_numeric(layer_index["bin_width_ps"], errors="coerce").astype(int)
    layer_index["layer_id"] = pd.to_numeric(layer_index["layer_id"], errors="coerce").astype(int)
    for col in ("k_best", "crc_bits", "frozen_count_best", "layer_block_symbols"):
        layer_index[col] = pd.to_numeric(layer_index[col], errors="coerce")
    for col in ("rate_best", "layer_ber"):
        if col in layer_index.columns:
            layer_index[col] = pd.to_numeric(layer_index[col], errors="coerce")

    allowed_losses = {infer_loss_db_from_path(p) for p in candidate_dirs}
    if allowed_losses:
        point_index = point_index[point_index["loss_db"].isin(allowed_losses)].copy()

    order_cache: dict[int, np.ndarray] = {}
    scl_decoder: PolarSCLDecoder | None = PolarSCLDecoder(
        repo_root=REPO_ROOT,
        force_rebuild=bool(args.force_rebuild_decoder),
        lib_stem="ca_scl_replay",
    )
    block_rows: list[dict[str, Any]] = []

    for _, prow in point_index.iterrows():
        if str(prow.get("replay_ready_tag", "")).strip().lower() != "yes":
            block_rows.append(
                {
                    "point_id": prow["point_id"],
                    "loss_db": int(prow["loss_db"]),
                    "dimension": int(prow["dimension"]),
                    "bin_width_ps": int(prow["bin_width_ps"]),
                    "layer_id": -1,
                    "block_index": -1,
                    "decoder_mode_used": "",
                    "k_used": "",
                    "rate_used": "",
                    "crc_bits_used": "",
                    "verification_protocol_id": "",
                    "verification_family": "",
                    "verification_scope": "",
                    "verification_tag_bits": "",
                    "verification_seed_policy": "",
                    "verification_public_message_rule": "",
                    "channel_model_tag": "",
                    "model_fallback_tag": "",
                    "p01_model": "",
                    "p10_model": "",
                    "llr_b0": "",
                    "llr_b1": "",
                    "verification_invoked_flag": "",
                    "verification_bits_budgeted": "",
                    "verification_bits_used_actual": "",
                    "verification_bits_revealed_legacy_crc": "",
                    "verification_seed_index": "",
                    "verification_pass_flag": "",
                    "verification_fail_flag": "",
                    "verification_transcript_source_tag": "",
                    "syndrome_bits_revealed": "",
                    "verification_bits_revealed": "",
                    "total_leak_ec_bits_legacy_crc": "",
                    "total_leak_ec_bits": "",
                    "block_match_oracle_flag": "",
                    "undetected_error_oracle_flag": "",
                    "block_success_flag": "",
                    "decode_fail_flag": "",
                    "verification_source_tag": "",
                    "replay_status": "blocked",
                    "blocked_reason": str(prow.get("replay_block_rule_tag", "blocked")),
                }
            )
            continue

        d = int(prow["dimension"])
        bw = int(prow["bin_width_ps"])
        pid = str(prow["point_id"])
        a_path = Path(str(prow["a_eff_source_path"]))
        b_path = Path(str(prow["b_eff_source_path"]))
        if (not a_path.exists()) or (not b_path.exists()):
            block_rows.append(
                {
                    "point_id": pid,
                    "loss_db": int(prow["loss_db"]),
                    "dimension": d,
                    "bin_width_ps": bw,
                    "layer_id": -1,
                    "block_index": -1,
                    "decoder_mode_used": "",
                    "k_used": "",
                    "rate_used": "",
                    "crc_bits_used": "",
                    "verification_protocol_id": "",
                    "verification_family": "",
                    "verification_scope": "",
                    "verification_tag_bits": "",
                    "verification_seed_policy": "",
                    "verification_public_message_rule": "",
                    "channel_model_tag": "",
                    "model_fallback_tag": "",
                    "p01_model": "",
                    "p10_model": "",
                    "llr_b0": "",
                    "llr_b1": "",
                    "verification_invoked_flag": "",
                    "verification_bits_budgeted": "",
                    "verification_bits_used_actual": "",
                    "verification_bits_revealed_legacy_crc": "",
                    "verification_seed_index": "",
                    "verification_pass_flag": "",
                    "verification_fail_flag": "",
                    "verification_transcript_source_tag": "",
                    "syndrome_bits_revealed": "",
                    "verification_bits_revealed": "",
                    "total_leak_ec_bits_legacy_crc": "",
                    "total_leak_ec_bits": "",
                    "block_match_oracle_flag": "",
                    "undetected_error_oracle_flag": "",
                    "block_success_flag": "",
                    "decode_fail_flag": "",
                    "verification_source_tag": "",
                    "replay_status": "blocked",
                    "blocked_reason": "missing_sidecar_arrays",
                }
            )
            continue

        a_eff = np.load(a_path, mmap_mode="r")
        b_eff = np.load(b_path, mmap_mode="r")
        point_layers = layer_index[
            (layer_index["loss_db"] == int(prow["loss_db"]))
            & (layer_index["dimension"] == d)
            & (layer_index["bin_width_ps"] == bw)
            & (layer_index["layer_replay_ready_tag"].astype(str).str.lower() == "yes")
        ].copy()
        if point_layers.empty:
            block_rows.append(
                {
                    "point_id": pid,
                    "loss_db": int(prow["loss_db"]),
                    "dimension": d,
                    "bin_width_ps": bw,
                    "layer_id": -1,
                    "block_index": -1,
                    "decoder_mode_used": "",
                    "k_used": "",
                    "rate_used": "",
                    "crc_bits_used": "",
                    "verification_protocol_id": "",
                    "verification_family": "",
                    "verification_scope": "",
                    "verification_tag_bits": "",
                    "verification_seed_policy": "",
                    "verification_public_message_rule": "",
                    "channel_model_tag": "",
                    "model_fallback_tag": "",
                    "p01_model": "",
                    "p10_model": "",
                    "llr_b0": "",
                    "llr_b1": "",
                    "verification_invoked_flag": "",
                    "verification_bits_budgeted": "",
                    "verification_bits_used_actual": "",
                    "verification_bits_revealed_legacy_crc": "",
                    "verification_seed_index": "",
                    "verification_pass_flag": "",
                    "verification_fail_flag": "",
                    "verification_transcript_source_tag": "",
                    "syndrome_bits_revealed": "",
                    "verification_bits_revealed": "",
                    "total_leak_ec_bits_legacy_crc": "",
                    "total_leak_ec_bits": "",
                    "block_match_oracle_flag": "",
                    "undetected_error_oracle_flag": "",
                    "block_success_flag": "",
                    "decode_fail_flag": "",
                    "verification_source_tag": "",
                    "replay_status": "blocked",
                    "blocked_reason": "missing_replayable_layers",
                }
            )
            continue

        bits = int(round(math.log2(d)))
        for _, lrow in point_layers.iterrows():
            layer_id = int(lrow["layer_id"])
            decoder_mode = str(lrow.get("decoder_mode_best") or "").strip().lower()
            k_best = int(float(lrow["k_best"]))
            crc_bits = int(float(lrow.get("crc_bits", 0) or 0))
            block_symbols = int(float(lrow["layer_block_symbols"]))
            frozen_count = int(float(lrow.get("frozen_count_best", block_symbols - k_best) or (block_symbols - k_best)))
            ber = float(lrow.get("layer_ber", np.nan))

            if block_symbols not in order_cache:
                order_cache[block_symbols] = _polar_weight_order(block_symbols)[::-1]
            info_idx_sorted = np.sort(np.asarray(order_cache[block_symbols][:k_best], dtype=np.int64))
            mask_u8 = np.zeros(block_symbols, dtype=np.uint8)
            mask_u8[info_idx_sorted] = 1
            n_log = int(round(math.log2(block_symbols)))

            a_bits = bit_layer_from_symbols(a_eff, dimension=d, layer_idx=layer_id)
            b_bits = bit_layer_from_symbols(b_eff, dimension=d, layer_idx=layer_id)
            full_blocks = int(min(a_bits.size, b_bits.size) // block_symbols)
            if full_blocks <= 0:
                block_rows.append(
                    {
                        "point_id": pid,
                        "loss_db": int(prow["loss_db"]),
                        "dimension": d,
                        "bin_width_ps": bw,
                        "layer_id": layer_id,
                        "block_index": -1,
                        "decoder_mode_used": decoder_mode,
                        "k_used": k_best,
                        "rate_used": lrow.get("rate_best"),
                        "crc_bits_used": crc_bits,
                        "verification_protocol_id": "",
                        "verification_family": "",
                        "verification_scope": "",
                        "verification_tag_bits": "",
                        "verification_seed_policy": "",
                        "verification_public_message_rule": "",
                        "channel_model_tag": "",
                        "model_fallback_tag": "",
                        "p01_model": "",
                        "p10_model": "",
                        "llr_b0": "",
                        "llr_b1": "",
                        "verification_invoked_flag": "",
                        "verification_bits_budgeted": "",
                        "verification_bits_used_actual": "",
                        "verification_bits_revealed_legacy_crc": "",
                        "verification_seed_index": "",
                        "verification_pass_flag": "",
                        "verification_fail_flag": "",
                        "verification_transcript_source_tag": "",
                        "syndrome_bits_revealed": "",
                        "verification_bits_revealed": "",
                        "total_leak_ec_bits_legacy_crc": "",
                        "total_leak_ec_bits": "",
                        "block_match_oracle_flag": "",
                        "undetected_error_oracle_flag": "",
                        "block_success_flag": "",
                        "decode_fail_flag": "",
                        "verification_source_tag": "",
                        "replay_status": "blocked",
                        "blocked_reason": "no_full_blocks",
                    }
                )
                continue

            for block_index in range(full_blocks):
                start = block_index * block_symbols
                end = start + block_symbols
                x_a = np.asarray(a_bits[start:end], dtype=np.uint8)
                x_b = np.asarray(b_bits[start:end], dtype=np.uint8)
                u_a = polar_encode_non_systematic(x_a.astype(np.int8), n_log).astype(np.uint8)
                frozen_values = np.zeros(block_symbols, dtype=np.uint8)
                frozen_values[mask_u8 == 0] = u_a[mask_u8 == 0]
                model_tag = str(args.channel_model_tag)
                model_fallback_tag = "none"
                p01_model: float | str = ""
                p10_model: float | str = ""
                llr_b0: float | str = ""
                llr_b1: float | str = ""
                if model_tag == "asym_binary_v1":
                    mrow = channel_model.get((pid, layer_id), {})
                    try:
                        p01_candidate = float(mrow.get("p01_model"))
                        p10_candidate = float(mrow.get("p10_model"))
                        eligible = int(float(mrow.get("eligible_for_B3_model_flag", 0))) == 1
                        if eligible and math.isfinite(p01_candidate) and math.isfinite(p10_candidate):
                            llr, llr_b0_val, llr_b1_val = _llr_from_asym_binary(x_b, p01_candidate, p10_candidate)
                            p01_model = p01_candidate
                            p10_model = p10_candidate
                            llr_b0 = llr_b0_val
                            llr_b1 = llr_b1_val
                        else:
                            llr = _llr_from_side_info(x_b, ber=ber)
                            model_fallback_tag = "ineligible_or_invalid_asym_binary_params"
                    except Exception:
                        llr = _llr_from_side_info(x_b, ber=ber)
                        model_fallback_tag = "missing_or_invalid_asym_binary_params"
                else:
                    llr = _llr_from_side_info(x_b, ber=ber)
                    model_tag = "bsc_legacy"
                    model_fallback_tag = "bsc_legacy_default"
                replay_status = "ok"
                blocked_reason = ""
                try:
                    u_hat, verification_source_tag = _decode_block(
                        decoder_mode=decoder_mode,
                        llr=llr,
                        mask_u8=mask_u8,
                        frozen_values_u8=frozen_values,
                        info_idx_sorted=info_idx_sorted,
                        n_log=n_log,
                        decoder=scl_decoder,
                    )
                    x_hat = polar_encode_non_systematic(u_hat.astype(np.int8), n_log).astype(np.uint8)
                    block_success = int(np.array_equal(x_hat, x_a))
                    decode_fail = int(1 - block_success)
                    verification_bits_legacy_crc = int(crc_bits if decoder_mode == "scl" and crc_bits > 0 else 0)
                    transcript = verification_transcript(
                        reference_bits=x_a,
                        candidate_bits=x_hat,
                        point_id=pid,
                        layer_id=layer_id,
                        block_index=block_index,
                        tag_bits=int(args.verification_tag_bits),
                    )
                    verification_bits = int(transcript["verification_bits_used_actual"])
                    verification_source_tag = "actual_replay" if verification_bits_legacy_crc == 0 else "configured_crc_budget"
                    if verification_bits_legacy_crc > 0:
                        replay_status = "ok_configured_crc_budget"
                except Exception as exc:
                    block_success = 0
                    decode_fail = 1
                    verification_bits = 0
                    verification_bits_legacy_crc = 0
                    verification_source_tag = ""
                    transcript = {}
                    replay_status = "blocked"
                    blocked_reason = f"{type(exc).__name__}"

                syndrome_bits = int(frozen_count)
                total_leak = int(syndrome_bits + verification_bits) if replay_status.startswith("ok") else ""
                total_leak_legacy_crc = int(syndrome_bits + verification_bits_legacy_crc) if replay_status.startswith("ok") else ""
                block_match_oracle = block_success if replay_status.startswith("ok") else ""
                undetected_error_oracle = int((1 - block_success) and int(transcript.get("verification_pass_flag", 0)) == 1) if replay_status.startswith("ok") else ""
                block_rows.append(
                    {
                        "point_id": pid,
                        "loss_db": int(prow["loss_db"]),
                        "dimension": d,
                        "bin_width_ps": bw,
                        "layer_id": layer_id,
                        "block_index": block_index,
                        "decoder_mode_used": decoder_mode,
                        "k_used": k_best,
                        "rate_used": lrow.get("rate_best"),
                        "crc_bits_used": crc_bits,
                        "verification_protocol_id": transcript.get("verification_protocol_id", ""),
                        "verification_family": transcript.get("verification_family", ""),
                        "verification_scope": transcript.get("verification_scope", ""),
                        "verification_tag_bits": int(args.verification_tag_bits) if replay_status.startswith("ok") else "",
                        "verification_seed_policy": transcript.get("verification_seed_policy", ""),
                        "verification_public_message_rule": transcript.get("verification_public_message_rule", ""),
                        "channel_model_tag": model_tag if replay_status.startswith("ok") else "",
                        "model_fallback_tag": model_fallback_tag if replay_status.startswith("ok") else "",
                        "p01_model": p01_model if replay_status.startswith("ok") else "",
                        "p10_model": p10_model if replay_status.startswith("ok") else "",
                        "llr_b0": llr_b0 if replay_status.startswith("ok") else "",
                        "llr_b1": llr_b1 if replay_status.startswith("ok") else "",
                        "verification_invoked_flag": transcript.get("verification_invoked_flag", ""),
                        "verification_bits_budgeted": transcript.get("verification_bits_budgeted", ""),
                        "verification_bits_used_actual": transcript.get("verification_bits_used_actual", ""),
                        "verification_bits_revealed_legacy_crc": verification_bits_legacy_crc if replay_status.startswith("ok") else "",
                        "verification_seed_index": transcript.get("verification_seed_index", ""),
                        "verification_pass_flag": transcript.get("verification_pass_flag", ""),
                        "verification_fail_flag": transcript.get("verification_fail_flag", ""),
                        "verification_transcript_source_tag": transcript.get("verification_transcript_source_tag", ""),
                        "syndrome_bits_revealed": syndrome_bits if replay_status.startswith("ok") else "",
                        "verification_bits_revealed": verification_bits if replay_status.startswith("ok") else "",
                        "total_leak_ec_bits_legacy_crc": total_leak_legacy_crc,
                        "total_leak_ec_bits": total_leak,
                        "block_match_oracle_flag": block_match_oracle,
                        "undetected_error_oracle_flag": undetected_error_oracle,
                        "block_success_flag": block_success if replay_status.startswith("ok") else "",
                        "decode_fail_flag": decode_fail if replay_status.startswith("ok") else "",
                        "verification_source_tag": verification_source_tag,
                        "replay_status": replay_status,
                        "blocked_reason": blocked_reason,
                    }
                )

    block_df = pd.DataFrame(block_rows)
    block_df.to_csv(output_dir / "actual_ir_block_table.csv", index=False)
    ok_points = int(block_df["replay_status"].astype(str).str.startswith("ok").groupby(block_df["point_id"]).any().sum()) if not block_df.empty else 0
    summary_lines = [
        f"candidate_input_dirs: {', '.join(str(p) for p in candidate_dirs)}",
        f"replay_index_dir: {replay_index_dir}",
        f"block_row_count: {len(block_df)}",
        f"points_with_actual_replay_rows: {ok_points}",
        f"verification_protocol_id: {VERIFICATION_PROTOCOL_ID}",
        f"verification_family: {VERIFICATION_FAMILY}",
        f"verification_scope: {VERIFICATION_SCOPE}",
        f"verification_seed_policy: {VERIFICATION_SEED_POLICY}",
        f"verification_public_message_rule: {VERIFICATION_PUBLIC_MESSAGE_RULE}",
        f"verification_tag_bits: {int(args.verification_tag_bits)}",
        f"channel_model_tag: {str(args.channel_model_tag)}",
        f"channel_model_table: {str(args.channel_model_table) if str(args.channel_model_table).strip() else 'none'}",
        "notes:",
        "- syndrome bits are actual replay outputs from frozen-value-aware decoding.",
        "- verification_bits_revealed now records universal-hash transcript leakage; legacy CRC budgeting is preserved in verification_bits_revealed_legacy_crc.",
        "- frame_success_rate remains unresolved at replay-run stage and is aggregated later as MISSING unless a rigorous denominator is available.",
    ]
    write_summary(output_dir / "round1b_summary.txt", summary_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
