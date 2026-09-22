# X1 Successor Entry — Pre-EXECUTE (2026-09-21) — RECORD ONLY, AUTHORIZES NOTHING

- Track: **EXPLORE** (synthetic only; **EXPLORE_HEAVY** cost annotation).
  This record is entry-evidence step (b) for the X1 successor entry gate
  (cycle V80-NBLDPC-JAN21, proposed Acceptance ID **G-X1S**).
  **RECORD-ONLY: it authorizes NOTHING and executes NO campaign arm.**
  No `.ttbin` was opened. No decoder/DE/graph kernel was called.
  Nothing was committed or pushed.
- Location note: packet §8 fixes the entry-evidence ITEMS (a)–(d) but does
  not fix a file location for the Pre-EXECUTE record itself; per the operator
  task it is written here:
  `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREEXEC.md`.
- Frozen contract: `X1_SUCCESSOR_ENTRY_PACKET.md` (§§1–8) +
  `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` (still `DRAFT_PENDING_AUTHORIZATION`,
  signature block BLANK) + `X1_SUCCESSOR_ENTRY_PROMPT.md`.
- Entry-evidence (a) pointer (Q6): `workspace/x1_bundles_7c1d4a2b/BUNDLE_BUILD_LOG.md`
  + `BUNDLE_VERIFY_LOG.md` (see Q6 below).

## Q0 — intended branch (verbatim)

```
$ git rev-parse --abbrev-ref HEAD
formal-ir-v72p1-addendum-clean
$ git rev-parse HEAD
e038f3c520f673601d6dd753eb31ed9d02a5ac49
$ git status --porcelain
?? .codebuddy/
?? .workbuddy/memory/2026-09-21.md
?? comparison_bench/src/comparison_bench/cli/x1_bundle_build.py
?? comparison_bench/tests/test_x1_bundle_build.py
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md
?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PROMPT.md
```

- Branch is `formal-ir-v72p1-addendum-clean` as expected. HEAD is `e038f3c5`
  (matches the last-push context given in the operator task).
- Dirt enumerated and EXPLAINED — exactly the 7 expected untracked entries,
  no other entry:
  - `?? .codebuddy/` — IDE scratch dir, unrelated to this cycle.
  - `?? .workbuddy/memory/2026-09-21.md` — agent scratch memory, unrelated.
  - `?? comparison_bench/src/comparison_bench/cli/x1_bundle_build.py` — the new
    additive T-X1S-1/T-X1S-2 module (entry-evidence (a) producer).
  - `?? comparison_bench/tests/test_x1_bundle_build.py` — its fake-only tests.
  - `?? docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md` /
    `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` / `X1_SUCCESSOR_ENTRY_PROMPT.md` —
    the frozen X1 successor entry packet family itself.
- Verdict: **Q0 PASS** (no other entry; any other entry would have been FAIL).

## Q1 — scoped cleanliness (verbatim)

```
$ git diff -- src/
(empty — no output)
$ git diff --stat
(empty — no output)
```

- `git diff -- src/` EMPTY: no frozen-source modification. Tracked tree is
  clean apart from the 7 enumerated untracked entries above (all additive:
  one new module, one new test file, three packet-family docs, two
  unrelated scratch dirs).
- Verdict: **Q1 PASS**.

## Q2 — arm-output absence (verbatim)

```
$ ls workspace | rg '^x1_'
x1_bundles_7c1d4a2b
$ ls -d workspace/x1_*
workspace/x1_bundles_7c1d4a2b
$ rg -n 'x1_bundles_' --glob '!docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_*' --glob '!results/**' --glob '!comparison_bench/outputs_comparison/**' --glob '!.git/**' .
./comparison_bench/tests/test_x1_bundle_build.py:150:    root = tmp_path / "x1_bundles_deadbeef"
./comparison_bench/src/comparison_bench/cli/x1_bundle_build.py:14:  file set under a fresh additive ``workspace/x1_bundles_<UUID8>/`` root.
./comparison_bench/src/comparison_bench/cli/x1_bundle_build.py:531:                    help="bundle root workspace/x1_bundles_<UUID8> "
```

- The ONLY `workspace/x1_*` hit is the bundle INPUT root
  `x1_bundles_7c1d4a2b` (entry-evidence (a) input, NOT an arm output).
  No `workspace/x1_<uuid8>` arm decode root exists.
- The `x1_bundles_` repo hits are only the new module/test's own internal
  references (a `tmp_path` fixture name, a docstring, a `--help` string).
- Verdict: **Q2 PASS**.

## Q3 — protected roots (verbatim)

