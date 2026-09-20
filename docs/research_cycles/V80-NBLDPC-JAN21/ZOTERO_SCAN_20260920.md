# Zotero Scan 2026-09-20 (EXPLORE read-only)

Probe: Zotero desktop NOT reachable from this session.
- `GET http://127.0.0.1:23119/connector/ping` -> curl RC=7 Connection refused
- `GET http://127.0.0.1:23119/api/users/0/items?limit=3` -> RC=7 refused
- `GET http://localhost:23119/...` (both paths) -> RC=7 refused (::1+127.0.0.1)

Queries run: none (Z2 skipped; API pre-condition failed, 0/10 calls used).
Collections list: not fetched (same reason).

Relevant items found: none new. Known item only: Müller ISTC 2023 (FN9JZSLS).
Relevance to V80: no new S2 (PEG/NB-LDPC) or S3 (rate-adaptive) refs added.

Retry: open Zotero desktop on Windows host with local HTTP API allowed,
then re-run the Z1 ping from this environment.
No writes to Zotero made; only non-auth GET probes. Branch untouched.
