# Manual handoff design

The user carries the repository-native paired prompt to OpenCode and carries
the final `COMPLETE`/`BLOCKED` receipt back to the main Codex/ChatGPT thread.
Task packets, cycle documents, and Git remain the durable exchange surface.

The project workflow does not invoke `opencode_session`,
`codex_desktop_bridge`, or an automatic callback loop. Existing global bridge
components remain installed and untouched.
