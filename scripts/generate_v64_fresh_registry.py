"""Authoritative V64 fresh 24-block registry generator — 8/source strict, zero overlap V48-V63, K2>=24 hard, no fallback."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.formal_ir.v64_full_symbol_verification import build_v64_fresh_registry  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/v64_fresh_registry.json"

def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Generate authoritative v64_fresh_registry.json 24 blocks 8/source")
    p.add_argument("--output", default=str(DEFAULT_OUT), help="Output path for registry json")
    p.add_argument("--check-only", action="store_true", help="Only validate K2>=24 and zero overlap, do not write")
    args = p.parse_args(argv)
    try:
        reg = build_v64_fresh_registry()
    except ValueError as exc:
        print(f"EVIDENCE_INVALID: {exc}", file=sys.stderr)
        return 2
    # verify per-source 8
    from collections import Counter
    c = Counter(r["source"] for r in reg)
    if c["1M"] != 8 or c["1p5M"] != 8 or c["2M"] != 8 or len(reg) != 24:
        print(f"EVIDENCE_INVALID: per-source {dict(c)} len {len(reg)} !=24", file=sys.stderr)
        return 2
    if args.check_only:
        print(f"V64 registry check PASS 24 blocks K2 per-source 8 provenance {[r['H_provenance']['K2'] for r in reg[:3]]}")
        return 0
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print(f"V64 fresh registry written {out} ({len(reg)} blocks)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
