"""V63 development (90 blocks) guarded runner — 90 L1+90 base+≤90 stage1+≤90 stage2 =180-360 hard cap."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comparison_bench/src"))

from comparison_bench.methods.nbldpc_shell_adapter import ACCEPTED_PLAN_SHA, DEV_HARD_CAP  # noqa: E402
from comparison_bench.pipeline.shell_integration import domain_check  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_01"
DEV_REGISTRY = REPO_ROOT / "docs/research_cycles/V63P0/v63_dev_registry.json"
SCOPED_TRACKED = (
    "comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py",
    "comparison_bench/src/comparison_bench/pipeline/shell_integration.py",
    "comparison_bench/src/comparison_bench/formal_ir/v54_two_stage_incremental_l2_rescue.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)


def _wilson_interval(k: int, n: int, z: float = 1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    delta = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5
    return [(centre - delta) / denom, (centre + delta) / denom]


def _build_v63_summary(records, total_calls, total_disclosed, per_source_disclosed, per_source_n, stage_counts, elapsed_s, head_sha):
    from collections import Counter
    # ponytail: stdlib only, no new deps
    total_blocks = len(records)
    accepted = sum(1 for r in records if r["accepted"])
    exact = sum(1 for r in records if r["exact"])
    undetected = sum(1 for r in records if r["undetected"])
    # per-source
    per_source = {}
    four_overall = Counter()
    per_source_blocks = Counter(r["source"] for r in records)
    for src in sorted(per_source_blocks):
        sub = [r for r in records if r["source"] == src]
        n = len(sub)
        a = sum(1 for r in sub if r["accepted"])
        e = sum(1 for r in sub if r["exact"])
        u = sum(1 for r in sub if r["undetected"])
        # four-class: exact, undetected (accepted non-exact undetected), rejected (accepted false), accepted_non_exact_detected
        # undetected already is accepted && !exact && undetected; rejected = not accepted; exact = accepted && exact
        rejected = sum(1 for r in sub if not r["accepted"])
        # accepted non-exact detected would be accepted && !exact && !undetected (should be 0 for this run)
        accepted_non_exact_detected = sum(1 for r in sub if r["accepted"] and not r["exact"] and not r["undetected"])
        per_source[src] = {
            "blocks": n,
            "accepted": f"{a}/{n}",
            "accepted_n": a,
            "exact": f"{e}/{n}",
            "exact_n": e,
            "undetected": u,
            "four_class": {"exact": e, "undetected": u, "rejected": rejected, "accepted_non_exact_detected": accepted_non_exact_detected},
            "wilson95_accepted": _wilson_interval(a, n),
            "wilson95_exact": _wilson_interval(e, n),
            "stage_used": dict(Counter(r["stage_used"] for r in sub)),
            "disclosed_total": sum(r["leak_total"] for r in sub),
            "disclosed_avg": sum(r["leak_total"] for r in sub) / n if n else 0,
            "disclosed_per_accepted": (sum(r["leak_total"] for r in sub if r["accepted"]) / a) if a else 0,
        }
        # overall total disclosed per accepted uses total_disclosed / accepted (includes failed blocks' leak in numerator — matches task 1176.71)
        four_overall["exact"] += e
        four_overall["undetected"] += u
        four_overall["rejected"] += rejected
        four_overall["accepted_non_exact_detected"] += accepted_non_exact_detected
    # rescue counts: N_stage1 = delta8, N_stage2 = delta16 (verification-only rescue)
    rescue = {"N_stage1_delta8": stage_counts.get("delta8", 0), "N_stage2_delta16": stage_counts.get("delta16", 0)}
    # overall verdict: undetected==1 forces CORRECTION_WORKS_BUT_NOT_PASS even though accepted 85/90 passes threshold
    if undetected != 0:
        overall_state = "V63_SHELL_CORRECTION_WORKS_BUT_NOT_PASS"
        overall_pass = False
        fail_reason = f"undetected=={undetected} blocks PASS gate (requires undetected==0); block v63_dev_1M_0133"
    elif accepted >= 70 and exact >= 70 and all(per_source[s]["accepted_n"] >= 20 for s in per_source) and all(per_source[s]["exact_n"] >= 20 for s in per_source):
        overall_state = "V63_SHELL_DEVELOPMENT_PASS"
        overall_pass = True
        fail_reason = ""
    elif exact > 0 or rescue["N_stage1_delta8"] > 0 or rescue["N_stage2_delta16"] > 0:
        overall_state = "V63_SHELL_CORRECTION_WORKS_BUT_NOT_PASS"
        overall_pass = False
        fail_reason = "below PASS thresholds but has_signal"
    else:
        overall_state = "V63_SHELL_NO_RETAINED_SIGNAL"
        overall_pass = False
        fail_reason = "no retained signal"
    # disclosure per accepted overall
    disclosure_per_accepted = float(total_disclosed / accepted) if accepted else 0
    return {
        "registry_type": "INTEGRATION_FRESH_CANDIDATE",
        "total_blocks": total_blocks,
        "total_calls": int(total_calls),
        "hard_cap": DEV_HARD_CAP,
        "budget": f"90 L1+90 base+≤90 stage1+≤90 stage2 =180-360, got {total_calls}",
        "total_disclosed_bits": int(total_disclosed),
        "overall_avg": float(total_disclosed / total_blocks) if total_blocks else 0,
        "per_source_avg": {k: float(v / per_source_n[k]) for k, v in per_source_disclosed.items()},
        "per_source_total": per_source_disclosed,
        "stage_used": stage_counts,
        "rescue": rescue,
        "elapsed_s": float(elapsed_s),
        "accepted_plan_sha": ACCEPTED_PLAN_SHA,
        "head_sha": head_sha,
        # required main metrics
        "accepted": f"{accepted}/{total_blocks}",
        "accepted_n": accepted,
        "exact": f"{exact}/{total_blocks}",
        "exact_n": exact,
        "undetected": undetected,
        "undetected_blocks": [r["block_id"] for r in records if r["undetected"]],
        "per_source": per_source,
        "four_class_overall": dict(four_overall),
        "disclosure_per_accepted": disclosure_per_accepted,
        "disclosure_per_accepted_str": f"{disclosure_per_accepted:.2f}",
        "wilson95_overall_accepted": _wilson_interval(accepted, total_blocks),
        "wilson95_overall_exact": _wilson_interval(exact, total_blocks),
        "overall_state": overall_state,
        "overall_pass": overall_pass,
        "fail_reason": fail_reason,
        "tag_scope": "l2_only",
        "leak_tiers": {
            "base": {"1M": 1064, "1p5M": 1094, "2M": 1104},
            "delta8": 40,
            "delta16": 80,
            "verified": True,
            "note": "tag64 included in base once, leak_stage1=base+40 leak_stage2=base+80",
        },
    }


def _parse_args(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="V63 development 90 blocks — requires --execution-authorized")
    p.add_argument("--execution-authorized", action="store_true", help="Required explicit authorization")
    p.add_argument("--authorized-target-sha", default=None, help="Full implementation SHA (must equal ACCEPTED_PLAN_SHA)")
    p.add_argument("--output-root", default=None, help="Override output root (for tests)")
    p.add_argument("--repair-summary", action="store_true", help="Regenerate v63_summary.json from existing v63_records.json without decoder (additive, records not overwritten)")
    return p.parse_args(argv)


def _check_git(authorized: str):
    if ACCEPTED_PLAN_SHA != "397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a":
        print(f"BLOCKED: ACCEPTED_PLAN_SHA drift {ACCEPTED_PLAN_SHA} != 397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a", file=sys.stderr)
        sys.exit(2)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        origin = subprocess.check_output(["git", "rev-parse", "origin/formal-ir-mainline"], text=True).strip()
    except Exception as exc:
        print(f"BLOCKED: git rev-parse failed: {exc}", file=sys.stderr)
        sys.exit(2)
    if head != authorized:
        print(f"BLOCKED: HEAD {head} != authorized {authorized}", file=sys.stderr)
        sys.exit(2)
    if origin != authorized:
        print(f"BLOCKED: origin/formal-ir-mainline {origin} != authorized {authorized}", file=sys.stderr)
        sys.exit(2)
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    except Exception as exc:
        print(f"BLOCKED: git status failed: {exc}", file=sys.stderr)
        sys.exit(2)
    dirty = [line for line in out.splitlines() if any(p in line for p in SCOPED_TRACKED)]
    if dirty:
        print(f"BLOCKED: SCOPED dirty {dirty}", file=sys.stderr)
        sys.exit(2)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.execution_authorized:
        print("BLOCKED: EXECUTE_NOT_AUTHORIZED — pass --execution-authorized with --authorized-target-sha", file=sys.stderr)
        return 2
    if not args.authorized_target_sha:
        print("BLOCKED: --authorized-target-sha required", file=sys.stderr)
        return 2
    if len(args.authorized_target_sha) != 40:
        print("BLOCKED: --authorized-target-sha must be 40-char full SHA", file=sys.stderr)
        return 2
    _check_git(args.authorized_target_sha)

    output_root = Path(args.output_root) if args.output_root else DEFAULT_OUTPUT_ROOT
    # additive repair path: regenerate summary from existing records without decoder
    if args.repair_summary:
        if not output_root.is_dir():
            print(f"BLOCKED: repair requires existing output_root {output_root}", file=sys.stderr)
            return 2
        rec_path = output_root / "v63_records.json"
        if not rec_path.is_file():
            print(f"BLOCKED: records missing {rec_path}", file=sys.stderr)
            return 2
        records = json.loads(rec_path.read_text(encoding="utf-8"))
        if len(records) != 90:
            print(f"BLOCKED: records must have 90 entries, got {len(records)}", file=sys.stderr)
            return 2
        total_calls = sum(r["decoder_calls"] for r in records)
        total_disclosed = sum(r["leak_total"] for r in records)
        from collections import Counter
        per_source_disclosed = dict(Counter())
        per_source_n = dict(Counter())
        stage_counts = dict(Counter(r["stage_used"] for r in records))
        # ensure keys
        for k in ("base", "delta8", "delta16"):
            stage_counts.setdefault(k, 0)
        for r in records:
            per_source_disclosed[r["source"]] = per_source_disclosed.get(r["source"], 0) + r["leak_total"]
            per_source_n[r["source"]] = per_source_n.get(r["source"], 0) + 1
        # elapsed from existing summary if present, else 0
        sum_path = output_root / "v63_summary.json"
        elapsed_s = 0
        if sum_path.is_file():
            try:
                old = json.loads(sum_path.read_text(encoding="utf-8"))
                elapsed_s = float(old.get("elapsed_s", 0))
            except Exception:
                elapsed_s = 0
        summary = _build_v63_summary(records, total_calls, total_disclosed, per_source_disclosed, per_source_n, stage_counts, elapsed_s, args.authorized_target_sha)
        # additive: only overwrite summary, never records
        sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"V63 summary repaired (additive, records preserved) -> {sum_path} overall {summary['overall_state']} accepted {summary['accepted']} exact {summary['exact']} undetected {summary['undetected']}")
        return 0

    if output_root.exists():
        print(f"BLOCKED: output root already exists: {output_root}", file=sys.stderr)
        return 2

    dc = domain_check(is_new_or_incompatible=False)
    if dc == "DOMAIN_CALIBRATION_REQUIRED":
        print("BLOCKED: DOMAIN_CALIBRATION_REQUIRED", file=sys.stderr)
        return 2

    if not DEV_REGISTRY.is_file():
        print(f"BLOCKED: dev registry missing {DEV_REGISTRY}", file=sys.stderr)
        return 2
    reg = json.loads(DEV_REGISTRY.read_text(encoding="utf-8"))
    entries = reg.get("entries", [])
    if len(entries) != 90:
        print(f"BLOCKED: dev registry must have 90 entries, got {len(entries)}", file=sys.stderr)
        return 2

    try:
        from comparison_bench.types import FrameBatch
        from comparison_bench.methods.nbldpc_shell_adapter import NbLdpcShellIRAdapter
    except Exception as exc:
        print(f"BLOCKED: import failed {exc}", file=sys.stderr)
        return 2

    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / "v63_records.json").write_text("[]", encoding="utf-8")

    records = []
    total_calls = 0
    total_disclosed = 0
    per_source_disclosed: dict[str, int] = {}
    per_source_n: dict[str, int] = {}
    stage_counts = {"base": 0, "delta8": 0, "delta16": 0}
    t0 = time.time()
    from collections import defaultdict
    by_source: dict[str, list] = defaultdict(list)
    for e in entries:
        by_source[e["source"]].append(e)

    def _load_entry(entry):
        src = entry["source"]
        fids = entry["frame_ids"]
        import numpy as np  # noqa: F401
        import pandas as pd
        parquet_map = {
            "1M": REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
            "1p5M": REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
            "2M": REPO_ROOT / "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
        }
        path = parquet_map[src]
        if not path.is_file():
            raise RuntimeError(f"EVIDENCE_INVALID: parquet missing {path} for {src}")
        try:
            df = pd.read_parquet(path)
        except Exception as exc:
            raise RuntimeError(f"EVIDENCE_INVALID: parquet read failed {path}: {exc}") from exc
        filt = df[df["frame_id"].isin(fids)].sort_values(["frame_id", "pair_idx"])
        alice = filt["alice_symbol"].to_numpy(dtype=np.int64)
        bob = filt["bob_symbol"].to_numpy(dtype=np.int64)
        if alice.size != 1024 or bob.size != 1024:
            raise RuntimeError(f"EVIDENCE_INVALID: row count {alice.size}/{bob.size} !=1024 for {entry['block_id']} {src} {fids}")
        return alice, bob

    try:
        for src, ents in by_source.items():
            alices = []
            bobs = []
            for e in ents:
                a, b = _load_entry(e)
                alices.append(a)
                bobs.append(b)
            import numpy as np
            alice_arr = np.stack(alices, axis=0)
            bob_arr = np.stack(bobs, axis=0)
            batch = FrameBatch(f"v63_dev_{src}", alice_arr, bob_arr, 1024, 1024, {"source": src})
            remaining = DEV_HARD_CAP - total_calls
            adapter = NbLdpcShellIRAdapter(src)
            shell = adapter.run_shell(batch, hard_cap=remaining)
            total_calls += shell.decoder_calls
            if total_calls > DEV_HARD_CAP:
                raise RuntimeError(f"hard cap {DEV_HARD_CAP} exceeded")
            total_disclosed += int(np.sum(shell.actual_disclosure_bits))
            per_source_disclosed[src] = per_source_disclosed.get(src, 0) + int(np.sum(shell.actual_disclosure_bits))
            per_source_n[src] = per_source_n.get(src, 0) + len(ents)
            for st in shell.stage_used:
                stage_counts[st] = stage_counts.get(st, 0) + 1
            _calls_map = {"base": 2, "delta8": 3, "delta16": 4}
            per_block_calls = [_calls_map[shell.stage_used[idx]] for idx in range(len(ents))]
            assert sum(per_block_calls) == int(shell.decoder_calls), f"EVIDENCE_INVALID decoder_calls sum {sum(per_block_calls)} != shell {shell.decoder_calls} stage_used {shell.stage_used}"
            for idx, e in enumerate(ents):
                records.append({
                    "block_id": e["block_id"],
                    "source": src,
                    "frame_ids": e["frame_ids"],
                    "stage_used": shell.stage_used[idx],
                    "leak_total": int(shell.actual_disclosure_bits[idx]),
                    "accepted": bool(shell.accepted[idx]),
                    "exact": bool(shell.exact[idx]),
                    "undetected": bool(shell.undetected[idx]),
                    "decoder_calls": int(per_block_calls[idx]),
                })
        assert sum(r["decoder_calls"] for r in records) == total_calls, f"EVIDENCE_INVALID global sum {sum(r['decoder_calls'] for r in records)} != total {total_calls}"
        if not (180 <= total_calls <= DEV_HARD_CAP):
            raise RuntimeError(f"budget violated: total_calls {total_calls} not in 180-360")
        elapsed = time.time() - t0
        summary = _build_v63_summary(records, total_calls, total_disclosed, per_source_disclosed, per_source_n, stage_counts, elapsed, args.authorized_target_sha)
        (output_root / "v63_records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        import csv
        if records:
            with (output_root / "v63_records.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
                w.writeheader()
                w.writerows(records)
        (output_root / "v63_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except BaseException as exc:
        notice = {"interrupted": True, "error": f"{type(exc).__name__}: {exc}", "total_calls": total_calls}
        (output_root / "v63_interrupted.json").write_text(json.dumps(notice, indent=2), encoding="utf-8")
        print(f"INTERRUPTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"V63 development evidence written to {output_root} total_calls {total_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
