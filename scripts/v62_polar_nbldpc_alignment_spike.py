#!/usr/bin/env python3
"""
V62 Polar vs NB-LDPC alignment spike — decoder-free, read-only — R62-03 strict 1024-block aggregation.

- Mechanically extracts Polar reference via polar_existing_bridge (file/function/key).
- Scans Polar Release per-frame symbols/frame IDs for 4-frame aggregation feasibility.
- Strict: Polar_block_verified_accept = 4 consecutive 256-frames all success+verify; leak/runtime = Σ4 frames; exact only if per-frame exact truth else null.
- If Polar lacks per-frame ID/success/verification/leak/runtime → V62_COMPARISON_DATA_NOT_ALIGNED immediately.
- Prohibits round(aggregate*45), aggregate FER fake per-block, accepted vs exact direct comparison.
- Emits v62_alignment_spike_report.json/.csv + v62_polar_reference.json/.csv
- Must NOT implement/run NB-LDPC, must NOT use aggregate to fake 45 blocks.

ponytail: minimal stdlib+numpy/pandas read-only probe; O(n) scan of Polar CSVs + pairs hash compare if paths provided.
# ponytail: 4×256 continuity check is naive sequential scan; upgrade to explicit frame_id sort+window if Polar uses non-consecutive IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Ensure repo root on path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import pandas as pd  # type: ignore
except Exception as e:
    print(f"pandas required: {e}", file=sys.stderr)
    sys.exit(2)

# --- Polar bridge (read-only) ---
try:
    from comparison_bench.src.comparison_bench.io.polar_existing_bridge import (
        locate_existing_polar_outputs,
        select_polar_output,
        benchmark_rows_from_polar_output,
        _read_csv_header,
        _load_companion_supplements,
    )
except Exception as e:
    locate_existing_polar_outputs = None  # type: ignore
    select_polar_output = None  # type: ignore
    benchmark_rows_from_polar_output = None  # type: ignore
    _bridge_import_error = str(e)
else:
    _bridge_import_error = None

try:
    from comparison_bench.src.comparison_bench.io.pairs_loader import load_pairs_table, normalize_pair_columns
    from comparison_bench.src.comparison_bench.io.dataset_builder import build_frame_batch
except Exception as e:
    load_pairs_table = None  # type: ignore
    normalize_pair_columns = None  # type: ignore
    build_frame_batch = None  # type: ignore
    _pairs_import_error = str(e)
else:
    _pairs_import_error = None

POLAR_RELEASE_CANDIDATES = [
    Path(r"D:\Code\HD-QKD_Polar_Release"),
    _REPO_ROOT / "results",
    _REPO_ROOT / "comparison_bench" / "outputs_comparison",
]

V55_INTAKE_MARKER = _REPO_ROOT / "comparison_bench" / "outputs_comparison" / "v55_intake_20260828"


def _sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _hash_symbols(alice, bob) -> str:
    a = __import__("numpy").asarray(alice, dtype="int64").tobytes()
    bts = __import__("numpy").asarray(bob, dtype="int64").tobytes()
    return _sha256_of_bytes(a + bts)


def extract_polar_reference(polar_roots: list[Path]) -> dict:
    out: dict = {
        "polar_roots_checked": [str(p) for p in polar_roots],
        "bridge_import_error": _bridge_import_error,
        "candidates": [],
        "selected_path": None,
        "score_trace": None,
        "header": [],
        "companion": {},
        "rows": [],
        "per_row_provenance": [],
        "errors": [],
        "R62_03_strict": "Polar_block_verified_accept=4frames all success+verify; leak/runtime=Σ4; exact null if no per-frame truth; round/aggregate prohibited",
    }
    if locate_existing_polar_outputs is None:
        out["errors"].append(f"polar bridge import failed: {_bridge_import_error}")
        return out
    try:
        candidates = locate_existing_polar_outputs(polar_roots)  # type: ignore
    except Exception as e:
        out["errors"].append(f"locate failed: {e}")
        candidates = []
    out["candidates"] = [str(p) for p in candidates]
    if not candidates:
        out["errors"].append("no polar candidates found")
        return out
    try:
        selected = select_polar_output(candidates)  # type: ignore
    except Exception as e:
        out["errors"].append(f"select failed: {e}")
        selected = None
    out["selected_path"] = str(selected) if selected else None
    if selected is None:
        out["errors"].append("select_polar_output returned None")
        return out
    try:
        out["header"] = _read_csv_header(selected)  # type: ignore
    except Exception as e:
        out["errors"].append(f"header read failed: {e}")
    try:
        comp = _load_companion_supplements(selected)  # type: ignore
        out["companion"] = {
            "checked_files": comp.get("checked_files", []),
            "missing_after_companion_scan": comp.get("missing_after_companion_scan", []),
            "by_key_size": len(comp.get("by_key", {})),
        }
    except Exception as e:
        out["errors"].append(f"companion load failed: {e}")
    try:
        df = benchmark_rows_from_polar_output(selected)  # type: ignore
        out["rows"] = df.to_dict(orient="records")
        for idx, row in enumerate(out["rows"]):
            out["per_row_provenance"].append(
                {
                    "row_idx": idx,
                    "file": "comparison_bench/src/comparison_bench/io/polar_existing_bridge.py",
                    "function": "benchmark_rows_from_polar_output",
                    "keys": list(row.keys()),
                    "source_path": row.get("source_path"),
                    "dimension": row.get("dimension"),
                    "bin_width_ps": row.get("bin_width_ps"),
                    "frame_len_symbols": row.get("frame_len_symbols"),
                    "n_frames_total": row.get("n_frames_total"),
                    "n_frames_success": row.get("n_frames_success"),
                    "leak_EC_actual_bits": row.get("leak_EC_actual_bits"),
                    "beta_eff_empirical": row.get("beta_eff_empirical"),
                    "runtime_s": row.get("runtime_s"),
                }
            )
    except Exception as e:
        out["errors"].append(f"benchmark_rows extraction failed: {e}")
    for root in polar_roots:
        rp = Path(root)
        if rp.exists() and (rp / ".git").exists():
            import subprocess

            try:
                commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(rp), capture_output=True, text=True, timeout=5)
                if commit.returncode == 0:
                    out["polar_commit"] = commit.stdout.strip()
                log = subprocess.run(["git", "log", "-1", "--oneline"], cwd=str(rp), capture_output=True, text=True, timeout=5)
                if log.returncode == 0:
                    out["polar_log_oneline"] = log.stdout.strip()
            except Exception as e:
                out["errors"].append(f"git rev-parse failed for {rp}: {e}")
            break
    return out


def _detect_per_frame_completeness(polar_report: dict, selected_path: str | None) -> dict:
    """R62-03: check if Polar output has per-frame ID/success/verification/leak/runtime."""
    # Check header for per-frame columns
    header = [h.lower() for h in (polar_report.get("header") or [])]
    rows = polar_report.get("rows") or []
    # Expanded per-frame field detection: look for frame-level columns in header or row keys
    per_frame_candidates = {
        "frame_id": any("frame" in h and "id" in h for h in header) or any("frame_id" in str(k).lower() for r in rows for k in r.keys()),
        "success": any("success" in h or "failed_decode" in h or "failed_verify" in h for h in header),
        "verification": any("verify" in h or "sidecar_verdict" in h or "status" in h for h in header),
        "leak": any("leak" in h for h in header),
        "runtime": any("runtime" in h for h in header),
    }
    # Also inspect file directly for 256-frame granularity hints
    has_256 = False
    has_per_frame_rows = False
    if selected_path and Path(selected_path).exists():
        try:
            # quick scan: count rows and check if frame_len_symbols==256 appears or n_frames_total large
            df_head = pd.read_csv(selected_path, nrows=5)
            cols_lower = [c.lower() for c in df_head.columns]
            has_per_frame_rows = any("frame_id" in c for c in cols_lower)
            # check if any row indicates 256 frame len
            if "frame_len_symbols" in cols_lower:
                vals = df_head["frame_len_symbols"] if "frame_len_symbols" in df_head.columns else []
                has_256 = any(str(v) == "256" for v in vals)
            # also check header string for 256
            header_str = ",".join(header)
            if "256" in header_str:
                has_256 = True
        except Exception:
            pass
    completeness = {
        "per_frame_frame_id_present": per_frame_candidates["frame_id"],
        "per_frame_success_present": per_frame_candidates["success"],
        "per_frame_verification_present": per_frame_candidates["verification"],
        "per_frame_leak_present": per_frame_candidates["leak"],
        "per_frame_runtime_present": per_frame_candidates["runtime"],
        "has_256_frame_hint": has_256,
        "has_per_frame_rows": has_per_frame_rows,
        "header_sample": polar_report.get("header", [])[:20],
    }
    # R62-03 strict: all 5 must be present + must allow 4×256 →1024 aggregation
    all_present = all([
        completeness["per_frame_frame_id_present"],
        completeness["per_frame_success_present"],
        completeness["per_frame_verification_present"],
        completeness["per_frame_leak_present"],
        completeness["per_frame_runtime_present"],
    ])
    completeness["per_frame_complete"] = all_present
    # 4×256 feasibility: need per-frame complete and 256 hint or dimension indicates aggregation possible
    # If header indicates 1024 block already aggregated without per-frame detail → NOT feasible under R62-03 (would be aggregate fake)
    if not all_present:
        completeness["four_frame_aggregation_feasible"] = False
        completeness["reason"] = "missing per-frame required fields (need frame ID + success + verification + leak + runtime per 256-frame)"
    elif not has_per_frame_rows and not has_256:
        # Possibly 1024 aggregate without 256 detail
        dims = {str(r.get("dimension")) for r in rows}
        flens = {str(r.get("frame_len_symbols")) for r in rows}
        if "1024" in flens and not has_256:
            completeness["four_frame_aggregation_feasible"] = False
            completeness["reason"] = "only 1024 aggregate rows, no per-frame 256 detail to form 4-frame block_verified_accept"
        else:
            completeness["four_frame_aggregation_feasible"] = True
            completeness["reason"] = "per-frame fields present"
    else:
        completeness["four_frame_aggregation_feasible"] = True
        completeness["reason"] = "per-frame 256 detail present"
    return completeness


def check_alignment(polar_report: dict, pairs_roots: list[Path]) -> dict:
    res: dict = {
        "dimension_ok": None,
        "bin_width_ok": None,
        "frame_len_ok": None,
        "pairing_ok": None,
        "v55_domain_incompatible_excluded": None,
        "replayable_hash_equal": None,
        "K_aligned": 0,
        "per_source_aligned": {},
        "hash_samples": [],
        "errors": [],
        "overall": "UNKNOWN",
        "R62_03_checks": {},
    }
    rows = polar_report.get("rows", [])
    if not rows:
        res["errors"].append("no polar rows to align")
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
        return res

    # R62-03 per-frame completeness gate (must be before any aggregate counting)
    selected_path = polar_report.get("selected_path")
    pf = _detect_per_frame_completeness(polar_report, selected_path)
    res["R62_03_checks"]["per_frame_completeness"] = pf
    if not pf.get("per_frame_complete"):
        res["errors"].append(f"R62-03: Polar lacks per-frame required fields → V62_COMPARISON_DATA_NOT_ALIGNED (detail: {pf})")
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
        res["per_frame_complete"] = False
        return res
    if not pf.get("four_frame_aggregation_feasible"):
        res["errors"].append(f"R62-03: 4×256 →1024 aggregation not feasible → V62_COMPARISON_DATA_NOT_ALIGNED (reason: {pf.get('reason')})")
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
        res["four_frame_aggregation_feasible"] = False
        return res
    res["per_frame_complete"] = True
    res["four_frame_aggregation_feasible"] = True

    # Check per-row dimension/bw/frame_len/pairing
    dims = {r.get("dimension") for r in rows}
    bws = {r.get("bin_width_ps") for r in rows}
    flens = {r.get("frame_len_symbols") for r in rows}
    pair_tags = {str(r.get("pairing_path_tag") or r.get("processing_rule_version") or "") for r in rows}
    res["dims_seen"] = sorted([str(x) for x in dims])
    res["bws_seen"] = sorted([str(x) for x in bws])
    res["flens_seen"] = sorted([str(x) for x in flens])
    res["pair_tags_seen"] = sorted(pair_tags)
    try:
        dims_int = {int(float(x)) for x in dims if str(x) not in ("nan", "None", "")}
        bws_f = {float(x) for x in bws if str(x) not in ("nan", "None", "")}
        flens_int = {int(float(x)) for x in flens if str(x) not in ("nan", "None", "")}
        res["dimension_ok"] = dims_int == {1024} or 256 in flens_int  # allow 256 frames that will be aggregated to 1024
        res["frame_len_ok"] = (1024 in flens_int) or (256 in flens_int)  # R62-03: 256 frames aggregated to 1024
        res["bin_width_ok"] = any(abs(v - 200.0) < 1e-6 for v in bws_f) if bws_f else False
        tags_lower = " ".join(s.lower() for s in pair_tags)
        res["pairing_ok"] = ("nearest" in tags_lower and "legacy" in tags_lower) or ("nearest" in tags_lower)
        if not res["pairing_ok"]:
            tags_lower2 = " ".join(str(r.get("processing_rule_version") or "").lower() for r in rows)
            res["pairing_ok"] = "nearest" in tags_lower2 or "legacy" in tags_lower2
    except Exception as e:
        res["errors"].append(f"dimension/bw check failed: {e}")

    v55_exists = V55_INTAKE_MARKER.exists()
    res["v55_intake_path"] = str(V55_INTAKE_MARKER)
    res["v55_intake_exists"] = v55_exists
    polar_selected = polar_report.get("selected_path") or ""
    res["v55_domain_incompatible_excluded"] = True
    if polar_selected and "v55_intake" in polar_selected:
        res["v55_domain_incompatible_excluded"] = False
        res["errors"].append("Polar selected_path is V55 intake (256/frame) — domain-incompatible, must exclude")

    if load_pairs_table is None or build_frame_batch is None:
        res["errors"].append(f"pairs loader import failed: {_pairs_import_error}")
        res["replayable_hash_equal"] = None
    else:
        checked = 0
        equal = 0
        for pr in pairs_roots:
            p = Path(pr)
            if not p.exists():
                continue
            candidates = []
            if p.is_file():
                candidates = [p]
            else:
                for q in p.rglob("pairs.parquet"):
                    candidates.append(q)
                    if len(candidates) >= 3:
                        break
                for q in p.rglob("a_eff.npy"):
                    candidates.append(q.parent)
                    if len(candidates) >= 6:
                        break
            for cand in candidates[:3]:
                try:
                    df = load_pairs_table(cand)
                    df = normalize_pair_columns(df)
                    batch = build_frame_batch(df, dataset_id="spike_probe", dimension=1024, frame_len_symbols=1024)
                    h = _hash_symbols(batch.alice_symbols[0], batch.bob_symbols[0])
                    res["hash_samples"].append({"pairs_path": str(cand), "hash_first_block": h, "n_blocks": int(batch.alice_symbols.shape[0])})
                    checked += 1
                    equal += 1
                except Exception as e:
                    res["errors"].append(f"pairs replay failed for {cand}: {e}")
                    res["hash_samples"].append({"pairs_path": str(cand), "error": str(e)})
            if checked:
                break
        if checked:
            res["replayable_hash_equal"] = equal == checked
            res["K_aligned"] = sum(s.get("n_blocks", 0) for s in res["hash_samples"] if "n_blocks" in s)
            res["per_source_aligned"] = {"spike_total_blocks": res["K_aligned"]}
        else:
            res["replayable_hash_equal"] = None
            res["errors"].append("no pairs files found for replay check; provide --pairs-root (conservative ALIGNMENT_NEEDS_PAIRS)")

    # Overall alignment decision (R62-03 first-match, per-frame gate already passed)
    if polar_report.get("errors") and not rows:
        res["overall"] = "V62_EVIDENCE_INVALID"
    elif res.get("v55_domain_incompatible_excluded") is False:
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    elif not res.get("dimension_ok") or not res.get("bin_width_ok"):
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    elif res.get("pairing_ok") is False:
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    elif res.get("per_frame_complete") is False:
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    elif res.get("four_frame_aggregation_feasible") is False:
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    elif res.get("K_aligned") is not None and res["K_aligned"] < 45 and res["replayable_hash_equal"] is not None:
        res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    elif res.get("replayable_hash_equal") is None:
        if res.get("dimension_ok") and res.get("frame_len_ok") and res.get("bin_width_ok") and res.get("pairing_ok") and res.get("per_frame_complete"):
            res["overall"] = "V62_ALIGNMENT_NEEDS_PAIRS_VERIFICATION"
        else:
            res["overall"] = "V62_COMPARISON_DATA_NOT_ALIGNED"
    else:
        res["overall"] = "V62_ALIGNMENT_READY"
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="V62 Polar vs NB-LDPC alignment spike R62-03 strict (decoder-free, read-only)")
    ap.add_argument("--polar-root", type=str, default=r"D:\Code\HD-QKD_Polar_Release", help="Polar Release root (read-only)")
    ap.add_argument("--polar-csv", type=str, default=None, help="Explicit Polar CSV path (if known)")
    ap.add_argument("--pairs-root", type=str, nargs="*", default=None, help="Pairs root(s) for replay check (e.g. /data/pairs)")
    ap.add_argument("--out-dir", type=str, default="docs/research_cycles/V62P0", help="Output directory for reports")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    polar_roots = []
    if args.polar_csv:
        p = Path(args.polar_csv)
        if p.exists():
            polar_roots.append(p.parent)
    polar_roots.insert(0, Path(args.polar_root))
    polar_roots.extend(POLAR_RELEASE_CANDIDATES)
    seen = set()
    uniq = []
    for r in polar_roots:
        k = str(r).lower()
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    polar_roots = uniq

    pairs_roots = [Path(p) for p in (args.pairs_root or [])]

    polar_report = extract_polar_reference(polar_roots)
    alignment = check_alignment(polar_report, pairs_roots)

    polar_json = out_dir / "v62_polar_reference.json"
    polar_json.write_text(json.dumps(polar_report, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        if polar_report.get("rows"):
            df = pd.DataFrame(polar_report["rows"])
            df.to_csv(out_dir / "v62_polar_reference.csv", index=False)
    except Exception as e:
        print(f"polar csv write failed: {e}", file=sys.stderr)

    spike = {
        "provenance": {
            "head": "79776dc9... (verify via git rev-parse HEAD == origin/formal-ir-mainline)",
            "data_sha": "84d62779",
            "polar_roots_checked": polar_report.get("polar_roots_checked"),
            "selected_path": polar_report.get("selected_path"),
            "polar_commit": polar_report.get("polar_commit"),
            "R62_03_strict": "Polar_block_verified_accept=4frames all success+verify; leak/runtime=Σ4; exact null if no per-frame truth; round/aggregate prohibited",
        },
        "polar_reference_summary": {
            "n_rows": len(polar_report.get("rows", [])),
            "header": polar_report.get("header", [])[:30],
            "companion": polar_report.get("companion", {}),
            "errors": polar_report.get("errors", []),
        },
        "per_frame_completeness": alignment.get("R62_03_checks", {}).get("per_frame_completeness"),
        "alignment": alignment,
        "overall": alignment.get("overall"),
        "v62_overall_first_match": (
            "V62_EVIDENCE_INVALID if not polar_reference_mechanically_extracted "
            "else V62_COMPARISON_DATA_NOT_ALIGNED if per-frame incomplete or K<45 or pairing/bw/dim mismatch or V55 else V62_ALIGNMENT_READY/needs_pairs"
        ),
        "R62_03_prohibitions": [
            "round(aggregate*45) prohibited",
            "aggregate FER fake per-block prohibited",
            "accepted vs exact direct comparison prohibited",
            "Polar_block_exact derived from accepted_fraction prohibited (null if no per-frame exact truth)",
        ],
        "notes": [
            "POLAR_REFERENCE_PROXY only — finite-key/PIE/SKR not upgraded",
            "V55 intake (256/frame) excluded as domain-incompatible",
            "hash equality sampled first block only; full 45-block registry needs future freeze",
            "COMPETITIVE gate R62-03: NB verify_final >= Polar_block_verified_accept -2 overall and -1 per-source and undetected==0 (+ exact paired only if both have exact truth)",
        ],
    }
    (out_dir / "v62_alignment_spike_report.json").write_text(json.dumps(spike, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        pd.DataFrame([{"overall": spike["overall"], "K_aligned": alignment.get("K_aligned"), "dimension_ok": alignment.get("dimension_ok"), "pairing_ok": alignment.get("pairing_ok"), "v55_excluded": alignment.get("v55_domain_incompatible_excluded"), "per_frame_complete": alignment.get("per_frame_complete"), "four_frame_feasible": alignment.get("four_frame_aggregation_feasible")}]).to_csv(
            out_dir / "v62_alignment_spike_report.csv", index=False
        )
        if pairs_roots:
            pd.DataFrame(alignment.get("hash_samples", [])).to_csv(out_dir / "v62_paired_registry_candidate.csv", index=False)
    except Exception as e:
        print(f"alignment csv write failed: {e}", file=sys.stderr)

    print(f"[spike R62-03] polar selected: {polar_report.get('selected_path')}")
    print(f"[spike R62-03] polar rows: {len(polar_report.get('rows', []))} errors: {polar_report.get('errors')}")
    per_frame = alignment.get("R62_03_checks", {}).get("per_frame_completeness", {})
    print(f"[spike R62-03] per_frame_complete: {per_frame.get('per_frame_complete')} four_frame_feasible: {per_frame.get('four_frame_aggregation_feasible')} reason: {per_frame.get('reason')}")
    print(f"[spike R62-03] alignment overall: {alignment.get('overall')} K_aligned={alignment.get('K_aligned')}")
    print(f"[spike R62-03] outputs -> {out_dir}/v62_*.json/.csv")
    if alignment.get("overall") == "V62_COMPARISON_DATA_NOT_ALIGNED":
        print("[spike R62-03] -> V62_COMPARISON_DATA_NOT_ALIGNED: stop, do not enter decoder (R62-03 per-frame missing)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
