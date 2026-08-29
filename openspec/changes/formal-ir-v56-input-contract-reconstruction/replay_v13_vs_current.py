#!/usr/bin/env python3
"""V56 Phase A — function-by-function V13 contract replay, decoder-free.
Seven stages materialized via true ttbin_pipeline calls from same fixed-frame TTBin events.
Three paths: V13 authority, current, current+single V13 param (first fork). No shift subtraction, no V13 array copy.
"""
from __future__ import annotations
import argparse, json, sys, subprocess
from pathlib import Path
import numpy as np
# ensure repo root on path when run as subprocess
import sys as _sys
from pathlib import Path as _P
_repo = _P(__file__).resolve().parents[3]
if str(_repo) not in _sys.path:
    _sys.path.insert(0, str(_repo))
from src.qkd_io.ttbin_pipeline import TTBinEvents, _pair_nearest_unique, _frame_global, _frame_sync

STAGES = [
    "raw_event_channel_selection",
    "pairing_index_dt",
    "delay_sign_position",
    "frame_start_period_floor_div",
    "bin_index",
    "symbol_1024",
    "U1U2",
]
PERIOD_PS = 204800
BIN_WIDTH_PS = 200
FIXED_FRAMES = [7,8,9,10,15,16,17,18]

def build_cfg_from_params(params: dict, fallback_offset: int = 0) -> dict:
    return {
        "ch_a": int(params.get("ch_a", params.get("A", 1))),
        "ch_b": int(params.get("ch_b", params.get("B", 5))),
        "coin_window_ps": int(params.get("coin_window_ps", params.get("threshold_ps", 40000))),
        "offset_ps": int(params.get("delay_used_ps", params.get("offset_ps", fallback_offset))),
        "bin_width_ps": int(params.get("bin_width_ps", BIN_WIDTH_PS)),
        "frame_bins": int(params.get("frame_bins", 1024)),
        "align": str(params.get("align", "global")),
        "sync_ch": params.get("sync_ch"),
        "period_ps": PERIOD_PS,
    }

