## Historical implemented scope — add-nbldpc-l1-degree2-layout

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-add-nbldpc-l1-degree2-layout-completed/specs/degree2-layout/spec.md -->

## SHALL (frozen Stage-1 contract)

- The change SHALL add exactly the files in `proposal.md` §Impact scope and
  SHALL modify no existing `formal_ir/*` module, frozen baseline, old packet,
  `AGENTS.md`, memory, decision-log, or sibling checkout.
- L055 cells SHALL be exactly n128 n2=83/n3=45/E=301/checks 2^53+3^65/m=118
  and n256 n2=166/n3=90/E=602/checks 2^106+3^130/m=236.
- Control and candidate SHALL share the identical Phase-A backbone at equal
  seeds; the candidate SHALL place degree-3 sockets first (index order) and
  degree-2 sockets last (seeded-permutation order) with the frozen priority
  unreachable-first → BFS-depth-desc → d2-cycle-asc(four, then six) →
  ACE-desc → seeded tie-break. The rule SHALL be fixed before any graph is
  generated and SHALL NOT be re-chosen after seeing metrics.
- Admission SHALL be A1–A6 only (`r2.structural_record` + edge/coefficient
  replay equality); four-cycle/girth/ACE SHALL stay diagnostics.
- Coefficients SHALL be `d10:coeff:{width}:{graph_seed}`, one `integers(1,32)`
  per edge in sorted `(v,c)` order, via `r2` import; matrix conversion SHALL
  reuse `r2.dense_from_edges` (no copies).
- The driver SHALL run control vs candidate on one fixed H2 with one shared
  frame/prior/binding, `oracle=False` hardcoded on both arms, no oracle CLI
  switch, and SHALL NOT call the D11 outer MIX runner. `decode_fn` SHALL be
  explicitly injected; absent/non-callable SHALL refuse before binding.
- The output schema SHALL reserve exactly `RESULT_SCHEMA_COLUMNS` in frozen
  order with `status` ∈ {`ok`,`nonconverged`,`resource_abort`};
  `accepted_wrong` SHALL be isolated and SHALL never merge into success;
  failed/aborted frames SHALL keep full disclosure accounting.
- Tests SHALL be fake-only (T0/T1, S-T01–S-T08); S-T04 failures SHALL stop
  with no seed change; no test SHALL write the production roots or contact
  real inputs or the production decoder.

<!-- Source: openspec/changes/archive/2026-10-04-add-nbldpc-l1-degree2-layout-completed/specs/degree2-layout/spec.md -->

## SHALL NOT

- No `--batch` / `--execute*` / `--forward-batch` / benchmark / sweep /
  replay surface in Stage-1 code or tests.
- No `results/` or `comparison_bench/outputs_comparison/` writes.
- No `.ttbin`/real-input reads; no production-decoder default binding.
