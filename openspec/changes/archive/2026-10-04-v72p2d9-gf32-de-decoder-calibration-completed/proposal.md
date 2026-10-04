# Proposal — V72P2D9 GF32 DE-decoder calibration and threshold (R1)

Change: `v72p2d9-gf32-de-decoder-calibration`
Cycle: `V72P2D9-DE-DECODER-CALIBRATION`
Track: readiness/implementation now (C01–C06, documentation + OpenSpec only);
the frozen future calibration batch is `EXPLORE_HEAVY` and requires a separate
explicit authorization.
Predecessor: `D8_DE_SWEEP_RESULT_ACCEPTED_ROUTE_TO_D9_CALIBRATION`
(accepted 2026-09-14; winner none; terminal `D8_DE_BASELINE_NOT_CONVERGED`).
Authority: `.workbuddy/tasks/D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`
(sole requirement source; C01–C06 frozen in this change, C07–C12 future).

## 1. What

Freeze the calibration contract that decides whether the accepted V26 MC-DE
convergence window (lambda2 0.45/0.50 primary f1.2 3/3) is a genuine ensemble
threshold signal, a Monte-Carlo stability artifact, or a
V26-DE-versus-v35-decoder semantic mismatch — **before** any further DE run or
finite-length decoder call. The change freezes:

1. the stage-by-stage V26↔v35 semantic map with exact code pointers,
   match/approximation/mismatch boundaries and an explicit equivalence ceiling;
2. the prospective scientific role of f1.0 (`BOUNDARY_DIAGNOSTIC`) with a
   frozen rate/information-margin criterion that is independent of the D8
   outcome;
3. deterministic finite-graph degree/socket realization rules for the
   `{2,3}` lambda support at n64/n128/n256 with the full feasibility table;
4. the minimal bounded stability/control matrix (regular-DV3 + 0.45, 0.50 and
   the 0.55 upper-flank control), seeds, populations, budgets and decision
   rules;
5. terminal/routing hooks so the future result is mechanically routable
   (semantics block, stability failure, selection, graph-invalid);
6. one fresh future calibration root (verified absent) and the exact future
   command, left absent and unauthorized.

## 2. Why

The accepted D8 sweep showed regular-DV3 0/3 at both conditions and 0
candidates passing the frozen both-condition rule, while lambda2 0.45 and 0.50
converged 3/3 at the primary f1.2 condition only. Before spending any
finite-length decoder budget, D9 must separate four hypotheses: C1 genuine
threshold window, C2 DE/decoder semantic mismatch, C3 Monte-Carlo instability,
C4 f1.0 gate-role mismatch. The D7-A certification already proved the check
kernel and tree posteriors; what remains unchecked is the *full* message-path
semantics (channel/prior chain, coefficient direction on both sides, variable
update, observable/stop metric, schedule correspondence) and the finite-graph
realizability of the D8 mixtures.

## 3. Scope (frozen; see `design.md` and `specs/`)

- Semantic map (design §2): channel centering/prior/floor; coefficient
  permutation + syndrome/coset centering; variable node; check node; posterior
  metric vs decoder output; flooding DE vs row-layered sweep; stopping metric.
  Every claim cites a real path:line.
- Equivalence ceiling (design §3): primitive same-input check-update equality is
  certified (D7-A `D7_A_DECODER_CERTIFICATION_PASS`, D8 unit-coefficient
  cross-kernel test); flooding-DE ↔ row-layered equivalence, DE-convergence ↔
  decoder-convergence, and any finite-length/FER claim are NOT established.
- f1.0 role (design §4): `BOUNDARY_DIAGNOSTIC`, derived from
  `H_L1=3.814742`, disclosure `5m/n`, margin `mu = 5m/n - H_L1`, frozen
  criterion `mu >= 0.05 bits/symbol` (and rate margin `>= 0.01`). f1.0 margin
  is `+0.013383` bits/symbol (0.35 % of `H_L1`): boundary, not a hard gate.
- Degree realization (design §5): reuse
  `v37_degree_feasibility.edge_to_node_distribution` /
  `largest_remainder_counts` / `calculate_node_degree_counts` /
  `calculate_total_sockets` / `calculate_check_degree_allocation` /
  `analyze_degree2_subgraph`; full table for baseline, 0.45, 0.50, 0.55 at all
  widths and both conditions; realized apportionment exact numbers, rate
  preservation identity, min check degree >= 2, realized max <= 4, all cells
  forest-feasible.
- Future calibration matrix (design §6): 4 candidates x f1.2 primary (4000 and
  16000 samples) + f1.0 boundary diagnostic (4000 samples only), 8 seeds
  (3 D8 reproduction + 5 fresh), <=96 DE calls + <=12 setup, wall <=1200 s,
  per-call <=300 s, RSS <2 GiB strict, single process, no retry/resume/seed
  extension/adaptive stop.
- Fresh root UUID `10076f83-d752-4bac-9161-d8b0907d951b` (verified absent) and
  the exact future command; left absent and unauthorized.

## 4. Non-goals (hard prohibitions)

No production decoder call in the readiness call; no scientific DE sweep; no
D7-H revival; no broader degree search or adaptive rule; no v35/V26/channel
modification; no generic DE framework, optimizer, graph library, checkpoint,
cache or new dependency; no CAL/VAL/raw/real-data contact; no output-root
creation; no authorization granted by implementation, tests or reviews; no
commit or push in the readiness call.

## 5. Claim boundary

Readiness establishes only that the calibration contract is mathematically
specified, semantically anchored, bounded and mechanically routable. It
establishes no finite-length/FER/leakage/SKR/qualification/promotion/real-data
claim and does not reinterpret the D8 terminal or its winner=none. A future
selected ensemble authorizes only the next finite-length synthetic task packet.
