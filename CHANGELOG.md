# Changelog

All notable project changes will be documented here. Release entries will follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions and semantic versioning once releases begin.

## [Unreleased]

- Enforce the runtime index reader's 2,500-record and 3 MB limits in the atomic JSON publisher, failing with actionable errors instead of publishing an unreadable oversized index.

- Validate every canonical Hermes listing entry and bound host response size/count before accepting catalogue updates; reject partial, duplicate or malformed successful responses instead of mistaking them for verified emptiness.

- Preserve a previous native eligibility snapshot when Hermes catalogue lookup fails during `rebuild` or non-dry-run `clean --audit`, mirroring `refresh-native`; verified-empty results still revoke prior names, and maintenance reports warnings.

- Clear per-session duplicate-hint suppression whenever the router cache is explicitly invalidated, so catalogue changes do not leave stale five-minute suppression behind.

- Publish the reconciled approved index before optional long-running local-model audit requests, avoiding needless native-only fallback throughout the audit; pending proposals still require explicit approval.
- Reject entire partially malformed native catalogues on read (including unexpected envelope fields, invalid load names/descriptions, and non-finite timestamps) instead of trusting a silently filtered subset.
- Distinguish a verified empty Hermes skill list from unavailable/malformed host responses during `refresh-native`: clear stale availability after successful empty lookups, preserve the previous snapshot on errors.

- Catch conditional Hermes skill fields inside compact YAML flow maps, avoiding accidental sidecar enrichment when tool or session requirements are hidden in inline mappings.

- Bound verified native snapshots to 2,500 entries on write and read, preventing oversized on-disk metadata from allocating unbounded live BM25 indexes. Failed refreshes preserve prior snapshots.
- Bounded and hashed session deduplication keys; avoid retaining raw/oversized host session IDs in the process-global hint cache.

- Secure existing sidecar directories to 0700 on POSIX, shielding SQLite WAL/SHM files on older profiles; reject final directory symlinks where supported.

- Restricted SQLite sidecar creation to owner-only permissions on POSIX, repairing old overly permissive database files and refusing final-path symlinks where O_NOFOLLOW is supported.
- Conservatively skip source enrichment for session-platform and required-environment-variable conditioned skills, including block-form YAML.

- Added real-Hermes enable/disable integration coverage for a native plugin skill and updated outdated skill-listing compatibility claims against current upstream source.

- Invalidate the published JSON index before SQLite updates that can change approved routing metadata, preventing stale disk hints when maintenance is interrupted; ensure cleanup invalidates in-process caches even on errors.
- Restore test discovery for the previously misplaced opt-in empty-root reconciliation regression.

- Fixed the offline Recall@3 sample to evaluate three eligible suggestions; runtime can now honour an explicit maximum of three while retaining its default two-hint limit and conservative evidence gates.
- Added opt-in `rebuild --allow-empty` to safely reconcile completely emptied trusted skill roots without pruning unrelated sidecar data.
- Validate persisted index records (including field types, size bounds and unique IDs) before routing; fall back to native-only metadata on malformed enrichment.

### Merged hardening since v0.2.2 candidate

- Initially documented a limitation in native-plugin skill discovery; **superseded by the host integration proof in #49**, which confirmed enabled registered plugin skills appear in the canonical listing on the tested Hermes version.

- Hardened text-only hot-path routing against multimodal input coercion, oversized-turn normalization and duplicate-name secondary hints (#39).

- Verified public GitHub installation and exact-PR installation checks (#15, #18).
- Guarded against stale or shadowed skill names and approved negative-intent mismatches (#19).
- Prevented incomplete and unreadable scans from corrupting or pruning sidecar data (#20, #24).
- Captured native skill eligibility as a bounded local snapshot for isolated plugin hosts (#17), with periodic cache refresh and safe config handling (#21).
- Added native-only/plugin-only availability refresh without requiring local SKILL.md files (#25).
- Added best-effort masking of obvious credential strings before optional metadata inference (#26).
- Streamlined pull-request CI while retaining the full scheduled/manual cross-platform matrix (#27).
- Immediately republished the index when an attempted metadata approval invalidates stale enrichment (#28).
- Added read-only operator diagnostics, actionable catalogue health reporting and safe enablement checks (#22).
- Conservatively excluded conditional block-form YAML sources from sidecar enrichment (#29).


### v0.2.2 — candidate (not a stable release)

- Native Hermes `skills_list()` availability gate, safe native-only fallback, and Markdown-description extraction (#9, #12).
- Synthetic, transparent selection benchmarks and support for user-provided offline labelled datasets (#10, #14).
- Root-scoped metadata cleanup and source-hash verification before approving proposals, including Windows line-ending correctness (#11).
- Full local HTTP stub audit → pending → manual approval integration suite, without modifying SKILL.md (#13).
- Actual Hermes plugin doctor/CLI lifecycle smoke test, plus cross-platform Python 3.11–3.13 tests.
- Direct GitHub installation and CLI workflow verified through CI (#15, #18).
- Remaining stable blockers: session-level availability parity (#7) and independently reviewed real-world retrieval quality (#8).


### Implemented for experimental v0.2.1
- Native Desktop settings for enablement, max suggestions and optional loopback model target (using ctx.get_config / set_config).
- Suppress repeat hints within a session and prevent direct injection of untrusted skill descriptions.
- Loopback HTTP integration tests and isolated Hermes plugin-doctor CI workflow.

### Implemented for experimental v0.2.0
- Read-only bounded skill scanner with missing frontmatter handling and platform restriction abstention.
- Transactional SQLite sidecar with source-hash invalidation, pending metadata proposals, approval and rejection.
- Immutable JSON BM25 index and opt-in per-turn hints with conservative abstention.
- Local-only, explicit numeric loopback OpenAI-compatible metadata inference; remote URLs, proxy use and redirects rejected.
- CLI rebuild, dry-run audit, model audit, review, enable/disable and status commands; gateway slash operations are status-only.
- Additional security, storage, routing and catalogue tests; synthetic benchmark harness.

### Historical outstanding gates at v0.2.0
- Hermes end-to-end smoke testing (subsequently implemented), real session-level skill availability parity and independently labelled relevance benchmarks (both still open).



### Added
- Native Hermes plugin scaffold (`plugin.yaml`, `register(ctx)`) with a no-op `pre_llm_call` and diagnostic CLI/slash commands.
- Dependency-free, pure Python BM25 search core and cross-platform unit tests.
- CI matrix, repository structure checks, maintainer/support guides, settings/CLI/FAQ/development docs and design decisions.
- Updated transparent, neutral SkillSense logo for dark and light UI backgrounds.
- Public SkillSense project bootstrap and brand identity.
- Initial product goal, Metadata Clean specification and architecture.
- Agent instructions, roadmap, security and contribution guidelines.
- Proposed metadata schema, integration plan and benchmarking protocol.
- GitHub issue/PR templates and documentation checks.

### Historical implementation gaps at initial bootstrap (now addressed)
- Live skill routing, skill eligibility discovery, sidecar metadata audit/review, local auxiliary inference.
- Verified end-to-end Hermes installation and plugin doctor results (subsequently validated through CI).

No tagged releases or measured runtime results exist yet.