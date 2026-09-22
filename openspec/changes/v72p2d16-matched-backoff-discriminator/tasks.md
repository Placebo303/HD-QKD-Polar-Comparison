# Tasks — D16 One-Point Matched-Backoff Discriminator (readiness D1601–D1609)

Packet: `.workbuddy/tasks/D16_MATCHED_BACKOFF_DISCRIMINATOR_READINESS_R1_TASK_PACKET.md`
Track: `EXPLORE` readiness planning for D1601–D1602 (docs only; no code, no
execution, decoder calls 0, no commit/push); future batch remains `EXPLORE`.
Scope for this call: `openspec/changes/v72p2d16-matched-backoff-discriminator/**`
for D1601; hand-arithmetic for D1602. Code/scripts/tests/cycle-docs per packet
§§3–6 for D1603–D1609 (later calls only).

- [x] **D1601 OpenSpec first**: proposal/design/tasks/delta spec with exact arithmetic,
  seeds, reuse map (D15 construction/admission/coeff/sampling/prior/dispatch/oracle/
  evidence/verifier + R2/D12/D5 donors; NO APP/transfer; no copied decoder/GF32),
  rejected alternatives, three-cell matrix, §7 six terminals with first-match priority
  (ENG → L2_DEGREE_SIGNAL → L1_CONSTRUCTION_SIGNAL → MATCHED_SUFFICIENT → BOTH_WEAK
  → AMBIGUOUS), L045-descriptive + Wilson/descriptive-only rules, budgets
  (96/22/900s/120s/2GiB/1-proc), claim ceiling (no investment choice, no
  D7-H/FER claims). Seeds/root/command frozen with absence proof (design §6).
- [x] **D1602 arithmetic/admission proof**: exact-rational recomputation of factors
  (L1 625/548.700215065776=1.1390555039696448; L2 470/412.508145233200=
  1.1393714413428093; gap 0.00031593737316448767), sockets and all three check
  allocations (L045 m125 `2^62+3^63` from 313−250=63; L055 m125 `2^74+3^51` from
  301−250=51; L2 m94 `4^86+5^8` from 384−376=8); every histogram sums to n/m/E
  (§3 table all PASS); constructor-feasibility screen (§4: min-dc-4 admitted per
  D15 precedent, max-dc-5 within D9 ≤8 ceiling, no gate requires degree-2 checks
  or n2>0; novel m125/m94 impose no gate constraint) — PASS, no STOP, no amend.
- [x] **D1603 additive core**: thin D15-derived plan, tallies and six-terminal gate;
  import helpers rather than copying them; batch tag prevents predecessor pooling.
- [x] **D1604 runner**: `--profile-only`, `--d16-batch`, default-false
  `--execution-authorized`, `--verify`; refusal before root/bind/Model-F load;
  authorized branch exactly one orchestrator plus one writer.
- [x] **D1605 evidence**: fresh never-overwrite six-file root; records include arm,
  rows/factor, graph/block, exact/syndrome/undetected, iterations, oracle/graded,
  wall/resources. L2 must be ORACLE and ungraded.
- [x] **D1606 tests**: exact math/sockets/seeds/plan; no-APP; all predicate edges and
  terminal collisions; fake authorized 96/96 scratch run; existing/partial-root,
  provenance/nonfinite and refusal tests; verifier PASS.
- [x] **D1607 PROFILE_ONLY**: 12/12 admitted, exact 96 plan, setup 22, zero decoder,
  future root absent.
- [x] **D1608 independent review**: actual access; separately recompute arithmetic,
  admissions, identities, fake true branch, gates, budgets, no-APP/no-production.
- [x] **D1609 freeze execution**: exact fresh UUID root, command and budgets; leave
  unauthorized and absent. Freeze-confirmation step: re-prove seed/root absence
  (`rg` per design §6), confirm exact command string character-for-character
  against design §6, confirm budgets 96/22/900s/120s/2GiB/1-proc, and confirm
  target root still absent — STOP on any collision before authorization.

Verification proportionality (packet §7): T0 compile + exact arithmetic fixtures;
T1 focused D16 plus directly affected D15 tests only. Broad suites only on concrete
conflict. Fake authorized true branch must complete 96/96 into a scratch root and
pass the verifier without entering production adapters. Reviewer evidence must state
`EVIDENCE_ACCESS: VERIFIED`; any blocking arithmetic, admission, pairing, gate or
production-boundary finding blocks readiness. After PASS, one explicit-path local
commit is permitted (NOT this call: no commit/push).
