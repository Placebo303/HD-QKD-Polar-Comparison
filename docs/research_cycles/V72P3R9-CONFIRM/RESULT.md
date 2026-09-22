# R9 CONFIRM (m100, P-1p5M-tail) — RESULT (DECIDE solidification, no execution)

Track: DECIDE. Main-thread ACCEPTANCE granted: FIRST_REAL_RECOVERY_CONDITIONAL (existence-only). Recorded, not re-judged. No execution/data/commit in this file.

## Z-ev (quoted operator return)

- exit 0; wall 103.21s OPERATOR-ATTESTED; RSS ~207.7MiB OPERATOR-ATTESTED.
- sci 128/128, setup 4.
- counts: attempted 128 / accepted 1 / exact 1 / undetected 0.
- fractions: 0.0078125 (1/128); FER_proxy 0.9921875 (127/128).
- disclosure: 72192 = 128 x 564 bits.
- beta: -0.3162395204930091 / -0.36724572961137003, derived-only (never hand-filled).
- net: 140 = 1 x 28 x 5 secret symbols; rate 0.001708984375; plain 1-frame facts.
- iters: 24/90 (sole success converged at 24 of max 90); syn/tag 1 (syndrome+tag verified).
- sole exact: call 34 / frame 2140 / seed 4720.
- frames: 2123..2186 (64-frame window, K=2 even-odd = 128 calls).
- verify: 128/0 (all 128 verification-invoked, 0 undetected).

## Freeze authorities

- k_sym = 28 <- runner L70 + L17-19 (m100 nominal; never hand-filled in prereg, now frozen by runner authority).
- Prior path <- runner L28-30 / L85 + pre-execute L310-311, with cross-session caveat (Model-F marginal read-only; source session differs from target window — caveat retained, not a blocker for existence-only claim).

## Provenance

- Zero replacement (single authorized invocation; no rerun/repair/retune).
- Truth post-decision (Alice reference used only for post-decision accounting, never as decoder input).
- Protected clean (predecessor/frozen inputs unmodified; no-overwrite holds).
- No commit/push (solidification record only).

## Artifact paths

- Single authorized UUID root under `workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d` (4 files, per operator return; sole execution root).

## Claim ceiling

- Existence-only: FIRST real-data recovery in project history (1 accepted, undetected 0, net 140).
- No SKR / qualification / promotion / generalization / route-closure claim.

## Acceptance block

- Execution grant "可以继续" consumed once — single root + contiguous block IDs 0..127.
- Pre-EXECUTE Q1-Q6 per operator return (branch, cleanliness, frozen contract, authorization, output absence, focused tests).
- Pre-RESULT reviewer-go PASS.
- Main-thread ACCEPTED FIRST_REAL_RECOVERY_CONDITIONAL.
