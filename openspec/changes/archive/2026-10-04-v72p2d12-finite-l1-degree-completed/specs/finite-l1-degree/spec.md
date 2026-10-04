# Spec delta — D12 finite L1 degree refinement (readiness)

D12 is a successor refinement, not a predecessor correction. D12 SHALL reuse
the accepted R2 construction/admission/decoder path and the R3 plan pattern
unchanged; every frozen D12 item below is preserved exactly and any conflict
resolves in favor of the frozen item (STOP with an explicit
engineering/resource blocked terminal). A1/R3/D11 evidence SHALL remain
contextual-only and SHALL be impossible to pool into D12 gates.

## SHALL (frozen D12 successor contract)

- The refinement SHALL contain exactly three arms, `L045` (λ2=0.45 frozen
  reference), `L050` (λ2=0.50 challenger), `L055` (λ2=0.55 challenger), and all
  arms SHALL share the same connectivity-first constructor
  `build_degree_sequence_peg`, tie-breaking policy, graph seed rule, Model-F
  CAL-only L1 prior chain, row count, block seeds and paired block objects,
  decoder, schedule, iteration cap, damping, field and coefficient rule; a
  challenger SHALL differ only in its forced degree/socket profile and the
  mathematically forced check-degree allocation.
- The frozen realizations SHALL be exactly: L045 n128 n2=71 n3=57 E=313
  `2^41+3^77`; L050 n128 n2=77 n3=51 E=307 `2^47+3^71`; L055 n128 n2=83 n3=45
  E=301 `2^53+3^65`; L045 n256 n2=141 n3=115 E=627 `2^81+3^155`; L050 n256
  n2=154 n3=102 E=614 `2^94+3^142`; L055 n256 n2=166 n3=90 E=602
  `2^106+3^130`. These integers SHALL NOT be re-derived, re-rounded,
  re-selected, or repaired.
- Graph seeds SHALL be exactly n128 `2026093001..2026093006` and n256
  `2026093101..2026093106`; block seeds SHALL be exactly n128
  `2026093201..2026093212` and n256 `2026093301..2026093312`. No seed SHALL be
  added, replaced, re-rolled, repaired, or searched after any result; any
  admission failure SHALL block without seed replacement.
- Every one of the 36 future graphs SHALL pass ALL six admission predicates
  A1–A6 (exact degrees/socket balance; simple graph; exactly one connected
  component over all `n+m` Tanner nodes; deterministic structural rank `== m`;
  exact GF32/poly37 row rank `== m` under the frozen coefficient rule;
  deterministic replay equality) before decoder binding. Four-cycle/girth/ACE
  SHALL be diagnostics only.
- Coefficients SHALL follow `v10_seed(f"d10:coeff:{width}:{graph_seed}")`, one
  `integers(1,32)` per edge in sorted `(variable,check)` order; same rule all
  arms; no repair/reseed/search. The prior chain SHALL be the accepted CAL-only
  Model-F chain from `workspace/v72p2d5_model_f_input/20260907_r1`
  (`prepare_model_f_prior_candidate` → `marginalize_f_to_p1` →
  `_floor_renorm(DECODER_FLOOR=1e-15)`); no VAL/real-data contact.
- The decoder SHALL be `decode_row_layered_fftqspa` with `max_iter=90`,
  `damping_alpha=1.0`, cold start, q=32/poly37, on f1.2 rows `(n,m) =
  (128,118), (256,236)`; `exact` (`syndrome_ok` and `x_hat == u1`) is primary
  and `syndrome_valid` and `undetected` SHALL be reported separately and SHALL
  never substitute for exact.
- The plan SHALL be exactly 432 L1 call identities (3 arms × 6 graphs × 12
  paired blocks × 2 widths), both widths always measured; one matched block
  SHALL be sampled once per `(width, block_seed)` and used identically by all
  arms and all six graphs at that width. Per-graph, per-width and pooled paired
  discordances SHALL be reported.
- An arm SHALL be `STABLE(w)` iff exact ≥18/72, at least 5/6 graphs have ≥2
  exact, and no engineering/resource violation (L045 is the frozen reference).
  A challenger SHALL be `MATERIAL_BETTER` iff, at both widths: it is STABLE;
  exact is at least L045+6; pooled challenger-only discordance exceeds
  L045-only; and it has higher per-graph exact on at least 4/6 graph pairs.
  Selection SHALL be: exactly one MATERIAL_BETTER → select it; both → rank by
  total exact, then worst-width exact, then smaller λ2; neither with no
  split-width conflict → retain L045; `SPLIT_WIDTH_CONFLICT` iff a challenger
  beats L045 by ≥6 at one width but trails by >2 at the other, or widths favor
  opposing challengers. Descriptive p-values SHALL NOT override the frozen
  selection.
- Terminals SHALL be exactly `D12_SELECT_L050`, `D12_SELECT_L055`,
  `D12_RETAIN_L045_NO_MATERIAL_GAIN`, `D12_FINITE_DEGREE_SPLIT_AMBIGUOUS`,
  plus an explicit engineering/resource blocked terminal.
- The future run SHALL use the fresh root
  `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
  (verified absent; STOP if present) with manifest, graph records, decoder
  records, arm/width summaries and command log; never-overwrite; verifier
  fails closed and independently recomputes identities, metrics, gates/rank
  and terminal. Budgets SHALL be: ≤432 scientific calls; ≤62 setup units (=36
  graph builds + 24 block samples + 2); wall ≤1800 s; ≤120 s/call; RSS
  <2147483648 B; one process; no retry/resume/repair/seed search/tuning.
- A1/R3/D11 records SHALL be contextual only and SHALL never be pooled into
  D12 gates; D1206 arithmetic SHALL make predecessor pooling impossible.
- The future batch path SHALL require explicit default-false CLI authorization,
  refusing before root creation, decoder binding or Model-F load.

## SHALL NOT (claim and boundary ceiling)

- Readiness SHALL perform zero scientific decoder calls and SHALL create no
  future root.
- D12 SHALL establish at most a synthetic finite L1 degree comparison; it
  SHALL NOT claim forward/L2, FER, leakage, SKR, real-data, qualification,
  optimality, promotion, publication, or D7-H outcomes.
- D12 SHALL NOT introduce a duplicate construction/admission/coefficient/
  prior/decoder/message framework; reuse of the accepted R2/R3 paths is
  mandatory.
