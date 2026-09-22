# LOADER_FIX_REVIEW_R1 — independent review of 299416ae + v72p2d5-p0-model-f-consumer-path-fix

- Role: independent read-only reviewer. Did not write the fix, P0 packet, or any prior D5 packet. Re-derived from source and measurement; no prior claim accepted on faith.
- Repo: `D:/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p2d5-addendum-clean` (observed `formal-ir-v72p1-addendum-clean`), HEAD `299416ae`.
- Under review: commit `299416ae` + OpenSpec change `openspec/changes/v72p2d5-p0-model-f-consumer-path-fix/` (proposal/design/tasks).
- Authorization: **false**. This document is not an authorization.
- Date: 2026-09-07/08. Packet: `.workbuddy/tasks/D5_LOADER_FIX_REVIEW_R1_PACKET.md` (§2→§8).

## Verdict

`LOADER_FIX_REVIEW_PASS`

The fix is correct, minimal, in-scope, and adequately tested for the assigned defect. The repository is fit for a **new** P0 authorization **provided** the conditions in §9 hold at authorization time. This is not itself an authorization, and reachability is not completion (see §10).

No blocking finding. One non-blocking module-identity caveat (§3) and one cosmetic worktree finding with a gate-scoping recommendation (§6) are recorded below; neither blocks P0 authorization.

## Check table

| # | Check | Result |
|---|-------|--------|
| C1 | Path resolution from `__file__`, `parents[4]` = repo root, relative-anchored / absolute-passthrough, no cwd/search/guess | PASS |
| C2 | Three-way failure separation, chained causes, `MODEL_F_BLOCKED` reserved for genuine absence | PASS |
| C3 | Frozen scientific constants / budgets / roots / thresholds / auth untouched; allowlist confined | PASS |
| C4 | Sibling contrast preload via `sys.modules` setdefault: minimal completion vs scope creep + shadowing risk | PASS (with noted low-risk identity caveat) |
| C5a | M22b genuinely simulates script launch (root+src+`''` off `sys.path`, `comparison_bench*` purged, chdir tmp, tmp artifact load) | PASS |
| C5b | M22a cwd-independence path assert (by design path-only) | PASS |
| C5c | M22c absent → genuine missing-input naming resolved absolute path | PASS |
| C5d | M22d invalid → invalid outcome, never missing-input | PASS |
| C5e | M22e injected short-circuit, zero filesystem access | PASS |
| C5f | No M22 test reads real Model-F root (`tmp_path` only) | PASS |
| C5g | SAFE A/B/C + AST static guard intact and unweakened | PASS |
| C5h | M22b would have failed pre-fix (execution re-run) | NOT_VERIFIABLE (static reason: YES, would have raised BLOCKED; execution not re-run per no-worktree-write rule) |
| C6 | Reachability probe: sentinel, exactly 1 call, tmp empty, roots absent, Model-F unchanged | PASS |
| C7 | Unauthorized `--phase p0-cost` still refuses exit 3, creates nothing | PASS |
| C8 | Commit `299416ae` confined to 5 intended files, no line-ending churn in commit | PASS |
| C9 | Worktree bulk-mtime / 1887 `M` with zero content diff is cosmetic, no scientific artifact affected | PASS (cosmetic; E6 gate recommendation in §6) |
| C10 | `test_T1_22_openspec_history_zero_mod` fails solely from C9 churn, not from this fix | PASS (for sole-cause-now; pre-`299416ae` same-cause re-run NOT_VERIFIABLE, commit-churn exclusion verified) |

## 1. §2 fix verification (source)

