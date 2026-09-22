# D7-D Pre-RESULT review R1 (independent reviewer; executed root under review)

## 0. Verdict, scope, independence

- Verdict: **D7_D_PRE_RESULT_REVIEW_PASS_R1**.
- Scope: independent Pre-RESULT recomputation R01-R20 of the single authorized
  D7-D invocation (`docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/`
  contracts; scoped code at HEAD `eba385bb`; immutable root
  `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7/`).
  PASS means internal coherence only: it is not result acceptance, not
  solidification, not route authority, and not a claim about either schedule.
- Independence: this reviewer is a separate context from the execution operator,
  authored none of the reviewed artifacts, ran no decoder, read no Model-F
  binary content (Model-F inspected by names/sizes/mtime only), did not re-run
  the one-shot verifier, and made no root/state/commit mutation. The sole write
  of this review is this file; scratch recomputation scripts/manifests were kept
  under `/tmp/opencode/d7d_review_r1/` only.
- Commands run (all read-only): file inventory + sha256 (twice, start/end);
  stdlib-only Python recomputation of `decoder_records.csv`,
  `paired_schedule.csv`, `stratum_summary.csv`, `manifest.json`,
  `summary.json`, `report.md`, `command_log.txt`; Markdown table reparse of the
  operator return; `git log/show/diff/status/check-ignore/rev-list`; metadata
  `find/stat` of protected roots; environment probes (venv `python`
  version/NumPy, `resource` RSS, `command -v timeout`, `timeout --version`,
  `uname`, `/etc/os-release`); forbidden-token scans. No `--verify` re-run (the
  one-shot was already spent by the operator), no decoder invocation, no
  Model-F content read, no test re-run.
- Review timestamp: 2026-09-11 (WSL local) after revocation commit `eba385bb`.

## 1. Lifecycle and authorization (R01-R02)

- **R01 PASS.**
  - Section 0 authorization is byte-identical between the task packet and
    `D7_D_AUTHORIZATION_RECORD_R1.md` (programmatic block extraction of both
    quote blocks compared equal, including every punctuation mark).
  - UUID `64660d16-397d-4ef3-8454-3066d27c12c7` is fresh and single: `git log
    --all -S <uuid>` returns only `7a3f0d92`; the only HEAD-tracked file
    containing it is the authorization record; exactly one
    `workspace/d7_d_schedule_discriminator_*` root exists; no second UUID
    anywhere in the cycle directory, `workspace/` or the root.
  - Lifecycle true->false: `7a3f0d92` adds the authorization record and changes
    exactly `d7d_execution_authorized: false -> true` (2 files, 187 insertions,
    1 deletion); `eba385bb` changes exactly `true -> false` and nothing else
    (1 insertion, 1 deletion). HEAD is `eba385bb` (branch
    `formal-ir-v72p1-addendum-clean`). Revocation time 07:31:15 +0800 is after
    the root's last write 07:30:05 +0800 and before the operator return was
    authored; the operator return is uncommitted, i.e. no root content was
    committed or interpreted before revocation.
  - One invocation, attempt CONSUMED: 256 completed decoder records with
    `converged_*` statuses, the manifest records `authorization_consumed: true`
    and `retries/reruns/resumes = 0`, and there is no second root, duplicate
    call, resume record or alternate UUID. `NOT_VERIFIABLE` correctly does not
    apply.
- **R02 PASS** (with one non-blocking wording observation, see §8 obs 2).
  - The frozen command with this UUID is token-identical in the authorization
    record §1 and in the operator return §1 JSON argv (parsed and compared
    token-by-token: exact match; no added flag, pipe, redirection, concurrency,
    alternate Python or alternate root).
  - `command_log.txt` line 1 equals `manifest.json.command` exactly:
    `scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root
    workspace/v72p2d5_model_f_input/20260907_r1 --out-root
    workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7`
    - the frozen command's script+argument tokens with this UUID, written by the
    frozen writer design (`" ".join(sys.argv)`); the `timeout -k 30 1800 python`
    launcher prefix is a parent-process fact preserved in the operator return
    argv JSON.
  - PATH adapter/interpreter/environment disclosure: authorization record
    §1/§3 with E08/E09, operator return §1. Independently re-checked read-only in
    the live WSL: venv interpreter `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`
    = CPython 3.12.3 / NumPy 2.4.4; bare `python` absent on the default PATH
    (adapter required); `PYTHONPATH` unset; `/usr/bin/timeout` = GNU coreutils
    9.4; kernel `6.18.33.2-microsoft-standard-WSL2`; Ubuntu 24.04.4 LTS - all
    match the recorded environment.

