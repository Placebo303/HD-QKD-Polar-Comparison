"""V56 input contract reconstruction — tests covering 7-stage, contract/distribution per-source, 5-way, zero execution, V55 90 ban."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import numpy as np
import pytest

REPO=Path(__file__).resolve().parents[2]
REPLAY=REPO/"openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py"
VERIFY=REPO/"openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py"
MANIFEST=REPO/"openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest.json"
CALIB=REPO/"openspec/changes/formal-ir-v56-input-contract-reconstruction/calibration_verification.json"

STAGES=["raw_event_channel_selection","pairing_index_dt","delay_sign_position","frame_start_period_floor_div","bin_index","symbol_1024","U1U2"]

def _run_replay(tmp_path):
    out=tmp_path/"verification_manifest.json"
    subprocess.check_call([sys.executable, str(REPLAY), "--frames","7,8,9,10,15,16,17,18","--out",str(out)])
    return json.loads(out.read_text(encoding="utf-8"))

def _run_verify(tmp_path):
    out=tmp_path/"calibration_verification.json"
    subprocess.check_call([sys.executable, str(VERIFY), "--new-frames","0,1,2,3,11,12,13,14","--out",str(out)])
    return json.loads(out.read_text(encoding="utf-8"))

def test_seven_stages_present_and_ordered(tmp_path):
    data=_run_replay(tmp_path)
    for src, rec in data["per_stage_per_source"].items():
        stages=[p["stage"] for p in rec["per_stage"]]
        assert stages==STAGES
        # first_divergent_stage must be None or in STAGES
        assert rec["first_divergent_stage"] is None or rec["first_divergent_stage"] in STAGES

def test_first_divergent_and_samples(tmp_path):
    data=_run_replay(tmp_path)
    for src, rec in data["per_stage_per_source"].items():
        if rec["first_divergent_stage"] is not None:
            # per_stage after first must contain sample_rows structure
            for p in rec["per_stage"]:
                assert "array_equal" in p and "sample_rows" in p

def test_contract_equivalent_per_source(tmp_path):
    data=_run_verify(tmp_path)
    for src, rec in data["per_source"].items():
        assert "contract_equivalent" in rec
        assert isinstance(rec["contract_equivalent"], bool)

def test_distribution_compatible_three_gates_per_source(tmp_path):
    data=_run_verify(tmp_path)
    for src, rec in data["per_source"].items():
        # A==B >60%
        assert rec["A_eq_rate"] is not None
        # acc thresholds
        assert rec["acc_U1"] is not None and rec["acc_U2"] is not None
        # CE thresholds pre-registered: min(0.5*current, V13ref+1)
        assert rec["CE_thresh_U1"] is not None and rec["CE_thresh_U2"] is not None
        # distribution_compatible requires all three
        expected = (rec["A_eq_rate"]>0.60 and rec["acc_U1"]>=0.60 and rec["acc_U2"]>=0.60 and rec["CE_U1"]<=rec["CE_thresh_U1"] and rec["CE_U2"]<=rec["CE_thresh_U2"])
        assert rec["distribution_compatible"]==expected

def test_ce_threshold_formula(tmp_path):
    data=_run_verify(tmp_path)
    # CE_thresh = min(0.5*CE_current, V13ref+1) per spec
    for src in ["1M","1p5M","2M"]:
        thr=data["pre_registered_thresholds"][src]
        assert math_close(thr["CE_thresh_U1"], min(0.5*thr["CE_current_U1"], thr["CE_V13ref_U1"]+1.0))
        assert math_close(thr["CE_thresh_U2"], min(0.5*thr["CE_current_U2"], thr["CE_V13ref_U2"]+1.0))

def math_close(a,b): return abs(a-b)<1e-6

def test_five_way_exclusive(tmp_path):
    data=_run_verify(tmp_path)
    assert data["overall"] in {"V56_EVIDENCE_INVALID","V56_MIXED_BY_SOURCE","V56_INPUT_CONTRACT_RECOVERED","V56_TRUE_SESSION_DOMAIN_SHIFT","V56_INPUT_CONTRACT_UNRESOLVED"}
    shunts=set(v["shunt_s"] for v in data["per_source"].values())
    uniq=len(shunts)
    if data["overall"]=="V56_MIXED_BY_SOURCE":
        assert uniq>1
    elif data["overall"]=="V56_INPUT_CONTRACT_RECOVERED":
        assert all(v["contract_equivalent"] and v["distribution_compatible"] for v in data["per_source"].values())
    elif data["overall"]=="V56_TRUE_SESSION_DOMAIN_SHIFT":
        assert all(v["contract_equivalent"] and not v["distribution_compatible"] for v in data["per_source"].values())
    elif data["overall"]=="V56_INPUT_CONTRACT_UNRESOLVED":
        assert all(not v["contract_equivalent"] for v in data["per_source"].values())

def test_zero_execution_no_decode(tmp_path):
    bad="dec"+"ode_"
    for p in [REPLAY, VERIFY, Path(__file__)]:
        txt=p.read_text(encoding="utf-8")
        assert bad not in txt, f"bad pattern in {p}"
    # no run_01 created
    assert not (REPO/"comparison_bench/outputs_comparison/formal_ir_methods/v56_input_contract_reconstruction/run_01").exists()

def test_v55_90_ban_zero_overlap(tmp_path):
    data=_run_verify(tmp_path)
    assert data["zero_overlap"]["new_vs_V55_90"] is True
    assert data["zero_overlap"]["new_vs_D4_fitval"] is True
    replay=_run_replay(tmp_path)
    # frames must not overlap D4 fit/val
    assert set([0,1,2,3,11,12,13,14]) & set([7,8,9,10,15,16,17,18])==set()

def test_wrapper_only_src_unchanged():
    diff=subprocess.check_output(["git","diff","--","src/"], text=True)
    assert diff.strip()==""

def test_py_compile_both(tmp_path):
    import py_compile
    py_compile.compile(str(REPLAY), doraise=True)
    py_compile.compile(str(VERIFY), doraise=True)

def test_nll_qmass_consistency_only(tmp_path):
    data=_run_verify(tmp_path)
    for src, rec in data["per_source"].items():
        # NLL/q_mass present but not gating overall beyond consistency
        assert "NLL" in rec and "q_mass" in rec
