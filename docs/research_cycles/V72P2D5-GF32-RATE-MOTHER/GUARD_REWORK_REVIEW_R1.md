# GUARD_REWORK_REVIEW_R1 — independent review of commit 860ebbff

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD `860ebbff74d8183c00cbb7d2f216447efb79d762`
- Under review: `860ebbff` — `test(v72p2d5): make formal-root guards lifecycle-aware` (2 test files, +146/−49)
- Role: independent read-only reviewer (did not write the rework, did not execute any prior D5 packet). All findings re-derived from source and own runs; no second-hand claim accepted.
- Authorization: **false**. See §9 for executed / not-executed statement.
- Verdict: **GUARD_REWORK_REVIEW_PASS** (with limitations carried into the G1 packet, §8)
- Non-claims: 无 FER、无泄漏、无密钥率、无资格、无方法裁决；不主张 G1 已就绪。

---

## 1. Numbered checks (PASS / FAIL / NOT_VERIFIABLE)

| # | Check | Result | One-line basis |
|---|-------|--------|----------------|
| C1 | Absent→absent passes, present→identical passes | PASS | `None==None` passes; dict equality on `(size, mtime_ns)` passes when untouched |
| C2 | Created during test → fails | PASS | `before=None` vs `after=dict` (or `{}` for empty dir) → `assert now==old` fires; independently reproduced in own scratch (§4) |
| C3 | Deleted / added / removed / resized / re-timestamped → fails | PASS | Any top-level file add/remove/size/mtime change alters the dict; `before=dict` vs `after=None` on deletion fires |
| C4 | No pass-while-created path (snapshot timing, skipped branch, exception bypass, discarded result) | PASS | Snapshot is first executable line in all six tests; final assert unconditional, no early return/try-except swallow; helper raises (no discardable return) |
| C5 | All seven roots covered, paths correct | PASS | Both files snapshot 7 entries; literals match core constants P0/G1/G2/G0/G0-recovery/Model-F(-input)/structure |
| C6 | `None` unambiguous vs empty directory | PASS | Absent→`None`, empty dir→`{}`; `None != {}` so creation of an empty root still fails |
| C7 | Nothing weakened in the six tests (only absence line changed) | PASS | Diff `860ebbff^..860ebbff` confirms: only `assert not …exists()` / narrow `g1_before` lines replaced; M20 reachability, P0G1G2_f no-file-access, P0G1G2_g four-file/no-overwrite/frozen-literal, R1_B2 authorization+budget asserts all verbatim surviving |
| C8 | No production `.py` changed; SAFE A/B/C + pre-existing AST guard intact | PASS | `--stat -- comparison_bench/src scripts` empty; TIS/SAFE hunks untouched (only append of T1_23 after TIS) |
| C9 | Depth limitation assessed | PASS (with limitation L1) | `_snapshot_dir` is top-level-files-only; nested writes invisible — acceptable as disclosed legacy for now, must be carried into G1 packet (§5, L1) |
| C10 | `test_T1_22` still red on real tracked-content change; staged+unstaged; binary | PASS (logic) + NOT_VERIFIABLE (live-fire) | Code covers `diff --numstat` + `diff --cached --numstat`, nonzero add/del or `-/-` → `changed`; live mutation demo deliberately not performed (no-residue requirement), see §6 |
| C11 | `STATUS=63` discrepancy resolved | PASS (report-only, does not affect rework correctness) | Measured 1969 porcelain lines (1887 ` M` + 82 `??`), `diff --numstat` 0 lines; implementer's `63` is a reporting error, §6 |
| C12 | `test_T1_23` real coverage stated | PASS (additive guard, narrow coverage L2) | Catches exactly `assert not … .exists()` with a root/literal token in the same assert segment; misses `os.path.exists`, `is_dir/is_file`, other operators, indirect variables, etc., §6/L2 |
| C13 | Full suite green with `workspace/` basetemp; formal roots unchanged; G2 still absent | PASS | `201 passed, 1 warning in 24.16s`; pre/post stat identical; `workspace/v72p2d5_g2/20260906_r1` ABSENT before and after |
| C14 | Hard prohibitions observed | PASS | No decoder/P0/G1/G2/prepare run, no CAL/VAL/parquet read, no edits to `.py`/`.md`/OpenSpec/`cycle_state.yaml`, no git writes; scratch+basetemp created under `workspace/` and removed |

Blocking findings: none. Hence PASS, not FAIL.

---

## 2. Guard semantics (§2 of packet)

