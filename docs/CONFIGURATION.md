# SkillSense Configuration — experimental v0.2.1

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

The CLI `enable`/`disable` commands use the supported Hermes plugin settings API when invoked through the host; standalone tests use a profile-scoped marker fallback. Changing enablement requires restarting existing Hermes sessions.

## Local inference

For enrichment, `--model aux` requires a numeric loopback target on HTTP. The operator can supply `--endpoint` and `--model-id` explicitly or configure the same values in Desktop settings. The endpoint must be `http://127.0.0.1:PORT/v1/chat/completions` (or `[::1]`).

No cloud URLs, DNS hostnames, auth credentials, proxies, automatic redirects or provider fallback. Host-native auxiliary task selection is registered but **not used for network transport** until a supported route can guarantee no remote fallback.

## Storage and portability

The cached index and SQLite sidecar are profile-scoped under the Hermes plugin data root. A broken cache results in no hint rather than an interrupted Hermes turn. Original SKILL.md files are never modified.

## Limitations

Only explicitly trusted roots are scanned. Nontrivial skill platforms, tool requirements and project precedence cannot yet be proven identical to native Hermes discovery. Treat hints as candidates requiring native verification.