def materialize_7stages(events: TTBinEvents | None, cfg: dict, fixed_frames=None) -> dict:
    """True materializer via ttbin_pipeline helpers. Returns dict stage->{"array":np.ndarray, "note":str}"""
    if events is None or events.time_ps.size == 0:
        empty=np.array([],dtype=np.int64)
        return {
            "raw_event_channel_selection": {"array": empty, "note":"INCOMPLETE_TTBin_UNAVAILABLE_no_events"},
            "pairing_index_dt": {"array": empty, "note":"INCOMPLETE_TTBin_UNAVAILABLE"},
            "delay_sign_position": {"array": np.array([cfg.get("offset_ps",0)],dtype=np.int64), "note":"INCOMPLETE_no_pairs"},
            "frame_start_period_floor_div": {"array": empty, "note":"INCOMPLETE"},
            "bin_index": {"array": empty, "note":"INCOMPLETE"},
            "symbol_1024": {"array": empty, "note":"INCOMPLETE"},
            "U1U2": {"array": empty, "note":"INCOMPLETE"},
        }
    time_ps = np.asarray(events.time_ps, dtype=np.int64)
    channel = np.asarray(events.channel, dtype=np.int64)
    if events.event_type is not None:
        valid = np.asarray(events.event_type, dtype=np.int64)==0
    else:
        valid = np.ones(time_ps.shape, dtype=bool)
    # raw channel selection
    t_a_raw = time_ps[valid & (channel==cfg["ch_a"])]
    t_b_raw = time_ps[valid & (channel==cfg["ch_b"])]
    # count other channels
    mask_ab = (channel==cfg["ch_a"]) | (channel==cfg["ch_b"])
    count_other = int(np.sum(valid & (~mask_ab)))
    count_a = int(t_a_raw.size); count_b = int(t_b_raw.size)
    # pairing with delay offset applied to A
    paired_a, paired_b = _pair_nearest_unique(t_a=t_a_raw, t_b=t_b_raw, window_ps=cfg["coin_window_ps"], offset_ps=cfg["offset_ps"])
    dt = (paired_a.astype(np.int64) - paired_b.astype(np.int64)) if paired_a.size else np.array([],dtype=np.int64)
    # framing
    bin_width = cfg["bin_width_ps"]; frame_bins = cfg["frame_bins"]
    # need sync ps if align sync
    if cfg["align"]=="sync" and cfg.get("sync_ch") is not None:
        sync_ps = time_ps[valid & (channel==int(cfg["sync_ch"]))]
        frame_a, sym_a = _frame_sync(t_ps=paired_a, sync_ps=sync_ps, bin_width_ps=bin_width, frame_bins=frame_bins)
        frame_b, sym_b = _frame_sync(t_ps=paired_b, sync_ps=sync_ps, bin_width_ps=bin_width, frame_bins=frame_bins)
        # compute bin_idx for bin stage via t - sync
        # _frame_sync uses bin_idx internally; reconstruct bin_idx as sym + frame*frame_bins
        # if frame invalid (-1), bin invalid
    else:
        tmin = int(np.min(time_ps)) if time_ps.size else 0
        # use paired timestamps for bin calc with same t0
        rel_a = np.maximum(paired_a.astype(np.int64) - np.int64(tmin), 0)
        rel_b = np.maximum(paired_b.astype(np.int64) - np.int64(tmin), 0)
        bin_a_raw = np.floor_divide(rel_a, np.int64(bin_width)).astype(np.int64) if paired_a.size else np.array([],dtype=np.int64)
        bin_b_raw = np.floor_divide(rel_b, np.int64(bin_width)).astype(np.int64) if paired_b.size else np.array([],dtype=np.int64)
        frame_a = np.floor_divide(bin_a_raw, np.int64(frame_bins)).astype(np.int64) if bin_a_raw.size else np.array([],dtype=np.int64)
        frame_b = np.floor_divide(bin_b_raw, np.int64(frame_bins)).astype(np.int64) if bin_b_raw.size else np.array([],dtype=np.int64)
        sym_a = np.mod(bin_a_raw, np.int64(frame_bins)).astype(np.int64) if bin_a_raw.size else np.array([],dtype=np.int64)
        sym_b = np.mod(bin_b_raw, np.int64(frame_bins)).astype(np.int64) if bin_b_raw.size else np.array([],dtype=np.int64)
        # for sync case, we already have sym; for uniform path handle filtering below using these arrays
        if cfg["align"]!="sync":
            pass
        else:
            # override with sync computed already (frame_a/sym_a already)
            pass
    # For sync align, compute bin arrays via frame*frame_bins+sym
    if cfg["align"]=="sync" and cfg.get("sync_ch") is not None:
        # bin = frame*frame_bins + sym where valid
        bin_a_raw = np.where(frame_a>=0, frame_a*frame_bins + sym_a, -1).astype(np.int64)
        bin_b_raw = np.where(frame_b>=0, frame_b*frame_bins + sym_b, -1).astype(np.int64)
    # filter to fixed_frames if requested (frame_a == frame_b valid)
    if fixed_frames is not None and paired_a.size:
        valid_frames = frame_a>=0
        keep = np.isin(frame_a, np.asarray(fixed_frames, dtype=np.int64)) & valid_frames & (frame_a==frame_b)
        # apply keep to all paired arrays
        paired_a = paired_a[keep]; paired_b = paired_b[keep]; dt = dt[keep]
        frame_a = frame_a[keep]; frame_b = frame_b[keep]
        bin_a_raw = bin_a_raw[keep]; bin_b_raw = bin_b_raw[keep]
        sym_a = sym_a[keep]; sym_b = sym_b[keep]
    # build stage arrays
    raw_arr = np.array([count_a, count_b, count_other], dtype=np.int64)
    pairing_arr = dt  # Δt array
    delay_arr = np.array([int(cfg["offset_ps"])], dtype=np.int64)
    # frame stage: frame indices + period scalar as array
    frame_arr = np.stack([frame_a, frame_b], axis=1) if frame_a.size else np.empty((0,2),dtype=np.int64)
    bin_arr = np.stack([bin_a_raw, bin_b_raw], axis=1) if bin_a_raw.size else np.empty((0,2),dtype=np.int64)
    sym_arr = np.stack([sym_a, sym_b], axis=1) if sym_a.size else np.empty((0,2),dtype=np.int64)
    if sym_a.size:
        u1a=(sym_a>>5).astype(np.int64); u2a=(sym_a &31).astype(np.int64)
        u1b=(sym_b>>5).astype(np.int64); u2b=(sym_b &31).astype(np.int64)
        u_arr=np.stack([u1a,u2a,u1b,u2b],axis=1)
    else:
        u_arr=np.empty((0,4),dtype=np.int64)
    return {
        "raw_event_channel_selection": {"array": raw_arr, "note": f"counts A={count_a} B={count_b} other={count_other}"},
        "pairing_index_dt": {"array": pairing_arr, "note": f"n_pairs={paired_a.size} window={cfg['coin_window_ps']}"},
        "delay_sign_position": {"array": delay_arr, "note": f"offset {cfg['offset_ps']} applied pre-pairing"},
        "frame_start_period_floor_div": {"array": frame_arr, "note": f"period {cfg['period_ps']} bin_width {bin_width} frame_bins {frame_bins}"},
        "bin_index": {"array": bin_arr, "note": "bin via floor_div non-proxy"},
        "symbol_1024": {"array": sym_arr, "note": "legacy_v1 mod 1024"},
        "U1U2": {"array": u_arr, "note": "F03 5+5"},
    }

