> **Amendment 2026-09-21 (main-thread decision — G-X1S GRANTED by conversation grant; this-cycle mode).** The user grants execution of the X1 successor 15-arm EXPLORE_HEAVY batch (verbatim: "授权 G-X1S"), strictly within the frozen contract of `X1_SUCCESSOR_ENTRY_PACKET.md` and this preregistration — no frozen scientific input, gate, threshold, seed, instance, budget ceiling, or stop rule is changed. The §7 signature block remains BLANK by design (no signature is forged); the verbatim chat grant above is the authorization of record and the paperwork deviation is flagged for administrative ratification after the batch-end independent review (P3-A1-REVIEW F-3 precedent; the R1 chat-grant precedent of the same cycle applies). This grant covers ONE bounded batch (15 arms, ≤27000 s total, per-arm ≤1800 s, RSS <4 GiB, 1 CPU). Any change of grid, seeds, instance, bundles, budgets, gates, or arm order requires a NEW grant. Entry evidence recorded before this grant: bundle build + G-D verification (`workspace/x1_bundles_7c1d4a2b/`) and Q0–Q6 Pre-EXECUTE (`X1_SUCCESSOR_ENTRY_PREEXEC.md`).

> **Administrative ratification 2026-09-22 (post-batch-end review, main thread).** The independent batch-end review (`X1_BATCH_END_REVIEW.md`, PASS_WITH_FINDINGS, no blocking findings) verified nil scientific impact of the conversation-grant paperwork deviation (§7 signature block blank; authorization of record = verbatim "授权 G-X1S"): all frozen scientific inputs, gates, thresholds, seeds, instance, budgets, and stop rules unchanged; every per-arm result re-derived from the arm roots. Per the P3-A1-REVIEW F-3 precedent, the main thread ratifies the G-X1S grant as given by conversation grant, for THIS cycle only. This does not establish a standing conversation-grant mode.

# X1 Successor Entry — PREREG_AND_AUTH (2026-09-21) — DRAFT_PENDING_AUTHORIZATION

- Track: **EXPLORE** (synthetic only; **EXPLORE_HEAVY** cost annotation: 15 arms × ≤1800 s = 27000 s ceiling). Status: `GRANTED-BY-CHAT-GRANT-2026-09-21 (see top amendment note; §7 signature block intentionally blank)`. Branch context: `formal-ir-v72p1-addendum-clean` (publication branch `formal-ir-v80-nbldpc-jan21` — not touched). No switch, no commit, no push, no PR.
- Packet (frozen contract): `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md` (Acceptance ID proposed **G-X1S**). Operator prompt: `X1_SUCCESSOR_ENTRY_PROMPT.md`.
- Planning authority: `docs/V80_BASELINE_20260921.md` (§0.1 [X1] retained rows ONLY; §1 I1–I6; §3 corrected basis; §5; §6-2; §7). Every number traces to baseline §0.1/§3 or the R1 artifacts; anything new is `[TO BE MEASURED]` / `[TO BE FROZEN]`; no new constant.
- **Nothing has been executed. No `.ttbin` has been opened. No decoder-kernel change has been made. No bundle has been built. No workspace root has been created. No output has been written.**
- EXPLORE form per `AGENTS.md` §1.2 / §10.3: this file + ONE append-only `EXPLORATION_LOG.md` + machine artifacts + ONE batch-end independent review.

## 1. Hypothesis / questions (single, falsifiable set)

- Q1 (per-source cliff position): where does the soft-marginal FER-vs-m cliff sit on EACH source's own bundle (1M / 1.5M / 2M) under the frozen b2f/v28 procedure (max_iter 300/streak 3, exact_match), 240 paired blocks, seeds `2026095601+idx`, instance 2026092001, standalone per-m constructs? Outcome `[TO BE MEASURED]` per (source, m) — fails/240 + FER only. No numeric outcome is pre-registered.
- Q2 (m_min per source): what is the smallest `m` per source that passes G-A (≤12/240) AND G-B (f_super ≤ 1.3 on own `H_corr` = 0.8012690084416184 / 0.8272902027770036 / 0.8333327179427281)? Outcome `[TO BE MEASURED]`. Bounded expectation only (not a prediction): the cliff position follows each source's own H (m_max 200/207/capped-208); 1M grid top 201 is EXPECTED-OUT on G-B (retained-frozen grid, packet §2.2).
- Q3 (conditional m≤201 decodability): do the measured curves sustain decoding at m≤201 per source? Interpretation is PRE-REGISTERED as CONDITIONAL: an affirmative reading relocates the operating point ONLY under the per-block disclosure model (baseline §2(a)); under the ratified sacrifice/amortized default it does NOT relocate the operating point.
- Control expectations (machinery checks, not science predictions): bundle build reproduces R1 checksums (N_train 315504/441487/589461; K_AB 2395/2439/2597; K_B 1024 ×3); `bind_empirical_bundle()` gates pass on the built files; dry-construct pins (fc=0/rank-full/twice-identical) verify per m; cross-source-label binding refuses.

