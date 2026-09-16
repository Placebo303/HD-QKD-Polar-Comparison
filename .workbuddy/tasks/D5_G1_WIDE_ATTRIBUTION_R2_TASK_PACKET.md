# D5-G1-WIDE-ATTRIBUTION-R2 — autonomous information-contract and decoder recovery study

## 0. Mission

Continue from accepted R1 attribution and resolve the remaining route question
far enough to make a long-term decision. Do not merely run the proposed
four-call square probe and return. Use it as the first discriminator, then
adaptively investigate the information model, disclosure frontier, and decoder
boundary. If a concrete defect or scientifically justified replacement contract
is found, implement a review-ready candidate with OpenSpec and tests.

The user explicitly permits long autonomous exploration and implementation
inside this packet. Routine choices, failed development hypotheses, test
repairs, and diagnostic redesigns do not require consultation. Return only
with a review-ready route candidate or one irreducible scientific decision.

## 1. Baseline

- Repo `D:/Code/HD-QKD_Polar_Comparison`
- Branch `formal-ir-v72p1-addendum-clean`
- Initial HEAD `07e5e638`
- G1 accepted negative result:
  `SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL`, `passed=false`
- R1 attribution: `FINITE_LENGTH_DISCLOSURE_INSUFFICIENT`
- R1 evidence root:
  `workspace/d5_g1_no_signal_attribution_r1_1dfa97a151f746569c95cc74d8786ae7`
- Current gate `G1_ATTRIBUTION_ROUTE_DECISION`
- Formal G1 root immutable; G2 absent; all execution authorizations false

R1 review has reported AC01–AC10 PASS. Recheck the underlying evidence rather
than relying only on that report.

## 2. Research question

Resolve this hierarchy:

1. Does a full-rank `m=n=64` square disclosure recover the frozen samples with
   uniform/accepted Model-F priors?
2. Why does the accepted Model-F consumer yield approximately
   `CE_L1≈5`, `CE_L2≈5`, while the frozen D4 sizing values are
   `3.814742` and `3.347605`?
3. Is the discrepancy an implementation/contract defect, a smoothing-model
   choice that destroys finite-sample information, a mismatched quantity or
   axis, or a genuine near-independent CAL-TRAIN channel?
4. What is the smallest scientifically justified successor:
   - repair Model-F construction/consumer;
   - replace the smoothing/estimation contract using CAL-only validation;
   - redesign disclosure/mother sizing;
   - stop this route because the accepted domain carries insufficient mutual
     information;
   - or perform one named remaining discriminator?

Do not presume R1's bucket is final. Preserve it if confirmed; supersede it
explicitly if stronger evidence identifies the upstream cause.

## 3. Authority and budgets

Allowed:

- up to 6 hours total operator wall;
- up to 1200 development decoder calls;
- each call under a 120 s outer watchdog;
- peak process RSS below 2 GiB;
- read accepted Model-F artifact and summary;
- read the exact canonical CAL-TRAIN source identified by accepted provenance,
  if needed; CAL-only folds/aggregates are allowed;
- build nonformal candidate counts/priors/mothers and compact diagnostics;
- implement comparison-layer candidate code after OpenSpec;
- run compile, focused tests, exact three-file D5 suite, and additional new
  focused tests;
- make multiple logical local commits; no push.

All new development outputs go under one unique
`workspace/d5_g1_wide_attribution_r2_<uuid>/`. Record a manifest, scripts,
compact scalar JSON/CSV, command log, call count, wall, and RSS. Do not dump
raw symbol rows or per-block beliefs.

## 4. Hard boundaries

- No formal G1 rerun/resume and no CLI `--phase` invocation.
- No G2, n=256 formal grading, n=1024 formal/real execution, or real IR.
- No VAL read or use for selection/confirmation. CAL-TRAIN only.
- No write/hash/delete/move/rename/overwrite under any formal evidence root.
- Do not open retained VOID-G1 contents.
- Do not change accepted formal result, frozen historical packet, authorization
  fields, thresholds, seeds, promotion, or G2 state.
