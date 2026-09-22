# D7-C independent Pre-RESULT review R1

D7_C_PRE_RESULT_REVIEW_PASS_R1

## 0. Verdict, scope, independence

- **Verdict token:** `D7_C_PRE_RESULT_REVIEW_PASS_R1` (internal coherence only;
  not result acceptance, not route authority, no FER/leakage/key-rate claim).
- **Reviewer scope:** independent context, separate from the executor. All R01–R20
  items were recomputed from the six root files, `cycle_state.yaml`, the frozen
  contracts, the reviewed git commits and the read-only source at HEAD
  `d3bd3c8b`; the stored `summary.json`/`report.md` were never trusted as inputs.
- **Writes:** exactly one repository artifact, this document. No commits, no
  `cycle_state.yaml` change, no root mutation, no verify re-run. The only
  filesystem artifact outside this document was a transient `/tmp` hash list of
  the six public file hashes used for the start/end comparison (outside the
  repository, no root/repo content).
- **Zero decoder/Model-F content:** no decoder call, no Model-F or NPZ read, no
  `--verify` invocation, no v35/D5 scientific execution by this reviewer.
- **Commands/queries run (read-only):**
  `read` of the six root files and the cycle documents; `python3` stdin scripts
  re-reading `decoder_records.csv` / `paired_summary.csv` / `summary.json` /
  `manifest.json` with stdlib `csv`/`json` only (no repo imports);
  `sha256sum` of the six files twice (start/end); `stat` on root and protected
  roots; `rg`/`grep` scoped searches; `git log`, `git show --stat`,
  `git diff` on the two lifecycle commits, `git status -sb`,
  `git check-ignore`, `git branch -r --contains`.
- **Independence statement:** the executor's `D7_C_OPERATOR_RETURN_R1.md` was
  read as an object of review, not as evidence; every headline number below was
  recomputed. No dependency on executor claims was accepted without a matching
  literal file value.

## 1. Lifecycle / authorization evidence (R01–R02)

- **R01 — authorization text and one UUID lifecycle: PASS.**
  - The authorization record §0 block is character-identical to the task
    packet §0 block (9 quote lines each, compared literally).
  - Sole UUID `94c0ea15-a786-4cb8-a991-6fec521cccae`: 3 occurrences in
    `D7_C_AUTHORIZATION_RECORD_R1.md`, 5 in `D7_C_OPERATOR_RETURN_R1.md`,
    3 in `manifest.json` (`uuid`, `out_root_name`, `command`), 1 in
    `command_log.txt`, 1 root directory name. No second D7-C UUID exists in the
    cycle directory or in `workspace/`; the only other UUIDs on those surfaces
    are the predecessor D7-B root `c605d1e6-…` (frozen provenance references).
  - Exactly one `workspace/d7_c_bidirectional_oracle_*` root exists
    (`ls -d`): `..._94c0ea15-a786-4cb8-a991-6fec521cccae`. No E13-disposable
    probe root, no replacement root.
  - Lifecycle commits inspected: `b07b5441` (authorize) adds the record and
    changes exactly one state line `d7c_execution_authorized: false -> true`;
    `d3bd3c8b` (revoke) changes exactly one state line `true -> false` and
    touches nothing else (diff `2 files, 189 insertions, 1 deletion` and
    `1 file, 1 insertion, 1 deletion` respectively). Order verified:
    `b07b5441` before `d3bd3c8b`, both before this review; current HEAD is
    `d3bd3c8b`.
  - `cycle_state.yaml` currently: `d7c_execution_authorized: false`,
    `decoder_executed: false`, `result_created: false`; no attempt/result
    fields (pre-solidification state, as required before review).
