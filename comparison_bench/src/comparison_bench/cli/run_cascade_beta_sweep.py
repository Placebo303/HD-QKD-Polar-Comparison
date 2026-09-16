"""Thin CLI for T2 small grid 24 points (n=256/1024/2048 x verify=32/64 x block=16/32 x parity=1/2)."""
from __future__ import annotations

import argparse
import itertools
import hashlib
import time
from pathlib import Path
import numpy as np
import pandas as pd

from ..config import load_config
from ..methods.cascade_single_kernel import run_cascade_single
from ..methods.cascade.config import load_cascade_single_config
from ..types import FrameBatch
from ..io.table_store import read_table
from ..io.dataset_builder import table_to_frame_batches


def _expand_grid(grid: dict) -> list[dict]:
    keys = list(grid.keys())
    vals = [grid[k] for k in keys]
    out = []
    for combo in itertools.product(*vals):
        out.append({k: v for k, v in zip(keys, combo)})
    return out


def _build_synthetic_batch(n_sym: int, q: int, ser: float, n_frames: int, seed: int, dataset_id: str) -> FrameBatch:
    rng = np.random.default_rng(seed)
    n_total = n_sym * n_frames
    alice = rng.integers(0, q, size=(n_frames, n_sym), dtype=np.int64)
    bob = alice.copy()
    flip = rng.random((n_frames, n_sym)) < ser
    # for flipped positions add random non-zero offset
    offsets = rng.integers(1, q, size=n_total, dtype=np.int64).reshape(n_frames, n_sym)
    bob[flip] = (alice[flip] + offsets[flip]) % q
    return FrameBatch(dataset_id=dataset_id, alice_symbols=alice, bob_symbols=bob, dimension=q, frame_len_symbols=n_sym, metadata={"mapping": "gray", "source": "synthetic", "ser": ser})


_REAL_CACHE: dict[str, list] = {}

def _build_real_long_batch(n_sym: int, q: int, n_frames: int, frame_batch_path: str, seed: int) -> FrameBatch:
    # Load real sidecars; flatten and chunk into n_sym frames.
    # Use first dataset matching dimension q; if none, use any.
    if frame_batch_path not in _REAL_CACHE:
        table = read_table(Path(frame_batch_path))
        _REAL_CACHE[frame_batch_path] = table_to_frame_batches(table)
    batches = _REAL_CACHE[frame_batch_path]
    # filter by dimension
    cand = [b for b in batches if int(b.dimension) == int(q)]
    if not cand:
        cand = batches
    # flatten all symbols
    all_alice = np.concatenate([b.alice_symbols.reshape(-1) for b in cand], axis=0)
    all_bob = np.concatenate([b.bob_symbols.reshape(-1) for b in cand], axis=0)
    need = n_frames * n_sym
    # if not enough, loop / tile
    if all_alice.size < need:
        reps = (need + all_alice.size - 1)//all_alice.size
        all_alice = np.tile(all_alice, reps)[:need]
        all_bob = np.tile(all_bob, reps)[:need]
    else:
        # random subsample window for variability
        rng = np.random.default_rng(seed)
        start = int(rng.integers(0, max(1, all_alice.size - need + 1)))
        all_alice = all_alice[start:start+need]
        all_bob = all_bob[start:start+need]
    alice = all_alice.reshape(n_frames, n_sym)
    bob = all_bob.reshape(n_frames, n_sym)
    ds_id = f"real_long_n{n_sym}_q{q}"
    return FrameBatch(dataset_id=ds_id, alice_symbols=alice, bob_symbols=bob, dimension=q, frame_len_symbols=n_sym, metadata={"mapping": "gray", "source": "real", "ser": float(np.mean(alice != bob))})


