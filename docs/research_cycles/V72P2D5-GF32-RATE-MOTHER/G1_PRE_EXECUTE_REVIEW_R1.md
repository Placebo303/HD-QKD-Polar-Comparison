# G1 Pre-EXECUTE Review R1 — independent final review before authorization

- Role: independent Pre-EXECUTE reviewer for D5-G1. Did not write the G1 packet, the v72p2d5 implementation (`614aab9e`/`cf61ee63`), any prior D5/P0/G1 artifact, or any prior review. No implementer PASS, test count, or mapping accepted on faith; every row below re-derived from actual frozen packet, commit diffs, current source/tests, plus fresh operator evidence gathered under the frozen task packet (read-only except own basetemp + external probe, both removed).
- Baseline: repo `D:/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`, HEAD `6494b623629746821d7bf445c25068ae2225c09c`, docs-freeze `6494b623`, accepted implementation `cf61ee63f5b76b0223838717b1344e0e7c3867ee`, gate `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`.
- Task packet: `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_PREEXECUTE_REVIEW_R1_TASK_PACKET.md` (§1→§8 followed; any STOP would have been reported verbatim with no repair).
- Authorization: **false**. This review authorizes nothing, executes no G1, accepts no result, grants no scientific qualification, permits no G2. `G1_PRE_EXECUTE_REVIEW_PASS` (if given) only allows the main thread to separately ask the user for a one-attempt explicit authorization in a new message.
- VOID hygiene: retained `workspace/v72p2d5_g1/20260906_r1/` listed by entry names + file sizes/mtimes only for hygiene. No file inside that root was opened; no number from inside is used or cited anywhere below as evidence or to tune any rule. Call-count `440` cited exclusively from design §3 + core arithmetic.
- **G1 Pre-EXECUTE 评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。**

## 1. P01–P03 contract and provenance audit

| ID | Check | Verdict | Evidence locations |
|----|-------|---------|--------------------|
| P01-provenance | `4bf2682a` exactly frozen G1 execution packet; `d47e7da1`/`614aab9e`/`cf61ee63` documented roles + scoped manifests; `6494b623` exactly seven acceptance/freeze paths, no production code; current production G1 content == accepted `cf61ee63`; no real content diff outside accepted scope (numstat 0/0, porcelain CRLF only, no normalization) | PASS | `git show --stat 4bf2682a` = 1 file `G1_EXECUTION_PACKET_R1.md` (248 ins); `d47e7da1` = 5 files (`G1_PACKET_REVIEW_R1.md` + `openspec/changes/v72p2d5-g1-readiness-rework/{proposal,design,specs/spec,tasks}.md`); `614aab9e` = 3 files (core + 2 D5 tests); `cf61ee63` = 3 files (core + rate-mother test + readiness tasks.md); `6494b623` = 7 files (`AGENT_PROJECT_MEMORY.md`, `docs/decision-log.md`, `G1_IMPLEMENTATION_ACCEPTANCE_R1.md`, `G1_PRE_EXECUTE_PACKET_R1.md`, `G1_READINESS_CODE_REVIEW_R1.md`, `G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md`, `cycle_state.yaml`), no `.py`; `git diff --numstat`=0 lines, `git diff --cached --numstat`=0, `git status --porcelain`=1966 lines CRLF churn only (informational); `git diff cf61ee63 -- <core>` empty, `-- <2 tests>` empty; `git diff cf61ee63 --stat` = same 7 docs/state files only. OpenSpec actual name `v72p2d5-g1-readiness-rework` (packet prefix `v72p2d5-g1-readiness` is prefix only; resolved from `d47e7da1`, not guessed) |
| P02-contract | phase `g1`; key `g1_execution_authorized`; root `workspace/v72p2d5_g1/20260907_r2`; width 64; `f` 1.0 then 1.2; L1 49/59 L2 43/52; one natural-prefix max mother per level+`f`; graph seeds 2026090501/02; block seeds 2026090600..2026090699 100/`f`; oracle first 20/`f` diagnostic; historical GF32 cold max_iter 90 damping 1.0; 440 calls; Model-F fixed accepted root; L1-then-L2; 4 no-overwrite scalars; wall ≤900s; watchdog 960+30k; RSS known + `<2147483648`; one attempt after later explicit auth, attempt consumes auth, no retry/rerun/resume/tuning | PASS | Packet `G1_PRE_EXECUTE_PACKET_R1.md` L10–L27/L33–L35; core `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py` L52–L53 (graph seeds), L54–L55 prefixes, L59 `G1_SEEDS=range(2026090600,2026090700)`, L61 `G1_F=(1.0,1.2)`, L64 `G1_BLOCKS=100`, L66 `ORACLE_SUBSET=20`, L68 `G1_WIDTH=64`, L73–L74 K_MIN 59/52, L78 `G1_FORMAL_ROOT="workspace/v72p2d5_g1/20260907_r2"`, L80–L81 4 files, L85 Model-F root, L86 900.0, L89–L90 90/1.0, L91–L98 phases/auth keys, L2043–L2044/L2092/L2100 440 arithmetic, L2104–L2135 RSS sampling/peaks, L2149–L2152 wall/RSS gates, L2414–L2428 no-overwrite, L1999–L2002/L2170–L2172 mothers, L2084/L2163/L2645–L2665 L1→L2 order, L882–L885 auth gate; CLI `scripts/v72p2d5_gf32_rate_mother.py` L39–L43 file-path load, L75 phase choices, L87–L95 refusal; tests L2884–L2887/L772 rows, L299 seeds, L635/L2875 440 (own re-read of L50–L99/L941–L989/L2140–L2169/L2290–L2354 confirms) |
| P03-signal | signal exactly `zero nonfinite AND APP rates nondecreasing AND top APP exact count > 0 AND (top > low OR both == attempted)`; outcome precedence 7 labels in frozen order; `passed=true iff G1_TREND_PASS`; no 50%/90%, no oracle decision, no FER/leakage/key/qual/promotion/G2 | PASS | Packet L80–L88 (7 labels), L95–L101 (signal + no-threshold/oracle-diagnostic/no-claims); core L2139–L2160 `_classify_g1_outcome` (L2143 nonfinite, L2149–L2150 wall, L2151–L2152 RSS, L2153–L2157 counts+`mono and top>0 and (top>low or both==attempted)`, L2158–L2160 TREND_PASS else NO_SIGNAL_FAIL; L2141–L2142 `PRE_EXECUTION_BLOCKED`/`WATCHDOG_TIMEOUT_VOID` operator-only, never fabricated); `passed iff TREND_PASS` L2204 + L2663; acceptance L19 scope `implementation readiness only. No decoder/G1 result, no FER, no leakage, no key rate, no qualification, no G2 claim` |

