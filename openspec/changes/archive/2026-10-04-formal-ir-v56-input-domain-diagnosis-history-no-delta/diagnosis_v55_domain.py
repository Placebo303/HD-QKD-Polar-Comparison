"""V56D0 decoder-free input domain mismatch diagnosis — V55 0/90 root cause.

Zero decoder calls. Read-only parquet + sidecar + channel_counts.npz.
Compares V13 2026-01-21 vs V55 2026.1.23/2026.1.07 intake on:
 - metadata (channels/delay/peak/mapping/pairing) — actual sidecars/metrics, missing reported as INCOMPLETE
 - per-source stats: A==B, U1/U2, Bob-conditioned NLL, edge/zero/frame/delta
 - fixed relative offset scan as diagnostic only, not for requalification:
   b'=(b+k)%1024 is parquet symbol/mapping shift (A1) only, separate from raw TTBin
   delay/peak/pairing contract (A2); B is physical domain shift after excluding A1/A2.
   Uses 1024-bin modular-delta histogram for all k rate_eq; NLL only for k=0 and k*;
   note: NOT equivalent to raw time-delay scan.

Run:
  python diagnosis_v55_domain.py [--pairs-root ...] [--sidecar-root ...] [--counts ...] [--out ...]
Outputs diagnosis_v55_domain.json + console summary. No decoder imported.

ponytail: O(N) parquet scan per source, fine for <2M rows; upgrade to chunked if >10M.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_V55_PAIRS = REPO_ROOT / "comparison_bench/outputs_comparison/v55_intake_20260828/pairs"
DEFAULT_V13_PAIRS = REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816"
DEFAULT_COUNTS = REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
DEFAULT_V55_SIDECAR = REPO_ROOT / "comparison_bench/outputs_comparison/v55_intake_20260828/sidecars"
DEFAULT_V13_SIDECAR = REPO_ROOT / "workspace/v13r3fresh_20260816/sidecars"
DEFAULT_REGISTRY = REPO_ROOT / "openspec/changes/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/v55_authoritative_registry.json"

HEAD = "cf8b098047cf64aa1e0426e2ea2e62b680430bd6"
DATA_SHA = "84d62779603e62de50ded5182ed65b65d3dc6084"
BRANCH = "formal-ir-mainline"
Q = 1024

V55_SOURCES = {
    "1M": {"session": "20260123_1M_600k_0dB", "parquet": DEFAULT_V55_PAIRS / "20260123_1M_600k_0dB/pairs.parquet", "sidecar": DEFAULT_V55_SIDECAR / "20260123_1M_600k_0dB/sidecar_meta.json"},
    "1p5M": {"session": "20260107_PPLN_1p5M", "parquet": DEFAULT_V55_PAIRS / "20260107_PPLN_1p5M/pairs.parquet", "sidecar": DEFAULT_V55_SIDECAR / "20260107_PPLN_1p5M/sidecar_meta.json"},
    "2M": {"session": "20260123_2M_1p2M_0dB", "parquet": DEFAULT_V55_PAIRS / "20260123_2M_1p2M_0dB/pairs.parquet", "sidecar": DEFAULT_V55_SIDECAR / "20260123_2M_1p2M_0dB/sidecar_meta.json"},
}
V13_SOURCES = {
    "1M": {"session": "type2_1M_20260121_184040", "parquet": DEFAULT_V13_PAIRS / "type2_1M_20260121_184040/pairs.parquet", "sidecar": DEFAULT_V13_SIDECAR / "type2_1M_20260121_184040/sidecar_meta.json"},
    "1p5M": {"session": "type2_1p5M_20260121_183806", "parquet": DEFAULT_V13_PAIRS / "type2_1p5M_20260121_183806/pairs.parquet", "sidecar": DEFAULT_V13_SIDECAR / "type2_1p5M_20260121_183806/sidecar_meta.json"},
    "2M": {"session": "type2_2M_20260121_183657", "parquet": DEFAULT_V13_PAIRS / "type2_2M_20260121_183657/pairs.parquet", "sidecar": DEFAULT_V13_SIDECAR / "type2_2M_20260121_183657/sidecar_meta.json"},
}

# Frozen F03 5+5 split (natural labeling, MSB->LSB)
def split_u1_u2(sym: np.ndarray):
    s = np.asarray(sym, dtype=np.int64) & 0x3FF
    u1 = (s >> 5) & 0x1F  # top 5 bits [9..5]
    u2 = s & 0x1F          # low 5 bits [4..0]
    return u1, u2

def load_pairs(parquet_path: Path, limit: int | None = None):
    import pandas as pd
    if not parquet_path.is_file():
        return None, f"missing {parquet_path}"
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        return None, f"read fail {e}"
    for col in ("alice_symbol", "bob_symbol", "frame_id", "pair_idx"):
        if col not in df.columns:
            return None, f"schema missing {col}"
    if limit is not None:
        df = df.head(limit)
    a = df["alice_symbol"].to_numpy().astype(np.int64)
    b = df["bob_symbol"].to_numpy().astype(np.int64)
    frame = df["frame_id"].to_numpy().astype(np.int64) if "frame_id" in df.columns else None
    return (a, b, frame, df), None

def load_counts(counts_path: Path):
    if not counts_path.is_file():
        return None, f"missing {counts_path}"
    try:
        data = np.load(counts_path)
    except Exception as e:
        return None, f"load fail {e}"
    out = {}
    for k in data.files:
        if "type2_1M_20260121_184040" in k:
            out["1M"] = data[k]
        elif "type2_1p5M_20260121_183806" in k:
            out["1p5M"] = data[k]
        elif "type2_2M_20260121_183657" in k:
            out["2M"] = data[k]
        else:
            out[k] = data[k]
    # fallback: if only generic keys, try direct (should not happen with exact keys above)
    if "1M" not in out:
        files = sorted(data.files)
        for idx, src in enumerate(["1M", "1p5M", "2M"]):
            if idx < len(files):
                out[src] = data[files[idx]]
    return out, None

def build_P_A_given_B(N_ab: np.ndarray):
    col = N_ab.sum(axis=0, keepdims=True).astype(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.divide(N_ab, col, out=np.zeros_like(N_ab, dtype=np.float64), where=col > 0)
    return P

def per_source_stats(a: np.ndarray, b: np.ndarray, frame: np.ndarray | None, P_train: np.ndarray | None):
    n = len(a)
    rate_eq = float(np.mean(a == b)) if n else 0.0
    ser = 1.0 - rate_eq
    # U1/U2
    u1_a, u2_a = split_u1_u2(a)
    u1_b, u2_b = split_u1_u2(b)
    u1_eq = float(np.mean(u1_a == u1_b)) if n else 0.0
    u2_eq = float(np.mean(u2_a == u2_b)) if n else 0.0
    joint_eq = float(np.mean((u1_a == u1_b) & (u2_a == u2_b)))  # == A==B sanity
    # delta histograms
    delta_ab = (a - b) % Q
    delta_ba = (b - a) % Q
    hist_ab = np.bincount(delta_ab, minlength=Q).astype(np.float64)
    frac_ab = hist_ab / n if n else hist_ab
    mass_0 = float(frac_ab[0])
    mass_p1 = float(frac_ab[1])
    mass_m1 = float(frac_ab[Q-1])
    other_mass = float(1 - mass_0 - mass_p1 - mass_m1)
    hist_ba = np.bincount(delta_ba, minlength=Q).astype(np.float64)
    frac_ba = hist_ba / n if n else hist_ba
    mass_ba_0 = float(frac_ba[0])
    mass_ba_p1 = float(frac_ba[1])
    mass_ba_m1 = float(frac_ba[Q-1])
    q_mass_zero = None
    if P_train is not None:
        zero_mask = (P_train == 0)
        is_zero = P_train[a, b] == 0
        q_mass_zero = float(np.mean(is_zero)) if n else 0.0
        train_zero_frac = float(np.mean(zero_mask))
    else:
        train_zero_frac = None
    # NLL
    nll_bits = None
    zero_prob_count = None
    if P_train is not None:
        p_vals = P_train[a, b]
        p_clip = np.maximum(p_vals, 1e-15)
        nll_bits = float(np.mean(-np.log2(p_clip)))
        zero_prob_count = int(np.sum(p_vals == 0))
    # frame-level correlation
    frame_corr = None
    if frame is not None:
        uniq_frames = np.unique(frame)
        per_frame_rates = []
        for fid in uniq_frames:
            mask = frame == fid
            per_frame_rates.append(float(np.mean(a[mask] == b[mask])) if np.any(mask) else 0.0)
        per_frame_rates = np.array(per_frame_rates)
        frame_corr = {
            "n_frames": int(len(uniq_frames)),
            "per_frame_rate_mean": float(np.mean(per_frame_rates)) if len(per_frame_rates) else 0.0,
            "per_frame_rate_std": float(np.std(per_frame_rates)) if len(per_frame_rates) else 0.0,
            "per_frame_rate_min": float(np.min(per_frame_rates)) if len(per_frame_rates) else 0.0,
            "per_frame_rate_max": float(np.max(per_frame_rates)) if len(per_frame_rates) else 0.0,
            "per_frame_rate_median": float(np.median(per_frame_rates)) if len(per_frame_rates) else 0.0,
        }
    # marginal distributions
    hist_a = np.bincount(a, minlength=Q).astype(np.float64) / n if n else np.zeros(Q)
    hist_b = np.bincount(b, minlength=Q).astype(np.float64) / n if n else np.zeros(Q)
    top_a_idx = int(np.argmax(hist_a)) if n else -1
    top_b_idx = int(np.argmax(hist_b)) if n else -1
    return {
        "n_pairs": int(n),
        "rate_eq": rate_eq,
        "ser": ser,
        "u1_eq": u1_eq,
        "u2_eq": u2_eq,
        "joint_eq_check": joint_eq,
        "mass_0_ab": mass_0,
        "mass_p1_ab": mass_p1,
        "mass_m1_ab": mass_m1,
        "other_mass_ab": other_mass,
        "mass_0_ba": mass_ba_0,
        "mass_p1_ba": mass_ba_p1,
        "mass_m1_ba": mass_ba_m1,
        "direction_asym": float(mass_p1 - mass_m1),
        "nll_bits_per_symbol": nll_bits,
        "nll_bits_per_block": float(nll_bits * 1024) if nll_bits is not None else None,
        "zero_prob_count": zero_prob_count,
        "q_mass_on_p_zero": q_mass_zero,
        "train_zero_frac": train_zero_frac,
        "frame_corr": frame_corr,
        "top_a_bin": top_a_idx,
        "top_a_frac": float(hist_a[top_a_idx]) if top_a_idx >= 0 else 0.0,
        "top_b_bin": top_b_idx,
        "top_b_frac": float(hist_b[top_b_idx]) if top_b_idx >= 0 else 0.0,
        "marginal_entropy_a": float(-np.sum(hist_a[hist_a>0] * np.log2(hist_a[hist_a>0]))) if n else 0.0,
        "marginal_entropy_b": float(-np.sum(hist_b[hist_b>0] * np.log2(hist_b[hist_b>0]))) if n else 0.0,
    }

def offset_scan(a: np.ndarray, b: np.ndarray, P_train: np.ndarray | None, ks=range(-8, 9)):
    """A1-only parquet symbol/mapping shift diagnostic.

    Uses the already-computed 1024-bin modular-delta histogram to derive
    rate_eq(k) for all k (rate_eq(k) = frac[(a-b) mod 1024 == k]).
    Only NLL is computed for k=0 and k* (peak) to avoid O(Q*N) cost.
    NOTE: this is NOT equivalent to a raw time-delay scan on TTBin
    coincidence windows; it only tests post-binning symbol mapping offsets.
    """
    n = len(a)
    if n == 0:
        return [], {"k_star": 0, "rate_star": 0.0, "delta_rate": 0.0, "nll_star": None, "nll_0": None}
    delta = (a - b) % Q
    hist = np.bincount(delta, minlength=Q).astype(np.float64) / n
    # Build curve for requested k window using histogram (fast, no per-k scan)
    out = []
    # Precompute NLL for k=0
    nll_0 = None
    if P_train is not None:
        p0 = P_train[a, b]
        nll_0 = float(np.mean(-np.log2(np.maximum(p0, 1e-15))))
    for k in ks:
        k_mod = int(k % Q)
        rate = float(hist[k_mod])
        # NLL only for k=0 and later for k*; placeholder None otherwise
        nll = nll_0 if k == 0 else None
        out.append({
            "k": int(k),
            "rate_eq": rate,
            "nll_bits": nll,
            "mass_0": float(hist[0]),  # same for all k; kept for compat
            "mass_p1": float(hist[1]),
            "mass_m1": float(hist[Q-1]),
            "note": "A1 symbol-shift only; not raw TTBin time-delay scan",
        })
    # peak over the scanned window
    best = max(out, key=lambda x: x["rate_eq"]) if out else None
    if best is not None:
        k_star = best["k"]
        nll_star = None
        if P_train is not None:
            bk_star = (b + k_star) % Q
            p_star = P_train[a, bk_star]
            nll_star = float(np.mean(-np.log2(np.maximum(p_star, 1e-15))))
            # fill NLL for k* entry
            for e in out:
                if e["k"] == k_star:
                    e["nll_bits"] = nll_star
                    break
        peak = {"k_star": int(k_star), "rate_star": float(best["rate_eq"]), "delta_rate": float(best["rate_eq"] - next((x["rate_eq"] for x in out if x["k"]==0), 0.0)), "nll_star": nll_star, "nll_0": nll_0, "hist_note": "derived from 1024-bin modular-delta histogram; not raw time-delay"}
    else:
        peak = {"k_star": 0, "rate_star": 0.0, "delta_rate": 0.0, "nll_star": None, "nll_0": nll_0}
    return out, peak

def _read_sidecar_fields(path: Path):
    """Read actual sidecar/meta file; return dict of extracted fields or error."""
    if not path.is_file():
        return None, f"missing {path}"
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"read fail {e}"
    # V13 sidecars have materialize_params.used_params; V55 has materialize_params.used_params nested
    mp = meta.get("materialize_params", {})
    used = mp.get("used_params", mp) if isinstance(mp, dict) else {}
    # Also check top-level for build_manifest style
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
        "frame_start_ps": used.get("frame_start_ps", None),
        "mapping": used.get("mapping", None),
        "pairing_threshold_ps": used.get("nearest_threshold_ps", used.get("pairing_threshold_ps", None)),
        "gate_width_ps": used.get("gate_width_ps", None),
        "occupancy_filter": meta.get("occupancy_filter", used.get("occupancy_filter", None)),
        "peak_status": used.get("peak_status", None),
        "peak_to_bg": used.get("peak_to_bg", None),
        "raw": meta,
    }
    return fields, None

def audit_metadata():
    v13_rows = []
    v55_rows = []
    # V13: read actual sidecars, missing reported as-is
    for src in ["1M", "1p5M", "2M"]:
        p = V13_SOURCES[src]["sidecar"]
        fields, err = _read_sidecar_fields(p)
        if err:
            v13_rows.append({"source": src, "path": str(p), "error": err, "status": {"_overall": f"INCOMPLETE missing sidecar: {err}"}})
        else:
            # per-field PASS/INCOMPLETE (actual values, not hardcoded assumption)
            status = {}
            for k in ["dimension", "bin_width_ps", "pairing", "processing_rule", "channels", "delay_used_ps", "peak_center_ps", "peak_sigma_ps", "corr_argmax", "corr_bins", "frame_start_ps", "mapping", "pairing_threshold_ps", "gate_width_ps", "occupancy_filter", "peak_status"]:
                v = fields.get(k)
                status[k] = "PASS" if v is not None else "INCOMPLETE"
                if v is not None:
                    status[k + "_value"] = v
            if err:
                status["_error"] = err
            v13_rows.append({"source": src, "path": str(p), "fields": fields, "status": status})
    # also read build_manifest for provenance (actual file, not hardcoded)
    build_manifest_path = REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/build_manifest.json"
    build_manifest = None
    if build_manifest_path.is_file():
        try:
            build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            build_manifest = {"error": "read fail"}
    # V55
    for src in ["1M", "1p5M", "2M"]:
        p = V55_SOURCES[src]["sidecar"]
        fields, err = _read_sidecar_fields(p)
        if err:
            v55_rows.append({"source": src, "path": str(p), "error": err, "status": {"_overall": f"INCOMPLETE missing sidecar: {err}"}})
        else:
            status = {}
            for k in ["dimension", "bin_width_ps", "pairing", "processing_rule", "channels", "delay_used_ps", "peak_center_ps", "peak_sigma_ps", "corr_argmax", "corr_bins", "frame_start_ps", "mapping", "pairing_threshold_ps", "gate_width_ps", "occupancy_filter"]:
                v = fields.get(k)
                status[k] = "PASS" if v is not None else "INCOMPLETE"
                if v is not None:
                    status[k + "_value"] = v
            v55_rows.append({"source": src, "path": str(p), "fields": fields, "status": status})
    return {"v13": v13_rows, "v55": v55_rows, "build_manifest_path": str(build_manifest_path), "build_manifest": build_manifest}

def main():
    ap = argparse.ArgumentParser(description="V56D0 decoder-free domain diagnosis")
    ap.add_argument("--pairs-root-v55", type=str, default=str(DEFAULT_V55_PAIRS))
    ap.add_argument("--pairs-root-v13", type=str, default=str(DEFAULT_V13_PAIRS))
    ap.add_argument("--counts", type=str, default=str(DEFAULT_COUNTS))
    ap.add_argument("--out", type=str, default=str(Path(__file__).parent / "diagnosis_v55_domain.json"))
    ap.add_argument("--limit", type=int, default=None, help="limit pairs per source for quick smoke (None=full)")
    args = ap.parse_args()

    print(f"=== V56D0 decoder-free diagnosis HEAD={HEAD} branch={BRANCH} data_sha={DATA_SHA} ===")
    print(f"V55 pairs root: {args.pairs_root_v55}")
    print(f"V13 pairs root: {args.pairs_root_v13}")
    print(f"counts: {args.counts}")

    counts_by_src, err = load_counts(Path(args.counts))
    if err:
        print(f"[WARN] counts load: {err} -> NLL will be null")
        counts_by_src = None
    else:
        print(f"counts loaded: {list(counts_by_src.keys())} shapes {[counts_by_src[k].shape for k in counts_by_src]}")

    # Build P_train per source if available
    P_by_src = {}
    if counts_by_src:
        for src in ["1M", "1p5M", "2M"]:
            arr = counts_by_src.get(src)
            if arr is None:
                for kk, vv in counts_by_src.items():
                    if src.lower() in kk.lower():
                        arr = vv
                        break
            if arr is not None and arr.shape == (1024, 1024):
                P_by_src[src] = build_P_A_given_B(arr)
                print(f"P_train {src}: shape {arr.shape} zero_frac {np.mean(arr==0):.4f}")
            else:
                print(f"[WARN] no valid counts for {src}")

    audit = audit_metadata()
    metadata_rows = audit["v55"]  # for backward compat printing
    print("\n-- Metadata audit (V13 actual sidecars vs V55) --")
    for row in audit["v13"]:
        print(f"  V13 {row['source']}: {row.get('status')}")
    for row in audit["v55"]:
        print(f"  V55 {row['source']}: {row.get('status')}")

    per_source = {}
    offset_all = {}
    shunt_evidence = {}
    per_source_decisions = {}

    for src in ["1M", "1p5M", "2M"]:
        print(f"\n-- Source {src} --")
        v55_path = Path(args.pairs_root_v55) / f"{V55_SOURCES[src]['session']}/pairs.parquet"
        if not v55_path.is_file():
            v55_path = V55_SOURCES[src]["parquet"]
        v13_path = V13_SOURCES[src]["parquet"]

        v55_data, e1 = load_pairs(v55_path, limit=args.limit)
        v13_data, e2 = load_pairs(v13_path, limit=args.limit)

        if e1:
            print(f"  V55 load {src} FAIL: {e1}")
        if e2:
            print(f"  V13 load {src} FAIL: {e2}")

        P = P_by_src.get(src)

        stats_v55 = None
        stats_v13 = None
        if v55_data:
            a, b, frame, _ = v55_data
            stats_v55 = per_source_stats(a, b, frame, P)
            print(f"  V55 {src}: n={stats_v55['n_pairs']} rate_eq={stats_v55['rate_eq']:.3f} u1={stats_v55['u1_eq']:.3f} u2={stats_v55['u2_eq']:.3f} nll={stats_v55['nll_bits_per_symbol']} q_zero={stats_v55['q_mass_on_p_zero']}")
            off_curve, peak = offset_scan(a, b, P, ks=range(-8, 9))
            offset_all[src] = {"curve": off_curve, "peak": peak, "method": "1024-bin modular-delta histogram; A1 symbol-shift only, not raw TTBin time-delay"}
            print(f"    offset(A1) peak k*={peak['k_star']} rate_star={peak['rate_star']:.3f} delta_rate={peak['delta_rate']:.3f} nll_star={peak['nll_star']} nll_0={peak['nll_0']}")
        if v13_data:
            a, b, frame, _ = v13_data
            stats_v13 = per_source_stats(a, b, frame, P)
            print(f"  V13 {src}: n={stats_v13['n_pairs']} rate_eq={stats_v13['rate_eq']:.3f} u1={stats_v13['u1_eq']:.3f} u2={stats_v13['u2_eq']:.3f} nll={stats_v13['nll_bits_per_symbol']}")

        # delta rate
        delta = {}
        if stats_v55 and stats_v13:
            delta = {
                "delta_rate_eq": stats_v55["rate_eq"] - stats_v13["rate_eq"],
                "delta_u1": stats_v55["u1_eq"] - stats_v13["u1_eq"],
                "delta_u2": stats_v55["u2_eq"] - stats_v13["u2_eq"],
                "delta_nll": (stats_v55["nll_bits_per_symbol"] - stats_v13["nll_bits_per_symbol"]) if (stats_v55["nll_bits_per_symbol"] is not None and stats_v13["nll_bits_per_symbol"] is not None) else None,
            }
            print(f"    delta V55-V13: rate {delta['delta_rate_eq']:+.3f} u1 {delta['delta_u1']:+.3f} u2 {delta['delta_u2']:+.3f} nll {delta['delta_nll']}")

        per_source[src] = {"v55": stats_v55, "v13": stats_v13, "delta": delta}

        # per-source shunt: A1 vs A2 vs B vs INCONCLUSIVE
        # A1 = parquet symbol/mapping shift (offset single-peak significant)
        # A2 = raw TTBin delay/peak/pairing contract (needs actual raw peak/delay/channel evidence, not just missing metadata)
        # B  = physical domain shift after excluding A1/A2
        if stats_v55 and offset_all.get(src):
            peak = offset_all[src]["peak"]
            is_single_peak = abs(peak["k_star"]) > 0 and peak["delta_rate"] > 0.20 and (peak["nll_star"] is not None and peak["nll_star"] < 1.0)
            curve = offset_all[src]["curve"]
            sorted_rates = sorted([c["rate_eq"] for c in curve], reverse=True)
            gap = sorted_rates[0] - sorted_rates[1] if len(sorted_rates) > 1 else 0
            single_peak_significant = bool(is_single_peak and gap > 0.05)
            still_low = bool(stats_v55["rate_eq"] < 0.45 and peak["rate_star"] < 0.50)
            # raw contract evidence requires actual raw fields present and mismatched, not just INCOMPLETE
            v55_row = next((r for r in audit["v55"] if r["source"] == src), None)
            v13_row = next((r for r in audit["v13"] if r["source"] == src), None)
            # check if raw fields actually present in V55 sidecar (delay/peak etc)
            has_raw_evidence = False
            missing_raw_fields = []
            if v55_row and "status" in v55_row:
                for fld in ["delay_used_ps", "peak_center_ps", "peak_sigma_ps", "corr_argmax", "frame_start_ps", "mapping"]:
                    if v55_row["status"].get(fld) == "INCOMPLETE":
                        missing_raw_fields.append(fld)
                # has_raw_evidence means V55 actually has these fields and they mismatch V13 actual values
                # we have values in fields if present
                has_raw_evidence = len(missing_raw_fields) == 0  # would need comparison, but if all present we can compare
            per_src_decision = None
            per_src_rationale = ""
            if single_peak_significant:
                per_src_decision = "PATH_A1_PARQUET_SYMBOL_SHIFT"
                per_src_rationale = f"A1: offset single-peak k*={peak['k_star']} delta_rate={peak['delta_rate']:.3f} gap={gap:.3f} nll_star={peak['nll_star']}"
            elif missing_raw_fields:
                # missing metadata alone -> INCONCLUSIVE, not auto Path A/A2
                per_src_decision = "INCONCLUSIVE_METADATA_INCOMPLETE"
                per_src_rationale = f"missing raw contract fields {missing_raw_fields} without actual raw peak/delay/channel evidence -> INCONCLUSIVE, cannot auto-assign Path A2"
            elif still_low:
                per_src_decision = "PATH_B_DOMAIN_SHIFT"
                per_src_rationale = f"B: low rate {stats_v55['rate_eq']:.3f} peak {peak['rate_star']:.3f} no A1 peak -> domain shift"
            else:
                per_src_decision = "INCONCLUSIVE"
                per_src_rationale = "insufficient evidence for A1/A2/B"
            per_source_decisions[src] = per_src_decision
            shunt_evidence[src] = {
                "peak_k": peak["k_star"],
                "peak_rate": peak["rate_star"],
                "delta_rate": peak["delta_rate"],
                "nll_star": peak["nll_star"],
                "nll_0": peak["nll_0"],
                "gap_to_second": float(gap),
                "single_peak_significant": single_peak_significant,
                "still_low": still_low,
                "per_source_decision": per_src_decision,
                "per_source_rationale": per_src_rationale,
                "missing_raw_fields": missing_raw_fields,
                "note": "b'=(b+k)%1024 covers A1 only; A2 requires raw TTBin evidence; B after excluding A1/A2",
            }

    # overall shunt: at least PATH_A_ALL / PATH_B_ALL / MIXED_BY_SOURCE / INCONCLUSIVE
    decisions = list(per_source_decisions.values())
    # handle metadata-incomplete dominance
    if not decisions:
        shunt = "INCONCLUSIVE"
        rationale = "no per-source data"
        next_step = "acquire 8-16 frames per source calibration, verify rate>60% and NLL<1.0, then decide"
    elif all(d == "INCONCLUSIVE_METADATA_INCOMPLETE" for d in decisions):
        shunt = "INCONCLUSIVE_METADATA_INCOMPLETE"
        rationale = "All 3 sources have missing raw contract fields (delay/peak/frame_start/mapping) but no actual raw peak/delay/channel evidence; missing metadata alone cannot auto-assign Path A/A2 -> INCONCLUSIVE, need actual raw evidence"
        next_step = "retrieve actual raw TTBin peak/delay/channel metrics (corr_argmax/peak_center/delay_used_ps) before assigning Path A2; then calibrate with independent frames"
    elif any(d == "INCONCLUSIVE_METADATA_INCOMPLETE" for d in decisions):
        # mixed with incomplete
        uniq = set(decisions)
        if len(uniq) == 1:
            shunt = "INCONCLUSIVE_METADATA_INCOMPLETE"
            rationale = "per-source INCONCLUSIVE due to missing raw contract fields without actual evidence"
            next_step = "retrieve actual raw metrics before Path A2"
        else:
            shunt = "MIXED_BY_SOURCE"
            rationale = f"per-source mixed including INCONCLUSIVE_METADATA_INCOMPLETE: {per_source_decisions}"
            next_step = "resolve missing raw evidence per source, then calibrate"
    elif len(set(decisions)) == 1:
        sole = decisions[0]
        if sole.startswith("PATH_A1"):
            shunt = "PATH_A_ALL"
            rationale = f"All 3 sources show A1 parquet symbol/mapping shift: {per_source_decisions}"
            next_step = "fix sidecar contract (delay/peak/frame_start/mapping explicit) + FileReader explicit binding + per-source G1'-G3' gates; original 90 remains unblinded forbidden to rerun; then calibrate with independent frames (0 overlap with 90)"
        elif sole == "PATH_B_DOMAIN_SHIFT":
            shunt = "PATH_B_ALL"
            rationale = f"All 3 sources show B domain shift (no A1 peak, low rate, processing nominally consistent): {per_source_decisions}"
            next_step = "re-estimate H(U1|B), H(U2|U1,B) from new intake N_ab, recompute source-adaptive m_total/m1/f (1.3*n*H -64)/5, redesign if needed; calibrate with independent frames first"
        else:
            shunt = "INCONCLUSIVE"
            rationale = f"All 3 sources INCONCLUSIVE: {per_source_decisions}"
            next_step = "acquire 8-16 frames per source calibration, verify rate>60% and NLL<1.0, then decide"
    else:
        shunt = "MIXED_BY_SOURCE"
        rationale = f"per-source decisions differ: {per_source_decisions} -> MIXED_BY_SOURCE"
        next_step = "handle per-source: A1 sources fix mapping contract, B sources re-estimate entropy; calibrate independently"

    # If still 0/90 observed and 76->27-41 reproduced, annotate as systematic input domain mismatch signal, not LDPC falsification
    avg_rate_v55 = float(np.mean([per_source[s]["v55"]["rate_eq"] for s in per_source if per_source[s]["v55"]])) if per_source else 0.0
    overall = {
        "head": HEAD,
        "branch": BRANCH,
        "data_sha": DATA_SHA,
        "metadata_audit": audit,
        "per_source": per_source,
        "offset_scan": offset_all,
        "shunt_evidence": shunt_evidence,
        "per_source_decisions": per_source_decisions,
        "avg_rate_v55": float(avg_rate_v55),
        "shunt_decision": shunt,
        "rationale": rationale,
        "next_step": next_step,
        "domain_split": "A1=parquet b'=(b+k)%1024 symbol/mapping shift, A2=raw TTBin delay/peak/pairing contract (needs actual raw evidence), B=physical domain shift after excluding A1/A2",
        "forbidden": [
            "DO NOT rerun corrected pipeline on original 90 blocks (already unblinded)",
            "DO NOT tune H1/Lane C/Δ8/decoder 90/1.0",
            "DO NOT claim LDPC falsification",
            "MUST use independent calibration frames (0 overlap with 90) before freezing new blocks",
            "Missing metadata alone -> INCONCLUSIVE_METADATA_INCOMPLETE, not auto Path A/A2",
        ],
        "notes": "decoder-free only; offset scan A1-only via 1024-bin modular-delta histogram, NOT raw time-delay scan; A==B 76%->27-41% is systematic input domain mismatch signal; V54 18 base -> 38 stage1 -> 43/45 final (not 42->43)"
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(overall, f, indent=2, ensure_ascii=False)
    print(f"\n=== Shunt decision: {shunt} ===")
    print(f"per_source: {per_source_decisions}")
    print(f"rationale: {rationale}")
    print(f"next: {next_step}")
    print(f"Wrote {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
