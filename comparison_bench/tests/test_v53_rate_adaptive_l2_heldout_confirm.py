"""Focused V53P0 tests (decoder-free, fake-runner) for nested heldout confirm."""
from __future__ import annotations
import csv, json, subprocess, sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, compute_gf32_rank, compute_tag_64, load_v25_channel_counts
from comparison_bench.formal_ir import v53_rate_adaptive_l2_heldout_confirm as v53
import comparison_bench.formal_ir.v38_architecture_triage as v38
SCRIPT_PATH = Path(__file__).resolve().parents[2].parent / "scripts" / "execute_v53_heldout_confirm.py"
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v53_heldout_confirm.py"
    if not SCRIPT_PATH.exists():
        SCRIPT_PATH = Path("D:/Code/HD-QKD_Polar_Comparison/scripts/execute_v53_heldout_confirm.py")
OUTPUT_ROOT_REAL = Path(__file__).resolve().parents[2] / "outputs_comparison" / "formal_ir_methods" / "v53_rate_adaptive_l2_heldout_confirm" / "run_01"
if not OUTPUT_ROOT_REAL.exists():
    OUTPUT_ROOT_REAL = Path("D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/formal_ir_methods/v53_rate_adaptive_l2_heldout_confirm/run_01")
@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()
class FakeWorld:
    def __init__(self):
        self.constructors = {"lane_c": self._make_ctor()}
    def _make_ctor(self):
        def _ctor(source: str, seed: int, field=None):
            field = field or GF2mField.create(32)
            H, metrics = v38.construct_lane_c_prototype(source=source, seed=seed, field=field)
            return H, metrics
        return _ctor
    def authority_file(self, tmp_path: Path) -> Path:
        records: list[dict] = []
        field = GF2mField.create(32)
        for source in v53.SOURCE_ORDER:
            seed = v53._rep_seed("lane_c", source)
            H, met = v38.construct_lane_c_prototype(source=source, seed=seed, field=field)
            records.append(dict(met))
        for i in range(24):
            records.append({"lane":"lane_a","source":"1M","construction_seed":900000+i,"matrix_id":f"lane_a_1M_s{900000+i}","shape":[4,1024],"rank_GF32":4,"support_edge_count":10,"col_degree_min":0,"col_degree_mean":0,"col_degree_max":1,"row_degree_min":1,"row_degree_mean":1,"row_degree_max":1,"degenerate_cycles_4":0,"degenerate_cycles_6":0,"degenerate_cycles_8":0,"support_cycles_4":0,"structurally_valid":True,"position_permutations":[[0]]})
        records = records[:27]
        for src in v53.SOURCE_ORDER:
            mid = f"lane_c_{src}_s{v53._rep_seed('lane_c', src)}"
            assert any(r["matrix_id"]==mid for r in records)
        path = tmp_path / "fake_authority_v53.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