Lifecycle initial (blocking STOP if deviated — all hold): all nine `*_execution_authorized` (structure/g0/g0_recovery/p0_cost/g1/g2/synthetic/real/formal) `false` (+`implementation_authorized` false); `scientific_promotion: false`; `p0_cost_result_accepted: true` + `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`; `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW`; `g1_accepted_implementation: cf61ee63f5b76b0223838717b1344e0e7c3867ee`; `g1_formal_root: workspace/v72p2d5_g1/20260907_r2`; `model_f_input_root: workspace/v72p2d5_model_f_input/20260907_r1`; `g1_unauthorized_output_disposition: VOID_RETAINED_IN_PLACE`; parent `workspace/v72p2d5_g1/` only `20260906_r1`; `20260907_r2` absent; `v72p2d5_g2` absent. Source: `cycle_state.yaml` (re-read) + operator `Test-Path False/False` + pre/post stats.

## 2. E01–E06 fresh executable checks (no G1 execution)

| ID | Exact command | Literal result | Verdict |
|----|---------------|----------------|---------|
| E01-compile | `python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py scripts/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_prepare_model_f_input.py` | `PY_COMPILE_EXIT=0` (covers core + sibling + both `scripts/v72p2d5*` D5 scripts: `v72p2d5_gf32_rate_mother.py 3755B`, `v72p2d5_prepare_model_f_input.py 5980B`) | PASS |
| E02-pytest | `python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/d5_g1_preexec_r1_5d5efdbc-159f-44f5-8083-94bd8712cab6 -q --tb=line` (one fresh unique basetemp under `workspace/`, cwd repo root) | `219 passed, 1 warning in 28.89s`; warning only `PytestConfigWarning: Unknown config option: cache_dir` (benign, pre-existing). Re-stat after: VOID 4 names/sizes/mtimes identical, `20260907_r2` False, `v72p2d5_g2` False, Model-F 752/208467 unchanged. Basetemp resolved `D:\Code\HD-QKD_Polar_Comparison\workspace\d5_g1_preexec_r1_...`, prefix-verified, `Remove-Item -Recurse -Force`, post `Test-Path False` | PASS |
| E03-RSS | unpatched direct `from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as m; v=m._rss_bytes()` + `ctypes` DWORD/HANDLE/BOOL/SIZE_T sizes | `VALUE=85778432`, `TYPE_IS_INT=True`, `GT0=True`; `DWORD 4 / HANDLE 8 / BOOL 4 / SIZE_T 8`; struct `_PMC` L958–L970 = 2×DWORD + 8×c_size_t ⇒ 72; three signatures L972 (`GetCurrentProcess.restype=HANDLE`) + L973–L977 (`GetProcessMemoryInfo.argtypes=[HANDLE,POINTER(_PMC),DWORD]`) + L978 (`restype=BOOL`) all before L982–L984 invocation; Unix `resource` path L941–L946 kept; `None`/0/fabrication would block — none observed (own re-read L941–L989 confirms) | PASS |
| E04-watchdog | binary stat + `& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 3 python -c "import time; time.sleep(10)"` | `timeout.exe Length 41752 LastWriteTime 2025/11/17 18:24:08 True`; `REHEARSAL_EXIT=124` (required 124 met; not the G1 command). Frozen future command verified character-for-character (NOT run — see §4) | PASS |
| E05-isolation | static audit of every `authorized=True` D5 synthetic call | PASS — `test_v72p2d5_gf32_rate_mother.py`: 97 `authorized=True` hits; other two files 0. TIS `test_TIS_static_authorized_synthetic_isolation` L3424 requires fake+out_dir+counts/p_b or allowlisted missing-isolation; SAFE A L3170/L3198–L3201 (unauthorized→`NotAuthorizedError`, empty tmp); SAFE B L3212/L3225–L3227/L3236 + L2388/L2280/L2319/L2420/L2489/L2660 (fake `FakeDecoder` L91–L102 + `_mffake_counts` L3163 + tmp `out_dir`, 4 files in tmp, formal snapshots unchanged L105–L130); SAFE C L3243/L3261–L3268/L3286 (absent-root BLOCKED, `entered==[]`); no authorized test binds `bind_historical_decoder` except via never-entered boom; formal roots only snapshot-compared; sentinel contract L3915–L3940 (`G1_SENTINEL_FIRST_CALL`, `len(seen)==1`, `(49,64)`+`prior[1]==32`, `rglob==[]`) + L3940–L3946 static contract (`spec_from_file_location` + `run_g1_phase` before `write_g1_evidence`) effective | PASS |
| E06-probe | external file `C:\Users\admin\AppData\Local\Temp\d5_g1_preexec_probe_e414b9e5-... \probe.py` (2908B, outside repo), cwd repo root, no `PYTHONPATH`, no `sys.path` insertion; synthetic G1 entry `authorized=True` + unique first-call sentinel + test-owned tmp out + **no** `counts_ab`/`p_b` | `PROBE_EXIT=0`, stderr empty; stdout literal: `SYS_PATH0='C:\Users\...\d5_g1_preexec_probe_...'` / `CWD='D:\Code\HD-QKD_Polar_Comparison'` / `REPO_ON_SYSPATH=False` / `IMPORT_BLOCKED_ModuleNotFoundError="No module named 'comparison_bench'"` / `CORE_EXISTS=True` / `CORE_LOADED=file-path` / `EXC_TYPE=RuntimeError` / `EXC_MSG='D5_G1_PREEXEC_R1_SENTINEL_e414b9e5-...'` / `EXC_IS_SENTINEL=True` / `CALLS=1` / `CALL0_H=(49, 64)` / `CALL0_PRIOR=(64, 32)` / `OUT_EMPTY=True` / `OUT_LIST=[]` / `G1_ABSENT=True` / `G2_ABSENT=True` / `PROBE_PASS`. Only keys/shapes inspected; no Model-F array values printed/retained. External dir outside-repo-verified, `Remove-Item -Recurse -Force`, post `Test-Path False`. Failure modes (sentinel unreached, calls≠1, historical bind, output file, formal-root change) none observed | PASS |