## 2. Root, schema, manifest (R03-R05)

- **R03 PASS.** The root contains exactly seven files and zero subdirectories:
  `manifest.json` 3164, `decoder_records.csv` 57659, `paired_schedule.csv`
  17690, `stratum_summary.csv` 1777, `summary.json` 1546, `report.md` 455,
  `command_log.txt` 290 bytes, all mtime 2026-09-11 07:30:05.5 +0800 (epoch
  1789083005.5, i.e. before the 07:31:15 revocation). Two independent reads
  (inventory+sizes+mtime and sha256 over all seven files) are identical:
  `MANIFEST_IDENTICAL` / `HASHES_IDENTICAL`; no post-exit write occurred.
- **R04 PASS.** The recorded matrix is exactly the frozen 256-call order:
  16 seeds `2026091300..2026091315` x `f in [1.0,1.2]` x four conditions, each
  identity dispatching `ROW_LAYERED` then `FLOODING`
  (`call_idx = 2k-1 / 2k`). Element-by-element comparison of all 256 rows to a
  literal re-derivation of the frozen loop: **0 mismatches**; first call
  `(1, 1.0, 2026091300, L1_MARGINAL, ROW_LAYERED, 49)`, last call
  `(256, 1.2, 2026091315, L2_ORACLE_U1, FLOODING, 52)`; layer mapping L1 for
  L1_* conditions and L2 for L2_*; rows 49/59 L1 and 43/52 L2; `n=64`.
- **R05 PASS.** The D7-D core only aliases the D7-C contract (no redefinition):
  `F_VALUES=(1.0,1.2)`, `L1_ROWS={1.0:49,1.2:59}`, `L2_ROWS={1.0:43,1.2:52}`,
  `BLOCK_SEEDS=2026091300..2026091315`, graph seeds `2026090501`/`2026090502`,
  `MAX_ITER=90`, `DAMPING_ALPHA=1.0`, `DECODER_FLOOR=1e-15`,
  `LAMBDA_STAR=137.3823795883264`, the four condition names and their layer map,
  `n=64`. The accepted estimator is called at D7-C source L448 as
  `d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)`; the rejected
  `prepare_model_f_prior(` and `build_f_model(` identifiers have **zero**
  occurrences in both the D7-C core and the D7-D core. The four prior formulas
  (`L1_MARGINAL = sum_u2`, `L1_ORACLE_U2 = J[:,u2_true,b]` normalized,
  `L2_MARGINAL = sum_u1`, `L2_ORACLE_U1 = J[u1_true,:,b]` normalized, zero-mass
  fallback uniform `1/32`) and the single boundary
  `d5._floor_renorm(prior_qn.T, DECODER_FLOOR)` are unchanged; oracle truth
  selects a slice only and is not persisted. Manifest fields match the run
  (`model_f_root`, `model_f_files` sizes 208467/752 metadata-verified, estimator
  string, lambda, rows, seeds, schedules, decoder IDs, budgets, seven-file list,
  terminal priority, call order) and the manifest `uuid`/`out_root_name` match
  the authorization UUID/root.

## 3. Implementation identities and scope (R06)

- **R06 PASS.** `bind_schedule_decoders()` returns exactly two schedules:
  `ROW_LAYERED -> v35.decode_row_layered_fftqspa` with `max_iter=90,
  damping_alpha=1.0, warm_beliefs=None, field=None`, and
  `FLOODING -> v35.decode_flooding_fftqspa` with `max_iter=90, field=None` (the
  v35 source signatures have no damping/warm-start parameter for flooding, and
  `DEFAULT_MAX_ITER` is never used). `dispatch_schedule` rejects any schedule
  outside the frozen two; the record/paired/strata files contain only
  `ROW_LAYERED`/`FLOODING`. No third schedule, no early stop across identities,
  no cross-layer APP or cross-layer returned beliefs in core or runner. The four
  reviewed artifacts are byte-identical between implementation commit `43f07186`
  and HEAD, and the worktree diff for them is empty (`DIFF_EMPTY_OK`); the test
  suite's S03 pins within-pair array equality and the production binding
  identities in fake qualification.

## 4. Record arithmetic (R07-R09), recomputed from CSV

