# Spec: formal-nonbinary-ldpc-v31-closeout-audit-correction

## Scope

This delta spec freezes the **closeout audit correction** for V31. It does not modify V31's numeric results, does not complete the missing n=2048 execution, and does not re-execute any DE/decoder. It adds an independent read-only verifier v2 and additive evidence under an isolated output root, and corrects the external lifecycle label/history of V31 to `ARCHIVED_PARTIAL`.

In scope:
- Correcting V31 lifecycle label from implicit "complete" to `ARCHIVED_PARTIAL` and freezing the corrected historical narrative in an addendum.
- Implementing `run_nonbinary_v31_closeout_audit.py` (verifier v2) and `test_nonbinary_v31_closeout_audit.py` with T0/T1/T2 verification.
- Generating additive audit evidence at `nbldpc_v31_closeout_audit_v2/run_01/` via one fake-tree qualification plus one real read-only recount (additive only).

Out of scope:
- Numeric overturn of n=1024 FER/syndrome (remains 0/300 `finite_graph_fail`).
- Completion of n=2048 1p5M/2M or extension of 14-block prefix.
- DE/decoder re-execution, production runner invocation, or canonical 16-file modification.
- Editing `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**`, `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`, `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md`, or `src/**`/`experiments/**`/`tools/**`.

## Definitions

- **Canonical `run_01`**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` containing exactly 16 files: `de_confirmation.json`, `gate.json`, `m1_registry.json`, `matrix_audits.json`, `matrix_payloads.json`, `per_block_n1024.jsonl`, `per_block_n2048.jsonl`, `progress.json`, `readonly_verify.json`, `RUN_MANIFEST.json`, `summary_n1024.json`, `summary_n2048.json`, `validation_blocks_n1024.json`, `validation_blocks_n2048.json`, `validation_frames_n1024.json`, `validation_frames_n2048.json`.
- **ARCHIVED_PARTIAL**: terminal lifecycle label meaning implementation complete but full frozen pre-registered execution incomplete; externally, V31 is `ARCHIVED_PARTIAL` with `n=1024` full-window `finite_graph_fail` (300/300) and `n=2048` bounded 14-block diagnostic prefix only; global `PASS` impossible under original both-n requirement.
- **Post-hoc contingency**: the `bounded-prefix contingency` text in `gate.json` `closeout_note` and `design.md §5`, added at closeout after n=1024 failure was known; MUST NOT be described as pre-registered.
- **Verifier v2**: `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py` — read-only, distrusting `gate.json` terminal and old `readonly_verify.json` ok, recomputing from raw `per_block_*.jsonl` and `matrix_audits.json`.
- **Additive root**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/` — sole writable output for this change.
- **Closeout terminals** (priority `closeout_evidence_inconsistent > closeout_verifier_blocked > closeout_corrected`): only `closeout_corrected` indicates a consistent, completed audit; others block publication/archiving.

## Constraints

- No DE, decoder, or production runner (`run_nonbinary_v31_gate`, `longrun_*`, `minrerun_*`, `routeA_*`, `experiments/run_e2e_pipeline.py`) SHALL be executed in any tier; synthetic T2 fixtures SHALL use an explicit fake runner.
- No file under canonical `run_01` SHALL be written, and its 16 files SHALL remain byte-identical (hash-verified).
- No file under `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**` SHALL be edited.
- No old report/plan (`docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`, `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md`) SHALL be edited; only `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` is additive and only after main ACCEPT.
- All new output SHALL be under the additive root; verifier SHALL refuse to start if input and output resolve to the same directory.
- `ponytail:` simplifications in verifier (naive O(n) scan, no cache) SHALL be marked and SHALL name the upgrade path if a ceiling exists.

## Requirements — Verifier & Audit (SHALL)

### Preservation

- **SHALL-C01** — The system SHALL keep the canonical 16 files byte-identical: count=16, names exact, SHA-256 identical to the frozen manifest before and after the audit. Any mismatch SHALL cause `closeout_verifier_blocked` (C01 FAIL).
- **SHALL-C02** — The system SHALL label V31 externally as `ARCHIVED_PARTIAL` in `proposal.md`, `design.md`, `closeout_gate.json`, and `docs/nbldpc-v31-closeout-audit-addendum-20260821.md`, with the exact definition `n=1024` full-window `finite_graph_fail` + `n=2048` bounded prefix only + global PASS impossible + original complete execution incomplete.
- **SHALL-C03** — The system SHALL state the bounded-prefix contingency (design §5 / `gate.json` closeout_note) is **post hoc** (added at closeout stage) and SHALL NOT describe it as pre-registered, in all docs and in `closeout_gate.json:contingency_post_hoc=true`.

### Independent Recount

- **SHALL-C04** — The verifier SHALL independently recount block counts from raw `per_block_*.jsonl` (not from `summary_*.json`): `n=1024` exactly 300 lines (100/source × 3: `type2_1M`/`type2_1p5M`/`type2_2M`), `n=2048` exactly 14 lines on `type2_1M_20260121_184040` and 0 on the other two sources.
- **SHALL-C05** — The verifier SHALL independently recount `exact`, `tag`, `false_accept` per source from per-record fields (not summary): `n=1024` 0/0/0 on accepted QC across all 300, `n=2048` 0/0/0 on 14.
- **SHALL-C06** — The verifier SHALL independently recount syndrome convergence and failure positions: recompute syndrome_conv rate from per-block `converged` flags, verify all 300 n=1024 + 14 n=2048 are L2 `converged_no_syndrome` failures with 0 false accepts, and rebuild waterfall as identically 0.
- **SHALL-C07** — The verifier SHALL independently recompute runtime from per-block `runtime` fields (wall-clock proxy) and SHALL NOT use `progress.json` resume-meter zero as ground truth; it SHALL report summed runtime and ignore resume offsets.

