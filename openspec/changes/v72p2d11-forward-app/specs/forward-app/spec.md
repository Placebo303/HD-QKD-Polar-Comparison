# Forward APP integration — delta spec

## Purpose

Freeze the D11 canonical forward L1→L2 APP diagnostic (packet §2 verbatim)
before any behavior edit. Normative keywords SHALL/SHALL NOT below bind
D1103+ implementation and D1110 review.

## Widths and dispatch

- SHALL run n128 first; SHALL run n256 iff n128 is `D11_FORWARD_SIGNAL`
  (conditional dispatch; maximum 720 scientific calls across both widths).

## L1 graphs, blocks, replay gate

- SHALL reuse R3 L1 graph seeds `2026092401..06` (n128) /
  `2026092501..06` (n256) and blocks `2026092601..12` (n128) /
  `2026092701..12` (n256); SHALL NOT search, replace, or resample seeds.
- SHALL enforce the L1 replay hard gate before interpretation: per-graph
  exact vectors SHALL equal n128 MIX `[4,4,2,5,3,5]` with CONTROL all zero,
  and n256 MIX `[6,3,5,5,6,4]` with CONTROL all zero.
- A replay mismatch SHALL be recorded as engineering-blocked and SHALL stop
  the width before interpretation.

## Shared L2 graphs

- SHALL create one shared connected/full-rank DV3 L2 graph per pair:
  n128 seeds `2026092801..06`, m=104, E=384, variables all degree 3,
  checks `3^32+4^72`; n256 seeds `2026092901..06`, m=208, E=768,
  variables all degree 3, checks `3^64+4^144`.
- SHALL admit every L1/L2 graph under A1–A6 via the accepted
  connectivity-first constructor and frozen coefficient rule (design §5
  reuse map); admission failure engineering-blocks with no seed change.
- SHALL use GF32/poly37, Model-F root
  `workspace/v72p2d5_model_f_input/20260907_r1`, max_iter=90,
  damping=1.0, cold start.

## Branches and calls

- SHALL implement exactly three branches: CONTROL (DV3 L1 → shared DV3 L2
  APP decoder), MIX (λ2=0.45 mixed L1 → the same shared DV3 L2 APP
  decoder), ORACLE (same L2 graph/block with the accepted true-L1
  conditional prior, once per graph/block, shared diagnostically).
- SHALL run 72 L1+L2 paired cells per width: 72 CONTROL L1 + 72 CONTROL
  L2 + 72 MIX L1 + 72 MIX L2 + 72 shared ORACLE L2 = 360 scientific calls
  per width.

## Metric isolation and provenance

- SHALL keep exact, syndrome-valid, L1 source exact, L2 target exact, and
  joint both-exact distinct; SHALL NOT merge `undetected`/syndrome-only
  outcomes into exact.
- SHALL fail closed unless every non-oracle transfer provenance is
  `CHECK_UPDATED`; uniform/prior-only fallback is forbidden.

## Gates, priority, terminals

- `D11_FORWARD_SIGNAL(w)` iff ALL of: `J_M>=9`; `J_M-J_C>=6`; MIX wins on
  ≥4/6 graph pairs; ≥3/6 MIX graphs have `J_Mg>=1`; `J_C<=3`; `O>=18`;
  all 72 MIX and 72 CONTROL transfers are CHECK_UPDATED; no
  engineering/resource violation (`J_M,J_C` pooled joint both-exact;
  `O` pooled L2 oracle exact; `J_Mg,J_Cg` per graph).
- `D11_TRANSFER_BOTTLENECK(w)` iff MIX L1 exact ≥18, `J_M<=3`, `O>=18`.
- `D11_L2_CODE_BOTTLENECK(w)` iff `O<=6`; otherwise
  `D11_FORWARD_AMBIGUOUS(w)`.
- Mutual priority (highest first): engineering block, L2-code bottleneck,
  forward signal, transfer bottleneck, ambiguous. Paired discordances and
  conditional target success are descriptive only and SHALL NOT override
  the gate.
- Terminals: `D11_FORWARD_APP_WIDE_RECOVERY` (n128 + n256 forward signal);
  `D11_N256_TRANSFER_BOTTLENECK` / `D11_N256_L2_CODE_BOTTLENECK` /
  `D11_N256_FORWARD_AMBIGUOUS` (n128 signal, n256 stop variants);
  `D11_N128_TRANSFER_BOTTLENECK` / `D11_N128_L2_CODE_BOTTLENECK` /
  `D11_N128_FORWARD_AMBIGUOUS` (n128 stop variants); explicit
  engineering/resource blocked terminal otherwise.

## Roots, budgets, ceiling

- Future root
  `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`
  (absent until separately authorized execution).
- Budgets: ≤720 scientific calls; ≤64 setup units; ≤2400 s wall;
  ≤120 s/call; RSS <2147483648 B; one process; no
  retry/resume/repair/seed search/tuning.
- Claim ceiling: synthetic two-layer forward diagnostic only; no FER,
  leakage, SKR, real-data, qualification, promotion, optimality, or D7-H
  claim.

## Prohibitions

- SHALL NOT execute D11, bind a production decoder, load Model-F content,
  create the future root, modify predecessor roots, implement D7-H,
  commit, or push under this change's readiness tasks.
