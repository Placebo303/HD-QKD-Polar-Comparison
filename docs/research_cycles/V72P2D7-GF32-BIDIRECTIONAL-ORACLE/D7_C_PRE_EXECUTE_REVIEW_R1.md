# D7-C pre-EXECUTE review R1

Verdict: D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION

## 0. Scope and independence

- Independent pre-EXECUTE review of D7-C at HEAD `ca00b234` on branch
  `formal-ir-v72p1-addendum-clean`, against
  `D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md` §8
  and `D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_A1_TASK_PACKET.md`
  §A1.4 (A1 wins on conflict), `D7_C_PREREG_R1.md`,
  `D7_C_EXECUTION_PACKET_R1.md`, `cycle_state.yaml`, the OpenSpec change
  `openspec/changes/v72p2d7-gf32-bidirectional-oracle/`, and
  `D7_C_IMPLEMENTATION_REVIEW_R1.md`.
- Reviewer is a separate agent instance from the planner, implementer and
  implementation reviewer. Every probe group ran as its own shell command; raw
  outputs are quoted verbatim below.
- Zero scientific decoder call, zero Model-F binary content read (metadata:
  names/sizes/mtime only), zero UUID, zero authorization flip, zero
  production/code/doc/OpenSpec edits, zero commits and zero push.
- The only repository write is this document. Probe scratch lives in
  `/tmp/opencode/d7c_pre_exec_r1/`; every pytest run used a fresh basetemp under
  `/tmp` with `-p no:cacheprovider`.

## 1. Branch / commit / dependency evidence

```text
$ git rev-parse HEAD
ca00b2343a02891a12048e637cc42414dd0aef47
$ git branch --show-current
formal-ir-v72p1-addendum-clean
$ git merge-base --is-ancestor 212f69ba HEAD; echo $?
0
$ git log --oneline -6
ca00b234 docs(d7-c): independent implementation review (R1+A1, no execution)
391fc6b0 feat(d7-c): bidirectional oracle harness, tests, runner (R1+A1 frozen, fake-qualified, no execution)
0c304875 docs(d7-c): freeze bidirectional oracle OpenSpec, prereg, execution packet (R1+A1, no code, no execution)
86f6baf6 docs(d7-b): freeze belief-provenance correction proposal before D7-C
212f69ba docs(d7-b): classify early-exit soft-belief semantics and next route
4dec0e5c docs(d7-b): accept WSL R2 hard-decision calibration with disclosed limits
$ git diff --name-only 86f6baf6..HEAD
comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_bidirectional_oracle.py
comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py
docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/D7_C_EXECUTION_PACKET_R1.md
docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/D7_C_IMPLEMENTATION_REVIEW_R1.md
docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/D7_C_PREREG_R1.md
docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/cycle_state.yaml
openspec/changes/v72p2d7-gf32-bidirectional-oracle/design.md
openspec/changes/v72p2d7-gf32-bidirectional-oracle/proposal.md
openspec/changes/v72p2d7-gf32-bidirectional-oracle/specs/gf32-bidirectional-oracle/spec.md
openspec/changes/v72p2d7-gf32-bidirectional-oracle/tasks.md
scripts/v72p2d7_gf32_bidirectional_oracle.py
$ git status --porcelain -- openspec/changes/v72p2d7-gf32-bidirectional-oracle docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE
(no output; rc 0)
```

- Phase-P commit `86f6baf6` precedes both D7-C commits
  (`0c304875` planning, `391fc6b0` implementation, then `ca00b234` review).
  `212f69ba` is an ancestor of HEAD (rc 0).
- Scoped OpenSpec/cycle paths are clean at review time.
- The D7-C source/test/script files have zero worktree diffs and zero status
  lines; the unrelated pre-existing dirty entries (~1965, mostly CRLF) are
  untouched by this review.

Predecessor verdicts in `cycle_state.yaml`:

```text
$ rg -n "predecessor_verdict|predecessor_layer_interface_verdict|..." docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/cycle_state.yaml
6:d7c_execution_authorized: false
7:decoder_executed: false
8:result_created: false
9:formal_execution_authorized: false
10:synthetic_execution_authorized: false
11:real_execution_authorized: false
14:predecessor_verdict: D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS
15:predecessor_layer_interface_verdict: D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING
18:r1d_state: R1D_PAUSED_PENDING_DECODER_CERTIFICATION_AND_EASY_REGIME
19:g1_authorized: false
20:g2_authorized: false
21:layer_interface_implementation: DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP
22:next_gate: D7_C_IMPLEMENTATION_AND_REVIEWS
```

