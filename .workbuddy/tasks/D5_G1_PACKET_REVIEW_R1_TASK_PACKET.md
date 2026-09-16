# D5-G1-PACKET-REVIEW-R1 — independent review of the frozen G1 packet

## 0. Role and verdict

Act as an independent, read-only scientific/implementation reviewer. Review
commit `4bf2682a` and
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`.

This review authorizes nothing and executes nothing. Its verdict is exactly one
of:

- `G1_PACKET_REVIEW_PASS` — D1–D6 are sufficient and all five open questions
  are prospectively decided; implementation may start, but G1 remains
  unauthorized.
- `G1_PACKET_REVIEW_FAIL` — name the blocking defect and the smallest packet
  revision required before implementation.

Do not edit code or repair findings.

## 1. Hard prohibitions

- No decoder and no `--phase` invocation, including refusal probes.
- No Model-F prepare/verify replay.
- No CAL/VAL/parquet/raw-row read.
- No write, delete, move, rename, copy, normalization, or hash under any
  `workspace/v72p2d5_*` evidence root.
- No modification to `.py`, existing `.md`, OpenSpec, decision-log, memory, or
  `cycle_state.yaml`.
- No git write command: no add/commit/push/reset/stash/checkout/clean/rebase/
  revert/amend/renormalize.
- Only one new file is permitted:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PACKET_REVIEW_R1.md`.
- Findings are reported, never fixed.

## 2. Baseline checks

Independently verify:

1. `4bf2682a` changes exactly one file: `G1_EXECUTION_PACKET_R1.md`.
2. Current state has P0 cost accepted, `next_gate: G1_PACKET_REVIEW`, all nine
   authorization keys false, and promotion false.
3. The retained invalid root `workspace/v72p2d5_g1/20260906_r1/` exists with
   four files and remains `VOID_RETAINED_IN_PLACE`.
4. Proposed root `workspace/v72p2d5_g1/20260907_r2/` and G2 root are absent.
5. The packet carries every limitation in `P0_RESULT_ACCEPTANCE_R1.md` A05 and
   `GUARD_REWORK_REVIEW_R1.md` L1–L4 without weakening it.

Use name/size/mtime stat only for workspace evidence. Capture pre/post snapshots
and require equality.

## 3. Frozen parameter audit

Compare every frozen parameter in the packet against both:

