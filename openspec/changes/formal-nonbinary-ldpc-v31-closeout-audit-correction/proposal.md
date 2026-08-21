# Change A: formal-nonbinary-ldpc-v31-closeout-audit-correction

Status: P1 SPECIFICATION FREEZE — read-only except for creating new OpenSpec files in this change. No DE/decoder, no formal evidence generation, no canonical run_01 modification, no archived V31 OpenSpec modification, no old report modification, no commit/push.

## Summary

This change corrects the lifecycle labeling and historical description of V31 (`openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate`) without rewriting its evidence. V31's original archive lifecycle was mislabeled: it was archived as if globally complete/qualified when the underlying execution was structurally incomplete. This is an audit/closeout correction, NOT a numeric overturn.

## CRITICAL CORRECTION (must appear verbatim in all Change A docs)

> **V31 is ARCHIVED_PARTIAL**: `n=1024` is a full-window negative result (300/300 blocks, `finite_graph_fail`) and remains valid as a bounded negative result; `n=2048` is only a 14-block diagnostic prefix on source `1M` (not a full 50 blocks/source × 3 sources = 150-block validation), not a complete validation. The `bounded-prefix contingency` text now present in `gate.json` `closeout_note` is **POST-HOC** — added at the closeout stage — and **MUST NOT be described as pre-registered** retroactively. Under the original pre-registered requirement that **both n must pass** with full windows, a global `PASS` was impossible once `n=1024` fully failed, regardless of `n=2048` completeness; the original complete execution is incomplete (`n=2048` truncated) and therefore global PASS possibility was never restored. This correction is audit-only and does not overwrite history.

Specific corrections:
- **Original archive lifecycle mislabel (not numeric overturn)**: V31 was archived with an implicit "complete execution → terminal final" lifecycle. The audit corrects the label to `ARCHIVED_PARTIAL` because `n=2048` never reached its pre-registered full window. No FER, syndrome, or leakage numbers are overturned.
- **`n=1024` negative result remains valid**: 300 blocks (100/source × 3 sources), exact=0/tag=0/false_accept=0 on accepted QC family, syndrome convergence 0.00, PEG family deterministically rejected for rank deficiency. This bounded negative result (tested deterministic families + frozen decoder) is preserved.
- **`n=2048` only bounded diagnostic prefix**: exactly 14 blocks on `type2_1M_20260121_184040` source, all QC, exact=0/tag=0, pattern `converged_no_syndrome`. `type2_1p5M` and `type2_2M` at `n=2048` were not executed. Not a full gate.
- **Post-hoc contingency cannot be called pre-registered retroactively**: `design.md §5` contingency and `gate.json` `closeout_note` bounded-prefix language were added at closeout, after the 300/300 `n=1024` failure was known. Describing them as pre-registered violates the original pre-registration. Change A freezes this post-hoc status explicitly.
- **Additive verifier/evidence, no rewrite history**: Change A adds an independent read-only verifier v2 and additive evidence under a new isolated output root. It does not edit `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/**`, does not edit `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**`, does not edit `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` or `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md`.
- **Change A success != V31 qualification nor restores PASS possibility**: Passing Change A means the closeout audit itself is consistent and correctly labeled. It does not qualify V31, does not promote it, and does not restore a global `finite_graph_pass` possibility under the original both-n requirement (which remains impossible).

## Goals (exactly 3)

1. **Correct lifecycle label/history**: Externally label V31 as `ARCHIVED_PARTIAL` and freeze the corrected historical narrative (n=1024 full-window `finite_graph_fail`, n=2048 bounded 14-block diagnostic prefix only, closeout_note contingency post-hoc, global PASS impossible, original complete execution incomplete) in `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` and `docs/decision-log.md` after acceptance, without rewriting canonical artifacts.
2. **New independent read-only verifier v2**: Implement `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py` that operates read-only on the canonical run_01 (distrusts `gate.json` terminal and old `readonly_verify.json` ok), recomputes all counts/rates from raw persisted records, and writes only to the new additive root. No DE, no decoder, no production runner invocation.
3. **Additive evidence, no overwrite**: Generate exactly one additive audit evidence tree at `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/*` via test-only fake runs plus one real recount over the canonical 16 files (additive only), proving the verifier and terminal priority logic while keeping the 16 canonical files byte-identical.

## Non-Goals (exactly 8)

1. No numeric overturn of V31 FER/syndrome/leakage — n=1024 0/300 remains.
2. No completion of the missing n=2048 1p5M/2M blocks or extension of the 14-block prefix to a full window.
3. No re-execution of DE (`nbldpc_v26` confirmation) or decoder (`run_nonbinary_v31_gate` M3) and no invocation of any production runner.
4. No modification of canonical `run_01` 16 files (`gate.json`, `readonly_verify.json`, `per_block_*`, `summary_*`, `matrix_*`, `validation_*`, `de_confirmation.json`, `m1_registry.json`, `progress.json`, `RUN_MANIFEST.json`).
5. No modification of `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**`.
6. No modification of `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` or `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md` (only new addendum is allowed).
7. No modification of frozen baseline `src/**`, `experiments/**`, `tools/**` (original Polar pipeline).
8. No qualification, promotion, V29 holdout, raw `.ttbin` residual claim, or commit/push during specification freeze (commit only after main ACCEPT in task A11).

