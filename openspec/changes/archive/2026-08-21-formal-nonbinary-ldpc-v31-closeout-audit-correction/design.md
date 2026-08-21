# Design: formal-nonbinary-ldpc-v31-closeout-audit-correction

## 0. Overview

Change A is a read-only closeout audit correction. It does not re-execute V31, does not complete the missing n=2048 blocks, and does not numerically overturn any FER/syndrome/leakage value. It introduces a second, independent read-only verifier (v2) that distrusts the original gate/readonly_verify terminals and recomputes counts/rates from raw persisted records, then classifies the closeout terminal via a strict priority. All new artifacts are additive under an isolated root; the canonical 16-file `run_01` remains byte-identical.

Pony-tail discipline: verifier is a single-file CLI with stdlib + already-installed deps (pyyaml, pyarrow optional). No new dependency, no caching layer, no retry framework. One small test file covers the 11 tamper checks.

---

## 1. Input Bindings (frozen)

Canonical inputs are trusted per P0 inventory (HEAD `c8d2acabccaae9d55a344e8f0c8ac1bb21ff9d1e`, `main`, tracked clean). The verifier must resolve and verify these bindings read-only; it must not modify them.

| Binding | Path / Identifier | Role |
|---|---|---|
| Canonical `run_01` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` | 16-file evidence under audit (see file list below) |
| `run_01` file list (16) | `de_confirmation.json`, `gate.json`, `m1_registry.json`, `matrix_audits.json`, `matrix_payloads.json`, `per_block_n1024.jsonl` (300 lines), `per_block_n2048.jsonl` (14 lines), `progress.json`, `readonly_verify.json`, `RUN_MANIFEST.json`, `summary_n1024.json`, `summary_n2048.json`, `validation_blocks_n1024.json`, `validation_blocks_n2048.json`, `validation_frames_n1024.json`, `validation_frames_n2048.json` | Byte-identical preservation |
| Gate | `run_01/gate.json` (`finite_graph_fail`, `closeout_note` bounded-prefix contingency) | Distrusted; contingency is POST-HOC |
| Old verifier | `run_01/readonly_verify.json` (`ok=true`, `problems=[]`) | Distrusted; v2 recomputes independently |
| Archive V31 | `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/` (proposal.md, design.md, tasks.md, specs/, archive_note.md) | Frozen predecessor spec; must be read-only |
| Reports/plans | `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`, `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md` | Frozen historical narrative; only new addendum may supplement |
| Git timeline | `c8d2acabccaae9d55a344e8f0c8ac1bb21ff9d1e` (HEAD on `main`, tracked clean at P1 freeze) | Code identity for verifier & canonical |
| Field authority | `GF2mField.create(32)`, poly `0b100101`, `field_id=c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf` | Checked via RUN_MANIFEST + source hash |
| Channel/allocation | V25 inventory/split/channel_counts, V26 `run_02` A02 `adapter_H` float64, `m1=16`, `m_total` tables, `f_total<1.3` | Checked via `de_confirmation.json` + `m1_registry.json` + `summary_*` |

File-system check at T0: `run_01` exists, is directory, contains exactly 16 files with exact names; any deviation → `closeout_verifier_blocked` (C01 fail).

---

## 2. Lifecycle Model (implementation complete ≠ full frozen execution complete ≠ qualification ≠ promotion)

```
implementation complete
    ≠ full frozen execution complete
    ≠ qualification
    ≠ promotion

V31 status before Change A:
  - implementation complete: YES (code for PEG-capacity-aware + QC-cyclic-projective frozen, M0/M1/M2/M3 implemented)
  - full frozen execution complete: NO  (pre-registered required: n=1024 300/300 + n=2048 150/150;
                                            actual: n=1024 300/300 + n=2048 14/150 on 1M only)
  - qualification: NO (never authorized)
  - promotion: NO (never authorized)

Therefore archiving as "complete gate with final terminal" is a lifecycle mislabel;
correct label is ARCHIVED_PARTIAL (see §3).
```

The audit does not retroactively mark execution as complete. It freezes the incompleteness as fact.

---

## 3. Correct Terminal (V31)

```
ARCHIVED_PARTIAL
  n=1024: full-window finite_graph_fail
          — 300/300 blocks (100/source × 3), all QC, exact=0 tag=0 false_accept=0,
            syndrome convergence 0.00, waterfall 0, PEG deterministically rank-rejected.
          — Bounded negative result: valid for tested deterministic families + frozen decoder.
  n=2048: bounded prefix only (diagnostic, not a full gate)
          — 14 blocks on 1M only (`type2_1M_20260121_184040`), all QC, exact=0 tag=0,
            `converged_no_syndrome`; 1p5M/2M not executed (0 blocks).
  global PASS impossible
          — original pre-registered rule: each n requires a passing family (95% exact/tag, 0 false_accept).
            n=1024 already fails 0/300, so no n=2048 outcome could restore global PASS.
  original complete execution: incomplete (n=2048 truncated)
  closeout_note bounded-prefix contingency: POST-HOC (added at closeout, not pre-registered)