## 3. Frozen parameters, signal, outcomes, budgets, attempt semantics (verbatim)

- Immutable run contract (packet §4.1): phase `g1`; auth key `g1_execution_authorized`; impl `cf61ee63`; output root `workspace/v72p2d5_g1/20260907_r2/`; width 64; `f` 1.0 then 1.2; rows L1 49/59, L2 43/52; one natural-prefix max mother per level and `f`; graph seeds 2026090501/2026090502; ordered paired block seeds 2026090600..2026090699, 100 per `f`; oracle first 20 per `f`, diagnostic only; historical GF32, cold start, `max_iter=90`, damping 1.0; exactly 440 decoder calls; Model-F fixed accepted input root `workspace/v72p2d5_model_f_input/20260907_r1`; L1 then L2 even when L1 not exact; exactly four no-overwrite scalar files (`results.json`, `table.csv`, `report.md`, `execution_summary.json`); scientific operator wall gate `<=900 s`; process watchdog 960 s + 30 s kill grace; run peak RSS known and `<2147483648` bytes (`None` fails); one attempt only after later explicit user authorization; attempt, not success, consumes authorization; no retry/rerun/resume/tuning.
- Signal (packet §4.6): `zero nonfinite AND APP rates nondecreasing AND top APP exact count > 0 AND (top exact count > low exact count OR both counts == attempted)`.
- Outcome precedence (packet §4.5): 1 `G1_PRE_EXECUTION_BLOCKED` > 2 `G1_WATCHDOG_TIMEOUT_VOID` > 3 `G1_NONFINITE_OR_CRASH_BLOCKED` > 4 `G1_OVERRUN_900S` > 5 `G1_RESOURCE_OVERRUN` > 6 `G1_TREND_PASS` > 7 `G1_COMPLETED_NO_SIGNAL_FAIL`. Normal completed `passed=true iff G1_TREND_PASS`. No 50%/90% threshold, no oracle decision role, no FER/leakage/key-rate/qualification/promotion/G2 claim.

