# D6 R1d BP provenance compatibility — implementation review R1 (Track A R05)

Verdict: `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_PASS`

Authority: `.workbuddy/tasks/D7_E_CROSS_LAYER_READINESS_AND_D6_COMPAT_R1_TASK_PACKET.md` §2 (R05 only).
Role: independent Track A implementation reviewer. Review-only; no commits, no code edits,
no decoder/Model-F content, no roots. The reviewer did not write the repair.
Scope: uncommitted working tree only. Entry HEAD verified `4a5206fbb1d933262f7f51b1855a152985fc508e`
(`git rev-parse HEAD`, branch `formal-ir-v72p1-addendum-clean`).

Under review (all verified from source, not from the operator summary):

- `scripts/v72p2d6_graph_mother_development.py` (working-tree diff: 49 insertions / 10 deletions).
- `comparison_bench/tests/test_v72p2d6_bp_provenance_compat.py` (new, 14 tests).
- `openspec/changes/v72p2d6-r1d-bp-provenance-compat/` (proposal.md, design.md, tasks.md,
  specs/d6-r1d-bp-provenance-compat/spec.md).
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_ADDENDUM_BP_COMPAT_A1.md`.

Frozen references confirmed from source:

- Accepted BP contract: `comparison_bench/.../formal_ir/v35_algorithm_development.py:523-551`
  (`BELIEF_PROVENANCE_*` tokens, `UnconditionedBeliefProvenanceError`,
  `require_check_updated_provenance` exact-token gate).
- Accepted six-tuple: `comparison_bench/.../formal_ir/v72p2d5_gf32_rate_mother.py:1026-1060`
  (`_decode_block` returns `(exact, syndrome_ok, it, finite, beliefs) + (provenance,)`,
  i.e. six normally, seven with `return_syndrome`).
- Prior R1d Pre-EXECUTE (`D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1D.md`) is declared stale and
  superseded by the addendum §1 ("no longer describes the code", "retained as history",
  "grants no execution"). It grants nothing; R1d stays paused/optional.

## Per-check evidence

### 1. R01 reproduction credible — PASS

Verified against `git show HEAD:...` (pre-repair code):

- Five-unpack at HEAD `scripts/v72p2d6_graph_mother_development.py:126`:
  `e, s, it, f, bel = core._decode_block(dec, h, prior, xt)`. Against the accepted
  six-returning `_decode_block` this raises `ValueError: too many values to unpack
  (expected 5)` — pinned behaviorally by new test `test_five_unpack_of_six_raises_value_error`.
- The broad worker `except` (HEAD L132-135, `except Exception as ex: ... crash consumes the cell`)
  maps that arity error to a crash cell (`crash=True`, `iterations=-1`, `error=repr(ex)`).
  New test `test_five_value_incompatibility_is_loud_and_not_ready` reproduces the mapping
  on the task path (keeps loud `ValueError`/`expected 6, got 5` signature in `error`).
- Warmup pre-fix (HEAD L108-116) discards the `_decode_block` return value and reports
  `warmup="ok"` on any non-raising call — shape-blind. Post-repair it validates shape.
- Unguarded path pre-fix (HEAD `run_cell` L778-793): pops L1 beliefs, unconditionally builds
  `q = softmax(bel)`, calls `d5.app_fed_l2_prior(p2, bob, q)` with no provenance check.
  The repair gates exactly this block; spy tests confirm the mixer now runs only on
  `CHECK_UPDATED`.

### 2. Six-value unpacking exact; provenance via explicit IPC; beliefs transient-only — PASS

- Worker unpacks exactly `e, s, it, f, bel, prov = core._decode_block(dec, h, prior, xt)`
  (source-pin test asserts the literal line).
- IPC dict carries `"belief_provenance": prov` explicitly (source-pin test asserts both
  `'"belief_provenance": prov'` and `'"belief_provenance": res.get("belief_provenance")'`).
  Provenance flows even when `return_beliefs` is false
  (`test_provenance_flows_even_when_beliefs_not_requested`: beliefs None, provenance present).
- Beliefs remain transient-only: included only when the task sets `return_beliefs` and the
  value is non-None (unchanged condition); `run_cell` pops both `beliefs` and
  `belief_provenance` from the in-memory rec; CSV writer
  (`scripts/...:983-986`) writes only `{k: r.get(k) for k in DECODER_FIELDNAMES}`,
  so neither key can reach persisted records. `DECODER_FIELDNAMES` list itself is
  byte-identical (frozen-schema test compares the full 23-name list).

### 3. CHECK_UPDATED gate exact; q numerics unchanged; deterministic fail-closed record — PASS

- `run_cell` calls the accepted `require_check_updated_provenance(prov, consumer="D6 run_cell L1->APP-L2")`
  via lazy import of `comparison_bench.formal_ir.v35_algorithm_development` (no V35 edit —
  `git diff --name-only` on the V35/D5/D6-module paths is empty). Exact token match only;
  `None`/missing/unknown all refused by the helper's `!=` comparison.
- On pass: the `softmax(bel)` → `app_fed_l2_prior` lines are textually identical to HEAD
  (re-indented under the `else` branch only) — q numerics unchanged. Spy test
  `test_check_updated_passthrough_runs_app_and_l2` observes exactly one mixer call with
  shape `(N, 32)` and three dispatched worker calls (L1 + L2-APP + L2-oracle).
- On refuse (`PRIOR_ONLY`, `WARM_START_UNSPECIFIED`, `None`, unknown token, missing key):
  no `q` constructed, mixer spy silent (`app_calls == []`), only 2 worker calls
  (L1 + L2-oracle; no L2-APP decode dispatched, no budget consumed — `state["calls"] == 2`).
  The L2-APP slot is the `skip=True` placeholder (`call_idx=-1` per `invoke` L855-856;
  such rows are excluded from flush per L980), overwritten to a deterministic named record:
  `crash=False`, `finite=True`, `error="provenance-blocked:belief_provenance=<repr(token)>:want-CHECK_UPDATED:no-L2-APP-decode"[:300]`,
  in-memory `note == PROVENANCE_BLOCKED_NOTE`. Never `crash=True`, never an L2 APP decode.
  Parametrize covers 4 refused tokens + missing-key test covers the legacy no-key dict.
- L1-crash path keeps the legacy `app-undefined-l1-unavailable` skip record
  (`crash=True`, no `provenance-blocked` marker) — non-BP record path byte/field compatible.

### 4. Warmup fails loudly; worker except NOT broadened — PASS

- Warmup validates `len(tuple(wres)) != 6` → raises
  `ValueError("decoder-result-shape-incompatible: want 6 ..., got %d")`, caught by the
  unchanged warmup `except` → hello carries `ready=False`, `warmup="fail:<reason>"`.
  Compatible shape → `ready=True`, `warmup="ok"` (existing behavior preserved).
  Tests: `test_five_value_incompatibility_is_loud_and_not_ready`,
  `test_warmup_exception_reports_not_ready`, six-value ready-true test.
- Both worker `except` clauses are textually unchanged
  (`except Exception as ex:  # noqa: BLE001` warmup;
  `except Exception as ex:  # noqa: BLE001 - crash consumes the cell` task path —
  asserted literally by `test_source_wiring_pins`). Arity/programming errors keep their
  loud `ValueError` signature; nothing is re-labeled or silenced.

