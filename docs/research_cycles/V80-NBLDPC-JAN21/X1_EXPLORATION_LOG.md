# X1 Successor EXPLORATION_LOG (EXPLORE_HEAVY batch, G-X1S) — APPEND-ONLY

- Cycle: V80-NBLDPC-JAN21, X1 successor entry.
- Acceptance ID: **G-X1S** (granted by conversation grant 2026-09-21, verbatim "授权 G-X1S", recorded in the top amendment note of `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md`; §7 signature block intentionally blank, flagged for administrative ratification after batch-end review).
- Date (UTC): 2026-09-21.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD `e038f3c520f673601d6dd753eb31ed9d02a5ac49`.
- Frozen contract: `X1_SUCCESSOR_ENTRY_PACKET.md` (§§2–8) + `X1_SUCCESSOR_ENTRY_PROMPT.md` + `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` + `X1_SUCCESSOR_ENTRY_PREEXEC.md` (Q0–Q6 PASS, G-D PASS).
- Runner: `comparison_bench/src/comparison_bench/cli/x1_arm_runner.py` (T-X1S-4; CLI-only invocation; NEVER `execute(bundle=dict)` with production bytes).

## Carried advisories (pre-execution review findings)

- **(R1) censored-arm read rule:** censored arms report fails-at-stop / blocks-at-stop — NEVER quote a censored arm's FER/f_eff as a 240-basis number. Censored-arm FER/f_eff are stop-point artifacts only; projection to 240 is FORBIDDEN.
- **(R4) production-invocation rule:** production invocation ONLY via the dual-flag CLI (`--execute-real --execution-authorized`) with the frozen exact bundle paths. 2M arms bind ONLY `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz`; 1M/1.5M arms bind ONLY `workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz` + `workspace/x1_bundles_7c1d4a2b/gamma_f03_pb.npz`.
- **(§9 fact) bundle-content correction:** `gamma_f03.npz` contains ALL THREE sources' keys (1M/1p5M/2M, verified by direct np.load) — the X1 assessment T2 "only 2M keys" detail was a wrong size-based inference; scientific conclusion unchanged (August-vintage keys are NOT reusable under the vintage ban; the runner's file-role gate prevents it).
- **Other carried rules:** `undetected` logged separately, NEVER merged into success; NEVER quote `f_super` as `f_eff` when FER > 0; NO pooling; f-margin IN vs N-count certifiability DISTINCT; 2M-only headline FORBIDDEN (generality headlines LEAD with 1M); `H_corr` CONDITIONAL on R1 §3A alignment + TRAIN split side; no `.ttbin` ever; `src/` frozen.

## Preflight (verbatim, recorded before first arm)

```
$ git rev-parse --abbrev-ref HEAD
formal-ir-v72p1-addendum-clean
$ git rev-parse HEAD
e038f3c520f673601d6dd753eb31ed9d02a5ac49
$ git status --porcelain
?? .codebuddy/
?? .workbuddy/memory/2026-09-21.md
?? comparison_bench/src/comparison_bench/cli/x1_arm_runner.py
?? comparison_bench/src/comparison_bench/cli/x1_bundle_build.py
?? comparison_bench/tests/test_x1_arm_runner.py
?? comparison_bench/tests/test_x1_bundle_build.py
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREEXEC.md
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PROMPT.md
$ git diff -- src/
(empty — no output)
```

- Dirt vs PREEXEC Q0: PREEXEC listed 7 untracked entries; now 11. Delta = `x1_arm_runner.py` + `test_x1_arm_runner.py` (T-X1S-4 additive runner + fake-only tests, built after PREEXEC) + `X1_SUCCESSOR_ENTRY_PREEXEC.md` itself (the record file). All additive; `git diff -- src/` EMPTY. Verdict: PASS.
- Bundle G-D re-verify (seconds): `PYTHONPATH=<root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.x1_bundle_build --mode verify --root workspace/x1_bundles_7c1d4a2b --r1-root workspace/r1_histogram_5e2a91c4` → `{"failures": [], "finding_2m": false, "wall_s": 0.293..., "rss_kib": 224068}`. Verdict: PASS.
- `ls workspace | grep '^x1_'` → only `x1_bundles_7c1d4a2b` (bundle INPUT root, not an arm output).

