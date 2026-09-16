# Tasks — D19 L2 Finite-Ensemble Validation

Legend: `[x]` done this call (F01+F02, planner, no production code, zero
scientific calls); `[ ]` packet-exact future work (each needs its own
authorization; future execution additionally needs one explicit user grant
with Pre-EXECUTE).

## Readiness spec (this call)

- [x] **F01 OpenSpec freeze** — this change (`proposal.md`, `design.md`,
  `tasks.md`, `specs/l2-finite-ensemble/spec.md`) with packet §§1–7 verbatim
  in scientific effect: §1 route acceptance + near-tie ceiling (explicit
  non-reopening, non-optimality); §2 four frozen cells + `delta_L2`; §3
  seeds (n128 graphs `2026094401..4406` / n256 `4407..4412`; n128 blocks
  `2026094501..4508` / n256 `4511..4518`, absence proven, STOP on
  collision) + paired plan (shared labels + same 8 blocks per width,
  arm-specific graphs, width→graph→block→arm, 96+96, max 192, controls
  never advance); §4 construction (D10-R2 import, `v10_seed(…)` sorted-edge
  uniform nonzero GF32, A1–A6 pre-bind, diagnostics never gating); §5
  decoder (D16 oracle sampler/prior + cold row-layered 90/1.0, exact sole
  gate, syndrome/undetected/iters/residual/provenance/wall separate,
  ORACLE provenance every row, ungraded, one call per cell, no retry);
  §6 gates (POSITIVE 5 clauses / NEGATIVE 2 / AMBIGUOUS, exact-only,
  descriptive p/Wilson/structure, n256 iff POSITIVE); §7 four terminals;
  claim ceiling; §9 execution boundary (fresh-root pattern, UUID at F08,
  ≤192/≤42/1800s/120s/2GiB/1-proc/no-retry, one later grant may cover
  n128 + mechanical n256, zero granted now). Zero decoder/DE calls; no
  code/scripts/tests/roots edits; no commit/push; branch unchanged.
- [x] **F02 Four-cell arithmetic** — independently rederived by hand (no code
  execution) from the D9 largest-remainder rule + socket balance: n128 DV3
  (`3^128`, E=384, `4^86+5^8`); n128 L020 (`L2=3/11/L3=8/11 → 35/93`,
  E=349, `3^27+4^67`); n256 DV3 (`3^256`, E=768, `4^172+5^16`); n256 L020
  (`70/186`, E=698, `3^54+4^134`); all VERIFIED, no mismatch/no STOP.
  Exact rational realized deviations recorded (`design.md` §§2.2–2.3):
  edge `lambda2=70/349` (+1/1745), node `L2=35/128` (+1/1408), check
  `rho`/`R` fractions per arm; `delta_L2` recomputed (`5·94/128 −
  H_L2 = 3.671875 − 3.222719884634378 = 0.449155115365622`, matches packet
  to 15dp). Evidence: `design.md` §2.

## Future implementation/readiness (packet §8 — [ ], each needs authorization)

- [x] **F03 Thin D19 module** (STOP: implemented but readiness blocked at frozen seed 4408) — add one thin D19 module importing D10-R2
  graph construction and D16 L2 oracle/decoder helpers; reject duplicate
  kernels/builders. Evidence: `design.md` §§4–5 + delta-spec reuse
  requirements.
- [x] **F04 Cells/plan/gates/writer/verifier** (STOP: implemented but readiness blocked at frozen seed 4408) — implement graph cells,
  seeds, paired plan, admissions, exact-only gates, conditional width
  dispatch, terminals, writer, and verifier. Evidence: `design.md`
  §§2–7 + delta-spec requirements.
- [x] **F05 Runner** (STOP: implemented but readiness blocked at frozen seed 4408) — add a runner with `--profile-only`, `--d19-batch`,
  default-false `--execution-authorized`, fresh-root refusal, and read-only
  `--verify`. Evidence: delta-spec boundary/runner requirements.
- [x] **F06 Focused tests** (STOP: 33/33 pass but readiness blocked at frozen seed 4408) — arithmetic/socket tables; 24 graph admissions
  (2 arms × 2 widths × 6); replay; seed disjointness; plan/order/pairing;
  every gate edge; n256 dispatch; exact/syndrome/undetected isolation; L2
  ORACLE-only boundary; fake complete/negative/ambiguous/engineering runs;
  refusal/no-overwrite; verifier recomputation. Evidence: delta-spec test
  requirements.
- [x] **F07 PROFILE_ONLY** (STOP: 24 attempted/23 admitted, zero calls, but readiness blocked at frozen seed 4408) — build all 24 graphs and the 192-call maximum
  plan with zero decoder calls and no official root. Evidence: profile log
  + root-absence proof.
- [x] **F08 Freeze** (STOP: frozen but root absent/unauthorized, readiness blocked at frozen seed 4408) — freeze one future root
  (`workspace/d19_l2_finite_ensemble_<uuid>`, UUID picked here),
  command, and budgets; leave root absent/unauthorized. Evidence:
  `design.md` §9.
- [x] **F09 Independent review** (D19-BLOCKER-REVIEW performed: EVIDENCE_ACCESS VERIFIED, PASS, blocker retained) — with actual access: D18 winner
  provenance, arithmetic, construction isolation, 24 admissions,
  seeds/plan/gates, decoder boundary, budgets, tests, zero production.
  Any blocker → STOP. Evidence: review record with `EVIDENCE_ACCESS`.
- [x] **F10 Memory + decision log** (closure+triage this call, docs-only, no push) — memory triage and one decision-log
  entry. Optional scoped local commit may include only additive D19 paths
  if safe; no push.

(End of file)