### 5. No science drift; schema unchanged; focused suites re-run by reviewer — PASS

- Diff touches no arms/seeds/rows/mothers/schedules/estimators/thresholds/budgets/watchdog/
  terminals: `git diff` on the script shows zero hunks outside `_worker_main` warmup+unpack+IPC,
  `run_cell` gate, `invoke` provenance threading, and the `PROVENANCE_BLOCKED_NOTE` const.
  Frozen pins asserted in-test: `R1D_ARMS` (3 arms), `R1D_VALID_SUBSET` (22),
  `MODES == ("L1", "L2-APP", "L2-oracle")`, `POINTS == ("f1.0", "f1.2", "square")`.
- `DECODER_FIELDNAMES` unchanged (full-list equality test); CSV writer/verify paths untouched.
- Reviewer re-ran all four suites, separate processes, fresh task-owned basetemps,
  `-p no:cacheprovider`, zero real decoder (fake `_decode_block`/fake workers only;
  production `bind_historical_decoder` patched to a counting sentinel in the new tests;
  no `--phase`/R1d/G1/G2/Model-F/root/UUID in any command). Literal results:

| Suite | Command (each own process, own basetemp) | Result |
|---|---|---|
| New compat | `pytest comparison_bench/tests/test_v72p2d6_bp_provenance_compat.py` (`/tmp/d6rev_compat_mBzFr8`) | **14 passed** |
| D6 focused | `pytest comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (`/tmp/d6rev_mother_oD8PCG`) | **62 passed** |
| R1d suite | `pytest comparison_bench/tests/test_v72p2d6_gf32_graph_mother_r1d.py` (`/tmp/d6rev_r1d_EVBvrD`) | **13 passed** |
| BP regression (V35 contract) | `pytest comparison_bench/tests/test_v35_algorithm_development.py` (`/tmp/d6rev_bp_fu2how`) | **25 passed** |
| BP regression (D7 provenance) | `pytest comparison_bench/tests/test_v72p2d7_bp_belief_provenance.py` (`/tmp/d6rev_bp2_Drk5yq`) | **23 passed** |

  Total reproduced by reviewer: 137 passed, 0 failed.

### 6. Scope clean — PASS

- Repair file set is exactly the seven listed paths: the D6 script (modified) +
  the new compat test + proposal/design/tasks/spec (4 OpenSpec paths) + the addendum.
  No D7-E files exist or were touched (`ls` for `*cross_layer*`/`*d7_e*` in
  `scripts/` and `formal_ir/` returns nothing; R14-R19 not started).
- No `v35_algorithm_development.py`, `v72p2d5_gf32_rate_mother.py`, or
  `v72p2d6_gf32_graph_mother.py` edits (empty `git diff --name-only` on those paths).
- No evidence roots: `workspace/d6_r1d_tests_*` are prior test basetemps (contain only
  `test_*` pytest subdirs), not R1d/D7-E result roots; no new root created by repair or tests.
- No authorization changes: no auth/promotion keys in the diff; addendum explicitly grants nothing.
- Pre-existing unrelated dirty tree / CRLF warnings / external V35 rewrites preserved
  untouched per packet §1 prohibitions (no clean/reset/stash/broad-stage performed).
  Other untracked R1C-era cycle docs in the same directory predate this repair and are
  outside the seven-path scope; left alone.

## Discrepancies

None blocking. Two non-blocking observations:

- Diff stat reads 49 insertions vs the operator-claimed "+48/−10" (deletions match at 10).
  One-line count difference is comment/blank-line accounting, not a semantic gap —
  every claimed hunk (warmup validation, unpack, IPC dict, pop, gate, blocked record,
  invoke threading) is present and source-pinned by tests.
- The repair's warmup gate uses `len(tuple(wres))`; a non-iterable decoder return would raise
  `TypeError` instead of the named `ValueError`, but it still lands in the same loud
  `ready=false`/`fail:` path — fail-closed either way, no rework warranted.

## Checklist

- [x] Matches OpenSpec spec (`v72p2d6-r1d-bp-provenance-compat` proposal/design/tasks/spec + addendum)
- [x] Tests pass (reviewer-reproduced literal counts above: 14 + 62 + 13 + 25 + 23)
- [x] No scope creep (seven listed paths only; no D7-E, no V35/D5/D6-module, no roots, no auth)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? — No: Track A R05 is a
  code/readiness review artifact only; state/roadmap updates belong to R21 (Track B owner),
  and no new reusable failure mode was encountered (venv `python` shim absent; used `.venv/bin/python`).

Review doc: `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_R1.md`
(sole reviewer write; uncommitted; no code edited; HEAD still `4a5206fbb1d93...`).
