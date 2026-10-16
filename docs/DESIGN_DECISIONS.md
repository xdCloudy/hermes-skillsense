# Design Decision Log

This file records choices that should remain stable unless a documented issue and benchmark justify a change.

## ADR-001 — In-process BM25 by default

**Status:** accepted. BM25 is deterministic, dependency-free, portable and fast for hundreds of skills. It is not semantic understanding. Improve recall using metadata aliases/intents before making a neural model mandatory.

## ADR-002 — Sidecar metadata, never SKILL.md edits

**Status:** accepted. Other developers own their skill files; upstream updates must remain unaffected. Sidecar versions are tied to source hashes, approvals and provenance.

## ADR-003 — Auxiliary inference only on explicit audit

**Status:** accepted. Normal conversations require zero inference overhead. During audit use a local Hermes auxiliary model *only if local-only routing can be proven*. Otherwise refuse, never fall back to cloud.

## ADR-004 — Abstention over ungrounded selection

**Status:** accepted. A false hint can waste context and tools; empty hints preserve native Hermes discovery. High BM25 scores do not imply calibrated confidence.

## ADR-005 — Native plugin SDK only

**Status:** accepted. No monkey-patching of `AIAgent` or skill registry. If eligibility is inaccessible through public Hermes interfaces, wait for an upstream hook instead of bypassing it.

## ADR-006 — Docs and scaffold before production claims

**Status:** accepted. Ship honest stage gates and cross-platform tests. Advertise installability as a diagnostic scaffold, not working routing, until feature CI and end-to-end validation pass.

Change process: open an issue, present alternatives and measurements, update this log and related tests in the same PR.