## 2. Exact command templates (placeholders — filled at Pre-EXECUTE, never invented)

Bundle build (seconds of numpy, zero `.ttbin`, zero code change to frozen modules):

```
PYTHONPATH=<repo-root> .venv/bin/python <BUNDLE_BUILD_ENTRYPOINT [TO BE FROZEN: thin additive script path]> \
  --r1-root workspace/r1_histogram_5e2a91c4 \
  --sources T2-1M;T2-1.5M;T2-2M \
  --fact-id F03 \
  --out-root workspace/x1_bundles_<UUID8 [TO BE FROZEN]> \
  --key-prefixes <1M;1p5M;2M [TO BE FROZEN: proposal packet §2.6; 1.5M display-only, never a key]>
```

Per-arm run (ONE arm per invocation; order frozen in the prompt §5; thin runner path `[TO BE FROZEN]` — filling it changes NO science input):

```
PYTHONPATH=<repo-root> .venv/bin/python <ARM_RUNNER_ENTRYPOINT [TO BE FROZEN]> \
  --arm X1-<SOURCE>-<M [TO BE FROZEN per arm: grid packet §2.2]> \
  --bundle workspace/x1_bundles_<UUID8>/x1_gamma_f03r1.npz \
  --pb-sidecar workspace/x1_bundles_<UUID8>/x1_gamma_f03r1_pb.npz \
  --source-key <1M|1p5M|2M [TO BE FROZEN]> \
  --construct-instance 2026092001 --standalone \
  --seeds 2026095601+idx --stream o1_blk:{seed} --blocks 240 \
  --root workspace/x1_<UUID8_PER_ARM [TO BE FROZEN]> \
  --per-decode-timeout-s 300 --budget-s 1800
```

- `<UUID8>` values, exact bundle paths, key-prefix freeze, thin-runner path, and arm order confirmation are `[TO BE FROZEN]` at Pre-EXECUTE. This file deliberately invents none of them. Frozen literals that MUST appear verbatim at Pre-EXECUTE: seeds `2026095601+idx`, stream `o1_blk:{seed}`, instance `2026092001`, b2f verbatim, v28 300/3 exact_match, grid integers (1M {185,189,193,197,201} / 1.5M {191,195,199,203,207} / 2M {192,196,200,204,208}), slope 4.785675, H_corr triple (§1), key-eligible counts 200/276/364 (certifiability reference only).
- 2M decode arms bind the FROZEN `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz` read-only (NEVER the re-derived-2M verification file). 1M/1.5M arms bind the §2.6-built bundles read-only.

## 3. Budget table (frozen single ceiling — bootstrap-free; no alternative row)

| item | ceiling |
|---|---|
| per-arm (bundle-bind + 240 decodes + persistence) | ≤ 1800 s |
| 15-arm total | ≤ 27000 s |
| bundle build + verification (all sources) | negligible (seconds of numpy; counted INSIDE the ceiling, no separate budget) |
| per-decode terminal | ≤ 300 s |
| per `.ttbin` read | 0 reads authorized (any read STOP-BLOCKED) |
| peak RSS | < 4 GiB |
| CPUs | 1 |
| decoder-kernel / DE / graph-construction calls beyond the frozen b2f/v28 arm procedure | 0 new (arms call ONLY the frozen procedure) |

Wall-partial ⇒ `INCOMPLETE`, retained, never continued. Bar-12 early-stop arms are CENSORED (packet §2.7), never extrapolated. ≤1 preregistered engineering repair+rerun for infrastructure failure ONLY, scientific inputs/seeds/thresholds/data roles/hypothesis unchanged, failed attempt retained in the same root(s) + log.

## 4. Output-absence checks (recorded at Pre-EXECUTE, before any execution)

