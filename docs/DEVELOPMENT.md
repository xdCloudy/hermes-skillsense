# Development Setup

This repository provides an **experimental native Hermes plugin**, a dependency-free BM25 implementation, and tests. Skill routing, metadata audit and review exist behind explicit opt-in, but a real Hermes integration smoke test **has passed**; stable skill-selection accuracy and dynamic eligibility are still unverified.

## Prerequisites

- Python 3.11 or newer for local project tests.
- Git.
- An optional up-to-date Hermes Agent installation for integration validation.

The plugin uses only Python standard-library dependencies at runtime and does not download or run a model for ordinary turns.

## Clone and test

```bash
git clone https://github.com/xdCloudy/hermes-skillsense.git
cd hermes-skillsense
python -m compileall -q __init__.py core.py tests tools
python -m unittest discover -s tests -v
python tools/check_repo.py
python tools/evaluate.py
python tools/benchmark.py
```

For Windows, use `py -3.11` in place of `python` if needed.

## Hermes integration smoke test

In a trusted local Hermes installation, from the repository root:

```bash
hermes plugins doctor . --ci
hermes plugins validate .
```

Plugin doctor exercises registration in a temporary `HERMES_HOME`. GitHub Actions also runs a separate isolated Hermes host integration workflow and an installation-from-GitHub workflow. The standalone Python test matrix intentionally needs no Hermes installation. Record the tested Hermes version when reproducing host issues.

The native hook emits no hints by default. An operator must rebuild the index and run `hermes skillrouter enable`, then restart Hermes. Only exact or evidence-supported BM25 candidates are suggested; Hermes remains responsible for skill loading.

## Design references

- [Hermes plugin development](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)
- [Plugin LLM access](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access)
- [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)

## Workflow

1. Open an issue for API changes or major security-sensitive behaviour.
2. Read [AGENTS.md](../AGENTS.md), [ARCHITECTURE.md](../ARCHITECTURE.md) and [SPEC.md](../SPEC.md).
3. Write pure, unit-testable functions; preserve the opt-in and fail-closed pre-LLM hook, and add end-to-end Hermes tests for any eligibility change.
4. Run the cross-platform test suite and host plugin doctor if available.
5. Update documentation/CHANGELOG and include reproducible tests in the PR.
6. Avoid checking in real user SKILL.md documents, private history or secrets.

## Windows-specific notes

Avoid POSIX-only subprocess invocations and treat paths with `pathlib`. Tests must work without WSL or Docker. Do not assume the user runs the plugin from the repository directory.