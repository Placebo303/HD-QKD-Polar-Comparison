# D7-E Operator Return R1 (bounded, no interpretation)

- UUID: `faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`
- Root: `workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`
- Root exists: True; files (sorted, with bytes + mtime_ns at inspection):
  - `command_log.txt` 290 1789126987886581800
  - `decoder_records.csv` 47144 1789126987876527800
  - `manifest.json` 3192 1789126987866398100
  - `report.md` 392 1789126987885581800
  - `stratum_summary.csv` 814 1789126987880046200
  - `summary.json` 982 1789126987883577200
  - `transfer_pairs.csv` 9070 1789126987878035700
- Subdirectories: 0 (`find -mindepth 1 -type d` empty)
- Exact file set matches frozen seven: `manifest.json`, `decoder_records.csv`, `transfer_pairs.csv`, `stratum_summary.csv`, `summary.json`, `report.md`, `command_log.txt`

## Invocation (STEP 3, exactly once)

- Exact argv: `timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`
- Cwd: repo root `/mnt/d/Code/HD-QKD_Polar_Comparison`
- Launch: detached via `setsid nohup ... > /tmp/d7e_exec_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c.log 2>&1`; outer PID 703387 (parent 139339 after detach), inner Python PID 703389 (per manifest `pid:703389`)
- Start local: 2026-09-11 19:41:59 CST; start UTC: 2026-09-11 11:41:59 UTC
- Manifest inner start_utc: `2026-09-11T11:42:02Z`; end_utc: `2026-09-11T11:43:07Z` (65 s inner span)
- Process observed running at 19:42:26, 19:42:42, 19:42:57 CST; observed done at 19:43:12 CST poll (root present, log 119 bytes/1 line); final poll timestamp 19:43:28 CST
- Outer wall: ~73 s from launch to first done-poll (19:41:59→19:43:12), ≤89 s to 19:43:28; far below 1800+30
- Stdout (full, 1 line, 119 bytes): `terminal=D7_E_L2_TO_L1_TRANSFER_LIFT out=workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c`
- Stderr: empty (log file contains only the stdout line; `wc -c 119`, `wc -l 1`)
- Exit-124 flag: False (wall <<1800; no timeout message; root completed)
- Exit code: numeric wait unavailable after setsid detach (`wait: not a child`, exit 127 on wait attempt); observed completion (192/192 rows, terminal line, root present, no timeout) consistent with 0; no retry was performed for any outcome
- Invocation count: 1 (no retry/rerun/resume; no second UUID; no replacement root)

## Authorization lifecycle

- Auth commit: `b148c9d4f547485db668e63655551cbd632314ed` (`chore(d7-e): authorize one frozen cross-layer discriminator invocation`; staged exactly authorization record + `cycle_state.yaml`)
- Revoke commit: `34085c159d87bcaf9b46f2dad5961688940223c5` (`chore(d7-e): consume and revoke one-shot execution authorization`; one-line `true->false`)
- Post-revoke flags: all false (`plan_accepted`, `implementation_authorized`, `d7e_execution_authorized`, `decoder_executed`, `result_created`, `formal_execution_authorized`, `synthetic_execution_authorized`, `real_execution_authorized`, `scientific_promotion`, `g1_authorized`, `g2_authorized`, `d7e_result_accepted`); `ALL_FALSE=True`
- No push performed.

## Frozen scalar arithmetic (recorded, not interpreted)

- Scheduled: 192 (`slots_scheduled:192`); slot indices numeric 1..192 complete (`FULL_1_192=True`); unique (`SLOT_UNIQUE=True`); missing 0; duplicate 0
- Invoked/completed: `calls_attempted:192`, `calls_completed:192`, `calls_remaining:0`
- Mandatory: `mandatory_completed:128` (roles SOURCE 64 + CONTROL 64)
- Transfer: `transfer_invoked:64`, `transfer_blocked:0`
- Retry/resume: `retries:0`, `reruns:0`, `resumes:0` (manifest + summary both 0)
- Directions: L1_TO_L2 96, L2_TO_L1 96; f=1.0 96, f=1.2 96; roles SOURCE/CONTROL/TRANSFER 64/64/64
- Per-stratum eligibility (all `COVERAGE_OK`, blocked 0):
  - stratum 1 f=1.0 L1_TO_L2: eligible 16, blocked 0, label `NO_TRANSFER_RECOVERY`
  - stratum 2 f=1.0 L2_TO_L1: eligible 16, blocked 0, label `NO_TRANSFER_RECOVERY`
  - stratum 3 f=1.2 L1_TO_L2: eligible 16, blocked 0, label `AMBIGUOUS_TRANSFER_EFFECT`
  - stratum 4 f=1.2 L2_TO_L1: eligible 16, blocked 0, label `STRONG_TRANSFER_LIFT`
