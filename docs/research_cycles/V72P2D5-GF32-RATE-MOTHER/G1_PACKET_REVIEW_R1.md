# G1 Packet Review R1 — independent read-only verdict on G1_EXECUTION_PACKET_R1.md

- Role: independent reviewer. Did not write the G1 packet, the v72p2d5 implementation,
  or any prior D5/P0/G1 artifact; did not execute any prior packet. No author claim
  accepted on faith; every row re-derived from source, OpenSpec, and accepted records.
- Under review: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`
  (packet status `EXECUTE_NOT_AUTHORIZED` + `IMPLEMENTATION_REWORK_REQUIRED_BEFORE_PRE_EXECUTE`),
  submitted as commit `4bf2682a`.
- Source truth: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  (core), `scripts/v72p2d5_gf32_rate_mother.py` (CLI),
  `openspec/changes/v72p2d5-p0-g1-g2-production-path/design.md` (design),
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml` (state),
  `P0_RESULT_ACCEPTANCE_R1.md` A05 + `GUARD_REWORK_REVIEW_R1.md` L1–L4 (carried limitations),
  `G1_UNAUTHORIZED_DISPOSITION_R1.md` (VOID record).
- Authorization: **false**. This review authorizes nothing and executes nothing.
  **G1 包评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。**
- VOID-root hygiene: the retained `workspace/v72p2d5_g1/20260906_r1/` root was listed
  by name only (entry names, never content). No number from inside that root is used
  anywhere below as evidence or to tune any rule; the signal rule in OQ-G1-SIGNAL is
  prospective only. Call-count `440` below is cited exclusively from design §3 and core
  code arithmetic, never from the VOID root.

## 1. Numbered baseline checks (PASS / FAIL / NOT_VERIFIABLE)

| # | Check | Result | Basis |
|---|-------|--------|-------|
| B1 | `4bf2682a` changes exactly one file (`G1_EXECUTION_PACKET_R1.md`) | NOT_VERIFIABLE | No shell/git in this review environment; `git show --stat` could not be run. Non-blocking: carried as required acceptance item A11 (confirm before implementation). Packet §6 self-checks are author claims, not independent evidence. |
| B2 | P0 cost accepted (`COST_MEASUREMENT_ONLY`), `next_gate: G1_PACKET_REVIEW`, all nine authorization keys false, promotion false | PASS | `cycle_state.yaml`: `p0_cost_result_accepted: true` + `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`; `next_gate: G1_PACKET_REVIEW`; `structure/g0/g0_recovery/p0_cost/g1/g2/synthetic/real/formal_execution_authorized` all `false`; `scientific_promotion: false`. |
| B3 | Retained invalid root `workspace/v72p2d5_g1/20260906_r1/` exists with four files, `VOID_RETAINED_IN_PLACE` | PASS (name-level) | Directory listing: parent holds only `20260906_r1`; it holds exactly `execution_summary.json, report.md, results.json, table.csv`. Sizes/mtimes not re-statable here (no shell); VOID status per `G1_UNAUTHORIZED_DISPOSITION_R1.md` D02–D04. No content read performed. |
| B4 | Proposed root `workspace/v72p2d5_g1/20260907_r2/` and G2 root absent | PASS (name-level) | Parent listing contains only `20260906_r1`; direct reads of `workspace/v72p2d5_g1/20260907_r2` and `workspace/v72p2d5_g2` both return file-not-found; full `workspace/` listing shows no `v72p2d5_g2*` entry. |
| B5 | Packet carries every A05 limitation and GUARD L1–L4 without weakening | PASS | Packet §4 carries L1, L2, L3, L4, L-RSS, L-SCALE, L-ITER, plus additive T1. L1 states the (a)/(b) choice explicitly (chooses no-subdirectory invariant); L2 keeps "narrow tripwire, not general proof"; L3 cites parser logic, not a live red run; L4 keeps 1969/1887/zero-content-diffs with `63` superseded; L-RSS/L-SCALE/L-ITER wording matches A05 substance. |

Pre/post root snapshots (§6 below) are identical.

## 2. Frozen parameter audit (packet §2 vs design + core)