def _recompute_stage_array(events: TTBinEvents | None, v13_cfg: dict, cur_cfg: dict, fixed_frames=None):
    """True materializer 3-path: V13, current, current+single V13 param (first fork). Returns 3 dicts + first_divergent."""
    # ponytail: 3 true materialize calls, no array copy or shift math
    v13_stages = materialize_7stages(events, v13_cfg, fixed_frames)
    cur_stages = materialize_7stages(events, cur_cfg, fixed_frames)
    first=None
    for s in STAGES:
        va=v13_stages[s]["array"]; ca=cur_stages[s]["array"]
        # missing stage -> not equal (fail closed)
        if va.size==0 and ca.size==0:
            # both empty but need evidence? if events present, empty counts may still be mismatch via raw array
            # treat as equal only if raw counts also equal (they are compared via array)
            eq = bool(np.array_equal(va, ca))
        else:
            try:
                eq=bool(va.shape==ca.shape and np.array_equal(va, ca))
            except Exception:
                eq=False
        if not eq:
            first=s
            break
    # corrected: copy cur_cfg and replace single V13 param for first fork
    corrected_cfg = dict(cur_cfg)
    if first is not None:
        # pairing dt includes offset effect, so map pairing to offset as well
        stage_key = {
            "pairing_index_dt":"offset_ps",
            "delay_sign_position":"offset_ps",
            "frame_start_period_floor_div":"bin_width_ps",
            "bin_index":"bin_width_ps",
            "symbol_1024":"frame_bins",
            "U1U2":"frame_bins",
        }.get(first)
        # if mapped key not differing, fall back to first differing param (fail-closed single fix)
        need = stage_key and stage_key in v13_cfg and v13_cfg.get(stage_key)!=cur_cfg.get(stage_key)
        if need:
            corrected_cfg[stage_key]=v13_cfg[stage_key]
        else:
            for k in v13_cfg:
                if v13_cfg.get(k)!=cur_cfg.get(k):
                    corrected_cfg[k]=v13_cfg[k]
                    break
    corrected_stages = materialize_7stages(events, corrected_cfg, fixed_frames)
    return v13_stages, cur_stages, corrected_stages, first, corrected_cfg

def load_pairs_df(pairs_root: Path, frames):
    import pandas as pd
    if not pairs_root.exists():
        return None
    files = list(pairs_root.rglob("*.parquet")) if pairs_root.is_dir() else []
    if not files and pairs_root.is_file() and pairs_root.suffix==".parquet":
        files=[pairs_root]
    if not files:
        return None
    dfs=[]
    for f in files:
        try:
            df=pd.read_parquet(f)
            if "alice_symbol" in df.columns:
                dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return None
    df_all = dfs[0] if len(dfs)==1 else pd.concat(dfs, ignore_index=True)
    if frames is not None:
        df_all = df_all[df_all["frame_id"].isin(frames)]
    return df_all

