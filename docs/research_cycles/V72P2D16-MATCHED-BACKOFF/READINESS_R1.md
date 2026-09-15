# D16 One-Point Matched-Backoff Discriminator — Readiness R1 (no execution)

- Authority: `.workbuddy/tasks/D16_MATCHED_BACKOFF_DISCRIMINATOR_READINESS_R1_TASK_PACKET.md` (§§1–7, sole authority; §7 return contract). Track: documentation-only (no code, no execution, no D16 batch, no decoder/scientific calls, no root creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- Predecessor: `D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR` — PRESENT (decision-log:4290, D15 EXPLORATION_LOG:192, packet:10).
- Companion log: `EXPLORATION_LOG.md` in this directory (single append-only root for D16).

## Frozen matrix

- n=128; loads L1 `548.700215065776` / L2 `412.508145233200` bits; disclosed L1 625 (m125) / L2 470 (m94); exact factors L1 `1.1390555039696448`, L2 `1.1393714413428093`; absolute gap `0.00031593737316448767` (16dp, design §2 recompute CONFIRMED).
- Cells: L045 71/57/E313 m125 `2^62+3^63`; L055 83/45/E301 m125 `2^74+3^51`; L2 DV3 128×3/E384 m94 `4^86+5^8`. Every histogram sums to (n,m,E) — PASS (design §3).
- Seeds (fresh, frozen, absence-proven design §6): graphs L045 `2026094001..04`, L055 `2026094005..08`, L2 `2026094009..12`; blocks `2026094101..08` shared across all arms. 40xx/41xx hundred-blocks, strictly above all priors (D10–D15); `rg` absence proven at D1601, re-proven at D1609 (below).
- Plan: 3 arms × 4 graphs × 8 blocks = 96 scientific calls; setup 12+8+2 = 22. Order L045→L055→L2-ORACLE, graph/block ascending; batch tag prevents predecessor pooling. No APP/transfer arm; L2 ORACLE diagnostic-only, ungraded except via §7 vocabulary.
- Predicates (D15 reuse, per 32-trial arm): ADEQUATE pool ≥24/32 + ≥2 graphs ≥6/8; WEAK pool ≤16/32 + ≥2 graphs ≤4/8; else MIDDLE. L045 descriptive only; Wilson + paired discordances descriptive only.
- Gates (first-match, design §7): 1 `D16_ENGINEERING_BLOCKED`; 2 `D16_L2_DEGREE_SIGNAL` (L055 ADEQUATE + L2 WEAK); 3 `D16_L1_CONSTRUCTION_SIGNAL` (L055 WEAK + L2 ADEQUATE); 4 `D16_MATCHED_BACKOFF_SUFFICIENT` (both ADEQUATE; main-thread declared packet string authoritative per D1608a); 5 `D16_BOTH_WEAK`; 6 `D16_AMBIGUOUS`. Stored terminals are evidence awaiting main-thread adjudication.
- Budgets (packet §6; code + spec): 96 / 22 / wall ≤900 s / per-call ≤120 s / RSS <2 GiB (2147483648 B) / 1 CPU process; no retry/resume/repair/seed search/tuning/adaptive stop.
- Claim ceiling: synthetic single-layer diagnostic only. No investment choice, no D7-H/FER/leakage/SKR/real-data/qualification/optimality/publication claims.

## D1601–D1609 evidence table (trusted VERIFIED, do not rerun)

| ID | Evidence |
|---|---|
| D1601 | OpenSpec first: proposal/design/tasks/delta spec with exact arithmetic, seeds, reuse map, gates, command/root proposal, claim ceiling. Predecessor PRESENT. |
| D1602 | Arithmetic/admission proof: 16dp factors + socket tables + all 12 A1–A6 feasibility screen — PASS, no STOP, no amend. |
| D1603 | Additive core: thin D15-derived plan, tallies, six-terminal gate; helpers imported, batch tag blocks predecessor pooling. |
| D1604 | Runner: `--profile-only`, `--d16-batch`, default-false `--execution-authorized`, `--verify`; refusal before root/bind/Model-F load; authorized branch one orchestrator + one writer. |
| D1605 | Evidence: fresh never-overwrite six-file root; arm/rows/factor/graph/block/exact/syndrome/undetected/iterations/oracle-graded/wall/resources; L2 ORACLE ungraded. |
| D1606 | Tests: 26/26 PASS (exact math/sockets/seeds/plan, no-APP, predicate edges + terminal collisions, fake authorized 96/96 scratch, existing/partial-root, provenance/nonfinite, refusal, verifier PASS). |
| D1607 | PROFILE_ONLY: 12/12 admitted, exact 96 plan, setup 22, zero decoder, future root absent. |
| D1608 | Independent review: VERIFIED `PASS_WITH_FINDINGS` — arithmetic/admission/seeds/plan/gates/reuse/refusal/budgets/no-production all PASS; 26/26 rerun; D15-4FAIL adjudicated environmental stale-world-state; non-blocking: (a) terminal-string drift, (b) stale boxes, (c) dirty-tree note. No blocker. |
| D1608a | Scoped re-verify PASS: main-thread declared packet string `D16_MATCHED_BACKOFF_SUFFICIENT` authoritative; 9 exact-string edits (module 4 + tests 5 counting T_ symbols; design/spec/proposal lists); zero short-form residue repo-wide; label-only confirmed via gate/writer/verifier reads; 26/26 rerun; nothing else changed. tasks.md:14 shorthand left as historical prose (reported). |
| D1609 | Freeze confirmation (this call, read-only — see below): future root ABSENT; command char-exact vs design §6; budgets 96/22/900s/120s/2GiB/1-proc in code + spec; authorization false. |

## D1609 execution-freeze confirmation (read-only, this call)

- Root absent: `ls workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a` → `No such file or directory`. Root UUID `b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a` frozen (design §6).
- Command verbatim (design §6 char-exact; `FROZEN_COMMAND` template + `MODEL_F_INPUT_ROOT workspace/v72p2d5_model_f_input/20260907_r1`):
  `.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
- Budgets in code (`comparison_bench/src/comparison_bench/formal_ir/v72p2d16_matched_backoff.py`): `SCIENTIFIC_CALL_CEILING=96`, `SETUP_CALL_CEILING=22` (`SETUP_FIXED_UNITS=2` plan+manifest), `WALL_BUDGET_S=900.0`, `PER_CALL_BUDGET_S=120.0`, `RSS_BUDGET_BYTES=r2.RSS_BUDGET_BYTES=2*1024**3=2147483648`, one process; spec §§60–62 matches (≤96 / ≤22 / ≤900s / ≤120s / <2147483648 B / one process).
- Authorization all-false: `--execution-authorized` default-false (`store_true`); `--d16-batch` refuses before root/bind/Model-F load while false; no batch executed (root absent); no authorization granted by readiness or by D16-R1608/R1608A.

## Terminal

`D16_MATCHED_BACKOFF_READY_AWAITING_EXPLICIT_AUTHORIZATION`

Next gate: separate explicit batch grant + Pre-EXECUTE (carried notes: d5-tree reconfirm; R3-first test order). No route/investment/D7-H/FER claims. Decoder/scientific calls in this call: 0. COMMIT_PUSH: none (commit separate).