Row-table arithmetic re-derived: `ceil(64*3.814742*1.0/5)=ceil(48.8286976)=49`;
`ceil(64*3.814742*1.2/5)=ceil(58.5944371)=59`;
`ceil(64*3.347605*1.0/5)=ceil(42.849344)=43`;
`ceil(64*3.347605*1.2/5)=ceil(51.4192128)=52`.
Call-count arithmetic re-derived: per `f`, 100 blocks × `calls+=2` = 200 APP calls
plus 20 subset × `calls+=1` = 20 oracle calls → 220 per `f` × 2 = **440**.

| # | Item | Verdict | Source locations |
|---|------|---------|------------------|
| P01 | Width `n_IR=64` | AGREE | Core `G1_WIDTH = 64`; `run_g1_phase` builds 64-wide mothers; design §3 G1 row |
| P02 | `f` values `1.0, 1.2`, in that order | AGREE | Core `G1_F = (1.0, 1.2)` tuple; `_run_rate_scan` iterates `f_list` in order |
| P03 | L1 rows `49, 59`; L2 rows `43, 52` | AGREE | `_rows_required` (`ceil(width*ce*f/5)`) + `CE_L1_MEAN`/`CE_L2_ORACLE_MEAN`; arithmetic above |
| P04 | Mother reuse (one L1 + one L2 max mother, natural-prefix reuse across both `f`) | AGREE | `run_g1_phase` builds one L1 (`G1_L1_K_MIN=59`) + one L2 (`G1_L2_K_MIN=52`) mother; design §2 |
| P05 | Graph seeds L1 `2026090501`, L2 `2026090502` | AGREE | Core `L1_GRAPH_SEED`/`L2_GRAPH_SEED`; `run_g1_phase` build sites |
| P06 | Block seeds exactly `2026090600..2026090699`, 100 paired blocks per `f`, same ordered list both `f` | AGREE | Core `G1_SEEDS = tuple(range(2026090600, 2026090700))`; `_run_rate_scan` uses `seeds[:n_blocks]` with `n_blocks=G1_BLOCKS=100` inside each `f` iteration |
| P07 | Oracle subset first 20 seeds per `f`, diagnostic only | AGREE | `G1_ORACLE_SUBSET = 20`, `t < oracle_subset`; `ora_ok` recorded but absent from `mono`/`passed`; design §3 "Oracle never gates PASS" |
| P08 | Decoder: historical GF32, cold start, `max_iter=90`, `damping_alpha=1.0` | AGREE | `MAX_ITER = 90`, `DAMPING_ALPHA = 1.0`; `bind_historical_decoder`/`historical_g0_decoder` pass `warm_beliefs=None`; entrypoint `decode_row_layered_fftqspa` in `v35_algorithm_development.py` |
| P09 | Calls 440 = APP `100×2×2` + oracle `20×2×1` | AGREE | `_run_rate_scan` increments; arithmetic above |
| P10 | Model-F input: accepted fixed root `workspace/v72p2d5_model_f_input/20260907_r1/` | AGREE | Core `MODEL_F_INPUT_FORMAL_ROOT`; `run_g1_synthetic` loads via `_load_model_f_input_or_blocked` then `prepare_model_f_prior` (frozen `LAMBDA_STAR`) before any build/decode/write |
| P11 | L1→L2 order; L2 always attempted; oracle never controls verdict | AGREE | `_run_layered_block`: L1 decode → softmax → APP-fed L2 decode unconditionally; `app_exact = e1 and e2`; oracle branch additive only |
| P12 | Budget: G1 total `<=900 s`; per-call reference `120 s`; one outer watchdog mandatory | AGREE (contract) | `G1_TOTAL_BUDGET_S = 900.0`; `G0_WALL_BUDGET_S = 120.0` (reference value); no in-code abort — operator/review-enforced, which is why OQ-G1-WATCHDOG freezes the outer guard. Not a scientific-input disagreement. |
| P13 | Output exactly four no-overwrite files | AGREE | `STAGE_EVIDENCE_FILES`; `_write_stage_evidence` raises `FileExistsError` before any write |
| P14 | Metric `app_failure_fraction = 1 - app_exact_count/attempted`; synthetic block fraction, never FER | AGREE | `_run_rate_scan` per-`f` dict; no `FER` claim in the G1 path |
| P15 | Current frozen trend condition: monotonic APP exact rate, zero crash, zero nonfinite | AGREE (note) | `run_g1_phase` returns `"passed": bool(mono and nonfinite == 0)` with `mono = all(b >= a ...)`; `crashes` is hard-coded `0` (exceptions abort the phase with no evidence rather than being counted — fail-loud, acceptable, but "zero crash" is vacuous as a conjunct today) |
| P16 | Current trend condition admits an all-zero APP exact sequence as pass | AGREE | Rates `[0.0, 0.0]` satisfy `all(b >= a)`; with `nonfinite == 0`, `passed` is `True` by pure reading of the expression. This is exactly the degeneracy OQ-G1-SIGNAL closes. |