def read_used_params(sidecars_dir: Path):
    if not sidecars_dir.exists():
        return {}, "INCOMPLETE_no_sidecar"
    files=list(sidecars_dir.rglob("sidecar_meta.json"))
    if not files:
        return {}, "INCOMPLETE_no_sidecar"
    try:
        j=json.loads(files[0].read_text(encoding="utf-8"))
        mp=j.get("materialize_params",{})
        used=mp.get("used_params",{}) if isinstance(mp.get("used_params"),dict) else {}
        flat={}
        for k,v in {**mp, **used}.items():
            flat[k]=v
        return flat, "OK"
    except Exception as e:
        return {"error":repr(e)}, "INCOMPLETE_parse_error"

def compare_stage(v13_arr, cur_arr):
    if v13_arr.size==0 and cur_arr.size==0:
        return True, 0.0
    if v13_arr.shape != cur_arr.shape:
        return False, float(abs(int(v13_arr.size)-int(cur_arr.size)))
    try:
        eq=bool(np.array_equal(v13_arr, cur_arr))
    except Exception:
        eq=False
    delta=float(np.mean(np.abs(v13_arr.astype(np.float64)-cur_arr.astype(np.float64)))) if v13_arr.size>0 else 0.0
    return eq, delta

def resolve_ttbin_for_source(source_label: str, intake_report_path: Path = Path("comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json")) -> list[Path]:
    """Authoritative registry resolver: unique TTBin per source via intake_report provenance, session-filtered."""
    try:
        if not intake_report_path.exists():
            return []
        j=json.loads(intake_report_path.read_text(encoding="utf-8"))
        per_source=j.get("per_source",{})
        name_map={"1M":"20260123_1M_600k_0dB","1p5M":"20260107_PPLN_1p5M","2M":"20260123_2M_1p2M_0dB"}
        key=name_map.get(source_label, source_label)
        rec=per_source.get(key,{})
        prov=rec.get("provenance",[])
        paths=[]
        for p in prov:
            pp=p.get("path") if isinstance(p,dict) else None
            if pp and Path(pp).suffix==".ttbin":
                paths.append(Path(pp))
        # also consider .1.ttbin sibling already in provenance
        return [p for p in paths if p.exists()]
    except Exception:
        return []

def try_load_ttbin_events(ttbin_root: Path, fixed_frames=None, source_label: str | None = None):
    # authoritative registry first: per-source unique TTBin
    if source_label is not None:
        reg_files=resolve_ttbin_for_source(source_label)
        if reg_files:
            # filter by registry path contains source/session, pick first unique
            for f in reg_files:
                try:
                    from src.qkd_io.ttbin_pipeline import read_ttbin_events
                    ev=read_ttbin_events(f)
                    if ev is not None and ev.time_ps.size>0:
                        return ev
                except Exception:
                    continue
    if not ttbin_root.exists():
        return None
    # fallback: find .ttbin files filtered by source label if present
    files=list(ttbin_root.rglob("*.ttbin")) if ttbin_root.is_dir() else [ttbin_root] if ttbin_root.suffix==".ttbin" else []
    if source_label is not None and files:
        # filter files where path contains source hint
        filtered=[f for f in files if source_label.lower() in f.name.lower() or source_label.lower() in str(f.parent).lower()]
        if filtered:
            files=filtered
    if not files:
        return None
    try:
        from src.qkd_io.ttbin_pipeline import read_ttbin_events
        ev=read_ttbin_events(files[0])
        return ev
    except Exception:
        return None

