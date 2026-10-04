# Spec delta — V72P2D10 R3 fresh-graph scaling replication (readiness)

R3 is a successor replication, not an R2 correction. R3 SHALL reuse the
accepted R2/A1 construction, admission, coefficient, prior and decoder
contract unchanged; every frozen R3 item below is preserved exactly and any
conflict resolves in favor of the frozen item (STOP with an explicit
engineering/resource blocked terminal). A1 evidence SHALL remain
contextual-only and SHALL be impossible to pool into R3 gates.

## SHALL (frozen R3 successor contract)

- The replication SHALL contain exactly two arms, `PEG_DV3_MATCHED` (regular
  variable degree 3 control) and `PEG_DV23_LAM2_045` (D9-selected `lambda2 =
  0.45` mixed `{2,3}` candidate), and both arms SHALL share the same
  connectivity-first constructor `build_degree_sequence_peg`, tie-breaking
  policy, graph seed set, Model-F L1 prior chain, row count, block seeds and
  paired block objects, decoder, schedule, iteration cap, damping, field and
  coefficient rule; the candidate SHALL differ only in its degree/socket
  profile and the mathematically forced check-degree allocation.
- The frozen n128/n256 realizations SHALL be exactly: DV3 n128 m=118 E=384
  `3^88+4^30`; DV3 n256 m=236 E=768 `3^176+4^60`; MIX n128 n2=71 n3=57 E=313
  `2^41+3^77`; MIX n256 n2=141 n3=115 E=627 `2^81+3^155`. These integers SHALL
  NOT be re-derived, re-rounded, re-selected, or repaired.
- Graph seeds SHALL be exactly n128 `2026092401..2026092406` and n256
  `2026092501..2026092506`; block seeds SHALL be exactly n128
  `2026092601..2026092612` and n256 `2026092701..2026092712`. No seed SHALL be
  added, replaced, re-rolled, repaired, or searched after any result; any
  admission failure SHALL block without seed replacement.
- Every one of the 24 future graphs SHALL pass ALL six R2 admission predicates
  A1–A6 (exact degrees/socket balance; simple graph; exactly one connected
  component over all `n+m` Tanner nodes; deterministic structural rank `== m`;
  exact GF32/poly37 row rank `== m` under the frozen coefficient rule;
  deterministic replay equality) before decoder binding. Four-cycle/girth/ACE
  SHALL be diagnostics only.
- Coefficients SHALL follow `v10_seed(f"d10:coeff:{width}:{graph_seed}")`, one
  `integers(1,32)` per edge in sorted `(variable,check)` order; same rule both
  arms; no repair/reseed/search. The prior chain SHALL be the accepted CAL-only
  Model-F chain from `workspace/v72p2d5_model_f_input/20260907_r1`
  (`prepare_model_f_prior_candidate` → `marginalize_f_to_p1` →
  `_floor_renorm(DECODER_FLOOR=1e-15)`); no VAL/real-data contact.
- The decoder SHALL be `decode_row_layered_fftqspa` with `max_iter=90`,
  `damping_alpha=1.0`, cold start, q=32/poly37, on f1.2 rows; `exact`
  (`syndrome_ok` and `x_hat == u1`) is primary and `syndrome_valid` SHALL be
  reported separately and SHALL never substitute for exact.
- The plan SHALL be exactly 144 calls per width (2 arms × 6 graphs × 12 paired
  blocks), n128 first, n256 dispatched if and only if n128 is
  `R3_REPRODUCED`; maximum 288 scientific calls. One matched block SHALL be
  sampled once per `(width, block_seed)` and used identically by both arms and
  all six graphs at that width.
- For each graph let `M_g`/`C_g` be MIX/DV3 exact counts from the same 12
  blocks; let `M`/`C` be fresh-width pools (72 each). `R3_REPRODUCED(w)` SHALL
  hold iff ALL of: (1) `M >= 18`; (2) `M - C >= 12`; (3) MIX wins (`M_g > C_g`)
  on at least 5 of 6 graph pairs; (4) at least 4 of 6 MIX graphs have `M_g >=
  2`; (5) `C <= 6`; (6) no engineering/resource violation. `R3_NEGATIVE(w)`
  SHALL hold iff `M <= 6` OR `M - C <= 3`, with no engineering block;
  otherwise `R3_AMBIGUOUS(w)`. Paired discordances, exact one-sided McNemar
  and intervals SHALL be descriptive only; p-values SHALL NOT override the
  frozen gate.
- Terminals SHALL be exactly `D10_R3_N128_NOT_REPRODUCED`,
  `D10_R3_N128_AMBIGUOUS`, `D10_R3_FINITE_WIDTH_DECAY`,
  `D10_R3_N256_AMBIGUOUS`, `D10_R3_WIDE_L1_SIGNAL_REPRODUCED`, plus an explicit
  engineering/resource blocked terminal; routing per packet §2 (n128 first;
  n256 only after n128 REPRODUCED).
- The future run SHALL use the fresh root
  `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
  (verified absent; STOP if present) with manifest, graph records, decoder
  records, arm/width summaries and command log; never-overwrite; verifier
  fails closed. Budgets SHALL be: ≤288 scientific calls; ≤50 setup units (=24
  graph builds + 24 width-block samples + Model-F load + plan build); wall
  ≤1800 s; ≤120 s/call; RSS <2147483648 B; one process; no retry/resume/
  repair/seed search/adaptation.
- A1 records SHALL be contextual only and SHALL never be pooled into R3 gates;
  R305 arithmetic SHALL make A1 pooling impossible.
- The future `--r3-batch` path SHALL require explicit CLI authorization,
  default false, refusing before root creation, decoder binding or Model-F
  load.

## SHALL NOT (claim and boundary ceiling)

- Readiness SHALL perform zero scientific decoder calls and SHALL create no
  future root.
- R3 SHALL establish at most an L1-only synthetic diagnostic; it SHALL NOT
  claim FER, leakage, SKR, qualification, promotion, publication, real-data,
  L2/APP, oracle-L2, or D7-H outcomes.
