# P3 Stage 0.5 Probe Packet — File Identity + Span Continuity + Config Survey (2026-09-21) — FROZEN, NOT GRANTED

- Track: **DECIDE** (raw acquisition `.ttbin` data). Why DECIDE, explicitly: it opens real/private/raw vendor acquisition files — DECIDE-eligible per `AGENTS.md` §1.2 ("Real/private/raw data … always DECIDE"). Scoped as the **minimum viable real-data contact**: header/config accessors + a first/last-timestamp span drain ONLY; zero histograms, zero coincidences, zero pairs, zero entropy. Its outputs gate (but do not authorize) the full P3 census.
- Acceptance ID: **G-P3-STAGE05** (packet frozen, NOT granted). Authorizes NOTHING. Nothing may run without the signed companion `P3_STAGE05_PREREG_AND_AUTH.md` + Pre-EXECUTE + explicit user grant.
- Authorities: `docs/DATA_INVENTORY_20260921.md` §1 (10 pairs, resolved paths); `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §§C–D (nested/superset semantics, measured durations); `docs/TTBIN_ENV_SETUP_20260921.md` verification section (Stage 0 PASS, alias shim, FileReader surface); parent P3 packet `P3_CENSUS_PACKET.md` §§2/4.4/11 (prohibition, measured-duration rule, env notes).
- Branch context: `formal-ir-v72p1-addendum-clean`; publication branch `formal-ir-v80-nbldpc-jan21` untouched. No switch, no commit, no push, no PR.
- **Nothing has been executed under this packet. No `.ttbin` has been opened under this packet. No workspace root has been created. No output has been written.**

## 1. Question (single, falsifiable)

- Does `FileReader("X.ttbin")` alone yield the full acquisition stream (auto-follow proven by span-continuity), and what does `getConfiguration()` verbatim contain — in particular anything bearing on channel roles/gates/markers, PM/EB and phase-matching (Type0 vs Type2 vs SHG), acquisition start, and split/part structure?
- Pre-registered NON-predictions: no span value beyond the two already measured (Jan-12 29.9999524 s, Jan-21-2M 2.9999997 s — authority semantics §C–D, quoted as prior evidence not as this packet's output); no config key is pre-registered; PM/EB relevance is UNPROVEN until measured.

## 2. Dataset manifest (10 datasets — open ONLY the base member)

Resolved POSIX paths from `docs/DATA_INVENTORY_20260921.md` §1. The probe opens ONLY the `X.ttbin` column (never `.1`, never both — §4 prohibition):

| id | family | base `X.ttbin` to open (ONLY) | fallback `.1` (shard-only, ONLY if base fails to open) | filename tag |
|---|---|---|---|---|
| JAN12 | D early Type2PPLN | `/mnt/d/Data/Raw Data/2026.1.12/Type2PPLN_3s_2026-01-12_165236.ttbin` | `/mnt/d/Data/Raw Data/2026.1.12/Type2PPLN_3s_2026-01-12_165236.1.ttbin` | `3s` (KNOWN-DISPUTED, measured 30 s) |
| SHG-A | C SHG | `/mnt/d/Data/Raw Data/2026.1.13/SHG_Type2PPLN_3s_2026-01-13_162106/SHG_Type2PPLN_3s_2026-01-13_162106.ttbin` | `.../SHG_Type2PPLN_3s_2026-01-13_162106.1.ttbin` | `3s` |
| SHG-B | C SHG `_2` | `/mnt/d/Data/Raw Data/2026.1.13/SHG_Type2PPLN_3s_2_2026-01-13_162148/SHG_Type2PPLN_3s_2_2026-01-13_162148.ttbin` | `.../SHG_Type2PPLN_3s_2_2026-01-13_162148.1.ttbin` | `3s` |
| T0-500K | A Type0 | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_500K_3s_2026-01-20_193050/Type0_nofilter_500K_3s_2026-01-20_193050.ttbin` | `.../Type0_nofilter_500K_3s_2026-01-20_193050.1.ttbin` | `3s` |
| T0-1M | A Type0 | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_1M_3s_2026-01-20_192857/Type0_nofilter_1M_3s_2026-01-20_192857.ttbin` | `.../Type0_nofilter_1M_3s_2026-01-20_192857.1.ttbin` | `3s` |
| T0-1.5M | A Type0 | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_1_5M_3s_2026-01-20_193255/Type0_nofilter_1_5M_3s_2026-01-20_193255.ttbin` | `.../Type0_nofilter_1_5M_3s_2026-01-20_193255.1.ttbin` | `3s` |
| T0-2M | A Type0 | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_2M_3s_2026-01-20_193411/Type0_nofilter_2M_3s_2026-01-20_193411.ttbin` | `.../Type0_nofilter_2M_3s_2026-01-20_193411.1.ttbin` | `3s` |
| T2-1.5M | B Type2 trio | `/mnt/d/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin` | `.../Type2_1-5M_3s_2026-01-21_183806.1.ttbin` | `3s` |
| T2-1M | B Type2 trio | `/mnt/d/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin` | `.../Type2_1M_3s_2026-01-21_184040.1.ttbin` | `3s` |
| T2-2M | B Type2 trio (V80 source) | `/mnt/d/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin` | `.../Type2_2M_3s_2026-01-21_183657.1.ttbin` | `3s` |

Note on 1.12 layout: files sit at the date root with no per-dataset subfolder (inventory §3 item 1) — tooling MUST special-case it, not assume `<date>/<dataset>/*.ttbin` nesting.

## 3. Frozen procedure (per dataset, in order)

1. Env: repo `.venv` (`.venv/bin/python`); call `comparison_bench/src/comparison_bench/io/ttbin_compat.py::install_timetagger_alias()` BEFORE any TimeTagger import (bare `import TimeTagger` fails — authority env-setup Task 4/verification); `PYTHONPATH` MUST include the repo root (`/mnt/d/Code/HD-QKD_Polar_Comparison`) or entrypoints fail with `No module named 'src'`.
2. Open ONLY `X.ttbin` via `FileReader("X.ttbin")`. Never open `.1` alongside; never concatenate. If and ONLY if the base fails to open, fall back to shard-only `FileReader("X.1.ttbin")` (single member, still never both) and record the fallback.
3. `getConfiguration()` → dump the raw value VERBATIM to JSON; record its Python TYPE (`dict` per docs vs `std::string` per signature — resolve empirically). Extract, if present: acquisition start time; channel roles/gates/markers; anything bearing on PM/EB and on phase-matching (Type0 vs Type2 vs SHG); anything indicating split/part structure (part index, sequence name, file count). Absent keys are recorded as absent — never invented.
4. `getChannelList()` and `getLastMarker()` → record verbatim.
5. Span: minimal bounded drain via `hasData()`/`getData(n)` keeping ONLY first and last timestamps; discard each array immediately; never materialise the full stream. Record `t_first`, `t_last`, `duration_measured_s = t_last − t_first` (seconds), plus `filename_duration_tag` and `tag_disputed = (duration_measured_s disagrees with tag)`.
6. Write per-dataset `<id>.json` + one row in the shared markdown duration table (§6 outputs) into the fresh additive root. `pm_eb_evidence` field states exactly what the config DOES and does NOT establish (no inference beyond quoted keys).

## 4. HARD PROHIBITIONS (probe-level, in addition to P3 census forbiddens)

- NEVER open both members of a pair; NEVER concatenate (UNION) streams — same prohibition as `P3_CENSUS_PACKET.md` §2 (nested/superset semantics, `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §C). Violation invalidates the dataset row.
- FORBIDDEN computations: histograms, cross-correlations, coincidences, pairing, pairs, `counts_ab`, `N_ab`, any entropy (`H_full`/`H_L1`/`H_L2`/MM/gap/CI), weights, drift, autocorrelation, splits.
- FORBIDDEN I/O: writing event/timestamp/channel arrays to disk (first/last scalars only); opening any excluded derived artifact (`results*/`, `e2e_new_ttbin_fullgrid_*/`, `sidecars/`, `run_config*.json`, `*.opju`/`*.pptx`/`*.xlsx`, JSI/histogram sidecars — inventory §1); writing to or touching `results/` or `comparison_bench/outputs_comparison/`; modifying anything under `src/` (frozen, `AGENTS.md` §5.1).
- FORBIDDEN calls: decoder, DE, graph construction, `tools/longrun_*`/`minrerun_*`/`routeA_*`, `experiments/run_e2e_pipeline.py`.

## 5. Gates (frozen, binary per dataset + batch)

- **G1 both-or-neither**: if EITHER member must be combined with the other to succeed (i.e. the operator is tempted to open both) ⇒ STOP-BLOCKED for that dataset, return to main thread. Both members are never opened in one process.
- **G2 span > 0**: `duration_measured_s > 0`, else STOP-BLOCKED.
- **G3 span-vs-gap consistency**: |span − (mtime(`X.1`) − mtime(`X`))| within the frozen tolerance (tolerance value frozen at Pre-EXECUTE, proposed 0.5 s to cover close/flush latency; `[TO BE CONFIRMED at authorization]`). Mismatch ⇒ STOP-BLOCKED (span ≈ 2× gap ⇒ suspected doubling; span ≪ gap ⇒ suspected truncation).
- **G4 config parses**: `getConfiguration()` returns a parseable value dumped verbatim; unparseable ⇒ STOP-BLOCKED for config-survey columns (span row still recorded).
- Batch PASS requires all 10 datasets to clear G1–G3 (G4 may pass per-dataset with absent-key recording). Any FAIL ⇒ batch does NOT gate-open Stage 1; escalate to main thread.

## 6. Outputs (fresh additive root ONLY)

- Root: `workspace/p3_stage05_<uuid8>` (absence proven at Pre-EXECUTE; example pattern only — the UUID is frozen at authorization, never invented here). No workspace root exists yet.
- Per dataset: `<id>.json` with keys `dataset_id | base_path | member_opened | fallback_used | config_type | config_verbatim | channel_list | last_marker | t_first_s | t_last_s | duration_measured_s | filename_duration_tag | tag_disputed | mtime_base | mtime_shard | mtime_gap_s | span_gap_agreement | pm_eb_evidence | gates_G1_G4 | status`.
- Shared: `duration_table.md` (per-dataset `duration_measured_s` vs `filename_tag` vs `tag_disputed`) + `config_notes.md` (one row per dataset: which config keys were present/absent for channel roles/gates/PM/EB/phase-matching/split-structure).
- Claim ceiling: file-identity verdict + span table + config survey. Establishes NO `H_full`, NO pairing/window/offset, NO alignment choice, NO FER/SKR/route/qualification/publication number. Whether `getConfiguration()` upgrades any branch-B alignment from FITTED to READ-FROM-FILE is recorded as a recommendation, decided by the main thread.

## 7. Budgets (frozen ceilings)

See the budget table in `P3_STAGE05_PREREG_AND_AUTH.md` §3 (≤300 s/read, ≤2 reads/dataset, ≤1800 s total, RSS < 4 GiB, 0 decoder/DE/graph calls). Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 preregistered engineering repair+rerun for infrastructure failure only (unchanged scientific inputs, failed attempt retained).

## 8. Lessons for any future ingest script (forward-looking guards from the sibling review)

Authority: `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §§A–B,E. The reported script does NOT exist here (zero hits for `stage_b_go`/`stage_a_parse`/`store_false`); these are guards, not fixes:

