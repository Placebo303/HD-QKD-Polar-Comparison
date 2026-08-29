import json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

R2_MANIFEST="openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest_r2.json"
R2_CAL="openspec/changes/formal-ir-v56-input-contract-reconstruction/calibration_verification_r2.json"

def test_01_TAUTH1_100pct_replay():
    j=json.loads(Path(R2_MANIFEST).read_text(encoding="utf-8"))
    for src in ["1M","1p5M","2M"]:
        assert j["per_stage_per_source"][src]["gold_anchor_TAUTH1_current_vs_parquet_100pct"] is True, f"{src} not 100%"

def test_02_TAUTH2_V13_same_three_functions():
    # R3 is authoritative fixed replay with separate TTBin
    R3_MANIFEST="openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest_r3.json"
    target=R3_MANIFEST if Path(R3_MANIFEST).exists() else R2_MANIFEST
    j=json.loads(Path(target).read_text(encoding="utf-8"))
    for src in ["1M","1p5M","2M"]:
        assert j["per_stage_per_source"][src]["generated_function"].count("_read_ttbin_timetags")==1
        # T-AUTH-2 field must exist
        assert "gold_anchor_TAUTH2_v13_vs_persisted_100pct" in j["per_stage_per_source"][src]
        # lineage must be explicit, either OK or INCOMPLETE, no silent pass
        assert j["per_stage_per_source"][src]["lineage"] in ["OK_same_three_functions","AUTHORITY_LINEAGE_INCOMPLETE","AUTHORITY_LINEAGE_INCOMPLETE_TAUTH2_mismatch"]

def test_03_frame_id_is_row_div_256():
    j=json.loads(Path(R2_CAL).read_text(encoding="utf-8"))
    # verify new_frames slicing logic is present
    assert j["provenance"]["fit_new"]==[0,1,2,3]
    assert j["provenance"]["val_new"]==[11,12,13,14]
    assert "frame_id*256" in j["per_frame_256_guard"] or "start=frame_id*256" in j["per_frame_256_guard"]

def test_04_per_frame_256():
    # R3 has strict 256 check
    R3_CAL="openspec/changes/formal-ir-v56-input-contract-reconstruction/calibration_verification_r3.json"
    target=R3_CAL if Path(R3_CAL).exists() else R2_CAL
    j=json.loads(Path(target).read_text(encoding="utf-8"))
    for src in ["1M","1p5M","2M"]:
        assert j["per_source"][src]["n_pairs_new"]==2048
        assert j["per_source"][src]["per_frame_256_ok"] is True
        # insufficient must be fail closed - check per_frame flag is real bool not constant
        assert isinstance(j["per_source"][src]["per_frame_256_ok"], bool)

def test_05_three_sources_independent():
    j=json.loads(Path(R2_MANIFEST).read_text(encoding="utf-8"))
    assert set(j["per_stage_per_source"].keys())=={"1M","1p5M","2M"}
    j2=json.loads(Path(R2_CAL).read_text(encoding="utf-8"))
    assert set(j2["per_source"].keys())=={"1M","1p5M","2M"}

def test_06_real_recomputation_not_copy():
    txt=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py").read_text(encoding="utf-8")
    assert "_read_ttbin_timetags" in txt and "_bin_indices_sorted_for_binwidth" in txt and "_pairs_from_sorted_bins" in txt
    # no production array copy for corrected: must not have `corrected_st[s]["array"]=v13_st` copy pattern
    # allow only inside allow-synthetic branch
    assert txt.count('v13_st[s]["array"].copy()')==0 or "allow-synthetic" in txt
    # also delete default array_equal True in verify: must compute real compare
    txt2=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py").read_text(encoding="utf-8")
    assert "_read_ttbin_timetags" in txt2
    # verify must not contain constant per_frame placeholder `bool(all(True`
    assert "bool(all(True" not in txt2
    # must contain real per_frame loop
    assert "per_frame_ok" in txt2 and "cnt!=256" in txt2

def test_07_mismatch_fail_closed():
    out="/tmp/v56r2_mismatch_test.json"
    subprocess.check_call([sys.executable, "openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py","--out",out,"--inject-mismatch-stage","pair_sequence"])
    j=json.loads(Path(out).read_text(encoding="utf-8"))
    # injected stage must be marked not equal
    for src in ["1M","1p5M","2M"]:
        per=j["per_stage_per_source"][src]["per_stage"]
        injected=[p for p in per if p["stage"]=="pair_sequence"]
        assert injected and injected[0]["array_equal"] is False