def _run_with_pattern(tmp_path, monkeypatch, real_counts, base_results: list[bool], rescue_results: list[bool], name="run"):
    call_log: list[dict] = []
    base_ptr = {"i":0}
    rescue_ptr = {"i":0}
    orig = v53._evaluate_one_l2
    def patched(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        call_log.append({"source":source,"block_seed":block_seed,"arm":spec.get("arm"),"matrix_shape":matrix.shape})
        empty=np.empty(0,dtype=np.uint8)
        arm=spec.get("arm")
        if arm=="base_shared":
            idx=base_ptr["i"]; base_ptr["i"]+=1
            ok=base_results[idx] if idx<len(base_results) else True
            if ok:
                target=compute_tag_64(empty,u2_alice)
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(v53.BLOCK_WINDOWS[block_seed]["frame_ids"]),"held_out_ordinal_start":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]),"held_out_ordinal_end":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":0,"exact_l2":bool(ok),"exact_u1":True,"exact_full":bool(ok),"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":v53.classify_reclassified(ok,True,True),"iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
            else:
                target=compute_tag_64(empty,u2_alice); alt=compute_tag_64(empty,(u2_alice+1)%32)
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(v53.BLOCK_WINDOWS[block_seed]["frame_ids"]),"held_out_ordinal_start":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]),"held_out_ordinal_end":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":10,"exact_l2":False,"exact_u1":True,"exact_full":False,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":alt,"tag_ok":False,"tag_scope":v53.TAG_SCOPE,"reclassified":"detected_verification_failure","iterations_l1":5,"iterations_l2":90,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"max_iter","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
        else:
            idx=rescue_ptr["i"]; rescue_ptr["i"]+=1
            ok=rescue_results[idx] if idx<len(rescue_results) else False
            target=compute_tag_64(empty,u2_alice)
            if ok:
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(v53.BLOCK_WINDOWS[block_seed]["frame_ids"]),"held_out_ordinal_start":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]),"held_out_ordinal_end":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_joint_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"rescue","pass_index":2,"used_increment":True,"joint":True}
            else:
                alt=compute_tag_64(empty,(u2_alice+1)%32)
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(v53.BLOCK_WINDOWS[block_seed]["frame_ids"]),"held_out_ordinal_start":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_start"]),"held_out_ordinal_end":int(v53.BLOCK_WINDOWS[block_seed]["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":10,"exact_l2":False,"exact_u1":True,"exact_full":False,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":alt,"tag_ok":False,"tag_scope":v53.TAG_SCOPE,"reclassified":"detected_verification_failure","iterations_l1":5,"iterations_l2":90,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_joint_for(source),"leak_joint":v53.leak_joint_for(source),"status":"max_iter","runtime_s":0.001,"arm":"rescue","pass_index":2,"used_increment":True,"joint":True}
    monkeypatch.setattr(v53, "_evaluate_one_l2", patched)
    world=FakeWorld()
    root=tmp_path/name
    result=v53.run_v53_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    monkeypatch.setattr(v53, "_evaluate_one_l2", orig)
    return result,root,call_log

def test_fresh45_zero_overlap():
    assert len(v53.NEW_BLOCK_SEEDS["1M"])==15
    assert v53.NEW_BLOCK_SEEDS["1M"]==[394001,394002,394003,394004,394005,394006,394007,394008,394009,394010,394011,394012,394013,394014,394015]
    assert v53.NEW_BLOCK_SEEDS["1p5M"]==[394101,394102,394103,394104,394105,394106,394107,394108,394109,394110,394111,394112,394113,394114,394115]
    assert v53.NEW_BLOCK_SEEDS["2M"]==[394201,394202,394203,394204,394205,394206,394207,394208,394209,394210,394211,394212,394213,394214,394215]
    flat=[s for src in v53.SOURCE_ORDER for s in v53.NEW_BLOCK_SEEDS[src]]
    assert len(flat)==45 and len(set(flat))==45
    assert set(flat) & v53.FORBIDDEN_171 == set()
    assert len(v53.FORBIDDEN_171)==171
    assert v53.BLOCK_WINDOWS[394001]["frame_ids"]==[1678,1679,1680,1681]
    assert v53.BLOCK_WINDOWS[394215]["frame_ids"]==[3637,3638,3639,3640]
    for src in v53.SOURCE_ORDER:
        assert v53.V52_HELDOUT_FRAME_IDS[src] & v53.V48_HELDOUT_FRAME_IDS[src]==set()
        assert v53.V52_HELDOUT_FRAME_IDS[src] & v53.V50_HELDOUT_FRAME_IDS[src]==set()
        assert v53.V52_HELDOUT_FRAME_IDS[src] & v53.V51_HELDOUT_FRAME_IDS[src]==set()
        # V53 vs V52 zero overlap per source
        v53_ids=v53.NEW_BLOCK_SEEDS[src]
        v53_frames=set().union(*[set(v53.BLOCK_WINDOWS[bid]["frame_ids"]) for bid in v53_ids])
        assert v53_frames & v53.V52_HELDOUT_FRAME_IDS[src]==set()
        assert v53_frames & v53.V48_HELDOUT_FRAME_IDS[src]==set()
    # also within V53 no overlap
    all_f=[v53.BLOCK_WINDOWS[bid]["frame_ids"] for src in v53.SOURCE_ORDER for bid in v53.NEW_BLOCK_SEEDS[src]]
    flat_frames=[fid for lst in all_f for fid in lst]
    assert len(flat_frames)==180 and len(set(flat_frames))==180
    ok,msg=v53.validate_seed_registry()
    assert ok,msg

