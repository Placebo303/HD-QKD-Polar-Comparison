# D7-E provenance-safe cross-layer discriminator — Pre-EXECUTE Review VENV A1

- reviewer: independent A1 reviewer (separate context from the A01–A03 operator; performed no A01–A03 edits)
- authority: `.workbuddy/tasks/D7_E_PREEXEC_VENV_COMMAND_CLOSEOUT_A1_TASK_PACKET.md` §5 (A04 only)
- branch: `formal-ir-v72p1-addendum-clean`
- entry HEAD: `031deee70378c19d5d8e32e3a2a2461d0c2343c5` (`031deee7 docs(d7-e): record implementation and pre-execute reviews`)
- date (UTC): 2026-09-11
- review-only: sole write is this file; no commits, no other edits, no decoder/Model-F content, no roots, no UUID
- scope: read the packet §0–§4, the changed docs (`D7_E_PREREG_R1.md`, `D7_E_EXECUTION_PACKET_R1.md`, `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`, `openspec/changes/v72p2d7-provenance-safe-cross-layer-discriminator/tasks.md`), the original reviews (`D7_E_IMPLEMENTATION_REVIEW_R1.md`, `D7_E_PRE_EXECUTE_REVIEW_R1.md`); reran §4 probes as separate commands from repo root with the corrected interpreter

## Verdict

`D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_A1_AWAITING_EXPLICIT_AUTHORIZATION`

It grants nothing. No execution authorized. No result accepted.

This review supersedes R1 ONLY for command/environment reachability. All R1 scientific checks remain valid.

## Freeze / HEAD verification (pre-review gate)

- `git rev-parse HEAD` = `031deee70378c19d5d8e32e3a2a2461d0c2343c5` — matches required HEAD exactly; `git branch --show-current` = `formal-ir-v72p1-addendum-clean`; `git log --oneline -1` = `031deee7 docs(d7-e): record implementation and pre-execute reviews`.
- Content diff (`git diff --name-only`) = exactly 13 files. A1-scoped: `D7_E_PREREG_R1.md` + `D7_E_EXECUTION_PACKET_R1.md` + `openspec/.../tasks.md` modified, plus new untracked `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`. The other 10 (`AGENTS.md`, `AGENT_HANDOFF.md`, `AGENT_PROJECT_MEMORY.md`, `README.md`, `RUN_COMMANDS.md`, `docs/CURRENT_MAINLINE.md`, `docs/decision-log.md`, `docs/research-cycle-sop.md`, `docs/troubleshooting.md`, `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`) are pre-existing dirty, preserved per packet §1.
- `git status --porcelain | wc -l` ≈ 1970 `M` entries are WSL stat noise: `git diff --numstat` confirms only the 13 files above have content deltas (same phenomenon documented in R18 §9 / R19 §28). No staging, no commits by reviewer.
- No production code/test edits: none of the 13 content-diff files is under `comparison_bench/src/`, `comparison_bench/tests/`, `scripts/`, `src/`, `experiments/` or `tools/`.
- Target globs absent before and after all probes (see §5).

## 1. Exact future command — PASS

- All three live authoritative locations carry byte-identical corrected spelling:
  - `D7_E_PREREG_R1.md:175`, `D7_E_EXECUTION_PACKET_R1.md:19`, `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md:17`:
  - `timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>`
- Preconditions frozen in all three docs: cwd is the repository root; `test -x .venv/bin/python`; `.venv/bin/python -c "import numpy, pytest; print(numpy.__version__)"`. No other venv, no bare `python`/`python3`, no `PYTHONPATH`, no wrapper; GNU timeout (`-k 30`, `1800`) and every scientific parameter unchanged.
- `openspec/.../proposal.md`, `design.md`, `specs/` contain no interpreter spelling (only budget text `Outer GNU timeout 1800 plus -k 30`), so no change was needed there — minimal scope is correct.
- Adjudication (non-blocking, historical provenance): one bare-`python` D7-E command string remains at `D7_E_PRE_EXECUTE_REVIEW_R1.md:52`. That file is frozen R1 provenance committed in `031deee7`, explicitly superseded by this A1 on interpreter reachability; editing its historical quotation would falsify review provenance. It is not a live command. All remaining bare-``python`` mentions in the three live docs are prohibitions (`Do not ... use bare python`), not commands.

## 2. Addendum scope — PASS

- `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md` supersedes ONLY the interpreter-spelling/environment portions of R1 §4 / exact-command sections (exhaustive scope section present). Scientific contract — matrix (R08), formulas and estimator identity (R09), eligibility (R10), labels (R11), terminal priority (R12), budgets (R13), root contract, seven-file schema, authorization lifecycle — untouched. It grants no execution authorization and runs nothing (explicit).

## 3. tasks.md lifecycle truth — PASS

