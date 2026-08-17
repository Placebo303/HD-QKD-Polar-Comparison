# Design: formal-nonbinary-ldpc-v21-bob-only-selector-validation

## Status
DRAFT — based on V20 audit and `docs/nbldpc-v21-bob-only-plan-20260816.md`.

## Problem
V20 cascade uses Alice truth to decide when to run bounded4 and which top-K
candidate to accept. Bob cannot execute that policy. V21 must provide a
Bob-executable selector.

## Strategies
- **S0 BP-only**: accept FFT-QSPA output if syndrome-consistent, else fail.
- **S1 bounded4-only**: always run `bounded_weight_ml_decode(max_weight=4)` and
  accept its unique candidate.
- **S2 BP-first-fallback-bounded4**: accept BP candidate when syndrome-consistent;
  otherwise run bounded4 and accept its candidate.

All strategies use only `(field, matrix, syndrome, w, max_iter)`.

## Metrics
- `exact_correct`: single selected candidate equals Alice (offline).
- `exact_mismatch`: syndrome-consistent but not Alice.
- `decode_failed`.
- `candidate_list_contains_alice` and `alice_rank`: diagnostic only.
- `f_plain` and `f_total` (including public/verification bits).

## Verification
- Static AST check: decoder functions must not reference `alice`.
- Runtime injection: replacing Alice array must not change selected candidates.
- Offline metric phase is the only place Alice is used.

## Stop gate
If all Bob-only strategies have FER >= 0.45 on >=64 fresh frames, freeze the
short-block OSD/top-K branch and move to V22 structured construction.
