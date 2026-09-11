# D7-E execution packet addendum VENV A1 (interpreter spelling correction only)

- Authority: `.workbuddy/tasks/D7_E_PREEXEC_VENV_COMMAND_CLOSEOUT_A1_TASK_PACKET.md`
  §2 (A01 only). Entry HEAD `031deee70378c19d5d8e32e3a2a2461d0c2343c5`.
- Status: this addendum supersedes ONLY the interpreter spelling and
  environment portions of `D7_E_PREREG_R1.md` §4 and
  `D7_E_EXECUTION_PACKET_R1.md` ("Exact future WSL command"). The R1
  scientific contract, matrix (R08), formulas and estimator identity
  (R09), eligibility (R10), labels (R11), terminal priority (R12),
  budgets (R13), root contract, seven-file schema, and authorization
  lifecycle are untouched and remain as frozen in R1.
- This addendum grants no execution authorization and runs nothing.

## Corrected exact future command (sole authorized spelling)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>
```

- Operational precondition: cwd is the repository root;
  `test -x .venv/bin/python` passes and `.venv/bin/python -c "import
  numpy, pytest; print(numpy.__version__)"` succeeds.
- Do not activate another venv, use bare `python`/`python3`, add
  `PYTHONPATH`, or alter child argv through a wrapper. GNU timeout
  (`-k 30`, `1800`) and every scientific parameter
  (`--model-f-root workspace/v72p2d5_model_f_input/20260907_r1`,
  `--out-root workspace/d7_e_cross_layer_discriminator_<uuid>`) are
  unchanged from R1.
- Rationale (factual, from R1 Pre-EXECUTE review): default `PATH` has no
  `python`; all successful R1 probes used `.venv/bin/python` explicitly
  while the frozen command still spelled bare `python`. This addendum
  closes that launch-reachability mismatch; no scientific content changes.

## Supersession scope (exhaustive)

- Superseded: the bare-`python` interpreter spelling and any implied
  PATH-based interpreter resolution in R1 §4 / exact-command sections.
- Not superseded: everything else in R1 (question, identities, seeds,
  rows, mothers, Model-F root, decoder contract, slot order, transfer
  formulas, estimator identity, eligibility, labels, terminals, budgets,
  schema, verifier contract, reviews, authorization lifecycle).