def test_h_joint_rank_nested_plus40():
    field=GF2mField.create(32)
    mats=v53.reconstruct_v53_matrices(field=field)
    for src in v53.SOURCE_ORDER:
        H_base=mats[("lane_c",src)][0]; H_inc=mats[("h_inc",src)][0]; H_joint=mats[("h_joint",src)][0]
        m2=v53.SOURCE_CHECKS[src]
        assert H_base.shape==(m2,1024); assert H_inc.shape==(8,1024); assert H_joint.shape==(m2+8,1024)
        assert int(compute_gf32_rank(H_base,field))==m2
        assert int(compute_gf32_rank(H_joint,field))==m2+8
        assert np.array_equal(H_joint[0:m2,:],H_base)
        assert int(compute_gf32_rank(H_joint,field))-int(compute_gf32_rank(H_base,field))==8
        Hs_inc=(H_inc!=0).astype(np.uint8)
        assert int(np.count_nonzero(Hs_inc,axis=0).max())<=1
        assert int(np.count_nonzero(Hs_inc,axis=1).max())<=16
        assert v53.leak_joint_for(src)-v53.leak_for(src)==40
    pre=v53.nested_rescue_preflight(matrices=mats, field=field)
    assert pre["nested_ok"] is True
    for src in v53.SOURCE_ORDER:
        assert pre["per_source"][src]["joint_rank_ok"] is True
        assert pre["per_source"][src]["independence_ok"] is True
        assert pre["per_source"][src]["leakage_accounted"] is True

def test_dedup_old_equals_base(tmp_path, monkeypatch, real_counts):
    base_results=[True]*45
    result,root,log=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_results,[],name="dedup")
    records=json.loads((root/"v53_records.json").read_text(encoding="utf-8"))
    assert len(records)==45
    assert all(r["arm"]=="base_shared" for r in records)
    assert len([c for c in log if c["arm"]=="base_shared"])==45
    assert len([c for c in log if c["arm"]=="rescue"])==0
    summary=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["old_exact_full"]==summary["counts"]["base_exact_full"]==45
    assert summary["counts"]["verify_base"]==45
    assert summary["counts"]["final_exact_full"]==45
    assert summary["leakage"]["n_rescue_attempted"]==0
    assert summary["leakage"]["total_disclosed_bits"]== sum(v53.leak_for(s) for s in v53.SOURCE_ORDER for _ in range(15))
    assert summary["leakage"]["disclosure_per_final_exact_block"]== pytest.approx(summary["leakage"]["total_disclosed_bits"]/45)

def test_budget_three_boundaries(tmp_path, monkeypatch, real_counts):
    base_all_pass=[True]*45
    r0,root0,log0=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_all_pass,[],name="budget0")
    s0=json.loads((root0/"v53_summary.json").read_text(encoding="utf-8"))
    assert s0["accounting"]["decoder_calls_completed"]["total"]==90
    assert s0["accounting"]["decoder_calls_completed"]["l1"]==45
    assert s0["accounting"]["decoder_calls_completed"]["base"]==45
    assert s0["accounting"]["decoder_calls_completed"]["rescue"]==0
    assert len(json.loads((root0/"v53_records.json").read_text(encoding="utf-8")))==45
    base_partial=[True]*30+[False]*15
    rescue_partial=[True]*10+[False]*5
    r1,root1,log1=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_partial,rescue_partial,name="budgetPartial")
    s1=json.loads((root1/"v53_summary.json").read_text(encoding="utf-8"))
    assert s1["leakage"]["n_rescue_attempted"]==15
    assert s1["accounting"]["decoder_calls_completed"]["total"]==45+45+15
    assert len(json.loads((root1/"v53_records.json").read_text(encoding="utf-8")))==60
    rescue_blocks={r["block_seed"] for r in json.loads((root1/"v53_records.json").read_text(encoding="utf-8")) if r["arm"]=="rescue"}
    assert len(rescue_blocks)==15
    base_all_fail=[False]*45
    rescue_all=[False]*45
    r2,root2,log2=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_all_fail,rescue_all,name="budgetAll")
    s2=json.loads((root2/"v53_summary.json").read_text(encoding="utf-8"))
    assert s2["leakage"]["n_rescue_attempted"]==45
    assert s2["accounting"]["decoder_calls_completed"]["total"]==135
    assert s2["accounting"]["decoder_calls_completed"]["rescue"]==45
    assert len(json.loads((root2/"v53_records.json").read_text(encoding="utf-8")))==90
    acc=v53.CallAccounting(hard_cap=135)
    for _ in range(45):
        acc.register_start(layer="l1"); acc.register_complete(layer="l1")
    for _ in range(45):
        acc.register_start(layer="base"); acc.register_complete(layer="base")
    for _ in range(45):
        acc.register_start(layer="rescue"); acc.register_complete(layer="rescue")
    with pytest.raises(v53.IntegrityFailure) as e:
        acc.register_start()
    assert e.value.check_id=="J10"
    with pytest.raises(v53.IntegrityFailure):
        acc.register_start(layer="rescue")

