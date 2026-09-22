# P3 Stage 0.5 Probe — PREREG_AND_AUTH (2026-09-21) — DRAFT_PENDING_AUTHORIZATION

- Track: **DECIDE** (raw acquisition `.ttbin` data; minimum viable contact). Status: `DRAFT_PENDING_AUTHORIZATION`. Branch context: `formal-ir-v72p1-addendum-clean` (publication branch `formal-ir-v80-nbldpc-jan21` untouched). No switch, no commit, no push, no PR.
- Packet (frozen contract, authoritative): `docs/research_cycles/V80-NBLDPC-JAN21/P3_STAGE05_PACKET.md` (Acceptance ID **G-P3-STAGE05**). Operator prompt: `P3_STAGE05_PROMPT.md`.
- **Nothing has been executed. No `.ttbin` has been opened. No workspace root has been created. No output has been written.**
- Compact DECIDE form permitted by `AGENTS.md` §10.3 / `docs/research-cycle-sop.md` §4: this file + result record + independent acceptance + machine artifacts. This stage is signable INDEPENDENTLY of the full P3 census (cheap, unblocks everything else); signing it authorizes ONLY the §2 reads, never Stage 1.
- Why DECIDE in one line: it touches real/raw acquisition streams, so per `AGENTS.md` §1.2 it cannot be EXPLORE — but scope is frozen to config accessors + first/last-timestamp span (no histograms/coincidences/pairs/entropy), bounding the contact to the minimum that unblocks the census.

## 1. Hypothesis / question (single set)

- H1: `FileReader("X.ttbin")` alone yields the full stream per dataset (G1–G3 pass), with `duration_measured_s` recorded against the filename tag.
- H2: `getConfiguration()` verbatim payload survey — which keys exist for acquisition start, channel roles/gates/markers, PM/EB + phase-matching (Type0/Type2/SHG), and split/part structure; `pm_eb_evidence` states exactly what is and is NOT established.
- **No numeric outcome is pre-registered** (prior measured spans Jan-12 29.9999524 s / Jan-21-2M 2.9999997 s are quoted evidence from `docs/TTBIN_MEMBER_SEMANTICS_20260921.md`, not predictions of this run).

## 2. Exact command (placeholder — filled at Pre-EXECUTE)

```
PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison \
  .venv/bin/python -m comparison_bench.src.comparison_bench.cli.<STAGE05_ENTRYPOINT> \
  --packet docs/research_cycles/V80-NBLDPC-JAN21/P3_STAGE05_PACKET.md \
  --bases <SEMICOLON_SEPARATED_BASE_TTBIN_PATHS> \
  --root workspace/p3_stage05_<UUID8> \
  --per-read-timeout-s 300 --max-reads-per-dataset 2
```

- `<STAGE05_ENTRYPOINT>` is a NEW thin module (read-only over `src/qkd_io/ttbin_pipeline.py` and all frozen modules); it MUST call `install_timetagger_alias()` before any TimeTagger import. `[TO BE FROZEN]` at Pre-EXECUTE — invented nowhere here.
- `<SEMICOLON_SEPARATED_BASE_TTBIN_PATHS>` is exactly the 10 base paths in packet §2, in packet order. `<UUID8>` is frozen at authorization with output-absence re-proved.

## 3. Budget table (frozen ceilings)

| item | ceiling |
|---|---|
| Per read (`FileReader` open + config + channel/marker + bounded span drain) | ≤ 300 s |
| Reads per dataset (one base member; one `.1` shard-only ONLY in the fallback case) | ≤ 2 |
| Total wall (10 datasets) | ≤ 1800 s |
| Peak RSS | < 4 GiB |
| Decoder / DE / graph / `tools/*` calls | **0** |
| Forbidden computations (histograms, coincidences, pairs, `counts_ab`, entropy, weights, drift, ACF, splits) | **0** |
| Event arrays written to disk | **0** (first/last scalars only) |

Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 preregistered engineering repair+rerun for infrastructure failure only, scientific inputs unchanged, failed attempt retained in the same log.

## 4. Output-absence checks (recorded at Pre-EXECUTE, before any execution)

