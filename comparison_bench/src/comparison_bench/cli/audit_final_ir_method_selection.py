from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..final_selection_audit import audit, route_a_gate


def _matches_persisted(expected: object, persisted: object) -> bool:
    """Allow an older healthy audit to omit later empty diagnostic fields."""
    if isinstance(expected, dict) and isinstance(persisted, dict):
        return all(key in expected and _matches_persisted(expected[key], value) for key, value in persisted.items())
    return expected == persisted


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only Phase-4 audit for final IR method selection.")
    ap.add_argument("--v1-dir", default="comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1")
    ap.add_argument("--v2-dir", default="comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v2")
    ap.add_argument("--output-dir", default="comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit")
    ap.add_argument("--verify", action="store_true", help="read and revalidate the existing audit without writing files")
    args = ap.parse_args()
    out = Path(args.output_dir)
    result, gate = audit(Path(args.v1_dir), Path(args.v2_dir)), route_a_gate()
    if args.verify:
        decision = {key: result[key] for key in ("decision", "decision_reason", "alpha", "exact_two_sided_p_value", "paired_outcomes", "domain", "non_claims")}
        required = {"audit_manifest.json": result, "paired_decision.json": decision,
                    "route_a_compatibility_gate.json": gate, "immutable_hash_ledger.json": result["hash_ledger"]}
        for name, expected in required.items():
            path = out / name
            if not path.is_file() or not _matches_persisted(expected, json.loads(path.read_text(encoding="utf-8"))):
                raise SystemExit(f"audit verification failed: {path}")
        print(f"verified {out}; {result['decision']} p={result['exact_two_sided_p_value']:.6g}; route_a_gate={gate['gate']}")
        return 0
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing audit output: {out}")
    out.mkdir(parents=True)
    (out / "audit_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision = {key: result[key] for key in ("decision", "decision_reason", "alpha", "exact_two_sided_p_value", "paired_outcomes", "domain", "non_claims")}
    (out / "paired_decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "route_a_compatibility_gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paired = result["paired_outcomes"]
    status = result["status_counts"]
    cascade_success = status["cascade_lite"].get("verified_success", 0)
    ldpc_success = status["layered_ldpc_lite"].get("verified_success", 0)
    required_frames = result["frame_identity"]["locked_confirmation_unique_keys"]
    lines = ["# Phase 4 audit decision", "", f"Decision: **{result['decision']}** (exact two-sided paired p={result['exact_two_sided_p_value']:.6g}; alpha={result['alpha']}).", "",
             f"Cascade has {cascade_success}/{required_frames} and Layered LDPC {ldpc_success}/{required_frames} independently verified successes; paired discordances are Cascade-only={paired['cascade_only_success']}, LDPC-only={paired['layered_ldpc_only_success']}.", "",
             "Leakage is preserved as method-specific disclosure accounting and is not cross-method ranked.", "",
             f"Route A documented-field compatibility gate: **{gate['gate']}**; no numerical Route A rerun was performed.", "", "## Supported domain", "", json.dumps(result["domain"], indent=2), "", "## Non-claims", ""] + [f"- {x}" for x in result["non_claims"]]
    (out / "decision_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "immutable_hash_ledger.json").write_text(json.dumps(result["hash_ledger"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{result['decision']} p={result['exact_two_sided_p_value']:.6g}; route_a_gate={gate['gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