def test_leakage_formulas_and_disclosure(tmp_path, monkeypatch, real_counts):
    # 1M 15 pass, 1p5M 15 rescue, 2M 15 fail
    base_results=[True]*15+[False]*15+[False]*15
    rescue_results=[True]*15+[False]*15  # first 15 rescue succeed, next 15 fail (total 30 rescue attempted but only 30? Actually base false =30, so rescue 30)
    # For this layout: 1M 0 rescue, 1p5M 15 rescue, 2M 15 rescue =30 attempted
    # But our base pattern splits per source: 1M first 15 true, 1p5M next 15 false, 2M last 15 false
    # rescue_results accordingly: 15 succeed for 1p5M, 15 fail for 2M
    rescue_results=[True]*15+[False]*15
    result,root,log=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_results,rescue_results,name="leak")
    records=json.loads((root/"v53_records.json").read_text(encoding="utf-8"))
    summary=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    for r in records:
        if r["arm"]=="base_shared": assert r["leak_total"]==v53.leak_for(r["source"])
        else: assert r["leak_total"]==v53.leak_joint_for(r["source"])
    assert summary["leakage"]["per_source"]["1M"]["leak_base"]==1064
    assert summary["leakage"]["per_source"]["1p5M"]["leak_base"]==1094
    assert summary["leakage"]["per_source"]["2M"]["leak_base"]==1104
    assert summary["leakage"]["n_rescue_attempted"]==30
    # per_source avg: 1M 0 rescue =>1064, 1p5M 15 rescue =>1094+40=1134, 2M 15 rescue =>1104+40=1144
    assert summary["leakage"]["avg_leak_per_source"]["1M"]==1064.0
    assert summary["leakage"]["avg_leak_per_source"]["1p5M"]==1134.0
    assert summary["leakage"]["avg_leak_per_source"]["2M"]==1144.0
    # overall_avg = (15*1064 +15*1134+15*1144)/45? Actually total = 15*1064 (1M) +15*1134 (1p5M joint) +15*1144 (2M joint) = (1064+1134+1144)*15/45 =1114
    # but with 30 rescue total, overall = (15*1064+15*1094+15*1104+40*30)/45 = (1064+1094+1104)*15/45 +40*30/45 =1087.33+26.66=1114
    assert summary["leakage"]["avg_overall"]== pytest.approx(1114.0)
    # disclosure_per_final_exact_block
    # final = 15 (1M) +15 rescued (1p5M) =30
    assert summary["counts"]["final_exact_full"]==30
    assert summary["leakage"]["total_disclosed_bits"]== 15*1064 +15*1134+15*1144
    assert summary["leakage"]["disclosure_per_final_exact_block"]== pytest.approx((15*1064+15*1134+15*1144)/30)
    assert summary["leakage"]["avg_disclosure_per_attempted_frame"]== pytest.approx(1114.0/1024)
    # null case: 0 final -> null
    base_all_fail=[False]*45
    rescue_all_fail=[False]*45
    _,root2,_=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_all_fail,rescue_all_fail,name="leak_null")
    s2=json.loads((root2/"v53_summary.json").read_text(encoding="utf-8"))
    assert s2["leakage"]["disclosure_per_final_exact_block"] is None
    assert s2["leakage"]["total_disclosed_bits"]== 15*1104+15*1134+15*1144

