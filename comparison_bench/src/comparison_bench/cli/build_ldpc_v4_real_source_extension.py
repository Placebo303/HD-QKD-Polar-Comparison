"""Build a no-overwrite binary-LDPC-v4 real source-extension manifest."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from ..formal_ir import ldpc_v4_real_source as source

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-source-manifest", type=Path, required=True)
    p.add_argument("--acquisitions-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    base = json.loads(a.base_source_manifest.read_bytes())
    acquisitions: Any = json.loads(a.acquisitions_json.read_bytes())
    print(source._compact(source.write_extension(a.output, base, acquisitions)).decode("ascii"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
