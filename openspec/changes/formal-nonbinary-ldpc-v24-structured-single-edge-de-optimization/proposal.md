# Proposal: formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization

> Status: FROZEN_PENDING_USER_AUTHORIZATION — P06 independent freeze review
> ACCEPT; implementation and scientific execution remain forbidden until P07.

## What

Run one bounded, falsifiable optimization of **single-edge** edge-perspective
degree distributions `(lambda, rho)` for the frozen q=1024 V17 structured
channel. The scientific target is design rate approximately 0.9375 with
`f_total <= 1.3`. This change stops at an asymptotic density-evolution (DE)
decision.

V24 reuses NumPy and the existing V22b structured Monte-Carlo DE kernel. It
does not introduce a new DE framework, a new dependency, a finite parity-check
matrix, or a decoder.

## Why

V21 closed the short-block Bob-only branch. V22 and V23 then found no
convergent point among the particular plain, SC, regular, and small irregular
single-edge ensembles they evaluated. Those results are valid negative
diagnostics for the evaluated candidates, but they are not an optimization of
the bounded single-edge `(lambda, rho)` space.

V23 also did **not** implement true protograph or multi-edge-type (MET) DE: it
reduced each base matrix to aggregate single-edge `lambda/rho` distributions
and called V22b. Therefore the accurate predecessor conclusion is
`NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`, not “MET failed” and not a
theory-wide impossibility result.

V24 is the smallest successor that closes this frozen bounded single-edge
search question: perform one pre-registered bounded search, then validate
selected candidates on seeds that were never used for search or ranking.

## Scope

- q=1024 only.
- The exact V17 model
  `nbldpc_v17_multibit_channel_model_v1`, including its declared independent
  bit-plane product approximation.
- Single-edge edge-perspective `lambda/rho` distributions only.
- Design rate `R >= 0.9375` and `f_total <= 1.3`; the bounded search is further
  restricted to `R <= 0.94140625` to stay on the predecessor target band.
- Degree cap `<= 512`.
- Between one and eight non-zero degrees on each single-edge distribution.
- Fully indexed proposal generation: one `SeedSequence([24000,k])` RNG per
  attempt, with frozen calls consumed lambda first and rho second.
- M0 read-only validation of the already accepted V8 corrected trace and
  frozen accounting checks; no V8 rerun.
- M1 bounded development search with fixed budgets and seeds.
- M2 independent holdout validation.
- M3 read-only verification, decision, and closeout.

The proposal generator contract is unique: attempt k constructs one
`default_rng(SeedSequence([24000,k]))`; using that same RNG it executes the
frozen `integers -> choice -> full -> multinomial` calls for lambda first, then
rho, over `np.arange(2,65,dtype=np.int64)` and
`np.arange(2,513,dtype=np.int64)` respectively. No alternative API, call
order, or extra RNG consumption is allowed; see design section 3.1.

## Out of scope

- True protograph topology-preserving DE or MET/multiple-edge state.
- SC-LDPC, bit-plane public disclosure, a different q, a different channel
  decomposition, or relaxation of `f_total <= 1.3`.
- Finite-code construction, lifting, parity-check matrices, decoders, FER,
  Bob-only frames, qualification, promotion, or fresh-data claims.
- Search-budget expansion, result-dependent seed changes, post-hoc threshold
  changes, or a “closest candidate” continuation.

True MET is only a possible **new change after V24 FAIL**, and only after a new
explicit user authorization. It is not a fallback inside V24.

## Decision states

- `mechanism_unverified`: M0 reference or semantic/accounting checks fail;
  M1 and M2 may not execute.
- `resource_blocked`: required frozen evaluations remain when the completed-
  DE-call 24-hour ceiling is reached, or an external interruption prevents
  completion; no scientific PASS/FAIL is claimed.
- `pass`: at least one pre-selected finalist satisfies every validity and DE
  requirement on every pre-registered holdout seed.
- `fail`: M0 passed and the frozen M1/M2 budget completed, but no finalist
  passes every holdout seed.

All evaluated and rejected candidates remain evidence. `pass` means only
“ready to propose a separate finite-code change.” It is not finite-length
success, FER evidence, qualification, or promotion.

Profile validity is determined before DE and only from lambda/rho, degrees,
support, rate, and `f_total`. A DE error or non-finite entropy does not make the
profile invalid: it consumes its frozen evaluation slot and ranks as
non-converged with `+inf` entropy.

After a completed call is recorded, completion has priority over the time
ceiling: if all frozen evaluations are complete, V24 computes PASS/FAIL even
at or beyond 24 hours. `resource_blocked` applies only when required
evaluations remain.