Explicit §3 confirmations (all AGREE): prefix slicing (`h1[:m1]`, `h2[:m2]`) occurs at
the top of each `f` iteration before any `_run_layered_block`/`_decode_block` call;
oracle is diagnostic only; the `passed` expression is exactly monotonic-plus-zero-nonfinite;
an all-zero APP exact sequence therefore currently passes; G1 persists neither APP
syndrome counts nor iteration aggregates (per-`f` dicts carry only
attempted/app_exact_count/app_exact_rate/app_failure_fraction/oracle_exact_count);
Windows RSS can currently be null (`_rss_bytes` returns `None` when `resource` is
unavailable — and `run_g1_phase` records no RSS at all today); the G1 root constant
still names the retained invalid root (`G1_FORMAL_ROOT = "workspace/v72p2d5_g1/20260906_r1"`);
both G1 and G2 evidence writers contain the duplicated fallback
`item.get("app_failure_fraction", item.get("app_failure_fraction", 1.0))`.

Counts: 16 AGREE, 0 DISAGREE, 0 NOT_VERIFIABLE. Zero scientific DISAGREE.

## 3. D1–D6 decisions

- **D1 root — ACCEPT.** The proposed `workspace/v72p2d5_g1/20260907_r2/` is absent,
  shares only the parent with the VOID root, and carries a distinct date+revision
  identity (`20260907_r2`) that cannot collide with a rerun of `20260906_r1`. The
  no-overwrite writer (`FileExistsError` before any write) plus the disposition bar
  on reuse/overwrite/comparison of `20260906_r1` close the overwrite path. Smallest
  sufficient implementation: change the G1 production root constant to exactly the
  decided path; touch only tests/OpenSpec/docs that own this G1 path. Decided in
  OQ-G1-ROOT below.
- **D2 RSS — ACCEPT.** The historical decoder runs fully in the current Python process:
  direct call through `bind_historical_decoder`/`historical_g0_decoder`, and
  `v35_algorithm_development.py` imports stdlib + numpy only (no subprocess,
  multiprocessing, threading, numba). No evidence of child processes exists, so no
  process-tree monitor and no new dependency may be required. Current-process working
  set is therefore the right scope. A single end-of-run reading is not a peak, so the
  gate additionally needs the frozen sampling semantics in OQ-G1-RSS below (sample
  after every block result, persist the maximum). Smallest sufficient implementation:
  extend `_rss_bytes()` with the ctypes/`GetProcessMemoryInfo` current-process
  fallback, keep the Unix `resource` path, `None` only when neither exists, plus
  focused fake/monkeypatched tests.
- **D3 observability — ACCEPT.** The proposed per-`f` aggregate schema (attempted; APP
  exact count/rate/failure fraction; APP syndrome-ok count; APP total + max per-block
  iterations; oracle exact/syndrome-ok/total-iterations on the frozen 20-block subset;
  nonfinite count; total decoder calls) distinguishes exact failure (exact=0,
  syndrome may be 0/1) from syndrome failure (syndrome_ok=0), nonfinite output
  (finite=0), and 90-iteration saturation (max per-block APP iterations at cap vs early
  convergence in the total). Per-`f` aggregates are sufficient; raw beliefs and
  per-symbol records must not be demanded. Implementation must enforce the identities
  `failure_fraction = 1 - exact/attempted`, `0 <= app_exact_count <= 100`,
  `0 <= oracle_exact_count <= 20`, `attempted == 100`, `decoder_calls == 440`.
