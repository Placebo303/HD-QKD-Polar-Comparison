# G1 No-Signal Attribution R1 — bounded development diagnosis of the accepted negative result

- Accepted result: `workspace/v72p2d5_g1/20260907_r2`, `G1_COMPLETED_NO_SIGNAL_FAIL`,
  `passed=false` (per `G1_RESULT_ACCEPTANCE_R1.md`). This document explains the
  zeros; it changes no formal value, threshold, seed, authorization, or semantic.
- Method: direct injected-function development diagnostics only (`n=64`, accepted
  Model-F, frozen mothers/prefixes/decoder settings, one axis per control). No CLI
  `--phase`, no formal-root write, no VOID read, no G2, no real-data IR.
- Evidence root (only workspace written):
  `workspace/d5_g1_no_signal_attribution_r1_1dfa97a151f746569c95cc74d8786ae7/`
  (`diag01_zero_call.json`, `diag02_decode_sanity.json`,
  `diag03_paired_controls.json` + the three harness scripts).

## 1. Causal ledger (AC04)

| Accepted fact | Rules out | Leaves open |
|---|---|---|
| APP exact 0/100 both f AND oracle exact 0/20 both f | APP-propagation path (`q` from L1 beliefs) as sole cause — oracle bypasses it and still scores 0 | input-side (priors), matrix, decoder, budget shared by both paths |
| syndrome_ok 0 on every APP and oracle block | "converged to wrong codeword" (that yields syndrome 1 / exact 0) | decoder never satisfies constraints: no signal, bad graph, broken adapter, or too few iterations |
| every APP block at aggregate max 180 iters (= 2x90), every oracle block at 90 | early-stop / stopping-logic bug aborting early | full-budget non-convergence |
| crashes 0, nonfinite 0, wall 238.9 s <= 900, RSS 115142656 B < 2 GiB | numerical blowup, OOM/kill, timeout | a clean, deterministic, information-less regime |
| exact / syndrome_ok / oracle counters isolated in source and record | conflation of the three signals | literal reading stands: nothing decoded, nothing verified |

Fewest-assumption hypothesis entering diagnostics: both paths share priors derived
from one Model-F, one disclosure-sizing table, one decoder — test priors first,
then matrix/decoder sanity, then paired controls.

## 2. Diagnostics (AC05 + AC06)

D1 (0 calls, read-only accepted NPZ): actual Model-F channel CE at `n=64` is
`L1=4.99999`, `L2=4.99966`, `joint=9.99964` bits vs frozen sizing constants
`3.814742 / 3.347605 / 7.162347`. Prior mass on truth `~= 0.03124 ~= 1/32`
(uniform) on every sampled block, both layers, including oracle. Root texture:
counts sum `262144` over `1048576` cells (mean cell `0.25`) vs smoothing
`lambda*=137.38` — smoothing dominates ~550x; `H(Alice)=9.9932/10` bits,
`H(A|B)=9.9996` bits, i.e. `I(A;B) ~= 0`. Disclosure need at actual CE:
`m1/m2 = 64/64 (f=1.0)`, `77/77 (f=1.2)` vs frozen `49/43`, `59/52`.
At `f=1.2` the need (77) exceeds the mothers themselves (59/52).

D2 (0 calls, mothers rebuilt exactly as formal defaults — L1 `(64,59,59,s501)`,
L2 `(64,52,52,s502)`): rank is full on all four frozen prefixes
(49/59/43/52), but every prefix fails the strict 11-gate audit
(`STRUCTURE_BLOCKED`): `H1[:49]` has 1 zero column / 2 components,
`H2[:43]` has degree-1 variables, full mothers carry base-pair duplicates.
G1-width prefixes were never covered by the N=1024 structure PASS.

D3 (0 calls): core GF32 tables == historical v35 tables (32x32 mul exact match,
add == XOR), syndrome cross-match on 12 trials, rank cross-match on 4 prefixes.
No field/order/orientation mismatch across H / symbols / syndrome / prior.

T-a/T-b (8 calls): delta-prior and 0.85-prior recovery exact=1 on all four
frozen prefixes — adapter path (shapes, dtypes, syndrome handoff, exact
extraction) is intact; decoder returns exact when the prior points at truth.

F1 (4 calls): decoy-peaked priors (6 misled positions, forcing real BP) converge
exact=1, syndrome_ok=1 in 1 sweep on all four frozen prefixes. Graph + decoder
machinery genuinely decode with signal; D2 defects are non-blocking with signal.