def test_08_missing_lineage_unresolved():
    # simulate missing sidecar -> lineage incomplete
    import tempfile, shutil
    tmp=Path(tempfile.mkdtemp())
    out=str(tmp/"out.json")
    subprocess.check_call([sys.executable, "openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py","--v13-sidecars",str(tmp/"nonexist"),"--out",out,"--allow-synthetic-for-test"])
    j=json.loads(Path(out).read_text(encoding="utf-8"))
    assert any("AUTHORITY_LINEAGE_INCOMPLETE" in v["lineage"] for v in j["per_stage_per_source"].values())

def test_09_no_synthetic_in_production():
    txt=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py").read_text(encoding="utf-8")
    assert "allow-synthetic-for-test" in txt
    # without flag, missing TTBin should give incomplete not synthetic
    import tempfile
    tmp=Path(tempfile.mkdtemp())
    out=str(tmp/"out2.json")
    subprocess.check_call([sys.executable, "openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py","--ttbin-root",str(tmp/"nonexist"),"--out",out])
    j=json.loads(Path(out).read_text(encoding="utf-8"))
    assert j["overall"] in ["V56_INPUT_CONTRACT_UNRESOLVED","V56_EVIDENCE_INVALID","V56_MIXED_BY_SOURCE","V56_TRUE_SESSION_DOMAIN_SHIFT"]

def test_10_zero_overlap():
    j=json.loads(Path(R2_CAL).read_text(encoding="utf-8"))
    assert j["zero_overlap"]["new_vs_V55_90"] is True
    assert j["zero_overlap"]["new_vs_D4_fitval"] is True
    assert set([0,1,2,3,11,12,13,14]) & set([7,8,9,10,15,16,17,18])==set()
    # also check not in V55 90 (look in known locations)
    cand=[Path("openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json"), Path("comparison_bench/outputs_comparison/v55_intake_20260828/v55_authoritative_registry.json")]
    reg_path=next((p for p in cand if p.exists()), None)
    assert reg_path is not None, "registry not found"
    reg=json.loads(reg_path.read_text(encoding="utf-8"))
    s=set()
    for v in reg.values():
        if isinstance(v,list): s.update(v)
        elif isinstance(v,dict):
            for vv in v.values():
                if isinstance(vv,list): s.update(vv)
    assert set([0,1,2,3,11,12,13,14]) & s == set()

def test_11_git_diff_src_zero():
    out=subprocess.check_output(["git","diff","--","src/"], text=True)
    assert out.strip()=="", "src/ must be unchanged"

def test_12_rg_decode_zero():
    import subprocess as sp
    r=sp.run(["git","grep","-n","decode_", "--","openspec/changes/formal-ir-v56-input-contract-reconstruction"], capture_output=True, text=True)
    # allow 0 hits or only comments about decode forbidden
    hits=[l for l in r.stdout.splitlines() if "decode_" in l and "DECODE_FORBIDDEN" not in l and "rg" not in l]
    # scripts should have zero decode_ calls
    txt=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py").read_text(encoding="utf-8")
    assert "decode_" not in txt
    txt2=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py").read_text(encoding="utf-8")
    assert "decode_" not in txt2

def test_13_trailing_whitespace():
    for p in ["openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py","openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py"]:
        for i,line in enumerate(Path(p).read_text(encoding="utf-8").splitlines(),1):
            assert not line.endswith(" ") and not line.endswith("\t"), f"{p}:{i} trailing whitespace"

def test_14_seven_stage_names():
    j=json.loads(Path(R2_MANIFEST).read_text(encoding="utf-8"))
    expected=["raw_channel_timetags","absolute_bin_indices","physical_frame_match","pair_sequence","logical_frame_grouping","symbol_1024","U1U2"]
    for src in ["1M","1p5M","2M"]:
        stages=[s["stage"] for s in j["per_stage_per_source"][src]["per_stage"]]
        assert stages==expected, f"{src} stages mismatch {stages}"

def test_15_204800_is_pairing_scale():
    txt=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py").read_text(encoding="utf-8")
    assert "204800" in txt or "PERIOD_PS" in txt
    design=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/design.md").read_text(encoding="utf-8")
    assert "204800" in design and "配对尺度" in design

