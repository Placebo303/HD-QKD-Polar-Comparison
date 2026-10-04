# Design — D13 L055 failure decoder ladder (readiness, D1301–D1303)

Authority: `.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md`
(§1–§4 frozen). Track: **implementation/readiness** — zero scientific calls, no
D13 execution, no decoder calls, no root creation, no L2/D7-H, no real data, no
commit/push. Branch `formal-ir-v72p1-addendum-clean` (not switched).
Predecessor `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER` is immutable
read-only context (root
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`, terminal
`D12_SELECT_L055`, VERIFIED PASS_WITH_FINDINGS); never modified, successes
never enter the ladder. Execution: false. Decoder calls: 0.

## 1. Diagnostic shape (packet §2, no behavior edit)

The future batch (separately authorized `EXPLORE`) replays each of the 56
frozen L055 failures through `ROW_LAYERED_90_ALPHA_1` (strict match gate on
stored baseline fields; first mismatch blocks all ladder calls), then runs
exactly three arms (`ROW_LAYERED_360_ALPHA_1`, `ROW_LAYERED_360_ALPHA_0_7`,
`FLOODING_360_ALPHA_1`) on every selected failure. Thin additive
selector/replay/ladder/gate/verifier only (D1304–D1306); default-false CLI
execution flag refusing before root creation, decoder binding or Model-F load
(D1305); fresh never-overwrite minimal future root with independent verifier
checks (D1306); focused fake tests (D1307); `py_compile` + focused D13 and
directly affected D12/X3 tests in a fresh workspace basetemp (D1308);
PLAN_ONLY reconstruction metadata with zero decoder calls (D1309); independent
reviewer-go readiness review (D1310). Rescue counting per arm by width+total;
MATERIAL (≥12 total, ≥4/width) / MODEST (3–11 + ≥1/width) / NO (≤2) /
AMBIGUOUS; ranking by total, then worst-width, then mean-iter-among-rescues,
then fixed arm order; seven terminals + eng-blocked; MATERIAL required for any
selection. Budgets ≤224/≤8/1800 s/120 s/RSS<2 GiB/1-proc/no-retry-resume-
repair-search-tune. Claim ceiling: frozen synthetic L1 decoder diagnostic only.

## 2. D1302 — read-only audit of the D12 root (PASS, no mismatch)

Selector predicate (exact, frozen):
`arm == "L055" AND exact == false` over
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450/decoder_records.csv`
(header line 1: `call_idx,width,arm,graph_seed,block_seed,batch_id,exact,
syndrome_ok,iterations,status,residual_syndrome_weight,belief_provenance,
prior_mass_on_truth,wall_s,crash,error`).

Independent count confirmation (three corroborating sources, all agreeing):

- `arm_summary.csv` L055 pooled rows: n128 `POOLED,72,42,42` (lines 16–22:
  per-graph exact 7,7,5,8,7,8 → 42/72 exact → 30 failures); n256
  `POOLED,72,46,46` (lines 37–43: per-graph exact 7,9,7,8,8,7 → 46/72 exact →
  26 failures). 30 + 26 = 56.
- `summary.json` `width_results` pools: n128 `L055: 42`, n256 `L055: 46`
  (with `exact_count: 221` total); `paired_pooled.L055.trials: 37`.
- Direct row audit: all 56 rows below carry `exact=False, syndrome_ok=False,
  iterations=90, status=converged_no_syndrome, belief_provenance=CHECK_UPDATED,
  batch_id=d12-finite-l1-degree-v1, crash=False` (n128 file lines 151–217
  passim; n256 file lines 364–431 passim). A targeted grep for
  `L055.*False,True` (exact-false yet syndrome-valid, i.e. undetected) returns
  **no matches**: no undetected record hides in the selection; exact,
  syndrome-valid and undetected remain separate per the packet.

Iteration confirmation: every one of the 56 selected records shows
`iterations=90` (= D12 `DECODER_MAX_ITER`; `manifest.json` decoder block:
adapter `v35.decode_row_layered_fftqspa`, `damping_alpha: 1.0`, `max_iter: 90`,
schedule `cold row-layered`). No count or iteration mismatch found → no
BLOCKED condition met; D1301 freeze proceeds on unambiguous input.

Frozen baseline fields per selected record (replay contract, D1304): `exact`,
`syndrome_ok`, `iterations`, `belief_provenance` (= `CHECK_UPDATED`), and
failure identity (`width`, `arm`, `graph_seed`, `block_seed`, stored per-width
`call_idx`). Preserved reconstruction fields (D1306/D1309): graph/block IDs,
degree tables (`manifest.json` degree_table: L055:128 var `{2:83,3:45}`
check `{2:53,3:65}` m=118; L055:256 var `{2:166,3:90}` check `{2:106,3:130}`
m=236), coefficient stream (`v10_seed` of `d10:coeff:{width}:{graph_seed}`),
Model-F prior chain, GF32/poly37 (`manifest.json` field: `q: 32`, `poly: 37`),
cold initialization (`warm_beliefs=None`).

## 3. D1302 — frozen 56-identity list (complete; `call_idx` as stored per-width)

n128 — graph `2026093001` (5): (149,3206) (150,3207) (151,3208) (152,3209)
(155,3212); graph `2026093002` (5): (161,3206) (162,3207) (163,3208) (164,3209)
(167,3212); graph `2026093003` (7): (168,3201) (171,3204) (174,3207) (175,3208)
(176,3209) (178,3211) (179,3212); graph `2026093004` (4): (183,3204) (186,3207)
(187,3208) (191,3212); graph `2026093005` (5): (197,3206) (198,3207) (199,3208)
(200,3209) (203,3212); graph `2026093006` (4): (204,3201) (209,3206) (211,3208)
(215,3212). Subtotal n128 = 5+5+7+4+5+4 = 30.

n256 — graph `2026093101` (5): (146,3303) (148,3305) (149,3306) (151,3308)
(153,3310); graph `2026093102` (3): (158,3303) (160,3305) (165,3310); graph
`2026093103` (5): (169,3302) (170,3303) (172,3305) (173,3306) (177,3310); graph
`2026093104` (4): (181,3302) (182,3303) (184,3305) (189,3310); graph
`2026093105` (4): (193,3302) (194,3303) (197,3306) (201,3310); graph
`2026093106` (5): (205,3302) (206,3303) (208,3305) (209,3306) (213,3310).
Subtotal n256 = 5+3+5+4+4+5 = 26.

Total = 30 + 26 = 56. Each tuple is (stored per-width `call_idx`, `block_seed`)
under (`width`, `arm=L055`, `graph_seed`); `call_idx` restarts per width in the
stored records (D12 `execute_width` records `call_idx=len(records)` per width),
so `width` is part of the identity. All 56 rows verified `exact=False`,
`syndrome_ok=False`, `iterations=90`, `CHECK_UPDATED` (raw rows cited in §2).

## 4. D1303 — binder semantic map (PASS, all required binders accepted)

Reconstruction path (D12 batch production path, import-only for D13):

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d12_finite_l1_degree.py:228`
  `build_graph` — frozen D12 graph builder via accepted R2 construction/
  admission (degree cell guard, `r2.build_degree_sequence_peg`,
  `r2.coefficients_for_edges`, `r2.dense_from_edges`,
  `r2.structural_record` A1–A5 plus A6 deterministic replay).
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d12_finite_l1_degree.py:150-152`
  shared binding re-export: `dispatch_l1`, `coefficient_seed`,
  `refuse_out_root` (= R2, import not copy); `:143-147` decoder/field
  contract (`DECODER_MAX_ITER`, `DAMPING_ALPHA`, `MODEL_F_INPUT_ROOT`, `Q`,
  `POLY`); `:287` `build_call_plan`, `:307` `build_full_plan`, `:577`
  `execute_width` via `r2.dispatch_l1` (`:618-619`).
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py:241`
  `build_degree_sequence_peg` (connectivity-first constructor); `:584`
  `coefficient_seed` (frozen `d10:coeff:{width}:{graph_seed}`); `:589`
  `coefficients_for_edges`; `:602` `dense_from_edges`; `:855` `dispatch_l1`
  (cold: `:882-884` `max_iter=DECODER_MAX_ITER, damping_alpha=DAMPING_ALPHA,
  warm_beliefs=None, field=None`); `:154` `DECODER_MAX_ITER = 90`; `:155`
  `DAMPING_ALPHA = 1.0`; `:92-94` `Q = 32`, `POLY = 37`, `MODEL_F_INPUT_ROOT`.
- `scripts/v72p2d10_mixed_degree_l1_development.py:120` `load_prior_chain`
  (accepted CAL-only Model-F chain); `:132` `prepare_blocks` (frozen L1 prior
  line from `p1[:, bob]`), wired by `scripts/v72p2d12_development.py:146,157,
  162-163`; production decoder bind `:616-617`
  (`decode_fn=v35.decode_row_layered_fftqspa`,
  `syndrome_fn=v35.syndrome_of_gf32`).

Accepted decoder binders (frozen R1, import unchanged):

- RL90 binder (row-layered max_iter90/damping1.0/cold):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py:666`
  `bind_row_layered_decoders` (SOURCE/TARGET wrappers `:676-684` with
  `max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, warm_beliefs=None,
  field=None`; `.target` exposed `:686-687`); constants `:92-93` via accepted
  D7-C (`MAX_ITER = 90`, `DAMPING_ALPHA = 1.0` per
  `v72p2d7_gf32_bidirectional_oracle.py:80-81`); decoder IDs `:207-214`.
- RL90 + flooding-90 pair binder (frozen R1):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_schedule_discriminator.py:431`
  `bind_schedule_decoders` (ROW_LAYERED `:442-445` max_iter90/damping1.0/cold;
  FLOODING `:447-449` max_iter90/fieldNone; `.target` `:451-452`).
- RL360 binder: parametrizable `max_iter` of the same accepted target —
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:781-786`
  `decode_row_layered_fftqspa(..., max_iter, damping_alpha, warm_beliefs,
  field)` called with `max_iter=360`; no new decoder.
- Damping-0.7 support: EXISTING tunable parameter only (NOT tuned, per packet) —
  `v35_algorithm_development.py:786` `damping_alpha` signature, `:831`
  `alpha = float(damping_alpha)`, `:870-876` probability-domain damping branch,
  `:939-954` `decode_damped_row_layered_fftqspa` wrapper; called with
  `damping_alpha=0.7`, `max_iter=360`, cold.
- Flooding-360 binder: same accepted target with `max_iter=360` —
  `v35_algorithm_development.py:672-678` `decode_flooding_fftqspa(...,
  max_iter, field)` (synchronous flooding, no damping parameter by design).
- CHECK_UPDATED provenance: `v35_algorithm_development.py:524`
  `BELIEF_PROVENANCE_CHECK_UPDATED = "CHECK_UPDATED"`, emitted `:759,:777`
  (flooding) and `:906,:932` (row-layered); accepted gate token
  `v72p2d7_gf32_cross_layer_discriminator.py:158`, schedule labels
  `v72p2d7_gf32_schedule_discriminator.py:115-117`; field `FIELD_Q = 32`
  (`v35_algorithm_development.py:32`), syndrome `:139` `syndrome_of_gf32`.

Duplication rejection: D13 MUST import the D12 reconstruction entry and the
D7-X3 binders above unchanged (same `.target` functions, cold init, field =
None → GF32/poly37 default). No new decoder, message-passing, or
provenance-token implementation is authorized; any missing/unaccepted binder
would have STOPped this change (packet STOP: missing accepted decoder binder)
— none is missing.

## 5. Future-root absence (raw evidence, D1301)

Probe of `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
returns `File not found:
.../workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
— future root absent as required; STOP-on-present condition not triggered. No
root created by this change (read-only audit only).

## 6. Preserved-items checklist (frozen for D1304–D1310)

Input root read-only + never modified; 56 identities (§3) with no-success rule
(successes never enter the ladder); preserved fields per record (graph/block
IDs, degree tables, coefficient stream, Model-F prior, GF32/poly37, cold
init); strict RL90 replay contract (match stored baseline fields; first
mismatch blocks all ladder calls); exactly three ladder arms in fixed order;
224 ceiling (56 + 56×3); rescue counting per arm by width+total with
MATERIAL/MODEST/NO/AMBIGUOUS gates verbatim; ranking (total, worst-width,
mean-iter-among-rescues, fixed arm order); seven terminals + eng-blocked with
MATERIAL required for selection; future root (§5); budgets
(≤224/≤8/1800 s/120 s/RSS<2 GiB/1-proc/no-retry-resume-repair-search-tune);
claim ceiling (frozen synthetic L1 decoder diagnostic only). Allowed files:
`openspec/changes/v72p2d13-l055-decoder-ladder/**` only.