- Exploratory success cannot become formal evidence or overwrite accepted
  Model-F/G1 artifacts.
- No seed search. Reuse frozen seeds or a predeclared deterministic prefix;
  paired controls share identical samples.
- No modification to frozen `src/`, `experiments/`, `tools/`, Release checkout,
  or unrelated comparison code.
- No new dependency, framework, retry system, generalized abstraction, or
  integrity machinery without a concrete need.
- No push/reset/stash/checkout/clean/rebase/revert/amend/renormalize/broad stage.

## 5. Workstream W1 — independently validate R1

Recompute from source/artifacts:

- accepted Model-F normalization, entropy, conditional entropy, mutual
  information, smoothing contribution, nonzero support, and truth prior mass;
- D4 frozen CE provenance and exact mathematical quantity/axes;
- G1 frozen row formula and rows;
- R1 D1–D3/F1–F4 scalar evidence and 29-call accounting.

Produce a discrepancy table: value, formula, source object, axis, smoothing,
sample population, units, and where consumed. Any comparison between unlike
quantities must be labeled, not subtracted as though equivalent.

## 6. Workstream W2 — square-disclosure and frontier probe

First run the approved development-only square test:

- new deterministic full-rank 64-row mother, `m=n=64`;
- uniform/accepted Model-F prior;
- four paired frozen seeds;
- oracle-L2 path;
- approximately four decoder calls.

Then, only as useful, map a compact paired disclosure frontier. Use an adaptive
bracket/bisection or sparse predeclared ladder rather than scanning every row.
Compare full-rank mothers/prefixes at enough rows to distinguish:

- algebraic sufficiency at square disclosure;
- rank/mother pathology;
- information-theoretic disclosure shortage;
- decoder failure despite full determination.

Record rank, exact, syndrome, iterations, wall, RSS, and changed axis. Square
success proves only zero-rate algebraic/decoder sufficiency. It does not prove
a useful reconciliation operating point.

## 7. Workstream W3 — Model-F and smoothing contract audit

Trace `counts_ab`, `p_b`, `lambda*`, normalization, and `P(A|B)`/layer-prior
construction end to end. Answer explicitly:

- Is `lambda*` a per-cell pseudocount, total concentration, likelihood scale,
  or another object?
- Was it estimated for the same alphabet, layer, axes, sample population, and
  probability object where it is applied?
- Does applying it to 1,048,576 cells overwhelm 262,144 observations by
  construction?
- Can the accepted D4 CE values be reproduced from the accepted Model-F input
  through the exact G1 consumer?
- Are L1 and oracle-L2 priors computed from the intended marginals/conditionals?

If provenance is insufficient, read only the referenced CAL-TRAIN source and
recompute counts/aggregates. Do not touch VAL. Verify row population and axis
semantics before drawing a conclusion.

## 8. Workstream W4 — CAL-only estimator controls

If W3 indicates smoothing/estimation—not genuine independence—is responsible,
compare a minimal set of principled candidates, for example:

- accepted construction;
- raw empirical conditional with explicit zero-support handling;
- scalar total-concentration Dirichlet shrinkage;
- one simple backoff/hierarchical shrinkage already supported by project math.

Do not invent a large model zoo. Select any smoothing strength using nested or
held-out CAL-only likelihood/CE, with deterministic folds fixed before reading
scores. VAL is forbidden. Report calibration objective and effective prior
mass, not merely decoder success.

For each justified candidate, run a small paired `n=64` decoder matrix across
the same seeds and a compact disclosure frontier. Separate:

- estimator quality (held-out CAL likelihood/CE);
- synthetic decoder exact/syndrome;
- disclosure cost;
- runtime/RSS.

No post-hoc parameter is accepted merely because it makes four blocks pass.

## 9. Workstream W5 — route classification

Choose the strongest supported terminal class:

