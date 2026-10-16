# SkillSense CLI reference — v0.2.2 beta

These commands are provided by Hermes' native plugin CLI registration.

```text
hermes skillrouter status
hermes skillrouter doctor
hermes skillrouter rebuild [--root DIRECTORY] ...
hermes skillrouter refresh-native
hermes skillrouter clean --audit --dry-run [--root DIRECTORY] ...
hermes skillrouter clean --audit --model aux --endpoint http://127.0.0.1:8011/v1/chat/completions --model-id MODEL [--max-inferences 10] [--offset 0]
hermes skillrouter review list
hermes skillrouter review approve SKILL_NAME_OR_ID
hermes skillrouter review reject SKILL_NAME_OR_ID
hermes skillrouter enable
hermes skillrouter disable
```

## Build or refresh the catalogue

`rebuild` scans the Hermes user's `skills` directory by default, or explicitly trusted `--root` directories. It preserves unrelated roots' metadata. For an installation containing only native/plugin-provided skills, `refresh-native` refreshes their canonical availability without scanning SKILL.md files or invoking a model.

A valid local index must exist before routing is enabled. Restart existing Hermes sessions after changing enablement settings; native availability changes should also trigger a refresh.

## Metadata Clean

`clean --audit --dry-run` scans trusted roots but makes no database writes or model requests. Non-dry-run cleanup updates the sidecar and publishes an index. New AI-generated proposals require `--model aux`, an explicit numeric loopback endpoint and a local model ID (which may be configured through Hermes Desktop settings).

The HTTP client rejects remote destinations, hostnames, redirects and configured HTTP proxies; it has no provider fallback. A server on loopback may itself forward requests externally. Verify the serving model really is local and its external fallbacks are disabled. Best-effort masking of common credentials is not a comprehensive secret detector.

Local inference is **bounded to 10 requests per invocation by default** (configurable with `--max-inferences N`, 1–50). Running the command again skips pending/approved/rejected skills and continues with remaining candidates. Use `--offset N` when a `--force` audit needs explicit pagination, or to bypass repeatedly failing skills. `--dry-run` makes no inference calls and does not require a model endpoint.\n\nAll generated metadata is **pending** until `review approve`. A changed source invalidates a stale approval. No maintenance command overwrites a SKILL.md source.

## Doctor and slash command

`hermes skillrouter status` separately reports sidecar records and currently verified native skills; if routing is configured but the native catalogue has expired or disappeared it reports **configured but inactive** rather than implying hints are available. `hermes skillrouter doctor` reports integration/index readiness. In addition to missing indexes, it can detect missing or expired canonical snapshots. `/skillrouter status` is deliberately read-only; authenticated local CLI commands are required for modifications.

## Limitations

- Skill visibility is determined from a profile-scoped canonical snapshot, not a complete per-session authorization decision.
- Skill audit/review buttons in Desktop have not been implemented.
- The registered auxiliary task is not used for direct model transport because of possible host-level provider fallback.
- Live selection accuracy has not been independently validated; do not interpret the included synthetic benchmark as production quality.
