# G1 Readiness Code Review R1 — independent read-only verdict

- Role: independent reviewer. Did not write `614aab9e` or `cf61ee63`; no implementer PASS, test count, or mapping accepted on faith. Every row re-derived from actual diff/current source plus allowed checks only.
- Under review (complete candidate): `d47e7da1` (review + OpenSpec), `614aab9e` (G1 readiness implementation), `cf61ee63` (Windows RSS ABI repair).
- Authorization: **false**. This review authorizes nothing, executes nothing, accepts no result, permits no G2. PASS means only `READY_FOR_G1_PRE_EXECUTE_PACKET`.
- VOID hygiene: retained `workspace/v72p2d5_g1/20260906_r1/` listed by name/size/mtime only; no number from inside used as evidence or to tune any rule. `440` cited from design §3 + code arithmetic only.

## 1. Baseline and provenance (§2)

| # | Check | Result | Basis |
|---|-------|--------|-------|
| 1 | `d47e7da1` exactly accepted review + four OpenSpec files | PASS | `git show --stat/name-status`: 5 files — `G1_PACKET_REVIEW_R1.md` (A) + `openspec/changes/v72p2d5-g1-readiness-rework/{proposal.md,specs/spec.md,design.md,tasks.md}` (A×4). No core/tests/production file. |
| 2 | `614aab9e` exactly core + two test files | PASS | `git show`: 3 files — `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py` (M) + `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (M) + `comparison_bench/tests/test_v72p2d5_model_f_input.py` (M). |
| 3 | `cf61ee63` exactly core + rate-mother test + readiness tasks | PASS | `git show`: 3 files — core (M) + `test_v72p2d5_gf32_rate_mother.py` (M) + `openspec/changes/v72p2d5-g1-readiness-rework/tasks.md` (M). |
| 4 | No production file outside D5 core changed | PASS | Three-commit file lists contain no `src/`, `experiments/`, `tools/`, `results/`, other `comparison_bench/src` modules, or other `scripts/`. `git log --oneline -3 -- scripts/v72p2d5_gf32_rate_mother.py` = `7c59d375/ce281b59/c6116276` (old, none of the three candidates). |
| 5 | Lifecycle: P0 cost accepted only, `next_gate: G1_PACKET_REVIEW`, all authorizations false, promotion false | PASS | `cycle_state.yaml`: `p0_cost_result_accepted: true` + `p0_cost_accepted_scope: COST_MEASUREMENT_ONLY`; `next_gate: G1_PACKET_REVIEW`; all 10 `*_authorized` keys false (`implementation/structure/g0/g0_recovery/p0_cost/g1/g2/synthetic/real/formal`); `scientific_promotion: false`. |
| 6 | Retained `20260906_r1` unchanged; proposed `20260907_r2` + G2 absent | PASS | Pre/post identical (see §8): parent only `20260906_r1` (2026/9/7 2:35:32); VOID four files 267/146/2593/126 bytes with identical mtimes; `20260907_r2` absent; `v72p2d5_g2` absent. No hashing of workspace evidence. |

A11 handoff (B1 provenance): `git show --stat/name-status 4bf2682a` = exactly 1 file `A docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md` (248 insertions). PASS, verified directly in this review.
A12 handoff (watchdog): `Test-Path "C:\Program Files\Git\usr\bin\timeout.exe"` = True (`Length=41752`, `LastWriteTime=2025/11/17 18:24:08`; VersionInfo fields empty, MSYS2-style). Existence stat only; `-k`/timeout semantics deferred to Pre-EXECUTE per frozen plan. PASS as handoff.

## 2. Requirements traceability (§3): D1–D6 / A01–A13

Source of items: `G1_PACKET_REVIEW_R1.md` §3/§4/§5. Code = current `v72p2d5_gf32_rate_mother.py`; tests = two D5 test files; spec = `v72p2d5-g1-readiness-rework` OpenSpec.

| Item | Code | Tests | OpenSpec | Verdict |
|------|------|-------|----------|---------|
| D1 fresh root | L78 `G1_FORMAL_ROOT = "workspace/v72p2d5_g1/20260907_r2"`; old string absent as G1 target (core `20260906_r1` hits only P0 L77 / G2 L79 / G0-recovery L105) | `test_G1R01_fresh_root_literal_and_old_barred` L3605 (`==".../20260907_r2"`, `"20260906_r1" not in G1_FORMAL_ROOT`, VOID snapshot len 4) | proposal §Decided/D1; design §1; spec Delta 1; tasks T1 | PASS |
| D2 RSS | `_rss_bytes` L941–989 (Unix `resource` kept L941–946; Windows ctypes fallback L950–989); sampling L2104–2106; peaks L2108–2135; gate L2151–2152 | `test_G1R02_unix_rss_path_preserved`; `test_G1R03_windows_rss_success_and_failure` L3630 (asserts 3 sigs pre-call); `test_G1R03R1_windows_rss_live_smoke` L3713 (unpatched `int>0` on win32) | design §2; spec Delta 2; tasks T2 + T2-R1 | PASS |
| D3 observability | per-f L2112–2124 (attempted/exact/rate/failure/syndrome/iter-total/iter-max/oracle/nonfinite/RSS); run L2126–2136 (mono/calls/nonfinite/peak) | `test_G1R04` (440), `test_G1R11` (identities/bounds incl. `<=2*MAX_ITER`) | design §3; spec Delta 3; tasks T3 | PASS (cap disclosure §4) |
| D4 writer | G1 L2496 + G2 L2581 `float(item["app_failure_fraction"])` direct; `_write_stage_evidence` L2417 no-overwrite pre-check | both-writers-missing-key-raise tests | design §5; spec Delta 5; tasks T5 | PASS |
| D5 guard | — (test-owned) | both `_snapshot_dir` (rate-mother L105–114; model_f_input L36–45) with `is_dir→AssertionError` + name/size/mtime; tmp demos `test_G1R13*` | design §6; spec Delta 6; tasks T6 | PASS |
| D6 reachability | `_load_model_f_loader`/`_resolve_model_f_input_root` file-path consumer (no sys.path); sentinel reaches first injected call; writes only after full scan | static + fake contract tests (SAFE A/B/C, TIS L3424); tmp empty + fresh roots absent asserts | design §7; spec Delta 7; tasks T7 | PASS (real probe deferred) |
| A01 fresh root | same as D1 | same as D1 + pre/post VOID stat equal | tasks T1 | PASS |
| A02 RSS | same as D2 | same as D2, green | tasks T2/T2-R1 | PASS |
| A03 aggregates | same as D3; 440 = 100·2·2+20·2·1 (L2092 `+=2`, L2100 `+=1`, G1 100/20×2f) | identity/bound/440 asserts green | tasks T3 | PASS |
| A04 writers | same as D4; G2 grading/schema otherwise unchanged | raise tests green | tasks T5 | PASS |
| A05 guard | same as D5 | 4-state scratch exercise literal (§6) | tasks T6 | PASS |
| A06 sentinel | same as D6 | contract tests green, no real-root read | tasks T7 | PASS |
| A07 lifecycle-safe | `_require_authorized` + `_require_decode_fn` gates | fake decoder L91 + `_mffake_counts` L3163 + tmp out_dir + formal-snapshot asserts | tasks T8 | PASS |
| A08 suite green | — | focused 25 passed; full 189 passed (see §7) | tasks T8 | PASS |
| A09 auth/roots | — | `*_authorized` false, promotion false, `next_gate` unchanged; `20260907_r2`/G2 absent pre/post | tasks T8 | PASS |
| A10 prohibitions | — | no decoder/`--phase`/prepare/verify/CAL-VAL-parquet except deferred D6 load (not run) | proposal Non-Goals | PASS |
| A11 `4bf2682a` single file | — (provenance) | — | §1 row | PASS (direct) |
| A12 watchdog binary | — (provenance) | — | OQ-G1-WATCHDOG | PASS (existence direct; semantics → Pre-EXECUTE) |
| A13 outcome wiring | `run_g1_phase` L2204 + `run_g1_synthetic` L2663 `passed == (outcome==TREND_PASS)`; entry wall L2649→L2655 pre-write reclassify L2657 | signal/precedence tests green incl. 0,0→fail | design §4; spec Delta 4; tasks T4 | PASS |

Counts: D 6/6 PASS; A 13/13 PASS; 0 FAIL; 0 NOT_VERIFIABLE.

## 3. Correctness audit (§4): C1–C8

- **C1 root/no-overwrite — PASS.** `G1_FORMAL_ROOT` exactly `workspace/v72p2d5_g1/20260907_r2` (L78). `20260906_r1` never a G1 production target (G1 asserts exclude it; VOID referenced only as snapshot variable `void_root` + P0/G2/G0-recovery own constants). `_write_stage_evidence` L2417–2419 raises `FileExistsError` before any `open`. Tests never use default G1 root on authorized path (all authorized synthetics pass explicit `out_dir=tmp`; formal roots only snapshot-compared).
- **C2 real Windows RSS ABI — PASS.** Unix path intact (L941–946). Struct: two DWORD (`cb`, `PageFaultCount`) + eight `c_size_t` (L959–970); live `sizeof==72` literal `PMC_SIZEOF 72`. Three signatures set before invocation: L972 `GetCurrentProcess.restype=HANDLE`, L973–977 `GetProcessMemoryInfo.argtypes=[HANDLE,POINTER(_PMC),DWORD]`, L978 `restype=BOOL`; call L982–984. Returns current-process `WorkingSetSize` (L987), not peak/tree. False/unavailable/exception → `None` (L985–989). Fake adequacy: `_SigFn` records `argtypes/restype` at call (L3648–3650); `_gpi_ok` asserts all three non-None at call time (L3661–3663) plus post-call exact-type/seen checks (L3675–3683). Removing any one signature fails. Not assignment-only.
- **C3 sampling/peak — PASS.** One `_rss_bytes()` after every completed APP block, after paired oracle call (L2082–2106: block→`_run_layered_block(t<oracle_subset)`→counters→L2104 sample). Frozen G1 = 200 samples (100×2 f). Per-f peak = max non-None (L2108–2111). Run peak = None if any required sample None (L2127–2128), else max of per-f peaks (L2132–2135); sampled-maximum lower-bound, no tree claim. `>=2GiB`/`None` → `G1_RESOURCE_OVERRUN` (L2151–2152), blocks pass. Thrown decoder exception propagates (no catch in `_run_rate_scan`); no false peak/evidence bundle manufacturable.
- **C4 aggregates — PASS with disclosure.** Per-f computed from correct record fields (L2086–2103: `app_exact/app_syndrome_ok/iterations/finite/oracle_*`). Persisted in JSON/CSV (L2488–2569: 13-column head incl. syndrome/iter/RSS/nonfinite). Arithmetic: attempted 100 each; oracle subset 20 each; total 440; failure identity `1-rate` (L2116); counts bounded by construction; no raw symbols/beliefs/priors/per-block samples persisted. Disclosure: `app_iterations_max<=180` is **test-asserted** (`<=2*MAX_ITER`), not code-clamped — `_run_layered_block` sums `it1+it2` (L1322) with no decoder-return clamp; `MAX_ITER=90` only binds the historical decoder kwargs. Do not overclaim runtime validation of that bound.
- **C5 signal/outcome — PASS.** Precedence in `_classify_g1_outcome` L2143–2160 is P3 nonfinite → P4 wall>900 → P5 RSS → P6 TREND_PASS → P7 NO_SIGNAL_FAIL (first match wins). Truth table (§5) all match incl. boundaries. `passed iff TREND_PASS` at both `run_g1_phase` L2204 and post-reclassify `run_g1_synthetic` L2663. Timer: `run_g1_synthetic` auth L2648 → entry L2649 → Model-F load L2650 → prepare L2651 → bind L2652 → decode L2653 → outer wall L2655 → reclassify L2657 → write L2665; inner `run_g1_phase` t_start L2168 → wall L2187 pre-write. Remaining distinction from operator outer wall disclosed per design §4 (evidence-write/startup excluded; outer >900 s overrides at Pre-RESULT). Exceptions fail-loud; `G1_PRE_EXECUTION_BLOCKED`/`G1_WATCHDOG_TIMEOUT_VOID` never fabricated as normal four-file results (operator-only by comment L2141–2142 + no manufacture path).
- **C6 writers — PASS.** G1 + G2 both `float(item["app_failure_fraction"])` (L2496/L2581); missing key raises `KeyError` (no fallback). G2 grading/schema otherwise unchanged. G1 four files carry recompute fields (per-f counts/rates/RSS + run mono/nonfinite/calls/peak/wall/outcome). No-overwrite retained.
- **C7 guard depth — PASS.** Both helpers fail on any direct child dir (rate-mother L109–112; model_f_input L40–43) while retaining top-level name/size/mtime (L113–114 / L44–45). Independent scratch exercise (outside formal roots): absent→absent None (pass); present-flat dict (pass); present→new nested `AssertionError` (fail); absent→created nested `AssertionError` (fail). Scratch removed only. No recursive hashing.
- **C8 reachability/isolation — PASS.** Static/fake tests use injected arrays (`_mffake_counts` 1024×1024), `FakeDecoder` (L91–102), tmp output. No unit test reads accepted real Model-F artifact. SAFE A (unauthorized→`NotAuthorizedError`, empty tmp), B (authorized fake reaches runner, 4 files in tmp, formal unchanged), C (absent-root BLOCKED, empty tmp) + TIS static isolation (L3424) effective. No test-level `authorized=True` synthetic binds production decoder or formal root. Real external-file probe deferred to Pre-EXECUTE; not performed here (correct).

## 4. Live RSS, ABI/layout, fake-test adequacy

- Live unpatched `_rss_bytes()` literal: `85860352`, `type is int True`, `>0 True`. Not None.
- Layout: `DWORD 4`, `HANDLE 8`, `BOOL 4`, `SIZE_T 8`, `PMC_SIZEOF 72`. Matches 64-bit `PROCESS_MEMORY_COUNTERS` (2×DWORD + 8×pointer-sized).
- Signatures: L972/L973–977/L978 all assigned before L982–984 invocation.
- Fake adequacy: sufficient — call-time `assert argtypes/restype is not None` (×3) plus post-call exact-identity + `seen` ordering checks; any single signature removal fails.

## 5. Sampling count / peak / None semantics

200 RSS samples on frozen G1 (100 blocks × 2 f, one per completed APP result after paired oracle). Per-f peak = max available; run peak = max of per-f peaks only when every required sample known; any `None` → run `None` → `G1_RESOURCE_OVERRUN`, never pass. `>=2147483648` → same. Thrown exception aborts fail-loud with no peak/evidence.

## 6. Signal/outcome truth table (direct `_classify_g1_outcome`, hand-built per_f, attempted=100)

| Input (low,top,mono,nonfinite,wall,peak) | Literal return |
|---|---|
| 0,0,T,0,5.0,1000 | `G1_COMPLETED_NO_SIGNAL_FAIL` |
| 10,20,T,0,5.0,1000 | `G1_TREND_PASS` |
| 100,100,T,0,5.0,1000 | `G1_TREND_PASS` |
| 50,50,T,0,5.0,1000 | `G1_COMPLETED_NO_SIGNAL_FAIL` |
| 90,20,F,0,5.0,1000 (decreasing) | `G1_COMPLETED_NO_SIGNAL_FAIL` |
| 90,100,T,1,5000,3GiB | `G1_NONFINITE_OR_CRASH_BLOCKED` (overrides wall/RSS/signal) |
| 90,100,T,0,901,3GiB | `G1_OVERRUN_900S` (overrides RSS/signal) |
| 90,100,T,0,10,None | `G1_RESOURCE_OVERRUN` |
| 90,100,T,0,10,2GiB | `G1_RESOURCE_OVERRUN` |
| 90,100,T,0,10,3GiB | `G1_RESOURCE_OVERRUN` |
| 90,100,T,0,900.0,2GiB-1 | `G1_TREND_PASS` (eligible boundary) |

All-zero cannot pass; saturated 1.0,1.0 passes; flat <1.0 fails.

## 7. Schema and writer audit

G1 `results.json`/`table.csv`/`report.md`/`execution_summary.json` carry per-f `attempted/app_exact_count/app_exact_rate/app_failure_fraction/oracle_exact_count/app_syndrome_ok_count/app_iterations_total/app_iterations_max/oracle_syndrome_ok_count/oracle_iterations_total/nonfinite_count/peak_rss_bytes` + run `monotonic/crashes/nonfinite/decoder_calls/peak_rss_bytes/wall_seconds/outcome/passed`. CSV head 13 columns (L2564–2568). Fail-loud on missing `app_failure_fraction` both writers. G2 schema/grading unchanged except same fail-loud line.

## 8. Test execution (unique basetemp, `-p no:cacheprovider`)

- `py_compile` core + both D5 scripts + CLI: `PY_COMPILE_EXIT:0`.
- Focused: `pytest -p no:cacheprovider --basetemp="workspace/d5_g1_review_r1_26522acd-..." test_v72p2d5_gf32_rate_mother.py -k "G1R01..G1R17 or TIS_static or T1_23 or M19 or M20 or M21"` → `25 passed, 132 deselected, 1 warning in 2.05s`.
- Full: same basetemp, both `test_v72p2d5_gf32_rate_mother.py + test_v72p2d5_model_f_input.py` → `189 passed, 1 warning in 13.59s`.
- Warning: `PytestConfigWarning: Unknown config option: cache_dir` — benign, pre-existing.
- "Three-file" note: repo contains exactly 2 `test_v72p2d5*` files; tasks allowlist = core + 2 test files = 3 files; dual-file 189-pass run is the full D5 scope. Non-blocking terminology clarification.
- Basetemp removed after exact resolved-path + prefix validation (`REMOVED_BASETEMP`, post `Test-Path False`). Guard scratch likewise removed.

## 9. Pre/post root snapshots

- Pre: `workspace/v72p2d5_g1/` → `[20260906_r1]`; `20260906_r1/` → `execution_summary.json` 267 B / `report.md` 146 B / `results.json` 2593 B / `table.csv` 126 B (mtimes 2026-09-07T02:35:32); `20260907_r2` absent; `v72p2d5_g2` absent.
- Post: byte-identical names/sizes/mtimes; both proposed/absent roots still absent. Equality holds.

## 10. Commands run and explicitly not run

- Ran: `git show --stat/name-status` (d47e7da1/614aab9e/cf61ee63/4bf2682a); `git log --oneline` (scripts scope); `cycle_state.yaml`/core/OpenSpec/test source reads; `Get-ChildItem`/`Test-Path`/stat listings (pre/post); `sys.path`-anchored unpatched `_rss_bytes()` + `sizeof` + line-number prints; 11-group `_classify_g1_outcome` hand-dict calls; guard 4-state scratch exercise + removal; `py_compile`; focused + full `pytest -p no:cacheprovider --basetemp workspace/...`; resolved-path basetemp/scratch removals; `Test-Path timeout.exe` stat.
- Explicitly NOT run (all true): no decoder invocation; no `--phase` of any kind (not even refusal probe); no Model-F prepare/verify; no CAL/VAL/parquet/raw-row read; no read of real Model-F artifact contents; no write/delete/move/rename/copy/hash/normalization under any formal root; no edit to any `.py`/existing `.md`/OpenSpec/state/decision-log/memory; no git write of any kind; no real external-file probe (deferred to Pre-EXECUTE); truth table never touched `run_g1_phase`/`run_g1_synthetic`/production decoder.

## 11. Findings

Blocking: none.
Non-blocking (disclosed, not verdict-changing):
1. `app_iterations_max<=180` is test-enforced, not code-clamped (arbitrary `decode_fn` could exceed; frozen G1 fake returns 1/block).
2. `three-file D5 suite` = core + 2 test files per allowlist; pytest scope is the 2 test files (189 tests).
3. Watchdog `timeout.exe` functional/`-k` semantics remain Pre-EXECUTE work; only existence stat confirmed here.
4. Operator outer wall vs stored `wall_seconds` distinction remains Pre-RESULT business; code correctly stops timer pre-write.

## 12. Verdict

`G1_READINESS_CODE_REVIEW_PASS`

(Ready only for a separate Pre-EXECUTE packet/review. Authorizes nothing, executes nothing, permits no G2.)
