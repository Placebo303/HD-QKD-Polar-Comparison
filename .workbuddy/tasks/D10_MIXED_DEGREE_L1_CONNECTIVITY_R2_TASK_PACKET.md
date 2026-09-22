# D10 Mixed-Degree L1 Connectivity/Rank R2 — task packet

## 1. Purpose and authority

Repository: `HD-QKD_Polar_Comparison`. This is implementation/readiness work;
no research execution track is entered and no decoder, DE, CAL, VAL, or real
data call is authorized. R1 remains retained evidence. The main-thread decision
is `REVISE_REQUIRED_CONNECTIVITY_AND_RANK`: R1 graphs are fragmented and
sometimes rank-deficient, confounding the degree-profile test.

Use the verified independent review as evidence; do not rerun broad suites for
ceremony. Update the existing D10 OpenSpec before changing behavior.

## 2. Frozen scientific contract

Preserve the two R1 arms, widths 64/128/256, exact variable/check degree-count
tables, original graph seeds `2026092201..2026092209` with their R1 assignment,
block seeds, Model-F input, rows, priors, GF32/poly 37, coefficient seed rule,
decoder settings, paired blocks, thresholds, progression, budgets and claim
ceiling. Both arms must use one constructor and tie policy; only the forced
degree sequence may differ.

Do not use replacement seeds, seed search, topology selection across candidates,
threshold tuning, decoder feedback, adaptive construction, or coefficient
repair/reseeding.

## 3. Required delta

- R201: Amend the active D10 OpenSpec proposal/design/tasks/delta spec for R2.
- R202: Implement the smallest deterministic connectivity-first degree-sequence
  PEG builder. First create a spanning backbone over every variable and check
  node while respecting exact target degrees; then fill remaining sockets with
  the shared PEG/ACE rule. Reject parallel edges and degree/socket mismatch.
- R203: Add deterministic maximum bipartite matching and require all `m` checks
  covered (`structural_rank == m`).
- R204: Generate coefficients by the frozen R1 rule and compute exact GF32 row
  rank. Require `gf32_rank == m`; on failure record the cell and stop, without
  altering graph/coefficient seeds.
- R205: Before decoder binding require exact degrees/socket balance, a simple
  graph, exactly one connected component across all `n+m` Tanner nodes,
  structural rank `m`, GF32 rank `m`, and deterministic replay equality.
  Four-cycle/girth/ACE values remain reported diagnostics.
- R206: Replace source constant flipping with an explicit CLI execution-
  authorization argument. It defaults false and must refuse `--batch` before
  root creation or decoder binding. Keep it false and unused in this task.
- R207: Keep `--verify` fail-closed for partial/engineering-blocked roots. Do
  not create a scientific root here.

## 4. Validation and evidence

- R208: Focused tests must cover all six admission predicates, exact frozen
  tables/seeds, both arms sharing the constructor, unauthorized no-write/no-bind
  refusal, and deliberate disconnected/rank-deficient rejection. Use fake
  decoders for entry-boundary tests.
- R209: Run `py_compile` and focused D10 tests only, with a fresh task-owned
  `workspace/` basetemp and `-p no:cacheprovider`. Run broader tiers only if a
  focused failure demonstrates an external regression.
- R210: Run no-decoder `PROFILE_ONLY` for exactly the original 18 cells. Record
  component count, largest fraction, structural/GF32 rank, four-cycles, girth
  and wall time. Require zero replacement seeds and zero decoder calls/binds.
- R211: One independent readiness review with `EVIDENCE_ACCESS: VERIFIED` must
  recompute every admission predicate for all 18 cells and check R1 frozen-
  contract equality. Do not ceremonially duplicate a traceable passing review.
- R212: Append evidence/review to the existing exploration log and perform
  project-memory triage. No commit or push unless separately requested.

## 5. Terminals and STOP rules

Return `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION` only if
all 18 original cells pass and review has no blocker. This never authorizes
execution.

Return `BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION` with exact failing cells
if any cannot pass without changing a frozen item. STOP on ambiguity, frozen
input drift, seed replacement/search, decoder entry, scientific-root creation,
unrelated dirty-file conflict, or failed review. Do not self-authorize, run,
retry with new seeds, remove R1 evidence, commit, push, or revive D7-H.

## 6. Return contract

Report terminal; R201--R212; changed files; constructor delta; 18-cell admission
table; commands/tests; independent verdict/findings; decoder/scientific-call
counts (both zero); authorization/root/commit/push state; and one blocker if any.