- R14–R19 all checked complete with real evidence: R15/R16/R17 → commit `08590fba` (3 files, `verify_root`, 25 tests); R18 → `D7_E_IMPLEMENTATION_REVIEW_PASS` line 17 + `031deee7`; R19 → `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` line 13 + `031deee7`.
- Stale claims removed: `R15–R19 ... are later gates` replaced with completion record; non-goals now read `R15–R19 are complete with the evidence above. No execution authorization, no D7-E run, no result acceptance in this change.`
- Scientific wording preserved: `No scientific/budget/terminal/schema change beyond the frozen R08–R13; no V35/D5/D6/D7-C edits; no R1d/G1/G2 work.` unchanged.
- A1 item present and UNCHECKED (`- [ ] A1 — Venv command closeout (pending, later step)`; checked only after A04 passes).

## 4. No production code/test edits — PASS (see Freeze section)

## 5. §4 probes rerun (separate commands, repo root, corrected interpreter) — PASS

1. HEAD/branch/cwd: `/mnt/d/Code/HD-QKD_Polar_Comparison`, `031deee70378c19d5d8e32e3a2a2461d0c2343c5`, `formal-ir-v72p1-addendum-clean`.
2. `test -x .venv/bin/python` → `test-x_exit=0`.
3. `.venv/bin/python --version` → `Python 3.12.3`; `import sys, numpy, pytest` → `3.12.3` / `2.5.3` / `/mnt/d/Code/HD-QKD_Polar_Comparison/.venv/bin/python`.
4. Bare interpreter absent: `which python` → exit 1; `/usr/bin/python3` is `3.12.3` without numpy (`ModuleNotFoundError`); venv numpy import exit 0.
5. `which timeout` → `/usr/bin/timeout`; `timeout --version | head -1` → `timeout (GNU coreutils) 9.4`.
6. `--help` via `.venv/bin/python` → exit 0, usage with `--model-f-root/--out-root/--dry-run/--verify`, no bind/loader/root.
7. `--dry-run` via `.venv/bin/python` → exit 0, `193` lines (`slots=192 mandatory=128 budget=192`); head `1 1.0 2026091300 L1_TO_L2 SOURCE L1_MARGINAL L1 49`; tail `192 1.2 2026091315 L2_TO_L1 TRANSFER L1_TRANSFER L1 59`; f-split 96/96, directions 96/96, roles SOURCE/CONTROL/TRANSFER 64/64/64.
8. Unauthorized exact-shape probe via corrected interpreter (`--out-root workspace/d7_e_cross_layer_discriminator_A1_VENV_PROBE`, pre-absent exit 2) → stdout `D7-E execution is not authorized; refusing before any work`, exit 3; probe root absent after; `ls workspace/ | grep -E "d7_e_|d6_graph_mother_r1d"` → no match (exit 1).
9. Foreign-cwd sentinels from `/tmp/d7e_a1_foreign` via absolute repo paths only: `cwd= /tmp/d7e_a1_foreign`; `SOURCE_target_is_v35= True`; `TARGET_target_is_v35= True`; `loader_is_d7c= True`; sentinel dispatch `events= ['src', 'tgt']`; `unknown_key_refused= True`; `FOREIGN_SENTINEL_OK`; repo `d7_e_*` / `r1d_*` roots `[]` / `[]`. Zero decoder calls, zero Model-F reads, zero roots.
10. Targets rechecked absent (`No such file or directory` ×2); protected roots stat-only unchanged (`workspace/v72p2d5_model_f_input/20260907_r1` Sep 7, D7-C root Sep 11, D7-D root Sep 11 — matching R1 §9); `cycle_state.yaml` all 12 authorization keys false (`all_false= True`), attempts 0, `d7e_terminal= D7_E_NOT_EXECUTED`, `next_gate= D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.

## Checklist

- [x] Matches OpenSpec spec (command spelling + preconditions + R14–R19 evidence + A1 unchecked + non-goals/scientific wording preserved)
- [x] Tests pass (no new tests in scope; R1 scientific checks remain valid per R18/R19, untouched by this change)
- [x] No scope creep (docs-only: 3 modified + 1 addendum; no production/test edits; no roots; no auth change)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No — D7-E remains frozen/unauthorized/unexecuted; A05 state/commit belongs to the operator closeout, not this review.

## Return delta

- verdict: `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_A1_AWAITING_EXPLICIT_AUTHORIZATION` (grants nothing)
- per-item evidence: Freeze + §§1–5 above (corrected command byte-identical in 3 live docs; preconditions frozen; addendum interpreter-only; tasks.md R14–R19 evidenced + A1 unchecked; zero production/test edits; §4 probes all PASS with literal outputs)
- review doc path: `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_PRE_EXECUTE_REVIEW_VENV_A1.md`
- blockers: none. Non-blocking: (a) frozen R1 review retains the historical bare-`python` quotation (superseded provenance, must not be edited); (b) pre-existing 10-file content-dirty worktree + WSL stat noise, preserved per packet.
