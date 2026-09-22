# V72P2D5-GF32-RATE-MOTHER Implementation Packet R2 (frozen constraints, no implementation)

- document: IMPLEMENTATION_PACKET_R2
- cycle_id: V72P2D5-GF32-RATE-MOTHER
- plan_revision: R2_DV3
- packet_status: IMPLEMENTATION_PACKET_FROZEN_R2
- date_utc: 2026-09-05
- note: This file records frozen constraints only. It implements nothing, executes nothing, constructs no mother, runs no rank audit, calls no decoder, reads no CAL/VAL, creates no structure/G0/G1/G2 output, and grants no implementation or execution authorization. Future code changes occur only after this packet passes R2_IMPLEMENTATION_PACKET_REVIEW, and then only within the closed file set below.

## 1. Allowed future implementation files (exact closed set, 5)

Future R2 implementation submission may touch only:

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
2. `scripts/v72p2d5_gf32_rate_mother.py`
3. `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
4. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/IMPLEMENTATION_REVIEW_R2.md`
5. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`

Current state of the first three: `UNTRACKED_PARTIAL_CANDIDATE NOT_ACCEPTED`. They are revisable in place by the future R2 implementation turn only. The old committed version (if any content exists in the worktree) SHALL NEVER be committed as-is; the future turn revises it to this R2 contract first. `IMPLEMENTATION_REVIEW_R2.md` does not exist yet and is created only by the future review. `cycle_state.yaml` changes only for the frozen state transition already recorded (PLAN_ACCEPTED_R2, all authorizations false).

## 2. Forbidden future modification (exact closed set)

Future R2 implementation SHALL NOT modify:

- D5 R2 OpenSpec five: `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/proposal.md`, `design.md`, `tasks.md`, `specs/spec.md`, `PLAN_FREEZE.md`.
- R2 corrigendum: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_CORRIGENDUM_R2.md`.
- This packet's companions: `PLAN_REVIEW_VERDICT_R2.md` (this review cycle), `IMPLEMENTATION_PACKET_R2.md` (this file).
- History: `PLAN_REVIEW_VERDICT.md` (R1), `IMPLEMENTATION_PACKET.md` (R1), `IMPLEMENTATION_REVIEW.md` (R1) — retained by reference as superseded for the mother path; byte-identical, never edited.
- Historical code: V31 / V35 / V54 implementations; D3 / D4 code and results.
- Frozen baseline: `src/`, `experiments/`, `tools/`, `results/`.
- Memory: `AGENT_PROJECT_MEMORY.md`, `docs/decision-log.md`.
- Any real / VAL output directories; any `run_01`; unrelated dirty worktree files.
- No hash / checksum / tag field SHALL be added anywhere.

If code and plan disagree, state is `PLAN_REVISE_REQUIRED`. The plan SHALL NOT be edited to suit code. Stop and return to planner / OpenSpec on a new SHA.

## 3. Core delta (retain / delete / add)

Retain unchanged from the R1 packet path (same semantics, adapted to dv3 where noted):

- prior math: canonical `counts[Alice,Bob]`, `P_F.shape=(Alice,Bob)`, `axis0=Alice axis1=Bob`, `assert_allclose(P_F.sum(axis=0),1.0)`; single-coefficient `lambda*=137.3823795883264` smoothing on counts column direction then normalize along `axis=0`.
- F to P1/P2: `P_reshaped=P_F.reshape(32,32,1024)=(U1,U2,Bob)`; `P1=P_reshaped.sum(axis=1)` with `P1.sum(axis=0)==1`; `P2[u1,b,u2]` fixed `(u1,b)` normalized over `u2`; chain check `|CE_joint-CE_L1-CE_L2_oracle|<1e-10`.
- production `q@P`: `prior_l2=q@P` with `q=softmax(L1 final_beliefs)`; oracle L2 (`v35.get_conditional_posterior_l2` semantics) diagnostic-only, never a hard gate.
- matched generator: `B~P_CAL(B)` CAL-only marginal injected by caller + `A~P_F(.|B)` sampling with frozen `lambda*` truth table; `A=32*U1+U2`; no AWGN/BSC/QSC; no VAL; no per-symbol array persistence; generator never self-reads CAL/VAL files.
- structure metrics + phase isolation + `decode_fn=None` + single authorization + CLI phases (see sections 6, 10, 11).