- [ ] `workspace/x1_bundles_*` does not exist (`ls workspace | rg '^x1_bundles_'` returns nothing).
- [ ] `workspace/x1_*` decode roots for the frozen UUID pattern do not exist (`ls workspace | rg '^x1_'` returns nothing beyond pre-existing unrelated entries, each enumerated).
- [ ] `rg -n 'x1_bundles_|X1_SUCCESSOR' --glob '!docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_*'` returns only this packet family.
- [ ] `results/` and `comparison_bench/outputs_comparison/` are byte-identical to their pre-execution state (no new files, no overwrites; snapshot recorded).
- [ ] Existing evidence roots (`workspace/p3_census_3954637c/`, `workspace/p3_stage05_ee32030a/`, `workspace/r1_histogram_5e2a91c4/`) untouched; R1 root opened read-only (no write path in the bundle builder); `git diff -- src/` empty.
- [ ] Intended branch confirmed: `formal-ir-v72p1-addendum-clean`; no switch; no commit; no push; no PR.
- [ ] Scoped code/config/test/packet cleanliness confirmed (only the additive bundle builder + verification reporter + thin runner, if any, + their fake-only tests).
- [ ] Focused tests pass: fake-only bundle round-trip / bind-gate refusals (incl. cross-source-label) / construct-pin / bar-gate-arithmetic / root-refusal tests (packet §7 T-X1S-3).
- [ ] G-D bundle verification (packet §2.6 items 1–3) recorded PASS before any arm launches; target output roots absence re-proved with the final UUIDs immediately before launch.

## 5. Scope / non-goals (explicitly forbidden)

- No real data (any `.ttbin` read STOP-BLOCKED); no decoder/DE/graph-kernel change; no prior refit; no V25 `channel_counts.npz` vintage substitution; no P1/P2 execution; no operating-point selection.
- No change to any frozen scientific input (grid, seeds, instance, H_corr basis, gates, thresholds, slope, trio parameters, bundle-key semantics).
- No pooling across sources/m/instances; no `undetected`-merging; no `f_super`-as-`f_eff`; no cross-m monotonicity inference; no 2M-only generality headline.
- **No FER / SKR / route / qualification / publication claim.** Curves do not select an operating point.

## 6. Decision criteria (frozen, binary per gate — mirror packet §4)

- **G-A (route):** fails/240 ≤ 12 per arm, else FAIL (+CENSORED if bar-12 early-stop).
- **G-B (efficiency):** f_super ≤ 1.3 on the arm's OWN `H_corr` (§1 triple), else FAIL (1M m=201 EXPECTED-FAIL).
- **G-C (N-rule + presentation ban):** N-rule evaluated per arm (expected FAIL at high m); presenting any single-source f_eff as certifiable/literature-comparable ⇒ gate FAIL (presentation violation, batch-end adjudication).
- **G-D (bundle entry):** bind shape/normalization gates + R1 checksum identities PASS per source before its arms; 2M report-only comparison materiality (|ΔH|>0.01/plane OR p_b L_inf>1e-3) ⇒ FINDING escalated, never refit. FAIL ⇒ STOP-BLOCKED for that source.
- **G-E (integrity/stop):** budgets held; zero `.ttbin`; cross-source reuse refused; no pooling/merging/misquoting/inference; `src/` clean; protected roots untouched. FAIL ⇒ STOP-BLOCKED.
- Each arm reported as monotone / non-monotone / censored (no inference). Batch closes only with batch-end independent review + main-thread acceptance. Any gate FAIL blocks promotion of that arm's evidence; never publish-then-patch.

## 7. SIGNATURE BLOCK — the user must fill this to grant execution (OR record a verbatim conversation grant below)

Authorization-mode justification (why BOTH boxes exist): the R1 cycle's conversation-grant mode was ratified as a THIS-cycle-only exception (R1 acceptance: "NOT authorized … a standing conversation-grant mode — that would be an AGENTS.md/OpenSpec workflow change"). This successor therefore DEFAULTS to the written-signature box. The conversation-grant box is provided ONLY so that, if the user explicitly chooses this cycle's demonstrated mode again, the verbatim grant is captured as the authorization of record with nil-impact verification at batch-end review — it is NOT pre-authorized here, and the signature boxes remain BLANK until the user fills one.

