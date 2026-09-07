"""V72P2D5 Model-F input prepare/verify runner — implement-only, no execution.

Only ``--phase prepare|verify`` with ``--registry`` + ``--out-dir`` is
supported. ``--phase`` is required. Every phase refuses before any work
unless ``--execution-authorized`` is given. The single file read on the
authorized prepare path is the registry/parquet chain; verify is
read-only artifact load with no decoder and no parquet. No data tables
are read and no output is created while unauthorized.

Future real prepare needs a separate Pre-EXECUTE review + explicit
authorization; a prepare review must pass before any P0 authorization.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
CORE_PATH = (
    ROOT
    / "comparison_bench"
    / "src"
    / "comparison_bench"
    / "formal_ir"
    / "v72p2d5_model_f_input.py"
)

_SPEC = importlib.util.spec_from_file_location(
    "v72p2d5_model_f_input_core", str(CORE_PATH)
)
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)


def _load_state(path):
    """Parse the flat ``cycle_state.yaml`` into a plain dict."""
    state = {}
    with open(str(path), "r", encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip().strip("'\"").lower()
            if val in ("true", "false"):
                state[key] = val == "true"
            else:
                state[key] = val
    return state


def build_parser():
    ap = argparse.ArgumentParser(
        description="V72P2D5 Model-F input prepare/verify (authorization-gated)."
    )
    ap.add_argument(
        "--phase", required=True, choices=("prepare", "verify"),
        help="explicit phase to enter",
    )
    ap.add_argument("--registry", required=True, type=Path,
                    help="registry JSON for prepare (ignored by verify)")
    ap.add_argument("--out-dir", required=True, type=Path,
                    help="model-F input root (fresh for prepare, existing for verify)")
    ap.add_argument("--execution-authorized", action="store_true",
                    help="explicit authorization choke; absent refuses with exit 3")
    return ap


def _resolve_parquet_path(raw):
    """Resolve registry parquet_path vs Comparison repo root only."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("registry parquet_path must be a non-empty string")
    cand = Path(raw.strip())
    if not cand.is_absolute():
        cand = (ROOT / cand).resolve()
    else:
        cand = cand.resolve()
    if not cand.is_file():
        raise FileNotFoundError(f"parquet file not found: {cand}")
    return cand


def _load_cal_arrays(registry_path):
    """Real CAL loader: registry validate + parquet CAL702..1725 read.

    Separated for fake injection in tests; never entered while
    unauthorized. Rejects VAL use for fitting.
    """
    import json

    import pandas as pd

    reg_raw = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    schema = str(reg_raw.get("schema", ""))
    if schema != "v72p2d3_real_registry_v1":
        raise ValueError("registry schema must be v72p2d3_real_registry_v1")
    if str(reg_raw.get("session_id", "")) != "20260123_1M_600k_0dB":
        raise ValueError("registry session must be 20260123_1M_600k_0dB")
    cal_ids = [int(v) for v in reg_raw.get("cal_frame_ids", [])]
    if cal_ids != list(range(702, 1726)):
        raise ValueError("CAL ids must be the frozen 702..1725 sequence")
    val_ids = [int(v) for v in reg_raw.get("val_frame_ids", [])]
    if val_ids != [1726, 1727, 1728, 1729]:
        raise ValueError("VAL ids must stay 1726..1729 (never fit here)")
    parquet_path = _resolve_parquet_path(reg_raw.get("parquet_path", ""))
    cols = ["frame_id", "pair_idx", "alice_symbol", "bob_symbol"]
    df = pd.read_parquet(parquet_path, columns=cols)
    keep = df[df["frame_id"].isin(cal_ids)]
    if int(len(keep)) != 262144:
        raise ValueError("CAL retained rows must be 262144")
    alice = keep["alice_symbol"].to_numpy()
    bob = keep["bob_symbol"].to_numpy()
    frames = keep["frame_id"].to_numpy()
    return alice, bob, frames


def run_prepare(*, registry_path, out_dir, cal_loader=None):
    """Authorized prepare: registry/CAL -> build -> write 2 files."""
    loader = cal_loader if cal_loader is not None else _load_cal_arrays
    alice, bob, frames = loader(str(registry_path))
    built = _mod.build_model_f_input(alice, bob, frames)
    _mod.write_model_f_input(
        str(out_dir), built["counts_ab"], built["p_b"]
    )
    return {"phase": "prepare", "decoder_calls": 0, "p0_calls": 0,
            "val_rows_read": 0}


def run_verify(*, out_dir):
    """Authorized verify: read-only artifact load, no decoder/parquet."""
    loaded = _mod.load_model_f_input(str(out_dir))
    return {"phase": "verify", "n_symbols": 262144,
            "status": str(loaded["summary"].get("status", ""))}


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.execution_authorized:
        print(
            f"phase '{args.phase}' is not authorized; refusing before any work"
        )
        return 3
    try:
        if args.phase == "prepare":
            run_prepare(registry_path=args.registry, out_dir=args.out_dir)
        elif args.phase == "verify":
            run_verify(out_dir=args.out_dir)
        else:
            print(f"unknown phase '{args.phase}'")
            return 3
    except Exception as exc:
        print(f"phase '{args.phase}' refused: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