- **R02 — exact command, adapter and estimator identity: PASS.**
  - `command_log.txt` line 1 is exactly `manifest.json.command` (string equality
    verified): `scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root
    workspace/v72p2d5_model_f_input/20260907_r1 --out-root
    workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae`.
    These are the frozen command's script + argument tokens with this UUID, with
    no added argument, pipe, redirection or alternate root (the manifest string
    is by frozen design the child's `sys.argv`; the `timeout -k 30 1800 python`
    launcher prefix is a parent-process fact, see next bullet).
  - The full frozen argv including the launcher is independently preserved in
    the unmodified harness record `/tmp/d7c_exec_94c0ea15.json`:
    `["timeout","-k","30","1800","python","scripts/…","--model-f-root",
    "workspace/v72p2d5_model_f_input/20260907_r1","--out-root",
    "workspace/d7_c_bidirectional_oracle_94c0ea15-…"]`, with
    `invocation_count: 1`, `return_code: 0`, `timeout_124: false`,
    `outer_wall_s: 33.74325648800004`, empty stderr and the literal stdout
    `terminal=D7_C_BIDIRECTIONAL_DEPENDENCE out=…`. `pythonpath_present_in_ambient:
    false`, `pythonpath_removed_from_child: true`, `path_prepended:
    /home/karel_303/.venvs/hd-qkd-polar-comparison/bin`. This matches operator
    return §1 verbatim.
  - PATH adapter/interpreter evidence: `PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH"`,
    `sys.executable=/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`,
    CPython 3.12.3, NumPy 2.4.4, disclosed in the authorization record §3 and
    E08/E09.
  - Estimator identity: the D7-C module calls
    `d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)` (L448) with the
    default `lam=LAMBDA_STAR=137.3823795883264`; D5's function (verified at
    source) calls `build_f_model_concentration` (`P(a|b) = (counts + lam *
    p_global)/(n_b + lam)`). The rejected `prepare_model_f_prior` /
    `build_f_model` identifiers occur **zero** times in the D7-C module.
    Manifest `estimator`/`lambda_star` match.

## 2. Root / schema / manifest evidence (R03–R05)

- **R03 — fresh six-file root: PASS.** Exactly six files, zero subdirectories
  (`find -mindepth 1 -type d | wc -l` = 0; code `write_root` refuses
  subdirectories and overwrite). Sizes: `command_log.txt` 282,
  `decoder_records.csv` 23599, `manifest.json` 2709, `paired_summary.csv` 1130,
  `report.md` 362, `summary.json` 728 — identical to operator return §2. All six
  mtimes fall in the single exit window `2026-09-11 00:33:39`; directory mtime
  `00:33:39.815529500 +0800`. No extra file. The root is the only D7-C root.
- **R04 — manifest matrix and call order: PASS.** `block_seeds`
  `2026091300..2026091315` (16, ascending), `f_values [1.0,1.2]`, four
  conditions in the frozen order, `l1_rows {1.0:49, 1.2:59}`,
  `l2_rows {1.0:43, 1.2:52}`, `graph_seeds {L1:2026090501, L2:2026090502}`.
  Recomputed from `decoder_records.csv`: the 128 `(f,seed,condition)` rows are
  exactly `for f in [1.0,1.2]: for seed ascending: L1_MARGINAL, L1_ORACLE_U2,
  L2_MARGINAL, L2_ORACLE_U1` (exact list equality; f=1.0 = calls 1–64,
  f=1.2 = calls 65–128).
- **R05 — accepted concentration semantics and prior formulas: PASS.**
  Manifest `estimator`, `lambda_star 137.3823795883264`, `decoder_floor 1e-15`,
  `damping_alpha 1.0`, `max_iter 90`, `n 64` all present and frozen. Code:
  total-concentration backoff (no per-cell pseudocount); four priors at
  `condition_prior_qn` (L487–511): L1 marginal `sum_u2 J[:,u2,b]`, L1 oracle
  `J[:,u2_true,b]` normalized over u1 with the uniform `1/32` zero-mass
  fallback, L2 marginal `sum_u1 J[u1,:,b]`, L2 oracle `J[u1_true,:,b]`
  normalized over u2; single transpose+`d5._floor_renorm(..., 1e-15)`
  application at the decoder boundary (`decoder_prior` L514–516), no other
  floor/clip/renorm. No decoder-returned belief enters any prior.

## 3. Scope-boundary evidence (R06)

