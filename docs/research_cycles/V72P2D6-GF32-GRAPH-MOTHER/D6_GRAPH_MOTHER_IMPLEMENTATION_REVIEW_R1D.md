# D6 graph/mother implementation review R1d (read-only)

Reviewer: independent re-check pass over landed commits `8e8e4ae` (freeze)
and `cddaaed9` (implementation+tests). No files edited during review (this
file excepted at commit time). Independence mechanism: fresh reads of the
landed diff (never the operator's notes), fresh subset derivation from
`ROW_BUDGETS` + role rules (no `R1D_VALID_SUBSET` read for construction),
one live structure-only recompute spot-check, and the recorded test outcomes
below (356/356 green in a fresh task-owned basetemp). This review never
authorizes execution.

## Scope

`comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
(+121, pure append at EOF), `scripts/v72p2d6_graph_mother_development.py`
(+166/-19, `--r1d` branches + frozen-shape-preserving callsite),
`comparison_bench/tests/test_v72p2d6_gf32_graph_mother_r1d.py` (+459, new),
R1d OpenSpec (4 files) + 2 cycle docs + decision-log/memory/state appends.

## Re-checks

1. Mother diff is append-only (`@@ -977,3 +977,124`, zero deletions):
   no `_build_*`, `build_support`, `assign_mother_from_support`,
   `audit_extra`, or gate hunk touched. A4/A6 builder path intact. PASS.
2. `R1D_ARMS` is exactly {B0,B1,T1}; `R1D_NEW_ARM`/`R1D_SCALING_FALLBACKS`
   are T1; schema/semantics markers `r1d-v2`/`frozen-AND-I1`. PASS.
3. `R1D_VALID_SUBSET` (22 cells) equals the reviewer's independent
   derivation from `ROW_BUDGETS` + canary/confirmation/scaling role rules
   (22 == 22, set-equal); every derived cell is frozen+I1-valid in the
   accepted CSV (0 invalid); live spot recompute T1 n256-L2-square gives
   (rmin 2, nbelow 0). PASS.
4. Guard fails closed: `assert_r1d_arm` rejects all 5 non-R1d arms;
   `assert_r1d_dispatchable` requires subset membership AND live degree≥2
   (tested incl. a structurally fine but out-of-subset T1 cell). PASS.
5. `enrich_r1d_records` copies dicts (frozen dicts unmutated — old writer
   output provably unchanged); v2 writer header is frozen columns +
   the two I1 fields, new-roots-only. PASS.
6. `R1D_REFUSED_ROOTS` names exactly the historical A2 root + 3 VOID roots
   (A2-01 UUIDs match); refusal fires before the exists-check. PASS.
7. Runner: frozen default call shapes preserved (A4 callsite-pin test green
   in-suite); `--r1d` default off; `run_cell` R1d guard gated on
   `state["r1d"]`; selection/fallback asserts (`{B0,B1,T1}`, `fallback_M`
   None); scaling T1-only assert; manifest/summary markers R1d-only;
   `--verify` old-root behavior byte-identical in logic (A5 historical test
   green in-suite; v2 gate fires on marker only). PASS.
8. Tests: 13 tests cover all 12 packet properties (arm set; non-dispatch;
   T1-only fallback + control semantics; 22/22 live+CSV eligibility; invalid
   cell pre-decoder refusal with `_NoCall` zero-calls; schema-v2 present +
   recomputable; old schema readable + immutable; crash/nonfinite override +
   terminal agreement; no-reuse incl. `--r1d` refusal `SystemExit(2)`;
   seq==par + unchanged-output pin; source wiring pins; `--dry-structure`
   behavioral R1d run; fake e2e v2 root verifies with production decoder
   stubbed to raise). Fake-only, task `tmp_path` basetemps. PASS.
9. Zero decoder calls in implementation and tests (builders/verify only;
   e2e stubs `bind_historical_decoder` to raise via monkeypatch). PASS.
10. Dirty-tree scope: staged paths exactly the 11 scoped files; unrelated
    V35/perf-v38/CRLF churn untouched; no R1d output root created. PASS.

## Findings

- One correction applied pre-review by the operator (not a review finding):
  the freeze layer counted 26 role-cells as distinct cells; the code
  frozenset held the correct 22 distinct cells and all docs/tests were
  corrected to 22 before this review. No rework requested.
- No blocking finding. Zero rework rounds used (one scoped operator-side
  test-shape fix for the A4 callsite pin preceded this review; the pin
  itself is green).

## Verdict

`D6_R1D_IMPLEMENTATION_REVIEW_PASS` — the eligible-only dispatch layer, the
`--r1d` runner mode, and their tests are landed and correct; frozen builders,
gates, writers, and historical evidence are unchanged.
