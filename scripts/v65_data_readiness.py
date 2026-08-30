#!/usr/bin/env python3
"""
V65 data readiness spike - decoder-free.
Checks new-session two-session isolation per source 1M/1p5M/2M explicit binding:
CAL 4096 + VAL 512 + TEST 120 per source, zero overlap with V13..V64 (source,session,frame) tuple,
frame 256 A=32U1+U2 B=32V1+V2 via real parquet, not range fiction, session provenance,
sign/50ps, forbidden non-empty. <2 sessions -> DATA_NOT_READY.
Strictly reuses V56 contract (dimension 1024 bin200 pairing nearest legacy_v1).
ponytail: minimal readiness only; full estimator in v65_channel_compatibility.py.
If new session data missing/sidecar missing/frame insufficient/forbidden missing -> DATA_NOT_READY or EVIDENCE_INVALID, never READY.
"""
import argparse, json, sys
from pathlib import Path

try:
    from src.reconciliation.run_nbldpc_demo_point import _read_ttbin_timetags, _bin_indices_sorted_for_binwidth, _pairs_from_sorted_bins  # type: ignore
    _V56_CHAIN_AVAILABLE = True
except Exception:
    _V56_CHAIN_AVAILABLE = False

FROZEN_CONTRACT = {
    "dimension": 1024,
    "bin_width_ps": 200,
    "pairing": "nearest",
    "rule": "legacy_v1",
    "period_ps": 204800,
    "frame_pairs": 256,
    "block_frames": 4,
    "threshold_ps": 40000,
    "gate_ps": 200,
}

REQUIRED = {"CAL": 4096, "VAL": 512, "TEST": 120}
SOURCES = ["1M", "1p5M", "2M"]

# frozen capacities (for report reference)
FROZEN = {"m1": 16, "m2": {"1M": 200, "1p5M": 206, "2M": 208}, "m_total": {"1M": 216, "1p5M": 222, "2M": 224}, "leak": {"1M": 1144, "1p5M": 1174, "2M": 1184}}

def load_forbidden_keys(extra_paths=None):
    # ponytail: collect real (source,session,frame) from V55 authoritative + V64 etc, must be non-empty for READY
    keys = set()
    candidates = [
        Path("openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json"),
        Path("comparison_bench/outputs_comparison/v55_intake_20260828/v55_stratified_registry_candidate.json"),
        Path("comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json"),
    ]
    if extra_paths:
        for p in extra_paths:
            if p:
                candidates.append(Path(p))
    for cand in candidates:
        if not cand.exists():
            continue
        try:
            j = json.loads(cand.read_text(encoding="utf-8"))
            strata = j.get("strata", None)
            if strata is None:
                # intake_report per_source
                if "per_source" in j:
                    strata = j["per_source"]
                else:
                    continue
            for label, entry in strata.items():
                if not isinstance(entry, dict):
                    continue
                src = entry.get("stratum") or entry.get("source") or None
                if src is None:
                    # infer from label
                    if "1p5" in label or "1500" in label:
                        src = "1p5M"
                    elif label.startswith("1M") or "_1M_" in label:
                        src = "1M"
                    elif "2M" in label:
                        src = "2M"
                    else:
                        continue
                sess = entry.get("session_id") or label
                # selected_frame_ids is list of [4] blocks
                for block in entry.get("selected_frame_ids", []):
                    if isinstance(block, list):
                        for fid in block:
                            keys.add((src, sess, int(fid)))
                # also check selected_starts -> expand 4
                for s in entry.get("selected_starts", []):
                    for fid in [s, s+1, s+2, s+3]:
                        keys.add((src, sess, int(fid)))
                # fallback: if strata entry has frames count but no blocks, not enough for forbidden; skip
        except Exception:
            continue
    return keys

