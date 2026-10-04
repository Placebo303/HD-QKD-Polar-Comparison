# Tasks — NB-LDPC L1 degree-2 layout Stage-1 (implementation-only)

Branch `formal-ir-v72p1-addendum-clean`. No commit/push. Allowed commands only
(`py_compile` + the focused `pytest` line below). Forbidden flags:
`--batch`, `--execute*`, `--forward-batch`, any benchmark/sweep/replay.

- [ ] S101: freeze the exact additive file manifest + the single module name
  (`proposal.md` §Impact scope; `design.md` §1). No `v72p2d14*` name.
- [ ] S102: implement `nbldpc_l1_degree2_layout.py` F-1 (L055 cells, shared
  backbone, d3-first / d2-seeded-permutation Phase B, frozen §3 priority,
  deterministic replay, A1–A6 via `r2`, no new predicates).
- [ ] S103: implement F-2 (frozen coefficient stream via `r2` import; matrix
  conversion via `r2` import, zero copies) + GF32/symbol-mapping wrappers.
- [ ] S104: implement thin driver F-3 (fixed H2, shared frame/prior/binding,
  `oracle=False` hardcoded both arms, no oracle switch, no D11 outer runner,
  injected `decode_fn` only, CHECK_UPDATED forward semantics).
- [ ] S105: reserve F-4 output schema (`RESULT_SCHEMA_COLUMNS`, status set,
  `accepted_wrong` isolation, disclosure-on-attempted semantics; no data
  produced).
- [ ] S106: write `test_nbldpc_l1_degree2_layout.py` (S-T01–S-T05, fake-only).
- [ ] S107: write `test_nbldpc_l1_degree2_driver.py` (S-T06–S-T08, fake-only).
- [ ] S108: run `py_compile` + focused pytest; collect PROFILE_ONLY
  structural records (stdout/memory objects, no production root); report
  (a) full PASS with file list + test output, or (b) concrete blocker.

Focused test matrix (T0/T1 only, fake runner; S-T04 seeds in
`GRAPH_SEEDS`, PROFILE_ONLY, no decoder):

- S-T01 GF32 add/mul/syndrome vs tiny oracle full equality.
- S-T02 symbol-mapping roundtrip.
- S-T03 S/C at n128/n256: n, m, degree counts, edge count, check
  distribution, syndrome bits vs L055 table item-by-item.
- S-T04 A1–A6 admission (both arms × frozen seeds, PROFILE_ONLY) all PASS,
  else STOP with no seed change.
- S-T05 noiseless small example: U1/U2/pair/syndrome/verify semantics 100%
  with correct separation.
- S-T06 isolation diagnostic truth-swap invariance.
- S-T07 failed-frame disclosure + accepted-wrong isolation + abort≠success.
- S-T08 no-production-call guard (explicit fake injection; missing fake
  refuses; grep finds no default production binding).

Stop rules: requirement ambiguity → stop, return to planner; infeasible under
equal degree counts → record infeasible, stop; any T0/T1 FAIL → stop;
forbidden-file / real-input / production-decoder contact → stop; out-of-budget
test expansion → stop.
