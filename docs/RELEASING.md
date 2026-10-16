# Releasing SkillSense

This policy describes **future** releases. No production-ready version exists yet.

## Pre-release checklist

1. Tests pass on Ubuntu, Windows and macOS under supported Python versions.
2. `hermes plugins doctor . --ci` and `hermes plugins validate .` pass under supported Hermes versions.
3. No unreviewed cloud fallback, subprocess execution or unsafe skill file access.
4. Profile-scoped state migrations and rollback are tested.
5. Benchmarks report actual latencies, recall/precision and no-skill false positives.
6. Installation, removal, update and recovery are verified on isolated Hermes profiles.
7. README and CHANGELOG clearly say what works; docs show correct CLI flags.
8. Logo/source attribution and MIT licence are correct.
9. A signed/tagged release commit identifies the exact tested version.
10. GitHub release notes link benchmark methodology and known limitations.

## Versioning

Use SemVer: `0.x.y` while APIs may change; `1.0.0` only after normal routing, local Metadata Clean and durable review work end-to-end. A release must not claim features only present in a specification.

## Security

Never publish fixture datasets sourced from real private user transcripts or proprietary skills without permission. Secrets must be absent from releases, logs and workflow artifacts.