F2 (12 calls, paired, first 4 formal seeds `2026090600..03`, identical
sample/seed within pair): APP-layered formal-prior path 0/4 exact, 0/4 syndrome,
180/180 iters (reproduces the formal signature); oracle-L2 same blocks 0/4
exact, 0/4 syndrome, 90/90 iters. Prior axis (APP-fed -> oracle-true-U1) changes
nothing: APP propagation is not the cause.

F3 (4 calls, rows axis only): same blocks, oracle prior, `H2[:43]` -> full
`H2[:52]`: still 0/4. More rows within available mothers do not help.

F4 (1 call, cap axis only): block `2026090600`, oracle, `max_iter` 90 -> 180:
still fails at 180. Not a cap problem.

## 3. Call / resource accounting (AC06 budget)

Total development decoder calls: 29 (T 8 + F1 4 + F2 12 + F3 4 + F4 1) of 300.
Diagnostic wall: 0.34 + 0.23 + 12.30 ~= 12.9 s of 2 h operator budget.
Per-call wall max ~= 1.5 s (F2a layered), all <= 120 s outer watchdog.
Peak RSS 113790976 B < 2 GiB. Every control recorded input identity, changed
axis, calls, exact, syndrome, iterations, nonfinite, wall, RSS in the JSONs.
No formal CLI invocation, no formal-root write, no VOID content read.

## 4. Rejected hypotheses

- `DECODER_OR_FIELD_INTEGRATION_DEFECT`: rejected (D3 exact table/syndrome/rank
  match; F1 nontrivial convergence on frozen prefixes).
- `APP_MODEL_PROPAGATION_DEFECT` (as primary): rejected (F2b oracle fails
  identically on paired samples; oracle bypasses the APP path).
- `ITERATION_DYNAMICS_STAGNATION`: rejected (F4 doubles the cap, still fails;
  F1 converges in 1 sweep with signal — dynamics are healthy).
- `MATRIX_PREFIX_OR_RANK_DEFECT` (as primary): rejected as primary, carried as
  secondary (D2 audit failures are real but F1 proves they do not block decoding
  with signal; rank is full everywhere).
- "a few more rows" fix: rejected (F3 full-disclosure control fails; D1 need
  64/64 at f=1.0 = rate 0, 77/77 at f=1.2 = impossible in these mothers).

## 5. Selected bucket

`FINITE_LENGTH_DISCLOSURE_INSUFFICIENT` — sole primary, single-assumption account:
the accepted Model-F delivers ~uniform priors (`I ~= 0`), while frozen disclosures
were sized from stale CE constants far below the actual CE. Frozen rows sit below
the Slepian-Wolf need (need 64/64 vs have 49/43 at f=1.0; need 77/77 vs have
59/52 at f=1.2), so neither APP nor oracle (the APP path's upper bound) can
recover; BP with uniform priors never hits the random target syndrome
(syndrome 0 + saturation). F1/F3/F4 confirm: signal fixes it, rows/cap do not.

## 6. Implementation rationale: no code change (Phase C)

No implementation defect was found — decoder, field, adapter, matrix builders,
and audit math all behave as frozen-specified. The shortfall is the frozen
operating point (stale CE constants vs accepted Model-F actual CE), and changing
frozen thresholds/rows/semantics to alter the failed outcome is explicitly
forbidden. `F3` shows no in-scope stronger prefix repairs the boundary, so there
is no evidence-implied minimal correction and no OpenSpec/code diff. Exploratory
diagnostics gain no pass/accepted fields.

## 7. Residual uncertainty

1. Why the accepted Model-F is smoothing-dominated (counts scale vs `lambda*`,
   CAL-only session physics) is input-domain and out of scope — not adjudicated.
2. D2 prefix audit failures are carried secondary: non-blocking with strong
   signal (F1) but untested under weak-but-nonzero signal.
3. Paired controls use a minimal 4-block discriminating sample; the formal
   100-block zeros corroborate the same signature.

## 8. Exact main-thread next decision (single route fork)

`G1_ATTRIBUTION_ROUTE_DECISION`: authorize or reject ONE next development
diagnostic — oracle-L2 recovery at full square disclosure (`m = n = 64`,
new 64-row mother, uniform Model-F priors, 4 paired seeds, ~= 4 decoder calls):
pass proves decoder/matrix sufficiency at zero rate and isolates the shortfall
purely to disclosure-vs-actual-CE; fail re-implicates matrix/decoder despite F1.
This needs a non-frozen mother build, so it is returned — not run — here.
Terminal gate: `NEXT = G1_ATTRIBUTION_ROUTE_DECISION` (square-disclosure oracle probe: approve / reject / redirect).
