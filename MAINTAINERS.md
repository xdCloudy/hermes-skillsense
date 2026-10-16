# Maintainer Guide

**Maintainer:** [xdCloudy](https://github.com/xdCloudy)

## Branches and releases

- `main` is the working integration branch.
- Prefer pull requests with CI passing before merge; protect `main` when repository settings permit.
- Use semantic versioning from the first tagged pre-release. No stable release while actual routing and audit behaviour remain unimplemented.
- Release notes must separate shipped behaviour from targets.
- Do not publish an install guide declaring missing features operational.

## Contribution review priorities

1. Privacy: no remote exfiltration of skill contents.
2. Native Hermes compatibility: only documented surfaces.
3. Correctness: deterministic fallback, availability filtering, explicit review.
4. Performance: no inference or network in normal turns.
5. Portability: Windows, Linux, macOS.
6. Docs and reproducible tests.

## Release checklist

See [docs/RELEASING.md](docs/RELEASING.md). Ensure CI passes, Hermes plugin doctor/validator pass for pinned host versions, a rollback path is documented, and the CHANGELOG has dated, measured changes.

## Triage labels

Suggested labels: `bug`, `enhancement`, `documentation`, `security`, `performance`, `compatibility`, `good first issue`, `help wanted`, `blocked-upstream`, `needs-repro`.

GitHub repository settings (description/topics, branch protection, security advisories and social preview) must be configured by an administrator when not exposed through the available integration.