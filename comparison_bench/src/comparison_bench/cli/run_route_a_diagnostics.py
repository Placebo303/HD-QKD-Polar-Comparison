"""Route A diagnostics for V13-R3 legacy drift audit failures.

Reads the full audit outcomes/telemetry and the D4 pairs tables, computes
failure-frame features, then re-decodes the 128 failures with max_iter=200
and 500 (diagnostic only, not a formal claim).
"""
from __future__ import annotations

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v13r3_legacy_audit as core
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v13_r3_candidate as r3

import csv
import json
import time
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd

from comparison_bench.src.comparison_bench.utils.bitops import symbols_to_bits

BASE = Path('comparison_bench/outputs_comparison/nonbinary_diagnostics')
FULL = BASE / 'v13r3_legacy_drift_audit_full_20260816'
OUT = BASE / 'v13r3_legacy_route_a_20260816'

SOURCES = [
    ('type2_1p5M_20260121_183806', BASE / 'v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet'),
    ('type2_1M_20260121_184040', BASE / 'v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet'),
    ('type2_2M_20260121_183657', BASE / 'v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet'),
]

def load_frames() -> dict[tuple[str,int], dict]:
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

def bitplane_mismatch(alice, bob, q=1024):
    ab = symbols_to_bits(alice, q, mapping='gray')
    bb = symbols_to_bits(bob, q, mapping='gray')
    return [float(np.mean(ab[:, i] != bb[:, i])) for i in range(ab.shape[1])]

def load_telemetry():
    tel = {}
    with (FULL / 'decoder_telemetry.jsonl').open(encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            d=json.loads(line)
            tel[(d['source_tag'], int(d['frame_id']))] = d.get('telemetry') or {}
    return tel

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = load_frames()
    tel = load_telemetry()
    failures=[]
    with (FULL / 'audit_outcomes.csv').open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] == 'syndrome_consistent':
                continue
            tag=row['source_tag']; fid=int(row['frame_id'])
            alice=frames[(tag,fid)]['alice']; bob=frames[(tag,fid)]['bob']
            bpm = bitplane_mismatch(alice, bob)
            t = tel.get((tag,fid), {})
            failures.append({
                'source_tag': tag, 'frame_id': fid,
                'raw_ser': float(row['raw_ser']),
                'status': row['status'], 'reason': row['reason'],
                'iterations_original': int(row['iterations']),
                'bitplane_mismatch': bpm,
                'max_bitplane_mismatch': max(bpm),
                'min_bitplane_mismatch': min(bpm),
                'lsb_mismatch': bpm[-1],
                'msb_mismatch': bpm[0],
                'telemetry': t,
                'final_entropy': t.get('final_mean_posterior_entropy_bits'),
                'final_max': t.get('final_mean_posterior_max'),
                'stagnation_iterations': t.get('stagnation_iterations'),
                'oscillation_detected': t.get('oscillation_detected'),
            })
    print('failure count', len(failures))

    # Re-decode with max_iter=200 and 500
    manifest, matrix = r3.build_r3_codebook()
    for mi in (200, 500):
        count_exact=0; count_consistent=0; count_fail=0
        rows=[]
        for i, fr in enumerate(failures, 1):
            tag=fr['source_tag']; fid=fr['frame_id']
            frame=frames[(tag,fid)]
            out=core._decode_frame_prebuilt(frame, manifest, matrix, max_iter=mi)
            res=out['result']
            status=res.get('status')
            exact=False
            if status=='syndrome_consistent':
                count_consistent += 1
                dec=tuple(int(x) for x in res.get('decoded_symbols', ()))
                exact = dec == tuple(int(x) for x in frame['alice'])
                if exact: count_exact += 1
            else:
                count_fail += 1
            rows.append({'source_tag':tag,'frame_id':fid,'max_iter':mi,
                         'status':status,'iterations':res.get('iterations',0),
                         'exact_correct':exact,
                         'final_entropy': (out.get('telemetry') or {}).get('final_mean_posterior_entropy_bits')})
            if i % 25 == 0:
                print('  max_iter',mi,'progress',i,'/',len(failures),'exact',count_exact,'fail',count_fail)
        path=OUT / f'max_iter_{mi}_diagnostic.csv'
        with path.open('w', encoding='utf-8', newline='') as f:
            w=csv.DictWriter(f, fieldnames=['source_tag','frame_id','max_iter','status','iterations','exact_correct','final_entropy'])
            w.writeheader(); w.writerows(rows)
        print('max_iter',mi,'consistent',count_consistent,'exact',count_exact,'fail',count_fail,'->',path)

    # Write feature report
    summary = {
        'schema': 'nbldpc_v13r3_route_a_diagnostics_v1',
        'run_id': 'v13r3_legacy_route_a_20260816',
        'claim_boundary': 'diagnostic_only',
        'failure_count': len(failures),
        'raw_ser_mean': float(np.mean([x['raw_ser'] for x in failures])),
        'bitplane_mismatch_mean': [float(np.mean([x['bitplane_mismatch'][i] for x in failures])) for i in range(10)],
        'final_entropy_mean': float(np.mean([x['final_entropy'] for x in failures if x['final_entropy'] is not None])),
        'stagnation_mean': float(np.mean([x['stagnation_iterations'] for x in failures if x['stagnation_iterations'] is not None])),
        'oscillation_count': int(sum(1 for x in failures if x['oscillation_detected'])),
    }
    (OUT / 'route_a_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print('summary written', OUT)

if __name__ == '__main__':
    main()
