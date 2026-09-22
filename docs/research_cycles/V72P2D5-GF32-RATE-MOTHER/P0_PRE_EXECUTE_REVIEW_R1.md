# P0 Pre-EXECUTE review R1 — independent read-only verdict on P0_EXECUTION_PACKET.md

Reviewer: independent session. Did not write the P0 packet, the Model-F implementation,
or any prior D5 packet. No prior verdict accepted on faith; every row re-derived from source.
Task packet: `.workbuddy/tasks/D5_P0_PREEXECUTE_R1_REVIEW_PACKET.md`.
Under review: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`
(`P0_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`).
Source truth: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
(core), `scripts/v72p2d5_gf32_rate_mother.py` (CLI),
`openspec/changes/v72p2d5-p0-g1-g2-production-path/design.md` (design),
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml` (state).
HEAD at review: `b27f31da`, branch `formal-ir-v72p1-addendum-clean`, worktree clean
(`git status --porcelain --untracked-files=no` empty, operator E1).

## 1. Numbered checks

| ID | Check | Result |
| --- | --- | --- |
| C1 | P03 frozen-parameter fidelity (§2 table below; zero DISAGREE on scientific inputs) | PASS |
| C2 | Defect fix: per-`f` mother-prefix slicing before any decode; L1→L2 order; L2 always attempted; oracle diagnostic-only (§3) | PASS |
| C3 | Authorization chain: single choke, key mapping, CLI exit-3-before-work, synthetic refuse, R-R1 honesty (§4) | PASS |
| C4 | Guarded refusal empirical (§5 shape, once) | PASS |
| C5 | Compile evidence: py_compile on 4 files | PASS |
| C6 | Test evidence: 3 files, literal `195 passed`, 0 failures | PASS |
| C7 | Protected-root invariance: P0/G2 roots absent before, during, after | PASS |
| C8 | Provenance: frozen commit is ancestor; no scoped-code delta since freeze | PASS |
| C9 | Five open questions OQ-P0-1..OQ-P0-5 | all DECIDED (§7) |
| C10 | Hard prohibitions observed (reviewer + operators) | PASS |

P01 pre-state note (non-blocking): the packet records `HEAD b7540421 / ahead 4`.
`b7540421` is the direct parent of the packet-freeze commit `b27f31da`
(`docs(v72p2d5): freeze P0 cost-preflight execution packet, not authorized`;
`git merge-base --is-ancestor` true), i.e. P01 captured the drafting HEAD before the
packet's own commit landed. `git log b7540421..HEAD` on the three scoped code files is
empty — no scoped code changed — so all P03 verification at `b27f31da` transfers to the
frozen packet. Everything else in P01 re-verified exact: G1 root present with the same
4 files/sizes (267/146/2593/126), Model-F root present with the same 2 files/sizes
(752/208467), P0/G2 roots absent, `p0_cost_execution_authorized: false`,
`next_gate: P0_PACKET_REVIEW`, `model_f_input_accepted: true` (operator E2/E3).

## 2. P03 parameter verification (packet numbers never used as their own evidence)

Core = `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`.
Arithmetic re-derived: `ceil(64*3.814742*1.0/5)=ceil(48.8286976)=49`;
`ceil(64*3.814742*1.2/5)=ceil(58.5944371)=59`;
`ceil(64*3.347605*1.0/5)=ceil(42.849344)=43`;
`ceil(64*3.347605*1.2/5)=ceil(51.4192128)=52`.