MUST DELETE (no live path, no symbol, no call):

- `order_rows_for_prefix_coverage` and every post-construction row-ordering function, natural-prefix repair path, decoder-driven reorder path, and any `extra_rows`-as-repair production use.
- V31-degree2-as-production-mother path (V31 degree-2 support construction as D5 nested mother; status `EXIT_PREFIX_CONNECTIVITY_IMPOSSIBLE`).
- seed-retry / seed++ / seed-list-scan / family-fallback paths.

ADD ONLY (exact signatures, no extra builders, no framework):

- `build_dv3_nested_support(n,m_max,k_min,seed)->support`
- `assign_gf32_coefficients(support,seed,field)->H`
- thin `build_dv3_nested_mother(n,m_max,k_min,seed,field)->H` (calls the two above in order, no other logic)

## 4. Support contract (frozen)

- Per-variable exactly 3 distinct checks. Base: 2 edges in `[0,k_min)`, on different checks, earliest-prefix variable-degree exactly 2 by construction, no shared unordered base pair across any two variables, every base row degree >= 2.
- Expansion: 1 edge distinct from the variable's base pair; cover all `[k_min,m_max)` suffix rows first (zero suffix rows forbidden, every suffix row degree >= 2); remaining placements use minimum-degree with deterministic tie-break; spill to base rows allowed for balance only and only without breaking per-variable degree 3 or triple uniqueness.
- Full logical shape `m_max x n`; total edges `3n`; zero rows 0; zero columns 0; duplicate `(check,var)` edges 0; duplicate unordered support triples 0.
- Single attempt only. Any construction failure => `DV3_SUPPORT_CONSTRUCTION_BLOCKED` (stop, return to planner; no retry, no reseed, no rank-chasing).

## 5. Determinism and seeds (frozen)

- L1 graph seed `2026090501`; L2 graph seed `2026090502`. G0 `2026090510..2026090517`; G1 `2026090600..2026090699`; G2 `2026091000..2026091199`. Frozen row-count tables, thresholds, gates, budgets, and call counts unchanged from the R2 plan.
- Documented seed effects (no declared-but-unused seed): the layer seed drives (a) variable visit-order permutation seed (fixed order `0..1023` under the frozen greedy; the seed is recorded as the construction-stream seed and any future order permutation must derive from it explicitly), (b) row-priority permutation / tie-break stream for minimum-degree selection, (c) coefficient-generation stream for `assign_gf32_coefficients`. Every declared seed SHALL be consumed by exactly the stream named here.
- Same input + same seed => bit-identical support and coefficients. L1 and L2 seeds differ so their mothers differ, but there is SHALL-NOT seed-loop-for-PASS: ban retry, seed++, list-scan, decoder-guided resample, and rank-guided resample.

## 6. GF32 coefficient contract (frozen)

- Coefficients `1..31` on support entries, else `0`. `q=32`, poly `37` (`0b100101`). Single deterministic PRNG seeded by the frozen layer seed; each nonzero generated exactly once.
- No redraw on rank shortfall, cycle count, or decoder outcome. Same-seed identical output. No V31 / V35 / V54 file change.
- Small-n tests may use the repo GF32 field / rank helper; full `1000x1024` prefix-rank verification is deferred to the Structure Gate (this implementation stage performs no full-mother rank).

## 7. Audit delta (retain + extend)

