# V8 V7-Interpretation Audit (additive; V7 files untouched)

Date: 2026-08-04
Change: `formal-nonbinary-ldpc-v8-reference-reproduction`
Operator: implementation operator (coder-fast); acceptance and scientific
gates remain with the main thread.

## Purpose

This is an **additive audit record**. No V1-V7 source, plan, result,
transcript, manifest, or evidence file was modified, deleted, reinterpreted,
or rerun. It corrects only what conclusions may be drawn from the V7
evidence, per `docs/nonbinary-ldpc-v7-audit-v8-plan.md` and the V8
proposal/design.

## 1. Engineering PASS vs canary failure are separate

The V7 routes passed their frozen engineering tiers (T0-T3 package tests)
and still failed their pre-registered scientific canary gates. Engineering
acceptance means the implementation met its frozen package tests; it does not
prove the underlying scientific model matches the intended literature
construction.

| Route | Frozen observed result (immutable) | Valid conclusion |
|---|---|---|
| V7 R1A | p=.20 0/4; p=.30 0/4 | Implemented short (2,3) mother candidate failed canary |
| V7 R1B | p=.20 3/4; p=.30 0/4 | Extra-observation diagnostic failed; NOT formal single-observation IR evidence |
| V7 R2 | p=.20 0/4; p=.30 0/4 | Implemented scalar-DE surrogate failed; full-vector paper route remains untested |
| V7 R3 | p=.20 0/4; p=.30 0/4 | Implemented GF(32)xGF(32) EMS candidate failed at layer 0 |

## 2. R1B = out-of-contract extra-observation diagnostic

R1B combines Bob's observation with a **second independently corrupted
observation synthesized from Alice**. The project's reconciliation contract
gives Bob **one** paired-symbol observation plus public disclosure. A second
observation synthesized from Alice is not public disclosure and not a second
Bob observation; therefore R1B's 3/4 at p=.20 is an algorithmic diagnostic
result, not a formal single-observation IR success claim. No V7 evidence was
rewritten; only the scope of the claim is re-recorded.

## 3. R2 = unvalidated scalar two-level DE surrogate result

R2's density evolution projects every q-ary message onto a scalar two-level
ratio (`R_hi`/`R_lo` and closed-form `(P0,P1)` convolutions), i.e. **scalar
ratios, not full q-vector messages**. The literature construction instead
evolves full length-q probability vectors, uses edge-perspective degree
distributions, samples actual node degrees, includes channel evidence at
every variable update, and judges convergence via message entropy. R2's 0/8
therefore tests only the implemented scalar surrogate; it does not close the
full-vector paper route.

## 4. Implications for V8

- V8 must express reconciliation in the error domain
  (`d = s + H*y = H*(x+y)`, decode `e`, reconstruct `x_hat = y + e_hat`).
- V8 must provide an independent probability-domain oracle that does not
  call V1-V7 FFT/FWHT/check-update/decoder functions.
- V8 must implement full-vector MC-DE (length-q messages) with exact sampled
  degrees, edge-perspective distributions, and fresh channel terms, with
  golden regressions that expose the old R2 missing-channel and
  fixed-`dv_max` behavior.
- V8 must reproduce at least one precisely sourced published q-ary QSC
  result before any project adaptation.
- V8 produces engineering evidence only: no canary, development,
  confirmation, real-data, N4, or formal comparison execution, and no new
  official output root.