def test_gating_boundaries(tmp_path, monkeypatch, real_counts):
    # Pass case: 35 final, per source >=10, undetected 0
    # distribute: 1M 12, 1p5M 11, 2M 12 =35
    base=[True]*35+[False]*10
    rescue=[True]*0+[False]*10  # no rescue succeed, final 35
    # Actually base has 35 true already, no rescue needed for those; final 35 < need 35 pass, per source? 12,11,12 each >=10
    # Use 36 to test pass
    # 12 per source ->36 total, each >=10
    base2=[True]*12+[False]*3 + [True]*12+[False]*3 + [True]*12+[False]*3
    rescue2=[False]*9
    _,root,_=_run_with_pattern(tmp_path,monkeypatch,real_counts,base2,rescue2,name="gate_pass")
    s=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    assert s["counts"]["final_exact_full"]==36
    assert s["terminal_state"]==v53.TERMINAL_V53_HELDOUT_CONFIRM_PASS
    # fail per source <10
    base3=[True]*35+[False]*10
    # need per source fail: make 1M 9/15
    # Our base pattern is source ordered: first 15 1M, next 15 1p5M, last 15 2M
    # So to make 1M less than 10, set first 9 true, 6 false etc
    # Simpler: construct exact per source manually: 1M 9 pass, 1p5M 13 pass, 2M 13 pass =35 total but 1M 9 <10
    base_per_source=[True]*9+[False]*6 + [True]*13+[False]*2 + [True]*13+[False]*2
    assert len(base_per_source)==45
    _,root3,_=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_per_source,[False]*12,name="gate_fail_source")
    s3=json.loads((root3/"v53_summary.json").read_text(encoding="utf-8"))
    assert s3["terminal_state"]==v53.TERMINAL_V53_HELDOUT_CONFIRM_FAIL
    # undetected case
    def _trap_undetected(tmp_path, monkeypatch, real_counts):
        orig=v53._evaluate_one_l2
        def patched(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
            empty=np.empty(0,dtype=np.uint8); target=compute_tag_64(empty,u2_alice); win=v53.BLOCK_WINDOWS[block_seed]
            if spec.get("arm")=="base_shared" and int(block_seed)==394001:
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":0,"errors_final":1,"exact_l2":False,"exact_u1":False,"exact_full":False,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"undetected_accepted_wrong","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
            if spec.get("arm")=="base_shared":
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":0,"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
            return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":0,"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_joint_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"rescue","pass_index":2,"used_increment":True,"joint":True}
        monkeypatch.setattr(v53,"_evaluate_one_l2",patched)
        world=FakeWorld(); root=tmp_path/"undetected"
        result=v53.run_v53_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors)
        monkeypatch.setattr(v53,"_evaluate_one_l2",orig)
        return root
    root_u=_trap_undetected(tmp_path,monkeypatch,real_counts)
    su=json.loads((root_u/"v53_summary.json").read_text(encoding="utf-8"))
    assert su["counts"]["undetected_accepted_wrong"]==1
    assert su["terminal_state"]==v53.TERMINAL_V53_HELDOUT_CONFIRM_FAIL

def test_terminal_and_counts(tmp_path, monkeypatch, real_counts):
    base_results=[True]*30+[False]*15
    rescue_results=[True]*10+[False]*5
    result,root,log=_run_with_pattern(tmp_path,monkeypatch,real_counts,base_results,rescue_results,name="terminal")
    summary=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["base_exact_full"]==30
    assert summary["counts"]["verify_base"]==30
    assert summary["counts"]["rescued_by_increment"]==10
    assert summary["counts"]["final_exact_full"]==40
    assert summary["counts"]["old_exact_full"]==30
    assert summary["counts"]["per_source"]["1M"]["old"]+summary["counts"]["per_source"]["1p5M"]["old"]+summary["counts"]["per_source"]["2M"]["old"]==30
    names={p.name for p in root.iterdir()}
    assert "v53_records.json" in names and "v53_records.csv" in names and "v53_summary.json" in names
    assert not list(root.glob("*.npz"))
    records=json.loads((root/"v53_records.json").read_text(encoding="utf-8"))
    with (root/"v53_records.csv").open(newline="",encoding="utf-8") as h:
        rows=list(csv.DictReader(h))
    assert len(rows)==len(records)
    for r in records:
        ok,msg=v53.validate_record_schema(r)
        assert ok,msg
        assert r["tag_scope"]=="l2_only"
        assert r["sampling_mode"]==v53.SAMPLING_MODE
        assert r["pairs_count"]==1024

def test_cli_guards():
    proc=subprocess.run([sys.executable,str(SCRIPT_PATH)],capture_output=True,text=True)
    assert proc.returncode!=0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout+proc.stderr)
    proc2=subprocess.run([sys.executable,str(SCRIPT_PATH),"--execution-authorized","--authorized-target-sha","0"*40],capture_output=True,text=True)
    assert proc2.returncode!=0
    script_text=SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script_text

