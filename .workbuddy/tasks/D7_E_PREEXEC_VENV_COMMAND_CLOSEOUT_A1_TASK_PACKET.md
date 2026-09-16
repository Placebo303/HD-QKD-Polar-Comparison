# D7-E Pre-EXECUTE venv command + OpenSpec closeout A1

Status: `FROZEN_ZERO_DECODER_READINESS_CORRECTION_A1`

## 0. Ruling

The D7-E implementation and scientific contract remain accepted. The existing
Pre-EXECUTE verdict cannot yet authorize a run because it established:

- default `PATH` has no `python`;
- all successful probes used `.venv/bin/python` explicitly;
- the frozen command still says bare `python`.

This is the same class of launch-reachability mismatch previously caught at
D7-B. Before any authorization, supersede only the interpreter spelling with
the repository venv and close stale OpenSpec checkboxes. No scientific input,
matrix, formula, threshold, budget, root, seed or implementation changes.

## 1. Baseline and prohibitions

- Branch `formal-ir-v72p1-addendum-clean`.
- Expected entry HEAD `031deee70378c19d5d8e32e3a2a2461d0c2343c5`.
- D7-E implementation review PASS and original Pre-EXECUTE PASS documents
  remain provenance, but the latter is superseded on interpreter reachability.
- D7-E root/UUID absent; all authorization/promotion false.

Zero decoder calls, zero Model-F content read, zero result root/UUID, zero R1d,
`--phase`, G1/G2, CAL/VAL/real/raw. Do not edit production code/tests. Preserve
dirty tree and protected roots. No broad Git action or push.

## 2. A01 — freeze the corrected exact command

Update the D7-E OpenSpec proposal/design/spec/tasks, prereg and execution packet
so the only exact future scientific command is:

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>
```

Freeze repo-root cwd as an operational precondition and require:

```bash
test -x .venv/bin/python
.venv/bin/python -c "import numpy, pytest; print(numpy.__version__)"
```

Do not activate another venv, use bare `python/python3`, add `PYTHONPATH`, or
alter child argv through a wrapper. GNU timeout and every scientific parameter
remain unchanged.

Create:

`docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`

It supersedes only the interpreter spelling/environment portions of R1.

## 3. A02 — OpenSpec lifecycle truth

Update only checkbox/status prose in
`openspec/changes/v72p2d7-provenance-safe-cross-layer-discriminator/tasks.md`:

- R14–R19 checked complete with their actual commit/review evidence;
- remove stale claims that R15–R19 are future/not performed;
- preserve all non-goals and scientific wording;
- add A1 command-closeout item and check it only after §4 passes.

Do not rewrite completed implementation or invent new acceptance work.

## 4. A03 — fresh zero-decoder reachability

From verified repository root, as separate commands:

1. prove `.venv/bin/python` executable, Python 3.12.3, NumPy import/version;
2. prove `/usr/bin/timeout` GNU 9.4; no rehearsal needed if unchanged;
3. run `--help` using `.venv/bin/python`, exit 0;
4. run `--dry-run` using `.venv/bin/python`, verify 193 lines and exact 192 slots;
5. run one unauthorized exact-shape probe using the corrected interpreter,
   expect exit 3 before loader/decoder/root;
6. external-cwd sentinels may use the absolute resolved venv interpreter only
   for import/bind proof, with zero decoder calls/Model-F reads/root;
7. recheck target glob absent, protected metadata unchanged and all auth false.

Every probe is a separate shell command. No chained environment/scientific
command. Any deviation is STOP; do not compensate with PATH activation.

## 5. A04 — independent A1 review

An independent reviewer reads the actual changed docs and reruns §4. Create:

`D7_E_PRE_EXECUTE_REVIEW_VENV_A1.md`

in the D7-E cycle directory. Required unique verdict:

`D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_A1_AWAITING_EXPLICIT_AUTHORIZATION`

The review must state that it supersedes R1 only for command/environment
reachability, that all R1 scientific checks remain valid, and that it grants no
authorization. FAIL stops; no repair beyond one docs-only correction/re-review.

## 6. A05 — state and commit

On PASS:

- keep `state/next_gate: D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`;
- set `d7e_pre_execute_review` to the A1 PASS token;
- add the addendum path and exact interpreter `.venv/bin/python` as factual
  readiness fields;
- keep every authorization/decoder/result/acceptance/promotion field unchanged.

Commit only OpenSpec/docs/state paths:

`docs(d7-e): close venv command reachability before execution authorization`

No production files, tests, workspace roots, decision-log/memory scientific
conclusion or push.

## 7. Return

Report A01–A05, changed paths, corrected command, literal probe outputs, review
verdict, commit SHA, task checkbox closure, target absence, protected-root
equality, all-auth-false and no-push.

Success ending:

`D7-E 的冻结科学合同与实现未变；执行命令已收口为 repo venv 的 .venv/bin/python，OpenSpec 生命周期与 renewed Pre-EXECUTE A1 一致，现等待新的明确执行授权。`

STOP ending:

`STOP — D7-E venv command closeout 未通过；未运行 decoder、未创建结果根、未改变授权。`