## Frozen 15-root list (generated BEFORE first arm; each proven absent immediately before its arm)

| # | arm | root |
|---|---|---|
| 1 | X1-2M-192 | workspace/x1_98be61fc |
| 2 | X1-2M-196 | workspace/x1_ebc2a354 |
| 3 | X1-2M-204 | workspace/x1_8997e889 |
| 4 | X1-2M-200 | workspace/x1_a8396d31 |
| 5 | X1-2M-208 | workspace/x1_e04f1f0a |
| 6 | X1-1.5M-191 | workspace/x1_174eaa87 |
| 7 | X1-1.5M-195 | workspace/x1_b3b7c34d |
| 8 | X1-1.5M-199 | workspace/x1_a94868ce |
| 9 | X1-1.5M-203 | workspace/x1_6a0c6a2c |
| 10 | X1-1.5M-207 | workspace/x1_079e4a14 |
| 11 | X1-1M-185 | workspace/x1_bfd2cc63 |
| 12 | X1-1M-189 | workspace/x1_538ec607 |
| 13 | X1-1M-193 | workspace/x1_db7abccd |
| 14 | X1-1M-197 | workspace/x1_ac8744f4 |
| 15 | X1-1M-201 | workspace/x1_214409f4 |

- UUID generation: `.venv/bin/python -c "import uuid; roots=[uuid.uuid4().hex[:8] for _ in range(15)]; ..."` → `98be61fc ebc2a354 8997e889 a8396d31 e04f1f0a 174eaa87 b3b7c34d a94868ce 6a0c6a2c 079e4a14 bfd2cc63 538ec607 db7abccd ac8744f4 214409f4` (assigned in frozen arm order above).
- Absence proof: `for u in <15 uuid8>; do test ! -e workspace/x1_$u && echo "absent ..."; done` → all 15 `absent` (verbatim in operator transcript). No `workspace/x1_<uuid8>` arm decode root exists.
- Repair path: no repair path used (so far; this line updated only if the ≤1 preregistered engineering repair+rerun is ever invoked).

---

## Per-arm entries (appended AS EACH ARM COMPLETES; frozen order)

### Arm 1 — X1-2M-192 (root workspace/x1_98be61fc) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 32** (bar 12 exceeded at block 32; projected NEVER — R1 read rule applies: the stop-point FER 0.40625 and f_eff 3.14418 are NOT 240-basis numbers and are NEVER quoted as such).
- Undetected: **0** (separate; never merged).
- Iters: min 11 / max 300 over 32 blocks. Wall: **770.2 s** total elapsed (cap 1800 s; per-decode ≤300 s held; no overrun rows). Peak RSS: **0.602 GiB** (<4 GiB).
- Own-H f_super / f_eff: **1.20000089 / 3.14418135** (own-basis H_corr[2M]=0.8333327179427281; f_eff is a stop-point artifact only — censored, not quotable as a 240-basis number).
- G-A: **FAIL** (13 > 12 at stop). G-B: **PASS** (f_super 1.2000 ≤ 1.3). G-C: **FAIL-expected** (N=32 < N_req=144; presentation ban held — no certifiability claim).
- Girth: **8** (recorded-not-gated); pins fc=0 + rank-full (rank=192) + twice-identical GATED PASS (pre-decode gate).
- Bundle: `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` key `2M` (frozen 2M role path; bound source label == arm source).
- Seeds/instance: `2026095601+idx` idx 0..31 drawn (stream `o1_blk:{seed}`); instance 2026092001 standalone `X1-2M-S192-standalone`.
- Anomaly: none (clean bar-12 early-stop; no infrastructure failure; no repair path used).
- Cumulative wall (arm elapsed): 770.2 s / 27000 s ceiling.