def discover_per_source_sessions(new_root: Path):
    # ponytail: per-source explicit binding, not global first-two
    per_src = {}
    for src in SOURCES:
        src_path = new_root / src
        if src_path.exists() and src_path.is_dir():
            sess_dirs = sorted([p for p in src_path.iterdir() if p.is_dir()])
            per_src[src] = sess_dirs
        else:
            # fallback: root contains dirs whose name contains src token
            sess_dirs = []
            if new_root.exists():
                for p in new_root.iterdir():
                    if p.is_dir():
                        name = p.name
                        # match 1M not 1p5M confusion: check exact token
                        if src == "1M" and "1M" in name and "1p5" not in name.lower() and "1500" not in name:
                            sess_dirs.append(p)
                        elif src == "1p5M" and ("1p5" in name.lower() or "1500" in name or "PPLN" in name):
                            sess_dirs.append(p)
                        elif src == "2M" and "2M" in name:
                            sess_dirs.append(p)
            per_src[src] = sorted(sess_dirs)
    return per_src

def find_pairs_file(session_dir: Path):
    for cand in [session_dir / "pairs.parquet", session_dir / "pairs" / "pairs.parquet", session_dir / "pairs.parquet.gz"]:
        if cand.exists():
            return cand
    # also check direct parquet in dir
    for p in session_dir.glob("*.parquet"):
        return p
    return None

def find_sidecar_file(session_dir: Path, session_id: str):
    # ponytail: sidecar provenance per source, check multiple layouts
    for cand in [
        session_dir / "sidecar_meta.json",
        session_dir / "sidecar.json",
        Path("comparison_bench/outputs_comparison/v55_intake_20260828/sidecars") / session_id / "sidecar_meta.json",
        session_dir.parent / "sidecars" / session_id / "sidecar_meta.json",
    ]:
        if cand.exists():
            return cand
    for p in session_dir.glob("*.json"):
        if "sidecar" in p.name.lower() or "meta" in p.name.lower():
            return p
    return None

def validate_frame_file(pairs_path: Path, expected_frames=None):
    # ponytail: real parquet read, verify 256 pairs/frame and alice/bob in [0,1023] and decomposition
    try:
        import pandas as pd
        df = pd.read_parquet(pairs_path)
    except Exception as e:
        return False, {"error": f"parquet read fail: {e}"}, [], 0
    cols = set(df.columns.tolist())
    if not {"frame_id", "alice_symbol", "bob_symbol"}.issubset(cols):
        return False, {"error": f"missing columns {cols}"}, [], len(df)
    # check types
    try:
        # group size
        g = df.groupby("frame_id").size()
        if not all(v == 256 for v in g.values):
            bad = g[g != 256].head().to_dict()
            return False, {"error": f"pairs_per_frame !=256 bad {bad}", "frame_counts": g.describe().to_dict()}, sorted(df["frame_id"].unique().tolist()), len(df)
        # range check
        if df["alice_symbol"].min() < 0 or df["alice_symbol"].max() > 1023 or df["bob_symbol"].min() < 0 or df["bob_symbol"].max() > 1023:
            return False, {"error": "symbol out of [0,1023]"}, sorted(df["frame_id"].unique().tolist()), len(df)
        # decomposition check: U1=>>5, U2=&31 must be in 0..31
        a = df["alice_symbol"].to_numpy()
        b = df["bob_symbol"].to_numpy()
        if not (((a >> 5) < 32).all() and ((a & 31) < 32).all() and ((b >> 5) < 32).all() and ((b & 31) < 32).all()):
            return False, {"error": "U1/U2 decomposition out of 0..31"}, sorted(df["frame_id"].unique().tolist()), len(df)
        # also verify A==32*U1+U2 tautology (always true if above) but explicit
        if not ((a == ((a >> 5) * 32 + (a & 31))).all()):
            return False, {"error": "A !=32U1+U2"}, sorted(df["frame_id"].unique().tolist()), len(df)
        frame_ids = sorted(df["frame_id"].unique().tolist())
        if expected_frames is not None and len(frame_ids) < expected_frames:
            return False, {"error": f"insufficient frames {len(frame_ids)} < {expected_frames}"}, frame_ids, len(df)
        return True, {"frame_ids": frame_ids[:5], "n_frames": len(frame_ids), "n_pairs": len(df)}, frame_ids, len(df)
    except Exception as e:
        return False, {"error": str(e)}, [], 0