- Six-label counts: `STRONG_TRANSFER_LIFT:1`, `TRANSFER_REGRESSION:0`, `NO_TRANSFER_RECOVERY:2`, `CONTROL_ALREADY_RECOVERS:0`, `AMBIGUOUS_TRANSFER_EFFECT:1`, empty:0
- Stored terminal: `D7_E_L2_TO_L1_TRANSFER_LIFT`; `stop_terminal:""`; priority position 9 of frozen 12 (`D7_E_PRE_EXECUTION_BLOCKED`, `D7_E_WATCHDOG_TIMEOUT_VOID`, `D7_E_NONFINITE_OR_CRASH_BLOCKED`, `D7_E_RESOURCE_OVERRUN`, `D7_E_INCOMPLETE_CORE_CALL_MATRIX`, `D7_E_PROVENANCE_COVERAGE_BLOCKED`, `D7_E_BIDIRECTIONAL_TRANSFER_LIFT`, `D7_E_L1_TO_L2_TRANSFER_LIFT`, `D7_E_L2_TO_L1_TRANSFER_LIFT`, `D7_E_TRANSFER_REGRESSION`, `D7_E_NO_USEFUL_TRANSFER_RECOVERY`, `D7_E_MIXED_TRANSFER_DIAGNOSTIC`); manifest `terminal_priority` matches frozen order
- Exact/syndrome/crash/nonfinite (kept separate columns): `exact True:16 False:176`; `syndrome_ok True:16 False:176`; `status converged_exact:16 converged_no_syndrome:176`; `crash_count:0`; `nonfinite_count:0`; `finite True:192`
- Stratum exact detail: s1 control 0/transfer 0/neither 16; s2 0/0/16; s3 control 0/transfer 3/transfer-only 3/neither 13; s4 control 3/transfer 7/transfer-only 4/both 3/neither 9 (syndrome counts mirror exact counts per stratum)
- Walls: stored `stored_wall_s:64.95356635501957` (≤1500); per-call max `0.43789475300582126` (<120), min `0.012907689000712708`, sum equals stored; outer ~73–89 s (<1800+30); `watchdog_timeouts:0`
- RSS: per-call `rss_bytes` min=max=`132390912`, all `0<rss<2147483648 True`; peak `peak_rss_bytes:132390912` (<2GiB); limit `rss_limit_bytes:2147483648`; `VmHWM`-sourced per frozen A2 path
- Provenance: `belief_provenance CHECK_UPDATED:192`; `PRIOR_ONLY:0`; `WARM_START_UNSPECIFIED:0`; `transfer_eligible True:64` (TRANSFER rows), empty:128 (SOURCE/CONTROL rows); `belief_shape_ok True:192`; `beliefs_conditioned True:192`; `current_belief_label CHECK_UPDATED_CURRENT_BELIEF:192`
- Writer/reader consistency (observed, not judged): `manifest.authorization_consumed:true`; `manifest.uuid` matches directory UUID; `manifest.model_f_root` is accepted root; `manifest.model_f_files` lists `model_f_input.npz 208467` + `model_f_input_summary.json 752`; `command_log.txt` holds exact command + terminal + calls_completed + stored wall; `report.md` holds terminal + counts + four stratum lines

## Forbidden-payload scan (recorded)

- `decoder_records.csv` fields (26): `slot_idx,f,seed,direction,role,condition,layer,rows,n,exact,syndrome_ok,iterations,status,finite,symbol_errors,unsatisfied_checks,wall_s,rss_bytes,belief_max_prob,belief_mean_true_p,belief_mean_entropy,beliefs_conditioned,current_belief_label,belief_provenance,belief_shape_ok,transfer_eligible`
- Substring hits `syndrome_ok,symbol_errors,beliefs_conditioned` are scalar booleans/counts (`syndrome_ok True/False`, `symbol_errors` counts, `beliefs_conditioned True/False`); no vector/belief-array/prior-matrix/symbol-vector/syndrome-vector/block-vector/digest field present
- All values scalar: `NONSCALAR_VALUES=0` (no value starts with `[` or `{`)
- `transfer_pairs.csv` fields (24) are pair scalars + `source_exact`/`source_provenance` context only; no belief/prior/syndrome payload
- No forbidden vector/belief/prior/symbol/syndrome payload persisted (scalar-only observation)

## No scientific interpretation

- This return records counts/labels/terminal/resources only. It makes no FER, leakage, key-rate, qualification, promotion, G2-permission, or deployment claim. Pre-RESULT review is still required before any acceptance.

(End of operator return — uncommitted)