```

This block must appear verbatim (or semantically identical) in the addendum and in `closeout_gate.json` produced by verifier v2.

---

## 4. Verifier v2 Principles (read-only, additive, distrusting)

- **Distrust `gate.json` terminal**: never use `gate.json:terminal` as ground truth; recompute `finite_graph_fail` vs `resource_blocked` vs `implementation_blocked` from raw `per_block_*` + `matrix_audits` + summaries.
- **Distrust old `readonly_verify` ok**: never use `readonly_verify.json:ok` as ground truth; recompute `ok` via independent C01–C18 checks; old `ok=true` is evidence to be verified, not authority.
- **Recompute from raw persisted records**: block counts, exact/tag/false_accept, syndrome convergence, failure positions, waterfall, runtime, allocation `f_total`, and terminal must all be recomputed from `per_block_*.jsonl` lines and `matrix_audits.json` entries, not from `summary_*.json` or `gate.json` summaries (summaries are cross-checked, not trusted).
- **No DE/decoder/production runner**: verifier must not import `formal_ir.nonbinary_v31` DE, decoder, or `run_nonbinary_v31_gate`; must not spawn subprocess to them; must not execute `experiments/run_e2e_pipeline.py`, `longrun_*`, `minrerun_*`, `routeA_*`. Fake-runner only for synthetic T2 fixtures.
- **Read-only input, additive output**: all inputs under `nbldpc_v31_20260820/run_01/` are opened read-only; all new outputs go under `nbldpc_v31_closeout_audit_v2/run_01/`; any write to canonical path is a hard failure (C14).
- **Rerun fields only as declaration, not fact**: if verifier output contains `rerun_*` or `resume_*` style fields, they are declarations of what would be needed to complete execution, not claims that execution is complete. `closeout_gate.json` must state `original_complete_execution: incomplete` and `global_pass_possible: false`.

Implementation sketch (single file, ponytail: naive line-by-line JSONL scan, no custom cache — upgrade to streaming hash if evidence grows beyond ~10k blocks):
- CLI: `python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit [--input run_01] [--output closeout_audit_v2/run_01] [--fake-root workspace/...]`
- Steps: (i) verify canonical 16-file presence/hashes, (ii) load + recount JSONL, (iii) cross-check summaries/gate, (iv) verify matrix audits (QC accept/PEG reject), (v) check input bindings/code identity, (vi) classify closeout terminal via §5 priority, (vii) write `closeout_verify.json`, `closeout_recount.json`, `closeout_gate.json` atomically under additive root.

---

## 5. Terminal Priority (closeout audit)

```
priority:
  closeout_evidence_inconsistent   (highest)
    > closeout_verifier_blocked
    > closeout_corrected           (lowest, success)

Rules:
  - closeout_evidence_inconsistent if any recomputed count/rate contradicts the persisted
    summary/gate beyond tolerance (e.g., per_block count ≠ summary blocks, exact/tag mismatch,
    syndrome rate mismatch, PEG/QC packet mislabeled) OR manifest missing without graceful downgrade.
  - closeout_verifier_blocked if verifier cannot run to completion
    (canonical missing/tampered, unreadable JSONL, input binding absent, overwrite attempt detected, T1 tamper fail).
  - closeout_corrected only if evidence is internally consistent AND verifier completes AND
    C01–C18 all ACCEPT (including POST-HOC label and ARCHIVED_PARTIAL narrative).