- Retain and extend `audit_prefix` / `audit_frozen_prefixes`. Every frozen `k` (L1 `{782,821,860,938}`, L2 `{686,720,755,823}`) SHALL ensure and report: `total_edges`, `column_degree_full`, `prefix_variable_degree_min`, `degree1/degree2/degree3 counts`, `support_triple_duplicates`, `base_pair_duplicates`, `four_cycle_variable_incidence_max`, plus the retained 13 items (rank, zero_rows, zero_columns, column active-degree min/median/max, connected-component count, largest-component fraction, isolated, check row-degree histogram, 4-cycle count, duplicate/projective-equivalent column count, GF32 coefficient nonzero).
- Minimum PASS (all must hold): `rank==k AND zero_rows==0 AND zero_columns==0 AND isolated==0 AND components==1 AND largest==1.0 AND dup_proj==0 AND coeff_nonzero AND variable_degree_min>=2`.
- `four_cycles>0` with otherwise PASS => `STRUCTURE_PASS_WITH_CYCLE_RISK` (recorded risk; G1/G2 decoder trends judge; never retune the graph from decoder results).

## 8. Small-n contract (frozen fixture, explicitly computed)

- T0/T1 SHALL NEVER build `1000x1024`. Frozen small fixture: `n=12, m_max=10, k_min=7, column_degree=3`.
- Mechanical verification (explicit, not guessed):
  - base-pair capacity: `C(k_min,2)=C(7,2)=21 >= n=12` PASS (margin 9; 21 distinct unordered base pairs available, no-duplicate-base-pair feasible).
  - suffix two-degree: suffix rows `m_max-k_min=3`; need `2*3=6` stubs; available expansion stubs `n=12`; `12>=6` PASS (margin 6).
  - base-row two-degree: need `2*7=14` base stubs; available `2n=24`; `24>=14` PASS.
  - earliest-prefix connectivity necessary: `E_prefix_earliest=2n=24`; `V_prefix=n+k_min=19`; need `18`; `24>=18` PASS.
  - full connectivity necessary: `E=3n=36`; `V=n+m_max=22`; need `21`; `36>=21` PASS.
  - full per-row two-degree: need `2*10=20`; available `36`; `36>=20` PASS.
- These values are frozen in this packet. If any check had failed, the packet would have frozen the minimal satisfying values instead; it did not need to because all pass.

## 9. T0 delta (no decoder call, small-n only)

- Keep old math tests: probability axis / transpose counterexample, normalization, P1/P2 derivation, `q@P` hand calc, one-hot mapping, floor behavior, row-count recomputation, seed/prefix constants, generator determinism, VAL ban.
- Delete: row-permutation-content tests, ordering-determinism-as-PASS tests, natural-prefix-PASS tests.
- Add (each small-n, never full-mother conclusions): degree2-impossibility-arithmetic, dv3-edge-count, base-pair-capacity, suffix-capacity, small-dv3-support build, per-variable-degree-3, base-degree-2-earliest, suffix-min-2, no-dup-base-pair, no-dup-triple, deterministic-same-seed, L1/L2-differ, coeff-deterministic, coeff-nonzero, no-resample-spy (rank-fail does not redraw), broken-support-audit-failure, cycle-risk-not-fail, forbidden-row-ordering-symbol-absent (grep/AST: no `order_rows_for_prefix_coverage`, no post-construction reorder).
- T0 SHALL NOT test full-mother conclusions.

## 10. T1 delta (fake decoder only)

- Keep: unauthorized-prework refusal, `decode_fn=None` refusal, fake-only execution, no-chain, no all-real-VAL, no-output, no production import.
- Add: structure-uses-dv3-not-V31-degree2 (structure path builds only via `build_dv3_nested_support` / thin mother; V31 degree-2 production path absent); builder-fail-blocks-audit/output (support `BLOCKED` never reaches audit pass or output); audit-fail-blocks-G0 (any frozen-prefix FAIL blocks G0 entry); all-exec-false (every phase authorization false); CLI-cannot-override-seed/k_min/m_max/degree (frozen values from core constants, no CLI flags for them); CLI-no-family/retry params (no `--family`, no retry, no seed-list flags).
- T1 runs only with an injected fake decoder; production decoder import/call is banned.

## 11. Structure Gate boundary