def test_output_root_not_exists_real():
    assert not OUTPUT_ROOT_REAL.exists(), f"formal output root should not exist: {OUTPUT_ROOT_REAL}"

def test_no_old_duplicate_decode():
    src=Path(v53.__file__).read_text(encoding="utf-8")
    assert "old_exact = base_exact" in src or "old_exact = exact_base" in src or "old_exact" in src
    assert "base 1(兼 old" in src or "兼 old" in src

def test_l1_fortyfive_true_bp_calls(tmp_path, monkeypatch, real_counts):
    import comparison_bench.formal_ir.v35_algorithm_development as v35
    def _fake_load(block_seed: int):
        rng=np.random.default_rng(int(block_seed) ^ 0x9E3779B9)
        alice=rng.integers(0,1024,size=1024,dtype=np.int64); bob=rng.integers(0,1024,size=1024,dtype=np.int64)
        return alice,bob
    monkeypatch.setattr(v53,"load_heldout_block",_fake_load)
    l1_calls: list[dict]=[]
    class _MockL1:
        def __init__(self, final_beliefs): self.final_beliefs=final_beliefs; self.iterations=5; self.syndrome_ok=True; self.status="converged_exact"; self.runtime_s=0.001; self.x_hat=np.zeros(1024,dtype=np.uint8)
    orig_dec=v35.decode_row_layered_fftqspa
    def _mock_dec(matrix, prior, syn, max_iter=90, damping_alpha=1.0, field=None):
        l1_calls.append({"shape":tuple(matrix.shape),"prior_shape":tuple(prior.shape)})
        fb=np.log(np.maximum(prior,1e-15))+0.01*np.random.default_rng(0).standard_normal(prior.shape)
        return _MockL1(fb)
    monkeypatch.setattr(v35,"decode_row_layered_fftqspa",_mock_dec)
    orig_eval=v53._evaluate_one_l2
    def _fake_eval(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        empty=np.empty(0,dtype=np.uint8); target=compute_tag_64(empty,u2_alice); win=v53.BLOCK_WINDOWS[block_seed]
        return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":spec.get("arm","base_shared"),"pass_index":int(spec.get("pass_index",1)),"used_increment":bool(spec.get("used_increment",False)),"joint":bool(spec.get("joint",False))}
    monkeypatch.setattr(v53,"_evaluate_one_l2",_fake_eval)
    world=FakeWorld(); root=tmp_path/"l1count"
    result=v53.run_v53_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=False, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    monkeypatch.setattr(v35,"decode_row_layered_fftqspa",orig_dec); monkeypatch.setattr(v53,"_evaluate_one_l2",orig_eval)
    assert len(l1_calls)==45, f"H1 BP true calls should be 45, got {len(l1_calls)}"
    assert all(c["shape"]==(16,1024) for c in l1_calls)
    summary=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_completed"]["l1"]==45
    assert summary["accounting"]["decoder_calls_completed"]["total"]==90

def test_q_reused_between_base_and_rescue(tmp_path, monkeypatch, real_counts):
    captured: dict[int, dict[str, np.ndarray]]={}
    orig=v53._evaluate_one_l2
    def _capture(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        arm=spec.get("arm"); entry=captured.setdefault(int(block_seed),{})
        if q is not None: entry[arm]={"q_id":id(q),"q":np.array(q,copy=True),"p_prior_id":id(p_prior) if p_prior is not None else None}
        empty=np.empty(0,dtype=np.uint8); target=compute_tag_64(empty,u2_alice); alt=compute_tag_64(empty,(u2_alice+1)%32); win=v53.BLOCK_WINDOWS[block_seed]
        if arm=="base_shared" and int(block_seed)==394001:
            return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":10,"exact_l2":False,"exact_u1":True,"exact_full":False,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":alt,"tag_ok":False,"tag_scope":v53.TAG_SCOPE,"reclassified":"detected_verification_failure","iterations_l1":5,"iterations_l2":90,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"max_iter","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
        else:
            is_rescue=arm=="rescue"
            return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_joint_for(source) if is_rescue else v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":arm,"pass_index":2 if is_rescue else 1,"used_increment":bool(is_rescue),"joint":bool(is_rescue)}
    monkeypatch.setattr(v53,"_evaluate_one_l2",_capture)
    world=FakeWorld(); root=tmp_path/"qreuse"
    result=v53.run_v53_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    monkeypatch.setattr(v53,"_evaluate_one_l2",orig)
    assert 394001 in captured and "base_shared" in captured[394001] and "rescue" in captured[394001]
    base_q=captured[394001]["base_shared"]["q"]; rescue_q=captured[394001]["rescue"]["q"]
    base_id=captured[394001]["base_shared"]["q_id"]; rescue_id=captured[394001]["rescue"]["q_id"]
    assert (base_id==rescue_id) or np.array_equal(base_q,rescue_q), "rescue should reuse same q"
    assert base_q.shape==(1024,32); assert np.allclose(base_q,rescue_q)
    summary=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["n_rescue_attempted"]==1
    assert captured[394001]["base_shared"]["p_prior_id"]==captured[394001]["rescue"]["p_prior_id"]

def test_verify_true_exact_false_no_rescue(tmp_path, monkeypatch, real_counts):
    orig=v53._evaluate_one_l2; rescue_calls: list[int]=[]; base_calls: list[int]=[]
    def _trap(matrix, source, block_seed, counts, bob, u2_alice, u2_bob, field, setting, fake_runner, decode_fn, errors_initial, spec, q=None, p_prior=None, **kw):
        arm=spec.get("arm"); empty=np.empty(0,dtype=np.uint8); target=compute_tag_64(empty,u2_alice); win=v53.BLOCK_WINDOWS[block_seed]
        if arm=="base_shared":
            base_calls.append(int(block_seed))
            if int(block_seed)==394002:
                return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":10,"exact_l2":False,"exact_u1":False,"exact_full":False,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"undetected_accepted_wrong","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
            return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"base_shared","pass_index":1,"used_increment":False,"joint":False}
        else:
            rescue_calls.append(int(block_seed))
            return {"source":source,"block_seed":block_seed,"matrix_id":spec["matrix_id"],"h1_matrix_id":v53.H1_MATRIX_ID,"frame_ids":list(win["frame_ids"]),"held_out_ordinal_start":int(win["held_out_ordinal_start"]),"held_out_ordinal_end":int(win["held_out_ordinal_end"]),"pairs_count":1024,"sampling_mode":v53.SAMPLING_MODE,"errors_initial":int(errors_initial),"errors_final":0,"exact_l2":True,"exact_u1":True,"exact_full":True,"syndrome_ok_l2":True,"syndrome_ok_l1":True,"target_tag":target,"candidate_tag":target,"tag_ok":True,"tag_scope":v53.TAG_SCOPE,"reclassified":"exact","iterations_l1":5,"iterations_l2":5,"bp_posterior_entropy":4.2,"mean_abs_diff_q_p":0.03,"leak_total":v53.leak_joint_for(source),"leak_joint":v53.leak_joint_for(source),"status":"converged_exact","runtime_s":0.001,"arm":"rescue","pass_index":2,"used_increment":True,"joint":True}
    monkeypatch.setattr(v53,"_evaluate_one_l2",_trap)
    world=FakeWorld(); root=tmp_path/"verify_no_rescue"
    result=v53.run_v53_diagnostic(execution_authorized=True, authorized_target_sha="f"*40, fake_runner=True, output_root=root, structural_authority_path=world.authority_file(tmp_path), counts_by_source=real_counts, check_git=False, check_scoped_dirty=False, constructors=world.constructors, decode_fn=None)
    monkeypatch.setattr(v53,"_evaluate_one_l2",orig)
    assert 394002 not in rescue_calls, f"verify true should not rescue, got {rescue_calls}"
    assert len(rescue_calls)==0
    assert len(base_calls)==45
    summary=json.loads((root/"v53_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage"]["n_rescue_attempted"]==0
    assert summary["accounting"]["decoder_calls_completed"]["rescue"]==0
    records=json.loads((root/"v53_records.json").read_text(encoding="utf-8"))
    rec=next(r for r in records if r["block_seed"]==394002)
    assert rec["reclassified"]=="undetected_accepted_wrong"
    assert rec["syndrome_ok_l2"] is True and rec["tag_ok"] is True
    assert rec["exact_l2"] is False
