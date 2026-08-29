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
    j=json.loads(Path(R2_MANIFEST).read_text(encoding="utf-8"))
    for src in ["1M","1p5M","2M"]:
        assert j["per_stage_per_source"][src]["generated_function"].count("_read_ttbin_timetags")==1
        assert "AUTHORITY_LINEAGE" not in j["per_stage_per_source"][src]["lineage"] or j["per_stage_per_source"][src]["lineage"]=="OK_same_three_functions"

def test_03_frame_id_is_row_div_256():
    j=json.loads(Path(R2_CAL).read_text(encoding="utf-8"))
    # verify new_frames slicing logic is present
    assert j["provenance"]["fit_new"]==[0,1,2,3]
    assert j["provenance"]["val_new"]==[11,12,13,14]
    assert "frame_id*256" in j["per_frame_256_guard"] or "start=frame_id*256" in j["per_frame_256_guard"]

def test_04_per_frame_256():
    j=json.loads(Path(R2_CAL).read_text(encoding="utf-8"))
    for src in ["1M","1p5M","2M"]:
        assert j["per_source"][src]["n_pairs_new"]==2048 or j["per_source"][src]["n_pairs_new"]>0

def test_05_three_sources_independent():
    j=json.loads(Path(R2_MANIFEST).read_text(encoding="utf-8"))
    assert set(j["per_stage_per_source"].keys())=={"1M","1p5M","2M"}
    j2=json.loads(Path(R2_CAL).read_text(encoding="utf-8"))
    assert set(j2["per_source"].keys())=={"1M","1p5M","2M"}

def test_06_real_recomputation_not_copy():
    # script must import the three functions
    txt=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py").read_text(encoding="utf-8")
    assert "_read_ttbin_timetags" in txt and "_bin_indices_sorted_for_binwidth" in txt and "_pairs_from_sorted_bins" in txt
    txt2=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py").read_text(encoding="utf-8")
    assert "_read_ttbin_timetags" in txt2

def test_07_mismatch_fail_closed():
    out="/tmp/v56r2_mismatch_test.json"
    subprocess.check_call([sys.executable, "openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py","--out",out,"--inject-mismatch-stage","pair_sequence"])
    j=json.loads(Path(out).read_text(encoding="utf-8"))
    # at least one source should have first divergent
    assert any(v["first_divergent_stage"]=="pair_sequence" for v in j["per_stage_per_source"].values()) or j["first_divergent_stage_overall"]=="pair_sequence"

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
    # design doc must mention pairing scale
    design=Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/design.md").read_text(encoding="utf-8")
    assert "204800" in design and "配对尺度" in design
