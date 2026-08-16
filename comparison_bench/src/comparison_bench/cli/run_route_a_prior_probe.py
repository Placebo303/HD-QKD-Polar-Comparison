"""Route A prior-calibration probe (A3b, diagnostic_only).

Decode the 128 failure frames with an oracle per-frame prior p=raw_ser, and
run a p-grid sweep on a deterministic 8-frame sample. This separates
prior-mismatch from code/graph limitation.
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
GRID_P = (0.16, 0.20, 0.24, 0.28, 0.32)
MAX_ITER = 100

def load_frames():
    frames = {}
    for tag, path in SOURCES:
        df = pd.read_parquet(path)
        for fid, sub in df.groupby('frame_id'):
            sub = sub.sort_values('pair_idx')
            frames[(tag, int(fid))] = {
                'alice': sub['alice_symbol'].to_numpy(dtype=np.int64),
                'bob': sub['bob_symbol'].to_numpy(dtype=np.int64),
            }
    return frames

def load_telemetry():
    tel = {}
    with (FULL / 'decoder_telemetry.jsonl').open(encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            d=json.loads(line)
            tel[(d['source_tag'], int(d['frame_id']))] = d.get('telemetry') or {}
    return tel

def bitplane_mismatch(alice, bob, q=1024):
    ab = symbols_to_bits(alice, q, mapping='gray')
    bb = symbols_to_bits(bob, q, mapping='gray')
    return [float(np.mean(ab[:, i] != bb[:, i])) for i in range(ab.shape[1])]

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = load_frames()
    tel = load_telemetry()
    failures = []
    with (FULL / 'audit_outcomes.csv').open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] != 'syndrome_consistent':
                failures.append({'source_tag': row['source_tag'], 'frame_id': int(row['frame_id']),
                                 'raw_ser': float(row['raw_ser'])})
    failures.sort(key=lambda x: (x['source_tag'], x['frame_id']))
    sample_idx = [int(round(i * (len(failures)-1) / (SAMPLE_SIZE-1))) for i in range(SAMPLE_SIZE)]
    sample = [failures[i] for i in sample_idx]

    manifest, matrix = r3.build_r3_codebook()

    # Feature table (A1 leftovers)
    feature_rows = []
    for fr in failures:
        tag, fid = fr['source_tag'], fr['frame_id']
        frame = frames[(tag, fid)]
        bpm = bitplane_mismatch(frame['alice'], frame['bob'])
        t = tel.get((tag, fid), {})
        feature_rows.append({
            'source_tag': tag, 'frame_id': fid, 'raw_ser': fr['raw_ser'],
            'bitplane_mismatch': bpm,
            'max_bitplane_mismatch': max(bpm), 'min_bitplane_mismatch': min(bpm),
            'lsb_mismatch': bpm[-1], 'msb_mismatch': bpm[0],
            'final_entropy': t.get('final_mean_posterior_entropy_bits'),
            'stagnation_iterations': t.get('stagnation_iterations'),
            'oscillation_detected': t.get('oscillation_detected'),
        })
    with (OUT / 'route_a_failure_features.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['source_tag','frame_id','raw_ser','bitplane_mismatch','max_bitplane_mismatch',
                    'min_bitplane_mismatch','lsb_mismatch','msb_mismatch','final_entropy',
                    'stagnation_iterations','oscillation_detected'])
        for r in feature_rows:
            w.writerow([r['source_tag'], r['frame_id'], r['raw_ser'], r['bitplane_mismatch'],
                        r['max_bitplane_mismatch'], r['min_bitplane_mismatch'], r['lsb_mismatch'],
                        r['msb_mismatch'], r['final_entropy'], r['stagnation_iterations'],
                        r['oscillation_detected']])

    # Oracle probe: p = raw_ser, all 128
    oracle_rows = []
    for n, fr in enumerate(failures, 1):
        tag, fid = fr['source_tag'], fr['frame_id']
        frame = frames[(tag, fid)]
        out = core._decode_frame_prebuilt(frame, manifest, matrix, max_iter=MAX_ITER, p=fr['raw_ser'])
        res = out['result']
        status = res.get('status')
        exact = False
        if status == 'syndrome_consistent':
            dec = tuple(int(x) for x in res.get('decoded_symbols', ()))
            exact = dec == tuple(int(x) for x in frame['alice'])
        oracle_rows.append({'source_tag': tag, 'frame_id': fid, 'raw_ser': fr['raw_ser'],
                            'p_prior': fr['raw_ser'], 'status': status,
                            'iterations': res.get('iterations', 0), 'exact_correct': exact})
        if n % 25 == 0:
            print(f'oracle progress {n}/{len(failures)} exact={sum(r["exact_correct"] for r in oracle_rows)}', flush=True)
    with (OUT / 'prior_probe_oracle_diagnostic.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_tag','frame_id','raw_ser','p_prior','status','iterations','exact_correct'])
        w.writeheader(); w.writerows(oracle_rows)

    # Grid sweep on sample
    grid_rows = []
    for fr in sample:
        tag, fid = fr['source_tag'], fr['frame_id']
        frame = frames[(tag, fid)]
        for p in GRID_P:
            out = core._decode_frame_prebuilt(frame, manifest, matrix, max_iter=MAX_ITER, p=p)
            res = out['result']
            status = res.get('status')
            exact = False
            if status == 'syndrome_consistent':
                dec = tuple(int(x) for x in res.get('decoded_symbols', ()))
                exact = dec == tuple(int(x) for x in frame['alice'])
            grid_rows.append({'source_tag': tag, 'frame_id': fid, 'raw_ser': fr['raw_ser'],
                              'p_prior': p, 'status': status, 'iterations': res.get('iterations', 0),
                              'exact_correct': exact})
    with (OUT / 'prior_grid_sample_diagnostic.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_tag','frame_id','raw_ser','p_prior','status','iterations','exact_correct'])
        w.writeheader(); w.writerows(grid_rows)

    summary = {
        'schema': 'nbldpc_v13r3_route_a_prior_probe_v1',
        'run_id': 'v13r3_legacy_route_a_prior_probe_20260816',
        'claim_boundary': 'diagnostic_only',
        'oracle': {
            'frames': len(oracle_rows),
            'exact_correct': sum(1 for r in oracle_rows if r['exact_correct']),
            'syndrome_consistent': sum(1 for r in oracle_rows if r['status'] == 'syndrome_consistent'),
            'decode_failed': sum(1 for r in oracle_rows if r['status'] != 'syndrome_consistent'),
        },
        'grid': {
            'sample_size': len(sample),
            'p_values': list(GRID_P),
            'decodes': len(grid_rows),
            'exact_correct': sum(1 for r in grid_rows if r['exact_correct']),
            'by_p': {str(p): {
                'exact_correct': sum(1 for r in grid_rows if r['p_prior'] == p and r['exact_correct']),
                'decode_failed': sum(1 for r in grid_rows if r['p_prior'] == p and r['status'] != 'syndrome_consistent'),
            } for p in GRID_P},
        },
    }
    (OUT / 'route_a_prior_probe_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