| # | P03 row | Finding | Source location |
| --- | --- | --- | --- |
| 1 | Phase name `p0-cost` | AGREE | core L88 `PHASES`, L93 auth-key map; CLI L45–52 `_RUNNERS` |
| 2 | Auth key `p0_cost_execution_authorized`, currently `false` | AGREE | core L93 mapping; `cycle_state.yaml` L24 `false`; operator E3 re-read |
| 3 | Block width `n_IR` 64 | AGREE | core L69 `P0_WIDTH = 64`; `run_p0_cost_phase` L1953–1966 builds 64-wide mothers, `width = h1.shape[1]` |
| 4 | `f` set `(1.0, 1.2)` | AGREE | core L62 `P0_F = (1.0, 1.2)`; loop L1970; echo L2005 |
| 5 | `m1(f)` `{1.0: 49, 1.2: 59}` | AGREE | `_rows_required` L918–919 + `CE_L1_MEAN` L48; call sites L1971, L2023, L2246; arithmetic re-derived above |
| 6 | `m2(f)` `{1.0: 43, 1.2: 52}` | AGREE | `_rows_required` L918–919 + `CE_L2_ORACLE_MEAN` L49; call sites L1972, L2024, L2247; arithmetic re-derived above |
| 7 | Row formula `rows = ceil(n*CE*f/5)` | AGREE | core L918–919 `int(math.ceil(width*float(ce)*float(f)/5.0))` |
| 8 | `CE_L1_MEAN = 3.814742` | AGREE | core L48; design §3; use sites L1971/L2023 |
| 9 | `CE_L2_ORACLE_MEAN = 3.347605` | AGREE | core L49; design §3; use sites L1972/L2024 |
| 10 | Builder `build_dv3_nested_mother`, one max mother per layer | AGREE | wrapper L632–635; `run_p0_cost_phase` L1953–1957 builds exactly one L1 + one L2 mother |
| 11 | Builder `k_min` L1 59 / L2 52 | AGREE | core L70–71 `P0_L1_K_MIN = 59`, `P0_L2_K_MIN = 52`; passed as `(m_max, k_min)` at L1955/L1957, so each max mother is exactly its largest prefix |
| 12 | Graph seeds L1 `2026090501` / L2 `2026090502` | AGREE | core L51–52; call sites L1955/L1957 |
| 13 | Block seeds `G0_SEEDS[:2]` = `2026090510`, `2026090511` (2 blocks) | AGREE | core L55 `tuple(range(2026090510, 2026090518))`; slice L1977 |
| 14 | Decoder calls 12 = per `f` (2 APP × 2 blocks) + (1 oracle × 2 blocks), over 2 `f` | AGREE | L1975–1989: app branch `calls += 2` (L1+L2) × 2 seeds = 4, oracle branch `calls += 1` × 2 seeds = 2 → 6 per `f` × 2 = 12 |
| 15 | Decoder historical `decode_row_layered_fftqspa`, `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None`, cold start, bound once and reused | AGREE | `MAX_ITER` L86, `DAMPING_ALPHA` L87; entrypoint name assembled L993–1000; frozen kwargs at `historical_g0_decoder` L1018–1026 and `bind_historical_decoder` L2204–2214; bound once per run at `run_p0_cost_synthetic` L2422 and reused for all 12 calls |
| 16 | Prior source: accepted Model-F artifact `workspace/v72p2d5_model_f_input/20260907_r1/`, via `prepare_model_f_prior` reusing `build_f_model` with `LAMBDA_STAR = 137.3823795883264` | AGREE | `LAMBDA_STAR` L45; `MODEL_F_INPUT_FORMAL_ROOT` L82; `_load_model_f_input_or_blocked` L2170–2197; `prepare_model_f_prior` L2139–2167 (default `lam=LAMBDA_STAR`, calls `build_f_model(counts_ab, lam)` L2154); wired in order at L2420–2421 |
| 17 | Output root `workspace/v72p2d5_p0_cost/20260906_r1/`, absent-before-run, refuses overwrite | AGREE | `P0_FORMAL_ROOT` L76; `_write_stage_evidence` L2228–2229 `raise FileExistsError` before any write; operator E2/E4/E7: absent at all times |
| 18 | Output files exactly `results.json`, `table.csv`, `report.md`, `execution_summary.json` | AGREE | `STAGE_EVIDENCE_FILES` L79–80; writer L2231–2241 writes exactly these four |
| 19 | Per record `f`, `kind` (`app`/`oracle`), `wall_s`, `iterations`, `rss_bytes` | AGREE | phase records L1992–1995; writer normalizes same keys L2249–2258; header L2293 |
| 20 | Returned scalars `decoder_calls`, `projected_g1_s`, `projected_g2_s`, `projection_blocked`, `passed` | AGREE | return block L2002–2012 |
| 21 | Projection basis `per_call = total_wall/decoder_calls`; `projected_g1_s = per_call*(100*2+20*2)`; `projected_g2_s = per_call*(200*3+40*3)` | AGREE | L1996–2001: `G1_BLOCKS`(L63,100)×`len(G1_F)`(L60,2)+`G1_ORACLE_SUBSET`(L65,20)×2 = 240; `G2_BLOCKS`(L64,200)×`len(G2_F)`(L61,3)+`G2_ORACLE_SUBSET`(L66,40)×3 = 720; matches packet factors exactly |
| 22 | `projection_blocked` rule `True` when `projected_g2_s > 3600.0` | AGREE | L2010 strict `>`; `G2_TOTAL_BUDGET_S = 3600.0` L84 |
| 23 | Single-call budget 120 s | AGREE (value; note below) | `G0_WALL_BUDGET_S = 120.0` L105; design §3; CLI watchdog docstring. NOTE: P0 code measures wall but has no in-code per-call abort — the budget is operator/review-enforced, which is exactly why OQ-P0-1/OQ-P0-2 are decided in §7. Not a scientific-input disagreement. |
| 24 | Downstream budgets, context only: G1 total ≤ 900 s, G2 total ≤ 3600 s, peak RSS < 2 GiB | AGREE | `G1_TOTAL_BUDGET_S = 900.0` L83; `G2_TOTAL_BUDGET_S = 3600.0` L84; `G0_RSS_BUDGET_BYTES` L106; packet correctly labels them context-only |
| 25 | Metric naming `exact_failure_fraction`; never FER; never extrapolate to real frames | AGREE (spelling note) | Design §3 names the quantity `exact_failure_fraction`; the P0/G1/G2 code key is `app_failure_fraction = 1 - app_exact_rate` (L2045/L2306/L2364); no `FER` string in the P0 path; packet discipline matches design intent and its own P02 claim boundary |
| 26 | Frozen command `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` | AGREE | CLI `build_parser` L72–77 (`--phase` required); operator E4 executed exactly this string |
| 27 | Invocation count exactly one; no retry/rerun/tuning/seed change | AGREE (contract) | Packet-internal contract (P04/P09), consistent with design §6/§9 no-override CLI; operator-enforced, not code-enforced |