```
I AUTHORIZE the X1 successor EXPLORE batch under Acceptance ID G-X1S,
strictly within the frozen contract of X1_SUCCESSOR_ENTRY_PACKET.md and
this preregistration (15-arm conditional sequence + §2.6 bundle build,
packet §§1–8; prompt run procedure).

  Bundle root (fresh, absent):              workspace/x1_bundles_<UUID8 [TO BE FROZEN]>
  Per-arm roots (fresh, absent pattern):    workspace/x1_<UUID8 [TO BE FROZEN: pattern per prompt §5]>
  Bundle inputs (read-only):                workspace/r1_histogram_5e2a91c4/ (T2-*-sparse-npz + p_b-npy + JSON)
  2M decode bundle (read-only, NEVER refit): docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz + gamma_f03_pb.npz
  1M/1.5M decode bundles (read-only):       workspace/x1_bundles_<UUID8>/x1_gamma_f03r1.npz + x1_gamma_f03r1_pb.npz
  Bundle key prefixes frozen as:            <[TO BE FROZEN: proposal 1M;1p5M;2M]>
  Grid / seeds / instance confirmed:        <[TO BE FROZEN: verbatim grid + 2026095601+idx / o1_blk:{seed} / 2026092001]>
  Budget confirmed (single ceiling):        ≤1800 s/arm, ≤27000 s total, per-decode ≤300 s, RSS <4 GiB, 1 CPU
  Thin-runner entrypoint (additive only):   <[TO BE FROZEN: path or "none — existing path used"]>
  Branch / commit context confirmed:        formal-ir-v72p1-addendum-clean

  Authorized by (name/handle):              ______________________________
  Date (UTC):                               ______________________________
  Signature:                                ______________________________

NOTES
- This signature is the ONLY written authorization. The frozen packet and this
  preregistration authorize NOTHING by themselves.
- Pre-EXECUTE Q0–Q6 (packet §8 + §4 above) must be recorded and PASS, and G-D
  bundle verification must PASS, before any arm execution.
- The grant covers ONE bounded batch (bundle build + frozen 15-arm conditional
  sequence). Any change of bundle inputs, roots, grid, seeds, instance, gates,
  thresholds, slope, H basis, or key prefixes requires a NEW signature.
- After execution: ONE append-only EXPLORATION_LOG.md, then batch-end
  independent review, then main-thread acceptance. No PR, no push, no commit
  without a separate explicit authorization.
```

*(This block is BLANK by design — the planner does not sign. The user fills it.)*

Conversation-grant capture box (ALTERNATIVE to the signature above — complete AT MOST one; leave blank unless the user explicitly grants in conversation):

```
Verbatim user grant (paste exact message, no paraphrase):

  <[TO BE FROZEN: verbatim chat grant quoted here at Pre-EXECUTE, or "not used — written signature above governs"]>

Recorded by: ______________________________   Date (UTC): ______________
Scope asserted (must match the §7 written scope line-for-line): YES / NO (circle; NO ⇒ STOP-BLOCKED)
Nil-impact verification at batch-end review (frozen inputs/gates/thresholds/seeds/budgets/stops unchanged): PENDING → recorded in the batch-end review
```

## 8. EXPLORATION_LOG.md requirements (append-only; ONE log for the batch)

- Location: the batch log lives at the batch root pattern `[TO BE FROZEN at Pre-EXECUTE: e.g. first per-arm root or bundle root sibling — exactly ONE path, frozen before launch]`; per-arm machine notes append to the SAME file (no per-arm log files).
- MUST record, in order: (i) frozen contract IDs (packet/prereg/prompt paths + G-X1S); (ii) Pre-EXECUTE Q0–Q6 verdicts + G-D verification verdicts; (iii) authorization-of-record (signed block OR verbatim grant); (iv) per-arm attempts (arm ID, root, bundle path+key prefix, seeds, construct pins, wall/RSS, fails/240, FER, f_super/f_eff own-basis, undetected count, monotone/non-monotone/censored label, gate verdicts G-A…G-E); (v) the ≤1 preregistered engineering correction IF used (what failed with exact error, unchanged-inputs attestation, failed attempt retained where, rerun verdict) — else the explicit line "no repair path used"; (vi) retained failures (INCOMPLETE/CENSORED/BLOCKED arms kept, never overwritten, never continued); (vii) batch-end review verdict + main-thread acceptance pointer.
- NEVER record: any `.ttbin` path content beyond the STOP-BLOCKED assertion; any pooled cross-source/m/instance number; any operating-point selection; any FER/SKR/route/qualification/publication claim.

## 9. Batch-end review plan (ONE independent review — no per-arm review)

- Reviewer: independent thread (read-only except the review file); gate per `AGENTS.md` §10.3 EXPLORE batch-end review.
- Scope: authorization boundary (frozen sequence respected; no arm outside the grid); machine gates (G-A…G-E re-derived from `rows.json`/`block_accounting.csv` + bundle checksums, not trusted from summaries); retained failures + repair-path compliance (inputs unchanged attestation); final-evidence completeness (15 attempted or INCOMPLETE-with-cause; no silent skips); claim-ceiling compliance (curves only; 1M-led generality framing; no operating-point selection; f-margin vs N-count distinctness); nil-impact verification of the authorization mode (if conversation-grant box used).
- Verdicts: PASS / PASS_WITH_FINDINGS (non-blocking findings listed; promotion allowed on main-thread acceptance) / FAIL (blocks promotion of the batch evidence; triggers escalation review, NOT another unreviewed arm).
- FAIL blocks promotion; never publish-then-patch.
