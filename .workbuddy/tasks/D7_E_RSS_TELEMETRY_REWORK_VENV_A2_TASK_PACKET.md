# D7-E RSS Telemetry Rework — WSL A2 Task Packet

## 0. Objective and lifecycle

Resolve the E09 pre-execution blocker without running D7-E or consuming authorization. The observed WSL `resource.getrusage(...).ru_maxrss` value intermittently disagreed with `/proc/self/status` by several GiB, making the one-shot execution gate non-deterministic.

This is a telemetry/environment compatibility correction only. It must not change D7-E's scientific matrix, estimator, priors, formulae, provenance eligibility, labels, terminal ordering, decoder configuration, call budgets, roots, or result schema.

Entry state remains `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`. Completion state is `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`. This packet grants no execution authorization.

## 1. Main-thread ruling

Freeze the following A2 rule:

1. On Linux/WSL, current-process peak RSS is read from `/proc/self/status`, field `VmHWM`, whose unit must be exactly `kB`; convert with `bytes = value * 1024`.
2. `VmHWM` is authoritative for this WSL execution path. Do not compare against or fall back to `ru_maxrss` when `/proc/self/status` is present.
3. Missing file, missing field, duplicate field, malformed/non-integer/non-positive value, wrong unit, read error, or overflow returns `None` and blocks before scientific execution or at the first affected call under the existing resource terminal.
4. Do not silently substitute `VmRSS`, `/proc/<pid>/statm`, psutil, shell commands, or another process.
5. The limit remains strict `< 2 GiB`; equality or greater is blocked. Units and threshold do not change.
6. The stored scalar key remains `rss_bytes`; no new scientific output field or schema revision is required.
7. `resource.ru_maxrss` may remain only for non-Linux legacy code if already necessary, but the frozen WSL path must not call it. Prefer deleting an unused fallback over adding a general telemetry framework.
8. A single fresh E09 probe after implementation is evidence. Repeating probes until one passes is forbidden.

## 2. Hard prohibitions

- Zero real decoder calls and zero `--phase` invocations.
- Do not execute D7-E, R1d, G1, G2, CAL, VAL, Model-F preparation, real/raw, oracle, flooding, warm start, alternating, joint, or feedback.
- Do not create any `workspace/d7_e_cross_layer_discriminator_*` result root or UUID.
- Do not read real Model-F contents or protected scientific artifact contents.
- Do not alter any D7-E scientific constant, matrix, estimator, formula, provenance rule, label, terminal priority, budget, root, command argument, writer column, or verifier scientific logic.
- Do not change the accepted D7-B/C/D roots or any formal root.
- Do not push, broad-stage, clean, reset, checkout, stash, rebase, or amend.
- Any requirement ambiguity or scoped test regression means STOP; do not self-authorize a broader repair.

## 3. Allowed paths

Only these paths may change:

1. `openspec/changes/v72p2d7-provenance-safe-cross-layer-discriminator/design.md`
2. `openspec/changes/v72p2d7-provenance-safe-cross-layer-discriminator/tasks.md`
3. `openspec/changes/v72p2d7-provenance-safe-cross-layer-discriminator/specs/provenance-safe-cross-layer-discriminator/spec.md`
4. `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`
5. `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py`
6. `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md` (new)
7. `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_RSS_TELEMETRY_REWORK_REVIEW_A2.md` (new)
8. `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_PRE_EXECUTE_REVIEW_VENV_RSS_A2.md` (new)
9. `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/cycle_state.yaml`
10. Append-only, only if a reusable failure-mode entry is warranted after review: `docs/troubleshooting.md`, `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`.

Do not edit the original preregistration or execution packet except through the named A2 addendum. Preserve the E09 STOP return as provenance if it already exists; do not fabricate a missing operator artifact.

## 4. T0 — baseline and failing-mode reproduction

Read all allowed existing files before editing. Record:

- branch, HEAD, required commits `08590fba`, `031deee7`, `d6e40dd`;
- current state and all authorization flags;
- D7-E root absence and protected-root metadata;
- exact current RSS implementation and existing tests;
- a zero-decoder unit reproduction using injected text where `ru_maxrss` is an implausible 3.84 GiB while `VmHWM` is a plausible positive value below 2 GiB.

Do not repeatedly sample the live kernel in T0. One live observation may be recorded only as context; correctness must be tested by deterministic fixtures.

## 5. T1 — OpenSpec and addendum freeze

Before production code changes:

1. Add the §1 rule as an explicit OpenSpec delta and tasks A2-01…A2-08.
2. Create `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md` declaring that it supersedes only RSS source semantics in R1/A1.
3. Preserve `.venv/bin/python`, the exact frozen command, all scientific constants, and the `<2 GiB` threshold.
4. State that the renewed Pre-EXECUTE review becomes stale until A2 implementation review and fresh E09 pass.

Commit the OpenSpec/addendum freeze separately, locally, with a precise scoped manifest. Do not push.

## 6. T2 — minimal implementation

Implement a small pure parser plus one file-read wrapper:

