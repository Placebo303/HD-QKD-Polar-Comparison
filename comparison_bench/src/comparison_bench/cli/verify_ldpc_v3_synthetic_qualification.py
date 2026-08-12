"""Strict, decoder-free Phase 6B qualification verifier."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
from typing import Any
from . import run_ldpc_v3_synthetic_qualification as lane
from ..formal_ir import ldpc_v3, ldpc_v3_ttbin_data as data
from ..formal_ir.shared import canonical_event, locked_seed_bits

def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
_BOOL={"attempted","denominator_included","verification_invoked"}
_INT={"n_pairs","dimension","frame_len_symbols","verification_tag_bits","key_dependent_disclosure_bits_total","public_control_bits_total","global_rounds_attempted","verification_check_count","ldpc_syndrome_bits","verification_tag_bits_component","transcript_bytes_len","transcript_first_event_id","transcript_last_event_id"}
_FLOAT={"raw_ser","epsilon_ec","runtime_s"}
_JSON={"candidate_ids"}
_OUTCOME_KEYS={"dataset_id","frame_id","n_pairs","pair_idx_sequence_sha256","method","attempted","denominator_included","status","failure_reason","dimension","frame_len_symbols","raw_ser","verification_invoked","verification_seed_id","verification_tag_bits","epsilon_ec","key_dependent_disclosure_bits_total","public_control_bits_total","transcript_first_event_id","transcript_last_event_id","transcript_sha256","runtime_s","global_rounds_attempted","verification_check_count","terminal_prefix_id","ldpc_syndrome_bits","verification_tag_bits_component","selection_binding_sha256","candidate_ids","calibration_sha256","mapping","leakage_comparison_policy","backend_name","backend_version"}
_PRIVATE_PLAN_KEYS={"run_id","frozen_calibration","caps","execution_order","toeplitz_seeds","_test_only","selected_candidate_binding_sha256","generator_contract","plan_sha256"}
_PRODUCTION_PLAN_KEYS={"run_id","method","dimension","mapping","frame_len_symbols","source_manifest_sha256","locked_data_sha256","locked_data","frozen_calibration","selected_candidate_binding_sha256","source_sha256","caps","generator_contract","execution_order","failure_finalizer","toeplitz_seeds","_test_only","plan_sha256"}
def _rows(p:Path)->list[dict[str,Any]]:
    with p.open(encoding='utf-8',newline='') as h: raw=list(csv.DictReader(h))
    out=[]
    for r in raw:
        row={}
        for k,v in r.items():
            if k in _BOOL:
                if v not in ('True','False'): raise ValueError('csv bool')
                row[k]=v=='True'
            elif k in _INT:
                if k in {"transcript_first_event_id","transcript_last_event_id"} and v=='': row[k]=None; continue
                if not v or str(int(v)) != v: raise ValueError('csv int')
                row[k]=int(v)
            elif k in _FLOAT:
                row[k]=float(v)
                if not __import__('math').isfinite(row[k]) and k != 'raw_ser': raise ValueError('csv float')
            elif k in _JSON:
                row[k]=json.loads(v)
            else: row[k]=v
        out.append(row)
    return out
def _plan(plan:dict[str,Any], private:bool)->None:
    if set(plan) != (_PRIVATE_PLAN_KEYS if private else _PRODUCTION_PLAN_KEYS): raise ValueError('plan schema')
    if plan.get('plan_sha256')!=_sha(lane._compact({k:v for k,v in plan.items() if k!='plan_sha256'})):raise ValueError('plan hash')
    if set(plan.get('generator_contract',{})) != {'algorithm','root_seeds','mask_call_order','gray_inverse'} or plan['generator_contract']['algorithm']!='PCG64' or plan['generator_contract']['root_seeds']!=lane.ROOT_SEEDS or plan['generator_contract']['mask_call_order']!='stratum, plane 0..9, rng.random((32,256))' or plan['generator_contract']['gray_inverse']!='xor shifts 1,2,4,8':raise ValueError('generator contract')
    if plan.get('execution_order')!=lane._order() or set(plan.get('toeplitz_seeds',{}))!=set(lane._order()):raise ValueError('order/seeds')
    ids=[]
    for seed in plan['toeplitz_seeds'].values(): locked_seed_bits(seed,lane.SEED_BITS); ids.append(seed['seed_id'])
    if len(set(ids))!=64:raise ValueError('seed uniqueness')
    if plan.get('caps')!={'per_frame':ldpc_v3.DEFAULT_CAPS,'complete_run_s':1800} or plan.get('selected_candidate_binding_sha256')!=ldpc_v3.SELECTION_BINDING_SHA256:raise ValueError('frozen protocol')
    if not private:
        if plan.get('source_sha256')!=lane._source_hashes():raise ValueError('source hashes')
        data.verify_locked_data(plan.get('locked_data',{}))
        if plan.get('locked_data_sha256')!=plan['locked_data'].get('lock_sha256') or plan.get('source_manifest_sha256')!=plan['locked_data'].get('source_manifest_sha256') or plan.get('frozen_calibration')!=plan['locked_data'].get('calibration'):raise ValueError('locked data')
def verify(output:Path, *, _private_test_only:bool=False)->dict[str,Any]:
    if not output.is_dir() or {x.name for x in output.iterdir()}!=set(lane.ARTIFACTS):raise ValueError('six artifact contract')
    plan=json.loads((output/lane.ARTIFACTS[0]).read_text()); manifest=json.loads((output/lane.ARTIFACTS[3]).read_text()); report=json.loads((output/lane.ARTIFACTS[5]).read_text())
    if bool(plan.get('_test_only')) != bool(_private_test_only):raise ValueError('test-only plan')
    _plan(plan,_private_test_only)
    if json.loads((output/lane.ARTIFACTS[4]).read_text())!=lane._codebook_manifest():raise ValueError('codebook reconstruction')
    if set(manifest)!={'run_id','schema','run_status','stop_reason','plan_sha256','artifacts','outcome_count','decoder_reexecution'} or manifest['schema']!='binary_ldpc_v3_phase6b_run_manifest_v1' or manifest['run_id']!=lane.RUN_ID or manifest['decoder_reexecution'] is not False or not isinstance(manifest['outcome_count'],int) or isinstance(manifest['outcome_count'],bool) or not isinstance(manifest['stop_reason'],str):raise ValueError('manifest schema')
    if set(report)!={'run_id','schema','run_status','stop_reason','promotion_gates','promoted','formal_run_manifest_sha256','decoder_reexecution'} or report['schema']!='binary_ldpc_v3_phase6b_report_v1' or report['run_id']!=lane.RUN_ID or report['decoder_reexecution'] is not False or not isinstance(report['stop_reason'],str) or not isinstance(report['promoted'],bool):raise ValueError('report schema')
    if manifest['plan_sha256']!=_sha((output/lane.ARTIFACTS[0]).read_bytes()) or manifest['artifacts']!=lane._artifact_hashes(output) or report['formal_run_manifest_sha256']!=_sha((output/lane.ARTIFACTS[3]).read_bytes()) or report['run_status']!=manifest['run_status']:raise ValueError('artifact DAG')
    rows=_rows(output/lane.ARTIFACTS[1]); events=[json.loads(x) for x in (output/lane.ARTIFACTS[2]).read_bytes().splitlines()];
    if len(rows)!=manifest['outcome_count'] or len(rows)>64 or [r.get('plan_frame_id') for r in rows]!=plan['execution_order'][:len(rows)]:raise ValueError('partial execution order')
    cursor=0; groups={'calibrated':[],'stress_125':[]}
    for row in rows:
        key=row['plan_frame_id']; s,fid=key.split(':f'); a,b=lane._synthetic_pair(s,int(fid),plan['frozen_calibration'])
        expected_seed=plan['toeplitz_seeds'][key]['seed_id'] if row.get('attempted') else ''
        if row.get('stratum')!=s or row.get('dataset_id')!=f'synthetic_{s}' or row.get('frame_id')!=key or row.get('alice_sha256')!=_sha(a.astype('<i8').tobytes()) or row.get('bob_sha256')!=_sha(b.astype('<i8').tobytes()) or row.get('verification_seed_id')!=expected_seed:raise ValueError('frame provenance')
        start=cursor; frame_key=f"{row['dataset_id']}:{row['frame_id']}"
        while cursor<len(events) and events[cursor]['frame_key']==frame_key:cursor+=1
        es=events[start:cursor];
        if set(row) != _OUTCOME_KEYS | {'stratum','plan_frame_id','transcript_bytes_len','transcript_bytes_sha256','alice_sha256','bob_sha256'}: raise ValueError(f'outcome csv schema: {sorted(set(row)^(_OUTCOME_KEYS | {"stratum","plan_frame_id","transcript_bytes_len","transcript_bytes_sha256","alice_sha256","bob_sha256"}))}')
        outcome={k:row[k] for k in _OUTCOME_KEYS}; ldpc_v3.validate_outcome_v3(outcome,es); blob=b''.join(canonical_event(e) for e in es)
        if row['transcript_bytes_len']!=len(blob) or row['transcript_bytes_sha256']!=_sha(blob):raise ValueError('transcript')
        groups[s].append(row)
    if cursor!=len(events) or b''.join(canonical_event(e) for e in events)!=(output/lane.ARTIFACTS[2]).read_bytes():raise ValueError('transcript grouping')
    gates={s:lane._gate(groups[s]) for s in groups}
    if manifest['run_status']=='completed':
        if manifest['stop_reason'] or report['stop_reason'] or len(rows)!=64 or report['promotion_gates']!=gates or report['promoted']!=all(g['promoted'] for g in gates.values()):raise ValueError('completed gates')
    elif manifest['run_status']=='non_promoted':
        if report['promoted'] or report['promotion_gates']!=gates or not manifest['stop_reason'] or not report['stop_reason']:raise ValueError('failure finalization')
    else:raise ValueError('manifest status')
    return {'verified':True,'run_status':manifest['run_status'],'outcomes':len(rows),'decoder_reexecution':False}
def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.output_dir),sort_keys=True))
if __name__=='__main__':main()
