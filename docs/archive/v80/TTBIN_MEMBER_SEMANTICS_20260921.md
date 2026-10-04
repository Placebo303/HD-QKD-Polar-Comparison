# `.ttbin` Pair-Member Semantics Investigation — 2026-09-21

Investigation of a relayed review claiming a census script (`Stage A/B`, `stage_a_parse.json`,
`--authorized`, UNION-concat at ~lines 243–247) double-counts `X.ttbin` + `X.1.ttbin`,
plus the 3 s-vs-30 s question. Read-only except header/metadata probes + one first/last-timestamp
span read on small members only. No histograms, pairs, counts, or entropies computed. No census run.

## A — Script location: NOT FOUND in either checkout

- `stage_b_go`, `stage_a_parse`: **zero hits** in `/mnt/d/Code/HD-QKD_Polar_Comparison` AND
  `/mnt/d/Code/HD-QKD_Polar_Release` (rg over all tracked + untracked files). No `*stage_a*` /
  `*stage_b*` JSON artifact exists anywhere in either repo or `/tmp/opencode`.
- `--authorized` with `action="store_false"`: **zero hits**. The only `store_false` uses are
  legitimate negations (`--no-resume`, `--no-recompute-corr`).
- The only real census implementation is the sibling's `low_dim_opt/core/ttbin_io.py`
  (`census_curve_files`, curve link census). It does the **opposite** of concatenating —
  `discover_link_files` (lines 118–147) **prefers the small index file and relies on
  FileReader auto-follow**, using `.1.ttbin` only as a shard-only fallback (lines 140–146).
  No `counts_ab`, no `H_full`, no Stage A/B, no `--authorized` in it.
- Our P3 census (`openspec/changes/v80-p3-real-hfull-census/`, `P3_CENSUS_*.md`) is
  **planning-only**: T4 executor unimplemented; T5/T6 authorization unsigned. Our design
  already contains the safeguard — "Stage 0.5 file-identity probe decides which pair member
  is the event stream; both-or-neither ⇒ STOP-BLOCKED" (`design.md` line 79).
- Sibling `workspace/` contains only test-scratch dirs; nothing matching census/stage names.

## B — Defect verification against real code

| # | Reported defect | Verdict | Evidence |
|---|---|---|---|
| 1 | UNION-concat doubling (~L243–247) | **NOT PRESENT** (no such code); hazard premise **CONFIRMED** (see §C) | No concat of both members exists in either repo |
| 2 | `stage_a_parse.json: stage_b_go:true` wrong | **NOT PRESENT** — file does not exist | rg zero hits, both repos |
| 3 | `--authorized` `store_false`+`default=False` always-False | **NOT PRESENT** | Only `--no-resume`/`--no-recompute-corr` use `store_false` |
| 4 | `python scripts/...py` ⇒ `No module named 'src'` | **NOT APPLICABLE** — the packaged command does not exist | No census script under any `scripts/` |
| 5 | Bare `TimeTagger` missing; shim necessary | **CONFIRMED** | `.venv` probe: `import TimeTagger` → `ModuleNotFoundError`; `Swabian.TimeTagger.FileReader` exists; shim `comparison_bench/src/comparison_bench/io/ttbin_compat.py::install_timetagger_alias()` verified working (used for all probes below) |

## C — Member semantics: NESTED / SUPERSET (auto-follow), not disjoint parts

Header-only probes (`getConfiguration` → `dict`, `getChannelList`, `getLastMarker`) on both
members of Jan-12 (`Type2PPLN_3s_2026-01-12_165236`) and Jan-21-2M
(`Type2_2M_3s_2026-01-21_183657`, V80 frozen-channel source):

- Both members of each pair return a **byte-identical full configuration** (Jan-12: 4913-char
  JSON equal), same `current time` = acquisition start = filename timestamp
  (Jan-12 `2026-01-12 16:52:36 +0800`; Jan-21 `2026-01-21 18:36:57 +0800`). No part-index,
  duration, or disjoint-range field exists anywhere in the config. `FileWriter.filename`
  in **both** members points at the base `X.ttbin` name (Windows provenance path
  `D:\SPDC源测试\2026.1.9\...`, provenance only).
- Same channel list both members (signal ch 1, 5; virtual coincidence ch 1001 — consistent
  with the V80 channel plan). `getLastMarker()` empty on all four.
- Vendor docstring (`Swabian/TimeTagger/__init__.py:6549`): *"`FileReader` will automatically
  recognize if the files were split and read them too one by one."* The sibling census
  docstring states the same ("TimeTagger follows its `.1` shard chain automatically").
