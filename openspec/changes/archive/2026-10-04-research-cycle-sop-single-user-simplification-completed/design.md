# Design

## Default trust model

This is a manually operated, single-user local research repository. Git records
provenance and supports recovery. It is not an execution capability system.

## Minimal gates

Before an authorized scientific run, check only what can change the result or
destroy evidence:

1. intended repository and branch;
2. scoped code, tests, configuration, and packet have no unreviewed changes;
3. frozen scientific inputs, thresholds, seeds, command, and stop rules match;
4. focused compile/tests pass;
5. target output does not already exist;
6. the user explicitly authorized this bounded run.

Commit IDs MAY be reported afterward for provenance. Remote equality, exact
implementation-SHA equality, stale-SHA searches, checksums, signatures, and
watchdog frameworks are not default gates.

## Escalation

Exact revision locking MAY be added to one packet only when a named concrete
risk exists: concurrent writers, an ambiguous checkout, a destructive data
migration, regulated/release publication, or a prior evidence-identity failure
that the lock would actually prevent.

## Review depth

Low-risk synthetic iterations use focused numerical review. Real-data,
claim-bearing, costly, or irreversible runs retain independent Pre-EXECUTE and
Pre-RESULT review. A failed algorithm outcome is still a completed experiment
when the frozen procedure ran and evidence was retained.

Documentation-only commits and tiny unchanged-scope corrections do not each
need another independent reviewer; batch them into the next milestone review.
Existing active packets inherit this policy. Their SHA/remote-equality clauses
are non-binding unless they name a concrete escalation risk, while their
scientific and no-overwrite constraints remain binding.