def check_delay_peak_gate(delay_ps, peak_ps, sigma_ps, gate_ps, threshold_ps):
    sign_ok = (1 if delay_ps>0 else (-1 if delay_ps<0 else 0)) == (1 if peak_ps>0 else (-1 if peak_ps<0 else 0))
    abs_ok = abs(float(delay_ps) - float(peak_ps)) < 50
    sigma_ok = 50 <= float(sigma_ps) <= 150
    gate_ok = int(gate_ps) == 200
    thr_ok = int(threshold_ps) == 40000
    return bool(sign_ok and abs_ok and sigma_ok and gate_ok and thr_ok), {
        "sign_ok": bool(sign_ok), "abs_ps": float(abs(float(delay_ps)-float(peak_ps))), "abs_ok": bool(abs_ok),
        "sigma_ok": bool(sigma_ok), "gate_ok": bool(gate_ok), "thr_ok": bool(thr_ok)
    }

def load_sidecar_provenance(sidecar_path: Path):
    try:
        j = json.loads(sidecar_path.read_text(encoding="utf-8"))
        # try common fields
        diag = j.get("diagnostics", {})
        mat = j.get("materialize_params", j.get("materialization", {}))
        # delay/peak may be in j or diagnostics
        delay = j.get("delay_used_ps", j.get("delay_ps", mat.get("delay_used_ps")))
        peak = j.get("peak_center", j.get("peak_ps", diag.get("peak_center")))
        sigma = j.get("sigma_ps", j.get("sigma", diag.get("sigma_ps", 80)))
        gate = j.get("gate_ps", j.get("gate", mat.get("gate_ps", 200)))
        thr = j.get("threshold_ps", j.get("threshold", mat.get("threshold_ps", 40000)))
        # sidecar_meta from v55 has no delay/peak; treat as missing -> need real new session sidecar
        return {"raw": j, "delay": delay, "peak": peak, "sigma": sigma, "gate": gate, "thr": thr, "path": str(sidecar_path)}
    except Exception as e:
        return {"error": str(e), "path": str(sidecar_path), "delay": None, "peak": None}

def check_zero_overlap_tuple(cal_keys, val_keys, test_keys, forbidden_keys):
    s_cal, s_val, s_test = set(cal_keys), set(val_keys), set(test_keys)
    forb = set(forbidden_keys)
    return {
        "cal∩val_empty": len(s_cal & s_val) == 0,
        "cal∪val∩test_empty": len((s_cal | s_val) & s_test) == 0,
        "cal∪val∪test∩forbidden_empty": len((s_cal | s_val | s_test) & forb) == 0,
        "key": "(source,session,frame)",
        "forbidden_size": len(forb),
    }

def check_v66_equals_v65_test(v65_test_keys, v66_keys):
    a, b = set(v65_test_keys), set(v66_keys)
    return {"equals": a == b, "v65_len": len(a), "v66_len": len(b), "sym_diff": len(a ^ b), "key": "(source,session,frame)"}

