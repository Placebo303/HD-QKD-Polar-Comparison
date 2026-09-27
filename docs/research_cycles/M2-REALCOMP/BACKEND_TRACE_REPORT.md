# Real M2 Layered-Binary backend provenance — read-only trace report (NOT RECOVERABLE)

- Date: 2026-09-27. Authority: decision D-5 option (iii) (see `docs/decision-log.md` entry "M2 accounting correction T0–T4 complete", D-5(iii)): a bounded read-only trace for contemporaneous Layered-Binary backend provenance. D-5(iii) mandated that "if a backend trace is found, the finding is refined, not withdrawn."
- Conduct: independent read-only investigation. Nothing was written, edited, moved or deleted; no decoder, arm runner, pytest or scientific command was run; no `.ttbin` or bundle was touched. The only commands were file searches, key inventories over already-persisted JSON, `git ls-files` / `git log` / `git cat-file`, and a bare `importlib.util.find_spec` probe. `results/` and `comparison_bench/outputs_comparison/` were untouched.
- Scope: the three real M2 roots and adjacent records only. No redecoding, no new execution.
- Status of this document: finding record only. This report authorizes nothing, grants no execution, changes no number in `CORRECTION_RESULT.md` or `CORRECTION_RECOMPUTE_CHECK.md`, and leaves `backend_used = UNKNOWN` in place.

## 1. Verdict: NOT RECOVERABLE

The backend identity of the real M2 Layered-Binary arms is not recoverable from this repository, and the reason is structural rather than a coverage gap.

Decisive mechanism, with cites:

- `m2real_runner.py:878-880` calls `spa_decode_with_explicit_fallback(...)` without passing a `sidecar`.
- `m2lb_arm_runner.py:1514` and `:1525-1530` skip the sidecar write when `sidecar=None`.
- The word `sidecar` occurs **zero** times in `m2real_runner.py`. The backend is resolved and then discarded.

Operational consequence, stated plainly: **a re-run of the identical command would reproduce the identical gap.** This upgrades "we lost the record" to "the record was never capturable."

## 2. Selection was deterministic and env-determined, never an operator choice

- `resolve_spa_decode_fn` (`m2lb_arm_runner.py:1482-1504`) is a pure function of `importlib.util.find_spec("ldpc")` — no RNG, no env var, no config, no CLI flag; a probe exception reads as absent (`:1497-1498`).
- `ldpc` present → `spa_decode_production`; absent or probe raises → `_spa_decode_numpy_planes` with `BACKEND_ID = "numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"` (`binary_spa_numpy.py:23`).
- There is no third path and no override; `find_spec_fn` is a test-only seam.
- The prereg and prompt pin construction, allocation, blind schedule, `max_iter`/streak and seeds in detail but **never pin a backend** — the backend was never a frozen input.

## 3. Four independent reasons no output signature could distinguish the paths retrospectively

1. `backend_used` is architecturally suppressed as in §1 above.
2. `iterations` is a required member of `m2lb_arm_runner`'s 13-key `OUTCOME_KEYS` (`:182-188`), but `layered_binary._OUTCOME_KEYS` is a different 11-key set that omits it; the `frame_rows` dict does not record it; and `grep -n iterations` in `m2real_runner.py` / `layered_binary.py` / `binary_spa_numpy.py` returns nothing. The field is discarded at the first hop.
3. No exception asymmetry: the true body refuses when `ldpc` is absent (`:461`), but the resolver only selects it when `ldpc` is present, so the two are mutually exclusive; and `binary_spa_numpy.py` emits no warning, log or distinguishing error.
4. No numeric artifact: both paths share the same leakage mapping, the same four status flags, the same double-gate semantics and the same `_P_ASSUMED = 0.02` (`m2lb_arm_runner.py:1468-1478`), and the real artifacts show `messages_actual = 3.14` and `leak_ec_bits = m` on every block including all 36 successes — identical to the fallback-produced synthetic values.

## 4. The negative evidence, stated as evidence

- Each of the three real roots contains exactly three files, no dotfiles, no subdirectories.
- `rows.json` top level is `{summary, rows}`; `summary` has 17 keys; `summary.arms[]` has 34 keys; per-block `rows[]` has 37 keys — and **none** of them is a backend field.
- `grep -i backend` across all nine files: 0 matches; `grep -iE "\b(spa|min_?sum|bposd|ldpc|...)\b"`: 0 matches.
- `backend_used` appears in the whole `workspace/` tree in exactly 12 files, all `workspace/m2lb_*/backend_used.sidecar.json` from the **synthetic** batch, and in none of the three real roots or the six `m2hdc_*` roots.
- The `M2REAL_RESULT_*.md` files carry no `decoder:` line at all, unlike the synthetic `M2LB_RESULT_*.md`.

## 5. Near-root artefacts that are NOT records of this run

Each identified:

- `workspace/m2real_t3_{1M,1p5M,2M}.log` are 2-line pre-flight **refusal** logs (`M2REAL-REFUSAL rc=2: explicit hdc_decode_fn + lb_construct_fn + lb_decode_fn required`), dated 2026-09-25 23:33, 40 minutes before the first real root output.
- The `workspace/m2_real_watch.log`, `m2_real_done.json` and `_r05_*` files are dated 2026-08-16 and point at an unrelated `nbldpc_v18_b2_real_search` task.
- No resource record of any kind exists for the real M2 batch — the only `*resource*.txt` in the tree belong to the accounting replay and the m3a/m3b batches.

## 6. The invocation itself is unrecorded — a wider hole than the adjudication states