- **R07 PASS.** `decoder_records.csv` has exactly 256 rows with the frozen
  25-column schema; `call_idx` is 1..256 unique and contiguous; each
  `identity_idx` 1..128 appears exactly once per schedule; odd=ROW_LAYERED,
  even=FLOODING parity holds for all 256; missing/duplicate/retry/resume = 0.
- **R08 PASS.** Exact is isolated from syndrome-only, crash and nonfinite:
  - `exact = (symbol_errors == 0)` for all 256 records: **0 mismatches**.
  - `syndrome_ok` never coexists with `unsatisfied_checks > 0`; `exact` true
    with `syndrome_ok` false = 0; `exact` with nonzero unsatisfied = 0.
  - exact 83 / syndrome_ok 83, syndrome-only without exact 0 -> exact and
    syndrome-only remain separate and unmerged.
  - statuses `converged_exact` 83, `converged_no_syndrome` 173; crash records 0,
    nonfinite records 0, watchdog timeouts 0.
- **R09 PASS.** Work arithmetic with the frozen disclosed-row degree sums
  (L1 49->147, 59->177; L2 43->129, 52->156):
  `check_node_updates = rows x completed_iterations` and
  `check_edge_updates = degree_sum x completed_iterations` for all 256 records:
  **0 mismatches**; iteration-0 records 0 (min iterations 2).

| Metric | ROW_LAYERED | FLOODING | Total |
|---|---|---|---|
| completed iterations min/median/max | 2 / 90 / 90 | 4 / 90 / 90 | min 2, max 90 |
| iterations sum | 8021 | 8444 | 16465 |
| check node updates (min/max, sum) | 118 / 5310, 395067 | 236 / 5310, 417423 | 812490 |
| check edge updates (min/max, sum) | 354 / 15930, 1185201 | 708 / 15930, 1252269 | 2437470 |

## 5. Pairs, strata and terminal (R10-R12), recomputed

- **R10 PASS.** All 128 `paired_schedule.csv` rows were independently
  recomputed from the 256 decoder records and compared field-by-field (booleans,
  integers exact; floats tolerance 1e-9): **0 mismatches**. Aggregates:
  `layered_exact=43`, `flooding_exact=40`, `layered_only_exact=3`,
  `flooding_only_exact=0`, `both_exact=40`, `neither_exact=85`; syndrome-only
  analogues `layered_only_syndrome_ok=3`, `flooding_only_syndrome_ok=0`,
  `both_syndrome_ok=40`, `neither_syndrome_ok=85` (kept separate from exact).
  The three layered-only identities are 26 (1.0/2026091306/L1_ORACLE_U2), 46
  (1.0/2026091311/L1_ORACLE_U2), 101 (1.2/2026091309/L1_MARGINAL).
  `iteration_diff`/`check_update_diff`/`edge_update_diff` and `wall_ratio` are
  non-empty for all 128 valid pairs; `iteration_diff` is 0 for 85 pairs and
  nonzero for 43 (range 0..80; flooding never wins an exact flag). The operator
  return's full 128-row table and its aggregates match the CSV exactly.
- **R11 PASS.** All eight stratum counts and labels recompute by the frozen
  first-match rules: **0 mismatches** (medians included, tolerance 1e-9):

| # | f | layer | condition | L exact | F exact | lo | fo | both | neither | label |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0 | L1 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 2 | 1.0 | L1 | L1_ORACLE_U2 | 10 | 8 | 2 | 0 | 8 | 6 | MIXED_SCHEDULE_EFFECT |
| 3 | 1.0 | L2 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 4 | 1.0 | L2 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 15 | EXACT_TIE_LOW |
| 5 | 1.2 | L1 | L1_MARGINAL | 3 | 2 | 1 | 0 | 2 | 13 | EXACT_TIE_LOW |
| 6 | 1.2 | L1 | L1_ORACLE_U2 | 16 | 16 | 0 | 0 | 16 | 0 | EXACT_TIE_HIGH |
| 7 | 1.2 | L2 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 8 | 1.2 | L2 | L2_ORACLE_U1 | 13 | 13 | 0 | 0 | 13 | 3 | EXACT_TIE_HIGH |

  No stratum is incomplete; flooding-advantage strata 0; layered-advantage
  strata 0; the operator return's stratum table and `summary.json.strata` match.
