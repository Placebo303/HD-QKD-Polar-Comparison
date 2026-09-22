# D5-G1-FREEZE-R1 — G1 trend-gate packet freeze (docs only)

## 0. Outcome and stop rule

Create one frozen G1 packet for independent review. This task does **not**
implement, authorize, or execute G1.

Stop immediately if any command invokes a decoder, any `--phase`, reads
CAL/VAL/parquet rows, writes under `workspace/v72p2d5_*`, changes a `.py`, or
changes `cycle_state.yaml`. Do not repair anything discovered; record it in the
packet as an open question or required implementation delta.

## 1. Required baseline

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected baseline commit: `0f2016d3` or a documentation-only descendant.
- Required state:
  - `p0_cost_result_accepted: true`
  - `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`
  - `next_gate: G1_PACKET_REVIEW`
  - all nine `*_execution_authorized: false`
  - `scientific_promotion: false`
- The invalid G1 root
  `workspace/v72p2d5_g1/20260906_r1/` must exist unchanged and remains
  `VOID_RETAINED_IN_PLACE`.
- `workspace/v72p2d5_g2/20260906_r1/` must remain absent.

Record branch, HEAD, ahead count, authorization lines, and a top-level
name/size/mtime snapshot of P0, invalid G1, G2, G0, G0-recovery, Model-F, and
structure roots. Read-only stat only; do not hash workspace evidence.

## 2. Only allowed repository change

Create exactly one file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`

Do not modify any existing file. After checks, commit only that file with:

```text
docs(v72p2d5): freeze G1 trend-gate packet, execution not authorized

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Do not push.

## 3. Frozen scientific contract to transcribe

The new packet must state all of the following without reinterpretation:

| Item | Frozen value |
| --- | --- |
| Stage | G1 synthetic integration trend gate |
| Width | `n_IR=64` symbols |
| `f` values | `1.0`, `1.2`, in that order |
| L1 rows | `49`, `59` |
| L2 rows | `43`, `52` |
| Mother construction | one L1 and one L2 max mother, reused by natural prefixes across both `f` values |
| Graph seeds | L1 `2026090501`, L2 `2026090502` |
| Block seeds | exactly `2026090600..2026090699`, 100 paired blocks per `f`, same ordered seed list for both `f` values |
| Oracle subset | first 20 seeds per `f`, diagnostic only |
| Decoder | historical GF32 decoder, cold start, `max_iter=90`, `damping_alpha=1.0` |
| Calls | 440 = APP `100×2×2` plus oracle `20×2×1` |
| Model input | accepted fixed Model-F root `workspace/v72p2d5_model_f_input/20260907_r1/` |
| Order | L1 APP then L2 APP; L2 is attempted even when L1 is not exact; oracle never controls the verdict |
| Runtime budget | G1 total `<=900 s`; per-call reference `120 s`; one outer watchdog is mandatory |
| Output | exactly four no-overwrite files: `results.json`, `table.csv`, `report.md`, `execution_summary.json` |
| Metric | `app_failure_fraction = 1 - app_exact_count/attempted`; synthetic block failure fraction, never real FER |
| Current frozen trend condition | monotonic APP exact rate across `f`, zero crash, zero nonfinite |

The packet must say that G1 is not real data, not FER, not leakage, not key
rate, not qualification, and not permission for G2.

## 4. Required pre-execution implementation deltas

The packet must mark G1 **`EXECUTE_NOT_AUTHORIZED`** and
**`IMPLEMENTATION_REWORK_REQUIRED_BEFORE_PRE_EXECUTE`**. Freeze the following
smallest deltas; none is implemented in this task.

### D1 — Fresh G1 root

The current production constant points at the retained VOID root and cannot be
used. Proposed fresh root:

`workspace/v72p2d5_g1/20260907_r2/`

Before any authorization, change the G1 production root to this exact path and
update only tests/OpenSpec/docs that own this G1 path. The old
`20260906_r1` root must remain untouched and barred from comparison or reuse.
The independent reviewer must explicitly accept or reject this proposed root.

### D2 — Windows RSS measurement

P0 returned `rss_bytes: null` because `resource` is unavailable on Windows.
Before G1, extend the existing `_rss_bytes()` with the smallest stdlib Windows
fallback using `ctypes` and `GetProcessMemoryInfo` for the current Python
process working set. Keep the existing Unix `resource` path. Return `None` only
when neither method is available. Add focused fake/monkeypatched tests; do not
add `psutil` or another dependency.

The reviewer must decide whether current-process working set is sufficient for
the frozen `<2 GiB` reference. Do not claim process-tree RSS unless measured.

### D3 — Exact/syndrome/iteration observability

G1 must persist, for each `f`, at minimum:

- attempted blocks;
- APP exact count/rate/failure fraction;
- APP syndrome-ok count;
- APP total iterations and maximum per-block APP iterations;
- oracle exact count, syndrome-ok count, and total iterations for the frozen
  20-block subset;
- nonfinite count;
- total decoder calls.

This is aggregate scalar evidence only; no per-symbol beliefs or raw samples.
It must allow reviewers to distinguish all calls reaching the 90-iteration cap
from early convergence and from syndrome failure.

### D4 — Fail-loud metric writer

