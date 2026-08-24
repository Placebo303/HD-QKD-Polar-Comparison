# Design: Copy-paste research-cycle protocol

GitHub is the durable exchange surface. OpenSpec remains the requirements
source of truth; ChatGPT returns an advisory review that becomes durable only
after it is copied into the repository; OpenCode implements a frozen task
packet and cannot accept its own work.

The minimal lifecycle is:

`PLAN_CANDIDATE -> PLAN_ACCEPTED -> IMPLEMENTATION_CANDIDATE ->
DEVELOPMENT_RESULT_REVIEW -> ACCEPTED | REVISE | CLOSED`.

Formal or expensive execution adds an explicit user `EXECUTE_AUTH` after
implementation acceptance. Each Git milestone includes machine-readable data
when reasonably small; otherwise it includes a result summary, provenance,
reproduction command, and an explicit list of omitted artifacts.

