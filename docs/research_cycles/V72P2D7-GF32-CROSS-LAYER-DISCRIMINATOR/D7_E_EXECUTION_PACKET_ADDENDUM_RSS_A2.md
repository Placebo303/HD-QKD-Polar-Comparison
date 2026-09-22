# D7-E execution packet addendum RSS A2 (telemetry source correction only)

- Authority: `.workbuddy/tasks/D7_E_RSS_TELEMETRY_REWORK_VENV_A2_TASK_PACKET.md`
  §§0–1, 3–5 (T0–T1 freeze). Entry HEAD `d6e40dd`.
- Status: this addendum supersedes ONLY the RSS source semantics in
  `D7_E_PREREG_R1.md` / `D7_E_EXECUTION_PACKET_R1.md` (and their A1
  carryover): wherever R1/A1 names WSL stdlib `resource` `ru_maxrss` as the
  RSS source, read `VmHWM` from `/proc/self/status` instead, per the §1 A2
  rule below. The A1 interpreter spelling (`.venv/bin/python` and the exact
  frozen command) stays as frozen in
  `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`.
- The R1 scientific contract — matrix (R08), formulas and estimator
  identity (R09), eligibility (R10), labels (R11), terminal priority
  (R12), budgets' numeric values including the strict `< 2 GiB` limit,
  root contract, seven-file schema with the `rss_bytes` key, and
  authorization lifecycle — is untouched. This addendum grants no
  execution authorization and runs nothing.

## Frozen A2 RSS rule (telemetry only)

1. On Linux/WSL, current-process peak RSS is read from
   `/proc/self/status`, field `VmHWM`, whose unit must be exactly `kB`;
   convert with `bytes = value * 1024`.
2. `VmHWM` is authoritative for this WSL execution path. Do not compare
   against or fall back to `ru_maxrss` when `/proc/self/status` is present.
3. Missing file, missing field, duplicate field, malformed/non-integer/
   non-positive value, wrong unit, read error, or overflow returns `None`
   and blocks before scientific execution or at the first affected call
   under the existing resource terminal.
4. Do not silently substitute `VmRSS`, `/proc/<pid>/statm`, psutil, shell
   commands, or another process.
5. The limit remains strict `< 2 GiB`; equality or greater is blocked.
   Units and threshold do not change.
6. The stored scalar key remains `rss_bytes`; no new scientific output
   field or schema revision is required.
7. `resource.ru_maxrss` may remain only for non-Linux legacy code if
   already necessary, but the frozen WSL path must not call it. Prefer
   deleting an unused fallback over adding a general telemetry framework.
8. A single fresh E09 probe after implementation is evidence. Repeating
   probes until one passes is forbidden.

Parser acceptance: exactly one ASCII `VmHWM: <positive integer> kB` line;
reject missing/duplicate/malformed/decimal/signed/zero/negative/
wrong-unit/non-ASCII; overflow rule — reject digit strings longer than 18
digits (≥10^18 kB is physically impossible; prevents pathological int
parsing). Production read opens `/proc/self/status` once per probe call:
no subprocess/shell/psutil/caching/retries/averaging/polling/env-switch/
provider abstraction.

## Review staleness

The renewed Pre-EXECUTE review becomes stale until A2 implementation
review (`D7_E_RSS_TELEMETRY_REWORK_REVIEW_A2.md`) plus a fresh single E09
pass. Nothing in this addendum reuses any previous authorization; a later
execution requires a fresh explicit authorization referencing RSS A2.

## Supersession scope (exhaustive)

- Superseded: the `ru_maxrss`-as-source semantics for the WSL execution
  path in R1/A1.
- Not superseded: everything else in R1/A1 (question, identities, seeds,
  rows, mothers, Model-F root, decoder contract, slot order, transfer
  formulas, estimator identity, eligibility, labels, terminals, numeric
  budgets, schema, verifier contract, reviews, authorization lifecycle,
  interpreter spelling, exact frozen command).