- The frozen command template in `M2-REALCOMP-PROMPT.md:27,31,35` omits `--with-production-fns`, which `main()` requires (`m2real_runner.py:912-914`) or refuses; the three refusal logs show exactly that template being refused.
- `grep -rn "with.production.fns"` across `docs/`, `openspec/`, `workspace/` returns nothing except the fake tests.
- So the command that actually succeeded is neither the frozen template nor recorded anywhere.

## 7. The gap was documented contemporaneously, and guessing was explicitly refused

- `RESULT.md:22` and `:105` record the operator's own declaration that the terminal END/exit stdout line was never written to any file.
- `RESULT.md:106` and `INDEPENDENT_ACCEPTANCE.md:54` record `grep -c backend_used` = 0 and explicitly decline to guess the string.
- `docs/decision-log.md:5006` records that transcribing the END line or writing in a backend string was **rejected** because the content was not on file and must not be guessed.

## 8. Post-hoc environment state — explicitly fenced as inadmissible for provenance

A bare import probe today: `ldpc` ABSENT, `numpy` 2.5.3 PRESENT, `numba` 0.67.0 PRESENT, `sionna` ABSENT, `galois` ABSENT. Therefore the resolver **would today** select the numpy fallback.

This is post-hoc environment state, not evidence of what happened. It must not be used to fill the field. The adjudication's ruling at `design.md:155` is correct. This paragraph is a different epistemic class from every artifact above.

## 9. The `wall_s` soft signal — recorded but refused as evidence

Successful LB blocks took 0.078–0.093 s, which is *consistent with* the fallback's Python `for` loops over roughly 197 rows × 10 planes × up to 300 iterations (`binary_spa_numpy.py:92-112`) and hard to reconcile with a C++ `BpOsdDecoder`.

The investigation explicitly declines to use it: it is a single unattributed scalar, there is no recorded baseline for either backend on this hardware, and using it would be exactly the post-hoc inference the correction forbids. It is a reason to keep the question open and fix the recording, not evidence.

## 10. Fake tests could not have caught it

- `test_m2real_lb_fake.py` is backend-agnostic: exactly one backend-related hit, line 311, `monkeypatch.setattr(m2lb, "spa_decode_with_explicit_fallback", _raise)`; the tests always inject `_fake_lb_decode` and assert `max_iter==300` / `streak==3` / 10 planes / 5 deltas, never exercising or constraining backend selection.
- `binary_spa_numpy.py`'s `BACKEND_ID` is documented at `:22` as "sidecar/log only, never an outcome key", and its `iters == 0` early exit (`:90-91`) is discarded at the first hop.

## 11. No git history pins the code or the artifacts

- `git ls-files --error-unmatch` returns UNTRACKED for `m2real_runner.py`, `m2lb_arm_runner.py`, `binary_spa_numpy.py`, `layered_binary.py` and `test_m2real_lb_fake.py`; `git log` for them is empty; `workspace/` is gitignored (`.gitignore:21`).
- The only available bound is filesystem mtime: `m2real_runner.py` = 2026-09-25 23:40, 33 minutes before the first real output and 7 minutes after the 23:33 refusal logs — consistent with the current file being the code that ran, and explicitly an **mtime-based, non-provenance-grade** inference.
- Operational consequence: committing this code would be the first version pin it has ever had.

## 12. Decision-relevant bottom line

Because the real LB arms corrected only 36 of 28,000 blocks (0.13%) — independently recounted by the investigation as 19 in 1M, 11 in 1.5M, 6 in 2M — the backend question could not be deferred as a provenance nicety.

But **the numerical outcome does not depend on the backend identity**: both paths share identical accounting, identical status-flag semantics and identical persisted fields, differing only in the per-plane error-estimation estimator. Knowing the backend would **not** change the 36/28,000, the FER, the `undetected` counts or the leak columns; it would change only the **label** — whether these are an assumed-prior non-`ldpc` diagnostic or a genuine `BpOsdDecoder` measurement of a failing configuration. That label is not establishable from this repository, and a re-run would reproduce the gap.

Per `openspec/changes/m2real-accounting-correction/design.md:484-495`, this negative outcome **does not withdraw or soften** D-5(i) — it **is** the finding. The `backend_used = UNKNOWN` label stands unchanged.

## 13. What would make this recoverable in future — requirements only, not a plan, not scheduled, not designed

Ranked by value per unit of intrusion:

1. Pass a `sidecar` dict from `_production_lb_decode_fn` and flush it — the capability already exists and is test-exercised, currently dead from the real path's perspective.
2. Persist the backend string into `rows.json` `summary.arms[]` and `block_accounting.csv`, not only a sidecar.
3. Capture an execution-time environment fingerprint (the `find_spec("ldpc")` result, the resolved backend literal, the resolved function's `__module__.__qualname__`) at run start — this converts today's inadmissible post-hoc inference into admissible contemporaneous evidence.
4. Persist `iterations` end-to-end through `layered_binary._OUTCOME_KEYS` → `frame_rows` → `_lb_block` → the row dict.
5. Write the per-root sidecar **from code**, never by hand, since a hand-authored sidecar should not be relied on as a provenance mechanism.
6. Capture and retain the stdout transcript including the terminal END/exit line.
7. Retain a per-arm resource record.
8. Record the exact invoked command line and argv in the root.

## 14. Closing

This report authorizes nothing, grants no execution, changes no number in `CORRECTION_RESULT.md` or `CORRECTION_RECOMPUTE_CHECK.md`, and leaves `backend_used = UNKNOWN` in place.