Zero `DISAGREE`. Zero `NOT_VERIFIABLE` in §2.

## 3. Defect-fix finding (the reason this change exists)

Claim under test: every `f` decodes with its own `H1_mother[:m1(f)]` / `H2_mother[:m2(f)]`,
sliced before any decode call for that `f`, in construction order, no row reordering. PASS:

- `run_p0_cost_phase` L1970–1974: inside `for f in P0_F`, computes
  `m1 = _rows_required(...)` / `m2 = _rows_required(...)`, then
  `h1_f = h1[:m1]` / `h2_f = h2[:m2]` before the kind/seed loops. Both decode
  call sites (L1981 `_run_layered_block` with `h1_f, h2_f`; L1986 `_decode_block`
  with `h2_f`) use only the sliced views. No decode precedes the slice.
- `_run_rate_scan` (G1/G2 shared path) L2022–2032: identical per-`f` slice-before-decode
  structure (`h1_f = h1[:m1]`, `h2_f = h2[:m2]` at L2025–2026, decode at L2031).
- Construction order, no reordering: slices are plain `H[:k]` views; the only
  permutations in the file (`rng.permutation` L424–427, `tuple(sorted(...))`
  L484–537) live inside mother construction bookkeeping (seeded support build),
  never as post-construction row reordering of a prefix. No
  `order_rows_for_prefix_coverage` or decoder-driven reordering exists.
