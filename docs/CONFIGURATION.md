# SkillSense configuration — v0.2.2 beta

## Hermes Desktop

The standard native Hermes plugin settings surface is supported via `ctx.get_config()` / `ctx.set_config()`. In **Settings → Plugins → SkillSense**, use:

| Setting | Default | Behaviour |
| --- | --- | --- |
| `enabled` | `false` | Opt-in skill hints after restarting Hermes |
| `max_suggestions` | `2` | Integer clamped to 1–3 |
| `local_endpoint` | Empty | Optional numeric loopback URL for metadata cleanup |
| `local_model_id` | Empty | Local model ID for manually triggered audit |

Desktop settings do not execute a cleanup. To scan, review or approve metadata, use the CLI.

## CLI

```bash
hermes skillrouter rebuild
hermes skillrouter status
hermes skillrouter enable
hermes skillrouter clean --audit --dry-run
hermes skillrouter clean --audit --model aux
hermes skillrouter review list
```

The CLI `enable` command refuses activation until both the published index and a non-empty, unexpired canonical native-skill snapshot exist. Run `refresh-native` if availability is missing or expired. Desktop configuration still relies on the normal-turn fail-closed check if manually enabled while the snapshot is unavailable. The CLI `enable`/`disable` commands use Hermes plugin settings when invoked through the host. Changing enablement generally requires restarting existing Hermes sessions. Explicit catalogue maintenance with `rebuild` or `refresh-native` should follow changes to installed/available skills.

## Canonical skill availability

`hermes skillrouter rebuild` stores trusted local skill metadata and refreshes the canonical native skill snapshot. `hermes skillrouter refresh-native` refreshes only names and descriptions actually returned by Hermes' `skills_list()`, including in some profiles without a user skill folder. Current Hermes versions can include enabled, registered native-plugin bundles in that list; the real-host integration test checks enable/disable behavior. Other versions may differ, so only actually listed names enter the snapshot. Snapshot validity is bounded to seven days. A missing, empty or expired catalogue suppresses routing hints.

A cache is not a session-scoped authorization decision: individual project directories and changes to tool/environment availability are still covered by [issue #7](https://github.com/xdCloudy/hermes-skillsense/issues/7).

## Local inference

For enrichment, `--model aux` requires a numeric loopback target on HTTP. The operator can supply `--endpoint` and `--model-id` explicitly or configure the same values in Desktop settings. The endpoint must be `http://127.0.0.1:PORT/v1/chat/completions` (or `[::1]`).

SkillSense refuses non-loopback URLs, DNS hostnames, URL credentials and redirects, and bypasses environment-configured HTTP proxies. Its HTTP transport has no provider fallback. **This only constrains the destination of SkillSense's request**: a local model gateway or proxy can still forward input to external services. Confirm that the server bound to the loopback address uses local weights and has remote fallback disabled. Host-native auxiliary task selection is registered but is **not used for model transport**.

## Storage and portability

The cached index and SQLite sidecar are profile-scoped under the Hermes plugin data root. A broken cache results in no hint rather than an interrupted Hermes turn. Original SKILL.md files are never modified.

## Limitations

Only explicitly trusted roots are scanned. The sidecar refuses enrichment for source skills declaring platform/requirement restrictions, including Hermes' `requires_toolsets`, `requires_tools`, `fallback_for_toolsets`, `fallback_for_tools`, `session_platforms` and `required_environment_variables` (inline or block-form). Such skills can still use a native-only fallback **if present in the canonical snapshot**; generated aliases are not attached to them. This conservative safeguard does not establish per-session availability equivalence. Project precedence and changing tool availability remain outside the plugin's proven contract. Treat hints as candidates requiring native verification.
