# Proposal — V72P2D10 mixed-degree L1 finite discriminator (R1 + R2 connectivity/rank revision)

Change: `v72p2d10-mixed-degree-l1-finite-discriminator`
Cycle: `V72P2D10-MIXED-DEGREE-L1`
Track: implementation/readiness (no EXPLORE/DECIDE execution; no decoder/DE/CAL/VAL/real-data).
  R1 readiness/design was `EXPLORE_HEAVY`-adjacent; R2 is readiness-only amendment (R201).
  No execution is authorized by this change.
Predecessor: `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`
  (accepted 2026-09-14; sole selected candidate `lam_d2_0.45_d3_0.55`).
Authority:
  - R1: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_FINITE_READINESS_R1_TASK_PACKET.md`
    (sole R1 requirement source; F01–F12, all complete, evidence retained).
  - R2: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_CONNECTIVITY_R2_TASK_PACKET.md`
    (sole R2 requirement source; R201–R212; read fully first).
R1 evidence (retained, immutable):
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/READINESS_R1.md`,
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/EXPLORATION_LOG.md`,
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/INDEPENDENT_REVIEW_R1.md`.
Main-thread decision: `REVISE_REQUIRED_CONNECTIVITY_AND_RANK` (F4 blocker:
  R1 profile shows 9–68 Tanner components per graph, largest-component fraction
  0.039–0.297, and GF32 rank below `m` in several cells — confounding the
  degree-profile test; R1 batch not authorized).

## 1. What (R1 frozen; R2 amends construction/admission only)

R1 freeze (unchanged, see §3): the smallest finite-length L1-only experiment
testing whether the D9-selected mixed degree distribution (edge-perspective
`lambda2 = 0.45`) restores reproducible syndrome-valid/exact L1 recovery
relative to a matched regular-DV3 control at f1.2 and n64/n128/n256 — before
any behavior edit or decoder call. R1 froze the two-arm isolation contract, the
accepted D9 f1.2 integer realizations, graph/block seeds, coefficient-stream
rule, paired call order, structural gates, 144-call matrix with
positive/negative/ambiguous/engineering-blocked rules, conditional progression,
terminals/routing, one fresh future root (absent, unauthorized) and budgets.

R2 revision (this amendment, R201): keeps the entire R1 scientific contract
(§3) byte-identical and changes ONLY the graph-construction mechanics and the
pre-decoder admission so that every one of the original 18 cells is a single
connected full-rank Tanner graph before any decoder binding:

1. the two-arm isolation contract (`PEG_DV3_MATCHED` vs
   `PEG_DV23_LAM2_045`): one construction algorithm, one tie-breaking policy,
   one graph-seed set, one prior chain, one decoder/schedule/cap/damping, one
   field and one coefficient-distribution rule; the candidate may differ only
   where its degree/socket profile forces it (R202; `design.md` §1–§2);
2. the accepted D9 f1.2 integer realizations transcribed exactly
   (`design.md` §3) — no re-derivation, no rounding change;
3. the three predeclared graph seeds per width with their R1 assignment, the
   eight block seeds per width, the deterministic coefficient-stream rule, the
   paired call order and the block sampler (`design.md` §4);
4. R2 admission predicates that must ALL pass before any decoder binding —
   exact degrees/socket balance, simple graph, exactly one connected component
   over all `n+m` Tanner nodes, deterministic structural rank `m`, exact GF32
   rank `m`, deterministic replay equality — with four-cycle/girth/ACE as
   reported diagnostics only (R202–R205; `design.md` §2/§5);
5. the paired 2 arms × 3 widths × 3 graphs × 8 blocks matrix (<=144 scientific
   L1 calls), predeclared thresholds, conditional width progression, terminal
   set and routing (`design.md` §6–§7) — unchanged;
6. one fresh future root (verified absent) and the exact future command, left
   absent and unauthorized, plus the frozen budgets (`design.md` §8) —
   unchanged; the R1 `BATCH_AUTHORIZED` source-constant flip is replaced by an
   explicit CLI execution-authorization argument defaulting false (R206), and
   `--verify` stays fail-closed (R207).

## 2. Why (R1 + R2)

R1 text retained: D9 accepted `lam_d2_0.45_d3_0.55` from a DE-only ensemble
screen (`stable_converged` 8/8 at both f1.2 populations, AUT_30 ratio 0.7453
vs DV3). The DE terminal is not a decoder result; DE-to-row-layered
equivalence is unproven and finite-length `{2,3}` behavior is open. D6 recorded
0/40 L1 exact/syndrome for its DV3-family graphs. The mixed distribution must
be tested as a base L1 code at accepted f1.2 row counts with a matched
constructor, multiple graph seeds and paired blocks.

R2 addition: the accepted R1 independent review (PASS_WITH_FINDINGS) recomputed
all 18 graphs exactly and confirmed the F4 interpretation caveat as measured
fact: every R1 Tanner graph is fragmented (9–68 components; largest fraction
0.039–0.297) and several parity-check matrices are GF32 rank-deficient
(e.g. 58/59, 116/118, 233–235/236). The main thread elevated F4 from
non-blocking caveat to scientific readiness blocker: a decoder comparison on
these graphs would compare different component decompositions and effective
constraint ranks, not just the forced variable-degree profile. R2 therefore
requires connected full-rank construction under the frozen seeds/degrees
before any decoder binding. If any of the 18 original cells cannot pass
without changing a frozen item, the terminal is
`BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION`, not a seed change.

## 3. Scope (frozen R1 contract + R2 delta; see `design.md` and `specs/`)

R1 frozen contract (preserved exactly by R2; equality checked in R211):

- Two arms only (design §1): `PEG_DV3_MATCHED` (regular degree 3 control) and
  `PEG_DV23_LAM2_045` (`lambda2 = 0.45` candidate), same deterministic
  degree-sequence PEG family, same seeds, same decoder contract.
- Degree tables (design §3): DV3 `(n2,n3,E) = (0,64,192)/(0,128,384)/
  (0,256,768)`, check `3^44+4^15` / `3^88+4^30` / `3^176+4^60` at
  `m = 59/118/236`; mixed `(35,29,157)` with `2^20+3^39`, `(71,57,313)` with
  `2^41+3^77`, `(141,115,627)` with `2^81+3^155`. Transcribed from accepted D9
  `design.md` §5; cross-checked against D9 root `summary.json` `graph.cells`.
- Graph seeds with R1 assignment (design §4.1): n64
  `2026092201,2026092202,2026092203`; n128 `2026092204,2026092205,2026092206`;
  n256 `2026092207,2026092208,2026092209`. No addition/replacement/re-roll
  after any decoder result; R2 permits ZERO replacement seeds (R1
  `PROFILE_REPLACEMENT_SEEDS 2026092210..2026092215` retired — see design
  §4.1).
- Block seeds (design §4.3): n64 `2026092301..2026092308`; n128
  `2026092311..2026092318`; n256 `2026092321..2026092328`; paired blocks
  sampled once per `(width, block_seed)` via accepted `sample_matched_block`.
- Model-F root `workspace/v72p2d5_model_f_input/20260907_r1` (CAL-only) and
  prior chain `prepare_model_f_prior_candidate` -> `marginalize_f_to_p1` ->
  `_floor_renorm(DECODER_FLOOR=1e-15)` (design §4.4); no VAL/real-data.
- Field `q=32, poly=37`; coefficient rule
  `v10_seed(f"d10:coeff:{width}:{graph_seed}")` -> `default_rng` -> one
  `integers(1,32)` per edge in sorted `(variable,check)` order (design
  §2/§4.2); same rule both arms.
- Decoder `v35.decode_row_layered_fftqspa`, `max_iter=90`,
  `damping_alpha=1.0`, cold (`warm_beliefs=None`); exact/syndrome reported
  separately with provenance + residual weight; `undetected` never merged
  (design §4.5).
- Thresholds POSITIVE/NEGATIVE/AMBIGUOUS/ENGINEERING_BLOCKED, conditional
  n64→n128→n256 progression, terminals/routing (design §6) — unchanged.
- Budgets (design §6.1/§8): <=144 scientific L1 calls; <=44 setup units
  (18 constructions + 24 block samplings + 2 fixed); wall <=1800 s; per-call
  <=120 s (between/after); RSS <2 GiB strict; single process; no
  retry/resume/seed-search/adaptive-stop.
- Fresh root UUID `b2dd13e4-6600-4e27-90df-5c9038cf2c34` (verified absent) and
  the exact future command; left absent and unauthorized.
- Claim ceiling (design §7): synthetic finite-length L1-only diagnostic under
  CAL-only Model-F prior; no L2/APP, FER, leakage, SKR, qualification,
  promotion or real-data claim; D7-H not revived.

R2 delta (construction/admission mechanics only; `design.md` §2/§5/§8, spec):

- R202 connectivity-first degree-sequence PEG: spanning backbone over every
  variable and check node respecting exact target degrees, then shared
  PEG/ACE fill; parallel edges and degree/socket mismatch rejected.
- R203 deterministic maximum bipartite matching; `structural_rank == m`
  required (all `m` checks covered).
- R204 frozen-rule coefficients + exact GF32 row rank; `gf32_rank == m`
  required; failure records the cell and stops, no seed/coefficient change.
- R205 six-predicate admission before decoder binding (degrees/socket,
  simple graph, exactly 1 component over `n+m` nodes, structural `m`, GF32
  `m`, deterministic replay); 4-cycle/girth/ACE diagnostics only.
- R206 explicit CLI execution-authorization argument (defaults false; refuses
  `--batch` before root/decoder binding), replacing the constant flip.
- R207 `--verify` fail-closed for partial/engineering-blocked roots.

## 4. Non-goals (hard prohibitions; R1 + R2)

R1 prohibitions retained: no production decoder call in a readiness call; no
scientific L1 batch without separate explicit authorization; no L2/APP,
oracle-L2, f1.0, square point or alternation; no D7-H revival; no broader
degree search/optimizer/adaptive rule; no modification of v35, V26, D5–D9
code, Model-F artifact or frozen baseline; no generalized graph library,
framework, checkpoint, cache, integrity manifest or new dependency; no
CAL/VAL/raw/real-data contact; no output-root creation in readiness; no
authorization granted by design/tests/review; no commit or push (R201/R212).

R2 prohibitions added (packet §2/§7): no replacement seeds, no seed search, no
topology selection across candidates, no threshold tuning, no decoder
feedback, no adaptive construction, no coefficient repair/reseeding; R201
writes OpenSpec only (no code, no tests, no decoder, no batch, no root
creation); R210 is no-decoder `PROFILE_ONLY` for exactly the original 18
cells with zero decoder calls/binds.

## 5. Claim boundary

Readiness establishes only that the two-arm L1 discriminator is mathematically
specified, construction-bounded, structurally gated, threshold-frozen and
mechanically routable — R2 additionally establishes that all 18 admitted
graphs are each one connected full-rank Tanner graph under the frozen
seeds/degrees (if the R2 gate passes). It establishes no decoder success, no
DE-to-decoder equivalence, and no
finite-length/FER/leakage/SKR/qualification/promotion/real-data claim. A
future positive result authorizes at most a separate L2/APP integration
proposal, and D7-H still does not auto-revive. R201 grants no execution.
