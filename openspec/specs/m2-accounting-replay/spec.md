## Historical implemented scope — m2real-accounting-replay

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-m2real-accounting-replay-completed/specs/m2-accounting-replay/spec.md -->

## ACR-1 Actual disclosure

The replay SHALL compute actual EC disclosure efficiency from the arm's recorded `lambda_parts.leak_EC` divided by `superframes_done*1024*H_corr`; it SHALL retain the original nominal f labels separately and SHALL NOT present them as actual disclosure.

<!-- Source: openspec/changes/archive/2026-10-04-m2real-accounting-replay-completed/specs/m2-accounting-replay/spec.md -->

## ACR-2 Tag scope

The replay SHALL preserve the recorded per-block tag total, report its ratio, and report the one-tag-per-superframe ratio only as a counterfactual. It SHALL refuse a complete T3 summary whose block/superframe or tag/block counts conflict with the frozen 16×64 map.

<!-- Source: openspec/changes/archive/2026-10-04-m2real-accounting-replay-completed/specs/m2-accounting-replay/spec.md -->

## ACR-3 Claim ceiling and provenance

The replay SHALL read only explicit JSON paths, write only stdout, keep source/arm rows separate, and mark its output `DIAGNOSTIC_UNREVIEWED`. It SHALL NOT calculate `f_eff_actual`, evaluate D2, infer the real LB backend, rank method families, or alter the existing T3 artifacts.