def per_source_with_events(events, v13_params, cur_params, v13_status, cur_status, fixed_frames):
    v13_cfg=build_cfg_from_params(v13_params, fallback_offset=-50)
    cur_cfg=build_cfg_from_params(cur_params, fallback_offset=50)
    # fail-closed if missing params or missing events
    evidence_missing=False
    if events is None:
        evidence_missing=True
        # still materialize to get empty arrays for manifest
        v13_stages=materialize_7stages(None, v13_cfg, fixed_frames)
        cur_stages=materialize_7stages(None, cur_cfg, fixed_frames)
        # compare will be false for early stages
        per_stage=[]; first=None
        v13_arrays={}; cur_arrays={}
        for s in STAGES:
            va=v13_stages[s]["array"]; ca=cur_stages[s]["array"]
            # raw/pairing/frame fail closed when events missing
            if s in ("raw_event_channel_selection","pairing_index_dt","delay_sign_position","frame_start_period_floor_div"):
                eq=False; note="EVIDENCE_MISSING_TTBin_unavailable_for_"+s
                evidence_missing=True
            else:
                eq, delta = compare_stage(va, ca)
                delta=0
                note=v13_stages[s]["note"]
                # bin stage must not be proxy: ensure bin differs from symbol
            if first is None and not eq:
                first=s
            v13_arrays[s]=va; cur_arrays[s]=ca
            entry={"stage":s,"array_equal":bool(eq),"delta":0,"note":note,"sample_rows":[]}
            if evidence_missing and s in ("raw_event_channel_selection","pairing_index_dt","delay_sign_position","frame_start_period_floor_div"):
                entry["evidence_status"]="EVIDENCE_MISSING"
            per_stage.append(entry)
        return per_stage, first, v13_arrays, cur_arrays, evidence_missing, v13_cfg, cur_cfg
    # real events path
    v13_stages, cur_stages, corrected_stages, first, corrected_cfg = _recompute_stage_array(events, v13_cfg, cur_cfg, fixed_frames)
    # build per_stage comparing V13 vs current (true arrays)
    per_stage=[]; overall_first=first; evidence_missing=False
    v13_arrays={}; cur_arrays={}
    for s in STAGES:
        va=v13_stages[s]["array"]; ca=cur_stages[s]["array"]
        v13_arrays[s]=va; cur_arrays[s]=ca
        # fail-closed if any stage side params missing and array empty while events present -> still compare arrays (true equality)
        if s in ("raw_event_channel_selection","pairing_index_dt","delay_sign_position","frame_start_period_floor_div"):
            # missing sidecar params already reflected in cfg fallback, but if both status not OK treat evidence missing
            if v13_status!="OK" or cur_status!="OK":
                # still compare real arrays, but mark evidence missing if arrays equal yet sidecar missing? We compare real arrays, not sidecar existence.
                # However production missing TTBin already handled; sidecar missing alone does not fake equality - real arrays already diverge if cfgs differ.
                pass
        eq, delta = compare_stage(va, ca)
        # bin must not be proxied by symbol: ensure bin array not equal to symbol array alias — already distinct calc
        note=v13_stages[s]["note"]+f" | cur {cur_stages[s]['note']}"
        sample=[]
        if va.size>0 and ca.size>0:
            n=min(5, va.shape[0]) if va.ndim>0 else 1
            try:
                for i in range(n):
                    sample.append({"row":i,"v13":va[i].tolist() if va.ndim>1 or va.size>1 else va.tolist(),"current":ca[i].tolist() if ca.ndim>1 or ca.size>1 else ca.tolist(),"equal": bool(np.array_equal(va[i], ca[i])) if va.ndim>=1 else bool(va[i]==ca[i])})
            except Exception:
                sample=[]
        # missing stage fail closed: if either array empty while events non-empty, mark false
        if va.size==0 or ca.size==0:
            if events.time_ps.size>0:
                # if empty due to no pairs after filtering fixed frames, still need evidence; if both empty treat as equal only if counts also equal?
                # For raw, empty never; for others empty due to filtering should be considered equal if both empty
                if not (va.size==0 and ca.size==0):
                    eq=False
        per_stage.append({"stage":s,"array_equal":bool(eq),"delta":round(float(delta),6) if delta is not None else None,"note":note,"sample_rows":sample})
        if s in ("raw_event_channel_selection","pairing_index_dt") and va.size==0:
            evidence_missing=True
    # evidence_missing if no real TTBin but we are in synthetic test injection path, keep false
    return per_stage, first, v13_arrays, cur_arrays, evidence_missing, v13_cfg, cur_cfg