## Evidence Citations (P0 inventory — TRUST, do not re-explore)

- Canonical `run_01`: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` — **16 files** exactly:
  `de_confirmation.json`, `gate.json`, `m1_registry.json`, `matrix_audits.json`, `matrix_payloads.json`, `per_block_n1024.jsonl`, `per_block_n2048.jsonl`, `progress.json`, `readonly_verify.json`, `RUN_MANIFEST.json`, `summary_n1024.json`, `summary_n2048.json`, `validation_blocks_n1024.json`, `validation_blocks_n2048.json`, `validation_frames_n1024.json`, `validation_frames_n2048.json`
- Gate terminal: `gate.json` `finite_graph_fail` (verifier `ok=true`, `problems=[]` in old `readonly_verify.json`, but verifier v2 MUST distrust and recompute)
- `n=1024`: 300/300 blocks full window (100/source × 3 sources), QC `exact=0 tag=0 false_accept=0`, syndrome 0.00, PEG deterministically rejected (rank-deficient)
- `n=2048`: 14-block **1M only** diagnostic prefix (`per_block_n2048.jsonl` 14 records), QC only, `exact=0 tag=0`, `converged_no_syndrome`, 1p5M/2M not run; `summary_n2048.json` reflects bounded prefix only
- `gate.json` `closeout_note` bounded-prefix contingency = **POST-HOC** (added at closeout, not pre-registered); `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` §n=2048 bounded prefix (design §5 contingency) is post-hoc
- Archive: `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/` (proposal.md, design.md, tasks.md, specs/, archive_note.md)
- Original reports/plans: `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`, `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md`
- Git: HEAD `c8d2acabccaae9d55a344e8f0c8ac1bb21ff9d1e`, branch `main`, tracked clean

## Allowed New Files (only after main ACCEPT, additive only)

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py` — verifier v2 (read-only)
- `comparison_bench/tests/test_nonbinary_v31_closeout_audit.py` — T0/T1/T2 tests
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/*` — additive audit evidence (closeout_verify.json, closeout_recount.json, closeout_gate.json, RUN_MANIFEST equivalent, tamper logs)
- `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` — addendum freezing corrected label/history (only after ACCEPT)

Any other new file requires explicit main approval.

## Forbidden (MUST NOT be overwritten/edited at any stage)

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/**` (canonical 16 files, byte-identical)
- `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**`
- `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`
- `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md`
- `src/**`, `experiments/**`, `tools/**` (frozen baseline)
- No `results/**` or `comparison_bench/outputs_comparison/**` outside the single new `nbldpc_v31_closeout_audit_v2` root

## C01–C18 Acceptance Matrix (frozen — ACCEPT/REJECT per item by main in A9)

| ID | Criterion | Source of Truth | Verifier v2 Check (read-only recompute) |
|---|---|---|---|
| C01 | Canonical 16 files byte-identical (count, names, hashes) | `run_01/` file listing | Count=16, names exact, SHA-256 byte-identical vs frozen manifest; fail → closeout_verifier_blocked |
| C02 | V31 externally labeled ARCHIVED_PARTIAL | This proposal + addendum | Addendum states ARCHIVED_PARTIAL with n1024 full fail + n2048 prefix-only definition |
| C03 | Bounded-prefix contingency declared POST-HOC (not pre-registered) | `gate.json` closeout_note, design §5 | Verifier reports contingency_post_hoc=true; addendum never claims pre-registered |
| C04 | Block counts independently recounted: n1024 300/300, n2048 14/1M-only | `per_block_n1024.jsonl` (300), `per_block_n2048.jsonl` (14) | Re-count JSONL lines; n1024 100/source, n2048 14 on 1M, 0 on 1p5M/2M |
| C05 | exact/tag/false_accept independently recounted (not trusted summary) | `per_block_*.jsonl` per-record fields | Sum exact/tag/false_accept per source; n1024 0/0/0 on QC, n2048 0/0/0 on 14 |
| C06 | Syndrome convergence independently recounted; failure positions verified | `per_block_*.jsonl` syndrome, L1/L2 converged flags | Recompute syndrome_conv rate, verify all 300 n1024 + 14 n2048 are `converged_no_syndrome` L2 fails |
| C07 | Runtime recomputed from per-block records (not resume meter zero) | `per_block_*.jsonl` runtime fields | Sum runtime per block; ignore progress.json resume meter; report total wall-clock proxy |
| C08 | Accepted QC packet evidence verified (full-rank, occupancy≤31, projective-safe) | `matrix_audits.json`, `matrix_payloads.json` | Verify QC n1024/n2048 accepted: full rank, max occupancy ≤31 (e.g., 9 at n1024), no duplicate/proportional keys |
| C09 | Rejected PEG evidence verified (rank-deficient, deterministic) | `matrix_audits.json` PEG entries | Verify PEG L2 REJECT: rank 199/200, 413/414 etc., deterministic; no replacement |
| C10 | Downgrade if manifest missing (graceful, not hard pass) | `RUN_MANIFEST.json` presence | If manifest missing, downgrade to closeout_evidence_inconsistent with explicit problem; do not claim ok |
| C11 | Input bindings checked (V25/V26/V28R/V30R paths, field, H float64, allocation) | `RUN_MANIFEST.json`, `de_confirmation.json`, `m1_registry.json` | Verify field_id `c3a3660...`, H float64 exact, m1=16, m_total/leak/f_total tables |
| C12 | Code identity checked (git commit c8d2acab, file hashes for audit runner) | `git rev-parse HEAD`, source file hashes | Record HEAD c8d2acabccaae9d55a344e8f0c8ac1bb21ff9d1e and verifier source SHA |
| C13 | No DE/decoder execution (no_de_rerun && no_decoder_rerun) | Verifier implementation | Static check: verifier imports no DE/decoder, no subprocess to `run_nonbinary_v31_gate` |
| C14 | All new output under independent additive root only | Filesystem | All writes under `nbldpc_v31_closeout_audit_v2/run_01/`; zero writes to `nbldpc_v31_20260820/run_01/` |
| C15 | Layered tamper tests pass (T1 11 items) | `test_nonbinary_v31_closeout_audit.py` T1 | Raw drift + semantic self-hash + manifest links + deep reconstruction (see design) |
| C16 | Independently reviewed by non-implementer (reviewer-go) | Reviewer report | Reviewer is not implementer; performs read-only T0/T1/T2, publishes findings |
| C17 | Addendum + decision-log + AGENT_PROJECT_MEMORY handoff after ACCEPT | `docs/` + memory | Addendum created only after ACCEPT; decision-log entry and memory handoff complete |
| C18 | Local commit only after ACCEPT, no push, no production overwrite | `git status` | Commit includes only Change A files + addendum/decision-log/memory; no canonical overwrite; no push |

All C01–C18 must be ACCEPT for terminal `closeout_corrected`; any FAIL maps via Terminal Priority (design §5).

## Testing Tiers

- **T0 — structural**: `python -m py_compile` verifier, `pytest -q -p no:cacheprovider` import/structural, tiny-math (allocation f_total<1.3, H float64 exact, field_id). No I/O beyond canonical read.
- **T1 — focused tamper (11 items)**: raw byte drift (16 files), semantic self-hash (RUN_MANIFEST/matrix_payloads per-record hash), manifest/index links (validation_frames ↔ validation_blocks ↔ per_block), deep source/transcript/public-payload/leakage/accounting/gate reconstruction. Must pass before any evidence generation.
- **T2 — full fake closeout qualification + strict recount**: run verifier on synthetic fake `run_01` fixtures (fabricated 16-file trees with known 300/14 counts) in `workspace/<task>/<uuid>` via fake runner; then one strict read-only recount over real canonical `run_01` but writing additive output only. Replay must be strict (re-running verifier on additive output yields identical closeout_verify).
- **T3 — cross-version/broad regression**: NOT needed for Lite (Change A is audit-only, no sweep). Deferred; would compare V25/V26/V28R/V30R/V31 bindings if broad regression were requested.

T2/T3 only at milestones (A6–A8). No production DE/decoder in any tier (fake runner only for synthetic fixtures).

## Role Isolation

- **Implementation (coder-fast)**: owns A3–A7 — writes verifier v2 and tests, runs T0/T1/T2, delivers candidate. Must not mark ACCEPT/REJECT.
- **Independent Review (reviewer-go)**: owns A8 — read-only T0/T1/T2 verification, publishes findings, checks frozen directories/hashes and absence of unauthorized output. Must not be the implementer.
- **Main (orchestrator/planner)**: owns A1–A2 specification freeze review, A9 C01–C18 ACCEPT/REJECT per item, A10–A12 closeout decisions. Only main can ACCEPT.

## Stop Conditions

- Stop and return to planner if: any canonical 16-file hash mismatch, any C01–C18 ambiguity, any temptation to edit canonical/archive/old reports, any DE/decoder execution path detected, any write outside additive root, or any global PASS claim.
- Do not mark tasks complete without evidence: each A* checkbox requires command output or file hash citation.

## Impact Scope

- `openspec/changes/formal-nonbinary-ldpc-v31-closeout-audit-correction/**` (new)
- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py` (new, after ACCEPT)
- `comparison_bench/tests/test_nonbinary_v31_closeout_audit.py` (new, after ACCEPT)
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/**` (new, after ACCEPT)
- `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` (new, after ACCEPT)
- `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md` (addendum entries only after ACCEPT)

No impact on `src/**`, `experiments/**`, `tools/**`, or `results/**`.
