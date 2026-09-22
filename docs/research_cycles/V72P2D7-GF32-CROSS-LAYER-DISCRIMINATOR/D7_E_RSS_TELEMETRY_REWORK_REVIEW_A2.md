# D7-E RSS telemetry rework — independent implementation review (A2, T5 only)

- Authority: `.workbuddy/tasks/D7_E_RSS_TELEMETRY_REWORK_VENV_A2_TASK_PACKET.md` §9 (T5 only).
- Reviewer context: separate from the implementer. Review-only. No commits, no edits beyond this file, no live-kernel evidence, no real artifact reads.
- Branch: `formal-ir-v72p1-addendum-clean`.
- HEAD verified: `9e095382b357c36f86c1936e45bc4f63d8d14943` (prefix `9e09538`, implementation commit).
- Required history present: `08590fba`, `031deee7`, `d6e40dd` (all resolve as commits).
- Frozen inputs read: packet §1 rule + T2/T3; A2 delta (`design.md` / `tasks.md` A2-01…A2-08 / `spec.md`) and `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md`; diff `becf60f..9e09538`; new `test_a2_*` tests.
- Packet §2 honored: zero real decoder calls, zero phase invocations, no result root created by this review, no protected-content reads. All probes below use injected status text/readers and fake decoders only.

## Scope (committed diff only)

- `git diff --name-only becf60f..9e09538` returns exactly two paths:
  - `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`
  - `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py`
- `git diff --name-status becf60f..9e09538` shows both as `M`, no adds/deletes/renames.
- Both paths are in the packet §3 allowed list. No other committed path changes in this range.
- Note: the working tree is dirty with unrelated modifications outside this range. This review covers only the committed `becf60f..9e09538` diff; unscoped worktree content was not used as evidence.
- Hunk structure: exactly one hunk in the module (`@@ -331,31 +331,89 @@`, RSS block only) and exactly one append hunk in the test file (`@@ -1538,3 +1538,246 @@`, A2 tests only). No other hunks.

## 1. Parser strictness — PASS

Source inspected: `parse_vmhwm_rss_bytes` accepts exactly one ASCII line starting with `VmHWM:`, requires ≥1 space/tab after the colon, ASCII digits, and exact suffix ` kB`; rejects length >18 digits, non-positive values, and any non-text input.

Independent probes run by this reviewer with `.venv/bin/python` (injected text only, never the live kernel):

- Valid: `VmHWM: 1 kB` → `1024`; tab+spaces variant → `value*1024`; leading zeros `007` → `7*1024`; embedded in larger status text → correct.
- Missing/empty/non-text: empty, `None`, bytes, int, list, missing-field status, prefixed field name → all `None`.
- Case: lowercase/mixed/uppercase field names → all `None`.
- Duplicate: identical, different-value, and valid+malformed pairs → all `None`.
- Units: `MB/KB/kb/K/k/B/bytes/kBB/KiB`, missing unit, missing space, tab or double-space before unit, trailing space, `CRLF` → all `None`.
- Malformed/signed/zero: decimal, exponent, `+`/`-`, zero and all-zero strings (including 19-char all-zero), alphabetic, empty value, missing colon, comma, hex, unicode digits, trailing comment, extra colon suffix → all `None`.
- Whitespace strictness: no space after colon, space before colon, leading space/tab, NBSP/em-space variants → all `None`; multiple spaces/tabs after colon where Linux formatting puts them → accepted (matches frozen tests).
- Non-ASCII field/unit: fullwidth field initial, fullwidth unit initial, fullwidth colon, fullwidth digits → all `None`; BOM prefix → `None`.
- Overflow: 19-digit, 100-digit, and 1+18-zero inputs → `None`; 18-digit max (`18×9`) → `int*1024` exact; 18-digit `1e17` shape → exact.
- Exactness: `1/48256/262144` kB → `1024/49414144/268435456` respectively; `2097151/2097152` kB → `2147482624/2147483648` (`bytes = value*1024` exact).
- Extra reviewer edge cases beyond the test list (all matched expectation): no-trailing-newline accepted; extra blank line ignored (single field still accepted); 1000 spaces after colon accepted; `BOM` rejected; value-in-wrong-field rejected; `19-char leading-zero` rejected by length rule; trailing `CR` rejected.
- One initial reviewer expectation was corrected during probing: a trailing whitespace-only line after a valid line still yields the valid value (single-field count is unaffected). This is correct behavior, not a parser failure.

