# D7-C operator return R1 (literal facts; NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED)

## Status

`NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED`

This document records literal facts only. It accepts nothing and concludes
nothing. Independent Pre-RESULT R1 (R01–R20) is mandatory before any result
root/return/summary is committed as a result.

## 1. Execution provenance and exact process evidence

- Sole D7-C UUID: `94c0ea15-a786-4cb8-a991-6fec521cccae` (frozen at
  authorization commit `b07b5441`; this execution generated no UUID and used
  no other root).
- Exact child argv (preserved exactly; no added args, pipes, tee, redirection,
  PYTHONPATH, alternate Python, alternate estimator or replacement root):

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae
```

- Parent timing/capture harness `/tmp/d7c_exec_harness.py` (packet-allowed;
  spawns the child with argv/env exactly as above; only captures I/O/timing;
  PATH prepended with `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin`,
  ambient `PYTHONPATH` absent and removed from the child env, cwd
  `/mnt/d/Code/HD-QKD_Polar_Comparison`; no other env override).
- Launch: detached `setsid nohup` exactly once, launch local
  `2026-09-11 00:33:06 CST`, UTC `2026-09-10 16:33:06 UTC`; harness PID
  `258562`; child (`timeout`) PID `258564`; decoder process PID `258565`
  (manifest `pid`).
- `command_invocations: 1` (one scientific invocation; no relaunch/retry/
  rerun/resume under any outcome).
- Timing (harness-captured): start local `2026-09-11 00:33:06 CST`, UTC
  `2026-09-10 16:33:06 UTC`; end local `2026-09-11 00:33:39 CST`, UTC
  `2026-09-10 16:33:39 UTC`; outer wall `33.74325648800004` s.
- Process exit code: `0`; timeout-124 flag: `false` (not the watchdog);
  `root_exists_at_exit: true` (existence check only).
- Literal stdout (complete):
  `terminal=D7_C_BIDIRECTIONAL_DEPENDENCE out=workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae`
- Literal stderr (complete): empty.
- `scientific_attempt_consumed: true` — 128 decoder records are stored
  (`call_idx` 1..128, non-empty `decoder_records.csv`; see §4). Basis: stored
  decoder attempts evidenced, not inference.
- Authorization lifecycle: authorize `b07b5441` (record + state false→true) →
  exactly one invocation (exit 0, outer wall 33.743 s) → revoke
  `d3bd3c8b94c6ab7f9baf66b696b1e172214b98d3` (state true→false; diff exactly
  one line; committed alone before any root content was read). Current
  `d7c_execution_authorized: false`. Both commits local-only, no push; no
  attempt/result fields added to `cycle_state.yaml`.

## 2. Root inventory (new D7-C UUID root only; immutable post-exit)

- Root: `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae/`
  (fresh; ABSENT immediately before launch, confirmed by `ls -d` rc 2 and by
  the harness pre-launch assertion; created by the single invocation; directory
  mtime `2026-09-11 00:33:39.815529500 +0800`).
- Exactly six files, zero subdirectories (`find -mindepth 1 -type d | wc -l`
  → `0`):

| file | size (bytes) |
|---|---|
| `command_log.txt` | 282 |
| `decoder_records.csv` | 23599 |
| `manifest.json` | 2709 |
| `paired_summary.csv` | 1130 |
| `report.md` | 362 |
| `summary.json` | 728 |

- All six files have mtime `2026-09-11 00:33` (single exit window). No other
  `workspace/d7_c_bidirectional_oracle_*` root exists. Immutable post-exit:
  inspected read-only; sizes/mtimes identical before/after verify (§11).
- `command_log.txt` literal line 1 equals the manifest `command` string and
  the exact argv above (minus the outer `timeout` wrapper).

## 3. Frozen manifest identity

`manifest.json` (read literally):

- `change: v72p2d7-gf32-bidirectional-oracle`; `contract: R1+A1`;
  `authorization_consumed: true`.
- Estimator: `v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate(counts_ab, p_b)`;
  `lambda_star: 137.3823795883264`; `damping_alpha: 1.0`; `decoder_floor: 1e-15`;
  `decoder: "v35.decode_row_layered_fftqspa via d5.bind_historical_decoder()"`;
  `max_iter: 90`; `n: 64`.
- Model-F identity: root `workspace/v72p2d5_model_f_input/20260907_r1`;
  files listed as `model_f_input.npz` 208467 bytes and
  `model_f_input_summary.json` 752 bytes (names/sizes as recorded in the
  manifest; Model-F content was read only by the single scientific command).
- Seeds: `block_seeds` `2026091300..2026091315` (16 seeds); `graph_seeds`
  `L1: 2026090501`, `L2: 2026090502`; `f_values: [1.0, 1.2]`;
  `l1_rows: {1.0: 49, 1.2: 59}`; `l2_rows: {1.0: 43, 1.2: 52}`.
- Conditions: `[L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1]`.
- Call ordering (`call_order`): `for f in [1.0, 1.2]: for seed in
  2026091300..2026091315: L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL,
  L2_ORACLE_U1`. Recomputed from `decoder_records.csv`: block order holds for
  all 32 `(f, seed)` blocks; `f=1.0` occupies calls 1–64 and `f=1.2` calls
  65–128.
- Budgets recorded: `max_calls: 128`, `per_call_watchdog_s: 120.0`,
  `stored_wall_limit_s: 1500.0`, `outer_watchdog_s: 1800.0`,
  `outer_grace_s: 30.0`, `rss_limit_bytes: 2147483648`;
  `retries/resumes/reruns: 0`; `start_utc: 2026-09-10T16:33:07Z`.
- `six_files` list and `out_root_name` match §2 exactly.
- `terminal_priority` is the frozen T1–T11 order:
  `D7_C_PRE_EXECUTION_BLOCKED`, `D7_C_WATCHDOG_TIMEOUT_VOID`,
  `D7_C_NONFINITE_OR_CRASH_BLOCKED`, `D7_C_RESOURCE_OVERRUN`,
  `D7_C_INCOMPLETE_CALL_MATRIX`, `D7_C_BIDIRECTIONAL_DEPENDENCE`,
  `D7_C_L1_DEPENDS_ON_U2`, `D7_C_L2_DEPENDS_ON_U1`,
  `D7_C_MARGINAL_REGION_EXISTS`, `D7_C_ORACLE_NO_USEFUL_RECOVERY`,
  `D7_C_MIXED_DIAGNOSTIC`.

## 4. Scheduled / invoked / missing / duplicate arithmetic

- Scheduled: `128` = 2 f × 16 seeds × 4 conditions (manifest `max_calls` 128).
- Invoked/completed: `128` (`summary.calls_attempted` 128,
  `calls_completed` 128, `calls_remaining` 0).
- `decoder_records.csv`: 128 data rows + header; `call_idx` contiguous
  `1..128`; 128 unique `(f, seed, condition)` tuples.
- Missing: `0`; duplicate: `0`.
- `retries: 0`, `resumes: 0`, `reruns: 0` (manifest and summary agree).
- `stop_terminal: ""` — no early stop; all 128 scheduled calls present.

## 5. Per `(f, layer)` marginal/oracle paired 2×2 (as stored; recomputed, agrees)

`paired_summary.csv` stores per stratum: marginal/oracle exact counts,
`oracle_only`, `marginal_only`, `both`, `neither`, paired syndrome counts,
nonfinite/crash counts and iteration/wall summaries. Stored values
(recomputed from `decoder_records.csv` independently; all agree):

| f | layer | marginal cond | oracle cond | marginal_exact | oracle_exact | oracle_only | marginal_only | both | neither | pairs sum | paired_syndrome_ok | paired_syndrome_disagreement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | L1 | L1_MARGINAL | L1_ORACLE_U2 | 0 | 10 | 10 | 0 | 0 | 6 | 16 | 0 | 10 |
| 1.0 | L2 | L2_MARGINAL | L2_ORACLE_U1 | 0 | 1 | 1 | 0 | 0 | 15 | 16 | 0 | 1 |
| 1.2 | L1 | L1_MARGINAL | L1_ORACLE_U2 | 3 | 16 | 13 | 0 | 3 | 0 | 16 | 3 | 13 |
| 1.2 | L2 | L2_MARGINAL | L2_ORACLE_U1 | 0 | 13 | 13 | 0 | 0 | 3 | 16 | 0 | 13 |

- `pairs sum` = `oracle_only + marginal_only + both + neither` = 16 per
  stratum (64 pairs total). No `marginal_only` pair exists in any stratum.
- Per-stratum nonfinite/crash counts: all `0/0`.
- Stored iteration medians (marginal/oracle): 90.0/9.0, 90.0/90.0, 90.0/3.5,
  90.0/9.5 for the four rows above; recomputed medians agree.
- Stored per-stratum wall medians (marginal/oracle) and maxima are in
  `paired_summary.csv`; recomputed values agree (max over all invoked calls
  `0.43867251399933593` s; see §8).

## 6. Exact / syndrome / iterations / crash / nonfinite / status summaries

- `exact: True` rows: `43/128`; `syndrome_ok: True` rows: `43/128`.
  In this data `exact` and `syndrome_ok` coincide (0 exact-without-syndrome,
  0 syndrome-without-exact). Exact is never upgraded from syndrome; the two
  columns are stored separately.
- All exact rows have `symbol_errors = 0` and `unsatisfied_checks = 0`.
  Max over all rows: `symbol_errors` 49, `unsatisfied_checks` 57.
- Iterations: min `2` (exact), max `90` (= `max_iter`); all 85 non-exact rows
  are at `90`; max iterations among exact rows `80`.
- `status` counter: `ok` 128. `finite: True` 128. `crash_count: 0`,
  `nonfinite_count: 0`, `watchdog_timeouts: 0` (summary) — consistent with
  records (no crash strings, no non-finite flags, no watchdog rows).
- Per-condition exact totals (recomputed): L1_MARGINAL 3, L1_ORACLE_U2 26,
  L2_MARGINAL 0, L2_ORACLE_U1 14. Total 43.

## 7. Strata and stored run terminal

- Four `(f, layer)` strata labels (stored in `summary.json`, repeated in
  `report.md`):
  - f=1.0 L1: `STRONG_ORACLE_LIFT` (marginal 0/16, oracle 10/16)
  - f=1.0 L2: `NO_ORACLE_RECOVERY` (marginal 0/16, oracle 1/16)
  - f=1.2 L1: `STRONG_ORACLE_LIFT` (marginal 3/16, oracle 16/16)
  - f=1.2 L2: `STRONG_ORACLE_LIFT` (marginal 0/16, oracle 13/16)
- Stored run terminal: `D7_C_BIDIRECTIONAL_DEPENDENCE`
  (`summary.json`, `report.md`, `command_log.txt` and stdout agree);
  `stop_terminal` empty (no early stop).
- Terminal priority T1–T11 is recorded in the manifest (§3). This document
  does not recompute the terminal verdict; independent R14 must replay it.

## 8. Call / stored / outer wall and RSS

- Per-call watchdog: `120.0` s; max stored per-call `wall_s`
  `0.43867251399933593` s (no per-call watchdog event).
- Stored scientific wall: `32.63112180600365` s (limit `1500.0`).
- Outer wall (harness): `33.74325648800004` s (outer GNU timeout `1800` s +
  `30` s grace); exit `0`, not 124.
- RSS: all 128 records store `rss_bytes = 105172992` (constant; equals
  `summary.peak_rss_bytes = 105172992` ≈ 100.30 MiB) < `rss_limit_bytes
  2147483648`. Frozen measurement is the stdlib current-process reading
  (`resource.getrusage(RUSAGE_SELF).ru_maxrss` with explicit KiB→bytes rule,
  as frozen; no psutil). Limit never evaluated against an unknown value.

## 9. Belief provenance and no-cross-layer evidence (as stored)

- `current_belief_label`: single value `CHECK_UPDATED_CURRENT_BELIEF` across
  all 128 records (the only labels permitted are `PRIOR_ONLY_CURRENT_BELIEF` /
  `CHECK_UPDATED_CURRENT_BELIEF`; `PRIOR_ONLY_CURRENT_BELIEF` does not occur).
- `beliefs_conditioned: True` for all 128 records; the only belief-derived
  stored fields are scalars (`belief_max_prob`, `belief_mean_true_p`,
  `belief_mean_entropy`); no belief/symbol/prior/syndrome/block vector is
  persisted.
- No returned belief crossed layers (stored evidence): condition layer and
  `layer` column agree 128/128 (`L1_*` records are L1, `L2_*` records are L2);
  every `(f, seed)` block is ordered same-layer `L1_MARGINAL, L1_ORACLE_U2,
  L2_MARGINAL, L2_ORACLE_U1`; `paired_summary.csv` pairs only same-layer
  conditions (`L1_MARGINAL` with `L1_ORACLE_U2`; `L2_MARGINAL` with
  `L2_ORACLE_U1`). The verifier (§11) additionally rechecks pair identity and
  stratum schema; code-level cross-layer exclusion is a frozen-contract
  property of the single executed command, not independently re-proven here.

## 10. Boundary compliance

- Exactly one scientific invocation; exactly one read-only verifier
  invocation (§11). No retry/rerun/resume/relaunch/UUID replacement.
- Result root not modified or filled by this task; read-only inspection only.
- No R1d, no `--phase`, no formal G1/G2, no CAL/VAL/parquet/raw/real/VOID
  content; no cross-layer APP; no decoder or Model-F load in the verifier.
- No edits to code/tests/OpenSpec/frozen packets; no broad staging, no push;
  pre-existing unrelated dirty/CRLF paths preserved untouched.
- Model-F content was read only by the single authorized scientific command;
  every other Model-F observation is metadata stored in the D7-C manifest.

## 11. Verify (§7)

- One read-only non-decoder invocation (the sole verifier invocation):

```bash
PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" python scripts/v72p2d7_gf32_bidirectional_oracle.py --verify workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae
```

- Literal output (complete):
  `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal': 'D7_C_BIDIRECTIONAL_DEPENDENCE'}`
- Exit: `0`. Root sizes/mtimes unchanged after verify (six files, zero
  subdirectories; §2 values identical before/after; no bytes written).
- Verifier limits (disclosed): the verifier recomputes schema, record
  identity/count, pair/stratum structure and terminal from the six stored
  files; it does not call the decoder, does not load Model-F, does not attest
  scientific correctness beyond internal consistency, and does not convert the
  stored terminal into an acceptance.

## 12. Forbidden claims (explicitly NOT claimed)

- No FER, leakage, key-rate, qualification, promotion, acceptance, or general
  algorithm-success claim.
- The stored terminal `D7_C_BIDIRECTIONAL_DEPENDENCE` and the four stratum
  labels are stored run diagnostics only; this document does not interpret
  them and they are not an accepted scientific conclusion.
- No decoder certification or performance conclusion of any kind; independent
  Pre-RESULT R1 (R01–R20) must recompute from the six files before any
  acceptance.

(End of file — uncommitted; awaits independent Pre-RESULT R1 review.)
