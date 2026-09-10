# D7-B operator return R1 (literal facts; NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED)

## Status

`NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED`

This document records literal facts only. It accepts nothing.

## 1. Command / exit / walls / stdio (literal)

- Exact instantiated command (invocation count = 1, never repeated):

```bash
PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c
```

- UUID: `0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c` (the single UUID from the
  authorization record; no second UUID generated).
- CWD: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean`.
- Start local: `2026-09-10 19:16:54 CST`; start UTC: `2026-09-10 11:16:54 UTC`.
- End local: `2026-09-10 19:16:54 CST`; end UTC: `2026-09-10 11:16:54 UTC`.
- Outer wall: `0` s (process returned in under one second).
- Process exit code: `3`.
- 124-timeout flag: NO (exit 3 is the frozen refusal path, not the watchdog).
- Literal stdout (complete):

```
D7-B refused: ImportError('attempted relative import with no known parent package')
```

- Literal stderr (complete): empty.
- Stdout/stderr were captured by an outer file wrapper (`/tmp/d7b_stdout.txt`,
  `/tmp/d7b_stderr.txt`); no tee/redirection/pipeline was added to the
  scientific command text.

## 2. Failure point (read-only static attribution; no re-execution performed)

- The runner reached `run_easy_regime` (authorization gate passed:
  `d7b_execution_authorized` was true) and entered `bind_historical_decoder()`
  with `decode_fn=None`.
- `bind_historical_decoder()` first tries
  `from comparison_bench.formal_ir import v35_algorithm_development`; the
  `comparison_bench` package is not installed in the execution venv, so the
  frozen `ModuleNotFoundError` fallback file-loads
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
  via `spec_from_file_location` with no parent package; that production module
  contains explicit relative imports, raising
  `ImportError: attempted relative import with no known parent package`.
- Sequence proof from frozen code order (`run_easy_regime`):
  `_refuse_protected` → `_require_authorized` → overwrite check (root absent,
  passed) → `bind_historical_decoder()` raised → `_EXECUTION_CONSUMED = True`
  never reached → `out.mkdir(...)` never reached.
- Consequence: zero decoder calls attempted, zero cells executed, zero files
  written. `command_invocations: 1`;
  `scientific_attempt_consumed: NOT_VERIFIABLE` (logs prove the bind attempt
  failed before any decoder call; `false` is never used as a retry basis —
  no retry is permitted under any outcome).

## 3. Root inventory

- Target root `workspace/d7_b_easy_regime_0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`:
  ABSENT (verified `test -e` and `ls -d workspace/d7_b_easy_regime_*` → no
  such file). No files created, none modified, none deleted.
- No-subdirectory result: not applicable (no root). No partial root exists to
  retain; absence is the immutable end state.
- No other `workspace/d7_b_easy_regime_*` root exists (exactly zero D7-B
  result roots before and after).

## 4. Manifest / parameters / counts / aggregates

- No `manifest.json` exists (no root). Frozen parameters were never read from
  a manifest; for the record, invocation parameters were exactly the frozen
  ones (script path, `--out-root <fresh uuid root>`, no `--phase`, no R1d).
- Scheduled/invoked/not-needed/budget-not-reached: no cells scheduled at run
  time (run aborted before cell loop). All counts: none observed.
- Stored terminal: none (no `summary.json`, no `report.md`, no
  `command_log.txt`, no `decoder_records.csv`).
- Per-tier/per-prior/per-seed outcomes: none (zero rows).
- Tractable posterior/MAP errors: none observed. Crash/nonfinite/status
  counts: none observed (no decoder records exist).
- Max per-call wall / stored run wall / RSS known/max: none observed. RSS
  gate never evaluated at run time (run ended during decoder bind).
- `decoder_executed`: false (no evidence of any decoder call).
  `result_created`: false (no root).

## 5. Authorization lifecycle (lifecycle facts)

- Authorize commit: `ce52ac5` (`chore(d7-b): authorize one frozen easy-regime
  invocation`; staged exactly authorization record + cycle_state flip
  false→true). Target re-verified absent after commit.
- Single invocation: exit 3, outer wall 0 s (see §1).
- Revoke commit: `9e41e0d` (`chore(d7-b): consume and revoke one-shot
  execution authorization`; staged exactly cycle_state flip true→false,
  committed alone before this return was written).
- Current: `d7b_execution_authorized: false`. No push performed for either
  commit (local only; verified by performing no push).

## 6. Boundary compliance

- No R1d, no `--phase`, no G1/G2 invoked or referenced at run time.
- No Model-F/CAL/VAL/real/raw/VOID/formal content read (only metadata-only
  directory listings and the frozen D7-B code/packet/prereg reads required by
  the gates).
- No edits to v35/D5/D7-A/D7-B code, tests, OpenSpec, or frozen packets.
- No result-root mutation (no root exists). Exactly one scientific command and
  zero verifier commands so far (verifier addressed in §7).
- No broad git operations, no cleanup, no push. Pre-existing dirty/CRLF paths
  outside scope preserved untouched.

## 7. Verifier (§7 outcome)

- `VERIFY_NOT_RUN`: the target root is absent (exit-3 refusal before root
  creation), so the accepted verifier has no invocable structure. The
  verifier command is not run on any other path.

## 8. Forbidden claims (explicitly NOT claimed)

- No FER, leakage, key-rate, qualification, or channel-recovery claim.
- No easy-regime confirmation/partial/alert terminal (no terminal stored).
- No decoder certification or performance conclusion of any kind.
- The exit-3 refusal is an environment/bind failure of the single authorized
  invocation, not a scientific observation.

(End of file — uncommitted; awaits independent Pre-RESULT review.)