Both files implement byte-identical helpers (modulo constant source):

```python
def _snapshot_dir(path):
    p = Path(path)
    if not p.exists():
        return None
    return {q.name: (q.stat().st_size, q.stat().st_mtime_ns)
            for q in p.iterdir() if q.is_file()}

def _formal_roots():
    # model_f_input.py: ROOT/_P0.._STRUCTURE rels + mod.MODEL_F_FORMAL_ROOT
    # rate_mother.py:  ROOT/mod.P0/G1/G2/G0/G0_RECOVERY/MODEL_F_INPUT/STRUCTURE
    ...

def _snapshot_formal_roots():
    return {str(r): _snapshot_dir(r) for r in _formal_roots()}

def _assert_formal_roots_unchanged(before):
    for key, old in before.items():
        now = _snapshot_dir(key)
        assert now == old, (
            f"formal root touched during test: {key} "
            f"(before={old!r}, after={now!r}); tests must snapshot-and-compare "
            f"formal roots, never assert their absence")
```

Four required behaviours:

1. **Absent→absent passes.** `before=None`, `now=None` → equal → pass. Verified by reading helper (no special-casing) and by suite green with G2 absent throughout.
2. **Present→identical passes.** Snapshot dict `{name: (size, mtime_ns)}` compared with `==`. Five of six formal roots were present with content (P0/G1/G0/G0-recovery/Model-F/structure) and the suite passed → this is precisely the lifecycle fix (old absence asserts would have failed here).
3. **Created→fails.** `before=None` vs `after={...}` (or `{}` for an empty dir) → `None != dict` → `AssertionError`. Independently reproduced (§4). Empty-dir creation is NOT confused with absence because `_snapshot_dir` returns `None` only when `p.exists()` is false and `{}` for an existing-but-empty directory.
4. **Deleted/added/removed/resized/re-timestamped→fails.** Any top-level file-list, size, or `mtime_ns` delta changes the dict. Deletion gives `after=None ≠ before=dict`. All fail via the same `assert now == old`.

No pass-while-created path found:

- **Snapshot timing.** In all six tests the snapshot is the first state-capturing statement before any test-controlled mutation: `test_R1_B2` line 2156 (function first line); `test_P0G1G2_f` line 2969 (after pure in-memory `_tiny_tables/_tiny_h`, before `chdir` and any `run_*_phase`); `test_P0G1G2_g` line 2984 (before any `run_p0_cost_phase`); `test_M20` line 3211 (after in-memory `_mffake_counts`, before fake-load/runner); `test_M24` line 453 and `test_P12` line 668 (immediately after `chdir tmp`, before the only tmp assertion). `_tiny_tables/_tiny_h/_mffake_counts` build in-memory frames only; no formal-root I/O precedes the snapshot.
- **Skipped comparison.** The terminal `_assert_formal_roots_unchanged(formal_before)` is unconditional in every test; no `if`/`return`/`pytest.skip`/`xfail` guards it. The two `test_P12/M24` bodies are straight-line (chdir → snapshot → tmp assert → invariance assert).
- **Exception bypass.** If the body raises before the terminal assert, the test errors/fails — it cannot pass. No `try/except` in any of the six tests swallows such an error.
- **Discarded result.** The helper returns `None` and enforces via `assert`; there is no result value to discard. Merely calling it performs the check.
- **Seven-root coverage, paths correct.** `test_v72p2d5_gf32_rate_mother.py` `_formal_roots` uses the owning core constants `mod.P0/G1/G2/G0/G0_RECOVERY/MODEL_F_INPUT/STRUCTURE_FORMAL_ROOT`; `test_v72p2d5_model_f_input.py` mirrors six relpath literals plus `mod.MODEL_F_FORMAL_ROOT`. Core values verified: `workspace/v72p2d5_p0_cost/20260906_r1`, `workspace/v72p2d5_g1/20260906_r1`, `workspace/v72p2d5_g2/20260906_r1`, `workspace/v72p2d5_g0/20260905_r2`, `workspace/v72p2d5_g0_recovery/20260906_r1`, `workspace/v72p2d5_model_f_input/20260907_r1`, `workspace/v72p2d5_structure/20260905_r2`. The mirror literals in the model-f test file match the core strings verbatim.

Comparison basis: file **names + sizes + mtimes (`st_mtime_ns`)**; `None` unambiguously means absent.

---

## 3. Nothing weakened (§3 of packet)

