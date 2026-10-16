# Roadmap

SkillSense is **pre-alpha / planning**. These are intended milestones, not delivered features.

| Milestone | Scope | Gate |
| --- | --- | --- |
| M0: Bootstrap | Brand, docs, issue templates, license, agent guidance | Repository is coherent; no broken feature claims |
| M1: Plugin skeleton | Native Hermes manifest, registration, no-op hook, CLI/slash status, doctor | Installs and disables with no side effects |
| M2: Lexical retrieval | Safe skill discovery, parser, BM25, availability filters, abstention | Reproducible retrieval tests; normal Hermes still works |
| M3: Sidecar storage | SQLite schema, versioning, atomic indexes, profile isolation | Integrity and migration tests |
| M4: Deterministic audit | Metadata quality checks, hashing, dry-run, reports | No model necessary |
| M5: Local auxiliary audit | Strict local-only routing, schema generation, source evidence checks | Remote exfiltration tests fail closed |
| M6: Review & UX | Field-level approval, CLI/slash, Desktop settings | Accessible, reversible review; no source edits |
| M7: Benchmark & release | Performance + recall metrics, Windows/macOS/Linux CI, packaging | Published reproducible data; native plugin validation |

## Release policy

Do not publish a "stable" package or documentation implying working commands until M1–M6 have passed. For beta, define supported Hermes versions, migration guarantees and benchmark datasets. All stages require zero modification to user skill source files.

## Future considerations

- Optional local tiny reranker only if independent benchmarks justify the additional cost.
- Metadata profiles shared with compatible agent harnesses.
- First-class Desktop review pane if supported by the Desktop Plugin SDK.
- Better historical usage analysis, with explicit opt-in and privacy controls.

Track work in GitHub Issues; link pull requests to milestones. See [SPEC.md](SPEC.md).