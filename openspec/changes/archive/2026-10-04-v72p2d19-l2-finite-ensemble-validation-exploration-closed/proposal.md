# Proposal — D19 L2 Finite-Ensemble Validation (Readiness R1)

- Authority: `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`
  (§§1–11 sole authority; §§2/4/5 take precedence on any conflict; STOP rules
  are fail-closed), `AGENTS.md` §1.2/§3/§5/§10.1.
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- Track: `EXPLORE` readiness planning (OpenSpec-only, this call). Future
  scientific batch track: `EXPLORE_HEAVY`. This packet grants zero scientific
  decoder/DE calls.
- This call (F01+F02, planner, no production code): OpenSpec freeze only
  (`proposal.md`, `design.md`, `tasks.md`, `specs/l2-finite-ensemble/spec.md`)
  + independent hand rederivation of the four degree/socket cells (F02, no code
  execution). Zero decoder/DE calls, no roots created, no commits, no push.
- Predecessor: `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`
  — verdict PRESENT (exact-string search, 6 hits: `docs/decision-log.md:4382`,
  `AGENT_PROJECT_MEMORY.md:4010`,
  `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md:312`,
  D18 A1 packet + prompt + this D19 packet; see Return section).
- Trusted read-only context: D18 winner `lam_d2_0.20_d3_0.80`; near-tie record
  (0.15/0.20/0.25 identical DE thresholds, 0.20 won by frozen max-check-degree
  then ID tie-break; rank-4..6 0.30/0.35/0.40 screen-indistinguishable);
  D18 stage-C selected cells (m89 0/8, m94–m109 8/8; brackets lo89/hi94
  `h=0.09765625`, `delta_DE=0.35149886536562214`); DV3 baseline
  `delta_DE=0.5468113653656221`; D10-R2 connectivity-first constructor +
  A1–A6; D16 true-conditioned L2 oracle/decoder semantics.

## 1. Route acceptance + near-tie ceiling (packet §1 — recorded FIRST, verbatim in scientific effect)

1. Accept the D18 winner `lam_d2_0.20_d3_0.80` for ONE finite L2 validation
   against DV3. This is not an optimality claim.
2. D18's 0.15/0.20/0.25 candidates had identical reviewed DE thresholds;
   0.20 won only through the frozen max-check-degree then ID tie-break.
   Do NOT reopen the family and do NOT include extra near-tie arms in D19.
3. No scientific decoder calls, D7-H, APP, L1, real data, FER/leakage/SKR/
   qualification, route closure, or push are authorized by readiness.

## Goal

Freeze, before any new execution, the complete readiness contract for a
bounded paired finite-ensemble validation of the single D18 winner
(`lam_d2_0.20_d3_0.80`, arm `L020`) against DV3 at the single discriminating
rate point m/n = 94/128 (`delta_L2=0.44915511536562214`): four frozen
(width, arm) cells with exact degree/socket tables, frozen seeds with a
paired width→graph→block→arm plan, shared construction/admission/decoder
with exact-only gates and conditional n256 dispatch, four terminals, claim
ceiling, and future execution boundary. The result is a synthetic finite-L2
diagnostic only; it selects no new ensemble and claims no optimality.

## Non-Goals

No decoder/DE execution or authorization; no new graph constructor (reuse
D10-R2) and no new decoder (reuse D16); no near-tie/family arm; no threshold
refit; no APP/L1/D7-H/transfer; no graded oracle; no real data; no
FER/leakage/SKR/qualification/publication/optimality/route-closure claim;
no change to any predecessor root, frozen baseline (`src/`, `experiments/`,
`tools/`), `AGENTS.md`, or decision log; no commit/push in this call.

## Impact Scope

- Added only: `openspec/changes/v72p2d19-l2-finite-ensemble-validation/`
  (`proposal.md`, `design.md`, `tasks.md`, `specs/l2-finite-ensemble/spec.md`).
- Read-only inputs (never modified): D18 reviewed winner + near-tie record,
  D18 stage-C brackets, DV3 baseline, D9 largest-remainder + socket-balance
  rule, D10-R2 `build_degree_sequence_peg` + A1–A6, D16 L2 oracle/decoder
  semantics.
- Forbidden this call: code/scripts/tests/roots/`AGENTS.md`/decision-log
  edits, commits, pushes, branch switch, any decoder/DE call.

## Acceptance Criteria

1. §1 route acceptance + near-tie ceiling recorded FIRST and verbatim in
   scientific effect (single-winner acceptance, explicit non-reopening,
   non-optimality).
2. §2 four cells frozen (variable counts, E, check allocs) with F02 hand
   rederivation + exact rational realized lambda/rho deviations + `delta_L2`
   recompute recorded; any mismatch would have STOPped (none found).
3. §3 seeds frozen (n128 graphs `2026094401..4406`, n256 `4407..4412`; n128
   blocks `2026094501..4508`, n256 `4511..4518`), proven absent outside the
   D19 packet (rg evidence in Return), STOP on collision; paired plan frozen
   (shared labels + same 8 blocks per width, arm-specific graphs,
   width→graph→block→arm, 96+96, max 192, controls never advance).
4. §4 construction frozen (D10-R2 import, `v10_seed("d19:l2:coeff:…")`
   sorted-edge uniform nonzero GF32, A1–A6 pre-bind, diagnostics never
   gating, invalid graph → engineering-blocked, zero replacement).
5. §5 decoder frozen (D16 oracle sampler/prior + cold row-layered 90/1.0,
   exact sole gate, syndrome/undetected/iters/residual/provenance/wall
   separate, ORACLE provenance every row, ungraded, one call per cell, no
   retry).
