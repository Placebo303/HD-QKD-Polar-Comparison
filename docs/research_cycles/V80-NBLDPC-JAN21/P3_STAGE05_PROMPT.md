# P3 Stage 0.5 Operator Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track **DECIDE** (raw `.ttbin` data, minimum viable contact). Branch context `formal-ir-v72p1-addendum-clean`; publication branch untouched. No switch, no commit, no push, no PR. ID **G-P3-STAGE05**: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/P3_STAGE05_PACKET.md` (§§1–9 frozen) + `P3_STAGE05_PREREG_AND_AUTH.md` (signature required).
- Zero histograms, zero coincidences, zero pairs, zero entropy. Zero decoder/DE/graph/`tools/*` calls.

## Before anything (stop conditions)

1. Confirm the signed `P3_STAGE05_PREREG_AND_AUTH.md` names the 10 base paths (packet §2 order), thin module, UUID, G3 tolerance, and wall ceiling. Any blank ⇒ **STOP-BLOCKED**, return to main thread. Do not fill them in yourself.
2. Confirm intended branch, scoped cleanliness, output absence (`workspace/p3_stage05_*` absent; `rg 'p3_stage05_'` only in this packet family). Record Q0–Q5 Pre-EXECUTE. FAIL ⇒ stop.
3. Stage 0 smoke (no data): `PYTHONPATH=<repo-root> .venv/bin/python -c "from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias; install_timetagger_alias(); from TimeTagger import FileReader; print('smoke OK')"`. FAIL ⇒ **STOP-BLOCKED** (never modify `src/`; the alias is the only adapter).
4. Root: fresh additive `workspace/p3_stage05_<uuid8>` (absence re-proved with the final UUID immediately before launch). `results/` and `comparison_bench/outputs_comparison/` forbidden. Existing evidence roots untouched.

## Per dataset (packet §2 order, ONLY the base member)

5. Open ONLY `X.ttbin` via `FileReader`. Never open `.1` alongside; never concatenate. Base fails to open ⇒ single-member `.1` shard-only fallback (record `fallback_used=true`); both-members-needed ⇒ **STOP-BLOCKED** (G1).
6. `getConfiguration()` → dump VERBATIM to `<id>.json` + record Python type (`dict` vs `str` — resolve empirically). Note present/absent keys for: acquisition start; channel roles/gates/markers; PM/EB + phase-matching (Type0/Type2/SHG); split/part structure. Invent nothing.
7. `getChannelList()` + `getLastMarker()` → record verbatim.
8. Span: bounded `hasData()`/`getData(n)` drain keeping ONLY first/last timestamps; discard each array immediately. Record `t_first_s`, `t_last_s`, `duration_measured_s`, `filename_duration_tag`, `tag_disputed`. Span ≤ 0 ⇒ STOP-BLOCKED (G2). |span − mtime-gap| beyond tolerance ⇒ STOP-BLOCKED (G3).
9. Write `<id>.json` with the packet §6 keys including `pm_eb_evidence` (exactly what the config DOES and does NOT establish) and `gates_G1_G4` + `status`.

## Close out

10. Write `duration_table.md` (`duration_measured_s` vs `filename_tag` vs `tag_disputed`, all 10) + `config_notes.md` (present/absent keys per dataset for roles/gates/PM/EB/phase-matching/split-structure).
11. Budgets: ≤300 s/read; ≤2 reads/dataset; ≤1800 s total; RSS < 4 GiB; 0 decoder/DE/graph calls; 0 arrays to disk. Wall-partial ⇒ `INCOMPLETE`, retained, no continuation.
12. FORBIDDEN: both-member open/concat; histograms/coincidences/pairs/`counts_ab`/entropy/weights/drift/ACF/splits; excluded derived artifacts; `results/` or `comparison_bench/outputs_comparison/` writes; `src/` edits; inventing keys, durations, or channel plans; committing or pushing.
13. Deliverables: 10× `<id>.json` + `duration_table.md` + `config_notes.md`. Then independent batch-end review → main-thread acceptance. No publication before that review.

## Lessons card (tape to the monitor)

- No UNION-concat (members are NESTED, not disjoint) — prove auto-follow with span-vs-gap, don't dedup-after-concat.
- Future `--authorized` ⇒ `store_true`, never `store_false`.
- `PYTHONPATH=<repo-root>` + `install_timetagger_alias()` before any TimeTagger import; never touch `src/`.
- Duration MEASURED, never tagged; Jan-12 = 30.0 s, tag disputed.

## Interpretation / claim ceiling

14. Claim ceiling: file-identity verdict + span table + config survey. Does NOT establish `H_full`, alignment, FER, SKR, a route decision, qualification, or a publication number. A `getConfiguration()` payload that supplies channel roles/gates is a recommendation (branch-B FITTED → READ-FROM-FILE candidate) for the main thread — the operator decides nothing.
15. **Pre-EXECUTE Q0–Q5 + the signed user grant are required before ANY execution. This prompt authorizes NOTHING.**

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved there; retained for history.
