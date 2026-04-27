#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import ensure_output_dir, write_text


def main() -> int:
    ap = argparse.ArgumentParser(description='Build a manifest of reusable fresh rerun artifacts for minimal rerun.')
    ap.add_argument('--input-dirs', nargs='*', default=[])
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    if bool(args.overwrite):
        ensure_output_dir(out_dir, overwrite=True)
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
    audit_path = out_dir / 'frame_accounting_input_audit.csv'
    if not audit_path.exists():
        raise SystemExit('frame_accounting_input_audit.csv not found; run Stage A audit first')
    audit = pd.read_csv(audit_path)
    lines = [
        '# Reuse Manifest',
        '',
        '## Decision',
        '- Reuse fresh rerun candidate, stage1 actual replay, and stage2 security outputs.',
        '- Do not rerun ttbin parsing, sidecar generation, pairing/materialization, or full polar search.',
        '',
        '## Counts',
        f"- points: {len(audit)}",
        f"- minrerun_ready: {int(audit['minrerun_status'].eq('minrerun_ready').sum())}",
        f"- replay_patch_needed: {int(audit['minrerun_status'].eq('replay_patch_needed').sum())}",
        f"- front_half_rerun_required: {int(audit['minrerun_status'].eq('front_half_rerun_required').sum())}",
        '',
        '## Reused Artifacts',
        '- replay_index_point_table.csv / replay_index_layer_table.csv',
        '- actual_ir_block_table.csv / actual_ir_point_table.csv',
        '- security_calibrated_master_table.csv / finite_key_audit_point_table.csv',
        '- sidecar occupancy_filter_summary.csv',
        '- a_eff.npy / b_eff.npy only as provenance anchors, not for full rerun',
    ]
    write_text(out_dir / 'reuse_manifest.md', '\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

