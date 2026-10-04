# Spec delta — V72P2D10 mixed-degree L1 finite discriminator (R1 + R2)

R1 SHALL set retained (F01–F12 evidence immutable). R2 delta (R202–R207)
amends construction/admission mechanics only; every frozen R1 scientific
input below is preserved exactly and any conflict resolves in favor of the
frozen item (STOP with `BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION`).

## SHALL (frozen R1 + R2 delta)

- The discriminator SHALL contain exactly two arms, `PEG_DV3_MATCHED`
  (regular variable degree 3 control) and `PEG_DV23_LAM2_045` (D9-selected
  `lambda2 = 0.45` mixed `{2,3}` candidate), and both arms SHALL share the same
  graph-construction algorithm, tie-breaking policy, graph seed set, Model-F
  L1 prior chain, row count, block seeds and paired block objects, decoder,
  schedule, iteration cap, damping, field and coefficient rule; the candidate
  SHALL differ only in its degree/socket profile and the mathematically forced
  check-degree allocation. R2: both arms SHALL share the ONE
  connectivity-first constructor and tie policy (R202); only the forced §3
  degree sequence input may differ.
- The graph construction SHALL be a minimal deterministic degree-sequence PEG
  honoring the exact variable and check degree counts of design §3, reusing
  read-only the `nonbinary_v10_peg` placement primitives (`_tie_pick`,
  `_bfs_distance`, `_ace_score`) and the `nonbinary_v10_common.v10_seed`
  derivation, with one deterministic attempt per seed and no retry loop. R2
  (R202): construction SHALL first create a deterministic spanning backbone
  touching every variable and every check node while respecting exact target
  degrees, then fill remaining sockets with the shared PEG/ACE rule; parallel
  edges and degree/socket mismatch SHALL be rejected fail-closed
  (`construction_failed`, no partial graph forwarded).
- The frozen f1.2 realizations SHALL be exactly: DV3
  `(n2,n3,E) = (0,n,3n)` with check allocation `3^44+4^15`, `3^88+4^30`,
  `3^176+4^60` at n = 64/128/256 (`m = 59/118/236`); and 0.45
  `(35,29,157)` with `2^20+3^39`, `(71,57,313)` with `2^41+3^77`,
  `(141,115,627)` with `2^81+3^155`. These integers SHALL be transcribed from
  the accepted D9 `design.md` §5 and SHALL NOT be re-derived with different
  rounding, re-selected, or repaired by R2.
- Graph seeds SHALL be exactly three per width, frozen fresh before execution
  (n64 `2026092201..03`, n128 `2026092204..06`, n256 `2026092207..09`) with
  the R1 width assignment preserved, and separate from the eight block seeds
  per width (n64 `2026092301..08`, n128 `2026092311..18`, n256
  `2026092321..28`); no seed SHALL be added, replaced or re-rolled after any
  decoder result. R2 (packet §2/§7): ZERO replacement seeds — the R1
  `PROFILE_REPLACEMENT_SEEDS 2026092210..2026092215` clause is RETIRED and
  SHALL NOT be implemented or consumed; any R2 construction/admission failure
  SHALL be retained and treated as an engineering block, never repaired by
  reseeding. The authorized batch path SHALL have no replacement mechanism.
- Coefficients SHALL be one independent uniform nonzero GF32 draw per edge, in
  sorted `(variable, check)` order, seeded by
  `v10_seed(f"d10:coeff:{width}:{graph_seed}")`; the same distribution and
  seed rule SHALL apply to both arms, with no edgewise-identity claim. R2
  (R204): the rule is UNCHANGED; no coefficient repair, reseed or search is
  permitted.
- One matched block SHALL be sampled once per `(width, block_seed)` via the
  accepted `sample_matched_block(p_b, p_f, n, seed)` before decoder dispatch
  and used identically by both arms and all three graphs at that width.
- The prior chain SHALL be the accepted CAL-only Model-F chain:
  `prepare_model_f_prior_candidate` -> `marginalize_f_to_p1` ->
  `_floor_renorm(p1[:, bob].T, DECODER_FLOOR=1e-15)` from
  `workspace/v72p2d5_model_f_input/20260907_r1`, with no VAL/real-data
  contact and no modification of the accepted artifact.
- The decoder SHALL be the production `decode_row_layered_fftqspa` with
  `max_iter=90`, `damping_alpha=1.0`, cold start (`warm_beliefs=None`),
  q=32/poly37; exact (`syndrome_ok` and `x_hat == u1_true`), syndrome-valid,
  iterations, status, belief provenance and residual syndrome weight SHALL be
  reported as separate fields; `undetected`/failed calls SHALL NOT be merged
  into success.
- R2 admission (R205): every one of the 18 graphs SHALL pass ALL six
  predicates before decoder binding — (A1) exact variable/check degree
  histograms and socket balance `sum_v = sum_c = E`; (A2) simple graph (no
  duplicate edge, no empty check, min check degree == design §3 min);
  (A3) exactly ONE connected component over all `n+m` Tanner nodes;
  (A4) deterministic structural rank `structural_rank == m` (maximum bipartite
  matching covers all `m` checks); (A5) exact GF32 (poly 37) row rank
  `gf32_rank == m` under the frozen coefficient rule; (A6) deterministic
  replay equality (identical sorted edge list + coefficient stream on
  rebuild). Four-cycle count, girth and ACE values SHALL be reported
  diagnostics only and SHALL NOT gate admission. Any predicate failure SHALL
  retain the cell record, exclude the graph before decoder dispatch, and make
  the width engineering-blocked; failure SHALL NOT alter graph/coefficient
  seeds.