- `openspec/changes/v72p2d5-p0-g1-g2-production-path/design.md`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`

Give one row per item: width, `f` order, row tables, mother reuse, graph seeds,
block seeds, paired-block count, oracle subset, decoder configuration, call
count, Model-F input, L1→L2 ordering, budget, output files, metric definition,
and current trend condition. Mark `AGREE`, `DISAGREE`, or `NOT_VERIFIABLE`,
with source locations. Any scientific `DISAGREE` blocks PASS.

Explicitly verify that:

- prefix slicing occurs before each `f` decode;
- oracle is diagnostic only;
- the current `passed` expression is exactly monotonic plus zero nonfinite;
- an all-zero APP exact sequence therefore currently passes;
- G1 currently persists neither APP syndrome counts nor iteration aggregates;
- current Windows RSS can be null;
- current G1 root constant still names the retained invalid root;
- both evidence writers contain the duplicated fallback named in D4.

## 4. Review D1–D6 for sufficiency and minimality

For each delta, give `ACCEPT`, `REVISE`, or `REJECT` and explain the smallest
scientifically sufficient implementation.

### D1 root

Confirm the new root does not exist, cannot overwrite the VOID root, and has an
unambiguous no-rerun identity. Decide OQ-G1-ROOT.

### D2 RSS

Inspect whether the historical decoder runs in the current Python process or
spawns a child. Decide whether current-process Windows working set is the right
scope. Also decide **sampling semantics**: a single end-of-run reading is not a
peak. If `<2 GiB` remains a gate, require sampling at a prospectively fixed
location (at least after every decoder/block result) and persisting the maximum.
Do not require a new dependency or a process-tree monitor without evidence that
the decoder uses child processes. Decide OQ-G1-RSS.

### D3 observability

Confirm the proposed aggregate schema can distinguish exact failure, syndrome
failure, nonfinite output, and 90-iteration saturation. Decide whether per-f
aggregates are sufficient; do not demand raw beliefs or per-symbol records.
Require internal identities such as `failure_fraction=1-exact/attempted`, counts
within attempted/subset bounds, and decoder calls = 440.

### D4 writer

Prefer the smallest fail-loud correction. The producer owns the field, so direct
required-key access is preferred unless a concrete compatibility need is shown.
The public column remains `app_failure_fraction`.

### D5 guard depth

Confirm a no-subdirectory invariant closes the disclosed nested-write gap for
the current flat four-file evidence contract. Do not expand this into recursive
hashing or a manifest system.

### D6 reachability

Review the stated real-launch probe. It is sufficient only if the repository
root is absent from `sys.path`, package import fails, no `sys.path` insertion is
performed, the accepted Model-F input is reached, the sentinel fires exactly at
the first decoder call, tmp output is empty, and both the proposed G1 root and
G2 root remain absent.

## 5. Decide the five open questions

Every question must be `DECIDED`; otherwise verdict is FAIL.

### OQ-G1-ROOT

Accept `workspace/v72p2d5_g1/20260907_r2/` or provide one exact replacement.
The retained `20260906_r1` root is never an option.

### OQ-G1-RSS

State whether Windows current-process working-set sampling is sufficient for
the 2 GiB gate; freeze sample timing and persisted maximum semantics. If it is
only context, say so and explain why the budget is not a gate.

### OQ-G1-SIGNAL

Prospectively decide the all-zero degeneracy before seeing authorized G1 data.
The recommended minimum meaningful trend rule is:

```text
zero crash/nonfinite
AND rates are nondecreasing
AND top APP exact count > 0
AND (top APP exact rate > low APP exact rate OR top APP exact rate == 1.0)
```

Accept it or replace it with one exact rule. Explain why a flat all-zero line
cannot be called a trend pass, and why a saturated `1.0,1.0` line should not be
rejected merely for lacking strict increase. This is a G1 trend gate, not G2
qualification; do not introduce a 50% or 90% threshold here without a separate
scientific reason.

### OQ-G1-WATCHDOG

Freeze the exact outer command and outcomes. Evaluate the proposal:

`"C:\Program Files\Git\usr\bin\timeout.exe" -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1`

The frozen scientific budget remains 900 s; 960 s is an outer process guard,
not permission to pass over budget. Timeout/kill consumes the sole attempt; any
partial root is retained VOID; no retry.

### OQ-G1-OUTCOME

Define mutually exclusive honest terminal labels for at least:

- completed meaningful trend pass;
- completed no-signal/current-configuration fail;
- nonfinite or crash;
- scientific runtime over 900 s despite process completion;
- watchdog timeout/kill;
- pre-execution blocked/refused.

Labels must not imply FER, real-data performance, qualification, or G2
authorization. State whether the existing boolean `passed` must be revised to
match the selected signal rule.

## 6. Required review output

Create only `G1_PACKET_REVIEW_R1.md`, containing:

1. role, baseline, and non-authorization statement;
2. numbered check table with PASS/FAIL/NOT_VERIFIABLE;
3. parameter audit table;
4. D1–D6 decisions;
5. five OQ decisions with exact frozen wording;
6. required implementation acceptance matrix;
7. pre/post root snapshots;
8. commands executed and explicitly not executed;
9. strongest supported claim and explicit non-claims;
10. one final verdict token.

If PASS, the implementation acceptance matrix must at minimum require:

- fresh root constant and no old-root reuse;
- Windows RSS implementation and frozen peak sampling semantics;
- exact/syndrome/iteration/RSS aggregate schema plus identities;
- fail-loud writer correction;
- no-subdirectory invariant in both test helpers;
- real-launch sentinel test/probe;
- lifecycle-safe fake/injected/tmp tests;
- full three-file D5 suite green with basetemp under `workspace/`;
- all authorizations still false and both proposed G1/G2 roots absent.

Do not commit the review.

## 7. Return format

Report verdict, parameter audit counts, D1–D6 decisions, each OQ decision in one
line, any blocking/non-blocking findings, tests run (normally none), pre/post
root equality, and true/false prohibitions.

End with:

`G1 包评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。`

