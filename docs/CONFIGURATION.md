# Configuration — experimental v0.2.0

SkillSense does not read an undocumented Hermes settings object. Local state is controlled by the native CLI.

## Defaults

| Option | Default |
| --- | --- |
| Routing | Disabled until \`hermes skillrouter enable\` |
| Max hints | Two, maximum three internally |
| Index location | Hermes profile data directory / \`plugin-data/skillsense/index.json\` |
| Sidecar | SQLite \`data.db\`, transactional |
| Source scan | Active Hermes profile \`skills\` directory |
| Metadata audit | Manual |
| Inference | None unless \`--model aux\` is specified |
| Model endpoint | Explicit numeric loopback URL; no remote fallback |
| SKILL.md modifications | Never |

Plugin data survives updates/removal and is profile-scoped through the host storage API when available.

The auxiliary task \`skillrouter-tagger\` is registered in Hermes. The current secure audit path uses an explicit loopback endpoint and model ID instead of \`ctx.llm\`, because the host API can use cloud fallbacks not controllable by the plugin.

## Desktop

Native Desktop settings can show plugin manifest information. Dedicated buttons for scanning and review are not implemented; use CLI. Do not assume toggles in Desktop affect routing unless their wiring is tested.