- This implementation stage provides functions only. It SHALL NOT perform: `n=1024` builds, `m_max=1000` builds, L1/L2 full builds, full `gf_rank` over `1000x1024`, or all-frozen-prefixes audit over full size.
- The future Structure Packet (separate authorization) allows at most: L1x1 + L2x1 small builds, no retry, decoder 0 calls, VAL 0 rows, CAL 0 reads beyond injected tables, scalar-only stage outputs. Any Structure Gate failure returns to planner; no tuning, no reseed, no reorder repair.

## 12. CLI (frozen)

- Keep phases: `structure | g0 | p0-cost | g1 | g2`. Explicit `--phase` required; missing phase prints help and exits; default performs no execution.
- Forbid params: `--phase all`, autochain, `real`, `retry`, `seed`, `degree`, `family`, `k_min`, `m_max`, any VAL path, any `run_01` flag. Frozen values come from core constants; CLI is non-overridable for seed / k_min / m_max / degree / family.
- All phases refuse at this stage (every execution authorization is false).

## 13. Future R2 Implementation Review checklist I1-I18 (document only, do NOT execute)

- I1 manifest-5: submission touches only the 5 allowed files.
- I2 R2-OpenSpec-zero-diff: 5 D5 R2 plan files byte-unchanged.
- I3 V31/V35/V54-zero-diff: historical implementations byte-unchanged.
- I4 row-ordering-0: no `order_rows_for_prefix_coverage` symbol, no post-construction reorder, no decoder-driven reorder.
- I5 no-V31-degree2-path: degree-2 support as D5 nested mother absent; only field/rank/decoder reuse retained.
- I6 per-var-3: every variable exactly 3 distinct checks on the small fixture.
- I7 base/suffix contracts: 2 distinct base edges in `[0,k_min)` with earliest-prefix degree >= 2, no shared base pair, base rows >= 2; expansion covers all suffix rows, suffix rows >= 2, spill only without breaking degree-3/triple-uniqueness.
- I8 seed-real-no-search: frozen L1/L2 seeds consumed by the documented streams; no retry/seed++/list-scan/decoder-guided/rank-guided resample.
- I9 coeff-once-no-redraw: `1..31` once per nonzero via single deterministic PRNG; zero forbidden; no reseed on rank/cycle/decoder.
- I10 T0-small-only: T0 builds at most the frozen small fixture; no `1000x1024`; no full-mother conclusions.
- I11 no-full-mother: no `n=1024` / `m_max=1000` / L1-L2-full-build / full-`gf_rank` / all-full-prefixes execution.
- I12 no-prod-import/call: no production decoder import or call; `decode_fn=None` refuses; fake-only.
- I13 no-CAL/VAL: zero CAL/VAL reads; tables injected by caller only.
- I14 no-output: no structure/G0/G1/G2 output files, no `run_01`, no workspace production root creation.
- I15 all-unauthorized: every structure/G0/P0-cost/G1/G2/synthetic/real/formal authorization false; scientific promotion false.
- I16 py_compile+tests PASS: `py_compile` on touched `.py` plus frozen T0/T1 green.
- I17 frozen-rows/thresholds intact: row-count tables, `lambda*`, floors, disclosure sets, seeds, gates, budgets, call counts unchanged.
- I18 no plan-to-fit-code: code follows plan; plan never edited to suit code; ambiguity returns to planner/OpenSpec on a new SHA.

## 14. Output roots and prohibitions (future execution artifacts, not this stage)

- Future stage roots (declared only, not created now): `workspace/v72p2d5_structure/<run_id>/`, `workspace/v72p2d5_g0/<run_id>/`, `workspace/v72p2d5_p0_cost/<run_id>/`, `workspace/v72p2d5_g1/<run_id>/`, `workspace/v72p2d5_g2/<run_id>/`. Each stage uses a fresh directory; overwriting banned. Scalar-only files; banned from storage: complete mother, raw counts, prior tables, syndromes, BP messages, any hash.
- This stage creates no output and grants no execution.
