# Design Decision Log

This file records choices that should remain stable unless a documented issue and benchmark justify a change.

## ADR-001 — In-process BM25 by default

**Status:** accepted. BM25 is deterministic, dependency-free, portable and fast for hundreds of skills. It is not semantic understanding. Improve recall using metadata aliases/intents before making a neural model mandatory.

## ADR-002 — Sidecar metadata, never SKILL.md edits

**Status:** accepted. Other developers own their skill files; upstream updates must remain unaffected. Sidecar versions are tied to source hashes, approvals and provenance.

## ADR-003 — Auxiliary inference only on explicit audit

**Status:** accepted with a transport clarification. Normal conversations require zero inference overhead. The auxiliary task is registered, but actual audit model requests use an operator-specified numeric loopback HTTP endpoint, with redirects and client proxies disabled. A loopback server could itself forward prompts remotely; operators must verify the server's offline configuration.

## ADR-004 — Abstention over ungrounded selection

**Status:** accepted. A false hint can waste context and tools; empty hints preserve native Hermes discovery. High BM25 scores do not imply calibrated confidence.

## ADR-005 — Native plugin SDK only

**Status:** accepted, with a known beta compatibility gap. No monkey-patching of `AIAgent` or native skill tools. Maintenance currently uses Hermes' internal `tools.skills_tool.skills_list()` to capture a fail-closed native catalogue snapshot; normal-turn routing has no host-internal imports. A documented session-aware eligibility API is still needed for stable compatibility (issue #7).

## ADR-006 — Docs and scaffold before production claims

**Status:** accepted; initial scaffold gate satisfied. Functional opt-in routing, metadata review and isolated Hermes installation have since passed CI. Continue to advertise SkillSense as an **experimental beta**, not a stable release, until session-aware availability and held-out quality gates pass.

Change process: open an issue, present alternatives and measurements, update this log and related tests in the same PR.