`git diff 860ebbff^..860ebbff --stat`: 2 files changed, 146 insertions, 49 deletions — exactly the two test files. `git diff 860ebbff^..860ebbff --stat -- comparison_bench/src scripts`: empty (exit 0). No production `.py` changed.

Per-test delta (old → new), confirmed from the full diff:

- `test_M24_formal_roots_absent` / `test_P12_formal_roots_absent` (model-f file): removed per-test `mf_root/g1_root/mf_before/g1_before` + two `assert not …exists()` (P0/G2) + two snapshot-equality asserts; added `formal_before = _snapshot_formal_roots()` + `_assert_formal_roots_unchanged(formal_before)`. Surviving verbatim: `monkeypatch.chdir(tmp_path)`, `assert list(tmp_path.rglob("model_f_input.npz")) == []`.
- `test_R1_B2_all_exec_false_formal_absent_and_budgets`: added leading `formal_before`; removed the two `assert not …exists()` (P0/G2); replaced 3-line comment; added `_assert…`. All surviving verbatim: `_rec_before/_g1_before` loads, all-exec-false loops, `scientific_promotion is False`, `is_phase_authorized is False` loops, `G0 exists` + `G0 == G0_EVIDENCE_FILES`, `_rec == _rec_before`, `_snapshot_dir(_g1_root) == _g1_before`, `G0_WALL_BUDGET_S == 120.0`, `G0_RSS_BUDGET_BYTES == 2*1024**3`.
- `test_P0G1G2_f_no_holdout_or_file_access`: `g1_root/g1_before` → `formal_before`; terminal 3 lines (2 absence + 1 G1-snapshot equality) → 1 invariance line. Surviving verbatim: 12-fragment `assert frag not in src` loop, `build_g0_fixture` loop, `_tiny_tables/_tiny_h`, `chdir`, three `run_*_phase(…FakeDecoder(), authorized=True)`, `assert list(tmp_path.rglob("*")) == []`.
- `test_P0G1G2_g_four_file_no_overwrite`: same head swap; terminal 2 absence + G1-equality → invariance + comment. Surviving verbatim: `run_p0/g1/g2_phase`, `write_*_evidence == STAGE_EVIDENCE_FILES`, sorted-name equality, 3× `pytest.raises(FileExistsError)`, payload-hash loop, table/summary asserts, and the three frozen literal-path asserts (`P0/G1/G2_FORMAL_ROOT == "workspace/…"`).
- `test_M20_d5_authorized_fake_load_reaches_runner`: head 2→1; terminal (G1-equality + 2 absence) → invariance. Surviving verbatim: `_spy.called`, `seen["injected"] is True`, `decoder_calls == 440`, `phase == "g1"`, `sorted(out) == STAGE_EVIDENCE_FILES`, `prepare_model_f_prior` shape asserts.
- `test_T1_22_openspec_history_zero_mod`: comment +5; `git status --porcelain` block → `git diff --numstat` + `git diff --cached --numstat` loop with `-/-` binary handling (§6). The `banned_calls` AST sub-block is verbatim.
- `test_T1_23_no_formal_root_absence_assertion`: purely additive (+44 lines after TIS). No deletion.
- SAFE A/B/C containment cases and the pre-existing `test_TIS_static_authorized_synthetic_isolation` AST guard: diff hunk headers show the only hunk near TIS is the append *after* it (`@@ -3511,0 +3543,44 @@`); no TIS/SAFE/`_flag/_k0/_k1/_k2` line is modified. No `skip`/`xfail` added; no trivially-true assertion introduced.

The new model is strictly stronger than what it replaced: the old model snapshotted only Model-F/G1 and asserted P0/G2 absent, so any legitimate P0/G1 artifact broke it (the observed all-red) and any write to the other four roots was unwatched. The new model watches all seven roots and accepts legitimate pre-existing artifacts while still failing on any touch.

---

## 4. Creation-catch demonstration — own scratch, own script (not the implementer's)

Principle: never touch a real formal root. Built a private scratch dir under `workspace/` (removed afterwards) containing one pre-existing root (`fake_root_present/keep.txt`, 4 bytes) and one absent root (`fake_root_absent/` not created). Copied the reviewed helper logic verbatim (variable names only adapted) operating **only** on those two scratch paths:

- Call sequence: `_snapshot_formal_roots()` → `mkdir fake_root_absent` + write `new_artifact.txt` (12 bytes) → `_assert_formal_roots_unchanged(before)`.
- Observed snapshot before: `{'…\\fake_root_absent': None, '…\\fake_root_present': {'keep.txt': (4, …)}}`.
- Observed failure (verbatim `AssertionError` message):