- [ ] `workspace/p3_stage05_*` does not exist (`ls workspace | rg '^p3_stage05_'` returns nothing).
- [ ] `rg -n 'p3_stage05_' --glob '!docs/research_cycles/V80-NBLDPC-JAN21/P3_STAGE05_*'` returns only this packet family.
- [ ] `results/` and `comparison_bench/outputs_comparison/` byte-identical to pre-execution state (no new files, no overwrites).
- [ ] No existing evidence root under `docs/research_cycles/` modified; only `P3_STAGE05_*.md` are new.
- [ ] Intended branch confirmed: `formal-ir-v72p1-addendum-clean`; no switch; no commit; no push; no PR.
- [ ] Alias smoke (no data): `install_timetagger_alias()` then `from TimeTagger import FileReader` resolves in `.venv`; `import qkd_io.ttbin_pipeline` clean. FAIL ⇒ **STOP-BLOCKED**.
- [ ] Scoped cleanliness confirmed (no unreviewed staged/unstaged changes outside the new thin module).
- [ ] Target output root absence re-proved with the final UUID immediately before launch.

## 5. Scope / non-goals (explicitly forbidden)

- No histograms, cross-correlations, coincidences, pairing, pairs, `counts_ab`/`N_ab`, entropy (`H_full`/`H_L1`/`H_L2`/MM/gap/CI), weights, drift, autocorrelation, or splits.
- No opening of `.1` except single-member shard-only fallback; NEVER both members; NEVER concatenation.
- No event/timestamp/channel arrays to disk; no excluded-derived-artifact reads; no writes to `results/` or `comparison_bench/outputs_comparison/`; no modification under `src/`.
- No decoder/DE/graph/`tools/*`/`run_e2e_pipeline.py` calls. No Stage 1 census read — this grant covers §2 reads only.
- **No FER / SKR / operating-point / route / qualification / publication claim.**

## 6. Decision criteria (frozen, binary)

- **G1 both-or-neither**: both members needed to succeed ⇒ STOP-BLOCKED for that dataset. PASS = base-only open succeeds.
- **G2 span > 0**: FAIL ⇒ STOP-BLOCKED.
- **G3 span-vs-gap**: |span − (mtime(`.1`) − mtime(base))| within the frozen tolerance (proposed 0.5 s, `[TO BE CONFIRMED]`). FAIL ⇒ STOP-BLOCKED.
- **G4 config parses**: verbatim dump + type recorded; unparseable ⇒ config columns BLOCKED (span row stands).
- Batch PASS (gates Stage 1 eligibility, authorizes nothing by itself): all 10 clear G1–G3. Any FAIL ⇒ escalate, no Stage 1.

## 7. SIGNATURE BLOCK — the user must fill this to grant execution

```
I AUTHORIZE execution of the P3 Stage 0.5 probe under Acceptance ID G-P3-STAGE05,
strictly within the frozen contract of P3_STAGE05_PACKET.md and this preregistration.
This grant covers ONLY the §2 base-member reads + config/span survey. It does NOT
authorize any Stage 1 census read, pairing, entropy, or alignment fit.

  Base list authorized (10 paths, packet §2 order):  ______________________________
  Thin entrypoint module:                            ______________________________
  Output root UUID (p3_stage05_<UUID8>):              ______________________________
  G3 span-vs-gap tolerance (s):                      ______________________________
  Total wall ceiling authorized (s, ≤1800):           ______________________________
  Branch / commit context confirmed:                 formal-ir-v72p1-addendum-clean

  Authorized by (name/handle):                       ______________________________
  Date (UTC):                                        ______________________________
  Signature:                                         ______________________________

NOTES
- This signature is the ONLY authorization. The frozen packet and this
  preregistration authorize NOTHING by themselves.
- Pre-EXECUTE Q0–Q5 (packet §9) must be recorded and PASS before any execution.
- The grant covers ONE bounded probe. Any change of base list, module, UUID,
  tolerance, or budget requires a NEW signature.
- After execution: one result record (10× JSON + duration_table.md +
  config_notes.md), then independent batch-end review, then main-thread
  acceptance. No PR, no push, no commit without a separate explicit authorization.
```