Both required predecessor verdicts are recorded (lines 14–15). Objective and
nonclaim boundaries (`D7_C_PREREG_R1.md` §12, proposal `May not establish`) are
consistent with the single-layer diagnostic scope.

## 2. Exact 128 matrix and thresholds

Frozen dry-run from the repository cwd. Bare `python` is absent from the default
PATH in this WSL shell (rc 127, no script executed), so the command was run with
the same venv-on-PATH adapter documented for the accepted D7-B R2 execution
(`~/.venvs/hd-qkd-polar-comparison/bin`):

```text
$ PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" python scripts/v72p2d7_gf32_bidirectional_oracle.py --dry-run
(129 output lines: 1 header + 128 identities; rc 0)
head:
calls=128 conditions=['L1_MARGINAL', 'L1_ORACLE_U2', 'L2_MARGINAL', 'L2_ORACLE_U1'] budget=128
1 L1_MARGINAL 2026091300 1.0 L1 49
2 L1_ORACLE_U2 2026091300 1.0 L1 49
3 L2_MARGINAL 2026091300 1.0 L2 43
tail:
125 L1_MARGINAL 2026091315 1.2 L1 59
126 L1_ORACLE_U2 2026091315 1.2 L1 59
127 L2_MARGINAL 2026091315 1.2 L2 52
128 L2_ORACLE_U1 2026091315 1.2 L2 52
$ python scripts/v72p2d7_gf32_bidirectional_oracle.py --dry-run
/bin/bash: line 1: python: command not found        (EXIT=127)
```

Programmatic verification of every one of the 128 rows against the frozen order
`for f in [1.0, 1.2]: for seed in 2026091300..2026091315: L1_MARGINAL,
L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1`:

```text
MATRIX_OK: 128 identities, frozen order f[1.0,1.2] x seeds 2026091300..2026091315 ascending x conditions ['L1_MARGINAL', 'L1_ORACLE_U2', 'L2_MARGINAL', 'L2_ORACLE_U1']
boundary call1= ['1', 'L1_MARGINAL', '2026091300', '1.0', 'L1', '49']  call64= ['64', 'L2_ORACLE_U1', '2026091315', '1.0', 'L2', '43']  call65= ['65', 'L1_MARGINAL', '2026091300', '1.2', 'L1', '59']  call128= ['128', 'L2_ORACLE_U1', '2026091315', '1.2', 'L2', '52']
```

Frozen constants in prereg and module (selected lines):

```text
prereg: "Block seeds: `2026091300..2026091315`" (L90); table `| 1.0 | 49 | 43 |`, `| 1.2 | 59 | 52 |` (L158-159);
        "per-call watchdog `120 s`" (L238); "stored scientific wall `<= 1500 s`" (L239); "outer GNU timeout `1800 s`, kill grace `30 s`" (L240);
        "RSS must stay `< 2 GiB` (`2 * 1024**3` bytes)" (L245)
module: L60: L1_ROWS = {1.0: 49, 1.2: 59}; L61: L2_ROWS = {1.0: 43, 1.2: 52}; L62: ROWS = {"L1": L1_ROWS, "L2": L2_ROWS}
        L64: BLOCK_SEEDS = tuple(range(2026091300, 2026091316)); L83: MAX_CALLS = 128
        L84: PER_CALL_WATCHDOG_S = 120.0; L85: STORED_WALL_LIMIT_S = 1500.0
        L86: OUTER_WATCHDOG_S = 1800.0; L87: OUTER_GRACE_S = 30.0; L88: RSS_LIMIT_BYTES = 2 * 1024**3
```

11 terminals and 4 strata thresholds, module vs prereg §10:

