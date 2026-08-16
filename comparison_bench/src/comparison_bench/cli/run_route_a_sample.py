"""Route A sampled max_iter=500 diagnostic.

Instead of re-decoding all 128 failures at max_iter=500 (very slow), select a
deterministic sample and report whether any can be rescued. Diagnostic only.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v13r3_legacy_audit as core
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v13_r3_candidate as r3
from comparison_bench.src.comparison_bench.utils.bitops import symbols_to_bits

BASE = Path('comparison_bench/outputs_comparison/nonbinary_diagnostics')
FULL = BASE / 'v13r3_legacy_drift_audit_full_20260816'
OUT = BASE / 'v13r3_legacy_route_a_20260816'
SOURCES = [
    ('type2_1p5M_20260121_183806', BASE / 'v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet'),
    ('type2_1M_20260121_184040', BASE / 'v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet'),
    ('type2_2M_20260121_183657', BASE / 'v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet'),
]
SAMPLE_SIZE = 8
MAX_ITER = 500

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    with (FULL / 'audit_outcomes.csv').open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] != 'syndrome_consistent':
                failures.append((row['source_tag'], int(row['frame_id']), float(row['raw_ser'])))
    failures.sort(key=lambda x: (x[0], x[1]))
    # Deterministic evenly-spaced sample across the sorted failure list.
    idx = [int(round(i * (len(failures)-1) / (SAMPLE_SIZE-1))) for i in range(SAMPLE_SIZE)]
    sample = [failures[i] for i in idx]

    frames = {}
    for tag, path in SOURCES:
        df = pd.read_parquet(path)
        for fid, sub in df.groupby('frame_id'):
            sub = sub.sort_values('pair_idx')
            frames[(tag, int(fid))] = {
                'alice': sub['alice_symbol'].to_numpy(dtype=np.int64),
                'bob': sub['bob_symbol'].to_numpy(dtype=np.int64),
            }

    manifest, matrix = r3.build_r3_codebook()
    rows = []
    for n, (tag, fid, ser) in enumerate(sample, 1):
        frame = frames[(tag, fid)]
        out = core._decode_frame_prebuilt(frame, manifest, matrix, max_iter=MAX_ITER)
        res = out['result']
        status = res.get('status')
        exact = False
        if status == 'syndrome_consistent':
            dec = tuple(int(x) for x in res.get('decoded_symbols', ()))
            exact = dec == tuple(int(x) for x in frame['alice'])
        rows.append({
            'source_tag': tag, 'frame_id': fid, 'raw_ser': ser,
            'max_iter': MAX_ITER, 'status': status,
            'iterations': res.get('iterations', 0), 'exact_correct': exact,
        })
        print(f'progress {n}/{len(sample)} frame {tag}:{fid} status={status} exact={exact}', flush=True)

    out_csv = OUT / 'max_iter_500_sample_diagnostic.csv'
    with out_csv.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_tag','frame_id','raw_ser','max_iter','status','iterations','exact_correct'])
        w.writeheader(); w.writerows(rows)
    summary = {
        'schema': 'nbldpc_v13r3_route_a_sample_v1',
        'run_id': 'v13r3_legacy_route_a_sample_20260816',
        'claim_boundary': 'diagnostic_only',
        'sample_size': len(rows),
        'max_iter': MAX_ITER,
        'exact_correct': sum(1 for r in rows if r['exact_correct']),
        'decode_failed': sum(1 for r in rows if r['status'] != 'syndrome_consistent'),
        'sample_frame_ids': [(r['source_tag'], r['frame_id']) for r in rows],
    }
    (OUT / 'route_a_sample_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
