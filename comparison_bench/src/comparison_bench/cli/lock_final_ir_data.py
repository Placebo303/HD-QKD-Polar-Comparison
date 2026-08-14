from __future__ import annotations

import argparse
from pathlib import Path

from ..data_lock import lock_frames, verify_lock


def main() -> int:
    ap = argparse.ArgumentParser(description="Lock Phase-2 frames for final IR method selection.")
    ap.add_argument("--source", default="comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet")
    ap.add_argument("--output-dir", default="comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1")
    ap.add_argument("--verify", action="store_true", help="verify an existing manifest instead of creating a lock")
    ap.add_argument("--manifest", help="manifest for --verify (default: OUTPUT-DIR/data_lock_manifest.json)")
    args = ap.parse_args()
    if args.verify:
        path = Path(args.manifest or Path(args.output_dir) / "data_lock_manifest.json")
        if not verify_lock(path):
            raise SystemExit("data lock verification failed")
        print(f"verified {path}")
        return 0
    manifest = lock_frames(Path(args.source), Path(args.output_dir))
    print(f"locked {manifest['counts']['tuning_frames']} tuning and {manifest['counts']['confirmation_frames']} confirmation frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