- parser input: text equivalent to `/proc/self/status`;
- parser output: positive integer bytes or `None`;
- recognize exactly one `VmHWM: <positive integer> kB` line;
- reject missing, duplicate, malformed, decimal, signed, zero, negative, wrong-unit, overflow, and non-ASCII-confusable field/unit cases;
- production Linux/WSL read uses `/proc/self/status` once per probe call;
- no subprocess, shell, psutil, caching, retries, averaging, polling, environment switch, or generalized provider abstraction.

Keep `get_rss_bytes()`'s return contract unchanged. Do not change callers except where strictly required to route through the new parser.

## 7. T3 — deterministic tests

Add focused tests for at least:

1. valid representative `VmHWM` conversion;
2. whitespace accepted only where Linux status formatting requires it;
3. missing field;
4. duplicate field;
5. wrong unit;
6. malformed/non-integer/signed/zero/negative value;
7. read failure;
8. overflow/unreasonably large integer handling without wrapping;
9. conflicting bogus `ru_maxrss` cannot affect WSL result and `_read_ru_maxrss` is not called;
10. value below limit permits the existing path;
11. value equal to and above 2 GiB blocks;
12. `None` blocks before the first scientific decoder attempt in the preflight path;
13. mid-run `None`/over-limit preserves existing resource-terminal behavior without retry;
14. writers/verifier retain the same `rss_bytes` schema;
15. imports, `--help`, dry-run, unauthorized exact-shape refusal, and external-cwd sentinel remain zero-decoder/zero-root.

Use injected status text/readers and fake decoders only. Never read the real Model-F artifact in tests.

## 8. T4 — verification matrix

Run with `.venv/bin/python` from repo root, using fresh owned basetemps:

1. `py_compile` for D7-E core, test, and runner.
2. Focused A2 RSS tests.
3. Full D7-E test file.
4. BP provenance focused suite and D7-C/D7-D focused compatibility suites named in the existing OpenSpec.
5. One standard milestone regression sufficient to show no scientific drift; do not run unrelated perf-v38 or long suites.
6. Byte/value checks proving all frozen D7-E scientific constants and dry-run 192-slot sequence are unchanged.

Any newly failing in-scope test is blocking. Pre-existing stale root-absence tripwires may be reported only if reproduced at the pre-change baseline and explicitly isolated; do not skip, xfail, or delete them for green output.

## 9. T5 — independent implementation review

Create a read-only review whose unique verdict is either:

- `D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2`, or
- `D7_E_RSS_TELEMETRY_REWORK_REVIEW_FAIL_A2`.

The reviewer must independently inspect parser strictness, WSL source selection, fail-closed behavior, no fallback/gate-shopping, threshold boundary, unchanged schema/science, test sufficiency, root equality, and scope. It must run deterministic fixtures, not rely on repeated favorable live samples.

FAIL means STOP; do not renew Pre-EXECUTE.

## 10. T6 — renewed Pre-EXECUTE review

Only after T5 PASS:

1. Re-run the ordinary D7-E Pre-EXECUTE checklist with A1 interpreter rules.
2. Run exactly one fresh live E09 command using `.venv/bin/python`; capture `/proc/self/status` parser result and require positive finite `<2 GiB`.
3. In the same command, capture the raw `VmHWM` line for traceability. Do not call `ru_maxrss` and do not repeat E09.
4. Repeat dry-run, unauthorized refusal, and external-cwd sentinel once each; zero decoder/root/read.
5. Confirm no UUID/root, all auth false, attempts/completed zero, protected roots unchanged, and scoped content clean.

Unique verdict:

- `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`, or
- `D7_E_PRE_EXECUTE_REVIEW_FAIL_VENV_RSS_A2`.

This review grants no authorization.

## 11. T7 — closeout

For dual PASS only:

- mark A2 OpenSpec tasks complete with evidence;
- update state to `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`;
- point state to the A2 addendum and both PASS reviews;
- leave every authorization false, attempts/completed zero, decoder/result false, and no UUID/root;
- append only durable, non-scientific failure-mode facts if memory triage approves;
- commit scoped files locally and do not push.

Do not reuse the previous user authorization. A later execution requires a fresh explicit authorization referencing RSS A2.

## 12. Return format

Return delta only:

1. A2-01…A2-08 status.
2. Root cause and exact new RSS contract.
3. Changed paths and commit SHAs.
4. Deterministic test table and literal summaries.
5. Proof that bogus `ru_maxrss` cannot affect WSL decisions.
6. Exactly one live E09 result and raw `VmHWM` line.
7. Both unique review verdicts.
8. Frozen-science equality, protected-root equality, no-root/no-UUID, authorization/state, and no-push.
9. Remaining limitations and the exact next gate.

End with: `D7-E WSL RSS telemetry 已从不稳定 ru_maxrss 收口到 fail-closed /proc/self/status VmHWM，并通过实现与 renewed Pre-EXECUTE 评审；尚未授权、未执行，R1d、G1、G2 均未授权。`