- **D4 writer — ACCEPT.** The producer (`_run_rate_scan`) always emits
  `app_failure_fraction`, so the duplicated fallback is dead weight, not compatibility.
  Smallest fail-loud correction: direct required-key access in both writers; a single
  correctly named fallback only if a concrete compatibility need is shown (none is).
  Public column `app_failure_fraction` and its definition are preserved. No
  compatibility layer.
- **D5 guard depth — ACCEPT.** Both test-file helpers (`_snapshot_dir` in
  `test_v72p2d5_gf32_rate_mother.py` and `test_v72p2d5_model_f_input.py`) remain
  top-level-files-only (`q.is_file()` filter, no recursion), and no no-subdirectory
  assertion exists in either file today — so the disclosed nested-write gap is real
  and D5's option (b) closes it for the flat four-file evidence contract. Smallest
  sufficient implementation: add the explicit no-subdirectory invariant to both
  helpers. No recursive hashing, no manifest system.
- **D6 reachability — ACCEPT (conditional).** The stated probe is sufficient iff every
  listed condition holds: the CLI loads the core by file path with no `sys.path`
  insertion (`spec_from_file_location`, verified), so a probe file outside the repo
  with cwd at the repo root can observe repo-root-absent-from-`sys.path` and
  `import comparison_bench` failing; the Model-F file-path consumer
  (`_load_model_f_loader`/`_resolve_model_f_input_root`) reaches the accepted input
  without `sys.path` changes; a raising sentinel decode_fn reaches exactly the first
  decoder call (first block, L1 decode inside `_run_layered_block`); nothing is
  written before the sentinel fires (writes happen only after the full scan returns),
  so tmp output stays empty and both fresh roots stay absent. No `python -c`, no
  `sys.path` insertion. (Model-F artifact load inside the probe is an accepted-input
  consumer read, not a CAL/VAL read.)

## 4. Five open questions — all DECIDED

- **OQ-G1-ROOT: DECIDED — accept `workspace/v72p2d5_g1/20260907_r2/`.**
  Frozen wording: the sole fresh canonical G1 root is
  `workspace/v72p2d5_g1/20260907_r2/`; the retained `20260906_r1` root is permanently
  `VOID_RETAINED_IN_PLACE` and is never an option for reuse, overwrite, comparison,
  or citation. No replacement is named.
- **OQ-G1-RSS: DECIDED — current-process working-set sampling is sufficient for the
  2 GiB gate, with frozen peak semantics.**
  Frozen wording: the `<2 GiB` reference (`2147483648` bytes) remains a gate, measured
  as a sampled maximum — `_rss_bytes()` (Unix `resource` path kept; Windows ctypes
  `GetProcessMemoryInfo` current-process working-set fallback added; `None` only when
  neither exists) is called after every block result of the G1 scan (200 APP block
  results across both `f` values, covering the interleaved oracle decodes), and the
  running maximum is persisted as run-level `peak_rss_bytes` (plus per-`f` maxima from
  the same samples). The persisted peak is a sampled maximum (a lower bound on the
  true peak); no process-tree claim is made. Rationale: the decoder is proven
  in-process (D2), numpy temporaries keep freed pages in the working set on the
  sampling timescale, and the width-64 footprint is orders of magnitude below the
  gate, so the residual underestimation cannot flip a gate decision without also
  tripping the multi-sample trend. If `peak_rss_bytes` is `None` or `>= 2 GiB`, no
  PASS may be claimed (see `G1_RESOURCE_OVERRUN`).
- **OQ-G1-SIGNAL: DECIDED — accept the recommended minimum meaningful-signal rule,
  frozen before any authorized G1 data.**
  Frozen wording:
  ```text
  G1_SIGNAL_PASS := (phase completed without exception)
    AND (nonfinite == 0)
    AND (app_exact_rate(1.2) >= app_exact_rate(1.0))
    AND (app_exact_count(1.2) > 0)
    AND ((app_exact_count(1.2) > app_exact_count(1.0)) OR (app_exact_rate(1.2) == 1.0))
  ```
  Integer counts (denominator 100) govern the comparisons. Rationale: a flat all-zero
  line satisfies bare monotonicity but contains zero successful decodes at either
  operating point, so it carries no rate-response information and cannot be called a
  trend pass; a saturated `1.0, 1.0` line demonstrates ceiling performance at both
  points (improvement is impossible) and must not be rejected merely for lacking
  strict increase. This is a G1 trend gate, not G2 qualification: no 50%/90%
  threshold is introduced.