- **R06 — no forbidden data or cross-layer flow: PASS.** The six root files
  contain no `CAL`/`VAL`/`parquet`/`raw`/`real`/`VOID`/`posterior`/`APP`
  tokens (word-boundary searches). The D7-C module reads only the accepted
  Model-F root through the D5 loader chain; VOID/G1/G0/D7-B paths appear only
  as name-based `PROTECTED_ROOTS` refusal guards (no reads). No CAL/VAL/parquet
  reader exists in the module. `final_beliefs` appears only in result parsing
  and scalar `_belief_diagnostics`; no cross-layer consumer: each of the 128
  calls derives its prior solely from `J` + block truth, and records show
  condition layer and `layer` column agree 128/128
  (`L1_*`→L1, `L2_*`→L2). No files under `results/` or
  `comparison_bench/outputs_comparison/` were modified after the run window
  (newest pre-existing mtime Sep 10 19:05, before authorization).

## 4. Record arithmetic (R07–R11) — recomputed vs stored

- **R07 — uniqueness/completeness: PASS.** 128 data rows + header (exact frozen
  header order); `call_idx` 1..128 unique and contiguous; 128 unique
  `(f,seed,condition)` tuples; duplicates 0, missing 0; no replacement cell.
- **R08 — pair identity: PASS.** For each of the 4 `(f,layer)` strata the 16
  marginal and 16 oracle rows pair bijectively by seed with identical
  `f/layer/rows/n`; only `condition` differs. By code construction
  (`execute_calls` L657–666) the pair shares `H_prefix = mothers[layer][:rows]`,
  the same `x_true`-derived syndrome, the same block and the same cold decoder
  configuration (`warm_beliefs=None`, `max_iter=90`, `damping_alpha=1.0`,
  `field=None`); only the prior differs (reviewed C08 asserts H/syndrome
  array-equality).
- **R09 — exact vs syndrome isolation: PASS.** Recomputed: exact true = 43/128;
  `syndrome_ok` true = 43/128; rows with `syndrome_ok != exact` = **0** (any
  such event would be isolated, never merged). `exact = array_equal(x_hat,
  x_true)` and `syndrome_ok = reported AND syndrome(H,x_hat)==s` are independent
  fields in code; no code path upgrades exact from syndrome.
- **R10 — iterations/status/symbol-errors arithmetic: PASS.** Every
  `exact=true` row has `symbol_errors=0` and `unsatisfied_checks=0` (and the
  converse holds: exact ⇔ symbol_errors==0 on all 128 rows; no
  `syndrome_ok=true` row has nonzero unsatisfied). Statuses: `ok` ×128; all
  `finite=true`. Iterations: min 2, max 90 (=`max_iter`); all 85 non-exact rows
  at 90; exact-row max 80. Recount maxima: `symbol_errors` 49,
  `unsatisfied_checks` 57. Per-stratum medians recomputed independently match
  `paired_summary.csv` exactly (90.0/9.0, 90.0/90.0, 90.0/3.5, 90.0/9.5).
- **R11 — nonfinite/crash accounting and fail-closed priority: PASS.**
  `crash_count` 0, `nonfinite_count` 0, `watchdog_timeouts` 0 in `summary.json`
  and consistent with records (no `crash:` status, no non-finite flag, no
  watchdog wall). `stop_terminal` is empty. Code enforces the fail-closed
  per-record priority watchdog > crash/nonfinite > resource (`execute_calls`
  L688–694) and blocks pre-first-call on an unavailable/nonpositive RSS probe
  (`run_bidirectional_oracle` L1271–1276).

**Per-stratum 2×2 (R12) — recomputed from `decoder_records.csv`; stored
`paired_summary.csv` values in parentheses:**

| f | layer | marg | orac | oracle_only | marginal_only | both | neither | sum |
|---|---|---|---|---|---|---|---|---|
| 1.0 | L1 | 0 | 10 | 10 (10) | 0 (0) | 0 (0) | 6 (6) | 16 |
| 1.0 | L2 | 0 | 1 | 1 (1) | 0 (0) | 0 (0) | 15 (15) | 16 |
| 1.2 | L1 | 3 | 16 | 13 (13) | 0 (0) | 3 (3) | 0 (0) | 16 |
| 1.2 | L2 | 0 | 13 | 13 (13) | 0 (0) | 0 (0) | 3 (3) | 16 |

