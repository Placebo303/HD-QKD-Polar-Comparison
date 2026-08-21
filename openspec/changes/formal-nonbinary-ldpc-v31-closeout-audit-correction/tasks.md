# Tasks: formal-nonbinary-ldpc-v31-closeout-audit-correction

> Do NOT mark any task complete without evidence (command output, file hash, or reviewer report). Checkbox format. P1 freeze is read-only for spec; implementation starts only at A3 after main review.

## Allowed New Files (only after main ACCEPT in A9)

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py`
- `comparison_bench/tests/test_nonbinary_v31_closeout_audit.py`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01/*` (closeout_verify.json, closeout_recount.json, closeout_gate.json, closeout_run_manifest.json, tamper_log.json, strict_replay_log.json)
- `docs/nbldpc-v31-closeout-audit-addendum-20260821.md`

## Forbidden (MUST NOT be edited at any stage)

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/**` (canonical 16 files byte-identical)
- `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**`
- `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`
- `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md`
- `src/**`, `experiments/**`, `tools/**` (frozen Polar baseline)

## C01–C18 Matrix (frozen — same as proposal.md)

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
| C15 | Layered tamper tests pass (T1 11 items) | `test_nonbinary_v31_closeout_audit.py` T1 | Raw drift + semantic self-hash + manifest links + deep reconstruction (see design §7) |
| C16 | Independently reviewed by non-implementer (reviewer-go) | Reviewer report | Reviewer is not implementer; performs read-only T0/T1/T2, publishes findings |
| C17 | Addendum + decision-log + AGENT_PROJECT_MEMORY handoff after ACCEPT | `docs/` + memory | Addendum created only after ACCEPT; decision-log entry and memory handoff complete |
| C18 | Local commit only after ACCEPT, no push, no production overwrite | `git status` | Commit includes only Change A files + addendum/decision-log/memory; no canonical overwrite; no push |

## Testing Tiers (frozen)

- **T0 — structural**: `python -m py_compile` verifier, `pytest -q -p no:cacheprovider` import/structural, tiny-math (allocation f_total<1.3, H float64 exact, field_id). No I/O beyond canonical read.
- **T1 — focused tamper (11 items)**: raw byte drift (16 files), semantic self-hash (RUN_MANIFEST/matrix_payloads per-record hash), manifest/index links (validation_frames ↔ validation_blocks ↔ per_block), deep source/transcript/public-payload/leakage/accounting/gate reconstruction. Must pass before any evidence generation.
- **T2 — full fake closeout qualification + strict recount**: synthetic fake `run_01` fixtures via fake runner in `workspace/<task>/<uuid>` (fabricated 16-file trees with known 300/14 counts) + one strict read-only recount over real canonical `run_01` but writing additive output only. Strict replay: re-running verifier on additive output yields identical closeout_recount.
- **T3 — cross-version/broad regression**: NOT needed for Lite (Change A is audit-only, no sweep). Deferred.

T2/T3 only at milestones (A6–A8). No production DE/decoder in any tier (fake runner only for synthetic fixtures).

## Role Isolation (frozen)

- **Implementation → coder-fast**: owns A3–A7, must not mark ACCEPT/REJECT.
- **Review → reviewer-go (independent, not implementer)**: owns A8 read-only T0/T1/T2 verification.
- **Main (orchestrator/planner)**: owns A1–A2 spec review, A9 C01–C18 ACCEPT/REJECT, A10–A12 closeout decisions. Only main can ACCEPT.

## Stop Conditions (frozen)

- Any canonical 16-file hash mismatch → stop, return to planner.
- Any write outside additive root detected → stop.
- Any DE/decoder import or subprocess call in verifier → stop.
- Any edit to canonical/archive/old reports/`src/**`/`experiments/**`/`tools/**` → stop.
- Any claim that bounded-prefix contingency is pre-registered or that V31 global PASS is restored → stop.
- Any C01–C18 ambiguity uncovered → stop and return to planner; do not guess.

---

### A1 — Freeze OpenSpec and C01–C18

- [x] A1.1 Create `openspec/changes/formal-nonbinary-ldpc-v31-closeout-audit-correction/` with `proposal.md`, `design.md`, `tasks.md`, `specs/formal-nonbinary-ldpc-v31-closeout-audit-correction/spec.md` per P1 spec.
- [x] A1.2 Verify proposal states: lifecycle mislabel (not numeric overturn), n1024 valid, n2048 prefix-only, post-hoc not pre-registered, additive no-rewrite, Change A success ≠ V31 qualification nor restores PASS.
- [x] A1.3 Verify proposal/design/tasks all contain identical Allowed new files (4), Forbidden list, C01–C18 matrix (18 rows), T0/T1/T2/T3 tiers, role isolation, stop conditions.
- [x] A1.4 Verify design has ≥5 sections with code blocks for lifecycle model (§2), correct terminal (§3), terminal priority (§5), plus input binding table, verification strategy, evidence root segregation.
- [x] A1.5 Verify spec uses SHALL statements and freezes all items in §Scope (see spec.md).
- **Evidence**: `ls` of new change directory, `grep -c SHALL specs/**/spec.md`, `diff` of C01–C18 tables across proposal/design/tasks.
- **Done when**: all four files exist and `grep` checks above pass.

### A2 — Main Specification Review

- [x] A2.1 Main reviews proposal/design/tasks/spec for fidelity to P1 spec, lifecycle correctness (ARCHIVED_PARTIAL, post-hoc, global PASS impossible), and scientific semantics.
- [x] A2.2 Main verifies no forbidden file is listed as allowed, no DE/decoder execution is implied, no canonical overwrite is authorized.
- [x] A2.3 Main records review outcome (ACCEPT spec or REJECT with required fixes) in task comments or `docs/decision-log.md` draft.
- **Evidence**: review checklist with per-section PASS/FAIL, reviewer identity = main (not coder-fast).
- **Done when**: main marks A2 ACCEPT.

### A3 — Implementation Agent Implements Verifier v2

- [x] A3.1 `coder-fast` implements `comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py` per design §4 (read-only, distrust gate/old verify, recompute from JSONL, no DE/decoder, additive output only, rerun fields declarative).
- [x] A3.2 `coder-fast` implements `comparison_bench/tests/test_nonbinary_v31_closeout_audit.py` covering T0/T1/T2 contracts (fake runner for synthetic fixtures, never production decoder).
- [x] A3.3 Verifier statically grep-clean: `grep -r "nonbinary_v31\|run_nonbinary_v31_gate\|formal_ir" comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py` must be empty; `grep -r "subprocess.*run_nonbinary" ...` empty.
- **Evidence**: `git diff --stat` shows only the two new files under allowed paths; `grep` outputs empty.
- **Done when**: both files exist and static checks pass.

### A4 — Implementation T0 (structural)

- [x] A4.1 `python -m py_compile comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py`
- [x] A4.2 `pytest -q comparison_bench/tests/test_nonbinary_v31_closeout_audit.py -k t0 -p no:cacheprovider` — import, tiny-math, field_id, allocation f_total<1.3, file count=16 structural checks.
- [x] A4.3 Verify canonical `run_01` exists and has exactly 16 files with expected names (no hash check yet, just structural).
- **Evidence**: `py_compile` exit 0, `pytest -k t0` log with PASSED, `ls run_01 | wc -l` =16.
- **Done when**: T0 PASSED.

### A5 — Implementation T1 Tamper Tests (11 items)

- [x] A5.1 Run `pytest -q -p no:cacheprovider -k t1` — all 11 layered tamper tests (design §7: T1-01..T1-11).
- [x] A5.2 Verify each T1 item reports PASS/FAIL individually in `tamper_log.json` under `workspace/<task>/<uuid>` (fresh additive `workspace/...` root on Windows, `pytest -p no:cacheprovider`).
- [x] A5.3 Confirm no canonical write: `git diff -- comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` empty.
- **Evidence**: `pytest -k t1` log 11 passed, `tamper_log.json` with 11 entries, `git diff` empty.
- **Done when**: all 11 T1 PASS and no canonical drift.

### A6 — Implementation Generate One Additive Audit Evidence (test-only + one real recount but additive)

- [x] A6.1 **Test-only**: run verifier with `--fake-root workspace/<task>/<uuid>/fake_run_01` on synthetic fixtures (fabricated 300/14 JSONL, fake matrix audits) producing `workspace/.../fake_run_01/closeout_*` — proves verifier logic without touching canonical.
- [x] A6.2 **One real recount but additive**: run verifier once over real canonical `run_01` (`--input comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01 --output comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_01`) producing `closeout_verify.json`, `closeout_recount.json`, `closeout_gate.json`, `closeout_run_manifest.json`. This is a read-only recount, not a DE/decoder rerun.
- [x] A6.3 Verify output file list is exactly the additive set (4–6 files) and no file under canonical `run_01` was modified (check mtimes/hashes before vs after).
- **Evidence**: `ls` of fake output, `ls` of additive `run_01`, before/after hash manifest for canonical 16 files identical, `cat closeout_gate.json` shows ARCHIVED_PARTIAL + post-hoc + global_pass_possible:false.
- **Done when**: fake evidence + one additive real recount exist, canonical hashes unchanged.

### A7 — Candidate Delivery

- [x] A7.1 Implementation agent delivers candidate as frozen file set: verifier v2, tests, one additive evidence tree, plus transcript of T0/T1/T2 runs. No ACCEPT claim.
- [x] A7.2 Implementation agent reports delta only: changed files (`git status`), commands/results, remaining frozen items (none, or explicit blocker with failing command + traceback + decision needed).
- [x] A7.3 Implementation agent asserts no production work was invoked implicitly from tests (fake runner explicitly passed for synthetic; real recount explicitly passed as additive read-only).
- **Evidence**: candidate manifest (file list + SHA), command log, `git status` delta.
- **Done when**: candidate manifest + logs delivered to main.

### A8 — Independent Reviewer Read-Only T0/T1/T2

- [x] A8.1 `reviewer-go` (not the implementer) performs read-only `pytest -q -p no:cacheprovider -k "t0 or t1"` over the candidate.
- [x] A8.2 `reviewer-go` performs read-only `pytest -q -p no:cacheprovider -k t2` — full fake closeout qualification + strict recount replay (re-running verifier on additive output yields identical recount).
- [x] A8.3 `reviewer-go` checks frozen directories/source hashes: `git diff -- comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` empty, `git diff -- openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/` empty, `git diff -- docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` empty, and absence of unauthorized production output.
- [x] A8.4 `reviewer-go` publishes findings (PASS/FAIL per C01–C18 observable, per T1 item, per T2 replay) without editing files.
- **Evidence**: reviewer report file or comment with per-check PASS/FAIL, `git diff` outputs, `pytest` logs.
- **Done when**: reviewer report published and T0/T1/T2 all PASS.

### A9 — Main C01–C18 ACCEPT/REJECT Per Item

- [x] A9.1 Main reviews candidate + reviewer report, independently verifies C01–C18 one by one (see matrix). Each C* gets explicit ACCEPT or REJECT with citation (hash, JSON field, or log line).
- [x] A9.2 Main checks terminal priority: `closeout_evidence_inconsistent > closeout_verifier_blocked > closeout_corrected`; only if all C01–C18 ACCEPT and evidence consistent and verifier completed may terminal be `closeout_corrected`.
- [x] A9.3 Main records overall Change A verdict: `closeout_corrected` (all ACCEPT) or `closeout_evidence_inconsistent`/`closeout_verifier_blocked` (any FAIL) and blocks A10–A12 if not `closeout_corrected`.
- **Evidence**: C01–C18 decision table with per-item ACCEPT/REJECT + citation, terminal classification log.
- **Done when**: main publishes C01–C18 table and terminal verdict.

### A9R — C09 PEG limitation reopen fix (narrow, additive run_02)

- C09 REOPEN in prior review: run_01 `evidence_limitations=[]` missing PEG replay limitation; verifier line 235 downgrade not persisted for canonical QC-only run.
- Fix (A9R) persists exact limitation when QC accepted present but no PEG rejected packet with sufficient reconstructable data: "The canonical V31 manifest does not retain independently reconstructable rejected PEG packets. matrix_audits.json records two PEG rejection summaries, but the rejected constructions and rank decisions cannot be fully replayed from the persisted closeout inputs. This limitation does not alter the accepted QC packet recount or the n=1024 finite_graph_fail result." Appears in `closeout_verify.json`, `closeout_recount.json`, `closeout_gate.json` `evidence_limitations`; does NOT imply QC failure, n=1024 invalid, or decoder rerun; C09 remains PASS. When fake fixture provides complete PEG packet, limitation absent.
- Formal evidence regenerated as empty additive `nbldpc_v31_closeout_audit_v2/run_02` (run_01 retained superseded, hashes identical before/after); run_01/run_02 overwrite blocked (return 2). After run_02, C09 will be ACCEPT.

### A10 — Addendum / Decision-Log / Memory Handoff After ACCEPT

- [x] A10.1 Only if A9 is `closeout_corrected`: create `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` freezing corrected label/history (ARCHIVED_PARTIAL, n1024 full fail, n2048 14-block prefix only, post-hoc contingency, global PASS impossible).
- [x] A10.2 Append entry to `docs/decision-log.md` recording Change A correction (why post-hoc, why ARCHIVED_PARTIAL, why additive).
- [x] A10.3 Perform memory handoff via memory agent: update `AGENT_PROJECT_MEMORY.md` with corrected V31 lifecycle (do not edit old reports/plans).
- **Evidence**: `cat` of new addendum (first 30 lines), `git diff -- docs/decision-log.md`, memory handoff log.
- **Done when**: addendum exists, decision-log updated, memory handoff complete.

### A11 — Local Commit

- [ ] A11.1 `git status` shows only allowed new files + addendum/decision-log/memory diffs; no canonical/archive/old-report/src/experiments/tools diffs.
- [ ] A11.2 `git add` only the allowed set; `git commit -m "closeout-audit-correction: V31 ARCHIVED_PARTIAL ..."` locally (no push).
- [ ] A11.3 Verify `git log --oneline -1` shows new commit on `main` atop `c8d2acab`.
- **Evidence**: `git status` before/after, `git log --oneline -2`, `git show --stat HEAD`.
- **Done when**: local commit exists, no push performed.

### A12 — Decide Archive Change A

- [ ] A12.1 Main decides if Change A is archivable: requires A9 `closeout_corrected`, all evidence additive, no forbidden overwrite, reviewer PASS, addendum present.
- [ ] A12.2 If archivable: run `/opsx-archive formal-nonbinary-ldpc-v31-closeout-audit-correction` (or manual move to `openspec/changes/archive/`), merging delta spec into `openspec/specs/`.
- [ ] A12.3 If not archivable: keep change open, file follow-up tasks, retain failure evidence immutably.
- **Evidence**: archive command log or decision not to archive with rationale.
- **Done when**: archive decision recorded.

---

**Do not mark tasks complete without evidence. Each checkbox requires a cited command output or file hash.**