## 2. WSL source selection — PASS

- Production reader is `_read_proc_self_status_text`, which opens the frozen status path once per call with `open(path, "r", encoding="utf-8")` and returns `None` on any failure. `get_rss_bytes` is `parse_vmhwm_rss_bytes(_read_proc_self_status_text())` with no other input.
- Forbidden-pattern grep over the module returns no match for `subprocess`, `psutil`, `shell=True`/`Popen`/`os.system`, `VmRSS`, `statm`, `ru_maxrss`, `import resource`/`getrusage`, caching (`lru_cache`/`_CACHE`), retry/averaging/polling/sleep, environment switch (`getenv`/`environ`), or provider abstraction. The only `retry` mentions are pre-existing `no retry` comments outside the RSS block.
- `hasattr(module, "_read_ru_maxrss")` is `False`. Both the core module and the thin runner contain zero occurrences of `ru_maxrss` and zero occurrences of `import resource`.
- Open-count probe (own fixture, counting wrapper): a single `get_rss_bytes` call performs exactly `1` open of the fixture path.
- Fresh-read probe (own fixture): `100 kB` then rewrite to `200 kB` yields `102400` then `204800` with no caching.
- Rigged-bogus-reader run (own): monkeypatched stdlib usage counter to return an implausible multi-GiB value (and separately to raise); with a plausible below-limit fixture the WSL result still equals the `VmHWM` parse and the counter records zero calls. Deletion (not dead-code fallback) is confirmed by attribute absence plus zero-call behavior.

## 3. Fail-closed behavior — PASS (code paths + fake-decoder tests; no scientific runs)

- Preflight path (`run_cross_layer_discriminator`): probes once via `_probe_rss_valid`; `None`/invalid raises `PreflightBlocked` with the pre-execution terminal before input preparation and before any decoder bind/call; existing root is not created.
  - Own fake-decoder probe: `rss_probe=lambda: None` raises `PreflightBlocked`, terminal is the pre-execution terminal, decoder event list is empty, output path does not exist.
  - Missing-field fixture routed through `get_rss_bytes` blocks identically with zero decoder events.
- Mid-run path (`execute_slots`): each slot probes once; `not rss_valid` or `rss_bytes >= RSS_LIMIT_BYTES` sets the existing resource terminal and breaks with no retry/resume/replacement. Transfer non-eligibility remains a recorded non-invocation and does not interact with the RSS stop.
  - Own sequence probe: 5 valid probes then `None` yields terminal `D7_E_RESOURCE_OVERRUN`, `records == 5`, decoder call count `== 5` (preflight plus slots 1–4 valid, 5th recorded once, then stop).
  - Over-limit mid-run variant yields the same `5`-record resource-terminal shape.
- Over-limit at start does not raise preflight; it records one call then stops under the resource terminal (existing semantics, covered by `test_a2_11`). This distinction is preserved and documented here to avoid misreading the task shorthand: `None` blocks preflight zero-call; over-limit blocks at the first affected call.

## 4. Threshold boundary and schema — PASS

- `RSS_LIMIT_BYTES == 2147483648` (`2*1024**3`), unchanged from baseline.
- Stop condition is `rss_bytes >= RSS_LIMIT_BYTES` in both the loop and the terminal/verify paths (strict `<2GiB` permits; equality blocks).
- Own fake-decoder boundary probes: limit value blocks with `records == 1` under the resource terminal; double-limit blocks identically; limit-minus-`1024` permits a full `192`-record run under a non-resource terminal.
- `bytes = value*1024` exactness verified above for representative values including the boundary-adjacent pair.
- Schema: `RECORD_FIELDS.count("rss_bytes") == 1`; `RECORD_FIELDS` text is byte-identical to the `becf60f` baseline; `SEVEN_FILES` tuple unchanged; no new output key appears in the diff; manifest still carries the same limit scalar.

## 5. Unchanged science/schema and dry-run sequence — PASS