## 4. Live RSS value and ABI

- Live unpatched `_rss_bytes()` = `85778432`, `type(value) is int` True, `value > 0` True. `None`/zero/fabricated fallback would block — none observed.
- ABI: `DWORD 4`, `HANDLE 8`, `BOOL 4`, `SIZE_T 8`; `_PMC` 2×DWORD + 8×`c_size_t` ⇒ `sizeof==72` (`PMC_SIZEOF 72` literal in prior review; current struct identical per L958–L970 re-read). Three ctypes signatures assigned before invocation (L972/L973–L977/L978 → L982–L984). Wrong ABI would block — none observed.

## 5. Watchdog rehearsal and frozen-command comparison

- Binary: `C:\Program Files\Git\usr\bin\timeout.exe` exists, `Length=41752`, `LastWriteTime=2025/11/17 18:24:08`.
- Rehearsal (harmless, NOT G1): `& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 3 python -c "import time; time.sleep(10)"` ⇒ exit `124` as required.
- Frozen future command verified character-for-character (ABSOLUTELY NOT RUN):
```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```
Matches packet L33–L35 frozen block; cwd repo root; no flags/seeds/overrides/retries.

## 6. Full test command and literal summary

```text
python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/d5_g1_preexec_r1_5d5efdbc-159f-44f5-8083-94bd8712cab6 -q --tb=line
........................................................................ [ 32%]
........................................................................ [ 65%]
........................................................................ [ 98%]
...                                                                      [100%]
============================== warnings summary ===============================
..\..\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434
  D:\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434: PytestConfigWarning: Unknown config option: cache_dir
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
219 passed, 1 warning in 28.89s
```
Zero failures. Warning benign. Own basetemp prefix-verified and removed (`Test-Path False`).

## 7. Reachability probe output and why it cannot call the real decoder

- Literal probe stdout/stderr/exit: see E06 table (exit 0, stderr empty, `PROBE_PASS`, `CALLS=1`, `OUT_EMPTY=True`, `G1_ABSENT/G2_ABSENT=True`, unique sentinel `D5_G1_PREEXEC_R1_SENTINEL_<uuid>` as `RuntimeError`).
- Why real decoder unreachable in probe: sentinel `decode_fn` explicitly supplied, so `run_g1_synthetic` takes the `decode_fn if ... else bind_historical_decoder()` branch and never binds historical; sentinel raises on the very first decoder call (first G1 block L1 `(49,64)`, `prior (64,32)`) before any second call or any write (writes occur only after full scan returns); exception identity is the unique sentinel string, not a loader/path/data error (`MODEL_F_*` errors distinct); tmp output stays `[]`; accepted real Model-F input traversed the production file-path consumer (`_load_model_f_loader` L2324/L2341 `spec_from_file_location`, `_resolve_model_f_input_root` L2294) because `counts_ab`/`p_b` were `None`. No historical decoder bound at any point; history never imported for decoding.
- Probe minimization: only keys/shapes needed by validation inspected; no Model-F array values printed or retained. External probe dir + test output outside-repo-verified and removed.

