# R10 CTRL (m100, same-session control) — RESULT (DECIDE solidification, no execution)

Track: DECIDE. Main-thread ACCEPTANCE granted: contrast 1 (R10) vs 1 (R9) → ≤2 → RATE-ADAPTIVE TRACK; prior-match line CLOSED (with PPLN-vs-Type2 setup-confound caveat). Recorded, not re-judged. No execution/data/commit in this file.

## W-ev (quoted operator return)

- exit 0; wall 114s OPERATOR-ATTESTED; RSS ~158MiB OPERATOR-ATTESTED.
- sci 128/128, setup 4.
- counts: attempted 128 / accepted 1 / exact 1 / undetected 0.
- fractions: 0.0078125 (1/128); FER_proxy 0.9921875 (127/128).
- disclosure: 72192 = 128 x 564 bits.
- beta: -0.31624 / -0.36725, derived-only (never hand-filled).
- net: 140 = 1 x 28 x 5 secret symbols; plain 1-frame facts.
- iters: 21/90 (sole success converged at 21 of max 90).
- sole exact: call 86 / frame 2026 / seed 4720 / iters 21 / residual 0.
- verify: 128/0 (all 128 verification-invoked, 0 undetected).

## Provenance

- Zero replacement (single authorized invocation; no rerun/repair/retune).
- Truth post-decision (Alice reference used only for post-decision accounting, never as decoder input).
- Protected clean (predecessor/frozen inputs unmodified; no-overwrite holds).
- No commit/push (solidification record only).

## Artifact paths

- Single authorized UUID root under `workspace/` (4 files, per operator return; sole execution root).

## Claim ceiling

- Control-contrast only: R10 1/128 in-session == R9 1/128 cross-session → prior-match line CLOSED.
- Setup-confound caveat retained: PPLN-vs-Type2 setup difference noted, not a blocker for the contrast routing.
- No SKR / qualification / promotion / generalization / route-closure claim.

## Acceptance block

- Execution grant "继续往下" consumed once — single root.
- Pre-EXECUTE Q1-Q6 per operator return (branch, cleanliness, frozen contract, authorization, output absence, focused tests).
- Pre-RESULT reviewer-go PASS (X1-X10, transcribed in INDEPENDENT_ACCEPTANCE.md).
- Main-thread ACCEPTED contrast routing to rate-adaptive track.
