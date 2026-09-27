# M2 accounting replay tasks

- [ ] A1: Implement `comparison_bench/src/comparison_bench/cli/m2_accounting_replay.py` exactly per design. No import from decoder/construction modules; stdlib JSON and argparse suffice. Explicit paths only, stdout only, no D2 or backend conclusion.
- [ ] A2: Add `comparison_bench/tests/test_m2_accounting_replay_fake.py` using tiny synthetic summary dictionaries. Assert EC and both tag formulas, unit guards, source/arm separation, and no output file creation. Tests must not read the real roots or `.ttbin`.
- [ ] A3: Run only the focused fake test, report exact command/result and scoped file manifest. Do not run the three real roots, edit any original artifact, or commit/push. Return on A1–A3 complete or a concrete blocker.