```text
formal root touched during test: D:\\Code\\HD-QKD_Polar_Comparison\\workspace\\guard_review_r1_scratch_abd98e95\\fake_root_absent (before=None, after={'new_artifact.txt': (12, …)}); tests must snapshot-and-compare formal roots, never assert their absence
```

- Result: the helper **does fail on creation**, including the absent→created transition. Had it passed, that would have been a blocking finding; it did not. Scratch directory removed (`Test-Path=False` after `Remove-Item -Recurse -Force`).

---

## 5. Depth blind spot — `_snapshot_dir` is top-level-files-only

Disclosed limitation, confirmed in source: the dict comprehension iterates `p.iterdir()` filtered by `q.is_file()`. Consequences:

- A new **subdirectory** created directly under a formal root is invisible (filtered out).
- Any file created/modified/deleted **inside a nested subdirectory** is invisible (never walked).
- A formal root replaced by an empty directory vs. remaining absent IS distinguished (`{}` vs `None`), but a root whose only change is nested content is NOT.
- Same-size + same-`mtime_ns` overwrite of a top-level file would also be invisible, but that requires deliberate `utime` preservation (tamper-grade, out of scope for these guards).

Current formal roots are flat evidence bundles (measured pre/post: P0/G1/G0/G0-recovery 4 top-level files each, Model-F 2 files, structure 4 files), so the top-level snapshot covers the formats G0/P0/G1/Model-F/structure actually produce today. The gap is therefore **acceptable as a disclosed legacy limitation for this rework**, but it **must be carried into the G1 packet as limitation L1**: before G1/G2 produce output, either (a) extend `_snapshot_dir` to a recursive walk (names + sizes + mtimes of all nested files, plus dir-entry set), or (b) add an explicit no-subdirectory invariant assert (`all top-level entries are files`) so a nested write fails loudly by construction. The G1 packet must state which option it takes. This gap is pre-existing (the old `_snapshot_dir` had the same body) — the rework did not introduce it — so it does not block PASS, but G1/G2 formal runs must not proceed on the assumption that nested writes are guarded.

---

## 6. `test_T1_22` and `test_T1_23`

### 6.1 `test_T1_22_openspec_history_zero_mod` (porcelain → numstat)

New logic (lines 1020–1035): run `git diff --numstat -- <clean_paths>` (unstaged) and `git diff --cached --numstat -- <clean_paths>` (staged); any line with nonzero added/deleted counts, or `-`/`-` (binary), is collected into `changed`; `assert changed == []`. The `banned_calls` AST half is unchanged.

- **Still red on real tracked-content change (logic PASS).** Any genuine content edit under `clean_paths` yields a numstat line with nonzero counts (text) or `-/-` (binary), both of which the parser appends → `changed != []` → fail. Binary is explicitly handled (`added == "-" or deleted == "-"` branch). Staged and unstaged are both covered (two `git diff` invocations, one with `--cached`). Line-ending-only churn under `core.autocrlf=true` with no `.gitattributes` yields empty numstat (verified: current tree has 1887 worktree-modified paths yet numstat is 0 lines), so the guard now measures real content difference rather than CRLF status noise — the stated intent of the change.
- **Live-fire demo: NOT_VERIFIABLE (deliberately).** Mutating a tracked file and reverting it to prove red-then-green would violate the no-residue requirement for this review (any revert that is not byte-identical, including CRLF normalization, risks leaving the tree dirtier). No such mutation was performed. The verdict on T1_22 therefore rests on code reading (above) rather than a live red demonstration. A future change owner may demonstrate it in a throwaway clone; this review does not claim a live red run.
- **Old-vs-new semantics.** Old (`status --porcelain`) failed on *any* worktree/index status entry including mode/CRLF churn; new (`diff --numstat`) fails only on content add/delete lines. That is a deliberate narrowing from status-cleanliness to content-cleanliness, documented in the new comment block, and correct for the `clean_paths` purpose (frozen plan/history/source dirs) under the repo's `autocrlf=true` reality.

### 6.2 `STATUS=63` vs `1887` discrepancy

Independent measurement (this review, read-only, CRLF warnings suppressed):