- Full text diff of the module against the `becf60f` baseline contains only the RSS-block replacement quoted above; a filtered diff for budget/matrix/formula/estimator/schema identifiers returns no changes.
- Constants observed unchanged at runtime: slot/budget trio, per-call/stored/outer walls, limit, seven-file list, terminal tuple order, record-field list.
- Dry-run run by this reviewer (`.venv/bin/python`, twice from repo root plus once via absolute interpreter from an external temp cwd): exit `0`, `193` output lines, header `slots=192 mandatory=128 budget=192`, slot indices exactly `1..192`, and full `(f, seed, direction, role)` order matches the frozen 6-per-group enumeration. No evidence root created (result-root count for the discriminator prefix remains `0`); unauthorized exact-shape invocation returns exit `3` with a not-authorized message and creates no target; `--help` returns exit `0`.

## 6. Test sufficiency and literal runs — PASS

T3-to-test mapping (all genuinely exercised; inspected, not name-matched):

- T3-01 valid conversion → `test_a2_01_valid_vmhwm_conversion`.
- T3-02 whitespace only where Linux requires → `test_a2_02_whitespace_only_where_linux_requires`.
- T3-03 missing field → `test_a2_03_missing_field`.
- T3-04 duplicate field → `test_a2_04_duplicate_field`.
- T3-05 wrong unit → `test_a2_05_wrong_unit`.
- T3-06 malformed/non-integer/signed/zero/negative → `test_a2_06_malformed_signed_zero_negative`.
- T3-07 read failure (+ fresh-read-per-call) → `test_a2_07_read_failure_and_fresh_read_per_call`.
- T3-08 overflow without wrapping → `test_a2_08_overflow_rejection_without_wrapping`.
- T3-09 bogus-reader independence and legacy-reader absence → `test_a2_09_bogus_ru_maxrss_cannot_affect_wsl_result`.
- T3-10 below-limit permits existing path → `test_a2_10_below_limit_permits_existing_path`.
- T3-11 equal-to and above limit block → `test_a2_11_limit_boundary_blocks`.
- T3-12 `None` blocks preflight before first decoder → `test_a2_12_none_blocks_preflight_before_first_decoder`.
- T3-13 mid-run `None`/over-limit preserves resource terminal without retry → `test_a2_13_midrun_none_or_overlimit_keeps_resource_terminal`.
- T3-14 writers/verifier retain `rss_bytes` schema → `test_a2_14_rss_bytes_schema_invariant`.
- T3-15 imports/`--help`/dry-run/unauthorized refusal/external-cwd sentinel zero-call/zero-root → `test_a2_15_cli_surface_zero_decoder_zero_root`.

Literal runs by this reviewer (`.venv/bin/python`, `-p no:cacheprovider`, separate processes, fresh basetemps):

- `py_compile` for core, test, and runner: OK.
- Focused A2: `15 passed, 25 deselected` in `8.22s` (deselections are this reviewer’s own `-k test_a2_` filter, not stale skips).
- Full D7-E file: `40 passed` in `249.84s` (all `25` pre-A2 plus all `15` A2; zero failures, zero skips).
- No newly-failing in-scope test. Full run has zero deselected IDs, so no stale-tripwire isolation was needed.

## 7. Root equality and scope — PASS

- Committed diff touches only the two allowed files named above; no workspace result path is added or modified by the diff.
- Discriminator-prefix result-root count observed `0` before and after reviewer probes (reviewer used only `/tmp` fixtures and dry-run/help/refusal invocations that create no root).
- Authorization/state observed unchanged in the cycle file: execution authorizations false, attempts/completed zero, no execution consumed by review actions.

## Verdict

D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2

## Blockers

- None.

## Limitations and next gate

- This T5 review grants no execution authorization and renews nothing by itself.
- The renewed Pre-EXECUTE review is still required, with exactly one fresh live probe as specified in the packet T6; repeated probing until a pass remains forbidden.
- Reviewer did not execute any scientific run and did not evaluate scientific conclusions; science/dry-run equality here means no change, not correctness of the underlying method.

## Review doc path

`docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_RSS_TELEMETRY_REWORK_REVIEW_A2.md`