- **R12 PASS.** Terminal recomputed in the frozen T1-T10 priority order:
  no pre-execution block; 0 watchdog; 0 crash/nonfinite; resource gates pass
  (stored 65.945069 s <= 1500 s, peak RSS 105304064 B < 2147483648 B); 256/256
  records complete; 0 flooding-advantage and 0 layered-advantage strata; no
  both-direction mix; exact flags are **not** identical for all 128 identities
  (3 differ) -> first applicable terminal is
  **`D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`**, identical to the stored terminal in
  `summary.json`, `report.md`, `command_log.txt` and child stdout. All eight
  labels are recorded under this terminal, as required.

## 6. Resources, labels and verifier (R13-R17)

- **R13 PASS.** Single sequential `for` loop over the frozen matrix; records
  256/256; `stop_terminal=""`, `calls_remaining=0`; no replacement cell, no
  retry/rerun/resume/concurrency; the process-local single-use guard and the
  already-false state make any second production run impossible without a new
  authorization.
- **R14 PASS.** Per-call wall min 0.009717 s / max 0.435832 s, all <= 120 s;
  stored scientific wall 65.94506893705693 s (equals the record sum) <= 1500 s;
  outer GNU `timeout -k 30 1800` reported wall 67.17821956600528 s <= 1800 s
  (+30 s grace); exit 0 with `timeout_124 false` is consistent with 256
  completed records and no stop terminal; retries/reruns/resumes = 0.
- **R15 PASS.** All 256 records carry `rss_bytes = 105304064` (finite,
  positive, ~100.4 MiB), equal to `summary.json.peak_rss_bytes`, and
  `< 2 GiB`; the preflight/E10 sandbox probe inflation (1287495680 B) was also
  in-bounds; a fresh live probe now reads `ru_maxrss = 9132 KiB`, so the
  inflation did not reproduce - either way the run-stored value is in-bounds
  and no RSS stop applied.
- **R16 PASS.** Seven-file scalar-only schema: the CSV headers equal the frozen
  25/23/28 field lists exactly, all values are scalars, and the prohibited-token
  scan over all seven files found no `posterior`, `cross_layer`, vector/raw
  payload, digest or integrity token. `current_belief_label` is always
  `CHECK_UPDATED_CURRENT_BELIEF` (no iteration-0 `PRIOR_ONLY` row), and
  `beliefs_conditioned = (iterations > 0)` for all rows; belief diagnostics
  ranges are in-bounds (`belief_max_prob` 0.403067..1.000000,
  `belief_mean_entropy` 0..4.343407 bits). No cross-layer fields and no
  cross-layer APP.
- **R17 PASS (with stated limitations).** The sole verifier output recorded in
  the operator return is
  `VERIFY_OK {'ok': True, 'problems': [], 'records': 256, 'terminal': 'D7_D_SCHEDULE_EFFECT_INCONCLUSIVE'}`
  with exit 0; exactly one `VERIFY_OK` string exists in the cycle directory and
  no verifier artifact was written into the root. Per packet §7 this reviewer did
  **not** re-run the one-shot verifier. Verifier limitations: it recomputes
  pairing, paired counts, all eight strata, work arithmetic and the terminal from
  the seven scalar files only - it does not re-execute decoders nor re-derive raw
  arrays, so the within-pair array equality is pinned by the frozen S03
  qualification rather than re-checkable from the root alone (the operator
  return states this limitation honestly).

## 7. Authorization, prohibitions and immutability (R18-R20)

- **R18 PASS.** Protected roots are unchanged at metadata level: D7-C six files
  282/23599/2709/1130/362/728 B with mtime 1789058019; D7-B five files
  111/44743/1008/80/449 B with mtime 1789043618; Model-F `model_f_input.npz`
  208467 B and `model_f_input_summary.json` 752 B with mtime 1788718027 - all
  exactly matching the authorization record E06 snapshot. All 11 protected
  roots exist; their newest mtime (D7-C, 1789058019) predates the authorization
  time (1789082737) and the run. R1d (`workspace/d6_graph_mother_r1d_*`) and G2
  (`workspace/v72p2d5_g2`) are absent; the only workspace entry newer than the
  authorization time is the D7-D root itself.
- **R19 PASS.** `cycle_state.yaml` has `d7d_execution_authorized: false` after
  revocation and all other authorization fields false (`plan_accepted`,
  `implementation_authorized`, `formal/synthetic/real_execution_authorized`,
  `scientific_promotion`, `g1_authorized`, `g2_authorized`), with no
  accepted/qualification/promotion or attempt fields added prematurely
  (`decoder_executed: false`, `result_created: false` is the required
  pre-solidification state). No prohibited action/root/phase appears: the root
  and manifest contain no `--phase`, G1/G2, CAL/VAL/raw, cross-layer APP or
  acceptance token; no R1d/G2/CAL/real root was created.
