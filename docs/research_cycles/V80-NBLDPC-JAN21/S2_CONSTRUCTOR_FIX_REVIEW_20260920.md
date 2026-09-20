# S2 Constructor-Fix Independent Review (EXPLORE) — 2026-09-20

Track: EXPLORE independent review. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
Scope: `nonbinary_v10_peg.py` rework + `test_v10_peg_girth_fix.py` (NEW) + campaign pin updates.
Verdict: **PASS_WITH_FINDINGS** — no blocking issues; constructor fix ACCEPTED as basis for re-freezing the new experiment; this review authorizes nothing itself.

1. D1 selection: unreachable-first verified (`_select_check` L502-510); within reachable, max-depth→free-degree→ACE (L519-535) = local-girth maximization, no contradiction (unreachable ≡ infinite girth). Regression risk is the intended behavior change on all mixed graphs (V1 1158→0); no legacy placement pins exist — 12/12 `test_nonbinary_v10_peg.py` pass (run here).
2. D2 girth: `distance>0` gate (L396-399), acyclic→`None` sentinel; consumers enumerated — `v80_s2_peg.four_cycle_report` + campaign manifest use `.get` (None-safe); v19/v36 read only status/triples/rank/reason; D10 builder untouched with own local logic. Compatible.
3. D3 trials: `tie_seed=seed+(trial-1)`, trial 1 replays legacy stream (label RNG drawn once post-selection, placement-identical); best=min four_cycles, ties→lowest index, early-stop only on 0; failures consume cap; `trials_used`=trials consumed, not winning index. T2 per-trial replay via `seed+t`/`max_trials=1` is sound.
4. Consumers: `construct_l2` recomputes four-cycles independently (same formula); campaign executor + v19/v36 pass-through verified compatible. Tests run here: **30 passed** (7 new + 12 v10-peg + 11 s2-campaign). D10: 2 failures confirmed pre-existing/environmental (Windows `D:/` path assumption under WSL; D10 files untouched by diff) — not fixed per instructions.
5. Result plausibility: dv=2 regular, n=256/m=47 (E=512, avg check deg≈10.9); PEG unreachable-first + best-of-20 → 0 four-cycles + girth 6 is believable; old 1158 consistent with pre-fix reachable-preferring defect. Seed-specific 0/6/47 values sponsor-reported, not recomputed here (no production construction run).
6. Consequences encoded: V1 gate `==0`, V2 gate `<0` unpassable → V2 arm FAILs closed (SCF-01; packet-level adjudication, not a code bug; NOT fixed).
7. Scope: functional delta confined to the 4 files; no root/campaign/results writes; no commit/push. (Working tree also carries unrelated uncommitted journal lines + other-line untracked files — pre-existing, not this rework.)

Findings:
- SCF-01 (adjudication, non-blocking): V2 `<0` gate unpassable by construction — packet must decide V2 disposition at re-freeze (drop / replicate-V1 / new gate); executor behaves as specified.
- SCF-02 (cosmetic, non-blocking): `_select_check` L511-518 `if not reachable` branch is dead (unreachable non-empty returns earlier; candidates non-empty) — remove at next touch.
- SCF-03 (note): winning trial index not stored (`trials_used` = trials consumed) — acceptable per best-of-N semantics; flag only if provenance needs it.

Acceptance: constructor fix accepted as basis for re-freezing the new experiment. This review grants/authorizes no execution.
Return: verdict PASS_WITH_FINDINGS; blocking findings: none; record: this file.