```
$ find results -type f | wc -l; du -sb results
0
0	results
$ find comparison_bench/outputs_comparison -type f | wc -l; du -sb comparison_bench/outputs_comparison
1446
554423395	comparison_bench/outputs_comparison
```

- `results/`: 0 files / 0 B. `comparison_bench/outputs_comparison/`:
  1446 files / 554423395 B — IDENTICAL to the P3-A1-REVIEW item-10 snapshot
  (0 files/0 B and 1446 files/554423395 B; legacy permission-denied pytest
  dirs excluded identically — no new files, no overwrites).
- Verdict: **Q3 PASS**.

## Q4 — focused fake-only tests (verbatim)

```
$ PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" \
    comparison_bench/tests/test_x1_bundle_build.py \
    comparison_bench/tests/test_r1_histogram_rerun.py \
    comparison_bench/tests/test_p3_census_a1_align.py \
    comparison_bench/tests/test_p3_stage05_probe.py
collected 42 items
comparison_bench/tests/test_x1_bundle_build.py ...........               [ 26%]
comparison_bench/tests/test_r1_histogram_rerun.py .............          [ 57%]
comparison_bench/tests/test_p3_census_a1_align.py ...........            [ 83%]
comparison_bench/tests/test_p3_stage05_probe.py .......                  [100%]
======================== 42 passed, 1 warning in 22.15s ========================
```

- 11 + 13 + 11 + 7 = 42 passed, as expected. The single warning is the benign
  `PytestConfigWarning: Unknown config option: cache_dir` (repo-config
  interaction with `-p no:cacheprovider`, no test impact).
- Zero production decoder calls in tests; no `.ttbin` in tests (test-only
  fake paths explicitly passed).
- Verdict: **Q4 PASS**.

## Q5 — bundle dry-bind re-verified (verbatim)

```
$ PYTHONPATH=<root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.x1_bundle_build \
    --mode verify --root workspace/x1_bundles_7c1d4a2b --r1-root workspace/r1_histogram_5e2a91c4
{
 "failures": [],
 "finding_2m": false,
 "mode": "verify",
 "root": "workspace/x1_bundles_7c1d4a2b",
 "rss_kib": 224792,
 "wall_s": 0.28649800599669106
}
```

- `failures: []`, `finding_2m: false` — the seconds-scale dry-bind the
  consistency review required before T-X1S-2/T-X1S-4.
- Identity lines (from the re-verified `BUNDLE_VERIFY_LOG.md` §(i), unchanged
  by the rerun):
  - T2-1M [1M]: N 315504==JSON 315504 True; K_AB 2395==2395 True;
    K_B 1024==1024 True; built p_b vs COO colsum/N maxabs 0.0;
    H_L1+H_L2==H_plug err 0.0 ⇒ PASS
  - T2-1.5M [1p5M]: N 441487==JSON 441487 True; K_AB 2439==2439 True;
    K_B 1024==1024 True; built p_b vs COO colsum/N maxabs 0.0;
    H_L1+H_L2==H_plug err 0.0 ⇒ PASS
  - T2-2M [2M]: N 589461==JSON 589461 True; K_AB 2597==2597 True;
    K_B 1024==1024 True; built p_b vs COO colsum/N maxabs 0.0;
    H_L1+H_L2==H_plug err 0.0 ⇒ PASS
  - Bind gates (path-form, per source): 1M / 1p5M / 2M all bind PASS
    (g1 (32,1024) finite/nonneg/colsums=1; g2 (32,32,1024)
    cond-rowsums(axis=1)=1; p_b sum=1±1e-9).
  - F1 sibling-copy identity: 1M / 1p5M / 2M identical True ⇒ PASS.
  - 2M lineage (report-only): ΔH_L1=-0.000631756793718817,
    ΔH_L2=-0.000523191583527316, p_b L_inf=0.00019661427905427232,
    max-abs Δg1=0.05305388578789183, max-abs Δg2=1.0;
    materiality |ΔH|>0.01/plane OR p_b L_inf>0.001 ⇒ no finding.