### Arm 2 — X1-2M-196 (root workspace/x1_ebc2a354) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 80** (bar 12 exceeded at block 80; projected NEVER — R1 read rule applies: stop-point FER 0.1625 and f_eff 2.00111 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 9 / max 300 over 80 blocks. Wall: **1186.6 s** total elapsed (cap 1800 s held). Peak RSS: **0.602 GiB** (<4 GiB).
- Own-H f_super / f_eff: **1.22343840 / 2.00111059** (own-basis H_corr[2M]=0.8333327179427281; stop-point artifact only).
- G-A: **FAIL** (13 > 12 at stop). G-B: **PASS** (1.2234 ≤ 1.3). G-C: **FAIL-expected** (N=80 < 144... N_req=188; ban held).
- Girth: **6** (recorded-not-gated); pins fc=0 + rank-full (rank=196) + twice-identical GATED PASS.
- Bundle: frozen 2M role path, key `2M`. Seeds/instance verbatim (idx 0..79 drawn); `X1-2M-S196-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 770.2 + 1186.6 = **1956.8 s** / 27000 s.

### Arm 3 — X1-2M-204 (root workspace/x1_8997e889) — COMPLETE, NON-CENSORED PASS

- Status: **COMPLETE** (verdict `PASS`; full 240 blocks; no repair).
- Fails/240: **2/240** (FER 0.008333). NOT censored (curve-relative monotone label deferred to batch analysis).
- Undetected: **0** (separate; never merged).
- Iters: min 8 / max 300 over 240 blocks. Wall: **967.8 s** (cap 1800 s held). Peak RSS: **0.602 GiB**.
- Own-H f_super / f_eff: **1.27031344 / 1.31019406** (own-basis H_corr[2M]; DISTINCT lines; single-source f_eff NEVER presented as certifiable).
- G-A: **PASS** (2 ≤ 12). G-B: **PASS** (1.2703 ≤ 1.3). G-C: **FAIL-expected** (N=240 < N_req=484; f-margin IN vs N-count certifiability DISTINCT).
- Girth: **6**; pins fc=0 + rank-full (rank=204) + twice-identical GATED PASS.
- Bundle: frozen 2M role path, key `2M`. Seeds/instance verbatim (idx 0..239); `X1-2M-S204-standalone`.
- Anomaly: none. FINDING-adjacent note (not a gate surprise): first G-A PASS of the batch (2M high-m passes route gate while lower-m 2M arms censored — per-arm report only, NO cross-m monotonicity inference).
- Cumulative arm-elapsed wall: 1956.8 + 967.8 = **2924.6 s** / 27000 s.

### Arm 4 — X1-2M-200-STANDALONE (root workspace/x1_a8396d31) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair). Construction label `X1-2M-S200-standalone` — STANDALONE per-m construct, DISTINCT from P1 nested leading-200 (never equated, never substituted).
- Fails-at-stop / blocks-at-stop: **13 / 163** (projected NEVER — R1 read rule: stop-point FER 0.07975 and f_eff 1.62856 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 8 / max 300 over 163 blocks. Wall: **1589.7 s** (cap 1800 s held; closest to budget so far, 88% of window). Peak RSS: **0.602 GiB**.
- Own-H f_super / f_eff: **1.24687592 / 1.62855552** (own-basis H_corr[2M]; stop-point artifact only).
- G-A: **FAIL** (13 > 12 at stop). G-B: **PASS** (1.2469 ≤ 1.3). G-C: **FAIL-expected** (N=163 < N_req=271; ban held).
- Girth: **8**; pins fc=0 + rank-full (rank=200) + twice-identical GATED PASS.
- Bundle: frozen 2M role path, key `2M`. Seeds/instance verbatim (idx 0..162 drawn).
- Anomaly: none (clean bar-12 stop; no repair). Cumulative arm-elapsed wall: 2924.6 + 1589.7 = **4514.3 s** / 27000 s.

### Arm 5 — X1-2M-208 (root workspace/x1_e04f1f0a) — COMPLETE, NON-CENSORED PASS (zero-failure)

- Status: **COMPLETE** (verdict `PASS`; full 240 blocks; no repair).
- Fails/240: **0/240** (FER 0.0). NOT censored (curve label deferred to batch analysis).
- Undetected: **0** (separate; never merged).
- Iters: min 7 / max 23 over 240 blocks (no 300-cap hits). Wall: **722.0 s** (cap held). Peak RSS: **0.643 GiB**.
- Own-H f_super / f_eff: **1.29375096 / 1.29375096** (FER=0 so f_eff==f_super; matches frozen f@208 1.29375096; f-margin IN, count-certifiability DISTINCT — N=240 < N_req=2298).
- G-A: **PASS** (0 ≤ 12). G-B: **PASS** (1.2938 ≤ 1.3). G-C: **FAIL-expected** (N=240 < 2298; ban held — zero-failure f_eff NEVER presented as certifiable/literature-comparable).
- Girth: **8**; pins fc=0 + rank-full (rank=208) + twice-identical GATED PASS.
- Bundle: frozen 2M role path, key `2M`. Seeds/instance verbatim (idx 0..239); `X1-2M-S208-standalone`.
- Anomaly: none. Note: 2M family closes with 2 PASS (204: 2/240; 208: 0/240) + 3 CENSORED (192/196/200) — per-arm report only, NO cross-m inference.
- Cumulative arm-elapsed wall: 4514.3 + 722.0 = **5236.3 s** / 27000 s.

### Arm 6 — X1-1.5M-191 (root workspace/x1_174eaa87) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 40** (projected NEVER — R1 read rule: stop-point FER 0.325 and f_eff 2.75821 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 12 / max 300 over 40 blocks. Wall: **905.8 s** (cap held). Peak RSS: **0.643 GiB**.
- Own-H f_super / f_eff: **1.20286350 / 2.75820787** (own-basis H_corr[1p5M]=0.8272902027770036; stop-point artifact only).
- G-A: **FAIL** (13 > 12 at stop). G-B: **PASS** (1.2029 ≤ 1.3). G-C: **FAIL-expected** (N=40 < N_req=148; ban held).
- Girth: **6**; pins fc=0 + rank-full (rank=191) + twice-identical GATED PASS.
- Bundle: §2.6-built `workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz` key `1p5M` (role path; bound label == arm source).
- Seeds/instance verbatim (idx 0..39); `X1-1.5M-S191-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 5236.3 + 905.8 = **6142.1 s** / 27000 s.