- **R20 PASS.** Root read twice (start/end) with identical sizes, mtimes and
  sha256; the seven shas are
  `eed5c677...` (decoder_records), `a9e3a635...` (paired_schedule),
  `4f7bb513...` (stratum_summary), `6a818e4c...` (summary),
  `2c407ce9...` (report), `3134884c...` (command_log), `cad2ae0e...`
  (manifest). Scoped Git state is clean: only the uncommitted
  `D7_D_OPERATOR_RETURN_R1.md` (plus the pre-existing untracked
  `.workbuddy/tasks/` tree) is untracked in the scoped paths; nothing is staged;
  no scoped tracked file is modified. HEAD `eba385bb` is local-only (origin
  `formal-ir-v72p1-addendum-clean` is 0 behind / 106 ahead; origin contains
  neither lifecycle commit); no push. Claim ceiling is preserved: this review
  makes no FER, leakage, efficiency, key-rate, qualification, promotion,
  R1d/G1/G2 or general GF32/NB-LDPC claim, and the terminal remains
  INCONCLUSIVE rather than a superiority statement in either direction.

## 8. Discrepancies and blocking assessment

**No blocking discrepancy found. No FAIL/BLOCKED condition applies.**

Non-blocking observations (no arithmetic, schema, lifecycle or gate impact):

1. **Operator return §7 overall wall "median" label.** The reported
   `median 0.318371 s` is the upper of the two central order statistics
   (`sorted[128] = 0.318371162...`), not the interpolated median
   (`0.3169090934970882 s = (sorted[127] + sorted[128]) / 2`). Every other
   wall figure recomputes exactly (min 0.009717 s, max 0.435832 s, sum
   65.945068937057 s), the artifact-level medians in `stratum_summary.csv`
   recompute with zero mismatches, and both wall gates hold by >100x margin.
   Recommended (main thread, optional): correct that single descriptive number
   in the uncommitted operator return before the conditional solidification
   commit; no repair or re-execution of any kind is implied or needed.
2. **`command_log.txt` launcher prefix.** Line 1 is the child's `sys.argv`
   (script + argument tokens with this UUID), matching `manifest.json.command`;
   it omits the `timeout -k 30 1800 python` parent prefix by frozen writer
   design, and the complete frozen argv is preserved token-for-token in the
   operator return §1. Identical convention to the accepted D7-C root; not a
   defect.
3. **Preflight RSS inflation.** E10's sandbox probe value (1287495680 B) did
   not reproduce in a fresh live probe (9132 KiB); the run-stored in-process
   measurement 105304064 B is the frozen value and is in-bounds. No action.
4. **Verifier one-shot.** Not re-runnable and not re-run; its limits are
   recorded in §6/R17. No action.

## 9. Verdict restatement

- **`D7_D_PRE_RESULT_REVIEW_PASS_R1`** - the single D7-D invocation is
  internally coherent: one fresh UUID under one authorized, consumed and
  revoked one-shot authorization; one fresh seven-file/no-subdirectory root,
  immutable after process exit; 256/256 frozen calls in the frozen order with
  zero missing/duplicate/retry/resume; exact perfectly isolated from
  syndrome-only with zero crash/nonfinite/watchdog records; node/edge work
  arithmetic with zero mismatches; all 128 paired rows and all eight stratum
  labels recomputing exactly
  (`EXACT_TIE_LOW, MIXED_SCHEDULE_EFFECT, EXACT_TIE_LOW, EXACT_TIE_LOW,
  EXACT_TIE_LOW, EXACT_TIE_HIGH, EXACT_TIE_LOW, EXACT_TIE_HIGH`); terminal
  `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`; walls/RSS within frozen budgets;
  protected roots untouched; authorization false; no push.
- PASS means internal coherence only. It is not scientific acceptance, not a
  result solidification, not route authority, and does not establish FER,
  leakage, reconciliation efficiency, key rate, protocol recovery, cross-layer
  APP viability, interface acceptance, code qualification, R1d/G1/G2 readiness,
  promotion or any general GF32/NB-LDPC conclusion. The single schedule-effect
  terminal is INCONCLUSIVE and must not be described as a superiority result in
  either direction.