All 18 stored paired fields per stratum plus `stratum_label` and both
condition names recompute exactly (zero mismatches over 4×20 values); paired
syndrome counts also match 0/0/3/0 and 10/1/13/13.

## 5. Strata and terminal recomputation (R12–R14)

- **R12: PASS** — every stratum's `oracle_only + marginal_only + both +
  neither` = 16 (64 pairs total); `paired_syndrome_ok_count` +
  disagreement sum per stratum to its 16 (0+10, 0+1, 3+13, 0+13).
- **R13 — stratum labels: PASS (recomputed with frozen first-match order and
  thresholds):**
  - f=1.0 L1: `STRONG_ORACLE_LIFT` (10≥4, 0≤1, 10≥4, zero crash/nonfinite).
  - f=1.0 L2: `NO_ORACLE_RECOVERY` (oracle 1≤1, marginal 0≤1).
  - f=1.2 L1: `STRONG_ORACLE_LIFT` (13≥4, 0≤1, 16≥4).
  - f=1.2 L2: `STRONG_ORACLE_LIFT` (13≥4, 0≤1, 13≥4).
  Stored labels in `summary.json`/`report.md`/`paired_summary.csv` agree 4/4.
- **R14 — run terminal: PASS.** Independent replay in frozen T1–T11 order:
  T1 not blocked; T2 no watchdog; T3 no crash/nonfinite; T4 stored wall
  32.631 s < 1500 s and RSS < limit; T5 128/128 records; **T6 =
  `D7_C_BIDIRECTIONAL_DEPENDENCE`** (f=1.2 is strong for both L1 and L2) — first
  applicable terminal. Stored terminal (summary/report/command_log/stdout)
  agrees.

## 6. Resources, labels, verifier (R15–R18)

- **R15 — walls: PASS.** Max per-call `wall_s` = 0.43867251399933593 s
  (≤120 s); stored scientific wall = 32.63112180600365 s (≤1500 s), equal to
  the sum of per-call walls; outer harness wall = 33.74325648800004 s
  (≤1800 s + 30 s grace) with `return_code 0` and `timeout_124 false` (exit
  consistency 0 vs 124 verified from the harness JSON). Bounds recorded in
  manifest.
- **R16 — RSS: PASS.** All 128 records store `rss_bytes = 105172992` (finite,
  positive, known), equal to `summary.peak_rss_bytes`; `< 2*1024**3`
  (2147483648) with huge margin. Stdlib `ru_maxrss`×1024 only; no psutil.
- **R17 — scalar payload and belief labels: PASS.** `decoder_records.csv`
  contains only the 21 frozen scalar fields; no vector/prior/syndrome/block
  payload exists in the root; `write_root` refuses non-scalars and unknown
  fields. Belief fields are scalars only (`belief_max_prob` ∈ [0.403, 1.0],
  `belief_mean_true_p` ∈ [0.090, 1.0], `belief_mean_entropy` ∈ [~0, 4.343]).
  Labels: `CHECK_UPDATED_CURRENT_BELIEF` ×128 (all `iterations` 2..90 > 0,
  `beliefs_conditioned=true` ×128); the only permitted tokens occur, and
  `posterior`/`APP` appear nowhere in the root.
- **R18 — sole verifier outcome: PASS as recorded, limitations stated.** The
  operator return records exactly one read-only invocation with literal output
  `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal':
  'D7_C_BIDIRECTIONAL_DEPENDENCE'}` and exit 0; it was not re-run by this
  reviewer (per prohibition). Code inspection confirms `verify_root` (L1119–1190)
  reads only the six files and cannot reach the decoder or Model-F. The
  disclosed limits are accurate: the verifier attests internal schema/identity/
  pair/counts/strata/terminal consistency only — it performs no independent
  `x_hat` replay and confers no scientific acceptance.

## 7. Authorization, prohibitions, immutability (R19–R20)

- **R19 — authorization false; no prohibited action: PASS.**
  `d7c_execution_authorized: false` after revocation; no attempt/result fields
  added. No R1d scientific root (`workspace/d6_graph_mother_r1d_*` absent), no
  G1/G2 root change, no `--phase` invocation evidence; the two
  `workspace/d6_r1d_tests_*` scratch directories are pre-existing (mtimes
  Sep 10 10:02/10:11, before the D7-C freeze) and unrelated. No CAL/VAL/raw
  output was read or written (see R06 mtime check). No new root exists besides
  the reviewed UUID root. Nothing is staged (`git diff --cached` empty).
- **R20 — immutability and no push: PASS.**
  - The six files were read at review start and re-hashed at review end;
    sha256 identical across passes and mtimes/sizes unchanged:

    ```text
    command_log.txt    6d9ec28610274f4b5f4752892d2f389067a7a0ea971ba061e40ba2ddf598a496
    decoder_records.csv 9bf26465f1d6de2868ae2c07f492a84cc72cb8da3266f37aa41ef1f3ca12e853
    manifest.json      ccc7289463e3519c6106f1dd2f225d26d76c37a95dd8fe816ce8dfd0e7bc4b40
    paired_summary.csv 9b7f962a3fe158886deb9a745b5e2a898b767bee66d78c587d1cf23eab1ecb40
    report.md          17a3c17dd5c61031ee969fedd6f973b5a6c8b253a81a4c2155b89e884891c421
    summary.json       fe7916e8c303824266c2ead2370751fc826a734af5c054779fa60db7b6eb3c5f
    ```

    The root was never written by this reviewer.
  - Protected metadata unchanged vs the accepted Pre-EXECUTE snapshots: D7-B R2
    root five files `1008 / 44743 / 80 / 449 / 111` bytes (E06 values), Model-F
    `model_f_input.npz 208467` and `model_f_input_summary.json 752` bytes;
    `results` dir mtime Apr 14 and `comparison_bench/outputs_comparison` dir
    mtime Sep 10 19:05 (E07 values).
  - No push: `origin/formal-ir-v72p1-addendum-clean` contains neither
    `b07b5441` nor `d3bd3c8b` (`git branch -r --contains` empty); branch remains
    98 commits ahead of origin. Both lifecycle commits are local-only.

## 8. Discrepancies and blocking assessment

**No blocking discrepancy found. No FAIL/BLOCKED condition applies.**

Non-blocking observations (no arithmetic, schema, scope or lifecycle impact):

1. Operator return §2 says `command_log.txt` line 1 equals the exact argv
   "(minus the outer `timeout` wrapper)"; the literal line is the child's
   `sys.argv`, so it also omits the `python` interpreter token. This is the
   frozen writer design (manifest `command` = `" ".join(sys.argv)`), the
   manifest and command_log agree exactly, and the full frozen argv including
   `timeout -k 30 1800 python` is independently preserved in
   `/tmp/d7c_exec_94c0ea15.json` and stated in operator return §1. Suggested
   future phrasing: "minus the `timeout -k 30 1800 python` launcher prefix".
2. `workspace/` is listed in `.gitignore` (line 20), so the conditional
   §9 solidification `git add` of the UUID root will need `-f` (the accepted
   D7-B root is likewise force-tracked). Process note for the main thread only;
   not a coherence defect of this execution.
3. `cycle_state.yaml` intentionally carries no UUID/attempt fields yet; per
   packet §9 these are added only after PASS. This is correct
   pre-solidification state, recorded here for completeness.

## 9. Verdict restatement

`D7_C_PRE_RESULT_REVIEW_PASS_R1` — the single D7-C invocation is internally
coherent: one authorized invocation with the exact frozen argv and UUID, one
fresh six-file root, 128/128 frozen calls in frozen order, 43 exact / 43
syndrome-ok with zero disagreement, four recomputed stratum labels
(`STRONG_ORACLE_LIFT`, `NO_ORACLE_RECOVERY`, `STRONG_ORACLE_LIFT`,
`STRONG_ORACLE_LIFT`), first-applicable terminal
`D7_C_BIDIRECTIONAL_DEPENDENCE`, walls and RSS within frozen budgets,
authorization consumed and revoked, protected roots immutable, no push.

This PASS means internal coherence only. It is not scientific acceptance, not
a result solidification, not route authority, and supports no FER, leakage,
reconciliation-efficiency, key-rate, CAL/real-data, qualification, promotion,
R1d, G1/G2 or general GF32/NB-LDPC claim.