```text
TERMINALS_MATCH: 11 exact strings and priority order identical
prereg section-10 list == module TERMINALS tuple (L95-107):
D7_C_PRE_EXECUTION_BLOCKED, D7_C_WATCHDOG_TIMEOUT_VOID, D7_C_NONFINITE_OR_CRASH_BLOCKED,
D7_C_RESOURCE_OVERRUN, D7_C_INCOMPLETE_CALL_MATRIX, D7_C_BIDIRECTIONAL_DEPENDENCE,
D7_C_L1_DEPENDS_ON_U2, D7_C_L2_DEPENDS_ON_U1, D7_C_MARGINAL_REGION_EXISTS,
D7_C_ORACLE_NO_USEFUL_RECOVERY, D7_C_MIXED_DIAGNOSTIC
THRESHOLD_OPS_MATCH: >=4 / <=1 / >=4 / <=1 / <=1 / >=12
```

`classify_stratum` (module L737–748) is first-match in the frozen order; 
`classify_terminal` (L844–871) applies T1–T11 first-applicable with T6 requiring
strong L1 **and** L2 in the same f. Exact match with prereg §10.

## 3. Model-F metadata evidence

```text
$ ls -la workspace/v72p2d5_model_f_input/20260907_r1/
total 208
drwxrwxrwx 1 karel_303 karel_303   4096 Sep  7 02:07 .
drwxrwxrwx 1 karel_303 karel_303   4096 Sep  7 02:07 ..
-rwxrwxrwx 1 karel_303 karel_303 208467 Sep  7 02:07 model_f_input.npz
-rwxrwxrwx 1 karel_303 karel_303    752 Sep  7 02:07 model_f_input_summary.json
```

Names/sizes/mtime only; no content was read or hashed. Production loader path:
`_default_model_f_loader` (module L402–413) calls
`d5._load_model_f_input_or_blocked()` (L404); it is reachable only when
`joint is None` inside `prepare_inputs` (L441, loader selection L445), which is
called from `run_bidirectional_oracle` L1278 — after the authorization check at
L1265. The CLI returns at `--help`/`--dry-run` (script L50–64) before any of
this. C18 independently shows the injected real-loader sentinel is never called
while the decode sentinel is.

## 4. External-cwd package/decode sentinels

External cwd `/tmp/opencode/d7c_pre_exec_r1/extcwd`, absolute repo script path:

```text
$ PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" python /mnt/d/Code/HD-QKD_Polar_Comparison/scripts/v72p2d7_gf32_bidirectional_oracle.py --help        (HELP_RC=0)
usage: v72p2d7_gf32_bidirectional_oracle.py [-h] [--model-f-root MODEL_F_ROOT]
                                            [--out-root OUT_ROOT] [--dry-run]
                                            [--verify VERIFY]
... --dry-run  print the frozen 128-call matrix only
$ PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" python /mnt/d/Code/HD-QKD_Polar_Comparison/scripts/v72p2d7_gf32_bidirectional_oracle.py --dry-run       (DRYRUN_EXT_RC=0)
129 lines; `cmp` vs repo-cwd output -> IDENTICAL_TO_REPO_CWD
```

The two sentinel test nodes were located by `-k` and each run as its own pytest
invocation with a fresh basetemp and `-p no:cacheprovider` (interpreter
`.venv/bin/python`, pytest 9.1.1):

```text
$ .venv/bin/python -m pytest comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py --collect-only -q -p no:cacheprovider -k "sentinel or loader or fail_before"
comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py::test_c13_wsl_rss_kib_to_bytes_and_fail_before_first_call
comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py::test_c18_external_cwd_sentinel_reaches_first_decoder_call

$ .venv/bin/python -m pytest "comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py::test_c18_external_cwd_sentinel_reaches_first_decoder_call" -q -p no:cacheprovider --basetemp=/tmp/opencode/d7c_pre_exec_r1/bt_c18
1 passed, 1 warning in 2.96s
$ .venv/bin/python -m pytest "comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py::test_c13_wsl_rss_kib_to_bytes_and_fail_before_first_call" -q -p no:cacheprovider --basetemp=/tmp/opencode/d7c_pre_exec_r1/bt_c13
1 passed, 1 warning in 1.01s
$ .venv/bin/python -m pytest "comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py::test_c17_lazy_import_help_dry_run_and_unauthorized_isolation" -q -p no:cacheprovider --basetemp=/tmp/opencode/d7c_pre_exec_r1/bt_c17
1 passed, 1 warning in 11.98s
```

