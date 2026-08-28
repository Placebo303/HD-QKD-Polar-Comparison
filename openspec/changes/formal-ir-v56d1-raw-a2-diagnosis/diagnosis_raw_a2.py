"""V56D1 decoder-free raw-A2 TTBin diagnosis — V55 0/90 A2 root cause.

Zero decoder calls. Zero code params. Read-only raw TTBin + sidecar.
- Reads three original TTBin (2026.1.23 1M/2M + 2026.1.7 PPLN 1p5M) true channel IDs
- Recomputes timestamp cross-correlation (lag = t_B - t_A, 100ps / 819200ps / 16384 bins)
  outputs peak_center, peak_width (sigma/FWHM), peak_to_bg, delay_sign
- Audits nearest threshold / pairing direction / frame_start / bin origin vs V13 realtime read
- Per-source A2 judgement (3 sources) + overall 4-state, explicit contract error -> 0-overlap calibration, else Path B entropy re-est

Run:
  python diagnosis_raw_a2.py [--intake-report ...] [--v13-sidecar-root ...] [--out ...] [--recompute-corr]
Outputs diagnosis_raw_a2.json + console summary. No decoder imported.

ponytail: O(N) TTBin scan per source, chunked histogram; fallback INCOMPLETE if TimeTagger missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INTAKE_REPORT = REPO_ROOT / "comparison_bench/outputs_comparison/v55_intake_20260828/intake_report.json"
DEFAULT_V55_SIDECAR_ROOT = REPO_ROOT / "comparison_bench/outputs_comparison/v55_intake_20260828/sidecars"
DEFAULT_V13_SIDECAR_ROOT = REPO_ROOT / "workspace/v13r3fresh_20260816/sidecars"
DEFAULT_V13_MANIFEST = REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json"
DEFAULT_COUNTS = REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
DEFAULT_REGISTRY = REPO_ROOT / "openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json"

HEAD = "4914b56d8d353e7445a621fb142f340c37245f12"
DATA_SHA = "84d62779603e62de50ded5182ed65b65d3dc6084"
BRANCH = "formal-ir-mainline"
Q = 1024

# V55 three sources (labels for reporting)
V55_SOURCE_IDS = ["20260123_1M_600k_0dB", "20260107_PPLN_1p5M", "20260123_2M_1p2M_0dB"]
V55_LABELS = {"20260123_1M_600k_0dB": "1M", "20260107_PPLN_1p5M": "1p5M", "20260123_2M_1p2M_0dB": "2M"}
# Fallback provenance (same as intake_report) for when report missing
FALLBACK_TTBIN_PROVENANCE = {
    "20260123_1M_600k_0dB": [
        "D:\\Data\\Raw Data\\2026.1.23\\Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin",
        "D:\\Data\\Raw Data\\2026.1.23\\Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin",
    ],
    "20260107_PPLN_1p5M": [
        "D:\\Data\\Raw Data\\2026.1.7\\Type2PPLN_1500K_3s_2026-01-07_174222.ttbin",
        "D:\\Data\\Raw Data\\2026.1.7\\Type2PPLN_1500K_3s_2026-01-07_174222.1.ttbin",
    ],
    "20260123_2M_1p2M_0dB": [
        "D:\\Data\\Raw Data\\2026.1.23\\Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin",
        "D:\\Data\\Raw Data\\2026.1.23\\Type2_2M_1.2M_3s_0dB_2026-01-23_175008.1.ttbin",
    ],
}
V13_SIDECAR_SIDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}

CORR_BIN_WIDTH_PS = 100
CORR_MAX_LAG_PS = 819200
CORR_N_BINS = 16384  # 2*819200/100


def _read_sidecar_fields(path: Path):
    if not path.is_file():
        return None, f"missing {path}"
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"read fail {e}"
    mp = meta.get("materialize_params", {})
    used = mp.get("used_params", mp) if isinstance(mp, dict) else {}
    fields = {
        "dimension": mp.get("dimension", used.get("dimension", None)),
        "bin_width_ps": mp.get("bin_width_ps", used.get("bin_width_ps", None)),
        "pairing": mp.get("pairing", used.get("pairing_mode", mp.get("pairing_mode", None))),
        "processing_rule": mp.get("processing_rule", used.get("processing_rule_version", None)),
        "channels": mp.get("channels", used.get("channels", None)),
        "delay_used_ps": used.get("delay_used_ps", None),
        "peak_center_ps": used.get("peak_center_ps", None),
        "peak_sigma_ps": used.get("peak_sigma_ps", None),
        "corr_argmax": used.get("corr_argmax", None),
        "corr_bins": used.get("corr_bins", None),
        "corr_max": used.get("corr_max", None),
        "peak_to_bg": used.get("peak_to_bg", None),
        "peak_status": used.get("peak_status", None),
        "frame_start_ps": used.get("frame_start_ps", None),
        "frame_anchor": used.get("frame_anchor", None),
        "mapping": used.get("mapping", None),
        "wrap_rule": used.get("wrap_rule", None),
        "pairing_threshold_ps": used.get("nearest_threshold_ps", used.get("pairing_threshold_ps", None)),
        "gate_width_ps": used.get("gate_width_ps", None),
        "occupancy_filter": meta.get("occupancy_filter", used.get("occupancy_filter", None)),
        "frame_period_ps": used.get("frame_period_ps", None),
        "raw": meta,
    }
    return fields, None


def _load_intake_provenance(report_path: Path):
    out = {}
    if report_path.is_file():
        try:
            doc = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            doc = {}
        # intake_report.json shape: has no top-level dict of sources, but sidecars/* exist
        # Try parse as sidecar meta list: check if doc has "sources" or is intake_report
        # V55 intake_report is flat? Actually it's not per-source list, but we can scan sidecars
        pass
    # Fallback: use filesystem sidecars to discover sources
    for sid in V55_SOURCE_IDS:
        spec = FALLBACK_TTBIN_PROVENANCE.get(sid, [])
        # prefer reading intake_report sidecars if exists
        sidecar_path = DEFAULT_V55_SIDECAR_ROOT / sid / "sidecar_meta.json"
        if sidecar_path.is_file():
            try:
                meta = json.loads(sidecar_path.read_text(encoding="utf-8"))
                prov = meta.get("provenance", [])
                if isinstance(prov, list) and prov:
                    paths = [p.get("path") for p in prov if isinstance(p, dict) and p.get("path")]
                    if paths:
                        out[sid] = paths
                        continue
            except Exception:
                pass
        out[sid] = spec
    return out


def audit_metadata_realtime():
    """Real-time read V13 vs V55 sidecars, not hardcoded."""
    v13_rows = []
    v55_rows = []
    for src_label, sid in V13_SIDECAR_SIDS.items():
        p = DEFAULT_V13_SIDECAR_ROOT / sid / "sidecar_meta.json"
        fields, err = _read_sidecar_fields(p)
        if err:
            v13_rows.append({"source": src_label, "sid": sid, "path": str(p), "error": err, "status": {"_overall": f"INCOMPLETE missing sidecar: {err}"}})
        else:
            status = {}
            for k in ["dimension", "bin_width_ps", "pairing", "processing_rule", "channels", "delay_used_ps", "peak_center_ps", "peak_sigma_ps", "corr_argmax", "corr_bins", "corr_max", "peak_to_bg", "peak_status", "frame_start_ps", "frame_anchor", "mapping", "wrap_rule", "pairing_threshold_ps", "gate_width_ps", "occupancy_filter", "frame_period_ps"]:
                v = fields.get(k)
                status[k] = "PASS" if v is not None else "INCOMPLETE"
                if v is not None:
                    status[k + "_value"] = v
            v13_rows.append({"source": src_label, "sid": sid, "path": str(p), "fields": fields, "status": status})
    manifest_path = DEFAULT_V13_MANIFEST
    build_manifest = None
    if manifest_path.is_file():
        try:
            build_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            build_manifest = {"error": "read fail"}
    for sid in V55_SOURCE_IDS:
        label = V55_LABELS[sid]
        p = DEFAULT_V55_SIDECAR_ROOT / sid / "sidecar_meta.json"
        fields, err = _read_sidecar_fields(p)
        if err:
            v55_rows.append({"source": label, "sid": sid, "path": str(p), "error": err, "status": {"_overall": f"INCOMPLETE missing sidecar: {err}"}})
        else:
            status = {}
            for k in ["dimension", "bin_width_ps", "pairing", "processing_rule", "channels", "delay_used_ps", "peak_center_ps", "peak_sigma_ps", "corr_argmax", "corr_bins", "corr_max", "peak_to_bg", "peak_status", "frame_start_ps", "frame_anchor", "mapping", "wrap_rule", "pairing_threshold_ps", "gate_width_ps", "occupancy_filter", "frame_period_ps"]:
                v = fields.get(k)
                status[k] = "PASS" if v is not None else "INCOMPLETE"
                if v is not None:
                    status[k + "_value"] = v
            v55_rows.append({"source": label, "sid": sid, "path": str(p), "fields": fields, "status": status})
    return {"v13": v13_rows, "v55": v55_rows, "build_manifest_path": str(manifest_path), "build_manifest": build_manifest}


def _analyze_peak(hist_counts: np.ndarray, lag_centers: np.ndarray):
    """Return peak_center, peak_count, peak_width sigma/FWHM, p2bg, delay_sign."""
    if hist_counts.size == 0:
        return None
    idx = int(np.argmax(hist_counts))
    peak_center = float(lag_centers[idx])
    peak_count = int(hist_counts[idx])
    # FWHM estimation
    half = peak_count / 2.0
    # search left
    left = idx
    while left > 0 and hist_counts[left] > half:
        left -= 1
    right = idx
    while right < len(hist_counts) - 1 and hist_counts[right] > half:
        right += 1
    # interpolate roughly: FWHM = (right-left)*bin_width
    fwhm_ps = float((right - left) * CORR_BIN_WIDTH_PS) if (right > left and peak_count > 0) else float(CORR_BIN_WIDTH_PS)
    if fwhm_ps < CORR_BIN_WIDTH_PS:
        fwhm_ps = float(CORR_BIN_WIDTH_PS)
    sigma_ps = float(fwhm_ps / 2.355) if fwhm_ps > 0 else float(CORR_BIN_WIDTH_PS)
    # background: median outside 5 sigma (or 2000ps)
    excl = max(5 * sigma_ps, 2000.0)
    mask = np.abs(lag_centers - peak_center) > excl
    bg_vals = hist_counts[mask] if np.any(mask) else hist_counts
    bg_median = float(np.median(bg_vals)) if bg_vals.size else 1.0
    if bg_median < 1:
        bg_median = 1.0
    p2bg = float(peak_count / bg_median)
    delay_sign = int(np.sign(peak_center)) if peak_center != 0 else 0
    return {
        "peak_idx": idx,
        "peak_center_ps": peak_center,
        "peak_count": peak_count,
        "fwhm_ps": fwhm_ps,
        "sigma_ps": sigma_ps,
        "bg_median": bg_median,
        "peak_to_bg": p2bg,
        "delay_sign": delay_sign,
        "n_bins": int(len(hist_counts)),
        "bin_width_ps": int(CORR_BIN_WIDTH_PS),
        "max_lag_ps": int(CORR_MAX_LAG_PS),
        "lag_convention": "t_B_minus_t_A",
    }


def try_recompute_corr_for_source(ttbin_paths: list[str], ch_a=1, ch_b=5):
    """Attempt to read TTBin and recompute correlation; return channel_hist + peak or INCOMPLETE."""
    # First check files exist
    missing = [p for p in ttbin_paths if not Path(p).exists()]
    if missing:
        return None, f"INCOMPLETE_TTBin_UNAVAILABLE missing files {missing}"
    # Try import ttbin_pipeline
    try:
        from comparison_bench.src.comparison_bench.io.ttbin_pipeline import (  # type: ignore
            read_ttbin_events,
            compute_cross_correlation_histogram,
        )
    except Exception as e:
        # try alternative import path src.qkd_io
        try:
            from src.qkd_io.ttbin_pipeline import read_ttbin_events, compute_cross_correlation_histogram  # type: ignore
        except Exception as e2:
            return None, f"INCOMPLETE_TTBin_UNAVAILABLE ttbin_pipeline not importable: {e} / {e2}"
    # Need TimeTagger availability check
    try:
        import importlib.util as _ilu

        if _ilu.find_spec("TimeTagger") is None:
            return None, "INCOMPLETE_TTBin_UNAVAILABLE TimeTagger package not installed"
    except Exception:
        pass
    # Read events: .ttbin + .1.ttbin merged? FileReader auto-merge via reading main only?
    # We read main file only; FileReader merges .1.ttbin automatically if present in same dir.
    main = Path(ttbin_paths[0])
    try:
        events = read_ttbin_events(main)
    except Exception as e:
        return None, f"INCOMPLETE_TTBin_UNAVAILABLE read_ttbin_events failed: {e}"
    # channel hist
    try:
        ch = np.asarray(events.channel, dtype=np.int64)
        uniq, cnts = np.unique(ch, return_counts=True) if ch.size else (np.array([], dtype=np.int64), np.array([], dtype=np.int64))
        hist = {int(k): int(v) for k, v in zip(uniq.tolist(), cnts.tolist())}
        count_A = int(hist.get(ch_a, 0))
        count_B = int(hist.get(ch_b, 0))
        other = int(ch.size - count_A - count_B)
        frac_A = float(count_A / ch.size) if ch.size else 0.0
        frac_B = float(count_B / ch.size) if ch.size else 0.0
        frac_other = float(other / ch.size) if ch.size else 0.0
        try:
            tps = np.asarray(events.time_ps, dtype=np.int64)
            if tps.size:
                tmin = int(np.min(tps))
                tmax = int(np.max(tps))
                acq_s = float(max(0, tmax - tmin)) * 1e-12
            else:
                tmin = 0
                tmax = 0
                acq_s = 0.0
        except Exception:
            tmin = 0
            tmax = 0
            acq_s = 0.0
        chunk_path = Path(ttbin_paths[1]) if len(ttbin_paths) > 1 else None
        main_size = int(Path(ttbin_paths[0]).stat().st_size) if Path(ttbin_paths[0]).exists() else None
        chunk_size = int(chunk_path.stat().st_size) if chunk_path is not None and chunk_path.exists() else None
        chunk_exists = bool(chunk_path is not None and chunk_path.exists() and chunk_size is not None and chunk_size > 0)
        merge_verified = bool(chunk_exists and int(ch.size) > 50000)
        channel_result = {
            "unique_channels": sorted(hist.keys()),
            "hist": hist,
            "count_A": count_A,
            "count_B": count_B,
            "other": other,
            "total_events": int(ch.size),
            "frac_A": frac_A,
            "frac_B": frac_B,
            "frac_other": frac_other,
            "chan_A": ch_a,
            "chan_B": ch_b,
            "acquisition_duration_s": acq_s,
            "timetag_min_ps": tmin,
            "timetag_max_ps": tmax,
            "ttbin_merge": {
                "main_path": str(ttbin_paths[0]),
                "chunk_path": str(chunk_path) if chunk_path is not None else None,
                "main_size": main_size,
                "chunk_size": chunk_size,
                "chunk_exists": chunk_exists,
                "total_events_after_load": int(ch.size),
                "acquisition_duration_s": acq_s,
                "merge_verified": merge_verified,
                "note": "FileReader auto-merge .1.ttbin when reading main; merge_verified requires chunk_exists and total_events>50000; compare with intake sidecar diagnostics counts",
            },
        }
    except Exception as e:
        return None, f"INCOMPLETE channel hist failed: {e}"
    # correlation
    try:
        corr = compute_cross_correlation_histogram(
            events=events, ch_a=ch_a, ch_b=ch_b, bin_width_ps=CORR_BIN_WIDTH_PS, max_lag_ps=CORR_MAX_LAG_PS
        )
        counts = np.asarray(corr["counts"], dtype=np.int64)
        centers = np.asarray(corr["lag_center_ps"], dtype=np.float64)
        peak = _analyze_peak(counts, centers)
        if peak is None:
            return {"channel": channel_result, "corr": corr, "peak": None}, "peak analyze empty"
        # augment summary
        summary = corr.get("summary", {})
        return {
            "channel": channel_result,
            "corr": {"counts": counts.tolist()[:5], "counts_len": int(len(counts)), "summary": summary},  # trim for json size
            "peak": peak,
            "full_summary": summary,
        }, None
    except Exception as e:
        return {"channel": channel_result, "corr": None, "peak": None}, f"corr failed: {e}"


def main():
    ap = argparse.ArgumentParser(description="V56D1 decoder-free raw-A2 diagnosis")
    ap.add_argument("--intake-report", type=str, default=str(DEFAULT_INTAKE_REPORT), help="v55_intake_20260828/intake_report.json")
    ap.add_argument("--v13-sidecar-root", type=str, default=str(DEFAULT_V13_SIDECAR_ROOT))
    ap.add_argument("--v55-sidecar-root", type=str, default=str(DEFAULT_V55_SIDECAR_ROOT))
    ap.add_argument("--counts", type=str, default=str(DEFAULT_COUNTS))
    ap.add_argument("--registry", type=str, default=str(DEFAULT_REGISTRY))
    ap.add_argument("--out", type=str, default=str(Path(__file__).parent / "diagnosis_raw_a2.json"))
    ap.add_argument("--recompute-corr", action="store_true", default=True, help="recompute cross-correlation (default true if TimeTagger available)")
    ap.add_argument("--no-recompute-corr", dest="recompute_corr", action="store_false")
    args = ap.parse_args()

    print(f"=== V56D1 raw-A2 decoder-free diagnosis HEAD={HEAD} branch={BRANCH} data_sha={DATA_SHA} ===")
    print(f"intake_report: {args.intake_report}")
    print(f"v13 sidecar root: {args.v13_sidecar_root}")
    print(f"v55 sidecar root: {args.v55_sidecar_root}")
    print(f"recompute_corr: {args.recompute_corr}")

    # check counts (only for background, not required)
    counts_path = Path(args.counts)
    if counts_path.is_file():
        print(f"counts: {counts_path} exists (background only)")
    else:
        print(f"[WARN] counts missing {counts_path} -> NLL background unavailable, but not required for A2")

    audit = audit_metadata_realtime()
    print("\n-- Metadata audit realtime (V13 actual sidecars vs V55) --")
    for row in audit["v13"]:
        s = row.get("status", {})
        # compact print delay/peak
        d = s.get("delay_used_ps", "INCOMPLETE")
        pc = s.get("peak_center_ps", "INCOMPLETE")
        print(f"  V13 {row['source']}: delay {d} peak_center {pc} corr {s.get('corr_argmax','INCOMPLETE')}")
    for row in audit["v55"]:
        s = row.get("status", {})
        print(f"  V55 {row['source']}: channels {s.get('channels','INCOMPLETE')} delay {s.get('delay_used_ps','INCOMPLETE')} peak {s.get('peak_center_ps','INCOMPLETE')}")

    # provenance
    prov = _load_intake_provenance(Path(args.intake_report))
    print("\n-- TTBin provenance --")
    for sid in V55_SOURCE_IDS:
        print(f"  {V55_LABELS[sid]} {sid}: {prov.get(sid)}")

    per_source = {}
    per_source_decisions = {}
    shunt_evidence = {}
    corr_results = {}

    # Also need parquet-derived still_low background (from V56D0) for B decision: we can attempt to load parquet A==B rates if available, else skip
    # Try load parquet quickly for still_low check
    parquet_rates = {}
    for sid in V55_SOURCE_IDS:
        label = V55_LABELS[sid]
        parquet_path = REPO_ROOT / f"comparison_bench/outputs_comparison/v55_intake_20260828/pairs/{sid}/pairs.parquet"
        if parquet_path.is_file():
            try:
                import pandas as pd

                df = pd.read_parquet(parquet_path, columns=["alice_symbol", "bob_symbol"])
                a = df["alice_symbol"].to_numpy(dtype=np.int64)
                b = df["bob_symbol"].to_numpy(dtype=np.int64)
                rate = float(np.mean(a == b)) if len(a) else 0.0
                parquet_rates[label] = rate
            except Exception:
                parquet_rates[label] = None
        else:
            parquet_rates[label] = None
    print(f"\n-- Parquet background rates (for B) {parquet_rates} --")

    for sid in V55_SOURCE_IDS:
        label = V55_LABELS[sid]
        print(f"\n-- Source {label} ({sid}) --")
        ttbins = prov.get(sid, FALLBACK_TTBIN_PROVENANCE.get(sid, []))
        channel_res = None
        peak = None
        corr_err = None
        if args.recompute_corr:
            res, err = try_recompute_corr_for_source(ttbins, ch_a=1, ch_b=5)
            if err and res is None:
                print(f"  corr {label}: {err}")
                corr_err = err
                per_source[label] = {"ttbin_paths": ttbins, "error": err, "channel": None, "peak": None}
            else:
                if res is not None:
                    channel_res = res.get("channel")
                    peak = res.get("peak")
                    corr_results[label] = res
                    print(f"  channel {label}: unique {channel_res.get('unique_channels')} count_A={channel_res.get('count_A')} frac_A={channel_res.get('frac_A'):.3f} count_B={channel_res.get('count_B')} frac_B={channel_res.get('frac_B'):.3f} other_frac={channel_res.get('frac_other'):.3f}")
                    if peak:
                        print(f"  peak {label}: center {peak['peak_center_ps']:.1f}ps sigma {peak['sigma_ps']:.1f}ps fwhm {peak['fwhm_ps']:.1f}ps p2bg {peak['peak_to_bg']:.1f} delay_sign {peak['delay_sign']} total_pairs {res.get('full_summary',{}).get('total_pairs_in_window')}")
                    if err:
                        print(f"  corr warn {err}")
                per_source[label] = {"ttbin_paths": ttbins, "channel": channel_res, "peak": peak, "error": err, "full": res}
        else:
            print(f"  corr skipped for {label}")
            per_source[label] = {"ttbin_paths": ttbins, "channel": None, "peak": None, "error": "skipped"}

        # Contract field checks vs V13 realtime
        v13_row = next((r for r in audit["v13"] if r["source"] == label), None)
        v55_row = next((r for r in audit["v55"] if r["source"] == label), None)
        contract_row = {}
        # Helper to get V13 value
        def v13_val(field):
            if v13_row and "fields" in v13_row:
                return v13_row["fields"].get(field)
            return None

        def v55_val(field):
            if v55_row and "fields" in v55_row:
                return v55_row["fields"].get(field)
            return None

        # delay/peak comparison
        delay_v13 = v13_val("delay_used_ps")
        peak_v13 = v13_val("peak_center_ps")
        sigma_v13 = v13_val("peak_sigma_ps")
        p2bg_v13 = v13_val("peak_to_bg")
        corr_argmax_v13 = v13_val("corr_argmax")
        thr_v13 = v13_val("pairing_threshold_ps")
        gate_v13 = v13_val("gate_width_ps")

        delay_v55_decl = v55_val("delay_used_ps")
        peak_v55_decl = v55_val("peak_center_ps")
        sigma_v55_decl = v55_val("peak_sigma_ps")
        thr_v55_decl = v55_val("pairing_threshold_ps")
        gate_v55_decl = v55_val("gate_width_ps")
        frame_start_v55 = v55_val("frame_start_ps")
        mapping_v55 = v55_val("mapping")

        # Determine contract status per field
        contract_status = {}
        for fld, v13v, v55v in [
            ("delay_used_ps", delay_v13, delay_v55_decl),
            ("peak_center_ps", peak_v13, peak_v55_decl),
            ("peak_sigma_ps", sigma_v13, sigma_v55_decl),
            ("corr_argmax", corr_argmax_v13, v55_val("corr_argmax")),
            ("peak_to_bg", p2bg_v13, v55_val("peak_to_bg")),
            ("pairing_threshold_ps", thr_v13, thr_v55_decl),
            ("gate_width_ps", gate_v13, gate_v55_decl),
            ("frame_start_ps", v13_val("frame_start_ps"), frame_start_v55),
            ("mapping", v13_val("mapping"), mapping_v55),
        ]:
            if v55v is None:
                contract_status[fld] = "INCOMPLETE"
            elif v13v is not None and v55v != v13v:
                # For delay/peak, allow 50ps tolerance? But strict MISMATCH if not equal
                contract_status[fld] = "MISMATCH" if fld in ("delay_used_ps", "peak_center_ps", "corr_argmax") else "MISMATCH"
            else:
                contract_status[fld] = "PASS"
        # Special handling: if V55 sidecar missing delay/peak, INCOMPLETE is already, raw peak takes over
        # Compare raw peak vs declared delay
        raw_center = peak["peak_center_ps"] if peak else None
        raw_sigma = peak["sigma_ps"] if peak else None
        raw_p2bg = peak["peak_to_bg"] if peak else None
        explicit_error = False
        explicit_reasons = []
        healthy = False
        # channel mismatch
        if channel_res:
            if channel_res["frac_A"] < 0.40 or channel_res["frac_B"] < 0.40:
                explicit_error = True
                explicit_reasons.append(f"channel_mismatch frac_A {channel_res['frac_A']:.3f} frac_B {channel_res['frac_B']:.3f} <0.40")
            if channel_res["frac_other"] > 0.20:
                explicit_error = True
                explicit_reasons.append(f"other_channels {channel_res['frac_other']:.3f} >0.20")

        # default timing contract (separate gate) - must be recovered and matched before B
            if corr_err and "INCOMPLETE_TTBin_UNAVAILABLE" in corr_err:
                decision = "INCONCLUSIVE_NEED_CALIBRATION"
                rationale = f"TTBin unavailable: {corr_err}"
            else:
                explicit_error = True
                explicit_reasons.append("peak_missing p2bg<10 or no peak")
                decision = "PATH_A2_RAW_CONTRACT_ERROR"
                rationale = "; ".join(explicit_reasons)
        else:
            # Check raw peak health vs declared delay
            if raw_p2bg is not None and raw_p2bg < 10:
                explicit_error = True
                explicit_reasons.append(f"peak_missing p2bg {raw_p2bg:.1f} <10")
            if raw_sigma is not None and raw_sigma > 150:
                explicit_error = True
                explicit_reasons.append(f"broad_peak sigma {raw_sigma:.1f} >150ps")
            if delay_v55_decl is not None and raw_center is not None:
                if abs(raw_center - delay_v55_decl) > 50:
                    explicit_error = True
                    explicit_reasons.append(f"|peak_center {raw_center:.1f} - delay_used {delay_v55_decl}| >50ps")
            # threshold mismatch
            if thr_v55_decl is not None and thr_v55_decl != 40000:
                explicit_error = True
                explicit_reasons.append(f"nearest_threshold {thr_v55_decl} != 40000")
            # sign mismatch is explicit A2 when delay known
            if delay_v55_decl is not None and raw_center is not None:
                if int(np.sign(raw_center)) != int(np.sign(delay_v55_decl)) and raw_center != 0 and delay_v55_decl != 0:
                    explicit_error = True
                    explicit_reasons.append(f"delay_sign mismatch raw {int(np.sign(raw_center))} vs declared {int(np.sign(delay_v55_decl))}")
            # frame_start/wrap_rule missing is INCOMPLETE, not explicit error unless raw peak offset clearly indicates
            # timing_contract_verified: separate gate, only when V55 delay/pairing recovered and matches raw peak
            timing_contract_verified = False
            timing_contract_reasons = []
            if peak is not None and delay_v55_decl is not None and raw_center is not None:
                sign_match = int(np.sign(raw_center)) == int(np.sign(delay_v55_decl)) or raw_center == 0 or delay_v55_decl == 0
                numeric_match = abs(raw_center - delay_v55_decl) < 50
                pairing_ok = (thr_v55_decl is None) or (thr_v55_decl == 40000)
                if not sign_match:
                    timing_contract_reasons.append(f"delay_sign mismatch raw {int(np.sign(raw_center))} vs declared {int(np.sign(delay_v55_decl))}")
                if not numeric_match:
                    timing_contract_reasons.append(f"|peak {raw_center:.1f} - delay {delay_v55_decl}| >=50ps")
                if not pairing_ok:
                    timing_contract_reasons.append(f"pairing threshold {thr_v55_decl} !=40000")
                timing_contract_verified = bool(sign_match and numeric_match and pairing_ok)
                if not timing_contract_verified:
                    timing_contract_reasons.append("timing_contract not verified")
            else:
                timing_contract_reasons.append("delay_used or peak unavailable -> timing_contract INCOMPLETE")
                timing_contract_verified = False
            # Check healthy (peak shape only, no delay gating)
            peak_shape_healthy = bool(raw_center is not None and raw_sigma is not None and raw_p2bg is not None and 50 <= raw_sigma <= 150 and raw_p2bg > 1000)
            if peak_shape_healthy:
                healthy = True

            # Decision
            if explicit_error:
                decision = "PATH_A2_RAW_CONTRACT_ERROR"
                rationale = "; ".join(explicit_reasons)
            elif peak_shape_healthy:
                still_low = False
                rate = parquet_rates.get(label)
                if rate is not None and rate < 0.45:
                    still_low = True
                if still_low:
                    if timing_contract_verified:
                        decision = "PATH_B_DOMAIN_SHIFT"
                        rationale = f"raw peak healthy center {raw_center:.1f} σ {raw_sigma:.1f} p2bg {raw_p2bg:.1f} timing_contract_verified (delay {delay_v55_decl} matched) but A==B {rate:.3f} <0.45 still low -> domain shift"
                    else:
                        decision = "INCONCLUSIVE_A2_NOT_EXCLUDED"
                        rationale = f"raw peak healthy center {raw_center:.1f} σ {raw_sigma:.1f} p2bg {raw_p2bg:.1f} but timing_contract not verified ({'; '.join(timing_contract_reasons)}); A==B {rate} low -> cannot enter Path B, A2 not excluded"
                else:
                    decision = "INCONCLUSIVE"
                    rationale = f"raw peak healthy but rate {rate} not low enough to confirm B; timing_verified={timing_contract_verified}"
            else:
                incomplete_fields = [k for k, v in contract_status.items() if v == "INCOMPLETE"]
                if incomplete_fields:
                    decision = "INCONCLUSIVE_METADATA_INCOMPLETE"
                    rationale = f"raw peak incomplete or unhealthy but not explicit error; missing {incomplete_fields} without sufficient error evidence"
                else:
                    decision = "INCONCLUSIVE"
                    rationale = "insufficient evidence for A2/B"

            if corr_err and "INCOMPLETE_TTBin_UNAVAILABLE" in corr_err:
                decision = "INCONCLUSIVE_NEED_CALIBRATION"
                rationale = f"TTBin unavailable after attempt: {corr_err}"

        merge_info = channel_res.get("ttbin_merge") if channel_res else None
        merge_verified = bool(merge_info and merge_info.get("merge_verified")) if merge_info else False
        if channel_res and not merge_verified and not corr_err:
            if channel_res.get("total_events", 0) < 50000:
                rationale += f" [WARN ttbin_merge not verified: total_events {channel_res.get('total_events')} <50000, possible silent miss of .1.ttbin; chunk {merge_info.get('chunk_size') if merge_info else 'n/a'}]"
        per_source_decisions[label] = decision
        shunt_evidence[label] = {
            "channel": channel_res,
            "peak": peak,
            "contract_status": contract_status,
            "parquet_rate": parquet_rates.get(label),
            "explicit_reasons": explicit_reasons,
            "healthy": healthy,
            "timing_contract_verified": timing_contract_verified,
            "timing_contract_reasons": timing_contract_reasons,
            "delay_declared_ps": delay_v55_decl,
            "thr_declared_ps": thr_v55_decl,
            "ttbin_merge": merge_info,
            "ttbin_merge_verified": merge_verified,
            "per_source_decision": decision,
            "per_source_rationale": rationale,
            "corr_error": corr_err,
            "note": "lag = t_B - t_A, bin 100ps max_lag 819200 n_bins 16384; timing_contract_verified separate from peak healthy; A2 not excluded unless verified; 0-overlap calibration required if A2",
        }

    # overall
    decisions = list(per_source_decisions.values())
    if not decisions:
        overall = "INCONCLUSIVE"
        rationale = "no per-source data"
        next_step = "acquire TTBin or fallback to sidecar audit, then 8-16 frames calibration"
    elif all("INCOMPLETE_TTBin_UNAVAILABLE" in (per_source[k].get("error") or "") for k in per_source):
        overall = "INCONCLUSIVE"
        rationale = "All 3 sources TTBin unavailable -> INCONCLUSIVE, fallback to sidecar metadata_incomplete, need actual raw peak"
        next_step = "ensure TimeTagger installed and TTBin files accessible, then rerun diagnosis_raw_a2"
    elif all(d == "PATH_A2_RAW_CONTRACT_ERROR" for d in decisions):
        overall = "PATH_A2_ALL"
        rationale = f"All 3 sources PATH_A2: {per_source_decisions}"
        next_step = "fix sidecar contract (channels/delay/peak/frame_start/mapping explicit) + FileReader explicit binding + G1'-G3' gates; original 90 remains unblinded forbidden to rerun; then calibrate with independent frames (0 overlap with 90) verify A==B>60% p2bg>1000"
    elif all(d == "PATH_B_DOMAIN_SHIFT" for d in decisions):
        overall = "PATH_B_ALL"
        rationale = f"All 3 sources PATH_B (raw peak healthy but A==B 27-41%): {per_source_decisions}"
        next_step = "re-estimate H(U1|B), H(U2|U1,B) from new intake N_ab, recompute source-adaptive m_total/f (1.3*n*H-64)/5, redesign if needed; calibrate with independent frames first"
    elif any(d == "INCONCLUSIVE_A2_NOT_EXCLUDED" for d in decisions):
        if all(d == "INCONCLUSIVE_A2_NOT_EXCLUDED" for d in decisions):
            overall = "INCONCLUSIVE"
            rationale = f"All 3 INCONCLUSIVE_A2_NOT_EXCLUDED (peak healthy but timing untraceable, cannot enter B): {per_source_decisions}"
            next_step = "recover V55 actually used delay/pairing params and verify |peak-delay|<50 + sign match before Path B; then calibrate"
        else:
            overall = "MIXED_BY_SOURCE"
            rationale = f"mixed with INCONCLUSIVE_A2_NOT_EXCLUDED: {per_source_decisions} -> A2 not excluded for healthy-peak sources"
            next_step = "handle per-source: A2 sources fix contract, A2_NOT_EXCLUDED sources recover timing contract, then 0-overlap calibration"
    elif any(d == "INCONCLUSIVE_METADATA_INCOMPLETE" for d in decisions) and len(set(decisions)) == 1:
        overall = "INCONCLUSIVE"
        rationale = "per-source INCONCLUSIVE due to missing raw contract fields without explicit error"
        next_step = "retrieve actual raw metrics before Path A2, then calibrate"
    elif len(set(decisions)) == 1:
        sole = decisions[0]
        if sole == "PATH_A2_RAW_CONTRACT_ERROR":
            overall = "PATH_A2_ALL"
            rationale = f"All 3 Path A2: {per_source_decisions}"
            next_step = "fix contract then 0-overlap calibration"
        elif sole == "PATH_B_DOMAIN_SHIFT":
            overall = "PATH_B_ALL"
            rationale = f"All 3 Path B: {per_source_decisions}"
            next_step = "entropy re-estimation then calibration"
        else:
            overall = "INCONCLUSIVE"
            rationale = f"All 3 {sole}: {per_source_decisions}"
            next_step = "acquire 8-16 frames per source calibration, verify rate>60% p2bg>1000"
    else:
        overall = "MIXED_BY_SOURCE"
        rationale = f"per-source decisions differ: {per_source_decisions} -> MIXED_BY_SOURCE"
        next_step = "handle per-source: A2 sources fix contract, B sources re-estimate entropy; calibrate independently with 0 overlap"

    # avg rate
    valid_rates = [v for v in parquet_rates.values() if v is not None]
    avg_rate = float(np.mean(valid_rates)) if valid_rates else 0.0

    overall_doc = {
        "head": HEAD,
        "branch": BRANCH,
        "data_sha": DATA_SHA,
        "metadata_audit": audit,
        "per_source": per_source,
        "shunt_evidence": shunt_evidence,
        "per_source_decisions": per_source_decisions,
        "overall_shunt": overall,
        "rationale": rationale,
        "next_step": next_step,
        "avg_rate_v55_parquet": avg_rate,
        "parquet_rates": parquet_rates,
        "corr_params": {"bin_width_ps": CORR_BIN_WIDTH_PS, "max_lag_ps": CORR_MAX_LAG_PS, "n_bins": CORR_N_BINS, "lag_convention": "t_B_minus_t_A", "channels": {"A": 1, "B": 5}},
        "domain_split": "A2=raw TTBin delay/peak/pairing contract (needs actual raw evidence), B=physical domain shift after excluding A2, A1 already excluded by V56D0 k*=0",
        "forbidden": [
            "DO NOT rerun corrected pipeline on original 90 blocks (already unblinded)",
            "DO NOT tune H1/Lane C/Δ8/decoder 90/1.0",
            "DO NOT claim LDPC falsification",
            "MUST use independent calibration frames (0 overlap with 90) before freezing new blocks",
            "Missing metadata alone -> INCONCLUSIVE, not auto Path A2",
            "Zero decoder, zero code params",
        ],
        "notes": "decoder-free only; lag=t_B-t_A; peak width σ≈FWHM/2.355; p2bg=peak/bg_median; healthy p2bg>1000 σ 50-150ps; V56D0 A1 excluded k*=0",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # json dump with handling of numpy types
    def _convert(o):
        if isinstance(o, (np.integer, np.floating)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(overall_doc, f, indent=2, ensure_ascii=False, default=_convert)
    print(f"\n=== Overall shunt: {overall} ===")
    print(f"per_source: {per_source_decisions}")
    print(f"rationale: {rationale}")
    print(f"next: {next_step}")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
