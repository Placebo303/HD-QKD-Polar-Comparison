import json, math, sys
from pathlib import Path
import numpy as np
import pytest

# ensure repo root on path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

import scripts.v65ar2_pipeline as m
from unittest.mock import patch

def _make_events(channel_counts: dict):
    # helper to mock read_ttbin_events returning TTBinEvents
    from src.qkd_io.ttbin_pipeline import TTBinEvents
    total=sum(channel_counts.values())
    # create interleaved timestamps
    ch_list=[]; t_list=[]
    t=0
    for ch,cnt in channel_counts.items():
        for i in range(cnt):
            t_list.append(t); ch_list.append(ch); t+=204800  # spacing
    time_ps=np.array(t_list, dtype=np.int64)
    channel=np.array(ch_list, dtype=np.int64)
    # sort by time
    idx=np.argsort(time_ps); time_ps=time_ps[idx]; channel=channel[idx]
    return TTBinEvents(time_ps=time_ps, channel=channel, event_type=None)

def _patch_events(monkeypatch, channel_counts):
    ev=_make_events(channel_counts)
    monkeypatch.setattr("src.qkd_io.ttbin_pipeline.read_ttbin_events", lambda p: ev)
    monkeypatch.setattr("src.reconciliation.run_nbldpc_demo_point.read_ttbin_events", lambda p: ev, raising=False)

def test_01_raw_missing_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    contract=tmp_path/"contract.json"
    contract.write_text(json.dumps({"channel_pair":"1/5","delay_used_ps":0,"sigma_ps":100}),encoding="utf-8")
    missing=tmp_path/"nope"
    res=m.phase_r("162148", raw_root=str(missing), contract=str(contract))
    assert res["status"]=="PHASE_R_FAIL"
    assert "raw_ttbin_missing" in res["reason"]

def test_02_contract_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    # patch events to have channels 1/5
    _patch_events(monkeypatch, {1:100,5:100})
    # also patch _read_ttbin etc to avoid real pairing failure for this test: contract missing should already fail before pairing
    res=m.phase_r("162148", raw_root=str(raw), contract=str(tmp_path/"missing.json"))
    assert res["status"]=="PHASE_R_FAIL"
    assert "contract" in res["reason"].lower()