C18 asserts exactly what the probe requires: the external-cwd bind reaches
exactly one decoder call (`events["decode"] == 1`), the Model-F loader sentinel
count is 0, the 16 seeds are sampled once each in ascending order, and no root
exists during the call phase. C17 additionally proves `--help`/`--dry-run` from
an external cwd bind no decoder and the unauthorized CLI path exits 3 without
creating the target.

## 5. Live stdlib RSS and units

```text
$ .venv/bin/python - <<'EOF'
(raw ru_maxrss, module get_rss_bytes, /proc/self/status VmHWM)
ru_maxrss_units_raw=95716
module_get_rss_bytes=98013184
raw_x1024=98013184
proc_self_status_VmHWM_kB=96272  VmHWM_x1024=98582528
RSS_OK: positive, module bytes == ru_maxrss*1024, 93.473 MiB < 2.000 GiB limit
HWM_SANITY: |VmHWM - ru_maxrss| = 556 KiB (same order, both positive)
```

Unit conversion is `ru_maxrss (KiB) * 1024` exactly (`get_rss_bytes` L280–294),
matches `/proc/self/status` VmHWM in the same KiB unit within 556 KiB, and is
positive and well below `2 * 1024**3`. No psutil.

## 6. GNU timeout

```text
$ command -v timeout
/usr/bin/timeout
$ timeout --version | head -1
timeout (GNU coreutils) 9.4
$ timeout -k 5 3 sleep 10; echo EXIT=$?
EXIT=124
```

GNU coreutils timeout exists; a killed child yields exit 124 as required.

## 7. Unauthorized refusal before everything

Exact frozen command shape with the frozen `--model-f-root` and a non-UUID
probe out-root (`workspace/d7_c_bidirectional_oracle_PROBE_REFUSAL`); no UUID
and no authorization flip:

```text
$ PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_PROBE_REFUSAL
D7-C execution is not authorized; refusing before any work
EXIT=3
$ ls -d workspace/d7_c_bidirectional_oracle_PROBE_REFUSAL 2>/dev/null; echo PROBE_ROOT_ABSENT=$?
PROBE_ROOT_ABSENT=2
```

The probe root was not created. Code order (authorization before Model-F load,
decoder bind, root creation):

- CLI runner `scripts/v72p2d7_gf32_bidirectional_oracle.py`: pure root-shape
  refusal L68–73 → state read L74–78 → authorization refusal L79–81 →
  `--model-f-root` equality L82–87 → `run_bidirectional_oracle` L88–92. With the
  false key the process exits before the model-root check and before the core
  run function.
- Core `run_bidirectional_oracle` (L1250–1321): single-use guard L1258–1259 →
  state read + `_require_authorized` L1263–1265 → existing-target refusal
  L1267–1268 → protected-root refusal L1269 → RSS preflight L1271–1276 →
  `prepare_inputs`/Model-F load L1278–1281 → production decoder bind L1283–1286
  → `execute_calls` L1289 → `write_root` L1319, and the root directory is
  created only at `out.mkdir(...)` inside `write_root` L951, i.e. after all
  calls. No decoder, Model-F or root can precede the authorization check.

## 8. Tests

Full new suite re-run with a fresh basetemp (`--basetemp=/tmp/opencode/d7c_pre_exec_r1/bt_full`):

```text
$ .venv/bin/python -m pytest comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py -q -p no:cacheprovider --basetemp=/tmp/opencode/d7c_pre_exec_r1/bt_full
20 passed, 1 warning in 60.81s (0:01:00)
```

Fake-only qualification, no production decoder call, no real Model-F content.
The warning is the pre-existing `Unknown config option: cache_dir` pytest
config notice, benign.

## 9. Protected metadata, authorizations, R1d/G2

Before/after probe snapshots (names, sizes, mtime) of
`workspace/v72p2d5_model_f_input/20260907_r1/` and
`workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`:

```text
before: D7-B root 5 files (manifest.json 1008, decoder_records.csv 44743,
        report.md 80, summary.json 449, command_log.txt 111; dir mtime 1789043618)
        Model-F root: model_f_input.npz 208467, model_f_input_summary.json 752 (mtime 1788718027)
$ diff protected_before.txt protected_after.txt && echo PROTECTED_METADATA_IDENTICAL
PROTECTED_METADATA_IDENTICAL
```