```

Only `closeout_corrected` allows the addendum to be published and Change A to be considered for archiving. The other two terminals keep V31 as `ARCHIVED_PARTIAL` without a corrected closeout mark and require a new fix change.

---

## 6. Verification Strategy

| Tier | What | Where | Evidence |
|---|---|---|---|
| T0 structural | File count/names, importability, tiny-math (H float64, f_total<1.3, field_id) | `test_nonbinary_v31_closeout_audit.py::test_t0_*` | `pytest -q -p no:cacheprovider` log |
| T1 tamper (11) | See §7 layered tamper | `test_nonbinary_v31_closeout_audit.py::test_t1_*` | Tamper log with per-check PASS/FAIL |
| T2 fake + real recount | Synthetic 16-file fixtures (fake runner) + one real additive recount | `workspace/<task>/<uuid>/fake_*` + `nbldpc_v31_closeout_audit_v2/run_01/` | `closeout_verify.json`, `closeout_recount.json`, `closeout_gate.json`, strict replay log |
| T3 broad | Not needed for Lite (deferred) | — | — |

Strict replay: re-running verifier v2 on its own additive output (`closeout_verify.json` input) must yield byte-identical `closeout_recount.json` (deterministic).

---

## 7. Layered Tamper Tests (T1 11 items — frozen)

Each tamper test is `ponytail: O(n) scan, global lock not needed; per-file hash if evidence exceeds 10k blocks`.

1. **T1-01 raw byte drift**: 16-file SHA-256 vs frozen manifest; any byte change → FAIL.
2. **T1-02 semantic self-hash RUN_MANIFEST**: recompute `RUN_MANIFEST.json` self-hash (canonical field order, float64 exact) and compare to stored hash.
3. **T1-03 semantic self-hash per_block JSONL**: recompute per-record canonical JSON hash for each line in `per_block_n1024.jsonl` (300) and `per_block_n2048.jsonl` (14); compare to registry.
4. **T1-04 manifest/index links**: `validation_frames_*.json` frame ranges (1M 1200..1599 etc.) ↔ `validation_blocks_*.json` block ids ↔ `per_block_*.jsonl` block keys must align; missing link → FAIL.
5. **T1-05 matrix payload vs audit consistency**: `matrix_payloads.json` matrix bytes hash ↔ `matrix_audits.json` audit entry (rank, occupancy, projective keys) must match.
6. **T1-06 summary recomputed from per_block**: `summary_n1024.json`/`summary_n2048.json` FER/syndrome/waterfall recomputed from JSONL; mismatch → evidence_inconsistent.
7. **T1-07 gate terminal recomputed**: `gate.json` persisted terminal vs recomputed terminal from summaries+audits; mismatch → evidence_inconsistent.
8. **T1-08 deep source check**: `channel_counts.npz`/`data_inventory.json` source stats vs `de_confirmation.json` channel binding; mismatch → verifier_blocked.
9. **T1-09 deep public-payload check**: `matrix_payloads.json` QC/PEG payload counts vs `gate.json` accepted/rejected counts.
10. **T1-10 deep leakage/accounting**: `m_total`/`leak_total`/`f_total` tables recomputed from `m1_registry.json` + H float64; `f_total<1.3` and `leak=5*m+64` must hold.
11. **T1-11 deep gate reconstruction**: rebuild `gate.json` closeout_note parsing to confirm bounded-prefix contingency text is post-hoc (not in original proposal `terminal states` list).

All 11 must PASS for `closeout_corrected`; any FAIL maps to `closeout_evidence_inconsistent` or `closeout_verifier_blocked` per §5 priority.

---

## 8. Evidence Root Segregation

```
comparison_bench/outputs_comparison/nonbinary_diagnostics/
  nbldpc_v31_20260820/run_01/                          ← canonical (16 files, READ-ONLY, never written)
  nbldpc_v31_closeout_audit_v2/run_01/                 ← additive audit evidence (new, isolated)
    closeout_verify.json        # C01–C18 per-item verdicts, terminal priority result
    closeout_recount.json       # recomputed counts/rates from raw JSONL
    closeout_gate.json          # corrected terminal block (§3) + post-hoc declaration
    closeout_run_manifest.json  # audit run manifest (git HEAD, verifier SHA, input hashes)
    tamper_log.json             # T1 11-item results
    strict_replay_log.json      # T2 replay determinism proof
```

No other output path is permitted. The verifier must `mkdir -p` the additive root and refuse to start if canonical and additive roots resolve to the same directory.

---

## 9. Constraints & Non-Goals Enforcement

- No import of `formal_ir.nonbinary_v31` DE/decoder in verifier (static grep in T0).
- No `subprocess` call to `run_nonbinary_v31_gate` (static grep in T0).
- No write to `nbldpc_v31_20260820` (filesystem assertion before any write).
- No edit of `openspec/changes/archive/2026-08-21-formal-nonbinary-ldpc-v31-deterministic-finite-graph-redesign-gate/**` (git diff check in T1).
- Addendum only after main ACCEPT (task A9 gate).
