# Development Setup

This repository provides an **initial native Hermes plugin scaffold**, a dependency-free BM25 implementation, and tests. End-to-end skill routing and Metadata Clean do **not** exist yet.

## Prerequisites

- Python 3.11 or newer for local project tests.
- Git.
- An optional up-to-date Hermes Agent installation for integration validation.

The base scaffold uses no third-party Python runtime dependencies and does not download a model.

## Clone and test

```bash
git clone https://github.com/xdCloudy/hermes-skillsense.git
cd hermes-skillsense
python -m compileall -q __init__.py core.py tests tools
python -m unittest discover -s tests -v
python tools/check_repo.py
```

For Windows, use `py -3.11` in place of `python` if needed.

## Hermes integration smoke test

In a trusted local Hermes installation, from the repository root:

```bash
hermes plugins doctor . --ci
hermes plugins validate .
```

Plugin doctor exercises discovery and registration with a temporary `HERMES_HOME`. Neither command is run by the GitHub CI matrix because CI does not install Hermes itself. Record the exact Hermes version when testing.

The native entry point currently registers `pre_llm_call` as a **no-op**, plus `hermes skillrouter status|doctor` and `/skillrouter` status. It does **not** inject hints or change native skill loading.

## Design references

- [Hermes plugin development](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)
- [Plugin LLM access](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access)
- [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)

## Workflow

1. Open an issue for API changes or major security-sensitive behaviour.
2. Read [AGENTS.md](../AGENTS.md), [ARCHITECTURE.md](../ARCHITECTURE.md) and [SPEC.md](../SPEC.md).
3. Write pure unit-testable functions; preserve the no-op hook until eligibility and audit tests pass.
4. Run the cross-platform test suite and host plugin doctor if available.
5. Update documentation/CHANGELOG and include reproducible tests in the PR.
6. Avoid checking in real user SKILL.md documents, private history or secrets.

## Windows-specific notes

Avoid POSIX-only subprocess invocations and treat paths with `pathlib`. Tests must work without WSL or Docker. Do not assume the user runs the plugin from the repository directory.