- `MODEL_F_CONSUMER_OR_AXIS_DEFECT`
- `LAMBDA_APPLICATION_CONTRACT_DEFECT`
- `SMOOTHING_MODEL_INADEQUATE_FOR_SPARSE_1024X1024`
- `GENUINE_CAL_TRAIN_NEAR_INDEPENDENCE`
- `DISCLOSURE_MOTHER_REGIME_INADEQUATE`
- `DECODER_OR_MATRIX_FAILURE_AT_FULL_DETERMINATION`
- `MIXED_CAUSE_WITH_NAMED_REMAINING_DISCRIMINATOR`

State causal evidence, counterevidence, and what is not identified. Apply
Occam's razor: prefer the earliest upstream cause that explains D4/G1
discrepancy, APP+oracle zeros, and control results.

## 10. Workstream W6 — implementation and validation

When evidence supports a concrete correction:

1. create/update OpenSpec
   `openspec/changes/v72p2d5-g1-information-recovery-r2/` before code;
2. preserve old accepted artifacts and create only a nonformal candidate path;
3. implement the smallest correction in the allowed files;
4. add tests for the exact defect, numerical limits, axis/normalization,
   deterministic CAL-only selection if present, and formal-root isolation;
5. run compile, focused tests, exact three-file D5 suite, and candidate
   development diagnostics;
6. commit proposal/evidence and implementation in logical commits.

If the correct conclusion is genuine near-independence or an unavoidable
zero-rate frontier, do not force a code diff. Produce a route-stop candidate.

## 11. File boundary

Always allowed:

- new `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_WIDE_ATTRIBUTION_R2.md`;
- append-only `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md`;
- `cycle_state.yaml` only for final next gate and R2 candidate metadata;
- new R2 OpenSpec directory;
- unique R2 workspace evidence root.

Conditionally allowed after OpenSpec:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py`
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_model_f_input.py`
- `comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`
- `scripts/v72p2d5_gf32_rate_mother.py`
- `scripts/v72p2d5_prepare_model_f_input.py`

Read-only reference is allowed for the D4 audit and contrast/model provenance.
No other modification without returning a concrete boundary blocker.

## 12. Acceptance IDs

- `R2-01`: R1 facts and accounting independently reproduced.
- `R2-02`: square disclosure and minimal frontier completed.
- `R2-03`: D4-vs-consumer discrepancy table complete and like-for-like.
- `R2-04`: lambda semantics/provenance and smoothing dominance resolved.
- `R2-05`: CAL-only estimator controls used iff warranted, without VAL leakage.
- `R2-06`: paired decoder evidence separates estimator, disclosure, and decoder.
- `R2-07`: calls <=1200, wall <=6h, call <=120s, RSS <2GiB.
- `R2-08`: one terminal class or one irreducible named discriminator.
- `R2-09`: any code change has prior OpenSpec and focused/full green tests.
- `R2-10`: formal roots unchanged, G2 absent, all authorizations false.
- `R2-11`: no overclaim; accepted G1 negative result remains unchanged.
- `R2-12`: scoped logical commits, no unrelated cleanup, no push.

## 13. Deliverable and return

`G1_WIDE_ATTRIBUTION_R2.md` must include methods, formulas, provenance table,
all controls, calls/resources, CAL/VAL boundary, disclosure frontier, estimator
comparison, terminal class, implementation/tests if any, rejected hypotheses,
residual uncertainty, and one recommended long-term route.

Final next gate:

- review-ready correction → `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`;
- evidence-backed route stop → `D5_ROUTE_STOP_REVIEW`;
- one irreducible experiment → `G1_R2_ROUTE_DECISION`.

Return deltas only: R2-01–R2-12, terminal class, strongest evidence, calls/wall/
RSS, changed files/commits, tests, formal-root equality, and exact next gate.

End:

`R2 有界探索完成；正式 G1 负结果未改写、未重跑，G2 未授权；长期路线等待独立评审或主线程裁决。`