### Arm 7 — X1-1.5M-195 (root workspace/x1_b3b7c34d) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 63** (projected NEVER — R1 read rule: stop-point FER 0.20635 and f_eff 2.21399 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 10 / max 300 over 63 blocks. Wall: **987.5 s** (cap held). Peak RSS: **0.643 GiB**.
- Own-H f_super / f_eff: **1.22647220 / 2.21399244** (own-basis H_corr[1p5M]; stop-point artifact only).
- G-A: **FAIL**. G-B: **PASS** (1.2265 ≤ 1.3). G-C: **FAIL-expected** (N=63 < N_req=196; ban held).
- Girth: **6**; pins fc=0 + rank-full (rank=195) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1p5M`. Seeds/instance verbatim (idx 0..62); `X1-1.5M-S195-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 6142.1 + 987.5 = **7129.6 s** / 27000 s.

### Arm 8 — X1-1.5M-199 (root workspace/x1_a94868ce) — COMPLETE run, CENSORED result + BUDGET NOTE

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, terminal bar-12 status reached; no repair).
- Fails-at-stop / blocks-at-stop: **13 / 203** (projected NEVER — R1 read rule: stop-point FER 0.06404 and f_eff 1.55655 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 8 / max 300 over 203 blocks. Wall: **1825.7 s** elapsed vs 1800 s cap — BUDGET NOTE (see below). Peak RSS: **0.677 GiB** (<4 GiB).
- Own-H f_super / f_eff: **1.25008091 / 1.55655271** (own-basis H_corr[1p5M]; stop-point artifact only).
- G-A: **FAIL**. G-B: **PASS** (1.2501 ≤ 1.3). G-C: **FAIL-expected** (N=203 < N_req=288; ban held).
- Girth: **6**; pins fc=0 + rank-full (rank=199) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1p5M`. Seeds/instance verbatim (idx 0..202); `X1-1.5M-S199-standalone`.
- BUDGET NOTE (FINDING for batch-end review): total elapsed 1825.7 s exceeds the 1800 s per-arm window by ~25.7 s. The runner's wall gate is checked at loop-top (`clock() - t_start > X1_WALL_CAP_S`); the in-flight decode that hit bar-12 completed past the window, so the arm reached terminal bar-12 status rather than INCOMPLETE-wall. Per-decode ≤300 s held on every block (no overrun rows); RSS held. This is an in-flight-completion overshoot, NOT a wall-partial, NOT an infrastructure failure — no repair path invoked. Batch-end review adjudicates G-E for this arm.
- Cumulative arm-elapsed wall: 7129.6 + 1825.7 = **8955.3 s** / 27000 s.

### Arm 9 — X1-1.5M-203 (root workspace/x1_6a0c6a2c) — COMPLETE, NON-CENSORED PASS

- Status: **COMPLETE** (verdict `PASS`; full 240 blocks; no repair).
- Fails/240: **2/240** (FER 0.008333). NOT censored (curve label deferred to batch analysis).
- Undetected: **0** (separate; never merged).
- Iters: min 7 / max 300 over 240 blocks. Wall: **966.8 s** (cap held). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.27368961 / 1.31357024** (own-basis H_corr[1p5M]; DISTINCT lines; never certifiable-presented).
- G-A: **PASS** (2 ≤ 12). G-B: **PASS** (1.2737 ≤ 1.3). G-C: **FAIL-expected** (N=240 < N_req=546; margin-IN vs count DISTINCT).
- Girth: **8**; pins fc=0 + rank-full (rank=203) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1p5M`. Seeds/instance verbatim (idx 0..239); `X1-1.5M-S203-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 8955.3 + 966.8 = **9922.1 s** / 27000 s.

### Arm 10 — X1-1.5M-207 (root workspace/x1_079e4a14) — COMPLETE, NON-CENSORED PASS (top pinned at own corrected m_max)

- Status: **COMPLETE** (verdict `PASS`; full 240 blocks; no repair).
- Fails/240: **1/240** (FER 0.004167). NOT censored (curve label deferred to batch analysis).
- Undetected: **0** (separate; never merged).
- Iters: min 7 / max 300 over 240 blocks. Wall: **823.4 s** (cap held). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.29729832 / 1.31723863** (own-basis H_corr[1p5M]; DISTINCT lines; never certifiable-presented).
- G-A: **PASS** (1 ≤ 12). G-B: **PASS** (1.2973 ≤ 1.3 — inside f-margin by 0.0027). G-C: **FAIL-expected** (N=240 < N_req=5315 — matches frozen §2.1 expectation N=5315 at m_max 207; margin-IN vs count DISTINCT).
- Girth: **8**; pins fc=0 + rank-full (rank=207) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1p5M`. Seeds/instance verbatim (idx 0..239); `X1-1.5M-S207-standalone`.
- Anomaly: none. 1.5M family closes with 2 PASS (203: 2/240; 207: 1/240) + 3 CENSORED (191/195/199) — per-arm report only, NO cross-m inference.
- Cumulative arm-elapsed wall: 9922.1 + 823.4 = **10745.5 s** / 27000 s.

### Arm 11 — X1-1M-185 (root workspace/x1_bfd2cc63) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 33** (projected NEVER — R1 read rule: stop-point FER 0.39394 and f_eff 3.09063 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 14 / max 300 over 33 blocks. Wall: **724.1 s** (cap held). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.20536337 / 3.09062928** (own-basis H_corr[1M]=0.8012690084416184; stop-point artifact only).
- G-A: **FAIL**. G-B: **PASS** (1.2054 ≤ 1.3). G-C: **FAIL-expected** (N=33 < N_req=152; ban held).
- Girth: **6**; pins fc=0 + rank-full (rank=185) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1M`. Seeds/instance verbatim (idx 0..32); `X1-1M-S185-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 10745.5 + 724.1 = **11469.6 s** / 27000 s.

### Arm 12 — X1-1M-189 (root workspace/x1_538ec607) — COMPLETE run, CENSORED result

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 62** (projected NEVER — R1 read rule: stop-point FER 0.20968 and f_eff 2.23319 are NOT 240-basis numbers).
- Undetected: **0** (separate; never merged).
- Iters: min 10 / max 300 over 62 blocks. Wall: **1053.2 s** (cap held). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.22973877 / 2.23318675** (own-basis H_corr[1M]; stop-point artifact only).
- G-A: **FAIL**. G-B: **PASS** (1.2297 ≤ 1.3). G-C: **FAIL-expected** (N=62 < N_req=205; ban held).
- Girth: **6**; pins fc=0 + rank-full (rank=189) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1M`. Seeds/instance verbatim (idx 0..61); `X1-1M-S189-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 11469.6 + 1053.2 = **12522.8 s** / 27000 s.

### Arm 13 — X1-1M-193 (root workspace/x1_db7abccd) — COMPLETE run, CENSORED result + UNDETECTED FINDING

- Status: **CENSORED-bar12** (verdict `FAIL-early-stop`; run COMPLETE, no repair).
- Fails-at-stop / blocks-at-stop: **13 / 214** (projected NEVER — R1 read rule: stop-point FER 0.06075 and f_eff 1.54483 are NOT 240-basis numbers).
- Undetected: **1** — FIRST undetected hit of the batch (block 167, seed 2026095768, iters 33, wall 8.3 s; converged but x_hat != x). Logged SEPARATELY, counted inside gate-(a) fails (13 includes it, b2f-verbatim), NEVER merged into success. Batch-end review adjudicates.
- Iters: min 8 / max 300 over 214 blocks. Wall: **1662.9 s** (cap held, 92% of window). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.25411416 / 1.54483274** (own-basis H_corr[1M]; stop-point artifact only).
- G-A: **FAIL**. G-B: **PASS** (1.2541 ≤ 1.3). G-C: **FAIL-expected** (N=214 < N_req=313; ban held).
- Girth: **8**; pins fc=0 + rank-full (rank=193) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1M`. Seeds/instance verbatim (idx 0..213); `X1-1M-S193-standalone`.
- Anomaly: the undetected hit (above) — otherwise clean. Cumulative arm-elapsed wall: 12522.8 + 1662.9 = **14185.7 s** / 27000 s.

### Arm 14 — X1-1M-197 (root workspace/x1_ac8744f4) — COMPLETE, NON-CENSORED PASS

- Status: **COMPLETE** (verdict `PASS`; full 240 blocks; no repair).
- Fails/240: **3/240** (FER 0.0125). NOT censored (curve label deferred to batch analysis).
- Undetected: **0** (separate; never merged).
- Iters: min 7 / max 300 over 240 blocks. Wall: **1043.2 s** (cap held). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.27848956 / 1.33831050** (own-basis H_corr[1M]; DISTINCT lines; never certifiable-presented).
- G-A: **PASS** (3 ≤ 12). G-B: **PASS** (1.2785 ≤ 1.3). G-C: **FAIL-expected** (N=240 < N_req=668; margin-IN vs count DISTINCT).
- Girth: **8**; pins fc=0 + rank-full (rank=197) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1M`. Seeds/instance verbatim (idx 0..239); `X1-1M-S197-standalone`.
- Anomaly: none. Cumulative arm-elapsed wall: 14185.7 + 1043.2 = **15228.9 s** / 27000 s.

### Arm 15 — X1-1M-201 (root workspace/x1_214409f4) — COMPLETE, NON-CENSORED, EXPECTED G-B OUT (a result, not a stop)

- Status: **COMPLETE** (verdict `FAIL` on gate (b) only; full 240 blocks; no repair). Retained-frozen grid top above corrected m_max 200 — EXPECTED-OUT characterization, run and reported per the frozen contract.
- Fails/240: **0/240** (FER 0.0). NOT censored (curve label deferred to batch analysis).
- Undetected: **0** (separate; never merged).
- Iters: min 7 / max 29 over 240 blocks (no 300-cap hits). Wall: **686.8 s** (cap held). Peak RSS: **0.677 GiB**.
- Own-H f_super / f_eff: **1.30286496 / 1.30286496** (FER=0 so f_eff==f_super; own-basis H_corr[1M]; f_super > 1.3 by 0.00286 ⇒ G-B OUT as expected).
- G-A: **PASS** (0 ≤ 12). G-B: **FAIL (EXPECTED-OUT)** — a RESULT, not a stop (packet §2.2/§4: grid unchanged, interpretation expects OUT). G-C: **FAIL-expected** (f_super > 1.3 ⇒ N_req=inf; ban held — zero-failure f_eff NEVER presented as certifiable).
- Girth: **8**; pins fc=0 + rank-full (rank=201) + twice-identical GATED PASS.
- Bundle: §2.6-built role path, key `1M`. Seeds/instance verbatim (idx 0..239); `X1-1M-S201-standalone`.
- Anomaly: none. 1M family closes with 2 PASS (197: 3/240; 201: 0/240 with G-B EXPECTED-OUT) + 3 CENSORED (185/189/193) — per-arm report only, NO cross-m inference.
- Cumulative arm-elapsed wall: 15228.9 + 686.8 = **15915.7 s** / 27000 s ceiling (59% of ceiling; all 15 arms terminal).

---

## Batch close-out (all 15 arms terminal — no STOP triggered)

- Terminal tally: **6 COMPLETE non-censored** (2M-204 PASS, 2M-208 PASS, 1.5M-203 PASS, 1.5M-207 PASS, 1M-197 PASS, 1M-201 G-B-OUT-result) + **9 CENSORED-bar12** (2M-192, 2M-196, 2M-200S, 1.5M-191, 1.5M-195, 1.5M-199, 1M-185, 1M-189, 1M-193) + **0 INCOMPLETE-wall** + **0 budget-FAIL**. No arm resumed/continued. No repair path used — explicit line per prereg §8: **no repair path used**.
- Censored-arm R1 read rule restated: the 9 CENSORED arms' fails-at-stop/blocks-at-stop (13/32, 13/80, 13/163, 13/40, 13/63, 13/203, 13/33, 13/62, 13/214) and their stop-point FER/f_eff values are NOT 240-basis numbers and are NEVER quoted as such; projected NEVER.
- FINDINGS for batch-end review: (F-a) Arm 13 (X1-1M-193) undetected=1 (block 167, seed 2026095768, iters 33) — first/only undetected hit of the batch; isolated, never merged. (F-b) Arm 8 (X1-1.5M-199) elapsed 1825.7 s vs 1800 s window (+25.7 s in-flight-completion overshoot; terminal bar-12, not wall-partial; per-decode/RSS held). (F-c) Non-monotone cliff pattern per source (low-m CENSORED, high-m PASS on all three sources) — per-arm report only, NO cross-m monotonicity inference保持; curve synthesis is batch-analysis scope, not claimed here.
- Gate surprises: none beyond the EXPECTED-OUT (1M-201 G-B FAIL as frozen-expected). No G-D/G-E FAIL (subject to (F-b) adjudication). Zero `.ttbin` reads (no such code path in the runner). `undetected` never merged. `f_super` never quoted as `f_eff` (FER>0 arms report DISTINCT lines). No pooling. No science-input change (grid/seeds `2026095601+idx`/stream `o1_blk:{seed}`/instance 2026092001/bundles/gates/H basis/slope all verbatim; role paths per R4).
- Cumulative wall: **15915.7 s** (arm-elapsed sum) vs **27000 s** ceiling — HELD with 11084.3 s margin. Per-decode ≤300 s held on all 240×6 + stopped-block decodes (no overrun rows). RSS <0.68 GiB on every arm (<4 GiB).
- Next: ONE batch-end independent review (prereg §9), then main-thread acceptance. No operating-point selection. No FER/SKR/route/qualification/publication claim. Generality headlines LEAD with 1M; 2M-only headline FORBIDDEN.

> **Editorial correction 2026-09-22 (main-thread acceptance; additive per the append-only discipline, per batch-end review finding F-c).** A stray fragment ("144...") appears in one per-arm entry around line 92 of this log; the machine artifacts in all 15 arm roots are unaffected (verified by the batch-end review). The append-only discipline forbids editing the original line, so this note records the correction. No gate, number, or verdict is affected.