Replace the duplicated fallback
`item.get("app_failure_fraction", item.get("app_failure_fraction", 1.0))`
in both G1 and G2 evidence writers. Because the internal schema is trusted and
the producer always emits the field, use direct required-key access or one
single correctly named fallback accepted by review. Do not add a compatibility
layer. Preserve the public output column name `app_failure_fraction` and its
definition above.

### D5 — Lifecycle guard depth

Choose the minimal accepted option from guard-review L1: add an explicit
no-subdirectory invariant to both test-file formal-root snapshot helpers, so
any formal root containing a subdirectory fails loudly. Do not build recursive
hashing or a generic manifest system. Keep the existing top-level
name/size/mtime comparison.

### D6 — Real launch-path reachability

The future Pre-EXECUTE gate must run a first-call sentinel probe from a Python
file outside the repository while cwd is the repository root. It must prove:

- repository root is absent from `sys.path`;
- `import comparison_bench` fails in that condition;
- accepted Model-F input loads through the file-path consumer;
- the sentinel reaches exactly the first decoder call;
- temporary output stays empty;
- fresh G1 and G2 roots remain absent.

No `python -c` and no `sys.path` insertion are allowed for this probe.

## 5. Limitations that must be carried verbatim in substance

- `L1`: current formal-root snapshots are top-level only; D5 chooses the
  no-subdirectory invariant before G1.
- `L2`: `test_T1_23` is a narrow tripwire, not a general proof against every
  spelling of an absence assertion. Primary evidence is lifecycle snapshot
  invariance plus review.
- `L3`: `test_T1_22` red-on-real-content-change is established by parser logic,
  not a live mutation run. Do not cite a live-fire result that does not exist.
- `L4`: the corrected dirty-tree observation is 1969 porcelain lines / 1887
  modified paths / zero content diffs at that review point; the old `63` figure
  is superseded. Current counts are informational and may drift.
- `L-RSS`: P0 did not verify the 2 GiB budget; D2 is mandatory before G1.
- `L-SCALE`: P0's `projected_g1_s=161.8241519993171` is same-width call-count
  guidance only. It is not a completion guarantee. P0's G2 projection has no
  licensing force.
- `L-ITER`: all 12 P0 decoder calls ran to `MAX_ITER=90`; G1 must budget at the
  cap and persist exact/syndrome/iteration evidence.
- `T1`: all tests invoking authorized synthetic entrypoints must keep explicit
  fake decoder, injected Model-F arrays, and temporary output root. No test may
  bind the production decoder or default formal root.

## 6. Open questions for independent packet review

The packet must leave exactly these decisions to the independent reviewer:

1. `OQ-G1-ROOT`: accept `workspace/v72p2d5_g1/20260907_r2/` as the fresh
   canonical root, or name one replacement. Reuse of `20260906_r1` is forbidden.
2. `OQ-G1-RSS`: is current-process Windows working-set RSS sufficient for the
   `<2 GiB` reference, or must the budget be explicitly downgraded to
   context-only? No process-tree claim without measurement.
3. `OQ-G1-SIGNAL`: under the current frozen condition, an all-zero APP exact
   sequence is monotonic and can set `passed=true`. Decide whether G1 may advance
   on that degenerate no-signal result. If not, define the smallest prospective
   signal condition before implementation; do not tune it after seeing G1.
4. `OQ-G1-WATCHDOG`: freeze the exact outer watchdog and timeout outcome. The
   proposal is Git-for-Windows GNU `timeout.exe -k 30 960 ...`; timeout consumes
   the sole attempt, leaves any partial root VOID in place, and forbids rerun.
5. `OQ-G1-OUTCOME`: define honest terminal labels for completion, timeout,
   nonfinite/crash, no-signal, and trend-pass. Labels must not imply FER or
   qualification.

The authoring session must not answer these questions.

## 7. Evidence and self-checks

Before committing:

1. Re-stat all roots from STEP 1 and prove name/size/mtime unchanged; G2 and the
   proposed fresh G1 root remain absent.
2. Confirm all nine authorization keys remain false and
   `next_gate: G1_PACKET_REVIEW`.
3. Run no pytest: this is docs-only and the accepted suite evidence is already
   `201 passed`; rerunning adds no information here.
4. Confirm `git diff --numstat -- '*.py'` and
   `git diff --cached --numstat -- '*.py'` are empty.
5. Stage only `G1_EXECUTION_PACKET_R1.md`. Confirm staged count is 1 and no
   other path appears. Any deviation is STOP; do not self-repair with reset or
   checkout.

## 8. Return format

Report:

1. baseline branch/HEAD/ahead and authorization state;
2. pre/post root snapshots and whether identical;
3. the frozen G1 parameter table;
4. D1–D6 each present in the packet;
5. OQ-G1-ROOT/RSS/SIGNAL/WATCHDOG/OUTCOME each still OPEN;
6. staged path, commit SHA, final `git status -sb`;
7. true/false: decoder run, any phase invoked, CAL/VAL/parquet rows read,
   workspace changed, `.py` changed, authorization changed, G2 root created,
   pushed.

End with:

`G1 执行包已冻结待独立评审；G1 未授权、未执行；新 G1 根尚未创建；G2 未授权。`

