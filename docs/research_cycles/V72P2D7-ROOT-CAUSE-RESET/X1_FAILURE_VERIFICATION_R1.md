# X1 failure verification R1 — independent re-check

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Reviewer context: independent verification assigned by the main thread on
  2026-09-13; separate from the X1 execution operator. Read-only re-check of
  the retained attempt transcripts, the operator return, and the code paths;
  the probe was not re-executed, nothing was repaired or cleaned.
- Artifact under review: `X1_OPERATOR_RETURN_R1.md` (BLOCKED) for the one
  authorized X1 process start under
  `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_A1_TASK_PACKET.md`
  (master packet §7 X1, §8, §9).

## 1. Verdict

**`X1_FAILURE_VERIFIED`** — the consumed X1 attempt failed the frozen success
contract exactly as reported, the recorded evidence is internally consistent,
and no write, retry, or later-phase activity occurred.

## 2. Evidence re-checked

- Command (WSL frozen form, `meta.txt` line 3):
  `timeout -k 30 120 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --historical-provenance-probe`
- Exit code 2 (`meta.txt` `EXIT_CODE=2`); wall `2142 ms`
  (`WALL_MS=2142`); `TIMEOUT_DISPOSITION=COMPLETED_BEFORE_OUTER_WATCHDOG`.
- stdout (md5 `f41e519d74f8de1dff7562ed8c26ff0c`, 299 bytes), verbatim:

  ```json
  {"accepted_check_updated": false, "belief_shape_ok": true, "beliefs_finite": true, "decoder_calls": 1, "iterations": 0, "mode": "historical_provenance_probe", "ok": false, "provenance": "PRIOR_ONLY", "resolved_decoder_identity": "historical_g0_decoder", "resolved_is_historical": true, "writes": 0}
  ```

- stderr (md5 `8df6c7f91a1ba9d3fd9ee52ad291de08`, 27 bytes):
  `X1_PROVENANCE_PROBE_FAILED`.
- meta md5 `a95c7768c995634af48681025b78871c`; all three hashes were
  re-computed from the retained transcripts in
  `/tmp/opencode/x1_r1_attempt_20260913/` and matched.
- Contract evaluation: provenance `PRIOR_ONLY` != `CHECK_UPDATED`,
  `iterations: 0` < 1, exit 2 != 0, `accepted_check_updated: false` -> X1
  failure terminal (`X1_PROVENANCE_PROBE_FAILED`). Attempt shape was correct:
  `decoder_calls: 1`, `writes: 0`, beliefs finite and shape-valid.
- No writes: `status_before.txt` and `status_after.txt` identical (both md5
  `df682a08b9d224e9999ef7f1b23033c5`), `status_diff.txt` empty (0 bytes),
  `repo_files_touched.txt` empty (0 bytes).
- X2/X3/X4 frozen roots absent after the attempt (re-verified at review):
  `workspace/d7_r1_multigraph_20260913_r1`,
  `workspace/d7_r1_reference_ladder_20260913_r1`,
  `workspace/v72p2d5_g2/20260906_r1` — all `ABSENT`.
- Flag restored false: `x1_consistency_probe_authorized: false`; X1
  authorization consumed; X2–X4 unused; no retry, repair, or cleanup.
- Branch `formal-ir-v72p1-addendum-clean`; HEAD `278fdf07` unchanged.

## 3. Root cause (verified against code)

The pre-fix `_probe_fixture()`
(`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`)
used a zero syndrome with a uniform prior. The historical row-layered decoder
early-returns at iteration 0 whenever `H @ argmax(beliefs) == syndrome`
(`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:835-854`);
with `argmax(uniform prior) = 0` and `syndrome = 0` this always held, so the
decoder returned `iterations=0` + provenance `PRIOR_ONLY`, which the frozen
X1 contract (`CHECK_UPDATED`, `iterations >= 1`, exit 0) can never accept.
The decoder is correct; the fixture made the contract unsatisfiable by
construction.

## 4. Inconsistencies found (for the main thread)

1. Stale `cycle_state.yaml` markers relative to the operator return:
   `state`/`terminal` still `X1_AUTHORIZED_AWAITING_OPERATOR_EXECUTION`,
   `x1_authorization_consumed: false`,
   `x1_x4_authorization_consumed: false`, `next_gate: X1_OPERATOR_EXECUTION`.
   Corrected additively in the same fix step.
2. Authorization-record filename ambiguity: the grant note
   `X1_X4_AUTHORIZATION_A1.md` vs the X1 pre-EXECUTE record
   `A1_X1_X4_AUTHORIZATION_RECORD_R1.md`. Both are retained; the pre-EXECUTE
   record is referenced by `a1_preexecute_record`.