- L1-then-L2 order: `_run_layered_block` L1262–1279 always decodes L1 first
  (L1265), derives the L2 prior from L1 beliefs via `app_fed_l2_prior` (L1273),
  then decodes L2 (L1274). No early return on L1 failure — L2 is attempted even
  when `e1` is false; `app_exact = e1 and e2` (L1276) records the joint outcome.
- Oracle diagnostic-only, never gates: app records never include oracle fields
  unless the `oracle` flag is set (L1280–1284); P0 `passed` is unconditional
  `True` (L2011); G1 `passed` uses app monotonicity + nonfinite only (L2085);
  G2 grade uses app top-rate + monotonicity + nonfinite only (L2089–2096,
  L2122–2135); `oracle<APP` is a diagnostic counter, not a gate (design §3).

## 4. Authorization-chain finding. PASS.

- Single choke: `is_phase_authorized` (core L115–125) is the only authorization
  predicate; unknown phases deny (L122–124). All six phase entrypoints gate on
  `_require_authorized` first (P0: L1951/L2419; same pattern G1/G2/structure/G0).
- Mapping: `"p0-cost" -> "p0_cost_execution_authorized"` (core L89–96, L93).
- CLI refuses with exit 3 before any construction/loader import/decode/write while
  the key is `false`: `main()` (CLI L80–89) reads only the state file, checks
  `is_phase_authorized`, prints the refusal and returns 3 before any runner is
  touched. The historical decoder import is function-local (`_load_g0_decoder`
  L983–1003, called only from `bind_historical_decoder` on the authorized path);
  importing the core module only defines functions.
- `run_p0_cost_synthetic(authorized=False)` refuses via `_require_authorized`
  (L2419) before prep/build/decode/write.
- R-R1, exactly as packet P06 states it: `run_p0_cost_synthetic(authorized=True)`
  with no injected arguments binds the **production** decoder
  (`decode_fn if ... else bind_historical_decoder()`, L2422) and writes to the
  **formal** root (`target = P0_FORMAL_ROOT if out_dir is None else out_dir`,
  L2425). The guard is test-side only: `test_TIS_static_authorized_synthetic_isolation`
  (test file L3289–3409) AST-enforces that every authorized-True synthetic call in
  tests passes explicit fake `decode_fn` + tmp `out_dir` + injected counts, and
  forbids CLI-auth flags and `cycle_state` mutation in tests. Packet description of
  R-R1 is HONEST (AGREE). R-R2 likewise honest: `test_M24`/`test_P12`
  snapshot only the Model-F and G1 roots, asserting no global formal-root gate.
- State: all nine `*_execution_authorized` keys are `false`
  (`structure`, `g0`, `g0_recovery`, `p0_cost`, `g1`, `g2`, `synthetic`, `real`,
  `formal`; operator E3 literal re-read) and `next_gate` is `P0_PACKET_REVIEW`.

## 5. Guarded refusal check (§5 shape). PASS — ATTEMPTED once, all four steps.

1. Pre-stat: P0 root absent (`False`), G2 root absent (`False`) — operator E2.
2. `p0_cost_execution_authorized: false` confirmed — operator E3. Proceeded.
3. `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` →
   stdout/stderr: `phase 'p0-cost' is not authorized; refusing before any work`,
   exit code `3`.
4. Immediate re-stat: P0 root still absent, G2 root still absent. No STOP.

## 6. Compile and test evidence

- py_compile PASS (exit 0) on all four: core `v72p2d5_gf32_rate_mother.py`,
  `v72p2d5_model_f_input.py`, `scripts/v72p2d5_gf32_rate_mother.py`,
  `scripts/v72p2d5_prepare_model_f_input.py` (operator E5).