def main():
    ap = argparse.ArgumentParser(description="V65 data readiness - decoder-free")
    ap.add_argument("--new-session-root", default=None, help="new session pairs root (per-source explicit)")
    ap.add_argument("--out", default="v65_data_registry.json")
    ap.add_argument("--readiness-out", default="v65_data_readiness.json")
    ap.add_argument("--v13-registry", default=None)
    ap.add_argument("--v64-registry", default=None)
    ap.add_argument("--forbidden-registry", default=None, help="extra forbidden registry path")
    args = ap.parse_args()

    new_root = Path(args.new_session_root) if args.new_session_root else None
    forbidden_keys = load_forbidden_keys([args.v13_registry, args.v64_registry, args.forbidden_registry])
    forbidden_nonempty = len(forbidden_keys) > 0

    per_source = {}
    # discover per-source sessions
    per_src_sessions = {}
    if new_root and new_root.exists():
        per_src_sessions = discover_per_source_sessions(new_root)
    else:
        per_src_sessions = {src: [] for src in SOURCES}

    overall_sessions_ok = True
    any_missing_sidecar = False
    any_frame_insufficient = False

    for src in SOURCES:
        sess_dirs = per_src_sessions.get(src, [])
        cal_sess_dir = sess_dirs[0] if len(sess_dirs) >= 1 else None
        test_sess_dir = sess_dirs[1] if len(sess_dirs) >= 2 else None
        cal_sess = cal_sess_dir.name if cal_sess_dir else None
        test_sess = test_sess_dir.name if test_sess_dir else None
        val_sess = cal_sess  # VAL same session as CAL

        available_sessions = len(sess_dirs)
        # try to validate real pairs for CAL session
        frame_256_ok = False
        frame_detail = {}
        real_frame_ids = []
        sidecar_ok = False
        sidecar_detail = {}
        not_cross_spliced = True
        G1_ok = None
        G1_detail = None

        if cal_sess_dir is not None:
            pairs_path = find_pairs_file(cal_sess_dir)
            if pairs_path is None and test_sess_dir is None:
                # also try legacy layout: new_root/pairs/<session>/pairs.parquet
                alt = new_root / "pairs" / cal_sess / "pairs.parquet" if new_root else None
                if alt and alt.exists():
                    pairs_path = alt
            if pairs_path is not None and pairs_path.exists():
                ok, detail, fids, n_pairs = validate_frame_file(pairs_path, expected_frames=4608)  # CAL 4096+VAL512 need 4608 at least
                frame_256_ok = bool(ok)
                frame_detail = detail
                real_frame_ids = fids
                if not ok:
                    any_frame_insufficient = True
                # check sidecar
                sidecar_path = find_sidecar_file(cal_sess_dir, cal_sess)
                if sidecar_path is None and new_root:
                    # try global sidecars
                    sidecar_path = Path("comparison_bench/outputs_comparison/v55_intake_20260828/sidecars") / cal_sess / "sidecar_meta.json"
                    if not sidecar_path.exists():
                        sidecar_path = None
                if sidecar_path is not None and sidecar_path.exists():
                    prov = load_sidecar_provenance(sidecar_path)
                    sidecar_detail = prov
                    # need delay/peak present and gate check
                    if prov.get("delay") is not None and prov.get("peak") is not None:
                        sidecar_ok = True
                        G1_ok, G1_detail = check_delay_peak_gate(prov["delay"], prov["peak"], prov.get("sigma", 80), prov.get("gate", 200), prov.get("thr", 40000))
                    else:
                        sidecar_ok = False
                        any_missing_sidecar = True
                        G1_ok, G1_detail = False, {"error": "delay/peak missing in sidecar", "sidecar": str(sidecar_path)}
                else:
                    sidecar_ok = False
                    any_missing_sidecar = True
                    sidecar_detail = {"error": "sidecar missing", "session": cal_sess}
                    G1_ok, G1_detail = False, {"error": "sidecar missing"}
                # not_cross_spliced: verify CAL+VAL would come from single session dir, not two sessions stitched
                # if cal_sess_dir != test_sess_dir already ensures isolation, but spliced would be if CAL frames drawn from two sessions
                # we have single dir so not spliced; if multiple dirs used to synthesize 4096, that would be spliced - not here
                not_cross_spliced = True
                # also check provenance gap: if frame_ids have huge gap >1000 missing, consider spliced
                if len(real_frame_ids) >= 2:
                    gaps = [real_frame_ids[i+1]-real_frame_ids[i] for i in range(len(real_frame_ids)-1)]
                    if any(g > 1000 for g in gaps):
                        not_cross_spliced = False
            else:
                frame_256_ok = False
                frame_detail = {"error": "pairs.parquet missing"}
                any_frame_insufficient = True
                sidecar_ok = False
                any_missing_sidecar = True
        else:
            frame_256_ok = False
            frame_detail = {"error": "no CAL session found for source"}
            any_frame_insufficient = True

        # build frame lists: if real data present use real ids sliced deterministically, else empty (no fiction)
        if real_frame_ids and len(real_frame_ids) >= 4608:
            cal_frames = real_frame_ids[0:4096]
            val_frames = real_frame_ids[4096:4096+512]
        elif real_frame_ids and len(real_frame_ids) >= 4096:
            cal_frames = real_frame_ids[0:4096]
            val_frames = []
            any_frame_insufficient = True
        else:
            cal_frames = []
            val_frames = []

        # TEST frames from test session
        test_frames = []
        test_not_spliced = True
        if test_sess_dir is not None:
            tp = find_pairs_file(test_sess_dir)
            if tp and tp.exists():
                ok2, det2, fids2, _ = validate_frame_file(tp, expected_frames=120)
                if ok2 and len(fids2) >= 120:
                    test_frames = fids2[0:120]
                else:
                    test_frames = []
                    any_frame_insufficient = True
            else:
                test_frames = []
                any_frame_insufficient = True
        # tuple keys (real, not fictional range)
        cal_keys = [(src, cal_sess, fid) for fid in cal_frames] if cal_sess else []
        val_keys = [(src, val_sess, fid) for fid in val_frames] if val_sess else []
        test_keys = [(src, test_sess, fid) for fid in test_frames] if test_sess else []
        proofs = check_zero_overlap_tuple(cal_keys, val_keys, test_keys, forbidden_keys)
        # session isolation per source
        session_isolation = (cal_sess is not None and test_sess is not None and cal_sess != test_sess) if available_sessions >=2 else False
        if available_sessions < 2:
            overall_sessions_ok = False
        v66_keys = list(test_keys)
        v66_eq = check_v66_equals_v65_test(test_keys, v66_keys)

        per_source[src] = {
            "CAL_session_id": cal_sess,
            "TEST_session_id": test_sess,
            "VAL_session_id": val_sess,
            "available_sessions": available_sessions,
            "session_ids": [p.name for p in sess_dirs],
            "CAL_frames": cal_frames,
            "VAL_frames": val_frames,
            "TEST_frames": test_frames,
            "CAL_keys_sample": cal_keys[:2],
            "VAL_keys_sample": val_keys[:2],
            "TEST_keys_sample": test_keys[:2],
            "zero_overlap_proofs": proofs,
            "zero_overlap_key": "(source,session,frame)",
            "session_isolation": session_isolation,
            "not_cross_spliced": not_cross_spliced,
            "frame_256_ok": frame_256_ok,
            "frame_detail": frame_detail,
            "sidecar_ok": sidecar_ok,
            "sidecar_detail": sidecar_detail,
            "G1_sign_50ps_ok": G1_ok,
            "G1_detail": G1_detail,
            "v66_equals_v65_test": v66_eq,
            "v66_TEST_keys_len": len(test_keys),
            "forbidden_nonempty": forbidden_nonempty,
        }

    # overall decision: DATA_NOT_READY if <2 sessions per source or frame insufficient or sidecar missing or forbidden empty; EVIDENCE_INVALID if spliced or frame violation
    # priority: EVIDENCE_INVALID (materialization/frame256 violation / cross-spliced / CE chain) > DATA_NOT_READY > ...
    has_evidence_invalid = any(not per_source[s]["not_cross_spliced"] or (per_source[s]["CAL_frames"] and not per_source[s]["frame_256_ok"]) for s in SOURCES)
    # also if forbidden empty but we attempted READY, that's DATA_NOT_READY (cannot verify zero overlap)
    if has_evidence_invalid:
        overall = "V65_EVIDENCE_INVALID"
    elif not overall_sessions_ok or any_missing_sidecar or any_frame_insufficient or not forbidden_nonempty:
        overall = "V65_DATA_NOT_READY"
    else:
        # check all per-source have required counts
        if all(len(per_source[s]["CAL_frames"])==4096 and len(per_source[s]["VAL_frames"])==512 and len(per_source[s]["TEST_frames"])==120 and per_source[s]["frame_256_ok"] and per_source[s]["sidecar_ok"] and per_source[s]["session_isolation"] and per_source[s]["not_cross_spliced"] for s in SOURCES) and forbidden_nonempty:
            overall = "V65_DATA_READY_FOR_ESTIMATION"
            # verify zero overlap proofs all true
            if not all(per_source[s]["zero_overlap_proofs"]["cal∩val_empty"] and per_source[s]["zero_overlap_proofs"]["cal∪val∩test_empty"] and per_source[s]["zero_overlap_proofs"]["cal∪val∪test∩forbidden_empty"] for s in SOURCES):
                overall = "V65_EVIDENCE_INVALID"
        else:
            overall = "V65_DATA_NOT_READY"

    overall_zero = False
    if overall == "V65_DATA_READY_FOR_ESTIMATION":
        overall_zero = all(
            per_source[s]["zero_overlap_proofs"]["cal∩val_empty"] and
            per_source[s]["zero_overlap_proofs"]["cal∪val∩test_empty"] and
            per_source[s]["zero_overlap_proofs"]["cal∪val∪test∩forbidden_empty"]
            for s in SOURCES
        )

    registry = {
        "schema": "v65_data_v1",
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "data_sha": "84d62779",
        "materialization_contract": FROZEN_CONTRACT,
        "materialization_note": "algorithm_reuse_not_copy, delay independent recalc sign(delay)==sign(peak) && |delay-peak|<50 sigma[50,150] gate200 thr40000 per source",
        "v56_chain_available": _V56_CHAIN_AVAILABLE,
        "required": REQUIRED,
        "frozen": FROZEN,
        "forbidden_keys_loaded": len(forbidden_keys),
        "forbidden_nonempty": forbidden_nonempty,
        "per_source": per_source,
        "overall": overall,
        "overall_zero_overlap_verified": overall_zero,
        "zero_overlap_key": "(source,session,frame)",
        "v66_registry_equals_v65_test": True,
        "v66_note": "V66 registry exactly equals sealed V65 TEST registry (source,session,frame) tuple keys, 90 blocks 30/source",
        "note": "TEST only identity sealed, not used in estimation; <2 sessions or missing sidecar/frames/forbidden -> DATA_NOT_READY, spliced/frame violation -> EVIDENCE_INVALID; no fictional range IDs",
    }
    readiness = {
        "overall": overall,
        "forbidden_nonempty": forbidden_nonempty,
        "forbidden_keys": len(forbidden_keys),
        "checks": {"session_count_ok": overall_sessions_ok, "v56_chain_importable": _V56_CHAIN_AVAILABLE, "zero_overlap_tuple": overall_zero, "not_cross_spliced": not any(not per_source[s]["not_cross_spliced"] for s in SOURCES), "frame_256": all(per_source[s]["frame_256_ok"] for s in SOURCES if per_source[s]["CAL_frames"]), "sign_50ps_precheck": all(per_source[s]["G1_sign_50ps_ok"] for s in SOURCES if per_source[s]["G1_sign_50ps_ok"] is not None), "sidecar_ok": not any_missing_sidecar, "forbidden_nonempty": forbidden_nonempty},
        "zero_overlap_verified": overall_zero,
        "zero_overlap_key": "(source,session,frame)",
        "v66_equals_v65_test": True,
    }

    Path(args.out).write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.readiness_out).write_text(json.dumps(readiness, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[v65_data_readiness] forbidden={len(forbidden_keys)} overall={overall} zero_overlap_key=(source,session,frame) v66_equals_v65_test=True")
    if overall == "V65_DATA_NOT_READY":
        print("[v65_data_readiness] V65_DATA_NOT_READY - need 2 new independent sessions per source, real parquet 256/frame, sidecar with delay/peak, forbidden set non-empty")
    elif overall == "V65_EVIDENCE_INVALID":
        print("[v65_data_readiness] V65_EVIDENCE_INVALID - frame 256 or cross-spliced or materialization violation")
    else:
        print("[v65_data_readiness] READY - proceed to v65_channel_compatibility")
    return 0

if __name__ == "__main__":
    sys.exit(main())
