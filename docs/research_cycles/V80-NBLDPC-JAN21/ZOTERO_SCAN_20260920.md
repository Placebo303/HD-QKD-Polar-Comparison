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

## Retry 2026-09-21 (skill: zotero-local-search, read-only)
- Helper: `check_zotero.py` -> `connected:false, status:unavailable`
  (`localhost:23119/api/` + WSL host fallback `10.255.255.254` both refused).
- Verdict: still offline; searches not attempted (no real Zotero search possible).
- Single user-side step: start Zotero desktop on the Windows host with
  Settings → Advanced → "Allow other applications…" enabled, then re-run check.
- Items found: none new (known: Müller ISTC 2023 FN9JZSLS only). S2/S3: unchanged.
