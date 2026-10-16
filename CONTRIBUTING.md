# Contributing to SkillSense

Thanks for helping build a small, reliable, local-first Hermes skill router.

## Before starting

Read [GOAL.md](GOAL.md), [SPEC.md](SPEC.md), [ARCHITECTURE.md](ARCHITECTURE.md), [AGENTS.md](AGENTS.md), and [SECURITY.md](SECURITY.md). Search existing issues before starting substantial work; propose API or security changes in an issue first.

This is a **pre-alpha** repository. A minimal plugin entry point, pure BM25 core, and Python unit tests exist. Routing, Metadata Clean and actual Hermes-host validation are outstanding.

## Local development (when implementation exists)

- Use a recent supported Python version and an isolated environment.
- Avoid introducing a runtime dependency without an explicit rationale.
- Run `python -m unittest discover -s tests -v` for the existing unit-test suite.
- Validate with `hermes plugins doctor . --ci` and `hermes plugins validate .` against supported Hermes versions when a valid plugin manifest exists.
- Test Windows, macOS and Linux behaviour when touching filesystem or process logic.

Do not install this repo into a production Hermes profile until a release is published and validated.

## Pull requests

Prefer a single scoped change with:

1. Problem statement and related issue.
2. Proposed behaviour and compatibility assumptions.
3. Security/privacy effects (including any endpoint or local file access).
4. Tests run and results; explicitly list what could not be tested.
5. Before/after performance or retrieval measurements where relevant.
6. Documentation and changelog changes for user-facing behaviour.

No fabricated success rates or benchmark comparisons. Do not submit copyrighted datasets, personal Hermes transcripts, tokens, private skill content, or secrets.

## Code style

- Type-hinted, small Python modules; standard library preferred.
- Use `pathlib`, UTC-aware timestamps and cross-platform file handling.
- Prefer explicit schemas and pure functions for ranking/validation.
- Avoid broad exception swallowing except in the per-turn fail-open-to-Hermes boundary, where diagnostics should still be rate-limited.
- Treat model output and skill files as untrusted.
- Keep the synchronous hook cheap and bounded.

## Reporting security issues

Follow [SECURITY.md](SECURITY.md), not a public issue with exploit details.

## Community behaviour

Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Contributions are offered under the repository's [MIT license](LICENSE).