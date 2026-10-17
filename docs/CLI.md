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

`rebuild` scans the Hermes user's `skills` directory by default, or explicitly trusted `--root` directories. It preserves unrelated roots' metadata. For an installation without local SKILL.md files, `refresh-native` can use skills explicitly returned by the canonical `skills_list()` API, without scanning skill files or invoking a model. A **successful empty listing** revokes the previous snapshot so routing abstains rather than continuing to hint removed skills; a failed or malformed host listing refuses the refresh and preserves the previous snapshot. Native-plugin bundled skills omitted by that API are not discovered here; their explicit `skill_view("plugin:skill")` loading remains a Hermes capability.

If a previously indexed trusted root becomes empty (all its skills were removed
or no longer pass the conservative scan), `rebuild` refuses the zero-result
scan by default rather than implicitly pruning records. Once you have verified
the root is genuinely empty, run:

```bash
hermes skillrouter rebuild --root /path/to/confirmed-empty-skills --allow-empty
```

This removes only sidecar records whose stored source paths are under that
explicit root, republishes the index and leaves unrelated roots and source
files intact. `--allow-empty` is intentionally unavailable for model audits.
A scan that fails due to unreadable files or incomplete traversal still aborts.

A valid local index must exist before routing is enabled. Restart existing Hermes sessions after changing enablement settings; native availability changes should also trigger a refresh.

## Metadata Clean

`clean --audit --dry-run` scans trusted roots but makes no database writes or model requests. Non-dry-run cleanup updates the sidecar and publishes an index. New AI-generated proposals require `--model aux`, an explicit numeric loopback endpoint and a local model ID (which may be configured through Hermes Desktop settings).

The HTTP client rejects remote destinations, hostnames, redirects and configured HTTP proxies; it has no provider fallback. A server on loopback may itself forward requests externally. Verify the serving model really is local and its external fallbacks are disabled. Best-effort masking of common credentials is not a comprehensive secret detector.

Local inference is **bounded to 10 requests per invocation by default** (configurable with `--max-inferences N`, 1–50). Running the command again skips pending/approved/rejected skills and continues with remaining candidates. Use `--offset N` when a `--force` audit needs explicit pagination, or to bypass repeatedly failing skills. `--dry-run` makes no inference calls and does not require a model endpoint.\n\nAll generated metadata is **pending** until `review approve`. A changed source invalidates a stale approval. No maintenance command overwrites a SKILL.md source.

## Doctor and slash command

`hermes skillrouter status` separately reports sidecar records and currently verified native skills; if routing is configured but the native catalogue has expired or disappeared it reports **configured but inactive** rather than implying hints are available. `hermes skillrouter doctor` reports integration/index readiness. In addition to missing indexes, it detects invalid/unreadable index data and missing or expired canonical snapshots. A malformed enrichment index causes native-only fallback rather than a crash; the doctor reports the problem and recommends `rebuild`. `/skillrouter status` is deliberately read-only; authenticated local CLI commands are required for modifications.

## Limitations

- Skill visibility is determined from a profile-scoped canonical snapshot, not a complete per-session authorization decision.
- Skill audit/review buttons in Desktop have not been implemented.
- The registered auxiliary task is not used for direct model transport because of possible host-level provider fallback.
- Live selection accuracy has not been independently validated; do not interpret the included synthetic benchmark as production quality.