- Rerun note: by module design (`run_verify`: "Verify a built bundle root
  read-only; writes the verify log") the rerun regenerated
  `BUNDLE_VERIFY_LOG.md` in place. Pre-rerun sha256 was
  `cc0c95c08576438476e66507d8115b1ab8d07bb4910964cc756d24177c6ceee5`;
  post-rerun diff vs the saved copy shows ONLY the wall/RSS line changed
  (`verify wall: 0.4 s; peak RSS: 223392 KiB (0.213 GiB)` →
  `verify wall: 0.3 s; peak RSS: 224792 KiB (0.214 GiB)`). All verdict
  content is byte-identical. No bundle npz was touched.
- Verdict: **Q5 PASS**.

## Q6 — entry-evidence (a) pointer

- `workspace/x1_bundles_7c1d4a2b/BUNDLE_BUILD_LOG.md` (T-X1S-1):
  bundle root `workspace/x1_bundles_7c1d4a2b` (fresh; absence proven
  immediately before creation: `not exists` == True); R1 root read-only;
  frozen `ChannelAdapter(fact_id="F03", …)` UNMODIFIED; wall 0.3 s,
  RSS 0.602 GiB, 1 CPU; decoder/DE/graph calls 0; `.ttbin` reads 0.
- `workspace/x1_bundles_7c1d4a2b/BUNDLE_VERIFY_LOG.md` (T-X1S-2,
  re-verified in Q5 above): ALL CHECKS PASS — no finding; wall 0.3 s,
  RSS 0.214 GiB, 1 CPU; decoder/DE/graph calls 0; `.ttbin` reads 0.
- F2 segregation statement (build log): the re-derived 2M factorization in
  `x1_gamma_f03r1_2M_verify.npz` is VERIFICATION-ONLY, never bound by any
  decode path; 2M decode arms bind ONLY the frozen
  `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`
  (+ `gamma_f03_pb.npz`) read-only.
- Source-id triple: `type2_1M_20260121_184040` / `type2_1p5M_20260121_183806` /
  `type2_2M_20260121_183657` with prefixes `1M` / `1p5M` / `2M`.

## Q-notes (recorded, not gates)

(i) F1 binding convention freeze — the bundle root carries
`x1_gamma_f03r1.npz` (all `{source}_*` keys: `{source}_gamma1_L1`,
`{source}_gamma2_L2condU1`, `{source}_p_b`) + sibling `gamma_f03_pb.npz`
(same `{source}_p_b` keys) so the frozen path-form bind works with zero
frozen-module change; verifier and runner use this ONE convention.

(ii) F2 freeze — the verification-only re-derived 2M factorization lives only
in `x1_gamma_f03r1_2M_verify.npz`, never bound by any decode path; 2M decode
arms bind ONLY the frozen `gamma_f03.npz` (+sidecar), NEVER refit.

(iii) The Δg2 max-abs = 1.0 observation at the delta-at-0 fallback cell
(zero-mass vintage support difference; frozen bars cover ΔH/p_b only) is
recorded for the batch-end review to adjudicate.

(iv) The campaign grant is NOT given by this record — the 15-arm
EXPLORE_HEAVY batch (≤1800 s/arm, ≤27000 s total) requires its own explicit
grant after this Pre-EXECUTE (prereg §7 signature / conversation-grant box,
still BLANK).

(v) Budget confirmation row (prereg §3, single bootstrap-free ceiling):
per-arm ≤ 1800 s; 15-arm total ≤ 27000 s; bundle build + verification
negligible seconds of numpy counted INSIDE the ceiling; per-decode terminal
≤ 300 s; per-`.ttbin`-read 0 authorized (any read STOP-BLOCKED); peak RSS
< 4 GiB; 1 CPU; 0 new decoder-kernel/DE/graph calls beyond the frozen
b2f/v28 arm procedure. Arm order per the prompt §6: (i) bundle verification
(G-D, DONE — Q5/Q6 above); (ii) X1-2M {192,196,204} ONCE (P2-overlap: consume
BY REFERENCE if P2 already ran any); (iii) X1-2M {200-STANDALONE, 208}
(200-STANDALONE ≠ P1 nested leading-200); (iv) X1-1.5M {191,195,199,203,207}
ascending; (v) X1-1M {185,189,193,197,201} ascending with m=201
EXPECTED-OUT on G-B (retained-frozen characterization, report OUT).

## Close-out

- Pre-EXECUTE verdict: **Q0–Q6 all PASS. No FAIL encountered.**
- No campaign arm was executed. No `.ttbin` was opened. Nothing was committed,
  pushed, or PR'd. The only file written outside `workspace/` temp is this
  record itself (plus the Q5 in-place verify-log regeneration, wall/RSS line
  only, inside the bundle root).
- This record does NOT grant the campaign. Next gate: explicit user grant in
  `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` §7, then execution under the frozen
  arm order above.

> **Grant update 2026-09-21 (supersedes Q-note (iv) above).** G-X1S was GRANTED by the main thread by conversation grant (verbatim "授权 G-X1S", recorded in the top amendment note of `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md`). The grant covers ONE bounded 15-arm batch under the frozen packet contract; the paperwork deviation (blank signature block) is flagged for administrative ratification after the batch-end review. Execution may now proceed per the prompt's frozen arm order (verify → 2M {192,196,204} → 2M {200S,208} → 1.5M ascending → 1M ascending with 201 EXPECTED-OUT on G-B).