```text
$ ls -d workspace/v72p2d5_g2_20260907_r2 2>/dev/null; echo G2_EXPLICIT_ABSENT=$?
G2_EXPLICIT_ABSENT=2
$ ls -d workspace/v72p2d5_g2 workspace/d6_graph_mother_r1d_* 2>/dev/null; echo G2_R1D_GLOB_ABSENT=$?
G2_R1D_GLOB_ABSENT=2
$ ls -d workspace/d7_c_bidirectional_oracle_* 2>/dev/null; echo AFTER_PROBES_ABSENT=$?
AFTER_PROBES_ABSENT=2
```

- All authorization keys false (cycle_state lines 6–11, 19–20 above); no
  attempts/results/completed fields; `r1d_state` is `R1D_PAUSED_...` (line 18);
  G1 and G2 unauthorized; no G2 root.
- No `d7_c_bidirectional_oracle_*` root was created by any probe; no UUID exists
  anywhere in the D7-C artifacts (regex scan for
  `d7_c_bidirectional_oracle_<hex-uuid>` returned no match).

## 10. Frozen future command and mandatory Pre-RESULT

Quoted exactly from `D7_C_EXECUTION_PACKET_R1.md` L13 (also proposal L118,
design L166):

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_<uuid>
```

- Frozen but not run: the packet states it is "frozen but unauthorized and not
  executed"; no UUID was generated and no root exists. The `<uuid>` placeholder
  appears only as a placeholder.
- Mandatory Pre-RESULT review is stated in the execution packet §"Mandatory
  Pre-RESULT review" (L77–85: independent re-check of thresholds,
  prior/pair construction, exact/syndrome isolation, per-stratum breakdown,
  evidence schema, disclosure accounting and terminal replay against the six
  files; issues trigger rework; no publish-then-patch) and in the OpenSpec
  design (L169: "Pre-RESULT review mandatory before any result commit"). It is
  additionally binding via AGENTS.md §3.

## 11. Blocking assessment and non-blocking observations

No blocking issue found. All probes pass: branch/commit/dependency ordering,
scoped cleanliness, the exact 128-call matrix and frozen constants/thresholds,
Model-F metadata immutability with no content read, external-cwd bind plus both
sentinels, live RSS units, GNU timeout exit 124, unauthorized refusal before
decoder/Model-F/root with the probe root absent, the full new suite (20 passed),
protected metadata before/after identical, all authorization keys false, and
R1d/G2/D7-C-root absence. Direct four-prior construction and the absence of a
`final_beliefs -> other layer` data flow were re-confirmed (`final_beliefs`
appears only in result parsing L537/L543 and `_belief_diagnostics` L560; the
module imports only stdlib + numpy + D5 and references no interface-rework
implementation). This review records no decoder execution, reads no Model-F
content and grants no authorization; execution remains unauthorized.

Non-blocking observations:

1. Bare `python` is absent from the default PATH in this WSL shell (rc 127, no
   script executed). The accepted D7-B R2 execution documented a
   venv-on-PATH adapter (`~/.venvs/hd-qkd-polar-comparison/bin`). The D7-C
   authorization record should again resolve `python` to the accepted venv; the
   literal token otherwise fails safely before the script starts.
2. `validate_production_out_root` (L237–254) enforces the prefix and
   `workspace/` parent but not strict UUID syntax (e.g. `..._abc` is accepted;
   C17 codifies this). The authorization key plus one-shot consumption is the
   real gate; the future authorization should still use a fresh real UUID per
   packet.
3. `openspec/.../tasks.md` checkboxes T0–T4 remain unchecked and its status
   paragraph still says "T0/T2–T7 are not started" although planning,
   implementation and implementation review are committed. Docs-only; closeout
   (T6) should update them. Already noted by the implementation review §10.5.
4. The per-call watchdog is post-hoc (a call that never returns is bounded only
   by the outer 1800 s timeout) and `verify_root` is an internal-consistency
   checker that accepts a forged-but-consistent truncation. Both are frozen
   design limits already documented in `D7_C_IMPLEMENTATION_REVIEW_R1.md` §10
   and cannot alter a D7-C numerical or scientific conclusion.
5. The review-side pytest used the repo-local `.venv` (pytest 9.1.1,
   CPython 3.12.3, numpy 2.5.3) while the D7-B execution used
   `~/.venvs/hd-qkd-polar-comparison`; the authorization record should name the
   interpreter used for the one authorized invocation.