- **OQ-G1-WATCHDOG: DECIDED — freeze the exact outer command and its outcome semantics.**
  Frozen wording: the sole authorized G1 outer command, run with cwd at the repository
  root, is
  ```text
  "C:\Program Files\Git\usr\bin\timeout.exe" -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
  ```
  The frozen scientific budget is 900 s of operator-measured outer wall (monotonic
  clock around the command); 960 s is an outer process guard, never permission to pass
  over budget. Timeout/KILL (exit 124 or signal-kill) consumes the sole attempt; any
  partial root is retained VOID in place; no retry, no rerun, no tuning. Completion
  inside 960 s with outer wall over 900 s is `G1_OVERRUN_900S`, never a pass.
  (Watchdog-binary existence at that path was NOT_VERIFIABLE in this shell-less
  review; Pre-EXECUTE must confirm it — acceptance item A12.)
- **OQ-G1-OUTCOME: DECIDED — seven mutually exclusive terminal labels, evaluated in
  the frozen precedence order.**
  Frozen wording: precedence P1 > P2 > …; the first matching label applies.
  ```text
  P1. G1_PRE_EXECUTION_BLOCKED  — refused before the first decoder call
       (authorization false, Model-F missing/invalid, sentinel failure, target root
       already present, watchdog binary absent, …). Zero decoder calls executed;
       no output created.
  P2. G1_WATCHDOG_TIMEOUT_VOID  — killed by the outer watchdog. Sole attempt
       consumed; any partial root retained VOID; no retry.
  P3. G1_NONFINITE_OR_CRASH_BLOCKED — ≥1 decoder call executed, then nonfinite > 0
       or an exception aborted the run.
  P4. G1_OVERRUN_900S — process completed inside the watchdog but operator outer
       wall exceeded 900 s. Never a pass regardless of signal.
  P5. G1_RESOURCE_OVERRUN — completed in time but peak_rss_bytes >= 2 GiB or
       unmeasurable (None); the reason (rss_over_2gib / rss_unknown) is recorded.
       Never a pass.
  P6. G1_TREND_PASS — completed; G1_SIGNAL_PASS holds; wall ≤ 900 s; peak RSS
       measured and < 2 GiB.
  P7. G1_COMPLETED_NO_SIGNAL_FAIL — completed with zero crash/nonfinite but
       G1_SIGNAL_PASS not met. A current-configuration no-signal verdict only.
  ```
  No label implies FER, real-data performance, qualification, leakage, key rate, or G2
  authorization. The stored boolean `passed` MUST be revised to the full conjunction:
  `passed == true` iff the terminal label is `G1_TREND_PASS` (i.e. signal ∧ wall≤900 s
  ∧ rss-ok); `monotonic`/`nonfinite` fields are retained as components. (Reviewer-added
  implementation requirement; see A13.)

## 5. Required implementation acceptance matrix

Implementation may start only against all frozen items above, and acceptance requires
every box checked (fake/injected/tmp tests throughout; lifecycle-safe):

- A01. Fresh root constant is exactly `workspace/v72p2d5_g1/20260907_r2/`; old-root
  string `20260906_r1` appears nowhere as a G1 production target; the VOID root is
  untouched (pre/post name/size/mtime stat equal).
- A02. Windows RSS fallback implemented with the frozen per-block-result sampling and
  persisted maximum (`peak_rss_bytes` run-level + per-`f`); Unix path unchanged; `None`
  only when neither method exists; fake/monkeypatched tests green.
- A03. Exact/syndrome/iteration/RSS aggregate schema per D3 + OQ-G1-RSS; identities
  (`failure_fraction = 1 - exact/attempted`), bounds (`app ≤ 100`, `oracle ≤ 20`,
  `attempted == 100`), and `decoder_calls == 440` asserted in tests.
- A04. Fail-loud writer correction in both G1 and G2 writers; public column
  `app_failure_fraction` unchanged.
- A05. No-subdirectory invariant in both test-file snapshot helpers; top-level
  name/size/mtime comparison kept; no recursive hashing/manifest.
