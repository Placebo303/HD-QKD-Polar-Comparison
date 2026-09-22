# Proposal — V72P2D8 rate-aligned GF32 ensemble feasibility (L1-first)

Change: `v72p2d8-rate-aligned-gf32-ensemble-feasibility`
Cycle: `V72P2D8-RATE-ALIGNED-ENSEMBLE`
Track: `EXPLORE_HEAVY` (readiness/implementation; no DE scientific sweep authorized here)
Predecessor: `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`
(accepted facts: L1 exact/syndrome 0/40, L2-APP 5/40, L2-oracle 35/40,
end-to-end APP exact 0/120, T1 PEG-DV3 silent at n64/n128/n256; closes only the
eligible-only DV3 topology substitution, no graph-family-impossibility claim).
Authority: `.workbuddy/tasks/D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY_R1_TASK_PACKET.md`
(sole requirement source; E01–E06 frozen in this change, E07–E12 future).

## 1. What

Freeze the smallest scientifically defensible **rate-aligned GF32 ensemble
feasibility contract** that can advance exactly one variable-degree-distribution
candidate into a future finite-length decoder packet **before** another decoder
batch runs. The contract reuses the accepted V26 Monte-Carlo density-evolution
kernel unchanged, adds one thin L1 Model-F channel adapter, and freezes a
bounded deterministic candidate family, rate/check-row mapping, DE
observables/budgets, advancement rule, terminal states and claim ceiling.

This change is documentation + OpenSpec + readiness only (E01–E06). No
production code, no DE sweep, no decoder, no real/CAL/VAL/raw data contact, no
output root, no commit authorization.

## 2. Why

D6 closed DV3 topology substitution at the unchanged Model-F channel. The next
orthogonal variable is the ensemble/degree distribution itself
(packet §2). Existing DE machinery exists and is accepted (V26/V27/V37); the
missing piece is a contract that pins the current Model-F L1 channel into an
accepted DE representation, maps the accepted D5/D6 row budgets to a code rate,
and bounds the candidate search so the future sweep cannot drift into an
adaptive or unbounded optimizer.

## 3. Scope (frozen; see `design.md` and `specs/`)

- Reused DE engine: `nonbinary_v26_mcde.run_mcde_posterior` (q=32, GF(32) poly 37)
  with the exact delta list in `design.md` §1.
- Channel: accepted CAL-only Model-F artifact
  `workspace/v72p2d5_model_f_input/20260907_r1` → E2 concentration-backoff
  `P_F` → `P1 = marginalize_f_to_p1` → decoder floor `1e-15` → per-sample
  true-symbol XOR centering; 32-ary posterior rows preserved exactly (no
  BSC/AWGN/q-SC/scalar surrogate).
- L1-first; L2 excluded from the sweep (read-only comparator only).
- Rate/check-row mapping to the accepted D6 row budgets (n64 L1 (49,59,64),
  L2 (43,52,64); n128/n256 ×2/×4), rate `R = 1 - m/n`, `ρ = make_rho(R, λ)`.
- Deterministic bounded candidate family: edge-perspective λ over degree
  support {2,3}, grid step 0.05, exactly 21 candidates; hard cap 21;
  regular-DV3 baseline `λ={3:1}` included; canonical IDs and lexicographic
  order; no adaptation to outcomes.
- Future DE sweep: 2 rate conditions × 3 frozen seeds = 126 DE calls,
  n_samples 4000, max_iter 60, entropy tol 1e-4 bits, V26 streak; wall ≤1800 s,
  per-call ≤120 s, RSS <2 GiB; no retry/resume/seed search.
- Advancement to exactly one candidate by a frozen rank key; terminal states
  and the bounded-search claim ceiling in `design.md` §5.
- Fresh future root UUID `5edf0630-f357-4a7e-b4c5-9ba955021405` (verified
  absent) and exact future command; left absent and unauthorized.

## 4. Non-goals (hard prohibitions)

No production decoder call; no DE scientific sweep; no CAL/VAL/raw/real-data
contact; no D7-H revival; no L2 joint optimization; no coefficient/graph search
beyond the frozen family; no finite-length construction in this change; no
generalized optimizer/workflow/cache/checkpoint/integrity machinery; no new
dependency; no output-root creation; no authorization grant by implementation,
tests or reviews; no commit or push in the readiness call.

## 5. Claim boundary

Readiness establishes only that the proposed DE experiment is mathematically
specified, implementation-tested, rate-aligned and executable. It establishes
no decoder improvement, no ensemble superiority, no FER/leakage/SKR,
qualification, promotion or real-data claim. A future DE advancement authorizes
neither finite-length execution nor D7-H; it generates the next finite-length
task packet.