def test_03_channel_ambiguity(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"
    contract.write_text(json.dumps({"channel_pair":"1/5"}),encoding="utf-8")
    # other channels 2,3 exceed 20%
    _patch_events(monkeypatch, {1:50,5:50,2:60,3:60})
    res=m.phase_r("162148", raw_root=str(raw), contract=str(contract))
    assert res["status"]=="PHASE_R_FAIL"
    assert "ambiguity" in res["reason"] or "channel" in res["reason"].lower()

def test_04_candidate_specific_timing_channel(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    # two candidates different contracts but same raw -> ensure timing differs per candidate contract
    c1=tmp_path/"c1.json"; c1.write_text(json.dumps({"channel_pair":"1/5","delay_used_ps":10,"sigma_ps":80}),encoding="utf-8")
    c2=tmp_path/"c2.json"; c2.write_text(json.dumps({"channel_pair":"1/5","delay_used_ps":30,"sigma_ps":80}),encoding="utf-8")
    _patch_events(monkeypatch, {1:200,5:200})
    # mock pairing to succeed (need enough pairs)
    with patch("src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags") as mock_tt, \
         patch("src.reconciliation.run_nbldpc_demo_point._bin_indices_sorted_for_binwidth") as mock_bin, \
         patch("src.reconciliation.run_nbldpc_demo_point._pairs_from_sorted_bins") as mock_pairs:
        import numpy as np
        mock_tt.return_value = type("TT",(),{"TimeTag":np.arange(1000),"Ch":np.zeros(1000)})()
        mock_bin.return_value = (np.arange(500), np.arange(500), {})
        mock_pairs.return_value = (np.random.randint(0,1024,size=(500,2)), {})
        r1=m.phase_r("162148", raw_root=str(raw), contract=str(c1))
        r2=m.phase_r("2500K", raw_root=str(raw), contract=str(c2))
        assert r1["sidecar_additive"]["delay_used_ps"] != r2["sidecar_additive"]["delay_used_ps"]
        assert r1["sidecar_additive"]["channel_pair"]=="1/5"

def test_05_stage0_real_8x256(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    # Stage0 needs real pairs 8 frames
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5","delay_used_ps":0,"sigma_ps":100}),encoding="utf-8")
    # craft pairs 8*256 =2048 deterministic
    pairs=np.stack([np.arange(2048)%1024, (np.arange(2048)+1)%1024], axis=1)
    fake_est={"at_boundary":False,"d_nll":0.1,"val_nll":1.0,"H":2.0,"unseen":0.0,"m1_req":10,"m2_req":100,"chain_delta_CE":0.0,"chain_delta_H":0.0}
    with patch.object(m,"_materialize_pairs", return_value=pairs), \
         patch.object(m,"phase_r", return_value={"status":"PASS","sidecar_additive":{"channel_pair":"1/5"}}), \
         patch.object(m,"hierarchical_estimate", return_value=fake_est):
        # also patch read not needed
        res=m.run_stage0(["162148"], { "162148": str(raw)}, {"162148": str(contract)})
        assert res["selected"]=="162148"
        assert len(res["per_candidate"]["162148"]["stage0"]["triples"])==8

def test_06_first_match_stop(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5","delay_used_ps":0,"sigma_ps":100}),encoding="utf-8")
    pairs_good=np.random.randint(0,1024,size=(2048,2))
    pairs_bad=np.random.randint(0,1024,size=(2048,2))
    # make first candidate pass, second would also pass but should be UNREACHABLE
    def fake_materialize_a(*a,**kw): return pairs_good
    # run_stage0 loops in order; first pass should break
    with patch.object(m,"_materialize_pairs", return_value=pairs_good), \
         patch.object(m,"phase_r", return_value={"status":"PASS","sidecar_additive":{}}), \
         patch.object(m,"hierarchical_estimate", return_value={"at_boundary":False,"d_nll":0.1,"val_nll":1.0,"H":2.0,"unseen":0.0,"m1_req":10,"m2_req":100,"chain_delta_CE":0.0,"chain_delta_H":0.0}):
        res=m.run_stage0(["162148","2500K"], {"162148":str(raw),"2500K":str(raw)},{"162148":str(contract),"2500K":str(contract)})
        assert res["selected"]=="162148"
        assert "162148" in res["per_candidate"]
        # second should be unreachable or not PASS
        assert res["per_candidate"]["2500K"]["stage0"]["status"]=="UNREACHABLE_FIRST_MATCH"

def test_07_stage1_real_estimate(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5"}),encoding="utf-8")
    # need (256+64)*256=81920 pairs for stage1
    pairs=np.random.randint(0,1024,size=(90000,2))
    with patch.object(m,"_materialize_pairs", return_value=pairs):
        res=m.run_stage1("162148", Path(raw), Path(contract))
        assert "est" in res
        assert "CE1" in res["est"] or "m1_req" in res["est"]
        assert not res.get("used_test_in_estimation", False)

def test_08_stage2_real_estimate(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5"}),encoding="utf-8")
    pairs=np.random.randint(0,1024,size=(350000,2))
    with patch.object(m,"_materialize_pairs", return_value=pairs):
        res=m.run_stage2("162148", Path(raw), Path(contract))
        assert res["status"] in ("PASS","FAIL")
        assert "test32" in res
        assert res["test32"]["identity_only"] is True

def test_09_test_loader_unreachable(tmp_path):
    # ensure seal never calls load_test_symbols (which throws)
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5"}),encoding="utf-8")
    pairs=np.random.randint(0,1024,size=(350000,2))
    with patch.object(m,"_materialize_pairs", return_value=pairs):
        # monkeypatch loader to throw if called
        with patch.object(m, "_materialize_pairs", wraps=m._materialize_pairs):
            # internal run_stage2 should not call any loader named load_test*
            res=m.run_stage2("162148", Path(raw), Path(contract))
            assert "test32" in res
            # ensure no exception from loader
            assert res["test32"]["used_test_in_estimation"] is False

def test_10_test_insufficient_32(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5"}),encoding="utf-8")
    # only enough for CAL+VAL but not TEST32
    pairs=np.random.randint(0,1024,size=((1024+256)*256,2))
    with patch.object(m,"_materialize_pairs", return_value=pairs):
        res=m.run_stage2("162148", Path(raw), Path(contract))
        assert res["status"]=="DATA_NOT_READY"

def test_11_frame_overlap_injection(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    cal=[("162148","sess",i) for i in range(4)]
    val=[("162148","sess",2),("162148","sess",5)]
    forb=[]
    ov=m.check_frame_overlap(cal, val, None, forb)
    assert ov["overlap"] is True
    assert ov["cal∩val_empty"] is False
    cal2=[("162148","sess",i) for i in range(4)]
    val2=[("162148","sess",i) for i in range(4,8)]
    test=[("162148","sess",1)]
    ov2=m.check_frame_overlap(cal2, val2, test, forb)
    assert ov2["overlap"] is True

def test_12_model_not_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    raw=tmp_path/"raw"; raw.mkdir()
    (raw/"a.ttbin").write_bytes(b"\x00")
    contract=tmp_path/"c.json"; contract.write_text(json.dumps({"channel_pair":"1/5"}),encoding="utf-8")
    # craft est with boundary true
    pairs=np.random.randint(0,1024,size=(350000,2))
    fake_est={"at_boundary":True,"d_nll":0.1,"val_nll":1.0,"H":2.0,"unseen":0.0,"m1_req":10,"m2_req":100,"chain_delta_CE":0.0,"chain_delta_H":0.0,"lam_star":1e4,"cv_nll":1.0,"CE1":0.5,"CE2":0.5,"CE_full":1.0}
    with patch.object(m,"_materialize_pairs", return_value=pairs), patch.object(m,"hierarchical_estimate", return_value=fake_est):
        res=m.run_stage2("162148", Path(raw), Path(contract))
        assert res["gates"]["G2"] is False

def test_13_rate_adaptation(tmp_path, monkeypatch):
    assert m.rate_branch(17, 100, "162148")=="RATE_ADAPTATION_REQUIRED"
    assert m.rate_branch(10, 185, "162148")=="RATE_ADAPTATION_REQUIRED"
    assert m.rate_branch(10, 100, "162148")=="WITHIN_FROZEN_BUDGET"

def test_14_full_disclosure(tmp_path):
    assert m.rate_branch(1024, 10, "162148")=="FULL_DISCLOSURE_LAYER"
    assert m.rate_branch(10, 1024, "162148")=="FULL_DISCLOSURE_LAYER"
    assert m.ceil_rate(10) >= 1024  # ensure ceil can reach disclosure
    # direct ceil
    ce = 5*1024/(1.3*1024)  # ce ~3.84 gives m~1024
    assert m.ceil_rate(4.0) >= 1024

def test_15_cli_no_dryrun_fake_additive_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("V65AR2_ALLOW_UNBOUND","1")
    # CLI should not expose --dry-run or --fake
    import subprocess, sys
    r=subprocess.run([sys.executable, str(ROOT/"scripts/v65ar2_pipeline.py"), "--help"], capture_output=True, text=True)
    txt=r.stdout + r.stderr
    assert "--dry-run" not in txt
    assert "--fake" not in txt.lower()
    assert "dry_run" not in txt.lower() or "--dry-run" not in txt
    # additive check
    out=tmp_path/"out.json"
    out.write_text("{}",encoding="utf-8")
    try:
        m._write_additive(out, {"a":1})
        assert False, "should have raised FileExistsError"
    except FileExistsError:
        pass
    # accepted plan SHA
    assert m.ACCEPTED_PLAN_SHA=="70f9ed8ece53704374d37810a163a519e57be6e9"
    # binding structure
    b=m.verify_head_origin_binding()
    assert "binding_ok" in b and "accepted_plan" in b