### Packet Evidence

- **SHALL-C08** — The verifier SHALL verify the accepted QC packet evidence: `matrix_audits.json` QC entries for n=1024 and n=2048 are full-rank, max support occupancy ≤31 (e.g., 9 at n=1024), zero duplicate projective keys, zero proportional pairs, first coefficient 1, and SHALL cross-check `matrix_payloads.json` hash consistency (C08).
- **SHALL-C09** — The verifier SHALL verify the rejected PEG packet evidence: `matrix_audits.json` PEG L2 entries are deterministically `REJECT` with rank-deficient (e.g., m=184→rank 199 at n=1024, m=414→rank 413 at n=2048), and SHALL NOT permit replacement or seed change (C09).
- **SHALL-C10** — If `RUN_MANIFEST.json` is missing, the verifier SHALL downgrade gracefully to `closeout_evidence_inconsistent` with explicit `problem="manifest_missing"` and SHALL NOT claim `ok` (C10).

### Bindings & Identity

- **SHALL-C11** — The verifier SHALL check input bindings: `GF2mField.create(32)` poly `0b100101` `field_id=c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, `ratio_index` zero-based, V25/V26/V28R/V30R paths, `H_L1`/`H_L2`/`H_total` float64 exact per source, and allocation table (`m1=16`, `m_total` n=1024 {200,206,208} n=2048 {413,426,430}, `leak=5*m+64`, `f_total<1.3`) via `RUN_MANIFEST.json`/`de_confirmation.json`/`m1_registry.json` (C11).
- **SHALL-C12** — The verifier SHALL check code identity: record `git rev-parse HEAD` equals `c8d2acabccaae9d55a344e8f0c8ac1bb21ff9d1e` (or successor after allowed commit) and record verifier source SHA in `closeout_run_manifest.json` (C12).

### Read-Only & Isolation

- **SHALL-C13** — The verifier SHALL NOT execute DE/decoder: it SHALL NOT import `formal_ir.nonbinary_v31`, SHALL NOT call `run_nonbinary_v31_gate`, and SHALL NOT spawn any production runner; static `grep` for these strings in the verifier file SHALL be empty (C13). Property `no_de_rerun=true` and `no_decoder_rerun=true` in `closeout_verify.json`.
- **SHALL-C14** — The verifier SHALL write all new output to the independent additive root `nbldpc_v31_closeout_audit_v2/run_01/` and SHALL write zero bytes to `nbldpc_v31_20260820/run_01/`; any write outside the additive root SHALL be a hard failure (C14).

### Tamper & Review

- **SHALL-C15** — The system SHALL pass layered tamper tests T1-01..T1-11 (design §7): raw byte drift, semantic self-hash (RUN_MANIFEST, per_block JSONL per-record hash), manifest/index links, matrix payload↔audit consistency, summary recomputed from JSONL, gate terminal recomputed, deep source/transcript/public-payload/leakage/accounting/gate reconstruction. All 11 SHALL PASS for `closeout_corrected` (C15).
- **SHALL-C16** — The system SHALL be independently reviewed by a non-implementer (`reviewer-go`): reviewer SHALL perform read-only T0/T1/T2 verification, check frozen-directory diffs, and publish findings without editing files (C16).
- **SHALL-C17** — After main ACCEPT with `closeout_corrected`, the system SHALL create `docs/nbldpc-v31-closeout-audit-addendum-20260821.md`, append to `docs/decision-log.md`, and perform memory handoff to `AGENT_PROJECT_MEMORY.md` (C17).
- **SHALL-C18** — The system SHALL commit locally only after ACCEPT, with only allowed new files + addendum/decision-log/memory in the commit, and SHALL NOT push or overwrite production outputs (C18).

### Terminal Priority

- **SHALL-TERM** — The system SHALL classify the closeout terminal by priority `closeout_evidence_inconsistent > closeout_verifier_blocked > closeout_corrected` (design §5 code block). Only when evidence is internally consistent AND verifier completes AND C01–C18 all ACCEPT SHALL terminal be `closeout_corrected`; otherwise it SHALL be one of the higher-priority failure terminals.

## Acceptance Mapping

| Requirement | C* | Verified by |
|---|---|---|
| Preservation | SHALL-C01..C03 | T0 file count/hash, addendum content grep, closeout_gate.json fields |
| Recount | SHALL-C04..C07 | T1-04/T1-06 + closeout_recount.json recomputed values |
| Packet | SHALL-C08..C10 | T1-05/T1-09/T1-11 + matrix audits cross-check |
| Bindings/Identity | SHALL-C11..C12 | T0 tiny-math + closeout_run_manifest.json |
| Isolation | SHALL-C13..C14 | T0 grep + filesystem write-path assertion |
| Tamper/Review | SHALL-C15..C18 | T1 11 items + reviewer report + git log |

## Evidence Outputs (additive only)

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/closeout_verify.json` — C01–C18 per-item verdicts, terminal priority result, `no_de_rerun`/`no_decoder_rerun` flags
- `.../closeout_recount.json` — recomputed counts/rates from raw JSONL (block counts, exact/tag/false_accept, syndrome, waterfall, runtime)
- `.../closeout_gate.json` — corrected terminal block (§3 definition), `contingency_post_hoc=true`, `original_complete_execution=incomplete`, `global_pass_possible=false`
- `.../closeout_run_manifest.json` — audit run manifest (git HEAD, verifier SHA, input file hashes)
- `.../tamper_log.json` / `.../strict_replay_log.json` — T1/T2 logs

All SHALL be additive; none SHALL overwrite canonical `run_01`.