- A06. Real-launch sentinel probe/file outside the repo meeting all six D6 conditions;
  no `python -c`, no `sys.path` insertion.
- A07. Lifecycle-safe tests only (explicit fake decoder, injected Model-F arrays,
  temporary output root); no test binds the production decoder or a default formal root.
- A08. Full three-file D5 suite green with basetemp under `workspace/`.
- A09. All authorizations still false, promotion false, `next_gate` unchanged by
  implementation; both proposed G1 (`20260907_r2`) and G2 roots absent before/after tests.
- A10. No decoder/`--phase` execution, no prepare/verify, no CAL/VAL/parquet/row reads
  during implementation except the D6 probe's accepted-Model-F consumer load.
- A11. (Provenance handoff for B1) Confirm `git show --stat 4bf2682a` touches exactly
  `G1_EXECUTION_PACKET_R1.md` before implementation starts.
- A12. (Watchdog handoff) Confirm the frozen `timeout.exe` path exists and `timeout -k`
  semantics behave as frozen, at Pre-EXECUTE.
- A13. (Outcome wiring) `passed` revised to the OQ-G1-OUTCOME conjunction
  (`true` ⟺ `G1_TREND_PASS`); entrypoint measures outer wall for the 900 s conjunct.

## 6. Pre/post root snapshots (name-level; read-only)

- Pre (review start): `workspace/v72p2d5_g1/` → `[20260906_r1]`;
  `workspace/v72p2d5_g1/20260906_r1/` → 4 entries
  (`execution_summary.json`, `report.md`, `results.json`, `table.csv`);
  `workspace/v72p2d5_g1/20260907_r2/` → absent; `workspace/v72p2d5_g2/` → absent.
- Post (after drafting this review, before writing it): identical — parent still only
  `20260906_r1`; VOID root still exactly the same 4 names; `20260907_r2` still absent;
  `v72p2d5_g2` still absent. Equality holds. (Sizes/mtimes are unchanged by
  construction: this review performed directory listings and source reads only, never
  a workspace write; byte-level re-stat is left to the shell-owning implementer per A01.)

## 7. Commands executed and explicitly not executed

- Executed: none that touch state. This review used file/directory reads only
  (task packet, G1 packet, design, core `v72p2d5_gf32_rate_mother.py`, CLI script,
  `cycle_state.yaml`, P0/GUARD/disposition records, test helpers, `v35` decoder
  imports) plus hand arithmetic. No pytest was run (packet review; source reading and
  arithmetic are sufficient; no green number was sought).
- Explicitly NOT executed (all prohibitions observed = true): no decoder invocation;
  no `--phase` of any kind (not even a refusal probe); no Model-F prepare/verify; no
  CAL/VAL/parquet/raw-row read; no write/delete/move/rename/copy/normalization/hash
  under any `workspace/v72p2d5_*` root; no modification to any `.py`, existing `.md`,
  OpenSpec, decision-log, memory, or `cycle_state.yaml`; no git write of any kind
  (no add/commit/push/reset/stash/checkout/clean/rebase/revert/amend/renormalize).
  The single permitted new file is this review. It is not committed or pushed.

## 8. Strongest supported claim and explicit non-claims

- Strongest supported claim: the frozen G1 contract (width, `f` order, row tables,
  mother reuse, seeds, oracle discipline, decoder configuration, 440-call budget,
  Model-F input, L1→L2 ordering, budgets, four-file output, metric) agrees with both
  the OpenSpec design and the core implementation on all 16 audited parameters with
  zero scientific disagreement; the current `passed` expression provably admits an
  all-zero exact sequence; D1–D6 are each sufficient in their smallest stated form;
  and the five open questions are now prospectively decided with exact frozen wording,
  so a future implementation is well-posed.
- Non-claims: no FER, no leakage, no key rate, no real-data performance, no method
  qualification, no statement that G1 will pass/complete/fit its budgets, no G2
  authorization, and no citation — ever — of the VOID root's contents. This review
  grants no authorization and executes nothing.

## 9. Verdict

`G1_PACKET_REVIEW_PASS`

(Implementation may start against §5, but G1 remains unauthorized and unexecuted.
G1 包评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。)
