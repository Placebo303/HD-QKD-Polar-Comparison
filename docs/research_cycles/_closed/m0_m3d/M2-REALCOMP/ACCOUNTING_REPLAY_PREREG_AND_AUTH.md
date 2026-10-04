# M2 accounting replay — PREREG_AND_AUTH

- Acceptance ID: `G-M2-ACCT-REPLAY`; track: **DECIDE** (claim-bearing recalculation from existing real-result artifacts). This is a new analysis, not an amendment or rerun of T3.
- Authority: `MAIN_ADJUDICATION_20260926.md` and `openspec/changes/m2real-accounting-replay/` define scope. The user's 2026-09-26 instruction, “需要的授权我现在都一次性给你，待我后续检查的时候我会一并查看结果，你只需要往下推进即可”, grants this bounded follow-on once this preregistration and Pre-EXECUTE pass. The grant does not turn unreviewed diagnostics into accepted results.
- Contract: this document, `ACCOUNTING_REPLAY_PROMPT.md`, one fresh machine root, a `ACCOUNTING_REPLAY_RESULT.md` result record, independent `ACCOUNTING_REPLAY_INDEPENDENT_ACCEPTANCE.md`, then main-thread decision. Original T3 roots and review are immutable.

## Frozen inputs and calculation

Read only these three files, each explicitly named: `workspace/m2real_d4e5f6a7/rows.json` (1M), `workspace/m2real_b8c9d0e1/rows.json` (1p5M), `workspace/m2real_f2a3b4c5/rows.json` (2M). Use only the stored `summary` values; no `.ttbin`, bundle, CSV, decoder, construction, or original result modification. `H_corr` stays source-specific and already persisted.

Exactly 12 new-method arms, kept source/family/m separate. For each, `D=superframes_done*1024*H_corr`, `E=lambda_parts.leak_EC`, `T=lambda_parts.tag`. Report `f_ec_actual=E/D`, `f_with_recorded_tags=(E+T)/D`, `tag_bits_recorded=T`, `tags_per_superframe=T/(64*superframes_done)`, and `f_if_one_tag_per_superframe=(E+64*superframes_done)/D` labeled **counterfactual**. Preserve the original nominal f values in distinct fields for discrepancy display. Require 16 blocks per superframe and 64 tag bits per recorded block. `f_eff_actual`, D2, backend identity, SKR, certification, publication and method-family rank stay **undetermined**, not numeric or inferred.

## Budget, command, output and stop

- One process, wall ≤300 s, RSS <2 GiB, no retry/resume. Output root fixed to fresh `workspace/m2_accounting_replay_20260926/`; it must be absent at Pre-EXECUTE. The only new machine files are `diagnostic.json` and `resource.txt` there. An incomplete/failed attempt is retained in that root and stops this grant.
- The exact WSL command, from `/mnt/d/Code/HD-QKD_Polar_Comparison`, after focused fake test and output-absence check:

```bash
mkdir workspace/m2_accounting_replay_20260926
timeout -k 10 300 /usr/bin/time -v .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m2_accounting_replay workspace/m2real_d4e5f6a7/rows.json workspace/m2real_b8c9d0e1/rows.json workspace/m2real_f2a3b4c5/rows.json > workspace/m2_accounting_replay_20260926/diagnostic.json 2> workspace/m2_accounting_replay_20260926/resource.txt
```

- STOP if branch is not `formal-ir-v72p1-addendum-clean`, frozen code/test changes expand beyond the OpenSpec pair, `src/ experiments/ tools/` changed by this task, any original input/output root is modified, output root preexists, focused fake test fails, any input count/field guard fails, wall/RSS cap fails, or the command requires a scientific-input change. No fallback to raw data or redecoding.

## Pre-EXECUTE checklist (record immediately before execution)

1. Branch/HEAD, scoped dirty-tree manifest, original roots and output-root absence.
2. Focused fake test command/output and `git diff -- src/ experiments/ tools/` empty for this task.
3. Explicit three JSON inputs, exact formulas, command and 300 s/2 GiB budget rechecked; no `.ttbin` or decoder import path.
4. Grant verbatim above recorded; all checks PASS or STOP. Append observations below before running.

Pre-EXECUTE record (2026-09-26, main thread): **PASS** for this one replay. Branch `formal-ir-v72p1-addendum-clean`, HEAD `ce85d61f`. Scoped new code/test/OpenSpec/packet files are the named files only; the wider dirty tree predates this replay and is preserved. `git diff --stat -- src/ experiments/ tools/` returned empty. The three `rows.json` input sizes are 14,042,522 / 19,734,691 / 26,471,294 bytes in source order 1M / 1p5M / 2M; each exists. `Test-Path workspace/m2_accounting_replay_20260926` returned False, and WSL confirmed `.venv/bin/python`, `/usr/bin/time`, and output-root absence (`PREEXEC_ENV_PASS`). The implementation imports only argparse/json/math/pathlib/typing; it has no decoder or raw-data path. Focused fake test reported **8 passed, exit 0** under WSL `.venv/bin/python -m pytest -p no:cacheprovider --basetemp workspace/m2_accounting_replay_test_f104193f85db4be183e8ab6613978ae6 comparison_bench/tests/test_m2_accounting_replay_fake.py`; the sole `pytest.ini` cache-dir warning did not affect result. Exact command and 300 s/2 GiB cap above rechecked. The user grant verbatim is recorded at the top of this packet. All four checks PASS; proceed once, with no retry.

## Pre-RESULT and claim ceiling

An independent reviewer recomputes at least one arm from the persisted `summary` and checks all 12 identities, tag counts, denominators, source separation, original-root immutability, and absence of D2/backend/f_eff claims. FAIL blocks a result record. Passing this replay establishes only the stored disclosure arithmetic for these implementations. It does not establish a fair method-family comparison or a verification protocol for the one-tag counterfactual.