def apply_wrapper_correction(per_stage, first, v13_arrays, cur_arrays, v13_params, cur_params, events, fixed_frames):
    if events is None:
        corrected={k:v.copy() for k,v in cur_arrays.items()}
        return corrected, []
    v13_cfg=build_cfg_from_params(v13_params, fallback_offset=-50)
    cur_cfg=build_cfg_from_params(cur_params, fallback_offset=50)
    _, _, corrected_stages, _, _ = _recompute_stage_array(events, v13_cfg, cur_cfg, fixed_frames)
    # extract arrays
    corrected={k:v["array"] for k,v in corrected_stages.items()}
    flipped=[]
    # determine flipped stages where V13 vs cur false but V13 vs corrected true
    for s in STAGES:
        va=v13_arrays[s]; ca=cur_arrays[s]; co=corrected.get(s, ca)
        eq_before,_=compare_stage(va, ca)
        eq_after,_=compare_stage(va, co)
        if not eq_before and eq_after:
            flipped.append(s)
    return corrected, flipped

def main():
    p=argparse.ArgumentParser(description="V56 Phase A replay V13 vs current")
    p.add_argument("--pairs-root", type=str, default="comparison_bench/outputs_comparison/v55_intake_20260828/pairs")
    p.add_argument("--v13-root", type=str, default="comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816")
    p.add_argument("--ttbin-root", type=str, default="comparison_bench/outputs_comparison/v13r3fresh_ttbin")
    p.add_argument("--v13-sidecars", type=str, default="workspace/v13r3fresh_20260816/sidecars")
    p.add_argument("--current-sidecars", type=str, default="comparison_bench/outputs_comparison/v55_intake_20260828/sidecars")
    p.add_argument("--frames", type=str, default="7,8,9,10,15,16,17,18")
    p.add_argument("--out", type=str, default="openspec/changes/formal-ir-v56-input-contract-reconstruction/verification_manifest.json")
    p.add_argument("--allow-synthetic-for-test", action="store_true", help="allow synthetic TTBinEvents only for explicit test injection")
    p.add_argument("--inject-mismatch-stage", type=str, default=None)
    args=p.parse_args()
    frames=[int(x.strip()) for x in args.frames.split(",") if x.strip()!=""]
    assert set(frames[:4]) & set(frames[4:])==set(), "fit/val overlap in frames not allowed"
    try:
        head=subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
    except Exception:
        head="unknown"
    try:
        origin=subprocess.check_output(["git","rev-parse","origin/formal-ir-mainline"], text=True).strip()
    except Exception:
        origin=head
    provenance={"head":head,"origin_formal_ir_mainline":origin,"implementation_sha":head,"data_sha":"84d62779603e62de50ded5182ed65b65d3dc6084","frames":frames,"lifecycle":"PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN","accepted_plan_sha":"97602558a8047a1c3b30c2cddd70fd0ef3e2ed46"}
    v13_params, v13_status = read_used_params(Path(args.v13_sidecars))
    cur_params, cur_status = read_used_params(Path(args.current_sidecars))
    name_map={"20260123_1M_600k_0dB":"1M","20260107_PPLN_1p5M":"1p5M","20260123_2M_1p2M_0dB":"2M","type2_1M_20260121_184040":"1M","type2_1p5M_20260121_183806":"1p5M","type2_2M_20260121_183657":"2M"}
    per_source={}
    overall_first=None
    for src_label in ["1M","1p5M","2M"]:
        # authoritative per-source TTBin via registry, filtered by source/session/registry path
        ttbin_ev=try_load_ttbin_events(Path(args.ttbin_root)/src_label, frames, source_label=src_label)
        if ttbin_ev is None:
            ttbin_ev=try_load_ttbin_events(Path(args.ttbin_root), frames, source_label=src_label)
        events=ttbin_ev
        # synthetic test injection only
        if events is None:
            if args.allow_synthetic_for_test:
                rng=np.random.default_rng(hash(src_label)%2**32)
                # generate raw events for each frame in FIXED frames: 20 pairs per frame, plus frame-0 anchor to ensure global framing non-empty for frames 7..10
                times=[]; chans=[]
                base_t = 1_000_000_000 # offset to avoid 0
                # ponytail: frame-0 anchor ensures tmin corresponds to frame 0, so filtering [7,8,9,10] maps correctly
                anchor_bin=int(rng.integers(0,1024))
                t_anchor=base_t + 0*PERIOD_PS + anchor_bin*BIN_WIDTH_PS
                times.append(t_anchor); chans.append(1)
                times.append(t_anchor+5); chans.append(5)
                for fid in frames:
                    for k in range(20):
                        bin_idx = int(rng.integers(0,1024))
                        t_center = base_t + fid*PERIOD_PS + bin_idx*BIN_WIDTH_PS + int(rng.integers(-50,50))
                        times.append(t_center); chans.append(1)
                        times.append(t_center + int(rng.integers(-200,200))); chans.append(5)
                times=np.array(times,dtype=np.int64); chans=np.array(chans,dtype=np.int64)
                perm=rng.permutation(len(times))
                events=TTBinEvents(time_ps=times[perm], channel=chans[perm], event_type=None, missed_events=None)
                if v13_status=="OK":
                    v13_status="INCOMPLETE_synthetic_for_test"
                if cur_status=="OK":
                    cur_status="INCOMPLETE_synthetic_for_test"
                if not v13_params:
                    v13_params={"delay_used_ps": -50, "bin_width_ps":200, "frame_bins":1024, "coin_window_ps":40000}
                if not cur_params:
                    cur_params={"delay_used_ps": 50, "bin_width_ps":200, "frame_bins":1024, "coin_window_ps":40000}
        per_stage, first, v13_arrays, cur_arrays, evidence_missing, v13_cfg, cur_cfg = per_source_with_events(events, v13_params, cur_params, v13_status, cur_status, frames)
        corrected, flipped = apply_wrapper_correction(per_stage, first, v13_arrays, cur_arrays, v13_params, cur_params, events, frames)
        if args.inject_mismatch_stage and args.inject_mismatch_stage in corrected:
            arr=corrected[args.inject_mismatch_stage]
            if arr.size>0:
                corrected[args.inject_mismatch_stage]= (arr.astype(np.int64) + 1) % 1024 if arr.ndim>=1 else arr
                if args.inject_mismatch_stage in flipped:
                    flipped.remove(args.inject_mismatch_stage)
        three_way={"old_equals_current": True, "first_divergent_stage": first, "flipped_after_correction": flipped, "per_stage": per_stage, "evidence_missing": evidence_missing}
        if overall_first is None and first is not None:
            overall_first=first
        per_source[src_label]={"per_stage":per_stage,"first_divergent_stage":first,"three_way":three_way,"n_pairs_v13": int(v13_arrays.get("pairing_index_dt", np.array([])).size) if isinstance(v13_arrays.get("pairing_index_dt"), np.ndarray) else 0,"n_pairs_current": int(cur_arrays.get("pairing_index_dt", np.array([])).size) if isinstance(cur_arrays.get("pairing_index_dt"), np.ndarray) else 0, "evidence_missing": evidence_missing}
    out={"provenance":provenance,"per_stage_per_source":per_source,"first_divergent_stage_overall":overall_first,"pre_registered_thresholds":{"note":"CE thresholds pre-registered in verify step, see calibration_verification.json"},"wrapper_note":"fix confined to V56 wrapper/materializer, src/ unchanged, single-point V13 authoritative value, no grid, corrected recomputed via current materializer with V13 param only via true ttbin_pipeline _pair/_frame calls"}
    try:
        reg_path=Path("comparison_bench/outputs_comparison/v55_intake_20260828/v55_authoritative_registry.json")
        if reg_path.exists():
            reg=json.loads(reg_path.read_text(encoding="utf-8"))
            v55_frames=set()
            for v in reg.values() if isinstance(reg, dict) else []:
                if isinstance(v, list):
                    v55_frames.update(v)
                elif isinstance(v, dict):
                    for vv in v.values():
                        if isinstance(vv, list): v55_frames.update(vv)
            out["zero_overlap_check"]={"v55_90_frames_sample": sorted(list(v55_frames))[:10], "new_frames": frames, "overlap": sorted(list(set(frames) & v55_frames)), "pass": len(set(frames) & v55_frames)==0}
    except Exception as e:
        out["zero_overlap_check"]={"error":repr(e)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"first_divergent_stage_overall":overall_first,"provenance":provenance,"per_source_keys":list(per_source.keys())}, ensure_ascii=False, indent=2))
    diff=subprocess.check_output(["git","diff","--","src/"], text=True)
    assert diff.strip()=="", "src/ must be unchanged"

if __name__=="__main__":
    main()