- `git status --porcelain=v1 | Measure-Object -Line` → **1969** lines.
- Breakdown: ` M` (worktree-modified) **1887**, `??` (untracked) **82**; 1887 + 82 = 1969. Deduplicated path count likewise 1969.
- `git diff --numstat | Measure-Object -Line` → **0**; content empty. `git diff --cached --numstat` → **0**; `git diff --name-only` → **0**.
- `git config core.autocrlf` → `true`; `.gitattributes` absent. Sample `status` head shows `.gitignore/README.md/src/…` all ` M` — consistent with CRLF-normalization churn, not content edits.
- `clean_paths`-scoped diffs (`PLAN_FREEZE.md`, `PLAN_CORRIGENDUM_R2.md`, `PLAN_REVIEW_VERDICT_R2.md`, `IMPLEMENTATION_PACKET_R2.md`, `src`, `experiments`, `tools`, `results`): both unstaged and cached numstat empty.

The review-initiation figure (**1887 modified paths, numstat 0**) is reproduced exactly (the 1887 is the ` M` subset of the 1969 porcelain lines). The implementer's reported **`STATUS=63` is wrong** — off by more than an order of magnitude against two independent counts (1887/1969). Most plausible cause is a reporting/staleness error (e.g. counting a filtered path subset, a cached shell, or a different `status` flag set) rather than a different repo state. **Effect on the rework: none.** The rework's correctness does not depend on the absolute porcelain count — it depends on (a) numstat being 0 for `clean_paths` (confirmed) and (b) the parser failing on nonzero numstat (confirmed by reading). The `63` is therefore a **report-only error**, not a correctness defect in `860ebbff`. It should be corrected on the record but does not block PASS.

### 6.3 `test_T1_23_no_formal_root_absence_assertion` — real coverage (not intended coverage)

What it actually does (lines 3545–3586): for each of the two test files, parse with stdlib `ast`, walk every `FunctionDef` except itself, and for every `assert not <…>` node whose source segment contains `.exists()` AND at least one token from `root_names` (`P0_FORMAL_ROOT`, …, `STRUCTURE_FORMAL_ROOT`) or `literal_frags` (`v72p2d5_p0_cost`, …, `v72p2d5_structure`), fail with file:function:line.

Real coverage — catches:

- The exact historical regression form: `assert not (ROOT / mod.P0_FORMAL_ROOT).exists()`, `assert not (ROOT / "workspace/v72p2d5_g2/…").exists()`, and any `assert not X.exists()` where the same assert line/segment names a watched root or literal. All six removed absence lines were of this form, so a verbatim reintroduction is caught.

Really misses (non-exhaustive, each verified against the predicate chain `Assert → UnaryOp(Not) → ".exists()" in segment → token in segment`):