- R203: structural rank SHALL be computed by a deterministic maximum bipartite
  matching with fixed visitation order under the frozen graph seed; R204:
  GF32 rank SHALL be computed by a deterministic exact GF32 (poly 37) row-rank
  algorithm; both SHALL equal `m` for admission.
- The matrix SHALL be exactly 2 arms × 3 widths × 3 graphs × 8 paired blocks
  (full ceiling 144 scientific L1 calls; 48 per width) with deterministic call
  order (width, control then candidate, graph seed ascending, block seed
  ascending), no width skipped and no mid-width partial dispatch.
- Conditional progression SHALL start at n64 and dispatch n128 (then n256)
  only if the preceding width is POSITIVE; POSITIVE requires
  `S_g(MIX) >= 3` for every graph, `E_g(MIX) >= 2` for at least two graphs,
  `S_pool(MIX) >= 12`, `E_pool(MIX) >= 6`, `S_pool(DV3) <= 3` and
  `E_pool(DV3) <= 1`; NEGATIVE requires `E_pool(MIX) <= 2` and
  `S_pool(MIX) <= 4`; AMBIGUOUS is everything else that is not
  engineering-blocked. Thresholds SHALL be frozen before execution and SHALL
  NOT be changed after observing results; a single rescued block or a
  pooled-only count SHALL NOT be sufficient evidence.
- Terminals SHALL be exactly `D10_L1_CANDIDATE_REPRODUCIBLE`,
  `D10_L1_FINITE_SIZE_SIGNAL`, `D10_L1_NO_MATERIAL_ADVANTAGE`,
  `D10_L1_AMBIGUOUS`, `D10_L1_ENGINEERING_BLOCKED`, `D10_L1_NOT_RUN`, with
  routing as design §6.4 (packet §7), plus R2 readiness terminals
  `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION` (all 18
  original cells pass A1–A6, zero replacement seeds, zero decoder calls/binds
  in R210, independent VERIFIED review with no blocker; grants NO execution)
  and `BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION` (any cell unpassable
  without changing a frozen item; exact failing cells reported; STOP).
- Budgets SHALL be: <=144 scientific L1 calls; <=44 setup units (18 graph
  constructions + 24 block samplings + 2 fixed); wall <=1800 s; per-call
  <=120 s checked between/after calls; RSS <2 GiB strict; single process;
  `retry=false`, `resume=false`, `seed_search=false`, `adaptive_stop=false`.
- The future run SHALL use the fresh root
  `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
  (verified absent at freeze), the six-file D10 evidence convention
  (`manifest.json`, `l1_records.csv`, `graph_records.csv`, `arm_summary.csv`,
  `summary.json`, `command_log.txt`), fresh-root refusal and the exact command
  frozen in `design.md` §8. The root SHALL remain absent and unauthorized
  until a separate explicit user/main-thread authorization names this batch.
- R206: the runner SHALL expose an explicit CLI execution-authorization
  argument defaulting false (repo `--execution-authorized` convention) and
  SHALL refuse `--batch` before any root creation and before any decoder
  binding while it is false; source-constant flipping SHALL NOT authorize
  execution; R201–R211 keep it false and unused.
- R207: `--verify` SHALL recompute A1–A6 for every stored graph with zero
  skip and SHALL exit FAIL on any partial or engineering-blocked root; it
  SHALL create no scientific root.
- F06–F12/R202–R212 implementation SHALL keep invalid structure from reaching
  the decoder and SHALL NOT let tests reach the production decoder without an
  explicitly injected runner (fake decoders for entry-boundary tests).

## SHALL NOT

- No production decoder call, no scientific L1 batch, no output-root creation,
  no CAL/VAL/raw/real-data contact in readiness (F01–F05, R201, R210–R211).
- No L2, APP transfer, oracle-L2, f1.0, square point, alternation or D7-H in
  this change.
- No broader degree search, seed search, replacement seeds, topology selection
  across candidates, adaptive threshold, retry/resume, post-hoc threshold
  change, decoder feedback into construction, adaptive construction, or
  coefficient repair/reseed; no re-derivation of the D9 degree tables with
  different rounding; no change to graph/block seeds, Model-F input, priors,
  GF32/poly37, coefficient rule, decoder settings, paired blocks, thresholds,
  progression, budgets or claim ceiling under R2.
- No modification of v35, V26, the D5–D9 code, the Model-F artifact or the
  frozen baseline; no generic graph library, optimizer, framework, checkpoint,
  cache, integrity manifest, retry framework or new dependency.
- No finite-length/FER/leakage/SKR/qualification/promotion/real-data claim;
  no DE-to-decoder equivalence claim; no reinterpretation of the D9 terminal;
  no self-authorization by design, tests or review; no commit or push in R201.
