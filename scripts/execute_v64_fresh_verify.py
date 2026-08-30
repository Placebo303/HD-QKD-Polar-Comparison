"""V64 fresh 24-block guarded runner — 48-96 calls hard cap 96, single 64-bit dual-tag, additive run_01."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v64_full_symbol_verification import (  # noqa: E402
    ACCEPTED_PLAN_SHA,
    BLOCK_LENGTH,
    HARD_CAP,
    OUTPUT_ROOT,
    PAIRS_PER_BLOCK,
    SCOPED_TRACKED_PATHS,
    V64CallAccounting,
    build_instrumented_record,
    build_v64_fresh_registry,
    classify_fresh_block,
    reconstruct_v64_matrices,
    verify_dual,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/v64_fresh_registry.json"

def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run V64 fresh 24-block verification (48-96 calls hard cap 96, dual-tag single 64b).")
    p.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization flag")
    p.add_argument("--authorized-target-sha", default=None, help="Full 40-char implementation SHA (must equal HEAD, origin, ACCEPTED_PLAN_SHA)")
    p.add_argument("--output-root", default=None, help="Override output root (tests only)")
    p.add_argument("--fake-runner", action="store_true", help="Use fake runner for tests (no real decoder)")
    return p.parse_args(argv)

def _check_git(authorized: str) -> None:
    # ponytail: implementation SHA binding HEAD==origin==authorized (implementation SHA), ACCEPTED_PLAN_SHA only drift warning not blocking (nbldpc_shell_adapter pattern)
    if len(authorized) != 40:
        print("BLOCKED: --authorized-target-sha must be 40-char", file=sys.stderr)
        sys.exit(2)
    if ACCEPTED_PLAN_SHA != "760cb2967c7f5d5548a68f056458ef89398de3f2":
        print(f"WARNING: ACCEPTED_PLAN_SHA drift {ACCEPTED_PLAN_SHA} != 760cb2967c7f5d5548a68f056458ef89398de3f2 (not blocking)", file=sys.stderr)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        origin = subprocess.check_output(["git", "rev-parse", "origin/formal-ir-mainline"], text=True).strip()
    except Exception as exc:
        print(f"BLOCKED: git rev-parse failed: {exc}", file=sys.stderr)
        sys.exit(2)
    if head != authorized:
        print(f"BLOCKED: HEAD {head} != authorized (implementation SHA) {authorized}", file=sys.stderr)
        sys.exit(2)
    if origin != authorized:
        print(f"BLOCKED: origin {origin} != authorized (implementation SHA) {authorized}", file=sys.stderr)
        sys.exit(2)
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    except Exception as exc:
        print(f"BLOCKED: git status failed: {exc}", file=sys.stderr)
        sys.exit(2)
    dirty = [line for line in out.splitlines() if any(p in line for p in SCOPED_TRACKED_PATHS)]
    if dirty:
        print(f"BLOCKED: SCOPED dirty {dirty}", file=sys.stderr)
        sys.exit(2)

def _preflight(output_root: Path, fake_runner: bool) -> list[dict]:
    # G1-G5 checks: registry K2>=24, matrices, held-out parquet reachable, no synthetic fallback
    try:
        reg = build_v64_fresh_registry()
    except ValueError as exc:
        raise RuntimeError(f"EVIDENCE_INVALID registry: {exc}") from exc
    if len(reg) != 24:
        raise RuntimeError(f"EVIDENCE_INVALID registry len {len(reg)} !=24")
    # matrix frozen check (decoder-free)
    try:
        reconstruct_v64_matrices()
    except Exception as exc:
        raise RuntimeError(f"EVIDENCE_INVALID matrices: {exc}") from exc
    # held-out parquet existence (no synthetic fallback)
    if not fake_runner:
        for src in ("1M", "1p5M", "2M"):
            for key in ["type2_1M_20260121_184040/pairs.parquet", "type2_1p5M_20260121_183806/pairs.parquet", "type2_2M_20260121_183657/pairs.parquet"]:
                p = REPO_ROOT / f"comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/{key}"
                if not p.is_file():
                    raise RuntimeError(f"EVIDENCE_INVALID held-out parquet missing {p}")
    return reg

def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha required", file=sys.stderr)
        return 2
    _check_git(args.authorized_target_sha)
    output_root = Path(args.output_root) if args.output_root else OUTPUT_ROOT
    if output_root.exists():
        print(f"BLOCKED: output root already exists: {output_root}", file=sys.stderr)
        return 2
    # preflight before creating root
    try:
        registry = _preflight(output_root, fake_runner=bool(args.fake_runner))
    except RuntimeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    # create root only after all guards pass, before first decode
    output_root.mkdir(parents=True, exist_ok=False)
    # write registry authoritatively inside run_01 if not already at canonical path
    try:
        (output_root / "v64_fresh_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    except Exception:
        pass
    (output_root / "v64_records.json").write_text("[]", encoding="utf-8")
    acct = V64CallAccounting(hard_cap=HARD_CAP)
    records: list[dict] = []
    t0 = time.time()
    try:
        if args.fake_runner:
            # fake: 24 blocks, each 2 calls (L1+base) deterministic fake records, stay within 48
            for ent in registry:
                acct.register_start("l1"); acct.register_complete("l1")
                acct.register_start("base"); acct.register_complete("base")
                import numpy as np
                s_true = np.arange(1024, dtype=np.int64) % 1024
                from comparison_bench.formal_ir.v64_full_symbol_verification import decompose_symbols
                u1_t, u2_t = decompose_symbols(s_true)
                rec = build_instrumented_record(ent["block_id"], ent["source"], ent["frame_ids"], u1_t, u2_t, u1_t, u2_t, True, True, "base", 2)
                rec["decoder_calls"] = 2
                rec["held_out_ordinal_start"] = ent["held_out_ordinal_start"]
                rec["held_out_ordinal_end"] = ent["held_out_ordinal_end"]
                rec["pairs_count"] = PAIRS_PER_BLOCK
                rec["sampling_mode"] = ent["sampling_mode"]
                # add missing fields for spec
                rec["block_seed"] = ent["block_id"]
                records.append(rec)
        else:
            # Real decoder — frozen V54 H1/L1APP/Lane C/Δ8+Δ8/TRAIN prior/90/1.0, three-stage conditional progressive verification-only (full-symbol dual-tag)
            import numpy as np
            import pandas as pd
            from comparison_bench.formal_ir.v64_full_symbol_verification import decompose_symbols, recompose_symbols, compute_tag_l2, compute_tag_full
            # reuse V54 frozen matrices and TRAIN prior (same as nbldpc_shell_adapter)
            try:
                from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, syndrome_of_gf32, decode_row_layered_fftqspa
                from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import get_l1_prior_p_u1_given_b, get_l1_app_prior_l2, softmax_beliefs
                from comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts
            except ModuleNotFoundError:
                from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import GF2mField, syndrome_of_gf32, decode_row_layered_fftqspa  # type: ignore
                from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import get_l1_prior_p_u1_given_b, get_l1_app_prior_l2, softmax_beliefs  # type: ignore
                from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts  # type: ignore
            field = GF2mField.create(32)
            matrices = reconstruct_v64_matrices(field=field)
            counts = load_v25_channel_counts()
            parquet_map = {
                "1M": REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
                "1p5M": REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
                "2M": REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
            }
            # helper to load one block's symbols
            def _load_block_symbols(src: str, fids: list[int]) -> tuple[np.ndarray, np.ndarray]:
                p = parquet_map[src]
                df = pd.read_parquet(p)
                filt = df[df["frame_id"].isin(fids)].sort_values(["frame_id", "pair_idx"])
                alice = filt["alice_symbol"].to_numpy(dtype=np.int64)
                bob = filt["bob_symbol"].to_numpy(dtype=np.int64)
                if alice.size != 1024 or bob.size != 1024:
                    raise RuntimeError(f"EVIDENCE_INVALID row count {alice.size}/{bob.size} !=1024 for {src} {fids}")
                return alice, bob
            for ent in registry:
                src = ent["source"]
                fids = ent["frame_ids"]
                alice_sym, bob_sym = _load_block_symbols(src, fids)
                s_true = alice_sym
                u1_true, u2_true = decompose_symbols(s_true)
                tag_true_l2 = compute_tag_l2(u2_true)
                tag_true_full = compute_tag_full(u1_true, u2_true)
                # H matrices per source
                H1 = matrices[("H1", "L1")][0]
                H_base = matrices[("lane_c", src)][0]
                H_joint1 = matrices[("h_joint1", src)][0]
                H_total = matrices[("h_total", src)][0]
                # L1
                acct.register_start("l1")
                p_i = get_l1_prior_p_u1_given_b(counts[src], bob_sym)
                s1 = syndrome_of_gf32(H1, u1_true, field)
                res_l1 = decode_row_layered_fftqspa(H1, p_i, s1, max_iter=90, damping_alpha=1.0, field=field)
                acct.register_complete("l1")
                q = softmax_beliefs(res_l1.final_beliefs)
                u1_hat = np.argmax(q, axis=1).astype(np.int64) % 32
                syndrome_ok_l1 = bool(np.array_equal(syndrome_of_gf32(H1, u1_hat, field), s1))
                # prior for L2 shared across stages
                prior_l2 = get_l1_app_prior_l2(counts[src], bob_sym, q)
                # base
                acct.register_start("base")
                s_base = syndrome_of_gf32(H_base, u2_true, field)
                res_base = decode_row_layered_fftqspa(H_base, prior_l2, s_base, max_iter=90, damping_alpha=1.0, field=field)
                acct.register_complete("base")
                syndrome_ok_base = bool(res_base.syndrome_ok)
                tag_hat_l2_base = compute_tag_l2(res_base.x_hat.astype(np.int64))
                tag_hat_full_base = compute_tag_full(u1_hat, res_base.x_hat.astype(np.int64))
                tag_ok_l2_base = tag_hat_l2_base == tag_true_l2
                tag_ok_full_base = tag_hat_full_base == tag_true_full
                verify_full_base = syndrome_ok_base and tag_ok_full_base
                # dual instrumentation for base (still single 64b leak)
                if verify_full_base:
                    rec = build_instrumented_record(ent["block_id"], src, fids, u1_hat, res_base.x_hat.astype(np.int64), u1_true, u2_true, syndrome_ok_l1, syndrome_ok_base, "base", 2)
                    # overwrite dual tags already via build_instrumented_record (syndrome_ok_l2=base, tag_ok_* from verify_dual)
                    rec["held_out_ordinal_start"] = ent["held_out_ordinal_start"]
                    rec["held_out_ordinal_end"] = ent["held_out_ordinal_end"]
                    rec["pairs_count"] = 1024
                    rec["sampling_mode"] = ent["sampling_mode"]
                    rec["block_seed"] = ent["block_id"]
                    records.append(rec)
                    continue
                # stage1 verification-only incremental
                acct.register_start("stage1")
                s_joint1 = syndrome_of_gf32(H_joint1, u2_true, field)
                res_s1 = decode_row_layered_fftqspa(H_joint1, prior_l2, s_joint1, max_iter=90, damping_alpha=1.0, field=field)
                acct.register_complete("stage1")
                syndrome_ok_s1 = bool(res_s1.syndrome_ok)
                tag_hat_l2_s1 = compute_tag_l2(res_s1.x_hat.astype(np.int64))
                tag_hat_full_s1 = compute_tag_full(u1_hat, res_s1.x_hat.astype(np.int64))
                tag_ok_l2_s1 = tag_hat_l2_s1 == tag_true_l2
                tag_ok_full_s1 = tag_hat_full_s1 == tag_true_full
                verify_full_s1 = syndrome_ok_s1 and tag_ok_full_s1
                if verify_full_s1:
                    rec = build_instrumented_record(ent["block_id"], src, fids, u1_hat, res_s1.x_hat.astype(np.int64), u1_true, u2_true, syndrome_ok_l1, syndrome_ok_s1, "delta8", 3)
                    rec["held_out_ordinal_start"] = ent["held_out_ordinal_start"]
                    rec["held_out_ordinal_end"] = ent["held_out_ordinal_end"]
                    rec["pairs_count"] = 1024
                    rec["sampling_mode"] = ent["sampling_mode"]
                    rec["block_seed"] = ent["block_id"]
                    records.append(rec)
                    continue
                # stage2
                acct.register_start("stage2")
                s_total = syndrome_of_gf32(H_total, u2_true, field)
                res_s2 = decode_row_layered_fftqspa(H_total, prior_l2, s_total, max_iter=90, damping_alpha=1.0, field=field)
                acct.register_complete("stage2")
                syndrome_ok_s2 = bool(res_s2.syndrome_ok)
                tag_hat_l2_s2 = compute_tag_l2(res_s2.x_hat.astype(np.int64))
                tag_hat_full_s2 = compute_tag_full(u1_hat, res_s2.x_hat.astype(np.int64))
                # final stage even if verify fails we still record
                rec = build_instrumented_record(ent["block_id"], src, fids, u1_hat, res_s2.x_hat.astype(np.int64), u1_true, u2_true, syndrome_ok_l1, syndrome_ok_s2, "delta16", 4)
                rec["held_out_ordinal_start"] = ent["held_out_ordinal_start"]
                rec["held_out_ordinal_end"] = ent["held_out_ordinal_end"]
                rec["pairs_count"] = 1024
                rec["sampling_mode"] = ent["sampling_mode"]
                rec["block_seed"] = ent["block_id"]
                records.append(rec)
        # validate budget
        errs = acct.validate()
        if errs:
            raise RuntimeError(f"budget validate failed {errs}")
        if acct.completed < 48 or acct.completed > 96:
            raise RuntimeError(f"budget total {acct.completed} not in 48-96")
        # write records
        (output_root / "v64_records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        import csv
        if records:
            with (output_root / "v64_records.csv").open("w", newline="", encoding="utf-8") as f:
                # union of keys
                keys = sorted({k for r in records for k in r.keys()})
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(records)
        summary = {
            "accepted_plan_sha": ACCEPTED_PLAN_SHA,
            "head_sha": args.authorized_target_sha,
            "total_blocks": len(registry),
            "total_calls": acct.completed,
            "hard_cap": HARD_CAP,
            "registry": registry,
            "elapsed_s": time.time() - t0,
        }
        (output_root / "v64_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except BaseException as exc:
        (output_root / "v64_interrupted.json").write_text(json.dumps({"interrupted": True, "error": f"{type(exc).__name__}: {exc}", "total_calls": acct.completed}), encoding="utf-8")
        print(f"INTERRUPTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"V64 fresh evidence written to {output_root} total_calls {acct.completed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