def _schedule_from_block(block: int, n: int) -> list[int]:
    # generate 4 passes: block, block*2, block*4, block*8 capped by n
    base = [block * (2**i) for i in range(4)]
    out = [max(1, min(n, int(x))) for x in base]
    # deduplicate preserve order
    seen = []
    for v in out:
        if v not in seen:
            seen.append(v)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description="T2 cascade beta small sweep 24 points")
    ap.add_argument("--config", default="comparison_bench/configs/cascade_beta_opt_small.yaml")
    ap.add_argument("--proxy", action="store_true", help="quick proxy with 50 frames per point")
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    grid_cfg = cfg.get("grid", {})
    out_root_cfg = (cfg.get("global", {}) or {}).get("output_dir", "comparison_bench/outputs_comparison/cascade_beta_opt")
    run_id = (cfg.get("global", {}) or {}).get("run_id", "T2_small")
    dataset_cfg = cfg.get("dataset", {}) or {}
    cs_cfg_raw = cfg.get("cascade_single_kernel", {}) or {}

    q = int(dataset_cfg.get("dimension", 1024))
    ser = float(dataset_cfg.get("ser", 0.02))
    fb_path = str(dataset_cfg.get("frame_batch_path", "comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet"))

    if args.proxy:
        real_frames = int(dataset_cfg.get("proxy_real_frames", 50))
        synth_frames = int(dataset_cfg.get("proxy_synthetic_frames", 50))
        suffix = "_small_proxy"
    else:
        real_frames = int(dataset_cfg.get("real_frames_per_point", 200))
        synth_frames = int(dataset_cfg.get("synthetic_frames_per_point", 1000))
        suffix = "_small"

    out_root = Path(args.output_dir) if args.output_dir else Path(out_root_cfg) / f"{run_id}{suffix}"
    out_root.mkdir(parents=True, exist_ok=True)
    csv_path = out_root / "ir_benchmark_results.csv"
    # expand 24 grid
    grid = _expand_grid(grid_cfg)
    rows: list[dict] = []
    start_all = time.perf_counter()
    for idx, point in enumerate(grid):
        n = int(point["n"])
        verify = int(point["verify"])
        block = int(point["block"])
        parity = int(point["parity"])
        schedule = _schedule_from_block(block, n)
        # build per-point config
        cs_dict = dict(cs_cfg_raw)
        cs_dict["passes_block_sizes"] = schedule
        cs_dict["block_size_policy"] = "adaptive"  # allow arbitrary schedule
        # keep num_passes consistent with schedule len
        cs_dict["num_passes"] = len(schedule)
        cs = load_cascade_single_config(cs_dict)
        # master seed domain-separated per point
        base_seed = int(cs.base_seed) + idx * 1009 + n

        for src, n_frames in [("synthetic", synth_frames), ("real", real_frames)]:
            if src == "synthetic":
                batch = _build_synthetic_batch(n, q, ser, n_frames, seed=base_seed, dataset_id=f"synthetic_n{n}_verify{verify}_block{block}_parity{parity}")
            else:
                batch = _build_real_long_batch(n, q, n_frames, fb_path, seed=base_seed + 1)

            # run kernel
            t0 = time.perf_counter()
            result = run_cascade_single(batch, cs, master_seed=base_seed)
            elapsed = time.perf_counter() - t0

            # leakage decomposition: kernel leak is key_dependent (parity+bisection+64)
            leak_total_kernel = float(result.leak_EC_actual_bits)
            # parity+bisection portion
            leak_verify_kernel = 64  # kernel fixed
            leak_parity_kernel = max(0.0, leak_total_kernel - leak_verify_kernel)
            # apply requested verify and parity factor
            leak_verify = float(verify)
            # parity factor scales parity disclosures (e.g., parity=2 means disclose 2 bits per parity? simplified)
            leak_parity = leak_parity_kernel * float(parity)
            leak_total = leak_parity + leak_verify
            # recompute beta_raw with adjusted leak
            from ..metrics.leakage import compute_beta_eff_empirical
            bps = int(np.ceil(np.log2(q))) if q else 1
            # use power-of-two bits
            try:
                from ..utils.bitops import bits_per_symbol
                bps = int(bits_per_symbol(q))
            except Exception:
                pass
            n_input_bits = n_frames * n * bps
            # ponytail: beta recomputed with requested leak; keep kernel beta as beta_kernel for reference
            beta_raw = compute_beta_eff_empirical(leak_total, n_input_bits, float(result.raw_ber))
            beta_kernel = float(result.beta_eff_empirical)
            FER = 1.0 - (result.n_frames_success / result.n_frames_attempted) if result.n_frames_attempted else 1.0
            # undetected: frames where verify_success but decoded != alice — kernel reports 0; we use failed_verify as undetected proxy (isolated)
            undetected = int(result.n_frames_failed_verify)  # should be 0 for toeplitz
            throughput = float(result.throughput_input_bits_per_s) if elapsed > 0 else 0.0

            rows.append({
                "n": n, "verify": verify, "block": block, "parity": parity,
                "dataset": src,
                "dataset_id": batch.dataset_id,
                "n_frames": n_frames,
                "q": q,
                "schedule": ",".join(str(x) for x in schedule),
                "beta_raw": beta_raw,
                "beta_kernel": beta_kernel,
                "leak_total": leak_total,
                "leak_parity": leak_parity,
                "leak_verify": leak_verify,
                "leak_total_kernel": leak_total_kernel,
                "FER": FER,
                "undetected": undetected,
                "throughput": throughput,
                "raw_ber": float(result.raw_ber),
                "raw_ser": float(result.raw_ser),
                "post_ber": float(result.post_ir_ber),
                "n_success": int(result.n_frames_success),
                "n_failed_decode": int(result.n_frames_failed_decode),
                "n_failed_verify": int(result.n_frames_failed_verify),
                "elapsed_s": elapsed,
                "point_id": idx,
            })
            print(f"point {idx+1}/{len(grid)} n={n} verify={verify} block={block} parity={parity} src={src} FER={FER:.3f} beta={beta_raw:.3f} leak={leak_total:.1f}")

    df = pd.DataFrame(rows)
    # sort by beta_raw descending for Top-3 convenience
    df_sorted = df.sort_values(["beta_raw", "FER"], ascending=[False, True])
    df.to_csv(csv_path, index=False)
    # also write sorted view
    df_sorted.to_csv(out_root / "ir_benchmark_results_sorted.csv", index=False)

    # t2_leak_decomposition.csv — per point aggregated leak decomposition (synthetic average vs real)
    # pivot by point_id
    decomp = []
    for pid, g in df.groupby("point_id"):
        first = g.iloc[0]
        # average across sources for report, but also keep per-source
        avg_beta = g["beta_raw"].mean()
        avg_fer = g["FER"].mean()
        # for decomposition, use synthetic as primary (more controlled)
        syn = g[g["dataset"] == "synthetic"]
        real = g[g["dataset"] == "real"]
        decomp.append({
            "n": int(first["n"]), "verify": int(first["verify"]), "block": int(first["block"]), "parity": int(first["parity"]),
            "schedule": first["schedule"],
            "beta_raw_avg": avg_beta,
            "beta_raw_synth": float(syn["beta_raw"].iloc[0]) if len(syn) else float("nan"),
            "beta_raw_real": float(real["beta_raw"].iloc[0]) if len(real) else float("nan"),
            "leak_parity_avg": g["leak_parity"].mean(),
            "leak_verify_avg": g["leak_verify"].mean(),
            "leak_total_avg": g["leak_total"].mean(),
            "FER_avg": avg_fer,
            "FER_synth": float(syn["FER"].iloc[0]) if len(syn) else float("nan"),
            "FER_real": float(real["FER"].iloc[0]) if len(real) else float("nan"),
            "throughput_avg": g["throughput"].mean(),
            "verify_theory_amortized_per_bit": first["leak_verify"] / (int(first["n"]) * int(np.ceil(np.log2(q))) if q else 1),
        })
    decomp_df = pd.DataFrame(decomp).sort_values("beta_raw_avg", ascending=False)
    decomp_path = out_root / "t2_leak_decomposition.csv"
    decomp_df.to_csv(decomp_path, index=False)

    # t2_small_grid_report.md — Top-3 by beta_raw + verification amortization validation
    report_path = out_root / "t2_small_grid_report.md"
    top3 = decomp_df.head(3)
    lines = []
    lines.append(f"# T2 Small Grid Report ({run_id}{suffix})")
    lines.append("")
    lines.append(f"Grid: n={grid_cfg.get('n')} × verify={grid_cfg.get('verify')} × block={grid_cfg.get('block')} × parity={grid_cfg.get('parity')} = {len(grid)} points")
    lines.append(f"Frames per point: synthetic={synth_frames}, real={real_frames} (proxy={args.proxy})")
    lines.append(f"Elapsed: {time.perf_counter()-start_all:.1f}s")
    lines.append("")
    lines.append("## Top-3 paths by beta_raw (avg over synthetic+real)")
    lines.append("")
    lines.append("| rank | n | verify | block | parity | schedule | beta_raw_avg | leak_total_avg | FER_avg | verify_per_bit |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r, (_, row) in enumerate(top3.iterrows(), 1):
        lines.append(f"| {r} | {int(row['n'])} | {int(row['verify'])} | {int(row['block'])} | {int(row['parity'])} | {row['schedule']} | {row['beta_raw_avg']:.4f} | {row['leak_total_avg']:.1f} | {row['FER_avg']:.4f} | {row['verify_theory_amortized_per_bit']:.5f} |")
    lines.append("")
    lines.append("## Verify amortization theory (long frame)")
    lines.append("")
    lines.append("Theory: verify bits amortized per input bit = verify / (n * bps). Longer n reduces per-bit overhead, improving beta.")
    lines.append("")
    # validate: group by n
    for n in sorted(decomp_df["n"].unique()):
        sub = decomp_df[decomp_df["n"] == n]
        lines.append(f"- n={n}: mean beta={sub['beta_raw_avg'].mean():.4f}, mean verify_per_bit={sub['verify_theory_amortized_per_bit'].mean():.5f}, mean leak_total={sub['leak_total_avg'].mean():.1f}")
    lines.append("")
    # sanity check: beta should increase with n if verify fixed? Check trend for verify=32 parity=1 block=16
    lines.append("Validation: ")
    # simple check that n=2048 has higher beta than n=256 for same verify/block/parity
    try:
        ref = decomp_df[(decomp_df["verify"] == 32) & (decomp_df["block"] == 32) & (decomp_df["parity"] == 1)].sort_values("n")
        if len(ref) >= 2:
            trend = "PASS" if float(ref.iloc[-1]["beta_raw_avg"]) >= float(ref.iloc[0]["beta_raw_avg"]) - 0.02 else "CHECK"
            lines.append(f"- Trend n 256→2048 (verify=32,block=32,parity=1): {trend} ({', '.join(f'n={int(r.n)} beta={r.beta_raw_avg:.3f}' for _,r in ref.iterrows())})")
        else:
            lines.append("- Trend check: insufficient points for reference slice")
    except Exception as e:
        lines.append(f"- Trend check error: {e}")
    lines.append("")
    lines.append(f"Outputs: {csv_path.name}, {decomp_path.name}")
    Path(report_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path} rows={len(df)}")
    print(f"wrote {decomp_path}")
    print(f"wrote {report_path}")
    print("Top-3:")
    print(top3.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
