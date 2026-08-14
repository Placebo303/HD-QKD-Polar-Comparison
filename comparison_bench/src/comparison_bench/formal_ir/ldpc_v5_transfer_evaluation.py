"""Evaluation-only (retrospective) cross-loss transfer evaluation for the
frozen, promoted binary LDPC V5-C2 policy.

Declarations: evaluation_only, non-qualification, retrospective transfer
evaluation using the frozen V5-C2 policy from the 20260731 development
package.  No rate/matrix/OSD/redundancy/channel-model knob is re-selected:
everything is read from the frozen development package manifests.

  - 10 dB: official 20260801_v2_binary_ldpc_v5_real outcomes are referenced
    directly (never re-decoded).
  - 6 dB / 16 dB / 20 dB: every complete frame of the existing sidecars is
    decoded with the production ``run_ldpc_formal_v5`` unchanged (no
    parameter adaptation) and per-(loss, stratum) statistics are reported.
    The 6 dB acquisition uses a different sidecar layout
    (``e2e_pipeline_20260303_105145/sidecars`` instead of
    ``e2e_new_ttbin_fullgrid/sidecars``); it is mapped explicitly as a
    path special case, never guessed.
  - No promotion statement is produced.  Denominators are per-stratum
    complete frames (2676/2685/2687 at 6 dB, 289/290/290 at 16 dB,
    117/117/117 at 20 dB); three strata are never merged into one
    denominator.
  - The per-loss sidecar mapping above is the default; a caller-supplied
    ``sidecar_root`` overrides the sidecar root for the decoded losses of a
    run (used for the 20 dB pairing_v2 re-evaluation against the frozen
    V5-C2 policy, evaluation-only, zero parameter changes).  Default
    behavior is unchanged when no override is given.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import secrets
import statistics
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import ldpc_v5
from .shared import seed_record, sha256_bytes

RUN_ID = "binary_ldpc_v5_transfer_evaluation_v1"
DECLARATION = (
    "evaluation_only, non-qualification, retrospective transfer evaluation "
    "using frozen V5-C2"
)
N = 256
Q = 1024
SEED_BIT_LENGTH = 2623
CANDIDATE = "V5-C2"
PUBLIC_STRATA = ("bw120", "bw180", "bw200")
LOCK_TO_PUBLIC = {"d1024_bw120": "bw120", "d1024_bw180": "bw180", "d1024_bw200": "bw200"}
PUBLIC_TO_LOCK = {v: k for k, v in LOCK_TO_PUBLIC.items()}

_REPO = Path(__file__).resolve().parents[4]
_OUTROOT = _REPO / "comparison_bench" / "outputs_comparison"
DEV_PKG = _OUTROOT / "formal_ir_methods" / "20260731_v1_binary_ldpc_v5_development"
REAL10_PKG = _OUTROOT / "formal_ir_methods" / "20260801_v2_binary_ldpc_v5_real"
V4_16DB_PKG = _OUTROOT / "formal_ir_methods" / "20260729_v1_binary_ldpc_v4_16db_transfer"
V3_SYNTH_PKG = _OUTROOT / "formal_ir_methods" / "20260726_v1_binary_ldpc_v3_synthetic"
PROPOSAL_20DB = (
    _REPO / "openspec" / "changes" / "binary-ldpc-v4-corrected-qualification-v2" / "proposal.md"
)
RAW_ROOT = Path(r"D:\Data\Raw Data\QKD_Loss")
ACQUISITIONS = {
    "6": RAW_ROOT / "TypeII_776.1nm_3s" / "Type2_5s_6dB_2026-01-30_224719",
    "16": RAW_ROOT / "TypeII_776.1nm_3s" / "Type2_5s_16dB_2026-01-30_224900",
    "20": RAW_ROOT / "TypeII_776.1nm_3s" / "Type2_5s_20dB_2026-01-30_224943",
}
# 6 dB acquisition stores its sidecars under a different pipeline directory;
# explicit per-loss mapping, no generic discovery/guessing.
SIDECAR_SUBDIR = {
    "6": "e2e_pipeline_20260303_105145/sidecars",
    "16": "e2e_new_ttbin_fullgrid/sidecars",
    "20": "e2e_new_ttbin_fullgrid/sidecars",
}
_LOG = logging.getLogger(__name__)
FROZEN_NAMES = (
    "formal_codebook_manifest.json",
    "formal_selection_manifest.json",
    "formal_channel_model.json",
    "v5_h2_manifest.json",
    "v5_policy_manifest.json",
)
SUMMARY_COLUMNS = (
    "loss_db", "stratum", "denominator", "successes", "rate",
    "ci_low", "ci_high", "ser_mean", "ser_min", "ser_max",
    "leakage_mean_bits", "rounds_mean", "runtime_mean_s",
    "fallback_count", "data_exposure_note",
)


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise ValueError(f"json object expected: {path}")
    return doc


# --- frozen V5-C2 loading ---------------------------------------------------

def _load_frozen(pkg: Path) -> dict[str, Any]:
    """Read the frozen manifests; tampering is rejected by the production
    policy binding inside ``run_ldpc_formal_v5`` (reconstructed manifest hash
    must match)."""
    docs: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for name in FROZEN_NAMES:
        p = pkg / name
        hashes[name] = sha256_bytes(p.read_bytes())
        docs[name] = _json_read(p)
    policy = docs["v5_policy_manifest.json"]
    candidates = {c["candidate_id"]: c for c in policy["candidates"]}
    if CANDIDATE not in candidates:
        raise ValueError("V5-C2 policy missing from frozen manifest")
    selection = docs["formal_selection_manifest.json"]
    selected = [x["candidate_id"] for x in selection["plane_selections"]]
    return {"docs": docs, "hashes": hashes,
            "candidate_policy": candidates[CANDIDATE], "selected": selected}


# --- evaluation-specific seeds (recorded, deterministic per recorded root) ---

def _new_root_hex() -> str:
    return secrets.token_bytes(32).hex()


def _derive_seed(root_hex: str, loss_db: str, stratum: str, round_: int,
                 frame_id: int) -> dict[str, Any]:
    label = f"{RUN_ID}|{loss_db}db|{stratum}|round={round_}|frame={frame_id}".encode("ascii")
    raw = hashlib.shake_256(bytes.fromhex(root_hex) + b"\0" + label).digest(
        (SEED_BIT_LENGTH + 7) // 8)
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:SEED_BIT_LENGTH]
    return seed_record(bits)


# --- frame data (read-only sidecars) ----------------------------------------

def _load_sidecar(loss_db: str, stratum: str,
                  sidecar_root: Path | None = None) -> tuple[np.ndarray, np.ndarray, int]:
    if sidecar_root is not None:
        d = Path(sidecar_root) / PUBLIC_TO_LOCK[stratum] / "blk0"
    else:
        acq = ACQUISITIONS[loss_db]
        rel = SIDECAR_SUBDIR[loss_db]
        d = acq / rel / PUBLIC_TO_LOCK[stratum] / "blk0"
    a = np.load(d / "a_eff.npy", allow_pickle=False)
    b = np.load(d / "b_eff.npy", allow_pickle=False)
    if (a.ndim != 1 or b.ndim != 1 or a.shape != b.shape
            or not np.issubdtype(a.dtype, np.integer)
            or not np.issubdtype(b.dtype, np.integer)
            or np.any(a < 0) or np.any(a >= Q)
            or np.any(b < 0) or np.any(b >= Q)):
        raise ValueError(f"sidecar arrays invalid: {loss_db}/{stratum}")
    n_frames = a.size // N
    if n_frames < 1:
        raise ValueError(f"no complete frames: {loss_db}/{stratum}")
    return a, b, n_frames


# --- statistics -------------------------------------------------------------

def _cp_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float, str]:
    """Clopper-Pearson exact 95% binomial CI (scipy) with fallbacks."""
    if n <= 0 or not (0 <= k <= n):
        raise ValueError("binomial interval requires 0 <= k <= n")
    try:
        from scipy.stats import beta
        low = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
        high = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
        return float(low), float(high), "clopper_pearson_exact_scipy"
    except Exception:
        pass
    try:
        from scipy.special import betaincinv
        low = betaincinv(k, n - k + 1, alpha / 2) if k > 0 else 0.0
        high = betaincinv(k + 1, n - k, 1 - alpha / 2) if k < n else 1.0
        return float(low), float(high), "clopper_pearson_exact_betaincinv"
    except Exception:
        pass
    # ponytail: Wilson fallback, named so readers never mistake it for exact.
    z = 1.959963984540054
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, center - half), min(1.0, center + half), "wilson_approximation"


def _frame_record(loss_db: str, stratum: str, frame_id: Any, out: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "loss_db": loss_db, "stratum": stratum, "frame_id": frame_id,
        "dataset_id": out["dataset_id"], "status": out["status"],
        "failure_reason": out["failure_reason"], "raw_ser": out["raw_ser"],
        "fallback_invoked": bool(out["fallback_invoked"]),
        "rounds_attempted": int(out["rounds_attempted"]),
        "key_dependent_disclosure_bits_total": int(out["key_dependent_disclosure_bits_total"]),
        "public_control_bits_total": int(out["public_control_bits_total"]),
        "h1_syndrome_bits": int(out["h1_syndrome_bits"]),
        "h2_syndrome_bits": int(out["h2_syndrome_bits"]),
        "verification_tag_bits_component": int(out["verification_tag_bits_component"]),
        "feedback_control_bits": int(out["feedback_control_bits"]),
        "runtime_s": float(out["runtime_s"]),
        "decoder_call_count": int(out["decoder_call_count"]),
        "verification_check_count": int(out["verification_check_count"]),
        "selection_sha256": out["selection_sha256"],
        "channel_model_sha256": out["channel_model_sha256"],
        "h1_codebook_manifest_sha256": out["h1_codebook_manifest_sha256"],
        "h2_manifest_sha256": out["h2_manifest_sha256"],
        "policy_sha256": out["policy_sha256"],
    }


def _stats(rows: list[dict[str, Any]], *, denominator: int) -> dict[str, Any]:
    successes = sum(r["status"] == "verified_success" for r in rows)
    rate = successes / denominator if denominator else float("nan")
    ci_low, ci_high, ci_method = _cp_interval(successes, denominator)
    ser = [r["raw_ser"] for r in rows if isinstance(r["raw_ser"], (int, float))
           and np.isfinite(r["raw_ser"])]
    leak = [r["key_dependent_disclosure_bits_total"] for r in rows
            if r["status"] == "verified_success"]
    rounds = [r["rounds_attempted"] for r in rows]
    rt = [r["runtime_s"] for r in rows]
    return {
        "denominator": denominator, "successes": successes, "rate": rate,
        "ci_low": ci_low, "ci_high": ci_high, "ci_method": ci_method,
        "ser_mean": statistics.mean(ser) if ser else None,
        "ser_min": min(ser) if ser else None,
        "ser_max": max(ser) if ser else None,
        "leakage_mean_bits": statistics.mean(leak) if leak else None,
        "rounds_mean": statistics.mean(rounds) if rounds else None,
        "runtime_mean_s": statistics.mean(rt) if rt else None,
        "fallback_count": sum(bool(r["fallback_invoked"]) for r in rows),
    }


# --- exposure audit (read-only provenance trace) ------------------------------

def _v4_16db_exposure() -> dict[str, Any]:
    """Frames previously selected/used by the v4 16 dB transfer run."""
    report = _json_read(V4_16DB_PKG / "formal_qualification_report.json")
    gates = report["promotion_gates"]
    return {s: {"denominator": int(g["denominator"]),
                "successes": int(g["verified_success"])}
            for s, g in gates.items()}


def _v3_20db_reservation() -> dict[str, Any]:
    """v3 synthetic source manifest: 32 confirmation frames per 20 dB stratum."""
    plan = _json_read(V3_SYNTH_PKG / "pre_run_plan.json")
    manifest = plan["locked_data"]["source_manifest"]
    out = {}
    for ds in manifest["datasets"]:
        if ds["acquisition_loss"] == 20:
            out[ds["dataset_id"]] = {"role": ds["role"],
                                     "required_frames": int(ds["required_frames"])}
    return out


def _exposure_note(loss_db: str, stratum: str,
                   pairing_version: str | None = None) -> str:
    if loss_db == "20" and pairing_version == "pairing_v2":
        return ("20 dB pairing_v2 sidecars "
                "(e2e_20dB_fullgrid_pairing_v2_candidate); pairing_version=pairing_v2; "
                "these v2-paired frames were not used for any v5/v4 confirmation "
                "(the v3 32-frame reservation applies to the e2e_new_ttbin_fullgrid "
                "pairing, not to this pairing); denominator = all complete frames, "
                "no eligibility filtering (sidecar_meta fail_reason=map_ser>=0.1 "
                "left unfiltered)")
    if loss_db == "6":
        return ("retrospective evaluation of 6 dB sidecars (e2e_pipeline_20260303_105145); "
                "no prior v3/v4/official selection used these frames; denominator = all complete "
                "frames, no eligibility filtering (sidecar_meta fail_reason=map_ser>=0.1 "
                "left unfiltered)")
    if loss_db == "10":
        return ("official 20260801_v2_binary_ldpc_v5_real outcomes referenced "
                "directly (384/384 V5-C2, 128/128 per stratum); not re-decoded")
    if loss_db == "16":
        v4 = _v4_16db_exposure()
        s = f"v4 transfer (20260729_v1_binary_ldpc_v4_16db_transfer) previously selected 128 frames/stratum"
        for st, g in v4.items():
            s += f", {st}: {g['successes']}/{g['denominator']} verified_success"
        s += ("; those frames are exposure-used, remaining complete frames were not used in any "
              "confirmation; denominator = all complete frames, no eligibility filtering "
              "(sidecar_meta fail_reason=map_ser>=0.1 left unfiltered)")
        return s
    if loss_db == "20":
        v3 = _v3_20db_reservation()
        counts = {PUBLIC_TO_LOCK[stratum]: v3.get(PUBLIC_TO_LOCK[stratum], {})}
        note = ("v3 synthetic package (20260726_v1_binary_ldpc_v3_synthetic) source manifest "
                "reserved 32 confirmation frames per stratum (85 eligible = 117 - 32, per "
                "binary-ldpc-v4-corrected-qualification-v2 proposal.md)")
        for lock_s, rec in counts.items():
            note += f"; {lock_s} role={rec.get('role')} required={rec.get('required_frames')}"
        note += ("; denominator = all complete frames, no eligibility filtering "
                 "(sidecar_meta fail_reason=map_ser>=0.1 left unfiltered)")
        return note
    return ""


# --- execution ---------------------------------------------------------------

def _run_loss(frozen: Mapping[str, Any], loss_db: str,
              strata, sidecar_root: Path | None = None) -> dict[str, Any]:
    roots: dict[str, str] = {}
    for s in strata:
        for r in (0, 1):
            roots[f"{s}|round{r}"] = _new_root_hex()
    per_frame: list[dict[str, Any]] = []
    per_stratum: dict[str, dict[str, Any]] = {}
    for s in strata:
        a, b, n_frames = _load_sidecar(loss_db, s, sidecar_root=sidecar_root)
        rows: list[dict[str, Any]] = []
        _LOG.info("loss=%s stratum=%s frames=%d start", loss_db, s, n_frames)
        for i in range(n_frames):
            if i % 1000 == 0:
                _LOG.info("loss=%s stratum=%s frame=%d/%d", loss_db, s, i, n_frames)
            start = i * N
            alice = a[start:start + N]
            bob = b[start:start + N]
            seeds = [_derive_seed(roots[f"{s}|round{r}"], loss_db, s, r, i)
                     for r in (0, 1)]
            result = ldpc_v5.run_ldpc_formal_v5(
                alice, bob,
                pair_idx_sequence=np.arange(N, dtype=np.int64),
                dataset_id=f"real_{loss_db}db_{s}", frame_id=str(i),
                stratum=s,
                candidate_policy=frozen["candidate_policy"],
                policy_manifest=frozen["docs"]["v5_policy_manifest.json"],
                selection_manifest=frozen["docs"]["formal_selection_manifest.json"],
                channel_model=frozen["docs"]["formal_channel_model.json"],
                h2_manifest=frozen["docs"]["v5_h2_manifest.json"],
                locked_seeds=seeds)
            rows.append(_frame_record(loss_db, s, i, result["outcome"]))
        per_stratum[s] = _stats(rows, denominator=n_frames)
        per_frame.extend(rows)
    return {"roots": roots, "per_frame": per_frame, "per_stratum": per_stratum}


def _reference_10db() -> dict[str, Any]:
    """Direct reference of the official 10 dB outcomes; never decodes."""
    csv_path = REAL10_PKG / "real_frame_outcomes.csv"
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    per_frame: list[dict[str, Any]] = []
    per_stratum: dict[str, dict[str, Any]] = {}
    for s in PUBLIC_STRATA:
        rr = [r for r in rows if r["stratum"] == s]
        recs = [_frame_record("10", s, r["frame_id"], r) for r in rr]
        per_stratum[s] = _stats(recs, denominator=len(rr))
        per_frame.extend(recs)
    return {"roots": {}, "per_frame": per_frame, "per_stratum": per_stratum,
            "decoded": False, "source": str(csv_path)}


def evaluate_loss(dir_out: Path, loss_db: str, strata=PUBLIC_STRATA,
                  sidecar_root: Path | None = None,
                  pairing_version: str | None = None) -> dict[str, Any]:
    """Run the retrospective evaluation for one loss value (or reference 10 dB).

    ``sidecar_root`` (when given) overrides the per-loss fixed sidecar path
    for decoded losses; ``pairing_version`` is recorded for provenance in
    summary/report outputs (e.g. ``pairing_v2``).  Default behavior is
    unchanged when both are omitted.

    Returns the per-stratum statistics and per-frame outcomes; writes nothing.
    """
    loss_db = str(loss_db)
    if loss_db == "10":
        result = _reference_10db()
    elif loss_db in ACQUISITIONS:
        result = _run_loss(_load_frozen(DEV_PKG), loss_db, strata,
                           sidecar_root=sidecar_root)
    else:
        raise ValueError(f"unsupported loss: {loss_db!r}")
    result["loss_db"] = loss_db
    if pairing_version:
        result["pairing_version"] = pairing_version
    if sidecar_root is not None:
        result["sidecar_root"] = str(sidecar_root)
    return result


def evaluate_all(dir_out: Path, losses, strata=PUBLIC_STRATA,
                 allow_existing: bool = False,
                 sidecar_root: Path | None = None,
                 pairing_version: str | None = None,
                 report_name: str = "evaluation_report.json",
                 summary_name: str = "evaluation_summary.csv") -> dict[str, Any]:
    """Run all requested losses and write summary/report files into ``dir_out``.

    Default (``allow_existing=False``) requires a fresh, empty directory.
    With ``allow_existing=True`` an existing report (named ``report_name``)
    is carried over additively: losses present in the previous report but
    not re-run are preserved unchanged (never re-decoded), and the requested
    losses are evaluated and appended.

    ``sidecar_root``/``pairing_version`` (optional) are forwarded to
    ``evaluate_loss``; ``report_name``/``summary_name`` select the output
    file names so an override run can write new files next to existing ones
    without overwriting them.
    """
    dir_out = Path(dir_out)
    if dir_out.exists():
        if any(dir_out.iterdir()) and not allow_existing:
            raise FileExistsError(f"non-empty output directory: {dir_out}")
    else:
        dir_out.mkdir(parents=True, exist_ok=True)
    losses = [str(x) for x in losses]
    started = time.monotonic()
    frozen = _load_frozen(DEV_PKG)
    results: dict[str, dict[str, Any]] = {}
    merged_frames: list[dict[str, Any]] = []
    prev_report_path = dir_out / report_name
    if allow_existing and prev_report_path.exists():
        prev = _json_read(prev_report_path)
        prev_frames = list(prev.get("per_frame_outcomes", []))
        for loss_db, res in prev.get("losses", {}).items():
            if str(loss_db) in losses:
                continue  # re-evaluated below
            res = dict(res)
            res["loss_db"] = loss_db
            if "roots" not in res and "seed_roots" in res:
                res["roots"] = res["seed_roots"]  # report stores under seed_roots
            results[str(loss_db)] = res
            merged_frames.extend(r for r in prev_frames
                                 if r.get("loss_db") == str(loss_db))
    for loss_db in losses:
        results[loss_db] = evaluate_loss(dir_out, loss_db, strata,
                                         sidecar_root=sidecar_root,
                                         pairing_version=pairing_version)
        merged_frames.extend(results[loss_db]["per_frame"])
    rows: list[dict[str, Any]] = []
    for loss_db, res in results.items():
        for s, st in res["per_stratum"].items():
            row = {"loss_db": loss_db, "stratum": s, **{k: st[k] for k in
                   ("denominator", "successes", "rate", "ci_low", "ci_high",
                    "ser_mean", "ser_min", "ser_max", "leakage_mean_bits",
                    "rounds_mean", "runtime_mean_s", "fallback_count")},
                   "data_exposure_note": _exposure_note(loss_db, s,
                                                        pairing_version)}
            rows.append(row)
    columns = list(SUMMARY_COLUMNS)
    if pairing_version:
        columns.append("pairing_version")
    with open(dir_out / summary_name, "w", newline="",
              encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            rec = {k: ("" if row.get(k) is None else row.get(k))
                   for k in SUMMARY_COLUMNS}
            if pairing_version:
                rec["pairing_version"] = pairing_version
            writer.writerow(rec)
    denom_note = ("denominator per stratum = all complete frames ("
                  + ", ".join(f"{l} dB: " + "/".join(
                      str(res["per_stratum"][s]["denominator"])
                      for s in PUBLIC_STRATA)
                      for l, res in results.items())
                  + "); no eligibility filtering applied")
    report = {
        "run_id": RUN_ID,
        "declaration": DECLARATION,
        "candidate": CANDIDATE,
        "pairing_version": pairing_version,
        "sidecar_root": str(sidecar_root) if sidecar_root is not None else None,
        "frozen_policy_source": str(DEV_PKG),
        "frozen_manifest_sha256": frozen["hashes"],
        "selected_plane_candidates": frozen["selected"],
        "losses": {loss_db: {"decoded": res.get("decoded", True),
                             "seed_roots": res["roots"],
                             "per_stratum": res["per_stratum"]}
                   for loss_db, res in results.items()},
        "per_frame_outcomes": merged_frames,
        "exposure_audit": {
            "16db_v4_transfer": _v4_16db_exposure(),
            "20db_v3_reserved": _v3_20db_reservation(),
            "proposal_20db": "85 eligible = 117 - 32 reserved "
                             "(binary-ldpc-v4-corrected-qualification-v2 proposal.md)",
            "note_6db": ("6 dB retrospective evaluation included (sidecars from "
                         "e2e_pipeline_20260303_105145)" if "6" in results
                         else "6 dB not included in this evaluation; can be added later"),
        },
        "denominator_note": denom_note,
        "environment": {
            "numpy": np.__version__,
            "ldpc": (lambda: __import__("importlib.metadata", fromlist=["version"])
                     .version("ldpc"))(),
        },
        "elapsed_wall_s": time.monotonic() - started,
    }
    with open(dir_out / report_name, "w", encoding="utf-8") as f:
        f.write(_compact(report).decode("ascii") + "\n")
    return report