- pytest (operator E6-RETRY, single run, `-p no:cacheprovider`,
  `--basetemp=workspace/v72p2d5_p0_preexec_r1_b7f0d3e5`):
  literal summary `======================= 195 passed, 1 warning in 19.93s =======================`;
  failing test IDs: NONE. Matches the reference value 195 (orientation only, met).
  (First attempt used a mistyped third filename `test_v72p2d5_...` instead of
  `test_v72p2d4_cal_gf32_model_rate_audit.py`, exit 4, 0 collected; retried once
  with the exact §6 set. Both basetemps left in place; nothing else written.)
- Post-test stat: P0/G2 roots still absent; changed = False (E7 + E6-RETRY (d)).

Pre/post stat snapshot of protected roots:

| Root | Pre (E2) | Post-refusal (E4.4) | Post-tests (E7/E6-RETRY) |
| --- | --- | --- | --- |
| `workspace/v72p2d5_p0_cost/20260906_r1` | absent | absent | absent |
| `workspace/v72p2d5_g2/20260906_r1` | absent | absent | absent |

Neither root existed at any point during this review. No STOP condition fired.

## 7. Open-question decisions (decided here, not deferred)

- OQ-P0-1 (total wall cap). DECIDED: cap the decode-attributed total
  `sum(records[].wall_s) <= 1440 s` (= 12 calls × 120 s single-call budget).
  Process `total_wall` (includes mother build + sampling) is recorded without a
  cap. Breach is a recorded `RESOURCE_OVERRUN`, not an in-run abort — aborting
  would destroy the measurement the phase exists to take — and does not un-pass
  the cost measurement; any single record `> 120 s` must be named in Pre-RESULT
  review, which must then rule on projection validity. Reason: the frozen source
  pins only the 120 s single-call budget (C-row 23 has no in-code enforcer), so
  the tightest artifact-enforceable total is 12 × 120 s on the decode-attributed
  sum. Run delta: the authorization record carries the 1440 s decode-sum cap +
  record-only rule; the operator computes the sum at read-out; no new code.
- OQ-P0-2 (watchdog). DECIDED: an outer wall guard is REQUIRED. The operator
  executes the single frozen invocation under an outer 1500 s guard (1440 s
  decode cap + 60 s harness allowance) that terminates the whole process tree on
  expiry; the authorizing operator session owns the guard and the stop action.
  Reason: the CLI docstring states a hanging historical call needs an
  outer-process watchdog and that none lives in the script (frozen CLI gains no
  machinery per design §9), so the guard must be operator-side. Run delta: the
  authorization record must name the exact outer-guard command for the
  operator's platform; expiry enters the OQ-P0-5 hang path.
- OQ-P0-3 (`projection_blocked` semantics). DECIDED: P0 PASS is independent of
  `projection_blocked` — the code returns `passed=True` unconditionally (L2011);
  P0 measures cost. `projection_blocked=True` records
  `RESOURCE_PROJECTION_BLOCKED`, which CLOSES the G2 gate (no G2 authorization
  while blocked without a fresh decision) and does NOT close G1; G1's gate is
  judged from `projected_g1_s <= 900 s` at Pre-RESULT review. Reason: matches the
  code (unconditional pass) and design §3 (`projected>3600s` is a G2 resource
  flag, tag never generated/counted). Run delta: Pre-RESULT review must state
  both projections and the resulting G1-open / G2-closed positions; the operator
  must not seek G2 authorization while blocked.
- OQ-P0-4 (pre-authorization isolation evidence, given R-R1). DECIDED: the
  following read-only evidence must be freshly produced immediately before the
  flip and attached to the authorization record — (i) TIS static guard passes on
  current HEAD (`test_TIS_static_authorized_synthetic_isolation`; live evidence:
  195 passed including TIS); (ii) P0 + G2 formal roots absent by stat;
  (iii) all nine `*_execution_authorized` false + `next_gate P0_PACKET_REVIEW`
  by direct read; (iv) CLI refusal re-verified once in §5 shape (exit 3);
  (v) lazy decoder import confirmed static (`_load_g0_decoder` function-local,
  `bind_historical_decoder` reachable only on the authorized path);
  (vi) the flip touches ONLY `p0_cost_execution_authorized` false→true, performed
  by the user, recorded with timestamp. Reason: R-R1's trigger is a bare
  authorized-True call with defaults, so the evidence must show no test/import
  path can issue one and that the formal roots are untouched. Run delta: this
  review's E-evidence EXPIRES at the flip — (ii)–(iv) must be re-produced, not
  cited from here; no `python -c` import-and-call of any synthetic entrypoint is
  permitted at any time.