6. §6 width gates frozen (POSITIVE 5 clauses / NEGATIVE 2 / AMBIGUOUS,
   exact-only, descriptive p/Wilson/structure, n256 iff POSITIVE) and §7
   four terminals frozen as synthetic diagnostics.
7. §9 boundary frozen (fresh-root pattern, UUID at F08, ≤192/≤42,
   1800s/120s/2GiB/1-proc/no-retry, one later grant may cover n128 +
   mechanical n256, zero granted now).
8. `tasks.md`: F01+F02 `[x]`, F03–F10 packet-exact `[ ]`.
9. Zero scientific calls; decoder/DE counters 0; no commit/push.

## Frozen plan summary (§§2–7, 9 in scientific effect; full freeze in `design.md` + delta spec)

- Cells (§2): single rate point m/n = 94/128 (`delta_L2=0.44915511536562214`,
  below DV3's DE threshold, above the candidate's). `n128/DV3: 3^128,
  E=384, 4^86+5^8`; `n128/L020: 2^35+3^93, E=349, 3^27+4^67`;
  `n256/DV3: 3^256, E=768, 4^172+5^16`; `n256/L020: 2^70+3^186, E=698,
  3^54+4^134`. Only the frozen degree profile and implied sockets/checks
  differ; L2 channel is true-U1-conditioned ORACLE, diagnostic-only,
  ungraded, no APP/transfer.
- Seeds/plan (§3): graph seeds n128 `2026094401..4406`, n256
  `2026094407..4412`; block seeds n128 `2026094501..4508`, n256
  `2026094511..4518`; disjointness proven, no replacement/seed search.
  Within each width both arms share graph-seed labels and the same eight
  generated source blocks; graphs remain arm-specific. Deterministic order
  width→graph→block→arm; n128 plan 2×6×8=96; n256 dispatched only after
  frozen n128 POSITIVE, another 96; maximum 192; controls never advance
  independently.
- Construction (§4): reuse accepted D10-R2 connectivity-first
  `build_degree_sequence_peg` + coefficient/admission helpers; no new
  constructor. One deterministic coefficient namespace
  `v10_seed("d19:l2:coeff:{width}:{arm}:{graph_seed}")`, uniform nonzero
  GF32 in sorted-edge order. A1–A6 for every graph before binding (exact
  variable/check degrees, one component, full structural rank m, full GF32
  rank m, deterministic replay). Four-cycle/girth recorded, never
  gating/repairing. Any invalid graph → engineering-blocked, zero
  replacement seeds.
- Decoder (§5): reuse D16 true-conditioned L2 oracle sampler/prior +
  canonical cold row-layered decoder (GF32/poly37, max_iter90,
  damping1.0). Exact recovery is the sole gate; syndrome-valid,
  undetected, iterations, residual, provenance, wall, failures recorded
  separately and never merged. ORACLE provenance required every row;
  oracle rows ungraded. One call per (width,graph,block,arm); no
  retry/resume/warm start.
- Gates (§6): per width, `M_g`/`C_g` L020/DV3 exact out of 8, `M`/`C`
  pooled out of 48, `b` candidate-only / `c` control-only paired blocks.
  POSITIVE iff all five: `M>=30/48`; ≥5/6 graphs `M_g>=4/8`; L020 strict
  win on ≥5/6 graphs; `b-c>=12`; `C<=20/48`. NEGATIVE iff both:
  `M<=16/48` and `b-c<=4`. Else AMBIGUOUS. Exact-only; paired
  p-values/Wilson + structure correlations descriptive. n256 iff n128
  POSITIVE.
- Terminals (§7): `D19_L2_FINITE_SIGNAL_REPRODUCED` (n128+n256 POSITIVE);
  `D19_L2_FINITE_NO_USEFUL_RECOVERY` (n128 NEGATIVE, or n128 POSITIVE then
  n256 NEGATIVE); `D19_L2_FINITE_AMBIGUOUS` (any entered width
  AMBIGUOUS); `D19_L2_FINITE_ENGINEERING_BLOCKED`
  (contract/admission/resource/incomplete-plan failure). All synthetic
  finite-L2 diagnostics, not qualification.
- Boundary (§9): fresh root `workspace/d19_l2_finite_ensemble_<uuid>`
  (UUID chosen/frozen at F08; absent afterwards). Max 192 decoder calls;
  setup ≤42 (24 graphs + 16 blocks + 2 binding/plan). Wall ≤1800s,
  per-call ≤120s, RSS <2GiB, one CPU process, no retry/resume/replacement/
  tuning/adaptive thresholds. One later explicit grant may cover n128 and
  the mechanically conditional n256 sequence. Readiness grants none.
- STOP (§10): degree/socket arithmetic mismatch; D18 winner change;
  non-winner arm added; corrected current-channel L2 oracle identity not
  exact; any A1–A6 failure; seed collision; APP/L1 or graded oracle;
  exact/syndrome/undetected merge; adaptive thresholds; future root
  exists; independent review blocker.

## Claim ceiling

Synthetic finite-L2 diagnostic evidence only. No FER/leakage/SKR/
qualification/promotion/publication/optimality/route-closure claim. The
batch tests whether the single D18 winner shows useful finite recovery at
the discriminating point; it does not validate a code or close the route.

## Return

`F01–F02 DONE` (details in the final message). Execution false;
decoder/DE calls `0`; no commit/push. Next: F03–F10 per `tasks.md` (each
needs its own authorization; future execution additionally needs one
explicit user grant + Pre-EXECUTE).

(End of file)