Read: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py` lines 2173–2270 (current), `git show --stat HEAD`, `git diff 3ecaebb6..299416ae` file hunk list (via directed read-only operator; quoted lines verified against my own `default.read`).

### C1 path resolution — PASS

- `_model_f_repo_root()` returns `Path(__file__).resolve().parents[4]` with docstring `no sys.path, no cwd`.
- File is `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`, so `parents[0]=formal_ir, [1]=comparison_bench(inner), [2]=src, [3]=comparison_bench(outer), [4]=repo root`. Count verified from path, not from any claim.
- `_resolve_model_f_input_root()`: `cand=Path(MODEL_F_INPUT_FORMAL_ROOT)`; if absolute `return cand.resolve()`; else `return (_model_f_repo_root()/cand).resolve()`. No `getcwd/chdir/glob/search/fallback`. Same root-anchoring contract as prepare script (mirrored, not imported).
- `_load_model_f_loader()`: `here=Path(__file__).resolve().parent`; `contrast_path=here/"v72p2d3_gf32_contrast.py"`; `sibling_path=here/"v72p2d5_model_f_input.py"`; both via `spec_from_file_location + module_from_spec + exec_module`. Zero `sys.path.insert/append` in the new helper (the pre-existing `sys.path.insert` in `_load_g0_decoder` is untouched and out of this path). Old two-stage package-import fallback chain (`from comparison_bench.formal_ir... / except ImportError: from comparison_bench.src...`) is removed.

### C2 failure separation — PASS

- Constants: `MODEL_F_BLOCKED="MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"` (unchanged, genuine-absence only), new `MODEL_F_LOADER_UNAVAILABLE="MODEL_F_INPUT_LOADER_UNAVAILABLE"`, new `MODEL_F_INPUT_INVALID="MODEL_F_INPUT_INVALID"`.
- Loader faults (4 sites: contrast spec None, contrast exec fail, sibling spec None, sibling exec fail) raise loader-unavailable, exec-fail sites with `from exc`.
- `if not root.is_dir(): raise ValueError(MODEL_F_BLOCKED + ... f"resolved artifact root absent: {root}")` — names resolved absolute path.
- `except (FileNotFoundError, NotADirectoryError) as exc: raise ValueError(MODEL_F_BLOCKED + ... f"artifact files missing under: {root}") from exc`.
- `except ValueError as exc: raise ValueError(MODEL_F_INPUT_INVALID + ... f"failed at {root}: {exc}") from exc` — surfaces loader validation, chained.
- Old broad `except Exception` that collapsed everything into missing-input is removed from `_load_model_f_input_or_blocked`. Two `except Exception as exc` remain inside `_load_model_f_loader` but both are `raise ... from exc` (chained, never relabelled as missing input). Acceptable; narrowing to `ImportError/OSError` is optional future tightening, not required.

### C3 scope — PASS

- Diff `+/-` lines contain none of the frozen items as changed lines: `Q/GF_POLY/N/M_MAX/COLUMN_DEGREE/L1_K_MIN/L2_K_MIN/LAMBDA_STAR/AUDIT_FLOOR/DECODER_FLOOR/CE_*/G0/G1/G2/P0 seeds/F sets/blocks/widths/roots/budgets/MAX_ITER/DAMPING_ALPHA/PHASES/auth keys`. Substring hits are only hunk headers and context lines.
- No touch to `_load_g0_decoder`, `is_phase_authorized`, decoder-call counts, `cycle_state.yaml` (verified `next_gate: P0_PACKET_REVIEW` unchanged, all `*_execution_authorized: false`).
- `git show --stat HEAD`: exactly 5 files (mother core + mother tests + 3 OpenSpec docs), `549 insertions, 17 deletions`. No sibling, frozen-plan, `src/`, `experiments/`, `tools/`, `results/`, `workspace/*` file in commit.

## 2. §3 declared scope call — sys.modules preload

Implementer disclosed: sibling `v72p2d5_model_f_input.py` itself does `from comparison_bench.formal_ir.v72p2d3_gf32_contrast import build_canonical_counts` with fallback to `comparison_bench.src...`, so path-loading the sibling alone still raises `ImportError` under script launch. Fix preloads `v72p2d3_gf32_contrast.py` by file path and registers under both dotted names via `setdefault`, no `sys.path` change, no sibling edit. Verified sibling diff empty, contrast top imports stdlib/numpy only (`importlib.util/math/pathlib/typing/numpy`), so one preload covers the sibling.

Exact lines (verified by my own read):

```python
contrast_names = (
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast",
)
if contrast_names[0] not in sys.modules:
    ...
    sys.modules[contrast_names[0]] = contrast_mod
for _name in contrast_names:
    sys.modules.setdefault(_name, sys.modules[contrast_names[0]])
```

Judgment: **minimal completion of the assigned fix, not scope creep**. Without it the sibling's `exec_module` fails and the fix is ineffective; with it the change stays inside the helper, touches no frozen file, mutates no `sys.path`.

Risk, stated plainly: `setdefault` never overwrites, so a genuine pytest import that is already in `sys.modules` (rootdir on path) is kept — no shadowing in that direction. Opposite direction (helper loads first, later `import comparison_bench.formal_ir...` hits `sys.modules` and returns the file-loaded object) aliases two dotted names to one object loaded from the same file with identical content, bypassing parent-package `__init__`; `__spec__.origin`/`reload`/`pickle` identity can surprise, but numerical content is identical and the contrast module is stateless stdlib/numpy. Scientific risk is negligible; module-identity surprise is non-zero but contained (sibling itself is loaded under a unique `v72p2d5_model_f_input_consumer` name, not a package name, so it does not pollute the package namespace). `setdefault` is sufficient for the stated purpose; no stronger guard is required for P0.

## 3. §4 test evidence

Read: `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` lines 3289–3387 + `test_TIS_static_authorized_synthetic_isolation` (3389–3511).

- M22a (`test_M22a_model_f_root_resolves_cwd_independent`): `chdir tmp_path`, assert resolved is absolute and equals `mod._model_f_repo_root()/MODEL_F_REL_TAIL` and `(ROOT/MODEL_F_REL_TAIL).resolve()`, tmp empty. Path assert only, no `sys.path` strip — by design; PASS for cwd-independence, not a launch simulation.
- M22b (`test_M22b_model_f_loader_without_repo_root_on_path`): **genuinely simulates script launch**. Strips `""`, `str(ROOT)`, `src_root` from `sys.path` via monkeypatch, purges `comparison_bench/comparison_bench.*/v72p2d5_model_f_input_consumer` from `sys.modules` (with before/after cleanup), writes a `tmp_path/mf_valid` artifact via the sibling's own writer, `chdir tmp_path`, calls `_load_model_f_input_or_blocked(None,None)`, asserts round-tripped content. This is the condition that escaped all 195 prior tests (every prior test either injected tables or left rootdir on path). PASS.
- M22c: absolute missing path, `chdir tmp`, expects `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` and `str(missing.resolve())` in message, tmp empty. PASS.
- M22d: present root with wrong file set expects `MODEL_F_INPUT_INVALID` and asserts missing-input string absent. PASS.
- M22e: injected tables with loader+resolver boomed, asserts identity short-circuit (`is`) and tmp empty. PASS (zero filesystem access).
- Real-artifact read: **none**. M22a resolves the real path string only; M22b/c/d monkeypatch `MODEL_F_INPUT_FORMAL_ROOT` to `tmp_path` values; grep shows `real_root/_snapshot_dir(real` only in pre-existing M21 context, not in M22. PASS.
- SAFE/AST: M22 block contains zero `authorized=True`, zero `run_p0_cost_synthetic/run_g1_synthetic/run_g2_synthetic/decode_fn/out_dir`; helper called directly. `exceptions` set in `test_TIS_static_authorized_synthetic_isolation` unchanged (3 documented missing-isolation names); SAFE A/B/C branches verbatim intact; `T0_38/T1_13/T1_14/T1_21` unaffected per subset run (10 passed, only T1_22 failed for worktree reason below). PASS.
- Would M22b have failed pre-fix: static reason YES — old code was package-import + fallback, both raising `ModuleNotFoundError` with root off path, mapped to BLOCKED, so the tmp load would have raised instead of returning. Live pre-fix execution (checkout parent into scratch + run) was not performed per the no-worktree-write rule → marked NOT_VERIFIABLE for execution, with static reasoning recorded.

## 4. §5 reachability probe (required, run under my direction)

Direct call (not CLI, so no authorization involved): `run_p0_cost_synthetic(authorized=True, decode_fn=probe, out_dir=<fresh tmp outside formal roots>, counts_ab=None, p_b=None)` with probe raising unique sentinel on first invocation. The `counts_ab=None/p_b=None` path is the one permitted real-artifact read.

Literal stdout/stderr (verbatim from directed operator):

```text
SYS_PATH_BEFORE=['C:\\Users\\admin\\AppData\\Local\\Temp', 'C:\\Program Files\\Swabian Instruments\\Time Tagger\\driver\\python', 'D:\\software\\Miniforge3\\python312.zip', 'D:\\software\\Miniforge3\\DLLs', 'D:\\software\\Miniforge3\\Lib']
CWD='D:\\Code\\HD-QKD_Polar_Comparison'
REPO=D:\Code\HD-QKD_Polar_Comparison
SYS_PATH_PATCHED=inserted repo root at 0
SYS_PATH_AFTER=['D:\\Code\\HD-QKD_Polar_Comparison', 'C:\\Users\\admin\\AppData\\Local\\Temp', 'C:\\Program Files\\Swabian Instruments\\Time Tagger\\driver\\python', 'D:\\software\\Miniforge3\\python312.zip', 'D:\\software\\Miniforge3\\DLLs']
IMPORT_OK=comparison_bench.src.comparison_bench.formal_ir.v72p2d5_gf32_rate_mother
TMP=C:\Users\admin\AppData\Local\Temp\loader_probe_5598yr4_
SENTINEL_CAUGHT: PROBE_SENTINEL_LOADER_FIX_REVIEW_R1_UNIQUE
CALLS=1
TMP_EMPTY=True
TMP=C:\Users\admin\AppData\Local\Temp\loader_probe_5598yr4_
TMP_LISTING_START
DIR=C:\Users\admin\AppData\Local\Temp\loader_probe_5598yr4_ DIRS=[] FILES=[]
TMP_LISTING_END
```

Note: an initial naive `import comparison_bench...` from a TEMP script failed with `ModuleNotFoundError` (because `python <TEMP>` sets `sys.path[0]=TEMP`), which itself reproduces the incident mechanism; the patched probe explicitly inserted the repo root for the *test harness import only* and recorded it — the unit under test still resolved its loader/root from `__file__`, not from that `sys.path` entry.

Result: **PASS** — sentinel caught, probe called exactly once, tmp empty. If this had failed it would have been blocking; it did not.

Pre/post protected-roots snapshot (verbatim stat):

```text
Pre-probe:  P0 root workspace/v72p2d5_p0_cost/20260906_r1: False (absent)
            G2 root workspace/v72p2d5_g2/20260906_r1: False (absent)
            Model-F workspace/v72p2d5_model_f_input/20260907_r1: True,
              model_f_input_summary.json 752 2026/9/6 18:07:07 (mtime 1788718027.0436988)
              model_f_input.npz 208467 2026/9/6 18:07:07 (mtime 1788718027.0436988)
Post-probe: P0 root: False; G2 root: False (parents also False)
            Model-F: identical — 2 files, 752/208467, same mtime 1788718027.0436988
```

Unauthorized-refusal check (the one permitted CLI run), literal:

```text
phase 'p0-cost' is not authorized; refusing before any work
EXIT_CODE=3
```

Created nothing (`workspace/v72p2d5_p0_cost` still `False`). PASS.

## 5. §6 worktree state (read-only, no repair)

Independently established (read-only `git status/diff/show/log/config --get`):

- `git status --porcelain` count: **1967** total, **1887** `^ M` (tracked modified), 80 untracked. First lines e.g. `M .gitignore, M AGENT_HANDOFF.md, M CURRENT_TASK.md, ...`.
- `git diff --numstat`: **0** (empty). `git diff --ignore-cr-at-eol --numstat`: **0** (empty). `git diff --name-only`: **0**. `git diff HEAD --stat` / `--summary`: empty. Unsuppressed stderr shows many `warning: in the working copy of '...', LF will be replaced by CRLF the next time Git touches it`.
- Config: `core.autocrlf=true`, `core.eol` unset, `.gitattributes` absent (`False`), `core.filemode=false`.
- Commit: `git log --oneline -3` → `299416ae fix(v72p2d5)... / 3ecaebb6 result... / a71188fb chore...`. `git show --stat HEAD` + `--name-only HEAD` → confined to the 5 intended files (mother core, mother tests, 3 OpenSpec docs), `549 insertions, 17 deletions`. **No line-ending churn in `299416ae` itself.**
- `test_T1_22_openspec_history_zero_mod` in subset run: `1 failed, 10 passed, 128 deselected`. Failure is `assert r.stdout.strip()==""` on `git status --porcelain -- <clean_paths>` listing `M experiments/... / M src/...` (57 lines); it names no CRLF/whitespace text itself, but the corroborating check `git diff --numstat -- <same clean_paths>` is **0/empty** — status flags modification while content diff is zero. Sole-cause-now: **this churn, no other reason** (no content assertion failed). Whether it failed for this same reason *before* `299416ae` was not re-executed (would need parent checkout + run); the commit-churn exclusion above plus the packet-author's same-day clean-tree observation bounds it to the bulk rewrite at ~17:22:29 preceding the 17:31:42 commit, not to the fix. Pre-commit same-cause re-run: NOT_VERIFIABLE.
- Scientific artifacts: Model-F byte-identical across probe (sizes/mtime above); commit touches no `workspace/*`, no frozen constants, no evidence files. Other formal roots (G0/G0-recovery/G1/structure) byte-identity across the fix was not re-statted here (no pre-fix snapshot in scope) — but the commit file list excludes them and `git diff --numstat` is zero, so no substantive effect is evidenced. Cosmetic, not substantive.

Does it block a new P0 authorization? **No for authorization; yes as-written for the R2 execution packet's `E6 clean tracked tree` gate.** The tree fails `git status --porcelain` cleanliness while having zero content difference. My recommendation: **(a) narrow cleanliness gates to real content differences** (e.g. `git diff --numstat` / `git diff --ignore-cr-at-eol` empty, or `git status` filtered through content diff) as the required change before the next execution gate; treat (b) repository-side normalization (`core.autocrlf` / `.gitattributes` / renormalize) as a separate, out-of-band hygiene task, not a P0 precondition — precisely because any renormalizing write now would touch ~1887 tracked files and, under the current emphatic no-write rule, risks far more than the cosmetic issue it fixes. Do not perform either in this review (no repair per packet).

## 6. What was and was not executed

Executed (under my direction, authorization false throughout):
- Direct-call reachability probe (§5) with unique sentinel + fresh tmp `out_dir` + `authorized=True` on the synthetic entrypoint only (no CLI authorization involved).
- Single unauthorized CLI refusal check (`python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` → exit 3).
- Read-only git: `status --porcelain`, `diff --numstat`, `diff --ignore-cr-at-eol --numstat`, `diff --name-only/summary/stat`, `show --stat/--name-only HEAD`, `log --oneline -3`, `config --get core.autocrlf/eol/filemode`, `.gitattributes` existence.
- Read-only stat: `Test-Path`/`Get-ChildItem`/`os.stat` size+mtime on P0/G2/Model-F roots pre/post probe.
- Focused pytest subset with fresh `--basetemp` under `workspace/` and `-p no:cacheprovider`: `-k "M22 or TIS_static or T1_22 or T0_38 or T1_13 or T1_21 or T1_14"` → `1 failed, 10 passed, 128 deselected` (only T1_22 fails, for §6 reason).
- Source reads: mother core hunks, sibling import block, contrast imports, M22a-e + AST guard, proposal/design/tasks, `cycle_state.yaml`.

Not executed (per hard prohibitions): no decoder run except the single first-call-raising sentinel probe; no P0/G1/G2 run; no `v72p2d5_prepare_model_f_input.py`; no `pandas.read_parquet` and no CAL/VAL/parquet-row read (Model-F stat was size/mtime + directory listing only, plus the single permitted loader read inside the probe); no `workspace/v72p2d5_*` creation (P0/G2 verified absent throughout; had either appeared I would have stopped); no `cycle_state.yaml` change; no `.py`/`.md`/OpenSpec edit; no git write op (`add/commit/push/reset/stash/checkout/clean/rebase/revert/renormalize` all avoided); no repair. Unverifiable items are marked NOT_VERIFIABLE with reasons above.

Workspace writes: only my pytest `--basetemp` (`workspace/review_r1_basetemp_<uuid>`) and operator tmp files under `$env:TEMP` (`loader_probe_r1_probe*.py`, `loader_probe_<id>/` empty out_dir). No other writes.

## 7. Pytest literal

```text
....F......                                                              [100%]
FAILED comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_T1_22_openspec_history_zero_mod
1 failed, 10 passed, 128 deselected, 1 warning in 1.09s
```

(T1_22 assertion lists only `M ...` status lines for `src/experiments/tools/results` + plan-history paths; `git diff --numstat` for the same paths is empty — line-ending-only churn. All M22 + TIS + T0_38/T1_13/T1_14/T1_21 in the subset passed.)

## 8. Conditions that must hold at authorization time

This PASS becomes actionable only if all hold when the new P0 is authorized:
1. `workspace/v72p2d5_p0_cost/20260906_r1` and `workspace/v72p2d5_g2/20260906_r1` still absent (verified absent here).
2. Model-F root still exactly 2 files with unchanged size/mtime (`model_f_input.npz 208467`, `model_f_input_summary.json 752`, mtime `1788718027.0436988`).
3. `cycle_state.yaml` still `p0_cost/g1/g2_execution_authorized: false`, `next_gate: P0_PACKET_REVIEW` (verified unchanged here).
4. E6-style cleanliness gates are scoped to real content differences (per §6 recommendation), or the tree is normalized through an explicitly authorized hygiene change — a raw `git status --porcelain` empty check will fail cosmetically until then.
5. Authorization is a fresh, explicit grant for the new P0 run; the consumed 2026-09-07 authorization is wasted and cannot be reused.

## 9. Explicitly not claimed

No FER, no leakage, no key rate, no qualification, no method verdict, no end-to-end proof, and **no prediction that P0 will now complete — reachability is not completion**. The probe proves the consumer now reaches the loader and the decoder (sentinel, 1 call, empty tmp); it proves nothing about decode success, cost projection, budgets, or formal-output acceptance, which require a newly authorized P0 run.

## 10. Closing

`LOADER_FIX_REVIEW_PASS` — fix correct and in-scope, tests cover the escaped launch condition, probe effective, worktree issue cosmetic with a gate-scoping disposition. This review is not a P0 authorization.
