# R21 RESULT — NO-DAMP-GAIN both arms (damping-inert on outcomes)

## Dc-ev (quoted, OPERATOR-ATTESTED)

- Exit 0 both arms; wall 133 s each; RSS ~217 MiB each.
- Budgets: sci 128+128=256/256, setup 4+4/8.
- Per arm: 128 frames / 2 accepts / 2 verified / 0 undetected.
- Disclosure 72192/arm; net −70912/arm.
- Betas: −0.31624 (0.5) / −0.36725 (0.8).
- Accepts @34/106 both arms (SAME as S1-shift baseline).
- Accept-iters {12,35} (0.5) / {7,19} (0.8) vs S1 {6,13}.
- OUTCOME-REPLICATION: accept/exact/outcome/syndrome/tag/undetected/frame/block/seed 128/128 identical across 0.5 / 0.8 / 1.0.
- Residuals near-identical: 0.5-vs-S1 126/128 (mean +0.0469); 0.8-vs-S1 127/128 (mean +0.0234); medians all 75.0.
- Verify 128/0 ×2.

## Provenance

- Zero replacement/retune. `damping_alpha` recorded 0.5/0.8; 1.0 path untouched — S1 sha 3e6bb067… recomputed match.
- Prior R9/R20 read-only; truth files dated post-decision.
- Single invocation per arm, contiguous; protected-dir clean; no commit/push under this solidification.

## Roots (4 files each)

- 0.5: `workspace/g6r21_damp_9f43bc04-0b0b-44a0-a0f9-3b66329c272f`
- 0.8: `workspace/g6r21_damp_8dbeced5-7d77-478f-9dc6-0b992500bbcd`

## Ceiling (diagnostic-only)

- NO-DAMP-GAIN stated LITERALLY per arm (execution reports lack the string — stated here).
- Damping-inert on outcomes as observed fact (outcome vectors identical; only accept-iters + 1–2 residual wiggles differ).
- Converges-marginally-slower + residual-wiggles noted; no success/FER/leakage-efficiency claim beyond gate verdict.

## Acceptance block

- Grant single-consumption per arm (mandate + pre-approvals, one consumption covering both arms).
- Pre-EXECUTE Q1–Q6 PASS (recorded in cycle).
- Pre-RESULT reviewer-go PASS (see INDEPENDENT_ACCEPTANCE.md).
- Main-thread ACCEPTED: NO-DAMP-GAIN both arms.
