# Hermes integration

**Status:** SkillSense v0.2.2 is an opt-in beta. GitHub Actions has verified the public GitHub install, plugin manifest validation, native CLI registration, and an isolated Hermes catalogue/routing lifecycle. This is **not a stable release certification**.

## Runtime integration

- The plugin registers a `pre_llm_call` hook through Hermes' `PluginContext`. When routing is enabled, a sufficiently specific query may return `{"context": "..."}`, adding ephemeral user-turn context without modifying the stable system prompt or installed skill files.
- A cached BM25 index is loaded from `index.json`. A separate `native-catalogue.json` snapshot records the Hermes-visible skill load names and descriptions. Both are in the plugin's profile-local storage.
- Canonical names are captured during explicitly invoked maintenance commands using Hermes' existing `tools.skills_tool.skills_list()`; the ordinary-turn hook does **not** import that host-internal module.
- The router only emits names supported by the native snapshot, omits duplicates or ambiguous matches, and uses native-only descriptions when sidecar attribution cannot be verified. An absent, malformed, empty or expired native snapshot produces no suggestions.
- The native snapshot is valid for at most seven days. The in-memory router periodically rechecks it. Refresh after modifying installed skills, environment availability or profiles.
- Native `skill_view` and skill loading remain fully owned by Hermes. SkillSense only suggests possible relevant load names.

## Maintenance APIs

`hermes skillrouter rebuild` scans only selected trusted local roots, updates the SQLite sidecar and publishes a new index. `hermes skillrouter refresh-native` refreshes native and plugin skill availability without reading local SKILL.md sources. The latter also supports profiles with no local skill directory.

`hermes skillrouter clean --audit` is explicitly invoked and may use an operator-provided numeric HTTP loopback inference endpoint. It produces pending sidecar metadata; only manual `review approve` activates a proposal. A changed source hash invalidates its pending/approved enrichment. Source SKILL.md files are never rewritten.

The hook has no per-turn model inference or network requests. The optional audit client's destination is constrained to loopback, with HTTP environment proxies disabled and redirects refused. This **does not prove** that a local model gateway itself does not relay requests to remote providers.

## Hermes API compatibility and remaining blocker

The `PluginContext` registration APIs and `pre_llm_call` ephemeral-context response have been validated in an actual Hermes test installation. However, `tools.skills_tool.skills_list()` is an internal module imported by maintenance commands, not a guaranteed stable plugin SDK interface.

More importantly, the snapshot is profile-wide rather than fully session-specific. Project trust, working-directory changes, environment/toolset gates and disabled skills can alter what a particular session can load. Until Hermes offers a documented context-aware skill availability API, **issue #7 remains a release blocker**. The router intentionally abstains when it cannot verify eligibility.

**Issue #8** remains a separate release blocker: the included retrieval benchmark is synthetic and not independently labelled. The independent accuracy evaluator is documented in [EVALUATION.md](EVALUATION.md).

## Testing

Use:

```bash
python -m unittest discover -s tests -v
python tools/check_repo.py
python tools/evaluate.py
hermes plugins doctor . --ci
hermes plugins validate .
```

GitHub Actions also verifies direct public installation, CLI maintenance and routing against a real Hermes instance, plus a multi-OS Python test matrix. See [DEVELOPMENT.md](DEVELOPMENT.md), [CLI.md](CLI.md) and [RELEASING.md](RELEASING.md).

## Desktop and gateway

`config_schema` provides native Hermes settings for enablement, maximum hints and the local model target. Changes to enablement may require restarting existing Hermes sessions. The `/skillrouter` slash command is read-only so untrusted gateway senders cannot launch filesystem scans or model requests. Custom Desktop review controls remain unimplemented.