1. Never assume disjoint members — never UNION-concat `X` + `.1`; open `X.ttbin` only and prove auto-follow with the §5 span assertion (dedup-after-concat is the wrong fix — it masks the error).
2. Any future `--authorized` gate flag MUST be `action="store_true", default=False` (never `store_false`).
3. Any future `scripts/` entrypoint MUST run from the repo root or with `PYTHONPATH=<repo-root>` (else `No module named 'src'`) AND call `install_timetagger_alias()` before the frozen loader's `from TimeTagger import FileReader` (never modify `src/`).
4. Duration is MEASURED (span drain), never the filename tag; Jan-12 stays quarantined (`duration_measured_s=30.0`, `filename_tag_disputed=true`).
5. Do not invent a parallel JSON gate (no `stage_*_go` file); the DECIDE chain (signed prereg + Pre-EXECUTE + Pre-RESULT + main acceptance) is the only gate.

## 9. Entry + authorization gate (STOPS HERE)

- Entry: (a) alias + `PYTHONPATH` smoke (no data: `install_timetagger_alias()` then `from TimeTagger import FileReader` resolves; `import qkd_io.ttbin_pipeline` clean); (b) Q0–Q5 Pre-EXECUTE recorded (intended branch context, scoped cleanliness, frozen contract §§1–8, output-absence + `rg` proofs, focused no-data tests); (c) FRESH EXPLICIT USER GRANT in `P3_STAGE05_PREREG_AND_AUTH.md` signature block. This packet is NOT a grant.
- `[BLOCKING: needs user input]` — the signature, the UUID, and the G3 tolerance confirmation.
- Deliverables: 10× `<id>.json` + `duration_table.md` + `config_notes.md` + `INDEPENDENT_ACCEPTANCE.md` after independent batch-end review, then main-thread acceptance. Prompt: `P3_STAGE05_PROMPT.md`.

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved to the consolidated baseline. This file is retained as history. Executed evidence and review verdicts recorded here remain authoritative; do not cite its frozen clauses as current without checking the baseline.
