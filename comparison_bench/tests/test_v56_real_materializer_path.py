"""Decoder-free real path test: miniature deterministic TTBin fixture via same materializer."""
import importlib.util
from pathlib import Path
import numpy as np

REPO=Path(__file__).resolve().parents[2]
REPLAY=REPO/"openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py"

def load_replay():
    spec=importlib.util.spec_from_file_location("replay_v13_vs_current", str(REPLAY))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_real_three_paths_and_first_fork():
    mod=load_replay()
    from src.qkd_io.ttbin_pipeline import TTBinEvents
    # miniature deterministic fixture: fixed frames [0,1,2,3] with frame-0 anchor ensuring global framing non-empty
    PERIOD=204800; BIN=200
    base=1_000_000_000
    times=[]; chans=[]
    # frame-0 anchor ensures tmin at frame 0 so filtering [0,1,2,3] non-empty (distinct bin from loop)
    t_anchor=base + 0*PERIOD + 700*BIN
    times.append(t_anchor); chans.append(1); times.append(t_anchor+5); chans.append(5)
    for fid in [0,1,2,3]:
        for b in [10, 100, 500]:
            t = base + fid*PERIOD + b*BIN
            times.append(t); chans.append(1)
            times.append(t + 5); chans.append(5)
    times=np.array(times,dtype=np.int64); chans=np.array(chans,dtype=np.int64)
    # deterministic order
    order=np.argsort(times)
    events=TTBinEvents(time_ps=times[order], channel=chans[order], event_type=None, missed_events=None)
    v13_params={"delay_used_ps": -50, "bin_width_ps":200, "frame_bins":1024, "coin_window_ps":40000, "ch_a":1, "ch_b":5}
    cur_params={"delay_used_ps": 50, "bin_width_ps":200, "frame_bins":1024, "coin_window_ps":40000, "ch_a":1, "ch_b":5}
    v13_cfg=mod.build_cfg_from_params(v13_params)
    cur_cfg=mod.build_cfg_from_params(cur_params)
    v13_st, cur_st, corr_st, first, corr_cfg = mod._recompute_stage_array(events, v13_cfg, cur_cfg, fixed_frames=[0,1,2,3])
    # must have 7 stages each
    assert set(v13_st.keys())==set(mod.STAGES)
    assert set(cur_st.keys())==set(mod.STAGES)
    assert set(corr_st.keys())==set(mod.STAGES)
    # first divergent should be pairing or delay stage due to offset difference
    assert first in mod.STAGES
    # corrected should equal V13 for stages >= first
    for s in mod.STAGES:
        idx=mod.STAGES.index(s); fidx=mod.STAGES.index(first)
        va=v13_st[s]["array"]; co=corr_st[s]["array"]
        if idx >= fidx:
            assert np.array_equal(va, co), f"corrected should match V13 at {s}"
    # V13 vs current should differ at first
    va=v13_st[first]["array"]; ca=cur_st[first]["array"]
    assert not np.array_equal(va, ca)
    # bin not proxied: bin array distinct object from symbol array and computed via floor_div
    assert not np.array_equal(v13_st["bin_index"]["array"], v13_st["symbol_1024"]["array"]) or v13_st["bin_index"]["array"].size==0 or np.all(v13_st["bin_index"]["array"]>=1024)
    assert "floor_div" in v13_st["bin_index"]["note"] or "bin via" in v13_st["bin_index"]["note"]
    # downstream must be non-empty when using fixed frames [0,1,2,3] with anchor
    assert v13_st["symbol_1024"]["array"].size > 0
    assert v13_st["U1U2"]["array"].size > 0
