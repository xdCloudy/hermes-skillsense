# Changelog

All notable project changes will be documented here. Release entries will follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions and semantic versioning once releases begin.

## [Unreleased]

### v0.2.2 — candidate (not a stable release)

- Native Hermes `skills_list()` availability gate, safe native-only fallback, and Markdown-description extraction (#9, #12).
- Synthetic, transparent selection benchmarks and support for user-provided offline labelled datasets (#10, #14).
- Root-scoped metadata cleanup and source-hash verification before approving proposals, including Windows line-ending correctness (#11).
- Full local HTTP stub audit → pending → manual approval integration suite, without modifying SKILL.md (#13).
- Actual Hermes plugin doctor/CLI lifecycle smoke test, plus cross-platform Python 3.11–3.13 tests.
- Direct remote GitHub installation workflow proposed for additional user-facing verification (#15).
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

### Outstanding production gates
- Native Hermes end-to-end smoke test; real skill availability parity; labelled relevance benchmarks.



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

### Not yet available
- Live skill routing, skill eligibility discovery, sidecar metadata audit/review, local auxiliary inference.
- Verified end-to-end Hermes installation and plugin doctor results (must be validated on an installed host).

No tagged releases or measured runtime results exist yet.