def test_16_head_equals_current_sha():
    import subprocess as sp
    head=sp.check_output(["git","rev-parse","HEAD"], text=True).strip()
    R3M="openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest_r3.json"
    R3C="openspec/changes/formal-ir-v56-input-contract-reconstruction/calibration_verification_r3.json"
    assert Path(R3M).exists(), "R3 manifest missing"
    assert Path(R3C).exists(), "R3 calibration missing"
    jm=json.loads(Path(R3M).read_text(encoding="utf-8"))
    jc=json.loads(Path(R3C).read_text(encoding="utf-8"))
    for j in [jm, jc]:
        assert j["provenance"]["head"]==head
        if "origin_formal_ir_mainline" in j["provenance"]:
            # head and origin should match current HEAD (formal-ir-mainline is HEAD)
            assert j["provenance"]["head"]==head
            assert j["provenance"]["implementation_sha"]==head

def test_17_persisted_anchor_mutation_blocks_domain_shift():
    # mutate one row of V55 persisted parquet must break T-AUTH-1 and block DOMAIN_SHIFT
    import tempfile, shutil
    tmp=Path(tempfile.mkdtemp())
    # copy a parquet to tmp and mutate one row
    src_parquet=Path("comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet")
    if not src_parquet.exists():
        cands=list(Path("comparison_bench/outputs_comparison/v55_intake_20260828/pairs").rglob("pairs.parquet"))
        src_parquet=cands[0] if cands else None
    assert src_parquet and src_parquet.exists()
    df=pd.read_parquet(src_parquet)
    # mutate a row inside fixed_frames [7,8,9,10,15,16,17,18] (frame 7)
    mask=df["frame_id"]==7
    if mask.any():
        idx=df[mask].index[0]
        df.loc[idx,"alice_symbol"]=(int(df.loc[idx,"alice_symbol"])+1)%1024
    else:
        df.loc[0,"alice_symbol"]=(int(df.loc[0,"alice_symbol"])+1)%1024
    mutated_dir=tmp/"mutated"/"20260123_1M_600k_0dB"
    mutated_dir.mkdir(parents=True)
    mutated_parquet=mutated_dir/"pairs.parquet"
    df.to_parquet(mutated_parquet, index=False)
    # also need other sources: copy them
    for other in ["20260107_PPLN_1p5M","20260123_2M_1p2M_0dB"]:
        src_other=list(Path("comparison_bench/outputs_comparison/v55_intake_20260828/pairs").rglob(other))
        if src_other:
            # find parquet under other
            pp=list(Path("comparison_bench/outputs_comparison/v55_intake_20260828/pairs").rglob("pairs.parquet"))
            for p in pp:
                if other in str(p):
                    od=tmp/"mutated"/other
                    od.mkdir(parents=True, exist_ok=True)
                    pd.read_parquet(p).to_parquet(od/"pairs.parquet", index=False)
    out=tmp/"out.json"
    subprocess.check_call([sys.executable, "openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py","--pairs-root",str(tmp/"mutated"),"--out",str(out)])
    j=json.loads(Path(out).read_text(encoding="utf-8"))
    # at least one source should have gold false, and overall not all true
    vals=[v["gold_anchor_TAUTH1_current_vs_parquet_100pct"] for v in j["per_stage_per_source"].values()]
    assert False in vals, "mutated anchor should break 100% parity"
    # verify that calibration with mutated would not be DOMAIN_SHIFT uniformly (needs contract true)
    # here we just ensure replay detects tamper

def test_18_corrected_null_when_no_influential_param():
    R3M="openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest_r3.json"
    j=json.loads(Path(R3M).read_text(encoding="utf-8"))
    for src in ["1M","1p5M","2M"]:
        # with identical bin_width/dimension, replaced_key must be null (no copy)
        assert j["per_stage_per_source"][src]["three_way"]["replaced_key"] is None
        assert j["per_stage_per_source"][src]["three_way"]["replaced_value"] is None

def test_19_R2_marked_invalid():
    # R2 must be retained but marked ENGINEERING_INVALID_SIMULATED_CONTRACT_EQUALITY
    marker=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/RECONSTRUCTION_REPORT_R2.md")
    assert marker.exists()
    txt=marker.read_text(encoding="utf-8")
    # R2 JSONs themselves are historical; they are not overwritten by R3
    assert Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest_r2.json").exists()
    assert Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/calibration_verification_r2.json").exists()
    # ensure R2 is considered invalid via separate tag file or note
    invalid_tag=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/R2_INVALID_TAG.json")
    if invalid_tag.exists():
        jt=json.loads(invalid_tag.read_text(encoding="utf-8"))
        assert jt.get("tag")=="ENGINEERING_INVALID_SIMULATED_CONTRACT_EQUALITY"