- **Measured**: opening ONLY the 8 KB Jan-12 `X.ttbin` and draining (`hasData`/`getData`,
  first+last timestamps kept, arrays discarded) yields span **29.9999524 s**; the 21 KB
  Jan-21 `X.ttbin` alone yields **2.9999997 s**. An 8 KB file cannot store a 30 s MHz
  stream — `FileReader(X.ttbin)` transparently followed into `X.1.ttbin`.
- **Consequence**: any code that reads both members and concatenates (UNION) counts every
  event twice. The review's *mechanism* is real even though the *script* is not found:
  disjointness must never be assumed.

## D — 3 s vs 30 s: the Jan-12 acquisition IS 30 s; its `3s` filename tag is wrong

- Metadata implies **no duration** (no duration field in config) — duration came from the
  minimal span read: Jan-12 = 30.0 s, Jan-21-2M = 3.0 s (first timestamps are
  time-since-startup counters, not wall clock; only the difference is meaningful).
- Filesystem cross-check (`docs/DATA_INVENTORY_20260921.md`): base mtime == filename
  timestamp == config `current time` (acquisition start) for every pair; `.1` mtime =
  start + span (+30 s Jan-12, +3 s all others). The mtime gap **is** the acquisition
  duration, and Jan-12's 30 s gap is consistent with its 30.0 s event span.
- Size sanity (inference — assumes ~12–16 B/event, NOT measured): Jan-21-2M
  39.8 MiB / 3 s ≈ 13 MB/s (bright 2M source); Jan-12 16.1 MiB / 30 s ≈ 0.56 MB/s
  (much dimmer operating point, consistent with no rate tag and an earlier protocol).
  A 3 s Jan-12 at that brightness would be ~1.6 MiB, far below the observed 16.1 MiB —
  30 s is self-consistent, 3 s is not.
- **Conclusion**: (i) acquisition duration Jan-12 = **30 s** (measured event span);
  (ii) file-write/mtime gap = 30 s (same thing — file closed at acquisition end);
  (iii) filename tag `3s` = stale/incorrect label for Jan-12 only (all other pairs'
  `3s` tags agree with their 3.0 s spans). The user's skepticism inverts: it is the
  `3s` tag, not the 30 s figure, that is wrong for this pair. Any census MUST NOT trust
  filename duration tags — measure span from the stream.

## E — Minimal fix set (report only; nothing applied)

1. **Concatenation safety**: never open both members. Open `X.ttbin` only (auto-follow
   covers `.1`); assert single-reader span continuity instead. Our P3 Stage 0.5
   file-identity probe already encodes this — keep it as the gate, add the measured-span
   check (span must be > 0 and consistent with `.1` mtime − base mtime within tolerance;
   mismatch ⇒ STOP-BLOCKED). Dedup is the wrong fix (masks the error); dropping one
   member is correct only with the span-continuity assertion proving auto-follow.
2. **argparse**: N/A — no such flag exists. If a future census CLI adds `--authorized`,
   declare `action="store_true", default=False`.
3. **`stage_b_go`**: N/A — no such artifact. P3's gate chain (T5 signed grant, T7
   Pre-RESULT) already plays this role; do not invent a parallel JSON gate.
4. **`PYTHONPATH`**: any future `scripts/` census entrypoint must run from the repo root
   (or set `PYTHONPATH=<root>`) AND call `install_timetagger_alias()` before the frozen
   loader's `from TimeTagger import FileReader`. Respects `src/` frozen (§5.1).
5. **Jan-12 handling**: quarantine its `3s` tag — per-source reporting must carry
   `duration_measured_s=30.0` with `filename_tag_disputed` provenance, never pool it
   with 3 s acquisitions without explicit declaration.

## Bottom line

- **Members: NESTED (auto-follow superset), not disjoint.** Proven by byte-identical
  configs, shared acquisition start, vendor auto-follow documentation, and the measured
  full-span drain through the small file alone.
- **Doubling bug: real as a mechanism, absent as code** — the reported script with
  UNION-concat/`stage_b_go`/`--authorized` exists in NEITHER checkout; but any future
  census that concatenates both members WILL double-count. P3's Stage 0.5 probe is the
  correct (still unimplemented) guard.
- **Acquisition: Jan-12 is 30 s, not 3 s** — event-span measured 29.99995 s, mtime gap
  30 s, size self-consistent; the `3s` filename tag is wrong for this pair only.
- **Before any Stage B**: implement the Stage 0.5 identity + span-continuity gate, open
  only `X.ttbin`, flag Jan-12's duration tag as disputed, and require the signed T5
  authorization — all already specified in the P3 packet, none yet executed.
