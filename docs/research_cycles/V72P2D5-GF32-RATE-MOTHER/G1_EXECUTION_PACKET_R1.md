# G1 Execution Packet R1 — V72P2D5 GF32 Rate Mother (trend gate, frozen for independent review)

Status: `EXECUTE_NOT_AUTHORIZED` and `IMPLEMENTATION_REWORK_REQUIRED_BEFORE_PRE_EXECUTE`.

This packet freezes the G1 synthetic integration trend gate for independent
review. This packet does not implement, authorize, or execute G1.

## 1. Baseline (freeze-time record, read-only)

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `0f2016d356038cd081a85b90718fed46bc0c9caf`
  (`result(v72p2d5): accept P0 cost preflight, cost measurement only`;
  HEAD equals the expected baseline commit, so there are zero commits after
  `0f2016d3` to verify)
- Ahead count: `12` (`formal-ir-v72p1-addendum-clean...origin/formal-ir-v72p1-addendum-clean [ahead 12]`)
- Required authorization state (from
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`):
  - `p0_cost_result_accepted: true`
  - `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`
  - `next_gate: G1_PACKET_REVIEW`
  - `structure_execution_authorized: false`
  - `g0_execution_authorized: false`
  - `g0_recovery_execution_authorized: false`
  - `p0_cost_execution_authorized: false`
  - `g1_execution_authorized: false`
  - `g2_execution_authorized: false`
  - `synthetic_execution_authorized: false`
  - `real_execution_authorized: false`
  - `formal_execution_authorized: false`
  - `scientific_promotion: false`
  - `g1_unauthorized_output_disposition: VOID_RETAINED_IN_PLACE`
- Root snapshots (top-level only; read-only stat, no hashing, no content reads):
  - P0 `workspace/v72p2d5_p0_cost`: EXISTS, Name=`v72p2d5_p0_cost`,
    LastWriteTime=`2026-09-07 18:09:17`, TopEntries=`1`;
    top level: DIR `20260906_r1`, LastWriteTime=`2026-09-07 18:09:17`.
  - Invalid G1 `workspace/v72p2d5_g1/20260906_r1`: EXISTS,
    Name=`20260906_r1`, LastWriteTime=`2026-09-07 02:35:32`, TopEntries=`4`;
    top level: FILE `execution_summary.json` Length=`267`
    LastWriteTime=`2026-09-07 02:35:32`; FILE `report.md` Length=`146`
    LastWriteTime=`2026-09-07 02:35:32`; FILE `results.json` Length=`2593`
    LastWriteTime=`2026-09-07 02:35:32`; FILE `table.csv` Length=`126`
    LastWriteTime=`2026-09-07 02:35:32`.
    This root is `VOID_RETAINED_IN_PLACE`: untouched, never reused,
    overwritten, compared, or cited as performance.
  - G2 `workspace/v72p2d5_g2/20260906_r1`: ABSENT.
  - G2 parent `workspace/v72p2d5_g2`: ABSENT.
  - G0 `workspace/v72p2d5_g0`: EXISTS, Name=`v72p2d5_g0`,
    LastWriteTime=`2026-09-06 00:34:34`, TopEntries=`1`;
    top level: DIR `20260905_r2`, LastWriteTime=`2026-09-06 00:34:34`.
  - G0-recovery `workspace/v72p2d5_g0_recovery`: EXISTS,
    Name=`v72p2d5_g0_recovery`, LastWriteTime=`2026-09-06 02:47:43`,
    TopEntries=`1`; top level: DIR `20260906_r1`,
    LastWriteTime=`2026-09-06 02:47:43`.
  - Model-F `workspace/v72p2d5_model_f_input/20260907_r1`: EXISTS,
    Name=`20260907_r1`, LastWriteTime=`2026-09-07 02:07:07`, TopEntries=`2`;
    top level: FILE `model_f_input_summary.json` Length=`752`
    LastWriteTime=`2026-09-07 02:07:07`; FILE `model_f_input.npz`
    Length=`208467` LastWriteTime=`2026-09-07 02:07:07`.
    This is the accepted fixed Model-F root.
  - Structure `workspace/v72p2d5_structure`: EXISTS, Name=`v72p2d5_structure`,
    LastWriteTime=`2026-09-05 21:44:34`, TopEntries=`1`;
    top level: DIR `20260905_r2`, LastWriteTime=`2026-09-05 21:44:34`.
  - G1 parent `workspace/v72p2d5_g1`: EXISTS, Name=`v72p2d5_g1`,
    LastWriteTime=`2026-09-07 02:35:32`, TopEntries=`1`
    (only `20260906_r1`).
  - Proposed fresh G1 root `workspace/v72p2d5_g1/20260907_r2`: ABSENT.
- Frozen facts carried without questioning:
  - P0 accepted scope is `COST_MEASUREMENT_ONLY`.
  - The old G1 root `workspace/v72p2d5_g1/20260906_r1/` is
    `VOID_RETAINED_IN_PLACE` (untouched, never reused/overwritten/compared/
    cited as performance).
  - The production constant still points at the old root, so G1 is not
    executable in the current tree.
  - The proposed new root `workspace/v72p2d5_g1/20260907_r2/` needs reviewer
    accept/replace.
  - The G1 schema lacks syndrome/iteration/RSS observability, carries a
    duplicated `app_failure_fraction` fallback, and uses top-level-only
    snapshots; these are pre-execution deltas (D1–D6 below), NOT fixed here.
  - The current `passed = monotonic and nonfinite == 0` condition lets an
    all-zero exact sequence pass; this is NOT decided here and is left as
    `OQ-G1-SIGNAL`.

## 2. Frozen scientific contract (transcribed without reinterpretation)

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

Explicit non-claims: G1 is not real data, not FER, not leakage, not key rate,
not qualification, and not permission for G2.

## 3. Required pre-execution implementation deltas (frozen; none implemented here)

G1 is `EXECUTE_NOT_AUTHORIZED` and
`IMPLEMENTATION_REWORK_REQUIRED_BEFORE_PRE_EXECUTE`.

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

## 4. Limitations carried in substance

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

## 5. Open questions for independent packet review (OPEN, UNANSWERED)

1. `OQ-G1-ROOT`: accept `workspace/v72p2d5_g1/20260907_r2/` as the fresh
   canonical root, or name one replacement. Reuse of `20260906_r1` is forbidden.
   Status: OPEN, UNANSWERED.
2. `OQ-G1-RSS`: is current-process Windows working-set RSS sufficient for the
   `<2 GiB` reference, or must the budget be explicitly downgraded to
   context-only? No process-tree claim without measurement.
   Status: OPEN, UNANSWERED.
3. `OQ-G1-SIGNAL`: under the current frozen condition, an all-zero APP exact
   sequence is monotonic and can set `passed=true`. Decide whether G1 may advance
   on that degenerate no-signal result. If not, define the smallest prospective
   signal condition before implementation; do not tune it after seeing G1.
   Status: OPEN, UNANSWERED.
4. `OQ-G1-WATCHDOG`: freeze the exact outer watchdog and timeout outcome. The
   proposal is Git-for-Windows GNU `timeout.exe -k 30 960 ...`; timeout consumes
   the sole attempt, leaves any partial root VOID in place, and forbids rerun.
   Status: OPEN, UNANSWERED.
5. `OQ-G1-OUTCOME`: define honest terminal labels for completion, timeout,
   nonfinite/crash, no-signal, and trend-pass. Labels must not imply FER or
   qualification.
   Status: OPEN, UNANSWERED.

The authoring session did not answer these questions.

## 6. Freeze self-checks (docs-only)

- No decoder was invoked; no `--phase` of any kind; no prepare/verify.
- No CAL/VAL/parquet row reads.
- No `workspace/v72p2d5_*` creation or modification (read-only
  stat/name/size/mtime only, no hashing).
- No `.py` / existing `.md` / OpenSpec / decision-log / memory /
  `cycle_state.yaml` changes.
- Created ONLY `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`.
- No pytest (accepted suite evidence already `201 passed`).
- Before commit: re-stat all §1 roots (name/size/mtime identical; G2 and the
  proposed fresh G1 root absent); nine authorization keys remain false and
  `next_gate: G1_PACKET_REVIEW`; `git diff --numstat -- '*.py'` and
  `git diff --cached --numstat -- '*.py'` both empty; stage ONLY
  `G1_EXECUTION_PACKET_R1.md` (staged count 1).
