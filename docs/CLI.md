# CLI reference — experimental v0.2.0

All commands are registered through Hermes' native CLI plugin API.

## Commands

\`\`\`text
hermes skillrouter status
hermes skillrouter doctor
hermes skillrouter rebuild [--root DIRECTORY] ...
hermes skillrouter clean --audit --dry-run [--root DIRECTORY] ...
hermes skillrouter clean --audit --model aux --endpoint http://127.0.0.1:8011/v1/chat/completions --model-id MODEL
hermes skillrouter review list
hermes skillrouter review approve SKILL_NAME_OR_ID
hermes skillrouter review reject SKILL_NAME_OR_ID
hermes skillrouter enable
hermes skillrouter disable
\`\`\`

Each scan defaults to the user's Hermes \`skills\` directory and can take one or more explicit trusted roots. A rebuild is required before enabling live hints. After enabling/disabling restart existing Hermes sessions.

## Slash commands

\`/skillrouter status\` is read-only. All mutating maintenance must run locally via CLI. This prevents unauthorised gateway senders from launching skill scans or LLM jobs.

## Metadata Clean

\`--dry-run\` reports missing tags/descriptions but performs **no writes or model calls**. A normal \`clean --audit\` refreshes source hashes and preserves approved metadata, but cannot generate new tags without \`--model aux\`.

\`--model aux\` requires explicit \`--endpoint\` on \`127.0.0.1\` or \`[::1]\` and \`--model-id\`. The HTTP client rejects remote hosts, DNS names, redirects and proxy settings, and has no provider fallback. A server running on loopback can still forward requests externally; to remain genuinely offline, operators must verify that the local inference service has no remote backends. Suggestions go into the SQLite sidecar as **pending**, never directly into SKILL.md.

\`review approve\` activates pending metadata and regenerates the index. \`review reject\` discards it. Existing approved metadata is invalidated when its skill source changes.

## Known limitations

- Hermes auxiliary task is registered, but model resolution is currently explicit on the CLI to avoid host-level cloud fallback.
- No Desktop audit/review buttons.
- No automatic project-skill discovery: only user-approved roots.
- Eligibility decisions are conservative but are not proven identical to Hermes' full native skill registry.
- Rebuild/index changes require restarting existing Hermes sessions for fresh state.