## 8. Pre/post root and lifecycle comparison

- Pre: `workspace/v72p2d5_g1/` → `[20260906_r1]` (2026-09-07T02:35:32); VOID `20260906_r1/` → `execution_summary.json 267` / `report.md 146` / `results.json 2593` / `table.csv 126` (same mtimes); `20260907_r2` absent (False); `v72p2d5_g2` absent (False); P0 `[20260906_r1]`; G0 `[20260905_r2]`; G0-recovery `[20260906_r1]`; Model-F `[20260907_r1]` (752 + 208467); Structure `[20260905_r2]`. VOID content never read (names/sizes/mtimes only).
- Post (after E01–E06): names/sizes/mtimes character-identical to pre; both new G1/G2 roots still absent (False/False); all nine authorizations still false; `scientific_promotion: false`; `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW`; HEAD still `6494b623`; `diff --numstat` 0, `diff --cached` 0; scoped core/tests still equal `cf61ee63`; review basetemp + external probe both `Test-Path False`. Equality holds except review-owned temps gone (as required).
- VOID remains unchanged and numerically uncited; proposed G1 absent; G2 absent; no tracked/staged content change introduced.

## 9. Findings

- Blocking: none.
- Non-blocking (disclosed, not verdict-changing):
  1. Porcelain 1966 lines is known CRLF status churn; `diff --numstat`/`--cached` 0 authoritative for content — no normalization performed (correct).
  2. OpenSpec packet text `v72p2d5-g1-readiness` vs actual dir `v72p2d5-g1-readiness-rework` — resolved via `d47e7da1` per packet instruction; not a deviation.
  3. `sizeof(PROCESS_MEMORY_COUNTERS)==72` evidenced via field arithmetic (2×DWORD + 8×pointer-sized) + `PMC_SIZEOF 72` literal + DWORD/SIZE_T sizes; live struct is function-local `_PMC` with no module-level name — no fabrication.
  4. Operator outer wall vs stored entrypoint `wall_seconds` distinction remains Pre-RESULT business; entry timer stops pre-write by design (disclosed boundary).

## 10. Explicit did / did-not checklist

- Did: read frozen packet/acceptance/packet-review/readiness-review/addendum/cycle_state/current core (L50–L99/L941–L989/L2140–L2169/L2290–L2354)/CLI loader/OpenSpec name via `d47e7da1`; captured branch/HEAD/log/diffs/lifecycle/root snapshots pre+post; compiled core+sibling+both D5 scripts; ran exact three-file pytest with fresh `workspace/` basetemp + cleanup; called unpatched `_rss_bytes()` + ABI sizes; stat `timeout.exe` + harmless `-k 30 3` rehearsal (124); audited every `authorized=True` isolation path; ran outside-repo file-path Model-F reachability probe (sentinel once, tmp empty, roots absent) + cleanup; wrote ONLY this review file (uncommitted).
- Did NOT (all true): no CLI `--phase` of any kind (not even refusal probe); no production/historical decoder run or bind; no Model-F prepare/verify; no CAL/VAL/parquet/raw-row read; no read or citation of VOID-G1 numbers from inside; no create/delete/move/rename/overwrite/hash/normalize of any formal evidence root/file; no edit to any `.py`/existing `.md`/OpenSpec/`cycle_state.yaml`/decision-log/memory; no git write of any kind (no add/commit/push/reset/stash/checkout/clean/rebase/revert/amend/renormalize); no repair of findings; no request or manufacture of execution authorization; no run of frozen future `960 ... --phase g1` command; no print/retention of Model-F array values; no commit/push of this report; no `cycle_state.yaml` change.
- Test writes only to own basetemp (prefix-verified, removed); probe writes only to outside-repo temp dir (outside-verified, removed). Both verified by absolute path before deletion; only those paths deleted.
- Sole created durable file: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_REVIEW_R1.md` (this file). No commit, no push.

## 11. Verdict

`G1_PRE_EXECUTE_REVIEW_PASS`

(PASS means only that the main thread may separately ask the user for a one-attempt explicit authorization in a new message. PASS is not authorization, execution, result acceptance, scientific qualification, or G2 permission. G1 Pre-EXECUTE 评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。)