1. `os.path.exists(...)` — segment `assert not os.path.exists(p)` contains `.exists(` but the predicate requires the substring `.exists()` (with empty parens); `os.path.exists(p)` does not contain it → **missed**.
2. `Path.is_dir()` / `Path.is_file()` / `Path.exists` without call parens in segment → no `.exists()` substring → **missed**.
3. Any non-`not` form: `assert X.exists() == False`, `assert X.exists() is False`, `assert len(list(p.iterdir())) == 0`, `assert p.stat() …` → **missed**.
4. Indirect path variable: `r = ROOT / mod.P0_FORMAL_ROOT; assert not r.exists()` — segment contains neither a root name nor a literal frag → **missed**. This is the most plausible evasion by refactoring.
5. Literal path not in the fragment list (new root name, typo'd String, or `Path.home()`-joined construction) → **missed**.
6. Non-`assert` enforcement (`if …exists(): raise/pytest.fail`, `assertFalse` in unittest style) and module-level (non-function) asserts → **missed** (only `FunctionDef` bodies scanned; only `ast.Assert` nodes).
7. The guard skips itself (`node.name == "test_T1_23…" → continue`), so absence asserts *inside* T1_23 would be silently exempt (minor self-blindness).

Bottom line: T1_23 is a **narrow tripwire for the exact historical spelling**, not a general absence-assertion ban. That is acceptable as an additive recurrence guard (it can only add failures for the matched spelling; it weakens nothing), but the G1 packet must carry it as limitation **L2**: do not cite T1_23 as proof that "no absence assert can return" — cite the snapshot-invariance asserts plus review discipline for the general case, and consider extending T1_23 (or a reviewer checklist) to `os.path.exists` / `is_dir` / indirect-variable forms if the threat model warrants it. Narrowness does not block PASS because the primary protection is the per-test invariance assert, not this static grep.

---

## 7. Suite run + formal-root stat (literal)

Command (basetemp under `workspace/`, per packet §6):

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -m pytest comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/guard_review_r1_basetemp_97ed80d8 -q
```

Literal output:

```text
........................................................................ [ 35%]
........................................................................ [ 71%]
.........................................................                [100%]
============================== warnings summary ===============================
..\..\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434
  D:\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434: PytestConfigWarning: Unknown config option: cache_dir
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
201 passed, 1 warning in 24.16s
```

Failing ids: none. (`201 passed`, no `failed`/`error` lines; the single warning is a pre-existing `cache_dir` config notice.)

Pre-run formal-root stat (existence + top-level file count + total bytes; content never read):

```text
workspace/v72p2d5_p0_cost/20260906_r1 EXISTS files=4 bytes=1877
workspace/v72p2d5_g1/20260906_r1 EXISTS files=4 bytes=3132
workspace/v72p2d5_g2/20260906_r1 ABSENT
workspace/v72p2d5_g0/20260905_r2 EXISTS files=4 bytes=3915
workspace/v72p2d5_g0_recovery/20260906_r1 EXISTS files=4 bytes=3963
workspace/v72p2d5_model_f_input/20260907_r1 EXISTS files=2 bytes=209219
workspace/v72p2d5_structure/20260905_r2 EXISTS files=4 bytes=12395
```

Post-run stat: byte-identical to pre-run on all seven entries; `workspace/v72p2d5_g2/20260906_r1` ABSENT before and after (`Test-Path=False`; the STOP condition never triggered). Basetemp and scratch removed after the run (`Test-Path=False` for both); `git status --porcelain` line count unchanged at 1969 (no residue).

---

## 8. Verdict

**GUARD_REWORK_REVIEW_PASS**

- The new snapshot-invariance guard model is sound (§2, C1–C6), strictly stronger than the stale-absence model it replaced (7 roots watched vs 2; legitimate artifacts accepted; every touch still fails), and nothing was weakened to obtain the green suite (§3, C7–C8).
- No blocking finding. The creation-catch property was independently reproduced (§4).

Limitations that **must** be carried into the G1 packet:

- **L1 (depth).** `_snapshot_dir` sees top-level files only; nested writes are invisible. G1/G2 must either make the snapshot recursive or add a no-subdirectory invariant before producing output (§5).
- **L2 (T1_23 narrowness).** The recurrence guard catches only `assert not … .exists()` with a root/literal token in the same assert; `os.path.exists`, `is_dir/is_file`, alternate operators, indirect variables, and non-assert enforcement bypass it. Do not over-claim its coverage (§6.3).
- **L3 (T1_22 live-fire).** Red-on-content-change is established by code reading, not by a live mutation demo in this review (NOT_VERIFIABLE by design, §6.1). If the G1 packet relies on T1_22 as a freeze proof, it should cite the parser logic, not a live red run from this review.
- **L4 (STATUS=63 record correction).** The implementer's `STATUS=63` figure is superseded by the §6.2 measurement (1969 porcelain / 1887 modified / numstat 0). No correctness impact, but the record should be corrected so future reviewers do not chase a phantom clean tree.

---

## 9. What was and was not executed (authorization: false)

- Executed: source reads of the two test files and core constant modules; `git diff 860ebbff^..860ebbff` (+ `--stat`, `--name-only`, `comparison_bench/src`/`scripts` filter); read-only `git status --porcelain`, `git diff --numstat` / `--cached --numstat` / `--name-only` / `--summary` / `--stat`, `git config core.autocrlf`; full pytest of the three named test files with `--basetemp` under `workspace/` (then removed); pre/post directory stat (existence/file-count/byte-total only) of the six formal roots plus Model-F input root; own scratch creation-catch demo under `workspace/` (then removed).
- Explicitly NOT executed: no decoder; no P0/G1/G2 phase via CLI (not even an exit-3 refusal probe — no authorization flip was in scope for this packet); no `scripts/v72p2d5_prepare_model_f_input.py`; no CAL/VAL/parquet row reads (`pandas.read_parquet` never invoked); no modification of any `.py`, existing `.md`, OpenSpec, or `cycle_state.yaml`; no `git add/commit/push/reset/stash/checkout/clean/rebase/revert/renormalize` or any tracked-file write; no basetemp outside `workspace/`; no live T1_22 mutation demo.
- The six formal roots were treated as read-only evidence throughout; `workspace/v72p2d5_g2/20260906_r1` never came into existence during this review.

---

*End of GUARD_REWORK_REVIEW_R1. P0 结果仅为记录，未接受；G1 未授权；next_gate 仍为 P0_PACKET_REVIEW.*