- OQ-P0-5 (failure disposition). DECIDED: on crash, hang, or non-finite output,
  any partial root is RETAINED undisturbed in place and marked VOID (precedent:
  `g1_unauthorized_output_disposition: VOID_RETAINED_IN_PLACE`) — no deletion, no
  completion, no reuse of `workspace/v72p2d5_p0_cost/20260906_r1` ever; any future
  attempt needs a new packet with a new root and a new authorization. The P0
  authorization is consumed by the attempt (P04), success or not. Non-finite in
  any numeric payload is a P0 FAIL in the
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED` family with the same retention
  disposition, recorded at Pre-RESULT review. Reason: the writer refuses
  overwrite, so a partial root permanently occupies the name; silent removal
  would destroy failure evidence. Run delta: the operator must not touch a
  partial root except to stat/list it for the failure record.

## 8. What was and was not executed

Executed: source reads (core constants L40–109, auth L111–125, builder L632–635,
`_rows_required` L918–919, decode path L947–1035/L1257–1285, P0 phase L1948–2012,
scan L2015–2049, prior L2139–2197, binder L2200–2222, writers L2225–2294,
synthetics L2416–2455; CLI; design §1–§5/§8–§9; `cycle_state.yaml`;
TIS/M24/P12 test regions); operator E1 (git state), E2/E7 (stat),
E3 (state re-read), E4 (single guarded `--phase p0-cost` refusal, exit 3),
E5 (4× py_compile), E6-RETRY (single 3-file pytest, 195 passed),
G1–G4 (read-only git provenance).
NOT executed: no decoder call; no P0/G1/G2 phase (authorized or otherwise);
no `v72p2d5_prepare_model_f_input.py`; no `pandas.read_parquet`, no CAL/VAL/raw
row reads (no pyarrow use at all); no workspace writes except the two pytest
basetemps (`workspace/v72p2d5_p0_preexec_r1_d2deaf26`,
`workspace/v72p2d5_p0_preexec_r1_b7f0d3e5`); no edits to any `.py`/`.md`/OpenSpec/
decision-log/memory/cycle_state; no git write operation; no
RESULT_SUMMARY/OPERATOR_RETURN/run_01. Nothing was fixed; findings are reported only.

## 9. Verdict

`PRE_EXECUTE_REVIEW_PASS` — the frozen packet is faithful to the source and the
accepted plan (27/27 P03 rows AGREE, zero DISAGREE, defect fix and authorization
chain verified in code, R-R1/R-R2 honestly described, refusal exit-3 verified
empirically, 195/195 tests pass, protected roots absent throughout), and all five
open questions are DECIDED in §7 with run/operator deltas.

This is NOT an authorization. `p0_cost_execution_authorized` remains `false`;
only the user may flip it, and only after freshly re-producing the OQ-P0-4
evidence (roots absent, nine keys false, gate `P0_PACKET_REVIEW`, exit-3 refusal).

Strongest claim supported by the evidence: the frozen P0 parameters, per-`f`
slicing fix, authorization gating, output contract, and residual-risk disclosures
match the code at `b27f31da`, and the packet is fit to be authorized under the §7
decisions.
Explicitly NOT claimed: no FER, no leakage, no secret-key rate, no qualification,
no verdict on NB-LDPC or the dv3 mother, no prediction that P0 will pass, and no
claim about any future G1/G2 outcome.
