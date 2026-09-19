# V80 S1 Batch-End Review (2026-09-20) — EXPLORE, review-record only

- Track: EXPLORE batch-end review (AGENTS §10.3). No patches, no execution,
  no commit/push, no S1-number interpretation. Branch
  `formal-ir-v72p1-addendum-clean`. This review **authorizes nothing** —
  no S2 entry, no rerun, no resume.
- Verdict: **PASS_WITH_FINDINGS** — batch may be considered **closed**;
  findings gate S2 entry, not closure.

## Authorization boundary — PASS
- Rerun ran under quoted autonomous grant 2026-09-19 (G-RERUN, frozen
  contract hash `60ab1e44…0da`) + Pre-EXEC Q0–Q6 PASS + user
  pre-authorization 2026-09-20; halt+close per user-authorized option
  (立即停+关批), quiescence 6×60s verified. Spend 539 ≤ ~612 estimate.

## Machine gates — PASS
- F1/F2/F3 rework + G-D5R PASS (`S1_D5R_REVIEW_20260919.md`) + Pre-EXECUTE
  Q0–Q6 PASS all recorded; HOLD release §(f) + decision-log backfill
  (HOLD / batch-close / f-freeze) present.

## Retained failure — PASS (edge b: yes)
- Old root `07723233` retained untouched, hash-foreign (`57e5da44…684`);
  pre-fix PRIMARY 0/420 + pseudo-pass f_ens=0.7506 preserved as the
  invalid arm, never deleted/overwritten. Immutable retention satisfied.

## Final evidence ledger (raw facts, uninterpretted)
- New root `1b079a49`: PRIMARY 420 / SECONDARY 119 / SETUP 12 / TOTAL 539;
  wall_windows 11; hash `60ab1e44…0da` stable; partial true; terminals
  PRIMARY SELECT / SECONDARY resource_blocked; 61 SECONDARY-confirm slots
  abandoned (80−19). Gate raw: PRIMARY f_ens=1.1375 n=32 pass=true sw=0;
  SECONDARY null/0/false; flip withheld (cross-unit).

## Edges ruled
- (a) Abandoned 61 slots do **not** invalidate PRIMARY: 420/420 complete
  with SELECT under frozen gate pre-halt; arms independent.
- (c) f-freeze (PROGRAM_PLAN §1.3, user-approved docs-only) is **not** a
  science-input change: grids/seeds/H-anchors/gate-1.15 unchanged; it is
  S2/S3 accounting. No escalation required; numbers stay raw.

## Findings
- **BER-1 (S2-blocking)**: P1 status-label — `_row` hardcodes
  `status="ok"` (runner:899); 9 rows >300 s, 0/539 overrun labels; gate
  screens `status=="ok"` so overrun rows are gate-eligible. This instance
  unaffected (overruns confined to 0-converged SECONDARY-confirm).
- **BER-2 (S2-blocking)**: P3 reproducibility — PRIMARY pass rests on one
  m₂=47 1/9 confirm candidate; confirm single-seed by code design
  (runner:837-839 vs declared 2 seeds); non-monotonic convergence.
- BER-3 (non-blocking): G-D5R red-green evidence partly supplied
  (implementer 48+6, 7-row table), mitigated by in-batch behavioral
  confirmation; re-run F3 pins independently at S2 readiness.
- BER-4 (non-blocking): rework files untracked (`??` runner+test);
  provenance rests on hash chain, not commits; re-verify identity at S2.
- BER-5 (non-blocking): tool-bridge respawn waves R1/R2 killed; S2 must
  use a single owned process, no relaunch loops.

## Claim ceiling
- Synthetic DE-ensemble diagnostics only. No FER/SKR/qualification/
  promotion/publication/route-closure; all numbers raw, pending Pre-RESULT.
  S2/S3 require fresh gates. Pre-S2 clearance: **BER-1 fix + re-verify,
  BER-2 m₂=47 multi-seed×multi-restart gate, f-basis mapping in S2 prereg.**

## Addendum 2026-09-20 — BER-1/BER-2 re-review (EXPLORE, review-only)

- Source: independent reviewer-go re-review (inspection-only; suite not re-run).
- CLAIM-1 PASS (REV-1/REV-2): overrun honestly labelled (`_row` status carried; overrun call sites screen/confirm/repro); `evaluate_gate` / `evaluate_flip_rule` / `_find_cached_fit` remain `status=="ok"`-gated so overruns stay excluded from converged-pass computation; `_validate_partial` `completed == n_ok + n_overrun` is the minimal change preserving resume of overrun-halted partials, no-retry intact.
- CLAIM-2 PASS (REV-3/REV-4/REV-5): `config_hash == recorded_hash == 60ab1e44…0da` unchanged (restart `seed+r*7919` is gate-local, outside `frozen_config`); m₂=47 5/5 + 5/5 both seeds (bar ≥3/5), pooled converged range 0.000559 ≤ 0.04 ⇒ G-REPRO PASS with no post-hoc m selection, no threshold tuning, no retry-on-failure; every row carries `f_row` + `f_superframe` (dual-unit reporting satisfied).
- REV-6: no scope creep, no S2/S3 advance; frozen thresholds/budgets/seeds unchanged; fresh root `workspace/s1_repro_26483764` only; old roots untouched.
- Suite 54 passed + 6 subtests cited from PREEXEC, not re-executed here.
- S2-entry status: BER-1 and BER-2 CLEARED. Remaining: edge-c (S2 prereg must map the layer-unit gate basis m₂=47 / f=1.1375 onto the frozen whole-frame-with-tag superframe-n=1024 accounting) plus non-blocking BER-3 (F3 re-pin at S2 readiness) / BER-4 (untracked runner+test; hash-chain provenance only).
- This addendum authorizes nothing; S2 is not yet clear to enter.
