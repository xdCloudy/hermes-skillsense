# Roadmap

**Current state:** v0.2.2 experimental beta candidate. SkillSense is functional and opt-in, but **not production-certified**. Do not call the synthetic evaluation a real-world accuracy benchmark.

| Milestone | Status | Completed or pending work |
| --- | --- | --- |
| M0: Bootstrap | Complete | Public repository, branding, contributor/security docs, MIT licence |
| M1: Native plugin | Verified in CI | Hermes plugin doctor, manifest validation and isolated CLI lifecycle |
| M2: BM25 routing | Experimental | Names, descriptions, tags, aliases, intents, abstention and native skill gate |
| M3: Sidecar integrity | Verified in CI | SQLite transactions, source-hash invalidation, root-scoped pruning, safe approval |
| M4: Metadata Clean | Verified with stub | Audit, local-only inference, pending proposals, approval/rejection |
| M5: Cross-platform | Passing | Python 3.11/3.12/3.13 on Windows, Linux and macOS |
| M6: Evaluation infrastructure | Implemented | Synthetic smoke dataset, custom local labelled datasets, reproducible measurements |
| M7: Stable release | **Blocked** | Real held-out selection quality and dynamic/session skill eligibility parity |

## Release blockers

1. [#7 Native session-level skill availability](https://github.com/xdCloudy/hermes-skillsense/issues/7): Hermes can vary skill visibility by project, environment, platform and session, and native plugin-bundled skills are not generally listed by the host's canonical skill index; the present router uses a profile-local canonical snapshot refreshed by explicit maintenance and rechecked periodically; it cannot prove every session's effective visibility.
2. [#8 Independently labelled real-world benchmark](https://github.com/xdCloudy/hermes-skillsense/issues/8): authored synthetic fixtures demonstrate functionality but cannot prove production selection accuracy.

## Longer-term ideas

- Optional tiny local reranker only if measured recall improves enough to justify its memory and latency.
- Authenticated Desktop controls for metadata review when supported by Hermes.
- Export/import metadata with stable provenance and user approval.
- Additional host/plugin compatibility tests and independently reproduced performance measurements.

See [SPEC.md](SPEC.md), [docs/EVALUATION.md](docs/EVALUATION.md), and [docs/RELEASING.md](docs/RELEASING.md).
